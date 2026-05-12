# =============================================================================
# Файл: online_tester_reconciliation.py
# Назначение: Сверка online/tester `ml_trade_events.csv` с ожидаемыми ML-сигналами.
# Обновлён: 2026-05-12
# Входные данные:
#   - ml_trade_events.csv (online, от MT4 эксперта)
#   - ml_signals.csv (runtime signals)
#   - optional: tester ml_trade_events.csv (после прогона тестера)
# Выходные данные:
#   - summary.json, summary.md, signals_diff.csv, trades_comparison.csv
#   - online_trades.csv, online_closed_trades.csv
# Использование:
#   python -m ML.online_tester_reconciliation \
#     --events <online_ml_trade_events.csv> \
#     --signals <ml_signals.csv> \
#     --output-dir <dir> \
#     [--tester-events <tester_ml_trade_events.csv>] \
#     [--start-time "YYYY.MM.DD HH:MM"] [--end-time "YYYY.MM.DD HH:MM"]
# Примечания:
#   - Сравнение online/tester выполняется по `signal_time + direction`, а не по ticket.
#   - `OPEN_FAILED` считается отдельным статусом, не пропадает как обычный skip.
# =============================================================================

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd


TIME_FORMAT = "%Y.%m.%d %H:%M"
TIME_COLUMNS = ("signal_time", "entry_time", "exit_time")
NUMERIC_COLUMNS = (
    "ticket",
    "signal",
    "score",
    "atr",
    "bid",
    "ask",
    "spread",
    "spread_atr",
    "bar_open",
    "bar_high",
    "bar_low",
    "bar_close",
    "requested_price",
    "order_open_price",
    "order_close_price",
    "slippage_points",
    "entry",
    "stop",
    "take_profit",
    "close",
    "profit",
    "swap",
    "commission",
    "hold_bars",
    "open_positions",
    "max_positions",
    "balance",
    "equity",
)


def parse_time(value: str | None) -> pd.Timestamp | None:
    if value is None:
        return None
    parsed = pd.to_datetime(value, format=TIME_FORMAT, errors="coerce")
    return None if pd.isna(parsed) else parsed


def load_events(path: str | Path) -> pd.DataFrame:
    """Загружает MT4 event-log и приводит время/числа к рабочим типам."""
    df = pd.read_csv(path, sep=";")
    for col in TIME_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], format=TIME_FORMAT, errors="coerce")
    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def load_signals(path: str | Path) -> pd.DataFrame:
    """Загружает `ml_signals.csv`, оставляя только последнюю ненулевую строку на время."""
    df = pd.read_csv(path, sep=";")
    df["signal_time"] = pd.to_datetime(df["time"], format=TIME_FORMAT, errors="coerce")
    df["signal"] = pd.to_numeric(df["signal"], errors="coerce")
    df["direction"] = df["signal"].map({1: "BUY", -1: "SELL"})
    df = df[df["direction"].notna() & df["signal_time"].notna()].copy()
    df = df.drop_duplicates(subset=["signal_time"], keep="last")
    return df[["signal_time", "signal", "direction"]].sort_values("signal_time").reset_index(drop=True)


def filter_time_window(df: pd.DataFrame, column: str, start_time: str | None, end_time: str | None) -> pd.DataFrame:
    start = parse_time(start_time)
    end = parse_time(end_time)
    out = df.copy()
    if start is not None:
        out = out[out[column] >= start]
    if end is not None:
        out = out[out[column] <= end]
    return out.reset_index(drop=True)


def filter_events_window(events: pd.DataFrame, start_time: str | None, end_time: str | None) -> pd.DataFrame:
    """Фильтрует OPEN/OPEN_FAILED по signal_time, но сохраняет CLOSE для связи по ticket."""
    start = parse_time(start_time)
    end = parse_time(end_time)
    if start is None and end is None:
        return events.reset_index(drop=True)

    open_like = events["event"].isin(["OPEN", "OPEN_FAILED"])
    mask = ~open_like
    if start is not None:
        mask |= open_like & (events["signal_time"] >= start)
    else:
        mask |= open_like
    if end is not None:
        mask &= (~open_like) | (events["signal_time"] <= end)
    return events[mask].reset_index(drop=True)


