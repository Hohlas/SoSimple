import argparse
import json

import pandas as pd
import pytest

from ML.baseline import audit_leaderboard_robustness as leaderboard
import ML.baseline.benchmark_fractal0_entry_exit_grid as base
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


def test_rich_phase_a_search_budget_and_eligibility():
    profiles = runner.rich_feature_profile_grid()
    models = runner.rich_model_grid(include_diagnostic_models=True)
    targets = runner.rich_target_grid()
    filters = runner.rich_filter_grid()
    budget = runner.compute_search_budget(profiles, models, targets, filters)

    assert budget["n_profiles"] == 9
    assert budget["n_models"] == 3
    assert budget["n_targets"] == 3
    assert budget["n_primary_filters"] == 3
    assert budget["n_total_ranked_configs"] == 243

    diagnostic_profiles = {p["profile_id"] for p in profiles if not p["eligible_for_winner"]}
    diagnostic_models = {m["model_id"] for m in models if not m["eligible_for_winner"]}
    diagnostic_filters = {f["filter_id"] for f in filters if not f["eligible_for_winner"]}

    assert {"structure_nearest_k80", "structure_all100"}.issubset(diagnostic_profiles)
    assert {"xgboost_depth3", "xgboost_depth5", "lightgbm_small"}.issubset(diagnostic_models)
    assert {"top20", "top10"}.issubset(diagnostic_filters)
    assert budget["n_total_executed_configs_default"] == 243
    by_id = {m["model_id"]: m for m in models}
    assert all(
        by_id[model_id]["runnable_by_default"] is False
        for model_id in {"xgboost_depth3", "xgboost_depth5", "lightgbm_small"}
    )


def test_build_rich_entry_labels_keeps_no_fill_and_stronger_targets():
    planned = pd.DataFrame(
        [
            {"position_id": "a", "filled": True},
            {"position_id": "b", "filled": True},
            {"position_id": "c", "filled": False},
        ]
    )
    trades = pd.DataFrame(
        [
            {"position_id": "a", "pnl_r": 0.6, "close_reason": "ML_CLOSE"},
            {"position_id": "b", "pnl_r": -1.0, "close_reason": "SL"},
        ]
    )
    labels = runner.build_rich_entry_labels(planned, trades).set_index("position_id")
    assert bool(labels.loc["a", "order_filled"]) is True
    assert labels.loc["a", "target_entry_good_0_5r"] == 1
    assert labels.loc["a", "target_entry_avoid_sl"] == 1
    assert labels.loc["b", "target_entry_good_0_5r"] == 0
    assert labels.loc["b", "target_entry_avoid_sl"] == 0
    assert bool(labels.loc["c", "order_filled"]) is False
    assert labels.loc["c", "target_entry_filled"] == 0
    assert pd.isna(labels.loc["c", "target_entry_ev_regression"])


def test_planned_order_diagnostics_reports_fill_rate_and_expected_pnl():
    planned = pd.DataFrame({"position_id": ["a", "b", "c"], "filled": [True, True, False]})
    trades = pd.DataFrame({"position_id": ["a", "b"], "pnl_r": [0.5, -0.25]})
    diag = runner.planned_order_diagnostics(planned, trades, "val_select")
    assert diag["split"] == "val_select"
    assert diag["planned_orders"] == 3
    assert diag["filled_orders"] == 2
    assert diag["fill_rate"] == pytest.approx(2 / 3)
    assert diag["expected_pnl_per_filled_trade"] == pytest.approx(0.125)
    assert diag["expected_pnl_per_planned_order"] == pytest.approx(0.25 / 3)


def test_rich_feature_frame_uses_closed_h1_and_forbids_top_level_targets():
    entries = pd.DataFrame(
        {
            "time": pd.to_datetime(["2020-01-01 10:00:00"]),
            "side": ["BUY"],
            "ATR": [2.0],
            "fractal0_price": [100.0],
            "planned_entry_bid_equivalent": [101.0],
            "planned_protective_stop_price": [97.0],
            "planned_r_value": [4.0],
            "signal": [1],
            "predict": [0],
            "up_3": [999.0],
            "dn_3": [999.0],
            "ret_3": [999.0],
            "fav_3": [999.0],
            "adv_3": [999.0],
            "pnl_r": [999.0],
            "close_reason": ["SL"],
            "fill_lag": [3],
            "exit_time": pd.to_datetime(["2020-01-01 13:00:00"]),
            "target_leak": [1],
        }
    )
    ohlc = pd.DataFrame(
        {
            "time": pd.to_datetime(["2020-01-01 08:00:00", "2020-01-01 09:00:00"]),
            "open": [90.0, 95.0],
            "high": [98.0, 103.0],
            "low": [89.0, 94.0],
            "close": [96.0, 102.0],
        }
    )
    features, audit = runner.build_rich_feature_frame(entries, ohlc, "price_action_h1")
    forbidden = {"signal", "predict", "up_3", "dn_3", "ret_3", "fav_3", "adv_3", "pnl_r", "close_reason", "fill_lag", "exit_time", "target_leak"}
    assert forbidden.isdisjoint(features.columns)
    assert features.loc[0, "h1_close"] == 102.0
    assert all(item["live_safe"] for item in audit)


