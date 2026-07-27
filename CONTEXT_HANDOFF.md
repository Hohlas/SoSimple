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

Later manual tester diagnostics did run per-rule CSV loading. They confirmed
that signals are read, but the first run did not match Python trades because
`ML_MaxPositions=1` blocked most signals and `ML_AllowReversal=0` disabled the
Python `X2_ml_opposite_any_p0_50` style reverse close.

After recompilation with `ML_MaxPositions=20` and `ML_AllowReversal=1`, the
fresh rule slot 1 tester run loaded `1137` CSV rows and opened `1136` trades:
`BUY=489`, `SELL=647`, `Position blocked=0`, `Timeout closes=516`,
`Reverse closes=620`, `OPEN_FAILED=0`. The remaining mismatch is entry
execution: all matched `signal_time + direction` keys had different Python
`fill_time` versus MT4 `entry_time`, because that compiled build entered by
market on the next H1 bar instead of using Python fixed11
`E3_open_pullback_1_0atr`.

Latest source fix after that finding: fixed11 multi-position entry now places
`OP_BUYLIMIT`/`OP_SELLLIMIT` pending orders using `Open[0] - atr` for BUY and
`Open[0] + atr` for SELL. After the 15:02 tester log, two more mismatches were
fixed: pending expiration now covers the six Python fill-check bars after the
calculation bar, and per-rule signal files now use `time;signal;atr;stop`.
`atr` comes from `DATA/Nero_XAUUSD_test_labeled.csv`; `stop` comes from Python
`protective_stop_price` for `S2`. `ORDER_PLACED` logs include
`calculation_open`, `atr`, `signal_time`, `order_time`, `expires`,
`requested_price`, `stop_source`, `Val`, `Stp`, `Prf`; real `OPEN` is logged
after tester fills the pending order and repeats the stored `calculation_open`,
`requested_price`, `atr` and `signal_time`.

After the 16:35 tester log, two more facts were confirmed: the tester ran with
`TestGenerator: spread set to 100`, producing `Ask-Bid=1.00` instead of Python
fixed11 `spread=0.20`; and `23` closed tickets had no explicit `OPEN` row
because they opened and closed inside one H1 runtime interval. Source was patched
again to log missing history `OPEN` rows before `CLOSE` and to print
`MLP SPREAD_MISMATCH` when fixed11 tester spread differs from `0.20`.

After the 16:43 tester log, spread and missing-OPEN logging were correct:
`ORDER_PLACED=1136`, `OPEN=981`, `CLOSE=981`, `deleted due expiration=155`,
`broker_history_missing_open=22`, and no `SPREAD_MISMATCH`/`OPEN_FAILED`.
Reconciliation found `981` MT4 closes matching Python export-shape rows and `0`
MT4-only closes, but `156` Python rows were still absent. Ticket `24` proves one
remaining boundary issue: MT4 deleted the pending order at `2023.01.05 06:02:30`
with `expires=2023.01.05 06:00`, while Python fill time for the same signal is
`2023-01-05 06:00:00`. Source was patched again to keep one extra H1 guard bar
after the Python fill-window. The larger unresolved mismatch is exit logic:
Python `X2_ml_opposite_any_p0_50` is a separate ML close signal per open
position; MT4 currently closes on opposite entry signals from the entry CSV.

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
Per-rule `time;signal;atr;stop` files were created in both MT4 file directories for
manual tester runs. The export policy is conservative: same-direction duplicate
times are collapsed; opposite-direction same-time groups are omitted because one
timestamp cannot represent both directions.

Latest fixed11 diagnostic settings:

- `ML_MaxPositions=20`
- `ML_AllowReversal=1`
- `ML_HoldBars=24`
- `ML_BackStopATR=50` fallback only when CSV has no `stop`
- `ML_TakeProfitATR=0`

`lib_ML_Signal.mqh` now closes multi-position BUY on new `signal=-1` and SELL
on new `signal=1` with reason `ReverseSignal`. It also stores `signal_time` in
the order comment and writes that value back to `ML_Trade_Events` on close, so
new tester runs can reconcile close rows to source signals.

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
- Targeted MQL contract tests: `./.venv/bin/python -m pytest tests/test_mql_telemetry_params_csv_contract.py -q` -> `26 passed`.
- Full `tests/` run intentionally not used for this MT4-only iteration.
- Wiki generation/status passed after docs sync.

## Next Step

Next immediate step:

- recompile `$o$imple.mq4` after the latest history-OPEN and spread-warning
  source fix;
- rerun tester with `BackTest=2` first;
- set tester Spread to `20` for XAUUSD if `Point=0.01`, so `Ask-Bid=0.20`;
- compare against Python by `signal_time + direction + fill_time`, not only by
  count.

Stress-spread disclosure and model card remain blocked until this parity track is resolved.
