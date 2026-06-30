# Stage 6.2: H12 Price Action Feature Family

> **Дата**: 2026-06-30  
> **Статус**: Completed  
> **Вердикт**: DIAGNOSTIC_ONLY / TRADING_GATE_FAILED  
> **Цель**: Проверить, добавляет ли недавнее OHLC price action полезный сигнал для H12 TP/SL touch сверх same-run baseline `h12_clock_shift_back`.  
> **Related plan/spec**: [Stage 6.2 Plan](../superpowers/plans/2026-06-30-stage6_2-h12-price-action-feature-family.md)

---

## Context

Stage 6.1 показал, что локальная геометрия фракталов вокруг `fractal0` не даёт полезного H12 TP/SL touch сигнала. Stage 6.2 проверяет другую семью: последние OHLC-бары перед строкой `fractal0` confirmation.

Исследовательская гипотеза: движение цены, структура свечи, диапазон и положение close относительно recent high/low до `row.time` могут менять вероятность того, какой барьер будет достигнут первым за H12.

Уровень этапа: поисковый. Максимальный статус артефакта — `DIAGNOSTIC_ONLY`; результат не может стать кандидатом без отдельного проверочного цикла.

## What Was Done

Добавлен runner `ML/baseline/benchmark_stage6_2_price_action.py`.

Фиксированный торговый контракт:

- XAUUSD H1
- horizon H12
- entry `Open[row+1]`
- SL `0.5 ATR`
- TP `2.0 ATR`
- same-bar ambiguity = SL-first
- target: `stage6_definitive_tp_vs_sl_flag`

Проверены 5 профилей × 3 seed = 15 XGBoost runs:

| Profile | Назначение | Feature count |
|---|---|---:|
| `h12_clock_shift_back` | same-run baseline/control | 204 |
| `h12_price_action_core` | OHLC-only price action | 30 |
| `h12_price_action_regime` | core + ATR/source volume state | 34 |
| `h12_clock_shift_back_plus_price_action_core` | delta test vs baseline | 234 |
| `h12_clock_shift_back_plus_price_action_regime` | delta test vs baseline + regime | 238 |

Feature windows: `(1, 3, 6, 12, 24)` H1 bars ending at `row.time`. Features use only OHLC bars with `time <= row.time`. They do not read `Open[row+1]`, entry bar, future H12 bars, labels, `stage6_*`, `trade_*`, `fav_*`, `adv_*`, `ret_*`, or `path_*`.

`volume` from `DATA/XAUUSD_H1_OHLC.csv` is treated as source volume, not real exchange volume, unless producer documentation proves otherwise.

## Multiple Testing Context

Search budget is fixed and bounded:

- 1 horizon: H12
- 1 target: `stage6_definitive_tp_vs_sl_flag`
- 5 profiles
- 3 seeds: `42`, `77`, `123`
- total: 15 model runs

`val_stop` (`2021-2022`) was used for model and threshold selection. `diagnostic_holdout` (`2023-2025`) and `low_n_disclosure` (`2026`) are disclosure-only and were not used for profile, seed, threshold, or gate selection.

No correction promotes this to candidate status. All results remain `DIAGNOSTIC_ONLY`.

## Changed Files

- `ML/baseline/benchmark_stage6_2_price_action.py`
- `tests/test_stage6_2_price_action.py`
- `ML/reports/stage6_2_h12_price_action_feature_family.json`
- `docs/reports/2026-06-30-stage6_2-h12-price-action-feature-family.md`
- `CHANGELOG.md`
- `CONTEXT_HANDOFF.md`
- `wiki/research/fractal-stop-research.md`, `wiki/index.md`, `wiki/log.md`, `wiki/REPO_integrity.md`

## Verification

Commands:

```bash
./.venv/bin/python -m pytest tests/test_stage6_2_price_action.py -q
rg -n "benchmark_stage6_2|stage6-2-price-action|--no-resume|--stage6" tests/
./.venv/bin/python statistics/data_contract_smoke_check.py
./.venv/bin/python -m pytest tests/ -q
./.venv/bin/python ML/baseline/benchmark_stage6_2_price_action.py --stage6-2-price-action --no-resume
```

