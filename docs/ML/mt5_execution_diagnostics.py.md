# mt5_execution_diagnostics.py

## Purpose
Read-only diagnostics for MT5 execution error logs. The module scans `ERROR_SoSimple_*.csv` files, classifies error rows by explicit message/code rules, and writes a summary plus a classified row table.

## Input
- `ERROR_SoSimple_*.csv` files found under the repository tree
- `--root` may restrict discovery to a custom subtree

## Output
- `ML/reports/mt5_execution_loop/diagnostics/error_inventory.json` for `--phase inventory`
- `ML/reports/mt5_execution_loop/diagnostics/error_summary.json` for `--phase errors`
- `ML/reports/mt5_execution_loop/diagnostics/error_rows_classified.csv` for `--phase errors`

## Command
```bash
./.venv/bin/python -m ML.baseline.mt5_execution_diagnostics \
  --phase errors \
  --output-json ML/reports/mt5_execution_loop/diagnostics/error_summary.json \
  --output-csv ML/reports/mt5_execution_loop/diagnostics/error_rows_classified.csv
```

## Schema
- `load_error_rows(paths)`: loads error rows from one or more CSV files and returns a classified `DataFrame`
- `summarize_error_rows(rows)`: returns counts by source bucket, source file, Magic, error code, and error class
- `classify_error_message(message)`: maps explicit message/code patterns to a stable error class

## Status
DIAGNOSTIC_ONLY — no model training, no mutation of source artifacts.

## Limitations
- CSV parsing is chunked with minimal `usecols` only for error diagnostics; the module does not load full tables into memory for large logs.
- The summary separates MT5 tester files from MT4 files via `source_bucket`; the result is diagnostic output, not a verdict.
- If `Lot/Ticket` is missing, row-level `Magic` stays `UNKNOWN` and the file is reported in `unknowns.missing_magic_column_files`.
