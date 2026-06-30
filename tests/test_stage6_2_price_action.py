import inspect

import numpy as np
import pandas as pd

import ML.baseline.benchmark_stage6_2_price_action as s62


def test_stage62_config_is_fixed_and_narrow():
    cfg = s62.STAGE6_2_CONFIG

    assert cfg.horizon_bars == 12
    assert cfg.stop_offset_atr == 0.5
    assert cfg.take_profit_atr == 2.0
    assert cfg.entry_lag_bars == 1
    assert cfg.primary_profile == "h12_price_action_core"
    assert cfg.profile_keys == (
        "h12_clock_shift_back",
        "h12_price_action_core",
        "h12_price_action_regime",
        "h12_clock_shift_back_plus_price_action_core",
        "h12_clock_shift_back_plus_price_action_regime",
    )
    assert cfg.seeds == (42, 77, 123)
    assert cfg.windows == (1, 3, 6, 12, 24)
    assert cfg.xgb_n_jobs == 24


def test_stage62_feature_denylist_blocks_future_columns():
    denylist = set(s62.stage62_feature_denylist())

    assert "stage6_definitive_tp_vs_sl_flag" in denylist
    assert "stage6_pnl_r" in denylist
    assert "trade_fav_h12" in denylist
    assert "fav_12_atr" in denylist
    assert "ret_12_dir_atr" in denylist
    assert "buy_bars_to_breach_H12_off05" in denylist
    assert "sell_stop_broken_H12_off05_flag" in denylist


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


def test_stage62_price_action_uses_only_bars_at_or_before_row_time():
    ohlc = _tiny_ohlc()
    row_time = ohlc.loc[24, "time"].strftime("%Y.%m.%d %H:%M")
    df = pd.DataFrame({"time": [row_time], "ATR": [2.0]})

    X_before = s62.stage62_build_price_action_features(df, "h12_price_action_core", ohlc=ohlc)
    ohlc_future_changed = ohlc.copy()
    ohlc_future_changed.loc[25:, ["open", "high", "low", "close"]] = 9999.0
    X_after = s62.stage62_build_price_action_features(df, "h12_price_action_core", ohlc=ohlc_future_changed)

    np.testing.assert_allclose(X_before, X_after)


def test_stage62_price_action_does_not_read_entry_open_row_plus_one():
    ohlc = _tiny_ohlc()
    row_time = ohlc.loc[24, "time"].strftime("%Y.%m.%d %H:%M")
    df = pd.DataFrame({"time": [row_time], "ATR": [2.0]})

    X_before = s62.stage62_build_price_action_features(df, "h12_price_action_core", ohlc=ohlc)
    ohlc_entry_open_changed = ohlc.copy()
    ohlc_entry_open_changed.loc[25, "open"] = 9999.0
    X_after = s62.stage62_build_price_action_features(df, "h12_price_action_core", ohlc=ohlc_entry_open_changed)

    np.testing.assert_allclose(X_before, X_after)


def test_stage62_price_action_features_have_stable_names_and_shape():
    ohlc = _tiny_ohlc()
    df = pd.DataFrame({
        "time": [ohlc.loc[24, "time"].strftime("%Y.%m.%d %H:%M")],
        "ATR": [2.0],
    })

    X_core = s62.stage62_build_price_action_features(df, "h12_price_action_core", ohlc=ohlc)
    X_regime = s62.stage62_build_price_action_features(df, "h12_price_action_regime", ohlc=ohlc)

    assert X_core.shape == (1, len(s62.stage62_price_action_feature_names("h12_price_action_core")))
    assert X_regime.shape == (1, len(s62.stage62_price_action_feature_names("h12_price_action_regime")))
    assert "ret_close_w12_atr" in s62.stage62_price_action_feature_names("h12_price_action_core")
    assert "source_volume_to_source_volume_mean_24" in s62.stage62_price_action_feature_names(
        "h12_price_action_regime"
    )
    assert np.isfinite(X_core).all()
    assert np.isfinite(X_regime).all()


