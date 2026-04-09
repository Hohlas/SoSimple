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
    ENTRY_PATH_CLASS_TARGET,
    ENTRY_PATH_PATH_REG_TARGETS,
    ENTRY_PATH_RET_TARGETS,
    ENTRY_PATH_TARGET,
    build_entry_path_export_frame,
    split_entry_path_targets,
)


def test_entry_path_target_contract():
    assert ENTRY_PATH_TARGET == 'entry_path_v1'
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
        y_reg=np.zeros((1, 9), dtype=np.float32),
        y_cls=np.array([2], dtype=np.int64),
        mask=np.array([[True, True, False, False]]),
        signal=np.array([1], dtype=np.int64),
    )

    X_item, y_reg_item, y_cls_item, mask_item, signal_item = dataset[0]

    assert X_item.shape == (4, 3)
    assert y_reg_item.shape == (9,)
    assert y_cls_item.dtype == torch.int64
    assert mask_item.dtype == torch.bool
    assert signal_item.dtype == torch.int64
    assert signal_item.item() == 1
