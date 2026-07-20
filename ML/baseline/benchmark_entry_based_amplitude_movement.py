# =============================================================================
# File: benchmark_entry_based_amplitude_movement.py
# Purpose: diagnostic-only helpers for entry-based amplitude movement targets
#   and evaluation metrics.
# Language: Python 3.10+
# Updated: 2026-07-07
# =============================================================================

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import sys
import time
from itertools import product
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.ensemble import ExtraTreesRegressor, HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.preprocessing import RobustScaler

from ML.baseline import benchmark_entry_based_next_open_closeout as closeout
from ML.baseline import benchmark_entry_based_powerful_tabular as powerful
from ML.baseline import benchmark_entry_based_sequence_transformer as sequence
from ML.baseline import benchmark_entry_based_updn_fractal_selection_ablation as selection_ablation

AMPLITUDE_MOVEMENT_SCHEMA_VERSION = 1
OUTPUT_PREFIX = "entry_based_amplitude_movement"
TARGET_HORIZONS = (3, 6, 12, 24)
MOVEMENT_QUANTILES = (0.80, 0.90, 0.95)
TOP_LIFT_FRACS = (0.05, 0.10, 0.20)
SEEDS = (42, 43, 44)

FORBIDDEN_INPUT_COLUMN_PATTERNS = (
    "up_",
    "dn_",
    "entry_up_",
    "entry_dn_",
    "entry_log_ratio_",
    "ret_",
    "fav_",
    "adv_",
    "target_",
    "label_",
    "outcome_",
)
FORBIDDEN_INPUT_COLUMN_EXACT = ("predict", "signal")

SIMPLE_PROFILES = (
    "atr_only",
    "time_only_clean",
    "time_plus_atr",
    "distance_to_level_pre_entry_only",
    "fractal_density_only",
    "simple_combined",
)
POST_ENTRY_DIAGNOSTIC_PROFILES = ("distance_to_entry_open_post_entry_diagnostic_only",)
SELECTION_FORBIDDEN_PROFILES = POST_ENTRY_DIAGNOSTIC_PROFILES

DECISION_PRICE_CANDIDATES = ("signal_price", "close", "Close", "bid_snapshot", "ask_snapshot")
ENTRY_PRICE_CANDIDATES = ("entry_open", "entry_price", "open")

TARGET_UNIT_CONTRACT = {
    "source_columns": "entry_up_H/entry_dn_H",
    "movement_formula": "max(entry_up_H, entry_dn_H)",
    "units": "same_as_entry_up_dn_targets",
    "unit_description": "same_as_entry_up_dn_targets movement magnitude contract",
    "normalization": "none",
    "source_contract_file": "docs/methodology/A8-feature-target-catalog.md",
    "source_function_or_builder": "build_movement_targets",
    "source_file": "ML/baseline/benchmark_entry_based_amplitude_movement.py",
    "target_columns": [
        "entry_movement_3",
        "entry_movement_6",
        "entry_movement_12",
        "entry_movement_24",
        "movement_flag_q80_3",
        "movement_flag_q90_3",
        "movement_flag_q95_3",
        "movement_flag_q80_6",
        "movement_flag_q90_6",
        "movement_flag_q95_6",
        "movement_flag_q80_12",
        "movement_flag_q90_12",
        "movement_flag_q95_12",
        "movement_flag_q80_24",
        "movement_flag_q90_24",
        "movement_flag_q95_24",
    ],
    "verdict": "PASS",
}

TARGET_CONTRACT = {
    "target_family": "entry_movement",
    "movement_formula": "max(entry_up_H, entry_dn_H)",
    "threshold_source_split": "train",
    "threshold_quantiles": [float(quantile) for quantile in MOVEMENT_QUANTILES],
    "target_columns_path": "target_unit_contract.target_columns",
    "status": "PASS",
}

SELECTION_POLICY = {
    "winner_metric": "val_select",
    "winner_unit": "seed_aggregate",
    "val_eval": "check_only",
    "low_n_disclosure_2026": "disclosure_only",
    "locked_test": "not_opened",
    "direction_selection": "forbidden",
    "decision_time": "pre_entry_decision",
}

NORMALIZATION_CONTRACT = {
    "fit_split": "train",
    "validation_splits_do_not_fit": ("val_select", "val_eval", "low_n_disclosure"),
    "feature_scaler": "RobustScaler",
    "target_scaler": "none",
    "input_and_target_scalers_separate": True,
}

ALLOWED_VERDICTS = {
    "AMPLITUDE_EXPLAINED_BY_SIMPLE_BASELINES",
    "MOVEMENT_REGIME_TRACE_FOUND",
    "REJECT_MOVEMENT_REGIME",
    "ABORT_CONTRACT_FAIL",
}
FORBIDDEN_VERDICTS = {"CANDIDATE", "FROZEN", "READY_FOR_LOCKED_TEST", "DIRECTION_FOUND", "TRADING_RULE_FOUND"}

PROFILE_KEYS = (
    "atr_only",
    "time_only_clean",
    "time_plus_atr",
    "distance_to_level_pre_entry_only",
    "fractal_density_only",
    "simple_combined",
    "distance_to_entry_open_post_entry_diagnostic_only",
    "nearest_k60_tabular",
    "nearest_k80_tabular",
    "nearest_k60_no_price_coord_tabular",
    "nearest_k80_no_price_coord_tabular",
    "nearest_k60_sequence_flat",
    "nearest_k80_sequence_flat",
    "nearest_k60_no_time_sequence_flat",
    "nearest_k60_no_price_coord_sequence_flat",
)
MODEL_KEYS = ("ridge_regression", "hist_gradient_boosting", "extra_trees_small")
SIMPLE_BASELINE_PROFILES = {
    "atr_only",
    "time_only_clean",
    "time_plus_atr",
    "distance_to_level_pre_entry_only",
    "fractal_density_only",
    "simple_combined",
}

REPORT_JSON_PATH = Path(f"ML/reports/{OUTPUT_PREFIX}.json")
REPORT_METRICS_PATH = Path(f"ML/reports/{OUTPUT_PREFIX}_metrics.csv")
REPORT_SEED_AGGREGATE_PATH = Path(f"ML/reports/{OUTPUT_PREFIX}_seed_aggregate.csv")
REPORT_QUANTILES_PATH = Path(f"ML/reports/{OUTPUT_PREFIX}_quantiles.csv")
REPORT_YEARLY_PATH = Path(f"ML/reports/{OUTPUT_PREFIX}_yearly.csv")
REPORT_TARGET_DISTRIBUTION_PATH = Path(f"ML/reports/{OUTPUT_PREFIX}_target_distribution.csv")
REPORT_FEATURE_AUDIT_PATH = Path(f"ML/reports/{OUTPUT_PREFIX}_feature_audit.csv")
REPORT_ROWS_PATH = Path(f"ML/reports/{OUTPUT_PREFIX}_rows.csv")
REPORT_LOG_PATH = Path(f"ML/reports/{OUTPUT_PREFIX}_run.log")

TIME_FEATURE_NAMES = ("hour_sin", "hour_cos", "dow_sin", "dow_cos")
PRICE_COORD_FEATURE_NAMES = ("price_coord_atr", "abs_price_coord_atr", "dir_price_coord_atr")


def _required_entry_columns() -> list[str]:
    return [f"entry_{side}_{horizon}" for horizon in TARGET_HORIZONS for side in ("up", "dn")]


