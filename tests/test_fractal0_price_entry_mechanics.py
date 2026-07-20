import pandas as pd

import ML.baseline.benchmark_fractal0_price_entry_mechanics as runner


def test_parse_fractal0_extracts_time_price_direction_and_shift():
    value = "1700000000:2030.5:-1:0.1:0.2:0:0:0:0.3:1:0.4:1:2:3:4:5:6:0.7:0.8:0.9:1.0:2.5:2"

    parsed = runner.parse_fractal0(value)

    assert parsed == {
        "time": 1700000000,
        "price": 2030.5,
        "direction": -1,
        "shift": 2,
    }


def test_trade_side_from_fractal_direction_uses_project_contract():
    assert runner.trade_side_from_fractal_direction(-1) == "BUY"
    assert runner.trade_side_from_fractal_direction(1) == "SELL"
    assert runner.trade_side_from_fractal_direction(0) is None
    assert runner.trade_side_from_fractal_direction(float("nan")) is None


def test_fractal0_entry_config_discloses_verdict_lifecycle_and_budget():
    config = runner.fractal0_entry_config()

    assert config["experiment"] == "fractal0_price_entry_mechanics"
    assert config["research_level"] == "search"
    assert config["initial_lifecycle_status"] == "research_scan"
    assert config["lifecycle_if_gate_pass"] == "research_hypothesis"
    assert config["allowed_max_verdict"] == "research_only"
    assert config["verdict_if_gate_pass"] == "research_only"
    assert config["entry_price_modes"] == ["limit_at_fractal0", "zone_edge"]
    assert config["zone_width_atr"] == [0.0, 0.25, 0.5]
    assert config["max_fill_lag_bars"] == [3, 6]
    assert config["horizons"] == [3, 6, 12]
    assert config["spread_values"] == [0.0, 0.2, 0.4]
    assert config["side_rule"] == "direction = -fractal0.dir"
    assert config["current_search_budget"] == 108
    assert config["prior_search_budget_lower_bound"] == 76
    assert config["cumulative_search_budget_lower_bound"] == 184
    assert config["locked_test"] == "not_opened"


def test_audit_side_contract_requires_real_distribution():
    rows = pd.DataFrame({"fractal0_direction": [1, -1, 1, -1]})

    audit = runner.audit_side_contract(rows)

    assert audit["status"] == "PASS"
    assert audit["direction_counts"] == {"-1": 2, "1": 2}
    assert audit["required_before_research_only"] is True


def test_audit_side_contract_fails_when_only_one_direction_present():
    rows = pd.DataFrame({"fractal0_direction": [-1, -1, -1]})

    audit = runner.audit_side_contract(rows)

    assert audit["status"] == "FAIL"
    assert audit["direction_counts"] == {"-1": 3}
    assert audit["has_both_directions"] is False


def _ohlc_frame():
    return runner.next_open.prepare_ohlc(pd.DataFrame({
        "time": [
            "2021.01.01 10:00",
            "2021.01.01 11:00",
            "2021.01.01 12:00",
            "2021.01.01 13:00",
            "2021.01.01 14:00",
        ],
        "open": [101.0, 102.0, 100.5, 103.0, 104.0],
        "high": [102.0, 103.0, 101.0, 106.0, 105.0],
        "low": [100.0, 101.0, 99.75, 102.0, 103.0],
    }))


def test_first_order_eligible_index_skips_first_bar_after_signal_time():
    ohlc = _ohlc_frame()

    idx = runner.first_order_eligible_index(
        signal_time=pd.Timestamp("2021-01-01 10:00"),
        ohlc=ohlc,
        offset=1,
    )

    assert idx == 2


def test_limit_at_fractal0_requires_level_cross():
    fill = runner.resolve_retest_zone_fill(
        signal_time=pd.Timestamp("2021-01-01 10:00"),
        fractal0_price=100.0,
        atr=2.0,
        zone_width_atr=0.25,
        max_fill_lag_bars=3,
        entry_price_mode="limit_at_fractal0",
        ohlc=_ohlc_frame(),
    )

    assert fill["filled"] is True
    assert fill["fill_time"] == pd.Timestamp("2021-01-01 12:00")
    assert fill["entry_price"] == 100.0


