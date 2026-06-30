import inspect

import numpy as np
import pandas as pd
import pytest

import ML.baseline.benchmark_stage6_3_h6_feature_parity as s63


def test_stage63_config_horizon_is_6():
    cfg = s63.STAGE6_3_CONFIG

    assert cfg.horizon_bars == 6
    assert cfg.stop_offset_atr == 0.5
    assert cfg.take_profit_atr == 2.0
    assert cfg.entry_lag_bars == 1
    assert cfg.primary_profile == "h6_clock_shift_back"
    assert cfg.seeds == (42, 77, 123)


def test_stage63_profile_keys_include_baseline():
    keys = s63.stage63_profile_keys()

    assert "h6_clock_shift_back" in keys


def test_stage63_profile_keys_include_geometry_profiles():
    keys = s63.stage63_profile_keys()

    assert "h6_nearest_price40_relative_geometry" in keys
    assert "h6_nearest_time40_relative_geometry" in keys
    assert "h6_corridor3_relative_geometry" in keys
    assert "h6_corridor10_relative_geometry" in keys
    assert "h6_zones10_uniform_summary" in keys


def test_stage63_profile_keys_include_price_action_profiles():
    keys = s63.stage63_profile_keys()

    assert "h6_price_action_core" in keys
    assert "h6_price_action_regime" in keys


def test_stage63_profile_keys_include_combined_profiles():
    keys = s63.stage63_profile_keys()

    assert "h6_clock_shift_back_plus_nearest_time40_geometry" in keys
    assert "h6_clock_shift_back_plus_corridor3_geometry" in keys
    assert "h6_clock_shift_back_plus_corridor10_geometry" in keys
    assert "h6_clock_shift_back_plus_price_action_core" in keys
    assert "h6_clock_shift_back_plus_price_action_regime" in keys


def test_stage63_feature_names_clock_shift_back_matches_stage5_4():
    names = s63.stage63_feature_names("h6_clock_shift_back")

    assert len(names) > 0
    assert "fractal0.shift" in names
    assert "fractal0.back" in names


def test_stage63_feature_names_geometry_matches_stage61_width():
    names = s63.stage63_feature_names("h6_corridor3_relative_geometry")

    assert len(names) == 40 * 8
    assert "slot00_price_coord_atr" in names


def test_stage63_feature_names_price_action_core_matches_stage62_width():
    names = s63.stage63_feature_names("h6_price_action_core")

    assert len(names) == 30
    assert "range_w1_atr" in names


def test_stage63_feature_names_price_action_regime_includes_regime_fields():
    names = s63.stage63_feature_names("h6_price_action_regime")

    assert len(names) == 34
    assert "source_volume_to_source_volume_mean_24" in names


def test_stage63_feature_names_combined_geometry_have_baseline_prefix():
    names = s63.stage63_feature_names("h6_clock_shift_back_plus_corridor3_geometry")

    assert names[0].startswith("baseline.")
    assert any(n.startswith("geometry.") for n in names)
    assert len(names) == 204 + 40 * 8


def test_stage63_feature_names_combined_price_action_have_baseline_prefix():
    names = s63.stage63_feature_names("h6_clock_shift_back_plus_price_action_core")

    assert names[0].startswith("baseline.")
    assert any(n.startswith("price_action.") for n in names)
    assert len(names) == 204 + 30


def test_stage63_feature_names_count_matches_matrix_for_all_profiles(monkeypatch):
    def fake_61_builder(df, profile):
        if "zones10" in profile:
            return np.zeros((len(df), 20 * 5), dtype=np.float32)
        if "corridor" in profile or "nearest" in profile:
            return np.zeros((len(df), 40 * 8), dtype=np.float32)
        return np.zeros((len(df), 2), dtype=np.float32)

    def fake_62_builder(df, profile, ohlc=None):
        if profile == "h12_price_action_regime":
            return np.zeros((len(df), 34), dtype=np.float32)
        return np.zeros((len(df), 30), dtype=np.float32)

    def fake_baseline_builder(df, profile):
        return np.zeros((len(df), 204), dtype=np.float32)

    def fake_s5_4_names(profile):
        return [f"f{i}" for i in range(204)]

    monkeypatch.setattr(s63, "stage61_build_features", fake_61_builder)
    monkeypatch.setattr(s63, "stage62_build_features", fake_62_builder)
    monkeypatch.setattr(s63, "build_stage5_4_features", fake_baseline_builder)
    monkeypatch.setattr(s63, "stage5_4_feature_names", fake_s5_4_names)

    df = pd.DataFrame({"time": ["2021.01.02 00:00", "2021.01.02 01:00"], "ATR": [2.0, 2.0]})

    for profile in s63.stage63_profile_keys():
        X = s63.stage63_build_features(df, profile)
        assert X.shape[1] == len(s63.stage63_feature_names(profile)), f"mismatch for {profile}: matrix {X.shape[1]} vs names {len(s63.stage63_feature_names(profile))}"


