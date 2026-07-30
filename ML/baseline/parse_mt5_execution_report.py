from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from ML.baseline.mt5_signal_schema import validate_mt5_event_frame


def parse_mt5_events(path: str | Path) -> pd.DataFrame:
    frame = pd.read_csv(path, sep=";")
    validate_mt5_event_frame(frame)
    return frame


def _event_counts(events: pd.DataFrame) -> dict[str, int]:
    counts = events["event"].astype(str).value_counts(dropna=False)
    return {str(key): int(value) for key, value in counts.items()}


def _filtered_reason_counts(events: pd.DataFrame) -> dict[str, int]:
    if "close_reason" not in events.columns:
        return {}
    closes = events.loc[events["event"].astype(str).eq("CLOSE"), "close_reason"].astype(str)
    closes = closes[closes.ne("") & closes.ne("nan")]
    return {str(key): int(value) for key, value in closes.value_counts(dropna=False).items()}


def compute_mt5_metrics(events: pd.DataFrame) -> dict[str, object]:
    order_counts = _event_counts(events)
    open_counts = {
        "OPEN": int(order_counts.get("OPEN", 0)),
        "ORDER_PLACED": int(order_counts.get("ORDER_PLACED", 0)),
    }
    close_counts = {
        "CLOSE": int(order_counts.get("CLOSE", 0)),
    }
    closes = events.loc[events["event"].astype(str).eq("CLOSE")].copy()
    profit = pd.to_numeric(closes.get("profit"), errors="coerce").fillna(0.0)
    missing_open_estimate = max(int(order_counts.get("ORDER_PLACED", 0)) - int(order_counts.get("OPEN", 0)), 0)
    ml_close_decision_count = int(order_counts.get("ML_CLOSE", 0))

    return {
        "status": "DIAGNOSTIC_ONLY",
        "order_counts": order_counts,
        "open_counts": open_counts,
        "close_counts": close_counts,
        "close_reason_counts": _filtered_reason_counts(events),
        "ml_close_decision_count": ml_close_decision_count,
        "profit_sum": float(profit.sum()),
        "missing_open_estimate": missing_open_estimate,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse MT5 execution report and emit diagnostic metrics.")
    parser.add_argument("--events", required=True, help="Path to MT5 event CSV")
    parser.add_argument("--output-json", required=True, help="Path to output metrics JSON")
    args = parser.parse_args()

    events = parse_mt5_events(args.events)
    metrics = compute_mt5_metrics(events)
    Path(args.output_json).write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
