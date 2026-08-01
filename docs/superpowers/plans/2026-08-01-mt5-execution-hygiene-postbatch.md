# MT5 Execution Hygiene And Post-Batch Diagnostics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Classify MT5 execution failures and produce a reproducible post-batch diagnostic report before opening any new ML research track.

**Architecture:** Add one small Python analysis module for MT5 error-log parsing, event anomaly extraction, and post-batch summaries. Keep analysis read-only over existing artifacts; write derived JSON/CSV/Markdown reports under `ML/reports/mt5_execution_loop/diagnostics/` and `docs/reports/`. Do not rerun MT5 tester and do not change model, signal, threshold, split, or locked-test state in this plan.

**Tech Stack:** Python via `./.venv/bin/python`, `pandas`, `json`, `pytest`, existing MT5 parser `ML/baseline/parse_mt5_execution_report.py`, existing artifacts in `ML/reports/mt5_execution_loop/`.

## Global Constraints

- Work from repository root `/home/hohla/git/SoSimple`.
- Use `./.venv/bin/python` for Python commands.
- CSV files in this project use `sep=";"`; read large CSVs with `nrows`, `usecols`, or `chunksize`.
- Do not use `locked_test` for any selection, cutoff, feature, entry, exit, stop, spread, or PnL convention decision.
- Do not interpret tester PF/PnL as profitable, production-ready, live-ready, tradable, or model-quality proof.
- Maximum verdict for this plan is `DIAGNOSTIC_ONLY`.
- This plan does not create a model candidate and does not pick a new winner.
- All derived reports must distinguish facts from hypotheses.
- If an expected external artifact is missing, record it as `UNKNOWN` and continue with available repo artifacts.
- `git push` is forbidden unless the user explicitly asks.

---

## Cold-Start Context

Current state:

- Latest batch report: `docs/reports/2026-07-31-mt5-batch-selection.md`.
- Latest batch plan: `docs/superpowers/plans/2026-07-31-mt5-batch-selection.md`.
- Batch summary: `ML/reports/mt5_execution_loop/batch/batch_summary.json`.
- Batch result: 32 MT5 Strategy Tester runs on XAUUSD H1, validation 2021.01.04-2022.12.02, `BATCH_NO_WINNER`, `DIAGNOSTIC_ONLY`.
- Batch gate failure: 11 eligible candidates all failed `BS_p05 > 1.0`; Holm-Bonferroni rejected 0 hypotheses.
- Active roadmap priority: classify MT5 execution failures before starting new ML research.

Important prior reports:

- `docs/reports/2026-07-30-mt5-single-rule-diagnostic-run.md`: reports 690 `ERROR-4756` lines in tester agent log, 9 `ORDER_EXPIRED`, 32 "pending order was not found", and an unanalysed `ERROR_SoSimple_163856259.csv` observation.
- `docs/reports/2026-07-31-mt5-ontradetransaction-lifecycle.md`: OnTradeTransaction lifecycle closed, 269 positions, `CLOSED_TX=269`, `UNEXPLAINED=0`, `same_h1_count=17`; still leaves ERROR-4756 classification as next step.
- `docs/reports/2026-07-31-mt5-nero-parity.md`: current report states `PARITY_PASS` with diagnostic limitations.

Known repo artifacts:

- `ML/reports/mt5_execution_loop/mt5_trade_events_20260730_entry_quality_filter.csv`
- `ML/reports/mt5_execution_loop/mt5_trade_events_20260731_tx_lifecycle.csv`
- `ML/reports/mt5_execution_loop/mt5_execution_metrics_20260730_entry_quality_filter.json`
- `ML/reports/mt5_execution_loop/mt5_execution_metrics_20260731_tx_lifecycle.json`
- `ML/reports/mt5_execution_loop/mt5_single_rule_run_manifest_20260730_entry_quality_filter.json`
- `ML/reports/mt5_execution_loop/mt5_tx_lifecycle_run_manifest_20260731.json`
- `ML/reports/mt5_execution_loop/batch/batch_summary.json`
- `MT/tester/files/ERROR_SoSimple_113230240.csv`
- `MT/tester/files/ERROR_SoSimple_1709200448.csv`
- `MT/MQL4/Files/ERROR_SoSimple_0.csv`
- `MT/MQL4/Files/ERROR_SoSimple_517154336.csv`
- `MT/MQL4/Files/ERROR_SoSimple_662427296.csv`
- `MT/MQL4/Files/ERROR_SoSimple_899542240.csv`

Known unknowns:

- The specific `ERROR_SoSimple_163856259.csv` mentioned in the 2026-07-30 report was not found in the repo by `find . -name 'ERROR_SoSimple_*.csv'`.
- The cumulative tester agent log containing the 690 `ERROR-4756` lines may be outside the repo. If not found locally, classify available `ERROR_SoSimple_*.csv` files and record agent-log linkage as `UNKNOWN`.
- Batch INI, batch compile log, terminal log, and agent log were not saved as batch artifacts according to the batch report.
- Batch candidate directories under `ML/reports/mt5_execution_loop/batch/` contain per-run `events.csv`, `metrics.json`, and `entry_signals.json`; service directories such as `_smoke` must be excluded from 32-candidate batch attribution unless the report explicitly labels them as reference artifacts.

## Methodology Map

- `docs/methodology/00-research-management.md`: applies to scope, allowed verdict, and stop conditions. Mandatory checks: fixed level, known allowed verdict, no locked-test use, no trading interpretation.
- `docs/methodology/13b-mt5-execution-parity.md`: applies to MT5 event/deal reconciliation and execution failure classification. Mandatory checks: current `.ex5` provenance if rerun occurs, tester metadata if available, all execution discrepancies classified, tester-result not model quality.
- `docs/methodology/12-backtest-costs.md`: applies to fill failures and cost/fill risk. Mandatory checks: missed opens are not treated as zero risk; cost assumptions are not left implicit for any final verdict.
- `docs/methodology/09-validation-freeze.md`: applies to post-batch interpretation. Mandatory checks: no winner chosen from failed gates, no max-PF selection, no locked-test use, low-N overfit risk documented.
- `docs/methodology/A5-post-mortem-diagnostics.md`: applies because batch ended `BATCH_NO_WINNER` but movement-filter ranking signal exists. Mandatory checks: reproduce baseline, decompose result, identify whether weakness is model, rule, execution, cost, or sample size; output remains `DIAGNOSTIC_ONLY`.
- `docs/methodology/16-reporting-audit.md`: applies to final report. Mandatory checks: reproducibility, facts versus hypotheses, commands/paths/hashes, limitations, forbidden interpretations, next step.

