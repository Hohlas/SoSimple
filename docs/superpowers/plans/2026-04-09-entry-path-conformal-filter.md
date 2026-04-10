# Entry Path Conformal Filter v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Добавить первый conformal-слой поверх уже замороженного `A @ 7.5%` и честно проверить, улучшает ли он отбор сделок без ухудшения последовательной проверки.

**Architecture:** План не меняет обучение `entry_path_v1` и не пересобирает trade filter. Новый модуль берёт уже готовые `validation/test`-предсказания, применяет замороженную базу `A @ 7.5%`, калибрует общий conformal-радиус только на validation-сделках после базы, затем сравнивает правила `LB > 0`, `LB > 0.25`, `LB > 0.50`, `LB > 0.75`. Benchmark замораживает победителя на validation, применяет его на test и выпускает JSON/CSV/Markdown артефакты.

**Tech Stack:** Python 3.11+, pandas, numpy, pytest

---

## File Map

- `ML/entry_path_conformal_filter.py`
  Назначение: ядро conformal-слоя поверх `A @ 7.5%`: загрузка базового правила, применение базового фильтра, расчёт conformal-квантили, построение нижней границы, таблица кандидатов, выбор победителя и Markdown-отчёт.
- `ML/benchmark_entry_path_conformal_filter.py`
  Назначение: CLI-обвязка для полного прогона на `validation/test`, выпуска JSON/CSV/Markdown артефактов и печати итогового payload.
- `tests/test_entry_path_conformal_filter.py`
  Назначение: unit/smoke тесты conformal-математики, baseline fallback, ограничения `>= 25` сделок и защиты от ухудшения последовательной проверки.

---

### Task 1: Добавить ядро conformal-слоя и базовые тесты

**Files:**
- Create: `ML/entry_path_conformal_filter.py`
- Create: `tests/test_entry_path_conformal_filter.py`

- [ ] **Step 1: Write the failing tests for baseline application, conformal quantile, and lower-bound rules**

```python
# tests/test_entry_path_conformal_filter.py
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, '.')

from ML import entry_path_conformal_filter as epcf


def _frame():
    return pd.DataFrame(
        {
            'time': pd.to_datetime(
                [
                    '2020-01-01 00:00',
                    '2020-01-02 00:00',
                    '2020-01-03 00:00',
                    '2020-01-04 00:00',
                ]
            ),
            'signal': [1, 1, -1, 0],
            'pred_ret_24_dir_atr': [0.40, 0.10, -0.20, 0.90],
            'true_ret_24_dir_atr': [0.55, 0.05, -0.30, 0.00],
        }
    )


def test_apply_baseline_rule_uses_frozen_a_threshold():
    frame = _frame()
    rule = {
        'winner': {
            'candidate': 'A',
            'score_threshold': 0.05,
            'target_coverage': 0.075,
        }
    }

    selected, mask = epcf.apply_baseline_rule(frame, rule)

    assert selected.index.tolist() == [0, 1]
    assert mask.tolist() == [True, True, False, False]


def test_compute_conformal_quantile_uses_finite_sample_correction():
    scores = np.array([0.10, 0.20, 0.30, 0.40], dtype=np.float64)

    q = epcf.compute_conformal_quantile(scores, alpha=0.10)

    assert q == pytest.approx(0.40)


def test_build_lower_bound_uses_pred_minus_quantile():
    lower, upper = epcf.build_prediction_interval(
        np.array([0.60, 0.15], dtype=np.float64),
        quantile=0.25,
    )

    assert np.allclose(lower, np.array([0.35, -0.10]))
    assert np.allclose(upper, np.array([0.85, 0.40]))


def test_apply_lower_bound_rule_filters_by_margin():
    mask = epcf.apply_lower_bound_rule(
        np.array([0.35, 0.10, -0.05], dtype=np.float64),
        margin=0.25,
    )

    assert mask.tolist() == [True, False, False]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_entry_path_conformal_filter.py -q`
