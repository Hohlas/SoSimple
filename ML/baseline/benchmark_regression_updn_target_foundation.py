import argparse
import datetime as dt
import hashlib
import json
import math
import os
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import permutation_importance
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.multioutput import MultiOutputRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeRegressor
import xgboost as xgb

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from ML.baseline.benchmark_stage5_transformer_breach import (
    PROJECT_ROOT,
    REPORTS_DIR,
    STAGE5_1B_FIELD_TO_FRACTAL_INDEX,
    TIME_ONLY_ROW_FIELDS,
    N_FRACTALS,
    FRACTAL_SEP,
    build_stage5_4_features,
    stage5_4_feature_names,
    _build_stage5_flat_features_from_profile,
)


DATA_DIR = PROJECT_ROOT / "DATA"
REGRESSION_UPDN_JSON_REPORT_PATH = REPORTS_DIR / "regression_updn_target_foundation.json"
UPDN_TARGET_COLUMNS = (
    "up_3", "dn_3", "up_6", "dn_6", "up_12", "dn_12", "up_24", "dn_24", "up_48", "dn_48",
)
TARGET_PAIRS_BY_HORIZON = {
    3: ("up_3", "dn_3"),
    6: ("up_6", "dn_6"),
    12: ("up_12", "dn_12"),
    24: ("up_24", "dn_24"),
    48: ("up_48", "dn_48"),
}
XAUUSD_SPLIT_FILES = {
    "train_core": DATA_DIR / "Nero_XAUUSD_train_labeled.csv",
    "val_stop": DATA_DIR / "Nero_XAUUSD_validation_labeled.csv",
    "diagnostic_holdout": DATA_DIR / "Nero_XAUUSD_test_labeled.csv",
    "low_n_disclosure": DATA_DIR / "Nero_XAUUSD_test_labeled.csv",
}
HEARTBEAT_INTERVAL_SEC = 30.0


@dataclass(frozen=True)
class RegressionUpDnConfig:
    horizons: tuple[int, ...] = (3, 6, 12, 24, 48)
    legacy_reference_horizon: int = 12
    seeds: tuple[int, ...] = (42, 77, 123)
    primary_profile: str = "clock_shift_back"
    artifact_status: str = "DIAGNOSTIC_ONLY"
    train_max_year: int = 2020
    val_years: tuple[int, ...] = (2021, 2022)
    holdout_years: tuple[int, ...] = (2023, 2024, 2025)
    low_n_years: tuple[int, ...] = (2026,)
    bootstrap_block: int = 32
    bootstrap_repeats: int = 200
    xgb_n_jobs: int = 24


REGRESSION_UPDN_CONFIG = RegressionUpDnConfig()


def updn_profile_keys() -> tuple[str, ...]:
    return (
        "clock_only",
        "clock_shift",
        "clock_shift_back",
        "clock_shift_back_impulse",
        "structure_full",
    )


def updn_model_keys() -> tuple[str, ...]:
    return (
        "constant_median",
        "ridge",
        "decision_tree_depth3",
        "random_forest_depth4",
        "xgboost_depth3",
    )


def updn_feature_denylist() -> tuple[str, ...]:
    extra = (
        "predict",
        "signal",
        "stage6_definitive_tp_vs_sl_flag",
        "sell_stop_broken_H6_off05_flag",
        "buy_bars_to_breach_H6_off05",
        "buy_stop_broken_H6_off05_flag",
    )
    return UPDN_TARGET_COLUMNS + extra


def updn_allowed_input_sources(profile: str) -> dict:
    mapping = {
        "clock_only": {"row_fields": ["time"], "token_fields": []},
        "clock_shift": {"row_fields": ["time"], "token_fields": ["shift"]},
        "clock_shift_back": {"row_fields": ["time"], "token_fields": ["shift", "back"]},
        "clock_shift_back_impulse": {"row_fields": ["time"], "token_fields": ["shift", "back", "impulse"]},
        "structure_full": {
            "row_fields": ["time"],
            "token_fields": ["direction", "front", "back", "strong", "break", "reverse", "power", "count", "impulse", "shift"],
        },
    }
    if profile not in mapping:
        raise ValueError(f"Unknown profile: {profile}")
    return mapping[profile]


