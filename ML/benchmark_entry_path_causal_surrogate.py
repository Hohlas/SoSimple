# =============================================================================
# Файл: benchmark_entry_path_causal_surrogate.py
# Назначение: Causal surrogate benchmark для offline `label_all().signal`.
# Обновлён: 2026-05-14
# Входные данные:
#   - train/validation/test source CSV, prediction CSV, OHLC CSV
# Выходные данные:
#   - summary JSON/Markdown и selected rows CSV (куда: ML/reports/...)
# Использование:
#   python -m ML.benchmark_entry_path_causal_surrogate
# Примечания:
#   - Surrogate использует только live-доступные поля текущего fractal0.
# =============================================================================

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

from ML.benchmark_entry_path_all_rows_ranking import _format_metric
from ML.benchmark_entry_path_all_rows_ranking import run_sequential_all_rows
from ML.entry_path_trade_filter import compute_pf
from processing.label_signals import compute_entry_path_slice
from processing.label_signals import load_ohlc_index


DEFAULT_ROOT = Path("ML/reports/entry_path_v1_live_safe_xauusd_no_predict_pool_server_multiseed/seed_042")
DEFAULT_TRAIN_SOURCE = Path("DATA/Nero_XAUUSD_train_labeled.csv")
DEFAULT_VALIDATION_SOURCE = Path("DATA/Nero_XAUUSD_validation_labeled.csv")
DEFAULT_TEST_SOURCE = Path("DATA/Nero_XAUUSD_test_labeled.csv")
DEFAULT_VALIDATION_PREDICTIONS = DEFAULT_ROOT / "validation_predictions.csv"
DEFAULT_TEST_PREDICTIONS = DEFAULT_ROOT / "test_predictions.csv"
DEFAULT_OHLC = Path("DATA/XAUUSD_H1_OHLC.csv")
DEFAULT_OUTPUT_DIR = Path("ML/reports/entry_path_v1_causal_surrogate")
DEFAULT_PROBABILITY_GRID = [0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60]
DEFAULT_SCORE_THRESHOLD = -0.07158749

FEATURE_COLUMNS = [
    "atr",
    "session_hour",
    "weekday",
    "fractal_dir",
    "fractal_front",
    "fractal_back",
    "fractal_strong",
    "fractal_break",
    "fractal_reverse",
    "fractal_power",
    "fractal_count",
    "fractal_impulse",
    "fractal_atr",
]


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


def _fractal_field(frame: pd.DataFrame, position: int) -> pd.Series:
    parts = frame["fractal0"].astype(str).str.split(":", expand=True)
    if position >= parts.shape[1]:
        return pd.Series(0.0, index=frame.index, dtype="float64")
    return pd.to_numeric(parts[position], errors="coerce").fillna(0.0)


def build_live_safe_features(frame: pd.DataFrame) -> pd.DataFrame:
    parsed_time = pd.to_datetime(frame["time"], format="%Y.%m.%d %H:%M", errors="coerce")
    out = pd.DataFrame(index=frame.index)
    out["atr"] = pd.to_numeric(frame["ATR"], errors="coerce").fillna(0.0)
    out["session_hour"] = parsed_time.dt.hour.fillna(0).astype(int)
    out["weekday"] = parsed_time.dt.weekday.fillna(0).astype(int)
    out["fractal_dir"] = _fractal_field(frame, 2)
    out["fractal_front"] = _fractal_field(frame, 3)
    out["fractal_back"] = _fractal_field(frame, 4)
    out["fractal_strong"] = _fractal_field(frame, 5)
    out["fractal_break"] = _fractal_field(frame, 6)
    out["fractal_reverse"] = _fractal_field(frame, 7)
    out["fractal_power"] = _fractal_field(frame, 8)
    out["fractal_count"] = _fractal_field(frame, 9)
    out["fractal_impulse"] = _fractal_field(frame, 10)
    out["fractal_atr"] = _fractal_field(frame, 21)
    return out[FEATURE_COLUMNS]


def target_signal(frame: pd.DataFrame) -> pd.Series:
    signal = pd.to_numeric(frame["signal"], errors="coerce").fillna(0).astype(int)
    signal.loc[~signal.isin([-1, 0, 1])] = 0
    return signal


def fit_surrogate_model(
    train_source: pd.DataFrame,
    *,
    random_state: int = 42,
    n_estimators: int = 160,
) -> RandomForestClassifier:
    model = RandomForestClassifier(
        n_estimators=int(n_estimators),
        min_samples_leaf=20,
        class_weight="balanced_subsample",
        random_state=int(random_state),
        n_jobs=-1,
    )
    model.fit(build_live_safe_features(train_source), target_signal(train_source))
    return model


