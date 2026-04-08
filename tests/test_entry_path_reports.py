import sys

import numpy as np

sys.path.insert(0, '.')

from ML.entry_path_task import build_entry_path_export_frame
from ML.entry_path_task import build_entry_path_report_markdown


def test_entry_path_export_frame_keeps_validation_columns():
    frame = build_entry_path_export_frame(
        times=np.array(['2025.01.01 00:00', '2025.01.01 01:00']),
        signals=np.array([1, -1]),
        pred_ret=np.array([[0.3, 0.2, 0.1], [-0.1, 0.0, 0.2]], dtype=np.float32),
        pred_path_reg=np.array([
            [0.4, 0.1, 0.6, 0.2, 0.8, 0.3],
            [0.2, 0.5, 0.1, 0.6, 0.3, 0.7],
        ], dtype=np.float32),
        pred_path_cls=np.array([[0.1, 0.2, 0.7], [0.6, 0.3, 0.1]], dtype=np.float32),
        true_reg=np.zeros((2, 9), dtype=np.float32),
        true_cls=np.array([2, 0], dtype=np.int64),
    )

    assert frame.columns.tolist()[:5] == [
        'time',
        'signal',
        'pred_ret_6_dir_atr',
        'pred_ret_12_dir_atr',
        'pred_ret_24_dir_atr',
    ]
    assert 'true_ret_24_dir_atr' in frame.columns
    assert 'true_path_6_class' in frame.columns


def test_entry_path_report_markdown_contains_target_sections_and_slice():
    frame = build_entry_path_export_frame(
        times=np.array([f'2025.01.01 {hour:02d}:00' for hour in range(10)]),
        signals=np.array([1] * 5 + [-1] * 5),
        pred_ret=np.array([
            [-0.2, -0.1, -0.3],
            [-0.1, -0.1, -0.2],
            [0.0, 0.1, -0.1],
            [0.1, 0.1, 0.0],
            [0.2, 0.2, 0.1],
            [0.3, 0.2, 0.2],
            [0.4, 0.3, 0.3],
            [0.5, 0.4, 0.5],
            [0.6, 0.5, 0.7],
            [0.7, 0.6, 0.9],
        ], dtype=np.float32),
        pred_path_reg=np.array([
            [0.1, 0.6, 0.2, 0.7, 0.3, 0.8],
            [0.2, 0.5, 0.3, 0.6, 0.4, 0.7],
            [0.3, 0.4, 0.4, 0.5, 0.5, 0.6],
            [0.4, 0.3, 0.5, 0.4, 0.6, 0.5],
            [0.5, 0.2, 0.6, 0.3, 0.7, 0.4],
            [0.6, 0.1, 0.7, 0.2, 0.8, 0.3],
            [0.7, 0.2, 0.8, 0.3, 0.9, 0.4],
            [0.8, 0.3, 0.9, 0.4, 1.0, 0.5],
            [0.9, 0.4, 1.0, 0.5, 1.1, 0.6],
            [1.0, 0.5, 1.1, 0.6, 1.2, 0.7],
        ], dtype=np.float32),
        pred_path_cls=np.array([
            [0.8, 0.1, 0.1],
            [0.7, 0.2, 0.1],
            [0.2, 0.7, 0.1],
            [0.2, 0.6, 0.2],
            [0.1, 0.2, 0.7],
            [0.1, 0.2, 0.7],
            [0.1, 0.7, 0.2],
            [0.7, 0.2, 0.1],
            [0.2, 0.2, 0.6],
            [0.1, 0.1, 0.8],
        ], dtype=np.float32),
        true_reg=np.array([
            [-0.3, -0.2, -0.4, 0.0, 0.7, 0.1, 0.8, 0.2, 0.9],
            [-0.2, -0.1, -0.3, 0.1, 0.6, 0.2, 0.7, 0.3, 0.8],
            [-0.1, 0.0, -0.2, 0.2, 0.5, 0.3, 0.6, 0.4, 0.7],
            [0.0, 0.1, -0.1, 0.3, 0.4, 0.4, 0.5, 0.5, 0.6],
            [0.1, 0.2, 0.0, 0.4, 0.3, 0.5, 0.4, 0.6, 0.5],
            [0.2, 0.3, 0.2, 0.5, 0.2, 0.6, 0.3, 0.7, 0.4],
            [0.3, 0.4, 0.3, 0.6, 0.3, 0.7, 0.4, 0.8, 0.5],
            [0.4, 0.5, 0.5, 0.7, 0.4, 0.8, 0.5, 0.9, 0.6],
            [0.5, 0.6, 0.8, 0.8, 0.5, 0.9, 0.6, 1.0, 0.7],
            [0.6, 0.7, 1.0, 0.9, 0.6, 1.0, 0.7, 1.1, 0.8],
        ], dtype=np.float32),
        true_cls=np.array([0, 0, 1, 1, 2, 2, 1, 0, 2, 2], dtype=np.int64),
    )

    report = build_entry_path_report_markdown(
        frame=frame,
        model_name='transformer',
        artifact_name='entry_path_test_predictions.csv',
        split_label='Test',
    )

    assert '## Return Targets' in report
    assert 'ret_24_dir_atr' in report
    assert '## Path Targets' in report
    assert 'fav_24_atr' in report
    assert '## Path Class' in report
    assert '| -1 |' in report
    assert '## Slice: pred_ret_24_dir_atr' in report
    assert 'Top 10%' in report
    assert 'Bottom 10%' in report
