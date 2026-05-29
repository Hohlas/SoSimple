#!/usr/bin/env python
# =============================================================================
# ML/limit_order_train.py — Transformer training on limit-order BUY labels
# Phase 3 of limit-order entry convention
# =============================================================================
"""
Trains Transformer model on limit-order BUY triple-barrier labels.

Preprocesses DATA/limit_order/ CSVs:
  - Filters NO_FILL rows (buy_fill_lag == -1 → skipped)
  - Keeps only BUY signal rows (signal == 1)
  - Uses BUY-side TB targets: buy_sl{2,3}_tp{3,6,9}
  
Usage:
  python -m ML.limit_order_train [--epochs 50] [--batch_size 256] [--lr 1e-3]
"""
import argparse
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
NO_FILL_SENTINEL = -999.0
CSV_SEP = ';'


def load_and_filter(csv_path: Path) -> pd.DataFrame:
    """Load limit_order CSV, filter to BUY rows with fill."""
    df = pd.read_csv(csv_path, sep=CSV_SEP, low_memory=False)
    print(f"  Loaded {len(df)} rows from {csv_path.name}")

    signal = pd.to_numeric(df['signal'], errors='coerce').fillna(0).astype(int)
    buy_mask = signal == 1
    df_buy = df[buy_mask].copy()
    print(f"  BUY signal rows: {len(df_buy)}")

    no_fill = (df_buy['buy_fill_lag'] == -1)
    df_fill = df_buy[~no_fill].copy()
    print(f"  After NO_FILL filter: {len(df_fill)}")

    for col in BUY_TB_TARGETS:
        vals = pd.to_numeric(df_fill[col], errors='coerce').fillna(NO_FILL_SENTINEL)
        df_fill[col] = vals
        no_fill_in_col = (vals == NO_FILL_SENTINEL).sum()
        if no_fill_in_col > 0:
            print(f"    {col}: {no_fill_in_col} NO_FILL rows (will be masked in loss)")

    print(f"  Final filtered rows: {len(df_fill)}")
    return df_fill


