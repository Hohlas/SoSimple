# =============================================================================
# File: ML/baseline/diagnose_walk_forward.py
# Purpose: Stage 5.1 DIAGNOSTIC_ONLY — walk-forward optimization diagnostics.
#           Tests whether extending training data rescues val_eval profitability
#           after Stage 4.6 val_eval failure (PF=0.897, trail_atr_0_2 on 2023-2026).
# Variants:
#   1. Expanding Window  — train ≤T, all tested on 2023-2026 (Nero.csv)
#   2. Anchored WFO       — train ≤T, test T+1..T+2
#   3. Rolling 10yr       — train [T-10, T], test T+1..T+2
#   4. Warm-start         — sequential refit on expanding data, test 2023-2026
# Input:  DATA/Nero_XAUUSD_*_labeled.csv, MT/MQL4/Files/Nero.csv,
#         DATA/XAUUSD_H1_OHLC.csv
# Output: ML/reports/walk_forward_diagnostics.json
# Status: DIAGNOSTIC_ONLY — no test, no winner, walk-forward exploration only
# Language: Python 3.10+
# Created: 2026-06-15
# =============================================================================

import argparse, json, os, sys
from collections import Counter
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import xgboost as xgb

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from processing.label_signals import load_ohlc_index

from ML.baseline.diagnose_stage4_3 import (
    profile_base_raw,
    profile_base_raw_plus_time,
    compute_entry_prices,
    train_rf_fav,
    compute_trade_metrics,
    block_bootstrap_pf,
    BREACH_TARGETS,
    FAV_TARGETS,
    CAP,
)

from ML.baseline.diagnose_stage4_5_exit_mechanics import (
    simulate_trades_with_policy,
)

CANONICAL_SPREAD = 0.20
WINNER_TARGET = 'sell_H6_off05'
WINNER_H = 6
WINNER_OFF = 0.5
WINNER_SIDE = 'sell'
BASELINE_P = 0.4
BASELINE_MIN_FAV = 0.3
BASELINE_MIN_RR = 1.0
WARMSTART_EXTRA_TREES = 50

TRAIL_CFG = {'policy': 'trailing', 'r_value': 0.7, 'trail_atr': 0.2}
TRAIL_TP_KIND = 'fixed_r'

WINDOWS = [
    {'name': 'w1', 'train_to': 2016, 'test_from': 2017, 'test_to': 2018},
    {'name': 'w2', 'train_to': 2018, 'test_from': 2019, 'test_to': 2020},
    {'name': 'w3', 'train_to': 2020, 'test_from': 2021, 'test_to': 2022},
    {'name': 'w4', 'train_to': 2022, 'test_from': 2023, 'test_to': 2026},
]


def _safe(v):
    if isinstance(v, (np.floating,)):
        return float(v)
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (float,)) and not np.isfinite(v):
        return None
    return v


# ===========================================================================
# Data loading
# ===========================================================================

def _load_csv(path):
    df = pd.read_csv(path, sep=';')
    df['_year'] = pd.to_datetime(
        df['time'], format='%Y.%m.%d %H:%M', errors='coerce').dt.year
    return df


def load_labeled_all(train_path, val_path):
    return pd.concat([_load_csv(train_path), _load_csv(val_path)],
                     ignore_index=True)


def load_nero_all(nero_path):
    return _load_csv(nero_path)


def year_mask(df, year_from, year_to):
    mask = pd.Series(True, index=df.index)
    if year_from is not None:
        mask &= df['_year'] >= year_from
    if year_to is not None:
        mask &= df['_year'] <= year_to
    return mask


def slice_by_year(df, year_from, year_to):
    """Return df subset with original index preserved."""
    return df.loc[year_mask(df, year_from, year_to)].copy()


def slice_by_year_reset(df, year_from, year_to):
    """Return df subset with reset index."""
    return df.loc[year_mask(df, year_from, year_to)].reset_index(drop=True)


# ===========================================================================
# Precomputed features + entry prices (once per full dataset)
# ===========================================================================

def precompute_features(df):
    X_b, _ = profile_base_raw_plus_time(df)
    X_f, _ = profile_base_raw(df)
    return X_b, X_f


def precompute_entry_map(df, ohlc, times, time_idx):
    return compute_entry_prices(df, ohlc, times, time_idx)


# ===========================================================================
# Model training
# ===========================================================================

