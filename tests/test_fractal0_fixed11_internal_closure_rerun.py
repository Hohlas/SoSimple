from pathlib import Path

import pandas as pd

from ML.baseline import benchmark_fractal0_entry_exit_grid as entry_exit
from ML.baseline import audit_leaderboard_robustness as leaderboard
from ML.baseline import fractal0_fixed11_internal_closure_rerun as rerun


def test_fixed_rule_manifest_reuses_exact_leaderboard_rules():
    manifest = rerun.fixed_rule_manifest_frame()

    assert len(manifest) == 11
    assert manifest["original_rank"].tolist() == list(range(1, 12))
    assert manifest["rule_id"].tolist() == [rule.rule_id for rule in leaderboard.LEADERBOARD_RULES]
    assert set(manifest["locked_test_policy"]) == {"not_opened"}


def test_internal_run_matrix_is_bounded_not_full_cross_product():
    matrix = rerun.build_internal_run_matrix()

    assert matrix["run_group"].value_counts().to_dict() == {
        "stress_cost": 33,
        "timezone_calendar": 55,
        "multiseed": 55,
    }
    assert set(matrix["provider_drift_status"]) == {"NOT_IN_SCOPE"}
    assert set(matrix["transfer_status"]) == {"NOT_IN_SCOPE"}
    assert matrix.loc[matrix["run_group"].eq("stress_cost"), "seed"].eq(42).all()
    assert matrix.loc[matrix["run_group"].eq("stress_cost"), "timezone_shift_hours"].eq(0).all()
    assert matrix.loc[matrix["run_group"].eq("timezone_calendar"), "seed"].eq(42).all()
    assert matrix.loc[matrix["run_group"].eq("timezone_calendar"), "spread"].eq(0.2).all()
    assert matrix.loc[matrix["run_group"].eq("multiseed"), "spread"].eq(0.2).all()
    assert matrix.loc[matrix["run_group"].eq("multiseed"), "timezone_shift_hours"].eq(0).all()


def test_smoke_run_matrix_keeps_one_rule_per_axis():
    matrix = rerun.build_internal_run_matrix(smoke_first_rule_only=True)

    assert matrix["run_group"].value_counts().to_dict() == {
        "stress_cost": 3,
        "timezone_calendar": 5,
        "multiseed": 5,
    }
    assert set(matrix["original_rank"]) == {1}


def test_load_saved_cutoffs_uses_rule_id_and_cutoff(tmp_path):
    path = tmp_path / "rules.csv"
    pd.DataFrame(
        {
            "rule_id": ["rank01_time_only_linear_target_entry_ev_regression_top30"],
            "score_cutoff_on_val_select": [-0.026718184259660646],
        }
    ).to_csv(path, sep=";", index=False)

    result = rerun.load_saved_cutoffs(path)

    assert result == {"rank01_time_only_linear_target_entry_ev_regression_top30": -0.026718184259660646}


def test_build_classification_is_fail_closed_on_missing_rows():
    manifest = pd.DataFrame({"rule_id": ["rank01", "rank02"], "original_rank": [1, 2]})
    stress = pd.DataFrame({"rule_id": ["rank01"], "status": ["COMPUTED"], "risk_flag": [False]})
    timezone = pd.DataFrame({"rule_id": ["rank01"], "status": ["COMPUTED"], "risk_flag": [False]})
    permutation = pd.DataFrame({"rule_id": ["rank01"], "status": ["COMPUTED"], "risk_flag": [False]})
    baseline = pd.DataFrame({"rule_id": ["rank01"], "status": ["COMPUTED"], "risk_flag": [False]})
    multiseed = pd.DataFrame({"rule_id": ["rank01"], "status": ["COMPUTED"], "risk_flag": [False]})

    result = rerun.build_classification(manifest, stress, timezone, permutation, baseline, multiseed)

    missing = result.loc[result["rule_id"].eq("rank02")].iloc[0]
    assert missing["decision"] == "INTERNAL_CLOSURE_INCOMPLETE"
    assert "missing_stress_cost" in missing["reasons"]


