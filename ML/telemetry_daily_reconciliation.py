# =============================================================================
# Файл: telemetry_daily_reconciliation.py
# Назначение: Ежедневная сверка telemetry ML-сигналов, MT4 open/close log и export metadata.
# Обновлён: 2026-04-27
# Входные данные:
#   - ml_signals.csv (откуда: API/export_take_skip_trailing_stop_v2_signals.py)
#   - MT4 log со строками MLP BUY/SELL/CLOSE (откуда: tester/runtime log)
#   - optional export_metadata.json (откуда: telemetry export)
# Выходные данные:
#   - summary.json, summary.md, signals_diff.csv, trades_reconciliation.csv
# Использование:
#   python -m ML.telemetry_daily_reconciliation --signals ... --mt4-log ... --output-dir ...
# Примечания:
#   - non-zero exit code означает критичные расхождения в daily reconciliation.
# =============================================================================

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import pandas as pd


OPEN_RE = re.compile(r"\bMLP\s+(BUY|SELL)\b(?!.*reason=)")
CLOSE_RE = re.compile(r"\bMLP\s+CLOSE\s+(BUY|SELL)\b")
KEY_VALUE_RE = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)=(.*?)(?=\s+[A-Za-z_][A-Za-z0-9_]*=|$)")


def _parse_key_values(line: str) -> dict[str, str]:
    return {key: value.strip() for key, value in KEY_VALUE_RE.findall(line)}


def _to_int(value: str | None, default: int = 0) -> int:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return default


def _to_float(value: str | None, default: float = 0.0) -> float:
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return default


def parse_mlp_events(log_path: str | Path) -> dict[str, pd.DataFrame]:
    """Парсит MLP open/close события из MT4 log."""
    opens: list[dict[str, Any]] = []
    closes: list[dict[str, Any]] = []
    text = Path(log_path).read_text(encoding="utf-8", errors="replace")

    for line in text.splitlines():
        close_match = CLOSE_RE.search(line)
        if close_match:
            fields = _parse_key_values(line)
            closes.append(
                {
                    "ticket": _to_int(fields.get("ticket")),
                    "direction": close_match.group(1),
                    "reason": fields.get("reason", ""),
                    "entry_time": fields.get("entry_time", ""),
                    "exit_time": fields.get("exit_time", ""),
                    "hold_bars": _to_int(fields.get("hold_bars")),
                    "entry": _to_float(fields.get("entry")),
                    "exit": _to_float(fields.get("exit")),
                    "atr": _to_float(fields.get("atr")),
                    "spread": _to_float(fields.get("spread")),
                    "spread_atr": _to_float(fields.get("spread_atr")),
                    "pnl_atr": _to_float(fields.get("pnl_atr")),
                    "profit": _to_float(fields.get("profit")),
                    "raw_line": line,
                }
            )
            continue

        open_match = OPEN_RE.search(line)
        if open_match:
            fields = _parse_key_values(line)
            opens.append(
                {
                    "ticket": _to_int(fields.get("ticket")),
                    "direction": open_match.group(1),
                    "mode": fields.get("mode", ""),
                    "signal_time": fields.get("signal_time", ""),
                    "entry_time": fields.get("entry_time", ""),
                    "score": _to_float(fields.get("score")),
                    "atr": _to_float(fields.get("atr")),
                    "spread": _to_float(fields.get("spread")),
                    "spread_atr": _to_float(fields.get("spread_atr")),
                    "open_positions": _to_int(fields.get("open_positions")),
                    "max_positions": _to_int(fields.get("max_positions") or fields.get("MaxPositions")),
                    "entry": _to_float(fields.get("Val")),
                    "stop": _to_float(fields.get("Stp")),
                    "take_profit": _to_float(fields.get("Prf")),
                    "lot": _to_float(fields.get("Lot")),
                    "raw_line": line,
                }
            )

    return {
        "opens": pd.DataFrame(opens),
        "closes": pd.DataFrame(closes),
    }


