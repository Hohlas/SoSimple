# Entry Path Trade Filter v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Добавить первый слой `торговать / не торговать` поверх текущего `entry_path_v1`, честно сравнить простой фильтр `A` и составной фильтр `B`, выбрать победителя только на `validation` и проверить его на `test`.

**Architecture:** Новый слой строится не в обучении, а поверх уже готовых предсказаний `entry_path_v1` из `ML/reports/entry_path_v1_validation_predictions.csv` и `ML/reports/entry_path_test_predictions.csv`. Общая логика выносится в отдельный модуль: построение score, percentile-нормализация на `validation`, подбор порога под coverage около `70%`, расчёт качества по сигналам, проверка устойчивости по времени и вторичная последовательная проверка с фиксированным удержанием `24` бара. Поверх этого добавляется отдельный benchmark-скрипт, который пишет таблицы сравнения, замороженное правило и итоговый markdown-отчёт.

**Tech Stack:** Python 3.11+, pandas, numpy, pytest, JSON, markdown reports

---

## File Map

- `ML/entry_path_trade_filter.py`
  Назначение: чистые helper-функции для фильтров `A/B`, percentile-нормализации, расчёта quality-метрик, устойчивости по времени, вторичной последовательной проверки и сборки markdown-отчёта.
- `ML/benchmark_entry_path_trade_filter.py`
  Назначение: CLI-обвязка поверх helper-модуля; читает `validation/test` CSV предсказаний, строит benchmark, выбирает победителя на `validation`, замораживает правило и пишет артефакты в `ML/reports/`.
- `tests/test_entry_path_trade_filter.py`
  Назначение: unit- и smoke-тесты новой логики score, percentile-нормализации, выбора порога, проверки устойчивости, последовательной проверки и markdown-отчёта.
- `ML/reports/entry_path_trade_filter_validation_summary.csv`
  Назначение: таблица всех проверенных срезов для кандидатов `A/B` на `validation`.
- `ML/reports/entry_path_trade_filter_test_summary.csv`
  Назначение: таблица итоговой проверки замороженного победителя на `test`.
- `ML/reports/entry_path_trade_filter_selected_rule.json`
  Назначение: замороженное правило победителя для дальнейших этапов.
- `ML/reports/entry_path_trade_filter_report.md`
  Назначение: читаемый итог сравнения `A/B`, выбора победителя и secondary-check.

---

### Task 1: Вынести score и percentile-нормализацию в отдельный модуль

**Files:**
- Create: `ML/entry_path_trade_filter.py`
- Create: `tests/test_entry_path_trade_filter.py`

- [ ] **Step 1: Write the failing tests for фильтр A, percentile rank и составной score B**

```python
# tests/test_entry_path_trade_filter.py
import numpy as np
import pandas as pd

from ML import entry_path_trade_filter as etf


def test_candidate_a_uses_pred_ret_24_dir_atr():
    frame = pd.DataFrame({
        'pred_ret_24_dir_atr': [0.4, -0.2, 0.1],
    })

    score = etf.build_candidate_a_score(frame)

    assert np.allclose(score, np.array([0.4, -0.2, 0.1]))


def test_percentile_rank_uses_only_validation_distribution():
    fit = etf.fit_percentile_rank(np.array([10.0, 20.0, 30.0, 40.0]))
    transformed = etf.apply_percentile_rank(np.array([5.0, 20.0, 35.0, 50.0]), fit)

    assert np.allclose(transformed, np.array([0.0, 0.5, 0.75, 1.0]))


def test_candidate_b_score_uses_fixed_weights():
    normalized = pd.DataFrame({
        'ret24': [0.9, 0.1],
        'ret12': [0.8, 0.2],
        'edge12': [0.7, 0.3],
        'edge24': [0.6, 0.4],
        'path6': [0.5, 0.5],
    })

    score = etf.compose_candidate_b_score(normalized)

    assert np.allclose(score, np.array([0.79, 0.21]))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_entry_path_trade_filter.py -q`
Expected: FAIL with `ImportError` or `AttributeError` for missing `entry_path_trade_filter` helpers.

- [ ] **Step 3: Implement score helpers and percentile mapping**