def test_source_rules_csv_argument_is_recorded_and_used(tmp_path):
    rules_csv = tmp_path / "rules.csv"
    pd.DataFrame(
        {
            "rule_id": ["rank01_time_only_linear_target_entry_ev_regression_top30"],
            "score_cutoff_on_val_select": [-0.123],
        }
    ).to_csv(rules_csv, sep=";", index=False)

    cutoffs = rerun.load_saved_cutoffs(rules_csv)
    metadata = rerun.source_rules_metadata(rules_csv)

    assert cutoffs["rank01_time_only_linear_target_entry_ev_regression_top30"] == -0.123
    assert metadata["source_rules_csv"] == str(rules_csv)
    assert metadata["source_rules_csv_sha256"]


def test_parse_args_exposes_task6_cli_contract():
    args = rerun.parse_args([])

    assert args.source_prefix == str(rerun.SOURCE_INPUT_PREFIX)
    assert args.source_rules_csv == str(rerun.SOURCE_RULES_CSV)
    assert args.output_prefix == str(rerun.CLOSURE_OUTPUT_PREFIX)
    assert args.run_groups == "stress_cost,timezone_calendar,multiseed"
    assert args.threads == 24
    assert args.smoke_first_rule_only is False
    assert args.no_resume is False

    custom = rerun.parse_args(
        [
            "--source-prefix",
            "in",
            "--source-rules-csv",
            "rules.csv",
            "--output-prefix",
            "out",
            "--run-groups",
            "multiseed",
            "--threads",
            "7",
            "--smoke-first-rule-only",
            "--no-resume",
        ]
    )

    assert custom.source_prefix == "in"
    assert custom.source_rules_csv == "rules.csv"
    assert custom.output_prefix == "out"
    assert custom.run_groups == "multiseed"
    assert custom.threads == 7
    assert custom.smoke_first_rule_only is True
    assert custom.no_resume is True


def test_calendar_feature_columns_are_profile_specific():
    assert rerun.calendar_feature_columns("time_only") == [
        "session_hour_unit",
        "weekday_unit",
        "hour_sin_unit",
        "hour_cos_unit",
        "weekday_sin_unit",
        "weekday_cos_unit",
    ]
    assert rerun.calendar_feature_columns("movement_plus_time") == [
        "session_hour_unit",
        "weekday_unit",
        "hour_sin_unit",
        "hour_cos_unit",
        "weekday_sin_unit",
        "weekday_cos_unit",
    ]


def test_timezone_risk_flag_uses_shift0_anchor():
    frame = pd.DataFrame(
        {
            "rule_id": ["rank01", "rank01"],
            "timezone_shift_hours": [0, 4],
            "pf": [4.0, 2.0],
            "n_trades": [500, 500],
            "bs_p05": [3.0, 1.5],
        }
    )

    result = rerun.add_timezone_risk_flags(frame)

    shifted = result.loc[result["timezone_shift_hours"].eq(4)].iloc[0]
    assert shifted["pf_drop_from_shift0_ratio"] == 0.5
    assert bool(shifted["risk_flag"]) is True


def test_aggregate_multiseed_flags_unstable_rule():
    frame = pd.DataFrame(
        {
            "rule_id": ["rank01"] * 5,
            "seed": [41, 42, 43, 44, 45],
            "pf": [1.3, 1.4, 0.9, 1.5, 1.6],
            "bs_p05": [1.1, 1.2, 0.8, 1.1, 1.2],
            "n_trades": [400, 400, 400, 400, 400],
            "status": ["COMPUTED"] * 5,
        }
    )

    result = rerun.aggregate_multiseed(frame)

    row = result.iloc[0]
    assert row["computed_seed_count"] == 5
    assert row["passing_seed_count"] == 4
    assert bool(row["risk_flag"]) is False


