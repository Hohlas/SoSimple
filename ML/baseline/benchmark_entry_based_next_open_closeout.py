# =============================================================================
# Файл: benchmark_entry_based_next_open_closeout.py
# Назначение: closeout runner для `entry-based next open` на shortlist профилей
#   с H3/H6/H12/H24, scale audit и простым торговым diagnostic.
# Язык: Python 3.10+
# Обновлён: 2026-07-05
# =============================================================================

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from ML.baseline import benchmark_entry_based_updn_fractal_selection_ablation as base


REPORT_JSON_PATH = Path("ML/reports/entry_based_next_open_closeout.json")
REPORT_METRICS_PATH = Path("ML/reports/entry_based_next_open_closeout_metrics.csv")
REPORT_ROWS_PATH = Path("ML/reports/entry_based_next_open_closeout_rows.csv")
REPORT_SCALE_AUDIT_PATH = Path("ML/reports/entry_based_next_open_closeout_scale_audit.csv")

SHORTLIST_REPRESENTATIONS = (
    "all100",
    "corridor_5atr",
    "nearest_k20",
    "nearest_k60",
    "nearest_k80",
)
CLOSEOUT_HORIZONS = ("3", "6", "12", "24")
CROSS_PAIR_VALIDATION = "excluded_by_plan"
SPLIT_POLICY = {
    "train": {"source": ["train_core"], "calendar": "<=2020"},
    "validation": {"source": ["val_stop", "diagnostic_holdout"], "calendar": "2021-2025"},
    "locked_test": {"source": [], "calendar": "not_opened"},
    "low_n_disclosure": {"source": ["low_n_disclosure"], "calendar": "2026", "selection_use": "forbidden"},
}
CLOSEOUT_MODEL_KEYS = (
    "xgboost_depth3",
    "xgboost_depth5",
    "hist_gradient_boosting",
    "ridge",
)
CLOSEOUT_SEEDS = (42,)
CANDIDATE_REPRESENTATIONS = tuple(key for key in SHORTLIST_REPRESENTATIONS if key != "all100")
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
DIRECTIONAL_SCORE_GATE = 0.10
VALIDATION_EVAL_NONZERO_GATE = 0.02
AMPLITUDE_SCORE_GATE = 0.15
TRADE_MEAN_GATE = 0.0


def build_closeout_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Entry-based next-open closeout runner")
    parser.add_argument("--entry-based-next-open-closeout", action="store_true")
    parser.add_argument("--resume", dest="resume", action="store_true", default=True)
    parser.add_argument("--no-resume", dest="resume", action="store_false")
    return parser


def enumerate_closeout_jobs(
    representation_keys: tuple[str, ...] = SHORTLIST_REPRESENTATIONS,
    model_keys: tuple[str, ...] = CLOSEOUT_MODEL_KEYS,
    seeds: tuple[int, ...] = CLOSEOUT_SEEDS,
) -> list[dict]:
    return [
        {"representation_key": representation_key, "model_key": model_key, "seed": seed}
        for representation_key in representation_keys
        for model_key in model_keys
        for seed in seeds
    ]


def job_key(job: dict) -> str:
    return f"{job['representation_key']}/{job['model_key']}/{job['seed']}"


def _utc_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def _required_entry_target_columns() -> list[str]:
    columns: list[str] = []
    for horizon in CLOSEOUT_HORIZONS:
        columns.extend([f"entry_up_{horizon}", f"entry_dn_{horizon}", f"entry_log_ratio_{horizon}"])
    return columns


