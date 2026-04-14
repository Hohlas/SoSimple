import math

import pandas as pd
import pytest

from ML.benchmark_quantile_early_timeout import (
    build_yearly_breakdown,
    compute_metrics,
    decide_hold12_gate,
    evaluate_split,
    select_quantile_trades,
)


def test_compute_metrics_counts_pf_from_named_pnl_column():
    frame = pd.DataFrame({"pnl_atr": [2.0, -1.0, 3.0, 0.0]})

    result = compute_metrics(frame, pnl_column="pnl_atr")

    assert result["n_trades"] == 4
    assert result["wins"] == 2
    assert result["losses"] == 1
    assert result["gross_profit"] == 5.0
    assert result["gross_loss"] == 1.0
    assert result["pf"] == 5.0
    assert result["win_rate"] == 0.5
    assert result["mean_pnl_atr"] == 1.0


def test_compute_metrics_returns_inf_pf_without_losses():
    frame = pd.DataFrame({"pnl_atr": [1.0, 2.0]})

    result = compute_metrics(frame, pnl_column="pnl_atr")

    assert result["pf"] == math.inf
    assert result["losses"] == 0


@pytest.mark.parametrize("pnl_value", [pd.NA, float("nan")])
def test_compute_metrics_rejects_null_or_nan_pnl_values(pnl_value):
    frame = pd.DataFrame({"pnl_atr": [1.0, pnl_value, 2.0]})

    with pytest.raises(ValueError, match=r"pnl_atr contains null/NaN pnl values"):
        compute_metrics(frame, pnl_column="pnl_atr")


def test_decide_hold12_gate_passes_when_hold12_is_stable():
    result = decide_hold12_gate(
        hold24_pf=8.0,
        hold12_pf=10.0,
        hold12_n_trades=48,
        hold12_negative_year_slices=0,
        seed_pf_values=[9.0, 8.0, 7.5, 11.0, 6.0],
    )

    assert result == {"verdict": "gate_pass", "reasons": []}


def test_decide_hold12_gate_rejects_pf_collapse():
    result = decide_hold12_gate(
        hold24_pf=8.0,
        hold12_pf=0.9,
        hold12_n_trades=48,
        hold12_negative_year_slices=0,
        seed_pf_values=[9.0, 8.0, 7.5, 11.0, 6.0],
    )

    assert result["verdict"] == "gate_fail"
    assert "hold12_pf=0.9000 <= 2.0" in result["reasons"]


def test_select_quantile_trades_uses_baseline_and_lb_rule():
    frame = pd.DataFrame(
        {
            "time": ["2023.01.01 00:00", "2023.01.01 01:00", "2023.01.01 02:00"],
            "signal": [1, 1, 1],
            "pred_ret_24_q10": [-1.0, -5.0, -1.0],
            "pred_ret_24_q90": [3.0, 1.0, 3.0],
            "true_ret_12_dir_atr": [1.0, 2.0, 3.0],
            "true_ret_24_dir_atr": [1.5, 2.5, 3.5],
        }
    )
    baseline_frame = pd.DataFrame(
        {
            "time": ["2023.01.01 00:00", "2023.01.01 01:00", "2023.01.01 02:00"],
            "signal": [1, 1, 1],
            "pred_ret_24_dir_atr": [0.5, 0.5, -0.5],
        }
    )
    selected_rule = {
        "baseline_threshold": 0.0,
        "winner": {
            "rule": "lb_gt_m",
            "m": -3.0,
            "w": 10.0,
            "correction": 1.0,
        },
    }

    result = select_quantile_trades(frame, baseline_frame, selected_rule)

    assert list(result["time"]) == ["2023.01.01 00:00"]
    assert list(result["pnl_hold12_atr"]) == [1.0]
    assert list(result["pnl_hold24_atr"]) == [1.5]


def test_build_yearly_breakdown_ignores_small_years_for_negative_count():
    frame = pd.DataFrame(
        {
            "time": [
                "2023.01.01 00:00",
                "2023.02.01 00:00",
                "2023.03.01 00:00",
                "2024.01.01 00:00",
            ],
            "pnl_hold12_atr": [-1.0, -2.0, 1.0, -10.0],
            "pnl_hold24_atr": [1.0, 1.0, 1.0, -10.0],
        }
    )

    table, negative_years = build_yearly_breakdown(frame, min_year_trades=3)

    assert negative_years == 1
    assert list(table["year"]) == [2023, 2024]
    assert list(table["n_trades_hold12"]) == [3, 1]


def test_evaluate_split_compares_hold12_and_hold24():
    frame = pd.DataFrame(
        {
            "time": ["2023.01.01 00:00", "2023.02.01 00:00", "2023.03.01 00:00"],
            "pnl_hold12_atr": [2.0, -1.0, 3.0],
            "pnl_hold24_atr": [1.0, -1.0, 1.0],
        }
    )

    result = evaluate_split(frame, split="validation")

    assert result["split"] == "validation"
    assert result["hold12"]["pf"] == 5.0
    assert result["hold24"]["pf"] == 2.0
    assert result["negative_year_slices_hold12"] == 0