def test_zone_edge_uses_reachable_edge_when_center_not_crossed():
    fill = runner.resolve_retest_zone_fill(
        signal_time=pd.Timestamp("2021-01-01 10:00"),
        fractal0_price=100.0,
        atr=2.0,
        zone_width_atr=0.25,
        max_fill_lag_bars=3,
        entry_price_mode="zone_edge",
        ohlc=_ohlc_frame(),
    )

    assert fill["filled"] is True
    assert fill["entry_price"] == 100.0

    edge_fill = runner.resolve_retest_zone_fill(
        signal_time=pd.Timestamp("2021-01-01 10:00"),
        fractal0_price=99.5,
        atr=2.0,
        zone_width_atr=0.25,
        max_fill_lag_bars=3,
        entry_price_mode="zone_edge",
        ohlc=_ohlc_frame(),
    )

    assert edge_fill["filled"] is True
    assert edge_fill["entry_price"] == 100.0


def test_compute_future_updn_from_fill_uses_fill_price_and_horizon():
    up, dn = runner.compute_future_updn_from_fill(
        fill_index=2,
        horizon=2,
        ohlc=_ohlc_frame(),
        entry_price=100.0,
    )

    assert up == 6.0
    assert dn == 0.25


def test_build_retest_rows_adds_fill_and_target_columns_without_trade_exit():
    rows = pd.DataFrame({
        "time": ["2021.01.01 10:00"],
        "ATR": [2.0],
        "fractal0": ["1609491600:100.0:1:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:1.0:2"],
    })

    out = runner.build_retest_rows(
        rows,
        _ohlc_frame(),
        zone_width_atr=0.25,
        max_fill_lag_bars=3,
        entry_price_mode="limit_at_fractal0",
        horizons=(1, 2),
    )

    assert out.loc[0, "side"] == "SELL"
    assert bool(out.loc[0, "filled"]) is True
    assert out.loc[0, "target_entry_up_1"] == 1.0
    assert out.loc[0, "target_entry_dn_1"] == 0.25
    assert out.loc[0, "target_entry_up_2"] == 6.0
    assert out.loc[0, "target_entry_dn_2"] == 0.25
    assert "pnl_price" not in out.columns


def test_compute_oracle_mfe_rows_uses_favorable_and_adverse_not_trade_result():
    rows = pd.DataFrame({
        "filled": [True, True],
        "side": ["BUY", "SELL"],
        "target_entry_up_3": [3.0, 1.0],
        "target_entry_dn_3": [1.0, 4.0],
        "time": ["2021.01.01 10:00", "2021.01.02 10:00"],
    })

    events = runner.compute_oracle_mfe_rows(rows, horizon=3, spread=0.2)

    assert events.loc[0, "oracle_favorable_move_after_cost"] == 2.8
    assert events.loc[0, "oracle_adverse_move"] == 1.0
    assert events.loc[1, "oracle_favorable_move_after_cost"] == 3.8
    assert events.loc[1, "oracle_adverse_move"] == 1.0
    assert "pnl_price" not in events.columns
    assert "pf" not in events.columns


def test_summarize_mfe_metrics_reports_ratio_and_no_fill_context():
    events = pd.DataFrame({
        "oracle_favorable_move_after_cost": [2.0, -0.1, 3.0, 0.5],
        "oracle_adverse_move": [1.0, 2.0, 1.0, 0.5],
        "time": pd.to_datetime(["2021-01-01", "2021-02-01", "2022-01-01", "2023-01-01"]),
    })

    summary = runner.summarize_mfe_metrics(events, rows_total=10, rows_filled=4)

    assert summary["filled_events"] == 4
    assert summary["no_fill_rate"] == 0.6
    assert summary["favorable_sum_after_cost"] == 5.4
    assert summary["adverse_sum"] == 4.5
    assert round(summary["favorable_to_adverse_ratio"], 6) == round(5.4 / 4.5, 6)
    assert summary["active_years"] == 3


