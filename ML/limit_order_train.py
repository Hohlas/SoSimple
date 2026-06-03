#!/usr/bin/env python
# =============================================================================
# ML/limit_order_train.py — Transformer training on limit-order BUY labels
# Phase 3 of limit-order entry convention (canonical spread 0.20)
# =============================================================================
"""
Trains Transformer model on limit-order BUY triple-barrier labels.

Pre-filters DATA/limit_order/ CSVs to filled BUY limit entries (all rows,
no signal filter), saves to DATA/limit_order_buy_fill_*.csv, and trains
standard triple_barrier pipeline via monkey-patched data_loader.

Usage:
  python -m ML.limit_order_train [--epochs 50] [--batch_size 256] [--lr 1e-3]
"""
import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn

torch.use_deterministic_algorithms(True)
os.environ['CUBLAS_WORKSPACE_CONFIG'] = ':4096:8'

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / 'DATA'
LIMIT_ORDER_DIR = DATA_DIR / 'limit_order'
ML_DIR = PROJECT_ROOT / 'ML'
CHECKPOINTS_DIR = ML_DIR / 'checkpoints'
PLOTS_DIR = ML_DIR / 'plots'

BUY_TB_TARGETS = ['buy_sl2_tp3', 'buy_sl2_tp6', 'buy_sl2_tp9',
                   'buy_sl3_tp3', 'buy_sl3_tp6', 'buy_sl3_tp9']
CSV_SEP = ';'
TMP_TRAIN_FILE = DATA_DIR / 'limit_order_buy_fill_train.csv'
TMP_VAL_FILE = DATA_DIR / 'limit_order_buy_fill_val.csv'


def prefilter_csv(src: Path, dst: Path) -> pd.DataFrame:
    """Load limit_order CSV, filter to filled BUY limit orders (all rows, not only signal!=0)."""
    df = pd.read_csv(src, sep=CSV_SEP, low_memory=False)
    fill_mask = pd.to_numeric(df['buy_fill_lag'], errors='coerce').fillna(-1).astype(int) != -1
    result = df[fill_mask].copy()
    for col in BUY_TB_TARGETS:
        vals = pd.to_numeric(result[col], errors='coerce').fillna(0.0)
        vals = np.where(vals == 0.5, 0.0, vals)  # TIMEOUT -> LOSS
        result[col] = vals
    result.to_csv(dst, sep=CSV_SEP, index=False)
    print(f"  prefilter_csv: {len(result)} rows (fill-only, no signal filter)")
    return result


