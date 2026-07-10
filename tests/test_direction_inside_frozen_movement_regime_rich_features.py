from __future__ import annotations

import pandas as pd
import pytest

from ML.baseline import benchmark_direction_inside_frozen_movement_regime_rich_features as runner


def test_config_uses_full_train_not_selected_train():
    config = runner.rich_direction_config()

    assert config["training_scope"] == "full_train"
    assert config["frozen_mask_usage"] == "evaluation_only"
    assert config["selection_metric"] == "val_select_inside_mask"
    assert config["validation_roles"] == {
        "val_stop": "not_used_no_early_stopping",
        "val_select": "selection",
        "val_eval": "confirmation",
    }
    assert "score" in config["forbidden_input_columns"]
    assert "selected" in config["forbidden_input_columns"]


def test_feature_profiles_include_old_control_and_borrowed_profiles():
    assert runner.RICH_FEATURE_PROFILES == (
        "simple_combined",
        "nearest_k60",
        "nearest_k80",
        "corridor_5atr",
        "all100",
    )


def test_nearest_k80_is_exploratory_control_not_positive_verdict_source():
    config = runner.rich_direction_config()

    assert "nearest_k80" in runner.RICH_FEATURE_PROFILES
    assert config["exploratory_only_profiles"] == ["nearest_k80"]


def test_forbidden_feature_audit_rejects_top_level_targets_and_mask_columns():
    features = pd.DataFrame(
        {
            "ATR": [1.0],
            "entry_up_3": [2.0],
            "selected": [True],
            "score": [10.0],
        }
    )

    audit = runner.audit_forbidden_feature_columns(features)

    assert audit["status"] == "ERROR"
    assert set(audit["forbidden_present"]) == {"entry_up_3", "selected", "score"}


def test_feature_availability_allows_targets_in_source_frame_when_features_are_clean():
    frame = pd.DataFrame(
        {
            "ATR": [1.0],
            "fractal0": ["0|0|100.0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0"],
            "fractal1": ["1|0|99.0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0"],
            "entry_up_3": [2.0],
            "entry_dn_3": [1.0],
        }
    )
    features = pd.DataFrame({"fractal1_shift": [3.0], "fractal1_up_3": [1.0]})

    audit = runner.audit_feature_availability(frame, features, {"feature_families": ["updn_full"]})

    assert audit["status"] == "PASS"


def test_rich_feature_metadata_for_json_exposes_feature_columns(monkeypatch):
    def fake_build_simple_feature_frame(frame, profile):
        return pd.DataFrame({"ATR": [1.0, 2.0]}, index=frame.index), {"profile": profile}

    monkeypatch.setattr(runner.amplitude, "build_simple_feature_frame", fake_build_simple_feature_frame)
    splits = {
        "train": pd.DataFrame(
            {
                "time": ["2020-01-01 00:00:00", "2020-01-02 00:00:00"],
                "ATR": [1.0, 2.0],
                "fractal0": ["x", "y"],
                "fractal1": ["a", "b"],
                "entry_up_3": [2.0, 1.0],
                "entry_dn_3": [1.0, 2.0],
            }
        )
    }

    runner.build_rich_feature_frames(splits, "simple_combined")
    metadata = runner.rich_feature_metadata_for_json()

    assert metadata["splits"]["train"]["feature_names"] == ["ATR"]


def test_attach_frozen_mask_uses_split_row_id_not_time():
    splits = {
        "train": pd.DataFrame(
            {
                "time": ["2020-01-01 00:00:00", "2020-01-01 00:00:00"],
                "entry_up_3": [2.0, 1.0],
                "entry_dn_3": [1.0, 2.0],
            }
        )
    }
    scores = pd.DataFrame(
        {
            "split": ["train", "train"],
            "split_row_id": [0, 1],
            "time": ["2020-01-01 00:00:00", "2020-01-01 00:00:00"],
            "selected": [True, False],
            "score": [10.0, 1.0],
        }
    )

    out = runner.attach_frozen_mask_by_row_id(splits, scores)

    assert out["train"]["frozen_selected"].tolist() == [True, False]


