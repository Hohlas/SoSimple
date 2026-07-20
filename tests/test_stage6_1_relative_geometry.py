import numpy as np
import pandas as pd
import pytest

import ML.baseline.benchmark_stage6_1_relative_geometry as s61


def test_stage61_config_is_fixed_and_narrow():
    cfg = s61.STAGE6_1_CONFIG

    assert cfg.horizon_bars == 12
    assert cfg.stop_offset_atr == 0.5
    assert cfg.take_profit_atr == 2.0
    assert cfg.entry_lag_bars == 1
    assert cfg.primary_profile == "h12_corridor3_relative_geometry"
    assert cfg.profile_keys == (
        "h12_clock_shift_back",
        "h12_nearest_price40_relative_geometry",
        "h12_nearest_time40_relative_geometry",
        "h12_corridor3_relative_geometry",
        "h12_corridor10_relative_geometry",
        "h12_zones10_uniform_summary",
        "h12_clock_shift_back_plus_nearest_time40_geometry",
        "h12_clock_shift_back_plus_corridor3_geometry",
        "h12_clock_shift_back_plus_corridor10_geometry",
    )
    assert cfg.seeds == (42, 77, 123)


def test_stage61_combined_profiles_are_fixed_to_top_three_geometry_profiles():
    assert s61.stage61_combined_profile_keys() == (
        "h12_clock_shift_back_plus_nearest_time40_geometry",
        "h12_clock_shift_back_plus_corridor3_geometry",
        "h12_clock_shift_back_plus_corridor10_geometry",
    )
    assert s61.STAGE6_1_COMBINED_PROFILE_TO_GEOMETRY == {
        "h12_clock_shift_back_plus_nearest_time40_geometry": "h12_nearest_time40_relative_geometry",
        "h12_clock_shift_back_plus_corridor3_geometry": "h12_corridor3_relative_geometry",
        "h12_clock_shift_back_plus_corridor10_geometry": "h12_corridor10_relative_geometry",
    }


def test_stage61_profile_keys_include_baseline_geometry_and_combined_profiles():
    keys = s61.stage61_profile_keys()

    assert keys[-3:] == s61.stage61_combined_profile_keys()
    assert "h12_clock_shift_back_plus_nearest_time40_geometry" in keys
    assert "h12_clock_shift_back_plus_corridor3_geometry" in keys
    assert "h12_clock_shift_back_plus_corridor10_geometry" in keys
    assert "h12_clock_shift_back_plus_nearest_price40_geometry" not in keys
    assert "h12_clock_shift_back_plus_zones10_geometry" not in keys


def test_stage61_feature_denylist_includes_stage6_targets():
    denylist = set(s61.stage61_feature_denylist())

    assert "stage6_tp_vs_rest_flag" in denylist
    assert "stage6_definitive_tp_vs_sl_flag" in denylist
    assert "stage6_pnl_r" in denylist
    assert all(col.startswith("stage6_") for col in denylist)


def test_stage61_fractal_field_contract_matches_stage5_1b_parser():
    assert s61.STAGE5_1B_FIELD_TO_FRACTAL_INDEX["price"] == 1
    assert s61.STAGE5_1B_FIELD_TO_FRACTAL_INDEX["direction"] == 2
    assert s61.STAGE5_1B_FIELD_TO_FRACTAL_INDEX["front"] == 3
    assert s61.STAGE5_1B_FIELD_TO_FRACTAL_INDEX["back"] == 4
    assert s61.STAGE5_1B_FIELD_TO_FRACTAL_INDEX["impulse"] == 10
    assert "atr" not in s61.STAGE5_1B_FIELD_TO_FRACTAL_INDEX


def _row_with_fractals():
    return pd.Series({
        "ATR": 2.0,
        "fractal0": "0:100.0:-1:1.0:2.0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:1.0:0",
        "fractal1": "0:104.0:1:1.5:3.0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:1.2:4",
        "fractal2": "0:90.0:-1:2.0:4.0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0.8:8",
        "fractal3": "0:130.0:1:3.0:5.0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:2.0:12",
    })


def _fake_split():
    return {
        k: pd.DataFrame({
            "stage6_definitive_tp_vs_sl_flag": [1.0, 0.0],
            "dummy": [0.1, 0.2],
            "stage6_pnl_r": [0.5, -0.3],
        })
        for k in ("train_core", "val_stop", "diagnostic_holdout", "low_n_disclosure")
    }


