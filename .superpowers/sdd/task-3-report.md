# Task 3 Report: Export Entry-Only MT5 Signals From Python

## RED

- Added `test_export_mt5_entry_signals_writes_entry_only_csv` to `tests/test_mt5_signal_executor_schema.py`.
- Ran:

```bash
./.venv/bin/python -m pytest tests/test_mt5_signal_executor_schema.py::test_export_mt5_entry_signals_writes_entry_only_csv -q
```

- Result: `ModuleNotFoundError: No module named 'ML.baseline.export_mt5_entry_signals'`.

## GREEN

- Created `ML/baseline/export_mt5_entry_signals.py`.
- Implemented `export_mt5_entry_signals(...) -> pd.DataFrame`.
- Export frame is entry-only and validates against `MT5_SIGNAL_COLUMNS`.
- Forbidden lifecycle/result fields are not exported.
- JSON metadata includes counts, hashes, and run configuration hash.
- Added CLI with `--source-csv/--input-csv`, `--output-csv`, `--output-json`, `--run-id`, `--rule-metadata`, and `--max-fill-lag-bars`.
- Created `ML/reports/mt5_execution_loop/README.md`.

## Verification

- Passed:

```bash
./.venv/bin/python -m pytest tests/test_mt5_signal_executor_schema.py::test_export_mt5_entry_signals_writes_entry_only_csv -q
```

- Result: `1 passed in 0.19s`
