# =============================================================================
# Файл: statistics/pair_spread/backtest.py
# Назначение: ступень 2 kill-теста — симулятор z-score правила (спека, раздел 6)
#             + stationary bootstrap BS_p05 (методология 09)
# Обновлён: 2026-08-18
# Зависимости:
#   Входные данные: z по close (train-нормировка), s_exec по open, времена, издержки
#   Выходные данные: BacktestResult(trades, dropped_open_at_end), PF, BS_p05
#                    (куда: run_pair_spread.py)
# Конвенция исполнения: сигнал на закрытии бара i -> исполнение на открытии i+1.
# =============================================================================
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

__all__ = ['BacktestResult', 'Trade', 'profit_factor', 'run_backtest',
           'stationary_bootstrap_ci']

ENTRY_Z = 2.0
STOP_Z = 4.0
TIMEOUT_BARS = 2880


@dataclass
class Trade:
    side: int            # +1 long спреда, -1 short спреда
    entry_i: int         # индекс бара исполнения входа (open)
    exit_i: int          # индекс бара исполнения выхода (open)
    pnl_gross: float
    pnl_net: float
    exit_reason: str     # 'revert' | 'stop' | 'timeout'
    nights: int


@dataclass
class BacktestResult:
    trades: list[Trade] = field(default_factory=list)
    # позиция, открытая на конец данных: сигнал выхода на последнем баре
    # исполнить негде — сделка не учитывается в PF, но подсчитывается (аудит К-2.4/Q-3)
    dropped_open_at_end: int = 0


def _nights_between(times, i_entry, i_exit) -> int:
    d0 = times[i_entry].astype('datetime64[D]')
    d1 = times[i_exit].astype('datetime64[D]')
    return int((d1 - d0).astype(int))


def run_backtest(z: np.ndarray, s_exec: np.ndarray, times: np.ndarray,
                 round_trip_cost: float,
                 swap_cost_long: float = 0.0, swap_cost_short: float = 0.0,
                 entry_z: float = ENTRY_Z, stop_z: float = STOP_Z,
                 timeout_bars: int = TIMEOUT_BARS) -> BacktestResult:
    """swap_cost_long/short — стоимость ночи удержания (положительная — издержка,
    отрицательная — кэрри-доход) для сделки side=+1 и side=-1 соответственно
    (аудит В-6: своп комбинированной позиции зависит от стороны)."""
    z = np.asarray(z, dtype=float)
    s_exec = np.asarray(s_exec, dtype=float)
    n = len(z)
    result = BacktestResult()
    need_zero_cross = False
    pos = None  # dict: side, entry_bar (бар сигнала), exec_i, entry_sign

    for i in range(n):
        # --- выход (проверяется на закрытии бара i при открытой позиции) ---
        if pos is not None:
            held = i - pos['entry_bar']
            crossed_zero = z[i] * pos['entry_sign'] <= 0.0
            reason = None
            if crossed_zero:
                reason = 'revert'
            elif abs(z[i]) >= stop_z:
                reason = 'stop'
            elif held >= timeout_bars:
                reason = 'timeout'
            if reason is not None and i + 1 < n:
                exec_exit = i + 1
                gross = pos['side'] * (s_exec[exec_exit] - s_exec[pos['exec_i']])
                nights = _nights_between(times, pos['exec_i'], exec_exit)
                swap = swap_cost_long if pos['side'] > 0 else swap_cost_short
                net = gross - round_trip_cost - swap * nights
                result.trades.append(Trade(pos['side'], pos['exec_i'], exec_exit,
                                           gross, net, reason, nights))
                pos = None
                need_zero_cross = reason in ('stop', 'timeout')
                continue
        # --- вход (проверяется на закрытии бара i при плоской позиции) ---
        if pos is None and i + 1 < n:
            if need_zero_cross:
                if i > 0 and z[i] * z[i - 1] < 0.0:
                    need_zero_cross = False
                else:
                    continue
            if entry_z <= abs(z[i]) < stop_z:
                pos = {
                    'side': -1 if z[i] > 0 else 1,
                    'entry_bar': i,
                    'exec_i': i + 1,
                    'entry_sign': 1.0 if z[i] > 0 else -1.0,
                }
    if pos is not None:
        result.dropped_open_at_end = 1
    return result


def profit_factor(pnls) -> float:
    gains = sum(p for p in pnls if p > 0)
    losses = -sum(p for p in pnls if p < 0)
    if losses <= 0:
        return 0.0 if gains <= 0 else float('inf')
    return gains / losses


def stationary_bootstrap_ci(pnls, expected_block: float, n_resamples: int = 10000,
                            quantile: float = 0.05, seed: int = 0) -> float:
    """Stationary bootstrap Политиса-Романо по ряду PnL сделок (временной порядок).
    Длина блока геометрическая с матожиданием expected_block.
    Возвращает нижнюю границу PF (BS_p05 по умолчанию)."""
    pnls = np.asarray(pnls, dtype=float)
    n = len(pnls)
    if n == 0:
        return 0.0
    rng = np.random.default_rng(seed)
    p = 1.0 / max(expected_block, 1.0)
    pfs = np.empty(n_resamples)
    for r in range(n_resamples):
        sample = np.empty(n)
        idx = rng.integers(n)
        for k in range(n):
            sample[k] = pnls[idx]
            if rng.random() < p:
                idx = rng.integers(n)
            else:
                idx = (idx + 1) % n
        pf = profit_factor(sample)
        pfs[r] = min(pf, 1e6)
    return float(np.quantile(pfs, quantile))
