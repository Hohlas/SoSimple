# prune_fractal0_fixed11_mutual_correlation.py

Pruning runner for the 11 passed Fractal0 fixed rules.

## Inputs

- `ML/reports/fractal0_fixed11_candidate_audit.json`
- `ML/reports/fractal0_fixed11_rich_entry_locked_test_summary.csv`
- `ML/reports/fractal0_fixed11_rich_entry_locked_test_selection.csv`
- `ML/reports/fractal0_fixed11_rich_entry_locked_test_trades.csv`

## Command

```bash
./.venv/bin/python ML/baseline/prune_fractal0_fixed11_mutual_correlation.py \
  --input-prefix ML/reports/fractal0_fixed11_rich_entry_locked_test \
  --audit-json ML/reports/fractal0_fixed11_candidate_audit.json \
  --output-prefix ML/reports/fractal0_fixed11_mutual_correlation_pruning
```

## Outputs

- `ML/reports/fractal0_fixed11_mutual_correlation_pruning_pairwise.csv`
- `ML/reports/fractal0_fixed11_mutual_correlation_pruning_clusters.csv`
- `ML/reports/fractal0_fixed11_mutual_correlation_pruning_fill_daily_pnl_matrix.csv`
- `ML/reports/fractal0_fixed11_mutual_correlation_pruning_fill_weekly_pnl_matrix.csv`
- `ML/reports/fractal0_fixed11_mutual_correlation_pruning_exit_daily_pnl_matrix.csv`
- `ML/reports/fractal0_fixed11_mutual_correlation_pruning_exit_weekly_pnl_matrix.csv`
- `ML/reports/fractal0_fixed11_mutual_correlation_pruning_exit_drawdown_overlap_matrix.csv`
- `ML/reports/fractal0_fixed11_mutual_correlation_pruning_retained_subset.json`
- `ML/reports/fractal0_fixed11_mutual_correlation_pruning_summary.json`

## Constraints

- Does not train, score, simulate, or change rules.
- Uses saved `locked_test` trades only for pruning among already passed candidates.
- Representative choice inside duplicate groups uses `BS_p05 / max_drawdown_r`, then robustness and trading metric tie-breakers.
