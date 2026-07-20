from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ML.baseline.benchmark_stage5_transformer_breach import (
    FRACTAL_SEP,
    STAGE5_1B_FIELD_TO_FRACTAL_INDEX,
    build_stage5_4_features,
    extract_stage5_1b_fields,
    stage5_4_feature_names,
)
from sklearn.metrics import roc_auc_score
from xgboost import XGBClassifier

from ML.baseline.benchmark_stage6_outcome_based import (
    DATA_DIR,
    OHLC_FILE,
    REPORTS_DIR,
    STAGE6_0_CONFIG,
    Stage60Config,
    stage6_all_trade_baseline,
    stage6_binary_metrics,
    stage6_build_outcome_labels,
    stage6_feature_denylist,
    stage6_load_labeled_splits,
    stage6_outcome_preflight,
    stage6_permutation_threshold_baseline,
    stage6_select_threshold_on_val,
    stage6_simulate_threshold,
)


STAGE6_1_JSON_REPORT_PATH = REPORTS_DIR / "stage6_1_h12_relative_fractal_geometry.json"


STAGE6_1_COMBINED_PROFILE_TO_GEOMETRY = {
    "h12_clock_shift_back_plus_nearest_time40_geometry": "h12_nearest_time40_relative_geometry",
    "h12_clock_shift_back_plus_corridor3_geometry": "h12_corridor3_relative_geometry",
    "h12_clock_shift_back_plus_corridor10_geometry": "h12_corridor10_relative_geometry",
}


@dataclass(frozen=True)
class Stage61Config:
    horizon_bars: int = 12
    stop_offset_atr: float = 0.5
    take_profit_atr: float = 2.0
    entry_lag_bars: int = 1
    primary_profile: str = "h12_corridor3_relative_geometry"
    profile_keys: tuple[str, ...] = (
        "h12_clock_shift_back",
        "h12_nearest_price40_relative_geometry",
        "h12_nearest_time40_relative_geometry",
        "h12_corridor3_relative_geometry",
        "h12_corridor10_relative_geometry",
        "h12_zones10_uniform_summary",
        "h12_clock_shift_back_plus_nearest_time40_geometry",
        "h12_clock_shift_back_plus_corridor3_geometry",
        "h12_clock_shift_back_plus_corridor10_geometry",
    )
    seeds: tuple[int, ...] = (42, 77, 123)


STAGE6_1_CONFIG = Stage61Config()


def stage61_parse_fractals(row: pd.Series) -> list[dict]:
    out: list[dict] = []
    for i in range(100):
        col = f"fractal{i}"
        if col not in row:
            continue
        raw = str(row.get(col, ""))
        parts = raw.split(FRACTAL_SEP)
        if len(parts) < 23:
            continue
        try:
            price = float(parts[1])
        except (ValueError, IndexError):
            continue
        if price <= 0.0:
            continue
        try:
            direction = float(parts[2])
        except (ValueError, IndexError):
            direction = 0.0
        try:
            front = float(parts[3])
        except (ValueError, IndexError):
            front = 0.0
        try:
            back = float(parts[4])
        except (ValueError, IndexError):
            back = 0.0
        try:
            impulse = float(parts[10])
        except (ValueError, IndexError):
            impulse = 0.0
        try:
            raw_shift = float(parts[22])
        except (ValueError, IndexError):
            raw_shift = 0.0
        raw_shift = float(np.nan_to_num(raw_shift, nan=0.0))
        out.append({
            "fractal_idx": i,
            "price": price,
            "direction": float(np.nan_to_num(direction, nan=0.0)),
            "front": float(np.nan_to_num(front, nan=0.0)),
            "back": float(np.nan_to_num(back, nan=0.0)),
            "impulse": float(np.nan_to_num(impulse, nan=0.0)),
            "shift_bars": max(raw_shift, 0.0),
            "log_shift": float(np.log1p(max(raw_shift, 0.0))),
        })
    return out