def test_attach_frozen_mask_parses_csv_style_selected_values():
    splits = {
        "train": pd.DataFrame(
            {
                "time": ["2020-01-01 00:00:00", "2020-01-02 00:00:00", "2020-01-03 00:00:00"],
                "entry_up_3": [2.0, 1.0, 3.0],
                "entry_dn_3": [1.0, 2.0, 1.0],
            }
        )
    }
    scores = pd.DataFrame(
        {
            "split": ["train", "train", "train"],
            "split_row_id": [0, 1, 2],
            "selected": ["True", "False", "0"],
        }
    )

    out = runner.attach_frozen_mask_by_row_id(splits, scores)

    assert out["train"]["frozen_selected"].tolist() == [True, False, False]


def test_attach_frozen_mask_requires_split_row_id():
    splits = {
        "train": pd.DataFrame(
            {
                "time": ["2020-01-01 00:00:00"],
                "entry_up_3": [2.0],
                "entry_dn_3": [1.0],
            }
        )
    }
    scores = pd.DataFrame(
        {
            "split": ["train"],
            "selected": [True],
            "score": [10.0],
        }
    )

    with pytest.raises(ValueError, match="split_row_id"):
        runner.attach_frozen_mask_by_row_id(splits, scores)


@pytest.mark.parametrize("split_row_id", ([0.5], [1.5]))
def test_attach_frozen_mask_rejects_non_integer_split_row_id(split_row_id):
    splits = {
        "train": pd.DataFrame(
            {
                "time": ["2020-01-01 00:00:00"],
                "entry_up_3": [2.0],
                "entry_dn_3": [1.0],
            }
        )
    }
    scores = pd.DataFrame(
        {
            "split": ["train"],
            "split_row_id": split_row_id,
            "selected": [True],
            "score": [10.0],
        }
    )

    with pytest.raises(ValueError, match="split_row_id"):
        runner.attach_frozen_mask_by_row_id(splits, scores)


def test_attach_frozen_mask_aborts_when_join_changes_row_count():
    splits = {
        "train": pd.DataFrame(
            {
                "time": ["2020-01-01 00:00:00", "2020-01-02 00:00:00"],
                "entry_up_3": [2.0, 1.0],
                "entry_dn_3": [1.0, 2.0],
            }
        )
    }
    scores = pd.DataFrame(
        {
            "split": ["train"],
            "split_row_id": [0],
            "selected": [True],
            "score": [10.0],
        }
    )

    with pytest.raises(ValueError, match="row count"):
        runner.attach_frozen_mask_by_row_id(splits, scores)


def test_attach_frozen_mask_aborts_when_row_ids_do_not_match_split_identity():
    splits = {
        "train": pd.DataFrame(
            {
                "time": ["2020-01-01 00:00:00", "2020-01-02 00:00:00"],
                "entry_up_3": [2.0, 1.0],
                "entry_dn_3": [1.0, 2.0],
            }
        )
    }
    scores = pd.DataFrame(
        {
            "split": ["train", "train"],
            "split_row_id": [0, 2],
            "selected": [True, False],
            "score": [10.0, 1.0],
        }
    )

    with pytest.raises(ValueError, match="split_row_id mismatch"):
        runner.attach_frozen_mask_by_row_id(splits, scores)


def test_target_families_and_horizons_are_borrowed_from_previous_studies():
    assert runner.RICH_TARGET_HORIZONS == (3, 6, 12, 24)
    assert runner.RICH_TARGET_FAMILIES == (
        "entry_log_ratio",
        "entry_up_dn_delta",
        "entry_up_dn_classifier",
    )


def test_build_direction_targets_uses_log_ratio_and_up_dn_comparison():
    frame = pd.DataFrame(
        {
            "entry_log_ratio_12": [0.4, -0.2, 0.0],
            "entry_up_12": [5.0, 1.0, 2.0],
            "entry_dn_12": [1.0, 3.0, 2.0],
        }
    )

    targets = runner.build_direction_targets(frame, 12)

    assert targets["direction_from_log_ratio"].tolist() == [1, -1, 0]
    assert targets["direction_from_up_dn"].tolist() == [1, -1, 0]


def test_dead_zone_marks_small_log_ratio_as_neutral():
    frame = pd.DataFrame(
        {
            "entry_log_ratio_3": [0.2, 0.000001, -0.3],
            "entry_up_3": [3.0, 2.0, 1.0],
            "entry_dn_3": [1.0, 2.0, 4.0],
        }
    )

    targets = runner.build_direction_targets(frame, 3, dead_zone=0.01)

    assert targets["direction_from_log_ratio"].tolist() == [1, 0, -1]


