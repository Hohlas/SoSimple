from __future__ import annotations

from argparse import Namespace
from collections.abc import Sequence
from pathlib import Path

import numpy as np
import pandas as pd
from pytest import approx

import ML.baseline.benchmark_entry_based_next_open_closeout as closeout
import ML.baseline.benchmark_entry_based_powerful_tabular as runner


def test_scope_includes_all100_and_requested_candidates_in_one_experiment():
    assert runner.POWERFUL_TABULAR_REPRESENTATIONS == (
        "all100",
        "corridor_5atr",
        "nearest_k60",
        "nearest_k80",
    )
    assert runner.CONTROL_REPRESENTATIONS == ("all100",)
    assert runner.CANDIDATE_REPRESENTATIONS == (
        "corridor_5atr",
        "nearest_k60",
        "nearest_k80",
    )


def test_output_paths_do_not_overwrite_closeout_artifacts():
    assert str(runner.REPORT_JSON_PATH) == "ML/reports/entry_based_powerful_tabular.json"
    assert str(runner.REPORT_METRICS_PATH) == "ML/reports/entry_based_powerful_tabular_metrics.csv"
    assert str(runner.REPORT_ROWS_PATH) == "ML/reports/entry_based_powerful_tabular_rows.csv"
    assert str(runner.REPORT_SCALE_AUDIT_PATH) == "ML/reports/entry_based_powerful_tabular_scale_audit.csv"
    assert runner.REPORT_JSON_PATH != closeout.REPORT_JSON_PATH
    assert runner.REPORT_METRICS_PATH != closeout.REPORT_METRICS_PATH
    assert runner.REPORT_ROWS_PATH != closeout.REPORT_ROWS_PATH
    assert runner.REPORT_SCALE_AUDIT_PATH != closeout.REPORT_SCALE_AUDIT_PATH


def test_jobs_cover_every_profile_model_seed_once():
    jobs = runner.enumerate_powerful_tabular_jobs()
    assert len(jobs) == 4 * 10 * 1
    assert {job["representation_key"] for job in jobs} == set(runner.POWERFUL_TABULAR_REPRESENTATIONS)
    assert {job["model_key"] for job in jobs} == set(runner.POWERFUL_TABULAR_MODEL_KEYS)
    assert {job["seed"] for job in jobs} == {42}


def test_model_factory_exposes_expected_families_and_thread_count():
    expected_families = {
        "xgboost_depth3_baseline": "xgboost",
        "xgboost_depth5_baseline": "xgboost",
        "xgboost_depth7_regularized": "xgboost",
        "xgboost_depth9_regularized": "xgboost",
        "lightgbm_depth7_regularized": "lightgbm",
        "lightgbm_leaves63_regularized": "lightgbm",
        "catboost_depth6_regularized": "catboost",
        "catboost_depth8_regularized": "catboost",
        "extra_trees_regressor": "extra_trees",
        "hist_gradient_boosting_strong": "hist_gradient_boosting",
    }
    for model_key, family in expected_families.items():
        model, metadata = runner.build_powerful_tabular_model(model_key, seed=42, thread_count=24)
        assert model is not None
        assert metadata["model_key"] == model_key
        assert metadata["family"] == family
        assert metadata["seed"] == 42
        assert metadata["thread_count"] == 24


def test_powerful_runner_reuses_closeout_horizons_and_targets():
    assert runner.CLOSEOUT_HORIZONS == closeout.CLOSEOUT_HORIZONS
    assert runner.closeout_target_matrix is closeout.closeout_target_matrix
    assert runner.compute_closeout_split_metrics is closeout.compute_closeout_split_metrics


def test_job_key_is_stable_and_includes_profile_model_seed():
    job = {"representation_key": "nearest_k60", "model_key": "xgboost_depth7_regularized", "seed": 42}
    assert runner.job_key(job) == "nearest_k60/xgboost_depth7_regularized/42"


