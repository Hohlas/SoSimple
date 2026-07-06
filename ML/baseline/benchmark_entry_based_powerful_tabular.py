# =============================================================================
# Файл: benchmark_entry_based_powerful_tabular.py
# Назначение: DIAGNOSTIC_ONLY runner мощных табличных моделей для ветки
#   `entry-based next open` с control `all100`, candidate-only summary,
#   split-overlap gate, audit decisions и отдельными артефактами.
# Язык: Python 3.10+
# Обновлён: 2026-07-06
# Зависимости:
#   Входные данные:
#     - foundation entry-based splits через benchmark_entry_based_next_open_closeout.py
#   Выходные данные:
#     - ML/reports/entry_based_powerful_tabular.json
#     - ML/reports/entry_based_powerful_tabular_metrics.csv
#     - ML/reports/entry_based_powerful_tabular_rows.csv
#     - ML/reports/entry_based_powerful_tabular_scale_audit.csv
# Использование:
#   ./.venv/bin/python ML/baseline/benchmark_entry_based_powerful_tabular.py \
#     --entry-based-powerful-tabular --no-resume
# Примечания:
#   - `low_n_disclosure=2026` не участвует в verdict.
#   - Положительный direction может дать только `DIRECTION_REPLICATION_REQUIRED`.
# =============================================================================

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from collections.abc import Sequence
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import lightgbm as lgb
import numpy as np
import pandas as pd
import xgboost as xgb
from catboost import CatBoostRegressor
from sklearn.ensemble import ExtraTreesRegressor, HistGradientBoostingRegressor
from sklearn.multioutput import MultiOutputRegressor

from ML.baseline import benchmark_entry_based_next_open_closeout as closeout


CLOSEOUT_HORIZONS = closeout.CLOSEOUT_HORIZONS
closeout_target_matrix = closeout.closeout_target_matrix
closeout_predictions_frame = closeout.closeout_predictions_frame
compute_closeout_split_metrics = closeout.compute_closeout_split_metrics
build_closeout_representation_features = closeout.build_closeout_representation_features


POWERFUL_TABULAR_SCHEMA_VERSION = 1
CLOSEOUT_CANDIDATE_ONLY_BASELINE = {
    "representation_key": "nearest_k60",
    "model_key": "xgboost_depth5",
    "horizon": "H12",
    "val_select": 0.0373,
    "val_eval": 0.0274,
    "simple_trade_val_select": 0.03811276203196225,
    "simple_trade_val_eval": -0.014823368357370996,
}


REPORT_JSON_PATH = Path("ML/reports/entry_based_powerful_tabular.json")
REPORT_METRICS_PATH = Path("ML/reports/entry_based_powerful_tabular_metrics.csv")
REPORT_ROWS_PATH = Path("ML/reports/entry_based_powerful_tabular_rows.csv")
REPORT_SCALE_AUDIT_PATH = Path("ML/reports/entry_based_powerful_tabular_scale_audit.csv")

POWERFUL_TABULAR_REPRESENTATIONS = (
    "all100",
    "corridor_5atr",
    "nearest_k60",
    "nearest_k80",
)
CONTROL_REPRESENTATIONS = ("all100",)
CANDIDATE_REPRESENTATIONS = tuple(
    key for key in POWERFUL_TABULAR_REPRESENTATIONS if key not in CONTROL_REPRESENTATIONS
)
POWERFUL_TABULAR_MODEL_KEYS = (
    "xgboost_depth3_baseline",
    "xgboost_depth5_baseline",
    "xgboost_depth7_regularized",
    "xgboost_depth9_regularized",
    "lightgbm_depth7_regularized",
    "lightgbm_leaves63_regularized",
    "catboost_depth6_regularized",
    "catboost_depth8_regularized",
    "extra_trees_regressor",
    "hist_gradient_boosting_strong",
)
POWERFUL_TABULAR_SEEDS = (42,)


