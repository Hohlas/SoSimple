import pandas as pd
import pytest

from ML.benchmark_quantile_forward_validation import (
    build_time_slices,
    compute_forward_metrics,
    decide_operational_verdict,
)


def test_compute_forward_metrics_counts_pf_and_trades():
    frame = pd.DataFrame(
        {
            "true_ret_24_dir_atr": [2.0, -1.0, 3.0],
        }
    )

    result = compute_forward_metrics(frame)

    assert result["n_trades"] == 3
    assert result["gross_profit"] == 5.0
    assert result["gross_loss"] == 1.0
    assert result["pf"] == 5.0


def test_compute_forward_metrics_returns_empty_defaults_for_no_trades():
    result = compute_forward_metrics(pd.DataFrame({"true_ret_24_dir_atr": []}))

    assert result == {
        "n_trades": 0,
        "wins": 0,
        "losses": 0,
        "gross_profit": 0.0,
        "gross_loss": 0.0,
        "pf": None,
        "win_rate": None,
        "mean_pnl_atr": None,
    }


def test_compute_forward_metrics_returns_infinite_pf_without_losses():
    frame = pd.DataFrame({"true_ret_24_dir_atr": [0.5, 1.0, 2.0]})

    result = compute_forward_metrics(frame)

    assert result["wins"] == 3
    assert result["losses"] == 0
    assert result["gross_profit"] == 3.5
    assert result["gross_loss"] == 0.0
    assert result["pf"] == float("inf")


def test_compute_forward_metrics_returns_zero_pf_without_wins():
    frame = pd.DataFrame({"true_ret_24_dir_atr": [-0.5, -1.0, 0.0]})

    result = compute_forward_metrics(frame)

    assert result["wins"] == 0
    assert result["losses"] == 2
    assert result["gross_profit"] == 0.0
    assert result["gross_loss"] == 1.5
    assert result["pf"] == 0.0


def test_build_time_slices_groups_rows_by_quarter():
    frame = pd.DataFrame(
        {
            "time": ["2026-01-10", "2026-02-10", "2026-05-10"],
            "true_ret_24_dir_atr": [1.0, -1.0, 2.0],
        }
    )

    result = build_time_slices(frame, mode="quarter")

    assert list(result["slice"]) == ["2026-Q1", "2026-Q2"]
    assert list(result["n_trades"]) == [2, 1]
    assert list(result["gross_profit"]) == [1.0, 2.0]
    assert list(result["gross_loss"]) == [1.0, 0.0]
    assert list(result["pf"]) == [1.0, float("inf")]


def test_build_time_slices_returns_expected_schema_for_empty_frame():
    frame = pd.DataFrame({"time": [], "true_ret_24_dir_atr": []})

    result = build_time_slices(frame, mode="quarter")

    assert result.empty
    assert list(result.columns) == [
        "slice",
        "n_trades",
        "wins",
        "losses",
        "gross_profit",
        "gross_loss",
        "pf",
        "win_rate",
        "mean_pnl_atr",
    ]


def test_build_time_slices_rejects_unsupported_mode():
    frame = pd.DataFrame({"time": ["2026-01-10"], "true_ret_24_dir_atr": [1.0]})

    with pytest.raises(ValueError, match="unsupported slice mode: month"):
        build_time_slices(frame, mode="month")


def test_decide_operational_verdict_returns_watch_for_missing_forward_pf():
    result = decide_operational_verdict(
        historical_pf=8.18,
        forward_pf=None,
        n_trades=18,
        negative_slices=0,
    )

    assert result == {"verdict": "watch", "reason": "low_support"}


def test_decide_operational_verdict_returns_watch_for_low_trade_count():
    result = decide_operational_verdict(
        historical_pf=8.18,
        forward_pf=7.0,
        n_trades=9,
        negative_slices=0,
    )

    assert result == {"verdict": "watch", "reason": "low_support"}


def test_decide_operational_verdict_returns_revisit_for_pf_below_one():
    result = decide_operational_verdict(
        historical_pf=8.18,
        forward_pf=0.9,
        n_trades=18,
        negative_slices=0,
    )

    assert result == {"verdict": "revisit", "reason": "pf_below_1"}


def test_decide_operational_verdict_prefers_pf_drawdown_signal():
    result = decide_operational_verdict(
        historical_pf=8.18,
        forward_pf=3.5,
        n_trades=18,
        negative_slices=1,
    )

    assert result == {"verdict": "watch", "reason": "pf_drawdown"}


def test_decide_operational_verdict_returns_watch_for_many_weak_slices():
    result = decide_operational_verdict(
        historical_pf=8.18,
        forward_pf=5.0,
        n_trades=18,
        negative_slices=2,
    )

    assert result == {"verdict": "watch", "reason": "weak_time_slices"}


def test_decide_operational_verdict_returns_confirmed_when_pf_holds():
    result = decide_operational_verdict(
        historical_pf=8.18,
        forward_pf=5.0,
        n_trades=18,
        negative_slices=1,
    )

    assert result == {"verdict": "confirmed", "reason": "forward_pf_holds"}
