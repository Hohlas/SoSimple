# Stage 6.3: H6 Feature Parity Check

> **Дата**: 2026-06-30
> **Статус**: Completed
> **Вердикт**: DIAGNOSTIC_ONLY / NO_ADDITIVE_VALUE_CONFIRMED
> **Цель**: Проверить, работают ли Stage 6.1 geometry и Stage 6.2 price-action признаки лучше на H6, чем на H12, с тем же TP/SL контрактом.
> **Related plan/spec**: [Stage 6.3 Plan](../superpowers/plans/2026-06-30-stage6_3-h6-feature-parity-check.md)

> **Run:** 2026-06-30, 13 profiles × 3 seeds = 39 XGBoost runs
> **Elapsed:** 3175s (52.9 min)
> **Runtime contract:** `xgb_n_jobs=24`, `started_at=2026-06-30T13:09:15Z`, `finished_at=2026-06-30T14:02:10Z`, per-run `elapsed_sec` present.

---

## Context

Stage 6.1 и Stage 6.2 проверяли две feature семьи на H12 horizon: (1) относительную геометрию фракталов вокруг `fractal0` и (2) недавний OHLC price action. Оба этапа показали слабые результаты на H12: geometry — MODEL_GATE_FAILED, price action — TRADING_GATE_FAILED. Один из открытых вопросов в обоих отчётах: не является ли H12 слишком жёстким горизонтом для этих признаков.

Stage 6.3 проверяет эту гипотезу: фиксирует horizon=6 (вместо 12) и повторяет оценку обеих feature families с тем же TP/SL контрактом. Результат — диагностический; максимальный статус артефакта — DIAGNOSTIC_ONLY.

Важное ограничение: H6 parity не делает Stage 5 и Stage 6 идентичными, потому что Stage 5 использует breach/time-to-breach цели, а Stage 6 — TP/SL touch. H6 parity проверяет только, ведут ли себя Stage 6 признаки по-разному на более коротком горизонте.

## What Was Done

Добавлен runner `ML/baseline/benchmark_stage6_3_h6_feature_parity.py`, который использует существующие Stage 6.1/6.2 билдеры признаков с переименованными профилями (`h6_*` вместо `h12_*`).

Фиксированный торговый контракт:
- XAUUSD H1
- horizon H6 (изменён с H12)
- entry `Open[row+1]`
- SL `0.5 ATR`
- TP `2.0 ATR`
- same-bar ambiguity = SL-first
- target: `stage6_definitive_tp_vs_sl_flag`

Проверены 13 профилей × 3 seed = 39 XGBoost runs:

| Profile | Feature count | Источник |
|---|---|---:|---|
| `h6_clock_shift_back` | 204 | same-run H6 baseline |
| `h6_nearest_price40_relative_geometry` | 320 | Stage 6.1 geometry |
| `h6_nearest_time40_relative_geometry` | 320 | Stage 6.1 geometry |
| `h6_corridor3_relative_geometry` | 320 | Stage 6.1 geometry |
| `h6_corridor10_relative_geometry` | 320 | Stage 6.1 geometry |
| `h6_zones10_uniform_summary` | 100 | Stage 6.1 geometry |
| `h6_price_action_core` | 30 | Stage 6.2 price action |
| `h6_price_action_regime` | 34 | Stage 6.2 price action |
| `h6_clock_shift_back_plus_nearest_time40_geometry` | 524 | baseline + geometry (delta) |
| `h6_clock_shift_back_plus_corridor3_geometry` | 524 | baseline + geometry (delta) |
| `h6_clock_shift_back_plus_corridor10_geometry` | 524 | baseline + geometry (delta) |
| `h6_clock_shift_back_plus_price_action_core` | 234 | baseline + price action (delta) |
| `h6_clock_shift_back_plus_price_action_regime` | 238 | baseline + price action (delta) |

## Multiple Testing Context

