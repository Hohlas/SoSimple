# =============================================================================
# Файл: benchmark_entry_path_direct_bar_model.py
# Назначение: Benchmark прямой модели BUY/SELL/SKIP для каждого бара entry_path.
# Обновлён: 2026-05-14
# Входные данные:
#   - train/validation/test source CSV и OHLC CSV
# Выходные данные:
#   - summary JSON/Markdown и selected rows CSV (куда: ML/reports/...)
# Использование:
#   python -m ML.benchmark_entry_path_direct_bar_model
# Примечания:
#   - Модель не использует offline `signal` как gate при выборе сделок.
# =============================================================================

from __future__ import annotations

import argparse
import json
from datetime import timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

from ML.benchmark_entry_path_all_rows_ranking import _format_metric
from ML.benchmark_entry_path_all_rows_ranking import run_sequential_all_rows
from ML.benchmark_entry_path_causal_surrogate import FEATURE_COLUMNS
from ML.benchmark_entry_path_causal_surrogate import build_live_safe_features
from ML.entry_path_trade_filter import compute_pf
from processing.label_signals import load_ohlc_index


DEFAULT_TRAIN_SOURCE = Path("DATA/Nero_XAUUSD_train_labeled.csv")
DEFAULT_VALIDATION_SOURCE = Path("DATA/Nero_XAUUSD_validation_labeled.csv")
DEFAULT_TEST_SOURCE = Path("DATA/Nero_XAUUSD_test_labeled.csv")
DEFAULT_OHLC = Path("DATA/XAUUSD_H1_OHLC.csv")
DEFAULT_OUTPUT_DIR = Path("ML/reports/entry_path_v1_direct_bar_model")
DEFAULT_PROBABILITY_GRID = [0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95]
DEFAULT_EDGE_THRESHOLD = 0.25
DEFAULT_RETURN_COLUMN = "ohlc_24"


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


def compute_buy_sell_returns(source: pd.DataFrame, ohlc_path: str | Path, horizon: int) -> pd.DataFrame:
    """Считает доходность BUY и SELL от следующего бара до закрытия горизонта."""
    ohlc, times, time_idx = load_ohlc_index(str(ohlc_path))
    parsed_time = pd.to_datetime(source["time"], format="%Y.%m.%d %H:%M", errors="coerce")
    atr_values = pd.to_numeric(source["ATR"], errors="coerce").fillna(0.0).to_numpy(dtype=np.float64)
    buy = np.zeros(len(source), dtype=np.float64)
    sell = np.zeros(len(source), dtype=np.float64)

    for idx, row_time in enumerate(parsed_time):
        atr = float(atr_values[idx])
        if pd.isna(row_time) or atr <= 0:
            continue
        row_dt = row_time.to_pydatetime().replace(tzinfo=timezone.utc)
        base_idx = time_idx.get(row_dt)
        if base_idx is None:
            continue
        entry_idx = base_idx + 1
        exit_idx = base_idx + int(horizon)
        if entry_idx >= len(times) or exit_idx >= len(times):
            continue
        entry_price = float(ohlc[times[entry_idx]][0])
        exit_price = float(ohlc[times[exit_idx]][3])
        buy_ret = (exit_price - entry_price) / atr
        buy[idx] = buy_ret
        sell[idx] = -buy_ret

    return pd.DataFrame({"buy_ret_atr": buy, "sell_ret_atr": sell}, index=source.index)


def build_direct_target(
    frame: pd.DataFrame,
    *,
    return_column: str,
    edge_threshold: float,
    buy_sell_returns: pd.DataFrame | None = None,
) -> pd.Series:
    """Строит цель `BUY/SELL/SKIP` для прямой модели."""
    edge = float(edge_threshold)
    if buy_sell_returns is not None:
        buy = pd.to_numeric(buy_sell_returns["buy_ret_atr"], errors="coerce").fillna(0.0)
        sell = pd.to_numeric(buy_sell_returns["sell_ret_atr"], errors="coerce").fillna(0.0)
        target = pd.Series(0, index=frame.index, dtype="int64")
        target.loc[(buy > sell) & (buy >= edge)] = 1
        target.loc[(sell > buy) & (sell >= edge)] = -1
        return target

    if return_column not in frame.columns:
        raise ValueError(f"missing return column: {return_column}")

    signal = pd.to_numeric(frame["signal"], errors="coerce").fillna(0).astype(int)
    ret = pd.to_numeric(frame[return_column], errors="coerce").fillna(0.0)
    target = pd.Series(0, index=frame.index, dtype="int64")
    active = signal.isin([-1, 1])
    target.loc[active & (ret >= edge)] = signal.loc[active & (ret >= edge)]
    target.loc[active & (ret <= -edge)] = -signal.loc[active & (ret <= -edge)]
    return target


