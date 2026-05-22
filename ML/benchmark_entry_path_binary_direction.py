# =============================================================================
# Файл: benchmark_entry_path_binary_direction.py
# Назначение: Binary BUY-vs-REST and SELL-vs-REST direction benchmark.
# Обновлён: 2026-05-15
# Входные данные:
#   - DATA/Nero_XAUUSD_*_labeled.csv, prediction CSV, OHLC CSV
# Выходные данные:
#   - validation grid и benchmark reports (куда: ML/reports/entry_path_v1_binary_direction/)
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
from ML.entry_path_direct_direction_targets import build_buy_sell_fav_adv
from ML.entry_path_direct_direction_targets import build_target_d_masks
from ML.entry_path_direct_direction_targets import summarize_target_frequencies
from ML.fractal_level_feature_builder import apply_feature_normalizer
from ML.fractal_level_feature_builder import build_fractal_level_features
from ML.fractal_level_feature_builder import fit_feature_normalizer
from ML.entry_path_trade_filter import compute_pf
from processing.fractal_preprocessing import sort_fractals_in_dataframe


DEFAULT_ROOT = Path("ML/reports/entry_path_v1_live_safe_xauusd_no_predict_pool_server_multiseed/seed_042")
DEFAULT_TRAIN_SOURCE = Path("DATA/Nero_XAUUSD_train_labeled.csv")
DEFAULT_VALIDATION_SOURCE = Path("DATA/Nero_XAUUSD_validation_labeled.csv")
DEFAULT_TEST_SOURCE = Path("DATA/Nero_XAUUSD_test_labeled.csv")
DEFAULT_VALIDATION_PREDICTIONS = DEFAULT_ROOT / "validation_predictions.csv"
DEFAULT_TEST_PREDICTIONS = DEFAULT_ROOT / "test_predictions.csv"
DEFAULT_OHLC = Path("DATA/XAUUSD_H1_OHLC.csv")
DEFAULT_OUTPUT_DIR = Path("ML/reports/entry_path_v1_binary_direction")
DEFAULT_RAW_FEATURE_SOURCE = Path("MT/MQL4/Files/Nero.csv")
DEFAULT_OLD_SCORE_THRESHOLD = -0.07158749
DEFAULT_THRESHOLD_GRID = [0.30, 0.40, 0.50, 0.60]
DEFAULT_MARGIN_GRID = [0.00, 0.05, 0.10, 0.15]
DEFAULT_NEAREST_K = 4


def selection_policy() -> dict[str, Any]:
    """Возвращает машинно-читаемые gates и порядок сортировки validation winner."""
    return {
        "candidate_scope": "validation_only",
        "excluded_modes": ["old_score_diagnostic"],
        "required_mode": "standalone",
        "min_validation_trades": 100,
        "min_validation_pf": 1.15,
        "min_validation_sequential_pf": 1.10,
        "max_negative_years": 0,
        "exclude_one_sided_candidate": True,
        "exclude_overfitting_risk": True,
        "primary_metric": "validation_sequential_pf",
        "sort_order": [
            {"column": "validation_sequential_pf", "ascending": False},
            {"column": "validation_pf", "ascending": False},
            {"column": "validation_trades", "ascending": False},
        ],
    }


def pick_validation_winner(grid: pd.DataFrame) -> dict[str, Any]:
    if grid.empty:
        return {}
    policy = selection_policy()
    work = grid.copy()
    defaults = {
        "negative_years": 0,
        "one_sided_candidate": False,
        "overfitting_risk": False,
    }
    for column, default in defaults.items():
        if column not in work.columns:
            work[column] = default
    candidates = work[
        (work["mode"] == policy["required_mode"])
        & (work["validation_trades"] >= policy["min_validation_trades"])
        & (work["validation_pf"] >= policy["min_validation_pf"])
        & (work["validation_sequential_pf"] >= policy["min_validation_sequential_pf"])
        & (work["negative_years"] <= policy["max_negative_years"])
        & (~work["one_sided_candidate"].astype(bool))
        & (~work["overfitting_risk"].astype(bool))
    ].copy()
    if candidates.empty:
        return {}
    sort_columns = [item["column"] for item in policy["sort_order"]]
    ascending = [bool(item["ascending"]) for item in policy["sort_order"]]
    candidates = candidates.sort_values(sort_columns, ascending=ascending)
    return candidates.iloc[0].to_dict()