Search budget is fixed and bounded:
- 1 horizon: H6 (изменён с H12)
- 1 target: `stage6_definitive_tp_vs_sl_flag`
- 13 profiles (1 baseline + 5 geometry + 2 price-action + 5 combined)
- 3 seeds: `42`, `77`, `123`
- total: 39 model runs

`val_stop` (`2021-2022`) for model/threshold/gate decisions. `diagnostic_holdout` (`2023-2025`) and `low_n_disclosure` (`2026`) are disclosure-only.

No correction promotes this to candidate status. All results remain `DIAGNOSTIC_ONLY`.

## Changed Files

- `ML/baseline/benchmark_stage6_3_h6_feature_parity.py`
- `tests/test_stage6_3_h6_feature_parity.py`
- `ML/reports/stage6_3_h6_feature_parity.json`
- `docs/reports/2026-06-30-stage6_3-h6-feature-parity-check.md`
- `CHANGELOG.md`
- `CONTEXT_HANDOFF.md`
- `docs/reports/2026-06-29-stage6_1-h12-relative-fractal-geometry.md` (cross-link)
- `docs/reports/2026-06-30-stage6_2-h12-price-action-feature-family.md` (cross-link)
- wiki files

## Verification

Commands:

```bash
./.venv/bin/python -m pytest tests/test_stage6_3_h6_feature_parity.py -q
./.venv/bin/python ML/baseline/benchmark_stage6_3_h6_feature_parity.py --stage6-3-h6-feature-parity --no-resume
```

Observed:
- focused Stage 6.3 tests: `24 passed in 2.91s`
- benchmark: `done_runs == total_runs == 39`
- runtime: `elapsed_sec=3174.6`
- `config.xgb_n_jobs == 24`; top-level and per-run `elapsed_sec` present; runner writes initial checkpoint, checkpoint after preflight, checkpoint after every run, and supports `--resume` / `--no-resume`

Input files inherited from Stage 6.1/6.2 (unchanged).

## Results

### Same-Run H6 Summary by Profile

Aggregation rule: AUC, PR lift, selected PF and permutation p-value are medians over three seeds. Selected threshold is the median-PF seed among selected seeds.

| Profile | Val AUC med | PR AUC lift med | Threshold | Selected PF med | Permutation p-value |
|---|---:|---:|---|---:|---:|
| `h6_clock_shift_back` | 0.6649 | 0.1692 | SELECTED | 1.006 | 0.700 |
| `h6_nearest_price40_relative_geometry` | 0.5278 | 0.0266 | NO_THRESHOLD | — | N/A |
| `h6_nearest_time40_relative_geometry` | 0.5820 | 0.0601 | NO_THRESHOLD | — | N/A |
| `h6_corridor3_relative_geometry` | 0.5400 | 0.0304 | NO_THRESHOLD | — | N/A |
| `h6_corridor10_relative_geometry` | 0.5331 | 0.0267 | NO_THRESHOLD | — | N/A |
| `h6_zones10_uniform_summary` | 0.5155 | 0.0177 | NO_THRESHOLD | — | N/A |
| `h6_price_action_core` | 0.6676 | 0.1809 | SELECTED | 1.075 | 0.570 |
| `h6_price_action_regime` | 0.6725 | 0.1817 | SELECTED | 1.213 | 0.305 |

### Per-Seed Table for Profiles That Look Strong