def test_collect_stress_cost_requires_computed_rows(tmp_path):
    run_prefix = tmp_path / "run"
    pd.DataFrame(
        {
            "run_group": ["stress_cost"],
            "original_rank": [1],
            "rule_id": ["rank01"],
            "spread": [0.4],
            "split": ["val_eval"],
            "n_trades": [400],
            "pf": [1.5],
            "bs_p05": [1.1],
            "max_drawdown_r": [5.0],
        }
    ).to_csv(run_prefix.with_name(run_prefix.name + "_summary.csv"), sep=";", index=False)
    pd.DataFrame(
        columns=[
            "entry_effective_price",
            "fill_time",
            "exit_time",
            "close_reason",
            "r_value",
            "pnl_r",
            "spread",
        ]
    ).to_csv(run_prefix.with_name(run_prefix.name + "_trades.csv"), sep=";", index=False)

    result = rerun.collect_stress_cost(
        run_prefix,
        pd.DataFrame(
            {
                "run_group": ["stress_cost"],
                "original_rank": [1],
                "rule_id": ["rank01"],
                "spread": [0.4],
                "seed": [42],
                "timezone_shift_hours": [0],
                "locked_test_status": ["not_opened"],
                "provider_drift_status": ["NOT_IN_SCOPE"],
                "transfer_status": ["NOT_IN_SCOPE"],
            }
        ),
    )

    assert result["status"].tolist() == ["COMPUTED"]
    assert result["spread"].tolist() == [0.4]
    assert result["pf"].tolist() == [1.5]
    assert result["stress_2x_4x_flag"].tolist() == [False]
    assert result["locked_test_status"].tolist() == ["not_opened"]


def test_collect_stress_cost_keeps_zero_trade_rows_when_smoke_trades_file_is_empty(tmp_path):
    run_prefix = tmp_path / "run_zero"
    pd.DataFrame(
        {
            "run_group": ["stress_cost"],
            "original_rank": [1],
            "rule_id": ["rank01"],
            "spread": [0.8],
            "split": ["val_eval"],
            "n_trades": [0],
            "pf": [float("nan")],
            "bs_p05": [float("nan")],
            "max_drawdown_r": [0.0],
        }
    ).to_csv(run_prefix.with_name(run_prefix.name + "_summary.csv"), sep=";", index=False)
    run_prefix.with_name(run_prefix.name + "_trades.csv").write_text("\n", encoding="utf-8")

    result = rerun.collect_stress_cost(
        run_prefix,
        pd.DataFrame(
            {
                "run_group": ["stress_cost"],
                "original_rank": [1],
                "rule_id": ["rank01"],
                "spread": [0.8],
                "seed": [42],
                "timezone_shift_hours": [0],
                "locked_test_status": ["not_opened"],
                "provider_drift_status": ["NOT_IN_SCOPE"],
                "transfer_status": ["NOT_IN_SCOPE"],
            }
        ),
    )

    assert result["status"].tolist() == ["COMPUTED"]
    assert result["n_trades"].tolist() == [0]
    assert result["stress_2x_4x_flag"].tolist() == [True]
    assert result["reason"].tolist() == ["producer_level_rich_runner_resimulation"]


def test_run_rich_fixed_once_passes_threads_to_rich_runner(monkeypatch, tmp_path):
    captured = {}

    def fake_run(args):
        captured["threads"] = args.threads
        captured["fixed_cutoffs_csv"] = args.fixed_cutoffs_csv
        captured["fixed_leaderboard_rules_only"] = args.fixed_leaderboard_rules_only
        captured["smoke_first_rule_only"] = args.smoke_first_rule_only
        captured["stop_grid_artifact"] = args.stop_grid_artifact
        return {"status": "completed"}

    monkeypatch.setattr(rerun.rich, "run_rich_entry_quality", fake_run)

    result = rerun.run_rich_fixed_once(
        output_prefix=tmp_path / "stress",
        seed=42,
        spread=0.8,
        timezone_shift_hours=0,
        fixed_cutoffs_csv=tmp_path / "rules.csv",
        threads=24,
        smoke_first_rule_only=True,
    )

    assert result == {"status": "completed"}
    assert captured == {
        "threads": 24,
        "fixed_cutoffs_csv": str(tmp_path / "rules.csv"),
        "fixed_leaderboard_rules_only": True,
        "smoke_first_rule_only": True,
        "stop_grid_artifact": "ML/reports/fractal0_entry_exit_grid_stop_policy.json",
    }


