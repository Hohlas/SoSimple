import sys

import numpy as np

sys.path.insert(0, '.')

from ML import entry_path_v1_quantile_task as task


def test_build_export_frame_includes_quantile_bounds():
    frame = task.build_entry_path_v1_quantile_export_frame(
        times=np.array(['2024.01.01 00:00']),
        signals=np.array([1]),
        pred_ret=np.array([[0.1, 0.2, 0.3]], dtype=np.float32),
        pred_path_reg=np.array([[1, 2, 3, 4, 5, 6]], dtype=np.float32),
        pred_path_cls=np.array([[0.2, 0.5, 0.3]], dtype=np.float32),
        pred_q10=np.array([[0.05]], dtype=np.float32),
        pred_q90=np.array([[0.55]], dtype=np.float32),
    )

    assert 'pred_ret_24_q10' in frame.columns
    assert 'pred_ret_24_q90' in frame.columns
    assert frame.loc[0, 'pred_ret_24_q10'] == 0.05
    assert frame.loc[0, 'pred_ret_24_q90'] == 0.55


def test_quantile_metrics_penalize_bad_coverage_and_width():
    metrics = task.compute_entry_path_v1_quantile_metrics(
        true_ret=np.array([0.0, 1.0, 2.0], dtype=np.float32),
        pred_ret24=np.array([0.0, 0.8, 1.9], dtype=np.float32),
        pred_q10=np.array([-1.0, -0.5, -0.5], dtype=np.float32),
        pred_q90=np.array([1.0, 2.0, 3.0], dtype=np.float32),
        path_reg_pearson_r=0.30,
        path_cls_f1_macro=0.40,
    )

    assert 'val_score' in metrics
    assert 'interval_coverage' in metrics
    assert 'median_interval_width' in metrics