Observed:

- focused Stage 6.2 tests: `17 passed in 1.42s`
- full suite: `934 passed, 30 warnings in 161.39s`
- legacy data smoke-check failed on an unused historical target column `target_buy_H6_val`; Stage 6.2-specific checks passed, but global data-contract debt remains
- benchmark: `done_runs == total_runs == 15`
- runtime: `started_at=2026-06-30T06:47:04.551186+00:00`, `finished_at=2026-06-30T07:09:25.966096+00:00`, `elapsed_sec=1341.4`
- `config.xgb_n_jobs == 24`; top-level and per-run `elapsed_sec` present; runner writes initial checkpoint, checkpoint after preflight, checkpoint after every run, and supports `--resume` / `--no-resume`

Input files:

| File | Rows | Bytes | SHA256 |
|---|---:|---:|---|
| `XAUUSD_H1_OHLC.csv` | 126,637 | 7,443,441 | `84b0efbdab7fde3d862131d8f2b3d4945b596af40500dffb477845c0195ddce6` |
| `Nero_XAUUSD_train_labeled.csv` | 44,159 | 845,963,293 | `2f02f1c1347dfda8ef8fa8163f3788acabeb9f3612cc9aacb71cd24aaa88e3ef` |
| `Nero_XAUUSD_validation_labeled.csv` | 9,463 | 182,022,271 | `83f6fb607043ff003f73b26b2342cba6f9faa356001995d248af4032d896e707` |
| `Nero_XAUUSD_test_labeled.csv` | 9,463 | 182,725,354 | `749752bc2088e01ab6107d7ca5e3911d9239e581859e74061f4fb16e27815d2a` |

## Feature Contract And Preflight

Row-time contract:

- For rows with exact OHLC match, features use the closed OHLC bar at `row.time`.
- Rows without exact OHLC match receive a zero-vector for price-action features and are disclosed separately.
- Unit tests mutate future bars and `Open[row+1]`; feature vectors do not change.

OHLC coverage and feature audit:

| Split | Rows | Missing exact OHLC | Incomplete 24-window | Core all-zero rows | Regime all-zero rows | Status |
|---|---:|---:|---:|---:|---:|---|
| `train_core` | 48,417 | 0 | 0 | 0 | 0 | PASS |
| `val_stop` | 5,415 | 3 | 0 | 3 | 3 | WARNING |
| `diagnostic_holdout` | 8,091 | 48 | 0 | 48 | 48 | WARNING |
| `low_n_disclosure` | 1,162 | 551 | 0 | 551 | 551 | WARNING |

The warnings are missing exact OHLC rows. Missing rows receive all-zero price-action features by explicit contract and are disclosed. No non-finite feature values were found.

## Results

All-profile validation summary:

Aggregation rule: AUC, PR lift, selected PF and permutation p-value are medians over the three seeds. The `selected` threshold stored in JSON is the selected seed row with median PF among selected seeds. Top feature importance is reported separately from the best validation-AUC seed and is not used for gate selection.

| Profile | Val AUC med | PR AUC lift med | Threshold | Selected PF med | Permutation p-value |
|---|---:|---:|---|---:|---:|
| `h12_clock_shift_back` | 0.6174 | 0.1305 | SELECTED | 1.249 | 0.225 |
| `h12_price_action_core` | 0.6233 | 0.1402 | SELECTED | 1.307 | 0.160 |
| `h12_price_action_regime` | 0.6225 | 0.1376 | SELECTED | 1.257 | 0.260 |
| `h12_clock_shift_back_plus_price_action_core` | 0.6273 | 0.1451 | SELECTED | 1.326 | 0.185 |
| `h12_clock_shift_back_plus_price_action_regime` | 0.6275 | 0.1419 | SELECTED | 1.250 | 0.255 |

The primary standalone profile `h12_price_action_core` passes AUC, PR lift, threshold, PF, trades/year, and spread 0.20 PF checks. It fails the median-over-seeds permutation gate (`0.160 > 0.10`), so the overall result is `TRADING_GATE_FAILED`.

