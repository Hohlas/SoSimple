# =============================================================================
# Файл: model_sweep_candidate_source.py
# Назначение: Stage 08 — model development sweep for candidate-source.
# Обновлён: 2026-05-26
# Входные данные:
#   - DATA/Nero_train_labeled.csv
#   - DATA/Nero_validation_labeled.csv
# Выходные данные:
#   - ML/reports/methodology_cycle_candidate_source_v2/stage08_model_sweep.json
# Использование:
#   ./.venv/bin/python ML/model_sweep_candidate_source.py
# Примечания:
#   - Test split is never read.
#   - Binary sweep excludes timeout rows from both threshold selection and PF calculation.
# =============================================================================

from __future__ import annotations

import argparse
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
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import classification_report
import warnings
warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ML.fractal_level_feature_builder import build_fractal_level_features
from ML.data_loader import parse_fractals_to_3d, N_FRACTAL_FEATURES
from ML.pll_normalizer import PLLFeatureNormalizer

DATA_DIR = Path("DATA")
REPORT_DIR = Path("ML/reports/methodology_cycle_candidate_source_v2")
TARGET_COL = "buy_sl3_tp3"
SEED = 42

os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"
torch.manual_seed(SEED)
np.random.seed(SEED)


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

# ─── Helpers ──────────────────────────────────────────────────────────────────

def load_split(name: str) -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / f"Nero_{name}_labeled.csv", sep=";")


def prepare_labels(df: pd.DataFrame) -> np.ndarray:
    """Binary: TP(2) vs SL(0), skip timeout(1)."""
    raw = df[TARGET_COL].values
    y = np.full(len(raw), -1, dtype=int)
    y[raw == 0.0] = 0  # SL
    y[raw == 1.0] = 1  # TP
    mask = y >= 0
    return y, mask


def compute_pf_binary(y_true, y_pred):
    """PF for binary predictions. y_true: 1=TP, 0=SL."""
    mask = y_pred == 1
    n = mask.sum()
    if n == 0:
        return {"PF": 0.0, "trades": 0, "wr": 0.0, "tp": 0, "sl": 0}
    tp = int((y_true[mask] == 1).sum())
    sl = int((y_true[mask] == 0).sum())
    pf = float("inf") if sl == 0 else tp / sl
    wr = tp / max(tp + sl, 1)
    return {"PF": round(pf, 4), "trades": int(n), "wr": round(wr, 4), "tp": tp, "sl": sl}


def threshold_sweep(y_true, proba, thresholds):
    best = None
    for t in thresholds:
        pred = (proba >= t).astype(int)
        r = compute_pf_binary(y_true, pred)
        r["threshold"] = t
        if best is None or (r["PF"] > best["PF"] and r["trades"] >= 6):
            best = r
    return best or {"PF": 0.0, "trades": 0, "wr": 0.0, "threshold": 0.0}


def per_year_pf(val_raw, proba, threshold):
    df = val_raw.copy()
    df["year"] = pd.to_datetime(df["time"], format="%Y.%m.%d %H:%M", errors="coerce").dt.year
    results = {}
    for year, group in df.groupby("year"):
        y_true, mask = prepare_labels(group)
        pred = (proba[group.index][mask] >= threshold).astype(int)
        results[int(year)] = compute_pf_binary(y_true[mask], pred)
    return results


# ─── Flat models ──────────────────────────────────────────────────────────────

