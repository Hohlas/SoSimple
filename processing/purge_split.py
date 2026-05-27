#!/usr/bin/env python3
"""
Применить 30-bar purge/embargo к train/val/test split.

Purge считается по времени (timestamp), а не по числу строк (защита от пропусков).

Использование:
  .venv/bin/python processing/purge_split.py \
    --train DATA/limit_order/Nero_train_labeled.csv \
    --val DATA/limit_order/Nero_validation_labeled.csv \
    --test DATA/limit_order/Nero_test_labeled.csv \
    --output-dir DATA/limit_order/ \
    --purge-hours 30
"""

import argparse
import pandas as pd
import os
import sys


def purge_boundary(df, next_df_min_time, purge_hours):
    """Удалить строки из df, чей row_time + purge_hours >= начало следующего сплита."""
    if next_df_min_time is None:
        return df, 0
    times = pd.to_datetime(df['time'])
    cutoff = next_df_min_time - pd.Timedelta(hours=purge_hours)
    keep = times < cutoff
    removed = (~keep).sum()
    return df[keep].copy(), removed


def main():
    parser = argparse.ArgumentParser(description="30-bar purge/embargo for split boundaries")
    parser.add_argument('--train', required=True)
    parser.add_argument('--val', required=True)
    parser.add_argument('--test', required=True)
    parser.add_argument('--purge-hours', type=int, default=30)
    parser.add_argument('--output-dir', default=None)
    args = parser.parse_args()

    train = pd.read_csv(args.train, sep=';')
    val = pd.read_csv(args.val, sep=';')
    test = pd.read_csv(args.test, sep=';')

    val_min = pd.to_datetime(val['time']).min()
    test_min = pd.to_datetime(test['time']).min()
    train_max = pd.to_datetime(train['time']).max()
    val_max = pd.to_datetime(val['time']).max()

    print(f"Original sizes: train={len(train)} val={len(val)} test={len(test)}")
    print(f"Boundaries: train_end={train_max} val_start={val_min} val_end={val_max} test_start={test_min}")

    train_purged, n1 = purge_boundary(train, val_min, args.purge_hours)
    val_purged, n2 = purge_boundary(val, test_min, args.purge_hours)
    # Test tail: удаляем строки без purge_hours будущих баров
    test_times = pd.to_datetime(test['time'])
    test_cutoff = test_times.max() - pd.Timedelta(hours=args.purge_hours)
    test_keep = test_times < test_cutoff
    n3 = (~test_keep).sum()
    test_purged = test[test_keep].copy()

    print(f"Purged: train -{n1}, val -{n2}, test tail -{n3}")
    print(f"New sizes: train={len(train_purged)} val={len(val_purged)} test={len(test_purged)}")

    output_dir = args.output_dir or os.path.dirname(args.train)
    os.makedirs(output_dir, exist_ok=True)
    for name, df in [('train', train_purged), ('validation', val_purged), ('test', test_purged)]:
        path = os.path.join(output_dir, f'Nero_{name}_labeled.csv')
        df.to_csv(path, sep=';', index=False)
        print(f"Saved: {path}")


if __name__ == '__main__':
    main()
