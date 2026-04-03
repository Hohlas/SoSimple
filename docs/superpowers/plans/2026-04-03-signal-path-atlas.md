# Signal Path Atlas Research Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a standalone Python research tool that produces an ATR-normalized `discovery / holdout` path atlas for the ML signal, validates replicated path effects on holdout, and outputs decision-support evidence for future `market` and `pullback` research without returning to `SL/TP` rule search.

**Architecture:** Keep the existing Variant 2/3 tool untouched and add a new entry point `API/signal_path_atlas.py`. The new script will reuse the same merged signal universe, compute a direction-aware `1..12h` path tensor in ATR units from `entry_close`, derive live pre-signal conditioning features, summarize discovery-only atlas slices, fit interpretable path archetypes with constrained `k-means` plus a shallow explanation tree, freeze those artifacts, then run a single holdout replication pass with structured verdicts and optional CSV exports.

**Tech Stack:** Python 3.11+, pandas, NumPy, scikit-learn (`KMeans`, `DecisionTreeClassifier`), pytest, existing signal/OHLC CSV pipeline

**Repo note:** This plan intentionally omits `git commit` steps because [AGENTS.md](/home/hohla/git/SoSimple/AGENTS.md) allows commits only on explicit user request or during explicit stage-closing work.

---

## File Structure

| File | Action | Responsibility |
|---|---|---|
| `API/signal_path_atlas.py` | Create | Standalone atlas CLI, feature screen, path tensor, archetypes, holdout replication, optional CSV exports |
| `tests/test_signal_path_atlas.py` | Create | Unit and smoke coverage for split logic, path math, feature screening, slices, archetypes, verdict logic, and CLI sections |
| `API/README.md` | Modify | Document the new research tool and its command line entry points |
| `docs/superpowers/specs/2026-04-03-signal-path-atlas-design.md` | Read | Approved design spec that defines the research contract |
| `API/signal_research.py` | Read | Existing loader/OOS semantics reference; do not extend this already-large file for atlas work |

## Tasks

### Task 1: Scaffold the standalone atlas tool and lock the core path tensor

**Files:**
- Create: `API/signal_path_atlas.py`
- Create: `tests/test_signal_path_atlas.py`

- [ ] **Step 1: Write the failing tests for split semantics and direction-aware path math**

```python
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, 'API')
import signal_path_atlas as spa


def _ohlc_frame():
    return pd.DataFrame({
        'time': pd.to_datetime([
            '2024-12-31 23:00',
            '2025-01-01 00:00',
            '2025-01-01 01:00',
            '2025-01-01 02:00',
            '2025-01-01 03:00',
        ]),
        'open': [100.0, 100.0, 102.0, 99.0, 103.0],
        'high': [101.0, 103.0, 104.0, 105.0, 106.0],
        'low': [99.0, 99.5, 97.0, 98.0, 101.0],
        'close': [100.0, 102.0, 98.0, 104.0, 105.0],
        'atr14': [2.0, 2.0, 2.0, 2.0, 2.0],
    })


def test_annotate_sample_split_uses_fixed_calendar_boundary():
    frame = pd.DataFrame({
        'time': pd.to_datetime(['2024-12-31 23:59:59', '2025-01-01 00:00:00'])
    })
    out = spa.annotate_sample_split(frame)
    assert out['sample'].tolist() == ['discovery', 'holdout']


def test_build_path_tensor_aligns_buy_and_sell_in_signed_atr_space():
    ohlc = _ohlc_frame()
    signals = pd.DataFrame([
        {'time': ohlc.loc[0, 'time'], 'signal': 1, 'entry_close': 100.0, 'entry_atr14': 2.0},
        {'time': ohlc.loc[1, 'time'], 'signal': -1, 'entry_close': 102.0, 'entry_atr14': 2.0},
    ])

    out = spa.build_path_tensor(signals, ohlc)

    assert out.loc[0, 'signed_ret_1'] == pytest.approx(1.0, abs=1e-9)
    assert out.loc[0, 'fav_2'] == pytest.approx(2.0, abs=1e-9)
    assert out.loc[0, 'adv_2'] == pytest.approx(1.5, abs=1e-9)
    assert out.loc[1, 'signed_ret_1'] == pytest.approx(2.0, abs=1e-9)
    assert out.loc[1, 'fav_2'] == pytest.approx(2.5, abs=1e-9)
    assert out.loc[1, 'adv_2'] == pytest.approx(1.5, abs=1e-9)
```

- [ ] **Step 2: Run the new tests to verify they fail before implementation**

Run:

```bash
./.venv/bin/python -m pytest tests/test_signal_path_atlas.py::test_annotate_sample_split_uses_fixed_calendar_boundary tests/test_signal_path_atlas.py::test_build_path_tensor_aligns_buy_and_sell_in_signed_atr_space -q
```

Expected: `FAILED` because `signal_path_atlas.py` and its helpers do not exist yet.

- [ ] **Step 3: Write the minimal atlas skeleton with split helpers and path tensor math**