Per-seed validation disclosure:

| Profile | Seed | Val AUC | Threshold | PF | Permutation p-value |
|---|---:|---:|---:|---:|---:|
| `h12_clock_shift_back` | 42 | 0.6197 | 0.700 | 1.249 | 0.225 |
| `h12_clock_shift_back` | 77 | 0.6144 | 0.700 | 1.297 | 0.205 |
| `h12_clock_shift_back` | 123 | 0.6174 | 0.600 | 1.143 | 0.390 |
| `h12_price_action_core` | 42 | 0.6233 | 0.700 | 1.307 | 0.160 |
| `h12_price_action_core` | 77 | 0.6213 | 0.725 | 1.180 | 0.350 |
| `h12_price_action_core` | 123 | 0.6238 | 0.725 | 1.359 | 0.155 |
| `h12_price_action_regime` | 42 | 0.6215 | 0.700 | 1.130 | 0.400 |
| `h12_price_action_regime` | 77 | 0.6231 | 0.750 | 1.257 | 0.260 |
| `h12_price_action_regime` | 123 | 0.6225 | 0.750 | 1.491 | 0.105 |
| `h12_clock_shift_back_plus_price_action_core` | 42 | 0.6264 | 0.700 | 1.326 | 0.185 |
| `h12_clock_shift_back_plus_price_action_core` | 77 | 0.6302 | 0.700 | 1.252 | 0.285 |
| `h12_clock_shift_back_plus_price_action_core` | 123 | 0.6273 | 0.700 | 1.503 | 0.065 |
| `h12_clock_shift_back_plus_price_action_regime` | 42 | 0.6275 | 0.500 | 1.048 | 0.540 |
| `h12_clock_shift_back_plus_price_action_regime` | 77 | 0.6266 | 0.725 | 1.250 | 0.255 |
| `h12_clock_shift_back_plus_price_action_regime` | 123 | 0.6279 | 0.750 | 1.290 | 0.215 |

Baseline-plus-price-action delta, using only the same Stage 6.2 JSON baseline:

| Combined profile | AUC delta | PR lift delta | PF delta | Permutation p-value | Delta gate |
|---|---:|---:|---:|---:|---|
| `h12_clock_shift_back_plus_price_action_core` | +0.0098 | +0.0146 | +0.0766 | 0.185 | FAIL |
| `h12_clock_shift_back_plus_price_action_regime` | +0.0101 | +0.0114 | +0.0007 | 0.255 | FAIL |

Both combined profiles improve AUC and do not reduce median PF, but the AUC delta is below the required `+0.02` and permutation p-value is above `0.10`.

Diagnostic holdout disclosure:

| Profile | Holdout AUC med | Holdout PR lift med | 2026 AUC med | 2026 PR lift med |
|---|---:|---:|---:|---:|
| `h12_clock_shift_back` | 0.6105 | 0.1209 | 0.5977 | 0.1273 |
| `h12_price_action_core` | 0.6050 | 0.1147 | 0.6029 | 0.1466 |
| `h12_price_action_regime` | 0.6064 | 0.1164 | 0.5989 | 0.1367 |
| `h12_clock_shift_back_plus_price_action_core` | 0.6150 | 0.1264 | 0.6063 | 0.1361 |
| `h12_clock_shift_back_plus_price_action_regime` | 0.6170 | 0.1275 | 0.5961 | 0.1386 |

Holdout was disclosure-only. It supports the narrow reading that combined profiles are close to the same-run baseline, not that a production signal is proven. The 2026 disclosure is especially weak for price-action profiles because `551/1162` rows have no exact OHLC match and therefore receive zero-vector price-action features.

Top validation permutation feature importance per non-baseline profile:

Rule: choose the seed with the highest `val_stop` AUC for that profile, then report top-5 validation permutation features from that model. This is interpretability disclosure only and is not used for gate selection.

