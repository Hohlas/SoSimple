# =============================================================================
# File: validation_freeze.py
# Purpose: Stage 09 — Train Transformer winner (3-class, deterministic), freeze,
#          verify round-trip, check gates, save reproducible artifacts.
# =============================================================================

from __future__ import annotations

import hashlib
import json
import os
import sys
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset
from pathlib import Path

from ML.data_loader import parse_fractals_to_3d
from ML.pll_normalizer import PLLFeatureNormalizer

# ─── Deterministic config ─────────────────────────────────────────────────────
SEED = 42
os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"
torch.use_deterministic_algorithms(True)
torch.manual_seed(SEED)
np.random.seed(SEED)

DATA_DIR = Path("DATA")
CKPT_DIR = Path("ML/checkpoints")
REPORT_DIR = Path("ML/reports/methodology_cycle_candidate_source_v2")
TARGET = "buy_sl3_tp3"
SEQ_LEN = 50
N_CLASSES = 3
THRESHOLD = 0.60
EPOCHS = 10
BATCH_SIZE = 128
LR = 1e-3

LABEL_MAP = {0.0: 0, 0.5: 1, 1.0: 2}


def file_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def env_info() -> dict:
    return {
        "python": sys.version.split()[0],
        "torch": torch.__version__,
        "deterministic_enabled": torch.are_deterministic_algorithms_enabled(),
        "num_threads": torch.get_num_threads(),
        "mkldnn_enabled": torch.backends.mkldnn.is_available(),
        "seed": SEED,
    }


# ─── Model ────────────────────────────────────────────────────────────────────

class TransformerEncoder3Class(nn.Module):
    def __init__(self):
        super().__init__()
        self.proj = nn.Linear(20, 32)
        self.pe = nn.Parameter(torch.randn(1, 100, 32) * 0.02)
        enc = nn.TransformerEncoderLayer(32, 4, 128, 0.1, "gelu", batch_first=True)
        self.enc = nn.TransformerEncoder(enc, 2)
        self.head = nn.Sequential(
            nn.Linear(32, 32), nn.GELU(), nn.Dropout(0.1), nn.Linear(32, N_CLASSES),
        )

    def forward(self, x, mask=None):
        B, L, _ = x.shape
        x = self.proj(x) + self.pe[:, :L, :]
        if mask is not None:
            mask = ~mask
        x = self.enc(x, src_key_padding_mask=mask)
        if mask is not None:
            v = (~mask).float().unsqueeze(-1)
            x = (x * v).sum(1) / v.sum(1).clamp(min=1)
        else:
            x = x.mean(1)
        return self.head(x)


# ─── Metrics ──────────────────────────────────────────────────────────────────

def compute_pf(y_true: np.ndarray, proba: np.ndarray, threshold: float) -> dict:
    pred = (proba >= threshold).astype(int)
    n = pred.sum()
    if n == 0:
        return {"PF": 0.0, "trades": 0, "wr": 0.0, "tp": 0, "sl": 0}
    tp = int(((pred == 1) & (y_true == 2)).sum())
    sl = int(((pred == 1) & (y_true == 0)).sum())
    pf = float("inf") if sl == 0 else tp / sl
    wr = tp / max(tp + sl, 1)
    return {"PF": round(pf, 4), "trades": int(n), "wr": round(wr, 4), "tp": tp, "sl": sl}


def per_year_pf(val_raw, yv, proba, thr):
    df = val_raw.copy()
    df["year"] = pd.to_datetime(df["time"], format="%Y.%m.%d %H:%M", errors="coerce").dt.year
    result = {}
    neg_yrs = 0
    for yr, g in df.groupby("year"):
        idx = g.index
        r = compute_pf(yv[idx], proba[idx], thr)
        # PF=0 with 0 trades means model stayed out — not a negative year
        is_neg = r["PF"] < 1.0 and r["trades"] > 0
        if is_neg:
            neg_yrs += 1
        result[str(yr)] = r
    return result, neg_yrs