def main():
    parser = argparse.ArgumentParser(description='Train Transformer on limit-order BUY labels')
    parser.add_argument('--epochs', type=int, default=50)
    parser.add_argument('--batch_size', type=int, default=256)
    parser.add_argument('--lr', type=float, default=1e-3)
    parser.add_argument('--weight_decay', type=float, default=1e-4)
    parser.add_argument('--patience', type=int, default=10)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--d_model', type=int, default=128)
    parser.add_argument('--nhead', type=int, default=8)
    parser.add_argument('--num_layers', type=int, default=3)
    parser.add_argument('--device', type=str, default='cpu')
    args = parser.parse_args()

    # ── Pre-filter CSVs ───────────────────────────────────────────────
    print("Pre-filtering limit_order CSVs -> BUY + filled only")
    df_train = prefilter_csv(
        LIMIT_ORDER_DIR / 'Nero_train_labeled.csv', TMP_TRAIN_FILE)
    df_val = prefilter_csv(
        LIMIT_ORDER_DIR / 'Nero_validation_labeled.csv', TMP_VAL_FILE)
    print(f"  Train (BUY + fill): {len(df_train)} rows")
    print(f"  Val   (BUY + fill): {len(df_val)} rows")

    # ── Monkey-patch data_loader ──────────────────────────────────────
    import ML.data_loader as dl
    dl.TRAIN_FILE = TMP_TRAIN_FILE
    dl.VAL_FILE = TMP_VAL_FILE
    dl.TB_TARGET_NAMES = BUY_TB_TARGETS
    dl.validate_csv_columns = lambda *a, **kw: None
    dl.validate_fractal_format = lambda *a, **kw: None
    dl.target_uses_signal_rows = lambda t: False

    # ── Setup ─────────────────────────────────────────────────────────
    from ML.utils import set_seed, get_device, count_parameters
    from ML.data_loader import create_data_loaders, N_FRACTAL_FEATURES
    from ML.models import get_model

    set_seed(args.seed)
    device = get_device(args.device)
    CHECKPOINTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print(" LIMIT-ORDER: Transformer on BUY TB labels")
    print(f"  Targets: {BUY_TB_TARGETS}")
    print(f"  Device: {device}")
    print("=" * 60)

    # ── Data ──────────────────────────────────────────────────────────
    n_buy_targets = len(BUY_TB_TARGETS)
    train_loader, val_loader, _ = create_data_loaders(
        batch_size=args.batch_size, target='triple_barrier',
        use_scaler=False, use_weighted_sampler=False,
        clear_cache=True, seed=args.seed)

    # Compute pos_weight
    y_train_all = []
    for _, y_batch, _ in train_loader:
        y_train_all.append(y_batch.numpy())
    y_train_np = np.concatenate(y_train_all)
    n_pos = (y_train_np == 1).sum(axis=0).astype(float)
    n_neg = (y_train_np == 0).sum(axis=0).astype(float)
    pos_weight = torch.tensor(n_neg / (n_pos + 1e-6), dtype=torch.float32).to(device)
    print(f"  Pos weights: {[f'{w:.2f}' for w in pos_weight.tolist()]}")

    # ── Model ─────────────────────────────────────────────────────────
    model_kwargs = {
        'input_features': N_FRACTAL_FEATURES,
        'd_model': args.d_model,
        'nhead': args.nhead,
        'num_layers': args.num_layers,
        'dropout': 0.1,
    }
    model = get_model('transformer', num_classes=n_buy_targets, **model_kwargs)
    model = model.to(device)
    n_params = count_parameters(model)
    print(f"\n  Model: Transformer d={args.d_model} h={args.nhead} L={args.num_layers}")
    print(f"  Params: {n_params:,}")

    # ── Loss, Optimizer, Scheduler ────────────────────────────────────
    loss_fn = nn.BCEWithLogitsLoss(pos_weight=pos_weight).to(device)
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='max', patience=5, factor=0.5)

    # ── Training ──────────────────────────────────────────────────────
    best_mean_auc = -1.0
    best_epoch = 0
    best_state = None
    epochs_no_improve = 0
    history = {'train_loss': [], 'val_loss': [], 'val_mean_auc': []}

    print(f"\n{'Epoch':>5} | {'Train Loss':>10} | {'Val Loss':>10} | {'Mean AUC':>10} | {'LR':>10}")
    print(f"{'─' * 55}")

    for epoch in range(1, args.epochs + 1):
        # Train
        model.train()
        total_loss = 0.0
        n_batches = 0
        for X_batch, y_batch, mask_batch in train_loader:
            X_batch = X_batch.to(device)
            y_batch = y_batch.to(device).float()
            mask_batch = mask_batch.to(device)
            optimizer.zero_grad()
            logits = model(X_batch, mask=mask_batch)
            loss = loss_fn(logits, y_batch)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            total_loss += loss.item()
            n_batches += 1
        train_loss = total_loss / n_batches

        # Validate
        model.eval()
        val_loss = 0.0
        n_val_batches = 0
        all_logits, all_targets = [], []
        with torch.no_grad():
            for X_batch, y_batch, mask_batch in val_loader:
                X_batch = X_batch.to(device)
                y_batch = y_batch.to(device).float()
                mask_batch = mask_batch.to(device)
                logits = model(X_batch, mask=mask_batch)
                loss = loss_fn(logits, y_batch)
                val_loss += loss.item()
                n_val_batches += 1
                all_logits.append(logits.cpu().numpy())
                all_targets.append(y_batch.cpu().numpy())
        val_loss /= n_val_batches
        all_logits = np.concatenate(all_logits)
        all_targets = np.concatenate(all_targets)

        # Per-target AUC
        from sklearn.metrics import roc_auc_score
        per_auc = []
        for i in range(n_buy_targets):
            yt = all_targets[:, i]
            prob = 1.0 / (1.0 + np.exp(-all_logits[:, i]))
            try:
                auc = roc_auc_score(yt, prob)
            except ValueError:
                auc = 0.5
            per_auc.append(auc)
        mean_auc = float(np.mean(per_auc))

        lr = optimizer.param_groups[0]['lr']
        history['train_loss'].append(train_loss)
        history['val_loss'].append(val_loss)
        history['val_mean_auc'].append(mean_auc)

        print(f"{epoch:>5} | {train_loss:>10.4f} | {val_loss:>10.4f} | {mean_auc:>10.4f} | {lr:>10.6f}")
        scheduler.step(mean_auc)

        if mean_auc > best_mean_auc:
            best_mean_auc = mean_auc
            best_epoch = epoch
            best_state = {
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'best_mean_auc': best_mean_auc,
                'per_target_auc': dict(zip(BUY_TB_TARGETS, per_auc)),
                'model_kwargs': model_kwargs,
                'args': vars(args),
            }
            ckpt_path = CHECKPOINTS_DIR / 'transformer_limit_order_buy_best.pt'
            torch.save(best_state, ckpt_path)
            print(f"      ✅ Best AUC={best_mean_auc:.4f} -> {ckpt_path.name}")
            epochs_no_improve = 0
        else:
            epochs_no_improve += 1
            if epochs_no_improve >= args.patience:
                print(f"\n  Early stopping at epoch {epoch}")
                break

    # ── Results ───────────────────────────────────────────────────────
    print(f"\n{'═' * 60}")
    print(f"  LIMIT-ORDER Transformer: BUY TB RESULTS")
    print(f"{'═' * 60}")
    print(f"  Best epoch: {best_epoch}   Mean AUC: {best_mean_auc:.4f}")
    for t, a in best_state['per_target_auc'].items():
        print(f"    {t}: {a:.4f}")

    report = {
        'phase': 'Phase 3: Transformer on limit-order BUY labels',
        'targets': BUY_TB_TARGETS,
        'model': {**model_kwargs, 'n_params': n_params},
        'results': {
            'best_epoch': best_epoch,
            'best_mean_auc': best_mean_auc,
            'per_target_auc': best_state['per_target_auc'] if best_state else {},
            'history': history,
        },
        'args': vars(args),
    }
    report_path = ML_DIR / 'reports' / 'limit_order_transformer.json'
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\n  Report: {report_path.name}")
    print(f"  Checkpoint: {ckpt_path}")


if __name__ == '__main__':
    main()