def test_training_scope_counts_full_train_and_selected_separately():
    frame = pd.DataFrame({"frozen_selected": [True, False, True, False]})

    counts = runner.training_scope_counts(frame)

    assert counts == {
        "train_rows_used_for_fit": 4,
        "train_frozen_selected_rows": 2,
        "training_scope": "full_train",
    }


def test_sample_size_gate_blocks_tiny_masked_validation():
    metrics_input = pd.DataFrame(
        {
            "split": ["val_select"] * 50,
            "frozen_selected": [True] * 50,
            "target_direction": [1, -1] * 25,
        }
    )

    gate = runner.masked_sample_size_gate(metrics_input, split="val_select")

    assert gate["status"] == "FAIL"
    assert "min_masked_rows" in gate["reasons"]


def test_winner_selection_uses_val_select_inside_mask_not_val_eval_or_full_split():
    metrics = pd.DataFrame(
        [
            {"run_id": "a", "split": "val_select", "slice": "frozen_selected", "balanced_accuracy": 0.60},
            {"run_id": "c", "split": "val_select", "slice": "full", "balanced_accuracy": 0.95},
            {"run_id": "a", "split": "val_eval", "slice": "frozen_selected", "balanced_accuracy": 0.40},
            {"run_id": "b", "split": "val_select", "slice": "frozen_selected", "balanced_accuracy": 0.55},
            {"run_id": "b", "split": "val_eval", "slice": "frozen_selected", "balanced_accuracy": 0.80},
        ]
    )

    winner = runner.select_rich_direction_winner(metrics)

    assert winner["run_id"] == "a"
    assert winner["selection_split"] == "val_select"
    assert winner["selection_slice"] == "frozen_selected"


def test_run_rich_direction_experiment_writes_real_metric_rows(monkeypatch):
    def fake_build_rich_feature_frames(splits, profile):
        return {
            split_name: pd.DataFrame({"feature": frame["feature"].to_numpy(dtype=float)}, index=frame.index)
            for split_name, frame in splits.items()
        }

    monkeypatch.setattr(runner, "build_rich_feature_frames", fake_build_rich_feature_frames)
    splits = {
        split_name: pd.DataFrame(
            {
                "feature": [0.0, 1.0, 0.0, 1.0],
                "entry_log_ratio_3": [-0.4, 0.5, -0.3, 0.6],
                "entry_up_3": [1.0, 3.0, 1.0, 3.0],
                "entry_dn_3": [3.0, 1.0, 3.0, 1.0],
            }
        )
        for split_name in ("train", "val_select", "val_eval", "low_n_disclosure")
    }
    scores = pd.DataFrame(
        [
            {"split": split_name, "split_row_id": row_id, "selected": row_id in (0, 1)}
            for split_name in splits
            for row_id in range(4)
        ]
    )

    result = runner.run_rich_direction_experiment(
        splits,
        scores,
        {
            "feature_profiles": ["simple_combined"],
            "target_horizons": [3],
            "target_families": ["entry_log_ratio"],
            "model_keys": ["extra_trees"],
            "min_masked_rows": 1,
            "min_active_sign_rows": 1,
        },
    )

    assert result["summary"]["contract_status"] == "PASS"
    assert result["summary"]["training_scope"] == "full_train"
    assert len(result["metrics"]) >= 6
    assert set(result["metrics"]["split"]) >= {"val_select", "val_eval", "low_n_disclosure"}
    assert {"full", "frozen_selected"} <= set(result["metrics"]["slice"])
    assert len(result["rows"]) > 0