def test_stage63_xgboost_uses_n_jobs_24():
    src = inspect.getsource(s63.evaluate_stage63_profile_seed)
    assert "n_jobs=STAGE6_3_CONFIG.xgb_n_jobs" in src


def _tiny_ohlc():
    return pd.DataFrame({
        "time": pd.date_range("2021-01-01 00:00", periods=30, freq="h"),
        "open": np.arange(100.0, 130.0),
        "high": np.arange(101.0, 131.0),
        "low": np.arange(99.0, 129.0),
        "close": np.arange(100.5, 130.5),
        "volume": np.arange(1000.0, 1030.0),
        "atr14": np.full(30, 2.0),
    })


def _fake_split():
    base = pd.DataFrame({
        "time": ["2021.01.02 00:00", "2021.01.02 01:00", "2021.01.02 02:00", "2021.01.02 03:00"],
        "ATR": [2.0, 2.0, 2.0, 2.0],
        "stage6_close_reason": ["TP", "SL", "TP", "SL"],
        "stage6_definitive_tp_vs_sl_flag": [1.0, 0.0, 1.0, 0.0],
        "stage6_pnl_r": [4.0, -1.0, 4.0, -1.0],
    })
    return {
        "train_core": base.copy(),
        "val_stop": base.copy(),
        "diagnostic_holdout": base.copy(),
        "low_n_disclosure": base.copy(),
    }


def test_stage63_runner_writes_initial_checkpoint(monkeypatch, tmp_path):
    import json

    out = tmp_path / "stage63.json"

    monkeypatch.setattr(s63, "stage63_input_file_manifest", lambda: {"dummy": {"sha256": "a" * 64}})
    monkeypatch.setattr(s63, "stage6_load_labeled_splits", lambda config: _fake_split())
    monkeypatch.setattr(s63, "stage62_load_ohlc_frame", lambda: _tiny_ohlc())
    monkeypatch.setattr(s63, "stage6_outcome_preflight", lambda split: {"ok": True})
    monkeypatch.setattr(s63, "stage6_all_trade_baseline", lambda df: {"pf": 1.0})
    monkeypatch.setattr(
        s63,
        "stage63_build_features",
        lambda df, profile, ohlc=None: np.ones((len(df), 2), dtype=np.float32),
    )
    monkeypatch.setattr(
        s63,
        "evaluate_stage63_profile_seed",
        lambda split, feature_split, profile, seed: {
            "profile": profile,
            "seed": seed,
            "val_stop": {"auc": 0.51, "pr_auc_lift": 0.01},
            "threshold_selection": {"status": "NO_THRESHOLD", "selected": None},
            "predictions": {"val_stop": {"y_score_all": [0.1, 0.2, 0.3, 0.4]}},
        },
    )

    report = s63.run_stage6_3_h6_feature_parity(output_path=out, resume=False)

    assert out.exists()
    assert report["done_runs"] == report["total_runs"]
    assert report["config"]["xgb_n_jobs"] == 24
    assert "started_at" in report
    assert "finished_at" in report
    assert "elapsed_sec" in report
    assert all("elapsed_sec" in run for run in report["raw_runs"])


def test_stage63_runner_writes_required_json_sections(monkeypatch, tmp_path):
    import json

    out = tmp_path / "stage63_check.json"

    monkeypatch.setattr(s63, "stage63_input_file_manifest", lambda: {"dummy": {"sha256": "a" * 64}})
    monkeypatch.setattr(s63, "stage6_load_labeled_splits", lambda config: _fake_split())
    monkeypatch.setattr(s63, "stage62_load_ohlc_frame", lambda: _tiny_ohlc())
    monkeypatch.setattr(s63, "stage6_outcome_preflight", lambda split: {"ok": True})
    monkeypatch.setattr(s63, "stage6_all_trade_baseline", lambda df: {"pf": 1.0})
    monkeypatch.setattr(
        s63,
        "stage63_build_features",
        lambda df, profile, ohlc=None: np.ones((len(df), 2), dtype=np.float32),
    )
    monkeypatch.setattr(
        s63,
        "evaluate_stage63_profile_seed",
        lambda split, feature_split, profile, seed: {
            "profile": profile,
            "seed": seed,
            "val_stop": {"auc": 0.51, "pr_auc_lift": 0.01},
            "threshold_selection": {"status": "NO_THRESHOLD", "selected": None},
            "predictions": {"val_stop": {"y_score_all": [0.1, 0.2, 0.3, 0.4]}},
        },
    )

    report = s63.run_stage6_3_h6_feature_parity(output_path=out, resume=False)
    data = json.loads(out.read_text())

    assert "config" in data
    assert "raw_runs" in data
    assert "summary" in data
    assert "baseline_plus_feature_delta" in data
    assert "h6_vs_h12_disclosure" in data
    assert "gate" in data
    assert "status" in data
    assert "elapsed_sec" in data


