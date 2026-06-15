# =============================================================================
# File: ML/baseline/diagnose_stage4_5_exit_mechanics.py
# Purpose: Stage 4.5 DIAGNOSTIC_ONLY — trailing / breakeven / partial exit
#           mechanics for Fractal Stop, using fixed Stage 4.4 predictions.
# Input:  DATA/Nero_XAUUSD_*_labeled.csv, DATA/XAUUSD_H1_OHLC.csv
# Output: ML/reports/stage4_5_exit_mechanics.json
# Status: DIAGNOSTIC_ONLY — no test, no winner, exit mechanics only
# Language: Python 3.10+
# Created: 2026-06-15
# =============================================================================

import argparse, json, os, sys
from collections import Counter
from datetime import datetime, timezone
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from processing.label_signals import load_ohlc_index

from ML.baseline.diagnose_stage4_3 import (
    load_splits,
    profile_base_raw,
    profile_base_raw_plus_time,
    compute_entry_prices,
    train_xgb_breach,
    train_rf_fav,
    parse_trade_fractal0,
    resolve_tp_val,
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
FIXED_R07_PF = 1.038

N_PERMUTATION = 500

EXIT_POLICIES = [
    {'name': 'fixed_r_0_7', 'policy': 'fixed', 'r_value': 0.7},
    {'name': 'breakeven_0_3', 'policy': 'breakeven', 'r_value': 0.7,
     'breakeven_trigger_r': 0.3},
    {'name': 'trail_atr_0_2', 'policy': 'trailing', 'r_value': 0.7,
     'trail_atr': 0.2},
    {'name': 'trail_atr_0_3', 'policy': 'trailing', 'r_value': 0.7,
     'trail_atr': 0.3},
    {'name': 'partial_50_at_0_5R_then_trail_0_2', 'policy': 'partial',
     'r_value': 0.7, 'partial_ratio': 0.5, 'partial_target_r': 0.5,
     'trail_atr': 0.2},
]


def simulate_exit(bars_h, direction, entry_price, sl_price, tp_price, atr,
                  policy='fixed', breakeven_trigger_r=None,
                  trail_atr=None, partial_ratio=None,
                  partial_target_r=None):
    assert policy in ('fixed', 'breakeven', 'trailing', 'partial')

    best_fav = entry_price
    sl_active = sl_price
    breakeven_done = False
    partial_done = False
    partial_pnl = 0.0

    for bi, (o, h, l, c) in enumerate(bars_h):
        if direction == -1:
            fav_hit = h if h > 0 else best_fav
        else:
            fav_hit = l if l > 0 else best_fav

        is_fav_move = (direction == -1 and fav_hit > best_fav) or \
                      (direction == 1 and fav_hit < best_fav)
        if is_fav_move:
            best_fav = fav_hit

        if direction == -1:
            hit_sl = l <= sl_active
            hit_tp = h >= tp_price
        else:
            hit_sl = h >= sl_active
            hit_tp = l <= tp_price

        if hit_sl and hit_tp:
            if direction == -1:
                return {'exit': 'SL', 'pnl_val': -(entry_price - sl_active) / atr,
                        'ambiguous': 1}
            else:
                return {'exit': 'SL', 'pnl_val': -(sl_active - entry_price) / atr,
                        'ambiguous': 1}

        if hit_tp:
            if partial_done:
                total_pnl = partial_pnl
                if direction == -1:
                    total_pnl += partial_ratio * (tp_price - entry_price) / atr
                else:
                    total_pnl += partial_ratio * (entry_price - tp_price) / atr
                return {'exit': 'TP', 'pnl_val': total_pnl, 'ambiguous': 0}
            else:
                if direction == -1:
                    return {'exit': 'TP', 'pnl_val': (tp_price - entry_price) / atr,
                            'ambiguous': 0}
                else:
                    return {'exit': 'TP', 'pnl_val': (entry_price - tp_price) / atr,
                            'ambiguous': 0}

        if hit_sl:
            if partial_done:
                total_pnl = partial_pnl
                if direction == -1:
                    total_pnl += (1 - partial_ratio) * (-(entry_price - sl_active)) / atr
                else:
                    total_pnl += (1 - partial_ratio) * (-(sl_active - entry_price)) / atr
                return {'exit': 'SL', 'pnl_val': total_pnl, 'ambiguous': 0}
            else:
                if direction == -1:
                    return {'exit': 'SL', 'pnl_val': -(entry_price - sl_active) / atr,
                            'ambiguous': 0}
                else:
                    return {'exit': 'SL', 'pnl_val': -(sl_active - entry_price) / atr,
                            'ambiguous': 0}

        # Breakeven logic
        if policy == 'breakeven' and not breakeven_done and \
           breakeven_trigger_r is not None:
            tp_move = abs(tp_price - entry_price)
            if tp_move > 0:
                fraction = abs(best_fav - entry_price) / tp_move
                if fraction >= breakeven_trigger_r:
                    sl_active = entry_price
                    breakeven_done = True

        # Trailing stop logic
        if policy in ('trailing',) and trail_atr is not None:
            if direction == -1:
                new_sl = best_fav - trail_atr * atr
                if new_sl > sl_active:
                    sl_active = new_sl
            else:
                new_sl = best_fav + trail_atr * atr
                if new_sl < sl_active:
                    sl_active = new_sl

        # Partial exit logic
        if policy == 'partial' and not partial_done and partial_ratio is not None \
           and partial_target_r is not None:
            ptarget_price = (entry_price +
                             (direction == -1 and 1 or -1) * partial_target_r * atr)
            if direction == -1:
                hit_pt = h >= ptarget_price
            else:
                hit_pt = l <= ptarget_price
            if hit_pt:
                if direction == -1:
                    partial_pnl = partial_ratio * (ptarget_price - entry_price) / atr
                else:
                    partial_pnl = partial_ratio * (entry_price - ptarget_price) / atr
                partial_done = True
                if trail_atr is not None:
                    sl_active = entry_price

        if hit_sl and not hit_tp:
            if partial_done:
                total_pnl = partial_pnl
                if direction == -1:
                    total_pnl += (1 - partial_ratio) * (-(entry_price - sl_active)) / atr
                else:
                    total_pnl += (1 - partial_ratio) * (-(sl_active - entry_price)) / atr
                return {'exit': 'SL', 'pnl_val': total_pnl, 'ambiguous': 0}
            else:
                if direction == -1:
                    return {'exit': 'SL', 'pnl_val': -(entry_price - sl_active) / atr,
                            'ambiguous': 0}
                else:
                    return {'exit': 'SL', 'pnl_val': -(sl_active - entry_price) / atr,
                            'ambiguous': 0}

        # Check sl again after trailing update
        if direction == -1:
            hit_sl_now = l <= sl_active
        else:
            hit_sl_now = h >= sl_active
        if hit_sl_now and not hit_tp:
            exit_reason = 'TRAIL' if policy in ('trailing',) else 'SL'
            if partial_done:
                total_pnl = partial_pnl
                if direction == -1:
                    total_pnl += (1 - partial_ratio) * (-(entry_price - sl_active)) / atr
                else:
                    total_pnl += (1 - partial_ratio) * (-(sl_active - entry_price)) / atr
                return {'exit': exit_reason, 'pnl_val': total_pnl, 'ambiguous': 0}
            else:
                if direction == -1:
                    return {'exit': exit_reason, 'pnl_val': -(entry_price - sl_active) / atr,
                            'ambiguous': 0}
                else:
                    return {'exit': exit_reason, 'pnl_val': -(sl_active - entry_price) / atr,
                            'ambiguous': 0}

    close_h = bars_h[-1][3]
    if direction == -1:
        timeout_pnl = (close_h - entry_price) / atr
    else:
        timeout_pnl = (entry_price - close_h) / atr
    if partial_done:
        timeout_pnl = partial_pnl + (1 - partial_ratio) * timeout_pnl
    return {'exit': 'TIMEOUT', 'pnl_val': timeout_pnl, 'ambiguous': 0}


def _safe(v):
    if isinstance(v, (np.floating,)):
        return float(v)
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (float,)) and not np.isfinite(v):
        return None
    return v


