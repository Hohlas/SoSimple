from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
from xgboost import XGBClassifier

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ML.baseline.benchmark_stage5_transformer_breach import build_stage5_4_features, stage5_4_feature_names
from ML.baseline.benchmark_stage6_outcome_based import (
    DATA_DIR,
    OHLC_FILE,
    REPORTS_DIR,
    STAGE6_0_CONFIG,
    Stage60Config,
    stage6_all_trade_baseline,
    stage6_binary_metrics,
    stage6_feature_denylist,
    stage6_load_labeled_splits,
    stage6_outcome_preflight,
    stage6_permutation_threshold_baseline,
    stage6_select_threshold_on_val,
    stage6_simulate_threshold,
)
from ML.baseline.benchmark_stage6_1_relative_geometry import (
    stage61_build_features,
    stage61_feature_names as stage61_feature_names_fn,
    stage61_profile_keys as stage61_profile_keys_fn,
    stage61_definitive_mask as stage61_definitive_mask_fn,
    stage61_permutation_feature_importance,
    stage61_combined_profile_keys,
)
from ML.baseline.benchmark_stage6_2_price_action import (
    STAGE6_2_JSON_REPORT_PATH,
    stage62_build_features,
    stage62_feature_names as stage62_feature_names_fn,
    stage62_profile_keys as stage62_profile_keys_fn,
    stage62_definitive_mask as stage62_definitive_mask_fn,
    stage62_load_ohlc_frame,
    stage62_permutation_feature_importance,
    COMBINED_TO_PRICE_ACTION as STAGE62_COMBINED_TO_PRICE_ACTION,
)


STAGE6_3_JSON_REPORT_PATH = REPORTS_DIR / "stage6_3_h6_feature_parity.json"

H6_PREFIX = "h6_"
H12_PREFIX = "h12_"


def _h6_to_h12_profile(h6_name: str) -> str:
    if h6_name.startswith(H6_PREFIX):
        return h6_name.replace(H6_PREFIX, H12_PREFIX, 1)
    return h6_name


def _h12_to_h6_profile(h12_name: str) -> str:
    if h12_name.startswith(H12_PREFIX):
        return h12_name.replace(H12_PREFIX, H6_PREFIX, 1)
    return h12_name


STAGE63_H6_GEOMETRY_ONLY: tuple[str, ...] = (
    "h12_nearest_price40_relative_geometry",
    "h12_nearest_time40_relative_geometry",
    "h12_corridor3_relative_geometry",
    "h12_corridor10_relative_geometry",
    "h12_zones10_uniform_summary",
)

STAGE63_H6_PRICE_ACTION_ONLY: tuple[str, ...] = (
    "h12_price_action_core",
    "h12_price_action_regime",
)

STAGE63_H6_GEOMETRY_PROFILES: tuple[str, ...] = tuple(
    sorted(_h12_to_h6_profile(p) for p in STAGE63_H6_GEOMETRY_ONLY)
)

STAGE63_H6_PRICE_ACTION_PROFILES: tuple[str, ...] = tuple(
    sorted(_h12_to_h6_profile(p) for p in STAGE63_H6_PRICE_ACTION_ONLY)
)

STAGE63_COMBINED_PROFILES: tuple[str, ...] = (
    "h6_clock_shift_back_plus_nearest_time40_geometry",
    "h6_clock_shift_back_plus_corridor3_geometry",
    "h6_clock_shift_back_plus_corridor10_geometry",
    "h6_clock_shift_back_plus_price_action_core",
    "h6_clock_shift_back_plus_price_action_regime",
)

STAGE63_ALL_PROFILES: tuple[str, ...] = (
    "h6_clock_shift_back",
) + STAGE63_H6_GEOMETRY_PROFILES + STAGE63_H6_PRICE_ACTION_PROFILES + STAGE63_COMBINED_PROFILES