```python
# ML/entry_path_trade_filter.py
from __future__ import annotations

import numpy as np
import pandas as pd


CANDIDATE_B_WEIGHTS = {
    'ret24': 0.45,
    'ret12': 0.20,
    'edge12': 0.15,
    'edge24': 0.10,
    'path6': 0.10,
}


def build_candidate_a_score(frame: pd.DataFrame) -> np.ndarray:
    return frame['pred_ret_24_dir_atr'].to_numpy(dtype=np.float64)


def build_candidate_b_components(frame: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({
        'ret24': frame['pred_ret_24_dir_atr'].to_numpy(dtype=np.float64),
        'ret12': frame['pred_ret_12_dir_atr'].to_numpy(dtype=np.float64),
        'edge12': (
            frame['pred_fav_12_atr'].to_numpy(dtype=np.float64) -
            frame['pred_adv_12_atr'].to_numpy(dtype=np.float64)
        ),
        'edge24': (
            frame['pred_fav_24_atr'].to_numpy(dtype=np.float64) -
            frame['pred_adv_24_atr'].to_numpy(dtype=np.float64)
        ),
        'path6': (
            frame['pred_path_6_prob_pos'].to_numpy(dtype=np.float64) -
            frame['pred_path_6_prob_neg'].to_numpy(dtype=np.float64)
        ),
    })


def fit_percentile_rank(values: np.ndarray) -> dict[str, np.ndarray]:
    clean = np.asarray(values, dtype=np.float64)
    return {'sorted_values': np.sort(clean)}


def apply_percentile_rank(values: np.ndarray, fit: dict[str, np.ndarray]) -> np.ndarray:
    sorted_values = fit['sorted_values']
    if len(sorted_values) == 0:
        return np.zeros(len(values), dtype=np.float64)
    positions = np.searchsorted(sorted_values, np.asarray(values, dtype=np.float64), side='right')
    return positions / float(len(sorted_values))


def compose_candidate_b_score(normalized: pd.DataFrame) -> np.ndarray:
    score = np.zeros(len(normalized), dtype=np.float64)
    for key, weight in CANDIDATE_B_WEIGHTS.items():
        score += weight * normalized[key].to_numpy(dtype=np.float64)
    return score


def fit_candidate_b_score(frame: pd.DataFrame) -> tuple[np.ndarray, dict[str, dict[str, np.ndarray]]]:
    raw = build_candidate_b_components(frame)
    scaler = {name: fit_percentile_rank(raw[name].to_numpy(dtype=np.float64)) for name in raw.columns}
    normalized = pd.DataFrame({
        name: apply_percentile_rank(raw[name].to_numpy(dtype=np.float64), scaler[name])
        for name in raw.columns
    })
    return compose_candidate_b_score(normalized), scaler


def apply_candidate_b_score(frame: pd.DataFrame, scaler: dict[str, dict[str, np.ndarray]]) -> np.ndarray:
    raw = build_candidate_b_components(frame)
    normalized = pd.DataFrame({
        name: apply_percentile_rank(raw[name].to_numpy(dtype=np.float64), scaler[name])
        for name in raw.columns
    })
    return compose_candidate_b_score(normalized)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `./.venv/bin/python -m pytest tests/test_entry_path_trade_filter.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add ML/entry_path_trade_filter.py tests/test_entry_path_trade_filter.py
git commit -m "feat: add entry path trade filter score helpers"
```

---

### Task 2: Добавить выбор среза по coverage и проверку устойчивости по времени

**Files:**
- Modify: `ML/entry_path_trade_filter.py`
- Modify: `tests/test_entry_path_trade_filter.py`

- [ ] **Step 1: Write the failing tests for coverage-window selection and yearly stability**

```python
# tests/test_entry_path_trade_filter.py
import json
import pandas as pd

from ML import entry_path_trade_filter as etf


def test_evaluate_score_grid_computes_pf_and_year_stability():
    frame = pd.DataFrame({
        'time': pd.to_datetime([
            '2023-01-01 00:00',
            '2023-01-02 00:00',
            '2024-01-01 00:00',
            '2024-01-02 00:00',
        ]),
        'signal': [1, 1, -1, -1],
        'true_ret_24_dir_atr': [1.0, -0.5, 1.2, -0.4],
    })
    score = [0.9, 0.8, 0.2, 0.1]

    table = etf.evaluate_score_grid(frame, score, candidate='A', target_coverages=[0.50], min_period_trades=1)

    assert table.iloc[0]['candidate'] == 'A'
    assert table.iloc[0]['trades'] == 2
    assert table.iloc[0]['pf'] == 2.0
    assert table.iloc[0]['stability_ratio'] == 1.0
    detail = json.loads(table.iloc[0]['period_detail_json'])
    assert set(detail.keys()) == {'2023'}


