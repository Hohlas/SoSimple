# =============================================================================
# Файл: tests/processing/test_limit_order_barriers.py
# Назначение: Тесты для LABEL_FN()
# Язык: Python 3.11+
# Обновлён: 2026-05-27
# Зависимости: pytest, numpy, pandas
#   Входные данные: синтетические OHLC / Nero DataFrames
#   Выходные данные: assert на label values
# Внешние зависимости: processing/label_signals.py
# Использование:
#   ./.venv/bin/python -m pytest tests/processing/test_limit_order_barriers.py -v
# =============================================================================

import os
import sys
import tempfile
import numpy as np
import pandas as pd
import pytest

import sys

sys.path.insert(0, 'processing')
import label_signals as ls

LABEL_FN = ls.label_limit_order_barriers
LIMIT_NO_FILL_SENTINEL = ls.LIMIT_NO_FILL_SENTINEL
LIMIT_AMBIGUOUS_SENTINEL = ls.LIMIT_AMBIGUOUS_SENTINEL
TB_TARGET_NAMES = ls.TB_TARGET_NAMES


def _make_ohlc_csv(path, rows):
    """Создать синтетический XAUUSD_H1_OHLC.csv."""
    df = pd.DataFrame(rows, columns=['time', 'open', 'high', 'low', 'close'])
    df.to_csv(path, sep=';', index=False)
    return df


def _make_nero_df(times, atr_vals, fractal0_vals):
    """Создать DataFrame в формате Nero (до нормализации)."""
    return pd.DataFrame({
        'time': times,
        'fractal0': fractal0_vals,
        'ATR': atr_vals,
    })


def _fractal_str(price, direction):
    """Создать minimal valid fractal string (23 поля, field[0]=int timestamp)."""
    return f'123:{price}:{direction}:1.0:2.0:0:0:0.0:0.0:0:0.0:0.0:0.0:0.0:0.0:0.0:0.0:0.0:0.0:0.0:0.0:0:0'


