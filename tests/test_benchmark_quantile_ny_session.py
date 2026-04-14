import math
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ML.benchmark_quantile_ny_session import (
    assign_session_bucket,
    count_negative_year_slices,
    decide_session_gate,
    evaluate_split,
    filter_session_trades,
    select_quantile_trades,
)


def test_assign_session_bucket_maps_known_hours():
    assert assign_session_bucket(2) == "asia"
    assert assign_session_bucket(6) == "asia"
    assert assign_session_bucket(7) == "london"
    assert assign_session_bucket(9) == "london"
    assert assign_session_bucket(12) == "london"
    assert assign_session_bucket(13) == "overlap"
    assert assign_session_bucket(15) == "overlap"
    assert assign_session_bucket(18) == "overlap"
    assert assign_session_bucket(19) == "ny"
    assert assign_session_bucket(21) == "ny"


def test_assign_session_bucket_rejects_invalid_hours():
    with pytest.raises(ValueError, match=r"hour must be in \[0, 23\], got -1"):
        assign_session_bucket(-1)

    with pytest.raises(ValueError, match=r"hour must be in \[0, 23\], got 24"):
        assign_session_bucket(24)


def test_count_negative_year_slices_ignores_tiny_years():
    frame = pd.DataFrame(
        [
            {"year": 2023, "pnl_atr": -1.0},
            {"year": 2023, "pnl_atr": 3.0},
            {"year": 2024, "pnl_atr": -2.0},
            {"year": 2024, "pnl_atr": -1.0},
            {"year": 2025, "pnl_atr": -1.0},
            {"year": 2025, "pnl_atr": 2.0},
            {"year": 2025, "pnl_atr": 2.0},
        ]
    )

    assert count_negative_year_slices(frame, pnl_column="pnl_atr") == 0


def test_evaluate_split_does_not_count_all_zero_year_as_negative():
    frame = pd.DataFrame(
        [
            {"time": "2025.01.01 02:00", "pnl_atr": 0.0},
            {"time": "2025.01.02 02:00", "pnl_atr": 0.0},
            {"time": "2025.01.03 02:00", "pnl_atr": 0.0},
        ]
    )

    result = evaluate_split(frame, split="validation", pnl_column="pnl_atr")

    assert result["pf"] is None
    assert result["negative_year_slices"] == 0
    assert result["yearly"][0]["pf"] is None


def test_select_quantile_trades_assigns_sessions_then_filters_non_ny():
    quantile_frame = pd.DataFrame(
        {
            "time": [
                "2025.01.01 02:00",
                "2025.01.01 15:00",
                "2025.01.01 21:00",
            ],
            "signal": [1, -1, 1],
            "pred_ret_24_q10": [0.5, 1.0, 0.5],
            "pred_ret_24_q90": [2.0, 3.0, 2.0],
            "true_ret_12_dir_atr": [1.5, 2.5, -1.0],
            "true_ret_24_dir_atr": [2.0, 3.0, -2.0],
        }
    )
    baseline_frame = pd.DataFrame(
        {
            "time": [
                "2025.01.01 02:00",
                "2025.01.01 15:00",
                "2025.01.01 21:00",
            ],
            "signal": [1, -1, 1],
            "pred_ret_24_dir_atr": [0.5, 0.5, 0.5],
        }
    )
    rule_payload = {
        "baseline_threshold": 0.0,
        "winner": {
            "rule": "lb_gt_m",
            "m": 0.0,
            "w": 10.0,
            "correction": 0.0,
        },
    }

    selected = select_quantile_trades(
        frame=quantile_frame,
        baseline_frame=baseline_frame,
        selected_rule=rule_payload,
    )

    filtered = filter_session_trades(selected)

    assert selected["session"].tolist() == ["asia", "overlap", "ny"]
    assert filtered["session"].tolist() == ["asia", "overlap"]
    assert filtered["time"].tolist() == ["2025.01.01 02:00", "2025.01.01 15:00"]
    assert filtered["year"].tolist() == [2025, 2025]
    assert filtered["pnl_hold24_atr"].tolist() == [2.0, 3.0]