def write_selection_decision(
    output_dir: str | Path,
    *,
    automatic_winner: dict[str, Any],
    selected_config: dict[str, Any] | None = None,
    reason: str | None = None,
) -> Path:
    """Пишет selection_decision.json для reproducible validation-only selection."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    selected = selected_config or automatic_winner
    automatic_config = automatic_winner.get("config") if automatic_winner else None
    selected_config_id = selected.get("config") if selected else None
    is_override = bool(automatic_config and selected_config_id and automatic_config != selected_config_id)
    if is_override and not reason:
        raise ValueError("selection override requires an explicit reason")
    payload = {
        "test_set_used": False,
        "policy": selection_policy(),
        "automatic_winner": automatic_winner,
        "selected_config": selected,
        "decision_type": "manual_override" if is_override else "automatic",
        "reason": reason or ("automatic validation winner" if selected else "no validation winner"),
    }
    path = output_path / "selection_decision.json"
    path.write_text(json.dumps(_jsonable(payload), ensure_ascii=False, indent=2), encoding="utf-8")
    return path


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


def _binary_signal(
    p_buy: np.ndarray,
    p_sell: np.ndarray,
    buy_threshold: float,
    sell_threshold: float,
    margin: float,
) -> np.ndarray:
    buy_fire = p_buy >= buy_threshold
    sell_fire = p_sell >= sell_threshold
    if margin > 0:
        buy_margin = (p_buy - p_sell) >= margin
        sell_margin = (p_sell - p_buy) >= margin
        buy_ok = buy_fire & buy_margin
        sell_ok = sell_fire & sell_margin
    else:
        buy_ok = buy_fire & ~sell_fire
        sell_ok = sell_fire & ~buy_fire
    signals = np.zeros(len(p_buy), dtype=int)
    signals[buy_ok] = 1
    signals[sell_ok] = -1
    return signals


def run_target_frequency(
    *,
    train_source: str | Path,
    validation_source: str | Path,
    ohlc: str | Path,
    output_dir: str | Path,
) -> dict[str, Any]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    usecols = ["time", "signal", "ATR", "up_3", "dn_3", "up_6", "dn_6", "up_12", "dn_12", "up_24", "dn_24", "up_48", "dn_48"]
    train = pd.read_csv(Path(train_source), sep=";", usecols=usecols)
    validation = pd.read_csv(Path(validation_source), sep=";", usecols=usecols)
    frequencies = summarize_target_frequencies(
        {"train": train, "validation": validation},
        ohlc_path=ohlc,
    )
    target_path = output_path / "target_frequency.csv"
    frequencies.to_csv(target_path, sep=";", index=False)
    gate = (
        frequencies.groupby("target_family")["gate_pass"].first().reset_index().to_dict(orient="records")
    )
    return {
        "stage": "target-frequency",
        "target_frequency_path": str(target_path),
        "test_set_used": False,
        "target_gates": gate,
        "any_gate_pass": bool(frequencies.groupby("target_family")["gate_pass"].first().any()),
    }


def run_validation_matrix(
    *,
    train_source: str | Path,
    validation_source: str | Path,
    validation_predictions: str | Path,
    ohlc: str | Path,
    output_dir: str | Path,
    old_score_threshold: float,
    raw_feature_source: str | Path | None = None,
    k: int = DEFAULT_NEAREST_K,
    threshold_grid: list[float] | None = None,
    margin_grid: list[float] | None = None,
) -> dict[str, Any]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    target_frequency_path = output_path / "target_frequency.csv"
    if not target_frequency_path.exists():
        run_target_frequency(
            train_source=train_source,
            validation_source=validation_source,
            ohlc=ohlc,
            output_dir=output_path,
        )
    target_frequency = pd.read_csv(target_frequency_path, sep=";")
    passed_targets = set(target_frequency.loc[target_frequency["gate_pass"].astype(bool), "target_family"].unique())
    if "D" not in passed_targets:
        return {"stage": "validation-matrix", "stopped": True, "reason": "target_D_gate_not_passed"}

    source_usecols = ["time", "signal", "ATR", *[f"fractal{idx}" for idx in range(100)]]
    target_usecols = ["time", "signal", "ATR", "up_3", "dn_3", "up_6", "dn_6", "up_12", "dn_12", "up_24", "dn_24", "up_48", "dn_48"]
    train_features_source = pd.read_csv(Path(train_source), sep=";", usecols=source_usecols)
    validation_features_source = pd.read_csv(Path(validation_source), sep=";", usecols=source_usecols)
    train_target_source = pd.read_csv(Path(train_source), sep=";", usecols=target_usecols)
    validation_target_source = pd.read_csv(Path(validation_source), sep=";", usecols=target_usecols)
    raw_train_features = None
    raw_validation_features = None
    feature_source = "labeled_split_fractals"
    if raw_feature_source is not None:
        raw_nrows = len(train_features_source) + len(validation_features_source)
        raw_all = pd.read_csv(Path(raw_feature_source), sep=";", usecols=source_usecols, nrows=raw_nrows)
        raw_all.columns = [str(c).strip() for c in raw_all.columns]
        raw_all = sort_fractals_in_dataframe(raw_all, debug=False)
        raw_train_features = raw_all.iloc[: len(train_features_source)].reset_index(drop=True)
        raw_validation_features = raw_all.iloc[len(train_features_source): raw_nrows].reset_index(drop=True)
        feature_source = str(raw_feature_source)

    t0 = time.perf_counter()
    x_train_raw = build_fractal_level_features(
        train_features_source,
        raw_price_frame=raw_train_features,
        input_family="nearest_k",
        k=k,
    )
    feature_build_seconds = time.perf_counter() - t0
    x_validation_raw = build_fractal_level_features(
        validation_features_source,
        raw_price_frame=raw_validation_features,
        input_family="nearest_k",
        k=k,
    )
    normalizer = fit_feature_normalizer(x_train_raw)
    x_train = _model_feature_frame(apply_feature_normalizer(x_train_raw, normalizer))
    x_validation = _model_feature_frame(apply_feature_normalizer(x_validation_raw, normalizer))

    train_buy_good, train_sell_good = build_target_d_masks(
        train_target_source, ohlc, trail_n=2.0, profit_z=1.0, horizon=24
    )
    validation_buy_good, validation_sell_good = build_target_d_masks(
        validation_target_source, ohlc, trail_n=2.0, profit_z=1.0, horizon=24
    )
    y_buy_train = train_buy_good.astype(int)
    y_sell_train = train_sell_good.astype(int)

    returns = compute_buy_sell_returns(validation_target_source, ohlc, horizon=24)
    validation_pred = pd.read_csv(Path(validation_predictions), sep=";")
    score = pd.to_numeric(validation_pred["pred_ret_24_dir_atr"], errors="coerce").fillna(float("-inf"))

    effective_thresholds = threshold_grid if threshold_grid is not None else DEFAULT_THRESHOLD_GRID
    effective_margins = margin_grid if margin_grid is not None else DEFAULT_MARGIN_GRID

    model_variants = [
        ("hgb", _make_hgb),
        ("rf", _make_rf),
    ]

    rows = []
    feature_importance_frames = []
    for model_label, model_factory in model_variants:
        buy_model = model_factory()
        buy_sample_weight = compute_sample_weight("balanced", y_buy_train)
        buy_model.fit(x_train, y_buy_train, sample_weight=buy_sample_weight)

        sell_model = model_factory()
        sell_sample_weight = compute_sample_weight("balanced", y_sell_train)
        sell_model.fit(x_train, y_sell_train, sample_weight=sell_sample_weight)

        p_buy = buy_model.predict_proba(x_validation)[:, 1]
        p_sell = sell_model.predict_proba(x_validation)[:, 1]

        if model_label == "rf":
            feature_importance_frames.append(
                _feature_importance_frame_binary(buy_model, list(x_train.columns), "D_buy_rf")
            )
            feature_importance_frames.append(
                _feature_importance_frame_binary(sell_model, list(x_train.columns), "D_sell_rf")
            )

        for buy_threshold in effective_thresholds:
            for sell_threshold in effective_thresholds:
                for margin in effective_margins:
                    if margin == 0.0:
                        variant_label = "simple"
                    else:
                        variant_label = f"margin_{margin:.2f}"
                    signals = _binary_signal(p_buy, p_sell, buy_threshold, sell_threshold, margin)
                    eval_frame = _build_eval_frame_binary(
                        validation_target_source, signals, p_buy, p_sell, returns
                    )
                    old_score_frame = eval_frame.copy()
                    old_score_frame["selected"] = old_score_frame["selected"] & (score.reset_index(drop=True) >= float(old_score_threshold))

                    rows.append(
                        _grid_row_binary(
                            eval_frame,
                            validation_buy_good,
                            validation_sell_good,
                            buy_threshold=buy_threshold,
                            sell_threshold=sell_threshold,
                            margin=margin,
                            mode="standalone",
                            model_type=model_label,
                            feature_count=int(x_train.shape[1]),
                            validation_candidates=int(eval_frame["selected"].sum()),
                            p_buy=p_buy,
                            p_sell=p_sell,
                        )
                    )
                    rows.append(
                        _grid_row_binary(
                            old_score_frame,
                            validation_buy_good,
                            validation_sell_good,
                            buy_threshold=buy_threshold,
                            sell_threshold=sell_threshold,
                            margin=margin,
                            mode="old_score_diagnostic",
                            model_type=model_label,
                            feature_count=int(x_train.shape[1]),
                            validation_candidates=int(old_score_frame["selected"].sum()),
                            p_buy=p_buy,
                            p_sell=p_sell,
                        )
                    )

    grid = pd.DataFrame(rows)
    winner = pick_validation_winner(grid)
    selection_decision_path = write_selection_decision(output_path, automatic_winner=winner)
    validation_grid_path = output_path / "validation_grid.csv"
    feature_importance_path = output_path / "feature_importance.csv"
    summary_path = output_path / "summary.json"
    grid.to_csv(validation_grid_path, sep=";", index=False)
    if feature_importance_frames:
        pd.concat(feature_importance_frames, ignore_index=True).to_csv(
            feature_importance_path, sep=";", index=False
        )
    feature_manifest = {
        "feature_source": feature_source,
        "target_source": str(validation_source),
        "diagnostic_source": str(validation_predictions),
        "raw_price_distance_source": feature_source,
        "test_artifacts_used_for_selection": False,
        "notes": [
            "distance features use raw_price_frame when raw_feature_source is provided",
            "Target D is OHLC-derived; A/C ATR targets require raw up/dn over raw ATR",
        ],
    }
    feature_manifest_path = output_path / "feature_manifest.json"
    feature_manifest_path.write_text(json.dumps(_jsonable(feature_manifest), ensure_ascii=False, indent=2), encoding="utf-8")
    summary = {
        "stage": "validation-matrix",
        "test_set_used": False,
        "target_family": "D",
        "winner": winner,
        "selection_policy": selection_policy(),
        "selection_decision_path": str(selection_decision_path),
        "feature_build_seconds": float(feature_build_seconds),
        "feature_count": int(x_train.shape[1]),
        "input_family": f"nearest_k{k}",
        "feature_manifest_path": str(feature_manifest_path),
    }
    summary_path.write_text(json.dumps(_jsonable(summary), ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "stage": "validation-matrix",
        "validation_grid_path": str(validation_grid_path),
        "feature_importance_path": str(feature_importance_path) if feature_importance_frames else None,
        "summary_path": str(summary_path),
        "selection_decision_path": str(selection_decision_path),
        "winner_found": bool(winner),
        "winner": winner,
    }


def _make_hgb() -> HistGradientBoostingClassifier:
    return HistGradientBoostingClassifier(
        max_iter=200, max_depth=5, min_samples_leaf=40,
        learning_rate=0.05, random_state=42,
    )


def _make_rf() -> RandomForestClassifier:
    return RandomForestClassifier(
        n_estimators=160, min_samples_leaf=20,
        class_weight="balanced_subsample", random_state=42, n_jobs=-1,
    )


def _build_eval_frame_binary(
    source: pd.DataFrame,
    signals: np.ndarray,
    p_buy: np.ndarray,
    p_sell: np.ndarray,
    returns: pd.DataFrame,
) -> pd.DataFrame:
    selected = signals != 0
    true_ret = np.zeros(len(signals), dtype=float)
    buy_mask = signals == 1
    sell_mask = signals == -1
    true_ret[buy_mask] = returns.loc[buy_mask, "buy_ret_atr"].values if buy_mask.any() else 0.0
    true_ret[sell_mask] = returns.loc[sell_mask, "sell_ret_atr"].values if sell_mask.any() else 0.0
    both_high = (p_buy >= 0.5) & (p_sell >= 0.5)
    return pd.DataFrame({
        "time": pd.to_datetime(source["time"], format="%Y.%m.%d %H:%M", errors="coerce"),
        "candidate_signal": signals,
        "true_ret_24_dir_atr": true_ret,
        "p_buy": p_buy,
        "p_sell": p_sell,
        "selected": selected,
        "both_high_rate_row": both_high.astype(int),
    })


def _grid_row_binary(
    frame: pd.DataFrame,
    buy_good: pd.Series,
    sell_good: pd.Series,
    *,
    buy_threshold: float,
    sell_threshold: float,
    margin: float,
    mode: str,
    model_type: str,
    feature_count: int,
    validation_candidates: int,
    p_buy: np.ndarray,
    p_sell: np.ndarray,
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
    features_per_candidate = float(feature_count / max(validation_candidates, 1))
    both_high_count = int(frame.loc[frame["selected"], "both_high_rate_row"].sum()) if len(selected) > 0 else 0
    conflict_count = int(((frame["candidate_signal"] == 1) & (p_buy >= buy_threshold) & (p_sell >= sell_threshold)).sum()) + int(((frame["candidate_signal"] == -1) & (p_sell >= sell_threshold) & (p_buy >= buy_threshold)).sum())
    buy_trades = int(len(buy))
    sell_trades = int(len(sell))
    total_trades = int(len(selected))
    ambiguous_rate = float((buy_good & sell_good).mean())
    return {
        "config": f"D_{model_type}_buy{buy_threshold:.2f}_sell{sell_threshold:.2f}_m{margin:.2f}_{mode}",
        "mode": mode,
        "target_family": "D",
        "target_params": '{"horizon":24,"profit_z":1.0,"trail_n":2.0}',
        "model_type": model_type,
        "buy_threshold": buy_threshold,
        "sell_threshold": sell_threshold,
        "margin": margin,
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
        "buy_mean_pnl_atr": float(buy.mean()) if buy_trades else 0.0,
        "sell_mean_pnl_atr": float(sell.mean()) if sell_trades else 0.0,
        "buy_sell_balance": float(min(buy_trades, sell_trades) / max(total_trades, 1)),
        "one_sided_candidate": bool(total_trades > 0 and min(buy_trades, sell_trades) / max(total_trades, 1) < 0.20),
        "both_high_rate": float(both_high_count / max(total_trades, 1)),
        "conflict_rate": float(conflict_count / max(total_trades, 1)) if total_trades else 0.0,
        "ambiguous_rate": ambiguous_rate,
        "yearly_pf": json.dumps(yearly, ensure_ascii=False),
        "negative_years": int(negative_years),
        "feature_count": feature_count,
        "features_per_validation_candidates": features_per_candidate,
        "overfitting_risk": bool(features_per_candidate >= 0.10),
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


def _feature_importance_frame_binary(
    model: RandomForestClassifier,
    feature_names: list[str],
    config_id: str,
) -> pd.DataFrame:
    order = np.argsort(model.feature_importances_)[::-1][:20]
    return pd.DataFrame([
        {
            "config_id": config_id,
            "rank": int(rank + 1),
            "feature": feature_names[idx],
            "importance": float(model.feature_importances_[idx]),
        }
        for rank, idx in enumerate(order)
    ])


def run_frozen_test(
    *,
    train_source: str | Path,
    validation_source: str | Path,
    test_source: str | Path,
    validation_predictions: str | Path,
    test_predictions: str | Path,
    ohlc: str | Path,
    output_dir: str | Path,
    old_score_threshold: float,
    k: int = DEFAULT_NEAREST_K,
    model_type: str = "rf",
    buy_threshold: float = 0.4,
    sell_threshold: float = 0.6,
    margin: float = 0.10,
    target_family: str = "D",
) -> dict[str, Any]:
    """Frozen test: retrain on train+validation, evaluate on test with frozen config."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    source_usecols = ["time", "signal", "ATR", *[f"fractal{idx}" for idx in range(100)]]
    target_usecols = ["time", "signal", "ATR", "up_3", "dn_3", "up_6", "dn_6", "up_12", "dn_12", "up_24", "dn_24", "up_48", "dn_48"]

    train_features = pd.read_csv(Path(train_source), sep=";", usecols=source_usecols)
    validation_features = pd.read_csv(Path(validation_source), sep=";", usecols=source_usecols)
    test_features = pd.read_csv(Path(test_source), sep=";", usecols=source_usecols)
    train_target = pd.read_csv(Path(train_source), sep=";", usecols=target_usecols)
    validation_target = pd.read_csv(Path(validation_source), sep=";", usecols=target_usecols)
    test_target = pd.read_csv(Path(test_source), sep=";", usecols=target_usecols)

    combined_features = pd.concat([train_features, validation_features], ignore_index=True)
    combined_target = pd.concat([train_target, validation_target], ignore_index=True)

    x_combined_raw = build_fractal_level_features(combined_features, input_family="nearest_k", k=k)
    x_test_raw = build_fractal_level_features(test_features, input_family="nearest_k", k=k)
    normalizer = fit_feature_normalizer(x_combined_raw)
    x_combined = _model_feature_frame(apply_feature_normalizer(x_combined_raw, normalizer))
    x_test = _model_feature_frame(apply_feature_normalizer(x_test_raw, normalizer))

    combined_buy_good, combined_sell_good = build_target_d_masks(
        combined_target, ohlc, trail_n=2.0, profit_z=1.0, horizon=24
    )
    test_buy_good, test_sell_good = build_target_d_masks(
        test_target, ohlc, trail_n=2.0, profit_z=1.0, horizon=24
    )
    test_returns = compute_buy_sell_returns(test_target, ohlc, horizon=24)

    y_buy_combined = combined_buy_good.astype(int)
    y_sell_combined = combined_sell_good.astype(int)

    model_variants = {"rf": _make_rf, "hgb": _make_hgb}
    model_factory = model_variants.get(model_type)
    if model_factory is None:
        raise ValueError(f"unsupported model_type for frozen test: {model_type}")

    buy_model = model_factory()
    buy_sw = compute_sample_weight("balanced", y_buy_combined)
    buy_model.fit(x_combined, y_buy_combined, sample_weight=buy_sw)

    sell_model = model_factory()
    sell_sw = compute_sample_weight("balanced", y_sell_combined)
    sell_model.fit(x_combined, y_sell_combined, sample_weight=sell_sw)

    p_buy = buy_model.predict_proba(x_test)[:, 1]
    p_sell = sell_model.predict_proba(x_test)[:, 1]

    signals = _binary_signal(p_buy, p_sell, buy_threshold, sell_threshold, margin)
    selected = signals != 0
    true_ret = np.zeros(len(signals), dtype=float)
    buy_mask = signals == 1
    sell_mask = signals == -1
    true_ret[buy_mask] = test_returns.loc[buy_mask, "buy_ret_atr"].values if buy_mask.any() else 0.0
    true_ret[sell_mask] = test_returns.loc[sell_mask, "sell_ret_atr"].values if sell_mask.any() else 0.0

    eval_frame = pd.DataFrame({
        "time": pd.to_datetime(test_target["time"], format="%Y.%m.%d %H:%M", errors="coerce"),
        "candidate_signal": signals,
        "true_ret_24_dir_atr": true_ret,
        "p_buy": p_buy,
        "p_sell": p_sell,
        "selected": selected,
    })

    selected_df = eval_frame.loc[eval_frame["selected"]].copy()
    buy = selected_df.loc[selected_df["candidate_signal"] == 1, "true_ret_24_dir_atr"].to_numpy(dtype=np.float64)
    sell = selected_df.loc[selected_df["candidate_signal"] == -1, "true_ret_24_dir_atr"].to_numpy(dtype=np.float64)
    pnl = selected_df["true_ret_24_dir_atr"].to_numpy(dtype=np.float64)
    sequential = run_sequential_all_rows(
        eval_frame.rename(columns={"candidate_signal": "signal"}),
        eval_frame["selected"],
        hold_bars=24,
    )
    yearly = _yearly_pf(selected_df)

    result = {
        "stage": "frozen-test",
        "config": f"{target_family}_{model_type}_buy{buy_threshold:.2f}_sell{sell_threshold:.2f}_m{margin:.2f}",
        "model_type": model_type,
        "buy_threshold": buy_threshold,
        "sell_threshold": sell_threshold,
        "margin": margin,
        "target_family": target_family,
        "input_family": f"nearest_k{k}",
        "test_trades": int(len(selected_df)),
        "test_pf": compute_pf(pnl),
        "test_sequential_pf": float(sequential["pf"]),
        "test_sequential_trades": int(sequential["trades"]),
        "test_buy_trades": int(len(buy)),
        "test_sell_trades": int(len(sell)),
        "test_buy_pf": compute_pf(buy),
        "test_sell_pf": compute_pf(sell),
        "test_buy_win_rate": float((buy > 0).mean()) if len(buy) else 0.0,
        "test_sell_win_rate": float((sell > 0).mean()) if len(sell) else 0.0,
        "test_buy_sell_balance": float(min(len(buy), len(sell)) / max(len(selected_df), 1)),
        "test_yearly_pf": yearly,
        "negative_years": sum(1 for y in yearly if y["trades"] >= 20 and y["pf"] < 1.0),
        "feature_count": int(x_combined.shape[1]),
        "train_combined_rows": int(len(combined_features)),
    }

    result_path = output_path / "frozen_test.json"
    result_path.write_text(json.dumps(_jsonable(result), ensure_ascii=False, indent=2), encoding="utf-8")

    frozen_grid_path = output_path / "frozen_test_grid.csv"
    eval_frame.to_csv(frozen_grid_path, sep=";", index=False)

    print(json.dumps(_jsonable(result), ensure_ascii=False, indent=2))
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Binary BUY/SELL direction benchmark.")
    parser.add_argument("--stage", choices=["target-frequency", "validation-matrix", "frozen-test"], required=True)
    parser.add_argument("--train-source", default=str(DEFAULT_TRAIN_SOURCE))
    parser.add_argument("--validation-source", default=str(DEFAULT_VALIDATION_SOURCE))
    parser.add_argument("--test-source", default=str(DEFAULT_TEST_SOURCE))
    parser.add_argument("--validation-predictions", default=str(DEFAULT_VALIDATION_PREDICTIONS))
    parser.add_argument("--test-predictions", default=str(DEFAULT_TEST_PREDICTIONS))
    parser.add_argument("--ohlc", default=str(DEFAULT_OHLC))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--old-score-threshold", type=float, default=DEFAULT_OLD_SCORE_THRESHOLD)
    parser.add_argument("--raw-feature-source", default=str(DEFAULT_RAW_FEATURE_SOURCE))
    parser.add_argument("--k", type=int, default=DEFAULT_NEAREST_K, choices=[4, 6, 8, 16])
    parser.add_argument("--model", type=str, default="rf", choices=["rf", "hgb"])
    parser.add_argument("--buy-threshold", type=float, default=0.4)
    parser.add_argument("--sell-threshold", type=float, default=0.6)
    parser.add_argument("--margin", type=float, default=0.10)
    return parser.parse_args()