class TestBuyLimit:
    def test_fill_and_tp(self):
        """BUY LIMIT: fill на t+1, TP на t+2."""
        with tempfile.TemporaryDirectory() as tmp:
            ohlc_path = os.path.join(tmp, 'test_ohlc.csv')
            _make_ohlc_csv(ohlc_path, [
                ('2020.01.01 00:00', 1500.0, 1502.0, 1499.0, 1500.0),
                ('2020.01.01 01:00', 1501.0, 1503.0, 1499.0, 1501.0),
                ('2020.01.01 02:00', 1501.0, 1510.0, 1500.0, 1508.0),
            ])
            df = _make_nero_df(
                times=['2020.01.01 00:00'],
                atr_vals=[2.0],
                fractal0_vals=[_fractal_str(1501.0, 0)],
            )
            result = LABEL_FN(df, ohlc_path)
            assert result.at[0, 'buy_sl3_tp3'] == 1.0
            assert result.at[0, 'buy_fill_lag'] == 0
            assert result.at[0, 'buy_sl3_tp3_pnl_r'] == 3.0

    def test_no_fill(self):
        """BUY LIMIT: цена уходит вверх, fill не происходит за 6 баров."""
        with tempfile.TemporaryDirectory() as tmp:
            ohlc_path = os.path.join(tmp, 'test_ohlc.csv')
            rows = [('2020.01.01 00:00', 1500.0, 1502.0, 1499.0, 1500.0)]
            for h in range(1, 8):
                rows.append((f'2020.01.01 {h:02d}:00', 1502.0, 1505.0, 1501.0, 1503.0))
            _make_ohlc_csv(ohlc_path, rows)
            df = _make_nero_df(
                times=['2020.01.01 00:00'],
                atr_vals=[2.0],
                fractal0_vals=[_fractal_str(1501.0, 0)],
            )
            result = LABEL_FN(df, ohlc_path)
            assert result.at[0, 'buy_sl3_tp3'] == LIMIT_NO_FILL_SENTINEL
            assert result.at[0, 'buy_fill_lag'] == -1

    def test_same_bar_fill_sl_conservative(self):
        """BUY: fill+SL в одном баре → conservative → SL, но ambiguous_flag=1."""
        with tempfile.TemporaryDirectory() as tmp:
            ohlc_path = os.path.join(tmp, 'test_ohlc.csv')
            _make_ohlc_csv(ohlc_path, [
                ('2020.01.01 00:00', 1500.0, 1502.0, 1499.0, 1500.0),
                ('2020.01.01 01:00', 1495.0, 1496.0, 1490.0, 1492.0),
            ])
            df = _make_nero_df(
                times=['2020.01.01 00:00'],
                atr_vals=[2.0],
                fractal0_vals=[_fractal_str(1501.0, 0)],
            )
            result = LABEL_FN(df, ohlc_path, mode="conservative")
            assert result.at[0, 'buy_sl3_tp3'] == 0.0  # SL
            assert result.at[0, 'ambiguous_flag_buy_sl3_tp3'] == 1  # fill+SL

    def test_same_bar_fill_sl_optimistic(self):
        """BUY: fill+SL в одном баре → optimistic → timeout (нет баров после fill)."""
        with tempfile.TemporaryDirectory() as tmp:
            ohlc_path = os.path.join(tmp, 'test_ohlc.csv')
            _make_ohlc_csv(ohlc_path, [
                ('2020.01.01 00:00', 1500.0, 1502.0, 1499.0, 1500.0),
                ('2020.01.01 01:00', 1495.0, 1496.0, 1490.0, 1492.0),
            ])
            df = _make_nero_df(
                times=['2020.01.01 00:00'],
                atr_vals=[2.0],
                fractal0_vals=[_fractal_str(1501.0, 0)],
            )
            result = LABEL_FN(df, ohlc_path, mode="optimistic")
            assert result.at[0, 'buy_sl3_tp3'] == 0.5  # fill first, no barrier bars → timeout
            assert result.at[0, 'ambiguous_flag_buy_sl3_tp3'] == 1  # flag still set

    def test_spread_harder_fill(self):
        """BUY LIMIT со spread: fill требует более низкого Bid."""
        with tempfile.TemporaryDirectory() as tmp:
            ohlc_path = os.path.join(tmp, 'test_ohlc.csv')
            _make_ohlc_csv(ohlc_path, [
                ('2020.01.01 00:00', 1500.0, 1502.0, 1499.0, 1500.0),
                ('2020.01.01 01:00', 1500.0, 1502.0, 1499.5, 1500.5),
            ])
            df = _make_nero_df(
                times=['2020.01.01 00:00'],
                atr_vals=[2.0],
                fractal0_vals=[_fractal_str(1501.0, 0)],
            )
            r05 = LABEL_FN(df, ohlc_path, spread=0.5)
            assert r05.at[0, 'buy_sl3_tp3'] != LIMIT_NO_FILL_SENTINEL  # fill

            r10 = LABEL_FN(
                _make_nero_df(['2020.01.01 00:00'], [2.0], [_fractal_str(1501.0, 0)]),
                ohlc_path, spread=1.0,
            )
            assert r10.at[0, 'buy_sl3_tp3'] == LIMIT_NO_FILL_SENTINEL  # no fill

    def test_fill_lag_values(self):
        """buy_fill_lag: 0=t+1, 1=t+2, ..."""
        with tempfile.TemporaryDirectory() as tmp:
            ohlc_path = os.path.join(tmp, 'test_ohlc.csv')
            rows = [('2020.01.01 00:00', 1500.0, 1502.0, 1499.0, 1500.0)]
            for h in range(1, 8):
                low = 1501.0 if h < 3 else 1499.0
                rows.append((f'2020.01.01 {h:02d}:00', 1501.0, 1503.0, low, 1502.0))
            _make_ohlc_csv(ohlc_path, rows)
            df = _make_nero_df(
                times=['2020.01.01 00:00'],
                atr_vals=[2.0],
                fractal0_vals=[_fractal_str(1501.0, 0)],
            )
            result = LABEL_FN(df, ohlc_path)
            assert result.at[0, 'buy_fill_lag'] == 2