def _dedupe_events(events: pd.DataFrame, event_type: str) -> pd.DataFrame:
    subset = events[events["event"] == event_type].copy()
    if subset.empty:
        return subset
    return subset.drop_duplicates(subset=["signal_time", "direction"], keep="last")


def match_signals_to_trades(signals: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    """Сверяет ожидаемые сигналы с OPEN/OPEN_FAILED по `signal_time + direction`."""
    expected = signals[["signal_time", "signal", "direction"]].copy()
    open_cols = ["signal_time", "direction", "ticket", "entry_time", "atr", "spread", "spread_atr", "open_positions"]
    opens = _dedupe_events(events, "OPEN")
    failed = _dedupe_events(events, "OPEN_FAILED")
    if opens.empty:
        opens = pd.DataFrame(columns=open_cols)
    if failed.empty:
        failed = pd.DataFrame(columns=["signal_time", "direction", "reason"])

    merged = expected.merge(opens[[c for c in open_cols if c in opens.columns]], on=["signal_time", "direction"], how="left")
    merged = merged.merge(
        failed[[c for c in ("signal_time", "direction", "reason") if c in failed.columns]].rename(columns={"reason": "failed_reason"}),
        on=["signal_time", "direction"],
        how="left",
    )

    any_open = opens[["signal_time", "direction"]].rename(columns={"direction": "opened_direction"})
    merged = merged.merge(any_open, on="signal_time", how="left")
    exact_open = merged["ticket"].notna()
    exact_failed = merged["failed_reason"].notna()
    wrong_direction = (~exact_open) & (~exact_failed) & merged["opened_direction"].notna()
    merged["status"] = "missing_open"
    merged.loc[exact_open, "status"] = "executed"
    merged.loc[exact_failed, "status"] = "open_failed"
    merged.loc[wrong_direction, "status"] = "wrong_direction"
    merged["critical"] = merged["status"].isin(["missing_open", "open_failed", "wrong_direction"])
    return merged.drop_duplicates(subset=["signal_time", "direction"], keep="first").reset_index(drop=True)


def build_trades(events: pd.DataFrame) -> pd.DataFrame:
    """Связывает OPEN и CLOSE по ticket, сохраняя незакрытый хвост."""
    opens = events[events["event"] == "OPEN"].copy()
    closes = events[events["event"] == "CLOSE"].copy()
    if opens.empty:
        return pd.DataFrame()

    close_cols = [
        "ticket",
        "exit_time",
        "reason",
        "close",
        "order_close_price",
        "profit",
        "swap",
        "commission",
        "hold_bars",
        "balance",
        "equity",
    ]
    available_close_cols = [c for c in close_cols if c in closes.columns]
    trades = opens.merge(closes[available_close_cols], on="ticket", how="left", suffixes=("_open", "_close"))
    if "profit_close" in trades.columns:
        zero = pd.Series(0.0, index=trades.index)
        trades["pnl"] = (
            trades["profit_close"].fillna(0)
            + trades.get("swap_close", zero).fillna(0)
            + trades.get("commission_close", zero).fillna(0)
        )
        trades.loc[trades["exit_time_close"].isna(), "pnl"] = pd.NA
    else:
        trades["pnl"] = pd.NA
    trades["close_status"] = trades["exit_time_close"].notna().map({True: "closed", False: "open"})
    return trades.sort_values(["signal_time", "direction", "ticket"]).reset_index(drop=True)


def build_closed_trades(events: pd.DataFrame) -> pd.DataFrame:
    """Обратимо-совместимый helper: возвращает только закрытые сделки."""
    trades = build_trades(events)
    if trades.empty:
        return trades
    return trades[trades["close_status"] == "closed"].reset_index(drop=True)


def _profit_factor(pnl: pd.Series) -> float:
    gross_profit = pnl[pnl > 0].sum()
    gross_loss = abs(pnl[pnl < 0].sum())
    return float(gross_profit / gross_loss) if gross_loss > 0 else float("inf")


def compute_trade_stats(trades: pd.DataFrame, label: str = "") -> dict[str, Any]:
    """Считает торговые характеристики по закрытым сделкам."""
    if trades.empty:
        return {"label": label, "total_trades": 0, "expectancy": 0.0}
    closed = trades[trades.get("close_status", "closed") == "closed"].copy()
    if closed.empty:
        return {"label": label, "total_trades": 0, "expectancy": 0.0}

    closed = closed.sort_values("exit_time_close")
    pnl = closed["pnl"].astype(float)
    reason_col = "reason_close" if "reason_close" in closed.columns else "reason"
    total_profit = pnl.sum()
    wins = int((pnl > 0).sum())
    losses = int((pnl < 0).sum())
    breakeven = int((pnl == 0).sum())
    total = len(closed)
    win_rate = wins / total * 100 if total > 0 else 0
    avg_profit = pnl.mean()
    avg_win = pnl[pnl > 0].mean() if wins > 0 else 0
    avg_loss = pnl[pnl < 0].mean() if losses > 0 else 0
    pf = _profit_factor(pnl)
    max_dd = (pnl.cumsum().cummax() - pnl.cumsum()).max()

    by_reason = {}
    for reason, grp in closed.groupby(reason_col):
        grp_pnl = grp["pnl"].astype(float)
        by_reason[reason] = {
            "count": len(grp),
            "profit": round(grp_pnl.sum(), 2),
            "avg_profit": round(grp_pnl.mean(), 2),
            "win_rate": round((grp_pnl > 0).sum() / len(grp) * 100, 1),
        }

    by_direction = {}
    for d, grp in closed.groupby("direction"):
        grp_pnl = grp["pnl"].astype(float)
        by_direction[d] = {
            "count": len(grp),
            "profit": round(grp_pnl.sum(), 2),
            "win_rate": round((grp_pnl > 0).sum() / len(grp) * 100, 1),
        }

    delay = (closed["entry_time"] - closed["signal_time"]).dt.total_seconds() / 60
    spread_atr = closed["spread_atr"].describe().to_dict() if "spread_atr" in closed.columns else {}

    return {
        "label": label,
        "total_trades": total,
        "total_profit": round(total_profit, 2),
        "expectancy": round(avg_profit, 4),
        "wins": int(wins),
        "losses": int(losses),
        "breakeven": int(breakeven),
        "win_rate_pct": round(win_rate, 1),
        "avg_profit": round(avg_profit, 2),
        "avg_win": round(avg_win, 2),
        "avg_loss": round(avg_loss, 2),
        "profit_factor": round(pf, 4),
        "max_drawdown": round(max_dd, 2),
        "by_reason": by_reason,
        "by_direction": by_direction,
        "delay_minutes": {
            "mean": round(delay.mean(), 1),
            "median": round(delay.median(), 1),
            "max": round(delay.max(), 1),
            "std": round(delay.std(), 1),
        },
        "spread_atr": {k: round(v, 4) for k, v in spread_atr.items()},
    }


def compute_signal_basis_stats(signals: pd.DataFrame, trades: pd.DataFrame, label: str) -> dict[str, Any]:
    """Считает матожидание на ожидаемый сигнал, где пропуск/хвост дают PnL=0."""
    if signals.empty:
        return {"label": label, "expected_signals": 0, "expectancy": 0.0}
    if trades.empty:
        pnl = pd.Series([0.0] * len(signals))
    else:
        trade_pnl = trades[["signal_time", "direction", "pnl"]].copy()
        trade_pnl = trade_pnl.drop_duplicates(subset=["signal_time", "direction"], keep="last")
        ledger = signals[["signal_time", "direction"]].merge(trade_pnl, on=["signal_time", "direction"], how="left")
        pnl = ledger["pnl"].fillna(0).astype(float)
    return {
        "label": label,
        "expected_signals": int(len(signals)),
        "total_profit": round(float(pnl.sum()), 2),
        "expectancy": round(float(pnl.mean()), 4),
        "wins": int((pnl > 0).sum()),
        "losses": int((pnl < 0).sum()),
        "breakeven": int((pnl == 0).sum()),
        "profit_factor": round(_profit_factor(pnl), 4),
    }


def compare_online_tester(online_trades: pd.DataFrame, tester_trades: pd.DataFrame) -> pd.DataFrame:
    if tester_trades.empty:
        return pd.DataFrame()
    key = ["signal_time", "direction"]
    cols = key + ["ticket", "entry_time", "exit_time_close", "reason_close", "entry", "close_close", "pnl", "hold_bars_close"]
    online_paired = online_trades[[c for c in cols if c in online_trades.columns]].copy()
    tester_paired = tester_trades[[c for c in cols if c in tester_trades.columns]].copy()
    merged = online_paired.merge(tester_paired, on=key, how="outer", suffixes=("_online", "_tester"), indicator=True)
    merged["match_status"] = merged["_merge"].map({"both": "matched", "left_only": "online_only", "right_only": "tester_only"})
    merged["pnl_diff"] = merged["pnl_online"] - merged["pnl_tester"]
    return merged


def _paired_summary(comparison: pd.DataFrame) -> dict[str, Any] | None:
    if comparison.empty:
        return None
    paired = comparison[
        (comparison["match_status"] == "matched")
        & comparison["pnl_online"].notna()
        & comparison["pnl_tester"].notna()
    ].copy()
    if paired.empty:
        return {"paired_closed_trades": 0}
    diff = paired["pnl_diff"].astype(float)
    return {
        "paired_closed_trades": int(len(paired)),
        "online_total_profit": round(float(paired["pnl_online"].sum()), 2),
        "tester_total_profit": round(float(paired["pnl_tester"].sum()), 2),
        "pnl_diff_total": round(float(diff.sum()), 2),
        "online_expectancy": round(float(paired["pnl_online"].mean()), 4),
        "tester_expectancy": round(float(paired["pnl_tester"].mean()), 4),
        "pnl_diff_expectancy": round(float(diff.mean()), 4),
        "abs_diff_mean": round(float(diff.abs().mean()), 4),
        "abs_diff_max": round(float(diff.abs().max()), 4),
    }


def generate_summary(summary: dict[str, Any], output_dir: Path) -> None:
    """Пишет JSON и краткий Markdown summary."""
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")

    signals = summary["signals"]
    online_closed = summary["online"]["closed_trades"]
    online_signal = summary["online"]["signal_basis"]
    summary = {
        **summary,
        "signals": signals,
        "online_closed": online_closed,
        "online_signal": online_signal,
    }
    lines = [
        "# Online / Tester Reconciliation",
        "",
        "## Signal Matching",
        "| Metric | Value |",
        "|---|---:|",
        f"| Expected signals | {signals['expected']} |",
        f"| Executed | {signals['executed']} |",
        f"| Open failed | {signals['open_failed']} |",
        f"| Missing open | {signals['missing_open']} |",
        f"| Wrong direction | {signals['wrong_direction']} |",
        "",
        "## Online Trade Statistics",
        "| Metric | Closed trades | Signal basis |",
        "|---|---:|---:|",
        f"| Total profit | {online_closed.get('total_profit', 0)} | {online_signal.get('total_profit', 0)} |",
        f"| Expectancy | {online_closed.get('expectancy', 0)} | {online_signal.get('expectancy', 0)} |",
        f"| Win rate % | {online_closed.get('win_rate_pct', 0)} | - |",
        f"| Profit factor | {online_closed.get('profit_factor', 0)} | {online_signal.get('profit_factor', 0)} |",
    ]
    tester = summary.get("tester")
    if tester:
        tester_closed = tester["closed_trades"]
        tester_signal = tester["signal_basis"]
        lines += [
            "",
            "## Tester Trade Statistics",
            "| Metric | Closed trades | Signal basis |",
            "|---|---:|---:|",
            f"| Total profit | {tester_closed.get('total_profit', 0)} | {tester_signal.get('total_profit', 0)} |",
            f"| Expectancy | {tester_closed.get('expectancy', 0)} | {tester_signal.get('expectancy', 0)} |",
            f"| Win rate % | {tester_closed.get('win_rate_pct', 0)} | - |",
            f"| Profit factor | {tester_closed.get('profit_factor', 0)} | {tester_signal.get('profit_factor', 0)} |",
        ]
    paired = summary.get("paired")
    if paired:
        lines += [
            "",
            "## Paired Closed Trades",
            "| Metric | Value |",
            "|---|---:|",
            f"| Paired closed trades | {paired.get('paired_closed_trades', 0)} |",
            f"| Online total profit | {paired.get('online_total_profit', 0)} |",
            f"| Tester total profit | {paired.get('tester_total_profit', 0)} |",
            f"| PnL diff total | {paired.get('pnl_diff_total', 0)} |",
            f"| PnL diff expectancy | {paired.get('pnl_diff_expectancy', 0)} |",
        ]

    (output_dir / "summary.md").write_text("\n".join(lines), encoding="utf-8")


def run_reconciliation(
    events_path: str | Path,
    signals_path: str | Path,
    output_dir: str | Path,
    tester_events_path: str | Path | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    events = load_events(events_path)
    signals = filter_time_window(load_signals(signals_path), "signal_time", start_time, end_time)
    events = filter_events_window(events, start_time, end_time)

    signals_diff = match_signals_to_trades(signals, events)
    online_trades = build_trades(events)
    online_closed = build_closed_trades(events)
    online_trades.to_csv(output / "online_trades.csv", index=False, sep=";")
    online_closed.to_csv(output / "online_closed_trades.csv", index=False, sep=";")
    signals_diff.to_csv(output / "signals_diff.csv", index=False, sep=";")

    status_counts = signals_diff["status"].value_counts()
    summary: dict[str, Any] = {
        "signals": {
            "expected": int(len(signals_diff)),
            "executed": int(status_counts.get("executed", 0)),
            "open_failed": int(status_counts.get("open_failed", 0)),
            "missing_open": int(status_counts.get("missing_open", 0)),
            "wrong_direction": int(status_counts.get("wrong_direction", 0)),
            "critical_mismatch_count": int(signals_diff["critical"].sum()),
        },
        "online": {
            "closed_trades": compute_trade_stats(online_trades, label="online_closed"),
            "signal_basis": compute_signal_basis_stats(signals, online_trades, label="online_signal_basis"),
        },
        "tester": None,
        "paired": None,
    }

    if tester_events_path:
        tester_events = load_events(tester_events_path)
        tester_events = filter_events_window(tester_events, start_time, end_time)
        tester_trades = build_trades(tester_events)
        tester_closed = build_closed_trades(tester_events)
        tester_trades.to_csv(output / "tester_trades.csv", index=False, sep=";")
        tester_closed.to_csv(output / "tester_closed_trades.csv", index=False, sep=";")
        comparison = compare_online_tester(online_trades, tester_trades)
        comparison.to_csv(output / "trades_comparison.csv", index=False, sep=";")
        summary["tester"] = {
            "closed_trades": compute_trade_stats(tester_trades, label="tester_closed"),
            "signal_basis": compute_signal_basis_stats(signals, tester_trades, label="tester_signal_basis"),
        }
        summary["paired"] = _paired_summary(comparison)

    generate_summary(summary, output)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Online/Tester trade reconciliation")
    parser.add_argument("--events", required=True, help="Path to online ml_trade_events.csv")
    parser.add_argument("--signals", required=True, help="Path to ml_signals.csv")
    parser.add_argument("--output-dir", required=True, help="Output directory")
    parser.add_argument("--tester-events", default=None, help="Path to tester ml_trade_events.csv")
    parser.add_argument("--start-time", default=None, help="Optional inclusive start time: YYYY.MM.DD HH:MM")
    parser.add_argument("--end-time", default=None, help="Optional inclusive end time: YYYY.MM.DD HH:MM")
    args = parser.parse_args()

    summary = run_reconciliation(
        events_path=args.events,
        signals_path=args.signals,
        output_dir=args.output_dir,
        tester_events_path=args.tester_events,
        start_time=args.start_time,
        end_time=args.end_time,
    )

    print(f"Reconciliation saved to {args.output_dir}")
    print(
        f"  Signals: {summary['signals']['expected']}, "
        f"Executed: {summary['signals']['executed']}, "
        f"Open failed: {summary['signals']['open_failed']}, "
        f"Missing open: {summary['signals']['missing_open']}"
    )
    online_stats = summary["online"]["closed_trades"]
    print(
        f"  Online closed: {online_stats.get('total_trades', 0)} trades, "
        f"PF={online_stats.get('profit_factor', 0)}, "
        f"EV={online_stats.get('expectancy', 0)}, "
        f"PnL={online_stats.get('total_profit', 0)}"
    )

    if summary["signals"]["wrong_direction"] > 0:
        print("WARNING: Direction mismatches detected!", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
