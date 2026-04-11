# Quantile Status Decision Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Определить, может ли `entry_path_v1_quantile` стать parallel execution mode, увеличив N через ослабление фильтра / ensemble, и если да — вынести в production path.

**Architecture:** Два последовательных этапа с жёстким gate. Research Stage расширяет benchmark по двум направлениям (relax filter, multi-seed ensemble) на validation, freeze → test. Если gate пройден, Production Stage строит parallel export path, MQL-переключатель и MT4 parity-check.

**Tech Stack:** Python (pandas, numpy, torch), MQL4, pytest.

**Spec:** `docs/superpowers/specs/2026-04-11-quantile-status-decision-design.md`

---

## File Structure

### Research Stage (новые файлы)

| File | Responsibility |
|------|----------------|
| `ML/benchmark_entry_path_v1_quantile_n_boost.py` | Расширенный benchmark: перебор всех rules + ослабленные пороги + ensemble, validation → freeze → test → gate |
| `ML/entry_path_v1_quantile_ensemble.py` | Агрегация predictions из нескольких seed (mean quantile, majority vote) |
| `tests/test_entry_path_v1_quantile_n_boost.py` | Тесты для расширенного benchmark |
| `tests/test_entry_path_v1_quantile_ensemble.py` | Тесты для ensemble логики |

### Research Stage (модифицируемые файлы)

| File | Изменение |
|------|-----------|
| `ML/benchmark_entry_path_v1_quantile_filter.py` | Добавить параметризуемые пороги для `lb_gt_m` (сейчас hardcoded `> m` где m = median) |

### Production Stage (модифицируемые файлы, только если gate pass)

| File | Изменение |
|------|-----------|
| `API/export_entry_path_v1_quantile_signals.py` | Поддержка ensemble-режима (если winner = ensemble) |
| `MT/MQL4/Include/lib_ML_Signal.mqh` | `MLP_SIGNALS_FILE` → параметр из EA вместо `#define` |
| `MT/MQL4/Experts/$o$imple.mq4` | Новый `extern string ML_SignalFile` |
| `tests/test_export_entry_path_v1_quantile_signals.py` | Тест для ensemble export (если нужен) |

### Artifacts

| Artifact | Описание |
|----------|----------|
| `ML/reports/entry_path_v1_quantile_n_boost_result.json` | Результат gate evaluation |
| `MT/MQL4/Files/ml_signals_quantile.csv` | Production quantile signals (только при gate pass) |
| `docs/reports/2026-04-XX-quantile-status-decision.md` | Stage report |

---

## Task 1: Параметризуемые пороги в benchmark filter

Текущий `build_rule_mask` для `lb_gt_m` использует фиксированный `m = median(lb)`. Нужно добавить возможность задавать `m` как произвольный квантиль lb-распределения (q30, q40, median и т.д.).

**Files:**
- Modify: `ML/benchmark_entry_path_v1_quantile_filter.py:75-84` (`build_rule_mask`), `:176-293` (`run_benchmark`)
- Test: `tests/test_entry_path_v1_quantile_filter.py`

- [ ] **Step 1: Write failing test for parameterized m**

В `tests/test_entry_path_v1_quantile_filter.py` добавить тест:

```python
def test_build_rule_mask_lb_gt_m_uses_custom_threshold():
    """lb_gt_m with m set to a lower quantile should select more rows."""
    frame = pd.DataFrame({
        'baseline_selected': [True, True, True, True],
        'lb': [0.5, 1.0, 1.5, 2.0],
        'width': [1.0, 1.0, 1.0, 1.0],
    })
    mask_median = bench.build_rule_mask(frame, rule='lb_gt_m', m=1.25, w=0.0)
    mask_q30 = bench.build_rule_mask(frame, rule='lb_gt_m', m=0.65, w=0.0)
    assert mask_median.sum() < mask_q30.sum()
```

- [ ] **Step 2: Run test to verify it passes (existing logic already supports custom m)**

Run: `pytest tests/test_entry_path_v1_quantile_filter.py::test_build_rule_mask_lb_gt_m_uses_custom_threshold -v`

Expected: PASS — `build_rule_mask` уже принимает `m` как аргумент. Тест подтверждает, что механизм работает.

- [ ] **Step 3: Add `compute_m_at_quantile` helper in benchmark filter**

В `ML/benchmark_entry_path_v1_quantile_filter.py` добавить после `apply_conformal_correction`:

```python
def compute_m_at_quantile(frame: pd.DataFrame, quantile: float) -> float:
    """Return the lb value at the given quantile of baseline-selected rows."""
    selected = frame.loc[frame['baseline_selected'], 'lb']
    if selected.empty:
        return 0.0
    return float(selected.quantile(quantile))
```

- [ ] **Step 4: Write test for `compute_m_at_quantile`**

```python
def test_compute_m_at_quantile():
    frame = pd.DataFrame({
        'baseline_selected': [True, True, True, True, False],
        'lb': [1.0, 2.0, 3.0, 4.0, 100.0],
    })
    assert bench.compute_m_at_quantile(frame, 0.5) == 2.5
    assert bench.compute_m_at_quantile(frame, 0.0) == 1.0
```

