from __future__ import annotations

import numpy as np
import pandas as pd


TAKE_SKIP_TRAILING_STOP_V2_TARGET = 'take_skip_trailing_stop_v2'
TAKE_SKIP_THRESHOLD_ATR_V2 = 0.5
TAKE_SKIP_V2_HORIZONS = (12, 24, 48)
TAKE_SKIP_V2_X_VALUES = (2, 4, 8)
TAKE_SKIP_V2_ROW_FEATURE_COLUMNS = [
    'predict',
    'ATR',
    'session_hour',
    'weekday',
    'range_atr_6',
    'body_atr_3',
    'ret_dir_atr_lag1',
    'vol_regime_24',
    'ret_6_dir_atr',
    'ret_12_dir_atr',
    'ret_24_dir_atr',
    'fav_3_atr',
    'adv_3_atr',
    'fav_6_atr',
    'adv_6_atr',
    'fav_12_atr',
    'adv_12_atr',
    'fav_24_atr',
    'adv_24_atr',
]

TAKE_SKIP_TRAILING_STOP_V2_COLUMNS = [
    f'take_{horizon}_x{x_value}'
    for horizon in TAKE_SKIP_V2_HORIZONS
    for x_value in TAKE_SKIP_V2_X_VALUES
]
TAKE_SKIP_TRUE_PNL_V2_COLUMNS = [
    f'trail_{horizon}_pnl_atr_x{x_value}'
    for horizon in TAKE_SKIP_V2_HORIZONS
    for x_value in TAKE_SKIP_V2_X_VALUES
]


def _as_1d_vector(name: str, values, expected_rows: int | None = None) -> np.ndarray:
    array = np.asarray(values)
    if array.ndim == 1:
        result = array
    elif array.ndim == 2 and array.shape[1] == 1:
        result = array.reshape(-1)
    else:
        raise ValueError(f'{name} must have shape (n,) or (n, 1); got shape {array.shape}')
    if expected_rows is not None and len(result) != expected_rows:
        raise ValueError(f'{name} must have the same row count as times')
    return result


def split_take_skip_v2_targets(df: pd.DataFrame) -> np.ndarray:
    missing = [column for column in TAKE_SKIP_TRUE_PNL_V2_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f'missing take/skip v2 source columns: {missing}')
    pnl = df[TAKE_SKIP_TRUE_PNL_V2_COLUMNS].to_numpy(dtype=np.float32)
    return (pnl >= TAKE_SKIP_THRESHOLD_ATR_V2).astype(np.float32)


def build_take_skip_v2_export_frame(
    times,
    signals,
    pred_prob: np.ndarray,
    true_label: np.ndarray | None = None,
    true_pnl: np.ndarray | None = None,
) -> pd.DataFrame:
    times = _as_1d_vector('times', times)
    signals = _as_1d_vector('signals', signals, expected_rows=len(times))
    pred_prob = np.asarray(pred_prob, dtype=np.float32)
    expected_cols = len(TAKE_SKIP_TRAILING_STOP_V2_COLUMNS)
    if pred_prob.ndim != 2 or pred_prob.shape[1] != expected_cols:
        raise ValueError(f'pred_prob must have shape (n, {expected_cols})')
    if pred_prob.shape[0] != len(times):
        raise ValueError('pred_prob must have the same row count as times')

    frame = pd.DataFrame({'time': times, 'signal': signals})
    for idx, column in enumerate(TAKE_SKIP_TRAILING_STOP_V2_COLUMNS):
        frame[f'pred_{column}'] = pred_prob[:, idx]

    if true_label is not None:
        true_label = np.asarray(true_label, dtype=np.float32)
        if true_label.shape != pred_prob.shape:
            raise ValueError(f'true_label shape {true_label.shape} does not match pred_prob shape {pred_prob.shape}')
        for idx, column in enumerate(TAKE_SKIP_TRAILING_STOP_V2_COLUMNS):
            frame[f'true_{column}'] = true_label[:, idx]

    if true_pnl is not None:
        true_pnl = np.asarray(true_pnl, dtype=np.float32)
        if true_pnl.shape != pred_prob.shape:
            raise ValueError(f'true_pnl shape {true_pnl.shape} does not match pred_prob shape {pred_prob.shape}')
        for idx, column in enumerate(TAKE_SKIP_TRUE_PNL_V2_COLUMNS):
            frame[f'true_{column}'] = true_pnl[:, idx]

    return frame


def _validate_metric_inputs(y_true: np.ndarray, y_prob: np.ndarray) -> None:
    expected_cols = len(TAKE_SKIP_TRAILING_STOP_V2_COLUMNS)
    if y_true.shape != y_prob.shape:
        raise ValueError(f'y_true shape {y_true.shape} does not match y_prob shape {y_prob.shape}')
    if y_true.ndim != 2 or y_true.shape[1] != expected_cols:
        raise ValueError(f'y_true must have shape (n, {expected_cols})')
    if not np.isfinite(y_true).all() or not np.isfinite(y_prob).all():
        raise ValueError('non-finite values are not allowed in y_true or y_prob')
    if not np.isin(y_true, (0.0, 1.0)).all():
        raise ValueError('y_true must contain only 0/1 labels')
    if (y_prob < 0.0).any() or (y_prob > 1.0).any():
        raise ValueError('y_prob must contain probabilities in [0, 1]')


def compute_take_skip_v2_metrics(y_true: np.ndarray, y_prob: np.ndarray) -> dict[str, float]:
    y_true = np.asarray(y_true, dtype=np.float32)
    y_prob = np.asarray(y_prob, dtype=np.float32)
    _validate_metric_inputs(y_true, y_prob)

    clipped = np.clip(y_prob, 1e-7, 1.0 - 1e-7)
    bce = -(y_true * np.log(clipped) + (1.0 - y_true) * np.log(1.0 - clipped))

    metrics: dict[str, float] = {'bce': float(np.mean(bce))}
    for idx, column in enumerate(TAKE_SKIP_TRAILING_STOP_V2_COLUMNS):
        yt = y_true[:, idx]
        yp = y_prob[:, idx]
        metrics[f'positive_rate_{column}'] = float(np.mean(yt))
        metrics[f'brier_{column}'] = float(np.mean((yp - yt) ** 2))
    return metrics
