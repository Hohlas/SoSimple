# =============================================================================
# File: transformer_direction_train.py
# Purpose: DataLoader + targets + fine-tune Transformer on direction
# Created: 2026-05-21
# =============================================================================

import argparse
import csv
import json
import os
import pickle
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

from ML.data_loader import parse_fractals_to_3d
from ML.entry_path_direct_direction_targets import build_target_d_masks
from ML.models.transformer import TransformerClassifier

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "DATA"
OHLC_PATH = DATA_DIR / "XAUUSD_H1_OHLC.csv"
RAW_FEATURES_PATH = DATA_DIR / "raw_features_for_direction.pkl"
CHECKPOINT_PATH = PROJECT_ROOT / "ML" / "checkpoints" / "transformer_updn_best.pt"
REPORTS_DIR = PROJECT_ROOT / "ML" / "reports" / "transformer_direction"
CHECKPOINTS_DIR = PROJECT_ROOT / "ML" / "checkpoints"

LABELED_PATHS = {
    "train": DATA_DIR / "Nero_XAUUSD_train_labeled.csv",
    "validation": DATA_DIR / "Nero_XAUUSD_validation_labeled.csv",
    "test": DATA_DIR / "Nero_XAUUSD_test_labeled.csv",
}

HORIZONS = (6, 12, 24)
TRAIL_HORIZONS = (12, 24, 48)
REG_HORIZONS = (6, 12)
SEQ_LEN = 20

ENC_D_MODEL = 32
ENC_NHEAD = 8
ENC_NUM_LAYERS = 3
ENC_DIM_FF = 128
ENC_DROPOUT = 0.166

# ===========================================================================
# DATA LOADING
# ===========================================================================

def load_raw_targets() -> tuple:
    with open(RAW_FEATURES_PATH, "rb") as f:
        df = pickle.load(f)
    atr = df["raw_ATR"].values.astype(np.float64)
    return df, atr


def load_feature_tensors() -> dict:
    result = {}
    for split_name, path in LABELED_PATHS.items():
        print(f"  Parsing {split_name}: {path.name} ...")
        df = pd.read_csv(path, sep=";")
        X, mask = parse_fractals_to_3d(df)
        X = X[:, :SEQ_LEN, :]
        mask = mask[:, :SEQ_LEN]
        result[split_name] = (X, mask)
        print(f"    X={X.shape}, mask={mask.shape}")
    return result


def get_split_mask(df_raw, split):
    return (df_raw["split"] == split).values


def get_raw_updn(df_raw, split, horizon):
    mask = get_split_mask(df_raw, split)
    up_col = f"f0_up_{horizon}_raw"
    dn_col = f"f0_dn_{horizon}_raw"
    up = df_raw.loc[mask, up_col].values.astype(np.float64)
    dn = df_raw.loc[mask, dn_col].values.astype(np.float64)
    atr = df_raw.loc[mask, "raw_ATR"].values.astype(np.float64)
    return up, dn, atr


def get_row_time_strings(df_raw, split):
    mask = get_split_mask(df_raw, split)
    return df_raw.loc[mask, "time"].values


# ===========================================================================
# TARGET CONSTRUCTORS
# ===========================================================================

def build_tb_targets(up_raw, dn_raw, atr, tp_level, sl_level):
    safe_atr = np.where(atr > 0, atr, np.nan)
    up_atr = up_raw / safe_atr
    dn_atr = dn_raw / safe_atr
    buy = ((up_atr >= tp_level) & (dn_atr < sl_level)).astype(np.int64)
    sell = ((dn_atr >= tp_level) & (up_atr < sl_level)).astype(np.int64)
    buy[np.isnan(up_atr)] = 0
    sell[np.isnan(up_atr)] = 0
    return buy, sell


def build_reg_targets(up_raw, dn_raw, atr):
    safe_atr = np.where(atr > 0, atr, np.nan)
    up_atr = up_raw / safe_atr
    dn_atr = dn_raw / safe_atr
    return up_atr.astype(np.float32), dn_atr.astype(np.float32)