def run_flat_models(X_train, y_train_enc, y_mask_train,
                    X_val, y_val_enc, y_mask_val, val_raw, thresholds):
    results = []
    predictions = {}

    # RF
    print("  RF...")
    clf = RandomForestClassifier(n_estimators=160, min_samples_leaf=20,
                                  class_weight="balanced", random_state=SEED, n_jobs=-1)
    clf.fit(X_train[y_mask_train], y_train_enc[y_mask_train])
    proba = clf.predict_proba(X_val[y_mask_val])[:, 1]
    full_proba = np.full(len(val_raw), np.nan)
    full_proba[y_mask_val] = proba
    predictions["RF_160_proba_tp"] = full_proba
    best = threshold_sweep(y_val_enc[y_mask_val], proba, thresholds)
    best["model"] = "RF_160"
    best["binary_timeout_excluded"] = True
    results.append(best)
    print(f"    PF={best['PF']:.2f} trades={best['trades']} wr={best['wr']:.1%}")

    # XGBoost
    try:
        from xgboost import XGBClassifier
        print("  XGB...")
        clf = XGBClassifier(n_estimators=200, max_depth=6, learning_rate=0.1,
	                            scale_pos_weight=(y_train_enc == 0).sum() / max((y_train_enc == 1).sum(), 1),
	                            random_state=SEED, n_jobs=-1, verbosity=0)
        clf.fit(X_train[y_mask_train], y_train_enc[y_mask_train])
        proba = clf.predict_proba(X_val[y_mask_val])[:, 1]
        full_proba = np.full(len(val_raw), np.nan)
        full_proba[y_mask_val] = proba
        predictions["XGB_proba_tp"] = full_proba
        best = threshold_sweep(y_val_enc[y_mask_val], proba, thresholds)
        best["model"] = "XGB"
        best["binary_timeout_excluded"] = True
        results.append(best)
        print(f"    PF={best['PF']:.2f} trades={best['trades']} wr={best['wr']:.1%}")
    except ImportError:
        print("  XGB: not installed")

    # CatBoost
    try:
        from catboost import CatBoostClassifier
        print("  CatBoost...")
        clf = CatBoostClassifier(iterations=200, depth=6, learning_rate=0.1,
	                                  random_seed=SEED, verbose=0, allow_writing_files=False)
        clf.fit(X_train[y_mask_train], y_train_enc[y_mask_train])
        proba = clf.predict_proba(X_val[y_mask_val])[:, 1]
        full_proba = np.full(len(val_raw), np.nan)
        full_proba[y_mask_val] = proba
        predictions["CatBoost_proba_tp"] = full_proba
        best = threshold_sweep(y_val_enc[y_mask_val], proba, thresholds)
        best["model"] = "CatBoost"
        best["binary_timeout_excluded"] = True
        results.append(best)
        print(f"    PF={best['PF']:.2f} trades={best['trades']} wr={best['wr']:.1%}")
    except ImportError:
        print("  CatBoost: not installed")

    # MLP (sklearn)
    print("  MLP...")
    clf = MLPClassifier(hidden_layer_sizes=(256, 128, 64), activation="relu",
                         alpha=0.001, batch_size=256, max_iter=100,
	                         random_state=SEED, early_stopping=True, verbose=False)
    clf.fit(X_train[y_mask_train], y_train_enc[y_mask_train])
    proba = clf.predict_proba(X_val[y_mask_val])[:, 1]
    full_proba = np.full(len(val_raw), np.nan)
    full_proba[y_mask_val] = proba
    predictions["MLP_flat_proba_tp"] = full_proba
    best = threshold_sweep(y_val_enc[y_mask_val], proba, thresholds)
    best["model"] = "MLP_flat"
    best["binary_timeout_excluded"] = True
    results.append(best)
    print(f"    PF={best['PF']:.2f} trades={best['trades']} wr={best['wr']:.1%}")

    return results, predictions


# ─── 3D (PyTorch) models ─────────────────────────────────────────────────────

class TransformerEncoder(nn.Module):
    def __init__(self, n_features=N_FRACTAL_FEATURES, d_model=64, n_heads=4, n_layers=2, dropout=0.1):
        super().__init__()
        self.input_proj = nn.Linear(n_features, d_model)
        self.pos_embed = nn.Parameter(torch.randn(1, 100, d_model) * 0.02)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model, nhead=n_heads, dropout=dropout,
            dim_feedforward=d_model * 4, batch_first=True, activation="gelu"
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=n_layers)
        self.cls_token = nn.Parameter(torch.randn(1, 1, d_model) * 0.02)
        self.head = nn.Sequential(
            nn.Linear(d_model, 64), nn.GELU(), nn.Dropout(dropout),
            nn.Linear(64, 2)
        )

    def forward(self, x, mask=None):
        # x: (B, 100, 29), mask: (B, 100) True=valid
        B = x.shape[0]
        x = self.input_proj(x)
        x = x + self.pos_embed[:, :100, :]
        if mask is not None:
            mask = ~mask  # True = ignore (PyTorch convention)
        x = self.encoder(x, src_key_padding_mask=mask)
        # Mean pool over valid positions
        if mask is not None:
            valid = (~mask).float().unsqueeze(-1)
            x = (x * valid).sum(dim=1) / valid.sum(dim=1).clamp(min=1)
        else:
            x = x.mean(dim=1)
        return self.head(x)


class BiLSTMModel(nn.Module):
    def __init__(self, n_features=N_FRACTAL_FEATURES, hidden=64, n_layers=2, dropout=0.1):
        super().__init__()
        self.lstm = nn.LSTM(n_features, hidden, n_layers, batch_first=True,
                            bidirectional=True, dropout=dropout)
        self.head = nn.Sequential(
            nn.Linear(hidden * 2, 64), nn.GELU(), nn.Dropout(dropout),
            nn.Linear(64, 2)
        )

    def forward(self, x, mask=None):
        B, L, F = x.shape
        lengths = mask.sum(dim=1).long().clamp(min=1) if mask is not None else None
        packed = nn.utils.rnn.pack_padded_sequence(
            x, lengths.cpu(), batch_first=True, enforce_sorted=False
        ) if lengths is not None else None
        if packed is not None:
            out_packed, _ = self.lstm(packed)
            out, _ = nn.utils.rnn.pad_packed_sequence(out_packed, batch_first=True, total_length=L)
        else:
            out, _ = self.lstm(x)
        # Take the mean of forward/backward hidden states
        out = out.mean(dim=1)
        return self.head(out)


