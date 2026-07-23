from pathlib import Path

import pandas as pd

from ML.baseline import audit_leaderboard_closure as closure
from ML.baseline import audit_leaderboard_robustness as leaderboard


def test_closure_reuses_exact_11_leaderboard_rules():
    assert closure.LEADERBOARD_RULES is leaderboard.LEADERBOARD_RULES
    assert len(closure.LEADERBOARD_RULES) == 11
    assert [rule.original_rank for rule in closure.LEADERBOARD_RULES] == list(range(1, 12))
    assert closure.CLOSURE_SCOPE == "validation_artifact_leaderboard_cost_calendar_sequential_multiseed_closure"


def test_closure_global_statuses_exclude_provider_and_transfer():
    statuses = closure.default_closure_statuses()

    assert statuses["locked_test_status"] == "not_opened"
    assert statuses["provider_drift_status"] == "NOT_IN_SCOPE"
    assert statuses["transfer_status"] == "NOT_IN_SCOPE"
    assert statuses["allowed_max_verdict"] == "research_only"


def test_contract_result_preserves_original_rank_order():
    rows = []
    for rule in leaderboard.LEADERBOARD_RULES:
        for split in ["val_select", "val_eval"]:
            rows.append(
                {
                    "stop_policy_id": leaderboard.STOP_POLICY_ID,
                    "entry_id": leaderboard.ENTRY_ID,
                    "mask_id": leaderboard.MASK_ID,
                    "exit_id": leaderboard.EXIT_ID,
                    "spread": leaderboard.CANONICAL_SPREAD,
                    "split": split,
                    "profile_id": rule.profile_id,
                    "model_id": rule.model_id,
                    "target_id": rule.target_id,
                    "filter_id": rule.filter_id,
                    "entry_filter_score_col": leaderboard.ENTRY_FILTER_SCORE_COL,
                    "score_cutoff_on_val_select": -0.02,
                    "n_trades": 500,
                    "pf": 2.0,
                    "bs_p05": 1.5,
                    "eligible_for_winner": True,
                    "not_eligible_for_winner": False,
                    "not_eligible_reason": "",
                }
            )
    contract = closure.verify_leaderboard_contract(pd.DataFrame(rows), closure.LEADERBOARD_RULES)

    assert contract["original_rank"].tolist() == list(range(1, 12))


def test_stress_cost_grid_marks_uncomputable_without_resimulation_path():
    contract_row = {"original_rank": 1, "rule_id": "rank01", "profile_id": "time_only"}
    trades = pd.DataFrame(
        {
            "position_id": ["a"],
            "pnl_r": [1.0],
            "spread": [0.2],
            "entry_effective_price": [100.0],
            "exit_price": [101.0],
            "side": ["BUY"],
        }
    )

    result = closure.stress_cost_grid_for_rule(trades, contract_row)

    assert set(result["stress_multiplier"]) == {1.0, 2.0, 3.0, 4.0}
    assert set(result["status"]) == {"NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS"}
    assert "requires explicit resimulation" in result["reason"].iloc[0]


def test_cost_model_disclosure_lists_non_spread_costs():
    result = closure.cost_model_disclosure_for_rule({"original_rank": 1, "rule_id": "rank01"})

    assert {
        "commission",
        "swap",
        "slippage",
        "requote_open_failure",
        "latency",
        "position_limits",
    }.issubset(set(result["cost_component"]))
    assert set(result.loc[result["cost_component"].ne("spread"), "status"]) == {"NOT_IN_SCOPE"}


def test_time_calendar_for_rule_covers_signal_fill_exit_and_hour_month():
    contract_row = {"original_rank": 1, "rule_id": "rank01"}
    trades = pd.DataFrame(
        [
            {
                "signal_time": "2021-01-01 02:00",
                "fill_time": "2021-01-01 03:00",
                "exit_time": "2021-01-02 04:00",
                "pnl_r": 1.0,
            },
            {
                "signal_time": "2021-02-01 02:00",
                "fill_time": "2021-02-01 03:00",
                "exit_time": "2021-02-02 04:00",
                "pnl_r": -0.5,
            },
        ]
    )

    result = closure.time_calendar_for_rule(trades, contract_row)

    assert {"signal_time", "fill_time", "exit_time"}.issubset(set(result["time_basis"]))
    assert {"month", "weekday", "hour"}.issubset(set(result["calendar_field"]))
    assert set(result["rule_id"]) == {"rank01"}
    assert "n_trades_gate_status" in result.columns
    assert set(result["n_trades_gate_status"]) == {"LOW_N_LT_30"}


def test_calendar_permutation_importance_is_explicitly_uncomputable_without_fitted_estimator():
    result = closure.calendar_permutation_importance_for_rule({}, {"original_rank": 1, "rule_id": "rank01"})

    assert result["status"].tolist() == ["NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS"]
    assert "fitted estimator" in result["reason"].iloc[0]


