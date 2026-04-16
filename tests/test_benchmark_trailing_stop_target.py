import pandas as pd

from ML.benchmark_trailing_stop_target import pick_validation_winner


def test_pick_validation_winner_prefers_pf_then_lower_ulcer():
    frame = pd.DataFrame(
        [
            {"candidate": "a", "pf": 1.10, "ulcer_index_atr": 50.0, "trades": 120},
            {"candidate": "b", "pf": 1.10, "ulcer_index_atr": 40.0, "trades": 120},
            {"candidate": "c", "pf": 0.95, "ulcer_index_atr": 10.0, "trades": 120},
        ]
    )

    winner = pick_validation_winner(frame)

    assert winner["candidate"] == "b"


def test_pick_validation_winner_ignores_sub_pf_one_rows_when_any_pf_one_exists():
    frame = pd.DataFrame(
        [
            {"candidate": "a", "pf": 0.90, "ulcer_index_atr": 20.0, "trades": 140},
            {"candidate": "b", "pf": 1.05, "ulcer_index_atr": 80.0, "trades": 140},
        ]
    )
    winner = pick_validation_winner(frame)
    assert winner["candidate"] == "b"
