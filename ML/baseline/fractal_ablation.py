#!/usr/bin/env python3
"""
Ablation study: вклад групп признаков 29-канального тензора в edge_h и TB-таргеты.
Работает напрямую с parse_fractals_to_3d().

Группы:
  base:       price, direction, front, back, strong, break, reverse, power, count, impulse  (0–9)
  path:       up_12, dn_12, up_24, dn_24, up_48, dn_48, up_3, dn_3, up_6, dn_6  (10–19)
  atr_ratio:  log(fractal_atr / ATR)  (20)
  time:       hour_sin, hour_cos, time_pos, log_shift, log_delta_shift  (21–25)
  atr_dist:   signed_dist_atr, abs_dist_atr, dir_dist_atr  (26–28)

Варианты:
  all:        все 29 каналов
  no_path:    без path-группы (каналы 0–9 + 20–28)
  no_atr_dist: без ATR-distance (каналы 0–25)
  no_time:    без time (каналы 0–20 + 26–28)
  no_base:    без base (только channel groups)
  only_dir:   только direction (канал 1) — baseline

Цели: edge_6 (регрессия, пороги 70/30 на train), buy_sl3_tp3 (классификация по known)
Оценка только на validation. Test не участвует в выборе.

Использование:
  .venv/bin/python -m ML.baseline.fractal_ablation
"""

import argparse, json, sys, os
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ML.data_loader import parse_fractals_to_3d, N_FRACTAL_FEATURES
from ML.data_loader import DIST_ATR_IDX, ABS_DIST_ATR_IDX, DIR_DIST_ATR_IDX
from ML.data_loader import ATR_RATIO_IDX

DATA = PROJECT_ROOT / 'DATA'

# Feature group channel masks (0 = excluded, 1 = included)
BASE_CHANNELS = set(range(0, 10))        # price, dir, front, back, strong, break, rev, pwr, cnt, imp
PATH_CHANNELS = set(range(10, 20))       # all up/dn horizons
ATR_RATIO_CH = {20}
TIME_CHANNELS = set(range(21, 26))
ATR_DIST_CHANNELS = {26, 27, 28}

ALL_CHANNELS = set(range(N_FRACTAL_FEATURES))

VARIANTS = {
    'all':        ALL_CHANNELS,
    'no_path':    ALL_CHANNELS - PATH_CHANNELS,
    'no_atr_dist': ALL_CHANNELS - ATR_DIST_CHANNELS,
    'no_time':    ALL_CHANNELS - TIME_CHANNELS,
    'no_base':    ALL_CHANNELS - BASE_CHANNELS,
    'only_dir':   {1},
}


def profit_factor(pnl):
    gp = float(pnl[pnl > 0].sum())
    gl = float(-pnl[pnl < 0].sum())
    return gp / gl if gl > 0 else (float('inf') if gp > 0 else 0.0)


def evaluate_edge(X_train, X_val, y_train, y_val, df_val, channels):
    """RF regression на edge_6. Пороги 70/30 на train."""
    c = sorted(channels)
    X_tr = X_train[:, :, c].reshape(len(X_train), -1)
    X_v = X_val[:, :, c].reshape(len(X_val), -1)

    rf = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
    rf.fit(X_tr, y_train)
    pred_tr = rf.predict(X_tr)
    pred_v = rf.predict(X_v)

    long_thr = np.percentile(pred_tr, 70)
    short_thr = np.percentile(pred_tr, 30)

    edge_v = y_val  # edge_6 already computed
    buy = pred_v > long_thr
    sell = pred_v < short_thr
    pnl = np.where(buy, edge_v, np.where(sell, -edge_v, 0))
    trades = buy.sum() + sell.sum()

    times = pd.to_datetime(df_val['time'])
    yearly = {}
    neg_y = 0
    for yr in sorted(times.dt.year.unique()):
        m = times.dt.year == yr
        pnl_y = pnl[m.values]
        tr_y = (pnl_y != 0).sum()
        pf_y = profit_factor(pnl_y) if tr_y > 0 else 0
        yearly[int(yr)] = {'pf': round(pf_y, 3), 'n_trades': int(tr_y)}
        if pf_y < 1.0:
            neg_y += 1

    return {
        'pf': profit_factor(pnl), 'trades': int(trades),
        'win': float(np.mean(pnl[pnl != 0] > 0)) if trades > 0 else 0,
        'buy': int(buy.sum()), 'sell': int(sell.sum()),
        'neg_years': neg_y, 'yearly': yearly,
        'n_features': len(c),
    }


