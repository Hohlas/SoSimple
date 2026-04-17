import pandas as pd
import pytest

from ML.benchmark_trailing_stop_target import pick_validation_winner, summarize_candidate


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


def test_summarize_candidate_uses_explicit_true_column():
    frame = pd.DataFrame(
        [
            {"score": 0.90, "true_trail_48_pnl_atr_x5": 2.0},
            {"score": 0.80, "true_trail_48_pnl_atr_x5": -1.0},
            {"score": 0.70, "true_trail_48_pnl_atr_x5": 3.0},
        ]
    )

    result = summarize_candidate(frame, score_col="score", threshold=0.80, true_pnl_col="true_trail_48_pnl_atr_x5")

    assert result["candidate"] == "score"
    assert result["trades"] == 2
    assert result["gross_profit"] == pytest.approx(2.0)
    assert result["gross_loss"] == pytest.approx(1.0)
    assert result["pf"] == pytest.approx(2.0)


def test_summarize_candidate_returns_empty_defaults_for_no_trades():
    frame = pd.DataFrame(
        [
            {"score": 0.10, "true_trail_48_pnl_atr_x2": 2.0},
            {"score": 0.20, "true_trail_48_pnl_atr_x2": -1.0},
        ]
    )

    result = summarize_candidate(frame, score_col="score", threshold=0.80, true_pnl_col="true_trail_48_pnl_atr_x2")

    assert result["trades"] == 0
    assert result["gross_profit"] == pytest.approx(0.0)
    assert result["gross_loss"] == pytest.approx(0.0)
    assert result["pf"] == pytest.approx(0.0)
    assert result["ulcer_index_atr"] == pytest.approx(0.0)


def test_pick_validation_winner_returns_none_when_no_candidate_meets_min_pf():
    frame = pd.DataFrame(
        [
            {"candidate": "a", "pf": 0.90, "ulcer_index_atr": 20.0, "trades": 140},
            {"candidate": "b", "pf": 0.95, "ulcer_index_atr": 10.0, "trades": 140},
        ]
    )

    winner = pick_validation_winner(frame, min_pf=1.0)

    assert winner is None
