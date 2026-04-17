from __future__ import annotations

import numpy as np
import pandas as pd


TAKE_SKIP_TRAILING_STOP_TARGET = 'take_skip_trailing_stop_v1'
TAKE_SKIP_THRESHOLD_ATR = 0.5
TAKE_SKIP_X_VALUES = (2, 3, 4, 6, 8)
TAKE_SKIP_TRAILING_STOP_COLUMNS = [f'take_48_x{x}' for x in TAKE_SKIP_X_VALUES]
TAKE_SKIP_TRUE_PNL_COLUMNS = [f'trail_48_pnl_atr_x{x}' for x in TAKE_SKIP_X_VALUES]


def _as_1d_vector(name: str, values, expected_rows: int | None = None) -> np.ndarray:
    array = np.asarray(values)
    if array.ndim == 1:
        result = array
    elif array.ndim == 2 and array.shape[1] == 1:
        result = array.reshape(-1)
    else:
        raise ValueError(f'{name} must have shape (n,) or (n, 1); got shape {array.shape}')

    if expected_rows is not None and len(result) != expected_rows:
        if name == 'signals':
            raise ValueError('signals must have the same length as times')
        raise ValueError(f'{name} must have the same row count as times')
    return result


def split_take_skip_targets(df: pd.DataFrame) -> np.ndarray:
    missing = [column for column in TAKE_SKIP_TRUE_PNL_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f'missing take/skip source columns: {missing}')
    pnl = df[TAKE_SKIP_TRUE_PNL_COLUMNS].to_numpy(dtype=np.float32)
    return (pnl >= TAKE_SKIP_THRESHOLD_ATR).astype(np.float32)


def build_take_skip_export_frame(
    times,
    signals,
    pred_prob: np.ndarray,
    true_label: np.ndarray | None = None,
    true_pnl: np.ndarray | None = None,
) -> pd.DataFrame:
    times = _as_1d_vector('times', times)
    signals = _as_1d_vector('signals', signals, expected_rows=len(times))
    pred_prob = np.asarray(pred_prob, dtype=np.float32)
    expected_cols = len(TAKE_SKIP_TRAILING_STOP_COLUMNS)
    if pred_prob.ndim != 2 or pred_prob.shape[1] != expected_cols:
        raise ValueError(f'pred_prob must have shape (n, {expected_cols})')
    if pred_prob.shape[0] != len(times):
        raise ValueError('pred_prob must have the same row count as times')

    frame = pd.DataFrame({'time': times, 'signal': signals})
    for idx, column in enumerate(TAKE_SKIP_TRAILING_STOP_COLUMNS):
        frame[f'pred_{column}'] = pred_prob[:, idx]

    if true_label is not None:
        true_label = np.asarray(true_label, dtype=np.float32)
        if true_label.shape != pred_prob.shape:
            raise ValueError(f'true_label shape {true_label.shape} does not match pred_prob shape {pred_prob.shape}')
        for idx, column in enumerate(TAKE_SKIP_TRAILING_STOP_COLUMNS):
            frame[f'true_{column}'] = true_label[:, idx]

    if true_pnl is not None:
        true_pnl = np.asarray(true_pnl, dtype=np.float32)
        if true_pnl.shape != pred_prob.shape:
            raise ValueError(f'true_pnl shape {true_pnl.shape} does not match pred_prob shape {pred_prob.shape}')
        for idx, column in enumerate(TAKE_SKIP_TRUE_PNL_COLUMNS):
            frame[f'true_{column}'] = true_pnl[:, idx]

    return frame


def compute_take_skip_metrics(y_true: np.ndarray, y_prob: np.ndarray) -> dict[str, float]:
    y_true = np.asarray(y_true, dtype=np.float32)
    y_prob = np.asarray(y_prob, dtype=np.float32)
    expected_cols = len(TAKE_SKIP_TRAILING_STOP_COLUMNS)
    if y_true.shape != y_prob.shape:
        raise ValueError(f'y_true shape {y_true.shape} does not match y_prob shape {y_prob.shape}')
    if y_true.ndim != 2 or y_true.shape[1] != expected_cols:
        raise ValueError(f'y_true must have shape (n, {expected_cols})')

    clipped = np.clip(y_prob, 1e-7, 1.0 - 1e-7)
    bce = -(y_true * np.log(clipped) + (1.0 - y_true) * np.log(1.0 - clipped))

    metrics: dict[str, float] = {'bce': float(np.mean(bce))}
    for idx, column in enumerate(TAKE_SKIP_TRAILING_STOP_COLUMNS):
        yt = y_true[:, idx]
        yp = y_prob[:, idx]
        metrics[f'positive_rate_{column}'] = float(np.mean(yt))
        metrics[f'brier_{column}'] = float(np.mean((yp - yt) ** 2))
    return metrics
