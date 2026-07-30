# MT5 Single Rule Diagnostic Run Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run one fixed entry-only diagnostic signal set through MT5 Strategy Tester, parse `mt5_trade_events.csv`, and produce a factual reconciliation report without ML-profitability claims.

**Architecture:** Keep Python responsible only for frozen entry-signal export and event-log parsing. Keep MT5 responsible for order placement, fill, SL/TP/close mechanics, and event logging. Treat the whole stage as `DIAGNOSTIC_ONLY` until MT5 `Nero.csv` parity, tester event lifecycle, and feature timing are proven.

**Tech Stack:** Python 3 via `./.venv/bin/python`, pandas, pytest, MQL5, MetaEditor 5 under Wine, MT5 Strategy Tester.

```text
depends_on: docs/reports/2026-07-29-mt5-execution-loop-migration.md; docs/reports/2026-07-29-mt5-manual-tester-runbook.md
blocks: MT5 batch selection for 20-50 candidates
supersedes: none
exit_decisions: continue | close | unblock
locked_test_policy: not used for new selection; no winner/threshold/rule/cost/entry/exit/stop selection
```

## Global Constraints

- Work on the current branch; do not switch branches inside this plan.
- Do not run full test suite command `./.venv/bin/python -m pytest tests/ -q`; run only targeted tests named in this plan.
- Do not use `locked_test` to choose a winner, threshold, rule, feature, cost model, entry, exit, or stop.
- This plan may use existing fixed/diagnostic source signals only; it must not create a new ML search.
- All results from this plan are `DIAGNOSTIC_ONLY`.
- If MT5 tester cannot be launched by the agent, stop at a manual run package and state exactly what the user must run.
- Do not edit unrelated docs or code.

## Methodology Map

- `docs/methodology/README.md`: main principle. Result is not model quality until data, features, split, export, and execution match the decision time.
- `docs/methodology/03-feature-contract-leakage.md`: applies to entry CSV and any ML-derived columns. Required checks: no future/result columns in entry CSV; `feature_time <= feature_available_time <= decision_time`; no new `locked_test` selection.
- `docs/methodology/12-backtest-costs.md`: applies to execution interpretation. Required checks: entry price is executable only through tester fill; costs and missing opens are not ignored.
- `docs/methodology/13-export-mt4-parity.md`: applies by inheritance through MT5 parity methodology. Required checks: frozen export hash, row counts, opened/closed trades, missing opens, close reasons, event-log cleanup.
- `docs/methodology/13b-mt5-execution-parity.md`: primary methodology for this plan. Required checks: compile from git source, copy signal CSV to actual tester `Files`, run tester with diagnostic inputs, parse event CSV, record tester metadata.
- `docs/methodology/16-reporting-audit.md`: applies to final report. Required checks: commands, paths, hashes, limitations, verdict, and next decision are recorded.

## Known Unknowns

- The actual MT5 tester `Files` directory is not proven. It must be discovered during Task 4 or filled by the user.
- Automatic MT5 Strategy Tester launch from this environment is not proven. The plan first attempts to compile and package the run; if tester launch is unavailable, it produces a manual run package.
- MT5 `Nero.csv` row-by-row parity with MT4/current source is currently `UNKNOWN`.
- Current MQL5 event lifecycle is known to be limited on H1-bar polling; same-H1 open-and-close trades may not be fully reconstructed. This plan must measure or document that limitation, not hide it.

---

## Task 1: Freeze Scope And Pick One Diagnostic Source

**Files:**
- Read: `docs/superpowers/roadmap.md`
- Read: `docs/reports/2026-07-29-mt5-execution-loop-migration.md`
- Read: `ML/baseline/export_mt5_entry_signals.py`
- Read: `ML/baseline/mt5_signal_schema.py`
- Create: `ML/reports/mt5_execution_loop/mt5_single_rule_run_manifest_<run_id>.json`