def test_stage62_feature_names_for_combined_profiles_are_prefixed(monkeypatch):
    monkeypatch.setattr(s62, "stage5_4_feature_names", lambda profile: ["shift", "back"])

    names = s62.stage62_feature_names("h12_clock_shift_back_plus_price_action_core")

    assert names[:2] == ["baseline.shift", "baseline.back"]
    assert "price_action.ret_close_w12_atr" in names


def test_stage62_feature_name_count_matches_matrix_for_all_profiles(monkeypatch):
    ohlc = _tiny_ohlc()
    df = pd.DataFrame({
        "time": [ohlc.loc[24, "time"].strftime("%Y.%m.%d %H:%M")],
        "ATR": [2.0],
    })
    monkeypatch.setattr(
        s62,
        "build_stage5_4_features",
        lambda clean, profile: np.ones((len(clean), 2), dtype=np.float32),
    )
    monkeypatch.setattr(s62, "stage5_4_feature_names", lambda profile: ["shift", "back"])

    for profile in s62.stage62_profile_keys():
        X = s62.stage62_build_features(df, profile, ohlc=ohlc)
        assert X.shape[1] == len(s62.stage62_feature_names(profile)), profile


def test_stage62_feature_preflight_flags_nonfinite_values(monkeypatch):
    split = {"train_core": pd.DataFrame({"time": ["2021.01.02 00:00"], "ATR": [2.0]})}
    monkeypatch.setattr(
        s62,
        "stage62_build_features",
        lambda df, profile, ohlc=None: np.asarray([[1.0, np.nan]], dtype=np.float32),
    )

    audit = s62.stage62_feature_preflight(split, ohlc=_tiny_ohlc())

    assert audit["h12_price_action_core"]["feature_distribution"]["train_core"]["status"] == "ERROR"


def test_stage62_ohlc_contract_preflight_counts_missing_and_incomplete_windows():
    ohlc = _tiny_ohlc()
    df = pd.DataFrame({
        "time": [
            ohlc.loc[10, "time"].strftime("%Y.%m.%d %H:%M"),
            "2021.01.10 00:00",
        ],
        "ATR": [2.0, 2.0],
    })

    audit = s62.stage62_ohlc_contract_preflight(df, ohlc)

    assert audit["rows"] == 2
    assert audit["missing_exact_ohlc_rows"] == 1
    assert audit["incomplete_window_24_rows"] == 1
    assert audit["status"] == "WARNING"


def test_stage62_ohlc_preflight_requires_unique_monotonic_closed_bars():
    ohlc = _tiny_ohlc()
    bad = pd.concat([ohlc, ohlc.iloc[[5]]], ignore_index=True)

    audit = s62.stage62_ohlc_contract_preflight(
        pd.DataFrame({"time": [ohlc.loc[24, "time"].strftime("%Y.%m.%d %H:%M")]}),
        bad,
    )

    assert audit["status"] == "ERROR"
    assert "OHLC_TIME_NOT_UNIQUE" in audit["warnings"]


def test_stage62_definitive_mask_excludes_timeout_and_invalid():
    df = pd.DataFrame({
        "stage6_close_reason": ["TP", "SL", "AMBIGUOUS_SL_FIRST", "TIMEOUT", "INVALID"],
        "stage6_definitive_tp_vs_sl_flag": [1.0, 0.0, 0.0, np.nan, np.nan],
    })

    mask = s62.stage62_definitive_mask(df)

    assert mask.tolist() == [True, True, True, False, False]


def test_stage62_xgboost_uses_n_jobs_24():
    src = inspect.getsource(s62.evaluate_stage62_profile_seed)
    assert "n_jobs=STAGE6_2_CONFIG.xgb_n_jobs" in src


def test_stage62_gate_fails_when_primary_model_is_weak():
    report = {
        "summary": {
            "h12_price_action_core": {
                "val_stop": {"auc_median": 0.55, "pr_auc_lift_median": 0.02},
                "threshold_selection": {"status": "NO_THRESHOLD", "selected": None},
                "permutation_baseline": {"empirical_p_value": 0.5},
            }
        },
        "baseline_plus_price_action_delta": {"any_delta_gate_pass": False},
    }

    gate = s62.stage62_gate_results(report)

    assert gate["overall_status"] == "MODEL_GATE_FAILED"
    assert gate["artifact_status"] == "DIAGNOSTIC_ONLY"


