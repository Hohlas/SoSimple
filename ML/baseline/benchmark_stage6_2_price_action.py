from __future__ import annotations

# =============================================================================
# Файл: benchmark_stage6_2_price_action.py
# Назначение: Stage 6.2 H12 price-action benchmark для TP/SL touch outcome.
# Обновлён: 2026-06-30
# Зависимости:
#   Входные данные:
#     - DATA/Nero_XAUUSD_*_labeled.csv
#     - DATA/XAUUSD_H1_OHLC.csv
#   Выходные данные:
#     - ML/reports/stage6_2_h12_price_action_feature_family.json
#   Внутренние зависимости:
#     - ML/baseline/benchmark_stage6_outcome_based.py
#     - ML/baseline/benchmark_stage5_transformer_breach.py
# Использование:
#   ./.venv/bin/python ML/baseline/benchmark_stage6_2_price_action.py \
#     --stage6-2-price-action --resume
# Примечания:
#   - DIAGNOSTIC_ONLY: H12/SL/TP fixed, holdout disclosure-only.
# =============================================================================

import hashlib
import json
import sys
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np
import pandas as pd
from xgboost import XGBClassifier

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ML.baseline.benchmark_stage5_transformer_breach import (
    build_stage5_4_features,
    stage5_4_feature_names,
)
from ML.baseline.benchmark_stage6_outcome_based import (
    DATA_DIR,
    OHLC_FILE,
    REPORTS_DIR,
    STAGE6_0_CONFIG,
    stage6_all_trade_baseline,
    stage6_binary_metrics,
    stage6_feature_denylist,
    stage6_load_labeled_splits,
    stage6_outcome_preflight,
    stage6_permutation_threshold_baseline,
    stage6_select_threshold_on_val,
    stage6_simulate_threshold,
)


STAGE6_2_JSON_REPORT_PATH = REPORTS_DIR / "stage6_2_h12_price_action_feature_family.json"


@dataclass(frozen=True)
class Stage62Config:
    horizon_bars: int = 12
    stop_offset_atr: float = 0.5
    take_profit_atr: float = 2.0
    entry_lag_bars: int = 1
    primary_profile: str = "h12_price_action_core"
    profile_keys: tuple[str, ...] = (
        "h12_clock_shift_back",
        "h12_price_action_core",
        "h12_price_action_regime",
        "h12_clock_shift_back_plus_price_action_core",
        "h12_clock_shift_back_plus_price_action_regime",
    )
    seeds: tuple[int, ...] = (42, 77, 123)
    windows: tuple[int, ...] = (1, 3, 6, 12, 24)
    xgb_n_jobs: int = 24


STAGE6_2_CONFIG = Stage62Config()


def stage62_profile_keys() -> tuple[str, ...]:
    return STAGE6_2_CONFIG.profile_keys


def stage62_feature_denylist() -> tuple[str, ...]:
    prefixes = (
        "stage6_",
        "trade_",
        "fav_",
        "adv_",
        "ret_",
        "path_",
    )
    explicit = (
        "predict",
        "signal",
        "archetype_target",
        "trade_fav_h12",
        "trade_adv_h12",
        "trade_fav_h12_atr",
        "trade_adv_h12_atr",
        "trade_outcome_h12",
        "trade_pnl_h12_atr",
        "ret_6_dir_atr",
        "ret_12_dir_atr",
        "ret_24_dir_atr",
        "fav_3_atr",
        "adv_3_atr",
        "fav_6_atr",
        "adv_6_atr",
        "fav_12_atr",
        "adv_12_atr",
        "fav_24_atr",
        "adv_24_atr",
        "path_6_class",
        "buy_sl2_tp3",
        "buy_sl2_tp6",
        "buy_sl2_tp9",
        "buy_sl3_tp3",
        "buy_sl3_tp6",
        "buy_sl3_tp9",
        "sell_sl2_tp3",
        "sell_sl2_tp6",
        "sell_sl2_tp9",
        "sell_sl3_tp3",
        "sell_sl3_tp6",
        "sell_sl3_tp9",
    )
    breach_flags = tuple(
        f"{side}_stop_broken_H{h}_off{off}_flag"
        for side in ("buy", "sell")
        for h in (6, 12)
        for off in ("00", "02", "05")
    )
    breach_bars = tuple(
        f"{side}_bars_to_breach_H{h}_off{off}"
        for side in ("buy", "sell")
        for h in (6, 12)
        for off in ("00", "02", "05")
    )
    return tuple(stage6_feature_denylist()) + explicit + breach_flags + breach_bars + prefixes


