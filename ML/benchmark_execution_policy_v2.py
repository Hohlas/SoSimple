# =============================================================================
# Файл: benchmark_execution_policy_v2.py
# Назначение: Сравнить варианты выхода для готовых ML-сигналов без обучения.
# Обновлён: 2026-04-19
# Входные данные:
#   - MT/tester/files/ml_signals_quality.csv
#   - MT/tester/files/ml_signals_frequency.csv
#   - DATA/XAUUSD_H1_OHLC.csv
# Выходные данные:
#   - ML/reports/execution_policy_v2/summary.csv
#   - ML/reports/execution_policy_v2/summary.json
#   - ML/reports/execution_policy_v2/trades.csv
# Использование:
#   python -m ML.benchmark_execution_policy_v2
# =============================================================================

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ExitPolicy:
    name: str
    stop_atr: float = 8.0
    trail_atr: float | None = 8.0
    take_profit_atr: float | None = None
    hold_bars: int | None = None
    shrink_tiers: tuple[tuple[float, float], ...] = ()


DEFAULT_POLICIES: tuple[ExitPolicy, ...] = (
    ExitPolicy(name="trail_x6", stop_atr=6.0, trail_atr=6.0),
    ExitPolicy(name="trail_x8", stop_atr=8.0, trail_atr=8.0),
    ExitPolicy(name="trail_x10", stop_atr=10.0, trail_atr=10.0),
    ExitPolicy(name="hold_24_backstop_50", stop_atr=50.0, trail_atr=None, hold_bars=24),
    ExitPolicy(name="trail_x8_tp8", stop_atr=8.0, trail_atr=8.0, take_profit_atr=8.0),
    ExitPolicy(name="trail_x8_tp12", stop_atr=8.0, trail_atr=8.0, take_profit_atr=12.0),
    ExitPolicy(name="trail_x8_tp16", stop_atr=8.0, trail_atr=8.0, take_profit_atr=16.0),
    ExitPolicy(name="trail_x8_tp24", stop_atr=8.0, trail_atr=8.0, take_profit_atr=24.0),
    ExitPolicy(name="stop_x8_tp8", stop_atr=8.0, trail_atr=None, take_profit_atr=8.0),
    ExitPolicy(name="stop_x8_tp12", stop_atr=8.0, trail_atr=None, take_profit_atr=12.0),
    ExitPolicy(name="stop_x8_tp16", stop_atr=8.0, trail_atr=None, take_profit_atr=16.0),
    ExitPolicy(name="stop_x8_tp24", stop_atr=8.0, trail_atr=None, take_profit_atr=24.0),
    ExitPolicy(
        name="shrinking_trail_8_6_4_3",
        stop_atr=8.0,
        trail_atr=8.0,
        shrink_tiers=((8.0, 6.0), (16.0, 4.0), (24.0, 3.0)),
    ),
)


FREQUENCY_TRAIL_SCAN_POLICIES: tuple[ExitPolicy, ...] = (
    ExitPolicy(name="trail_x6", stop_atr=6.0, trail_atr=6.0),
    ExitPolicy(name="trail_x8", stop_atr=8.0, trail_atr=8.0),
    ExitPolicy(name="trail_x10", stop_atr=10.0, trail_atr=10.0),
)


POLICY_SETS: dict[str, tuple[ExitPolicy, ...]] = {
    "default": DEFAULT_POLICIES,
    "frequency_trail_scan": FREQUENCY_TRAIL_SCAN_POLICIES,
}


def load_signals(path: Path, start: pd.Timestamp | None = None, end: pd.Timestamp | None = None) -> pd.DataFrame:
    df = pd.read_csv(path, sep=";")
    df["time"] = pd.to_datetime(df["time"], format="%Y.%m.%d %H:%M")
    df = df.drop_duplicates("time", keep="last")
    if start is not None:
        df = df[df["time"] >= start]
    if end is not None:
        df = df[df["time"] < end]
    return df[df["signal"] != 0][["time", "signal"]].copy()


