# CONTEXT HANDOFF

## Current Active State

- active track: `MT5 diagnostic timing contract -> full-batch event-output investigation`
- latest report: `docs/reports/2026-08-01-mt5-diagnostic-timing-contract.md`
- latest plan: `docs/superpowers/plans/2026-08-01-mt5-diagnostic-timing-contract.md`
- latest spec: `docs/superpowers/specs/2026-08-01-mt5-diagnostic-timing-contract-design.md`
- batch summary: `ML/reports/mt5_execution_loop/batch/batch_summary.json`
- event diagnostics: `ML/reports/mt5_execution_loop/diagnostics/event_anomaly_summary.json`

## Decision

MT5 diagnostic timing contract is implemented as `DIAGNOSTIC_ONLY`.

- Signal CSV timing is now `feature_time <= time < feature_available_time <= decision_time`.
- Event timing for signal-linked rows is now `feature_time <= signal_time < feature_available_time <= decision_time <= execution_time`.
- MQL5 signal matching uses only `time` / `MT5_EntryTimes[i] == Time[bar]`; `decision_time` is descriptive and no longer a match key.
- Invalid signal rows are logged as `TIMING_VIOLATION` and skipped before order placement.
- `TX_OPEN` and `TX_CLOSE` may keep timing fields empty; Python reconciliation links them later.
- Default mode remains `latency_bars=0`; positive latency is diagnostic-only export mode and must not enter winner selection.

## Current Diagnostic Facts

- 32/32 regenerated `entry_signals.json` files contain `timing_contract` and `latency_bars=0`.
- Signal timing verification: `checked_signal_files=32`, `bad_files=0`.
- MetaEditor compile log: `Result: 0 errors, 0 warnings`.
- Smoke tester: passed with `UNEXPLAINED=0`.
- Full batch runtime: `UNKNOWN`; only 2/32 full-batch runs emitted expected fresh event files.
- `batch_summary.json`: `status=DIAGNOSTIC_ONLY`, `verdict=BATCH_NO_WINNER`, `n_candidates=32`, `n_valid=2`, `n_eligible=0`.
- `batch_runs.timing_contract`: `checked_rows=2189`, `violation_rows=0`, `timing_violation_event_count=0`.
- `reference_runs.timing_contract`: historical copied-timing violations remain (`violation_rows=22510`); treat them as legacy context, not fresh batch evidence.

## Do Not Do

- Do not interpret tester PF/PnL as profitable, live-ready, tradable, or model-quality proof.
- Do not select a new winner from this diagnostic rerun.
- Do not use or open `locked_test` for any choice.
- Do not let `latency_bars>0` artifacts participate in default batch selection.

## Next Step

Investigate MT5/Wine tester file output: smoke and the first two full-batch runs wrote event files, but 30/32 full-batch runs failed with missing expected `mt5_trade_events_<run_id>.csv`.

After fixing the event-output issue, rerun `./.venv/bin/python -m ML.baseline.run_mt5_batch --phase all` and then regenerate event diagnostics. Keep verdict at `DIAGNOSTIC_ONLY`.

## Verification

Completed relevant checks:

- targeted schema/parser/diagnostics pytest subsets passed during Tasks 1-5.
- `./.venv/bin/python -m pytest tests/test_mt5_execution_diagnostics.py -q` -> `21 passed` after final diagnostics fix.
- MetaEditor compile log contained `Result: 0 errors, 0 warnings`.
- `./.venv/bin/python -m ML.baseline.run_mt5_batch --phase signals` regenerated 32 signal artifacts.
- timing verification over 32 signal CSVs passed.
- smoke tester passed.
- full-batch runtime verification remains `UNKNOWN` because expected event files were missing for 30/32 runs.
