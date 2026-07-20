from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

import ML.baseline.benchmark_entry_based_amplitude_movement as runner


def _canonical_fractal(price: float) -> str:
    values = ["0"] * 23
    values[1] = f"{price:.4f}"
    values[21] = "1"
    return ":".join(values)


def test_build_movement_targets_uses_max_up_dn_and_train_thresholds():
    frame = pd.DataFrame(
        {
            "entry_up_3": [1.0, 4.0, 2.0, 8.0],
            "entry_dn_3": [3.0, 1.0, 5.0, 2.0],
            "entry_up_6": [2.0, 2.0, 2.0, 9.0],
            "entry_dn_6": [1.0, 3.0, 4.0, 1.0],
            "entry_up_12": [1.0, 1.0, 7.0, 1.0],
            "entry_dn_12": [2.0, 5.0, 1.0, 1.0],
            "entry_up_24": [1.0, 6.0, 1.0, 1.0],
            "entry_dn_24": [1.0, 1.0, 8.0, 1.0],
        }
    )

    targets, thresholds = runner.build_movement_targets(frame)

    assert targets["entry_movement_3"].tolist() == [3.0, 4.0, 5.0, 8.0]
    assert targets["entry_movement_6"].tolist() == [2.0, 3.0, 4.0, 9.0]
    assert "movement_flag_q80_3" in targets
    assert "movement_flag_q90_3" in targets
    assert "movement_flag_q95_3" in targets
    assert thresholds["q80_3"] == np.quantile([3.0, 4.0, 5.0, 8.0], 0.80)


def test_build_movement_targets_can_reuse_train_thresholds():
    frame = pd.DataFrame(
        {
            "entry_up_3": [1.0, 10.0],
            "entry_dn_3": [2.0, 1.0],
            "entry_up_6": [1.0, 1.0],
            "entry_dn_6": [1.0, 1.0],
            "entry_up_12": [1.0, 1.0],
            "entry_dn_12": [1.0, 1.0],
            "entry_up_24": [1.0, 1.0],
            "entry_dn_24": [1.0, 1.0],
        }
    )
    thresholds = {f"q{q}_{h}": 5.0 for q in (80, 90, 95) for h in runner.TARGET_HORIZONS}

    targets, reused = runner.build_movement_targets(frame, thresholds)

    assert reused == thresholds
    assert targets["movement_flag_q80_3"].tolist() == [0, 1]


def test_build_movement_targets_rejects_incomplete_train_thresholds():
    frame = pd.DataFrame(
        {
            "entry_up_3": [1.0, 10.0],
            "entry_dn_3": [2.0, 1.0],
            "entry_up_6": [1.0, 1.0],
            "entry_dn_6": [1.0, 1.0],
            "entry_up_12": [1.0, 1.0],
            "entry_dn_12": [1.0, 1.0],
            "entry_up_24": [1.0, 1.0],
            "entry_dn_24": [1.0, 1.0],
        }
    )
    thresholds = {f"q{q}_{h}": 5.0 for q in (80, 90, 95) for h in runner.TARGET_HORIZONS}
    thresholds.pop("q95_24")

    try:
        runner.build_movement_targets(frame, thresholds)
    except ValueError as exc:
        message = str(exc)
    else:
        raise AssertionError("Expected ValueError for incomplete train_thresholds")

    assert "q95_24" in message
    assert "Missing train threshold keys" in message


def test_target_unit_contract_is_explicit():
    assert runner.TARGET_UNIT_CONTRACT["source_columns"] == "entry_up_H/entry_dn_H"
    assert runner.TARGET_UNIT_CONTRACT["movement_formula"] == "max(entry_up_H, entry_dn_H)"
    assert runner.TARGET_UNIT_CONTRACT["units"] == "same_as_entry_up_dn_targets"
    assert runner.TARGET_UNIT_CONTRACT["unit_description"] == "same_as_entry_up_dn_targets movement magnitude contract"
    assert runner.TARGET_UNIT_CONTRACT["source_contract_file"] == "docs/methodology/A8-feature-target-catalog.md"
    assert runner.TARGET_UNIT_CONTRACT["source_function_or_builder"] == "build_movement_targets"
    assert runner.TARGET_UNIT_CONTRACT["source_file"] == "ML/baseline/benchmark_entry_based_amplitude_movement.py"
    assert len(runner.TARGET_UNIT_CONTRACT["target_columns"]) == 16
    assert runner.TARGET_UNIT_CONTRACT["verdict"] == "PASS"
    assert runner.TARGET_UNIT_CONTRACT["normalization"] == "none"


