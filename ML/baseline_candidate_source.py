# =============================================================================
# File: baseline_candidate_source.py
# Purpose: Stage 07 — Dummy + ML baselines for live-safe candidate-source model.
# Target: buy_sl3_tp3 (most balanced Triple Barrier combo: SL=35%, TP=36%)
# Method: tree-based (RF, HGB) on flat fractal-level features + dummy baselines.
# Data: train (fit) + validation (evaluate only). Test NOT viewed.
# Updated: 2026-05-25
# =============================================================================

from __future__ import annotations

import argparse
import json
import numpy as np
import pandas as pd
from pathlib import Path
from collections import defaultdict

from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.dummy import DummyClassifier
from sklearn.metrics import classification_report

from ML.fractal_level_feature_builder import build_fractal_level_features

DATA_DIR = Path("DATA")
REPORT_DIR = Path("ML/reports/methodology_cycle_candidate_source_v2")
TARGET_COL = "buy_sl3_tp3"
FEATURE_K = 16


def load_split(name: str) -> pd.DataFrame:
    path = DATA_DIR / f"Nero_{name}_labeled.csv"
    return pd.read_csv(path, sep=";")


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    return build_fractal_level_features(df, input_family="nearest_k", k=FEATURE_K)


def compute_pf(df: pd.DataFrame, proba_col: str, threshold: float) -> dict:
    """Profit factor for buy_sl3_tp3: TP hit=+3ATR, SL hit=-3ATR, timeout=0.
    Raw labels: 0.0=SL, 0.5=timeout, 1.0=TP."""
    pred = (df[proba_col] >= threshold).astype(int)
    mask = pred == 1
    n = mask.sum()
    if n == 0:
        return {"PF": 0.0, "trades": 0, "win_rate": 0.0, "tp": 0, "sl": 0, "timeout": 0}

    outcomes = df.loc[mask, TARGET_COL]
    tp = int((outcomes == 1.0).sum())
    sl = int((outcomes == 0.0).sum())
    timeout = int((outcomes == 0.5).sum())

    gross_profit = tp * 3.0
    gross_loss = sl * 3.0

    pf = float("inf") if gross_loss == 0 else gross_profit / gross_loss
    wr = tp / max(tp + sl, 1)
    return {"PF": round(pf, 4), "trades": int(n), "win_rate": round(wr, 4),
            "tp": tp, "sl": sl, "timeout": timeout}


def per_year_pf(df: pd.DataFrame, proba_col: str, threshold: float) -> dict[int, dict]:
    df = df.copy()
    df["year"] = pd.to_datetime(df["time"], format="%Y.%m.%d %H:%M", errors="coerce").dt.year
    results = {}
    for year, group in df.groupby("year"):
        results[int(year)] = compute_pf(group, proba_col, threshold)
    return results


def per_side_pf(df: pd.DataFrame, proba_col: str, threshold: float) -> dict:
    """Evaluate BUY-only and SELL-only using the signal label (for diagnostic only)."""
    results = {}
    for side, label in [("BUY", 1), ("SELL", -1)]:
        subset = df[df["signal"] == label]
        results[side] = compute_pf(subset, proba_col, threshold)
    return results


def threshold_sweep(df: pd.DataFrame, proba_col: str, thresholds: list[float]) -> dict:
    best = None
    for t in thresholds:
        r = compute_pf(df, proba_col, t)
        r["threshold"] = t
        if best is None or (r["PF"] > best["PF"] and r["trades"] >= 6):
            best = r
    return best or {"PF": 0.0, "trades": 0}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--k", type=int, default=FEATURE_K, help="nearest-k slots")
    parser.add_argument("--thresholds", type=str, default="0.5,0.55,0.6,0.65,0.7,0.75",
                        help="comma-separated thresholds for sweep")
    parser.add_argument("--target", default=TARGET_COL)
    args = parser.parse_args()
    thresholds = [float(x) for x in args.thresholds.split(",")]

    print("Loading data...")
    train_raw = load_split("train")
    val_raw = load_split("validation")
    print(f"  Train: {len(train_raw)} rows, Val: {len(val_raw)} rows")

    print(f"Building features (k={args.k})...")
    X_train = build_features(train_raw)
    X_val = build_features(val_raw)
    print(f"  Features: {X_train.shape[1]} columns")

    y_train = train_raw[args.target].values
    y_val = val_raw[args.target].values

    # Map TB labels {0.0, 0.5, 1.0} → {0, 1, 2} for sklearn classifiers
    label_map = {0.0: 0, 0.5: 1, 1.0: 2}
    inv_label_map = {0: 0.0, 1: 0.5, 2: 1.0}
    y_train_enc = np.array([label_map.get(y, 0) for y in y_train])
    y_val_enc = np.array([label_map.get(y, 0) for y in y_val])

    feature_cols = [c for c in X_train.columns]
    results = []

    # ─── Dummy baselines ───
    print("\n=== Dummy Baselines ===")
    for strategy in ["most_frequent", "stratified", "uniform"]:
        name = f"dummy_{strategy}"
        clf = DummyClassifier(strategy=strategy, random_state=42)
        clf.fit(X_train, y_train_enc)
        val_df = val_raw.copy()
        val_df["proba"] = clf.predict_proba(X_val)[:, 2]  # TP probability (class 2)

        best = threshold_sweep(val_df, "proba", thresholds)
        best["model"] = name
        results.append(best)
        print(f"  {name:20s} best_t={best.get('threshold',0):.2f} PF={best['PF']:.2f} trades={best['trades']}")

    # ─── Simple ML baselines ───
    print("\n=== ML Baselines ===")
    ml_models = {
        "RF_160": RandomForestClassifier(n_estimators=160, min_samples_leaf=20,
                                          class_weight="balanced_subsample", random_state=42, n_jobs=-1),
        "HGB": HistGradientBoostingClassifier(max_iter=200, early_stopping=True,
                                               random_state=42),
    }

    for name, clf in ml_models.items():
        print(f"  Training {name}...")
        clf.fit(X_train, y_train_enc)
        val_df = val_raw.copy()
        val_df["proba"] = clf.predict_proba(X_val)[:, 2]  # TP probability

        best = threshold_sweep(val_df, "proba", thresholds)
        best["model"] = name
        results.append(best)

        year_pf = per_year_pf(val_df, "proba", best["threshold"])
        neg_years = sum(1 for y, r in year_pf.items() if r["PF"] < 1.0 and r["trades"] > 0)
        print(f"  {name:20s} best_t={best['threshold']:.2f} PF={best['PF']:.2f} "
              f"trades={best['trades']} wr={best['win_rate']:.1%} neg_years={neg_years}")

    # ─── Report ───
    print("\n=== Baseline Summary ===")
    for r in sorted(results, key=lambda x: x["PF"], reverse=True):
        print(f"  {r['model']:20s} PF={r['PF']:6.2f} trades={r['trades']:5d} wr={r['win_rate']:.1%}")

    # Save
    output = {
        "cycle_id": "methodology_cycle_candidate_source_v2",
        "stage": "07-baseline-first",
        "created_at": "2026-05-25",
        "target": args.target,
        "feature_config": {"input_family": "nearest_k", "k": args.k, "n_features": len(feature_cols)},
        "split": {"train_rows": len(train_raw), "val_rows": len(val_raw)},
        "results": results,
    }
    out_path = REPORT_DIR / "stage07_baselines.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2, default=str)
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
