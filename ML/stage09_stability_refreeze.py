# =============================================================================
# Файл: stage09_stability_refreeze.py
# Назначение: Stage 09 — validation-only stability scan + canonical frozen rule.
#   SOURCE OF TRUTH for stage09_frozen_rule.json.
#   Run AFTER validation_freeze.py (which trains and saves the checkpoint).
# Обновлён: 2026-05-27
# Входные данные:
#   - DATA/Nero_validation_labeled.csv
#   - ML/checkpoints/transformer_winner.pt
#   - ML/checkpoints/pll_normalizer_v1.pkl
# Выходные данные:
#   - ML/reports/methodology_cycle_candidate_source_v2/stage09_frozen_rule.json  ← canonical rule
#   - ML/reports/methodology_cycle_candidate_source_v2/stage09_stability_refreeze.json  ← full scan
# Использование:
#   ./.venv/bin/python ML/stage09_stability_refreeze.py
# Примечания:
#   - Test split is never read.
#   - Top-k candidates are converted to validation-calibrated thresholds for live/test safety.
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
    PNL_COL,
    SEED,
    SEQ_LEN,
    TARGET,
    THRESHOLD as TRAINING_THRESHOLD,
    EPOCHS,
    N_CLASSES,
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
FROZEN_RULE_PATH = REPORT_DIR / "stage09_frozen_rule.json"
SCAN_PATH = REPORT_DIR / "stage09_stability_refreeze.json"

THRESHOLDS = [round(x, 2) for x in np.arange(0.30, 0.76, 0.025)]
TOP_K_PCTS = [0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0, 7.5, 10.0, 12.5, 15.0, 20.0, 25.0, 30.0]

MIN_PF = 1.5
MIN_TRADES_PER_YEAR = 6.0
MIN_ACTIVE_YEARS = 3
MAX_YEAR_TRADE_SHARE = 0.60
MIN_BOOTSTRAP_CI_LOW = 1.0
VALIDATION_YEARS = 3.5


def load_validation_proba() -> tuple[pd.DataFrame, np.ndarray, np.ndarray, np.ndarray]:
    val_raw = pd.read_csv(DATA_DIR / "Nero_validation_labeled.csv", sep=";")
    yv = val_raw[TARGET].map(LABEL_MAP).fillna(0).astype(int).values
    pnl_r = pd.to_numeric(val_raw[PNL_COL], errors="coerce").fillna(0.0).astype(float).values

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
    return val_raw, yv, torch.cat(probs).numpy(), pnl_r