def stage61_relative_fractal_frame(row: pd.Series, mode: str,
                                   k: int = 40,
                                   corridor_atr: float = 10.0) -> pd.DataFrame:
    atr = float(row.get("ATR", 0.0) or 0.0)
    if atr <= 0.0:
        return pd.DataFrame()
    fractals = stage61_parse_fractals(row)
    if not fractals:
        return pd.DataFrame()
    anchor = next((f for f in fractals if f["fractal_idx"] == 0), None)
    if anchor is None:
        return pd.DataFrame()
    anchor_price = float(anchor["price"])
    rows = []
    for item in fractals:
        if item["fractal_idx"] == 0:
            continue
        coord = (float(item["price"]) - anchor_price) / atr
        row_out = {
            "fractal_idx": int(item["fractal_idx"]),
            "price_coord_atr": float(coord),
            "abs_price_coord_atr": float(abs(coord)),
            "direction": float(item["direction"]),
            "front": float(item["front"]),
            "back": float(item["back"]),
            "impulse": float(item["impulse"]),
            "log_shift": float(item["log_shift"]),
            "selection_rank": 0.0,
        }
        rows.append(row_out)
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    if mode == "nearest_price":
        frame = frame.sort_values(["abs_price_coord_atr", "fractal_idx"]).head(k)
    elif mode == "nearest_time":
        frame = frame.sort_values(["log_shift", "fractal_idx"]).head(k)
    elif mode == "corridor":
        frame = frame.loc[frame["abs_price_coord_atr"] <= corridor_atr]
        frame = frame.sort_values(["abs_price_coord_atr", "fractal_idx"]).head(k)
    else:
        raise ValueError(f"unknown mode: {mode}")
    frame = frame.reset_index(drop=True)
    frame["selection_rank"] = np.arange(len(frame), dtype=np.float32)
    return frame


GEOMETRY_FIELDS = (
    "price_coord_atr",
    "abs_price_coord_atr",
    "direction",
    "front",
    "back",
    "impulse",
    "log_shift",
    "selection_rank",
)

ZONE_BOUNDS = tuple((float(i), float(i + 1)) for i in range(-10, 10))


def _stage61_pad_flat(frame: pd.DataFrame, max_rows: int = 40) -> np.ndarray:
    arr = np.zeros((max_rows, len(GEOMETRY_FIELDS)), dtype=np.float32)
    if frame.empty:
        return arr.reshape(-1)
    values = frame.loc[:, GEOMETRY_FIELDS].to_numpy(dtype=np.float32)
    n = min(len(values), max_rows)
    arr[:n, :] = values[:n, :]
    return arr.reshape(-1)


def _stage61_zone_features(row: pd.Series) -> np.ndarray:
    frame = stage61_relative_fractal_frame(row, mode="corridor", corridor_atr=10.0, k=100)
    out = []
    for low, high in ZONE_BOUNDS:
        zone = frame.loc[(frame["price_coord_atr"] >= low) & (frame["price_coord_atr"] < high)]
        if zone.empty:
            out.extend([0.0, 0.0, 0.0, 0.0, 0.0])
            continue
        out.extend([
            float(len(zone)),
            float(zone["back"].mean()),
            float(zone["back"].max()),
            float(zone["impulse"].mean()),
            float(zone["abs_price_coord_atr"].min()),
        ])
    return np.asarray(out, dtype=np.float32)


def stage61_feature_names(profile: str) -> list[str]:
    if profile in {
        "h12_nearest_price40_relative_geometry",
        "h12_nearest_time40_relative_geometry",
        "h12_corridor3_relative_geometry",
        "h12_corridor10_relative_geometry",
    }:
        return [f"slot{i:02d}_{field}" for i in range(40) for field in GEOMETRY_FIELDS]
    if profile == "h12_zones10_uniform_summary":
        zone_fields = ("count", "back_mean", "back_max", "impulse_mean", "nearest_abs_coord")
        return [
            f"zone_{int(low):+03d}_{int(high):+03d}_{field}"
            for low, high in ZONE_BOUNDS
            for field in zone_fields
        ]
    if profile in STAGE6_1_COMBINED_PROFILE_TO_GEOMETRY:
        geometry_profile = STAGE6_1_COMBINED_PROFILE_TO_GEOMETRY[profile]
        baseline_names = [f"baseline.{name}" for name in stage5_4_feature_names("clock_shift_back")]
        geometry_names = [f"geometry.{name}" for name in stage61_feature_names(geometry_profile)]
        return baseline_names + geometry_names
    raise ValueError(f"unknown Stage 6.1 profile: {profile}")


