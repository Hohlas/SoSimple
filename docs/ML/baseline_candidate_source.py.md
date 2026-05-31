# baseline_candidate_source.py

Stage 07 baseline-first runner for the `methodology_cycle_candidate_source_v2` cycle.

## Purpose

The script trains dummy and simple ML baselines on train, evaluates only on validation, and writes the baseline report required before model development. It uses live-safe flat fractal-level features and the `buy_sl3_tp3` Triple Barrier target.

## Inputs

- `DATA/Nero_train_labeled.csv`
- `DATA/Nero_validation_labeled.csv`

## Output

- `ML/reports/methodology_cycle_candidate_source_v2/stage07_baselines.json`

## Command

```bash
./.venv/bin/python ML/baseline_candidate_source.py --thresholds 0.35,0.40,0.45,0.50,0.55,0.60,0.65,0.70,0.75
```

## Notes

- Test split is never read.
- Trading metrics are gross diagnostics; costs are deferred to Stage 12.
- The report includes confusion matrices, classification metrics, per-year slices, and diagnostic BUY/SELL slices.
