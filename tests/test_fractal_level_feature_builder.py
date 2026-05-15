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


def test_old_updn_features_skip_fractal0_and_use_fractal1():
    features = build_zone_features(make_source_frame_with_fractal0_and_fractal1_updn())

    assert "fractal0_up_24" not in features.columns
    assert features.filter(like="old_up_24").sum(axis=1).iloc[0] > 0


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
