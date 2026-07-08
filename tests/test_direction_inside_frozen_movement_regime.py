import json
from pathlib import Path

import pandas as pd

from ML.baseline.benchmark_direction_inside_frozen_movement_regime import (
    build_arg_parser,
    build_report,
    build_rows_export,
    build_direction_targets,
    build_feature_matrices,
    build_masked_direction_dataset,
    compute_direction_robustness,
    decide_direction_verdict,
    evaluate_direction_predictions,
    fit_direction_models,
    frozen_direction_config,
    load_frozen_mask,
    main,
    run_cli,
    select_direction_rule,
    validate_frozen_movement_contract,
    validate_mask_join_keys,
    write_artifacts,
)
from ML.baseline.benchmark_entry_based_movement_filter_freeze import (
    frozen_rule,
    sha256_file,
    stable_rule_hash,
)


def _freeze_report() -> dict:
    return {
        "verdict": "FROZEN_MOVEMENT_FILTER_FOR_NEXT_RESEARCH_PLAN",
        "frozen_config": {"frozen_rule": frozen_rule()},
        "frozen_rule_hash": stable_rule_hash(frozen_rule()),
        "contract_status": {"locked_test": "not_opened", "status": "PASS"},
    }


def _scores() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "split": ["train", "train", "val_select", "val_eval", "low_n_disclosure"],
            "time": [
                "2020-01-01 00:00:00",
                "2020-01-02 00:00:00",
                "2021-01-01 00:00:00",
                "2024-01-01 00:00:00",
                "2026-01-01 00:00:00",
            ],
            "year": [2020, 2020, 2021, 2024, 2026],
            "score": [10.0, 1.0, 9.0, 8.0, 7.0],
            "entry_movement_3": [5.0, 1.0, 4.0, 3.0, 2.0],
            "selected": [True, False, True, True, True],
        }
    )


def test_frozen_direction_config_keeps_movement_rule_read_only():
    config = frozen_direction_config()

    assert config["movement_rule"] == frozen_rule()
    assert config["movement_rule_hash"] == stable_rule_hash(frozen_rule())
    assert config["direction_horizon"] == 3
    assert config["locked_test"] == "not_opened"
    assert config["forbidden_input_columns"] == [
        "score",
        "entry_movement_3",
        "entry_up_3",
        "entry_dn_3",
        "target_direction_3",
        "target_is_tie_3",
        "target_up_3",
        "target_dn_3",
        "label_direction_3",
    ]


def test_validate_frozen_movement_contract_rejects_changed_rule():
    report = _freeze_report()
    report["frozen_config"]["frozen_rule"] = {**frozen_rule(), "selected_fraction": 0.10}

    result = validate_frozen_movement_contract(report, _scores())

    assert result["status"] == "ABORT_CONTRACT_FAIL"
    assert "movement_rule_mismatch" in result["reasons"]


def test_validate_frozen_movement_contract_rejects_locked_test_opened():
    report = _freeze_report()
    report["contract_status"]["locked_test"] = "opened"

    result = validate_frozen_movement_contract(report, _scores())

    assert result["status"] == "ABORT_CONTRACT_FAIL"
    assert "locked_test" in result["reasons"]


def test_validate_frozen_movement_contract_requires_expected_score_columns():
    scores = _scores().drop(columns=["selected"])

    result = validate_frozen_movement_contract(_freeze_report(), scores)

    assert result["status"] == "ABORT_CONTRACT_FAIL"
    assert "scores_schema" in result["reasons"]


def test_load_frozen_mask_reports_unknown_selected_values_as_contract_fail(tmp_path: Path):
    report_path = tmp_path / "freeze.json"
    scores_path = tmp_path / "scores.csv"
    report_path.write_text(json.dumps(_freeze_report()), encoding="utf-8")
    scores = _scores()
    scores["selected"] = scores["selected"].astype(object)
    scores.loc[0, "selected"] = "maybe"
    scores.to_csv(scores_path, index=False)

    loaded = load_frozen_mask(report_path, scores_path)

    assert loaded["contract"]["status"] == "ABORT_CONTRACT_FAIL"
    assert "scores.selected_format" in loaded["contract"]["reasons"]


def test_load_frozen_mask_reads_report_and_scores(tmp_path: Path):
    report_path = tmp_path / "freeze.json"
    scores_path = tmp_path / "scores.csv"
    report_path.write_text(json.dumps(_freeze_report()), encoding="utf-8")
    _scores().to_csv(scores_path, index=False)

    loaded = load_frozen_mask(report_path, scores_path)

    assert loaded["contract"]["status"] == "PASS"
    assert loaded["scores_hash"] == sha256_file(scores_path)
    assert set(loaded["scores"]["split"]) == {"train", "val_select", "val_eval", "low_n_disclosure"}
    assert int(loaded["scores"]["selected"].sum()) == 4


