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
        baseline_pf=math.inf,
        filtered_pf=math.nan,
        filtered_n_trades=30,
        filtered_negative_year_slices=0,
        seed_pf_values=[2.0, math.nan],
    )

    assert result["verdict"] == "gate_fail"
    assert "baseline_pf=inf is not finite" in result["reasons"]
    assert any(reason.startswith("filtered_pf=nan is not finite") for reason in result["reasons"])
    assert any(reason.startswith("seed_pf_values_contain_non_finite: [nan]") for reason in result["reasons"])
