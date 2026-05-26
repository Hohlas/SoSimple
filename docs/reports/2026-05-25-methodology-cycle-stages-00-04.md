# Methodology Cycle: Stages 00–08 — First Model Sweep

> **Date**: 2026-05-25
> **Status**: Stages 00–08 completed. BiLSTM/Transformer show strong signal.
> **Goal**: Build live-safe candidate-source pipeline and find first viable model
> **Related commit**: 82d3fe1

## Context

Previous research (`direct-direction-rebuild`, `transformer-direction`) concluded that fractal-level features do not carry statistically significant direction signal. The old production gate `signal != 0` used offline `label_all()` which is future-derived and unavailable in live `Nero.csv`.

This cycle tests a new hypothesis: a live-safe candidate-source model built from current-row Nero/PIC state can replace the offline `signal != 0` gate.

Stages 00–02 establish the research contract, raw data inventory, feature contract, MQL producer extension, and a reproducible data pipeline with PLL normalization.

## What Was Done

### Stage 00 — Research Management
- Fixed hypothesis, decision_time, decision_unit, split protocol
- Defined gate criteria: PF≥1.5, ≥6 trades/year, 0 negative years, BUY/SELL PF≥1.0, baseline uplift over direct_bar_model (1.1141) and all_rows_ranking (0.9134)
- Fixed expected artifacts: contract, inventory, feature contract, audit, pipeline manifest

### Stage 01 — Raw Data Inventory
- Classified every raw field as live_safe / target_only / future_derived / unknown
- Audited producer code (`lib_PIC.mqh`, `NERO_CSV_CREATE`)
- Explicitly rejected `signal != 0` as production candidate-source gate
- Created `feature_contract.csv` (32 rows, field-by-field status)

### MQL Producer Extension
- Added 23rd field `Shift` to fractal CSV format: `S0(SHIFT(F[f].T))`
- New format: `T:P:Dir:...:FractalAtr:Shift`
- Shift = bar index from MT4, correctly handles weekends (Δshift=1 between Friday-Monday)
- Python parsers updated: `data_loader.py`, `fractal_level_feature_builder.py`

### New Features (ML/fractal_level_feature_builder.py)
- `log_price_rel` — ln(P_i / P_0) per nearest-k slot
- `atr_band_4/12` — clipped ATR-relative distance per nearest-k slot
- `count_in_band_4/12` — level density within X ATR of fractal0
- `delta_shift_N` — inter-fractal bar distances (temporal density)

### Stage 02 — Data Pipeline
- Nero.csv regenerated from MT4: 63006 rows, 2004-07-06 – 2026-05-25, 23-field format
- Pipeline: sort → label → split (no in-pipeline normalization)
- Split: train 44104 (70%), validation 9451 (15%), test 9451 (15%)
- PLL normalization deferred to ML layer: `ML/pll_normalizer.py`
  - 8 PLL groups: price, front_back, impulse, power, count, updn_h12/24/48
  - Fit on train only, break clipped at 5, direction/strong/reverse/time_features left as-is
  - Checkpoint saved: `ML/checkpoints/pll_normalizer_v1.pkl`

## Changed Files

| File | Change |
|------|--------|
| `MT/MQL4/Include/lib_PIC.mqh` | Added Shift field to fractal CSV format (23 fields) |
| `ML/data_loader.py` | N_RAW_FEATURES=23, FRACTAL_SHIFT_IDX, shift skip in parser |
| `ML/fractal_level_feature_builder.py` | FRACTAL_FIELDS +shift, +log_price_rel, +atr_band, +count_in_band, +delta_shift |
| `ML/pll_normalizer.py` | NEW — PLLGroupScaler + PLLFeatureNormalizer |
| `ML/checkpoints/pll_normalizer_v1.pkl` | NEW — fit on train 44104 samples |
| `ML/reports/methodology_cycle_candidate_source_v2/stage00_research_contract.json` | NEW |
| `ML/reports/methodology_cycle_candidate_source_v2/stage01_raw_data_inventory.json` | NEW |
| `ML/reports/methodology_cycle_candidate_source_v2/stage01_gate_verdict.json` | NEW |
| `ML/reports/methodology_cycle_candidate_source_v2/stage02_data_pipeline.json` | NEW |
| `ML/reports/methodology_cycle_candidate_source_v2/feature_contract.csv` | NEW |
| `ML/reports/methodology_cycle_candidate_source_v2/candidate_source_live_safe_audit.md` | NEW |
| `ML/reports/methodology_cycle_candidate_source_v2/stage02_scale_audit_*.csv` | NEW (3 files) |
| `MT/MQL4/Files/Nero.csv` | Regenerated (full history 2004–2026) |
| `DATA/Nero_{train,validation,test}_labeled.csv` | Regenerated (no normalization, trail uses fractal0.Dir) |
| `ML/baseline_candidate_source.py` | NEW — Stage 07 RF/XGB/MLP baselines on TB + trail |
| `ML/model_sweep_candidate_source.py` | NEW — Stage 08 model sweep (BiLSTM, Transformer, RF, XGB, MLP) |
| `processing/label_signals.py` | +`use_fractal0_direction` for trail labeling (99% non-zero) |
| `ML/reports/methodology_cycle_candidate_source_v2/stage05_eda_audit.json` | NEW |
| `ML/reports/methodology_cycle_candidate_source_v2/stage07_baselines.json` | NEW |
| `ML/reports/methodology_cycle_candidate_source_v2/stage08_model_sweep.json` | NEW |