def updn_feature_source_contract(profile: str) -> dict:
    allowed = updn_allowed_input_sources(profile)
    return {
        "profile": profile,
        "input_selection": "allowlist",
        "allowed_sources": {
            "row_fields": allowed["row_fields"],
            "token_fields": allowed["token_fields"],
            "producer": "MT/MQL4/Files/Nero_XAUUSD.csv -> processing/label_main.py -> DATA/Nero_XAUUSD_*_labeled.csv",
            "availability": "known at row decision time",
            "live_safe_verdict": "PASS_WITH_DIAGNOSTIC_STATUS_CAP",
        },
        "forbidden_sources": {
            "top_level_updn_targets": list(UPDN_TARGET_COLUMNS),
            "future_row_labels": list(updn_feature_denylist()),
        },
        "role": "input",
        "transformation": "stage5 flat feature extraction with explicit allowlist",
    }


def _profile_stage5_spec(profile: str) -> dict:
    if profile == "clock_only":
        return {
            "name": "updn_clock_only",
            "selection": "all100",
            "order": "freshness",
            "token_fields": [],
            "row_fields": TIME_ONLY_ROW_FIELDS.copy(),
        }
    if profile == "clock_shift":
        return {
            "name": "updn_clock_shift",
            "selection": "all100",
            "order": "freshness",
            "token_fields": ["shift"],
            "row_fields": TIME_ONLY_ROW_FIELDS.copy(),
        }
    if profile == "structure_full":
        return {
            "name": "updn_structure_full",
            "selection": "all100",
            "order": "freshness",
            "token_fields": ["direction", "front", "back", "strong", "break", "reverse", "power", "count", "impulse", "shift"],
            "row_fields": TIME_ONLY_ROW_FIELDS.copy(),
        }
    raise ValueError(f"Unknown profile: {profile}")


def updn_feature_names(profile: str) -> list[str]:
    if profile in {"clock_shift_back", "clock_shift_back_impulse"}:
        return stage5_4_feature_names(profile)
    spec = _profile_stage5_spec(profile)
    names = []
    for fractal_idx in range(N_FRACTALS):
        for field in spec["token_fields"]:
            names.append(f"fractal{fractal_idx}.{field}")
    names.extend(spec["row_fields"])
    return names


def validate_updn_target_contract(splits: dict[str, pd.DataFrame]) -> dict:
    result = {"status": "PASS", "missing_columns": {}, "non_numeric_columns": {}, "split_summary": {}}
    for split_name, df in splits.items():
        missing = [col for col in UPDN_TARGET_COLUMNS if col not in df.columns]
        result["missing_columns"][split_name] = missing
        non_numeric = []
        summary = {}
        for col in UPDN_TARGET_COLUMNS:
            if col not in df.columns:
                continue
            series = pd.to_numeric(df[col], errors="coerce")
            if series.isna().all():
                non_numeric.append(col)
            summary[col] = {
                "n_rows": int(len(series)),
                "null_rate": _safe_float(series.isna().mean()),
                "min": _safe_float(series.min()),
                "max": _safe_float(series.max()),
            }
        result["non_numeric_columns"][split_name] = non_numeric
        result["split_summary"][split_name] = summary
        if missing or non_numeric:
            result["status"] = "FAIL"
    return result


def _safe_float(value):
    if value is None:
        return None
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(value) or math.isinf(value):
        return None
    return value


def _median_or_none(values) -> float | None:
    clean = [float(v) for v in values if v is not None and not math.isnan(float(v)) and not math.isinf(float(v))]
    if not clean:
        return None
    return _safe_float(np.median(np.asarray(clean, dtype=float)))


def _parse_years(series: pd.Series) -> pd.Series:
    parsed = pd.to_datetime(series, format="%Y.%m.%d %H:%M", errors="coerce")
    return parsed.dt.year


