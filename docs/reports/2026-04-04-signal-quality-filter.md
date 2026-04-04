# Signal Quality Filter Research (Variant 4)

> **Date**: 2026-04-04
> **Status**: Completed
> **Goal**: Исследовать, могут ли multi-horizon predictions модели (up_3..dn_48) дать более точный фильтр качества сигнала, чем текущий ratio_12, и скрестить лучшие фильтры с pullback entry из Variant 3
> **Related plan/spec**: [docs/superpowers/specs/2026-04-03-signal-quality-filter-claude.md](../superpowers/specs/2026-04-03-signal-quality-filter-claude.md), [docs/superpowers/plans/2026-04-03-signal-quality-filter.md](../superpowers/plans/2026-04-03-signal-quality-filter.md)
> **Related commit**: pending

## Context

Variant 2/3 показали, что ratio_12 — единственный используемый фильтр качества сигнала, а Filter3/Filter6 как ratio-threshold бесполезны (96% сигналов имеют ratio_3 > 5.0). Модель предсказывает 10 значений (up_3..dn_48), и комбинации горизонтов потенциально могут дать лучшую фильтрацию. Лучший Variant 3 кандидат (`ratio 4-5 × ATR Q4 + pullback entry_close-2ATR`, PF=3.69, 36 fills) имел medium-support.

Это исследование построено как гибрид score/ranking + shallow tree + explicit holdout validation, с разделением OOS на discovery (до 2024-12-31) и holdout (2025+).

## What Was Done

- Создан новый standalone research tool `API/signal_quality_research.py` с 6-step pipeline
- Реализованы 3 filter feature families (17 features):
  - `ratio_h` (5): pred_fav_h / pred_adv_h для h ∈ {3,6,12,24,48}
  - `spread_h` (5): pred_fav_h - pred_adv_h
  - `short_vs_long` (7): ratio/spread divergence между горизонтами (3v12, 6v24, 12v48)
- Реализован полный pipeline: variance check → discovery/holdout split → univariate response maps → depth-2 decision tree → pairwise combinations с negative control check → score construction + holdout validation
- Добавлены year-stability split и direct holdout тест для индивидуальных правил
- Добавлен cross-analysis: quality filters × pullback entry scenarios (market, entry_close-1/2/3ATR) на discovery и holdout отдельно
- Создан `tests/test_signal_quality_research.py` (19 тестов)

## Changed Files

- `API/signal_quality_research.py` (создан)
- `tests/test_signal_quality_research.py` (создан)
- `docs/superpowers/specs/2026-04-03-signal-quality-filter-claude.md`
- `docs/superpowers/specs/2026-04-03-signal-quality-filter-design.md`
- `docs/superpowers/plans/2026-04-03-signal-quality-filter.md`

## Verification

```bash
./.venv/bin/python -m pytest tests/test_signal_quality_research.py -q   # 19 passed
./.venv/bin/python -m pytest tests/test_signal_research.py -q           # 31 passed (no regressions)
./.venv/bin/python -m API.signal_quality_research --test-only           # full pipeline, no crashes
```

## Results

### OOS coverage

- 2603 real BUY/SELL signals (OOS 2022-07-18 — 2026-03-20)
- Discovery: 1751 signals (до 2024-12-31), BUY 51.6%
- Holdout: 852 signals (2025+), BUY 55.3%

### Step 0 — Feature Variance Check

Все 17 features прошли kill criterion (ни один не убит). Ожидалось, что ratio_3 будет flat, но его дисперсия оказалась достаточной (mean=200, std=9419), хотя `spread_3_vs_12` и `spread_12_vs_48` имеют узкий диапазон (std≈0.03-0.04).

### Step 2 — Univariate Response Maps: top features

