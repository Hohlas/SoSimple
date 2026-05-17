# =============================================================================
# Файл: entry_path_level_targets.py
# Назначение: Target families и ранние gates для fractal-level entry path.
# Обновлён: 2026-05-15
# Входные данные:
#   - DATA/Nero_*_labeled.csv и DATA/XAUUSD_H1_OHLC.csv
# Выходные данные:
#   - candidate_direction, target summaries и direction baseline artifacts
# Использование:
#   from ML.entry_path_level_targets import summarize_direction_baseline
# Примечания:
#   - Исторический source["signal"] не используется для candidate/target construction.
# =============================================================================

from __future__ import annotations

from datetime import timezone
from math import erf
from math import sqrt
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ML.entry_path_trade_filter import compute_pf
from ML.fractal_level_feature_builder import parse_fractal
from processing.label_signals import compute_entry_path_slice
from processing.label_signals import load_ohlc_index


def candidate_signal_from_fractal0_direction(fractal_direction: int) -> int:
    """Преобразует направление fractal0 в live-safe направление сделки."""
    if int(fractal_direction) == -1:
        return 1
    if int(fractal_direction) == 1:
        return -1
    return 0


def reverse_signal(signal: int) -> int:
    """Возвращает обратное направление сделки."""
    return -int(signal)


def build_candidate_direction_from_fractal0(source: pd.DataFrame) -> pd.Series:
    """Строит `candidate_direction` из `fractal0.direction`, игнорируя source['signal']."""
    values = []
    for raw in source["fractal0"]:
        parsed = parse_fractal(raw)
        direction = int(parsed["direction"]) if parsed is not None else 0
        values.append(candidate_signal_from_fractal0_direction(direction))
    return pd.Series(values, index=source.index, dtype="int64", name="candidate_direction")


def summarize_direction_baseline(
    source: pd.DataFrame,
    ohlc_path: str | Path,
    horizon: int = 24,
) -> dict[str, Any]:
    """Сравнивает `fractal0.direction` с обратным направлением на OHLC path."""
    candidate_direction = build_candidate_direction_from_fractal0(source)
    reverse_direction = candidate_direction.map(reverse_signal).astype("int64")
    direct_pnl = _compute_pnl_for_signal(source, candidate_direction, ohlc_path, horizon)
    reverse_pnl = _compute_pnl_for_signal(source, reverse_direction, ohlc_path, horizon)
    valid = candidate_direction.isin([-1, 1])
    buy_mask = valid & (candidate_direction == 1)
    sell_mask = valid & (candidate_direction == -1)
    direct_wins = direct_pnl.loc[valid] > 0
    reverse_wins = reverse_pnl.loc[valid] > 0
    correct_direction_rate = float((direct_pnl.loc[valid] > reverse_pnl.loc[valid]).mean()) if valid.any() else 0.0
    p_value = _two_sided_binomial_normal_pvalue(int((direct_pnl.loc[valid] > reverse_pnl.loc[valid]).sum()), int(valid.sum()))

    direct = _pnl_summary(direct_pnl.loc[valid])
    reverse = _pnl_summary(reverse_pnl.loc[valid])
    buy_only = _pnl_summary(direct_pnl.loc[buy_mask])
    sell_only = _pnl_summary(direct_pnl.loc[sell_mask])
    direction_counts = {
        str(direction): int((candidate_direction == direction).sum())
        for direction in (-1, 0, 1)
    }
    advantage = direct["win_rate"] - reverse["win_rate"]
    gate_failures = []
    if reverse["pf"] > direct["pf"] or reverse["win_rate"] > direct["win_rate"]:
        gate_failures.append("reverse_direction_better")
    if valid.sum() >= 100 and correct_direction_rate <= 0.52:
        gate_failures.append("correct_direction_rate_lte_52pct")
    if valid.sum() >= 30 and p_value >= 0.05:
        gate_failures.append("not_statistically_above_50pct")
    if advantage < 0.02:
        gate_failures.append("win_rate_advantage_lt_2pp")
    if reverse["mean_pnl_atr"] >= direct["mean_pnl_atr"]:
        gate_failures.append("reverse_mean_pnl_gte_direct")
    if buy_only["trades"] >= 100 and buy_only["pf"] < 0.9:
        gate_failures.append("buy_only_pf_lt_0_9")
    if sell_only["trades"] >= 100 and sell_only["pf"] < 0.9:
        gate_failures.append("sell_only_pf_lt_0_9")

    return {
        "horizon": int(horizon),
        "valid_rows": int(valid.sum()),
        "trades_by_candidate_direction": direction_counts,
        "direct": direct,
        "reverse": reverse,
        "buy_only": buy_only,
        "sell_only": sell_only,
        "direct_win_count": int(direct_wins.sum()),
        "reverse_win_count": int(reverse_wins.sum()),
        "correct_direction_rate": correct_direction_rate,
        "binomial_p_value_vs_50pct": float(p_value),
        "conditional_win_rate_advantage": float(advantage),
        "gate_pass": not gate_failures,
        "gate_failures": gate_failures,
    }


def _compute_pnl_for_signal(
    source: pd.DataFrame,
    signal: pd.Series,
    ohlc_path: str | Path,
    horizon: int,
) -> pd.Series:
    ohlc, times, time_idx = load_ohlc_index(str(ohlc_path))
    parsed_time = pd.to_datetime(source["time"], format="%Y.%m.%d %H:%M", errors="coerce")
    atr_values = pd.to_numeric(source["ATR"], errors="coerce").fillna(0.0).to_numpy(dtype=np.float64)
    pnl = pd.Series(0.0, index=source.index, dtype="float64")

    for pos, row_time in enumerate(parsed_time):
        direction = int(signal.iloc[pos])
        atr = float(atr_values[pos])
        if direction not in (-1, 1) or pd.isna(row_time) or atr <= 0:
            continue
        row_dt = row_time.to_pydatetime().replace(tzinfo=timezone.utc)
        base_idx = time_idx.get(row_dt)
        if base_idx is None:
            continue
        entry_idx = base_idx + 1
        end_idx = entry_idx + int(horizon)
        if entry_idx >= len(times) or end_idx > len(times):
            continue
        entry_price = float(ohlc[times[entry_idx]][0])
        bars = pd.DataFrame(
            [
                {
                    "open": ohlc[times[idx]][0],
                    "high": ohlc[times[idx]][1],
                    "low": ohlc[times[idx]][2],
                    "close": ohlc[times[idx]][3],
                }
                for idx in range(entry_idx, end_idx)
            ],
            columns=["open", "high", "low", "close"],
        )
        pnl.iloc[pos] = compute_entry_path_slice(bars, direction, entry_price, atr, int(horizon))["ret_dir_atr"]
    return pnl


def _pnl_summary(pnl: pd.Series) -> dict[str, Any]:
    values = pd.to_numeric(pnl, errors="coerce").fillna(0.0).to_numpy(dtype=np.float64)
    return {
        "trades": int(len(values)),
        "pf": compute_pf(values),
        "win_rate": float((values > 0).mean()) if len(values) else 0.0,
        "mean_pnl_atr": float(values.mean()) if len(values) else 0.0,
    }


def _two_sided_binomial_normal_pvalue(successes: int, trials: int) -> float:
    if trials <= 0:
        return 1.0
    z = (float(successes) - 0.5 * float(trials)) / sqrt(0.25 * float(trials))
    normal_cdf = 0.5 * (1.0 + erf(abs(z) / sqrt(2.0)))
    return float(2.0 * (1.0 - normal_cdf))
