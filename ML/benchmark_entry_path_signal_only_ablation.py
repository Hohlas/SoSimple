# =============================================================================
# Файл: benchmark_entry_path_signal_only_ablation.py
# Назначение: Ablation benchmark для оценки вклада offline `signal != 0`.
# Обновлён: 2026-05-14
# Входные данные:
#   - entry_path prediction CSV (откуда: `ML.run_entry_path_live_safe_retrain`)
# Выходные данные:
#   - summary JSON/Markdown и selected rows CSV (куда: `ML/reports/...`)
# Использование:
#   python -m ML.benchmark_entry_path_signal_only_ablation
# Примечания:
#   - Не переобучает модель и не меняет frozen rules.
# =============================================================================

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ML.benchmark_entry_path_trade_filter import load_prediction_frame
from ML.entry_path_trade_filter import compute_pf
from ML.entry_path_trade_filter import run_sequential_check


DEFAULT_PREDICTIONS = Path(
    "ML/reports/entry_path_v1_live_safe_xauusd_no_predict_pool_server_multiseed/seed_042/test_predictions.csv"
)
DEFAULT_OUTPUT_DIR = Path("ML/reports/entry_path_v1_signal_only_ablation")
DEFAULT_THRESHOLD = -0.07158749


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if hasattr(value, "item"):
        return value.item()
    return value


def build_signal_only_mask(frame: pd.DataFrame) -> pd.Series:
    return pd.to_numeric(frame["signal"], errors="coerce").fillna(0).astype(int) != 0


def build_current_score_gate_mask(frame: pd.DataFrame, *, threshold: float) -> pd.Series:
    signal_mask = build_signal_only_mask(frame)
    score = pd.to_numeric(frame["pred_ret_24_dir_atr"], errors="coerce").fillna(float("-inf"))
    return signal_mask & (score >= float(threshold))


def _selected_summary(frame: pd.DataFrame, selected_mask: pd.Series, *, min_period_trades: int) -> dict[str, Any]:
    selected = frame.loc[selected_mask].copy()
    pnl = pd.to_numeric(selected["true_ret_24_dir_atr"], errors="coerce").fillna(0.0).to_numpy(dtype=np.float64)
    trades = int(len(selected))
    yearly = _yearly_summary(selected)
    eligible_years = [row for row in yearly if row["trades"] >= min_period_trades]
    negative_years = [row["year"] for row in eligible_years if row["pf"] < 1.0]
    return {
        "trades": trades,
        "pf": compute_pf(pnl),
        "win_rate": float((pnl > 0).mean()) if trades > 0 else 0.0,
        "mean_pnl_atr": float(pnl.mean()) if trades > 0 else 0.0,
        "gross_profit_atr": float(pnl[pnl > 0].sum()),
        "gross_loss_atr": float(-pnl[pnl < 0].sum()),
        "eligible_years": int(len(eligible_years)),
        "negative_years": negative_years,
        "yearly": yearly,
    }


def _yearly_summary(frame: pd.DataFrame) -> list[dict[str, Any]]:
    if frame.empty:
        return []
    work = frame.copy()
    time = pd.to_datetime(work["time"], errors="coerce")
    work = work.loc[time.notna()].copy()
    work["year"] = time.loc[time.notna()].dt.year.to_numpy(dtype=np.int64)
    rows = []
    for year, group in work.groupby("year", sort=True):
        pnl = pd.to_numeric(group["true_ret_24_dir_atr"], errors="coerce").fillna(0.0).to_numpy(dtype=np.float64)
        rows.append(
            {
                "year": int(year),
                "trades": int(len(group)),
                "pf": compute_pf(pnl),
                "win_rate": float((pnl > 0).mean()) if len(group) else 0.0,
                "mean_pnl_atr": float(pnl.mean()) if len(group) else 0.0,
            }
        )
    return rows


def summarize_mask(
    frame: pd.DataFrame,
    *,
    selected_mask: pd.Series,
    label: str,
    min_period_trades: int,
    sequential_hold_bars: int,
) -> dict[str, Any]:
    selected_mask = pd.Series(selected_mask, index=frame.index, dtype=bool)
    sequential = run_sequential_check(frame, selected_mask=selected_mask, hold_bars=sequential_hold_bars)
    return {
        "label": label,
        "selected": _selected_summary(frame, selected_mask, min_period_trades=min_period_trades),
        "sequential": sequential,
    }


def _pf_delta(current_pf: float, signal_only_pf: float) -> float:
    if np.isinf(current_pf) and np.isinf(signal_only_pf):
        return 0.0
    return float(current_pf - signal_only_pf)


