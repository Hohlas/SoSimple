#!/usr/bin/env python3
"""
Triple Barrier direction signal experiment.
Проверяет предсказательную силу 100 бинарных направлений фракталов (±1)
на 12 TB-таргетах buy_sl*_tp* / sell_sl*_tp* (SL2/SL3 × TP3/TP6/TP9).

Гипотеза: направления несут сигнал о том, что случится первым — TP или SL,
при фиксированной стороне (BUY/SELL) и заданных уровнях.

Использование:
  .venv/bin/python -m ML.baseline.tb_direction_signal
  .venv/bin/python -m ML.baseline.tb_direction_signal --json-out ML/reports/tb_direction_signal.json

Вход: DATA/Nero_XAUUSD_*_labeled.csv
Выход: stdout (таблица результатов)
"""

import json
import argparse
import re
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from ML.data_loader import validate_data_contract

DATA = Path('DATA')

TB_COLUMNS = [
    'buy_sl2_tp3', 'buy_sl2_tp6', 'buy_sl2_tp9',
    'buy_sl3_tp3', 'buy_sl3_tp6', 'buy_sl3_tp9',
    'sell_sl2_tp3', 'sell_sl2_tp6', 'sell_sl2_tp9',
    'sell_sl3_tp3', 'sell_sl3_tp6', 'sell_sl3_tp9',
]


def parse_sl_tp(col):
    """Извлечь SL, TP, сторону из имени колонки: buy_sl2_tp3 → ('buy', 2, 3)."""
    m = re.match(r'(buy|sell)_sl(\d+)_tp(\d+)', col)
    side, sl, tp = m.groups()
    return side, int(sl), int(tp)


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


def evaluate_tb(train_df, val_df, test_df, col, X_tr, X_val, X_te):
    """Обучить RF-классификатор на TB-таргете col, оценить на val/test."""
    side, sl, tp = parse_sl_tp(col)

    y_tr = train_df[col].values
    mask_tr = y_tr != 0.5
    y_tr_bin = (y_tr[mask_tr] == 1.0).astype(int)
    X_tr_fit = X_tr[mask_tr]

    if y_tr_bin.sum() == 0 or (1 - y_tr_bin).sum() == 0:
        return None  # Все одного класса, модель бесполезна

    clf = RandomForestClassifier(
        n_estimators=100, max_depth=10, random_state=42, n_jobs=-1
    )
    clf.fit(X_tr_fit, y_tr_bin)

    prob_tr = clf.predict_proba(X_tr_fit)[:, 1]
    thr = float(np.percentile(prob_tr, 70))

    results = {}
    for split_name, X, df in [
        ('val', X_val, val_df), ('test', X_te, test_df)
    ]:
        y = df[col].values
        known = y != 0.5
        prob = clf.predict_proba(X)[:, 1]

        trade = prob > thr

        # --- Known-only mode ---
        known_active = trade & known
        pnl_k = np.where(
            known_active & (y == 1.0), tp,
            np.where(known_active & (y == 0.0), -sl, 0)
        )

        # --- All-rows mode ---
        pnl_a = np.where(
            trade & (y == 1.0), tp,
            np.where(trade & (y == 0.0), -sl, 0)
        )
        timeout_trades = int((trade & (y == 0.5)).sum())

        # Yearly PF (all-rows)
        times = pd.to_datetime(df['time'])
        yearly_pf = {}
        neg_years = 0
        pnl_a_series = pd.Series(pnl_a, index=df.index)
        for yr in sorted(times.dt.year.unique()):
            m = times.dt.year == yr
            pnl_y = pnl_a_series[m.values].values
            tr_y = (pnl_y != 0).sum()
            pf_y = profit_factor(pnl_y) if tr_y > 0 else 0
            yearly_pf[yr] = pf_y
            if pf_y < 1.0:
                neg_years += 1

        results[split_name] = {
            'known': {
                'pf': profit_factor(pnl_k),
                'trades': int(known_active.sum()),
                'win': float(np.mean(pnl_k[pnl_k != 0] > 0)) if (pnl_k != 0).sum() > 0 else 0,
            },
            'all_rows': {
                'pf': profit_factor(pnl_a),
                'trades': int((trade).sum()),
                'timeout_trades': timeout_trades,
                'win': float(np.mean(pnl_a[pnl_a != 0] > 0)) if (pnl_a != 0).sum() > 0 else 0,
                'mean_r': float(pnl_a.mean()),
                'neg_years': neg_years,
                'yearly_pf': {str(k): v for k, v in yearly_pf.items()},
            },
        }

    # Baseline: f0.dir
    f0_dir = X_te[:, 0].astype(int)
    y_te = test_df[col].values
    known_te = y_te != 0.5
    pnl_f0_k = np.zeros(len(test_df))
    for i in range(len(test_df)):
        if not known_te[i]:
            continue
        di = f0_dir[i]
        if side == 'buy' and di == 1:
            pnl_f0_k[i] = tp if y_te[i] == 1.0 else -sl
        elif side == 'sell' and di == -1:
            pnl_f0_k[i] = tp if y_te[i] == 1.0 else -sl
    baseline = {
        'pf': profit_factor(pnl_f0_k),
        'trades': int((pnl_f0_k != 0).sum()),
    }

    return results, baseline, thr


