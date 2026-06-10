# =============================================================================
# Файл: tests/processing/test_fractal_stop_breach_labels.py
# Назначение: Тесты для label_fractal_stop_breach()
# Язык: Python 3.10+
# Обновлён: 2026-06-10
# Зависимости: pytest, numpy, pandas
#   Входные данные: синтетические OHLC / Nero DataFrames
#   Выходные данные: assert на label values
# Внешние зависимости: processing/label_signals.py
# Использование:
#   source ~/git/SoSimple/.venv/bin/activate
#   python -m pytest tests/processing/test_fractal_stop_breach_labels.py -v
# =============================================================================

import os
import sys
import tempfile

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, 'processing')
import label_signals as ls

LABEL_FN = ls.label_fractal_stop_breach
BR_BREACH_COLUMNS = ls.BR_BREACH_COLUMNS


def _make_ohlc_csv(path, rows):
    """rows: list of (time, open, high, low, close)."""
    df = pd.DataFrame(rows, columns=['time', 'open', 'high', 'low', 'close'])
    df.to_csv(path, sep=';', index=False)


def _make_nero_df(times, atr_vals, fractal0_vals):
    return pd.DataFrame({
        'time': times,
        'fractal0': fractal0_vals,
        'ATR': atr_vals,
    })


def _fractal_str(price, direction):
    """23 поля: T:P:Dir:Frnt:Back:Strong:Brk:Rev:Pwr:Cnt:Imp:Up12:Dn12:Up24:Dn24:Up48:Dn48:Up3:Dn3:Up6:Dn6:FractalAtr:Shift"""
    return f'123:{price}:{direction}:1.0:2.0:0:0:0.0:0.0:0:0.0:0.0:0.0:0.0:0.0:0.0:0.0:0.0:0.0:0.0:0:0:0'


class TestBuyBreach:
    def test_buy_breach_H6_off02(self):
        """BUY: valley=1500, off=0.2*ATR=4 → stop=1496, low touches 1495 → breach=1."""
        with tempfile.TemporaryDirectory() as tmp:
            ohlc_path = os.path.join(tmp, 'ohlc.csv')
            bars = [('2020.01.01 00:00', 1502.0, 1503.0, 1501.0, 1502.0)]
            for k in range(1, 7):
                bars.append((f'2020.01.01 {k:02d}:00', 1501.0, 1502.0, 1500.0, 1501.0))
            bars[1] = ('2020.01.01 01:00', 1501.0, 1502.0, 1495.0, 1498.0)  # breach
            _make_ohlc_csv(ohlc_path, bars)
            df = _make_nero_df(
                times=['2020.01.01 00:00'],
                atr_vals=[20.0],
                fractal0_vals=[_fractal_str(1500.0, -1)],
            )
            result = LABEL_FN(df, ohlc_path)
            assert result.at[0, 'buy_stop_broken_H6_off02_flag'] == 1.0
            assert pd.isna(result.at[0, 'sell_stop_broken_H6_off02_flag'])

    def test_buy_no_breach_H6_off02(self):
        """BUY: цена остаётся выше стопа."""
        with tempfile.TemporaryDirectory() as tmp:
            ohlc_path = os.path.join(tmp, 'ohlc.csv')
            bars = [('2020.01.01 00:00', 1502.0, 1503.0, 1501.0, 1502.0)]
            for k in range(1, 7):
                bars.append((f'2020.01.01 {k:02d}:00', 1503.0, 1505.0, 1502.0, 1504.0))
            _make_ohlc_csv(ohlc_path, bars)
            df = _make_nero_df(
                times=['2020.01.01 00:00'],
                atr_vals=[20.0],
                fractal0_vals=[_fractal_str(1500.0, -1)],
            )
            result = LABEL_FN(df, ohlc_path)
            assert result.at[0, 'buy_stop_broken_H6_off02_flag'] == 0.0


