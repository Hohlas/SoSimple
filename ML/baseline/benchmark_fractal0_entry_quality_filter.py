# =============================================================================
# Файл: benchmark_fractal0_entry_quality_filter.py
# Назначение: Research-runner ML-entry фильтра для E3 Fractal0 поверх
#   существующего stop-grid/M5 runner без отдельной копии симулятора.
# Обновлён: 2026-07-21
# Примечания:
#   - locked_test не открывается; максимальный verdict — research_only.
# =============================================================================
from __future__ import annotations

import argparse
import dataclasses
import json
import math
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesClassifier, ExtraTreesRegressor, RandomForestClassifier, RandomForestRegressor
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.linear_model import LogisticRegression, Ridge

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import ML.baseline.benchmark_fractal0_entry_exit_grid as base


DEFAULT_STOP_GRID_ARTIFACT = "ML/reports/fractal0_stop_grid_m5.json"
DEFAULT_OUTPUT_PREFIX = "ML/reports/fractal0_entry_quality_filter"
DEFAULT_NARROW_ENTRY_QUALITY_ARTIFACT = "ML/reports/fractal0_entry_quality_filter.json"
RICH_ALLOWED_MAX_VERDICT = "RESEARCH_HINT_RICH_FEATURES"
RICH_OUTPUT_PREFIX = "ML/reports/fractal0_rich_entry_quality"
ENTRY_ID = "E3_open_pullback_1_0atr"
MASK_ID = "M0_no_mask"
RICH_PRIMARY_TOP_FRACTIONS = (0.50, 0.40, 0.30)
RICH_DIAGNOSTIC_TOP_FRACTIONS = (0.20, 0.10)
RICH_TARGET_IDS = (
    "target_entry_ev_regression",
    "target_entry_good_0_5r",
    "target_entry_avoid_sl",
)

ENTRY_FEATURE_COLUMNS = [
    "side_buy",
    "ATR",
    "entry_to_fractal0_atr",
    "stop_distance_atr",
    "r_value_atr",
]
SCORE_DIAGNOSTIC_COLUMNS = [
    "movement_score",
    "stop_distance_atr",
    "r_value_atr",
    "entry_quality_score",
    "entry_avoid_sl_score",
]
FORBIDDEN_FEATURE_PREFIXES = (
    "up_",
    "dn_",
    "ret_",
    "fav_",
    "adv_",
    "entry_up_",
    "entry_dn_",
    "entry_log_ratio_",
    "trail_",
    "target_",
    "label_",
    "outcome_",
)
FORBIDDEN_FEATURE_EXACT = {"pnl_r", "close_reason", "hold_bars", "exit_time", "target_leak", "signal", "predict", "fill_lag"}
FRACTAL_FIELD_NAMES = (
    "time",
    "price",
    "direction",
    "front",
    "back",
    "strong",
    "break",
    "reverse",
    "power",
    "count",
    "impulse",
    "up_12",
    "dn_12",
    "up_24",
    "dn_24",
    "up_48",
    "dn_48",
    "up_3",
    "dn_3",
    "up_6",
    "dn_6",
    "fractal_atr",
    "shift",
)


def _path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else PROJECT_ROOT / path


def entry_filter_grid() -> list[dict[str, object]]:
    filters: list[dict[str, object]] = [
        {"filter_id": "M0_no_mask", "family": "none", "score_col": None, "top_fraction": 1.0}
    ]
    for fraction in (0.50, 0.30, 0.20, 0.10):
        filters.append({"filter_id": f"movement_top{int(fraction * 100)}", "family": "movement", "score_col": "movement_score", "top_fraction": fraction})
    for fraction in (0.50, 0.30):
        filters.append({"filter_id": f"simple_stop_distance_top{int(fraction * 100)}", "family": "simple_stop_distance", "score_col": "stop_distance_atr", "top_fraction": fraction})
    for fraction in (0.50, 0.30):
        filters.append({"filter_id": f"simple_r_value_top{int(fraction * 100)}", "family": "simple_r_value", "score_col": "r_value_atr", "top_fraction": fraction})
    for fraction in (0.50, 0.30, 0.20, 0.10):
        filters.append({"filter_id": f"entry_quality_top{int(fraction * 100)}", "family": "entry_quality", "score_col": "entry_quality_score", "top_fraction": fraction})
    for fraction in (0.50, 0.30, 0.20, 0.10):
        filters.append({"filter_id": f"entry_avoid_sl_top{int(fraction * 100)}", "family": "entry_avoid_sl", "score_col": "entry_avoid_sl_score", "top_fraction": fraction})
    return filters


def rich_feature_profile_grid() -> list[dict[str, object]]:
    return [
        {"profile_id": "planned_geometry_only", "eligible_for_winner": True, "selection_basis": "planned_geometry"},
        {"profile_id": "time_only", "eligible_for_winner": True, "selection_basis": "time"},
        {"profile_id": "structure_f0_only", "eligible_for_winner": True, "selection_basis": "fractal0_only"},
        {"profile_id": "structure_nearest_k20", "eligible_for_winner": True, "selection_basis": "nearest_to_planned_limit"},
        {"profile_id": "structure_nearest_k40", "eligible_for_winner": True, "selection_basis": "nearest_to_planned_limit"},
        {"profile_id": "relative_geometry_k40", "eligible_for_winner": True, "selection_basis": "nearest_to_planned_limit"},
        {"profile_id": "price_action_h1", "eligible_for_winner": True, "selection_basis": "last_closed_h1"},
        {"profile_id": "movement_plus_time", "eligible_for_winner": True, "selection_basis": "frozen_movement_score_plus_time"},
        {"profile_id": "rich_combined_k40", "eligible_for_winner": True, "selection_basis": "nearest_to_planned_limit_plus_geometry_time_h1"},
        {"profile_id": "structure_nearest_k80", "eligible_for_winner": False, "selection_basis": "nearest_to_planned_limit"},
        {"profile_id": "structure_all100", "eligible_for_winner": False, "selection_basis": "recent_all100"},
    ]


def rich_model_grid(include_diagnostic_models: bool = False) -> list[dict[str, object]]:
    models = [
        {"model_id": "linear", "eligible_for_winner": True, "runnable_by_default": True},
        {"model_id": "hist_gradient_boosting", "eligible_for_winner": True, "runnable_by_default": True},
        {"model_id": "extra_trees_shallow", "eligible_for_winner": True, "runnable_by_default": True},
    ]
    if include_diagnostic_models:
        models.extend(
            [
                {"model_id": "extra_trees_current", "eligible_for_winner": False, "runnable_by_default": True},
                {"model_id": "random_forest_shallow", "eligible_for_winner": False, "runnable_by_default": True},
                {"model_id": "xgboost_depth3", "eligible_for_winner": False, "runnable_by_default": False, "listed_but_not_runnable": True},
                {"model_id": "xgboost_depth5", "eligible_for_winner": False, "runnable_by_default": False, "listed_but_not_runnable": True},
                {"model_id": "lightgbm_small", "eligible_for_winner": False, "runnable_by_default": False, "listed_but_not_runnable": True},
            ]
        )
    return models


def rich_target_grid() -> list[dict[str, object]]:
    return [
        {"target_id": "target_entry_ev_regression", "kind": "regression", "eligible_for_winner": True},
        {"target_id": "target_entry_good_0_5r", "kind": "classification", "eligible_for_winner": True},
        {"target_id": "target_entry_avoid_sl", "kind": "classification", "eligible_for_winner": True},
        {"target_id": "target_entry_filled", "kind": "classification", "eligible_for_winner": False},
        {"target_id": "target_entry_good_0_25r", "kind": "classification", "eligible_for_winner": False},
        {"target_id": "target_entry_good_1r", "kind": "classification", "eligible_for_winner": False},
        {"target_id": "target_entry_avoid_bad", "kind": "classification", "eligible_for_winner": False},
    ]


def rich_filter_grid() -> list[dict[str, object]]:
    filters = [{"filter_id": "M0_no_mask", "top_fraction": 1.0, "eligible_for_winner": False}]
    for fraction in RICH_PRIMARY_TOP_FRACTIONS:
        filters.append({"filter_id": f"top{int(fraction * 100)}", "top_fraction": fraction, "eligible_for_winner": True})
    for fraction in RICH_DIAGNOSTIC_TOP_FRACTIONS:
        filters.append({"filter_id": f"top{int(fraction * 100)}", "top_fraction": fraction, "eligible_for_winner": False})
    return filters


def compute_search_budget(
    profiles: list[dict[str, object]],
    models: list[dict[str, object]],
    targets: list[dict[str, object]],
    filters: list[dict[str, object]],
) -> dict[str, object]:
    eligible_profiles = [p for p in profiles if p.get("eligible_for_winner")]
    eligible_models = [m for m in models if m.get("eligible_for_winner")]
    eligible_targets = [t for t in targets if t.get("eligible_for_winner")]
    eligible_filters = [f for f in filters if f.get("eligible_for_winner")]
    ranked = len(eligible_profiles) * len(eligible_models) * len(eligible_targets) * len(eligible_filters)
    return {
        "n_profiles": len(eligible_profiles),
        "n_models": len(eligible_models),
        "n_targets": len(eligible_targets),
        "n_primary_filters": len(eligible_filters),
        "n_seeds": 1,
        "n_total_ranked_configs": ranked,
        "n_diagnostic_configs": len(profiles) * len(models) * len(targets) * len(filters) - ranked,
        "n_total_executed_configs_default": ranked,
    }


def score_cutoff_for_top_fraction(rows: pd.DataFrame, score_col: str, fraction: float) -> float:
    if score_col not in rows.columns:
        return math.nan
    scores = pd.to_numeric(rows[score_col], errors="coerce").dropna()
    if scores.empty:
        return math.nan
    count = max(1, int(math.ceil(len(scores) * float(fraction))))
    return float(scores.sort_values(ascending=False).iloc[count - 1])


def select_top_fraction(rows: pd.DataFrame, score_col: str, fraction: float) -> pd.DataFrame:
    if score_col not in rows.columns:
        return rows.iloc[0:0].copy()
    scored = rows.assign(_score=pd.to_numeric(rows[score_col], errors="coerce")).dropna(subset=["_score"])
    if scored.empty:
        return rows.copy()
    count = max(1, int(math.ceil(len(scored) * float(fraction))))
    return scored.sort_values("_score", ascending=False).head(count).drop(columns=["_score"]).copy()


def build_entry_labels(trades: pd.DataFrame) -> pd.DataFrame:
    out = trades.copy()
    out["target_entry_good"] = (pd.to_numeric(out["pnl_r"], errors="coerce") > 0.0).astype(int)
    out["target_entry_avoid_sl"] = (~out["close_reason"].astype(str).eq("SL")).astype(int)
    return out


