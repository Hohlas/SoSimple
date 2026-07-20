from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from ML.baseline.benchmark_entry_based_movement_filter import (
    main,
    enumerate_filter_candidates,
    evaluate_top_fraction_filter,
    decide_verdict,
    load_amplitude_artifact,
    select_filter,
    validate_source_artifact,
    validate_source_path,
    validate_low_n_disclosure_years,
)


def test_load_amplitude_artifact_reads_json(tmp_path: Path):
    artifact = {
        "selection_policy": {"locked_test": "not_opened"},
        "run_config_hash": "abc",
        "feature_audit_rows": [],
    }
    path = tmp_path / "artifact.json"
    path.write_text(json.dumps(artifact), encoding="utf-8")

    loaded = load_amplitude_artifact(path)

    assert loaded == artifact


def test_validate_source_artifact_requires_not_opened_locked_test():
    artifact = {
        "selection_policy": {"locked_test": "opened"},
        "feature_audit_rows": [],
        "run_config_hash": "abc",
    }

    verdict = validate_source_artifact(artifact)

    assert verdict["status"] == "ABORT_CONTRACT_FAIL"
    assert "locked_test" in verdict["reasons"]


def test_validate_source_artifact_accepts_expected_source_contract():
    artifact = {
        "selection_policy": {"locked_test": "not_opened"},
        "run_config_hash": "abc",
        "feature_audit_rows": [
            {"profile": "time_plus_atr", "split": "train", "family": "metadata", "decision": "PASS"},
            {"profile": "time_plus_atr", "split": "val_select", "family": "metadata", "decision": "PASS"},
            {"profile": "time_plus_atr", "split": "val_eval", "family": "metadata", "decision": "PASS"},
            {"profile": "time_plus_atr", "split": "low_n_disclosure", "family": "metadata", "decision": "PASS"},
            {"profile": "simple_combined", "split": "train", "family": "metadata", "decision": "PASS"},
            {"profile": "simple_combined", "split": "val_select", "family": "metadata", "decision": "PASS"},
            {"profile": "simple_combined", "split": "val_eval", "family": "metadata", "decision": "PASS"},
            {"profile": "simple_combined", "split": "low_n_disclosure", "family": "metadata", "decision": "PASS"},
        ],
    }

    verdict = validate_source_artifact(artifact)

    assert verdict == {"status": "PASS", "reasons": []}


def test_validate_source_path_rejects_noncanonical_source(tmp_path):
    source = tmp_path / "entry_based_amplitude_movement.json"
    source.write_text("{}", encoding="utf-8")

    try:
        validate_source_path(source)
    except ValueError as exc:
        assert "ML/reports/entry_based_amplitude_movement.json" in str(exc)
    else:
        raise AssertionError("non-canonical source path was not rejected")

    validate_source_path(source, allow_noncanonical_source=True)


def test_enumerate_filter_candidates_is_bounded_to_simple_profiles():
    artifact = {
        "seed_aggregate": [
            {
                "profile": "time_plus_atr",
                "model_key": "extra_trees_small",
                "horizon": 3,
                "target_family": "entry_movement",
                "selection_eligible": True,
                "post_entry_diagnostic_only": False,
                "val_select_spearman_median": 0.50,
            },
            {
                "profile": "nearest_k80_sequence_flat",
                "model_key": "hist_gradient_boosting",
                "horizon": 3,
                "target_family": "entry_movement",
                "selection_eligible": False,
                "post_entry_diagnostic_only": False,
                "val_select_spearman_median": 0.80,
            },
        ]
    }

    candidates = enumerate_filter_candidates(artifact)

    assert {row["profile"] for row in candidates} == {"time_plus_atr"}
    assert {row["selected_fraction"] for row in candidates} == {0.05, 0.10, 0.20, 0.30}