```python
# API/signal_path_atlas.py
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

DISCOVERY_END = pd.Timestamp('2024-12-31 23:59:59')
PATH_HORIZONS = list(range(1, 13))
ADVERSE_LEVELS = [1.0, 2.0, 3.0]
FAVORABLE_LEVELS = [1.0, 2.0, 3.0, 5.0]


def annotate_sample_split(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out['sample'] = np.where(out['time'] <= DISCOVERY_END, 'discovery', 'holdout')
    return out


def build_path_tensor(signals: pd.DataFrame, ohlc: pd.DataFrame) -> pd.DataFrame:
    ohlc = ohlc.sort_values('time').reset_index(drop=True)
    time_to_idx = {ts: idx for idx, ts in enumerate(ohlc['time'])}
    highs = ohlc['high'].to_numpy()
    lows = ohlc['low'].to_numpy()
    closes = ohlc['close'].to_numpy()
    rows = []

    for row in signals.itertuples(index=False):
        idx = time_to_idx.get(row.time)
        if idx is None:
            continue
        rec = {'time': row.time, 'signal': row.signal, 'entry_close': row.entry_close, 'entry_atr14': row.entry_atr14}
        for h in PATH_HORIZONS:
            end = min(idx + h, len(ohlc) - 1)
            if end <= idx:
                rec[f'signed_ret_{h}'] = np.nan
                rec[f'fav_{h}'] = np.nan
                rec[f'adv_{h}'] = np.nan
                continue
            window_high = highs[idx + 1:end + 1]
            window_low = lows[idx + 1:end + 1]
            exit_close = closes[end]
            rec[f'signed_ret_{h}'] = (exit_close - row.entry_close) * row.signal / row.entry_atr14
            if row.signal == 1:
                rec[f'fav_{h}'] = (window_high.max() - row.entry_close) / row.entry_atr14
                rec[f'adv_{h}'] = (row.entry_close - window_low.min()) / row.entry_atr14
            else:
                rec[f'fav_{h}'] = (row.entry_close - window_low.min()) / row.entry_atr14
                rec[f'adv_{h}'] = (window_high.max() - row.entry_close) / row.entry_atr14
        for level in ADVERSE_LEVELS:
            adverse_hits = [h for h in PATH_HORIZONS if pd.notna(rec[f'adv_{h}']) and rec[f'adv_{h}'] >= level]
            favorable_hits = [h for h in PATH_HORIZONS if pd.notna(rec[f'fav_{h}']) and rec[f'fav_{h}'] >= level]
            adverse_idx = adverse_hits[0] if adverse_hits else np.nan
            favorable_idx = favorable_hits[0] if favorable_hits else np.nan
            rec[f'adverse_first_{int(level)}atr'] = float(pd.notna(adverse_idx) and (pd.isna(favorable_idx) or adverse_idx < favorable_idx))
            rec[f'favorable_first_{int(level)}atr'] = float(pd.notna(favorable_idx) and (pd.isna(adverse_idx) or favorable_idx < adverse_idx))
            rec[f'dip_then_rally_{int(level)}atr'] = float(pd.notna(adverse_idx) and pd.notna(favorable_idx) and adverse_idx < favorable_idx)
            rec[f'rally_then_dip_{int(level)}atr'] = float(pd.notna(adverse_idx) and pd.notna(favorable_idx) and favorable_idx < adverse_idx)
        rows.append(rec)

    return pd.DataFrame(rows)
```

- [ ] **Step 4: Run the focused tests again and verify they pass**

Run:

```bash
./.venv/bin/python -m pytest tests/test_signal_path_atlas.py::test_annotate_sample_split_uses_fixed_calendar_boundary tests/test_signal_path_atlas.py::test_build_path_tensor_aligns_buy_and_sell_in_signed_atr_space -q
```

Expected: `2 passed`.

### Task 2: Add conditioning features, categorical cohorts, and the discovery feature screen

**Files:**
- Modify: `API/signal_path_atlas.py`
- Modify: `tests/test_signal_path_atlas.py`

- [ ] **Step 1: Write failing tests for feature families, ATR buckets, and kill criteria**

```python
def test_build_conditioning_frame_creates_ratio_spread_short_vs_long_and_fixed_cohorts():
    frame = pd.DataFrame([
        {
            'time': pd.Timestamp('2024-06-01 00:00'),
            'signal': 1,
            'entry_atr14': 2.0,
            'up_3': 6.0, 'dn_3': 2.0,
            'up_6': 8.0, 'dn_6': 4.0,
            'up_12': 10.0, 'dn_12': 5.0,
            'up_24': 12.0, 'dn_24': 6.0,
            'up_48': 14.0, 'dn_48': 7.0,
        },
        {
            'time': pd.Timestamp('2024-06-01 01:00'),
            'signal': 1,
            'entry_atr14': 2.5,
            'up_3': 7.0, 'dn_3': 3.0,
            'up_6': 9.0, 'dn_6': 4.0,
            'up_12': 11.0, 'dn_12': 5.0,
            'up_24': 13.0, 'dn_24': 6.0,
            'up_48': 15.0, 'dn_48': 8.0,
        },
        {
            'time': pd.Timestamp('2024-06-01 02:00'),
            'signal': -1,
            'entry_atr14': 3.0,
            'up_3': 4.0, 'dn_3': 8.0,
            'up_6': 5.0, 'dn_6': 10.0,
            'up_12': 6.0, 'dn_12': 12.0,
            'up_24': 7.0, 'dn_24': 14.0,
            'up_48': 8.0, 'dn_48': 16.0,
        },
        {
            'time': pd.Timestamp('2024-06-01 03:00'),
            'signal': -1,
            'entry_atr14': 4.0,
            'up_3': 5.0, 'dn_3': 9.0,
            'up_6': 6.0, 'dn_6': 11.0,
            'up_12': 7.0, 'dn_12': 13.0,
            'up_24': 8.0, 'dn_24': 15.0,
            'up_48': 9.0, 'dn_48': 17.0,
        },
    ])
    out, artifacts = spa.build_conditioning_frame(frame)
    assert out.loc[0, 'ratio_12'] == pytest.approx(2.0, abs=1e-9)
    assert out.loc[0, 'spread_12'] == pytest.approx(5.0, abs=1e-9)
    assert out.loc[0, 'ratio_3_vs_12'] == pytest.approx(1.5, abs=1e-9)
    assert out.loc[0, 'signal_label'] == 'BUY'
    assert out.loc[0, 'ratio_bin_12'] == '2-3'
    assert artifacts['atr_edges'][0] <= out.loc[0, 'entry_atr14'] <= artifacts['atr_edges'][-1]


def test_screen_features_drops_near_constant_axes_before_slicing():
    frame = pd.DataFrame({
        'time': pd.date_range('2024-01-01', periods=120, freq='h'),
        'good_feature': np.linspace(1.0, 3.0, 120),
        'flat_q90_q10': np.ones(120),
        'flat_iqr': np.r_[np.zeros(119), 1.0],
    })
    summary, live = spa.screen_numeric_features(frame, ['good_feature', 'flat_q90_q10', 'flat_iqr'])
    assert 'good_feature' in live
    assert 'flat_q90_q10' not in live
    assert 'flat_iqr' not in live
```