**Interfaces:**
- Consumes: existing source CSV with columns accepted by `export_mt5_entry_signals.py`: `time`, `feature_time`, `feature_available_time`, `decision_time`, `side`, `limit_price`, `stop_price` or `protective_stop_price`, `atr` or `ATR`, optional `rule_id`.
- Produces: fixed `run_id`, selected source path, source hash, date range, and `max_fill_lag_bars` for later tasks.

**Methodology:** `00-research-management.md` for frozen scope; `03-feature-contract-leakage.md` for no future/result fields in export; `13b-mt5-execution-parity.md` for diagnostic-only MT5 contour.

- [ ] **Step 1: Inspect available source candidates**

Run:

```bash
rg --files ML/reports DATA MT/MQL4/Files | rg '(^|/)(.*fixed11.*|.*entry.*|.*signal.*).*\.csv$'
```

Expected: identify one existing source CSV. Prefer a recent fixed diagnostic source already used in reports. Do not create or select a new rule by profitability. Do not treat missing `MT/MQL5/Files` as an error; the real MT5 tester file directory is discovered in Task 4.

- [ ] **Step 2: Verify source has required columns**

Run, replacing `<source_csv>`:

```bash
./.venv/bin/python - <<'PY'
from pathlib import Path
import pandas as pd

path = Path("<source_csv>")
df = pd.read_csv(path, sep=";")
required_any = {
    "time": ["time"],
    "feature_time": ["feature_time"],
    "feature_available_time": ["feature_available_time"],
    "decision_time": ["decision_time"],
    "side": ["side"],
    "limit_price": ["limit_price"],
    "stop_price": ["stop_price", "protective_stop_price"],
    "atr": ["atr", "ATR"],
}
for label, cols in required_any.items():
    if not any(col in df.columns for col in cols):
        raise SystemExit(f"missing {label}: expected one of {cols}")
print({"path": str(path), "rows": len(df), "columns": len(df.columns)})
PY
```

Expected: command prints path, row count, and column count. If required columns are absent, stop and write the missing columns under "Known Unknowns" in the manifest.

- [ ] **Step 3: Create run manifest**

Create `ML/reports/mt5_execution_loop/mt5_single_rule_run_manifest_<run_id>.json` with this exact structure:

```json
{
  "status": "DIAGNOSTIC_ONLY",
  "run_id": "<run_id>",
  "source_csv": "<source_csv>",
  "source_csv_sha256": "<sha256>",
  "selection_policy": "existing fixed diagnostic source; no new selection by tester result",
  "symbol": "XAUUSD",
  "timeframe": "H1",
  "max_fill_lag_bars": 6,
  "date_from": "<first source time or tester date_from>",
  "date_to": "<last source time or tester date_to>",
  "date_range_policy": "source time range unless Task 4 records narrower tester range",
  "locked_test_policy": "not used for new selection",
  "methodology": [
    "docs/methodology/03-feature-contract-leakage.md",
    "docs/methodology/12-backtest-costs.md",
    "docs/methodology/13-export-mt4-parity.md",
    "docs/methodology/13b-mt5-execution-parity.md",
    "docs/methodology/16-reporting-audit.md"
  ],
  "unknowns": [
    "actual MT5 tester Files path",
    "automatic Strategy Tester launch availability",
    "MT5 Nero.csv row-by-row parity status"
  ]
}
```

Use this command to compute `<sha256>`:

```bash
sha256sum <source_csv>
```

**Mandatory checks:** source is pre-existing; source hash recorded; source date range recorded or explicitly marked as pending tester range; no new profitability-based selection.

**Completion criterion:** manifest exists and contains `status=DIAGNOSTIC_ONLY`, source path, source hash, source/tester date range policy, and fixed `max_fill_lag_bars`.

---

## Task 2: Export Entry-Only MT5 Signals

**Files:**
- Modify only if tests fail for a confirmed bug: `ML/baseline/export_mt5_entry_signals.py`
- Modify only if schema tests fail for a confirmed bug: `ML/baseline/mt5_signal_schema.py`
- Create: `ML/reports/mt5_execution_loop/mt5_entry_signals_<run_id>.csv`
- Create: `ML/reports/mt5_execution_loop/mt5_entry_signals_<run_id>.json`