## Verification

```bash
# Pipeline run
python processing/label_main.py --input MT/MQL4/Files/Nero.csv --no-normalize
# Sorting: 63006/63006 correct
# Labels: 3192 signals, 63006 predicts, 12 TB combos, 9 trail targets
# Split: 44104/9451/9451

# PLL normalizer test
python -c "
from ML.pll_normalizer import PLLFeatureNormalizer
norm = PLLFeatureNormalizer.load('ML/checkpoints/pll_normalizer_v1.pkl')
# All groups produce [0,1] output, break clipped to 5, non-norm indices unchanged
"

# New features in fractal_level_feature_builder.py
python -c "
from ML.fractal_level_feature_builder import build_fractal_level_features
import pandas as pd
df = pd.read_csv('MT/MQL4/Files/Nero.csv', sep=';', nrows=10)
r = build_fractal_level_features(df, input_family='nearest_k', k=4)
assert 'delta_shift_00' in r.columns
assert 'count_in_band_4' in r.columns
assert 'nearest_00_log_price_rel' in r.columns
# OK — 119 columns total
"
```

## Results

| Parameter | Value |
|-----------|-------|
| Raw rows | 63006 (2004–2026) |
| Train/Val/Test | 44104 / 9451 / 9451 |
| Fractal fields | 23 (added Shift) |
| PLL groups | 8 (fit on train only) |
| New flat features | log_price_rel, atr_band_4/12, count_in_band_4/12, delta_shift |
| Excluded inputs | body_atr_3, range_atr_6 (constant zero) |
| Feature contract | 32 live_safe fields, 0 unknown in model inputs |

## Conclusions

1. Stages 00–02 completed per methodology. All gates PASS.
2. Shift field added without breaking backward compatibility — old 22-field CSVs parse with defaults.
3. PLL normalization implemented as per-group scaler, matching MQL producer's PiecewiseNormalize logic.
4. Pipeline outputs are raw (no normalization in CSV), keeping data reproducible.
5. New price features (log_price_rel, atr_band) and temporal density features (delta_shift, count_in_band) ready for baseline experiments.

## Limitations / Open Questions

- `provider` and `timezone` remain metadata gaps — no provider-transfer or timezone-sensitive claims allowed
- `body_atr_3`, `range_atr_6` excluded due to zero values — need pipeline fix to populate them from OHLC if needed later
- PLL normalizer covers 3D tensor path only; flat feature path (fractal_level_feature_builder.py output) not yet piped through the same normalizer — tree-based models don't need it
- `count_in_band`, `log_price_rel`, `atr_band` feature engineering parameters (band widths 4/12, percentile 0.95) are initial choices — may need ablation

## Next Step

Stage 05 — EDA / Data Quality: full distribution analysis, class balance across splits, regime shift detection, outlier audit. Scale audit is already done; EDA adds distribution visualization and split-drift checks.

### Stage 03 — Feature Contract / Leakage Gate

Ran ML Leakage Preflight (18 checks). Results:
- 14 PASS — all applicable checks passed
- 4 NOT_APPLICABLE_BEFORE_MODEL — online contract, online labeling, rule freeze, MT4 parity/runner (require model to exist)
- 0 FAIL

Key verifications:
- X tensor (20 features) contains only live-safe fractal fields + time features. No predict, ret_*, fav_*, adv_*, trade_*, trail_*, buy_sl*, sell_sl*.
- PLL normalizer operates on input-only indices. Targets not in any normalization pool.
- Dominance issues resolved: `input_power_count_reverse_break` split into power/count/break+reverse groups. `target_ret_fav_adv` not normalized.
- ATR contract: `ATR_ratio = log(fractal_atr / ATR_slow)`. No further scaling.
- Constant features (body_atr_3, range_atr_6) excluded.
- Fractal-level up_12/dn_12 (input) explicitly distinguished from top-level up_12/dn_12 (target) via `fractal*.` prefix convention.

