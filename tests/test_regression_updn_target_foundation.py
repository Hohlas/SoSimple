import inspect
import json

import numpy as np
import pandas as pd
import pytest

import ML.baseline.benchmark_regression_updn_target_foundation as updn


def test_updn_config_is_fixed_and_bounded():
    cfg = updn.REGRESSION_UPDN_CONFIG

    assert cfg.horizons == (3, 6, 12, 24, 48)
    assert cfg.legacy_reference_horizon == 12
    assert cfg.seeds == (42, 77, 123)
    assert cfg.primary_profile == "clock_shift_back"
    assert cfg.artifact_status == "DIAGNOSTIC_ONLY"
    assert cfg.train_max_year == 2020
    assert cfg.val_years == (2021, 2022)
    assert cfg.holdout_years == (2023, 2024, 2025)
    assert cfg.low_n_years == (2026,)


def test_updn_target_columns_are_top_level_labels_only():
    assert updn.UPDN_TARGET_COLUMNS == (
        "up_3", "dn_3", "up_6", "dn_6", "up_12", "dn_12",
        "up_24", "dn_24", "up_48", "dn_48",
    )


def test_updn_feature_denylist_blocks_top_level_targets_and_future_labels():
    denylist = set(updn.updn_feature_denylist())

    for col in updn.UPDN_TARGET_COLUMNS:
        assert col in denylist
    assert "predict" in denylist
    assert "signal" in denylist
    assert "stage6_definitive_tp_vs_sl_flag" in denylist
    assert "sell_stop_broken_H6_off05_flag" in denylist
    assert "buy_bars_to_breach_H6_off05" in denylist


def test_updn_baselines_include_dummy_linear_tree_forest_and_xgboost():
    assert updn.updn_model_keys() == (
        "constant_median",
        "ridge",
        "decision_tree_depth3",
        "random_forest_depth4",
        "xgboost_depth3",
    )


def test_updn_profiles_exclude_token_updn_from_main_run():
    assert "updn_token_diagnostic" not in updn.updn_profile_keys()
    assert "updn_token_appendix" not in updn.updn_profile_keys()


def test_feature_source_contract_is_allowlist_based():
    contract = updn.updn_feature_source_contract("clock_shift_back")

    assert contract["profile"] == "clock_shift_back"
    assert contract["input_selection"] == "allowlist"
    assert "top_level_updn_targets" not in contract["allowed_sources"]
    assert contract["forbidden_sources"]["top_level_updn_targets"] == list(updn.UPDN_TARGET_COLUMNS)


def test_feature_read_audit_separates_declared_sources_from_raw_touches():
    audit = updn._feature_read_audit("clock_shift_back")

    assert "declared_feature_sources" in audit
    assert "raw_columns_touched" in audit
    assert "raw_fractal_subfields_touched" in audit
    assert "ATR" in audit["raw_columns_touched"]
    assert "price" in audit["raw_fractal_subfields_touched"]
    assert audit["validation"]["technical_reads_exceed_declared_sources"] is True


def test_validate_updn_target_contract_rejects_missing_target():
    splits = {
        "train_core": pd.DataFrame({"time": ["2021.01.01 00:00"], "up_3": [1.0]}),
        "val_stop": pd.DataFrame({"time": ["2021.01.01 00:00"], "up_3": [1.0]}),
    }

    result = updn.validate_updn_target_contract(splits)

    assert result["status"] == "FAIL"
    assert "dn_3" in result["missing_columns"]["train_core"]


def _tiny_labeled_frame():
    base = {
        "time": ["2021.01.04 10:00", "2021.01.04 11:00", "2021.01.04 12:00", "2021.01.04 13:00"],
        "ATR": [1.0, 2.0, 1.5, 1.25],
    }
    for idx, col in enumerate(updn.UPDN_TARGET_COLUMNS):
        base[col] = [0.1 + idx * 0.01, 0.2 + idx * 0.01, 0.3 + idx * 0.01, 0.4 + idx * 0.01]
    for i in range(100):
        base[f"fractal{i}"] = [
            "1:10:1:0.1:0.2:0:0:0:0.3:1:0.4:0.01:0.02:0.03:0.04:0.05:0.06:0.001:0.002:0.003:0.004:1.0:0",
            "2:11:-1:0.2:0.3:0:0:0:0.4:2:0.5:0.02:0.03:0.04:0.05:0.06:0.07:0.002:0.003:0.004:0.005:1.0:1",
            "3:12:1:0.3:0.4:0:0:0:0.5:3:0.6:0.03:0.04:0.05:0.06:0.07:0.08:0.003:0.004:0.005:0.006:1.0:2",
            "4:13:-1:0.4:0.5:0:0:0:0.6:4:0.7:0.04:0.05:0.06:0.07:0.08:0.09:0.004:0.005:0.006:0.007:1.0:3",
        ]
    return pd.DataFrame(base)


