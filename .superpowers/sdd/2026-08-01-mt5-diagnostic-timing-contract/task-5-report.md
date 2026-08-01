# Task 5 Report: Batch Timing Diagnostics

## Status
- Added the three required timing diagnostics tests to `tests/test_mt5_execution_diagnostics.py`.
- Confirmed the expected red stage: targeted pytest selection failed because `summarize_timing_contract` was missing.
- Added `TIMING_CHECK_EVENT_NAMES`, `TIMING_CONTRACT_COLUMNS`, `_complete_timing_rows`, and `summarize_timing_contract()` to `ML/baseline/mt5_execution_diagnostics.py`.
- Included `timing_contract` in `summarize_event_anomalies()`.

## Test Results
- Expected failing command:
  - `./.venv/bin/python -m pytest tests/test_mt5_execution_diagnostics.py::test_summarize_timing_contract_excludes_tx_rows_with_empty_timing_fields tests/test_mt5_execution_diagnostics.py::test_summarize_timing_contract_reports_signal_time_violation tests/test_mt5_execution_diagnostics.py::test_summarize_timing_contract_reports_invalid_timestamp_separately -q`
  - Result before implementation: `3 failed`
- Full required suite after fix:
  - `./.venv/bin/python -m pytest tests/test_mt5_execution_diagnostics.py -q`
  - Result: `17 passed`

## Diagnostics Command
- Command run against current MT5 event artifacts with temp outputs:
  - `./.venv/bin/python -m ML.baseline.mt5_execution_diagnostics --phase events --output-json /tmp/task5_timing_events_summary.json --output-csv /tmp/task5_timing_events_anomalies.csv`
- Result:
  - command failed while reading current reference artifacts, before summary output;
  - exception: `ValueError: MT5 timing contract violation: signal_time >= feature_available_time`
- Interpretation:
  - the new diagnostics code is in place and tests pass;
  - current event artifacts still contain at least one pre-existing timing-contract violation.

## Files Changed
- `ML/baseline/mt5_execution_diagnostics.py`
- `tests/test_mt5_execution_diagnostics.py`

## Review Fix (2026-08-01)
- Problem: batch diagnostics loaded event CSVs through `parse_mt5_events()`, so strict `validate_mt5_event_frame()` raised on `signal_time >= feature_available_time` before `summarize_timing_contract()` could count the violation.
- Fix: `load_event_rows()` now uses a diagnostics-only loader that first tries strict `parse_mt5_events()`, and falls back only for `MT5 timing contract violation:` errors.
- Diagnostics fallback keeps the schema guardrails that matter here:
  - backfills legacy execution-context columns exactly like `parse_mt5_events()`;
  - still raises on missing `MT5_EVENT_COLUMNS`;
  - still raises on unknown event names;
  - still returns columns in canonical `MT5_EVENT_COLUMNS` order.
- Scope guard: strict validation elsewhere is unchanged because the fallback lives only inside `ML/baseline/mt5_execution_diagnostics.py`.
- Added integration coverage in `tests/test_mt5_execution_diagnostics.py` proving `build_event_anomaly_outputs()` returns `reference_runs.timing_contract` with one counted `signal_time < feature_available_time` violation for an invalid event CSV instead of raising.

## Verification
- `./.venv/bin/python -m pytest tests/test_mt5_execution_diagnostics.py::test_build_event_anomaly_outputs_tolerates_timing_violation_in_diagnostic_load -q`
  - Result: `1 passed`
- `./.venv/bin/python -m pytest tests/test_mt5_execution_diagnostics.py -q`
  - Result: `18 passed`

## Remaining Review Fix (2026-08-01)
- Review finding: diagnostics fallback could load a legacy row after strict validation failed, but `summarize_timing_contract()` only counted rows with all five timing fields, so a row with empty `signal_time` and `feature_time > feature_available_time` could disappear as `checked_rows=0`, `violation_rows=0`.
- Fix applied in `ML/baseline/mt5_execution_diagnostics.py`:
  - kept strict parser behavior untouched for non-diagnostic paths;
  - extended diagnostics summary to count legacy complete 4-field timing rows when `signal_time` is empty;
  - added legacy rule accounting for `feature_time <= feature_available_time`, plus the existing downstream order checks without `signal_time`.
- Regression coverage added in `tests/test_mt5_execution_diagnostics.py`:
  - `test_summarize_timing_contract_reports_legacy_violation_without_signal_time`
  - proves `feature_time > feature_available_time` with empty `signal_time` now reports one checked row and one violation row.
- Verification:
  - `./.venv/bin/python -m pytest tests/test_mt5_execution_diagnostics.py -q`
  - Result: `19 passed`

## Final Review Fix (2026-08-01)
- Review finding: coverage still missed `timing_violation_event_count` inside `summarize_timing_contract()`, so the summary field could regress without a direct unit-test failure.
- Fix applied:
  - added `test_summarize_timing_contract_counts_timing_violation_events_separately` to `tests/test_mt5_execution_diagnostics.py`;
  - the test proves `TIMING_VIOLATION` rows are counted in `timing_violation_event_count` while remaining excluded from `checked_rows` and `violation_rows`.
- Verification:
  - `./.venv/bin/python -m pytest tests/test_mt5_execution_diagnostics.py -q`
  - Result: `20 passed`
  - `./.venv/bin/python -m ML.baseline.mt5_execution_diagnostics --phase events --output-json ML/reports/mt5_execution_loop/diagnostics/event_anomaly_summary.json --output-csv ML/reports/mt5_execution_loop/diagnostics/event_anomalies.csv`
  - Result: exit `0`; command rewrote `ML/reports/mt5_execution_loop/diagnostics/event_anomaly_summary.json` and `ML/reports/mt5_execution_loop/diagnostics/event_anomalies.csv`
  - Scope note: generated diagnostics artifacts changed during verification and are intentionally left out of this final Task 5 review-fix commit.

## Final Review Finding Fix (2026-08-01)
- Review finding: `summarize_event_anomalies()` kept its protective early return for frames without `event`, but the added `timing_contract` branch called `summarize_timing_contract(events)`, which accessed `events["event"]` and raised `KeyError` on a non-empty malformed frame.
- Fix applied:
  - restored the safe path by treating `event`-less input as a diagnostic-only empty timing summary inside `summarize_timing_contract()`;
  - kept the existing protective `summarize_event_anomalies()` return shape unchanged for non-empty frames missing `event`.
- Regression coverage:
  - added `test_summarize_event_anomalies_handles_non_empty_frame_without_event_column`;
  - the test proves the function now returns the protective summary plus an empty `timing_contract` block instead of raising.
- Verification:
  - `./.venv/bin/python -m pytest tests/test_mt5_execution_diagnostics.py -k non_empty_frame_without_event_column -q`
  - Result: `1 failed` before the fix with `KeyError: 'event'`
  - `./.venv/bin/python -m pytest tests/test_mt5_execution_diagnostics.py -q`
  - Result: `21 passed`