@dataclass(frozen=True)
class Stage63Config:
    horizon_bars: int = 6
    stop_offset_atr: float = 0.5
    take_profit_atr: float = 2.0
    entry_lag_bars: int = 1
    primary_profile: str = "h6_clock_shift_back"
    profile_keys: tuple[str, ...] = STAGE63_ALL_PROFILES
    seeds: tuple[int, ...] = (42, 77, 123)
    xgb_n_jobs: int = 24


STAGE6_3_CONFIG = Stage63Config()


def stage63_profile_keys() -> tuple[str, ...]:
    return STAGE6_3_CONFIG.profile_keys


def stage63_geometry_only_profiles() -> tuple[str, ...]:
    return STAGE63_H6_GEOMETRY_PROFILES


def stage63_price_action_only_profiles() -> tuple[str, ...]:
    return STAGE63_H6_PRICE_ACTION_PROFILES


def stage63_combined_profiles() -> tuple[str, ...]:
    return STAGE63_COMBINED_PROFILES


def stage63_is_geometry_profile(profile: str) -> bool:
    return profile in STAGE63_H6_GEOMETRY_PROFILES


def stage63_is_price_action_profile(profile: str) -> bool:
    return profile in STAGE63_H6_PRICE_ACTION_PROFILES


def stage63_is_combined_geometry(profile: str) -> bool:
    return profile in (
        "h6_clock_shift_back_plus_nearest_time40_geometry",
        "h6_clock_shift_back_plus_corridor3_geometry",
        "h6_clock_shift_back_plus_corridor10_geometry",
    )


def stage63_is_combined_price_action(profile: str) -> bool:
    return profile in (
        "h6_clock_shift_back_plus_price_action_core",
        "h6_clock_shift_back_plus_price_action_regime",
    )


def stage63_is_combined(profile: str) -> bool:
    return stage63_is_combined_geometry(profile) or stage63_is_combined_price_action(profile)


def stage63_feature_names(profile: str) -> list[str]:
    if profile == "h6_clock_shift_back":
        return stage5_4_feature_names("clock_shift_back")
    if stage63_is_geometry_profile(profile) and not stage63_is_combined(profile):
        return stage61_feature_names_fn(_h6_to_h12_profile(profile))
    if stage63_is_price_action_profile(profile) and not stage63_is_combined(profile):
        return stage62_feature_names_fn(_h6_to_h12_profile(profile))
    if profile == "h6_clock_shift_back_plus_nearest_time40_geometry":
        geometry_profile = _h6_to_h12_profile(
            "h6_nearest_time40_relative_geometry"
        )
        baseline_names = [f"baseline.{name}" for name in stage5_4_feature_names("clock_shift_back")]
        geometry_names = [f"geometry.{name}" for name in stage61_feature_names_fn(geometry_profile)]
        return baseline_names + geometry_names
    if profile == "h6_clock_shift_back_plus_corridor3_geometry":
        geometry_profile = _h6_to_h12_profile("h6_corridor3_relative_geometry")
        baseline_names = [f"baseline.{name}" for name in stage5_4_feature_names("clock_shift_back")]
        geometry_names = [f"geometry.{name}" for name in stage61_feature_names_fn(geometry_profile)]
        return baseline_names + geometry_names
    if profile == "h6_clock_shift_back_plus_corridor10_geometry":
        geometry_profile = _h6_to_h12_profile("h6_corridor10_relative_geometry")
        baseline_names = [f"baseline.{name}" for name in stage5_4_feature_names("clock_shift_back")]
        geometry_names = [f"geometry.{name}" for name in stage61_feature_names_fn(geometry_profile)]
        return baseline_names + geometry_names
    if profile == "h6_clock_shift_back_plus_price_action_core":
        baseline_names = [f"baseline.{name}" for name in stage5_4_feature_names("clock_shift_back")]
        price_names = [
            f"price_action.{name}"
            for name in stage62_feature_names_fn("h12_price_action_core")
        ]
        return baseline_names + price_names
    if profile == "h6_clock_shift_back_plus_price_action_regime":
        baseline_names = [f"baseline.{name}" for name in stage5_4_feature_names("clock_shift_back")]
        price_names = [
            f"price_action.{name}"
            for name in stage62_feature_names_fn("h12_price_action_regime")
        ]
        return baseline_names + price_names
    raise ValueError(f"unknown Stage 6.3 profile: {profile}")


