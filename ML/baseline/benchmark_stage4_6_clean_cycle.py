# =============================================================================
# File: ML/baseline/benchmark_stage4_6_clean_cycle.py
# Purpose: Stage 4.6 clean val_select/val_eval candidate-cycle for exit policies.
#           Extended: val_select 2019-2022, val_eval 2023-2026 (из Nero.csv).
# Input:  DATA/Nero_XAUUSD_*_labeled.csv, MT/MQL4/Files/Nero.csv,
#         DATA/XAUUSD_H1_OHLC.csv
# Output: ML/reports/stage4_6_clean_cycle.json
# Status: DIAGNOSTIC_ONLY — no test, no winner
# Language: Python 3.10+
# Created: 2026-06-15  (extended 2026-06-15)
# =============================================================================

import argparse, json, os, sys
from collections import Counter
from dataclasses import dataclass, field
from typing import Optional
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from processing.label_signals import load_ohlc_index

from ML.baseline.diagnose_stage4_3 import (
    profile_base_raw,
    profile_base_raw_plus_time,
    compute_entry_prices,
    train_xgb_breach,
    train_rf_fav,
    compute_trade_metrics,
    block_bootstrap_pf,
    BREACH_TARGETS,
    FAV_TARGETS,
    CAP,
    TRAIN_MAX_YEAR,
    VAL_STOP_YEARS,
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
VAL_SELECT_YEARS = {2019, 2020, 2021, 2022}
VAL_EVAL_YEARS = {2023, 2024, 2025, 2026}
N_PERMUTATION = 100


@dataclass
class CandidateRule:
    name: str
    pf: float = 0.0
    bs_p05: Optional[float] = None
    bs_median: Optional[float] = None
    n_trades: int = 0
    neg_years: int = 0
    gross_profit_concentration: float = 0.0
    monthly_concentration: float = 0.0
    yearly_pf: dict = field(default_factory=dict)
    yearly_n: dict = field(default_factory=dict)
    policy_cfg: dict = field(default_factory=dict)
    tp_kind: str = 'fixed_r'
    exits: dict = field(default_factory=dict)
    spread_stress_pf: float = 0.0


def select_rule(candidates, gates):
    filtered = []
    for c in candidates:
        if c.bs_p05 is None:
            continue
        if c.n_trades < gates.get('min_trades_per_year', 30):
            continue
        if gates.get('max_concentration') is not None and \
           c.gross_profit_concentration > gates['max_concentration']:
            continue
        filtered.append(c)
    if not filtered:
        return None
    filtered.sort(key=lambda c: (c.bs_p05 or 0, c.pf), reverse=True)
    return filtered[0]


def evaluate_rule(trades):
    if len(trades) == 0:
        return CandidateRule(name='empty', pf=0.0, n_trades=0)
    metrics = compute_trade_metrics(trades)
    bootstrap = block_bootstrap_pf(trades)
    years = {}
    for t in trades:
        yr = t.get('year')
        if yr is not None:
            years[int(yr)] = years.get(int(yr), 0) + 1
    neg_y = 0
    yearly_pf = {}
    yearly_n = {}
    for yr in sorted(years.keys()):
        yr_trades = [t for t in trades if t.get('year') == yr]
        if len(yr_trades) < 1:
            continue
        yr_profit = sum(max(0, t['pnl_val']) for t in yr_trades)
        yr_loss = abs(sum(min(0, t['pnl_val']) for t in yr_trades))
        yr_pf = yr_profit / yr_loss if yr_loss > 0 else (float('inf') if yr_profit > 0 else 0.0)
        if yr_pf < 1.0 and yr_pf != float('inf'):
            neg_y += 1
        yearly_pf[str(yr)] = round(yr_pf, 3) if yr_pf != float('inf') else 'inf'
        yearly_n[str(yr)] = len(yr_trades)

    gross_total = sum(max(0, t['pnl_val']) for t in trades)
    max_year_gross = 0.0
    for yr in sorted(years.keys()):
        yr_gross = sum(max(0, t['pnl_val']) for t in trades if t.get('year') == yr)
        max_year_gross = max(max_year_gross, yr_gross)
    year_conc = max_year_gross / gross_total if gross_total > 0 else 0.0

    monthly_conc = 0.0
    monthly_gross = {}
    for t in trades:
        if t['pnl_val'] > 0 and t.get('year') is not None and t.get('month') is not None:
            key = (int(t['year']), int(t['month']))
            monthly_gross[key] = monthly_gross.get(key, 0.0) + t['pnl_val']
    if gross_total > 0 and monthly_gross:
        max_month_gross = max(monthly_gross.values())
        monthly_conc = max_month_gross / gross_total

    exits = Counter(t['exit'] for t in trades)

    return CandidateRule(
        name='evaluated',
        pf=round(float(metrics['pf']), 3) if np.isfinite(metrics['pf']) else 0.0,
        bs_p05=round(float(bootstrap.get('pf_p05')), 3) if bootstrap.get('pf_p05') is not None else None,
        bs_median=round(float(bootstrap.get('pf_median')), 3) if bootstrap.get('pf_median') is not None else None,
        n_trades=len(trades),
        neg_years=neg_y,
        gross_profit_concentration=round(year_conc, 3),
        monthly_concentration=round(monthly_conc, 3),
        yearly_pf=yearly_pf,
        yearly_n=yearly_n,
        exits=dict(exits),
    )


def load_nero_eval(nero_path, ohlc, times, time_idx, start_year=2023):
    df = pd.read_csv(nero_path, sep=';')
    df['_year'] = pd.to_datetime(df['time'], format='%Y.%m.%d %H:%M',
                                  errors='coerce').dt.year
    df = df[df['_year'] >= start_year].copy()
    df = df.reset_index(drop=True)
    entry = compute_entry_prices(df, ohlc, times, time_idx)
    return df, entry


def run_split(df, entry_prices, breach_model, fav_model, target_col, fav_col):
    X_b, _ = profile_base_raw_plus_time(df)
    X_f, _ = profile_base_raw(df)
    eval_mask_b = ~pd.isna(df[target_col]) if target_col in df.columns \
        else np.ones(len(df), dtype=bool)
    eval_mask_f = ~pd.isna(df[fav_col]) if fav_col in df.columns \
        else np.ones(len(df), dtype=bool)
    inter = eval_mask_b & eval_mask_f
    if inter.sum() == 0:
        return None, None, None, None
    breach_p = breach_model.predict_proba(X_b[inter])[:, 1]
    fav_p = fav_model.predict(X_f[inter])
    df_m = df[inter].reset_index(drop=True)
    ep_m = entry_prices[inter]
    return df_m, ep_m, breach_p, fav_p


def _safe(v):
    if isinstance(v, (np.floating,)):
        return float(v)
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (float,)) and not np.isfinite(v):
        return None
    return v