def _run_with_direction(rep, model, select, eval_score):
    return {
        "representation_key": rep,
        "model_key": model,
        "seed": 42,
        "split_metrics": {
            "val_select": {
                "entry_log_ratio_12": {"spearman": select},
                "entry_up_3": {"spearman": 0.10},
                "entry_dn_3": {"spearman": 0.10},
                "simple_trade_12": {"mean": 0.01, "trade_count": 100, "long_count": 50, "short_count": 50},
            },
            "val_eval": {
                "entry_log_ratio_12": {"spearman": eval_score},
                "entry_up_3": {"spearman": 0.10},
                "entry_dn_3": {"spearman": 0.10},
                "simple_trade_12": {"mean": 0.01, "trade_count": 100, "long_count": 50, "short_count": 50},
            },
        },
    }


def _mark_direction_replication_ready(summary):
    candidate = summary["best_direction_candidate_only"]
    candidate["yearly_check_pass"] = True
    candidate["simple_trade_vs_closeout_baseline"] = {
        "select_delta": 0.01,
        "eval_delta": 0.01,
        "ranking_only_evidence": False,
    }
    candidate["same_model_all100_comparison"] = {
        "available": True,
        "candidate_minus_all100_val_select": 0.04,
        "candidate_minus_all100_val_eval": 0.02,
        "all100_underperformance_explained": False,
    }


def test_all100_can_win_overall_but_cannot_create_direction_replication_required():
    summary = runner.summarize_powerful_tabular_runs([
        _run_with_direction("all100", "xgboost_depth9_regularized", 0.20, 0.10)
    ])
    assert summary["best_direction_overall"]["representation_key"] == "all100"
    assert summary["best_direction_candidate_only"]["score"] == 0.0
    assert runner.decide_powerful_tabular_verdict(summary) != "DIRECTION_REPLICATION_REQUIRED"


def test_candidate_direction_requires_replication_instead_of_freeze():
    summary = runner.summarize_powerful_tabular_runs([
        _run_with_direction("nearest_k60", "xgboost_depth7_regularized", 0.12, 0.06),
        _run_with_direction("all100", "xgboost_depth7_regularized", 0.08, 0.04),
    ])
    _mark_direction_replication_ready(summary)
    assert runner.decide_powerful_tabular_verdict(summary) == "DIRECTION_REPLICATION_REQUIRED"


def test_candidate_direction_without_yearly_confirmation_is_rejected():
    summary = runner.summarize_powerful_tabular_runs([
        _run_with_direction("nearest_k60", "xgboost_depth7_regularized", 0.12, 0.06),
        _run_with_direction("all100", "xgboost_depth7_regularized", 0.08, 0.04),
    ])
    candidate = summary["best_direction_candidate_only"]
    candidate["yearly_check_pass"] = False
    candidate["simple_trade_vs_closeout_baseline"] = {
        "select_delta": 0.01,
        "eval_delta": 0.01,
        "ranking_only_evidence": False,
    }
    assert runner.decide_powerful_tabular_verdict(summary) != "DIRECTION_REPLICATION_REQUIRED"


def test_candidate_direction_must_not_underperform_same_model_all100():
    summary = runner.summarize_powerful_tabular_runs([
        _run_with_direction("nearest_k60", "xgboost_depth7_regularized", 0.12, 0.06),
        _run_with_direction("all100", "xgboost_depth7_regularized", 0.13, 0.07),
    ])
    _mark_direction_replication_ready(summary)
    summary["best_direction_candidate_only"]["same_model_all100_comparison"] = {
        "available": True,
        "candidate_minus_all100_val_select": -0.01,
        "candidate_minus_all100_val_eval": -0.01,
        "all100_underperformance_explained": False,
    }
    assert runner.decide_powerful_tabular_verdict(summary) != "DIRECTION_REPLICATION_REQUIRED"


def test_candidate_direction_must_not_have_weaker_simple_trade_than_closeout():
    summary = runner.summarize_powerful_tabular_runs([
        _run_with_direction("nearest_k60", "xgboost_depth7_regularized", 0.12, 0.06),
        _run_with_direction("all100", "xgboost_depth7_regularized", 0.08, 0.04),
    ])
    _mark_direction_replication_ready(summary)
    summary["best_direction_candidate_only"]["simple_trade_vs_closeout_baseline"] = {
        "select_delta": -0.01,
        "eval_delta": -0.01,
        "ranking_only_evidence": False,
    }
    assert runner.decide_powerful_tabular_verdict(summary) != "DIRECTION_REPLICATION_REQUIRED"


