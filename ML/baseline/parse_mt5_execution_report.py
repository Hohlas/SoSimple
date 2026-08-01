from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from ML.baseline.mt5_signal_schema import MT5_EVENT_COLUMNS
from ML.baseline.mt5_signal_schema import validate_mt5_event_frame

NEW_EXECUTION_CONTEXT_DEFAULTS: dict[str, object] = {
    "error_code": 0,
    "error_class": "",
    "retcode": 0,
    "retcode_text": "",
    "request_seq": -1,
    "magic": 0,
    "symbol": "",
    "entry_type": "",
}


def parse_mt5_events(path: str | Path) -> pd.DataFrame:
    frame = pd.read_csv(path, sep=";")
    for column, default in NEW_EXECUTION_CONTEXT_DEFAULTS.items():
        if column not in frame.columns:
            frame[column] = default
    validate_mt5_event_frame(frame)
    return frame[MT5_EVENT_COLUMNS]


def _event_counts(events: pd.DataFrame) -> dict[str, int]:
    counts = events["event"].astype(str).value_counts(dropna=False)
    return {str(key): int(value) for key, value in counts.items()}


def _filtered_reason_counts(events: pd.DataFrame) -> dict[str, int]:
    if "close_reason" not in events.columns:
        return {}
    closes = events.loc[events["event"].astype(str).eq("CLOSE"), "close_reason"].astype(str)
    closes = closes[closes.ne("") & closes.ne("nan")]
    return {str(key): int(value) for key, value in closes.value_counts(dropna=False).items()}


def _tx_comment_field(comment: str, key: str) -> str:
    for part in str(comment).split("|"):
        if part.startswith(key + "="):
            return part[len(key) + 1:]
    return ""


def _tx_position_ids(events: pd.DataFrame, event_name: str) -> dict[str, pd.Series]:
    rows = events.loc[events["event"].astype(str).eq(event_name)]
    result: dict[str, pd.Series] = {}
    for _, row in rows.iterrows():
        position_id = _tx_comment_field(row.get("comment", ""), "position_id")
        if position_id and position_id != "0":
            result.setdefault(position_id, row)
    return result


def reconcile_positions(events: pd.DataFrame) -> dict[str, object]:
    tx_opens = _tx_position_ids(events, "TX_OPEN")
    tx_closes = _tx_position_ids(events, "TX_CLOSE")

    open_rows = events.loc[events["event"].astype(str).eq("OPEN")]
    open_tickets = {
        str(int(t)) if str(t).replace(".0", "").isdigit() else str(t)
        for t in pd.to_numeric(open_rows.get("ticket"), errors="coerce").dropna().astype("int64")
    }

    all_positions = sorted(set(tx_opens) | set(tx_closes) | open_tickets, key=lambda v: (len(v), v))

    classification: dict[str, str] = {}
    same_h1_count = 0
    for position_id in all_positions:
        if position_id in tx_closes:
            classification[position_id] = "CLOSED_TX"
            if position_id in tx_opens:
                open_time = pd.to_datetime(tx_opens[position_id]["time"], errors="coerce")
                close_time = pd.to_datetime(tx_closes[position_id]["time"], errors="coerce")
                if pd.notna(open_time) and pd.notna(close_time) and open_time.floor("h") == close_time.floor("h"):
                    same_h1_count += 1
        elif position_id in tx_opens:
            classification[position_id] = "OPEN_AT_END"
        else:
            classification[position_id] = "UNEXPLAINED"

    class_counts = {"CLOSED_TX": 0, "OPEN_AT_END": 0, "UNEXPLAINED": 0}
    for value in classification.values():
        class_counts[value] += 1

    signal_linked = sum(1 for position_id in tx_opens if position_id in open_tickets)

    return {
        "position_count": len(all_positions),
        "class_counts": class_counts,
        "unexplained_position_ids": sorted(
            (pid for pid, cls in classification.items() if cls == "UNEXPLAINED"),
            key=lambda v: (len(v), v),
        ),
        "open_at_end_position_ids": sorted(
            (pid for pid, cls in classification.items() if cls == "OPEN_AT_END"),
            key=lambda v: (len(v), v),
        ),
        "same_h1_count": same_h1_count,
        "tx_open_count": len(tx_opens),
        "tx_close_count": len(tx_closes),
        "signal_linked_tx_open_count": signal_linked,
    }


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
    open_without_close_estimate = max(int(order_counts.get("OPEN", 0)) - int(order_counts.get("CLOSE", 0)), 0)
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
        "open_without_close_estimate": open_without_close_estimate,
        "reconciliation": reconcile_positions(events),
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