def test_target_distribution_reports_split_quantiles():
    targets_by_split = {
        "train": pd.DataFrame({"entry_movement_3": [1.0, 2.0, 3.0, 4.0]}),
        "val_select": pd.DataFrame({"entry_movement_3": [2.0, 4.0, 6.0, 8.0]}),
    }

    rows = runner.compute_target_distribution(targets_by_split)

    train_h3 = next(row for row in rows if row["split"] == "train" and row["horizon"] == 3)
    assert train_h3["n"] == 4
    assert train_h3["p50"] == 2.5
    assert train_h3["p80"] == np.quantile([1.0, 2.0, 3.0, 4.0], 0.80)


def test_forbidden_target_columns_are_rejected():
    forbidden = [
        "entry_up_3",
        "entry_dn_24",
        "entry_log_ratio_12",
        "target_future",
        "label_win",
        "ret_6",
        "fav_12",
        "adv_12",
        "predict",
        "signal",
    ]
    assert all(runner.is_forbidden_input_column(column) for column in forbidden)
    assert not runner.is_forbidden_input_column("ATR")
    assert not runner.is_forbidden_input_column("hour_sin")


def test_time_only_clean_profile_contains_only_calendar_features():
    frame = pd.DataFrame({"time": ["2021-01-04 03:00:00"], "ATR": [1.2]})
    features, meta = runner.build_simple_feature_frame(frame, "time_only_clean")

    assert features.columns.tolist() == ["hour_sin", "hour_cos", "dow_sin", "dow_cos"]
    assert meta["profile"] == "time_only_clean"


def test_atr_only_profile_contains_only_atr():
    frame = pd.DataFrame({"time": ["2021-01-04 03:00:00"], "ATR": [1.2]})
    features, meta = runner.build_simple_feature_frame(frame, "atr_only")

    assert features.columns.tolist() == ["ATR"]
    assert features.iloc[0]["ATR"] == 1.2
    assert meta["profile"] == "atr_only"


def test_time_plus_atr_profile_contains_calendar_and_atr():
    frame = pd.DataFrame({"time": ["2021-01-04 03:00:00"], "ATR": [1.2]})
    features, meta = runner.build_simple_feature_frame(frame, "time_plus_atr")

    assert features.columns.tolist() == ["ATR", "hour_sin", "hour_cos", "dow_sin", "dow_cos"]
    assert meta["feature_contract_verdict"] == "PASS"


def test_pre_entry_distance_rejects_entry_open_as_input():
    frame = pd.DataFrame(
        {
            "time": ["2021-01-04 03:00:00"],
            "ATR": [0.5],
            "entry_open": [1.2300],
            "fractal0": [_canonical_fractal(1.2200)],
        }
    )

    features, meta = runner.build_simple_feature_frame(frame, "distance_to_level_pre_entry_only")

    assert features.empty
    assert meta["status"] == "SKIPPED_NO_DECISION_PRICE"
    assert meta["used_entry_open_as_input"] is False


def test_post_entry_distance_is_selection_forbidden():
    frame = pd.DataFrame(
        {
            "time": ["2021-01-04 03:00:00"],
            "ATR": [0.5],
            "entry_open": [1.2300],
            "fractal0": [_canonical_fractal(1.2200)],
        }
    )

    features, meta = runner.build_simple_feature_frame(frame, "distance_to_entry_open_post_entry_diagnostic_only")

    assert features.columns.tolist() == ["distance_to_entry_open_atr"]
    assert meta["post_entry_diagnostic_only"] is True
    assert meta["selection_eligible"] is False


def test_fractal_density_excludes_fractal0_anchor(monkeypatch):
    frame = pd.DataFrame(
        {
            "ATR": [0.05],
            "fractal0": ["f0"],
            "fractal1": ["f1"],
            "fractal2": ["f2"],
        }
    )
    prices = {"f0": [0.0, 1.20], "f1": [0.0, 1.25], "f2": [0.0, 1.40]}
    monkeypatch.setattr(runner, "_parse_fractal_values", lambda raw: prices.get(raw))

    features, meta = runner.build_simple_feature_frame(frame, "fractal_density_only")

    assert meta["excludes_fractal0"] is True
    assert features.iloc[0]["valid_fractal_count"] == 2
    assert features.iloc[0]["nearest_distance_atr"] == 1.0
    assert features.iloc[0]["count_within_1atr"] == 1


def test_simple_combined_retains_child_audit_metadata():
    frame = pd.DataFrame(
        {
            "time": ["2021-01-04 03:00:00"],
            "ATR": [0.5],
            "fractal0": [_canonical_fractal(1.2200)],
            "fractal1": [_canonical_fractal(1.2500)],
        }
    )

    features, meta = runner.build_simple_feature_frame(frame, "simple_combined")

    assert meta["components"] == ["atr_only", "time_only_clean", "fractal_density_only"]
    distance_child = next(child for child in meta["child_profiles"] if child["profile"] == "distance_to_level_pre_entry_only")
    assert distance_child["status"] == "SKIPPED_NO_DECISION_PRICE"
    assert distance_child["available_at_decision_time"] is False
    assert distance_child["feature_contract_verdict"] == "SKIPPED"
    assert distance_child["selection_eligible"] is False
    assert distance_child["used_entry_open_as_input"] is False
    assert distance_child["selected"] is False
    assert distance_child["feature_count"] == 0


