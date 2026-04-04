# Signal Quality Filter Research (Variant 4) Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `API/signal_quality_research.py` — a research tool that explores multi-horizon prediction features as signal quality filters, with discovery/holdout validation.

**Architecture:** New standalone script that imports data loading functions from `signal_research.py`, computes 3 filter feature families (ratio_h, spread_h, short_vs_long) + response variables (path_atr), then runs a 6-step research pipeline: variance check → split → univariate maps → shallow tree → pairwise combinations → score + holdout. All output goes to stdout as formatted tables (same pattern as `signal_research.py`).

**Tech Stack:** Python 3.11+, pandas, numpy, scikit-learn (DecisionTreeClassifier)

**Spec:** [docs/superpowers/specs/2026-04-03-signal-quality-filter-claude.md](../specs/2026-04-03-signal-quality-filter-claude.md)

---

### Task 1: Script skeleton + data loading + feature engineering

**Files:**
- Create: `API/signal_quality_research.py`
- Create: `tests/test_signal_quality_research.py`

This task creates the script with header, imports from `signal_research.py`, and all feature computation. No report sections yet — just data pipeline and feature columns.

- [ ] **Step 1: Write failing test for feature engineering**

```python
# tests/test_signal_quality_research.py
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

    # ratio_h for all 5 horizons
    for h in [3, 6, 12, 24, 48]:
        assert f'ratio_{h}' in exc.columns
        assert f'spread_{h}' in exc.columns

    # short_vs_long
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_signal_quality_research.py -q`
Expected: FAIL (module not found)

- [ ] **Step 3: Write script skeleton + compute_filter_features()**

```python
# API/signal_quality_research.py
# =============================================================================
# Файл: API/signal_quality_research.py
# Назначение: Signal Quality Filter Research (Variant 4):
#              исследование multi-horizon prediction features как фильтров
#              качества ML-сигналов
# Язык: Python 3.11+
# Создан: 2026-04-03
# Зависимости:
#   Входные данные:
#     - MT/MQL4/Files/ml_signals.csv
#     - DATA/XAUUSD_H1_OHLC.csv
#   Выходные данные:
#     - stdout (таблицы)
# Использование:
#   python -m API.signal_quality_research
#   python -m API.signal_quality_research --test-only
# =============================================================================

"""
Signal Quality Filter Research (Variant 4).

Исследует, могут ли комбинации multi-horizon predictions модели (up_3..dn_48)
дать более точный фильтр качества сигнала, чем текущий ratio_12.

Pipeline:
  Step 0: Feature Variance Check — убиваем features с near-zero дисперсией
  Step 1: Discovery / Holdout Split — 60/40 по дате
  Step 2: Univariate Response Maps — quantile bins → PF, N, net_ATR
  Step 3: Shallow Tree Discovery — depth-2 tree для поиска лучших splits
  Step 4: Pairwise Combinations — top splits × top univariate winners
  Step 5: Score Construction & Holdout Validation

Filter Feature Families:
  1. ratio_h = pred_fav_h / pred_adv_h          (h ∈ {3,6,12,24,48})
  2. spread_h = pred_fav_h - pred_adv_h          (h ∈ {3,6,12,24,48})
  3. short_vs_long: ratio/spread divergence       (3v12, 6v24, 12v48)

Response Variables (post-signal, not filters):
  fav_k_atr, adv_k_atr (k ∈ {1,3,6}), net_12_atr
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

import signal_research as sr

PROJECT_ROOT = Path(__file__).resolve().parent.parent

HORIZONS = [3, 6, 12, 24, 48]
PRED_COLS = sr.PRED_COLS
PULLBACK_WINDOWS = [1, 3, 6]
BASE_HORIZON = 12
DISCOVERY_CUTOFF = '2024-12-31'
MIN_DISCOVERY_N = 1000
MIN_HOLDOUT_N = 400
MIN_N_FINAL = 56

FILTER_FEATURES = []  # populated by compute_filter_features

RATIO_FEATURES = [f'ratio_{h}' for h in HORIZONS]
SPREAD_FEATURES = [f'spread_{h}' for h in HORIZONS]
SVL_FEATURES = [
    'ratio_3_vs_12', 'spread_3_vs_12', 'fav_3_vs_12',
    'ratio_6_vs_24', 'spread_6_vs_24',
    'ratio_12_vs_48', 'spread_12_vs_48',
]
ALL_FILTER_FEATURES = RATIO_FEATURES + SPREAD_FEATURES + SVL_FEATURES


def compute_filter_features(sig_df: pd.DataFrame,
                            ohlc: pd.DataFrame) -> pd.DataFrame:
    """Compute excursions via signal_research, then add filter features
    and response variables."""
    exc = sr.compute_excursions(sig_df, ohlc)

    # pred_fav/pred_adv for ALL 5 horizons (signal_research only does 3,6,12)
    for h in HORIZONS:
        fav_col = f'pred_fav_{h}'
        adv_col = f'pred_adv_{h}'
        if fav_col not in exc.columns:
            exc[fav_col] = np.where(
                exc['signal'] == 1, exc[f'up_{h}'], exc[f'dn_{h}'])
            exc[adv_col] = np.where(
                exc['signal'] == 1, exc[f'dn_{h}'], exc[f'up_{h}'])

    eps = 1e-6
    # Family 1: ratio_h
    for h in HORIZONS:
        exc[f'ratio_{h}'] = exc[f'pred_fav_{h}'] / (exc[f'pred_adv_{h}'] + eps)

    # Family 2: spread_h
    for h in HORIZONS:
        exc[f'spread_{h}'] = exc[f'pred_fav_{h}'] - exc[f'pred_adv_{h}']

    # Family 3: short_vs_long
    exc['ratio_3_vs_12'] = exc['ratio_3'] / (exc['ratio_12'] + eps)
    exc['spread_3_vs_12'] = exc['spread_3'] / (exc['spread_12'] + eps)
    exc['fav_3_vs_12'] = exc['pred_fav_3'] / (exc['pred_fav_12'] + eps)
    exc['ratio_6_vs_24'] = exc['ratio_6'] / (exc['ratio_24'] + eps)
    exc['spread_6_vs_24'] = exc['spread_6'] / (exc['spread_24'] + eps)
    exc['ratio_12_vs_48'] = exc['ratio_12'] / (exc['ratio_48'] + eps)
    exc['spread_12_vs_48'] = exc['spread_12'] / (exc['spread_48'] + eps)

    # Response variables (not filters)
    atr = exc['entry_atr14']
    for k in PULLBACK_WINDOWS:
        exc[f'fav_{k}_atr'] = exc[f'fav_{k}'] / (atr + eps)
        exc[f'adv_{k}_atr'] = exc[f'adv_{k}'] / (atr + eps)
    exc['net_12_atr'] = exc[f'net_{BASE_HORIZON}'] / (atr + eps)

    return exc
```

