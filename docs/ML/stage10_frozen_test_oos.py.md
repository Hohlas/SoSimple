# stage10_frozen_test_oos.py

One-shot Stage 10 frozen test/OOS evaluation for the candidate-source Transformer.

## Purpose

This script consumes the Stage 09 canonical frozen rule and applies it to `DATA/Nero_test_labeled.csv` without training, refitting, threshold search, top-k search, or rule changes.

## Inputs

- `DATA/Nero_test_labeled.csv`
- `ML/reports/methodology_cycle_candidate_source_v2/stage09_frozen_rule.json`
- `ML/checkpoints/transformer_winner.pt`
- `ML/checkpoints/pll_normalizer_v1.pkl`

## Outputs

- `ML/reports/methodology_cycle_candidate_source_v2/stage10_frozen_test_oos.json` — frozen test summary and verdict
- `ML/reports/methodology_cycle_candidate_source_v2/stage10_test_predictions.csv` — all test rows with TP probability and selected flag
- `ML/reports/methodology_cycle_candidate_source_v2/stage10_test_trades.csv` — selected test rows only

## Command

```bash
./.venv/bin/python ML/stage10_frozen_test_oos.py
```

## Methodology Constraints

- Test split is read only by this frozen-test stage.
- The threshold is read from `stage09_frozen_rule.json`.
- The checkpoint and normalizer hashes must match the frozen rule.
- If any frozen protocol check fails, the Stage 10 artifact is `INVALID` and all metrics are diagnostic only.
- Aggregate PF is reported together with yearly, quarterly, side-diagnostic and concentration slices.
- A Stage 10 candidate verdict is possible only when all frozen protocol checks pass. If the artifact is `INVALID`, metrics are diagnostic only and no Stage 11 transition is allowed.
- Even a valid candidate verdict is not production approval; robustness, costs, MT4 parity and forward-test remain required.
