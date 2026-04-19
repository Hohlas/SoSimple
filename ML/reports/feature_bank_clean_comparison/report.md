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
| baseline_clean | 12000 | 6000 | 117 | 0.083736 | 0.238819 | 0.842623 |
| baseline_clean_path | 12000 | 6000 | 422 | 0.081836 | 0.250021 | 0.836066 |
| baseline_clean_geometry_path | 12000 | 6000 | 567 | 0.076765 | 0.249481 | 0.829508 |
| baseline_full_path | 12000 | 6000 | 566 | 0.074359 | 0.267621 | 0.839344 |
| baseline_full | 12000 | 6000 | 261 | 0.060763 | 0.280381 | 0.836066 |

## Interpretation

- `baseline_clean` removes raw groups: `direction, price_position, path_long, path_short`.
- `baseline_full_path` adds the path-reaction bank to the full baseline.
- `baseline_clean_path` adds the path-reaction bank to the cleaned baseline.
- `baseline_clean_geometry_path` adds both banks to the cleaned baseline.
- This is a feature diagnostic, not a trading verdict.
