import pandas as pd
import pytest

from ML.baseline import audit_leaderboard_robustness as audit


def _contract_rows():
    rows = []
    for rule in audit.LEADERBOARD_RULES:
        for split in ["val_select", "val_eval"]:
            rows.append(
                {
                    "stop_policy_id": audit.STOP_POLICY_ID,
                    "entry_id": audit.ENTRY_ID,
                    "mask_id": audit.MASK_ID,
                    "exit_id": audit.EXIT_ID,
                    "spread": audit.CANONICAL_SPREAD,
                    "split": split,
                    "profile_id": rule.profile_id,
                    "model_id": rule.model_id,
                    "target_id": rule.target_id,
                    "filter_id": rule.filter_id,
                    "entry_filter_score_col": "rich_entry_score",
                    "score_cutoff_on_val_select": -0.01 - rule.original_rank / 1000,
                    "n_trades": 100 + rule.original_rank,
                    "pf": 2.0,
                    "bs_p05": 1.5,
                    "mean_pnl_r": 0.1,
                    "max_drawdown_r": 1.0,
                    "pf_without_best_year": 1.2,
                    "effective_profit_years": 2.0,
                    "n_years": 2,
                    "eligible_for_winner": True,
                    "not_eligible_for_winner": False,
                    "not_eligible_reason": "",
                }
            )
    return rows


def test_fixed_audit_input_manifest_has_exact_11_rows_and_anchor_first():
    assert len(audit.LEADERBOARD_RULES) == 11
    assert audit.LEADERBOARD_RULES[0].original_rank == 1
    assert audit.LEADERBOARD_RULES[0].profile_id == "time_only"
    assert audit.LEADERBOARD_RULES[0].model_id == "linear"
    assert audit.LEADERBOARD_RULES[0].target_id == "target_entry_ev_regression"
    assert audit.LEADERBOARD_RULES[0].filter_id == "top30"
    assert [rule.original_rank for rule in audit.LEADERBOARD_RULES] == list(range(1, 12))


def test_global_artifact_contract_blocks_locked_test_or_legacy_contract():
    good = {"locked_test": "not_opened", "feature_contract_variant": "normalized_atr_unit"}
    assert audit.verify_global_artifact_contract(good)["status"] == "PASS"

    with pytest.raises(ValueError, match="locked_test"):
        audit.verify_global_artifact_contract({"locked_test": "opened", "feature_contract_variant": "normalized_atr_unit"})

    with pytest.raises(ValueError, match="feature_contract_variant"):
        audit.verify_global_artifact_contract({"locked_test": "not_opened", "feature_contract_variant": "legacy_rich"})


def test_leaderboard_contract_requires_exact_val_select_and_val_eval_rows():
    summary = pd.DataFrame(_contract_rows())

    result = audit.verify_leaderboard_contract(summary, audit.LEADERBOARD_RULES)

    assert len(result) == 11
    assert set(result["contract_status"]) == {"PASS"}
    assert set(result["split_pair_status"]) == {"PASS"}


def test_leaderboard_contract_fails_when_a_fixed_input_row_is_missing():
    summary = pd.DataFrame(
        [
            {
                "stop_policy_id": audit.STOP_POLICY_ID,
                "entry_id": audit.ENTRY_ID,
                "mask_id": audit.MASK_ID,
                "exit_id": audit.EXIT_ID,
                "spread": audit.CANONICAL_SPREAD,
                "split": "val_select",
                "profile_id": "time_only",
                "model_id": "linear",
                "target_id": "target_entry_ev_regression",
                "filter_id": "top30",
                "entry_filter_score_col": "rich_entry_score",
                "score_cutoff_on_val_select": -0.026718184259660646,
            }
        ]
    )

    with pytest.raises(ValueError, match="missing leaderboard summary row"):
        audit.verify_leaderboard_contract(summary, audit.LEADERBOARD_RULES)