def stage61_build_geometry_features(df: pd.DataFrame, profile: str) -> np.ndarray:
    rows = []
    for _, row in df.iterrows():
        if profile == "h12_nearest_price40_relative_geometry":
            frame = stage61_relative_fractal_frame(row, mode="nearest_price", k=40)
            rows.append(_stage61_pad_flat(frame, max_rows=40))
        elif profile == "h12_nearest_time40_relative_geometry":
            frame = stage61_relative_fractal_frame(row, mode="nearest_time", k=40)
            rows.append(_stage61_pad_flat(frame, max_rows=40))
        elif profile == "h12_corridor3_relative_geometry":
            frame = stage61_relative_fractal_frame(row, mode="corridor", k=40, corridor_atr=3.0)
            rows.append(_stage61_pad_flat(frame, max_rows=40))
        elif profile == "h12_corridor10_relative_geometry":
            frame = stage61_relative_fractal_frame(row, mode="corridor", k=40, corridor_atr=10.0)
            rows.append(_stage61_pad_flat(frame, max_rows=40))
        elif profile == "h12_zones10_uniform_summary":
            rows.append(_stage61_zone_features(row))
        else:
            raise ValueError(f"not a geometry profile: {profile}")
    if not rows:
        width = 20 * 5 if profile == "h12_zones10_uniform_summary" else 40 * len(GEOMETRY_FIELDS)
        return np.zeros((0, width), dtype=np.float32)
    return np.vstack(rows).astype(np.float32)


def stage61_build_combined_features(df: pd.DataFrame, profile: str) -> np.ndarray:
    geometry_profile = STAGE6_1_COMBINED_PROFILE_TO_GEOMETRY[profile]
    clean = df.drop(columns=[c for c in stage61_feature_denylist() if c in df.columns])
    baseline = build_stage5_4_features(clean, "clock_shift_back")
    geometry = stage61_build_geometry_features(clean, geometry_profile)
    if len(baseline) != len(geometry):
        raise ValueError(
            f"combined feature row mismatch for {profile}: baseline={len(baseline)} geometry={len(geometry)}"
        )
    return np.concatenate([baseline.astype(np.float32), geometry.astype(np.float32)], axis=1)


def stage61_build_features(df: pd.DataFrame, profile: str) -> np.ndarray:
    clean = df.drop(columns=[c for c in stage61_feature_denylist() if c in df.columns])
    if profile == "h12_clock_shift_back":
        return build_stage5_4_features(clean, "clock_shift_back")
    if profile in {
        "h12_nearest_price40_relative_geometry",
        "h12_nearest_time40_relative_geometry",
        "h12_corridor3_relative_geometry",
        "h12_corridor10_relative_geometry",
        "h12_zones10_uniform_summary",
    }:
        return stage61_build_geometry_features(clean, profile)
    if profile in STAGE6_1_COMBINED_PROFILE_TO_GEOMETRY:
        return stage61_build_combined_features(clean, profile)
    raise ValueError(f"unknown Stage 6.1 profile: {profile}")


def _stage61_quantiles(values) -> dict:
    arr = np.asarray(values, dtype=np.float64)
    arr = arr[np.isfinite(arr)]
    if len(arr) == 0:
        return {"p5": None, "p25": None, "median": None, "p75": None, "p95": None}
    return {
        "p5": float(np.percentile(arr, 5)),
        "p25": float(np.percentile(arr, 25)),
        "median": float(np.median(arr)),
        "p75": float(np.percentile(arr, 75)),
        "p95": float(np.percentile(arr, 95)),
    }


def stage61_fractal_format_preflight(split: dict[str, pd.DataFrame]) -> dict:
    out = {}
    for name, df in split.items():
        if not isinstance(df, pd.DataFrame) or "fractal0" not in df.columns:
            continue
        non_empty = df["fractal0"].dropna().astype(str)
        non_empty = non_empty.loc[non_empty.str.len() > 0]
        field_counts = non_empty.map(lambda value: len(value.split(FRACTAL_SEP)))
        short_rows = int((field_counts < 23).sum())
        warnings = []
        if short_rows:
            warnings.append("SHORT_FRACTAL0_ROWS")
        out[name] = {
            "non_empty_fractal0_rows": int(len(non_empty)),
            "short_fractal0_rows": short_rows,
            "min_field_count": int(field_counts.min()) if len(field_counts) else None,
            "median_field_count": float(field_counts.median()) if len(field_counts) else None,
            "warnings": warnings,
        }
    return out


