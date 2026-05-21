# =============================================================================
# Файл: benchmark_buy_only_direction.py
# Назначение: BUY-only baseline на исправленных сырых признаках (Phase A+B ребилда).
# Создан: 2026-05-18 — Phase A/B переделки E0-E5 (audit rebuild)
# =============================================================================

from __future__ import annotations

import argparse, csv, json, os, pickle, sys, time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.utils.class_weight import compute_sample_weight

from ML.entry_path_trade_filter import compute_pf

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_FEATURES_PATH = PROJECT_ROOT / "DATA" / "raw_features_for_direction.pkl"
OHLC_PATH = PROJECT_ROOT / "DATA" / "XAUUSD_H1_OHLC.csv"
REPORT_DIR = PROJECT_ROOT / "ML" / "reports" / "buy_only_direction_rebuild"

_RANDOM_SEED = 42
HOLD_BARS = 24
DEFAULT_K = 4
RF_TREES = 160
RF_MIN_SAMPLES_LEAF = 20
HGB_MAX_ITER = 200
HGB_MAX_DEPTH = 5
HGB_MIN_SAMPLES_LEAF = 40
LEARNING_RATE = 0.05

TARGET_THRESHOLD_GRID = [0.0, 0.5, 1.0, 1.5, 2.0]
BUY_THRESHOLD_GRID = [0.3, 0.4, 0.5, 0.6]
MARGIN_GRID = [0.0, 0.05, 0.10]

RF_N_JOBS = -1


def _sf(val, default=0.0):
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


# ═══════════════════════════════════════════════════════════════════════════════
# OHLC
# ═══════════════════════════════════════════════════════════════════════════════

def load_ohlc(path: Path):
    ohlc = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f, delimiter=";"):
            t = datetime.strptime(row["time"], "%Y.%m.%d %H:%M").replace(tzinfo=timezone.utc)
            ohlc[t] = (float(row["open"]), float(row["high"]), float(row["low"]), float(row["close"]))
    times = sorted(ohlc.keys())
    return ohlc, times, {t: i for i, t in enumerate(times)}


# ═══════════════════════════════════════════════════════════════════════════════
# Feature builder (raw prices, correct ATR units)
# ═══════════════════════════════════════════════════════════════════════════════

def build_features_from_raw(df_raw: pd.DataFrame, *, k: int = DEFAULT_K, verbose: bool = True) -> pd.DataFrame:
    """Строит nearest-k признаки из сырых цен и сырого ATR."""
    n = len(df_raw)
    records = []
    for i, (_, row) in enumerate(df_raw.iterrows()):
        if verbose and (i + 1) % 10000 == 0:
            print(f"  features: {i + 1}/{n}...", flush=True)

        raw_atr = max(_sf(row.get("raw_ATR", 0)), 0.001)
        f0_price_raw = _sf(row.get("fractal0_price_raw", 0))
        f0_direction = int(row.get("fractal0_direction", 0))
        f0_strong = int(row.get("fractal0_strong", 0))

        feat = {
            "atr": raw_atr,
            "fractal0_direction": float(f0_direction),
            "fractal0_strong": float(f0_strong),
        }

        candidates = []
        all_prices = []
        for fi in range(100):
            p_raw = _sf(row.get(f"f{fi}_price_raw", None), default=np.nan)
            if not np.isnan(p_raw):
                all_prices.append(p_raw)
            if fi == 0:
                continue
            direction = int(row.get(f"f{fi}_direction", 0))
            if direction == 0:
                continue
            raw_distance = (p_raw - f0_price_raw) / raw_atr if not np.isnan(p_raw) else 1000.0
            candidates.append({
                "fi": fi,
                "abs_distance": abs(raw_distance),
                "raw_distance": raw_distance,
                "direction": direction,
                "front": _sf(row.get(f"f{fi}_front", 0)),
                "back": _sf(row.get(f"f{fi}_back", 0)),
                "strong": int(row.get(f"f{fi}_strong", 0)),
                "break": _sf(row.get(f"f{fi}_break", 0)),
                "reverse": _sf(row.get(f"f{fi}_reverse", 0)),
                "power": _sf(row.get(f"f{fi}_power", 0)),
                "count": _sf(row.get(f"f{fi}_count", 0)),
                "impulse": _sf(row.get(f"f{fi}_impulse", 0)),
                "fractal_atr": _sf(row.get(f"f{fi}_fractal_atr", 0)),
            })

        candidates.sort(key=lambda c: (c["abs_distance"], c["fi"]))

        below = sum(1 for p in all_prices if p < f0_price_raw)
        feat["fractal0_price_rank"] = below / max(len(all_prices) - 1, 1) if len(all_prices) > 1 else 0.5
        feat["fractals_above_count"] = float(sum(1 for c in candidates if c["raw_distance"] > 0 and c["raw_distance"] < 1000))
        feat["fractals_below_count"] = float(len([c for c in candidates if c["raw_distance"] < 0 and c["raw_distance"] > -1000]))

        for slot in range(k):
            prefix = f"nearest_{slot:02d}"
            if slot < len(candidates):
                c = candidates[slot]
                feat[f"{prefix}_valid"] = 1.0
                feat[f"{prefix}_source_index"] = float(c["fi"])
                feat[f"{prefix}_raw_distance_atr"] = c["raw_distance"]
                feat[f"{prefix}_abs_distance_atr"] = c["abs_distance"]
                for field in ("direction", "front", "back", "strong", "break", "reverse", "power", "count", "impulse", "fractal_atr"):
                    feat[f"{prefix}_{field}"] = float(c[field])
            else:
                feat[f"{prefix}_valid"] = 0.0
                feat[f"{prefix}_source_index"] = -1.0
                feat[f"{prefix}_raw_distance_atr"] = 0.0
                feat[f"{prefix}_abs_distance_atr"] = 0.0
                for field in ("direction", "front", "back", "strong", "break", "reverse", "power", "count", "impulse", "fractal_atr"):
                    feat[f"{prefix}_{field}"] = 0.0

        records.append(feat)

    return pd.DataFrame(records)