def test_leaderboard_contract_requires_source_eligible_rows():
    rows = _contract_rows()
    rows[0]["eligible_for_winner"] = False
    summary = pd.DataFrame(rows)

    with pytest.raises(ValueError, match="not source-eligible"):
        audit.verify_leaderboard_contract(summary, audit.LEADERBOARD_RULES)


def test_fixed_rule_from_contract_row_preserves_execution_contract_and_cutoff():
    row = {
        "original_rank": 7,
        "profile_id": "movement_plus_time",
        "model_id": "linear",
        "target_id": "target_entry_good_0_5r",
        "filter_id": "top40",
        "score_cutoff_on_val_select": -0.0123,
    }

    rule = audit.fixed_rule_from_contract_row(row)

    assert rule.stop_policy_id == audit.STOP_POLICY_ID
    assert rule.entry_id == audit.ENTRY_ID
    assert rule.mask_id == audit.MASK_ID
    assert rule.exit_id == audit.EXIT_ID
    assert rule.spread == audit.CANONICAL_SPREAD
    assert rule.profile_id == "movement_plus_time"
    assert rule.model_id == "linear"
    assert rule.target_id == "target_entry_good_0_5r"
    assert rule.filter_id == "top40"
    assert rule.entry_filter_score_col == "rich_entry_score"
    assert rule.score_cutoff_on_val_select == -0.0123


def test_summary_usecols_include_source_eligibility_fields():
    assert "eligible_for_winner" in audit.SUMMARY_USECOLS
    assert "not_eligible_for_winner" in audit.SUMMARY_USECOLS
    assert "not_eligible_reason" in audit.SUMMARY_USECOLS


def test_audit_one_rule_recomputes_block_bootstrap_and_tags_all_rows():
    contract_row = {
        "original_rank": 1,
        "rule_id": "rank01_time_only_linear_target_entry_ev_regression_top30",
        "profile_id": "time_only",
        "model_id": "linear",
        "target_id": "target_entry_ev_regression",
        "filter_id": "top30",
        "score_cutoff_on_val_select": -0.02,
    }
    base_cols = {
        "stop_policy_id": audit.STOP_POLICY_ID,
        "entry_id": audit.ENTRY_ID,
        "mask_id": audit.MASK_ID,
        "exit_id": audit.EXIT_ID,
        "spread": audit.CANONICAL_SPREAD,
        "profile_id": "time_only",
        "model_id": "linear",
        "target_id": "target_entry_ev_regression",
    }
    summary = pd.DataFrame(
        [
            {
                **base_cols,
                "split": "val_eval",
                "filter_id": "top30",
                "n_trades": 4,
                "gross_profit": 2.2,
                "gross_loss": 0.7,
                "pf": 3.142857,
                "mean_pnl_r": 0.375,
                "median_pnl_r": 0.25,
                "max_drawdown_r": 0.5,
                "win_rate": 0.5,
                "bs_p05": 2.0,
                "negative_years": 0,
                "pf_without_best_year": 1.5,
                "effective_profit_years": 2.0,
                "n_years": 2,
                "score_cutoff_on_val_select": -0.02,
                "entry_filter_score_col": "rich_entry_score",
            }
        ]
    )
    trades = pd.DataFrame(
        [
            {**base_cols, "split": "val_eval", "filter_id": "top30", "position_id": "a", "side": "BUY", "signal_time": "2021-01-01", "fill_time": "2021-01-01 01:00", "exit_time": "2021-01-02", "pnl_r": 1.0, "close_reason": "TP", "hold_bars": 3, "ambiguous": False},
            {**base_cols, "split": "val_eval", "filter_id": "top30", "position_id": "b", "side": "SELL", "signal_time": "2021-02-01", "fill_time": "2021-02-01 01:00", "exit_time": "2021-02-02", "pnl_r": -0.5, "close_reason": "SL", "hold_bars": 2, "ambiguous": False},
            {**base_cols, "split": "val_eval", "filter_id": "top30", "position_id": "c", "side": "BUY", "signal_time": "2022-01-01", "fill_time": "2022-01-01 01:00", "exit_time": "2022-01-02", "pnl_r": 1.2, "close_reason": "ML_CLOSE", "hold_bars": 5, "ambiguous": False},
            {**base_cols, "split": "val_eval", "filter_id": "top30", "position_id": "d", "side": "SELL", "signal_time": "2022-02-01", "fill_time": "2022-02-01 01:00", "exit_time": "2022-02-02", "pnl_r": -0.2, "close_reason": "TIME", "hold_bars": 4, "ambiguous": False},
        ]
    )
    scores = pd.DataFrame(
        [
            {"split": "val_select", "profile_id": "time_only", "model_id": "linear", "target_id": "target_entry_ev_regression", "filter_id": "top30", "position_id": "s1", "rich_entry_score": -0.01},
            {"split": "val_eval", "profile_id": "time_only", "model_id": "linear", "target_id": "target_entry_ev_regression", "filter_id": "top30", "position_id": "a", "rich_entry_score": -0.01},
            {"split": "val_eval", "profile_id": "time_only", "model_id": "linear", "target_id": "target_entry_ev_regression", "filter_id": "top30", "position_id": "b", "rich_entry_score": -0.03},
        ]
    )

    result = audit.audit_one_rule(summary, trades, scores, contract_row)

    assert result["summary"]["rule_id"] == contract_row["rule_id"]
    assert result["summary"]["original_rank"] == 1
    assert result["summary"]["sequential_block_bs_p05"] is not None
    assert set(result["yearly"]["rule_id"]) == {contract_row["rule_id"]}
    assert set(result["side"]["side"]) == {"BUY", "SELL"}
    assert {"signal_time", "fill_time", "exit_time"}.issubset(set(result["calendar_slices"]["time_basis"]))