def stage63_feature_denylist() -> tuple[str, ...]:
    return stage6_feature_denylist()


def stage63_build_features(df: pd.DataFrame, profile: str, ohlc: pd.DataFrame | None = None) -> np.ndarray:
    clean = df.drop(columns=[c for c in stage63_feature_denylist() if c in df.columns])
    if profile == "h6_clock_shift_back":
        return build_stage5_4_features(clean, "clock_shift_back")
    if stage63_is_geometry_profile(profile) and not stage63_is_combined(profile):
        return stage61_build_features(clean, _h6_to_h12_profile(profile))
    if stage63_is_price_action_profile(profile) and not stage63_is_combined(profile):
        return stage62_build_features(clean, _h6_to_h12_profile(profile), ohlc=ohlc)
    if stage63_is_combined_geometry(profile):
        baseline = build_stage5_4_features(clean, "clock_shift_back")
        geom_name = profile.replace("h6_clock_shift_back_plus_", "h6_").replace("_geometry", "_relative_geometry")
        if geom_name == "h6_nearest_time40_relative_geometry":
            h12_geometry = "h12_nearest_time40_relative_geometry"
        elif geom_name == "h6_corridor3_relative_geometry":
            h12_geometry = "h12_corridor3_relative_geometry"
        elif geom_name == "h6_corridor10_relative_geometry":
            h12_geometry = "h12_corridor10_relative_geometry"
        else:
            h12_geometry = _h6_to_h12_profile(geom_name)
        geometry = stage61_build_features(clean, h12_geometry)
        if len(baseline) != len(geometry):
            raise ValueError(f"combined feature row mismatch for {profile}")
        return np.concatenate([baseline.astype(np.float32), geometry.astype(np.float32)], axis=1)
    if stage63_is_combined_price_action(profile):
        baseline = build_stage5_4_features(clean, "clock_shift_back")
        h12_pa_name = "h12_price_action_core" if "price_action_core" in profile else "h12_price_action_regime"
        price_action = stage62_build_features(clean, h12_pa_name, ohlc=ohlc)
        if len(baseline) != len(price_action):
            raise ValueError(f"combined feature row mismatch for {profile}")
        return np.concatenate([baseline.astype(np.float32), price_action.astype(np.float32)], axis=1)
    raise ValueError(f"unknown Stage 6.3 profile: {profile}")


def stage63_input_file_manifest() -> dict:
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


def stage63_definitive_mask(df: pd.DataFrame) -> np.ndarray:
    y = df["stage6_definitive_tp_vs_sl_flag"].to_numpy(dtype=np.float64)
    reason = df["stage6_close_reason"].astype(str)
    return np.isfinite(y) & reason.isin(["TP", "SL", "AMBIGUOUS_SL_FIRST"]).to_numpy()


def _stage63_median(values) -> float | None:
    vals = [v for v in values if v is not None and np.isfinite(v)]
    return float(np.median(vals)) if vals else None


def _stage63_min(values) -> float | None:
    vals = [v for v in values if v is not None and np.isfinite(v)]
    return float(np.min(vals)) if vals else None


def _stage63_max(values) -> float | None:
    vals = [v for v in values if v is not None and np.isfinite(v)]
    return float(np.max(vals)) if vals else None