| Profile | Seed | Val AUC | Threshold | PF | Trades/yr | Permutation p-value |
|---|---:|---:|---:|---:|---:|---:|
| `h6_clock_shift_back` | 42 | 0.6649 | 0.525 | 1.006 | 144.0 | 0.700 |
| `h6_clock_shift_back` | 77 | 0.6635 | 0.575 | 1.092 | 95.5 | 0.480 |
| `h6_clock_shift_back` | 123 | 0.6683 | 0.550 | 0.990 | 121.0 | 0.735 |
| `h6_price_action_core` | 42 | 0.6665 | 0.775 | 1.075 | 39.0 | 0.570 |
| `h6_price_action_core` | 77 | 0.6681 | 0.775 | 1.056 | 37.5 | 0.610 |
| `h6_price_action_core` | 123 | 0.6676 | 0.775 | 1.310 | 33.5 | 0.230 |
| `h6_price_action_regime` | 42 | 0.6723 | 0.775 | 1.221 | 42.5 | 0.260 |
| `h6_price_action_regime` | 77 | 0.6725 | 0.775 | 1.213 | 38.5 | 0.305 |
| `h6_price_action_regime` | 123 | 0.6737 | 0.775 | 1.179 | 34.5 | 0.355 |
| `h6_clock_shift_back_plus_price_action_core` | 42 | 0.6760 | 0.725 | 1.466 | 48.0 | **0.095** |
| `h6_clock_shift_back_plus_price_action_core` | 77 | 0.6759 | 0.725 | 1.213 | 45.5 | 0.270 |
| `h6_clock_shift_back_plus_price_action_core` | 123 | 0.6769 | 0.700 | 1.241 | 61.5 | 0.350 |

### H6 Baseline vs H6 Feature Delta

Delta gate rules:
- AUC delta ≥ +0.02
- PR AUC lift delta ≥ 0.0
- threshold SELECTED
- median selected PF not worse than baseline
- permutation empirical_p_value ≤ 0.10

| Combined profile | AUC delta | PR lift delta | PF delta | Permutation p-value | Delta gate |
|---|---:|---:|---:|---:|---|
| `h6_clock_shift_back_plus_nearest_time40_geometry` | +0.0030 | +0.0045 | +0.062 | 0.540 | FAIL |
| `h6_clock_shift_back_plus_corridor3_geometry` | -0.0008 | +0.0030 | +0.174 | 0.355 | FAIL |
| `h6_clock_shift_back_plus_corridor10_geometry` | -0.0001 | +0.0018 | +0.185 | 0.330 | FAIL |
| `h6_clock_shift_back_plus_price_action_core` | +0.0111 | +0.0168 | +0.236 | 0.270 | FAIL |
| `h6_clock_shift_back_plus_price_action_regime` | +0.0121 | +0.0150 | +0.196 | 0.365 | FAIL |

AUC deltas for combined geometry profiles are near zero. Price-action combined profiles show stronger deltas (+0.011–+0.012) but still below the required +0.02, with permutation p-values well above 0.10.

### H6 vs H12 Disclosure

| Metric | H6 | H12 | Delta |
|---|---:|---:|---:|
| Baseline AUC median | 0.665 | 0.617 | +0.048 |
| Baseline median PF | 1.006 | 1.249 | -0.243 |

H6 substantially improves ranking (AUC +0.048) but at the cost of PF (−0.243). The baseline selects a threshold on both horizons, but permutation is not convincing on either (H6 p=0.700, H12 p=0.225).

H6 disclosure is reported for comparison only. It does not affect Stage 6.3 gate decisions.

### Permutation Context

H6 permutation p-values are uniformly high across almost all profiles and seeds. The only seed with p ≤ 0.10 is `h6_clock_shift_back_plus_price_action_core` seed=42 (p=0.095). This is a single-seed finding from a combined profile; the median over three seeds is 0.270. No standalone profile achieves median p ≤ 0.10.

## Gate

| Check | Status |
|---|---|
| Baseline AUC ≥ 0.60 | PASS (0.665) |
| Baseline PR AUC lift ≥ 0.05 | PASS (0.169) |
| Baseline threshold selected | PASS |
| Baseline permutation p-value ≤ 0.10 | FAIL (0.700) |
| Any delta gate pass | FAIL |
| **Overall** | **DIAGNOSTIC_ONLY** |

No profile or combined profile passes the delta gate. The best combined profile (`h6_clock_shift_back_plus_price_action_core`) has AUC delta +0.011 (below +0.02) and median permutation p=0.270.

## Conclusions