def stage61_geometry_coverage(df: pd.DataFrame, profile: str) -> dict:
    token_counts = []
    min_coords = []
    max_coords = []
    above_counts = []
    below_counts = []
    for _, row in df.iterrows():
        if profile == "h12_nearest_price40_relative_geometry":
            frame = stage61_relative_fractal_frame(row, mode="nearest_price", k=40)
        elif profile == "h12_nearest_time40_relative_geometry":
            frame = stage61_relative_fractal_frame(row, mode="nearest_time", k=40)
        elif profile == "h12_corridor3_relative_geometry":
            frame = stage61_relative_fractal_frame(row, mode="corridor", k=100, corridor_atr=3.0)
        elif profile in {"h12_corridor10_relative_geometry", "h12_zones10_uniform_summary"}:
            frame = stage61_relative_fractal_frame(row, mode="corridor", k=100, corridor_atr=10.0)
        else:
            continue
        token_counts.append(len(frame))
        if frame.empty:
            continue
        min_coords.append(float(frame["price_coord_atr"].min()))
        max_coords.append(float(frame["price_coord_atr"].max()))
        above_counts.append(int((frame["price_coord_atr"] > 0).sum()))
        below_counts.append(int((frame["price_coord_atr"] < 0).sum()))
    warnings = []
    if token_counts and profile == "h12_corridor3_relative_geometry" and np.median(token_counts) < 1:
        warnings.append("CORRIDOR3_MEDIAN_LT_1")
    if token_counts and profile in {"h12_corridor10_relative_geometry", "h12_zones10_uniform_summary"} and np.median(token_counts) < 3:
        warnings.append("CORRIDOR10_MEDIAN_LT_3")
    rows_0 = float(np.mean(np.asarray(token_counts) == 0)) if token_counts else 1.0
    if rows_0 > 0.05:
        warnings.append("ROWS_WITH_0_TOKENS_GT_5PCT")
    min_coord = min(min_coords) if min_coords else None
    max_coord = max(max_coords) if max_coords else None
    corridor_bound = 3.0 if profile == "h12_corridor3_relative_geometry" else 10.0
    if profile in {"h12_corridor3_relative_geometry", "h12_corridor10_relative_geometry", "h12_zones10_uniform_summary"}:
        if min_coord is not None and min_coord < -corridor_bound - 0.0001:
            warnings.append("CORRIDOR_MIN_BELOW_BOUND")
        if max_coord is not None and max_coord > corridor_bound + 0.0001:
            warnings.append("CORRIDOR_MAX_ABOVE_BOUND")
    return {
        "n_rows": int(len(df)),
        "token_count": _stage61_quantiles(token_counts),
        "rows_with_0_tokens_rate": rows_0,
        "rows_with_1_2_tokens_rate": float(np.mean((np.asarray(token_counts) >= 1) & (np.asarray(token_counts) <= 2))) if token_counts else 0.0,
        "rows_with_3plus_tokens_rate": float(np.mean(np.asarray(token_counts) >= 3)) if token_counts else 0.0,
        "min_price_coord_atr": min_coord,
        "max_price_coord_atr": max_coord,
        "above_count": _stage61_quantiles(above_counts),
        "below_count": _stage61_quantiles(below_counts),
        "warnings": warnings,
    }


def stage61_feature_preflight(split: dict[str, pd.DataFrame]) -> dict:
    out = {}
    for profile in stage61_profile_keys():
        if profile == "h12_clock_shift_back":
            continue
        out[profile] = {
            name: stage61_geometry_coverage(df, profile)
            for name, df in split.items()
            if isinstance(df, pd.DataFrame)
        }
    return out


def stage61_definitive_mask(df: pd.DataFrame) -> np.ndarray:
    y = df["stage6_definitive_tp_vs_sl_flag"].to_numpy(dtype=np.float64)
    return np.isfinite(y)