def fit_feature_normalizer(train_features: pd.DataFrame) -> dict:
    stats = {}
    for col in train_features.columns:
        if col.endswith("_valid") or col.endswith("_source_index"):
            continue
        vals = train_features[col].values.astype(np.float64)
        mean = float(np.nanmean(vals))
        std = float(np.nanstd(vals))
        stats[col] = (mean, max(std, 1e-10))
    return stats


def apply_feature_normalizer(features: pd.DataFrame, stats: dict) -> pd.DataFrame:
    result = features.copy()
    for col, (mean, std) in stats.items():
        if col in result.columns:
            result[col] = (result[col].astype(np.float64) - mean) / std
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# Target builder
# ═══════════════════════════════════════════════════════════════════════════════

def build_buy_only_target_batch(
    df_raw: pd.DataFrame,
    ohlc: dict,
    ohlc_times: list,
    ohlc_time_idx: dict,
    threshold_atr: float,
    verbose: bool = True,
) -> tuple[np.ndarray, np.ndarray]:
    """Векторизованное построение BUY-only target."""
    n = len(df_raw)
    buy_targets = np.zeros(n, dtype=np.int32)
    true_returns = np.zeros(n, dtype=np.float64)

    for i, (_, row) in enumerate(df_raw.iterrows()):
        if verbose and (i + 1) % 20000 == 0:
            print(f"  targets: {i + 1}/{n}...", flush=True)
        time_str = str(row.get("time", ""))
        raw_atr = _sf(row.get("raw_ATR", 0), 0)
        if raw_atr <= 0:
            continue
        try:
            dt = datetime.strptime(time_str, "%Y.%m.%d %H:%M").replace(tzinfo=timezone.utc)
        except (ValueError, KeyError):
            continue
        idx = ohlc_time_idx.get(dt)
        if idx is None or idx + 1 + HOLD_BARS >= len(ohlc_times):
            continue
        entry_price = ohlc[ohlc_times[idx + 1]][0]
        exit_price = ohlc[ohlc_times[idx + 1 + HOLD_BARS]][3]
        price_change = exit_price - entry_price
        atr_change = abs(price_change) / raw_atr
        true_returns[i] = price_change / raw_atr
        if atr_change > threshold_atr and price_change > 0:
            buy_targets[i] = 1

    return buy_targets, true_returns


# ═══════════════════════════════════════════════════════════════════════════════
# Evaluation
# ═══════════════════════════════════════════════════════════════════════════════

