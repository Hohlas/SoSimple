#!/usr/bin/env python3
"""
Directions + flat up/dn → TB experiment.
**ВНИМАНИЕ:** flat up/dn в labeled CSV — future-derived (label_updn() отслеживает
эволюцию fractal0 ПОСЛЕ decision-time). Использование их как признаков = leakage.
Результаты TB PF > 1 только при наличии up/dn — НЕ считать сигналом.

Этот скрипт оставлен как документация отрицательного результата.

Корректная альтернатива: fractal-level path-каналы в тензоре (индексы 10–19),
проверенные в fractal_ablation.py (`only_path` PF=3.97 на edge_6 test).

Использование:
  .venv/bin/python -m ML.baseline.direction_updn_signal
"""

import argparse, json, sys, os
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
DATA = PROJECT_ROOT / 'DATA'


def extract_dirs(df, n_fractals=100):
    X = np.zeros((len(df), n_fractals), dtype=np.float32)
    for i in range(n_fractals):
        col = f'fractal{i}'
        if col not in df.columns:
            break
        parts = df[col].astype(str).str.split(':', expand=True)
        X[:, i] = pd.to_numeric(parts[2], errors='coerce').fillna(0).values
    return X


def profit_factor(pnl):
    gp = float(pnl[pnl > 0].sum())
    gl = float(-pnl[pnl < 0].sum())
    return gp / gl if gl > 0 else (float('inf') if gp > 0 else 0.0)


def _yearly(times, pnl):
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
    return yearly, neg_y


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', action='store_true')
    args = parser.parse_args()

    train = pd.read_csv(DATA / 'Nero_XAUUSD_train_labeled.csv', sep=';')
    eval_name = 'test' if args.test else 'validation'
    eval_df = pd.read_csv(DATA / f'Nero_XAUUSD_{eval_name}_labeled.csv', sep=';')

    t_tr = pd.to_datetime(train['time'])
    t_ev = pd.to_datetime(eval_df['time'])
    print(f'train: {len(train):,}  {t_tr.min()} → {t_tr.max()}')
    print(f'{eval_name}: {len(eval_df):,}  {t_ev.min()} → {t_ev.max()}')

    up6_tr = pd.to_numeric(train['up_6'], errors='coerce').fillna(0).values
    dn6_tr = pd.to_numeric(train['dn_6'], errors='coerce').fillna(0).values
    y_tr = up6_tr - dn6_tr
    up6_ev = pd.to_numeric(eval_df['up_6'], errors='coerce').fillna(0).values
    dn6_ev = pd.to_numeric(eval_df['dn_6'], errors='coerce').fillna(0).values
    y_ev = up6_ev - dn6_ev

    X_tr = extract_dirs(train)
    X_ev = extract_dirs(eval_df)

    rf = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
    rf.fit(X_tr, y_tr)
    pred_tr = rf.predict(X_tr)
    pred_ev = rf.predict(X_ev)

    long_thr = np.percentile(pred_tr, 70)
    short_thr = np.percentile(pred_tr, 30)

    buy = pred_ev > long_thr
    sell = pred_ev < short_thr
    pnl = np.where(buy, y_ev, np.where(sell, -y_ev, 0))
    yearly, neg_y = _yearly(pd.to_datetime(eval_df['time']), pnl)

    print(f'edge_6 (dir only): PF={profit_factor(pnl):.3f}  trades={int(buy.sum()+sell.sum())}  win={float(np.mean(pnl[pnl!=0]>0)):.1%}  neg_y={neg_y}')
    yn = '  '.join(f'{y}:{d["pf"]:.2f}' for y, d in sorted(yearly.items()))
    print(f'yearly: {yn}')

    print('\nFlat up/dn = future-derived target columns. Not usable as features (leakage).')
    print('См. fractal_ablation.py: only_path — fractal-level path-каналы (10–19).')


if __name__ == '__main__':
    main()