def simulate_trades_with_policy(df, entry_prices, breach_proba, fav_pred,
                                ohlc, times, time_idx, side, h, stop_offset,
                                p, min_fav_val, min_rr, tp_policy_name,
                                policy_cfg, cap, spread):
    trades = []
    trade_direction = -1 if side == 'buy' else 1
    expected_fractal_dir = -1 if side == 'buy' else 1

    for i, (idx, row) in enumerate(df.iterrows()):
        fractal0 = parse_trade_fractal0(row.get('fractal0'))
        if fractal0 is None or fractal0['direction'] != expected_fractal_dir:
            continue

        fractal_price = fractal0['price']
        try:
            row_dt = datetime.strptime(str(row['time']), '%Y.%m.%d %H:%M') \
                .replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            continue
        idx0 = time_idx.get(row_dt)
        if idx0 is None or idx0 + h >= len(times):
            continue

        entry_price_val = entry_prices[i]
        if np.isnan(entry_price_val):
            continue
        atr_val = float(row.get('ATR', np.nan))
        if np.isnan(atr_val) or atr_val <= 0:
            continue

        pred_break = breach_proba[i]
        pred_fav = fav_pred[i]
        if np.isnan(pred_break) or np.isnan(pred_fav):
            continue

        if trade_direction == -1:
            stop_price = min(fractal_price, entry_price_val) - stop_offset * atr_val
            stop_val = (entry_price_val - stop_price) / atr_val
        else:
            stop_price = max(fractal_price, entry_price_val) + stop_offset * atr_val
            stop_val = (stop_price - entry_price_val) / atr_val
        if stop_val <= 0:
            continue

        if tp_policy_name == 'fav_fraction':
            tp_val_atr = resolve_tp_val('fav_fraction',
                                         policy_cfg.get('tp_fraction', 0.4),
                                         pred_fav, stop_val)
        else:
            r_val = policy_cfg.get('r_value', 0.7)
            tp_val_atr = r_val * stop_val
        tp_val_atr = min(tp_val_atr, cap)
        if tp_val_atr <= 0:
            continue

        if trade_direction == -1:
            tp_price = entry_price_val + tp_val_atr * atr_val
        else:
            tp_price = entry_price_val - tp_val_atr * atr_val

        bars_h_bid = [(ohlc[times[k]][0], ohlc[times[k]][1],
                        ohlc[times[k]][2], ohlc[times[k]][3])
                       for k in range(idx0 + 1, idx0 + 1 + h)]
        if trade_direction == -1:
            entry_eff = entry_price_val + spread
            bars_h_eff = bars_h_bid
        else:
            entry_eff = entry_price_val
            bars_h_eff = [(o + spread, h + spread, l + spread, c + spread)
                          for o, h, l, c in bars_h_bid]

        stop_val_actual = abs(entry_eff - stop_price) / atr_val
        if stop_val_actual <= 0:
            continue

        if pred_break >= p:
            continue
        if pred_fav < min_fav_val:
            continue
        if pred_fav / stop_val_actual < min_rr:
            continue

        exit_policy = policy_cfg.get('policy', 'fixed')
        outcome = simulate_exit(
            bars_h_eff, trade_direction, entry_eff, stop_price, tp_price,
            atr_val,
            policy=exit_policy,
            breakeven_trigger_r=policy_cfg.get('breakeven_trigger_r'),
            trail_atr=policy_cfg.get('trail_atr'),
            partial_ratio=policy_cfg.get('partial_ratio'),
            partial_target_r=policy_cfg.get('partial_target_r'),
        )

        year_val = row.get('_year')
        year_int = int(year_val) if not pd.isna(year_val) else None

        trade_rec = {
            'exit': outcome['exit'],
            'pnl_val': outcome['pnl_val'],
            'stop_val': stop_val_actual,
            'pnl_r': outcome['pnl_val'] / stop_val_actual
                if stop_val_actual > 0 else outcome['pnl_val'],
            'ambiguous': outcome['ambiguous'],
            'year': year_int,
            'side': side,
        }
        trades.append(trade_rec)

    return trades


