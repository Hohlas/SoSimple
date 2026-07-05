# =============================================================================
# Файл: benchmark_entry_based_updn_fractal_selection_ablation.py
# Назначение: bounded runner для абляции отбора фракталов на фиксированном
#   `entry-based next open` target с progress JSON, resume и coverage audit
# Язык: Python 3.10+
# Обновлён: 2026-07-03
# Зависимости:
#   Входные данные:
#     - DATA/Nero_*_labeled.csv (через foundation runner)
#   Выходные данные:
#     - ML/reports/entry_based_updn_fractal_selection_ablation.json
#     - ML/reports/entry_based_updn_fractal_selection_ablation_metrics.csv
#     - ML/reports/entry_based_updn_fractal_selection_ablation_rows.csv
#   Внутренние зависимости:
#     - ML/baseline/benchmark_next_open_entry_updn_foundation.py
#     - ML/fractal_level_feature_builder.py
#     - statistics/data_contract_smoke_check.py
# Использование:
#   ./.venv/bin/python ML/baseline/benchmark_entry_based_updn_fractal_selection_ablation.py \
#     --entry-based-updn-fractal-selection-ablation --resume
# Примечания:
#   - Этап остаётся DIAGNOSTIC_ONLY.
#   - Representation matrix и model grid намеренно заморожены планом.
# =============================================================================

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import inspect
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.multioutput import MultiOutputRegressor
import xgboost as xgb

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from ML.baseline import benchmark_next_open_entry_updn_foundation as entry_foundation
from ML.fractal_level_feature_builder import (
    FRACTAL_FIELDS,
    build_feature_contract,
    build_fractal_level_features,
    fractal_columns_in_order,
    parse_fractal,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PYTHON_BIN = PROJECT_ROOT / ".venv" / "bin" / "python"
SMOKE_CHECK_PATH = PROJECT_ROOT / "statistics" / "data_contract_smoke_check.py"
REPORTS_DIR = PROJECT_ROOT / "ML" / "reports"
REPORT_JSON_PATH = REPORTS_DIR / "entry_based_updn_fractal_selection_ablation.json"
REPORT_METRICS_PATH = REPORTS_DIR / "entry_based_updn_fractal_selection_ablation_metrics.csv"
REPORT_ROWS_PATH = REPORTS_DIR / "entry_based_updn_fractal_selection_ablation_rows.csv"

TARGET_COLUMNS = (
    "entry_up_3",
    "entry_dn_3",
    "entry_up_6",
    "entry_dn_6",
    "entry_up_12",
    "entry_dn_12",
)
ENTRY_LOG_RATIO_COLUMNS = ("entry_log_ratio_3", "entry_log_ratio_6", "entry_log_ratio_12")
FORBIDDEN_FEATURE_PREFIXES = ("entry_up_", "entry_dn_", "entry_log_ratio_", "up_", "dn_")
REPRESENTATION_ORDER = (
    "all100",
    "nearest_k20",
    "nearest_k40",
    "nearest_k60",
    "nearest_k80",
    "corridor_5atr",
    "corridor_10atr",
    "corridor_15atr",
    "zones_atr",
    "zones_plus_nearest_k40",
)
MODEL_ORDER = (
    "xgboost_depth3",
    "xgboost_depth5",
    "hist_gradient_boosting",
    "ridge",
)
SPLIT_ORDER = ("train_core", "val_stop", "diagnostic_holdout", "low_n_disclosure")
HORIZON_MAP = {"H3": (0, 1), "H6": (2, 3), "H12": (4, 5)}
SUMMARY_HORIZONS = ("3", "6", "12")
DEFAULT_SERIALIZED_UPDN_FEATURE_HORIZONS = ("3", "6", "12")
FULL_SERIALIZED_UPDN_FEATURE_HORIZONS = ("3", "6", "12", "24", "48")
ALLOWED_UPDN_HORIZONS = DEFAULT_SERIALIZED_UPDN_FEATURE_HORIZONS
EXCLUDED_UPDN_HORIZONS = ("24", "48")
COMMON_SELECTION_FIELDS = (
    "direction",
    "front",
    "back",
    "strong",
    "break",
    "reverse",
    "power",
    "count",
    "impulse",
    "fractal_atr",
    "up_3",
    "dn_3",
    "up_6",
    "dn_6",
    "up_12",
    "dn_12",
    "up_24",
    "dn_24",
    "up_48",
    "dn_48",
)
STRUCTURE_CONTEXT_FIELDS = ("atr", "fractal0_direction", "fractals_above_count", "fractals_below_count", "fractal0_price_rank")


@dataclass(frozen=True)
class SelectionAblationConfig:
    seeds: tuple[int, ...] = (42, 77, 123)
    xgb_threads: int = 24
    primary_split: str = "val_stop"
    resume_default: bool = True
    report_json_path: Path = REPORT_JSON_PATH
    report_metrics_path: Path = REPORT_METRICS_PATH
    report_rows_path: Path = REPORT_ROWS_PATH
    target_mode_default: str = "rebuilt"


CONFIG = SelectionAblationConfig()


def build_representation_registry() -> dict[str, dict]:
    return {
        "all100": {"selection_family": "all100", "role": "baseline", "k": 99},
        "nearest_k20": {"selection_family": "nearest_k", "role": "primary", "k": 20},
        "nearest_k40": {"selection_family": "nearest_k", "role": "primary", "k": 40},
        "nearest_k60": {"selection_family": "nearest_k", "role": "primary", "k": 60},
        "nearest_k80": {"selection_family": "nearest_k", "role": "primary", "k": 80},
        "corridor_5atr": {"selection_family": "corridor_Xatr", "role": "primary", "width_atr": 5.0, "slot_count": 99},
        "corridor_10atr": {"selection_family": "corridor_Xatr", "role": "primary", "width_atr": 10.0, "slot_count": 99},
        "corridor_15atr": {"selection_family": "corridor_Xatr", "role": "primary", "width_atr": 15.0, "slot_count": 99},
        "zones_atr": {"selection_family": "zones_atr", "role": "secondary"},
        "zones_plus_nearest_k40": {"selection_family": "zones_plus_nearest_k", "role": "secondary", "k": 40},
    }


def build_model_registry() -> dict[str, dict]:
    return {
        "xgboost_depth3": {"family": "xgboost", "max_depth": 3},
        "xgboost_depth5": {"family": "xgboost", "max_depth": 5},
        "hist_gradient_boosting": {"family": "hist_gradient_boosting", "max_depth": 5, "max_iter": 150},
        "ridge": {"family": "ridge", "alpha": 1.0},
    }


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fractal selection ablation on entry-based target.")
    parser.add_argument("--entry-based-updn-fractal-selection-ablation", action="store_true")
    resume_group = parser.add_mutually_exclusive_group()
    resume_group.add_argument("--resume", dest="resume", action="store_true", default=CONFIG.resume_default)
    resume_group.add_argument("--no-resume", dest="resume", action="store_false")
    return parser


def load_or_init_report(path: Path, resume: bool) -> dict:
    if resume and path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"runs": []}


