#!/usr/bin/env python3
"""
Аудит limit-order лейблов: buy/sell fill_lag статистика, ambiguity, сравнение со старыми.

Использование:
  .venv/bin/python processing/label_audit.py \
    --new DATA/limit_order/Nero_train_labeled.csv \
    --old DATA/Nero_train_labeled.csv --primary-target buy_sl3_tp3
"""

import argparse
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'processing'))
from label_signals import TB_TARGET_NAMES, LIMIT_NO_FILL_SENTINEL, LIMIT_AMBIGUOUS_SENTINEL


def audit_fill_lag(df, primary_target):
    """Распределение fill_lag по сторонам (buy/sell)."""
    print("=" * 60)
    print("FILL_LAG AUDIT")
    print("=" * 60)
    total = len(df)
    for side in ['buy', 'sell']:
        lag_col = f'{side}_fill_lag'
        if lag_col not in df.columns:
            print(f"  {side.upper()}: column '{lag_col}' not found")
            continue
        fill_lag = df[lag_col]
        no_fill = (fill_lag == -1).sum()
        filled = (fill_lag >= 0).sum()
        print(f"\n  {side.upper()} fill_lag:")
        print(f"  Filled:     {filled} ({filled / max(total, 1) * 100:.1f}%)")
        print(f"  NO_FILL:    {no_fill} ({no_fill / max(total, 1) * 100:.1f}%)")
        for lag in sorted(fill_lag[fill_lag >= 0].unique()):
            n = (fill_lag == lag).sum()
            print(f"    lag={int(lag)}: {n:5d} ({n / max(filled, 1) * 100:5.1f}%)")
    print()


def audit_ambiguity(df, primary_target):
    """Статистика ambiguous_bar_flag для primary target."""
    print("=" * 60)
    print(f"AMBIGUITY AUDIT ({primary_target})")
    print("=" * 60)
    amb_col = f'ambiguous_flag_{primary_target}'
    if amb_col not in df.columns:
        print(f"WARNING: column {amb_col} not found")
        return
    amb = df[amb_col]
    target_side = 'buy' if primary_target.startswith('buy_') else 'sell'
    fill_col = f'{target_side}_fill_lag'
    filled = df[fill_col] >= 0 if fill_col in df.columns else pd.Series(True, index=df.index)
    filled_amb = amb[filled]

    flags = {0: 'clean', 1: 'fill+SL (same bar)', 2: 'fill+TP (same bar)',
             3: 'fill+TP+SL (same bar)', 4: 'TP+SL (barrier bar)'}
    print("Ambiguous bar flags (filled rows):")
    for val, label in flags.items():
        n = (filled_amb == val).sum()
        if n > 0:
            print(f"  {val} ({label}): {n:5d} ({n / max(filled.sum(), 1) * 100:5.1f}%)")

    # Show avg PnL for ambiguous vs clean
    pnl_col = f'{primary_target}_pnl_r'
    if pnl_col in df.columns:
        filled_pnl = df.loc[filled, pnl_col]
        clean_pnl = filled_pnl[amb[filled] == 0]
        amb_pnl = filled_pnl[amb[filled] != 0]
        print(f"\n  Avg PnL (clean):    {clean_pnl.mean():.3f}R  (n={len(clean_pnl)})")
        print(f"  Avg PnL (ambiguous): {amb_pnl.mean():.3f}R  (n={len(amb_pnl)})")
    print()


def audit_comparison(df_new, df_old, primary_target):
    """Сравнение старых и новых лейблов на пересекающихся строках."""
    print("=" * 60)
    print(f"COMPARISON: old vs new labels ({primary_target})")
    print("=" * 60)

    merged = df_new[['time', primary_target]].merge(
        df_old[['time', primary_target]], on='time', suffixes=('_new', '_old'),
        how='inner',
    )

    n = len(merged)
    if n == 0:
        print("No overlapping rows found.")
        return

    new_vals = merged[f'{primary_target}_new']
    old_vals = merged[f'{primary_target}_old']

    valid = (new_vals != LIMIT_NO_FILL_SENTINEL) & (new_vals != LIMIT_AMBIGUOUS_SENTINEL)
    new_v = new_vals[valid]
    old_v = old_vals[valid]

    agreement = (new_v == old_v).sum()
    print(f"Overlapping rows: {n}")
    print(f"Valid (non-sentinel): {len(new_v)}")
    print(f"Agreement: {agreement} ({agreement / max(len(new_v), 1) * 100:.1f}%)")

    for new_label in [0.0, 0.5, 1.0]:
        for old_label in [0.0, 0.5, 1.0]:
            cnt = ((new_v == new_label) & (old_v == old_label)).sum()
            if cnt > 0:
                print(f"  old={old_label} new={new_label}: {cnt}")
    print()


def main():
    parser = argparse.ArgumentParser(description="Limit-order label audit")
    parser.add_argument('--new', required=True, help='Path to new labeled CSV')
    parser.add_argument('--old', default=None, help='Path to old labeled CSV for comparison')
    parser.add_argument('--primary-target', default='buy_sl3_tp3')
    args = parser.parse_args()

    df_new = pd.read_csv(args.new, sep=';')

    audit_fill_lag(df_new, args.primary_target)
    audit_ambiguity(df_new, args.primary_target)

    if args.old and os.path.exists(args.old):
        df_old = pd.read_csv(args.old, sep=';')
        audit_comparison(df_new, df_old, args.primary_target)


if __name__ == '__main__':
    main()