def load_ohlc(path: Path, start: pd.Timestamp | None = None, end: pd.Timestamp | None = None) -> tuple[list[dict], dict[pd.Timestamp, int]]:
    frame = pd.read_csv(path, sep=";", usecols=["time", "open", "high", "low", "close", "atr14"])
    frame["time"] = pd.to_datetime(frame["time"], format="%Y.%m.%d %H:%M")
    if start is not None:
        # Берём один бар до старта, чтобы сигнал на последнем предшествующем баре не ломал индекс.
        frame = frame[frame["time"] >= start - pd.Timedelta(days=7)]
    if end is not None:
        frame = frame[frame["time"] < end]
    bars = frame.to_dict("records")
    index_by_time = {row["time"]: idx for idx, row in enumerate(bars)}
    return bars, index_by_time


def _active_trail_atr(policy: ExitPolicy, max_profit_atr: float) -> float | None:
    if policy.trail_atr is None:
        return None
    trail_atr = policy.trail_atr
    for profit_threshold, narrowed_trail in policy.shrink_tiers:
        if max_profit_atr >= profit_threshold:
            trail_atr = narrowed_trail
    return trail_atr


def _profit_factor(pnl: np.ndarray) -> float | str:
    gross_profit = float(pnl[pnl > 0].sum()) if pnl.size else 0.0
    gross_loss = float(-pnl[pnl < 0].sum()) if pnl.size else 0.0
    if gross_loss == 0.0:
        return "inf" if gross_profit > 0.0 else 0.0
    return gross_profit / gross_loss


def _max_drawdown(equity: np.ndarray) -> float:
    if equity.size == 0:
        return 0.0
    peaks = np.maximum.accumulate(np.insert(equity, 0, 0.0))[1:]
    return float(np.maximum(0.0, peaks - equity).max(initial=0.0))


def _ulcer_index(equity: np.ndarray) -> float:
    if equity.size == 0:
        return 0.0
    peaks = np.maximum.accumulate(np.insert(equity, 0, 0.0))[1:]
    drawdown = np.maximum(0.0, peaks - equity)
    return float(np.sqrt(np.mean(np.square(drawdown))))


def _equity_linearity_r2(equity: np.ndarray) -> float:
    if equity.size < 2:
        return 0.0
    x = np.arange(equity.size, dtype=float)
    y = equity.astype(float)
    slope, intercept = np.polyfit(x, y, 1)
    predicted = slope * x + intercept
    ss_res = float(np.square(y - predicted).sum())
    ss_tot = float(np.square(y - y.mean()).sum())
    if ss_tot == 0.0:
        return 1.0
    return max(0.0, min(1.0, 1.0 - ss_res / ss_tot))


def _profit_concentration(pnl: np.ndarray, top_n: int) -> float:
    gross_profit = float(pnl[pnl > 0].sum()) if pnl.size else 0.0
    if gross_profit <= 0.0:
        return 0.0
    winners = np.sort(pnl[pnl > 0])[::-1]
    if winners.size == 0:
        return 0.0
    return float(winners[: min(top_n, winners.size)].sum() / gross_profit)


def _negative_periods(trades: pd.DataFrame, period: str) -> int:
    if trades.empty:
        return 0
    grouped = trades.groupby(trades["exit_time"].dt.to_period(period))["pnl_atr"].sum()
    return int((grouped < 0).sum())


def _max_consecutive_count(pnl: np.ndarray, positive: bool) -> int:
    best = 0
    current = 0
    for value in pnl:
        if (value > 0) == positive and value != 0:
            current += 1
            best = max(best, current)
        else:
            current = 0
    return best


def _max_consecutive_sum(pnl: np.ndarray, positive: bool) -> float:
    best = 0.0
    current = 0.0
    for value in pnl:
        if (value > 0) == positive and value != 0:
            current += float(value)
            if positive:
                best = max(best, current)
            else:
                best = min(best, current)
        else:
            current = 0.0
    return best