def test_stage62_gate_marks_standalone_without_additive_value():
    report = {
        "summary": {
            "h12_price_action_core": {
                "val_stop": {"auc_median": 0.61, "pr_auc_lift_median": 0.06},
                "threshold_selection": {
                    "status": "SELECTED",
                    "selected": {"pf": 1.2, "trades_per_year": 30, "pf_spread_020": 1.1},
                },
                "permutation_baseline": {"empirical_p_value": 0.05},
            }
        },
        "baseline_plus_price_action_delta": {"any_delta_gate_pass": False},
    }

    gate = s62.stage62_gate_results(report)

    assert gate["overall_status"] == "DIAGNOSTIC_SIGNAL_FOUND"
    assert gate["interpretation"] == "STANDALONE_ONLY_NO_ADDITIVE_VALUE_CONFIRMED"


def test_stage62_delta_gate_requires_auc_and_pf_improvement():
    report = {
        "summary": {
            "h12_clock_shift_back": {
                "val_stop": {"auc_median": 0.617, "pr_auc_lift_median": 0.13},
                "threshold_selection": {"status": "SELECTED", "selected": {"pf": 1.25}},
            },
            "h12_clock_shift_back_plus_price_action_core": {
                "val_stop": {"auc_median": 0.622, "pr_auc_lift_median": 0.14},
                "threshold_selection": {"status": "SELECTED", "selected": {"pf": 1.20}},
                "permutation_baseline": {"empirical_p_value": 0.05},
            },
        }
    }

    delta = s62.stage62_baseline_delta_summary(report)

    row = delta["profiles"]["h12_clock_shift_back_plus_price_action_core"]
    assert row["passes_delta_gate"] is False
    assert row["auc_delta_vs_baseline"] < 0.02
    assert row["pf_delta_vs_baseline"] < 0.0


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


def test_stage62_runner_writes_initial_checkpoint_and_elapsed(monkeypatch, tmp_path):
    out = tmp_path / "stage62.json"

    monkeypatch.setattr(s62, "stage62_input_file_manifest", lambda: {"dummy": {"sha256": "a" * 64}})
    monkeypatch.setattr(s62, "stage6_load_labeled_splits", lambda config: _fake_split())
    monkeypatch.setattr(s62, "stage62_load_ohlc_frame", lambda: _tiny_ohlc())
    monkeypatch.setattr(s62, "stage6_outcome_preflight", lambda split: {"ok": True})
    monkeypatch.setattr(s62, "stage62_feature_preflight", lambda split, ohlc=None: {"ok": True})
    monkeypatch.setattr(s62, "stage6_all_trade_baseline", lambda df: {"pf": 1.0})
    monkeypatch.setattr(
        s62,
        "stage62_build_features",
        lambda df, profile, ohlc=None: np.ones((len(df), 2), dtype=np.float32),
    )
    monkeypatch.setattr(
        s62,
        "evaluate_stage62_profile_seed",
        lambda split, feature_split, profile, seed: {
            "profile": profile,
            "seed": seed,
            "val_stop": {"auc": 0.51, "pr_auc_lift": 0.01},
            "threshold_selection": {"status": "NO_THRESHOLD", "selected": None},
            "predictions": {"val_stop": {"y_score_all": [0.1, 0.2, 0.3, 0.4]}},
            "feature_importance": [],
        },
    )

    report = s62.run_stage6_2_price_action(output_path=out, resume=False)

    assert out.exists()
    assert report["done_runs"] == report["total_runs"]
    assert report["config"]["xgb_n_jobs"] == 24
    assert "started_at" in report
    assert "finished_at" in report
    assert "elapsed_sec" in report
    assert all("elapsed_sec" in run for run in report["raw_runs"])


def test_stage62_cli_has_resume_flags():
    src = inspect.getsource(s62.main)
    assert "--stage6-2-price-action" in src
    assert "--resume" in src
    assert "--no-resume" in src