- [ ] **Step 2: Run the tests and confirm the new expectations fail**

Run:

```bash
./.venv/bin/python -m pytest tests/test_signal_path_atlas.py::test_build_conditioning_frame_creates_ratio_spread_short_vs_long_and_fixed_cohorts tests/test_signal_path_atlas.py::test_screen_features_drops_near_constant_axes_before_slicing -q
```

Expected: `FAILED` because the conditioning frame and screen helpers are not implemented yet.

- [ ] **Step 3: Implement conditioning features and freeze discovery-side screening artifacts**

```python
RATIO_BIN_EDGES = [0.0, 2.0, 3.0, 4.0, 5.0, np.inf]
RATIO_BIN_LABELS = ['<2', '2-3', '3-4', '4-5', '5+']
NUMERIC_FEATURES = [
    'ratio_3', 'ratio_6', 'ratio_12', 'ratio_24', 'ratio_48',
    'spread_3', 'spread_6', 'spread_12', 'spread_24', 'spread_48',
    'ratio_3_vs_12', 'spread_3_vs_12', 'fav_3_vs_12',
    'ratio_6_vs_24', 'spread_6_vs_24', 'ratio_12_vs_48', 'spread_12_vs_48',
]
FIXED_COHORT_COLS = ['signal_label', 'ratio_bin_12', 'atr_bucket']


def build_conditioning_frame(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    out = frame.copy()
    eps = 1e-6
    for h in (3, 6, 12, 24, 48):
        if f'pred_fav_{h}' not in out.columns:
            out[f'pred_fav_{h}'] = np.where(out['signal'] == 1, out[f'up_{h}'], out[f'dn_{h}'])
            out[f'pred_adv_{h}'] = np.where(out['signal'] == 1, out[f'dn_{h}'], out[f'up_{h}'])
        out[f'ratio_{h}'] = out[f'pred_fav_{h}'] / out[f'pred_adv_{h}'].clip(lower=eps)
        out[f'spread_{h}'] = out[f'pred_fav_{h}'] - out[f'pred_adv_{h}']
    out['ratio_3_vs_12'] = out['ratio_3'] / out['ratio_12'].clip(lower=eps)
    out['spread_3_vs_12'] = out['spread_3'] / out['spread_12'].replace(0, np.nan)
    out['fav_3_vs_12'] = out['pred_fav_3'] / out['pred_fav_12'].clip(lower=eps)
    out['ratio_6_vs_24'] = out['ratio_6'] / out['ratio_24'].clip(lower=eps)
    out['spread_6_vs_24'] = out['spread_6'] / out['spread_24'].replace(0, np.nan)
    out['ratio_12_vs_48'] = out['ratio_12'] / out['ratio_48'].clip(lower=eps)
    out['spread_12_vs_48'] = out['spread_12'] / out['spread_48'].replace(0, np.nan)
    out['signal_label'] = np.where(out['signal'] == 1, 'BUY', 'SELL')
    out['ratio_bin_12'] = pd.cut(out['ratio_12'], bins=RATIO_BIN_EDGES, labels=RATIO_BIN_LABELS, right=False)
    atr_edges = np.quantile(out['entry_atr14'], [0.0, 0.25, 0.5, 0.75, 1.0])
    out['atr_bucket'] = pd.cut(out['entry_atr14'], bins=atr_edges, labels=['Q1', 'Q2', 'Q3', 'Q4'], include_lowest=True, duplicates='drop')
    return out, {'atr_edges': atr_edges}


def screen_numeric_features(frame: pd.DataFrame, features: list[str]) -> tuple[pd.DataFrame, list[str]]:
    rows = []
    live = []
    for feature in features:
        series = frame[feature].replace([np.inf, -np.inf], np.nan).dropna()
        q10 = series.quantile(0.10)
        q50 = series.quantile(0.50)
        q90 = series.quantile(0.90)
        iqr = series.quantile(0.75) - series.quantile(0.25)
        is_live = not (q90 == q10 or iqr == 0 or series.nunique() < 20)
        rows.append({'feature': feature, 'mean': series.mean(), 'std': series.std(ddof=0), 'q10': q10, 'q50': q50, 'q90': q90, 'iqr': iqr, 'n_unique': int(series.nunique()), 'is_live': is_live})
        if is_live:
            live.append(feature)
    return pd.DataFrame(rows), live
```

- [ ] **Step 4: Run the focused tests again and verify they pass**

Run:

```bash
./.venv/bin/python -m pytest tests/test_signal_path_atlas.py::test_build_conditioning_frame_creates_ratio_spread_short_vs_long_and_fixed_cohorts tests/test_signal_path_atlas.py::test_screen_features_drops_near_constant_axes_before_slicing -q
```

Expected: `2 passed`.

### Task 3: Build the discovery atlas summaries for global, numeric-bin, and categorical slices

**Files:**
- Modify: `API/signal_path_atlas.py`
- Modify: `tests/test_signal_path_atlas.py`

- [ ] **Step 1: Write failing tests for first-passage tables, bin-merging, and categorical cohort summaries**