def test_build_feature_profile_with_metadata_retains_split_metadata():
    splits = {
        "train": pd.DataFrame({"time": ["2021-01-04 03:00:00"], "ATR": [0.5], "close": [1.2300], "fractal0": [_canonical_fractal(1.2200)]}),
        "val": pd.DataFrame({"time": ["2021-01-05 03:00:00"], "ATR": [0.6], "close": [1.2500], "fractal0": [_canonical_fractal(1.2400)]}),
    }

    profile = runner.build_feature_profile_with_metadata(splits, "distance_to_level_pre_entry_only")

    assert set(profile.keys()) == {"features", "metadata"}
    assert set(profile["features"].keys()) == {"train", "val"}
    assert profile["metadata"]["train"]["profile"] == "distance_to_level_pre_entry_only"
    assert profile["metadata"]["train"]["available_at_decision_time"] is True
    assert profile["metadata"]["val"]["feature_contract_verdict"] == "PASS"


def test_scope_and_selection_policy_are_bounded():
    assert runner.OUTPUT_PREFIX == "entry_based_amplitude_movement"
    assert runner.SELECTION_POLICY == {
        "winner_metric": "val_select",
        "winner_unit": "seed_aggregate",
        "val_eval": "check_only",
        "low_n_disclosure_2026": "disclosure_only",
        "locked_test": "not_opened",
        "direction_selection": "forbidden",
        "decision_time": "pre_entry_decision",
    }
    jobs = runner.enumerate_jobs()
    assert jobs
    assert all(job["target_family"] == "entry_movement" for job in jobs)
    assert all(job["horizon"] in runner.TARGET_HORIZONS for job in jobs)
    ridge_seeds = {job["seed"] for job in jobs if job["model_key"] == "ridge_regression"}
    non_deterministic_seeds = {
        job["seed"]
        for job in jobs
        if not runner.is_model_deterministic(job["model_key"])
    }
    assert ridge_seeds == {42}
    assert non_deterministic_seeds == set(runner.SEEDS)


def test_config_hash_changes_when_scope_changes():
    base = runner.build_run_config()
    changed = dict(base)
    changed["profiles"] = list(base["profiles"]) + ["new_profile"]

    assert runner.compute_config_hash(base) != runner.compute_config_hash(changed)


@pytest.mark.parametrize("model_key", runner.MODEL_KEYS)
def test_make_model_passes_thread_count_to_parallel_estimators(model_key):
    model = runner.make_model(model_key, seed=42, threads=24)

    if model_key == "extra_trees_small":
        assert model.n_jobs == 24
        assert runner.model_thread_settings(model_key, threads=24)["n_jobs"] == 24
    if model_key == "hist_gradient_boosting":
        assert runner.model_thread_settings(model_key, threads=24)["thread_control"] == "not_supported_by_estimator"


def test_progress_json_contains_runtime_and_thread_metadata():
    progress = runner.build_initial_progress(total_runs=7, requested_threads=24, effective_threads=24)

    assert progress["total_runs"] == 7
    assert progress["done_runs"] == 0
    assert progress["requested_threads"] == 24
    assert progress["effective_threads"] == 24
    assert "started_at" in progress
    assert "elapsed_sec" in progress


def test_resume_key_and_completed_run_skip_policy():
    job = {"profile": "atr_only", "model_key": "hist_gradient_boosting", "seed": 42, "horizon": 3, "target_family": "entry_movement"}
    completed = {runner.resume_key(job)}

    assert runner.resume_key(job) == "atr_only/hist_gradient_boosting/42/3/entry_movement"
    assert runner.should_skip_job(job, completed_keys=completed, resume=True) is True
    assert runner.should_skip_job(job, completed_keys=completed, resume=False) is False