def heartbeat(stage: str, *, done_runs: int | None = None, total_runs: int | None = None, elapsed_sec: float | None = None, eta_sec: float | None = None) -> None:
    parts = [f"[fractal-selection] {stage}"]
    if done_runs is not None and total_runs is not None:
        parts.append(f"{done_runs}/{total_runs}")
    if elapsed_sec is not None:
        parts.append(f"elapsed={elapsed_sec:.1f}s")
    if eta_sec is not None:
        parts.append(f"eta={eta_sec:.1f}s")
    print(" | ".join(parts), flush=True)


def _utc_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def target_builder_fingerprint() -> str:
    source = inspect.getsource(entry_foundation.rebuild_entry_targets)
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


def load_entry_based_splits(target_mode: str = "rebuilt") -> dict[str, pd.DataFrame]:
    source_splits = entry_foundation.load_research_splits()
    if target_mode not in {"rebuilt", "loaded_verified"}:
        raise ValueError(f"Unsupported target_mode: {target_mode}")
    if target_mode == "rebuilt":
        ohlc = entry_foundation.load_ohlc()
        return {
            split_name: entry_foundation.rebuild_entry_targets(frame.copy(), ohlc, horizons=(3, 6, 12))
            for split_name, frame in source_splits.items()
        }
    return source_splits


def build_split_summary(splits: dict[str, pd.DataFrame]) -> dict:
    return {split_name: {"rows": int(len(frame))} for split_name, frame in splits.items() if split_name in SPLIT_ORDER}


def find_forbidden_feature_columns(columns: list[str]) -> list[str]:
    return [column for column in columns if any(column.startswith(prefix) for prefix in FORBIDDEN_FEATURE_PREFIXES)]


def validate_entry_based_target_contract(splits: dict[str, pd.DataFrame], target_mode: str = "rebuilt") -> dict:
    split_checks = {}
    overall_pass = True
    required_columns = list(TARGET_COLUMNS + ENTRY_LOG_RATIO_COLUMNS)
    for split_name in SPLIT_ORDER:
        frame = splits[split_name]
        missing = [column for column in required_columns if column not in frame.columns]
        finite = True
        if not missing:
            values = frame.loc[:, required_columns].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
            finite = bool(np.isfinite(values).all())
        status = "PASS" if (not missing and finite) else "FAIL"
        split_checks[split_name] = {"status": status, "rows": int(len(frame)), "missing_columns": missing}
        overall_pass = overall_pass and status == "PASS"

    feature_contract = build_feature_contract(fractal_count=100)
    return {
        "status": "PASS" if overall_pass else "FAIL",
        "target_mode": target_mode,
        "target_builder_fingerprint": target_builder_fingerprint(),
        "target_builder_metadata": {"module": entry_foundation.__name__, "function": "rebuild_entry_targets"},
        "feature_contract_count": len(feature_contract),
        "split_checks": split_checks,
        "scope": "entry-based target contract",
    }


def _safe_atr(value: object) -> float:
    try:
        atr = float(value)
    except (TypeError, ValueError):
        return 1.0
    if not np.isfinite(atr) or atr <= 0.0:
        return 1.0
    return atr


def _selection_columns(prefix: str) -> list[str]:
    columns = [f"{prefix}_valid", f"{prefix}_source_index", f"{prefix}_price_coord_atr", f"{prefix}_abs_price_coord_atr"]
    columns.extend(f"{prefix}_{field}" for field in COMMON_SELECTION_FIELDS)
    return columns


def _fill_selection_slot(row_features: dict[str, float], prefix: str, parsed: dict[str, Any] | None, source_index: int, price_coord_atr: float, valid: int) -> None:
    row_features[f"{prefix}_valid"] = float(valid)
    row_features[f"{prefix}_source_index"] = float(source_index)
    row_features[f"{prefix}_price_coord_atr"] = float(price_coord_atr)
    row_features[f"{prefix}_abs_price_coord_atr"] = abs(float(price_coord_atr))
    parsed = parsed or {}
    for field in COMMON_SELECTION_FIELDS:
        row_features[f"{prefix}_{field}"] = float(parsed.get(field, 0.0) or 0.0)


def _filter_serialized_updn_horizon_columns(features: pd.DataFrame, allowed_horizons: tuple[str, ...]) -> pd.DataFrame:
    allowed_parts = tuple(f"_{side}_{horizon}" for horizon in allowed_horizons for side in ("up", "dn"))
    filtered_columns = []
    for column in features.columns:
        is_updn = any(f"_{side}_" in column for side in ("up", "dn"))
        if not is_updn or any(part in column for part in allowed_parts):
            filtered_columns.append(column)
    return features.loc[:, filtered_columns].copy()


def _candidate_fractals(row: pd.Series) -> tuple[float, list[dict[str, Any]]]:
    fractal0 = parse_fractal(row.get("fractal0", ""))
    base_price = float(fractal0.get("price", 0.0)) if fractal0 else 0.0
    atr = _safe_atr(row.get("ATR"))
    candidates = []
    for column in fractal_columns_in_order(row.index):
        parsed = parse_fractal(row.get(column, ""))
        if parsed is None:
            continue
        source_index = int(column.removeprefix("fractal"))
        if source_index == 0:
            continue
        price_coord_atr = (float(parsed.get("price", 0.0) or 0.0) - base_price) / atr
        candidates.append(
            {
                "source_index": source_index,
                "parsed": parsed,
                "price_coord_atr": float(price_coord_atr),
                "abs_price_coord_atr": abs(float(price_coord_atr)),
            }
        )
    return base_price, candidates