**Interfaces:**
- Consumes: manifest from Task 1.
- Produces: `mt5_entry_signals_<run_id>.csv` with columns from `MT5_SIGNAL_COLUMNS`; JSON sidecar with counts and hashes.

**Methodology:** `03-feature-contract-leakage.md`; `13b-mt5-execution-parity.md`.

- [ ] **Step 1: Run focused exporter tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_mt5_signal_executor_schema.py::test_export_mt5_entry_signals_writes_entry_only_csv -q
```

Expected: pass. If it fails, fix only the exporter/schema defect needed for this plan and rerun the same test.

- [ ] **Step 2: Export entry signals**

Run, replacing `<source_csv>` and `<run_id>`:

```bash
./.venv/bin/python -m ML.baseline.export_mt5_entry_signals \
  --source-csv <source_csv> \
  --run-id <run_id> \
  --max-fill-lag-bars 6
```

Expected: creates:

```text
ML/reports/mt5_execution_loop/mt5_entry_signals_<run_id>.csv
ML/reports/mt5_execution_loop/mt5_entry_signals_<run_id>.json
```

- [ ] **Step 3: Verify entry CSV contract**

Run:

```bash
./.venv/bin/python - <<'PY'
from pathlib import Path
import pandas as pd
from ML.baseline.mt5_signal_schema import MT5_SIGNAL_COLUMNS, MT5_FORBIDDEN_SIGNAL_COLUMNS, validate_mt5_signal_frame

path = Path("ML/reports/mt5_execution_loop/mt5_entry_signals_<run_id>.csv")
df = pd.read_csv(path, sep=";")
validate_mt5_signal_frame(df)
forbidden = sorted(set(df.columns) & MT5_FORBIDDEN_SIGNAL_COLUMNS)
if forbidden:
    raise SystemExit(f"forbidden columns exported: {forbidden}")
if list(df.columns) != MT5_SIGNAL_COLUMNS:
    raise SystemExit(f"wrong column order: {list(df.columns)}")
print({"rows": len(df), "columns": list(df.columns), "forbidden": forbidden})
PY
```

Expected: prints row count and empty forbidden list. The validator enforces `feature_time <= feature_available_time <= decision_time`.

**Mandatory checks:** no `fill_time`, `exit_time`, `pnl_r`, or future outcome columns; time order validator passes for `feature_time <= feature_available_time <= decision_time`; JSON sidecar hash exists.

**Completion criterion:** entry CSV and JSON sidecar are reproducible and validated.

---

## Task 3: Compile MT5 Expert From Git Source

**Files:**
- Read: `MT/MQL5/Experts/$o$imple.mq5`
- Read: `MT/MQL5/Include/lib_ML_Signal.mqh`
- Read: `MT/MQL5/Include/lib_PIC.mqh`
- Output: `/tmp/sosimple_mt5_compile.log`
- Output: `MT/MQL5/Experts/$o$imple.ex5`

**Interfaces:**
- Consumes: existing MT5 expert.
- Produces: compiled `.ex5` from current git source.

**Methodology:** `13b-mt5-execution-parity.md`.

- [ ] **Step 1: Verify diagnostic inputs exist**

Run:

```bash
for name in \
  InpMT5_DiagnosticExecutor \
  InpMT5_EntrySignalFile \
  InpMT5_EventFile \
  InpMT5_BlockBarsSinceFill0Exit \
  InpMT5_ExportNero \
  InpMT5_NeroFile
do
  rg -n "$name" MT/MQL5/Experts/'$o$imple.mq5' >/dev/null || exit 1