def test_aggregate_seed_metrics_uses_median_and_best_simple_baseline():
    rows = [
        {"profile": "atr_only", "model_key": "hist_gradient_boosting", "seed": seed, "horizon": 3, "target_family": "entry_movement", "val_select_spearman": value, "val_eval_spearman": 0.15, "val_select_top10_lift": 1.15, "val_eval_top10_lift": 1.08, "selection_eligible": True, "yearly_check_pass": True, "status": "completed", "deterministic": False}
        for seed, value in zip([42, 43, 44], [0.20, 0.21, 0.19])
    ]
    rows += [
        {"profile": "nearest_k60_sequence_flat", "model_key": "hist_gradient_boosting", "seed": seed, "horizon": 3, "target_family": "entry_movement", "val_select_spearman": value, "val_eval_spearman": eval_value, "val_select_top10_lift": 1.25, "val_eval_top10_lift": 1.12, "val_eval_top10_lift_ci_p05": 1.01, "selection_eligible": True, "yearly_check_pass": True, "status": "completed", "deterministic": False}
        for seed, value, eval_value in zip([42, 43, 44], [0.60, 0.24, 0.26], [0.18, 0.19, -0.01])
    ]

    aggregates = runner.aggregate_seed_metrics(rows)
    complex_row = next(row for row in aggregates if row["profile"] == "nearest_k60_sequence_flat")

    assert complex_row["val_select_spearman_median"] == 0.26
    assert complex_row["best_simple_profile"] == "atr_only"
    assert complex_row["val_eval_positive_seed_count"] == 2
    assert complex_row["deterministic"] is False
    assert complex_row["beats_best_simple_val_select"] is True


def test_verdict_uses_seed_aggregate_not_best_single_seed_or_2026():
    report = {
        "seed_aggregate": [
            {
                "profile": "nearest_k60_sequence_flat",
                "model_key": "hist_gradient_boosting",
                "horizon": 3,
                "target_family": "entry_movement",
                "deterministic": False,
                "n_seeds": 3,
                "val_select_spearman_median": 0.31,
                "val_eval_spearman_median": 0.20,
                "low_n_disclosure_spearman": -0.99,
                "val_eval_positive_seed_count": 2,
                "val_select_top10_lift_median": 1.25,
                "val_eval_top10_lift_median": 1.12,
                "val_eval_top10_lift_pass_seed_count": 2,
                "val_eval_top10_lift_ci_p05": 1.01,
                "best_simple_val_select_spearman_median": 0.20,
                "best_simple_val_eval_spearman_median": 0.15,
                "beats_best_simple_val_select": True,
                "beats_best_simple_val_eval": True,
                "yearly_check_pass": True,
                "selection_eligible": True,
                "post_entry_diagnostic_only": False,
            }
        ],
        "feature_audit": {"status": "PASS", "errors": []},
        "target_unit_contract": {"verdict": "PASS"},
    }
    assert runner.decide_verdict(report) == "MOVEMENT_REGIME_TRACE_FOUND"


def test_best_single_seed_does_not_drive_verdict():
    report = {
        "metrics": [
            {
                "profile": "nearest_k60_sequence_flat",
                "model_key": "hist_gradient_boosting",
                "seed": 42,
                "horizon": 3,
                "target_family": "entry_movement",
                "val_select_spearman": 0.60,
                "val_eval_spearman": 0.30,
            }
        ],
        "seed_aggregate": [],
        "feature_audit": {"status": "PASS", "errors": []},
        "target_unit_contract": {"verdict": "PASS"},
    }
    assert runner.decide_verdict(report) == "REJECT_MOVEMENT_REGIME"


def test_best_simple_baseline_matching_complex_explains_amplitude():
    report = {
        "seed_aggregate": [
            {
                "profile": "nearest_k60_sequence_flat",
                "model_key": "hist_gradient_boosting",
                "horizon": 3,
                "target_family": "entry_movement",
                "deterministic": False,
                "n_seeds": 3,
                "val_select_spearman_median": 0.31,
                "val_eval_spearman_median": 0.20,
                "val_eval_positive_seed_count": 3,
                "val_select_top10_lift_median": 1.25,
                "val_eval_top10_lift_median": 1.12,
                "val_eval_top10_lift_pass_seed_count": 3,
                "val_eval_top10_lift_ci_p05": 1.03,
                "best_simple_val_select_spearman_median": 0.30,
                "best_simple_val_eval_spearman_median": 0.19,
                "beats_best_simple_val_select": False,
                "beats_best_simple_val_eval": False,
                "yearly_check_pass": True,
                "selection_eligible": True,
                "post_entry_diagnostic_only": False,
            }
        ],
        "feature_audit": {"status": "PASS", "errors": []},
        "target_unit_contract": {"verdict": "PASS"},
    }
    assert runner.decide_verdict(report) == "AMPLITUDE_EXPLAINED_BY_SIMPLE_BASELINES"


def test_post_entry_diagnostic_profile_cannot_win():
    report = {
        "seed_aggregate": [
            {
                "profile": "distance_to_entry_open_post_entry_diagnostic_only",
                "model_key": "hist_gradient_boosting",
                "horizon": 3,
                "target_family": "entry_movement",
                "deterministic": False,
                "n_seeds": 3,
                "val_select_spearman_median": 0.80,
                "val_eval_spearman_median": 0.70,
                "val_eval_positive_seed_count": 3,
                "val_select_top10_lift_median": 1.60,
                "val_eval_top10_lift_median": 1.50,
                "val_eval_top10_lift_pass_seed_count": 3,
                "val_eval_top10_lift_ci_p05": 1.20,
                "best_simple_val_select_spearman_median": 0.10,
                "best_simple_val_eval_spearman_median": 0.10,
                "beats_best_simple_val_select": True,
                "beats_best_simple_val_eval": True,
                "yearly_check_pass": True,
                "selection_eligible": False,
                "post_entry_diagnostic_only": True,
            }
        ],
        "feature_audit": {"status": "PASS", "errors": []},
        "target_unit_contract": {"verdict": "PASS"},
    }
    assert runner.decide_verdict(report) == "REJECT_MOVEMENT_REGIME"