def _build_all100_features(frame: pd.DataFrame) -> pd.DataFrame:
    out_rows = []
    ordered = [f"fractal{i}" for i in range(1, 100)]
    for _, row in frame.iterrows():
        atr = _safe_atr(row.get("ATR"))
        fractal0 = parse_fractal(row.get("fractal0", ""))
        base_direction = float(fractal0.get("direction", 0) or 0) if fractal0 else 0.0
        base_price, candidates = _candidate_fractals(row)
        by_index = {f"fractal{item['source_index']}": item for item in candidates}
        row_features = {
            "atr": atr,
            "fractal0_direction": base_direction,
            "fractals_above_count": float(sum(1 for item in candidates if item["price_coord_atr"] > 0)),
            "fractals_below_count": float(sum(1 for item in candidates if item["price_coord_atr"] < 0)),
            "fractal0_price_rank": 0.0,
        }
        if candidates:
            row_features["fractal0_price_rank"] = row_features["fractals_below_count"] / max(len(candidates), 1)
        for slot, column in enumerate(ordered):
            prefix = f"slot_{slot:02d}"
            item = by_index.get(column)
            if item is None:
                _fill_selection_slot(row_features, prefix, None, 0, 0.0, 0)
            else:
                _fill_selection_slot(row_features, prefix, item["parsed"], item["source_index"], item["price_coord_atr"], 1)
        out_rows.append(row_features)
    return pd.DataFrame(out_rows, index=frame.index).fillna(0.0)


def _coverage_summary(selected_counts: list[int], truncation_count: int, min_coords: list[float], max_coords: list[float]) -> dict:
    array = np.asarray(selected_counts, dtype=float) if selected_counts else np.asarray([0.0], dtype=float)
    return {
        "selected_count_distribution": {
            "p5": float(np.percentile(array, 5)),
            "p25": float(np.percentile(array, 25)),
            "p50": float(np.percentile(array, 50)),
            "p75": float(np.percentile(array, 75)),
            "p95": float(np.percentile(array, 95)),
        },
        "share_rows_0": float(np.mean(array == 0)),
        "share_rows_1": float(np.mean(array == 1)),
        "share_rows_2": float(np.mean(array == 2)),
        "share_rows_3plus": float(np.mean(array >= 3)),
        "truncation_share": float(truncation_count / max(len(selected_counts), 1)),
        "min_price_coord_atr": float(min(min_coords)) if min_coords else 0.0,
        "max_price_coord_atr": float(max(max_coords)) if max_coords else 0.0,
    }


def _build_corridor_features(frame: pd.DataFrame, width_atr: float, slot_count: int) -> tuple[pd.DataFrame, dict]:
    out_rows = []
    selected_counts: list[int] = []
    min_coords: list[float] = []
    max_coords: list[float] = []
    truncation_count = 0
    for _, row in frame.iterrows():
        atr = _safe_atr(row.get("ATR"))
        fractal0 = parse_fractal(row.get("fractal0", ""))
        base_direction = float(fractal0.get("direction", 0) or 0) if fractal0 else 0.0
        _, candidates = _candidate_fractals(row)
        corridor = [item for item in candidates if item["abs_price_coord_atr"] <= width_atr + 1e-9]
        corridor.sort(key=lambda item: (item["abs_price_coord_atr"], item["source_index"]))
        selected = corridor[:slot_count]
        if len(corridor) > slot_count:
            truncation_count += 1
        selected_counts.append(len(corridor))
        if corridor:
            min_coords.append(min(item["price_coord_atr"] for item in corridor))
            max_coords.append(max(item["price_coord_atr"] for item in corridor))
        row_features = {
            "atr": atr,
            "fractal0_direction": base_direction,
            "fractals_above_count": float(sum(1 for item in corridor if item["price_coord_atr"] > 0)),
            "fractals_below_count": float(sum(1 for item in corridor if item["price_coord_atr"] < 0)),
            "fractal0_price_rank": 0.0,
        }
        for slot in range(slot_count):
            prefix = f"slot_{slot:02d}"
            if slot >= len(selected):
                _fill_selection_slot(row_features, prefix, None, 0, 0.0, 0)
            else:
                item = selected[slot]
                _fill_selection_slot(row_features, prefix, item["parsed"], item["source_index"], item["price_coord_atr"], 1)
        out_rows.append(row_features)
    coverage = _coverage_summary(selected_counts, truncation_count, min_coords, max_coords)
    return pd.DataFrame(out_rows, index=frame.index).fillna(0.0), coverage


def _build_nearest_k_features(frame: pd.DataFrame, k: int) -> tuple[pd.DataFrame, dict]:
    features = build_fractal_level_features(frame, input_family="nearest_k", k=k, geometry_only=False).copy()
    rename_map = {}
    for column in list(features.columns):
        if column.startswith("nearest_") and column.endswith("_raw_distance_atr"):
            rename_map[column] = column.replace("_raw_distance_atr", "_price_coord_atr")
        if column.startswith("nearest_") and column.endswith("_abs_distance_atr"):
            rename_map[column] = column.replace("_abs_distance_atr", "_abs_price_coord_atr")
    if rename_map:
        features = features.rename(columns=rename_map)
    features = features.rename(columns={"nearest_00_valid": "slot_00_valid"}).rename(columns={"slot_00_valid": "nearest_00_valid"})
    coverage = _coverage_summary(
        [int(features[[f"nearest_{slot:02d}_valid" for slot in range(k)]].iloc[row].sum()) for row in range(len(features))],
        0,
        [],
        [],
    )
    return features, coverage


def _build_zones_features(frame: pd.DataFrame, with_nearest_k: int | None = None) -> tuple[pd.DataFrame, dict]:
    input_family = "zones_plus_nearest_k" if with_nearest_k else "zones"
    kwargs = {"input_family": input_family, "geometry_only": False}
    if with_nearest_k:
        kwargs["k"] = with_nearest_k
    features = build_fractal_level_features(frame, **kwargs).copy()
    coverage = {"selected_count_distribution": {"p5": 0.0, "p25": 0.0, "p50": 0.0, "p75": 0.0, "p95": 0.0}, "share_rows_0": 0.0, "share_rows_1": 0.0, "share_rows_2": 0.0, "share_rows_3plus": 1.0, "truncation_share": 0.0, "min_price_coord_atr": 0.0, "max_price_coord_atr": 0.0}
    return features, coverage


