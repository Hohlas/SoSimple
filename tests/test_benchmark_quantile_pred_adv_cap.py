import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ML.benchmark_quantile_pred_adv_cap import (
    compute_adv_threshold,
    decide_adv_cap_gate,
    filter_by_adv_cap,
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
