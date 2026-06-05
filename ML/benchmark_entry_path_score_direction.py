# =============================================================================
# Файл: benchmark_entry_path_score_direction.py
# Назначение: Score-filtered direction resolver — binary BUY/SELL on score universe.
# Обновлён: 2026-05-15
# Входные данные:
#   - DATA/Nero_XAUUSD_*_labeled.csv, prediction CSV, OHLC CSV
# Выходные данные:
#   - validation grid и benchmark reports (куда: ML/reports/entry_path_v1_score_direction/)
# =============================================================================

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.utils.class_weight import compute_sample_weight

from ML.benchmark_entry_path_all_rows_ranking import run_sequential_all_rows
from ML.benchmark_entry_path_direct_bar_model import compute_buy_sell_returns
from ML.entry_path_direct_direction_targets import build_target_d_masks
from ML.fractal_level_feature_builder import apply_feature_normalizer
from ML.fractal_level_feature_builder import build_fractal_level_features
from ML.fractal_level_feature_builder import fit_feature_normalizer
from ML.entry_path_trade_filter import compute_pf


DEFAULT_ROOT = Path("ML/reports/entry_path_v1_live_safe_xauusd_no_predict_pool_server_multiseed/seed_042")
DEFAULT_TRAIN_SOURCE = Path("DATA/Nero_XAUUSD_train_labeled.csv")
DEFAULT_VALIDATION_SOURCE = Path("DATA/Nero_XAUUSD_validation_labeled.csv")
DEFAULT_TEST_SOURCE = Path("DATA/Nero_XAUUSD_test_labeled.csv")
DEFAULT_VALIDATION_PREDICTIONS = DEFAULT_ROOT / "validation_predictions.csv"
DEFAULT_TEST_PREDICTIONS = DEFAULT_ROOT / "test_predictions.csv"
DEFAULT_OHLC = Path("DATA/XAUUSD_H1_OHLC.csv")
DEFAULT_OUTPUT_DIR = Path("ML/reports/entry_path_v1_score_direction")
DEFAULT_OLD_SCORE_THRESHOLD = -0.07158749
DEFAULT_THRESHOLD_GRID = [0.30, 0.40, 0.50, 0.60]
DEFAULT_NEAREST_K = 4


def pick_validation_winner(grid: pd.DataFrame) -> dict[str, Any]:
    if grid.empty:
        return {}
    work = grid.copy()
    if "negative_years" not in work.columns:
        work["negative_years"] = 0
    candidates = work[
        (work["mode"] == "standalone")
        & (work["validation_trades"] >= 100)
        & (work["validation_pf"] >= 1.15)
        & (work["validation_sequential_pf"] >= 1.1)
        & (~work["overfitting_risk"].astype(bool))
    ].copy()
    if candidates.empty:
        return {}
    candidates = candidates.sort_values(
        ["validation_pf", "validation_sequential_pf", "validation_trades"],
        ascending=[False, False, False],
    )
    return candidates.iloc[0].to_dict()


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


def _model_feature_frame(features: pd.DataFrame) -> pd.DataFrame:
    return features[[c for c in features.columns if not str(c).endswith("_source_index")]].copy()


