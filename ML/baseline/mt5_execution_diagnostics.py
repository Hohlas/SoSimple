#
# =============================================================================
# File: mt5_execution_diagnostics.py
# Purpose: Read-only diagnostics for MT5 execution error logs and summaries.
# Updated: 2026-08-01
# Dependencies:
#   External:
#     - pandas>=2.0
# Usage:
#   python -m ML.baseline.mt5_execution_diagnostics --phase inventory|errors
# =============================================================================
#
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Iterator

import pandas as pd

from ML.baseline.mt5_signal_schema import MT5_EVENT_COLUMNS
from ML.baseline.parse_mt5_execution_report import compute_mt5_metrics, parse_mt5_events


REPO_ROOT = Path(__file__).resolve().parents[2]
DIAG_DIR = REPO_ROOT / "ML" / "reports" / "mt5_execution_loop" / "diagnostics"
DEFAULT_EVENT_PATHS = [
    REPO_ROOT / "ML" / "reports" / "mt5_execution_loop" / "mt5_trade_events_20260730_entry_quality_filter.csv",
    REPO_ROOT / "ML" / "reports" / "mt5_execution_loop" / "mt5_trade_events_20260731_tx_lifecycle.csv",
]
BATCH_ROOT = REPO_ROOT / "ML" / "reports" / "mt5_execution_loop" / "batch"
EXPECTED_ERROR_FILES = {"ERROR_SoSimple_163856259.csv"}
ERROR_USECOLS = ["Error", "Lot/Ticket"]
ERROR_CHUNKSIZE = 50_000
ERROR_OUTPUT_COLUMNS = [
    "source_path",
    "source_file",
    "source_bucket",
    "Magic",
    "error_message",
    "error_code",
    "error_class",
    "missing_magic_column",
    "missing_magic_column_file",
]
EVENT_METADATA_COLUMNS = ["source_file", "source_path", "run_id"]
EVENT_ANOMALY_EVENTS = {"OPEN_FAILED", "ORDER_EXPIRED"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def discover_error_csvs(root: Path = REPO_ROOT) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("ERROR_SoSimple_*.csv")
        if ".git" not in path.parts and "graphify-out" not in path.parts
    )


def read_error_csv_sample(path: Path, nrows: int = 5) -> pd.DataFrame:
    return pd.read_csv(path, sep=";", nrows=nrows)


