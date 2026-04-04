# Signal Quality Filter Research (Variant 4) — Design Spec

> **Date**: 2026-04-03
> **Status**: Draft
> **Goal**: Исследовать, могут ли multi-horizon predictions модели (up_3..dn_48) дать более точный фильтр качества сигнала, чем текущий ratio_12
> **Approach**: feature engineering → univariate response maps → shallow tree → score → holdout validation

## Context

Variant 2/3 исследования показали:
- ML-сигнал — слабый дрейф, не импульс (`baseline PF=1.05` при `12H/SL=5/TP=50`)
- `ratio_12` bucket `4-5` — лучший, `3-4` — устойчивый анти-паттерн
- `Filter3/Filter6` как ratio-threshold бесполезны: 96% сигналов имеют `ratio_3 > 5.0`
- Лучший Variant 3 кандидат: `ratio 4-5 × ATR Q4 + pullback entry_close-2ATR` (`PF=3.69`, `36` fills)

Текущий фильтр (`ratio_12` bins) использует только один горизонт. Модель предсказывает 10 значений (`up_3..dn_48`), и комбинации горизонтов могут дать лучшую фильтрацию.

## New Script

`API/signal_quality_research.py` — отдельный research tool.

- Импортирует данные из того же pipeline (`ml_signals.csv` + `XAUUSD_H1_OHLC.csv`)
- Переиспользует data loading / merge / excursion logic из `signal_research.py` где возможно
- Фокусируется на feature-based фильтрации, а не на entry mechanics
- CLI: `python -m API.signal_quality_research` / `python -m API.signal_quality_research --test-only`

## Filter Feature Families

Три оси исследования. Все features — direction-aware (`pred_fav`/`pred_adv`, не raw `up`/`dn`).
Скрипт самостоятельно вычисляет `pred_fav_h`/`pred_adv_h` для всех 5 горизонтов (`h ∈ {3, 6, 12, 24, 48}`), не зависит от маппинга в `signal_research.py` (там покрыты только `h=3,6,12`).

### 1. `ratio_h` — сила сигнала по горизонтам
```
ratio_h = pred_fav_h / (pred_adv_h + 1e-6)
h ∈ {3, 6, 12, 24, 48}
```

### 2. `spread_h` — абсолютная разница fav/adv
```
spread_h = pred_fav_h - pred_adv_h
h ∈ {3, 6, 12, 24, 48}
```

### 3. `short_vs_long` — divergence коротких vs длинных горизонтов
```
ratio_3_vs_12  = ratio_3 / (ratio_12 + 1e-6)
spread_3_vs_12 = spread_3 / (spread_12 + 1e-6)
fav_3_vs_12    = pred_fav_3 / (pred_fav_12 + 1e-6)
ratio_6_vs_24  = ratio_6 / (ratio_24 + 1e-6)
spread_6_vs_24 = spread_6 / (spread_24 + 1e-6)
ratio_12_vs_48 = ratio_12 / (ratio_48 + 1e-6)
spread_12_vs_48 = spread_12 / (spread_48 + 1e-6)
```
Пары `3_vs_12` могут быть убиты в Step 0 из-за низкой дисперсии `ratio_3`; пары `6_vs_24` и `12_vs_48` добавлены как запасные.

## Response Variables (не фильтры)

Post-signal path features используются **только как response metrics** для оценки качества фильтров, а не как filter candidates (в момент сигнала они неизвестны).

```
fav_k_atr = fav_k / atr14    для k ∈ {1, 3, 6}
adv_k_atr = adv_k / atr14    для k ∈ {1, 3, 6}
net_12_atr = net_12 / atr14
```

## Research Steps (CLI Report Sections)

### Step 0 — Feature Variance Check

Для каждого feature из 4 семейств:
- `mean`, `std`, `Q10`, `Q50`, `Q90`
- `unique_ratio` = число уникальных quantile bins с >= 5% данных / общее число bins

**Kill criterion** (по типу feature):
- ratio-type (`ratio_h`, `short_vs_long` ratios): `std < 1% * |mean|` или `>90%` значений в одном bin
- spread-type (`spread_h`, `short_vs_long` spreads): `std < 0.01 * IQR` или `>90%` значений в одном bin
- Любой feature с `>90%` значений в одном quantile bin — мёртв, исключается из дальнейшего анализа.