def build_powerful_tabular_model(model_key: str, seed: int, thread_count: int) -> tuple[object, dict[str, object]]:
    if model_key.startswith("xgboost_"):
        depth_by_key = {
            "xgboost_depth3_baseline": 3,
            "xgboost_depth5_baseline": 5,
            "xgboost_depth7_regularized": 7,
            "xgboost_depth9_regularized": 9,
        }
        if model_key not in depth_by_key:
            raise ValueError(f"unknown powerful tabular model: {model_key}")
        max_depth = depth_by_key[model_key]
        base_model = xgb.XGBRegressor(
            n_estimators=700,
            max_depth=max_depth,
            learning_rate=0.025,
            subsample=0.80,
            colsample_bytree=0.80,
            reg_alpha=0.10 if max_depth >= 7 else 0.0,
            reg_lambda=3.0 if max_depth >= 7 else 1.0,
            objective="reg:squarederror",
            random_state=seed,
            n_jobs=thread_count,
            tree_method="hist",
        )
        metadata: dict[str, object] = {
            "model_key": model_key,
            "family": "xgboost",
            "seed": seed,
            "thread_count": thread_count,
            "max_depth": max_depth,
            "n_estimators": 700,
            "learning_rate": 0.025,
            "subsample": 0.80,
            "colsample_bytree": 0.80,
            "reg_alpha": 0.10 if max_depth >= 7 else 0.0,
            "reg_lambda": 3.0 if max_depth >= 7 else 1.0,
        }
        return MultiOutputRegressor(base_model, n_jobs=1), metadata

    if model_key == "lightgbm_depth7_regularized":
        base_model = lgb.LGBMRegressor(
            n_estimators=900,
            max_depth=7,
            num_leaves=63,
            learning_rate=0.02,
            subsample=0.80,
            colsample_bytree=0.80,
            reg_alpha=0.10,
            reg_lambda=3.0,
            random_state=seed,
            n_jobs=thread_count,
            verbosity=-1,
        )
        return MultiOutputRegressor(base_model, n_jobs=1), {
            "model_key": model_key,
            "family": "lightgbm",
            "seed": seed,
            "thread_count": thread_count,
            "max_depth": 7,
            "num_leaves": 63,
            "n_estimators": 900,
            "learning_rate": 0.02,
        }

    if model_key == "lightgbm_leaves63_regularized":
        base_model = lgb.LGBMRegressor(
            n_estimators=900,
            max_depth=-1,
            num_leaves=63,
            learning_rate=0.02,
            subsample=0.80,
            colsample_bytree=0.80,
            min_child_samples=80,
            reg_alpha=0.10,
            reg_lambda=5.0,
            random_state=seed,
            n_jobs=thread_count,
            verbosity=-1,
        )
        return MultiOutputRegressor(base_model, n_jobs=1), {
            "model_key": model_key,
            "family": "lightgbm",
            "seed": seed,
            "thread_count": thread_count,
            "max_depth": -1,
            "num_leaves": 63,
            "n_estimators": 900,
            "learning_rate": 0.02,
            "min_child_samples": 80,
        }

    if model_key.startswith("catboost_"):
        depth_by_key = {
            "catboost_depth6_regularized": 6,
            "catboost_depth8_regularized": 8,
        }
        if model_key not in depth_by_key:
            raise ValueError(f"unknown powerful tabular model: {model_key}")
        depth = depth_by_key[model_key]
        base_model = CatBoostRegressor(
            iterations=900,
            depth=depth,
            learning_rate=0.025,
            loss_function="RMSE",
            l2_leaf_reg=6.0 if depth >= 8 else 3.0,
            random_seed=seed,
            thread_count=thread_count,
            verbose=False,
            allow_writing_files=False,
        )
        return MultiOutputRegressor(base_model, n_jobs=1), {
            "model_key": model_key,
            "family": "catboost",
            "seed": seed,
            "thread_count": thread_count,
            "iterations": 900,
            "depth": depth,
            "learning_rate": 0.025,
            "l2_leaf_reg": 6.0 if depth >= 8 else 3.0,
        }

    if model_key == "extra_trees_regressor":
        model = ExtraTreesRegressor(
            n_estimators=600,
            max_features=0.70,
            min_samples_leaf=20,
            random_state=seed,
            n_jobs=thread_count,
        )
        return model, {
            "model_key": model_key,
            "family": "extra_trees",
            "seed": seed,
            "thread_count": thread_count,
            "n_estimators": 600,
            "max_features": 0.70,
            "min_samples_leaf": 20,
        }

    if model_key == "hist_gradient_boosting_strong":
        base_model = HistGradientBoostingRegressor(
            max_iter=700,
            learning_rate=0.025,
            max_leaf_nodes=63,
            l2_regularization=1.0,
            random_state=seed,
        )
        return MultiOutputRegressor(base_model, n_jobs=1), {
            "model_key": model_key,
            "family": "hist_gradient_boosting",
            "seed": seed,
            "thread_count": thread_count,
            "max_iter": 700,
            "learning_rate": 0.025,
            "max_leaf_nodes": 63,
            "l2_regularization": 1.0,
        }

    raise ValueError(f"unknown powerful tabular model: {model_key}")


def job_key(job: dict[str, object]) -> str:
    return f"{job['representation_key']}/{job['model_key']}/{job['seed']}"


def fit_and_predict_powerful_tabular(
    model_key: str,
    seed: int,
    train_features: pd.DataFrame,
    train_targets: np.ndarray,
    eval_features: dict[str, pd.DataFrame],
    thread_count: int,
) -> dict[str, object]:
    model, metadata = build_powerful_tabular_model(model_key, seed=seed, thread_count=thread_count)
    model.fit(train_features.to_numpy(dtype=np.float32), train_targets)
    predictions_by_split: dict[str, pd.DataFrame] = {}
    for split_name, features in eval_features.items():
        preds = np.asarray(model.predict(features.to_numpy(dtype=np.float32)), dtype=np.float32)
        predictions_by_split[split_name] = closeout_predictions_frame(preds)
    return {"predictions_by_split": predictions_by_split, "model_metadata": metadata}


def compute_yearly_split_metrics(frame: pd.DataFrame, predictions: pd.DataFrame) -> dict[str, object]:
    timestamps = pd.to_datetime(frame["time"], errors="coerce")
    metrics: dict[str, object] = {}
    for year in sorted(timestamps.dropna().dt.year.unique()):
        mask = timestamps.dt.year == int(year)
        if not bool(mask.any()):
            continue
        metrics[str(int(year))] = compute_closeout_split_metrics(
            frame.loc[mask].reset_index(drop=True),
            predictions.loc[mask.to_numpy()].reset_index(drop=True),
        )
    return metrics


def enumerate_powerful_tabular_jobs() -> list[dict[str, object]]:
    jobs: list[dict[str, object]] = []
    for representation_key in POWERFUL_TABULAR_REPRESENTATIONS:
        for model_key in POWERFUL_TABULAR_MODEL_KEYS:
            for seed in POWERFUL_TABULAR_SEEDS:
                jobs.append(
                    {
                        "representation_key": representation_key,
                        "model_key": model_key,
                        "seed": seed,
                    }
                )
    return jobs


def _get_cached_representation(splits: dict[str, pd.DataFrame], split_name: str, profile_key: str) -> tuple[pd.DataFrame, dict]:
    cache = splits.setdefault("_powerful_tabular_rep_cache", {})
    key = (split_name, profile_key)
    if key not in cache:
        cache[key] = build_closeout_representation_features(splits[split_name], profile_key)
    return cache[key]