def load_updn_labeled_splits() -> dict[str, pd.DataFrame]:
    train = pd.read_csv(XAUUSD_SPLIT_FILES["train_core"], sep=";")
    val = pd.read_csv(XAUUSD_SPLIT_FILES["val_stop"], sep=";")
    test = pd.read_csv(XAUUSD_SPLIT_FILES["diagnostic_holdout"], sep=";")

    train_year = _parse_years(train["time"])
    val_year = _parse_years(val["time"])
    test_year = _parse_years(test["time"])

    splits = {
        "train_core": train.loc[train_year <= REGRESSION_UPDN_CONFIG.train_max_year].reset_index(drop=True),
        "val_stop": pd.concat(
            [train.loc[train_year.isin(REGRESSION_UPDN_CONFIG.val_years)], val.loc[val_year.isin(REGRESSION_UPDN_CONFIG.val_years)]],
            ignore_index=True,
        ),
        "diagnostic_holdout": pd.concat(
            [train.loc[train_year.isin(REGRESSION_UPDN_CONFIG.holdout_years)], val.loc[val_year.isin(REGRESSION_UPDN_CONFIG.holdout_years)], test.loc[test_year.isin(REGRESSION_UPDN_CONFIG.holdout_years)]],
            ignore_index=True,
        ),
        "low_n_disclosure": pd.concat(
            [train.loc[train_year.isin(REGRESSION_UPDN_CONFIG.low_n_years)], val.loc[val_year.isin(REGRESSION_UPDN_CONFIG.low_n_years)], test.loc[test_year.isin(REGRESSION_UPDN_CONFIG.low_n_years)]],
            ignore_index=True,
        ),
    }
    return splits


def extract_updn_targets(df: pd.DataFrame) -> np.ndarray:
    return df.loc[:, list(UPDN_TARGET_COLUMNS)].apply(pd.to_numeric, errors="coerce").fillna(0.0).to_numpy(dtype=np.float32)


def build_updn_features(df: pd.DataFrame, profile: str, return_preflight: bool = False):
    names = updn_feature_names(profile)
    if any(name in UPDN_TARGET_COLUMNS for name in names):
        raise ValueError("Top-level Up/Dn targets must not appear in feature names")

    if profile in {"clock_shift_back", "clock_shift_back_impulse"}:
        X = build_stage5_4_features(df, profile).astype(np.float32)
    else:
        X = _build_stage5_flat_features_from_profile(df, _profile_stage5_spec(profile)).astype(np.float32)

    non_finite_mask = ~np.isfinite(X)
    preflight = {
        "profile": profile,
        "non_finite_feature_count": int(non_finite_mask.sum()),
        "feature_count": int(X.shape[1]),
    }
    if non_finite_mask.any():
        X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
    if return_preflight:
        return X, preflight
    return X


def updn_constant_median_predict(train_y: np.ndarray, eval_n: int) -> np.ndarray:
    median = np.median(train_y, axis=0)
    return np.repeat(median[None, :], eval_n, axis=0)


def _corr_or_none(fn, a: np.ndarray, b: np.ndarray):
    if len(a) < 2:
        return None
    if np.allclose(a, a[0]) or np.allclose(b, b[0]):
        return None
    return _safe_float(fn(a, b)[0])


def updn_regression_metrics(y_true: np.ndarray, y_pred: np.ndarray, target_names: tuple[str, ...], atr: np.ndarray | None = None) -> dict:
    targets = {}
    for idx, name in enumerate(target_names):
        yt = y_true[:, idx]
        yp = y_pred[:, idx]
        mae = mean_absolute_error(yt, yp)
        rmse = math.sqrt(mean_squared_error(yt, yp))
        median_abs_target = np.median(np.abs(yt))
        median_atr = np.median(np.abs(atr)) if atr is not None and len(atr) else None
        targets[name] = {
            "mae": _safe_float(mae),
            "rmse": _safe_float(rmse),
            "pearson": _corr_or_none(stats.pearsonr, yt, yp),
            "spearman": _corr_or_none(stats.spearmanr, yt, yp),
            "mae_over_median_abs_target": _safe_float(mae / median_abs_target) if median_abs_target not in (None, 0) else None,
            "mae_over_median_atr": _safe_float(mae / median_atr) if median_atr not in (None, 0) else None,
        }
    return {"targets": targets}


