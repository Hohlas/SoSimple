# =============================================================================
# Файл: benchmark_direction_inside_frozen_movement_regime_rich_features.py
# Назначение: контрактный runner для проверки direction внутри frozen movement-mask
#   с богатыми feature-профилями и full-train политикой обучения.
# Язык: Python 3.10+
# Обновлён: 2026-07-10
# Зависимости:
#   Входные данные:
#     - entry-based split-ы из существующих baseline runners
#     - frozen movement scores с split_row_id
#   Выходные данные:
#     - ML/reports/direction_inside_frozen_movement_regime_rich_features.json
#     - ML/reports/direction_inside_frozen_movement_regime_rich_features_metrics.csv
#     - ML/reports/direction_inside_frozen_movement_regime_rich_features_rows.csv
#     - ML/reports/direction_inside_frozen_movement_regime_narrow_replication*.json/csv
# Использование:
#   ./.venv/bin/python ML/baseline/benchmark_direction_inside_frozen_movement_regime_rich_features.py
#   ./.venv/bin/python ML/baseline/benchmark_direction_inside_frozen_movement_regime_rich_features.py --replication-mode narrow
# Примечания:
#   - locked_test не открывается.
#   - CLI подключён к реальным split/freeze артефактам; полный grid может быть
#     тяжёлым, поэтому для smoke используйте CLI-фильтры profiles/horizons/models.
# =============================================================================

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesClassifier, HistGradientBoostingClassifier
from sklearn.metrics import accuracy_score, balanced_accuracy_score

from ML.baseline import benchmark_entry_based_amplitude_movement as amplitude
from ML.baseline import benchmark_entry_based_next_open_closeout as closeout
from ML.baseline.benchmark_entry_based_movement_filter_freeze import frozen_rule, stable_rule_hash

RICH_DIRECTION_OUTPUT_PREFIX = "direction_inside_frozen_movement_regime_rich_features"
NARROW_REPLICATION_OUTPUT_PREFIX = "direction_inside_frozen_movement_regime_narrow_replication"
REQUIRED_SCORE_COLUMNS = ("split", "split_row_id", "selected")
RICH_FEATURE_PROFILES = ("simple_combined", "nearest_k60", "nearest_k80", "corridor_5atr", "all100")
RICH_TARGET_HORIZONS = (3, 6, 12, 24)
NARROW_REPLICATION_HORIZONS = (3, 6, 9)
NARROW_REPLICATION_SEEDS = (41, 42, 43, 44, 45)
RICH_TARGET_FAMILIES = ("entry_log_ratio", "entry_up_dn_delta", "entry_up_dn_classifier")
RICH_MODEL_KEYS = ("hist_gradient_boosting", "extra_trees", "xgboost_depth3", "xgboost_depth5")
ALLOWED_RICH_VERDICTS = (
    "REJECT_DIRECTION_INSIDE_MOVEMENT_REGIME",
    "PIVOT_AMPLITUDE_OR_ENTRY_MECHANICS",
    "DIRECTION_REPLICATION_REQUIRED",
    "ABORT_CONTRACT_FAIL",
)
DEFAULT_OUTPUT_PREFIX = Path(f"ML/reports/{RICH_DIRECTION_OUTPUT_PREFIX}")
DEFAULT_FREEZE_SCORES_PATH = Path("ML/reports/entry_based_movement_filter_freeze_scores.csv")
DEFAULT_THREADS = 24
DEFAULT_SEED = 42
FORBIDDEN_FEATURE_PREFIXES = (
    "entry_up_",
    "entry_dn_",
    "entry_log_ratio_",
    "up_",
    "dn_",
    "ret_",
    "fav_",
    "adv_",
    "target_",
    "label_",
    "outcome_",
)
FORBIDDEN_FEATURE_EXACT = ("score", "selected", "frozen_selected")
SELECTED_VALUE_MAP = {
    "true": True,
    "1": True,
    "yes": True,
    "false": False,
    "0": False,
    "no": False,
}


