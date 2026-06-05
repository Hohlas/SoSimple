#!/usr/bin/env python3
"""
GridSearch для RF: ключевые гипотезы.
Признаки: первые 10 фракталов тензора (10×29=290 признаков).
Выборка: 10K train rows. Оценка на полной validation.
Метрика: validation PF, пороги 70/30 на train.
Результат — диагностический, не production-дефолт.
"""

import sys, os, argparse, json
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from ML.data_loader import parse_fractals_to_3d

DATA = PROJECT_ROOT / 'DATA'


def profit_factor(pnl):
    gp = float(pnl[pnl > 0].sum())
    gl = float(-pnl[pnl < 0].sum())
    return gp / gl if gl > 0 else (float('inf') if gp > 0 else 0.0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--json-out', type=str, default=None)
    args = parser.parse_args()

    print('Загрузка...')
    train = pd.read_csv(DATA / 'Nero_XAUUSD_train_labeled.csv', sep=';')
    val = pd.read_csv(DATA / 'Nero_XAUUSD_validation_labeled.csv', sep=';')

    print('Парсинг тензоров (10 фракталов)...')
    X_tr_full, _ = parse_fractals_to_3d(train)
    X_val_full, _ = parse_fractals_to_3d(val)
    X_tr_full = X_tr_full[:, :10, :]  # first 10 fractals
    X_val_full = X_val_full[:, :10, :]
    n_features = X_tr_full.shape[1] * X_tr_full.shape[2]  # 10 × 29 = 290

    # Sample 10K train
    rng = np.random.RandomState(42)
    idx = rng.choice(len(X_tr_full), min(10000, len(X_tr_full)), replace=False)
    X_tr = X_tr_full[idx].reshape(len(idx), -1)
    up6_tr = pd.to_numeric(train['up_6'].iloc[idx], errors='coerce').fillna(0).values
    dn6_tr = pd.to_numeric(train['dn_6'].iloc[idx], errors='coerce').fillna(0).values
    y_tr = up6_tr - dn6_tr

    X_val = X_val_full.reshape(len(X_val_full), -1)
    up6_val = pd.to_numeric(val['up_6'], errors='coerce').fillna(0).values
    dn6_val = pd.to_numeric(val['dn_6'], errors='coerce').fillna(0).values
    y_val = up6_val - dn6_val

    print(f'Train: {len(X_tr):,} rows × {n_features} features')
    print(f'Val:   {len(X_val):,} rows')

    # Baseline
    rf = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
    rf.fit(X_tr, y_tr)
    pred_tr = rf.predict(X_tr)
    pred_val = rf.predict(X_val)
    long_thr = np.percentile(pred_tr, 70)
    short_thr = np.percentile(pred_tr, 30)
    buy = pred_val > long_thr
    sell = pred_val < short_thr
    pnl = np.where(buy, y_val, np.where(sell, -y_val, 0))
    base_pf = profit_factor(pnl)
    base_trades = int(buy.sum() + sell.sum())
    print(f'\nBaseline (n=100, d=10, leaf=1): PF={base_pf:.3f}  trades={base_trades}')

    # ─── GridSearch (coarse) ─────────────────────────────────────────────
    print('\n=== GridSearch ===')
    configs = [
        (100, 10, 1), (100, 10, 5), (100, 20, 1), (100, 20, 5),
        (100, None, 5), (200, 10, 1), (200, 10, 5), (200, 20, 1),
        (200, 20, 5), (200, None, 5), (300, 10, 1), (300, None, 5),
    ]
    best = {'pf': 0, 'config': None}
    grid_output = []
    for n, d, l in configs:
        rf = RandomForestRegressor(
            n_estimators=n, max_depth=d, min_samples_leaf=l,
            random_state=42, n_jobs=-1,
        )
        rf.fit(X_tr, y_tr)
        p_tr = rf.predict(X_tr)
        p_val = rf.predict(X_val)
        lt = np.percentile(p_tr, 70)
        st = np.percentile(p_tr, 30)
        b = p_val > lt
        s = p_val < st
        pnl_v = np.where(b, y_val, np.where(s, -y_val, 0))
        pf = profit_factor(pnl_v)
        tr = int(b.sum() + s.sum())
        d_str = str(d) if d else 'None'
        print(f'  n={n:>3}  d={d_str:>4}  leaf={l}  PF={pf:.3f}  trades={tr:>5}  Δ={pf-base_pf:+.3f}')
        grid_output.append({'n': n, 'depth': d_str, 'leaf': l, 'pf': float(pf), 'trades': tr})
        if pf > best['pf']:
            best = {'pf': pf, 'config': f'n={n} d={d_str} leaf={l}'}

    print(f'\nBEST: PF={best["pf"]:.3f}  {best["config"]}  vs baseline Δ={best["pf"]-base_pf:+.3f}')

    # ─── OOB convergence (best config) ───────────────────────────────────
    print(f'\n=== OOB convergence (n_trees=10..300, d=None, leaf=5) ===')
    for n_est in [10, 25, 50, 75, 100, 150, 200, 300]:
        rf = RandomForestRegressor(
            n_estimators=n_est, max_depth=None, min_samples_leaf=5,
            random_state=42, n_jobs=-1, oob_score=True,
        )
        rf.fit(X_tr, y_tr)
        print(f'  n_est={n_est:>3}: OOB R²={rf.oob_score_:.4f}')

    # ─── max_depth=None leaf=5 vs baseline (full train, not sample) ──────
    print(f'\n=== max_depth=None, leaf=5 on FULL train (not sample) ===')
    X_tr_f = X_tr_full.reshape(len(X_tr_full), -1)
    up6_f = pd.to_numeric(train['up_6'], errors='coerce').fillna(0).values
    dn6_f = pd.to_numeric(train['dn_6'], errors='coerce').fillna(0).values
    y_tr_f = up6_f - dn6_f

    rf_f = RandomForestRegressor(
        n_estimators=200, max_depth=None, min_samples_leaf=5,
        random_state=42, n_jobs=-1,
    )
    rf_f.fit(X_tr_f, y_tr_f)
    p_tr_f = rf_f.predict(X_tr_f)
    p_val_f = rf_f.predict(X_val)
    lt_f = np.percentile(p_tr_f, 70)
    st_f = np.percentile(p_tr_f, 30)
    b_f = p_val_f > lt_f
    s_f = p_val_f < st_f
    pnl_f = np.where(b_f, y_val, np.where(s_f, -y_val, 0))
    pf_f = profit_factor(pnl_f)
    print(f'  unlimited depth (full train): PF={pf_f:.3f}  trades={int(b_f.sum()+s_f.sum())}')
    print(f'  baseline (n=100,d=10,leaf=1):  PF={base_pf:.3f}')
    print(f'  Δ={pf_f - base_pf:+.3f}')

    if args.json_out:
        output = {
            'baseline': {'n': 100, 'depth': 10, 'leaf': 1, 'pf': float(base_pf), 'trades': base_trades},
            'grid_results': grid_output,
            'best': best,
            'full_train_unlimited': {'n': 200, 'depth': 'None', 'leaf': 5, 'pf': float(pf_f)},
        }
        with open(args.json_out, 'w') as f:
            json.dump(output, f, indent=2)
        print(f'\nSaved: {args.json_out}')


if __name__ == '__main__':
    main()