def stage62_input_file_manifest() -> dict:
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


CORE_WINDOWS = STAGE6_2_CONFIG.windows
CORE_WINDOW_FIELDS = (
    "ret_close",
    "range",
    "close_to_high",
    "close_to_low",
    "close_pos",
)
CANDLE_FIELDS = (
    "body_1_atr",
    "abs_body_1_atr",
    "upper_wick_1_atr",
    "lower_wick_1_atr",
    "bar_range_1_atr",
)
REGIME_FIELDS = (
    "atr14_to_atr_row",
    "atr14_to_atr14_mean_24",
    "source_volume_to_source_volume_mean_24",
    "range_24_to_atr14",
)
COMBINED_TO_PRICE_ACTION = {
    "h12_clock_shift_back_plus_price_action_core": "h12_price_action_core",
    "h12_clock_shift_back_plus_price_action_regime": "h12_price_action_regime",
}


def stage62_load_ohlc_frame(path: Path = OHLC_FILE) -> pd.DataFrame:
    df = pd.read_csv(path, sep=";")
    df["time"] = pd.to_datetime(df["time"], format="%Y.%m.%d %H:%M", errors="coerce")
    df = df.dropna(subset=["time"]).sort_values("time").reset_index(drop=True)
    for col in ("open", "high", "low", "close", "volume", "atr14"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def stage62_price_action_feature_names(profile: str) -> list[str]:
    names = [
        f"{field}_w{window}_atr" if field != "close_pos" else f"{field}_w{window}"
        for window in CORE_WINDOWS
        for field in CORE_WINDOW_FIELDS
    ]
    names.extend(CANDLE_FIELDS)
    if profile == "h12_price_action_regime":
        names.extend(REGIME_FIELDS)
    if profile in {"h12_price_action_core", "h12_price_action_regime"}:
        return names
    raise ValueError(f"not a price-action profile: {profile}")


def _stage62_parse_time(value) -> pd.Timestamp | None:
    ts = pd.to_datetime(value, format="%Y.%m.%d %H:%M", errors="coerce")
    if pd.isna(ts):
        return None
    return pd.Timestamp(ts)


def _stage62_safe_div(num: float, den: float) -> float:
    if not np.isfinite(num) or not np.isfinite(den) or abs(den) < 1e-12:
        return 0.0
    return float(num / den)


def _stage62_ohlc_position(row_time: pd.Timestamp, ohlc: pd.DataFrame) -> int | None:
    times = ohlc["time"].to_numpy(dtype="datetime64[ns]")
    pos = int(np.searchsorted(times, np.datetime64(row_time), side="right") - 1)
    if pos < 0:
        return None
    if pd.Timestamp(ohlc.iloc[pos]["time"]) != row_time:
        return None
    return pos


def _stage62_price_action_row(row: pd.Series, ohlc: pd.DataFrame, profile: str) -> list[float]:
    row_time = _stage62_parse_time(row.get("time"))
    atr_row = float(row.get("ATR", 0.0) or 0.0)
    if row_time is None or atr_row <= 0.0:
        return [0.0] * len(stage62_price_action_feature_names(profile))

    pos = _stage62_ohlc_position(row_time, ohlc)
    if pos is None:
        return [0.0] * len(stage62_price_action_feature_names(profile))
    start = max(0, pos - max(CORE_WINDOWS))
    hist = ohlc.iloc[start:pos + 1]

    current = hist.iloc[-1]
    close_t = float(current["close"])
    open_t = float(current["open"])
    high_t = float(current["high"])
    low_t = float(current["low"])

    out: list[float] = []
    for window in CORE_WINDOWS:
        segment = hist.tail(window + 1)
        if len(segment) < window + 1:
            out.extend([0.0, 0.0, 0.0, 0.0, 0.0])
            continue
        prev_close = float(segment.iloc[0]["close"])
        max_high = float(segment["high"].max())
        min_low = float(segment["low"].min())
        width = max_high - min_low
        out.extend([
            _stage62_safe_div(close_t - prev_close, atr_row),
            _stage62_safe_div(width, atr_row),
            _stage62_safe_div(max_high - close_t, atr_row),
            _stage62_safe_div(close_t - min_low, atr_row),
            _stage62_safe_div(close_t - min_low, width),
        ])

    out.extend([
        _stage62_safe_div(close_t - open_t, atr_row),
        _stage62_safe_div(abs(close_t - open_t), atr_row),
        _stage62_safe_div(high_t - max(open_t, close_t), atr_row),
        _stage62_safe_div(min(open_t, close_t) - low_t, atr_row),
        _stage62_safe_div(high_t - low_t, atr_row),
    ])

    if profile == "h12_price_action_regime":
        hist24 = hist.tail(24)
        atr14_t = float(current.get("atr14", 0.0) or 0.0)
        volume_t = float(current.get("volume", 0.0) or 0.0)
        atr14_mean_24 = float(hist24["atr14"].mean()) if len(hist24) else 0.0
        volume_mean_24 = float(hist24["volume"].mean()) if len(hist24) else 0.0
        range_24 = float(hist24["high"].max() - hist24["low"].min()) if len(hist24) else 0.0
        out.extend([
            _stage62_safe_div(atr14_t, atr_row),
            _stage62_safe_div(atr14_t, atr14_mean_24),
            _stage62_safe_div(volume_t, volume_mean_24),
            _stage62_safe_div(range_24, atr14_t),
        ])
    return [float(np.nan_to_num(v, nan=0.0, posinf=0.0, neginf=0.0)) for v in out]


def stage62_build_price_action_features(
    df: pd.DataFrame,
    profile: str,
    ohlc: pd.DataFrame | None = None,
) -> np.ndarray:
    if profile not in {"h12_price_action_core", "h12_price_action_regime"}:
        raise ValueError(f"not a price-action profile: {profile}")
    frame = stage62_load_ohlc_frame() if ohlc is None else ohlc.copy()
    rows = [_stage62_price_action_row(row, frame, profile) for _, row in df.iterrows()]
    width = len(stage62_price_action_feature_names(profile))
    if not rows:
        return np.zeros((0, width), dtype=np.float32)
    return np.asarray(rows, dtype=np.float32)


def _stage62_drop_forbidden(df: pd.DataFrame) -> pd.DataFrame:
    forbidden_prefixes = ("stage6_", "trade_", "fav_", "adv_", "ret_", "path_")
    explicit = set(stage62_feature_denylist())
    cols = [
        c for c in df.columns
        if c in explicit or any(c.startswith(prefix) for prefix in forbidden_prefixes)
    ]
    return df.drop(columns=cols, errors="ignore")


def stage62_build_features(
    df: pd.DataFrame,
    profile: str,
    ohlc: pd.DataFrame | None = None,
) -> np.ndarray:
    clean = _stage62_drop_forbidden(df)
    if profile == "h12_clock_shift_back":
        return build_stage5_4_features(clean, "clock_shift_back")
    if profile in {"h12_price_action_core", "h12_price_action_regime"}:
        return stage62_build_price_action_features(clean, profile, ohlc=ohlc)
    if profile in COMBINED_TO_PRICE_ACTION:
        baseline = build_stage5_4_features(clean, "clock_shift_back")
        price_action = stage62_build_price_action_features(clean, COMBINED_TO_PRICE_ACTION[profile], ohlc=ohlc)
        return np.hstack([baseline, price_action]).astype(np.float32)
    raise ValueError(f"unknown Stage 6.2 profile: {profile}")


def stage62_feature_names(profile: str) -> list[str]:
    if profile == "h12_clock_shift_back":
        return stage5_4_feature_names("clock_shift_back")
    if profile in {"h12_price_action_core", "h12_price_action_regime"}:
        return stage62_price_action_feature_names(profile)
    if profile in COMBINED_TO_PRICE_ACTION:
        baseline_names = [f"baseline.{name}" for name in stage5_4_feature_names("clock_shift_back")]
        price_names = [
            f"price_action.{name}"
            for name in stage62_price_action_feature_names(COMBINED_TO_PRICE_ACTION[profile])
        ]
        return baseline_names + price_names
    raise ValueError(f"unknown Stage 6.2 profile: {profile}")


def stage62_definitive_mask(df: pd.DataFrame) -> np.ndarray:
    y = df["stage6_definitive_tp_vs_sl_flag"].to_numpy(dtype=np.float64)
    reason = df["stage6_close_reason"].astype(str)
    return np.isfinite(y) & reason.isin(["TP", "SL", "AMBIGUOUS_SL_FIRST"]).to_numpy()


def stage62_ohlc_contract_preflight(df: pd.DataFrame, ohlc: pd.DataFrame) -> dict:
    warnings = []
    times = ohlc["time"]
    if not times.is_monotonic_increasing:
        warnings.append("OHLC_TIME_NOT_MONOTONIC")
    if times.duplicated().any():
        warnings.append("OHLC_TIME_NOT_UNIQUE")

    missing = 0
    incomplete_24 = 0
    for value in df["time"]:
        row_time = _stage62_parse_time(value)
        if row_time is None:
            missing += 1
            continue
        pos = _stage62_ohlc_position(row_time, ohlc)
        if pos is None:
            missing += 1
            continue
        if pos < 24:
            incomplete_24 += 1

    status = "PASS"
    if missing > 0 or incomplete_24 > 0:
        status = "WARNING"
    if "OHLC_TIME_NOT_MONOTONIC" in warnings or "OHLC_TIME_NOT_UNIQUE" in warnings:
        status = "ERROR"
    return {
        "status": status,
        "rows": int(len(df)),
        "missing_exact_ohlc_rows": int(missing),
        "incomplete_window_24_rows": int(incomplete_24),
        "warnings": warnings,
    }


def _stage62_quantiles(values) -> dict:
    arr = np.asarray(values, dtype=np.float64)
    arr = arr[np.isfinite(arr)]
    if len(arr) == 0:
        return {"n": 0, "min": None, "p50": None, "p95": None, "p99": None, "max": None}
    return {
        "n": int(len(arr)),
        "min": float(np.min(arr)),
        "p50": float(np.percentile(arr, 50)),
        "p95": float(np.percentile(arr, 95)),
        "p99": float(np.percentile(arr, 99)),
        "max": float(np.max(arr)),
    }


def stage62_feature_distribution_audit(
    split: dict[str, pd.DataFrame],
    feature_split: dict[str, np.ndarray],
    profile: str,
) -> dict:
    del split
    out = {}
    names = stage62_feature_names(profile)
    for split_name, X in feature_split.items():
        finite = np.isfinite(X)
        status = "PASS" if finite.all() else "ERROR"
        zero_rate = float(np.mean(X == 0.0)) if X.size else 0.0
        tail_abs = np.abs(X[np.isfinite(X)])
        warnings = []
        if tail_abs.size and float(np.percentile(tail_abs, 99)) > 20.0:
            warnings.append("TAIL_ABS_P99_GT_20")
        if X.shape[1] != len(names):
            status = "ERROR"
            warnings.append("FEATURE_NAME_COUNT_MISMATCH")
        out[split_name] = {
            "status": status,
            "rows": int(X.shape[0]),
            "cols": int(X.shape[1]) if X.ndim == 2 else 0,
            "finite_rate": float(np.mean(finite)) if finite.size else 1.0,
            "zero_rate": zero_rate,
            "all_zero_rows": int(np.sum(np.all(X == 0.0, axis=1))) if X.ndim == 2 and X.size else 0,
            "abs_value": _stage62_quantiles(tail_abs),
            "warnings": warnings,
        }
    return out


def stage62_feature_preflight(
    split: dict[str, pd.DataFrame],
    ohlc: pd.DataFrame | None = None,
) -> dict:
    frame = stage62_load_ohlc_frame() if ohlc is None else ohlc
    out = {}
    for profile in stage62_profile_keys():
        feature_split = {
            name: stage62_build_features(df, profile, ohlc=frame)
            for name, df in split.items()
            if isinstance(df, pd.DataFrame)
        }
        out[profile] = {
            "ohlc_contract": {
                name: stage62_ohlc_contract_preflight(df, frame)
                for name, df in split.items()
                if isinstance(df, pd.DataFrame)
            },
            "feature_distribution": stage62_feature_distribution_audit(split, feature_split, profile),
        }
    return out


def stage62_permutation_feature_importance(
    model,
    X_val: np.ndarray,
    y_val: np.ndarray,
    profile: str,
    seed: int,
    top_n: int = 10,
) -> list[dict]:
    if len(np.unique(y_val)) < 2:
        return []
    rng = np.random.default_rng(seed)
    baseline_score = float(stage6_binary_metrics(y_val, model.predict_proba(X_val)[:, 1])["auc"])
    names = stage62_feature_names(profile)
    rows = []
    for idx, name in enumerate(names):
        X_perm = X_val.copy()
        X_perm[:, idx] = rng.permutation(X_perm[:, idx])
        perm_score = float(stage6_binary_metrics(y_val, model.predict_proba(X_perm)[:, 1])["auc"])
        rows.append({
            "feature": name,
            "auc_drop": float(baseline_score - perm_score),
            "baseline_auc": baseline_score,
            "permuted_auc": perm_score,
        })
    rows.sort(key=lambda item: item["auc_drop"], reverse=True)
    return rows[:top_n]


def evaluate_stage62_profile_seed(
    split: dict[str, pd.DataFrame],
    feature_split: dict[str, np.ndarray],
    profile: str,
    seed: int,
) -> dict:
    train = split["train_core"]
    val = split["val_stop"]
    train_mask = stage62_definitive_mask(train)
    val_mask = stage62_definitive_mask(val)
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
        n_jobs=STAGE6_2_CONFIG.xgb_n_jobs,
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
        "feature_importance": [] if profile == "h12_clock_shift_back" else stage62_permutation_feature_importance(
            clf, X_val[val_mask], y_val[val_mask], profile, seed=seed
        ),
    }
    for split_name in ("diagnostic_holdout", "low_n_disclosure"):
        df = split[split_name]
        X = feature_split[split_name]
        mask = stage62_definitive_mask(df)
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


