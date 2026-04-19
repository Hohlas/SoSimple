# Feature Bank Comparison Diagnostics

## Scope

Read-only comparison of current baseline features against geometry/path feature banks.
No neural-network training and no MT4/lib_PIC changes.

## Configuration

- Target: `trail_24_pnl_atr_x8`
- seq_len: `20`
- Train rows: `12000`
- Validation rows: `6000`
- RandomForest trees: `80`

## Results

| variant | train_rows | validation_rows | feature_count | validation_r2 | validation_mae | directional_accuracy |
| --- | --- | --- | --- | --- | --- | --- |
| baseline_path | 12000 | 6000 | 566 | 0.074359 | 0.267621 | 0.839344 |
| baseline_geometry_path | 12000 | 6000 | 711 | 0.072829 | 0.261340 | 0.832787 |
| baseline_geometry | 12000 | 6000 | 406 | 0.069316 | 0.266884 | 0.826230 |
| baseline | 12000 | 6000 | 261 | 0.060763 | 0.280381 | 0.836066 |

## Interpretation

- `baseline` uses the existing grouped fractal summaries from `feature_importance_diagnostics`.
- `baseline_geometry` adds the geometry bank.
- `baseline_path` adds the path-reaction bank.
- `baseline_geometry_path` adds both banks.
- This is a feature diagnostic, not a trading verdict.