No methodology section exactly covers MT5 `ERROR_SoSimple_*.csv` parsing. Use `13b-mt5-execution-parity.md` as the controlling method because these files are execution artifacts, and apply this additional order: inventory files, parse schema, classify error messages, link to event anomalies where possible, report unlinked items explicitly.

## File Structure

- Create `ML/baseline/mt5_execution_diagnostics.py`: read-only helpers and CLI for error CSV parsing, event anomaly extraction, correlation, batch event summaries, and batch diagnostics.
- Modify `tests/test_mt5_execution_diagnostics.py`: focused unit tests for the new helpers.
- Create directory `ML/reports/mt5_execution_loop/diagnostics/`: derived JSON/CSV artifacts.
- Create `docs/reports/2026-08-01-mt5-execution-hygiene-postbatch.md`: final diagnostic report.
- Modify `CONTEXT_HANDOFF.md`: update active state and next step after report is complete.
- Modify `CHANGELOG.md`: add a compact entry after report is complete.
- Modify `docs/superpowers/roadmap.md`: already updated to make this plan the active track; implementation should only touch it again if findings change the next action.

---

### Task 1: Error CSV Parser And Inventory

**Files:**
- Create: `ML/baseline/mt5_execution_diagnostics.py`
- Create: `tests/test_mt5_execution_diagnostics.py`
- Output: `ML/reports/mt5_execution_loop/diagnostics/error_inventory.json`

**Applicable Methodology:** `13b-mt5-execution-parity.md`, `16-reporting-audit.md`, CSV processing rule.

**Mandatory Checks:**
- Every discovered `ERROR_SoSimple_*.csv` has path, row count, sha256, detected columns, and source bucket.
- CSV reading uses `sep=";"` and does not load large files unnecessarily outside the parser.
- Missing `ERROR_SoSimple_163856259.csv` is recorded as `UNKNOWN`, not silently ignored.

**Completion Criterion:** `error_inventory.json` exists and tests pass.

**Interfaces:**
- Produces: `discover_error_csvs(root: Path) -> list[Path]`
- Produces: `sha256_file(path: Path) -> str`
- Produces: `read_error_csv_sample(path: Path, nrows: int = 5) -> pd.DataFrame`
- Produces: `build_error_inventory(root: Path) -> dict[str, object]`

- [ ] **Step 1: Write failing parser tests**

Add this file:

```python
# tests/test_mt5_execution_diagnostics.py
from __future__ import annotations

from pathlib import Path

import pandas as pd

from ML.baseline.mt5_execution_diagnostics import (
    build_error_inventory,
    classify_error_message,
    extract_error_code,
    read_error_csv_sample,
    _source_bucket,
)


HEADER = "INFO;SymPer;ServerTime;Ask/Bid/StpLev;Spred;Lot/Ticket;Error;Expir BUY/SEL\n"


def test_read_error_csv_sample_uses_semicolon(tmp_path: Path) -> None:
    path = tmp_path / "ERROR_SoSimple_1.csv"
    path.write_text(
        HEADER
        + "run;XAUUSD60;-2022.12.20 06:00:00;1792.48/1792.28/1;0.20;0.00/13;MLP_OpenLimitOrder: invalid stops! ERROR-130;2022.12.21 03:00/2022.12.21 03:00\n",
        encoding="utf-8",
    )

    sample = read_error_csv_sample(path, nrows=1)

    assert sample.columns.tolist()[:7] == [
        "INFO",
        "SymPer",
        "ServerTime",
        "Ask/Bid/StpLev",
        "Spred",
        "Lot/Ticket",
        "Error",
    ]
    assert sample.loc[0, "Error"] == "MLP_OpenLimitOrder: invalid stops! ERROR-130"


def test_error_inventory_records_missing_expected_file(tmp_path: Path) -> None:
    path = tmp_path / "ERROR_SoSimple_1.csv"
    path.write_text(HEADER, encoding="utf-8")

    inventory = build_error_inventory(tmp_path)

    assert inventory["status"] == "DIAGNOSTIC_ONLY"
    assert inventory["files"][0]["path"].endswith("ERROR_SoSimple_1.csv")
    assert "ERROR_SoSimple_163856259.csv" in inventory["unknowns"]["not_found_expected_files"]
    assert "ERROR_SoSimple_1.csv" in inventory["unknowns"]["missing_magic_column_files"][0]


def test_source_bucket_uses_path_parts(tmp_path: Path) -> None:
    tester_path = tmp_path / "MT" / "tester" / "files" / "ERROR_SoSimple_1.csv"
    mt4_path = tmp_path / "MT" / "MQL4" / "Files" / "ERROR_SoSimple_2.csv"

    assert _source_bucket(tester_path) == "mt_tester_files"
    assert _source_bucket(mt4_path) == "mt4_files"


def test_extract_and_classify_error_message() -> None:
    assert extract_error_code("Trade request send failed ERROR-4756") == 4756
    assert classify_error_message("MLP_OpenLimitOrder: invalid stops! ERROR-130") == "INVALID_STOPS"
    assert classify_error_message("MLP_Close Ticket=235: modification denied because order is too close to market! ERROR-145") == "MODIFICATION_TOO_CLOSE"
    assert classify_error_message("Trade request send failed ERROR-4756") == "TRADE_REQUEST_SEND_FAILED"
    assert classify_error_message("MAIL_SEND-702: function is not confirmed! ERROR-4060") == "OTHER"
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_mt5_execution_diagnostics.py -q
```

Expected: fail with `ModuleNotFoundError` or missing functions.

- [ ] **Step 3: Implement parser and inventory**

Create `ML/baseline/mt5_execution_diagnostics.py` with:

```python
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterator

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
DIAG_DIR = REPO_ROOT / "ML" / "reports" / "mt5_execution_loop" / "diagnostics"
EXPECTED_ERROR_FILES = {"ERROR_SoSimple_163856259.csv"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def discover_error_csvs(root: Path = REPO_ROOT) -> list[Path]:
    return sorted(
        path for path in root.rglob("ERROR_SoSimple_*.csv")
        if ".git" not in path.parts and "graphify-out" not in path.parts
    )


def read_error_csv_sample(path: Path, nrows: int = 5) -> pd.DataFrame:
    return pd.read_csv(path, sep=";", nrows=nrows)


def _line_count(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(1 for _ in handle)


def _source_bucket(path: Path) -> str:
    parts = tuple(path.resolve().parent.parts)
    if len(parts) >= 3 and parts[-3:] == ("MT", "tester", "files"):
        return "mt_tester_files"
    if len(parts) >= 3 and parts[-3:] == ("MT", "MQL4", "Files"):
        return "mt4_files"
    return "other"


def extract_error_code(message: str) -> int | None:
    match = re.search(r"ERROR-(\d+)", str(message))
    return int(match.group(1)) if match else None


def classify_error_message(message: str) -> str:
    text = str(message)
    code = extract_error_code(text)
    if code == 4756:
        return "TRADE_REQUEST_SEND_FAILED"
    if code == 130 or "invalid stops" in text.lower():
        return "INVALID_STOPS"
    if code == 145 or "too close to market" in text.lower():
        return "MODIFICATION_TOO_CLOSE"
    if "market closed" in text.lower():
        return "MARKET_CLOSED"
    if "position_or_pending_order_exists" in text:
        return "POSITION_OR_PENDING_EXISTS"
    return "OTHER"


def build_error_inventory(root: Path = REPO_ROOT) -> dict[str, Any]:
    files = []
    found_names = set()
    for path in discover_error_csvs(root):
        found_names.add(path.name)
        sample = read_error_csv_sample(path, nrows=5)
        files.append({
            "path": str(path.relative_to(root) if path.is_relative_to(root) else path),
            "rows_including_header": _line_count(path),
            "sha256": sha256_file(path),
            "columns": [str(col) for col in sample.columns],
            "source_bucket": _source_bucket(path),
            "has_magic_column": "Magic" in sample.columns,
        })
    return {
        "status": "DIAGNOSTIC_ONLY",
        "files": files,
        "unknowns": {
            "not_found_expected_files": sorted(EXPECTED_ERROR_FILES - found_names),
            "missing_magic_column_files": [
                item["path"] for item in files if not item["has_magic_column"]
            ],
        },
    }


def write_json(data: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="MT5 execution diagnostics")
    parser.add_argument("--phase", choices=["inventory"], required=True)
    parser.add_argument("--output-json", type=Path, default=DIAG_DIR / "error_inventory.json")
    args = parser.parse_args()
    if args.phase == "inventory":
        write_json(build_error_inventory(REPO_ROOT), args.output_json)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify pass**

Run:

```bash
./.venv/bin/python -m pytest tests/test_mt5_execution_diagnostics.py -q
```

Expected: `3 passed`.

- [ ] **Step 5: Generate inventory artifact**

Run:

```bash
./.venv/bin/python -m ML.baseline.mt5_execution_diagnostics \
  --phase inventory \
  --output-json ML/reports/mt5_execution_loop/diagnostics/error_inventory.json
```

Expected: JSON contains discovered `ERROR_SoSimple_*.csv` files and records missing `ERROR_SoSimple_163856259.csv` if still absent.

- [ ] **Step 6: Commit**

```bash
git add ML/baseline/mt5_execution_diagnostics.py tests/test_mt5_execution_diagnostics.py ML/reports/mt5_execution_loop/diagnostics/error_inventory.json
git commit -m "feat: inventory mt5 execution error logs"
```

---

### Task 2: Error Log Summary And Classification

**Files:**
- Modify: `ML/baseline/mt5_execution_diagnostics.py`
- Modify: `tests/test_mt5_execution_diagnostics.py`
- Output: `ML/reports/mt5_execution_loop/diagnostics/error_summary.json`
- Output: `ML/reports/mt5_execution_loop/diagnostics/error_rows_classified.csv`

**Applicable Methodology:** `13b-mt5-execution-parity.md`, `12-backtest-costs.md`, `16-reporting-audit.md`.

**Mandatory Checks:**
- Error rows are classified by explicit message/code rules.
- Counts are grouped by source file, `Magic`, error code, and class.
- The report separates MT5 tester files from old MT4 files; do not mix them into one verdict.
- Large error CSVs are processed with `chunksize` and minimal `usecols`; do not load a 34 MB external agent-log CSV into memory just to count classes.
- If `Magic` is missing from a file, add the file to `unknowns.missing_magic_column_files` and keep the row-level `Magic` value as `UNKNOWN`.

**Completion Criterion:** `error_summary.json` and `error_rows_classified.csv` exist and tests pass.

**Interfaces:**
- Consumes: `classify_error_message(message: str) -> str`
- Produces: `load_error_rows(paths: list[Path]) -> pd.DataFrame`
- Produces: `summarize_error_rows(rows: pd.DataFrame) -> dict[str, object]`

- [ ] **Step 1: Extend tests**

Append to `tests/test_mt5_execution_diagnostics.py`:

```python
from ML.baseline.mt5_execution_diagnostics import load_error_rows, summarize_error_rows


def test_load_and_summarize_error_rows(tmp_path: Path) -> None:
    path = tmp_path / "ERROR_SoSimple_2.csv"
    path.write_text(
        HEADER
        + "run;XAUUSD60;-2022.12.20 06:00:00;1792.48/1792.28/1;0.20;0.00/13;MLP_OpenLimitOrder: invalid stops! ERROR-130;2022.12.21 03:00/2022.12.21 03:00\n"
        + "run;XAUUSD60;-2022.12.20 07:00:00;1792.48/1792.28/1;0.20;0.00/14;Trade request send failed ERROR-4756;2022.12.21 04:00/2022.12.21 04:00\n",
        encoding="utf-8",
    )

    rows = load_error_rows([path])
    summary = summarize_error_rows(rows)

    assert rows["error_code"].tolist() == [130, 4756]
    assert rows["error_class"].tolist() == ["INVALID_STOPS", "TRADE_REQUEST_SEND_FAILED"]
    assert summary["total_rows"] == 2
    assert summary["by_error_class"]["INVALID_STOPS"] == 1
    assert summary["by_error_class"]["TRADE_REQUEST_SEND_FAILED"] == 1
    assert summary["by_magic"]["13"] == 1
    assert summary["by_magic"]["14"] == 1
    assert summary["unknowns"]["missing_magic_column_files"] == []
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_mt5_execution_diagnostics.py::test_load_and_summarize_error_rows -q
```

Expected: fail because functions are missing.

- [ ] **Step 3: Implement classification aggregation**

Add to `ML/baseline/mt5_execution_diagnostics.py`:

The helper `load_error_rows()` may concatenate chunks for focused unit tests and current small repo files, but the production CLI path must iterate through `_load_error_rows_iter()` and write `error_rows_classified.csv` chunk-by-chunk if a large external agent log is added.

```python
ERROR_USECOLS = ["ServerTime", "Error", "Lot/Ticket", "SymPer", "Expir BUY/SEL"]
ERROR_CHUNKSIZE = 50_000


