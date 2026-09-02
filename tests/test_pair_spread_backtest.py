# tests/test_pair_spread_backtest.py
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_MODULE_PATH = Path(__file__).resolve().parents[1] / 'statistics' / 'pair_spread' / 'backtest.py'
_spec = importlib.util.spec_from_file_location('backtest', _MODULE_PATH)
backtest = importlib.util.module_from_spec(_spec)
sys.modules['backtest'] = backtest  # dataclass-аннотации резолвятся через sys.modules (аудит К-1)
_spec.loader.exec_module(backtest)


def _times(n):
    return pd.date_range('2023-01-02', periods=n, freq='5min').to_numpy()


def test_basic_revert_trade():
    # z: 0, 2.5 (сигнал), 2.6, 0.5, -0.1 (пересечение нуля на баре 4)
    z = np.array([0.0, 2.5, 2.6, 0.5, -0.1, 0.0])
    s = np.array([10.0, 10.0, 10.4, 10.3, 10.0, 10.0])  # исполнение по open-спреду
    trades = backtest.run_backtest(z, s, _times(6), round_trip_cost=0.1).trades
    assert len(trades) == 1
    t = trades[0]
    assert t.side == -1                    # z>=2 -> short спреда
    assert t.exit_reason == 'revert'
    # вход на open бара 2 (10.4), выход на open бара 5 (10.0): gross = -1*(10.0-10.4)=0.4
    assert abs(t.pnl_gross - 0.4) < 1e-12
    assert abs(t.pnl_net - 0.3) < 1e-12    # минус round-trip cost 0.1


def test_no_entry_in_stop_zone():
    z = np.array([0.0, 4.5, 4.6, 0.0])
    s = np.array([10.0, 10.0, 10.1, 10.0])
    result = backtest.run_backtest(z, s, _times(4), round_trip_cost=0.0)
    assert result.trades == []
    assert result.dropped_open_at_end == 0


def test_stop_exit_blocks_reentry_until_zero_cross():
    # вход на баре 1 (z=2.5), стоп на баре 2 (z=4.5), далее z всё ещё >=2 (бар 3) —
    # повторный вход запрещён; пересечение нуля на баре 4; новый сигнал на баре 5;
    # возврат и закрытие второго трейда на баре 7
    z = np.array([0.0, 2.5, 4.5, 2.6, -0.1, -2.5, -0.5, 0.1, 0.2])
    s = np.array([10.0, 10.0, 10.5, 10.6, 10.2, 9.8, 9.8, 9.9, 10.0])
    trades = backtest.run_backtest(z, s, _times(9), round_trip_cost=0.0).trades
    assert len(trades) == 2
    assert trades[0].exit_reason == 'stop'
    assert trades[1].side == 1             # z<=-2 -> long спреда (после пересечения нуля)
    assert trades[1].exit_reason == 'revert'


def test_timeout_exit():
    n = 2885
    z = np.zeros(n)
    z[1] = 2.5
    z[2:2882] = 2.1    # держится в зоне, нуля не пересекает
    s = np.full(n, 10.0)
    trades = backtest.run_backtest(z, s, _times(n), round_trip_cost=0.0).trades
    assert len(trades) == 1
    assert trades[0].exit_reason == 'timeout'
    # сигнал на баре 1, удержание 2880 баров, исполнение выхода на баре 1+2880+1
    assert trades[0].exit_i == 1 + 2880 + 1


def test_one_position_no_pyramiding():
    # завершающий бар 0.0 даёт исполнимый выход по возврату (аудит К-2.4)
    z = np.array([0.0, 2.5, 2.6, 2.7, 0.1, -0.1, 0.0])
    s = np.full(7, 10.0)
    result = backtest.run_backtest(z, s, _times(7), round_trip_cost=0.0)
    assert len(result.trades) == 1
    assert result.dropped_open_at_end == 0


def test_open_position_at_end_dropped_and_counted():
    # тот же сценарий без завершающего бара: сигнал выхода на последнем баре
    # исполнить негде — сделка не входит в trades, но подсчитана (аудит К-2.4/Q-3)
    z = np.array([0.0, 2.5, 2.6, 2.7, 0.1, -0.1])
    s = np.full(6, 10.0)
    result = backtest.run_backtest(z, s, _times(6), round_trip_cost=0.0)
    assert result.trades == []
    assert result.dropped_open_at_end == 1


def test_no_entry_on_last_bar():
    z = np.array([0.0, 2.5])   # сигнал на последнем баре — исполнять негде
    s = np.array([10.0, 10.0])
    result = backtest.run_backtest(z, s, _times(2), round_trip_cost=0.0)
    assert result.trades == []
    assert result.dropped_open_at_end == 0


def test_nights_and_swap_short_side():
    # удержание через 2 календарные ночи; z=+2.5 -> side=-1 -> swap_cost_short (аудит В-6)
    n = 3 * 288   # 3 суток по 288 баров M5
    z = np.zeros(n)
    z[1] = 2.5
    z[2:] = 0.9    # без пересечения нуля -> выход по таймауту
    times = pd.date_range('2023-01-02', periods=n, freq='5min').to_numpy()
    s = np.full(n, 10.0)
    trades = backtest.run_backtest(z, s, times, round_trip_cost=0.0,
                                   swap_cost_long=0.99, swap_cost_short=0.05,
                                   timeout_bars=2 * 288).trades
    assert len(trades) == 1
    assert trades[0].side == -1
    assert trades[0].nights == 2
    assert abs(trades[0].pnl_net - (trades[0].pnl_gross - 2 * 0.05)) < 1e-12


def test_nights_and_swap_long_side():
    # z=-2.5 -> side=+1 -> swap_cost_long (аудит В-6)
    n = 3 * 288
    z = np.zeros(n)
    z[1] = -2.5
    z[2:] = -0.9
    times = pd.date_range('2023-01-02', periods=n, freq='5min').to_numpy()
    s = np.full(n, 10.0)
    trades = backtest.run_backtest(z, s, times, round_trip_cost=0.0,
                                   swap_cost_long=0.07, swap_cost_short=0.99,
                                   timeout_bars=2 * 288).trades
    assert len(trades) == 1
    assert trades[0].side == 1
    assert trades[0].nights == 2
    assert abs(trades[0].pnl_net - (trades[0].pnl_gross - 2 * 0.07)) < 1e-12


def test_profit_factor():
    assert backtest.profit_factor([2.0, -1.0]) == 2.0
    assert backtest.profit_factor([-1.0, -2.0]) == 0.0
    assert backtest.profit_factor([]) == 0.0


def test_stationary_bootstrap_ci_bounds():
    rng = np.random.RandomState(0)
    pnls = list(rng.randn(200) * 0.5 + 0.1)   # положительное ожидание
    lo = backtest.stationary_bootstrap_ci(pnls, expected_block=10, n_resamples=500, seed=7)
    pf = backtest.profit_factor(pnls)
    assert 0.0 < lo <= pf


def test_run_backtest_empty_input_raises():
    try:
        backtest.run_backtest(np.array([]), np.array([]), np.array([]), round_trip_cost=0.1)
        assert False, "expected ValueError"
    except ValueError as e:
        assert "empty" in str(e).lower()


def test_run_backtest_length_mismatch_raises():
    z = np.array([0.0, 2.5, -0.1, 0.0])
    s_exec = np.array([10.0, 10.0, 10.5])
    times = np.array([1, 2, 3, 4])
    try:
        backtest.run_backtest(z, s_exec, times, round_trip_cost=0.1)
        assert False, "expected ValueError"
    except ValueError as e:
        assert "mismatch" in str(e).lower()
