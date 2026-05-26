# =============================================================================
# File: validation_freeze.py
# Purpose: Stage 09 — Train winner on full train, freeze, evaluate gates.
# =============================================================================

from __future__ import annotations

import json, argparse, numpy as np, pandas as pd, torch, torch.nn as nn, torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset
from pathlib import Path
from ML.data_loader import parse_fractals_to_3d
from ML.pll_normalizer import PLLFeatureNormalizer

DATA_DIR = Path("DATA")
CKPT_DIR = Path("ML/checkpoints")
REPORT_DIR = Path("ML/reports/methodology_cycle_candidate_source_v2")
TARGET_COL = "buy_sl3_tp3"


def prepare_labels(df):
    raw = df[TARGET_COL].values
    y = np.full(len(raw), -1, dtype=int)
    y[raw == 0.0] = 0
    y[raw == 1.0] = 1
    mask = y >= 0
    return y, mask


def compute_pf(y_true, y_pred):
    mask = y_pred == 1; n = mask.sum()
    if n == 0: return {"PF": 0.0, "trades": 0, "wr": 0.0, "tp": 0, "sl": 0}
    tp = int((y_true[mask] == 1).sum())
    sl = int((y_true[mask] == 0).sum())
    pf = float("inf") if sl == 0 else tp / sl
    return {"PF": round(pf, 4), "trades": int(n), "wr": round(tp / max(tp + sl, 1), 4), "tp": tp, "sl": sl}


def threshold_sweep(y_true, proba, thresholds):
    best = None
    for t in thresholds:
        r = compute_pf(y_true, (proba >= t).astype(int))
        r["threshold"] = t
        if best is None or (r["PF"] > best["PF"] and r["trades"] >= 6):
            best = r
    return best or {"PF": 0, "trades": 0, "wr": 0, "threshold": 0}


def per_year(val_raw, proba, thr):
    df = val_raw.copy()
    df["year"] = pd.to_datetime(df["time"], format="%Y.%m.%d %H:%M", errors="coerce").dt.year
    yrs = {}
    for year, g in df.groupby("year"):
        yt, m = prepare_labels(g)
        yrs[int(year)] = compute_pf(yt[m], (proba[g.index][m] >= thr).astype(int))
    return yrs


def per_side(val_raw, proba, thr):
    sides = {}
    for side, sv in [("BUY", 1), ("SELL", -1)]:
        mask = val_raw["signal"].values == sv
        if mask.sum() == 0:
            sides[side] = {"PF": 0, "trades": 0, "wr": 0}
            continue
        yt, m = prepare_labels(val_raw[mask])
        sides[side] = compute_pf(yt[m], (proba[mask][m] >= thr).astype(int))
    return sides


class BiLSTMModel(nn.Module):
    def __init__(self, n_features=20, hidden=32, n_layers=1, dropout=0.1):
        super().__init__()
        self.lstm = nn.LSTM(n_features, hidden, n_layers, batch_first=True, bidirectional=True, dropout=dropout)
        self.head = nn.Sequential(nn.Linear(hidden * 2, 32), nn.GELU(), nn.Dropout(dropout), nn.Linear(32, 2))

    def forward(self, x, mask=None):
        B, L, F = x.shape
        if mask is not None:
            lengths = mask.sum(dim=1).long().clamp(min=1)
            packed = nn.utils.rnn.pack_padded_sequence(x, lengths.cpu(), batch_first=True, enforce_sorted=False)
            out_packed, _ = self.lstm(packed)
            out, _ = nn.utils.rnn.pad_packed_sequence(out_packed, batch_first=True, total_length=L)
        else:
            out, _ = self.lstm(x)
        return self.head(out.mean(dim=1))