def _summarize(dataset: str, policy: ExitPolicy, trades: pd.DataFrame) -> dict:
    pnl = trades["pnl_atr"].to_numpy(dtype=float) if not trades.empty else np.array([], dtype=float)
    equity = np.cumsum(pnl)
    gross_profit = float(pnl[pnl > 0].sum()) if pnl.size else 0.0
    gross_loss = float(-pnl[pnl < 0].sum()) if pnl.size else 0.0
    years = 0.0
    if not trades.empty:
        days = max((trades["exit_time"].max() - trades["entry_time"].min()).days, 1)
        years = days / 365.25

    return {
        "dataset": dataset,
        "policy": policy.name,
        "trades": int(len(trades)),
        "trades_per_year": float(len(trades) / years) if years > 0 else 0.0,
        "pf": _profit_factor(pnl),
        "net_atr": float(pnl.sum()) if pnl.size else 0.0,
        "gross_profit_atr": gross_profit,
        "gross_loss_atr": gross_loss,
        "mean_pnl_atr": float(pnl.mean()) if pnl.size else 0.0,
        "median_pnl_atr": float(np.median(pnl)) if pnl.size else 0.0,
        "win_rate": float((pnl > 0).mean()) if pnl.size else 0.0,
        "max_drawdown_atr": _max_drawdown(equity),
        "ulcer_index_atr": _ulcer_index(equity),
        "equity_linearity_r2": _equity_linearity_r2(equity),
        "profit_concentration_top_1": _profit_concentration(pnl, 1),
        "profit_concentration_top_3": _profit_concentration(pnl, 3),
        "profit_concentration_top_10": _profit_concentration(pnl, 10),
        "negative_months": _negative_periods(trades, "M"),
        "negative_years": _negative_periods(trades, "Y"),
        "worst_trade_atr": float(pnl.min()) if pnl.size else 0.0,
        "best_trade_atr": float(pnl.max()) if pnl.size else 0.0,
        "max_consecutive_losses": _max_consecutive_count(pnl, positive=False),
        "max_consecutive_loss_atr": _max_consecutive_sum(pnl, positive=False),
        "max_consecutive_wins": _max_consecutive_count(pnl, positive=True),
        "max_consecutive_win_atr": _max_consecutive_sum(pnl, positive=True),
        "avg_hold_hours": float(trades["hold_hours"].mean()) if not trades.empty else 0.0,
        "max_hold_hours": float(trades["hold_hours"].max()) if not trades.empty else 0.0,
    }


def simulate_policy(signals: pd.DataFrame, bars: list[dict], index_by_time: dict[pd.Timestamp, int], policy: ExitPolicy) -> pd.DataFrame:
    rows: list[dict] = []

    for sig in signals.itertuples(index=False):
        sig_idx = index_by_time.get(sig.time)
        if sig_idx is None:
            continue
        entry_idx = sig_idx + 1
        if entry_idx >= len(bars):
            continue

        entry = bars[entry_idx]
        entry_time = entry["time"]
        entry_price = float(entry["open"])
        entry_atr = float(entry["atr14"])
        if entry_atr <= 0.0:
            continue

        direction = int(sig.signal)
        best = entry_price
        worst = entry_price
        max_profit_atr = 0.0

        if direction == 1:
            stop_price = entry_price - policy.stop_atr * entry_atr
            take_profit_price = None if policy.take_profit_atr is None else entry_price + policy.take_profit_atr * entry_atr
        else:
            stop_price = entry_price + policy.stop_atr * entry_atr
            take_profit_price = None if policy.take_profit_atr is None else entry_price - policy.take_profit_atr * entry_atr

        exit_idx = None
        exit_price = entry_price
        exit_reason = "no_exit"
        exit_atr = entry_atr
        hold_exit_idx = None
        if policy.hold_bars is not None:
            hold_exit_idx = entry_idx + int(policy.hold_bars) - 1
            if hold_exit_idx >= len(bars):
                hold_exit_idx = None

        for i in range(entry_idx, len(bars)):
            bar = bars[i]
            high = float(bar["high"])
            low = float(bar["low"])
            current_atr = float(bar["atr14"])
            if current_atr <= 0.0:
                continue

            if direction == 1:
                best = max(best, high)
                worst = min(worst, low)
                max_profit_atr = max(max_profit_atr, (best - entry_price) / entry_atr)
                trail_atr = _active_trail_atr(policy, max_profit_atr)
                active_stop = stop_price if trail_atr is None else max(stop_price, best - trail_atr * current_atr)

                stop_hit = low <= active_stop
                take_hit = take_profit_price is not None and high >= take_profit_price
                if stop_hit or take_hit:
                    exit_idx = i
                    exit_reason = "stop_or_trail" if stop_hit else "take_profit"
                    exit_price = active_stop if stop_hit else float(take_profit_price)
                    exit_atr = current_atr
                    break
            else:
                best = min(best, low)
                worst = max(worst, high)
                max_profit_atr = max(max_profit_atr, (entry_price - best) / entry_atr)
                trail_atr = _active_trail_atr(policy, max_profit_atr)
                active_stop = stop_price if trail_atr is None else min(stop_price, best + trail_atr * current_atr)

                stop_hit = high >= active_stop
                take_hit = take_profit_price is not None and low <= take_profit_price
                if stop_hit or take_hit:
                    exit_idx = i
                    exit_reason = "stop_or_trail" if stop_hit else "take_profit"
                    exit_price = active_stop if stop_hit else float(take_profit_price)
                    exit_atr = current_atr
                    break

            if hold_exit_idx is not None and i >= hold_exit_idx:
                exit_idx = i
                exit_reason = "fixed_hold"
                exit_price = float(bar["close"])
                exit_atr = current_atr
                break

        if exit_idx is None:
            continue

        pnl_price = (exit_price - entry_price) * direction
        rows.append(
            {
                "signal_time": sig.time,
                "entry_time": entry_time,
                "exit_time": bars[exit_idx]["time"],
                "signal": direction,
                "policy": policy.name,
                "entry": entry_price,
                "exit": exit_price,
                "entry_atr": entry_atr,
                "exit_atr": exit_atr,
                "pnl_price": pnl_price,
                "pnl_atr": pnl_price / entry_atr,
                "max_profit_atr": max_profit_atr,
                "max_adverse_atr": ((entry_price - worst) / entry_atr) if direction == 1 else ((worst - entry_price) / entry_atr),
                "hold_hours": (bars[exit_idx]["time"] - entry_time).total_seconds() / 3600.0,
                "exit_reason": exit_reason,
            }
        )

    return pd.DataFrame(rows)