def test_enumerate_filter_candidates_skips_guardrailed_rows():
    artifact = {
        "seed_aggregate": [
            {
                "profile": "time_plus_atr",
                "model_key": "valid_model",
                "horizon": 3,
                "target_family": "entry_movement",
                "selection_eligible": True,
                "post_entry_diagnostic_only": False,
                "val_select_spearman_median": 0.10,
            },
            {
                "profile": "time_plus_atr",
                "model_key": "blocked_by_selection_eligible",
                "horizon": 3,
                "target_family": "entry_movement",
                "selection_eligible": False,
                "post_entry_diagnostic_only": False,
                "val_select_spearman_median": 0.90,
            },
            {
                "profile": "simple_combined",
                "model_key": "blocked_by_post_entry_diagnostic_only",
                "horizon": 6,
                "target_family": "entry_movement",
                "selection_eligible": True,
                "post_entry_diagnostic_only": True,
                "val_select_spearman_median": 0.95,
            },
        ]
    }

    candidates = enumerate_filter_candidates(artifact)

    assert {row["model_key"] for row in candidates} == {"valid_model"}
    assert all(row["selection_eligible"] is True for row in candidates)
    assert all(row["post_entry_diagnostic_only"] is False for row in candidates)


def test_enumerate_filter_candidates_rejects_missing_or_none_post_entry_diagnostic_only():
    artifact = {
        "seed_aggregate": [
            {
                "profile": "time_plus_atr",
                "model_key": "valid_model",
                "horizon": 3,
                "target_family": "entry_movement",
                "selection_eligible": True,
                "post_entry_diagnostic_only": False,
                "val_select_spearman_median": 0.20,
            },
            {
                "profile": "time_plus_atr",
                "model_key": "missing_flag",
                "horizon": 3,
                "target_family": "entry_movement",
                "selection_eligible": True,
                "val_select_spearman_median": 0.90,
            },
            {
                "profile": "simple_combined",
                "model_key": "none_flag",
                "horizon": 6,
                "target_family": "entry_movement",
                "selection_eligible": True,
                "post_entry_diagnostic_only": None,
                "val_select_spearman_median": 0.95,
            },
        ]
    }

    candidates = enumerate_filter_candidates(artifact)

    assert {row["model_key"] for row in candidates} == {"valid_model"}
    assert all(row["post_entry_diagnostic_only"] is False for row in candidates)


def test_enumerate_filter_candidates_rejects_missing_or_none_selection_eligible():
    artifact = {
        "seed_aggregate": [
            {
                "profile": "time_plus_atr",
                "model_key": "valid_model",
                "horizon": 3,
                "target_family": "entry_movement",
                "selection_eligible": True,
                "post_entry_diagnostic_only": False,
                "val_select_spearman_median": 0.20,
            },
            {
                "profile": "time_plus_atr",
                "model_key": "missing_selection_eligible",
                "horizon": 3,
                "target_family": "entry_movement",
                "post_entry_diagnostic_only": False,
                "val_select_spearman_median": 0.90,
            },
            {
                "profile": "simple_combined",
                "model_key": "none_selection_eligible",
                "horizon": 6,
                "target_family": "entry_movement",
                "selection_eligible": None,
                "post_entry_diagnostic_only": False,
                "val_select_spearman_median": 0.95,
            },
        ]
    }

    candidates = enumerate_filter_candidates(artifact)

    assert {row["model_key"] for row in candidates} == {"valid_model"}
    assert all(row["selection_eligible"] is True for row in candidates)


def test_validate_low_n_disclosure_years_requires_2026_only():
    good = pd.DataFrame({"time": ["2026-01-01 00:00:00", "2026-12-31 23:00:00"]})
    bad = pd.DataFrame({"time": ["2025-12-31 23:00:00", "2026-01-01 00:00:00"]})
    missing = pd.DataFrame({"time": [None, "2026-01-01 00:00:00"]})

    validate_low_n_disclosure_years(good)

    try:
        validate_low_n_disclosure_years(bad)
    except ValueError as exc:
        assert "years=[2025, 2026]" in str(exc)
    else:
        raise AssertionError("low_n_disclosure year contract was not enforced")

    try:
        validate_low_n_disclosure_years(missing)
    except ValueError as exc:
        assert "years=[]" in str(exc)
    else:
        raise AssertionError("missing low_n_disclosure time values were not rejected")