def run_validation_matrix(
    *,
    train_source: str | Path,
    validation_source: str | Path,
    validation_predictions: str | Path,
    ohlc: str | Path,
    output_dir: str | Path,
    old_score_threshold: float,
    k: int = DEFAULT_NEAREST_K,
) -> dict[str, Any]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    source_usecols = ["time", "signal", "ATR", *[f"fractal{idx}" for idx in range(100)]]
    target_usecols = ["time", "signal", "ATR", "up_3", "dn_3", "up_6", "dn_6", "up_12", "dn_12", "up_24", "dn_24", "up_48", "dn_48"]
    train_features_source = pd.read_csv(Path(train_source), sep=";", usecols=source_usecols)
    validation_features_source = pd.read_csv(Path(validation_source), sep=";", usecols=source_usecols)
    train_target_source = pd.read_csv(Path(train_source), sep=";", usecols=target_usecols)
    validation_target_source = pd.read_csv(Path(validation_source), sep=";", usecols=target_usecols)

    t0 = time.perf_counter()
    x_train_raw = build_fractal_level_features(train_features_source, input_family="nearest_k", k=k)
    feature_build_seconds = time.perf_counter() - t0
    x_validation_raw = build_fractal_level_features(validation_features_source, input_family="nearest_k", k=k)
    normalizer = fit_feature_normalizer(x_train_raw)
    x_train = _model_feature_frame(apply_feature_normalizer(x_train_raw, normalizer))
    x_validation = _model_feature_frame(apply_feature_normalizer(x_validation_raw, normalizer))
    returns = compute_buy_sell_returns(validation_target_source, ohlc, horizon=24)
    validation_pred = pd.read_csv(Path(validation_predictions), sep=";")
    score = pd.to_numeric(validation_pred["pred_ret_24_dir_atr"], errors="coerce").fillna(float("-inf"))

    train_buy_good, train_sell_good = build_target_d_masks(
        train_target_source, ohlc, trail_n=2.0, profit_z=1.0, horizon=24
    )
    validation_buy_good, validation_sell_good = build_target_d_masks(
        validation_target_source, ohlc, trail_n=2.0, profit_z=1.0, horizon=24
    )

    candidate_mask = score >= float(old_score_threshold)
    candidate_indices = candidate_mask.reset_index(drop=True)

    train_score = pd.read_csv(Path(train_source).parent / Path(train_source).name.replace("validation", "train").replace("_labeled", "_labeled"), sep=";") if False else None

    y_buy_train = train_buy_good.astype(int).values
    y_sell_train = train_sell_good.astype(int).values

    rows = []
    feature_importance_frames = []

    hgb_dir = HistGradientBoostingClassifier(
        max_iter=200, max_depth=5, min_samples_leaf=20,
        learning_rate=0.05, random_state=42,
    )
    sw_dir = compute_sample_weight("balanced", np.where(train_buy_good.values | train_sell_good.values, 1, 0))
    y_direction_train = np.where(train_buy_good.values, 1, np.where(train_sell_good.values, -1, 0))
    direction_mask_train = y_direction_train != 0
    hgb_dir.fit(
        x_train.iloc[direction_mask_train],
        y_direction_train[direction_mask_train],
        sample_weight=compute_sample_weight("balanced", y_direction_train[direction_mask_train]),
    )
    p_dir = hgb_dir.predict_proba(x_validation)
    dir_classes = list(hgb_dir.classes_)

    fractal0_direction = validation_features_source["fractal0"].apply(
        lambda x: int(str(x).split(":")[2]) if pd.notna(x) and len(str(x).split(":")) > 2 else 0
    ).reset_index(drop=True)

    for threshold in DEFAULT_THRESHOLD_GRID:
        selected = candidate_mask.reset_index(drop=True) & (p_dir[:, dir_classes.index(1)] >= threshold if 1 in dir_classes else np.zeros(len(x_validation)))
        eval_frame = pd.DataFrame({
            "time": pd.to_datetime(validation_target_source["time"], format="%Y.%m.%d %H:%M", errors="coerce"),
            "candidate_signal": np.where(selected, np.where(p_dir[:, dir_classes.index(1)] > (p_dir[:, dir_classes.index(-1)] if -1 in dir_classes else 0), 1, -1), 0),
            "true_ret_24_dir_atr": 0.0,
            "selected": selected,
        })
        buy_mask = selected & (eval_frame["candidate_signal"] == 1)
        sell_mask = selected & (eval_frame["candidate_signal"] == -1)
        eval_frame.loc[buy_mask, "true_ret_24_dir_atr"] = returns.loc[buy_mask, "buy_ret_atr"].values
        eval_frame.loc[sell_mask, "true_ret_24_dir_atr"] = returns.loc[sell_mask, "sell_ret_atr"].values

        rows.append(_grid_row_score_dir(
            eval_frame, validation_buy_good, validation_sell_good,
            threshold=float(threshold),
            mode="standalone",
            feature_count=int(x_train.shape[1]),
            candidate_count=int(selected.sum()),
        ))

        baseline_frame = pd.DataFrame({
            "time": pd.to_datetime(validation_target_source["time"], format="%Y.%m.%d %H:%M", errors="coerce"),
            "candidate_signal": np.where(candidate_mask.reset_index(drop=True), np.where(fractal0_direction == -1, 1, np.where(fractal0_direction == 1, -1, 0)), 0),
            "true_ret_24_dir_atr": 0.0,
            "selected": candidate_mask.reset_index(drop=True),
        })
        buy_mask_bl = baseline_frame["selected"] & (baseline_frame["candidate_signal"] == 1)
        sell_mask_bl = baseline_frame["selected"] & (baseline_frame["candidate_signal"] == -1)
        baseline_frame.loc[buy_mask_bl, "true_ret_24_dir_atr"] = returns.loc[buy_mask_bl, "buy_ret_atr"].values
        baseline_frame.loc[sell_mask_bl, "true_ret_24_dir_atr"] = returns.loc[sell_mask_bl, "sell_ret_atr"].values

        rows.append(_grid_row_score_dir(
            baseline_frame, validation_buy_good, validation_sell_good,
            threshold=float(threshold),
            mode="fractal0_direction_diagnostic",
            feature_count=int(x_train.shape[1]),
            candidate_count=int(candidate_mask.sum()),
        ))

    grid = pd.DataFrame(rows)
    winner = pick_validation_winner(grid)
    grid.to_csv(output_path / "validation_grid.csv", sep=";", index=False)
    summary = {
        "stage": "validation-matrix",
        "test_set_used": False,
        "target_family": "D",
        "winner": winner,
        "feature_build_seconds": float(feature_build_seconds),
        "feature_count": int(x_train.shape[1]),
        "input_family": f"nearest_k{k}",
        "candidate_universe": int(candidate_mask.sum()),
        "old_score_threshold": float(old_score_threshold),
    }
    (output_path / "summary.json").write_text(json.dumps(_jsonable(summary), ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "stage": "validation-matrix",
        "validation_grid_path": str(output_path / "validation_grid.csv"),
        "summary_path": str(output_path / "summary.json"),
        "winner_found": bool(winner),
        "winner": winner,
    }


def _grid_row_score_dir(
    frame: pd.DataFrame,
    buy_good: pd.Series,
    sell_good: pd.Series,
    *,
    threshold: float,
    mode: str,
    feature_count: int,
    candidate_count: int,
) -> dict[str, Any]:
    selected = frame.loc[frame["selected"]].copy()
    pnl = selected["true_ret_24_dir_atr"].to_numpy(dtype=np.float64)
    buy = selected.loc[selected["candidate_signal"] == 1, "true_ret_24_dir_atr"].to_numpy(dtype=np.float64)
    sell = selected.loc[selected["candidate_signal"] == -1, "true_ret_24_dir_atr"].to_numpy(dtype=np.float64)
    sequential = run_sequential_all_rows(
        frame.rename(columns={"candidate_signal": "signal"}),
        frame["selected"],
        hold_bars=24,
    )
    yearly = _yearly_pf(selected)
    negative_years = sum(1 for item in yearly if item["trades"] >= 20 and item["pf"] < 1.0)
    buy_trades = int(len(buy))
    sell_trades = int(len(sell))
    total_trades = int(len(selected))
    ambiguous_rate = float((buy_good & sell_good).mean())
    features_per_candidate = float(feature_count / max(candidate_count, 1))
    return {
        "config": f"D_score_dir_{threshold:.2f}_{mode}",
        "mode": mode,
        "target_family": "D",
        "threshold": float(threshold),
        "validation_trades": total_trades,
        "validation_pf": compute_pf(pnl),
        "validation_sequential_pf": float(sequential["pf"]),
        "validation_sequential_trades": int(sequential["trades"]),
        "buy_trades": buy_trades,
        "sell_trades": sell_trades,
        "buy_pf": compute_pf(buy),
        "sell_pf": compute_pf(sell),
        "buy_win_rate": float((buy > 0).mean()) if buy_trades else 0.0,
        "sell_win_rate": float((sell > 0).mean()) if sell_trades else 0.0,
        "buy_sell_balance": float(min(buy_trades, sell_trades) / max(total_trades, 1)),
        "one_sided_candidate": bool(total_trades > 0 and min(buy_trades, sell_trades) / max(total_trades, 1) < 0.20),
        "ambiguous_rate": ambiguous_rate,
        "yearly_pf": json.dumps(yearly, ensure_ascii=False),
        "negative_years": int(negative_years),
        "feature_count": feature_count,
        "features_per_validation_candidates": features_per_candidate,
        "overfitting_risk": bool(features_per_candidate >= 0.10),
        "candidate_universe_count": candidate_count,
    }


def _yearly_pf(selected: pd.DataFrame) -> list[dict[str, Any]]:
    if selected.empty:
        return []
    work = selected.copy()
    work["year"] = pd.to_datetime(work["time"], errors="coerce").dt.year
    rows = []
    for year, group in work.groupby("year", dropna=True, sort=True):
        pnl = group["true_ret_24_dir_atr"].to_numpy(dtype=np.float64)
        rows.append({"year": int(year), "trades": int(len(group)), "pf": compute_pf(pnl)})
    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Score-filtered direction resolver benchmark.")
    parser.add_argument("--stage", choices=["validation-matrix"], required=True)
    parser.add_argument("--train-source", default=str(DEFAULT_TRAIN_SOURCE))
    parser.add_argument("--validation-source", default=str(DEFAULT_VALIDATION_SOURCE))
    parser.add_argument("--test-source", default=str(DEFAULT_TEST_SOURCE))
    parser.add_argument("--validation-predictions", default=str(DEFAULT_VALIDATION_PREDICTIONS))
    parser.add_argument("--test-predictions", default=str(DEFAULT_TEST_PREDICTIONS))
    parser.add_argument("--ohlc", default=str(DEFAULT_OHLC))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--old-score-threshold", type=float, default=DEFAULT_OLD_SCORE_THRESHOLD)
    parser.add_argument("--k", type=int, default=DEFAULT_NEAREST_K, choices=[4, 6, 8, 16])
    return parser.parse_args()


def main() -> dict[str, Any]:
    args = parse_args()
    if args.stage == "validation-matrix":
        result = run_validation_matrix(
            train_source=args.train_source,
            validation_source=args.validation_source,
            validation_predictions=args.validation_predictions,
            ohlc=args.ohlc,
            output_dir=args.output_dir,
            old_score_threshold=args.old_score_threshold,
            k=args.k,
        )
    else:
        raise ValueError(f"unsupported stage: {args.stage}")
    print(json.dumps(_jsonable(result), ensure_ascii=False, indent=2))
    return result


if __name__ == "__main__":
    main()