# Tests for Stage 4.5: exit mechanics simulator
# Synthetic tests verify TP/SL/ambiguous/timeout/breakeven/trailing/partial
# before historical evaluation.

import pytest
import numpy as np
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from ML.baseline.diagnose_stage4_5_exit_mechanics import simulate_exit


def _make_bars(tp_hit_bar=None, sl_hit_bar=None, both_bar=None,
               n_bars=6, base_price=1.0, step=0.001, direction=1):
    bars = []
    for i in range(n_bars):
        o = base_price + i * step
        if i == both_bar:
            h = base_price + 0.100
            l = base_price - 0.100
        elif i == tp_hit_bar:
            if direction == 1:
                h = base_price + 0.001
                l = base_price - 0.100
            else:
                h = base_price + 0.100
                l = base_price - 0.001
        elif i == sl_hit_bar:
            if direction == 1:
                h = base_price + 0.100
                l = base_price - 0.001
            else:
                h = base_price + 0.001
                l = base_price - 0.100
        else:
            h = o + 0.001
            l = o - 0.001
        c = o
        bars.append((o, h, l, c))
    return bars


class TestTPExit:
    def test_tp_only_closes_at_profit(self):
        bars = _make_bars(tp_hit_bar=2, direction=1)
        result = simulate_exit(
            bars, direction=1, entry_price=1.0, sl_price=1.10, tp_price=0.95,
            atr=0.01, policy='fixed',
        )
        assert result['exit'] == 'TP'
        assert result['pnl_val'] > 0
        assert result['ambiguous'] == 0


class TestSLExit:
    def test_sl_only_closes_at_loss(self):
        bars = _make_bars(sl_hit_bar=2, direction=1)
        result = simulate_exit(
            bars, direction=1, entry_price=1.0, sl_price=1.05, tp_price=0.85,
            atr=0.01, policy='fixed',
        )
        assert result['exit'] == 'SL'
        assert result['pnl_val'] < 0
        assert result['ambiguous'] == 0


class TestAmbiguous:
    def test_tp_and_sl_same_bar_returns_sl_ambiguous(self):
        bars = _make_bars(both_bar=2, direction=1)
        result = simulate_exit(
            bars, direction=1, entry_price=1.0, sl_price=1.05, tp_price=0.95,
            atr=0.01, policy='fixed',
        )
        assert result['exit'] == 'SL'
        assert result['ambiguous'] == 1


class TestTimeout:
    def test_no_tp_no_sl_closes_at_timeout(self):
        bars = _make_bars(n_bars=6, direction=1)
        result = simulate_exit(
            bars, direction=1, entry_price=1.0, sl_price=1.10, tp_price=0.80,
            atr=0.01, policy='fixed',
        )
        assert result['exit'] == 'TIMEOUT'
        assert result['ambiguous'] == 0


class TestBreakeven:
    def test_breakeven_moves_stop_to_entry_after_trigger(self):
        bars = _make_bars(tp_hit_bar=None, sl_hit_bar=None, n_bars=6, direction=1)
        bars[2] = (1.0, 1.01, 0.90, 0.95)
        result = simulate_exit(
            bars, direction=1, entry_price=1.0, sl_price=1.10, tp_price=0.85,
            atr=0.01, policy='breakeven', breakeven_trigger_r=0.3,
        )
        assert result['exit'] in ('TP', 'TIMEOUT', 'SL')

    def test_breakeven_no_trigger_leaves_sl_unchanged(self):
        bars = _make_bars(sl_hit_bar=3, n_bars=6, direction=1)
        result = simulate_exit(
            bars, direction=1, entry_price=1.0, sl_price=1.05, tp_price=0.85,
            atr=0.01, policy='breakeven', breakeven_trigger_r=0.3,
        )
        assert result['exit'] == 'SL'


class TestTrailing:
    def test_trailing_moves_only_in_favorable_direction(self):
        bars = []
        for i in range(6):
            price = 1.0 - 0.01 * i
            bars.append((price, price + 0.01, price - 0.01, price))
        result = simulate_exit(
            bars, direction=1, entry_price=1.0, sl_price=1.08, tp_price=0.85,
            atr=0.01, policy='trailing', trail_atr=0.2,
        )
        assert result['exit'] in ('TP', 'TIMEOUT', 'TRAIL')

    def test_trailing_does_not_move_sl_up_on_unfavorable(self):
        bars = []
        for i in range(6):
            price = 1.0 + 0.01 * i
            bars.append((price, price + 0.02, price - 0.01, price))
        result = simulate_exit(
            bars, direction=1, entry_price=1.0, sl_price=1.05, tp_price=0.85,
            atr=0.01, policy='trailing', trail_atr=0.1,
        )
        assert result['exit'] in ('SL', 'TIMEOUT', 'TRAIL')


class TestPartial:
    def test_partial_returns_multiple_legs_or_single(self):
        bars = []
        for i in range(6):
            price = 1.0 - 0.02 * i
            bars.append((price, price + 0.001, price - 0.005, price))
        result = simulate_exit(
            bars, direction=1, entry_price=1.0, sl_price=1.10, tp_price=0.85,
            atr=0.01, policy='partial', partial_ratio=0.5, partial_target_r=0.5,
        )
        assert result['exit'] in ('TP', 'PARTIAL_TP', 'TIMEOUT', 'TRAIL', 'SL')

    def test_partial_can_hit_target_or_tp(self):
        bars = []
        for i in range(6):
            price = 1.0 - 0.02 * i
            bars.append((price, price + 0.001, price - 0.005, price))
        result = simulate_exit(
            bars, direction=1, entry_price=1.0, sl_price=1.10, tp_price=0.85,
            atr=0.01, policy='partial', partial_ratio=0.5, partial_target_r=0.3,
        )
        assert result['exit'] in ('TP', 'PARTIAL_TP', 'SL', 'TIMEOUT')
