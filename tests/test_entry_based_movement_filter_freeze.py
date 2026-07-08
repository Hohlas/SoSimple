import hashlib
import json
from pathlib import Path

import pandas as pd

from ML.baseline.benchmark_entry_based_movement_filter_freeze import (
    build_score_export,
    main,
    evaluate_frozen_rule,
    decide_freeze_verdict,
    frozen_rule,
    load_source_artifacts,
    materialize_frozen_score_frames,
    score_cutoff_diagnostics,
    sha256_file,
    stable_rule_hash,
    validate_source_hashes,
    validate_frozen_rule,
)
import ML.baseline.benchmark_entry_based_movement_filter_freeze as freeze_module


def test_frozen_rule_is_exactly_the_preselected_filter():
    assert frozen_rule() == {
        "profile": "simple_combined",
        "model_key": "extra_trees_small",
        "horizon": 3,
        "target_family": "entry_movement",
        "threshold_type": "top_fraction",
        "selected_fraction": 0.05,
        "score_aggregation": "median_across_rerun_seeds",
        "seeds": [42, 43, 44],
    }


def test_validate_frozen_rule_rejects_changed_threshold():
    artifact = {
        "selected_filter": {
            "profile": "simple_combined",
            "model_key": "extra_trees_small",
            "horizon": 3,
            "target_family": "entry_movement",
            "threshold_type": "top_fraction",
            "selected_fraction": 0.10,
            "score_aggregation": "median_across_rerun_seeds",
            "seeds": [42, 43, 44],
        },
        "locked_test": "not_opened",
    }

    verdict = validate_frozen_rule(artifact)

    assert verdict["status"] == "ABORT_CONTRACT_FAIL"
    assert "frozen_rule_mismatch" in verdict["reasons"]


def test_stable_rule_hash_is_order_independent():
    rule = frozen_rule()
    reversed_rule = dict(reversed(list(rule.items())))

    assert stable_rule_hash(rule) == stable_rule_hash(reversed_rule)


def test_validate_frozen_rule_rejects_changed_seed_contract():
    artifact = {
        "selected_filter": {
            "profile": "simple_combined",
            "model_key": "extra_trees_small",
            "horizon": 3,
            "target_family": "entry_movement",
            "threshold_type": "top_fraction",
            "selected_fraction": 0.05,
            "score_aggregation": "median_across_rerun_seeds",
            "seeds": [42, 43],
        },
        "locked_test": "not_opened",
    }

    verdict = validate_frozen_rule(artifact)

    assert verdict["status"] == "ABORT_CONTRACT_FAIL"
    assert "frozen_rule_mismatch" in verdict["reasons"]


def test_validate_frozen_rule_accepts_seed_count_bridge_and_returns_hash():
    artifact = {
        "selected_filter": {
            "profile": "simple_combined",
            "model_key": "extra_trees_small",
            "horizon": 3,
            "target_family": "entry_movement",
            "threshold_type": "top_fraction",
            "selected_fraction": 0.05,
            "score_aggregation": "median_across_rerun_seeds",
            "seed_count": 3,
        },
        "locked_test": "not_opened",
    }

    verdict = validate_frozen_rule(artifact)

    assert verdict["status"] == "PASS"
    assert verdict["reasons"] == []
    assert verdict["rule_hash"] == stable_rule_hash(frozen_rule())


def test_validate_frozen_rule_rejects_string_horizon_variant():
    artifact = {
        "selected_filter": {
            "profile": "simple_combined",
            "model_key": "extra_trees_small",
            "horizon": "3",
            "target_family": "entry_movement",
            "threshold_type": "top_fraction",
            "selected_fraction": 0.05,
            "score_aggregation": "median_across_rerun_seeds",
            "seeds": [42, 43, 44],
        },
        "locked_test": "not_opened",
    }

    verdict = validate_frozen_rule(artifact)

    assert verdict["status"] == "ABORT_CONTRACT_FAIL"
    assert "frozen_rule_mismatch" in verdict["reasons"]


def test_sha256_file_uses_raw_bytes(tmp_path: Path):
    payload = b"\x00utf-8-\xff\n"
    path = tmp_path / "amplitude.json"
    path.write_bytes(payload)

    assert sha256_file(path) == hashlib.sha256(payload).hexdigest()


