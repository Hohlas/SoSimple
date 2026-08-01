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
from pathlib import Path
from typing import Any, Iterator

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
DIAG_DIR = REPO_ROOT / "ML" / "reports" / "mt5_execution_loop" / "diagnostics"
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


def write_error_outputs(paths: list[Path], output_csv: Path, output_json: Path) -> None:
    """Writes classified error rows and the summary JSON for a set of CSV paths."""
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    if output_csv.exists():
        output_csv.unlink()

    frames: list[pd.DataFrame] = []
    wrote_header = False

    for frame in _load_error_rows_iter(paths):
        frame.to_csv(output_csv, sep=";", index=False, mode="a", header=not wrote_header)
        wrote_header = True
        frames.append(frame)

    if frames:
        rows = pd.concat(frames, ignore_index=True)
    else:
        rows = _empty_error_rows_frame()
        rows.to_csv(output_csv, sep=";", index=False)

    write_json(summarize_error_rows(rows), output_json)


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


def main() -> None:
    parser = argparse.ArgumentParser(description="MT5 execution diagnostics")
    parser.add_argument("--phase", choices=["inventory", "errors"], required=True)
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    parser.add_argument("--output-json", type=Path, default=DIAG_DIR / "error_inventory.json")
    parser.add_argument("--output-csv", type=Path, default=DIAG_DIR / "error_rows_classified.csv")
    args = parser.parse_args()

    if args.phase == "inventory":
        write_json(build_error_inventory(args.root), args.output_json)
    elif args.phase == "errors":
        write_error_outputs(discover_error_csvs(args.root), args.output_csv, args.output_json)


if __name__ == "__main__":
    main()