def build_representation_features(
    df: pd.DataFrame,
    profile_key: str,
    serialized_updn_horizons: tuple[str, ...] = DEFAULT_SERIALIZED_UPDN_FEATURE_HORIZONS,
) -> tuple[pd.DataFrame, dict]:
    registry = build_representation_registry()
    spec = registry[profile_key]
    selection_family = spec["selection_family"]
    if selection_family == "all100":
        features = _build_all100_features(df)
        coverage = {"selected_count_distribution": {"p5": 99.0, "p25": 99.0, "p50": 99.0, "p75": 99.0, "p95": 99.0}, "share_rows_0": 0.0, "share_rows_1": 0.0, "share_rows_2": 0.0, "share_rows_3plus": 1.0, "truncation_share": 0.0, "min_price_coord_atr": 0.0, "max_price_coord_atr": 0.0}
    elif selection_family == "nearest_k":
        features, coverage = _build_nearest_k_features(df, spec["k"])
    elif selection_family == "corridor_Xatr":
        features, coverage = _build_corridor_features(df, spec["width_atr"], spec["slot_count"])
    elif selection_family == "zones_atr":
        features, coverage = _build_zones_features(df)
    elif selection_family == "zones_plus_nearest_k":
        features, coverage = _build_zones_features(df, with_nearest_k=spec["k"])
    else:
        raise ValueError(f"Unsupported selection_family: {selection_family}")

    features = _filter_serialized_updn_horizon_columns(features, serialized_updn_horizons)
    metadata = {
        "profile_key": profile_key,
        "selection_family": selection_family,
        "feature_names": list(features.columns),
        "feature_count": int(features.shape[1]),
        "coverage_summary": coverage,
        "anchor_contract": {"price": "fractal0.price", "atr": "row_ATR"},
        "same_feature_bundle": "structure_full + distance_atr + price_coord_atr",
        "updn_horizons": list(serialized_updn_horizons),
        "excluded_updn_horizons": [
            horizon for horizon in FULL_SERIALIZED_UPDN_FEATURE_HORIZONS if horizon not in serialized_updn_horizons
        ],
    }
    if "k" in spec:
        metadata["k"] = int(spec["k"])
    if "width_atr" in spec:
        metadata["width_atr"] = float(spec["width_atr"])
    return features, metadata


def get_cached_representation(
    splits: dict[str, pd.DataFrame],
    split_name: str,
    profile_key: str,
) -> tuple[pd.DataFrame, dict]:
    cache = splits.setdefault("_representation_cache", {})
    key = (split_name, profile_key)
    if key not in cache:
        cache[key] = build_representation_features(splits[split_name], profile_key)
    return cache[key]


def run_representation_preflight(df: pd.DataFrame, profile_key: str) -> dict:
    _, metadata = build_representation_features(df, profile_key)
    coverage = metadata["coverage_summary"]
    status = "PASS"
    issues: list[str] = []
    width_atr = metadata.get("width_atr")
    if width_atr is not None:
        if coverage["min_price_coord_atr"] < -width_atr - 1e-9 or coverage["max_price_coord_atr"] > width_atr + 1e-9:
            status = "ERROR"
            issues.append("corridor_out_of_range")
        if coverage["share_rows_0"] > 0.05:
            status = "ERROR"
            issues.append("empty_rows")
        elif coverage["selected_count_distribution"]["p50"] < 3.0:
            status = "WARNING"
            issues.append("low_median_coverage")
        if coverage["truncation_share"] > 0.25 and status != "ERROR":
            status = "WARNING"
            issues.append("high_truncation")
    return {"status": status, "issues": issues, "metadata": metadata}


def run_all_preflight(splits: dict[str, pd.DataFrame]) -> dict:
    profiles = {}
    overall = "PASS"
    train = splits["train_core"]
    for profile_key in REPRESENTATION_ORDER:
        result = run_representation_preflight(train, profile_key)
        profiles[profile_key] = result
        if result["status"] == "ERROR":
            overall = "ERROR"
        elif result["status"] == "WARNING" and overall == "PASS":
            overall = "WARNING"
    return {"status": overall, "profiles": profiles}


def _series_stats(values: pd.Series) -> dict[str, float]:
    numeric = pd.to_numeric(values, errors="coerce")
    finite = numeric[np.isfinite(numeric.fillna(np.nan))]
    if finite.empty:
        finite = pd.Series([0.0])
    arr = finite.to_numpy(dtype=float)
    abs_arr = np.abs(arr)
    return {
        "missing_pct": float(numeric.isna().mean() * 100.0),
        "zero_pct": float((arr == 0.0).mean() * 100.0),
        "p1": float(np.percentile(arr, 1)),
        "p5": float(np.percentile(arr, 5)),
        "p50": float(np.percentile(arr, 50)),
        "p95": float(np.percentile(arr, 95)),
        "p99": float(np.percentile(arr, 99)),
        "frac_abs_gt3": float(np.mean(abs_arr > 3.0)),
        "frac_abs_gt5": float(np.mean(abs_arr > 5.0)),
        "frac_abs_gt10": float(np.mean(abs_arr > 10.0)),
        "frac_abs_gt20": float(np.mean(abs_arr > 20.0)),
        "std": float(np.std(arr)),
        "unique_count": int(pd.Series(arr).nunique()),
    }


def audit_feature_distribution(train_df: pd.DataFrame, other_df: pd.DataFrame, profile_key: str) -> dict:
    train_features, train_meta = build_representation_features(train_df, profile_key)
    other_features, _ = build_representation_features(other_df, profile_key)
    return audit_feature_distribution_from_frames(train_features, other_features, train_meta, profile_key=profile_key)


def audit_feature_distribution_from_frames(
    train_features: pd.DataFrame,
    other_features: pd.DataFrame,
    train_meta: dict,
    *,
    profile_key: str,
) -> dict:
    feature_stats = {}
    flags: list[str] = []
    shifts = {}
    for column in train_features.columns:
        train_stats = _series_stats(train_features[column])
        other_stats = _series_stats(other_features[column]) if column in other_features else _series_stats(pd.Series([0.0]))
        feature_stats[column] = train_stats
        shifts[column] = {"p50_shift": float(other_stats["p50"] - train_stats["p50"]), "p95_shift": float(other_stats["p95"] - train_stats["p95"])}
        if train_stats["frac_abs_gt10"] > 0.01:
            flags.append(f"TAIL_GT10:{column}")
        if train_stats["std"] <= 1e-12 or train_stats["unique_count"] <= 1:
            flags.append(f"NEAR_CONSTANT:{column}")
        series = pd.to_numeric(train_features[column], errors="coerce")
        if series.isna().any():
            flags.append(f"NaN:{column}")
        if not np.isfinite(series.fillna(0.0).to_numpy(dtype=float)).all():
            flags.append(f"Inf:{column}")
    width_atr = train_meta.get("width_atr")
    if width_atr is not None:
        coverage = train_meta["coverage_summary"]
        if coverage["min_price_coord_atr"] < -width_atr - 1e-9 or coverage["max_price_coord_atr"] > width_atr + 1e-9:
            flags.append("corridor_out_of_range")
    status = "PASS"
    if any(flag.startswith(("NaN", "Inf", "corridor_out_of_range")) for flag in flags):
        status = "ERROR"
    elif flags:
        status = "WARNING"
    return {
        "status": status,
        "profile_key": profile_key,
        "feature_stats": feature_stats,
        "flags": sorted(set(flags)),
        "train_to_other_shift": shifts,
    }


