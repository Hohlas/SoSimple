from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.multioutput import MultiOutputRegressor
import xgboost as xgb

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from ML.baseline import benchmark_next_open_entry_updn_foundation as entry_foundation
from ML.lib_pic_path_reaction_feature_bank import build_lib_pic_path_reaction_feature_bank


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORTS_DIR = PROJECT_ROOT / "ML" / "reports"
PYTHON_BIN = PROJECT_ROOT / ".venv" / "bin" / "python"
SMOKE_CHECK_PATH = PROJECT_ROOT / "statistics" / "data_contract_smoke_check.py"
REPORT_JSON_PATH = REPORTS_DIR / "entry_based_updn_price_feature_matrix.json"
REPORT_ROWS_PATH = REPORTS_DIR / "entry_based_updn_price_feature_matrix_rows.csv"

PROFILE_KEYS = [
    "structure_full",
    "structure_full_relative_price",
    "structure_full_distance_atr",
    "structure_full_price_coord_atr",
    "structure_full_short_updn_source_audited",
    "structure_full_path_reaction",
    "structure_full_price_atr_scaled",
]
PRIMARY_PROFILE_KEYS = [
    "structure_full_relative_price",
    "structure_full_price_coord_atr",
    "structure_full_path_reaction",
]
SECONDARY_PROFILE_KEYS = [
    "structure_full_distance_atr",
    "structure_full_short_updn_source_audited",
]
DIAGNOSTIC_PROFILE_KEYS = ["structure_full_price_atr_scaled"]


@dataclass(frozen=True)
class EntryPriceMatrixConfig:
    profile_keys: tuple[str, ...] = tuple(PROFILE_KEYS)
    seeds: tuple[int, ...] = (42, 77, 123)
    xgb_threads: int = 24
    report_json_path: Path = REPORT_JSON_PATH
    report_rows_path: Path = REPORT_ROWS_PATH
    resume_default: bool = True


CONFIG = EntryPriceMatrixConfig()
FRACTAL_PREFIX = "fractal"
FRACTAL_SEP = ":"
FRACTAL_PRICE_INDEX = 1
FRACTAL_DIRECTION_INDEX = 2
FRACTAL_UP12_INDEX = 11
FRACTAL_DN12_INDEX = 12
FRACTAL_UP3_INDEX = 17
FRACTAL_DN3_INDEX = 18
FRACTAL_UP6_INDEX = 19
FRACTAL_DN6_INDEX = 20
FRACTAL_ATR_INDEX = 21
FRACTAL_SHIFT_INDEX = 22
SHORT_UPDN_HORIZONS = (3, 6, 12)
STRUCTURE_FIELD_INDEX = {
    "direction": 2,
    "front": 3,
    "back": 4,
    "strong": 5,
    "break": 6,
    "reverse": 7,
    "power": 8,
    "count": 9,
    "impulse": 10,
    "shift": 22,
}
ROW_TIME_FEATURE_NAMES = ["hour_sin", "hour_cos", "dow_sin", "dow_cos"]
FORBIDDEN_TOP_LEVEL_TARGET_PREFIXES = (
    "entry_up_",
    "entry_dn_",
    "entry_log_ratio_",
    "up_",
    "dn_",
)
PROFILE_HYPOTHESES = {
    "structure_full": "Control baseline with structure-only inputs.",
    "structure_full_relative_price": "Relative fractal price may add local positional signal after entry.",
    "structure_full_distance_atr": "Signed and absolute ATR distance may explain post-entry movement ranking.",
    "structure_full_price_coord_atr": "ATR-normalized price coordinates may add richer price geometry.",
    "structure_full_short_updn_source_audited": "Short-horizon MT-accumulated Up/Dn may carry local reaction signal into the executable entry.",
    "structure_full_path_reaction": "Aggregated path-reaction history may add post-entry predictive value.",
    "structure_full_price_atr_scaled": "Price/ATR regime may reveal whether only scale, not level mechanics, explains weak traces.",
}
TARGET_COLUMNS = (
    "entry_up_3",
    "entry_dn_3",
    "entry_up_6",
    "entry_dn_6",
    "entry_up_12",
    "entry_dn_12",
)