def test_forbidden_verdict_guard_rejects_non_diagnostic_labels():
    for verdict in sorted(runner.FORBIDDEN_VERDICTS):
        with pytest.raises(ValueError, match=verdict):
            runner.ensure_allowed_verdict(verdict)


def test_decide_verdict_aborts_on_feature_audit_error_or_target_contract_fail():
    ok_row = {
        "profile": "nearest_k60_sequence_flat",
        "model_key": "hist_gradient_boosting",
        "horizon": 3,
        "target_family": "entry_movement",
        "deterministic": False,
        "n_seeds": 3,
        "val_select_spearman_median": 0.31,
        "val_eval_spearman_median": 0.20,
        "val_eval_positive_seed_count": 2,
        "val_select_top10_lift_median": 1.25,
        "val_eval_top10_lift_median": 1.12,
        "val_eval_top10_lift_pass_seed_count": 2,
        "val_eval_top10_lift_ci_p05": 1.01,
        "best_simple_val_select_spearman_median": 0.20,
        "best_simple_val_eval_spearman_median": 0.15,
        "beats_best_simple_val_select": True,
        "beats_best_simple_val_eval": True,
        "yearly_check_pass": True,
        "selection_eligible": True,
        "post_entry_diagnostic_only": False,
    }
    report = {
        "seed_aggregate": [ok_row],
        "feature_audit": {"status": "ERROR", "errors": []},
        "target_unit_contract": {"verdict": "PASS"},
    }
    assert runner.decide_verdict(report) == "ABORT_CONTRACT_FAIL"
    report["feature_audit"] = {"status": "PASS", "errors": []}
    report["target_unit_contract"] = {"verdict": "FAIL"}
    assert runner.decide_verdict(report) == "ABORT_CONTRACT_FAIL"
    report["target_unit_contract"] = {"verdict": "PASS"}
    report["target_contract"] = {"verdict": "FAIL"}
    assert runner.decide_verdict(report) == "ABORT_CONTRACT_FAIL"


def test_audit_feature_frame_marks_price_coord_tails_as_requires_comparison():
    features = pd.DataFrame(
        {
            "token_00_price_coord_atr": [0.0] * 19 + [11.0],
            "token_00_keep": [0.0] * 19 + [12.0],
        }
    )

    rows, errors = runner.audit_feature_frame("nearest_k60_sequence_flat", "val_select", features)

    by_feature = {row["feature"]: row for row in rows}
    assert by_feature["token_00_price_coord_atr"]["family"] == "TAIL_GT10"
    assert by_feature["token_00_price_coord_atr"]["feature_family"] == "price_coord"
    assert by_feature["token_00_price_coord_atr"]["decision"] == "requires_no_price_coord_comparison"
    assert by_feature["token_00_price_coord_atr"]["rate"] == 0.05
    assert by_feature["token_00_keep"]["family"] == "TAIL_GT10"
    assert by_feature["token_00_keep"]["feature_family"] == "non_price_coord"
    assert by_feature["token_00_keep"]["decision"] == "accept_as_warning"
    assert errors == []


def test_audit_feature_frame_errors_on_non_finite_or_missing_profile():
    bad = pd.DataFrame({"x": [1.0, np.inf]})
    rows, errors = runner.audit_feature_frame("nearest_k60_sequence_flat", "train", bad)

    assert rows == []
    assert errors
    assert "non-finite" in errors[0]

    rows, errors = runner.audit_feature_frame("", "train", pd.DataFrame({"x": [1.0]}))
    assert rows == []
    assert errors
    assert "missing required profile" in errors[0]