def test_amplitude_without_direction_returns_pivot_amplitude():
    run = _run_with_direction("nearest_k80", "lightgbm_depth7_regularized", 0.04, 0.02)
    run["split_metrics"]["val_select"]["entry_up_3"]["spearman"] = 0.35
    run["split_metrics"]["val_eval"]["entry_up_3"]["spearman"] = 0.22
    summary = runner.summarize_powerful_tabular_runs([run])
    assert runner.decide_powerful_tabular_verdict(summary) == "PIVOT_AMPLITUDE"


def test_low_n_disclosure_does_not_affect_verdict():
    run = _run_with_direction("nearest_k60", "xgboost_depth7_regularized", 0.01, 0.01)
    run["split_metrics"]["low_n_disclosure"] = {
        "entry_log_ratio_12": {"spearman": 0.99},
        "simple_trade_12": {"mean": 1.0, "trade_count": 10, "long_count": 5, "short_count": 5},
    }
    summary = runner.summarize_powerful_tabular_runs([run])
    assert runner.decide_powerful_tabular_verdict(summary) == "REJECT_CAPACITY_EXPLANATION"


def test_forbidden_target_columns_are_rejected_by_powerful_runner():
    feature_names = [
        "slot_0_price_atr",
        "entry_log_ratio_12",
        "entry_up_12",
        "target_buy_H6_val",
    ]
    try:
        runner.validate_powerful_tabular_feature_names(feature_names)
    except ValueError as exc:
        assert "forbidden target/label columns" in str(exc)
    else:
        raise AssertionError("forbidden target columns were accepted")


def test_candidate_summary_includes_same_model_all100_comparison():
    candidate = _run_with_direction("nearest_k60", "xgboost_depth7_regularized", 0.12, 0.06)
    control = _run_with_direction("all100", "xgboost_depth7_regularized", 0.08, 0.04)
    summary = runner.summarize_powerful_tabular_runs([candidate, control])
    comparison = summary["best_direction_candidate_only"]["same_model_all100_comparison"]
    assert comparison["available"] is True
    assert comparison["all100_val_select_score"] == 0.08
    assert comparison["candidate_minus_all100_val_select"] == approx(0.04)


def test_freeze_like_verdicts_are_rejected_from_summary_artifact():
    summary = {"verdict": "FREEZE_PROPOSAL_ONLY"}
    try:
        runner.validate_allowed_powerful_tabular_verdicts(summary)
    except ValueError as exc:
        assert "freeze-like verdict is not allowed" in str(exc)
    else:
        raise AssertionError("freeze-like verdict was accepted")


def test_arg_parser_defaults_to_resume():
    parser = runner.build_arg_parser()
    args = parser.parse_args(["--entry-based-powerful-tabular"])
    assert args.entry_based_powerful_tabular is True
    assert args.resume is True


def test_arg_parser_accepts_no_resume():
    parser = runner.build_arg_parser()
    args = parser.parse_args(["--entry-based-powerful-tabular", "--no-resume"])
    assert args.resume is False


def test_run_config_hash_changes_when_scope_changes():
    config = runner.build_run_config(thread_count=24, dependency_versions={"catboost": "1.2.8"})
    changed = dict(config)
    changed["models"] = tuple(list(config["models"]) + ["extra_model_not_in_scope"])
    assert runner.compute_run_config_hash(config) != runner.compute_run_config_hash(changed)


def test_resume_rejects_incompatible_run_config():
    saved = {"run_config_hash": "old-hash"}
    current = {"run_config_hash": "new-hash"}
    try:
        runner.validate_resume_compatibility(saved, current)
    except RuntimeError as exc:
        assert "run_config_hash mismatch" in str(exc)
    else:
        raise AssertionError("resume accepted incompatible run config")


def test_normalization_contract_declares_train_only_fit():
    contract = runner.build_normalization_contract(
        model_key="xgboost_depth7_regularized",
        feature_names=("slot_0_price_atr", "slot_0_up_24"),
    )
    assert contract["mode"] == "raw_numeric"
    assert contract["fit_split"] == "train"
    assert contract["validation_splits_do_not_fit"] == ("val_select", "val_eval", "low_n_disclosure")
    assert contract["feature_count"] == 2