done
```

Expected: all six inputs are present.

- [ ] **Step 2: Compile with MetaEditor 5**

Run:

```bash
WINEPREFIX=/home/hohla/.mt5 xvfb-run -a wine \
  '/home/hohla/.mt5/drive_c/Program Files/MetaTrader 5/MetaEditor64.exe' \
  /compile:'/home/hohla/git/SoSimple/MT/MQL5/Experts/$o$imple.mq5' \
  /log:'/tmp/sosimple_mt5_compile.log'
```

Expected: Wine exit code may be non-zero. Do not use it as final verdict.

- [ ] **Step 3: Read compile verdict**

Run:

```bash
iconv -f UTF-16LE -t UTF-8 /tmp/sosimple_mt5_compile.log | tail -n 30
```

Expected: `Result: 0 errors, 0 warnings`.

- [ ] **Step 4: Verify `.ex5` timestamp**

Run:

```bash
stat MT/MQL5/Experts/'$o$imple.mq5' MT/MQL5/Experts/'$o$imple.ex5'
```

Expected: `.ex5` modification time is not older than `$o$imple.mq5`.

**Mandatory checks:** compile log says `0 errors, 0 warnings`; `.ex5` is current.

**Completion criterion:** compiled expert is ready for tester run or a clear compile blocker is recorded.

---

## Task 4: Package And Run One MT5 Tester Diagnostic

**Files:**
- Input: `ML/reports/mt5_execution_loop/mt5_entry_signals_<run_id>.csv`
- Output from tester: `mt5_trade_events.csv`
- Optional output from tester: HTML/XML tester report
- Modify only if needed to expose file paths: `MT/MQL5/Include/lib_ML_Signal.mqh`

**Interfaces:**
- Consumes: compiled `.ex5`, entry CSV.
- Produces: real tester event CSV or manual-run blocker with exact missing path/action.

**Methodology:** `12-backtest-costs.md`; `13-export-mt4-parity.md`; `13b-mt5-execution-parity.md`.

- [ ] **Step 1: Discover actual MT5 tester Files directory**

Preferred: use MT5 terminal logs or a minimal tester run that prints `TerminalInfoString(TERMINAL_DATA_PATH)` and the file path used by `FileOpen()`.

If the agent cannot discover it automatically, stop this task and ask the user for the actual tester `Files` path. Do not assume `MT/MQL5/Files`.

- [ ] **Step 2: Copy signal CSV**

Copy:

```text
ML/reports/mt5_execution_loop/mt5_entry_signals_<run_id>.csv
```

to the discovered tester `Files` directory as:

```text
mt5_entry_signals.csv
```

Do not rename the repo artifact.

- [ ] **Step 3: Run Strategy Tester**

Use:

```text
Expert: MT/MQL5/Experts/$o$imple.ex5
Symbol: XAUUSD
Timeframe: H1
InpMT5_DiagnosticExecutor=true
InpMT5_EntrySignalFile=mt5_entry_signals.csv
InpMT5_EventFile=mt5_trade_events.csv
InpMT5_BlockBarsSinceFill0Exit=true
```

Record exact values:

```text
MT5 build
broker/server
tester model
date_from/date_to
deposit/currency/leverage
spread mode
account mode: netting or hedging
actual signal CSV path
actual event CSV path
```

- [ ] **Step 4: Bring back event CSV**

Copy the tester-produced `mt5_trade_events.csv` to:

```text
ML/reports/mt5_execution_loop/mt5_trade_events_<run_id>.csv
```

If tester produced an HTML/XML report, copy it to:

```text
ML/reports/mt5_execution_loop/mt5_tester_report_<run_id>.<html-or-xml>
```

- [ ] **Step 5: Hash returned tester artifacts**

Run:

```bash
sha256sum ML/reports/mt5_execution_loop/mt5_trade_events_<run_id>.csv
```

If an HTML/XML tester report exists, include it in the same `sha256sum` command.

**Mandatory checks:** tester uses the copied entry CSV; event log is from the current run; event file is not stale from a previous run; event CSV hash is recorded.

**Completion criterion:** event CSV exists for this run, or the plan records a concrete manual blocker.

---

## Task 5: Parse Event Log And Classify Execution Gaps

**Files:**
- Read: `ML/reports/mt5_execution_loop/mt5_trade_events_<run_id>.csv`
- Modify only if parser schema is wrong: `ML/baseline/parse_mt5_execution_report.py`
- Modify only if schema validation is wrong: `ML/baseline/mt5_signal_schema.py`
- Create: `ML/reports/mt5_execution_loop/mt5_execution_metrics_<run_id>.json`

**Interfaces:**
- Consumes: tester event CSV.
- Produces: parsed metrics with event counts, open/close counts, close reasons, missing-open estimate, open-without-close estimate, and diagnostic profit sum.

**Methodology:** `13-export-mt4-parity.md`; `13b-mt5-execution-parity.md`.

- [ ] **Step 1: Run focused parser tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_parse_mt5_execution_report.py -q
```

