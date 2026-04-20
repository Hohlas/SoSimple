# =============================================================================
# Файл: tests/test_entry_path_task.py
# Назначение: Контрактные тесты для entry_path_v1 target contract и export helpers.
# Язык: Python 3.11+
# Создан: 2026-04-08
# Зависимости:
#   - pytest>=8.0, numpy>=1.24, pandas>=2.0
# Использование:
#   ./.venv/bin/python -m pytest tests/test_entry_path_task.py -q
# =============================================================================

import sys

import numpy as np
import pandas as pd
import pytest
import torch

sys.path.insert(0, '.')

from ML.data_loader import EntryPathDataset
from ML.entry_path_task import (
    ENTRY_PATH_ALLOWED_SEQUENCE_LENGTHS,
    ENTRY_PATH_FEATURE_PROFILES,
    ENTRY_PATH_MODEL_NAMES,
    ENTRY_PATH_CLASS_TARGET,
    ENTRY_PATH_V1_FEATURE_COLUMNS,
    ENTRY_PATH_PATH_REG_TARGETS,
    ENTRY_PATH_RET_TARGETS,
    ENTRY_PATH_TARGET,
    build_entry_path_model,
    build_entry_path_export_frame,
    split_entry_path_features,
    split_entry_path_targets,
)
from ML.lib_pic_feature_profiles import build_lib_pic_feature_profile


def _fractal(seed: int) -> str:
    fields = [
        1_700_000_000 + seed,
        100.0 + seed,
        1 if seed % 2 == 0 else -1,
        2.0 + seed,
        3.0 + seed,
        1,
        seed % 3,
        0.5 + seed,
        4.0 + seed,
        2,
        1.2 + seed,
        0.1 + seed,
        0.2 + seed,
        0.3 + seed,
        0.4 + seed,
        0.5 + seed,
        0.6 + seed,
        0.7 + seed,
        0.8 + seed,
        0.9 + seed,
        1.0 + seed,
        1.5 + seed,
    ]
    return ':'.join(str(value) for value in fields)


def test_entry_path_target_contract():
    assert ENTRY_PATH_TARGET == 'entry_path_v1'
    assert ENTRY_PATH_ALLOWED_SEQUENCE_LENGTHS == (20, 50, 100)
    assert ENTRY_PATH_MODEL_NAMES == ('transformer', 'entry_path_dual_stream')
    assert 'entry_path_v1' in ENTRY_PATH_FEATURE_PROFILES
    assert 'baseline_clean' in ENTRY_PATH_FEATURE_PROFILES
    assert ENTRY_PATH_RET_TARGETS == ['ret_6_dir_atr', 'ret_12_dir_atr', 'ret_24_dir_atr']
    assert ENTRY_PATH_PATH_REG_TARGETS == [
        'fav_6_atr',
        'adv_6_atr',
        'fav_12_atr',
        'adv_12_atr',
        'fav_24_atr',
        'adv_24_atr',
    ]
    assert ENTRY_PATH_CLASS_TARGET == 'path_6_class'


def test_entry_path_task_exposes_frequency_feature_columns():
    expected = {
        'session_hour',
        'weekday',
        'range_atr_6',
        'body_atr_3',
        'ret_dir_atr_lag1',
        'vol_regime_24',
    }
    assert expected.issubset(set(ENTRY_PATH_V1_FEATURE_COLUMNS))


def test_entry_path_task_exposes_feature_bank_columns():
    expected = {
        'row_strong_share_w5',
        'row_break_share_w10',
        'row_direction_balance_w20',
        'row_back_mean_w50',
        'row_impulse_mean_w100',
    }
    assert expected.issubset(set(ENTRY_PATH_V1_FEATURE_COLUMNS))


def test_split_entry_path_targets_returns_reg_and_cls_parts():
    frame = pd.DataFrame([
        {
            'ret_6_dir_atr': 0.1,
            'ret_12_dir_atr': 0.2,
            'ret_24_dir_atr': 0.3,
            'fav_6_atr': 0.4,
            'adv_6_atr': 0.5,
            'fav_12_atr': 0.6,
            'adv_12_atr': 0.7,
            'fav_24_atr': 0.8,
            'adv_24_atr': 0.9,
            'path_6_class': -1,
        }
    ])

    y_reg, y_cls = split_entry_path_targets(frame)

    assert y_reg.shape == (1, 9)
    assert y_cls.tolist() == [0]