def test_run_rich_direction_experiment_ignores_combined_validation_split(monkeypatch):
    def fake_build_rich_feature_frames(splits, profile):
        assert "validation" not in splits
        return {
            split_name: pd.DataFrame({"feature": frame["feature"].to_numpy(dtype=float)}, index=frame.index)
            for split_name, frame in splits.items()
        }

    monkeypatch.setattr(runner, "build_rich_feature_frames", fake_build_rich_feature_frames)
    base_frame = pd.DataFrame(
        {
            "feature": [0.0, 1.0, 0.0, 1.0],
            "entry_log_ratio_3": [-0.4, 0.5, -0.3, 0.6],
            "entry_up_3": [1.0, 3.0, 1.0, 3.0],
            "entry_dn_3": [3.0, 1.0, 3.0, 1.0],
        }
    )
    splits = {split_name: base_frame.copy() for split_name in ("train", "validation", "val_select", "val_eval", "low_n_disclosure")}
    scores = pd.DataFrame(
        [
            {"split": split_name, "split_row_id": row_id, "selected": row_id in (0, 1)}
            for split_name in ("train", "val_select", "val_eval", "low_n_disclosure")
            for row_id in range(4)
        ]
    )

    result = runner.run_rich_direction_experiment(
        splits,
        scores,
        {
            "feature_profiles": ["simple_combined"],
            "target_horizons": [3],
            "target_families": ["entry_log_ratio"],
            "model_keys": ["extra_trees"],
            "min_masked_rows": 1,
            "min_active_sign_rows": 1,
        },
    )

    assert result["summary"]["contract_status"] == "PASS"


@pytest.mark.parametrize("model_key", runner.RICH_MODEL_KEYS)
def test_make_direction_model_passes_thread_count_to_parallel_estimators(model_key):
    model = runner._make_direction_model(model_key, {"seed": 42, "threads": 24})

    settings = runner.model_thread_settings(model_key, threads=24)
    if settings["n_jobs"] is not None:
        assert model.n_jobs == 24
    assert settings["requested_threads"] == 24


def test_progress_json_contains_runtime_and_thread_metadata():
    progress = runner.build_initial_progress(total_runs=7, requested_threads=24, effective_threads=24)

    assert progress["done_runs"] == 0
    assert progress["total_runs"] == 7
    assert progress["requested_threads"] == 24
    assert progress["effective_threads"] == 24
    assert "started_at" in progress
    assert "finished_at" in progress
    assert "elapsed_sec" in progress


def test_resume_key_and_completed_run_skip_policy():
    job = {
        "profile": "simple_combined",
        "model_key": "extra_trees",
        "seed": 42,
        "horizon": 3,
        "target_family": "entry_log_ratio",
    }
    completed = {runner.resume_key(job)}

    assert runner.resume_key(job) == "simple_combined/42/extra_trees/H3/entry_log_ratio"
    assert runner.should_skip_job(job, completed_keys=completed, resume=True) is True
    assert runner.should_skip_job(job, completed_keys=completed, resume=False) is False


def test_arg_parser_defaults_to_resume_and_accepts_no_resume():
    parser = runner.build_arg_parser()

    assert parser.parse_args([]).resume is True
    assert parser.parse_args(["--no-resume"]).resume is False


def test_run_rich_direction_experiment_resume_skips_completed_jobs(monkeypatch, tmp_path):
    def fake_build_rich_feature_frames(splits, profile):
        return {
            split_name: pd.DataFrame({"feature": frame["feature"].to_numpy(dtype=float)}, index=frame.index)
            for split_name, frame in splits.items()
        }

    calls = {"fit": 0}
    original_make_model = runner._make_direction_model

    def counting_make_model(model_key, config):
        calls["fit"] += 1
        return original_make_model(model_key, config)

    monkeypatch.setattr(runner, "build_rich_feature_frames", fake_build_rich_feature_frames)
    monkeypatch.setattr(runner, "_make_direction_model", counting_make_model)
    splits = {
        split_name: pd.DataFrame(
            {
                "feature": [0.0, 1.0, 0.0, 1.0],
                "entry_log_ratio_3": [-0.4, 0.5, -0.3, 0.6],
                "entry_up_3": [1.0, 3.0, 1.0, 3.0],
                "entry_dn_3": [3.0, 1.0, 3.0, 1.0],
            }
        )
        for split_name in ("train", "val_select", "val_eval", "low_n_disclosure")
    }
    scores = pd.DataFrame(
        [
            {"split": split_name, "split_row_id": row_id, "selected": row_id in (0, 1)}
            for split_name in splits
            for row_id in range(4)
        ]
    )
    config = {
        "feature_profiles": ["simple_combined"],
        "target_horizons": [3],
        "target_families": ["entry_log_ratio"],
        "model_keys": ["extra_trees"],
        "min_masked_rows": 1,
        "min_active_sign_rows": 1,
        "threads": 24,
    }
    output_prefix = tmp_path / "rich_direction_resume"

    first = runner.run_rich_direction_experiment(splits, scores, config, output_prefix=output_prefix, resume=True)
    first_fit_count = calls["fit"]
    second = runner.run_rich_direction_experiment(splits, scores, config, output_prefix=output_prefix, resume=True)

    assert first_fit_count == 1
    assert calls["fit"] == 1
    assert first["summary"]["progress"]["done_runs"] == 1
    assert second["summary"]["progress"]["done_runs"] == 1
    assert second["summary"]["progress"]["completed_keys"] == ["simple_combined/42/extra_trees/H3/entry_log_ratio"]
    assert len(second["metrics"]) == len(first["metrics"])


