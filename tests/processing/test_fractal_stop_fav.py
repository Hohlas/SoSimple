import os
import sys
import tempfile

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, 'processing')
import label_signals as ls

LABEL_FAV = ls.label_fractal_stop_fav_targets
EVAL_TRADE = ls.evaluate_fractal_stop_trade


def _make_ohlc_csv(path, rows):
    df = pd.DataFrame(rows, columns=['time', 'open', 'high', 'low', 'close'])
    df.to_csv(path, sep=';', index=False)


def _make_nero_df(times, atr_vals, fractal0_vals):
    return pd.DataFrame({
        'time': times,
        'fractal0': fractal0_vals,
        'ATR': atr_vals,
    })


def _fractal_str(price, direction):
    return f'123:{price}:{direction}:1.0:2.0:0:0:0.0:0.0:0:0.0:0.0:0.0:0.0:0.0:0.0:0.0:0.0:0.0:0.0:0:0:0'


class TestFavTargets:
    def test_buy_fav_H6_val(self):
        """BUY: entry=1502, high reaches 1510 -> fav = 8/20 = 0.4."""
        with tempfile.TemporaryDirectory() as tmp:
            ohlc_path = os.path.join(tmp, 'ohlc.csv')
            rows = [('2020.01.01 00:00', 1500.0, 1501.0, 1499.0, 1500.0)]  # idx0
            rows.append(('2020.01.01 01:00', 1502.0, 1510.0, 1501.0, 1508.0))  # entry=1502, H=1510
            for k in range(2, 7):
                rows.append((f'2020.01.01 {k:02d}:00', 1508.0, 1509.0, 1506.0, 1507.0))
            _make_ohlc_csv(ohlc_path, rows)
            df = _make_nero_df(
                times=['2020.01.01 00:00'],
                atr_vals=[20.0],
                fractal0_vals=[_fractal_str(1500.0, -1)],  # BUY
            )
            result = LABEL_FAV(df, ohlc_path)
            assert result.at[0, 'target_buy_H6_val'] == pytest.approx(0.4, abs=0.01)
            assert pd.isna(result.at[0, 'target_sell_H6_val'])

    def test_sell_fav_H6_val(self):
        """SELL: entry=1498, low reaches 1490 -> fav = 8/20 = 0.4."""
        with tempfile.TemporaryDirectory() as tmp:
            ohlc_path = os.path.join(tmp, 'ohlc.csv')
            rows = [('2020.01.01 00:00', 1500.0, 1501.0, 1499.0, 1500.0)]
            rows.append(('2020.01.01 01:00', 1498.0, 1499.0, 1490.0, 1492.0))  # entry=1498, L=1490
            for k in range(2, 7):
                rows.append((f'2020.01.01 {k:02d}:00', 1492.0, 1495.0, 1491.0, 1493.0))
            _make_ohlc_csv(ohlc_path, rows)
            df = _make_nero_df(
                times=['2020.01.01 00:00'],
                atr_vals=[20.0],
                fractal0_vals=[_fractal_str(1500.0, 1)],  # SELL
            )
            result = LABEL_FAV(df, ohlc_path)
            assert result.at[0, 'target_sell_H6_val'] == pytest.approx(0.4, abs=0.01)
            assert pd.isna(result.at[0, 'target_buy_H6_val'])

    def test_fav_H_differ(self):
        """H12 > H6 strictly: max High is after bar 6."""
        with tempfile.TemporaryDirectory() as tmp:
            ohlc_path = os.path.join(tmp, 'ohlc.csv')
            rows = [('2020.01.01 00:00', 1500.0, 1501.0, 1499.0, 1500.0)]
            rows.append(('2020.01.01 01:00', 1502.0, 1502.0, 1501.0, 1502.0))  # entry=1502
            for k in range(2, 7):
                rows.append((f'2020.01.01 {k:02d}:00', 1502.0, 1505.0, 1501.0, 1503.0))
            rows.append(('2020.01.01 07:00', 1503.0, 1520.0, 1502.0, 1515.0))
            for k in range(8, 14):
                rows.append((f'2020.01.01 {k:02d}:00', 1510.0, 1512.0, 1508.0, 1510.0))
            _make_ohlc_csv(ohlc_path, rows)
            df = _make_nero_df(
                times=['2020.01.01 00:00'],
                atr_vals=[20.0],
                fractal0_vals=[_fractal_str(1500.0, -1)],
            )
            result = LABEL_FAV(df, ohlc_path)
            h6 = result.at[0, 'target_buy_H6_val']
            h12 = result.at[0, 'target_buy_H12_val']
            assert h12 > h6, f'H12={h12} must be strictly greater than H6={h6}'
            assert h6 == pytest.approx(0.15, abs=0.01)
            assert h12 == pytest.approx(0.9, abs=0.01)

    def test_fav_no_entry_bar(self):
        """No Open[row+1] -> NaN."""
        with tempfile.TemporaryDirectory() as tmp:
            ohlc_path = os.path.join(tmp, 'ohlc.csv')
            _make_ohlc_csv(ohlc_path, [
                ('2020.01.01 00:00', 1500.0, 1501.0, 1499.0, 1500.0),
            ])
            df = _make_nero_df(
                times=['2020.01.01 00:00'],
                atr_vals=[20.0],
                fractal0_vals=[_fractal_str(1500.0, -1)],
            )
            result = LABEL_FAV(df, ohlc_path)
            assert pd.isna(result.at[0, 'target_buy_H6_val'])
            assert pd.isna(result.at[0, 'target_sell_H6_val'])


