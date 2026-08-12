from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from mi_upper_bound import (
    estimate_mi,
    estimate_mi_per_feature,
    load_mi_data,
)


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
    args = parser.parse_args()

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

        results[split_name] = split_result

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2, default=float)
    print(f'Results saved to {args.output}')


if __name__ == '__main__':
    main()