def test_load_entry_based_splits_reuses_foundation_contract(monkeypatch):
    old_splits = {
        "train_core": pd.DataFrame({"time": ["2020-01-01"]}),
        "val_stop": pd.DataFrame({"time": ["2021-01-01"]}),
        "diagnostic_holdout": pd.DataFrame({"time": ["2022-01-01"]}),
        "low_n_disclosure": pd.DataFrame({"time": ["2026-01-02"]}),
    }
    converted = {
        "train": pd.DataFrame({"time": ["2020-01-01"]}),
        "validation": pd.DataFrame({"time": ["2021-01-01", "2022-01-01"]}),
        "low_n_disclosure": pd.DataFrame({"time": ["2026-01-02"]}),
    }
    val_roles = {
        "val_select": pd.DataFrame({"time": ["2021-01-01"]}),
        "val_eval": pd.DataFrame({"time": ["2022-01-01"]}),
    }
    calls = {"load": 0, "add_h24": 0, "convert": 0, "roles": 0, "embargo": 0}

    monkeypatch.setattr(runner.closeout.base, "load_entry_based_splits", lambda target_mode="rebuilt": calls.__setitem__("load", calls["load"] + 1) or old_splits)
    monkeypatch.setattr(runner.powerful, "_add_h24_targets_if_missing", lambda splits: calls.__setitem__("add_h24", calls["add_h24"] + 1) or splits)
    monkeypatch.setattr(runner.powerful, "_convert_splits", lambda splits: calls.__setitem__("convert", calls["convert"] + 1) or converted)
    monkeypatch.setattr(runner.powerful, "_split_validation_roles", lambda frame: calls.__setitem__("roles", calls["roles"] + 1) or val_roles)
    monkeypatch.setattr(runner.powerful, "apply_horizon_embargo", lambda splits, max_horizon_hours: calls.__setitem__("embargo", calls["embargo"] + 1) or dict(splits, embargo=max_horizon_hours))

    splits = runner.load_entry_based_splits()

    assert calls == {"load": 1, "add_h24": 1, "convert": 1, "roles": 1, "embargo": 1}
    assert splits["train"].equals(converted["train"])
    assert splits["val_select"].equals(val_roles["val_select"])
    assert splits["embargo"] == max(runner.TARGET_HORIZONS)


def test_complex_profile_builders_reuse_existing_nearest_and_sequence_helpers(monkeypatch):
    frame = pd.DataFrame({"ATR": [1.0], "time": ["2021-01-01 00:00:00"]})
    calls: dict[str, str] = {}

    def fake_build_representation_features(df, profile_key):
        calls["tabular"] = profile_key
        return pd.DataFrame({"nearest_00_price_coord_atr": [1.5], "keep_col": [2.0]}), {"coverage_summary": {"share_rows_0": 0.0}}

    def fake_build_sequence_tensor(df, representation):
        calls["sequence"] = representation
        return SimpleNamespace(
            tokens=np.asarray([[[1.0, 2.0, 3.0, 4.0]]], dtype=np.float32),
            mask=np.asarray([[True]], dtype=bool),
            feature_names=("price_coord_atr", "hour_sin", "keep_a", "keep_b"),
        )

    monkeypatch.setattr(runner.selection_ablation, "build_representation_features", fake_build_representation_features)
    monkeypatch.setattr(runner.sequence, "build_sequence_tensor", fake_build_sequence_tensor)

    tabular_features, _ = runner.build_feature_frame(frame, "nearest_k60_no_price_coord_tabular")
    sequence_features, _ = runner.build_feature_frame(frame, "nearest_k60_no_time_sequence_flat")

    assert calls["tabular"] == "nearest_k60"
    assert calls["sequence"] == "nearest_k60_sequence"
    assert tabular_features.columns.tolist() == ["keep_col"]
    assert "token_00_hour_sin" not in sequence_features.columns
    assert "token_00_price_coord_atr" in sequence_features.columns
    assert "token_00_mask" in sequence_features.columns


def test_done_keys_are_unique_and_success_removes_old_failed_record():
    job = {"profile": "atr_only", "model_key": "hist_gradient_boosting", "seed": 42, "horizon": 3, "target_family": "entry_movement"}
    key = runner.resume_key(job)
    report = {
        "metrics": [{"resume_key": key, "status": "completed"}],
        "failed_runs": [{"resume_key": key, "status": "failed"}, {"resume_key": "other", "status": "failed"}],
    }

    assert runner._done_keys_from_report(report) == {key, "other"}

    runner._remove_failed_run(report, key)

    assert report["failed_runs"] == [{"resume_key": "other", "status": "failed"}]
    assert len(runner._done_keys_from_report(report)) == 2


def test_align_feature_frames_reindexes_non_train_splits_to_train_columns():
    split_features = {
        "train": pd.DataFrame({"a": ["1.0"], "b": ["2.0"]}),
        "val_select": pd.DataFrame({"b": ["5.0"], "c": ["7.0"]}),
        "val_eval": pd.DataFrame({"a": ["9.0"]}),
        "low_n_disclosure": pd.DataFrame({"c": ["3.0"]}),
    }

    aligned = runner._align_feature_frames_to_train(split_features)

    assert aligned["train"].columns.tolist() == ["a", "b"]
    assert aligned["val_select"].columns.tolist() == ["a", "b"]
    assert aligned["val_select"].iloc[0].tolist() == [0.0, 5.0]
    assert aligned["low_n_disclosure"].iloc[0].tolist() == [0.0, 0.0]