class TestSellLimit:
    def test_fill_and_sl(self):
        """SELL LIMIT: fill на t+1, SL на t+2."""
        with tempfile.TemporaryDirectory() as tmp:
            ohlc_path = os.path.join(tmp, 'test_ohlc.csv')
            _make_ohlc_csv(ohlc_path, [
                ('2020.01.01 00:00', 1500.0, 1502.0, 1499.0, 1500.0),
                ('2020.01.01 01:00', 1499.0, 1502.0, 1498.0, 1500.0),
                ('2020.01.01 02:00', 1500.0, 1510.0, 1499.0, 1509.0),
            ])
            df = _make_nero_df(
                times=['2020.01.01 00:00'],
                atr_vals=[2.0],
                fractal0_vals=[_fractal_str(1499.0, 1)],
            )
            result = LABEL_FN(df, ohlc_path)
            assert result.at[0, 'sell_sl3_tp3'] == 0.0  # SL
            assert result.at[0, 'sell_fill_lag'] == 0

    def test_spread_tp_harder(self):
        """SELL со spread: TP труднее (LowBid + spread <= TP)."""
        with tempfile.TemporaryDirectory() as tmp:
            ohlc_path = os.path.join(tmp, 'test_ohlc.csv')
            _make_ohlc_csv(ohlc_path, [
                ('2020.01.01 00:00', 1500.0, 1502.0, 1499.0, 1500.0),
                ('2020.01.01 01:00', 1499.0, 1502.0, 1498.0, 1500.0),  # fill
                ('2020.01.01 02:00', 1495.0, 1496.0, 1494.0, 1495.0),  # Low=1494
                ('2020.01.01 03:00', 1495.0, 1496.0, 1494.0, 1494.0),  # Low=1494, no TP w/spread
            ])
            r0 = LABEL_FN(
                _make_nero_df(['2020.01.01 00:00'], [2.0], [_fractal_str(1499.0, 1)]),
                ohlc_path, spread=0.0,
            )
            # spread=0: bar2 LowBid=1494.0 <= TP=1494 → TP
            assert r0.at[0, 'sell_sl3_tp3'] == 1.0

            r05 = LABEL_FN(
                _make_nero_df(['2020.01.01 00:00'], [2.0], [_fractal_str(1499.0, 1)]),
                ohlc_path, spread=0.5,
            )
            # spread=0.5: bar2 LowAsk=1494.5 > TP → no TP, bar3 LowAsk=1494.5 > TP → no TP → timeout
            assert r05.at[0, 'sell_sl3_tp3'] == 0.5

    def test_spread_sl_easier(self):
        """SELL со spread: SL легче (HighBid + spread >= SL)."""
        with tempfile.TemporaryDirectory() as tmp:
            ohlc_path = os.path.join(tmp, 'test_ohlc.csv')
            _make_ohlc_csv(ohlc_path, [
                ('2020.01.01 00:00', 1500.0, 1502.0, 1499.0, 1500.0),
                ('2020.01.01 01:00', 1499.0, 1502.0, 1498.0, 1500.0),  # fill
                ('2020.01.01 02:00', 1501.0, 1505.8, 1500.0, 1505.0),  # SL check
                ('2020.01.01 03:00', 1495.0, 1496.0, 1495.0, 1495.0),  # filler bar, no TP/SL
            ])
            r0 = LABEL_FN(
                _make_nero_df(['2020.01.01 00:00'], [2.0], [_fractal_str(1499.0, 1)]),
                ohlc_path, spread=0.0,
            )
            # spread=0: High=1505.8 < SL=1506 → no SL. Later bars: filler. → timeout
            assert r0.at[0, 'sell_sl3_tp3'] == 0.5

            r05 = LABEL_FN(
                _make_nero_df(['2020.01.01 00:00'], [2.0], [_fractal_str(1499.0, 1)]),
                ohlc_path, spread=0.5,
            )
            # spread=0.5: HighAsk=1505.8+0.5=1506.3 >= 1506 → SL
            assert r05.at[0, 'sell_sl3_tp3'] == 0.0

    def test_timeout_pnl_spread(self):
        """SELL timeout PnL уменьшается на spread/ATR."""
        with tempfile.TemporaryDirectory() as tmp:
            ohlc_path = os.path.join(tmp, 'test_ohlc.csv')
            _make_ohlc_csv(ohlc_path, [
                ('2020.01.01 00:00', 1500.0, 1502.0, 1499.0, 1500.0),
                ('2020.01.01 01:00', 1499.0, 1502.0, 1498.0, 1500.0),  # fill
                ('2020.01.01 02:00', 1495.0, 1496.0, 1495.0, 1495.0),  # no TP/SL → timeout
            ])
            r0 = LABEL_FN(
                _make_nero_df(['2020.01.01 00:00'], [2.0], [_fractal_str(1499.0, 1)]),
                ohlc_path, spread=0.0,
            )
            pnl0 = r0.at[0, 'sell_sl3_tp3_pnl_r']
            # PnL0 = (1500 - 1495) / 2 = 2.5

            r05 = LABEL_FN(
                _make_nero_df(['2020.01.01 00:00'], [2.0], [_fractal_str(1499.0, 1)]),
                ohlc_path, spread=0.5,
            )
            pnl05 = r05.at[0, 'sell_sl3_tp3_pnl_r']
            # PnL05 = (1500 - (1495 + 0.5)) / 2 = (1500 - 1495.5) / 2 = 2.25

            # spread=0.5 / ATR=2.0 = 0.25
            assert abs((pnl0 - pnl05) - 0.25) < 0.01

    def test_same_bar_fill_sl_spread(self):
        """SELL: same-bar fill+SL spread-adjusted на fill bar."""
        with tempfile.TemporaryDirectory() as tmp:
            ohlc_path = os.path.join(tmp, 'test_ohlc.csv')
            _make_ohlc_csv(ohlc_path, [
                ('2020.01.01 00:00', 1500.0, 1502.0, 1499.0, 1500.0),
                # SL=1506, fill bar High=1505.8
                # spread=0: SL не задета (1505.8 < 1506)
                # spread=0.5: SL задета (1505.8+0.5=1506.3 >= 1506)
                ('2020.01.01 01:00', 1499.0, 1505.8, 1498.0, 1505.0),
            ])
            r0 = LABEL_FN(
                _make_nero_df(['2020.01.01 00:00'], [2.0], [_fractal_str(1499.0, 1)]),
                ohlc_path, spread=0.0, mode="conservative",
            )
            # No SL on fill bar → timeout (no barrier bars after)
            assert r0.at[0, 'sell_sl3_tp3'] == 0.5

            r05 = LABEL_FN(
                _make_nero_df(['2020.01.01 00:00'], [2.0], [_fractal_str(1499.0, 1)]),
                ohlc_path, spread=0.5, mode="conservative",
            )
            assert r05.at[0, 'sell_sl3_tp3'] == 0.0  # SL via spread
            assert r05.at[0, 'ambiguous_flag_sell_sl3_tp3'] == 1  # fill+SL