def _stage63_median_selected(selected: list[dict]) -> dict | None:
    if not selected:
        return None
    ranked = sorted(
        selected,
        key=lambda row: (
            float(row.get("pf")) if row.get("pf") is not None and np.isfinite(row.get("pf")) else -1e9,
            int(row.get("trades", 0)),
            float(row.get("threshold", 0.0)),
        ),
    )
    return ranked[len(ranked) // 2]


def evaluate_stage63_profile_seed(
    split: dict[str, pd.DataFrame],
    feature_split: dict[str, np.ndarray],
    profile: str,
    seed: int,
) -> dict:
    train = split["train_core"]
    val = split["val_stop"]
    train_mask = stage63_definitive_mask(train)
    val_mask = stage63_definitive_mask(val)
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
        n_jobs=STAGE6_3_CONFIG.xgb_n_jobs,
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
    }
    for split_name in ("diagnostic_holdout", "low_n_disclosure"):
        df = split[split_name]
        X = feature_split[split_name]
        mask = stage63_definitive_mask(df)
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


def stage63_baseline_delta_summary(report: dict) -> dict:
    summary = report.get("summary", {})
    baseline = summary.get("h6_clock_shift_back", {})
    baseline_auc = baseline.get("val_stop", {}).get("auc_median")
    baseline_pr = baseline.get("val_stop", {}).get("pr_auc_lift_median")
    threshold = baseline.get("threshold_selection", {}) or {}
    baseline_selected = threshold.get("selected") or {}
    baseline_pf = threshold.get("val_pf_median", baseline_selected.get("pf"))
    rows = {}
    best_profile = None
    best_auc_delta = None
    for profile in stage63_combined_profiles():
        item = summary.get(profile, {})
        auc = item.get("val_stop", {}).get("auc_median")
        pr = item.get("val_stop", {}).get("pr_auc_lift_median")
        thresh = item.get("threshold_selection", {}) or {}
        selected = thresh.get("selected") or {}
        pf = thresh.get("val_pf_median", selected.get("pf"))
        perm = item.get("permutation_baseline") or {}
        auc_delta = None if auc is None or baseline_auc is None else float(auc - baseline_auc)
        pr_delta = None if pr is None or baseline_pr is None else float(pr - baseline_pr)
        pf_delta = None if pf is None or baseline_pf is None else float(pf - baseline_pf)
        passes = (
            auc_delta is not None and auc_delta >= 0.02
            and pr_delta is not None and pr_delta >= 0.0
            and thresh.get("status") == "SELECTED"
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
        "baseline_profile": "h6_clock_shift_back",
        "best_profile": best_profile,
        "profiles": rows,
        "delta_gate": {
            "auc_delta_ge_0_02": 0.02,
            "pr_auc_lift_delta_ge_0": 0.0,
            "pf_delta_ge_0": 0.0,
            "permutation_p_value_le_0_10": 0.10,
        },
    }


def stage63_h6_vs_h12_disclosure(report: dict, h12_summary: dict | None = None) -> dict:
    if h12_summary is None:
        return {"status": "NO_H12_DATA"}
    out = {}
    h6_summary = report.get("summary", {})
    for profile in ("h6_clock_shift_back",):
        h6_entry = h6_summary.get(profile, {})
        h12_entry = h12_summary.get("h12_clock_shift_back", {})
        if not h6_entry or not h12_entry:
            continue
        out[profile] = {
            "h6_auc_median": h6_entry.get("val_stop", {}).get("auc_median"),
            "h12_auc_median": h12_entry.get("val_stop", {}).get("auc_median"),
            "h6_pf_median": (h6_entry.get("threshold_selection", {}) or {}).get("val_pf_median"),
            "h12_pf_median": (h12_entry.get("threshold_selection", {}) or {}).get("val_pf_median"),
        }
    return out