def evaluate_powerful_tabular_job(job: dict[str, object], splits: dict[str, pd.DataFrame], thread_count: int) -> dict[str, object]:
    started = time.time()
    rep_key = job["representation_key"]
    model_key = job["model_key"]
    seed = int(job["seed"])
    train_features, train_meta = _get_cached_representation(splits, "train", rep_key)
    eval_features = {}
    for split_name in ("train", "val_select", "val_eval", "low_n_disclosure"):
        features, _ = _get_cached_representation(splits, split_name, rep_key)
        eval_features[split_name] = features
    fitted = fit_and_predict_powerful_tabular(
        model_key=model_key,
        seed=seed,
        train_features=train_features,
        train_targets=closeout_target_matrix(splits["train"]),
        eval_features=eval_features,
        thread_count=thread_count,
    )
    split_metrics = {
        split_name: compute_closeout_split_metrics(splits[split_name], preds)
        for split_name, preds in fitted["predictions_by_split"].items()
    }
    yearly_metrics = {
        split_name: compute_yearly_split_metrics(splits[split_name], preds)
        for split_name, preds in fitted["predictions_by_split"].items()
        if split_name in {"val_select", "val_eval"}
    }
    metrics_rows = []
    for split_name, metrics in split_metrics.items():
        for metric_name, payload in metrics.items():
            target_name, horizon = metric_name.rsplit("_", 1)
            row = {
                "representation_key": rep_key,
                "model_key": model_key,
                "seed": seed,
                "split_name": split_name,
                "target_name": target_name,
                "horizon": f"H{horizon}",
            }
            if target_name == "simple_trade":
                row.update(payload)
            else:
                row["spearman"] = payload["spearman"]
            metrics_rows.append(row)
    preview = fitted["predictions_by_split"]["val_eval"].head(8).copy()
    preview.insert(0, "split_name", "val_eval")
    preview.insert(0, "seed", seed)
    preview.insert(0, "model_key", model_key)
    preview.insert(0, "representation_key", rep_key)
    preview["time"] = splits["val_eval"]["time"].head(len(preview)).astype(str).to_list()
    return {
        "job_key": job_key(job),
        "representation_key": rep_key,
        "model_key": model_key,
        "seed": seed,
        "elapsed_sec": time.time() - started,
        "feature_count": int(train_features.shape[1]),
        "actual_thread_count": int(thread_count),
        "status": "completed",
        "error_text": None,
        "normalization_contract": build_normalization_contract(model_key, train_features.columns),
        "representation_metadata": train_meta,
        "model_metadata": fitted["model_metadata"],
        "split_metrics": split_metrics,
        "yearly_metrics": yearly_metrics,
        "rows_preview": preview,
        "metrics_rows": metrics_rows,
    }


TARGET_COLUMN_PREFIXES = (
    "entry_up_",
    "entry_dn_",
    "entry_log_ratio_",
    "target_",
    "label_",
    "outcome_",
    "ret_",
    "fav_",
    "adv_",
)

FORBIDDEN_POWERFUL_TABULAR_VERDICTS = {
    "FREEZE_PROPOSAL_ONLY",
    "CANDIDATE",
    "FROZEN",
    "READY_FOR_LOCKED_TEST",
}


def _best_metric_from_runs(
    runs: list[dict[str, object]],
    split_name: str,
    target_names: tuple[str, ...],
    allowed_representations: tuple[str, ...] | None = None,
) -> dict[str, object]:
    best: dict[str, object] = {
        "representation_key": "",
        "model_key": "",
        "seed": 0,
        "target_name": target_names[0],
        "horizon": "H3",
        "score": 0.0,
    }
    allowed = set(allowed_representations) if allowed_representations is not None else None
    for run in runs:
        rep = str(run.get("representation_key", ""))
        if allowed is not None and rep not in allowed:
            continue
        metrics = run.get("split_metrics", {}).get(split_name, {})
        for target_name in target_names:
            for horizon in CLOSEOUT_HORIZONS:
                payload = metrics.get(f"{target_name}_{horizon}", {})
                score = float(payload.get("spearman") or 0.0)
                if score > float(best["score"]):
                    best = {
                        "representation_key": rep,
                        "model_key": run["model_key"],
                        "seed": int(run["seed"]),
                        "target_name": target_name,
                        "horizon": f"H{horizon}",
                        "score": score,
                    }
    return best


def _metric_for(run: dict[str, object], split_name: str, target_name: str, horizon: str) -> float:
    suffix = horizon.removeprefix("H")
    value = run.get("split_metrics", {}).get(split_name, {}).get(f"{target_name}_{suffix}", {}).get("spearman")
    return float(value) if value is not None else 0.0


def _trade_for(run: dict[str, object], split_name: str, horizon: str) -> float | None:
    suffix = horizon.removeprefix("H")
    payload = run.get("split_metrics", {}).get(split_name, {}).get(f"simple_trade_{suffix}", {})
    value = payload.get("mean_signed_log_ratio")
    if value is None:
        value = payload.get("mean")
    return value


def compare_candidate_against_all100_same_model(
    runs: list[dict[str, object]], selected: dict[str, object]
) -> dict[str, object]:
    selected_rep = str(selected.get("representation_key", ""))
    selected_model = str(selected.get("model_key", ""))
    selected_horizon = str(selected.get("horizon", "H12"))
    selected_target = str(selected.get("target_name", "entry_log_ratio"))
    all100_run = None
    for run in runs:
        if str(run.get("representation_key", "")) == "all100" and str(run.get("model_key", "")) == selected_model:
            all100_run = run
            break
    if all100_run is None:
        return {"available": False}
    all100_val_select = _metric_for(all100_run, "val_select", selected_target, selected_horizon)
    all100_val_eval = _metric_for(all100_run, "val_eval", selected_target, selected_horizon)
    candidate_val_select = float(selected.get("score", 0.0))
    candidate_val_eval = float(selected.get("eval_score", 0.0) or 0.0)
    return {
        "available": True,
        "all100_representation": "all100",
        "all100_model_key": selected_model,
        "all100_val_select_score": all100_val_select,
        "all100_val_eval_score": all100_val_eval,
        "candidate_minus_all100_val_select": candidate_val_select - all100_val_select,
        "candidate_minus_all100_val_eval": candidate_val_eval - all100_val_eval,
        "all100_underperformance_explained": False,
    }


