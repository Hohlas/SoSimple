import pandas as pd

from ML.benchmark_execution_policy_v2 import ExitPolicy
from ML.benchmark_execution_policy_v2 import _summarize
from ML.benchmark_execution_policy_v2 import simulate_policy


def test_summarize_includes_stability_and_concentration_metrics():
    trades = pd.DataFrame(
        {
            "entry_time": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
            "exit_time": pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-04"]),
            "pnl_atr": [2.0, -1.0, 0.5],
            "hold_hours": [24.0, 24.0, 24.0],
        }
    )

    result = _summarize("sample", ExitPolicy(name="trail_x8"), trades)

    assert result["dataset"] == "sample"
    assert result["policy"] == "trail_x8"
    assert "ulcer_index_atr" in result
    assert "equity_linearity_r2" in result
    assert "profit_concentration_top_3" in result
    assert result["worst_trade_atr"] == -1.0
    assert result["max_consecutive_losses"] == 1
    assert result["max_drawdown_atr"] > 0.0


def test_shrinking_trailing_closes_after_profit_gives_back_less():
    bars = [
        {"time": pd.Timestamp("2024-01-01 00:00"), "open": 100.0, "high": 100.0, "low": 100.0, "close": 100.0, "atr14": 1.0},
        {"time": pd.Timestamp("2024-01-01 01:00"), "open": 100.0, "high": 100.0, "low": 100.0, "close": 100.0, "atr14": 1.0},
        {"time": pd.Timestamp("2024-01-01 02:00"), "open": 100.0, "high": 110.0, "low": 104.5, "close": 109.0, "atr14": 1.0},
        {"time": pd.Timestamp("2024-01-01 03:00"), "open": 109.0, "high": 110.0, "low": 103.5, "close": 104.0, "atr14": 1.0},
    ]
    index_by_time = {row["time"]: idx for idx, row in enumerate(bars)}
    signals = pd.DataFrame({"time": [pd.Timestamp("2024-01-01 00:00")], "signal": [1]})

    fixed = simulate_policy(
        signals,
        bars,
        index_by_time,
        ExitPolicy(name="trail_x8", stop_atr=8.0, trail_atr=8.0),
    )
    shrinking = simulate_policy(
        signals,
        bars,
        index_by_time,
        ExitPolicy(name="shrinking", stop_atr=8.0, trail_atr=8.0, shrink_tiers=((8.0, 6.0),)),
    )

    assert fixed.empty
    assert shrinking.iloc[0]["pnl_atr"] == 4.0
