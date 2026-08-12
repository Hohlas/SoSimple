import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

_MODULE_PATH = Path(__file__).resolve().parents[1] / 'statistics' / 'mi_upper_bound.py'
_spec = importlib.util.spec_from_file_location('mi_upper_bound', _MODULE_PATH)
mi_upper_bound = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mi_upper_bound)

estimate_mi = mi_upper_bound.estimate_mi
estimate_mi_per_feature = mi_upper_bound.estimate_mi_per_feature
load_mi_data = mi_upper_bound.load_mi_data
estimate_rolling_mi = mi_upper_bound.estimate_rolling_mi


def test_estimate_rolling_mi_returns_time_series():
    rng = np.random.RandomState(42)
    n = 1000
    X = rng.randn(n, 2)
    y = X[:, 0] + rng.randn(n) * 0.5
    timestamps = pd.date_range('2020-01-01', periods=n, freq='h')
    result = estimate_rolling_mi(X, y, timestamps, window=200, step=100, k=5, random_state=42)
    assert 'timestamps' in result
    assert 'mi_bits' in result
    assert 'r2_ceiling' in result
    assert len(result['mi_bits']) == len(result['timestamps'])
    assert all(0 <= v <= 1 for v in result['r2_ceiling'])


def test_load_mi_data_returns_features_and_targets():
    data = load_mi_data('DATA/Nero_train_labeled.csv', ohlc_path='DATA/XAUUSD_H1_OHLC.csv')
    assert 'X' in data
    assert 'y_direction' in data
    assert 'y_amplitude' in data
    assert 'feature_names' in data
    assert 'time' in data
    assert data['X'].shape[1] == len(data['feature_names'])
    assert data['X'].shape[0] > 1000
    assert set(np.unique(data['y_direction'])).issubset({-1.0, 0.0, 1.0})
    assert np.isfinite(data['y_amplitude']).all()


def test_estimate_mi_per_feature_returns_dataframe():
    rng = np.random.RandomState(42)
    X = rng.randn(200, 3)
    y = X[:, 0] * 2.0 + rng.randn(200) * 0.1
    feature_names = ['feat_a', 'feat_b', 'feat_c']
    result = estimate_mi_per_feature(X, y, feature_names, k=5, random_state=42)
    assert len(result) == 3
    assert list(result.columns) == ['feature', 'mi_bits']
    assert result.iloc[0]['feature'] == 'feat_a'


def test_estimate_mi_returns_dict_with_required_keys():
    rng = np.random.RandomState(42)
    X = rng.randn(200, 3)
    y = X @ np.array([1.0, 0.5, 0.0]) + rng.randn(200) * 0.1
    result = estimate_mi(X, y, k=5, n_folds=5, n_permutations=20, random_state=42)
    assert 'mean_marginal_mi_bits' in result
    assert 'max_marginal_mi_bits' in result
    assert 'mi_ci_p05' in result
    assert 'mi_ci_p95' in result
    assert 'perm_p_value' in result
    assert 'r2_ceiling' in result
    assert 'n_samples' in result
    assert 'n_features' in result


def test_estimate_mi_r2_ceiling_formula():
    rng = np.random.RandomState(42)
    X = rng.randn(200, 2)
    y = X @ np.array([2.0, -1.0]) + rng.randn(200) * 0.01
    result = estimate_mi(X, y, k=5, n_folds=5, n_permutations=20, random_state=42)
    assert 0.0 <= result['r2_ceiling'] <= 1.0
    assert result['r2_ceiling'] == pytest.approx(1 - 2**(-2 * result['mean_marginal_mi_bits']), rel=1e-6)


def test_estimate_mi_independent_features_low_mi():
    rng = np.random.RandomState(42)
    X = rng.randn(500, 2)
    y = rng.randn(500)
    result = estimate_mi(X, y, k=5, n_folds=5, n_permutations=20, random_state=42)
    assert result['mean_marginal_mi_bits'] < 0.05
    assert result['perm_p_value'] > 0.05


def test_estimate_mi_r2_ceiling_not_below_true_r2():
    # Семантический тест (аудит п.1): для гауссовой пары R²-потолок обязан быть
    # не ниже истинной R². Если MI перепутать nats/bits, потолок 0.83 < 0.92 — тест падает.
    rng = np.random.RandomState(42)
    X = rng.randn(20000, 1)
    y = X[:, 0] + rng.randn(20000) * 0.3
    true_r2 = np.corrcoef(X[:, 0], y)[0, 1] ** 2
    result = estimate_mi(X, y, k=5, n_folds=5, n_permutations=10, random_state=42)
    assert result['r2_ceiling'] >= true_r2 - 0.05


def test_estimate_mi_zero_permutations_returns_none_p_value():
    # Аудит п.2: n_permutations=0 — p-value не вычисляется, не фейковое 1.0
    rng = np.random.RandomState(42)
    X = rng.randn(200, 2)
    y = X[:, 0] + rng.randn(200) * 0.5
    result = estimate_mi(X, y, k=5, n_folds=5, n_permutations=0, random_state=42)
    assert result['perm_p_value'] is None