def test_report_metadata_is_available_at_top_level():
    report = {
        "run_config": {
            "schema_version": 1,
            "dependency_versions": {"catboost": "1.2.8"},
        },
        "summary": {"verdict": "PIVOT_AMPLITUDE"},
    }
    enriched = runner.enrich_powerful_tabular_report_metadata(report)
    assert enriched["schema_version"] == 1
    assert enriched["dependency_versions"] == {"catboost": "1.2.8"}
    assert enriched["verdict"] == "PIVOT_AMPLITUDE"
    assert enriched["normalization_contract"]["fit_split"] == "train"
    assert enriched["normalization_contract"]["per_run_path"] == "runs[].normalization_contract"


def test_horizon_overlap_check_reports_every_horizon():
    splits = {
        "train": runner._test_frame_for_overlap_check(("2020-12-30", "2020-12-31")),
        "val_select": runner._test_frame_for_overlap_check(("2021-01-01", "2023-06-30")),
        "val_eval": runner._test_frame_for_overlap_check(("2023-07-01", "2025-12-31")),
        "low_n_disclosure": runner._test_frame_for_overlap_check(("2026-01-01", "2026-03-31")),
    }
    check = runner.compute_split_horizon_overlap_check(splits)
    assert set(check["horizons"]) == {"H3", "H6", "H12", "H24"}
    assert "H24" in check["boundary_checks"]
    assert check["status"] in {"PASS", "DIAGNOSTIC_ONLY"}


def test_apply_horizon_embargo_removes_boundary_crossing_rows():
    splits = {
        "train": runner._test_frame_for_overlap_check(("2020-12-30", "2020-12-31")),
        "val_select": runner._test_frame_for_overlap_check(("2021-01-01", "2023-06-29")),
        "val_eval": runner._test_frame_for_overlap_check(("2023-07-01", "2025-12-31 12:00")),
        "low_n_disclosure": runner._test_frame_for_overlap_check(("2026-01-01", "2026-03-31")),
    }
    cleaned = runner.apply_horizon_embargo(splits, max_horizon_hours=24)
    check = runner.compute_split_horizon_overlap_check(cleaned)
    assert check["status"] == "PASS"


def test_convert_splits_keeps_2026_out_of_validation():
    old = {
        "train_core": runner._test_frame_for_overlap_check(("2020-01-01", "2020-12-31")),
        "val_stop": runner._test_frame_for_overlap_check(("2021-01-01", "2022-12-31")),
        "diagnostic_holdout": runner._test_frame_for_overlap_check(("2025-12-31", "2026-01-02")),
        "low_n_disclosure": runner._test_frame_for_overlap_check(("2026-01-01", "2026-03-31")),
    }
    splits = runner._convert_splits(old)
    assert pd.to_datetime(splits["validation"]["time"]).max() < pd.Timestamp("2026-01-01")
    assert pd.to_datetime(splits["low_n_disclosure"]["time"]).min() >= pd.Timestamp("2026-01-01")


def test_audit_warning_requires_recorded_decision():
    scale_audit = {"status": "WARNING", "warnings": [{"family": "TAIL_GT10"}]}
    try:
        runner.validate_audit_decisions(scale_audit, audit_decisions={})
    except RuntimeError as exc:
        assert "missing audit decision" in str(exc)
    else:
        raise AssertionError("audit warning without decision was accepted")


def test_audit_decisions_are_built_from_profile_flags():
    scale_audit = {
        "status": "WARNING",
        "profiles": {
            "nearest_k60": {
                "flags": [
                    {"feature": "nearest_00_valid", "split": "train", "flag": "NEAR_CONSTANT"},
                    {"feature": "nearest_01_up_24", "split": "validation", "flag": "TAIL_GT10"},
                ]
            }
        },
    }
    decisions = runner.build_audit_decisions(scale_audit)
    assert decisions["NEAR_CONSTANT"]["decision"] == "accept_as_warning"
    assert decisions["TAIL_GT10"]["decision"] == "accept_as_warning"
    runner.validate_audit_decisions(scale_audit, decisions)