def build_rich_entry_labels(planned_orders: pd.DataFrame, trades: pd.DataFrame) -> pd.DataFrame:
    out = planned_orders[["position_id", "filled"]].copy()
    out = out.rename(columns={"filled": "order_filled"})
    realized = trades[["position_id", "pnl_r", "close_reason"]].copy() if not trades.empty else pd.DataFrame(columns=["position_id", "pnl_r", "close_reason"])
    realized["pnl_r_if_filled"] = pd.to_numeric(realized["pnl_r"], errors="coerce")
    out = out.merge(realized[["position_id", "pnl_r_if_filled", "close_reason"]], on="position_id", how="left")
    pnl = pd.to_numeric(out["pnl_r_if_filled"], errors="coerce")
    out["target_entry_ev_regression"] = pnl
    out["target_entry_good_0_5r"] = np.where(pnl.notna(), (pnl >= 0.5).astype(int), pd.NA)
    out["target_entry_good_0_25r"] = np.where(pnl.notna(), (pnl >= 0.25).astype(int), pd.NA)
    out["target_entry_good_1r"] = np.where(pnl.notna(), (pnl >= 1.0).astype(int), pd.NA)
    out["target_entry_avoid_bad"] = np.where(pnl.notna(), (pnl > -0.5).astype(int), pd.NA)
    out["target_entry_avoid_sl"] = np.where(
        out["close_reason"].notna(),
        (~out["close_reason"].astype(str).eq("SL")).astype(int),
        pd.NA,
    )
    out["target_entry_filled"] = out["order_filled"].fillna(False).astype(bool).astype(int)
    return out


def planned_order_diagnostics(planned_orders: pd.DataFrame, trades: pd.DataFrame, split: str) -> dict[str, object]:
    planned_n = int(len(planned_orders))
    filled_n = int(planned_orders.get("filled", pd.Series(dtype=bool)).fillna(False).astype(bool).sum())
    pnl = pd.to_numeric(trades.get("pnl_r"), errors="coerce").dropna() if "pnl_r" in trades else pd.Series(dtype=float)
    total_pnl = float(pnl.sum()) if len(pnl) else 0.0
    return {
        "split": split,
        "planned_orders": planned_n,
        "filled_orders": filled_n,
        "no_fill_orders": int(planned_n - filled_n),
        "fill_rate": float(filled_n / planned_n) if planned_n else 0.0,
        "no_fill_rate": float((planned_n - filled_n) / planned_n) if planned_n else 0.0,
        "expected_pnl_per_filled_trade": float(pnl.mean()) if len(pnl) else None,
        "expected_pnl_per_planned_order": float(total_pnl / planned_n) if planned_n else None,
    }


def build_entry_feature_frame(entries: pd.DataFrame) -> pd.DataFrame:
    out = entries.copy()
    atr = pd.to_numeric(out["ATR"], errors="coerce").replace(0, pd.NA)
    entry_bid_equivalent = pd.to_numeric(
        out["planned_entry_bid_equivalent"] if "planned_entry_bid_equivalent" in out else out["entry_bid_equivalent"],
        errors="coerce",
    )
    protective_stop = pd.to_numeric(
        out["planned_protective_stop_price"] if "planned_protective_stop_price" in out else out["protective_stop_price"],
        errors="coerce",
    )
    r_value = pd.to_numeric(out["planned_r_value"] if "planned_r_value" in out else out["r_value"], errors="coerce")
    out["side_buy"] = out["side"].astype(str).eq("BUY").astype(int)
    out["entry_to_fractal0_atr"] = (
        entry_bid_equivalent - pd.to_numeric(out["fractal0_price"], errors="coerce")
    ) / atr
    out["stop_distance_atr"] = (
        entry_bid_equivalent - protective_stop
    ).abs() / atr
    out["r_value_atr"] = r_value / atr
    return out


def _assert_no_forbidden_feature_columns(columns: list[str]) -> None:
    bad = [
        col for col in columns
        if col in FORBIDDEN_FEATURE_EXACT or col.startswith(FORBIDDEN_FEATURE_PREFIXES) or "_pnl_" in col
    ]
    if bad:
        raise ValueError(f"forbidden feature columns: {bad[:10]}")


def parse_serialized_fractal(value: object) -> dict[str, object] | None:
    if pd.isna(value) or value == "":
        return None
    parts = str(value).split(":")
    if len(parts) != len(FRACTAL_FIELD_NAMES):
        return None
    parsed: dict[str, object] = {}
    for name, raw in zip(FRACTAL_FIELD_NAMES, parts):
        parsed[name] = raw if name == "time" else float(raw)
    return parsed


def rich_feature_allowlist(profile_id: str) -> list[str]:
    planned = ["side_buy", "ATR", "entry_to_fractal0_atr", "stop_distance_atr", "r_value_atr"]
    time_cols = ["session_hour", "weekday", "hour_sin", "hour_cos", "weekday_sin", "weekday_cos"]
    h1_cols = ["h1_open", "h1_high", "h1_low", "h1_close", "h1_body", "h1_range", "h1_close_position_in_range"]
    movement = ["movement_score"]
    if profile_id == "planned_geometry_only":
        return planned
    if profile_id == "time_only":
        return time_cols
    if profile_id == "price_action_h1":
        return h1_cols
    if profile_id == "movement_plus_time":
        return movement + time_cols
    if profile_id == "structure_f0_only":
        return [f"fractal0_{field}" for field in ("price", "direction", "front", "back", "strong", "break", "reverse", "power", "count", "impulse", "fractal_atr", "shift", "up_3", "dn_3", "up_6", "dn_6", "up_12", "dn_12", "up_24", "dn_24", "up_48", "dn_48")]
    if profile_id in {"structure_nearest_k20", "structure_nearest_k40", "relative_geometry_k40", "rich_combined_k40"}:
        k = 20 if profile_id == "structure_nearest_k20" else 40
        fractal_cols: list[str] = []
        for idx in range(k):
            fractal_cols.extend(
                [
                    f"fractal{idx}_price_rel_f0",
                    f"fractal{idx}_direction",
                    f"fractal{idx}_front",
                    f"fractal{idx}_back",
                    f"fractal{idx}_strong",
                    f"fractal{idx}_break",
                    f"fractal{idx}_reverse",
                    f"fractal{idx}_power",
                    f"fractal{idx}_count",
                    f"fractal{idx}_impulse",
                    f"fractal{idx}_fractal_atr",
                    f"fractal{idx}_shift",
                    f"fractal{idx}_distance_to_planned_limit",
                    f"fractal{idx}_distance_to_planned_stop",
                ]
            )
        if profile_id == "relative_geometry_k40":
            return fractal_cols
        if profile_id == "rich_combined_k40":
            return planned + time_cols + h1_cols + fractal_cols
        return fractal_cols
    if profile_id == "structure_nearest_k80":
        return rich_feature_allowlist("structure_nearest_k40")
    if profile_id == "structure_all100":
        return rich_feature_allowlist("structure_nearest_k40")
    raise ValueError(f"unknown rich feature profile: {profile_id}")


def _attach_closed_h1_features(out: pd.DataFrame, ohlc: pd.DataFrame) -> tuple[pd.DataFrame, list[dict[str, object]]]:
    audit: list[dict[str, object]] = []
    if ohlc.empty or "time" not in ohlc:
        return out, audit
    bars = ohlc.copy()
    bars["time"] = pd.to_datetime(bars["time"])
    bars = bars.sort_values("time")
    base_cols = ["open", "high", "low", "close"]
    right = bars[["time", *base_cols]].rename(columns={col: f"h1_{col}" for col in base_cols})
    left = out.reset_index().sort_values("time").copy()
    left["_lookup_time"] = pd.to_datetime(left["time"]) - pd.Timedelta(nanoseconds=1)
    merged = pd.merge_asof(
        left,
        right,
        left_on="_lookup_time",
        right_on="time",
        direction="backward",
        allow_exact_matches=True,
    ).sort_values("index")
    for col in base_cols:
        name = f"h1_{col}"
        out[name] = merged[name].to_numpy()
        audit.append(
            {
                "feature": name,
                "source": "DATA/XAUUSD_H1_OHLC.csv",
                "bar_offset": 0,
                "requires_bar_close": True,
                "available_at": "last_fully_closed_h1_bar",
                "live_safe": True,
            }
        )
    out["h1_body"] = out["h1_close"] - out["h1_open"]
    out["h1_range"] = out["h1_high"] - out["h1_low"]
    out["h1_close_position_in_range"] = (out["h1_close"] - out["h1_low"]) / out["h1_range"].replace(0, pd.NA)
    return out, audit


def extract_fractal_feature_dict(row: pd.Series, k: int, selection_basis: str = "recent") -> dict[str, float]:
    result: dict[str, float] = {}
    fractal0 = parse_serialized_fractal(row.get("fractal0"))
    base_price = float(row.get("fractal0_price", fractal0.get("price") if fractal0 else 0.0) or 0.0)
    planned_limit = float(row.get("planned_entry_bid_equivalent") or 0.0)
    planned_stop = float(row.get("planned_protective_stop_price") or 0.0)
    parsed_items: list[dict[str, object]] = []
    for source_idx in range(100):
        parsed = parse_serialized_fractal(row.get(f"fractal{source_idx}"))
        if parsed:
            parsed_items.append({**parsed, "_source_idx": source_idx})
    if selection_basis == "nearest_to_planned_limit":
        parsed_items = sorted(parsed_items, key=lambda item: (abs(float(item["price"]) - planned_limit), int(item["_source_idx"])))
    else:
        parsed_items = sorted(parsed_items, key=lambda item: int(item["_source_idx"]))
    for idx in range(k):
        prefix = f"fractal{idx}_"
        parsed = parsed_items[idx] if idx < len(parsed_items) else None
        price = float(parsed["price"]) if parsed else base_price
        for field in ("direction", "front", "back", "strong", "break", "reverse", "power", "count", "impulse", "fractal_atr", "shift"):
            result[f"{prefix}{field}"] = float(parsed.get(field, 0.0)) if parsed else 0.0
        result[f"{prefix}price_rel_f0"] = price - base_price
        result[f"{prefix}distance_to_planned_limit"] = price - planned_limit
        result[f"{prefix}distance_to_planned_stop"] = price - planned_stop
    return result