def evaluate_predictions(
    df_raw: pd.DataFrame,
    signal: np.ndarray,
    ohlc: dict,
    ohlc_times: list,
    ohlc_time_idx: dict,
) -> dict[str, Any]:
    """Оценивает сигналы: PF, sequential PF, yearly PF."""
    active = signal.astype(bool)
    n_active = active.sum()
    if n_active == 0:
        return {"validation_trades": 0, "validation_pf": 0.0, "validation_sequential_pf": 0.0,
                "buy_trades": 0, "sell_trades": 0, "buy_pf": 0.0, "sell_pf": 0.0,
                "buy_win_rate": 0.0, "sell_win_rate": 0.0, "negative_years": 0, "yearly_pf": {}}

    # True returns for all active signals
    true_rets = np.zeros(n_active, dtype=np.float64)
    years_map: dict[str, list[int]] = {}
    active_indices = np.where(active)[0]
    for j, i in enumerate(active_indices):
        row = df_raw.iloc[i]
        raw_atr = _sf(row.get("raw_ATR", 0), 0)
        if raw_atr <= 0:
            continue
        time_str = str(row.get("time", ""))
        try:
            dt = datetime.strptime(time_str, "%Y.%m.%d %H:%M").replace(tzinfo=timezone.utc)
        except (ValueError, KeyError):
            continue
        idx = ohlc_time_idx.get(dt)
        if idx is None or idx + 1 + HOLD_BARS >= len(ohlc_times):
            continue
        entry_price = ohlc[ohlc_times[idx + 1]][0]
        exit_price = ohlc[ohlc_times[idx + 1 + HOLD_BARS]][3]
        true_rets[j] = (exit_price - entry_price) / raw_atr
        year = time_str[:4]
        years_map.setdefault(year, []).append(j)

    pnl = true_rets

    # Sequential: non-overlapping
    seq_accepted = []
    last_accepted = -HOLD_BARS - 1
    for j, i in enumerate(active_indices):
        if i - last_accepted >= HOLD_BARS:
            seq_accepted.append(j)
            last_accepted = i
    seq_pnl = pnl[seq_accepted] if seq_accepted else np.array([], dtype=np.float64)

    # Yearly PF
    yearly_pf = {}
    negative_years = 0
    for year, idxs in years_map.items():
        yr_pnl = pnl[idxs]
        yr_pf = compute_pf(yr_pnl) if len(yr_pnl) > 0 else 0.0
        yearly_pf[year] = yr_pf
        if yr_pf < 0.8:
            negative_years += 1

    return {
        "validation_trades": int(n_active),
        "validation_pf": compute_pf(pnl),
        "validation_sequential_pf": compute_pf(seq_pnl),
        "validation_sequential_trades": int(len(seq_accepted)),
        "buy_trades": int(n_active),
        "sell_trades": 0,
        "buy_pf": compute_pf(pnl),
        "sell_pf": 0.0,
        "buy_win_rate": float((pnl > 0).mean()) if len(pnl) else 0.0,
        "sell_win_rate": 0.0,
        "negative_years": negative_years,
        "yearly_pf": yearly_pf,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Winner Selection (исправленный протокол)
# ═══════════════════════════════════════════════════════════════════════════════

def pick_validation_winner(grid: pd.DataFrame) -> dict[str, Any]:
    work = grid.copy()
    work = work[work["validation_trades"] >= 50]
    if "negative_years" in work.columns:
        work = work[work["negative_years"] == 0]
    if len(work) == 0:
        return {"winner": None, "selection_reason": "no candidates pass gates", "candidates_count": 0}
    work = work.sort_values(
        ["validation_sequential_pf", "validation_pf", "validation_trades"],
        ascending=[False, False, False],
    )
    winner_row = work.iloc[0]
    return {
        "winner": winner_row.to_dict(),
        "selection_reason": f"top sequential_pf={winner_row['validation_sequential_pf']:.4f} among {len(work)}",
        "candidates_count": len(work),
        "candidates": work.to_dict("records"),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Phase A
# ═══════════════════════════════════════════════════════════════════════════════

def run_phase_a(
    df_raw: pd.DataFrame,
    ohlc: dict,
    ohlc_times: list,
    ohlc_time_idx: dict,
    output_dir: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    print("=" * 60)
    print("Phase A: BUY-only baseline (directional close target)")
    print("=" * 60, flush=True)

    train_mask = df_raw["split"] == "train"
    val_mask = df_raw["split"] == "validation"
    test_mask = df_raw["split"] == "test"
    df_train = df_raw[train_mask]
    df_val = df_raw[val_mask]
    df_test = df_raw[test_mask]
    n_train = len(df_train)
    n_val = len(df_val)
    n_test = len(df_test)
    print(f"Train: {n_train}, Validation: {n_val}, Test: {n_test}", flush=True)

    # Build features ONCE (they don't depend on target)
    print("Building features (raw price distances, correct ATR units)...", flush=True)
    t0 = time.time()
    X_all = build_features_from_raw(df_raw, k=DEFAULT_K, verbose=True)
    model_cols = [c for c in X_all.columns if not c.endswith("_valid") and not c.endswith("_source_index")]
    X_train_raw = X_all.iloc[:n_train].copy()
    X_val_raw = X_all.iloc[n_train:n_train + n_val].copy()
    X_test_raw = X_all.iloc[n_train + n_val:].copy()
    normalizer = fit_feature_normalizer(X_train_raw)
    X_train = apply_feature_normalizer(X_train_raw, normalizer)[model_cols].values.astype(np.float64)
    X_val = apply_feature_normalizer(X_val_raw, normalizer)[model_cols].values.astype(np.float64)
    X_test = apply_feature_normalizer(X_test_raw, normalizer)[model_cols].values.astype(np.float64)
    print(f"  Done in {time.time() - t0:.1f}s. Features: {X_train.shape[1]}", flush=True)

    all_results = []
    best_seq_pf = -1
    best_config = None

    for target_thr in TARGET_THRESHOLD_GRID:
        print(f"\n--- Target threshold: {target_thr:.1f} ATR ---", flush=True)
        t0 = time.time()

        # Build targets for ALL rows (for evaluation)
        y_all, true_ret_all = build_buy_only_target_batch(
            df_raw, ohlc, ohlc_times, ohlc_time_idx, target_thr, verbose=True
        )
        y_train = y_all[:n_train]
        y_val = y_all[n_train:n_train + n_val]
        true_ret_val = true_ret_all[n_train:n_train + n_val]

        buy_rate = y_train.mean()
        print(f"  BUY rate on train: {buy_rate:.3f} ({y_train.sum()} / {n_train})", flush=True)
        if y_train.sum() < 500:
            print(f"  SKIP: too few positives ({y_train.sum()})", flush=True)
            continue

        for model_type in ["rf", "hgb"]:
            print(f"  Model: {model_type.upper()}", flush=True)
            t1 = time.time()
            if model_type == "rf":
                model = RandomForestClassifier(
                    n_estimators=RF_TREES, min_samples_leaf=RF_MIN_SAMPLES_LEAF,
                    class_weight="balanced_subsample", random_state=_RANDOM_SEED, n_jobs=RF_N_JOBS,
                )
                model.fit(X_train, y_train)
                y_val_prob = model.predict_proba(X_val)[:, 1]
            else:
                sw = compute_sample_weight("balanced", y_train)
                model = HistGradientBoostingClassifier(
                    max_iter=HGB_MAX_ITER, max_depth=HGB_MAX_DEPTH,
                    min_samples_leaf=HGB_MIN_SAMPLES_LEAF,
                    learning_rate=LEARNING_RATE, random_state=_RANDOM_SEED,
                )
                model.fit(X_train, y_train, sample_weight=sw)
                y_val_prob = model.predict_proba(X_val)[:, 1]
            print(f"    trained in {time.time() - t1:.1f}s", flush=True)

            for buy_thr in BUY_THRESHOLD_GRID:
                signal_val = (y_val_prob >= buy_thr).astype(np.int32)
                metrics = evaluate_predictions(df_val, signal_val, ohlc, ohlc_times, ohlc_time_idx)
                result = {
                    "target_threshold_atr": target_thr,
                    "model_type": model_type,
                    "buy_threshold": buy_thr,
                    "feature_count": X_train.shape[1],
                    **metrics,
                }
                all_results.append(result)

                print(f"    buy_thr={buy_thr:.1f} → trades={metrics['validation_trades']:5d} "
                      f"pf={metrics['validation_pf']:.3f} seq_pf={metrics['validation_sequential_pf']:.3f} "
                      f"buy_pf={metrics['buy_pf']:.3f} neg_yrs={metrics['negative_years']}", flush=True)

                if metrics["validation_sequential_pf"] > best_seq_pf and metrics["negative_years"] == 0:
                    best_seq_pf = metrics["validation_sequential_pf"]
                    best_config = result.copy()

        print(f"  Target {target_thr:.1f} done in {time.time() - t0:.1f}s", flush=True)

    # Save grid
    grid_df = pd.DataFrame(all_results)
    grid_df.to_csv(output_dir / "phase_a_validation_grid.csv", index=False)
    print(f"\nGrid saved ({len(all_results)} configs)", flush=True)

    # Winner selection
    winner = pick_validation_winner(grid_df)
    summary = {
        "phase": "A",
        "target_type": "directional_close_buy_only",
        "threshold_grid": TARGET_THRESHOLD_GRID,
        "model_types": ["rf", "hgb"],
        "buy_threshold_grid": BUY_THRESHOLD_GRID,
        "feature_count": X_train.shape[1],
        "k": DEFAULT_K,
        **winner,
        "best_config": best_config,
        "total_configs": len(all_results),
    }

    with open(output_dir / "phase_a_summary.json", "w") as f:
        json.dump(summary, f, indent=2, default=str)

    # Gate verdict
    if best_config:
        print(f"\n=== Best Config ===")
        for k, v in best_config.items():
            if not isinstance(v, dict):
                print(f"  {k}: {v}")
        gate_pass = (
            best_config.get("validation_pf", 0) >= 1.5
            and best_config.get("validation_sequential_pf", 0) >= 1.5
            and best_config.get("negative_years", 99) <= 1
        )
        print(f"\nGATE A: {'PASSED' if gate_pass else 'NOT PASSED'}")

    with open(output_dir / "summary.json", "w") as f:
        json.dump(summary, f, indent=2, default=str)

    return summary


# ═══════════════════════════════════════════════════════════════════════════════
# Phase B: расширение признаков
# ═══════════════════════════════════════════════════════════════════════════════

def add_regime_features(
    df_raw: pd.DataFrame,
    X_base: pd.DataFrame,
    ohlc: dict,
    ohlc_times: list,
    ohlc_time_idx: dict,
) -> pd.DataFrame:
    """Regime-aware: trend strength, volatility regime, trend classification.
    Оптимизировано через numpy-предвычисление."""
    n = len(df_raw)
    result = X_base.copy()
    ma_window = 50
    print("  Computing regime features (vectorized)...", flush=True)

    # Precompute OHLC close array aligned with df_raw rows
    closes = np.full(n, np.nan)
    for i, (_, row) in enumerate(df_raw.iterrows()):
        time_str = str(row.get("time", ""))
        try:
            dt = datetime.strptime(time_str, "%Y.%m.%d %H:%M").replace(tzinfo=timezone.utc)
        except (ValueError, KeyError):
            continue
        idx = ohlc_time_idx.get(dt)
        if idx is not None and idx < len(ohlc_times):
            closes[i] = ohlc[ohlc_times[idx]][3]  # close price

    # Precompute ATR array
    atrs = np.array([_sf(df_raw.iloc[i].get("raw_ATR", 0), 1.0) for i in range(n)], dtype=np.float64)

    # Precompute MA50 as rolling mean
    ma50 = np.full(n, np.nan)
    for i in range(ma_window, n):
        ma50[i] = np.nanmean(closes[i - ma_window + 1:i + 1])

    # Trend strength: (MA50[t] - MA50[t-50]) / ATR[t]
    trend_strength = np.zeros(n)
    for i in range(ma_window * 2, n):
        if not np.isnan(ma50[i]) and not np.isnan(ma50[i - ma_window]):
            trend_strength[i] = (ma50[i] - ma50[i - ma_window]) / max(atrs[i], 0.001)

    # Volatility regime: ATR / rolling median ATR (200 bars)
    vol_regime_ratio = np.ones(n)
    vol_regime_high = np.zeros(n)
    vol_regime_low = np.zeros(n)
    for i in range(200, n):
        atr_median = np.median(atrs[i - 200:i])
        if atr_median > 0:
            ratio = atrs[i] / atr_median
            vol_regime_ratio[i] = ratio
            if ratio > 1.5:
                vol_regime_high[i] = 1.0
            elif ratio < 0.5:
                vol_regime_low[i] = 1.0

    # Populate result DataFrame
    result["trend_strength_50"] = trend_strength
    result["vol_regime_ratio"] = vol_regime_ratio
    result["vol_regime_high"] = vol_regime_high
    result["vol_regime_low"] = vol_regime_low

    # Regime classification one-hot
    regime_bull = np.zeros(n)
    regime_bear = np.zeros(n)
    regime_ranging = np.zeros(n)
    for i in range(n):
        if trend_strength[i] > 0.5:
            regime_bull[i] = 1.0
        elif trend_strength[i] < -0.5:
            regime_bear[i] = 1.0
        else:
            regime_ranging[i] = 1.0
    result["regime_bull"] = regime_bull
    result["regime_bear"] = regime_bear
    result["regime_ranging"] = regime_ranging

    return result


def add_direction_specific_features(X_base: pd.DataFrame) -> pd.DataFrame:
    """Direction-specific: f0_dir × front/back/impulse для nearest-k слотов."""
    result = X_base.copy()
    f0_dir = result.get("fractal0_direction", pd.Series(0, index=result.index))
    for fi in range(DEFAULT_K):
        prefix = f"nearest_{fi:02d}"
        for field in ("front", "back", "impulse", "power"):
            col = f"{prefix}_{field}"
            if col in result.columns:
                result[f"{prefix}_dir_x_{field}"] = f0_dir * result[col].astype(float)
    return result


def run_phase_b(
    df_raw: pd.DataFrame,
    ohlc: dict,
    ohlc_times: list,
    ohlc_time_idx: dict,
    output_dir: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    print("=" * 60)
    print("Phase B: Feature improvement (regime + direction-specific)")
    print("=" * 60, flush=True)

    n_train = (df_raw["split"] == "train").sum()
    n_val = (df_raw["split"] == "validation").sum()
    df_train = df_raw[df_raw["split"] == "train"]
    df_val = df_raw[df_raw["split"] == "validation"]

    # Build base features
    print("Building base features...", flush=True)
    t0 = time.time()
    X_all = build_features_from_raw(df_raw, k=DEFAULT_K, verbose=True)
    print(f"  Base features: {X_all.shape[1]} cols in {time.time() - t0:.1f}s", flush=True)

    # Regime features
    X_all = add_regime_features(df_raw, X_all, ohlc, ohlc_times, ohlc_time_idx)

    # Direction-specific features
    X_all = add_direction_specific_features(X_all)
    print(f"  Extended features: {X_all.shape[1]} cols", flush=True)

    # Use best target from Phase A (thr=1.0 ATR)
    target_thr = 1.0
    print(f"Target threshold: {target_thr:.1f} ATR", flush=True)
    print("Building targets...", flush=True)
    y_all, true_ret_all = build_buy_only_target_batch(
        df_raw, ohlc, ohlc_times, ohlc_time_idx, target_thr, verbose=True
    )
    y_train = y_all[:n_train]
    y_val = y_all[n_train:n_train + n_val]

    # Split features
    X_train_raw = X_all.iloc[:n_train]
    X_val_raw = X_all.iloc[n_train:n_train + n_val]

    normalizer = fit_feature_normalizer(X_train_raw)
    model_cols = [c for c in X_train_raw.columns
                  if not c.endswith("_valid") and not c.endswith("_source_index")]
    X_train = apply_feature_normalizer(X_train_raw, normalizer)[model_cols].values.astype(np.float64)
    X_val = apply_feature_normalizer(X_val_raw, normalizer)[model_cols].values.astype(np.float64)

    print(f"  Model features: {X_train.shape[1]}", flush=True)

    # --- Feature selection via RF importance ---
    print("Feature importance analysis...", flush=True)
    rf_temp = RandomForestClassifier(
        n_estimators=RF_TREES, min_samples_leaf=RF_MIN_SAMPLES_LEAF,
        class_weight="balanced_subsample", random_state=_RANDOM_SEED, n_jobs=RF_N_JOBS,
    )
    rf_temp.fit(X_train, y_train)
    importances = rf_temp.feature_importances_
    top_idx = np.argsort(importances)[::-1][:20]
    print("  Top-20 features by importance:")
    for rank, idx in enumerate(top_idx):
        print(f"    {rank + 1:2d}. {model_cols[idx]:40s} {importances[idx]:.4f}")

    # Remove features with importance < 0.005 (0.5%)
    keep_idx = np.where(importances >= 0.005)[0]
    print(f"  Features before selection: {len(model_cols)}")
    print(f"  Features after selection (imp >= 0.5%): {len(keep_idx)}")

    X_train_sel = X_train[:, keep_idx]
    X_val_sel = X_val[:, keep_idx]
    selected_cols = [model_cols[i] for i in keep_idx]

    # --- Model evaluation ---
    all_results = []
    best_seq_pf = -1
    best_config = None

    for model_type in ["rf", "hgb"]:
        print(f"  Model: {model_type.upper()}", flush=True)
        if model_type == "rf":
            model = RandomForestClassifier(
                n_estimators=RF_TREES, min_samples_leaf=RF_MIN_SAMPLES_LEAF,
                class_weight="balanced_subsample", random_state=_RANDOM_SEED, n_jobs=RF_N_JOBS,
            )
            model.fit(X_train_sel, y_train)
            y_val_prob = model.predict_proba(X_val_sel)[:, 1]
        else:
            sw = compute_sample_weight("balanced", y_train)
            model = HistGradientBoostingClassifier(
                max_iter=HGB_MAX_ITER, max_depth=HGB_MAX_DEPTH,
                min_samples_leaf=HGB_MIN_SAMPLES_LEAF,
                learning_rate=LEARNING_RATE, random_state=_RANDOM_SEED,
            )
            model.fit(X_train_sel, y_train, sample_weight=sw)
            y_val_prob = model.predict_proba(X_val_sel)[:, 1]

        for buy_thr in BUY_THRESHOLD_GRID:
            signal_val = (y_val_prob >= buy_thr).astype(np.int32)
            metrics = evaluate_predictions(df_val, signal_val, ohlc, ohlc_times, ohlc_time_idx)
            result = {
                "phase": "B",
                "target_threshold_atr": target_thr,
                "model_type": model_type,
                "buy_threshold": buy_thr,
                "feature_count_before_selection": len(model_cols),
                "feature_count_after_selection": len(selected_cols),
                **metrics,
            }
            all_results.append(result)
            print(f"    buy_thr={buy_thr:.1f} → trades={metrics['validation_trades']:5d} "
                  f"pf={metrics['validation_pf']:.3f} seq_pf={metrics['validation_sequential_pf']:.3f} "
                  f"neg_yrs={metrics['negative_years']}", flush=True)

            if metrics["validation_sequential_pf"] > best_seq_pf and metrics["negative_years"] == 0:
                best_seq_pf = metrics["validation_sequential_pf"]
                best_config = result.copy()

    grid_df = pd.DataFrame(all_results)
    grid_df.to_csv(output_dir / "phase_b_validation_grid.csv", index=False)

    summary = {
        "phase": "B",
        "feature_count_before": len(model_cols),
        "feature_count_after": len(selected_cols),
        "removed_features": [model_cols[i] for i in range(len(model_cols)) if i not in keep_idx],
        "top20_features": [model_cols[i] for i in top_idx],
        "top20_importances": [float(importances[i]) for i in top_idx],
        "best_config": best_config,
        "total_configs": len(all_results),
    }

    with open(output_dir / "phase_b_summary.json", "w") as f:
        json.dump(summary, f, indent=2, default=str)

    if best_config:
        print(f"\nBest B config: pf={best_config['validation_pf']:.3f} seq_pf={best_config['validation_sequential_pf']:.3f}")
        phase_a_best = None
        pa_path = output_dir / "phase_a_summary.json"
        if pa_path.exists():
            with open(pa_path) as f:
                phase_a_best = json.load(f).get("best_config", {})
        if phase_a_best:
            improvement = best_config.get("validation_sequential_pf", 0) - phase_a_best.get("validation_sequential_pf", 0)
            print(f"  vs Phase A best seq_pf={phase_a_best.get('validation_sequential_pf', 0):.3f} → delta={improvement:+.3f}")
        gate_pass = best_config.get("validation_pf", 0) >= 1.5
        print(f"GATE B: {'PASSED' if gate_pass else 'NOT PASSED'}")

    return summary


# ═══════════════════════════════════════════════════════════════════════════════
# Phase D: Frozen Test
# ═══════════════════════════════════════════════════════════════════════════════

def run_phase_d(
    df_raw: pd.DataFrame,
    ohlc: dict,
    ohlc_times: list,
    ohlc_time_idx: dict,
    output_dir: Path,
    config: dict,
) -> dict[str, Any]:
    """Frozen test: единственный прогон для замороженной конфигурации."""
    output_dir.mkdir(parents=True, exist_ok=True)
    print("=" * 60)
    print("Phase D: Frozen Test")
    print("=" * 60, flush=True)

    target_thr = config.get("target_threshold_atr", 1.0)
    model_type = config.get("model_type", "rf")
    buy_thr = config.get("buy_threshold", 0.5)

    print(f"Config: target_thr={target_thr}, model={model_type}, buy_thr={buy_thr}", flush=True)

    train_mask = df_raw["split"] == "train"
    val_mask = df_raw["split"] == "validation"
    test_mask = df_raw["split"] == "test"
    n_train = train_mask.sum()
    n_val = val_mask.sum()
    df_train_val = df_raw[train_mask | val_mask].copy()
    df_test = df_raw[test_mask].copy()

    # Build features
    print("Building features...", flush=True)
    X_all = build_features_from_raw(df_raw, k=DEFAULT_K, verbose=True)

    # Targets
    print("Building targets...", flush=True)
    y_all, _ = build_buy_only_target_batch(df_raw, ohlc, ohlc_times, ohlc_time_idx, target_thr, verbose=True)

    # Split: train on train+val, test on test
    X_train_raw = pd.concat([X_all.iloc[:n_train], X_all.iloc[n_train:n_train + n_val]], ignore_index=True)
    X_test_raw = X_all.iloc[n_train + n_val:].copy()
    y_train = np.concatenate([y_all[:n_train], y_all[n_train:n_train + n_val]])
    y_test = y_all[n_train + n_val:]

    normalizer = fit_feature_normalizer(X_train_raw)
    model_cols = [c for c in X_train_raw.columns
                  if not c.endswith("_valid") and not c.endswith("_source_index")]
    X_train = apply_feature_normalizer(X_train_raw, normalizer)[model_cols].values.astype(np.float64)
    X_test = apply_feature_normalizer(X_test_raw, normalizer)[model_cols].values.astype(np.float64)

    # Feature selection — skip for Phase D to match validation config exactly
    keep_idx = np.arange(len(model_cols))
    X_train_sel = X_train
    X_test_sel = X_test
    selected_cols = model_cols
    print(f"  Features: {X_train.shape[1]} (no selection — matching Phase A config)", flush=True)

    # Train final model
    if model_type == "rf":
        model = RandomForestClassifier(
            n_estimators=RF_TREES, min_samples_leaf=RF_MIN_SAMPLES_LEAF,
            class_weight="balanced_subsample", random_state=_RANDOM_SEED, n_jobs=RF_N_JOBS,
        )
        model.fit(X_train_sel, y_train)
        y_test_prob = model.predict_proba(X_test_sel)[:, 1]
    else:
        sw = compute_sample_weight("balanced", y_train)
        model = HistGradientBoostingClassifier(
            max_iter=HGB_MAX_ITER, max_depth=HGB_MAX_DEPTH,
            min_samples_leaf=HGB_MIN_SAMPLES_LEAF,
            learning_rate=LEARNING_RATE, random_state=_RANDOM_SEED,
        )
        model.fit(X_train_sel, y_train, sample_weight=sw)
        y_test_prob = model.predict_proba(X_test_sel)[:, 1]

    signal_test = (y_test_prob >= buy_thr).astype(np.int32)
    metrics = evaluate_predictions(df_test, signal_test, ohlc, ohlc_times, ohlc_time_idx)

    # Yearly PF for test
    yearly_pf = metrics.pop("yearly_pf", {})

    result = {
        "phase": "D (frozen test)",
        "config": config,
        "feature_count": X_train_sel.shape[1],
        **metrics,
        "yearly_pf": yearly_pf,
    }

    with open(output_dir / "frozen_test.json", "w") as f:
        json.dump(result, f, indent=2, default=str)

    print(f"\nFrozen test results:")
    for k, v in result.items():
        if k not in ("config", "yearly_pf"):
            print(f"  {k}: {v}")

    if yearly_pf:
        print(f"  Yearly PF:")
        for yr, pf in sorted(yearly_pf.items()):
            print(f"    {yr}: {pf:.3f}")

    gate_pass = metrics.get("validation_pf", 0) >= 1.5 and metrics.get("negative_years", 99) <= 1
    print(f"\nGATE D: {'PASSED' if gate_pass else 'NOT PASSED'}")

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    parser = argparse.ArgumentParser(description="BUY-only direction benchmark (Phase A/B/D rebuild)")
    parser.add_argument("--phase", choices=["A", "B", "D"], default="A")
    parser.add_argument("--raw-features", type=Path, default=RAW_FEATURES_PATH)
    parser.add_argument("--ohlc", type=Path, default=OHLC_PATH)
    parser.add_argument("--output-dir", type=Path, default=REPORT_DIR)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    global _RANDOM_SEED
    _RANDOM_SEED = args.seed

    if not args.raw_features.exists():
        print(f"ERROR: {args.raw_features} not found. Run Phase 0 first.", flush=True)
        sys.exit(1)

    print(f"Loading raw features from {args.raw_features} ...", flush=True)
    t0 = time.time()
    with open(args.raw_features, "rb") as f:
        df_raw = pickle.load(f)
    print(f"  Loaded {len(df_raw)} rows in {time.time() - t0:.1f}s", flush=True)

    print(f"Loading OHLC from {args.ohlc} ...", flush=True)
    t0 = time.time()
    ohlc, ohlc_times, ohlc_time_idx = load_ohlc(args.ohlc)
    print(f"  Loaded {len(ohlc)} bars in {time.time() - t0:.1f}s", flush=True)

    if args.phase == "A":
        run_phase_a(df_raw, ohlc, ohlc_times, ohlc_time_idx, args.output_dir)
    elif args.phase == "B":
        run_phase_b(df_raw, ohlc, ohlc_times, ohlc_time_idx, args.output_dir)
    elif args.phase == "D":
        # Load Phase A winner config (from pick_validation_winner, not best_config)
        pa_path = args.output_dir / "phase_a_summary.json"
        if pa_path.exists():
            with open(pa_path) as f:
                pa = json.load(f)
            config = pa.get("winner", pa.get("best_config", {}))
        else:
            config = {"target_threshold_atr": 0.0, "model_type": "rf", "buy_threshold": 0.6}
        print(f"Winner config: target_thr={config.get('target_threshold_atr')}, "
              f"model={config.get('model_type')}, buy_thr={config.get('buy_threshold')}", flush=True)
        run_phase_d(df_raw, ohlc, ohlc_times, ohlc_time_idx, args.output_dir, config)

    print(f"\nDone. Results: {args.output_dir}", flush=True)


if __name__ == "__main__":
    main()
