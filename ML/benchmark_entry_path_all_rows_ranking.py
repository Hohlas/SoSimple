# =============================================================================
# Файл: benchmark_entry_path_all_rows_ranking.py
# Назначение: Benchmark all-rows ranking для entry_path score без offline signal gate.
# Обновлён: 2026-05-14
# Входные данные:
#   - prediction CSV, labeled source CSV, OHLC CSV (откуда: DATA/ и ML/reports/)
# Выходные данные:
#   - summary JSON/Markdown и selected rows CSV (куда: ML/reports/...)
# Использование:
#   python -m ML.benchmark_entry_path_all_rows_ranking
# Примечания:
#   - Направление берётся из fractal0.direction по diagnostic all-rows конвенции.
# =============================================================================

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ML.benchmark_entry_path_trade_filter import evaluate_frozen_threshold
from ML.benchmark_entry_path_trade_filter import evaluate_score_grid
from ML.entry_path_trade_filter import compute_pf
from ML.entry_path_trade_filter import pick_best_slice
from processing.label_signals import compute_entry_path_slice
from processing.label_signals import load_ohlc_index


DEFAULT_ROOT = Path("ML/reports/entry_path_v1_live_safe_xauusd_no_predict_pool_server_multiseed/seed_042")
DEFAULT_VALIDATION_PREDICTIONS = DEFAULT_ROOT / "validation_predictions.csv"
DEFAULT_TEST_PREDICTIONS = DEFAULT_ROOT / "test_predictions.csv"
DEFAULT_VALIDATION_SOURCE = Path("DATA/Nero_XAUUSD_validation_labeled.csv")
DEFAULT_TEST_SOURCE = Path("DATA/Nero_XAUUSD_test_labeled.csv")
DEFAULT_OHLC = Path("DATA/XAUUSD_H1_OHLC.csv")
DEFAULT_OUTPUT_DIR = Path("ML/reports/entry_path_v1_all_rows_ranking")
DEFAULT_COVERAGE_GRID = [0.005, 0.01, 0.02, 0.05, 0.075, 0.10]


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


def direction_from_fractal0(fractal0: pd.Series) -> pd.Series:
    direction = fractal0.astype(str).str.split(":", n=3).str[2]
    direction = pd.to_numeric(direction, errors="coerce").fillna(0).astype(int)
    signal = pd.Series(0, index=fractal0.index, dtype="int64")
    signal.loc[direction == -1] = 1
    signal.loc[direction == 1] = -1
    return signal


def _load_csv(path: str | Path, usecols: list[str] | None = None) -> pd.DataFrame:
    return pd.read_csv(Path(path), sep=";", usecols=usecols)


def _validate_alignment(predictions: pd.DataFrame, source: pd.DataFrame) -> None:
    if len(predictions) != len(source):
        raise ValueError(f"row count mismatch: predictions={len(predictions)}, source={len(source)}")
    left = predictions["time"].astype(str).reset_index(drop=True)
    right = source["time"].astype(str).reset_index(drop=True)
    if not left.equals(right):
        mismatch = int(np.flatnonzero(left.to_numpy() != right.to_numpy())[0])
        raise ValueError(
            "time alignment mismatch between predictions and source "
            f"at row {mismatch}: {left.iloc[mismatch]} != {right.iloc[mismatch]}"
        )