def test_timezone_shift_is_not_faked_from_saved_scores():
    result = closure.timezone_shift_for_rule(
        pd.DataFrame({"rich_entry_score": [0.1]}),
        {"original_rank": 1, "rule_id": "rank01"},
    )

    assert set(result["shift_hours"]) == {-8, -4, 4, 8}
    assert set(result["status"]) == {"NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS"}
    assert "requires frozen rescore" in result["reason"].iloc[0]


def test_sequential_positions_uses_fill_time_not_signal_time():
    contract_row = {"original_rank": 1, "rule_id": "rank01"}
    trades = pd.DataFrame(
        [
            {
                "position_id": "a",
                "signal_time": "2021-01-01 00:00",
                "fill_time": "2021-01-01 02:00",
                "exit_time": "2021-01-01 03:00",
                "pnl_r": 1.0,
            },
            {
                "position_id": "b",
                "signal_time": "2021-01-01 01:00",
                "fill_time": "2021-01-01 03:30",
                "exit_time": "2021-01-01 04:00",
                "pnl_r": 1.0,
            },
            {"position_id": "c", "signal_time": "2021-01-01 04:00", "exit_time": "2021-01-01 05:00", "pnl_r": -0.5},
        ]
    )

    result = closure.sequential_positions_for_rule(trades, contract_row)
    single = result.loc[result["position_policy"].eq("single_position")].iloc[0]

    assert single["n_trades"] == 3
    assert single["dropped_trades"] == 0
    assert single["status"] == "COMPUTED"
    assert single["interval_basis"] == "fill_time"


def test_sequential_positions_marks_signal_time_fallback_when_fill_time_missing():
    contract_row = {"original_rank": 1, "rule_id": "rank01"}
    trades = pd.DataFrame(
        [
            {"position_id": "a", "signal_time": "2021-01-01 00:00", "exit_time": "2021-01-01 03:00", "pnl_r": 1.0},
            {"position_id": "b", "signal_time": "2021-01-01 01:00", "exit_time": "2021-01-01 04:00", "pnl_r": -0.5},
        ]
    )

    result = closure.sequential_positions_for_rule(trades, contract_row)

    assert set(result["interval_basis"]) == {"signal_time_fallback"}
    assert set(result["status"]) == {"COMPUTED_WITH_SIGNAL_TIME_FALLBACK"}


def test_multiseed_status_is_not_computable_when_seed_artifacts_absent():
    result = closure.multiseed_for_rule({}, {"original_rank": 1, "rule_id": "rank01"})

    assert set(result["seed"]) == {41, 42, 43, 44, 45}
    assert set(result["status"]) == {"NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS"}
    assert "persisted per-seed" in result["reason"].iloc[0]


def test_bounded_multiseed_rerun_contract_has_fixed_11_rule_universe():
    contract = closure.bounded_multiseed_rerun_contract()

    assert contract["seeds"] == [41, 42, 43, 44, 45]
    assert contract["rule_count"] == 11
    assert contract["new_search_allowed"] is False
    assert contract["locked_test"] == "not_opened"


def test_input_artifacts_for_prefix_records_sha256(tmp_path):
    prefix = tmp_path / "sample"
    for suffix in [".json", "_summary.csv", "_trades.csv", "_scores.csv"]:
        path = prefix.with_suffix(suffix) if suffix == ".json" else prefix.with_name(prefix.name + suffix)
        path.write_text("x", encoding="utf-8")

    result = closure.input_artifacts_for_prefix(prefix)

    assert set(result) == {"artifact_json", "summary_csv", "trades_csv", "scores_csv"}
    assert all(len(item["sha256"]) == 64 for item in result.values())


def test_build_closure_classification_preserves_rank_and_blocks_winner_selection():
    rules = pd.DataFrame(
        [
            {"original_rank": 2, "rule_id": "rank02"},
            {"original_rank": 1, "rule_id": "rank01"},
        ]
    )
    stress = pd.DataFrame({"rule_id": ["rank01"], "status": ["NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS"]})
    calendar = pd.DataFrame({"rule_id": ["rank01"], "status": ["COMPUTED"]})
    calendar_permutation = pd.DataFrame({"rule_id": ["rank01"], "status": ["NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS"]})
    calendar_no_ml = pd.DataFrame({"rule_id": ["rank01"], "status": ["NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS"]})
    timezone = pd.DataFrame({"rule_id": ["rank01"], "status": ["NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS"]})
    sequential = pd.DataFrame({"rule_id": ["rank01"], "status": ["COMPUTED"]})
    multiseed = pd.DataFrame({"rule_id": ["rank01"], "status": ["NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS"]})

    result = closure.build_closure_classification(
        rules,
        stress,
        calendar,
        calendar_permutation,
        calendar_no_ml,
        timezone,
        sequential,
        multiseed,
    )

    assert result["original_rank"].tolist() == [1, 2]
    assert set(result["new_winner_selected"]) == {False}
    assert set(result["allowed_max_verdict"]) == {"research_only"}
    assert "stress_costs_missing" in result.loc[result["rule_id"].eq("rank02"), "reasons"].iloc[0]