def test_build_direction_targets_drops_ties_and_labels_up_down():
    frame = pd.DataFrame(
        {
            "entry_up_3": [5.0, 1.0, 2.0, float("nan")],
            "entry_dn_3": [1.0, 4.0, 2.0, 3.0],
        }
    )

    targets = build_direction_targets(frame)

    assert targets["target_direction_3"].tolist() == [1, -1, pd.NA, pd.NA]
    assert targets["target_is_tie_3"].tolist() == [False, False, True, True]


def test_build_masked_direction_dataset_keeps_only_selected_rows_by_split():
    splits = {
        "train": pd.DataFrame(
            {
                "time": ["2020-01-01 00:00:00", "2020-01-02 00:00:00"],
                "entry_up_3": [3.0, 1.0],
                "entry_dn_3": [1.0, 3.0],
                "ATR": [0.5, 0.6],
            }
        ),
        "val_select": pd.DataFrame(
            {
                "time": ["2021-01-01 00:00:00"],
                "entry_up_3": [4.0],
                "entry_dn_3": [1.0],
                "ATR": [0.7],
            }
        ),
    }
    scores = pd.DataFrame(
        {
            "split": ["train", "train", "val_select"],
            "time": ["2020-01-01 00:00:00", "2020-01-02 00:00:00", "2021-01-01 00:00:00"],
            "selected": [True, False, True],
            "score": [10.0, 1.0, 9.0],
            "entry_movement_3": [3.0, 3.0, 4.0],
            "year": [2020, 2020, 2021],
        }
    )

    dataset = build_masked_direction_dataset(splits, scores)

    assert len(dataset["train"]) == 1
    assert len(dataset["val_select"]) == 1
    assert dataset["train"]["target_direction_3"].tolist() == [1]
    assert "score" not in dataset["train"].columns
    assert "entry_up_3" not in dataset["train"].columns
    assert "entry_dn_3" not in dataset["train"].columns
    assert "entry_movement_3" not in dataset["train"].columns
    assert "target_up_3" in dataset["train"].columns
    assert "target_dn_3" in dataset["train"].columns


def test_validate_mask_join_keys_rejects_duplicate_split_time():
    splits = {
        "train": pd.DataFrame(
            {
                "time": ["2020-01-01 00:00:00", "2020-01-01 00:00:00"],
                "entry_up_3": [3.0, 1.0],
                "entry_dn_3": [1.0, 3.0],
            }
        )
    }
    scores = pd.DataFrame(
        {
            "split": ["train", "train"],
            "time": ["2020-01-01 00:00:00", "2020-01-01 00:00:00"],
            "selected": [True, False],
            "score": [10.0, 1.0],
            "entry_movement_3": [3.0, 3.0],
            "year": [2020, 2020],
        }
    )

    result = validate_mask_join_keys(splits, scores)

    assert result["status"] == "ABORT_CONTRACT_FAIL"
    assert "scores.duplicate_split_time" in result["reasons"]
    assert "splits.train.duplicate_time" in result["reasons"]


def test_validate_mask_join_keys_rejects_selected_count_mismatch():
    splits = {
        "train": pd.DataFrame(
            {
                "time": ["2020-01-01 00:00:00"],
                "entry_up_3": [3.0],
                "entry_dn_3": [1.0],
            }
        )
    }
    scores = pd.DataFrame(
        {
            "split": ["train", "train"],
            "time": ["2020-01-01 00:00:00", "2020-01-02 00:00:00"],
            "selected": [True, True],
            "score": [10.0, 9.0],
            "entry_movement_3": [3.0, 3.0],
            "year": [2020, 2020],
        }
    )

    result = validate_mask_join_keys(splits, scores)

    assert result["status"] == "ABORT_CONTRACT_FAIL"
    assert "splits.train.selected_count_mismatch" in result["reasons"]


def test_evaluate_direction_predictions_reports_balanced_metrics():
    metrics = evaluate_direction_predictions(
        pd.Series([1, 1, -1, -1]),
        pd.Series([1, -1, -1, -1]),
    )

    assert metrics["total_n"] == 4
    assert metrics["accuracy"] == 0.75
    assert metrics["up_recall"] == 0.5
    assert metrics["dn_recall"] == 1.0