def _extract_magic(value: object) -> str:
    text = str(value)
    if "/" in text:
        return text.rsplit("/", 1)[-1] or "UNKNOWN"
    return "UNKNOWN"


def _load_error_rows_iter(paths: list[Path]) -> Iterator[pd.DataFrame]:
    for path in paths:
        columns = list(pd.read_csv(path, sep=";", nrows=0).columns)
        usecols = [col for col in ERROR_USECOLS if col in columns]
        missing_magic = "Lot/Ticket" not in columns
        for frame in pd.read_csv(path, sep=";", usecols=usecols or None, chunksize=ERROR_CHUNKSIZE):
            if frame.empty:
                continue
            if "Error" not in frame.columns:
                frame["Error"] = ""
            if "Lot/Ticket" in frame.columns:
                frame["Magic"] = frame["Lot/Ticket"].map(_extract_magic)
            else:
                frame["Magic"] = "UNKNOWN"
            frame["missing_magic_column"] = bool(missing_magic)
            frame["missing_magic_column_file"] = str(path) if missing_magic else ""
            frame["source_path"] = str(path)
            frame["source_file"] = path.name
            frame["source_bucket"] = _source_bucket(path)
            frame["error_message"] = frame["Error"].astype(str)
            frame["error_code"] = frame["error_message"].map(extract_error_code)
            frame["error_class"] = frame["error_message"].map(classify_error_message)
            yield frame


def load_error_rows(paths: list[Path]) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for frame in _load_error_rows_iter(paths):
        frames.append(frame)
    if not frames:
        return pd.DataFrame(columns=["source_path", "source_file", "source_bucket", "Magic", "error_message", "error_code", "error_class", "missing_magic_column"])
    return pd.concat(frames, ignore_index=True)


def _value_counts(series: pd.Series) -> dict[str, int]:
    return {str(key): int(value) for key, value in series.value_counts(dropna=False).items()}


def summarize_error_rows(rows: pd.DataFrame) -> dict[str, Any]:
    if rows.empty:
        return {
            "status": "DIAGNOSTIC_ONLY",
            "total_rows": 0,
            "by_error_class": {},
            "by_error_code": {},
            "by_source_bucket": {},
            "by_source_file": {},
            "by_magic": {},
            "unknowns": {"missing_magic_column_files": []},
        }
    missing_magic_files = sorted(
        str(path) for path in rows.loc[rows["missing_magic_column"].astype(bool), "source_path"].dropna().unique()
    ) if "missing_magic_column" in rows.columns else []
    return {
        "status": "DIAGNOSTIC_ONLY",
        "total_rows": int(len(rows)),
        "by_error_class": _value_counts(rows["error_class"]),
        "by_error_code": _value_counts(rows["error_code"]),
        "by_source_bucket": _value_counts(rows["source_bucket"]),
        "by_source_file": _value_counts(rows["source_file"]),
        "by_magic": _value_counts(rows["Magic"] if "Magic" in rows.columns else pd.Series(["UNKNOWN"] * len(rows))),
        "unknowns": {"missing_magic_column_files": missing_magic_files},
    }


def write_error_outputs(paths: list[Path], output_csv: Path, output_json: Path) -> None:
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    frames_for_summary: list[pd.DataFrame] = []
    wrote_header = False
    for chunk in _load_error_rows_iter(paths):
        chunk.to_csv(output_csv, sep=";", index=False, mode="a", header=not wrote_header)
        wrote_header = True
        frames_for_summary.append(chunk)
    rows = pd.concat(frames_for_summary, ignore_index=True) if frames_for_summary else load_error_rows([])
    write_json(summarize_error_rows(rows), output_json)
```

Extend `main()` choices and branch:

```python
parser.add_argument("--phase", choices=["inventory", "errors"], required=True)
parser.add_argument("--output-csv", type=Path, default=DIAG_DIR / "error_rows_classified.csv")
...
if args.phase == "errors":
    write_error_outputs(discover_error_csvs(REPO_ROOT), args.output_csv, args.output_json)
```

- [ ] **Step 4: Run tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_mt5_execution_diagnostics.py -q
```

Expected: all tests pass.

- [ ] **Step 5: Generate classified outputs**

Run:

```bash
./.venv/bin/python -m ML.baseline.mt5_execution_diagnostics \
  --phase errors \
  --output-json ML/reports/mt5_execution_loop/diagnostics/error_summary.json \
  --output-csv ML/reports/mt5_execution_loop/diagnostics/error_rows_classified.csv
```

Expected: summary JSON has nonzero counts if repo error CSVs are present.

- [ ] **Step 6: Commit**

```bash
git add ML/baseline/mt5_execution_diagnostics.py tests/test_mt5_execution_diagnostics.py ML/reports/mt5_execution_loop/diagnostics/error_summary.json ML/reports/mt5_execution_loop/diagnostics/error_rows_classified.csv
git commit -m "feat: classify mt5 execution error rows"
```

---

### Task 3: Event Anomaly Summary And Linkage

**Files:**
- Modify: `ML/baseline/mt5_execution_diagnostics.py`
- Modify: `tests/test_mt5_execution_diagnostics.py`
- Output: `ML/reports/mt5_execution_loop/diagnostics/event_anomaly_summary.json`
- Output: `ML/reports/mt5_execution_loop/diagnostics/event_anomalies.csv`

**Applicable Methodology:** `13b-mt5-execution-parity.md`, `12-backtest-costs.md`.

**Mandatory Checks:**
- Count `ORDER_PLACED`, `OPEN`, `OPEN_FAILED`, `ORDER_EXPIRED`, `TX_OPEN`, `TX_CLOSE`, reconciliation classes.
- Identify `OPEN_FAILED` reason categories from event `comment` or `close_reason` when available.
- Analyze batch candidate events separately from historical reference runs: discover `ML/reports/mt5_execution_loop/batch/*/events.csv`, exclude service directories whose name starts with `_`, and preserve parent directory as `run_id`.
- If event rows cannot be linked to error rows by timestamp/ticket, record linkage as `UNKNOWN`; do not infer causality.

**Completion Criterion:** event anomaly outputs exist for both `reference_runs` and `batch_runs`, exclude `_smoke` from the 32-candidate batch scope, and state whether linkage is `LINKED`, `PARTIAL`, or `UNKNOWN`.

**Interfaces:**
- Produces: `load_event_rows(paths: list[Path]) -> pd.DataFrame`
- Produces: `discover_batch_event_paths(batch_root: Path) -> list[Path]`
- Produces: `summarize_event_anomalies(events: pd.DataFrame) -> dict[str, object]`

