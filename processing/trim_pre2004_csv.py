# =============================================================================
# Файл: trim_pre2004_csv.py
# Назначение: Dry-run и in-place обрезка CSV строк старше заданной календарной даты.
# Обновлён: 2026-04-25
# Входные данные:
#   - DATA/*.csv и/или MT/MQL4/Files/*.csv (откуда: существующие проектные датасеты)
# Выходные данные:
#   - Те же CSV-файлы после удаления строк старше cutoff (куда: in-place)
# Использование:
#   python -m processing.trim_pre2004_csv
#   python -m processing.trim_pre2004_csv --apply
#   python -m processing.trim_pre2004_csv --files DATA/Nero_EURUSD_train_labeled.csv
# Примечания:
#   - По умолчанию работает в dry-run режиме.
#   - Резервные копии не создаёт.
#   - Удаляет только строки, где колонка `time` раньше cutoff; header сохраняется.
# =============================================================================

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


DEFAULT_CUTOFF = "2004-01-01"
DEFAULT_FILES = [
    "DATA/Nero_EURUSD_train_labeled.csv",
    "DATA/Nero_GBPUSD_train_labeled.csv",
    "DATA/Nero_USDCHF_train_labeled.csv",
    "MT/MQL4/Files/Nero_EURUSD.csv",
    "MT/MQL4/Files/Nero_GBPUSD.csv",
    "MT/MQL4/Files/Nero_USDCHF.csv",
    "MT/MQL4/Files/EURUSD_H1_OHLC.csv",
    "MT/MQL4/Files/GBPUSD_H1_OHLC.csv",
    "MT/MQL4/Files/USDCHF_H1_OHLC.csv",
]


@dataclass(frozen=True)
class TrimSummary:
    path: Path
    total_rows: int
    deleted_rows: int
    kept_rows: int
    first_kept_time: str | None
    last_kept_time: str | None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Trim CSV rows older than cutoff date.")
    parser.add_argument("--apply", action="store_true", help="Apply changes in place. Default is dry-run.")
    parser.add_argument(
        "--cutoff",
        default=DEFAULT_CUTOFF,
        help="Inclusive keep boundary in YYYY-MM-DD format. Rows older than this are removed.",
    )
    parser.add_argument(
        "--files",
        nargs="+",
        default=DEFAULT_FILES,
        help="Explicit CSV paths to trim. Default is the agreed project candidate list.",
    )
    return parser.parse_args()


def _parse_time(value: str) -> datetime:
    return datetime.strptime(value, "%Y.%m.%d %H:%M")


def _resolve_cutoff(cutoff: str) -> datetime:
    return datetime.strptime(cutoff, "%Y-%m-%d")


def trim_csv(path: Path, cutoff: datetime, apply: bool) -> TrimSummary:
    if not path.exists():
        raise FileNotFoundError(f"missing file: {path}")

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=";")
        fieldnames = reader.fieldnames
        if fieldnames is None:
            raise ValueError(f"missing header: {path}")
        if "time" not in fieldnames:
            raise ValueError(f"missing time column: {path}")

        kept_rows: list[dict[str, str]] = []
        total_rows = 0
        for row in reader:
            total_rows += 1
            if _parse_time(row["time"]) >= cutoff:
                kept_rows.append(row)

    deleted_rows = total_rows - len(kept_rows)

    if apply:
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter=";")
            writer.writeheader()
            writer.writerows(kept_rows)

    first_kept_time = kept_rows[0]["time"] if kept_rows else None
    last_kept_time = kept_rows[-1]["time"] if kept_rows else None
    return TrimSummary(
        path=path,
        total_rows=total_rows,
        deleted_rows=deleted_rows,
        kept_rows=len(kept_rows),
        first_kept_time=first_kept_time,
        last_kept_time=last_kept_time,
    )


def main() -> None:
    args = parse_args()
    cutoff = _resolve_cutoff(args.cutoff)
    summaries = [trim_csv(Path(raw_path), cutoff=cutoff, apply=args.apply) for raw_path in args.files]

    mode = "applied" if args.apply else "dry_run"
    total_deleted = 0
    total_kept = 0
    for summary in summaries:
        total_deleted += summary.deleted_rows
        total_kept += summary.kept_rows
        deleted_label = "deleted_rows" if args.apply else "would_delete_rows"
        print(
            f"{summary.path}|mode={mode}|total_rows={summary.total_rows}|"
            f"{deleted_label}={summary.deleted_rows}|kept_rows={summary.kept_rows}|"
            f"first_kept={summary.first_kept_time}|last_kept={summary.last_kept_time}"
        )

    total_label = "deleted_rows" if args.apply else "would_delete_rows"
    print(f"TOTAL|mode={mode}|files={len(summaries)}|{total_label}={total_deleted}|kept_rows={total_kept}")


if __name__ == "__main__":
    main()