def predict_probabilities(model: RandomForestClassifier, source: pd.DataFrame) -> pd.DataFrame:
    probabilities = model.predict_proba(build_live_safe_features(source))
    out = pd.DataFrame(0.0, index=source.index, columns=[-1, 0, 1])
    for idx, klass in enumerate(model.classes_):
        if int(klass) in out.columns:
            out[int(klass)] = probabilities[:, idx]
    return out


def predict_surrogate_signal(probabilities: pd.DataFrame, threshold: float) -> pd.DataFrame:
    p_sell = probabilities.get(-1, pd.Series(0.0, index=probabilities.index)).astype(float)
    p_buy = probabilities.get(1, pd.Series(0.0, index=probabilities.index)).astype(float)
    active_probability = p_sell + p_buy
    signal = pd.Series(0, index=probabilities.index, dtype="int64")
    active = active_probability >= float(threshold)
    signal.loc[active & (p_buy >= p_sell)] = 1
    signal.loc[active & (p_sell > p_buy)] = -1
    return pd.DataFrame({"surrogate_signal": signal, "active_probability": active_probability})


def surrogate_classification_metrics(truth: pd.Series, pred: pd.Series) -> dict[str, float]:
    truth = pd.Series(truth).astype(int)
    pred = pd.Series(pred).astype(int)
    true_active = truth != 0
    pred_active = pred != 0
    true_positive_active = true_active & pred_active
    correct_direction = true_positive_active & (truth == pred)
    return {
        "active_precision": float(true_positive_active.sum() / pred_active.sum()) if pred_active.any() else 0.0,
        "active_recall": float(true_positive_active.sum() / true_active.sum()) if true_active.any() else 0.0,
        "direction_accuracy_on_true_active": float((truth[true_active] == pred[true_active]).mean())
        if true_active.any()
        else 0.0,
    }


def _validate_prediction_alignment(source: pd.DataFrame, predictions: pd.DataFrame) -> None:
    if len(source) != len(predictions):
        raise ValueError(f"row count mismatch: source={len(source)}, predictions={len(predictions)}")
    left = source["time"].astype(str).reset_index(drop=True)
    right = predictions["time"].astype(str).reset_index(drop=True)
    if not left.equals(right):
        raise ValueError("time mismatch between source and predictions")


def _compute_pnl_for_signal(source: pd.DataFrame, signal: pd.Series, ohlc_path: str | Path, horizon: int) -> pd.Series:
    ohlc, times, time_idx = load_ohlc_index(str(ohlc_path))
    parsed_time = pd.to_datetime(source["time"], format="%Y.%m.%d %H:%M", errors="coerce")
    atr_values = pd.to_numeric(source["ATR"], errors="coerce").fillna(0.0).to_numpy(dtype=np.float64)
    pnl = pd.Series(0.0, index=source.index, dtype="float64")
    from datetime import timezone

    for idx, row_time in enumerate(parsed_time):
        direction = int(signal.iloc[idx])
        atr = float(atr_values[idx])
        if direction not in (-1, 1) or pd.isna(row_time) or atr <= 0:
            continue
        row_dt = row_time.to_pydatetime().replace(tzinfo=timezone.utc)
        base_idx = time_idx.get(row_dt)
        if base_idx is None:
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
        pnl.iloc[idx] = compute_entry_path_slice(bars, direction, entry_price, atr, int(horizon))["ret_dir_atr"]
    return pnl


def build_eval_frame(
    *,
    source: pd.DataFrame,
    predictions: pd.DataFrame,
    probabilities: pd.DataFrame,
    threshold: float,
    score_threshold: float,
    ohlc_path: str | Path,
    horizon: int,
) -> pd.DataFrame:
    _validate_prediction_alignment(source, predictions)
    pred_signal = predict_surrogate_signal(probabilities, threshold=threshold)
    out = pd.DataFrame(
        {
            "time": pd.to_datetime(source["time"], format="%Y.%m.%d %H:%M", errors="coerce"),
            "signal": pred_signal["surrogate_signal"].astype(int),
            "offline_signal": target_signal(source),
            "active_probability": pred_signal["active_probability"].astype(float),
            "pred_ret_24_dir_atr": pd.to_numeric(predictions["pred_ret_24_dir_atr"], errors="coerce").fillna(
                float("-inf")
            ),
        }
    )
    out["true_ret_24_dir_atr"] = _compute_pnl_for_signal(source, out["signal"], ohlc_path, horizon)
    out["selected"] = (out["signal"] != 0) & (out["pred_ret_24_dir_atr"] >= float(score_threshold))
    return out


