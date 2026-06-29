# Stage 6.1: H12 Relative Fractal Geometry

> **Дата**: 2026-06-29  
> **Статус**: Completed  
> **Вердикт**: DIAGNOSTIC_ONLY / MODEL_GATE_FAILED  
> **Цель**: Проверить, даёт ли относительная геометрия фракталов вокруг `fractal0` сигнал для H12 TP/SL touch.  
> **Related plan/spec**: [Stage 6.1 Plan](../superpowers/plans/2026-06-29-stage6_1-h12-relative-fractal-geometry.md)

> **Run:** 2026-06-29, 6 profiles × 3 seeds = 18 XGBoost runs  
> **Elapsed:** 3581s (59.7 min)  
> **Runtime contract:** `xgb_n_jobs=24`, `started_at=2026-06-29T17:54:41.565617+00:00`, `finished_at=2026-06-29T18:54:22.599773+00:00`, per-run `elapsed_sec` present.

---

## Context

Stage 6.0 showed that H1 triple-barrier TP/SL touch prediction can contain ranking signal on clock/backward-looking features. The question was whether local fractal geometry around `fractal0` — measured as relative price distance and recency — carries signal for *which* barrier is touched first.

Stage 6.1 fixes horizon to 12 bars, inherits the Stage 6.0 barrier contract (SL at −0.5 ATR, TP at +2.0 ATR, SL-first same-bar ambiguity), and uses `stage6_definitive_tp_vs_sl_flag` as the main training target. Timeout rows are excluded from model labels but included in trading simulation PnL.

## What Was Done

### Feature Profiles

| Profile | Description | Expected signal |
|---------|-------------|----------------|
| `h12_clock_shift_back` | Stage 5.4 baseline (clock shift + backward-looking bar features) | Control |
| `h12_nearest_price40_relative_geometry` | K=40 fractals closest to fractal0 by relative ATR price distance | Price proximity |
| `h12_nearest_time40_relative_geometry` | K=40 fractals closest to fractal0 by log(shift) | Recency |
| `h12_corridor3_relative_geometry` | All fractals within ±3 ATR of fractal0, K≤40 padded | Local structure |
| `h12_corridor10_relative_geometry` | All fractals within ±10 ATR, K≤40 padded | Wide structure (control) |
| `h12_zones10_uniform_summary` | Same ±10 ATR window compressed into twenty 1 ATR zone buckets | Crowding/asymmetry |

### Predeclared Geometry Comparisons

Per the research contract:
- **nearest_price vs nearest_time**: asks whether price proximity or recency dominates
- **corridor3 vs corridor10**: asks whether very local structure (±3 ATR) is enough vs wide irrelevant
- **zones10**: alternative encoding to test whether bucket-summary works when token-order fails

### Search Budget

- 6 profiles × 3 seeds (42, 77, 123) = 18 runs
- Model: XGBoost (max_depth=6, lr=0.03, n_estimators=500, early_stopping=20)
- Threads: `xgb_n_jobs=24`
- Runner supports `--resume` / `--no-resume`, writes JSON checkpoint before preflight and after every run, and prints heartbeat progress.
- Selection: val_stop (2021–2022) only
- Disclosure-only: diagnostic_holdout (2023–2025), low_n_disclosure (2026)
- No threshold, seed, or profile was selected using holdout data

## Multiple Testing Context

Stage 6.1 is exploratory and `DIAGNOSTIC_ONLY`.

- Search budget: 1 horizon (`H12`) × 1 target (`stage6_definitive_tp_vs_sl_flag`) × 6 predeclared profiles × 3 seeds = 18 model runs.
- No correction promotes the result to candidate status.
- `h12_corridor3_relative_geometry` was the predeclared primary profile.
- `diagnostic_holdout` (`2023-2025`) and `low_n_disclosure` (`2026`) were not used for profile, seed, threshold, or gate selection.

## Changed Files

- `ML/baseline/benchmark_stage6_1_relative_geometry.py`
- `tests/test_stage6_1_relative_geometry.py`
- `ML/reports/stage6_1_h12_relative_fractal_geometry.json`
- `docs/reports/2026-06-29-stage6_1-h12-relative-fractal-geometry.md`
- `docs/superpowers/plans/2026-06-29-stage6_1-h12-relative-fractal-geometry.md`
- `CHANGELOG.md`
- `CONTEXT_HANDOFF.md`
- `wiki/research/fractal-stop-research.md`, `wiki/index.md`, `wiki/log.md`, `wiki/REPO_integrity.md`