def test_resume_discards_legacy_rows_without_current_resume_key(monkeypatch, tmp_path):
    def fake_build_rich_feature_frames(splits, profile):
        return {
            split_name: pd.DataFrame({"feature": frame["feature"].to_numpy(dtype=float)}, index=frame.index)
            for split_name, frame in splits.items()
        }

    monkeypatch.setattr(runner, "build_rich_feature_frames", fake_build_rich_feature_frames)
    splits = {
        split_name: pd.DataFrame(
            {
                "feature": [0.0, 1.0, 0.0, 1.0],
                "entry_log_ratio_3": [-0.4, 0.5, -0.3, 0.6],
                "entry_up_3": [1.0, 3.0, 1.0, 3.0],
                "entry_dn_3": [3.0, 1.0, 3.0, 1.0],
            }
        )
        for split_name in ("train", "val_select", "val_eval", "low_n_disclosure")
    }
    scores = pd.DataFrame(
        [
            {"split": split_name, "split_row_id": row_id, "selected": row_id in (0, 1)}
            for split_name in splits
            for row_id in range(4)
        ]
    )
    output_prefix = tmp_path / "rich_direction_legacy_resume"
    key = "simple_combined/42/extra_trees/H3/entry_log_ratio"
    output_prefix.with_suffix(".json").write_text(
        runner.json.dumps(
            {
                "progress": {"completed_keys": [key]},
                "runs": [{"resume_key": key, "status": "completed"}, {"status": "legacy"}],
                "failed_runs": [{"resume_key": "legacy", "status": "failed"}],
            }
        ),
        encoding="utf-8",
    )
    pd.DataFrame(
        [
            {
                "run_id": "legacy",
                "profile": "legacy",
                "horizon": 3,
                "target_family": "entry_log_ratio",
                "model_key": "extra_trees",
                "split": "val_select",
                "slice": "frozen_selected",
                "balanced_accuracy": 0.99,
                "accuracy": 0.99,
                "n": 1,
                "positive_rows": 1,
                "negative_rows": 0,
                "sample_size_gate": "PASS",
                "gate_reasons": "",
                "resume_key": "",
                "seed": "",
            },
            {
                "run_id": "simple_combined|H3|entry_log_ratio|extra_trees",
                "profile": "simple_combined",
                "horizon": 3,
                "target_family": "entry_log_ratio",
                "model_key": "extra_trees",
                "split": "val_select",
                "slice": "frozen_selected",
                "balanced_accuracy": 0.55,
                "accuracy": 0.55,
                "n": 4,
                "positive_rows": 2,
                "negative_rows": 2,
                "sample_size_gate": "PASS",
                "gate_reasons": "",
                "resume_key": key,
                "seed": 42,
            },
        ]
    ).to_csv(f"{output_prefix}_metrics.csv", index=False)
    pd.DataFrame(
        [
            {"run_id": "legacy", "resume_key": "", "split": "val_select", "row_id": 0, "prediction": 1},
            {"run_id": "simple_combined|H3|entry_log_ratio|extra_trees", "resume_key": key, "split": "val_select", "row_id": 0, "prediction": 1},
        ]
    ).to_csv(f"{output_prefix}_rows.csv", index=False)

    result = runner.run_rich_direction_experiment(
        splits,
        scores,
        {
            "feature_profiles": ["simple_combined"],
            "target_horizons": [3],
            "target_families": ["entry_log_ratio"],
            "model_keys": ["extra_trees"],
            "min_masked_rows": 1,
            "min_active_sign_rows": 1,
        },
        output_prefix=output_prefix,
        resume=True,
    )

    assert set(result["metrics"]["resume_key"]) == {key}
    assert set(result["rows"]["resume_key"]) == {key}
    assert result["summary"]["runs"] == [{"resume_key": key, "status": "completed"}]
    assert result["summary"]["failed_runs"] == []