def compare_summaries(*, signal_only: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    signal_selected = signal_only["selected"]
    current_selected = current["selected"]
    signal_sequential = signal_only["sequential"]
    current_sequential = current["sequential"]
    return {
        "selected_trade_delta": int(current_selected["trades"] - signal_selected["trades"]),
        "selected_pf_delta": _pf_delta(current_selected["pf"], signal_selected["pf"]),
        "selected_win_rate_delta": float(current_selected["win_rate"] - signal_selected["win_rate"]),
        "selected_mean_pnl_atr_delta": float(current_selected["mean_pnl_atr"] - signal_selected["mean_pnl_atr"]),
        "sequential_trade_delta": int(current_sequential["trades"] - signal_sequential["trades"]),
        "sequential_pf_delta": _pf_delta(current_sequential["pf"], signal_sequential["pf"]),
        "sequential_win_rate_delta": float(current_sequential["win_rate"] - signal_sequential["win_rate"]),
        "sequential_mean_pnl_atr_delta": float(
            current_sequential["mean_pnl_atr"] - signal_sequential["mean_pnl_atr"]
        ),
    }


def _selected_rows_export(frame: pd.DataFrame, signal_only_mask: pd.Series, current_mask: pd.Series) -> pd.DataFrame:
    out = frame.loc[signal_only_mask, ["time", "signal", "pred_ret_24_dir_atr", "true_ret_24_dir_atr"]].copy()
    out["selection"] = np.where(
        pd.Series(current_mask, index=frame.index).loc[out.index].to_numpy(dtype=bool),
        "current_score_gate",
        "signal_only_rejected_by_score",
    )
    return out.reset_index(drop=True)


def _format_metric(value: float) -> str:
    if np.isinf(value):
        return "inf"
    if np.isnan(value):
        return "nan"
    return f"{float(value):.4f}"


def build_report_markdown(payload: dict[str, Any]) -> str:
    signal_only = payload["signal_only"]
    current = payload["current_score_gate"]
    comparison = payload["comparison"]
    lines = [
        "# Entry Path v1 Signal-Only Ablation",
        "",
        "## Context",
        "",
        "Цель: оценить вклад offline `signal != 0` без ML score-фильтра.",
        "",
        "## Inputs",
        "",
        f"- predictions: `{payload['predictions']}`",
        f"- score_threshold: `{payload['score_threshold']}`",
        f"- sequential_hold_bars: `{payload['sequential_hold_bars']}`",
        "",
        "## Summary",
        "",
        "| Mode | Selected trades | Selected PF | Selected win rate | Sequential trades | Sequential PF | Sequential win rate |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for item in [signal_only, current]:
        lines.append(
            "| "
            f"{item['label']} | "
            f"{item['selected']['trades']} | "
            f"{_format_metric(item['selected']['pf'])} | "
            f"{item['selected']['win_rate']:.2%} | "
            f"{item['sequential']['trades']} | "
            f"{_format_metric(item['sequential']['pf'])} | "
            f"{item['sequential']['win_rate']:.2%} |"
        )
    lines.extend(
        [
            "",
            "## Delta: current_score_gate - signal_only",
            "",
            f"- selected_trade_delta: `{comparison['selected_trade_delta']}`",
            f"- selected_pf_delta: `{_format_metric(comparison['selected_pf_delta'])}`",
            f"- selected_mean_pnl_atr_delta: `{comparison['selected_mean_pnl_atr_delta']:.4f}`",
            f"- sequential_trade_delta: `{comparison['sequential_trade_delta']}`",
            f"- sequential_pf_delta: `{_format_metric(comparison['sequential_pf_delta'])}`",
            f"- sequential_mean_pnl_atr_delta: `{comparison['sequential_mean_pnl_atr_delta']:.4f}`",
            "",
            "## Interpretation",
            "",
            "Если `signal_only` уже силён, edge в основном приходит из offline candidate universe. "
            "Если `current_score_gate` заметно лучше, модель вносит дополнительный фильтрующий вклад, "
            "но всё ещё поверх недоступного live `signal`.",
        ]
    )
    return "\n".join(lines)


def run_ablation(
    *,
    predictions: str | Path,
    threshold: float,
    output_dir: str | Path,
    min_period_trades: int = 10,
    sequential_hold_bars: int = 24,
) -> dict[str, Any]:
    predictions_path = Path(predictions)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    frame = load_prediction_frame(predictions_path)
    signal_only_mask = build_signal_only_mask(frame)
    current_mask = build_current_score_gate_mask(frame, threshold=threshold)

    signal_only = summarize_mask(
        frame,
        selected_mask=signal_only_mask,
        label="signal_only",
        min_period_trades=min_period_trades,
        sequential_hold_bars=sequential_hold_bars,
    )
    current = summarize_mask(
        frame,
        selected_mask=current_mask,
        label="current_score_gate",
        min_period_trades=min_period_trades,
        sequential_hold_bars=sequential_hold_bars,
    )
    payload = {
        "predictions": str(predictions_path),
        "score_threshold": float(threshold),
        "min_period_trades": int(min_period_trades),
        "sequential_hold_bars": int(sequential_hold_bars),
        "signal_only": signal_only,
        "current_score_gate": current,
        "comparison": compare_summaries(signal_only=signal_only, current=current),
    }

    selected_rows_path = output_path / "selected_rows.csv"
    summary_path = output_path / "summary.json"
    report_path = output_path / "summary.md"
    _selected_rows_export(frame, signal_only_mask, current_mask).to_csv(selected_rows_path, sep=";", index=False)
    summary_path.write_text(json.dumps(_jsonable(payload), ensure_ascii=False, indent=2), encoding="utf-8")
    report_path.write_text(build_report_markdown(payload), encoding="utf-8")

    return {
        "summary_path": str(summary_path),
        "report_path": str(report_path),
        "selected_rows_path": str(selected_rows_path),
        **payload,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark signal-only ablation for entry_path_v1 live-safe artifacts.")
    parser.add_argument("--predictions", default=str(DEFAULT_PREDICTIONS))
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--min-period-trades", type=int, default=10)
    parser.add_argument("--sequential-hold-bars", type=int, default=24)
    return parser.parse_args()


def main() -> dict[str, Any]:
    args = parse_args()
    result = run_ablation(
        predictions=args.predictions,
        threshold=args.threshold,
        output_dir=args.output_dir,
        min_period_trades=args.min_period_trades,
        sequential_hold_bars=args.sequential_hold_bars,
    )
    print(json.dumps(_jsonable(result), ensure_ascii=False, indent=2))
    return result


if __name__ == "__main__":
    main()