### Input Files

| File | Rows | Bytes | SHA256 |
|------|------|-------|--------|
| XAUUSD_H1_OHLC.csv | 126,637 | 7,443,441 | `84b0efbdab7fde3d862131d8f2b3d4945b596af40500dffb477845c0195ddce6` |
| Nero_XAUUSD_train_labeled.csv | 44,159 | 845,963,293 | `2f02f1c1347dfda8ef8fa8163f3788acabeb9f3612cc9aacb71cd24aaa88e3ef` |
| Nero_XAUUSD_validation_labeled.csv | 9,463 | 182,022,271 | `83f6fb607043ff003f73b26b2342cba6f9faa356001995d248af4032d896e707` |
| Nero_XAUUSD_test_labeled.csv | 9,463 | 182,725,354 | `749752bc2088e01ab6107d7ca5e3911d9239e581859e74061f4fb16e27815d2a` |

## Verification

Commands:

```bash
./.venv/bin/python ML/baseline/benchmark_stage6_1_relative_geometry.py --stage6-1-relative-geometry --no-resume
./.venv/bin/python -m pytest tests/test_stage6_1_relative_geometry.py -q
./.venv/bin/python -m pytest tests/ -q
```

Structured artifact checks:

- `done_runs == total_runs == 18`
- `len(raw_runs) == 18`
- `config.xgb_n_jobs == 24`
- `started_at`, `finished_at`, top-level `elapsed_sec` present
- every `raw_runs[*]` entry contains `elapsed_sec`
- gate reads `empirical_p_value` from the inherited Stage 6 permutation baseline

### Fractal Format Preflight

- All 4 analysis splits (`train_core`, `val_stop`, `diagnostic_holdout`, `low_n_disclosure`) have 100% valid `fractal0` strings with 23 colon-separated fields.
- Zero short_fractal0_rows detected
- No warnings

### A7-Style Coverage Preflight

This is an A7-style geometry coverage preflight, not a full A7 distribution audit. It checks token counts, corridor bounds, empty-token rates, and above/below balance. It does not audit every derived feature for tails, zero inflation, and train/validation/holdout distribution shift.

| Profile | Median tokens | Zero-rate | min_coord | max_coord |
|---------|---------------|-----------|-----------|-----------|
| nearest_price40 | 40.0 | 0.0% | −24.4 ATR | +30.5 ATR |
| nearest_time40 | 40.0 | 0.0% | −29.8 ATR | +38.3 ATR |
| corridor3 | 26.0 | 0.1% | −3.0 ATR | +3.0 ATR |
| corridor10 | 60.0 | 0.0% | −10.0 ATR | +10.0 ATR |
| zones10 | 60.0 | 0.0% | −10.0 ATR | +10.0 ATR |

- Corridor min/max exactly at bounds — corridor filtering correct
- Above/below balance ~50/50 across all profiles
- No warnings triggered — all stop conditions met before training

## Results

### Primary Profile: `h12_corridor3_relative_geometry`

| Metric | Value |
|--------|-------|
| Val AUC (median over 3 seeds) | 0.5316 |
| Val PR AUC lift | 0.0282 |
| Threshold selected | NO_THRESHOLD |
| Permutation p-value | N/A (no trading threshold) |

### All Profiles

| Profile | Val AUC med | PR AUC lift med | Threshold | Selected PF med | Permutation p-value |
|---------|-------------|-----------------|-----------|-----------------|---------------------|
| `h12_clock_shift_back` | **0.6174** | **0.1305** | SELECTED | 1.249 | 0.225 |
| `h12_nearest_price40_relative_geometry` | 0.5194 | 0.0220 | NO_THRESHOLD | — | N/A |
| `h12_nearest_time40_relative_geometry` | 0.5500 | 0.0381 | NO_THRESHOLD | — | N/A |
| `h12_corridor3_relative_geometry` | 0.5316 | 0.0282 | NO_THRESHOLD | — | N/A |
| `h12_corridor10_relative_geometry` | 0.5211 | 0.0278 | NO_THRESHOLD | — | N/A |
| `h12_zones10_uniform_summary` | 0.5142 | 0.0211 | NO_THRESHOLD | — | N/A |