def test_pick_best_slice_prefers_pf_then_stability_then_coverage_gap():
    table = pd.DataFrame([
        {'candidate': 'A', 'pf': 1.30, 'stability_ratio': 1.0, 'coverage_gap': 0.01, 'trades': 80},
        {'candidate': 'A', 'pf': 1.25, 'stability_ratio': 1.0, 'coverage_gap': 0.00, 'trades': 82},
    ])

    best = etf.pick_best_slice(table)

    assert best['pf'] == 1.30
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_entry_path_trade_filter.py -q`
Expected: FAIL with missing `evaluate_score_grid` and `pick_best_slice`.

- [ ] **Step 3: Implement validation slice evaluation and time stability**

```python
# ML/entry_path_trade_filter.py
import json


def compute_pf(values: np.ndarray) -> float:
    gross_profit = float(values[values > 0].sum())
    gross_loss = float(-values[values < 0].sum())
    return gross_profit / gross_loss if gross_loss > 0 else (np.inf if gross_profit > 0 else 0.0)


def _attach_period_column(frame: pd.DataFrame, min_period_trades: int) -> tuple[pd.Series, str]:
    year = frame['time'].dt.year.astype('Int64').astype(str)
    if year.nunique(dropna=True) >= 2:
        return year, 'year'

    half = frame['time'].dt.year.astype('Int64').astype(str) + 'H' + np.where(frame['time'].dt.month <= 6, '1', '2')
    return pd.Series(half, index=frame.index), 'half_year'


def evaluate_score_grid(
    frame: pd.DataFrame,
    score: np.ndarray,
    candidate: str,
    target_coverages: list[float],
    min_period_trades: int = 10,
) -> pd.DataFrame:
    active = frame.loc[frame['signal'] != 0].copy().reset_index(drop=True)
    active['score'] = np.asarray(score, dtype=np.float64)

    rows = []
    for target_coverage in target_coverages:
        threshold = float(active['score'].quantile(1.0 - target_coverage))
        selected = active.loc[active['score'] >= threshold].copy()
        pnl = selected['true_ret_24_dir_atr'].to_numpy(dtype=np.float64)

        period_key, period_mode = _attach_period_column(selected, min_period_trades)
        selected['period_key'] = period_key
        eligible_periods = 0
        stable_periods = 0
        worst_period_pf = np.nan
        detail = {}
        period_pfs = []

        for period, group in selected.groupby('period_key', dropna=True):
            group_pnl = group['true_ret_24_dir_atr'].to_numpy(dtype=np.float64)
            period_pf = compute_pf(group_pnl)
            detail[str(period)] = {
                'trades': int(len(group)),
                'pf': period_pf,
                'mean_pnl': float(group_pnl.mean()),
            }
            if len(group) >= min_period_trades:
                eligible_periods += 1
                stable_periods += int(period_pf >= 1.0)
                period_pfs.append(period_pf)

        if period_pfs:
            worst_period_pf = float(np.min(period_pfs))

        actual_coverage = len(selected) / max(len(active), 1)
        rows.append({
            'candidate': candidate,
            'target_coverage': float(target_coverage),
            'coverage': float(actual_coverage),
            'coverage_gap': abs(float(actual_coverage) - float(target_coverage)),
            'score_threshold': threshold,
            'trades': int(len(selected)),
            'pf': compute_pf(pnl),
            'win_rate': float((pnl > 0).mean()) if len(pnl) else 0.0,
            'mean_pnl_atr': float(pnl.mean()) if len(pnl) else 0.0,
            'period_mode': period_mode,
            'eligible_periods': eligible_periods,
            'stable_periods': stable_periods,
            'stability_ratio': float(stable_periods / eligible_periods) if eligible_periods > 0 else 0.0,
            'worst_period_pf': worst_period_pf,
            'period_detail_json': json.dumps(detail, ensure_ascii=False, sort_keys=True),
        })

    return pd.DataFrame(rows)