Expected: FAIL with `ImportError` or `AttributeError` for missing `entry_path_conformal_filter` helpers.

- [ ] **Step 3: Write the minimal conformal core**

```python
# ML/entry_path_conformal_filter.py
import json
from pathlib import Path

import numpy as np
import pandas as pd

from ML.entry_path_trade_filter import build_candidate_a_score


DEFAULT_ALPHA = 0.10
DEFAULT_MARGIN_GRID = (0.0, 0.25, 0.50, 0.75)


def load_rule_payload(path) -> dict:
    return json.loads(Path(path).read_text(encoding='utf-8'))


def apply_baseline_rule(frame: pd.DataFrame, rule_payload: dict) -> tuple[pd.DataFrame, pd.Series]:
    winner = rule_payload['winner']
    if winner.get('candidate') != 'A':
        raise ValueError('Conformal v1 expects frozen candidate A baseline.')

    score = pd.Series(build_candidate_a_score(frame), index=frame.index, dtype='float64')
    active_mask = frame['signal'].to_numpy() != 0
    selected_mask = active_mask & (score.to_numpy(dtype=np.float64) >= float(winner['score_threshold']))

    selected = frame.loc[selected_mask].copy()
    selected['baseline_score'] = score.loc[selected.index].to_numpy(dtype=np.float64)
    return selected, pd.Series(selected_mask, index=frame.index, dtype=bool)


def compute_conformal_quantile(scores, alpha: float = DEFAULT_ALPHA) -> float:
    scores = np.sort(np.asarray(scores, dtype=np.float64))
    if scores.size == 0:
        raise ValueError('Conformal calibration requires at least one score.')

    level = min((1.0 - alpha) * (1.0 + 1.0 / scores.size), 1.0)
    return float(np.quantile(scores, level))


def build_prediction_interval(prediction, quantile: float) -> tuple[np.ndarray, np.ndarray]:
    prediction = np.asarray(prediction, dtype=np.float64)
    q = float(quantile)
    return prediction - q, prediction + q


def apply_lower_bound_rule(lower_bound, margin: float) -> np.ndarray:
    lower_bound = np.asarray(lower_bound, dtype=np.float64)
    return lower_bound > float(margin)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `./.venv/bin/python -m pytest tests/test_entry_path_conformal_filter.py -q`
Expected: PASS for 4 tests.

- [ ] **Step 5: Commit**

```bash
git add ML/entry_path_conformal_filter.py tests/test_entry_path_conformal_filter.py
git commit -m "feat: add entry path conformal filter core"
```

---

### Task 2: Добавить оценку кандидатов и выбор победителя

**Files:**
- Modify: `ML/entry_path_conformal_filter.py`
- Modify: `tests/test_entry_path_conformal_filter.py`

- [ ] **Step 1: Add failing tests for baseline fallback, min-trades guard, and sequential PF guard**

```python
def test_pick_best_candidate_falls_back_to_baseline_when_all_rules_too_small():
    table = pd.DataFrame(
        [
            {'candidate': 'baseline', 'pf': 2.6, 'mean_pnl_atr': 1.4, 'trades': 36, 'sequential_pf': 2.8, 'stability_ratio': 1.0},
            {'candidate': 'LB>0', 'pf': 4.0, 'mean_pnl_atr': 2.0, 'trades': 24, 'sequential_pf': 3.1, 'stability_ratio': 1.0},
            {'candidate': 'LB>0.25', 'pf': 5.0, 'mean_pnl_atr': 2.2, 'trades': 18, 'sequential_pf': 3.4, 'stability_ratio': 1.0},
        ]
    )

    best = epcf.pick_best_candidate(table, min_trades=25, baseline_sequential_pf=2.8)

    assert best['candidate'] == 'baseline'