def _stage62_median(values) -> float | None:
    vals = [v for v in values if v is not None and np.isfinite(v)]
    return float(np.median(vals)) if vals else None


def stage62_baseline_delta_summary(report: dict) -> dict:
    summary = report.get("summary", {})
    baseline = summary.get("h12_clock_shift_back", {})
    baseline_auc = baseline.get("val_stop", {}).get("auc_median")
    baseline_pr = baseline.get("val_stop", {}).get("pr_auc_lift_median")
    baseline_selected = (baseline.get("threshold_selection", {}) or {}).get("selected") or {}
    baseline_pf = baseline.get("threshold_selection", {}).get("val_pf_median", baseline_selected.get("pf"))
    rows = {}
    any_pass = False
    for profile in (
        "h12_clock_shift_back_plus_price_action_core",
        "h12_clock_shift_back_plus_price_action_regime",
    ):
        item = summary.get(profile, {})
        auc = item.get("val_stop", {}).get("auc_median")
        pr = item.get("val_stop", {}).get("pr_auc_lift_median")
        threshold = item.get("threshold_selection", {}) or {}
        selected = threshold.get("selected") or {}
        pf = threshold.get("val_pf_median", selected.get("pf"))
        perm = item.get("permutation_baseline") or {}
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
        any_pass = any_pass or bool(passes)
    return {
        "baseline_profile": "h12_clock_shift_back",
        "profiles": rows,
        "any_delta_gate_pass": bool(any_pass),
        "delta_gate": {
            "auc_delta_ge_0_02": 0.02,
            "pr_auc_lift_delta_ge_0": 0.0,
            "pf_delta_ge_0": 0.0,
            "permutation_p_value_le_0_10": 0.10,
        },
    }


