# CONTEXT HANDOFF

## Current Active State

- report: `docs/reports/2026-07-27-fractal0-fixed11-retained-subset-mt4-parity.md`
- plan: `docs/superpowers/plans/2026-07-27-fixed11-retained-subset-mt4-parity.md`
- artifacts: `ML/reports/fractal0_fixed11_retained_mt4_parity/feasibility.json`, `ML/reports/fractal0_fixed11_retained_mt4_parity/freeze.json`
- latest manual tester export summary: `ML/reports/fractal0_fixed11_retained_mt4_parity/fixed11_rule_signal_exports.json`
- inputs: `ML/reports/fractal0_fixed11_mutual_correlation_pruning_retained_subset.json`, `ML/reports/fractal0_fixed11_rich_entry_locked_test_trades.csv`, `ML/reports/fractal0_fixed11_rich_entry_locked_test.json`

## Decision

Fixed11 retained-subset MT4 parity is blocked, not passed.

- verdict: `UNKNOWN`
- stage_decision: `parity_blocked`
- retained_rule_count: `5`
- retained_trade_count: `6177`
- unique_signal_time_count: `2806`
- unique_signal_time_direction_count: `2827`
- duplicate_signal_time_count: `1670`
- opposite_signal_time_count: `21`
- plain_time_signal_export_allowed: `false`

## Why It Is Blocked

Current retained trades cannot be represented by one plain `time;signal` MT4 stream:

- it would drop `rule_id`;
- it would collapse duplicate `signal_time` rows;
- `21` time groups contain opposite directions;
- current `iSignal=3` direct mode is documented as next-bar CSV execution with `ML_HoldBars`/TP/back-stop/reversal settings, not as proven Python fixed11 `E3/S2/X2/spread=0.20` execution.

No export, MT4 tester run or reconciliation was produced.

## Per-Rule MT4 Switch Added

MT4 can now switch retained rules by tester row:

- `BackTest=2` -> `ML_RuleSlot=1` -> `ml_signals_fixed11_rule01.csv`
- `BackTest=3` -> `ML_RuleSlot=2` -> `ml_signals_fixed11_rule02.csv`
- `BackTest=4` -> `ML_RuleSlot=3` -> `ml_signals_fixed11_rule03.csv`
- `BackTest=5` -> `ML_RuleSlot=4` -> `ml_signals_fixed11_rule04.csv`
- `BackTest=6` -> `ML_RuleSlot=5` -> `ml_signals_fixed11_rule05.csv`

Changed runtime/settings:

- `MT/MQL4/Experts/$o$imple.mq4`
- `MT/MQL4/Include/MAIN.mqh`
- `MT/MQL4/Include/lib_ML_Signal.mqh`
- `MT/MQL4/Files/#.csv`
- `MT/tester/files/#.csv`
- `MT/tester/$o$imple.ini`

This does not yet pass parity. MT4 must still be compiled and run externally.
Per-rule `time;signal` files were created in both MT4 file directories for
manual tester runs. The export policy is conservative: same-direction duplicate
times are collapsed; opposite-direction same-time groups are omitted because one
timestamp cannot represent both directions.

## Frozen Scope

Retained subset:

- `rank05_time_only_linear_target_entry_avoid_sl_top30`
- `rank02_time_only_linear_target_entry_ev_regression_top40`
- `rank11_movement_plus_time_linear_target_entry_good_0_5r_top50`
- `rank09_time_only_hist_gradient_boosting_target_entry_good_0_5r_top50`
- `rank10_movement_plus_time_linear_target_entry_ev_regression_top50`

Do not change frozen rules, cutoffs, profiles, models, targets, filters, entries, exits, stops, spread, fill policy or PnL convention.

## Verified Facts

- `feasibility.json` and `freeze.json` are valid JSON.
- Task 2 stop check returned `parity_blocked` with exit code `2`.
- Targeted MQL contract tests: `./.venv/bin/python -m pytest tests/test_mql_telemetry_params_csv_contract.py -q` -> `15 passed`.
- Full tests after code/test changes: `./.venv/bin/python -m pytest tests/ -q` -> `1482 passed, 52 warnings`.
- Wiki generation/status passed after docs sync.

## Next Step

Next immediate step:

- compile `$o$imple.mq4` in MT4;
- run tester with `BackTest=2..6`;
- reconcile each run separately.

Stress-spread disclosure and model card remain blocked until this parity track is resolved.