def test_split_entry_path_features_is_numeric_and_zero_fills_missing_columns():
    frame = pd.DataFrame([
        {
            'session_hour': '7',
            'weekday': '2',
            'range_atr_6': '1.5',
            'body_atr_3': None,
            'ret_dir_atr_lag1': 'nan',
            'vol_regime_24': '3',
        }
    ])

    features = split_entry_path_features(frame)

    assert features.shape == (1, len(ENTRY_PATH_V1_FEATURE_COLUMNS))
    assert features.dtype == np.float32
    assert features[0, 0] == 7.0
    assert features[0, 1] == 2.0
    assert features[0, 2] == 1.5
    assert features[0, 3] == 0.0
    assert features[0, 4] == 0.0
    assert features[0, 5] == 3.0
    assert np.all(features[0, 6:] == 0.0)


def test_split_entry_path_features_supports_clean_lib_pic_profile():
    frame = pd.DataFrame(
        {
            'ATR': [1.0, 1.1],
            'session_hour': [7, 8],
            'weekday': [2, 3],
            **{
                f'fractal{fractal_idx}': [_fractal(fractal_idx), _fractal(fractal_idx + 1)]
                for fractal_idx in range(5)
            },
        }
    )

    expected = build_lib_pic_feature_profile(frame, profile='baseline_clean', seq_len=5)
    features = split_entry_path_features(frame, feature_profile='baseline_clean', seq_len=5)

    assert features.shape == expected.shape
    assert features.dtype == np.float32
    assert np.allclose(features, expected.to_numpy(dtype=np.float32))


def test_split_entry_path_targets_rejects_unknown_class():
    frame = pd.DataFrame([
        {
            'ret_6_dir_atr': 0.1,
            'ret_12_dir_atr': 0.2,
            'ret_24_dir_atr': 0.3,
            'fav_6_atr': 0.4,
            'adv_6_atr': 0.5,
            'fav_12_atr': 0.6,
            'adv_12_atr': 0.7,
            'fav_24_atr': 0.8,
            'adv_24_atr': 0.9,
            'path_6_class': 2,
        }
    ])

    with pytest.raises(ValueError, match='Unsupported path_6_class values'):
        split_entry_path_targets(frame)


def test_build_entry_path_model_supports_transformer_and_dual_stream():
    transformer = build_entry_path_model('transformer', {'input_features': 20, 'engineered_feature_dim': 6})
    dual_stream = build_entry_path_model('entry_path_dual_stream', {'input_features': 20, 'engineered_feature_dim': 6})

    assert transformer.__class__.__name__ == 'EntryPathTransformer'
    assert dual_stream.__class__.__name__ == 'EntryPathDualStreamTransformer'


def test_build_entry_path_model_uses_canonical_engineered_width_by_default():
    transformer = build_entry_path_model('transformer', {'input_features': 20})
    dual_stream = build_entry_path_model('entry_path_dual_stream', {'input_features': 20})

    assert transformer.entry_path_projection[0].normalized_shape[0] == len(ENTRY_PATH_V1_FEATURE_COLUMNS) + 64
    assert dual_stream.engineered_encoder[0].normalized_shape[0] == len(ENTRY_PATH_V1_FEATURE_COLUMNS)


def test_build_entry_path_export_frame_contains_core_columns():
    frame = build_entry_path_export_frame(
        times=np.array(['2025-01-01T00:00:00'], dtype=object),
        signals=np.array([1], dtype=np.int64),
        pred_ret=np.array([[0.1, 0.2, 0.3]], dtype=np.float32),
        pred_path_reg=np.array([[1.1, 0.4, 1.2, 0.5, 1.3, 0.6]], dtype=np.float32),
        pred_path_cls=np.array([[0.1, 0.2, 0.7]], dtype=np.float32),
        true_reg=np.array([[0.9, 0.8, 0.7, 1.9, 1.8, 1.7, 2.9, 2.8, 2.7]], dtype=np.float32),
        true_cls=np.array([2], dtype=np.int64),
    )

    assert 'pred_ret_24_dir_atr' in frame.columns
    assert 'pred_fav_24_atr' in frame.columns
    assert 'pred_path_6_class' in frame.columns
    assert frame.at[0, 'pred_path_6_class'] == 1


def test_entry_path_dataset_returns_mixed_tensors():
    dataset = EntryPathDataset(
        X=np.zeros((1, 4, 3), dtype=np.float32),
        engineered=np.zeros((1, 6), dtype=np.float32),
        y_reg=np.zeros((1, 9), dtype=np.float32),
        y_cls=np.array([2], dtype=np.int64),
        mask=np.array([[True, True, False, False]]),
        signal=np.array([1], dtype=np.int64),
    )

    X_item, engineered_item, y_reg_item, y_cls_item, mask_item, signal_item = dataset[0]

    assert X_item.shape == (4, 3)
    assert engineered_item.shape == (6,)
    assert y_reg_item.shape == (9,)
    assert y_cls_item.dtype == torch.int64
    assert mask_item.dtype == torch.bool
    assert signal_item.dtype == torch.int64
    assert signal_item.item() == 1
