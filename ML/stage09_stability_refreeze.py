# =============================================================================
# Файл: stage09_stability_refreeze.py
# Назначение: Stage 09 validation-only stability scan for the frozen Transformer.
# Обновлён: 2026-05-26
# Входные данные:
#   - DATA/Nero_validation_labeled.csv
#   - ML/checkpoints/transformer_winner.pt
#   - ML/checkpoints/pll_normalizer_v1.pkl
# Выходные данные:
#   - ML/reports/methodology_cycle_candidate_source_v2/stage09_stability_refreeze.json
# Использование:
#   ./.venv/bin/python ML/stage09_stability_refreeze.py
# Примечания:
#   - Test split is never read. Top-k candidates are converted to validation-calibrated thresholds for live/test safety.
# =============================================================================

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ML.data_loader import parse_fractals_to_3d
from ML.pll_normalizer import PLLFeatureNormalizer
from ML.validation_freeze import (
    LABEL_MAP,
    SEED,
    SEQ_LEN,
    TARGET,
    TransformerEncoder3Class,
    compute_pf,
    env_info,
    file_sha256,
    sanitize_for_json,
)

os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"
torch.use_deterministic_algorithms(True)
torch.manual_seed(SEED)
np.random.seed(SEED)

DATA_DIR = Path("DATA")
CKPT_DIR = Path("ML/checkpoints")
REPORT_DIR = Path("ML/reports/methodology_cycle_candidate_source_v2")

CHECKPOINT = CKPT_DIR / "transformer_winner.pt"
NORMALIZER = CKPT_DIR / "pll_normalizer_v1.pkl"
OUT_PATH = REPORT_DIR / "stage09_stability_refreeze.json"

THRESHOLDS = [round(x, 2) for x in np.arange(0.30, 0.76, 0.025)]
TOP_K_PCTS = [0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0, 7.5, 10.0, 12.5, 15.0, 20.0, 25.0, 30.0]

MIN_PF = 1.5
MIN_TRADES_PER_YEAR = 6.0
MIN_ACTIVE_YEARS = 3
MAX_YEAR_TRADE_SHARE = 0.60
MIN_BOOTSTRAP_CI_LOW = 1.0
VALIDATION_YEARS = 3.5


def load_validation_proba() -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    val_raw = pd.read_csv(DATA_DIR / "Nero_validation_labeled.csv", sep=";")
    yv = val_raw[TARGET].map(LABEL_MAP).fillna(0).astype(int).values

    x_val, mask_val = parse_fractals_to_3d(val_raw)
    x_val, mask_val = x_val[:, :SEQ_LEN, :], mask_val[:, :SEQ_LEN]
    norm = PLLFeatureNormalizer.load(str(NORMALIZER))
    x_val = norm.transform(x_val)

    ckpt = torch.load(CHECKPOINT, map_location="cpu")
    model = TransformerEncoder3Class()
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()

    ds = TensorDataset(
        torch.from_numpy(x_val).float(),
        torch.from_numpy(mask_val).bool(),
        torch.from_numpy(yv).long(),
    )
    probs = []
    with torch.no_grad():
        for xb, mb, _ in DataLoader(ds, batch_size=256, shuffle=False):
            probs.append(F.softmax(model(xb, mb), 1)[:, 2].cpu())
    return val_raw, yv, torch.cat(probs).numpy()


def bootstrap_pf_ci(y_true: np.ndarray, selected: np.ndarray, n_bootstrap: int = 1000) -> dict | None:
    idx_selected = np.flatnonzero(selected)
    if len(idx_selected) < 2:
        return None
    rng = np.random.RandomState(SEED)
    pfs = []
    for _ in range(n_bootstrap):
        sample_idx = rng.choice(idx_selected, len(idx_selected), replace=True)
        tp = int((y_true[sample_idx] == 2).sum())
        sl = int((y_true[sample_idx] == 0).sum())
        if sl == 0:
            continue
        pf = tp / sl
        if pf > 0:
            pfs.append(pf)
    if len(pfs) < 20:
        return None
    pfs_arr = np.asarray(pfs, dtype=float)
    return {
        "mean": round(float(pfs_arr.mean()), 4),
        "ci95_low": round(float(np.percentile(pfs_arr, 2.5)), 4),
        "ci95_high": round(float(np.percentile(pfs_arr, 97.5)), 4),
        "n_bootstrap": n_bootstrap,
        "finite_samples": int(len(pfs_arr)),
    }