def test_ratio_without_best_year_removes_year_with_best_ratio_not_best_sum():
    events = pd.DataFrame({
        "oracle_favorable_move_after_cost": [100.0, 1.0, 10.0],
        "oracle_adverse_move": [100.0, 0.1, 5.0],
        "time": pd.to_datetime(["2021-01-01", "2022-01-01", "2023-01-01"]),
    })

    summary = runner.summarize_mfe_metrics(events, rows_total=3, rows_filled=3)

    assert summary["best_year_by_ratio"] == 2022
    assert round(summary["ratio_without_best_year"], 6) == round(110.0 / 105.0, 6)


def test_research_gate_ignores_zero_spread_and_requires_side_contract_pass():
    selected_train = {"spread": 0.2, "favorable_to_adverse_ratio": 1.20, "filled_events": 500}
    eval_summary = {
        "spread": 0.2,
        "filled_events": 200,
        "filled_events_per_year_min": 40,
        "active_years": 3,
        "no_fill_rate": 0.50,
        "favorable_to_adverse_ratio": 1.08,
        "ratio_without_best_year": 1.00,
        "stress_favorable_to_adverse_ratio": 0.96,
        "dummy_or_simple_rule_comparison": {"status": "PASS"},
    }
    side_contract_audit = {"status": "PASS"}

    gate = runner.research_gate(selected_train, eval_summary, side_contract_audit)

    assert gate["passes"] is True
    assert gate["verdict_if_pass"] == "research_only"
    assert gate["lifecycle_if_pass"] == "research_hypothesis"


def test_research_gate_blocks_failed_side_contract():
    gate = runner.research_gate(
        {"spread": 0.2, "favorable_to_adverse_ratio": 9.0, "filled_events": 999},
        {
            "spread": 0.2,
            "filled_events": 999,
            "filled_events_per_year_min": 999,
            "active_years": 9,
            "no_fill_rate": 0.01,
            "favorable_to_adverse_ratio": 9.0,
            "ratio_without_best_year": 9.0,
            "stress_favorable_to_adverse_ratio": 9.0,
            "dummy_or_simple_rule_comparison": {"status": "PASS"},
        },
        {"status": "FAIL"},
    )

    assert gate["passes"] is False
    assert gate["checks"]["side_contract_status"] is False


def test_research_gate_requires_dummy_or_simple_rule_comparison():
    selected_train = {"spread": 0.2, "favorable_to_adverse_ratio": 1.20, "filled_events": 500}
    eval_summary = {
        "spread": 0.2,
        "filled_events": 200,
        "filled_events_per_year_min": 40,
        "active_years": 3,
        "no_fill_rate": 0.50,
        "favorable_to_adverse_ratio": 1.08,
        "ratio_without_best_year": 1.00,
        "stress_favorable_to_adverse_ratio": 0.96,
    }

    gate = runner.research_gate(selected_train, eval_summary, {"status": "PASS"})

    assert gate["passes"] is False
    assert gate["checks"]["dummy_or_simple_rule_comparison"] is False


def test_select_best_rule_uses_train_core_only_and_ignores_zero_spread():
    summary = {
        "train_core": {
            "rule_a_spread_0.0": {"spread": 0.0, "favorable_to_adverse_ratio": 99.0},
            "rule_b_spread_0.2": {"spread": 0.2, "favorable_to_adverse_ratio": 1.10},
            "rule_c_spread_0.2": {"spread": 0.2, "favorable_to_adverse_ratio": 1.20},
        },
        "val_stop": {
            "rule_z_spread_0.2": {"spread": 0.2, "favorable_to_adverse_ratio": 2.00},
        },
    }

    selected = runner.select_best_train_rule(summary)

    assert selected["key"] == "rule_c_spread_0.2"
    assert selected["selection_split"] == "train_core"


def test_validate_report_requires_research_first_fields():
    report = {"experiment": "fractal0_price_entry_mechanics"}

    missing = runner.validate_report(report)

    assert "verdict" in missing
    assert "lifecycle_status" in missing
    assert "allowed_max_verdict" in missing
    assert "cumulative_search_budget_lower_bound" in missing
    assert "target_contract" in missing
    assert "execution_contract" in missing
    assert "forbidden_interpretations" in missing


def test_build_arg_parser_accepts_fractal0_entry_mechanics():
    parser = runner.build_arg_parser()

    args = parser.parse_args(["--fractal0-entry-mechanics"])

    assert args.fractal0_entry_mechanics is True