def run_entry_based_smoke_check(splits: dict[str, pd.DataFrame]) -> dict:
    required = _required_entry_target_columns()
    missing_columns: dict[str, list[str]] = {}
    nonfinite_columns: dict[str, list[str]] = {}
    constant_target_columns: dict[str, list[str]] = {}
    entry_time_order_violations: dict[str, int] = {}
    row_counts: dict[str, int] = {}
    time_ranges: dict[str, dict[str, str | None]] = {}
    for split_name, frame in splits.items():
        row_counts[split_name] = int(len(frame))
        missing = [column for column in required if column not in frame.columns]
        if missing:
            missing_columns[split_name] = missing
            continue
        bad_nonfinite: list[str] = []
        bad_constant: list[str] = []
        for column in required:
            values = pd.to_numeric(frame[column], errors="coerce").replace([np.inf, -np.inf], np.nan)
            if values.isna().any():
                bad_nonfinite.append(column)
            if values.dropna().nunique() <= 1:
                bad_constant.append(column)
        if bad_nonfinite:
            nonfinite_columns[split_name] = bad_nonfinite
        if bad_constant:
            constant_target_columns[split_name] = bad_constant
        signal_time = pd.to_datetime(frame.get("time"), format="%Y.%m.%d %H:%M", errors="coerce")
        entry_time = pd.to_datetime(frame.get("entry_time"), format="%Y.%m.%d %H:%M", errors="coerce")
        order_bad = int(((entry_time <= signal_time) | signal_time.isna() | entry_time.isna()).sum())
        if order_bad:
            entry_time_order_violations[split_name] = order_bad
        if len(signal_time.dropna()):
            time_ranges[split_name] = {
                "min_time": signal_time.min().isoformat(),
                "max_time": signal_time.max().isoformat(),
            }
        else:
            time_ranges[split_name] = {"min_time": None, "max_time": None}
    split_order_violations: list[dict[str, str]] = []
    ordered_split_names = [name for name in ("train", "validation", "low_n_disclosure") if name in time_ranges]
    for left, right in zip(ordered_split_names, ordered_split_names[1:]):
        left_max = time_ranges[left]["max_time"]
        right_min = time_ranges[right]["min_time"]
        if left_max is not None and right_min is not None and left_max >= right_min:
            split_order_violations.append({"left_split": left, "right_split": right, "left_max_time": left_max, "right_min_time": right_min})
    return {
        "status": "FAIL" if missing_columns or nonfinite_columns or constant_target_columns or entry_time_order_violations or split_order_violations else "PASS",
        "legacy_target_columns_required": False,
        "horizons": list(CLOSEOUT_HORIZONS),
        "required_columns": required,
        "missing_columns": missing_columns,
        "nonfinite_columns": nonfinite_columns,
        "constant_target_columns": constant_target_columns,
        "entry_time_order_violations": entry_time_order_violations,
        "time_ranges": time_ranges,
        "split_order_violations": split_order_violations,
        "row_counts": row_counts,
    }


def closeout_target_matrix(df: pd.DataFrame) -> np.ndarray:
    return df[_required_entry_target_columns()].apply(pd.to_numeric, errors="coerce").fillna(0.0).to_numpy(dtype=np.float32)


def closeout_predictions_frame(preds: np.ndarray) -> pd.DataFrame:
    columns: list[str] = []
    for horizon in CLOSEOUT_HORIZONS:
        columns.extend([f"pred_entry_up_{horizon}", f"pred_entry_dn_{horizon}", f"pred_entry_log_ratio_{horizon}"])
    return pd.DataFrame(preds, columns=columns)


def _row_context_time_features(df: pd.DataFrame) -> pd.DataFrame:
    timestamps = pd.to_datetime(df["time"], errors="coerce")
    hour = timestamps.dt.hour.fillna(0).astype(float)
    dow = timestamps.dt.dayofweek.fillna(0).astype(float)
    return pd.DataFrame(
        {
            "row_hour_sin": np.sin(2.0 * np.pi * hour / 24.0),
            "row_hour_cos": np.cos(2.0 * np.pi * hour / 24.0),
            "row_dow_sin": np.sin(2.0 * np.pi * dow / 7.0),
            "row_dow_cos": np.cos(2.0 * np.pi * dow / 7.0),
        },
        index=df.index,
    )