def evaluate_frozen_threshold(
    frame: pd.DataFrame,
    score: np.ndarray,
    candidate: str,
    threshold: float,
    target_coverage: float,
    min_period_trades: int = 10,
) -> pd.DataFrame:
    active = frame.loc[frame['signal'] != 0].copy().reset_index(drop=True)
    active['score'] = np.asarray(score, dtype=np.float64)
    selected = active.loc[active['score'] >= float(threshold)].copy()
    pnl = selected['true_ret_24_dir_atr'].to_numpy(dtype=np.float64)

    period_key, period_mode = _attach_period_column(selected, min_period_trades)
    selected['period_key'] = period_key
    eligible_periods = 0
    stable_periods = 0
    worst_period_pf = np.nan
    detail = {}
    period_pfs = []

    for period, group in selected.groupby('period_key', dropna=True):
        group_pnl = group['true_ret_24_dir_atr'].to_numpy(dtype=np.float64)
        period_pf = compute_pf(group_pnl)
        detail[str(period)] = {
            'trades': int(len(group)),
            'pf': period_pf,
            'mean_pnl': float(group_pnl.mean()),
        }
        if len(group) >= min_period_trades:
            eligible_periods += 1
            stable_periods += int(period_pf >= 1.0)
            period_pfs.append(period_pf)

    if period_pfs:
        worst_period_pf = float(np.min(period_pfs))

    actual_coverage = len(selected) / max(len(active), 1)
    return pd.DataFrame([{
        'candidate': candidate,
        'target_coverage': float(target_coverage),
        'coverage': float(actual_coverage),
        'coverage_gap': abs(float(actual_coverage) - float(target_coverage)),
        'score_threshold': float(threshold),
        'trades': int(len(selected)),
        'pf': compute_pf(pnl),
        'win_rate': float((pnl > 0).mean()) if len(pnl) else 0.0,
        'mean_pnl_atr': float(pnl.mean()) if len(pnl) else 0.0,
        'period_mode': period_mode,
        'eligible_periods': eligible_periods,
        'stable_periods': stable_periods,
        'stability_ratio': float(stable_periods / eligible_periods) if eligible_periods > 0 else 0.0,
        'worst_period_pf': worst_period_pf,
        'period_detail_json': json.dumps(detail, ensure_ascii=False, sort_keys=True),
    }])


def pick_best_slice(table: pd.DataFrame) -> pd.Series:
    ranked = table.sort_values(
        ['pf', 'stability_ratio', 'coverage_gap', 'trades'],
        ascending=[False, False, True, False],
    ).reset_index(drop=True)
    return ranked.iloc[0]
```

- [ ] **Step 4: Run the tests to verify the selection layer passes**

Run: `./.venv/bin/python -m pytest tests/test_entry_path_trade_filter.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add ML/entry_path_trade_filter.py tests/test_entry_path_trade_filter.py
git commit -m "feat: add entry path filter selection and stability checks"
```

---

### Task 3: Добавить вторичную последовательную проверку и markdown-отчёт

**Files:**
- Modify: `ML/entry_path_trade_filter.py`
- Modify: `tests/test_entry_path_trade_filter.py`

- [ ] **Step 1: Write the failing tests for sequential mode and markdown report**

```python
# tests/test_entry_path_trade_filter.py
import pandas as pd

from ML import entry_path_trade_filter as etf


def test_sequential_check_skips_overlapping_rows():
    frame = pd.DataFrame({
        'time': pd.to_datetime([
            '2024-01-01 00:00',
            '2024-01-01 01:00',
            '2024-01-01 02:00',
            '2024-01-01 03:00',
        ]),
        'signal': [1, -1, 1, -1],
        'true_ret_24_dir_atr': [1.0, -1.0, 0.5, 0.7],
    })
    selected_mask = pd.Series([True, True, False, True])

    out = etf.run_sequential_check(frame, selected_mask, hold_bars=2)

    assert out['trades'] == 2
    assert out['accepted_indices'] == [0, 3]