def test_build_fixed_leaderboard_job_list_returns_exact_11_rules():
    jobs = runner.build_fixed_leaderboard_job_list(
        runner.rich_feature_profile_grid(),
        runner.rich_model_grid(include_diagnostic_models=True),
        runner.rich_target_grid(),
        runner.rich_filter_grid(),
        leaderboard.LEADERBOARD_RULES,
    )

    rule_ids = [job[4]["rule_id"] for job in jobs]
    assert len(jobs) == 11
    assert rule_ids == [rule.rule_id for rule in leaderboard.LEADERBOARD_RULES]


def test_resolve_fixed_cutoff_prefers_saved_cutoff():
    selected_val = pd.DataFrame({"rich_entry_score": [0.5, 0.4]})
    selected_val.attrs["score_cutoff_on_val_select"] = 0.4

    result = runner.resolve_fixed_cutoff("rank01", {"rank01": -0.0267}, selected_val)

    assert result == -0.0267


def test_verify_fixed_output_contract_rejects_wrong_spread():
    rows = pd.DataFrame(
        {
            "rule_id": ["rank01_time_only_linear_target_entry_ev_regression_top30"],
            "original_rank": [1],
            "profile_id": ["time_only"],
            "model_id": ["linear"],
            "target_id": ["target_entry_ev_regression"],
            "filter_id": ["top30"],
            "stop_policy_id": ["S2_fractal0_buffer_0_5_entry_floor_2"],
            "entry_id": ["E3_open_pullback_1_0atr"],
            "mask_id": ["M0_no_mask"],
            "exit_id": ["X2_ml_opposite_any_p0_50"],
            "entry_filter_score_col": ["rich_entry_score"],
            "score_cutoff_on_val_select": [-0.026718184259660646],
            "rich_entry_seed": [42],
            "timezone_shift_hours": [0],
            "spread": [0.2],
            "locked_test": ["not_opened"],
            "fixed_cutoff_source": ["tmp_rules.csv"],
        }
    )

    with pytest.raises(ValueError, match="spread"):
        runner.verify_fixed_output_contract(
            rows,
            expected_spread=0.4,
            expected_seed=42,
            timezone_shift_hours=0,
            fixed_cutoff_source="tmp_rules.csv",
        )


def test_normalized_time_features_shift_without_mutating_input_times():
    entries = pd.DataFrame(
        {
            "time": pd.to_datetime(["2021-01-04 22:00:00"]),
            "side": ["BUY"],
            "ATR": [10.0],
            "planned_entry_bid_equivalent": [100.0],
            "planned_protective_stop_price": [99.0],
            "planned_r_value": [1.0],
            "entry_bid_equivalent": [100.0],
            "fractal0_price": [99.5],
        }
    )

    base_frame, _ = runner.build_normalized_rich_feature_frame(entries, pd.DataFrame(), "time_only", timezone_shift_hours=0)
    shifted_frame, _ = runner.build_normalized_rich_feature_frame(entries, pd.DataFrame(), "time_only", timezone_shift_hours=4)

    assert float(base_frame["session_hour_unit"].iloc[0]) == 22.0 / 23.0
    assert float(shifted_frame["session_hour_unit"].iloc[0]) == 2.0 / 23.0
    assert entries["time"].iloc[0] == pd.Timestamp("2021-01-04 22:00:00")


def test_spread_override_is_consistent_in_fixed_rerun_smoke(tmp_path):
    prefix = tmp_path / "fixed_spread_smoke"
    args = argparse.Namespace(
        threads=1,
        no_resume=True,
        output_prefix=str(prefix),
        execution_ohlc_path="MT/MQL4/Files/XAUUSD_M5_OHLC.csv",
        stop_policy_id="",
        stop_grid_artifact="ML/reports/fractal0_entry_exit_grid_stop_policy.json",
        permutation_repeats=0,
        smoke_limit_filters=1,
        smoke_first_rule_only=True,
        rich_entry_quality=True,
        include_diagnostic_models=True,
        normalized_rich_features=True,
        rich_entry_seed=42,
        fixed_leaderboard_rules_only=True,
        fixed_cutoffs_csv="ML/reports/leaderboard_closure_audit_rules.csv",
        spread=0.4,
        timezone_shift_hours=0,
    )

    runner.run_rich_entry_quality(args)

    summary = pd.read_csv(prefix.with_name(prefix.name + "_summary.csv"), sep=";")
    trades = pd.read_csv(prefix.with_name(prefix.name + "_trades.csv"), sep=";")
    assert set(summary["spread"].dropna().astype(float)) == {0.4}
    assert set(trades["spread"].dropna().astype(float)) == {0.4}


