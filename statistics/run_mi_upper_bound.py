# =============================================================================
# Файл: run_mi_upper_bound.py
# Назначение: runner оценки MI upper bound: train/validation, per-feature, групповой разбор, rolling, графики, JSON-отчёт
# Обновлён: 2026-08-12
# Зависимости:
#   Входные данные:
#     - DATA/Nero_{train,validation,test}_labeled.csv (откуда: processing/)
#     - DATA/XAUUSD_H1_OHLC.csv (откуда: MT4-экспорт)
#   Выходные данные:
#     - ML/reports/mi_upper_bound.json (куда: отчёт docs/reports/2026-08-11-mi-upper-bound.md)
#     - ML/plots/mi_per_feature.png, ML/plots/mi_rolling.png
#   Внутренние зависимости:
#     - mi_upper_bound.py (load_mi_data, estimate_mi, estimate_mi_per_feature, estimate_rolling_mi)
# Использование:
#   .venv/bin/python statistics/run_mi_upper_bound.py [--k 5] [--no-rolling] [--replot]
# =============================================================================
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from mi_upper_bound import (
    ENTRY_PATH_V1_LIVE_SAFE_FEATURE_COLUMNS,
    estimate_mi,
    estimate_mi_per_feature,
    estimate_rolling_mi,
    load_mi_data,
)


FEATURE_GROUPS = {
    'time': ['session_hour', 'weekday'],
    'strong': [c for c in ENTRY_PATH_V1_LIVE_SAFE_FEATURE_COLUMNS if 'strong' in c],
    'break': [c for c in ENTRY_PATH_V1_LIVE_SAFE_FEATURE_COLUMNS if 'break' in c],
    'direction_balance': [c for c in ENTRY_PATH_V1_LIVE_SAFE_FEATURE_COLUMNS if 'direction_balance' in c],
    'back': [c for c in ENTRY_PATH_V1_LIVE_SAFE_FEATURE_COLUMNS if 'back' in c],
    'impulse': [c for c in ENTRY_PATH_V1_LIVE_SAFE_FEATURE_COLUMNS if 'impulse' in c],
    'power': [c for c in ENTRY_PATH_V1_LIVE_SAFE_FEATURE_COLUMNS if 'power' in c],
    'count': [c for c in ENTRY_PATH_V1_LIVE_SAFE_FEATURE_COLUMNS if 'count' in c],
}


def group_mi(per_feature: list[dict]) -> dict:
    df = pd.DataFrame(per_feature)
    result = {}
    for group_name, group_features in FEATURE_GROUPS.items():
        mask = df['feature'].isin(group_features)
        if mask.any():
            result[group_name] = {
                'mean_mi': float(df.loc[mask, 'mi_bits'].mean()),
                'max_mi': float(df.loc[mask, 'mi_bits'].max()),
                'n_features': int(mask.sum()),
            }
    return result


def compute_rolling_mi(split_paths: list[str], ohlc_path: str, k: int, random_state: int) -> dict:
    parts = [load_mi_data(path, ohlc_path=ohlc_path) for path in split_paths]
    X = np.concatenate([p['X'] for p in parts])
    order = np.argsort(np.concatenate([p['time'] for p in parts]), kind='stable')
    X = X[order]
    y_dir = np.concatenate([p['y_direction'] for p in parts])[order]
    y_amp = np.concatenate([p['y_amplitude'] for p in parts])[order]
    timestamps = np.concatenate([p['time'] for p in parts])[order]

    # Границы split'ов (аудит п.10): последний timestamp каждого split'а —
    # для вертикальных линий на plot и disclosure окон на стыках.
    split_boundaries = []
    for p in parts[:-1]:
        split_boundaries.append(str(p['time'].max()))

    return {
        'direction': estimate_rolling_mi(
            X, y_dir, timestamps, window=500, step=100, k=k,
            random_state=random_state, discrete_target=True,
        ),
        'amplitude': estimate_rolling_mi(
            X, y_amp, timestamps, window=500, step=100, k=k,
            random_state=random_state, discrete_target=False,
        ),
        'splits': split_paths,
        'split_boundaries': split_boundaries,
        'disclosure': ('окно W=500 может охватывать два split\'а; значения MI на '
                       'границах имеют смешанный характер и интерпретируются как '
                       'сглаженный переход'),
        'n_samples_total': int(len(y_dir)),
    }