def fit_direct_model(
    train_source: pd.DataFrame,
    target: pd.Series,
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
    model.fit(build_live_safe_features(train_source), target.astype(int))
    return model


def predict_probabilities(model: RandomForestClassifier, source: pd.DataFrame) -> pd.DataFrame:
    probabilities = model.predict_proba(build_live_safe_features(source))
    out = pd.DataFrame(0.0, index=source.index, columns=[-1, 0, 1])
    for idx, klass in enumerate(model.classes_):
        if int(klass) in out.columns:
            out[int(klass)] = probabilities[:, idx]
    return out


def predict_direct_signal(probabilities: pd.DataFrame, threshold: float) -> pd.DataFrame:
    p_sell = probabilities.get(-1, pd.Series(0.0, index=probabilities.index)).astype(float)
    p_buy = probabilities.get(1, pd.Series(0.0, index=probabilities.index)).astype(float)
    direct_score = p_sell + p_buy
    direction_edge = p_buy - p_sell
    signal = pd.Series(0, index=probabilities.index, dtype="int64")
    active = direct_score >= float(threshold)
    signal.loc[active & (direction_edge >= 0)] = 1
    signal.loc[active & (direction_edge < 0)] = -1
    return pd.DataFrame(
        {
            "direct_signal": signal,
            "direct_score": direct_score,
            "direction_edge": direction_edge,
        }
    )


def direct_classification_metrics(truth: pd.Series, pred: pd.Series) -> dict[str, float]:
    truth = pd.Series(truth).astype(int)
    pred = pd.Series(pred).astype(int)
    true_active = truth != 0
    pred_active = pred != 0
    true_positive_active = true_active & pred_active
    correct_signal = true_positive_active & (truth == pred)
    return {
        "active_precision": float(true_positive_active.sum() / pred_active.sum()) if pred_active.any() else 0.0,
        "active_recall": float(true_positive_active.sum() / true_active.sum()) if true_active.any() else 0.0,
        "direction_accuracy_on_pred_active": float((truth[true_positive_active] == pred[true_positive_active]).mean())
        if true_positive_active.any()
        else 0.0,
        "correct_signal_precision": float(correct_signal.sum() / pred_active.sum()) if pred_active.any() else 0.0,
        "correct_signal_recall": float(correct_signal.sum() / true_active.sum()) if true_active.any() else 0.0,
    }


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


def build_eval_frame(
    *,
    source: pd.DataFrame,
    probabilities: pd.DataFrame,
    threshold: float,
    buy_sell_returns: pd.DataFrame,
) -> pd.DataFrame:
    pred = predict_direct_signal(probabilities, threshold=threshold)
    signal = pred["direct_signal"].astype(int)
    buy = pd.to_numeric(buy_sell_returns["buy_ret_atr"], errors="coerce").fillna(0.0)
    sell = pd.to_numeric(buy_sell_returns["sell_ret_atr"], errors="coerce").fillna(0.0)
    true_ret = pd.Series(0.0, index=source.index, dtype="float64")
    true_ret.loc[signal == 1] = buy.loc[signal == 1]
    true_ret.loc[signal == -1] = sell.loc[signal == -1]
    out = pd.DataFrame(
        {
            "time": pd.to_datetime(source["time"], format="%Y.%m.%d %H:%M", errors="coerce"),
            "signal": signal,
            "direct_score": pred["direct_score"].astype(float),
            "direction_edge": pred["direction_edge"].astype(float),
            "buy_ret_atr": buy,
            "sell_ret_atr": sell,
            "true_ret_24_dir_atr": true_ret,
        }
    )
    out["selected"] = out["signal"] != 0
    return out


def evaluate_threshold_grid(
    *,
    source: pd.DataFrame,
    probabilities: pd.DataFrame,
    truth: pd.Series,
    buy_sell_returns: pd.DataFrame,
    probability_grid: list[float],
    min_period_trades: int,
) -> tuple[pd.DataFrame, dict[float, pd.DataFrame]]:
    rows = []
    frames = {}
    for threshold in probability_grid:
        frame = build_eval_frame(
            source=source,
            probabilities=probabilities,
            threshold=float(threshold),
            buy_sell_returns=buy_sell_returns,
        )
        frames[float(threshold)] = frame
        summary = _selected_summary(frame, frame["selected"], min_period_trades)
        metrics = direct_classification_metrics(truth, frame["signal"])
        rows.append({"threshold": float(threshold), **summary, **metrics})
    return pd.DataFrame(rows), frames


def pick_direct_threshold(summary: pd.DataFrame) -> pd.Series:
    workable = summary.loc[summary["trades"] >= 30].copy()
    pool = workable if not workable.empty else summary
    return pool.sort_values(["pf", "eligible_years", "trades"], ascending=[False, False, False]).iloc[0]


def build_report(payload: dict[str, Any]) -> str:
    winner = payload["winner"]
    test = payload["test"]
    seq = payload["sequential"]
    return "\n".join(
        [
            "# Entry Path v1 Direct Bar Model",
            "",
            "## Context",
            "",
            "Цель: проверить модель, которая сама выбирает BUY/SELL/SKIP для каждого бара.",
            "",
            "## Winner",
            "",
            f"- probability_threshold: `{winner['threshold']}`",
            f"- validation trades: `{winner['trades']}`",
            f"- validation pf: `{_format_metric(winner['pf'])}`",
            f"- active precision: `{winner['active_precision']:.2%}`",
            f"- active recall: `{winner['active_recall']:.2%}`",
            f"- direction accuracy on selected active: `{winner['direction_accuracy_on_pred_active']:.2%}`",
            f"- correct signal precision: `{winner['correct_signal_precision']:.2%}`",
            "",
            "## Frozen Test",
            "",
            f"- trades: `{test['trades']}`",
            f"- pf: `{_format_metric(test['pf'])}`",
            f"- win_rate: `{test['win_rate']:.2%}`",
            f"- mean_pnl_atr: `{test['mean_pnl_atr']:.4f}`",
            f"- direction accuracy on selected active: `{test['direction_accuracy_on_pred_active']:.2%}`",
            f"- correct signal precision: `{test['correct_signal_precision']:.2%}`",
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
    ohlc: str | Path,
    output_dir: str | Path,
    probability_grid: list[float],
    return_column: str = DEFAULT_RETURN_COLUMN,
    edge_threshold: float = DEFAULT_EDGE_THRESHOLD,
    min_period_trades: int = 10,
    sequential_hold_bars: int = 24,
    horizon: int = 24,
    random_state: int = 42,
    n_estimators: int = 160,
) -> dict[str, Any]:
    usecols = ["time", "signal", "ATR", "fractal0"]
    extra_usecols = [] if return_column == DEFAULT_RETURN_COLUMN else [return_column]
    train = pd.read_csv(train_source, sep=";", usecols=usecols + extra_usecols)
    validation = pd.read_csv(validation_source, sep=";", usecols=usecols + extra_usecols)
    test = pd.read_csv(test_source, sep=";", usecols=usecols + extra_usecols)

    train_returns = compute_buy_sell_returns(train, ohlc, horizon)
    validation_returns = compute_buy_sell_returns(validation, ohlc, horizon)
    test_returns = compute_buy_sell_returns(test, ohlc, horizon)
    train_target = build_direct_target(
        train,
        return_column=return_column,
        edge_threshold=edge_threshold,
        buy_sell_returns=train_returns if return_column == DEFAULT_RETURN_COLUMN else None,
    )
    validation_truth = build_direct_target(
        validation,
        return_column=return_column,
        edge_threshold=edge_threshold,
        buy_sell_returns=validation_returns if return_column == DEFAULT_RETURN_COLUMN else None,
    )
    test_truth = build_direct_target(
        test,
        return_column=return_column,
        edge_threshold=edge_threshold,
        buy_sell_returns=test_returns if return_column == DEFAULT_RETURN_COLUMN else None,
    )

    model = fit_direct_model(train, train_target, random_state=random_state, n_estimators=n_estimators)
    validation_prob = predict_probabilities(model, validation)
    test_prob = predict_probabilities(model, test)
    validation_summary, _validation_frames = evaluate_threshold_grid(
        source=validation,
        probabilities=validation_prob,
        truth=validation_truth,
        buy_sell_returns=validation_returns,
        probability_grid=probability_grid,
        min_period_trades=min_period_trades,
    )
    winner = pick_direct_threshold(validation_summary).to_dict()
    winner_threshold = float(winner["threshold"])
    test_frame = build_eval_frame(
        source=test,
        probabilities=test_prob,
        threshold=winner_threshold,
        buy_sell_returns=test_returns,
    )
    test_summary = _selected_summary(test_frame, test_frame["selected"], min_period_trades)
    test_summary.update(direct_classification_metrics(test_truth, test_frame["signal"]))
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
        "ohlc": str(ohlc),
        "probability_grid": [float(value) for value in probability_grid],
        "return_column": return_column,
        "edge_threshold": float(edge_threshold),
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
    parser = argparse.ArgumentParser(description="Benchmark direct BUY/SELL/SKIP entry_path model.")
    parser.add_argument("--train-source", default=str(DEFAULT_TRAIN_SOURCE))
    parser.add_argument("--validation-source", default=str(DEFAULT_VALIDATION_SOURCE))
    parser.add_argument("--test-source", default=str(DEFAULT_TEST_SOURCE))
    parser.add_argument("--ohlc", default=str(DEFAULT_OHLC))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--probability-grid", nargs="+", type=float, default=DEFAULT_PROBABILITY_GRID)
    parser.add_argument("--return-column", default=DEFAULT_RETURN_COLUMN)
    parser.add_argument("--edge-threshold", type=float, default=DEFAULT_EDGE_THRESHOLD)
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
        ohlc=args.ohlc,
        output_dir=args.output_dir,
        probability_grid=args.probability_grid,
        return_column=args.return_column,
        edge_threshold=args.edge_threshold,
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
