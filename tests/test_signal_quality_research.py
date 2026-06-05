# =============================================================================
# Файл: tests/test_signal_quality_research.py
# Назначение: Unit и smoke-тесты для API/signal_quality_research.py (Variant 4).
#   Проверяет контракт filter features, variance check, univariate response maps,
#   shallow tree discovery, score/holdout validation и вспомогательных утилит.
# Язык: Python 3.10+
# Обновлён: 2026-04-05
# Зависимости:
#   Входные данные:
#     - синтетические OHLC и signal DataFrame fixtures внутри тестов
#   Выходные данные:
#     - pytest assertions для API/signal_quality_research.py
# Внешние зависимости:
#   - pytest>=8.0, numpy>=1.24, pandas>=2.0, scikit-learn
# Использование:
#   ./.venv/bin/python -m pytest tests/test_signal_quality_research.py -q
# Примечания:
#   - ratio_N = fav/adv с учётом направления сигнала (BUY/SELL)
#   - discovery/holdout split контролируется DISCOVERY_CUTOFF из sqr
# =============================================================================

import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, 'API')
import signal_quality_research as sqr


def _ohlc_frame(n=20):
    """Minimal OHLC with enough bars for ATR14 + excursions."""
    times = pd.date_range('2024-01-01', periods=n, freq='h')
    rng = np.random.RandomState(42)
    close = 2000.0 + rng.randn(n).cumsum() * 5
    high = close + rng.uniform(1, 5, n)
    low = close - rng.uniform(1, 5, n)
    opn = close + rng.randn(n) * 2
    return pd.DataFrame({
        'time': times, 'open': opn, 'high': high,
        'low': low, 'close': close,
    })


def _signal_row(ts, signal):
    return {
        'time': ts, 'signal': signal,
        'up_3': 0.30, 'dn_3': 0.05,
        'up_6': 0.40, 'dn_6': 0.20,
        'up_12': 0.50, 'dn_12': 0.25,
        'up_24': 0.60, 'dn_24': 0.35,
        'up_48': 0.70, 'dn_48': 0.45,
    }


def test_compute_filter_features_adds_ratio_spread_svl_columns():
    ohlc = _ohlc_frame(20)
    sig = pd.DataFrame([_signal_row(ohlc['time'].iloc[0], 1)])
    exc = sqr.compute_filter_features(sig, ohlc)

    for h in [3, 6, 12, 24, 48]:
        assert f'ratio_{h}' in exc.columns
        assert f'spread_{h}' in exc.columns

    assert 'ratio_3_vs_12' in exc.columns
    assert 'spread_3_vs_12' in exc.columns
    assert 'fav_3_vs_12' in exc.columns
    assert 'ratio_6_vs_24' in exc.columns
    assert 'spread_6_vs_24' in exc.columns
    assert 'ratio_12_vs_48' in exc.columns
    assert 'spread_12_vs_48' in exc.columns


def test_compute_filter_features_direction_aware():
    """BUY: pred_fav=up, pred_adv=dn. SELL: flipped."""
    ohlc = _ohlc_frame(20)
    buy = pd.DataFrame([_signal_row(ohlc['time'].iloc[0], 1)])
    sell = pd.DataFrame([_signal_row(ohlc['time'].iloc[0], -1)])

    exc_buy = sqr.compute_filter_features(buy, ohlc)
    exc_sell = sqr.compute_filter_features(sell, ohlc)

    # BUY: ratio_12 = up_12 / dn_12 = 0.50 / 0.25 = 2.0
    assert abs(exc_buy['ratio_12'].iloc[0] - 2.0) < 0.01
    # SELL: ratio_12 = dn_12 / up_12 = 0.25 / 0.50 = 0.5
    assert abs(exc_sell['ratio_12'].iloc[0] - 0.5) < 0.01


def test_response_variables_computed():
    ohlc = _ohlc_frame(20)
    sig = pd.DataFrame([_signal_row(ohlc['time'].iloc[0], 1)])
    exc = sqr.compute_filter_features(sig, ohlc)

    for k in [1, 3, 6]:
        assert f'fav_{k}_atr' in exc.columns
        assert f'adv_{k}_atr' in exc.columns
    assert 'net_12_atr' in exc.columns


def test_variance_check_kills_flat_feature():
    """Feature with >90% in one bin should be killed."""
    exc = pd.DataFrame({
        'ratio_3': [5.5] * 95 + [1.0] * 5,
        'ratio_12': np.linspace(1, 10, 100),
        'spread_3': [0.25] * 95 + [0.01] * 5,
        'spread_12': np.linspace(0, 2, 100),
    })
    alive, dead, report = sqr.variance_check(
        exc, ['ratio_3', 'ratio_12', 'spread_3', 'spread_12'])
    assert 'ratio_12' in alive
    assert 'spread_12' in alive
    assert 'ratio_3' in dead
    assert 'spread_3' in dead