@pytest.mark.parametrize(
    "kwargs, expected_reason",
    [
        (
            dict(
                hold24_pf=8.0,
                hold12_pf=float("nan"),
                hold12_n_trades=48,
                hold12_negative_year_slices=0,
                seed_pf_values=[9.0, 8.0, 7.5],
            ),
            "hold12_pf=nan is invalid",
        ),
        (
            dict(
                hold24_pf=float("nan"),
                hold12_pf=10.0,
                hold12_n_trades=48,
                hold12_negative_year_slices=0,
                seed_pf_values=[9.0, 8.0, 7.5],
            ),
            "hold24_pf=nan is invalid",
        ),
        (
            dict(
                hold24_pf=8.0,
                hold12_pf=10.0,
                hold12_n_trades=48,
                hold12_negative_year_slices=0,
                seed_pf_values=[9.0, float("nan"), 7.5],
            ),
            "seed_pf_values_contain_invalid_numeric_values: [nan]",
        ),
        (
            dict(
                hold24_pf=8.0,
                hold12_pf=10.0,
                hold24_mean_pnl_atr=1.25,
                hold12_mean_pnl_atr=float("nan"),
                mean_pnl_tolerance_atr=0.1,
                hold12_n_trades=48,
                hold12_negative_year_slices=0,
                seed_pf_values=[9.0, 8.0, 7.5],
            ),
            "hold12_mean_pnl_atr=nan is invalid",
        ),
        (
            dict(
                hold24_pf=8.0,
                hold12_pf=10.0,
                hold12_n_trades=48,
                hold12_negative_year_slices=0,
                seed_pf_values=[9.0, None, 7.5],
            ),
            "seed_pf_values_contain_invalid_numeric_values: [None]",
        ),
        (
            dict(
                hold24_pf=8.0,
                hold12_pf=10.0,
                mean_pnl_tolerance_atr=float("nan"),
                hold12_n_trades=48,
                hold12_negative_year_slices=0,
                seed_pf_values=[9.0, 8.0, 7.5],
            ),
            "mean_pnl_tolerance_atr=nan is invalid",
        ),
        (
            dict(
                hold24_pf=8.0,
                hold12_pf=10.0,
                hold12_n_trades=float("nan"),
                hold12_negative_year_slices=0,
                seed_pf_values=[9.0, 8.0, 7.5],
            ),
            "hold12_n_trades=nan is invalid",
        ),
        (
            dict(
                hold24_pf=8.0,
                hold12_pf=10.0,
                hold12_n_trades=48,
                hold12_negative_year_slices=float("nan"),
                seed_pf_values=[9.0, 8.0, 7.5],
            ),
            "hold12_negative_year_slices=nan is invalid",
        ),
        (
            dict(
                hold24_pf=8.0,
                hold12_pf=10.0,
                hold12_n_trades=30.5,
                hold12_negative_year_slices=0,
                seed_pf_values=[9.0, 8.0, 7.5],
            ),
            "hold12_n_trades=30.5 is invalid",
        ),
        (
            dict(
                hold24_pf=8.0,
                hold12_pf=10.0,
                hold12_n_trades=48,
                hold12_negative_year_slices=-1,
                seed_pf_values=[9.0, 8.0, 7.5],
            ),
            "hold12_negative_year_slices=-1 is invalid",
        ),
    ],
)
def test_decide_hold12_gate_rejects_invalid_numeric_values(kwargs, expected_reason):
    result = decide_hold12_gate(**kwargs)

    assert result["verdict"] == "gate_fail"
    assert expected_reason in result["reasons"]


@pytest.mark.parametrize(
    "kwargs, expected_reason",
    [
        (
            dict(
                hold24_pf=8.0,
                hold12_pf=10.0,
                hold12_n_trades=29,
                hold12_negative_year_slices=0,
                seed_pf_values=[9.0, 8.0, 7.5],
            ),
            "hold12_n_trades=29 < 30",
        ),
        (
            dict(
                hold24_pf=8.0,
                hold12_pf=7.9,
                hold12_n_trades=48,
                hold12_negative_year_slices=0,
                seed_pf_values=[9.0, 8.0, 7.5],
            ),
            "hold12_pf=7.9000 < hold24_pf=8.0000",
        ),
        (
            dict(
                hold24_pf=8.0,
                hold12_pf=10.0,
                hold12_n_trades=48,
                hold12_negative_year_slices=1,
                seed_pf_values=[9.0, 8.0, 7.5],
            ),
            "hold12_negative_year_slices=1 > 0",
        ),
        (
            dict(
                hold24_pf=8.0,
                hold12_pf=10.0,
                hold12_n_trades=48,
                hold12_negative_year_slices=0,
                seed_pf_values=[0.95, 8.0, 7.5],
            ),
            "seed_pf_values_contain_pf<=1.0: [0.95]",
        ),
        (
            dict(
                hold24_pf=8.0,
                hold12_pf=None,
                hold12_n_trades=48,
                hold12_negative_year_slices=0,
                seed_pf_values=[9.0, 8.0, 7.5],
            ),
            "hold12_pf=None <= 2.0",
        ),
        (
            dict(
                hold24_pf=8.0,
                hold12_pf=10.0,
                hold24_mean_pnl_atr=1.25,
                hold12_mean_pnl_atr=1.0,
                mean_pnl_tolerance_atr=0.1,
                hold12_n_trades=48,
                hold12_negative_year_slices=0,
                seed_pf_values=[9.0, 8.0, 7.5],
            ),
            "hold12_mean_pnl_atr=1.0000 < hold24_mean_pnl_atr=1.2500",
        ),
    ],
)
def test_decide_hold12_gate_rejects_expected_branches(kwargs, expected_reason):
    result = decide_hold12_gate(**kwargs)

    assert result["verdict"] == "gate_fail"
    assert expected_reason in result["reasons"]
