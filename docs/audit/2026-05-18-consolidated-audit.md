# Консолидированный аудит: Direct Direction Improvement (E0–E5)

> **Дата**: 2026-05-18
> **Источники**:
> - `docs/archive/answer.md` — скорректированный промпт для аудита
> - `docs/audit/2026-05-18-codex-direct-direction-chain-audit.md` — аудит цепочки Codex
> - `docs/audit/2026-05-18-kimi-independent-audit.md` — независимый аудит Kimi
> **Статус**: Завершён, all findings confirmed by ≥2 sources

---

## 0. Контекст

Этап `2026-05-15-direct-direction-improvement` (эксперименты E0–E5) ставил целью улучшить предсказание направления входа (BUY/SELL) на fractal-level признаках. Лучший кандидат (Binary RF) показал:

| Метрика | Значение |
|---------|----------|
| Test PF | 1.226 |
| Test Seq PF | 1.537 |
| BUY PF | 1.904 |
| SELL PF | 0.618 |
| Негативные годы | 2022, 2023 |

Результат признан неудовлетворительным: SELL направление убыточно, целевой PF > 2.0 не достигнут. Проведены два независимых аудита (Codex, Kimi), объединённые ниже.

---

## 1. Критические ошибки (подтверждены обоими аудитами)

### 1.1. Нарушение протокола: frozen test не соответствует validation winner

**Codex**: `summary.json` содержит winner `D_hgb_buy0.30_sell0.60_m0.05_standalone` (HGB, one-sided, balance=0.09), но frozen test выполнен для `D_rf_buy0.40_sell0.60_m0.10` (RF, balanced). Код `pick_validation_winner()` не исключает `one_sided_candidate`, не фильтрует по `negative_years == 0` и сортирует по `validation_pf` раньше `validation_sequential_pf`.

**Kimi**: Прямое цитирование плана: "Select the single best validation winner... freeze its configuration and run **one** frozen test." Результат frozen test не соответствует строгому протоколу; HGB отброшен как one-sided, но frozen test запущен для другой конфигурации без явной документации выбора.

**Вывод**: Selection layer не является механически воспроизводимым. Frozen test не может служить доказательством качества модели, поскольку winner selection не documentирован.

### 1.2. SELL систематически хуже случайного выбора

**Codex**: SELL PF на frozen artifact убыточен почти по всем годам. Любая SELL repair гипотеза должна заново проходить validation-only selection.

**Kimi** (с доказательствами):
- Random SELL precision baseline = 1745/9415 = **0.185**
- Model SELL precision = 129/843 = **0.153**
- Разница: **−0.032** — модель генерирует anti-signal для SELL
- Инверсия калибровки: SELL prob [0.5, 0.7): win_rate=0.413; prob [0.7, 1.0]: win_rate=**0.376**

**Вывод**: SELL-сигнал не просто слабый — он активно вредит. Чем увереннее модель в SELL, тем вероятнее убыток. Лечить SELL подбором порогов (threshold/margin) нельзя.

### 1.3. Признаки не несут направленческой информации

**Codex**: Feature importance E0 показывает топ-признаки front/back/impulse. `fractal0_direction` не является одновременно входом и таргетом, но content-связь признаков с направлением движения не установлена.

**Kimi** (с доказательствами):
- Top-20 feature importance для BUY и SELL **идентичны**: `nearest_02_impulse`, `nearest_00_front`, `nearest_03_front`, `nearest_02_front`, `nearest_01_back`
- `fractal0_direction` — **20-е место** (importance ~1.5%)
- Feature builder не создаёт направленчески-специфичных признаков; признаки описывают «структуру вокруг уровня», но не «куда пойдёт цена»

**Вывод**: Модель использует одни и те же геометрические паттерны для обоих направлений, не различая их. При нынешнем наборе признаков модель не может научиться direction-specific сигналу.

### 1.4. BUY сигнал маргинально лучше случайного

**Kimi** (подтверждается данными Codex):
- Random BUY precision = 2416/9415 = **0.257**
- Model BUY precision = 340/1202 = **0.283**
- Edge: +0.026 (~10% относительно)
- Recall = 14.1% (модель находит лишь 1/7 всех возможных хороших BUY)