def run_benchmark(
    signal_paths: dict[str, Path],
    ohlc_path: Path,
    policies: Iterable[ExitPolicy],
    output_dir: Path,
    start: pd.Timestamp | None = None,
    end: pd.Timestamp | None = None,
) -> dict:
    bars, index_by_time = load_ohlc(ohlc_path, start=start, end=end)
    summaries: list[dict] = []
    all_trades: list[pd.DataFrame] = []

    for dataset, signal_path in signal_paths.items():
        signals = load_signals(signal_path, start=start, end=end)
        for policy in policies:
            trades = simulate_policy(signals, bars, index_by_time, policy)
            if not trades.empty:
                trades.insert(0, "dataset", dataset)
                all_trades.append(trades)
            summaries.append(_summarize(dataset, policy, trades))

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_frame = pd.DataFrame(summaries)
    summary_frame.to_csv(output_dir / "summary.csv", index=False)
    if all_trades:
        trades_frame = pd.concat(all_trades, ignore_index=True)
    else:
        trades_frame = pd.DataFrame()
    trades_frame.to_csv(output_dir / "trades.csv", index=False)

    result = {
        "ohlc_path": str(ohlc_path),
        "period": {
            "start": str(start) if start is not None else None,
            "end": str(end) if end is not None else None,
        },
        "signals": {name: str(path) for name, path in signal_paths.items()},
        "summary": summaries,
    }
    (output_dir / "summary.json").write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quality-signals", default="MT/tester/files/ml_signals_quality.csv")
    parser.add_argument("--frequency-signals", default="MT/tester/files/ml_signals_frequency.csv")
    parser.add_argument("--ohlc", default="DATA/XAUUSD_H1_OHLC.csv")
    parser.add_argument("--output-dir", default="ML/reports/execution_policy_v2")
    parser.add_argument("--start", default="2023-01-01")
    parser.add_argument("--end", default="2026-01-01")
    parser.add_argument("--policy-set", choices=sorted(POLICY_SETS), default="default")
    parser.add_argument(
        "--datasets",
        nargs="+",
        choices=("quality", "frequency"),
        default=["quality", "frequency"],
        help="Какие наборы сигналов прогонять.",
    )
    args = parser.parse_args()

    signal_paths = {}
    if "quality" in args.datasets:
        signal_paths["quality"] = Path(args.quality_signals)
    if "frequency" in args.datasets:
        signal_paths["frequency"] = Path(args.frequency_signals)

    result = run_benchmark(
        signal_paths=signal_paths,
        ohlc_path=Path(args.ohlc),
        policies=POLICY_SETS[args.policy_set],
        output_dir=Path(args.output_dir),
        start=pd.Timestamp(args.start) if args.start else None,
        end=pd.Timestamp(args.end) if args.end else None,
    )
    print(json.dumps(result["summary"], indent=2, default=str))


if __name__ == "__main__":
    main()
