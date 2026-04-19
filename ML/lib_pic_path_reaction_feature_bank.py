# =============================================================================
# Файл: lib_pic_path_reaction_feature_bank.py
# Назначение: Производные признаки исторической реакции цены Up/Dn после уровней.
# Обновлён: 2026-04-19
# Входные данные:
#   - DataFrame с колонками fractal0..fractal99
# Выходные данные:
#   - DataFrame с добавленными path-reaction feature columns
# Использование:
#   from ML.lib_pic_path_reaction_feature_bank import build_lib_pic_path_reaction_feature_bank
# Примечания:
#   - Up/Dn считаются исторической реакцией цены, накопленной в lib_PIC по уже прошедшим барам.
# =============================================================================

from __future__ import annotations

import numpy as np
import pandas as pd


PATH_REACTION_WINDOWS = (5, 10, 20, 50, 100)
PATH_REACTION_FEATURE_PREFIX = 'pic_path'
EPS = 1e-6

FIELD_DIRECTION = 2
FIELD_UP_12 = 11
FIELD_DN_12 = 12
FIELD_UP_24 = 13
FIELD_DN_24 = 14
FIELD_UP_48 = 15
FIELD_DN_48 = 16
FIELD_UP_3 = 17
FIELD_DN_3 = 18
FIELD_UP_6 = 19
FIELD_DN_6 = 20

HORIZONS = (3, 6, 12, 24, 48)
UP_INDEX = {
    3: FIELD_UP_3,
    6: FIELD_UP_6,
    12: FIELD_UP_12,
    24: FIELD_UP_24,
    48: FIELD_UP_48,
}
DN_INDEX = {
    3: FIELD_DN_3,
    6: FIELD_DN_6,
    12: FIELD_DN_12,
    24: FIELD_DN_24,
    48: FIELD_DN_48,
}


def _path_reaction_columns(window: int) -> list[str]:
    base: list[str] = []
    for horizon in HORIZONS:
        base.extend(
            [
                f'fav{horizon}_mean',
                f'fav{horizon}_max',
                f'fav{horizon}_recent',
                f'adv{horizon}_mean',
                f'adv{horizon}_max',
                f'adv{horizon}_recent',
                f'edge{horizon}_mean',
                f'edge{horizon}_recent',
                f'rr{horizon}_mean',
                f'rr{horizon}_recent',
                f'win_proxy{horizon}_share',
            ]
        )
    base.extend(
        [
            'fav_slope_3_48_mean',
            'adv_slope_3_48_mean',
            'edge_slope_3_48_mean',
            'fav_slope_12_48_mean',
            'adv_slope_12_48_mean',
            'edge_slope_12_48_mean',
        ]
    )
    return [f'{PATH_REACTION_FEATURE_PREFIX}_{name}_w{window}' for name in base]


PATH_REACTION_FEATURE_COLUMNS = [
    column
    for window in PATH_REACTION_WINDOWS
    for column in _path_reaction_columns(window)
]


def _parse_float(parts: list[str], index: int) -> float:
    try:
        value = float(parts[index])
    except (IndexError, TypeError, ValueError):
        return 0.0
    if not np.isfinite(value):
        return 0.0
    return value


def _parse_path_reaction(raw: object) -> tuple[float, dict[int, float], dict[int, float]] | None:
    if pd.isna(raw):
        return None
    text = str(raw).strip()
    if not text:
        return None
    parts = text.split(':')
    if len(parts) < 21:
        return None
    direction = _parse_float(parts, FIELD_DIRECTION)
    if direction == 0:
        direction = 1.0
    up = {horizon: _parse_float(parts, UP_INDEX[horizon]) for horizon in HORIZONS}
    dn = {horizon: _parse_float(parts, DN_INDEX[horizon]) for horizon in HORIZONS}
    return direction, up, dn


def _fav_adv_arrays(chunk: list[tuple[float, dict[int, float], dict[int, float]]]) -> tuple[dict[int, np.ndarray], dict[int, np.ndarray]]:
    fav: dict[int, list[float]] = {horizon: [] for horizon in HORIZONS}
    adv: dict[int, list[float]] = {horizon: [] for horizon in HORIZONS}
    for direction, up, dn in chunk:
        for horizon in HORIZONS:
            if direction > 0:
                fav[horizon].append(up[horizon])
                adv[horizon].append(dn[horizon])
            else:
                fav[horizon].append(dn[horizon])
                adv[horizon].append(up[horizon])
    return (
        {horizon: np.asarray(values, dtype=np.float64) for horizon, values in fav.items()},
        {horizon: np.asarray(values, dtype=np.float64) for horizon, values in adv.items()},
    )


