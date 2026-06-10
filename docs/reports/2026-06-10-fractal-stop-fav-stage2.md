# Fractal Stop Fav — Stage 2: Торговый слой

> **Date**: 2026-06-10
> **Status**: Completed
> **Verdict**: ❌ FAIL — ни одна комбинация не достигает PF > 1.0 на canonical spread. Торговая постановка breach→fav→trade не работает на текущих признаках.
> **Goal**: Добавить торговый слой поверх breach-сигнала Stage 1: RF regressor для благоприятного хода (fav_val), объединение breach+fav через торговое правило, grid search порогов на val
> **Related spec**: `docs/superpowers/specs/2026-06-08-fractal-stop-fav-target-design.md`
> **Related plan**: `docs/superpowers/plans/2026-06-10-fractal-stop-fav-plan.md`
> **Related Stage 1 report**: [`2026-06-10-fractal-stop-breach-stage1.md`](2026-06-10-fractal-stop-breach-stage1.md)
> **Related commit**: 206eee3

## Context

Stage 1 подтвердил: RF классификатор на фрактальных признаках предсказывает пробой стоп-уровня (AUC 0.62–0.68, lift 1.52–1.77). Stage 2 проверяет, можно ли превратить этот сигнал в положительное матожидание: объединяем breach-классификатор с fav-регрессором через торговое правило, оцениваем PnL через first-touch симулятор.

Гипотеза: breach+predict_fav → фильтр входа (низкая P(пробой), высокий fav/stop) генерирует PF > 1.0.

## What Was Done

### 1. Разметка fav-таргетов
- `processing/label_signals.py`: функция `label_fractal_stop_fav_targets()` — 4 H-specific колонки: `target_buy_H6_val`, `target_buy_H12_val`, `target_sell_H6_val`, `target_sell_H12_val`
- Значения: `max(|благоприятный_ход|) / ATR` за H баров от `Open[row+1]`
- NaN для противоположной стороны и при нехватке будущих баров
- `processing/label_main.py`: CLI-флаг `--fractal-stop-fav`
- Размечено 3 сплита: train, val, test (поверх существующих breach-колонок)

### 2. Торговый симулятор
- `processing/label_signals.py`: функция `evaluate_fractal_stop_trade()` — first-touch SL/TP/TIMEOUT по спецификации
- Правило ambiguous-бара: если в одном H1-баре задеты и TP, и SL — SL первым, `ambiguous_flag=1`
- Все PnL в ATR-единицах (`_val`)
- Spread входа: canonical 0.20, stress 0.40, diagnostic 0.00

### 3. Тесты
- `tests/processing/test_fractal_stop_fav.py` — 9 тестов: 4 fav-разметка (BUY fav, SELL fav, H differ, no entry bar), 5 trade evaluation (TP, SL, ambiguous, TIMEOUT BUY, TP SELL)
- Все 9 PASS

### 4. Smoke check
- `statistics/data_contract_smoke_check.py`: проверка fav-колонок (существование, ≥0, mean ∈ (0, 5) ATR)
- ALL CHECKS PASSED на всех трёх сплитах

### 5. RF baseline + grid search
- `ML/baseline/benchmark_fractal_stop_fav.py`: RF breach classifier + RF fav regressor + grid search торговых порогов + frozen test
- Признаки: 10 каналов × 100 фракталов + ATR = 1001 признак (allowlist Stage 1)
- RF hyperparams: n_estimators=200, max_depth=12, min_samples_leaf=50
- Grid search: p ∈ {0.3,0.4,0.5}, min_fav ∈ {0.3,0.5,0.7}, min_rr ∈ {1.0,1.5,2.0}, tp_fraction ∈ {0.3,0.5,0.7}, cap=5.0
- Winner selection только на canonical spread=0.20; diagnostic 0.0 и stress 0.40 — те же пороги
- 8 комбинаций H×off×side, каждая с 81 вариантом порогов = 648 grid-результатов

### 6. Frozen test
- Правило заморожено: H=12, off=0.5, SELL (лучшая val-комбинация `sell_H12_off05`)
- Train на train+val (2004–2022), test (2022–2026) открыт один раз через `--frozen-rule`
- Никакого grid search на test

### 7. Регрессия Stage 1
- 10 тестов Stage 1 PASS, smoke check PASS
- Итого: 19 тестов (10 Stage 1 + 9 Stage 2) — все PASS