def build_trail_targets(df_raw, split, ohlc_path, trail_n, profit_z, horizon):
    mask = get_split_mask(df_raw, split)
    n = mask.sum()
    source = pd.DataFrame({
        "time": df_raw.loc[mask, "time"].values,
        "ATR": df_raw.loc[mask, "raw_ATR"].values,
    }, index=np.arange(n))
    buy_mask, sell_mask = build_target_d_masks(
        source, ohlc_path, trail_n=trail_n, profit_z=profit_z, horizon=horizon
    )
    return buy_mask.values.astype(np.int64), sell_mask.values.astype(np.int64)


# ===========================================================================
# GRID CONFIGURATIONS
# ===========================================================================

def build_tb_grid():
    combos = []
    for h in HORIZONS:
        for tp in (2, 4, 6):
            for sl in (1, 2):
                name = f"tb_h{h}_tp{tp}_sl{sl}"
                combos.append(dict(family="tb", h=h, tp=tp, sl=sl, name=name))
    return combos


def build_trail_grid():
    combos = []
    for h in TRAIL_HORIZONS:
        for trail_n in (2, 4, 6):
            for profit_z in (2, 4, 6):
                name = f"trail_h{h}_tn{trail_n}_pz{profit_z}"
                combos.append(dict(family="trail", h=h, trail_n=trail_n, profit_z=profit_z, name=name))
    return combos


def build_reg_grid():
    return [dict(family="reg", h=h, name=f"reg_h{h}") for h in REG_HORIZONS]


# ===========================================================================
# PYTORCH DATASET
# ===========================================================================

class DirectionDataset(Dataset):
    def __init__(self, X, mask, y_buy, y_sell, y_up=None, y_dn=None):
        self.X = torch.from_numpy(X).float()
        self.mask = torch.from_numpy(mask).bool()
        self.y_buy = torch.from_numpy(y_buy).long()
        self.y_sell = torch.from_numpy(y_sell).long()
        self.regression = y_up is not None
        if self.regression:
            self.y_up = torch.from_numpy(y_up).float()
            self.y_dn = torch.from_numpy(y_dn).float()

    def __len__(self):
        return len(self.y_buy)

    def __getitem__(self, idx):
        if self.regression:
            return (self.X[idx], self.mask[idx], self.y_buy[idx],
                    self.y_sell[idx], self.y_up[idx], self.y_dn[idx])
        return (self.X[idx], self.mask[idx], self.y_buy[idx], self.y_sell[idx])


# ===========================================================================
# MODEL LOADING
# ===========================================================================

def load_pretrained_encoder(device="cpu"):
    ckpt = torch.load(CHECKPOINT_PATH, map_location=device, weights_only=False)
    model_kwargs = ckpt["model_kwargs"]
    model_kwargs["num_classes"] = ckpt.get("num_classes", 3)
    model = TransformerClassifier(**model_kwargs)
    model.load_state_dict(ckpt["model_state_dict"])
    model.to(device)
    return model, model_kwargs


def forward_encoder(model, X, mask):
    batch_size = X.size(0)
    x = model.input_projection(X)
    cls_tokens = model.cls_token.expand(batch_size, -1, -1)
    x = torch.cat([cls_tokens, x], dim=1)
    x = model.pos_encoding(x)
    if mask is not None:
        cls_mask = torch.ones(batch_size, 1, dtype=torch.bool, device=mask.device)
        extended_mask = torch.cat([cls_mask, mask], dim=1)
        src_key_padding_mask = ~extended_mask
    else:
        src_key_padding_mask = None
    x = model.transformer_encoder(x, src_key_padding_mask=src_key_padding_mask)
    return x


def extract_frozen_features(model, X, mask, device="cpu"):
    model.eval()
    with torch.no_grad():
        X_t = torch.from_numpy(X).float().to(device)
        mask_t = torch.from_numpy(mask).bool().to(device)
        hidden = forward_encoder(model, X_t, mask_t)
        cls_hidden = hidden[:, 0, :]
        return cls_hidden.cpu().numpy()


# ===========================================================================
# EVALUATION
# ===========================================================================

def compute_pf(trades):
    gross_profit = sum(t["pnl"] for t in trades if t["pnl"] > 0)
    gross_loss = abs(sum(t["pnl"] for t in trades if t["pnl"] < 0))
    if gross_loss == 0:
        return float("inf") if gross_profit > 0 else 0.0
    return gross_profit / gross_loss


