# =============================================================================
# Файл: tests/test_entry_path_labels.py
# Назначение: Unit-тесты для entry_path_v1 helpers из processing/label_signals.py
# Язык: Python 3.11+
# Обновлён: 2026-04-08
# Зависимости:
#   Входные данные:
#     - синтетические OHLC-окна, pandas DataFrame
#   Выходные данные:
#     - pytest assertions
# Внешние зависимости:
#   - pytest>=8.0, pandas>=2.0
# Использование:
#   ./.venv/bin/python -m pytest tests/test_entry_path_labels.py -q
# =============================================================================

import sys

import pandas as pd
import pytest

sys.path.insert(0, 'processing')
import label_signals as ls


def test_compute_entry_path_slice_buy():
    bars = pd.DataFrame([
        {'open': 100.0, 'high': 112.0, 'low': 99.0, 'close': 110.0},
        {'open': 110.0, 'high': 118.0, 'low': 107.0, 'close': 115.0},
        {'open': 115.0, 'high': 116.0, 'low': 104.0, 'close': 105.0},
    ])

    out = ls.compute_entry_path_slice(
        bars=bars,
        direction=1,
        entry_price=100.0,
        atr=10.0,
        horizon=3,
    )

    assert out['ret_dir_atr'] == pytest.approx(0.5)
    assert out['fav_atr'] == pytest.approx(1.8)
    assert out['adv_atr'] == pytest.approx(0.1)


def test_compute_entry_path_slice_sell():
    bars = pd.DataFrame([
        {'open': 100.0, 'high': 101.0, 'low': 95.0, 'close': 96.0},
        {'open': 96.0, 'high': 99.0, 'low': 90.0, 'close': 92.0},
        {'open': 92.0, 'high': 98.0, 'low': 89.0, 'close': 97.0},
    ])

    out = ls.compute_entry_path_slice(
        bars=bars,
        direction=-1,
        entry_price=100.0,
        atr=10.0,
        horizon=3,
    )

    assert out['ret_dir_atr'] == pytest.approx(0.3)
    assert out['fav_atr'] == pytest.approx(1.1)
    assert out['adv_atr'] == pytest.approx(0.1)


def test_first_touch_path_class_prefers_first_hit():
    bars = pd.DataFrame([
        {'open': 100.0, 'high': 100.8, 'low': 98.9, 'close': 99.2},
        {'open': 99.2, 'high': 101.3, 'low': 99.0, 'close': 101.1},
    ])

    out = ls.first_touch_path_class(
        bars=bars,
        direction=1,
        entry_price=100.0,
        atr=1.0,
        threshold_atr=1.0,
    )

    assert out == -1


def test_compute_entry_path_slice_invalid_direction_returns_zeroes():
    bars = pd.DataFrame([
        {'open': 100.0, 'high': 101.0, 'low': 99.0, 'close': 100.5},
    ])

    out = ls.compute_entry_path_slice(
        bars=bars,
        direction=0,
        entry_price=100.0,
        atr=10.0,
        horizon=1,
    )

    assert out == {'ret_dir_atr': 0.0, 'fav_atr': 0.0, 'adv_atr': 0.0}


def test_first_touch_path_class_returns_zero_on_timeout():
    bars = pd.DataFrame([
        {'open': 100.0, 'high': 100.6, 'low': 99.5, 'close': 100.1},
        {'open': 100.1, 'high': 100.7, 'low': 99.4, 'close': 100.0},
    ])

    out = ls.first_touch_path_class(
        bars=bars,
        direction=1,
        entry_price=100.0,
        atr=1.0,
        threshold_atr=1.0,
    )

    assert out == 0
