from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.feature_selection import mutual_info_classif, mutual_info_regression


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
