# =============================================================================
# Файл: baseline_candidate_source.py
# Назначение: Stage 07 — dummy + ML baselines for live-safe candidate-source model.
# Обновлён: 2026-05-26
# Входные данные:
#   - DATA/Nero_train_labeled.csv
#   - DATA/Nero_validation_labeled.csv
# Выходные данные:
#   - ML/reports/methodology_cycle_candidate_source_v2/stage07_baselines.json
# Использование:
#   ./.venv/bin/python ML/baseline_candidate_source.py --thresholds 0.35,0.40,0.45,0.50,0.55,0.60,0.65,0.70,0.75
# Примечания:
#   - Test split is never read.
#   - Trading metrics are gross diagnostic; costs are handled in later methodology stages.
# =============================================================================

from __future__ import annotations

import argparse
import json
import sys
import numpy as np
import pandas as pd
from pathlib import Path
from collections import defaultdict

from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.dummy import DummyClassifier
from sklearn.metrics import classification_report, confusion_matrix, matthews_corrcoef

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ML.fractal_level_feature_builder import build_fractal_level_features

DATA_DIR = Path("DATA")
REPORT_DIR = Path("ML/reports/methodology_cycle_candidate_source_v2")
TARGET_COL = "buy_sl3_tp3"
FEATURE_K = 16
LABEL_MAP = {0.0: 0, 0.5: 1, 1.0: 2}
LABEL_NAMES = ["SL", "timeout", "TP"]


def sanitize_for_json(obj):
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize_for_json(v) for v in obj]
    if isinstance(obj, float):
        if obj == float("inf"):
            return "inf"
        if obj == float("-inf"):
            return "-inf"
        if obj != obj:
            return None
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    return obj


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


def classification_metrics(y_true_enc: np.ndarray, y_pred_enc: np.ndarray) -> dict:
    """Build full validation classification metrics for the 3-class TB target."""
    return {
        "confusion_matrix_labels": LABEL_NAMES,
        "confusion_matrix": confusion_matrix(y_true_enc, y_pred_enc, labels=[0, 1, 2]).tolist(),
        "classification_report": classification_report(
            y_true_enc,
            y_pred_enc,
            labels=[0, 1, 2],
            target_names=LABEL_NAMES,
            output_dict=True,
            zero_division=0,
        ),
        "mcc": float(matthews_corrcoef(y_true_enc, y_pred_enc)),
    }


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

    y_train_enc = np.array([LABEL_MAP.get(y, 0) for y in y_train])
    y_val_enc = np.array([LABEL_MAP.get(y, 0) for y in y_val])

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
        pred_enc = clf.predict(X_val)
        best["classification"] = classification_metrics(y_val_enc, pred_enc)
        best["per_year"] = per_year_pf(val_df, "proba", best["threshold"])
        best["per_side_diagnostic"] = per_side_pf(val_df, "proba", best["threshold"])
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

        year_pf = per_year_pf(val_df, "proba", best["threshold"])
        neg_years = sum(1 for y, r in year_pf.items() if r["PF"] < 1.0 and r["trades"] > 0)
        best["negative_years"] = neg_years
        best["per_year"] = year_pf
        best["per_side_diagnostic"] = per_side_pf(val_df, "proba", best["threshold"])
        best["classification"] = classification_metrics(y_val_enc, clf.predict(X_val))
        results.append(best)
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
        "updated_at": "2026-05-26",
        "methodology_stage": "07-baseline-first",
        "stage_verdict": "PASS",
        "target": args.target,
        "feature_config": {"input_family": "nearest_k", "k": args.k, "n_features": len(feature_cols)},
        "split": {"train_rows": len(train_raw), "val_rows": len(val_raw)},
        "methodology_compliance": {
            "split": "train/validation only; test not read",
            "trading_metrics": "gross diagnostic; costs deferred to Stage 12",
            "classification_metrics_included": True,
            "confusion_matrix_included": True,
            "buy_sell_slices": "diagnostic only because signal label is future-derived and not a live candidate-source input",
        },
        "results": results,
        "baseline_to_beat": {
            "model": "RF_160",
            "validation_pf": max((r["PF"] for r in results if r.get("model") == "RF_160"), default=None),
            "requirement_for_models": "beat RF_160 validation PF and satisfy 0 negative years",
            "note": "Best simple baseline may be gross-profitable but is not production-ready until it satisfies robustness/cost gates.",
        },
    }
    out_path = REPORT_DIR / "stage07_baselines.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(sanitize_for_json(output), f, indent=2, allow_nan=False)
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