class TestTradeEvaluator:
    ATR = 20.0

    def test_buy_tp_hit(self):
        """BUY: entry=1500, SL=1490, TP=1520. High=1525 -> TP first. PnL=(1520-1500)/20=1.0."""
        bars = [
            (1501.0, 1510.0, 1500.0, 1505.0),
            (1505.0, 1525.0, 1504.0, 1520.0),
        ]
        result = EVAL_TRADE(bars, direction=-1, entry_price=1500.0,
                            sl_price=1490.0, tp_price=1520.0, atr=self.ATR)
        assert result['exit'] == 'TP'
        assert result['pnl_val'] == pytest.approx(1.0, abs=0.01)
        assert result['ambiguous'] == 0

    def test_buy_sl_hit(self):
        """BUY: entry=1500, SL=1490. Low=1485 -> SL. PnL=-(1500-1490)/20=-0.5."""
        bars = [
            (1501.0, 1502.0, 1485.0, 1490.0),
        ]
        result = EVAL_TRADE(bars, direction=-1, entry_price=1500.0,
                            sl_price=1490.0, tp_price=1520.0, atr=self.ATR)
        assert result['exit'] == 'SL'
        assert result['pnl_val'] == pytest.approx(-0.5, abs=0.01)
        assert result['ambiguous'] == 0

    def test_buy_ambiguous(self):
        """BUY: both TP and SL in same bar -> SL first, ambiguous=1."""
        bars = [
            (1490.0, 1525.0, 1480.0, 1505.0),
        ]
        result = EVAL_TRADE(bars, direction=-1, entry_price=1500.0,
                            sl_price=1490.0, tp_price=1520.0, atr=self.ATR)
        assert result['exit'] == 'SL'
        assert result['ambiguous'] == 1

    def test_buy_timeout(self):
        """BUY: neither SL nor TP. Close[H]=1510. PnL=(1510-1500)/20=0.5."""
        bars = [
            (1501.0, 1505.0, 1495.0, 1503.0),
            (1503.0, 1508.0, 1501.0, 1510.0),
        ]
        result = EVAL_TRADE(bars, direction=-1, entry_price=1500.0,
                            sl_price=1480.0, tp_price=1530.0, atr=self.ATR)
        assert result['exit'] == 'TIMEOUT'
        assert result['pnl_val'] == pytest.approx(0.5, abs=0.01)
        assert result['ambiguous'] == 0

    def test_sell_tp_hit(self):
        """SELL: entry=1500, SL=1510, TP=1480. Low=1475 -> TP. PnL=(1500-1480)/20=1.0."""
        bars = [
            (1499.0, 1501.0, 1475.0, 1485.0),
        ]
        result = EVAL_TRADE(bars, direction=1, entry_price=1500.0,
                            sl_price=1510.0, tp_price=1480.0, atr=self.ATR)
        assert result['exit'] == 'TP'
        assert result['pnl_val'] == pytest.approx(1.0, abs=0.01)
        assert result['ambiguous'] == 0