def stage61_permutation_feature_importance(model,
                                           X: np.ndarray,
                                           y: np.ndarray,
                                           profile: str,
                                           seed: int,
                                           top_n: int = 25) -> list[dict]:
    if len(np.unique(y)) < 2:
        return []
    rng = np.random.default_rng(seed)
    names = stage61_feature_names(profile)
    baseline_score = float(roc_auc_score(y, model.predict_proba(X)[:, 1]))
    rows = []
    for col_idx, name in enumerate(names):
        X_perm = X.copy()
        X_perm[:, col_idx] = rng.permutation(X_perm[:, col_idx])
        perm_score = float(roc_auc_score(y, model.predict_proba(X_perm)[:, 1]))
        rows.append({
            "feature": name,
            "auc_drop": float(baseline_score - perm_score),
            "baseline_auc": baseline_score,
            "permuted_auc": perm_score,
        })
    rows.sort(key=lambda item: item["auc_drop"], reverse=True)
    return rows[:top_n]


def evaluate_stage61_profile_seed(split: dict[str, pd.DataFrame],
                                  feature_split: dict[str, np.ndarray],
                                  profile: str,
                                  seed: int) -> dict:
    train = split["train_core"]
    val = split["val_stop"]
    train_mask = stage61_definitive_mask(train)
    val_mask = stage61_definitive_mask(val)
    X_train = feature_split["train_core"]
    X_val = feature_split["val_stop"]
    y_train = train["stage6_definitive_tp_vs_sl_flag"].to_numpy(dtype=np.float64)
    y_val = val["stage6_definitive_tp_vs_sl_flag"].to_numpy(dtype=np.float64)
    clf = XGBClassifier(
        max_depth=6,
        learning_rate=0.03,
        n_estimators=500,
        subsample=0.8,
        colsample_bytree=0.8,
        early_stopping_rounds=20,
        random_state=seed,
        eval_metric="logloss",
        verbosity=0,
        n_jobs=24,
    )
    clf.fit(
        X_train[train_mask],
        y_train[train_mask],
        eval_set=[(X_val[val_mask], y_val[val_mask])],
        verbose=False,
    )
    val_score_def = clf.predict_proba(X_val[val_mask])[:, 1]
    val_score_all = clf.predict_proba(X_val)[:, 1]
    threshold = stage6_select_threshold_on_val(val.copy(), val_score_all)
    out = {
        "profile": profile,
        "seed": int(seed),
        "train_definitive_n": int(train_mask.sum()),
        "val_definitive_n": int(val_mask.sum()),
        "val_stop": stage6_binary_metrics(y_val[val_mask], val_score_def),
        "threshold_selection": threshold,
        "predictions": {
            "val_stop": {
                "y_true_definitive": y_val[val_mask].astype(int).tolist(),
                "y_score_definitive": val_score_def.tolist(),
                "y_score_all": val_score_all.tolist(),
                "pnl_r_all": val["stage6_pnl_r"].astype(float).tolist(),
            }
        },
        "feature_importance": [] if profile == "h12_clock_shift_back" else stage61_permutation_feature_importance(
            clf,
            X_val[val_mask],
            y_val[val_mask],
            profile,
            seed=seed,
        ),
    }
    for split_name in ("diagnostic_holdout", "low_n_disclosure"):
        df = split[split_name]
        X = feature_split[split_name]
        mask = stage61_definitive_mask(df)
        y = df["stage6_definitive_tp_vs_sl_flag"].to_numpy(dtype=np.float64)
        score_all = clf.predict_proba(X)[:, 1]
        score_def = score_all[mask]
        out[split_name] = stage6_binary_metrics(y[mask], score_def) if mask.any() else {}
        if threshold.get("status") == "SELECTED" and threshold.get("selected"):
            out[f"threshold_on_{split_name}"] = stage6_simulate_threshold(
                df.copy(), score_all, threshold["selected"]["threshold"]
            )
        else:
            out[f"threshold_on_{split_name}"] = None
    return out


def _stage61_median(values) -> float | None:
    vals = [v for v in values if v is not None and np.isfinite(v)]
    return float(np.median(vals)) if vals else None


