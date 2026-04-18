# =============================================================================
# Файл: benchmark_take_skip_mt4_trailing_sequential.py
# Назначение: Быстро сравнить independent vs single-position trailing-stop для take/skip сигналов.
# Обновлён: 2026-04-18
# Входные данные:
#   - MT/tester/files/ml_signals_*.csv
#   - DATA/Nero_test_labeled.csv
#   - DATA/XAUUSD_H1_OHLC.csv
# Выходные данные:
#   - ML/reports/take_skip_mt4_trailing_sequential/summary.json
# Использование:
#   python -m ML.benchmark_take_skip_mt4_trailing_sequential
# Примечания:
#   - Read-only benchmark: обучение не запускается.
# =============================================================================

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd


@dataclass
class ModeSummary:
    mode: str
    signals: int
    opened: int
    blocked: int
    pf: float | str
    gross_profit_atr: float
    gross_loss_atr: float
    net_atr: float
    win_rate: float
    avg_hold_hours: float | None
    max_hold_hours: float | None
    yearly: dict[str, dict[str, float | int | str]]


def _profit_factor(values: list[float]) -> tuple[float | str, float, float]:
    gp = sum(v for v in values if v > 0)
    gl = -sum(v for v in values if v < 0)
    if gl == 0:
        pf: float | str = "inf" if gp > 0 else 0.0
    else:
        pf = gp / gl
    return pf, gp, gl


def _yearly(rows: list[dict]) -> dict[str, dict[str, float | int | str]]:
    out: dict[str, dict[str, float | int | str]] = {}
    by_year: dict[str, list[float]] = {}
    for row in rows:
        by_year.setdefault(str(row["exit_time"].year), []).append(row["pnl_atr"])
    for year, values in sorted(by_year.items()):
        pf, gp, gl = _profit_factor(values)
        out[year] = {
            "trades": len(values),
            "wins": sum(v > 0 for v in values),
            "losses": sum(v < 0 for v in values),
            "pf": pf,
            "net_atr": sum(values),
            "gross_profit_atr": gp,
            "gross_loss_atr": gl,
        }
    return out


def _summary(mode: str, signals: int, opened: int, blocked: int, rows: list[dict]) -> ModeSummary:
    values = [r["pnl_atr"] for r in rows]
    pf, gp, gl = _profit_factor(values)
    holds = [r["hold_hours"] for r in rows if "hold_hours" in r]
    return ModeSummary(
        mode=mode,
        signals=signals,
        opened=opened,
        blocked=blocked,
        pf=pf,
        gross_profit_atr=gp,
        gross_loss_atr=gl,
        net_atr=sum(values),
        win_rate=(sum(v > 0 for v in values) / len(values)) if values else 0.0,
        avg_hold_hours=(sum(holds) / len(holds)) if holds else None,
        max_hold_hours=max(holds) if holds else None,
        yearly=_yearly(rows),
    )


def load_signals(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, sep=";")
    df["time"] = pd.to_datetime(df["time"], format="%Y.%m.%d %H:%M")
    df = df.drop_duplicates("time", keep="last")
    return df[df["signal"] != 0][["time", "signal"]].copy()


def independent_from_labels(signals: pd.DataFrame, labels_path: Path, target: str) -> ModeSummary:
    labels = pd.read_csv(labels_path, sep=";", usecols=["time", "signal", target])
    labels["time"] = pd.to_datetime(labels["time"], format="%Y.%m.%d %H:%M")
    labels = labels.drop_duplicates(["time", "signal"], keep="last")
    merged = signals.merge(labels, on=["time", "signal"], how="left")
    rows = []
    for row in merged[["time", target]].itertuples(index=False, name=None):
        exit_time, pnl = row
        pnl = float(pnl)
        if not math.isnan(pnl):
            rows.append({"exit_time": exit_time, "pnl_atr": pnl})
    return _summary("independent_label", len(signals), len(rows), 0, rows)


def sequential_trailing(signals: pd.DataFrame, ohlc_path: Path, trail_atr: float) -> ModeSummary:
    ohlc = pd.read_csv(ohlc_path, sep=";", usecols=["time", "open", "high", "low", "atr14"])
    ohlc["time"] = pd.to_datetime(ohlc["time"], format="%Y.%m.%d %H:%M")
    bars = ohlc.to_dict("records")
    index_by_time = {row["time"]: i for i, row in enumerate(bars)}

    rows: list[dict] = []
    blocked = 0
    occupied_until = -1

    for sig in signals.itertuples(index=False):
        sig_idx = index_by_time.get(sig.time)
        if sig_idx is None:
            continue
        entry_idx = sig_idx + 1
        if entry_idx >= len(bars):
            continue
        if entry_idx <= occupied_until:
            blocked += 1
            continue

        entry = bars[entry_idx]
        entry_price = float(entry["open"])
        best = entry_price
        exit_idx = None
        exit_price = entry_price
        pnl_atr = 0.0

        for i in range(entry_idx, len(bars)):
            bar = bars[i]
            atr = float(bar["atr14"])
            if atr <= 0:
                continue
            if sig.signal == 1:
                best = max(best, float(bar["high"]))
                trail = best - atr * trail_atr
                if float(bar["low"]) <= trail:
                    exit_idx = i
                    exit_price = trail
                    pnl_atr = (exit_price - entry_price) / atr
                    break
            else:
                best = min(best, float(bar["low"]))
                trail = best + atr * trail_atr
                if float(bar["high"]) >= trail:
                    exit_idx = i
                    exit_price = trail
                    pnl_atr = (entry_price - exit_price) / atr
                    break

        if exit_idx is None:
            continue
        occupied_until = exit_idx
        hold_hours = (bars[exit_idx]["time"] - entry["time"]).total_seconds() / 3600.0
        rows.append(
            {
                "entry_time": entry["time"],
                "exit_time": bars[exit_idx]["time"],
                "signal": int(sig.signal),
                "entry": entry_price,
                "exit": exit_price,
                "pnl_atr": pnl_atr,
                "hold_hours": hold_hours,
            }
        )

    return _summary("single_position_trailing", len(signals), len(rows), blocked, rows)


def run_mode(name: str, signal_path: Path, labels_path: Path, ohlc_path: Path, target: str, trail_atr: float) -> dict:
    signals = load_signals(signal_path)
    return {
        "name": name,
        "signal_path": str(signal_path),
        "target": target,
        "trail_atr": trail_atr,
        "independent": asdict(independent_from_labels(signals, labels_path, target)),
        "single_position": asdict(sequential_trailing(signals, ohlc_path, trail_atr)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quality-signals", default="MT/tester/files/ml_signals_quality.csv")
    parser.add_argument("--frequency-signals", default="MT/tester/files/ml_signals_frequency.csv")
    parser.add_argument("--labels", default="DATA/Nero_test_labeled.csv")
    parser.add_argument("--ohlc", default="DATA/XAUUSD_H1_OHLC.csv")
    parser.add_argument("--target", default="trail_24_pnl_atr_x8")
    parser.add_argument("--trail-atr", type=float, default=8.0)
    parser.add_argument("--output-dir", default="ML/reports/take_skip_mt4_trailing_sequential")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    result = {
        "quality": run_mode(
            "quality",
            Path(args.quality_signals),
            Path(args.labels),
            Path(args.ohlc),
            args.target,
            args.trail_atr,
        ),
        "frequency": run_mode(
            "frequency",
            Path(args.frequency_signals),
            Path(args.labels),
            Path(args.ohlc),
            args.target,
            args.trail_atr,
        ),
    }
    (output_dir / "summary.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