def test_variance_check_reports_stats():
    exc = pd.DataFrame({'ratio_12': np.linspace(1, 10, 100)})
    alive, dead, report = sqr.variance_check(exc, ['ratio_12'])
    row = report[report['feature'] == 'ratio_12'].iloc[0]
    assert 'mean' in report.columns
    assert 'std' in report.columns
    assert 'Q10' in report.columns
    assert 'Q90' in report.columns
    assert row['alive']


def test_discovery_holdout_split():
    times = pd.date_range('2022-01-01', periods=2000, freq='D')
    exc = pd.DataFrame({'time': times, 'signal': 1, 'net_12': 1.0})
    disc, hold, info = sqr.discovery_holdout_split(exc)
    assert len(disc) + len(hold) == 2000
    assert disc['time'].max() <= pd.Timestamp(sqr.DISCOVERY_CUTOFF)
    assert hold['time'].min() > pd.Timestamp(sqr.DISCOVERY_CUTOFF)
    assert 'N_discovery' in info
    assert 'N_holdout' in info


def test_discovery_holdout_split_aborts_if_too_small():
    exc = pd.DataFrame({
        'time': pd.date_range('2024-06-01', periods=50, freq='D'),
        'signal': 1, 'net_12': 1.0,
    })
    with pytest.raises(ValueError, match='too few'):
        sqr.discovery_holdout_split(exc)


# ── Step 2: Univariate Response Maps ────────────────────────────────────────

def test_univariate_response_map_returns_bins_with_pf():
    n = 200
    rng = np.random.RandomState(42)
    exc = pd.DataFrame({
        'ratio_12': np.linspace(1, 10, n),
        'net_12': rng.randn(n) * 10,
        'entry_atr14': [20.0] * n,
        'fav_6': rng.uniform(0, 15, n),
        'adv_6': rng.uniform(0, 15, n),
        'time': pd.date_range('2023-01-01', periods=n, freq='D'),
    })
    result = sqr.univariate_response_map(exc, 'ratio_12', n_bins=5)
    assert len(result) == 5
    assert 'bin' in result.columns
    assert 'PF' in result.columns
    assert 'N' in result.columns
    assert 'net_ATR' in result.columns
    assert 'uplift' in result.columns


# ── Step 3: Shallow Tree Discovery ──────────────────────────────────────────

def test_shallow_tree_returns_splits_and_importances():
    n = 300
    rng = np.random.RandomState(42)
    features = ['ratio_12', 'spread_12', 'ratio_3_vs_12']
    exc = pd.DataFrame({
        'ratio_12': rng.uniform(1, 10, n),
        'spread_12': rng.uniform(-1, 3, n),
        'ratio_3_vs_12': rng.uniform(0.5, 2, n),
        'net_12': np.zeros(n),
        'entry_atr14': [20.0] * n,
    })
    exc.loc[exc['ratio_12'] > 5, 'net_12'] = 10.0
    exc.loc[exc['ratio_12'] <= 5, 'net_12'] = -5.0

    result = sqr.shallow_tree_discovery(exc, features)
    assert 'tree_text' in result
    assert 'importances' in result
    assert 'leaves' in result
    assert len(result['importances']) == len(features)
    imp = result['importances']
    assert imp.loc['ratio_12'] > imp.loc['spread_12']


def test_shallow_tree_leaf_stats_include_pf():
    n = 200
    rng = np.random.RandomState(42)
    exc = pd.DataFrame({
        'ratio_12': rng.uniform(1, 10, n),
        'net_12': rng.randn(n) * 10,
        'entry_atr14': [20.0] * n,
    })
    result = sqr.shallow_tree_discovery(exc, ['ratio_12'])
    leaves = result['leaves']
    assert 'N' in leaves.columns
    assert 'PF' in leaves.columns
    assert 'net_ATR_mean' in leaves.columns


# ── Step 4: Pairwise Combinations ───────────────────────────────────────────

def test_pairwise_combinations_returns_metrics():
    n = 300
    rng = np.random.RandomState(42)
    exc = pd.DataFrame({
        'ratio_12': rng.uniform(1, 10, n),
        'spread_12': rng.uniform(-1, 3, n),
        'net_12': rng.randn(n) * 10,
        'entry_atr14': [20.0] * n,
        'fav_6': rng.uniform(0, 15, n),
        'adv_6': rng.uniform(0, 15, n),
    })
    candidates = [
        ('ratio_12', '>', 5.0),
        ('spread_12', '>', 1.0),
    ]
    result = sqr.pairwise_combinations(exc, candidates, max_pairs=5)
    assert len(result) > 0
    assert 'rule' in result.columns
    assert 'PF' in result.columns
    assert 'N' in result.columns