def build_movement_targets(
    frame: pd.DataFrame,
    train_thresholds: dict[str, float] | None = None,
) -> tuple[pd.DataFrame, dict[str, float]]:
    missing = [column for column in _required_entry_columns() if column not in frame.columns]
    if missing:
        raise ValueError(f"Missing movement source columns: {missing}")

    thresholds = dict(train_thresholds or {})
    if train_thresholds is not None:
        missing_thresholds = [
            f"q{int(round(quantile * 100))}_{horizon}"
            for horizon in TARGET_HORIZONS
            for quantile in MOVEMENT_QUANTILES
            if f"q{int(round(quantile * 100))}_{horizon}" not in thresholds
        ]
        if missing_thresholds:
            raise ValueError(f"Missing train threshold keys: {missing_thresholds}")

    targets = pd.DataFrame(index=frame.index)

    for horizon in TARGET_HORIZONS:
        movement = np.maximum(
            pd.to_numeric(frame[f"entry_up_{horizon}"], errors="coerce").to_numpy(dtype=float),
            pd.to_numeric(frame[f"entry_dn_{horizon}"], errors="coerce").to_numpy(dtype=float),
        )
        targets[f"entry_movement_{horizon}"] = movement
        for quantile in MOVEMENT_QUANTILES:
            q_int = int(round(quantile * 100))
            threshold_key = f"q{q_int}_{horizon}"
            if threshold_key not in thresholds:
                thresholds[threshold_key] = float(np.quantile(movement, quantile))
            targets[f"movement_flag_q{q_int}_{horizon}"] = (movement >= thresholds[threshold_key]).astype(int)

    return targets, thresholds