def neg_years(yearly_metrics):
    return sum(1 for v in yearly_metrics.values() if v.get('pf', 0) < 1.0)


def main():
    parser = argparse.ArgumentParser(description='Stage 4.5 DIAGNOSTIC_ONLY exit mechanics')
    parser.add_argument('--train', default='DATA/Nero_XAUUSD_train_labeled.csv')
    parser.add_argument('--val', default='DATA/Nero_XAUUSD_validation_labeled.csv')
    parser.add_argument('--ohlc', default='DATA/XAUUSD_H1_OHLC.csv')
    parser.add_argument('--output', default='ML/reports/stage4_5_exit_mechanics.json')
    parser.add_argument('--spread', type=float, default=CANONICAL_SPREAD)
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()

    print('=' * 70)
    print('Stage 4.5: DIAGNOSTIC_ONLY — trailing / breakeven / partial exit')
    print('=' * 70)

    train_df, val_stop_df, val_eval_df = load_splits(args.train, args.val)
    print(f'Train (<=2016): {len(train_df)}  '
          f'Val-stop (2017-2018): {len(val_stop_df)}  '
          f'Val-eval (>=2019): {len(val_eval_df)}')

    ohlc, times, time_idx = load_ohlc_index(args.ohlc)
    entry_prices_val = compute_entry_prices(val_eval_df, ohlc, times, time_idx)

    h, off, side = WINNER_H, WINNER_OFF, WINNER_SIDE
    target_col = BREACH_TARGETS[h][off][side]
    fav_col = FAV_TARGETS[h][side]

    X_tr_breach, _ = profile_base_raw_plus_time(train_df)
    X_st_breach, _ = profile_base_raw_plus_time(val_stop_df)
    X_ev_breach, _ = profile_base_raw_plus_time(val_eval_df)
    X_tr_fav, _ = profile_base_raw(train_df)
    X_ev_fav, _ = profile_base_raw(val_eval_df)

    y_train_b = train_df[target_col].values
    y_stop_b = val_stop_df[target_col].values
    y_eval_b = val_eval_df[target_col].values
    train_mask_b = ~np.isnan(y_train_b)
    stop_mask_b = ~np.isnan(y_stop_b)
    eval_mask_b = ~np.isnan(y_eval_b)

    y_train_f = train_df[fav_col].values
    eval_mask_f = ~np.isnan(val_eval_df[fav_col].values)
    train_mask_f = ~np.isnan(y_train_f)

    print('\nTraining XGBoost breach...')
    breach_model = train_xgb_breach(
        X_tr_breach[train_mask_b], y_train_b[train_mask_b],
        X_st_breach[stop_mask_b], y_stop_b[stop_mask_b],
        random_state=args.seed)

    print('Training RF fav...')
    fav_model = train_rf_fav(
        X_tr_fav[train_mask_f], y_train_f[train_mask_f],
        random_state=args.seed)

    intersection_mask = eval_mask_b & eval_mask_f
    n_valid = intersection_mask.sum()
    print(f'Intersection valid: {n_valid}')

    breach_proba = breach_model.predict_proba(X_ev_breach[intersection_mask])[:, 1]
    fav_pred = fav_model.predict(X_ev_fav[intersection_mask])
    val_masked = val_eval_df[intersection_mask].reset_index(drop=True)
    entry_masked = entry_prices_val[intersection_mask]

    # =========================================================================
    # Baseline reproduction: fixed TP R=0.7
    # =========================================================================
    print(f'\n{"=" * 70}')
    print('BASELINE: fixed_r_0_7')
    print(f'{"=" * 70}')

    baseline_cfg = {'policy': 'fixed', 'r_value': 0.7}
    baseline_trades = simulate_trades_with_policy(
        val_masked, entry_masked, breach_proba, fav_pred,
        ohlc, times, time_idx, side, h, off,
        BASELINE_P, BASELINE_MIN_FAV, BASELINE_MIN_RR,
        'fixed_r', baseline_cfg, CAP, args.spread)
    baseline_m = compute_trade_metrics(baseline_trades)
    baseline_y = compute_yearly_metrics(baseline_trades)
    baseline_bs = block_bootstrap_pf(baseline_trades)
    exits_b = Counter(t['exit'] for t in baseline_trades)
    print(f'  PF={baseline_m["pf"]:.3f}  n={len(baseline_trades)}  '
          f'BS_p05={baseline_bs.get("pf_p05", 0):.3f}')
    print(f'  Exits: {dict(exits_b)}')

    baseline_repro = {
        'pf': round(float(baseline_m['pf']), 3),
        'n_trades': len(baseline_trades),
        'bs_p05': round(_safe(baseline_bs.get('pf_p05')), 3),
        'expected_pf': FIXED_R07_PF, 'expected_n': BASELINE_N_TRADES,
        'pf_ok': abs(baseline_m['pf'] - FIXED_R07_PF) < 0.002,
        'n_ok': len(baseline_trades) == BASELINE_N_TRADES,
    }
    if not baseline_repro['pf_ok']:
        print(f'  WARNING: PF mismatch {baseline_m["pf"]} != {FIXED_R07_PF}')

    # =========================================================================
    # Run exit policies
    # =========================================================================
    print(f'\n{"=" * 70}')
    print(f'EXIT POLICIES ({len(EXIT_POLICIES)} variants)')
    print(f'{"=" * 70}')

    policy_results = []
    for pdef in EXIT_POLICIES:
        cfg = dict(pdef)
        cfg.pop('name')
        name = pdef['name']
        tp_kind = 'fixed_r' if cfg.get('r_value') is not None else 'fav_fraction'

        print(f'\n--- {name} ---')
        trades = simulate_trades_with_policy(
            val_masked, entry_masked, breach_proba, fav_pred,
            ohlc, times, time_idx, side, h, off,
            BASELINE_P, BASELINE_MIN_FAV, BASELINE_MIN_RR,
            tp_kind, cfg, CAP, args.spread)

        metrics = compute_trade_metrics(trades)
        yearly = compute_yearly_metrics(trades)
        bootstrap = block_bootstrap_pf(trades)
        exits = Counter(t['exit'] for t in trades)
        n = len(trades)

        # Spread stress
        trades_stress = simulate_trades_with_policy(
            val_masked, entry_masked, breach_proba, fav_pred,
            ohlc, times, time_idx, side, h, off,
            BASELINE_P, BASELINE_MIN_FAV, BASELINE_MIN_RR,
            tp_kind, cfg, CAP, 0.40)
        stress_m = compute_trade_metrics(trades_stress)
        stress_bs = block_bootstrap_pf(trades_stress)

        result = {
            'name': name,
            'policy': cfg.get('policy', 'fixed'),
            'pf': round(float(metrics['pf']), 3),
            'n_trades': n,
            'trades_per_year': round(float(metrics.get('trades_per_year', 0)), 1),
            'n_years': metrics.get('n_years', 0),
            'yearly_pf': {str(k): round(v['pf'], 3) if isinstance(v['pf'], float) else v['pf']
                          for k, v in yearly.items()},
            'yearly_n': {str(k): v['n'] for k, v in yearly.items()},
            'bs_median': round(_safe(bootstrap.get('pf_median')), 3),
            'bs_p05': round(_safe(bootstrap.get('pf_p05')), 3),
            'bs_p95': round(_safe(bootstrap.get('pf_p95')), 3),
            'neg_years': neg_years(yearly),
            'gross_profit': round(float(metrics.get('gross_profit', 0)), 3),
            'gross_loss': round(float(metrics.get('gross_loss', 0)), 3),
            'win_rate': round(float(metrics.get('win_rate', 0)), 1),
            'exits': {k: v for k, v in exits.items()},
            'spread_stress': {
                'pf': round(float(stress_m['pf']), 3),
                'bs_p05': round(_safe(stress_bs.get('pf_p05')), 3),
            },
        }

        print(f'  PF={result["pf"]}  n={n}  BS_p05={result["bs_p05"]}  '
              f'neg_years={result["neg_years"]}')
        print(f'  Exits: {result["exits"]}')
        print(f'  Spread 0.40: PF={result["spread_stress"]["pf"]}  '
              f'BS_p05={result["spread_stress"]["bs_p05"]}')

        policy_results.append(result)

    # =========================================================================
    # Permutation test for baseline (fixed R=0.7)
    # =========================================================================
    print(f'\n{"=" * 70}')
    print('PERMUTATION TEST (baseline fixed R=0.7)')
    print(f'{"=" * 70}')

    rng = np.random.RandomState(args.seed)
    perm_pfs = []
    for _ in range(N_PERMUTATION):
        perm_breach = rng.permutation(breach_proba.copy())
        perm_trades = simulate_trades_with_policy(
            val_masked, entry_masked, perm_breach, fav_pred,
            ohlc, times, time_idx, side, h, off,
            BASELINE_P, BASELINE_MIN_FAV, BASELINE_MIN_RR,
            'fixed_r', {'policy': 'fixed', 'r_value': 0.7}, CAP, args.spread)
        pm = compute_trade_metrics(perm_trades)
        perm_pf = pm['pf']
        perm_pfs.append(perm_pf if np.isfinite(perm_pf) else 0.0)
    perm_arr = np.array(perm_pfs)
    n_ge = int((perm_arr >= baseline_m['pf']).sum())

    permutation = {
        'n_iter': N_PERMUTATION,
        'perm_median_pf': round(float(np.median(perm_arr)), 3),
        'perm_p05_pf': round(float(np.percentile(perm_arr, 5)), 3),
        'perm_p95_pf': round(float(np.percentile(perm_arr, 95)), 3),
        'n_ge_observed': n_ge,
        'p_value': (n_ge + 1) / (N_PERMUTATION + 1),
    }
    print(f'  Perm median PF: {permutation["perm_median_pf"]}  '
          f'n_ge={n_ge}  p={permutation["p_value"]:.4f}')

    # =========================================================================
    # Assemble output
    # =========================================================================
    output = {
        'status': 'DIAGNOSTIC_ONLY',
        'source': 'docs/audit/to_do.md → trailing / partial exit mechanics',
        'config': {
            'target': WINNER_TARGET,
            'spread': args.spread,
            'seed': args.seed,
            'search_budget': {
                'n_policies': len(EXIT_POLICIES),
                'policies': [p['name'] for p in EXIT_POLICIES],
            },
        },
        'baseline_reproduction': baseline_repro,
        'exit_policies': policy_results,
        'permutation_test': permutation,
        'interpretation_guards': [
            'DIAGNOSTIC_ONLY: no test opened, no winner selected',
            'Exit policy alone — breach/fav models unchanged from Stage 4.4',
            'No policy deserves a clean candidate-cycle without BS_p05 > 1.0 '
            'and PF improvement',
            'Old trailing PF=1.655 is not reused as evidence',
            'Cost stress at spread=0.40 applied — reject if fails',
            'Any attractive policy requires separate val_select/val_eval',
        ],
    }

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(output, f, indent=2, default=str)
    print(f'\nSaved: {args.output}')
    print('DIAGNOSTIC_ONLY — complete.')


if __name__ == '__main__':
    main()