- [ ] **Step 5: Run tests**

Run: `pytest tests/test_entry_path_v1_quantile_filter.py -v`
Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add ML/benchmark_entry_path_v1_quantile_filter.py tests/test_entry_path_v1_quantile_filter.py
git commit -m "feat: add compute_m_at_quantile for parameterized lb thresholds"
```

---

## Task 2: Ensemble predictions module

Агрегация quantile predictions из нескольких seed.

**Files:**
- Create: `ML/entry_path_v1_quantile_ensemble.py`
- Create: `tests/test_entry_path_v1_quantile_ensemble.py`

- [ ] **Step 1: Write failing tests for mean_quantile aggregation**

```python
# tests/test_entry_path_v1_quantile_ensemble.py
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, '.')

from ML import entry_path_v1_quantile_ensemble as ensemble


def _make_seed_frame(q10_values, q90_values):
    return pd.DataFrame({
        'time': ['2024.01.01 00:00', '2024.01.01 01:00'],
        'signal': [1, -1],
        'pred_ret_24_dir_atr': [0.5, 0.3],
        'pred_ret_24_q10': q10_values,
        'pred_ret_24_q90': q90_values,
        'true_ret_24_dir_atr': [1.0, -0.5],
    })


def test_mean_quantile_averages_across_seeds():
    frames = [
        _make_seed_frame([0.2, -0.1], [0.8, 0.3]),
        _make_seed_frame([0.4, -0.3], [1.0, 0.5]),
    ]
    result = ensemble.aggregate_mean_quantile(frames)
    assert abs(result['pred_ret_24_q10'].iloc[0] - 0.3) < 1e-6
    assert abs(result['pred_ret_24_q90'].iloc[0] - 0.9) < 1e-6


def test_majority_vote_requires_quorum():
    # 3 seeds: row 0 selected by all 3, row 1 selected by 1
    masks = [
        pd.Series([True, True]),
        pd.Series([True, False]),
        pd.Series([True, False]),
    ]
    result = ensemble.majority_vote(masks, quorum=3)
    assert result.iloc[0] == True
    assert result.iloc[1] == False

    result2 = ensemble.majority_vote(masks, quorum=2)
    assert result2.iloc[0] == True
    assert result2.iloc[1] == False


def test_aggregate_mean_quantile_preserves_non_quantile_columns():
    frames = [
        _make_seed_frame([0.2, -0.1], [0.8, 0.3]),
        _make_seed_frame([0.4, -0.3], [1.0, 0.5]),
    ]
    result = ensemble.aggregate_mean_quantile(frames)
    assert 'time' in result.columns
    assert 'signal' in result.columns
    assert 'true_ret_24_dir_atr' in result.columns
    assert len(result) == 2
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_entry_path_v1_quantile_ensemble.py -v`
Expected: FAIL (module not found).

- [ ] **Step 3: Implement ensemble module**

```python
# ML/entry_path_v1_quantile_ensemble.py
"""
Aggregate quantile predictions from multiple seed checkpoints.

Two modes:
- mean_quantile: average pred_ret_24_q10/q90 across seeds, keep other columns from first frame.
- majority_vote: signal passes only if >= quorum seeds select it.
"""
from pathlib import Path

import pandas as pd


QUANTILE_COLUMNS = ['pred_ret_24_q10', 'pred_ret_24_q90']


def load_seed_predictions(seed_dir: str | Path, split: str = 'test') -> pd.DataFrame:
    path = Path(seed_dir) / f'entry_path_v1_quantile_{split}_predictions.csv'
    return pd.read_csv(path, sep=';')


def aggregate_mean_quantile(frames: list[pd.DataFrame]) -> pd.DataFrame:
    base = frames[0].copy()
    for col in QUANTILE_COLUMNS:
        stacked = pd.concat([f[col] for f in frames], axis=1)
        base[col] = stacked.mean(axis=1)
    return base


def majority_vote(masks: list[pd.Series], quorum: int = 3) -> pd.Series:
    stacked = pd.concat(masks, axis=1)
    return stacked.sum(axis=1) >= quorum
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_entry_path_v1_quantile_ensemble.py -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add ML/entry_path_v1_quantile_ensemble.py tests/test_entry_path_v1_quantile_ensemble.py
git commit -m "feat: add quantile ensemble module (mean_quantile + majority_vote)"
```

---

## Task 3: N-boost benchmark script

Расширенный benchmark, который перебирает ослабленные пороги и ensemble, применяет gate.

**Files:**
- Create: `ML/benchmark_entry_path_v1_quantile_n_boost.py`
- Create: `tests/test_entry_path_v1_quantile_n_boost.py`

- [ ] **Step 1: Write failing test for relax_filter_sweep**

```python
# tests/test_entry_path_v1_quantile_n_boost.py
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, '.')

from ML import benchmark_entry_path_v1_quantile_n_boost as boost