def test_load_source_artifacts_reads_both_json_files(tmp_path: Path):
    movement = tmp_path / "entry_based_movement_filter.json"
    amplitude = tmp_path / "entry_based_amplitude_movement.json"
    movement.write_text(json.dumps({"selected_filter": {}}), encoding="utf-8")
    amplitude.write_text(json.dumps({"schema_version": 1}), encoding="utf-8")

    loaded = load_source_artifacts(movement, amplitude)

    assert loaded["movement_filter_artifact"]["selected_filter"] == {}
    assert loaded["amplitude_artifact"]["schema_version"] == 1
    assert loaded["movement_filter_path"] == str(movement)
    assert loaded["amplitude_path"] == str(amplitude)


def test_validate_source_hashes_rejects_amplitude_hash_mismatch(tmp_path: Path):
    amplitude = tmp_path / "entry_based_amplitude_movement.json"
    amplitude.write_text('{"changed": true}', encoding="utf-8")
    movement_artifact = {"source_artifact_hash": "not-the-real-hash"}

    verdict = validate_source_hashes(movement_artifact, amplitude)

    assert verdict["status"] == "ABORT_CONTRACT_FAIL"
    assert "source_amplitude_hash_mismatch" in verdict["reasons"]


def test_materialize_frozen_score_frames_adds_train_when_base_helper_omits_it(monkeypatch):
    frame = pd.DataFrame(
        {
            "score": [3.0, 2.0, 1.0],
            "entry_movement_3": [9.0, 4.0, 1.0],
            "time": ["2024-01-01 00:00:00"] * 3,
        }
    )
    train_frame = pd.DataFrame(
        {
            "score": [4.0, 1.0],
            "entry_movement_3": [8.0, 2.0],
            "time": ["2020-01-01 00:00:00"] * 2,
        }
    )

    monkeypatch.setattr(freeze_module, "_build_runtime_context", lambda artifact: {"sentinel": True})
    monkeypatch.setattr(
        freeze_module,
        "materialize_candidate_score_frames",
        lambda candidate, runtime_context: {
            "frames": {
                "val_select": frame.copy(),
                "val_eval": frame.copy(),
                "low_n_disclosure": pd.DataFrame(
                    {
                        "score": [5.0],
                        "entry_movement_3": [10.0],
                        "time": ["2026-01-01 00:00:00"],
                    }
                ),
            },
            "seed_count": 3,
            "score_aggregation": "median_across_rerun_seeds",
        },
    )
    monkeypatch.setattr(freeze_module, "_materialize_train_score_frame", lambda candidate, runtime_context: train_frame.copy())
    artifact = {
        "selected_filter": {
            "profile": "simple_combined",
            "model_key": "extra_trees_small",
            "horizon": 3,
            "target_family": "entry_movement",
            "threshold_type": "top_fraction",
            "selected_fraction": 0.05,
            "score_aggregation": "median_across_rerun_seeds",
            "seeds": [42, 43, 44],
        },
        "locked_test": "not_opened",
    }

    result = materialize_frozen_score_frames(artifact)

    assert "train" in result["frames"]
    assert result["frames"]["train"].equals(train_frame)


def test_evaluate_frozen_rule_uses_fixed_top_five_percent():
    frame = pd.DataFrame(
        {
            "score": list(range(100, 0, -1)),
            "entry_movement_3": [10.0] * 5 + [2.0] * 95,
            "time": ["2024-01-01 00:00:00"] * 100,
        }
    )
    frames = {
        "val_select": frame.copy(),
        "val_eval": frame.copy(),
        "low_n_disclosure": pd.DataFrame(
            {
                "score": list(range(20, 0, -1)),
                "entry_movement_3": [10.0] + [2.0] * 19,
                "time": ["2026-01-01 00:00:00"] * 20,
            }
        ),
    }

    result = evaluate_frozen_rule(frames)

    assert result["val_select"]["selected_n"] == 5
    assert result["val_eval"]["selected_n"] == 5
    assert result["val_eval"]["movement_lift"] > 4.0
    assert result["low_n_disclosure_2026"]["years"] == [2026]