def utc_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def resolve_effective_threads(requested_threads: int | None, parallel_workers: int = 1) -> int:
    threads = int(requested_threads or DEFAULT_THREADS)
    if parallel_workers > 1:
        threads = max(1, threads // int(parallel_workers))
    return max(1, threads)


def model_thread_settings(model_key: str, threads: int) -> dict[str, object]:
    if model_key == "extra_trees":
        return {"requested_threads": int(threads), "n_jobs": int(threads), "thread_control": "n_jobs"}
    if model_key in {"xgboost_depth3", "xgboost_depth5"}:
        return {
            "requested_threads": int(threads),
            "n_jobs": int(threads),
            "nthread": int(threads),
            "xgb_threads": int(threads),
            "thread_control": "n_jobs",
        }
    return {
        "requested_threads": int(threads),
        "n_jobs": None,
        "thread_control": "not_supported_by_estimator",
    }


def build_initial_progress(total_runs: int, requested_threads: int, effective_threads: int) -> dict[str, object]:
    return {
        "started_at": utc_now_iso(),
        "finished_at": None,
        "elapsed_sec": 0.0,
        "done_runs": 0,
        "total_runs": int(total_runs),
        "requested_threads": int(requested_threads),
        "effective_threads": int(effective_threads),
        "completed_keys": [],
    }


def resume_key(job: dict[str, object]) -> str:
    return (
        f"{job['profile']}/{job.get('seed', DEFAULT_SEED)}/{job['model_key']}/"
        f"H{int(job['horizon'])}/{job['target_family']}"
    )


def should_skip_job(job: dict[str, object], completed_keys: set[str], resume: bool) -> bool:
    return bool(resume and resume_key(job) in completed_keys)


def heartbeat(label: str, done_runs: int, total_runs: int, started: float) -> None:
    elapsed = time.time() - started
    eta = (elapsed / done_runs * (total_runs - done_runs)) if done_runs else None
    eta_text = f"{eta:.1f}s" if eta is not None else "unknown"
    print(f"[heartbeat] {label}: done_runs={done_runs}/{total_runs}, elapsed={elapsed:.1f}s, ETA={eta_text}", flush=True)


def load_completed_keys(output_prefix: Path, resume: bool) -> set[str]:
    if not resume:
        return set()
    path = Path(f"{output_prefix}.json")
    if not path.exists():
        return set()
    data = json.loads(path.read_text(encoding="utf-8"))
    progress = data.get("progress", {}) if isinstance(data, dict) else {}
    return {str(key) for key in progress.get("completed_keys", [])}


def rich_direction_config() -> dict[str, object]:
    rule = frozen_rule()
    return {
        "output_prefix": RICH_DIRECTION_OUTPUT_PREFIX,
        "frozen_rule": rule,
        "frozen_rule_hash": stable_rule_hash(rule),
        "required_score_columns": list(REQUIRED_SCORE_COLUMNS),
        "training_scope": "full_train",
        "frozen_mask_usage": "evaluation_only",
        "selection_metric": "val_select_inside_mask",
        "validation_roles": {
            "val_stop": "not_used_no_early_stopping",
            "val_select": "selection",
            "val_eval": "confirmation",
        },
        "forbidden_input_columns": [
            "score",
            "selected",
            "frozen_selected",
        ],
        "feature_profiles": list(RICH_FEATURE_PROFILES),
        "exploratory_only_profiles": ["nearest_k80"],
        "feature_availability_contract": {
            "Up/Dn": "serialized_fractal_fields_only",
            "shift": "serialized_fractal_fields_available_at_row",
            "fractal0.price": "serialized_fractal0_available_at_row",
            "ATR": "row_value_available_at_row",
        },
    }


def narrow_replication_config() -> dict[str, object]:
    config = rich_direction_config()
    config.update(
        {
            "stage_name": "direction_inside_frozen_mask_narrow_replication",
            "output_prefix_name": NARROW_REPLICATION_OUTPUT_PREFIX,
            "replication_mode": "narrow",
            "feature_profiles": ["nearest_k60"],
            "model_keys": ["extra_trees"],
            "target_families": ["entry_log_ratio"],
            "target_horizons": list(NARROW_REPLICATION_HORIZONS),
            "replication_seeds": list(NARROW_REPLICATION_SEEDS),
            "primary_horizon": 3,
            "secondary_horizons": [6, 9],
            "selection_policy": "pre_registered_no_new_winner_search",
            "max_positive_verdict": "DIRECTION_REPLICATION_SUPPORTED_RESEARCH_ONLY",
            "locked_test": "not_opened",
            "threads": DEFAULT_THREADS,
            "parallel_workers": 1,
        }
    )
    return config


def build_rich_direction_jobs(config: dict[str, object]) -> list[dict[str, object]]:
    profiles = tuple(config.get("feature_profiles", RICH_FEATURE_PROFILES))
    horizons = tuple(
        int(value)
        for value in config.get("executable_horizons", config.get("target_horizons", RICH_TARGET_HORIZONS))
    )
    target_families = tuple(config.get("target_families", RICH_TARGET_FAMILIES))
    model_keys = tuple(config.get("model_keys", RICH_MODEL_KEYS))
    seeds = tuple(int(value) for value in config.get("replication_seeds", [config.get("seed", DEFAULT_SEED)]))
    return [
        {
            "profile": str(profile),
            "horizon": int(horizon),
            "target_family": str(target_family),
            "model_key": str(model_key),
            "seed": int(seed),
        }
        for seed in seeds
        for profile in profiles
        for horizon in horizons
        for target_family in target_families
        for model_key in model_keys
    ]


def _normalize_split_row_ids(scores: pd.DataFrame) -> pd.Series:
    row_ids = pd.to_numeric(scores["split_row_id"], errors="coerce")
    numeric_row_ids = row_ids.to_numpy(dtype=float)

    if not np.isfinite(numeric_row_ids).all():
        raise ValueError("scores.split_row_id contains missing or invalid values")
    if not np.equal(numeric_row_ids, np.floor(numeric_row_ids)).all():
        raise ValueError("scores.split_row_id must contain integer values")

    return row_ids.astype(int)


def _normalize_selected_values(scores: pd.DataFrame) -> pd.Series:
    selected = scores["selected"]
    if pd.api.types.is_bool_dtype(selected):
        return selected.astype(bool)
    if pd.api.types.is_numeric_dtype(selected):
        numeric = pd.to_numeric(selected, errors="coerce")
        if numeric.isna().any() or not numeric.isin([0, 1]).all():
            raise ValueError("scores.selected contains invalid values")
        return numeric.astype(bool)

    selected_raw = selected.astype(str).str.strip().str.lower()
    unknown = sorted(set(selected_raw) - set(SELECTED_VALUE_MAP))
    if unknown:
        raise ValueError(f"scores.selected contains invalid values: {unknown}")
    return selected_raw.map(SELECTED_VALUE_MAP).astype(bool)


def _validate_score_contract(scores: pd.DataFrame) -> None:
    missing = [column for column in REQUIRED_SCORE_COLUMNS if column not in scores.columns]
    if missing:
        raise ValueError(f"scores missing required columns: {', '.join(missing)}")

    row_ids = _normalize_split_row_ids(scores)

    duplicated = pd.DataFrame({"split": scores["split"], "split_row_id": row_ids}).duplicated()
    if duplicated.any():
        raise ValueError("scores split + split_row_id must be unique")


def load_rich_direction_inputs(
    splits: dict[str, pd.DataFrame],
    scores: pd.DataFrame,
) -> dict[str, object]:
    return {
        "config": rich_direction_config(),
        "splits": attach_frozen_mask_by_row_id(splits, scores),
        "scores": scores.copy(),
    }


def attach_frozen_mask_by_row_id(
    splits: dict[str, pd.DataFrame],
    scores: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    _validate_score_contract(scores)

    working_scores = scores.loc[:, ["split", "split_row_id", "selected"]].copy()
    working_scores["split_row_id"] = _normalize_split_row_ids(working_scores)
    working_scores["frozen_selected"] = _normalize_selected_values(working_scores)
    working_scores = working_scores.drop(columns=["selected"])

    joined: dict[str, pd.DataFrame] = {}
    for split_name, frame in splits.items():
        split_mask = working_scores.loc[working_scores["split"] == split_name, ["split_row_id", "frozen_selected"]]
        expected_ids = pd.Index(range(len(frame)), dtype="int64")
        actual_ids = pd.Index(split_mask["split_row_id"].to_numpy(dtype=int), dtype="int64")

        split_frame = frame.copy()
        split_frame["split_row_id"] = split_frame.index.to_numpy()
        before_rows = len(split_frame)
        merged = split_frame.merge(split_mask, on="split_row_id", how="left", validate="one_to_one")

        if len(merged) != before_rows:
            raise ValueError(f"mask join changed row count for {split_name}")

        if len(split_mask) != before_rows:
            raise ValueError(
                f"mask join row count mismatch for {split_name}: scores={len(split_mask)} split={before_rows}"
            )
        if not actual_ids.equals(expected_ids):
            raise ValueError(f"mask join split_row_id mismatch for {split_name}")

        merged["frozen_selected"] = merged["frozen_selected"].fillna(False).astype(bool)
        joined[split_name] = merged.drop(columns=["split_row_id"])

    return joined


def _is_forbidden_feature_column(column: str) -> bool:
    return column in FORBIDDEN_FEATURE_EXACT or any(column.startswith(prefix) for prefix in FORBIDDEN_FEATURE_PREFIXES)


def audit_forbidden_feature_columns(features: pd.DataFrame) -> dict[str, object]:
    forbidden = [column for column in features.columns if _is_forbidden_feature_column(str(column))]
    return {
        "status": "ERROR" if forbidden else "PASS",
        "forbidden_present": forbidden,
        "forbidden_exact": list(FORBIDDEN_FEATURE_EXACT),
        "forbidden_prefixes": list(FORBIDDEN_FEATURE_PREFIXES),
    }


def audit_feature_availability(
    frame: pd.DataFrame,
    features: pd.DataFrame,
    metadata: dict[str, object] | None = None,
) -> dict[str, object]:
    feature_names = [str(column) for column in features.columns]
    serialized_columns = [str(column) for column in frame.columns if str(column).startswith("fractal")]
    metadata = metadata or {}
    feature_families = {str(item) for item in metadata.get("feature_families", []) if item is not None}
    updn_feature_names = [
        name
        for name in feature_names
        if "_up_" in name.lower() or "_dn_" in name.lower() or name.lower().endswith("_up") or name.lower().endswith("_dn")
    ]
    forbidden_updn_feature_names = [
        name for name in feature_names if name.startswith(("Up", "Dn", "up_", "dn_", "entry_up_", "entry_dn_"))
    ]
    source_columns = {
        "ATR": "ATR" in frame.columns,
        "fractal0.price": "fractal0" in frame.columns,
        "shift": bool([name for name in feature_names if "shift" in name.lower()])
        or bool(serialized_columns)
        or "shift_age" in feature_families,
        "Up/Dn": bool(updn_feature_names) or bool(serialized_columns) or "updn_full" in feature_families,
    }
    reasons = [name for name, present in source_columns.items() if not present]
    if forbidden_updn_feature_names:
        reasons.append("top_level_updn_source_forbidden")
    return {
        "status": "ERROR" if reasons else "PASS",
        "required_sources": source_columns,
        "forbidden_updn_feature_names": forbidden_updn_feature_names,
        "serialized_fractal_columns_present": bool(serialized_columns),
        "feature_families": sorted(feature_families),
        "updn_feature_count": len(updn_feature_names),
        "reasons": reasons,
    }


def _numeric_model_inputs(features: pd.DataFrame) -> pd.DataFrame:
    numeric = features.apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan)
    return numeric.fillna(0.0).astype(float)


def _build_rich_feature_frame(frame: pd.DataFrame, profile: str) -> tuple[pd.DataFrame, dict[str, object]]:
    if profile == "simple_combined":
        features, metadata = amplitude.build_simple_feature_frame(frame, "simple_combined")
    elif profile in {"nearest_k60", "nearest_k80", "corridor_5atr", "all100"}:
        features, metadata = closeout.build_closeout_representation_features(frame, profile)
    else:
        raise ValueError(f"unknown rich feature profile: {profile}")

    numeric_features = _numeric_model_inputs(features)
    forbidden_audit = audit_forbidden_feature_columns(numeric_features)
    availability_audit = audit_feature_availability(frame, numeric_features, metadata)
    if forbidden_audit["status"] != "PASS":
        raise ValueError(f"Forbidden feature columns present: {forbidden_audit['forbidden_present']}")
    if availability_audit["status"] != "PASS":
        raise ValueError(f"Feature availability audit failed: {availability_audit['reasons']}")

    output_metadata = dict(metadata)
    output_metadata.update(
        {
            "profile": profile,
            "feature_names": list(numeric_features.columns),
            "feature_count": int(numeric_features.shape[1]),
            "forbidden_feature_audit": forbidden_audit,
            "feature_availability_audit": availability_audit,
        }
    )
    return numeric_features, output_metadata


def rich_feature_metadata_for_json() -> dict[str, object]:
    return getattr(build_rich_feature_frames, "last_metadata", {"profiles": list(RICH_FEATURE_PROFILES), "splits": {}})


def build_rich_feature_frames(
    splits: dict[str, pd.DataFrame],
    profile: str,
) -> dict[str, pd.DataFrame]:
    if profile not in RICH_FEATURE_PROFILES:
        raise ValueError(f"unknown rich feature profile: {profile}")

    frames: dict[str, pd.DataFrame] = {}
    metadata_by_split: dict[str, dict[str, object]] = {}
    expected_columns: list[str] | None = None
    for split_name, frame in splits.items():
        features, metadata = _build_rich_feature_frame(frame, profile)
        if len(features) != len(frame):
            raise ValueError(f"feature row count mismatch for {split_name}")
        if not features.index.equals(frame.index):
            features.index = frame.index
        columns = list(features.columns)
        if expected_columns is None:
            expected_columns = columns
        elif columns != expected_columns:
            raise ValueError(f"feature columns differ for {split_name}")
        frames[split_name] = features
        metadata_by_split[split_name] = metadata

    setattr(build_rich_feature_frames, "last_metadata", {"profile": profile, "splits": metadata_by_split})
    return frames


def _required_target_columns(horizon: int) -> tuple[str, str, str]:
    return (f"entry_log_ratio_{horizon}", f"entry_up_{horizon}", f"entry_dn_{horizon}")


def preflight_target_horizons(
    splits: dict[str, pd.DataFrame],
    horizons: tuple[int, ...] | list[int],
) -> dict[str, object]:
    horizon_results: dict[str, dict[str, object]] = {}
    executable: list[int] = []
    skipped: list[int] = []
    for horizon_value in horizons:
        horizon = int(horizon_value)
        required = list(_required_target_columns(horizon))
        missing_by_split = {
            split_name: [column for column in required if column not in frame.columns]
            for split_name, frame in splits.items()
        }
        missing_by_split = {name: missing for name, missing in missing_by_split.items() if missing}
        if missing_by_split:
            skipped.append(horizon)
            horizon_results[str(horizon)] = {
                "status": "SKIPPED_MISSING_TARGET_COLUMNS",
                "required_columns": required,
                "missing_by_split": missing_by_split,
            }
            continue
        executable.append(horizon)
        horizon_results[str(horizon)] = {
            "status": "PASS",
            "required_columns": required,
            "missing_by_split": {},
        }

    return {
        "status": "PASS" if not skipped else "WARNING",
        "horizons": horizon_results,
        "executable_horizons": executable,
        "skipped_horizons": skipped,
    }


def build_direction_targets(
    frame: pd.DataFrame,
    horizon: int,
    dead_zone: float = 0.0,
) -> pd.DataFrame:
    allowed_horizons = set(RICH_TARGET_HORIZONS).union(NARROW_REPLICATION_HORIZONS)
    if horizon not in allowed_horizons:
        raise ValueError(f"unknown target horizon: {horizon}")

    log_ratio_column, up_column, dn_column = _required_target_columns(horizon)
    missing = [column for column in (log_ratio_column, up_column, dn_column) if column not in frame.columns]
    if missing:
        raise ValueError(f"missing direction target columns: {missing}")

    log_ratio = pd.to_numeric(frame[log_ratio_column], errors="coerce")
    up = pd.to_numeric(frame[up_column], errors="coerce")
    dn = pd.to_numeric(frame[dn_column], errors="coerce")

    log_direction = pd.Series(0, index=frame.index, dtype="int64")
    valid_log = log_ratio.notna()
    active_log = valid_log & (log_ratio.abs() > float(dead_zone))
    log_direction.loc[active_log & (log_ratio > 0.0)] = 1
    log_direction.loc[active_log & (log_ratio < 0.0)] = -1

    delta = up - dn
    updn_direction = pd.Series(0, index=frame.index, dtype="int64")
    valid_updn = up.notna() & dn.notna()
    updn_direction.loc[valid_updn & (up > dn)] = 1
    updn_direction.loc[valid_updn & (dn > up)] = -1

    targets = pd.DataFrame(index=frame.index)
    targets["entry_log_ratio"] = log_ratio
    targets["entry_up_dn_delta"] = delta
    targets["entry_up_dn_classifier"] = pd.Series(pd.NA, index=frame.index, dtype="Int64")
    targets.loc[valid_updn & (up > dn), "entry_up_dn_classifier"] = 1
    targets.loc[valid_updn & (up < dn), "entry_up_dn_classifier"] = 0
    targets["direction_from_log_ratio"] = log_direction
    targets["direction_from_up_dn"] = updn_direction
    targets["is_log_ratio_dead_zone"] = valid_log & (log_ratio.abs() <= float(dead_zone))
    targets["is_up_dn_tie"] = valid_updn & (up == dn)
    targets["horizon"] = int(horizon)
    targets["dead_zone"] = float(dead_zone)
    return targets


def training_scope_counts(frame: pd.DataFrame) -> dict[str, object]:
    frozen_selected = frame.get("frozen_selected", pd.Series([False] * len(frame), index=frame.index)).astype(bool)
    return {
        "train_rows_used_for_fit": int(len(frame)),
        "train_frozen_selected_rows": int(frozen_selected.sum()),
        "training_scope": "full_train",
    }


def masked_sample_size_gate(
    metrics_input: pd.DataFrame,
    split: str,
    min_masked_rows: int = 100,
    min_active_sign_rows: int = 30,
) -> dict[str, object]:
    split_frame = metrics_input.loc[metrics_input["split"].eq(split)].copy() if "split" in metrics_input.columns else metrics_input.copy()
    masked = split_frame.loc[split_frame.get("frozen_selected", False).astype(bool)].copy()
    reasons: list[str] = []
    if len(masked) < min_masked_rows:
        reasons.append("min_masked_rows")

    target_column = "target_direction" if "target_direction" in masked.columns else "direction_from_log_ratio"
    if target_column in masked.columns:
        active = pd.to_numeric(masked[target_column], errors="coerce")
        for sign, reason in ((1, "min_active_positive_rows"), (-1, "min_active_negative_rows")):
            if int((active == sign).sum()) < min_active_sign_rows:
                reasons.append(reason)
    else:
        reasons.append("target_direction_missing")

    return {
        "status": "FAIL" if reasons else "PASS",
        "split": split,
        "masked_rows": int(len(masked)),
        "min_masked_rows": int(min_masked_rows),
        "min_active_sign_rows": int(min_active_sign_rows),
        "reasons": reasons,
    }


def _direction_metrics(y_true: pd.Series, y_pred: pd.Series) -> dict[str, object]:
    actual = pd.to_numeric(y_true, errors="coerce")
    pred = pd.to_numeric(y_pred, errors="coerce")
    valid = actual.isin([-1, 1]) & pred.isin([-1, 1])
    if int(valid.sum()) == 0:
        return {
            "n": 0,
            "accuracy": float("nan"),
            "balanced_accuracy": float("nan"),
            "positive_rows": 0,
            "negative_rows": 0,
        }
    actual_valid = actual.loc[valid].astype(int)
    pred_valid = pred.loc[valid].astype(int)
    return {
        "n": int(valid.sum()),
        "accuracy": float(accuracy_score(actual_valid, pred_valid)),
        "balanced_accuracy": float(balanced_accuracy_score(actual_valid, pred_valid)),
        "positive_rows": int((actual_valid == 1).sum()),
        "negative_rows": int((actual_valid == -1).sum()),
    }


def evaluate_direction_predictions(
    predictions: pd.Series | np.ndarray | list[float],
    targets: pd.DataFrame,
    frozen_selected: pd.Series | np.ndarray | list[bool],
) -> dict[str, object]:
    pred_series = pd.Series(predictions, index=targets.index)
    target_column = "target_direction" if "target_direction" in targets.columns else "direction_from_log_ratio"
    if target_column not in targets.columns:
        raise ValueError("targets must include target_direction or direction_from_log_ratio")
    frozen = pd.Series(frozen_selected, index=targets.index).astype(bool)
    full_metrics = _direction_metrics(targets[target_column], pred_series)
    frozen_metrics = _direction_metrics(targets.loc[frozen, target_column], pred_series.loc[frozen])
    gate_input = pd.DataFrame(
        {
            "split": ["evaluation"] * len(targets),
            "frozen_selected": frozen.to_numpy(dtype=bool),
            "target_direction": targets[target_column].to_numpy(),
        },
        index=targets.index,
    )
    return {
        "full": full_metrics,
        "frozen_selected": frozen_metrics,
        "sample_size_gate": masked_sample_size_gate(gate_input, split="evaluation"),
    }


def _make_direction_model(model_key: str, config: dict[str, object]) -> object:
    seed = int(config.get("seed", DEFAULT_SEED))
    threads = int(config.get("threads", DEFAULT_THREADS))
    if model_key == "hist_gradient_boosting":
        return HistGradientBoostingClassifier(max_iter=80, learning_rate=0.05, random_state=seed)
    if model_key == "extra_trees":
        settings = model_thread_settings(model_key, threads)
        return ExtraTreesClassifier(n_estimators=200, min_samples_leaf=5, random_state=seed, n_jobs=int(settings["n_jobs"]))
    if model_key in {"xgboost_depth3", "xgboost_depth5"}:
        import xgboost as xgb

        settings = model_thread_settings(model_key, threads)
        return xgb.XGBClassifier(
            n_estimators=200,
            max_depth=3 if model_key == "xgboost_depth3" else 5,
            learning_rate=0.05,
            subsample=0.80,
            colsample_bytree=0.80,
            objective="binary:logistic",
            eval_metric="logloss",
            random_state=seed,
            n_jobs=int(settings["n_jobs"]),
            tree_method="hist",
        )
    raise ValueError(f"unknown model key: {model_key}")


def _target_direction_for_fit(train_targets: pd.DataFrame) -> pd.Series:
    column = "target_direction" if "target_direction" in train_targets.columns else "direction_from_log_ratio"
    if column not in train_targets.columns:
        raise ValueError("train_targets must include target_direction or direction_from_log_ratio")
    direction = pd.to_numeric(train_targets[column], errors="coerce")
    return direction


def fit_direction_models(
    train_features: pd.DataFrame,
    train_targets: pd.DataFrame,
    config: dict[str, object],
) -> dict[str, object]:
    model_keys = tuple(config.get("model_keys", RICH_MODEL_KEYS))
    features = _numeric_model_inputs(train_features)
    direction = _target_direction_for_fit(train_targets)
    valid = direction.isin([-1, 1])
    x_train = features.loc[valid]
    y_train = (direction.loc[valid].astype(int) == 1).astype(int)

    fitted_models: dict[str, object] = {}
    failed_runs: list[dict[str, object]] = []
    for model_key in model_keys:
        try:
            model = _make_direction_model(str(model_key), config)
            if y_train.nunique() < 2:
                raise ValueError("need both active direction classes for fit")
            model.fit(x_train, y_train)
            fitted_models[str(model_key)] = model
        except Exception as exc:  # optional xgboost and tiny synthetic data should disclose, not abort.
            failed_runs.append({"model_key": str(model_key), "error": type(exc).__name__, "message": str(exc)})

    return {
        "training_scope": "full_train",
        "train_rows_seen_before_active_filter": int(len(train_features)),
        "train_rows_used_for_fit": int(len(x_train)),
        "model_keys": list(model_keys),
        "models": fitted_models,
        "failed_runs": failed_runs,
        "cumulative_search_budget": int(len(model_keys)),
        "baselines": {
            "majority_sign_prior": int(1 if (direction == 1).sum() >= (direction == -1).sum() else -1),
            "no_direction": 0,
            "old_simple_combined": "control_profile",
        },
        "early_stopping": "not_used",
    }


def _json_ready(value: object) -> object:
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, pd.DataFrame):
        return value.to_dict(orient="records")
    if isinstance(value, pd.Series):
        return value.tolist()
    return value