def build_all_rows_frame(
    *,
    predictions: pd.DataFrame,
    source: pd.DataFrame,
    ohlc_path: str | Path,
    horizon: int = 24,
) -> pd.DataFrame:
    required_predictions = {"time", "signal", "pred_ret_24_dir_atr"}
    required_source = {"time", "ATR", "fractal0"}
    missing_predictions = required_predictions.difference(predictions.columns)
    missing_source = required_source.difference(source.columns)
    if missing_predictions:
        raise ValueError(f"predictions missing columns: {sorted(missing_predictions)}")
    if missing_source:
        raise ValueError(f"source missing columns: {sorted(missing_source)}")

    _validate_alignment(predictions, source)
    ohlc, times, time_idx = load_ohlc_index(str(ohlc_path))
    parsed_time = pd.to_datetime(predictions["time"], format="%Y.%m.%d %H:%M", errors="coerce")
    all_rows_signal = direction_from_fractal0(source["fractal0"])

    out = pd.DataFrame(
        {
            "time": parsed_time,
            "original_signal": pd.to_numeric(predictions["signal"], errors="coerce").fillna(0).astype(int),
            "signal": all_rows_signal.to_numpy(dtype=np.int64),
            "all_rows_signal": all_rows_signal.to_numpy(dtype=np.int64),
            "pred_ret_24_dir_atr": pd.to_numeric(
                predictions["pred_ret_24_dir_atr"], errors="coerce"
            ).fillna(float("-inf")),
            "true_ret_24_dir_atr": 0.0,
            "all_rows_ret_24_dir_atr": 0.0,
        }
    )

    atr_values = pd.to_numeric(source["ATR"], errors="coerce").fillna(0.0).to_numpy(dtype=np.float64)
    for idx, row_time in enumerate(parsed_time):
        direction = int(all_rows_signal.iloc[idx])
        atr = float(atr_values[idx])
        if direction not in (-1, 1) or pd.isna(row_time) or atr <= 0:
            continue
        row_dt = row_time.to_pydatetime().replace(tzinfo=None)
        from datetime import timezone

        row_dt = row_dt.replace(tzinfo=timezone.utc)
        base_idx = time_idx.get(row_dt)
        if base_idx is None or base_idx + 1 >= len(times):
            continue
        end_idx = base_idx + 1 + int(horizon)
        if end_idx > len(times):
            continue
        entry_bar = ohlc[times[base_idx + 1]]
        entry_price = float(entry_bar[0])
        bars = pd.DataFrame(
            [
                {
                    "open": ohlc[times[k]][0],
                    "high": ohlc[times[k]][1],
                    "low": ohlc[times[k]][2],
                    "close": ohlc[times[k]][3],
                }
                for k in range(base_idx + 1, end_idx)
            ],
            columns=["open", "high", "low", "close"],
        )
        pnl = compute_entry_path_slice(
            bars=bars,
            direction=direction,
            entry_price=entry_price,
            atr=atr,
            horizon=int(horizon),
        )["ret_dir_atr"]
        out.at[idx, "true_ret_24_dir_atr"] = float(pnl)
        out.at[idx, "all_rows_ret_24_dir_atr"] = float(pnl)

    return out


def _selected_summary(frame: pd.DataFrame, selected_mask: pd.Series, *, min_period_trades: int) -> dict[str, Any]:
    selected = frame.loc[selected_mask].copy()
    pnl = selected["true_ret_24_dir_atr"].to_numpy(dtype=np.float64)
    yearly = []
    if not selected.empty:
        work = selected.copy()
        work["year"] = pd.to_datetime(work["time"], errors="coerce").dt.year
        for year, group in work.groupby("year", dropna=True, sort=True):
            group_pnl = group["true_ret_24_dir_atr"].to_numpy(dtype=np.float64)
            yearly.append(
                {
                    "year": int(year),
                    "trades": int(len(group)),
                    "pf": compute_pf(group_pnl),
                    "win_rate": float((group_pnl > 0).mean()) if len(group) else 0.0,
                    "mean_pnl_atr": float(group_pnl.mean()) if len(group) else 0.0,
                }
            )
    eligible = [row for row in yearly if row["trades"] >= min_period_trades]
    return {
        "trades": int(len(selected)),
        "pf": compute_pf(pnl),
        "win_rate": float((pnl > 0).mean()) if len(selected) else 0.0,
        "mean_pnl_atr": float(pnl.mean()) if len(selected) else 0.0,
        "eligible_years": int(len(eligible)),
        "negative_years": [row["year"] for row in eligible if row["pf"] < 1.0],
        "yearly": yearly,
    }