def stage62_gate_results(report: dict) -> dict:
    summary = report.get("summary", {})
    primary = summary.get(STAGE6_2_CONFIG.primary_profile, {})
    val = primary.get("val_stop", {})
    threshold = primary.get("threshold_selection", {})
    selected = threshold.get("selected") or {}
    perm = primary.get("permutation_baseline") or {}
    checks = {
        "primary_auc_ge_0_60": bool(val.get("auc_median") is not None and val["auc_median"] >= 0.60),
        "primary_pr_auc_lift_ge_0_05": bool(
            val.get("pr_auc_lift_median") is not None and val["pr_auc_lift_median"] >= 0.05
        ),
        "primary_threshold_selected": bool(threshold.get("status") == "SELECTED" and selected),
        "primary_permutation_p_value_le_0_10": bool(
            perm.get("empirical_p_value") is not None and perm["empirical_p_value"] <= 0.10
        ),
        "primary_pf_ge_1_15": bool(selected.get("pf") is not None and selected["pf"] >= 1.15),
        "primary_trades_per_year_ge_25": bool(selected.get("trades_per_year", 0) >= 25),
        "primary_spread_020_pf_ge_1_05": bool(
            selected.get("pf_spread_020") is not None and selected["pf_spread_020"] >= 1.05
        ),
        "any_delta_gate_pass": bool(
            (report.get("baseline_plus_price_action_delta") or {}).get("any_delta_gate_pass", False)
        ),
    }
    primary_model_pass = checks["primary_auc_ge_0_60"] and checks["primary_pr_auc_lift_ge_0_05"]
    primary_trading_pass = (
        primary_model_pass
        and checks["primary_threshold_selected"]
        and checks["primary_permutation_p_value_le_0_10"]
        and checks["primary_pf_ge_1_15"]
        and checks["primary_trades_per_year_ge_25"]
        and checks["primary_spread_020_pf_ge_1_05"]
    )
    if checks["any_delta_gate_pass"]:
        return {
            "overall_status": "DIAGNOSTIC_SIGNAL_FOUND",
            "artifact_status": "DIAGNOSTIC_ONLY",
            "interpretation": "ADDITIVE_VALUE_OVER_BASELINE_FOUND",
            "checks": checks,
        }
    if primary_trading_pass:
        return {
            "overall_status": "DIAGNOSTIC_SIGNAL_FOUND",
            "artifact_status": "DIAGNOSTIC_ONLY",
            "interpretation": "STANDALONE_ONLY_NO_ADDITIVE_VALUE_CONFIRMED",
            "checks": checks,
        }
    if not primary_model_pass and not checks["any_delta_gate_pass"]:
        return {"overall_status": "MODEL_GATE_FAILED", "artifact_status": "DIAGNOSTIC_ONLY", "checks": checks}
    return {"overall_status": "TRADING_GATE_FAILED", "artifact_status": "DIAGNOSTIC_ONLY", "checks": checks}