def _window_features(parsed: list[tuple[float, dict[int, float], dict[int, float]]], window: int) -> dict[str, float]:
    chunk = parsed[:window]
    columns = _path_reaction_columns(window)
    if not chunk:
        return {column: 0.0 for column in columns}

    fav, adv = _fav_adv_arrays(chunk)
    features: dict[str, float] = {}
    for horizon in HORIZONS:
        fav_h = fav[horizon]
        adv_h = adv[horizon]
        edge = fav_h - adv_h
        rr = fav_h / (adv_h + EPS)
        win_proxy = fav_h > adv_h
        features.update(
            {
                f'{PATH_REACTION_FEATURE_PREFIX}_fav{horizon}_mean_w{window}': float(np.mean(fav_h)),
                f'{PATH_REACTION_FEATURE_PREFIX}_fav{horizon}_max_w{window}': float(np.max(fav_h)),
                f'{PATH_REACTION_FEATURE_PREFIX}_fav{horizon}_recent_w{window}': float(fav_h[0]),
                f'{PATH_REACTION_FEATURE_PREFIX}_adv{horizon}_mean_w{window}': float(np.mean(adv_h)),
                f'{PATH_REACTION_FEATURE_PREFIX}_adv{horizon}_max_w{window}': float(np.max(adv_h)),
                f'{PATH_REACTION_FEATURE_PREFIX}_adv{horizon}_recent_w{window}': float(adv_h[0]),
                f'{PATH_REACTION_FEATURE_PREFIX}_edge{horizon}_mean_w{window}': float(np.mean(edge)),
                f'{PATH_REACTION_FEATURE_PREFIX}_edge{horizon}_recent_w{window}': float(edge[0]),
                f'{PATH_REACTION_FEATURE_PREFIX}_rr{horizon}_mean_w{window}': float(np.mean(rr)),
                f'{PATH_REACTION_FEATURE_PREFIX}_rr{horizon}_recent_w{window}': float(rr[0]),
                f'{PATH_REACTION_FEATURE_PREFIX}_win_proxy{horizon}_share_w{window}': float(np.mean(win_proxy)),
            }
        )

    features.update(
        {
            f'{PATH_REACTION_FEATURE_PREFIX}_fav_slope_3_48_mean_w{window}': float(np.mean((fav[48] - fav[3]) / 45.0)),
            f'{PATH_REACTION_FEATURE_PREFIX}_adv_slope_3_48_mean_w{window}': float(np.mean((adv[48] - adv[3]) / 45.0)),
            f'{PATH_REACTION_FEATURE_PREFIX}_edge_slope_3_48_mean_w{window}': float(np.mean(((fav[48] - adv[48]) - (fav[3] - adv[3])) / 45.0)),
            f'{PATH_REACTION_FEATURE_PREFIX}_fav_slope_12_48_mean_w{window}': float(np.mean((fav[48] - fav[12]) / 36.0)),
            f'{PATH_REACTION_FEATURE_PREFIX}_adv_slope_12_48_mean_w{window}': float(np.mean((adv[48] - adv[12]) / 36.0)),
            f'{PATH_REACTION_FEATURE_PREFIX}_edge_slope_12_48_mean_w{window}': float(np.mean(((fav[48] - adv[48]) - (fav[12] - adv[12])) / 36.0)),
        }
    )
    return features


def build_lib_pic_path_reaction_feature_bank(
    frame: pd.DataFrame,
    windows: tuple[int, ...] = PATH_REACTION_WINDOWS,
) -> pd.DataFrame:
    """Добавляет признаки исторической реакции цены `Up/Dn` к DataFrame.

    Аргументы:
        frame: DataFrame с колонками `fractal0..fractalN`.
        windows: Окна по свежим фракталам. `fractal0` считается самым свежим.

    Возвращает:
        Копия исходного DataFrame с добавленными path-reaction columns.
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
    fractal_cols = fractal_cols[:max(windows)]

    rows: list[dict[str, float]] = []
    for _, row in out[fractal_cols].iterrows() if fractal_cols else []:
        parsed: list[tuple[float, dict[int, float], dict[int, float]]] = []
        for column in fractal_cols:
            item = _parse_path_reaction(row[column])
            if item is not None:
                parsed.append(item)
        features: dict[str, float] = {}
        for window in windows:
            features.update(_window_features(parsed, window))
        rows.append(features)

    expected_columns = [column for window in windows for column in _path_reaction_columns(window)]
    if rows:
        bank = pd.DataFrame(rows, index=out.index, columns=expected_columns).fillna(0.0)
    else:
        bank = pd.DataFrame(0.0, index=out.index, columns=expected_columns)

    bank = bank.replace([np.inf, -np.inf], 0.0).fillna(0.0)
    return out.join(bank)
