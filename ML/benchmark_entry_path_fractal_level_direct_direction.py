# =============================================================================
# Файл: benchmark_entry_path_fractal_level_direct_direction.py
# Назначение: Direct SELL/SKIP/BUY benchmark по fractal-level признакам.
# Обновлён: 2026-05-15
# Входные данные:
#   - DATA/Nero_XAUUSD_*_labeled.csv, prediction CSV, OHLC CSV
# Выходные данные:
#   - gate artifacts и benchmark reports (куда: ML/reports/entry_path_v1_fractal_level_direct_direction/)
# Использование:
#   python -m ML.benchmark_entry_path_fractal_level_direct_direction --stage feature-audit
# Примечания:
#   - Не использует source["signal"] как input или target source.
# =============================================================================

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

from ML.benchmark_entry_path_all_rows_ranking import run_sequential_all_rows
from ML.benchmark_entry_path_direct_bar_model import compute_buy_sell_returns
from ML.entry_path_direct_direction_targets import build_target_d_classes
from ML.fractal_level_feature_builder import audit_fractal_rows
from ML.fractal_level_feature_builder import apply_feature_normalizer
from ML.fractal_level_feature_builder import build_fractal_level_features
from ML.fractal_level_feature_builder import build_feature_contract
from ML.fractal_level_feature_builder import fit_feature_normalizer
from ML.entry_path_trade_filter import compute_pf
from ML.entry_path_direct_direction_targets import summarize_target_frequencies


DEFAULT_ROOT = Path("ML/reports/entry_path_v1_live_safe_xauusd_no_predict_pool_server_multiseed/seed_042")
DEFAULT_TRAIN_SOURCE = Path("DATA/Nero_XAUUSD_train_labeled.csv")
DEFAULT_VALIDATION_SOURCE = Path("DATA/Nero_XAUUSD_validation_labeled.csv")
DEFAULT_TEST_SOURCE = Path("DATA/Nero_XAUUSD_test_labeled.csv")
DEFAULT_VALIDATION_PREDICTIONS = DEFAULT_ROOT / "validation_predictions.csv"
DEFAULT_TEST_PREDICTIONS = DEFAULT_ROOT / "test_predictions.csv"
DEFAULT_OHLC = Path("DATA/XAUUSD_H1_OHLC.csv")
DEFAULT_OUTPUT_DIR = Path("ML/reports/entry_path_v1_fractal_level_direct_direction")
DEFAULT_OLD_SCORE_THRESHOLD = -0.07158749
DEFAULT_THRESHOLD_GRID = [0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90]
DEFAULT_NEAREST_K = 4
E0_THRESHOLD_GRID = [0.10, 0.20, 0.30, 0.40]


def pick_validation_winner(grid: pd.DataFrame) -> dict[str, Any]:
    """Select standalone validation winner; old-score diagnostics cannot win."""
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


def _audit_usecols() -> list[str]:
    return ["time", "ATR", *[f"fractal{idx}" for idx in range(100)]]


def _load_audit_source(path: str | Path) -> pd.DataFrame:
    return pd.read_csv(Path(path), sep=";", usecols=_audit_usecols())