def test_pick_best_candidate_rejects_worse_sequential_pf():
    table = pd.DataFrame(
        [
            {'candidate': 'baseline', 'pf': 2.6, 'mean_pnl_atr': 1.4, 'trades': 36, 'sequential_pf': 2.8, 'stability_ratio': 1.0},
            {'candidate': 'LB>0', 'pf': 4.0, 'mean_pnl_atr': 2.0, 'trades': 30, 'sequential_pf': 2.1, 'stability_ratio': 1.0},
            {'candidate': 'LB>0.25', 'pf': 3.1, 'mean_pnl_atr': 1.8, 'trades': 28, 'sequential_pf': 2.8, 'stability_ratio': 1.0},
        ]
    )

    best = epcf.pick_best_candidate(table, min_trades=25, baseline_sequential_pf=2.8)

    assert best['candidate'] == 'LB>0.25'


def test_evaluate_margin_grid_adds_baseline_and_lb_candidates():
    frame = pd.DataFrame(
        {
            'time': pd.to_datetime(
                [
                    '2020-01-01 00:00',
                    '2020-01-02 00:00',
                    '2020-01-03 00:00',
                    '2020-01-04 00:00',
                ]
            ),
            'signal': [1, 1, -1, -1],
            'pred_ret_24_dir_atr': [0.80, 0.55, 0.30, 0.10],
            'true_ret_24_dir_atr': [1.10, 0.60, -0.20, -0.50],
        }
    )

    table = epcf.evaluate_margin_grid(
        frame=frame,
        quantile=0.25,
        margin_grid=(0.0, 0.25),
        min_period_trades=1,
        hold_bars=24,
    )

    assert table['candidate'].tolist() == ['baseline', 'LB>0', 'LB>0.25']
    assert 'sequential_pf' in table.columns
    assert table.iloc[0]['trades'] == 4
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_entry_path_conformal_filter.py -q`
Expected: FAIL with missing `pick_best_candidate` and `evaluate_margin_grid`.

- [ ] **Step 3: Implement candidate evaluation and winner selection**

```python
# ML/entry_path_conformal_filter.py
from ML.entry_path_trade_filter import evaluate_frozen_threshold
from ML.entry_path_trade_filter import run_sequential_check


def evaluate_margin_grid(
    frame: pd.DataFrame,
    quantile: float,
    margin_grid=DEFAULT_MARGIN_GRID,
    min_period_trades: int = 10,
    hold_bars: int = 24,
) -> pd.DataFrame:
    score = frame['pred_ret_24_dir_atr'].to_numpy(dtype=np.float64)
    lower_bound, upper_bound = build_prediction_interval(score, quantile)

    rows = []
    baseline_summary = evaluate_frozen_threshold(
        frame=frame,
        score=np.ones(len(frame), dtype=np.float64),
        candidate='baseline',
        threshold=float('-inf'),
        target_coverage=1.0,
        min_period_trades=min_period_trades,
    ).iloc[0].to_dict()
    baseline_seq = run_sequential_check(frame, np.ones(len(frame), dtype=bool), hold_bars=hold_bars)
    baseline_summary.update(
        {
            'quantile': float(quantile),
            'margin': np.nan,
            'sequential_pf': float(baseline_seq['pf']),
            'sequential_trades': int(baseline_seq['trades']),
        }
    )
    rows.append(baseline_summary)

    for margin in margin_grid:
        mask = apply_lower_bound_rule(lower_bound, margin)
        summary = evaluate_frozen_threshold(
            frame=frame,
            score=lower_bound,
            candidate=f'LB>{margin:g}',
            threshold=float(margin),
            target_coverage=np.nan,
            min_period_trades=min_period_trades,
        ).iloc[0].to_dict()
        seq = run_sequential_check(frame, mask, hold_bars=hold_bars)
        summary.update(
            {
                'quantile': float(quantile),
                'margin': float(margin),
                'interval_width': float(2.0 * quantile),
                'sequential_pf': float(seq['pf']),
                'sequential_trades': int(seq['trades']),
            }
        )
        rows.append(summary)

    return pd.DataFrame(rows)