def test_build_feature_matrices_excludes_direction_targets_and_movement_score():
    masked = {
        "train": pd.DataFrame(
            {
                "time": ["2020-01-01 00:00:00", "2020-01-02 00:00:00"],
                "ATR": [0.5, 0.6],
                "score": [10.0, 1.0],
                "entry_up_3": [3.0, 1.0],
                "entry_dn_3": [1.0, 3.0],
                "entry_movement_3": [3.0, 3.0],
                "target_direction_3": [1, -1],
            }
        ),
        "val_select": pd.DataFrame(
            {
                "time": ["2021-01-01 00:00:00", "2021-01-02 00:00:00"],
                "ATR": [0.7, 0.8],
                "score": [9.0, 8.0],
                "entry_up_3": [4.0, 1.0],
                "entry_dn_3": [1.0, 4.0],
                "entry_movement_3": [4.0, 4.0],
                "target_direction_3": [1, -1],
            }
        ),
    }

    matrices = build_feature_matrices(masked, profile="time_plus_atr")

    for frame in matrices["features"].values():
        assert "score" not in frame.columns
        assert "entry_up_3" not in frame.columns
        assert "entry_dn_3" not in frame.columns
        assert "entry_movement_3" not in frame.columns
        assert "target_direction_3" not in frame.columns
        assert "target_up_3" not in frame.columns
        assert "target_dn_3" not in frame.columns


def test_fit_direction_models_fits_once_and_predicts_each_split():
    class CountingModel:
        def __init__(self):
            self.fit_calls = 0

        def fit(self, train_x, train_y):
            self.fit_calls += 1
            return self

        def predict(self, eval_x):
            return [1] * len(eval_x)

    model = CountingModel()
    fitted = fit_direction_models(
        {"counting": model},
        pd.DataFrame({"ATR": [0.5, 0.6]}),
        pd.Series([1, -1]),
    )

    assert fitted["counting"] is model
    assert model.fit_calls == 1


def test_decide_direction_verdict_rejects_weak_val_eval():
    contract = {"status": "PASS"}
    selection = {
        "status": "SELECTED",
        "winner": "extra_trees_small",
        "val_select": {"total_n": 120, "balanced_accuracy": 0.58, "mcc": 0.12},
        "val_eval": {"total_n": 120, "balanced_accuracy": 0.51, "mcc": 0.01},
        "beats_majority_on_val_eval": False,
    }

    assert decide_direction_verdict(contract, selection) == "REJECT_DIRECTION_INSIDE_MOVEMENT_REGIME"


def test_select_direction_rule_uses_val_select_not_val_eval():
    results = {
        "baselines": {
            "model_a": {
                "val_select": {"total_n": 100, "balanced_accuracy": 0.60, "mcc": 0.20},
                "val_eval": {"total_n": 100, "balanced_accuracy": 0.52, "mcc": 0.01},
            },
            "model_b": {
                "val_select": {"total_n": 100, "balanced_accuracy": 0.55, "mcc": 0.10},
                "val_eval": {"total_n": 100, "balanced_accuracy": 0.90, "mcc": 0.80},
            },
            "majority_class": {
                "val_select": {"total_n": 100, "balanced_accuracy": 0.50, "mcc": 0.0},
                "val_eval": {"total_n": 100, "balanced_accuracy": 0.50, "mcc": 0.0},
            },
        }
    }

    selection = select_direction_rule(results)

    assert selection["winner"] == "model_a"


def test_select_direction_rule_ignores_low_n_disclosure():
    base_results = {
        "baselines": {
            "model_a": {
                "val_select": {"total_n": 100, "balanced_accuracy": 0.60, "mcc": 0.20},
                "val_eval": {"total_n": 100, "balanced_accuracy": 0.56, "mcc": 0.08},
                "low_n_disclosure": {"total_n": 100, "balanced_accuracy": 0.10, "mcc": -0.80},
            },
            "model_b": {
                "val_select": {"total_n": 100, "balanced_accuracy": 0.55, "mcc": 0.10},
                "val_eval": {"total_n": 100, "balanced_accuracy": 0.56, "mcc": 0.08},
                "low_n_disclosure": {"total_n": 100, "balanced_accuracy": 0.99, "mcc": 0.95},
            },
            "majority_class": {"val_eval": {"total_n": 100, "balanced_accuracy": 0.50, "mcc": 0.0}},
        }
    }

    selection = select_direction_rule(base_results)

    assert selection["winner"] == "model_a"