def bootstrap_pf_ci(pnl_r: np.ndarray, selected: np.ndarray, n_bootstrap: int = 1000) -> dict | None:
    """Bootstrap PF for selected trades using the shared Stage 09 PF convention."""
    idx_selected = np.flatnonzero(selected)
    if len(idx_selected) < 2:
        return None
    rng = np.random.RandomState(SEED)
    pfs = []
    for _ in range(n_bootstrap):
        sample_idx = rng.choice(idx_selected, len(idx_selected), replace=True)
        sel_mask = np.zeros(len(selected), dtype=bool)
        sel_mask[sample_idx] = True
        r = compute_pf(pnl_r, selected=sel_mask)
        if r["trades"] > 0 and r["PF"] > 0:
            pfs.append(r["PF"])
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
    pnl_r: np.ndarray,
    y_true: np.ndarray,
    proba: np.ndarray,
    selected: np.ndarray,
    family: str,
    value: float,
    threshold_equivalent: float | None = None,
) -> dict:
    selected = selected.astype(bool)
    base = compute_pf(pnl_r, selected=selected)

    years = pd.to_datetime(val_raw["time"], format="%Y.%m.%d %H:%M", errors="coerce").dt.year
    per_year = {}
    negative_years = 0
    active_years = 0
    max_year_trades = 0
    for year in sorted(years.dropna().unique()):
        mask = (years.values == year)
        r = compute_pf(pnl_r[mask], selected=selected[mask])
        per_year[str(int(year))] = r
        max_year_trades = max(max_year_trades, r["trades"])
        if r["trades"] > 0:
            active_years += 1
            if r["PF"] < 1.0:
                negative_years += 1

    trades = base["trades"]
    max_year_trade_share = max_year_trades / trades if trades else 0.0
    bootstrap = bootstrap_pf_ci(pnl_r, selected)

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
    val_raw, y_true, proba, pnl_r = load_validation_proba()
    rows = []

    for threshold in THRESHOLDS:
        rows.append(
            evaluate_selection(
                val_raw,
                pnl_r,
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
                pnl_r,
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

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    # ─── Full stability scan (for audit/reproducibility) ────────────────────────
    scan_output = sanitize_for_json({
        "cycle_id": "methodology_cycle_candidate_source_v2",
        "stage": "09-validation-freeze-stability-refreeze",
        "scope": "validation-only; test not read",
        "canonical_rule": str(FROZEN_RULE_PATH) if eligible else None,
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
    })
    with open(SCAN_PATH, "w") as f:
        json.dump(scan_output, f, indent=2, allow_nan=False)
    print(f"Full scan: {SCAN_PATH}")

    print(f"\nEligible stable rules: {len(eligible)}")
    if not eligible:
        best = by_stability[0]
        print(
            f"No stable rule. Best stability: {best['family']}={best['value']} PF={best['PF']} "
            f"trades={best['trades']} active_years={best['active_years']} "
            f"max_year_share={best['max_year_trade_share']}"
        )
        print("Canonical frozen rule was not written because no rule passed stability gates.")
        return

    # ─── Canonical frozen rule ──────────────────────────────────────────────────

    # Find training-threshold rule (THRESHOLD=0.60) in scan results as superseded.
    superseded = next((r for r in rows if r["family"] == "threshold" and r["value"] == TRAINING_THRESHOLD), None)

    selected = eligible[0]
    canonical_threshold = selected.get("threshold_equivalent", selected["value"])

    frozen_rule = sanitize_for_json({
        "model": "Transformer",
        "checkpoint": str(CHECKPOINT),
        "checkpoint_sha256": file_sha256(str(CHECKPOINT)),
        "normalizer": str(NORMALIZER),
        "normalizer_sha256": file_sha256(str(NORMALIZER)),
        "selection_rule": {
            "type": "validation_calibrated_threshold",
            "threshold": canonical_threshold,
            "calibrated_from": {
                "family": selected["family"],
                "value": selected["value"],
                "source": "stage09_stability_refreeze.json",
            },
            "reason": (
                "Chosen by validation-only stability gates: PF>=1.5, >=6 trades/year, "
                "0 negative years, >=3 active years, max year trade share <=0.60, "
                "bootstrap CI low >=1.0."
            ),
        },
        "threshold": canonical_threshold,
        "seq_len": SEQ_LEN,
        "target": TARGET,
        "n_classes": N_CLASSES,
        "epochs": EPOCHS,
        "val_pf": selected["PF"],
        "val_trades": selected["trades"],
        "val_trades_per_year": selected["trades_per_year"],
        "val_wr": selected["wr"],
        "val_tp": selected["tp"],
        "val_sl": selected["sl"],
        "negative_years": selected["negative_years"],
        "active_years": selected["active_years"],
        "max_year_trade_share": selected["max_year_trade_share"],
        "per_year": selected["per_year"],
        "bootstrap": selected["bootstrap"],
        "stability_gates": {
            "active_years_ge_3": selected["active_years"] >= MIN_ACTIVE_YEARS,
            "max_year_trade_share_le_0_60": selected["max_year_trade_share"] <= MAX_YEAR_TRADE_SHARE,
            "bootstrap_ci_low_ge_1_0": bool(selected["bootstrap"] and selected["bootstrap"]["ci95_low"] >= MIN_BOOTSTRAP_CI_LOW),
        },
    })

    if superseded and superseded != selected:
        frozen_rule["superseded_high_pf_rule"] = {
            "threshold": TRAINING_THRESHOLD,
            "val_pf": superseded["PF"],
            "val_trades": superseded["trades"],
            "negative_years": superseded["negative_years"],
            "max_year_trade_share": superseded["max_year_trade_share"],
            "reason": (
                f"Rejected as canonical frozen rule because "
                f"{superseded['max_year_trade_share']*100:.0f}% of validation trades concentrate "
                f"in max year and active_years={superseded['active_years']} < 4."
            ),
        }

    frozen_rule["environment"] = env_info()
    frozen_rule["overfit_risk"] = (
        f"Stability refreeze reduces concentration versus the high-PF threshold: "
        f"{selected['trades']} trades, all {selected['active_years']} validation years active, "
        f"max year share {selected['max_year_trade_share']:.1%}, "
        f"bootstrap CI low {selected['bootstrap']['ci95_low']:.2f}. "
        f"Still validation-only and research_only until frozen test, robustness, costs, and MT4 parity pass."
    )

    with open(FROZEN_RULE_PATH, "w") as f:
        json.dump(frozen_rule, f, indent=2, allow_nan=False)
    print(f"Canonical frozen rule: {FROZEN_RULE_PATH}")

    print(
        f"Selected: {selected['family']}={selected['value']} thr={canonical_threshold} "
        f"PF={selected['PF']} trades={selected['trades']} "
        f"active_years={selected['active_years']} max_year_share={selected['max_year_trade_share']}"
    )


if __name__ == "__main__":
    main()
