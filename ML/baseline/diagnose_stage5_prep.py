# =============================================================================
# File: ML/baseline/diagnose_stage5_prep.py
# Purpose: Stage 5.0-prep DIAGNOSTIC_ONLY — feature ablation + AUC→PF sensitivity.
#           Tests whether breach signal comes from fractal structure or calendar,
#           and estimates model-quality gap needed for PF-gate.
# Input:  DATA/Nero_XAUUSD_*_labeled.csv, DATA/XAUUSD_H1_OHLC.csv
# Output: ML/reports/stage5_prep_diagnostics.json
# Status: DIAGNOSTIC_ONLY — no test, no winner, oracle uses future info
# Language: Python 3.10+
# Created: 2026-06-15
# =============================================================================

import argparse, json, os, sys
from collections import Counter
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, average_precision_score
import xgboost as xgb

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from ML.baseline.diagnose_stage4_3 import (
    load_splits,
    profile_base_raw,
    profile_base_raw_plus_time,
    _extract_base,
    _extract_time,
    compute_entry_prices,
    train_xgb_breach,
    train_rf_fav,
    simulate_trades,
    compute_trade_metrics,
    compute_yearly_metrics,
    block_bootstrap_pf,
    BREACH_TARGETS,
    FAV_TARGETS,
    CAP,
    BLOCK_BOOTSTRAP_SIZE,
    N_BOOTSTRAP,
    TRAIN_MAX_YEAR,
    VAL_STOP_YEARS,
    VAL_EVAL_MIN_YEAR,
    BASE_CHANNEL_KEYS,
)

CANONICAL_SPREAD = 0.20
WINNER_TARGET = 'sell_H6_off05'
WINNER_H = 6
WINNER_OFF = 0.5
WINNER_SIDE = 'sell'
BASELINE_P = 0.4
BASELINE_MIN_FAV = 0.3
BASELINE_MIN_RR = 1.0
BASELINE_TP_FRACTION = 0.4
BASELINE_PF = 1.015
BASELINE_N_TRADES = 503
BASELINE_AUC = 0.6674
PERMUTATION_ITER = 500

FEATURE_PROFILES = [
    'all_base_raw_plus_time',
    'no_time',
    'time_only',
    'fractal_core_only',
    'no_price',
    'no_atr',
]

ORACLE_ALPHAS = [0.0, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0]


def get_feature_groups(all_names):
    indices = {'time': [], 'fractal_core': [], 'atr': []}
    for i, name in enumerate(all_names):
        if name in ('hour_sin', 'hour_cos', 'dow_sin', 'dow_cos'):
            indices['time'].append(i)
        elif name == 'ATR':
            indices['atr'].append(i)
        else:
            indices['fractal_core'].append(i)
    return indices


def build_feature_mask(profile, all_names):
    groups = get_feature_groups(all_names)
    mask = np.zeros(len(all_names), dtype=bool)
    if profile == 'all_base_raw_plus_time':
        mask[:] = True
    elif profile == 'no_time':
        mask[groups['fractal_core']] = True
        mask[groups['atr']] = True
    elif profile == 'time_only':
        mask[groups['time']] = True
    elif profile == 'fractal_core_only':
        mask[groups['fractal_core']] = True
    elif profile == 'no_price':
        price_indices = [i for i, n in enumerate(all_names)
                         if n.endswith('_price')]
        mask[:] = True
        mask[price_indices] = False
    elif profile == 'no_atr':
        mask[:] = True
        mask[groups['atr']] = False
    return mask


