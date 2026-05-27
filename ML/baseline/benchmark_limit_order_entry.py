#!/usr/bin/env python3
"""
RF/HGB Baseline для limit-order entry convention.
Проверяет edge на уровне простых моделей перед инвестициями в Transformer.

Gate: PF >= 1.3 AND fill_rate >= 20% AND trades/year >= 6 AND negative_years == 0.
Uses _pnl_r columns (R-multiple PnL including timeout).

Использование:
  .venv/bin/python -m ML.baseline.benchmark_limit_order_entry \
    --train DATA/limit_order/Nero_train_labeled.csv \
    --val DATA/limit_order/Nero_validation_labeled.csv \
    --target buy_sl3_tp3
"""

import argparse
import os
import sys
import warnings
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from collections import defaultdict

warnings.filterwarnings('ignore')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'processing'))
from label_signals import (
    TB_TARGET_NAMES, LIMIT_NO_FILL_SENTINEL, LIMIT_AMBIGUOUS_SENTINEL,
)


def parse_fractal_to_features(df, max_levels=100):
    """Извлечь плоские признаки из fractal0..fractal99."""
    feature_list = []
    feature_names = []

    for level in range(max_levels):
        col = f'fractal{level}'
        if col not in df.columns:
            break

        prices = []
        dirs = []

        for val in df[col]:
            try:
                parts = str(val).split(':')
                if len(parts) >= 4:
                    prices.append(float(parts[2]))
                    dirs.append(float(parts[3]))
                else:
                    prices.append(np.nan)
                    dirs.append(np.nan)
            except (ValueError, IndexError):
                prices.append(np.nan)
                dirs.append(np.nan)

        feature_list.append(np.array(prices, dtype=np.float64))
        feature_names.append(f'f{level}_price')

        if level == 0:
            feature_list.append(np.array(dirs, dtype=np.float64))
            feature_names.append('f0_dir')

    if 'ATR' in df.columns:
        feature_list.append(df['ATR'].values.astype(np.float64))
        feature_names.append('ATR')

    X = np.column_stack([f for f in feature_list if len(f) > 0])
    X = np.nan_to_num(X, nan=0.0)
    return X, feature_names


def compute_pf(pnl_values):
    """Profit Factor: gross_profit / gross_loss (R-multiples)."""
    pnl = np.asarray(pnl_values, dtype=np.float64)
    gross_profit = float(pnl[pnl > 0].sum())
    gross_loss = float(-pnl[pnl < 0].sum())
    if gross_loss == 0:
        return float('inf') if gross_profit > 0 else 0.0
    return gross_profit / gross_loss


def evaluate_threshold(scores, pnl_values, fill_mask, time_col, threshold=None):
    """Выбрать сигналы по threshold. PF по _pnl_r значениям."""
    n = len(scores)
    selected = scores >= threshold if threshold is not None else np.ones(n, dtype=bool)

    n_selected = selected.sum()
    if n_selected == 0:
        return {'pf': 0, 'n_selected': 0, 'n_filled': 0, 'fill_rate': 0,
                'mean_r_signal': 0, 'mean_r_trade': 0, 'trades_per_year': 0,
                'negative_years': 0}

    selected_fill = selected & fill_mask
    n_filled = selected_fill.sum()

    if n_filled > 0:
        filled_pnl = pnl_values[selected_fill]
        pf_val = compute_pf(filled_pnl)
        mean_r_trade = float(np.mean(filled_pnl))
    else:
        pf_val = 0.0
        mean_r_trade = 0.0

    mean_r_signal = pnl_values[selected_fill].sum() / n_selected if n_selected > 0 else 0.0
    fill_rate_val = n_filled / n_selected if n_selected > 0 else 0.0

    if time_col is not None and n_filled > 0:
        filled_times = time_col[selected_fill]
        filled_pnl_series = pd.Series(pnl_values[selected_fill], index=filled_times.index)
        yearly_pnl = filled_pnl_series.groupby(filled_times.dt.year).sum()
        negative_years_val = int((yearly_pnl < 0).sum())
        total_years = (time_col.max() - time_col.min()).days / 365.25
        tpy = n_filled / max(total_years, 0.5)
    else:
        negative_years_val = 0
        tpy = 0.0

    return {
        'pf': pf_val,
        'n_selected': int(n_selected),
        'n_filled': int(n_filled),
        'fill_rate': fill_rate_val,
        'mean_r_signal': mean_r_signal,
        'mean_r_trade': mean_r_trade,
        'trades_per_year': tpy,
        'negative_years': negative_years_val,
    }