def _summarize_metric_window(frame: pd.DataFrame) -> dict[str, object]:
    numeric = pd.to_numeric(frame["balanced_accuracy"], errors="coerce").dropna()
    if numeric.empty:
        return {
            "median_balanced_accuracy": float("nan"),
            "mean_balanced_accuracy": float("nan"),
            "min_balanced_accuracy": float("nan"),
            "max_balanced_accuracy": float("nan"),
        }
    return {
        "median_balanced_accuracy": float(numeric.median()),
        "mean_balanced_accuracy": float(numeric.mean()),
        "min_balanced_accuracy": float(numeric.min()),
        "max_balanced_accuracy": float(numeric.max()),
    }


def aggregate_narrow_replication(metrics: pd.DataFrame, summary: dict[str, object]) -> dict[str, object]:
    target_preflight = summary.get("target_preflight", {}) if isinstance(summary.get("target_preflight"), dict) else {}
    requested_horizons = [
        int(value)
        for value in summary.get("target_horizons", list(NARROW_REPLICATION_HORIZONS))
    ]
    primary_horizon = int(summary.get("primary_horizon", 3))
    secondary_horizons = [int(value) for value in summary.get("secondary_horizons", [6, 9])]
    filtered = metrics.copy()
    if "slice" in filtered.columns:
        filtered = filtered.loc[filtered["slice"].eq("frozen_selected")].copy()
    if "split" in filtered.columns:
        filtered = filtered.loc[filtered["split"].isin(["val_select", "val_eval"])].copy()
    if "horizon" in filtered.columns:
        filtered["horizon"] = pd.to_numeric(filtered["horizon"], errors="coerce").astype("Int64")
    if "seed" in filtered.columns:
        filtered["seed"] = pd.to_numeric(filtered["seed"], errors="coerce").astype("Int64")
    if "balanced_accuracy" in filtered.columns:
        filtered["balanced_accuracy"] = pd.to_numeric(filtered["balanced_accuracy"], errors="coerce")

    failed_runs = summary.get("failed_runs", []) if isinstance(summary.get("failed_runs"), list) else []
    horizon_summaries: dict[str, dict[str, object]] = {}
    for horizon in requested_horizons:
        horizon_key = str(horizon)
        horizon_rows = filtered.loc[filtered["horizon"].eq(horizon)].copy() if "horizon" in filtered.columns else filtered.iloc[0:0]
        preflight_entry = target_preflight.get("horizons", {}).get(horizon_key, {})
        horizon_target_failures = [
            run
            for run in failed_runs
            if str(run.get("stage")) == "targets" and int(run.get("horizon", -1)) == int(horizon)
        ]
        executed = not horizon_rows.empty
        gate_failures: list[dict[str, object]] = []
        same_positive_sign_seed_count = 0
        val_eval_seeds_ge_0_52 = 0
        val_eval_seeds_ge_0_50 = 0
        seed_rows: list[dict[str, object]] = []

        for seed_value in sorted(horizon_rows["seed"].dropna().astype(int).unique()) if "seed" in horizon_rows.columns else []:
            seed_frame = horizon_rows.loc[horizon_rows["seed"].eq(seed_value)].copy()
            val_select_row = seed_frame.loc[seed_frame["split"].eq("val_select")].head(1)
            val_eval_row = seed_frame.loc[seed_frame["split"].eq("val_eval")].head(1)
            val_select_score = float(val_select_row["balanced_accuracy"].iloc[0]) if not val_select_row.empty else float("nan")
            val_eval_score = float(val_eval_row["balanced_accuracy"].iloc[0]) if not val_eval_row.empty else float("nan")
            val_select_gate = str(val_select_row["sample_size_gate"].iloc[0]) if not val_select_row.empty else "MISSING"
            val_eval_gate = str(val_eval_row["sample_size_gate"].iloc[0]) if not val_eval_row.empty else "MISSING"
            if val_select_gate != "PASS" or val_eval_gate != "PASS":
                gate_failures.append(
                    {
                        "seed": int(seed_value),
                        "val_select_gate": val_select_gate,
                        "val_eval_gate": val_eval_gate,
                    }
                )
            if np.isfinite(val_eval_score) and val_eval_score >= 0.52:
                val_eval_seeds_ge_0_52 += 1
            if np.isfinite(val_eval_score) and val_eval_score >= 0.50:
                val_eval_seeds_ge_0_50 += 1
            if np.isfinite(val_select_score) and np.isfinite(val_eval_score) and val_select_score > 0.50 and val_eval_score > 0.50:
                same_positive_sign_seed_count += 1
            seed_rows.append(
                {
                    "seed": int(seed_value),
                    "val_select_balanced_accuracy": val_select_score,
                    "val_eval_balanced_accuracy": val_eval_score,
                    "val_select_gate": val_select_gate,
                    "val_eval_gate": val_eval_gate,
                }
            )

        if "split" in horizon_rows.columns:
            val_eval_rows = horizon_rows.loc[horizon_rows["split"].eq("val_eval")].copy()
            val_select_rows = horizon_rows.loc[horizon_rows["split"].eq("val_select")].copy()
        else:
            val_eval_rows = horizon_rows.iloc[0:0].copy()
            val_select_rows = horizon_rows.iloc[0:0].copy()
        val_eval_summary = _summarize_metric_window(val_eval_rows) if not val_eval_rows.empty else _summarize_metric_window(
            pd.DataFrame({"balanced_accuracy": []})
        )
        val_select_summary = _summarize_metric_window(val_select_rows) if not val_select_rows.empty else _summarize_metric_window(
            pd.DataFrame({"balanced_accuracy": []})
        )

        status = str(preflight_entry.get("status", "PASS"))
        if horizon_target_failures:
            status = "TARGET_CONTRACT_FAIL"
        if executed:
            status = "PASS"
        horizon_summaries[horizon_key] = {
            "status": status,
            "executed": executed,
            "seed_count": int(len(seed_rows)),
            "seed_rows": seed_rows,
            "val_select_median_balanced_accuracy": val_select_summary["median_balanced_accuracy"],
            "val_select_mean_balanced_accuracy": val_select_summary["mean_balanced_accuracy"],
            "val_select_min_balanced_accuracy": val_select_summary["min_balanced_accuracy"],
            "val_select_max_balanced_accuracy": val_select_summary["max_balanced_accuracy"],
            "val_eval_median_balanced_accuracy": val_eval_summary["median_balanced_accuracy"],
            "val_eval_mean_balanced_accuracy": val_eval_summary["mean_balanced_accuracy"],
            "val_eval_min_balanced_accuracy": val_eval_summary["min_balanced_accuracy"],
            "val_eval_max_balanced_accuracy": val_eval_summary["max_balanced_accuracy"],
            "val_eval_seeds_ge_0_52": int(val_eval_seeds_ge_0_52),
            "val_eval_seeds_ge_0_50": int(val_eval_seeds_ge_0_50),
            "same_positive_sign_seed_count": int(same_positive_sign_seed_count),
            "gate_failures": gate_failures,
            "gate_failures_count": int(len(gate_failures)),
            "required_columns": preflight_entry.get("required_columns", list(_required_target_columns(horizon))),
            "missing_by_split": preflight_entry.get("missing_by_split", {}),
            "target_contract_failures": _json_ready(horizon_target_failures),
        }

    contract_status = str(summary.get("contract_status", "PASS"))
    return {
        "status": "PASS" if contract_status == "PASS" else "WARNING",
        "scope": "research_only",
        "contract_status": contract_status,
        "failed_run_count": int(len(failed_runs)),
        "primary_horizon": primary_horizon,
        "secondary_horizons": secondary_horizons,
        "requested_horizons": requested_horizons,
        "executed_horizons": [int(value) for value in target_preflight.get("executable_horizons", [])] or [
            int(key) for key, value in horizon_summaries.items() if value.get("executed")
        ],
        "skipped_horizons": [int(value) for value in target_preflight.get("skipped_horizons", [])],
        "horizons": horizon_summaries,
    }