def build_profile_registry() -> dict[str, dict]:
    return {
        "structure_full": {"role": "baseline", "added_blocks": []},
        "structure_full_relative_price": {"role": "primary", "added_blocks": ["relative_price"]},
        "structure_full_distance_atr": {"role": "secondary", "added_blocks": ["distance_atr"]},
        "structure_full_price_coord_atr": {"role": "primary", "added_blocks": ["price_coord_atr"]},
        "structure_full_short_updn_source_audited": {
            "role": "secondary",
            "added_blocks": ["short_updn_source_audited"],
        },
        "structure_full_path_reaction": {"role": "primary", "added_blocks": ["path_reaction"]},
        "structure_full_price_atr_scaled": {"role": "diagnostic-only", "added_blocks": ["price_atr_scaled"]},
    }


def should_resume(default: bool = True) -> bool:
    return bool(default)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Bounded benchmark for entry-based Up/Dn price-feature matrix."
    )
    parser.add_argument(
        "--entry-based-updn-price-feature-matrix",
        action="store_true",
        help="Run the entry-based Up/Dn price-feature matrix benchmark.",
    )
    resume_group = parser.add_mutually_exclusive_group()
    resume_group.add_argument(
        "--resume",
        dest="resume",
        action="store_true",
        default=CONFIG.resume_default,
        help="Resume from an existing JSON report.",
    )
    resume_group.add_argument(
        "--no-resume",
        dest="resume",
        action="store_false",
        help="Start the benchmark from scratch.",
    )
    return parser


def _fractal_columns(df: pd.DataFrame) -> list[str]:
    return sorted(
        [column for column in df.columns if column.startswith(FRACTAL_PREFIX)],
        key=lambda name: int(name.removeprefix(FRACTAL_PREFIX)),
    )


def _fractal_parts(raw: object) -> list[str]:
    text = "" if pd.isna(raw) else str(raw).strip()
    return text.split(FRACTAL_SEP) if text else []


def _fractal_float(raw: object, index: int) -> float:
    parts = _fractal_parts(raw)
    try:
        value = float(parts[index])
    except (IndexError, TypeError, ValueError):
        return 0.0
    return float(value) if np.isfinite(value) else 0.0


def _safe_atr_series(df: pd.DataFrame) -> pd.Series:
    atr = pd.to_numeric(df.get("ATR", 0.0), errors="coerce").fillna(0.0).astype(float)
    return atr.clip(lower=1e-6)


def _fractal_price_frame(df: pd.DataFrame) -> pd.DataFrame:
    columns = {
        f"price_{column}": df[column].map(lambda raw: _fractal_float(raw, FRACTAL_PRICE_INDEX))
        for column in _fractal_columns(df)
    }
    return pd.DataFrame(columns, index=df.index)


def _signed_log1p(values: pd.Series) -> pd.Series:
    return np.sign(values) * np.log1p(np.abs(values))


def _build_structure_full_block(df: pd.DataFrame) -> pd.DataFrame:
    out = {}
    fractal_columns = _fractal_columns(df)
    for column in fractal_columns:
        parts = df[column].fillna("").astype(str).str.split(FRACTAL_SEP, expand=True)
        for field, index in STRUCTURE_FIELD_INDEX.items():
            if index < parts.shape[1]:
                values = pd.to_numeric(parts[index], errors="coerce").fillna(0.0).astype(np.float32)
            else:
                values = pd.Series(0.0, index=df.index, dtype=np.float32)
            if field == "shift":
                values = np.log1p(values.clip(lower=0.0)).astype(np.float32)
            out[f"{column}.{field}"] = values

    parsed_time = pd.to_datetime(df.get("time", ""), format=entry_foundation.CONFIG.project_time_format, errors="coerce")
    hour = parsed_time.dt.hour.fillna(0).astype(float)
    dow = parsed_time.dt.dayofweek.fillna(0).astype(float)
    out["hour_sin"] = np.sin(2.0 * np.pi * hour / 24.0).astype(np.float32)
    out["hour_cos"] = np.cos(2.0 * np.pi * hour / 24.0).astype(np.float32)
    out["dow_sin"] = np.sin(2.0 * np.pi * dow / 7.0).astype(np.float32)
    out["dow_cos"] = np.cos(2.0 * np.pi * dow / 7.0).astype(np.float32)
    return pd.DataFrame(out, index=df.index)