def test_rule_decision_discloses_missing_cost_and_time_checks_without_candidate_language():
    summary_row = {
        "rule_id": "rank07_movement_plus_time_linear_target_entry_good_0_5r_top40",
        "n_trades": 979,
        "pf": 3.3,
        "bs_p05": 2.8,
        "sequential_block_bs_p05": 2.8,
        "pf_without_best_year": 2.0,
        "concentration_n_years": 2,
        "concentration_effective_profit_years": 1.9,
    }
    side = pd.DataFrame({"side": ["BUY", "SELL"], "n_trades": [500, 479], "mean_pnl_r": [0.2, 0.1], "pf": [2.0, 1.5], "max_drawdown_r": [2.0, 3.0]})
    stricter = pd.DataFrame({"cutoff_offset": [0.0, 0.005, 0.01, 0.02], "n_trades": [979, 800, 610, 340], "pf": [3.3, 3.1, 2.8, 2.0]})
    topk = pd.DataFrame({"filter_id": ["top30", "top40", "top50"], "n_trades": [760, 979, 1223], "pf": [3.4, 3.3, 3.2]})
    missing = audit.missing_diagnostics_for_rule({"rule_id": summary_row["rule_id"], "profile_id": "movement_plus_time"})

    result = audit.rule_decision(summary_row, side, stricter, topk, missing)

    assert result["decision"] == "RULE_ROBUSTNESS_INCOMPLETE"
    assert "stress_costs_not_computable" in result["reasons"]
    assert "timezone_shift_not_run" in result["disclosures"]
    assert result["allowed_max_verdict"] == "research_only"
    assert "candidate" not in result["decision"].lower()


