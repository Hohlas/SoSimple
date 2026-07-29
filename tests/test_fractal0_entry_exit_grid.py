from pathlib import Path

import pandas as pd
import pytest

import ML.baseline.benchmark_fractal0_entry_exit_grid as runner


def test_grid_has_disclosed_size_and_required_controls():
    assert [item["entry_id"] for item in runner.entry_grid()] == [
        "E0_selected_zone_edge",
        "E1_simple_limit_at_fractal0",
        "E2_open_pullback_0_5atr",
        "E3_open_pullback_1_0atr",
    ]
    assert len(runner.exit_grid()) == 48
    assert {item["exit_id"] for item in runner.exit_grid()} >= {
        "X0_fixed_r_0_7",
        "X6_trail_atr_0_2_activation_0",
        "X6_trail_atr_5_activation_3",
        "X7_time_1",
        "X7_time_12",
    }
    assert [item["mask_id"] for item in runner.mask_grid()] == ["M0_no_mask", "M1_frozen_movement_top5"]
    assert len(runner.expanded_grid()) == 1536


def test_stop_policy_grid_has_current_and_entry_floor_variants():
    ids = [item["stop_policy_id"] for item in runner.stop_policy_grid()]
    assert ids == [
        "S0_current_0_5",
        "S1_fractal0_buffer_0_5_entry_floor_1",
        "S2_fractal0_buffer_0_5_entry_floor_2",
        "S3_fractal0_buffer_0_5_entry_floor_3",
    ]


def test_entry_floor_stop_keeps_buy_stop_at_least_x_atr_from_entry():
    policy = {
        "stop_policy_id": "S2_fractal0_buffer_0_5_entry_floor_2",
        "family": "fractal0_buffer_entry_floor",
        "fractal0_buffer_atr": 0.5,
        "entry_floor_atr": 2.0,
    }
    resolved = runner.resolve_protective_stop("BUY", 100.0, 101.0, 2.0, policy)
    assert resolved["protective_stop_price"] == 97.0
    assert resolved["stop_source"] == "entry_floor"


def test_entry_floor_stop_keeps_sell_stop_at_least_x_atr_from_entry():
    policy = {
        "stop_policy_id": "S3_fractal0_buffer_0_5_entry_floor_3",
        "family": "fractal0_buffer_entry_floor",
        "fractal0_buffer_atr": 0.5,
        "entry_floor_atr": 3.0,
    }
    resolved = runner.resolve_protective_stop("SELL", 100.0, 99.0, 2.0, policy)
    assert resolved["protective_stop_price"] == 105.0
    assert resolved["stop_source"] == "entry_floor"


def test_hash_is_stable_and_resume_key_ignores_runtime_order():
    assert runner.stable_json_hash({"b": 2, "a": {"x": 1}}) == runner.stable_json_hash({"a": {"x": 1}, "b": 2})
    left = {"entry_id": "E1", "exit_id": "X0", "mask_id": "M0", "spread": 0.2}
    right = {"spread": 0.2, "mask_id": "M0", "exit_id": "X0", "entry_id": "E1"}
    assert runner.resume_key(left) == runner.resume_key(right)


def test_expanded_grid_includes_stop_policy_id():
    grid = runner.expanded_grid(
        active_stop_policies=[{"stop_policy_id": "S0_current_0_5", "family": "current", "fractal0_buffer_atr": 0.5, "entry_floor_atr": 0.5}],
        active_entries=[runner.entry_grid()[0]],
        active_masks=[runner.mask_grid()[0]],
        active_exits=[runner.exit_grid()[0]],
    )
    assert grid[0]["stop_policy_id"] == "S0_current_0_5"


def test_resume_key_distinguishes_stop_policy():
    base = {"entry_id": "E3", "mask_id": "M0", "exit_id": "X2", "spread": 0.2, "stop_policy_id": "S0"}
    changed = {**base, "stop_policy_id": "S1"}
    assert runner.resume_key(base) != runner.resume_key(changed)


def test_stop_grid_exit_shortlist_is_bounded():
    exits = runner.exit_grid(shortlist="stop_grid")
    ids = {item["exit_id"] for item in exits}
    assert ids == {
        "X0_fixed_r_0_7",
        "X1_ml_opposite_strong_p0_55",
        "X1_ml_opposite_strong_p0_65",
        "X1_ml_opposite_strong_p0_75",
        "X2_ml_opposite_any_p0_50",
        "X2_ml_opposite_any_p0_55",
        "X2_ml_opposite_any_p0_60",
        "X3_ml_hold_close_p0_50",
        "X3_ml_hold_close_p0_60",
        "X3_ml_hold_close_p0_70",
        "X7_time_6",
        "X7_time_12",
    }


def test_load_progress_rejects_hash_mismatch(tmp_path: Path):
    path = tmp_path / "progress.json"
    runner.write_progress_atomic(path, {"run_config_hash": "old", "completed": {}})
    with pytest.raises(ValueError, match="run_config_hash mismatch"):
        runner.load_progress(path, expected_hash="new")


def test_preflight_reports_missing_input_with_clear_label(tmp_path: Path):
    config = runner.Fractal0EntryExitGridConfig(
        ohlc_path=str(tmp_path / "missing_ohlc.csv"),
        train_path=str(tmp_path / "train.csv"),
        validation_path=str(tmp_path / "validation.csv"),
        movement_freeze_json=str(tmp_path / "freeze.json"),
        movement_freeze_scores=str(tmp_path / "scores.csv"),
    )
    result = runner.preflight_inputs(config)
    assert result["status"] == "FAIL"
    assert any(item["id"] == "ohlc" for item in result["errors"])