def test_decide_direction_verdict_needs_robustness_for_frozen_status():
    contract = {"status": "PASS"}
    selection = {
        "status": "SELECTED",
        "val_select": {"total_n": 120, "balanced_accuracy": 0.58, "mcc": 0.12},
        "val_eval": {"total_n": 120, "balanced_accuracy": 0.57, "mcc": 0.10},
        "beats_majority_on_val_eval": True,
    }

    assert decide_direction_verdict(contract, selection, robustness=None) == "RESEARCH_ONLY_DIRECTION_SIGNAL"
    assert decide_direction_verdict(contract, selection, robustness={"status": "PASS"}) == "RESEARCH_ONLY_DIRECTION_SIGNAL"
    assert (
        decide_direction_verdict(
            contract,
            selection,
            robustness={
                "status": "PASS",
                "required_pass_checks": {
                    "yearly_stability": {"status": "PASS", "evidence": {"active_years": 2}},
                    "block_stability": {"status": "PASS", "evidence": {"method": "block_bootstrap"}},
                    "confidence_interval_lower_bound": {"status": "PASS", "evidence": {"lower": 0.53}},
                    "class_balance_disclosure": {"status": "PASS", "evidence": {"up_support": 60, "dn_support": 60}},
                    "exact_search_budget": {"status": "PASS", "evidence": {"direction_baselines_trained": 3}},
                },
            },
        )
        == "FROZEN_DIRECTION_RULE_FOR_NEXT_PLAN"
    )


def test_compute_direction_robustness_never_passes_without_block_stability():
    masked = {
        "val_eval": pd.DataFrame(
            {
                "time": ["2024-01-01 00:00:00"] * 60 + ["2025-01-01 00:00:00"] * 60,
                "target_direction_3": [1, -1] * 60,
            }
        )
    }
    baseline_results = {
        "baselines": {
            "extra_trees_small": {
                "val_eval": {
                    "total_n": 120,
                    "balanced_accuracy": 0.58,
                    "mcc": 0.10,
                    "up_recall": 0.62,
                    "dn_recall": 0.58,
                    "up_support": 60,
                    "dn_support": 60,
                }
            }
        }
    }

    robustness = compute_direction_robustness(masked, baseline_results, {"winner": "extra_trees_small"})

    assert robustness["status"] == "RESEARCH_ONLY"
    assert "val_eval.block_stability_not_run" in robustness["reasons"]
    assert robustness["required_pass_checks"]["block_stability"]["status"] == "NOT_RUN"


def test_decide_direction_verdict_requires_complete_robustness_checks_for_frozen_status():
    contract = {"status": "PASS"}
    selection = {
        "status": "SELECTED",
        "val_select": {"total_n": 120, "balanced_accuracy": 0.58, "mcc": 0.12},
        "val_eval": {"total_n": 120, "balanced_accuracy": 0.57, "mcc": 0.10},
        "beats_majority_on_val_eval": True,
    }

    incomplete_robustness = {
        "status": "PASS",
        "checks": {"yearly_stability": "PASS"},
    }

    assert (
        decide_direction_verdict(contract, selection, robustness=incomplete_robustness)
        == "RESEARCH_ONLY_DIRECTION_SIGNAL"
    )


def test_compute_direction_robustness_reports_research_only_on_single_year():
    masked = {
        "val_eval": pd.DataFrame(
            {
                "time": ["2024-01-01 00:00:00"] * 120,
                "target_direction_3": [1, -1] * 60,
            }
        )
    }
    baseline_results = {
        "baselines": {
            "extra_trees_small": {
                "val_eval": {
                    "total_n": 120,
                    "balanced_accuracy": 0.57,
                    "mcc": 0.10,
                    "up_recall": 0.58,
                    "dn_recall": 0.56,
                    "up_support": 60,
                    "dn_support": 60,
                }
            }
        }
    }
    selection = {"winner": "extra_trees_small"}

    robustness = compute_direction_robustness(masked, baseline_results, selection)

    assert robustness["status"] == "RESEARCH_ONLY"
    assert "val_eval.active_years" in robustness["reasons"]


def test_build_report_keeps_contract_fail_as_first_class_outcome():
    report = build_report(
        {"status": "ABORT_CONTRACT_FAIL", "reasons": ["scores.duplicate_split_time"]},
        {"baselines": {}},
        {"status": "NO_CANDIDATE", "winner": None},
        {"status": "NOT_RUN"},
        "ABORT_CONTRACT_FAIL",
    )

    assert report["contract"]["status"] == "ABORT_CONTRACT_FAIL"
    assert report["verdict"] == "ABORT_CONTRACT_FAIL"
    assert report["selection"]["status"] == "NO_CANDIDATE"
    assert report["search_budget"]["direction_baselines_trained"] == 0