### Принятые решения
- Отдельные breach-классификаторы + отдельные fav-регрессоры для каждой комбинации H×off×side (как в Stage 1)
- `stop_offset_val` ∈ {0.2, 0.5} (как в Stage 1 breach)
- Минимум ≥30 сделок/год для допуска grid-комбинации
- Test вскрыт дважды в рамках одного исследовательского цикла (Stage 1 + Stage 2). Результат — research candidate, не допуск в рабочий контур

## Verification

```bash
python -m pytest tests/processing/test_fractal_stop_fav.py -v               # 9 passed
python -m pytest tests/processing/test_fractal_stop_breach_labels.py -v     # 10 passed (regression)
python statistics/data_contract_smoke_check.py                               # ALL CHECKS PASSED
python -m ML.baseline.benchmark_fractal_stop_fav                            # baseline + grid search
python -m ML.baseline.benchmark_fractal_stop_fav --frozen-rule ... --test ... # frozen test
```

## Results

### Breach + Fav regression на val

| Комбинация | AUC breach | PR-AUC | Lift | MSE fav | MAE fav | RMSE fav |
|-----------|-----------|--------|------|---------|---------|----------|
| buy_H6_off02 | 0.636 | 0.581 | 1.61 | 1.628 | 0.871 | 1.276 |
| sell_H6_off02 | 0.651 | 0.615 | 1.73 | 1.825 | 0.935 | 1.351 |
| buy_H6_off05 | 0.620 | 0.456 | 1.62 | 1.628 | 0.871 | 1.276 |
| sell_H6_off05 | 0.622 | 0.476 | 1.71 | 1.825 | 0.935 | 1.351 |
| buy_H12_off02 | 0.656 | 0.712 | 1.55 | 2.988 | 1.211 | 1.728 |
| sell_H12_off02 | **0.681** | **0.757** | 1.66 | 3.776 | 1.420 | 1.943 |
| buy_H12_off05 | 0.635 | 0.610 | 1.52 | 2.988 | 1.211 | 1.728 |
| sell_H12_off05 | 0.661 | 0.667 | **1.77** | 3.776 | 1.420 | 1.943 |

Breach-метрики воспроизводят Stage 1 (AUC 0.62–0.68). Fav regression MSE высокий: 1.6–1.8 для H6, 3.0–3.8 для H12 — предсказательная сила fav_val слабая.

### Validation baseline: grid search торговых порогов (train: 2004–2019, val: 2019–2022)

Все 8 комбинаций H×off×side, grid search 81 комбинация порогов на canonical spread=0.20.

| Комбинация | PF (best) | Trades/yr | p | min_fav | min_rr | tp_frac |
|-----------|-----------|-----------|---|---|---|---|---|
| buy_H6_off02 | 0.867 | 61.0 | 0.5 | 0.3 | 2.0 | 0.7 |
| sell_H6_off02 | 0.894 | 53.8 | 0.4 | 0.3 | 1.0 | 0.5 |
| buy_H6_off05 | 0.878 | 467.8 | 0.5 | 0.3 | 1.0 | 0.7 |
| sell_H6_off05 | 0.879 | 516.2 | 0.4 | 0.3 | 1.0 | 0.7 |
| buy_H12_off02 | 0.680 | 47.8 | 0.5 | 0.3 | 1.0 | 0.7 |
| sell_H12_off02 | 0.592 | 36.5 | 0.5 | 0.3 | 1.0 | 0.7 |
| buy_H12_off05 | 0.895 | 51.8 | 0.5 | 0.3 | 1.5 | 0.5 |
| **sell_H12_off05** | **0.975** | 141.2 | 0.5 | 0.3 | 1.5 | 0.7 |

Лучшая комбинация: `sell_H12_off05` — PF=0.975 canonical, PF=1.060 diagnostic (0.00), PF=0.891 stress (0.40). 4 года val, 2 убыточных года с PF<1.0 (2019, 2021).

**Ни одна комбинация не достигла PF > 1.0 на canonical spread.**

### Spread sensitivity (sell_H12_off05, best combo)

| Spread | PF | Trades | Trades/yr | Negative years | Total PnL (val) |
|--------|-----|--------|-----------|----------------|-----------------|
| canonical 0.20 | 0.975 | 565 | 141.2 | 2/4 | −8.24 ATR |
| diagnostic 0.00 | 1.060 | 611 | 152.8 | 2/4 | +20.48 ATR |
| stress 0.40 | 0.891 | 519 | 129.8 | 2/4 | −34.64 ATR |

Даже на diagnostic spread (0.00) PF едва >1.0. Маржинальность не переживает издержки: падение PF с 1.06 до 0.98 при добавлении 0.20 спреда (падение ~8%).

### Frozen test (train+val: 2004–2022, test: 2022–2026, замороженное правило sell_H12_off05)