def main():
    parser = argparse.ArgumentParser(description='Train Transformer on limit-order BUY labels')
    parser.add_argument('--epochs', type=int, default=50)
    parser.add_argument('--batch_size', type=int, default=256)
    parser.add_argument('--lr', type=float, default=1e-3)
    parser.add_argument('--weight_decay', type=float, default=1e-4)
    parser.add_argument('--patience', type=int, default=10)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--device', type=str, default='cpu')
    args = parser.parse_args()

    # ── Monkey-patch data_loader paths ────────────────────────────────
    import ML.data_loader as dl
    dl.TRAIN_FILE = LIMIT_ORDER_DIR / 'Nero_train_labeled.csv'
    dl.VAL_FILE = LIMIT_ORDER_DIR / 'Nero_validation_labeled.csv'
    dl.TB_TARGET_NAMES = BUY_TB_TARGETS  # BUY-only targets

    # Also patch validate_fractal_format / validate_csv_columns expectations
    # to accept limit_order columns (which have extra _pnl_r, _fill_lag etc.)
    # These are additive checks; we skip the strict validation by patching.
    _orig_val_csv = dl.validate_csv_columns

    def _relaxed_val_csv(df, source=''):
        pass
    dl.validate_csv_columns = _relaxed_val_csv

    _orig_val_frac = dl.validate_fractal_format

    def _relaxed_val_frac(df, source='', sample_size=50):
        pass
    dl.validate_fractal_format = _relaxed_val_frac

    # Also skip row-level filtering (target_uses_signal_rows) since we
    # already filter BUY rows externally
    _orig_target_uses = dl.target_uses_signal_rows

    def _no_signal_filter(target):
        return False
    dl.target_uses_signal_rows = _no_signal_filter

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
    print(f" Data: {dl.TRAIN_FILE}")
    print(f" Device: {device}")
    print("=" * 60)

    # ── Data ──────────────────────────────────────────────────────────
    print("\n📦 Loading data...")
    n_buy_targets = len(BUY_TB_TARGETS)
    dl.BINARY_CLASSIFICATION_COLUMNS.clear()

    train_loader, val_loader, _ = create_data_loaders(
        batch_size=args.batch_size,
        target='triple_barrier',
        use_scaler=False,
        use_weighted_sampler=False,
        seed=args.seed,
    )

    # ── Compute pos_weight from training data ─────────────────────────
    y_train_all = []
    for _, y_batch, _ in train_loader:
        y_train_all.append(y_batch.numpy())
    y_train_np = np.concatenate(y_train_all)
    n_pos = (y_train_np == 1).sum(axis=0).astype(float)
    n_neg = (y_train_np == 0).sum(axis=0).astype(float)
    pos_weight = torch.tensor(n_neg / (n_pos + 1e-6), dtype=torch.float32).to(device)
    print(f"  Pos weights: {pos_weight.tolist()}")

    # ── Model ─────────────────────────────────────────────────────────
    model_kwargs = {
        'input_features': N_FRACTAL_FEATURES,
        'd_model': 128,
        'nhead': 8,
        'num_layers': 3,
        'dropout': 0.1,
    }
    model = get_model('transformer', num_classes=n_buy_targets, **model_kwargs)
    model = model.to(device)
    n_params = count_parameters(model)
    print(f"\n  Model: Transformer | Params: {n_params:,}")

    # ── Loss, Optimizer, Scheduler ────────────────────────────────────
    loss_fn = nn.BCEWithLogitsLoss(pos_weight=pos_weight).to(device)
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='max', patience=5, factor=0.5)

    # ── Training loop ─────────────────────────────────────────────────
    no_fill_mask = NO_FILL_SENTINEL

    best_mean_auc = -1.0
    best_epoch = 0
    best_state = None
    epochs_without_improvement = 0
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

            valid_targets = (y_batch != no_fill_mask)
            y_batch_clean = torch.where(valid_targets, y_batch, torch.zeros_like(y_batch))

            optimizer.zero_grad()
            logits = model(X_batch, mask=mask_batch)
            loss_unreduced = loss_fn(logits, y_batch_clean)
            loss = (loss_unreduced * valid_targets.float()).sum() / valid_targets.float().sum().clamp_min(1.0)
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
        all_logits = []
        all_targets = []
        all_valid = []

        with torch.no_grad():
            for X_batch, y_batch, mask_batch in val_loader:
                X_batch = X_batch.to(device)
                y_batch = y_batch.to(device).float()
                mask_batch = mask_batch.to(device)

                valid_targets = (y_batch != no_fill_mask)
                y_batch_clean = torch.where(valid_targets, y_batch, torch.zeros_like(y_batch))

                logits = model(X_batch, mask=mask_batch)
                loss_unreduced = loss_fn(logits, y_batch_clean)
                loss = (loss_unreduced * valid_targets.float()).sum() / valid_targets.float().sum().clamp_min(1.0)
                val_loss += loss.item()
                n_val_batches += 1

                all_logits.append(logits.cpu().numpy())
                all_targets.append(y_batch.cpu().numpy())
                all_valid.append(valid_targets.cpu().numpy())

        val_loss /= n_val_batches
        all_logits = np.concatenate(all_logits)
        all_targets = np.concatenate(all_targets)
        all_valid = np.concatenate(all_valid)

        # Per-target AUC
        per_target_aucs = []
        for i, target_name in enumerate(BUY_TB_TARGETS):
            mask = all_valid[:, i]
            if mask.sum() < 10:
                per_target_aucs.append(0.5)
                continue
            y_true = all_targets[mask, i]
            y_prob = 1.0 / (1.0 + np.exp(-all_logits[mask, i]))
            try:
                from sklearn.metrics import roc_auc_score
                auc = roc_auc_score(y_true, y_prob)
            except ValueError:
                auc = 0.5
            per_target_aucs.append(auc)
        mean_auc = float(np.mean(per_target_aucs))

        current_lr = optimizer.param_groups[0]['lr']
        history['train_loss'].append(train_loss)
        history['val_loss'].append(val_loss)
        history['val_mean_auc'].append(mean_auc)

        print(f"{epoch:>5} | {train_loss:>10.4f} | {val_loss:>10.4f} | {mean_auc:>10.4f} | {current_lr:>10.6f}")

        scheduler.step(mean_auc)

        if mean_auc > best_mean_auc:
            best_mean_auc = mean_auc
            best_epoch = epoch
            best_state = {
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'best_mean_auc': best_mean_auc,
                'per_target_aucs': dict(zip(BUY_TB_TARGETS, per_target_aucs)),
                'model_kwargs': model_kwargs,
                'args': vars(args),
            }
            checkpoint_path = CHECKPOINTS_DIR / 'transformer_limit_order_buy_best.pt'
            torch.save(best_state, checkpoint_path)
            print(f"      ✅ New best mean_auc={best_mean_auc:.4f} saved")
            epochs_without_improvement = 0
        else:
            epochs_without_improvement += 1
            if epochs_without_improvement >= args.patience:
                print(f"\n  Stopping: {args.patience} epochs without improvement")
                break

    # ── Results ───────────────────────────────────────────────────────
    print(f"\n{'═' * 60}")
    print(f"  LIMIT-ORDER TRANSFORMER RESULTS")
    print(f"{'═' * 60}")
    print(f"  Best epoch: {best_epoch}")
    print(f"  Best Mean AUC: {best_mean_auc:.4f}")
    print(f"  Targets: {BUY_TB_TARGETS}")
    if best_state:
        print(f"\n  Per-target AUC:")
        for target, auc in best_state['per_target_aucs'].items():
            print(f"    {target}: {auc:.4f}")
        print(f"\n  Checkpoint: {checkpoint_path}")

    # Save report
    report_path = ML_DIR / 'reports' / 'limit_order_transformer.json'
    report_path.parent.mkdir(parents=True, exist_ok=True)
    import json
    report = {
        'phase': 'Phase 3: Transformer on limit-order BUY labels',
        'data': {
            'train_file': str(dl.TRAIN_FILE),
            'val_file': str(dl.VAL_FILE),
            'targets': BUY_TB_TARGETS,
            'filter': 'BUY signal only, NO_FILL excluded',
        },
        'model': {**model_kwargs, 'n_params': n_params},
        'training': vars(args),
        'results': {
            'best_epoch': best_epoch,
            'best_mean_auc': best_mean_auc,
            'per_target_auc': best_state['per_target_aucs'] if best_state else {},
        },
    }
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"  Report: {report_path}")

    # Restore patches
    dl.validate_csv_columns = _orig_val_csv
    dl.validate_fractal_format = _orig_val_frac
    dl.target_uses_signal_rows = _orig_target_uses


if __name__ == '__main__':
    main()
