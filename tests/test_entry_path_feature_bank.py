# =============================================================================
# Файл: tests/test_entry_path_feature_bank.py
# Назначение: Контрактные тесты для entry_path feature bank.
# Язык: Python 3.10+
# Использование:
#   ./.venv/bin/python -m pytest tests/test_entry_path_feature_bank.py -q
# =============================================================================

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, '.')

from ML.entry_path_feature_bank import build_entry_path_feature_bank


def _make_fractal(
    time: int,
    price: float,
    direction: int,
    front: float,
    back: float,
    strong: int,
    brk: int,
    power: float,
    count: float,
    impulse: float,
    atr: float,
) -> str:
    return (
        f'{time}:{price:.6f}:{direction}:{front:.6f}:{back:.6f}:{strong}:{brk}:'
        f'0.0:{power:.6f}:{count:.6f}:{impulse:.6f}:0:0:0:0:0:0:0:0:0:0:{atr:.6f}'
    )


def test_build_entry_path_feature_bank_adds_window_summaries_and_ignores_invalid_entries():
    frame = pd.DataFrame([
        {
            'time': '2026.01.15 10:00',
            'fractal0': _make_fractal(1, 1.0, 1, 0.1, 1.0, 1, 0, 2.0, 1.0, 10.0, 0.5),
            'fractal1': _make_fractal(2, 1.1, 1, 0.2, 2.0, 0, 1, 4.0, 2.0, 20.0, 0.6),
            'fractal2': 'bad:entry',
            'fractal3': _make_fractal(3, 1.2, -1, 0.3, 3.0, 1, 0, 6.0, 3.0, 30.0, 0.7),
            'fractal4': '',
            'fractal5': _make_fractal(4, 1.3, -1, 0.4, 4.0, 0, 1, 8.0, 4.0, 40.0, 0.8),
            'fractal6': _make_fractal(5, 1.4, 1, 0.5, 5.0, 1, 0, 10.0, 5.0, 50.0, 0.9),
            'fractal7': _make_fractal(6, 1.5, -1, 0.6, 6.0, 0, 1, 12.0, 6.0, 60.0, 1.0),
        }
    ])

    out = build_entry_path_feature_bank(frame)

    assert out.loc[0, 'row_strong_share_w5'] == 0.6
    assert out.loc[0, 'row_break_share_w5'] == 0.4
    assert out.loc[0, 'row_direction_balance_w5'] == 0.2
    assert out.loc[0, 'row_back_mean_w5'] == 3.0
    assert out.loc[0, 'row_back_std_w5'] == np.sqrt(2.0)
    assert out.loc[0, 'row_impulse_mean_w5'] == 30.0
    assert out.loc[0, 'row_power_mean_w5'] == 6.0
    assert out.loc[0, 'row_count_mean_w5'] == 3.0

    assert out.loc[0, 'row_strong_share_w10'] == 0.5
    assert out.loc[0, 'row_break_share_w10'] == 0.5
    assert out.loc[0, 'row_direction_balance_w10'] == 0.0
    assert out.loc[0, 'row_back_mean_w10'] == 3.5
    assert out.loc[0, 'row_back_std_w10'] == np.std([1, 2, 3, 4, 5, 6])
    assert out.loc[0, 'row_impulse_mean_w10'] == 35.0
    assert out.loc[0, 'row_power_mean_w10'] == 7.0
    assert out.loc[0, 'row_count_mean_w10'] == 3.5


def test_build_entry_path_feature_bank_zero_fills_when_no_valid_fractals():
    frame = pd.DataFrame([
        {
            'time': '2026.01.15 10:00',
            'fractal0': '',
            'fractal1': None,
            'fractal2': 'not-a-fractal',
        }
    ])

    out = build_entry_path_feature_bank(frame)
    bank_cols = [column for column in out.columns if column.startswith('row_')]

    assert bank_cols
    assert np.all(out.loc[0, bank_cols].to_numpy(dtype=np.float64) == 0.0)
