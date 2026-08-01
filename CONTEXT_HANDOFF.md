# CONTEXT HANDOFF

## Current Active State

- active track: `MT5 execution hygiene -> next frozen probe from saved batch artifacts`
- latest report: `docs/reports/2026-08-01-mt5-execution-hygiene-postbatch.md`
- latest plan: `docs/superpowers/plans/2026-08-01-mt5-execution-hygiene-postbatch.md`
- diagnostics CLI: `ML/baseline/mt5_execution_diagnostics.py`
- diagnostics dir: `ML/reports/mt5_execution_loop/diagnostics/`
- batch summary: `ML/reports/mt5_execution_loop/batch/batch_summary.json`

## Decision

MT5 execution hygiene and post-batch diagnostics completed as `DIAGNOSTIC_ONLY`.
Execution hygiene status: `EXECUTION_HYGIENE_PARTIAL`.

- Available `ERROR_SoSimple_*.csv` files classified.
- Reference and 32 batch event artifacts summarized; `_smoke` excluded.
- Batch failure attribution preserves `BATCH_NO_WINNER`; no new winner selected.
- Historical `ERROR_SoSimple_163856259.csv` and cumulative tester agent log are missing, abandoned as non-reproducible inputs, and must not block current batch follow-up.
- Error-to-event linkage status: `UNKNOWN`.

## Current Diagnostic Facts

- Error rows: 1879 total; `INVALID_STOPS=670`, `OTHER=621`, `REQUOTE=550`, `MODIFICATION_TOO_CLOSE=35`, `MARKET_CLOSED=2`, `INVALID_PRICE=1`.
- Source buckets: `mt4_files=1174`, `mt_tester_files=705`.
- Batch events: `batch_run_count=32`, `OPEN_FAILED=22767`, `ORDER_EXPIRED=67`.
- Post-batch top 11: all failed `BS_p05 > 1.0`; buckets `100-149=9`, `150+=2`.
- Top candidate remains diagnostic only: PF `1.2323`, `BS_p05=0.8867479736061653`, 102 trades, fill rate `0.09444444444444444`, `gross_profit=5468.199999999997`, `gross_loss=4437.3`.

## Do Not Do

- Do not interpret tester PF/PnL as profitable, live-ready, tradable, or model-quality proof.
- Do not select a new winner from this diagnostic.
- Do not use `locked_test` for any choice.
- Do not infer causality between `ERROR_SoSimple` rows and event anomalies while linkage is `UNKNOWN`.

## Next Step

Plan the next frozen probe using only current saved batch artifacts. Do not wait for historical `ERROR_SoSimple_163856259.csv` or cumulative tester agent log with external `ERROR-4756` lines.

## Verification

Completed:

- `./.venv/bin/python -m pytest tests/test_mt5_execution_diagnostics.py tests/test_parse_mt5_execution_report.py tests/test_mt5_signal_executor_schema.py -q`
- generated `error_inventory.json`, `error_summary.json`, `error_rows_classified.csv`
- generated `event_anomaly_summary.json`, `event_anomalies.csv`
- generated `post_batch_diagnostics.json`, `post_batch_top_candidates.csv`