def run_distribution_audit(splits: dict[str, pd.DataFrame], profile_keys: list[str]) -> dict:
    profiles = {}
    overall = "PASS"
    for profile_key in profile_keys:
        train_vs_val = audit_feature_distribution(splits["train_core"], splits["val_stop"], profile_key)
        train_vs_holdout = audit_feature_distribution(splits["train_core"], splits["diagnostic_holdout"], profile_key)
        profile_status = "PASS"
        if "ERROR" in {train_vs_val["status"], train_vs_holdout["status"]}:
            profile_status = "ERROR"
            overall = "ERROR"
        elif "WARNING" in {train_vs_val["status"], train_vs_holdout["status"]} and overall == "PASS":
            profile_status = "WARNING"
            overall = "WARNING"
        profiles[profile_key] = {
            "status": profile_status,
            "train_vs_val": train_vs_val,
            "train_vs_holdout": train_vs_holdout,
        }
    return {"status": overall, "profiles": profiles}


def run_all_preflight_with_progress(
    splits: dict[str, pd.DataFrame],
    *,
    report: dict,
    report_path: Path,
    total_runs: int,
    started_at: float,
) -> dict:
    profiles = {}
    overall = "PASS"
    for idx, profile_key in enumerate(REPRESENTATION_ORDER, start=1):
        heartbeat("preflight_profile_start", done_runs=0, total_runs=total_runs, elapsed_sec=time.time() - started_at)
        _, metadata = get_cached_representation(splits, "train_core", profile_key)
        coverage = metadata["coverage_summary"]
        status = "PASS"
        issues: list[str] = []
        width_atr = metadata.get("width_atr")
        if width_atr is not None:
            if coverage["min_price_coord_atr"] < -width_atr - 1e-9 or coverage["max_price_coord_atr"] > width_atr + 1e-9:
                status = "ERROR"
                issues.append("corridor_out_of_range")
            if coverage["share_rows_0"] > 0.05:
                status = "ERROR"
                issues.append("empty_rows")
            elif coverage["selected_count_distribution"]["p50"] < 3.0:
                status = "WARNING"
                issues.append("low_median_coverage")
            if coverage["truncation_share"] > 0.25 and status != "ERROR":
                status = "WARNING"
                issues.append("high_truncation")
        profiles[profile_key] = {"status": status, "issues": issues, "metadata": metadata}
        if status == "ERROR":
            overall = "ERROR"
        elif status == "WARNING" and overall == "PASS":
            overall = "WARNING"
        report["representation_preflight"] = {"status": overall, "profiles": profiles}
        report["progress"] = {
            "done_runs": len(report.get("runs", [])),
            "total_runs": total_runs,
            "started_at": report.get("started_at", _utc_now_iso()),
            "finished_at": None,
            "elapsed_sec": time.time() - started_at,
            "preflight_profiles_done": idx,
            "preflight_profiles_total": len(REPRESENTATION_ORDER),
            "thread_count": CONFIG.xgb_threads,
        }
        save_report_json(report, report_path)
        heartbeat("preflight_profile_end", done_runs=0, total_runs=total_runs, elapsed_sec=time.time() - started_at)
    return {"status": overall, "profiles": profiles}


def run_distribution_audit_with_progress(
    splits: dict[str, pd.DataFrame],
    *,
    report: dict,
    report_path: Path,
    total_runs: int,
    started_at: float,
) -> dict:
    profiles = {}
    overall = "PASS"
    for idx, profile_key in enumerate(REPRESENTATION_ORDER, start=1):
        heartbeat("distribution_audit_profile_start", done_runs=0, total_runs=total_runs, elapsed_sec=time.time() - started_at)
        train_features, train_meta = get_cached_representation(splits, "train_core", profile_key)
        val_features, _ = get_cached_representation(splits, "val_stop", profile_key)
        holdout_features, _ = get_cached_representation(splits, "diagnostic_holdout", profile_key)
        train_vs_val = audit_feature_distribution_from_frames(train_features, val_features, train_meta, profile_key=profile_key)
        train_vs_holdout = audit_feature_distribution_from_frames(train_features, holdout_features, train_meta, profile_key=profile_key)
        profile_status = "PASS"
        if "ERROR" in {train_vs_val["status"], train_vs_holdout["status"]}:
            profile_status = "ERROR"
            overall = "ERROR"
        elif "WARNING" in {train_vs_val["status"], train_vs_holdout["status"]} and overall == "PASS":
            profile_status = "WARNING"
            overall = "WARNING"
        profiles[profile_key] = {
            "status": profile_status,
            "train_vs_val": train_vs_val,
            "train_vs_holdout": train_vs_holdout,
        }
        report["distribution_audit"] = {"status": overall, "profiles": profiles}
        report["progress"] = {
            "done_runs": len(report.get("runs", [])),
            "total_runs": total_runs,
            "started_at": report.get("started_at", _utc_now_iso()),
            "finished_at": None,
            "elapsed_sec": time.time() - started_at,
            "distribution_profiles_done": idx,
            "distribution_profiles_total": len(REPRESENTATION_ORDER),
            "thread_count": CONFIG.xgb_threads,
        }
        save_report_json(report, report_path)
        heartbeat("distribution_audit_profile_end", done_runs=0, total_runs=total_runs, elapsed_sec=time.time() - started_at)
    return {"status": overall, "profiles": profiles}


def thread_config_for(model_key: str) -> dict:
    if model_key.startswith("xgboost"):
        return {"thread_count": CONFIG.xgb_threads}
    return {"thread_count": 1}


def build_model(model_key: str, seed: int, thread_count: int) -> tuple[object, dict]:
    spec = build_model_registry()[model_key]
    if model_key == "xgboost_depth3":
        base = xgb.XGBRegressor(objective="reg:squarederror", max_depth=3, n_estimators=64, learning_rate=0.05, subsample=1.0, colsample_bytree=1.0, tree_method="hist", random_state=seed, n_jobs=thread_count)
    elif model_key == "xgboost_depth5":
        base = xgb.XGBRegressor(objective="reg:squarederror", max_depth=5, n_estimators=96, learning_rate=0.05, subsample=1.0, colsample_bytree=1.0, tree_method="hist", random_state=seed, n_jobs=thread_count)
    elif model_key == "hist_gradient_boosting":
        base = HistGradientBoostingRegressor(max_depth=spec["max_depth"], max_iter=spec["max_iter"], learning_rate=0.05, random_state=seed)
    elif model_key == "ridge":
        base = Ridge(alpha=spec["alpha"], random_state=seed)
    else:
        raise ValueError(f"Unsupported model_key: {model_key}")
    return MultiOutputRegressor(base), {"model_key": model_key, "seed": int(seed), "thread_count": int(thread_count), "params": spec}


