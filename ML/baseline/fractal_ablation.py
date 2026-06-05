#!/usr/bin/env python3
"""
Ablation study: вклад групп признаков 29-канального тензора в edge_h и TB-таргеты.

Использование:
  .venv/bin/python -m ML.baseline.fractal_ablation                           # validation only
  .venv/bin/python -m ML.baseline.fractal_ablation --test all no_atr_dist    # frozen test
  .venv/bin/python -m ML.baseline.fractal_ablation --json-out ML/reports/fractal_ablation.json
"""

import argparse, json, sys, os
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ML.data_loader import parse_fractals_to_3d, N_FRACTAL_FEATURES

DATA = PROJECT_ROOT / 'DATA'

# Feature group channel masks
BASE_CHANNELS = set(range(0, 10))
PATH_CHANNELS = set(range(10, 20))
ATR_RATIO_CH = {20}
TIME_CHANNELS = set(range(21, 26))
ATR_DIST_CHANNELS = {26, 27, 28}

ALL_CHANNELS = set(range(N_FRACTAL_FEATURES))

VARIANTS = {
    # drop-one
    'all':        ALL_CHANNELS,
    'no_path':    ALL_CHANNELS - PATH_CHANNELS,
    'no_atr_dist': ALL_CHANNELS - ATR_DIST_CHANNELS,
    'no_time':    ALL_CHANNELS - TIME_CHANNELS,
    'no_base':    ALL_CHANNELS - BASE_CHANNELS,
    'no_horizon6': ALL_CHANNELS - {18, 19},  # drop up_6/dn_6 (same horizon as edge_6 target)
    # keep-one
    'only_dir':   {1},
    'only_base':  BASE_CHANNELS,
    'only_time':  TIME_CHANNELS,
    'only_path':  PATH_CHANNELS,
}


def profit_factor(pnl):
    gp = float(pnl[pnl > 0].sum())
    gl = float(-pnl[pnl < 0].sum())
    return gp / gl if gl > 0 else (float('inf') if gp > 0 else 0.0)


def _yearly(times, pnl_array):
    yearly = {}
    neg_y = 0
    for yr in sorted(times.dt.year.unique()):
        m = times.dt.year == yr
        pnl_y = pnl_array[m.values]
        tr_y = (pnl_y != 0).sum()
        pf_y = profit_factor(pnl_y) if tr_y > 0 else 0
        win_y = float(np.mean(pnl_y[pnl_y != 0] > 0)) if (pnl_y != 0).sum() > 0 else 0
        yearly[int(yr)] = {
            'pf': round(pf_y, 3),
            'n_trades': int(tr_y),
            'win': round(win_y, 3),
            'mean_r': round(float(pnl_y.sum()), 3),
        }
        if pf_y < 1.0:
            neg_y += 1
    return yearly, neg_y


def evaluate_edge(X_train, X_test, y_train, y_test, df_test, channels):
    """RF regression на edge_h. Пороги 70/30 — только на train."""
    c = sorted(channels)
    X_tr = X_train[:, :, c].reshape(len(X_train), -1)
    X_te = X_test[:, :, c].reshape(len(X_test), -1)

    rf = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
    rf.fit(X_tr, y_train)
    pred_tr = rf.predict(X_tr)
    pred_te = rf.predict(X_te)

    long_thr = np.percentile(pred_tr, 70)
    short_thr = np.percentile(pred_tr, 30)

    buy = pred_te > long_thr
    sell = pred_te < short_thr
    pnl = np.where(buy, y_test, np.where(sell, -y_test, 0))
    trades = buy.sum() + sell.sum()

    yearly, neg_y = _yearly(pd.to_datetime(df_test['time']), pnl)

    return {
        'pf': profit_factor(pnl), 'trades': int(trades),
        'win': float(np.mean(pnl[pnl != 0] > 0)) if trades > 0 else 0,
        'buy': int(buy.sum()), 'sell': int(sell.sum()),
        'neg_years': neg_y, 'yearly': yearly,
        'n_features': len(c),
        'long_thr': float(long_thr), 'short_thr': float(short_thr),
    }


def evaluate_tb(X_train, X_eval, df_train, df_eval, channels):
    """RF classification на buy_sl3_tp3. Порог — 70-й перцентиль train-вероятностей (fixed, no sweep)."""
    col = 'buy_sl3_tp3'
    y_tr = df_train[col].values
    y_ev = df_eval[col].values

    mask_tr = y_tr != 0.5
    y_tr_bin = (y_tr[mask_tr] == 1.0).astype(int)

    c = sorted(channels)
    X_tr_fit = X_train[:, :, c].reshape(len(X_train), -1)[mask_tr]
    X_tr_all = X_train[:, :, c].reshape(len(X_train), -1)
    X_ev = X_eval[:, :, c].reshape(len(X_eval), -1)

    if y_tr_bin.sum() == 0 or (1 - y_tr_bin).sum() == 0:
        return None

    clf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
    clf.fit(X_tr_fit, y_tr_bin)

    # Fixed threshold: 70th percentile on train (top 30% most confident)
    prob_tr_all = clf.predict_proba(X_tr_all)[:, 1]
    thr = float(np.percentile(prob_tr_all, 70))

    # Apply to eval — no sweep, no eval data influences threshold
    prob_ev = clf.predict_proba(X_ev)[:, 1]
    trade = prob_ev > thr
    known_ev = y_ev != 0.5
    active = trade & known_ev
    pnl = np.where(active & (y_ev == 1.0), 3.0, np.where(active & (y_ev == 0.0), -3.0, 0.0))

    yearly, neg_y = _yearly(pd.to_datetime(df_eval['time']), pnl)
    return {
        'pf': profit_factor(pnl), 'trades': int(active.sum()),
        'win': float(np.mean(pnl[pnl != 0] > 0)) if (pnl != 0).sum() > 0 else 0,
        'neg_years': neg_y, 'yearly': yearly,
        'n_features': len(c),
    }


