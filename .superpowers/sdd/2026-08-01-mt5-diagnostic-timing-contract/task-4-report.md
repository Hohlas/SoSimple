# Task 4 Report: MQL Reader Timing Guard

## Status
- Added three static MQL contract tests in `tests/test_mt5_signal_executor_schema.py`.
- Confirmed expected pre-fix failure of the targeted pytest selection.
- Updated `MT/MQL5/Include/lib_ML_Signal.mqh` to:
  - match entry rows only by `MT5_EntryTimes[i] == barTime`;
  - validate `feature_time <= time < feature_available_time <= decision_time` before loading a row;
  - emit `TIMING_VIOLATION` and skip invalid rows;
  - keep source `MT5_DecisionTimes[idx]` in `ML_EVAL` and `ML_CLOSE`.
- Checked `ML/baseline/parse_mt5_execution_report.py`: reconciliation depends on event names, tickets, and `position_id` from `comment`, not equality to the current bar `decision_time`.

## Test Results
- Expected failing command:
  - `./.venv/bin/python -m pytest tests/test_mt5_signal_executor_schema.py::test_mt5_find_entry_signal_uses_entry_time_only tests/test_mt5_signal_executor_schema.py::test_mt5_entry_init_logs_and_skips_timing_violations tests/test_mt5_signal_executor_schema.py::test_mt5_lifecycle_events_keep_source_decision_time -q`
  - Result before MQL changes: `3 failed`
- Static suite after fix:
  - `./.venv/bin/python -m pytest tests/test_mt5_signal_executor_schema.py -q`
  - Result: `23 passed`

## Compile Attempt
- Command run exactly as required:
  - `WINEPREFIX=/home/hohla/.mt5 xvfb-run -a wine '/home/hohla/.mt5/drive_c/Program Files/MetaTrader 5/MetaEditor64.exe' /compile:'/home/hohla/git/SoSimple/MT/MQL5/Experts/$o$imple.mq5' /log:'/tmp/sosimple_mt5_compile.log'`
- Runtime behavior:
  - initial sandbox run failed with `Bad system call (core dumped)`;
  - escalated rerun produced Wine/Xvfb shutdown noise and exit code `1`;
  - compile verdict taken from log, per brief.
- Compile log tail from `/tmp/sosimple_mt5_compile.log`:
  - `Result: 0 errors, 0 warnings, 5180 ms elapsed, cpu='X64 Regular'`

## Files Changed
- `MT/MQL5/Include/lib_ML_Signal.mqh`
- `tests/test_mt5_signal_executor_schema.py`
