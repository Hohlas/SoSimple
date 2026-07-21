import pandas as pd
import pytest

import ML.baseline.benchmark_fractal0_entry_quality_filter as runner


def test_entry_filter_grid_contains_baseline_movement_and_entry_quality_filters():
    ids = [item["filter_id"] for item in runner.entry_filter_grid()]
    assert ids == [
        "M0_no_mask",
        "movement_top50",
        "movement_top30",
        "movement_top20",
        "movement_top10",
        "simple_stop_distance_top50",
        "simple_stop_distance_top30",
        "simple_r_value_top50",
        "simple_r_value_top30",
        "entry_quality_top50",
        "entry_quality_top30",
        "entry_quality_top20",
        "entry_quality_top10",
        "entry_avoid_sl_top50",
        "entry_avoid_sl_top30",
        "entry_avoid_sl_top20",
        "entry_avoid_sl_top10",
    ]


def test_select_top_fraction_keeps_highest_scores_and_cutoff():
    rows = pd.DataFrame({"score": [0.1, 0.9, 0.5, 0.7], "id": [1, 2, 3, 4]})
    selected = runner.select_top_fraction(rows, "score", 0.5)
    assert selected["id"].tolist() == [2, 4]
    assert runner.score_cutoff_for_top_fraction(rows, "score", 0.5) == 0.7


def test_top_fraction_ignores_missing_scores_for_cutoff():
    rows = pd.DataFrame({"score": [0.9, 0.7, 0.5, pd.NA, pd.NA], "id": [1, 2, 3, 4, 5]})
    top50 = runner.select_top_fraction(rows, "score", 0.5)
    top30 = runner.select_top_fraction(rows, "score", 0.3)
    assert top50["id"].tolist() == [1, 2]
    assert top30["id"].tolist() == [1]
    assert len(top50) >= len(top30)


def test_build_entry_labels_distinguishes_good_from_avoid_sl():
    trades = pd.DataFrame(
        [
            {"position_id": "a", "pnl_r": -1.0, "close_reason": "SL"},
            {"position_id": "b", "pnl_r": -0.2, "close_reason": "ML_CLOSE"},
            {"position_id": "c", "pnl_r": 0.4, "close_reason": "ML_CLOSE"},
        ]
    )
    labels = runner.build_entry_labels(trades).set_index("position_id")
    assert labels.loc["a", "target_entry_good"] == 0
    assert labels.loc["a", "target_entry_avoid_sl"] == 0
    assert labels.loc["b", "target_entry_good"] == 0
    assert labels.loc["b", "target_entry_avoid_sl"] == 1
    assert labels.loc["c", "target_entry_good"] == 1
    assert labels.loc["c", "target_entry_avoid_sl"] == 1


def test_entry_features_exclude_future_and_target_columns():
    assert not any(col.startswith(("future_", "target_", "pnl_")) for col in runner.ENTRY_FEATURE_COLUMNS)
    assert {"close_reason", "hold_bars", "exit_time"}.isdisjoint(runner.ENTRY_FEATURE_COLUMNS)


def test_build_entry_feature_frame_adds_direction_and_distance_features():
    entries = pd.DataFrame(
        {
            "side": ["BUY", "SELL"],
            "ATR": [2.0, 2.0],
            "fractal0_price": [100.0, 100.0],
            "planned_entry_bid_equivalent": [101.0, 99.0],
            "planned_protective_stop_price": [97.0, 103.0],
            "planned_r_value": [4.0, 4.0],
        }
    )
    frame = runner.build_entry_feature_frame(entries)
    assert frame["side_buy"].tolist() == [1, 0]
    assert frame["entry_to_fractal0_atr"].tolist() == [0.5, -0.5]
    assert frame["r_value_atr"].tolist() == [2.0, 2.0]


def test_train_and_score_entry_models_adds_scores():
    rows = pd.DataFrame(
        {
            "side": ["BUY", "SELL", "BUY", "SELL"],
            "ATR": [2.0, 2.0, 3.0, 3.0],
            "fractal0_price": [100.0, 100.0, 100.0, 100.0],
            "planned_entry_bid_equivalent": [101.0, 99.0, 103.0, 97.0],
            "planned_protective_stop_price": [97.0, 103.0, 96.0, 104.0],
            "planned_r_value": [4.0, 4.0, 7.0, 7.0],
            "target_entry_good": [1, 0, 1, 0],
            "target_entry_avoid_sl": [1, 0, 1, 0],
        }
    )
    models = runner.train_entry_models(rows, threads=1, seeds=(1,), n_estimators=5)
    scored = runner.score_entry_models(models, rows)
    assert "entry_quality_score" in scored
    assert "entry_avoid_sl_score" in scored


def test_apply_entry_filter_no_mask_and_top_fraction():
    rows = pd.DataFrame({"position_id": ["a", "b", "c"], "entry_quality_score": [0.2, 0.9, 0.6]})
    no_mask = runner.apply_entry_filter(rows, {"filter_id": "M0_no_mask", "family": "none", "top_fraction": 1.0, "score_col": None})
    top = runner.apply_entry_filter(
        rows,
        {"filter_id": "entry_quality_top50", "family": "entry_quality", "top_fraction": 0.5, "score_col": "entry_quality_score"},
        mode="select",
    )
    assert no_mask["position_id"].tolist() == ["a", "b", "c"]
    assert top["position_id"].tolist() == ["b", "c"]
    assert top.attrs["score_cutoff_on_val_select"] == 0.6


def test_apply_entry_filter_uses_val_select_cutoff_on_val_eval():
    val_eval = pd.DataFrame({"position_id": ["a", "b", "c"], "entry_quality_score": [0.95, 0.61, 0.59]})
    selected = runner.apply_entry_filter(
        val_eval,
        {"filter_id": "entry_quality_top50", "family": "entry_quality", "top_fraction": 0.5, "score_col": "entry_quality_score"},
        mode="eval",
        score_cutoff=0.60,
    )
    assert selected["position_id"].tolist() == ["a", "b"]


def test_apply_entry_filter_requires_cutoff_on_val_eval():
    with pytest.raises(ValueError, match="score_cutoff"):
        runner.apply_entry_filter(
            pd.DataFrame({"entry_quality_score": [0.5]}),
            {"filter_id": "entry_quality_top50", "family": "entry_quality", "top_fraction": 0.5, "score_col": "entry_quality_score"},
            mode="eval",
        )


def test_summary_for_filter_handles_empty_trades():
    run = {
        "stop_policy_id": "S2_fractal0_buffer_0_5_entry_floor_2",
        "entry_id": "E3_open_pullback_1_0atr",
        "mask_id": "M0_no_mask",
        "exit_id": "X2_ml_opposite_any_p0_50",
        "filter_id": "entry_quality_top10",
        "filter_family": "entry_quality",
        "top_fraction": 0.10,
        "available_trades_before_filter": 10,
    }
    summary = runner._summary_for_filter(pd.DataFrame(), run, "val_eval")
    assert summary["n_trades"] == 0
    assert summary["filter_id"] == "entry_quality_top10"