def build_relative_price_block(df: pd.DataFrame) -> pd.DataFrame:
    prices = _fractal_price_frame(df)
    base = prices.get("price_fractal0", pd.Series(0.0, index=df.index))
    atr = _safe_atr_series(df)
    out = {}
    for column in _fractal_columns(df):
        rel = (prices[f"price_{column}"] - base) / atr
        out[f"rel_price_atr_{column}"] = rel.astype(np.float32)
    return pd.DataFrame(out, index=df.index)


def build_distance_atr_block(df: pd.DataFrame) -> pd.DataFrame:
    relative = build_relative_price_block(df)
    out = {}
    for column in _fractal_columns(df):
        src = relative[f"rel_price_atr_{column}"]
        out[f"distance_atr_signed_{column}"] = src.astype(np.float32)
        out[f"distance_atr_abs_{column}"] = src.abs().astype(np.float32)
    return pd.DataFrame(out, index=df.index)


def build_price_coord_atr_block(df: pd.DataFrame) -> pd.DataFrame:
    relative = build_relative_price_block(df)
    out = {}
    for column in _fractal_columns(df):
        out[f"price_coord_atr_{column}"] = _signed_log1p(relative[f"rel_price_atr_{column}"]).astype(np.float32)
    return pd.DataFrame(out, index=df.index)


def audit_updn_feature_source(
    df: pd.DataFrame,
    used_top_level_columns: list[str] | None = None,
) -> dict:
    forbidden = list(used_top_level_columns or [])
    return {
        "status": "pass" if not forbidden else "fail",
        "uses_only_fractal_fields": not forbidden,
        "forbidden_top_level_columns": forbidden,
        "fractal_fields_used": ["Up3", "Dn3", "Up6", "Dn6", "Up12", "Dn12"],
        "availability": "MT-accumulated fractal fields known at signal_time",
    }


def build_short_updn_source_audited_block(df: pd.DataFrame, source_audit: dict) -> pd.DataFrame:
    if source_audit.get("status") != "pass":
        raise ValueError("Up/Dn source audit failed")

    out = {}
    for column in _fractal_columns(df):
        direction = df[column].map(lambda raw: _fractal_float(raw, FRACTAL_DIRECTION_INDEX))
        for horizon, up_idx, dn_idx in (
            (3, FRACTAL_UP3_INDEX, FRACTAL_DN3_INDEX),
            (6, FRACTAL_UP6_INDEX, FRACTAL_DN6_INDEX),
            (12, FRACTAL_UP12_INDEX, FRACTAL_DN12_INDEX),
        ):
            up = df[column].map(lambda raw, idx=up_idx: _fractal_float(raw, idx))
            dn = df[column].map(lambda raw, idx=dn_idx: _fractal_float(raw, idx))
            fav = np.where(direction >= 0, up, dn)
            adv = np.where(direction >= 0, dn, up)
            out[f"short_updn_fav_{horizon}_{column}"] = fav.astype(np.float32)
            out[f"short_updn_adv_{horizon}_{column}"] = adv.astype(np.float32)
            out[f"short_updn_edge_{horizon}_{column}"] = (fav - adv).astype(np.float32)
    return pd.DataFrame(out, index=df.index)


def build_price_atr_scaled_block(df: pd.DataFrame) -> pd.DataFrame:
    prices = _fractal_price_frame(df)
    atr = _safe_atr_series(df)
    out = {}
    for column in _fractal_columns(df):
        scaled = np.arcsinh(prices[f"price_{column}"] / atr)
        out[f"price_atr_scaled_{column}"] = scaled.astype(np.float32)
    return pd.DataFrame(out, index=df.index)