def narrow_replication_verdict(replication: dict[str, object]) -> str:
    horizons = replication.get("horizons", {}) if isinstance(replication.get("horizons"), dict) else {}
    primary = horizons.get(str(replication.get("primary_horizon", 3)), {})
    primary_median = float(primary.get("val_eval_median_balanced_accuracy", float("nan")))
    primary_seeds_ge_0_52 = int(primary.get("val_eval_seeds_ge_0_52", 0))
    primary_same_positive = int(primary.get("same_positive_sign_seed_count", 0))
    primary_gate_failures = int(primary.get("gate_failures_count", 0))

    if not np.isfinite(primary_median):
        return "DIRECTION_REPLICATION_INCONCLUSIVE"
    if primary_median < 0.515 or primary_seeds_ge_0_52 < 2:
        return "REJECT_DIRECTION_REPLICATION"

    if replication.get("contract_status") != "PASS" or int(replication.get("failed_run_count", 0)) > 0:
        return "DIRECTION_REPLICATION_INCONCLUSIVE"

    primary_pass = (
        primary_seeds_ge_0_52 >= 3
        and primary_median >= 0.525
        and primary_same_positive >= 3
        and primary_gate_failures == 0
    )
    if not primary_pass:
        return "DIRECTION_REPLICATION_INCONCLUSIVE"

    for horizon in replication.get("secondary_horizons", []):
        horizon_summary = horizons.get(str(horizon), {})
        status = horizon_summary.get("status")
        if status == "SKIPPED_MISSING_TARGET_COLUMNS":
            continue
        if not horizon_summary.get("executed"):
            continue
        median_score = float(horizon_summary.get("val_eval_median_balanced_accuracy", float("nan")))
        seeds_ge_0_50 = int(horizon_summary.get("val_eval_seeds_ge_0_50", 0))
        if not np.isfinite(median_score) or median_score < 0.505 or seeds_ge_0_50 < 2:
            return "DIRECTION_REPLICATION_INCONCLUSIVE"

    return "DIRECTION_REPLICATION_SUPPORTED_RESEARCH_ONLY"


