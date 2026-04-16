import numpy as np
import pytest

from ML.trailing_stop_target_quantile_task import (
    TRAILING_STOP_TARGET_QUANTILE_Q10_COLUMN,
    TRAILING_STOP_TARGET_QUANTILE_Q50_COLUMN,
    TRAILING_STOP_TARGET_QUANTILE_Q90_COLUMN,
    TRAILING_STOP_TARGET_QUANTILE_TARGET,
    build_trailing_stop_quantile_export_frame,
    compute_trailing_stop_quantile_metrics,
)


def test_quantile_task_constants_match_design():
    assert TRAILING_STOP_TARGET_QUANTILE_TARGET == 'trailing_stop_target_quantile_v1'
    assert TRAILING_STOP_TARGET_QUANTILE_Q10_COLUMN == 'pred_trail_48_pnl_atr_x3_q10'
    assert TRAILING_STOP_TARGET_QUANTILE_Q50_COLUMN == 'pred_trail_48_pnl_atr_x3_q50'
    assert TRAILING_STOP_TARGET_QUANTILE_Q90_COLUMN == 'pred_trail_48_pnl_atr_x3_q90'


def test_build_export_frame_orders_crossed_quantiles():
    frame = build_trailing_stop_quantile_export_frame(
        times=np.array(['2026.01.01 00:00']),
        signals=np.array([1]),
        pred_q10=np.array([[0.8]], dtype=np.float32),
        pred_q50=np.array([[0.4]], dtype=np.float32),
        pred_q90=np.array([[0.1]], dtype=np.float32),
        true=np.array([[0.3]], dtype=np.float32),
    )

    assert frame.loc[0, 'pred_trail_48_pnl_atr_x3_q10'] == 0.1
    assert frame.loc[0, 'pred_trail_48_pnl_atr_x3_q50'] == 0.4
    assert frame.loc[0, 'pred_trail_48_pnl_atr_x3_q90'] == 0.8
    assert frame.loc[0, 'true_trail_48_pnl_atr_x3'] == 0.3


def test_compute_quantile_metrics_rejects_crossed_bounds():
    with pytest.raises(ValueError, match='must satisfy q10 <= q50 <= q90'):
        compute_trailing_stop_quantile_metrics(
            true_target=np.array([0.0, 1.0], dtype=np.float32),
            pred_q10=np.array([0.5, 0.8], dtype=np.float32),
            pred_q50=np.array([0.4, 0.7], dtype=np.float32),
            pred_q90=np.array([0.3, 0.6], dtype=np.float32),
        )