def stage63_gate_results(report: dict) -> dict:
    summary = report.get("summary", {})
    baseline = summary.get("h6_clock_shift_back", {})
    val = baseline.get("val_stop", {})
    threshold = baseline.get("threshold_selection", {})
    selected = threshold.get("selected") or {}
    perm = baseline.get("permutation_baseline") or {}
    auc_delta = report.get("baseline_plus_feature_delta", {})
    any_delta_pass = any(
        v.get("passes_delta_gate", False)
        for v in (auc_delta.get("profiles") or {}).values()
    )
    checks = {
        "baseline_auc_ge_0_60": bool(val.get("auc_median") is not None and val["auc_median"] >= 0.60),
        "baseline_pr_auc_lift_ge_0_05": bool(
            val.get("pr_auc_lift_median") is not None and val["pr_auc_lift_median"] >= 0.05
        ),
        "baseline_threshold_selected": bool(threshold.get("status") == "SELECTED" and selected),
        "baseline_permutation_p_value_le_0_10": bool(
            perm.get("empirical_p_value") is not None and perm["empirical_p_value"] <= 0.10
        ),
        "any_delta_gate_pass": any_delta_pass,
    }
    if not checks["baseline_auc_ge_0_60"] or not checks["baseline_pr_auc_lift_ge_0_05"]:
        return {"overall_status": "MODEL_GATE_FAILED", "artifact_status": "DIAGNOSTIC_ONLY", "checks": checks}
    if checks["any_delta_gate_pass"]:
        return {
            "overall_status": "DIAGNOSTIC_SIGNAL_FOUND",
            "artifact_status": "DIAGNOSTIC_ONLY",
            "interpretation": "H6_FEATURE_ADDITIVE_VALUE_DETECTED",
            "checks": checks,
        }
    return {
        "overall_status": "DIAGNOSTIC_ONLY",
        "artifact_status": "DIAGNOSTIC_ONLY",
        "interpretation": "NO_ADDITIVE_VALUE_CONFIRMED",
        "checks": checks,
    }


def stage63_summary(report: dict, split: dict[str, pd.DataFrame]) -> dict:
    summary = {}
    for profile in STAGE6_3_CONFIG.profile_keys:
        runs = [r for r in report["raw_runs"] if r["profile"] == profile]
        if not runs:
            continue
        aucs = [r["val_stop"].get("auc") for r in runs]
        lifts = [r["val_stop"].get("pr_auc_lift") for r in runs]
        selected = [
            r["threshold_selection"]["selected"]
            for r in runs
            if r["threshold_selection"].get("status") == "SELECTED" and r["threshold_selection"].get("selected")
        ]
        seed_rows = []
        permutation_rows = []
        for run in runs:
            val_scores = run.get("predictions", {}).get("val_stop", {}).get("y_score_all", [])
            perm = None
            if val_scores and "_year" in split["val_stop"].columns:
                perm = stage6_permutation_threshold_baseline(
                    split["val_stop"].copy(),
                    np.asarray(val_scores),
                    seed=int(run["seed"]),
                )
                permutation_rows.append(perm)
            threshold = run.get("threshold_selection", {}) or {}
            seed_rows.append({
                "seed": int(run["seed"]),
                "val_auc": run["val_stop"].get("auc"),
                "val_pr_auc_lift": run["val_stop"].get("pr_auc_lift"),
                "threshold_status": threshold.get("status"),
                "threshold": (threshold.get("selected") or {}).get("threshold"),
                "pf": (threshold.get("selected") or {}).get("pf"),
                "trades": (threshold.get("selected") or {}).get("trades"),
                "trades_per_year": (threshold.get("selected") or {}).get("trades_per_year"),
                "pf_spread_020": (threshold.get("selected") or {}).get("pf_spread_020"),
                "permutation_p_value": None if perm is None else perm.get("empirical_p_value"),
            })
        p_values = [row.get("empirical_p_value") for row in permutation_rows]
        perm_result = None
        if permutation_rows:
            perm_result = {
                "n_seed": int(len(permutation_rows)),
                "n_perm_per_seed": int(permutation_rows[0].get("n_perm", 0)),
                "empirical_p_value": _stage63_median(p_values),
                "empirical_p_value_min": _stage63_min(p_values),
                "empirical_p_value_max": _stage63_max(p_values),
                "per_seed": permutation_rows,
                "aggregation": "median_over_seeds",
            }
        selected_median = _stage63_median_selected(selected)
        summary[profile] = {
            "val_stop": {
                "auc_median": _stage63_median(aucs),
                "pr_auc_lift_median": _stage63_median(lifts),
            },
            "threshold_selection": {
                "status": "SELECTED" if selected else "NO_THRESHOLD",
                "selected": selected_median,
                "n_selected": len(selected),
                "val_pf_median": _stage63_median([s.get("pf") for s in selected]),
                "selected_rule": "median_pf_over_selected_seeds",
            },
            "diagnostic_holdout": {
                "auc_median": _stage63_median([r.get("diagnostic_holdout", {}).get("auc") for r in runs]),
                "pr_auc_lift_median": _stage63_median([
                    r.get("diagnostic_holdout", {}).get("pr_auc_lift") for r in runs
                ]),
            },
            "low_n_disclosure": {
                "auc_median": _stage63_median([r.get("low_n_disclosure", {}).get("auc") for r in runs]),
                "pr_auc_lift_median": _stage63_median([
                    r.get("low_n_disclosure", {}).get("pr_auc_lift") for r in runs
                ]),
            },
            "permutation_baseline": perm_result,
            "seed_runs": seed_rows,
        }
    return summary