def _write_minimal_seed(root, seed, *, n_rows=20, candidate='lb_gt_m'):
    """Create minimal seed artifacts for testing."""
    seed_dir = root / f'seed_{seed:03d}'
    seed_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for i in range(n_rows):
        rows.append({
            'time': f'2024.01.{1 + i // 24:02d} {i % 24:02d}:00',
            'signal': 1 if i % 2 == 0 else -1,
            'pred_ret_24_dir_atr': 0.5 + i * 0.01,
            'pred_ret_24_q10': 0.1 + i * 0.005,
            'pred_ret_24_q90': 0.8 + i * 0.005,
            'true_ret_24_dir_atr': 0.3 if i % 3 != 0 else -0.2,
        })
    frame = pd.DataFrame(rows)

    for split in ['validation', 'test']:
        frame.to_csv(seed_dir / f'entry_path_v1_quantile_{split}_predictions.csv', sep=';', index=False)

    result_json = {
        'best_val_score': 0.20,
        'val_metrics': {'val_score': 0.20},
    }
    (seed_dir / 'transformer_entry_path_v1_quantile_result.json').write_text(
        json.dumps(result_json), encoding='utf-8',
    )

    rule_json = {
        'winner': {'candidate': candidate, 'rule': candidate, 'm': 0.2, 'w': 5.0,
                    'trades': 15, 'pf': 3.0, 'win_rate': 0.7, 'mean_pnl_atr': 0.5,
                    'coverage': 0.5, 'median_interval_width': 7.0, 'gross_profit': 4.5, 'gross_loss': 1.5},
        'frozen_winner': {'candidate': candidate, 'rule': candidate, 'm': 0.2, 'w': 5.0,
                          'trades': 15, 'pf': 3.0, 'win_rate': 0.7, 'mean_pnl_atr': 0.5,
                          'coverage': 0.5, 'median_interval_width': 7.0, 'gross_profit': 4.5, 'gross_loss': 1.5},
        'baseline_threshold': 0.4,
        'correction': 0.1,
        'sequential_summary': {'trades': 10, 'pf': 2.5, 'win_rate': 0.6, 'mean_pnl_atr': 0.4, 'coverage': 0.4},
        'sequential_hold_bars': 24,
        'validation_csv': str(seed_dir / 'entry_path_v1_quantile_validation_predictions.csv'),
        'test_csv': str(seed_dir / 'entry_path_v1_quantile_test_predictions.csv'),
    }
    (seed_dir / 'entry_path_v1_quantile_filter_selected_rule.json').write_text(
        json.dumps(rule_json), encoding='utf-8',
    )
    return seed_dir


def test_evaluate_gate_pass():
    result = boost.evaluate_gate(n_trades=35, pf=2.5, negative_year_slices=0, same_winner_ratio=4/5)
    assert result['verdict'] == 'gate_pass'


def test_evaluate_gate_fail_low_n():
    result = boost.evaluate_gate(n_trades=25, pf=3.0, negative_year_slices=0, same_winner_ratio=4/5)
    assert result['verdict'] == 'gate_fail'


def test_evaluate_gate_fail_low_pf():
    result = boost.evaluate_gate(n_trades=40, pf=1.5, negative_year_slices=0, same_winner_ratio=4/5)
    assert result['verdict'] == 'gate_fail'