def train_xgb_breach_selfval(X, y, seed=42):
    rng = np.random.RandomState(seed)
    n = len(X)
    idx = rng.permutation(n)
    n_val = max(1, n // 5)
    train_idx = idx[n_val:]
    val_idx = idx[:n_val]

    neg = int((y[train_idx] == 0).sum())
    pos = int((y[train_idx] == 1).sum())
    scale_pos_weight = neg / pos if pos > 0 else 1.0

    model = xgb.XGBClassifier(
        n_estimators=200, max_depth=6, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8,
        scale_pos_weight=scale_pos_weight,
        objective='binary:logistic', eval_metric='auc',
        early_stopping_rounds=20, random_state=seed,
        n_jobs=-1, verbosity=0,
    )
    model.fit(X[train_idx], y[train_idx],
              eval_set=[(X[val_idx], y[val_idx])],
              verbose=False)
    return model


def warmstart_xgb(base_model, X, y, seed=42):
    rng = np.random.RandomState(seed)
    n = len(X)
    idx = rng.permutation(n)
    n_val = max(1, n // 5)
    train_idx = idx[n_val:]
    val_idx = idx[:n_val]

    neg = int((y[train_idx] == 0).sum())
    pos = int((y[train_idx] == 1).sum())
    scale_pos_weight = neg / pos if pos > 0 else 1.0

    new_model = xgb.XGBClassifier(
        n_estimators=base_model.n_estimators + WARMSTART_EXTRA_TREES,
        max_depth=6, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8,
        scale_pos_weight=scale_pos_weight,
        objective='binary:logistic', eval_metric='auc',
        early_stopping_rounds=20, random_state=seed,
        n_jobs=-1, verbosity=0,
    )
    new_model.fit(X[train_idx], y[train_idx],
                  eval_set=[(X[val_idx], y[val_idx])],
                  xgb_model=base_model.get_booster(),
                  verbose=False)
    return new_model


def train_breach_fav(X_b, y_b, X_f, y_f, seed, prev_breach=None):
    mask_b = ~np.isnan(y_b)
    if prev_breach is not None:
        breach = warmstart_xgb(prev_breach, X_b[mask_b], y_b[mask_b], seed=seed)
    else:
        breach = train_xgb_breach_selfval(X_b[mask_b], y_b[mask_b], seed=seed)

    mask_f = ~np.isnan(y_f)
    fav = train_rf_fav(X_f[mask_f], y_f[mask_f], random_state=seed)
    return breach, fav


# ===========================================================================
# Simulation
# ===========================================================================

def simulate_on_df(df, entry_arr, breach_model, fav_model,
                   ohlc, times, time_idx, target_col, fav_col, spread):
    X_b_eval, _ = profile_base_raw_plus_time(df)
    X_f_eval, _ = profile_base_raw(df)

    eval_mask_b = ~pd.isna(df[target_col]).values if target_col in df.columns \
        else np.ones(len(df), dtype=bool)
    eval_mask_f = ~pd.isna(df[fav_col]).values if fav_col in df.columns \
        else np.ones(len(df), dtype=bool)
    inter = eval_mask_b & eval_mask_f

    if inter.sum() == 0:
        return [], {}

    bp = breach_model.predict_proba(X_b_eval[inter])[:, 1]
    fp = fav_model.predict(X_f_eval[inter])
    df_m = df[inter].reset_index(drop=True)
    ep_m = entry_arr[inter]

    trades = simulate_trades_with_policy(
        df_m, ep_m, bp, fp,
        ohlc, times, time_idx,
        WINNER_SIDE, WINNER_H, WINNER_OFF,
        BASELINE_P, BASELINE_MIN_FAV, BASELINE_MIN_RR,
        TRAIL_TP_KIND, TRAIL_CFG, CAP, spread)

    metrics = compute_trade_metrics(trades)
    bootstrap = block_bootstrap_pf(trades)

    return trades, {
        'pf': round(float(metrics['pf']), 3) if np.isfinite(metrics['pf']) else 0.0,
        'bs_p05': round(_safe(bootstrap.get('pf_p05')), 3) if bootstrap.get('pf_p05') is not None else None,
        'bs_median': round(_safe(bootstrap.get('pf_median')), 3) if bootstrap.get('pf_median') is not None else None,
        'n_trades': len(trades),
        'n_years': metrics.get('n_years', 0),
        'trades_per_year': round(float(metrics.get('trades_per_year', 0)), 1),
        'win_rate': round(float(metrics.get('win_rate', 0)), 1),
        'gross_profit': round(float(metrics.get('gross_profit', 0)), 3),
        'gross_loss': round(float(metrics.get('gross_loss', 0)), 3),
        'exits': dict(Counter(t['exit'] for t in trades)),
        'yearly_pf': {str(k): round(v['pf'], 3) if isinstance(v['pf'], float) else v['pf']
                      for k, v in metrics.get('yearly', {}).items()},
        'yearly_n': {str(k): v['n'] for k, v in metrics.get('yearly', {}).items()},
    }


def get_test_data(nero_full, labeled_full,
                  entry_nero, entry_labeled,
                  test_from, test_to):
    if test_from >= 2023:
        df = slice_by_year_reset(nero_full, test_from, test_to)
        mask = year_mask(nero_full, test_from, test_to)
        entry = entry_nero[mask.values]
        return df, entry, 'nero'
    else:
        df = slice_by_year_reset(labeled_full, test_from, test_to)
        mask = year_mask(labeled_full, test_from, test_to)
        entry = entry_labeled[mask.values]
        return df, entry, 'labeled'


# ===========================================================================
# Variant runners
# ===========================================================================

def run_expanding(windows, labeled_full, nero_full,
                  entry_nero,
                  models_cache,
                  ohlc, times, time_idx,
                  target_col, fav_col, spread):
    print(f'\n{"=" * 70}')
    print('VARIANT 1: Expanding Window (all tested on 2023-2026 Nero.csv)')
    print(f'{"=" * 70}')

    test_df, test_entry, _ = get_test_data(
        nero_full, None, entry_nero, None, 2023, 2026)

    results = []
    for wi, w in enumerate(windows):
        train_to = w['train_to']
        breach_model, fav_model = models_cache.get(train_to, (None, None))
        if breach_model is None:
            results.append({'name': f'exp_train<={train_to}',
                            'error': 'no_model', 'window': wi + 1})
            continue

        _, sim = simulate_on_df(
            test_df, test_entry, breach_model, fav_model,
            ohlc, times, time_idx, target_col, fav_col, spread)

        n_train = len(slice_by_year(labeled_full, None, train_to))
        sim['name'] = f'exp_train<={train_to}'
        sim['train_years'] = f'<={train_to}'
        sim['test_years'] = '2023-2026'
        sim['test_source'] = 'nero'
        sim['window'] = wi + 1
        sim['n_train_rows'] = n_train

        print(f'  [{sim["name"]}] n_train={n_train}  '
              f'PF={sim["pf"]}  BS_p05={sim["bs_p05"]}  '
              f'n_trades={sim["n_trades"]}  wr={sim["win_rate"]}%')
        results.append(sim)

    return results


def run_anchored(windows, labeled_full, nero_full,
                 entry_labeled, entry_nero,
                 models_cache,
                 ohlc, times, time_idx,
                 target_col, fav_col, spread):
    print(f'\n{"=" * 70}')
    print('VARIANT 2: Anchored WFO (anchor ≤earliest, test moves forward)')
    print(f'{"=" * 70}')

    results = []
    for wi, w in enumerate(windows):
        train_to = w['train_to']
        test_from, test_to = w['test_from'], w['test_to']

        breach_model, fav_model = models_cache.get(train_to, (None, None))
        if breach_model is None:
            results.append({'name': f'wfo_train<={train_to}_test{test_from}-{test_to}',
                            'error': 'no_model', 'window': wi + 1})
            continue

        test_df, test_entry, test_src = get_test_data(
            nero_full, labeled_full, entry_nero, entry_labeled, test_from, test_to)

        _, sim = simulate_on_df(
            test_df, test_entry, breach_model, fav_model,
            ohlc, times, time_idx, target_col, fav_col, spread)

        n_train = len(slice_by_year(labeled_full, None, train_to))
        sim['name'] = f'wfo_train<={train_to}_test{test_from}-{test_to}'
        sim['train_years'] = f'<={train_to}'
        sim['test_years'] = f'{test_from}-{test_to}'
        sim['test_source'] = test_src
        sim['window'] = wi + 1
        sim['n_train_rows'] = n_train

        print(f'  [{sim["name"]}] n_train={n_train}  '
              f'PF={sim["pf"]}  BS_p05={sim["bs_p05"]}  '
              f'n_trades={sim["n_trades"]}  wr={sim["win_rate"]}%')
        results.append(sim)

    return results


def run_rolling(windows, labeled_full, nero_full,
                entry_labeled, entry_nero,
                ohlc, times, time_idx,
                target_col, fav_col, spread, seed):
    ROLLING_YEARS = 10
    print(f'\n{"=" * 70}')
    print(f'VARIANT 3: Rolling Window ({ROLLING_YEARS}yr fixed, slides forward)')
    print(f'{"=" * 70}')

    results = []
    for wi, w in enumerate(windows):
        test_from, test_to = w['test_from'], w['test_to']
        train_from = test_from - ROLLING_YEARS
        train_to = test_from - 1

        train_df = slice_by_year_reset(labeled_full, train_from, train_to)
        if len(train_df) == 0:
            results.append({'name': f'rolling{train_from}-{train_to}_test{test_from}-{test_to}',
                            'error': 'empty_train', 'window': wi + 1})
            continue

        X_b, _ = profile_base_raw_plus_time(train_df)
        X_f, _ = profile_base_raw(train_df)
        y_b = train_df[target_col].values
        y_f = train_df[fav_col].values

        breach_model, fav_model = train_breach_fav(
            X_b, y_b, X_f, y_f, seed=seed + wi)

        test_df, test_entry, test_src = get_test_data(
            nero_full, labeled_full, entry_nero, entry_labeled, test_from, test_to)

        _, sim = simulate_on_df(
            test_df, test_entry, breach_model, fav_model,
            ohlc, times, time_idx, target_col, fav_col, spread)

        sim['name'] = f'rolling{train_from}-{train_to}_test{test_from}-{test_to}'
        sim['train_years'] = f'{train_from}-{train_to}'
        sim['test_years'] = f'{test_from}-{test_to}'
        sim['test_source'] = test_src
        sim['window'] = wi + 1
        sim['n_train_rows'] = len(train_df)

        print(f'  [{sim["name"]}] n_train={len(train_df)}  '
              f'PF={sim["pf"]}  BS_p05={sim["bs_p05"]}  '
              f'n_trades={sim["n_trades"]}  wr={sim["win_rate"]}%')
        results.append(sim)

    return results


def run_warmstart(windows, labeled_full, nero_full,
                  entry_labeled, entry_nero,
                  ohlc, times, time_idx,
                  target_col, fav_col, spread, seed):
    print(f'\n{"=" * 70}')
    print('VARIANT 4: XGBoost Warm-start (sequential refit, test 2023-2026)')
    print(f'{"=" * 70}')

    test_df, test_entry, _ = get_test_data(
        nero_full, None, entry_nero, None, 2023, 2026)

    results = []
    prev_breach = None

    for wi, w in enumerate(windows):
        train_to = w['train_to']
        train_df = slice_by_year_reset(labeled_full, None, train_to)
        if len(train_df) == 0:
            results.append({'name': f'warm_train<={train_to}',
                            'error': 'empty_train', 'window': wi + 1})
            continue

        X_b, _ = profile_base_raw_plus_time(train_df)
        X_f, _ = profile_base_raw(train_df)
        y_b = train_df[target_col].values
        y_f = train_df[fav_col].values

        breach_model, fav_model = train_breach_fav(
            X_b, y_b, X_f, y_f, seed=seed + wi, prev_breach=prev_breach)

        _, sim = simulate_on_df(
            test_df, test_entry, breach_model, fav_model,
            ohlc, times, time_idx, target_col, fav_col, spread)

        kind = 'warmstart' if prev_breach is not None else 'fresh'
        sim['name'] = f'warm_train<={train_to}'
        sim['kind'] = kind
        sim['train_years'] = f'<={train_to}'
        sim['test_years'] = '2023-2026'
        sim['test_source'] = 'nero'
        sim['window'] = wi + 1
        sim['n_train_rows'] = len(train_df)
        sim['trees'] = breach_model.n_estimators

        print(f'  [{sim["name"]}] kind={kind} trees={breach_model.n_estimators}  '
              f'n_train={len(train_df)}  PF={sim["pf"]}  '
              f'BS_p05={sim["bs_p05"]}  n_trades={sim["n_trades"]}')
        results.append(sim)

        prev_breach = breach_model

    return results


# ===========================================================================
# Main
# ===========================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Stage 5.1 DIAGNOSTIC_ONLY walk-forward diagnostics')
    parser.add_argument('--train', default='DATA/Nero_XAUUSD_train_labeled.csv')
    parser.add_argument('--val', default='DATA/Nero_XAUUSD_validation_labeled.csv')
    parser.add_argument('--nero', default='MT/MQL4/Files/Nero.csv')
    parser.add_argument('--ohlc', default='DATA/XAUUSD_H1_OHLC.csv')
    parser.add_argument('--output', default='ML/reports/walk_forward_diagnostics.json')
    parser.add_argument('--spread', type=float, default=CANONICAL_SPREAD)
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()

    h, off, side = WINNER_H, WINNER_OFF, WINNER_SIDE
    target_col = BREACH_TARGETS[h][off][side]
    fav_col = FAV_TARGETS[h][side]

    print('=' * 70)
    print('Stage 5.1: DIAGNOSTIC_ONLY — Walk-Forward Optimization Diagnostics')
    print('=' * 70)
    print(f'  Target: {WINNER_TARGET}  (h={h}, off={off}, side={side})')
    print(f'  Exit: trail_atr_0_2  (R=0.7, trail_atr=0.2)')
    print(f'  Spread: {args.spread}  Seed: {args.seed}')
    t0 = datetime.now()

    print('\nLoading data...', flush=True)
    ohlc, times, time_idx = load_ohlc_index(args.ohlc)
    labeled_full = load_labeled_all(args.train, args.val)
    nero_full = load_nero_all(args.nero)

    print(f'  Labeled: {len(labeled_full)} rows  '
          f'({int(labeled_full["_year"].min())}-{int(labeled_full["_year"].max())})')
    print(f'  Nero: {len(nero_full)} rows  '
          f'({int(nero_full["_year"].min())}-{int(nero_full["_year"].max())})')
    print(f'  OHLC: {len(times)} bars')

    print('\nPrecomputing features...', flush=True)
    feat_labeled_b, feat_labeled_f = precompute_features(labeled_full)
    print(f'  Labeled: breach={feat_labeled_b.shape}, fav={feat_labeled_f.shape}'
          f'  ({datetime.now() - t0})', flush=True)
    feat_nero_b, feat_nero_f = precompute_features(nero_full)
    print(f'  Nero:    breach={feat_nero_b.shape}, fav={feat_nero_f.shape}'
          f'  ({datetime.now() - t0})', flush=True)

    print('\nPrecomputing entry prices...', flush=True)
    entry_labeled = precompute_entry_map(labeled_full, ohlc, times, time_idx)
    entry_nero = precompute_entry_map(nero_full, ohlc, times, time_idx)
    print(f'  Done. ({datetime.now() - t0})', flush=True)

    print('\nTraining base models...', flush=True)
    models_cache = {}
    for w in WINDOWS:
        train_to = w['train_to']
        print(f'  Train ≤{train_to}...', flush=True)
        train_sub = slice_by_year(labeled_full, None, train_to)
        idx = train_sub.index.values.astype(int)
        X_b = feat_labeled_b[idx]
        X_f = feat_labeled_f[idx]
        y_b = train_sub[target_col].values
        y_f = train_sub[fav_col].values

        breach, fav = train_breach_fav(X_b, y_b, X_f, y_f, seed=args.seed)
        models_cache[train_to] = (breach, fav)
    print(f'  All base models trained. ({datetime.now() - t0})', flush=True)

    results = {}
    results['expanding'] = run_expanding(
        WINDOWS, labeled_full, nero_full,
        entry_nero,
        models_cache,
        ohlc, times, time_idx,
        target_col, fav_col, args.spread)

    results['anchored_wfo'] = run_anchored(
        WINDOWS, labeled_full, nero_full,
        entry_labeled, entry_nero,
        models_cache,
        ohlc, times, time_idx,
        target_col, fav_col, args.spread)

    results['rolling_10yr'] = run_rolling(
        WINDOWS, labeled_full, nero_full,
        entry_labeled, entry_nero,
        ohlc, times, time_idx,
        target_col, fav_col, args.spread, args.seed)

    results['warmstart'] = run_warmstart(
        WINDOWS, labeled_full, nero_full,
        entry_labeled, entry_nero,
        ohlc, times, time_idx,
        target_col, fav_col, args.spread, args.seed)

    output = {
        'status': 'DIAGNOSTIC_ONLY',
        'source': 'Stage 4.6 val_eval failure (PF=0.897) -> do expanding data rescue?',
        'config': {
            'target': WINNER_TARGET,
            'exit_policy': 'trail_atr_0_2',
            'exit_cfg': TRAIL_CFG,
            'spread': args.spread,
            'seed': args.seed,
            'windows': WINDOWS,
            'duration_s': round((datetime.now() - t0).total_seconds(), 1),
        },
        'results': results,
        'interpretation_guards': [
            'DIAGNOSTIC_ONLY: no test opened, no winner selected',
            'Expanding/warm-start: all tested on 2023-2026 (Nero.csv, unlabeled)',
            'Anchored/rolling: each step tested on its own period (not cross-comparable)',
            'Warm-start adds 50 trees/step with self-validation (random 20% split)',
            'Walk-forward explores whether longer history rescues val_eval profit',
        ],
    }

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(output, f, indent=2, default=str)
    print(f'\nSaved: {args.output}')
    print(f'Total time: {datetime.now() - t0}')
    print('DIAGNOSTIC_ONLY — complete.')


if __name__ == '__main__':
    main()