def compare_simple_trade_against_closeout_baseline(selected: dict[str, object]) -> dict[str, object]:
    select_mean = selected.get("simple_trade_select_mean")
    eval_mean = selected.get("simple_trade_eval_mean")
    baseline_select = float(CLOSEOUT_CANDIDATE_ONLY_BASELINE["simple_trade_val_select"])
    baseline_eval = float(CLOSEOUT_CANDIDATE_ONLY_BASELINE["simple_trade_val_eval"])
    return {
        "baseline": CLOSEOUT_CANDIDATE_ONLY_BASELINE,
        "baseline_select_mean": baseline_select,
        "baseline_eval_mean": baseline_eval,
        "select_delta": None if select_mean is None else float(select_mean) - baseline_select,
        "eval_delta": None if eval_mean is None else float(eval_mean) - baseline_eval,
        "ranking_only_evidence": False,
    }


def selected_yearly_metrics(
    runs: list[dict[str, object]],
    selected: dict[str, object],
    target_name: str,
) -> dict[str, object]:
    selected_run = next(
        (
            run
            for run in runs
            if str(run.get("representation_key", "")) == str(selected.get("representation_key", ""))
            and str(run.get("model_key", "")) == str(selected.get("model_key", ""))
            and int(run.get("seed", 0)) == int(selected.get("seed", 0))
        ),
        None,
    )
    horizon = str(selected.get("horizon", "H12")).removeprefix("H")
    metric_key = f"{target_name}_{horizon}"
    result: dict[str, object] = {}
    for split_name in ("val_select", "val_eval"):
        by_year = (selected_run or {}).get("yearly_metrics", {}).get(split_name, {})
        scores = [
            float(payload.get(metric_key, {}).get("spearman", 0.0) or 0.0)
            for _, payload in sorted(by_year.items())
            if metric_key in payload
        ]
        positive_scores = [score for score in scores if score > 0.0]
        positive_years = len(positive_scores)
        total_positive = sum(positive_scores)
        best_year_share = max(positive_scores) / total_positive if total_positive > 0 else 1.0
        if len(scores) > 1:
            without_best_year_score = (sum(scores) - max(scores)) / (len(scores) - 1)
        else:
            without_best_year_score = 0.0
        result[split_name] = {
            "year_scores": scores,
            "positive_years": positive_years,
            "best_year_share": float(best_year_share),
            "without_best_year_score": float(without_best_year_score),
            "yearly_check_pass": positive_years >= 2 and without_best_year_score > 0.0 and best_year_share < 0.80,
        }
    return result


def summarize_powerful_tabular_runs(runs: list[dict[str, object]]) -> dict[str, object]:
    best_direction_overall = _best_metric_from_runs(runs, "val_select", ("entry_log_ratio",))
    best_direction_candidate_only = _best_metric_from_runs(
        runs,
        "val_select",
        ("entry_log_ratio",),
        allowed_representations=CANDIDATE_REPRESENTATIONS,
    )
    best_amplitude_overall = _best_metric_from_runs(runs, "val_select", ("entry_up", "entry_dn"))
    direction_run = None
    amplitude_run = None
    for run in runs:
        if str(run.get("representation_key", "")) == str(best_direction_candidate_only.get("representation_key", "")) and str(run.get("model_key", "")) == str(best_direction_candidate_only.get("model_key", "")):
            direction_run = run
            break
    for run in runs:
        if str(run.get("representation_key", "")) == str(best_amplitude_overall.get("representation_key", "")) and str(run.get("model_key", "")) == str(best_amplitude_overall.get("model_key", "")):
            amplitude_run = run
            break

    cand_select_score = float(best_direction_candidate_only.get("score", 0.0))
    cand_horizon = str(best_direction_candidate_only.get("horizon", "H12"))
    cand_target = str(best_direction_candidate_only.get("target_name", "entry_log_ratio"))
    cand_eval_score = _metric_for(direction_run, "val_eval", cand_target, cand_horizon) if direction_run else 0.0

    amp_select_score = float(best_amplitude_overall.get("score", 0.0))
    amp_horizon = str(best_amplitude_overall.get("horizon", "H12"))
    amp_target = str(best_amplitude_overall.get("target_name", "entry_up"))
    amp_eval_score = _metric_for(amplitude_run, "val_eval", amp_target, amp_horizon) if amplitude_run else 0.0

    simple_trade_select = _trade_for(direction_run, "val_select", cand_horizon) if direction_run else 0.0
    simple_trade_eval = _trade_for(direction_run, "val_eval", cand_horizon) if direction_run else 0.0

    best_direction_candidate_only["eval_score"] = cand_eval_score
    best_direction_candidate_only["simple_trade_select_mean"] = simple_trade_select
    best_direction_candidate_only["simple_trade_eval_mean"] = simple_trade_eval

    best_amplitude_overall["eval_score"] = amp_eval_score

    summary: dict[str, object] = {
        "search_width": {
            "representations": len(POWERFUL_TABULAR_REPRESENTATIONS),
            "models": len(POWERFUL_TABULAR_MODEL_KEYS),
            "seeds": len(POWERFUL_TABULAR_SEEDS),
            "horizons": len(CLOSEOUT_HORIZONS),
            "predicted_target_families": 3,
            "derived_trading_diagnostics": 1,
            "jobs": len(runs),
            "metric_comparisons": len(POWERFUL_TABULAR_REPRESENTATIONS)
            * len(POWERFUL_TABULAR_MODEL_KEYS)
            * len(POWERFUL_TABULAR_SEEDS)
            * len(CLOSEOUT_HORIZONS)
            * 3,
        },
        "best_direction_overall": best_direction_overall,
        "best_direction_candidate_only": best_direction_candidate_only,
        "best_amplitude_overall": best_amplitude_overall,
        "best_direction_candidate_only_vs_closeout_baseline": {
            "baseline": CLOSEOUT_CANDIDATE_ONLY_BASELINE,
            "val_select_delta": float(best_direction_candidate_only.get("score", 0.0))
            - CLOSEOUT_CANDIDATE_ONLY_BASELINE["val_select"],
            "val_eval_delta": cand_eval_score - CLOSEOUT_CANDIDATE_ONLY_BASELINE["val_eval"],
        },
        "replication_required": False,
    }

    summary["best_direction_candidate_only"]["same_model_all100_comparison"] = (
        compare_candidate_against_all100_same_model(runs, best_direction_candidate_only)
    )
    summary["best_direction_candidate_only"]["simple_trade_vs_closeout_baseline"] = (
        compare_simple_trade_against_closeout_baseline(best_direction_candidate_only)
    )
    summary["best_direction_candidate_only"]["yearly_metrics"] = selected_yearly_metrics(
        runs,
        best_direction_candidate_only,
        target_name="entry_log_ratio",
    )
    summary["best_direction_candidate_only"]["yearly_check_pass"] = (
        summary["best_direction_candidate_only"]["yearly_metrics"]["val_select"]["yearly_check_pass"]
        and summary["best_direction_candidate_only"]["yearly_metrics"]["val_eval"]["yearly_check_pass"]
    )
    summary["best_amplitude_overall"]["yearly_metrics"] = selected_yearly_metrics(
        runs,
        best_amplitude_overall,
        target_name=str(best_amplitude_overall["target_name"]),
    )
    summary["verdict"] = decide_powerful_tabular_verdict(summary)
    summary["replication_required"] = summary["verdict"] == "DIRECTION_REPLICATION_REQUIRED"
    validate_allowed_powerful_tabular_verdicts(summary)
    return summary