def target_matrix(df: pd.DataFrame) -> np.ndarray:
    return df.loc[:, list(TARGET_COLUMNS)].apply(pd.to_numeric, errors="coerce").fillna(0.0).to_numpy(dtype=np.float32)


def _entry_log_ratio_frame(preds: np.ndarray) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "pred_entry_log_ratio_3": np.log1p(np.clip(preds[:, 0], 0.0, None)) - np.log1p(np.clip(preds[:, 1], 0.0, None)),
            "pred_entry_log_ratio_6": np.log1p(np.clip(preds[:, 2], 0.0, None)) - np.log1p(np.clip(preds[:, 3], 0.0, None)),
            "pred_entry_log_ratio_12": np.log1p(np.clip(preds[:, 4], 0.0, None)) - np.log1p(np.clip(preds[:, 5], 0.0, None)),
        }
    )


def _predictions_frame(preds: np.ndarray) -> pd.DataFrame:
    frame = pd.DataFrame(
        preds,
        columns=[
            "pred_entry_up_3",
            "pred_entry_dn_3",
            "pred_entry_up_6",
            "pred_entry_dn_6",
            "pred_entry_up_12",
            "pred_entry_dn_12",
        ],
    )
    return pd.concat([frame, _entry_log_ratio_frame(preds)], axis=1)


def fit_and_predict(*, model_key: str, seed: int, thread_count: int, train_features: pd.DataFrame, train_targets: np.ndarray, eval_frames: dict[str, pd.DataFrame], eval_features: dict[str, pd.DataFrame]) -> dict:
    model, metadata = build_model(model_key, seed, thread_count)
    model.fit(train_features.to_numpy(dtype=np.float32), train_targets)
    predictions_by_split = {}
    for split_name, frame in eval_features.items():
        preds = model.predict(frame.to_numpy(dtype=np.float32))
        predictions_by_split[split_name] = _predictions_frame(np.asarray(preds, dtype=np.float32))
    return {"predictions_by_split": predictions_by_split, "model_metadata": metadata}


def _corr_or_none(left: np.ndarray, right: np.ndarray) -> float | None:
    if len(left) < 2 or np.allclose(left, left[0]) or np.allclose(right, right[0]):
        return None
    return float(stats.spearmanr(left, right)[0])


def _split_metrics(y_true: np.ndarray, pred_frame: pd.DataFrame) -> dict:
    metrics = {}
    for horizon, (up_idx, dn_idx) in HORIZON_MAP.items():
        ratio_true = np.log1p(np.clip(y_true[:, up_idx], 0.0, None)) - np.log1p(np.clip(y_true[:, dn_idx], 0.0, None))
        metrics[f"entry_log_ratio_{horizon[1:]}"] = {"spearman": _corr_or_none(ratio_true, pred_frame[f"pred_entry_log_ratio_{horizon[1:]}"].to_numpy(dtype=float))}
        metrics[f"entry_up_{horizon[1:]}"] = {"spearman": _corr_or_none(y_true[:, up_idx], pred_frame[f"pred_entry_up_{horizon[1:]}"].to_numpy(dtype=float))}
        metrics[f"entry_dn_{horizon[1:]}"] = {"spearman": _corr_or_none(y_true[:, dn_idx], pred_frame[f"pred_entry_dn_{horizon[1:]}"].to_numpy(dtype=float))}
    return metrics


def enumerate_jobs(representation_keys: list[str] | None = None, model_keys: list[str] | None = None, seeds: list[int] | None = None) -> list[dict]:
    reps = representation_keys or list(REPRESENTATION_ORDER)
    models = model_keys or list(MODEL_ORDER)
    seeds_to_use = seeds or list(CONFIG.seeds)
    return [{"representation_key": rep, "model_key": model, "seed": int(seed)} for rep in reps for model in models for seed in seeds_to_use]


def job_key(job: dict) -> str:
    return f"{job['representation_key']}/{job['model_key']}/{job['seed']}"


def run_data_contract_smoke_check() -> dict:
    command = [str(PYTHON_BIN), str(SMOKE_CHECK_PATH)]
    started = time.time()
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    last_heartbeat = started
    while process.poll() is None:
        now = time.time()
        if now - last_heartbeat >= 30.0:
            heartbeat("smoke_check_wait", elapsed_sec=now - started)
            last_heartbeat = now
        time.sleep(1.0)
    stdout, stderr = process.communicate()
    return {
        "status": "PASS" if process.returncode == 0 else "FAIL",
        "returncode": int(process.returncode),
        "command": " ".join(command),
        "elapsed_sec": time.time() - started,
        "stdout": stdout[-4000:],
        "stderr": stderr[-4000:],
    }


def build_smoke_check_disclosure(legacy_smoke_check: dict, entry_based_target_contract_check: dict) -> dict:
    legacy_status = str(legacy_smoke_check.get("status", "UNKNOWN"))
    entry_status = str(entry_based_target_contract_check.get("status", "UNKNOWN"))
    if legacy_status == "PASS" and entry_status == "PASS":
        interpretation = "ALL_CONTRACT_CHECKS_PASS"
    elif legacy_status != "PASS" and entry_status == "PASS":
        interpretation = "LEGACY_SMOKE_FAIL_STAGE_CONTRACT_PASS"
    else:
        interpretation = "CONTRACT_CHECK_REQUIRES_REVIEW"
    return {
        "legacy_smoke_check_status": legacy_status,
        "entry_based_target_contract_status": entry_status,
        "legacy_returncode": legacy_smoke_check.get("returncode"),
        "interpretation": interpretation,
    }


