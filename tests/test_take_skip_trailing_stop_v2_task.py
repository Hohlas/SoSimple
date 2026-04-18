import numpy as np
import pandas as pd
import pytest

from ML.take_skip_trailing_stop_v2_task import (
    TAKE_SKIP_THRESHOLD_ATR_V2,
    TAKE_SKIP_TRAILING_STOP_V2_COLUMNS,
    TAKE_SKIP_TRAILING_STOP_V2_TARGET,
    TAKE_SKIP_TRUE_PNL_V2_COLUMNS,
    build_take_skip_v2_export_frame,
    compute_take_skip_v2_metrics,
    split_take_skip_v2_targets,
)


def test_take_skip_v2_columns_match_design():
    assert TAKE_SKIP_TRAILING_STOP_V2_TARGET == 'take_skip_trailing_stop_v2'
    assert TAKE_SKIP_THRESHOLD_ATR_V2 == 0.5
    assert TAKE_SKIP_TRAILING_STOP_V2_COLUMNS == [
        'take_12_x2', 'take_12_x4', 'take_12_x8', 'take_12_x10', 'take_12_x12',
        'take_24_x2', 'take_24_x4', 'take_24_x8', 'take_24_x10', 'take_24_x12',
        'take_48_x2', 'take_48_x4', 'take_48_x8', 'take_48_x10', 'take_48_x12',
    ]
    assert TAKE_SKIP_TRUE_PNL_V2_COLUMNS == [
        'trail_12_pnl_atr_x2', 'trail_12_pnl_atr_x4', 'trail_12_pnl_atr_x8', 'trail_12_pnl_atr_x10', 'trail_12_pnl_atr_x12',
        'trail_24_pnl_atr_x2', 'trail_24_pnl_atr_x4', 'trail_24_pnl_atr_x8', 'trail_24_pnl_atr_x10', 'trail_24_pnl_atr_x12',
        'trail_48_pnl_atr_x2', 'trail_48_pnl_atr_x4', 'trail_48_pnl_atr_x8', 'trail_48_pnl_atr_x10', 'trail_48_pnl_atr_x12',
    ]


def test_split_take_skip_v2_targets_thresholds_at_half_atr():
    frame = pd.DataFrame(
        {
            'trail_12_pnl_atr_x2': [0.49, 0.50],
            'trail_12_pnl_atr_x4': [0.50, 0.10],
            'trail_12_pnl_atr_x8': [0.0, 0.51],
            'trail_12_pnl_atr_x10': [0.49, 0.50],
            'trail_12_pnl_atr_x12': [0.50, 0.10],
            'trail_24_pnl_atr_x2': [1.0, -1.0],
            'trail_24_pnl_atr_x4': [0.40, 0.50],
            'trail_24_pnl_atr_x8': [0.80, 0.20],
            'trail_24_pnl_atr_x10': [0.0, 0.51],
            'trail_24_pnl_atr_x12': [0.49, 0.50],
            'trail_48_pnl_atr_x2': [0.49, 0.51],
            'trail_48_pnl_atr_x4': [0.50, 0.50],
            'trail_48_pnl_atr_x8': [-0.50, 3.00],
            'trail_48_pnl_atr_x10': [0.80, 0.20],
            'trail_48_pnl_atr_x12': [0.50, 0.51],
        }
    )

    y = split_take_skip_v2_targets(frame)

    assert y.dtype == np.float32
    assert y.tolist() == [
        [0.0, 1.0, 0.0, 0.0, 1.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 1.0, 1.0],
        [1.0, 0.0, 1.0, 1.0, 0.0, 0.0, 1.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 1.0],
    ]


def test_split_take_skip_v2_targets_fails_on_missing_columns():
    frame = pd.DataFrame({'trail_12_pnl_atr_x2': [1.0]})

    with pytest.raises(ValueError, match='missing take/skip v2 source columns'):
        split_take_skip_v2_targets(frame)


def test_build_take_skip_v2_export_frame_includes_probabilities_and_true_pnl():
    pred_prob = np.full((2, 15), 0.25, dtype=np.float32)
    true_label = np.zeros((2, 15), dtype=np.float32)
    true_pnl = np.arange(30, dtype=np.float32).reshape(2, 15)

    frame = build_take_skip_v2_export_frame(
        times=['2026.01.01 00:00', '2026.01.02 00:00'],
        signals=[1, -1],
        pred_prob=pred_prob,
        true_label=true_label,
        true_pnl=true_pnl,
    )

    assert frame.shape[0] == 2
    assert 'pred_take_12_x2' in frame.columns
    assert 'true_take_48_x12' in frame.columns
    assert 'true_trail_24_pnl_atr_x10' in frame.columns


def test_compute_take_skip_v2_metrics_validates_inputs():
    y_true = np.zeros((2, 15), dtype=np.float32)
    y_prob = np.ones((2, 15), dtype=np.float32) * 0.5

    metrics = compute_take_skip_v2_metrics(y_true, y_prob)

    assert metrics['bce'] > 0.0
    assert 'positive_rate_take_12_x2' in metrics
    assert 'brier_take_48_x12' in metrics

    bad_prob = y_prob.copy()
    bad_prob[0, 0] = 1.5
    with pytest.raises(ValueError, match='probabilities in \\[0, 1\\]'):
        compute_take_skip_v2_metrics(y_true, bad_prob)