def stage61_gate_results(report: dict) -> dict:
    summary = report.get("summary", {})
    primary = summary.get(STAGE6_1_CONFIG.primary_profile, {})
    val = primary.get("val_stop", {})
    threshold = primary.get("threshold_selection", {})
    checks = {
        "auc_ge_0_60": bool(val.get("auc_median") is not None and val["auc_median"] >= 0.60),
        "pr_auc_lift_ge_0_05": bool(val.get("pr_auc_lift_median") is not None and val["pr_auc_lift_median"] >= 0.05),
        "permutation_p_value_le_0_10": bool(
            (primary.get("permutation_baseline") or {}).get("empirical_p_value") is not None
            and (primary.get("permutation_baseline") or {})["empirical_p_value"] <= 0.10
        ),
        "threshold_selected": bool(threshold.get("status") == "SELECTED" and threshold.get("selected") is not None),
    }
    checks["model_gate_pass"] = (
        checks["auc_ge_0_60"]
        and checks["pr_auc_lift_ge_0_05"]
        and checks["permutation_p_value_le_0_10"]
    )
    if not checks["model_gate_pass"]:
        return {"overall_status": "MODEL_GATE_FAILED", "artifact_status": "DIAGNOSTIC_ONLY", "checks": checks}
    if not checks["threshold_selected"]:
        return {"overall_status": "TRADING_GATE_FAILED", "artifact_status": "DIAGNOSTIC_ONLY", "checks": checks}
    selected = threshold["selected"]
    checks["val_pf_ge_1_15"] = bool(selected.get("pf") is not None and selected["pf"] >= 1.15)
    checks["val_trades_per_year_ge_25"] = bool(selected.get("trades_per_year", 0) >= 25)
    checks["spread_020_pf_ge_1_05"] = bool(selected.get("pf_spread_020") is not None and selected["pf_spread_020"] >= 1.05)
    if all(checks.values()):
        return {"overall_status": "DIAGNOSTIC_SIGNAL_FOUND", "artifact_status": "DIAGNOSTIC_ONLY", "checks": checks}
    return {"overall_status": "TRADING_GATE_FAILED", "artifact_status": "DIAGNOSTIC_ONLY", "checks": checks}


def stage61_profile_keys() -> tuple[str, ...]:
    return STAGE6_1_CONFIG.profile_keys


def stage61_combined_profile_keys() -> tuple[str, ...]:
    return tuple(STAGE6_1_COMBINED_PROFILE_TO_GEOMETRY.keys())


def stage61_feature_denylist() -> tuple[str, ...]:
    return stage6_feature_denylist()


def stage61_input_file_manifest() -> dict:
    paths = {
        "ohlc": OHLC_FILE,
        "train_labeled": DATA_DIR / "Nero_XAUUSD_train_labeled.csv",
        "validation_labeled": DATA_DIR / "Nero_XAUUSD_validation_labeled.csv",
        "test_labeled": DATA_DIR / "Nero_XAUUSD_test_labeled.csv",
    }
    out = {}
    for name, path in paths.items():
        payload = path.read_bytes()
        with path.open("rb") as fh:
            row_count = sum(1 for _ in fh) - 1
        out[name] = {
            "path": str(path),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "bytes": len(payload),
            "row_count": int(max(row_count, 0)),
        }
    return out


