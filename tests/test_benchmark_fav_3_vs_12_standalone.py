import pandas as pd

from ML.benchmark_fav_3_vs_12_standalone import (
    EPS,
    add_fav_ratio,
    compute_metrics,
    evaluate_threshold_grid,
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
    assert result.loc[1, "fav_3_vs_12"] == 2.0 / EPS


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


def test_compute_metrics_returns_numeric_pf_for_zero_pnl():
    frame = pd.DataFrame(
        {
            "pnl_atr": [0.0, 0.0],
        }
    )

    result = compute_metrics(frame)

    assert result["n_trades"] == 2
    assert result["gross_profit"] == 0.0
    assert result["gross_loss"] == 0.0
    assert result["pf"] == 0.0


def test_evaluate_threshold_grid_selects_ratio_lte_threshold():
    frame = pd.DataFrame(
        {
            "fav_3_vs_12": [0.2, 0.5, 0.8],
            "pnl_atr": [1.0, -1.0, 2.0],
            "time": ["2022-01-01", "2022-01-02", "2022-01-03"],
        }
    )

    result = evaluate_threshold_grid(frame, thresholds=[0.3, 0.6])

    assert list(result["threshold"]) == [0.3, 0.6]
    assert list(result["n_trades"]) == [1, 2]
    assert list(result["pf"]) == [float("inf"), 1.0]
