import re
from pathlib import Path

import pandas as pd
import pytest

from ML.baseline.mt5_signal_schema import (
    MT5_EVENT_COLUMNS,
    MT5_SIGNAL_COLUMNS,
    validate_mt5_event_frame,
    validate_mt5_signal_frame,
)

MQL_SIGNAL_LIB = Path("MT/MQL5/Include/lib_ML_Signal.mqh")


def test_mt5_event_mql_header_matches_python_contract():
    text = MQL_SIGNAL_LIB.read_text(encoding="utf-8")
    match = re.search(r'FileWrite\(handle,\s*("event".*?)\);', text, flags=re.S)

    assert match is not None
    mql_columns = re.findall(r'"([^"]+)"', match.group(1))
    assert mql_columns == MT5_EVENT_COLUMNS


def test_mt5_signal_schema_rejects_future_exit_columns():
    frame = pd.DataFrame(
        [
            {
                "time": "2023.01.02 09:00",
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
                "time": "2023.01.02 09:00",
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
                "time": "2023.01.02 09:00",
                "feature_time": "2023.01.02 09:00",
                "feature_available_time": "2023.01.02 10:00",
                "decision_time": "2023.01.02 09:00",
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

    with pytest.raises(ValueError, match="decision_time"):
        validate_mt5_signal_frame(frame)


def test_mt5_signal_schema_rejects_decision_before_feature_available_time():
    frame = pd.DataFrame(
        [
            {
                "time": "2023.01.02 09:00",
                "feature_time": "2023.01.02 09:00",
                "feature_available_time": "2023.01.02 10:01",
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

    with pytest.raises(ValueError, match="feature_available_time > decision_time"):
        validate_mt5_signal_frame(frame)


def test_mt5_signal_schema_requires_match_time_before_feature_available_time():
    frame = pd.DataFrame(
        [
            {
                "time": "2023.01.02 09:00",
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


def test_mt5_signal_schema_rejects_copied_timing_contract():
    frame = pd.DataFrame(
        [
            {
                "time": "2023.01.02 09:00",
                "feature_time": "2023.01.02 09:00",
                "feature_available_time": "2023.01.02 09:00",
                "decision_time": "2023.01.02 09:00",
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

    with pytest.raises(ValueError, match="time >= feature_available_time"):
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
                "signal_time": "2023.01.02 09:00",
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


def test_mt5_event_schema_rejects_decision_before_feature_available_time():
    frame = pd.DataFrame(
        [
            {
                "event": "OPEN",
                "time": "2023.01.02 10:05",
                "feature_time": "2023.01.02 09:00",
                "feature_available_time": "2023.01.02 10:01",
                "decision_time": "2023.01.02 10:00",
                "execution_time": "2023.01.02 10:05",
                "rule_id": "rule01",
                "signal_time": "2023.01.02 09:00",
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

    with pytest.raises(ValueError, match="feature_available_time > decision_time"):
        validate_mt5_event_frame(frame)


def test_mt5_event_schema_rejects_unknown_event_name():
    frame = pd.DataFrame(
        [{col: "" for col in MT5_EVENT_COLUMNS}],
        columns=MT5_EVENT_COLUMNS,
    )
    frame.loc[0, "event"] = "TX_OPEN_TYPO"

    with pytest.raises(ValueError, match="unknown MT5 event names"):
        validate_mt5_event_frame(frame)


def test_mt5_event_schema_accepts_timing_violation_event_name():
    frame = pd.DataFrame(
        [{col: "" for col in MT5_EVENT_COLUMNS}],
        columns=MT5_EVENT_COLUMNS,
    )
    frame.loc[0, "event"] = "TIMING_VIOLATION"

    validate_mt5_event_frame(frame)


def test_mt5_event_schema_validates_signal_time_as_entry_match_key():
    frame = pd.DataFrame(
        [
            {
                "event": "ORDER_PLACED",
                "time": "2023.01.02 10:00",
                "feature_time": "2023.01.02 09:00",
                "feature_available_time": "2023.01.02 10:00",
                "decision_time": "2023.01.02 10:00",
                "execution_time": "2023.01.02 10:00",
                "rule_id": "rule01",
                "signal_time": "2023.01.02 09:00",
                "error_code": 0,
                "error_class": "",
                "retcode": 0,
                "retcode_text": "",
                "request_seq": 1,
                "magic": 163856259,
                "symbol": "XAUUSD",
                "entry_type": "BUY_LIMIT",
                "ticket": 0,
                "side": "BUY",
                "requested_price": 1900.0,
                "fill_price": 0.0,
                "order_open_price": 0.0,
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
                "entry": 0.0,
                "take_profit": 0.0,
                "close": 0.0,
                "swap": 0.0,
                "commission": 0.0,
                "hold_bars": 0,
                "open_positions": 0,
                "max_positions": 1,
                "balance": 10000.0,
                "equity": 10000.0,
                "entry_time": "",
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

    validate_mt5_event_frame(frame)


def test_export_mt5_entry_signals_writes_entry_only_csv(tmp_path):
    from ML.baseline.export_mt5_entry_signals import export_mt5_entry_signals

    source = pd.DataFrame(
        [
            {
                "time": "2023.01.02 09:00",
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


def test_prepare_mt5_entry_source_from_entry_quality_scores_contract():
    from ML.baseline.prepare_mt5_entry_source import prepare_entry_quality_source

    source = pd.DataFrame(
        [
            {
                "time": "2023.01.02 10:00",
                "signal_time": "2023.01.02 10:00",
                "side": "SELL",
                "limit_price": 1910.0,
                "protective_stop_price": 1920.0,
                "atr": 10.0,
                "pnl_r": -1.0,
                "exit_time": "2023.01.02 15:00",
            }
        ]
    )

    prepared = prepare_entry_quality_source(source)

    assert prepared.to_dict(orient="records") == [
        {
            "time": "2023.01.02 10:00",
            "feature_time": "2023.01.02 10:00",
            "feature_available_time": "2023.01.02 11:00",
            "decision_time": "2023.01.02 11:00",
            "rule_id": "entry_quality_filter",
            "side": "SELL",
            "limit_price": 1910.0,
            "protective_stop_price": 1920.0,
            "atr": 10.0,
        }
    ]
    assert "pnl_r" not in prepared.columns
    assert "exit_time" not in prepared.columns


def test_prepare_mt5_entry_source_latency_bars_shifts_match_time_to_decision_minus_one_bar():
    from ML.baseline.prepare_mt5_entry_source import prepare_entry_quality_source

    source = pd.DataFrame(
        [
            {
                "time": "2023.01.02 10:00",
                "signal_time": "2023.01.02 10:00",
                "side": "BUY",
                "limit_price": 1900.0,
                "protective_stop_price": 1890.0,
                "atr": 10.0,
            }
        ]
    )

    prepared = prepare_entry_quality_source(source, latency_bars=2)

    assert prepared.loc[0, "feature_time"] == "2023.01.02 10:00"
    assert prepared.loc[0, "feature_available_time"] == "2023.01.02 11:00"
    assert prepared.loc[0, "decision_time"] == "2023.01.02 13:00"
    assert prepared.loc[0, "time"] == "2023.01.02 12:00"


def test_prepare_mt5_entry_source_rejects_negative_latency_bars():
    from ML.baseline.prepare_mt5_entry_source import prepare_entry_quality_source

    source = pd.DataFrame(
        [
            {
                "time": "2023.01.02 10:00",
                "signal_time": "2023.01.02 10:00",
                "side": "BUY",
                "limit_price": 1900.0,
                "protective_stop_price": 1890.0,
                "atr": 10.0,
            }
        ]
    )

    with pytest.raises(ValueError, match="latency_bars must be >= 0"):
        prepare_entry_quality_source(source, latency_bars=-1)


def test_write_prepared_source_records_timing_metadata(tmp_path: Path):
    import json

    from ML.baseline.prepare_mt5_entry_source import TIMING_CONTRACT, write_prepared_source

    input_csv = tmp_path / "input.csv"
    output_csv = tmp_path / "prepared.csv"
    output_json = tmp_path / "prepared.json"
    input_csv.write_text(
        "\n".join(
            [
                "time;signal_time;side;limit_price;protective_stop_price;atr;pnl_r",
                "2023.01.02 10:00;2023.01.02 10:00;BUY;1900;1890;10;1.0",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    metadata = write_prepared_source(
        input_csv=input_csv,
        output_csv=output_csv,
        output_json=output_json,
        latency_bars=2,
    )

    written = json.loads(output_json.read_text(encoding="utf-8"))
    assert metadata == written
    assert written["time_policy"] == (
        "H1 diagnostic timing: feature_time=signal_time; "
        "feature_available_time=signal_time+1h; "
        "decision_time=feature_available_time+latency_bars*h; "
        "time=decision_time-1h for MT5 Time[1] matching"
    )
    assert written["timing_contract"] == TIMING_CONTRACT
    assert written["latency_bars"] == 2
    assert written["output_csv_sha256"]
    assert written["forbidden_source_columns_present"] == ["pnl_r"]
