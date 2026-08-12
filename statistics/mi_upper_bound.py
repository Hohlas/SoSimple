from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_selection import mutual_info_classif, mutual_info_regression

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from ML.entry_path_task import ENTRY_PATH_V1_LIVE_SAFE_FEATURE_COLUMNS
from ML.entry_path_feature_bank import build_entry_path_feature_bank

__all__ = [
    'ENTRY_PATH_V1_LIVE_SAFE_FEATURE_COLUMNS',
    'estimate_mi',
    'estimate_mi_per_feature',
    'estimate_rolling_mi',
    'load_mi_data',
]


FUTURE_DERIVED_DENYLIST = {
    'predict', 'signal', 'ret_dir_atr_lag1',
    'ret_6_dir_atr', 'ret_12_dir_atr', 'ret_24_dir_atr',
    'fav_3_atr', 'adv_3_atr', 'fav_6_atr', 'adv_6_atr',
    'fav_12_atr', 'adv_12_atr', 'fav_24_atr', 'adv_24_atr',
}


def load_mi_data(csv_path: str, ohlc_path: str = 'DATA/XAUUSD_H1_OHLC.csv') -> dict:
    df = pd.read_csv(csv_path, delimiter=';')
    assert 'time' in df.columns
    df = df.sort_values('time').reset_index(drop=True)
    n_raw = len(df)
    df = df.drop_duplicates('time', keep='last').reset_index(drop=True)
    n_dedup_dropped = n_raw - len(df)

    overlap = set(ENTRY_PATH_V1_LIVE_SAFE_FEATURE_COLUMNS) & FUTURE_DERIVED_DENYLIST
    assert not overlap, f'Live-safe features overlap with denylist: {overlap}'

    ohlc = pd.read_csv(ohlc_path, delimiter=';')
    assert ohlc['time'].is_unique, 'OHLC time column has duplicates'
    merged = df.merge(ohlc[['time', 'open', 'close']], on='time', how='inner', validate='one_to_one')
    drop_ratio = 1.0 - len(merged) / len(df)
    assert drop_ratio <= 0.05, f'OHLC join dropped {drop_ratio:.1%} of rows'
    merged = merged.sort_values('time').reset_index(drop=True)

    df_with_bank = build_entry_path_feature_bank(merged)
    missing = [c for c in ENTRY_PATH_V1_LIVE_SAFE_FEATURE_COLUMNS if c not in df_with_bank.columns]
    assert not missing, f'Missing features after feature bank build: {missing}'
    X = df_with_bank[ENTRY_PATH_V1_LIVE_SAFE_FEATURE_COLUMNS].apply(
        pd.to_numeric, errors='coerce'
    ).fillna(0.0).values.astype(np.float64)

    # Таргеты — следующий бар (t+1), известны только после его закрытия:
    # это таргеты, не признаки — live-safe контракт признаков не нарушается.
    next_open = merged['open'].shift(-1)
    next_close = merged['close'].shift(-1)
    y_direction = np.sign(next_close - next_open).values.astype(np.float64)
    y_amplitude = np.abs(np.log(next_close / next_open)).values

    valid = np.isfinite(y_amplitude) & np.isfinite(y_direction)
    return {
        'X': X[valid],
        'y_direction': y_direction[valid],
        'y_amplitude': y_amplitude[valid],
        'feature_names': list(ENTRY_PATH_V1_LIVE_SAFE_FEATURE_COLUMNS),
        'time': merged['time'].values[valid],
        'n_dedup_dropped': int(n_dedup_dropped),
        'n_join_dropped': int(len(df) - len(merged)),
    }


def _mi_scores(X, y, k, random_state, discrete_target, discrete_mask):
    estimator = mutual_info_classif if discrete_target else mutual_info_regression
    return estimator(
        X, y, discrete_features=discrete_mask, n_neighbors=k, random_state=random_state,
    )