| Feature | Best bin PF | Uplift | N |
|---------|---:|---:|---:|
| `ratio_3_vs_12` (low bin) | 1.43 | +0.43 | 351 |
| `ratio_12_vs_48` (low bin) | 1.34 | +0.35 | 351 |
| `spread_3` (mid bin) | 1.32 | +0.33 | 350 |
| `spread_12` (mid bin) | 1.30 | +0.30 | 350 |
| `ratio_3` (low bin) | 1.28 | +0.29 | 351 |

Важная находка: **низкий `ratio_3_vs_12`** (ratio_3 / ratio_12 < 2.99) даёт PF=1.43 на 351 сигнале — когда ratio_3 непропорционально ниже ratio_12, сигнал сильнее.

### Step 3 — Shallow Tree: `fav_3_vs_12` доминирует

Дерево поставило 100% importance на `fav_3_vs_12` (pred_fav_3 / pred_fav_12). Лучший лист: `fav_3_vs_12 ∈ (0.625, 0.653]` → 172 сигнала, PF=1.98, win_rate=62.2%.

Интерпретация: сигнал лучше, когда краткосрочный favorable move (3H) составляет 63-65% от среднесрочного (12H) — не слишком "выстреливший", не слишком слабый.

### Step 5 — Score-based holdout: в основном NOT CONFIRMED

Additive score из top-3/top-5 univariate features не дал устойчивого результата: 7 из 8 вариантов NOT CONFIRMED. Score-подход на этих данных не работает.

### Step 7 — Direct holdout отдельных правил

| Rule | N_disc | PF_disc | N_hold | PF_hold | Confirmed |
|------|---:|---:|---:|---:|:---:|
| `ratio_6 > 4.41 AND fav_3_vs_12 <= 0.653` | 137 | 1.81 | 52 | 3.48 | YES |
| `fav_3_vs_12 <= 0.653` | 194 | 1.65 | 84 | 2.11 | YES |
| `fav_3_vs_12 <= 0.656` | 214 | 1.35 | 94 | 1.79 | YES |
| `ratio_3_vs_12 > 4.751` | 352 | 1.15 | 160 | 1.49 | YES |
| `ratio_6_vs_24 > 3.054` | 351 | 1.13 | 127 | 1.46 | YES |
| `spread_12 > 0.276` | 705 | 1.12 | 423 | 1.40 | YES |
| `ratio_12_vs_48 > 2.458` | 353 | 1.14 | 127 | 0.99 | NO |

### Step 6 — Year stability

`fav_3_vs_12 <= 0.653` — тренд деградации на discovery (2022: PF=3.72, 2023: PF=2.02, 2024: PF=1.02), но holdout (2025+) PF=2.11 — edge вернулся.

`ratio_6 > 4.41 AND fav_3_vs_12 <= 0.653` — стабильнее: 2022: PF=2.36, 2023: PF=1.75, 2024: PF=1.64.

`ratio_3_vs_12 > 4.751` — самый объёмный и стабильный: 2022: PF=1.12, 2023: PF=1.30, 2024: PF=1.06.

### Steps 8-10 — Cross-analysis: Quality Filters × Pullback Entry

Ключевая таблица discovery vs holdout:

| Filter × Entry | Disc PF (N) | Hold PF (N) | Status |
|----------------|---:|---:|:---:|
| **ALL + market** | 1.06 (1751) | 1.05 (851) | OK |
| **ALL + pullback 3ATR** | 1.26 (323) | 2.51 (148) | OK |
| `fav_3_vs_12<=0.653` + market | 1.64 (194) | 1.78 (84) | OK |
| `fav_3_vs_12<=0.653` + pullback 2ATR | 1.93 (60) | 2.30 (19) | OK |
| `ratio_6>4.41 AND fav_3_vs_12<=0.653` + market | 1.61 (137) | 1.33 (52) | OK |
| `ratio_6>4.41 AND fav_3_vs_12<=0.653` + pullback 2ATR | 1.90 (34) | 7.78 (9) | OK* |
| **`ratio_3_vs_12>4.751` + market** | 1.18 (352) | 0.90 (160) | -- |
| **`ratio_3_vs_12>4.751` + pullback 1ATR** | 1.27 (205) | **1.62 (94)** | **OK** |
| **`ratio_3_vs_12>4.751` + pullback 3ATR** | 1.61 (48) | **3.52 (24)** | **OK** |