def build_path_reaction_block(df: pd.DataFrame) -> pd.DataFrame:
    full = build_lib_pic_path_reaction_feature_bank(df)
    columns = [name for name in full.columns if name.startswith("pic_path_")]
    return full.loc[:, columns].copy()


def build_profile_features(df: pd.DataFrame, profile_key: str) -> tuple[pd.DataFrame, dict]:
    registry = build_profile_registry()
    if profile_key not in registry:
        raise ValueError(f"Unknown profile_key: {profile_key}")

    metadata = {
        "profile_key": profile_key,
        "added_blocks": list(registry[profile_key]["added_blocks"]),
        "block_hypothesis": PROFILE_HYPOTHESES[profile_key],
    }
    blocks = [_build_structure_full_block(df)]

    if profile_key == "structure_full_relative_price":
        blocks.append(build_relative_price_block(df))
    elif profile_key == "structure_full_distance_atr":
        blocks.append(build_distance_atr_block(df))
    elif profile_key == "structure_full_price_coord_atr":
        blocks.append(build_price_coord_atr_block(df))
    elif profile_key == "structure_full_short_updn_source_audited":
        audit = audit_updn_feature_source(df)
        blocks.append(build_short_updn_source_audited_block(df, audit))
        metadata["updn_source_audit"] = audit
        metadata["transform"] = {"horizons": list(SHORT_UPDN_HORIZONS), "direction_mapping": "fav_adv_by_fractal_direction"}
    elif profile_key == "structure_full_path_reaction":
        blocks.append(build_path_reaction_block(df))
    elif profile_key == "structure_full_price_atr_scaled":
        blocks.append(build_price_atr_scaled_block(df))
        metadata["transform"] = {"name": "asinh"}

    features = pd.concat(blocks, axis=1)
    metadata["feature_names"] = list(features.columns)
    metadata["feature_count"] = int(features.shape[1])
    return features, metadata


def load_entry_based_splits() -> dict[str, pd.DataFrame]:
    heartbeat("split_load_start")
    source_splits = entry_foundation.load_research_splits()
    heartbeat("split_rebuild_start")
    ohlc = entry_foundation.load_ohlc()
    rebuilt = {
        split_name: entry_foundation.rebuild_entry_targets(
            df=frame,
            ohlc=ohlc,
            horizons=(3, 6, 12),
        )
        for split_name, frame in source_splits.items()
    }
    heartbeat("split_rebuild_end")
    return rebuilt


def target_matrix(df: pd.DataFrame) -> np.ndarray:
    missing = [column for column in TARGET_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"Missing target columns: {missing}")
    return (
        df.loc[:, list(TARGET_COLUMNS)]
        .apply(pd.to_numeric, errors="coerce")
        .fillna(0.0)
        .to_numpy(dtype=np.float32)
    )


def _find_forbidden_feature_columns(columns: list[str]) -> list[str]:
    return [
        column
        for column in columns
        if any(column.startswith(prefix) for prefix in FORBIDDEN_TOP_LEVEL_TARGET_PREFIXES)
    ]


def profile_matrix(df: pd.DataFrame, profile_key: str) -> tuple[np.ndarray, dict]:
    features, metadata = build_profile_features(df, profile_key)
    forbidden = _find_forbidden_feature_columns(list(features.columns))
    if forbidden:
        raise ValueError(f"Forbidden target columns detected: {sorted(set(forbidden))}")
    matrix = features.apply(pd.to_numeric, errors="coerce").fillna(0.0).to_numpy(dtype=np.float32)
    metadata = dict(metadata)
    metadata["feature_names_sha256"] = hashlib.sha256(
        "\n".join(metadata["feature_names"]).encode("utf-8")
    ).hexdigest()
    metadata["feature_count"] = int(matrix.shape[1])
    return matrix, metadata


def make_xgb_model_params(seed: int, xgb_threads: int) -> dict:
    return {
        "objective": "reg:squarederror",
        "max_depth": 3,
        "n_estimators": 64,
        "learning_rate": 0.05,
        "subsample": 1.0,
        "colsample_bytree": 1.0,
        "tree_method": "hist",
        "random_state": int(seed),
        "n_jobs": int(xgb_threads),
    }