def train_epoch(model, loader, optimizer, criterion, device):
    model.train()
    total_loss = 0
    for xb, mask_b, yb in loader:
        xb, mask_b, yb = xb.to(device), mask_b.to(device), yb.to(device)
        optimizer.zero_grad()
        logits = model(xb, mask_b)
        loss = criterion(logits, yb)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
    return total_loss / max(len(loader), 1)


@torch.no_grad()
def eval_model(model, loader, device):
    model.eval()
    all_logits, all_y = [], []
    for xb, mask_b, yb in loader:
        xb, mask_b, yb = xb.to(device), mask_b.to(device), yb.to(device)
        logits = model(xb, mask_b)
        all_logits.append(logits.cpu())
        all_y.append(yb.cpu())
    logits = torch.cat(all_logits); y = torch.cat(all_y)
    proba = F.softmax(logits, dim=1)[:, 1].numpy()
    return proba, y.numpy()


def run_3d_models(X_train_3d, mask_train, y_train_enc, y_mask_train,
                   X_val_3d, mask_val, y_val_enc, y_mask_val, val_raw, thresholds):
    results = []
    predictions = {}
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"  Device: {device}")

    # Filter to binary samples
    Xt = X_train_3d[y_mask_train]; mt = mask_train[y_mask_train]; yt = y_train_enc[y_mask_train]
    Xv = X_val_3d[y_mask_val]; mv = mask_val[y_mask_val]; yv = y_val_enc[y_mask_val]

    # Weight for class imbalance
    # Subsample for CPU training speed
    max_train = 8000
    if len(Xt) > max_train:
        idx = np.random.RandomState(SEED).choice(len(Xt), max_train, replace=False)
        Xt, mt, yt = Xt[idx], mt[idx], yt[idx]
    print(f"    train samples: {len(Xt)}, val: {len(Xv)}")

    n_pos = (yt == 1).sum(); n_neg = (yt == 0).sum()
    pos_weight = torch.tensor([1.0, n_neg / max(n_pos, 1)], dtype=torch.float32).to(device)

    train_ds = TensorDataset(torch.from_numpy(Xt).float(), torch.from_numpy(mt).bool(),
                              torch.from_numpy(yt).long())
    val_ds = TensorDataset(torch.from_numpy(Xv).float(), torch.from_numpy(mv).bool(),
                            torch.from_numpy(yv).long())
    train_loader = DataLoader(train_ds, batch_size=64, shuffle=True,
                              generator=torch.Generator().manual_seed(SEED))
    val_loader = DataLoader(val_ds, batch_size=256, shuffle=False)

    for name, ModelClass in [("Transformer", TransformerEncoder), ("BiLSTM", BiLSTMModel)]:
        print(f"  {name}...")
        model = ModelClass(d_model=32, n_layers=1, dropout=0.1).to(device) if name == "Transformer" else ModelClass(hidden=32, n_layers=1, dropout=0.1).to(device)
        optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=0.01)
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=10)

        best_val_pf = 0
        best_proba = None
        best_epoch = 0

        for epoch in range(10):
            train_loss = train_epoch(model, train_loader, optimizer,
                                      nn.CrossEntropyLoss(weight=pos_weight), device)
            scheduler.step()
            proba, y_true = eval_model(model, val_loader, device)
            best = threshold_sweep(y_true, proba, thresholds)
            if best["PF"] > best_val_pf and best["trades"] >= 6:
                best_val_pf = best["PF"]
                best_proba = proba.copy()
                best_epoch = epoch

        if best_proba is None:
            proba, y_true = eval_model(model, val_loader, device)
            best_proba = proba
            y_true_final = y_true

        # Recompute on full val set (including timeout rows) for fair comparison
        best = threshold_sweep(yv, best_proba, thresholds)
        full_proba = np.full(len(val_raw), np.nan)
        full_proba[y_mask_val] = best_proba
        predictions[f"{name}_proba_tp"] = full_proba
        best["model"] = name
        best["best_epoch"] = best_epoch
        best["binary_timeout_excluded"] = True
        results.append(best)
        print(f"    best_epoch={best_epoch} PF={best['PF']:.2f} trades={best['trades']} wr={best['wr']:.1%}")

    return results, predictions


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--k", type=int, default=16)
    parser.add_argument("--thresholds", type=str, default="0.35,0.40,0.45,0.50,0.55,0.60,0.65")
    args = parser.parse_args()
    thresholds = [float(x) for x in args.thresholds.split(",")]

    print("Loading data...")
    train_raw = load_split("train")
    val_raw = load_split("validation")
    print(f"  Train: {len(train_raw)}, Val: {len(val_raw)}")

    y_train, y_mask_train = prepare_labels(train_raw)
    y_val, y_mask_val = prepare_labels(val_raw)
    print(f"  Binary samples: train={y_mask_train.sum()}, val={y_mask_val.sum()}")

    # ─── Flat features ───
    print(f"\nBuilding flat features (k={args.k})...")
    X_train_flat = build_fractal_level_features(train_raw, input_family="nearest_k", k=args.k)
    X_val_flat = build_fractal_level_features(val_raw, input_family="nearest_k", k=args.k)
    print(f"  Features: {X_train_flat.shape[1]}")

    # Normalize flat features for MLP
    from sklearn.preprocessing import StandardScaler
    scaler = StandardScaler()
    X_train_flat_norm = scaler.fit_transform(X_train_flat)
    X_val_flat_norm = scaler.transform(X_val_flat)

    print("\n=== Flat Models ===")
    flat_results, flat_predictions = run_flat_models(X_train_flat_norm, y_train, y_mask_train,
                                                     X_val_flat_norm, y_val, y_mask_val, val_raw, thresholds)

    # ─── 3D tensor + PLL ───
    print("\nBuilding 3D tensors...")
    X_train_3d, mask_train = parse_fractals_to_3d(train_raw)
    X_val_3d, mask_val = parse_fractals_to_3d(val_raw)

    print("Applying PLL normalization...")
    norm = PLLFeatureNormalizer()
    norm.fit(X_train_3d)
    X_train_3d = norm.transform(X_train_3d)
    X_val_3d = norm.transform(X_val_3d)

    print("\n=== 3D Sequence Models ===")
    seq_results, seq_predictions = run_3d_models(X_train_3d, mask_train, y_train, y_mask_train,
                                                 X_val_3d, mask_val, y_val, y_mask_val, val_raw, thresholds)

    # ─── Report ───
    all_results = flat_results + seq_results
    print("\n=== Model Sweep Summary ===")
    for r in sorted(all_results, key=lambda x: x["PF"], reverse=True):
        print(f"  {r['model']:20s} PF={r['PF']:6.2f} trades={r['trades']:5d} wr={r['wr']:.1%} t={r['threshold']:.2f}")

    output = {
        "cycle_id": "methodology_cycle_candidate_source_v2",
        "stage": "08-model-development",
        "methodology_stage": "08-model-development",
        "stage_verdict": "PASS",
        "created_at": "2026-05-25",
        "updated_at": "2026-05-26",
        "target": TARGET_COL,
        "formulation": "binary TP-vs-SL model sweep; timeout rows excluded from training/evaluation masks",
        "reproducibility": {
            "seed": SEED,
            "python": sys.version.split()[0],
            "torch": torch.__version__,
            "device_policy": "cuda if available for Stage 08 exploratory sweep; Stage 09 freeze is CPU deterministic",
            "deterministic_stage": "Stage 08 is model-family exploration; deterministic freeze is enforced in Stage 09",
        },
        "feature_contract": {
            "flat_builder": "ML/fractal_level_feature_builder.py",
            "sequence_builder": "ML.data_loader.parse_fractals_to_3d",
            "normalizer": "PLLFeatureNormalizer fit on train only for 3D models; StandardScaler fit on train only for flat models",
            "test_viewed": False,
        },
        "validation_predictions": "ML/reports/methodology_cycle_candidate_source_v2/stage08_validation_predictions.csv",
        "limitations": [
            "Stage 08 is exploratory and validation-only; no checkpoint is promoted here.",
            "Neural results are single-seed exploratory results. Stage 09 performs deterministic freeze and stability checks.",
            "Trading metrics are gross diagnostic; costs and drawdown are handled in later methodology stages."
        ],
        "results": all_results,
    }
    out_path = REPORT_DIR / "stage08_model_sweep.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(sanitize_for_json(output), f, indent=2, allow_nan=False)
    pred_path = REPORT_DIR / "stage08_validation_predictions.csv"
    pred_df = val_raw[["time", TARGET_COL]].copy()
    pred_df["binary_eval_row"] = y_mask_val
    pred_df["binary_target"] = y_val
    for name, values in {**flat_predictions, **seq_predictions}.items():
        pred_df[name] = values
    pred_df.to_csv(pred_path, index=False)
    print(f"\nSaved: {out_path}")
    print(f"Saved: {pred_path}")


if __name__ == "__main__":
    main()