def test_closed_h1_excludes_exact_open_time():
    entries = pd.DataFrame(
        {
            "time": pd.to_datetime(["2020-01-01 10:00:00"]),
            "side": ["BUY"],
            "ATR": [2.0],
            "fractal0_price": [100.0],
            "planned_entry_bid_equivalent": [101.0],
            "planned_protective_stop_price": [97.0],
            "planned_r_value": [4.0],
        }
    )
    ohlc = pd.DataFrame(
        {
            "time": pd.to_datetime(["2020-01-01 09:00:00", "2020-01-01 10:00:00"]),
            "open": [90.0, 200.0],
            "high": [98.0, 210.0],
            "low": [89.0, 190.0],
            "close": [96.0, 205.0],
        }
    )
    features, _ = runner.build_rich_feature_frame(entries, ohlc, "price_action_h1")
    assert features.loc[0, "h1_close"] == 96.0


def test_parse_serialized_fractal_and_nonzero_structure_features():
    raw0 = "1700000000:100.5:1:2:3:1:0:1:4:5:6:0.1:0.2:0.3:0.4:0.5:0.6:0.7:0.8:0.9:1.0:2.5:12"
    raw1 = "1699996400:99.0:-1:1:2:0:1:0:3:4:5:0.2:0.1:0.4:0.3:0.6:0.5:0.8:0.7:1.0:0.9:2.0:24"
    entries = pd.DataFrame(
        {
            "time": pd.to_datetime(["2020-01-01 10:00:00"]),
            "side": ["BUY"],
            "ATR": [2.0],
            "fractal0": [raw0],
            "fractal1": [raw1],
            "fractal0_price": [100.5],
            "planned_entry_bid_equivalent": [101.0],
            "planned_protective_stop_price": [97.0],
            "planned_r_value": [4.0],
        }
    )
    parsed = runner.parse_serialized_fractal(raw0)
    assert parsed["price"] == 100.5
    assert parsed["direction"] == 1
    assert parsed["up_3"] == 0.7
    assert parsed["dn_48"] == 0.6
    features, _ = runner.build_rich_feature_frame(entries, pd.DataFrame(), "structure_f0_only")
    assert features.loc[0, "fractal0_power"] == 4.0
    assert features.loc[0, "fractal0_shift"] == 12.0
    rel, _ = runner.build_rich_feature_frame(entries, pd.DataFrame(), "relative_geometry_k40")
    assert rel.loc[0, "fractal1_price_rel_f0"] == -1.5
    assert rel.loc[0, "fractal1_direction"] == -1.0


def test_base_entry_rows_preserve_serialized_fractals_for_rich_features():
    raw0 = "1700000000:100.5:1:2:3:1:0:1:4:5:6:0.1:0.2:0.3:0.4:0.5:0.6:0.7:0.8:0.9:1.0:2.5:12"
    raw1 = "1699996400:99.0:-1:1:2:0:1:0:3:4:5:0.2:0.1:0.4:0.3:0.6:0.5:0.8:0.7:1.0:0.9:2.0:24"
    rows = pd.DataFrame(
        {
            "time": pd.to_datetime(["2020-01-01 10:00:00"]),
            "ATR": [2.0],
            "fractal0": [raw0],
            "fractal1": [raw1],
            "split_row_id": [7],
            "split": ["train_core"],
        }
    )
    ohlc = pd.DataFrame(
        {
            "time": pd.to_datetime(["2020-01-01 11:00:00", "2020-01-01 12:00:00"]),
            "open": [102.0, 101.0],
            "high": [103.0, 102.0],
            "low": [100.0, 99.0],
            "close": [101.0, 100.0],
        }
    )
    entries = base.build_entry_rows(rows, ohlc, runner._entry_rule(), base.CONFIG.canonical_spread, base.stop_policy_grid()[2])
    assert entries.loc[0, "fractal0"] == raw0
    assert entries.loc[0, "fractal1"] == raw1
    features, _ = runner.build_rich_feature_frame(entries, pd.DataFrame(), "structure_f0_only")
    assert features.loc[0, "fractal0_price"] == 100.5
    assert features.loc[0, "fractal0_direction"] == 1.0
    assert features.loc[0, "fractal0_shift"] == 12.0


