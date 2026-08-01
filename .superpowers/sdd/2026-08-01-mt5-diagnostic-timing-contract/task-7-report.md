## Task 7 report

- Date: 2026-08-01
- Scope: regenerate MT5 diagnostic artifacts and verify runtime in the exact brief order.
- Runtime verdict: UNKNOWN

### 1. Expert string check

Command:

```bash
rg -n "#property tester_file \"mt5_entry_signals.csv\"|int      bar=1|MT5_FindEntrySignal\\(Time\\[bar\\]\\)" 'MT/MQL5/Experts/$o$imple.mq5' MT/MQL5/Include/lib_ML_Signal.mqh
```

Observed:

```text
MT/MQL5/Include/lib_ML_Signal.mqh:777:      int mt5_idx = MT5_FindEntrySignal(Time[bar]);
MT/MQL5/Experts/$o$imple.mq5:6:#property tester_file "mt5_entry_signals.csv"
MT/MQL5/Experts/$o$imple.mq5:83:int      bar=1, Today, TesterFile;
```

Verdict: PASS.

### 2. Compile expert

Sandbox compile attempt failed with:

```text
Bad system call (core dumped)
```

Escalated compile command:

```bash
WINEPREFIX=/home/hohla/.mt5 xvfb-run -a wine \
  '/home/hohla/.mt5/drive_c/Program Files/MetaTrader 5/MetaEditor64.exe' \
  /compile:'/home/hohla/git/SoSimple/MT/MQL5/Experts/$o$imple.mq5' \
  /log:'/tmp/sosimple_mt5_compile.log'
iconv -f UTF-16LE -t UTF-8 /tmp/sosimple_mt5_compile.log | tail -n 20
```

Observed tail:

```text
Result: 0 errors, 0 warnings, 5172 ms elapsed, cpu='X64 Regular'
```

`.ex5` timestamp after compile:

```text
2026-08-01 12:38:39.674336338 +0000 MT/MQL5/Experts/$o$imple.ex5
```

Verdict: PASS.

### 3. Regenerate signals

Command:

```bash
./.venv/bin/python -m ML.baseline.run_mt5_batch --phase signals
```

Observed:

```text
Signal generation done: 32 generated, 0 skipped (already existed).
```

Verdict: PASS.

### 4. Verify regenerated signal timing

Command: exact Python check from the brief.

Observed:

```text
{'checked_signal_files': 32, 'bad_files': 0}
```

Verdict: PASS.

### 5. Smoke tester

Sandbox attempt failed because MT5 runtime path is outside workspace write scope:

```text
OSError: [Errno 30] Read-only file system: '/home/hohla/.mt5/drive_c/Program Files/MetaTrader 5/MQL5/Files/mt5_entry_signals.csv'
```

Escalated command: exact Python smoke command from the brief.

Observed:

```text
SMOKE TEST: simple_combined_extra_trees_small_3h_thr0.05 (Model=2, 2021.01-2021.03)
  SMOKE RESULT: positions=3, UNEXPLAINED=0
```

Verdict: PASS.

### 6. Full batch

First `--phase all` run exposed stale runtime artifacts from 2026-07-31: `run_mt5_batch.py` skipped tester when `metrics.json` already existed with `UNEXPLAINED=0`. That left old `events.csv` in place and produced false timing failures in later diagnostics.

To actually regenerate Task 7 runtime artifacts, I removed only generated Task 7 scope artifacts:

```text
ML/reports/mt5_execution_loop/batch/*/events.csv
ML/reports/mt5_execution_loop/batch/*/metrics.json
ML/reports/mt5_execution_loop/batch/batch_summary.json
ML/reports/mt5_execution_loop/diagnostics/event_anomaly_summary.json
ML/reports/mt5_execution_loop/diagnostics/event_anomalies.csv
```

Then reran:

```bash
./.venv/bin/python -m ML.baseline.run_mt5_batch --phase all
```

Observed final batch result:

```text
Batch complete: 2 done, 0 skipped, 30 failed.
Verdict: BATCH_NO_WINNER
Summary written to /home/hohla/git/SoSimple/ML/reports/mt5_execution_loop/batch/batch_summary.json
```

Successful runtime runs:

```text
[1/32] simple_combined_extra_trees_small_3h_thr0.05 -> DONE (68s): positions=58, UNEXPLAINED=0
[2/32] simple_combined_extra_trees_small_3h_thr0.1  -> DONE (70s): positions=88, UNEXPLAINED=0
```

Repeated runtime failure pattern for the remaining 30 runs:

```text
ERROR: events file not found: /home/hohla/.mt5/drive_c/Program Files/MetaTrader 5/Tester/Agent-127.0.0.1-3000/MQL5/Files/mt5_trade_events_<run_id>.csv
```

Verdict: UNKNOWN for full runtime verification because the environment did not produce the expected tester event files for 30/32 runs.

### 7. Timing diagnostics

Command:

```bash
./.venv/bin/python -m ML.baseline.mt5_execution_diagnostics \
  --phase events \
  --output-json ML/reports/mt5_execution_loop/diagnostics/event_anomaly_summary.json \
  --output-csv ML/reports/mt5_execution_loop/diagnostics/event_anomalies.csv
```

Observed for regenerated batch runs:

```text
batch_runs.timing_contract.checked_rows = 2189
batch_runs.timing_contract.violation_rows = 0
batch_runs.timing_contract.timing_violation_event_count = 0
```

Observed for legacy reference runs bundled into the same summary:

```text
reference_runs.timing_contract.violation_rows = 22510
```

Interpretation:

- Regenerated batch runs that actually emitted events satisfy the timing contract.
- The `reference_runs` block still reports historical legacy violations and is not evidence against the two regenerated batch runs.
- Full 32-run timing verification is UNKNOWN because only 2 batch runs emitted fresh event logs.

### 8. Artifacts produced in this task

- Regenerated `entry_signals.json` timing metadata for all 32 batch run directories.
- Fresh runtime artifacts for:
  - `simple_combined_extra_trees_small_3h_thr0.05`
  - `simple_combined_extra_trees_small_3h_thr0.1`
- Fresh:
  - `ML/reports/mt5_execution_loop/batch/batch_summary.json`
  - `ML/reports/mt5_execution_loop/diagnostics/event_anomaly_summary.json`
  - `ML/reports/mt5_execution_loop/diagnostics/event_anomalies.csv`

### Final verdict

- Expert strings: PASS
- Compile: PASS
- Signal regeneration: PASS
- Signal timing verification: PASS
- Smoke tester: PASS
- Full 32-run runtime verification: UNKNOWN
- Full 32-run timing diagnostics: UNKNOWN

Cause of UNKNOWN: MT5 tester environment did not write the expected per-run `mt5_trade_events_<run_id>.csv` files for 30 of 32 batch runs, despite the same workflow succeeding for smoke and the first two full runs.