def run_feature_audit(
    *,
    train_source: str | Path,
    validation_source: str | Path,
    test_source: str | Path,
    output_dir: str | Path,
) -> dict[str, Any]:
    """Пишет live-safe audit и feature contract для direct-direction ветки."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    split_paths = {
        "train": Path(train_source),
        "validation": Path(validation_source),
        "test": Path(test_source),
    }
    split_audits = {
        split: audit_fractal_rows(_load_audit_source(path))
        for split, path in split_paths.items()
    }
    aggregate = {
        "row_count": sum(int(item["row_count"]) for item in split_audits.values()),
        "missing_invalid_fractal0_rows": sum(int(item["missing_invalid_fractal0_rows"]) for item in split_audits.values()),
        "future_fractal_rows": sum(int(item["future_fractal_rows"]) for item in split_audits.values()),
        "unknown_time_format_rows": sum(int(item["unknown_time_format_rows"]) for item in split_audits.values()),
        "fractal0_updn_nonzero_rows": sum(int(item["fractal0_updn_nonzero_rows"]) for item in split_audits.values()),
        "old_updn_nonzero_rows": sum(int(item["old_updn_nonzero_rows"]) for item in split_audits.values()),
        "sort_violation_rows": sum(int(item["sort_violation_rows"]) for item in split_audits.values()),
    }
    aggregate["old_updn_nonzero_share"] = (
        float(aggregate["old_updn_nonzero_rows"] / aggregate["row_count"])
        if aggregate["row_count"]
        else 0.0
    )
    aggregate["gate_pass"] = bool(
        aggregate["row_count"] > 0
        and aggregate["missing_invalid_fractal0_rows"] == 0
        and aggregate["future_fractal_rows"] == 0
        and aggregate["unknown_time_format_rows"] == 0
        and aggregate["sort_violation_rows"] == 0
    )
    feature_audit = {
        "stage": "feature-audit",
        "architecture": "direct_direction_sell_skip_buy",
        "inputs": {name: str(path) for name, path in split_paths.items()},
        "usecols": _audit_usecols(),
        "ignored_offline_columns": ["signal", "predict", "ret_*", "fav_*", "adv_*", "trail_*"],
        "splits": split_audits,
        "aggregate": aggregate,
    }
    feature_contract = {
        "stage": "feature-audit",
        "architecture": "direct_direction_sell_skip_buy",
        "feature_contract": build_feature_contract(fractal_count=100),
    }
    audit_path = output_path / "feature_audit.json"
    contract_path = output_path / "feature_contract.json"
    audit_path.write_text(json.dumps(_jsonable(feature_audit), ensure_ascii=False, indent=2), encoding="utf-8")
    contract_path.write_text(json.dumps(_jsonable(feature_contract), ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "feature_audit_path": str(audit_path),
        "feature_contract_path": str(contract_path),
        **feature_audit,
    }


def run_target_frequency(
    *,
    train_source: str | Path,
    validation_source: str | Path,
    ohlc: str | Path,
    output_dir: str | Path,
) -> dict[str, Any]:
    """Пишет target frequency gate для direct SELL/SKIP/BUY targets."""
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
    k: int = DEFAULT_NEAREST_K,
    geometry_only: bool = False,
    threshold_grid: list[float] | None = None,
) -> dict[str, Any]:
    """Train Stage 1 nearest_k16 direct-direction model and write validation grid."""
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
    if not passed_targets:
        return {"stage": "validation-matrix", "stopped": True, "reason": "target_D_gate_not_passed"}

    input_family_label = f"nearest_k{k}" if not geometry_only else f"nearest_k{k}_geometry_only"
    source_usecols = ["time", "signal", "ATR", *[f"fractal{idx}" for idx in range(100)]]
    target_usecols = ["time", "signal", "ATR", "up_3", "dn_3", "up_6", "dn_6", "up_12", "dn_12", "up_24", "dn_24", "up_48", "dn_48"]
    train_features_source = pd.read_csv(Path(train_source), sep=";", usecols=source_usecols)
    validation_features_source = pd.read_csv(Path(validation_source), sep=";", usecols=source_usecols)
    train_target_source = pd.read_csv(Path(train_source), sep=";", usecols=target_usecols)
    validation_target_source = pd.read_csv(Path(validation_source), sep=";", usecols=target_usecols)

    t0 = time.perf_counter()
    x_train_raw = build_fractal_level_features(train_features_source, input_family="nearest_k", k=k, geometry_only=geometry_only)
    feature_build_seconds = time.perf_counter() - t0
    x_validation_raw = build_fractal_level_features(validation_features_source, input_family="nearest_k", k=k, geometry_only=geometry_only)
    normalizer = fit_feature_normalizer(x_train_raw)
    x_train = _model_feature_frame(apply_feature_normalizer(x_train_raw, normalizer))
    x_validation = _model_feature_frame(apply_feature_normalizer(x_validation_raw, normalizer))
    returns = compute_buy_sell_returns(validation_target_source, ohlc, horizon=24)
    validation_pred = pd.read_csv(Path(validation_predictions), sep=";")
    score = pd.to_numeric(validation_pred["pred_ret_24_dir_atr"], errors="coerce").fillna(float("-inf"))

    effective_threshold_grid = threshold_grid if threshold_grid is not None else DEFAULT_THRESHOLD_GRID
    rows = []
    frames_by_threshold: dict[str, pd.DataFrame] = {}
    feature_importance_frames = []
    for target_family in sorted(passed_targets):
        y_train, y_validation, target_params = _build_target_classes_for_family(
            target_family,
            train_target_source,
            validation_target_source,
            ohlc=ohlc,
        )
        model = RandomForestClassifier(
            n_estimators=160,
            min_samples_leaf=20,
            class_weight="balanced_subsample",
            random_state=42,
            n_jobs=-1,
        )
        model.fit(x_train, y_train)
        probabilities = _class_probability_frame(model, x_validation)
        config_id = f"{target_family}_{input_family_label}"
        feature_importance_frames.append(_feature_importance_frame(model, list(x_train.columns), config_id=config_id))
        for threshold in effective_threshold_grid:
            eval_frame = _build_eval_frame_from_probabilities(validation_target_source, probabilities, returns, threshold)
            frames_by_threshold[f"{target_family}_{threshold:.2f}"] = eval_frame
            rows.append(
                _grid_row(
                    eval_frame,
                    y_validation,
                    threshold=float(threshold),
                    mode="standalone",
                    feature_count=int(x_train.shape[1]),
                    validation_candidates=int((eval_frame["candidate_signal"] != 0).sum()),
                    target_family=target_family,
                    target_params=target_params,
                    input_family=input_family_label,
                )
            )
            old_score_frame = eval_frame.copy()
            old_score_frame["selected"] = (old_score_frame["candidate_signal"] != 0) & (score.reset_index(drop=True) >= float(old_score_threshold))
            rows.append(
                _grid_row(
                    old_score_frame,
                    y_validation,
                    threshold=float(threshold),
                    mode="old_score_diagnostic",
                    feature_count=int(x_train.shape[1]),
                    validation_candidates=int(old_score_frame["selected"].sum()),
                    target_family=target_family,
                    target_params=target_params,
                    input_family=input_family_label,
                )
            )

    grid = pd.DataFrame(rows)
    winner = pick_validation_winner(grid)
    validation_grid_path = output_path / "validation_grid.csv"
    feature_importance_path = output_path / "feature_importance.csv"
    score_distribution_path = output_path / "score_distribution.csv"
    summary_path = output_path / "summary.json"
    grid.to_csv(validation_grid_path, sep=";", index=False)
    pd.concat(feature_importance_frames, ignore_index=True).to_csv(
        feature_importance_path, sep=";", index=False
    )
    _score_distribution_frame(validation_target_source, score, frames_by_threshold).to_csv(
        score_distribution_path, sep=";", index=False
    )
    summary = {
        "stage": "validation-matrix",
        "test_set_used": False,
        "passed_targets": sorted(passed_targets),
        "winner": winner,
        "feature_build_seconds": float(feature_build_seconds),
        "feature_build_rows_per_second": float(len(train_features_source) / feature_build_seconds) if feature_build_seconds > 0 else 0.0,
        "feature_count": int(x_train.shape[1]),
        "input_family": input_family_label,
        "normalizer": normalizer,
    }
    summary_path.write_text(json.dumps(_jsonable(summary), ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "stage": "validation-matrix",
        "validation_grid_path": str(validation_grid_path),
        "feature_importance_path": str(feature_importance_path),
        "score_distribution_path": str(score_distribution_path),
        "summary_path": str(summary_path),
        "winner_found": bool(winner),
        "winner": winner,
    }
    summary_path.write_text(json.dumps(_jsonable(summary), ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "stage": "validation-matrix",
        "validation_grid_path": str(validation_grid_path),
        "feature_importance_path": str(feature_importance_path),
        "score_distribution_path": str(score_distribution_path),
        "summary_path": str(summary_path),
        "winner_found": bool(winner),
        "winner": winner,
    }


def _model_feature_frame(features: pd.DataFrame) -> pd.DataFrame:
    """Drops diagnostic-only feature columns before model fit/predict."""
    return features[[column for column in features.columns if not str(column).endswith("_source_index")]].copy()


def _build_target_classes_for_family(
    target_family: str,
    train_source: pd.DataFrame,
    validation_source: pd.DataFrame,
    *,
    ohlc: str | Path,
) -> tuple[pd.Series, pd.Series, str]:
    from ML.entry_path_direct_direction_targets import build_buy_sell_fav_adv
    from ML.entry_path_direct_direction_targets import build_target_a_classes
    from ML.entry_path_direct_direction_targets import build_target_c_classes

    if target_family == "A":
        params = {"stop_n": 0.2, "take_y": 0.3}
        train_moves = build_buy_sell_fav_adv(train_source, horizons=(6,))
        validation_moves = build_buy_sell_fav_adv(validation_source, horizons=(6,))
        return (
            build_target_a_classes(train_moves, **params),
            build_target_a_classes(validation_moves, **params),
            json.dumps(params, sort_keys=True, separators=(",", ":")),
        )
    if target_family == "C":
        params = {"take_x": 0.5, "adverse_y": 0.3}
        train_moves = build_buy_sell_fav_adv(train_source, horizons=(12, 24))
        validation_moves = build_buy_sell_fav_adv(validation_source, horizons=(12, 24))
        return (
            build_target_c_classes(train_moves, **params),
            build_target_c_classes(validation_moves, **params),
            json.dumps(params, sort_keys=True, separators=(",", ":")),
        )
    if target_family == "D":
        params = {"horizon": 24, "profit_z": 1.0, "trail_n": 2.0}
        return (
            build_target_d_classes(train_source, ohlc, **params),
            build_target_d_classes(validation_source, ohlc, **params),
            json.dumps(params, sort_keys=True, separators=(",", ":")),
        )
    raise ValueError(f"unsupported target family: {target_family}")


def _class_probability_frame(model: RandomForestClassifier, features: pd.DataFrame) -> pd.DataFrame:
    raw = model.predict_proba(features)
    out = pd.DataFrame(0.0, index=features.index, columns=[-1, 0, 1])
    for pos, klass in enumerate(model.classes_):
        out[int(klass)] = raw[:, pos]
    return out


def _build_eval_frame_from_probabilities(
    source: pd.DataFrame,
    probabilities: pd.DataFrame,
    returns: pd.DataFrame,
    threshold: float,
) -> pd.DataFrame:
    p_sell = probabilities[-1].astype(float)
    p_buy = probabilities[1].astype(float)
    signal = pd.Series(0, index=probabilities.index, dtype="int64")
    signal.loc[(p_buy >= float(threshold)) & (p_buy > p_sell)] = 1
    signal.loc[(p_sell >= float(threshold)) & (p_sell > p_buy)] = -1
    true_ret = pd.Series(0.0, index=probabilities.index, dtype="float64")
    true_ret.loc[signal == 1] = pd.to_numeric(returns.loc[signal == 1, "buy_ret_atr"], errors="coerce").fillna(0.0)
    true_ret.loc[signal == -1] = pd.to_numeric(returns.loc[signal == -1, "sell_ret_atr"], errors="coerce").fillna(0.0)
    return pd.DataFrame(
        {
            "time": pd.to_datetime(source["time"], format="%Y.%m.%d %H:%M", errors="coerce"),
            "candidate_signal": signal,
            "true_ret_24_dir_atr": true_ret,
            "direction_margin": (p_buy - p_sell).abs(),
            "max_direction_probability": pd.concat([p_buy, p_sell], axis=1).max(axis=1),
            "selected": signal != 0,
        }
    )


def _grid_row(
    frame: pd.DataFrame,
    target: pd.Series,
    *,
    threshold: float,
    mode: str,
    feature_count: int,
    validation_candidates: int,
    target_family: str,
    target_params: str,
    input_family: str,
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
    old_signal = pd.Series(target).reset_index(drop=True)
    overlap = selected["candidate_signal"].reset_index(drop=True).ne(0) & old_signal.loc[selected.index].reset_index(drop=True).ne(0)
    buy_trades = int(len(buy))
    sell_trades = int(len(sell))
    total_trades = int(len(selected))
    return {
        "config": f"{target_family}_{input_family}_{threshold:.2f}_{mode}",
        "mode": mode,
        "target_family": target_family,
        "target_params": target_params,
        "input_family": input_family,
        "threshold": float(threshold),
        "direction_margin_mean": float(selected["direction_margin"].mean()) if total_trades else 0.0,
        "max_direction_probability_mean": float(selected["max_direction_probability"].mean()) if total_trades else 0.0,
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
        "target_selected_match_rate": float((selected["candidate_signal"] == target.loc[selected.index]).mean()) if total_trades else 0.0,
        "yearly_pf": json.dumps(yearly, ensure_ascii=False),
        "negative_years": int(negative_years),
        "feature_count": int(feature_count),
        "features_per_validation_candidates": features_per_candidate,
        "overfitting_risk": bool(features_per_candidate >= 0.10),
        "overlap_with_old_signal_rate": float(overlap.mean()) if total_trades else 0.0,
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


def _feature_importance_frame(model: RandomForestClassifier, feature_names: list[str], *, config_id: str) -> pd.DataFrame:
    order = np.argsort(model.feature_importances_)[::-1][:20]
    return pd.DataFrame(
        [
            {
                "config_id": config_id,
                "rank": int(rank + 1),
                "feature": feature_names[idx],
                "importance": float(model.feature_importances_[idx]),
            }
            for rank, idx in enumerate(order)
        ]
    )


def _score_distribution_frame(
    source: pd.DataFrame,
    score: pd.Series,
    frames_by_threshold: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    old_signal = pd.to_numeric(source["signal"], errors="coerce").fillna(0).astype(int).reset_index(drop=True)
    rows = [_score_distribution_row("all_rows", score)]
    rows.append(_score_distribution_row("old_signal_nonzero", score.loc[old_signal != 0]))
    for label, frame in frames_by_threshold.items():
        rows.append(_score_distribution_row(f"candidate_{label}", score.loc[frame["candidate_signal"].reset_index(drop=True) != 0]))
    return pd.DataFrame(rows)


def _score_distribution_row(universe: str, values: pd.Series) -> dict[str, Any]:
    values = pd.to_numeric(values, errors="coerce").dropna()
    return {
        "universe": universe,
        "count": int(len(values)),
        "mean": float(values.mean()) if len(values) else 0.0,
        "median": float(values.median()) if len(values) else 0.0,
        "std": float(values.std(ddof=0)) if len(values) else 0.0,
        "p10": float(values.quantile(0.10)) if len(values) else 0.0,
        "p25": float(values.quantile(0.25)) if len(values) else 0.0,
        "p75": float(values.quantile(0.75)) if len(values) else 0.0,
        "p90": float(values.quantile(0.90)) if len(values) else 0.0,
        "share_above_original_threshold": float((values >= DEFAULT_OLD_SCORE_THRESHOLD).mean()) if len(values) else 0.0,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Entry path fractal-level direct direction benchmark.")
    parser.add_argument("--stage", choices=["feature-audit", "target-frequency", "validation-matrix"], required=True)
    parser.add_argument("--train-source", default=str(DEFAULT_TRAIN_SOURCE))
    parser.add_argument("--validation-source", default=str(DEFAULT_VALIDATION_SOURCE))
    parser.add_argument("--test-source", default=str(DEFAULT_TEST_SOURCE))
    parser.add_argument("--validation-predictions", default=str(DEFAULT_VALIDATION_PREDICTIONS))
    parser.add_argument("--test-predictions", default=str(DEFAULT_TEST_PREDICTIONS))
    parser.add_argument("--ohlc", default=str(DEFAULT_OHLC))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--old-score-threshold", type=float, default=DEFAULT_OLD_SCORE_THRESHOLD)
    parser.add_argument("--k", type=int, default=DEFAULT_NEAREST_K, choices=[4, 6, 8, 16], help="Number of nearest fractal neighbors")
    parser.add_argument("--geometry-only", action="store_true", default=False, help="Exclude up_*/dn_* features from nearest_k")
    parser.add_argument("--e0-grid", action="store_true", default=False, help="Use E0 threshold grid [0.10, 0.20, 0.30, 0.40]")
    return parser.parse_args()


def main() -> dict[str, Any]:
    args = parse_args()
    if args.stage == "feature-audit":
        result = run_feature_audit(
            train_source=args.train_source,
            validation_source=args.validation_source,
            test_source=args.test_source,
            output_dir=args.output_dir,
        )
    elif args.stage == "target-frequency":
        result = run_target_frequency(
            train_source=args.train_source,
            validation_source=args.validation_source,
            ohlc=args.ohlc,
            output_dir=args.output_dir,
        )
    elif args.stage == "validation-matrix":
        k = args.k
        geometry_only = args.geometry_only
        suffix = f"_nearest_k{k}" if not geometry_only else f"_nearest_k{k}_geometry_only"
        effective_output_dir = str(args.output_dir).replace("_fractal_level_direct_direction", suffix) if args.output_dir == str(DEFAULT_OUTPUT_DIR) else args.output_dir
        threshold_grid = E0_THRESHOLD_GRID if args.e0_grid else None
        result = run_validation_matrix(
            train_source=args.train_source,
            validation_source=args.validation_source,
            validation_predictions=args.validation_predictions,
            ohlc=args.ohlc,
            output_dir=effective_output_dir,
            old_score_threshold=args.old_score_threshold,
            k=k,
            geometry_only=geometry_only,
            threshold_grid=threshold_grid,
        )
    else:
        raise ValueError(f"unsupported stage: {args.stage}")
    print(json.dumps(_jsonable(result), ensure_ascii=False, indent=2))
    return result


if __name__ == "__main__":
    main()