def build_closeout_representation_features(df: pd.DataFrame, profile_key: str) -> tuple[pd.DataFrame, dict]:
    features, metadata = base.build_representation_features(
        df,
        profile_key,
        serialized_updn_horizons=base.FULL_SERIALIZED_UPDN_FEATURE_HORIZONS,
    )
    features = pd.concat(
        [
            features.reset_index(drop=True),
            _row_context_time_features(df).reset_index(drop=True),
        ],
        axis=1,
    )
    forbidden_top_level = [column for column in features.columns if column.startswith(TARGET_COLUMN_PREFIXES)]
    if forbidden_top_level:
        raise ValueError(f"Top-level target columns leaked into features: {forbidden_top_level[:10]}")
    metadata = dict(metadata)
    metadata["target_horizons"] = list(CLOSEOUT_HORIZONS)
    metadata["feature_horizons"] = list(base.FULL_SERIALIZED_UPDN_FEATURE_HORIZONS)
    metadata["feature_families"] = sorted(set(metadata.get("feature_families", [])) | {"row_context_time", "updn_full"})
    metadata["feature_names"] = list(features.columns)
    metadata["feature_count"] = int(features.shape[1])
    return features, metadata


def build_normalization_contract() -> dict:
    return {
        "normalization_mode": "none_tree_raw",
        "reason": "Tree and linear diagnostic models receive the final numeric feature matrix directly; scale audit is still mandatory.",
        "scaler_fit_split": "train",
        "target_columns_forbidden_in_input_pools": True,
        "feature_groups": {
            "structure_fields": {"normalization": "as_produced", "source": "serialized_fractal_snapshot"},
            "shift_age": {"normalization": "as_produced_or_log", "source": "serialized_fractal_snapshot"},
            "atr_ratio": {"normalization": "log_ratio", "source": "row_ATR_and_fractal_atr"},
            "price_coord_atr": {"normalization": "atr_scaled", "source": "row_ATR_and_fractal_price"},
            "distance_atr": {"normalization": "atr_scaled", "source": "row_ATR_and_fractal_price"},
            "updn_full": {"normalization": "as_produced", "source": "serialized_fractal_snapshot"},
            "row_context_time": {"normalization": "sin_cos", "source": "row_time"},
        },
        "target_groups": {
            "entry_based_updn": {
                "columns": [f"entry_{kind}_{horizon}" for horizon in CLOSEOUT_HORIZONS for kind in ("up", "dn")]
                + [f"entry_log_ratio_{horizon}" for horizon in CLOSEOUT_HORIZONS],
                "normalization": "target_only_not_input",
            }
        },
    }


def assert_no_target_columns_in_normalization(features: pd.DataFrame, contract: dict) -> None:
    offenders = [column for column in features.columns if column.startswith(TARGET_COLUMN_PREFIXES)]
    if offenders:
        raise ValueError(f"Target/label columns are forbidden in input normalization pools: {offenders[:20]}")
    if not contract["target_columns_forbidden_in_input_pools"]:
        raise ValueError("normalization contract must forbid target columns in input pools")


def _feature_group_for_column(column: str) -> str:
    if "_up_" in column or "_dn_" in column:
        return "updn_full"
    if "price_coord_atr" in column or "distance_atr" in column:
        return "price_coord_atr"
    if column.startswith("row_"):
        return "row_context_time"
    if "shift" in column:
        return "shift_age"
    if "atr" in column.lower():
        return "atr_ratio"
    return "structure_fields"


