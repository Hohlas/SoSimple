# =============================================================================
# Файл: ML/baseline/benchmark_fractal_stop_breach.py
# Назначение: Dummy + RF baseline — предсказание пробоя уровня fractal0 (Stage 1)
# Язык: Python 3.10+
# Обновлён: 2026-06-10
# Зависимости: numpy, pandas, scikit-learn
#   Входные данные: DATA/Nero_XAUUSD_train_labeled.csv, ...validation_labeled.csv
#   Выходные данные: ML/reports/fractal_stop_breach_baseline.json
#   Примечание: test не открывается в Stage 1 (заморожен до freeze-решения)
# Использование:
#   source ~/git/SoSimple/.venv/bin/activate
#   python -m ML.baseline.benchmark_fractal_stop_breach
# =============================================================================

import argparse
import json
import os
import sys

import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score, average_precision_score

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'processing'))
from label_signals import (  # noqa: E402
    BR_BREACH_COLUMNS,
    BR_BREACH_HORIZONS,
    BR_BREACH_OFFSETS,
    BR_BREACH_OFFSETS_PRIMARY,
)

# Feature contract: 10 live-safe каналов × 100 фракталов + ATR
BASE_CHANNEL_KEYS = [
    'price', 'direction', 'front', 'back', 'strong',
    'break', 'reverse', 'power', 'count', 'impulse',
]


def extract_flat_base_features(df, n_fractals=100):
    """Извлечь BASE_CHANNEL_KEYS × n_fractals как плоские float64 признаки + ATR."""
    features = []
    feature_names = []
    for level in range(n_fractals):
        col = f'fractal{level}'
        if col not in df.columns:
            break
        parts = df[col].astype(str).str.split(':', expand=True)
        key_to_idx = {
            'price': 1, 'direction': 2, 'front': 3, 'back': 4,
            'strong': 5, 'break': 6, 'reverse': 7, 'power': 8,
            'count': 9, 'impulse': 10,
        }
        for key in BASE_CHANNEL_KEYS:
            idx = key_to_idx[key]
            vals = pd.to_numeric(parts[idx], errors='coerce').fillna(0.0).values
            features.append(vals.astype(np.float64))
            feature_names.append(f'f{level}_{key}')
    if 'ATR' in df.columns:
        features.append(df['ATR'].values.astype(np.float64))
        feature_names.append('ATR')
    X = np.column_stack(features)
    return X, feature_names


def load_split(path, purge_bars=12):
    """Загрузить сплит, добавить колонку _year, применить H-барный purge на хвосте."""
    df = pd.read_csv(path, sep=';')
    if purge_bars > 0 and len(df) > purge_bars:
        df = df.iloc[:-purge_bars]
    df['_year'] = pd.to_datetime(
        df['time'], format='%Y.%m.%d %H:%M', errors='coerce'
    ).dt.year
    return df


def compute_metrics(y_true, y_pred_proba, years=None):
    """AUC, PR-AUC, breach_rate, lift@20%. При years — годовые срезы."""
    mask = ~np.isnan(y_true)
    y_true = y_true[mask]
    y_pred_proba = y_pred_proba[mask]
    if years is not None:
        years = years[mask]
    if len(y_true) < 10:
        return None

    unique_classes = np.unique(y_true)
    if len(unique_classes) < 2:
        return {
            'auc': None, 'pr_auc': None,
            'breach_rate': round(float(y_true.mean()), 4),
            'n': int(len(y_true)),
            'note': 'single_class',
        }

    auc = roc_auc_score(y_true, y_pred_proba)
    pr_auc = average_precision_score(y_true, y_pred_proba)
    overall_rate = float(y_true.mean())

    cutoff = np.quantile(y_pred_proba, 0.20)
    low_risk_mask = y_pred_proba <= cutoff
    low_risk_rate = float(y_true[low_risk_mask].mean()) if low_risk_mask.sum() > 0 else 0.0
    lift = overall_rate / low_risk_rate if low_risk_rate > 0 else float('inf')

    metrics = {
        'auc': round(auc, 4),
        'pr_auc': round(pr_auc, 4),
        'breach_rate': round(overall_rate, 4),
        'low_risk_breach_rate': round(low_risk_rate, 4),
        'lift': round(lift, 2),
        'n': int(len(y_true)),
    }

    if years is not None:
        yearly = {}
        for yr in sorted(set(years)):
            ym = years == yr
            if ym.sum() >= 5:
                yr_unique = np.unique(y_true[ym])
                if len(yr_unique) >= 2:
                    try:
                        yr_auc = roc_auc_score(y_true[ym], y_pred_proba[ym])
                    except ValueError:
                        yr_auc = None
                else:
                    yr_auc = None
                yearly[int(yr)] = {
                    'auc': round(yr_auc, 4) if yr_auc is not None else None,
                    'n': int(ym.sum()),
                    'breach_rate': round(float(y_true[ym].mean()), 4),
                }
        metrics['yearly'] = yearly
    return metrics