def test_trade_filter_report_mentions_winner_and_secondary_check():
    validation_best = {'candidate': 'B', 'pf': 1.42, 'coverage': 0.69, 'stability_ratio': 1.0}
    test_row = {'candidate': 'B', 'pf': 1.31, 'coverage': 0.68, 'stability_ratio': 1.0}
    sequential = {'trades': 24, 'pf': 1.18, 'coverage': 0.52}

    report = etf.build_trade_filter_report_markdown(
        validation_best=validation_best,
        test_row=test_row,
        sequential_summary=sequential,
        rule_path='ML/reports/entry_path_trade_filter_selected_rule.json',
    )

    assert 'Победитель: **B**' in report
    assert '## Validation Winner' in report
    assert '## Test Check' in report
    assert '## Sequential Check' in report
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_entry_path_trade_filter.py -q`
Expected: FAIL with missing `run_sequential_check` and `build_trade_filter_report_markdown`.

- [ ] **Step 3: Implement the secondary sequential check and report builder**

```python
# ML/entry_path_trade_filter.py
def run_sequential_check(
    frame: pd.DataFrame,
    selected_mask: pd.Series,
    hold_bars: int = 24,
) -> dict[str, object]:
    active = frame.loc[frame['signal'] != 0].copy()
    active['selected'] = selected_mask.to_numpy(dtype=bool)
    accepted_indices = []
    accepted_pnl = []
    next_free_idx = -1

    for idx, row in active.iterrows():
        if not bool(row['selected']):
            continue
        if idx <= next_free_idx:
            continue
        accepted_indices.append(int(idx))
        accepted_pnl.append(float(row['true_ret_24_dir_atr']))
        next_free_idx = idx + hold_bars

    pnl = np.asarray(accepted_pnl, dtype=np.float64)
    return {
        'trades': int(len(pnl)),
        'accepted_indices': accepted_indices,
        'coverage': float(len(pnl) / max(int(selected_mask.sum()), 1)),
        'pf': compute_pf(pnl) if len(pnl) else 0.0,
        'mean_pnl_atr': float(pnl.mean()) if len(pnl) else 0.0,
        'win_rate': float((pnl > 0).mean()) if len(pnl) else 0.0,
    }


def build_trade_filter_report_markdown(
    validation_best: dict,
    test_row: dict,
    sequential_summary: dict,
    rule_path: str,
) -> str:
    lines = [
        '# Entry Path Trade Filter v1',
        '',
        f"Победитель: **{validation_best['candidate']}**",
        '',
        '## Validation Winner',
        '',
        f"- candidate: {validation_best['candidate']}",
        f"- pf: {validation_best['pf']:.4f}",
        f"- coverage: {validation_best['coverage']:.1%}",
        f"- stability_ratio: {validation_best['stability_ratio']:.2f}",
        '',
        '## Test Check',
        '',
        f"- candidate: {test_row['candidate']}",
        f"- pf: {test_row['pf']:.4f}",
        f"- coverage: {test_row['coverage']:.1%}",
        f"- stability_ratio: {test_row['stability_ratio']:.2f}",
        '',
        '## Sequential Check',
        '',
        f"- trades: {sequential_summary['trades']}",
        f"- pf: {sequential_summary['pf']:.4f}",
        f"- coverage_vs_selected: {sequential_summary['coverage']:.1%}",
        '',
        '## Frozen Rule',
        '',
        f'- `{rule_path}`',
    ]
    return '\n'.join(lines)
```

- [ ] **Step 4: Run the tests to verify it passes**

Run: `./.venv/bin/python -m pytest tests/test_entry_path_trade_filter.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add ML/entry_path_trade_filter.py tests/test_entry_path_trade_filter.py
git commit -m "feat: add entry path trade filter report and sequential check"
```

---

### Task 4: Собрать benchmark-CLI, заморозить победителя и выпустить артефакты

**Files:**
- Create: `ML/benchmark_entry_path_trade_filter.py`
- Modify: `tests/test_entry_path_trade_filter.py`
- Create: `ML/reports/entry_path_trade_filter_validation_summary.csv`
- Create: `ML/reports/entry_path_trade_filter_test_summary.csv`
- Create: `ML/reports/entry_path_trade_filter_selected_rule.json`
- Create: `ML/reports/entry_path_trade_filter_report.md`

- [ ] **Step 1: Write the failing integration-style test for benchmark runner**

```python
# tests/test_entry_path_trade_filter.py
import json
from pathlib import Path

import pandas as pd

from ML import benchmark_entry_path_trade_filter as bench