Expected: pass. If it fails, fix only parser/schema defects related to MT5 event parsing.

- [ ] **Step 2: Parse tester events**

Run:

```bash
./.venv/bin/python -m ML.baseline.parse_mt5_execution_report \
  --events ML/reports/mt5_execution_loop/mt5_trade_events_<run_id>.csv \
  --output-json ML/reports/mt5_execution_loop/mt5_execution_metrics_<run_id>.json
```

Expected: output JSON with `status=DIAGNOSTIC_ONLY`.

- [ ] **Step 3: Verify timing contract**

Run:

```bash
./.venv/bin/python - <<'PY'
from pathlib import Path
import pandas as pd
from ML.baseline.mt5_signal_schema import validate_mt5_event_frame

path = Path("ML/reports/mt5_execution_loop/mt5_trade_events_<run_id>.csv")
df = pd.read_csv(path, sep=";")
validate_mt5_event_frame(df)
counts = df["event"].astype(str).value_counts().to_dict()
print({"rows": len(df), "event_counts": counts})
PY
```

Expected: schema and `feature_time <= feature_available_time <= decision_time <= execution_time` pass.

- [ ] **Step 4: Classify lifecycle limitations**

Inspect counts:

```bash
./.venv/bin/python - <<'PY'
from pathlib import Path
import pandas as pd

path = Path("ML/reports/mt5_execution_loop/mt5_trade_events_<run_id>.csv")
df = pd.read_csv(path, sep=";")
events = df["event"].astype(str).value_counts()
placed = int(events.get("ORDER_PLACED", 0))
opened = int(events.get("OPEN", 0))
closed = int(events.get("CLOSE", 0))
ml_close = int(events.get("ML_CLOSE", 0))
print({
    "ORDER_PLACED": placed,
    "OPEN": opened,
    "CLOSE": closed,
    "ML_CLOSE": ml_close,
    "missing_open_estimate": max(placed - opened, 0),
    "open_without_close_estimate": max(opened - closed, 0),
})
PY
```

Expected: counts are reported. Do not call gaps harmless unless event/deal rows prove that.

- [ ] **Step 5: Classify same-H1 lifecycle evidence**

If MT5 tester HTML/XML report or MT5 history/deals export is available, compare its trade/deal count with `OPEN` and `CLOSE` event counts from `mt5_trade_events_<run_id>.csv`.

If no independent tester report or deal export is available, write this exact status into the report inputs:

```text
same_h1_lifecycle_status=UNKNOWN
reason=no independent MT5 history/deals or tester report available to detect same-H1 open-and-close rows missed by H1 event polling
```

- [ ] **Step 6: Hash structured metric artifacts**

Run after parser output exists:

```bash
sha256sum \
  ML/reports/mt5_execution_loop/mt5_trade_events_<run_id>.csv \
  ML/reports/mt5_execution_loop/mt5_execution_metrics_<run_id>.json
```

Expected: both hashes are recorded for the report.

**Mandatory checks:** parser passes; event schema passes; event counts and lifecycle gaps are explicitly classified; same-H1 lifecycle is either compared to independent tester/deal data or marked `UNKNOWN`.

