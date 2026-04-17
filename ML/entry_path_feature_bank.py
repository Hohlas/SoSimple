# =============================================================================
# Файл: ML/entry_path_feature_bank.py
# Назначение: Банк row-wise engineered features для entry_path_v1.
# Язык: Python 3.11+
# =============================================================================

from __future__ import annotations

import numpy as np
import pandas as pd

FEATURE_BANK_WINDOWS = (5, 10, 20, 50, 100)
FEATURE_BANK_METRICS = (
    'row_strong_share',
    'row_break_share',
    'row_direction_balance',
    'row_back_mean',
    'row_back_std',
    'row_impulse_mean',
    'row_power_mean',
    'row_count_mean',
)
FEATURE_BANK_COLUMNS = [
    f'{metric}_w{window}'
    for window in FEATURE_BANK_WINDOWS
    for metric in FEATURE_BANK_METRICS
]


def _parse_fractal(raw: object) -> dict[str, float] | None:
    if pd.isna(raw):
        return None
    text = str(raw)
    if not text:
        return None
    parts = text.split(':')
    if len(parts) < 22:
        return None
    try:
        return {
            'direction': float(parts[2]),
            'back': float(parts[4]),
            'strong': float(parts[5]),
            'break': float(parts[6]),
            'power': float(parts[8]),
            'count': float(parts[9]),
            'impulse': float(parts[10]),
        }
    except (TypeError, ValueError, IndexError):
        return None


def _window_stats(parsed: list[dict[str, float]], window: int) -> dict[str, float]:
    chunk = parsed[:window]
    if not chunk:
        return {
            f'row_strong_share_w{window}': 0.0,
            f'row_break_share_w{window}': 0.0,
            f'row_direction_balance_w{window}': 0.0,
            f'row_back_mean_w{window}': 0.0,
            f'row_back_std_w{window}': 0.0,
            f'row_impulse_mean_w{window}': 0.0,
            f'row_power_mean_w{window}': 0.0,
            f'row_count_mean_w{window}': 0.0,
        }

    def values(name: str) -> np.ndarray:
        return np.asarray([item[name] for item in chunk], dtype=np.float64)

    direction = values('direction')
    back = values('back')
    return {
        f'row_strong_share_w{window}': float(values('strong').mean()),
        f'row_break_share_w{window}': float(values('break').mean()),
        f'row_direction_balance_w{window}': float(direction.mean()),
        f'row_back_mean_w{window}': float(back.mean()),
        f'row_back_std_w{window}': float(back.std()),
        f'row_impulse_mean_w{window}': float(values('impulse').mean()),
        f'row_power_mean_w{window}': float(values('power').mean()),
        f'row_count_mean_w{window}': float(values('count').mean()),
    }


def build_entry_path_feature_bank(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    fractal_cols = sorted(
        [column for column in out.columns if column.startswith('fractal')],
        key=lambda column: int(column.replace('fractal', '')),
    )
    rows: list[dict[str, float]] = []

    for _, row in out[fractal_cols].iterrows() if fractal_cols else []:
        parsed: list[dict[str, float]] = []
        for column in fractal_cols:
            item = _parse_fractal(row[column])
            if item is not None:
                parsed.append(item)
        features: dict[str, float] = {}
        for window in FEATURE_BANK_WINDOWS:
            features.update(_window_stats(parsed, window))
        rows.append(features)

    if rows:
        bank = pd.DataFrame(rows, index=out.index, columns=FEATURE_BANK_COLUMNS).fillna(0.0)
    else:
        bank = pd.DataFrame(0.0, index=out.index, columns=FEATURE_BANK_COLUMNS)

    return out.join(bank)