def stage63_h12_summary_for_disclosure() -> dict | None:
    try:
        data = json.loads(STAGE6_2_JSON_REPORT_PATH.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        try:
            from ML.baseline.benchmark_stage6_1_relative_geometry import STAGE6_1_JSON_REPORT_PATH as S61_PATH
            data = json.loads(S61_PATH.read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            return None
    h12_clock_shift = (data.get("summary") or {}).get("h12_clock_shift_back") or {}
    return {"h12_clock_shift_back": h12_clock_shift}


def run_stage6_3_h6_feature_parity(
    output_path: Path = STAGE6_3_JSON_REPORT_PATH,
    resume: bool = True,
) -> dict:
    import datetime
    import time

    started_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    wall0 = time.time()

    if resume and output_path.exists():
        report = json.loads(output_path.read_text())
        done_set = {(r["profile"], int(r["seed"])) for r in report.get("raw_runs", [])}
        print(f"[stage6.3] RESUME existing report: {output_path}", flush=True)
        print(
            f"[stage6.3] Already done: {len(done_set)} runs "
            f"({report.get('done_runs', 0)}/{report.get('total_runs', '?')})",
            flush=True,
        )
        report["resumed_at"] = started_at
    else:
        feature_contract = {
            profile: {
                "feature_names": stage63_feature_names(profile),
                "feature_names_sha256": hashlib.sha256(
                    "\n".join(stage63_feature_names(profile)).encode("utf-8")
                ).hexdigest(),
                "feature_count": len(stage63_feature_names(profile)),
            }
            for profile in STAGE6_3_CONFIG.profile_keys
        }
        report = {
            "stage": "6.3",
            "status": "RUNNING",
            "started_at": started_at,
            "config": {
                "horizon_bars": STAGE6_3_CONFIG.horizon_bars,
                "stop_offset_atr": STAGE6_3_CONFIG.stop_offset_atr,
                "take_profit_atr": STAGE6_3_CONFIG.take_profit_atr,
                "entry_lag_bars": STAGE6_3_CONFIG.entry_lag_bars,
                "profiles": list(STAGE6_3_CONFIG.profile_keys),
                "primary_profile": STAGE6_3_CONFIG.primary_profile,
                "seeds": list(STAGE6_3_CONFIG.seeds),
                "target": "stage6_definitive_tp_vs_sl_flag",
                "ohlc_file": str(OHLC_FILE),
                "xgb_n_jobs": STAGE6_3_CONFIG.xgb_n_jobs,
            },
            "feature_contract": feature_contract,
            "input_manifest": stage63_input_file_manifest(),
            "raw_runs": [],
            "done_runs": 0,
            "total_runs": len(STAGE6_3_CONFIG.profile_keys) * len(STAGE6_3_CONFIG.seeds),
        }
        done_set = set()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2, default=str))
        print(f"[stage6.3] Started fresh report: {output_path}", flush=True)

    cfg = Stage60Config(
        horizon_bars=STAGE6_3_CONFIG.horizon_bars,
        stop_offset_atr=STAGE6_3_CONFIG.stop_offset_atr,
        take_profit_atr=STAGE6_3_CONFIG.take_profit_atr,
        entry_lag_bars=STAGE6_3_CONFIG.entry_lag_bars,
    )
    ohlc = stage62_load_ohlc_frame()
    split = stage6_load_labeled_splits(config=cfg)

    if "preflight" not in report:
        print("[stage6.3] Running preflight ...", flush=True)
        report["preflight"] = stage6_outcome_preflight(split)
        report["oracle_preflight"] = {
            name: stage6_all_trade_baseline(df)
            for name, df in split.items()
            if isinstance(df, pd.DataFrame)
        }
        output_path.write_text(json.dumps(report, indent=2, default=str))
        print("[stage6.3] Preflight done, saved checkpoint.", flush=True)

    total_runs = int(report["total_runs"])
    done_runs = int(report.get("done_runs", 0))
    for profile in STAGE6_3_CONFIG.profile_keys:
        print(f"[stage6.3] Building features for profile={profile} ...", flush=True)
        t0_profile = time.time()
        feature_split = {
            name: stage63_build_features(df, profile, ohlc=ohlc)
            for name, df in split.items()
            if isinstance(df, pd.DataFrame)
        }
        print(f"[stage6.3] Features built in {time.time() - t0_profile:.1f}s", flush=True)
        for seed in STAGE6_3_CONFIG.seeds:
            key = (profile, int(seed))
            if key in done_set:
                print(f"[stage6.3] SKIP profile={profile} seed={seed} (already done)", flush=True)
                continue
            t0_run = time.time()
            print(f"[stage6.3] Training profile={profile} seed={seed} ({done_runs + 1}/{total_runs}) ...", flush=True)
            result = evaluate_stage63_profile_seed(split, feature_split, profile, seed)
            result["elapsed_sec"] = float(time.time() - t0_run)
            report["raw_runs"].append(result)
            done_runs += 1
            report["done_runs"] = done_runs
            elapsed = time.time() - wall0
            remaining = (total_runs - done_runs) * (elapsed / max(done_runs, 1))
            print(f"[stage6.3] done {done_runs}/{total_runs} elapsed={elapsed:.0f}s ETA={remaining:.0f}s", flush=True)
            output_path.write_text(json.dumps(report, indent=2, default=str))

    report["summary"] = stage63_summary(report, split)
    report["baseline_plus_feature_delta"] = stage63_baseline_delta_summary(report)
    report["h6_vs_h12_disclosure"] = stage63_h6_vs_h12_disclosure(report, stage63_h12_summary_for_disclosure())
    report["gate"] = stage63_gate_results(report)
    report["status"] = report["gate"]["overall_status"]
    report["finished_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    report["elapsed_sec"] = float(time.time() - wall0)
    output_path.write_text(json.dumps(report, indent=2, default=str))
    return report


def main(argv: list[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage6-3-h6-feature-parity", action="store_true")
    parser.add_argument("--resume", action="store_true", default=True, dest="resume")
    parser.add_argument("--no-resume", action="store_false", dest="resume")
    args = parser.parse_args(argv)
    if args.stage6_3_h6_feature_parity:
        report = run_stage6_3_h6_feature_parity(resume=args.resume)
        print({"status": report.get("status"), "json": str(STAGE6_3_JSON_REPORT_PATH)})
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