def decide_powerful_tabular_verdict(summary: dict[str, object]) -> str:
    candidate = summary.get("best_direction_candidate_only", {})
    amplitude = summary.get("best_amplitude_overall", {})
    candidate_select = float(candidate.get("score", 0.0) or 0.0)
    candidate_eval = float(candidate.get("eval_score", 0.0) or 0.0)
    candidate_trade_select = float(candidate.get("simple_trade_select_mean", 0.0) or 0.0)
    candidate_trade_eval = float(candidate.get("simple_trade_eval_mean", 0.0) or 0.0)
    amplitude_select = float(amplitude.get("score", 0.0) or 0.0)
    amplitude_eval = float(amplitude.get("eval_score", 0.0) or 0.0)
    candidate_baseline = summary.get("best_direction_candidate_only_vs_closeout_baseline", {})
    beats_closeout = (
        float(candidate_baseline.get("val_select_delta", 0.0) or 0.0) > 0.0
        and float(candidate_baseline.get("val_eval_delta", 0.0) or 0.0) > 0.0
    )
    yearly_check_pass = bool(candidate.get("yearly_check_pass", False))
    all100_comparison = candidate.get("same_model_all100_comparison", {})
    beats_or_explains_all100 = (
        not bool(all100_comparison.get("available", False))
        or (
            float(all100_comparison.get("candidate_minus_all100_val_select", 0.0) or 0.0) > 0.0
            and float(all100_comparison.get("candidate_minus_all100_val_eval", 0.0) or 0.0) >= 0.0
        )
        or bool(all100_comparison.get("all100_underperformance_explained", False))
    )
    simple_trade_comparison = candidate.get("simple_trade_vs_closeout_baseline", {})
    simple_trade_beats_closeout = (
        (
            float(simple_trade_comparison.get("select_delta", 0.0) or 0.0) >= 0.0
            and float(simple_trade_comparison.get("eval_delta", 0.0) or 0.0) >= 0.0
        )
        or bool(simple_trade_comparison.get("ranking_only_evidence", False))
    )

    if (
        candidate.get("representation_key") in CANDIDATE_REPRESENTATIONS
        and candidate_select >= 0.10
        and candidate_eval >= 0.05
        and beats_closeout
        and beats_or_explains_all100
        and yearly_check_pass
        and candidate_trade_select is not None
        and candidate_trade_eval is not None
        and candidate_trade_select > 0.0
        and candidate_trade_eval > 0.0
        and simple_trade_beats_closeout
    ):
        return "DIRECTION_REPLICATION_REQUIRED"
    if amplitude_select >= 0.25 and amplitude_eval >= 0.15:
        return "PIVOT_AMPLITUDE"
    return "REJECT_CAPACITY_EXPLANATION"


def validate_powerful_tabular_feature_names(feature_names: Sequence[str]) -> None:
    forbidden = [col for col in feature_names if col.startswith(TARGET_COLUMN_PREFIXES)]
    if forbidden:
        raise ValueError(f"forbidden target/label columns in feature names: {forbidden[:10]}")


def validate_allowed_powerful_tabular_verdicts(summary: dict[str, object]) -> None:
    verdict = str(summary.get("verdict", ""))
    if verdict in FORBIDDEN_POWERFUL_TABULAR_VERDICTS:
        raise ValueError(f"freeze-like verdict is not allowed in this stage: {verdict}")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Entry-based powerful tabular model runner")
    parser.add_argument("--entry-based-powerful-tabular", action="store_true")
    parser.add_argument("--resume", dest="resume", action="store_true", default=True)
    parser.add_argument("--no-resume", dest="resume", action="store_false")
    parser.add_argument("--thread-count", type=int, default=24)
    return parser


