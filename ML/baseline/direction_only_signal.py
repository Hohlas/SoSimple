#!/usr/bin/env python3
"""
Direction-only signal experiment.
Проверяет предсказательную силу 100 бинарных направлений фракталов (±1).

Использование:
  .venv/bin/python -m ML.baseline.direction_only_signal
  .venv/bin/python -m ML.baseline.direction_only_signal --json-out ML/reports/direction_only_signal.json

Вход: DATA/Nero_XAUUSD_*_labeled.csv
Выход: stdout (таблица результатов)
"""

import json
import argparse
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score
from scipy.stats import pearsonr
from ML.data_loader import validate_data_contract

DATA = Path('DATA')


def extract_dirs(df, n_fractals=100):
    """Извлечь direction (idx 2) из fractal0..fractal{N-1}. Возвращает (N, n_fractals) float32 (±1)."""
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


def json_safe(obj):
    """Рекурсивно заменить inf/nan на null в dict/list для строгого JSON."""
    if isinstance(obj, dict):
        return {k: json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [json_safe(v) for v in obj]
    if isinstance(obj, float):
        if np.isinf(obj) or np.isnan(obj):
            return None
    return obj


def evaluate(train_df, val_df, test_df, horizon, instrument):
    """Обучить RF на edge_h = up_h - dn_h, оценить на val/test."""
    up_tr = pd.to_numeric(train_df[f'up_{horizon}'], errors='coerce').fillna(0).values
    dn_tr = pd.to_numeric(train_df[f'dn_{horizon}'], errors='coerce').fillna(0).values
    edge_tr = up_tr - dn_tr

    rf = RandomForestRegressor(
        n_estimators=100, max_depth=10, random_state=42, n_jobs=-1
    )
    X_tr = extract_dirs(train_df)
    rf.fit(X_tr, edge_tr)
    pred_tr = rf.predict(X_tr)

    long_thr = np.percentile(pred_tr, 70)
    short_thr = np.percentile(pred_tr, 30)

    results = {}
    for split_name, df in [('val', val_df), ('test', test_df)]:
        X = extract_dirs(df)
        up = pd.to_numeric(df[f'up_{horizon}'], errors='coerce').fillna(0).values
        dn = pd.to_numeric(df[f'dn_{horizon}'], errors='coerce').fillna(0).values
        edge = up - dn

        pred = rf.predict(X)
        buy = pred > long_thr
        sell = pred < short_thr
        skip = ~(buy | sell)
        pnl = np.where(buy, edge, np.where(sell, -edge, 0))
        trades = buy.sum() + sell.sum()

        r2 = r2_score(edge, pred)
        r, _ = pearsonr(edge, pred)

        # Yearly
        times = pd.to_datetime(df['time'])
        yearly_pf = {}
        neg_years = 0
        for yr in sorted(times.dt.year.unique()):
            m = times.dt.year == yr
            pnl_y = pnl[m.values]
            tr_y = (pnl_y != 0).sum()
            pf_y = profit_factor(pnl_y) if tr_y > 0 else 0
            yearly_pf[yr] = pf_y
            if pf_y < 1.0:
                neg_years += 1

        results[split_name] = {
            'r2': r2, 'r': r, 'pf': profit_factor(pnl),
            'win': np.mean(pnl[pnl != 0] > 0) if trades > 0 else 0,
            'trades': int(trades), 'buy': int(buy.sum()), 'sell': int(sell.sum()),
            'skip': int(skip.sum()), 'mean_r': float(pnl.mean()),
            'neg_years': neg_years, 'yearly_pf': yearly_pf,
        }

    # Baseline: fractal0.dir
    X_te = extract_dirs(test_df)
    f0_dir = X_te[:, 0].astype(int)
    up_te = pd.to_numeric(test_df[f'up_{horizon}'], errors='coerce').fillna(0).values
    dn_te = pd.to_numeric(test_df[f'dn_{horizon}'], errors='coerce').fillna(0).values
    edge_te = up_te - dn_te
    buy_f0 = f0_dir == 1
    sell_f0 = f0_dir == -1
    pnl_f0 = np.where(buy_f0, edge_te, np.where(sell_f0, -edge_te, 0))
    baseline = {
        'pf': profit_factor(pnl_f0),
        'trades': int(buy_f0.sum() + sell_f0.sum()),
        'mean_r': float(pnl_f0.mean()),
    }

    return results, baseline, long_thr, short_thr


def main():
    parser = argparse.ArgumentParser(description='Direction-only signal experiment')
    parser.add_argument('--json-out', type=str, default=None, help='Save results to JSON file')
    args = parser.parse_args()

    train = pd.read_csv(DATA / 'Nero_XAUUSD_train_labeled.csv', sep=';')
    val = pd.read_csv(DATA / 'Nero_XAUUSD_validation_labeled.csv', sep=';')
    test = pd.read_csv(DATA / 'Nero_XAUUSD_test_labeled.csv', sep=';')

    for name, df in [('train', train), ('val', val), ('test', test)]:
        validate_data_contract(df, source=f'Nero_XAUUSD_{name}_labeled.csv')

    meta = {}
    for name, df in [('train', train), ('val', val), ('test', test)]:
        t = pd.to_datetime(df['time'])
        meta[name] = {'rows': len(df), 'start': str(t.min()), 'end': str(t.max())}
        print(f'{name}: {len(df):,} rows  {t.min()} → {t.max()}')

    print()

    all_results = {}
    for h in [6, 12]:
        results, baseline, long_thr, short_thr = evaluate(train, val, test, h, 'XAUUSD')
        print(f'=== edge_{h} = up_{h} - dn_{h} ===')
        print(f'  thresholds (train): LONG > {long_thr:.4f}  SHORT < {short_thr:.4f}')
        print(f'  baseline f0.dir: PF={baseline["pf"]:.3f}  trades={baseline["trades"]}')

        for split in ['val', 'test']:
            r = results[split]
            print(f'  {split.upper()}: R²={r["r2"]:.4f}  r={r["r"]:.3f}  PF={r["pf"]:.3f}  win={r["win"]:.1%}  '
                  f'trades={r["trades"]}  BUY={r["buy"]}  SELL={r["sell"]}  SKIP={r["skip"]}  '
                  f'mean_r={r["mean_r"]:.4f}  neg_years={r["neg_years"]}')

        print('  Yearly test PF:')
        for yr, pf_y in sorted(results['test']['yearly_pf'].items()):
            print(f'    {yr}: PF={pf_y:.3f}')
        print()

        # Сериализуем yearly_pf ключи в str для JSON
        r_test = dict(results['test'])
        r_test['yearly_pf'] = {str(k): v for k, v in r_test['yearly_pf'].items()}
        r_val = dict(results['val'])
        r_val['yearly_pf'] = {str(k): v for k, v in r_val['yearly_pf'].items()}
        all_results[f'edge_{h}'] = {
            'thresholds': {'long': float(long_thr), 'short': float(short_thr)},
            'baseline_f0_dir': baseline,
            'val': r_val,
            'test': r_test,
        }

    if args.json_out:
        output = {'meta': meta, 'instrument': 'XAUUSD', 'results': all_results}
        with open(args.json_out, 'w') as f:
            json.dump(json_safe(output), f, indent=2, allow_nan=False)
        print(f'Saved: {args.json_out}')


if __name__ == '__main__':
    main()