def test_run_internal_closure_smoke_writes_computed_stress_artifacts(monkeypatch, tmp_path):
    output_prefix = tmp_path / "closure"
    source_rules_csv = tmp_path / "rules.csv"
    first_rule_id = leaderboard.LEADERBOARD_RULES[0].rule_id
    pd.DataFrame(
        {
            "rule_id": [first_rule_id],
            "score_cutoff_on_val_select": [0.12],
        }
    ).to_csv(source_rules_csv, sep=";", index=False)

    calls = []

    def fake_guard(*args, **kwargs) -> None:
        return None

    def fake_run_rich_fixed_once(output_prefix, seed, spread, timezone_shift_hours, fixed_cutoffs_csv, threads, smoke_first_rule_only=False):
        calls.append(
            {
                "output_prefix": output_prefix,
                "seed": seed,
                "spread": spread,
                "timezone_shift_hours": timezone_shift_hours,
                "fixed_cutoffs_csv": fixed_cutoffs_csv,
                "threads": threads,
                "smoke_first_rule_only": smoke_first_rule_only,
            }
        )
        pd.DataFrame(
            {
                "run_group": ["stress_cost"],
                "original_rank": [1],
                "rule_id": [first_rule_id],
                "spread": [spread],
                "split": ["val_eval"],
                "n_trades": [410],
                "pf": [1.6],
                "bs_p05": [1.1],
                "max_drawdown_r": [4.5],
            }
        ).to_csv(output_prefix.with_name(output_prefix.name + "_summary.csv"), sep=";", index=False)
        pd.DataFrame(
            columns=[
                "entry_effective_price",
                "fill_time",
                "exit_time",
                "close_reason",
                "r_value",
                "pnl_r",
                "spread",
            ]
        ).to_csv(output_prefix.with_name(output_prefix.name + "_trades.csv"), sep=";", index=False)
        return {"status": "completed"}

    monkeypatch.setattr(rerun, "_guard_locked_test_not_opened", fake_guard)
    monkeypatch.setattr(rerun, "run_rich_fixed_once", fake_run_rich_fixed_once)

    result = rerun.run_internal_closure(
        rerun._build_parser().parse_args(
            [
                "--output-prefix",
                str(output_prefix),
                "--source-rules-csv",
                str(source_rules_csv),
                "--run-groups",
                "stress_cost",
                "--smoke-first-rule-only",
                "--threads",
                "24",
            ]
        )
    )

    stress = pd.read_csv(output_prefix.with_name(output_prefix.name + "_stress_cost.csv"), sep=";")

    assert result["stress_cost_status"] == "COMPUTED_SMOKE"
    assert result["locked_test"] == "not_opened"
    assert result["locked_test_status"] == "not_opened"
    assert result["fixed_cutoff_source"] == str(source_rules_csv)
    assert stress["spread"].tolist() == [0.2, 0.4, 0.8]
    assert stress["status"].tolist() == ["COMPUTED", "COMPUTED", "COMPUTED"]
    assert len(calls) == 3
    assert {call["threads"] for call in calls} == {24}
    assert all(call["smoke_first_rule_only"] for call in calls)


def test_run_internal_closure_resume_skips_completed_child_runs(monkeypatch, tmp_path):
    output_prefix = tmp_path / "closure"
    source_rules_csv = tmp_path / "rules.csv"
    first_rule_id = leaderboard.LEADERBOARD_RULES[0].rule_id
    pd.DataFrame(
        {
            "rule_id": [first_rule_id],
            "score_cutoff_on_val_select": [0.12],
        }
    ).to_csv(source_rules_csv, sep=";", index=False)

    for spread in rerun.STRESS_SPREADS:
        run_prefix = rerun._run_prefix(output_prefix, "stress_cost", 42, float(spread), 0)
        run_prefix.with_suffix(".json").write_text('{"status": "completed"}', encoding="utf-8")
        pd.DataFrame(
            {
                "run_group": ["stress_cost"],
                "original_rank": [1],
                "rule_id": [first_rule_id],
                "spread": [spread],
                "split": ["val_eval"],
                "n_trades": [410],
                "pf": [1.6],
                "bs_p05": [1.1],
                "max_drawdown_r": [4.5],
            }
        ).to_csv(run_prefix.with_name(run_prefix.name + "_summary.csv"), sep=";", index=False)
        pd.DataFrame(
            columns=[
                "entry_effective_price",
                "fill_time",
                "exit_time",
                "close_reason",
                "r_value",
                "pnl_r",
                "spread",
            ]
        ).to_csv(run_prefix.with_name(run_prefix.name + "_trades.csv"), sep=";", index=False)

    monkeypatch.setattr(rerun, "_guard_locked_test_not_opened", lambda *args, **kwargs: {"loaded": {"artifact": {}}})

    def fail_if_called(*args, **kwargs):
        raise AssertionError("completed child run should be skipped by resume")

    monkeypatch.setattr(rerun, "run_rich_fixed_once", fail_if_called)

    result = rerun.run_internal_closure(
        rerun.parse_args(
            [
                "--output-prefix",
                str(output_prefix),
                "--source-rules-csv",
                str(source_rules_csv),
                "--run-groups",
                "stress_cost",
                "--smoke-first-rule-only",
            ]
        )
    )

    assert result["resume_enabled"] is True
    assert result["resume_skipped_run_count"] == 3
    assert result["stress_cost_status"] == "COMPUTED_SMOKE"


