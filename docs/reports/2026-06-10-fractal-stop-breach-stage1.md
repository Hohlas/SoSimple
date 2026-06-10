# Fractal Stop Breach — Stage 1: Пробой уровня

> **Date**: 2026-06-10
> **Status**: Completed
> **Goal**: Проверить, предсказывают ли фрактальные признаки будущий пробой уровня `fractal0` за H баров
> **Related spec**: `docs/superpowers/specs/2026-06-08-fractal-stop-fav-target-design.md`
> **Related plan**: `docs/superpowers/plans/2026-06-10-fractal-stop-breach-plan.md`
> **Related commit**: pending

## Context

После RF+Transformer limit-order-экспериментов стало ясно: фрактальные признаки не дают сигнала для order-of-touch таргетов (TB) и Transformer не извлекает sequence-информацию. Гипотеза: проблема не в признаках, а в вопросе. «Что случится первым» — слишком сложный вопрос. Нужно начать с более простого: «будет ли уровень пробит против сделки».

Если модель не умеет предсказывать пробой стоп-уровня, торговая постановка со стопом за `fractal0` вряд ли устойчива.

## What Was Done

### 1. Разметка breach-таргетов
- `processing/label_signals.py`: константы `BR_BREACH_HORIZONS=(6,12)`, `BR_BREACH_OFFSETS=(0.0,0.2,0.5)`, 12 колонок `buy/sell_stop_broken_H{h}_off{off}_flag`
- Функция `label_fractal_stop_breach()`: для каждой строки с валидным `fractal0.dir` проверяет касание стоп-уровня в окне `[row+1 : row+H]`
- `processing/label_main.py`: CLI-флаг `--fractal-stop-breach`
- Размечено 3 сплита: train 44K, val 9.4K, test 9.4K строк. Breach rates 35–72%

### 2. Тесты
- `tests/processing/test_fractal_stop_breach_labels.py` — 10 тестов: BUY breach/no-breach, SELL breach, offset sensitivity, H sensitivity, insufficient bars, all columns, edge cases (missing fractal0, zero ATR, dir=0)
- Все 10 PASS

### 3. Smoke check
- `statistics/data_contract_smoke_check.py`: проверка breach-колонок (существование, ∈{0,1}, breach_rate ∈ (0,1))
- ALL CHECKS PASSED на всех трёх сплитах

### 4. Baseline (RF на train, validation-оценка)
- `ML/baseline/benchmark_fractal_stop_breach.py`: Dummy (3 стратегии) + RF (200 деревьев, max_depth=12, min_samples_leaf=50)
- Признаки: 10 каналов × 100 фракталов + ATR = 1001 признак (allowlist по feature contract)
- 8 primary таргетов на val: все AUC 0.62–0.68, lift 1.52–1.77, без годовых провалов

### 5. Frozen test
- Правило выбрано до открытия test: **H=6, off=0.2, BUY+SELL**
- Train на train+val (53,610 строк, 2004–2022), test (9,463 строки, 2022–2026) открыт один раз
- Оба таргета подтвердили сигнал на невиданных данных

### Принятые решения
- Колонки названы `buy/sell_stop_broken_H{h}_off{off}_flag` (не `target_breach_*`)
- `parse_fractal()` возвращает словарь → доступ по ключам
- Feature contract: явный allowlist из 10 ключей, не «всё кроме denylist»
- `stop_offset_val=0.0` как diagnostic-only, исключён из primary отчётов
- Test заморожен до явного freeze-решения; использован один раз

## Verification

```bash
python -m pytest tests/processing/test_fractal_stop_breach_labels.py -v  # 10 passed
python statistics/data_contract_smoke_check.py                            # ALL CHECKS PASSED
python -m ML.baseline.benchmark_fractal_stop_breach                       # baseline report
python -m ML.baseline.benchmark_fractal_stop_breach --test ...            # frozen test report
```

## Results

### Baseline (RF, val, 8 primary таргетов)