def test_write_artifacts_persists_report_and_rows(tmp_path: Path):
    report = {
        "verdict": "ABORT_CONTRACT_FAIL",
        "contract": {"status": "ABORT_CONTRACT_FAIL", "reasons": ["scores.duplicate_split_time"]},
    }
    rows = pd.DataFrame({"split": ["val_eval"], "time": ["2024-01-01 00:00:00"], "selected": [True]})
    output_prefix = tmp_path / "direction_inside_frozen_movement_regime"

    write_artifacts(report, rows, output_prefix)

    json_path = Path(f"{output_prefix}.json")
    rows_path = Path(f"{output_prefix}_rows.csv")
    assert json_path.exists()
    assert rows_path.exists()
    loaded_report = json.loads(json_path.read_text(encoding="utf-8"))
    loaded_rows = pd.read_csv(rows_path)
    assert loaded_report["verdict"] == "ABORT_CONTRACT_FAIL"
    assert loaded_rows.to_dict(orient="records") == rows.to_dict(orient="records")


def test_cli_smoke_writes_direction_artifacts(tmp_path: Path, monkeypatch):
    import ML.baseline.benchmark_direction_inside_frozen_movement_regime as module

    freeze_report_path = tmp_path / "freeze.json"
    scores_path = tmp_path / "scores.csv"
    output_prefix = tmp_path / "direction"
    freeze_report_path.write_text(json.dumps(_freeze_report()), encoding="utf-8")
    scores = pd.DataFrame(
        {
            "split": ["train", "train", "val_select", "val_select", "val_eval", "val_eval"],
            "time": [
                "2020-01-01 00:00:00",
                "2020-01-02 00:00:00",
                "2021-01-01 00:00:00",
                "2021-01-02 00:00:00",
                "2024-01-01 00:00:00",
                "2024-01-02 00:00:00",
            ],
            "year": [2020, 2020, 2021, 2021, 2024, 2024],
            "score": [10, 9, 8, 7, 6, 5],
            "entry_movement_3": [3, 3, 3, 3, 3, 3],
            "selected": [True, True, True, True, True, True],
        }
    )
    scores.to_csv(scores_path, index=False)
    splits = {
        "train": pd.DataFrame(
            {
                "time": ["2020-01-01 00:00:00", "2020-01-02 00:00:00"],
                "entry_up_3": [3.0, 1.0],
                "entry_dn_3": [1.0, 3.0],
                "ATR": [0.5, 0.6],
            }
        ),
        "val_select": pd.DataFrame(
            {
                "time": ["2021-01-01 00:00:00", "2021-01-02 00:00:00"],
                "entry_up_3": [3.0, 1.0],
                "entry_dn_3": [1.0, 3.0],
                "ATR": [0.5, 0.6],
            }
        ),
        "val_eval": pd.DataFrame(
            {
                "time": ["2024-01-01 00:00:00", "2024-01-02 00:00:00"],
                "entry_up_3": [3.0, 1.0],
                "entry_dn_3": [1.0, 3.0],
                "ATR": [0.5, 0.6],
            }
        ),
    }
    monkeypatch.setattr(module.amplitude, "load_entry_based_splits", lambda: splits)
    monkeypatch.setattr(
        module,
        "run_direction_baselines",
        lambda masked: {
            "profile": "simple_combined",
            "target": "target_direction_3",
            "baselines": {
                "majority_class": {"val_eval": {"total_n": 2, "balanced_accuracy": 0.5, "mcc": 0.0}},
                "extra_trees_small": {
                    "val_select": {"total_n": 120, "balanced_accuracy": 0.60, "mcc": 0.20},
                    "val_eval": {"total_n": 120, "balanced_accuracy": 0.57, "mcc": 0.10},
                },
            },
        },
    )

    parser = build_arg_parser()
    args = parser.parse_args(
        [
            "--freeze-report",
            str(freeze_report_path),
            "--freeze-scores",
            str(scores_path),
            "--output-prefix",
            str(output_prefix),
        ]
    )
    report = run_cli(args)
    exit_code = main(
        [
            "--freeze-report",
            str(freeze_report_path),
            "--freeze-scores",
            str(scores_path),
            "--output-prefix",
            str(output_prefix),
        ]
    )

    assert exit_code == 0
    assert report["verdict"] == "RESEARCH_ONLY_DIRECTION_SIGNAL"
    json_path = Path(f"{output_prefix}.json")
    rows_path = Path(f"{output_prefix}_rows.csv")
    assert json_path.exists()
    assert rows_path.exists()
    rows = pd.read_csv(rows_path)
    expected_rows = build_rows_export(build_masked_direction_dataset(splits, scores))
    assert rows.to_dict(orient="records") == expected_rows.to_dict(orient="records")
