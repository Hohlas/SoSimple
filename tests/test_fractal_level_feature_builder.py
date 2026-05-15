import pandas as pd

from ML.fractal_level_feature_builder import parse_fractal
from ML.fractal_level_feature_builder import parse_fractal_time
from ML.fractal_level_feature_builder import parse_row_time
from ML.fractal_level_feature_builder import audit_fractal_rows
from ML.fractal_level_feature_builder import build_feature_contract
from ML.fractal_level_feature_builder import build_fractal_level_features
from ML.fractal_level_feature_builder import build_zone_features
from ML.fractal_level_feature_builder import apply_feature_normalizer
from ML.fractal_level_feature_builder import fit_feature_normalizer


def make_source_frame(row_time: str, fractal0: str, fractal1: str) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "time": [row_time],
            "ATR": [1.0],
            "fractal0": [fractal0],
            "fractal1": [fractal1],
        }
    )


def make_source_frame_with_fractal0_and_fractal1_updn() -> pd.DataFrame:
    return make_source_frame(
        row_time="2024.01.01 10:00",
        fractal0="2024.01.01 10:00:100:-1:0:0:0:0:0:0:0:0:9:9:9:9:9:9:9:9:9:9:1",
        fractal1="2024.01.01 09:00:101:1:0:0:0:0:0:0:0:0:1:1:2:1:1:1:1:1:1:1:1",
    )


def make_frame_with_fractal1_far_and_fractal9_near() -> pd.DataFrame:
    row = {
        "time": "2024.01.01 10:00",
        "ATR": 2.0,
        "fractal0": "1704103200:100:-1:0:0:0:0:0:0:0:0:9:9:9:9:9:9:9:9:9:9:1",
    }
    for idx in range(1, 10):
        price = 130.0 if idx == 1 else 120.0
        if idx == 9:
            price = 101.0
        row[f"fractal{idx}"] = f"1704100{idx:03d}:{price}:1:0:0:1:0:0:0.5:{idx}:0.1:1:2:3:4:5:6:7:8:9:10:1"
    return pd.DataFrame([row])


def test_parse_fractal_reads_price_direction_time_and_updn():
    parsed = parse_fractal(
        "123:2010.5:-1:0.1:0.2:1:0:0.3:0.4:2:0.5:"
        "1.0:0.2:1.5:0.3:2.0:0.4:0.6:0.1:0.8:0.2:1.1"
    )

    assert parsed["time"] == 123
    assert parsed["price"] == 2010.5
    assert parsed["direction"] == -1
    assert parsed["up_24"] == 1.5
    assert parsed["dn_24"] == 0.3


def test_parse_row_time_and_fractal_time_use_same_unit():
    row_time = parse_row_time("2024.01.01 10:00")
    fractal_time = parse_fractal_time("2024.01.01 09:00")

    assert fractal_time <= row_time


def test_audit_rejects_future_fractal_time():
    frame = make_source_frame(
        row_time="2024.01.01 10:00",
        fractal0="100:2000:-1:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:1",
        fractal1="9999999999:2001:1:0:0:0:0:0:0:0:0:1:1:1:1:1:1:1:1:1:1:1",
    )

    result = audit_fractal_rows(frame)

    assert result["future_fractal_rows"] == 1


def test_old_updn_features_available_in_zones():
    features = build_zone_features(make_source_frame_with_fractal0_and_fractal1_updn())
    assert "fractal0_up_24" not in features.columns
    updn_cols = [c for c in features.columns if "up_24_sum" in c or "dn_24_sum" in c]
    assert len(updn_cols) > 0, "zone features should include up_24_sum/dn_24_sum columns"


def test_feature_contract_marks_offline_targets_as_not_model_inputs():
    contract = {entry["name"]: entry for entry in build_feature_contract(fractal_count=2)}

    assert contract["signal"]["available_at"] == "diagnostic_only"
    assert contract["signal"]["model_input"] is False
    assert contract["up_6"]["available_at"] == "target_only"
    assert contract["up_6"]["model_input"] is False
    assert contract["trail_*"]["available_at"] == "target_only"
    assert contract["fractal0_up_24"]["available_at"] == "target_only"
    assert contract["fractal0_up_24"]["model_input"] is False
    assert contract["fractal1_up_24"]["available_at"] == "historical_fractal_state"
    assert contract["fractal1_up_24"]["model_input"] is True


def test_nearest_k_sorts_by_price_distance_not_fractal_index():
    frame = make_frame_with_fractal1_far_and_fractal9_near()
    features = build_fractal_level_features(frame, input_family="nearest_k", k=1)

    assert features.loc[0, "fractal0_direction"] == -1
    assert features.loc[0, "nearest_00_source_index"] == 9
    assert features.loc[0, "nearest_00_valid"] == 1
    assert "fractal0_up_24" not in features.columns


