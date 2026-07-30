from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from ML.baseline.mt5_signal_schema import MT5_EVENT_COLUMNS
from ML.baseline.parse_mt5_execution_report import compute_mt5_metrics, parse_mt5_events


def _event_row(event: str, time: str, **overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "event": event,
        "time": time,
        "feature_time": "2023.01.02 09:00",
        "feature_available_time": "2023.01.02 10:00",
        "decision_time": "2023.01.02 10:00",
        "execution_time": time,
        "rule_id": "rule01",
        "signal_time": "2023.01.02 10:00",
        "ticket": 1,
        "side": "BUY",
        "requested_price": 1900.0,
        "fill_price": 1900.0,
        "order_open_price": 1900.0,
        "order_close_price": 1912.5 if event == "CLOSE" else 0.0,
        "stop_price": 1890.0,
        "close_reason": "",
        "profit": 0.0,
        "bars_since_fill": 0,
        "bid": 1900.0,
        "ask": 1900.2,
        "spread": 0.2,
        "spread_atr": 0.02,
        "bar_open": 1901.0,
        "bar_high": 1913.0,
        "bar_low": 1899.0,
        "bar_close": 1912.5,
        "calculation_open": 1901.0,
        "slippage_points": 0.0,
        "entry": 1900.0,
        "take_profit": 0.0,
        "close": 1912.5 if event == "CLOSE" else 0.0,
        "swap": 0.0,
        "commission": 0.0,
        "hold_bars": 0,
        "open_positions": 1 if event != "CLOSE" else 0,
        "max_positions": 1,
        "balance": 10000.0,
        "equity": 10012.5,
        "entry_time": "2023.01.02 10:05" if event != "ORDER_PLACED" else "",
        "exit_time": time if event == "CLOSE" else "",
        "unrealized_pnl_r_before_decision": 0.0,
        "max_favorable_r_before_decision": 0.0,
        "max_adverse_r_before_decision": 0.0,
        "ml_exit_score": 1.0 if event == "CLOSE" else 0.0,
        "ml_exit_decision": 1 if event == "CLOSE" else 0,
        "comment": "",
    }
    row.update(overrides)
    return row


def test_parse_mt5_events_and_compute_metrics(tmp_path: Path) -> None:
    path = tmp_path / "events.csv"
    pd.DataFrame(
        [
            _event_row("ORDER_PLACED", "2023.01.02 10:00", open_positions=0),
            _event_row("OPEN", "2023.01.02 10:05", open_positions=1),
            _event_row(
                "ML_CLOSE",
                "2023.01.02 11:00",
                bars_since_fill=1,
                close_reason="ML_CLOSE",
                profit=0.0,
                open_positions=1,
                ml_exit_score=1.0,
                ml_exit_decision=1,
            ),
            _event_row(
                "CLOSE",
                "2023.01.02 12:00",
                bars_since_fill=1,
                close_reason="broker_history_limited",
                profit=12.5,
                open_positions=0,
            ),
        ],
        columns=MT5_EVENT_COLUMNS,
    ).to_csv(path, sep=";", index=False)

    events = parse_mt5_events(path)
    metrics = compute_mt5_metrics(events)

    assert metrics["status"] == "DIAGNOSTIC_ONLY"
    assert metrics["order_counts"]["ORDER_PLACED"] == 1
    assert metrics["order_counts"]["OPEN"] == 1
    assert metrics["order_counts"]["ML_CLOSE"] == 1
    assert metrics["order_counts"]["CLOSE"] == 1
    assert metrics["open_counts"]["OPEN"] == 1
    assert metrics["close_counts"]["CLOSE"] == 1
    assert metrics["ml_close_decision_count"] == 1
    assert "ML_CLOSE" not in metrics["close_reason_counts"]
    assert metrics["close_reason_counts"]["broker_history_limited"] == 1
    assert metrics["profit_sum"] == 12.5
    assert metrics["missing_open_estimate"] == 0


def test_parse_mt5_events_rejects_missing_columns(tmp_path: Path) -> None:
    path = tmp_path / "events_missing.csv"
    frame = pd.DataFrame(
        [
            {
                "event": "OPEN",
                "time": "2023.01.02 10:05",
                "feature_time": "2023.01.02 09:00",
            }
        ]
    )
    frame.to_csv(path, sep=";", index=False)

    with pytest.raises(ValueError, match="missing MT5 event columns"):
        parse_mt5_events(path)
