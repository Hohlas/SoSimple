from __future__ import annotations

import pandas as pd

MT5_SIGNAL_COLUMNS = [
    "time",
    "feature_time",
    "feature_available_time",
    "decision_time",
    "rule_id",
    "side",
    "entry_type",
    "limit_price",
    "stop_price",
    "atr",
    "max_fill_lag_bars",
]

MT5_FORBIDDEN_SIGNAL_COLUMNS = {
    "fill_time",
    "exit_time",
    "future_exit_time",
    "future_favorable_r_3",
    "future_adverse_r_3",
    "hold_3_pnl_r",
    "pnl_r",
}

MT5_EVENT_COLUMNS = [
    "event",
    "time",
    "feature_time",
    "feature_available_time",
    "decision_time",
    "execution_time",
    "rule_id",
    "signal_time",
    "error_code",
    "error_class",
    "retcode",
    "retcode_text",
    "request_seq",
    "magic",
    "symbol",
    "entry_type",
    "ticket",
    "side",
    "requested_price",
    "fill_price",
    "order_open_price",
    "order_close_price",
    "stop_price",
    "close_reason",
    "profit",
    "bars_since_fill",
    "bid",
    "ask",
    "spread",
    "spread_atr",
    "bar_open",
    "bar_high",
    "bar_low",
    "bar_close",
    "calculation_open",
    "slippage_points",
    "entry",
    "take_profit",
    "close",
    "swap",
    "commission",
    "hold_bars",
    "open_positions",
    "max_positions",
    "balance",
    "equity",
    "entry_time",
    "exit_time",
    "unrealized_pnl_r_before_decision",
    "max_favorable_r_before_decision",
    "max_adverse_r_before_decision",
    "ml_exit_score",
    "ml_exit_decision",
    "comment",
]


def _validate_time_order(frame: pd.DataFrame, columns: list[str]) -> None:
    parsed = {
        col: pd.to_datetime(frame[col], errors="coerce")
        for col in columns
        if col in frame.columns
    }
    bad_parse = [
        col
        for col, values in parsed.items()
        if (values.isna() & frame[col].fillna("").astype(str).str.strip().ne("")).any()
    ]
    if bad_parse:
        raise ValueError(f"invalid MT5 timestamp values in columns: {bad_parse}")

    for left, right in zip(columns, columns[1:]):
        if left not in parsed or right not in parsed:
            continue
        invalid = parsed[left].notna() & parsed[right].notna() & parsed[left].gt(parsed[right])
        if invalid.any():
            raise ValueError(f"MT5 timing contract violation: {left} > {right}")


def validate_mt5_signal_frame(frame: pd.DataFrame) -> None:
    missing = [col for col in MT5_SIGNAL_COLUMNS if col not in frame.columns]
    if missing:
        raise ValueError(f"missing MT5 signal columns: {missing}")

    forbidden = sorted(MT5_FORBIDDEN_SIGNAL_COLUMNS.intersection(frame.columns))
    if forbidden:
        raise ValueError(
            f"forbidden future/result columns in MT5 signal frame: {forbidden}"
        )

    bad_side = set(frame["side"].astype(str)) - {"BUY", "SELL"}
    if bad_side:
        raise ValueError(f"unsupported side values: {sorted(bad_side)}")

    bad_entry = set(frame["entry_type"].astype(str)) - {"BUY_LIMIT", "SELL_LIMIT"}
    if bad_entry:
        raise ValueError(f"unsupported entry_type values: {sorted(bad_entry)}")

    _validate_time_order(frame, ["feature_time", "feature_available_time", "decision_time"])


MT5_EVENT_NAMES = {
    "INIT",
    "ORDER_PLACED",
    "ORDER_EXPIRED",
    "OPEN_FAILED",
    "OPEN",
    "ML_EVAL",
    "ML_CLOSE",
    "CLOSE",
    "TX_OPEN",
    "TX_CLOSE",
}


def validate_mt5_event_frame(frame: pd.DataFrame) -> None:
    missing = [col for col in MT5_EVENT_COLUMNS if col not in frame.columns]
    if missing:
        raise ValueError(f"missing MT5 event columns: {missing}")

    unknown = sorted(set(frame["event"].astype(str)) - MT5_EVENT_NAMES)
    if unknown:
        raise ValueError(f"unknown MT5 event names: {unknown}")

    _validate_time_order(
        frame,
        ["feature_time", "feature_available_time", "decision_time", "execution_time"],
    )