def test_build_classification_preserves_original_rank_and_never_selects_new_winner():
    summaries = pd.DataFrame(
        [
            {"original_rank": 2, "rule_id": "rank02", "profile_id": "time_only", "model_id": "linear", "target_id": "target_entry_ev_regression", "filter_id": "top40", "pf": 9.0, "sequential_block_bs_p05": 8.0},
            {"original_rank": 1, "rule_id": "rank01", "profile_id": "time_only", "model_id": "linear", "target_id": "target_entry_ev_regression", "filter_id": "top30", "pf": 4.0, "sequential_block_bs_p05": 3.0},
        ]
    )
    decisions = {
        "rank01": {"decision": "RULE_ROBUSTNESS_INCOMPLETE", "reasons": ["stress_costs_not_computable"], "disclosures": [], "allowed_max_verdict": "research_only"},
        "rank02": {"decision": "RULE_ROBUSTNESS_INCOMPLETE", "reasons": ["stress_costs_not_computable"], "disclosures": [], "allowed_max_verdict": "research_only"},
    }

    result = audit.build_classification(summaries, decisions)

    assert result["original_rank"].tolist() == [1, 2]
    assert set(result["new_winner_selected"]) == {False}
    assert set(result["allowed_max_verdict"]) == {"research_only"}


def test_overall_decision_reflects_incomplete_missing_checks_not_only_run_completion():
    classification = pd.DataFrame(
        [
            {"original_rank": 1, "rule_id": "rank01", "profile_id": "time_only", "decision": "RULE_ROBUSTNESS_INCOMPLETE"},
            {"original_rank": 2, "rule_id": "rank02", "profile_id": "movement_plus_time", "decision": "RULE_ROBUSTNESS_INCOMPLETE"},
        ]
    )
    missing = pd.DataFrame(
        [
            {"rule_id": "rank01", "diagnostic": "stress_costs", "status": "NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS"},
            {"rule_id": "rank01", "diagnostic": "timezone_shift", "status": "NOT_RUN"},
        ]
    )

    result = audit.overall_decision_from_classification(classification, missing)

    assert result["overall_decision"] == "LEADERBOARD_ROBUSTNESS_INCOMPLETE_NEEDS_COST_TIME_CHECKS"
    assert "stress_costs_not_computable" in result["overall_decision_reasons"]


def test_source_scale_contract_counts_final_normalized_audit_warnings(tmp_path):
    audit_csv = tmp_path / "normalized_feature_distribution_audit.csv"
    pd.DataFrame({"flag": ["PASS", "WARNING", "WARNING"]}).to_csv(audit_csv, sep=";", index=False)
    artifact = {
        "feature_contract_variant": "normalized_atr_unit",
        "normalization_config": {"mode": "normalized_atr_unit", "fit_split": "train_core"},
        "artifacts": {"normalized_feature_distribution_audit_csv": str(audit_csv)},
        "feature_distribution_flags": [{"status": "PASS"}],
    }

    result = audit.source_scale_contract(artifact)

    assert result["structural_profile_gate_status"] == "PASS"
    assert result["normalized_feature_distribution_flag_counts"] == {"PASS": 1, "WARNING": 2}
    assert result["status"] == "DIAGNOSTIC_ONLY"
    assert result["warning_action"] == "accept-as-warning"


def test_overall_decision_reasons_include_all_blocking_limitations():
    classification = pd.DataFrame(
        [{"original_rank": 1, "rule_id": "rank01", "profile_id": "time_only", "decision": "RULE_ROBUSTNESS_INCOMPLETE"}]
    )
    missing = pd.DataFrame(
        [
            {"rule_id": "rank01", "diagnostic": "stress_costs", "status": "NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS"},
            {"rule_id": "rank01", "diagnostic": "timezone_shift", "status": "NOT_RUN"},
            {"rule_id": "rank01", "diagnostic": "calendar_permutation_importance", "status": "NOT_RUN"},
            {"rule_id": "rank01", "diagnostic": "sequential_position_constraint", "status": "NOT_RUN"},
        ]
    )

    result = audit.overall_decision_from_classification(classification, missing)

    assert result["overall_decision_reasons"] == [
        "stress_costs_not_computable",
        "timezone_shift_not_run",
        "calendar_permutation_importance_not_run",
        "sequential_position_constraint_not_run",
        "multi_seed_not_run",
        "provider_drift_not_run",
        "transfer_not_run",
    ]