def _feature_scale_stats_frame(features: pd.DataFrame) -> dict[str, dict]:
    numeric = features.apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan)
    quantiles = numeric.quantile([0.01, 0.50, 0.99], axis=0, numeric_only=True)
    stats_by_column: dict[str, dict] = {}
    for column in numeric.columns:
        series = numeric[column]
        clean = series.dropna()
        if clean.empty:
            stats_by_column[column] = {
                "n": int(len(series)),
                "nan_rate": float(series.isna().mean()),
                "zero_rate": None,
                "unique_count": 0,
                "min": None,
                "p1": None,
                "p50": None,
                "p99": None,
                "max": None,
                "std": None,
            }
            continue
        stats_by_column[column] = {
            "n": int(len(series)),
            "nan_rate": float(series.isna().mean()),
            "zero_rate": float((clean == 0.0).mean()),
            "unique_count": int(clean.nunique(dropna=True)),
            "min": float(clean.min()),
            "p1": float(quantiles.at[0.01, column]),
            "p50": float(quantiles.at[0.50, column]),
            "p99": float(quantiles.at[0.99, column]),
            "max": float(clean.max()),
            "std": float(clean.std(ddof=0)),
        }
    return stats_by_column


def compute_feature_scale_audit(features_by_split: dict[str, pd.DataFrame], feature_metadata: dict) -> dict:
    contract = build_normalization_contract()
    for features in features_by_split.values():
        assert_no_target_columns_in_normalization(features, contract)

    feature_stats: dict[str, dict] = {}
    flags: list[dict] = []
    split_stats = {split_name: _feature_scale_stats_frame(features) for split_name, features in features_by_split.items()}
    for column in features_by_split["train"].columns:
        feature_stats[column] = {}
        for split_name in features_by_split:
            stats = split_stats[split_name][column]
            feature_stats[column][split_name] = stats
            if stats["unique_count"] <= 1:
                flags.append({"feature": column, "split": split_name, "flag": "NEAR_CONSTANT"})
            if stats["nan_rate"] is not None and stats["nan_rate"] > 0.05:
                flags.append({"feature": column, "split": split_name, "flag": "NAN_GT5"})

    dominance_checks: dict[str, dict] = {}
    grouped: dict[str, list[float]] = {}
    for column, stats_by_split in feature_stats.items():
        p99 = stats_by_split["train"]["p99"]
        if p99 is not None:
            grouped.setdefault(_feature_group_for_column(column), []).append(abs(float(p99)))
    for group, p99_values in grouped.items():
        max_p99 = max(p99_values) if p99_values else 0.0
        median_p99 = float(np.median(p99_values)) if p99_values else 0.0
        ratio = None if median_p99 == 0.0 else max_p99 / median_p99
        dominance_checks[group] = {
            "max_abs_p99": max_p99,
            "median_abs_p99": median_p99,
            "max_to_median_p99": ratio,
            "status": "WARNING" if ratio is not None and ratio > 100.0 else "PASS",
        }
    status = "WARNING" if flags or any(item["status"] == "WARNING" for item in dominance_checks.values()) else "PASS"
    return {
        "status": status,
        "normalization_contract": contract,
        "profile_key": feature_metadata.get("profile_key"),
        "features": feature_stats,
        "flags": flags,
        "dominance_checks": dominance_checks,
    }


def write_scale_audit_csv(scale_audit: dict, path: Path) -> None:
    rows = []
    audits = scale_audit.get("profiles", scale_audit)
    if isinstance(audits, dict) and "features" in audits:
        audits = {audits.get("profile_key", "unknown"): audits}
    for profile_key, audit in audits.items():
        for feature_name, stats_by_split in audit["features"].items():
            group = _feature_group_for_column(feature_name)
            for split_name, stats in stats_by_split.items():
                rows.append({"profile_key": profile_key, "feature": feature_name, "group": group, "split": split_name, **stats})
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, sep=";", index=False)


def _safe_mean(values: np.ndarray) -> float | None:
    clean = values[np.isfinite(values)]
    if len(clean) == 0:
        return None
    return float(np.mean(clean))


