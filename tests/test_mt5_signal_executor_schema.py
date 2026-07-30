import pandas as pd
import pytest

from ML.baseline.mt5_signal_schema import (
    MT5_EVENT_COLUMNS,
    MT5_SIGNAL_COLUMNS,
    validate_mt5_event_frame,
    validate_mt5_signal_frame,
)


def test_mt5_signal_schema_rejects_future_exit_columns():
    frame = pd.DataFrame(
        [
            {
                "time": "2023.01.02 10:00",
                "feature_time": "2023.01.02 09:00",
                "feature_available_time": "2023.01.02 10:00",
                "decision_time": "2023.01.02 10:00",
                "rule_id": "rule01",
                "side": "BUY",
                "entry_type": "BUY_LIMIT",
                "limit_price": 1900.0,
                "stop_price": 1890.0,
                "atr": 10.0,
                "max_fill_lag_bars": 6,
                "future_exit_time": "2023.01.02 14:00",
            }
        ]
    )

    with pytest.raises(ValueError, match="future_exit_time"):
        validate_mt5_signal_frame(frame)


def test_mt5_signal_schema_accepts_entry_only_contract():
    frame = pd.DataFrame(
        [
            {
                "time": "2023.01.02 10:00",
                "feature_time": "2023.01.02 09:00",
                "feature_available_time": "2023.01.02 10:00",
                "decision_time": "2023.01.02 10:00",
                "rule_id": "rule01",
                "side": "BUY",
                "entry_type": "BUY_LIMIT",
                "limit_price": 1900.0,
                "stop_price": 1890.0,
                "atr": 10.0,
                "max_fill_lag_bars": 6,
            }
        ]
    )

    validate_mt5_signal_frame(frame)


def test_mt5_signal_schema_rejects_decision_before_features():
    frame = pd.DataFrame(
        [
            {
                "time": "2023.01.02 10:00",
                "feature_time": "2023.01.02 11:00",
                "feature_available_time": "2023.01.02 11:00",
                "decision_time": "2023.01.02 10:00",
                "rule_id": "rule01",
                "side": "BUY",
                "entry_type": "BUY_LIMIT",
                "limit_price": 1900.0,
                "stop_price": 1890.0,
                "atr": 10.0,
                "max_fill_lag_bars": 6,
            }
        ]
    )

    with pytest.raises(ValueError, match="feature_time > decision_time"):
        validate_mt5_signal_frame(frame)


def test_mt5_event_schema_requires_reconciliation_columns():
    assert {
        "event",
        "time",
        "feature_time",
        "feature_available_time",
        "decision_time",
        "execution_time",
        "rule_id",
        "signal_time",
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
        "slippage_points",
        "commission",
        "swap",
        "balance",
        "equity",
        "entry_time",
        "exit_time",
        "unrealized_pnl_r_before_decision",
        "max_favorable_r_before_decision",
        "max_adverse_r_before_decision",
        "ml_exit_score",
        "ml_exit_decision",
    }.issubset(set(MT5_EVENT_COLUMNS))


def test_mt5_event_schema_rejects_execution_before_decision():
    frame = pd.DataFrame(
        [
            {
                "event": "OPEN",
                "time": "2023.01.02 10:05",
                "feature_time": "2023.01.02 09:00",
                "feature_available_time": "2023.01.02 10:00",
                "decision_time": "2023.01.02 10:00",
                "execution_time": "2023.01.02 09:59",
                "rule_id": "rule01",
                "signal_time": "2023.01.02 10:00",
                "ticket": 1,
                "side": "BUY",
                "requested_price": 1900.0,
                "fill_price": 1900.0,
                "order_open_price": 1900.0,
                "order_close_price": 0.0,
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
                "close": 0.0,
                "swap": 0.0,
                "commission": 0.0,
                "hold_bars": 0,
                "open_positions": 1,
                "max_positions": 1,
                "balance": 10000.0,
                "equity": 10012.5,
                "entry_time": "2023.01.02 10:05",
                "exit_time": "",
                "unrealized_pnl_r_before_decision": 0.0,
                "max_favorable_r_before_decision": 0.0,
                "max_adverse_r_before_decision": 0.0,
                "ml_exit_score": 0.0,
                "ml_exit_decision": 0,
                "comment": "",
            }
        ],
        columns=MT5_EVENT_COLUMNS,
    )

    with pytest.raises(ValueError, match="decision_time > execution_time"):
        validate_mt5_event_frame(frame)


def test_export_mt5_entry_signals_writes_entry_only_csv(tmp_path):
    from ML.baseline.export_mt5_entry_signals import export_mt5_entry_signals

    source = pd.DataFrame(
        [
            {
                "time": "2023.01.02 10:00",
                "feature_time": "2023.01.02 09:00",
                "feature_available_time": "2023.01.02 10:00",
                "decision_time": "2023.01.02 10:00",
                "rule_id": "rule01",
                "side": "BUY",
                "limit_price": 1900.0,
                "protective_stop_price": 1890.0,
                "ATR": 10.0,
                "exit_time": "2023.01.02 14:00",
                "pnl_r": 1.5,
            }
        ]
    )

    out_csv = tmp_path / "signals.csv"
    out_json = tmp_path / "signals.json"

    frame = export_mt5_entry_signals(
        source,
        out_csv,
        out_json,
        max_fill_lag_bars=6,
    )

    assert out_csv.exists()
    assert out_json.exists()
    assert list(frame.columns) == MT5_SIGNAL_COLUMNS
    assert "exit_time" not in frame.columns
    assert "pnl_r" not in frame.columns
