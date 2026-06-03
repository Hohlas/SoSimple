# model_sweep_candidate_source.py

Stage 08 exploratory model sweep for the `methodology_cycle_candidate_source_v2` cycle.

## Purpose

The script compares flat models and 3D sequence models on validation before Stage 09 freeze. It is not a production freeze script; it identifies viable model families and saves validation predictions for audit.

## Inputs

- `DATA/Nero_train_labeled.csv`
- `DATA/Nero_validation_labeled.csv`

## Outputs

- `ML/reports/methodology_cycle_candidate_source_v2/stage08_model_sweep.json`
- `ML/reports/methodology_cycle_candidate_source_v2/stage08_validation_predictions.csv`

## Command

```bash
./.venv/bin/python ML/model_sweep_candidate_source.py
```

## Notes

- Test split is never read.
- Binary TP-vs-SL evaluation excludes timeout rows from training masks, threshold selection, and PF calculation.
- Stage 08 is exploratory and validation-only. Deterministic checkpoint freeze is handled by `ML/validation_freeze.py` in Stage 09.