def evaluate_edge_diagnostics(y_true: np.ndarray, y_pred: np.ndarray, target_names: tuple[str, ...]) -> dict:
    up_name, dn_name = target_names
    horizon = up_name.split("_")[1]
    edge_true = y_true[:, 0] - y_true[:, 1]
    edge_pred = y_pred[:, 0] - y_pred[:, 1]
    return {
        f"edge_{horizon}": {
            "spearman": _corr_or_none(stats.spearmanr, edge_true, edge_pred),
            "pearson": _corr_or_none(stats.pearsonr, edge_true, edge_pred),
            "sign_accuracy": _safe_float(np.mean(np.sign(edge_true) == np.sign(edge_pred))),
        }
    }


def _bootstrap_metric(values: np.ndarray, preds: np.ndarray, metric_fn, block: int, repeats: int, seed: int) -> dict:
    rng = np.random.default_rng(seed)
    n = len(values)
    if n == 0:
        return {"samples": [], "p05": None}
    samples = []
    for _ in range(repeats):
        indices = []
        while len(indices) < n:
            start = int(rng.integers(0, n))
            indices.extend(((start + i) % n) for i in range(block))
        take = np.asarray(indices[:n], dtype=int)
        samples.append(metric_fn(values[take], preds[take]))
    samples = np.asarray(samples, dtype=float)
    return {
        "samples": samples.tolist(),
        "p05": _safe_float(np.quantile(samples, 0.05)),
        "median": _safe_float(np.median(samples)),
    }


def _fit_model(model_key: str, seed: int):
    if model_key == "ridge":
        return Ridge(alpha=1.0)
    if model_key == "decision_tree_depth3":
        return DecisionTreeRegressor(max_depth=3, random_state=seed)
    if model_key == "random_forest_depth4":
        return RandomForestRegressor(
            n_estimators=200, max_depth=4, min_samples_leaf=8, random_state=seed, n_jobs=REGRESSION_UPDN_CONFIG.xgb_n_jobs
        )
    if model_key == "xgboost_depth3":
        base = xgb.XGBRegressor(
            n_estimators=200,
            max_depth=3,
            learning_rate=0.05,
            subsample=0.9,
            colsample_bytree=0.9,
            objective="reg:squarederror",
            random_state=seed,
            n_jobs=REGRESSION_UPDN_CONFIG.xgb_n_jobs,
        )
        return MultiOutputRegressor(base)
    raise ValueError(f"Unknown model_key: {model_key}")


def _train_predict_model(model_key: str, seed: int, train_X: np.ndarray, train_y: np.ndarray, eval_X: np.ndarray):
    if model_key == "constant_median":
        return updn_constant_median_predict(train_y, len(eval_X)), {"scaler_used": False}

    scaler = StandardScaler()
    train_X_scaled = scaler.fit_transform(train_X)
    eval_X_scaled = scaler.transform(eval_X)
    model = _fit_model(model_key, seed)
    model.fit(train_X_scaled, train_y)
    pred = model.predict(eval_X_scaled)
    meta = {"scaler_used": True}
    if model_key == "xgboost_depth3":
        try:
            perm = permutation_importance(model.estimators_[0], eval_X_scaled, eval_X_scaled[:, 0], n_repeats=5, random_state=seed)
            meta["permutation_dummy"] = True
            meta["calendar_importance_share"] = None
        except Exception:
            meta["calendar_importance_share"] = None
    return np.asarray(pred, dtype=np.float32), meta


def _calendar_share(feature_names: list[str], importances: np.ndarray | None) -> float | None:
    if importances is None or len(importances) != len(feature_names):
        return None
    total = float(np.abs(importances).sum())
    if total <= 0:
        return None
    cal = 0.0
    for name, imp in zip(feature_names, importances):
        if any(key in name for key in ("hour_", "dow_")):
            cal += abs(float(imp))
    return cal / total


