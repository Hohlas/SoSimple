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
    )
    assert cfg.seeds == (42, 77, 123)


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
                "permutation_baseline": {"p_value": 0.03},
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
                "permutation_baseline": {"p_value": 0.50},
            }
        }
    }

    gate = s61.stage61_gate_results(report)

    assert gate["overall_status"] == "MODEL_GATE_FAILED"
    assert gate["checks"]["permutation_p_value_le_0_10"] is False


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