def compute_narrow_time_diagnostics(rows: pd.DataFrame, block_count: int = 4) -> dict[str, object]:
    filtered = rows.copy()
    if "split" in filtered.columns:
        filtered = filtered.loc[filtered["split"].isin(["val_select", "val_eval"])].copy()
    if "frozen_selected" in filtered.columns:
        filtered = filtered.loc[pd.Series(filtered["frozen_selected"]).astype(bool)].copy()
    else:
        filtered = filtered.iloc[0:0]

    by_year: dict[str, dict[str, object]] = {}
    by_block: list[dict[str, object]] = []
    status = "PASS"

    if "time" in filtered.columns:
        filtered["parsed_time"] = pd.to_datetime(filtered["time"], errors="coerce")
        time_available = filtered["parsed_time"].notna().any()
        if time_available:
            for year, year_frame in filtered.loc[filtered["parsed_time"].notna()].groupby(filtered["parsed_time"].dt.year.astype(str)):
                metrics = _direction_metrics(year_frame["target_direction"], year_frame["prediction"])
                by_year[str(year)] = {
                    "n": int(metrics["n"]),
                    "accuracy": metrics["accuracy"],
                    "balanced_accuracy": metrics["balanced_accuracy"],
                    "status": "LOW_N_DIAGNOSTIC_ONLY" if int(metrics["n"]) < 30 else "PASS",
                }
        else:
            status = "WARNING"
    else:
        status = "WARNING"
        filtered["parsed_time"] = pd.NaT

    group_columns = ["resume_key", "split"] if {"resume_key", "split"} <= set(filtered.columns) else ["split"]
    for group_key, group_frame in filtered.groupby(group_columns, dropna=False):
        ordered = group_frame.sort_values(
            by=["parsed_time", "row_id"] if "row_id" in group_frame.columns else ["parsed_time"],
            ascending=[True, True] if "row_id" in group_frame.columns else [True],
            na_position="last",
        ).reset_index(drop=True)
        blocks = np.array_split(np.arange(len(ordered)), max(1, int(block_count)))
        if not isinstance(group_key, tuple):
            group_key = (group_key,)
        for block_index, block_indices in enumerate(blocks, start=1):
            block_frame = ordered.iloc[block_indices].copy() if len(block_indices) else ordered.iloc[0:0].copy()
            metrics = _direction_metrics(block_frame["target_direction"], block_frame["prediction"]) if not block_frame.empty else {
                "n": 0,
                "accuracy": float("nan"),
                "balanced_accuracy": float("nan"),
            }
            block_record = {
                "resume_key": str(group_key[0]) if group_columns[0] == "resume_key" else "",
                "split": str(group_key[-1]),
                "block_index": int(block_index),
                "n": int(metrics["n"]),
                "accuracy": metrics["accuracy"],
                "balanced_accuracy": metrics["balanced_accuracy"],
                "status": "LOW_N_DIAGNOSTIC_ONLY" if int(metrics["n"]) < 30 else "PASS",
            }
            if not block_frame.empty:
                block_record["row_id_start"] = int(block_frame["row_id"].min()) if "row_id" in block_frame.columns else 0
                block_record["row_id_end"] = int(block_frame["row_id"].max()) if "row_id" in block_frame.columns else 0
            by_block.append(block_record)

    return {
        "status": status,
        "scope": "diagnostic_only_not_verdict_gate",
        "by_year": by_year,
        "by_block": by_block,
    }


def select_rich_direction_winner(metrics: pd.DataFrame) -> dict[str, object]:
    required = {"run_id", "split", "slice", "balanced_accuracy"}
    missing = sorted(required - set(metrics.columns))
    if missing:
        raise ValueError(f"metrics missing required columns: {missing}")

    selectable = metrics.loc[
        metrics["split"].eq("val_select")
        & metrics["slice"].eq("frozen_selected")
        & pd.to_numeric(metrics["balanced_accuracy"], errors="coerce").notna()
    ].copy()
    if selectable.empty:
        return {"status": "NO_CANDIDATE", "selection_split": "val_select", "selection_slice": "frozen_selected"}

    selectable["_selection_score"] = pd.to_numeric(selectable["balanced_accuracy"], errors="coerce")
    row = selectable.sort_values(["_selection_score", "run_id"], ascending=[False, True]).iloc[0].drop(labels=["_selection_score"])
    run_id = row["run_id"]
    matching = metrics.loc[metrics["run_id"].eq(run_id)].copy()
    eval_rows = matching.loc[matching["split"].eq("val_eval") & matching["slice"].eq("frozen_selected")]
    full_rows = matching.loc[matching["slice"].eq("full")]
    return {
        "status": "SELECTED",
        "run_id": run_id,
        "selection_split": "val_select",
        "selection_slice": "frozen_selected",
        "selection_metric": "balanced_accuracy",
        "selection_score": float(row["balanced_accuracy"]),
        "winner": _json_ready(row.to_dict()),
        "val_eval_inside_mask": _json_ready(eval_rows.to_dict(orient="records")),
        "full_split_diagnostics": _json_ready(full_rows.to_dict(orient="records")),
        "selection_policy": "val_select_inside_mask_only",
        "low_n_disclosure_used_for_selection": False,
    }


def rich_direction_verdict(summary: dict[str, object]) -> str:
    if summary.get("contract_status") == "ABORT_CONTRACT_FAIL" or summary.get("audit_status") == "ERROR":
        return "ABORT_CONTRACT_FAIL"

    winner = summary.get("winner") if isinstance(summary.get("winner"), dict) else summary
    if winner.get("status") != "SELECTED":
        return "REJECT_DIRECTION_INSIDE_MOVEMENT_REGIME"

    profile = str(winner.get("profile") or winner.get("winner", {}).get("profile", ""))
    if profile in rich_direction_config()["exploratory_only_profiles"]:
        return "REJECT_DIRECTION_INSIDE_MOVEMENT_REGIME"

    gate_status = summary.get("masked_sample_size_gate", {}).get("status") if isinstance(summary.get("masked_sample_size_gate"), dict) else None
    if gate_status not in (None, "PASS"):
        return "REJECT_DIRECTION_INSIDE_MOVEMENT_REGIME"

    selection_score = float(winner.get("selection_score", 0.0))
    eval_score = summary.get("val_eval_inside_mask_balanced_accuracy")
    if eval_score is None:
        eval_rows = winner.get("val_eval_inside_mask", [])
        if eval_rows:
            eval_score = eval_rows[0].get("balanced_accuracy")
    eval_score = float(eval_score) if eval_score is not None and pd.notna(eval_score) else float("nan")

    if selection_score >= 0.55 and np.isfinite(eval_score) and eval_score >= 0.52:
        return "DIRECTION_REPLICATION_REQUIRED"
    if bool(summary.get("amplitude_diagnostics_stronger", False)):
        return "PIVOT_AMPLITUDE_OR_ENTRY_MECHANICS"
    return "REJECT_DIRECTION_INSIDE_MOVEMENT_REGIME"