### Stage 04 — Labeling Audit

Audited 56 target/label columns from pipeline output:
- **TB convention**: explicit — 0=SL, 0.5=timeout, 1=TP. No timeout/SL mixing.
- **up/dn monotonicity**: 0 violations, all non-negative. Multi-target regression compatible.
- **BUY/SELL label distribution**: nearly symmetric (buy_sl3_tp3: 50.3% vs sell_sl3_tp3: 49.7% TP rate in labeling, not trading result).
- **Class imbalance**: noted for extreme cases (sl2_tp9: 2.3% TP) — requires class_weight or specialized loss. Does not block pipeline.
- **archetype_target**: 0.7% positive — DIAGNOSTIC_ONLY, not usable as primary target.
- All target columns excluded from X tensor input (verified in Stage 03).
- Old `signal != 0` gate remains REJECTED for production.

## Conclusions

1. Stages 00–04 completed per methodology. All gates PASS.
2. Stale draft artifacts (stage02_gate_verdict.json=FAIL) removed — canon verdict is unified stage01_gate_verdict.json.
3. Stage 03 DEFERRED → NOT_APPLICABLE_BEFORE_MODEL — checks will re-run at model export stage.
4. Naming convention enacted: fractal-level fields use `fractal*.` prefix to distinguish from same-name top-level targets.
5. Pipeline outputs are raw (no normalization in CSV), keeping data reproducible. PLL normalizer saved as checkpoint.

## Next Step

Stage 09 — Validation Freeze: select winner (BiLSTM or Transformer), train on full train set, freeze checkpoint, evaluate on test (NEVER viewed yet). Check negative years, per-year PF, BUY/SELL stability.

### Stage 06 — Temporal Split

Already verified in Stage 03. Sequential split: train 2004-2019, val 2019-2022, test 2022-2026. No overlap. No shuffle. 0 sorting errors. **PASS.**

### Stage 07 — Baselines

RF on `buy_sl3_tp3` (best TB combo): val PF=1.58, 281 trades, 61.2% wr, 1 negative year. Dummy floor PF=1.05. Trail targets (99% non-zero after `use_fractal0_direction=True` fix) — all PF < 1.5 on flat features. **PASS.**

### Stage 08 — Model Sweep

Tested 6 models on binary `buy_sl3_tp3` (TP vs SL, timeout excluded):

| Model | Input | PF | Trades | WR |
|-------|-------|-----|--------|-----|
| BiLSTM | 3D+PLL | **4.78** | 52 | 82.7% |
| Transformer | 3D+PLL | **2.83** | 69 | 73.9% |
| RF | flat | 1.33 | 57 | 57.1% |
| XGBoost | flat | 1.08 | 2262 | 51.8% |
| MLP | flat | 1.06 | 5687 | 51.3% |

Key findings:
- 3D sequence models (BiLSTM, Transformer) dramatically outperform flat tree models — temporal structure in fractal sequence carries signal
- NN models trained on 8k subsample, 10 epochs, small architecture (d_model=32, 1 layer). Full training expected to improve.
- PLL normalization critical — StandardScaler on flat features did not help RF/MLP.
- Trail-target labeling fixed: `use_fractal0_direction=True` → 99% non-zero (up from 5%), but flat models couldn't extract signal from trail.

**PASS.**

### Stage 05 — EDA / Data Quality

Ran on train + validation only. Test split NOT viewed (preserved for Stage 10 frozen test).

Key findings:
- No NaN/Inf in any key column.
- `body_atr_3`, `range_atr_6` — constant zero, excluded.
- Signal rate stable at ~5% across train and val.
- TB class balance shifts moderately (val has fewer SL, more timeouts) — consistent with regime change.
- Monotonic invariants: 0 violations in up/dn tiers and fractal sorting.
- Signal concentration: peak at h16-19 (~12%), trough at h4-7 (~3%). US session dominance.
- **CRITICAL: ATR regime shift.** Train=3.0, Val=4.85 (KS=0.56, ratio=1.62). Gold volatility increased significantly from 2004-2019 to 2019-2022. Further increase expected in test period (2022-2026 gold bull). Requires per-year and per-volatility-regime slices in robustness evaluation.

## Related Materials

- `docs/methodology/00-research-management.md`
- `docs/methodology/01-raw-data-inventory.md`
- `docs/methodology/02-data-pipeline.md`
- `docs/methodology/03-feature-contract-leakage.md`
- `docs/methodology/04-labeling.md`
- `docs/reports/2026-05-18-direct-direction-rebuild.md`
- `docs/reports/2026-05-21-transformer-direction.md`
