# CONTEXT HANDOFF

## Current Completed Stage

- report: `docs/reports/2026-07-27-fractal0-fixed11-mutual-correlation-pruning.md`
- script: `ML/baseline/prune_fractal0_fixed11_mutual_correlation.py`
- artifacts: `ML/reports/fractal0_fixed11_mutual_correlation_pruning_summary.json`, `ML/reports/fractal0_fixed11_mutual_correlation_pruning_retained_subset.json`, `ML/reports/fractal0_fixed11_mutual_correlation_pruning_pairwise.csv`
- inputs: `ML/reports/fractal0_fixed11_rich_entry_locked_test*`, `ML/reports/fractal0_fixed11_candidate_audit.json`

## Decision

Fixed-11 mutual-correlation pruning is complete.

- overall_decision: `pruning_passed`
- input_rule_count: `11`
- retained_count: `5`
- removed_count: `6`
- pair_count: `55`
- locked_test_policy: `overlap_measurement_and_metric_representative_selection_within_passed_duplicates`
- representative_policy: `best_bs_p05_per_drawdown_then_robustness_metrics`
- representative_metric: `BS_p05 / max_drawdown_r`
- locked_test_performance_used_for_representative_choice: `true`

## Retained Subset

- `rank05_time_only_linear_target_entry_avoid_sl_top30`
- `rank02_time_only_linear_target_entry_ev_regression_top40`
- `rank11_movement_plus_time_linear_target_entry_good_0_5r_top50`
- `rank09_time_only_hist_gradient_boosting_target_entry_good_0_5r_top50`
- `rank10_movement_plus_time_linear_target_entry_ev_regression_top50`

## Dropped Strong Duplicates

- `rank03_time_only_linear_target_entry_ev_regression_top50`
- `rank04_time_only_linear_target_entry_good_0_5r_top40`
- `rank06_time_only_linear_target_entry_good_0_5r_top50`
- `rank08_movement_plus_time_linear_target_entry_good_0_5r_top30`
- `rank01_time_only_linear_target_entry_ev_regression_top30`
- `rank07_movement_plus_time_linear_target_entry_good_0_5r_top40`

## Evidence Basis

- `docs/reports/2026-07-25-fractal0-fixed11-candidate-audit.md`
- `ML/reports/fractal0_fixed11_candidate_audit.json`
- `ML/reports/fractal0_fixed11_rich_entry_locked_test_summary.csv`
- `ML/reports/fractal0_fixed11_rich_entry_locked_test_selection.csv`
- `ML/reports/fractal0_fixed11_rich_entry_locked_test_trades.csv`
- pruning artifacts under `ML/reports/fractal0_fixed11_mutual_correlation_pruning_*`

## Verified Facts

- Targeted tests: `./.venv/bin/python -m pytest tests/test_fractal0_fixed11_mutual_correlation_pruning.py -q` -> `12 passed`.
- Pruning command exited with code `0`.
- All expected pruning CSV/JSON artifacts exist.
- Pairwise CSV has `55` rows.
- Correlation matrices are `11 x 11`, symmetric, with diagonal `1.0`.

## Next Step

Run MT4/tester parity for the retained subset only.

Do not export all 11 rules as independent. Do not change frozen rules, cutoffs, model/profile/target/filter choices, entry/exit/stop, spread, fill policy or PnL convention. Stress-spread disclosure should run after parity for the retained subset. Model card remains blocked until pruning, parity and stress disclosure are complete.