def _ohlc():
    return pd.DataFrame(
        {
            "time": pd.to_datetime(["2021-01-01 10:00", "2021-01-01 11:00", "2021-01-01 12:00", "2021-01-01 13:00"]),
            "open": [100.0, 101.0, 102.0, 103.0],
            "high": [101.0, 102.0, 104.0, 105.0],
            "low": [99.0, 100.0, 100.5, 102.5],
            "close": [100.5, 101.5, 103.5, 104.0],
        }
    )


def test_buy_limit_fill_uses_ask_side_with_full_spread():
    fill = runner.resolve_executable_fill("BUY", pd.Timestamp("2021-01-01 10:00"), 100.7, 2, 0.2, _ohlc(), 1)
    assert fill["filled"] is True
    assert fill["fill_index"] == 2
    assert fill["entry_effective_price"] == 100.7
    assert fill["entry_bid_equivalent"] == 100.5


def test_sell_limit_fill_uses_bid_side():
    fill = runner.resolve_executable_fill("SELL", pd.Timestamp("2021-01-01 10:00"), 103.0, 2, 0.2, _ohlc(), 1)
    assert fill["filled"] is True
    assert fill["fill_index"] == 2
    assert fill["entry_effective_price"] == 103.0
    assert fill["entry_bid_equivalent"] == 103.0


def test_limit_fill_records_first_execution_ohlc_timestamp_inside_h1():
    rows = pd.DataFrame(
        {
            "time": pd.to_datetime(["2021-01-01 08:00"]),
            "fractal0": [":".join(["0", "100.0", "1"] + ["0"] * 20)],
            "ATR": [1.0],
            "split": ["locked_test"],
            "split_row_id": [7],
        }
    )
    h1 = pd.DataFrame(
        {
            "time": pd.to_datetime(["2021-01-01 09:00", "2021-01-01 10:00", "2021-01-01 11:00"]),
            "open": [100.0, 100.2, 101.0],
            "high": [100.4, 101.2, 102.0],
            "low": [99.6, 99.8, 100.0],
            "close": [100.1, 100.8, 101.5],
        }
    )
    m5 = pd.DataFrame(
        {
            "time": pd.to_datetime(["2021-01-01 10:00", "2021-01-01 10:05", "2021-01-01 10:10"]),
            "open": [100.0, 100.4, 100.7],
            "high": [100.3, 100.6, 101.2],
            "low": [99.8, 100.2, 100.6],
            "close": [100.2, 100.5, 101.0],
        }
    )
    entry_rule = {"entry_id": "E3_open_pullback_1_0atr", "entry_mode": "open_pullback", "pullback_atr": 1.0, "lag_bars": 2}
    policy = {"stop_policy_id": "S2", "family": "fractal0_buffer_entry_floor", "fractal0_buffer_atr": 0.5, "entry_floor_atr": 2.0}

    entries = runner.build_entry_rows(rows, h1, entry_rule, spread=0.2, stop_policy=policy, execution_ohlc=m5)

    assert bool(entries.loc[0, "filled"]) is True
    assert entries.loc[0, "side"] == "SELL"
    assert entries.loc[0, "limit_price"] == 101.0
    assert entries.loc[0, "fill_index"] == 1
    assert entries.loc[0, "fill_time"] == pd.Timestamp("2021-01-01 10:00")
    assert entries.loc[0, "fill_execution_time"] == pd.Timestamp("2021-01-01 10:10")


def test_protective_stop_uses_fixed_half_atr():
    assert runner.protective_stop_price("BUY", 100.0, 100.5, 2.0) == 99.0
    assert runner.protective_stop_price("SELL", 100.0, 99.5, 2.0) == 101.0


def test_simulator_tp_only_returns_positive_pnl_r():
    entry = {"side": "BUY", "fill_index": 0, "entry_effective_price": 100.2, "entry_bid_equivalent": 100.0, "protective_stop_price": 99.0, "r_value": 1.2, "atr": 2.0}
    bars = pd.DataFrame({"open": [100.0, 100.8], "high": [100.9, 101.1], "low": [100.0, 100.7], "close": [100.8, 101.0], "time": pd.to_datetime(["2021-01-01 10:00", "2021-01-01 11:00"])})
    result = runner.simulate_trade(entry, bars, {"family": "fixed_r", "tp_r": 0.7}, spread=0.2)
    assert result["close_reason"] == "TP"
    assert result["pnl_r"] > 0


def test_simulator_sl_first_when_tp_and_sl_same_bar():
    entry = {"side": "BUY", "fill_index": 0, "entry_effective_price": 100.2, "entry_bid_equivalent": 100.0, "protective_stop_price": 99.0, "r_value": 1.2, "atr": 2.0}
    bars = pd.DataFrame({"open": [100.0], "high": [101.2], "low": [98.9], "close": [100.5], "time": pd.to_datetime(["2021-01-01 10:00"])})
    result = runner.simulate_trade(entry, bars, {"family": "fixed_r", "tp_r": 0.7}, spread=0.2)
    assert result["close_reason"] == "SL"
    assert result["ambiguous"] is True
    assert result["pnl_r"] < 0