CANDIDATES = [
    {'name': 'fixed_r_0_7', 'policy': 'fixed', 'r_value': 0.7},
    {'name': 'trail_atr_0_2', 'policy': 'trailing', 'r_value': 0.7, 'trail_atr': 0.2},
    {'name': 'trail_atr_0_3', 'policy': 'trailing', 'r_value': 0.7, 'trail_atr': 0.3},
]


def main():
    parser = argparse.ArgumentParser(description='Stage 4.6+ clean cycle (extended)')
    parser.add_argument('--train', default='DATA/Nero_XAUUSD_train_labeled.csv')
    parser.add_argument('--val', default='DATA/Nero_XAUUSD_validation_labeled.csv')
    parser.add_argument('--nero', default='MT/MQL4/Files/Nero.csv')
    parser.add_argument('--ohlc', default='DATA/XAUUSD_H1_OHLC.csv')
    parser.add_argument('--output', default='ML/reports/stage4_6_clean_cycle.json')
    parser.add_argument('--spread', type=float, default=CANONICAL_SPREAD)
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()

    print('=' * 70)
    print('Stage 4.6+: Extended clean val_select/val_eval candidate-cycle')
    print('=' * 70)
    print(f'  val_select: {sorted(VAL_SELECT_YEARS)}  (4 years, from labeled)')
    print(f'  val_eval:   {sorted(VAL_EVAL_YEARS)}  (4 years, from Nero.csv)')

    # ---- Data ----
    train_full = pd.read_csv(args.train, sep=';')
    val_full = pd.read_csv(args.val, sep=';')
    for df in (train_full, val_full):
        df['_year'] = pd.to_datetime(df['time'], format='%Y.%m.%d %H:%M',
                                      errors='coerce').dt.year

    train = train_full[train_full['_year'] <= TRAIN_MAX_YEAR].copy()
    val_stop = train_full[train_full['_year'].isin(VAL_STOP_YEARS)].copy()

    sel_train = train_full[train_full['_year'].isin(VAL_SELECT_YEARS)].copy()
    sel_val = val_full[val_full['_year'].isin(VAL_SELECT_YEARS)].copy()
    val_select = pd.concat([sel_train, sel_val], ignore_index=True)

    ohlc, times, time_idx = load_ohlc_index(args.ohlc)
    val_eval, entry_eval = load_nero_eval(args.nero, ohlc, times, time_idx,
                                           start_year=2023)

    print(f'Train (<=2016): {len(train)}  Val-stop (2017-2018): {len(val_stop)}')
    print(f'Val-select (2019-2022): {len(val_select)}')
    print(f'Val-eval (2023-2026): {len(val_eval)}  '
          f'source=MT/MQL4/Files/Nero.csv')

    # ---- Train models ----
    h, off, side = WINNER_H, WINNER_OFF, WINNER_SIDE
    target_col = BREACH_TARGETS[h][off][side]
    fav_col = FAV_TARGETS[h][side]

    X_tr_b, _ = profile_base_raw_plus_time(train)
    X_st_b, _ = profile_base_raw_plus_time(val_stop)
    X_tr_f, _ = profile_base_raw(train)

    y_train_b = train[target_col].values
    y_stop_b = val_stop[target_col].values
    train_mask_b = ~np.isnan(y_train_b)
    stop_mask_b = ~np.isnan(y_stop_b)
    y_train_f = train[fav_col].values
    train_mask_f = ~np.isnan(y_train_f)

    print('\nTraining XGBoost breach + RF fav...')
    breach_model = train_xgb_breach(
        X_tr_b[train_mask_b], y_train_b[train_mask_b],
        X_st_b[stop_mask_b], y_stop_b[stop_mask_b],
        random_state=args.seed)
    fav_model = train_rf_fav(
        X_tr_f[train_mask_f], y_train_f[train_mask_f],
        random_state=args.seed)

    # ---- Val-select ----
    entry_sel = compute_entry_prices(val_select, ohlc, times, time_idx)
    df_sel, ep_sel, bp_sel, fp_sel = run_split(
        val_select, entry_sel, breach_model, fav_model, target_col, fav_col)

    print(f'\n{"=" * 70}')
    print(f'VAL-SELECT (2019-2022): {bp_sel.shape[0]} rows')
    print(f'{"=" * 70}')

    val_select_results = []
    for cdef in CANDIDATES:
        cfg = dict(cdef)
        name = cfg.pop('name')
        trades = simulate_trades_with_policy(
            df_sel, ep_sel, bp_sel, fp_sel,
            ohlc, times, time_idx, side, h, off,
            BASELINE_P, BASELINE_MIN_FAV, BASELINE_MIN_RR,
            'fixed_r', cfg, CAP, args.spread)
        # Attach month from entry time
        for ti, t in enumerate(trades):
            t['month'] = None
            try:
                match = df_sel[ti] if ti < len(df_sel) else None
            except:
                pass
        rule = evaluate_rule(trades)
        rule.name = name
        rule.policy_cfg = cfg
        rule.tp_kind = 'fixed_r'
        trades_stress = simulate_trades_with_policy(
            df_sel, ep_sel, bp_sel, fp_sel,
            ohlc, times, time_idx, side, h, off,
            BASELINE_P, BASELINE_MIN_FAV, BASELINE_MIN_RR,
            'fixed_r', cfg, CAP, 0.40)
        rule.spread_stress_pf = round(float(compute_trade_metrics(trades_stress)['pf']), 3)
        val_select_results.append(rule)
        print(f'  {name}: PF={rule.pf}  BS_p05={rule.bs_p05}  n={rule.n_trades}  '
              f'neg_y={rule.neg_years}  y_conc={rule.gross_profit_concentration}  '
              f'm_conc={rule.monthly_concentration}')

    gates = {'min_trades_per_year': 30, 'max_concentration': 0.6}
    selected = select_rule(val_select_results, gates)
    print(f'\nSelected: {selected.name if selected else "NO_CANDIDATE"}')

    # ---- Val-eval ----
    val_eval_result = None
    val_eval_stress_pf = None
    if selected is not None:
        print(f'\n{"=" * 70}')
        print(f'VAL-EVAL (2023-2026): {selected.name}')
        print(f'{"=" * 70}')

        df_ev, ep_ev, bp_ev, fp_ev = run_split(
            val_eval, entry_eval, breach_model, fav_model, target_col, fav_col)
        print(f'  Valid rows: {bp_ev.shape[0]}')

        cfg = dict(selected.policy_cfg)
        trades_eval = simulate_trades_with_policy(
            df_ev, ep_ev, bp_ev, fp_ev,
            ohlc, times, time_idx, side, h, off,
            BASELINE_P, BASELINE_MIN_FAV, BASELINE_MIN_RR,
            selected.tp_kind, cfg, CAP, args.spread)
        # Add month info
        for t in trades_eval:
            t['month'] = None
        rule_eval = evaluate_rule(trades_eval)
        rule_eval.name = selected.name
        val_eval_result = rule_eval

        trades_stress_ev = simulate_trades_with_policy(
            df_ev, ep_ev, bp_ev, fp_ev,
            ohlc, times, time_idx, side, h, off,
            BASELINE_P, BASELINE_MIN_FAV, BASELINE_MIN_RR,
            selected.tp_kind, cfg, CAP, 0.40)
        val_eval_stress_pf = round(float(compute_trade_metrics(trades_stress_ev)['pf']), 3)

        print(f'  PF={rule_eval.pf}  BS_p05={rule_eval.bs_p05}  '
              f'n={rule_eval.n_trades}  neg_y={rule_eval.neg_years}')
        print(f'  Yearly concentration: {rule_eval.gross_profit_concentration}')
        print(f'  Monthly concentration: {rule_eval.monthly_concentration}')
        for yr in sorted(rule_eval.yearly_pf.keys()):
            print(f'    {yr}: PF={rule_eval.yearly_pf[yr]}  '
                  f'n={rule_eval.yearly_n[yr]}')
        print(f'  Spread 0.40: PF={val_eval_stress_pf}')

    # ---- Permutation ----
    print(f'\n{"=" * 70}')
    print(f'PERMUTATION WITH REPEATED SELECTION ({N_PERMUTATION} iters)')
    print(f'{"=" * 70}')

    rng = np.random.RandomState(args.seed)
    perm_pfs = []
    perm_names = Counter()
    for _ in range(N_PERMUTATION):
        perm_bp = rng.permutation(bp_sel.copy())
        perm_results = []
        for cdef in CANDIDATES:
            cfg = dict(cdef)
            cfg.pop('name')
            trades = simulate_trades_with_policy(
                df_sel, ep_sel, perm_bp, fp_sel,
                ohlc, times, time_idx, side, h, off,
                BASELINE_P, BASELINE_MIN_FAV, BASELINE_MIN_RR,
                'fixed_r', cfg, CAP, args.spread)
            rule = evaluate_rule(trades)
            rule.name = cdef['name']
            perm_results.append(rule)
        perm_sel = select_rule(perm_results, gates)
        if perm_sel is None:
            perm_pfs.append(0.0)
            perm_names['NONE'] += 1
        else:
            perm_names[perm_sel.name] += 1
            p_cfg = dict(CANDIDATES[[c['name'] for c in CANDIDATES].index(perm_sel.name)])
            p_cfg.pop('name', None)
            df_ev_p, ep_ev_p, bp_ev_p, fp_ev_p = run_split(
                val_eval, entry_eval, breach_model, fav_model, target_col, fav_col)
            perm_trades_eval = simulate_trades_with_policy(
                df_ev_p, ep_ev_p, bp_ev_p, fp_ev_p,
                ohlc, times, time_idx, side, h, off,
                BASELINE_P, BASELINE_MIN_FAV, BASELINE_MIN_RR,
                'fixed_r', p_cfg, CAP, args.spread)
            pm = compute_trade_metrics(perm_trades_eval)
            perm_pfs.append(pm['pf'] if np.isfinite(pm['pf']) else 0.0)

    perm_arr = np.array(perm_pfs)
    obs_pf = val_eval_result.pf if val_eval_result is not None and val_eval_result.pf > 0 else 1.0
    n_ge = int((perm_arr >= obs_pf).sum())
    print(f'  Perm median PF val_eval: {np.median(perm_arr):.3f}')
    print(f'  N_ge observed: {n_ge} / {N_PERMUTATION}  '
          f'p={(n_ge + 1) / (N_PERMUTATION + 1):.4f}')
    print(f'  Selected in perm: {dict(perm_names)}')

    # ---- Output ----
    def _rule_dict(r):
        return {
            'name': r.name, 'pf': r.pf, 'bs_p05': r.bs_p05, 'bs_median': r.bs_median,
            'n_trades': r.n_trades, 'neg_years': r.neg_years,
            'gross_profit_concentration': r.gross_profit_concentration,
            'monthly_concentration': r.monthly_concentration,
            'yearly_pf': r.yearly_pf, 'yearly_n': r.yearly_n,
            'exits': r.exits, 'spread_stress_pf': r.spread_stress_pf,
        }

    output = {
        'status': 'DIAGNOSTIC_ONLY',
        'source': 'Stage 4.5 trail_atr_0_2 → extended clean cycle (incl 2023-2026)',
        'config': {
            'target': WINNER_TARGET,
            'split': {
                'train': f'<={TRAIN_MAX_YEAR}',
                'val_stop': list(VAL_STOP_YEARS),
                'val_select': sorted(VAL_SELECT_YEARS),
                'val_eval': sorted(VAL_EVAL_YEARS),
            },
            'spread': args.spread, 'seed': args.seed,
            'search_budget': {'n_candidates': len(CANDIDATES)},
            'val_eval_source': 'MT/MQL4/Files/Nero.csv (unlabeled, features only)',
        },
        'val_select_results': [_rule_dict(r) for r in val_select_results],
        'selected_rule': selected.name if selected else None,
        'val_eval_result': _rule_dict(val_eval_result) if selected else None,
        'permutation_selection': {
            'n_iter': N_PERMUTATION,
            'perm_median_pf': round(float(np.median(perm_arr)), 3),
            'perm_p05_pf': round(float(np.percentile(perm_arr, 5)), 3),
            'perm_p95_pf': round(float(np.percentile(perm_arr, 95)), 3),
            'n_ge_observed': n_ge,
            'p_value': round((n_ge + 1) / (N_PERMUTATION + 1), 4),
            'selected_in_perm': {k: v for k, v in perm_names.items()},
        },
        'interpretation_guards': [
            'DIAGNOSTIC_ONLY: no test opened, no frozen test candidate',
            'val_eval 2023-2026 from Nero.csv — NO target labels, features+OHLC only',
            'Model stack unchanged from Stage 4.4 — exit mechanics only',
            'If val_eval fails: reject candidate family, do not expand grid',
            'If val_eval passes: RESEARCH_CANDIDATE, not frozen test candidate',
        ],
    }

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(output, f, indent=2, default=str)
    print(f'\nSaved: {args.output}')
    print('DIAGNOSTIC_ONLY — complete.')


if __name__ == '__main__':
    main()