def test_stage61_relative_fractal_frame_nearest_price_uses_atr_coordinates():
    frame = s61.stage61_relative_fractal_frame(_row_with_fractals(), mode="nearest_price", k=2)

    assert list(frame["fractal_idx"]) == [1, 2]
    assert np.allclose(frame["price_coord_atr"].to_numpy(), [2.0, -5.0])
    assert np.allclose(frame["abs_price_coord_atr"].to_numpy(), [2.0, 5.0])
    assert "price" not in frame.columns


def test_stage61_relative_fractal_frame_nearest_time_uses_shift_before_price():
    frame = s61.stage61_relative_fractal_frame(_row_with_fractals(), mode="nearest_time", k=2)

    assert list(frame["fractal_idx"]) == [1, 2]
    assert np.allclose(frame["log_shift"].to_numpy(), [np.log1p(4.0), np.log1p(8.0)])
    assert "price" not in frame.columns


def test_stage61_relative_fractal_frame_corridor_filters_by_atr_width():
    frame = s61.stage61_relative_fractal_frame(_row_with_fractals(), mode="corridor", corridor_atr=3.0)

    assert list(frame["fractal_idx"]) == [1]
    assert frame["price_coord_atr"].min() >= -3.0
    assert frame["price_coord_atr"].max() <= 3.0


def test_stage61_build_geometry_features_has_stable_shape_and_no_price():
    df = pd.DataFrame([_row_with_fractals(), _row_with_fractals()])

    X_price = s61.stage61_build_geometry_features(df, "h12_nearest_price40_relative_geometry")
    X_time = s61.stage61_build_geometry_features(df, "h12_nearest_time40_relative_geometry")
    X_corridor3 = s61.stage61_build_geometry_features(df, "h12_corridor3_relative_geometry")
    X_corridor = s61.stage61_build_geometry_features(df, "h12_corridor10_relative_geometry")
    X_zones = s61.stage61_build_geometry_features(df, "h12_zones10_uniform_summary")

    assert X_price.shape == (2, 40 * 8)
    assert X_time.shape == (2, 40 * 8)
    assert X_corridor3.shape == (2, 40 * 8)
    assert X_corridor.shape == (2, 40 * 8)
    assert X_zones.shape == (2, 20 * 5)
    assert np.isfinite(X_price).all()
    assert np.isfinite(X_time).all()
    assert np.isfinite(X_corridor3).all()
    assert np.isfinite(X_corridor).all()
    assert np.isfinite(X_zones).all()
    assert len(s61.stage61_feature_names("h12_corridor3_relative_geometry")) == 40 * 8
    assert len(s61.stage61_feature_names("h12_zones10_uniform_summary")) == 20 * 5
    assert "slot00_price_coord_atr" in s61.stage61_feature_names("h12_corridor3_relative_geometry")
    assert "zone_-01_+00_count" in s61.stage61_feature_names("h12_zones10_uniform_summary")


def test_stage61_geometry_coverage_reports_token_counts():
    df = pd.DataFrame([_row_with_fractals(), _row_with_fractals()])

    cov = s61.stage61_geometry_coverage(df, "h12_corridor3_relative_geometry")

    assert cov["n_rows"] == 2
    assert cov["token_count"]["median"] == 1.0
    assert cov["rows_with_0_tokens_rate"] == 0.0
    assert cov["min_price_coord_atr"] >= -3.0
    assert cov["max_price_coord_atr"] <= 3.0
    assert cov["warnings"] == []


def test_stage61_fractal_format_preflight_rejects_short_fractal0():
    split = {
        "train_core": pd.DataFrame({
            "fractal0": ["1:2:3", "0:100:-1:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:1:0"],
        })
    }

    audit = s61.stage61_fractal_format_preflight(split)

    assert audit["train_core"]["non_empty_fractal0_rows"] == 2
    assert audit["train_core"]["short_fractal0_rows"] == 1
    assert "SHORT_FRACTAL0_ROWS" in audit["train_core"]["warnings"]