def build_rich_feature_frame(entries: pd.DataFrame, ohlc: pd.DataFrame, profile_id: str) -> tuple[pd.DataFrame, list[dict[str, object]]]:
    out = build_entry_feature_frame(entries)
    audit: list[dict[str, object]] = [
        {"feature": col, "source": "planned_execution_geometry", "available_at": "pre_order", "live_safe": True}
        for col in ENTRY_FEATURE_COLUMNS
    ]
    if profile_id in {"time_only", "movement_plus_time", "rich_combined_k40"}:
        times = pd.to_datetime(out["time"])
        out["session_hour"] = times.dt.hour.astype(float)
        out["weekday"] = times.dt.weekday.astype(float)
        out["hour_sin"] = np.sin(2 * np.pi * out["session_hour"] / 24.0)
        out["hour_cos"] = np.cos(2 * np.pi * out["session_hour"] / 24.0)
        out["weekday_sin"] = np.sin(2 * np.pi * out["weekday"] / 7.0)
        out["weekday_cos"] = np.cos(2 * np.pi * out["weekday"] / 7.0)
    if profile_id in {"price_action_h1", "rich_combined_k40"}:
        out, ohlc_audit = _attach_closed_h1_features(out, ohlc)
        audit.extend(ohlc_audit)
    if profile_id in {"structure_f0_only", "structure_nearest_k20", "structure_nearest_k40", "relative_geometry_k40", "rich_combined_k40", "structure_nearest_k80", "structure_all100"}:
        k = 1 if profile_id == "structure_f0_only" else 40
        basis = "recent" if profile_id in {"structure_f0_only", "structure_all100"} else "nearest_to_planned_limit"
        fractal_features = pd.DataFrame([extract_fractal_feature_dict(row, k, selection_basis=basis) for _, row in entries.iterrows()], index=out.index)
        out = pd.concat([out, fractal_features], axis=1)
        if profile_id == "structure_f0_only":
            parsed_f0 = [parse_serialized_fractal(value) for value in entries.get("fractal0", pd.Series(index=entries.index, dtype=object))]
            for field in ("price", "up_3", "dn_3", "up_6", "dn_6", "up_12", "dn_12", "up_24", "dn_24", "up_48", "dn_48"):
                out[f"fractal0_{field}"] = [float(item.get(field, 0.0)) if item else 0.0 for item in parsed_f0]
    if profile_id == "movement_plus_time" and ("movement_score" not in out or pd.to_numeric(out["movement_score"], errors="coerce").isna().any()):
        raise ValueError("movement_plus_time requires movement_score provenance; do not fill with zero")
    feature_columns = rich_feature_allowlist(profile_id)
    missing = [col for col in feature_columns if col not in out.columns]
    if missing:
        raise ValueError(f"missing feature columns for {profile_id}: {missing[:10]}")
    _assert_no_forbidden_feature_columns(feature_columns)
    return out[feature_columns].copy(), audit


def train_entry_models(
    train_rows: pd.DataFrame,
    threads: int,
    seeds: tuple[int, ...] = (42, 43, 44),
    n_estimators: int = 200,
) -> dict[str, object]:
    frame = build_entry_feature_frame(train_rows)
    x = frame[ENTRY_FEATURE_COLUMNS].fillna(0.0)
    models: dict[str, object] = {}
    targets = {"entry_quality_score": "target_entry_good", "entry_avoid_sl_score": "target_entry_avoid_sl"}
    for score_col, target_col in targets.items():
        y = frame[target_col].astype(int)
        if y.nunique() < 2:
            models[score_col] = [float(y.iloc[0]) if len(y) else 0.0]
            continue
        fitted = []
        for seed in seeds:
            clf = ExtraTreesClassifier(n_estimators=n_estimators, max_depth=8, min_samples_leaf=50, random_state=seed, n_jobs=threads)
            clf.fit(x, y)
            fitted.append(clf)
        models[score_col] = fitted
    return models


def score_entry_models(models: dict[str, object], rows: pd.DataFrame) -> pd.DataFrame:
    out = build_entry_feature_frame(rows)
    x = out[ENTRY_FEATURE_COLUMNS].fillna(0.0)
    for score_col, fitted in models.items():
        values = []
        for model in fitted:
            values.append(np.full(len(out), model) if isinstance(model, float) else model.predict_proba(x)[:, 1])
        out[score_col] = np.median(np.vstack(values), axis=0) if values else 0.0
    return out


def train_rich_entry_model(
    x_train: pd.DataFrame,
    y_train: pd.Series,
    target_kind: str,
    model_id: str,
    threads: int,
    seed: int,
) -> object:
    x = x_train.fillna(0.0)
    y = y_train.dropna()
    x = x.loc[y.index]
    if target_kind == "classification":
        y = y.astype(int)
        if y.nunique() < 2:
            return float(y.iloc[0]) if len(y) else 0.0
        if model_id == "linear":
            model = LogisticRegression(max_iter=500, random_state=seed)
        elif model_id == "hist_gradient_boosting":
            model = HistGradientBoostingClassifier(max_iter=100, max_leaf_nodes=15, min_samples_leaf=2, random_state=seed)
        elif model_id == "extra_trees_shallow":
            model = ExtraTreesClassifier(n_estimators=160, max_depth=6, min_samples_leaf=1, random_state=seed, n_jobs=threads)
        elif model_id == "extra_trees_current":
            model = ExtraTreesClassifier(n_estimators=200, max_depth=8, min_samples_leaf=1, random_state=seed, n_jobs=threads)
        elif model_id == "random_forest_shallow":
            model = RandomForestClassifier(n_estimators=120, max_depth=6, min_samples_leaf=1, random_state=seed, n_jobs=threads)
        else:
            raise ValueError(f"unsupported rich classification model_id: {model_id}")
    else:
        if model_id == "linear":
            model = Ridge(alpha=1.0, random_state=seed)
        elif model_id == "hist_gradient_boosting":
            model = HistGradientBoostingRegressor(max_iter=100, max_leaf_nodes=15, min_samples_leaf=2, random_state=seed)
        elif model_id == "extra_trees_shallow":
            model = ExtraTreesRegressor(n_estimators=160, max_depth=6, min_samples_leaf=1, random_state=seed, n_jobs=threads)
        elif model_id == "extra_trees_current":
            model = ExtraTreesRegressor(n_estimators=200, max_depth=8, min_samples_leaf=1, random_state=seed, n_jobs=threads)
        elif model_id == "random_forest_shallow":
            model = RandomForestRegressor(n_estimators=120, max_depth=6, min_samples_leaf=1, random_state=seed, n_jobs=threads)
        else:
            raise ValueError(f"unsupported rich regression model_id: {model_id}")
    model.fit(x, y)
    return model


def score_rich_entry_model(model: object, x_rows: pd.DataFrame, target_kind: str) -> np.ndarray:
    if isinstance(model, float):
        return np.full(len(x_rows), model, dtype=float)
    x = x_rows.fillna(0.0)
    if target_kind == "classification":
        return np.asarray(model.predict_proba(x)[:, 1], dtype=float)
    return np.asarray(model.predict(x), dtype=float)


def prepare_rich_training_target(
    entries: pd.DataFrame,
    x_train: pd.DataFrame,
    labels: pd.DataFrame,
    target_id: str,
) -> tuple[pd.DataFrame, pd.Series]:
    keyed_x = x_train.copy()
    keyed_x.index = entries["position_id"].astype(str).to_numpy()
    keyed_labels = labels.set_index(labels["position_id"].astype(str))
    y = pd.to_numeric(keyed_labels[target_id], errors="coerce").dropna()
    common = keyed_x.index.intersection(y.index)
    return keyed_x.loc[common], y.loc[common]


def apply_entry_filter(
    entries: pd.DataFrame,
    filter_rule: dict[str, object],
    mode: str = "select",
    score_cutoff: float | None = None,
) -> pd.DataFrame:
    if filter_rule["family"] == "none":
        out = entries.copy()
        out["entry_filter_selected"] = True
        out["entry_filter_score_cutoff"] = None
        out.attrs["score_cutoff_on_val_select"] = None
        return out
    score_col = str(filter_rule["score_col"])
    if mode == "select":
        cutoff = score_cutoff_for_top_fraction(entries, score_col, float(filter_rule["top_fraction"]))
    elif mode == "eval":
        if score_cutoff is None:
            raise ValueError("score_cutoff is required when applying filter in eval mode")
        cutoff = float(score_cutoff)
    else:
        raise ValueError(f"unknown filter mode: {mode}")
    out = entries.loc[pd.to_numeric(entries[score_col], errors="coerce") >= cutoff].copy()
    out["entry_filter_selected"] = True
    out["entry_filter_score_cutoff"] = cutoff
    out.attrs["score_cutoff_on_val_select"] = cutoff
    return out


def load_stop_grid_choice(path: str | Path, explicit_stop_policy_id: str | None) -> dict[str, object]:
    artifact_path = _path(path)
    if not artifact_path.exists():
        raise SystemExit(f"entry-quality full run requires completed stop-grid artifact: {artifact_path}")
    data = json.loads(artifact_path.read_text(encoding="utf-8"))
    if data.get("locked_test") != "not_opened":
        raise SystemExit("locked_test must remain not_opened")
    summary_path = artifact_path.with_name(artifact_path.stem + "_summary.csv")
    completed = int(data.get("progress", {}).get("completed", 0))
    if completed == 0 and summary_path.exists():
        completed = int(sum(1 for _ in summary_path.open("r", encoding="utf-8", errors="ignore")) - 1)
    expected = int(data.get("current_search_budget", {}).get("expected_completed_without_stress", 0))
    if expected and completed < expected:
        raise SystemExit("entry-quality full run requires completed stop-grid")
    winner = data.get("selected_winner", {})
    stop_policy_id = explicit_stop_policy_id or winner.get("stop_policy_id")
    if not stop_policy_id:
        raise SystemExit("entry-quality full run requires explicit stop_policy_id")
    stop_policy = next((item for item in base.stop_policy_grid() if item["stop_policy_id"] == stop_policy_id), None)
    if stop_policy is None:
        raise SystemExit(f"unknown stop_policy_id: {stop_policy_id}")
    exit_id = str(winner.get("exit_id") or "X0_fixed_r_0_7")
    exit_rule = next((item for item in base.exit_grid(shortlist="stop_grid") if item["exit_id"] == exit_id), None)
    if exit_rule is None:
        raise SystemExit(f"stop-grid winner exit_id is unavailable: {exit_id}")
    return {"artifact": data, "stop_policy": stop_policy, "exit_rule": exit_rule, "stop_policy_source": "fractal0_stop_grid_m5_selected_or_explicit"}


def attach_movement_scores(entries: pd.DataFrame, scores: pd.DataFrame, split: str) -> pd.DataFrame:
    split_name = "train" if split == "train_core" else split
    movement = scores.loc[scores["split"].astype(str).eq(split_name), ["split_row_id", "score"]].rename(columns={"score": "movement_score"})
    out = entries.drop(columns=["movement_score"], errors="ignore").merge(movement, on="split_row_id", how="left")
    out["movement_score_available"] = out["movement_score"].notna()
    return out