def test_run_benchmark_writes_rule_and_report(tmp_path):
    val = pd.DataFrame({
        'time': ['2023.01.01 00:00', '2023.01.02 00:00', '2024.01.01 00:00', '2024.01.02 00:00'],
        'signal': [1, 1, -1, -1],
        'pred_ret_12_dir_atr': [0.9, 0.8, 0.2, 0.1],
        'pred_ret_24_dir_atr': [0.9, 0.8, 0.2, 0.1],
        'pred_fav_12_atr': [1.2, 1.1, 0.4, 0.3],
        'pred_adv_12_atr': [0.2, 0.3, 0.5, 0.6],
        'pred_fav_24_atr': [1.5, 1.3, 0.5, 0.4],
        'pred_adv_24_atr': [0.3, 0.4, 0.6, 0.7],
        'pred_path_6_prob_neg': [0.1, 0.2, 0.6, 0.7],
        'pred_path_6_prob_pos': [0.8, 0.7, 0.2, 0.1],
        'true_ret_24_dir_atr': [1.0, 0.8, -0.3, -0.4],
    })
    test = val.copy()

    val_path = tmp_path / 'val.csv'
    test_path = tmp_path / 'test.csv'
    val.to_csv(val_path, sep=';', index=False)
    test.to_csv(test_path, sep=';', index=False)

    out = bench.run_benchmark(
        validation_csv=val_path,
        test_csv=test_path,
        output_dir=tmp_path,
        coverage_grid=[0.70],
        min_period_trades=1,
        sequential_hold_bars=2,
    )

    assert out['winner']['candidate'] in {'A', 'B'}
    assert (tmp_path / 'entry_path_trade_filter_selected_rule.json').exists()
    assert (tmp_path / 'entry_path_trade_filter_report.md').exists()

    payload = json.loads((tmp_path / 'entry_path_trade_filter_selected_rule.json').read_text(encoding='utf-8'))
    assert payload['winner']['candidate'] == out['winner']['candidate']
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_entry_path_trade_filter.py -q`
Expected: FAIL with `ImportError` for missing `benchmark_entry_path_trade_filter`.

- [ ] **Step 3: Implement the benchmark runner and CLI**

```python
# ML/benchmark_entry_path_trade_filter.py
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from ML.entry_path_trade_filter import (
    apply_candidate_b_score,
    build_candidate_a_score,
    build_trade_filter_report_markdown,
    evaluate_frozen_threshold,
    evaluate_score_grid,
    fit_candidate_b_score,
    pick_best_slice,
    run_sequential_check,
)


def load_prediction_frame(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, sep=';', low_memory=False)
    frame['time'] = pd.to_datetime(frame['time'], format='%Y.%m.%d %H:%M', errors='coerce')
    return frame


