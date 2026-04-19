# =============================================================================
# Файл: lib_pic_geometry_feature_bank.py
# Назначение: Производные признаки геометрии уровней из текущих fractal-полей.
# Обновлён: 2026-04-19
# Входные данные:
#   - DataFrame с колонками fractal0..fractal99
# Выходные данные:
#   - DataFrame с добавленными geometry feature columns
# Использование:
#   from ML.lib_pic_geometry_feature_bank import build_lib_pic_geometry_feature_bank
# Примечания:
#   - Не использует Up/Dn поля, чтобы не добавлять будущий ход цены во входы.
# =============================================================================

from __future__ import annotations

import numpy as np
import pandas as pd


GEOMETRY_WINDOWS = (5, 10, 20, 50, 100)
GEOMETRY_FEATURE_PREFIX = 'pic_geom'
EPS = 1e-6

FIELD_FRONT = 3
FIELD_BACK = 4
FIELD_REVERSE = 7
FIELD_FRACTAL_ATR = 21


def _geometry_columns(window: int) -> list[str]:
    base = [
        'front_mean',
        'front_std',
        'front_max',
        'front_recent',
        'back_mean',
        'back_std',
        'back_max',
        'back_recent',
        'reverse_mean',
        'reverse_max',
        'reverse_recent',
        'ratio_mean',
        'ratio_std',
        'ratio_recent',
        'balance_mean',
        'balance_std',
        'balance_recent',
        'front_share_mean',
        'front_dominant_share',
        'balanced_share',
        'size_mean',
        'size_std',
        'size_recent',
        'atr_mean',
        'atr_std',
        'atr_recent',
        'front_recent_minus_mean',
        'back_recent_minus_mean',
        'size_recent_minus_mean',
    ]
    return [f'{GEOMETRY_FEATURE_PREFIX}_{name}_w{window}' for name in base]


GEOMETRY_FEATURE_COLUMNS = [
    column
    for window in GEOMETRY_WINDOWS
    for column in _geometry_columns(window)
]


def _parse_float(parts: list[str], index: int) -> float:
    try:
        value = float(parts[index])
    except (IndexError, TypeError, ValueError):
        return 0.0
    if not np.isfinite(value):
        return 0.0
    return value


def _parse_geometry(raw: object) -> tuple[float, float, float, float] | None:
    if pd.isna(raw):
        return None
    text = str(raw).strip()
    if not text:
        return None
    parts = text.split(':')
    if len(parts) < 11:
        return None
    front = _parse_float(parts, FIELD_FRONT)
    back = _parse_float(parts, FIELD_BACK)
    reverse = _parse_float(parts, FIELD_REVERSE)
    fractal_atr = _parse_float(parts, FIELD_FRACTAL_ATR) if len(parts) > FIELD_FRACTAL_ATR else 0.0
    return front, back, reverse, fractal_atr


def _safe_std(values: np.ndarray) -> float:
    if values.size == 0:
        return 0.0
    return float(np.std(values))