def evaluate_job(job: dict, splits: dict[str, pd.DataFrame], report: dict) -> dict:
    rep_key = job["representation_key"]
    model_key = job["model_key"]
    seed = int(job["seed"])
    train_features, train_meta = get_cached_representation(splits, "train_core", rep_key)
    train_targets = target_matrix(splits["train_core"])
    eval_features = {}
    for split_name in SPLIT_ORDER:
        features, _ = get_cached_representation(splits, split_name, rep_key)
        eval_features[split_name] = features
    fitted = fit_and_predict(model_key=model_key, seed=seed, thread_count=thread_config_for(model_key)["thread_count"], train_features=train_features, train_targets=train_targets, eval_frames={name: splits[name] for name in SPLIT_ORDER}, eval_features=eval_features)
    split_metrics = {split_name: _split_metrics(target_matrix(splits[split_name]), fitted["predictions_by_split"][split_name]) for split_name in SPLIT_ORDER}
    metrics_rows = []
    for split_name, metrics in split_metrics.items():
        for target_name, payload in metrics.items():
            metrics_rows.append({"representation_key": rep_key, "model_key": model_key, "seed": seed, "split_name": split_name, "target_name": target_name.rsplit("_", 1)[0], "horizon": f"H{target_name.rsplit('_', 1)[1]}", "spearman": payload["spearman"], "elapsed_sec": 0.0})
    preview = fitted["predictions_by_split"]["val_stop"].head(8).copy()
    preview.insert(0, "split_name", "val_stop")
    preview.insert(0, "seed", seed)
    preview.insert(0, "model_key", model_key)
    preview.insert(0, "representation_key", rep_key)
    preview["time"] = splits["val_stop"]["time"].head(len(preview)).astype(str).to_list()
    preview["entry_time"] = splits["val_stop"].get("entry_time", pd.Series([""] * len(preview))).head(len(preview)).astype(str).to_list()
    for column in TARGET_COLUMNS:
        preview[column] = pd.to_numeric(splits["val_stop"][column].head(len(preview)), errors="coerce").fillna(0.0).to_list()
    return {
        "job_key": job_key(job),
        "representation_key": rep_key,
        "model_key": model_key,
        "seed": seed,
        "elapsed_sec": 0.0,
        "representation_metadata": train_meta,
        "model_metadata": fitted["model_metadata"],
        "coverage_penalty": run_representation_preflight(splits["train_core"], rep_key)["status"] != "PASS",
        "split_metrics": split_metrics,
        "rows_preview": preview,
        "metrics_rows": metrics_rows,
    }


def save_report_json(report: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    serializable = json.loads(json.dumps(report, ensure_ascii=True, indent=2, default=_json_default))
    tmp.write_text(json.dumps(serializable, ensure_ascii=True, indent=2), encoding="utf-8")
    tmp.replace(path)


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


def write_metrics_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False, sep=";")