| Profile | Top-5 features by AUC drop |
|---|---|
| `h12_price_action_core` | `range_w1_atr` 0.0525; `close_to_low_w1_atr` 0.0069; `close_to_high_w1_atr` 0.0053; `range_w6_atr` 0.0033; `ret_close_w3_atr` 0.0031 |
| `h12_price_action_regime` | `range_w1_atr` 0.0568; `close_to_low_w1_atr` 0.0111; `close_to_high_w1_atr` 0.0085; `ret_close_w3_atr` 0.0054; `upper_wick_1_atr` 0.0041 |
| `h12_clock_shift_back_plus_price_action_core` | `baseline.fractal0.back` 0.0296; `price_action.range_w1_atr` 0.0133; `baseline.hour_sin` 0.0106; `price_action.close_to_high_w1_atr` 0.0040; `price_action.close_to_high_w3_atr` 0.0022 |
| `h12_clock_shift_back_plus_price_action_regime` | `baseline.fractal0.back` 0.0248; `price_action.range_w1_atr` 0.0164; `price_action.close_to_low_w1_atr` 0.0033; `price_action.close_to_high_w1_atr` 0.0030; `price_action.close_pos_w1` 0.0025 |

## Gate

| Check | Status |
|---|---|
| Primary AUC >= 0.60 | PASS |
| Primary PR AUC lift >= 0.05 | PASS |
| Primary threshold selected | PASS |
| Primary permutation p-value <= 0.10 | FAIL (`0.160`) |
| Primary selected PF >= 1.15 | PASS |
| Primary trades/year >= 25 | PASS |
| Primary spread 0.20 PF >= 1.05 | PASS |
| Any delta gate pass | FAIL |

Overall: `TRADING_GATE_FAILED`, artifact status `DIAGNOSTIC_ONLY`.

## Conclusions

The tested price-action family shows a weak ranking trace on `val_stop`: `h12_price_action_core` improves median validation AUC over same-run `h12_clock_shift_back` from `0.6174` to `0.6233`, and combined profiles reach about `0.627`.

The signal is not strong enough for the predeclared Stage 6.2 gates. The primary standalone profile fails median-over-seeds permutation (`p=0.160`), and combined profiles fail the additive delta gate because AUC delta is only about `+0.010`, below the required `+0.020`, with median permutation p-values `0.185` and `0.255`.

Narrow verdict: recent OHLC price action, as encoded here, has a weak validation ranking trace but did not prove robust standalone or additive trading value over `h12_clock_shift_back`. This rejects only this fixed feature family, not every possible OHLC-derived representation.

## Limitations / Open Questions

- The legacy data smoke-check failed on an unused historical target column `target_buy_H6_val`; Stage 6.2-specific checks passed, but global data-contract debt remains.
- Missing exact OHLC rows create all-zero price-action rows, especially in the 2026 low-N disclosure split.
- `source_volume_to_source_volume_mean_24` uses source volume only; no claim is made about exchange volume.
- Early stopping and threshold selection both use `val_stop`; this is acceptable only because the stage is exploratory and diagnostic.
- No horizon, ATR, TP/SL, spread, or profile search beyond the fixed plan was performed.

## Validation Split Disclosure

Selection split:

- `val_stop` (`2021-2022`) selected thresholds and evaluated gates.

Disclosure-only:

- `diagnostic_holdout` (`2023-2025`)
- `low_n_disclosure` (`2026`)

No profile, seed, threshold, or gate was selected using `2023-2025` or `2026`.

## Next Step

Do not promote Stage 6.2 to candidate. The next defensible step is either:

- a bounded post-mortem on why `range_w1_atr` dominates and why permutation remains weak; or
- a new predeclared family with materially new information, not another small variant of the same OHLC windows.

Do not open broad horizon/ATR/TP/SL search based on this result.

## Related Materials

- [Stage 6.2 JSON](../../ML/reports/stage6_2_h12_price_action_feature_family.json)
- [Stage 6.2 Plan](../superpowers/plans/2026-06-30-stage6_2-h12-price-action-feature-family.md)
- [Stage 6.1 Report](2026-06-29-stage6_1-h12-relative-fractal-geometry.md)
- [Stage 6.0 Report](2026-06-29-stage6_0-outcome-based-triple-barrier-foundation.md)