- [ ] **Step 1: Write tests**

Append:

```python
from ML.baseline.mt5_execution_diagnostics import discover_batch_event_paths, load_event_rows, summarize_event_anomalies


def test_summarize_event_anomalies(tmp_path: Path) -> None:
    from tests.test_parse_mt5_execution_report import _event_row, _tx_row
    from ML.baseline.mt5_signal_schema import MT5_EVENT_COLUMNS

    path = tmp_path / "events.csv"
    pd.DataFrame(
        [
            _event_row("ORDER_PLACED", "2023.01.02 10:00", comment="placed"),
            _event_row("OPEN_FAILED", "2023.01.02 10:00", comment="position_or_pending_order_exists"),
            _event_row("ORDER_EXPIRED", "2023.01.02 16:00", comment="pending order not active after max_fill_lag_bars"),
            _tx_row("TX_OPEN", "2023.01.03 10:05", 100, 1001, "EXPERT"),
            _tx_row("TX_CLOSE", "2023.01.03 10:40", 100, 1002, "SL"),
        ],
        columns=MT5_EVENT_COLUMNS,
    ).to_csv(path, sep=";", index=False)

    events = load_event_rows([path])
    summary = summarize_event_anomalies(events)

    assert summary["event_counts"]["ORDER_PLACED"] == 1
    assert summary["event_counts"]["OPEN_FAILED"] == 1
    assert summary["event_counts"]["ORDER_EXPIRED"] == 1
    assert summary["open_failed_reasons"]["position_or_pending_order_exists"] == 1


def test_discover_batch_event_paths_excludes_smoke(tmp_path: Path) -> None:
    batch_root = tmp_path / "batch"
    candidate = batch_root / "candidate_a"
    smoke = batch_root / "_smoke"
    candidate.mkdir(parents=True)
    smoke.mkdir(parents=True)
    (candidate / "events.csv").write_text("event\n", encoding="utf-8")
    (smoke / "events.csv").write_text("event\n", encoding="utf-8")

    assert discover_batch_event_paths(batch_root) == [candidate / "events.csv"]
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_mt5_execution_diagnostics.py::test_summarize_event_anomalies -q
```

Expected: fail because functions are missing.

- [ ] **Step 3: Implement event anomaly extraction**

Add:

```python
from ML.baseline.parse_mt5_execution_report import compute_mt5_metrics, parse_mt5_events


DEFAULT_EVENT_PATHS = [
    REPO_ROOT / "ML/reports/mt5_execution_loop/mt5_trade_events_20260730_entry_quality_filter.csv",
    REPO_ROOT / "ML/reports/mt5_execution_loop/mt5_trade_events_20260731_tx_lifecycle.csv",
]
BATCH_ROOT = REPO_ROOT / "ML/reports/mt5_execution_loop/batch"


def discover_batch_event_paths(batch_root: Path = BATCH_ROOT) -> list[Path]:
    return sorted(
        path for path in batch_root.glob("*/events.csv")
        if not path.parent.name.startswith("_")
    )


def load_event_rows(paths: list[Path]) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for path in paths:
        if not path.exists():
            continue
        frame = parse_mt5_events(path)
        frame["source_file"] = path.name
        frame["source_path"] = str(path)
        frame["run_id"] = path.parent.name if path.name == "events.csv" else ""
        frames.append(frame)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def _reason_from_event_row(row: pd.Series) -> str:
    text = str(row.get("comment", "") or row.get("close_reason", ""))
    if "position_or_pending_order_exists" in text:
        return "position_or_pending_order_exists"
    if "Market closed" in text or "market closed" in text:
        return "market_closed"
    if text.strip():
        return text.strip()
    return "unknown"


def summarize_event_anomalies(events: pd.DataFrame) -> dict[str, Any]:
    if events.empty:
        return {"status": "DIAGNOSTIC_ONLY", "event_counts": {}, "open_failed_reasons": {}, "reconciliation_by_run": {}}
    event_counts = _value_counts(events["event"].astype(str))
    open_failed = events.loc[events["event"].astype(str).eq("OPEN_FAILED")]
    open_failed_reasons = _value_counts(open_failed.apply(_reason_from_event_row, axis=1)) if not open_failed.empty else {}
    reconciliation_by_run: dict[str, Any] = {}
    group_key = "run_id" if "run_id" in events.columns and events["run_id"].astype(str).ne("").any() else "source_path"
    for source, group in events.groupby(group_key):
        reconciliation_by_run[str(source)] = compute_mt5_metrics(group)["reconciliation"]
    return {
        "status": "DIAGNOSTIC_ONLY",
        "event_counts": event_counts,
        "open_failed_reasons": open_failed_reasons,
        "reconciliation_by_run": reconciliation_by_run,
        "linkage_status": "UNKNOWN",
        "linkage_note": "Event rows and ERROR_SoSimple rows do not share a proven stable key in current artifacts.",
    }
```

Extend `main()`:

```python
parser.add_argument("--phase", choices=["inventory", "errors", "events"], required=True)
...
if args.phase == "events":
    reference_events = load_event_rows(DEFAULT_EVENT_PATHS)
    batch_events = load_event_rows(discover_batch_event_paths(BATCH_ROOT))
    events = pd.concat([reference_events, batch_events], ignore_index=True) if not batch_events.empty else reference_events
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    events[events["event"].astype(str).isin(["OPEN_FAILED", "ORDER_EXPIRED"])].to_csv(args.output_csv, sep=";", index=False)
    write_json({
        "status": "DIAGNOSTIC_ONLY",
        "reference_runs": summarize_event_anomalies(reference_events),
        "batch_runs": summarize_event_anomalies(batch_events),
        "batch_run_count": int(batch_events["run_id"].nunique()) if not batch_events.empty else 0,
        "excluded_service_dirs": ["_smoke"],
        "linkage_status": "UNKNOWN",
    }, args.output_json)
```

- [ ] **Step 4: Run tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_mt5_execution_diagnostics.py tests/test_parse_mt5_execution_report.py -q
```

Expected: all tests pass.

- [ ] **Step 5: Generate event outputs**

Run:

```bash
./.venv/bin/python -m ML.baseline.mt5_execution_diagnostics \
  --phase events \
  --output-json ML/reports/mt5_execution_loop/diagnostics/event_anomaly_summary.json \
  --output-csv ML/reports/mt5_execution_loop/diagnostics/event_anomalies.csv