class TestSellBreach:
    def test_sell_breach_H6_off02(self):
        """SELL: peak=1500, off=0.2*ATR=4 → stop=1504, high touches 1505 → breach=1."""
        with tempfile.TemporaryDirectory() as tmp:
            ohlc_path = os.path.join(tmp, 'ohlc.csv')
            bars = [('2020.01.01 00:00', 1498.0, 1499.0, 1497.0, 1498.0)]
            for k in range(1, 7):
                bars.append((f'2020.01.01 {k:02d}:00', 1499.0, 1500.0, 1498.0, 1499.0))
            bars[1] = ('2020.01.01 01:00', 1499.0, 1505.0, 1498.0, 1502.0)  # breach
            _make_ohlc_csv(ohlc_path, bars)
            df = _make_nero_df(
                times=['2020.01.01 00:00'],
                atr_vals=[20.0],
                fractal0_vals=[_fractal_str(1500.0, 1)],
            )
            result = LABEL_FN(df, ohlc_path)
            assert result.at[0, 'sell_stop_broken_H6_off02_flag'] == 1.0
            assert pd.isna(result.at[0, 'buy_stop_broken_H6_off02_flag'])

    def test_sell_offset_sensitivity(self):
        """Больший offset → дальше стоп → меньше breach."""
        with tempfile.TemporaryDirectory() as tmp:
            ohlc_path = os.path.join(tmp, 'ohlc.csv')
            bars = [('2020.01.01 00:00', 1498.0, 1499.0, 1497.0, 1498.0)]
            for k in range(1, 7):
                bars.append((f'2020.01.01 {k:02d}:00', 1499.0, 1500.0, 1498.0, 1499.0))
            bars[1] = ('2020.01.01 01:00', 1499.0, 1505.0, 1498.0, 1502.0)
            _make_ohlc_csv(ohlc_path, bars)
            df = _make_nero_df(
                times=['2020.01.01 00:00'],
                atr_vals=[20.0],
                fractal0_vals=[_fractal_str(1500.0, 1)],
            )
            result = LABEL_FN(df, ohlc_path)
            assert result.at[0, 'sell_stop_broken_H6_off02_flag'] == 1.0
            assert result.at[0, 'sell_stop_broken_H6_off05_flag'] == 0.0

    def test_longer_horizon_more_breaches(self):
        """H=12 захватывает breach на 8-м баре, H=6 — нет."""
        with tempfile.TemporaryDirectory() as tmp:
            ohlc_path = os.path.join(tmp, 'ohlc.csv')
            bars = [('2020.01.01 00:00', 1498.0, 1499.0, 1497.0, 1498.0)]
            for k in range(1, 13):
                bars.append((f'2020.01.01 {k:02d}:00', 1499.0, 1500.0, 1498.0, 1499.0))
            bars[8] = ('2020.01.01 08:00', 1499.0, 1505.0, 1498.0, 1502.0)  # breach at bar 8
            _make_ohlc_csv(ohlc_path, bars)
            df = _make_nero_df(
                times=['2020.01.01 00:00'],
                atr_vals=[20.0],
                fractal0_vals=[_fractal_str(1500.0, 1)],
            )
            result = LABEL_FN(df, ohlc_path)
            assert result.at[0, 'sell_stop_broken_H6_off02_flag'] == 0.0
            assert result.at[0, 'sell_stop_broken_H12_off02_flag'] == 1.0

    def test_insufficient_future_bars(self):
        """7 будущих баров: H6 — ok, H12 — NaN."""
        with tempfile.TemporaryDirectory() as tmp:
            ohlc_path = os.path.join(tmp, 'ohlc.csv')
            bars = [('2020.01.01 00:00', 1498.0, 1499.0, 1497.0, 1498.0)]
            for k in range(1, 8):
                bars.append((f'2020.01.01 {k:02d}:00', 1499.0, 1500.0, 1498.0, 1499.0))
            _make_ohlc_csv(ohlc_path, bars)
            df = _make_nero_df(
                times=['2020.01.01 00:00'],
                atr_vals=[20.0],
                fractal0_vals=[_fractal_str(1500.0, 1)],
            )
            result = LABEL_FN(df, ohlc_path)
            assert result.at[0, 'sell_stop_broken_H6_off02_flag'] in (0.0, 1.0)
            assert pd.isna(result.at[0, 'sell_stop_broken_H12_off02_flag'])


class TestColumns:
    def test_all_breach_columns_exist(self):
        """Все 12 колонок созданы (нужно >=13 OHLC баров для H=12)."""
        with tempfile.TemporaryDirectory() as tmp:
            ohlc_path = os.path.join(tmp, 'ohlc.csv')
            bars = [('2020.01.01 00:00', 1502.0, 1503.0, 1501.0, 1502.0)]
            for k in range(1, 13):
                bars.append((f'2020.01.01 {k:02d}:00', 1502.0, 1503.0, 1501.0, 1502.0))
            _make_ohlc_csv(ohlc_path, bars)
            df = _make_nero_df(
                times=['2020.01.01 00:00'],
                atr_vals=[20.0],
                fractal0_vals=[_fractal_str(1500.0, -1)],
            )
            result = LABEL_FN(df, ohlc_path)
            for col in BR_BREACH_COLUMNS:
                assert col in result.columns, f'{col} not found'


class TestEdgeCases:
    def test_missing_fractal0(self):
        """Пустой fractal0 → все breach колонки NaN."""
        with tempfile.TemporaryDirectory() as tmp:
            ohlc_path = os.path.join(tmp, 'ohlc.csv')
            _make_ohlc_csv(ohlc_path, [
                ('2020.01.01 00:00', 1502.0, 1503.0, 1501.0, 1502.0),
            ])
            df = _make_nero_df(
                times=['2020.01.01 00:00'],
                atr_vals=[20.0],
                fractal0_vals=[''],
            )
            result = LABEL_FN(df, ohlc_path)
            for col in BR_BREACH_COLUMNS:
                assert pd.isna(result.at[0, col]), f'{col} should be NaN'

    def test_zero_atr(self):
        """ATR=0 → все breach колонки NaN."""
        with tempfile.TemporaryDirectory() as tmp:
            ohlc_path = os.path.join(tmp, 'ohlc.csv')
            _make_ohlc_csv(ohlc_path, [
                ('2020.01.01 00:00', 1502.0, 1503.0, 1501.0, 1502.0),
            ])
            df = _make_nero_df(
                times=['2020.01.01 00:00'],
                atr_vals=[0.0],
                fractal0_vals=[_fractal_str(1500.0, -1)],
            )
            result = LABEL_FN(df, ohlc_path)
            for col in BR_BREACH_COLUMNS:
                assert pd.isna(result.at[0, col]), f'{col} should be NaN'

    def test_fractal_dir_zero(self):
        """dir=0 → нет стороны → NaN."""
        with tempfile.TemporaryDirectory() as tmp:
            ohlc_path = os.path.join(tmp, 'ohlc.csv')
            _make_ohlc_csv(ohlc_path, [
                ('2020.01.01 00:00', 1502.0, 1503.0, 1501.0, 1502.0),
            ])
            df = _make_nero_df(
                times=['2020.01.01 00:00'],
                atr_vals=[20.0],
                fractal0_vals=[_fractal_str(1500.0, 0)],
            )
            result = LABEL_FN(df, ohlc_path)
            for col in BR_BREACH_COLUMNS:
                assert pd.isna(result.at[0, col]), f'{col} should be NaN'