def evaluate_updn_gate(summary: dict) -> dict:
    if summary["target_contract"]["status"] != "PASS":
        return {"research_gate_status": "TARGET_CONTRACT_FAILED", "artifact_status": REGRESSION_UPDN_CONFIG.artifact_status}
    primary = summary.get("primary") or {}
    horizon = summary.get("selected_horizon")
    if not primary or not horizon:
        return {"research_gate_status": "MODEL_GATE_FAILED", "artifact_status": REGRESSION_UPDN_CONFIG.artifact_status}
    up_key = f"up_{horizon}"
    dn_key = f"dn_{horizon}"
    upm = primary["target_metrics"].get(up_key, {})
    dnm = primary["target_metrics"].get(dn_key, {})
    edge = primary.get(f"edge_{horizon}", {})
    model_ok = (
        (upm.get("normalized_mae_improvement_vs_constant") or -1) >= 0.05 and
        (dnm.get("normalized_mae_improvement_vs_constant") or -1) >= 0.05 and
        (upm.get("spearman") or -1) >= 0.15 and
        (dnm.get("spearman") or -1) >= 0.15 and
        (edge.get("spearman") or -1) >= 0.10
    )
    robust_ok = (
        (upm.get("bootstrap_p05_improvement") or -1) > 0 and
        (dnm.get("bootstrap_p05_improvement") or -1) > 0 and
        (edge.get("bootstrap_p05_spearman") or -1) > 0 and
        not edge.get("val_year_sign_reversal", True) and
        int(primary.get("seed_pass_count", 0)) >= 2
    )
    status = "TARGET_FOUNDATION_PASSED" if model_ok and robust_ok else ("ROBUSTNESS_GATE_FAILED" if model_ok else "MODEL_GATE_FAILED")
    return {
        "research_gate_status": status,
        "artifact_status": REGRESSION_UPDN_CONFIG.artifact_status,
        "calendar_warning": bool(primary.get("calendar_warning", False)),
    }


def _summary_for_horizon(report: dict, horizon: int, profile: str) -> dict:
    selected_runs = [r for r in report["runs"] if r["profile"] == profile and r["model_key"] == "xgboost_depth3"]
    if not selected_runs:
        return {}
    up_key, dn_key = TARGET_PAIRS_BY_HORIZON[horizon]
    per_seed_pass = 0
    target_metrics = {}
    edge_entry = {}
    for name in (up_key, dn_key):
        improvements = []
        spearmans = []
        bootstrap_p05 = []
        for run in selected_runs:
            cur = run["split_metrics"]["val_stop"]["targets"][name]
            improvements.append(cur.get("normalized_mae_improvement_vs_constant"))
            spearmans.append(cur.get("spearman"))
            bootstrap_p05.append(cur.get("bootstrap_p05_improvement"))
        target_metrics[name] = {
            "normalized_mae_improvement_vs_constant": _median_or_none(improvements),
            "spearman": _median_or_none(spearmans),
            "bootstrap_p05_improvement": _median_or_none(bootstrap_p05),
        }
    edge_key = f"edge_{horizon}"
    edge_s = []
    edge_p05 = []
    signs = []
    calendar_flags = []
    for run in selected_runs:
        edge = run["split_metrics"]["val_stop"]["edge"][edge_key]
        edge_s.append(edge.get("spearman"))
        edge_p05.append(edge.get("bootstrap_p05_spearman"))
        signs.extend(edge.get("yearly_spearman_signs", {}).values())
        calendar_flags.append(run.get("calendar_warning", False))
        up_imp = run["split_metrics"]["val_stop"]["targets"][up_key].get("normalized_mae_improvement_vs_constant")
        dn_imp = run["split_metrics"]["val_stop"]["targets"][dn_key].get("normalized_mae_improvement_vs_constant")
        up_sp = run["split_metrics"]["val_stop"]["targets"][up_key].get("spearman")
        dn_sp = run["split_metrics"]["val_stop"]["targets"][dn_key].get("spearman")
        edge_sp = edge.get("spearman")
        if (
            (up_imp or -1) >= 0.05
            and (dn_imp or -1) >= 0.05
            and (up_sp or -1) >= 0.15
            and (dn_sp or -1) >= 0.15
            and (edge_sp or -1) >= 0.10
        ):
            per_seed_pass += 1
    edge_entry[edge_key] = {
        "spearman": _median_or_none(edge_s),
        "bootstrap_p05_spearman": _median_or_none(edge_p05),
        "val_year_sign_reversal": any(float(v) < 0 for v in signs if v is not None),
    }
    return {
        "profile": profile,
        "seed_pass_count": per_seed_pass,
        "target_metrics": target_metrics,
        edge_key: edge_entry[edge_key],
        "calendar_warning": any(calendar_flags),
    }