def build_run_config(thread_count: int, dependency_versions: dict[str, str]) -> dict[str, object]:
    return {
        "schema_version": POWERFUL_TABULAR_SCHEMA_VERSION,
        "representations": POWERFUL_TABULAR_REPRESENTATIONS,
        "control_representations": CONTROL_REPRESENTATIONS,
        "candidate_representations": CANDIDATE_REPRESENTATIONS,
        "models": POWERFUL_TABULAR_MODEL_KEYS,
        "seeds": POWERFUL_TABULAR_SEEDS,
        "horizons": tuple(f"H{h}" for h in CLOSEOUT_HORIZONS),
        "predicted_target_families": ("entry_log_ratio", "entry_up", "entry_dn"),
        "derived_trading_diagnostics": ("simple_trade",),
        "output_paths": {
            "json": str(REPORT_JSON_PATH),
            "metrics": str(REPORT_METRICS_PATH),
            "rows": str(REPORT_ROWS_PATH),
            "scale_audit": str(REPORT_SCALE_AUDIT_PATH),
        },
        "thread_count": thread_count,
        "dependency_versions": dict(sorted(dependency_versions.items())),
    }


def compute_run_config_hash(config: dict[str, object]) -> str:
    payload = json.dumps(config, sort_keys=True, default=list).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def validate_resume_compatibility(saved: dict[str, object], current: dict[str, object]) -> None:
    if saved.get("run_config_hash") != current.get("run_config_hash"):
        raise RuntimeError("run_config_hash mismatch; refuse to resume incompatible run")


def build_normalization_contract(model_key: str, feature_names: Sequence[str]) -> dict[str, object]:
    return {
        "model_key": model_key,
        "mode": "raw_numeric",
        "fit_split": "train",
        "validation_splits_do_not_fit": ("val_select", "val_eval", "low_n_disclosure"),
        "scaler_type": None,
        "feature_count": len(tuple(feature_names)),
    }


def _test_frame_for_overlap_check(date_pair: tuple[str, str]) -> pd.DataFrame:
    timestamps = pd.to_datetime([date_pair[0], date_pair[1]], format="mixed")
    return pd.DataFrame({"time": timestamps, "entry_time": timestamps + pd.Timedelta(hours=1)})


def compute_split_horizon_overlap_check(splits: dict[str, pd.DataFrame]) -> dict[str, object]:
    boundary_checks: dict[str, dict[str, object]] = {}
    status = "PASS"
    ordered = ("train", "val_select", "val_eval", "low_n_disclosure")
    boundaries = []
    basis = "entry_time"
    for left_name, right_name in zip(ordered, ordered[1:]):
        if left_name not in splits or right_name not in splits:
            continue
        if "entry_time" in splits[left_name].columns:
            left_end = pd.to_datetime(splits[left_name]["entry_time"]).max()
        else:
            left_end = pd.to_datetime(splits[left_name]["time"]).max()
            basis = "signal_time_fallback"
            status = "DIAGNOSTIC_ONLY"
        right_start = pd.to_datetime(splits[right_name]["time"]).min()
        boundaries.append((left_name, right_name, left_end, right_start))
    for horizon in CLOSEOUT_HORIZONS:
        horizon_key = f"H{horizon}"
        horizon_delta = pd.Timedelta(hours=int(horizon))
        issues = []
        for left_name, right_name, left_end, right_start in boundaries:
            crosses = left_end + horizon_delta >= right_start
            if crosses:
                issues.append(
                    {
                        "left_split": left_name,
                        "right_split": right_name,
                        "left_end": str(left_end),
                        "right_start": str(right_start),
                    }
                )
        if issues:
            status = "DIAGNOSTIC_ONLY"
        boundary_checks[horizon_key] = {"crosses_boundary": bool(issues), "issues": issues}
    return {
        "status": status,
        "basis": basis,
        "horizons": tuple(f"H{h}" for h in CLOSEOUT_HORIZONS),
        "boundary_checks": boundary_checks,
    }


def apply_horizon_embargo(splits: dict[str, pd.DataFrame], max_horizon_hours: int) -> dict[str, pd.DataFrame]:
    cleaned = {name: frame.copy().reset_index(drop=True) for name, frame in splits.items()}
    ordered = ("train", "val_select", "val_eval", "low_n_disclosure")
    horizon_delta = pd.Timedelta(hours=max_horizon_hours)
    for left_name, right_name in zip(ordered, ordered[1:]):
        if left_name not in cleaned or right_name not in cleaned:
            continue
        right_start = pd.to_datetime(cleaned[right_name]["time"], errors="coerce").min()
        if pd.isna(right_start):
            continue
        time_col = "entry_time" if "entry_time" in cleaned[left_name].columns else "time"
        left_times = pd.to_datetime(cleaned[left_name][time_col], errors="coerce")
        keep = left_times + horizon_delta < right_start
        cleaned[left_name] = cleaned[left_name].loc[keep.fillna(False)].reset_index(drop=True)
    cleaned.pop("_powerful_tabular_rep_cache", None)
    return cleaned


def _audit_warning_families(scale_audit: dict[str, object]) -> set[str]:
    families: set[str] = set()
    for warning in scale_audit.get("warnings", []) or []:
        family = str(warning.get("family", ""))
        if family:
            families.add(family)
    for profile in (scale_audit.get("profiles", {}) or {}).values():
        for flag in profile.get("flags", []) or []:
            family = str(flag.get("flag", ""))
            if family:
                families.add(family)
    return families