def pick_best_candidate(
    table: pd.DataFrame,
    min_trades: int = 25,
    baseline_sequential_pf: float | None = None,
) -> pd.Series:
    if table.empty:
        raise ValueError('No conformal candidates to rank.')

    baseline_row = table.loc[table['candidate'] == 'baseline'].iloc[0]
    seq_floor = float(baseline_sequential_pf if baseline_sequential_pf is not None else baseline_row['sequential_pf'])
    candidate_mask = (
        (table['candidate'] != 'baseline')
        & (table['trades'] >= int(min_trades))
        & (table['sequential_pf'] >= seq_floor)
    )
    eligible = table.loc[candidate_mask].copy()
    if eligible.empty:
        return baseline_row

    return eligible.sort_values(
        ['pf', 'mean_pnl_atr', 'stability_ratio', 'trades'],
        ascending=[False, False, False, False],
    ).iloc[0]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `./.venv/bin/python -m pytest tests/test_entry_path_conformal_filter.py -q`
Expected: PASS for 7 tests.

- [ ] **Step 5: Commit**

```bash
git add ML/entry_path_conformal_filter.py tests/test_entry_path_conformal_filter.py
git commit -m "feat: add conformal candidate evaluation"
```

---

### Task 3: Добавить benchmark CLI и выпуск артефактов

**Files:**
- Create: `ML/benchmark_entry_path_conformal_filter.py`
- Modify: `ML/entry_path_conformal_filter.py`
- Modify: `tests/test_entry_path_conformal_filter.py`

- [ ] **Step 1: Add failing smoke test for the end-to-end benchmark**

```python
def test_run_benchmark_writes_rule_report_and_csvs(tmp_path: Path):
    frame = pd.DataFrame(
        {
            'time': ['2020.01.01 00:00', '2020.01.02 00:00', '2020.01.03 00:00', '2020.01.04 00:00'],
            'signal': [1, 1, -1, -1],
            'pred_ret_24_dir_atr': [0.80, 0.55, 0.30, 0.10],
            'true_ret_24_dir_atr': [1.10, 0.60, -0.20, -0.50],
        }
    )
    validation_csv = tmp_path / 'val.csv'
    test_csv = tmp_path / 'test.csv'
    frame.to_csv(validation_csv, sep=';', index=False)
    frame.to_csv(test_csv, sep=';', index=False)

    baseline_rule = tmp_path / 'baseline.json'
    baseline_rule.write_text(
        json.dumps(
            {
                'winner': {
                    'candidate': 'A',
                    'score_threshold': 0.0,
                    'target_coverage': 0.075,
                },
                'sequential_hold_bars': 24,
                'sequential_summary': {'pf': 1.0},
            }
        ),
        encoding='utf-8',
    )

    payload = bench.run_benchmark(
        validation_csv=validation_csv,
        test_csv=test_csv,
        baseline_rule_path=baseline_rule,
        output_dir=tmp_path,
        alpha=0.10,
        margin_grid=[0.0, 0.25],
        min_trades=1,
        min_period_trades=1,
        sequential_hold_bars=24,
    )

    assert (tmp_path / 'entry_path_conformal_filter_selected_rule.json').exists()
    assert (tmp_path / 'entry_path_conformal_filter_report.md').exists()
    assert (tmp_path / 'entry_path_conformal_filter_validation_summary.csv').exists()
    assert (tmp_path / 'entry_path_conformal_filter_test_summary.csv').exists()
    assert payload['winner']['candidate'] in {'baseline', 'LB>0', 'LB>0.25'}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_entry_path_conformal_filter.py::test_run_benchmark_writes_rule_report_and_csvs -q`
Expected: FAIL with `ImportError` for missing benchmark module.

- [ ] **Step 3: Implement the benchmark runner and Markdown report**