```

Expected: JSON reports counts for 2026-07-30/2026-07-31 reference artifacts and 32 batch candidate event artifacts, excluding `_smoke` if present.

- [ ] **Step 6: Commit**

```bash
git add ML/baseline/mt5_execution_diagnostics.py tests/test_mt5_execution_diagnostics.py ML/reports/mt5_execution_loop/diagnostics/event_anomaly_summary.json ML/reports/mt5_execution_loop/diagnostics/event_anomalies.csv
git commit -m "feat: summarize mt5 execution anomalies"
```

---

### Task 4: Batch Failure Attribution

**Files:**
- Modify: `ML/baseline/mt5_execution_diagnostics.py`
- Modify: `tests/test_mt5_execution_diagnostics.py`
- Output: `ML/reports/mt5_execution_loop/diagnostics/post_batch_diagnostics.json`
- Output: `ML/reports/mt5_execution_loop/diagnostics/post_batch_top_candidates.csv`

**Applicable Methodology:** `A5-post-mortem-diagnostics.md`, `09-validation-freeze.md`, `12-backtest-costs.md`, `16-reporting-audit.md`.

**Mandatory Checks:**
- Reproduce the batch baseline numbers from `batch_summary.json`.
- Decompose top and near-top candidates by trades, BUY/SELL coverage, PF, `BS_p05`, profit concentration, gross profit/loss, yearly PF/PnL, and fill rate.
- For every selected `run_id`, read available per-run `entry_signals.json`, `metrics.json`, and `events.csv`; if any file is missing, record the missing input under `unknowns` and do not infer the missing metric.
- Fill rate is diagnostic only: compute `trades_count / active_signal_rows` only when `active_signal_rows > 0`.
- Use only predefined trade-count diagnostic buckets: `<100`, `100-149`, `150+`. Do not use bucket labels as gates and do not introduce a new winner rule.
- Do not select a new winner; output only diagnostic attribution.

**Completion Criterion:** post-batch diagnostics produce an A5-compatible decomposition of the failed batch, preserve `BATCH_NO_WINNER`, and label all causal language as hypothesis unless directly proven by linked artifacts.

**Interfaces:**
- Produces: `summarize_batch_failure(batch_summary_path: Path, batch_root: Path = BATCH_ROOT, top_n: int = 11) -> dict[str, object]`
- Produces: `load_json_if_exists(path: Path) -> dict[str, Any] | None`
- Produces: `trade_count_bucket(trades_count: int) -> str`

- [ ] **Step 1: Write tests**

Append:

```python
from ML.baseline.mt5_execution_diagnostics import summarize_batch_failure