def test_build_features_does_not_depend_on_top_level_updn_targets():
    df = _tiny_labeled_frame()
    baseline = updn.build_updn_features(df, "clock_shift_back")

    mutated = df.copy()
    for col in updn.UPDN_TARGET_COLUMNS:
        mutated[col] = 9999.0

    after = updn.build_updn_features(mutated, "clock_shift_back")
    np.testing.assert_allclose(after, baseline)


def test_extract_updn_targets_preserves_declared_order():
    df = _tiny_labeled_frame()

    y = updn.extract_updn_targets(df)

    assert y.shape == (4, 10)
    assert list(updn.UPDN_TARGET_COLUMNS) == [
        "up_3", "dn_3", "up_6", "dn_6", "up_12", "dn_12",
        "up_24", "dn_24", "up_48", "dn_48",
    ]


@pytest.mark.parametrize("profile", updn.updn_profile_keys())
def test_feature_names_match_feature_width(profile):
    df = _tiny_labeled_frame()

    X, preflight = updn.build_updn_features(df, profile, return_preflight=True)
    names = updn.updn_feature_names(profile)

    assert X.shape[1] == len(names)
    assert len(names) == len(set(names))
    assert "non_finite_feature_count" in preflight
    assert "feature_read_audit" in preflight
    assert preflight["feature_read_audit"]["validation"]["allowlist_match"] is True
    assert "declared_feature_sources" in preflight["feature_read_audit"]


def test_constant_median_predict_uses_train_only_values():
    train_y = np.array([[1.0, 4.0], [3.0, 8.0], [5.0, 12.0]])

    pred = updn.updn_constant_median_predict(train_y, eval_n=2)

    np.testing.assert_allclose(pred, np.array([[3.0, 8.0], [3.0, 8.0]]))


def test_regression_metrics_include_primary_targets_and_improvement():
    y_true = np.array([[1.0, 2.0], [2.0, 1.0], [3.0, 0.5]])
    y_pred = np.array([[1.1, 1.9], [2.2, 1.1], [2.8, 0.6]])
    atr = np.array([2.0, 2.0, 2.0])

    metrics = updn.updn_regression_metrics(y_true, y_pred, ("up_12", "dn_12"), atr=atr)

    assert "up_12" in metrics["targets"]
    assert "dn_12" in metrics["targets"]
    assert metrics["targets"]["up_12"]["mae"] >= 0.0
    assert metrics["targets"]["up_12"]["spearman"] is not None
    assert metrics["targets"]["up_12"]["mae_over_median_atr"] is not None


def test_edge_diagnostics_reports_up_minus_dn_for_each_horizon():
    y_true = np.array([[2.0, 1.0], [1.0, 3.0], [4.0, 1.0]])
    y_pred = np.array([[1.8, 1.2], [1.1, 2.8], [3.5, 1.2]])

    result = updn.evaluate_edge_diagnostics(
        y_true,
        y_pred,
        target_names=("up_12", "dn_12"),
    )

    assert result["edge_12"]["spearman"] is not None
    assert result["edge_12"]["sign_accuracy"] >= 0.0


def test_log_ratio_diagnostics_reports_log_ratio_per_horizon():
    y_true = np.array([[2.0, 1.0], [1.0, 3.0], [4.0, 1.0]])
    y_pred = np.array([[1.8, 1.2], [1.1, 2.8], [3.5, 1.2]])

    result = updn.evaluate_log_ratio_diagnostics(
        y_true,
        y_pred,
        target_names=("up_12", "dn_12"),
    )

    assert result["log_ratio_12"]["spearman"] is not None