def test_filter_session_trades_rejects_unknown_session_values():
    frame = pd.DataFrame({"session": ["asia", "broken"]})

    with pytest.raises(ValueError, match=r"unknown session values: \['broken'\]"):
        filter_session_trades(frame)


def test_select_quantile_trades_rejects_misaligned_baseline_frame():
    quantile_frame = pd.DataFrame(
        {
            "time": ["2025.01.01 02:00", "2025.01.01 15:00"],
            "signal": [1, -1],
            "pred_ret_24_q10": [0.5, 1.0],
            "pred_ret_24_q90": [2.0, 3.0],
            "true_ret_12_dir_atr": [1.5, 2.5],
            "true_ret_24_dir_atr": [2.0, 3.0],
        }
    )
    baseline_frame = pd.DataFrame(
        {
            "time": ["2025.01.01 02:00"],
            "signal": [1],
            "pred_ret_24_dir_atr": [0.5],
        }
    )
    rule_payload = {
        "baseline_threshold": 0.0,
        "winner": {"rule": "lb_gt_m", "m": 0.0, "w": 10.0, "correction": 0.0},
    }

    with pytest.raises(ValueError, match=r"baseline_frame does not align one-to-one"):
        select_quantile_trades(
            frame=quantile_frame,
            baseline_frame=baseline_frame,
            selected_rule=rule_payload,
        )


def test_select_quantile_trades_rejects_unparsable_timestamps():
    quantile_frame = pd.DataFrame(
        {
            "time": ["2025.01.01 02:00", "bad-time"],
            "signal": [1, -1],
            "pred_ret_24_q10": [0.5, 1.0],
            "pred_ret_24_q90": [2.0, 3.0],
            "true_ret_12_dir_atr": [1.5, 2.5],
            "true_ret_24_dir_atr": [2.0, 3.0],
        }
    )
    baseline_frame = pd.DataFrame(
        {
            "time": ["2025.01.01 02:00", "2025.01.01 15:00"],
            "signal": [1, -1],
            "pred_ret_24_dir_atr": [0.5, 0.5],
        }
    )
    rule_payload = {
        "baseline_threshold": 0.0,
        "winner": {
            "rule": "lb_gt_m",
            "m": 0.0,
            "w": 10.0,
            "correction": 0.0,
        },
    }

    with pytest.raises(ValueError, match=r"time contains unparsable timestamps"):
        select_quantile_trades(
            frame=quantile_frame,
            baseline_frame=baseline_frame,
            selected_rule=rule_payload,
        )


def test_decide_session_gate_rejects_support_and_seed_collapse():
    result = decide_session_gate(
        baseline_pf=8.0,
        filtered_pf=20.0,
        filtered_n_trades=29,
        filtered_negative_year_slices=0,
        seed_pf_values=[2.0, 3.0, 0.9],
    )

    assert result["verdict"] == "gate_fail"
    assert "filtered_n_trades=29 < 30" in result["reasons"]
    assert "seed_pf_values_contain_pf<=1.0: [0.9]" in result["reasons"]


def test_decide_session_gate_rejects_non_finite_pf_values():
    result = decide_session_gate(
        baseline_pf=None,
        filtered_pf=None,
        filtered_n_trades=30,
        filtered_negative_year_slices=0,
        seed_pf_values=[2.0, math.nan, None],
    )

    assert result["verdict"] == "gate_fail"
    assert "baseline_pf=None" in result["reasons"]
    assert "filtered_pf=None" in result["reasons"]
    assert "filtered_pf=None <= 2.0" in result["reasons"]
    assert any(reason.startswith("seed_pf_values_contain_non_finite: [nan, None]") for reason in result["reasons"])