def main():
    parser = argparse.ArgumentParser(description='TB direction signal experiment')
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
    print('Извлечение 100 направлений фракталов...')
    X_tr = extract_dirs(train)
    X_val = extract_dirs(val)
    X_te = extract_dirs(test)
    print(f'  Tensor: {X_tr.shape} / {X_val.shape} / {X_te.shape}')

    print()
    print('=' * 90)

    all_results = {}
    for col in TB_COLUMNS:
        side, sl, tp = parse_sl_tp(col)
        out = evaluate_tb(train, val, test, col, X_tr, X_val, X_te)
        if out is None:
            print(f'\n{col}: SKIP (один класс на train known subset)')
            continue
        results, baseline, thr = out

        print(f'\n=== {col}  (side={side}  SL={sl}  TP={tp}  RR={tp/sl:.1f}) ===')
        print(f'  threshold (train): prob > {thr:.4f}')
        print(f'  baseline f0.dir: PF={baseline["pf"]:.3f}  trades={baseline["trades"]}')

        for split in ['val', 'test']:
            r = results[split]
            k = r['known']
            a = r['all_rows']
            print(f'  {split.upper()}:')
            print(f'    known-only  — PF={k["pf"]:.3f}  win={k["win"]:.1%}  trades={k["trades"]}')
            print(f'    all-rows    — PF={a["pf"]:.3f}  win={a["win"]:.1%}  trades={a["trades"]}  '
                  f'timeout={a["timeout_trades"]}  mean_r={a["mean_r"]:.4f}  neg_years={a["neg_years"]}')

        print(f'  Yearly test PF (all-rows):')
        for yr, pf_y in sorted(results['test']['all_rows']['yearly_pf'].items()):
            print(f'    {yr}: PF={pf_y:.3f}')

        all_results[col] = {
            'side': side, 'sl': sl, 'tp': tp,
            'threshold': float(thr),
            'baseline_f0_dir': baseline,
            'val': results['val'],
            'test': results['test'],
        }

    if args.json_out:
        output = {'meta': meta, 'instrument': 'XAUUSD', 'results': all_results}
        with open(args.json_out, 'w') as f:
            json.dump(json_safe(output), f, indent=2, allow_nan=False)
        print(f'\nSaved: {args.json_out}')

    print('\n' + '=' * 90)
    print('Сводка: лучшие TB-таргеты по Test all-rows PF')
    pf_list = []
    for col, r in all_results.items():
        pf_list.append((col, r['test']['all_rows']['pf']))
    pf_list.sort(key=lambda x: -x[1])
    for col, pf in pf_list:
        print(f'  {col}: PF={pf:.3f}')


if __name__ == '__main__':
    main()