def main() -> dict[str, Any]:
    args = parse_args()
    if args.stage == "target-frequency":
        result = run_target_frequency(
            train_source=args.train_source,
            validation_source=args.validation_source,
            ohlc=args.ohlc,
            output_dir=args.output_dir,
        )
    elif args.stage == "validation-matrix":
        result = run_validation_matrix(
            train_source=args.train_source,
            validation_source=args.validation_source,
            validation_predictions=args.validation_predictions,
            ohlc=args.ohlc,
            output_dir=args.output_dir,
            old_score_threshold=args.old_score_threshold,
            raw_feature_source=args.raw_feature_source,
            k=args.k,
        )
    elif args.stage == "frozen-test":
        result = run_frozen_test(
            train_source=args.train_source,
            validation_source=args.validation_source,
            test_source=args.test_source,
            validation_predictions=args.validation_predictions,
            test_predictions=args.test_predictions,
            ohlc=args.ohlc,
            output_dir=args.output_dir,
            old_score_threshold=args.old_score_threshold,
            k=args.k,
            model_type=args.model,
            buy_threshold=args.buy_threshold,
            sell_threshold=args.sell_threshold,
            margin=args.margin,
        )
    else:
        raise ValueError(f"unsupported stage: {args.stage}")
    print(json.dumps(_jsonable(result), ensure_ascii=False, indent=2))
    return result


if __name__ == "__main__":
    main()