def _window_features(parsed: list[tuple[float, float, float, float]], window: int) -> dict[str, float]:
    chunk = parsed[:window]
    columns = _geometry_columns(window)
    if not chunk:
        return {column: 0.0 for column in columns}

    arr = np.asarray(chunk, dtype=np.float64)
    front = arr[:, 0]
    back = arr[:, 1]
    reverse = arr[:, 2]
    fractal_atr = arr[:, 3]

    ratio = front / (back + EPS)
    balance = (front - back) / (front + back + EPS)
    front_share = front / (front + back + EPS)
    size = front + back

    recent_front = float(front[0])
    recent_back = float(back[0])
    recent_size = float(size[0])

    return {
        f'{GEOMETRY_FEATURE_PREFIX}_front_mean_w{window}': float(np.mean(front)),
        f'{GEOMETRY_FEATURE_PREFIX}_front_std_w{window}': _safe_std(front),
        f'{GEOMETRY_FEATURE_PREFIX}_front_max_w{window}': float(np.max(front)),
        f'{GEOMETRY_FEATURE_PREFIX}_front_recent_w{window}': recent_front,
        f'{GEOMETRY_FEATURE_PREFIX}_back_mean_w{window}': float(np.mean(back)),
        f'{GEOMETRY_FEATURE_PREFIX}_back_std_w{window}': _safe_std(back),
        f'{GEOMETRY_FEATURE_PREFIX}_back_max_w{window}': float(np.max(back)),
        f'{GEOMETRY_FEATURE_PREFIX}_back_recent_w{window}': recent_back,
        f'{GEOMETRY_FEATURE_PREFIX}_reverse_mean_w{window}': float(np.mean(reverse)),
        f'{GEOMETRY_FEATURE_PREFIX}_reverse_max_w{window}': float(np.max(reverse)),
        f'{GEOMETRY_FEATURE_PREFIX}_reverse_recent_w{window}': float(reverse[0]),
        f'{GEOMETRY_FEATURE_PREFIX}_ratio_mean_w{window}': float(np.mean(ratio)),
        f'{GEOMETRY_FEATURE_PREFIX}_ratio_std_w{window}': _safe_std(ratio),
        f'{GEOMETRY_FEATURE_PREFIX}_ratio_recent_w{window}': float(ratio[0]),
        f'{GEOMETRY_FEATURE_PREFIX}_balance_mean_w{window}': float(np.mean(balance)),
        f'{GEOMETRY_FEATURE_PREFIX}_balance_std_w{window}': _safe_std(balance),
        f'{GEOMETRY_FEATURE_PREFIX}_balance_recent_w{window}': float(balance[0]),
        f'{GEOMETRY_FEATURE_PREFIX}_front_share_mean_w{window}': float(np.mean(front_share)),
        f'{GEOMETRY_FEATURE_PREFIX}_front_dominant_share_w{window}': float(np.mean(front > back)),
        f'{GEOMETRY_FEATURE_PREFIX}_balanced_share_w{window}': float(np.mean(np.abs(balance) <= 0.20)),
        f'{GEOMETRY_FEATURE_PREFIX}_size_mean_w{window}': float(np.mean(size)),
        f'{GEOMETRY_FEATURE_PREFIX}_size_std_w{window}': _safe_std(size),
        f'{GEOMETRY_FEATURE_PREFIX}_size_recent_w{window}': recent_size,
        f'{GEOMETRY_FEATURE_PREFIX}_atr_mean_w{window}': float(np.mean(fractal_atr)),
        f'{GEOMETRY_FEATURE_PREFIX}_atr_std_w{window}': _safe_std(fractal_atr),
        f'{GEOMETRY_FEATURE_PREFIX}_atr_recent_w{window}': float(fractal_atr[0]),
        f'{GEOMETRY_FEATURE_PREFIX}_front_recent_minus_mean_w{window}': recent_front - float(np.mean(front)),
        f'{GEOMETRY_FEATURE_PREFIX}_back_recent_minus_mean_w{window}': recent_back - float(np.mean(back)),
        f'{GEOMETRY_FEATURE_PREFIX}_size_recent_minus_mean_w{window}': recent_size - float(np.mean(size)),
    }


def build_lib_pic_geometry_feature_bank(
    frame: pd.DataFrame,
    windows: tuple[int, ...] = GEOMETRY_WINDOWS,
) -> pd.DataFrame:
    """Добавляет производные признаки геометрии `lib_PIC` к DataFrame.

    Аргументы:
        frame: DataFrame с колонками `fractal0..fractalN`.
        windows: Окна по свежим фракталам. `fractal0` считается самым свежим.

    Возвращает:
        Копия исходного DataFrame с добавленными geometry columns.
    """
    if not windows:
        raise ValueError('windows must not be empty')
    invalid_windows = [window for window in windows if window <= 0]
    if invalid_windows:
        raise ValueError(f'windows must be positive, got {invalid_windows}')

    out = frame.copy()
    fractal_cols = sorted(
        [column for column in out.columns if column.startswith('fractal')],
        key=lambda column: int(column.replace('fractal', '')),
    )
    max_window = max(windows)
    fractal_cols = fractal_cols[:max_window]

    rows: list[dict[str, float]] = []
    for _, row in out[fractal_cols].iterrows() if fractal_cols else []:
        parsed: list[tuple[float, float, float, float]] = []
        for column in fractal_cols:
            item = _parse_geometry(row[column])
            if item is not None:
                parsed.append(item)
        features: dict[str, float] = {}
        for window in windows:
            features.update(_window_features(parsed, window))
        rows.append(features)

    expected_columns = [column for window in windows for column in _geometry_columns(window)]
    if rows:
        bank = pd.DataFrame(rows, index=out.index, columns=expected_columns).fillna(0.0)
    else:
        bank = pd.DataFrame(0.0, index=out.index, columns=expected_columns)

    bank = bank.replace([np.inf, -np.inf], 0.0).fillna(0.0)
    return out.join(bank)