def test_narrow_replication_config_freezes_search_space():
    config = runner.narrow_replication_config()

    assert config["stage_name"] == "direction_inside_frozen_mask_narrow_replication"
    assert config["output_prefix_name"] == "direction_inside_frozen_movement_regime_narrow_replication"
    assert config["feature_profiles"] == ["nearest_k60"]
    assert config["model_keys"] == ["extra_trees"]
    assert config["target_families"] == ["entry_log_ratio"]
    assert config["target_horizons"] == [3, 6, 9]
    assert config["replication_seeds"] == [41, 42, 43, 44, 45]
    assert config["primary_horizon"] == 3
    assert config["secondary_horizons"] == [6, 9]
    assert config["selection_policy"] == "pre_registered_no_new_winner_search"
    assert config["max_positive_verdict"] == "DIRECTION_REPLICATION_SUPPORTED_RESEARCH_ONLY"
    assert config["locked_test"] == "not_opened"


def test_preflight_target_horizons_marks_h9_missing_without_crash():
    splits = {
        "train": pd.DataFrame(
            {
                "entry_log_ratio_3": [0.1],
                "entry_up_3": [2.0],
                "entry_dn_3": [1.0],
                "entry_log_ratio_6": [0.2],
                "entry_up_6": [3.0],
                "entry_dn_6": [1.0],
            }
        ),
        "val_select": pd.DataFrame(
            {
                "entry_log_ratio_3": [0.1],
                "entry_up_3": [2.0],
                "entry_dn_3": [1.0],
                "entry_log_ratio_6": [0.2],
                "entry_up_6": [3.0],
                "entry_dn_6": [1.0],
            }
        ),
    }

    preflight = runner.preflight_target_horizons(splits, horizons=[3, 6, 9])

    assert preflight["status"] == "WARNING"
    assert preflight["horizons"]["3"]["status"] == "PASS"
    assert preflight["horizons"]["6"]["status"] == "PASS"
    assert preflight["horizons"]["9"]["status"] == "SKIPPED_MISSING_TARGET_COLUMNS"
    assert preflight["executable_horizons"] == [3, 6]
    assert preflight["skipped_horizons"] == [9]


def test_preflight_target_horizons_allows_h9_when_columns_exist():
    splits = {
        "train": pd.DataFrame(
            {
                "entry_log_ratio_9": [0.1],
                "entry_up_9": [2.0],
                "entry_dn_9": [1.0],
            }
        )
    }

    preflight = runner.preflight_target_horizons(splits, horizons=[9])

    assert preflight["status"] == "PASS"
    assert preflight["horizons"]["9"]["status"] == "PASS"
    assert preflight["executable_horizons"] == [9]


def test_replication_jobs_use_all_pre_registered_seeds():
    config = runner.narrow_replication_config()
    config.update(
        {
            "target_horizons": [3, 6],
            "replication_seeds": [41, 42],
        }
    )

    jobs = runner.build_rich_direction_jobs(config)

    assert [job["seed"] for job in jobs] == [41, 41, 42, 42]
    assert [job["horizon"] for job in jobs] == [3, 6, 3, 6]
    assert {job["profile"] for job in jobs} == {"nearest_k60"}
    assert {job["model_key"] for job in jobs} == {"extra_trees"}
    assert {job["target_family"] for job in jobs} == {"entry_log_ratio"}


def test_replication_jobs_use_only_executable_horizons_after_h9_preflight():
    config = runner.narrow_replication_config()
    config.update(
        {
            "target_horizons": [3, 6, 9],
            "executable_horizons": [3, 6],
            "replication_seeds": [41],
        }
    )

    jobs = runner.build_rich_direction_jobs(config)

    assert [job["horizon"] for job in jobs] == [3, 6]


def _replication_metric(run_id, seed, horizon, split, bal_acc, gate="PASS"):
    return {
        "run_id": run_id,
        "resume_key": f"nearest_k60/{seed}/extra_trees/H{horizon}/entry_log_ratio",
        "profile": "nearest_k60",
        "seed": seed,
        "model_key": "extra_trees",
        "horizon": horizon,
        "target_family": "entry_log_ratio",
        "split": split,
        "slice": "frozen_selected",
        "balanced_accuracy": bal_acc,
        "sample_size_gate": gate,
        "gate_reasons": "",
    }


