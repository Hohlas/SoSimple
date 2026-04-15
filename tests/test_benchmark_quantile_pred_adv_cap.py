import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ML.benchmark_quantile_ny_session import select_quantile_trades as upstream_select_quantile_trades
from ML.benchmark_quantile_pred_adv_cap import (
    compute_adv_threshold,
    evaluate_split,
    decide_adv_cap_gate,
    filter_by_adv_cap,
    build_validation_first_adv_cap,
    select_frozen_quantile_trades,
)


def test_compute_adv_threshold_uses_validation_q75():
    frame = pd.DataFrame({"pred_adv_12_atr": [0.01, 0.02, 0.03, 0.04]})

    assert compute_adv_threshold(frame, quantile=0.75) == 0.0325


def test_compute_adv_threshold_requires_pred_adv_12_atr():
    frame = pd.DataFrame({"other": [0.01, 0.02]})

    with pytest.raises(ValueError, match=r"missing columns: \['pred_adv_12_atr'\]"):
        compute_adv_threshold(frame, quantile=0.75)


@pytest.mark.parametrize("bad_value", [None, float("nan"), float("inf"), float("-inf")])
def test_compute_adv_threshold_rejects_non_finite_pred_adv_values(bad_value):
    frame = pd.DataFrame({"pred_adv_12_atr": [0.01, bad_value, 0.03]})

    with pytest.raises(ValueError, match=r"pred_adv_12_atr contains null/NaN/non-finite values"):
        compute_adv_threshold(frame, quantile=0.75)


def test_filter_by_adv_cap_keeps_values_at_threshold():
    frame = pd.DataFrame({"pred_adv_12_atr": [0.01, 0.03, 0.04]})

    out = filter_by_adv_cap(frame, threshold=0.03)

    assert out["pred_adv_12_atr"].tolist() == [0.01, 0.03]


def test_filter_by_adv_cap_requires_pred_adv_12_atr():
    frame = pd.DataFrame({"other": [0.01, 0.03, 0.04]})

    with pytest.raises(ValueError, match=r"missing columns: \['pred_adv_12_atr'\]"):
        filter_by_adv_cap(frame, threshold=0.03)


@pytest.mark.parametrize("bad_threshold", [None, float("nan"), float("inf"), float("-inf")])
def test_filter_by_adv_cap_rejects_non_finite_threshold(bad_threshold):
    frame = pd.DataFrame({"pred_adv_12_atr": [0.01, 0.03, 0.04]})

    with pytest.raises(ValueError, match=r"threshold must be a finite number"):
        filter_by_adv_cap(frame, threshold=bad_threshold)


def test_decide_adv_cap_gate_rejects_support_and_seed_collapse():
    result = decide_adv_cap_gate(
        baseline_pf=8.0,
        filtered_pf=12.0,
        filtered_n_trades=29,
        filtered_negative_year_slices=0,
        seed_pf_values=[2.0, 0.9],
    )

    assert result["verdict"] == "gate_fail"
    assert "filtered_n_trades=29 < 30" in result["reasons"]
    assert "seed_pf_values_contain_pf<=1.0: [0.9]" in result["reasons"]


@pytest.mark.parametrize(
    "kwargs, expected_reason",
    [
        (
            dict(
                baseline_pf=None,
                filtered_pf=12.0,
                filtered_n_trades=30,
                filtered_negative_year_slices=0,
                seed_pf_values=[2.0, 2.5],
            ),
            "baseline_pf=None",
        ),
        (
            dict(
                baseline_pf=8.0,
                filtered_pf=float("nan"),
                filtered_n_trades=30,
                filtered_negative_year_slices=0,
                seed_pf_values=[2.0, 2.5],
            ),
            "filtered_pf=nan is not finite",
        ),
        (
            dict(
                baseline_pf=8.0,
                filtered_pf=12.0,
                filtered_n_trades=float("nan"),
                filtered_negative_year_slices=0,
                seed_pf_values=[2.0, 2.5],
            ),
            "filtered_n_trades=nan is not finite",
        ),
        (
            dict(
                baseline_pf=8.0,
                filtered_pf=12.0,
                filtered_n_trades=30,
                filtered_negative_year_slices=float("nan"),
                seed_pf_values=[2.0, 2.5],
            ),
            "filtered_negative_year_slices=nan is not finite",
        ),
        (
            dict(
                baseline_pf=8.0,
                filtered_pf=12.0,
                filtered_n_trades=30,
                filtered_negative_year_slices=0,
                seed_pf_values=[2.0, float("inf"), 2.5],
            ),
            "seed_pf_values_contain_non_finite: [inf]",
        ),
    ],
)
def test_decide_adv_cap_gate_rejects_invalid_numeric_values(kwargs, expected_reason):
    result = decide_adv_cap_gate(**kwargs)

    assert result["verdict"] == "gate_fail"
    assert expected_reason in result["reasons"]