- [ ] **Step 4: Run test to verify it passes**

Run: `./.venv/bin/python -m pytest tests/test_signal_quality_research.py -q`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add API/signal_quality_research.py tests/test_signal_quality_research.py
git commit -m "feat: signal_quality_research skeleton with filter feature engineering"
```

---

### Task 2: Step 0 — Feature Variance Check

**Files:**
- Modify: `API/signal_quality_research.py`
- Modify: `tests/test_signal_quality_research.py`

- [ ] **Step 1: Write failing test for variance check**

```python
def test_variance_check_kills_flat_feature():
    """Feature with >90% in one bin should be killed."""
    exc = pd.DataFrame({
        'ratio_3': [5.5] * 95 + [1.0] * 5,  # 95% same value
        'ratio_12': np.linspace(1, 10, 100),  # good variance
        'spread_3': [0.25] * 95 + [0.01] * 5,
        'spread_12': np.linspace(0, 2, 100),
    })
    alive, dead, report = sqr.variance_check(
        exc, ['ratio_3', 'ratio_12', 'spread_3', 'spread_12'])
    assert 'ratio_12' in alive
    assert 'spread_12' in alive
    assert 'ratio_3' in dead  # killed: >90% in one bin
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_signal_quality_research.py::test_variance_check_kills_flat_feature -v`
Expected: FAIL

- [ ] **Step 3: Implement variance_check()**

```python
def variance_check(exc: pd.DataFrame,
                   features: list[str],
                   n_bins: int = 10) -> tuple[list, list, pd.DataFrame]:
    """Step 0: check feature variance, kill near-constant features.

    Returns (alive_features, dead_features, report_df).
    """
    rows = []
    alive, dead = [], []
    for f in features:
        s = exc[f].dropna()
        if len(s) < 20:
            dead.append(f)
            rows.append({'feature': f, 'mean': np.nan, 'std': np.nan,
                         'Q10': np.nan, 'Q50': np.nan, 'Q90': np.nan,
                         'max_bin_pct': 100.0, 'alive': False,
                         'kill_reason': 'too few values'})
            continue

        mean, std = s.mean(), s.std()
        q10, q50, q90 = s.quantile([0.1, 0.5, 0.9])
        iqr = s.quantile(0.75) - s.quantile(0.25)

        # max % in one quantile bin
        try:
            binned = pd.qcut(s, n_bins, duplicates='drop')
            max_bin_pct = binned.value_counts(normalize=True).max() * 100
        except ValueError:
            max_bin_pct = 100.0

        # Kill criteria
        is_ratio = f.startswith('ratio') or f.startswith('fav_')
        if max_bin_pct > 90.0:
            dead.append(f)
            reason = '>90% in one bin'
        elif is_ratio and abs(mean) > eps and std < 0.01 * abs(mean):
            dead.append(f)
            reason = 'std < 1% of |mean|'
        elif not is_ratio and iqr > 0 and std < 0.01 * iqr:
            dead.append(f)
            reason = 'std < 1% of IQR'
        else:
            alive.append(f)
            reason = ''

        rows.append({'feature': f, 'mean': mean, 'std': std,
                     'Q10': q10, 'Q50': q50, 'Q90': q90,
                     'max_bin_pct': max_bin_pct, 'alive': reason == '',
                     'kill_reason': reason})

    return alive, dead, pd.DataFrame(rows)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `./.venv/bin/python -m pytest tests/test_signal_quality_research.py -q`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add API/signal_quality_research.py tests/test_signal_quality_research.py