def compute_spearman(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    valid = np.isfinite(y_true) & np.isfinite(y_pred)
    y_true = y_true[valid]
    y_pred = y_pred[valid]
    if len(y_true) < 3:
        return float("nan")
    value = spearmanr(y_true, y_pred).correlation
    return float(value) if value is not None and np.isfinite(value) else float("nan")


def _single_quantile_lift(y_true: np.ndarray, y_pred: np.ndarray, frac: float) -> dict[str, float]:
    if len(y_true) == 0:
        return {
            "top_frac": float(frac),
            "top_n": 0.0,
            "rest_n": 0.0,
            "top_mean": float("nan"),
            "rest_mean": float("nan"),
            "lift": float("nan"),
        }

    top_n = max(1, int(math.ceil(len(y_true) * frac)))
    order = np.argsort(y_pred)[::-1]
    top_idx = order[:top_n]
    rest_idx = order[top_n:]
    top_mean = float(np.mean(y_true[top_idx]))
    rest_mean = float(np.mean(y_true[rest_idx])) if len(rest_idx) else float("nan")
    if rest_mean == 0.0 or not np.isfinite(rest_mean):
        lift = float("nan")
    else:
        lift = float(top_mean / rest_mean)
    return {
        "top_frac": float(frac),
        "top_n": float(top_n),
        "rest_n": float(len(rest_idx)),
        "top_mean": top_mean,
        "rest_mean": rest_mean,
        "lift": lift,
    }


def _block_bootstrap_lift_ci(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    frac: float,
    block_size: int = 20,
    rounds: int = 200,
    seed: int = 42,
) -> tuple[float, float, float]:
    if len(y_true) < block_size * 2:
        return (float("nan"), float("nan"), float("nan"))

    rng = np.random.default_rng(seed)
    starts = np.arange(0, len(y_true), block_size)
    lifts: list[float] = []
    for _ in range(rounds):
        sampled_parts = []
        for start in rng.choice(starts, size=len(starts), replace=True):
            sampled_parts.append(np.arange(start, min(start + block_size, len(y_true))))
        sampled_idx = np.concatenate(sampled_parts)
        row = _single_quantile_lift(y_true[sampled_idx], y_pred[sampled_idx], frac)
        if np.isfinite(row["lift"]):
            lifts.append(float(row["lift"]))

    if not lifts:
        return (float("nan"), float("nan"), float("nan"))
    return tuple(float(value) for value in np.quantile(lifts, [0.05, 0.50, 0.95]))


def compute_quantile_lift(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    top_fracs: tuple[float, ...] = TOP_LIFT_FRACS,
) -> list[dict[str, float]]:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    valid = np.isfinite(y_true) & np.isfinite(y_pred)
    y_true = y_true[valid]
    y_pred = y_pred[valid]

    rows: list[dict[str, float]] = []
    for frac in top_fracs:
        row = _single_quantile_lift(y_true, y_pred, frac)
        ci_p05, ci_p50, ci_p95 = _block_bootstrap_lift_ci(y_true, y_pred, frac)
        row.update(
            {
                "lift_ci_p05": ci_p05,
                "lift_ci_p50": ci_p50,
                "lift_ci_p95": ci_p95,
            }
        )
        rows.append(row)
    return rows


def compute_target_distribution(targets_by_split: dict[str, pd.DataFrame]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for split_name, targets in targets_by_split.items():
        for horizon in TARGET_HORIZONS:
            column = f"entry_movement_{horizon}"
            if column not in targets.columns:
                continue
            values = pd.to_numeric(targets[column], errors="coerce").dropna().to_numpy(dtype=float)
            rows.append(
                {
                    "split": split_name,
                    "horizon": horizon,
                    "n": int(len(values)),
                    "p50": float(np.quantile(values, 0.50)) if len(values) else float("nan"),
                    "p80": float(np.quantile(values, 0.80)) if len(values) else float("nan"),
                    "p90": float(np.quantile(values, 0.90)) if len(values) else float("nan"),
                    "p95": float(np.quantile(values, 0.95)) if len(values) else float("nan"),
                }
            )
    return rows


def is_forbidden_input_column(column: str) -> bool:
    return column in FORBIDDEN_INPUT_COLUMN_EXACT or any(column.startswith(pattern) for pattern in FORBIDDEN_INPUT_COLUMN_PATTERNS)


def _calendar_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if "time" in frame.columns:
        timestamps = pd.to_datetime(frame["time"], errors="coerce")
    else:
        timestamps = pd.Series(pd.NaT, index=frame.index, dtype="datetime64[ns]")
    hour = timestamps.dt.hour.fillna(0).astype(float)
    dow = timestamps.dt.dayofweek.fillna(0).astype(float)
    return pd.DataFrame(
        {
            "hour_sin": np.sin(2.0 * np.pi * hour / 24.0),
            "hour_cos": np.cos(2.0 * np.pi * hour / 24.0),
            "dow_sin": np.sin(2.0 * np.pi * dow / 7.0),
            "dow_cos": np.cos(2.0 * np.pi * dow / 7.0),
        },
        index=frame.index,
    )


def _parse_fractal_values(raw: object) -> list[float] | None:
    return sequence._parse_fractal(raw)


def _decision_price_series(frame: pd.DataFrame) -> tuple[pd.Series | None, str | None]:
    for column in DECISION_PRICE_CANDIDATES:
        if column in frame.columns:
            return pd.to_numeric(frame[column], errors="coerce").astype(float), column
    return None, None


def _entry_price_series(frame: pd.DataFrame) -> tuple[pd.Series | None, str | None]:
    for column in ENTRY_PRICE_CANDIDATES:
        if column in frame.columns:
            return pd.to_numeric(frame[column], errors="coerce").astype(float), column
    return None, None


def _fractal0_price(frame: pd.DataFrame) -> pd.Series:
    prices: list[float] = []
    for raw in frame.get("fractal0", pd.Series([None] * len(frame), index=frame.index)):
        values = _parse_fractal_values(raw)
        prices.append(float(values[1]) if values is not None and len(values) > 1 else float("nan"))
    return pd.Series(prices, index=frame.index, dtype=float)


def _atr_series(frame: pd.DataFrame) -> pd.Series:
    return pd.to_numeric(frame.get("ATR"), errors="coerce").astype(float)


def _build_atr_only_frame(frame: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({"ATR": _atr_series(frame)}, index=frame.index)


def _build_pre_entry_distance_frame(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    decision_price, source = _decision_price_series(frame)
    if decision_price is None:
        return pd.DataFrame(index=frame.index), {
            "profile": "distance_to_level_pre_entry_only",
            "status": "SKIPPED_NO_DECISION_PRICE",
            "available_at_decision_time": False,
            "feature_contract_verdict": "SKIPPED",
            "selection_eligible": False,
            "post_entry_diagnostic_only": False,
            "used_entry_open_as_input": False,
        }

    f0_price = _fractal0_price(frame)
    atr = _atr_series(frame).replace(0.0, np.nan)
    distance = (f0_price - decision_price).abs() / atr
    features = pd.DataFrame({"distance_to_fractal0_pre_entry_atr": distance.fillna(0.0)}, index=frame.index)
    return features, {
        "profile": "distance_to_level_pre_entry_only",
        "status": "PASS",
        "distance_price_source": source,
        "available_at_decision_time": True,
        "feature_contract_verdict": "PASS",
        "selection_eligible": True,
        "post_entry_diagnostic_only": False,
        "used_entry_open_as_input": False,
    }


def _build_post_entry_distance_frame(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    entry_price, source = _entry_price_series(frame)
    if entry_price is None:
        return pd.DataFrame(index=frame.index), {
            "profile": "distance_to_entry_open_post_entry_diagnostic_only",
            "status": "SKIPPED_NO_ENTRY_PRICE",
            "available_at_decision_time": False,
            "feature_contract_verdict": "SKIPPED",
            "selection_eligible": False,
            "post_entry_diagnostic_only": True,
            "used_entry_open_as_input": False,
        }

    f0_price = _fractal0_price(frame)
    atr = _atr_series(frame).replace(0.0, np.nan)
    distance = (f0_price - entry_price).abs() / atr
    features = pd.DataFrame({"distance_to_entry_open_atr": distance.fillna(0.0)}, index=frame.index)
    return features, {
        "profile": "distance_to_entry_open_post_entry_diagnostic_only",
        "status": "PASS",
        "distance_price_source": source,
        "available_at_decision_time": False,
        "feature_contract_verdict": "POST_ENTRY_DIAGNOSTIC_ONLY",
        "selection_eligible": False,
        "post_entry_diagnostic_only": True,
        "used_entry_open_as_input": True,
    }


def _build_fractal_density_frame(frame: pd.DataFrame) -> pd.DataFrame:
    f0_price = _fractal0_price(frame)
    atr = _atr_series(frame).replace(0.0, np.nan)
    eps = 1e-12
    rows: list[dict[str, float]] = []
    for idx, row in frame.iterrows():
        distances: list[float] = []
        f0 = f0_price.loc[idx]
        row_atr = atr.loc[idx]
        if not np.isfinite(f0) or not np.isfinite(row_atr):
            rows.append(
                {
                    "valid_fractal_count": 0,
                    "count_within_1atr": 0,
                    "count_within_2atr": 0,
                    "count_within_5atr": 0,
                    "count_within_10atr": 0,
                    "nearest_distance_atr": 0.0,
                }
            )
            continue
        for token_idx in range(1, 100):
            values = _parse_fractal_values(row.get(f"fractal{token_idx}"))
            if values is None or len(values) <= 1:
                continue
            price = float(values[1])
            if not np.isfinite(price):
                continue
            distances.append(abs(price - f0) / row_atr)
        arr = np.asarray(distances, dtype=float)
        rows.append(
            {
                "valid_fractal_count": int(len(arr)),
                "count_within_1atr": int(np.sum(arr <= 1.0 + eps)) if len(arr) else 0,
                "count_within_2atr": int(np.sum(arr <= 2.0 + eps)) if len(arr) else 0,
                "count_within_5atr": int(np.sum(arr <= 5.0 + eps)) if len(arr) else 0,
                "count_within_10atr": int(np.sum(arr <= 10.0 + eps)) if len(arr) else 0,
                "nearest_distance_atr": float(np.round(np.min(arr), 12)) if len(arr) else 0.0,
            }
        )
    return pd.DataFrame(rows, index=frame.index)


def build_simple_feature_frame(frame: pd.DataFrame, profile: str) -> tuple[pd.DataFrame, dict[str, Any]]:
    meta: dict[str, Any] = {"profile": profile}
    if profile == "atr_only":
        features = _build_atr_only_frame(frame)
        meta.update(
            {
                "available_at_decision_time": True,
                "feature_contract_verdict": "PASS",
                "selection_eligible": True,
                "post_entry_diagnostic_only": False,
            }
        )
        return features, meta

    if profile == "time_only_clean":
        features = _calendar_frame(frame)
        meta.update(
            {
                "available_at_decision_time": True,
                "feature_contract_verdict": "PASS",
                "selection_eligible": True,
                "post_entry_diagnostic_only": False,
            }
        )
        return features, meta

    if profile == "time_plus_atr":
        features = pd.concat([_build_atr_only_frame(frame), _calendar_frame(frame)], axis=1)
        meta.update(
            {
                "available_at_decision_time": True,
                "feature_contract_verdict": "PASS",
                "selection_eligible": True,
                "post_entry_diagnostic_only": False,
            }
        )
        return features, meta

    if profile == "distance_to_level_pre_entry_only":
        features, distance_meta = _build_pre_entry_distance_frame(frame)
        meta.update(distance_meta)
        return features, meta

    if profile == "fractal_density_only":
        features = _build_fractal_density_frame(frame)
        meta.update(
            {
                "available_at_decision_time": True,
                "feature_contract_verdict": "PASS",
                "selection_eligible": True,
                "post_entry_diagnostic_only": False,
                "excludes_fractal0": True,
            }
        )
        return features, meta

    if profile == "simple_combined":
        parts: list[pd.DataFrame] = []
        component_profiles: list[str] = []
        child_profiles: list[dict[str, Any]] = []
        for child_profile in ("atr_only", "time_only_clean", "distance_to_level_pre_entry_only", "fractal_density_only"):
            child_features, child_meta = build_simple_feature_frame(frame, child_profile)
            child_audit = dict(child_meta)
            child_audit.setdefault("status", "PASS" if not child_features.empty else "SKIPPED")
            child_audit["selected"] = not child_features.empty
            child_audit["feature_count"] = int(child_features.shape[1])
            child_profiles.append(child_audit)
            if child_features.empty:
                continue
            parts.append(child_features)
            component_profiles.append(child_profile)
            meta[f"{child_profile}_status"] = child_meta.get("status", "PASS")
        features = pd.concat(parts, axis=1) if parts else pd.DataFrame(index=frame.index)
        meta.update(
            {
                "available_at_decision_time": True,
                "feature_contract_verdict": "PASS",
                "selection_eligible": True,
                "post_entry_diagnostic_only": False,
                "components": component_profiles,
                "child_profiles": child_profiles,
            }
        )
        return features, meta

    if profile == "distance_to_entry_open_post_entry_diagnostic_only":
        features, distance_meta = _build_post_entry_distance_frame(frame)
        meta.update(distance_meta)
        return features, meta

    raise ValueError(f"Unknown simple profile: {profile}")


def _drop_feature_families(frame: pd.DataFrame, remove_time: bool = False, remove_price_coord: bool = False) -> pd.DataFrame:
    keep_columns: list[str] = []
    for column in frame.columns:
        if remove_time and any(column.endswith(name) or column == name for name in TIME_FEATURE_NAMES):
            continue
        if remove_price_coord and any(name in column for name in PRICE_COORD_FEATURE_NAMES):
            continue
        keep_columns.append(column)
    return frame.loc[:, keep_columns].copy()


def _build_tabular_representation_frame(frame: pd.DataFrame, profile: str) -> tuple[pd.DataFrame, dict[str, Any]]:
    profile_map = {
        "nearest_k60_tabular": ("nearest_k60", False),
        "nearest_k80_tabular": ("nearest_k80", False),
        "nearest_k60_no_price_coord_tabular": ("nearest_k60", True),
        "nearest_k80_no_price_coord_tabular": ("nearest_k80", True),
    }
    representation_key, remove_price_coord = profile_map[profile]
    features, metadata = selection_ablation.build_representation_features(frame, representation_key)
    filtered = _drop_feature_families(features, remove_price_coord=remove_price_coord)
    return filtered, {
        "profile": profile,
        "status": "PASS",
        "available_at_decision_time": True,
        "feature_contract_verdict": "PASS",
        "selection_eligible": True,
        "post_entry_diagnostic_only": False,
        "representation_key": representation_key,
        "remove_price_coord": remove_price_coord,
        "source_feature_count": int(features.shape[1]),
        "feature_count": int(filtered.shape[1]),
        "coverage_summary": metadata.get("coverage_summary"),
    }


def _flatten_sequence_tensor(
    frame_index: pd.Index,
    tensor: Any,
    remove_time: bool = False,
    remove_price_coord: bool = False,
) -> pd.DataFrame:
    keep_feature_idx = [
        idx
        for idx, name in enumerate(tensor.feature_names)
        if not (remove_time and name in TIME_FEATURE_NAMES) and not (remove_price_coord and name in PRICE_COORD_FEATURE_NAMES)
    ]
    kept_names = [str(tensor.feature_names[idx]) for idx in keep_feature_idx]
    selected_tokens = tensor.tokens[:, :, keep_feature_idx]
    token_columns = [f"token_{slot:02d}_{name}" for slot in range(selected_tokens.shape[1]) for name in kept_names]
    flat_tokens = selected_tokens.reshape(len(frame_index), -1)
    mask_columns = [f"token_{slot:02d}_mask" for slot in range(tensor.mask.shape[1])]
    flat_mask = tensor.mask.astype(np.float32)
    data = np.concatenate([flat_tokens, flat_mask], axis=1)
    return pd.DataFrame(data, index=frame_index, columns=token_columns + mask_columns)


def _build_sequence_flat_frame(frame: pd.DataFrame, profile: str) -> tuple[pd.DataFrame, dict[str, Any]]:
    profile_map = {
        "nearest_k60_sequence_flat": ("nearest_k60_sequence", False, False),
        "nearest_k80_sequence_flat": ("nearest_k80_sequence", False, False),
        "nearest_k60_no_time_sequence_flat": ("nearest_k60_sequence", True, False),
        "nearest_k60_no_price_coord_sequence_flat": ("nearest_k60_sequence", False, True),
    }
    representation_key, remove_time, remove_price_coord = profile_map[profile]
    tensor = sequence.build_sequence_tensor(frame, representation_key)
    filtered = _flatten_sequence_tensor(
        frame.index,
        tensor,
        remove_time=remove_time,
        remove_price_coord=remove_price_coord,
    )
    return filtered, {
        "profile": profile,
        "status": "PASS",
        "available_at_decision_time": True,
        "feature_contract_verdict": "PASS",
        "selection_eligible": True,
        "post_entry_diagnostic_only": False,
        "representation_key": representation_key,
        "remove_time": remove_time,
        "remove_price_coord": remove_price_coord,
        "source_feature_count": int(len(tensor.feature_names) * tensor.tokens.shape[1] + tensor.mask.shape[1]),
        "feature_count": int(filtered.shape[1]),
    }


def build_feature_frame(frame: pd.DataFrame, profile: str) -> tuple[pd.DataFrame, dict[str, Any]]:
    if profile in SIMPLE_PROFILES or profile in POST_ENTRY_DIAGNOSTIC_PROFILES:
        return build_simple_feature_frame(frame, profile)
    if profile.endswith("_tabular"):
        return _build_tabular_representation_frame(frame, profile)
    if profile.endswith("_sequence_flat"):
        return _build_sequence_flat_frame(frame, profile)
    raise ValueError(f"Unknown profile: {profile}")


def build_feature_profile_with_metadata(
    splits: dict[str, pd.DataFrame],
    profile: str,
) -> dict[str, dict[str, Any]]:
    features_by_split: dict[str, pd.DataFrame] = {}
    metadata_by_split: dict[str, dict[str, Any]] = {}
    for split_name, frame in splits.items():
        features, metadata = build_feature_frame(frame, profile)
        features_by_split[split_name] = features
        metadata_by_split[split_name] = metadata
    return {"features": features_by_split, "metadata": metadata_by_split}


def build_feature_profile(splits: dict[str, pd.DataFrame], profile: str) -> dict[str, pd.DataFrame]:
    return build_feature_profile_with_metadata(splits, profile)["features"]


def build_run_config() -> dict[str, Any]:
    return {
        "schema_version": AMPLITUDE_MOVEMENT_SCHEMA_VERSION,
        "profiles": PROFILE_KEYS,
        "models": MODEL_KEYS,
        "seeds": SEEDS,
        "horizons": TARGET_HORIZONS,
        "target_family": "entry_movement",
        "target_unit_contract": TARGET_UNIT_CONTRACT,
        "selection_policy": SELECTION_POLICY,
        "split_policy": {
            "train": "<=2020",
            "validation": "2021-2025 split into val_select/val_eval",
            "low_n_disclosure": "2026 disclosure_only",
            "locked_test": "not_opened",
            "embargo_hours": max(TARGET_HORIZONS),
        },
        "output_prefix": OUTPUT_PREFIX,
    }


def compute_config_hash(config: dict[str, Any]) -> str:
    payload = json.dumps(config, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def ensure_allowed_verdict(verdict: str) -> str:
    verdict = str(verdict)
    if verdict in FORBIDDEN_VERDICTS:
        raise ValueError(f"Forbidden verdict: {verdict}")
    if verdict not in ALLOWED_VERDICTS:
        raise ValueError(f"Unknown verdict: {verdict}")
    return verdict


def decide_verdict(report: dict[str, Any]) -> str:
    audit = report.get("feature_audit", {})
    if audit.get("status") == "ERROR" or audit.get("errors"):
        return ensure_allowed_verdict("ABORT_CONTRACT_FAIL")
    target_contract = report.get("target_unit_contract", {})
    if target_contract.get("verdict", "PASS") != "PASS":
        return ensure_allowed_verdict("ABORT_CONTRACT_FAIL")
    top_level_target_contract = report.get("target_contract", {})
    if top_level_target_contract.get("verdict", "PASS") != "PASS":
        return ensure_allowed_verdict("ABORT_CONTRACT_FAIL")
    aggregates = [
        row
        for row in report.get("seed_aggregate", [])
        if row.get("target_family") == "entry_movement"
        and bool(row.get("selection_eligible", True))
        and not bool(row.get("post_entry_diagnostic_only", False))
    ]
    if not aggregates:
        return ensure_allowed_verdict("REJECT_MOVEMENT_REGIME")
    best = max(aggregates, key=lambda row: float(row.get("val_select_spearman_median", float("-inf"))))
    select = float(best.get("val_select_spearman_median", float("nan")))
    eval_score = float(best.get("val_eval_spearman_median", float("nan")))
    top10_select = float(best.get("val_select_top10_lift_median", float("nan")))
    top10_eval = float(best.get("val_eval_top10_lift_median", float("nan")))
    top10_eval_ci_p05 = float(best.get("val_eval_top10_lift_ci_p05", float("nan")))
    deterministic = bool(best.get("deterministic", False))
    seed_gate = deterministic or (
        int(best.get("n_seeds", 0)) == 3
        and int(best.get("val_eval_positive_seed_count", 0)) >= 2
        and int(best.get("val_eval_top10_lift_pass_seed_count", 0)) >= 2
    )
    beats_simple = bool(best.get("beats_best_simple_val_select", False)) and bool(best.get("beats_best_simple_val_eval", False))
    movement_gate = (
        select >= 0.25
        and eval_score >= 0.15
        and top10_select >= 1.20
        and top10_eval >= 1.10
        and top10_eval_ci_p05 >= 1.00
        and seed_gate
        and bool(best.get("yearly_check_pass", False))
    )
    if movement_gate and beats_simple:
        return ensure_allowed_verdict("MOVEMENT_REGIME_TRACE_FOUND")
    if movement_gate and not beats_simple:
        return ensure_allowed_verdict("AMPLITUDE_EXPLAINED_BY_SIMPLE_BASELINES")
    return ensure_allowed_verdict("REJECT_MOVEMENT_REGIME")


def seeds_for_model(model_key: str) -> tuple[int, ...]:
    if is_model_deterministic(model_key):
        return (SEEDS[0],)
    return SEEDS


def enumerate_jobs() -> list[dict[str, Any]]:
    jobs: list[dict[str, Any]] = []
    for profile, model_key, horizon in product(PROFILE_KEYS, MODEL_KEYS, TARGET_HORIZONS):
        if model_key == "ridge_regression" and profile not in SIMPLE_PROFILES:
            continue
        for seed in seeds_for_model(model_key):
            jobs.append(
                {
                    "profile": profile,
                    "model_key": model_key,
                    "seed": seed,
                    "horizon": horizon,
                    "target_family": "entry_movement",
                }
            )
    return jobs


def model_thread_settings(model_key: str, threads: int) -> dict[str, Any]:
    if model_key == "extra_trees_small":
        return {"requested_threads": int(threads), "n_jobs": int(threads), "thread_control": "n_jobs"}
    if model_key == "hist_gradient_boosting":
        return {
            "requested_threads": int(threads),
            "n_jobs": None,
            "thread_control": "not_supported_by_estimator",
        }
    return {"requested_threads": int(threads), "n_jobs": None, "thread_control": "single_thread_or_external_blas"}


def make_model(model_key: str, seed: int, threads: int):
    if model_key == "ridge_regression":
        return Ridge(alpha=1.0)
    if model_key == "hist_gradient_boosting":
        return HistGradientBoostingRegressor(
            max_iter=250,
            learning_rate=0.04,
            l2_regularization=0.05,
            random_state=seed,
        )
    if model_key == "extra_trees_small":
        thread_settings = model_thread_settings(model_key, threads)
        return ExtraTreesRegressor(
            n_estimators=48,
            max_depth=8,
            min_samples_leaf=20,
            max_features=0.5,
            random_state=seed,
            n_jobs=int(thread_settings["n_jobs"]),
        )
    raise ValueError(f"Unknown model_key: {model_key}")


def is_model_deterministic(model_key: str) -> bool:
    return model_key == "ridge_regression"


def resolve_effective_threads(requested_threads: int | None, parallel_workers: int = 1) -> int:
    default_threads = 24
    threads = int(requested_threads or default_threads)
    if parallel_workers > 1:
        threads = max(1, threads // parallel_workers)
    return max(1, threads)


def resume_key(job: dict[str, Any]) -> str:
    return f"{job['profile']}/{job['model_key']}/{job['seed']}/{job['horizon']}/{job['target_family']}"


def should_skip_job(job: dict[str, Any], completed_keys: set[str], resume: bool) -> bool:
    return bool(resume and resume_key(job) in completed_keys)


def build_initial_progress(total_runs: int, requested_threads: int, effective_threads: int) -> dict[str, Any]:
    return {
        "started_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "finished_at": None,
        "elapsed_sec": 0.0,
        "done_runs": 0,
        "total_runs": int(total_runs),
        "requested_threads": int(requested_threads),
        "effective_threads": int(effective_threads),
        "completed_keys": [],
    }


def load_entry_based_splits() -> dict[str, pd.DataFrame]:
    old_splits = powerful._add_h24_targets_if_missing(closeout.base.load_entry_based_splits(target_mode="rebuilt"))
    splits = powerful._convert_splits(old_splits)
    role_splits = powerful._split_validation_roles(splits["validation"])
    splits.update(role_splits)
    return powerful.apply_horizon_embargo(splits, max_horizon_hours=max(TARGET_HORIZONS))


def _float_values(rows: list[dict[str, Any]], key: str) -> np.ndarray:
    values = [float(row[key]) for row in rows if key in row and np.isfinite(float(row[key]))]
    return np.asarray(values, dtype=float)


def _nanmin_or_nan(values: list[object]) -> float:
    numeric = [float(value) for value in values if value is not None and np.isfinite(float(value))]
    return float(np.min(numeric)) if numeric else float("nan")


def aggregate_seed_metrics(metric_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, int, str], list[dict[str, Any]]] = {}
    for row in metric_rows:
        if row.get("status") != "completed":
            continue
        key = (str(row["profile"]), str(row["model_key"]), int(row["horizon"]), str(row["target_family"]))
        grouped.setdefault(key, []).append(row)

    aggregates: list[dict[str, Any]] = []
    by_horizon_simple: dict[int, dict[str, Any]] = {}
    for (profile, model_key, horizon, target_family), rows in grouped.items():
        val_select = _float_values(rows, "val_select_spearman")
        val_eval = _float_values(rows, "val_eval_spearman")
        select_lift = _float_values(rows, "val_select_top10_lift")
        eval_lift = _float_values(rows, "val_eval_top10_lift")
        deterministic = all(bool(row.get("deterministic", False)) for row in rows)
        aggregate = {
            "profile": profile,
            "model_key": model_key,
            "horizon": horizon,
            "target_family": target_family,
            "deterministic": deterministic,
            "n_seeds": int(len({row.get("seed") for row in rows})),
            "val_select_spearman_median": float(np.median(val_select)) if len(val_select) else float("nan"),
            "val_select_spearman_mean": float(np.mean(val_select)) if len(val_select) else float("nan"),
            "val_select_spearman_std": float(np.std(val_select, ddof=0)) if len(val_select) else float("nan"),
            "val_select_spearman_min": float(np.min(val_select)) if len(val_select) else float("nan"),
            "val_select_spearman_max": float(np.max(val_select)) if len(val_select) else float("nan"),
            "val_eval_spearman_median": float(np.median(val_eval)) if len(val_eval) else float("nan"),
            "val_eval_spearman_mean": float(np.mean(val_eval)) if len(val_eval) else float("nan"),
            "val_eval_spearman_std": float(np.std(val_eval, ddof=0)) if len(val_eval) else float("nan"),
            "val_eval_spearman_min": float(np.min(val_eval)) if len(val_eval) else float("nan"),
            "val_eval_spearman_max": float(np.max(val_eval)) if len(val_eval) else float("nan"),
            "val_eval_positive_seed_count": int(np.sum(val_eval > 0.0)) if len(val_eval) else 0,
            "val_select_top10_lift_median": float(np.median(select_lift)) if len(select_lift) else float("nan"),
            "val_eval_top10_lift_median": float(np.median(eval_lift)) if len(eval_lift) else float("nan"),
            "val_eval_top10_lift_pass_seed_count": int(np.sum(eval_lift >= 1.10)) if len(eval_lift) else 0,
            "val_eval_top10_lift_ci_p05": _nanmin_or_nan([row.get("val_eval_top10_lift_ci_p05") for row in rows]),
            "post_entry_diagnostic_only": any(bool(row.get("post_entry_diagnostic_only", False)) for row in rows),
            "selection_eligible": all(bool(row.get("selection_eligible", True)) for row in rows),
            "yearly_check_pass": all(bool(row.get("yearly_check_pass", False)) for row in rows),
            "selected_by": "val_select_seed_median",
        }
        aggregates.append(aggregate)
        if profile in SIMPLE_BASELINE_PROFILES and aggregate["selection_eligible"]:
            current = by_horizon_simple.get(horizon)
            if current is None or aggregate["val_select_spearman_median"] > current["val_select_spearman_median"]:
                by_horizon_simple[horizon] = aggregate

    for aggregate in aggregates:
        simple = by_horizon_simple.get(int(aggregate["horizon"]))
        if simple is None:
            aggregate.update(
                {
                    "best_simple_profile": None,
                    "best_simple_model_key": None,
                    "best_simple_val_select_spearman_median": float("nan"),
                    "best_simple_val_eval_spearman_median": float("nan"),
                    "beats_best_simple_val_select": False,
                    "beats_best_simple_val_eval": False,
                }
            )
            continue
        aggregate.update(
            {
                "best_simple_profile": simple["profile"],
                "best_simple_model_key": simple["model_key"],
                "best_simple_val_select_spearman_median": simple["val_select_spearman_median"],
                "best_simple_val_eval_spearman_median": simple["val_eval_spearman_median"],
                "beats_best_simple_val_select": aggregate["val_select_spearman_median"] - simple["val_select_spearman_median"] >= 0.03,
                "beats_best_simple_val_eval": aggregate["val_eval_spearman_median"] - simple["val_eval_spearman_median"] >= 0.02,
            }
        )
    return aggregates


def _utc_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def _heartbeat(label: str, done_runs: int, total_runs: int, elapsed_sec: float, eta_sec: float | None = None) -> None:
    suffix = f", eta={eta_sec:.1f}s" if eta_sec is not None and np.isfinite(eta_sec) else ""
    print(f"[heartbeat] {label}: done={done_runs}/{total_runs}, elapsed={elapsed_sec:.1f}s{suffix}", flush=True)


def _numeric_frame(frame: pd.DataFrame) -> pd.DataFrame:
    numeric = frame.apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan)
    return numeric.fillna(0.0)


def _feature_family(feature_name: str) -> str:
    return "price_coord" if "price_coord" in str(feature_name) else "non_price_coord"


def audit_feature_frame(profile: str, split_name: str, features: pd.DataFrame) -> tuple[list[dict[str, Any]], list[str]]:
    if not str(profile).strip():
        return [], ["missing required profile"]
    if features.empty:
        return [], []
    numeric = features.apply(pd.to_numeric, errors="coerce")
    values = numeric.to_numpy(dtype=float)
    if not np.isfinite(values).all():
        return [], [f"non-finite values in feature frame for profile={profile} split={split_name}"]
    rows: list[dict[str, Any]] = []
    for feature_name in numeric.columns:
        column = numeric[feature_name].to_numpy(dtype=float)
        rate = float(np.mean(np.abs(column) > 10.0))
        if rate < 0.05:
            continue
        family = _feature_family(str(feature_name))
        decision = "requires_no_price_coord_comparison" if family == "price_coord" else "accept_as_warning"
        rows.append(
            {
                "profile": profile,
                "split": split_name,
                "feature": str(feature_name),
                "family": "TAIL_GT10",
                "feature_family": family,
                "rate": rate,
                "decision": decision,
            }
        )
    return rows, []


def summarize_feature_audit(feature_audit_rows: list[dict[str, Any]], errors: list[str]) -> dict[str, Any]:
    status = "ERROR" if errors else "PASS"
    return {
        "status": status,
        "errors": list(errors),
        "tail_warning_count": int(
            sum(1 for row in feature_audit_rows if row.get("decision") == "accept_as_warning")
        ),
        "price_coord_comparison_required": any(
            row.get("decision") == "requires_no_price_coord_comparison" for row in feature_audit_rows
        ),
    }


def _best_seed_aggregate(report: dict[str, Any]) -> dict[str, Any] | None:
    aggregates = [
        row
        for row in report.get("seed_aggregate", [])
        if row.get("target_family") == "entry_movement"
        and bool(row.get("selection_eligible", True))
        and not bool(row.get("post_entry_diagnostic_only", False))
    ]
    if not aggregates:
        return None
    return max(aggregates, key=lambda row: float(row.get("val_select_spearman_median", float("-inf"))))


def enrich_report_contract(report: dict[str, Any]) -> dict[str, Any]:
    report["schema_version"] = AMPLITUDE_MOVEMENT_SCHEMA_VERSION
    report["selection_policy"] = SELECTION_POLICY
    report["normalization_contract"] = NORMALIZATION_CONTRACT
    report["target_contract"] = TARGET_CONTRACT
    report["target_unit_contract"] = report.get("target_unit_contract", TARGET_UNIT_CONTRACT)
    report["decision_time"] = SELECTION_POLICY["decision_time"]
    report["feature_audit"] = summarize_feature_audit(
        report.get("feature_audit_rows", []),
        report.get("feature_audit_errors", []),
    )
    report["verdict"] = decide_verdict(report)
    best = _best_seed_aggregate(report)
    report["summary"] = {
        "verdict": report["verdict"],
        "winner_unit": SELECTION_POLICY["winner_unit"],
        "wide_search_note": "diagnostic_only_wide_search_requires_replication",
        "best_profile": None if best is None else best.get("profile"),
        "best_model_key": None if best is None else best.get("model_key"),
        "best_horizon": None if best is None else best.get("horizon"),
    }
    return report


def _align_feature_frames_to_train(split_features: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    train_numeric = _numeric_frame(split_features["train"])
    aligned = {"train": train_numeric}
    for split_name, frame in split_features.items():
        if split_name == "train":
            continue
        aligned[split_name] = _numeric_frame(frame).reindex(columns=train_numeric.columns, fill_value=0.0)
    return aligned


def _yearly_spearman_rows(split_name: str, frame: pd.DataFrame, horizon: int, y_true: np.ndarray, y_pred: np.ndarray) -> list[dict[str, Any]]:
    if "time" not in frame.columns:
        return []
    timestamps = pd.to_datetime(frame["time"], errors="coerce")
    years = timestamps.dt.year.to_numpy()
    rows: list[dict[str, Any]] = []
    for year in range(2021, 2026):
        mask = years == year
        if not np.any(mask):
            continue
        year_true = np.asarray(y_true[mask], dtype=float)
        year_pred = np.asarray(y_pred[mask], dtype=float)
        lift_rows = compute_quantile_lift(year_true, year_pred, top_fracs=(0.10,))
        top10 = lift_rows[0] if lift_rows else {}
        rows.append(
            {
                "split": split_name,
                "year": year,
                "horizon": horizon,
                "spearman": compute_spearman(year_true, year_pred),
                "top10_lift": float(top10.get("lift", float("nan"))),
                "top_n": int(top10.get("top_n", 0.0) or 0),
                "rest_n": int(top10.get("rest_n", 0.0) or 0),
            }
        )
    return rows


def yearly_check_pass_for_split(yearly_rows: list[dict[str, Any]], split_name: str) -> bool:
    split_rows = [row for row in yearly_rows if row.get("split") == split_name]
    scores = [float(row.get("spearman", float("nan"))) for row in split_rows if np.isfinite(float(row.get("spearman", float("nan"))))]
    positive_scores = [score for score in scores if score > 0.0]
    if len(positive_scores) < 2:
        return False
    positive_contrib = np.asarray([abs(score) for score in positive_scores], dtype=float)
    total_positive = float(positive_contrib.sum())
    if not np.isfinite(total_positive) or total_positive <= 0.0:
        return False
    best_positive = float(np.max(positive_contrib))
    best_year_share = best_positive / total_positive
    best_index = int(np.argmax(scores))
    without_best_year_score = float(sum(score for idx, score in enumerate(scores) if idx != best_index))
    return bool(best_year_share < 0.80 and without_best_year_score > 0.0)


def _fit_single_job(
    job: dict[str, Any],
    splits: dict[str, pd.DataFrame],
    targets_by_split: dict[str, pd.DataFrame],
    requested_threads: int,
    effective_threads: int,
    feature_profile_cache: dict[str, dict[str, dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    run_started = time.time()
    run = {
        **job,
        "resume_key": resume_key(job),
        "requested_threads": requested_threads,
        "effective_threads": effective_threads,
        "model_thread_settings": model_thread_settings(str(job["model_key"]), effective_threads),
        "started_at": _utc_now_iso(),
        "deterministic": is_model_deterministic(str(job["model_key"])),
    }
    profile_key = str(job["profile"])
    if feature_profile_cache is not None and profile_key in feature_profile_cache:
        profile_bundle = feature_profile_cache[profile_key]
    else:
        profile_bundle = build_feature_profile_with_metadata(
            {name: splits[name] for name in ("train", "val_select", "val_eval", "low_n_disclosure")},
            profile_key,
        )
        if feature_profile_cache is not None:
            feature_profile_cache[profile_key] = profile_bundle
    split_features = profile_bundle["features"]
    split_meta = profile_bundle["metadata"]
    feature_audit_rows: list[dict[str, Any]] = []
    feature_audit_errors: list[str] = []
    for split_name, features in split_features.items():
        audit_rows, audit_errors = audit_feature_frame(profile_key, split_name, features)
        feature_audit_rows.extend(audit_rows)
        feature_audit_errors.extend(audit_errors)
    horizon = int(job["horizon"])
    target_col = f"entry_movement_{horizon}"
    train_meta = split_meta["train"]
    train_x = _numeric_frame(split_features["train"])
    if train_x.shape[1] == 0 or str(train_meta.get("status", "")).startswith("SKIPPED"):
        run.update(
            {
                "status": "skipped",
                "selection_eligible": False,
                "post_entry_diagnostic_only": bool(train_meta.get("post_entry_diagnostic_only", False)),
                "feature_contract_verdict": train_meta.get("feature_contract_verdict", "SKIPPED"),
                "available_at_decision_time": bool(train_meta.get("available_at_decision_time", False)),
                "skip_reason": train_meta.get("status", "SKIPPED_EMPTY_TRAIN_FEATURES"),
                "finished_at": _utc_now_iso(),
                "elapsed_sec": float(time.time() - run_started),
            }
        )
        return {
            "run": run,
            "quantiles": [],
            "yearly": [],
            "feature_metadata": split_meta,
            "feature_audit_rows": feature_audit_rows,
            "feature_audit_errors": feature_audit_errors,
        }

    aligned_features = _align_feature_frames_to_train(split_features)
    scaler = RobustScaler()
    scaler.fit(train_x)
    transformed = {
        split_name: scaler.transform(features)
        for split_name, features in aligned_features.items()
    }
    train_y = pd.to_numeric(targets_by_split["train"][target_col], errors="coerce").to_numpy(dtype=float)
    model = make_model(str(job["model_key"]), int(job["seed"]), effective_threads)
    model.fit(transformed["train"], train_y)

    run.update(
        {
            "status": "completed",
            "selection_eligible": bool(train_meta.get("selection_eligible", True)),
            "post_entry_diagnostic_only": bool(train_meta.get("post_entry_diagnostic_only", False)),
            "feature_contract_verdict": train_meta.get("feature_contract_verdict", "PASS"),
            "available_at_decision_time": bool(train_meta.get("available_at_decision_time", True)),
        }
    )

    yearly_rows: list[dict[str, Any]] = []
    quantile_rows: list[dict[str, Any]] = []
    for split_name in ("val_select", "val_eval", "low_n_disclosure"):
        y_true = pd.to_numeric(targets_by_split[split_name][target_col], errors="coerce").to_numpy(dtype=float)
        y_pred = np.asarray(model.predict(transformed[split_name]), dtype=float)
        run[f"{split_name}_spearman"] = compute_spearman(y_true, y_pred)
        split_lifts = compute_quantile_lift(y_true, y_pred)
        for lift_row in split_lifts:
            quantile_rows.append(
                {
                    "profile": job["profile"],
                    "model_key": job["model_key"],
                    "seed": job["seed"],
                    "horizon": horizon,
                    "target_family": job["target_family"],
                    "split": split_name,
                    **lift_row,
                }
            )
        top10 = next((row for row in split_lifts if abs(float(row["top_frac"]) - 0.10) < 1e-9), None)
        if top10 is not None:
            run[f"{split_name}_top10_lift"] = float(top10["lift"])
            run[f"{split_name}_top10_lift_ci_p05"] = float(top10["lift_ci_p05"])
        if split_name in {"val_select", "val_eval"}:
            for yearly_row in _yearly_spearman_rows(split_name, splits[split_name], horizon, y_true, y_pred):
                yearly_rows.append(
                    {
                        "profile": job["profile"],
                        "model_key": job["model_key"],
                        "seed": job["seed"],
                        "target_family": job["target_family"],
                        **yearly_row,
                    }
                )

    run["yearly_check_pass"] = yearly_check_pass_for_split(yearly_rows, "val_select") and yearly_check_pass_for_split(yearly_rows, "val_eval")
    run["selected_by"] = "val_select_seed_median"
    run["finished_at"] = _utc_now_iso()
    run["elapsed_sec"] = float(time.time() - run_started)
    return {
        "run": run,
        "quantiles": quantile_rows,
        "yearly": yearly_rows,
        "feature_metadata": split_meta,
        "feature_audit_rows": feature_audit_rows,
        "feature_audit_errors": feature_audit_errors,
    }


def _write_report_artifacts(report: dict[str, Any]) -> None:
    enrich_report_contract(report)
    REPORT_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON_PATH.write_text(json.dumps(report, ensure_ascii=True, indent=2, default=str), encoding="utf-8")
    pd.DataFrame(report.get("metrics", [])).to_csv(REPORT_METRICS_PATH, index=False)
    pd.DataFrame(report.get("seed_aggregate", [])).to_csv(REPORT_SEED_AGGREGATE_PATH, index=False)
    pd.DataFrame(report.get("quantiles", [])).to_csv(REPORT_QUANTILES_PATH, index=False)
    pd.DataFrame(report.get("yearly", [])).to_csv(REPORT_YEARLY_PATH, index=False)
    pd.DataFrame(report.get("target_distribution", [])).to_csv(REPORT_TARGET_DISTRIBUTION_PATH, index=False)
    pd.DataFrame(report.get("feature_audit_rows", [])).to_csv(REPORT_FEATURE_AUDIT_PATH, index=False)
    pd.DataFrame(report.get("rows", [])).to_csv(REPORT_ROWS_PATH, index=False)


def _completed_keys_from_report(report: dict[str, Any]) -> set[str]:
    return {str(row.get("resume_key")) for row in report.get("metrics", []) if row.get("resume_key")}


def _done_keys_from_report(report: dict[str, Any]) -> set[str]:
    done = _completed_keys_from_report(report)
    done.update(str(row.get("resume_key")) for row in report.get("failed_runs", []) if row.get("resume_key"))
    return done


def _remove_failed_run(report: dict[str, Any], key: str) -> None:
    report["failed_runs"] = [row for row in report.get("failed_runs", []) if str(row.get("resume_key")) != key]


def _upsert_failed_run(report: dict[str, Any], failed_run: dict[str, Any]) -> None:
    key = str(failed_run.get("resume_key"))
    _remove_failed_run(report, key)
    report.setdefault("failed_runs", []).append(failed_run)


def _load_or_init_report(resume: bool, run_config: dict[str, Any], run_config_hash: str, total_runs: int, requested_threads: int, effective_threads: int) -> dict[str, Any]:
    if resume and REPORT_JSON_PATH.exists():
        report = json.loads(REPORT_JSON_PATH.read_text(encoding="utf-8"))
        if report.get("run_config_hash") != run_config_hash:
            raise RuntimeError("run_config_hash mismatch; refuse to resume incompatible run")
        return report
    progress = build_initial_progress(total_runs, requested_threads, effective_threads)
    return {
        "schema_version": AMPLITUDE_MOVEMENT_SCHEMA_VERSION,
        "stage_status": "DIAGNOSTIC_ONLY",
        "output_prefix": OUTPUT_PREFIX,
        "selection_policy": SELECTION_POLICY,
        "normalization_contract": NORMALIZATION_CONTRACT,
        "target_contract": TARGET_CONTRACT,
        "target_unit_contract": TARGET_UNIT_CONTRACT,
        "decision_time": SELECTION_POLICY["decision_time"],
        "run_config": run_config,
        "run_config_hash": run_config_hash,
        "progress": progress,
        "metrics": [],
        "rows": [],
        "quantiles": [],
        "yearly": [],
        "seed_aggregate": [],
        "target_distribution": [],
        "feature_audit_rows": [],
        "feature_audit_errors": [],
        "feature_audit": {"status": "PASS", "errors": []},
        "failed_runs": [],
        "verdict": None,
        "summary": {},
        "started_at": progress["started_at"],
        "finished_at": None,
        "elapsed_sec": 0.0,
    }


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Entry-based amplitude movement runner")
    parser.add_argument("--entry-based-amplitude-movement", action="store_true")
    parser.add_argument("--resume", dest="resume", action="store_true", default=True)
    parser.add_argument("--no-resume", dest="resume", action="store_false")
    parser.add_argument("--threads", type=int, default=24)
    return parser


def run_entry_based_amplitude_movement(args: argparse.Namespace) -> dict[str, Any]:
    started = time.time()
    jobs = enumerate_jobs()
    requested_threads = int(getattr(args, "threads", 24) or 24)
    effective_threads = resolve_effective_threads(requested_threads=requested_threads, parallel_workers=1)
    run_config = dict(build_run_config())
    run_config["requested_threads"] = requested_threads
    run_config["effective_threads"] = effective_threads
    run_config_hash = compute_config_hash(run_config)
    report = _load_or_init_report(args.resume, run_config, run_config_hash, len(jobs), requested_threads, effective_threads)
    completed_keys = _completed_keys_from_report(report)
    done_keys = _done_keys_from_report(report)
    report["progress"]["completed_keys"] = sorted(completed_keys)
    report["progress"]["done_runs"] = len(done_keys)

    _heartbeat("preflight_start", len(completed_keys), len(jobs), time.time() - started)
    splits = load_entry_based_splits()
    train_targets, thresholds = build_movement_targets(splits["train"])
    targets_by_split = {"train": train_targets}
    for split_name in ("val_select", "val_eval", "low_n_disclosure"):
        targets_by_split[split_name], _ = build_movement_targets(splits[split_name], train_thresholds=thresholds)
    report["target_distribution"] = compute_target_distribution(targets_by_split)
    _heartbeat("preflight_done", len(completed_keys), len(jobs), time.time() - started)

    run_durations: list[float] = []
    feature_profile_cache: dict[str, dict[str, dict[str, Any]]] = {}
    for job in jobs:
        if should_skip_job(job, completed_keys, args.resume):
            continue
        job_started = time.time()
        job_started_at = _utc_now_iso()
        elapsed = time.time() - started
        eta_sec = None
        done_runs = int(report["progress"]["done_runs"])
        if run_durations:
            remaining = len(jobs) - done_runs
            eta_sec = float(np.mean(run_durations) * remaining)
        _heartbeat(f"run_start {resume_key(job)}", done_runs, len(jobs), elapsed, eta_sec)
        try:
            result = _fit_single_job(job, splits, targets_by_split, requested_threads, effective_threads, feature_profile_cache)
            report["metrics"].append(result["run"])
            report["rows"].append(result["run"])
            report["quantiles"].extend(result["quantiles"])
            report["yearly"].extend(result["yearly"])
            report["feature_audit_rows"].extend(result.get("feature_audit_rows", []))
            report["feature_audit_errors"].extend(result.get("feature_audit_errors", []))
            for split_name, meta in result["feature_metadata"].items():
                report["feature_audit_rows"].append(
                    {
                        "profile": job["profile"],
                        "split": split_name,
                        "feature": "",
                        "family": "metadata",
                        "rate": float("nan"),
                        "decision": meta.get("feature_contract_verdict", "PASS"),
                    }
                )
            completed_keys.add(result["run"]["resume_key"])
            done_keys.add(result["run"]["resume_key"])
            _remove_failed_run(report, result["run"]["resume_key"])
            report["progress"]["completed_keys"] = sorted(completed_keys)
            run_durations.append(float(result["run"]["elapsed_sec"]))
        except Exception as exc:
            failed_run = {
                **job,
                "resume_key": resume_key(job),
                "error": str(exc),
                "requested_threads": requested_threads,
                "effective_threads": effective_threads,
                "started_at": job_started_at,
                "finished_at": _utc_now_iso(),
                "elapsed_sec": float(time.time() - job_started),
                "status": "failed",
                "deterministic": is_model_deterministic(str(job["model_key"])),
            }
            _upsert_failed_run(report, failed_run)
            done_keys.add(failed_run["resume_key"])
        report["progress"]["done_runs"] = len(done_keys)
        report["progress"]["elapsed_sec"] = float(time.time() - started)
        report["seed_aggregate"] = aggregate_seed_metrics(report["metrics"])
        report["finished_at"] = _utc_now_iso()
        report["elapsed_sec"] = float(time.time() - started)
        report["progress"]["finished_at"] = report["finished_at"]
        _write_report_artifacts(report)
        _heartbeat(f"run_done {resume_key(job)}", int(report["progress"]["done_runs"]), len(jobs), time.time() - started)
    return report


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()
    if not args.entry_based_amplitude_movement:
        print("Pass --entry-based-amplitude-movement")
        return
    run_entry_based_amplitude_movement(args)


if __name__ == "__main__":
    main()