def write_rows_csv(rows: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows.to_csv(path, index=False, sep=";")


def _collect_rows_preview(runs: list[dict]) -> pd.DataFrame:
    frames = []
    for run in runs:
        preview = run.get("rows_preview")
        if isinstance(preview, pd.DataFrame):
            frames.append(preview)
        elif isinstance(preview, list):
            frames.append(pd.DataFrame(preview))
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def summarize_results(report: dict) -> dict:
    per_model = {}
    directional_models = set()
    weak_models = set()
    for model_key in MODEL_ORDER:
        model_runs = [run for run in report.get("runs", []) if run.get("model_key") == model_key]
        if not model_runs:
            continue
        baseline_runs = [run for run in model_runs if run["representation_key"] == "all100"]
        baseline_log_best = _best_metric(
            baseline_runs,
            split_name="val_stop",
            target_names=("entry_log_ratio",),
        )
        baseline_amp_best = _best_metric(
            baseline_runs,
            split_name="val_stop",
            target_names=("entry_up", "entry_dn"),
        )
        best_val = None
        best_holdout = None
        for run in model_runs:
            val_log = _best_metric([run], split_name="val_stop", target_names=("entry_log_ratio",))
            val_amp = _best_metric([run], split_name="val_stop", target_names=("entry_up", "entry_dn"))
            holdout_log = _metric_for(
                run,
                split_name="diagnostic_holdout",
                target_name=val_log["target_name"],
                horizon=val_log["horizon"],
            )
            holdout_amp = _best_metric([run], split_name="diagnostic_holdout", target_names=("entry_up", "entry_dn"))
            val_record = {
                **val_log,
                "representation_key": run["representation_key"],
                "amplitude_only": val_amp["score"] > val_log["score"],
                "amplitude_score": val_amp["score"],
                "coverage_penalty": run.get("coverage_penalty", False),
                "uplift_vs_all100": val_log["score"] - baseline_log_best["score"],
                "amplitude_uplift_vs_all100": val_amp["score"] - baseline_amp_best["score"],
            }
            if best_val is None or val_record["score"] > best_val["score"]:
                best_val = val_record
            holdout_record = {
                **holdout_log,
                "representation_key": run["representation_key"],
            }
            if best_holdout is None or holdout_record["score"] > best_holdout["score"]:
                best_holdout = holdout_record
            if run["representation_key"] != "all100" and val_log["score"] > baseline_log_best["score"] and val_log["score"] >= 0.10 and holdout_log["score"] > 0.0:
                directional_models.add(model_key)
            log_uplift = val_log["score"] > baseline_log_best["score"]
            amp_uplift = val_amp["score"] > baseline_amp_best["score"]
            disclosure_not_gone = holdout_log["score"] > 0.0 or holdout_amp["score"] > 0.0
            if run["representation_key"] != "all100" and (log_uplift or amp_uplift) and val_amp["score"] > val_log["score"] and disclosure_not_gone:
                weak_models.add(model_key)
        per_model[model_key] = {"best_val_stop": best_val, "best_disclosure": best_holdout}
    status = "NO_SIGNAL_FOUND"
    if len(directional_models) >= 2:
        status = "PASS_DIAGNOSTIC"
    elif len(weak_models) >= 2:
        status = "WEAK_TRACE_FOUND"
    return {"status": status, "best_by_model": per_model, "best_by_representation": _best_by_representation(report), "coverage_warnings": _coverage_warnings(report)}


def _best_metric(runs: list[dict], *, split_name: str, target_names: tuple[str, ...]) -> dict:
    best = {"target_name": target_names[0], "horizon": "H3", "score": 0.0}
    for run in runs:
        metrics = run.get("split_metrics", {}).get(split_name, {})
        for target_name in target_names:
            for horizon in SUMMARY_HORIZONS:
                score = metrics.get(f"{target_name}_{horizon}", {}).get("spearman")
                score = float(score) if score is not None else 0.0
                if score > best["score"]:
                    best = {"target_name": target_name, "horizon": f"H{horizon}", "score": score}
    return best


def _metric_for(run: dict, *, split_name: str, target_name: str, horizon: str) -> dict:
    horizon_suffix = horizon.removeprefix("H")
    score = run.get("split_metrics", {}).get(split_name, {}).get(f"{target_name}_{horizon_suffix}", {}).get("spearman")
    return {"target_name": target_name, "horizon": horizon, "score": float(score) if score is not None else 0.0}


def _best_by_representation(report: dict) -> dict:
    by_rep = {}
    for rep_key in REPRESENTATION_ORDER:
        runs = [run for run in report.get("runs", []) if run.get("representation_key") == rep_key]
        if not runs:
            continue
        by_rep[rep_key] = {
            "best_model_val_stop": _best_model_metric(runs, split_name="val_stop", target_names=("entry_log_ratio",)),
            "best_model_disclosure": _best_model_metric(runs, split_name="diagnostic_holdout", target_names=("entry_log_ratio",)),
            "role": build_representation_registry()[rep_key]["role"],
        }
    return by_rep


def _best_model_metric(runs: list[dict], *, split_name: str, target_names: tuple[str, ...]) -> dict:
    best = {"model_key": "", "target_name": target_names[0], "horizon": "H3", "score": 0.0}
    for run in runs:
        current = _best_metric([run], split_name=split_name, target_names=target_names)
        if current["score"] > best["score"]:
            best = {"model_key": run["model_key"], **current}
    return best


def _coverage_warnings(report: dict) -> dict:
    warnings = {}
    for run in report.get("runs", []):
        rep_key = run["representation_key"]
        if run.get("coverage_penalty"):
            warnings[rep_key] = run["representation_metadata"]["coverage_summary"]
    return warnings


def decide_stage_status(summary: dict) -> str:
    return summary["status"]


def run_benchmark(args: argparse.Namespace, report_path: Path = REPORT_JSON_PATH, metrics_path: Path = REPORT_METRICS_PATH, rows_path: Path = REPORT_ROWS_PATH) -> dict:
    total_start = time.time()
    jobs = enumerate_jobs()
    heartbeat("runner_start", done_runs=0, total_runs=len(jobs), elapsed_sec=0.0)
    heartbeat("split_load_start", done_runs=0, total_runs=len(jobs), elapsed_sec=0.0)
    splits = load_entry_based_splits(target_mode=CONFIG.target_mode_default)
    heartbeat("split_load_end", done_runs=0, total_runs=len(jobs), elapsed_sec=time.time() - total_start)
    report = load_or_init_report(report_path, resume=args.resume)
    report.setdefault("started_at", _utc_now_iso())
    report.setdefault("runs", [])
    report["target_mode"] = CONFIG.target_mode_default
    report.setdefault("entry_based_target_contract_check", validate_entry_based_target_contract(splits, target_mode=CONFIG.target_mode_default))
    report.setdefault("split_summary", build_split_summary(splits))
    report["progress"] = {
        "done_runs": len(report["runs"]),
        "total_runs": len(jobs),
        "started_at": report["started_at"],
        "finished_at": None,
        "elapsed_sec": time.time() - total_start,
        "thread_count": CONFIG.xgb_threads,
        "phase": "post_split_load",
    }
    save_report_json(report, report_path)
    if "data_contract_smoke_check" not in report:
        heartbeat("smoke_check_start", done_runs=len(report["runs"]), total_runs=len(jobs), elapsed_sec=time.time() - total_start)
        report["data_contract_smoke_check"] = run_data_contract_smoke_check()
        report["smoke_check_disclosure"] = build_smoke_check_disclosure(
            report["data_contract_smoke_check"],
            report["entry_based_target_contract_check"],
        )
        report["progress"]["elapsed_sec"] = time.time() - total_start
        report["progress"]["phase"] = "post_smoke_check"
        save_report_json(report, report_path)
        heartbeat("smoke_check_end", done_runs=len(report["runs"]), total_runs=len(jobs), elapsed_sec=time.time() - total_start)
    elif "smoke_check_disclosure" not in report:
        report["smoke_check_disclosure"] = build_smoke_check_disclosure(
            report["data_contract_smoke_check"],
            report["entry_based_target_contract_check"],
        )
        save_report_json(report, report_path)
    if "representation_preflight" not in report:
        report["representation_preflight"] = run_all_preflight_with_progress(
            splits,
            report=report,
            report_path=report_path,
            total_runs=len(jobs),
            started_at=total_start,
        )
    if "distribution_audit" not in report:
        report["distribution_audit"] = run_distribution_audit_with_progress(
            splits,
            report=report,
            report_path=report_path,
            total_runs=len(jobs),
            started_at=total_start,
        )
    done_keys = {run["job_key"] for run in report["runs"] if "job_key" in run}
    heartbeat("preflight_end", done_runs=len(done_keys), total_runs=len(jobs), elapsed_sec=time.time() - total_start)
    for idx, job in enumerate(jobs, start=1):
        key = job_key(job)
        if args.resume and key in done_keys:
            continue
        elapsed = time.time() - total_start
        eta = (elapsed / max(len(report["runs"]), 1)) * max(len(jobs) - len(report["runs"]), 0) if report["runs"] else None
        heartbeat("job_start", done_runs=len(report["runs"]), total_runs=len(jobs), elapsed_sec=elapsed, eta_sec=eta)
        started = time.time()
        result = evaluate_job(job, splits, report)
        result["elapsed_sec"] = time.time() - started
        for row in result["metrics_rows"]:
            row["elapsed_sec"] = result["elapsed_sec"]
        report["runs"].append(result)
        report["progress"] = {"done_runs": len(report["runs"]), "total_runs": len(jobs), "started_at": report.get("started_at", _utc_now_iso()), "finished_at": None, "elapsed_sec": time.time() - total_start, "eta_sec": eta, "thread_count": CONFIG.xgb_threads}
        save_report_json(report, report_path)
        write_metrics_csv([row for run in report["runs"] for row in run.get("metrics_rows", [])], metrics_path)
        write_rows_csv(_collect_rows_preview(report["runs"]), rows_path)
        heartbeat("job_end", done_runs=len(report["runs"]), total_runs=len(jobs), elapsed_sec=time.time() - total_start)
    summary = summarize_results(report)
    report["summary"] = summary
    report["status"] = decide_stage_status(summary)
    report["progress"] = {"done_runs": len(report["runs"]), "total_runs": len(jobs), "started_at": report.get("started_at", _utc_now_iso()), "finished_at": _utc_now_iso(), "elapsed_sec": time.time() - total_start, "thread_count": CONFIG.xgb_threads}
    save_report_json(report, report_path)
    write_metrics_csv([row for run in report["runs"] for row in run.get("metrics_rows", [])], metrics_path)
    write_rows_csv(_collect_rows_preview(report["runs"]), rows_path)
    heartbeat("runner_end", done_runs=len(report["runs"]), total_runs=len(jobs), elapsed_sec=time.time() - total_start)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    if not args.entry_based_updn_fractal_selection_ablation:
        parser.print_help()
        return 0
    run_benchmark(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