def stage61_baseline_delta_summary(report: dict) -> dict:
    summary = report.get("summary", {})
    baseline = summary.get("h12_clock_shift_back", {})
    baseline_val = baseline.get("val_stop", {})
    baseline_threshold = baseline.get("threshold_selection", {})
    baseline_selected = baseline_threshold.get("selected") or {}
    baseline_auc = baseline_val.get("auc_median")
    baseline_pr = baseline_val.get("pr_auc_lift_median")
    baseline_pf = baseline_threshold.get("val_pf_median", baseline_selected.get("pf"))
    rows = {}
    best_profile = None
    best_auc_delta = None
    for profile in stage61_combined_profile_keys():
        item = summary.get(profile, {})
        val = item.get("val_stop", {})
        threshold = item.get("threshold_selection", {}) or {}
        selected = threshold.get("selected") or {}
        perm = item.get("permutation_baseline") or {}
        auc = val.get("auc_median")
        pr = val.get("pr_auc_lift_median")
        pf = threshold.get("val_pf_median", selected.get("pf"))
        auc_delta = None if auc is None or baseline_auc is None else float(auc - baseline_auc)
        pr_delta = None if pr is None or baseline_pr is None else float(pr - baseline_pr)
        pf_delta = None if pf is None or baseline_pf is None else float(pf - baseline_pf)
        passes = (
            auc_delta is not None and auc_delta >= 0.02
            and pr_delta is not None and pr_delta >= 0.0
            and threshold.get("status") == "SELECTED"
            and pf_delta is not None and pf_delta >= 0.0
            and perm.get("empirical_p_value") is not None
            and perm["empirical_p_value"] <= 0.10
        )
        rows[profile] = {
            "auc_delta_vs_baseline": auc_delta,
            "pr_auc_lift_delta_vs_baseline": pr_delta,
            "pf_delta_vs_baseline": pf_delta,
            "permutation_p_value": perm.get("empirical_p_value"),
            "passes_delta_gate": bool(passes),
        }
        if auc_delta is not None and (best_auc_delta is None or auc_delta > best_auc_delta):
            best_profile = profile
            best_auc_delta = auc_delta
    return {
        "baseline_profile": "h12_clock_shift_back",
        "best_profile": best_profile,
        "profiles": rows,
        "delta_gate": {
            "auc_delta_ge_0_02": 0.02,
            "pr_auc_lift_delta_ge_0": 0.0,
            "pf_delta_ge_0": 0.0,
            "permutation_p_value_le_0_10": 0.10,
        },
    }