def build_audit_decisions(scale_audit: dict[str, object]) -> dict[str, dict[str, object]]:
    decisions: dict[str, dict[str, object]] = {}
    for family in sorted(_audit_warning_families(scale_audit)):
        decisions[family] = {
            "decision": "accept_as_warning",
            "reason": "diagnostic stage; warning disclosed and not used to select locked_test candidate",
        }
    return decisions


def validate_audit_decisions(scale_audit: dict[str, object], audit_decisions: dict[str, object]) -> None:
    status = str(scale_audit.get("status", "PASS"))
    if status == "ERROR":
        raise RuntimeError("scale/distribution audit ERROR blocks fitting")
    if status == "WARNING":
        for family in sorted(_audit_warning_families(scale_audit)):
            if family not in audit_decisions:
                raise RuntimeError(f"missing audit decision for warning family: {family}")
            payload = audit_decisions[family]
            decision = str(payload.get("decision", payload) if isinstance(payload, dict) else payload)
            if decision not in {"accept_as_warning", "fix_and_rerun", "block"}:
                raise RuntimeError(f"invalid audit decision for warning family {family}: {decision}")
            if decision == "block":
                raise RuntimeError(f"audit decision blocks fitting for warning family: {family}")


def _utc_now_iso() -> str:
    import datetime as dt
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def _json_default(value: object) -> object:
    if isinstance(value, pd.DataFrame):
        return value.to_dict(orient="records")
    if isinstance(value, pd.Series):
        return value.to_dict()
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def save_report_json(report: dict[str, object], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    enrich_powerful_tabular_report_metadata(report)
    serializable = json.loads(json.dumps(report, ensure_ascii=True, indent=2, default=_json_default))
    path.write_text(json.dumps(serializable, ensure_ascii=True, indent=2), encoding="utf-8")


def enrich_powerful_tabular_report_metadata(report: dict[str, object]) -> dict[str, object]:
    """Adds top-level machine-readable metadata without changing experiment scope."""
    run_config = report.get("run_config", {})
    summary = report.get("summary", {})
    if isinstance(run_config, dict):
        report["schema_version"] = run_config.get("schema_version", POWERFUL_TABULAR_SCHEMA_VERSION)
        report["dependency_versions"] = run_config.get("dependency_versions", {})
    else:
        report["schema_version"] = POWERFUL_TABULAR_SCHEMA_VERSION
        report["dependency_versions"] = {}
    if isinstance(summary, dict) and summary.get("verdict") is not None:
        report["verdict"] = summary["verdict"]
    report["normalization_contract"] = {
        "scope": "per_run_feature_matrix",
        "mode": "raw_numeric",
        "fit_split": "train",
        "validation_splits_do_not_fit": ("val_select", "val_eval", "low_n_disclosure"),
        "per_run_path": "runs[].normalization_contract",
    }
    return report


def _add_h24_targets_if_missing(splits: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    missing_h24 = any(f"entry_up_24" not in frame.columns for frame in splits.values())
    if not missing_h24:
        return splits
    rebuilt = closeout.base.load_entry_based_splits(target_mode="rebuilt")
    try:
        import ML.baseline.benchmark_next_open_entry_updn_foundation as foundation
        ohlc = foundation.load_ohlc()
        return {name: foundation.rebuild_entry_targets(frame.copy(), ohlc, horizons=(3, 6, 12, 24)) for name, frame in rebuilt.items()}
    except Exception:
        return rebuilt


def _convert_splits(old_splits: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    validation = pd.concat([old_splits["val_stop"], old_splits["diagnostic_holdout"]], ignore_index=True)
    validation_time = pd.to_datetime(validation["time"], errors="coerce")
    validation = validation.loc[validation_time < pd.Timestamp("2026-01-01")].reset_index(drop=True)
    disclosure = old_splits["low_n_disclosure"].copy()
    disclosure_time = pd.to_datetime(disclosure["time"], errors="coerce")
    disclosure = disclosure.loc[disclosure_time >= pd.Timestamp("2026-01-01")].reset_index(drop=True)
    return {
        "train": old_splits["train_core"].reset_index(drop=True),
        "validation": validation,
        "low_n_disclosure": disclosure,
    }


def _split_validation_roles(validation: pd.DataFrame) -> dict[str, pd.DataFrame]:
    frame = validation.reset_index(drop=True)
    if len(frame) < 300:
        return {"val_select": frame, "val_eval": frame}
    midpoint = len(frame) // 2
    return {"val_select": frame.iloc[:midpoint].reset_index(drop=True), "val_eval": frame.iloc[midpoint:].reset_index(drop=True)}


def _heartbeat(label: str, done_runs: int, total_runs: int, elapsed_sec: float) -> None:
    print(f"[heartbeat] {label}: done={done_runs}/{total_runs}, elapsed={elapsed_sec:.1f}s", flush=True)


def _get_dependency_versions() -> dict[str, str]:
    versions: dict[str, str] = {}
    for mod_name in ["xgboost", "lightgbm", "catboost", "sklearn"]:
        try:
            mod = __import__(mod_name)
            versions[mod_name] = getattr(mod, "__version__", "unknown")
        except ImportError:
            versions[mod_name] = "not_installed"
    return versions


def run_powerful_tabular(args: argparse.Namespace) -> dict[str, object]:
    started = time.time()
    jobs = enumerate_powerful_tabular_jobs()
    dep_versions = _get_dependency_versions()
    thread_count = args.thread_count

    _heartbeat("run_start", 0, len(jobs), 0.0)

    old_splits = _add_h24_targets_if_missing(closeout.base.load_entry_based_splits(target_mode="rebuilt"))
    splits = _convert_splits(old_splits)
    role_splits = _split_validation_roles(splits["validation"])
    splits.update(role_splits)
    splits = apply_horizon_embargo(splits, max_horizon_hours=max(int(h) for h in CLOSEOUT_HORIZONS))

    report: dict[str, object] = {}
    if args.resume and REPORT_JSON_PATH.exists():
        existing = json.loads(REPORT_JSON_PATH.read_text(encoding="utf-8"))
        run_config = build_run_config(thread_count, dep_versions)
        run_config_hash = compute_run_config_hash(run_config)
        existing_run_config = existing.get("run_config", {})
        existing_hash = existing.get("run_config_hash", "")
        saved_run_config = existing_run_config if existing_run_config else {"run_config_hash": existing_hash}
        current_run_config = dict(run_config)
        current_run_config["run_config_hash"] = run_config_hash
        validate_resume_compatibility({"run_config_hash": existing.get("run_config_hash", "")}, {"run_config_hash": run_config_hash})
        report = existing
        _heartbeat("resume", len(report.get("runs", [])), len(jobs), time.time() - started)

    report.setdefault("runs", [])
    report.setdefault("started_at", _utc_now_iso())
    report["target_mode"] = "rebuilt"
    report["stage_status"] = "DIAGNOSTIC_ONLY"
    report["split_policy"] = closeout.SPLIT_POLICY

    validation_roles_combined = splits["val_select"] is splits["val_eval"] or len(splits["val_select"]) == len(splits["validation"])
    report["validation_roles_combined"] = bool(validation_roles_combined)

    smoke_check = closeout.run_entry_based_smoke_check({k: splits[k] for k in ("train", "validation", "low_n_disclosure")})
    report["entry_based_smoke_check"] = smoke_check
    if smoke_check["status"] != "PASS":
        report["summary"] = {"verdict": "STOP", "status": "ENTRY_BASED_SMOKE_CHECK_FAILED"}
        save_report_json(report, REPORT_JSON_PATH)
        return report

    overlap_check = compute_split_horizon_overlap_check(splits)
    report["split_horizon_overlap_check"] = overlap_check
    if overlap_check["status"] != "PASS":
        report["summary"] = {
            "verdict": "REJECT_CAPACITY_EXPLANATION",
            "status": "SPLIT_HORIZON_OVERLAP_FAILED",
            "reason": "target horizon crosses split boundary after embargo",
        }
        save_report_json(report, REPORT_JSON_PATH)
        return report

    scale_profiles: dict[str, object] = {}
    for rep_key in POWERFUL_TABULAR_REPRESENTATIONS:
        _heartbeat(f"scale_audit:{rep_key}", len(report.get("runs", [])), len(jobs), time.time() - started)
        features_by_split: dict[str, pd.DataFrame] = {}
        metadata: dict[str, object] = {}
        for split_name in ("train", "validation", "low_n_disclosure"):
            features, metadata = _get_cached_representation(splits, split_name, rep_key)
            features_by_split[split_name] = features
        scale_profiles[rep_key] = closeout.compute_feature_scale_audit(features_by_split, metadata)
    scale_status = "WARNING" if any(audit["status"] == "WARNING" for audit in scale_profiles.values()) else "PASS"
    report["scale_audit"] = {"status": scale_status, "profiles": scale_profiles}
    report["audit_decisions"] = build_audit_decisions(report["scale_audit"])
    validate_audit_decisions(report["scale_audit"], report["audit_decisions"])
    closeout.write_scale_audit_csv(report["scale_audit"], REPORT_SCALE_AUDIT_PATH)
    save_report_json(report, REPORT_JSON_PATH)

    run_config = build_run_config(thread_count, dep_versions)
    run_config_hash = compute_run_config_hash(run_config)
    report["run_config"] = run_config
    report["run_config_hash"] = run_config_hash

    completed = {run["job_key"] for run in report.get("runs", [])}
    failed_runs: list[dict[str, object]] = report.get("failed_runs", [])

    for idx, job in enumerate(jobs, start=1):
        if job_key(job) in completed:
            continue
        _heartbeat(f"run:{job_key(job)}", len(report["runs"]), len(jobs), time.time() - started)
        try:
            run = evaluate_powerful_tabular_job(job, splits, thread_count)
            report["runs"].append(run)  # type: ignore[attr-defined]
        except Exception as exc:
            import traceback
            elapsed = time.time() - started
            failed_runs.append({
                "job_key": job_key(job),
                "representation_key": job["representation_key"],
                "model_key": job["model_key"],
                "seed": job["seed"],
                "elapsed_sec": round(elapsed, 1),
                "exception_type": type(exc).__name__,
                "error_text": str(exc),
                "traceback": traceback.format_exc(),
            })
        report["progress"] = {
            "done_runs": len(report["runs"]),
            "total_runs": len(jobs),
            "started_at": report["started_at"],
            "finished_at": None,
            "elapsed_sec": time.time() - started,
            "thread_count": thread_count,
            "current_job_index": idx,
        }
        report["failed_runs"] = failed_runs
        save_report_json(report, REPORT_JSON_PATH)

    report["summary"] = summarize_powerful_tabular_runs(report["runs"])
    report["progress"] = {
        "done_runs": len(report["runs"]),
        "total_runs": len(jobs),
        "started_at": report["started_at"],
        "finished_at": _utc_now_iso(),
        "elapsed_sec": time.time() - started,
        "thread_count": thread_count,
    }
    report["failed_runs"] = failed_runs

    metrics_rows = [row for run in report["runs"] for row in run.get("metrics_rows", [])]
    closeout.base.write_metrics_csv(metrics_rows, REPORT_METRICS_PATH)
    closeout.base.write_rows_csv(
        pd.concat([pd.DataFrame(run["rows_preview"]) for run in report["runs"] if run.get("rows_preview") is not None], ignore_index=True),
        REPORT_ROWS_PATH,
    )
    save_report_json(report, REPORT_JSON_PATH)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    if not args.entry_based_powerful_tabular:
        print("Pass --entry-based-powerful-tabular")
        return 1
    run_powerful_tabular(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