def test_run_internal_closure_timezone_smoke_passes_threads_to_each_shift(monkeypatch, tmp_path):
    output_prefix = tmp_path / "closure"
    source_rules_csv = tmp_path / "rules.csv"
    first_rule_id = leaderboard.LEADERBOARD_RULES[0].rule_id
    pd.DataFrame(
        {
            "rule_id": [first_rule_id],
            "score_cutoff_on_val_select": [0.12],
        }
    ).to_csv(source_rules_csv, sep=";", index=False)

    calls = []

    def fake_guard(*args, **kwargs) -> None:
        return None

    def fake_run_rich_fixed_once(output_prefix, seed, spread, timezone_shift_hours, fixed_cutoffs_csv, threads, smoke_first_rule_only=False):
        calls.append(
            {
                "output_prefix": output_prefix,
                "seed": seed,
                "spread": spread,
                "timezone_shift_hours": timezone_shift_hours,
                "fixed_cutoffs_csv": fixed_cutoffs_csv,
                "threads": threads,
                "smoke_first_rule_only": smoke_first_rule_only,
            }
        )
        pd.DataFrame(
            {
                "run_group": ["timezone_calendar"],
                "original_rank": [1],
                "rule_id": [first_rule_id],
                "spread": [spread],
                "split": ["val_eval"],
                "n_trades": [410],
                "pf": [1.6],
                "bs_p05": [1.1],
                "max_drawdown_r": [4.5],
                "timezone_shift_hours": [timezone_shift_hours],
            }
        ).to_csv(output_prefix.with_name(output_prefix.name + "_summary.csv"), sep=";", index=False)
        return {"status": "completed"}

    monkeypatch.setattr(rerun, "_guard_locked_test_not_opened", fake_guard)
    monkeypatch.setattr(rerun, "run_rich_fixed_once", fake_run_rich_fixed_once)
    monkeypatch.setattr(rerun, "_build_calendar_diagnostic_states", lambda *args, **kwargs: [])
    monkeypatch.setattr(
        rerun,
        "calendar_permutation_sensitivity",
        lambda *args, **kwargs: pd.DataFrame({"rule_id": [first_rule_id], "status": ["COMPUTED"]}),
        raising=False,
    )
    monkeypatch.setattr(
        rerun,
        "calendar_no_ml_baseline",
        lambda *args, **kwargs: pd.DataFrame({"rule_id": [first_rule_id], "status": ["COMPUTED"]}),
        raising=False,
    )

    result = rerun.run_internal_closure(
        rerun._build_parser().parse_args(
            [
                "--output-prefix",
                str(output_prefix),
                "--source-rules-csv",
                str(source_rules_csv),
                "--run-groups",
                "timezone_calendar",
                "--smoke-first-rule-only",
                "--threads",
                "24",
            ]
        )
    )

    timezone = pd.read_csv(output_prefix.with_name(output_prefix.name + "_timezone_rescore.csv"), sep=";")

    assert result["timezone_rescore_status"] == "COMPUTED_SMOKE"
    assert result["calendar_permutation_status"] == "COMPUTED_SMOKE"
    assert result["calendar_no_ml_baseline_status"] == "COMPUTED_SMOKE"
    assert result["locked_test"] == "not_opened"
    assert result["locked_test_status"] == "not_opened"
    assert timezone["timezone_shift_hours"].tolist() == [0, -8, -4, 4, 8]
    assert timezone["status"].tolist() == ["COMPUTED"] * 5
    assert len(calls) == 5
    assert {call["threads"] for call in calls} == {24}
    assert all(call["smoke_first_rule_only"] for call in calls)
    assert result["artifacts"]["calendar_permutation_importance_csv"].endswith("_calendar_permutation_importance.csv")
    assert Path(result["artifacts"]["calendar_permutation_importance_csv"]).exists()
    assert "calendar_permutation_sensitivity_csv" not in result["artifacts"]