def test_evaluate_job_reports_runtime_and_normalization_metadata(monkeypatch):
    frames = {
        "train": pd.DataFrame({"time": pd.date_range("2020-01-01", periods=3, freq="h")}),
        "val_select": pd.DataFrame({"time": pd.date_range("2021-01-01", periods=2, freq="h")}),
        "val_eval": pd.DataFrame({"time": pd.date_range("2024-01-01", periods=2, freq="h")}),
        "low_n_disclosure": pd.DataFrame({"time": pd.date_range("2026-01-01", periods=2, freq="h")}),
    }
    features = pd.DataFrame({"slot_0_price_atr": [0.1, 0.2, 0.3]})

    def fake_rep(frame, profile_key):
        return features.iloc[: len(frame)].reset_index(drop=True), {"feature_names": ["slot_0_price_atr"], "feature_count": 1}

    def fake_fit(**kwargs):
        preds = {}
        for split_name, frame in kwargs["eval_features"].items():
            preds[split_name] = pd.DataFrame({
                "pred_entry_up_3": np.zeros(len(frame)),
                "pred_entry_dn_3": np.zeros(len(frame)),
                "pred_entry_log_ratio_3": np.zeros(len(frame)),
            })
        return {"predictions_by_split": preds, "model_metadata": {"thread_count": kwargs["thread_count"]}}

    monkeypatch.setattr(runner, "CLOSEOUT_HORIZONS", ("3",))
    monkeypatch.setattr(runner, "build_closeout_representation_features", fake_rep)
    monkeypatch.setattr(runner, "fit_and_predict_powerful_tabular", fake_fit)
    monkeypatch.setattr(runner, "closeout_target_matrix", lambda frame: np.zeros((len(frame), 3), dtype=np.float32))
    monkeypatch.setattr(runner, "compute_closeout_split_metrics", lambda frame, preds: {
        "entry_log_ratio_3": {"spearman": 0.1},
        "entry_up_3": {"spearman": 0.2},
        "entry_dn_3": {"spearman": 0.3},
        "simple_trade_3": {"mean_signed_log_ratio": 0.01, "trade_count": len(frame)},
    })

    result = runner.evaluate_powerful_tabular_job(
        {"representation_key": "nearest_k60", "model_key": "xgboost_depth3_baseline", "seed": 42},
        frames,
        thread_count=24,
    )
    assert result["feature_count"] == 1
    assert result["actual_thread_count"] == 24
    assert result["status"] == "completed"
    assert result["error_text"] is None
    assert result["normalization_contract"]["fit_split"] == "train"


def test_yearly_metrics_are_computed_from_run_payload_not_constants():
    run = {
        "representation_key": "nearest_k60",
        "model_key": "xgboost_depth7_regularized",
        "seed": 42,
        "yearly_metrics": {
            "val_select": {
                "2021": {"entry_log_ratio_12": {"spearman": 0.10}},
                "2022": {"entry_log_ratio_12": {"spearman": -0.05}},
                "2023": {"entry_log_ratio_12": {"spearman": 0.20}},
            },
            "val_eval": {
                "2024": {"entry_log_ratio_12": {"spearman": 0.03}},
                "2025": {"entry_log_ratio_12": {"spearman": 0.04}},
            },
        },
    }
    selected = {
        "representation_key": "nearest_k60",
        "model_key": "xgboost_depth7_regularized",
        "seed": 42,
        "horizon": "H12",
    }
    metrics = runner.selected_yearly_metrics([run], selected, "entry_log_ratio")
    assert metrics["val_select"]["positive_years"] == 2
    assert metrics["val_select"]["without_best_year_score"] == approx(0.025)
    assert metrics["val_eval"]["positive_years"] == 2


def test_model_factory_rejects_unknown_model_key():
    try:
        runner.build_powerful_tabular_model("unknown_model_not_in_scope", seed=42, thread_count=24)
    except ValueError as exc:
        assert "unknown powerful tabular model" in str(exc)
    else:
        raise AssertionError("unknown model key was not rejected")
