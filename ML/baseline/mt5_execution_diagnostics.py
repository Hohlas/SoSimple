from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

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


def _relative_path(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


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
    parser.add_argument("--phase", choices=["inventory"], required=True)
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    parser.add_argument("--output-json", type=Path, default=DIAG_DIR / "error_inventory.json")
    args = parser.parse_args()

    if args.phase == "inventory":
        write_json(build_error_inventory(args.root), args.output_json)


if __name__ == "__main__":
    main()