def test_evaluate_gate_fail_negative_years():
    result = boost.evaluate_gate(n_trades=40, pf=3.0, negative_year_slices=1, same_winner_ratio=4/5)
    assert result['verdict'] == 'gate_fail'
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_entry_path_v1_quantile_n_boost.py -v`
Expected: FAIL (module not found).

- [ ] **Step 3: Implement `evaluate_gate` function**

```python
# ML/benchmark_entry_path_v1_quantile_n_boost.py (начало файла)
"""
N-boost benchmark for entry_path_v1_quantile.

Tries two approaches to increase trade count:
1. Relax filter: sweep lb quantile thresholds on validation.
2. Multi-seed ensemble: aggregate predictions across seeds.

Applies go/no-go gate to frozen test result.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from ML.benchmark_entry_path_v1_quantile_filter import (
    apply_conformal_correction,
    attach_baseline_score,
    build_rule_mask,
    compute_conformal_correction,
    compute_m_at_quantile,
    compute_pf,
    load_baseline_rule,
    load_prediction_frame,
    pick_winner,
    run_sequential_check,
    summarize_rule,
)
from ML.entry_path_v1_quantile_ensemble import (
    aggregate_mean_quantile,
    load_seed_predictions,
    majority_vote,
)
from ML.entry_path_v1_quantile_robustness import (
    build_yearly_summary,
)


GATE_MIN_TRADES = 30
GATE_MIN_PF = 2.0
GATE_MIN_YEAR_TRADES = 3
GATE_MIN_SAME_WINNER_RATIO = 0.8


def evaluate_gate(
    n_trades: int,
    pf: float,
    negative_year_slices: int,
    same_winner_ratio: float,
) -> dict:
    reasons = []
    if n_trades < GATE_MIN_TRADES:
        reasons.append(f'n_trades={n_trades} < {GATE_MIN_TRADES}')
    if pf < GATE_MIN_PF:
        reasons.append(f'pf={pf:.2f} < {GATE_MIN_PF}')
    if negative_year_slices > 0:
        reasons.append(f'negative_year_slices={negative_year_slices} > 0')
    if same_winner_ratio < GATE_MIN_SAME_WINNER_RATIO:
        reasons.append(f'same_winner_ratio={same_winner_ratio:.2f} < {GATE_MIN_SAME_WINNER_RATIO}')

    return {
        'verdict': 'gate_pass' if not reasons else 'gate_fail',
        'n_trades': n_trades,
        'pf': pf,
        'negative_year_slices': negative_year_slices,
        'same_winner_ratio': same_winner_ratio,
        'reasons': reasons,
    }
```

- [ ] **Step 4: Run gate tests to verify they pass**

Run: `pytest tests/test_entry_path_v1_quantile_n_boost.py -v -k gate`
Expected: all 4 gate tests PASS.

- [ ] **Step 5: Implement `run_relax_sweep` — sweep quantile thresholds on validation**

Добавить в `ML/benchmark_entry_path_v1_quantile_n_boost.py`:

```python
QUANTILE_SWEEP = [0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50]
RULES_TO_SWEEP = ['lb_gt_m', 'lb_gt_0', 'lb_gt_m_width_le_w']


def run_relax_sweep(
    validation_frame: pd.DataFrame,
    baseline_validation: pd.DataFrame,
    baseline_threshold: float,
    alpha: float = 0.10,
    min_trades: int = 10,
) -> pd.DataFrame:
    validation = attach_baseline_score(validation_frame, baseline_validation)
    validation['baseline_selected'] = (
        (validation['signal'].to_numpy() != 0)
        & (validation['baseline_score'].to_numpy(dtype=np.float64) >= baseline_threshold)
    )

    selected = validation.loc[validation['baseline_selected']].copy()
    correction = compute_conformal_correction(
        selected['true_ret_24_dir_atr'].to_numpy(dtype=np.float64),
        selected['pred_ret_24_q10'].to_numpy(dtype=np.float64),
        selected['pred_ret_24_q90'].to_numpy(dtype=np.float64),
        alpha=alpha,
    )
    validation = apply_conformal_correction(validation, correction)

    rows = []
    for q in QUANTILE_SWEEP:
        m = compute_m_at_quantile(validation, q)
        w = float(validation.loc[validation['baseline_selected'], 'width'].median()) if validation['baseline_selected'].any() else 0.0
        for rule in RULES_TO_SWEEP:
            candidate = f'{rule}_q{int(q*100):02d}'
            row = summarize_rule(validation, candidate=candidate, rule=rule, m=m, w=w)
            row['quantile'] = q
            row['correction'] = correction
            rows.append(row)

    # Also include original median (q50) baseline rule
    rows.append({
        **summarize_rule(validation, candidate='baseline', rule='baseline', m=0.0, w=0.0),
        'quantile': None,
        'correction': correction,
    })

    return pd.DataFrame(rows)
```

- [ ] **Step 6: Write test for `run_relax_sweep`**

```python
def test_relax_sweep_returns_multiple_candidates(tmp_path):
    n = 40
    frame = pd.DataFrame({
        'time': [f'2024.01.{1 + i // 24:02d} {i % 24:02d}:00' for i in range(n)],
        'signal': [1 if i % 2 == 0 else -1 for i in range(n)],
        'pred_ret_24_dir_atr': [0.5 + i * 0.01 for i in range(n)],
        'pred_ret_24_q10': [0.1 + i * 0.005 for i in range(n)],
        'pred_ret_24_q90': [0.8 + i * 0.005 for i in range(n)],
        'true_ret_24_dir_atr': [0.3 if i % 3 != 0 else -0.2 for i in range(n)],
    })
    baseline = frame[['time', 'signal', 'pred_ret_24_dir_atr']].copy()

    result = boost.run_relax_sweep(frame, baseline, baseline_threshold=0.4)
    assert len(result) > len(boost.QUANTILE_SWEEP)  # multiple rules * quantiles + baseline
    assert 'quantile' in result.columns
    assert any(result['candidate'].str.contains('q20'))
```

- [ ] **Step 7: Run tests**

Run: `pytest tests/test_entry_path_v1_quantile_n_boost.py -v`
Expected: all PASS.

- [ ] **Step 8: Implement `run_ensemble_benchmark` — aggregate seed predictions and benchmark**

Добавить в `ML/benchmark_entry_path_v1_quantile_n_boost.py`:

```python
def run_ensemble_benchmark(
    seed_dirs: list[str | Path],
    split: str,
    baseline_frame: pd.DataFrame,
    baseline_threshold: float,
    alpha: float = 0.10,
    min_trades: int = 10,
) -> pd.DataFrame:
    frames = [load_seed_predictions(sd, split=split) for sd in seed_dirs]

    # Mean quantile
    mean_frame = aggregate_mean_quantile(frames)
    mean_validation = attach_baseline_score(mean_frame, baseline_frame)
    mean_validation['baseline_selected'] = (
        (mean_validation['signal'].to_numpy() != 0)
        & (mean_validation['baseline_score'].to_numpy(dtype=np.float64) >= baseline_threshold)
    )
    selected = mean_validation.loc[mean_validation['baseline_selected']].copy()
    correction = compute_conformal_correction(
        selected['true_ret_24_dir_atr'].to_numpy(dtype=np.float64),
        selected['pred_ret_24_q10'].to_numpy(dtype=np.float64),
        selected['pred_ret_24_q90'].to_numpy(dtype=np.float64),
        alpha=alpha,
    )
    mean_validation = apply_conformal_correction(mean_validation, correction)
    m = compute_m_at_quantile(mean_validation, 0.5)
    w = float(mean_validation.loc[mean_validation['baseline_selected'], 'width'].median()) if mean_validation['baseline_selected'].any() else 0.0

    rows = []
    for rule in RULES_TO_SWEEP:
        candidate = f'ensemble_mean_{rule}'
        row = summarize_rule(mean_validation, candidate=candidate, rule=rule, m=m, w=w)
        row['method'] = 'mean_quantile'
        row['correction'] = correction
        rows.append(row)

    # Majority vote: per-seed masks, then quorum filter
    from ML.benchmark_entry_path_v1_quantile_filter import (
        apply_conformal_correction as _apc,
        attach_baseline_score as _abs,
        compute_conformal_correction as _ccc,
    )
    for quorum in [3, 4]:
        per_seed_masks = []
        for f in frames:
            sv = _abs(f, baseline_frame)
            sv['baseline_selected'] = (
                (sv['signal'].to_numpy() != 0)
                & (sv['baseline_score'].to_numpy(dtype=np.float64) >= baseline_threshold)
            )
            sel = sv.loc[sv['baseline_selected']].copy()
            c = _ccc(
                sel['true_ret_24_dir_atr'].to_numpy(dtype=np.float64),
                sel['pred_ret_24_q10'].to_numpy(dtype=np.float64),
                sel['pred_ret_24_q90'].to_numpy(dtype=np.float64),
                alpha=alpha,
            )
            sv = _apc(sv, c)
            sm = compute_m_at_quantile(sv, 0.5)
            per_seed_masks.append(build_rule_mask(sv, rule='lb_gt_m', m=sm, w=0.0))

        vote_mask = majority_vote(per_seed_masks, quorum=quorum)
        # Use mean_validation frame for PnL evaluation
        mean_validation_copy = mean_validation.copy()
        pnl = mean_validation_copy.loc[vote_mask, 'true_ret_24_dir_atr'].to_numpy(dtype=np.float64)
        trades = int(vote_mask.sum())
        pf = compute_pf(pnl) if trades > 0 else 0.0
        rows.append({
            'candidate': f'ensemble_vote_q{quorum}',
            'rule': 'majority_vote',
            'method': 'majority_vote',
            'trades': trades,
            'pf': pf,
            'win_rate': float((pnl > 0).mean()) if trades > 0 else 0.0,
            'mean_pnl_atr': float(pnl.mean()) if trades > 0 else 0.0,
            'm': 0.0,
            'w': 0.0,
            'coverage': 0.0,
            'median_interval_width': 0.0,
            'gross_profit': float(pnl[pnl > 0].sum()) if trades > 0 else 0.0,
            'gross_loss': float(-pnl[pnl < 0].sum()) if trades > 0 else 0.0,
            'correction': correction,
        })

    return pd.DataFrame(rows)
```

- [ ] **Step 9: Write test for `run_ensemble_benchmark`**

```python
def test_ensemble_benchmark_produces_rows(tmp_path):
    seeds = [7, 42]
    for s in seeds:
        _write_minimal_seed(tmp_path, s, n_rows=20)

    baseline_path = tmp_path / 'seed_007' / 'entry_path_v1_quantile_validation_predictions.csv'
    baseline = pd.read_csv(baseline_path, sep=';')[['time', 'signal', 'pred_ret_24_dir_atr']]
    seed_dirs = [tmp_path / f'seed_{s:03d}' for s in seeds]

    result = boost.run_ensemble_benchmark(
        seed_dirs=seed_dirs,
        split='validation',
        baseline_frame=baseline,
        baseline_threshold=0.4,
    )
    assert len(result) > 0
    assert 'method' in result.columns
    assert all(result['method'] == 'mean_quantile')
```

- [ ] **Step 10: Run all tests**

Run: `pytest tests/test_entry_path_v1_quantile_n_boost.py tests/test_entry_path_v1_quantile_ensemble.py -v`
Expected: all PASS.

- [ ] **Step 11: Commit**

```bash
git add ML/benchmark_entry_path_v1_quantile_n_boost.py tests/test_entry_path_v1_quantile_n_boost.py
git commit -m "feat: add n-boost benchmark with relax sweep, ensemble, and gate evaluation"
```

---

## Task 4: Full benchmark orchestration with gate

Добавить `run_full_benchmark` — оркестрация relax → ensemble → gate, с CLI.

**Files:**
- Modify: `ML/benchmark_entry_path_v1_quantile_n_boost.py`
- Modify: `tests/test_entry_path_v1_quantile_n_boost.py`

- [ ] **Step 1: Write failing test for full orchestration**

```python
def test_run_full_benchmark_produces_gate_result(tmp_path):
    seeds = [7, 17, 42]
    for s in seeds:
        _write_minimal_seed(tmp_path, s, n_rows=40)

    baseline_rule = {
        'winner': {'candidate': 'A', 'score_threshold': 0.4, 'pf': 2.0},
        'validation_csv': str(tmp_path / 'seed_007' / 'entry_path_v1_quantile_validation_predictions.csv'),
        'test_csv': str(tmp_path / 'seed_007' / 'entry_path_v1_quantile_test_predictions.csv'),
        'sequential_summary': {'pf': 1.5},
        'sequential_hold_bars': 24,
    }
    baseline_path = tmp_path / 'baseline_rule.json'
    baseline_path.write_text(json.dumps(baseline_rule), encoding='utf-8')

    result = boost.run_full_benchmark(
        root_dir=tmp_path,
        seeds=[7, 17, 42],
        baseline_rule=baseline_path,
        output_dir=tmp_path / 'output',
    )
    assert 'gate' in result
    assert result['gate']['verdict'] in ('gate_pass', 'gate_fail')
    assert 'best_candidate' in result
    assert (tmp_path / 'output' / 'n_boost_result.json').exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_entry_path_v1_quantile_n_boost.py::test_run_full_benchmark_produces_gate_result -v`
Expected: FAIL.

- [ ] **Step 3: Implement `run_full_benchmark`**

Добавить в `ML/benchmark_entry_path_v1_quantile_n_boost.py`:

```python
def count_negative_year_slices_from_trades(
    test_frame: pd.DataFrame,
    selected_mask: pd.Series,
    min_year_trades: int = GATE_MIN_YEAR_TRADES,
) -> int:
    """Count negative year slices on the best candidate's frozen test trades (not per-seed)."""
    selected = test_frame.loc[selected_mask].copy()
    if selected.empty or 'time' not in selected.columns:
        return 0
    selected['time'] = pd.to_datetime(selected['time'], format='%Y.%m.%d %H:%M', errors='coerce')
    selected['year'] = selected['time'].dt.year
    total = 0
    for _, group in selected.groupby('year'):
        if len(group) < min_year_trades:
            continue
        pnl = group['true_ret_24_dir_atr'].to_numpy(dtype=np.float64)
        if pnl.sum() < 0:
            total += 1
    return total