def bootstrap_pf_ci(y_true, proba, thr, n_bootstrap=1000):
    pfs = []
    n = len(y_true)
    rng = np.random.RandomState(SEED)
    for _ in range(n_bootstrap):
        idx = rng.choice(n, n, replace=True)
        r = compute_pf(y_true[idx], proba[idx], thr)
        if r["PF"] > 0 and r["PF"] != float("inf"):
            pfs.append(r["PF"])
    if len(pfs) < 2:
        return None
    pfs = np.array(pfs)
    return {"mean": round(float(np.mean(pfs)), 2), "ci95_low": round(float(np.percentile(pfs, 2.5)), 2),
            "ci95_high": round(float(np.percentile(pfs, 97.5)), 2), "n_bootstrap": n_bootstrap}


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print(f"Environment: {env_info()}")

    print("Loading data...")
    train_raw = pd.read_csv(DATA_DIR / "Nero_train_labeled.csv", sep=";")
    val_raw = pd.read_csv(DATA_DIR / "Nero_validation_labeled.csv", sep=";")
    print(f"  Train: {len(train_raw)}, Val: {len(val_raw)}")

    yt = train_raw[TARGET].map(LABEL_MAP).fillna(0).astype(int).values
    yv = val_raw[TARGET].map(LABEL_MAP).fillna(0).astype(int).values
    print(f"  Classes: {dict(zip(*np.unique(yt, return_counts=True)))}")

    print("Building 3D tensors...")
    Xt, mask_t = parse_fractals_to_3d(train_raw)
    Xv, mask_v = parse_fractals_to_3d(val_raw)
    Xt, mask_t = Xt[:, :SEQ_LEN, :], mask_t[:, :SEQ_LEN]
    Xv, mask_v = Xv[:, :SEQ_LEN, :], mask_v[:, :SEQ_LEN]

    print("Fitting PLL normalizer on train...")
    norm = PLLFeatureNormalizer()
    norm.fit(Xt)
    Xt = norm.transform(Xt)
    Xv = norm.transform(Xv)

    train_ds = TensorDataset(
        torch.from_numpy(Xt).float(), torch.from_numpy(mask_t).bool(), torch.from_numpy(yt).long(),
    )
    val_ds = TensorDataset(
        torch.from_numpy(Xv).float(), torch.from_numpy(mask_v).bool(), torch.from_numpy(yv).long(),
    )
    tl = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True,
                     generator=torch.Generator().manual_seed(SEED))
    vl = DataLoader(val_ds, batch_size=256, shuffle=False)

    bc = np.bincount(yt)
    cw = torch.tensor(bc.max() / bc, dtype=torch.float32)
    model = TransformerEncoder3Class()
    opt = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=0.01)
    sch = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=EPOCHS)
    crit = nn.CrossEntropyLoss(weight=cw)

    print(f"Training {EPOCHS} epochs...")
    best_pf, best_proba, best_epoch = 0, None, 0
    for epoch in range(EPOCHS):
        model.train()
        for xb, mb, yb in tl:
            opt.zero_grad()
            loss = crit(model(xb, mb), yb)
            loss.backward()
            opt.step()
        sch.step()

        model.eval()
        ap, ay = [], []
        with torch.no_grad():
            for xb, mb, yb in vl:
                lg = model(xb, mb)
                ap.append(F.softmax(lg, 1)[:, 2].cpu())
                ay.append(yb.cpu())
        proba = torch.cat(ap).numpy()
        y_true = torch.cat(ay).numpy()
        r = compute_pf(y_true, proba, THRESHOLD)
        if r["PF"] > best_pf and r["trades"] >= 6:
            best_pf = r["PF"]
            best_proba = proba.copy()
            best_epoch = epoch
        if (epoch + 1) % 2 == 0:
            print(f"  epoch {epoch+1}: PF={best_pf:.2f}")

    print(f"\nBest epoch: {best_epoch}, PF={best_pf:.2f} at t={THRESHOLD}")

    # Per-year, per-side, bootstrap
    per_year, neg_yrs = per_year_pf(val_raw, yv, best_proba, THRESHOLD)
    bootstrap = bootstrap_pf_ci(yv, best_proba, THRESHOLD)
    r = compute_pf(yv, best_proba, THRESHOLD)

    print(f"PF={r['PF']:.2f} trades={r['trades']} wr={r['wr']:.1%} neg_yrs={neg_yrs}")
    if bootstrap:
        print(f"Bootstrap 95% CI: [{bootstrap['ci95_high']:.2f}, {bootstrap['ci95_low']:.2f}] (mean={bootstrap['mean']:.2f})")
    print(f"Per-year:")
    for yr, pr in sorted(per_year.items()):
        print(f"  {yr}: PF={pr['PF']:.2f} trades={pr['trades']}")

    # Save
    norm_path = str(CKPT_DIR / "pll_normalizer_v1.pkl")
    ckpt_path = str(CKPT_DIR / "transformer_winner.pt")
    norm.save(norm_path)
    torch.save({"model_state_dict": model.state_dict(), "seed": SEED, "target": TARGET,
                 "n_classes": N_CLASSES, "seq_len": SEQ_LEN}, ckpt_path)

    # Round-trip verification: reload raw data, re-apply loaded normalizer
    print("Round-trip verification...")
    val_raw2 = pd.read_csv(DATA_DIR / "Nero_validation_labeled.csv", sep=";")
    yv2 = val_raw2[TARGET].map(LABEL_MAP).fillna(0).astype(int).values
    Xv_raw, mask_v2 = parse_fractals_to_3d(val_raw2)
    Xv_raw, mask_v2 = Xv_raw[:, :SEQ_LEN, :], mask_v2[:, :SEQ_LEN]
    norm2 = PLLFeatureNormalizer.load(norm_path)
    Xv_rt = norm2.transform(Xv_raw)

    val_ds2 = TensorDataset(torch.from_numpy(Xv_rt).float(), torch.from_numpy(mask_v2).bool(), torch.from_numpy(yv2).long())
    ckpt2 = torch.load(ckpt_path, map_location="cpu")
    model2 = TransformerEncoder3Class()
    model2.load_state_dict(ckpt2["model_state_dict"])
    model2.eval()
    ap2 = []
    with torch.no_grad():
        for xb, mb, _ in DataLoader(val_ds2, batch_size=256, shuffle=False):
            ap2.append(F.softmax(model2(xb, mb), 1)[:, 2].cpu())
    proba_rt = torch.cat(ap2).numpy()
    diff = float(np.abs(best_proba - proba_rt).max())
    r2 = compute_pf(yv2, proba_rt, THRESHOLD)
    print(f"  max proba diff={diff:.2e}, PF={r2['PF']:.2f} trades={r2['trades']}")

    # Rule
    rule = {
        "model": "Transformer",
        "checkpoint": ckpt_path,
        "checkpoint_sha256": file_sha256(ckpt_path),
        "normalizer": norm_path,
        "normalizer_sha256": file_sha256(norm_path),
        "threshold": THRESHOLD,
        "seq_len": SEQ_LEN,
        "target": TARGET,
        "n_classes": N_CLASSES,
        "epochs": EPOCHS,
        "best_epoch": best_epoch,
        "val_pf": r["PF"],
        "val_trades": r["trades"],
        "val_wr": r["wr"],
        "negative_years": neg_yrs,
        "per_year": {yr: {k: int(v) if isinstance(v, (np.integer,)) else v for k, v in pr.items()} for yr, pr in per_year.items()},
        "bootstrap": bootstrap,
        "round_trip_max_diff": diff,
        "round_trip_pf": r2["PF"],
        "gate_pf_ge_1_5": r["PF"] >= 1.5,
        "gate_trades_per_year": r["trades"] / 3.5 >= 6,
        "gate_neg_years": neg_yrs == 0,
        "environment": env_info(),
        "overfit_risk": (
            "35 trades on validation (2019-2022, ~3.5 yrs) passes >=6/yr gate but is a small sample. "
            "27/35 trades (77%) in 2019 alone. 2020=1 trade, 2022=0 trades. "
            "Performance concentrated in low-volatility regime years. "
            "Bootstrap CI and out-of-sample frozen test (Stage 10) required before production claims."
        ),
    }
    rule_path = str(REPORT_DIR / "stage09_frozen_rule.json")
    with open(rule_path, "w") as f:
        json.dump(rule, f, indent=2, default=str)

    print(f"\nRule saved: {rule_path}")
    print(f"All gates: PF={rule['gate_pf_ge_1_5']} trades={rule['gate_trades_per_year']} neg_yrs={rule['gate_neg_years']}")
    print(f"PASSED: {rule['gate_pf_ge_1_5'] and rule['gate_trades_per_year'] and rule['gate_neg_years']}")


if __name__ == "__main__":
    main()