def load_signal_export(signals_path: str | Path) -> pd.DataFrame:
    """Загружает `time;signal` export и оставляет ожидаемые ненулевые сигналы."""
    frame = pd.read_csv(Path(signals_path), sep=";", usecols=["time", "signal"])
    frame["time"] = frame["time"].astype(str)
    frame["signal"] = pd.to_numeric(frame["signal"], errors="coerce").fillna(0).astype(int)
    frame = frame.drop_duplicates(subset=["time"], keep="last").reset_index(drop=True)
    expected = frame.loc[frame["signal"] != 0].copy()
    expected["direction"] = expected["signal"].map({1: "BUY", -1: "SELL"}).fillna("UNKNOWN")
    expected = expected.rename(columns={"time": "signal_time"})
    return expected[["signal_time", "signal", "direction"]].reset_index(drop=True)


def filter_signals_by_time_range(
    signals: pd.DataFrame,
    *,
    start_time: str | None = None,
    end_time: str | None = None,
) -> pd.DataFrame:
    """Оставляет ожидаемые сигналы только внутри периода сверки."""
    if signals.empty or (start_time is None and end_time is None):
        return signals.reset_index(drop=True)

    parsed = pd.to_datetime(signals["signal_time"], format="%Y.%m.%d %H:%M", errors="coerce")
    mask = pd.Series(True, index=signals.index)
    if start_time is not None:
        start = pd.to_datetime(start_time, format="%Y.%m.%d %H:%M", errors="raise")
        mask &= parsed >= start
    if end_time is not None:
        end = pd.to_datetime(end_time, format="%Y.%m.%d %H:%M", errors="raise")
        mask &= parsed <= end
    return signals.loc[mask].reset_index(drop=True)


def reconcile_expected_vs_opened(signals: pd.DataFrame, opens: pd.DataFrame) -> pd.DataFrame:
    """Сравнивает ожидаемые signal rows с фактическими MLP open events."""
    rows: list[dict[str, Any]] = []
    open_pairs = set()
    if not opens.empty:
        open_pairs = set(zip(opens["signal_time"].astype(str), opens["direction"].astype(str)))

    for signal in signals.to_dict("records"):
        pair = (str(signal["signal_time"]), str(signal["direction"]))
        time_opens = opens.loc[opens["signal_time"].astype(str) == pair[0]] if not opens.empty else pd.DataFrame()
        if pair in open_pairs:
            status = "opened"
            critical = False
        elif not time_opens.empty:
            status = "wrong_direction"
            critical = True
        else:
            status = "missing_open"
            critical = True
        rows.append(
            {
                "signal_time": pair[0],
                "expected_direction": pair[1],
                "status": status,
                "critical": bool(critical),
            }
        )

    expected_times = set(signals["signal_time"].astype(str)) if not signals.empty else set()
    if not opens.empty:
        for item in opens.to_dict("records"):
            if str(item["signal_time"]) not in expected_times:
                rows.append(
                    {
                        "signal_time": str(item["signal_time"]),
                        "expected_direction": "",
                        "actual_direction": str(item["direction"]),
                        "status": "unexpected_open",
                        "critical": True,
                    }
                )

    out = pd.DataFrame(rows)
    if "critical" in out.columns:
        out["critical"] = out["critical"].astype(object)
    return out


def reconcile_open_close(opens: pd.DataFrame, closes: pd.DataFrame) -> pd.DataFrame:
    """Связывает open/close события по ticket."""
    if opens.empty:
        return pd.DataFrame()
    close_by_ticket = closes.set_index("ticket") if not closes.empty else pd.DataFrame()
    rows: list[dict[str, Any]] = []
    for item in opens.to_dict("records"):
        ticket = int(item["ticket"])
        row = dict(item)
        if not close_by_ticket.empty and ticket in close_by_ticket.index:
            close = close_by_ticket.loc[ticket]
            if isinstance(close, pd.DataFrame):
                close = close.iloc[-1]
            row.update(
                {
                    "close_status": "closed",
                    "close_reason": close.get("reason", ""),
                    "exit_time": close.get("exit_time", ""),
                    "hold_bars": int(close.get("hold_bars", 0)),
                    "pnl_atr": float(close.get("pnl_atr", 0.0)),
                    "profit": float(close.get("profit", 0.0)),
                }
            )
        else:
            row.update({"close_status": "missing_close", "close_reason": "", "pnl_atr": 0.0, "profit": 0.0})
        rows.append(row)
    return pd.DataFrame(rows)