def run_sequential_all_rows(frame: pd.DataFrame, selected_mask: pd.Series, *, hold_bars: int = 24) -> dict[str, Any]:
    selected = frame.loc[selected_mask].copy()
    accepted_indices = []
    accepted_pnl = []
    last_accepted_pos = None
    for pos, (idx, row) in enumerate(selected.iterrows()):
        original_pos = int(idx)
        if last_accepted_pos is not None and original_pos - last_accepted_pos < hold_bars:
            continue
        accepted_indices.append(original_pos)
        accepted_pnl.append(float(row["true_ret_24_dir_atr"]))
        last_accepted_pos = original_pos
    pnl = np.asarray(accepted_pnl, dtype=np.float64)
    return {
        "trades": int(len(accepted_indices)),
        "accepted_indices": accepted_indices,
        "coverage": float(len(accepted_indices) / len(selected)) if len(selected) else 0.0,
        "pf": compute_pf(pnl),
        "mean_pnl_atr": float(pnl.mean()) if len(pnl) else 0.0,
        "win_rate": float((pnl > 0).mean()) if len(pnl) else 0.0,
    }


def run_grid_benchmark(
    *,
    validation: pd.DataFrame,
    test: pd.DataFrame,
    coverage_grid: list[float],
    min_period_trades: int = 10,
    sequential_hold_bars: int = 24,
) -> dict[str, Any]:
    validation_candidates = validation.loc[validation["all_rows_signal"] != 0].copy()
    test_candidates = test.loc[test["all_rows_signal"] != 0].copy()
    validation_summary = evaluate_score_grid(
        frame=validation_candidates,
        score=validation_candidates["pred_ret_24_dir_atr"].to_numpy(dtype=np.float64),
        candidate="all_rows_fractal0_direction",
        target_coverages=coverage_grid,
        min_period_trades=min_period_trades,
    )
    winner = pick_best_slice(validation_summary).to_dict()
    threshold = float(winner["score_threshold"])
    test_summary = evaluate_frozen_threshold(
        frame=test_candidates,
        score=test_candidates["pred_ret_24_dir_atr"].to_numpy(dtype=np.float64),
        candidate="all_rows_fractal0_direction",
        threshold=threshold,
        target_coverage=float(winner["target_coverage"]),
        min_period_trades=min_period_trades,
    ).iloc[0].to_dict()
    selected_mask = pd.Series(False, index=test.index, dtype=bool)
    selected_mask.loc[test_candidates.index] = test_candidates["pred_ret_24_dir_atr"] >= threshold
    sequential = run_sequential_all_rows(test, selected_mask, hold_bars=sequential_hold_bars)
    return {
        "winner": winner,
        "test": test_summary,
        "sequential": sequential,
        "validation_summary": validation_summary.to_dict(orient="records"),
        "selected_mask": selected_mask,
    }


def _format_metric(value: float) -> str:
    if np.isinf(value):
        return "inf"
    if np.isnan(value):
        return "nan"
    return f"{float(value):.4f}"


def build_report(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Entry Path v1 All-Rows Ranking",
            "",
            "## Context",
            "",
            "Цель: проверить `pred_ret_24_dir_atr` на всех строках, без offline `signal != 0` gate.",
            "Направление берётся из `fractal0.direction` по существующей diagnostic-конвенции.",
            "",
            "## Inputs",
            "",
            f"- validation_predictions: `{payload['validation_predictions']}`",
            f"- test_predictions: `{payload['test_predictions']}`",
            f"- ohlc: `{payload['ohlc']}`",
            f"- horizon: `{payload['horizon']}`",
            "",
            "## Validation Winner",
            "",
            f"- target_coverage: `{payload['winner']['target_coverage']}`",
            f"- score_threshold: `{payload['winner']['score_threshold']}`",
            f"- trades: `{payload['winner']['trades']}`",
            f"- pf: `{_format_metric(payload['winner']['pf'])}`",
            "",
            "## Frozen Test",
            "",
            f"- trades: `{payload['test']['trades']}`",
            f"- pf: `{_format_metric(payload['test']['pf'])}`",
            f"- win_rate: `{payload['test']['win_rate']:.2%}`",
            f"- mean_pnl_atr: `{payload['test']['mean_pnl_atr']:.4f}`",
            "",
            "## Sequential Test",
            "",
            f"- trades: `{payload['sequential']['trades']}`",
            f"- pf: `{_format_metric(payload['sequential']['pf'])}`",
            f"- win_rate: `{payload['sequential']['win_rate']:.2%}`",
            f"- mean_pnl_atr: `{payload['sequential']['mean_pnl_atr']:.4f}`",
            "",
            "## Limitation",
            "",
            "Это не production approval. Модель обучалась на другой постановке, поэтому положительный "
            "результат требует отдельного retrain или forward-проверки.",
        ]
    )