def _selected_summary(frame: pd.DataFrame, selected_mask: pd.Series, min_period_trades: int) -> dict[str, Any]:
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


def evaluate_threshold_grid(
    *,
    source: pd.DataFrame,
    predictions: pd.DataFrame,
    probabilities: pd.DataFrame,
    probability_grid: list[float],
    score_threshold: float,
    ohlc_path: str | Path,
    horizon: int,
    min_period_trades: int,
) -> tuple[pd.DataFrame, dict[float, pd.DataFrame]]:
    rows = []
    frames = {}
    truth = target_signal(source)
    for threshold in probability_grid:
        frame = build_eval_frame(
            source=source,
            predictions=predictions,
            probabilities=probabilities,
            threshold=float(threshold),
            score_threshold=score_threshold,
            ohlc_path=ohlc_path,
            horizon=horizon,
        )
        frames[float(threshold)] = frame
        summary = _selected_summary(frame, frame["selected"], min_period_trades)
        metrics = surrogate_classification_metrics(truth, frame["signal"])
        rows.append({"threshold": float(threshold), **summary, **metrics})
    return pd.DataFrame(rows), frames


def pick_surrogate_threshold(summary: pd.DataFrame) -> pd.Series:
    workable = summary.loc[summary["trades"] >= 30].copy()
    pool = workable if not workable.empty else summary
    return pool.sort_values(["pf", "eligible_years", "trades"], ascending=[False, False, False]).iloc[0]


def build_report(payload: dict[str, Any]) -> str:
    winner = payload["winner"]
    test = payload["test"]
    seq = payload["sequential"]
    return "\n".join(
        [
            "# Entry Path v1 Causal Surrogate",
            "",
            "## Context",
            "",
            "Цель: проверить, можно ли причинно воспроизвести offline `signal != 0` и затем применить score gate.",
            "",
            "## Winner",
            "",
            f"- probability_threshold: `{winner['threshold']}`",
            f"- validation trades: `{winner['trades']}`",
            f"- validation pf: `{_format_metric(winner['pf'])}`",
            f"- active precision: `{winner['active_precision']:.2%}`",
            f"- active recall: `{winner['active_recall']:.2%}`",
            "",
            "## Frozen Test",
            "",
            f"- trades: `{test['trades']}`",
            f"- pf: `{_format_metric(test['pf'])}`",
            f"- win_rate: `{test['win_rate']:.2%}`",
            f"- mean_pnl_atr: `{test['mean_pnl_atr']:.4f}`",
            "",
            "## Sequential Test",
            "",
            f"- trades: `{seq['trades']}`",
            f"- pf: `{_format_metric(seq['pf'])}`",
            f"- win_rate: `{seq['win_rate']:.2%}`",
            f"- mean_pnl_atr: `{seq['mean_pnl_atr']:.4f}`",
        ]
    )


