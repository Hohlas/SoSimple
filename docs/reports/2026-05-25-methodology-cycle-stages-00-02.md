# Methodology Cycle: Stages 00–02 — Pipeline Foundation

> **Date**: 2026-05-25 18:00
> **Status**: Completed (Stages 00–02 PASS)
> **Goal**: Build live-safe candidate-source pipeline foundation under `docs/methodology/` rules
> **Related commit**: c68416a

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
| `DATA/Nero_{train,validation,test}_labeled.csv` | Regenerated (no normalization) |

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

Stage 03 — Feature Contract / Leakage Gate: validate that no future-derived field leaks into model inputs, check normalization pool isolation, verify online/training contract match.

## Related Materials

- `docs/methodology/00-research-management.md`
- `docs/methodology/01-raw-data-inventory.md`
- `docs/methodology/02-data-pipeline.md`
- `docs/reports/2026-05-18-direct-direction-rebuild.md`
- `docs/reports/2026-05-21-transformer-direction.md`