def run_full_benchmark(
    root_dir: str | Path,
    seeds: list[int],
    baseline_rule: str | Path,
    output_dir: str | Path,
    alpha: float = 0.10,
    min_trades: int = 10,
) -> dict:
    root = Path(root_dir)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    baseline_data = load_baseline_rule(baseline_rule)
    baseline_threshold = float(baseline_data['winner'].get('score_threshold', 0.0))
    baseline_validation = load_prediction_frame(baseline_data['validation_csv'])
    baseline_test = load_prediction_frame(baseline_data['test_csv'])
    hold_bars = int(baseline_data.get('sequential_hold_bars', 24))

    seed_dirs = [root / f'seed_{s:03d}' for s in seeds]
    primary_seed_dir = seed_dirs[0]

    # --- Step 1: Relax filter sweep on validation (primary seed) ---
    val_frame = load_seed_predictions(primary_seed_dir, split='validation')
    relax_table = run_relax_sweep(val_frame, baseline_validation, baseline_threshold, alpha, min_trades)

    # --- Step 2: Ensemble sweep on validation ---
    ensemble_table = run_ensemble_benchmark(seed_dirs, 'validation', baseline_validation, baseline_threshold, alpha, min_trades)

    # --- Combine and pick best on validation ---
    combined = pd.concat([relax_table, ensemble_table], ignore_index=True)
    combined_path = out / 'n_boost_validation_sweep.csv'
    combined.to_csv(combined_path, sep=';', index=False)

    best = pick_winner(combined, min_trades=min_trades).to_dict()

    # --- Frozen test ---
    is_ensemble = str(best.get('method', '')) == 'mean_quantile'

    if is_ensemble:
        test_frame = aggregate_mean_quantile([load_seed_predictions(sd, split='test') for sd in seed_dirs])
    else:
        test_frame = load_seed_predictions(primary_seed_dir, split='test')

    test = attach_baseline_score(test_frame, baseline_test)
    test['baseline_selected'] = (
        (test['signal'].to_numpy() != 0)
        & (test['baseline_score'].to_numpy(dtype=np.float64) >= baseline_threshold)
    )
    correction = float(best.get('correction', 0.0))
    test = apply_conformal_correction(test, correction)

    m = float(best.get('m', 0.0))
    w = float(best.get('w', 0.0))
    rule = best.get('rule', 'baseline')

    frozen_test = summarize_rule(test, candidate=best['candidate'], rule=rule, m=m, w=w)
    frozen_mask = build_rule_mask(test, rule=rule, m=m, w=w)
    sequential = run_sequential_check(test, frozen_mask, hold_bars=hold_bars)

    # --- Multi-seed stability (for relax variant) ---
    if not is_ensemble:
        same_count = 0
        for sd in seed_dirs:
            sd_val = load_seed_predictions(sd, split='validation')
            sd_table = run_relax_sweep(sd_val, baseline_validation, baseline_threshold, alpha, min_trades)
            sd_best = pick_winner(sd_table, min_trades=min_trades)
            if sd_best['candidate'] == best['candidate']:
                same_count += 1
        same_winner_ratio = same_count / len(seeds)
    else:
        same_winner_ratio = 1.0  # ensemble is deterministic

    # --- Negative year slices (on best candidate's frozen test trades) ---
    neg_year_slices = count_negative_year_slices_from_trades(test, frozen_mask)

    # --- Gate ---
    gate = evaluate_gate(
        n_trades=int(frozen_test['trades']),
        pf=float(frozen_test['pf']),
        negative_year_slices=neg_year_slices,
        same_winner_ratio=same_winner_ratio,
    )

    payload = {
        'best_candidate': best,
        'frozen_test': frozen_test,
        'sequential': sequential,
        'gate': gate,
        'is_ensemble': is_ensemble,
        'seeds': seeds,
        'sweep_path': str(combined_path),
    }

    result_path = out / 'n_boost_result.json'
    result_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding='utf-8')

    return payload