def _evaluate_single_run(
    profile: str,
    model_key: str,
    seed: int,
    split_frames: dict[str, pd.DataFrame],
    feature_split: dict[str, np.ndarray],
) -> dict:
    train_X = feature_split["train_core"]
    train_y = extract_updn_targets(split_frames["train_core"])
    result = {
        "profile": profile,
        "model_key": model_key,
        "seed": int(seed),
        "split_metrics": {},
    }
    val_feature_names = updn_feature_names(profile)
    calendar_warning = False
    for split_name, frame in split_frames.items():
        X = feature_split[split_name]
        y = extract_updn_targets(frame)
        atr = pd.to_numeric(frame.get("ATR"), errors="coerce").fillna(0.0).to_numpy(dtype=np.float32) if "ATR" in frame.columns else None
        pred, meta = _train_predict_model(model_key, seed, train_X, train_y, X)
        constant_pred = updn_constant_median_predict(train_y, len(X))
        base_metrics = updn_regression_metrics(y, constant_pred, UPDN_TARGET_COLUMNS, atr=atr)
        model_metrics = updn_regression_metrics(y, pred, UPDN_TARGET_COLUMNS, atr=atr)
        for name in UPDN_TARGET_COLUMNS:
            cur = model_metrics["targets"][name]
            base = base_metrics["targets"][name]
            norm_model = cur.get("mae_over_median_atr") or cur.get("mae_over_median_abs_target")
            norm_base = base.get("mae_over_median_atr") or base.get("mae_over_median_abs_target")
            if norm_model is not None and norm_base not in (None, 0):
                cur["normalized_mae_improvement_vs_constant"] = _safe_float((norm_base - norm_model) / norm_base)
            else:
                cur["normalized_mae_improvement_vs_constant"] = None
        edge = {}
        for horizon, names in TARGET_PAIRS_BY_HORIZON.items():
            idxs = [UPDN_TARGET_COLUMNS.index(names[0]), UPDN_TARGET_COLUMNS.index(names[1])]
            edge_metrics = evaluate_edge_diagnostics(y[:, idxs], pred[:, idxs], names)
            edge_key = f"edge_{horizon}"
            yearly_signs = {}
            years = _parse_years(frame["time"]) if "time" in frame.columns else pd.Series([None] * len(frame))
            for year in sorted(set(years.dropna().tolist())):
                mask = years == year
                yt = y[mask.to_numpy(), :][:, idxs]
                yp = pred[mask.to_numpy(), :][:, idxs]
                yearly = evaluate_edge_diagnostics(yt, yp, names)[edge_key]["spearman"]
                yearly_signs[str(int(year))] = yearly
            edge_metrics[edge_key]["yearly_spearman_signs"] = yearly_signs
            boot = _bootstrap_metric(
                y[:, idxs][:, 0] - y[:, idxs][:, 1],
                pred[:, idxs][:, 0] - pred[:, idxs][:, 1],
                lambda a, b: (_corr_or_none(stats.spearmanr, a, b) or -1.0),
                REGRESSION_UPDN_CONFIG.bootstrap_block,
                REGRESSION_UPDN_CONFIG.bootstrap_repeats,
                seed,
            )
            edge_metrics[edge_key]["bootstrap_p05_spearman"] = boot["p05"]
            edge[edge_key] = edge_metrics[edge_key]
        if split_name == "val_stop":
            for name in UPDN_TARGET_COLUMNS:
                idx = UPDN_TARGET_COLUMNS.index(name)
                y_true = y[:, idx]
                y_model = pred[:, idx]
                y_const = constant_pred[:, idx]
                boot = _bootstrap_metric(
                    np.column_stack([y_true, y_model, y_const]),
                    np.zeros((len(y_true), 1)),
                    lambda a, _: ((mean_absolute_error(a[:, 0], a[:, 2]) - mean_absolute_error(a[:, 0], a[:, 1])) / max(mean_absolute_error(a[:, 0], a[:, 2]), 1e-9)),
                    REGRESSION_UPDN_CONFIG.bootstrap_block,
                    REGRESSION_UPDN_CONFIG.bootstrap_repeats,
                    seed,
                )
                model_metrics["targets"][name]["bootstrap_p05_improvement"] = boot["p05"]
        result["split_metrics"][split_name] = {
            "targets": model_metrics["targets"],
            "constant_targets": base_metrics["targets"],
            "edge": edge,
        }

        if model_key == "xgboost_depth3" and split_name == "val_stop":
            scaler = StandardScaler()
            train_scaled = scaler.fit_transform(train_X)
            val_scaled = scaler.transform(X)
            base = xgb.XGBRegressor(
                n_estimators=120,
                max_depth=3,
                learning_rate=0.05,
                subsample=0.9,
                colsample_bytree=0.9,
                objective="reg:squarederror",
                random_state=seed,
                n_jobs=REGRESSION_UPDN_CONFIG.xgb_n_jobs,
            )
            base.fit(train_scaled, train_y[:, 0])
            perm = permutation_importance(base, val_scaled, y[:, 0], n_repeats=5, random_state=seed, n_jobs=1)
            share = _calendar_share(val_feature_names, perm.importances_mean)
            result["calendar_importance_share"] = share
            calendar_warning = bool(share is not None and share > 0.30)
    result["calendar_warning"] = calendar_warning
    return result