def test_narrow_replication_verdict_supported_when_h3_repeats():
    rows = []
    for seed, score in zip([41, 42, 43, 44, 45], [0.526, 0.531, 0.529, 0.521, 0.533]):
        rows.append(_replication_metric(f"h3-{seed}", seed, 3, "val_select", score + 0.02))
        rows.append(_replication_metric(f"h3-{seed}", seed, 3, "val_eval", score))
    for seed, score in zip([41, 42, 43, 44, 45], [0.507, 0.509, 0.501, 0.506, 0.508]):
        rows.append(_replication_metric(f"h6-{seed}", seed, 6, "val_select", score + 0.01))
        rows.append(_replication_metric(f"h6-{seed}", seed, 6, "val_eval", score))

    replication = runner.aggregate_narrow_replication(pd.DataFrame(rows), {"target_preflight": {"skipped_horizons": [9]}})

    assert replication["primary_horizon"] == 3
    assert replication["horizons"]["3"]["val_eval_median_balanced_accuracy"] == pytest.approx(0.529)
    assert replication["horizons"]["3"]["val_eval_seeds_ge_0_52"] == 5
    assert runner.narrow_replication_verdict(replication) == "DIRECTION_REPLICATION_SUPPORTED_RESEARCH_ONLY"


def test_narrow_replication_verdict_rejects_weak_h3():
    rows = []
    for seed, score in zip([41, 42, 43, 44, 45], [0.501, 0.511, 0.514, 0.509, 0.506]):
        rows.append(_replication_metric(f"h3-{seed}", seed, 3, "val_select", score + 0.02))
        rows.append(_replication_metric(f"h3-{seed}", seed, 3, "val_eval", score))

    replication = runner.aggregate_narrow_replication(pd.DataFrame(rows), {"target_preflight": {"skipped_horizons": [9]}})

    assert runner.narrow_replication_verdict(replication) == "REJECT_DIRECTION_REPLICATION"


def test_narrow_replication_verdict_inconclusive_when_val_select_eval_sign_disagree():
    rows = []
    for seed, eval_score in zip([41, 42, 43, 44, 45], [0.526, 0.531, 0.529, 0.521, 0.533]):
        select_score = 0.499 if seed in {41, 42, 43} else 0.551
        rows.append(_replication_metric(f"h3-{seed}", seed, 3, "val_select", select_score))
        rows.append(_replication_metric(f"h3-{seed}", seed, 3, "val_eval", eval_score))
    for seed, score in zip([41, 42, 43, 44, 45], [0.507, 0.509, 0.501, 0.506, 0.508]):
        rows.append(_replication_metric(f"h6-{seed}", seed, 6, "val_select", score + 0.01))
        rows.append(_replication_metric(f"h6-{seed}", seed, 6, "val_eval", score))

    replication = runner.aggregate_narrow_replication(pd.DataFrame(rows), {"target_preflight": {"skipped_horizons": [9]}})

    assert replication["horizons"]["3"]["same_positive_sign_seed_count"] == 2
    assert runner.narrow_replication_verdict(replication) == "DIRECTION_REPLICATION_INCONCLUSIVE"


def test_narrow_replication_verdict_inconclusive_when_h6_contradicts_and_h9_skipped():
    rows = []
    for seed, score in zip([41, 42, 43, 44, 45], [0.526, 0.531, 0.529, 0.521, 0.533]):
        rows.append(_replication_metric(f"h3-{seed}", seed, 3, "val_select", score + 0.02))
        rows.append(_replication_metric(f"h3-{seed}", seed, 3, "val_eval", score))
    for seed, score in zip([41, 42, 43, 44, 45], [0.491, 0.498, 0.501, 0.494, 0.499]):
        rows.append(_replication_metric(f"h6-{seed}", seed, 6, "val_select", score + 0.01))
        rows.append(_replication_metric(f"h6-{seed}", seed, 6, "val_eval", score))

    replication = runner.aggregate_narrow_replication(pd.DataFrame(rows), {"target_preflight": {"skipped_horizons": [9]}})

    assert runner.narrow_replication_verdict(replication) == "DIRECTION_REPLICATION_INCONCLUSIVE"