def test_fit_single_job_returns_skipped_when_train_profile_is_empty(monkeypatch):
    splits = {
        "train": pd.DataFrame({"time": ["2020-01-01 00:00:00"]}),
        "val_select": pd.DataFrame({"time": ["2021-01-01 00:00:00"]}),
        "val_eval": pd.DataFrame({"time": ["2022-01-01 00:00:00"]}),
        "low_n_disclosure": pd.DataFrame({"time": ["2026-01-01 00:00:00"]}),
    }
    targets = {name: pd.DataFrame({"entry_movement_3": [1.0]}) for name in splits}

    monkeypatch.setattr(
        runner,
        "build_feature_profile_with_metadata",
        lambda splits, profile: {
            "features": {name: pd.DataFrame(index=frame.index) for name, frame in splits.items()},
            "metadata": {
                name: {
                    "profile": profile,
                    "status": "SKIPPED_EMPTY_TRAIN_FEATURES",
                    "feature_contract_verdict": "SKIPPED",
                    "available_at_decision_time": False,
                    "selection_eligible": False,
                    "post_entry_diagnostic_only": False,
                }
                for name in splits
            },
        },
    )

    result = runner._fit_single_job(
        {"profile": "nearest_k60_tabular", "model_key": "hist_gradient_boosting", "seed": 42, "horizon": 3, "target_family": "entry_movement"},
        splits,
        targets,
        requested_threads=24,
        effective_threads=24,
    )

    assert result["run"]["status"] == "skipped"
    assert result["run"]["skip_reason"] == "SKIPPED_EMPTY_TRAIN_FEATURES"
    assert result["quantiles"] == []
    assert result["yearly"] == []


def test_fit_single_job_aligns_split_columns_before_predict(monkeypatch):
    class DummyModel:
        def __init__(self):
            self.fit_shape = None
            self.predict_shapes: list[tuple[int, int]] = []

        def fit(self, x, y):
            self.fit_shape = x.shape

        def predict(self, x):
            self.predict_shapes.append(x.shape)
            return np.zeros(x.shape[0], dtype=float)

    model = DummyModel()
    monkeypatch.setattr(runner, "make_model", lambda model_key, seed, threads: model)
    monkeypatch.setattr(
        runner,
        "build_feature_profile_with_metadata",
        lambda splits, profile: {
            "features": {
                "train": pd.DataFrame({"a": [1.0, 2.0]}),
                "val_select": pd.DataFrame({"b": [5.0, 6.0]}),
                "val_eval": pd.DataFrame({"c": [7.0, 8.0]}),
                "low_n_disclosure": pd.DataFrame({"d": [9.0, 10.0]}),
            },
            "metadata": {name: {"profile": profile, "status": "PASS", "feature_contract_verdict": "PASS", "available_at_decision_time": True, "selection_eligible": True, "post_entry_diagnostic_only": False} for name in splits},
        },
    )

    splits = {
        "train": pd.DataFrame({"time": ["2020-01-01 00:00:00", "2020-02-01 00:00:00"]}),
        "val_select": pd.DataFrame({"time": ["2021-01-01 00:00:00", "2023-01-01 00:00:00"]}),
        "val_eval": pd.DataFrame({"time": ["2022-01-01 00:00:00", "2024-01-01 00:00:00"]}),
        "low_n_disclosure": pd.DataFrame({"time": ["2026-01-01 00:00:00", "2026-02-01 00:00:00"]}),
    }
    targets = {name: pd.DataFrame({"entry_movement_3": [1.0, 2.0]}) for name in splits}

    result = runner._fit_single_job(
        {"profile": "nearest_k60_tabular", "model_key": "hist_gradient_boosting", "seed": 42, "horizon": 3, "target_family": "entry_movement"},
        splits,
        targets,
        requested_threads=24,
        effective_threads=24,
    )

    assert result["run"]["status"] == "completed"
    assert result["run"]["model_thread_settings"]["thread_control"] == "not_supported_by_estimator"
    assert model.fit_shape == (2, 1)
    assert model.predict_shapes == [(2, 1), (2, 1), (2, 1)]


def test_yearly_check_requires_two_positive_years_and_no_single_year_concentration():
    concentrated = [
        {"split": "val_select", "year": 2021, "spearman": 0.70},
        {"split": "val_select", "year": 2022, "spearman": 0.10},
    ]
    negative_residual = [
        {"split": "val_select", "year": 2021, "spearman": 0.70},
        {"split": "val_select", "year": 2022, "spearman": 0.11},
        {"split": "val_select", "year": 2023, "spearman": -0.40},
        {"split": "val_select", "year": 2024, "spearman": -0.35},
    ]
    balanced = [
        {"split": "val_eval", "year": 2021, "spearman": 0.55},
        {"split": "val_eval", "year": 2022, "spearman": 0.25},
        {"split": "val_eval", "year": 2023, "spearman": -0.10},
    ]

    assert runner.yearly_check_pass_for_split(concentrated, "val_select") is False
    assert runner.yearly_check_pass_for_split(negative_residual, "val_select") is False
    assert runner.yearly_check_pass_for_split(balanced, "val_eval") is True