def _entry_rule() -> dict[str, object]:
    return next(item for item in base.entry_grid() if item["entry_id"] == ENTRY_ID)


def _simulate_for_filter(entries: pd.DataFrame, ohlc: pd.DataFrame, run: dict[str, object], scored_decisions: pd.DataFrame, execution_ohlc: pd.DataFrame | None) -> pd.DataFrame:
    trades = base._simulate_entries(entries, ohlc, run, base.CONFIG.canonical_spread, scored_decisions, execution_ohlc)
    if trades.empty:
        return trades
    trades["filter_id"] = run["filter_id"]
    trades["score_cutoff_on_val_select"] = run.get("score_cutoff_on_val_select")
    trades["entry_filter_score_col"] = run.get("entry_filter_score_col")
    trades["spread"] = base.CONFIG.canonical_spread
    return trades


def _summary_for_filter(trades: pd.DataFrame, run: dict[str, object], split: str) -> dict[str, object]:
    if trades.empty and "pnl_r" not in trades.columns:
        trades = pd.DataFrame(
            columns=[
                "pnl_r",
                "close_reason",
                "ambiguous",
                "risk_distance_atr",
                "tp_distance_atr",
                "exit_time",
            ]
        )
    summary = base._summary_from_trades(trades, run, split, base.CONFIG.canonical_spread)
    summary["filter_id"] = run["filter_id"]
    summary["filter_family"] = run["filter_family"]
    summary["top_fraction"] = run["top_fraction"]
    summary["score_cutoff_on_val_select"] = run.get("score_cutoff_on_val_select")
    summary["entry_filter_score_col"] = run.get("entry_filter_score_col")
    summary["selected_fraction"] = float(len(trades) / max(1, int(run.get("available_trades_before_filter", 0))))
    summary["sl_rate"] = float(trades["close_reason"].astype(str).eq("SL").mean()) if len(trades) else 0.0
    return summary


def score_distribution_diagnostics(scores: pd.DataFrame) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    score_cols = [col for col in [*SCORE_DIAGNOSTIC_COLUMNS, "rich_entry_score"] if col in scores.columns]
    group_cols = [col for col in ("split", "profile_id", "model_id", "target_id", "filter_id") if col in scores.columns]
    grouped = scores.groupby(group_cols, dropna=False) if group_cols else [((), scores)]
    for keys, group in grouped:
        key_values = keys if isinstance(keys, tuple) else (keys,)
        base_row = dict(zip(group_cols, key_values))
        for score_col in score_cols:
            if score_col not in group.columns:
                continue
            series = pd.to_numeric(group[score_col], errors="coerce")
            valid = series.dropna()
            row: dict[str, object] = {
                **base_row,
                "score_col": score_col,
                "rows": int(len(series)),
                "valid_rows": int(len(valid)),
                "nan_rate": float(series.isna().mean()) if len(series) else 0.0,
                "zero_rate": float(series.fillna(0.0).eq(0.0).mean()) if len(series) else 0.0,
            }
            for q in (0.10, 0.30, 0.50, 0.70, 0.90):
                row[f"p{int(q * 100):02d}"] = float(valid.quantile(q)) if len(valid) else None
            rows.append(row)
    return rows


def previous_s0_x0_baseline(stop_grid_artifact: dict[str, object]) -> dict[str, object] | None:
    artifacts = stop_grid_artifact.get("artifacts", {}) if isinstance(stop_grid_artifact.get("artifacts"), dict) else {}
    summary_path = artifacts.get("summary_csv") or "ML/reports/fractal0_stop_grid_m5_summary.csv"
    path = _path(str(summary_path))
    if not path.exists():
        return None
    summary = pd.read_csv(path, sep=";", usecols=["stop_policy_id", "entry_id", "mask_id", "exit_id", "split", "n_trades", "pf", "bs_p05", "mean_pnl_r", "max_drawdown_r"])
    row = summary.loc[
        summary["stop_policy_id"].eq("S0_current_0_5")
        & summary["entry_id"].eq(ENTRY_ID)
        & summary["mask_id"].eq(MASK_ID)
        & summary["exit_id"].eq("X0_fixed_r_0_7")
        & summary["split"].eq("val_eval")
    ]
    return row.iloc[0].to_dict() if not row.empty else None


def previous_s2_x2_no_mask_baseline(stop_grid_artifact: dict[str, object]) -> dict[str, object] | None:
    artifacts = stop_grid_artifact.get("artifacts", {}) if isinstance(stop_grid_artifact.get("artifacts"), dict) else {}
    summary_path = artifacts.get("summary_csv") or "ML/reports/fractal0_stop_grid_m5_summary.csv"
    path = _path(str(summary_path))
    if not path.exists():
        return None
    wanted = ["stop_policy_id", "entry_id", "mask_id", "exit_id", "split", "n_trades", "pf", "bs_p05", "mean_pnl_r", "max_drawdown_r", "negative_years", "pf_without_best_year", "effective_profit_years", "n_years"]
    summary = pd.read_csv(path, sep=";", usecols=lambda col: col in wanted)
    row = summary.loc[
        summary["stop_policy_id"].eq("S2_fractal0_buffer_0_5_entry_floor_2")
        & summary["entry_id"].eq(ENTRY_ID)
        & summary["mask_id"].eq(MASK_ID)
        & summary["exit_id"].eq("X2_ml_opposite_any_p0_50")
        & summary["split"].eq("val_eval")
    ]
    return row.iloc[0].to_dict() if not row.empty else None


def select_entry_filter_winner(summary: pd.DataFrame) -> dict[str, object]:
    val_select = summary.loc[summary["split"].eq("val_select")].copy()
    primary = val_select.loc[val_select["filter_id"].astype(str).str.startswith("entry_quality_")].copy()
    candidates = primary if not primary.empty else val_select
    gated = candidates[(candidates["n_trades"] >= 100) & (candidates["mean_pnl_r"] > 0)].copy()
    if gated.empty:
        gated = candidates.copy()
    gated = gated.sort_values(["bs_p05", "pf", "n_trades"], ascending=[False, False, False])
    winner = gated.iloc[0].to_dict()
    winner["selection_metric"] = "val_select BS_p05 within primary entry_quality family"
    return winner


def select_rich_winner(summary: pd.DataFrame) -> dict[str, object]:
    candidates = summary.loc[
        summary["split"].eq("val_select")
        & summary["eligible_for_winner"].astype(bool)
        & (pd.to_numeric(summary["n_trades"], errors="coerce") >= 300)
    ].copy()
    if candidates.empty:
        return {"status": "no_eligible_winner"}
    candidates["_bs"] = pd.to_numeric(candidates["bs_p05"], errors="coerce").fillna(-np.inf)
    candidates["_dd"] = pd.to_numeric(candidates["max_drawdown_r"], errors="coerce").fillna(np.inf)
    candidates = candidates.sort_values(["_bs", "_dd", "profile_id", "model_id"], ascending=[False, True, True, True])
    return candidates.drop(columns=["_bs", "_dd"]).iloc[0].to_dict()


def evaluate_rich_verdict(
    selected_val_eval: dict[str, object],
    controls: dict[str, object],
    diagnostic_best_val_eval: dict[str, object] | None = None,
) -> str:
    _ = diagnostic_best_val_eval
    if selected_val_eval.get("status") == "no_eligible_winner":
        return "REJECT_RICH_ENTRY_QUALITY"
    if int(selected_val_eval.get("n_trades") or 0) < 300:
        return "REJECT_RICH_ENTRY_QUALITY"
    selected_bs = float(selected_val_eval.get("bs_p05") or 0.0)
    baseline_values = [float(value.get("bs_p05") or 0.0) for value in controls.values() if isinstance(value, dict)]
    baseline_bs = max(baseline_values) if baseline_values else 0.0
    if selected_bs <= baseline_bs:
        return "REJECT_RICH_ENTRY_QUALITY"
    return RICH_ALLOWED_MAX_VERDICT


def evaluate_winner_on_val_eval(winner: dict[str, object], summary: pd.DataFrame) -> dict[str, object]:
    rows = summary.loc[(summary["split"].eq("val_eval")) & (summary["filter_id"].eq(winner["filter_id"]))]
    return rows.iloc[0].to_dict() if not rows.empty else {}


def run_selection_permutation(summary: pd.DataFrame, trades: pd.DataFrame, repeats: int, seed: int) -> dict[str, object]:
    observed = float(select_entry_filter_winner(summary).get("bs_p05") or 0.0)
    val_select = trades.loc[trades["split"].eq("val_select")].reset_index(drop=True)
    if val_select.empty or repeats <= 0:
        return {"method": "block_shuffled_val_select_pnl_r", "null_repeats": int(repeats), "observed_winner_bs_p05": observed, "empirical_p_value": None, "status": "SKIPPED"}
    rng = np.random.default_rng(seed)
    pnl = pd.to_numeric(val_select["pnl_r"], errors="coerce").fillna(0.0).to_numpy()
    null = []
    for _ in range(repeats):
        shuffled = val_select.copy()
        shuffled["pnl_r"] = rng.permutation(pnl)
        rows = []
        for filter_id, group in shuffled.groupby("filter_id", sort=False):
            run = {"stop_policy_id": group["stop_policy_id"].iloc[0], "entry_id": ENTRY_ID, "mask_id": MASK_ID, "exit_id": group["exit_id"].iloc[0], "filter_id": filter_id}
            row = base._summary_from_trades(group, run, "val_select", base.CONFIG.canonical_spread, n_bootstrap=50)
            row["filter_id"] = filter_id
            rows.append(row)
        null.append(float(select_entry_filter_winner(pd.DataFrame(rows)).get("bs_p05") or 0.0))
    p_value = (1 + sum(value >= observed for value in null)) / (1 + len(null))
    return {"method": "block_shuffled_val_select_pnl_r", "null_repeats": int(repeats), "observed_winner_bs_p05": observed, "empirical_p_value": float(p_value), "status": "PASS" if p_value <= 0.10 else "RESEARCH_HINT", "null_best_bs_p05": null}


def empty_rich_artifact(search_budget: dict[str, object], feature_contract: list[dict[str, object]]) -> dict[str, object]:
    return {
        "status": "initialized",
        "experiment": "fractal0_rich_entry_quality",
        "verdict": "research_only",
        "lifecycle_status": "research_hint",
        "allowed_max_verdict": RICH_ALLOWED_MAX_VERDICT,
        "locked_test": "not_opened",
        "selection_policy": {
            "train_core": "trains ML-exit and ML-entry",
            "val_select": "selects exactly one eligible rule",
            "val_eval": "fixed selected_rule only",
            "diagnostic_grid": "not eligible for winner",
        },
        "forbidden_interpretations": ["candidate", "tradable", "live_ready", "production", "permission_to_open_locked_test"],
        "current_search_budget": search_budget,
        "feature_contract": feature_contract,
    }


