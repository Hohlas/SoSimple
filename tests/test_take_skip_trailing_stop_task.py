import numpy as np
import pandas as pd
import pytest

from ML.take_skip_trailing_stop_task import (
    TAKE_SKIP_TRAILING_STOP_COLUMNS,
    TAKE_SKIP_TRAILING_STOP_TARGET,
    TAKE_SKIP_TRUE_PNL_COLUMNS,
    build_take_skip_export_frame,
    compute_take_skip_metrics,
    split_take_skip_targets,
)


def test_take_skip_columns_match_expanded_trailing_grid():
    assert TAKE_SKIP_TRAILING_STOP_TARGET == 'take_skip_trailing_stop_v1'
    assert TAKE_SKIP_TRAILING_STOP_COLUMNS == [
        'take_48_x2',
        'take_48_x3',
        'take_48_x4',
        'take_48_x6',
        'take_48_x8',
    ]
    assert TAKE_SKIP_TRUE_PNL_COLUMNS == [
        'trail_48_pnl_atr_x2',
        'trail_48_pnl_atr_x3',
        'trail_48_pnl_atr_x4',
        'trail_48_pnl_atr_x6',
        'trail_48_pnl_atr_x8',
    ]


def test_split_take_skip_targets_thresholds_pnl_at_half_atr():
    frame = pd.DataFrame(
        {
            'trail_48_pnl_atr_x2': [0.49, 0.50, 1.20],
            'trail_48_pnl_atr_x3': [-0.10, 0.50, 0.40],
            'trail_48_pnl_atr_x4': [0.00, 0.51, 0.49],
            'trail_48_pnl_atr_x6': [0.50, -2.00, 0.50],
            'trail_48_pnl_atr_x8': [1.00, 0.20, 0.50],
        }
    )

    y = split_take_skip_targets(frame)

    assert y.dtype == np.float32
    assert y.tolist() == [
        [0.0, 0.0, 0.0, 1.0, 1.0],
        [1.0, 1.0, 1.0, 0.0, 0.0],
        [1.0, 0.0, 0.0, 1.0, 1.0],
    ]


def test_split_take_skip_targets_fails_on_missing_columns():
    frame = pd.DataFrame({'trail_48_pnl_atr_x2': [1.0]})

    with pytest.raises(ValueError, match='missing take/skip source columns'):
        split_take_skip_targets(frame)


def test_build_take_skip_export_frame_includes_probabilities_and_true_pnl():
    export = build_take_skip_export_frame(
        times=['2026.01.01 00:00', '2026.01.02 00:00'],
        signals=[1, -1],
        pred_prob=np.array(
            [
                [0.1, 0.2, 0.3, 0.4, 0.5],
                [0.6, 0.7, 0.8, 0.9, 1.0],
            ],
            dtype=np.float32,
        ),
        true_label=np.array(
            [
                [0, 0, 0, 0, 1],
                [1, 1, 1, 1, 1],
            ],
            dtype=np.float32,
        ),
        true_pnl=np.array(
            [
                [-1.0, -0.5, 0.0, 0.4, 0.5],
                [0.6, 0.7, 0.8, 0.9, 1.0],
            ],
            dtype=np.float32,
        ),
    )

    assert list(export.columns) == [
        'time',
        'signal',
        'pred_take_48_x2',
        'pred_take_48_x3',
        'pred_take_48_x4',
        'pred_take_48_x6',
        'pred_take_48_x8',
        'true_take_48_x2',
        'true_take_48_x3',
        'true_take_48_x4',
        'true_take_48_x6',
        'true_take_48_x8',
        'true_trail_48_pnl_atr_x2',
        'true_trail_48_pnl_atr_x3',
        'true_trail_48_pnl_atr_x4',
        'true_trail_48_pnl_atr_x6',
        'true_trail_48_pnl_atr_x8',
    ]
    assert export.loc[1, 'pred_take_48_x8'] == pytest.approx(1.0)
    assert export.loc[0, 'true_trail_48_pnl_atr_x2'] == pytest.approx(-1.0)