```python
def test_build_global_atlas_reports_quantiles_first_passage_and_ordering():
    frame = pd.DataFrame({
        'signed_ret_1': [0.5, -0.5, 1.0, 0.0],
        'signed_ret_12': [2.0, -1.0, 3.0, 0.5],
        'fav_3': [1.5, 0.4, 2.5, 0.8],
        'adv_3': [0.2, 1.2, 0.4, 0.7],
        'fav_12': [3.5, 1.0, 5.0, 1.5],
        'adv_12': [0.5, 2.5, 1.0, 1.2],
        'adverse_first_1atr': [0, 1, 0, 1],
        'favorable_first_1atr': [1, 0, 1, 0],
        'dip_then_rally_1atr': [0, 1, 0, 0],
        'rally_then_dip_1atr': [1, 0, 0, 1],
    })
    atlas = spa.build_global_atlas(frame)
    assert set(atlas.keys()) == {'path_quantiles', 'first_passage', 'ordering'}
    assert (atlas['first_passage']['level_atr'] == 3.0).any()


def test_build_numeric_slices_merges_thin_bins_until_support_floor_is_met():
    frame = pd.DataFrame({
        'feature_a': np.r_[np.linspace(0.0, 1.0, 90), np.linspace(10.0, 11.0, 10)],
        'signed_ret_12': np.linspace(-1.0, 2.0, 100),
        'fav_12': np.linspace(0.5, 4.0, 100),
        'adv_12': np.linspace(0.2, 2.0, 100),
        'adverse_first_1atr': [0] * 100,
        'favorable_first_1atr': [1] * 100,
        'dip_then_rally_1atr': [0] * 100,
        'rally_then_dip_1atr': [0] * 100,
    })
    slices = spa.build_numeric_slices(frame, feature='feature_a', min_rows=20, min_frac=0.10)
    assert slices['bin_id'].nunique() <= 4
    assert slices['N'].min() >= 20


def test_build_categorical_slices_keeps_signal_ratio_bucket_and_atr_bucket():
    frame = pd.DataFrame({
        'signal_label': ['BUY', 'BUY', 'SELL', 'SELL'],
        'ratio_bin_12': ['4-5', '4-5', '3-4', '5+'],
        'atr_bucket': ['Q4', 'Q4', 'Q2', 'Q1'],
        'signed_ret_12': [1.0, 1.2, -0.4, 0.1],
        'fav_12': [3.0, 3.5, 1.0, 1.5],
        'adv_12': [0.5, 0.6, 1.2, 0.8],
        'adverse_first_1atr': [0, 0, 1, 0],
        'favorable_first_1atr': [1, 1, 0, 1],
        'dip_then_rally_1atr': [0, 1, 0, 0],
        'rally_then_dip_1atr': [0, 0, 1, 0],
    })
    out = spa.build_categorical_slices(frame, ['signal_label', 'ratio_bin_12', 'atr_bucket'])
    assert {'signal_label', 'ratio_bin_12', 'atr_bucket'} <= set(out['group_col'])
```

- [ ] **Step 2: Run the new slice tests and confirm they fail**

Run:

```bash
./.venv/bin/python -m pytest tests/test_signal_path_atlas.py::test_build_global_atlas_reports_quantiles_first_passage_and_ordering tests/test_signal_path_atlas.py::test_build_numeric_slices_merges_thin_bins_until_support_floor_is_met tests/test_signal_path_atlas.py::test_build_categorical_slices_keeps_signal_ratio_bucket_and_atr_bucket -q
```

Expected: `FAILED` because the atlas summary helpers are still missing.

- [ ] **Step 3: Implement discovery atlas summaries with fixed support floors**