def threshold_sweep(scores, pnl_values, fill_mask, time_col, n_thresholds=50):
    """Перебор порогов на ВСЕХ validation строках (no fill pre-filtering)."""
    results = []
    unique = np.sort(np.unique(scores))
    if len(unique) <= n_thresholds:
        thresholds = unique
    else:
        indices = np.linspace(0, len(unique) - 1, n_thresholds, dtype=int)
        thresholds = unique[indices]

    for thr in thresholds:
        metrics = evaluate_threshold(scores, pnl_values, fill_mask, time_col, threshold=thr)
        metrics['threshold'] = thr
        results.append(metrics)

    return results


def main():
    parser = argparse.ArgumentParser(description="Limit-order RF/HGB baseline")
    parser.add_argument('--train', default='DATA/limit_order/Nero_train_labeled.csv')
    parser.add_argument('--val', default='DATA/limit_order/Nero_validation_labeled.csv')
    parser.add_argument('--target', default='buy_sl3_tp3')
    parser.add_argument('--purge-hours', type=int, default=30)
    args = parser.parse_args()

    target_side = 'buy' if args.target.startswith('buy_') else 'sell'
    pnl_col = f'{args.target}_pnl_r'
    fill_lag_col = f'{target_side}_fill_lag'

    print(f"Target: {args.target}  side: {target_side}  PnL col: {pnl_col}")

    train_df = pd.read_csv(args.train, sep=';')
    val_df = pd.read_csv(args.val, sep=';')

    train_fill = train_df[fill_lag_col] >= 0
    train_rows = train_df[train_fill].copy()
    val_fill_mask = (val_df[fill_lag_col] >= 0).values

    print(f"Train (fill-only): {len(train_rows)}  Val (all): {len(val_df)}")

    if 'time' in train_rows.columns:
        train_times = pd.to_datetime(train_rows['time'])
        val_min_time = pd.to_datetime(val_df['time']).min()
        purge_mask = train_times + pd.Timedelta(hours=args.purge_hours) < val_min_time
        train_rows = train_rows[purge_mask].copy()
        print(f"Train after purge: {len(train_rows)}")

    X_train, fnames = parse_fractal_to_features(train_rows)
    X_val, _ = parse_fractal_to_features(val_df)

    y_train = train_rows[args.target].values.astype(np.float64)
    pnl_val = val_df[pnl_col].values.astype(np.float64)
    time_val = pd.to_datetime(val_df['time'])

    from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor

    models = {
        'RF': RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1),
        'HGB': HistGradientBoostingRegressor(max_iter=100, max_depth=6, random_state=42),
    }

    gate_pass = False
    best_result = None

    for name, model in models.items():
        print(f"\n{'='*60}")
        print(f"Training {name} with {len(X_train)} rows, {X_train.shape[1]} features ...")
        model.fit(X_train, y_train)
        scores = model.predict(X_val)

        results = threshold_sweep(scores, pnl_val, val_fill_mask, time_val)

        valid = [r for r in results
                 if r['fill_rate'] >= 0.20
                 and r['trades_per_year'] >= 6
                 and r['negative_years'] == 0]
        if valid:
            best = max(valid, key=lambda r: r['pf'])
            best['model'] = name
            print(f"  Best threshold: {best['threshold']:.4f}")
            print(f"  PF={best['pf']:.3f}  fill_rate={best['fill_rate']:.1%}  "
                  f"trades/yr={best['trades_per_year']:.1f}  "
                  f"selected={best['n_selected']}  filled={best['n_filled']}  "
                  f"neg_years={best['negative_years']}")
            print(f"  mean_R/signal={best['mean_r_signal']:.3f}  "
                  f"mean_R/trade={best['mean_r_trade']:.3f}")
            if best['pf'] >= 1.3:
                gate_pass = True
                if best_result is None or best['pf'] > best_result['pf']:
                    best_result = best
        else:
            best_pf = max(results, key=lambda r: r['pf'])
            best_fr = max(results, key=lambda r: r['fill_rate'])
            print(f"  No threshold passes all gates.")
            print(f"  Max PF={best_pf['pf']:.3f} (fr={best_pf['fill_rate']:.1%}, "
                  f"t/yr={best_pf['trades_per_year']:.1f}, neg={best_pf['negative_years']})")
            print(f"  Max fill_rate: {best_fr['fill_rate']:.1%}")

    print(f"\n{'='*60}")
    if gate_pass and best_result:
        print(f"GATE PASS: {best_result['model']} PF={best_result['pf']:.3f} >= 1.3, "
              f"fill_rate={best_result['fill_rate']:.1%} >= 20%, "
              f"negative_years={best_result['negative_years']}")
        print("-> Proceed to Phase 3 (Transformer).")
    else:
        print("GATE FAIL.")
        print("-> Limit-order hypothesis NOT confirmed at baseline level. Stop.")


if __name__ == '__main__':
    main()
