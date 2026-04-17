import numpy as np
import pandas as pd


TRAILING_STOP_TARGET_QUANTILE_TARGET = 'trailing_stop_target_quantile_v1'
TRAILING_STOP_TARGET_QUANTILE_BASE_COLUMN = 'trail_48_pnl_atr_x3'
TRAILING_STOP_TARGET_QUANTILE_Q10_COLUMN = 'pred_trail_48_pnl_atr_x3_q10'
TRAILING_STOP_TARGET_QUANTILE_Q50_COLUMN = 'pred_trail_48_pnl_atr_x3_q50'
TRAILING_STOP_TARGET_QUANTILE_Q90_COLUMN = 'pred_trail_48_pnl_atr_x3_q90'


def split_trailing_stop_quantile_target(df: pd.DataFrame) -> np.ndarray:
    return df[[TRAILING_STOP_TARGET_QUANTILE_BASE_COLUMN]].values.astype(np.float32)


def _as_1d_vector(name: str, array, expected_rows: int | None = None) -> np.ndarray:
    values = np.asarray(array)
    if values.ndim == 1:
        result = values
    elif values.ndim == 2 and values.shape[1] == 1:
        result = values.reshape(-1)
    else:
        shape = tuple(values.shape)
        raise ValueError(f'{name} must have shape (n, 1) or (n,); got shape {shape}')
    if expected_rows is not None and len(result) != expected_rows:
        if name == 'signals':
            raise ValueError('signals must have the same length as times')
        raise ValueError(f'{name} must have the same row count as times')
    return result


def build_trailing_stop_quantile_export_frame(
    times,
    signals,
    pred_q10,
    pred_q50,
    pred_q90,
    true=None,
) -> pd.DataFrame:
    times = _as_1d_vector('times', times)
    signals = _as_1d_vector('signals', signals, expected_rows=len(times))
    pred_q10 = _as_1d_vector('pred_q10', pred_q10, expected_rows=len(times)).astype(np.float32)
    pred_q50 = _as_1d_vector('pred_q50', pred_q50, expected_rows=len(times)).astype(np.float32)
    pred_q90 = _as_1d_vector('pred_q90', pred_q90, expected_rows=len(times)).astype(np.float32)

    frame = pd.DataFrame({'time': times, 'signal': signals})
    frame[f'{TRAILING_STOP_TARGET_QUANTILE_Q10_COLUMN}_raw'] = pred_q10
    frame[f'{TRAILING_STOP_TARGET_QUANTILE_Q50_COLUMN}_raw'] = pred_q50
    frame[f'{TRAILING_STOP_TARGET_QUANTILE_Q90_COLUMN}_raw'] = pred_q90
    ordered = np.sort(np.stack([pred_q10, pred_q50, pred_q90], axis=1), axis=1)
    frame[TRAILING_STOP_TARGET_QUANTILE_Q10_COLUMN] = ordered[:, 0]
    frame[TRAILING_STOP_TARGET_QUANTILE_Q50_COLUMN] = ordered[:, 1]
    frame[TRAILING_STOP_TARGET_QUANTILE_Q90_COLUMN] = ordered[:, 2]
    if true is not None:
        true = _as_1d_vector('true', true, expected_rows=len(times)).astype(np.float32)
        frame[f'true_{TRAILING_STOP_TARGET_QUANTILE_BASE_COLUMN}'] = true
    return frame


def _pinball(y_true: np.ndarray, y_pred: np.ndarray, q: float) -> float:
    diff = np.asarray(y_true, dtype=np.float64) - np.asarray(y_pred, dtype=np.float64)
    return float(np.mean(np.maximum(q * diff, (q - 1.0) * diff)))


def _safe_pearson(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    if len(y_true) < 2 or len(y_pred) < 2:
        return 0.0
    if np.allclose(y_true, y_true[0]) or np.allclose(y_pred, y_pred[0]):
        return 0.0
    value = np.corrcoef(y_true, y_pred)[0, 1]
    if not np.isfinite(value):
        return 0.0
    return float(value)


def compute_trailing_stop_quantile_metrics(
    true_target,
    pred_q10,
    pred_q50,
    pred_q90,
) -> dict[str, float]:
    true_target = np.asarray(true_target, dtype=np.float64).reshape(-1)
    pred_q10 = np.asarray(pred_q10, dtype=np.float64).reshape(-1)
    pred_q50 = np.asarray(pred_q50, dtype=np.float64).reshape(-1)
    pred_q90 = np.asarray(pred_q90, dtype=np.float64).reshape(-1)

    lengths = {len(true_target), len(pred_q10), len(pred_q50), len(pred_q90)}
    if len(lengths) != 1:
        raise ValueError('true_target, pred_q10, pred_q50, and pred_q90 must have the same length')
    if np.any((pred_q10 > pred_q50) | (pred_q50 > pred_q90)):
        raise ValueError('predictions must satisfy q10 <= q50 <= q90')

    lower = pred_q10
    upper = pred_q90
    coverage = float(np.mean((true_target >= lower) & (true_target <= upper)))
    width = float(np.median(upper - lower))

    return {
        'q10_pinball_loss': _pinball(true_target, pred_q10, 0.10),
        'q50_pinball_loss': _pinball(true_target, pred_q50, 0.50),
        'q90_pinball_loss': _pinball(true_target, pred_q90, 0.90),
        'q50_mae': float(np.mean(np.abs(true_target - pred_q50))),
        'q50_pearson_r': _safe_pearson(true_target, pred_q50),
        'interval_coverage': coverage,
        'median_interval_width': width,
    }