def compute_simple_trade_metrics(frame: pd.DataFrame, predictions: pd.DataFrame, horizon: str) -> dict:
    pred = predictions[f"pred_entry_log_ratio_{horizon}"].to_numpy(dtype=float)
    actual = frame[f"entry_log_ratio_{horizon}"].to_numpy(dtype=float)
    side = np.where(pred >= 0.0, 1.0, -1.0)
    signed = side * actual
    wins = signed > 0.0
    return {
        "trade_count": int(len(signed)),
        "long_count": int(np.sum(side > 0.0)),
        "short_count": int(np.sum(side < 0.0)),
        "mean_signed_log_ratio": _safe_mean(signed),
        "median_signed_log_ratio": float(np.median(signed)) if len(signed) else None,
        "win_rate": float(np.mean(wins)) if len(wins) else None,
        "gross_positive_sum": float(np.sum(signed[signed > 0.0])) if len(signed) else 0.0,
        "gross_negative_sum": float(np.sum(signed[signed < 0.0])) if len(signed) else 0.0,
    }


def compute_closeout_split_metrics(frame: pd.DataFrame, predictions: pd.DataFrame) -> dict:
    metrics: dict[str, dict] = {}
    for horizon in CLOSEOUT_HORIZONS:
        for target_name in ("entry_log_ratio", "entry_up", "entry_dn"):
            actual = frame[f"{target_name}_{horizon}"].to_numpy(dtype=float)
            pred = predictions[f"pred_{target_name}_{horizon}"].to_numpy(dtype=float)
            metrics[f"{target_name}_{horizon}"] = {"spearman": base._corr_or_none(actual, pred)}
        metrics[f"simple_trade_{horizon}"] = compute_simple_trade_metrics(frame, predictions, horizon)
    return metrics


def decide_closeout_verdict(summary: dict) -> str:
    direction = summary["best_directional"]
    amplitude = summary["best_amplitude"]
    trade = summary["best_trade"]
    direction_survives = (
        direction.get("representation_key") in CANDIDATE_REPRESENTATIONS
        and
        direction["selection_score"] >= DIRECTIONAL_SCORE_GATE
        and direction["eval_score"] >= VALIDATION_EVAL_NONZERO_GATE
    )
    trade_survives = (
        trade["select_mean"] is not None
        and trade["eval_mean"] is not None
        and trade["select_mean"] > TRADE_MEAN_GATE
        and trade["eval_mean"] > TRADE_MEAN_GATE
    )
    amplitude_survives = (
        amplitude["selection_score"] >= AMPLITUDE_SCORE_GATE
        and amplitude["eval_score"] >= VALIDATION_EVAL_NONZERO_GATE
    )
    if direction_survives and trade_survives and not summary["validation_roles_combined"]:
        return "CONTINUE"
    if amplitude_survives:
        return "PIVOT"
    return "STOP"


