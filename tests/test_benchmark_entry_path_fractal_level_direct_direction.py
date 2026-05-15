import pandas as pd

from ML.benchmark_entry_path_fractal_level_direct_direction import pick_validation_winner


def test_pick_winner_rejects_old_score_and_tiny_trade_count():
    grid = pd.DataFrame(
        [
            {
                "config": "old_score",
                "mode": "old_score_diagnostic",
                "validation_pf": 3.0,
                "validation_trades": 500,
                "validation_sequential_pf": 2.0,
                "overfitting_risk": False,
            },
            {
                "config": "tiny",
                "mode": "standalone",
                "validation_pf": 4.0,
                "validation_trades": 12,
                "validation_sequential_pf": 2.0,
                "overfitting_risk": False,
            },
            {
                "config": "weak",
                "mode": "standalone",
                "validation_pf": 1.05,
                "validation_trades": 500,
                "validation_sequential_pf": 1.2,
                "overfitting_risk": False,
            },
            {
                "config": "stable",
                "mode": "standalone",
                "validation_pf": 1.4,
                "validation_trades": 500,
                "validation_sequential_pf": 1.2,
                "negative_years": 1,
                "overfitting_risk": False,
            },
        ]
    )

    assert pick_validation_winner(grid)["config"] == "stable"