def test_stage61_gate_fails_when_no_threshold_even_if_auc_passes():
    report = {
        "summary": {
            "h12_corridor3_relative_geometry": {
                "val_stop": {"auc_median": 0.68, "pr_auc_lift_median": 0.12},
                "threshold_selection": {"status": "NO_THRESHOLD", "selected": None},
                "permutation_baseline": {"empirical_p_value": 0.03},
            }
        }
    }

    gate = s61.stage61_gate_results(report)

    assert gate["overall_status"] == "TRADING_GATE_FAILED"
    assert gate["artifact_status"] == "DIAGNOSTIC_ONLY"
    assert gate["checks"]["model_gate_pass"] is True
    assert gate["checks"]["threshold_selected"] is False


def test_stage61_gate_fails_when_permutation_p_value_is_high():
    report = {
        "summary": {
            "h12_corridor3_relative_geometry": {
                "val_stop": {"auc_median": 0.68, "pr_auc_lift_median": 0.12},
                "threshold_selection": {
                    "status": "SELECTED",
                    "selected": {
                        "pf": 1.2,
                        "trades_per_year": 30,
                        "pf_spread_020": 1.1,
                    },
                },
                "permutation_baseline": {"empirical_p_value": 0.50},
            }
        }
    }

    gate = s61.stage61_gate_results(report)

    assert gate["overall_status"] == "MODEL_GATE_FAILED"
    assert gate["checks"]["permutation_p_value_le_0_10"] is False


def test_stage61_baseline_delta_summary_uses_val_stop_only():
    report = {
        "summary": {
            "h12_clock_shift_back": {
                "val_stop": {"auc_median": 0.61, "pr_auc_lift_median": 0.10},
                "threshold_selection": {
                    "status": "SELECTED",
                    "val_pf_median": 1.20,
                    "selected": {"pf": 1.20},
                },
                "permutation_baseline": {"empirical_p_value": 0.20},
            },
            "h12_clock_shift_back_plus_corridor3_geometry": {
                "val_stop": {"auc_median": 0.64, "pr_auc_lift_median": 0.11},
                "threshold_selection": {
                    "status": "SELECTED",
                    "val_pf_median": 1.25,
                    "selected": {"pf": 1.05},
                },
                "permutation_baseline": {"empirical_p_value": 0.05},
            },
        }
    }

    delta = s61.stage61_baseline_delta_summary(report)

    row = delta["profiles"]["h12_clock_shift_back_plus_corridor3_geometry"]
    assert row["auc_delta_vs_baseline"] == pytest.approx(0.03)
    assert row["pr_auc_lift_delta_vs_baseline"] == pytest.approx(0.01)
    assert row["pf_delta_vs_baseline"] == pytest.approx(0.05)
    assert row["passes_delta_gate"] is True
    assert delta["best_profile"] == "h12_clock_shift_back_plus_corridor3_geometry"


def test_stage61_definitive_mask_excludes_timeout_and_invalid():
    df = pd.DataFrame({
        "stage6_close_reason": ["TP", "SL", "AMBIGUOUS_SL_FIRST", "TIMEOUT", "INVALID"],
        "stage6_definitive_tp_vs_sl_flag": [1.0, 0.0, 0.0, np.nan, np.nan],
    })

    mask = s61.stage61_definitive_mask(df)

    assert mask.tolist() == [True, True, True, False, False]


def test_stage61_build_features_drops_stage6_columns(monkeypatch):
    captured = {}

    def fake_builder(df, profile):
        captured["columns"] = tuple(df.columns)
        return np.zeros((len(df), 4), dtype=np.float32)

    monkeypatch.setattr(s61, "build_stage5_4_features", fake_builder)
    df = pd.DataFrame({
        "time": ["2025.01.01 00:00"],
        "stage6_pnl_r": [1.0],
        "stage6_definitive_tp_vs_sl_flag": [1.0],
    })

    X = s61.stage61_build_features(df, "h12_clock_shift_back")

    assert X.shape == (1, 4)
    assert "stage6_pnl_r" not in captured["columns"]
    assert "stage6_definitive_tp_vs_sl_flag" not in captured["columns"]