def run_benchmark(
    *,
    train_source: str | Path,
    validation_source: str | Path,
    test_source: str | Path,
    validation_predictions: str | Path,
    test_predictions: str | Path,
    ohlc: str | Path,
    output_dir: str | Path,
    probability_grid: list[float],
    score_threshold: float = DEFAULT_SCORE_THRESHOLD,
    min_period_trades: int = 10,
    sequential_hold_bars: int = 24,
    horizon: int = 24,
    random_state: int = 42,
    n_estimators: int = 160,
) -> dict[str, Any]:
    train = pd.read_csv(train_source, sep=";", usecols=["time", "signal", "ATR", "fractal0"])
    validation = pd.read_csv(validation_source, sep=";", usecols=["time", "signal", "ATR", "fractal0"])
    test = pd.read_csv(test_source, sep=";", usecols=["time", "signal", "ATR", "fractal0"])
    validation_pred = pd.read_csv(validation_predictions, sep=";", usecols=["time", "pred_ret_24_dir_atr"])
    test_pred = pd.read_csv(test_predictions, sep=";", usecols=["time", "pred_ret_24_dir_atr"])
    model = fit_surrogate_model(train, random_state=random_state, n_estimators=n_estimators)
    validation_prob = predict_probabilities(model, validation)
    test_prob = predict_probabilities(model, test)
    validation_summary, validation_frames = evaluate_threshold_grid(
        source=validation,
        predictions=validation_pred,
        probabilities=validation_prob,
        probability_grid=probability_grid,
        score_threshold=score_threshold,
        ohlc_path=ohlc,
        horizon=horizon,
        min_period_trades=min_period_trades,
    )
    winner = pick_surrogate_threshold(validation_summary).to_dict()
    winner_threshold = float(winner["threshold"])
    test_frame = build_eval_frame(
        source=test,
        predictions=test_pred,
        probabilities=test_prob,
        threshold=winner_threshold,
        score_threshold=score_threshold,
        ohlc_path=ohlc,
        horizon=horizon,
    )
    test_summary = _selected_summary(test_frame, test_frame["selected"], min_period_trades)
    test_metrics = surrogate_classification_metrics(target_signal(test), test_frame["signal"])
    test_summary.update(test_metrics)
    sequential = run_sequential_all_rows(test_frame, test_frame["selected"], hold_bars=sequential_hold_bars)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    summary_path = output_path / "summary.json"
    report_path = output_path / "summary.md"
    validation_summary_path = output_path / "validation_summary.csv"
    selected_rows_path = output_path / "test_selected_rows.csv"
    payload = {
        "train_source": str(train_source),
        "validation_source": str(validation_source),
        "test_source": str(test_source),
        "validation_predictions": str(validation_predictions),
        "test_predictions": str(test_predictions),
        "ohlc": str(ohlc),
        "score_threshold": float(score_threshold),
        "probability_grid": [float(value) for value in probability_grid],
        "min_period_trades": int(min_period_trades),
        "sequential_hold_bars": int(sequential_hold_bars),
        "horizon": int(horizon),
        "random_state": int(random_state),
        "n_estimators": int(n_estimators),
        "feature_columns": FEATURE_COLUMNS,
        "winner": winner,
        "test": test_summary,
        "sequential": sequential,
    }
    summary_path.write_text(json.dumps(_jsonable(payload), ensure_ascii=False, indent=2), encoding="utf-8")
    report_path.write_text(build_report(payload), encoding="utf-8")
    validation_summary.to_csv(validation_summary_path, sep=";", index=False)
    test_frame.loc[test_frame["selected"]].to_csv(selected_rows_path, sep=";", index=False)
    return {
        "summary_path": str(summary_path),
        "report_path": str(report_path),
        "validation_summary_path": str(validation_summary_path),
        "selected_rows_path": str(selected_rows_path),
        **payload,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark causal surrogate for offline entry_path signal.")
    parser.add_argument("--train-source", default=str(DEFAULT_TRAIN_SOURCE))
    parser.add_argument("--validation-source", default=str(DEFAULT_VALIDATION_SOURCE))
    parser.add_argument("--test-source", default=str(DEFAULT_TEST_SOURCE))
    parser.add_argument("--validation-predictions", default=str(DEFAULT_VALIDATION_PREDICTIONS))
    parser.add_argument("--test-predictions", default=str(DEFAULT_TEST_PREDICTIONS))
    parser.add_argument("--ohlc", default=str(DEFAULT_OHLC))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--probability-grid", nargs="+", type=float, default=DEFAULT_PROBABILITY_GRID)
    parser.add_argument("--score-threshold", type=float, default=DEFAULT_SCORE_THRESHOLD)
    parser.add_argument("--min-period-trades", type=int, default=10)
    parser.add_argument("--sequential-hold-bars", type=int, default=24)
    parser.add_argument("--horizon", type=int, default=24)
    parser.add_argument("--random-state", type=int, default=42)
    parser.add_argument("--n-estimators", type=int, default=160)
    return parser.parse_args()


def main() -> dict[str, Any]:
    args = parse_args()
    result = run_benchmark(
        train_source=args.train_source,
        validation_source=args.validation_source,
        test_source=args.test_source,
        validation_predictions=args.validation_predictions,
        test_predictions=args.test_predictions,
        ohlc=args.ohlc,
        output_dir=args.output_dir,
        probability_grid=args.probability_grid,
        score_threshold=args.score_threshold,
        min_period_trades=args.min_period_trades,
        sequential_hold_bars=args.sequential_hold_bars,
        horizon=args.horizon,
        random_state=args.random_state,
        n_estimators=args.n_estimators,
    )
    print(json.dumps(_jsonable(result), ensure_ascii=False, indent=2))
    return result


if __name__ == "__main__":
    main()