1. **H6 horizon substantially improves ranking over H12** for the baseline `clock_shift_back`: AUC 0.665 vs 0.617. However, PF drops from 1.249 to 1.006, and permutation robustness remains weak (p=0.700).

2. **Geometry-only features fail on H6 just as they fail on H12.** All five geometry profiles produce AUC 0.51–0.58 and do not select a threshold. H6 horizon does not rescue fractal geometry.

3. **Price-action standalone shows stronger ranking on H6 than on H12:** `h6_price_action_core` (AUC 0.668, PF 1.075) and `h6_price_action_regime` (AUC 0.672, PF 1.213) both select thresholds with positive PF. But permutation p-values (0.305–0.570) are far above 0.10.

4. **Combined profiles improve AUC but not enough.** `h6_clock_shift_back_plus_price_action_core` achieves AUC 0.676 with delta +0.011 over baseline — the best ranking in the run — but below the +0.02 threshold. Median permutation p-values remain 0.27–0.37.

5. **One seed passes the permutation gate.** `h6_clock_shift_back_plus_price_action_core` seed=42 has perm p=0.095 and PF=1.466. This is a single diagnostic data point, not a robust finding — the other two seeds have p=0.27 and 0.35.

6. **H6 parity does not make Stage 5 and Stage 6 identical.** Stage 5 uses breach/time-to-breach targets on H6; Stage 6 uses TP/SL touch target. The results are from different target definitions.

## Limitations / Open Questions

1. H6 permutation robustness is worse than H12 despite better AUC — possibly because higher TP rate on H6 creates a narrower spread between model and baseline performance.

2. Price-action features on H6 show a consistent ranking trace that is stronger than on H12, but the evidence is not strong enough for the predeclared gate. This is a diagnostic observation, not a confirmation.

3. No new feature engineering, threshold grid, ATR/TP/SL search, or seed list was tested. The H6 parity run is limited to existing families with only the horizon changed.

4. The 2026 low-N disclosure split has severe OHLC coverage issues (553/1162 rows missing exact OHLC match), inherited from Stage 6.2.

5. Single-instrument, single-timeframe (XAUUSD H1). Results may not generalise.

### What Is Closed / Not Closed

| Closed by Stage 6.3 | Not closed by Stage 6.3 |
|---|---|
| H6 does not rescue fractal geometry features | Other horizon lengths (H24, H48) |
| Price-action shows stronger trace on H6 but still fails gate | Combined feature families not tested |
| Same-run H6 baseline can rank TP/SL touch | Other instruments or timeframes |

## Validation Split Disclosure

- **Model selection:** val_stop (2021–2022) only
- **Holdout:** diagnostic_holdout (2023–2025) and low_n_disclosure (2026) were not used for any selection decision
- **No profile, seed, or threshold was chosen using holdout data**

## Next Step

Proceed to `Regression Up/Dn target foundation` as previously indicated in CONTEXT_HANDOFF.md. H6 parity does not change the recommended research direction.

Do not reopen H6/geometry/price-action search based on these results. The bounded H6 parity check is complete and confirms that shorter horizon does not materially change the standing conclusions from Stage 6.1 and 6.2.

## Related Materials

- [Stage 6.3 JSON](../../ML/reports/stage6_3_h6_feature_parity.json)
- [Stage 6.3 Runner](../../ML/baseline/benchmark_stage6_3_h6_feature_parity.py)
- [Stage 6.3 Tests](../../tests/test_stage6_3_h6_feature_parity.py)
- [Stage 6.1 Report](2026-06-29-stage6_1-h12-relative-fractal-geometry.md)
- [Stage 6.2 Report](2026-06-30-stage6_2-h12-price-action-feature-family.md)
- [Stage 6.0 Report](2026-06-29-stage6_0-outcome-based-triple-barrier-foundation.md)
- [Stage 6.3 Plan](../superpowers/plans/2026-06-30-stage6_3-h6-feature-parity-check.md)