def test_summarize_batch_failure_keeps_no_winner(tmp_path: Path) -> None:
    batch = {
        "status": "DIAGNOSTIC_ONLY",
        "verdict": "BATCH_NO_WINNER",
        "n_candidates": 2,
        "n_valid": 2,
        "n_eligible": 1,
        "n_diagnostic_only": 1,
        "winners_ranked": [
            {
                "run_id": "a",
                "bs_p05": 0.88,
                "trades_count": 102,
                "profit_concentration_pass": True,
                "all_gates_pass": False,
            }
        ],
        "table": [
            {"run_id": "a", "trades_count": 102, "profit_factor": 1.23, "trades_buy": 55, "trades_sell": 47, "win_rate": 0.41},
            {"run_id": "b", "trades_count": 40, "profit_factor": 1.50, "trades_buy": 20, "trades_sell": 20, "win_rate": 0.50},
        ],
    }
    path = tmp_path / "batch_summary.json"
    path.write_text(json.dumps(batch), encoding="utf-8")

    run_dir = tmp_path / "a"
    run_dir.mkdir()
    (run_dir / "entry_signals.json").write_text(json.dumps({"active_signal_rows": 204, "buy_rows": 110, "sell_rows": 94}), encoding="utf-8")
    (run_dir / "metrics.json").write_text(json.dumps({"gross_profit": 123.0, "gross_loss": -100.0}), encoding="utf-8")

    summary = summarize_batch_failure(path, batch_root=tmp_path)

    assert summary["verdict"] == "BATCH_NO_WINNER"
    assert summary["top_failure_modes"]["low_bootstrap_lower_bound"] == 1
    assert summary["top_candidates"][0]["run_id"] == "a"
    assert summary["top_candidates"][0]["trade_count_bucket"] == "100-149"
    assert summary["top_candidates"][0]["fill_rate"] == 0.5
    assert summary["forbidden_interpretation_guard"] == "no_new_winner_selected"
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_mt5_execution_diagnostics.py::test_summarize_batch_failure_keeps_no_winner -q
```

Expected: fail because function is missing.

- [ ] **Step 3: Implement batch attribution**

Add:

```python
def load_json_if_exists(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def trade_count_bucket(trades_count: int) -> str:
    if trades_count < 100:
        return "<100"
    if trades_count < 150:
        return "100-149"
    return "150+"


def summarize_batch_failure(batch_summary_path: Path, batch_root: Path = BATCH_ROOT, top_n: int = 11) -> dict[str, Any]:
    data = json.loads(batch_summary_path.read_text(encoding="utf-8"))
    ranked = data.get("winners_ranked", [])[:top_n]
    table_by_id = {row.get("run_id"): row for row in data.get("table", [])}
    top_candidates = []
    low_bootstrap = 0
    trade_count_buckets: dict[str, int] = {}
    concentration_fail = 0
    missing_inputs: dict[str, list[str]] = {}
    for item in ranked:
        run_id = str(item.get("run_id"))
        row = table_by_id.get(run_id, {})
        run_dir = batch_root / run_id
        entry_signals = load_json_if_exists(run_dir / "entry_signals.json")
        metrics = load_json_if_exists(run_dir / "metrics.json")
        events_path = run_dir / "events.csv"
        missing_inputs[run_id] = [
            name for name, value in {
                "entry_signals.json": entry_signals,
                "metrics.json": metrics,
                "events.csv": events_path.exists(),
            }.items() if not value
        ]
        if float(item.get("bs_p05", 0.0)) <= 1.0:
            low_bootstrap += 1
        trades_count = int(item.get("trades_count", 0))
        bucket = trade_count_bucket(trades_count)
        trade_count_buckets[bucket] = trade_count_buckets.get(bucket, 0) + 1
        if not bool(item.get("profit_concentration_pass", True)):
            concentration_fail += 1
        active_signal_rows = int((entry_signals or {}).get("active_signal_rows", 0) or 0)
        fill_rate = trades_count / active_signal_rows if active_signal_rows > 0 else None
        event_counts = summarize_event_anomalies(load_event_rows([events_path]))["event_counts"] if events_path.exists() else {}
        top_candidates.append({
            "run_id": run_id,
            "profit_factor": row.get("profit_factor"),
            "trades_count": trades_count,
            "trade_count_bucket": bucket,
            "trades_buy": row.get("trades_buy"),
            "trades_sell": row.get("trades_sell"),
            "pf_buy": row.get("pf_buy"),
            "pf_sell": row.get("pf_sell"),
            "pf_by_year": row.get("pf_by_year"),
            "gross_profit_by_year": row.get("gross_profit_by_year"),
            "win_rate": row.get("win_rate"),
            "bs_p05": item.get("bs_p05"),
            "profit_concentration_pass": item.get("profit_concentration_pass"),
            "gross_profit": (metrics or {}).get("gross_profit"),
            "gross_loss": (metrics or {}).get("gross_loss"),
            "active_signal_rows": active_signal_rows if entry_signals is not None else None,
            "buy_signal_rows": (entry_signals or {}).get("buy_rows"),
            "sell_signal_rows": (entry_signals or {}).get("sell_rows"),
            "fill_rate": fill_rate,
            "event_counts": event_counts,
            "all_gates_pass": item.get("all_gates_pass"),
        })
    return {
        "status": "DIAGNOSTIC_ONLY",
        "verdict": data.get("verdict"),
        "n_candidates": data.get("n_candidates"),
        "n_valid": data.get("n_valid"),
        "n_eligible": data.get("n_eligible"),
        "n_diagnostic_only": data.get("n_diagnostic_only"),
        "top_failure_modes": {
            "low_bootstrap_lower_bound": low_bootstrap,
            "trade_count_buckets": trade_count_buckets,
            "profit_concentration_fail": concentration_fail,
        },
        "top_candidates": top_candidates,
        "unknowns": {"missing_per_run_inputs": missing_inputs},
        "forbidden_interpretation_guard": "no_new_winner_selected",
    }
```

Extend `main()`:

```python
parser.add_argument("--phase", choices=["inventory", "errors", "events", "batch"], required=True)
...
if args.phase == "batch":
    summary = summarize_batch_failure(REPO_ROOT / "ML/reports/mt5_execution_loop/batch/batch_summary.json")
    top = pd.DataFrame(summary["top_candidates"])
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    top.to_csv(args.output_csv, sep=";", index=False)
    write_json(summary, args.output_json)
```

- [ ] **Step 4: Run tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_mt5_execution_diagnostics.py -q
```

Expected: all tests pass.

- [ ] **Step 5: Generate batch diagnostics**

Run:

```bash
./.venv/bin/python -m ML.baseline.mt5_execution_diagnostics \
  --phase batch \
  --output-json ML/reports/mt5_execution_loop/diagnostics/post_batch_diagnostics.json \
  --output-csv ML/reports/mt5_execution_loop/diagnostics/post_batch_top_candidates.csv
```

Expected: JSON keeps `verdict=BATCH_NO_WINNER` and lists top candidate failure modes.

- [ ] **Step 6: Commit**

```bash
git add ML/baseline/mt5_execution_diagnostics.py tests/test_mt5_execution_diagnostics.py ML/reports/mt5_execution_loop/diagnostics/post_batch_diagnostics.json ML/reports/mt5_execution_loop/diagnostics/post_batch_top_candidates.csv
git commit -m "feat: diagnose mt5 batch failure modes"
```

---

### Task 5: Final Report, Handoff, And Roadmap Decision

**Files:**
- Create: `docs/reports/2026-08-01-mt5-execution-hygiene-postbatch.md`
- Modify: `CONTEXT_HANDOFF.md`
- Modify: `CHANGELOG.md`
- Modify: `docs/superpowers/roadmap.md` only if the final decision changes ACTIVE or next action

**Applicable Methodology:** `16-reporting-audit.md`, `00-research-management.md`, `A5-post-mortem-diagnostics.md`.

**Mandatory Checks:**
- Report includes Context, Stage Level, Research-first disclosure, Methodology, What Was Done, Multiple Testing Context, Changed Files, Verification, Results, Conclusions, Limitations/Open Questions, Split Disclosure, Forbidden Interpretations, Next Step, Related Materials.
- Report includes commands and paths for every generated JSON/CSV.
- Report includes sha256 hashes for generated JSON/CSV artifacts and the final report inputs that support key numbers.
- Report includes a structured artifact cross-check: every key number in the report must name its JSON/CSV source.
- Report confirms `locked_test` / holdout was not used for any selection or threshold decision.
- Report explicitly says whether `ERROR-4756` linkage is complete, partial, or unknown.
- Report explicitly says no new winner was selected.
- Handoff names the next single action.

**Completion Criterion:** another cold-start agent can continue from report + handoff without this conversation.

- [ ] **Step 1: Run verification**

Run:

```bash
./.venv/bin/python -m pytest tests/test_mt5_execution_diagnostics.py tests/test_parse_mt5_execution_report.py tests/test_mt5_signal_executor_schema.py -q
```

Expected: all tests pass.

- [ ] **Step 2: Write report**

Create `docs/reports/2026-08-01-mt5-execution-hygiene-postbatch.md` with this structure:

```markdown
# MT5 Execution Hygiene And Post-Batch Diagnostics

**Date:** 2026-08-01
**Status:** DIAGNOSTIC_ONLY
**Verdict:** EXECUTION_HYGIENE_CLASSIFIED | EXECUTION_HYGIENE_PARTIAL | EXECUTION_HYGIENE_BLOCKED
**Plan:** `docs/superpowers/plans/2026-08-01-mt5-execution-hygiene-postbatch.md`

## Stage Level

Search/post-mortem diagnostic stage. This report does not create a candidate and cannot raise verdict above `DIAGNOSTIC_ONLY`.

## Research-first disclosure

- **lifecycle_status:** DIAGNOSTIC_ONLY
- **origin_bias:** post-mortem after `BATCH_NO_WINNER`; no new selection
- **research_priority:** infrastructure first, then post-batch diagnostics
- **current_search_budget:** 0 new model/search configurations
- **cumulative_search_budget:** inherits 64 benchmark -> 32 shortlist -> 32 MT5 tester -> 11 eligible from 2026-07-31 batch
- **next_probe_freeze:** not selected in this report
- **allowed_max_verdict:** DIAGNOSTIC_ONLY
- **forbidden_interpretations:** profitable, ready, live-ready, tradable, new winner, model-quality proof

## Context

Summarize the 2026-07-30 single-rule diagnostic, 2026-07-31 lifecycle closure, 2026-07-31 Nero parity, and 2026-07-31 batch result.

## Methodology

List applicable methodology sections: 00, 13b, 12, 09, A5, 16. State that no exact section exists for `ERROR_SoSimple_*.csv`, so `13b` controls execution artifact classification.

## Multiple Testing Context

State that no new model/search configurations were selected. Reference the inherited 2026-07-31 batch budget and keep all post-mortem slices `DIAGNOSTIC_ONLY`.

## What Was Done

List generated artifacts:

- `ML/reports/mt5_execution_loop/diagnostics/error_inventory.json`
- `ML/reports/mt5_execution_loop/diagnostics/error_summary.json`
- `ML/reports/mt5_execution_loop/diagnostics/error_rows_classified.csv`
- `ML/reports/mt5_execution_loop/diagnostics/event_anomaly_summary.json`
- `ML/reports/mt5_execution_loop/diagnostics/event_anomalies.csv`
- `ML/reports/mt5_execution_loop/diagnostics/post_batch_diagnostics.json`
- `ML/reports/mt5_execution_loop/diagnostics/post_batch_top_candidates.csv`

## Changed Files

List every created/modified source, test, report, handoff, changelog, and generated artifact path.

## Artifact Hashes

List sha256 hashes for each generated JSON/CSV artifact and for `ML/reports/mt5_execution_loop/batch/batch_summary.json`.

## Structured Artifact Cross-Check

For every reported count or metric, cite the source artifact path and JSON key or CSV column. Block completion if report numbers disagree with structured artifacts.

## Verification

Include exact pytest command and result.

## Results

Report error class counts, event anomaly counts, linkage status, and batch failure attribution.

## Conclusions

State one of:

- `EXECUTION_HYGIENE_CLASSIFIED`: all known execution anomalies classified and no blocker remains for post-batch diagnostics.
- `EXECUTION_HYGIENE_PARTIAL`: available repo artifacts classified, but missing external agent log or missing expected error CSV prevents full linkage.
- `EXECUTION_HYGIENE_BLOCKED`: artifact mismatch or parser/schema issue prevents reliable classification.

If `ERROR_SoSimple_163856259.csv` or the cumulative tester agent log is still missing, maximum execution-hygiene verdict is `EXECUTION_HYGIENE_PARTIAL`, unless the report proves from structured batch artifacts that the missing artifact cannot affect batch metrics.

## Limitations / Open Questions

List missing agent logs, missing `ERROR_SoSimple_163856259.csv`, unsaved batch logs, and any unlinked rows.

## Split Disclosure

State validation/batch period, split role, sample-size gates inherited from the 2026-07-31 batch, and explicitly confirm that `locked_test` / holdout was not used for any selection, threshold, cost, entry, exit, or interpretation decision.

## Forbidden Interpretations

State that no trading or model-quality conclusion follows from this diagnostic.

## Next Step

Pick exactly one next action:

1. If classified and A5 batch attribution is complete: choose the next frozen probe plan.
2. If partial: retrieve missing agent log / expected CSV or accept partial status explicitly before choosing the next frozen probe plan.
3. If blocked: fix parser/schema/artifact mismatch first.

## Related Materials

Link prior reports, plan, roadmap, and generated artifacts.
```

Replace the verdict placeholder with the actual verdict from artifacts.

- [ ] **Step 3: Update handoff**

Modify `CONTEXT_HANDOFF.md` so `Current Active State`, `Decision`, `Current Diagnostic Facts`, `Do Not Do`, `Next Step`, and `Verification` match the new report. Keep it short.

- [ ] **Step 4: Update changelog**

Add a top entry to `CHANGELOG.md`:

```markdown
## [2026-08-01] — MT5 execution hygiene and post-batch diagnostics (DIAGNOSTIC_ONLY)
- **report**: `docs/reports/2026-08-01-mt5-execution-hygiene-postbatch.md`
- **topics**: `mt5`, `execution_hygiene`, `error_4756`, `post_batch_diagnostics`
- **summary**: Classified available MT5 execution error artifacts and summarized post-batch failure modes without selecting a new winner.
- **artifacts**: `ML/reports/mt5_execution_loop/diagnostics/error_summary.json`, `ML/reports/mt5_execution_loop/diagnostics/post_batch_diagnostics.json`
- **decision**: Use the report verdict: `EXECUTION_HYGIENE_CLASSIFIED`, `EXECUTION_HYGIENE_PARTIAL`, or `EXECUTION_HYGIENE_BLOCKED`.
- **notes**: Result remains `DIAGNOSTIC_ONLY`; no trading or model-quality conclusion.
```

- [ ] **Step 5: Update roadmap if needed**

If report verdict is `EXECUTION_HYGIENE_CLASSIFIED`, update `docs/superpowers/roadmap.md` ACTIVE next action to `post-batch diagnostic attribution` or the next chosen frozen probe. If verdict is `PARTIAL` or `BLOCKED`, keep ACTIVE on execution hygiene and name the missing artifact/fix.

- [ ] **Step 6: Final verification**

Run:

```bash
rg -n "EXECUTION_HYGIENE_CLASSIFIED|EXECUTION_HYGIENE_PARTIAL|EXECUTION_HYGIENE_BLOCKED|DIAGNOSTIC_ONLY|forbidden_interpretations" \
  docs/reports/2026-08-01-mt5-execution-hygiene-postbatch.md CONTEXT_HANDOFF.md CHANGELOG.md docs/superpowers/roadmap.md
./.venv/bin/python -m pytest tests/test_mt5_execution_diagnostics.py tests/test_parse_mt5_execution_report.py tests/test_mt5_signal_executor_schema.py -q
```

Expected: `rg` finds the report verdict and `DIAGNOSTIC_ONLY`; pytest passes.

- [ ] **Step 7: Commit**

```bash
git add docs/reports/2026-08-01-mt5-execution-hygiene-postbatch.md CONTEXT_HANDOFF.md CHANGELOG.md docs/superpowers/roadmap.md
git commit -m "docs: close mt5 execution hygiene diagnostics"
```

---

## Plan Self-Review

- Spec coverage: roadmap correction, ERROR-4756/error CSV classification, event/deal anomaly summary, post-batch attribution, final report, handoff, changelog are covered.
- Placeholder scan: no forbidden placeholder markers remain. The report template contains explicit verdict choices, not placeholders; implementer must pick one based on artifacts.
- Type consistency: all produced function names are defined before use in later tasks.
- Methodology coverage: each task names applicable methodology, mandatory checks, and completion criteria. The missing exact methodology for `ERROR_SoSimple_*.csv` is explicitly handled through `13b-mt5-execution-parity.md`.
- Unknowns: missing `ERROR_SoSimple_163856259.csv` and missing external agent log are explicit and do not block partial diagnostics.