def _empty_metrics_frame() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "run_id",
            "profile",
            "horizon",
            "target_family",
            "model_key",
            "split",
            "slice",
            "balanced_accuracy",
            "accuracy",
            "n",
        ]
    )


def _empty_rows_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=["run_id", "split", "row_id", "prediction", "target_direction", "frozen_selected", "time"])


def _target_direction_for_family(targets: pd.DataFrame, target_family: str) -> pd.Series:
    if target_family == "entry_log_ratio":
        return targets["direction_from_log_ratio"]
    if target_family in {"entry_up_dn_delta", "entry_up_dn_classifier"}:
        return targets["direction_from_up_dn"]
    raise ValueError(f"unknown target family: {target_family}")


def _model_prediction_direction(model: object, features: pd.DataFrame) -> pd.Series:
    raw = pd.Series(model.predict(_numeric_model_inputs(features)), index=features.index)
    numeric = pd.to_numeric(raw, errors="coerce")
    if numeric.dropna().isin([0, 1]).all():
        return pd.Series(np.where(numeric >= 1, 1, -1), index=features.index)
    return pd.Series(np.where(numeric >= 0, 1, -1), index=features.index)


def _append_metric_rows(
    rows: list[dict[str, object]],
    run_context: dict[str, object],
    split_name: str,
    evaluated: dict[str, object],
    gate: dict[str, object],
) -> None:
    for slice_name in ("full", "frozen_selected"):
        metrics = evaluated[slice_name]
        rows.append(
            {
                **run_context,
                "split": split_name,
                "slice": slice_name,
                "balanced_accuracy": metrics["balanced_accuracy"],
                "accuracy": metrics["accuracy"],
                "n": metrics["n"],
                "positive_rows": metrics["positive_rows"],
                "negative_rows": metrics["negative_rows"],
                "sample_size_gate": gate["status"] if slice_name == "frozen_selected" else "not_applicable",
                "gate_reasons": ",".join(gate["reasons"]) if slice_name == "frozen_selected" else "",
            }
        )


