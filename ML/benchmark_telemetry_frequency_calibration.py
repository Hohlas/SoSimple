# =============================================================================
# Файл: benchmark_telemetry_frequency_calibration.py
# Назначение: Калибровка частого diagnostic telemetry режима поверх take/skip score.
# Обновлён: 2026-04-27
# Входные данные:
#   - prediction CSV с time, signal, pred_take_* (откуда: frozen take/skip export)
# Выходные данные:
#   - calibration_grid.csv, selected_rule.json, summary.json, summary.md
#     (куда: ML/reports/telemetry_frequency_v1/calibration)
# Использование:
#   python -m ML.benchmark_telemetry_frequency_calibration --predictions ... --score-target take_24_x8 --output-dir ...
# Примечания:
#   - PF считается только как диагностика; winner выбирается по частоте сделок.
# =============================================================================

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Iterable

import pandas as pd


DEFAULT_THRESHOLDS: tuple[float, ...] = (0.05, 0.10, 0.15, 0.20, 0.30, 0.40, 0.50)
DEFAULT_TOP_K_VALUES: tuple[float, ...] = (0.20, 0.30, 0.40, 0.50, 0.70, 1.00)
DEFAULT_OUTPUT_DIR = Path("ML/reports/telemetry_frequency_v1/calibration")
DEFAULT_STOP_ATR = 3.0
DEFAULT_TAKE_PROFIT_ATR = 5.0
DEFAULT_MAX_HOLD_BARS = 24
DEFAULT_MAX_POSITIONS = 10


def load_prediction_frame(path: str | Path) -> pd.DataFrame:
    """Загружает prediction CSV и проверяет базовый контракт telemetry calibration."""
    frame = pd.read_csv(Path(path), sep=";")
    missing = {"time", "signal"}.difference(frame.columns)
    if missing:
        raise ValueError(f"prediction CSV missing required columns: {sorted(missing)}")
    frame = frame.copy()
    frame["time"] = frame["time"].astype(str)
    frame["signal"] = pd.to_numeric(frame["signal"], errors="coerce").fillna(0).astype(int)
    return frame


def _coverage_days(frame: pd.DataFrame) -> int:
    if frame.empty:
        return 1
    times = pd.to_datetime(frame["time"], format="%Y.%m.%d %H:%M", errors="coerce")
    times = times.dropna()
    if times.empty:
        return 1
    return max(1, int((times.max().normalize() - times.min().normalize()).days) + 1)


def _profit_factor(pnl: pd.Series) -> float | str:
    values = pd.to_numeric(pnl, errors="coerce").fillna(0.0)
    gross_profit = float(values[values > 0].sum())
    gross_loss = float(-values[values < 0].sum())
    if gross_loss == 0.0:
        return "inf" if gross_profit > 0.0 else 0.0
    return gross_profit / gross_loss


def _same_time_opposite_signal_groups(frame: pd.DataFrame) -> int:
    if frame.empty:
        return 0
    by_time = frame.groupby("time")["signal"].nunique()
    return int((by_time > 1).sum())


def _select_rows(frame: pd.DataFrame, *, score_col: str, selector: str, threshold: float) -> pd.DataFrame:
    active = frame.loc[frame["signal"] != 0].copy()
    if active.empty:
        return active

    scores = pd.to_numeric(active[score_col], errors="coerce").fillna(float("-inf"))
    active = active.assign(_score=scores)

    if selector == "prob_ge_threshold":
        return active.loc[active["_score"] >= threshold].drop(columns=["_score"])
    if selector == "top_k_probability":
        if not 0.0 < threshold <= 1.0:
            raise ValueError("top_k_probability threshold must be in (0, 1]")
        k_count = max(1, int(math.ceil(len(active) * threshold)))
        return active.nlargest(k_count, "_score").sort_index().drop(columns=["_score"])
    raise ValueError(f"unsupported selector: {selector}")


def evaluate_candidate(
    frame: pd.DataFrame,
    *,
    score_target: str,
    selector: str,
    threshold: float,
    pnl_column: str | None = None,
) -> dict[str, Any]:
    """Считает diagnostic-метрики одного threshold/top-k кандидата."""
    score_col = f"pred_{score_target}"
    if score_col not in frame.columns:
        raise ValueError(f"missing score column: {score_col}")

    live = _select_rows(frame, score_col=score_col, selector=selector, threshold=threshold)
    days = _coverage_days(frame)
    selected_times = live["time"].astype(str).tolist()

    if pnl_column is None:
        pnl_column = f"true_trail_24_pnl_atr_x{score_target.rsplit('x', 1)[-1]}"
    pnl = pd.to_numeric(live[pnl_column], errors="coerce").fillna(0.0) if pnl_column in live.columns else pd.Series(dtype=float)

    return {
        "score_target": score_target,
        "selector": selector,
        "threshold": float(threshold),
        "trades": int(len(live)),
        "trades_per_day": float(len(live) / days),
        "buy_trades": int((live["signal"] > 0).sum()) if not live.empty else 0,
        "sell_trades": int((live["signal"] < 0).sum()) if not live.empty else 0,
        "same_time_opposite_signal_groups": _same_time_opposite_signal_groups(live),
        "pf": _profit_factor(pnl),
        "mean_pnl_atr": float(pnl.mean()) if len(pnl) else 0.0,
        "selected_times": selected_times,
    }


