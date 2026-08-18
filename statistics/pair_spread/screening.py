# =============================================================================
# Файл: statistics/pair_spread/screening.py
# Назначение: ступень 1 kill-теста — метрики скрининга на train (спека, раздел 5)
# Обновлён: 2026-08-18
# Зависимости:
#   Входные данные: лог-спред train (pair_data), round-trip стоимость c (run_pair_spread)
#   Выходные данные: dict метрик + вердикт (куда: run_pair_spread.py)
#   Внешние зависимости: statsmodels.tsa.stattools.coint (Энгл-Грэнджер)
# =============================================================================
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import coint

__all__ = [
    'ScreeningThresholds', 'engle_granger_pvalue', 'episode_bounds',
    'fit_beta', 'half_life_bars', 'screening_metrics', 'spread_mu_sigma',
    'verdict_pass',
]


@dataclass(frozen=True)
class ScreeningThresholds:
    coint_p_max: float = 0.05
    half_life_min_bars: float = 6.0
    half_life_max_bars: float = 2880.0
    min_episodes_per_year: float = 5.0
    entry_z: float = 2.0


def fit_beta(a_log: np.ndarray | pd.Series, b_log: np.ndarray | pd.Series) -> float:
    x = np.asarray(b_log, dtype=float)
    y = np.asarray(a_log, dtype=float)
    x = x - x.mean()
    y = y - y.mean()
    return float((x * y).sum() / (x * x).sum())


def engle_granger_pvalue(a_log: np.ndarray | pd.Series, b_log: np.ndarray | pd.Series) -> float:
    _, p, _ = coint(np.asarray(a_log, dtype=float), np.asarray(b_log, dtype=float), trend='c')
    return float(p)


def half_life_bars(s: pd.Series) -> float:
    y = s.to_numpy(dtype=float)
    x_prev, y_next = y[:-1], y[1:]
    x = x_prev - x_prev.mean()
    yv = y_next - y_next.mean()
    rho = float((x * yv).sum() / (x * x).sum())
    if not (0.0 < rho < 1.0):
        return float('inf')
    return float(-np.log(2.0) / np.log(rho))


def spread_mu_sigma(s_train: pd.Series) -> tuple[float, float]:
    return float(s_train.mean()), float(s_train.std(ddof=1))


def episode_bounds(z: pd.Series, entry_z: float = 2.0) -> list[tuple[int, int]]:
    """Старт: первый бар с |z| >= entry после бара с |z| < entry.
    Конец: первый бар после старта с |z| <= |z_start|/2 (половина возврата).
    Незавершённые эпизоды отбрасываются."""
    zv = z.to_numpy(dtype=float)
    n = len(zv)
    episodes: list[tuple[int, int]] = []
    in_ep = False
    start = -1
    half = 0.0
    for i in range(n):
        if not in_ep:
            above = abs(zv[i]) >= entry_z
            was_below = (i == 0) or (abs(zv[i - 1]) < entry_z)
            if above and was_below:
                in_ep = True
                start = i
                half = abs(zv[i]) / 2.0
        else:
            if abs(zv[i]) <= half:
                episodes.append((start, i))
                in_ep = False
    return episodes


def screening_metrics(s_train: pd.Series, z_train: pd.Series, cost_c: float,
                      thresholds: ScreeningThresholds) -> dict:
    episodes = episode_bounds(z_train, thresholds.entry_z)
    years = max((z_train.index[-1] - z_train.index[0]).days / 365.25, 1e-9)
    ds = s_train.diff().dropna().abs()
    mu = float(s_train.mean())
    devs: list[float] = []
    durations: list[int] = []
    for start, end in episodes:
        devs.extend(abs(s_train.iloc[start:end + 1] - mu).tolist())
        durations.append(end - start)
    return {
        'n_episodes': len(episodes),
        'episodes_per_year': len(episodes) / years,
        'p75_abs_ds': float(np.percentile(ds, 75)) if len(ds) else float('nan'),
        'median_episode_deviation': float(np.median(devs)) if devs else 0.0,
        # длительности эпизодов: артефакт для отчёта (спека разделы 5, 8) и
        # замороженная длина блока bootstrap (спека раздел 6, аудит В-1/В-4)
        'episode_durations_bars': durations,
        'median_episode_duration_bars': float(np.median(durations)) if durations else 0.0,
        'cost_c': float(cost_c),
    }


def verdict_pass(metrics: dict, th: ScreeningThresholds) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if metrics['coint_p'] > th.coint_p_max:
        reasons.append(f"EG p {metrics['coint_p']:.4f} > {th.coint_p_max}")
    hl = metrics['half_life_bars']
    if not (th.half_life_min_bars <= hl <= th.half_life_max_bars):
        reasons.append(f'half-life {hl:.1f} вне [{th.half_life_min_bars}, {th.half_life_max_bars}]')
    if metrics['cost_c'] > metrics['p75_abs_ds']:
        reasons.append(f"cost {metrics['cost_c']:.6f} > P75|ds| {metrics['p75_abs_ds']:.6f}")
    if metrics['median_episode_deviation'] <= metrics['cost_c']:
        reasons.append('медианное отклонение в эпизодах <= round-trip стоимости')
    if metrics['episodes_per_year'] < th.min_episodes_per_year:
        reasons.append(f"эпизодов/год {metrics['episodes_per_year']:.2f} < {th.min_episodes_per_year}")
    return (len(reasons) == 0, reasons)
