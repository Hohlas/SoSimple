# stage09_stability_refreeze.py

Validation-only Stage 09 stability scan + canonical frozen rule for the candidate-source Transformer.

## Purpose

This script is the **source of truth** for `stage09_frozen_rule.json`. It evaluates alternative selection rules for the already frozen Transformer checkpoint without reading the test split. It compares absolute probability thresholds and validation top-k score cutoffs, applies stricter stability gates, and writes the canonical frozen rule.

Run AFTER `validation_freeze.py` (which trains and saves the checkpoint + normalizer).

## Inputs

- `DATA/Nero_validation_labeled.csv`
- `ML/checkpoints/transformer_winner.pt`
- `ML/checkpoints/pll_normalizer_v1.pkl`

## Outputs

- `ML/reports/methodology_cycle_candidate_source_v2/stage09_frozen_rule.json` — canonical frozen rule
- `ML/reports/methodology_cycle_candidate_source_v2/stage09_stability_refreeze.json` — full scan (audit)

## Command

```bash
./.venv/bin/python ML/stage09_stability_refreeze.py
```

## Methodology Constraints

- Test split is not read.
- Top-k validation candidates are converted to an equivalent validation-calibrated threshold before promotion, so the frozen rule can be applied to test/live without peeking at the target period distribution.
- Stability gates include PF, trades/year, active years, negative years, max year trade share, and bootstrap CI lower bound.
- This script is the ONLY source of truth for `stage09_frozen_rule.json`. `validation_freeze.py` does not overwrite it.