def test_build_take_skip_export_frame_validates_shapes():
    with pytest.raises(ValueError, match='pred_prob must have shape'):
        build_take_skip_export_frame(
            times=['2026.01.01 00:00'],
            signals=[1],
            pred_prob=np.array([[0.1, 0.2, 0.3, 0.4]], dtype=np.float32),
        )

    with pytest.raises(ValueError, match='signals must have the same length as times'):
        build_take_skip_export_frame(
            times=['2026.01.01 00:00'],
            signals=[1, -1],
            pred_prob=np.array([[0.1, 0.2, 0.3, 0.4, 0.5]], dtype=np.float32),
        )

    with pytest.raises(ValueError, match='pred_prob must have the same row count as times'):
        build_take_skip_export_frame(
            times=['2026.01.01 00:00', '2026.01.01 01:00'],
            signals=[1, -1],
            pred_prob=np.array([[0.1, 0.2, 0.3, 0.4, 0.5]], dtype=np.float32),
        )

    with pytest.raises(ValueError, match='true_label shape'):
        build_take_skip_export_frame(
            times=['2026.01.01 00:00'],
            signals=[1],
            pred_prob=np.array([[0.1, 0.2, 0.3, 0.4, 0.5]], dtype=np.float32),
            true_label=np.array([[0, 1, 0, 1]], dtype=np.float32),
        )

    with pytest.raises(ValueError, match='true_pnl shape'):
        build_take_skip_export_frame(
            times=['2026.01.01 00:00'],
            signals=[1],
            pred_prob=np.array([[0.1, 0.2, 0.3, 0.4, 0.5]], dtype=np.float32),
            true_pnl=np.array([[0, 1, 0, 1]], dtype=np.float32),
        )


def test_compute_take_skip_metrics_reports_positive_rates():
    y_true = np.array([[0, 1, 1, 0, 1], [1, 1, 0, 0, 0]], dtype=np.float32)
    y_prob = np.array([[0.2, 0.8, 0.7, 0.1, 0.9], [0.9, 0.6, 0.2, 0.3, 0.4]], dtype=np.float32)

    metrics = compute_take_skip_metrics(y_true, y_prob)

    assert metrics['positive_rate_take_48_x2'] == pytest.approx(0.5)
    assert metrics['positive_rate_take_48_x6'] == pytest.approx(0.0)
    assert metrics['brier_take_48_x3'] == pytest.approx(0.1)
    assert metrics['bce'] == pytest.approx(0.2720513343811035)
    assert 'brier_take_48_x3' in metrics


def test_compute_take_skip_metrics_rejects_invalid_y_true_values():
    with pytest.raises(ValueError, match='y_true must contain only 0/1 labels'):
        compute_take_skip_metrics(
            np.array([[0, 1, 0, 1, 0.5]], dtype=np.float32),
            np.array([[0.2, 0.8, 0.2, 0.8, 0.2]], dtype=np.float32),
        )


def test_compute_take_skip_metrics_rejects_invalid_y_prob_values():
    with pytest.raises(ValueError, match='y_prob must contain probabilities in \\[0, 1\\]'):
        compute_take_skip_metrics(
            np.array([[0, 1, 0, 1, 0]], dtype=np.float32),
            np.array([[0.2, -0.1, 0.2, 0.8, 0.2]], dtype=np.float32),
        )

    with pytest.raises(ValueError, match='y_prob must contain probabilities in \\[0, 1\\]'):
        compute_take_skip_metrics(
            np.array([[0, 1, 0, 1, 0]], dtype=np.float32),
            np.array([[0.2, 1.1, 0.2, 0.8, 0.2]], dtype=np.float32),
        )


def test_compute_take_skip_metrics_rejects_non_finite_inputs():
    with pytest.raises(ValueError, match='non-finite'):
        compute_take_skip_metrics(
            np.array([[0, 1, np.nan, 1, 0]], dtype=np.float32),
            np.array([[0.2, 0.8, 0.2, 0.8, 0.2]], dtype=np.float32),
        )

    with pytest.raises(ValueError, match='non-finite'):
        compute_take_skip_metrics(
            np.array([[0, 1, 0, 1, 0]], dtype=np.float32),
            np.array([[0.2, np.inf, 0.2, 0.8, 0.2]], dtype=np.float32),
        )