def test_gate_passes_only_with_contract_model_and_stability():
    summary = {
        "target_contract": {"status": "PASS"},
        "selected_horizon": 12,
        "primary": {
            "profile": "clock_shift_back",
            "seed_pass_count": 2,
            "target_metrics": {
                "up_12": {"normalized_mae_improvement_vs_constant": 0.06, "spearman": 0.16, "bootstrap_p05_improvement": 0.01},
                "dn_12": {"normalized_mae_improvement_vs_constant": 0.07, "spearman": 0.18, "bootstrap_p05_improvement": 0.02},
            },
            "edge_12": {"spearman": 0.11, "bootstrap_p05_spearman": 0.01, "val_year_sign_reversal": False},
            "calendar_warning": False,
        },
    }

    gate = updn.evaluate_updn_gate(summary)

    assert gate["research_gate_status"] == "TARGET_FOUNDATION_PASSED"
    assert gate["artifact_status"] == "DIAGNOSTIC_ONLY"


def test_runner_report_shape_with_tiny_data(monkeypatch, tmp_path):
    splits = {
        "train_core": _tiny_labeled_frame(),
        "val_stop": _tiny_labeled_frame(),
        "diagnostic_holdout": _tiny_labeled_frame(),
        "low_n_disclosure": _tiny_labeled_frame(),
    }
    monkeypatch.setattr(updn, "load_updn_labeled_splits", lambda: splits)
    monkeypatch.setattr(updn, "updn_input_file_manifest", lambda: {"dummy": {"sha256": "a" * 64}})

    output_path = tmp_path / "updn.json"
    report = updn.run_regression_updn_target_foundation(
        output_path=output_path,
        resume=False,
        profile_keys=("clock_only",),
    )

    assert output_path.exists()
    assert report["experiment"] == "regression_updn_target_foundation"
    assert report["artifact_status"] == "DIAGNOSTIC_ONLY"
    assert "target_contract" in report
    assert "runs" in report
    assert "summary" in report
    assert "gate" in report
    assert report["done_runs"] == report["total_runs"]


def test_cli_flag_is_registered():
    parser = updn.build_arg_parser()
    args = parser.parse_args(["--regression-updn-target-foundation", "--no-resume"])

    assert args.regression_updn_target_foundation is True
    assert args.resume is False


def test_cli_has_resume_flags():
    src = inspect.getsource(updn.build_arg_parser)
    assert "--resume" in src
    assert "--no-resume" in src


def test_runner_persists_feature_source_contract(monkeypatch, tmp_path):
    splits = {
        "train_core": _tiny_labeled_frame(),
        "val_stop": _tiny_labeled_frame(),
        "diagnostic_holdout": _tiny_labeled_frame(),
        "low_n_disclosure": _tiny_labeled_frame(),
    }
    monkeypatch.setattr(updn, "load_updn_labeled_splits", lambda: splits)
    monkeypatch.setattr(updn, "updn_input_file_manifest", lambda: {"dummy": {"sha256": "a" * 64}})

    output_path = tmp_path / "updn_contract.json"
    updn.run_regression_updn_target_foundation(
        output_path=output_path,
        resume=False,
        profile_keys=("clock_shift_back",),
    )

    data = json.loads(output_path.read_text())
    assert "feature_contract" in data
    assert "clock_shift_back" in data["feature_contract"]
    assert data["feature_contract"]["clock_shift_back"]["feature_source_contract"]["input_selection"] == "allowlist"
    assert data["runs"][0]["feature_read_audit"]["validation"]["allowlist_match"] is True
    assert "raw_columns_touched" in data["runs"][0]["feature_read_audit"]


def test_xgboost_calendar_dependence_is_recorded_per_target_and_horizon(monkeypatch, tmp_path):
    splits = {
        "train_core": _tiny_labeled_frame(),
        "val_stop": _tiny_labeled_frame(),
        "diagnostic_holdout": _tiny_labeled_frame(),
        "low_n_disclosure": _tiny_labeled_frame(),
    }
    monkeypatch.setattr(updn, "load_updn_labeled_splits", lambda: splits)
    monkeypatch.setattr(updn, "updn_input_file_manifest", lambda: {"dummy": {"sha256": "a" * 64}})

    output_path = tmp_path / "updn_calendar.json"
    data = updn.run_regression_updn_target_foundation(
        output_path=output_path,
        resume=False,
        profile_keys=("clock_only",),
    )
    xgb_run = next(r for r in data["runs"] if r["model_key"] == "xgboost_depth3")
    assert "calendar_dependence" in xgb_run
    assert "per_target" in xgb_run["calendar_dependence"]
    assert "per_horizon_median" in xgb_run["calendar_dependence"]
