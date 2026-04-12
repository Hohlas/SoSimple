import numpy as np
import pandas as pd

from ML import entry_path_quantile_task as eqt


def test_split_entry_path_quantile_targets_uses_ret24_only():
    df = pd.DataFrame({'ret_24_dir_atr': [1.5, -0.5, 0.0]})

    y = eqt.split_entry_path_quantile_targets(df)

    assert y.shape == (3, 1)
    assert np.allclose(y[:, 0], np.array([1.5, -0.5, 0.0], dtype=np.float32))


def test_pinball_loss_matches_expected_values():
    y_true = np.array([1.0, -1.0], dtype=np.float32)
    y_pred = np.array([0.0, 0.0], dtype=np.float32)

    loss_q10 = eqt.pinball_numpy(y_true, y_pred, quantile=0.1)
    loss_q90 = eqt.pinball_numpy(y_true, y_pred, quantile=0.9)

    assert np.allclose(loss_q10, np.array([0.1, 0.9], dtype=np.float32))
    assert np.allclose(loss_q90, np.array([0.9, 0.1], dtype=np.float32))


def test_build_entry_path_quantile_export_frame_includes_bounds():
    frame = eqt.build_entry_path_quantile_export_frame(
        times=np.array(['2024.01.01 00:00', '2024.01.01 01:00']),
        signals=np.array([1, -1]),
        pred_point=np.array([0.5, -0.2], dtype=np.float32),
        pred_q10=np.array([0.1, -0.8], dtype=np.float32),
        pred_q90=np.array([0.9, 0.2], dtype=np.float32),
        true_ret=np.array([0.7, -0.1], dtype=np.float32),
    )

    assert list(frame.columns) == [
        'time', 'signal',
        'pred_ret_24_point', 'pred_ret_24_q10', 'pred_ret_24_q90',
        'true_ret_24_dir_atr',
    ]