def test_feature_normalizer_uses_train_frozen_statistics():
    train = pd.DataFrame({"a": [1.0, 3.0], "nearest_00_valid": [1, 1], "nearest_00_source_index": [2, 9]})
    validation = pd.DataFrame({"a": [3.0], "nearest_00_valid": [1], "nearest_00_source_index": [9]})

    stats = fit_feature_normalizer(train)
    normalized = apply_feature_normalizer(validation, stats)

    assert normalized.loc[0, "a"] == 1.0
    assert normalized.loc[0, "nearest_00_valid"] == 1
    assert normalized.loc[0, "nearest_00_source_index"] == 9


def _make_multi_fractal_frame(n_fractals: int = 20) -> pd.DataFrame:
    row = {
        "time": "2024.01.01 10:00",
        "ATR": 1.0,
        "fractal0": "1704103200:100:-1:0:0:0:0:0:0:0:0:1:2:3:4:5:6:7:8:9:10:1",
    }
    for idx in range(1, n_fractals):
        row[f"fractal{idx}"] = (
            f"1704103200:{100 + idx}:1:0:0:1:0:0:0.5:{idx}:0.1:1:2:3:4:5:6:7:8:9:10:1"
        )
    return pd.DataFrame([row])


def test_k4_produces_97_features():
    frame = _make_multi_fractal_frame()
    features = build_fractal_level_features(frame, input_family="nearest_k", k=4)
    model_cols = [c for c in features.columns if not c.endswith("_source_index")]
    assert len(model_cols) == 97


def test_k6_produces_143_features():
    frame = _make_multi_fractal_frame()
    features = build_fractal_level_features(frame, input_family="nearest_k", k=6)
    model_cols = [c for c in features.columns if not c.endswith("_source_index")]
    assert len(model_cols) == 143


def test_k16_produces_373_features():
    frame = _make_multi_fractal_frame()
    features = build_fractal_level_features(frame, input_family="nearest_k", k=16)
    model_cols = [c for c in features.columns if not c.endswith("_source_index")]
    assert len(model_cols) == 373


def test_geometry_only_removes_updn_columns():
    frame = _make_multi_fractal_frame()
    features = build_fractal_level_features(frame, input_family="nearest_k", k=4, geometry_only=True)
    updn_fields = ["up_3", "dn_3", "up_6", "dn_6", "up_12", "dn_12", "up_24", "dn_24", "up_48", "dn_48"]
    for slot in range(4):
        for field in updn_fields:
            col = f"nearest_{slot:02d}_{field}"
            assert col not in features.columns, f"geometry_only should remove {col}"
    model_cols = [c for c in features.columns if not c.endswith("_source_index")]
    assert len(model_cols) == 57


def test_geometry_only_keeps_geometry_columns():
    frame = _make_multi_fractal_frame()
    features = build_fractal_level_features(frame, input_family="nearest_k", k=4, geometry_only=True)
    geometry_fields = ["direction", "front", "back", "strong", "break", "reverse", "power", "count", "impulse", "fractal_atr"]
    for slot in range(4):
        for field in geometry_fields:
            col = f"nearest_{slot:02d}_{field}"
            assert col in features.columns, f"geometry_only should keep {col}"


def test_zone_features_count_matches_fractal_distribution():
    row = {
        "time": "2024.01.01 10:00",
        "ATR": 1.0,
        "fractal0": "1704103200:100:-1:0:0:0:0:0:0:0:0:1:2:3:4:5:6:7:8:9:10:1",
    }
    for idx in range(1, 5):
        price = 100 + idx * 0.1
        row[f"fractal{idx}"] = f"1704100{idx:03d}:{price}:1:0:0:1:0:0:0.5:{idx}:0.1:1:2:3:4:5:6:7:8:9:10:1"
    frame = pd.DataFrame([row])
    features = build_fractal_level_features(frame, input_family="zones")
    assert "zone_0_above_0.00_0.25_count" in features.columns
    assert features.loc[0, "total_count"] == 4
    assert features.loc[0, "fractals_above_count"] == 4


def test_zone_features_exclude_updn_when_geometry_only():
    frame = _make_multi_fractal_frame()
    features = build_fractal_level_features(frame, input_family="zones", geometry_only=True)
    updn_cols = [c for c in features.columns if "up_24" in c or "dn_24" in c]
    assert len(updn_cols) == 0, f"geometry_only zones should not have updn columns, found: {updn_cols}"


def test_zone_features_include_updn_by_default():
    frame = _make_multi_fractal_frame()
    features = build_fractal_level_features(frame, input_family="zones")
    updn_cols = [c for c in features.columns if "up_24" in c or "dn_24" in c]
    assert len(updn_cols) > 0, "zones should have updn columns by default"


def test_zones_plus_nearest_k_combines_features():
    frame = _make_multi_fractal_frame()
    features = build_fractal_level_features(frame, input_family="zones_plus_nearest_k", k=4)
    zone_features = build_fractal_level_features(frame, input_family="zones")
    nearest_features = build_fractal_level_features(frame, input_family="nearest_k", k=4)
    overlap = set(zone_features.columns) & set(nearest_features.columns)
    expected = len(zone_features.columns) + len(nearest_features.columns) - len(overlap)
    assert len(features.columns) == expected
