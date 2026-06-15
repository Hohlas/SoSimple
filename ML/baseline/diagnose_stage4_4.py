# =============================================================================
# File: ML/baseline/diagnose_stage4_4.py
# Purpose: Stage 4.4 DIAGNOSTIC_ONLY micro-check before Transformer Stage 5.0.
#           Three experiments: relax breach p=0.5, fixed TP, breach-only entry.
#           No test, no winner selection, no new model training.
# Input:  DATA/Nero_XAUUSD_*_labeled.csv, DATA/XAUUSD_H1_OHLC.csv
# Output: ML/reports/stage4_4_micro_check.json
# Status: DIAGNOSTIC_ONLY — no test, no winner selection, no new model training
# Language: Python 3.10+
# Created: 2026-06-15
# =============================================================================

import argparse, json, os, sys
from collections import Counter
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from processing.label_signals import load_ohlc_index

from ML.baseline.diagnose_stage4_3 import (
    load_splits,
    profile_base_raw,
    profile_base_raw_plus_time,
    compute_entry_prices,
    train_xgb_breach,
    train_rf_fav,
    simulate_trades,
    resolve_tp_val,
    compute_trade_metrics,
    compute_yearly_metrics,
    loss_attribution,
    block_bootstrap_pf,
    BREACH_TARGETS,
    FAV_TARGETS,
    CAP,
    BLOCK_BOOTSTRAP_SIZE,
    N_BOOTSTRAP,
    TRAIN_MAX_YEAR,
    VAL_STOP_YEARS,
    VAL_EVAL_MIN_YEAR,
)

CANONICAL_SPREAD = 0.20
BASELINE_P = 0.4
BASELINE_MIN_FAV = 0.3
BASELINE_MIN_RR = 1.0
BASELINE_TP_FRACTION = 0.4
WINNER_H = 6
WINNER_OFF = 0.5
WINNER_SIDE = 'sell'
WINNER_TARGET = 'sell_H6_off05'
BASELINE_PF = 1.015
BASELINE_N_TRADES = 503
BASELINE_BS_MEDIAN = 0.996
BASELINE_BS_P05 = 0.837
PERMUTATION_ITER = 500
FIXED_TP_R_VALUES = [0.5, 0.7, 1.0]


def _safe(v):
    if isinstance(v, (np.floating,)):
        return float(v)
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (float,)) and not np.isfinite(v):
        return None
    return v


