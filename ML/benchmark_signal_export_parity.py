# =============================================================================
# Файл: benchmark_signal_export_parity.py
# Назначение: Диагностика соответствия exported ml_signals.csv и MT4 tester log
# Обновлён: 2026-04-22
# Входные данные:
#   - ml_signals.csv (откуда: API/export_take_skip_trailing_stop_v2_signals.py или другой exporter)
#   - optional MT4 tester log (откуда: MT/tester/logs/*.log)
# Выходные данные:
#   - summary.json / summary.md (куда: output-dir)
# Использование:
#   python -m ML.benchmark_signal_export_parity --signals MT/tester/files/ml_signals.csv --mt4-log MT/tester/logs/20260420.log
# Примечания:
#   - инструмент ничего не схлопывает и не меняет в сигналах, только считает parity-метрики
# =============================================================================

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd


DEFAULT_OUTPUT_DIR = Path("ML/reports/signal_export_parity")


def _to_int_signal(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(0).astype(int)


def analyze_signal_export(signals_path: str | Path) -> dict[str, Any]:
    """Считает строковую и временную структуру exported signal CSV."""
    path = Path(signals_path)
    frame = pd.read_csv(path, sep=";", usecols=["time", "signal"])
    frame["time"] = frame["time"].astype(str)
    frame["signal"] = _to_int_signal(frame["signal"])

    nonzero = frame[frame["signal"] != 0].copy()

    time_counts = Counter(nonzero["time"])
    time_signal_counts = Counter(zip(nonzero["time"], nonzero["signal"]))

    duplicate_time_examples = [
        {"time": time, "rows": count}
        for time, count in sorted(time_counts.items())
        if count > 1
    ][:20]
    duplicate_time_signal_examples = [
        {"time": time, "signal": int(signal), "rows": count}
        for (time, signal), count in sorted(time_signal_counts.items())
        if count > 1
    ][:20]

    by_time = nonzero.groupby("time")["signal"].nunique() if not nonzero.empty else pd.Series(dtype=int)
    same_time_opposite_signal_groups = int((by_time > 1).sum())

    return {
        "signals_path": str(path),
        "rows_total": int(len(frame)),
        "nonzero_rows": int(len(nonzero)),
        "zero_rows": int((frame["signal"] == 0).sum()),
        "long_rows": int((nonzero["signal"] > 0).sum()),
        "short_rows": int((nonzero["signal"] < 0).sum()),
        "unique_time_total": int(frame["time"].nunique()),
        "nonzero_unique_time": int(nonzero["time"].nunique()),
        "nonzero_unique_time_signal": int(len(nonzero.drop_duplicates(["time", "signal"]))),
        "duplicate_time_rows": int(sum(count - 1 for count in time_counts.values() if count > 1)),
        "duplicate_time_signal_rows": int(sum(count - 1 for count in time_signal_counts.values() if count > 1)),
        "duplicate_time_groups": int(sum(1 for count in time_counts.values() if count > 1)),
        "duplicate_time_signal_groups": int(sum(1 for count in time_signal_counts.values() if count > 1)),
        "same_time_opposite_signal_groups": same_time_opposite_signal_groups,
        "first_nonzero_time": str(nonzero["time"].iloc[0]) if not nonzero.empty else None,
        "last_nonzero_time": str(nonzero["time"].iloc[-1]) if not nonzero.empty else None,
        "duplicate_time_examples": duplicate_time_examples,
        "duplicate_time_signal_examples": duplicate_time_signal_examples,
    }


def _last_int(pattern: str, text: str) -> int | None:
    matches = re.findall(pattern, text, flags=re.MULTILINE)
    if not matches:
        return None
    return int(matches[-1])


def parse_mt4_log(mt4_log_path: str | Path) -> dict[str, Any]:
    """Извлекает MLP open events и финальные MLP diagnostics из tester log."""
    path = Path(mt4_log_path)
    text = path.read_text(encoding="utf-8", errors="replace")

    open_pattern = re.compile(
        r"MLP\s+(BUY|SELL)\b.*?signal_time=(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2})",
        flags=re.MULTILINE,
    )
    events = open_pattern.findall(text)
    directions = [direction for direction, _signal_time in events]
    signal_times = [signal_time for _direction, signal_time in events]

    diagnostics_text = text
    mlp_match = re.search(r"=== MLP DIAGNOSTICS ===(?P<body>.*?)(?:=== TB DIAGNOSTICS ===|$)", text, re.DOTALL)
    if mlp_match:
        diagnostics_text = mlp_match.group("body")
    elif "=== TB DIAGNOSTICS ===" in text:
        diagnostics_text = text.split("=== TB DIAGNOSTICS ===", 1)[0]

    diagnostics = {
        "total_signals": _last_int(r"Total signals:\s+(\d+)", diagnostics_text),
        "score_filtered": _last_int(r"Score filtered:\s+(\d+)", diagnostics_text),
        "position_blocked": _last_int(r"Position blocked:\s+(\d+)", diagnostics_text),
        "opened": _last_int(r"Opened:\s+(\d+)", diagnostics_text),
        "timeout_closes": _last_int(r"Timeout closes:\s+(\d+)", diagnostics_text),
        "trailing_closes": _last_int(r"Trailing closes:\s+(\d+)", diagnostics_text),
        "reverse_closes": _last_int(r"Reverse closes:\s+(\d+)", diagnostics_text),
    }

    return {
        "mt4_log_path": str(path),
        "opened_trades_from_events": int(len(events)),
        "opened_buy_from_events": int(sum(1 for direction in directions if direction == "BUY")),
        "opened_sell_from_events": int(sum(1 for direction in directions if direction == "SELL")),
        "unique_signal_times_opened": int(len(set(signal_times))),
        "duplicate_open_signal_time_rows": int(len(signal_times) - len(set(signal_times))),
        "first_open_signal_time": signal_times[0] if signal_times else None,
        "last_open_signal_time": signal_times[-1] if signal_times else None,
        "diagnostics": diagnostics,
    }


def build_summary(
    *,
    signals_path: str | Path,
    mt4_log_path: str | Path | None = None,
    label: str = "signal_export_parity",
) -> dict[str, Any]:
    export = analyze_signal_export(signals_path)
    mt4 = parse_mt4_log(mt4_log_path) if mt4_log_path is not None else None

    summary: dict[str, Any] = {
        "label": label,
        "export": export,
        "mt4": mt4,
    }

    if mt4 is not None:
        summary["comparison"] = {
            "nonzero_rows_minus_opened_events": export["nonzero_rows"] - mt4["opened_trades_from_events"],
            "unique_time_minus_opened_events": export["nonzero_unique_time"] - mt4["opened_trades_from_events"],
            "unique_time_signal_minus_opened_events": export["nonzero_unique_time_signal"]
            - mt4["opened_trades_from_events"],
            "mt4_diagnostics_opened_minus_opened_events": (
                None
                if mt4["diagnostics"]["opened"] is None
                else mt4["diagnostics"]["opened"] - mt4["opened_trades_from_events"]
            ),
        }

    return summary


def render_markdown(summary: dict[str, Any]) -> str:
    export = summary["export"]
    mt4 = summary.get("mt4")
    lines = [
        f"# Signal Export Parity — {summary['label']}",
        "",
        "## Export",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| rows_total | {export['rows_total']} |",
        f"| nonzero_rows | {export['nonzero_rows']} |",
        f"| nonzero_unique_time | {export['nonzero_unique_time']} |",
        f"| nonzero_unique_time_signal | {export['nonzero_unique_time_signal']} |",
        f"| duplicate_time_rows | {export['duplicate_time_rows']} |",
        f"| duplicate_time_signal_rows | {export['duplicate_time_signal_rows']} |",
        f"| same_time_opposite_signal_groups | {export['same_time_opposite_signal_groups']} |",
    ]

    if mt4 is not None:
        diagnostics = mt4["diagnostics"]
        lines += [
            "",
            "## MT4",
            "",
            "| Metric | Value |",
            "|---|---:|",
            f"| opened_trades_from_events | {mt4['opened_trades_from_events']} |",
            f"| opened_buy_from_events | {mt4['opened_buy_from_events']} |",
            f"| opened_sell_from_events | {mt4['opened_sell_from_events']} |",
            f"| unique_signal_times_opened | {mt4['unique_signal_times_opened']} |",
            f"| diagnostics.opened | {diagnostics['opened']} |",
            f"| diagnostics.position_blocked | {diagnostics['position_blocked']} |",
            f"| diagnostics.score_filtered | {diagnostics['score_filtered']} |",
        ]
        comparison = summary["comparison"]
        lines += [
            "",
            "## Comparison",
            "",
            "| Metric | Value |",
            "|---|---:|",
            f"| nonzero_rows_minus_opened_events | {comparison['nonzero_rows_minus_opened_events']} |",
            f"| unique_time_minus_opened_events | {comparison['unique_time_minus_opened_events']} |",
            f"| unique_time_signal_minus_opened_events | {comparison['unique_time_signal_minus_opened_events']} |",
        ]

    if export["duplicate_time_signal_examples"]:
        lines += ["", "## Duplicate time+signal examples", "", "| time | signal | rows |", "|---|---:|---:|"]
        for item in export["duplicate_time_signal_examples"]:
            lines.append(f"| {item['time']} | {item['signal']} | {item['rows']} |")

    return "\n".join(lines) + "\n"


def run_benchmark(
    *,
    signals_path: str | Path,
    mt4_log_path: str | Path | None,
    output_dir: str | Path,
    label: str,
) -> dict[str, Any]:
    summary = build_summary(signals_path=signals_path, mt4_log_path=mt4_log_path, label=label)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "summary.md").write_text(render_markdown(summary), encoding="utf-8")
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare exported ml_signals.csv rows with optional MT4 tester log.")
    parser.add_argument("--signals", required=True, help="Path to exported time;signal CSV.")
    parser.add_argument("--mt4-log", default=None, help="Optional MT4 tester log path.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Output directory for summary.json/md.")
    parser.add_argument("--label", default="signal_export_parity", help="Label stored in summary files.")
    return parser.parse_args()


def main() -> dict[str, Any]:
    args = parse_args()
    summary = run_benchmark(
        signals_path=args.signals,
        mt4_log_path=args.mt4_log,
        output_dir=args.output_dir,
        label=args.label,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return summary


if __name__ == "__main__":
    main()