def select_diagnostic_preset(
    results: pd.DataFrame,
    *,
    min_trades_per_day: float | None = None,
    stop_atr: float = DEFAULT_STOP_ATR,
    take_profit_atr: float = DEFAULT_TAKE_PROFIT_ATR,
    max_hold_bars: int = DEFAULT_MAX_HOLD_BARS,
    max_positions: int = DEFAULT_MAX_POSITIONS,
) -> dict[str, Any]:
    """Выбирает telemetry preset по частоте, не оптимизируя PF."""
    if results.empty:
        raise ValueError("cannot select diagnostic preset from empty results")

    eligible = results.copy()
    if min_trades_per_day is not None:
        eligible = eligible.loc[eligible["trades_per_day"] >= min_trades_per_day].copy()
    if eligible.empty:
        eligible = results.copy()

    ranked = eligible.sort_values(
        ["trades_per_day", "trades", "same_time_opposite_signal_groups"],
        ascending=[False, False, True],
    )
    winner = ranked.iloc[0]

    return {
        "mode": "telemetry_frequency_v1",
        "diagnostic": True,
        "winner": {
            "score_target": str(winner["score_target"]),
            "selector": str(winner["selector"]),
            "threshold": float(winner["threshold"]),
            "exit_atr_multiplier": int(str(winner["score_target"]).rsplit("x", 1)[-1]),
        },
        "execution": {
            "stop_atr": float(stop_atr),
            "take_profit_atr": float(take_profit_atr),
            "max_hold_bars": int(max_hold_bars),
            "max_positions": int(max_positions),
        },
        "selection_note": "Diagnostic preset selected by trade frequency; PF and same-time conflicts are diagnostic only.",
    }


def build_candidate_table(
    frame: pd.DataFrame,
    *,
    score_targets: Iterable[str],
    thresholds: Iterable[float] = DEFAULT_THRESHOLDS,
    top_k_values: Iterable[float] = DEFAULT_TOP_K_VALUES,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for score_target in score_targets:
        for threshold in thresholds:
            rows.append(
                evaluate_candidate(
                    frame,
                    score_target=score_target,
                    selector="prob_ge_threshold",
                    threshold=float(threshold),
                )
            )
        for top_k in top_k_values:
            rows.append(
                evaluate_candidate(
                    frame,
                    score_target=score_target,
                    selector="top_k_probability",
                    threshold=float(top_k),
                )
            )
    return pd.DataFrame(rows)


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    if hasattr(value, "item"):
        return value.item()
    return value


def render_summary_markdown(summary: dict[str, Any]) -> str:
    selected = summary["selected_rule"]
    winner = selected["winner"]
    grid = summary["grid"]
    lines = [
        "# Telemetry Frequency Calibration",
        "",
        "> Diagnostic calibration only. PF is not a selection criterion.",
        "",
        "## Selected Rule",
        "",
        "| Field | Value |",
        "|---|---:|",
        f"| score_target | {winner['score_target']} |",
        f"| selector | {winner['selector']} |",
        f"| threshold | {winner['threshold']} |",
        f"| stop_atr | {selected['execution']['stop_atr']} |",
        f"| take_profit_atr | {selected['execution']['take_profit_atr']} |",
        f"| max_hold_bars | {selected['execution']['max_hold_bars']} |",
        f"| max_positions | {selected['execution']['max_positions']} |",
        "",
        "## Grid Summary",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| candidates | {grid['candidates']} |",
        f"| max_trades_per_day | {grid['max_trades_per_day']:.4f} |",
        f"| max_trades | {grid['max_trades']} |",
    ]
    return "\n".join(lines) + "\n"


def run_calibration(
    *,
    predictions_path: str | Path,
    score_targets: Iterable[str],
    output_dir: str | Path,
    thresholds: Iterable[float] = DEFAULT_THRESHOLDS,
    top_k_values: Iterable[float] = DEFAULT_TOP_K_VALUES,
    min_trades_per_day: float | None = None,
) -> dict[str, Any]:
    frame = load_prediction_frame(predictions_path)
    table = build_candidate_table(
        frame,
        score_targets=tuple(score_targets),
        thresholds=tuple(thresholds),
        top_k_values=tuple(top_k_values),
    )
    selected_rule = select_diagnostic_preset(table, min_trades_per_day=min_trades_per_day)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    grid_for_csv = table.copy()
    if "selected_times" in grid_for_csv.columns:
        grid_for_csv["selected_times"] = grid_for_csv["selected_times"].map(lambda items: "|".join(items))
    grid_for_csv.to_csv(output / "calibration_grid.csv", sep=";", index=False)
    (output / "selected_rule.json").write_text(
        json.dumps(_jsonable(selected_rule), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    summary = {
        "predictions_path": str(predictions_path),
        "selected_rule": selected_rule,
        "grid": {
            "candidates": int(len(table)),
            "max_trades_per_day": float(table["trades_per_day"].max()) if len(table) else 0.0,
            "max_trades": int(table["trades"].max()) if len(table) else 0,
        },
    }
    (output / "summary.json").write_text(json.dumps(_jsonable(summary), ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "summary.md").write_text(render_summary_markdown(summary), encoding="utf-8")
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Calibrate telemetry_frequency_v1 diagnostic signal frequency.")
    parser.add_argument("--predictions", required=True, help="Prediction CSV with pred_take_* columns.")
    parser.add_argument("--score-target", action="append", required=True, help="Score target such as take_24_x8.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Output directory.")
    parser.add_argument("--min-trades-per-day", type=float, default=None, help="Optional frequency floor.")
    return parser.parse_args()


def main() -> dict[str, Any]:
    args = parse_args()
    summary = run_calibration(
        predictions_path=args.predictions,
        score_targets=tuple(args.score_target),
        output_dir=args.output_dir,
        min_trades_per_day=args.min_trades_per_day,
    )
    print(json.dumps(_jsonable(summary), ensure_ascii=False, indent=2))
    return summary


if __name__ == "__main__":
    main()