def run_simulation_and_metrics(df_val, entry_prices, breach_proba, fav_pred,
                               ohlc, times, time_idx,
                               side, h, stop_offset,
                               p, min_fav_val, min_rr, tp_fraction,
                               tp_policy, tp_policy_value,
                               skip_min_fav, skip_min_rr,
                               cap, spread):
    trades = simulate_trades(
        df=df_val, entry_prices=entry_prices,
        breach_proba=breach_proba, fav_pred=fav_pred,
        ohlc=ohlc, times=times, time_idx=time_idx,
        side=side, h=h, stop_offset=stop_offset,
        p=p, min_fav_val=min_fav_val, min_rr=min_rr,
        tp_fraction=tp_fraction, cap=cap, spread=spread,
        return_details=True,
        tp_policy=tp_policy, tp_policy_value=tp_policy_value,
        skip_min_fav=skip_min_fav, skip_min_rr=skip_min_rr,
    )
    metrics = compute_trade_metrics(trades)
    yearly = compute_yearly_metrics(trades)
    bootstrap = block_bootstrap_pf(trades)
    exits = Counter(t['exit'] for t in trades)
    n = len(trades)
    wins = [t for t in trades if t['pnl_val'] > 0]
    losses = [t for t in trades if t['pnl_val'] < 0]
    avg_win_atr = np.mean([t['pnl_val'] for t in wins]) if wins else 0
    avg_loss_atr = np.mean([abs(t['pnl_val']) for t in losses]) if losses else 0
    pnl_r_values = []
    for t in trades:
        sv = t.get('stop_val', 1.0)
        pnl_r_values.append(t['pnl_val'] / sv if sv > 0 else t['pnl_val'])
    pnl_r_arr = np.array(pnl_r_values)
    avg_win_r = np.mean(pnl_r_arr[pnl_r_arr > 0]) if (pnl_r_arr > 0).any() else 0
    avg_loss_r = np.mean(np.abs(pnl_r_arr[pnl_r_arr < 0])) if (pnl_r_arr < 0).any() else 0
    rr_values = [t.get('actual_rr', np.nan) for t in trades if 'actual_rr' in t]
    rr_arr = np.array([v for v in rr_values if not np.isnan(v)])

    cell = {
        'pf': metrics['pf'],
        'n_trades': n,
        'trades_per_year': metrics.get('trades_per_year', 0),
        'n_years': metrics.get('n_years', 0),
        'yearly_pf': {str(k): v['pf'] for k, v in yearly.items()},
        'yearly_n': {str(k): v['n'] for k, v in yearly.items()},
        'bs_median': bootstrap.get('pf_median'),
        'bs_p05': bootstrap.get('pf_p05'),
        'bs_p95': bootstrap.get('pf_p95'),
        'gross_profit': round(float(metrics.get('gross_profit', 0)), 3),
        'gross_loss': round(float(metrics.get('gross_loss', 0)), 3),
        'win_rate': round(float(metrics.get('win_rate', 0)), 1),
        'avg_win_atr': round(float(avg_win_atr), 3),
        'avg_loss_atr': round(float(avg_loss_atr), 3),
        'avg_win_r': round(float(avg_win_r), 3),
        'avg_loss_r': round(float(avg_loss_r), 3),
        'tp_n': exits.get('TP', 0),
        'sl_n': exits.get('SL', 0),
        'timeout_n': exits.get('TIMEOUT', 0),
        'ambiguous_n': sum(1 for t in trades if t.get('ambiguous', 0)),
        'tp_pct': round(exits.get('TP', 0) / n * 100, 1) if n else 0,
        'sl_pct': round(exits.get('SL', 0) / n * 100, 1) if n else 0,
        'timeout_pct': round(exits.get('TIMEOUT', 0) / n * 100, 1) if n else 0,
        'rr_mean': round(float(np.mean(rr_arr)), 4) if len(rr_arr) > 0 else None,
        'rr_median': round(float(np.median(rr_arr)), 4) if len(rr_arr) > 0 else None,
        'rr_p05': round(float(np.percentile(rr_arr, 5)), 4) if len(rr_arr) >= 20 else None,
        'rr_p95': round(float(np.percentile(rr_arr, 95)), 4) if len(rr_arr) >= 20 else None,
        'trades': trades,
    }
    return cell


def run_permutation_test(df_val, entry_prices, base_breach_proba, fav_pred,
                         ohlc, times, time_idx,
                         side, h, stop_offset,
                         p, min_fav_val, min_rr, tp_fraction,
                         tp_policy, tp_policy_value,
                         skip_min_fav, skip_min_rr,
                         cap, spread, observed_pf,
                         n_iter=PERMUTATION_ITER, seed=42):
    rng = np.random.RandomState(seed)
    perm_pfs = []
    perm_n_trades = []
    for _ in range(n_iter):
        perm_breach = rng.permutation(base_breach_proba.copy())
        perm_trades = simulate_trades(
            df=df_val, entry_prices=entry_prices,
            breach_proba=perm_breach, fav_pred=fav_pred,
            ohlc=ohlc, times=times, time_idx=time_idx,
            side=side, h=h, stop_offset=stop_offset,
            p=p, min_fav_val=min_fav_val, min_rr=min_rr,
            tp_fraction=tp_fraction, cap=cap, spread=spread,
            return_details=False,
            tp_policy=tp_policy, tp_policy_value=tp_policy_value,
            skip_min_fav=skip_min_fav, skip_min_rr=skip_min_rr,
        )
        pm = compute_trade_metrics(perm_trades)
        perm_pf = pm['pf']
        perm_pfs.append(perm_pf if np.isfinite(perm_pf) else 0.0)
        perm_n_trades.append(pm['n_trades'])
    perm_pfs_arr = np.array(perm_pfs)
    perm_n_arr = np.array(perm_n_trades)
    count_ge = int((perm_pfs_arr >= observed_pf).sum())
    return {
        'n_iter': n_iter,
        'observed_pf': round(float(observed_pf), 3),
        'perm_median_pf': round(float(np.median(perm_pfs_arr)), 3),
        'perm_max_pf': round(float(np.max(perm_pfs_arr)), 3),
        'perm_p05_pf': round(float(np.percentile(perm_pfs_arr, 5)), 3),
        'perm_p95_pf': round(float(np.percentile(perm_pfs_arr, 95)), 3),
        'n_perm_ge_observed': count_ge,
        'p_value_conservative': (count_ge + 1) / (n_iter + 1),
        'perm_n_trades_mean': round(float(np.mean(perm_n_arr)), 1),
    }