def run_rich_direction_experiment(
    splits: dict[str, pd.DataFrame],
    scores: pd.DataFrame,
    config_overrides: dict[str, object] | None = None,
    output_prefix: Path | None = None,
    resume: bool = True,
) -> dict[str, object]:
    started = time.time()
    config = rich_direction_config()
    config.update(config_overrides or {})
    replication_mode = str(config.get("replication_mode", "none"))
    profiles = tuple(config.get("feature_profiles", RICH_FEATURE_PROFILES))
    requested_horizons = tuple(int(value) for value in config.get("target_horizons", RICH_TARGET_HORIZONS))
    target_families = tuple(config.get("target_families", RICH_TARGET_FAMILIES))
    model_keys = tuple(config.get("model_keys", RICH_MODEL_KEYS))
    requested_threads = int(config.get("threads", DEFAULT_THREADS))
    effective_threads = resolve_effective_threads(requested_threads, int(config.get("parallel_workers", 1)))
    min_masked_rows = int(config.get("min_masked_rows", 100))
    min_active_sign_rows = int(config.get("min_active_sign_rows", 30))
    target_preflight: dict[str, object] = {
        "status": "NOT_RUN",
        "horizons": {},
        "executable_horizons": list(requested_horizons),
        "skipped_horizons": [],
    }
    planned_jobs = build_rich_direction_jobs({**config, "target_horizons": list(requested_horizons)})
    planned_search_budget = int(len(planned_jobs))
    discovery_search_budget = 240 if replication_mode == "narrow" else 0
    executable_horizons = requested_horizons
    run_records: list[dict[str, object]] = []

    def build_summary(metric_frame: pd.DataFrame, row_frame: pd.DataFrame) -> dict[str, object]:
        selection = select_rich_direction_winner(metric_frame)
        val_eval_score = None
        if selection.get("status") == "SELECTED" and selection.get("val_eval_inside_mask"):
            val_eval_score = selection["val_eval_inside_mask"][0].get("balanced_accuracy")
        winner_gate = {}
        if selection.get("status") == "SELECTED":
            winner_gate_rows = metric_frame.loc[
                metric_frame["run_id"].eq(selection["run_id"])
                & metric_frame["split"].eq("val_select")
                & metric_frame["slice"].eq("frozen_selected")
            ]
            if not winner_gate_rows.empty:
                winner_gate = {
                    "status": winner_gate_rows.iloc[0].get("sample_size_gate"),
                    "reasons": str(winner_gate_rows.iloc[0].get("gate_reasons", "")).split(",")
                    if winner_gate_rows.iloc[0].get("gate_reasons")
                    else [],
                }

        summary = {
            "schema_version": 1,
            "stage_status": "DIAGNOSTIC_ONLY",
            "replication_mode": replication_mode,
            "training_scope": config["training_scope"],
            "frozen_mask_usage": config["frozen_mask_usage"],
            "selection_metric": config["selection_metric"],
            "validation_roles": config["validation_roles"],
            "feature_profiles": list(profiles),
            "target_horizons": list(requested_horizons),
            "executable_horizons": list(executable_horizons),
            "target_families": list(target_families),
            "model_keys": list(model_keys),
            "seed": int(config.get("seed", DEFAULT_SEED)),
            "replication_seeds": [int(value) for value in config.get("replication_seeds", [config.get("seed", DEFAULT_SEED)])],
            "primary_horizon": int(config.get("primary_horizon", 3)),
            "secondary_horizons": [int(value) for value in config.get("secondary_horizons", [6, 9])],
            "locked_test": "not_opened",
            "low_n_disclosure_used_for_selection": False,
            "training_scope_counts": train_scope,
            "train_rows": int(len(masked_splits["train"])),
            "frozen_mask_row_counts": {
                split_name: int(frame["frozen_selected"].astype(bool).sum())
                for split_name, frame in masked_splits.items()
                if "frozen_selected" in frame.columns
            },
            "feature_metadata": feature_metadata,
            "threading": {
                "requested_threads": requested_threads,
                "effective_threads": effective_threads,
                "parallel_workers": int(config.get("parallel_workers", 1)),
                "model_settings": {
                    str(model_key): model_thread_settings(str(model_key), effective_threads) for model_key in model_keys
                },
            },
            "progress": progress,
            "runs": run_records,
            "failed_runs": failed_runs,
            "target_preflight": target_preflight,
            "planned_search_budget": planned_search_budget,
            "executed_search_budget": int(len(jobs)),
            "replication_search_budget_planned": planned_search_budget if replication_mode == "narrow" else None,
            "replication_search_budget_executed": int(len(jobs)) if replication_mode == "narrow" else None,
            "discovery_search_budget": discovery_search_budget,
            "cumulative_search_budget": int(len(jobs)),
            "cumulative_search_budget_disclosed": int(discovery_search_budget + len(jobs)),
            "selection": selection,
            "winner": selection,
            "val_eval_inside_mask_balanced_accuracy": val_eval_score,
            "masked_sample_size_gate": winner_gate,
            "contract_status": "PASS",
            "contract_reasons": [],
            "forbidden_interpretations": ["not_live_rule", "not_trading_candidate", "not_pnl", "not_pf"],
            "allowed_verdicts": list(ALLOWED_RICH_VERDICTS),
            "time_diagnostics": compute_narrow_time_diagnostics(row_frame),
        }
        if replication_mode == "narrow":
            if any(run.get("stage") == "targets" for run in failed_runs):
                summary["contract_status"] = "TARGET_CONTRACT_FAIL"
                summary["contract_reasons"] = ["target_construction_failed_after_preflight"]
            elif failed_runs:
                summary["contract_status"] = "MODEL_RUN_FAIL"
                summary["contract_reasons"] = ["model_fit_or_evaluation_failed"]
            summary["allowed_verdicts"] = [
                "DIRECTION_REPLICATION_SUPPORTED_RESEARCH_ONLY",
                "DIRECTION_REPLICATION_INCONCLUSIVE",
                "REJECT_DIRECTION_REPLICATION",
            ]
            summary["replication_summary"] = aggregate_narrow_replication(metric_frame, summary)
            summary["replication_verdict"] = narrow_replication_verdict(summary["replication_summary"])
        summary["elapsed_sec"] = float(time.time() - started)
        summary["started_at"] = progress["started_at"]
        summary["finished_at"] = progress["finished_at"]
        summary["verdict"] = (
            summary["replication_verdict"] if replication_mode == "narrow" else rich_direction_verdict(summary)
        )
        return summary

    def save_progress() -> None:
        if output_prefix is None:
            return
        metric_frame = pd.DataFrame(metric_rows) if metric_rows else _empty_metrics_frame()
        row_frame = pd.DataFrame(prediction_rows) if prediction_rows else _empty_rows_frame()
        summary = build_summary(metric_frame, row_frame)
        Path(output_prefix).parent.mkdir(parents=True, exist_ok=True)
        Path(f"{output_prefix}.json").write_text(
            json.dumps(_json_ready(summary), ensure_ascii=True, indent=2, allow_nan=True),
            encoding="utf-8",
        )
        metric_frame.to_csv(Path(f"{output_prefix}_metrics.csv"), index=False)
        row_frame.to_csv(Path(f"{output_prefix}_rows.csv"), index=False)

    heartbeat("start", 0, planned_search_budget, started)

    required_splits = ("train", "val_select", "val_eval", "low_n_disclosure")
    missing_splits = [split_name for split_name in required_splits if split_name not in splits]
    if missing_splits:
        raise ValueError(f"missing required rich direction splits: {missing_splits}")
    role_splits = {split_name: splits[split_name] for split_name in required_splits}
    heartbeat("preflight", 0, planned_search_budget, started)
    masked_splits = attach_frozen_mask_by_row_id(role_splits, scores)
    if replication_mode == "narrow":
        target_preflight = preflight_target_horizons(masked_splits, list(requested_horizons))
        executable_horizons = tuple(int(value) for value in target_preflight["executable_horizons"])
        config["executable_horizons"] = list(executable_horizons)
    else:
        executable_horizons = requested_horizons
    jobs = build_rich_direction_jobs(config)
    current_job_keys = {resume_key(job) for job in jobs}
    completed_keys = load_completed_keys(output_prefix, resume) if output_prefix is not None else set()
    completed_keys = completed_keys.intersection(current_job_keys)
    progress = build_initial_progress(len(jobs), requested_threads, effective_threads)
    progress["completed_keys"] = sorted(completed_keys)
    progress["done_runs"] = len(completed_keys)
    metric_rows: list[dict[str, object]] = []
    prediction_rows: list[dict[str, object]] = []
    failed_runs: list[dict[str, object]] = []
    feature_metadata: dict[str, object] = {}
    train_scope = training_scope_counts(masked_splits["train"])
    if resume and output_prefix is not None:
        metrics_path = Path(f"{output_prefix}_metrics.csv")
        rows_path = Path(f"{output_prefix}_rows.csv")
        json_path = Path(f"{output_prefix}.json")
        if metrics_path.exists():
            previous_metrics = pd.read_csv(metrics_path)
            if "resume_key" in previous_metrics.columns:
                previous_metrics = previous_metrics[
                    previous_metrics["resume_key"].astype(str).isin(current_job_keys)
                ]
            else:
                previous_metrics = previous_metrics.iloc[0:0]
            metric_rows = previous_metrics.to_dict("records")
        if rows_path.exists():
            previous_rows = pd.read_csv(rows_path)
            if "resume_key" in previous_rows.columns:
                previous_rows = previous_rows[
                    previous_rows["resume_key"].astype(str).isin(current_job_keys)
                ]
            else:
                previous_rows = previous_rows.iloc[0:0]
            prediction_rows = previous_rows.to_dict("records")
        if json_path.exists():
            previous = json.loads(json_path.read_text(encoding="utf-8"))
            run_records = [
                run
                for run in previous.get("runs", [])
                if str(run.get("resume_key", "")) in current_job_keys
            ]
            failed_runs = [
                run
                for run in previous.get("failed_runs", [])
                if str(run.get("resume_key", "")) in current_job_keys
            ]

    feature_cache: dict[str, dict[str, pd.DataFrame] | Exception] = {}
    target_cache: dict[int, dict[str, pd.DataFrame] | Exception] = {}

    for job in jobs:
        profile = str(job["profile"])
        horizon = int(job["horizon"])
        target_family = str(job["target_family"])
        model_key = str(job["model_key"])
        seed = int(job["seed"])
        if should_skip_job(job, completed_keys, resume):
            continue
        if profile not in feature_cache:
            try:
                feature_cache[profile] = build_rich_feature_frames(masked_splits, profile)
                feature_metadata[profile] = rich_feature_metadata_for_json()
            except Exception as exc:
                failed_runs.append(
                    {
                        "profile": profile,
                        "stage": "features",
                        "error": type(exc).__name__,
                        "message": str(exc),
                    }
                )
                feature_cache[profile] = exc
        if isinstance(feature_cache[profile], Exception):
            continue
        features_by_split = feature_cache[profile]

        if horizon not in target_cache:
            try:
                target_cache[horizon] = {
                    split_name: build_direction_targets(frame, horizon)
                    for split_name, frame in masked_splits.items()
                    if split_name in features_by_split
                }
            except Exception as exc:
                failed_runs.append(
                    {
                        "profile": profile,
                        "horizon": horizon,
                        "stage": "targets",
                        "error": type(exc).__name__,
                        "message": str(exc),
                    }
                )
                target_cache[horizon] = exc
        if isinstance(target_cache[horizon], Exception):
            continue
        targets_by_split = target_cache[horizon]
        train_targets = targets_by_split["train"].copy()
        train_targets["target_direction"] = _target_direction_for_family(train_targets, target_family)
        fit_result = fit_direction_models(
            features_by_split["train"],
            train_targets,
            {**config, "model_keys": [model_key], "threads": effective_threads, "seed": seed},
        )
        for failed in fit_result["failed_runs"]:
            failed_runs.append(
                {
                    "profile": profile,
                    "horizon": horizon,
                    "target_family": target_family,
                    "stage": "fit",
                    **failed,
                }
            )
        if not fit_result["models"]:
            continue

        for fitted_model_key, model in fit_result["models"].items():
            run_started = time.time()
            run_id = f"{profile}|S{seed}|H{horizon}|{target_family}|{fitted_model_key}"
            key = resume_key(job)
            heartbeat(f"run_start:{key}", int(progress["done_runs"]), len(jobs), started)
            run_context = {
                "run_id": run_id,
                "resume_key": key,
                "profile": profile,
                "horizon": horizon,
                "target_family": target_family,
                "model_key": fitted_model_key,
                "seed": seed,
            }
            for split_name in ("val_select", "val_eval", "low_n_disclosure"):
                if split_name not in features_by_split or split_name not in targets_by_split:
                    continue
                split_targets = targets_by_split[split_name].copy()
                split_targets["target_direction"] = _target_direction_for_family(split_targets, target_family)
                predictions = _model_prediction_direction(model, features_by_split[split_name])
                frozen = masked_splits[split_name]["frozen_selected"].astype(bool)
                evaluated = evaluate_direction_predictions(predictions, split_targets, frozen)
                gate_input = pd.DataFrame(
                    {
                        "split": [split_name] * len(split_targets),
                        "frozen_selected": frozen.to_numpy(dtype=bool),
                        "target_direction": split_targets["target_direction"].to_numpy(),
                    },
                    index=split_targets.index,
                )
                gate = masked_sample_size_gate(
                    gate_input,
                    split=split_name,
                    min_masked_rows=min_masked_rows,
                    min_active_sign_rows=min_active_sign_rows,
                )
                _append_metric_rows(metric_rows, run_context, split_name, evaluated, gate)

                for row_id, prediction in predictions.items():
                    row_payload = {
                        **run_context,
                        "split": split_name,
                        "row_id": int(row_id),
                        "prediction": int(prediction),
                        "target_direction": int(split_targets.loc[row_id, "target_direction"]),
                        "frozen_selected": bool(frozen.loc[row_id]),
                    }
                    if "time" in masked_splits[split_name].columns:
                        row_payload["time"] = str(masked_splits[split_name].loc[row_id, "time"])
                    prediction_rows.append(row_payload)
            run_elapsed = float(time.time() - run_started)
            completed_keys.add(key)
            progress["completed_keys"] = sorted(completed_keys)
            progress["done_runs"] = len(completed_keys)
            progress["elapsed_sec"] = float(time.time() - started)
            run_records.append(
                {
                    **run_context,
                    "status": "completed",
                    "started_at": dt.datetime.fromtimestamp(run_started, tz=dt.timezone.utc).isoformat(),
                    "finished_at": utc_now_iso(),
                    "elapsed_sec": run_elapsed,
                    "threading": model_thread_settings(str(fitted_model_key), effective_threads),
                }
            )
            save_progress()
            heartbeat(f"run_end:{key}", int(progress["done_runs"]), len(jobs), started)

    metrics = pd.DataFrame(metric_rows) if metric_rows else _empty_metrics_frame()
    rows = pd.DataFrame(prediction_rows) if prediction_rows else _empty_rows_frame()
    progress["finished_at"] = utc_now_iso()
    progress["elapsed_sec"] = float(time.time() - started)
    summary = build_summary(metrics, rows)
    return {"summary": summary, "metrics": metrics, "rows": rows}


def write_rich_direction_artifacts(
    summary: dict[str, object],
    metrics: pd.DataFrame,
    rows: pd.DataFrame,
    output_prefix: Path = DEFAULT_OUTPUT_PREFIX,
) -> None:
    output_prefix = Path(output_prefix)
    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    Path(f"{output_prefix}.json").write_text(
        json.dumps(_json_ready(summary), ensure_ascii=True, indent=2, allow_nan=True),
        encoding="utf-8",
    )
    metrics.to_csv(Path(f"{output_prefix}_metrics.csv"), index=False)
    rows.to_csv(Path(f"{output_prefix}_rows.csv"), index=False)


