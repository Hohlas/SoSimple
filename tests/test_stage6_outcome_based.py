import numpy as np
import pandas as pd
import pytest

import ML.baseline.benchmark_stage6_outcome_based as s6


def test_stage6_config_is_fixed_and_narrow():
    cfg = s6.STAGE6_0_CONFIG

    assert cfg.horizon_bars == 24
    assert cfg.stop_offset_atr == 0.5
    assert cfg.take_profit_atr == 2.0
    assert cfg.entry_lag_bars == 1
    assert cfg.same_bar_policy == "sl_first"
    assert cfg.primary_profile == "clock_shift_back"
    assert cfg.disclosure_profiles == ("clock_shift_back_impulse",)


def test_stage6_target_columns_are_denied_from_features():
    target_cols = set(s6.stage6_target_columns())
    denylist = set(s6.stage6_feature_denylist())

    assert "stage6_tp_vs_rest_flag" in target_cols
    assert "stage6_pnl_r" in target_cols
    assert target_cols <= denylist
    assert all(col.startswith("stage6_") for col in target_cols)


def test_stage6_first_touch_tp_sl_ambiguous_and_timeout():
    buy_tp = s6.stage6_first_touch_trade_result(
        entry_price=100.0,
        stop_price=98.0,
        take_price=104.0,
        side="buy",
        future_bars=[{"open": 100.0, "high": 104.5, "low": 99.0, "close": 104.0}],
    )
    sell_sl = s6.stage6_first_touch_trade_result(
        entry_price=100.0,
        stop_price=102.0,
        take_price=96.0,
        side="sell",
        future_bars=[{"open": 100.0, "high": 102.5, "low": 99.0, "close": 101.0}],
    )
    ambiguous = s6.stage6_first_touch_trade_result(
        entry_price=100.0,
        stop_price=98.0,
        take_price=104.0,
        side="buy",
        future_bars=[{"open": 100.0, "high": 105.0, "low": 97.5, "close": 100.0}],
    )
    timeout = s6.stage6_first_touch_trade_result(
        entry_price=100.0,
        stop_price=98.0,
        take_price=104.0,
        side="buy",
        future_bars=[{"open": 100.0, "high": 101.0, "low": 99.0, "close": 101.0}],
    )

    assert buy_tp == {"close_reason": "TP", "bars_held": 1, "pnl_r": 2.0}
    assert sell_sl == {"close_reason": "SL", "bars_held": 1, "pnl_r": -1.0}
    assert ambiguous == {"close_reason": "AMBIGUOUS_SL_FIRST", "bars_held": 1, "pnl_r": -1.0}
    assert timeout == {"close_reason": "TIMEOUT", "bars_held": 1, "pnl_r": 0.5}


def test_stage6_build_outcome_labels_uses_next_bar_open_and_row_time(tmp_path):
    ohlc_path = tmp_path / "ohlc.csv"
    rows = [{"time": f"2025.01.01 {i:02d}:00", "open": 100.0, "high": 100.0, "low": 100.0, "close": 100.0} for i in range(24)]
    rows += [{"time": f"2025.01.02 {i:02d}:00", "open": 100.0, "high": 100.0, "low": 100.0, "close": 100.0} for i in range(24)]
    rows[1] = {"time": "2025.01.01 01:00", "open": 101.0, "high": 101.0, "low": 100.0, "close": 100.5}
    rows[2] = {"time": "2025.01.01 02:00", "open": 101.0, "high": 105.5, "low": 100.8, "close": 105.0}
    pd.DataFrame(rows).to_csv(ohlc_path, sep=";", index=False)

    fractal0 = "0:100.0:-1:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:1.0:0"
    df = pd.DataFrame([{
        "time": "2025.01.01 01:00",
        "ATR": 2.0,
        "fractal0": fractal0,
    }])

    out = s6.stage6_build_outcome_labels(df, ohlc_path=ohlc_path)

    assert out.loc[0, "stage6_side"] == "buy"
    assert out.loc[0, "stage6_entry_price"] == 101.0
    assert out.loc[0, "stage6_stop_price"] == 99.0
    assert out.loc[0, "stage6_take_price"] == 105.0
    assert out.loc[0, "stage6_close_reason"] == "TP"
    assert out.loc[0, "stage6_tp_vs_rest_flag"] == 1


def test_stage6_entry_bar_high_low_are_counted_after_open(tmp_path):
    ohlc_path = tmp_path / "ohlc.csv"
    rows = [{"time": f"2025.01.01 {i:02d}:00", "open": 100.0, "high": 100.0, "low": 100.0, "close": 100.0} for i in range(24)]
    rows += [{"time": f"2025.01.02 {i:02d}:00", "open": 100.0, "high": 100.0, "low": 100.0, "close": 100.0} for i in range(24)]
    rows[1] = {"time": "2025.01.01 01:00", "open": 100.0, "high": 100.0, "low": 100.0, "close": 100.0}
    rows[2] = {"time": "2025.01.01 02:00", "open": 101.0, "high": 105.2, "low": 100.9, "close": 104.0}
    pd.DataFrame(rows).to_csv(ohlc_path, sep=";", index=False)

    fractal0 = "0:100.0:-1:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:1.0:0"
    df = pd.DataFrame([{
        "time": "2025.01.01 01:00",
        "ATR": 2.0,
        "fractal0": fractal0,
    }])

    out = s6.stage6_build_outcome_labels(df, ohlc_path=ohlc_path)

    assert out.loc[0, "stage6_entry_time"] == pd.Timestamp("2025-01-01 02:00:00")
    assert out.loc[0, "stage6_entry_price"] == 101.0
    assert out.loc[0, "stage6_close_reason"] == "TP"
    assert out.loc[0, "stage6_bars_held"] == 1
