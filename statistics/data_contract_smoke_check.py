#!/usr/bin/env python3
"""
Smoke-check данных перед ML-экспериментами.
Быстрая автоматическая проверка инвариантов тензора и меток.
Запускать до любых опытов с PF/R².

Использование:
  # С дефолтными путями (DATA/Nero_XAUUSD_*_labeled.csv):
  .venv/bin/python statistics/data_contract_smoke_check.py

  # С явными путями:
  .venv/bin/python statistics/data_contract_smoke_check.py \
      --train DATA/Nero_XAUUSD_train_labeled.csv \
      --val DATA/Nero_XAUUSD_validation_labeled.csv \
      --test DATA/Nero_XAUUSD_test_labeled.csv

Если smoke-check не прошёл — результаты модели имеют статус DIAGNOSTIC_ONLY или FAIL.
PF/R² нельзя интерпретировать при проваленных инвариантах данных.
"""

import argparse
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / 'DATA'
DEFAULT_FILES = {
    'train': DATA_DIR / 'Nero_XAUUSD_train_labeled.csv',
    'validation': DATA_DIR / 'Nero_XAUUSD_validation_labeled.csv',
    'test': DATA_DIR / 'Nero_XAUUSD_test_labeled.csv',
}


def check(msg, cond):
    if cond:
        print(f'  ✅ {msg}')
    else:
        print(f'  ✗ FAIL: {msg}')
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description='Data contract smoke-check перед ML-экспериментами')
    parser.add_argument('--train', type=str, default=str(DEFAULT_FILES['train']),
                        help='Путь к train CSV (по умолчанию: DATA/Nero_XAUUSD_train_labeled.csv)')
    parser.add_argument('--val', type=str, default=str(DEFAULT_FILES['validation']),
                        help='Путь к validation CSV (по умолчанию: DATA/Nero_XAUUSD_validation_labeled.csv)')
    parser.add_argument('--test', type=str, default=str(DEFAULT_FILES['test']),
                        help='Путь к test CSV (по умолчанию: DATA/Nero_XAUUSD_test_labeled.csv)')
    args = parser.parse_args()

    files = {
        'train': args.train,
        'validation': args.val,
        'test': args.test,
    }

    from ML.data_loader import parse_fractals_to_3d, N_FRACTAL_FEATURES
    from ML.data_loader import DIST_ATR_IDX, ABS_DIST_ATR_IDX, DIR_DIST_ATR_IDX
    from ML.data_loader import ATR_RATIO_IDX

    for name, path in files.items():
        print(f'\n━━━ {name.upper()} ({path}) ━━━')
        df = pd.read_csv(path, sep=';')
        n_rows = len(df)

        # 1. Tensor shape
        X, mask = parse_fractals_to_3d(df)
        check(f'shape = ({X.shape[0]}, {X.shape[1]}, {X.shape[2]}) — ожидается ({n_rows}, 100, {N_FRACTAL_FEATURES})',
              X.shape == (n_rows, 100, N_FRACTAL_FEATURES))

        valid = X[mask]

        # 2. No NaN/inf
        check(f'нет NaN: {np.isnan(X).sum()}, нет inf: {np.isinf(X).sum()}',
              not np.isnan(X).any() and not np.isinf(X).any())

        # 3. Price not binary (< 20 unique values → suspicious)
        price_vals = X[:, :, 0][mask]
        n_unique_price = len(np.unique(np.round(price_vals, 2)))
        check(f'price: {n_unique_price:.0f} уникальных значений (не бинарный)',
              n_unique_price > 2)

        # 4. Direction ∈ {-1, 1}
        dir_vals = X[:, :, 1][mask]
        dir_unique = set(np.unique(dir_vals[~np.isnan(dir_vals)]))
        check(f'direction values: {dir_unique} (expect {{-1, 1}})',
              dir_unique.issubset({-1, 1}) and len(dir_unique) > 0)

        # 5. Up/dn values within expected normalized range (piecewise, монотонность не гарантирована)
        up_indices = {'up_3': 16, 'up_6': 18, 'up_12': 10, 'up_24': 12, 'up_48': 14}
        dn_indices = {'dn_3': 17, 'dn_6': 19, 'dn_12': 11, 'dn_24': 13, 'dn_48': 15}
        up_vals_all = np.concatenate([valid[:, i] for i in up_indices.values()])
        dn_vals_all = np.concatenate([valid[:, i] for i in dn_indices.values()])
        check(f'up/dn в [0, 1]: up=[{up_vals_all.min():.3f}, {up_vals_all.max():.3f}], dn=[{dn_vals_all.min():.3f}, {dn_vals_all.max():.3f}]',
              up_vals_all.min() >= -1e-6 and dn_vals_all.min() >= -1e-6)

        # 6. ATR_ratio — log-scale, может быть отрицательным
        atr_vals = valid[:, ATR_RATIO_IDX]
        check(f'ATR_ratio: [{atr_vals.min():.3f}, {atr_vals.max():.3f}] (не NaN/inf)',
              not (np.isnan(atr_vals).any() or np.isinf(atr_vals).any()))

        # 7. ATR-distance not all in [0,1]
        dist = valid[:, DIST_ATR_IDX]
        dmin, dmax = dist.min(), dist.max()
        in_01 = ((dist >= 0) & (dist <= 1)).mean()
        check(f'signed_dist_atr: [{dmin:.1f}, {dmax:.1f}], в [0,1]: {in_01:.1%} (не должен быть все в [0,1])',
              in_01 < 0.99 and dmax > 1.0)

        # 8. abs >= 0, dir == dist × direction
        abs_vals = valid[:, ABS_DIST_ATR_IDX]
        check(f'abs_dist_atr >= 0',
              (abs_vals >= -1e-6).all())
        check(f'dir_dist_atr == dist × direction',
              np.allclose(valid[:, DIR_DIST_ATR_IDX],
                          valid[:, DIST_ATR_IDX] * valid[:, 1], atol=1e-5))

        # 9. TB target class fractions (не все нули, не все единицы)
        tb_cols = [c for c in df.columns if ('buy_sl' in c or 'sell_sl' in c) and '_tp' in c]
        for col in sorted(tb_cols):
            vals = df[col].dropna()
            vc = vals.value_counts(normalize=True)
            frac_known = (vals != 0.5).mean()
            check(f'{col}: known={frac_known:.1%}, TP={(vals==1.0).mean():.1%}, SL={(vals==0.0).mean():.1%}, timeout={(vals==0.5).mean():.1%}',
                  frac_known > 0.05)  # хотя бы 5% известных исходов

    print(f'\n{"="*60}')
    print('ALL CHECKS PASSED')


if __name__ == '__main__':
    main()