git commit -m "feat: Step 0 feature variance check with kill criteria"
```

---

### Task 3: Step 1 — Discovery / Holdout Split

**Files:**
- Modify: `API/signal_quality_research.py`
- Modify: `tests/test_signal_quality_research.py`

- [ ] **Step 1: Write failing test**

```python
def test_discovery_holdout_split():
    times = pd.date_range('2023-01-01', periods=100, freq='7D')
    exc = pd.DataFrame({'time': times, 'signal': 1, 'net_12': 1.0})
    disc, hold, info = sqr.discovery_holdout_split(exc)
    assert len(disc) + len(hold) == 100
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_signal_quality_research.py::test_discovery_holdout_split -v`
Expected: FAIL

- [ ] **Step 3: Implement discovery_holdout_split()**

```python
def discovery_holdout_split(exc: pd.DataFrame
                            ) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Step 1: split by DISCOVERY_CUTOFF date.

    Raises ValueError if either split is too small.
    """
    cutoff = pd.Timestamp(DISCOVERY_CUTOFF)
    disc = exc[exc['time'] <= cutoff].copy()
    hold = exc[exc['time'] > cutoff].copy()

    if len(disc) < MIN_DISCOVERY_N or len(hold) < MIN_HOLDOUT_N:
        raise ValueError(
            f'Split too few: discovery={len(disc)}, holdout={len(hold)}. '
            f'Need discovery>={MIN_DISCOVERY_N}, holdout>={MIN_HOLDOUT_N}')

    buy_d = (disc['signal'] == 1).sum()
    buy_h = (hold['signal'] == 1).sum()
    info = {
        'N_discovery': len(disc),
        'N_holdout': len(hold),
        'discovery_range': f"{disc['time'].min()} — {disc['time'].max()}",
        'holdout_range': f"{hold['time'].min()} — {hold['time'].max()}",
        'discovery_BUY_pct': round(buy_d / len(disc) * 100, 1),
        'holdout_BUY_pct': round(buy_h / len(hold) * 100, 1),
    }
    return disc, hold, info
```

- [ ] **Step 4: Run test to verify it passes**

Run: `./.venv/bin/python -m pytest tests/test_signal_quality_research.py -q`
Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add API/signal_quality_research.py tests/test_signal_quality_research.py
git commit -m "feat: Step 1 discovery/holdout split with N guards"
```

---

### Task 4: Step 2 — Univariate Response Maps

**Files:**
- Modify: `API/signal_quality_research.py`
- Modify: `tests/test_signal_quality_research.py`

- [ ] **Step 1: Write failing test**

```python
def test_univariate_response_map_returns_bins_with_pf():
    n = 200
    rng = np.random.RandomState(42)
    exc = pd.DataFrame({
        'ratio_12': np.linspace(1, 10, n),
        'net_12': rng.randn(n) * 10,
        'entry_atr14': [20.0] * n,
        'fav_1': rng.uniform(0, 5, n),
        'adv_1': rng.uniform(0, 5, n),
        'fav_3': rng.uniform(0, 10, n),
        'adv_3': rng.uniform(0, 10, n),
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_signal_quality_research.py::test_univariate_response_map_returns_bins_with_pf -v`
Expected: FAIL

- [ ] **Step 3: Implement univariate_response_map()**

```python
def _profit_factor(net: pd.Series) -> float:
    """PF = gross_profit / gross_loss."""
    wins = net[net > 0].sum()
    losses = net[net < 0].abs().sum()
    if losses == 0:
        return np.inf if wins > 0 else np.nan
    if wins == 0:
        return 0.0
    return wins / losses


def univariate_response_map(disc: pd.DataFrame,
                            feature: str,
                            n_bins: int = 5) -> pd.DataFrame:
    """Step 2: quantile-bin a feature, compute PF and response metrics per bin."""
    s = disc[feature].dropna()
    valid = disc.loc[s.index].copy()
    valid['_bin'] = pd.qcut(s, n_bins, duplicates='drop')

    baseline_pf = _profit_factor(valid['net_12'])
    atr = valid['entry_atr14']
    years = ((valid['time'].max() - valid['time'].min()).days + 1) / 365.25

    rows = []
    for label, grp in valid.groupby('_bin', observed=True):
        net = grp['net_12']
        pf = _profit_factor(net)
        rows.append({
            'bin': str(label),
            'N': len(grp),
            'trades_per_year': round(len(grp) / max(years, 0.1), 1),
            'PF': round(pf, 2) if np.isfinite(pf) else pf,
            'net_ATR': round((net / (grp['entry_atr14'] + 1e-6)).mean(), 3),
            'fav_ATR': round((grp['fav_6'] / (grp['entry_atr14'] + 1e-6)).mean(), 3),
            'adv_ATR': round((grp['adv_6'] / (grp['entry_atr14'] + 1e-6)).mean(), 3),
            'uplift': round(pf - baseline_pf, 2) if np.isfinite(pf) and np.isfinite(baseline_pf) else np.nan,
        })
    return pd.DataFrame(rows).sort_values('PF', ascending=False).reset_index(drop=True)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `./.venv/bin/python -m pytest tests/test_signal_quality_research.py -q`
Expected: 8 passed

- [ ] **Step 5: Commit**

```bash
git add API/signal_quality_research.py tests/test_signal_quality_research.py
git commit -m "feat: Step 2 univariate response maps with PF and response metrics"
```

---

### Task 5: Step 3 — Shallow Tree Discovery

**Files:**
- Modify: `API/signal_quality_research.py`
- Modify: `tests/test_signal_quality_research.py`

- [ ] **Step 1: Write failing test**

```python
def test_shallow_tree_returns_splits_and_importances():
    n = 300
    rng = np.random.RandomState(42)
    features = ['ratio_12', 'spread_12', 'ratio_3_vs_12']
    exc = pd.DataFrame({
        'ratio_12': rng.uniform(1, 10, n),
        'spread_12': rng.uniform(-1, 3, n),
        'ratio_3_vs_12': rng.uniform(0.5, 2, n),
        'net_12': np.zeros(n),
    })
    # Make ratio_12 > 5 → positive net (clear signal)
    exc.loc[exc['ratio_12'] > 5, 'net_12'] = 10.0
    exc.loc[exc['ratio_12'] <= 5, 'net_12'] = -5.0

    result = sqr.shallow_tree_discovery(exc, features)
    assert 'tree_text' in result
    assert 'importances' in result
    assert 'leaves' in result
    assert len(result['importances']) == len(features)
    # ratio_12 should dominate
    imp = result['importances']
    assert imp.loc['ratio_12'] > imp.loc['spread_12']


def test_shallow_tree_leaf_stats_include_pf():
    n = 200
    rng = np.random.RandomState(42)
    exc = pd.DataFrame({
        'ratio_12': rng.uniform(1, 10, n),
        'net_12': rng.randn(n) * 10,
    })
    result = sqr.shallow_tree_discovery(exc, ['ratio_12'])
    leaves = result['leaves']
    assert 'N' in leaves.columns
    assert 'PF' in leaves.columns
    assert 'net_ATR_mean' in leaves.columns
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_signal_quality_research.py::test_shallow_tree_returns_splits_and_importances -v`
Expected: FAIL

- [ ] **Step 3: Implement shallow_tree_discovery()**

```python
from sklearn.tree import DecisionTreeClassifier, export_text


def shallow_tree_discovery(disc: pd.DataFrame,
                           features: list[str],
                           max_depth: int = 2) -> dict:
    """Step 3: fit depth-2 tree, extract splits and leaf stats."""
    valid = disc.dropna(subset=features + ['net_12']).copy()
    X = valid[features].values
    y = (valid['net_12'] > 0).astype(int).values

    tree = DecisionTreeClassifier(max_depth=max_depth, random_state=42)
    tree.fit(X, y)

    tree_text = export_text(tree, feature_names=features, decimals=3)

    importances = pd.Series(tree.feature_importances_,
                            index=features, name='importance')

    # Leaf statistics
    leaf_ids = tree.apply(X)
    valid['_leaf'] = leaf_ids
    leaf_rows = []
    for lid, grp in valid.groupby('_leaf'):
        net = grp['net_12']
        pf = _profit_factor(net)
        leaf_rows.append({
            'leaf': lid,
            'N': len(grp),
            'win_rate': round((net > 0).mean() * 100, 1),
            'PF': round(pf, 2) if np.isfinite(pf) else pf,
            'net_ATR_mean': round(
                (net / (grp['entry_atr14'] + 1e-6)).mean(), 3)
                if 'entry_atr14' in grp.columns else round(net.mean(), 3),
        })

    return {
        'tree_text': tree_text,
        'importances': importances.sort_values(ascending=False),
        'leaves': pd.DataFrame(leaf_rows),
        'tree': tree,
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `./.venv/bin/python -m pytest tests/test_signal_quality_research.py -q`
Expected: 10 passed

- [ ] **Step 5: Commit**

```bash
git add API/signal_quality_research.py tests/test_signal_quality_research.py
git commit -m "feat: Step 3 shallow tree discovery with leaf PF stats"
```

---

### Task 6: Step 4 — Pairwise Combinations + Negative Controls

**Files:**
- Modify: `API/signal_quality_research.py`
- Modify: `tests/test_signal_quality_research.py`

- [ ] **Step 1: Write failing test**

```python
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
        'atr_bucket': ['Q4'] * 150 + ['Q3'] * 50 + ['Q2'] * 50 + ['Q1'] * 50,
    })
    # Compute ratio_bin for negative control cohort identification
    exc['ratio_bin'] = pd.cut(exc['ratio_12'],
                              bins=[0, 2, 3, 4, 5, np.inf],
                              labels=['<2', '2-3', '3-4', '4-5', '5+'])
    mask = exc['ratio_12'] > 5.0
    ctrl = sqr.negative_control_check(exc, mask)
    assert 'ratio_3_4_PF' in ctrl
    assert 'non_Q4_PF' in ctrl
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_signal_quality_research.py::test_pairwise_combinations_returns_metrics -v`
Expected: FAIL

- [ ] **Step 3: Implement pairwise_combinations() and negative_control_check()**

```python
def _apply_rule(exc, feature, op, threshold):
    if op == '>':
        return exc[feature] > threshold
    elif op == '<':
        return exc[feature] < threshold
    elif op == '>=':
        return exc[feature] >= threshold
    elif op == '<=':
        return exc[feature] <= threshold
    return pd.Series(False, index=exc.index)


def negative_control_check(exc: pd.DataFrame,
                           filter_mask: pd.Series) -> dict:
    """Apply filter_mask to negative control cohorts, return their PF."""
    result = {}
    # ratio 3-4
    r34_mask = exc['ratio_bin'] == '3-4'
    r34_filtered = exc[r34_mask & filter_mask]
    result['ratio_3_4_PF'] = _profit_factor(r34_filtered['net_12']) if len(r34_filtered) > 0 else np.nan
    result['ratio_3_4_N'] = len(r34_filtered)

    # non-Q4
    nq4_mask = exc['atr_bucket'] != 'Q4'
    nq4_filtered = exc[nq4_mask & filter_mask]
    result['non_Q4_PF'] = _profit_factor(nq4_filtered['net_12']) if len(nq4_filtered) > 0 else np.nan
    result['non_Q4_N'] = len(nq4_filtered)

    return result


def pairwise_combinations(disc: pd.DataFrame,
                          candidates: list[tuple],
                          max_pairs: int = 20) -> pd.DataFrame:
    """Step 4: test pairwise AND-combinations of candidate rules.

    candidates: list of (feature, op, threshold) tuples.
    """
    from itertools import combinations

    baseline_pf = _profit_factor(disc['net_12'])
    pairs = list(combinations(range(len(candidates)), 2))
    if len(pairs) > max_pairs:
        pairs = pairs[:max_pairs]

    rows = []
    # Also test each single rule
    for i, (f, op, thr) in enumerate(candidates):
        mask = _apply_rule(disc, f, op, thr)
        subset = disc[mask]
        if len(subset) < 10:
            continue
        pf = _profit_factor(subset['net_12'])
        ctrl = negative_control_check(disc, mask) if 'ratio_bin' in disc.columns else {}
        rows.append({
            'rule': f'{f} {op} {thr:.2f}',
            'N': len(subset),
            'PF': round(pf, 2) if np.isfinite(pf) else pf,
            'net_ATR': round((subset['net_12'] / (subset['entry_atr14'] + 1e-6)).mean(), 3),
            'uplift': round(pf - baseline_pf, 2) if np.isfinite(pf) and np.isfinite(baseline_pf) else np.nan,
            **ctrl,
        })

    for i, j in pairs:
        f1, op1, thr1 = candidates[i]
        f2, op2, thr2 = candidates[j]
        mask = _apply_rule(disc, f1, op1, thr1) & _apply_rule(disc, f2, op2, thr2)
        subset = disc[mask]
        if len(subset) < 10:
            continue
        pf = _profit_factor(subset['net_12'])
        ctrl = negative_control_check(disc, mask) if 'ratio_bin' in disc.columns else {}
        rows.append({
            'rule': f'{f1} {op1} {thr1:.2f} AND {f2} {op2} {thr2:.2f}',
            'N': len(subset),
            'PF': round(pf, 2) if np.isfinite(pf) else pf,
            'net_ATR': round((subset['net_12'] / (subset['entry_atr14'] + 1e-6)).mean(), 3),
            'uplift': round(pf - baseline_pf, 2) if np.isfinite(pf) and np.isfinite(baseline_pf) else np.nan,
            **ctrl,
        })

    return pd.DataFrame(rows).sort_values('PF', ascending=False).reset_index(drop=True)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `./.venv/bin/python -m pytest tests/test_signal_quality_research.py -q`
Expected: 12 passed

- [ ] **Step 5: Commit**

```bash
git add API/signal_quality_research.py tests/test_signal_quality_research.py
git commit -m "feat: Step 4 pairwise combinations with negative control check"
```

---

### Task 7: Step 5 — Score Construction & Holdout Validation

**Files:**
- Modify: `API/signal_quality_research.py`
- Modify: `tests/test_signal_quality_research.py`

- [ ] **Step 1: Write failing test**

```python
def test_build_score_uses_rank_normalization():
    n = 100
    rng = np.random.RandomState(42)
    exc = pd.DataFrame({
        'ratio_12': rng.uniform(1, 10, n),
        'spread_12': rng.uniform(-1, 3, n),
    })
    scored = sqr.build_score(exc, ['ratio_12', 'spread_12'])
    assert 'score' in scored.columns
    # rank-based: score should be in [0, 1] range approximately
    assert scored['score'].min() >= 0
    assert scored['score'].max() <= 1.0 + 1e-6


def test_holdout_validation_returns_confirmation():
    n = 200
    rng = np.random.RandomState(42)
    hold = pd.DataFrame({
        'net_12': rng.randn(n) * 10 + 2,  # slightly positive
        'entry_atr14': [20.0] * n,
        'score': rng.uniform(0, 1, n),
        'ratio_bin': ['4-5'] * 100 + ['3-4'] * 100,
        'atr_bucket': ['Q4'] * 100 + ['Q3'] * 100,
    })
    result = sqr.holdout_validation(hold, top_pct=0.25)
    assert 'PF_holdout' in result
    assert 'N_holdout' in result
    assert 'confirmed' in result
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_signal_quality_research.py::test_build_score_uses_rank_normalization -v`
Expected: FAIL

- [ ] **Step 3: Implement build_score() and holdout_validation()**

```python
def build_score(df: pd.DataFrame,
                features: list[str],
                weights: dict | None = None) -> pd.DataFrame:
    """Rank-based normalization + additive score.

    weights: {feature: weight}. Default = equal weights.
    """
    result = df.copy()
    if weights is None:
        weights = {f: 1.0 / len(features) for f in features}

    score = pd.Series(0.0, index=df.index)
    for f in features:
        ranked = df[f].rank(pct=True)
        score += weights[f] * ranked

    # Normalize to [0, 1]
    smin, smax = score.min(), score.max()
    if smax > smin:
        score = (score - smin) / (smax - smin)
    result['score'] = score
    return result


def holdout_validation(hold: pd.DataFrame,
                       top_pct: float = 0.25) -> dict:
    """Step 5: one-shot holdout test on top-scoring signals."""
    threshold = hold['score'].quantile(1.0 - top_pct)
    top = hold[hold['score'] >= threshold]
    baseline_pf = _profit_factor(hold['net_12'])
    top_pf = _profit_factor(top['net_12'])
    confirmed = (np.isfinite(top_pf) and np.isfinite(baseline_pf)
                 and top_pf > baseline_pf)

    ctrl = negative_control_check(hold, hold['score'] >= threshold) \
        if 'ratio_bin' in hold.columns else {}

    return {
        'top_pct': top_pct,
        'N_holdout': len(top),
        'PF_holdout': round(top_pf, 2) if np.isfinite(top_pf) else top_pf,
        'PF_baseline': round(baseline_pf, 2) if np.isfinite(baseline_pf) else baseline_pf,
        'confirmed': confirmed,
        **ctrl,
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `./.venv/bin/python -m pytest tests/test_signal_quality_research.py -q`
Expected: 14 passed

- [ ] **Step 5: Commit**

```bash
git add API/signal_quality_research.py tests/test_signal_quality_research.py
git commit -m "feat: Step 5 score construction with rank normalization and holdout validation"
```

---

### Task 8: CLI + Report Output + main()

**Files:**
- Modify: `API/signal_quality_research.py`
- Modify: `tests/test_signal_quality_research.py`

This task wires everything together: CLI argument parsing, print functions for each step, and the `main()` orchestrator.

- [ ] **Step 1: Write failing test for report smoke**

```python
def test_report_smoke(capsys):
    """Full pipeline on synthetic data — verifies no crashes and key sections appear."""
    n = 100
    rng = np.random.RandomState(42)
    # Minimal exc-like frame with all required columns
    times = pd.date_range('2023-01-01', periods=n, freq='7D')
    exc = pd.DataFrame({
        'time': times,
        'signal': rng.choice([1, -1], n),
        'net_12': rng.randn(n) * 10,
        'entry_atr14': [20.0] * n,
        'fav_1': rng.uniform(0, 5, n),
        'adv_1': rng.uniform(0, 5, n),
        'fav_3': rng.uniform(0, 10, n),
        'adv_3': rng.uniform(0, 10, n),
        'fav_6': rng.uniform(0, 15, n),
        'adv_6': rng.uniform(0, 15, n),
    })
    for h in sqr.HORIZONS:
        exc[f'ratio_{h}'] = rng.uniform(1, 10, n)
        exc[f'spread_{h}'] = rng.uniform(-1, 3, n)
    for f in sqr.SVL_FEATURES:
        exc[f] = rng.uniform(0.5, 2, n)

    sqr.print_variance_report(exc, sqr.ALL_FILTER_FEATURES)
    captured = capsys.readouterr()
    assert 'Variance Check' in captured.out
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_signal_quality_research.py::test_report_smoke -v`
Expected: FAIL

- [ ] **Step 3: Implement print functions and main()**

Implement these print/report functions:
- `print_separator(title)` — reuse pattern from signal_research
- `print_variance_report(exc, features)` — Step 0 table
- `print_split_info(info)` — Step 1 summary
- `print_univariate_maps(disc, alive_features)` — Step 2 tables
- `print_tree_discovery(result)` — Step 3 tree + importances
- `print_pairwise_results(results)` — Step 4 table
- `print_holdout_results(results)` — Step 5 verdict
- `extract_candidates_from_maps_and_tree(maps, tree_result, disc, alive_features)` — helper that picks top univariate bins + tree splits and converts them to `(feature, op, threshold)` tuples for Step 4
- `main()` — orchestrates Steps 0-5

```python
def print_separator(title: str):
    print(f'\n{"=" * 70}')
    print(f'  {title}')
    print(f'{"=" * 70}\n')


def print_variance_report(exc, features):
    print_separator('Step 0: Feature Variance Check')
    alive, dead, report = variance_check(exc, features)
    print(report.to_string(index=False))
    print(f'\nAlive: {len(alive)} | Dead: {len(dead)}')
    if dead:
        print(f'Killed: {", ".join(dead)}')
    return alive, dead


def print_split_info(info):
    print_separator('Step 1: Discovery / Holdout Split')
    for k, v in info.items():
        print(f'  {k}: {v}')


def print_univariate_maps(disc, alive_features, n_bins=5):
    print_separator('Step 2: Univariate Response Maps')
    maps = {}
    for f in alive_features:
        print(f'\n--- {f} ---')
        m = univariate_response_map(disc, f, n_bins=n_bins)
        print(m.to_string(index=False))
        maps[f] = m
    return maps


def print_tree_discovery(disc, alive_features):
    print_separator('Step 3: Shallow Tree Discovery')
    result = shallow_tree_discovery(disc, alive_features)
    print('Tree structure:')
    print(result['tree_text'])
    print('\nFeature importances:')
    print(result['importances'].to_string())
    print('\nLeaf statistics:')
    print(result['leaves'].to_string(index=False))
    return result


def extract_candidates_from_maps_and_tree(maps, tree_result, disc,
                                           alive_features):
    """Pick top univariate thresholds + tree split points as candidates."""
    candidates = []
    seen = set()
    baseline_pf = _profit_factor(disc['net_12'])

    # From univariate maps: top bins with PF > baseline + 0.1 and N >= 30
    for f, m in maps.items():
        for _, row in m.iterrows():
            if row['N'] < 30:
                continue
            pf = row['PF']
            if not np.isfinite(pf) or pf <= baseline_pf + 0.1:
                continue
            # Parse bin interval to get threshold
            bin_str = row['bin']
            try:
                # pandas Interval string like "(3.5, 5.2]"
                right = float(bin_str.split(',')[0].strip('(['))
                key = (f, '>', round(right, 3))
                if key not in seen:
                    candidates.append(key)
                    seen.add(key)
            except (ValueError, IndexError):
                continue

    # From tree: extract split thresholds
    tree = tree_result['tree']
    feature_idx = tree.tree_.feature
    threshold = tree.tree_.threshold
    for node_id in range(tree.tree_.node_count):
        if feature_idx[node_id] >= 0:  # not a leaf
            fname = alive_features[feature_idx[node_id]]
            thr = round(threshold[node_id], 3)
            key_gt = (fname, '>', thr)
            key_le = (fname, '<=', thr)
            if key_gt not in seen:
                candidates.append(key_gt)
                seen.add(key_gt)
            if key_le not in seen:
                candidates.append(key_le)
                seen.add(key_le)

    return candidates


def print_pairwise_results(disc, candidates):
    print_separator('Step 4: Pairwise Combinations')
    print(f'Candidates: {len(candidates)}')
    for c in candidates:
        print(f'  {c[0]} {c[1]} {c[2]}')
    result = pairwise_combinations(disc, candidates)
    print(f'\nResults ({len(result)} rules):')
    print(result.to_string(index=False))
    return result


def print_holdout_results(hold, top_pcts):
    print_separator('Step 5: Holdout Validation')
    results = []
    for pct in top_pcts:
        r = holdout_validation(hold, top_pct=pct)
        results.append(r)
        status = 'CONFIRMED' if r['confirmed'] else 'NOT CONFIRMED'
        print(f"  top {pct*100:.0f}%: N={r['N_holdout']}, "
              f"PF={r['PF_holdout']}, baseline={r['PF_baseline']} "
              f"-> {status}")
    return results


def main():
    parser = argparse.ArgumentParser(
        description='Signal Quality Filter Research (Variant 4)')
    parser.add_argument('--test-only', action='store_true',
                        help='Use only OOS test-period signals')
    args = parser.parse_args()

    # Load data
    sig_df, ohlc = sr.load_data(test_only=args.test_only)
    real = sig_df[sig_df['signal'].isin([1, -1])].copy()
    print(f'Loaded {len(real)} real BUY/SELL signals')

    # Compute features
    exc = compute_filter_features(real, ohlc)
    print(f'Computed features for {len(exc)} signals')

    # Step 0
    alive, dead = print_variance_report(exc, ALL_FILTER_FEATURES)
    if not alive:
        print('ERROR: No features survived variance check. Aborting.')
        return

    # Step 1
    disc, hold, info = discovery_holdout_split(exc)
    print_split_info(info)

    # Step 2
    maps = print_univariate_maps(disc, alive)

    # Step 3
    tree_result = print_tree_discovery(disc, alive)

    # Step 4
    candidates = extract_candidates_from_maps_and_tree(
        maps, tree_result, disc, alive)
    if candidates:
        pw_result = print_pairwise_results(disc, candidates)
    else:
        print('\nNo candidates passed filters. Skipping pairwise.')

    # Step 5
    # Build score from top features by importance
    top_features = tree_result['importances'].head(3).index.tolist()
    if len(top_features) >= 2:
        scored_disc = build_score(disc, top_features)
        scored_hold = build_score(hold, top_features)
        print_holdout_results(scored_hold, [0.10, 0.15, 0.20, 0.25])
    else:
        print('\nToo few features for score. Skipping holdout.')


if __name__ == '__main__':
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `./.venv/bin/python -m pytest tests/test_signal_quality_research.py -q`
Expected: 15 passed

- [ ] **Step 5: Commit**

```bash
git add API/signal_quality_research.py tests/test_signal_quality_research.py
git commit -m "feat: CLI, report output, and main() orchestrator for signal quality research"
```

---

### Task 9: Full integration test + first real run

**Files:**
- Modify: `tests/test_signal_quality_research.py`

- [ ] **Step 1: Run full test suite**

Run: `./.venv/bin/python -m pytest tests/test_signal_quality_research.py -v`
Expected: all tests pass

- [ ] **Step 2: Run existing signal_research tests to verify no regressions**

Run: `./.venv/bin/python -m pytest tests/test_signal_research.py -q`
Expected: all pass (no changes to signal_research.py)

- [ ] **Step 3: Run real data — test-only mode**

Run: `./.venv/bin/python -m API.signal_quality_research --test-only`
Expected: full output with all 6 steps, no crashes. Review output for correctness.

- [ ] **Step 4: Analyze output and adjust**

Review the real output:
- Step 0: which features survived? (ratio_3 likely killed)
- Step 1: verify N_discovery >= 1000, N_holdout >= 400
- Step 2: do any features show PF > 1.2 in top bins?
- Step 3: what splits does the tree find?
- Step 5: does holdout confirm or reject?

If any step produces obviously wrong results, fix and re-run.

- [ ] **Step 5: Commit final state**

```bash
git add -A
git commit -m "feat: signal quality filter research (Variant 4) complete"
```

Now I'll dispatch the plan review.

<function_calls>
<invoke name="TodoWrite">
<parameter name="todos">[{"content": "Write implementation plan for signal quality filter research", "status": "completed", "activeForm": "Writing implementation plan"}, {"content": "Run plan review", "status": "in_progress", "activeForm": "Running plan review"}]