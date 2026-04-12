from __future__ import annotations

import numpy as np
import pandas as pd
import torch


ENTRY_PATH_QUANTILE_TARGET = 'entry_path_quantile_v1'
ENTRY_PATH_QUANTILE_LABEL = 'ret_24_dir_atr'


def split_entry_path_quantile_targets(df: pd.DataFrame) -> np.ndarray:
    return df[[ENTRY_PATH_QUANTILE_LABEL]].values.astype(np.float32)


def pinball_numpy(y_true: np.ndarray, y_pred: np.ndarray, quantile: float) -> np.ndarray:
    err = np.asarray(y_true, dtype=np.float32) - np.asarray(y_pred, dtype=np.float32)
    q = float(quantile)
    return np.maximum(q * err, (q - 1.0) * err).astype(np.float32)


def pinball_loss_torch(y_pred: torch.Tensor, y_true: torch.Tensor, quantile: float) -> torch.Tensor:
    err = y_true - y_pred
    q = float(quantile)
    return torch.maximum(q * err, (q - 1.0) * err).mean()


def build_entry_path_quantile_export_frame(
    times: np.ndarray,
    signals: np.ndarray,
    pred_point: np.ndarray,
    pred_q10: np.ndarray,
    pred_q90: np.ndarray,
    true_ret: np.ndarray | None = None,
) -> pd.DataFrame:
    frame = pd.DataFrame({
        'time': times,
        'signal': signals,
        'pred_ret_24_point': np.asarray(pred_point, dtype=np.float32),
        'pred_ret_24_q10': np.asarray(pred_q10, dtype=np.float32),
        'pred_ret_24_q90': np.asarray(pred_q90, dtype=np.float32),
    })
    if true_ret is not None:
        frame['true_ret_24_dir_atr'] = np.asarray(true_ret, dtype=np.float32)
    return frame