def build_daily_summary(
    *,
    label: str,
    signals: pd.DataFrame,
    opens: pd.DataFrame,
    closes: pd.DataFrame,
    signals_diff: pd.DataFrame,
    trades: pd.DataFrame,
    export_metadata: dict[str, Any] | None,
) -> dict[str, Any]:
    critical_count = int(signals_diff["critical"].map(bool).sum()) if not signals_diff.empty else 0
    missing_closes = int((trades["close_status"] == "missing_close").sum()) if not trades.empty else 0
    return {
        "label": label,
        "expected_signals": int(len(signals)),
        "opened_trades": int(len(opens)),
        "closed_trades": int(len(closes)),
        "critical_mismatch_count": critical_count,
        "missing_close_count": missing_closes,
        "export_metadata": export_metadata,
    }


def render_summary_markdown(summary: dict[str, Any]) -> str:
    lines = [
        f"# Telemetry Daily Reconciliation — {summary['label']}",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| expected_signals | {summary['expected_signals']} |",
        f"| opened_trades | {summary['opened_trades']} |",
        f"| closed_trades | {summary['closed_trades']} |",
        f"| critical_mismatch_count | {summary['critical_mismatch_count']} |",
        f"| missing_close_count | {summary['missing_close_count']} |",
    ]
    return "\n".join(lines) + "\n"


def run_daily_reconciliation(
    *,
    signals_path: str | Path,
    mt4_log_path: str | Path,
    output_dir: str | Path,
    label: str,
    export_metadata_path: str | Path | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
) -> dict[str, Any]:
    signals = load_signal_export(signals_path)
    signals = filter_signals_by_time_range(signals, start_time=start_time, end_time=end_time)
    events = parse_mlp_events(mt4_log_path)
    opens = events["opens"]
    closes = events["closes"]
    signals_diff = reconcile_expected_vs_opened(signals, opens)
    trades = reconcile_open_close(opens, closes)
    export_metadata = None
    if export_metadata_path is not None:
        export_metadata = json.loads(Path(export_metadata_path).read_text(encoding="utf-8"))

    summary = build_daily_summary(
        label=label,
        signals=signals,
        opens=opens,
        closes=closes,
        signals_diff=signals_diff,
        trades=trades,
        export_metadata=export_metadata,
    )

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    signals_diff.to_csv(output / "signals_diff.csv", sep=";", index=False)
    trades.to_csv(output / "trades_reconciliation.csv", sep=";", index=False)
    (output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "summary.md").write_text(render_summary_markdown(summary), encoding="utf-8")
    return summary


def exit_code_from_summary(summary: dict[str, Any]) -> int:
    return 1 if int(summary.get("critical_mismatch_count", 0)) > 0 else 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Daily reconciliation for telemetry_frequency_v1.")
    parser.add_argument("--signals", required=True, help="Path to exported time;signal CSV.")
    parser.add_argument("--mt4-log", required=True, help="Path to MT4 tester/runtime log.")
    parser.add_argument("--export-metadata", default=None, help="Optional export metadata JSON.")
    parser.add_argument("--output-dir", required=True, help="Output directory.")
    parser.add_argument("--label", default="telemetry_frequency_v1", help="Label stored in summary.")
    parser.add_argument("--start-time", default=None, help="Optional inclusive start time, format YYYY.MM.DD HH:MM.")
    parser.add_argument("--end-time", default=None, help="Optional inclusive end time, format YYYY.MM.DD HH:MM.")
    return parser.parse_args()


def main() -> dict[str, Any]:
    args = parse_args()
    summary = run_daily_reconciliation(
        signals_path=args.signals,
        mt4_log_path=args.mt4_log,
        export_metadata_path=args.export_metadata,
        output_dir=args.output_dir,
        label=args.label,
        start_time=args.start_time,
        end_time=args.end_time,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    sys.exit(exit_code_from_summary(summary))


if __name__ == "__main__":
    main()