def test_simulator_uses_execution_ohlc_to_resolve_same_h1_bar_order():
    entry = {"side": "BUY", "fill_index": 0, "entry_effective_price": 100.2, "entry_bid_equivalent": 100.0, "protective_stop_price": 99.0, "r_value": 1.2, "atr": 2.0}
    h1 = pd.DataFrame({"open": [100.0], "high": [101.2], "low": [98.9], "close": [100.5], "time": pd.to_datetime(["2021-01-01 10:00"])})
    m5 = pd.DataFrame(
        {
            "open": [100.0, 100.7, 100.1],
            "high": [101.1, 100.8, 100.2],
            "low": [100.0, 100.0, 98.8],
            "close": [100.8, 100.1, 98.9],
            "time": pd.to_datetime(["2021-01-01 10:00", "2021-01-01 10:05", "2021-01-01 10:10"]),
        }
    )

    result = runner.simulate_trade(entry, h1, {"family": "fixed_r", "tp_r": 0.7}, spread=0.2, execution_ohlc=m5)

    assert result["close_reason"] == "TP"
    assert result["ambiguous"] is False
    assert result["exit_time"] == "2021-01-01 10:00:00"


def test_ml_exit_does_not_count_hypothetical_fixed_tp_as_same_bar_ambiguity():
    entry = {"side": "BUY", "fill_index": 0, "entry_effective_price": 100.2, "entry_bid_equivalent": 100.0, "protective_stop_price": 99.0, "r_value": 1.2, "atr": 2.0}
    bars = pd.DataFrame({"open": [100.0], "high": [101.2], "low": [98.9], "close": [100.5], "time": pd.to_datetime(["2021-01-01 10:00"])})

    result = runner.simulate_trade(entry, bars, {"family": "ml_opposite_any", "prob_threshold": 0.55}, spread=0.2)

    assert result["close_reason"] == "SL"
    assert result["ambiguous"] is False


def test_ml_exit_on_h1_open_is_not_processed_before_m5_fill_in_same_h1():
    entry = {
        "side": "SELL",
        "fill_index": 0,
        "fill_time": pd.Timestamp("2021-01-01 10:00"),
        "fill_execution_time": pd.Timestamp("2021-01-01 10:10"),
        "entry_effective_price": 101.0,
        "entry_bid_equivalent": 101.0,
        "protective_stop_price": 105.0,
        "r_value": 4.0,
        "atr": 2.0,
    }
    h1 = pd.DataFrame(
        {
            "time": pd.to_datetime(["2021-01-01 10:00", "2021-01-01 11:00"]),
            "open": [100.0, 100.2],
            "high": [101.2, 100.4],
            "low": [99.0, 99.4],
            "close": [100.5, 99.7],
        }
    )
    ml_scores = {0: 1.0, 1: 0.0}

    result = runner.simulate_trade(
        entry,
        h1,
        {"family": "ml_opposite_any", "prob_threshold": 0.55, "hold_bars": 1},
        spread=0.2,
        ml_scores=ml_scores,
    )

    assert result["close_reason"] == "TIME"
    assert result["exit_time"] == "2021-01-01 11:00:00"


def test_same_h1_stop_after_m5_fill_is_valid_when_touch_is_after_fill():
    entry = {
        "side": "BUY",
        "fill_index": 0,
        "fill_time": pd.Timestamp("2021-01-01 10:00"),
        "fill_execution_time": pd.Timestamp("2021-01-01 10:10"),
        "entry_effective_price": 100.2,
        "entry_bid_equivalent": 100.0,
        "protective_stop_price": 99.0,
        "r_value": 1.2,
        "atr": 2.0,
    }
    h1 = pd.DataFrame(
        {
            "time": pd.to_datetime(["2021-01-01 10:00"]),
            "open": [100.0],
            "high": [100.4],
            "low": [98.8],
            "close": [99.2],
        }
    )
    m5 = pd.DataFrame(
        {
            "time": pd.to_datetime(["2021-01-01 10:00", "2021-01-01 10:05", "2021-01-01 10:10", "2021-01-01 10:15"]),
            "open": [100.0, 100.1, 100.2, 99.8],
            "high": [100.3, 100.2, 100.3, 100.0],
            "low": [99.5, 99.4, 100.0, 98.8],
            "close": [100.1, 100.0, 100.1, 99.0],
        }
    )

    result = runner.simulate_trade(
        entry,
        h1,
        {"family": "ml_opposite_any", "prob_threshold": 0.55},
        spread=0.2,
        execution_ohlc=m5,
    )

    assert result["close_reason"] == "SL"
    assert result["exit_time"] == "2021-01-01 10:15:00"


def test_fill_m5_candle_stop_touch_is_marked_ambiguous_and_resolves_sl_first():
    entry = {
        "side": "BUY",
        "fill_index": 0,
        "fill_time": pd.Timestamp("2021-01-01 10:00"),
        "fill_execution_time": pd.Timestamp("2021-01-01 10:10"),
        "fill_execution_confirmed": True,
        "entry_effective_price": 100.2,
        "entry_bid_equivalent": 100.0,
        "protective_stop_price": 99.0,
        "r_value": 1.2,
        "atr": 2.0,
    }
    h1 = pd.DataFrame(
        {
            "time": pd.to_datetime(["2021-01-01 10:00"]),
            "open": [100.0],
            "high": [100.5],
            "low": [98.8],
            "close": [99.5],
        }
    )
    m5 = pd.DataFrame(
        {
            "time": pd.to_datetime(["2021-01-01 10:00", "2021-01-01 10:05", "2021-01-01 10:10"]),
            "open": [100.0, 100.1, 100.3],
            "high": [100.3, 100.2, 100.4],
            "low": [99.5, 99.4, 98.8],
            "close": [100.1, 100.0, 99.0],
        }
    )

    result = runner.simulate_trade(
        entry,
        h1,
        {"family": "ml_opposite_any", "prob_threshold": 0.55},
        spread=0.2,
        execution_ohlc=m5,
    )

    assert result["close_reason"] == "SL"
    assert result["ambiguous"] is True
    assert result["exit_time"] == "2021-01-01 10:10:00"


