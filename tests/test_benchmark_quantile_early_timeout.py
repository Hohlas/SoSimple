from __future__ import annotations

import pandas as pd

from ML.benchmark_quantile_early_timeout import build_yearly_breakdown
from ML.benchmark_quantile_early_timeout import evaluate_split


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