def compute_seq_pf(trades):
    pos_sum = 0.0
    neg_sum = 0.0
    for t in trades:
        if t["pnl"] >= 0:
            pos_sum += t["pnl"]
            neg_sum = max(0.0, neg_sum - t["pnl"])
        else:
            neg_sum += abs(t["pnl"])
            pos_sum = max(0.0, pos_sum - abs(t["pnl"]))
    if neg_sum == 0:
        return float("inf") if pos_sum > 0 else 0.0
    return pos_sum / neg_sum


def simulate_trades(signals, atr_values, time_values, ohlc_path, direction, hold_bars=1):
    ohlc_dict = {}
    with open(ohlc_path, newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            t = datetime.strptime(row["time"], "%Y.%m.%d %H:%M").replace(tzinfo=timezone.utc)
            ohlc_dict[t] = (float(row["open"]), float(row["high"]),
                            float(row["low"]), float(row["close"]))
    times = sorted(ohlc_dict.keys())
    time_to_idx = {t: i for i, t in enumerate(times)}

    trades = []
    for i in range(len(signals)):
        if signals[i] <= 0:
            continue
        if np.isnan(atr_values[i]) or atr_values[i] <= 0:
            continue
        time_str = time_values[i]
        try:
            dt = datetime.strptime(str(time_str), "%Y.%m.%d %H:%M").replace(tzinfo=timezone.utc)
        except (ValueError, KeyError):
            continue
        base_idx = time_to_idx.get(dt)
        if base_idx is None or base_idx + 2 >= len(times):
            continue
        entry_idx = base_idx + 1
        entry_price = float(ohlc_dict[times[entry_idx]][0])
        exit_price = float(ohlc_dict[times[entry_idx]][3])
        if direction == "buy":
            pnl_atr = (exit_price - entry_price) / atr_values[i]
        else:
            pnl_atr = (entry_price - exit_price) / atr_values[i]
        trades.append(dict(row=i, pnl=pnl_atr, entry_time=str(times[entry_idx])))
    return trades


# ===========================================================================
# PREPARE: build all target combos + save feature tensors
# ===========================================================================

def prepare_data():
    os.makedirs(REPORTS_DIR, exist_ok=True)

    print("=== Loading feature tensors ===")
    tensors = load_feature_tensors()

    print("\n=== Loading raw targets ===")
    df_raw, all_atr = load_raw_targets()
    print(f"  Raw features: {len(df_raw)} rows")

    all_targets = {}

    # --- TB targets ---
    print("\n=== Building TB targets ===")
    for combo in build_tb_grid():
        h, tp, sl = combo["h"], combo["tp"], combo["sl"]
        results = {}
        for split in ["train", "validation", "test"]:
            up_raw, dn_raw, atr = get_raw_updn(df_raw, split, h)
            buy, sell = build_tb_targets(up_raw, dn_raw, atr, tp, sl)
            results[split] = (buy, sell)
        buy_train = int(results["train"][0].sum())
        sell_train = int(results["train"][1].sum())
        if buy_train < 500 or sell_train < 500:
            print(f"  SKIP {combo['name']}: sparse (BUY={buy_train}, SELL={sell_train})")
            continue
        all_targets[combo["name"]] = results
        buy_val = int(results["validation"][0].sum())
        sell_val = int(results["validation"][1].sum())
        print(f"  {combo['name']}: BUY train={buy_train} val={buy_val}, SELL train={sell_train} val={sell_val}")

    # --- Trail targets ---
    print("\n=== Building Trail targets ===")
    for combo in build_trail_grid():
        h, tn, pz = combo["h"], combo["trail_n"], combo["profit_z"]
        results = {}
        ok = True
        for split in ["train", "validation"]:
            try:
                buy, sell = build_trail_targets(df_raw, split, str(OHLC_PATH), tn, pz, h)
                results[split] = (buy, sell)
            except Exception as e:
                print(f"  SKIP {combo['name']} ({split}): {e}")
                ok = False
                break
        if not ok:
            continue
        buy_train = int(results["train"][0].sum())
        sell_train = int(results["train"][1].sum())
        if buy_train < 500 or sell_train < 500:
            print(f"  SKIP {combo['name']}: sparse (BUY={buy_train}, SELL={sell_train})")
            continue
        all_targets[combo["name"]] = results
        buy_val = int(results["validation"][0].sum())
        sell_val = int(results["validation"][1].sum())
        print(f"  {combo['name']}: BUY train={buy_train} val={buy_val}, SELL train={sell_train} val={sell_val}")

    # --- Reg targets ---
    print("\n=== Building Reg targets ===")
    for combo in build_reg_grid():
        h = combo["h"]
        results = {}
        for split in ["train", "validation", "test"]:
            up_raw, dn_raw, atr = get_raw_updn(df_raw, split, h)
            up_atr, dn_atr = build_reg_targets(up_raw, dn_raw, atr)
            results[split] = (up_atr, dn_atr)
        all_targets[combo["name"]] = results
        print(f"  {combo['name']}: ready")

    # Save features
    np.savez_compressed(
        REPORTS_DIR / "prepared_features.npz",
        X_train=tensors["train"][0],
        mask_train=tensors["train"][1],
        X_val=tensors["validation"][0],
        mask_val=tensors["validation"][1],
    )
    print("\nSaved prepared_features.npz")

    # Save combo summary
    combo_names = sorted(all_targets.keys())
    with open(REPORTS_DIR / "target_combos.json", "w") as f:
        json.dump(dict(total_combos=len(combo_names), combo_names=combo_names), f, indent=2)
    print(f"Saved target_combos.json: {len(combo_names)} viable combos")

    # Save per-combo NPZ files
    for name in combo_names:
        data = all_targets[name]
        save_dict = {}
        for split_key, split_name in [("train", "train"), ("validation", "validation")]:
            if split_key in data:
                save_dict[f"buy_{split_name}"] = data[split_key][0]
                save_dict[f"sell_{split_name}"] = data[split_key][1]
        np.savez_compressed(REPORTS_DIR / f"targets_{name}.npz", **save_dict)

    print(f"Saved {len(combo_names)} target NPZ files")
    return all_targets


# ===========================================================================
# STATISTICAL VALIDATION
# ===========================================================================

def stat_validate():
    print("=== Statistical Validation ===")

    prep = np.load(REPORTS_DIR / "prepared_features.npz")
    X_val = prep["X_val"]
    mask_val = prep["mask_val"]
    print(f"Loaded X_val: {X_val.shape}")

    print("\nLoading pretrained encoder...")
    model, _ = load_pretrained_encoder(device="cpu")

    print("Extracting frozen encoder features (32-dim CLS)...")
    hidden = extract_frozen_features(model, X_val, mask_val, device="cpu")
    print(f"Hidden states: {hidden.shape}")

    stats = {
        "shape": list(hidden.shape),
        "n_features": int(hidden.shape[1]),
        "nans": int(np.isnan(hidden).sum()),
        "infs": int(np.isinf(hidden).sum()),
    }

    means = hidden.mean(axis=0)
    stds = hidden.std(axis=0, ddof=1)
    stats["collapsed_features"] = int((stds < 1e-6).sum())
    stats["low_variance_features"] = int((stds < 0.01).sum())
    stats["mean_mean"] = float(np.mean(means))
    stats["mean_std"] = float(np.mean(stds))
    stats["min_std"] = float(np.min(stds))
    stats["max_std"] = float(np.max(stds))

    n_sample = min(5000, hidden.shape[0])
    idx = np.random.RandomState(42).choice(hidden.shape[0], n_sample, replace=False)
    corr = np.corrcoef(hidden[idx].T)
    high_corr_pairs = (np.abs(corr) > 0.99).sum() - corr.shape[0]
    stats["high_correlation_pairs"] = int(high_corr_pairs // 2)

    z_scores = np.abs((hidden - means) / np.clip(stds, 1e-12, None))
    outlier_frac = (z_scores > 5).sum(axis=0) / hidden.shape[0]
    stats["outlier_features_mean_pct"] = float(np.mean(outlier_frac) * 100)
    stats["outlier_features_max_pct"] = float(np.max(outlier_frac) * 100)

    os.makedirs(REPORTS_DIR, exist_ok=True)
    with open(REPORTS_DIR / "feature_statistics.json", "w") as f:
        json.dump(stats, f, indent=2)
    print(f"Saved feature_statistics.json")
    print(json.dumps(stats, indent=2, default=str))


# ===========================================================================
# MAIN
# ===========================================================================

def main():
    parser = argparse.ArgumentParser(description="Transformer Direction Fine-Tune")
    parser.add_argument("--task", default="prepare",
                        choices=["prepare", "stat", "grid_rf", "grid_ft", "test"])
    args = parser.parse_args()

    if args.task == "prepare":
        prepare_data()
    elif args.task == "stat":
        stat_validate()
    elif args.task == "grid_rf":
        run_frozen_rf_grid()
    elif args.task == "grid_ft":
        run_fine_tune_grid()
    elif args.task == "test":
        print(f"Task {args.task} not implemented yet")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

# ===========================================================================
# FROZEN RF BASELINE
# ===========================================================================

def extract_all_frozen_features(model, device='cpu'):
    prep = np.load(REPORTS_DIR / 'prepared_features.npz')
    X_train = prep['X_train']
    mask_train = prep['mask_train']
    X_val = prep['X_val']
    mask_val = prep['mask_val']

    print('Extracting frozen features (train)...')
    ft_train = extract_frozen_features(model, X_train, mask_train, device)
    print('Extracting frozen features (val)...')
    ft_val = extract_frozen_features(model, X_val, mask_val, device)

    train_time = pd.read_csv(LABELED_PATHS['train'], sep=';')['time'].values
    train_atr = pd.to_numeric(pd.read_csv(LABELED_PATHS['train'], sep=';')['ATR'], errors='coerce').fillna(0).values
    val_time = pd.read_csv(LABELED_PATHS['validation'], sep=';')['time'].values
    val_atr = pd.to_numeric(pd.read_csv(LABELED_PATHS['validation'], sep=';')['ATR'], errors='coerce').fillna(0).values

    return ft_train, ft_val, train_time, train_atr, val_time, val_atr


def train_rf_classifier(X_train, y_train, n_estimators=100, max_depth=10):
    from sklearn.ensemble import RandomForestClassifier
    clf = RandomForestClassifier(
        n_estimators=n_estimators, max_depth=max_depth,
        class_weight='balanced', random_state=42, n_jobs=-1,
    )
    clf.fit(X_train, y_train)
    return clf


def evaluate_rf_predictions(clf, X, y_true, atr, time_vals, ohlc_path, direction, thresholds=(0.5, 0.6, 0.7, 0.8)):
    proba = clf.predict_proba(X)[:, 1]

    best = dict(pf=0.0, seq_pf=0.0, trades=0, win_rate=0.0, threshold=0.5)
    for thr in thresholds:
        signals = (proba >= thr).astype(np.int64)
        trades = simulate_trades(signals, atr, time_vals, str(ohlc_path), direction)
        if len(trades) < 50:
            continue
        pf = compute_pf(trades)
        seq_pf = compute_seq_pf(trades)
        win_rate = sum(1 for t in trades if t['pnl'] > 0) / len(trades)
        if seq_pf > best['seq_pf']:
            best = dict(pf=pf, seq_pf=seq_pf, trades=len(trades),
                    win_rate=win_rate, threshold=thr)
    return best


def run_frozen_rf_grid():
    print('=== Frozen RF Baseline Grid Search ===')
    print()

    model, _ = load_pretrained_encoder(device='cpu')
    ft_train, ft_val, train_time, train_atr, val_time, val_atr = extract_all_frozen_features(model, device='cpu')
    print(f'Frozen features: train={ft_train.shape}, val={ft_val.shape}')
    print()

    with open(REPORTS_DIR / 'target_combos.json', 'r') as f:
        combos_meta = json.load(f)
    combo_names = combos_meta['combo_names']
    print(f'Total combos: {len(combo_names)}')

    results = []
    for name in combo_names:
        if name.startswith('reg_'):
            print(f'  SKIP {name}: regression target, handled by fine-tune')
            continue

        print('')
        print(f'--- {name} ---')
        data = np.load(REPORTS_DIR / f'targets_{name}.npz')
        buy_train = data['buy_train']
        sell_train = data['sell_train']
        buy_val = data['buy_validation']
        sell_val = data['sell_validation']

        clf_buy = train_rf_classifier(ft_train, buy_train)
        buy_result = evaluate_rf_predictions(clf_buy, ft_val, buy_val, val_atr, val_time, OHLC_PATH, 'buy')

        clf_sell = train_rf_classifier(ft_train, sell_train)
        sell_result = evaluate_rf_predictions(clf_sell, ft_val, sell_val, val_atr, val_time, OHLC_PATH, 'sell')

        row = dict(
            combo=name,
            buy_pf=round(buy_result['pf'], 4),
            buy_seq_pf=round(buy_result['seq_pf'], 4),
            buy_trades=buy_result['trades'],
            buy_win_rate=round(buy_result['win_rate'], 4),
            buy_threshold=buy_result['threshold'],
            sell_pf=round(sell_result['pf'], 4),
            sell_seq_pf=round(sell_result['seq_pf'], 4),
            sell_trades=sell_result['trades'],
            sell_win_rate=round(sell_result['win_rate'], 4),
            sell_threshold=sell_result['threshold'],
        )
        results.append(row)
        print(f'  BUY: PF={row["buy_pf"]}, SeqPF={row["buy_seq_pf"]}, trades={buy_result["trades"]}, thr={buy_result["threshold"]}')
        print(f'  SELL: PF={row["sell_pf"]}, SeqPF={row["sell_seq_pf"]}, trades={sell_result["trades"]}, thr={sell_result["threshold"]}')

    with open(REPORTS_DIR / 'validation_grid_frozen.json', 'w') as f:
        json.dump(results, f, indent=2)
    print("")
    print(f"Saved validation_grid_frozen.json ({len(results)} rows)")

    print("")
    print("=== Top combos by min(buy_seq_pf, sell_seq_pf) ===")
    sorted_results = sorted(results, key=lambda r: min(r['buy_seq_pf'], r['sell_seq_pf']), reverse=True)
    for r in sorted_results[:10]:
        min_pf = min(r['buy_seq_pf'], r['sell_seq_pf'])
        print(f'  {r["combo"]}: min_seq_pf={min_pf:.4f} (BUY={r["buy_seq_pf"]}, SELL={r["sell_seq_pf"]})')

    return results


# ===========================================================================
# FINE-TUNE TRANSFORMER
# ===========================================================================

def build_fine_tune_model(model_kwargs, device='cpu'):
    model = TransformerClassifier(**model_kwargs)
    model, _ = load_pretrained_encoder(device)  # load pretrained weights
    return model


def replace_head_for_binary(model, dropout=None):
    if dropout is None:
        dropout = ENC_DROPOUT
    model.classifier = nn.Sequential(
        nn.Dropout(dropout),
        nn.Linear(ENC_D_MODEL, 32),
        nn.ReLU(),
        nn.Dropout(dropout),
        nn.Linear(32, 1),  # single logit for BCEWithLogitsLoss
    )
    return model


def train_transformer_binary(model, X_train, mask_train, y_train, X_val, mask_val, y_val,
                              lr=1e-4, epochs=20, patience=5, batch_size=256, device='cpu'):
    from sklearn.metrics import f1_score

    # Compute pos_weight for class balance
    pos_count = y_train.sum()
    neg_count = len(y_train) - pos_count
    pos_weight = torch.tensor([neg_count / max(pos_count, 1)], device=device)

    train_dataset = DirectionDataset(X_train, mask_train, y_train, np.zeros_like(y_train))
    val_dataset = DirectionDataset(X_val, mask_val, y_val, np.zeros_like(y_val))

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, drop_last=False)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, drop_last=False)

    # Build optimizer: different LR for encoder vs head
    encoder_params = []
    head_params = []
    for name, param in model.named_parameters():
        if name.startswith('classifier'):
            head_params.append(param)
        else:
            encoder_params.append(param)

    optimizer = torch.optim.AdamW([
        dict(params=encoder_params, lr=lr),
        dict(params=head_params, lr=lr * 10),
    ])

    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='max', factor=0.5, patience=3, min_lr=1e-6
    )

    model.train()
    best_val_f1 = 0.0
    best_state = None
    epochs_no_improve = 0

    for epoch in range(epochs):
        model.train()
        total_loss = 0.0
        for batch_X, batch_mask, batch_buy, batch_sell in train_loader:
            batch_X = batch_X.to(device)
            batch_mask = batch_mask.to(device)
            batch_y = batch_buy.float().unsqueeze(1).to(device)

            optimizer.zero_grad()
            hidden = forward_encoder(model, batch_X, batch_mask)
            cls_out = hidden[:, 0, :]
            logits = model.classifier(cls_out)
            loss = criterion(logits, batch_y)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            total_loss += loss.item()

        # Validation F1
        model.eval()
        all_preds = []
        all_labels = []
        with torch.no_grad():
            for batch_X, batch_mask, batch_buy, batch_sell in val_loader:
                batch_X = batch_X.to(device)
                batch_mask = batch_mask.to(device)
                batch_y = batch_buy.float().numpy()
                hidden = forward_encoder(model, batch_X, batch_mask)
                cls_out = hidden[:, 0, :]
                logits = model.classifier(cls_out)
                preds = (torch.sigmoid(logits).squeeze().cpu().numpy() >= 0.5).astype(int)
                all_preds.extend(preds)
                all_labels.extend(batch_y)

        val_f1 = f1_score(all_labels, all_preds, zero_division=0)
        scheduler.step(val_f1)

        if val_f1 > best_val_f1:
            best_val_f1 = val_f1
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            epochs_no_improve = 0
        else:
            epochs_no_improve += 1

        if epoch % 5 == 0:
            print(f'    epoch {epoch}: loss={total_loss/len(train_loader):.4f}, val_f1={val_f1:.4f}, best={best_val_f1:.4f}')

        if epochs_no_improve >= patience:
            print(f'    early stopping at epoch {epoch}')
            break

    # Restore best
    if best_state is not None:
        model.load_state_dict(best_state)

    return model, best_val_f1