def test_evaluate_top_fraction_filter_reports_lift_and_counts():
    frame = pd.DataFrame(
        {
            "score": [0.9, 0.8, 0.2, 0.1],
            "entry_movement_3": [10.0, 8.0, 2.0, 1.0],
        }
    )

    metrics = evaluate_top_fraction_filter(
        frame,
        score_col="score",
        target_col="entry_movement_3",
        selected_fraction=0.50,
    )

    assert metrics["selected_n"] == 2
    assert metrics["skipped_n"] == 2
    assert metrics["selected_mean_movement"] == 9.0
    assert metrics["skipped_mean_movement"] == 1.5
    assert metrics["selected_p50"] == 9.0
    assert metrics["selected_p80"] == 9.6
    assert metrics["selected_p90"] == 9.8
    assert metrics["skipped_p50"] == 1.5
    assert metrics["skipped_p80"] == 1.8
    assert metrics["skipped_p90"] == 1.9
    assert metrics["movement_lift"] == 6.0


def test_evaluate_top_fraction_filter_returns_none_lift_when_skipped_mean_is_zero():
    frame = pd.DataFrame(
        {
            "score": [0.9, 0.8, 0.2, 0.1],
            "entry_movement_3": [10.0, 8.0, 0.0, 0.0],
        }
    )

    metrics = evaluate_top_fraction_filter(
        frame,
        score_col="score",
        target_col="entry_movement_3",
        selected_fraction=0.50,
    )

    assert metrics["skipped_mean_movement"] == 0.0
    assert metrics["movement_lift"] is None


def test_select_filter_uses_declared_tie_breaker():
    candidates = [
        {
            "profile": "simple_combined",
            "horizon": 12,
            "selected_fraction": 0.10,
            "selected_n": 250,
            "movement_lift": 1.30,
            "selected_p80": 9.0,
            "skipped_p80": 7.0,
        },
        {
            "profile": "time_plus_atr",
            "horizon": 12,
            "selected_fraction": 0.10,
            "selected_n": 250,
            "movement_lift": 1.30,
            "selected_p80": 9.0,
            "skipped_p80": 7.0,
        },
    ]

    selected = select_filter(candidates)

    assert selected["profile"] == "time_plus_atr"


def test_select_filter_skips_strong_candidate_that_fails_val_select_gate():
    candidates = [
        {
            "profile": "time_plus_atr",
            "horizon": 12,
            "selected_fraction": 0.10,
            "selected_n": 180,
            "movement_lift": 1.80,
            "selected_p80": 9.5,
            "skipped_p80": 7.0,
        },
        {
            "profile": "simple_combined",
            "horizon": 12,
            "selected_fraction": 0.10,
            "selected_n": 220,
            "movement_lift": 1.26,
            "selected_p80": 8.5,
            "skipped_p80": 7.0,
        },
    ]

    selected = select_filter(candidates)

    assert selected["profile"] == "simple_combined"


def test_select_filter_returns_none_when_no_candidate_passes_gate():
    candidates = [
        {
            "profile": "time_plus_atr",
            "horizon": 12,
            "selected_fraction": 0.10,
            "selected_n": 199,
            "movement_lift": 1.80,
            "selected_p80": 9.5,
            "skipped_p80": 7.0,
        },
        {
            "profile": "simple_combined",
            "horizon": 12,
            "selected_fraction": 0.10,
            "selected_n": 220,
            "movement_lift": 1.26,
            "selected_p80": 6.5,
            "skipped_p80": 7.0,
        },
    ]

    assert select_filter(candidates) is None
    assert select_filter([]) is None


def test_decide_verdict_rejects_when_selected_filter_fails_val_eval():
    selected = {"profile": "time_plus_atr"}
    val_eval_metrics = {
        "selected_n": 120,
        "movement_lift": 1.10,
        "selected_p80": 9.0,
        "skipped_p80": 7.0,
        "yearly_lift_pass_rate": 0.80,
    }

    verdict = decide_verdict(selected, val_eval_metrics, {"status": "PASS", "reasons": []})

    assert verdict == "MOVEMENT_FILTER_REJECTED"