def evaluate_selection(
    val_raw: pd.DataFrame,
    y_true: np.ndarray,
    proba: np.ndarray,
    selected: np.ndarray,
    family: str,
    value: float,
    threshold_equivalent: float | None = None,
) -> dict:
    selected = selected.astype(bool)
    pred = selected.astype(int)
    base = compute_pf(y_true, proba=np.where(selected, 1.0, 0.0), threshold=0.5)

    years = pd.to_datetime(val_raw["time"], format="%Y.%m.%d %H:%M", errors="coerce").dt.year
    per_year = {}
    negative_years = 0
    active_years = 0
    max_year_trades = 0
    for year in sorted(years.dropna().unique()):
        mask = (years.values == year)
        r = compute_pf(y_true[mask], proba=pred[mask].astype(float), threshold=0.5)
        per_year[str(int(year))] = r
        max_year_trades = max(max_year_trades, r["trades"])
        if r["trades"] > 0:
            active_years += 1
            if r["PF"] < 1.0:
                negative_years += 1

    trades = base["trades"]
    max_year_trade_share = max_year_trades / trades if trades else 0.0
    bootstrap = bootstrap_pf_ci(y_true, selected)

    gates = {
        "pf_ge_1_5": base["PF"] >= MIN_PF,
        "trades_per_year_ge_6": (trades / VALIDATION_YEARS) >= MIN_TRADES_PER_YEAR,
        "negative_years_eq_0": negative_years == 0,
        "active_years_ge_3": active_years >= MIN_ACTIVE_YEARS,
        "max_year_trade_share_le_0_60": max_year_trade_share <= MAX_YEAR_TRADE_SHARE,
        "bootstrap_ci_low_ge_1_0": bool(bootstrap and bootstrap["ci95_low"] >= MIN_BOOTSTRAP_CI_LOW),
    }

    stability_score = (
        base["PF"]
        * min(trades / (MIN_TRADES_PER_YEAR * VALIDATION_YEARS), 2.0)
        * (1.0 - min(max_year_trade_share, 1.0))
        * (active_years / 4.0)
    )

    return {
        "family": family,
        "value": value,
        "threshold_equivalent": threshold_equivalent,
        **base,
        "trades_per_year": round(trades / VALIDATION_YEARS, 4),
        "negative_years": negative_years,
        "active_years": active_years,
        "max_year_trade_share": round(max_year_trade_share, 4),
        "per_year": per_year,
        "bootstrap": bootstrap,
        "gates": gates,
        "all_stability_gates_pass": all(gates.values()),
        "stability_score": round(float(stability_score), 6),
    }


def main() -> None:
    val_raw, y_true, proba = load_validation_proba()
    rows = []

    for threshold in THRESHOLDS:
        rows.append(
            evaluate_selection(
                val_raw,
                y_true,
                proba,
                proba >= threshold,
                "threshold",
                float(threshold),
            )
        )

    order = np.argsort(-proba)
    n = len(proba)
    for pct in TOP_K_PCTS:
        k = max(1, int(round(n * pct / 100.0)))
        selected = np.zeros(n, dtype=bool)
        selected[order[:k]] = True
        threshold_equivalent = float(proba[order[k - 1]])
        rows.append(
            evaluate_selection(
                val_raw,
                y_true,
                proba,
                selected,
                "top_k_pct",
                float(pct),
                threshold_equivalent=threshold_equivalent,
            )
        )

    eligible = [r for r in rows if r["all_stability_gates_pass"]]
    eligible.sort(key=lambda r: (r["stability_score"], r["PF"], r["trades"]), reverse=True)

    by_pf = sorted(rows, key=lambda r: (r["PF"], r["trades"]), reverse=True)[:10]
    by_trades = sorted(rows, key=lambda r: (r["trades"], r["PF"]), reverse=True)[:10]
    by_stability = sorted(rows, key=lambda r: (r["stability_score"], r["PF"]), reverse=True)[:10]

    output = sanitize_for_json(
        {
            "cycle_id": "methodology_cycle_candidate_source_v2",
            "stage": "09-validation-freeze-stability-refreeze",
            "scope": "validation-only; test not read",
            "source_rule": "stage09_frozen_rule.json",
            "checkpoint": str(CHECKPOINT),
            "checkpoint_sha256": file_sha256(str(CHECKPOINT)),
            "normalizer": str(NORMALIZER),
            "normalizer_sha256": file_sha256(str(NORMALIZER)),
            "target": TARGET,
            "seq_len": SEQ_LEN,
            "search_space": {
                "thresholds": THRESHOLDS,
                "top_k_pcts": TOP_K_PCTS,
            },
            "stability_gates": {
                "min_pf": MIN_PF,
                "min_trades_per_year": MIN_TRADES_PER_YEAR,
                "min_active_years": MIN_ACTIVE_YEARS,
                "max_year_trade_share": MAX_YEAR_TRADE_SHARE,
                "max_negative_years": 0,
                "min_bootstrap_ci_low": MIN_BOOTSTRAP_CI_LOW,
            },
            "eligible_count": len(eligible),
            "selected_rule": eligible[0] if eligible else None,
            "best_by_pf_top10": by_pf,
            "best_by_trades_top10": by_trades,
            "best_by_stability_top10": by_stability,
            "all_results": rows,
            "environment": env_info(),
            "verdict": "PASS" if eligible else "NO_STABLE_RULE_FOUND",
            "interpretation": (
                "A PASS here means an alternative validation-only selection rule passed the stricter "
                "stability gates. It does not authorize Stage 10 by itself; Stage 09 canonical rule "
                "must be updated explicitly before frozen test."
            ),
        }
    )
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(output, f, indent=2, allow_nan=False)
    print(f"Saved: {OUT_PATH}")
    print(f"Eligible stable rules: {len(eligible)}")
    if eligible:
        r = eligible[0]
        print(
            f"Selected: {r['family']}={r['value']} PF={r['PF']} trades={r['trades']} "
            f"active_years={r['active_years']} max_year_share={r['max_year_trade_share']}"
        )
    else:
        best = by_stability[0]
        print(
            f"No stable rule. Best stability: {best['family']}={best['value']} PF={best['PF']} "
            f"trades={best['trades']} active_years={best['active_years']} "
            f"max_year_share={best['max_year_trade_share']}"
        )


if __name__ == "__main__":
    main()