def _print_results(label, results):
    print(f'\n{"=" * 100}')
    print(f'{label}')
    print(f'{"=" * 100}')
    hdr = f"{'Variant':<15} {'ch':>3} {'PF':>7} {'Trades':>6} {'Win%':>6} {'NegY':>5} {'BUY':>5} {'SELL':>5}"
    if 'thr_pct' in next(iter(results.values()), {}):
        hdr += f" {'Thr%':>5}"
    print(hdr)
    print('-' * 80)

    base_pf = None
    for name, r in results.items():
        if name == 'all':
            base_pf = r['pf']
            break

    for name, r in results.items():
        line = f"  {name:<15} {r['n_features']:>3} {r['pf']:>7.3f} {r['trades']:>6} {r['win']:>6.1%} {r['neg_years']:>5}"
        if 'buy' in r:
            line += f" {r['buy']:>5} {r['sell']:>5}"
        if 'thr_pct' in r:
            line += f" {r['thr_pct']:>5}"
        print(line)

    if base_pf and base_pf != float('inf'):
        print(f"\n  Delta vs all ({base_pf:.3f}):")
        for name, r in sorted(results.items(), key=lambda x: -x[1]['pf']):
            if name == 'all':
                continue
            d = r['pf'] - base_pf
            print(f"    {name:<15} PF={r['pf']:.3f}  Δ={d:+.3f}")

    # Yearly for key variants
    for name in ['all', 'no_atr_dist', 'only_dir']:
        if name in results and 'yearly' in results[name]:
            r = results[name]
            yn = ' '.join(f'{y}:PF={d["pf"]:.2f}/{d["n_trades"]}' for y, d in sorted(r['yearly'].items()))
            print(f"  yearly [{name}]: {yn}")


def main():
    parser = argparse.ArgumentParser(description='Fractal channel ablation')
    parser.add_argument('--test', nargs='*', metavar='VARIANT',
                        help='Frozen test: оценить указанные варианты на test-сплите (например: all no_atr_dist)')
    parser.add_argument('--json-out', type=str, default=None)
    args = parser.parse_args()

    print('Загрузка данных...')
    train = pd.read_csv(DATA / 'Nero_XAUUSD_train_labeled.csv', sep=';')
    val = pd.read_csv(DATA / 'Nero_XAUUSD_validation_labeled.csv', sep=';')

    t_tr = pd.to_datetime(train['time'])
    t_v = pd.to_datetime(val['time'])
    print(f'train: {len(train):,} rows  {t_tr.min()} → {t_tr.max()}')
    print(f'val:   {len(val):,} rows  {t_v.min()} → {t_v.max()}')

    print('\nПарсинг тензоров...')
    X_tr, _ = parse_fractals_to_3d(train)

    if args.test:
        test = pd.read_csv(DATA / 'Nero_XAUUSD_test_labeled.csv', sep=';')
        t_te = pd.to_datetime(test['time'])
        print(f'test:  {len(test):,} rows  {t_te.min()} → {t_te.max()}')
        X_te, _ = parse_fractals_to_3d(test)
        eval_df = test
        X_eval = X_te
    else:
        X_eval, _ = parse_fractals_to_3d(val)
        eval_df = val

    # edge_6 target
    def _get_edge(df):
        up = pd.to_numeric(df['up_6'], errors='coerce').fillna(0).values
        dn = pd.to_numeric(df['dn_6'], errors='coerce').fillna(0).values
        return up - dn

    edge_tr = _get_edge(train)
    edge_eval = _get_edge(eval_df)

    variants_to_run = args.test if args.test else list(VARIANTS.keys())

    edge_results = {}
    for name in variants_to_run:
        if name not in VARIANTS:
            print(f"  SKIP: неизвестный вариант '{name}'")
            continue
        r = evaluate_edge(X_tr, X_eval, edge_tr, edge_eval, eval_df, VARIANTS[name])
        edge_results[name] = r

    _print_results('ABLATION: edge_6 (thresholds 70/30 on train ONLY)', edge_results)

    tb_results = {}
    for name in variants_to_run:
        if name not in VARIANTS:
            continue
        r = evaluate_tb(X_tr, X_eval, train, eval_df, VARIANTS[name])
        if r is None:
            print(f"  buy_sl3_tp3 {name}: SKIP (один класс на train known subset)")
            continue
        tb_results[name] = r

    _print_results('ABLATION: buy_sl3_tp3 (70th percentile threshold from train)', tb_results)

    if args.json_out:
        output = {'edge_6': edge_results, 'buy_sl3_tp3': tb_results}
        with open(args.json_out, 'w') as f:
            json.dump(output, f, indent=2, default=str)
        print(f'\nSaved: {args.json_out}')


if __name__ == '__main__':
    main()