def evaluate_transformer_model(model, X, mask, y_true, atr, time_vals, ohlc_path, direction,
                                device='cpu', thresholds=(0.3, 0.4, 0.5, 0.6, 0.7, 0.8)):
    dataset = DirectionDataset(X, mask, y_true, np.zeros_like(y_true))
    loader = DataLoader(dataset, batch_size=512, shuffle=False, drop_last=False)

    model.eval()
    all_probs = []
    with torch.no_grad():
        for batch_X, batch_mask, batch_buy, batch_sell in loader:
            batch_X = batch_X.to(device)
            batch_mask = batch_mask.to(device)
            hidden = forward_encoder(model, batch_X, batch_mask)
            cls_out = hidden[:, 0, :]
            logits = model.classifier(cls_out)
            probs = torch.sigmoid(logits).squeeze().cpu().numpy()
            all_probs.extend(probs)

    all_probs = np.array(all_probs)

    best = dict(pf=0.0, seq_pf=0.0, trades=0, win_rate=0.0, threshold=0.5)
    for thr in thresholds:
        signals = (all_probs >= thr).astype(np.int64)
        trades = simulate_trades(signals, atr, time_vals, str(ohlc_path), direction)
        if len(trades) < 50:
            continue
        pf = compute_pf(trades)
        seq_pf = compute_seq_pf(trades)
        win_rate = sum(1 for t in trades if t['pnl'] > 0) / len(trades)
        if seq_pf > best['seq_pf']:
            best = dict(pf=pf, seq_pf=seq_pf, trades=len(trades),
                    win_rate=win_rate, threshold=thr)
    return best