def plot_per_feature(results: dict, out_path: str = 'ML/plots/mi_per_feature.png') -> None:
    train = results.get('train', {})
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    for ax, target in zip(axes, ['direction', 'amplitude']):
        per_feat = train.get(f'per_feature_{target}', [])
        if not per_feat:
            continue
        df = pd.DataFrame(per_feat).head(20)
        ax.barh(df['feature'], df['mi_bits'])
        ax.set_xlabel('MI (bits)')
        ax.set_title(f'Top-20 features: {target}')
        ax.invert_yaxis()
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_rolling(results: dict, out_path: str = 'ML/plots/mi_rolling.png') -> None:
    rolling = results.get('rolling', {})
    if not rolling:
        return
    fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    boundaries = rolling.get('split_boundaries', [])
    for ax, target in zip(axes, ['direction', 'amplitude']):
        if target not in rolling:
            continue
        d = rolling[target]
        ts = [t[:10] for t in d['timestamps']]
        ax.plot(ts, d['mi_bits'], label='MI (bits)')
        ax.axhline(0.01, color='red', linestyle='--', alpha=0.5, label='threshold 0.01')
        for b in boundaries:
            idx = next((i for i, t in enumerate(d['timestamps']) if t >= b), None)
            if idx is not None:
                ax.axvline(idx, color='gray', linestyle=':', alpha=0.7)
        ax.set_ylabel('MI (bits)')
        ax.set_title(f'Rolling MI: {target}')
        ax.legend()
        ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description='MI Upper Bound estimation')
    parser.add_argument('--train', default='DATA/Nero_train_labeled.csv')
    parser.add_argument('--val', default='DATA/Nero_validation_labeled.csv')
    parser.add_argument('--ohlc', default='DATA/XAUUSD_H1_OHLC.csv')
    parser.add_argument('--output', default='ML/reports/mi_upper_bound.json')
    parser.add_argument('--k', type=int, default=5)
    parser.add_argument('--n-folds', type=int, default=10)
    parser.add_argument('--n-permutations', type=int, default=200)
    parser.add_argument('--random-state', type=int, default=42)
    parser.add_argument('--no-rolling', action='store_true')
    parser.add_argument('--replot', action='store_true',
                        help='перестроить графики из сохранённого JSON без пересчёта MI')
    args = parser.parse_args()

    if args.replot:
        with open(args.output) as f:
            results = json.load(f)
        plot_per_feature(results)
        plot_rolling(results)
        print(f'Plots rebuilt from {args.output}')
        return

    results = {
        'config': {
            'k': args.k,
            'n_folds': args.n_folds,
            'n_permutations': args.n_permutations,
            'random_state': args.random_state,
            'train_file': args.train,
            'val_file': args.val,
            'ohlc_file': args.ohlc,
            'feature_set': 'ENTRY_PATH_V1_LIVE_SAFE_FEATURE_COLUMNS',
            'n_features': 42,
            'r2_ceiling_formula': '1 - 2^(-2 * mean_marginal_mi_bits)',
            'mi_units': 'bits (sklearn возвращает nats; конверсия /ln(2) внутри estimate_mi)',
            'discrete_features': ['session_hour', 'weekday'],
            'targets': {
                'direction': 'sign(close[t+1] - open[t+1]) из OHLC-джойна, домен {-1,0,+1} (~3.8% нулей)',
                'amplitude': '|log(close[t+1] / open[t+1])| из OHLC-джойна',
            },
        },
    }

    for split_name, split_path in [('train', args.train), ('validation', args.val)]:
        data = load_mi_data(split_path, ohlc_path=args.ohlc)
        # session_hour (23 уровня) и weekday (5 уровней) — дискретные (аудит п.5):
        # передаём маску, чтобы sklearn не добавлял к ним noise как к continuous.
        discrete_mask = np.array([
            name in ('session_hour', 'weekday') for name in data['feature_names']
        ])
        split_result = {
            'n_samples': data['X'].shape[0],
            'n_features': data['X'].shape[1],
            'direction_class_balance': {
                str(int(c)): int(n) for c, n in zip(
                    *np.unique(data['y_direction'], return_counts=True))
            },
        }

        mi_dir = estimate_mi(
            data['X'], data['y_direction'],
            k=args.k, n_folds=args.n_folds, n_permutations=args.n_permutations,
            random_state=args.random_state, discrete_target=True,
            discrete_mask=discrete_mask,
        )
        split_result['direction'] = mi_dir

        mi_amp = estimate_mi(
            data['X'], data['y_amplitude'],
            k=args.k, n_folds=args.n_folds, n_permutations=args.n_permutations,
            random_state=args.random_state, discrete_target=False,
            discrete_mask=discrete_mask,
        )
        split_result['amplitude'] = mi_amp

        per_feat_dir = estimate_mi_per_feature(
            data['X'], data['y_direction'],
            data['feature_names'], k=args.k, random_state=args.random_state,
            discrete_target=True, discrete_mask=discrete_mask,
        )
        split_result['per_feature_direction'] = per_feat_dir.to_dict('records')

        per_feat_amp = estimate_mi_per_feature(
            data['X'], data['y_amplitude'],
            data['feature_names'], k=args.k, random_state=args.random_state,
            discrete_target=False, discrete_mask=discrete_mask,
        )
        split_result['per_feature_amplitude'] = per_feat_amp.to_dict('records')

        split_result['group_mi_direction'] = group_mi(split_result['per_feature_direction'])
        if 'per_feature_amplitude' in split_result:
            split_result['group_mi_amplitude'] = group_mi(split_result['per_feature_amplitude'])

        results[split_name] = split_result

    if not args.no_rolling:
        results['rolling'] = compute_rolling_mi(
            [args.train, args.val, 'DATA/Nero_test_labeled.csv'],
            ohlc_path=args.ohlc, k=args.k, random_state=args.random_state,
        )

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2, default=float)
    print(f'Results saved to {args.output}')

    plot_per_feature(results)
    plot_rolling(results)
    print('Plots saved to ML/plots/mi_per_feature.png, ML/plots/mi_rolling.png')


if __name__ == '__main__':
    main()