def heartbeat(stage: str, done_runs: int | None = None, total_runs: int | None = None) -> None:
    parts = [f"[entry-price-matrix] {stage}"]
    if done_runs is not None and total_runs is not None:
        parts.append(f"{done_runs}/{total_runs}")
    print(" | ".join(parts), flush=True)


def write_report_atomic(report: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(report, ensure_ascii=True, indent=2), encoding="utf-8")
    tmp_path.replace(path)


def load_existing_report(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def completed_run_keys(report: dict) -> set[tuple[str, int]]:
    return {
        (str(run["profile_key"]), int(run["seed"]))
        for run in report.get("runs", [])
        if "profile_key" in run and "seed" in run
    }


def _utc_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def _run_data_contract_smoke_check() -> dict:
    command = [str(PYTHON_BIN), str(SMOKE_CHECK_PATH)]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    return {
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "command": " ".join(command),
        "returncode": int(completed.returncode),
        "stdout": completed.stdout[-4000:],
        "stderr": completed.stderr[-4000:],
    }


def run_preflight(split_frames: dict[str, pd.DataFrame]) -> dict:
    started_at = _utc_now_iso()
    start = time.time()
    heartbeat("preflight_start", done_runs=0, total_runs=len(CONFIG.profile_keys) * len(CONFIG.seeds))
    smoke = _run_data_contract_smoke_check()
    report = {
        "status": "RUNNING",
        "artifact_status": "DIAGNOSTIC_ONLY",
        "started_at": started_at,
        "finished_at": None,
        "elapsed_sec": max(time.time() - start, 0.0),
        "split_row_counts": {name: int(len(frame)) for name, frame in split_frames.items()},
        "data_contract_smoke_check": smoke,
        "runs": [],
        "progress": {
            "done_runs": 0,
            "total_runs": len(CONFIG.profile_keys) * len(CONFIG.seeds),
            "elapsed_sec": max(time.time() - start, 0.0),
        },
    }
    heartbeat("preflight_end", done_runs=0, total_runs=report["progress"]["total_runs"])
    return report


def _safe_float(value: object) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if not np.isfinite(result):
        return None
    return result


def _entry_log_ratio_from_targets(targets: np.ndarray) -> dict[str, np.ndarray]:
    return {
        "H3": np.log1p(np.clip(targets[:, 0], 0.0, None)) - np.log1p(np.clip(targets[:, 1], 0.0, None)),
        "H6": np.log1p(np.clip(targets[:, 2], 0.0, None)) - np.log1p(np.clip(targets[:, 3], 0.0, None)),
        "H12": np.log1p(np.clip(targets[:, 4], 0.0, None)) - np.log1p(np.clip(targets[:, 5], 0.0, None)),
    }


def _corr_or_none(left: np.ndarray, right: np.ndarray) -> float | None:
    if len(left) < 2:
        return None
    if np.allclose(left, left[0]) or np.allclose(right, right[0]):
        return None
    return _safe_float(stats.spearmanr(left, right)[0])


def _split_metric_bundle(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    ratios_true = _entry_log_ratio_from_targets(y_true)
    ratios_pred = _entry_log_ratio_from_targets(y_pred)
    return {
        "entry_log_ratio": {
            horizon: {"spearman": _corr_or_none(ratios_true[horizon], ratios_pred[horizon])}
            for horizon in ("H3", "H6", "H12")
        },
        "entry_up": {
            "H3": {"spearman": _corr_or_none(y_true[:, 0], y_pred[:, 0])},
            "H6": {"spearman": _corr_or_none(y_true[:, 2], y_pred[:, 2])},
            "H12": {"spearman": _corr_or_none(y_true[:, 4], y_pred[:, 4])},
        },
        "entry_dn": {
            "H3": {"spearman": _corr_or_none(y_true[:, 1], y_pred[:, 1])},
            "H6": {"spearman": _corr_or_none(y_true[:, 3], y_pred[:, 3])},
            "H12": {"spearman": _corr_or_none(y_true[:, 5], y_pred[:, 5])},
        },
    }


def _build_rows_csv_preview(split_frames: dict[str, pd.DataFrame], limit: int = 12) -> list[dict]:
    preview: list[dict] = []
    for split_name, frame in split_frames.items():
        if not isinstance(frame, pd.DataFrame):
            continue
        take = frame.head(limit).copy()
        narrow = pd.DataFrame(
            {
                "split_name": split_name,
                "time": take.get("time", "").astype(str),
                "entry_up_3": pd.to_numeric(take.get("entry_up_3", 0.0), errors="coerce").fillna(0.0),
                "entry_dn_3": pd.to_numeric(take.get("entry_dn_3", 0.0), errors="coerce").fillna(0.0),
                "entry_up_6": pd.to_numeric(take.get("entry_up_6", 0.0), errors="coerce").fillna(0.0),
                "entry_dn_6": pd.to_numeric(take.get("entry_dn_6", 0.0), errors="coerce").fillna(0.0),
                "entry_up_12": pd.to_numeric(take.get("entry_up_12", 0.0), errors="coerce").fillna(0.0),
                "entry_dn_12": pd.to_numeric(take.get("entry_dn_12", 0.0), errors="coerce").fillna(0.0),
            }
        )
        preview.extend(narrow.to_dict(orient="records"))
    return preview


def _profile_split_payload(
    split_frames: dict[str, pd.DataFrame],
    profile_key: str,
) -> dict[str, tuple[np.ndarray, np.ndarray, dict]]:
    profile_cache = split_frames.setdefault("_profile_cache", {})
    if profile_key in profile_cache:
        return profile_cache[profile_key]

    payload = {}
    for split_name in ("train_core", "val_stop", "diagnostic_holdout", "low_n_disclosure"):
        frame = split_frames.get(split_name, split_frames["train_core"])
        matrix, feature_meta = profile_matrix(frame, profile_key)
        targets = target_matrix(frame)
        payload[split_name] = (matrix, targets, feature_meta)
    profile_cache[profile_key] = payload
    return payload


def evaluate_profile_seed(profile_key: str, seed: int, split_frames: dict[str, pd.DataFrame]) -> dict:
    started = time.time()
    payload = _profile_split_payload(split_frames, profile_key)
    train_matrix, train_targets, feature_meta = payload["train_core"]
    model = MultiOutputRegressor(xgb.XGBRegressor(**make_xgb_model_params(seed=seed, xgb_threads=CONFIG.xgb_threads)))
    model.fit(train_matrix, train_targets)

    metrics_by_split = {}
    for split_name in ("train_core", "val_stop", "diagnostic_holdout", "low_n_disclosure"):
        matrix, targets, _ = payload[split_name]
        preds = model.predict(matrix)
        metrics_by_split[split_name] = _split_metric_bundle(targets, preds)

    val_side_metrics = metrics_by_split["val_stop"]
    val_side_trace = max(
        [metric["spearman"] or 0.0 for group in ("entry_up", "entry_dn") for metric in val_side_metrics[group].values()],
        default=0.0,
    )
    return {
        "profile_key": profile_key,
        "profile_role": build_profile_registry()[profile_key]["role"],
        "block_hypothesis": PROFILE_HYPOTHESES[profile_key],
        "seed": int(seed),
        "elapsed_sec": max(time.time() - started, 0.0),
        "feature_metadata": feature_meta,
        "val_stop_metrics": metrics_by_split["val_stop"],
        "diagnostic_holdout_metrics": metrics_by_split["diagnostic_holdout"],
        "low_n_disclosure_metrics": metrics_by_split["low_n_disclosure"],
        "train_core_metrics": metrics_by_split["train_core"],
        "val_stop_entry_side_trace": val_side_trace,
        "rows_csv_preview": _build_rows_csv_preview(split_frames),
    }


def summarize_profiles(report: dict) -> dict:
    roles = {key: value["role"] for key, value in build_profile_registry().items()}
    baseline_runs = [run for run in report.get("runs", []) if run.get("profile_key") == "structure_full"]
    baseline_best = max(
        [
            max((metric["spearman"] or 0.0) for metric in run.get("val_stop_metrics", {}).get("entry_log_ratio", {}).values())
            for run in baseline_runs
        ],
        default=0.0,
    )
    block_matrix = {}
    weak_trace = False
    strong_primary = False
    for profile_key in PROFILE_KEYS:
        runs = [run for run in report.get("runs", []) if run.get("profile_key") == profile_key]
        if not runs:
            continue
        best_log_ratio = max(
            [
                max((metric["spearman"] or 0.0) for metric in run.get("val_stop_metrics", {}).get("entry_log_ratio", {}).values())
                for run in runs
            ],
            default=0.0,
        )
        best_side_trace = max((run.get("val_stop_entry_side_trace", 0.0) or 0.0) for run in runs)
        block_matrix[profile_key] = {
            "role": roles[profile_key],
            "best_val_stop_log_ratio": best_log_ratio,
            "best_val_stop_side_trace": best_side_trace,
            "improves_over_e0": best_log_ratio > baseline_best,
        }
        if roles[profile_key] in {"primary", "secondary"} and best_log_ratio > max(0.10, baseline_best):
            strong_primary = True
        if roles[profile_key] != "baseline" and best_log_ratio < 0.10 and best_side_trace >= 0.10:
            weak_trace = True

    runner_status = "NO_SIGNAL_FOUND"
    if strong_primary:
        runner_status = "PASS_DIAGNOSTIC"
    elif weak_trace:
        runner_status = "WEAK_TRACE_FOUND"
    return {
        "runner_status": runner_status,
        "profile_roles": roles,
        "block_matrix": block_matrix,
    }


def _rows_preview_to_frame(runs: list[dict]) -> pd.DataFrame:
    rows = []
    for run in runs:
        rows.extend(run.get("rows_csv_preview", []))
    if not rows:
        return pd.DataFrame(columns=["split_name", "time", "entry_up_3", "entry_dn_3", "entry_up_6", "entry_dn_6", "entry_up_12", "entry_dn_12"])
    return pd.DataFrame(rows)


def run_entry_based_updn_price_feature_matrix(
    resume: bool | None = None,
    report_path: Path = REPORT_JSON_PATH,
    rows_path: Path = REPORT_ROWS_PATH,
) -> dict:
    resume_enabled = CONFIG.resume_default if resume is None else bool(resume)
    heartbeat("runner_start", done_runs=0, total_runs=len(PROFILE_KEYS) * len(CONFIG.seeds))
    split_frames = load_entry_based_splits()
    report = load_existing_report(report_path) if resume_enabled else None
    if report is None:
        report = run_preflight(split_frames)
        report.setdefault("runs", [])
    total_runs = len(PROFILE_KEYS) * len(CONFIG.seeds)
    done_keys = completed_run_keys(report)
    start = time.time()

    for profile_key in PROFILE_KEYS:
        for seed in CONFIG.seeds:
            run_key = (profile_key, seed)
            if resume_enabled and run_key in done_keys:
                continue
            heartbeat("run_start", done_runs=len(report["runs"]), total_runs=total_runs)
            result = evaluate_profile_seed(profile_key, seed, split_frames)
            report["runs"].append(result)
            report["progress"] = {
                "done_runs": len(report["runs"]),
                "total_runs": total_runs,
                "elapsed_sec": max(time.time() - start, 0.0),
            }
            write_report_atomic(report, report_path)
            _rows_preview_to_frame(report["runs"]).to_csv(rows_path, index=False)
            heartbeat("run_end", done_runs=len(report["runs"]), total_runs=total_runs)

    report["summary"] = summarize_profiles(report)
    report["status"] = report["summary"]["runner_status"]
    report["finished_at"] = _utc_now_iso()
    report["elapsed_sec"] = report["progress"]["elapsed_sec"]
    write_report_atomic(report, report_path)
    _rows_preview_to_frame(report["runs"]).to_csv(rows_path, index=False)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    if not args.entry_based_updn_price_feature_matrix:
        parser.print_help()
        return 0
    run_entry_based_updn_price_feature_matrix(resume=args.resume)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
