import pytest
import pandas as pd

from ML.baseline import audit_time_only_robustness as audit


def _winner_payload(profile_id: str = "time_only") -> dict[str, object]:
    return {
        "stop_policy_id": "S2_fractal0_buffer_0_5_entry_floor_2",
        "entry_id": "E3_open_pullback_1_0atr",
        "mask_id": "M0_no_mask",
        "exit_id": "X2_ml_opposite_any_p0_50",
        "spread": 0.2,
        "profile_id": profile_id,
        "model_id": "linear",
        "target_id": "target_entry_ev_regression",
        "filter_id": "top30",
        "entry_filter_score_col": "rich_entry_score",
        "score_cutoff_on_val_select": -0.026718184259660646,
    }


def test_verify_fixed_rule_contract_accepts_normalized_time_only_winner():
    artifact = {
        "locked_test": "not_opened",
        "feature_contract_variant": "normalized_atr_unit",
        "selected_winner": _winner_payload(),
        "selected_winner_val_eval": _winner_payload(),
    }
    result = audit.verify_fixed_rule_contract(artifact, audit.EXPECTED_RULE)
    assert result["status"] == "PASS"
    assert result["checks"]["selected_winner"]["status"] == "PASS"
    assert result["checks"]["selected_winner_val_eval"]["status"] == "PASS"


def test_verify_fixed_rule_contract_blocks_locked_test_or_changed_rule():
    artifact = {
        "locked_test": "opened",
        "feature_contract_variant": "normalized_atr_unit",
        "selected_winner": _winner_payload(),
        "selected_winner_val_eval": _winner_payload("movement_plus_time"),
    }
    with pytest.raises(ValueError, match="fixed rule contract"):
        audit.verify_fixed_rule_contract(artifact, audit.EXPECTED_RULE)


def test_verify_fixed_rule_contract_blocks_changed_val_select_winner():
    artifact = {
        "locked_test": "not_opened",
        "feature_contract_variant": "normalized_atr_unit",
        "selected_winner": _winner_payload("movement_plus_time"),
        "selected_winner_val_eval": _winner_payload(),
    }
    with pytest.raises(ValueError, match="fixed rule contract"):
        audit.verify_fixed_rule_contract(artifact, audit.EXPECTED_RULE)


def test_period_side_and_profit_concentration_metrics():
    trades = pd.DataFrame(
        {
            "split": ["val_eval"] * 6,
            "profile_id": ["time_only"] * 6,
            "model_id": ["linear"] * 6,
            "target_id": ["target_entry_ev_regression"] * 6,
            "filter_id": ["top30"] * 6,
            "side": ["BUY", "BUY", "SELL", "SELL", "BUY", "SELL"],
            "exit_time": pd.to_datetime(
                ["2021-01-02", "2021-02-03", "2021-04-04", "2022-01-05", "2022-05-06", "2022-07-07"]
            ),
            "pnl_r": [1.0, -0.5, 0.8, 0.6, -0.2, 0.4],
            "close_reason": ["TP", "SL", "TP", "ML_CLOSE", "SL", "TP"],
        }
    )
    yearly = audit.metrics_by_period(trades, "Y")
    side = audit.metrics_by_side(trades)
    concentration = audit.profit_concentration(trades)

    assert set(yearly["period"]) == {"2021", "2022"}
    assert set(side["side"]) == {"BUY", "SELL"}
    assert concentration["n_years"] == 2
    assert concentration["effective_profit_years"] > 1.0
    assert concentration["best_year_share"] < 1.0


def test_score_shift_and_stricter_cutoff_use_fixed_rule_only():
    scores = pd.DataFrame(
        {
            "split": ["val_select", "val_select", "val_eval", "val_eval"],
            "profile_id": ["time_only"] * 4,
            "model_id": ["linear"] * 4,
            "target_id": ["target_entry_ev_regression"] * 4,
            "filter_id": ["top30"] * 4,
            "position_id": ["a", "b", "c", "d"],
            "rich_entry_score": [-0.01, -0.04, -0.02, -0.05],
        }
    )
    trades = pd.DataFrame(
        {
            "split": ["val_eval", "val_eval"],
            "profile_id": ["time_only", "time_only"],
            "model_id": ["linear", "linear"],
            "target_id": ["target_entry_ev_regression", "target_entry_ev_regression"],
            "filter_id": ["top30", "top30"],
            "position_id": ["c", "d"],
            "side": ["BUY", "SELL"],
            "exit_time": pd.to_datetime(["2022-01-01", "2022-01-02"]),
            "pnl_r": [1.0, -0.5],
            "close_reason": ["TP", "SL"],
        }
    )

    shift = audit.score_shift(scores, audit.EXPECTED_RULE)
    sensitivity = audit.stricter_cutoff_sensitivity(scores, trades, audit.EXPECTED_RULE, offsets=[0.0, 0.02])

    assert set(shift["split"]) == {"val_select", "val_eval"}
    assert set(sensitivity["cutoff_offset"]) == {0.0, 0.02}
    assert sensitivity.loc[sensitivity["cutoff_offset"].eq(0.0), "n_trades"].iloc[0] == 1


def test_sequential_block_bootstrap_preserves_adjacent_blocks():
    trades = pd.DataFrame({"pnl_r": [1.0, 2.0, -1.0, -2.0, 3.0, -3.0]})
    sample = audit._sequential_block_sample_indices(len(trades), seed=7, block_size=2)
    assert len(sample) == len(trades)
    assert all((sample[i + 1] - sample[i]) % len(trades) == 1 for i in range(0, len(sample), 2))