def test_prepare_execution_ohlc_index_supports_fast_h1_lookup():
    m5 = pd.DataFrame(
        {
            "open": [100.0, 100.7],
            "high": [101.1, 100.8],
            "low": [100.0, 100.0],
            "close": [100.8, 100.1],
            "time": pd.to_datetime(["2021-01-01 10:00", "2021-01-01 10:05"]),
        }
    )

    indexed = runner.prepare_execution_ohlc_index(m5)

    assert indexed.index.name == "_h1_time"
    assert len(indexed.loc[pd.Timestamp("2021-01-01 10:00")]) == 2


def test_sell_exit_uses_ask_shift_for_stop():
    entry = {"side": "SELL", "fill_index": 0, "entry_effective_price": 100.0, "entry_bid_equivalent": 100.0, "protective_stop_price": 101.0, "r_value": 1.0, "atr": 2.0}
    bars = pd.DataFrame({"open": [100.0], "high": [100.9], "low": [99.5], "close": [100.2], "time": pd.to_datetime(["2021-01-01 10:00"])})
    assert runner.simulate_trade(entry, bars, {"family": "fixed_r", "tp_r": 0.7}, spread=0.2)["close_reason"] == "SL"


def test_time_exit_closes_after_declared_bars():
    entry = {"side": "BUY", "fill_index": 0, "entry_effective_price": 100.2, "entry_bid_equivalent": 100.0, "protective_stop_price": 99.0, "r_value": 1.2, "atr": 2.0}
    bars = pd.DataFrame({"open": [100.0, 100.4, 100.6], "high": [100.3, 100.5, 100.7], "low": [99.8, 100.1, 100.3], "close": [100.2, 100.5, 100.6], "time": pd.to_datetime(["2021-01-01 10:00", "2021-01-01 11:00", "2021-01-01 12:00"])})
    result = runner.simulate_trade(entry, bars, {"family": "time_exit", "hold_bars": 2}, spread=0.2)
    assert result["close_reason"] == "TIME"
    assert result["hold_bars"] == 2


def test_compute_trade_metrics_reports_ambiguous_same_bar_rate():
    metrics = runner.compute_trade_metrics(pd.DataFrame({"pnl_r": [1.0, -1.0, -0.5, 0.3], "close_reason": ["TP", "SL", "SL", "TIME"], "ambiguous": [False, True, False, False]}))
    assert metrics["ambiguous_same_bar_rate"] == 0.25


def test_apply_movement_mask_keeps_only_selected_rows():
    rows = pd.DataFrame({"split_row_id": [1, 2, 3], "value": [10, 20, 30]})
    scores = pd.DataFrame({"split_row_id": [1, 2, 3], "selected": [True, False, True], "score": [0.9, 0.1, 0.8]})
    masked = runner.apply_mask(rows, "M1_frozen_movement_top5", scores)
    assert masked["split_row_id"].tolist() == [1, 3]
    assert masked["movement_score"].tolist() == [0.9, 0.8]


def test_validate_movement_mask_coverage_fails_missing_rows():
    coverage = runner.validate_movement_mask_coverage(pd.DataFrame({"split_row_id": [1, 2, 3]}), pd.DataFrame({"split_row_id": [1, 3], "selected": [True, True], "score": [0.9, 0.8]}))
    assert coverage["status"] == "FAIL"
    assert coverage["missing_score_rows"] == 1


def test_entry_cache_reports_rows_before_mask_not_entry_rule_count(monkeypatch):
    splits = {"val_select": pd.DataFrame({"split_row_id": [1, 2, 3]})}
    scores = pd.DataFrame({"split": ["val_select", "val_select", "val_select"], "split_row_id": [1, 2, 3], "selected": [True, False, True], "score": [0.9, 0.1, 0.8]})

    def fake_build_entry_rows(rows, ohlc, entry, spread, stop_policy=None, execution_ohlc=None):
        out = rows.copy()
        out["filled"] = [True, False, True]
        return out

    monkeypatch.setattr(runner, "build_entry_rows", fake_build_entry_rows)
    _, report = runner._entry_cache_for_spread(
        splits,
        pd.DataFrame(),
        0.2,
        scores,
        entries=[{"entry_id": "E1"}, {"entry_id": "E2"}],
        masks=[{"mask_id": "M0_no_mask"}, {"mask_id": "M1_frozen_movement_top5"}],
    )

    rows_report = report["rows_by_split_before_after_mask"]["val_select"]
    assert rows_report["S0_current_0_5:E1:M0_no_mask"]["entry_rows_before_mask"] == 3
    assert rows_report["S0_current_0_5:E1:M0_no_mask"]["rows_after_mask"] == 3
    assert rows_report["S0_current_0_5:E1:M1_frozen_movement_top5"]["entry_rows_before_mask"] == 3
    assert rows_report["S0_current_0_5:E1:M1_frozen_movement_top5"]["rows_after_mask"] == 2