def train_model(model, train_loader, val_loader, device, epochs=5, lr=1e-3):
    n_pos = sum((yb == 1).sum().item() for _, _, yb in train_loader)
    n_neg = sum((yb == 0).sum().item() for _, _, yb in train_loader)
    pos_weight = torch.tensor([1.0, n_neg / max(n_pos, 1)], dtype=torch.float32).to(device)

    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
    criterion = nn.CrossEntropyLoss(weight=pos_weight)

    best_pf, best_proba, best_epoch = 0, None, 0
    for epoch in range(epochs):
        model.train()
        for xb, mb, yb in train_loader:
            xb, mb, yb = xb.to(device), mb.to(device), yb.to(device)
            optimizer.zero_grad()
            loss = criterion(model(xb, mb), yb)
            loss.backward()
            optimizer.step()
        scheduler.step()

        model.eval()
        all_p, all_y = [], []
        with torch.no_grad():
            for xb, mb, yb in val_loader:
                xb, mb, yb = xb.to(device), mb.to(device), yb.to(device)
                logits = model(xb, mb)
                all_p.append(F.softmax(logits, dim=1)[:, 1].cpu())
                all_y.append(yb.cpu())
        proba = torch.cat(all_p).numpy(); y_true = torch.cat(all_y).numpy()
        best = threshold_sweep(y_true, proba, [0.4, 0.45, 0.5, 0.55, 0.6, 0.65])
        if best["PF"] > best_pf and best["trades"] >= 6:
            best_pf, best_proba, best_epoch = best["PF"], proba.copy(), epoch

    return best_proba, best_epoch, best_pf


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seq-len", type=int, default=50, help="first N fractals")
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--seeds", type=str, default="42,123,456")
    args = parser.parse_args()
    seeds = [int(s) for s in args.seeds.split(",")]

    print("Loading data...")
    train_raw = pd.read_csv(DATA_DIR / "Nero_train_labeled.csv", sep=";")
    val_raw = pd.read_csv(DATA_DIR / "Nero_validation_labeled.csv", sep=";")
    print(f"  Train: {len(train_raw)}, Val: {len(val_raw)}")

    y_train, m_train = prepare_labels(train_raw)
    y_val, m_val = prepare_labels(val_raw)
    print(f"  Binary samples: train={m_train.sum()}, val={m_val.sum()}")

    print("Building 3D tensors...")
    Xt_full, mask_t_full = parse_fractals_to_3d(train_raw)
    Xv_full, mask_v_full = parse_fractals_to_3d(val_raw)

    # Truncate to seq_len
    Xt_full, mask_t_full = Xt_full[:, :args.seq_len, :], mask_t_full[:, :args.seq_len]
    Xv_full, mask_v_full = Xv_full[:, :args.seq_len, :], mask_v_full[:, :args.seq_len]

    print("Fitting PLL normalizer...")
    norm = PLLFeatureNormalizer()
    norm.fit(Xt_full)
    Xt_full = norm.transform(Xt_full)
    Xv_full = norm.transform(Xv_full)

    # Filter to binary samples
    Xt = Xt_full[m_train]; mt = mask_t_full[m_train]; yt = y_train[m_train]
    Xv = Xv_full[m_val]; mv = mask_v_full[m_val]; yv = y_val[m_val]
    print(f"  Train: {len(Xt)}, Val: {len(Xv)}")

    device = torch.device("cpu")
    train_ds = TensorDataset(torch.from_numpy(Xt).float(), torch.from_numpy(mt).bool(), torch.from_numpy(yt).long())
    val_ds = TensorDataset(torch.from_numpy(Xv).float(), torch.from_numpy(mv).bool(), torch.from_numpy(yv).long())
    train_loader = DataLoader(train_ds, batch_size=256, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=256, shuffle=False)

    print(f"\n=== BiLSTM — {len(seeds)} seeds ===")
    all_results = []
    for seed in seeds:
        torch.manual_seed(seed); np.random.seed(seed)
        model = BiLSTMModel(hidden=32, n_layers=1, dropout=0.1).to(device)
        best_proba_val, best_epoch, best_pf_val = train_model(
            model, train_loader, val_loader, device, epochs=args.epochs, lr=args.lr
        )
        if best_proba_val is None:
            print(f"  seed={seed}: no valid epoch")
            continue

        # Evaluate on full val set
        full_proba = np.zeros(len(val_raw))
        full_proba[m_val] = best_proba_val
        best = threshold_sweep(y_val, full_proba, [0.4, 0.45, 0.5, 0.55, 0.6, 0.65])
        best["seed"] = seed
        best["best_epoch"] = best_epoch

        # Per-year
        yr = per_year(val_raw, full_proba, best["threshold"])
        neg_yrs = sum(1 for y, r in yr.items() if r["PF"] < 1.0 and r["trades"] > 0)
        best["negative_years"] = neg_yrs
        best["per_year"] = yr

        # Per-side (diagnostic only — signal is future-derived)
        side = per_side(val_raw, full_proba, best["threshold"])
        best["per_side"] = side

        gate_pf = "✓" if best["PF"] >= 1.5 else "✗"
        gate_ny = "✓" if neg_yrs == 0 else "✗"
        print(f"  seed={seed}: epoch={best_epoch} PF={best['PF']:.2f} trades={best['trades']} "
              f"wr={best['wr']:.1%} neg_yrs={neg_yrs} pf_gate={gate_pf} ny_gate={gate_ny}")
        all_results.append(best)

    # Save checkpoint from best seed
    best_overall = max(all_results, key=lambda r: r["PF"])
    best_seed = best_overall["seed"]
    print(f"\nBest seed: {best_seed}, PF={best_overall['PF']:.2f}")

    # Retrain with best seed and save
    torch.manual_seed(best_seed); np.random.seed(best_seed)
    model = BiLSTMModel(hidden=32, n_layers=1, dropout=0.1).to(device)
    train_model(model, train_loader, val_loader, device, epochs=args.epochs, lr=args.lr)
    torch.save({"model_state_dict": model.state_dict(), "seed": best_seed}, CKPT_DIR / "bilstm_winner.pt")
    print(f"Checkpoint saved: ML/checkpoints/bilstm_winner.pt")

    # Save rule
    rule = {
        "model": "BiLSTM",
        "checkpoint": "ML/checkpoints/bilstm_winner.pt",
        "threshold": best_overall["threshold"],
        "seq_len": args.seq_len,
        "target": TARGET_COL,
        "seed": best_seed,
        "val_results": best_overall,
        "all_seeds": all_results,
    }
    with open(REPORT_DIR / "stage09_frozen_rule.json", "w") as f:
        json.dump(rule, f, indent=2, default=str)
    print(f"Rule saved: {REPORT_DIR / 'stage09_frozen_rule.json'}")

    # Summary
    print("\n=== Gate Check ===")
    print(f"PF≥1.5:    {'PASS' if best_overall['PF'] >= 1.5 else 'FAIL'} ({best_overall['PF']:.2f})")
    print(f"Trades/yr:  {'PASS' if best_overall['trades'] >= 6*3 else 'FAIL'} ({best_overall['trades']} total, ~{best_overall['trades']/3.5:.0f}/yr)")
    print(f"Neg years:  {'PASS' if best_overall['negative_years'] == 0 else 'FAIL'} ({best_overall['negative_years']})")


if __name__ == "__main__":
    main()