```python
def build_global_atlas(frame: pd.DataFrame) -> dict[str, pd.DataFrame]:
    horizons = sorted(int(col.split('_')[-1]) for col in frame.columns if col.startswith('signed_ret_'))
    ordering_levels = sorted(int(col.split('_')[-1].replace('atr', '')) for col in frame.columns if col.startswith('adverse_first_'))
    path_rows = []
    for h in horizons:
        path_rows.append({
            'horizon': h,
            'signed_ret_q10': frame[f'signed_ret_{h}'].quantile(0.10),
            'signed_ret_q50': frame[f'signed_ret_{h}'].quantile(0.50),
            'signed_ret_q90': frame[f'signed_ret_{h}'].quantile(0.90),
            'fav_q10': frame[f'fav_{h}'].quantile(0.10),
            'fav_q50': frame[f'fav_{h}'].quantile(0.50),
            'fav_q90': frame[f'fav_{h}'].quantile(0.90),
            'adv_q10': frame[f'adv_{h}'].quantile(0.10),
            'adv_q50': frame[f'adv_{h}'].quantile(0.50),
            'adv_q90': frame[f'adv_{h}'].quantile(0.90),
        })
    first_passage = []
    for h in horizons:
        for level in ADVERSE_LEVELS:
            if f'adv_{h}' in frame.columns:
                first_passage.append({'side': 'adverse', 'level_atr': level, 'horizon': h, 'hit_pct': 100.0 * (frame[f'adv_{h}'] >= level).mean()})
        for level in FAVORABLE_LEVELS:
            if f'fav_{h}' in frame.columns:
                first_passage.append({'side': 'favorable', 'level_atr': level, 'horizon': h, 'hit_pct': 100.0 * (frame[f'fav_{h}'] >= level).mean()})
    ordering = pd.DataFrame([{
        'level_atr': level,
        'adverse_first_pct': 100.0 * frame[f'adverse_first_{int(level)}atr'].mean(),
        'favorable_first_pct': 100.0 * frame[f'favorable_first_{int(level)}atr'].mean(),
        'dip_then_rally_pct': 100.0 * frame[f'dip_then_rally_{int(level)}atr'].mean(),
        'rally_then_dip_pct': 100.0 * frame[f'rally_then_dip_{int(level)}atr'].mean(),
    } for level in ordering_levels])
    return {'path_quantiles': pd.DataFrame(path_rows), 'first_passage': pd.DataFrame(first_passage), 'ordering': ordering}


def summarize_slice_groups(frame: pd.DataFrame, group_col: str) -> pd.DataFrame:
    return frame.groupby(group_col, dropna=False).agg(
        N=('signed_ret_12', 'size'),
        signed_ret_12_q50=('signed_ret_12', 'median'),
        fav_12_q50=('fav_12', 'median'),
        adv_12_q50=('adv_12', 'median'),
        adverse_first_1atr_pct=('adverse_first_1atr', lambda s: 100.0 * s.mean()),
        favorable_first_1atr_pct=('favorable_first_1atr', lambda s: 100.0 * s.mean()),
        dip_then_rally_1atr_pct=('dip_then_rally_1atr', lambda s: 100.0 * s.mean()),
        rally_then_dip_1atr_pct=('rally_then_dip_1atr', lambda s: 100.0 * s.mean()),
    ).reset_index()


def build_numeric_slices(frame: pd.DataFrame, feature: str, min_rows: int = 80, min_frac: float = 0.05) -> pd.DataFrame:
    metric_cols = [col for col in frame.columns if col.startswith('signed_ret_') or col.startswith('fav_') or col.startswith('adv_')]
    metric_cols += ['adverse_first_1atr', 'favorable_first_1atr', 'dip_then_rally_1atr', 'rally_then_dip_1atr']
    work = frame[[feature] + metric_cols].dropna(subset=[feature]).copy()
    work['bin_id'] = pd.qcut(work[feature], q=5, labels=False, duplicates='drop')
    while work['bin_id'].nunique() >= 3 and (work['bin_id'].value_counts().min() < max(min_rows, int(np.ceil(min_frac * len(work))))):
        counts = work['bin_id'].value_counts().sort_index()
        smallest = counts.idxmin()
        target = smallest - 1 if smallest == counts.index.max() else smallest + 1
        work.loc[work['bin_id'] == smallest, 'bin_id'] = target
        work['bin_id'] = pd.Categorical(work['bin_id']).codes
    summary = summarize_slice_groups(work, 'bin_id')
    edges = work.groupby('bin_id')[feature].agg(lower_edge='min', upper_edge='max').reset_index()
    summary.insert(0, 'feature', feature)
    return summary.merge(edges, on='bin_id', how='left')


def build_categorical_slices(frame: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    parts = []
    for col in cols:
        grouped = summarize_slice_groups(frame.dropna(subset=[col]), col)
        grouped.insert(0, 'group_col', col)
        parts.append(grouped)
    return pd.concat(parts, ignore_index=True)
```

- [ ] **Step 4: Run the slice tests again and verify they pass**

Run:

```bash
./.venv/bin/python -m pytest tests/test_signal_path_atlas.py::test_build_global_atlas_reports_quantiles_first_passage_and_ordering tests/test_signal_path_atlas.py::test_build_numeric_slices_merges_thin_bins_until_support_floor_is_met tests/test_signal_path_atlas.py::test_build_categorical_slices_keeps_signal_ratio_bucket_and_atr_bucket -q
```

Expected: `3 passed`.

### Task 4: Fit interpretable path archetypes and the shallow explanation tree

**Files:**
- Modify: `API/signal_path_atlas.py`
- Modify: `tests/test_signal_path_atlas.py`

- [ ] **Step 1: Write failing tests for k-means archetypes, small-cluster merge, and tree constraints**

```python
def test_fit_path_archetypes_merges_tiny_clusters_and_returns_readable_names():
    rows = []
    for idx in range(40):
        rows.append({'signed_ret_1': 0.8, 'signed_ret_12': 2.5, 'fav_12': 3.5, 'adv_12': 0.4, 'fav_1': 1.0, 'adv_1': 0.2})
    for idx in range(40):
        rows.append({'signed_ret_1': -0.8, 'signed_ret_12': 1.8, 'fav_12': 3.0, 'adv_12': 2.0, 'fav_1': 0.2, 'adv_1': 1.4})
    for idx in range(40):
        rows.append({'signed_ret_1': 0.0, 'signed_ret_12': 0.2, 'fav_12': 1.0, 'adv_12': 0.9, 'fav_1': 0.1, 'adv_1': 0.1})
    frame = pd.DataFrame(rows)
    labeled, model = spa.fit_path_archetypes(frame, min_frac=0.10)
    assert labeled['archetype'].nunique() in (3, 4)
    assert set(labeled['archetype']).issubset({'immediate_continuation', 'deep_dip_then_recovery', 'flat_or_noisy_drift', 'failure_or_adverse_continuation'})


def test_fit_explanation_tree_is_depth_2_and_respects_min_leaf():
    frame = pd.DataFrame({
        'ratio_12': np.linspace(1.0, 5.0, 120),
        'spread_12': np.linspace(2.0, 10.0, 120),
        'ratio_3_vs_12': np.linspace(0.8, 1.2, 120),
        'archetype': ['immediate_continuation'] * 60 + ['deep_dip_then_recovery'] * 60,
    })
    model, text = spa.fit_explanation_tree(frame, ['ratio_12', 'spread_12', 'ratio_3_vs_12'])
    assert model.get_depth() <= 2
    assert model.min_samples_leaf >= 80
    assert 'class:' in text
```

- [ ] **Step 2: Run the archetype tests and confirm they fail**

Run:

```bash
./.venv/bin/python -m pytest tests/test_signal_path_atlas.py::test_fit_path_archetypes_merges_tiny_clusters_and_returns_readable_names tests/test_signal_path_atlas.py::test_fit_explanation_tree_is_depth_2_and_respects_min_leaf -q
```

Expected: `FAILED` because the clustering and tree helpers do not exist yet.

- [ ] **Step 3: Implement deterministic archetypes and the explanation tree**