def run_fine_tune_grid(combo_names=None, lrs=(1e-4, 5e-5), device='cpu'):
    print('=== Transformer Fine-Tune Grid Search ===')
    print()

    prep = np.load(REPORTS_DIR / 'prepared_features.npz')
    X_train = prep['X_train']
    mask_train = prep['mask_train']
    X_val = prep['X_val']
    mask_val = prep['mask_val']

    val_time = pd.read_csv(LABELED_PATHS['validation'], sep=';')['time'].values
    val_atr = pd.to_numeric(pd.read_csv(LABELED_PATHS['validation'], sep=';')['ATR'],
                            errors='coerce').fillna(0).values

    # Load pretrained weights + kwargs
    pretrained, model_kwargs = load_pretrained_encoder(device)
    del pretrained  # we recreate from scratch each time

    with open(REPORTS_DIR / 'target_combos.json', 'r') as f:
        combos_meta = json.load(f)

    if combo_names is None:
        # Default: top TB combos from frozen RF + Reg combos
        with open(REPORTS_DIR / 'validation_grid_frozen.json', 'r') as f:
            frozen_results = json.load(f)
        sorted_rf = sorted(frozen_results, key=lambda r: min(r['buy_seq_pf'], r['sell_seq_pf']), reverse=True)
        combo_names = [r['combo'] for r in sorted_rf[:4]]
        # Add Reg combos
        for name in combos_meta['combo_names']:
            if name.startswith('reg_'):
                combo_names.append(name)
        print(f'Selected combos: {combo_names}')
    else:
        print(f'Selected combos: {combo_names}')

    print()
    results = []

    for name in combo_names:
        is_reg = name.startswith('reg_')
        if is_reg:
            print(f'--- {name} ---')
            print('  SKIP: regression fine-tune not implemented yet')
            continue

        print('')
        print(f'=== {name} ===')
        data = np.load(REPORTS_DIR / f'targets_{name}.npz')
        buy_train = data['buy_train']
        sell_train = data['sell_train']
        buy_val = data['buy_validation']
        sell_val = data['sell_validation']

        best_buy = None
        best_sell = None
        best_buy_lr = 0
        best_sell_lr = 0

        for lr in lrs:
            # BUY
            print(f'  BUY lr={lr}...')
            model = TransformerClassifier(**model_kwargs)
            model.load_state_dict(load_pretrained_encoder(device)[0].state_dict())
            replace_head_for_binary(model)
            model.to(device)
            model, val_f1 = train_transformer_binary(
                model, X_train, mask_train, buy_train, X_val, mask_val, buy_val,
                lr=lr, device=device,
            )
            buy_result = evaluate_transformer_model(
                model, X_val, mask_val, buy_val, val_atr, val_time, OHLC_PATH, 'buy', device=device,
            )
            print(f'    BUY lr={lr}: PF={buy_result["pf"]:.4f}, SeqPF={buy_result["seq_pf"]:.4f}, '
                  f'trades={buy_result["trades"]}, thr={buy_result["threshold"]}')
            if best_buy is None or buy_result['seq_pf'] > best_buy['seq_pf']:
                best_buy = buy_result
                best_buy_lr = lr
                best_buy_model = model

            # SELL
            print(f'  SELL lr={lr}...')
            model = TransformerClassifier(**model_kwargs)
            model.load_state_dict(load_pretrained_encoder(device)[0].state_dict())
            replace_head_for_binary(model)
            model.to(device)
            model, val_f1 = train_transformer_binary(
                model, X_train, mask_train, sell_train, X_val, mask_val, sell_val,
                lr=lr, device=device,
            )
            sell_result = evaluate_transformer_model(
                model, X_val, mask_val, sell_val, val_atr, val_time, OHLC_PATH, 'sell', device=device,
            )
            print(f'    SELL lr={lr}: PF={sell_result["pf"]:.4f}, SeqPF={sell_result["seq_pf"]:.4f}, '
                  f'trades={sell_result["trades"]}, thr={sell_result["threshold"]}')
            if best_sell is None or sell_result['seq_pf'] > best_sell['seq_pf']:
                best_sell = sell_result
                best_sell_lr = lr
                best_sell_model = model

        row = dict(
            combo=name,
            buy_pf=round(best_buy['pf'], 4),
            buy_seq_pf=round(best_buy['seq_pf'], 4),
            buy_trades=best_buy['trades'],
            buy_win_rate=round(best_buy['win_rate'], 4),
            buy_threshold=best_buy['threshold'],
            buy_lr=best_buy_lr,
            sell_pf=round(best_sell['pf'], 4),
            sell_seq_pf=round(best_sell['seq_pf'], 4),
            sell_trades=best_sell['trades'],
            sell_win_rate=round(best_sell['win_rate'], 4),
            sell_threshold=best_sell['threshold'],
            sell_lr=best_sell_lr,
        )
        results.append(row)
        print(f'  BEST BUY: PF={row["buy_pf"]}, SeqPF={row["buy_seq_pf"]}, trades={best_buy["trades"]}')
        print(f'  BEST SELL: PF={row["sell_pf"]}, SeqPF={row["sell_seq_pf"]}, trades={best_sell["trades"]}')

    with open(REPORTS_DIR / 'validation_grid_finetune.json', 'w') as f:
        json.dump(results, f, indent=2)
    print('')
    print(f'Saved validation_grid_finetune.json ({len(results)} rows)')

    return results