def test_cli_smoke_writes_json_and_candidate_csv(tmp_path: Path, monkeypatch):
    artifact = {
        "selection_policy": {"locked_test": "not_opened"},
        "run_config_hash": "abc",
        "run_config": {"requested_threads": 1, "effective_threads": 1},
        "feature_audit_rows": [
            {"profile": "time_plus_atr", "split": "train", "family": "metadata", "decision": "PASS"},
            {"profile": "time_plus_atr", "split": "val_select", "family": "metadata", "decision": "PASS"},
            {"profile": "time_plus_atr", "split": "val_eval", "family": "metadata", "decision": "PASS"},
            {"profile": "time_plus_atr", "split": "low_n_disclosure", "family": "metadata", "decision": "PASS"},
            {"profile": "simple_combined", "split": "train", "family": "metadata", "decision": "PASS"},
            {"profile": "simple_combined", "split": "val_select", "family": "metadata", "decision": "PASS"},
            {"profile": "simple_combined", "split": "val_eval", "family": "metadata", "decision": "PASS"},
            {"profile": "simple_combined", "split": "low_n_disclosure", "family": "metadata", "decision": "PASS"},
        ],
        "seed_aggregate": [
            {
                "profile": "time_plus_atr",
                "model_key": "ridge_regression",
                "horizon": 3,
                "target_family": "entry_movement",
                "selection_eligible": True,
                "post_entry_diagnostic_only": False,
                "val_select_spearman_median": 0.50,
            },
            {
                "profile": "simple_combined",
                "model_key": "ridge_regression",
                "horizon": 6,
                "target_family": "entry_movement",
                "selection_eligible": True,
                "post_entry_diagnostic_only": False,
                "val_select_spearman_median": 0.40,
            },
        ],
        "metrics": [],
        "failed_runs": [],
    }
    source_path = tmp_path / "artifact.json"
    source_path.write_text(json.dumps(artifact), encoding="utf-8")

    def fake_build_runtime_context(source_artifact: dict):
        assert source_artifact["run_config_hash"] == "abc"
        return {}

    def fake_materialize_candidate_score_frames(candidate: dict, runtime_context: dict):
        assert runtime_context == {}
        target_col = f"entry_movement_{candidate['horizon']}"
        base = pd.DataFrame(
            {
                "score": [0.9, 0.8, 0.7, 0.2, 0.1],
                target_col: [9.0, 8.0, 7.0, 2.0, 1.0],
                "time": [
                    "2021-01-01 00:00:00",
                    "2022-01-01 00:00:00",
                    "2023-01-01 00:00:00",
                    "2024-01-01 00:00:00",
                    "2026-01-01 00:00:00",
                ],
            }
        )
        return {
            "frames": {
                "val_select": base.iloc[:4].copy(),
                "val_eval": base.iloc[:4].copy(),
                "low_n_disclosure": base.iloc[4:].copy(),
            },
            "seed_count": 1,
            "score_aggregation": "median_across_rerun_seeds",
            "feature_contract_verdict": "PASS",
            "available_at_decision_time": True,
            "selection_eligible": True,
        }

    monkeypatch.setattr(
        "ML.baseline.benchmark_entry_based_movement_filter._build_runtime_context",
        fake_build_runtime_context,
    )
    monkeypatch.setattr(
        "ML.baseline.benchmark_entry_based_movement_filter.materialize_candidate_score_frames",
        fake_materialize_candidate_score_frames,
    )

    output_prefix = tmp_path / "entry_based_movement_filter"
    exit_code = main(
        [
            "--source",
            str(source_path),
            "--output-prefix",
            str(output_prefix),
            "--allow-noncanonical-source",
        ]
    )

    assert exit_code == 0
    assert (tmp_path / "entry_based_movement_filter.json").exists()
    candidates = pd.read_csv(tmp_path / "entry_based_movement_filter_candidates.csv")
    assert not candidates.empty