def run_benchmark(
    *,
    validation_predictions: str | Path,
    validation_source: str | Path,
    test_predictions: str | Path,
    test_source: str | Path,
    ohlc: str | Path,
    output_dir: str | Path,
    coverage_grid: list[float],
    min_period_trades: int = 10,
    sequential_hold_bars: int = 24,
    horizon: int = 24,
) -> dict[str, Any]:
    validation_pred = _load_csv(validation_predictions)
    validation_src = _load_csv(validation_source, usecols=["time", "ATR", "fractal0"])
    test_pred = _load_csv(test_predictions)
    test_src = _load_csv(test_source, usecols=["time", "ATR", "fractal0"])
    validation = build_all_rows_frame(
        predictions=validation_pred,
        source=validation_src,
        ohlc_path=ohlc,
        horizon=horizon,
    )
    test = build_all_rows_frame(
        predictions=test_pred,
        source=test_src,
        ohlc_path=ohlc,
        horizon=horizon,
    )
    result = run_grid_benchmark(
        validation=validation,
        test=test,
        coverage_grid=coverage_grid,
        min_period_trades=min_period_trades,
        sequential_hold_bars=sequential_hold_bars,
    )
    selected_mask = result.pop("selected_mask")
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    summary_path = output_path / "summary.json"
    report_path = output_path / "summary.md"
    selected_rows_path = output_path / "test_selected_rows.csv"
    validation_summary_path = output_path / "validation_summary.csv"

    payload = {
        "validation_predictions": str(validation_predictions),
        "validation_source": str(validation_source),
        "test_predictions": str(test_predictions),
        "test_source": str(test_source),
        "ohlc": str(ohlc),
        "coverage_grid": [float(value) for value in coverage_grid],
        "min_period_trades": int(min_period_trades),
        "sequential_hold_bars": int(sequential_hold_bars),
        "horizon": int(horizon),
        **result,
    }
    summary_path.write_text(json.dumps(_jsonable(payload), ensure_ascii=False, indent=2), encoding="utf-8")
    report_path.write_text(build_report(payload), encoding="utf-8")
    pd.DataFrame(payload["validation_summary"]).to_csv(validation_summary_path, sep=";", index=False)
    test.loc[selected_mask].to_csv(selected_rows_path, sep=";", index=False)
    return {
        "summary_path": str(summary_path),
        "report_path": str(report_path),
        "selected_rows_path": str(selected_rows_path),
        "validation_summary_path": str(validation_summary_path),
        **payload,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark all-rows entry_path ranking without offline signal gate.")
    parser.add_argument("--validation-predictions", default=str(DEFAULT_VALIDATION_PREDICTIONS))
    parser.add_argument("--validation-source", default=str(DEFAULT_VALIDATION_SOURCE))
    parser.add_argument("--test-predictions", default=str(DEFAULT_TEST_PREDICTIONS))
    parser.add_argument("--test-source", default=str(DEFAULT_TEST_SOURCE))
    parser.add_argument("--ohlc", default=str(DEFAULT_OHLC))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--coverage-grid", nargs="+", type=float, default=DEFAULT_COVERAGE_GRID)
    parser.add_argument("--min-period-trades", type=int, default=10)
    parser.add_argument("--sequential-hold-bars", type=int, default=24)
    parser.add_argument("--horizon", type=int, default=24)
    return parser.parse_args()


def main() -> dict[str, Any]:
    args = parse_args()
    result = run_benchmark(
        validation_predictions=args.validation_predictions,
        validation_source=args.validation_source,
        test_predictions=args.test_predictions,
        test_source=args.test_source,
        ohlc=args.ohlc,
        output_dir=args.output_dir,
        coverage_grid=args.coverage_grid,
        min_period_trades=args.min_period_trades,
        sequential_hold_bars=args.sequential_hold_bars,
        horizon=args.horizon,
    )
    print(json.dumps(_jsonable(result), ensure_ascii=False, indent=2))
    return result


if __name__ == "__main__":
    main()