def test_build_score_export_contains_all_splits_and_selected_flag():
    frame = pd.DataFrame(
        {
            "score": list(range(100, 0, -1)),
            "entry_movement_3": [10.0] * 5 + [2.0] * 95,
            "time": ["2024-01-01 00:00:00"] * 100,
        }
    )
    frames = {
        "train": frame.copy(),
        "val_select": frame.copy(),
        "val_eval": frame.copy(),
        "low_n_disclosure": frame.copy(),
    }

    exported = build_score_export(frames)

    assert set(exported["split"]) == {"train", "val_select", "val_eval", "low_n_disclosure"}
    assert {"split", "split_row_id", "time", "year", "score", "entry_movement_3", "selected"}.issubset(exported.columns)
    assert int(exported.loc[exported["split"] == "val_eval", "selected"].sum()) == 5
    assert exported.loc[exported["split"] == "val_eval", "split_row_id"].tolist() == list(range(100))


def test_build_score_export_selects_highest_numeric_score_when_scores_are_strings():
    frame = pd.DataFrame(
        {
            "score": ["2", "10", "9", "1"],
            "entry_movement_3": [2.0, 10.0, 9.0, 1.0],
            "time": ["2024-01-01 00:00:00"] * 4,
        }
    )
    frames = {
        "train": frame.copy(),
        "val_select": frame.copy(),
        "val_eval": frame.copy(),
        "low_n_disclosure": frame.copy(),
    }

    exported = build_score_export(frames)
    selected = exported.loc[exported["split"] == "val_eval"].query("selected")

    assert len(selected) == 1
    assert selected.iloc[0]["score"] == "10"


def test_score_cutoff_diagnostics_reports_split_and_year_cutoffs():
    frame = pd.DataFrame(
        {
            "score": list(range(100, 0, -1)),
            "entry_movement_3": [10.0] * 5 + [2.0] * 95,
            "time": ["2024-01-01 00:00:00"] * 50 + ["2025-01-01 00:00:00"] * 50,
        }
    )
    diagnostics = score_cutoff_diagnostics({"val_eval": frame})

    assert diagnostics["status"] in {"PASS", "WARNING"}
    assert diagnostics["by_split"][0]["split"] == "val_eval"
    assert {row["year"] for row in diagnostics["by_year"]} == {2024, 2025}


def passing_metrics():
    return {
        "val_select": {
            "selected_n": 333,
            "movement_lift": 2.15,
            "selected_p80": 17.5,
            "skipped_p80": 8.2,
        },
        "val_eval": {
            "selected_n": 333,
            "movement_lift": 2.48,
            "selected_p80": 35.6,
            "skipped_p80": 14.4,
            "spearman": 0.69,
            "yearly_lift_pass_rate": 1.0,
            "yearly": [
                {"year": 2023, "selected_n": 62, "movement_lift": 2.10},
                {"year": 2024, "selected_n": 137, "movement_lift": 1.88},
                {"year": 2025, "selected_n": 135, "movement_lift": 1.77},
            ],
        },
        "low_n_disclosure_2026": {"years": [2026]},
        "random_baseline": {
            "seed": 20260708,
            "n_repeats": 1000,
            "p95_movement_lift": 1.20,
            "yearly": [
                {"year": 2023, "p95_movement_lift": 1.12},
                {"year": 2024, "p95_movement_lift": 1.10},
                {"year": 2025, "p95_movement_lift": 1.09},
            ],
        },
        "score_cutoff_diagnostics": {"status": "PASS"},
    }


def test_decide_freeze_verdict_passes_only_frozen_rule_gates():
    verdict = decide_freeze_verdict({"status": "PASS", "reasons": []}, passing_metrics())

    assert verdict == "FROZEN_MOVEMENT_FILTER_FOR_NEXT_RESEARCH_PLAN"


def test_decide_freeze_verdict_rejects_weak_val_eval_without_replacement():
    metrics = passing_metrics()
    metrics["val_eval"]["movement_lift"] = 1.10

    verdict = decide_freeze_verdict({"status": "PASS", "reasons": []}, metrics)

    assert verdict == "REJECT_MOVEMENT_FILTER_FREEZE"


def test_decide_freeze_verdict_aborts_on_contract_failure():
    verdict = decide_freeze_verdict({"status": "ABORT_CONTRACT_FAIL", "reasons": ["hash"]}, passing_metrics())

    assert verdict == "ABORT_CONTRACT_FAIL"