def test_main_writes_unknown_contract_json_and_returns_1(tmp_path):
    output_prefix = tmp_path / "closure"

    exit_code = rerun.main(
        [
            "--output-prefix",
            str(output_prefix),
            "--run-groups",
            "unknown_contract",
        ]
    )

    artifact = pd.read_json(output_prefix.with_suffix(".json"), typ="series")
    assert exit_code == 1
    assert artifact["status"] == "unknown_input_or_contract"
    assert artifact["decision"] == "UNKNOWN_INPUT_OR_CONTRACT"
    assert artifact["locked_test"] == "not_opened"


def test_build_overall_decision_reports_risk_flags_when_all_rows_computed():
    classification = pd.DataFrame(
        {
            "decision": [
                "INTERNAL_CLOSURE_RISK_FLAGGED",
                "INTERNAL_CLOSURE_RISK_FLAGGED",
            ]
        }
    )

    result = rerun.build_overall_decision(
        classification,
        stress_status="COMPUTED",
        timezone_rescore_status="COMPUTED",
        calendar_permutation_status="COMPUTED",
        calendar_baseline_status="COMPUTED",
        multiseed_status="COMPUTED",
    )

    assert result == "FIXED11_INTERNAL_CLOSURE_RISK_FLAGS_RESEARCH_ONLY"


def test_run_internal_closure_json_records_research_scope_statuses(monkeypatch, tmp_path):
    output_prefix = tmp_path / "closure"
    source_rules_csv = tmp_path / "rules.csv"
    first_rule_id = leaderboard.LEADERBOARD_RULES[0].rule_id
    pd.DataFrame(
        {
            "rule_id": [first_rule_id],
            "score_cutoff_on_val_select": [-0.1],
        }
    ).to_csv(source_rules_csv, sep=";", index=False)

    for spread in rerun.STRESS_SPREADS:
        run_prefix = rerun._run_prefix(output_prefix, "stress_cost", 42, float(spread), 0)
        run_prefix.with_suffix(".json").write_text('{"status": "completed"}', encoding="utf-8")
        pd.DataFrame(
            {
                "run_group": ["stress_cost"],
                "original_rank": [1],
                "rule_id": [first_rule_id],
                "spread": [spread],
                "split": ["val_eval"],
                "n_trades": [410],
                "pf": [1.6],
                "bs_p05": [1.1],
                "max_drawdown_r": [4.5],
            }
        ).to_csv(run_prefix.with_name(run_prefix.name + "_summary.csv"), sep=";", index=False)
        pd.DataFrame(
            columns=[
                "entry_effective_price",
                "fill_time",
                "exit_time",
                "close_reason",
                "r_value",
                "pnl_r",
                "spread",
            ]
        ).to_csv(run_prefix.with_name(run_prefix.name + "_trades.csv"), sep=";", index=False)

    monkeypatch.setattr(rerun, "_guard_locked_test_not_opened", lambda source_prefix: {})
    monkeypatch.setattr(
        rerun,
        "_source_input_metadata",
        lambda source_prefix, verified: {
            "source_input_prefix": str(source_prefix),
            "source_input_json": "source.json",
            "source_input_json_sha256": "abc",
            "source_input_artifact_hashes": {},
        },
    )
    monkeypatch.setattr(rerun, "source_rules_metadata", lambda path: {"source_rules_csv": str(path), "source_rules_csv_sha256": "ruleshash"})
    monkeypatch.setattr(rerun, "run_rich_fixed_once", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("resume should skip child runs")))

    result = rerun.run_internal_closure(
        rerun.parse_args(
            [
                "--output-prefix",
                str(output_prefix),
                "--source-rules-csv",
                str(source_rules_csv),
                "--run-groups",
                "stress_cost",
                "--smoke-first-rule-only",
                "--threads",
                "24",
            ]
        )
    )

    assert result["verdict"] == "research_only"
    assert result["provider_drift_status"] == "NOT_IN_SCOPE"
    assert result["transfer_status"] == "NOT_IN_SCOPE"
    assert result["leaderboard_rule_count"] == 1