def main():
    parser = argparse.ArgumentParser(description='Baseline: fractal stop breach (Stage 1)')
    parser.add_argument('--train', default='DATA/Nero_XAUUSD_train_labeled.csv')
    parser.add_argument('--val', default='DATA/Nero_XAUUSD_validation_labeled.csv')
    parser.add_argument('--target', default=None,
                        help='Конкретная колонка (default: все primary-колонки)')
    parser.add_argument('--purge-bars', type=int, default=12)
    parser.add_argument('--output-json', default='ML/reports/fractal_stop_breach_baseline.json')
    parser.add_argument('--n-estimators', type=int, default=200)
    parser.add_argument('--max-depth', type=int, default=12)
    parser.add_argument('--min-samples-leaf', type=int, default=50)
    parser.add_argument('--include-diagnostic-offsets', action='store_true',
                        help='Включить off00 (diagnostic only) в отчёт')
    args = parser.parse_args()

    train_df = load_split(args.train, args.purge_bars)
    val_df = load_split(args.val, args.purge_bars)

    X_train, feature_names = extract_flat_base_features(train_df)
    X_val, _ = extract_flat_base_features(val_df)

    if args.target:
        targets = [args.target]
    else:
        targets = []
        for h in BR_BREACH_HORIZONS:
            for off in (BR_BREACH_OFFSETS_PRIMARY if not args.include_diagnostic_offsets
                        else BR_BREACH_OFFSETS):
                off_str = f'{int(off * 10):02d}'
                targets.append(f'buy_stop_broken_H{h}_off{off_str}_flag')
                targets.append(f'sell_stop_broken_H{h}_off{off_str}_flag')

    results = {}

    for target_col in targets:
        y_train = train_df[target_col].values
        y_val = val_df[target_col].values

        train_mask = ~np.isnan(y_train)
        val_mask = ~np.isnan(y_val)

        n_train = train_mask.sum()
        n_val = val_mask.sum()

        if n_train < 50:
            print(f'{target_col}: SKIP (train n={n_train})')
            results[target_col] = {'status': 'SKIP', 'reason': f'train n={n_train}'}
            continue

        train_breach_rate = float(y_train[train_mask].mean())
        print(f'\n--- {target_col} ---')
        print(f'  Train: n={n_train}, breach_rate={train_breach_rate:.3f}')
        print(f'  Val:   n={n_val}')

        X_tr = X_train[train_mask]
        y_tr = y_train[train_mask]
        X_v = X_val[val_mask]
        y_v = y_val[val_mask]

        dummy_results = {}
        for strategy in ['most_frequent', 'stratified', 'uniform']:
            dummy = DummyClassifier(strategy=strategy, random_state=42)
            dummy.fit(X_tr, y_tr)
            pred_dummy = dummy.predict_proba(X_v)[:, 1]
            dummy_results[strategy] = compute_metrics(y_v, pred_dummy)
            print(f'  Dummy/{strategy}: AUC={dummy_results[strategy].get("auc", "N/A")}')

        rf = RandomForestClassifier(
            n_estimators=args.n_estimators,
            max_depth=args.max_depth,
            min_samples_leaf=args.min_samples_leaf,
            random_state=42,
            n_jobs=-1,
        )
        rf.fit(X_tr, y_tr)

        pred_val = rf.predict_proba(X_v)[:, 1]
        val_metrics = compute_metrics(y_v, pred_val, val_df['_year'].values[val_mask])

        results[target_col] = {
            'train_n': int(n_train),
            'train_breach_rate': round(train_breach_rate, 4),
            'val_n': int(n_val),
            'test_not_run': True,
            'dummy': dummy_results,
            'rf_val': val_metrics,
        }

        if val_metrics:
            print(f'  RF val:  AUC={val_metrics.get("auc", "N/A"):.3f} '
                  f'PR-AUC={val_metrics.get("pr_auc", "N/A"):.3f} '
                  f'lift={val_metrics.get("lift", "N/A")}')

    os.makedirs(os.path.dirname(args.output_json), exist_ok=True)
    report = {
        'config': {
            'purge_bars': args.purge_bars,
            'n_estimators': args.n_estimators,
            'max_depth': args.max_depth,
            'min_samples_leaf': args.min_samples_leaf,
            'feature_keys': BASE_CHANNEL_KEYS,
            'n_features': X_train.shape[1],
            'targets': targets,
        },
        'test_not_run': True,
        'results': results,
    }
    with open(args.output_json, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    print(f'\nSaved: {args.output_json}')


if __name__ == '__main__':
    main()