def test_aggregate_narrow_replication_marks_target_contract_fail_by_horizon():
    summary = {
        "target_horizons": [3, 9],
        "target_preflight": {
            "horizons": {
                "3": {"status": "PASS"},
                "9": {"status": "PASS"},
            },
            "executable_horizons": [3, 9],
            "skipped_horizons": [],
        },
        "failed_runs": [{"stage": "targets", "horizon": 9, "error": "ValueError"}],
        "contract_status": "TARGET_CONTRACT_FAIL",
    }

    replication = runner.aggregate_narrow_replication(pd.DataFrame([]), summary)

    assert replication["horizons"]["9"]["status"] == "TARGET_CONTRACT_FAIL"
    assert replication["horizons"]["9"]["target_contract_failures"] == [
        {"stage": "targets", "horizon": 9, "error": "ValueError"}
    ]


def test_compute_narrow_time_diagnostics_reports_year_and_blocks():
    rows = pd.DataFrame(
        {
            "resume_key": ["nearest_k60/41/extra_trees/H3/entry_log_ratio"] * 8,
            "split": ["val_eval"] * 8,
            "row_id": list(range(8)),
            "time": [
                "2021-01-01",
                "2021-02-01",
                "2021-03-01",
                "2021-04-01",
                "2022-01-01",
                "2022-02-01",
                "2022-03-01",
                "2022-04-01",
            ],
            "prediction": [1, 1, -1, -1, 1, -1, 1, -1],
            "target_direction": [1, -1, -1, -1, 1, -1, -1, -1],
            "frozen_selected": [True] * 8,
        }
    )

    diagnostics = runner.compute_narrow_time_diagnostics(rows, block_count=4)

    assert diagnostics["status"] == "PASS"
    assert diagnostics["scope"] == "diagnostic_only_not_verdict_gate"
    assert set(diagnostics["by_year"].keys()) == {"2021", "2022"}
    assert len(diagnostics["by_block"]) == 4
    assert diagnostics["by_year"]["2021"]["n"] == 4


def test_arg_parser_accepts_narrow_replication_mode_and_seeds():
    parser = runner.build_arg_parser()
    args = parser.parse_args(["--replication-mode", "narrow", "--replication-seeds", "41", "42", "43"])

    assert args.replication_mode == "narrow"
    assert args.replication_seeds == [41, 42, 43]


def test_narrow_smoke_horizons_override_limits_to_one_horizon():
    parser = runner.build_arg_parser()
    args = parser.parse_args(["--replication-mode", "narrow", "--horizons", "3", "--replication-seeds", "41"])
    config = runner.config_from_args(args)

    assert config["target_horizons"] == [3]
    assert config["replication_seeds"] == [41]


def test_narrow_replication_mode_defaults_to_narrow_horizons():
    parser = runner.build_arg_parser()
    args = parser.parse_args(["--replication-mode", "narrow"])
    config = runner.config_from_args(args)

    assert config["target_horizons"] == [3, 6, 9]


def test_narrow_replication_mode_rejects_matrix_overrides():
    parser = runner.build_arg_parser()
    args = parser.parse_args(["--replication-mode", "narrow", "--profiles", "all100"])

    with pytest.raises(ValueError, match="pre-registered matrix"):
        runner.config_from_args(args)


def test_validate_horizon_args_keeps_h9_replication_only():
    runner.validate_horizon_args("narrow", [3, 9])
    with pytest.raises(ValueError, match="unsupported horizons"):
        runner.validate_horizon_args("none", [3, 9])


def test_narrow_abort_artifact_keeps_replication_schema(tmp_path):
    output_prefix = tmp_path / "missing_freeze_narrow"

    summary = runner.run_rich_direction_cli(
        output_prefix=output_prefix,
        freeze_scores_path=tmp_path / "missing_scores.csv",
        config_overrides=runner.narrow_replication_config(),
        resume=False,
    )

    assert summary["contract_status"] == "ABORT_CONTRACT_FAIL"
    assert summary["replication_mode"] == "narrow"
    assert "replication_summary" in summary
    assert summary["replication_verdict"] == "DIRECTION_REPLICATION_INCONCLUSIVE"
    assert summary["replication_search_budget_planned"] == 15
    assert summary["replication_search_budget_executed"] == 0