The Stage 5.4 clock_shift_back baseline confirms that the labels and feature pipeline are not completely broken: it produces AUC 0.617 and selects a threshold with PF 1.25. It does **not** prove trading suitability, because its permutation threshold test is not statistically convincing (`empirical_p_value=0.225`, above the required `0.10`). All five geometry-only profiles are weak (AUC 0.51–0.55) and do not select a threshold.

### Diagnostic Holdout Disclosure

Diagnostic holdout (`2023-2025`) is disclosure-only. It did not influence profile, seed, threshold, or gate selection.

| Profile | Diagnostic holdout AUC med | Diagnostic PR lift med |
|---------|----------------------------|------------------------|
| `h12_clock_shift_back` | 0.6105 | 0.1209 |
| `h12_nearest_price40_relative_geometry` | 0.5254 | 0.0257 |
| `h12_nearest_time40_relative_geometry` | 0.5373 | 0.0339 |
| `h12_corridor3_relative_geometry` | 0.5288 | 0.0234 |
| `h12_corridor10_relative_geometry` | 0.5267 | 0.0253 |
| `h12_zones10_uniform_summary` | 0.5134 | 0.0146 |

The holdout disclosure is consistent with validation: geometry-only profiles remain weak.

### Validation Feature Importance

Rule: for each non-baseline geometry profile, select the seed with the highest `val_stop` AUC, then report top-5 validation permutation feature importance by AUC drop from `raw_runs[*].feature_importance`. This is interpretability disclosure only; it does not affect selection or gate.

| Profile | Best seed | Best val AUC | Top validation permutation features |
|---------|-----------|--------------|-------------------------------------|
| `h12_nearest_price40_relative_geometry` | 123 | 0.5201 | `slot39_price_coord_atr` (0.0077), `slot39_abs_price_coord_atr` (0.0043), `slot37_abs_price_coord_atr` (0.0042), `slot33_back` (0.0042), `slot04_log_shift` (0.0032) |
| `h12_nearest_time40_relative_geometry` | 42 | 0.5509 | `slot00_abs_price_coord_atr` (0.0208), `slot20_front` (0.0054), `slot00_log_shift` (0.0051), `slot30_price_coord_atr` (0.0035), `slot33_abs_price_coord_atr` (0.0033) |
| `h12_corridor3_relative_geometry` | 123 | 0.5365 | `slot00_back` (0.0066), `slot14_price_coord_atr` (0.0053), `slot21_impulse` (0.0043), `slot07_log_shift` (0.0038), `slot12_impulse` (0.0035) |
| `h12_corridor10_relative_geometry` | 77 | 0.5216 | `slot39_price_coord_atr` (0.0075), `slot22_front` (0.0050), `slot04_abs_price_coord_atr` (0.0042), `slot33_back` (0.0035), `slot38_front` (0.0035) |
| `h12_zones10_uniform_summary` | 123 | 0.5264 | `zone_+00_+01_count` (0.0141), `zone_+01_+02_impulse_mean` (0.0080), `zone_-07_-06_back_mean` (0.0053), `zone_+03_+04_back_mean` (0.0039), `zone_+02_+03_impulse_mean` (0.0037) |

Feature importance does not show a stable, high-magnitude geometry mechanism. The largest drops are small and appear in different slots/zones across profiles.

## Gate

| Check | Status |
|-------|--------|
| AUC ≥ 0.60 | ❌ (0.53) |
| PR AUC lift ≥ 0.05 | ❌ (0.028) |
| Permutation p-value ≤ 0.10 | ❌ (N/A) |
| Threshold selected | ❌ |
| **Model gate pass** | **❌** |
| **Overall status** | **MODEL_GATE_FAILED** |

## Conclusions

**The predeclared H12 relative-geometry profiles did not receive support.** Local support/resistance geometry around `fractal0`, as encoded here by flat token-order, nearest/corridor, and uniform zone features, did not predict which triple barrier is touched first within 12 H1 bars.

Three independent lines of evidence support this:

1. **Near-zero AUC lift across tested encodings.** Price proximity (nearest_price), recency (nearest_time), narrow corridor (±3 ATR), wide corridor (±10 ATR), and zone bucket summaries all produce AUC 0.51–0.55. None of the tested geometry-only encodings extracts useful signal.

2. **No tradeable threshold found.** Even with the most permissive threshold search (all positive PF thresholds), none of the geometry profiles produced a threshold that survives basic validation. This rules out the possibility that the model captures signal that a different scoring rule would exploit.

3. **Baseline confirms ranking signal exists outside geometry-only profiles.** The Stage 5.4 clock_shift_back profile — trained and evaluated on the same splits with the same H12 horizon — produces AUC 0.617 and a threshold with PF 1.25. However, its permutation p-value is 0.225, so this is evidence that the pipeline can rank outcomes, not evidence of a statistically convincing trading rule.

## Limitations / Open Questions

1. **Feature engineering is not exhaustive.** Only fractal-level geometry was tested. Other encodings (e.g., density kernel estimates, pairwise fractal-frontal distances, HMM of level occupancy) might extract signal that flat token-order features miss. However, the zone summaries were specifically designed to test the crowding/asymmetry hypothesis without relying on token order — and they also failed.

2. **H12-only.** The 12-bar horizon is fixed. A shorter (6-bar) or longer (24-bar) horizon might reveal fractal geometry signal that H12 does not. However, Stage 6.0 showed 6-bar horizon works for the baseline, and expanding the search would violate the fixed-horizon constraint.

3. **Single instrument.** XAUUSD H1 only. The fractal geometry hypothesis might hold on other instruments or timeframes.

4. **Stage 6.1 is `DIAGNOSTIC_ONLY`.** Even if the gate had passed, this stage would not produce a `CANDIDATE` artifact. The diagnostics are complete.

5. **Preflight is still a long silent section.** The runner now writes an initial checkpoint before preflight, but the heavy split loading / H12 relabeling step still has no internal progress marks. This does not affect metrics, but it is a runtime observability limitation.

6. **No baseline-plus-geometry delta test.** Stage 6.1 tests geometry-only profiles against the baseline, but does not test whether geometry adds incremental value on top of `h12_clock_shift_back`. A future test could predeclare exactly one baseline+geometry delta profile, without reopening a broad horizon/ATR/TP/SL search.

## Validation Split Disclosure

- **Model selection:** val_stop (2021–2022) only
- **Holdout:** diagnostic_holdout (2023–2025) and low_n_disclosure (2026) were not used for any selection decision
- **No profile, seed, or threshold was chosen using holdout data**
- Holdout AUC/PR lift is reported above as disclosure-only. Threshold holdout results are not reported for geometry profiles because no threshold was available.

## Next Step

The current H12 relative-geometry branch is closed for the tested encoding family. Recommended directions:

1. **Stage 6.2 (recommended):** Attempt to replicate Stage 6.0 results with a fundamentally different feature family (e.g., multi-timeframe momentum, micro-structure, or volume-based features) to establish whether H12 TP/SL prediction is robust or fragile.

2. **Stage 6.0 refinement:** The baseline achieves AUC 0.617 with clock_shift_back. Investigate whether ensembling or calibration improves trading results — but this is a separate research path.

3. **Archive this Stage 6.1 geometry-only approach.** The code and report are preserved. Further work on fractal geometry should require a new, narrow hypothesis, such as one predeclared baseline+geometry delta test, rather than another broad feature search.

## Related Materials

- [Plan](../superpowers/plans/2026-06-29-stage6_1-h12-relative-fractal-geometry.md)
- [Stage 6.0 Report](../reports/2026-06-29-stage6_0-outcome-based-triple-barrier-foundation.md)
- [Stage 6.1 JSON](../../ML/reports/stage6_1_h12_relative_fractal_geometry.json)
- [Stage 6.1 Runner](../../ML/baseline/benchmark_stage6_1_relative_geometry.py)
- [Stage 6.1 Tests](../../tests/test_stage6_1_relative_geometry.py)
- [Methodology: Feature Contract (A6)](../methodology/A6-fractal-feature-profile-catalog.md)
- [Methodology: Feature Distribution Audit (A7)](../methodology/A7-feature-distribution-audit.md)