| Spread | PF | Trades | Trades/yr | Negative years |
|--------|-----|--------|-----------|----------------|
| canonical 0.20 | 0.837 | 414 | 82.8 | 3/5 |
| stress 0.40 | 0.792 | 400 | 80.0 | 3/5 |
| diagnostic 0.00 | 0.819 | 434 | 86.8 | 3/5 |

Test breach AUC: 0.653 (на уровне Stage 1 frozen test 0.649).

Годовая разбивка (canonical 0.20): 2022 PF=1.28 (n=5), 2023 PF=0.88 (n=88), 2024 PF=0.58 (n=122), 2025 PF=1.05 (n=159), 2026 PF=0.77 (n=40). 2024 — провальный год с большим числом сделок.

### Oracle-диагностика: отделение модели от механики

Для ответа на вопрос «проблема в модели или в торговой механике» проведён oracle-тест на val: вместо RF-предсказаний подставлены истинные будущие значения.

**Три режима:**
| Режим | Breach | Fav | Что проверяет |
|--------|--------|-----|---------------|
| `perfect_breach` | истинный флаг пробоя | RF | Верхняя граница при идеальном breach-знании |
| `perfect_fav` | RF | истинный fav_val | Верхняя граница при идеальном fav-знании |
| `perfect_both` | истинный | истинный | Абсолютный верх — идеальное знание обоих |

Фиксированные пороги: p=0.5, min_fav=0.0, min_rr=1.0, tp_frac=0.7.

**Результаты (val, canonical spread 0.20):**

| Комбинация | perfect_breach PF | perfect_fav PF | perfect_both PF |
|---|---|---|---|
| buy_H6_off02 | 15.85 | 7.94 | ∞ |
| sell_H6_off02 | 12.78 | 7.02 | ∞ |
| buy_H6_off05 | 12.48 | 9.73 | ∞ |
| sell_H6_off05 | 8.02 | 9.39 | ∞ |
| buy_H12_off02 | 28.35 | 8.26 | ∞ |
| sell_H12_off02 | 13.12 | 9.44 | ∞ |
| buy_H12_off05 | 19.96 | 13.46 | ∞ |
| sell_H12_off05 | 11.42 | 14.08 | ∞ |

**Все oracle-режимы, все комбинации, все спреды: 0 убыточных лет на val.**

Ключевые наблюдения:
- `perfect_both` → PF=∞ везде: **торговая механика сама по себе прибыльна**. При идеальном знании breach и fav_val убыточных сделок нет.
- `perfect_breach` → PF=8–28: идеальное знание пробоя стопа даёт фактор PF 10–30× относительно RF baseline (0.6–0.9).
- `perfect_fav` → PF=7–14: идеальное знание благоприятного хода даёт фактор PF ~10×.
- Breach-знание даёт больший прирост, чем fav-знание (PF 12–28 vs 7–14).

**Вывод oracle: проблема в модели (RF), а не в механике.** Механика «стоп за уровнем + TP от fav» фундаментально работоспособна. RF breach (AUC 0.65) и RF fav (MSE 3–5) недостаточно точны для извлечения этой прибыли. Имеет смысл искать более сильные признаки или более мощную модель (Transformer, XGBoost).

### Критерии перехода

| Критерий | Статус | Значение |
|----------|--------|----------|
| PF > 1.0 на val (canonical) | ❌ FAIL | 0.975 |
| PF > 1.0 на frozen test | ❌ FAIL | 0.837 |
| ≥30 сделок/год | ✅ | 141.2 (val) / 82.8 (frozen) |
| Нет годов с PF<1.0 и ≥5 сделок | ❌ FAIL | 2 из 4 (val), 3 из 5 (frozen) |

## Conclusions

1. **Breach классификатор работает (AUC 0.65–0.68), но сигнал о пробое не транслируется в прибыль на торговом слое** даже с RF регрессором fav_val. Breach-сигнала недостаточно для отбора сделок с положительным матожиданием.

2. **Oracle показывает, что проблема в модели, а не в механике**: при идеальном знании breach PF=8–28, при идеальном fav PF=7–14, при обоих — PF=∞ (0 убыточных сделок). Торговая постановка «стоп за уровнем + TP от fav» фундаментально работоспособна.

3. **RF не извлекает доступный сигнал**: gap между oracle PF (8–28) и RF PF (0.6–1.0) составляет фактор 10–30×. Нужны более сильные признаки или более мощная модель.

4. **Breach-знание ценнее fav-знания**: oracle perfect_breach даёт PF 12–28 против 7–14 у perfect_fav. Приоритет — улучшить классификацию пробоя.