def test_summary_uses_effective_profit_years_formula():
    trades = pd.DataFrame(
        [
            {"pnl_r": 9.0, "exit_time": "2020-01-01", "close_reason": "TIME", "ambiguous": False},
            {"pnl_r": -1.0, "exit_time": "2020-01-02", "close_reason": "SL", "ambiguous": False},
            {"pnl_r": 3.0, "exit_time": "2021-01-01", "close_reason": "TIME", "ambiguous": False},
            {"pnl_r": -1.0, "exit_time": "2021-01-02", "close_reason": "SL", "ambiguous": False},
        ]
    )

    summary = runner._summary_from_trades(trades, {"entry_id": "E1", "mask_id": "M0", "exit_id": "X0"}, "val_eval", 0.2, n_bootstrap=5)

    assert summary["effective_profit_years"] == pytest.approx(1.6)


def test_filter_trades_for_rule_selects_winner_split_and_spread():
    trades = pd.DataFrame(
        [
            {"entry_id": "E1", "mask_id": "M0", "exit_id": "X0", "split": "val_eval", "spread": 0.2, "pnl_r": 1.0},
            {"entry_id": "E1", "mask_id": "M0", "exit_id": "X0", "split": "val_select", "spread": 0.2, "pnl_r": 2.0},
            {"entry_id": "E1", "mask_id": "M0", "exit_id": "X0", "split": "val_eval", "spread": 0.4, "pnl_r": 3.0},
            {"entry_id": "E2", "mask_id": "M0", "exit_id": "X0", "split": "val_eval", "spread": 0.2, "pnl_r": 4.0},
        ]
    )

    selected = runner.filter_trades_for_rule(trades, {"entry_id": "E1", "mask_id": "M0", "exit_id": "X0"}, split="val_eval", spread=0.2)

    assert selected["pnl_r"].tolist() == [1.0]


def test_filter_trades_for_rule_matches_stop_policy():
    trades = pd.DataFrame(
        [
            {"stop_policy_id": "S0", "entry_id": "E3", "mask_id": "M0", "exit_id": "X2", "split": "val_eval", "spread": 0.2, "pnl_r": 9.0},
            {"stop_policy_id": "S1", "entry_id": "E3", "mask_id": "M0", "exit_id": "X2", "split": "val_eval", "spread": 0.2, "pnl_r": 1.0},
        ]
    )
    selected = runner.filter_trades_for_rule(trades, {"stop_policy_id": "S1", "entry_id": "E3", "mask_id": "M0", "exit_id": "X2"}, split="val_eval", spread=0.2)
    assert selected["pnl_r"].tolist() == [1.0]


def test_compute_attribution_reports_entry_mask_and_exit_effects():
    summary = pd.DataFrame(
        [
            {"entry_id": "E3", "mask_id": "M1_frozen_movement_top5", "exit_id": "X4_ml_movement_exhaustion_p0_65", "pf": 2.1},
            {"entry_id": "E3", "mask_id": "M1_frozen_movement_top5", "exit_id": "X0_fixed_r_0_7", "pf": 1.4},
            {"entry_id": "E3", "mask_id": "M0_no_mask", "exit_id": "X4_ml_movement_exhaustion_p0_65", "pf": 1.6},
            {"entry_id": "E1_simple_limit_at_fractal0", "mask_id": "M1_frozen_movement_top5", "exit_id": "X4_ml_movement_exhaustion_p0_65", "pf": 1.5},
            {"entry_id": "E3", "mask_id": "M1_frozen_movement_top5", "exit_id": "X7_time_6", "pf": 1.3},
        ]
    )
    attribution = {row["check_id"]: row for row in runner.compute_attribution(summary, {"entry_id": "E3", "mask_id": "M1_frozen_movement_top5", "exit_id": "X4_ml_movement_exhaustion_p0_65"})}
    assert attribution["A0_matched_entry_mask_baseline_exit"]["baseline_pf"] == 1.4
    assert attribution["A1_same_exit_no_mask"]["baseline_pf"] == 1.6
    assert attribution["A2_same_exit_simple_entry"]["baseline_pf"] == 1.5
    assert attribution["A4_same_entry_mask_time_exit"]["baseline_pf"] == 1.3


def test_exit_decision_rows_use_next_open_execution_time():
    trades = pd.DataFrame([{"position_id": "p1", "side": "BUY", "fill_index": 0, "entry_effective_price": 100.2, "entry_bid_equivalent": 100.0, "protective_stop_price": 99.0, "r_value": 1.2, "atr": 2.0}])
    bars = pd.DataFrame({"time": pd.to_datetime(["2021-01-01 10:00", "2021-01-01 11:00", "2021-01-01 12:00"]), "open": [100.0, 100.4, 100.6], "high": [100.3, 100.5, 100.7], "low": [99.8, 100.1, 100.3], "close": [100.2, 100.5, 100.6]})
    decisions = runner.build_exit_decision_rows(trades, bars)
    assert decisions.loc[0, "decision_bar_time"] == pd.Timestamp("2021-01-01 11:00")
    assert decisions.loc[0, "feature_available_time"] == pd.Timestamp("2021-01-01 12:00")
    assert decisions.loc[0, "decision_time"] == pd.Timestamp("2021-01-01 12:00")
    assert decisions.loc[0, "ml_decision_time"] == pd.Timestamp("2021-01-01 12:00")
    assert decisions.loc[0, "first_exit_execution_time"] == pd.Timestamp("2021-01-01 12:00")
    assert "target_exit_hold_close" not in decisions.columns