def _make_quantile_frame(pred_adv_values, signals=None, years=None):
    signals = signals or [1, 1, 0, 1]
    years = years or [2023, 2023, 2023, 2024]
    rows = []
    for idx, (pred_adv, signal, year) in enumerate(zip(pred_adv_values, signals, years, strict=True), start=1):
        rows.append(
            {
                "time": f"{year}.01.0{idx} 0{idx}:00",
                "signal": signal,
                "pred_ret_24_q10": 1.0,
                "pred_ret_24_q90": 2.0,
                "true_ret_12_dir_atr": 0.5 * idx,
                "true_ret_24_dir_atr": 1.0 * idx,
                "pred_adv_12_atr": pred_adv,
            }
        )
    frame = pd.DataFrame(rows)
    baseline = pd.DataFrame(
        {
            "time": frame["time"],
            "signal": frame["signal"],
            "pred_ret_24_dir_atr": [0.6, 0.7, 0.8, 0.9],
        }
    )
    return frame, baseline


def _selected_rule():
    return {
        "baseline_threshold": 0.5,
        "winner": {
            "rule": "baseline",
            "correction": 0.0,
            "m": 0.0,
            "w": 0.0,
        },
    }


def test_select_frozen_quantile_trades_matches_upstream_selection_and_preserves_pred_adv():
    frame, baseline = _make_quantile_frame([0.10, 0.20, 0.90, 0.30])
    selected_rule = _selected_rule()

    upstream = upstream_select_quantile_trades(
        frame=frame,
        baseline_frame=baseline,
        selected_rule=selected_rule,
    )
    out = select_frozen_quantile_trades(
        frame=frame,
        baseline_frame=baseline,
        selected_rule=selected_rule,
    )

    pd.testing.assert_frame_equal(out, upstream)
    assert out["pred_adv_12_atr"].tolist() == [0.10, 0.20, 0.30]


def test_validation_threshold_comes_from_selected_validation_rows_only_and_caps_inclusively():
    validation_frame, validation_baseline = _make_quantile_frame(
        [0.10, 0.20, 0.30, 0.99],
        signals=[1, 1, 1, 0],
    )
    test_frame, test_baseline = _make_quantile_frame(
        [0.05, 0.25, 0.40, 0.80],
        signals=[1, 1, 1, 0],
    )
    selected_rule = _selected_rule()

    result = build_validation_first_adv_cap(
        validation_frame=validation_frame,
        validation_baseline_frame=validation_baseline,
        test_frame=test_frame,
        test_baseline_frame=test_baseline,
        selected_rule=selected_rule,
        quantile=0.75,
    )

    assert result["validation_threshold"] == pytest.approx(0.25)
    assert result["validation_selected"]["pred_adv_12_atr"].tolist() == [0.10, 0.20, 0.30]
    assert result["validation_filtered"]["pred_adv_12_atr"].tolist() == [0.10, 0.20]
    assert result["test_filtered"]["pred_adv_12_atr"].tolist() == [0.05, 0.25]
    assert result["test_summary"]["n_trades"] == 2


def test_evaluate_split_reports_yearly_metrics():
    frame = pd.DataFrame(
        {
            "time": [
                "2023.01.01 00:00",
                "2023.02.01 00:00",
                "2023.03.01 00:00",
                "2024.01.01 00:00",
                "2024.02.01 00:00",
                "2024.03.01 00:00",
            ],
            "pnl_hold24_atr": [1.0, -2.0, -1.0, 2.0, 1.0, -1.0],
        }
    )

    out = evaluate_split(frame, split="validation", pnl_column="pnl_hold24_atr")

    assert out["n_trades"] == 6
    assert out["wins"] == 3
    assert out["losses"] == 3
    assert out["gross_profit"] == 4.0
    assert out["gross_loss"] == 4.0
    assert out["pf"] == pytest.approx(1.0)
    assert out["win_rate"] == pytest.approx(0.5)
    assert out["mean_pnl_atr"] == pytest.approx(0.0)
    assert out["negative_year_slices"] == 1
    assert [row["year"] for row in out["yearly"]] == [2023, 2024]
    assert out["yearly"][0]["pf"] == pytest.approx(1 / 3)
    assert out["yearly"][1]["pf"] == pytest.approx(3.0)
