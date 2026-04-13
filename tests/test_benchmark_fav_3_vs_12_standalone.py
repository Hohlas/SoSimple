import pandas as pd

from ML.benchmark_fav_3_vs_12_standalone import (
    add_fav_ratio,
    compute_metrics,
)


def test_add_fav_ratio_uses_safe_denominator():
    frame = pd.DataFrame(
        {
            "pred_fav_3": [1.0, 2.0],
            "pred_fav_12": [2.0, 0.0],
        }
    )

    result = add_fav_ratio(frame)

    assert result.loc[0, "fav_3_vs_12"] == 0.5
    assert result.loc[1, "fav_3_vs_12"] > 1_000_000


def test_compute_metrics_counts_trades_and_pf():
    frame = pd.DataFrame(
        {
            "pnl_atr": [2.0, -1.0, 3.0],
        }
    )

    result = compute_metrics(frame)

    assert result["n_trades"] == 3
    assert result["gross_profit"] == 5.0
    assert result["gross_loss"] == 1.0
    assert result["pf"] == 5.0