def run_stage6_1_relative_geometry(
    output_path: Path = STAGE6_1_JSON_REPORT_PATH,
    resume: bool = True,
) -> dict:
    import datetime
    import time

    started_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    wall0 = time.time()

    if resume and output_path.exists():
        report = json.loads(output_path.read_text())
        done_set = {(r["profile"], int(r["seed"])) for r in report.get("raw_runs", [])}
        print(f"[stage6.1] RESUME existing report: {output_path}")
        print(f"[stage6.1] Already done: {len(done_set)} runs ({report.get('done_runs', 0)}/{report.get('total_runs', '?')})")
        report["resumed_at"] = started_at
    else:
        report = {
            "stage": "6.1",
            "status": "RUNNING",
            "started_at": started_at,
            "config": {
                "horizon_bars": STAGE6_1_CONFIG.horizon_bars,
                "profiles": list(STAGE6_1_CONFIG.profile_keys),
                "primary_profile": STAGE6_1_CONFIG.primary_profile,
                "seeds": list(STAGE6_1_CONFIG.seeds),
                "target": "stage6_definitive_tp_vs_sl_flag",
                "ohlc_file": str(OHLC_FILE),
                "xgb_n_jobs": 24,
            },
            "input_manifest": stage61_input_file_manifest(),
            "raw_runs": [],
            "done_runs": 0,
            "total_runs": len(STAGE6_1_CONFIG.profile_keys) * len(STAGE6_1_CONFIG.seeds),
        }
        done_set = set()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2, default=str))
        print(f"[stage6.1] Started fresh report: {output_path}", flush=True)

    # Preflight (skipped if resuming with existing preflight data)
    if "fractal_format_preflight" not in report:
        print("[stage6.1] Loading splits and running preflight ...", flush=True)
        cfg = replace(
            STAGE6_0_CONFIG,
            horizon_bars=STAGE6_1_CONFIG.horizon_bars,
            stop_offset_atr=STAGE6_1_CONFIG.stop_offset_atr,
            take_profit_atr=STAGE6_1_CONFIG.take_profit_atr,
            entry_lag_bars=STAGE6_1_CONFIG.entry_lag_bars,
        )
        split = stage6_load_labeled_splits(config=cfg)
        report["fractal_format_preflight"] = stage61_fractal_format_preflight(split)
        report["preflight"] = stage6_outcome_preflight(split)
        report["feature_preflight"] = stage61_feature_preflight(split)
        report["oracle_preflight"] = {
            name: stage6_all_trade_baseline(df)
            for name, df in split.items()
            if isinstance(df, pd.DataFrame)
        }
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2, default=str))
        print("[stage6.1] Preflight done, saved checkpoint.", flush=True)
    else:
        print("[stage6.1] Preflight data present, resuming from last checkpoint.", flush=True)
        cfg = replace(
            STAGE6_0_CONFIG,
            horizon_bars=STAGE6_1_CONFIG.horizon_bars,
            stop_offset_atr=STAGE6_1_CONFIG.stop_offset_atr,
            take_profit_atr=STAGE6_1_CONFIG.take_profit_atr,
            entry_lag_bars=STAGE6_1_CONFIG.entry_lag_bars,
        )
        split = stage6_load_labeled_splits(config=cfg)

    total_runs: int = report["total_runs"]
    done_runs: int = report["done_runs"]

    for profile in STAGE6_1_CONFIG.profile_keys:
        print(f"[stage6.1] Building features for profile={profile} ...", flush=True)
        t0_profile = time.time()
        feature_split = {
            name: stage61_build_features(df, profile)
            for name, df in split.items()
            if isinstance(df, pd.DataFrame)
        }
        print(f"[stage6.1] Features built in {time.time() - t0_profile:.1f}s", flush=True)

        for seed in STAGE6_1_CONFIG.seeds:
            key = (profile, int(seed))
            if key in done_set:
                print(f"[stage6.1] SKIP profile={profile} seed={seed} (already done)", flush=True)
                continue

            t0_run = time.time()
            print(f"[stage6.1] Training profile={profile} seed={seed} "
                  f"({done_runs + 1}/{total_runs}) ...", flush=True)
            result = evaluate_stage61_profile_seed(split, feature_split, profile, seed)
            result["elapsed_sec"] = float(time.time() - t0_run)
            report["raw_runs"].append(result)
            done_runs += 1
            report["done_runs"] = done_runs

            elapsed = time.time() - wall0
            remaining = (total_runs - done_runs) * (elapsed / max(done_runs, 1))
            print(f"[stage6.1] done {done_runs}/{total_runs}  "
                  f"elapsed={elapsed:.0f}s  ETA={remaining:.0f}s", flush=True)

            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps(report, indent=2, default=str))

    # Summary
    summary = {}
    for profile in STAGE6_1_CONFIG.profile_keys:
        runs = [r for r in report["raw_runs"] if r["profile"] == profile]
        aucs = [r["val_stop"].get("auc") for r in runs]
        lifts = [r["val_stop"].get("pr_auc_lift") for r in runs]
        selected = [
            r["threshold_selection"]["selected"]
            for r in runs
            if r["threshold_selection"].get("status") == "SELECTED" and r["threshold_selection"].get("selected")
        ]
        best_run = max(runs, key=lambda r: r["val_stop"].get("auc") or 0.0)
        perm = None
        val_scores = best_run.get("predictions", {}).get("val_stop", {}).get("y_score_all", [])
        if val_scores:
            perm = stage6_permutation_threshold_baseline(split["val_stop"].copy(), np.asarray(val_scores), seed=42)
        summary[profile] = {
            "val_stop": {
                "auc_median": _stage61_median(aucs),
                "pr_auc_lift_median": _stage61_median(lifts),
            },
            "threshold_selection": {
                "status": "SELECTED" if selected else "NO_THRESHOLD",
                "selected": selected[len(selected) // 2] if selected else None,
                "n_selected": len(selected),
                "val_pf_median": _stage61_median([s.get("pf") for s in selected]),
            },
            "threshold_on_diagnostic": best_run.get("threshold_on_diagnostic_holdout"),
            "permutation_baseline": perm,
        }
    report["summary"] = summary
    report["baseline_plus_geometry_delta"] = stage61_baseline_delta_summary(report)
    report["gate"] = stage61_gate_results(report)
    report["status"] = report["gate"]["overall_status"]
    finished_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    report["finished_at"] = finished_at
    report["elapsed_sec"] = float(time.time() - wall0)
    output_path.write_text(json.dumps(report, indent=2, default=str))
    return report


def main(argv: list[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage6-1-relative-geometry", action="store_true")
    parser.add_argument("--resume", action="store_true", default=True, dest="resume")
    parser.add_argument("--no-resume", action="store_false", dest="resume")
    args = parser.parse_args(argv)
    if args.stage6_1_relative_geometry:
        report = run_stage6_1_relative_geometry(resume=args.resume)
        print({"status": report.get("status"), "json": str(STAGE6_1_JSON_REPORT_PATH)})
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