def test_stage61_combined_features_concat_baseline_and_geometry(monkeypatch):
    df = pd.DataFrame({
        "time": ["2025.01.01 00:00", "2025.01.01 01:00"],
        "stage6_pnl_r": [1.0, -1.0],
        "stage6_definitive_tp_vs_sl_flag": [1.0, 0.0],
        "dummy": [0.1, 0.2],
    })
    captured = {}

    def fake_baseline_builder(clean_df, profile):
        captured["baseline_columns"] = tuple(clean_df.columns)
        assert profile == "clock_shift_back"
        return np.asarray([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)

    def fake_geometry_builder(clean_df, profile):
        captured["geometry_columns"] = tuple(clean_df.columns)
        assert profile == "h12_corridor3_relative_geometry"
        return np.asarray([[5.0, 6.0, 7.0], [8.0, 9.0, 10.0]], dtype=np.float32)

    monkeypatch.setattr(s61, "build_stage5_4_features", fake_baseline_builder)
    monkeypatch.setattr(s61, "stage61_build_geometry_features", fake_geometry_builder)

    X = s61.stage61_build_features(df, "h12_clock_shift_back_plus_corridor3_geometry")

    assert X.dtype == np.float32
    assert X.shape == (2, 5)
    assert X.tolist() == [[1.0, 2.0, 5.0, 6.0, 7.0], [3.0, 4.0, 8.0, 9.0, 10.0]]
    assert "stage6_pnl_r" not in captured["baseline_columns"]
    assert "stage6_definitive_tp_vs_sl_flag" not in captured["geometry_columns"]


def test_stage61_combined_feature_names_include_baseline_and_geometry_names():
    names = s61.stage61_feature_names("h12_clock_shift_back_plus_corridor3_geometry")

    assert names[0] == "baseline.fractal0.shift"
    assert names[1] == "baseline.fractal0.back"
    assert names[200] == "baseline.hour_sin"
    assert names[204] == "geometry.slot00_price_coord_atr"
    assert names[-1] == "geometry.slot39_selection_rank"
    assert len(names) == 204 + 40 * 8


def test_stage61_xgboost_uses_n_jobs_24():
    import inspect
    src = inspect.getsource(s61.evaluate_stage61_profile_seed)
    assert "n_jobs=24" in src, "evaluate_stage61_profile_seed must pass n_jobs=24 to XGBClassifier"


def test_stage61_runner_writes_timestamps_and_n_jobs(monkeypatch, tmp_path):
    import json

    def fake_evaluate(split, feature_split, profile, seed):
        return {
            "profile": profile,
            "seed": int(seed),
            "val_stop": {"auc": 0.5, "pr_auc_lift": 0.0},
            "threshold_selection": {"status": "NO_THRESHOLD", "selected": None},
            "predictions": {},
            "feature_importance": [],
        }

    monkeypatch.setattr(s61, "stage6_load_labeled_splits", lambda *a, **kw: _fake_split())
    monkeypatch.setattr(s61, "evaluate_stage61_profile_seed", fake_evaluate)
    monkeypatch.setattr(s61, "stage61_input_file_manifest", lambda: {"dummy": {"sha256": "a" * 64, "bytes": 100, "row_count": 10}})
    monkeypatch.setattr(s61, "stage61_fractal_format_preflight", lambda s: {})
    monkeypatch.setattr(s61, "stage6_outcome_preflight", lambda s: {})
    monkeypatch.setattr(s61, "stage61_feature_preflight", lambda s: {})
    monkeypatch.setattr(s61, "stage6_all_trade_baseline", lambda s: {})
    monkeypatch.setattr(s61, "stage61_build_features", lambda df, profile: np.ones((len(df), 2), dtype=np.float32))

    out = tmp_path / "test_stage6_1.json"
    report = s61.run_stage6_1_relative_geometry(output_path=out, resume=False)

    data = json.loads(out.read_text())
    assert "started_at" in data, "missing started_at"
    assert "finished_at" in data, "missing finished_at"
    assert data["config"].get("xgb_n_jobs") == 24, f"got xgb_n_jobs={data['config'].get('xgb_n_jobs')}"
    for run in data.get("raw_runs", []):
        assert "elapsed_sec" in run, f"missing elapsed_sec in {run.get('profile')} seed={run.get('seed')}"


def test_stage61_runner_writes_initial_checkpoint_before_preflight(monkeypatch, tmp_path):
    import json

    def fail_load(*args, **kwargs):
        raise RuntimeError("preflight boom")

    monkeypatch.setattr(s61, "stage6_load_labeled_splits", fail_load)
    monkeypatch.setattr(s61, "stage61_input_file_manifest", lambda: {"dummy": {"sha256": "a" * 64, "bytes": 100, "row_count": 10}})

    out = tmp_path / "test_stage6_1_initial.json"
    with pytest.raises(RuntimeError, match="preflight boom"):
        s61.run_stage6_1_relative_geometry(output_path=out, resume=False)

    data = json.loads(out.read_text())
    assert data["status"] == "RUNNING"
    assert "started_at" in data
    assert data["config"]["xgb_n_jobs"] == 24
    assert data["done_runs"] == 0
    assert data["total_runs"] == len(s61.STAGE6_1_CONFIG.profile_keys) * len(s61.STAGE6_1_CONFIG.seeds)


def test_stage61_script_help_runs_from_repo_root():
    import subprocess
    import sys

    proc = subprocess.run(
        [sys.executable, "ML/baseline/benchmark_stage6_1_relative_geometry.py", "--help"],
        cwd=s61.REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert proc.returncode == 0
    assert "--stage6-1-relative-geometry" in proc.stdout
    assert "--no-resume" in proc.stdout


def test_stage61_cli_has_resume_flags():
    from ML.baseline.benchmark_stage6_1_relative_geometry import main
    import sys
    try:
        main(argv=["prog", "--help"])
    except SystemExit as exc:
        assert exc.code == 0


def test_stage61_runner_resume_skips_done_runs(monkeypatch, tmp_path):
    import json

    all_profiles = list(s61.STAGE6_1_CONFIG.profile_keys)
    all_seeds = list(s61.STAGE6_1_CONFIG.seeds)
    all_runs = [
        {
            "profile": p, "seed": int(s),
            "val_stop": {"auc": 0.5, "pr_auc_lift": 0.0},
            "threshold_selection": {"status": "NO_THRESHOLD", "selected": None},
            "predictions": {},
            "feature_importance": [],
            "elapsed_sec": 0.1,
        }
        for p in all_profiles for s in all_seeds[:2]
    ]
    existing = {
        "stage": "6.1",
        "status": "RUNNING",
        "started_at": "2026-06-29T00:00:00+00:00",
        "config": {
            "profiles": all_profiles,
            "primary_profile": s61.STAGE6_1_CONFIG.primary_profile,
            "seeds": all_seeds,
            "xgb_n_jobs": 24,
        },
        "input_manifest": {"dummy": {"sha256": "a" * 64}},
        "raw_runs": all_runs,
        "done_runs": len(all_runs),
        "total_runs": len(all_profiles) * len(all_seeds),
    }
    out = tmp_path / "test_resume.json"
    out.write_text(json.dumps(existing))

    seen = []
    def fake_evaluate(split, feature_split, profile, seed):
        seen.append((profile, int(seed)))
        return {
            "profile": profile,
            "seed": int(seed),
            "val_stop": {"auc": 0.5, "pr_auc_lift": 0.0},
            "threshold_selection": {"status": "NO_THRESHOLD", "selected": None},
            "predictions": {},
            "feature_importance": [],
        }

    monkeypatch.setattr(s61, "stage6_load_labeled_splits", lambda *a, **kw: _fake_split())
    monkeypatch.setattr(s61, "evaluate_stage61_profile_seed", fake_evaluate)
    monkeypatch.setattr(s61, "stage61_input_file_manifest", lambda: {"dummy": {"sha256": "a" * 64}})
    monkeypatch.setattr(s61, "stage61_fractal_format_preflight", lambda s: {})
    monkeypatch.setattr(s61, "stage6_outcome_preflight", lambda s: {})
    monkeypatch.setattr(s61, "stage61_feature_preflight", lambda s: {})
    monkeypatch.setattr(s61, "stage6_all_trade_baseline", lambda s: {})
    monkeypatch.setattr(s61, "stage61_build_features", lambda df, profile: np.ones((len(df), 2), dtype=np.float32))

    s61.run_stage6_1_relative_geometry(output_path=out, resume=True)

    assert len(seen) == len(all_profiles) * (len(all_seeds) - 2), \
        f"expected {len(all_profiles) * (len(all_seeds) - 2)} new runs, got {len(seen)}: {seen}"
    for p, s in seen:
        assert s in all_seeds[2:], f"unexpected run: {p} seed={s}"