def test_exit_decision_rows_create_sequence_until_last_executable_bar():
    trades = pd.DataFrame([{"position_id": "p1", "side": "BUY", "fill_index": 0, "entry_effective_price": 100.2, "entry_bid_equivalent": 100.0, "protective_stop_price": 99.0, "r_value": 1.2, "atr": 2.0}])
    bars = pd.DataFrame({"time": pd.to_datetime(["2021-01-01 10:00", "2021-01-01 11:00", "2021-01-01 12:00", "2021-01-01 13:00"]), "open": [100.0, 100.4, 100.6, 100.7], "high": [100.3, 100.5, 100.7, 100.8], "low": [99.8, 100.1, 100.3, 100.5], "close": [100.2, 100.5, 100.6, 100.7]})
    decisions = runner.build_exit_decision_rows(trades, bars)
    assert decisions["bars_since_fill"].tolist() == [1, 2]
    assert decisions["decision_bar_time"].tolist() == list(bars["time"].iloc[1:3])
    assert decisions["feature_available_time"].tolist() == list(bars["time"].iloc[2:4])
    assert decisions["decision_time"].tolist() == list(bars["time"].iloc[2:4])
    assert decisions["first_exit_execution_time"].tolist() == list(bars["time"].iloc[2:4])


def test_exit_targets_are_named_as_future_derived_targets():
    targets = runner.build_exit_targets(pd.DataFrame({"side": ["BUY"], "entry_effective_price": [100.2], "r_value": [1.2], "future_favorable_r_3": [0.1], "future_adverse_r_3": [0.8], "close_now_pnl_r": [0.2], "hold_3_pnl_r": [-0.4]}))
    assert targets.loc[0, "target_exit_opposite_any"] == 1
    assert targets.loc[0, "target_exit_opposite_strong"] == 0
    assert targets.loc[0, "target_exit_hold_close"] == 1
    assert targets.loc[0, "target_exit_movement_exhaustion"] == 1


def test_exit_features_do_not_include_future_or_target_columns():
    cols = runner.exit_feature_columns("M1_frozen_movement_top5")
    assert not any(col.startswith(("future_", "target_")) for col in cols)
    assert {"hold_3_pnl_r", "close_now_pnl_r", "target_exit_hold_close"}.isdisjoint(cols)
    assert "movement_score" in cols
    assert "movement_score_available" in cols


def test_exit_features_exclude_future_derived_decision_fields():
    cols = set(runner.exit_feature_columns("M1_frozen_movement_top5"))

    forbidden = {
        "future_favorable_r_3",
        "future_adverse_r_3",
        "hold_3_pnl_r",
        "close_now_pnl_r",
        "target_exit_opposite_any",
        "target_exit_opposite_strong",
        "target_exit_hold_close",
        "target_exit_movement_exhaustion",
    }

    assert cols.isdisjoint(forbidden)


def test_exit_decision_rows_start_after_fill_bar_without_post_fill_decision_timestamp():
    trades = pd.DataFrame(
        [
            {
                "position_id": "p1",
                "side": "BUY",
                "fill_index": 0,
                "fill_time": pd.Timestamp("2021-01-01 10:00"),
                "entry_effective_price": 100.0,
                "r_value": 1.0,
                "ATR": 2.0,
            }
        ]
    )
    bars = pd.DataFrame(
        {
            "time": pd.to_datetime(["2021-01-01 10:00", "2021-01-01 11:00", "2021-01-01 12:00", "2021-01-01 13:00"]),
            "open": [100.0, 100.0, 100.0, 100.0],
            "high": [105.0, 101.0, 101.0, 101.0],
            "low": [95.0, 99.0, 99.0, 99.0],
            "close": [104.0, 100.0, 100.0, 100.0],
        }
    )

    decisions = runner.build_exit_decision_rows(trades, bars)

    assert 0 not in set(decisions["bars_since_fill"])
    first = decisions.iloc[0]
    assert first["bars_since_fill"] == 1
    assert first["decision_bar_time"] == pd.Timestamp("2021-01-01 11:00")
    assert first["feature_available_time"] == pd.Timestamp("2021-01-01 12:00")
    assert first["decision_time"] == pd.Timestamp("2021-01-01 12:00")
    assert first["ml_decision_time"] == pd.Timestamp("2021-01-01 12:00")
    assert first["first_exit_execution_time"] == pd.Timestamp("2021-01-01 12:00")


def test_score_map_excludes_bars_since_fill_zero():
    entries = pd.DataFrame(
        [
            {
                "position_id": "p1",
                "filled": True,
                "side": "BUY",
                "fill_index": 0,
            }
        ]
    )
    scored_decisions = pd.DataFrame(
        [
            {
                "position_id": "p1",
                "bars_since_fill": 0,
                "ml_exit_eligible": False,
                "score_target_exit_opposite_any_M0_no_mask": 0.99,
            },
            {
                "position_id": "p1",
                "bars_since_fill": 1,
                "ml_exit_eligible": True,
                "score_target_exit_opposite_any_M0_no_mask": 0.75,
            },
        ]
    )

    score_map = runner._score_map_for_entries(
        entries,
        pd.DataFrame(),
        scored_decisions,
        {"family": "ml_opposite_any"},
        "M0_no_mask",
    )

    assert score_map["p1"] == {1: 0.75}