def test_structure_nearest_profile_sorts_by_planned_limit_distance():
    far = "1700000000:100.0:1:1:1:1:0:0:1:1:1:0:0:0:0:0:0:0:0:0:0:1:10"
    near = "1700000001:104.8:-1:2:2:0:1:0:5:5:5:0:0:0:0:0:0:0:0:0:0:1:20"
    entries = pd.DataFrame(
        {
            "time": pd.to_datetime(["2020-01-01 10:00:00"]),
            "side": ["BUY"],
            "ATR": [2.0],
            "fractal0": [far],
            "fractal1": [near],
            "fractal0_price": [100.0],
            "planned_entry_bid_equivalent": [105.0],
            "planned_protective_stop_price": [97.0],
            "planned_r_value": [8.0],
        }
    )
    features, _ = runner.build_rich_feature_frame(entries, pd.DataFrame(), "structure_nearest_k20")
    assert features.loc[0, "fractal0_price_rel_f0"] == pytest.approx(4.8)
    assert features.loc[0, "fractal0_direction"] == -1.0


def test_structure_f0_gate_allows_constant_nonmissing_shift_with_live_price_direction():
    features = pd.DataFrame(
        {
            "fractal0_price": [100.0, 101.0, 102.0],
            "fractal0_direction": [-1.0, 1.0, -1.0],
            "fractal0_shift": [1.0, 1.0, 1.0],
        }
    )
    gate = runner.structural_feature_gate("structure_f0_only", features)
    assert gate["status"] == "PASS"


def test_structure_all100_is_diagnostic_only():
    profiles = {p["profile_id"]: p for p in runner.rich_feature_profile_grid()}
    assert profiles["structure_all100"]["eligible_for_winner"] is False


def test_train_rich_entry_model_scores_classification_and_regression():
    x = pd.DataFrame({"a": [0.0, 1.0, 2.0, 3.0], "b": [1.0, 1.0, 0.0, 0.0]})
    y_cls = pd.Series([0, 0, 1, 1])
    y_reg = pd.Series([-1.0, -0.5, 0.5, 1.0])

    cls_model = runner.train_rich_entry_model(x, y_cls, "classification", "extra_trees_shallow", threads=1, seed=42)
    reg_model = runner.train_rich_entry_model(x, y_reg, "regression", "linear", threads=1, seed=42)

    cls_score = runner.score_rich_entry_model(cls_model, x, "classification")
    reg_score = runner.score_rich_entry_model(reg_model, x, "regression")

    assert cls_score.shape == (4,)
    assert reg_score.shape == (4,)
    assert ((cls_score >= 0.0) & (cls_score <= 1.0)).all()


def test_prepare_rich_training_target_aligns_features_by_position_id():
    entries = pd.DataFrame({"position_id": ["p1", "p2", "p3"]})
    x = pd.DataFrame({"a": [10.0, 20.0, 30.0]})
    labels = pd.DataFrame({"position_id": ["p2", "p3"], "target_entry_ev_regression": [0.5, -0.25]})
    aligned_x, y = runner.prepare_rich_training_target(entries, x, labels, "target_entry_ev_regression")
    assert aligned_x.index.tolist() == ["p2", "p3"]
    assert aligned_x["a"].tolist() == [20.0, 30.0]
    assert y.tolist() == [0.5, -0.25]


def test_select_rich_winner_ignores_diagnostic_rows_and_low_n():
    summary = pd.DataFrame(
        [
            {"profile_id": "structure_all100", "model_id": "extra_trees_current", "target_id": "target_entry_good_0_5r", "filter_id": "top10", "split": "val_select", "bs_p05": 9.0, "max_drawdown_r": 1.0, "n_trades": 50, "eligible_for_winner": False},
            {"profile_id": "rich_combined_k40", "model_id": "hist_gradient_boosting", "target_id": "target_entry_good_0_5r", "filter_id": "top30", "split": "val_select", "bs_p05": 2.5, "max_drawdown_r": 2.0, "n_trades": 500, "eligible_for_winner": True},
            {"profile_id": "time_only", "model_id": "linear", "target_id": "target_entry_avoid_sl", "filter_id": "top50", "split": "val_select", "bs_p05": 2.4, "max_drawdown_r": 1.5, "n_trades": 500, "eligible_for_winner": True},
        ]
    )
    winner = runner.select_rich_winner(summary)
    assert winner["profile_id"] == "rich_combined_k40"
    assert winner["filter_id"] == "top30"


