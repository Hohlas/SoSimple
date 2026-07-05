# =============================================================================
# Файл: test_entry_based_next_open_closeout.py
# Назначение: focused-тесты closeout runner-а `entry-based next open`
# Язык: Python 3.10+
# Обновлён: 2026-07-04
# =============================================================================

from __future__ import annotations

from argparse import Namespace
from pathlib import Path

import numpy as np
import pandas as pd

import ML.baseline.benchmark_entry_based_next_open_closeout as runner


def _minimal_entry_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "time": ["2021.01.01 00:00", "2021.01.01 01:00"],
            "entry_time": ["2021.01.01 01:00", "2021.01.01 02:00"],
            "entry_open": [100.0, 101.0],
            "entry_up_3": [0.5, 0.6],
            "entry_dn_3": [0.4, 0.5],
            "entry_log_ratio_3": [0.01, -0.01],
            "entry_up_6": [0.7, 0.8],
            "entry_dn_6": [0.6, 0.7],
            "entry_log_ratio_6": [0.02, -0.02],
            "entry_up_12": [0.9, 1.0],
            "entry_dn_12": [0.8, 0.9],
            "entry_log_ratio_12": [0.03, -0.03],
            "entry_up_24": [1.1, 1.2],
            "entry_dn_24": [1.0, 1.1],
            "entry_log_ratio_24": [0.04, -0.04],
        }
    )