(*) N=9 — слишком мало для выводов.

Pullback entry без фильтра — generic "better price" effect (PF растёт с глубиной на всей выборке). Quality filter добавляет cohort-specific uplift поверх этого эффекта.

`ratio_3_vs_12 > 4.751`: market сам по себе не работает на holdout (0.90), но pullback спасает — 1ATR даёт PF=1.62 на 94 fills, 3ATR даёт PF=3.52 на 24 fills.

## Conclusions

1. **Score-based подход (additive score из нескольких features) не работает** на этих данных — holdout не подтверждает.

2. **Индивидуальные правила работают лучше scores**: 7 из 10 top rules подтверждены на holdout.

3. **Два discovery-confirmed filter axis:**
   - `fav_3_vs_12 <= 0.653` — "сигнал ещё не выстрелил" (short fav < 65% mid fav)
   - `ratio_3_vs_12 > 4.751` — "модель очень уверена на коротком горизонте"

4. **Cross-analysis выявил два практических кандидата** (holdout confirmed, filter + pullback):
   - **Агрессивный**: `ratio_3_vs_12 > 4.751 + pullback entry_close-1ATR` — PF=1.62, N=94 (holdout)
   - **Консервативный**: `ratio_3_vs_12 > 4.751 + pullback entry_close-3ATR` — PF=3.52, N=24 (holdout)

5. **Negative control check** (Step 4): `fav_3_vs_12 <= 0.653` не cohort-specific — non_Q4 даёт PF=1.65 с тем же правилом. `ratio_3_vs_12 > 4.751` тоже частично generic.

## Limitations / Open Questions

- `ratio_3_vs_12 > 4.751 + pullback 3ATR`: holdout N=24 — medium-support, не large-sample.
- `fav_3_vs_12 <= 0.653` показывает нестабильный year-split на discovery (деградация 2022→2024) с recovery на holdout — может быть mean reversion, может быть артефакт.
- Pullback entry сам по себе — generic "better price" effect; quality filter добавляет uplift, но не полностью отделим от generic эффекта.
- Не проверено: BUY/SELL split внутри фильтров, sensitivity к точным threshold-ам, сочетание с ATR Q4.

## Next Step

Два варианта для EA-прототипа:

1. **Если приоритет — объём**: `ratio_3_vs_12 > 4.751 + pullback entry_close-1ATR` (94 holdout fills, PF=1.62). Проверить year-stability cross result, BUY/SELL split, threshold sensitivity.

2. **Если приоритет — PF**: `ratio_3_vs_12 > 4.751 + pullback entry_close-3ATR` (24 holdout fills, PF=3.52). Нужно больше данных для подтверждения.

Перед EA: проверить эти кандидаты через Signal Path Atlas pipeline (atlas-level replication), чтобы убедиться, что path geometry поддерживает pullback entry для этих cohorts.

## Related Materials

- [docs/reports/2026-04-03-signal-path-atlas.md](2026-04-03-signal-path-atlas.md)
- [docs/reports/2026-04-02-signal-research-variant-3.md](2026-04-02-signal-research-variant-3.md)
- [docs/reports/2026-04-02-signal-research-variant-3-prep.md](2026-04-02-signal-research-variant-3-prep.md)
- [docs/reports/2026-04-01-signal-research-variant-2.md](2026-04-01-signal-research-variant-2.md)
- [docs/superpowers/specs/2026-04-03-signal-quality-filter-claude.md](../superpowers/specs/2026-04-03-signal-quality-filter-claude.md)
- [docs/superpowers/plans/2026-04-03-signal-quality-filter.md](../superpowers/plans/2026-04-03-signal-quality-filter.md)