def test_exit_features_for_no_mask_do_not_use_movement_score():
    cols = runner.exit_feature_columns("M0_no_mask")
    assert "movement_score" not in cols
    assert "movement_score_available" not in cols


def test_select_winner_requires_sample_size_and_prefers_bs_p05():
    summary = pd.DataFrame(
        [
            {"entry_id": "E1", "mask_id": "M0", "exit_id": "X0", "n_trades": 299, "pf": 3.0, "bs_p05": 2.0, "stress_pf": 2.0, "negative_years": 0, "mean_pnl_r": 0.2, "max_drawdown_r": 3.0, "effective_profit_years": 2.0, "pf_without_best_year": 1.5},
            {"entry_id": "E2", "mask_id": "M0", "exit_id": "X1", "n_trades": 350, "pf": 1.8, "bs_p05": 1.3, "stress_pf": 1.3, "negative_years": 0, "mean_pnl_r": 0.1, "max_drawdown_r": 5.0, "effective_profit_years": 2.0, "pf_without_best_year": 1.2},
            {"entry_id": "E3", "mask_id": "M0", "exit_id": "X2", "n_trades": 360, "pf": 1.7, "bs_p05": 1.4, "stress_pf": 1.3, "negative_years": 0, "mean_pnl_r": 0.1, "max_drawdown_r": 5.0, "effective_profit_years": 2.0, "pf_without_best_year": 1.2},
        ]
    )
    winner = runner.select_winner(summary)
    assert winner["entry_id"] == "E3"
    assert winner["selection_metric"] == "BS_p05"


def test_evaluate_winner_on_val_eval_uses_eval_metrics_not_select_metrics():
    winner = {"entry_id": "E3", "mask_id": "M0_no_mask", "exit_id": "X2", "val_select_pf": 2.5}
    val_eval_summary = pd.DataFrame([{"entry_id": "E3", "mask_id": "M0_no_mask", "exit_id": "X2", "pf": 1.2, "bs_p05": 0.9, "n_trades": 350, "stress_pf": 1.1, "negative_years": 0, "mean_pnl_r": 0.01, "pf_without_best_year": 1.0, "effective_profit_years": 2.0}])
    evaluated = runner.evaluate_winner_on_val_eval(winner, val_eval_summary)
    verdict = runner.decide_research_verdict(evaluated, {"status": "PASS", "empirical_p_value": 0.05})
    assert evaluated["pf"] == 1.2
    assert verdict["lifecycle_status"] == "research_hint"
    assert "val_eval_gate_failed" in verdict["reasons"]


def test_evaluate_winner_on_val_eval_matches_stop_policy():
    winner = {"stop_policy_id": "S1", "entry_id": "E3", "mask_id": "M0", "exit_id": "X2"}
    rows = pd.DataFrame(
        [
            {"stop_policy_id": "S0", "entry_id": "E3", "mask_id": "M0", "exit_id": "X2", "pf": 9.0, "bs_p05": 9.0, "n_trades": 350},
            {"stop_policy_id": "S1", "entry_id": "E3", "mask_id": "M0", "exit_id": "X2", "pf": 1.5, "bs_p05": 1.2, "n_trades": 350},
        ]
    )
    assert runner.evaluate_winner_on_val_eval(winner, rows)["pf"] == 1.5


def test_compute_stop_diagnostics_reports_source_sl_rate():
    trades = pd.DataFrame(
        [
            {"stop_policy_id": "S0", "split": "val_eval", "stop_source": "entry_floor", "close_reason": "SL", "stop_distance_atr": 0.5, "r_value": 1.0},
            {"stop_policy_id": "S0", "split": "val_eval", "stop_source": "entry_floor", "close_reason": "ML_CLOSE", "stop_distance_atr": 0.5, "r_value": 1.0},
            {"stop_policy_id": "S0", "split": "val_eval", "stop_source": "fractal0_buffer", "close_reason": "ML_CLOSE", "stop_distance_atr": 1.2, "r_value": 2.4},
        ]
    )
    rows = runner.compute_stop_diagnostics(trades)
    by_source = {(row["stop_policy_id"], row["stop_source"]): row for row in rows}
    assert by_source[("S0", "entry_floor")]["n_trades"] == 2
    assert by_source[("S0", "entry_floor")]["sl_rate"] == 0.5


def test_sample_size_warnings_marks_m1_control_as_low_n():
    summary = pd.DataFrame(
        [
            {"split": "val_eval", "mask_id": "M0_no_mask", "n_trades": 350},
            {"split": "val_eval", "mask_id": "M1_frozen_movement_top5", "n_trades": 9},
        ]
    )
    warnings = runner.sample_size_warnings(summary)
    assert warnings == [
        {
            "split": "val_eval",
            "mask_id": "M1_frozen_movement_top5",
            "warning": "low_trade_count_control_only",
            "min_n_trades": 9,
            "median_n_trades": 9.0,
            "interpretation": "do_not_compare_to_M0_as_equal_sample",
        }
    ]