def compare_trades_added(baseline_trades, experiment_trades, name):
    baseline_indices = set(t.get('row_index') for t in baseline_trades
                           if 'row_index' in t and t['row_index'] is not None)
    experiment_indices = set(t.get('row_index') for t in experiment_trades
                             if 'row_index' in t and t['row_index'] is not None)
    added = experiment_indices - baseline_indices
    removed = baseline_indices - experiment_indices
    n_added = len(added)
    n_removed = len(removed)
    oracle_safe = 0
    oracle_bad = 0
    for t in experiment_trades:
        if t.get('row_index') in added:
            if t.get('breach_flag_true', 0) == 0:
                oracle_safe += 1
            else:
                oracle_bad += 1
    return {
        'n_added': n_added,
        'n_removed': n_removed,
        'added_oracle_safe': oracle_safe,
        'added_oracle_bad': oracle_bad,
        'added_safe_ratio': round(oracle_safe / n_added, 3) if n_added > 0 else None,
    }


def main():
    parser = argparse.ArgumentParser(description='Stage 4.4 DIAGNOSTIC_ONLY micro-check')
    parser.add_argument('--train', default='DATA/Nero_XAUUSD_train_labeled.csv')
    parser.add_argument('--val', default='DATA/Nero_XAUUSD_validation_labeled.csv')
    parser.add_argument('--ohlc', default='DATA/XAUUSD_H1_OHLC.csv')
    parser.add_argument('--output', default='ML/reports/stage4_4_micro_check.json')
    parser.add_argument('--spread', type=float, default=CANONICAL_SPREAD)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--n-bootstrap', type=int, default=N_BOOTSTRAP)
    parser.add_argument('--n-permutation', type=int, default=PERMUTATION_ITER)
    args = parser.parse_args()

    print('=' * 70)
    print('Stage 4.4: DIAGNOSTIC_ONLY — micro-check before Transformer Stage 5.0')
    print('=' * 70)
    print(f'  Target: {WINNER_TARGET}')
    print(f'  Source: docs/audit/next.md')
    print(f'  Spread={args.spread} (OHLC=Bid)  seed={args.seed}')
    print()

    # ---- Data ----
    print('Loading data...')
    train_df, val_stop_df, val_eval_df = load_splits(args.train, args.val)
    print(f'  Train (<=2016): {len(train_df)}')
    print(f'  Val-stop (2017-2018): {len(val_stop_df)}')
    print(f'  Val-eval (>=2019): {len(val_eval_df)}')

    ohlc, times, time_idx = load_ohlc_index(args.ohlc)
    entry_prices_val = compute_entry_prices(val_eval_df, ohlc, times, time_idx)

    # ---- Features ----
    X_train_breach, _ = profile_base_raw_plus_time(train_df)
    X_val_stop_breach, _ = profile_base_raw_plus_time(val_stop_df)
    X_val_eval_breach, _ = profile_base_raw_plus_time(val_eval_df)
    X_train_fav, _ = profile_base_raw(train_df)
    X_val_eval_fav, _ = profile_base_raw(val_eval_df)

    h, off, side = WINNER_H, WINNER_OFF, WINNER_SIDE
    target_col = BREACH_TARGETS[h][off][side]
    fav_col = FAV_TARGETS[h][side]

    # ---- Train models ----
    y_train_b = train_df[target_col].values
    y_stop_b = val_stop_df[target_col].values
    y_eval_b = val_eval_df[target_col].values
    train_mask_b = ~np.isnan(y_train_b)
    stop_mask_b = ~np.isnan(y_stop_b)
    eval_mask_b = ~np.isnan(y_eval_b)

    print(f'\nTraining XGBoost breach (train={train_mask_b.sum()}, '
          f'val_stop={stop_mask_b.sum()})...')
    breach_model = train_xgb_breach(
        X_train_breach[train_mask_b], y_train_b[train_mask_b],
        X_val_stop_breach[stop_mask_b], y_stop_b[stop_mask_b],
        random_state=args.seed)
    breach_proba = breach_model.predict_proba(X_val_eval_breach[eval_mask_b])[:, 1]
    breach_auc = roc_auc_score(y_eval_b[eval_mask_b], breach_proba)
    print(f'  Breach AUC val_eval: {breach_auc:.4f}  '
          f'iters={getattr(breach_model, "best_iteration", "?")}')

    y_train_f = train_df[fav_col].values
    y_eval_f = val_eval_df[fav_col].values
    train_mask_f = ~np.isnan(y_train_f)
    eval_mask_f = ~np.isnan(y_eval_f)

    print(f'Training RF fav (train={train_mask_f.sum()})...')
    fav_model = train_rf_fav(X_train_fav[train_mask_f], y_train_f[train_mask_f],
                             random_state=args.seed)
    fav_pred = fav_model.predict(X_val_eval_fav[eval_mask_f])

    # ---- Align ----
    intersection_mask = eval_mask_b & eval_mask_f
    n_valid = intersection_mask.sum()
    print(f'  Intersection valid: {n_valid}')

    breach_proba_aligned = breach_model.predict_proba(
        X_val_eval_breach[intersection_mask])[:, 1]
    fav_pred_aligned = fav_model.predict(X_val_eval_fav[intersection_mask])
    val_masked = val_eval_df[intersection_mask].reset_index(drop=True)
    entry_masked = entry_prices_val[intersection_mask]

    print(f'  Verifying breach AUC on val_eval aligned...')
    y_eval_b_aligned = y_eval_b[intersection_mask]
    breach_auc_check = roc_auc_score(y_eval_b_aligned, breach_proba_aligned)
    print(f'  Breach AUC val_eval aligned: {breach_auc_check:.4f}')
    if abs(breach_auc_check - 0.6674) > 0.001:
        print(f'  WARNING: Breach AUC {breach_auc_check:.4f} differs from '
              f'Stage 4.2 baseline (0.6674) by >0.001')

    # ---- Baseline verification ----
    print(f'\n{"=" * 70}')
    print('BASELINE VERIFICATION (Stage 4.2 reproduction)')
    print(f'{"=" * 70}')

    baseline = run_simulation_and_metrics(
        df_val=val_masked, entry_prices=entry_masked,
        breach_proba=breach_proba_aligned, fav_pred=fav_pred_aligned,
        ohlc=ohlc, times=times, time_idx=time_idx,
        side=side, h=h, stop_offset=off,
        p=BASELINE_P, min_fav_val=BASELINE_MIN_FAV, min_rr=BASELINE_MIN_RR,
        tp_fraction=BASELINE_TP_FRACTION,
        tp_policy='fav_fraction', tp_policy_value=BASELINE_TP_FRACTION,
        skip_min_fav=False, skip_min_rr=False,
        cap=CAP, spread=args.spread,
    )

    print(f'  PF={baseline["pf"]}  n={baseline["n_trades"]}  '
          f't/yr={baseline["trades_per_year"]}')
    print(f'  BS: median={baseline["bs_median"]}  '
          f'p05={baseline["bs_p05"]}  p95={baseline["bs_p95"]}')
    print(f'  GP={baseline["gross_profit"]}  GL={baseline["gross_loss"]}')
    print(f'  Win rate={baseline["win_rate"]}%')
    print(f'  TP={baseline["tp_n"]}  SL={baseline["sl_n"]}  '
          f'TIMEOUT={baseline["timeout_n"]}  Ambiguous={baseline["ambiguous_n"]}')
    for yr_str in sorted(baseline['yearly_pf'].keys()):
        yn = baseline['yearly_n'].get(yr_str, 0)
        ypf = baseline['yearly_pf'][yr_str]
        print(f'    {yr_str}: PF={ypf}  n={yn}')

    baseline_pf_ok = abs(baseline['pf'] - BASELINE_PF) < 0.001
    baseline_n_ok = baseline['n_trades'] == BASELINE_N_TRADES
    print(f'  Baseline PF match: {baseline_pf_ok}  '
          f'Baseline n match: {baseline_n_ok}')

    if not baseline_pf_ok or not baseline_n_ok:
        print('  WARNING: Baseline does not reproduce Stage 4.2!')
        print(f'    Expected PF={BASELINE_PF} n={BASELINE_N_TRADES}, '
              f'got PF={baseline["pf"]} n={baseline["n_trades"]}')
        print('  Continuing with actual baseline values...')

    # Baseline permutation test
    print(f'  Running permutation test on baseline...')
    baseline_perm = run_permutation_test(
        df_val=val_masked, entry_prices=entry_masked,
        base_breach_proba=breach_proba_aligned, fav_pred=fav_pred_aligned,
        ohlc=ohlc, times=times, time_idx=time_idx,
        side=side, h=h, stop_offset=off,
        p=BASELINE_P, min_fav_val=BASELINE_MIN_FAV, min_rr=BASELINE_MIN_RR,
        tp_fraction=BASELINE_TP_FRACTION,
        tp_policy='fav_fraction', tp_policy_value=BASELINE_TP_FRACTION,
        skip_min_fav=False, skip_min_rr=False,
        cap=CAP, spread=args.spread,
        observed_pf=baseline['pf'],
        n_iter=args.n_permutation,
    )
    baseline['permutation_test'] = baseline_perm
    baseline['params'] = {
        'p': BASELINE_P, 'min_fav_val': BASELINE_MIN_FAV,
        'min_rr': BASELINE_MIN_RR, 'tp_fraction': BASELINE_TP_FRACTION,
        'tp_policy': 'fav_fraction', 'tp_policy_value': BASELINE_TP_FRACTION,
        'skip_min_fav': False, 'skip_min_rr': False,
    }
    print(f'    Perm median PF: {baseline_perm["perm_median_pf"]}  '
          f'n_ge={baseline_perm["n_perm_ge_observed"]}  '
          f'p≈{baseline_perm["p_value_conservative"]:.3f}')

    # =====================================================================
    # Experiment 1: Relax breach p=0.5
    # =====================================================================
    print(f'\n{"=" * 70}')
    print('EXPERIMENT 1: Relax breach filter p=0.5')
    print(f'{"=" * 70}')

    exp1 = run_simulation_and_metrics(
        df_val=val_masked, entry_prices=entry_masked,
        breach_proba=breach_proba_aligned, fav_pred=fav_pred_aligned,
        ohlc=ohlc, times=times, time_idx=time_idx,
        side=side, h=h, stop_offset=off,
        p=0.5, min_fav_val=BASELINE_MIN_FAV, min_rr=BASELINE_MIN_RR,
        tp_fraction=BASELINE_TP_FRACTION,
        tp_policy='fav_fraction', tp_policy_value=BASELINE_TP_FRACTION,
        skip_min_fav=False, skip_min_rr=False,
        cap=CAP, spread=args.spread,
    )

    print(f'  PF={exp1["pf"]}  n={exp1["n_trades"]}  '
          f't/yr={exp1["trades_per_year"]}')
    print(f'  BS: median={exp1["bs_median"]}  p05={exp1["bs_p05"]}  '
          f'p95={exp1["bs_p95"]}')
    print(f'  GP={exp1["gross_profit"]}  GL={exp1["gross_loss"]}')
    print(f'  TP={exp1["tp_n"]}  SL={exp1["sl_n"]}  '
          f'TIMEOUT={exp1["timeout_n"]}')

    exp1_trades_added = compare_trades_added(
        baseline['trades'], exp1['trades'], 'relax_breach')
    print(f'  Trades added vs baseline: {exp1_trades_added["n_added"]}  '
          f'removed: {exp1_trades_added["n_removed"]}')
    print(f'  Added: oracle_safe={exp1_trades_added["added_oracle_safe"]}  '
          f'oracle_bad={exp1_trades_added["added_oracle_bad"]}  '
          f'safe_ratio={exp1_trades_added["added_safe_ratio"]}')

    exp1_delta = {
        'delta_pf': round(float(exp1['pf'] - baseline['pf']), 3),
        'delta_n_trades': exp1['n_trades'] - baseline['n_trades'],
        'delta_bs_p05': round(float((exp1.get('bs_p05') or 0) - (baseline.get('bs_p05') or 0)), 3),
    }

    print(f'  Running permutation test (p=0.5)...')
    exp1_perm = run_permutation_test(
        df_val=val_masked, entry_prices=entry_masked,
        base_breach_proba=breach_proba_aligned, fav_pred=fav_pred_aligned,
        ohlc=ohlc, times=times, time_idx=time_idx,
        side=side, h=h, stop_offset=off,
        p=0.5, min_fav_val=BASELINE_MIN_FAV, min_rr=BASELINE_MIN_RR,
        tp_fraction=BASELINE_TP_FRACTION,
        tp_policy='fav_fraction', tp_policy_value=BASELINE_TP_FRACTION,
        skip_min_fav=False, skip_min_rr=False,
        cap=CAP, spread=args.spread,
        observed_pf=exp1['pf'],
        n_iter=args.n_permutation,
    )
    exp1['permutation_test'] = exp1_perm
    exp1['trades_added_vs_baseline'] = exp1_trades_added
    exp1['delta_vs_baseline'] = exp1_delta
    exp1['params'] = {
        'p': 0.5, 'min_fav_val': BASELINE_MIN_FAV,
        'min_rr': BASELINE_MIN_RR, 'tp_fraction': BASELINE_TP_FRACTION,
        'tp_policy': 'fav_fraction', 'tp_policy_value': BASELINE_TP_FRACTION,
        'skip_min_fav': False, 'skip_min_rr': False,
    }
    print(f'    Perm median PF: {exp1_perm["perm_median_pf"]}  '
          f'n_ge={exp1_perm["n_perm_ge_observed"]}  '
          f'p≈{exp1_perm["p_value_conservative"]:.3f}')

    # =====================================================================
    # Experiment 2: Fixed TP with breach+fav filter
    # =====================================================================
    print(f'\n{"=" * 70}')
    print('EXPERIMENT 2: Fixed TP (breach+fav filter)')
    print(f'{"=" * 70}')

    exp2_results = []
    for R in FIXED_TP_R_VALUES:
        print(f'\n  R = {R}')
        cell = run_simulation_and_metrics(
            df_val=val_masked, entry_prices=entry_masked,
            breach_proba=breach_proba_aligned, fav_pred=fav_pred_aligned,
            ohlc=ohlc, times=times, time_idx=time_idx,
            side=side, h=h, stop_offset=off,
            p=BASELINE_P, min_fav_val=BASELINE_MIN_FAV, min_rr=BASELINE_MIN_RR,
            tp_fraction=BASELINE_TP_FRACTION,
            tp_policy='fixed_r', tp_policy_value=R,
            skip_min_fav=False, skip_min_rr=False,
            cap=CAP, spread=args.spread,
        )

        print(f'    PF={cell["pf"]}  n={cell["n_trades"]}  '
              f't/yr={cell["trades_per_year"]}')
        print(f'    BS: median={cell["bs_median"]}  p05={cell["bs_p05"]}  '
              f'p95={cell["bs_p95"]}')
        print(f'    GP={cell["gross_profit"]}  GL={cell["gross_loss"]}')
        print(f'    avg_win_r={cell["avg_win_r"]}  avg_loss_r={cell["avg_loss_r"]}')
        print(f'    RR mean={cell["rr_mean"]}  median={cell["rr_median"]}')
        print(f'    TP={cell["tp_n"]}  SL={cell["sl_n"]}  '
              f'TIMEOUT={cell["timeout_n"]}')

        cell_delta = {
            'delta_pf': round(float(cell['pf'] - baseline['pf']), 3),
            'delta_n_trades': cell['n_trades'] - baseline['n_trades'],
            'delta_bs_p05': round(float((cell.get('bs_p05') or 0) - (baseline.get('bs_p05') or 0)), 3),
            'delta_avg_win_r': round(float(cell['avg_win_r'] - baseline['avg_win_r']), 3),
            'delta_avg_loss_r': round(float(cell['avg_loss_r'] - baseline['avg_loss_r']), 3),
        }
        cell['delta_vs_baseline'] = cell_delta
        cell['params'] = {
            'p': BASELINE_P, 'min_fav_val': BASELINE_MIN_FAV,
            'min_rr': BASELINE_MIN_RR, 'tp_fraction': BASELINE_TP_FRACTION,
            'tp_policy': 'fixed_r', 'tp_policy_value': R,
            'skip_min_fav': False, 'skip_min_rr': False,
        }
        exp2_results.append(cell)

    # =====================================================================
    # Experiment 3: Breach-only + Fixed TP
    # =====================================================================
    print(f'\n{"=" * 70}')
    print('EXPERIMENT 3: Breach-only entry + Fixed TP')
    print(f'{"=" * 70}')

    exp3_results = []
    for R in FIXED_TP_R_VALUES:
        print(f'\n  R = {R}')
        cell = run_simulation_and_metrics(
            df_val=val_masked, entry_prices=entry_masked,
            breach_proba=breach_proba_aligned, fav_pred=fav_pred_aligned,
            ohlc=ohlc, times=times, time_idx=time_idx,
            side=side, h=h, stop_offset=off,
            p=BASELINE_P, min_fav_val=BASELINE_MIN_FAV, min_rr=BASELINE_MIN_RR,
            tp_fraction=BASELINE_TP_FRACTION,
            tp_policy='fixed_r', tp_policy_value=R,
            skip_min_fav=True, skip_min_rr=True,
            cap=CAP, spread=args.spread,
        )

        print(f'    PF={cell["pf"]}  n={cell["n_trades"]}  '
              f't/yr={cell["trades_per_year"]}')
        print(f'    BS: median={cell["bs_median"]}  p05={cell["bs_p05"]}  '
              f'p95={cell["bs_p95"]}')
        print(f'    GP={cell["gross_profit"]}  GL={cell["gross_loss"]}')
        print(f'    avg_win_r={cell["avg_win_r"]}  avg_loss_r={cell["avg_loss_r"]}')
        print(f'    RR mean={cell["rr_mean"]}  median={cell["rr_median"]}')
        print(f'    TP={cell["tp_n"]}  SL={cell["sl_n"]}  '
              f'TIMEOUT={cell["timeout_n"]}')

        # Trade comparison vs baseline
        trades_added_vs_baseline = compare_trades_added(
            baseline['trades'], cell['trades'], 'breach_only')
        print(f'    Trades added vs baseline: {trades_added_vs_baseline["n_added"]}  '
              f'removed: {trades_added_vs_baseline["n_removed"]}')
        print(f'    Added: oracle_safe={trades_added_vs_baseline["added_oracle_safe"]}  '
              f'oracle_bad={trades_added_vs_baseline["added_oracle_bad"]}  '
              f'safe_ratio={trades_added_vs_baseline["added_safe_ratio"]}')

        cell_delta = {
            'delta_pf': round(float(cell['pf'] - baseline['pf']), 3),
            'delta_n_trades': cell['n_trades'] - baseline['n_trades'],
            'delta_bs_p05': round(float((cell.get('bs_p05') or 0) - (baseline.get('bs_p05') or 0)), 3),
            'delta_avg_win_r': round(float(cell['avg_win_r'] - baseline['avg_win_r']), 3),
            'delta_avg_loss_r': round(float(cell['avg_loss_r'] - baseline['avg_loss_r']), 3),
        }
        cell['trades_added_vs_baseline'] = trades_added_vs_baseline
        cell['delta_vs_baseline'] = cell_delta
        cell['params'] = {
            'p': BASELINE_P, 'min_fav_val': BASELINE_MIN_FAV,
            'min_rr': BASELINE_MIN_RR, 'tp_fraction': BASELINE_TP_FRACTION,
            'tp_policy': 'fixed_r', 'tp_policy_value': R,
            'skip_min_fav': True, 'skip_min_rr': True,
        }

        # Permutation test for breach-only cells
        print(f'    Running permutation test...')
        cell_perm = run_permutation_test(
            df_val=val_masked, entry_prices=entry_masked,
            base_breach_proba=breach_proba_aligned, fav_pred=fav_pred_aligned,
            ohlc=ohlc, times=times, time_idx=time_idx,
            side=side, h=h, stop_offset=off,
            p=BASELINE_P, min_fav_val=BASELINE_MIN_FAV, min_rr=BASELINE_MIN_RR,
            tp_fraction=BASELINE_TP_FRACTION,
            tp_policy='fixed_r', tp_policy_value=R,
            skip_min_fav=True, skip_min_rr=True,
            cap=CAP, spread=args.spread,
            observed_pf=cell['pf'],
            n_iter=args.n_permutation,
        )
        cell['permutation_test'] = cell_perm
        print(f'      Perm median PF: {cell_perm["perm_median_pf"]}  '
              f'n_ge={cell_perm["n_perm_ge_observed"]}  '
              f'p≈{cell_perm["p_value_conservative"]:.3f}')

        exp3_results.append(cell)

    # =====================================================================
    # Experiment 2 vs 3 comparison (isolated fav-filter contribution)
    # =====================================================================
    print(f'\n{"=" * 70}')
    print('FIXED TP: breach+fav vs breach-only comparison (fav-filter isolation)')
    print(f'{"=" * 70}')

    fav_filter_comparison = []
    for i, R in enumerate(FIXED_TP_R_VALUES):
        e2 = exp2_results[i]
        e3 = exp3_results[i]
        comp = {
            'R': R,
            'breach_fav_filter_pf': e2['pf'],
            'breach_only_pf': e3['pf'],
            'delta_pf': round(float(e3['pf'] - e2['pf']), 3),
            'breach_fav_filter_n': e2['n_trades'],
            'breach_only_n': e3['n_trades'],
            'delta_n': e3['n_trades'] - e2['n_trades'],
            'breach_fav_filter_bs_p05': e2.get('bs_p05'),
            'breach_only_bs_p05': e3.get('bs_p05'),
        }
        fav_filter_comparison.append(comp)
        print(f'  R={R}: fav-filter PF={e2["pf"]}  breach-only PF={e3["pf"]}  '
              f'ΔPF={comp["delta_pf"]}  Δn={comp["delta_n"]}')

    # =====================================================================
    # Comparison summary
    # =====================================================================
    comparison_summary = {
        'baseline_vs_exp1': {
            'baseline_pf': baseline['pf'],
            'exp1_relax_breach_pf': exp1['pf'],
            'delta_pf': exp1_delta['delta_pf'],
            'delta_n': exp1_delta['delta_n_trades'],
        },
        'fixed_tp_vs_baseline': [
            {'R': R, 'fixed_tp_pf': e2['pf'], 'delta_pf': e2['delta_vs_baseline']['delta_pf']}
            for e2, R in zip(exp2_results, FIXED_TP_R_VALUES)
        ],
        'breach_only_vs_baseline': [
            {'R': R, 'breach_only_pf': e3['pf'], 'delta_pf': e3['delta_vs_baseline']['delta_pf']}
            for e3, R in zip(exp3_results, FIXED_TP_R_VALUES)
        ],
        'fav_filter_isolation': fav_filter_comparison,
    }

    # =====================================================================
    # Clean trades from cells (remove list for JSON)
    # =====================================================================
    def clean_cell(cell):
        out = {k: v for k, v in cell.items() if k not in ('trades',)}
        return out

    # =====================================================================
    # Assemble JSON output
    # =====================================================================
    output = {
        'status': 'DIAGNOSTIC_ONLY',
        'source': 'docs/audit/next.md',
        'config': {
            'target': WINNER_TARGET,
            'split': {
                'train': f'<={TRAIN_MAX_YEAR}',
                'val_stop': list(VAL_STOP_YEARS),
                'val_eval': f'>={VAL_EVAL_MIN_YEAR}',
            },
            'spread': args.spread,
            'breach_auc_val_eval': round(breach_auc_check, 4),
            'bootstrap_iter': args.n_bootstrap,
            'bootstrap_block_size': BLOCK_BOOTSTRAP_SIZE,
            'permutation_iter': args.n_permutation,
            'seed': args.seed,
        },
        'search_budget': {
            'relax_breach_cells': 1,
            'fixed_tp_cells': 3,
            'breach_only_cells': 3,
            'baseline_cells': 1,
            'total_cells': 8,
        },
        'baseline': clean_cell(baseline),
        'experiment_1_relax_breach': clean_cell(exp1),
        'experiment_2_fixed_tp': [clean_cell(c) for c in exp2_results],
        'experiment_3_breach_only': [clean_cell(c) for c in exp3_results],
        'fav_filter_isolation': fav_filter_comparison,
        'comparison_summary': comparison_summary,
        'interpretation_guards': [
            'DIAGNOSTIC_ONLY: no test opened, no winner selected, '
            'Stage 4 verdict unchanged',
            'All cells evaluated on same val_eval where Stage 4 winner '
            'was historically selected',
            'hypothesis_only cells require separate clean val_select/val_eval '
            'protocol',
            'Stage 4.4 does NOT select a winner',
            'Test is NOT opened',
            'Best cell is NOT a trading rule — hypothesis_only',
            'Trailing stop was NOT evaluated',
            'Stage 4 verdict is NOT changed',
            'Results do NOT prove breach works without fav — '
            'diagnosis on historical data only',
        ],
    }

    def _custom_default(obj):
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (pd.Timestamp,)):
            return str(obj)
        raise TypeError(f'Object of type {type(obj)} is not JSON serializable')

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(output, f, indent=2, default=_custom_default)
    print(f'\nSaved: {args.output}')
    print('DIAGNOSTIC_ONLY — complete.')


if __name__ == '__main__':
    main()