def test_previous_s2_x2_no_mask_baseline_loads_exact_row(tmp_path, monkeypatch):
    reports = tmp_path / "ML" / "reports"
    reports.mkdir(parents=True)
    summary = reports / "fractal0_stop_grid_m5_summary.csv"
    summary.write_text(
        "stop_policy_id;entry_id;mask_id;exit_id;split;n_trades;pf;bs_p05;mean_pnl_r;max_drawdown_r\n"
        "S2_fractal0_buffer_0_5_entry_floor_2;E3_open_pullback_1_0atr;M0_no_mask;X2_ml_opposite_any_p0_50;val_eval;2298;2.78;2.50;0.28;8.3\n"
        "S2_fractal0_buffer_0_5_entry_floor_2;E3_open_pullback_1_0atr;M0_no_mask;X0_fixed_r_0_7;val_eval;1;9;9;9;9\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(runner, "PROJECT_ROOT", tmp_path)
    row = runner.previous_s2_x2_no_mask_baseline({"artifacts": {"summary_csv": "ML/reports/fractal0_stop_grid_m5_summary.csv"}})
    assert row["exit_id"] == "X2_ml_opposite_any_p0_50"
    assert row["n_trades"] == 2298


def test_rich_verdict_ignores_diagnostic_best_val_eval():
    selected = {"profile_id": "rich_combined_k40", "split": "val_eval", "n_trades": 400, "bs_p05": 2.6}
    diagnostic_best = {"profile_id": "structure_all100", "split": "val_eval", "n_trades": 30, "bs_p05": 99.0, "not_eligible_for_winner": True}
    controls = {"s2_no_mask": {"bs_p05": 2.3}, "s0_x0": {"bs_p05": 2.5}}
    verdict = runner.evaluate_rich_verdict(selected, controls, diagnostic_best_val_eval=diagnostic_best)
    assert verdict == "RESEARCH_HINT_RICH_FEATURES"


def test_rich_artifact_schema_contains_required_disclosures():
    artifact = runner.empty_rich_artifact(
        search_budget={"n_total_ranked_configs": 243},
        feature_contract=[{"feature": "side_buy", "live_safe": True}],
    )
    assert artifact["experiment"] == "fractal0_rich_entry_quality"
    assert artifact["locked_test"] == "not_opened"
    assert artifact["allowed_max_verdict"] == "RESEARCH_HINT_RICH_FEATURES"
    assert "forbidden_interpretations" in artifact
    assert artifact["selection_policy"]["val_eval"] == "fixed selected_rule only"


def test_rich_cumulative_search_budget_discloses_parent_and_current(monkeypatch, tmp_path):
    narrow_path = tmp_path / "ML" / "reports" / "fractal0_entry_quality_filter.json"
    narrow_path.parent.mkdir(parents=True)
    narrow_path.write_text(
        json.dumps(
            {
                "status": "completed",
                "verdict": "research_hint",
                "current_search_budget": {"filters": 17},
                "cumulative_search_budget": {"entry_quality_filters": 17},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(runner, "PROJECT_ROOT", tmp_path)

    budget = runner.build_rich_cumulative_search_budget(
        {"status": "PASS", "verdict": "research_only", "current_search_budget": {"selection_cells": 288}},
        {"n_total_ranked_configs": 243, "n_diagnostic_configs": 1143},
        {"n_total_ranked_configs": 243},
    )

    assert budget["parent_stop_grid"]["current_search_budget"]["selection_cells"] == 288
    assert budget["narrow_entry_quality_predecessor"]["current_search_budget"]["filters"] == 17
    assert budget["current_rich_ranked_search_budget"]["n_total_ranked_configs"] == 243
    assert budget["current_rich_diagnostic_budget"]["listed_diagnostic_configs"] == 1143
    assert budget["current_rich_diagnostic_budget"]["executed_by_default_run"] is False


def test_structure_f0_gate_discloses_constant_and_required_fields():
    features = pd.DataFrame(
        {
            "fractal0_price": [1.0, 2.0, 3.0],
            "fractal0_direction": [-1, 1, -1],
            "fractal0_shift": [3, 3, 3],
            "fractal0_break": [0, 0, 0],
        }
    )
    row = runner.structural_feature_gate("structure_f0_only", features)

    assert row["status"] == "PASS"
    assert row["constant_features"] == 2
    assert row["constant_feature_names"] == "fractal0_shift|fractal0_break"
    assert row["required_live_fields"] == "fractal0_price|fractal0_direction|fractal0_shift"
    assert row["informational_constant_fields"] == "fractal0_shift|fractal0_break"


def test_rich_score_distribution_diagnostics_is_grouped_and_nonempty():
    scores = pd.DataFrame(
        {
            "split": ["val_select", "val_select", "val_eval"],
            "profile_id": ["time_only", "time_only", "time_only"],
            "model_id": ["linear", "linear", "linear"],
            "target_id": ["target_entry_ev_regression"] * 3,
            "filter_id": ["top30"] * 3,
            "rich_entry_score": [0.1, 0.5, 0.2],
        }
    )
    diag = pd.DataFrame(runner.score_distribution_diagnostics(scores))
    assert not diag.empty
    assert "rich_entry_score" in set(diag["score_col"])
    assert {"profile_id", "model_id", "target_id", "filter_id"}.issubset(diag.columns)


def test_parse_args_accepts_rich_entry_quality_flags():
    args = runner.parse_args(
        [
            "--rich-entry-quality",
            "--include-diagnostic-models",
            "--output-prefix",
            "/tmp/fractal0_rich_entry_quality_smoke",
            "--smoke-limit-filters",
            "1",
        ]
    )
    assert args.rich_entry_quality is True
    assert args.include_diagnostic_models is True
    assert args.output_prefix == "/tmp/fractal0_rich_entry_quality_smoke"


def test_target_distribution_audit_counts_classes_and_regression_stats_by_split():
    labels = pd.DataFrame(
        {
            "split": ["train_core", "train_core", "val_select", "val_select", "val_select"],
            "side": ["BUY", "SELL", "BUY", "SELL", "SELL"],
            "time": pd.to_datetime(["2020-01-01", "2020-01-02", "2021-01-01", "2021-01-02", "2021-01-03"]),
            "target_entry_good_0_5r": [1, 0, 1, 1, 0],
            "target_entry_ev_regression": [0.6, -1.0, 0.7, 0.2, -0.3],
        }
    )
    target_contract = {
        "target_entry_good_0_5r": "classification",
        "target_entry_ev_regression": "regression",
    }
    audit = runner.target_distribution_audit(labels, target_contract)
    assert {"split", "side", "year", "target_id", "target_kind", "rows"}.issubset(audit.columns)
    cls = audit.loc[audit["target_id"].eq("target_entry_good_0_5r")]
    reg = audit.loc[audit["target_id"].eq("target_entry_ev_regression")]
    assert {"class_0_count", "class_1_count", "positive_rate", "minority_count"}.issubset(cls.columns)
    assert {"mean", "median", "p05", "p50", "p95", "std", "nan_rate"}.issubset(reg.columns)


def test_normalized_rich_allowlist_excludes_raw_price_like_columns():
    for profile_id in [
        "atr_only",
        "time_plus_atr",
        "planned_geometry_no_atr",
        "planned_geometry_only",
        "time_only",
        "structure_f0_only",
        "structure_nearest_k20",
        "structure_nearest_k40",
        "relative_geometry_k40",
        "price_action_h1",
        "movement_plus_time",
        "rich_combined_k40",
    ]:
        cols = runner.normalized_rich_feature_allowlist(profile_id)
        assert all(not col.endswith("_price") for col in cols)
        assert not {"h1_open", "h1_high", "h1_low", "h1_close"}.intersection(cols)
        assert "fractal0_price" not in cols
        runner.assert_no_raw_price_like_features(cols)

    for raw_name in ["h1_body", "h1_range", "planned_limit_distance", "entry_price_delta", "fractal12_price"]:
        with pytest.raises(ValueError, match="raw price-like"):
            runner.assert_no_raw_price_like_features([raw_name])


def test_normalized_fractal_geometry_uses_atr_coordinates():
    raw0 = "1700000000:100.0:1:2:3:1:0:1:4:5:6:0.1:0.2:0.3:0.4:0.5:0.6:0.7:0.8:0.9:1.0:2.5:12"
    raw1 = "1699996400:104.0:-1:1:2:0:1:0:3:4:5:0.2:0.1:0.4:0.3:0.6:0.5:0.8:0.7:1.0:0.9:2.0:24"
    entries = pd.DataFrame(
        {
            "time": pd.to_datetime(["2020-01-01 10:00:00"]),
            "side": ["BUY"],
            "ATR": [2.0],
            "fractal0_price": [100.0],
            "planned_entry_bid_equivalent": [101.0],
            "planned_protective_stop_price": [97.0],
            "planned_r_value": [4.0],
            "fractal0": [raw0],
            "fractal1": [raw1],
        }
    )
    ohlc = pd.DataFrame(columns=["time", "open", "high", "low", "close"])

    frame, _ = runner.build_normalized_rich_feature_frame(entries, ohlc, "structure_nearest_k20")

    assert "fractal0_price_rel_f0_atr" in frame.columns
    assert "fractal0_distance_to_planned_limit_atr" in frame.columns
    assert "fractal0_distance_to_planned_stop_atr" in frame.columns
    assert "fractal0_present" in frame.columns
    assert "fractal0_price_rel_f0" not in frame.columns
    assert "fractal0_distance_to_planned_limit" not in frame.columns


def test_normalized_fractal_padding_is_zero_and_explicitly_masked():
    raw0 = "1700000000:100.0:1:2:3:1:0:1:4:5:6:0.1:0.2:0.3:0.4:0.5:0.6:0.7:0.8:0.9:1.0:2.5:12"
    entries = pd.DataFrame(
        {
            "time": pd.to_datetime(["2020-01-01 10:00:00"]),
            "side": ["BUY"],
            "ATR": [2.0],
            "fractal0_price": [100.0],
            "planned_entry_bid_equivalent": [101.0],
            "planned_protective_stop_price": [97.0],
            "planned_r_value": [4.0],
            "fractal0": [raw0],
        }
    )
    ohlc = pd.DataFrame(columns=["time", "open", "high", "low", "close"])

    frame, _ = runner.build_normalized_rich_feature_frame(entries, ohlc, "structure_nearest_k20")

    padded_cols = [col for col in frame.columns if col.startswith("fractal1_") and col != "fractal1_present"]
    assert frame.loc[0, "fractal0_present"] == 1.0
    assert frame.loc[0, "fractal1_present"] == 0.0
    assert frame.loc[0, padded_cols].eq(0.0).all()


def test_normalized_token_coverage_uses_profile_k20_length():
    raws = [
        f"{1700000000 - i * 300}:{100.0 + i}:1:2:3:1:0:1:4:5:6:0.1:0.2:0.3:0.4:0.5:0.6:0.7:0.8:0.9:1.0:2.5:{12+i}"
        for i in range(25)
    ]
    entries = pd.DataFrame(
        {
            "time": pd.to_datetime(["2020-01-01 10:00:00"]),
            "side": ["BUY"],
            "ATR": [2.0],
            "fractal0_price": [100.0],
            "planned_entry_bid_equivalent": [101.0],
            "planned_protective_stop_price": [97.0],
            "planned_r_value": [4.0],
            **{f"fractal{i}": [raw] for i, raw in enumerate(raws)},
        }
    )
    ohlc = pd.DataFrame(columns=["time", "open", "high", "low", "close"])

    _, audit_rows = runner.build_normalized_rich_feature_frame(entries, ohlc, "structure_nearest_k20")
    coverage = runner.token_coverage_audit([{**row, "split": "train_core"} for row in audit_rows if "valid_token_count" in row])

    row = coverage.iloc[0]
    assert row["profile_id"] == "structure_nearest_k20"
    assert row["p50_valid_token_count"] == 20.0
    assert row["truncation_rate"] == 1.0


def test_normalized_schema_keeps_missing_indicator_columns_stable_across_splits():
    train = pd.DataFrame({"a": [0.0, 10.0], "b": [5.0, 6.0]})
    val = pd.DataFrame({"a": [1.0, None], "b": [5.0, 7.0]})
    schema = runner.build_normalized_feature_schema("unit_test_profile", train, missing_capable_columns=["a"])
    scaler = runner.fit_unit_scaler({"train_core": train}, schema)

    out_train = runner.apply_unit_scaler(train, scaler, schema)
    out_val = runner.apply_unit_scaler(val, scaler, schema)

    assert list(out_train.columns) == list(out_val.columns)
    assert "a_missing" in out_train.columns
    assert out_train["a_missing"].tolist() == [0.0, 0.0]
    assert out_val["a_missing"].tolist() == [0.0, 1.0]


def test_unit_scaler_fits_train_only_and_clips_validation():
    train = pd.DataFrame({"a": [0.0, 10.0], "b": [5.0, 5.0]})
    val = pd.DataFrame({"a": [-100.0, 100.0], "b": [5.0, 7.0]})
    schema = runner.build_normalized_feature_schema("unit_test_profile", train)
    scaler = runner.fit_unit_scaler({"train_core": train}, schema)

    out_train = runner.apply_unit_scaler(train, scaler, schema)
    out_val = runner.apply_unit_scaler(val, scaler, schema)

    assert out_train["a"].tolist() == [0.0, 1.0]
    assert out_train["b"].tolist() == [0.0, 0.0]
    assert out_val["a"].tolist() == [0.0, 1.0]
    assert out_val["b"].tolist() == [0.0, 0.0]
    assert scaler["a"]["fit_split"] == "train_core"
    assert scaler["b"]["constant"] is True


def test_assert_unit_scaled_frame_rejects_out_of_range_values():
    frame = pd.DataFrame({"ok": [0.0, 0.5, 1.0], "bad": [0.0, 1.2, 0.3]})
    with pytest.raises(ValueError, match="outside 0..1"):
        runner.assert_unit_scaled_frame(frame, "unit_test_profile")


def test_normalized_structure_f0_gate_uses_normalized_required_fields():
    features = pd.DataFrame(
        {
            "fractal0_price_to_planned_limit_atr": [0.1, 0.5, 0.9],
            "fractal0_direction_unit": [0.0, 1.0, 0.0],
            "fractal0_shift": [0.0, 0.0, 0.0],
            "fractal0_price_to_planned_limit_atr_missing": [0.0, 0.0, 0.0],
            "fractal0_direction_unit_missing": [0.0, 0.0, 0.0],
        }
    )

    gate = runner.structural_feature_gate("structure_f0_only", features)

    assert gate["status"] == "PASS"
    assert "fractal0_price_to_planned_limit_atr" in gate["required_live_fields"]
    assert "fractal0_direction_unit" in gate["required_live_fields"]


def test_forbidden_column_audit_exposes_raw_price_like_result(monkeypatch):
    monkeypatch.setattr(runner, "normalized_rich_feature_allowlist", lambda profile_id: ["target_leak", "fractal0_price", "safe_atr"])

    audit = runner.forbidden_column_audit(["unit_profile"])

    assert {"target_or_future_forbidden", "raw_price_like", "forbidden"}.issubset(audit.columns)
    assert bool(audit.loc[audit["feature"].eq("target_leak"), "target_or_future_forbidden"].iloc[0]) is True
    assert bool(audit.loc[audit["feature"].eq("fractal0_price"), "raw_price_like"].iloc[0]) is True
    assert bool(audit.loc[audit["feature"].eq("safe_atr"), "forbidden"].iloc[0]) is False


def test_normalized_updn_gate_marks_source_provenance_unknown():
    gate = runner.normalized_updn_provenance_gate()

    assert {"usage_status", "source_provenance_status", "status"}.issubset(gate.columns)
    row = gate.iloc[0]
    assert row["usage_status"] == "PASS"
    assert row["source_provenance_status"] == "UNKNOWN"
    assert row["status"] == "SOURCE_PROVENANCE_NOT_VERIFIED"


def test_compare_rich_runs_protocol_uses_val_select_then_fixed_val_eval():
    old = pd.DataFrame(
        [
            {"split": "val_select", "profile_id": "time_only", "model_id": "linear", "target_id": "target_entry_ev_regression", "filter_id": "top30", "eligible_for_winner": True, "bs_p05": 3.0, "pf": 4.0, "n_trades": 600},
            {"split": "val_eval", "profile_id": "time_only", "model_id": "linear", "target_id": "target_entry_ev_regression", "filter_id": "top30", "eligible_for_winner": True, "bs_p05": 2.7, "pf": 3.7, "n_trades": 610},
            {"split": "val_eval", "profile_id": "time_only", "model_id": "linear", "target_id": "target_entry_good_0_5r", "filter_id": "top10", "eligible_for_winner": True, "bs_p05": 9.9, "pf": 10.0, "n_trades": 120},
        ]
    )
    new = pd.DataFrame(
        [
            {"split": "val_select", "profile_id": "time_only", "model_id": "linear", "target_id": "target_entry_ev_regression", "filter_id": "top30", "eligible_for_winner": True, "bs_p05": 2.5, "pf": 3.5, "n_trades": 600},
            {"split": "val_eval", "profile_id": "time_only", "model_id": "linear", "target_id": "target_entry_ev_regression", "filter_id": "top30", "eligible_for_winner": True, "bs_p05": 2.4, "pf": 3.3, "n_trades": 610},
            {"split": "val_eval", "profile_id": "time_only", "model_id": "linear", "target_id": "target_entry_good_0_5r", "filter_id": "top10", "eligible_for_winner": True, "bs_p05": 8.8, "pf": 9.0, "n_trades": 120},
        ]
    )

    comparison = runner.compare_rich_runs_protocol(old, new)

    row = comparison.loc[comparison["profile_id"].eq("time_only")].iloc[0]
    assert row["old_eval_bs_p05"] == 2.7
    assert row["new_eval_bs_p05"] == 2.4
    assert row["delta_eval_bs_p05"] == pytest.approx(-0.3)
    assert row["old_filter_id"] == "top30"
    assert row["new_filter_id"] == "top30"


def test_split_manifest_has_dates_and_order():
    entries = {
        "val_select": pd.DataFrame({"time": pd.to_datetime(["2020-01-01", "2020-01-02"]), "filled": [True, False]}),
        "val_eval": pd.DataFrame({"time": pd.to_datetime(["2020-02-01", "2020-02-02"]), "filled": [True, True]}),
    }
    manifest = runner.build_split_manifest(entries)
    assert manifest.loc[manifest["split"].eq("val_select"), "max_time"].iloc[0] < manifest.loc[manifest["split"].eq("val_eval"), "min_time"].iloc[0]
    assert int(manifest.loc[manifest["split"].eq("val_eval"), "filled_trades"].iloc[0]) == 2


def test_movement_provenance_blocks_missing_score_contract():
    with pytest.raises(ValueError, match="movement_score provenance"):
        runner.validate_movement_provenance(pd.DataFrame({"position_id": ["a"], "movement_score": [pd.NA]}), {"movement_artifact_path": ""})