**Вывод**: BUY-сигнал существует, но крайне слабый. PF=1.90 достигается за счёт удачного совпадения с bull-режимом золота на test, а не за счёт качества модели.

---

## 2. Дополнительные ошибки (Codex — уникальные)

### 2.1. Target-dependent normalization (нормализация, зависящая от таргета)

`processing/normalize.py` нормализует фрактальные `Up/Dn` в общем пуле с top-level target columns `up_3..dn_48`. Минимальная проверка показала:

```
top_level_only_changed=True
fractal1_equal=False
changed_fields=up_12,dn_12,up_24,dn_24,up_48,dn_48
```

**Следствие**: даже если top-level targets не подаются в модель напрямую, они влияют на масштаб фрактальных `Up/Dn` признаков. Для direct-direction моделей, построенных из уже нормализованных `DATA/Nero_*_labeled.csv`, feature provenance небезопасен.

### 2.2. Неверные единицы расстояния в fractal-level features

`ML/fractal_level_feature_builder.py` вычисляет:
```
(fractal.price - fractal0.price) / ATR
```
Но в split CSV `price` уже rowwise min-max normalized, а `ATR` остаётся в сырой шкале.

**Следствие**: ломается физический смысл `raw_distance_atr`, nearest-k и zone features. Особенно критично для zone features — они строятся на искажённой геометрии.

### 2.3. A/C targets используют normalized up/dn как ATR-значения

`ML/entry_path_direct_direction_targets.py` строит `buy_fav_*_atr` и `sell_fav_*_atr` из top-level `up/dn` split CSV. Эти значения уже нормализованы, а не выражены в ATR. Target D (по OHLC) менее затронут, но вся A/C часть target grid некорректна без пересчёта из raw или OHLC.

---

## 3. Дополнительные ошибки (Kimi — уникальные)

### 3.1. Таргет (trailing profit) чрезмерно шумный

- BUY precision = 28.3%, recall = 14.1% — 86% хороших BUY модель пропускает
- SELL precision = 15.3%, recall = 7.4% — 93% хороших SELL модель пропускает
- Trailing stop срабатывает случайно из-за внутридневной волатильности
- 24-баровый горизонт пересекается с рыночным шумом

**Вывод**: trailing-profit — слишком «жёсткий» таргет. Модель обучается на шуме, а не на сигнале.

### 3.2. Режимная нестабильность

- Test period начинается с конца 2022 (начало bull run золота)
- SELL PF по месяцам 2022: октябрь 0.000, ноябрь 0.256, декабрь 0.066
- BUY PF по годам: 2022=0.65, 2023=1.09, 2024=2.49, 2025=2.00, 2026=2.62
- Статическая модель на 15-летнем train не переносится на резкий regime shift

### 3.3. Асимметрия данных

- `up_24 > dn_24` в 54.3% случаев на test; на горизонте 48 баров — 55.6%
- Trailing profit симметричен по построению, но рынок не симметричен
- SELL trailing stop срабатывает быстрее в bull market (adverse move превышает trail_n × ATR)

---

## 4. Структурные слабости (оба аудита)

| Проблема | Codex | Kimi |
|----------|-------|------|
| Winner selection не автомат.воспроизводим | ✅ | ✅ |
| SELL < baseline, не чинить test-порогами | ✅ | ✅ |
| Признаки без direction-сигнала | ✅ (feature provenance) | ✅ (идентичная importance) |
| Нормализация смешивает target/feature | ✅ | — |
| Неверные единицы расстояния | ✅ | — |
| Trailing profit target шумный | — | ✅ |
| Regime instability | — | ✅ |
| Feature builder игнорирует fractal0_direction | — | ✅ |
| E5 score-direction conclusion недоказан | ✅ | — |
| HGB skew-сигналы не проанализированы | — | ✅ |
| Calibration inversion (SELL) | — | ✅ |
| ASYM-данные (up_24 > dn_24 систематически) | — | ✅ |

---

## 5. Корневые причины слабого результата

1. **Feature-in-target contamination**: нормализация фрактальных признаков зависит от таргетов этой же строки
2. **Геометрия в неверных единицах**: расстояние считается от нормализованной цены, делённой на сырой ATR
3. **Отсутствие direction-специфичных признаков**: BUY и SELL получают одни и те же входы
4. **Шумный таргет**: trailing profit на 24 барах — плохая обучающая цель
5. **Один train/val/test split**: нет оценки стабильности по режимам
6. **SELL anti-signal**: модель систематически предсказывает убыточные SELL