**Completion criterion:** metrics JSON exists and all critical mismatches are either zero, classified, or marked blocker.

---

## Task 6: Produce Diagnostic Report And Update Current Work Point

**Files:**
- Create: `docs/reports/2026-07-30-mt5-single-rule-diagnostic-run.md`
- Modify: `CONTEXT_HANDOFF.md`
- Modify only if roadmap status changes: `docs/superpowers/roadmap.md`
- Modify only if this is a significant completed stage: `CHANGELOG.md`
- Optional wiki ingest only if project wiki workflow is available and required by `stage-reporting`.

**Interfaces:**
- Consumes: manifest, entry CSV sidecar, compile log verdict, tester metadata, event metrics JSON, tester report if present.
- Produces: factual stage report and next-step decision.

**Methodology:** `16-reporting-audit.md`; `13b-mt5-execution-parity.md`.

- [ ] **Step 1: Write report**

Report must include:

```text
Status: DIAGNOSTIC_ONLY
Context
Stage Level
What Was Done
Multiple Testing Context: no new ML search; no new winner/threshold/rule/cost/entry/exit/stop selection
Changed Files
Verification
Results
Conclusions
Limitations / Open Questions
Split Disclosure: locked_test not used
Next Step
Related Materials
forbidden_interpretations
Source CSV path and sha256
Entry CSV path and sha256
Compile command and compile verdict
Tester metadata
Event CSV path and sha256
Metrics JSON path and sha256
Event counts
Missing open estimate
Open without close estimate
same_h1_lifecycle_status
Known lifecycle limitations
Whether MT5 Nero.csv parity is PASS, FAIL, UNKNOWN, or not tested
Decision: continue, close, or unblock
```

Forbidden report claims:

```text
profitable
production-ready
candidate passed
MT5 parity proven
ML quality improved
```

unless each claim is backed by this run and applicable methodology checks.

- [ ] **Step 2: Update handoff**

Update `CONTEXT_HANDOFF.md` with:

```text
Current point: MT5 single-rule diagnostic run
Last completed artifact: docs/reports/2026-07-30-mt5-single-rule-diagnostic-run.md
Next action: based on report decision
Do not run full pytest tests/ -q
```

- [ ] **Step 3: Update roadmap only if decision changes ACTIVE**

If single-rule diagnostic is successful, update `docs/superpowers/roadmap.md` so `ACTIVE` points to the next concrete step. If tester run is blocked, leave `ACTIVE` on MT5 execution-loop prototype and record the blocker in `CONTEXT_HANDOFF.md`, not as roadmap history.

- [ ] **Step 4: Run final targeted checks**

Run:

```bash
./.venv/bin/python -m pytest tests/test_mt5_signal_executor_schema.py tests/test_parse_mt5_execution_report.py -q
git diff --check -- docs/reports/2026-07-30-mt5-single-rule-diagnostic-run.md CONTEXT_HANDOFF.md docs/superpowers/roadmap.md CHANGELOG.md ML/reports/mt5_execution_loop
```

Expected: targeted tests pass; `git diff --check` has no output.

**Mandatory checks:** report separates facts from unknowns; no profitability verdict; handoff points to the next concrete action.

**Completion criterion:** report, handoff, and any necessary roadmap/changelog updates are consistent with produced artifacts.

---

## Self-Review

- Spec coverage: plan covers current roadmap `ACTIVE` item: MT5 `Nero.csv` parity status, entry-only signal generation, Strategy Tester diagnostic run, event parsing, and reconciliation.
- Methodology coverage: each task names relevant methodology, mandatory checks, and completion criterion.
- Placeholder scan: plan contains no unfinished placeholder steps.
- Type consistency: file names use the same `<run_id>` convention across signal CSV, sidecar JSON, tester event CSV, metrics JSON, and report.
- Known gaps are explicit: tester path, automatic tester launch, MT5 `Nero.csv` parity, and H1 lifecycle logging limits.
