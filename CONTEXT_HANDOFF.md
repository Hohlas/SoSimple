# CONTEXT HANDOFF

## Current Completed Stage

- report: `docs/reports/2026-07-24-fractal0-fixed11-locked-test.md`
- script: `ML/baseline/run_fractal0_fixed11_rich_entry_locked_test.py`
- source runner: `ML/baseline/benchmark_fractal0_entry_quality_filter.py`
- artifacts: `ML/reports/fractal0_fixed11_rich_entry_locked_test*`

## Decision

11 frozen normalized rich-entry leaderboard rules were evaluated on `locked_test` with the M5 execution contract.

- Verdict: `candidate_check_required`
- kept_candidates: 11
- PF range: `2.6747-3.3667`
- BS p05 range: `1.9273-2.9239`

## Key Result

The locked_test split (`9463` rows, `2022-12-02` to `2026-06-04`) was used only for one-shot evaluation.

- Best locked_test PF: `3.3667` for `rank01_time_only_linear_target_entry_ev_regression_top30`
- Lowest locked_test PF: `2.6747` for `rank08_movement_plus_time_linear_target_entry_good_0_5r_top30`
- BUY PF range: `3.6196-5.1218`
- SELL PF range: `1.9485-3.0798`
- Weakest yearly PF: `1.9938`

## Implementation Notes

- Source rules/cutoffs: `ML/reports/leaderboard_closure_audit_rules.csv`
- Execution contract: `ML/reports/fractal0_stop_grid_m5.json`
- M5 OHLC: `MT/MQL4/Files/XAUUSD_M5_OHLC.csv`
- `movement_plus_time` locked-test scores are restored via the frozen movement protocol because source freeze scores do not include `locked_test`.

## Next Step

Run an independent audit of `ML/reports/fractal0_fixed11_rich_entry_locked_test.json` and CSV artifacts. If no blockers are found, proceed to MT4/tester parity, stress-spread disclosure and model card.