```python
# ML/benchmark_entry_path_conformal_filter.py
import argparse
import json
from pathlib import Path

import pandas as pd

from ML.entry_path_conformal_filter import DEFAULT_ALPHA
from ML.entry_path_conformal_filter import DEFAULT_MARGIN_GRID
from ML.entry_path_conformal_filter import apply_baseline_rule
from ML.entry_path_conformal_filter import build_conformal_report_markdown
from ML.entry_path_conformal_filter import compute_conformal_quantile
from ML.entry_path_conformal_filter import evaluate_margin_grid
from ML.entry_path_conformal_filter import load_rule_payload
from ML.entry_path_conformal_filter import pick_best_candidate


def load_prediction_frame(path) -> pd.DataFrame:
    frame = pd.read_csv(Path(path), sep=';')
    frame['time'] = pd.to_datetime(frame['time'], format='%Y.%m.%d %H:%M', errors='coerce')
    return frame


def run_benchmark(
    validation_csv,
    test_csv,
    baseline_rule_path,
    output_dir,
    alpha=DEFAULT_ALPHA,
    margin_grid=DEFAULT_MARGIN_GRID,
    min_trades=25,
    min_period_trades=10,
    sequential_hold_bars=24,
):
    rule_payload = load_rule_payload(baseline_rule_path)
    validation_frame = load_prediction_frame(validation_csv)
    test_frame = load_prediction_frame(test_csv)

    validation_base, _ = apply_baseline_rule(validation_frame, rule_payload)
    test_base, _ = apply_baseline_rule(test_frame, rule_payload)

    residuals = (
        validation_base['true_ret_24_dir_atr'].to_numpy(dtype='float64')
        - validation_base['pred_ret_24_dir_atr'].to_numpy(dtype='float64')
    )
    quantile = compute_conformal_quantile(abs(residuals), alpha=alpha)

    validation_summary = evaluate_margin_grid(
        frame=validation_base,
        quantile=quantile,
        margin_grid=margin_grid,
        min_period_trades=min_period_trades,
        hold_bars=sequential_hold_bars,
    )
    best_row = pick_best_candidate(
        validation_summary,
        min_trades=min_trades,
        baseline_sequential_pf=float(rule_payload['sequential_summary']['pf']),
    )

    test_summary = evaluate_margin_grid(
        frame=test_base,
        quantile=quantile,
        margin_grid=[],
        min_period_trades=min_period_trades,
        hold_bars=sequential_hold_bars,
    )
    if best_row['candidate'] == 'baseline':
        frozen_test_row = test_summary.iloc[[0]].copy()
    else:
        margin = float(best_row['margin'])
        frozen_test_row = evaluate_margin_grid(
            frame=test_base,
            quantile=quantile,
            margin_grid=[margin],
            min_period_trades=min_period_trades,
            hold_bars=sequential_hold_bars,
        ).iloc[[1]].copy()

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    validation_path = output_dir / 'entry_path_conformal_filter_validation_summary.csv'
    test_path = output_dir / 'entry_path_conformal_filter_test_summary.csv'
    rule_path = output_dir / 'entry_path_conformal_filter_selected_rule.json'
    report_path = output_dir / 'entry_path_conformal_filter_report.md'

    validation_summary.to_csv(validation_path, sep=';', index=False)
    frozen_test_row.to_csv(test_path, sep=';', index=False)

    payload = {
        'baseline_rule_path': str(baseline_rule_path),
        'validation_csv': str(validation_csv),
        'test_csv': str(test_csv),
        'alpha': float(alpha),
        'quantile': float(quantile),
        'margin_grid': [float(x) for x in margin_grid],
        'min_trades': int(min_trades),
        'winner': best_row.to_dict(),
        'validation_summary_path': str(validation_path),
        'test_summary_path': str(test_path),
    }
    rule_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    report_path.write_text(
        build_conformal_report_markdown(
            validation_best=best_row.to_dict(),
            test_row=frozen_test_row.iloc[0].to_dict(),
            rule_path=str(rule_path),
            quantile=float(quantile),
            alpha=float(alpha),
        ),
        encoding='utf-8',
    )
    return payload
```

- [ ] **Step 4: Extend the core module with the report builder**