---

## 6. Что нужно исправить (приоритеты)

### Обязательно (критические)
1. **Feature provenance**: перестроить fractal-level признаки из raw/current-row source, а не из нормализованного split CSV
2. **Протокол выбора winner**: frozen test строго соответствует validation winner; документировать причину отклонения
3. **Отказ от SELL в текущей архитектуре**: SELL хуже случайного; переход на BUY-only interim baseline (PF повышается с 1.23 до ~1.90)
4. **Исправить единицы расстояния**: найти правильный знаменатель (raw ATR из оригинальной строки)

### Высокий приоритет
5. **Alternative target**: заменить trailing-profit на более стабильный (directional close, фиксированный hold return)
6. **Direction-specific признаки**: добавить явное кодирование направления (fractal0.direction), momentum, trend strength
7. **Regime-aware признаки**: волатильностный режим, сила тренда, временные паттерны

### Средний приоритет
8. **Walk-Forward Validation** вместо единого split для оценки стабильности
9. **Transformer feature extractor**: использовать `transformer_updn_best.pt` (r=0.56) для извлечения hidden representations
10. **Калибровка вероятностей** (Platt / isotonic) перед пороговым решением
11. **BUY-only отдельная модель** — одна модель для BUY vs SKIP, не пытаясь предсказывать оба направления

### Низкий приоритет (если время останется)
12. Conformal Prediction для SELL (только если SELL всё же нужен)
13. Другие модели: XGBoost/LightGBM с monotonic constraints, CatBoost
14. Ансамбли: stacking/blending fractal-level + Transformer

---

## 7. Анти-паттерны (что НЕ делать)

- Не подбирать пороги как «решение» (косметика)
- Не использовать test split для подбора гипотез/параметров/моделей
- Frozen test — **только один раз** для финального кандидата
- Не повторять 3-class формулировку (нежизнеспособна, доказано)
- Не пытаться «подлатать» SELL фильтрацией — если SELL PF<<1.0 фундаментально, лучше BUY-only
- Не запускать model sweeps до исправления feature provenance (Gate 1)

---

## 8. Рекомендуемый план работ

### Phase A: BUY-only baseline
1. Исправить feature provenance (raw source, правильные единицы)
2. Alternative target (directional close или фиксированный hold return)
3. BUY-only модель (BUY vs SKIP)
4. Walk-Forward Validation
5. Gate: validation PF > 1.5, sequential PF > 1.5

### Phase B: Улучшение признаков
6. Regime-aware признаки (тренд/флэт по скользящей трендовой силе)
7. Direction-specific признаки (fractal0.direction как вход)
8. `pred_ret_24_dir_atr` от Transformer как входной признак
9. Gate: validation PF > 1.5 (или улучшение относительно Phase A)

### Phase C: Transformer feature extractor
10. Использование `transformer_updn_best.pt` для извлечения hidden representations
11. Лёгкий классификатор поверх энкодера
12. Gate: validation PF > 2.0, sequential PF > 2.0

### Phase D: Frozen test
13. Единственный frozen test для лучшего кандидата
14. Gate: test PF > 1.5, не более 1 негативного года

**Если ни одна фаза не проходит gate — честный вердикт**: текущая постановка задачи (fractal-level direction prediction на H1 XAUUSD) не позволяет достичь PF>2.0 без новых источников данных.

---

## 9. Ограничения консолидированного аудита

- Не проверена MQL4 сторона (lib_PIC.mqh, эксперт) — предполагается корректной
- Не проверен processing pipeline на полную parity raw→normalized
- Не проведён полный cross-instrument robustness анализ для BUY-only варианта
- Legacy regression_updn не перепроверялся

---

**Источники**:
- `docs/archive/answer.md` — скорректированный промпт
- `docs/audit/2026-05-18-codex-direct-direction-chain-audit.md` — аудит Codex
- `docs/audit/2026-05-18-kimi-independent-audit.md` — аудит Kimi
- `ML/reports/entry_path_v1_binary_direction/` — артефакты экспериментов
- `ML/reports/direct_direction_chain_audit/minimal_repro_checks.json` — проверки воспроизводимости