```python
from sklearn.cluster import KMeans
from sklearn.tree import DecisionTreeClassifier, export_text


ARCHETYPE_NAMES = {
    'best_early_and_final': 'immediate_continuation',
    'worst_early_but_positive_final': 'deep_dip_then_recovery',
    'worst_final': 'failure_or_adverse_continuation',
    'remainder': 'flat_or_noisy_drift',
}


def fit_path_archetypes(frame: pd.DataFrame, min_frac: float = 0.10) -> tuple[pd.DataFrame, dict]:
    feature_cols = sorted([col for col in frame.columns if col.startswith('signed_ret_') or col.startswith('fav_') or col.startswith('adv_')])
    X = frame[feature_cols].fillna(0.0).to_numpy()
    model = KMeans(n_clusters=4, n_init=20, random_state=0)
    labels = model.fit_predict(X)
    out = frame.copy()
    out['cluster_id'] = labels
    counts = out['cluster_id'].value_counts(normalize=True)
    if counts.min() < min_frac:
        small = counts.idxmin()
        centers = model.cluster_centers_
        distances = ((centers - centers[small]) ** 2).sum(axis=1)
        distances[small] = np.inf
        nearest = int(np.argmin(distances))
        out.loc[out['cluster_id'] == small, 'cluster_id'] = nearest
    early_col = 'signed_ret_1' if 'signed_ret_1' in out.columns else sorted([col for col in out.columns if col.startswith('signed_ret_')])[0]
    final_col = 'signed_ret_12' if 'signed_ret_12' in out.columns else sorted([col for col in out.columns if col.startswith('signed_ret_')])[-1]
    dip_col = 'adv_3' if 'adv_3' in out.columns else sorted([col for col in out.columns if col.startswith('adv_')])[-1]
    cluster_stats = out.groupby('cluster_id').agg(
        early_q50=(early_col, 'median'),
        final_q50=(final_col, 'median'),
        dip_q50=(dip_col, 'median'),
    )
    best_early = cluster_stats['early_q50'].idxmax()
    worst_final = cluster_stats['final_q50'].idxmin()
    deepest_dip = cluster_stats['dip_q50'].idxmax()
    name_map = {best_early: 'immediate_continuation', deepest_dip: 'deep_dip_then_recovery', worst_final: 'failure_or_adverse_continuation'}
    for cluster_id in cluster_stats.index:
        name_map.setdefault(cluster_id, 'flat_or_noisy_drift')
    out['archetype'] = out['cluster_id'].map(name_map)
    return out, {'feature_cols': feature_cols, 'cluster_stats': cluster_stats.reset_index(), 'model': model, 'name_map': name_map}


def fit_explanation_tree(frame: pd.DataFrame, feature_cols: list[str]) -> tuple[DecisionTreeClassifier, str]:
    min_leaf = max(80, int(np.ceil(0.05 * len(frame))))
    model = DecisionTreeClassifier(max_depth=2, min_samples_leaf=min_leaf, random_state=0)
    model.fit(frame[feature_cols].fillna(0.0), frame['archetype'])
    return model, export_text(model, feature_names=feature_cols)
```

- [ ] **Step 4: Run the archetype tests again and verify they pass**

Run:

```bash
./.venv/bin/python -m pytest tests/test_signal_path_atlas.py::test_fit_path_archetypes_merges_tiny_clusters_and_returns_readable_names tests/test_signal_path_atlas.py::test_fit_explanation_tree_is_depth_2_and_respects_min_leaf -q
```

Expected: `2 passed`.

### Task 5: Freeze discovery artifacts, run holdout replication, and expose CSV/report outputs

**Files:**
- Modify: `API/signal_path_atlas.py`
- Modify: `tests/test_signal_path_atlas.py`
- Modify: `API/README.md`

- [ ] **Step 1: Write failing tests for verdict classification, CSV export, and CLI report smoke**

```python
def test_classify_replication_verdict_uses_sign_and_magnitude_retention():
    verdict = spa.classify_replication_verdict({
        'N_holdout': 40,
        'delta_signed_ret_12_q50_discovery': 0.80,
        'delta_signed_ret_12_q50_holdout': 0.50,
        'delta_fav_hit_3atr_12h_discovery': 12.0,
        'delta_fav_hit_3atr_12h_holdout': 9.0,
        'delta_adv_hit_1atr_3h_discovery': -10.0,
        'delta_adv_hit_1atr_3h_holdout': -6.0,
        'delta_adverse_first_1atr_discovery': -8.0,
        'delta_adverse_first_1atr_holdout': -5.0,
    })
    assert verdict == 'Replicated'


def test_export_tables_writes_expected_csv_files(tmp_path):
    tables = {
        'feature_screen': pd.DataFrame({'feature': ['ratio_12'], 'is_live': [True]}),
        'holdout_verdicts': pd.DataFrame({'artifact_id': ['signal_label=BUY'], 'verdict': ['Replicated']}),
    }
    spa.export_tables(tables, tmp_path)
    assert (tmp_path / 'feature_screen.csv').exists()
    assert (tmp_path / 'holdout_verdicts.csv').exists()


def test_cli_report_smoke(capsys):
    tables = {
        'split_summary': pd.DataFrame({'sample': ['discovery', 'holdout'], 'N': [100, 40]}),
        'feature_screen': pd.DataFrame({'feature': ['ratio_12'], 'is_live': [True]}),
        'holdout_verdicts': pd.DataFrame({'artifact_id': ['signal_label=BUY'], 'verdict': ['Replicated']}),
        'execution_implications': pd.DataFrame({'recommendation': ['market and pullback both justified']}),
    }
    spa.print_report_sections(tables)
    out = capsys.readouterr().out
    assert 'Signal Path Atlas — Discovery/Holdout Split' in out
    assert 'Feature Variance Screen' in out
    assert 'Holdout Replication Verdicts' in out
    assert 'Execution Implications' in out
```