def test_topk_sensitivity_uses_saved_top30_top40_top50_trades():
    base_cols = {
        "stop_policy_id": "S2_fractal0_buffer_0_5_entry_floor_2",
        "entry_id": "E3_open_pullback_1_0atr",
        "mask_id": "M0_no_mask",
        "exit_id": "X2_ml_opposite_any_p0_50",
        "spread": 0.2,
        "split": "val_eval",
        "profile_id": "time_only",
        "model_id": "linear",
        "target_id": "target_entry_ev_regression",
    }
    trades = pd.DataFrame(
        {
            **{key: [value, value, value] for key, value in base_cols.items()},
            "filter_id": ["top30", "top40", "top50"],
            "pnl_r": [1.0, 0.5, -0.25],
            "close_reason": ["TP", "TP", "SL"],
        }
    )
    result = audit.topk_sensitivity(trades, audit.EXPECTED_RULE)
    assert set(result["filter_id"]) == {"top30", "top40", "top50"}


def test_robustness_decision_requires_stress_and_catches_bad_side():
    selected_summary = {"n_trades": 660, "pf": 4.0, "bs_p05": 3.3, "pf_without_best_year": 3.5}
    concentration = {"n_years": 2, "effective_profit_years": 1.99, "best_year_share": 0.55}
    side = pd.DataFrame({"side": ["BUY", "SELL"], "n_trades": [330, 330], "mean_pnl_r": [0.2, 0.3], "pf": [2.0, 3.0]})
    stricter_cutoff = pd.DataFrame({"cutoff_offset": [0.0, 0.01], "pf": [4.0, 3.2], "n_trades": [660, 620]})
    topk = pd.DataFrame({"filter_id": ["top30", "top40", "top50"], "pf": [4.0, 3.4, 3.0], "n_trades": [660, 880, 1100]})
    spread_stress = pd.DataFrame({"status": ["NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS"]})
    sequential = pd.DataFrame({"status": ["NOT_RUN"]})

    result = audit.robustness_decision(selected_summary, concentration, side, stricter_cutoff, topk, spread_stress, sequential)
    assert result["decision"] == "REGIME_REFORMULATION_REQUIRED"
    assert "stress_costs_not_computable" in result["reasons"]
    assert "sequential_position_constraint_not_run" not in result["reasons"]
    assert "sequential_position_constraint_not_run" in result["disclosures"]
    assert "concentration" in result["decision_gate_config"]
    assert "topk" in result["decision_gate_config"]

    bad_side = pd.DataFrame({"side": ["BUY", "SELL"], "n_trades": [620, 40], "mean_pnl_r": [0.2, -0.1], "pf": [3.0, 0.8]})
    result = audit.robustness_decision(selected_summary, concentration, bad_side, stricter_cutoff, topk, spread_stress, sequential)
    assert result["decision"] == "REGIME_REFORMULATION_REQUIRED"


def test_calendar_no_ml_baselines_reports_missing_unfiltered_baseline():
    trades = pd.DataFrame(
        {
            "stop_policy_id": ["S2_fractal0_buffer_0_5_entry_floor_2"],
            "entry_id": ["E3_open_pullback_1_0atr"],
            "mask_id": ["M0_no_mask"],
            "exit_id": ["X2_ml_opposite_any_p0_50"],
            "spread": [0.2],
            "split": ["val_eval"],
            "profile_id": ["time_only"],
            "model_id": ["linear"],
            "target_id": ["target_entry_ev_regression"],
            "filter_id": ["top30"],
            "exit_time": pd.to_datetime(["2022-01-01"]),
            "pnl_r": [1.0],
            "close_reason": ["TP"],
        }
    )

    result = audit.calendar_no_ml_baselines(trades, audit.EXPECTED_RULE)

    assert result["status"].iloc[0] == "NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS"
    assert "unfiltered" in result["reason"].iloc[0]


def test_calendar_slices_include_entry_fill_and_exit_time_basis():
    base_cols = {
        "stop_policy_id": "S2_fractal0_buffer_0_5_entry_floor_2",
        "entry_id": "E3_open_pullback_1_0atr",
        "mask_id": "M0_no_mask",
        "exit_id": "X2_ml_opposite_any_p0_50",
        "spread": 0.2,
        "split": "val_eval",
        "profile_id": "time_only",
        "model_id": "linear",
        "target_id": "target_entry_ev_regression",
        "filter_id": "top30",
    }
    trades = pd.DataFrame(
        {
            **{key: [value, value] for key, value in base_cols.items()},
            "signal_time": pd.to_datetime(["2022-01-31 23:00", "2022-02-01 00:00"]),
            "fill_time": pd.to_datetime(["2022-02-01 01:00", "2022-02-01 02:00"]),
            "exit_time": pd.to_datetime(["2022-02-01 03:00", "2022-03-01 00:00"]),
            "pnl_r": [1.0, -0.5],
            "close_reason": ["TP", "SL"],
        }
    )

    result = audit.calendar_slices(trades, audit.EXPECTED_RULE)

    assert set(result["time_basis"]) == {"signal_time", "fill_time", "exit_time"}
    assert {"month", "quarter"}.issubset(set(result["calendar_field"]))


def test_input_artifact_metadata_records_size_and_sha256(tmp_path):
    prefix = tmp_path / "artifact"
    for suffix, content in {
        ".json": "{}",
        "_summary.csv": "a;b\n1;2\n",
        "_trades.csv": "a;b\n1;2\n",
        "_scores.csv": "a;b\n1;2\n",
    }.items():
        path = prefix.with_suffix(suffix) if suffix == ".json" else prefix.with_name(prefix.name + suffix)
        path.write_text(content, encoding="utf-8")

    result = audit.input_artifact_metadata(prefix)

    assert set(result) == {"json", "summary_csv", "trades_csv", "scores_csv"}
    assert all(item["size_bytes"] > 0 and len(item["sha256"]) == 64 for item in result.values())