def estimate_mi(
    X: np.ndarray,
    y: np.ndarray,
    k: int = 5,
    n_folds: int = 10,
    n_permutations: int = 200,
    random_state: int = 42,
    discrete_target: bool = False,
    discrete_mask: np.ndarray | None = None,
) -> dict:
    n_samples, n_features = X.shape
    rng = np.random.RandomState(random_state)
    if discrete_mask is None:
        discrete_mask = False  # все признаки continuous
    else:
        discrete_mask = np.asarray(discrete_mask, dtype=bool)
    scores = _mi_scores(X, y, k, random_state, discrete_target, discrete_mask)
    # sklearn возвращает MI в nats (натуральный логарифм); переводим в bits:
    # формула R²-потолка 1 - 2^(-2·I) верна только для I в bits (аудит п.1).
    scores = scores / np.log(2)
    mean_mi = float(scores.mean())
    max_mi = float(scores.max())
    # Разброс по непересекающимся временным сегментам (данные отсортированы по времени).
    fold_scores = []
    for chunk in np.array_split(np.arange(n_samples), n_folds):
        if len(chunk) < max(2 * k + 1, 50):
            continue
        fold_scores.append(float(_mi_scores(
            X[chunk], y[chunk], k, rng.randint(0, 2**31), discrete_target, discrete_mask,
        ).mean() / np.log(2)))
    if len(fold_scores) >= 2:
        ci = np.percentile(fold_scores, [5, 95])
    else:
        ci = np.array([mean_mi, mean_mi])
    perm_scores = []
    for _ in range(n_permutations):
        y_perm = y[rng.permutation(n_samples)]
        perm_scores.append(float(_mi_scores(
            X, y_perm, k, rng.randint(0, 2**31), discrete_target, discrete_mask,
        ).mean() / np.log(2)))
    if n_permutations > 0:
        perm_p_value = float((np.sum(np.asarray(perm_scores) >= mean_mi) + 1) / (n_permutations + 1))
    else:
        perm_p_value = None  # p-value не вычислялось (аудит п.2)
    return {
        'mean_marginal_mi_bits': mean_mi,
        'max_marginal_mi_bits': max_mi,
        'mi_ci_p05': float(ci[0]),
        'mi_ci_p95': float(ci[1]),
        'perm_p_value': perm_p_value,
        # R² <= 1 - 2^(-2·I), I в bits; диагностическая оценка из маргинального MI
        'r2_ceiling': float(1 - 2**(-2 * mean_mi)),
        'n_samples': n_samples,
        'n_features': n_features,
        'n_folds_used': len(fold_scores),
        'discrete_target': discrete_target,
    }


def estimate_mi_per_feature(
    X: np.ndarray,
    y: np.ndarray,
    feature_names: list[str],
    k: int = 5,
    random_state: int = 42,
    discrete_target: bool = False,
    discrete_mask: np.ndarray | None = None,
) -> pd.DataFrame:
    scores = _mi_scores(X, y, k, random_state, discrete_target,
                        False if discrete_mask is None else np.asarray(discrete_mask, dtype=bool))
    df = pd.DataFrame({'feature': feature_names, 'mi_bits': scores / np.log(2)})
    return df.sort_values('mi_bits', ascending=False).reset_index(drop=True)


def estimate_rolling_mi(
    X: np.ndarray,
    y: np.ndarray,
    timestamps,
    window: int = 500,
    step: int = 100,
    k: int = 5,
    random_state: int = 42,
    discrete_target: bool = False,
) -> dict:
    n = len(y)
    ts_list, mi_list, r2_list = [], [], []
    for start in range(0, n - window + 1, step):
        end = start + window
        mi_result = estimate_mi(
            X[start:end], y[start:end], k=k,
            n_folds=5, n_permutations=0,
            random_state=random_state, discrete_target=discrete_target,
        )
        ts_list.append(str(timestamps[end - 1]))
        mi_list.append(mi_result['mean_marginal_mi_bits'])
        r2_list.append(mi_result['r2_ceiling'])
    return {
        'timestamps': ts_list,
        'mi_bits': mi_list,
        'r2_ceiling': r2_list,
        'window': window,
        'step': step,
    }
