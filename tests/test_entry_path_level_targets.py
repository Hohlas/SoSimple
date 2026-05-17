import pandas as pd

from ML.entry_path_level_targets import candidate_signal_from_fractal0_direction
from ML.entry_path_level_targets import summarize_direction_baseline


def test_signal_from_fractal0_direction_uses_entry_path_convention():
    assert candidate_signal_from_fractal0_direction(-1) == 1
    assert candidate_signal_from_fractal0_direction(1) == -1
    assert candidate_signal_from_fractal0_direction(0) == 0


def test_direction_baseline_reports_direct_reverse_and_side_buckets(tmp_path):
    source = pd.DataFrame(
        {
            "time": ["2024.01.01 00:00", "2024.01.01 02:00"],
            "ATR": [1.0, 1.0],
            "fractal0": [
                "1704067200:100:-1:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:1",
                "1704074400:100:1:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:1",
            ],
        }
    )
    ohlc_path = tmp_path / "ohlc.csv"
    pd.DataFrame(
        {
            "time": [
                "2024.01.01 00:00",
                "2024.01.01 01:00",
                "2024.01.01 02:00",
                "2024.01.01 03:00",
                "2024.01.01 04:00",
            ],
            "open": [100.0, 100.0, 101.0, 100.0, 99.0],
            "high": [101.0, 102.0, 102.0, 100.0, 99.5],
            "low": [99.0, 100.0, 100.0, 98.0, 97.5],
            "close": [100.0, 101.0, 102.0, 99.0, 98.0],
            "volume": [1, 1, 1, 1, 1],
        }
    ).to_csv(ohlc_path, sep=";", index=False)

    summary = summarize_direction_baseline(source, ohlc_path, horizon=2)

    assert summary["direct"]["trades"] == 2
    assert summary["reverse"]["trades"] == 2
    assert summary["buy_only"]["trades"] == 1
    assert summary["sell_only"]["trades"] == 1
    assert summary["direct"]["mean_pnl_atr"] > summary["reverse"]["mean_pnl_atr"]