class TestAmbiguousFlags:
    def test_flag_set_regardless_of_mode(self):
        """Ambiguous flag пишется даже в conservative mode."""
        with tempfile.TemporaryDirectory() as tmp:
            ohlc_path = os.path.join(tmp, 'test_ohlc.csv')
            _make_ohlc_csv(ohlc_path, [
                ('2020.01.01 00:00', 1500.0, 1502.0, 1499.0, 1500.0),
                ('2020.01.01 01:00', 1495.0, 1496.0, 1490.0, 1492.0),
            ])
            df = _make_nero_df(
                times=['2020.01.01 00:00'],
                atr_vals=[2.0],
                fractal0_vals=[_fractal_str(1501.0, 0)],
            )
            for mode in ['conservative', 'optimistic', 'ambiguous']:
                result = LABEL_FN(
                    _make_nero_df(['2020.01.01 00:00'], [2.0], [_fractal_str(1501.0, 0)]),
                    ohlc_path, mode=mode,
                )
                assert result.at[0, 'ambiguous_flag_buy_sl3_tp3'] == 1, \
                    f"flag not set in {mode} mode"


class TestColumns:
    def test_all_columns_exist(self):
        """Все 12 target + fill_lag + pnl_r + amb_flag колонки."""
        with tempfile.TemporaryDirectory() as tmp:
            ohlc_path = os.path.join(tmp, 'test_ohlc.csv')
            _make_ohlc_csv(ohlc_path, [
                ('2020.01.01 00:00', 1500.0, 1502.0, 1499.0, 1500.0),
                ('2020.01.01 01:00', 1500.0, 1502.0, 1499.0, 1501.0),
            ])
            df = _make_nero_df(
                times=['2020.01.01 00:00'],
                atr_vals=[2.0],
                fractal0_vals=[_fractal_str(1501.0, 0)],
            )
            result = LABEL_FN(df, ohlc_path)
            assert 'buy_fill_lag' in result.columns
            assert 'sell_fill_lag' in result.columns
            for name in TB_TARGET_NAMES:
                assert f'ambiguous_flag_{name}' in result.columns
                assert f'{name}_pnl_r' in result.columns