- [ ] **Step 2: Run the new reporting tests and confirm they fail**

Run:

```bash
./.venv/bin/python -m pytest tests/test_signal_path_atlas.py::test_classify_replication_verdict_uses_sign_and_magnitude_retention tests/test_signal_path_atlas.py::test_export_tables_writes_expected_csv_files tests/test_signal_path_atlas.py::test_cli_report_smoke -q
```

Expected: `FAILED` because the verdict/export/report helpers are not implemented yet.

- [ ] **Step 3: Implement the locked-artifact holdout pass, report printing, and README entry**

```python
try:
    from . import signal_research as sr
except ImportError:
    import signal_research as sr


KEY_REPLICATION_METRICS = [
    ('signed_ret_12_q50', 1.0),
    ('fav_hit_3atr_12h', 1.0),
    ('adv_hit_1atr_3h', -1.0),
    ('adverse_first_1atr', -1.0),
]


def classify_replication_verdict(row: dict) -> str:
    if row['N_holdout'] < 30:
        return 'Exploratory'
    same_sign = 0
    retained = 0
    for metric, direction in KEY_REPLICATION_METRICS:
        d_key = f'delta_{metric}_discovery'
        h_key = f'delta_{metric}_holdout'
        d_val = row[d_key] * direction
        h_val = row[h_key] * direction
        if d_val == 0:
            continue
        if np.sign(d_val) == np.sign(h_val) or h_val == 0:
            same_sign += 1
        if abs(h_val) >= 0.5 * abs(d_val):
            retained += 1
    if same_sign >= 3 and retained >= 2:
        return 'Replicated'
    if same_sign >= 3:
        return 'Directionally consistent'
    return 'Failed'


def build_split_summary(discovery: pd.DataFrame, holdout: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame([
        {
            'sample': 'discovery',
            'N': len(discovery),
            'start': discovery['time'].min(),
            'end': discovery['time'].max(),
            'buy_N': int((discovery['signal'] == 1).sum()),
            'sell_N': int((discovery['signal'] == -1).sum()),
        },
        {
            'sample': 'holdout',
            'N': len(holdout),
            'start': holdout['time'].min(),
            'end': holdout['time'].max(),
            'buy_N': int((holdout['signal'] == 1).sum()),
            'sell_N': int((holdout['signal'] == -1).sum()),
        },
    ])


def summarize_archetypes(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.groupby('archetype').agg(
        N=('archetype', 'size'),
        signed_ret_12_q50=('signed_ret_12', 'median'),
        fav_12_q50=('fav_12', 'median'),
        adv_12_q50=('adv_12', 'median'),
        adverse_first_1atr_pct=('adverse_first_1atr', lambda s: 100.0 * s.mean()),
    ).reset_index()


def _artifact_metrics(frame: pd.DataFrame) -> dict:
    return {
        'N': len(frame),
        'signed_ret_12_q50': frame['signed_ret_12'].median(),
        'fav_hit_3atr_12h': 100.0 * (frame['fav_12'] >= 3.0).mean(),
        'adv_hit_1atr_3h': 100.0 * (frame['adv_3'] >= 1.0).mean(),
        'adverse_first_1atr': 100.0 * frame['adverse_first_1atr'].mean(),
    }


def build_holdout_verdicts(
    discovery: pd.DataFrame,
    holdout: pd.DataFrame,
    numeric_slices: pd.DataFrame,
    archetype_artifacts: dict,
) -> pd.DataFrame:
    discovery_base = _artifact_metrics(discovery)
    holdout_base = _artifact_metrics(holdout)
    rows = []

    for slice_row in numeric_slices.itertuples(index=False):
        d_mask = discovery[slice_row.feature].between(slice_row.lower_edge, slice_row.upper_edge, inclusive='both')
        h_mask = holdout[slice_row.feature].between(slice_row.lower_edge, slice_row.upper_edge, inclusive='both')
        d_metrics = _artifact_metrics(discovery[d_mask])
        h_metrics = _artifact_metrics(holdout[h_mask])
        row = {
            'artifact_id': f'{slice_row.feature}:bin_{slice_row.bin_id}',
            'N_holdout': h_metrics['N'],
        }
        for metric, _ in KEY_REPLICATION_METRICS:
            row[f'delta_{metric}_discovery'] = d_metrics[metric] - discovery_base[metric]
            row[f'delta_{metric}_holdout'] = h_metrics[metric] - holdout_base[metric]
        row['verdict'] = classify_replication_verdict(row)
        rows.append(row)

    for col in FIXED_COHORT_COLS:
        for value, d_group in discovery.groupby(col):
            h_group = holdout[holdout[col] == value]
            d_metrics = _artifact_metrics(d_group)
            h_metrics = _artifact_metrics(h_group)
            row = {'artifact_id': f'{col}={value}', 'N_holdout': h_metrics['N']}
            for metric, _ in KEY_REPLICATION_METRICS:
                row[f'delta_{metric}_discovery'] = d_metrics[metric] - discovery_base[metric]
                row[f'delta_{metric}_holdout'] = h_metrics[metric] - holdout_base[metric]
            row['verdict'] = classify_replication_verdict(row)
            rows.append(row)

    X_holdout = holdout[archetype_artifacts['feature_cols']].fillna(0.0)
    holdout_clusters = archetype_artifacts['model'].predict(X_holdout)
    holdout_named = holdout.copy()
    holdout_named['archetype'] = pd.Series(holdout_clusters).map(archetype_artifacts['name_map'])
    for archetype, group in holdout_named.groupby('archetype'):
        d_group = discovery[discovery['archetype'] == archetype]
        d_metrics = _artifact_metrics(d_group)
        h_metrics = _artifact_metrics(group)
        row = {'artifact_id': f'archetype:{archetype}', 'N_holdout': h_metrics['N']}
        for metric, _ in KEY_REPLICATION_METRICS:
            row[f'delta_{metric}_discovery'] = d_metrics[metric] - discovery_base[metric]
            row[f'delta_{metric}_holdout'] = h_metrics[metric] - holdout_base[metric]
        row['verdict'] = classify_replication_verdict(row)
        rows.append(row)

    return pd.DataFrame(rows).sort_values(['verdict', 'artifact_id']).reset_index(drop=True)


def build_execution_implications(holdout_verdicts: pd.DataFrame) -> pd.DataFrame:
    replicated = holdout_verdicts[holdout_verdicts['verdict'] == 'Replicated']
    recommendation = 'neither'
    if any(replicated['artifact_id'].str.contains('archetype:deep_dip_then_recovery', regex=False)):
        recommendation = 'pullback'
    if any(replicated['artifact_id'].str.contains('archetype:immediate_continuation', regex=False)):
        recommendation = 'market' if recommendation == 'neither' else 'market and pullback both justified'
    return pd.DataFrame([{'recommendation': recommendation}])


def export_tables(tables: dict[str, pd.DataFrame], export_dir: Path) -> None:
    export_dir.mkdir(parents=True, exist_ok=True)
    for name, table in tables.items():
        table.to_csv(export_dir / f'{name}.csv', index=False)


def load_atlas_inputs(test_only: bool = False) -> tuple[pd.DataFrame, pd.DataFrame]:
    merged, ohlc = sr.load_data(test_only=test_only)
    base = merged[merged['signal'] != 0].copy()
    base['entry_close'] = base['close']
    base['entry_atr14'] = base['atr14']
    return base.reset_index(drop=True), ohlc


def print_report_sections(tables: dict[str, pd.DataFrame]) -> None:
    print('Signal Path Atlas — Discovery/Holdout Split')
    print(tables['split_summary'].to_string(index=False))
    print('\nFeature Variance Screen')
    print(tables['feature_screen'].to_string(index=False))
    print('\nHoldout Replication Verdicts')
    print(tables['holdout_verdicts'].to_string(index=False))
    print('\nExecution Implications')
    print(tables['execution_implications'].to_string(index=False))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--test-only', action='store_true')
    parser.add_argument('--export-dir', type=Path, default=None)
    args = parser.parse_args()

    signals, ohlc = load_atlas_inputs(test_only=args.test_only)
    split = annotate_sample_split(signals)
    tensor = build_path_tensor(split, ohlc)
    conditioned, conditioning_artifacts = build_conditioning_frame(tensor.merge(split, on=['time', 'signal', 'entry_close', 'entry_atr14']))
    discovery = conditioned[conditioned['sample'] == 'discovery'].reset_index(drop=True)
    holdout = conditioned[conditioned['sample'] == 'holdout'].reset_index(drop=True)

    feature_screen, live_numeric = screen_numeric_features(discovery, NUMERIC_FEATURES)
    global_atlas = build_global_atlas(discovery)
    numeric_slices = pd.concat([build_numeric_slices(discovery, feature) for feature in live_numeric], ignore_index=True)
    categorical_slices = build_categorical_slices(discovery, FIXED_COHORT_COLS)
    archetyped, archetype_artifacts = fit_path_archetypes(discovery)
    tree_model, tree_text = fit_explanation_tree(archetyped, live_numeric)
    discovery = archetyped
    holdout_verdicts = build_holdout_verdicts(discovery, holdout, numeric_slices, archetype_artifacts)
    tables = {
        'split_summary': build_split_summary(discovery, holdout),
        'feature_screen': feature_screen,
        'global_first_passage': global_atlas['first_passage'],
        'numeric_slices': numeric_slices,
        'categorical_slices': categorical_slices,
        'archetype_summary': summarize_archetypes(archetyped),
        'holdout_verdicts': holdout_verdicts,
        'execution_implications': build_execution_implications(holdout_verdicts),
    }
    print_report_sections(tables)
    if args.export_dir is not None:
        export_tables(tables, args.export_dir)
```