### Step 1 — Discovery / Holdout Split

- Discovery: сигналы с `time <= 2024-12-31` (~60% от 2603)
- Holdout: сигналы с `time > 2024-12-31` (~40%)
- **Guard**: если `N_discovery < 1000` или `N_holdout < 400` — abort с предупреждением
- Все Steps 2-4 используют **только discovery**
- Holdout трогается **один раз** в Step 5

Вывод: `N_discovery`, `N_holdout`, `date_ranges`, `BUY/SELL` balance в каждой части.

### Step 2 — Univariate Response Maps

Для каждого живого feature (прошедшего Step 0), **только на discovery set**:
- 5-10 quantile bins (точное число адаптируется к N)
- Для каждого bin: `PF`, `N`, `trades/year`, `net_ATR`, `fav_ATR`, `adv_ATR`
- `uplift` = `PF_bin - PF_baseline` (baseline = PF на всём discovery set)

Вывод: таблица per feature, sorted by PF descending.

### Step 3 — Shallow Tree Discovery

- Depth-2 `DecisionTreeClassifier` на discovery set
- Target: `net_12 > 0` (binary profitable/unprofitable)
- Features: все живые features из Step 0
- Output: tree structure (splits + thresholds), feature importances, leaf statistics (`N`, `PF`, `net_ATR`)

Цель: автоматически найти лучшие 2-3 split-а и их взаимодействия без ручного bias.

### Step 4 — Pairwise Combinations

Источники кандидатов:
- top splits из depth-2 tree (Step 3)
- top univariate bins с `PF > baseline + 0.1` и `N >= 30` (Step 2)

Для каждой pairwise комбинации (max 15):
- `PF`, `N`, `net_ATR`, `fav_ATR / adv_ATR`
- `uplift vs baseline`
- `uplift vs negative controls`: применить то же filter-правило к cohort `ratio_12 ∈ [3, 4)` и к cohort `ATR not in Q4` (квартили ATR считаются на discovery set). Filter проходит, если `PF_filter_on_primary - PF_filter_on_negative > 0`

### Step 5 — Score Construction & Holdout Validation

Из выживших features (positive uplift + N >= 56 на discovery):
- Нормализация: rank-based (percentile), `f_norm = rank(f) / N` — устойчива к outliers, не требует assumptions о распределении
- Simple additive score: `score = w1 * f1_norm + w2 * f2_norm + ...`
- Weights: equal или proportional to univariate uplift (не ML-fitted)
- Test top `10%`, `15%`, `20%`, `25%` score quantiles на discovery

Лучший вариант (max PF при N >= 56) → **один раз** на holdout:
- Holdout `PF > baseline PF` = confirmed
- Holdout `PF <= baseline PF` = not reproducible

## Final Selection Criteria

Кандидат проходит, если одновременно:
1. `N >= 56` (hard floor, ~15 trades/year)
2. `PF_holdout > PF_baseline`
3. `uplift vs negative controls > 0` (правило не работает на `ratio 3-4` / `non-Q4`)
4. Year stability: fills не сконцентрированы в одном кластере

## Constraints

- Не меняем EA
- Не меняем `signal_research.py`
- Pairwise комбинаций ≤ 20 (Step 4)
- Score — только simple additive, не ML-модель поверх модели
- Holdout трогается один раз

## Output

3-5 кандидатов-фильтров, каждый в форме короткого правила:
```
Пример: ratio_12 > 4.2 AND spread_12 > 15.0
```
С метриками: `PF_discovery`, `PF_holdout`, `N`, `uplift vs controls`, `year stability`.

## Data Sources

- `MT/MQL4/Files/ml_signals.csv` — predictions (10 cols: `up_3..dn_48`)
- `DATA/XAUUSD_H1_OHLC.csv` — OHLC + `atr14`
- Excursion data computed inline (same logic as `signal_research.py`)

## Related Materials

- [docs/reports/2026-04-02-signal-research-variant-3.md](../../reports/2026-04-02-signal-research-variant-3.md)
- [docs/reports/2026-04-02-signal-research-variant-3-prep.md](../../reports/2026-04-02-signal-research-variant-3-prep.md)
- [docs/reports/2026-04-01-signal-research-variant-2.md](../../reports/2026-04-01-signal-research-variant-2.md)