def evaluate_tb(X_train, X_val, df_train, df_val, channels):
    """RF classification на buy_sl3_tp3 (known outcomes only)."""
    col = 'buy_sl3_tp3'
    y_tr = df_train[col].values
    y_v = df_val[col].values

    mask_tr = y_tr != 0.5
    y_tr_bin = (y_tr[mask_tr] == 1.0).astype(int)

    c = sorted(channels)
    X_tr = X_train[:, :, c].reshape(len(X_train), -1)[mask_tr]
    X_v = X_val[:, :, c].reshape(len(X_val), -1)

    if y_tr_bin.sum() == 0 or (1 - y_tr_bin).sum() == 0:
        return None

    clf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
    clf.fit(X_tr, y_tr_bin)

    prob_tr = clf.predict_proba(X_tr)[:, 1]
    thr = float(np.percentile(prob_tr, 70))

    prob_v = clf.predict_proba(X_v)[:, 1]
    known_mask = y_v != 0.5
    trade = prob_v > thr
    active = trade & known_mask
    pnl = np.where(active & (y_v == 1.0), 3.0, np.where(active & (y_v == 0.0), -3.0, 0.0))

    trades = int(active.sum())
    times = pd.to_datetime(df_val['time'])
    yearly = {}
    neg_y = 0
    for yr in sorted(times.dt.year.unique()):
        m = times.dt.year == yr
        pnl_y = pnl[m.values]
        tr_y = (pnl_y != 0).sum()
        pf_y = profit_factor(pnl_y) if tr_y > 0 else 0
        yearly[int(yr)] = {'pf': round(pf_y, 3), 'n_trades': int(tr_y)}
        if pf_y < 1.0:
            neg_y += 1

    return {
        'pf': profit_factor(pnl), 'trades': trades,
        'win': float(np.mean(pnl[pnl != 0] > 0)) if trades > 0 else 0,
        'neg_years': neg_y, 'yearly': yearly,
        'n_features': len(c),
    }


def main():
    parser = argparse.ArgumentParser(description='Fractal channel ablation')
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
    X_tr, m_tr = parse_fractals_to_3d(train)
    X_v, m_v = parse_fractals_to_3d(val)

    # edge_6 target
    up6_tr = pd.to_numeric(train['up_6'], errors='coerce').fillna(0).values
    dn6_tr = pd.to_numeric(train['dn_6'], errors='coerce').fillna(0).values
    edge6_tr = up6_tr - dn6_tr
    up6_v = pd.to_numeric(val['up_6'], errors='coerce').fillna(0).values
    dn6_v = pd.to_numeric(val['dn_6'], errors='coerce').fillna(0).values
    edge6_v = up6_v - dn6_v

    print('\n' + '=' * 100)
    print('ABLATION: edge_6 (regression, thresholds 70/30 on train)')
    print('=' * 100)

    edge_results = {}
    for name, channels in VARIANTS.items():
        r = evaluate_edge(X_tr, X_v, edge6_tr, edge6_v, val, channels)
        edge_results[name] = r
        print(f"  {name:<15} ch={r['n_features']:>3}  PF={r['pf']:.3f}  "
              f"trades={r['trades']:>5}  win={r['win']:.1%}  "
              f"BUY={r['buy']}  SELL={r['sell']}  neg_y={r['neg_years']}")
        if name == 'all':
            base_pf = r['pf']

    # Delta vs all
    if base_pf:
        print(f"\n  Delta vs all ({base_pf:.3f}):")
        for name, r in sorted(edge_results.items(), key=lambda x: -x[1]['pf']):
            if name == 'all':
                continue
            d = r['pf'] - base_pf
            print(f"    {name:<15} PF={r['pf']:.3f}  Δ={d:+.3f}")

    print('\n' + '=' * 100)
    print('ABLATION: buy_sl3_tp3 (classification on known outcomes, threshold 70pct on train)')
    print('=' * 100)

    tb_results = {}
    for name, channels in VARIANTS.items():
        r = evaluate_tb(X_tr, X_v, train, val, channels)
        if r is None:
            print(f"  {name:<15} SKIP (один класс на train known subset)")
            continue
        tb_results[name] = r
        print(f"  {name:<15} ch={r['n_features']:>3}  PF={r['pf']:.3f}  "
              f"trades={r['trades']:>5}  win={r['win']:.1%}  neg_y={r['neg_years']}")

    if args.json_out:
        output = {'edge_6': edge_results, 'buy_sl3_tp3': tb_results}
        with open(args.json_out, 'w') as f:
            json.dump(output, f, indent=2, default=str)
        print(f'\nSaved: {args.json_out}')


if __name__ == '__main__':
    main()
