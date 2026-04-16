import numpy as np
import pandas as pd

from ML.trailing_stop_target_task import (
    TRAILING_STOP_TARGET,
    TRAILING_STOP_TARGET_COLUMNS,
    build_trailing_stop_export_frame,
)


def test_trailing_stop_task_constants_match_design():
    assert TRAILING_STOP_TARGET == 'trailing_stop_target_v1'
    assert TRAILING_STOP_TARGET_COLUMNS == [
        'trail_48_pnl_atr_x2',
        'trail_48_pnl_atr_x3',
        'trail_48_pnl_atr_x5',
    ]


def test_build_trailing_stop_export_frame_adds_pred_columns():
    frame = build_trailing_stop_export_frame(
        times=np.array(['2025.01.01 00:00']),
        signals=np.array([1]),
        pred=np.array([[0.1, 0.2, 0.3]], dtype=np.float32),
        true=np.array([[0.4, 0.5, 0.6]], dtype=np.float32),
    )
    assert list(frame.columns) == [
        'time',
        'signal',
        'pred_trail_48_pnl_atr_x2',
        'pred_trail_48_pnl_atr_x3',
        'pred_trail_48_pnl_atr_x5',
        'true_trail_48_pnl_atr_x2',
        'true_trail_48_pnl_atr_x3',
        'true_trail_48_pnl_atr_x5',
    ]