def run_rich_direction_cli(
    output_prefix: Path = DEFAULT_OUTPUT_PREFIX,
    freeze_scores_path: Path = DEFAULT_FREEZE_SCORES_PATH,
    config_overrides: dict[str, object] | None = None,
    resume: bool = True,
) -> dict[str, object]:
    cli_started = time.time()
    heartbeat("cli_start", 0, 0, cli_started)
    config = rich_direction_config()
    config.update(config_overrides or {})
    if not Path(freeze_scores_path).exists():
        started = time.time()
        progress = build_initial_progress(0, DEFAULT_THREADS, DEFAULT_THREADS)
        metrics = _empty_metrics_frame()
        rows = _empty_rows_frame()
        requested_horizons = [int(value) for value in config.get("target_horizons", RICH_TARGET_HORIZONS)]
        planned_jobs = build_rich_direction_jobs({**config, "target_horizons": requested_horizons})
        discovery_search_budget = 240 if str(config.get("replication_mode", "none")) == "narrow" else 0
        summary = {
            "schema_version": 1,
            "stage_status": "DIAGNOSTIC_ONLY",
            "replication_mode": str(config.get("replication_mode", "none")),
            "training_scope": config["training_scope"],
            "frozen_mask_usage": config["frozen_mask_usage"],
            "selection_metric": config["selection_metric"],
            "validation_roles": config["validation_roles"],
            "feature_profiles": list(config.get("feature_profiles", RICH_FEATURE_PROFILES)),
            "target_horizons": requested_horizons,
            "executable_horizons": requested_horizons,
            "target_families": list(config.get("target_families", RICH_TARGET_FAMILIES)),
            "model_keys": list(config.get("model_keys", RICH_MODEL_KEYS)),
            "replication_seeds": [int(value) for value in config.get("replication_seeds", [config.get("seed", DEFAULT_SEED)])],
            "primary_horizon": int(config.get("primary_horizon", 3)),
            "secondary_horizons": [int(value) for value in config.get("secondary_horizons", [6, 9])],
            "locked_test": "not_opened",
            "low_n_disclosure_used_for_selection": False,
            "selection": {"status": "NO_CANDIDATE", "selection_split": "val_select", "selection_slice": "frozen_selected"},
            "started_at": progress["started_at"],
            "finished_at": utc_now_iso(),
            "elapsed_sec": float(time.time() - started),
            "progress": progress,
            "contract_status": "ABORT_CONTRACT_FAIL",
            "contract_reasons": [f"freeze_scores_missing:{freeze_scores_path}"],
            "forbidden_interpretations": ["not_live_rule", "not_trading_candidate", "not_pnl", "not_pf"],
            "allowed_verdicts": list(ALLOWED_RICH_VERDICTS),
            "target_preflight": {
                "status": "NOT_RUN",
                "horizons": {},
                "executable_horizons": requested_horizons,
                "skipped_horizons": [],
            },
            "planned_search_budget": int(len(planned_jobs)),
            "executed_search_budget": 0,
            "replication_search_budget_planned": int(len(planned_jobs)) if str(config.get("replication_mode", "none")) == "narrow" else None,
            "replication_search_budget_executed": 0 if str(config.get("replication_mode", "none")) == "narrow" else None,
            "discovery_search_budget": discovery_search_budget,
            "cumulative_search_budget": 0,
            "cumulative_search_budget_disclosed": discovery_search_budget,
            "time_diagnostics": compute_narrow_time_diagnostics(rows),
        }
        if str(config.get("replication_mode", "none")) == "narrow":
            summary["allowed_verdicts"] = [
                "DIRECTION_REPLICATION_SUPPORTED_RESEARCH_ONLY",
                "DIRECTION_REPLICATION_INCONCLUSIVE",
                "REJECT_DIRECTION_REPLICATION",
            ]
            summary["replication_summary"] = aggregate_narrow_replication(metrics, summary)
            summary["replication_verdict"] = "DIRECTION_REPLICATION_INCONCLUSIVE"
            summary["verdict"] = summary["replication_verdict"]
        else:
            summary["verdict"] = rich_direction_verdict(summary)
        write_rich_direction_artifacts(summary, metrics, rows, output_prefix)
        return summary

    heartbeat("load_splits_start", 0, 0, cli_started)
    splits = amplitude.load_entry_based_splits()
    heartbeat("load_splits_end", 0, 0, cli_started)
    heartbeat("load_scores_start", 0, 0, cli_started)
    scores = pd.read_csv(freeze_scores_path)
    heartbeat("load_scores_end", 0, 0, cli_started)
    result = run_rich_direction_experiment(splits, scores, config_overrides, output_prefix=output_prefix, resume=resume)
    write_rich_direction_artifacts(result["summary"], result["metrics"], result["rows"], output_prefix)
    return result["summary"]


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Rich direction diagnostics inside frozen movement regime")
    parser.add_argument("--output-prefix", default=str(DEFAULT_OUTPUT_PREFIX))
    parser.add_argument("--freeze-scores", default=str(DEFAULT_FREEZE_SCORES_PATH))
    parser.add_argument("--profiles", nargs="+", default=list(RICH_FEATURE_PROFILES), choices=list(RICH_FEATURE_PROFILES))
    parser.add_argument("--horizons", nargs="+", type=int, default=None)
    parser.add_argument("--target-families", nargs="+", default=list(RICH_TARGET_FAMILIES), choices=list(RICH_TARGET_FAMILIES))
    parser.add_argument("--model-keys", nargs="+", default=list(RICH_MODEL_KEYS), choices=list(RICH_MODEL_KEYS))
    parser.add_argument("--replication-mode", choices=["none", "narrow"], default="none")
    parser.add_argument("--replication-seeds", nargs="+", type=int, default=None)
    parser.add_argument("--min-masked-rows", type=int, default=100)
    parser.add_argument("--min-active-sign-rows", type=int, default=30)
    parser.add_argument("--threads", type=int, default=DEFAULT_THREADS)
    parser.add_argument("--parallel-workers", type=int, default=1)
    parser.add_argument("--resume", dest="resume", action="store_true", default=True)
    parser.add_argument("--no-resume", dest="resume", action="store_false")
    return parser


def validate_horizon_args(replication_mode: str, horizons: tuple[int, ...] | list[int]) -> None:
    allowed = set(RICH_TARGET_HORIZONS)
    if replication_mode == "narrow":
        allowed = allowed.union(NARROW_REPLICATION_HORIZONS)
    invalid = sorted(set(int(value) for value in horizons).difference(allowed))
    if invalid:
        raise ValueError(f"unsupported horizons for {replication_mode}: {invalid}")


def config_from_args(args: argparse.Namespace) -> dict[str, object]:
    horizons = list(args.horizons) if args.horizons is not None else list(
        NARROW_REPLICATION_HORIZONS if args.replication_mode == "narrow" else RICH_TARGET_HORIZONS
    )
    validate_horizon_args(args.replication_mode, horizons)
    if args.replication_mode == "narrow":
        rejected_overrides = []
        if list(args.profiles) != list(RICH_FEATURE_PROFILES):
            rejected_overrides.append("--profiles")
        if list(args.target_families) != list(RICH_TARGET_FAMILIES):
            rejected_overrides.append("--target-families")
        if list(args.model_keys) != list(RICH_MODEL_KEYS):
            rejected_overrides.append("--model-keys")
        if rejected_overrides:
            raise ValueError(
                "narrow replication mode uses the pre-registered matrix; unsupported overrides: "
                + ", ".join(rejected_overrides)
            )
        config = narrow_replication_config()
        config["target_horizons"] = horizons
        config["threads"] = args.threads
        config["parallel_workers"] = args.parallel_workers
        config["min_masked_rows"] = args.min_masked_rows
        config["min_active_sign_rows"] = args.min_active_sign_rows
        if args.replication_seeds is not None:
            config["replication_seeds"] = list(args.replication_seeds)
        return config

    return {
        "replication_mode": args.replication_mode,
        "feature_profiles": args.profiles,
        "target_horizons": horizons,
        "target_families": args.target_families,
        "model_keys": args.model_keys,
        "min_masked_rows": args.min_masked_rows,
        "min_active_sign_rows": args.min_active_sign_rows,
        "threads": args.threads,
        "parallel_workers": args.parallel_workers,
    }


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    config = config_from_args(args)
    output_prefix = Path(args.output_prefix)
    if args.replication_mode == "narrow" and str(output_prefix) == str(DEFAULT_OUTPUT_PREFIX):
        output_prefix = Path(f"ML/reports/{NARROW_REPLICATION_OUTPUT_PREFIX}")
    summary = run_rich_direction_cli(
        output_prefix,
        Path(args.freeze_scores),
        config,
        resume=args.resume,
    )
    print(json.dumps({"verdict": summary["verdict"], "output_prefix": str(output_prefix)}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