def _line_count(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(1 for _ in handle)


def _source_bucket(path: Path) -> str:
    parts = path.parent.parts
    if len(parts) >= 3 and parts[-3:] == ("MT", "tester", "files"):
        return "mt_tester_files"
    if len(parts) >= 3 and parts[-3:] == ("MT", "MQL4", "Files"):
        return "mt4_files"
    return "other"


def discover_batch_event_paths(batch_root: Path = BATCH_ROOT) -> list[Path]:
    return sorted(
        path
        for path in batch_root.glob("*/events.csv")
        if not path.parent.name.startswith("_")
    )


def _batch_candidate_dirs(batch_root: Path = BATCH_ROOT) -> list[Path]:
    return sorted(
        path
        for path in batch_root.iterdir()
        if path.is_dir() and not path.name.startswith("_")
    )


def _empty_event_frame() -> pd.DataFrame:
    columns = [*MT5_EVENT_COLUMNS, *EVENT_METADATA_COLUMNS]
    return pd.DataFrame({column: pd.Series(dtype="object") for column in columns})


def load_event_rows(paths: list[Path]) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for path in paths:
        if not path.exists():
            continue
        frame = parse_mt5_events(path).copy()
        frame["source_file"] = path.name
        frame["source_path"] = str(path)
        frame["run_id"] = path.parent.name if path.name == "events.csv" else path.stem
        frames.append(frame[[*MT5_EVENT_COLUMNS, *EVENT_METADATA_COLUMNS]])

    if not frames:
        return _empty_event_frame()
    return pd.concat(frames, ignore_index=True)


def extract_error_code(message: str) -> int | None:
    match = re.search(r"ERROR-(\d+)", str(message))
    return int(match.group(1)) if match else None


def classify_error_message(message: str) -> str:
    text = str(message)
    lowered = text.lower()
    code = extract_error_code(text)

    if code == 4756 or "trade request send failed" in lowered:
        return "TRADE_REQUEST_SEND_FAILED"
    if code == 130 or "invalid stops" in lowered:
        return "INVALID_STOPS"
    if code == 145 or "too close to market" in lowered or "modification denied" in lowered:
        return "MODIFICATION_TOO_CLOSE"
    if "market closed" in lowered:
        return "MARKET_CLOSED"
    if "position_or_pending_order_exists" in lowered:
        return "POSITION_OR_PENDING_EXISTS"
    return "OTHER"


def _extract_magic(value: object) -> str:
    text = str(value)
    if "/" in text:
        magic = text.rsplit("/", 1)[-1].strip()
        return magic or "UNKNOWN"
    return "UNKNOWN"


def _relative_path(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _empty_error_rows_frame() -> pd.DataFrame:
    return pd.DataFrame({column: pd.Series(dtype="object") for column in ERROR_OUTPUT_COLUMNS})


def _load_error_rows_iter(paths: list[Path]) -> Iterator[pd.DataFrame]:
    for path in paths:
        columns = [str(column) for column in pd.read_csv(path, sep=";", nrows=0).columns]
        usecols = [column for column in ERROR_USECOLS if column in columns]
        missing_magic_column = "Lot/Ticket" not in columns
        source_path = _relative_path(REPO_ROOT, path)
        source_bucket = _source_bucket(path)

        if not usecols:
            continue

        for frame in pd.read_csv(
            path,
            sep=";",
            usecols=usecols,
            chunksize=ERROR_CHUNKSIZE,
            dtype=str,
            keep_default_na=False,
            na_filter=False,
        ):
            if frame.empty:
                continue
            if "Error" not in frame.columns:
                frame["Error"] = ""
            if "Lot/Ticket" in frame.columns:
                frame["Magic"] = frame["Lot/Ticket"].map(_extract_magic)
            else:
                frame["Magic"] = "UNKNOWN"
            frame["source_path"] = source_path
            frame["source_file"] = path.name
            frame["source_bucket"] = source_bucket
            frame["error_message"] = frame["Error"].astype(str)
            frame["error_code"] = frame["error_message"].map(extract_error_code)
            frame["error_class"] = frame["error_message"].map(classify_error_message)
            frame["missing_magic_column"] = bool(missing_magic_column)
            frame["missing_magic_column_file"] = source_path if missing_magic_column else ""
            yield frame[ERROR_OUTPUT_COLUMNS]


def load_error_rows(paths: list[Path]) -> pd.DataFrame:
    """Loads and classifies error rows from one or more CSV files."""
    frames = list(_load_error_rows_iter(paths))
    if not frames:
        return _empty_error_rows_frame()
    return pd.concat(frames, ignore_index=True)


def _value_counts(series: pd.Series) -> dict[str, int]:
    counts = series.fillna("UNKNOWN").astype(str).value_counts(dropna=False)
    return {str(key): int(value) for key, value in counts.items()}


def _event_reason_category(row: pd.Series) -> str:
    text = str(row.get("comment", "") or row.get("close_reason", "") or "").strip()
    lowered = text.lower()
    if not lowered:
        return "unknown"
    if "position_or_pending_order_exists" in lowered:
        return "position_or_pending_order_exists"
    if "pending order was not found after order_placed" in lowered or "pending order was not found" in lowered:
        return "pending_order_not_found_after_order_placed"
    if "pending order not active after max_fill_lag_bars" in lowered:
        return "pending_order_not_active_after_max_fill_lag_bars"
    if "market closed" in lowered:
        return "market_closed"
    if "requote" in lowered:
        return "requote"
    if "invalid stops" in lowered:
        return "invalid_stops"
    if "trade request send failed" in lowered:
        return "trade_request_send_failed"
    return re.sub(r"[^a-z0-9]+", "_", lowered).strip("_") or "unknown"


def summarize_event_anomalies(events: pd.DataFrame) -> dict[str, object]:
    if events.empty or "event" not in events.columns:
        return {
            "status": "DIAGNOSTIC_ONLY",
            "total_rows": 0,
            "event_counts": {},
            "open_failed_reasons": {},
            "order_expired_reasons": {},
            "reconciliation_by_run": {},
            "run_ids": [],
            "linkage_status": "UNKNOWN",
        }

    event_names = events["event"].astype(str)
    event_counts = _value_counts(event_names)

    open_failed = events.loc[event_names.eq("OPEN_FAILED")]
    order_expired = events.loc[event_names.eq("ORDER_EXPIRED")]

    open_failed_reasons = (
        _value_counts(open_failed.apply(_event_reason_category, axis=1)) if not open_failed.empty else {}
    )
    order_expired_reasons = (
        _value_counts(order_expired.apply(_event_reason_category, axis=1)) if not order_expired.empty else {}
    )

    reconciliation_by_run: dict[str, object] = {}
    run_ids: list[str] = []
    if "run_id" in events.columns:
        for run_id, group in events.groupby(events["run_id"].fillna("").astype(str), dropna=False):
            run_key = str(run_id).strip()
            if not run_key:
                if "source_path" in group.columns and not group.empty:
                    run_key = str(group.iloc[0].get("source_path", "")).strip() or "UNKNOWN"
                else:
                    run_key = "UNKNOWN"
            run_ids.append(run_key)
            reconciliation_by_run[run_key] = compute_mt5_metrics(group)["reconciliation"]
    else:
        reconciliation_by_run["UNKNOWN"] = compute_mt5_metrics(events)["reconciliation"]
        run_ids.append("UNKNOWN")

    return {
        "status": "DIAGNOSTIC_ONLY",
        "total_rows": int(len(events)),
        "event_counts": event_counts,
        "open_failed_reasons": open_failed_reasons,
        "order_expired_reasons": order_expired_reasons,
        "reconciliation_by_run": reconciliation_by_run,
        "run_ids": sorted(set(run_ids)),
        "linkage_status": "UNKNOWN",
    }


def summarize_error_rows(rows: pd.DataFrame) -> dict[str, object]:
    """Builds a compact diagnostic summary for classified error rows."""
    if rows.empty:
        return {
            "status": "DIAGNOSTIC_ONLY",
            "total_rows": 0,
            "by_source_bucket": {},
            "by_source_file": {},
            "by_magic": {},
            "by_error_code": {},
            "by_error_class": {},
            "unknowns": {"missing_magic_column_files": []},
        }

    missing_magic_column_files = sorted(
        {
            str(value)
            for value in rows.loc[rows["missing_magic_column"].astype(bool), "missing_magic_column_file"].tolist()
            if str(value)
        }
    )

    return {
        "status": "DIAGNOSTIC_ONLY",
        "total_rows": int(len(rows)),
        "by_source_bucket": _value_counts(rows["source_bucket"]),
        "by_source_file": _value_counts(rows["source_file"]),
        "by_magic": _value_counts(rows["Magic"]),
        "by_error_code": _value_counts(rows["error_code"]),
        "by_error_class": _value_counts(rows["error_class"]),
        "unknowns": {"missing_magic_column_files": missing_magic_column_files},
    }


def _counter_to_dict(counter: Counter[str]) -> dict[str, int]:
    return {str(key): int(value) for key, value in counter.most_common()}


def _empty_error_summary() -> dict[str, object]:
    return {
        "status": "DIAGNOSTIC_ONLY",
        "total_rows": 0,
        "by_source_bucket": {},
        "by_source_file": {},
        "by_magic": {},
        "by_error_code": {},
        "by_error_class": {},
        "unknowns": {"missing_magic_column_files": []},
    }


class _ErrorSummaryAccumulator:
    def __init__(self) -> None:
        self.total_rows = 0
        self.by_source_bucket: Counter[str] = Counter()
        self.by_source_file: Counter[str] = Counter()
        self.by_magic: Counter[str] = Counter()
        self.by_error_code: Counter[str] = Counter()
        self.by_error_class: Counter[str] = Counter()
        self.missing_magic_column_files: set[str] = set()

    def add(self, frame: pd.DataFrame) -> None:
        self.total_rows += int(len(frame))
        self.by_source_bucket.update(frame["source_bucket"].fillna("UNKNOWN").astype(str))
        self.by_source_file.update(frame["source_file"].fillna("UNKNOWN").astype(str))
        self.by_magic.update(frame["Magic"].fillna("UNKNOWN").astype(str))
        self.by_error_code.update(frame["error_code"].fillna("UNKNOWN").astype(str))
        self.by_error_class.update(frame["error_class"].fillna("UNKNOWN").astype(str))
        missing = frame.loc[
            frame["missing_magic_column"].astype(bool),
            "missing_magic_column_file",
        ]
        self.missing_magic_column_files.update(str(value) for value in missing.tolist() if str(value))

    def summary(self) -> dict[str, object]:
        if self.total_rows == 0:
            return _empty_error_summary()
        return {
            "status": "DIAGNOSTIC_ONLY",
            "total_rows": self.total_rows,
            "by_source_bucket": _counter_to_dict(self.by_source_bucket),
            "by_source_file": _counter_to_dict(self.by_source_file),
            "by_magic": _counter_to_dict(self.by_magic),
            "by_error_code": _counter_to_dict(self.by_error_code),
            "by_error_class": _counter_to_dict(self.by_error_class),
            "unknowns": {"missing_magic_column_files": sorted(self.missing_magic_column_files)},
        }


def write_error_outputs(paths: list[Path], output_csv: Path, output_json: Path) -> None:
    """Writes classified error rows and the summary JSON for a set of CSV paths."""
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    if output_csv.exists():
        output_csv.unlink()

    wrote_header = False
    accumulator = _ErrorSummaryAccumulator()

    for frame in _load_error_rows_iter(paths):
        frame.to_csv(output_csv, sep=";", index=False, mode="a", header=not wrote_header)
        wrote_header = True
        accumulator.add(frame)

    if not wrote_header:
        _empty_error_rows_frame().to_csv(output_csv, sep=";", index=False)

    write_json(accumulator.summary(), output_json)


def build_error_inventory(root: Path = REPO_ROOT) -> dict[str, object]:
    files: list[dict[str, object]] = []
    found_names: set[str] = set()

    for path in discover_error_csvs(root):
        found_names.add(path.name)
        sample = read_error_csv_sample(path, nrows=5)
        detected_columns = [str(column) for column in sample.columns]
        files.append(
            {
                "path": _relative_path(root, path),
                "row_count": max(_line_count(path) - 1, 0),
                "sha256": sha256_file(path),
                "detected_columns": detected_columns,
                "source_bucket": _source_bucket(path),
                "magic_present": "Magic" in detected_columns,
            }
        )

    files.sort(key=lambda item: str(item["path"]))
    missing_expected = sorted(EXPECTED_ERROR_FILES - found_names)
    missing_magic_column_files = [
        str(item["path"]) for item in files if not bool(item["magic_present"])
    ]

    return {
        "status": "DIAGNOSTIC_ONLY",
        "files": files,
        "unknowns": {
            "not_found_expected_files": missing_expected,
            "missing_magic_column_files": missing_magic_column_files,
            "expected_file_statuses": {
                name: ("UNKNOWN" if name in missing_expected else "FOUND")
                for name in sorted(EXPECTED_ERROR_FILES)
            },
        },
    }


def write_json(data: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_event_anomaly_outputs(
    reference_paths: list[Path] | None = None,
    batch_root: Path = BATCH_ROOT,
) -> tuple[dict[str, object], pd.DataFrame]:
    reference_paths = reference_paths if reference_paths is not None else [
        path for path in DEFAULT_EVENT_PATHS if path.exists()
    ]
    reference_events = load_event_rows(reference_paths)
    batch_event_paths = discover_batch_event_paths(batch_root)
    batch_events = load_event_rows(batch_event_paths)
    combined_frames = [frame for frame in [reference_events, batch_events] if not frame.empty]
    combined_events = pd.concat(combined_frames, ignore_index=True) if combined_frames else _empty_event_frame()
    anomaly_rows = combined_events.loc[
        combined_events["event"].astype(str).isin(EVENT_ANOMALY_EVENTS)
    ].copy()

    if not anomaly_rows.empty:
        anomaly_rows = anomaly_rows.sort_values(by=["source_file", "time", "event"], kind="mergesort")

    excluded_service_dirs = sorted(
        path.name for path in batch_root.iterdir() if path.is_dir() and path.name.startswith("_")
    ) if batch_root.exists() else []
    batch_run_count = len(_batch_candidate_dirs(batch_root))

    return (
        {
            "status": "DIAGNOSTIC_ONLY",
            "reference_runs": summarize_event_anomalies(reference_events),
            "batch_runs": summarize_event_anomalies(batch_events),
            "reference_event_paths": [str(path) for path in reference_paths if path.exists()],
            "batch_event_paths": [str(path) for path in batch_event_paths],
            "batch_run_count": batch_run_count,
            "batch_candidate_count": batch_run_count,
            "batch_event_path_count": len(batch_event_paths),
            "excluded_service_dirs": excluded_service_dirs,
            "linkage_status": "UNKNOWN",
        },
        anomaly_rows,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="MT5 execution diagnostics")
    parser.add_argument("--phase", choices=["inventory", "errors", "events"], required=True)
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    parser.add_argument("--output-json", type=Path, default=DIAG_DIR / "error_inventory.json")
    parser.add_argument("--output-csv", type=Path, default=DIAG_DIR / "error_rows_classified.csv")
    args = parser.parse_args()

    if args.phase == "inventory":
        write_json(build_error_inventory(args.root), args.output_json)
    elif args.phase == "errors":
        write_error_outputs(discover_error_csvs(args.root), args.output_csv, args.output_json)
    elif args.phase == "events":
        summary, anomaly_rows = build_event_anomaly_outputs()
        write_json(summary, args.output_json)
        args.output_csv.parent.mkdir(parents=True, exist_ok=True)
        anomaly_rows.to_csv(args.output_csv, sep=";", index=False)


if __name__ == "__main__":
    main()