def target_distribution_audit(labels: pd.DataFrame, target_contract: dict[str, str]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    work = labels.copy()
    work["year"] = pd.to_datetime(work["time"], errors="coerce").dt.year if "time" in work else pd.NA
    for target_id, target_kind in target_contract.items():
        if target_id not in work:
            continue
        for keys, group in work.groupby(["split", "side", "year"], dropna=False):
            values_all = pd.to_numeric(group[target_id], errors="coerce")
            values = values_all.dropna()
            row: dict[str, object] = {"split": keys[0], "side": keys[1], "year": keys[2], "target_id": target_id, "target_kind": target_kind, "rows": int(len(values))}
            if target_kind == "classification":
                ones = int((values == 1).sum())
                zeros = int((values == 0).sum())
                row.update({"class_0_count": zeros, "class_1_count": ones, "positive_rate": float(ones / len(values)) if len(values) else None, "minority_count": min(zeros, ones)})
            else:
                row.update(
                    {
                        "mean": float(values.mean()) if len(values) else None,
                        "median": float(values.median()) if len(values) else None,
                        "p05": float(values.quantile(0.05)) if len(values) else None,
                        "p50": float(values.quantile(0.50)) if len(values) else None,
                        "p95": float(values.quantile(0.95)) if len(values) else None,
                        "std": float(values.std(ddof=0)) if len(values) else None,
                        "nan_rate": float(values_all.isna().mean()) if len(values_all) else 0.0,
                    }
                )
            rows.append(row)
    return pd.DataFrame(rows)


def build_split_manifest(entry_cache: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for split, entries in entry_cache.items():
        times = pd.to_datetime(entries["time"], errors="coerce")
        filled = entries.get("filled", pd.Series(False, index=entries.index)).fillna(False).astype(bool)
        rows.append(
            {
                "split": split,
                "min_time": times.min(),
                "max_time": times.max(),
                "raw_rows": int(len(entries)),
                "planned_orders": int(len(entries)),
                "filled_trades": int(filled.sum()),
                "fill_rate": float(filled.mean()) if len(filled) else 0.0,
            }
        )
    return pd.DataFrame(rows)


def validate_movement_provenance(entries: pd.DataFrame, provenance: dict[str, object]) -> dict[str, object]:
    required = [
        "movement_artifact_path",
        "movement_artifact_sha256",
        "movement_rule_id",
        "movement_train_period",
        "movement_locked_before_rich_entry_quality",
    ]
    missing = [key for key in required if not provenance.get(key)]
    scores = pd.to_numeric(entries.get("movement_score"), errors="coerce") if "movement_score" in entries else pd.Series(dtype=float)
    if missing or scores.isna().any():
        raise ValueError("movement_score provenance is incomplete or scores contain missing values")
    return {**provenance, "status": "PASS"}


def forbidden_column_audit(profile_ids: list[str]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for profile_id in profile_ids:
        for feature in rich_feature_allowlist(profile_id):
            forbidden = (
                feature in FORBIDDEN_FEATURE_EXACT
                or feature.startswith(FORBIDDEN_FEATURE_PREFIXES)
                or "_pnl_" in feature
            )
            rows.append({"profile_id": profile_id, "feature": feature, "forbidden": bool(forbidden)})
    return pd.DataFrame(rows)


def structural_feature_gate(profile_id: str, features: pd.DataFrame) -> dict[str, object]:
    numeric = features.apply(pd.to_numeric, errors="coerce")
    unique_counts = numeric.nunique(dropna=True)
    constant_names = [str(name) for name, count in unique_counts.items() if count <= 1]
    constant = int((unique_counts <= 1).sum())
    total = int(len(unique_counts))
    non_constant_fraction = float((total - constant) / total) if total else 0.0
    status = "PASS"
    required: dict[str, bool] = {}
    informational_constant_fields: list[str] = []
    if profile_id == "structure_f0_only":
        required = {
            "fractal0_price": float(numeric["fractal0_price"].std(ddof=0)) > 0 if "fractal0_price" in numeric else False,
            "fractal0_direction": int(numeric["fractal0_direction"].nunique(dropna=True)) >= 2 if "fractal0_direction" in numeric else False,
            "fractal0_shift": numeric["fractal0_shift"].notna().any() if "fractal0_shift" in numeric else False,
        }
        informational_constant_fields = [name for name in constant_names if name.startswith("fractal0_")]
        status = "PASS" if all(required.values()) else "FEATURE_CONTRACT_FAIL"
    elif profile_id.startswith("structure_") or profile_id in {"relative_geometry_k40", "rich_combined_k40"}:
        status = "PASS" if non_constant_fraction >= 0.50 else "FEATURE_CONTRACT_FAIL"
    return {
        "profile_id": profile_id,
        "features": total,
        "constant_features": constant,
        "constant_feature_names": "|".join(constant_names),
        "non_constant_fraction": non_constant_fraction,
        "required_live_fields": "|".join(name for name, passed in required.items() if passed),
        "failed_required_live_fields": "|".join(name for name, passed in required.items() if not passed),
        "informational_constant_fields": "|".join(informational_constant_fields),
        "status": status,
    }


def build_rich_cumulative_search_budget(
    stop_grid_artifact: dict[str, object],
    ranked_search_budget: dict[str, object],
    active_search_budget: dict[str, object],
) -> dict[str, object]:
    narrow_path = _path(DEFAULT_NARROW_ENTRY_QUALITY_ARTIFACT)
    narrow_budget: dict[str, object] | None = None
    if narrow_path.exists():
        try:
            narrow = json.loads(narrow_path.read_text(encoding="utf-8"))
            narrow_budget = {
                "artifact_path": str(narrow_path),
                "status": narrow.get("status"),
                "verdict": narrow.get("verdict"),
                "current_search_budget": narrow.get("current_search_budget"),
                "cumulative_search_budget": narrow.get("cumulative_search_budget"),
            }
        except json.JSONDecodeError:
            narrow_budget = {"artifact_path": str(narrow_path), "status": "UNREADABLE_JSON"}
    return {
        "parent_stop_grid": {
            "artifact_path": str(_path(DEFAULT_STOP_GRID_ARTIFACT)),
            "status": stop_grid_artifact.get("status"),
            "verdict": stop_grid_artifact.get("verdict"),
            "current_search_budget": stop_grid_artifact.get("current_search_budget"),
            "cumulative_search_budget": stop_grid_artifact.get("cumulative_search_budget"),
        },
        "narrow_entry_quality_predecessor": narrow_budget,
        "current_rich_ranked_search_budget": ranked_search_budget,
        "current_rich_active_search_budget": active_search_budget,
        "current_rich_diagnostic_budget": {
            "listed_diagnostic_configs": int(ranked_search_budget.get("n_diagnostic_configs", 0)),
            "executed_by_default_run": False,
        },
    }


def selected_rule_score_diagnostics(scores: pd.DataFrame, selected: dict[str, object], cutoff: float | None) -> pd.DataFrame:
    columns = ["split", "rows", "valid_rows", "score_cutoff_on_val_select", "fraction_above_cutoff", "p10", "p30", "p50", "p70", "p90"]
    if scores.empty:
        return pd.DataFrame(columns=columns)
    required = {"profile_id", "model_id", "target_id", "filter_id", "rich_entry_score"}
    if selected.get("status") == "no_eligible_winner" or not required.issubset(scores.columns):
        return pd.DataFrame(columns=columns)
    mask = (
        scores["profile_id"].eq(selected.get("profile_id"))
        & scores["model_id"].eq(selected.get("model_id"))
        & scores["target_id"].eq(selected.get("target_id"))
        & scores["filter_id"].eq(selected.get("filter_id"))
    )
    rows: list[dict[str, object]] = []
    for split, group in scores.loc[mask].groupby("split", dropna=False):
        values = pd.to_numeric(group["rich_entry_score"], errors="coerce").dropna()
        row: dict[str, object] = {
            "split": split,
            "rows": int(len(group)),
            "valid_rows": int(len(values)),
            "score_cutoff_on_val_select": cutoff,
            "fraction_above_cutoff": float((values >= float(cutoff)).mean()) if cutoff is not None and len(values) else None,
        }
        for q in (0.10, 0.30, 0.50, 0.70, 0.90):
            row[f"p{int(q * 100):02d}"] = float(values.quantile(q)) if len(values) else None
        rows.append(row)
    return pd.DataFrame(rows)


def _rich_filter_rule(filter_spec: dict[str, object]) -> dict[str, object]:
    return {
        "filter_id": filter_spec["filter_id"],
        "family": "rich_score" if filter_spec["filter_id"] != "M0_no_mask" else "none",
        "score_col": "rich_entry_score",
        "top_fraction": filter_spec["top_fraction"],
    }


def feature_distribution_audit(frames: dict[tuple[str, str], pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for (split, profile_id), frame in frames.items():
        for col in frame.columns:
            series = pd.to_numeric(frame[col], errors="coerce")
            valid = series.dropna()
            rows.append(
                {
                    "split": split,
                    "profile_id": profile_id,
                    "feature": col,
                    "rows": int(len(series)),
                    "nan_rate": float(series.isna().mean()) if len(series) else 0.0,
                    "zero_rate": float(series.fillna(0.0).eq(0.0).mean()) if len(series) else 0.0,
                    "mean": float(valid.mean()) if len(valid) else None,
                    "std": float(valid.std(ddof=0)) if len(valid) else None,
                    "p05": float(valid.quantile(0.05)) if len(valid) else None,
                    "p50": float(valid.quantile(0.50)) if len(valid) else None,
                    "p95": float(valid.quantile(0.95)) if len(valid) else None,
                    "unique_count": int(valid.nunique()) if len(valid) else 0,
                }
            )
    return pd.DataFrame(rows)


def rich_feature_contract_rows(profile_ids: list[str]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for profile_id in profile_ids:
        for feature in rich_feature_allowlist(profile_id):
            if feature.startswith("h1_"):
                source = "DATA/XAUUSD_H1_OHLC.csv"
                available_at = "last_fully_closed_h1_bar"
            elif feature.startswith("fractal"):
                source = "serialized_fractal_fields"
                available_at = "pre_order_fractal_snapshot"
            elif feature == "movement_score":
                source = "frozen_movement_score"
                available_at = "pre_order_after_signal_before_limit_order_send"
            elif feature in {"session_hour", "weekday", "hour_sin", "hour_cos", "weekday_sin", "weekday_cos"}:
                source = "entry_time"
                available_at = "pre_order_after_signal_before_limit_order_send"
            else:
                source = "planned_execution_geometry"
                available_at = "pre_order_after_signal_before_limit_order_send"
            rows.append(
                {
                    "profile_id": profile_id,
                    "feature": feature,
                    "source": source,
                    "available_at": available_at,
                    "decision_time": "pre_order_after_signal_before_limit_order_send",
                    "live_safe": True,
                }
            )
    return rows


def run_entry_quality(args: argparse.Namespace) -> dict[str, object]:
    started = time.time()
    print("start fractal0_entry_quality_filter", flush=True)
    choice = load_stop_grid_choice(args.stop_grid_artifact, args.stop_policy_id)
    config = dataclasses.replace(base.CONFIG, output_prefix=args.output_prefix, execution_ohlc_path=args.execution_ohlc_path)
    preflight = base.preflight_inputs(config)
    preflight["stop_grid_artifact"] = {"path": str(_path(args.stop_grid_artifact)), "sha256": base.sha256_file(_path(args.stop_grid_artifact))}
    preflight["input_artifact_hashes"]["stop_grid_artifact"] = preflight["stop_grid_artifact"]["sha256"]
    print(f"preflight {preflight['status']}", flush=True)
    if preflight["status"] != "PASS":
        raise SystemExit(f"preflight failed: {preflight['errors']}")

    ohlc = base.load_ohlc(config)
    execution_ohlc = base.prepare_execution_ohlc_index(base.load_ohlc_path(config.execution_ohlc_path)) if config.execution_ohlc_path else None
    splits = base.load_role_splits(config)
    if args.smoke_limit_filters:
        splits = {name: frame.head(700).copy().reset_index(drop=True) for name, frame in splits.items()}
        for name, frame in splits.items():
            frame["split"] = name
            frame["split_row_id"] = np.arange(len(frame), dtype=int)
    frozen_scores = base._read_frozen_scores(config)

    stop_policy = choice["stop_policy"]
    exit_rule = choice["exit_rule"]
    run_base = {**stop_policy, **_entry_rule(), **{"mask_id": MASK_ID, "kind": "none"}, **exit_rule, "spread": base.CONFIG.canonical_spread}
    entry_cache = {}
    for split, rows in splits.items():
        entries = base.build_entry_rows(rows, ohlc, _entry_rule(), base.CONFIG.canonical_spread, stop_policy)
        entries = attach_movement_scores(entries, frozen_scores, split)
        entry_cache[split] = entries
        print(f"prepared entries split={split} rows={len(entries)} filled={int(entries['filled'].sum()) if len(entries) else 0}", flush=True)

    train_trade_labels = base._simulate_entries(entry_cache["train_core"], ohlc, run_base, base.CONFIG.canonical_spread, pd.DataFrame(), execution_ohlc)
    labelled = build_entry_labels(train_trade_labels)
    train_rows = entry_cache["train_core"].merge(labelled[["position_id", "target_entry_good", "target_entry_avoid_sl"]], on="position_id", how="inner")
    models = train_entry_models(train_rows, int(args.threads), seeds=(42,) if args.smoke_limit_filters else (42, 43, 44), n_estimators=25 if args.smoke_limit_filters else 200)

    scored_entries = {split: score_entry_models(models, rows) for split, rows in entry_cache.items()}
    scored_entries = {split: build_entry_feature_frame(rows) for split, rows in scored_entries.items()}

    exit_cache = {("train_core", str(stop_policy["stop_policy_id"]), ENTRY_ID, MASK_ID): entry_cache["train_core"]}
    ml_models, target_rates = base._train_ml_exit_layer(exit_cache, ohlc, int(args.threads), seeds=(42,) if args.smoke_limit_filters else base.EXIT_MODEL_SEEDS, n_estimators=25 if args.smoke_limit_filters else 200)
    scored_decisions = {}
    for split in ("val_select", "val_eval"):
        decisions = base.build_exit_decision_rows(scored_entries[split].loc[scored_entries[split]["filled"].astype(bool)], ohlc)
        scored_decisions[split] = base.score_exit_models({MASK_ID: ml_models[str(stop_policy["stop_policy_id"])][MASK_ID]}, decisions)

    filters = entry_filter_grid()[: args.smoke_limit_filters] if args.smoke_limit_filters else entry_filter_grid()
    summary_rows: list[dict[str, object]] = []
    trade_frames: list[pd.DataFrame] = []
    score_rows: list[pd.DataFrame] = []
    cutoffs: dict[str, float | None] = {}
    for split in ("val_select", "val_eval"):
        score_rows.append(scored_entries[split].assign(split=split))
    for filter_rule in filters:
        selected_by_split: dict[str, pd.DataFrame] = {}
        selected = apply_entry_filter(scored_entries["val_select"], filter_rule, mode="select")
        cutoffs[str(filter_rule["filter_id"])] = selected.attrs.get("score_cutoff_on_val_select")
        selected_by_split["val_select"] = selected
        selected_by_split["val_eval"] = apply_entry_filter(scored_entries["val_eval"], filter_rule, mode="eval", score_cutoff=cutoffs[str(filter_rule["filter_id"])]) if filter_rule["family"] != "none" else apply_entry_filter(scored_entries["val_eval"], filter_rule)
        for split, selected_entries in selected_by_split.items():
            run = {
                **run_base,
                "split": split,
                "filter_id": filter_rule["filter_id"],
                "filter_family": filter_rule["family"],
                "top_fraction": filter_rule["top_fraction"],
                "score_cutoff_on_val_select": cutoffs[str(filter_rule["filter_id"])],
                "entry_filter_score_col": filter_rule["score_col"],
                "available_trades_before_filter": int(scored_entries[split]["filled"].sum()) if "filled" in scored_entries[split] else len(scored_entries[split]),
            }
            trades = _simulate_for_filter(selected_entries, ohlc, run, scored_decisions[split], execution_ohlc)
            if not trades.empty:
                trade_frames.append(trades)
            summary_rows.append(_summary_for_filter(trades, run, split))
        print(f"filter done {filter_rule['filter_id']} elapsed={time.time() - started:.1f}", flush=True)

    summary = pd.DataFrame(summary_rows)
    non_empty_trade_frames = [frame.dropna(axis=1, how="all") for frame in trade_frames if not frame.empty]
    trades = pd.concat(non_empty_trade_frames, ignore_index=True) if non_empty_trade_frames else pd.DataFrame()
    for column in ("tp_distance_atr",):
        if column not in trades.columns:
            trades[column] = np.nan
    scores = pd.concat(score_rows, ignore_index=True) if score_rows else pd.DataFrame()
    winner = select_entry_filter_winner(summary)
    val_eval = evaluate_winner_on_val_eval(winner, summary)
    winner_trades = trades.loc[(trades["split"].eq("val_eval")) & (trades["filter_id"].eq(winner["filter_id"]))].copy() if not trades.empty else pd.DataFrame()
    yearly = pd.DataFrame([{**{"filter_id": winner["filter_id"], "split": "val_eval"}, **row} for row in base.yearly_metrics(winner_trades)])
    permutation = run_selection_permutation(summary, trades, int(args.permutation_repeats), base.CONFIG.permutation_seed)
    score_diagnostics = score_distribution_diagnostics(scores)
    previous_baseline = previous_s0_x0_baseline(choice["artifact"])

    prefix = _path(args.output_prefix)
    prefix.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(prefix.with_name(prefix.name + "_summary.csv"), sep=";", index=False)
    trades.to_csv(prefix.with_name(prefix.name + "_trades.csv"), sep=";", index=False)
    scores.to_csv(prefix.with_name(prefix.name + "_scores.csv"), sep=";", index=False)
    yearly.to_csv(prefix.with_name(prefix.name + "_yearly.csv"), sep=";", index=False)
    pd.DataFrame(score_diagnostics).to_csv(prefix.with_name(prefix.name + "_score_diagnostics.csv"), sep=";", index=False)
    pd.DataFrame(permutation.get("null_best_bs_p05", []), columns=["null_best_bs_p05"]).to_csv(prefix.with_name(prefix.name + "_permutation.csv"), sep=";", index=False)
    artifact = {
        "status": "completed",
        "experiment": "fractal0_entry_quality_filter",
        "verdict": "research_only",
        "lifecycle_status": "research_hint" if float(val_eval.get("bs_p05") or 0.0) < float(summary.loc[(summary["split"].eq("val_eval")) & (summary["filter_id"].eq("M0_no_mask")), "bs_p05"].iloc[0]) else "research_hypothesis",
        "allowed_max_verdict": "research_only",
        "locked_test": "not_opened",
        "stop_policy_id": stop_policy["stop_policy_id"],
        "stop_policy_source": choice["stop_policy_source"],
        "exit_policy_id_used_for_entry_labels": exit_rule["exit_id"],
        "entry_id": ENTRY_ID,
        "selected_winner": winner,
        "val_select_winner_metrics": winner,
        "val_eval_winner_metrics": val_eval,
        "filter_id": winner.get("filter_id"),
        "score_cutoff_on_val_select": winner.get("score_cutoff_on_val_select"),
        "actual_val_eval_selected_fraction": val_eval.get("selected_fraction"),
        "actual_val_eval_selected_trades": val_eval.get("n_trades"),
        "split_roles": {
            "train_core": "trains ML-exit and ML-entry",
            "val_select": "chooses filter family and score_cutoff_on_val_select",
            "val_eval": "evaluates fixed filter and fixed cutoff without reselection",
            "locked_test": "not_opened",
        },
        "forbidden_interpretations": ["candidate", "tradable", "live_ready", "production", "permission_to_open_locked_test"],
        "entry_feature_columns": ENTRY_FEATURE_COLUMNS,
        "entry_feature_contract": {
            "decision_time": "pre_order_after_signal_before_limit_order_send",
            "price_basis": "planned limit/stop/R fields, not post-fill outcome fields",
            "forbidden_columns": ["pnl_r", "close_reason", "hold_bars", "exit_time", "future_*", "target_*", "target_exit_*", "target_entry_*"],
        },
        "entry_label_contract": {
            "target_entry_good": "1 if pnl_r > 0 else 0, built from train_core simulated trades only",
            "target_entry_avoid_sl": "1 if close_reason != 'SL' else 0, built from train_core simulated trades only",
        },
        "filter_contract": {
            "val_select": "top fraction chooses score_cutoff_on_val_select using finite score rows only",
            "val_eval": "applies score >= score_cutoff_on_val_select; does not recalculate top fraction on val_eval",
            "simple_baselines": "simple top fractions are computed on finite planned geometry scores",
        },
        "input_artifact_hashes": preflight["input_artifact_hashes"],
        "current_search_budget": {"filters": len(filters), "splits": 2, "completed": int(len(summary)), "permutation_repeats": int(args.permutation_repeats)},
        "cumulative_search_budget": {"parent_stop_grid": choice["artifact"].get("cumulative_search_budget"), "entry_quality_filters": len(filters)},
        "target_rates": {"train_core": {col: float(train_rows[col].mean()) for col in ("target_entry_good", "target_entry_avoid_sl") if col in train_rows}},
        "permutation": permutation,
        "score_distribution_diagnostics": score_diagnostics,
        "comparison_controls": {
            "s2_e3_m0_x2_no_mask": summary.loc[(summary["split"].eq("val_eval")) & (summary["filter_id"].eq("M0_no_mask"))].iloc[0].to_dict(),
            "previous_s0_e3_m0_x0_baseline": previous_baseline,
        },
        "preflight": preflight,
        "artifacts": {
            "summary_csv": str(prefix.with_name(prefix.name + "_summary.csv")),
            "trades_csv": str(prefix.with_name(prefix.name + "_trades.csv")),
            "scores_csv": str(prefix.with_name(prefix.name + "_scores.csv")),
            "yearly_csv": str(prefix.with_name(prefix.name + "_yearly.csv")),
            "score_diagnostics_csv": str(prefix.with_name(prefix.name + "_score_diagnostics.csv")),
            "permutation_csv": str(prefix.with_name(prefix.name + "_permutation.csv")),
        },
    }
    prefix.with_suffix(".json").write_text(json.dumps(artifact, ensure_ascii=True, indent=2, default=str), encoding="utf-8")
    print("finished fractal0_entry_quality_filter", flush=True)
    return artifact


def run_rich_entry_quality(args: argparse.Namespace) -> dict[str, object]:
    started = time.time()
    print("start fractal0_rich_entry_quality", flush=True)
    if args.output_prefix == DEFAULT_OUTPUT_PREFIX:
        args.output_prefix = RICH_OUTPUT_PREFIX
    profiles = rich_feature_profile_grid()
    models = rich_model_grid(include_diagnostic_models=bool(args.include_diagnostic_models))
    targets = rich_target_grid()
    filters = rich_filter_grid()
    ranked_search_budget = compute_search_budget(profiles, models, targets, filters)
    prefix = _path(args.output_prefix)
    prefix.parent.mkdir(parents=True, exist_ok=True)

    choice = load_stop_grid_choice(args.stop_grid_artifact, args.stop_policy_id)
    config = dataclasses.replace(base.CONFIG, output_prefix=args.output_prefix, execution_ohlc_path=args.execution_ohlc_path)
    preflight = base.preflight_inputs(config)
    preflight["stop_grid_artifact"] = {"path": str(_path(args.stop_grid_artifact)), "sha256": base.sha256_file(_path(args.stop_grid_artifact))}
    preflight["input_artifact_hashes"]["stop_grid_artifact"] = preflight["stop_grid_artifact"]["sha256"]
    print(f"preflight {preflight['status']}", flush=True)
    if preflight["status"] != "PASS":
        artifact = empty_rich_artifact(ranked_search_budget, [])
        artifact.update({"status": "preflight_failed", "preflight": preflight})
        prefix.with_suffix(".json").write_text(json.dumps(artifact, ensure_ascii=True, indent=2, default=str), encoding="utf-8")
        raise SystemExit(f"preflight failed: {preflight['errors']}")

    ohlc = base.load_ohlc(config)
    execution_ohlc = base.prepare_execution_ohlc_index(base.load_ohlc_path(config.execution_ohlc_path)) if config.execution_ohlc_path else None
    splits = base.load_role_splits(config)
    if args.smoke_limit_filters:
        splits = {name: frame.head(700).copy().reset_index(drop=True) for name, frame in splits.items()}
        for name, frame in splits.items():
            frame["split"] = name
            frame["split_row_id"] = np.arange(len(frame), dtype=int)
    frozen_scores = base._read_frozen_scores(config)

    stop_policy = choice["stop_policy"]
    exit_rule = choice["exit_rule"]
    run_base = {**stop_policy, **_entry_rule(), **{"mask_id": MASK_ID, "kind": "none"}, **exit_rule, "spread": base.CONFIG.canonical_spread}
    entry_cache: dict[str, pd.DataFrame] = {}
    labels_by_split: dict[str, pd.DataFrame] = {}
    planned_diagnostics: list[dict[str, object]] = []
    for split, rows in splits.items():
        entries = base.build_entry_rows(rows, ohlc, _entry_rule(), base.CONFIG.canonical_spread, stop_policy)
        entries = attach_movement_scores(entries, frozen_scores, split)
        entry_cache[split] = entries
        simulated = base._simulate_entries(entries, ohlc, run_base, base.CONFIG.canonical_spread, pd.DataFrame(), execution_ohlc)
        labels = build_rich_entry_labels(entries, simulated)
        labels["split"] = split
        labels["side"] = entries["side"].to_numpy() if "side" in entries else pd.NA
        labels["time"] = entries["time"].to_numpy() if "time" in entries else pd.NaT
        labels_by_split[split] = labels
        planned_diagnostics.append(planned_order_diagnostics(entries, simulated, split))
        print(f"prepared rich entries split={split} rows={len(entries)} filled={int(entries['filled'].sum()) if len(entries) else 0}", flush=True)

    split_manifest = build_split_manifest(entry_cache)
    target_contract = {str(item["target_id"]): str(item["kind"]) for item in targets}
    all_labels = pd.concat(labels_by_split.values(), ignore_index=True)
    target_distribution = target_distribution_audit(all_labels, target_contract)
    movement_provenance = {
        "movement_artifact_path": str(_path(config.movement_freeze_scores)),
        "movement_artifact_sha256": preflight["input_artifact_hashes"].get("movement_freeze_scores"),
        "movement_rule_id": "frozen_scores_movement_score",
        "movement_train_period": "train_core",
        "movement_locked_before_rich_entry_quality": True,
    }

    exit_cache = {("train_core", str(stop_policy["stop_policy_id"]), ENTRY_ID, MASK_ID): entry_cache["train_core"]}
    ml_models, target_rates = base._train_ml_exit_layer(exit_cache, ohlc, int(args.threads), seeds=(42,) if args.smoke_limit_filters else base.EXIT_MODEL_SEEDS, n_estimators=25 if args.smoke_limit_filters else 200)
    scored_decisions = {}
    for split in ("val_select", "val_eval"):
        decisions = base.build_exit_decision_rows(entry_cache[split].loc[entry_cache[split]["filled"].astype(bool)], ohlc)
        scored_decisions[split] = base.score_exit_models({MASK_ID: ml_models[str(stop_policy["stop_policy_id"])][MASK_ID]}, decisions)

    eligible_profiles = [p for p in profiles if p.get("eligible_for_winner")]
    if any(str(profile["profile_id"]) == "movement_plus_time" for profile in eligible_profiles):
        try:
            movement_provenance = validate_movement_provenance(entry_cache["train_core"], movement_provenance)
        except ValueError as exc:
            eligible_profiles = [p for p in eligible_profiles if str(p["profile_id"]) != "movement_plus_time"]
            movement_provenance = {**movement_provenance, "status": "PROFILE_EXCLUDED", "reason": str(exc)}
    runnable_models = [m for m in models if m.get("eligible_for_winner") or (args.include_diagnostic_models and m.get("runnable_by_default"))]
    eligible_targets = [t for t in targets if t.get("eligible_for_winner")]
    primary_filters = [f for f in filters if f.get("eligible_for_winner")]
    active_search_budget = compute_search_budget(eligible_profiles, [m for m in models if m.get("eligible_for_winner")], eligible_targets, primary_filters)
    if args.smoke_limit_filters:
        eligible_profiles = eligible_profiles[:1]
        runnable_models = runnable_models[:1]
        eligible_targets = eligible_targets[:1]
        primary_filters = primary_filters[: int(args.smoke_limit_filters)]
    job_list = [
        (profile, model, target, filter_spec)
        for profile in eligible_profiles
        for model in runnable_models
        for target in eligible_targets
        for filter_spec in primary_filters
        if model.get("runnable_by_default", True)
    ]

    summary_rows: list[dict[str, object]] = []
    trade_frames: list[pd.DataFrame] = []
    score_frames: list[pd.DataFrame] = []
    feature_contract_rows = rich_feature_contract_rows([str(profile["profile_id"]) for profile in eligible_profiles])
    feature_frames_for_audit: dict[tuple[str, str], pd.DataFrame] = {}
    structural_gate_rows: list[dict[str, object]] = []
    total_jobs = len(job_list)
    for done, (profile, model_spec, target_spec, filter_spec) in enumerate(job_list):
        profile_id = str(profile["profile_id"])
        model_id = str(model_spec["model_id"])
        target_id = str(target_spec["target_id"])
        target_kind = str(target_spec["kind"])
        print(f"rich job start {done + 1}/{total_jobs} profile={profile_id} model={model_id} target={target_id}", flush=True)
        x_train, contract = build_rich_feature_frame(entry_cache["train_core"], ohlc, profile_id)
        feature_frames_for_audit.setdefault(("train_core", profile_id), x_train)
        if not any(row["profile_id"] == profile_id for row in structural_gate_rows):
            gate = structural_feature_gate(profile_id, x_train)
            structural_gate_rows.append(gate)
            if gate["status"] == "FEATURE_CONTRACT_FAIL":
                raise SystemExit(f"rich feature contract failed for {profile_id}: {gate}")
        x_fit, y_train = prepare_rich_training_target(entry_cache["train_core"], x_train, labels_by_split["train_core"], target_id)
        rich_model = train_rich_entry_model(x_fit, y_train, target_kind, model_id, int(args.threads), seed=42)
        scored_by_split: dict[str, pd.DataFrame] = {}
        for split in ("val_select", "val_eval"):
            x_split, contract_split = build_rich_feature_frame(entry_cache[split], ohlc, profile_id)
            feature_frames_for_audit.setdefault((split, profile_id), x_split)
            scored = entry_cache[split].copy()
            scored["rich_entry_score"] = score_rich_entry_model(rich_model, x_split, target_kind)
            scored["split"] = split
            scored["profile_id"] = profile_id
            scored["model_id"] = model_id
            scored["target_id"] = target_id
            scored["filter_id"] = filter_spec["filter_id"]
            score_frames.append(scored[["position_id", "split", "profile_id", "model_id", "target_id", "filter_id", "rich_entry_score"]])
            scored_by_split[split] = scored
        selected_val = apply_entry_filter(scored_by_split["val_select"], _rich_filter_rule(filter_spec), mode="select")
        cutoff = selected_val.attrs.get("score_cutoff_on_val_select")
        selected_eval = apply_entry_filter(scored_by_split["val_eval"], _rich_filter_rule(filter_spec), mode="eval", score_cutoff=cutoff)
        for split, selected_entries in {"val_select": selected_val, "val_eval": selected_eval}.items():
            run = {
                **run_base,
                "split": split,
                "filter_id": filter_spec["filter_id"],
                "filter_family": "rich_entry_quality",
                "top_fraction": filter_spec["top_fraction"],
                "score_cutoff_on_val_select": cutoff,
                "entry_filter_score_col": "rich_entry_score",
                "available_trades_before_filter": int(scored_by_split[split]["filled"].sum()) if "filled" in scored_by_split[split] else len(scored_by_split[split]),
            }
            trades = _simulate_for_filter(selected_entries, ohlc, run, scored_decisions[split], execution_ohlc)
            if not trades.empty:
                trades["split"] = split
                trades["profile_id"] = profile_id
                trades["model_id"] = model_id
                trades["target_id"] = target_id
                trade_frames.append(trades)
            row = _summary_for_filter(trades, run, split)
            eligible = bool(profile.get("eligible_for_winner") and model_spec.get("eligible_for_winner") and target_spec.get("eligible_for_winner") and filter_spec.get("eligible_for_winner"))
            row.update(
                {
                    "profile_id": profile_id,
                    "model_id": model_id,
                    "target_id": target_id,
                    "eligible_for_winner": eligible,
                    "not_eligible_for_winner": not eligible,
                    "not_eligible_reason": "" if eligible else "diagnostic_grid",
                }
            )
            summary_rows.append(row)
        print(f"rich job done {done + 1}/{total_jobs} elapsed={time.time() - started:.1f}", flush=True)

    summary = pd.DataFrame(summary_rows)
    trades = pd.concat([frame.dropna(axis=1, how="all") for frame in trade_frames], ignore_index=True) if trade_frames else pd.DataFrame()
    scores = pd.concat(score_frames, ignore_index=True) if score_frames else pd.DataFrame()
    winner = select_rich_winner(summary) if not summary.empty else {"status": "no_eligible_winner"}
    selected_val_eval = summary.loc[
        summary["split"].eq("val_eval")
        & summary["profile_id"].eq(winner.get("profile_id"))
        & summary["model_id"].eq(winner.get("model_id"))
        & summary["target_id"].eq(winner.get("target_id"))
        & summary["filter_id"].eq(winner.get("filter_id"))
    ].iloc[0].to_dict() if winner.get("status") != "no_eligible_winner" else winner
    val_eval_rows = summary.loc[summary["split"].eq("val_eval")].copy()
    diagnostic_best = val_eval_rows.sort_values("bs_p05", ascending=False).iloc[0].to_dict() if not val_eval_rows.empty else {}
    diagnostic_best_is_selected = bool(
        diagnostic_best
        and diagnostic_best.get("profile_id") == selected_val_eval.get("profile_id")
        and diagnostic_best.get("model_id") == selected_val_eval.get("model_id")
        and diagnostic_best.get("target_id") == selected_val_eval.get("target_id")
        and diagnostic_best.get("filter_id") == selected_val_eval.get("filter_id")
    )
    diagnostic_best_not_eligible = bool(diagnostic_best.get("not_eligible_for_winner")) if diagnostic_best else False
    controls = {
        "s2_e3_m0_x2_no_mask": previous_s2_x2_no_mask_baseline(choice["artifact"]),
        "previous_s0_e3_m0_x0_baseline": previous_s0_x0_baseline(choice["artifact"]),
    }
    verdict = evaluate_rich_verdict(selected_val_eval, controls, diagnostic_best)
    winner_trades = trades.loc[
        trades["split"].eq("val_eval")
        & trades["profile_id"].eq(winner.get("profile_id"))
        & trades["model_id"].eq(winner.get("model_id"))
        & trades["target_id"].eq(winner.get("target_id"))
        & trades["filter_id"].eq(winner.get("filter_id"))
    ].copy() if not trades.empty and winner.get("status") != "no_eligible_winner" else pd.DataFrame()
    winner_yearly = pd.DataFrame([{**{"split": "val_eval", "filter_id": winner.get("filter_id")}, **row} for row in base.yearly_metrics(winner_trades)])
    feature_distribution = feature_distribution_audit(feature_frames_for_audit)
    score_diagnostics = score_distribution_diagnostics(scores)
    selected_score_diagnostics = selected_rule_score_diagnostics(scores, selected_val_eval, selected_val_eval.get("score_cutoff_on_val_select"))
    permutation = {"method": "selected_rule_only", "null_repeats": int(args.permutation_repeats), "status": "DIAGNOSTIC_ONLY", "null_best_bs_p05": []}

    pd.DataFrame(feature_contract_rows).drop_duplicates().to_csv(prefix.with_name(prefix.name + "_feature_contract.csv"), sep=";", index=False)
    forbidden_column_audit([str(profile["profile_id"]) for profile in eligible_profiles]).to_csv(prefix.with_name(prefix.name + "_forbidden_column_audit.csv"), sep=";", index=False)
    pd.DataFrame(structural_gate_rows).to_csv(prefix.with_name(prefix.name + "_feature_distribution_flags.csv"), sep=";", index=False)
    target_distribution.to_csv(prefix.with_name(prefix.name + "_target_distribution.csv"), sep=";", index=False)
    pd.DataFrame(planned_diagnostics).to_csv(prefix.with_name(prefix.name + "_planned_order_diagnostics.csv"), sep=";", index=False)
    split_manifest.to_csv(prefix.with_name(prefix.name + "_split_manifest.csv"), sep=";", index=False)
    feature_distribution.to_csv(prefix.with_name(prefix.name + "_feature_distribution_audit.csv"), sep=";", index=False)
    summary.to_csv(prefix.with_name(prefix.name + "_summary.csv"), sep=";", index=False)
    scores.to_csv(prefix.with_name(prefix.name + "_scores.csv"), sep=";", index=False)
    trades.to_csv(prefix.with_name(prefix.name + "_trades.csv"), sep=";", index=False)
    winner_yearly.to_csv(prefix.with_name(prefix.name + "_winner_yearly.csv"), sep=";", index=False)
    pd.DataFrame(score_diagnostics).to_csv(prefix.with_name(prefix.name + "_score_diagnostics.csv"), sep=";", index=False)
    selected_score_diagnostics.to_csv(prefix.with_name(prefix.name + "_selected_score_diagnostics.csv"), sep=";", index=False)
    pd.DataFrame(permutation.get("null_best_bs_p05", []), columns=["null_best_bs_p05"]).to_csv(prefix.with_name(prefix.name + "_permutation.csv"), sep=";", index=False)

    artifact = empty_rich_artifact(ranked_search_budget, pd.DataFrame(feature_contract_rows).drop_duplicates().to_dict(orient="records"))
    artifact.update(
        {
            "status": "completed",
            "verdict": verdict,
            "report_verdict_note": "TIME_ONLY_WINNER",
            "lifecycle_status": "research_hint",
            "ranked_search_budget": ranked_search_budget,
            "active_search_budget": active_search_budget,
            "cumulative_search_budget": build_rich_cumulative_search_budget(choice["artifact"], ranked_search_budget, active_search_budget),
            "diagnostic_budget": {"listed_diagnostic_configs": int(ranked_search_budget["n_diagnostic_configs"])},
            "n_total_executed_configs": len(job_list),
            "selected_winner": winner,
            "selected_winner_val_eval": selected_val_eval,
            "diagnostic_best_val_eval": diagnostic_best,
            "diagnostic_best_val_eval_not_eligible": diagnostic_best_not_eligible,
            "diagnostic_best_val_eval_is_selected_winner": diagnostic_best_is_selected,
            "comparison_controls": controls,
            "split_manifest": split_manifest.to_dict(orient="records"),
            "planned_order_diagnostics": planned_diagnostics,
            "target_distribution": target_distribution.to_dict(orient="records"),
            "movement_provenance": movement_provenance,
            "selection_protocol_replayed_in_permutation": False,
            "permutation_null_repeats_executed_for_full_selection": 0,
            "permutation_scope": "selected_rule_only",
            "permutation_verdict": "diagnostic_only",
            "permutation_gate": "NOT_RUN_FOR_FULL_SELECTION",
            "permutation": permutation,
            "feature_distribution_flags": structural_gate_rows,
            "feature_importance_status": {
                "artifact": "feature_importance_by_profile.csv",
                "status": "NOT_PRODUCED",
                "reason": "Rich runner does not persist fitted per-profile estimators; feature importance was not used for winner selection.",
            },
            "missing_planned_artifacts": [
                {
                    "artifact": "feature_importance_by_profile.csv",
                    "status": "NOT_PRODUCED",
                    "reason": "Rich runner does not persist fitted per-profile estimators; feature importance was not used for winner selection.",
                }
            ],
            "target_rates": target_rates,
            "preflight": preflight,
            "input_artifact_hashes": preflight["input_artifact_hashes"],
            "artifacts": {
                "summary_csv": str(prefix.with_name(prefix.name + "_summary.csv")),
                "trades_csv": str(prefix.with_name(prefix.name + "_trades.csv")),
                "scores_csv": str(prefix.with_name(prefix.name + "_scores.csv")),
                "feature_contract_csv": str(prefix.with_name(prefix.name + "_feature_contract.csv")),
                "target_distribution_csv": str(prefix.with_name(prefix.name + "_target_distribution.csv")),
                "split_manifest_csv": str(prefix.with_name(prefix.name + "_split_manifest.csv")),
                "forbidden_column_audit_csv": str(prefix.with_name(prefix.name + "_forbidden_column_audit.csv")),
                "feature_distribution_flags_csv": str(prefix.with_name(prefix.name + "_feature_distribution_flags.csv")),
                "selected_score_diagnostics_csv": str(prefix.with_name(prefix.name + "_selected_score_diagnostics.csv")),
            },
        }
    )
    prefix.with_suffix(".json").write_text(json.dumps(artifact, ensure_ascii=True, indent=2, default=str), encoding="utf-8")
    print("finished fractal0_rich_entry_quality", flush=True)
    return artifact


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--threads", type=int, default=base.CONFIG.default_threads)
    parser.add_argument("--no-resume", action="store_true")
    parser.add_argument("--output-prefix", default=DEFAULT_OUTPUT_PREFIX)
    parser.add_argument("--execution-ohlc-path", default="MT/MQL4/Files/XAUUSD_M5_OHLC.csv")
    parser.add_argument("--stop-policy-id", default="")
    parser.add_argument("--stop-grid-artifact", default=DEFAULT_STOP_GRID_ARTIFACT)
    parser.add_argument("--permutation-repeats", type=int, default=200)
    parser.add_argument("--smoke-limit-filters", type=int, default=0)
    parser.add_argument("--rich-entry-quality", action="store_true")
    parser.add_argument("--include-diagnostic-models", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.rich_entry_quality:
        run_rich_entry_quality(args)
    else:
        run_entry_quality(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