def test_run_internal_closure_multiseed_smoke_writes_seed_and_aggregate_artifacts(monkeypatch, tmp_path):
    output_prefix = tmp_path / "closure"
    source_rules_csv = tmp_path / "rules.csv"
    first_rule = leaderboard.LEADERBOARD_RULES[0]
    pd.DataFrame(
        {
            "rule_id": [first_rule.rule_id],
            "score_cutoff_on_val_select": [0.12],
        }
    ).to_csv(source_rules_csv, sep=";", index=False)

    calls = []

    def fake_guard(*args, **kwargs) -> None:
        return None

    def fake_run_rich_fixed_once(output_prefix, seed, spread, timezone_shift_hours, fixed_cutoffs_csv, threads, smoke_first_rule_only=False):
        calls.append(
            {
                "output_prefix": output_prefix,
                "seed": seed,
                "spread": spread,
                "timezone_shift_hours": timezone_shift_hours,
                "fixed_cutoffs_csv": fixed_cutoffs_csv,
                "threads": threads,
                "smoke_first_rule_only": smoke_first_rule_only,
            }
        )
        pd.DataFrame(
            {
                "original_rank": [1],
                "rule_id": [first_rule.rule_id],
                "profile_id": [first_rule.profile_id],
                "model_id": [first_rule.model_id],
                "target_id": [first_rule.target_id],
                "filter_id": [first_rule.filter_id],
                "split": ["val_eval"],
                "n_trades": [410],
                "pf": [1.4 if seed != 43 else 0.9],
                "bs_p05": [1.1 if seed != 43 else 0.8],
                "spread": [spread],
                "timezone_shift_hours": [timezone_shift_hours],
            }
        ).to_csv(output_prefix.with_name(output_prefix.name + "_summary.csv"), sep=";", index=False)
        return {"status": "completed"}

    monkeypatch.setattr(rerun, "_guard_locked_test_not_opened", fake_guard)
    monkeypatch.setattr(rerun, "run_rich_fixed_once", fake_run_rich_fixed_once)

    result = rerun.run_internal_closure(
        rerun._build_parser().parse_args(
            [
                "--output-prefix",
                str(output_prefix),
                "--source-rules-csv",
                str(source_rules_csv),
                "--run-groups",
                "multiseed",
                "--smoke-first-rule-only",
                "--threads",
                "24",
            ]
        )
    )

    multiseed = pd.read_csv(output_prefix.with_name(output_prefix.name + "_multiseed.csv"), sep=";")
    aggregate = pd.read_csv(output_prefix.with_name(output_prefix.name + "_multiseed_aggregate.csv"), sep=";")

    assert result["multiseed_status"] == "COMPUTED_SMOKE"
    assert result["multiseed_row_count"] == 5
    assert result["multiseed_aggregate_row_count"] == 1
    assert multiseed["seed"].tolist() == [41, 42, 43, 44, 45]
    assert multiseed["status"].tolist() == ["COMPUTED"] * 5
    assert aggregate["computed_seed_count"].tolist() == [5]
    assert aggregate["passing_seed_count"].tolist() == [4]
    assert aggregate["risk_flag"].tolist() == [False]
    assert len(calls) == 5
    assert {call["threads"] for call in calls} == {24}
    assert all(call["spread"] == 0.2 for call in calls)
    assert all(call["timezone_shift_hours"] == 0 for call in calls)
    assert all(call["smoke_first_rule_only"] for call in calls)