def test_negative_control_check():
    n = 300
    rng = np.random.RandomState(42)
    exc = pd.DataFrame({
        'ratio_12': rng.uniform(1, 10, n),
        'net_12': rng.randn(n) * 10,
        'entry_atr14': [20.0] * n,
        'atr_bucket': (['Q4'] * 150 + ['Q3'] * 50
                       + ['Q2'] * 50 + ['Q1'] * 50),
    })
    exc['ratio_bin'] = pd.cut(exc['ratio_12'],
                              bins=[0, 2, 3, 4, 5, np.inf],
                              labels=['<2', '2-3', '3-4', '4-5', '5+'],
                              right=False)
    mask = exc['ratio_12'] > 5.0
    ctrl = sqr.negative_control_check(exc, mask)
    assert 'ratio_3_4_PF' in ctrl
    assert 'non_Q4_PF' in ctrl


# ── Step 5: Score & Holdout ─────────────────────────────────────────────────

def test_build_score_uses_rank_normalization():
    n = 100
    rng = np.random.RandomState(42)
    exc = pd.DataFrame({
        'ratio_12': rng.uniform(1, 10, n),
        'spread_12': rng.uniform(-1, 3, n),
    })
    scored = sqr.build_score(exc, ['ratio_12', 'spread_12'])
    assert 'score' in scored.columns
    assert scored['score'].min() >= -1e-9
    assert scored['score'].max() <= 1.0 + 1e-6


def test_holdout_validation_returns_confirmation():
    n = 200
    rng = np.random.RandomState(42)
    hold = pd.DataFrame({
        'net_12': rng.randn(n) * 10 + 2,
        'entry_atr14': [20.0] * n,
        'score': rng.uniform(0, 1, n),
        'ratio_bin': pd.Categorical(['4-5'] * 100 + ['3-4'] * 100,
                                    categories=['<2', '2-3', '3-4', '4-5', '5+']),
        'atr_bucket': ['Q4'] * 100 + ['Q3'] * 100,
    })
    result = sqr.holdout_validation(hold, top_pct=0.25)
    assert 'PF_holdout' in result
    assert 'N_holdout' in result
    assert 'confirmed' in result


# ── Report smoke test ───────────────────────────────────────────────────────

def test_print_variance_report_smoke(capsys):
    n = 100
    rng = np.random.RandomState(42)
    exc = pd.DataFrame({f: rng.uniform(1, 10, n) for f in sqr.ALL_FILTER_FEATURES})
    sqr.print_variance_report(exc, sqr.ALL_FILTER_FEATURES)
    captured = capsys.readouterr()
    assert 'Variance Check' in captured.out


def test_trivial_rule_filter():
    n = 200
    exc = pd.DataFrame({'ratio_12': np.linspace(1, 10, n)})
    # threshold at 0.5 catches 100% of data -> trivial
    assert sqr._is_trivial_rule(exc, 'ratio_12', '>', 0.5)
    # threshold at 8.0 catches ~20% -> not trivial
    assert not sqr._is_trivial_rule(exc, 'ratio_12', '>', 8.0)


def test_year_stability_returns_per_year():
    n = 400
    rng = np.random.RandomState(42)
    times = pd.date_range('2022-07-01', periods=n, freq='D')
    exc = pd.DataFrame({
        'time': times,
        'net_12': rng.randn(n) * 10,
        'entry_atr14': [20.0] * n,
        'ratio_12': rng.uniform(1, 10, n),
    })
    mask = exc['ratio_12'] > 5.0
    ys = sqr.year_stability(exc, mask, 'ratio_12 > 5.0')
    assert 'year' in ys.columns
    assert 'PF' in ys.columns
    assert len(ys) >= 2  # should span at least 2022 and 2023


def test_cross_filter_x_pullback_runs():
    ohlc = _ohlc_frame(20)
    sig = pd.DataFrame([_signal_row(ohlc['time'].iloc[0], 1)])
    exc = sqr.compute_filter_features(sig, ohlc)
    result = sqr.cross_filter_x_pullback(exc, ohlc, 'test')
    assert 'filter' in result.columns
    assert 'scenario' in result.columns


def test_apply_filter_rules():
    n = 100
    rng = np.random.RandomState(42)
    df = pd.DataFrame({
        'ratio_12': rng.uniform(1, 10, n),
        'fav_3_vs_12': rng.uniform(0.5, 0.9, n),
    })
    rules = [('ratio_12', '>', 5.0), ('fav_3_vs_12', '<=', 0.7)]
    mask = sqr._apply_filter_rules(df, rules)
    assert mask.sum() < n
    # None = no filter
    mask_all = sqr._apply_filter_rules(df, None)
    assert mask_all.sum() == n