def test_rejected_alternatives_discloses_baseline_and_eval_only_rows():
    summary = pd.DataFrame(
        [
            {"stop_policy_id": "S0_current_0_5", "entry_id": "E3_open_pullback_1_0atr", "mask_id": "M0_no_mask", "exit_id": "X0_fixed_r_0_7", "split": "val_eval", "n_trades": 350, "pf": 2.7, "bs_p05": 2.5, "risk_distance_atr": 0.5, "tp_distance_atr": 0.35},
            {"stop_policy_id": "S1_fractal0_buffer_0_5_entry_floor_1", "entry_id": "E3_open_pullback_1_0atr", "mask_id": "M0_no_mask", "exit_id": "X2_ml_opposite_any_p0_55", "split": "val_select", "n_trades": 350, "pf": 2.9, "bs_p05": 2.6, "risk_distance_atr": 1.0, "tp_distance_atr": None},
            {"stop_policy_id": "S3_fractal0_buffer_0_5_entry_floor_3", "entry_id": "E3_open_pullback_1_0atr", "mask_id": "M0_no_mask", "exit_id": "X2_ml_opposite_any_p0_50", "split": "val_select", "n_trades": 350, "pf": 2.7, "bs_p05": 2.4, "risk_distance_atr": 3.0, "tp_distance_atr": None},
            {"stop_policy_id": "S2_fractal0_buffer_0_5_entry_floor_2", "entry_id": "E1_simple_limit_at_fractal0", "mask_id": "M0_no_mask", "exit_id": "X2_ml_opposite_any_p0_50", "split": "val_eval", "n_trades": 350, "pf": 2.94, "bs_p05": 2.69, "risk_distance_atr": 2.0, "tp_distance_atr": None},
        ]
    )
    winner = {"stop_policy_id": "S2_fractal0_buffer_0_5_entry_floor_2", "entry_id": "E3_open_pullback_1_0atr", "mask_id": "M0_no_mask", "exit_id": "X2_ml_opposite_any_p0_50"}
    alternatives = runner.rejected_alternatives(summary, winner)
    assert {row["alternative_id"] for row in alternatives} == {
        "current_s0_fixed_r_baseline",
        "s1_neighbor_same_family",
        "s3_neighbor_same_key",
        "diagnostic_best_val_eval_s2_e1",
    }


def test_permutation_verdict_passes_when_tail_probability_is_small():
    result = runner.permutation_verdict(observed_bs_p05=1.50, null_best_bs_p05=[1.00] * 99)
    assert result["empirical_p_value"] == 0.01
    assert result["status"] == "PASS"


def test_permutation_verdict_returns_research_hint_when_tail_probability_is_large():
    result = runner.permutation_verdict(observed_bs_p05=1.10, null_best_bs_p05=[1.20] * 20 + [1.00] * 79)
    assert result["empirical_p_value"] == 0.21
    assert result["status"] == "RESEARCH_HINT"


def test_selection_permutation_returns_null_distribution_from_trades():
    trades = pd.DataFrame(
        [
            {"entry_id": "E1", "mask_id": "M0_no_mask", "exit_id": "X0", "split": "val_select", "side": "BUY", "exit_time": "2020-01-01", "pnl_r": 1.0, "ambiguous": False},
            {"entry_id": "E1", "mask_id": "M0_no_mask", "exit_id": "X0", "split": "val_select", "side": "BUY", "exit_time": "2020-01-02", "pnl_r": -0.4, "ambiguous": False},
            {"entry_id": "E2", "mask_id": "M0_no_mask", "exit_id": "X1", "split": "val_select", "side": "SELL", "exit_time": "2020-01-03", "pnl_r": -0.8, "ambiguous": False},
            {"entry_id": "E2", "mask_id": "M0_no_mask", "exit_id": "X1", "split": "val_select", "side": "SELL", "exit_time": "2020-01-04", "pnl_r": 0.2, "ambiguous": False},
        ]
    )
    summary = pd.DataFrame(
        [
            {"entry_id": "E1", "mask_id": "M0_no_mask", "exit_id": "X0", "spread": 0.2, "n_trades": 350, "pf": 2.5, "bs_p05": 1.3, "negative_years": 0, "mean_pnl_r": 0.1, "max_drawdown_r": 1.0, "pf_without_best_year": 1.2},
            {"entry_id": "E2", "mask_id": "M0_no_mask", "exit_id": "X1", "spread": 0.2, "n_trades": 350, "pf": 0.8, "bs_p05": 0.7, "negative_years": 0, "mean_pnl_r": 0.1, "max_drawdown_r": 1.0, "pf_without_best_year": 1.2},
        ]
    )

    result = runner.run_selection_permutation(summary, trades, repeats=5, seed=123, n_bootstrap=5)

    assert result["null_repeats"] == 5
    assert len(result["null_best_bs_p05"]) == 5
    assert result["method"] == "block_shuffled_val_select_pnl_r"


def test_stress_spread_does_not_choose_winner():
    canonical = pd.DataFrame(
        [
            {"entry_id": "E1", "mask_id": "M0_no_mask", "exit_id": "X0", "n_trades": 350, "pf": 1.6, "bs_p05": 1.20, "stress_pf": 0.80, "negative_years": 0, "mean_pnl_r": 0.1, "max_drawdown_r": 5.0, "effective_profit_years": 2.0, "pf_without_best_year": 1.2},
            {"entry_id": "E2", "mask_id": "M0_no_mask", "exit_id": "X1", "n_trades": 350, "pf": 1.5, "bs_p05": 1.10, "stress_pf": 2.50, "negative_years": 0, "mean_pnl_r": 0.1, "max_drawdown_r": 5.0, "effective_profit_years": 2.0, "pf_without_best_year": 1.2},
        ]
    )
    assert runner.select_winner(canonical)["entry_id"] == "E1"