def _synthetic_spread_cases() -> list[dict[str, object]]:
    return [
        {
            "case_id": "buy_tp",
            "entry": {"side": "BUY", "fill_index": 0, "entry_effective_price": 100.2, "entry_bid_equivalent": 100.0, "protective_stop_price": 99.0, "r_value": 1.2, "atr": 2.0},
            "bars": pd.DataFrame({"open": [100.0, 100.8], "high": [100.9, 101.1], "low": [100.0, 100.7], "close": [100.8, 101.0], "time": pd.to_datetime(["2021-01-01 10:00", "2021-01-01 11:00"])}),
            "exit_rule": {"family": "fixed_r", "tp_r": 0.7},
            "expected_reason": "TP",
            "expected_ambiguous": False,
        },
        {
            "case_id": "buy_same_bar_sl_first",
            "entry": {"side": "BUY", "fill_index": 0, "entry_effective_price": 100.2, "entry_bid_equivalent": 100.0, "protective_stop_price": 99.0, "r_value": 1.2, "atr": 2.0},
            "bars": pd.DataFrame({"open": [100.0], "high": [101.2], "low": [98.9], "close": [100.5], "time": pd.to_datetime(["2021-01-01 10:00"])}),
            "exit_rule": {"family": "fixed_r", "tp_r": 0.7},
            "expected_reason": "SL",
            "expected_ambiguous": True,
        },
        {
            "case_id": "sell_tp",
            "entry": {"side": "SELL", "fill_index": 0, "entry_effective_price": 100.0, "entry_bid_equivalent": 100.0, "protective_stop_price": 101.0, "r_value": 1.0, "atr": 2.0},
            "bars": pd.DataFrame({"open": [99.8], "high": [99.0], "low": [98.0], "close": [98.7], "time": pd.to_datetime(["2021-01-01 10:00"])}),
            "exit_rule": {"family": "fixed_r", "tp_r": 0.7},
            "expected_reason": "TP",
            "expected_ambiguous": False,
        },
        {
            "case_id": "sell_sl",
            "entry": {"side": "SELL", "fill_index": 0, "entry_effective_price": 100.0, "entry_bid_equivalent": 100.0, "protective_stop_price": 101.0, "r_value": 1.0, "atr": 2.0},
            "bars": pd.DataFrame({"open": [100.0], "high": [100.9], "low": [99.5], "close": [100.6], "time": pd.to_datetime(["2021-01-01 10:00"])}),
            "exit_rule": {"family": "fixed_r", "tp_r": 0.7},
            "expected_reason": "SL",
            "expected_ambiguous": False,
        },
        {
            "case_id": "sell_time",
            "entry": {"side": "SELL", "fill_index": 0, "entry_effective_price": 100.0, "entry_bid_equivalent": 100.0, "protective_stop_price": 101.0, "r_value": 1.0, "atr": 2.0},
            "bars": pd.DataFrame(
                {
                    "open": [99.7, 99.6, 99.5],
                    "high": [99.6, 99.5, 99.4],
                    "low": [99.2, 99.1, 99.0],
                    "close": [99.4, 99.3, 99.2],
                    "time": pd.to_datetime(["2021-01-01 10:00", "2021-01-01 11:00", "2021-01-01 12:00"]),
                }
            ),
            "exit_rule": {"family": "time_exit", "hold_bars": 2},
            "expected_reason": "TIME",
            "expected_ambiguous": False,
        },
    ]


def _simulate_synthetic_spread_cases(cases: list[dict[str, object]], spread: float) -> pd.DataFrame:
    rows = []
    for case in cases:
        result = entry_exit.simulate_trade(case["entry"], case["bars"], case["exit_rule"], spread=spread)
        rows.append(
            {
                "case_id": case["case_id"],
                "expected_reason": case["expected_reason"],
                "expected_ambiguous": case["expected_ambiguous"],
                "close_reason": result["close_reason"],
                "ambiguous": result["ambiguous"],
                "pnl_r": result["pnl_r"],
                "spread": spread,
            }
        )
    return pd.DataFrame(rows)


def test_stress_spread_simulator_contract_buy_sell_synthetic_cases():
    cases = _synthetic_spread_cases()

    for spread in (0.2, 0.4, 0.8):
        result = _simulate_synthetic_spread_cases(cases, spread=spread)

        assert result["close_reason"].tolist() == result["expected_reason"].tolist()
        assert result["ambiguous"].tolist() == result["expected_ambiguous"].tolist()
        assert set(result["close_reason"]) == {"TP", "SL", "TIME"}
        assert result.loc[result["close_reason"].eq("TP"), "pnl_r"].gt(0).all()
        assert result.loc[result["close_reason"].eq("SL"), "pnl_r"].lt(0).all()
        assert result["spread"].astype(float).eq(spread).all()