def _frame_with_fractal(rows: int = 6) -> pd.DataFrame:
    frame = pd.concat([_minimal_entry_frame()] * max(1, rows // 2 + 1), ignore_index=True).head(rows)
    frame["ATR"] = 1.0
    frame["fractal0"] = "1:100:1:1:1:0:0:0:1:1:1:0.5:0.4:0.7:0.6:0.9:0.8:0.2:0.1:0.3:0.2:1:1"
    return frame


def test_closeout_scope_is_frozen_and_excludes_cross_pair_validation():
    assert runner.SHORTLIST_REPRESENTATIONS == (
        "all100",
        "corridor_5atr",
        "nearest_k20",
        "nearest_k60",
        "nearest_k80",
    )
    assert runner.CLOSEOUT_HORIZONS == ("3", "6", "12", "24")
    assert runner.CROSS_PAIR_VALIDATION == "excluded_by_plan"


def test_closeout_jobs_use_shortlist_models_and_single_seed():
    jobs = runner.enumerate_closeout_jobs()
    assert len(jobs) == 5 * 4 * 1
    assert {job["representation_key"] for job in jobs} == set(runner.SHORTLIST_REPRESENTATIONS)
    assert {job["model_key"] for job in jobs} == {
        "xgboost_depth3",
        "xgboost_depth5",
        "hist_gradient_boosting",
        "ridge",
    }
    assert {job["seed"] for job in jobs} == {42}


def test_closeout_split_policy_uses_large_validation_and_no_locked_test():
    assert runner.SPLIT_POLICY == {
        "train": {"source": ["train_core"], "calendar": "<=2020"},
        "validation": {"source": ["val_stop", "diagnostic_holdout"], "calendar": "2021-2025"},
        "locked_test": {"source": [], "calendar": "not_opened"},
        "low_n_disclosure": {"source": ["low_n_disclosure"], "calendar": "2026", "selection_use": "forbidden"},
    }


def test_entry_based_smoke_check_passes_without_legacy_target_columns():
    splits = {"train": _minimal_entry_frame(), "validation": _minimal_entry_frame()}
    result = runner.run_entry_based_smoke_check(splits)
    assert result["status"] == "PASS"
    assert result["legacy_target_columns_required"] is False
    assert result["horizons"] == ["3", "6", "12", "24"]


def test_entry_based_smoke_check_fails_when_h24_target_is_missing():
    frame = _minimal_entry_frame().drop(columns=["entry_log_ratio_24"])
    result = runner.run_entry_based_smoke_check({"train": frame})
    assert result["status"] == "FAIL"
    assert "entry_log_ratio_24" in result["missing_columns"]["train"]


def test_closeout_target_matrix_includes_h24():
    frame = _minimal_entry_frame()
    matrix = runner.closeout_target_matrix(frame)
    assert matrix.shape == (2, 12)


def test_closeout_features_include_serialized_h24_updn_but_not_top_level_targets():
    frame = _frame_with_fractal(rows=2)
    features, metadata = runner.build_closeout_representation_features(frame, "all100")
    serialized_h24 = [column for column in features.columns if "_up_24" in column or "_dn_24" in column]
    assert serialized_h24
    assert any(column.startswith("slot_00_") for column in serialized_h24)
    assert "entry_up_24" not in features.columns
    assert "entry_dn_24" not in features.columns
    assert "entry_log_ratio_24" not in features.columns
    assert metadata["target_horizons"] == ["3", "6", "12", "24"]
    assert metadata["feature_horizons"] == ["3", "6", "12", "24", "48"]


def test_closeout_features_add_live_safe_row_context_time():
    frame = _frame_with_fractal(rows=2)
    features, metadata = runner.build_closeout_representation_features(frame, "all100")
    assert {"row_hour_sin", "row_hour_cos", "row_dow_sin", "row_dow_cos"}.issubset(features.columns)
    assert "row_context_time" in metadata["feature_families"]


def test_normalization_contract_keeps_inputs_and_targets_separate():
    contract = runner.build_normalization_contract()
    assert contract["normalization_mode"] == "none_tree_raw"
    assert contract["scaler_fit_split"] == "train"
    assert contract["target_columns_forbidden_in_input_pools"] is True
    assert "updn_full" in contract["feature_groups"]
    assert contract["feature_groups"]["updn_full"]["source"] == "serialized_fractal_snapshot"


def test_normalization_contract_rejects_target_columns_in_feature_matrix():
    contract = runner.build_normalization_contract()
    features = pd.DataFrame({"slot000_price_coord_atr": [0.0, 1.0], "entry_up_24": [1.0, 2.0]})
    try:
        runner.assert_no_target_columns_in_normalization(features, contract)
    except ValueError as exc:
        assert "entry_up_24" in str(exc)
    else:
        raise AssertionError("target column was not rejected")


def test_feature_scale_audit_reports_distribution_and_dominance_flags():
    features_by_split = {
        "train": pd.DataFrame(
            {
                "slot000_price_coord_atr": [0.0, 1.0, 2.0, 3.0],
                "slot000_up_24": [0.1, 0.2, 0.3, 100.0],
                "row_hour_sin": [0.0, 0.5, -0.5, 0.0],
            }
        ),
        "validation": pd.DataFrame(
            {
                "slot000_price_coord_atr": [0.0, 1.0],
                "slot000_up_24": [0.2, 0.4],
                "row_hour_sin": [0.0, 1.0],
            }
        ),
    }
    audit = runner.compute_feature_scale_audit(features_by_split, {"profile_key": "all100"})
    assert audit["status"] in {"PASS", "WARNING"}
    assert "slot000_up_24" in audit["features"]
    assert "p99" in audit["features"]["slot000_up_24"]["train"]
    assert "dominance_checks" in audit


def test_simple_trade_metrics_use_prediction_sign_as_side():
    frame = _minimal_entry_frame()
    predictions = pd.DataFrame(
        {
            "pred_entry_log_ratio_3": [0.5, -0.5],
            "pred_entry_up_3": [1.0, 1.0],
            "pred_entry_dn_3": [1.0, 1.0],
        }
    )
    result = runner.compute_simple_trade_metrics(frame, predictions, horizon="3")
    assert result["trade_count"] == 2
    assert result["long_count"] == 1
    assert result["short_count"] == 1
    assert result["mean_signed_log_ratio"] == 0.01


def test_closeout_split_metrics_contains_direction_amplitude_and_trade_blocks():
    frame = _minimal_entry_frame()
    predictions = pd.DataFrame({f"pred_entry_up_{h}": [0.5, 0.6] for h in runner.CLOSEOUT_HORIZONS})
    for h in runner.CLOSEOUT_HORIZONS:
        predictions[f"pred_entry_dn_{h}"] = [0.4, 0.5]
        predictions[f"pred_entry_log_ratio_{h}"] = [0.1, -0.1]
    metrics = runner.compute_closeout_split_metrics(frame, predictions)
    assert "entry_log_ratio_24" in metrics
    assert "entry_up_24" in metrics
    assert "simple_trade_24" in metrics


def test_closeout_verdict_stop_when_direction_and_trade_fail():
    summary = {
        "best_directional": {"selection_score": 0.079, "eval_score": 0.009},
        "best_amplitude": {"selection_score": 0.16, "eval_score": 0.01},
        "best_trade": {"select_mean": -0.001, "eval_mean": -0.001},
        "validation_roles_combined": False,
    }
    assert runner.decide_closeout_verdict(summary) == "STOP"


def test_closeout_verdict_pivot_when_amplitude_survives_but_direction_does_not():
    summary = {
        "best_directional": {"selection_score": 0.07, "eval_score": 0.01},
        "best_amplitude": {"selection_score": 0.18, "eval_score": 0.12},
        "best_trade": {"select_mean": 0.0, "eval_mean": -0.001},
        "validation_roles_combined": False,
    }
    assert runner.decide_closeout_verdict(summary) == "PIVOT"


def test_closeout_verdict_continue_requires_direction_and_trade_eval():
    summary = {
        "best_directional": {"selection_score": 0.12, "eval_score": 0.04},
        "best_amplitude": {"selection_score": 0.18, "eval_score": 0.12},
        "best_trade": {"select_mean": 0.002, "eval_mean": 0.001},
        "validation_roles_combined": False,
    }
    assert runner.decide_closeout_verdict(summary) == "CONTINUE"


def test_closeout_verdict_cannot_continue_when_validation_roles_are_combined():
    summary = {
        "best_directional": {"selection_score": 0.12, "eval_score": 0.04},
        "best_amplitude": {"selection_score": 0.18, "eval_score": 0.12},
        "best_trade": {"select_mean": 0.002, "eval_mean": 0.001},
        "validation_roles_combined": True,
    }
    assert runner.decide_closeout_verdict(summary) == "PIVOT"


def test_run_closeout_benchmark_writes_artifacts_with_small_mock(tmp_path: Path, monkeypatch):
    frame = _frame_with_fractal(rows=6)
    old_splits = {
        "train_core": frame,
        "val_stop": frame,
        "diagnostic_holdout": frame,
        "low_n_disclosure": frame,
    }
    monkeypatch.setattr(runner.base, "load_entry_based_splits", lambda target_mode="rebuilt": old_splits)
    monkeypatch.setattr(
        runner,
        "enumerate_closeout_jobs",
        lambda: [{"representation_key": "all100", "model_key": "ridge", "seed": 42}],
    )
    monkeypatch.setattr(
        runner.base,
        "run_all_preflight_with_progress",
        lambda splits, report, report_path, total_runs, started_at: {"status": "PASS", "profiles": {}},
    )
    monkeypatch.setattr(
        runner.base,
        "run_distribution_audit_with_progress",
        lambda splits, report, report_path, total_runs, started_at: {"status": "PASS", "profiles": {}},
    )
    monkeypatch.setattr(runner, "REPORT_SCALE_AUDIT_PATH", tmp_path / "scale.csv")

    report = runner.run_closeout_benchmark(
        Namespace(entry_based_next_open_closeout=True, resume=False),
        report_path=tmp_path / "report.json",
        metrics_path=tmp_path / "metrics.csv",
        rows_path=tmp_path / "rows.csv",
    )
    assert report["progress"]["done_runs"] == 1
    assert report["entry_based_smoke_check"]["status"] == "PASS"
    assert report["summary"]["verdict"] in {"STOP", "PIVOT", "CONTINUE"}
    assert (tmp_path / "metrics.csv").exists()
    assert (tmp_path / "rows.csv").exists()
    assert (tmp_path / "scale.csv").exists()