```python
# ML/entry_path_conformal_filter.py
def build_conformal_report_markdown(validation_best, test_row, rule_path, quantile: float, alpha: float) -> str:
    lines = [
        '# Entry Path Conformal Filter Report',
        '',
        f"- alpha: **{alpha:.2f}**",
        f"- quantile: **{quantile:.4f}**",
        '',
        '## Validation Winner',
        '',
        f"- candidate: `{validation_best.get('candidate', 'baseline')}`",
        f"- pf: **{float(validation_best.get('pf', 0.0)):.4f}**",
        f"- trades: **{int(validation_best.get('trades', 0))}**",
        f"- sequential_pf: **{float(validation_best.get('sequential_pf', 0.0)):.4f}**",
        '',
        '## Test Check',
        '',
        f"- candidate: `{test_row.get('candidate', 'baseline')}`",
        f"- pf: **{float(test_row.get('pf', 0.0)):.4f}**",
        f"- trades: **{int(test_row.get('trades', 0))}**",
        f"- sequential_pf: **{float(test_row.get('sequential_pf', 0.0)):.4f}**",
        '',
        '## Frozen Rule',
        '',
        f'- Rule path: `{rule_path}`',
    ]
    return '\n'.join(lines)
```

- [ ] **Step 5: Run the full focused suite**

Run: `./.venv/bin/python -m pytest tests/test_entry_path_conformal_filter.py -q`
Expected: PASS for the new conformal suite.

- [ ] **Step 6: Commit**

```bash
git add ML/entry_path_conformal_filter.py ML/benchmark_entry_path_conformal_filter.py tests/test_entry_path_conformal_filter.py
git commit -m "feat: add entry path conformal benchmark"
```

---

### Task 4: Выпустить реальные conformal-артефакты на текущей замороженной базе

**Files:**
- Modify: `ML/reports/entry_path_conformal_filter_selected_rule.json`
- Modify: `ML/reports/entry_path_conformal_filter_report.md`
- Modify: `ML/reports/entry_path_conformal_filter_validation_summary.csv`
- Modify: `ML/reports/entry_path_conformal_filter_test_summary.csv`

- [ ] **Step 1: Run the benchmark on the frozen `A @ 7.5%` baseline**

Run:

```bash
./.venv/bin/python -m ML.benchmark_entry_path_conformal_filter \
  --baseline-rule-path ML/reports/entry_path_trade_filter_selected_rule.json \
  --validation-csv ML/reports/entry_path_v1_validation_predictions.csv \
  --test-csv ML/reports/entry_path_test_predictions.csv \
  --output-dir ML/reports \
  --alpha 0.10 \
  --margin-grid 0.0 0.25 0.5 0.75 \
  --min-trades 25 \
  --min-period-trades 10 \
  --sequential-hold-bars 24
```

Expected: JSON payload printed to stdout and four files written under `ML/reports/`.

- [ ] **Step 2: Verify the winner is frozen from validation and no candidate cheats**

Run:

```bash
./.venv/bin/python - <<'PY'
import json
from pathlib import Path

payload = json.loads(Path('ML/reports/entry_path_conformal_filter_selected_rule.json').read_text(encoding='utf-8'))
winner = payload['winner']
assert winner['candidate'] in {'baseline', 'LB>0', 'LB>0.25', 'LB>0.5', 'LB>0.75'}
assert int(winner['trades']) >= 25 or winner['candidate'] == 'baseline'
print(winner['candidate'], winner['trades'], winner['pf'])
PY
```

Expected: one short line like `baseline 36 2.6683` or `LB>0.25 27 3.1142`.

- [ ] **Step 3: Re-run the focused tests after the real artifact pass**

Run: `./.venv/bin/python -m pytest tests/test_entry_path_conformal_filter.py tests/test_entry_path_trade_filter.py -q`
Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add ML/reports/entry_path_conformal_filter_selected_rule.json ML/reports/entry_path_conformal_filter_report.md ML/reports/entry_path_conformal_filter_validation_summary.csv ML/reports/entry_path_conformal_filter_test_summary.csv
git commit -m "chore: publish entry path conformal filter artifacts"
```