class TestPnL:
    def test_buy_timeout_pnl(self):
        """BUY timeout PnL = (Close[last] - entry) / ATR."""
        with tempfile.TemporaryDirectory() as tmp:
            ohlc_path = os.path.join(tmp, 'test_ohlc.csv')
            _make_ohlc_csv(ohlc_path, [
                ('2020.01.01 00:00', 1500.0, 1502.0, 1499.0, 1500.0),
                ('2020.01.01 01:00', 1500.0, 1502.0, 1499.0, 1501.0),
                ('2020.01.01 02:00', 1501.0, 1505.0, 1500.0, 1504.0),
            ])
            df = _make_nero_df(
                times=['2020.01.01 00:00'],
                atr_vals=[2.0],
                fractal0_vals=[_fractal_str(1501.0, 0)],
            )
            result = LABEL_FN(df, ohlc_path, barrier_window=1)
            assert abs(result.at[0, 'buy_sl3_tp3_pnl_r'] - 2.0) < 0.01

    def test_skipped_row_gets_nofill_sentinel(self):
        """Skipped rows (bad fractal0, no time in OHLC) must have NO_FILL_SENTINEL."""
        with tempfile.TemporaryDirectory() as tmp:
            ohlc_path = os.path.join(tmp, 'test_ohlc.csv')
            _make_ohlc_csv(ohlc_path, [
                ('2020.01.01 00:00', 1500.0, 1502.0, 1499.0, 1500.0),
                ('2020.01.01 01:00', 1500.0, 1502.0, 1499.0, 1501.0),
            ])
            # row with empty fractal0 — must be skipped, all TB targets = NO_FILL
            df = _make_nero_df(
                times=['2020.01.01 00:00'],
                atr_vals=[2.0],
                fractal0_vals=[''],
            )
            result = LABEL_FN(df, ohlc_path)
            assert result.at[0, 'buy_fill_lag'] == -1
            assert result.at[0, 'sell_fill_lag'] == -1
            assert result.at[0, 'buy_sl3_tp3'] == LIMIT_NO_FILL_SENTINEL
            assert result.at[0, 'sell_sl3_tp3'] == LIMIT_NO_FILL_SENTINEL
