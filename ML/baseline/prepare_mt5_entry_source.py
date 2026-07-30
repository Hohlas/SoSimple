from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd


SOURCE_COLUMNS = [
    "time",
    "signal_time",
    "side",
    "limit_price",
    "protective_stop_price",
    "atr",
]

OUTPUT_COLUMNS = [
    "time",
    "feature_time",
    "feature_available_time",
    "decision_time",
    "rule_id",
    "side",
    "limit_price",
    "protective_stop_price",
    "atr",
]

FORBIDDEN_COLUMNS = {
    "fill_time",
    "exit_time",
    "future_exit_time",
    "future_favorable_r_3",
    "future_adverse_r_3",
    "hold_3_pnl_r",
    "pnl_r",
}


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _coerce_time(series: pd.Series, *, label: str) -> pd.Series:
    parsed = pd.to_datetime(series, errors="coerce")
    if parsed.isna().any():
        raise ValueError(f"invalid {label} values")
    return parsed.dt.strftime("%Y.%m.%d %H:%M")


def prepare_entry_quality_source(
    source: pd.DataFrame,
    *,
    rule_id: str = "entry_quality_filter",
) -> pd.DataFrame:
    missing = [col for col in SOURCE_COLUMNS if col not in source.columns]
    if missing:
        raise ValueError(f"missing entry source columns: {missing}")

    time = _coerce_time(source["time"], label="time")
    signal_time = _coerce_time(source["signal_time"], label="signal_time")
    if not time.eq(signal_time).all():
        raise ValueError("time and signal_time differ; cannot infer a single diagnostic decision time")

    side = source["side"].astype(str).str.upper().str.strip()
    bad_side = sorted(set(side) - {"BUY", "SELL"})
    if bad_side:
        raise ValueError(f"unsupported side values: {bad_side}")

    prepared = pd.DataFrame(
        {
            "time": signal_time,
            "feature_time": signal_time,
            "feature_available_time": signal_time,
            "decision_time": signal_time,
            "rule_id": rule_id,
            "side": side,
            "limit_price": pd.to_numeric(source["limit_price"], errors="raise"),
            "protective_stop_price": pd.to_numeric(source["protective_stop_price"], errors="raise"),
            "atr": pd.to_numeric(source["atr"], errors="raise"),
        }
    )
    return prepared[OUTPUT_COLUMNS].copy()


def write_prepared_source(
    *,
    input_csv: str | Path,
    output_csv: str | Path,
    output_json: str | Path,
    rule_id: str = "entry_quality_filter",
) -> dict[str, Any]:
    input_path = Path(input_csv)
    output_csv_path = Path(output_csv)
    output_json_path = Path(output_json)

    source = pd.read_csv(input_path, sep=";", usecols=lambda col: col in set(SOURCE_COLUMNS) | FORBIDDEN_COLUMNS)
    prepared = prepare_entry_quality_source(source, rule_id=rule_id)

    output_csv_path.parent.mkdir(parents=True, exist_ok=True)
    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    prepared.to_csv(output_csv_path, sep=";", index=False)

    metadata: dict[str, Any] = {
        "status": "DIAGNOSTIC_ONLY",
        "source_csv": str(input_path),
        "source_csv_sha256": _sha256_file(input_path),
        "output_csv": str(output_csv_path),
        "output_csv_sha256": _sha256_file(output_csv_path),
        "rows": int(len(prepared)),
        "rule_id": rule_id,
        "date_from": str(prepared["time"].min()) if not prepared.empty else None,
        "date_to": str(prepared["time"].max()) if not prepared.empty else None,
        "time_policy": "feature_time, feature_available_time and decision_time are copied from signal_time; diagnostic bridge only",
        "forbidden_source_columns_present": sorted(set(source.columns) & FORBIDDEN_COLUMNS),
        "forbidden_columns_exported": sorted(set(prepared.columns) & FORBIDDEN_COLUMNS),
    }
    output_json_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return metadata


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare diagnostic MT5 entry source from entry-quality score CSV.")
    parser.add_argument("--input-csv", required=True)
    parser.add_argument("--output-csv", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--rule-id", default="entry_quality_filter")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    metadata = write_prepared_source(
        input_csv=args.input_csv,
        output_csv=args.output_csv,
        output_json=args.output_json,
        rule_id=args.rule_id,
    )
    print(json.dumps(metadata, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