def run_benchmark(
    validation_csv: Path,
    test_csv: Path,
    output_dir: Path,
    coverage_grid: list[float],
    min_period_trades: int = 10,
    sequential_hold_bars: int = 24,
) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    val = load_prediction_frame(validation_csv)
    test = load_prediction_frame(test_csv)

    val_active = val.loc[val['signal'] != 0].copy().reset_index(drop=True)
    test_active = test.loc[test['signal'] != 0].copy().reset_index(drop=True)

    score_a_val = build_candidate_a_score(val_active)
    score_a_test = build_candidate_a_score(test_active)

    score_b_val, scaler = fit_candidate_b_score(val_active)
    score_b_test = apply_candidate_b_score(test_active, scaler)

    table_a = evaluate_score_grid(val_active, score_a_val, candidate='A', target_coverages=coverage_grid, min_period_trades=min_period_trades)
    table_b = evaluate_score_grid(val_active, score_b_val, candidate='B', target_coverages=coverage_grid, min_period_trades=min_period_trades)
    validation_summary = pd.concat([table_a, table_b], ignore_index=True)
    winner = pick_best_slice(validation_summary)

    score_test = score_a_test if winner['candidate'] == 'A' else score_b_test
    threshold = float(winner['score_threshold'])
    selected_test = pd.Series(score_test >= threshold)
    test_table = evaluate_frozen_threshold(
        test_active,
        score_test,
        candidate=str(winner['candidate']),
        threshold=threshold,
        target_coverage=float(winner['target_coverage']),
        min_period_trades=min_period_trades,
    )
    sequential = run_sequential_check(test_active, selected_test, hold_bars=sequential_hold_bars)

    validation_summary.to_csv(output_dir / 'entry_path_trade_filter_validation_summary.csv', sep=';', index=False)
    test_table.to_csv(output_dir / 'entry_path_trade_filter_test_summary.csv', sep=';', index=False)

    payload = {
        'winner': winner.to_dict(),
        'coverage_grid': list(coverage_grid),
        'validation_csv': str(validation_csv),
        'test_csv': str(test_csv),
        'sequential_hold_bars': int(sequential_hold_bars),
    }
    (output_dir / 'entry_path_trade_filter_selected_rule.json').write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )
    (output_dir / 'entry_path_trade_filter_report.md').write_text(
        build_trade_filter_report_markdown(
            validation_best=winner.to_dict(),
            test_row=test_table.iloc[0].to_dict(),
            sequential_summary=sequential,
            rule_path=str(output_dir / 'entry_path_trade_filter_selected_rule.json'),
        ),
        encoding='utf-8',
    )
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('--validation-csv', default='ML/reports/entry_path_v1_validation_predictions.csv')
    parser.add_argument('--test-csv', default='ML/reports/entry_path_test_predictions.csv')
    parser.add_argument('--output-dir', default='ML/reports')
    parser.add_argument('--coverage-grid', nargs='+', type=float, default=[0.65, 0.68, 0.70, 0.72, 0.75])
    parser.add_argument('--min-period-trades', type=int, default=10)
    parser.add_argument('--sequential-hold-bars', type=int, default=24)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_benchmark(
        validation_csv=Path(args.validation_csv),
        test_csv=Path(args.test_csv),
        output_dir=Path(args.output_dir),
        coverage_grid=list(args.coverage_grid),
        min_period_trades=args.min_period_trades,
        sequential_hold_bars=args.sequential_hold_bars,
    )


if __name__ == '__main__':
    main()
```

- [ ] **Step 4: Run targeted tests to verify the benchmark layer passes**

Run: `./.venv/bin/python -m pytest tests/test_entry_path_trade_filter.py -q`
Expected: PASS

- [ ] **Step 5: Run the real benchmark on current `entry_path_v1` artifacts**

Run: `./.venv/bin/python -m ML.benchmark_entry_path_trade_filter --validation-csv ML/reports/entry_path_v1_validation_predictions.csv --test-csv ML/reports/entry_path_test_predictions.csv --output-dir ML/reports --coverage-grid 0.65 0.68 0.70 0.72 0.75 --min-period-trades 10 --sequential-hold-bars 24`
Expected:
- writes `ML/reports/entry_path_trade_filter_validation_summary.csv`
- writes `ML/reports/entry_path_trade_filter_test_summary.csv`
- writes `ML/reports/entry_path_trade_filter_selected_rule.json`
- writes `ML/reports/entry_path_trade_filter_report.md`
- prints winner `A` or `B` chosen only on `validation`

- [ ] **Step 6: Run the focused suite one more time**

Run: `./.venv/bin/python -m pytest tests/test_entry_path_trade_filter.py tests/test_entry_path_reports.py tests/test_entry_path_training.py -q`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add ML/entry_path_trade_filter.py \
        ML/benchmark_entry_path_trade_filter.py \
        tests/test_entry_path_trade_filter.py \
        ML/reports/entry_path_trade_filter_validation_summary.csv \
        ML/reports/entry_path_trade_filter_test_summary.csv \
        ML/reports/entry_path_trade_filter_selected_rule.json \
        ML/reports/entry_path_trade_filter_report.md
git commit -m "feat: add entry path trade filter benchmark"
```

---

## Self-Review

- Spec coverage:
  - `A` и `B` score: Task 1
  - validation-only подбор порога: Task 2 + Task 4
  - coverage около `70%`: Task 2 + Task 4
  - ranking `quality -> stability -> coverage`: Task 2
  - secondary sequential check: Task 3
  - frozen winner + report artifacts: Task 4
- Placeholder scan:
  - `TODO/TBD` нет
  - для каждого шага с кодом даны конкретные функции, команды и файлы
- Type consistency:
  - `true_ret_24_dir_atr` везде используется как единая цель качества фильтра
  - названия `candidate`, `coverage`, `stability_ratio`, `period_detail_json` согласованы между helper-модулем, CLI и отчётом
