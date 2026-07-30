# CONTEXT HANDOFF

## Current Active State

- active track: `MT5 execution-loop prototype`
- latest report: `docs/reports/2026-07-29-mt5-execution-loop-migration.md`
- latest plan: `docs/superpowers/plans/2026-07-29-mt5-execution-loop-migration.md`
- primary MT5 expert: `MT/MQL5/Experts/$o$imple.mq5`
- MT5 signal schema validator: `ML/baseline/mt5_signal_schema.py`
- MT5 execution methodology: `docs/methodology/13b-mt5-execution-parity.md`
- MT5 open-position feature contract: `docs/schemas/mt5_open_position_feature_contract.md`
- MT5 producer contract: `docs/schemas/mt5_nero_csv_contract.md`
- Python exporter: `ML/baseline/export_mt5_entry_signals.py`
- Python event parser: `ML/baseline/parse_mt5_execution_report.py`
- environment manifest: `ML/reports/mt5_execution_loop/mt5_environment_manifest.json`
- parity manifest: `ML/reports/mt5_execution_loop/mt5_nero_parity_manifest.json`

## Decision

MT5 diagnostic execution-loop prototype is prepared, but remains
`DIAGNOSTIC_ONLY`.

- verdict: `DIAGNOSTIC_ONLY`
- compile status: MetaEditor reports `0 errors, 0 warnings`
- tester runtime status: not run by agent
- MT5 `Nero.csv` producer parity: `UNKNOWN`
- manual user run: required before event metrics can be interpreted

## Current Diagnostic Facts

- Existing MT5 `$o$imple.mq5` is the primary target; no fallback expert was created.
- MT5 producer is default-off through `InpMT5_ExportNero=false`.
- MT5 diagnostic executor is default-off through `InpMT5_DiagnosticExecutor=false`.
- Entry signal CSV is entry-only and forbids `fill_time`, `exit_time`, `future_exit_time`, `pnl_r`.
- Event log schema includes order/fill/close fields and post-fill features.
- Diagnostic scorer can request `ML_CLOSE`, but it is not a trained model.
- `bars_since_fill=0` cannot trigger diagnostic ML-close.
- `OPEN/CLOSE` logging remains limited until actual MT5 tester history/deals are reconciled.

## Do Not Do

- Do not claim MT5 metrics exist until `mt5_trade_events.csv` comes from a real tester run.
- Do not treat the diagnostic scorer as ML-quality proof.
- Do not use Python PF/PnL as final selection metric when MT5 is the execution engine.
- Do not run batch selection before single-rule MT5 run and `Nero.csv` producer parity are understood.
- Do not claim feature-leakage safety from tester execution alone.

## Next Step

Run one manual MT5 tester diagnostic:

1. Follow `docs/reports/2026-07-29-mt5-manual-tester-runbook.md`.
2. Confirm MT5 tester file directory.
3. Generate/copy `mt5_entry_signals.csv`.
4. Run `MT/MQL5/Experts/$o$imple.mq5` with `InpMT5_DiagnosticExecutor=true`.
5. Return `mt5_trade_events.csv`.
6. Parse it with `ML/baseline/parse_mt5_execution_report.py`.

## Verification

Completed:

- `./.venv/bin/python -m pytest tests/test_mt5_signal_executor_schema.py tests/test_parse_mt5_execution_report.py -q`
- MetaEditor compile of `MT/MQL5/Experts/$o$imple.mq5`: `Result: 0 errors, 0 warnings`
- static checks from MT5 migration plan

Full `./.venv/bin/python -m pytest tests/ -q` was not run because this plan
explicitly forbids the full suite.