def oracle_mix_scores(model_scores, true_labels, alpha=0.0):
    alpha = float(alpha)
    if alpha <= 0.0:
        return model_scores.copy()
    if alpha >= 1.0:
        result = np.zeros_like(model_scores)
        result[true_labels == 1] = np.random.uniform(0.5, 1.0, (true_labels == 1).sum())
        result[true_labels == 0] = np.random.uniform(0.0, 0.5, (true_labels == 0).sum())
        return result
    perfect = np.zeros_like(model_scores)
    perfect[true_labels == 1] = np.random.uniform(0.8, 1.0, (true_labels == 1).sum())
    perfect[true_labels == 0] = np.random.uniform(0.0, 0.2, (true_labels == 0).sum())
    result = alpha * perfect + (1 - alpha) * model_scores
    result = np.clip(result, 0.0, 1.0)
    return result


def schema_ok(output):
    required = ['status', 'config', 'baseline_reproduction',
                'feature_ablation', 'auc_pf_sensitivity',
                'interpretation_guards']
    for key in required:
        if key not in output:
            return False
    return output['status'] == 'DIAGNOSTIC_ONLY'


def _safe(v):
    if isinstance(v, (np.floating,)):
        return float(v)
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (float,)) and not np.isfinite(v):
        return None
    return v


def sim_cell(df_val, entry_prices, breach_proba, fav_pred,
             ohlc, times, time_idx, side, h, stop_offset,
             p, min_fav_val, min_rr, tp_policy, tp_policy_value,
             cap, spread, skip_min_fav=False, skip_min_rr=False):
    trades = simulate_trades(
        df=df_val, entry_prices=entry_prices,
        breach_proba=breach_proba, fav_pred=fav_pred,
        ohlc=ohlc, times=times, time_idx=time_idx,
        side=side, h=h, stop_offset=stop_offset,
        p=p, min_fav_val=min_fav_val, min_rr=min_rr,
        tp_fraction=BASELINE_TP_FRACTION, cap=cap, spread=spread,
        return_details=False,
        tp_policy=tp_policy, tp_policy_value=tp_policy_value,
        skip_min_fav=skip_min_fav, skip_min_rr=skip_min_rr,
    )
    metrics = compute_trade_metrics(trades)
    yearly = compute_yearly_metrics(trades)
    bootstrap = block_bootstrap_pf(trades)
    exits = Counter(t['exit'] for t in trades)
    n = len(trades)
    return {
        'pf': round(float(metrics['pf']), 3),
        'n_trades': n,
        'trades_per_year': round(float(metrics.get('trades_per_year', 0)), 1),
        'n_years': metrics.get('n_years', 0),
        'yearly_pf': {str(k): v['pf'] for k, v in yearly.items()},
        'yearly_n': {str(k): v['n'] for k, v in yearly.items()},
        'bs_median': round(_safe(bootstrap.get('pf_median')), 3) if bootstrap.get('pf_median') is not None else None,
        'bs_p05': round(_safe(bootstrap.get('pf_p05')), 3) if bootstrap.get('pf_p05') is not None else None,
        'bs_p95': round(_safe(bootstrap.get('pf_p95')), 3) if bootstrap.get('pf_p95') is not None else None,
        'gross_profit': round(float(metrics.get('gross_profit', 0)), 3),
        'gross_loss': round(float(metrics.get('gross_loss', 0)), 3),
        'win_rate': round(float(metrics.get('win_rate', 0)), 1),
        'tp_n': exits.get('TP', 0), 'sl_n': exits.get('SL', 0),
        'timeout_n': exits.get('TIMEOUT', 0),
    }


def neg_years_count(yearly_pf):
    return sum(1 for v in yearly_pf.values() if v < 1.0)


