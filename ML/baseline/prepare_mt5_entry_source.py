from __future__ import annotations

import argparse
import hashlib
import json
from numbers import Integral, Real
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

H1_BAR_DELTA = pd.Timedelta(hours=1)
TIMING_CONTRACT = "feature_time <= time < feature_available_time <= decision_time"


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _coerce_time(series: pd.Series, *, label: str) -> pd.Series:
    parsed = pd.to_datetime(series, errors="coerce")
    if parsed.isna().any():
        raise ValueError(f"invalid {label} values")
    return parsed.dt.strftime("%Y.%m.%d %H:%M")


def _validate_latency_bars(latency_bars: int) -> int:
    if isinstance(latency_bars, bool):
        raise ValueError("latency_bars must be an integer number of bars")
    if isinstance(latency_bars, Integral):
        validated = int(latency_bars)
    elif isinstance(latency_bars, Real) and float(latency_bars).is_integer():
        validated = int(latency_bars)
    else:
        raise ValueError("latency_bars must be an integer number of bars")
    if validated < 0:
        raise ValueError("latency_bars must be >= 0")
    return validated


def prepare_entry_quality_source(
    source: pd.DataFrame,
    *,
    rule_id: str = "entry_quality_filter",
    latency_bars: int = 0,
) -> pd.DataFrame:
    latency_bars = _validate_latency_bars(latency_bars)

    missing = [col for col in SOURCE_COLUMNS if col not in source.columns]
    if missing:
        raise ValueError(f"missing entry source columns: {missing}")

    signal_dt = pd.to_datetime(source["signal_time"], errors="coerce")
    if signal_dt.isna().any():
        raise ValueError("invalid signal_time values")

    feature_time = signal_dt
    feature_available_time = signal_dt + H1_BAR_DELTA
    decision_time = feature_available_time + latency_bars * H1_BAR_DELTA
    match_time = decision_time - H1_BAR_DELTA

    side = source["side"].astype(str).str.upper().str.strip()
    bad_side = sorted(set(side) - {"BUY", "SELL"})
    if bad_side:
        raise ValueError(f"unsupported side values: {bad_side}")

    prepared = pd.DataFrame(
        {
            "time": match_time.dt.strftime("%Y.%m.%d %H:%M"),
            "feature_time": feature_time.dt.strftime("%Y.%m.%d %H:%M"),
            "feature_available_time": feature_available_time.dt.strftime("%Y.%m.%d %H:%M"),
            "decision_time": decision_time.dt.strftime("%Y.%m.%d %H:%M"),
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
    latency_bars: int = 0,
) -> dict[str, Any]:
    input_path = Path(input_csv)
    output_csv_path = Path(output_csv)
    output_json_path = Path(output_json)

    source = pd.read_csv(input_path, sep=";", usecols=lambda col: col in set(SOURCE_COLUMNS) | FORBIDDEN_COLUMNS)
    prepared = prepare_entry_quality_source(source, rule_id=rule_id, latency_bars=latency_bars)

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
        "time_policy": "H1 diagnostic timing: feature_time=signal_time; feature_available_time=signal_time+1h; decision_time=feature_available_time+latency_bars*h; time=decision_time-1h for MT5 Time[1] matching",
        "timing_contract": TIMING_CONTRACT,
        "latency_bars": int(latency_bars),
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
    parser.add_argument("--latency-bars", type=int, default=0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    metadata = write_prepared_source(
        input_csv=args.input_csv,
        output_csv=args.output_csv,
        output_json=args.output_json,
        rule_id=args.rule_id,
        latency_bars=args.latency_bars,
    )
    print(json.dumps(metadata, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
