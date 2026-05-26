# stage09_stability_refreeze.py

Validation-only Stage 09 stability scan for the frozen candidate-source Transformer.

## Purpose

The script evaluates alternative selection rules for the already frozen Transformer checkpoint without reading the test split. It compares absolute probability thresholds and validation top-k score cutoffs, then applies stricter stability gates before any rule can replace the canonical Stage 09 threshold.

## Inputs

- `DATA/Nero_validation_labeled.csv`
- `ML/checkpoints/transformer_winner.pt`
- `ML/checkpoints/pll_normalizer_v1.pkl`

## Output

- `ML/reports/methodology_cycle_candidate_source_v2/stage09_stability_refreeze.json`

## Command

```bash
./.venv/bin/python ML/stage09_stability_refreeze.py
```

## Methodology Constraints

- Test split is not read.
- Top-k validation candidates are converted to an equivalent validation-calibrated threshold before promotion, so the frozen rule can be applied to test/live without peeking at the target period distribution.
- Stability gates include PF, trades/year, active years, negative years, max year trade share, and bootstrap CI lower bound.