def test_decide_freeze_verdict_ignores_2026_metric_values_for_freeze():
    metrics = passing_metrics()
    metrics["low_n_disclosure_2026"]["movement_lift"] = 0.01
    metrics["low_n_disclosure_2026"]["spearman"] = -0.50

    verdict = decide_freeze_verdict({"status": "PASS", "reasons": []}, metrics)

    assert verdict == "FROZEN_MOVEMENT_FILTER_FOR_NEXT_RESEARCH_PLAN"


def test_decide_freeze_verdict_rejects_wrong_disclosure_year_as_freeze_gate():
    metrics = passing_metrics()
    metrics["low_n_disclosure_2026"]["years"] = [2025]

    verdict = decide_freeze_verdict({"status": "PASS", "reasons": []}, metrics)

    assert verdict == "REJECT_MOVEMENT_FILTER_FREEZE"


def test_decide_freeze_verdict_returns_research_only_replicated_on_warning_path():
    metrics = passing_metrics()
    metrics["val_eval"]["spearman"] = 0.49

    verdict = decide_freeze_verdict({"status": "PASS", "reasons": []}, metrics)

    assert verdict == "RESEARCH_ONLY_REPLICATED"


def test_cli_smoke_writes_freeze_artifacts_with_fixture_sources(tmp_path: Path, monkeypatch):
    amplitude_path = tmp_path / "entry_based_amplitude_movement.json"
    amplitude_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "run_config": {"split_policy": {"locked_test": "not_opened"}},
                "target_contract": {"target_family": "entry_movement", "status": "PASS"},
                "metrics": [],
                "failed_runs": [],
                "seed_aggregate": [],
            }
        ),
        encoding="utf-8",
    )

    movement_path = tmp_path / "entry_based_movement_filter.json"
    movement_path.write_text(
        json.dumps(
            {
                "source_artifact_hash": sha256_file(amplitude_path),
                "locked_test": "not_opened",
                "selected_filter": {
                    "profile": "simple_combined",
                    "model_key": "extra_trees_small",
                    "horizon": 3,
                    "target_family": "entry_movement",
                    "threshold_type": "top_fraction",
                    "selected_fraction": 0.05,
                    "score_aggregation": "median_across_rerun_seeds",
                    "seeds": [42, 43, 44],
                },
                "source_search_budget": {"completed_metric_runs": 356},
                "filter_search_budget": {"evaluated_candidates": 32},
            }
        ),
        encoding="utf-8",
    )

    frame = pd.DataFrame(
        {
            "score": list(range(100, 0, -1)),
            "entry_movement_3": [10.0] * 5 + [2.0] * 75 + [float(value) for value in range(1, 21)],
            "time": ["2024-01-01 00:00:00"] * 40 + ["2025-01-01 00:00:00"] * 40 + ["2026-01-01 00:00:00"] * 20,
        }
    )

    def fake_materialize(_: dict) -> dict[str, object]:
        return {
            "frames": {
                "train": frame.iloc[:80].reset_index(drop=True).copy(),
                "val_select": frame.iloc[:80].reset_index(drop=True).copy(),
                "val_eval": frame.iloc[:80].reset_index(drop=True).copy(),
                "low_n_disclosure": frame.iloc[80:].reset_index(drop=True).copy(),
            },
            "selected_filter": {
                **frozen_rule(),
                "feature_contract_verdict": "PASS",
                "available_at_decision_time": True,
                "selection_eligible": True,
            },
            "seed_count": 3,
            "score_aggregation": "median_across_rerun_seeds",
            "rule_hash": stable_rule_hash(frozen_rule()),
        }

    monkeypatch.setattr(
        "ML.baseline.benchmark_entry_based_movement_filter_freeze.materialize_frozen_score_frames",
        fake_materialize,
    )

    exit_code = main(
        [
            "--movement-filter-source",
            str(movement_path),
            "--amplitude-source",
            str(amplitude_path),
            "--output-prefix",
            str(tmp_path / "entry_based_movement_filter_freeze"),
            "--allow-noncanonical-source",
        ]
    )

    assert exit_code == 0
    assert (tmp_path / "entry_based_movement_filter_freeze.json").exists()
    assert (tmp_path / "entry_based_movement_filter_freeze_yearly.csv").exists()
    assert (tmp_path / "entry_based_movement_filter_freeze_scores.csv").exists()
    assert (tmp_path / "entry_based_movement_filter_freeze_score_cutoffs.csv").exists()