Also update `API/README.md` to add the new script and commands:

```markdown
| [signal_path_atlas.py](signal_path_atlas.py) | ATR-normalized discovery/holdout path atlas for ML signals | `ml_signals.csv` + OHLC -> stdout tables / optional CSV export | 🔬 |
```

```bash
# Path atlas research
python -m API.signal_path_atlas --test-only
python -m API.signal_path_atlas --test-only --export-dir /tmp/signal_path_atlas
```

- [ ] **Step 4: Run the dedicated atlas test file and the CLI smoke flow**

Run:

```bash
./.venv/bin/python -m pytest tests/test_signal_path_atlas.py -q
./.venv/bin/python -m API.signal_path_atlas --test-only
./.venv/bin/python -m API.signal_path_atlas --test-only --export-dir /tmp/signal_path_atlas
```

Expected:

- `pytest` reports all atlas tests passing
- the CLI prints the split, feature screen, atlas sections, holdout verdicts, and execution implications
- `/tmp/signal_path_atlas` contains the expected CSV tables, including `feature_screen.csv`, `global_first_passage.csv`, `numeric_slices.csv`, `categorical_slices.csv`, `archetype_summary.csv`, and `holdout_verdicts.csv`

## Self-Review Checklist

- [ ] The new tool is standalone in `API/signal_path_atlas.py`; `API/signal_research.py` was not expanded again.
- [ ] Discovery artifacts are frozen before holdout comparison.
- [ ] No task reintroduces `SL/TP` optimization or `PF`-first rule ranking.
- [ ] The holdout verdict logic uses the fixed `>=30` support floor.
- [ ] `API/README.md` documents the new CLI.
- [ ] Verification commands were actually run, not assumed.
