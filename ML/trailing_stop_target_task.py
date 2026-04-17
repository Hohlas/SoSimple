import numpy as np
import pandas as pd


TRAILING_STOP_TARGET = 'trailing_stop_target_v1'
TRAILING_STOP_TARGET_COLUMNS = [
    'trail_48_pnl_atr_x2',
    'trail_48_pnl_atr_x3',
    'trail_48_pnl_atr_x4',
    'trail_48_pnl_atr_x6',
    'trail_48_pnl_atr_x8',
]


def validate_trailing_stop_prediction_shape(pred: np.ndarray, context: str = 'pred') -> None:
    expected = len(TRAILING_STOP_TARGET_COLUMNS)
    if pred.ndim != 2 or pred.shape[1] != expected:
        raise ValueError(
            f"Trailing stop target {context} must have shape (N, {expected}); "
            f"got {pred.shape}"
        )


def split_trailing_stop_targets(df: pd.DataFrame) -> np.ndarray:
    return df[TRAILING_STOP_TARGET_COLUMNS].values.astype(np.float32)


def build_trailing_stop_export_frame(times, signals, pred, true=None) -> pd.DataFrame:
    frame = pd.DataFrame({'time': times, 'signal': signals})
    for idx, column in enumerate(TRAILING_STOP_TARGET_COLUMNS):
        frame[f'pred_{column}'] = pred[:, idx]
    if true is not None:
        for idx, column in enumerate(TRAILING_STOP_TARGET_COLUMNS):
            frame[f'true_{column}'] = true[:, idx]
    return frame