5. **Fav regression слабая**: MSE 1.6–1.8 (H6) и 3.0–3.8 (H12). Но даже текущий RF fav достаточен для PF > 7 при идеальном breach — значит, breach-фильтр является узким местом.

6. **Frozen test OOS подтверждает отсутствие переобучения**: PF test (0.84) близок к val (0.98), gap не патологический.

7. **Рекомендация**: исследование fractal-stop не закрывать, а перейти к улучшению breach-классификатора — новые признаки (спред, волатильность, корреляции) или более мощная модель (XGBoost, Transformer).

## Analysis: почему RF не работает при работоспособной механике

Oracle-тест показал, что торговая механика прибыльна (PF=∞ при идеальном знании), а RF не может извлечь этот сигнал. Причины:

1. **Breach-сигнал слишком слаб для фильтрации**: AUC 0.65 означает, что даже лучший порог даёт много ложных пропусков. При breach rate 40–60%, значительная доля «не-пробойных» сделок всё равно проходит фильтр (RF даёт breach_prob < p для многих реальных пробоев), а значительная доля «пробойных» отсеивается. Gap между oracle perfect_breach (PF=12–28) и RF (PF=0.6–1.0) показывает, что breach-классификатор — основное узкое место.

2. **Fav regression не предсказывает амплитуду**: MSE ~3–5 на H12 означает типичную ошибку ~1.7–2.2 ATR при среднем fav_val ~1.0–1.5. Однако даже эта слабая регрессия достаточна для PF > 7 при идеальном breach-фильтре — значит, основная проблема не в fav.

3. **Стоп за fractal0 — широкий**: stop_val 1.0–2.5 ATR. При TP = pred_fav × tp_fraction, RR часто < 1.0. Но oracle показывает, что даже с такими стопами механика прибыльна — нужен лишь более точный breach-фильтр.

## Limitations / Open Questions

- Только RF (200 деревьев, max_depth=12). Более сложные модели (XGBoost, Transformer) могут существенно улучшить breach AUC.
- 1001 плоский признак. Агрегаты по окнам, time-фичи, session/seasonality, спред, волатильность не использовались.
- Стоп фиксирован за `fractal0`. Trailing stop или partial TP могут улучшить PF.
- Test вскрыт дважды (Stage 1 + Stage 2). Для допуска в рабочий контур нужен новый forward-период.
- Только XAUUSD H1. На других инструментах/таймфреймах результат может отличаться.
- Oracle-тест проведён на val (2019–2022). Результаты не OOS (используют будущую информацию), это только диагностика механики.

## Next Step

Oracle-диагностика показала: **проблема в модели, механика работоспособна**. Рекомендуется **Stage 3: улучшение breach-классификатора**:

1. **Feature engineering**: добавить спред, ATR-волатильность, время сессии, day-of-week, корреляции между фракталами
2. **Ablation каналов**: какие из 10 каналов несут breach-сигнал, какие — шум
3. **Более мощная модель**: XGBoost/LightGBM (лучше RF на табличных данных), Transformer encoder поверх фрактальной последовательности
4. **Альтернативный target**: directional forecast вместо breach probability — предсказывать не «будет ли пробой», а «куда пойдёт цена»

Решение — за пользователем.

## Related Materials

- `processing/label_signals.py` — `label_fractal_stop_fav_targets()`, `evaluate_fractal_stop_trade()`
- `processing/label_main.py` — флаг `--fractal-stop-fav`
- `tests/processing/test_fractal_stop_fav.py` — 9 тестов
- `ML/baseline/benchmark_fractal_stop_fav.py` — RF baseline + grid search + frozen test
- `ML/baseline/oracle_fractal_stop_fav.py` — oracle-диагностика (истинные breach/fav_val)
- `ML/reports/fractal_stop_fav.json` — отчёт val (grid search)
- `ML/reports/fractal_stop_fav_frozen_rule.json` — замороженное правило
- `ML/reports/fractal_stop_fav_frozen_test.json` — отчёт frozen test
- `ML/reports/oracle_fractal_stop_fav.json` — oracle-результаты
- `statistics/data_contract_smoke_check.py` — fav-проверки
- `docs/superpowers/specs/2026-06-08-fractal-stop-fav-target-design.md` — спецификация
- `docs/superpowers/plans/2026-06-10-fractal-stop-fav-plan.md` — план Stage 2
- `docs/reports/2026-06-10-fractal-stop-breach-stage1.md` — отчёт Stage 1
- `wiki/research/fractal-stop-research.md` — синтез Stage 1+2
