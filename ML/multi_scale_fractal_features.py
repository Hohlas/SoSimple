from __future__ import annotations

import numpy as np


MULTI_SCALE_WINDOWS = (5, 10, 20, 50, 100)


def _window_summary(window_slice: np.ndarray) -> np.ndarray:
    mean_level = np.mean(window_slice, axis=1)
    std_level = np.std(window_slice, axis=1)
    last_minus_mean = window_slice[:, -1, :] - mean_level
    slope = (window_slice[:, -1, :] - window_slice[:, 0, :]) / float(window_slice.shape[1])
    value_range = np.max(window_slice, axis=1) - np.min(window_slice, axis=1)
    return np.concatenate([mean_level, std_level, last_minus_mean, slope, value_range], axis=1)


def build_multi_scale_fractal_features(
    fractal_tensor: np.ndarray,
    windows: tuple[int, ...] = MULTI_SCALE_WINDOWS,
) -> np.ndarray:
    tensor = np.asarray(fractal_tensor, dtype=np.float32)
    if tensor.ndim != 3:
        raise ValueError('fractal_tensor must have shape (n, seq_len, feature_dim)')
    if not windows:
        raise ValueError('windows must not be empty')

    _, seq_len, _ = tensor.shape
    summaries = []
    for window in windows:
        effective = min(int(window), seq_len)
        if effective <= 0:
            raise ValueError(f'window must be positive, got {window}')
        window_slice = tensor[:, seq_len - effective :, :]
        summaries.append(_window_summary(window_slice))

    features = np.concatenate(summaries, axis=1).astype(np.float32, copy=False)
    return np.nan_to_num(features, nan=0.0, posinf=0.0, neginf=0.0)