def _convert_splits(old_splits: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    validation = pd.concat([old_splits["val_stop"], old_splits["diagnostic_holdout"]], ignore_index=True)
    return {
        "train": old_splits["train_core"].reset_index(drop=True),
        "validation": validation,
        "low_n_disclosure": old_splits["low_n_disclosure"].reset_index(drop=True),
    }


def _add_h24_targets_if_missing(splits: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    missing_h24 = any(f"entry_up_24" not in frame.columns for frame in splits.values())
    if not missing_h24:
        return splits
    rebuilt = base.load_entry_based_splits(target_mode="rebuilt")
    try:
        import ML.baseline.benchmark_next_open_entry_updn_foundation as foundation

        ohlc = foundation.load_ohlc()
        return {name: foundation.rebuild_entry_targets(frame.copy(), ohlc, horizons=(3, 6, 12, 24)) for name, frame in rebuilt.items()}
    except Exception:
        return rebuilt


def _split_validation_roles(validation: pd.DataFrame) -> dict[str, pd.DataFrame]:
    frame = validation.reset_index(drop=True)
    if len(frame) < 300:
        return {"val_select": frame, "val_eval": frame}
    midpoint = len(frame) // 2
    return {"val_select": frame.iloc[:midpoint].reset_index(drop=True), "val_eval": frame.iloc[midpoint:].reset_index(drop=True)}


def _get_cached_closeout_representation(splits: dict[str, pd.DataFrame], split_name: str, profile_key: str) -> tuple[pd.DataFrame, dict]:
    cache = splits.setdefault("_closeout_representation_cache", {})
    key = (split_name, profile_key)
    if key not in cache:
        cache[key] = build_closeout_representation_features(splits[split_name], profile_key)
    return cache[key]


def _fit_and_predict_closeout(model_key: str, seed: int, train_features: pd.DataFrame, train_targets: np.ndarray, eval_features: dict[str, pd.DataFrame]) -> dict:
    model, metadata = base.build_model(model_key, seed, base.thread_config_for(model_key)["thread_count"])
    model.fit(train_features.to_numpy(dtype=np.float32), train_targets)
    predictions_by_split = {}
    for split_name, features in eval_features.items():
        preds = np.asarray(model.predict(features.to_numpy(dtype=np.float32)), dtype=np.float32)
        predictions_by_split[split_name] = closeout_predictions_frame(preds)
    return {"predictions_by_split": predictions_by_split, "model_metadata": metadata}


def evaluate_closeout_job(job: dict, splits: dict[str, pd.DataFrame], report: dict) -> dict:
    started = time.time()
    rep_key = job["representation_key"]
    model_key = job["model_key"]
    seed = int(job["seed"])
    train_features, train_meta = _get_cached_closeout_representation(splits, "train", rep_key)
    eval_features = {}
    for split_name in ("train", "val_select", "val_eval", "validation", "low_n_disclosure"):
        features, _ = _get_cached_closeout_representation(splits, split_name, rep_key)
        eval_features[split_name] = features
    fitted = _fit_and_predict_closeout(model_key, seed, train_features, closeout_target_matrix(splits["train"]), eval_features)
    split_metrics = {
        split_name: compute_closeout_split_metrics(splits[split_name], preds)
        for split_name, preds in fitted["predictions_by_split"].items()
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
    for column in _required_entry_target_columns():
        preview[column] = pd.to_numeric(splits["val_eval"][column].head(len(preview)), errors="coerce").fillna(0.0).to_list()
    return {
        "job_key": job_key(job),
        "representation_key": rep_key,
        "model_key": model_key,
        "seed": seed,
        "elapsed_sec": time.time() - started,
        "representation_metadata": train_meta,
        "model_metadata": fitted["model_metadata"],
        "split_metrics": split_metrics,
        "rows_preview": preview,
        "metrics_rows": metrics_rows,
    }


def _best_metric(runs: list[dict], split_name: str, target_names: tuple[str, ...]) -> dict:
    best = {"representation_key": "", "model_key": "", "seed": 0, "target_name": target_names[0], "horizon": "H3", "score": 0.0}
    for run in runs:
        metrics = run.get("split_metrics", {}).get(split_name, {})
        for target_name in target_names:
            for horizon in CLOSEOUT_HORIZONS:
                score = metrics.get(f"{target_name}_{horizon}", {}).get("spearman")
                score = float(score) if score is not None else 0.0
                if score > best["score"]:
                    best = {
                        "representation_key": run["representation_key"],
                        "model_key": run["model_key"],
                        "seed": int(run["seed"]),
                        "target_name": target_name,
                        "horizon": f"H{horizon}",
                        "score": score,
                    }
    return best


def _metric_for(run: dict, split_name: str, target_name: str, horizon: str) -> float:
    suffix = horizon.removeprefix("H")
    value = run.get("split_metrics", {}).get(split_name, {}).get(f"{target_name}_{suffix}", {}).get("spearman")
    return float(value) if value is not None else 0.0


def _trade_for(run: dict, split_name: str, horizon: str) -> float | None:
    suffix = horizon.removeprefix("H")
    return run.get("split_metrics", {}).get(split_name, {}).get(f"simple_trade_{suffix}", {}).get("mean_signed_log_ratio")


def summarize_closeout_results(report: dict) -> dict:
    runs = report.get("runs", [])
    best_direction_select = _best_metric(runs, "val_select", ("entry_log_ratio",))
    best_amp_select = _best_metric(runs, "val_select", ("entry_up", "entry_dn"))
    direction_run = next((run for run in runs if job_key(run) == f"{best_direction_select['representation_key']}/{best_direction_select['model_key']}/{best_direction_select['seed']}"), None)
    amp_run = next((run for run in runs if job_key(run) == f"{best_amp_select['representation_key']}/{best_amp_select['model_key']}/{best_amp_select['seed']}"), None)
    trade_best = {"representation_key": "", "model_key": "", "horizon": "H3", "select_mean": None, "eval_mean": None}
    for run in runs:
        for horizon in CLOSEOUT_HORIZONS:
            select_mean = _trade_for(run, "val_select", f"H{horizon}")
            if select_mean is not None and (trade_best["select_mean"] is None or select_mean > trade_best["select_mean"]):
                trade_best = {
                    "representation_key": run["representation_key"],
                    "model_key": run["model_key"],
                    "horizon": f"H{horizon}",
                    "select_mean": select_mean,
                    "eval_mean": _trade_for(run, "val_eval", f"H{horizon}"),
                }
    summary = {
        "validation_roles_combined": bool(report.get("validation_roles_combined", True)),
        "best_directional": {
            **best_direction_select,
            "selection_score": best_direction_select["score"],
            "eval_score": _metric_for(direction_run, "val_eval", best_direction_select["target_name"], best_direction_select["horizon"]) if direction_run else 0.0,
        },
        "best_amplitude": {
            **best_amp_select,
            "selection_score": best_amp_select["score"],
            "eval_score": _metric_for(amp_run, "val_eval", best_amp_select["target_name"], best_amp_select["horizon"]) if amp_run else 0.0,
        },
        "best_trade": trade_best,
    }
    summary["verdict"] = decide_closeout_verdict(summary)
    return summary


def _collect_rows_preview(runs: list[dict]) -> pd.DataFrame:
    frames = []
    for run in runs:
        preview = run.get("rows_preview")
        if isinstance(preview, pd.DataFrame):
            frames.append(preview)
        elif isinstance(preview, list):
            frames.append(pd.DataFrame(preview))
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


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


def save_report_json(report: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serializable = json.loads(json.dumps(report, ensure_ascii=True, indent=2, default=_json_default))
    path.write_text(json.dumps(serializable, ensure_ascii=True, indent=2), encoding="utf-8")


def run_closeout_benchmark(
    args: argparse.Namespace,
    report_path: Path = REPORT_JSON_PATH,
    metrics_path: Path = REPORT_METRICS_PATH,
    rows_path: Path = REPORT_ROWS_PATH,
) -> dict:
    started = time.time()
    jobs = enumerate_closeout_jobs()
    base.heartbeat("closeout_runner_start", done_runs=0, total_runs=len(jobs), elapsed_sec=0.0)
    old_splits = _add_h24_targets_if_missing(base.load_entry_based_splits(target_mode="rebuilt"))
    splits = _convert_splits(old_splits)
    role_splits = _split_validation_roles(splits["validation"])
    splits.update(role_splits)
    validation_roles_combined = splits["val_select"] is splits["val_eval"] or len(splits["val_select"]) == len(splits["validation"])
    report = base.load_or_init_report(report_path, resume=args.resume)
    report.setdefault("runs", [])
    report.setdefault("started_at", _utc_now_iso())
    report["target_mode"] = "rebuilt"
    report["stage_status"] = "DIAGNOSTIC_ONLY"
    report["split_policy"] = SPLIT_POLICY
    report["validation_roles_combined"] = bool(validation_roles_combined)
    report["entry_based_smoke_check"] = run_entry_based_smoke_check({k: splits[k] for k in ("train", "validation", "low_n_disclosure")})
    if report["entry_based_smoke_check"]["status"] != "PASS":
        report["summary"] = {"verdict": "STOP", "status": "ENTRY_BASED_SMOKE_CHECK_FAILED"}
        save_report_json(report, report_path)
        return report

    preflight_old = {"train_core": old_splits["train_core"], "val_stop": old_splits["val_stop"], "diagnostic_holdout": old_splits["diagnostic_holdout"], "low_n_disclosure": old_splits["low_n_disclosure"]}
    original_order = base.REPRESENTATION_ORDER
    base.REPRESENTATION_ORDER = SHORTLIST_REPRESENTATIONS
    try:
        report["representation_preflight"] = base.run_all_preflight_with_progress(preflight_old, report=report, report_path=report_path, total_runs=len(jobs), started_at=started)
        report["distribution_audit"] = base.run_distribution_audit_with_progress(preflight_old, report=report, report_path=report_path, total_runs=len(jobs), started_at=started)
    finally:
        base.REPRESENTATION_ORDER = original_order

    scale_profiles = {}
    for rep_key in SHORTLIST_REPRESENTATIONS:
        base.heartbeat(f"closeout_scale_audit_start:{rep_key}", done_runs=len(report.get("runs", [])), total_runs=len(jobs), elapsed_sec=time.time() - started)
        features_by_split = {}
        metadata: dict[str, Any] = {}
        for split_name in ("train", "validation", "low_n_disclosure"):
            features, metadata = _get_cached_closeout_representation(splits, split_name, rep_key)
            features_by_split[split_name] = features
        scale_profiles[rep_key] = compute_feature_scale_audit(features_by_split, metadata)
        base.heartbeat(f"closeout_scale_audit_end:{rep_key}", done_runs=len(report.get("runs", [])), total_runs=len(jobs), elapsed_sec=time.time() - started)
    scale_status = "WARNING" if any(audit["status"] == "WARNING" for audit in scale_profiles.values()) else "PASS"
    report["scale_audit"] = {"status": scale_status, "profiles": scale_profiles}
    write_scale_audit_csv(report["scale_audit"], REPORT_SCALE_AUDIT_PATH)
    save_report_json(report, report_path)

    completed = {run["job_key"] for run in report.get("runs", [])}
    for idx, job in enumerate(jobs, start=1):
        if job_key(job) in completed:
            continue
        base.heartbeat("closeout_run_start", done_runs=len(report["runs"]), total_runs=len(jobs), elapsed_sec=time.time() - started)
        run = evaluate_closeout_job(job, splits, report)
        report["runs"].append(run)
        report["progress"] = {
            "done_runs": len(report["runs"]),
            "total_runs": len(jobs),
            "started_at": report["started_at"],
            "finished_at": None,
            "elapsed_sec": time.time() - started,
            "thread_count": base.CONFIG.xgb_threads,
            "current_job_index": idx,
        }
        save_report_json(report, report_path)
        base.heartbeat("closeout_run_end", done_runs=len(report["runs"]), total_runs=len(jobs), elapsed_sec=time.time() - started)

    report["summary"] = summarize_closeout_results(report)
    report["progress"] = {
        "done_runs": len(report["runs"]),
        "total_runs": len(jobs),
        "started_at": report["started_at"],
        "finished_at": _utc_now_iso(),
        "elapsed_sec": time.time() - started,
        "thread_count": base.CONFIG.xgb_threads,
    }
    metrics_rows = [row for run in report["runs"] for row in run.get("metrics_rows", [])]
    base.write_metrics_csv(metrics_rows, metrics_path)
    base.write_rows_csv(_collect_rows_preview(report["runs"]), rows_path)
    save_report_json(report, report_path)
    return report


def main() -> None:
    args = build_closeout_arg_parser().parse_args()
    if not args.entry_based_next_open_closeout:
        raise SystemExit("Pass --entry-based-next-open-closeout")
    run_closeout_benchmark(args)


if __name__ == "__main__":
    main()