def stage62_summary(report: dict, split: dict[str, pd.DataFrame]) -> dict:
    summary = {}
    for profile in STAGE6_2_CONFIG.profile_keys:
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
        best_run = max(runs, key=lambda r: r["val_stop"].get("auc") or 0.0)
        val_scores = best_run.get("predictions", {}).get("val_stop", {}).get("y_score_all", [])
        perm = None
        if val_scores and "_year" in split["val_stop"].columns:
            perm = stage6_permutation_threshold_baseline(split["val_stop"].copy(), np.asarray(val_scores), seed=42)
        summary[profile] = {
            "val_stop": {
                "auc_median": _stage62_median(aucs),
                "pr_auc_lift_median": _stage62_median(lifts),
            },
            "threshold_selection": {
                "status": "SELECTED" if selected else "NO_THRESHOLD",
                "selected": selected[len(selected) // 2] if selected else None,
                "n_selected": len(selected),
                "val_pf_median": _stage62_median([s.get("pf") for s in selected]),
            },
            "diagnostic_holdout": {
                "auc_median": _stage62_median([r.get("diagnostic_holdout", {}).get("auc") for r in runs]),
                "pr_auc_lift_median": _stage62_median([
                    r.get("diagnostic_holdout", {}).get("pr_auc_lift") for r in runs
                ]),
            },
            "low_n_disclosure": {
                "auc_median": _stage62_median([r.get("low_n_disclosure", {}).get("auc") for r in runs]),
                "pr_auc_lift_median": _stage62_median([
                    r.get("low_n_disclosure", {}).get("pr_auc_lift") for r in runs
                ]),
            },
            "permutation_baseline": perm,
            "top_feature_importance": best_run.get("feature_importance", []),
        }
    return summary


def run_stage6_2_price_action(
    output_path: Path = STAGE6_2_JSON_REPORT_PATH,
    resume: bool = True,
) -> dict:
    import datetime
    import time

    started_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    wall0 = time.time()
    if resume and output_path.exists():
        report = json.loads(output_path.read_text())
        done_set = {(r["profile"], int(r["seed"])) for r in report.get("raw_runs", [])}
        print(f"[stage6.2] RESUME existing report: {output_path}", flush=True)
        print(
            f"[stage6.2] Already done: {len(done_set)} runs "
            f"({report.get('done_runs', 0)}/{report.get('total_runs', '?')})",
            flush=True,
        )
        report["resumed_at"] = started_at
    else:
        feature_contract = {
            profile: {
                "feature_names": stage62_feature_names(profile),
                "feature_names_sha256": hashlib.sha256(
                    "\n".join(stage62_feature_names(profile)).encode("utf-8")
                ).hexdigest(),
                "feature_count": len(stage62_feature_names(profile)),
            }
            for profile in STAGE6_2_CONFIG.profile_keys
        }
        report = {
            "stage": "6.2",
            "status": "RUNNING",
            "started_at": started_at,
            "config": {
                "horizon_bars": STAGE6_2_CONFIG.horizon_bars,
                "stop_offset_atr": STAGE6_2_CONFIG.stop_offset_atr,
                "take_profit_atr": STAGE6_2_CONFIG.take_profit_atr,
                "entry_lag_bars": STAGE6_2_CONFIG.entry_lag_bars,
                "profiles": list(STAGE6_2_CONFIG.profile_keys),
                "primary_profile": STAGE6_2_CONFIG.primary_profile,
                "seeds": list(STAGE6_2_CONFIG.seeds),
                "windows": list(STAGE6_2_CONFIG.windows),
                "target": "stage6_definitive_tp_vs_sl_flag",
                "ohlc_file": str(OHLC_FILE),
                "xgb_n_jobs": STAGE6_2_CONFIG.xgb_n_jobs,
            },
            "feature_contract": feature_contract,
            "input_manifest": stage62_input_file_manifest(),
            "raw_runs": [],
            "done_runs": 0,
            "total_runs": len(STAGE6_2_CONFIG.profile_keys) * len(STAGE6_2_CONFIG.seeds),
        }
        done_set = set()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2, default=str))
        print(f"[stage6.2] Started fresh report: {output_path}", flush=True)

    cfg = replace(
        STAGE6_0_CONFIG,
        horizon_bars=STAGE6_2_CONFIG.horizon_bars,
        stop_offset_atr=STAGE6_2_CONFIG.stop_offset_atr,
        take_profit_atr=STAGE6_2_CONFIG.take_profit_atr,
        entry_lag_bars=STAGE6_2_CONFIG.entry_lag_bars,
    )
    ohlc = stage62_load_ohlc_frame()
    split = stage6_load_labeled_splits(config=cfg)

    if "preflight" not in report:
        print("[stage6.2] Running preflight ...", flush=True)
        report["preflight"] = stage6_outcome_preflight(split)
        report["feature_preflight"] = stage62_feature_preflight(split, ohlc=ohlc)
        report["oracle_preflight"] = {
            name: stage6_all_trade_baseline(df)
            for name, df in split.items()
            if isinstance(df, pd.DataFrame)
        }
        output_path.write_text(json.dumps(report, indent=2, default=str))
        print("[stage6.2] Preflight done, saved checkpoint.", flush=True)

    total_runs = int(report["total_runs"])
    done_runs = int(report.get("done_runs", 0))
    for profile in STAGE6_2_CONFIG.profile_keys:
        print(f"[stage6.2] Building features for profile={profile} ...", flush=True)
        t0_profile = time.time()
        feature_split = {
            name: stage62_build_features(df, profile, ohlc=ohlc)
            for name, df in split.items()
            if isinstance(df, pd.DataFrame)
        }
        print(f"[stage6.2] Features built in {time.time() - t0_profile:.1f}s", flush=True)
        for seed in STAGE6_2_CONFIG.seeds:
            key = (profile, int(seed))
            if key in done_set:
                print(f"[stage6.2] SKIP profile={profile} seed={seed} (already done)", flush=True)
                continue
            t0_run = time.time()
            print(f"[stage6.2] Training profile={profile} seed={seed} ({done_runs + 1}/{total_runs}) ...", flush=True)
            result = evaluate_stage62_profile_seed(split, feature_split, profile, seed)
            result["elapsed_sec"] = float(time.time() - t0_run)
            report["raw_runs"].append(result)
            done_runs += 1
            report["done_runs"] = done_runs
            elapsed = time.time() - wall0
            remaining = (total_runs - done_runs) * (elapsed / max(done_runs, 1))
            print(f"[stage6.2] done {done_runs}/{total_runs} elapsed={elapsed:.0f}s ETA={remaining:.0f}s", flush=True)
            output_path.write_text(json.dumps(report, indent=2, default=str))

    report["summary"] = stage62_summary(report, split)
    report["baseline_plus_price_action_delta"] = stage62_baseline_delta_summary(report)
    report["gate"] = stage62_gate_results(report)
    report["status"] = report["gate"]["overall_status"]
    report["finished_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    report["elapsed_sec"] = float(time.time() - wall0)
    output_path.write_text(json.dumps(report, indent=2, default=str))
    return report


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--stage6-2-price-action", action="store_true")
    parser.add_argument("--resume", action="store_true", default=True, dest="resume")
    parser.add_argument("--no-resume", action="store_false", dest="resume")
    args = parser.parse_args(argv)
    if args.stage6_2_price_action:
        report = run_stage6_2_price_action(resume=args.resume)
        print({"status": report.get("status"), "json": str(STAGE6_2_JSON_REPORT_PATH)})
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