def test_stage63_gate_returns_diagnostic_only():
    report = {
        "summary": {
            "h6_clock_shift_back": {
                "val_stop": {"auc_median": 0.55, "pr_auc_lift_median": 0.02},
                "threshold_selection": {"status": "NO_THRESHOLD", "selected": None},
                "permutation_baseline": {"empirical_p_value": 0.5},
            }
        },
        "baseline_plus_feature_delta": {"profiles": {}},
    }

    gate = s63.stage63_gate_results(report)

    assert gate["artifact_status"] == "DIAGNOSTIC_ONLY"
    assert gate["overall_status"] in ("MODEL_GATE_FAILED", "DIAGNOSTIC_ONLY")


def test_stage63_cli_has_resume_flags():
    src = inspect.getsource(s63.main)
    assert "--stage6-3-h6-feature-parity" in src
    assert "--resume" in src
    assert "--no-resume" in src


def test_stage63_script_help_runs():
    import subprocess
    import sys

    proc = subprocess.run(
        [sys.executable, "ML/baseline/benchmark_stage6_3_h6_feature_parity.py", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0
    assert "--stage6-3-h6-feature-parity" in proc.stdout
    assert "--no-resume" in proc.stdout


def test_stage63_definitive_mask_excludes_timeout_and_invalid():
    df = pd.DataFrame({
        "stage6_close_reason": ["TP", "SL", "AMBIGUOUS_SL_FIRST", "TIMEOUT", "INVALID"],
        "stage6_definitive_tp_vs_sl_flag": [1.0, 0.0, 0.0, np.nan, np.nan],
    })

    mask = s63.stage63_definitive_mask(df)

    assert mask.tolist() == [True, True, True, False, False]


def test_stage63_baseline_delta_summary_requires_improvement_over_baseline():
    report = {
        "summary": {
            "h6_clock_shift_back": {
                "val_stop": {"auc_median": 0.61, "pr_auc_lift_median": 0.10},
                "threshold_selection": {"status": "SELECTED", "val_pf_median": 1.20, "selected": {"pf": 1.20}},
                "permutation_baseline": {"empirical_p_value": 0.20},
            },
            "h6_clock_shift_back_plus_corridor3_geometry": {
                "val_stop": {"auc_median": 0.64, "pr_auc_lift_median": 0.11},
                "threshold_selection": {"status": "SELECTED", "val_pf_median": 1.25, "selected": {"pf": 1.05}},
                "permutation_baseline": {"empirical_p_value": 0.05},
            },
        }
    }

    delta = s63.stage63_baseline_delta_summary(report)

    row = delta["profiles"]["h6_clock_shift_back_plus_corridor3_geometry"]
    assert row["auc_delta_vs_baseline"] == pytest.approx(0.03)
    assert row["pr_auc_lift_delta_vs_baseline"] == pytest.approx(0.01)
    assert row["passes_delta_gate"] is True
    assert delta["best_profile"] == "h6_clock_shift_back_plus_corridor3_geometry"


def test_stage63_delta_gate_fails_when_auc_delta_too_small():
    report = {
        "summary": {
            "h6_clock_shift_back": {
                "val_stop": {"auc_median": 0.617, "pr_auc_lift_median": 0.13},
                "threshold_selection": {"status": "SELECTED", "selected": {"pf": 1.25}},
            },
            "h6_clock_shift_back_plus_price_action_core": {
                "val_stop": {"auc_median": 0.622, "pr_auc_lift_median": 0.14},
                "threshold_selection": {"status": "SELECTED", "selected": {"pf": 1.20}},
                "permutation_baseline": {"empirical_p_value": 0.05},
            },
        }
    }

    delta = s63.stage63_baseline_delta_summary(report)

    row = delta["profiles"]["h6_clock_shift_back_plus_price_action_core"]
    assert row["passes_delta_gate"] is False
    assert row["auc_delta_vs_baseline"] < 0.02


def test_stage63_summary_aggregates_by_median_over_seeds(monkeypatch):
    split = {"val_stop": pd.DataFrame({"_year": [2021, 2021], "stage6_pnl_r": [1.0, -1.0]})}
    report = {
        "raw_runs": [
            {
                "profile": "h6_clock_shift_back",
                "seed": 42,
                "val_stop": {"auc": 0.61, "pr_auc_lift": 0.06},
                "threshold_selection": {"status": "SELECTED", "selected": {"threshold": 0.5, "pf": 1.1, "trades": 10}},
                "predictions": {"val_stop": {"y_score_all": [0.1, 0.2]}},
            },
            {
                "profile": "h6_clock_shift_back",
                "seed": 77,
                "val_stop": {"auc": 0.63, "pr_auc_lift": 0.08},
                "threshold_selection": {"status": "SELECTED", "selected": {"threshold": 0.6, "pf": 1.3, "trades": 20}},
                "predictions": {"val_stop": {"y_score_all": [0.2, 0.3]}},
            },
            {
                "profile": "h6_clock_shift_back",
                "seed": 123,
                "val_stop": {"auc": 0.62, "pr_auc_lift": 0.07},
                "threshold_selection": {"status": "SELECTED", "selected": {"threshold": 0.7, "pf": 1.2, "trades": 30}},
                "predictions": {"val_stop": {"y_score_all": [0.3, 0.4]}},
            },
        ]
    }

    monkeypatch.setattr(
        s63,
        "stage6_permutation_threshold_baseline",
        lambda df, score, seed: {"n_perm": 200, "observed_pf": 1.0, "empirical_p_value": 0.10 + seed / 1000.0},
    )

    summary = s63.stage63_summary(report, split)["h6_clock_shift_back"]

    assert summary["val_stop"]["auc_median"] == 0.62
    assert summary["threshold_selection"]["selected"]["pf"] == 1.2
    assert len(summary["seed_runs"]) == 3


def test_stage63_h6_vs_h12_disclosure_returns_comparison():
    h6_report = {
        "summary": {
            "h6_clock_shift_back": {
                "val_stop": {"auc_median": 0.68},
                "threshold_selection": {"val_pf_median": 1.3},
            }
        }
    }
    h12_summary = {
        "h12_clock_shift_back": {
            "val_stop": {"auc_median": 0.61},
            "threshold_selection": {"val_pf_median": 1.2},
        }
    }

    disclosure = s63.stage63_h6_vs_h12_disclosure(h6_report, h12_summary)

    assert "h6_clock_shift_back" in disclosure
    assert disclosure["h6_clock_shift_back"]["h6_auc_median"] == 0.68
    assert disclosure["h6_clock_shift_back"]["h12_auc_median"] == 0.61


def test_stage63_runner_handles_resume(monkeypatch, tmp_path):
    import json

    all_profiles = list(s63.STAGE6_3_CONFIG.profile_keys)
    all_seeds = list(s63.STAGE6_3_CONFIG.seeds)
    all_runs = [
        {
            "profile": p, "seed": int(s),
            "val_stop": {"auc": 0.5, "pr_auc_lift": 0.0},
            "threshold_selection": {"status": "NO_THRESHOLD", "selected": None},
            "predictions": {},
            "elapsed_sec": 0.1,
        }
        for p in all_profiles for s in all_seeds[:2]
    ]
    existing = {
        "stage": "6.3",
        "status": "RUNNING",
        "started_at": "2026-06-30T00:00:00+00:00",
        "config": {
            "profiles": all_profiles,
            "primary_profile": s63.STAGE6_3_CONFIG.primary_profile,
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
        }

    monkeypatch.setattr(s63, "stage63_input_file_manifest", lambda: {"dummy": {"sha256": "a" * 64}})
    monkeypatch.setattr(s63, "stage6_load_labeled_splits", lambda config: _fake_split())
    monkeypatch.setattr(s63, "stage62_load_ohlc_frame", lambda: _tiny_ohlc())
    monkeypatch.setattr(s63, "stage6_outcome_preflight", lambda split: {"ok": True})
    monkeypatch.setattr(s63, "stage6_all_trade_baseline", lambda df: {"pf": 1.0})
    monkeypatch.setattr(
        s63,
        "stage63_build_features",
        lambda df, profile, ohlc=None: np.ones((len(df), 2), dtype=np.float32),
    )
    monkeypatch.setattr(s63, "evaluate_stage63_profile_seed", fake_evaluate)

    s63.run_stage6_3_h6_feature_parity(output_path=out, resume=True)

    assert len(seen) == len(all_profiles) * (len(all_seeds) - 2), \
        f"expected {len(all_profiles) * (len(all_seeds) - 2)} new runs, got {len(seen)}: {seen}"
    for p, s in seen:
        assert s in all_seeds[2:], f"unexpected run: {p} seed={s}"
