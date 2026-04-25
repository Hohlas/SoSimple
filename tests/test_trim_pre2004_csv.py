from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["time", "value"], delimiter=";")
        writer.writeheader()
        writer.writerows(rows)


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter=";"))


def test_trim_pre2004_dry_run_reports_without_changing_file(tmp_path: Path) -> None:
    csv_path = tmp_path / "sample.csv"
    _write_csv(
        csv_path,
        [
            {"time": "2003.12.31 23:00", "value": "old"},
            {"time": "2004.01.01 00:00", "value": "keep"},
            {"time": "2005.01.01 00:00", "value": "new"},
        ],
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "processing.trim_pre2004_csv",
            "--cutoff",
            "2004-01-01",
            "--files",
            str(csv_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "would_delete_rows=1" in result.stdout
    assert "kept_rows=2" in result.stdout
    assert [row["value"] for row in _read_rows(csv_path)] == ["old", "keep", "new"]


def test_trim_pre2004_apply_removes_older_rows_in_place(tmp_path: Path) -> None:
    csv_path = tmp_path / "sample.csv"
    _write_csv(
        csv_path,
        [
            {"time": "2003.12.31 23:00", "value": "old"},
            {"time": "2004.01.01 00:00", "value": "keep"},
            {"time": "2005.01.01 00:00", "value": "new"},
        ],
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "processing.trim_pre2004_csv",
            "--cutoff",
            "2004-01-01",
            "--apply",
            "--files",
            str(csv_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "deleted_rows=1" in result.stdout
    assert [row["value"] for row in _read_rows(csv_path)] == ["keep", "new"]