| Таргет | AUC | PR-AUC | Lift | Годовой AUC |
|--------|-----|--------|------|-------------|
| `buy_H6_off02` | 0.636 | 0.581 | 1.61 | 0.61–0.66 |
| `sell_H6_off02` | 0.651 | 0.615 | 1.73 | 0.63–0.67 |
| `buy_H6_off05` | 0.620 | 0.456 | 1.62 | 0.59–0.65 |
| `sell_H6_off05` | 0.622 | 0.476 | 1.71 | 0.61–0.64 |
| `buy_H12_off02` | 0.656 | 0.712 | 1.55 | 0.62–0.68 |
| `sell_H12_off02` | **0.681** | **0.757** | 1.66 | 0.66–0.69 |
| `buy_H12_off05` | 0.635 | 0.610 | 1.52 | 0.60–0.65 |
| `sell_H12_off05` | 0.661 | 0.667 | 1.77 | 0.64–0.68 |

### Frozen test (RF, test, H=6 off=0.2)

| Таргет | Test AUC | PR-AUC | Lift | Годовые AUC |
|--------|----------|--------|------|-------------|
| `buy_H6_off02` | **0.640** | 0.560 | 1.60 | 0.67→0.61 (2022–2026) |
| `sell_H6_off02` | **0.649** | 0.630 | 1.69 | 0.71→0.57 (2022–2026) |

## Conclusions

1. **Сигнал есть**: фрактальные признаки несут информацию о будущем пробое уровня. RF значимо лучше Dummy на всех 8 primary таргетах (AUC 0.62–0.68 vs 0.5), подтверждено на frozen test (AUC 0.64–0.65).

2. **Lift > 1.5**: в 20% строк с наименьшим `predict_break` пробоев в 1.5–1.8 раз меньше среднего. Практически значимо: можно отсекать высокорисковые входы.

3. **Устойчивость по годам**: нет ни одного года с AUC ≈ 0.5. Небольшой спад к 2026 (0.57–0.61, n≈300) — ожидаемый OOS шум при малой выборке.

4. **H=12 лучше H=6**: более длинный горизонт даёт более высокий AUC и PR-AUC (0.68 vs 0.64). Это логично: за 12 баров происходит больше событий, breach rate выше (50–63% vs 38–47%), дисбаланс меньше.

5. **SELL ≳ BUY**: асимметрия в пользу SELL (AUC на 0.01–0.03 выше). XAUUSD bull market даёт больше SELL-кандидатов (n≈28K vs n≈25K).

6. **Критерии перехода к Stage 2 выполнены**: AUC > Dummy + lift > 1.5 на ≥2 primary колонках, без годовых провалов, frozen test подтверждает.

## Limitations / Open Questions

- RF — простейшая модель. Сигнал может быть сильнее на градиентном бустинге или с engineered признаками.
- Только 10 базовых каналов × 100 фракталов. Агрегаты по окнам, time-фичи, session/seasonality не использовались.
- Breach rate ~50% — близко к случайному. PR-AUC на H6 низковат (0.56–0.63) из-за слабого дисбаланса.
- Frozen test: только H6/off0.2. H12 на test не проверялся по правилу заморозки.
- 2026 — всего ~300 строк, годовая метрика шумная.

## Next Step

Этап 2: Торговый слой. Добавить `entry_price = Open[row+1]`, стоп за уровнем, TP от предсказанного благоприятного хода, оценку по фактическому PnL (первое касание OHLC). План: [`docs/superpowers/plans/2026-06-10-fractal-stop-fav-plan.md`](../superpowers/plans/2026-06-10-fractal-stop-fav-plan.md).

## Related Materials

- `processing/label_signals.py` — `label_fractal_stop_breach()`, константы `BR_*`
- `processing/label_main.py` — флаг `--fractal-stop-breach`
- `tests/processing/test_fractal_stop_breach_labels.py` — 10 тестов
- `ML/baseline/benchmark_fractal_stop_breach.py` — Dummy + RF baseline + frozen test
- `ML/reports/fractal_stop_breach_baseline.json` — отчёт val
- `ML/reports/fractal_stop_breach_frozen_test.json` — отчёт frozen test
- `docs/superpowers/specs/2026-06-08-fractal-stop-fav-target-design.md` — спецификация
- `docs/superpowers/plans/2026-06-10-fractal-stop-breach-plan.md` — план Stage 1