def test_fit_single_job_yearly_rows_include_run_identity(monkeypatch):
    splits = {
        name: pd.DataFrame(
                {
                    "time": ["2021-01-01", "2022-01-01", "2023-01-01"],
                    "ATR": [1.0, 2.0, 3.0],
                    "entry_up_3": [1.0, 2.0, 3.0],
                    "entry_dn_3": [0.5, 1.5, 2.5],
                    "entry_up_6": [1.0, 2.0, 3.0],
                    "entry_dn_6": [0.5, 1.5, 2.5],
                    "entry_up_12": [1.0, 2.0, 3.0],
                    "entry_dn_12": [0.5, 1.5, 2.5],
                    "entry_up_24": [1.0, 2.0, 3.0],
                    "entry_dn_24": [0.5, 1.5, 2.5],
                }
            )
        for name in ("train", "val_select", "val_eval", "low_n_disclosure")
    }
    targets_by_split = {name: runner.build_movement_targets(frame)[0] for name, frame in splits.items()}
    job = {
        "profile": "atr_only",
        "model_key": "ridge_regression",
        "seed": 42,
        "horizon": 3,
        "target_family": "entry_movement",
    }

    result = runner._fit_single_job(job, splits, targets_by_split, requested_threads=1, effective_threads=1)

    assert result["yearly"]
    for row in result["yearly"]:
        assert row["profile"] == "atr_only"
        assert row["model_key"] == "ridge_regression"
        assert row["seed"] == 42
        assert row["target_family"] == "entry_movement"


def test_deterministic_flag_marks_only_ridge_as_deterministic():
    assert runner.is_model_deterministic("ridge_regression") is True
    assert runner.is_model_deterministic("hist_gradient_boosting") is False
    assert runner.is_model_deterministic("extra_trees_small") is False


def test_failed_run_records_elapsed_and_original_start(monkeypatch, tmp_path):
    run_config = dict(runner.build_run_config(), requested_threads=24, effective_threads=24)
    report = {
        "metrics": [],
        "rows": [],
        "quantiles": [],
        "yearly": [],
        "seed_aggregate": [],
        "target_distribution": [],
        "feature_audit_rows": [],
        "failed_runs": [],
        "progress": {"done_runs": 0, "total_runs": 1, "completed_keys": [], "elapsed_sec": 0.0},
        "run_config_hash": runner.compute_config_hash(run_config),
    }
    job = {"profile": "atr_only", "model_key": "hist_gradient_boosting", "seed": 42, "horizon": 3, "target_family": "entry_movement"}

    for attr, filename in {
        "REPORT_JSON_PATH": "report.json",
        "REPORT_METRICS_PATH": "metrics.csv",
        "REPORT_SEED_AGGREGATE_PATH": "seed.csv",
        "REPORT_QUANTILES_PATH": "quantiles.csv",
        "REPORT_YEARLY_PATH": "yearly.csv",
        "REPORT_TARGET_DISTRIBUTION_PATH": "target.csv",
        "REPORT_FEATURE_AUDIT_PATH": "feature.csv",
        "REPORT_ROWS_PATH": "rows.csv",
    }.items():
        monkeypatch.setattr(runner, attr, tmp_path / filename)
    monkeypatch.setattr(runner, "enumerate_jobs", lambda: [job])
    monkeypatch.setattr(runner, "_load_or_init_report", lambda *args, **kwargs: report)
    monkeypatch.setattr(
        runner,
        "load_entry_based_splits",
        lambda: {
            name: pd.DataFrame(
                {
                    "time": ["2020-01-01"],
                    "ATR": [1.0],
                    "entry_up_3": [1.0],
                    "entry_dn_3": [1.0],
                    "entry_up_6": [1.0],
                    "entry_dn_6": [1.0],
                    "entry_up_12": [1.0],
                    "entry_dn_12": [1.0],
                    "entry_up_24": [1.0],
                    "entry_dn_24": [1.0],
                }
            )
            for name in ("train", "val_select", "val_eval", "low_n_disclosure")
        },
    )
    monkeypatch.setattr(runner, "_fit_single_job", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("boom")))

    result = runner.run_entry_based_amplitude_movement(SimpleNamespace(resume=True, threads=24))

    failed = result["failed_runs"][0]
    assert failed["status"] == "failed"
    assert failed["elapsed_sec"] >= 0.0
    assert failed["started_at"] <= failed["finished_at"]
    assert result["progress"]["done_runs"] == 1