def parse_args():
    parser = argparse.ArgumentParser(description='N-boost benchmark for entry_path_v1_quantile.')
    parser.add_argument('--root-dir', required=True)
    parser.add_argument('--seeds', type=int, nargs='+', required=True)
    parser.add_argument('--baseline-rule', required=True)
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--alpha', type=float, default=0.10)
    parser.add_argument('--min-trades', type=int, default=10)
    return parser.parse_args()


def main():
    args = parse_args()
    payload = run_full_benchmark(
        root_dir=args.root_dir,
        seeds=args.seeds,
        baseline_rule=args.baseline_rule,
        output_dir=args.output_dir,
        alpha=args.alpha,
        min_trades=args.min_trades,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return payload


if __name__ == '__main__':
    main()
```

- [ ] **Step 4: Run full test suite**

Run: `pytest tests/test_entry_path_v1_quantile_n_boost.py tests/test_entry_path_v1_quantile_ensemble.py tests/test_entry_path_v1_quantile_filter.py -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add ML/benchmark_entry_path_v1_quantile_n_boost.py tests/test_entry_path_v1_quantile_n_boost.py
git commit -m "feat: add full n-boost orchestration with gate evaluation and CLI"
```

---

## Task 5: Run research — execute benchmark on real data

**Checkpoint: требует ревью перед началом.** Это первый запуск на реальных данных.

**Files:**
- Existing: `ML/reports/entry_path_v1_quantile_robustness/seed_{007,017,042,077,123}/`
- Existing: `ML/reports/entry_path_trade_filter_selected_rule.json`
- Output: `ML/reports/entry_path_v1_quantile_n_boost_result.json`

- [ ] **Step 1: Verify seed artifacts exist**

Run:
```bash
ls ML/reports/entry_path_v1_quantile_robustness/seed_*/entry_path_v1_quantile_test_predictions.csv
```
Expected: 5 files for seeds 007, 017, 042, 077, 123.

- [ ] **Step 2: Run n-boost benchmark**

Run:
```bash
source .venv/bin/activate && python -m ML.benchmark_entry_path_v1_quantile_n_boost \
  --root-dir ML/reports/entry_path_v1_quantile_robustness \
  --seeds 7 17 42 77 123 \
  --baseline-rule ML/reports/entry_path_trade_filter_selected_rule.json \
  --output-dir ML/reports
```

- [ ] **Step 3: Evaluate gate result**

Read `ML/reports/n_boost_result.json`. Check:
- `gate.verdict` == `gate_pass` or `gate_fail`
- `frozen_test.trades` >= 30?
- `frozen_test.pf` > 2.0?
- `gate.negative_year_slices` == 0?

- [ ] **Step 4: Decision point**

- If `gate_pass` → continue to Task 6 (Production Stage).
- If `gate_fail` → write stage report with verdict "not ready", commit, and stop.

- [ ] **Step 5: Commit research artifacts**

```bash
git add ML/reports/n_boost_result.json ML/reports/n_boost_validation_sweep.csv
git commit -m "research: entry_path_v1_quantile n-boost benchmark result"
```

---

## Task 6: Production export path (ONLY IF GATE PASS)

Адаптировать exporter под winning вариант.

**Files:**
- Modify: `API/export_entry_path_v1_quantile_signals.py`
- Modify: `tests/test_export_entry_path_v1_quantile_signals.py`

- [ ] **Step 1: Determine what changes are needed**

Read `ML/reports/n_boost_result.json`:
- If `is_ensemble == true` → exporter needs to load multiple seed predictions and aggregate.
- If `is_ensemble == false` → exporter needs to use the relaxed `m` value from the winning candidate instead of the one in seed's `selected_rule.json`.

- [ ] **Step 2: Write failing test for the new export mode**

Конкретный тест зависит от результата Task 5. Шаблон:

```python
def test_export_with_n_boost_rule(tmp_path):
    """Export uses n_boost winner rule instead of per-seed rule."""
    # Setup: create seed artifacts + n_boost_result.json
    # Act: call export_signals with n_boost_rule
    # Assert: output CSV has expected number of active signals
    pass  # fill based on Task 5 result
```

- [ ] **Step 3: Implement changes in exporter**

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_export_entry_path_v1_quantile_signals.py -v`
Expected: PASS.

- [ ] **Step 5: Generate production CSV**

Run:
```bash
source .venv/bin/activate && python -m API.export_entry_path_v1_quantile_signals \
  <args based on winner> \
  --output MT/MQL4/Files/ml_signals_quantile.csv \
  --copy-to-mt4
```

- [ ] **Step 6: Commit**

```bash
git add API/export_entry_path_v1_quantile_signals.py tests/test_export_entry_path_v1_quantile_signals.py
git commit -m "feat: adapt quantile exporter for n-boost winner"
```

---

## Task 7: MQL integration (ONLY IF GATE PASS)

Параметр `ML_SignalFile` в EA для переключения между CSV.

**Files:**
- Modify: `MT/MQL4/Experts/$o$imple.mq4:41` (add `extern string`)
- Modify: `MT/MQL4/Include/lib_ML_Signal.mqh:19,63` (use parameter instead of `#define`)

- [ ] **Step 1: Add `extern string ML_SignalFile` to EA**

В `MT/MQL4/Experts/$o$imple.mq4` после строки 75 (`ML_UseScoreFilter`):

```mql4
extern string ML_SignalFile    = "ml_signals.csv"; // ML_SignalFile: CSV файл с сигналами
```

- [ ] **Step 2: Pass `ML_SignalFile` to `MLP_INIT`**

В `MT/MQL4/Include/lib_ML_Signal.mqh`:

Заменить `#define MLP_SIGNALS_FILE "ml_signals.csv"` на:

```mql4
// MLP_SIGNALS_FILE is now set by extern ML_SignalFile in EA
```

Изменить `MLP_INIT()` сигнатуру:

```mql4
bool MLP_INIT(string signalFile = "ml_signals.csv") {
   int handle = FileOpen(signalFile, FILE_READ | FILE_CSV | FILE_ANSI, ';');
```

Обновить все вызовы Print, заменив `MLP_SIGNALS_FILE` на `signalFile`.

- [ ] **Step 3: Update `MLP_INIT` call in MAIN.mqh**

Найти вызов `MLP_INIT()` и заменить на `MLP_INIT(ML_SignalFile)`.

- [ ] **Step 4: Verify compilation**

Компиляция MQL4 проверяется в MetaEditor (не автоматизируемо в CI). Записать инструкцию:
> Открыть `$o$imple.mq4` в MetaEditor, нажать Compile. Ожидается: 0 errors.

- [ ] **Step 5: Commit**

```bash
git add MT/MQL4/Experts/\$o\$imple.mq4 MT/MQL4/Include/lib_ML_Signal.mqh MT/MQL4/Include/MAIN.mqh
git commit -m "feat: add ML_SignalFile parameter for parallel quantile execution"
```

---

## Task 8: MT4 parity-check (ONLY IF GATE PASS)

**Files:**
- Input: `MT/MQL4/Files/ml_signals_quantile.csv`
- Output: `ML/reports/entry_path_v1_quantile_n_boost_mt4_reconciliation.csv`

- [ ] **Step 1: Configure MT4 tester**

В `MT/tester/$o$imple.ini` установить:
```
ML_SignalFile=ml_signals_quantile.csv
ML_HoldBars=24
ML_AllowReversal=0
ML_UseScoreFilter=0
```

- [ ] **Step 2: Run MT4 tester**

Ручной запуск в MetaTrader. Сохранить лог в `MT/tester/logs/`.

- [ ] **Step 3: Reconciliation**

Run:
```bash
source .venv/bin/activate && python -m statistics.signal_tracer --batch --top 10 --csv-out ML/reports/entry_path_v1_quantile_n_boost_mt4_reconciliation.csv
```

- [ ] **Step 4: Verify acceptance criteria**

- `Opened == N_expected` (from n_boost_result.json frozen_test.trades, adjusted for position blocking)
- `Position blocked` — объяснимо
- No unexplained discrepancies

- [ ] **Step 5: Commit**

```bash
git add ML/reports/entry_path_v1_quantile_n_boost_mt4_reconciliation.csv
git commit -m "research: entry_path_v1_quantile n-boost MT4 parity confirmed"
```

---

## Task 9: Stage report and docs

**Files:**
- Create: `docs/reports/2026-04-XX-quantile-status-decision.md`
- Modify: `CONTEXT_HANDOFF.md`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Write stage report**

Содержание зависит от verdict:

**Gate pass:**
- Research results: best candidate, N, PF, method (relax/ensemble)
- Gate criteria: all passed
- MT4 parity: confirmed
- Decision: quantile = parallel execution mode

**Gate fail:**
- Research results: best candidate, why gate failed
- Decision: quantile remains research-only

- [ ] **Step 2: Update `CONTEXT_HANDOFF.md`**

Обновить Current Stage, Next Step, Open Risks.

- [ ] **Step 3: Update `CHANGELOG.md`**

Добавить запись по формату: `## [2026-04-XX] — ...`

- [ ] **Step 4: Wiki ingest**

Обновить `wiki/research/execution-tracks.md` с результатами n-boost.

- [ ] **Step 5: Commit**

```bash
git add docs/reports/ CONTEXT_HANDOFF.md CHANGELOG.md wiki/
git commit -m "docs: quantile status decision stage report"
```