def updn_input_file_manifest() -> dict:
    manifest = {}
    for split_name, path in XAUUSD_SPLIT_FILES.items():
        if not path.exists():
            continue
        data = path.read_bytes()
        try:
            row_count = max(sum(1 for _ in path.open("r", encoding="utf-8", errors="ignore")) - 1, 0)
        except OSError:
            row_count = None
        manifest[split_name] = {
            "path": str(path),
            "byte_count": len(data),
            "row_count": row_count,
            "sha256": hashlib.sha256(data).hexdigest(),
        }
    return manifest


def _build_feature_contract(profile_keys: tuple[str, ...]) -> dict:
    return {
        profile: {
            "feature_names": updn_feature_names(profile),
            "feature_names_sha256": hashlib.sha256("\n".join(updn_feature_names(profile)).encode("utf-8")).hexdigest(),
            "feature_source_contract": updn_feature_source_contract(profile),
        }
        for profile in profile_keys
    }


def run_regression_updn_target_foundation(
    output_path: Path = REGRESSION_UPDN_JSON_REPORT_PATH,
    resume: bool = True,
    profile_keys: tuple[str, ...] | None = None,
) -> dict:
    started_at = dt.datetime.now(dt.timezone.utc).isoformat()
    wall0 = time.time()
    selected_profiles = profile_keys or updn_profile_keys()
    selected_models = updn_model_keys()
    total_runs = len(selected_profiles) * len(selected_models) * len(REGRESSION_UPDN_CONFIG.seeds)

    if resume and output_path.exists():
        report = json.loads(output_path.read_text())
        done_set = {(r["profile"], r["model_key"], int(r["seed"])) for r in report.get("runs", [])}
        report["resumed_at"] = started_at
    else:
        report = {
            "experiment": "regression_updn_target_foundation",
            "status": "RUNNING",
            "artifact_status": REGRESSION_UPDN_CONFIG.artifact_status,
            "started_at": started_at,
            "config": asdict(REGRESSION_UPDN_CONFIG),
            "feature_contract": _build_feature_contract(selected_profiles),
            "input_manifest": updn_input_file_manifest(),
            "runs": [],
            "done_runs": 0,
            "total_runs": total_runs,
        }
        done_set = set()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2, default=str))

    split_frames = load_updn_labeled_splits()
    report["target_contract"] = validate_updn_target_contract(split_frames)
    output_path.write_text(json.dumps(report, indent=2, default=str))

    for profile in selected_profiles:
        print(f"[updn] building features profile={profile}", flush=True)
        feature_split = {}
        preflight = {}
        for split_name, frame in split_frames.items():
            X, info = build_updn_features(frame, profile, return_preflight=True)
            feature_split[split_name] = X
            preflight[split_name] = info
        report.setdefault("feature_preflight", {})[profile] = preflight
        output_path.write_text(json.dumps(report, indent=2, default=str))
        for model_key in selected_models:
            for seed in REGRESSION_UPDN_CONFIG.seeds:
                key = (profile, model_key, int(seed))
                if key in done_set:
                    continue
                t0 = time.time()
                run = _evaluate_single_run(profile, model_key, seed, split_frames, feature_split)
                run["elapsed_sec"] = float(time.time() - t0)
                report["runs"].append(run)
                report["done_runs"] = int(report.get("done_runs", 0)) + 1
                output_path.write_text(json.dumps(report, indent=2, default=str))

    profile_horizon_summary = {}
    primary_profile_summary = {}
    selected_horizon = None
    selected_profile = None
    best_score = -1.0
    for profile in selected_profiles:
        per_profile = {}
        for horizon in REGRESSION_UPDN_CONFIG.horizons:
            entry = _summary_for_horizon(report, horizon, profile)
            per_profile[horizon] = entry
            if profile == REGRESSION_UPDN_CONFIG.primary_profile:
                primary_profile_summary[horizon] = entry
            if not entry:
                continue
            cur = entry["target_metrics"]
            edge = entry.get(f"edge_{horizon}", {})
            score = (
                (cur.get(f"up_{horizon}", {}).get("spearman") or 0.0)
                + (cur.get(f"dn_{horizon}", {}).get("spearman") or 0.0)
                + (edge.get("spearman") or 0.0)
            )
            if score > best_score:
                best_score = score
                selected_horizon = horizon
                selected_profile = profile
        profile_horizon_summary[profile] = per_profile
    report["summary"] = {"profiles": profile_horizon_summary, "primary_profile_horizons": primary_profile_summary}
    report["selected_horizon"] = selected_horizon
    report["selected_profile"] = selected_profile
    report["primary"] = (
        profile_horizon_summary.get(selected_profile, {}).get(selected_horizon)
        if selected_profile is not None and selected_horizon is not None
        else None
    )
    report["gate"] = evaluate_updn_gate({
        "target_contract": report["target_contract"],
        "selected_horizon": selected_horizon,
        "primary": report["primary"],
    })
    report["research_gate_status"] = report["gate"]["research_gate_status"]
    report["artifact_status"] = report["gate"]["artifact_status"]
    report["status"] = f"{report['research_gate_status']} / {report['artifact_status']}"
    report["finished_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
    report["elapsed_sec"] = float(time.time() - wall0)
    output_path.write_text(json.dumps(report, indent=2, default=str))
    return report


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--regression-updn-target-foundation", action="store_true")
    parser.add_argument("--resume", action="store_true", default=True, dest="resume")
    parser.add_argument("--no-resume", action="store_false", dest="resume")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    if args.regression_updn_target_foundation:
        report = run_regression_updn_target_foundation(resume=args.resume)
        print({"status": report.get("status"), "json": str(REGRESSION_UPDN_JSON_REPORT_PATH)})
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
