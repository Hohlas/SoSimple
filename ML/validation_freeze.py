# =============================================================================
# File: validation_freeze.py
# Purpose: Stage 09 — Train Transformer winner (3-class, deterministic), save
#          checkpoint + normalizer, verify round-trip. Does NOT generate the
#          canonical frozen rule — that is stage09_stability_refreeze.py's job.
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
PNL_COL = "buy_sl3_tp3_pnl_r"
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

def sanitize_for_json(obj):
    """Recursively replace inf/-inf with 'inf' string, nan with null for strict JSON."""
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize_for_json(v) for v in obj]
    if isinstance(obj, float):
        if obj == float("inf"):
            return "inf"
        if obj == float("-inf"):
            return "-inf"
        if obj != obj:  # NaN
            return None
    return obj


def compute_pf(pnl_r: np.ndarray, proba: np.ndarray | None = None,
               threshold: float | None = None, selected: np.ndarray | None = None) -> dict:
    if selected is not None:
        pred = selected.astype(int)
    elif proba is not None and threshold is not None:
        pred = (proba >= threshold).astype(int)
    else:
        raise ValueError("Either (proba, threshold) or selected must be provided")
    n = pred.sum()
    if n == 0:
        return {"PF": 0.0, "trades": 0, "wr": 0.0, "tp": 0, "sl": 0, "timeout": 0,
                "gross_profit_r": 0.0, "gross_loss_r": 0.0}
    sel = pnl_r[pred == 1]
    pos = sel[sel > 0]
    neg = sel[sel < 0]
    gross_profit = float(pos.sum())
    gross_loss = float(abs(neg.sum()))
    pf = 99.0 if gross_loss == 0 else gross_profit / gross_loss
    tp = int(len(pos))
    sl = int(len(neg))
    timeout = int(n) - tp - sl
    wr = tp / max(tp + sl, 1) if tp + sl > 0 else 0.0
    return {"PF": round(float(pf), 4), "trades": int(n), "wr": round(float(wr), 4),
            "tp": tp, "sl": sl, "timeout": timeout,
            "gross_profit_r": round(gross_profit, 4),
            "gross_loss_r": round(gross_loss, 4)}


def per_year_pf(val_raw, pnl_r, proba, thr):
    df = val_raw.copy()
    df["year"] = pd.to_datetime(df["time"], format="%Y.%m.%d %H:%M", errors="coerce").dt.year
    result = {}
    neg_yrs = 0
    for yr, g in df.groupby("year"):
        idx = g.index
        r = compute_pf(pnl_r[idx], proba[idx], thr)
        is_neg = r["PF"] < 1.0 and r["trades"] > 0
        if is_neg:
            neg_yrs += 1
        result[str(yr)] = r
    return result, neg_yrs


def bootstrap_pf_ci(pnl_r, proba, thr, n_bootstrap=1000):
    pfs = []
    n = len(pnl_r)
    rng = np.random.RandomState(SEED)
    for _ in range(n_bootstrap):
        idx = rng.choice(n, n, replace=True)
        r = compute_pf(pnl_r[idx], proba[idx], thr)
        if 0 < r["PF"] < 99.0:
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
    pnl_val = pd.to_numeric(val_raw[PNL_COL], errors="coerce").fillna(0.0).astype(float).values
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
    best_pf, best_state_dict, best_proba, best_epoch = 0, None, None, 0
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
        r = compute_pf(pnl_val, proba, THRESHOLD)
        if r["PF"] > best_pf and r["trades"] >= 6:
            best_pf = r["PF"]
            best_proba = proba.copy()
            best_state_dict = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            best_epoch = epoch
        if (epoch + 1) % 2 == 0:
            print(f"  epoch {epoch+1}: PF={best_pf:.2f}")

    print(f"\nBest epoch: {best_epoch}, PF={best_pf:.2f} at t={THRESHOLD}")

    # ─── Save checkpoint & normalizer ────────────────────────────────────────────
    norm_path = str(CKPT_DIR / "pll_normalizer_v1.pkl")
    ckpt_path = str(CKPT_DIR / "transformer_winner.pt")
    norm.save(norm_path)
    torch.save({"model_state_dict": best_state_dict, "seed": SEED, "target": TARGET,
                 "n_classes": N_CLASSES, "seq_len": SEQ_LEN}, ckpt_path)

    # ─── Round-trip verification ─────────────────────────────────────────────────
    print("Round-trip verification...")
    val_raw2 = pd.read_csv(DATA_DIR / "Nero_validation_labeled.csv", sep=";")
    yv2 = val_raw2[TARGET].map(LABEL_MAP).fillna(0).astype(int).values
    pnl_val2 = pd.to_numeric(val_raw2[PNL_COL], errors="coerce").fillna(0.0).astype(float).values
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
    r2 = compute_pf(pnl_val2, proba_rt, THRESHOLD)
    print(f"  max proba diff={diff:.2e}, PF={r2['PF']:.2f} trades={r2['trades']}")

    # ─── Summary ──────────────────────────────────────────────────────────────────
    # Canonical frozen rule is generated by stage09_stability_refreeze.py
    # after the checkpoint is saved. The diagnostics below are training-time
    # metrics at THRESHOLD={THRESHOLD} — they are NOT the canonical rule.

    high_pf = compute_pf(pnl_val, best_proba, THRESHOLD)
    high_per_year, high_neg = per_year_pf(val_raw, pnl_val, best_proba, THRESHOLD)
    high_bootstrap = bootstrap_pf_ci(pnl_val, best_proba, THRESHOLD)

    print(f"\nTraining threshold diagnostics (t={THRESHOLD}):")
    print(f"  PF={high_pf['PF']} trades={high_pf['trades']} wr={high_pf['wr']:.1%} neg_yrs={high_neg}")
    if high_bootstrap:
        print(f"  Bootstrap 95% CI: [{high_bootstrap['ci95_low']}, {high_bootstrap['ci95_high']}] mean={high_bootstrap['mean']}")
    per_year_str = ", ".join(f"{yr}:{v['PF']:.1f}" for yr, v in sorted(high_per_year.items()))
    print(f"  Per-year: {per_year_str}")
    print(f"  Round-trip max proba diff={diff:.2e}")
    print(f"\nCheckpoint saved: {ckpt_path}")
    print(f"Normalizer saved: {norm_path}")
    print(f"\n>>> Run stage09_stability_refreeze.py to generate canonical frozen rule <<<")
    print(f"    source .venv/bin/activate && python ML/stage09_stability_refreeze.py")


if __name__ == "__main__":
    main()