def main():
    parser = argparse.ArgumentParser(description='Stage 5.0-prep DIAGNOSTIC_ONLY')
    parser.add_argument('--train', default='DATA/Nero_XAUUSD_train_labeled.csv')
    parser.add_argument('--val', default='DATA/Nero_XAUUSD_validation_labeled.csv')
    parser.add_argument('--ohlc', default='DATA/XAUUSD_H1_OHLC.csv')
    parser.add_argument('--output', default='ML/reports/stage5_prep_diagnostics.json')
    parser.add_argument('--spread', type=float, default=CANONICAL_SPREAD)
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()

    print('=' * 70)
    print('Stage 5.0-Prep: DIAGNOSTIC_ONLY — feature ablation + AUC-PF sensitivity')
    print('=' * 70)

    train_df, val_stop_df, val_eval_df = load_splits(args.train, args.val)
    print(f'Train (<=2016): {len(train_df)}  '
          f'Val-stop (2017-2018): {len(val_stop_df)}  '
          f'Val-eval (>=2019): {len(val_eval_df)}')

    h, off, side = WINNER_H, WINNER_OFF, WINNER_SIDE
    target_col = BREACH_TARGETS[h][off][side]
    fav_col = FAV_TARGETS[h][side]

    y_train_b = train_df[target_col].values
    y_stop_b = val_stop_df[target_col].values
    y_eval_b = val_eval_df[target_col].values
    train_mask_b = ~np.isnan(y_train_b)
    stop_mask_b = ~np.isnan(y_stop_b)
    eval_mask_b = ~np.isnan(y_eval_b)

    y_train_f = train_df[fav_col].values
    y_eval_f = val_eval_df[fav_col].values
    train_mask_f = ~np.isnan(y_train_f)
    eval_mask_f = ~np.isnan(y_eval_f)

    all_names = profile_base_raw_plus_time(train_df)[1]

    # =========================================================================
    # Baseline reproduction
    # =========================================================================
    print(f'\n{"=" * 70}')
    print('BASELINE REPRODUCTION')
    print(f'{"=" * 70}')

    print('Training XGBoost breach (all features)...')
    X_tr_breach, _ = profile_base_raw_plus_time(train_df)
    X_st_breach, _ = profile_base_raw_plus_time(val_stop_df)
    X_ev_breach, _ = profile_base_raw_plus_time(val_eval_df)

    base_xgb = train_xgb_breach(
        X_tr_breach[train_mask_b], y_train_b[train_mask_b],
        X_st_breach[stop_mask_b], y_stop_b[stop_mask_b],
        random_state=args.seed)
    base_breach_proba = base_xgb.predict_proba(X_ev_breach[eval_mask_b])[:, 1]
    base_auc = roc_auc_score(y_eval_b[eval_mask_b], base_breach_proba)
    base_pr_auc = average_precision_score(y_eval_b[eval_mask_b], base_breach_proba)
    print(f'  Breach AUC val_eval: {base_auc:.4f}  PR-AUC: {base_pr_auc:.4f}')

    baseline_repro = {
        'breach_auc': round(float(base_auc), 4),
        'breach_pr_auc': round(float(base_pr_auc), 4),
        'expected_auc': BASELINE_AUC,
        'auc_ok': abs(base_auc - BASELINE_AUC) < 0.001,
    }
    if not baseline_repro['auc_ok']:
        print(f'  WARNING: AUC {base_auc:.4f} != expected {BASELINE_AUC}')

    # =========================================================================
    # Feature ablation
    # =========================================================================
    print(f'\n{"=" * 70}')
    print('FEATURE ABLATION')
    print(f'{"=" * 70}')

    ablation_results = []
    for profile in FEATURE_PROFILES:
        print(f'\n--- {profile} ---')
        mask = build_feature_mask(profile, all_names)
        n_feat = mask.sum()
        print(f'  Features: {n_feat}')

        X_tr_p = X_tr_breach[train_mask_b][:, mask]
        X_st_p = X_st_breach[stop_mask_b][:, mask]
        X_ev_p = X_ev_breach[eval_mask_b][:, mask]

        model = train_xgb_breach(
            X_tr_p, y_train_b[train_mask_b],
            X_st_p, y_stop_b[stop_mask_b],
            random_state=args.seed)
        proba = model.predict_proba(X_ev_p)[:, 1]
        auc = roc_auc_score(y_eval_b[eval_mask_b], proba)
        pr_auc = average_precision_score(y_eval_b[eval_mask_b], proba)

        fi = getattr(model, 'feature_importances_', None)
        top5 = []
        if fi is not None and len(fi) == len(all_names):
            ranked = sorted(
                [(int(i), all_names[i], float(fi[i])) for i in np.where(mask)[0]],
                key=lambda x: x[2], reverse=True)
            top5 = [{'name': r[1], 'importance': round(r[2], 4)} for r in ranked[:5]]

        ablation_results.append({
            'profile': profile,
            'n_features': int(n_feat),
            'breach_auc': round(float(auc), 4),
            'breach_pr_auc': round(float(pr_auc), 4),
            'delta_auc_vs_full': round(float(auc - base_auc), 4),
            'top5_features': top5,
        })
        print(f'  AUC={auc:.4f}  PR-AUC={pr_auc:.4f}  '
              f'ΔAUC={auc - base_auc:+.4f}')

    # =========================================================================
    # AUC-PF sensitivity (oracle mix)
    # =========================================================================
    print(f'\n{"=" * 70}')
    print('AUC→PF SENSITIVITY (oracle mix)')
    print(f'{"=" * 70}')

    from processing.label_signals import load_ohlc_index
    ohlc, times, time_idx = load_ohlc_index(args.ohlc)
    entry_prices_val = compute_entry_prices(val_eval_df, ohlc, times, time_idx)

    X_tr_fav, _ = profile_base_raw(train_df)
    X_ev_fav, _ = profile_base_raw(val_eval_df)

    intersection_mask = eval_mask_b & eval_mask_f
    n_valid = intersection_mask.sum()
    print(f'  Intersection valid: {n_valid}')

    breach_proba_a = base_xgb.predict_proba(X_ev_breach[intersection_mask])[:, 1]
    print('  Training RF fav...')
    fav_model = train_rf_fav(X_tr_fav[train_mask_f], y_train_f[train_mask_f], random_state=args.seed)
    fav_pred_a = fav_model.predict(X_ev_fav[intersection_mask])

    val_masked = val_eval_df[intersection_mask].reset_index(drop=True)
    entry_masked = entry_prices_val[intersection_mask]
    y_eval_b_a = y_eval_b[intersection_mask]

    sensitivity_results = []
    for alpha in ORACLE_ALPHAS:
        mixed = oracle_mix_scores(breach_proba_a, y_eval_b_a, alpha=alpha)

        n_unq = len(np.unique(y_eval_b_a))
        auc_val = roc_auc_score(y_eval_b_a, mixed) if n_unq >= 2 else 0.5

        cell_fav = sim_cell(
            df_val=val_masked, entry_prices=entry_masked,
            breach_proba=mixed, fav_pred=fav_pred_a,
            ohlc=ohlc, times=times, time_idx=time_idx,
            side=side, h=h, stop_offset=off,
            p=BASELINE_P, min_fav_val=BASELINE_MIN_FAV, min_rr=BASELINE_MIN_RR,
            tp_policy='fav_fraction', tp_policy_value=BASELINE_TP_FRACTION,
            cap=CAP, spread=args.spread,
            skip_min_fav=False, skip_min_rr=False,
        )

        cell_fixed = sim_cell(
            df_val=val_masked, entry_prices=entry_masked,
            breach_proba=mixed, fav_pred=fav_pred_a,
            ohlc=ohlc, times=times, time_idx=time_idx,
            side=side, h=h, stop_offset=off,
            p=BASELINE_P, min_fav_val=BASELINE_MIN_FAV, min_rr=BASELINE_MIN_RR,
            tp_policy='fixed_r', tp_policy_value=0.7,
            cap=CAP, spread=args.spread,
            skip_min_fav=False, skip_min_rr=False,
        )

        sensitivity_results.append({
            'alpha': alpha,
            'breach_auc': round(float(auc_val), 4),
            'fav_tp_pf': cell_fav['pf'],
            'fav_tp_n': cell_fav['n_trades'],
            'fav_tp_bs_p05': cell_fav['bs_p05'],
            'fav_tp_neg_years': neg_years_count(cell_fav['yearly_pf']),
            'fixed_r07_pf': cell_fixed['pf'],
            'fixed_r07_n': cell_fixed['n_trades'],
            'fixed_r07_bs_p05': cell_fixed['bs_p05'],
            'fixed_r07_neg_years': neg_years_count(cell_fixed['yearly_pf']),
        })
        print(f'  alpha={alpha:.1f}  AUC={auc_val:.4f}  '
              f'favTP PF={cell_fav["pf"]} (n={cell_fav["n_trades"]})  '
              f'fixedR0.7 PF={cell_fixed["pf"]} (n={cell_fixed["n_trades"]})')

    # =========================================================================
    # Sensitivity thresholds
    # =========================================================================
    gate_pf = 1.15
    first_alpha_fav = None
    first_alpha_fixed = None
    for s in sensitivity_results:
        if first_alpha_fav is None and s['fav_tp_pf'] > gate_pf and (s['fav_tp_bs_p05'] or 0) >= 1.0:
            first_alpha_fav = s['alpha']
            first_alpha_fav_auc = s['breach_auc']
        if first_alpha_fixed is None and s['fixed_r07_pf'] > gate_pf and (s['fixed_r07_bs_p05'] or 0) >= 1.0:
            first_alpha_fixed = s['alpha']
            first_alpha_fixed_auc = s['breach_auc']

    sensitivity_summary = {
        'gate_pf': gate_pf,
        'gate_bs_p05': 1.0,
        'first_alpha_fav_tp': first_alpha_fav,
        'first_alpha_fav_tp_auc': round(float(first_alpha_fav_auc), 4) if first_alpha_fav_auc is not None else None,
        'first_alpha_fixed_r07': first_alpha_fixed,
        'first_alpha_fixed_r07_auc': round(float(first_alpha_fixed_auc), 4) if first_alpha_fixed_auc is not None else None,
        'baseline_auc': round(float(base_auc), 4),
    }
    if first_alpha_fav is not None:
        print(f'\n  Fav-TP gate PF>{gate_pf} at alpha={first_alpha_fav} (AUC={first_alpha_fav_auc:.4f})')
    if first_alpha_fixed is not None:
        print(f'  Fixed R=0.7 gate PF>{gate_pf} at alpha={first_alpha_fixed} (AUC={first_alpha_fixed_auc:.4f})')

    # =========================================================================
    # Assemble JSON output
    # =========================================================================
    output = {
        'status': 'DIAGNOSTIC_ONLY',
        'source': 'docs/audit/to_do.md → Stage 5.0-prep diagnostics',
        'config': {
            'target': WINNER_TARGET,
            'split': {
                'train': f'<={TRAIN_MAX_YEAR}',
                'val_stop': list(VAL_STOP_YEARS),
                'val_eval': f'>={VAL_EVAL_MIN_YEAR}',
            },
            'spread': args.spread,
            'seed': args.seed,
        },
        'baseline_reproduction': baseline_repro,
        'feature_ablation': ablation_results,
        'auc_pf_sensitivity': sensitivity_results,
        'sensitivity_summary': sensitivity_summary,
        'interpretation_guards': [
            'DIAGNOSTIC_ONLY: no test opened, no winner selected',
            'Oracle-mix scores use future information (true breach labels)',
            'Oracle-mix is theoretical diagnostic, not achievable model quality',
            'Feature ablation uses same split as Stage 4.4 — no new winner search',
            'Sensitivity results are upper-bound estimates, not predictions',
            'Calendar risk is identified but not corrected',
            'Ablation does NOT prove any profile can pass PF gate',
        ],
    }
    assert schema_ok(output), 'Schema validation failed'

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(output, f, indent=2, default=str)
    print(f'\nSaved: {args.output}')
    print('DIAGNOSTIC_ONLY — complete.')


if __name__ == '__main__':
    main()
