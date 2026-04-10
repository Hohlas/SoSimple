# Entry Path CQR Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Построить быстрый табличный `CQR`-слой поверх готовых `entry_path_v1` выгрузок и проверить, может ли он улучшить базу `A @ 7.5%`.

**Architecture:** Две `LightGBMRegressor` quantile-модели учатся на активных строках `train` и предсказывают нижнюю и верхнюю границы для `true_ret_24_dir_atr`. На `validation` к этим границам добавляется conformal-поправка, затем поверх уже замороженного `A @ 7.5%` сравниваются правила по `LB` и `width`. Победитель выбирается только на `validation` и без перенастройки применяется на `test`.

**Tech Stack:** Python 3.11+, pandas, numpy, lightgbm, joblib, pytest

---

## File Map

- `ML/entry_path_cqr.py`
  Назначение: признаки, обучение quantile-моделей, conformal-калибровка, построение интервала `LB/UB/width`, оценка кандидатов.
- `ML/benchmark_entry_path_cqr.py`
  Назначение: полный прогон `train -> validation -> test` поверх замороженного `A @ 7.5%`, выпуск JSON/CSV/Markdown артефактов.
- `tests/test_entry_path_cqr.py`
  Назначение: unit/smoke тесты математики `CQR`, правил отбора и benchmark-потока.

---

### Task 1: Добавить ядро tabular CQR

**Files:**
- Create: `ML/entry_path_cqr.py`
- Create: `tests/test_entry_path_cqr.py`

- [ ] **Step 1: Write the failing tests for quantile core**

```python
# tests/test_entry_path_cqr.py
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, '.')

from ML import entry_path_cqr as epc


def test_build_cqr_features_uses_expected_columns():
    frame = pd.DataFrame(
        {
            'pred_ret_6_dir_atr': [0.1],
            'pred_ret_12_dir_atr': [0.2],
            'pred_ret_24_dir_atr': [0.3],
            'pred_fav_6_atr': [0.4],
            'pred_adv_6_atr': [0.1],
            'pred_fav_12_atr': [0.5],
            'pred_adv_12_atr': [0.2],
            'pred_fav_24_atr': [0.6],
            'pred_adv_24_atr': [0.3],
            'pred_path_6_prob_neg': [0.2],
            'pred_path_6_prob_flat': [0.3],
            'pred_path_6_prob_pos': [0.5],
            'signal': [1],
            'ATR': [1.7],
            'baseline_score': [0.3],
            'year': [2025],
        }
    )

    X = epc.build_cqr_features(frame)

    assert list(X.columns) == epc.CQR_FEATURE_COLUMNS
    assert X.shape == (1, len(epc.CQR_FEATURE_COLUMNS))


def test_compute_cqr_score_uses_outside_interval_distance():
    score = epc.compute_cqr_score(
        y_true=np.array([0.9, 0.1, -0.5], dtype=np.float64),
        lower_pred=np.array([0.4, 0.0, -0.6], dtype=np.float64),
        upper_pred=np.array([0.8, 0.3, -0.2], dtype=np.float64),
    )

    assert np.allclose(score, np.array([0.1, 0.0, 0.0]))


def test_apply_cqr_correction_expands_interval():
    lower, upper, width = epc.apply_cqr_correction(
        lower_pred=np.array([0.2, -0.1], dtype=np.float64),
        upper_pred=np.array([0.6, 0.3], dtype=np.float64),
        correction=0.25,
    )

    assert np.allclose(lower, np.array([-0.05, -0.35]))
    assert np.allclose(upper, np.array([0.85, 0.55]))
    assert np.allclose(width, np.array([0.9, 0.9]))


def test_lb_and_width_rules_return_boolean_masks():
    lower = np.array([0.3, 0.1, -0.2], dtype=np.float64)
    width = np.array([0.8, 1.2, 0.9], dtype=np.float64)

    assert epc.apply_lb_rule(lower, margin=0.15).tolist() == [True, False, False]
    assert epc.apply_width_rule(width, max_width=1.0).tolist() == [True, False, True]
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_entry_path_cqr.py -q`

Expected: FAIL with `ImportError`, because `ML/entry_path_cqr.py` does not exist yet.

- [ ] **Step 3: Create the CQR core module**

```python
# ML/entry_path_cqr.py
from __future__ import annotations

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor


CQR_FEATURE_COLUMNS = [
    'pred_ret_6_dir_atr',
    'pred_ret_12_dir_atr',
    'pred_ret_24_dir_atr',
    'pred_fav_6_atr',
    'pred_adv_6_atr',
    'pred_fav_12_atr',
    'pred_adv_12_atr',
    'pred_fav_24_atr',
    'pred_adv_24_atr',
    'pred_path_6_prob_neg',
    'pred_path_6_prob_flat',
    'pred_path_6_prob_pos',
    'signal',
    'ATR',
    'baseline_score',
    'year',
]


def build_cqr_features(frame: pd.DataFrame) -> pd.DataFrame:
    missing = [column for column in CQR_FEATURE_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f'Missing CQR feature columns: {missing}')
    return frame[CQR_FEATURE_COLUMNS].copy()


def select_active_rows(frame: pd.DataFrame) -> pd.DataFrame:
    signal = pd.to_numeric(frame['signal'], errors='coerce').fillna(0).astype(int)
    return frame.loc[signal != 0].copy()


def fit_quantile_model(
    train_frame: pd.DataFrame,
    *,
    quantile_alpha: float,
    random_state: int = 42,
) -> LGBMRegressor:
    active = select_active_rows(train_frame)
    if active.empty:
        raise ValueError('No active BUY/SELL rows available for quantile training')

    X = build_cqr_features(active)
    y = active['true_ret_24_dir_atr'].to_numpy(dtype=np.float64)
    model = LGBMRegressor(
        objective='quantile',
        alpha=float(quantile_alpha),
        n_estimators=300,
        learning_rate=0.05,
        num_leaves=31,
        min_child_samples=20,
        random_state=random_state,
    )
    model.fit(X, y)
    return model


def predict_quantile(model: LGBMRegressor, frame: pd.DataFrame) -> np.ndarray:
    return np.asarray(model.predict(build_cqr_features(frame)), dtype=np.float64)


def compute_cqr_score(y_true, lower_pred, upper_pred) -> np.ndarray:
    y_true = np.asarray(y_true, dtype=np.float64)
    lower_pred = np.asarray(lower_pred, dtype=np.float64)
    upper_pred = np.asarray(upper_pred, dtype=np.float64)
    return np.maximum(lower_pred - y_true, y_true - upper_pred).clip(min=0.0)


def compute_cqr_correction(score, alpha: float = 0.10) -> float:
    score = np.asarray(score, dtype=np.float64)
    if score.size == 0:
        raise ValueError('At least one calibration score is required')
    level = min((1.0 - float(alpha)) * (1.0 + 1.0 / score.size), 1.0)
    return float(np.quantile(score, level))


def apply_cqr_correction(lower_pred, upper_pred, correction: float):
    lower_pred = np.asarray(lower_pred, dtype=np.float64)
    upper_pred = np.asarray(upper_pred, dtype=np.float64)
    correction = float(correction)
    lower = lower_pred - correction
    upper = upper_pred + correction
    width = upper - lower
    return lower, upper, width


def apply_lb_rule(lower, margin: float) -> np.ndarray:
    return np.asarray(lower, dtype=np.float64) > float(margin)


def apply_width_rule(width, max_width: float) -> np.ndarray:
    return np.asarray(width, dtype=np.float64) <= float(max_width)
```

- [ ] **Step 4: Run the focused test to verify it passes**

Run: `/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_entry_path_cqr.py -q`

Expected: PASS for 4 tests.

- [ ] **Step 5: Commit**

```bash
git add ML/entry_path_cqr.py tests/test_entry_path_cqr.py
git commit -m "feat: add entry path cqr core"
```

---

### Task 2: Добавить оценку кандидатов и benchmark CLI

**Files:**
- Modify: `ML/entry_path_cqr.py`
- Create: `ML/benchmark_entry_path_cqr.py`
- Modify: `tests/test_entry_path_cqr.py`

- [ ] **Step 1: Extend tests with candidate grid and benchmark flow**

```python
def test_evaluate_candidate_grid_includes_base_lb_and_width_rules():
    frame = pd.DataFrame(
        {
            'time': pd.to_datetime(['2023-01-01 00:00', '2023-01-02 00:00', '2024-01-01 00:00', '2024-01-02 00:00']),
            'signal': [1, 1, -1, -1],
            'pred_ret_24_dir_atr': [0.9, 0.4, 0.2, 0.1],
            'true_ret_24_dir_atr': [1.1, 0.2, -0.1, -0.3],
        }
    )
    lower = np.array([0.4, 0.1, -0.1, -0.3], dtype=np.float64)
    upper = np.array([1.1, 0.7, 0.5, 0.4], dtype=np.float64)
    width = upper - lower

    table = epc.evaluate_candidate_grid(
        frame=frame,
        lower=lower,
        upper=upper,
        width=width,
        correction=0.0,
        lb_margins=(0.0, 0.25),
        width_caps=(1.0,),
        min_period_trades=1,
        hold_bars=24,
    )

    assert 'baseline' in table['candidate'].tolist()
    assert 'LB>0' in table['candidate'].tolist()
    assert 'LB>0.25|W<=1' in table['candidate'].tolist()


def test_pick_best_cqr_candidate_returns_baseline_when_no_candidate_passes():
    table = pd.DataFrame(
        [
            {'candidate': 'baseline', 'trades': 36, 'pf': 2.5, 'mean_pnl_atr': 1.2, 'stability_ratio': 1.0, 'sequential_pf': 2.0},
            {'candidate': 'LB>0', 'trades': 10, 'pf': 3.0, 'mean_pnl_atr': 2.0, 'stability_ratio': 1.0, 'sequential_pf': 1.5},
        ]
    )

    winner = epc.pick_best_cqr_candidate(table, min_trades=25)

    assert winner['candidate'] == 'baseline'


def test_run_benchmark_writes_cqr_artifacts(tmp_path):
    import json
    from ML import benchmark_entry_path_cqr as bench

    train = pd.DataFrame(
        {
            'time': ['2020.01.01 00:00', '2020.01.02 00:00', '2020.01.03 00:00'],
            'signal': [1, -1, 1],
            'ATR': [1.0, 1.2, 1.1],
            'baseline_score': [0.4, 0.3, 0.5],
            'year': [2020, 2020, 2020],
            'pred_ret_6_dir_atr': [0.2, -0.1, 0.3],
            'pred_ret_12_dir_atr': [0.3, -0.2, 0.4],
            'pred_ret_24_dir_atr': [0.4, -0.3, 0.5],
            'pred_fav_6_atr': [0.5, 0.4, 0.6],
            'pred_adv_6_atr': [0.1, 0.2, 0.1],
            'pred_fav_12_atr': [0.6, 0.5, 0.7],
            'pred_adv_12_atr': [0.1, 0.2, 0.1],
            'pred_fav_24_atr': [0.7, 0.6, 0.8],
            'pred_adv_24_atr': [0.1, 0.2, 0.1],
            'pred_path_6_prob_neg': [0.2, 0.5, 0.1],
            'pred_path_6_prob_flat': [0.3, 0.3, 0.2],
            'pred_path_6_prob_pos': [0.5, 0.2, 0.7],
            'true_ret_24_dir_atr': [0.8, -0.2, 0.9],
        }
    )
    validation = train.copy()
    test = train.copy()

    train_path = tmp_path / 'train.csv'
    val_path = tmp_path / 'val.csv'
    test_path = tmp_path / 'test.csv'
    train.to_csv(train_path, sep=';', index=False)
    validation.to_csv(val_path, sep=';', index=False)
    test.to_csv(test_path, sep=';', index=False)

    baseline_rule = tmp_path / 'baseline.json'
    baseline_rule.write_text(
        json.dumps({'winner': {'candidate': 'A', 'score_threshold': -999.0}}),
        encoding='utf-8',
    )

    payload = bench.run_benchmark(
        train_csv=train_path,
        validation_csv=val_path,
        test_csv=test_path,
        baseline_rule_path=baseline_rule,
        output_dir=tmp_path,
        min_trades=1,
        min_period_trades=1,
    )

    assert (tmp_path / 'entry_path_cqr_selected_rule.json').exists()
    assert (tmp_path / 'entry_path_cqr_report.md').exists()
    assert payload['winner']['candidate']
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_entry_path_cqr.py -q`

Expected: FAIL with missing `evaluate_candidate_grid`, `pick_best_cqr_candidate`, or `benchmark_entry_path_cqr`.

- [ ] **Step 3: Add candidate evaluation helpers**

```python
# ML/entry_path_cqr.py
from ML.entry_path_trade_filter import evaluate_frozen_threshold, run_sequential_check


def evaluate_single_candidate(
    frame: pd.DataFrame,
    *,
    candidate_name: str,
    selected_mask,
    score,
    threshold: float,
    target_coverage: float,
    correction: float,
    margin: float | None,
    width_cap: float | None,
    min_period_trades: int,
    hold_bars: int,
) -> tuple[dict[str, object], dict[str, object]]:
    row = evaluate_frozen_threshold(
        frame=frame,
        score=score,
        candidate=candidate_name,
        threshold=threshold,
        target_coverage=target_coverage,
        min_period_trades=min_period_trades,
    ).iloc[0].to_dict()
    sequential_summary = run_sequential_check(frame, selected_mask, hold_bars=hold_bars)
    row.update({
        'correction': float(correction),
        'margin': np.nan if margin is None else float(margin),
        'width_cap': np.nan if width_cap is None else float(width_cap),
        'sequential_pf': float(sequential_summary['pf']),
        'sequential_trades': int(sequential_summary['trades']),
    })
    return row, sequential_summary


def evaluate_candidate_grid(
    frame: pd.DataFrame,
    *,
    lower,
    upper,
    width,
    correction: float,
    lb_margins=(0.0, 0.25, 0.5),
    width_caps=(1.0, 1.5),
    min_period_trades: int = 10,
    hold_bars: int = 24,
) -> pd.DataFrame:
    rows = []

    baseline_mask = np.ones(len(frame), dtype=bool)
    baseline_row, _ = evaluate_single_candidate(
        frame=frame,
        candidate_name='baseline',
        selected_mask=baseline_mask,
        score=np.ones(len(frame), dtype=np.float64),
        threshold=float('-inf'),
        target_coverage=1.0,
        correction=correction,
        margin=None,
        width_cap=None,
        min_period_trades=min_period_trades,
        hold_bars=hold_bars,
    )
    rows.append(baseline_row)

    for margin in lb_margins:
        lb_mask = apply_lb_rule(lower, margin)
        lb_row, _ = evaluate_single_candidate(
            frame=frame,
            candidate_name=f'LB>{margin:g}',
            selected_mask=lb_mask,
            score=np.asarray(lower, dtype=np.float64),
            threshold=float(margin),
            target_coverage=float(lb_mask.mean()) if len(lb_mask) > 0 else 0.0,
            correction=correction,
            margin=margin,
            width_cap=None,
            min_period_trades=min_period_trades,
            hold_bars=hold_bars,
        )
        rows.append(lb_row)

        for width_cap in width_caps:
            mask = lb_mask & apply_width_rule(width, width_cap)
            width_row, _ = evaluate_single_candidate(
                frame=frame,
                candidate_name=f'LB>{margin:g}|W<={width_cap:g}',
                selected_mask=mask,
                score=np.where(mask, 1.0, -1.0),
                threshold=0.0,
                target_coverage=float(mask.mean()) if len(mask) > 0 else 0.0,
                correction=correction,
                margin=margin,
                width_cap=width_cap,
                min_period_trades=min_period_trades,
                hold_bars=hold_bars,
            )
            rows.append(width_row)

    return pd.DataFrame(rows)


def pick_best_cqr_candidate(table: pd.DataFrame, min_trades: int = 25) -> pd.Series:
    baseline = table.loc[table['candidate'] == 'baseline'].iloc[0]
    adaptive = table.loc[table['candidate'] != 'baseline'].copy()
    eligible = adaptive.loc[
        (adaptive['trades'] >= int(min_trades))
        & (adaptive['sequential_pf'] >= float(baseline['sequential_pf']))
    ].copy()
    if eligible.empty:
        return baseline
    return eligible.sort_values(
        ['pf', 'mean_pnl_atr', 'stability_ratio', 'trades'],
        ascending=[False, False, False, False],
    ).iloc[0]
```

- [ ] **Step 4: Create the benchmark CLI**

```python
# ML/benchmark_entry_path_cqr.py
import argparse
import json
from pathlib import Path

import numpy as np
import joblib
import pandas as pd

from ML.entry_path_adaptive_conformal import load_baseline_rule, load_prediction_frame, apply_baseline_filter
from ML.entry_path_cqr import (
    fit_quantile_model,
    predict_quantile,
    compute_cqr_score,
    compute_cqr_correction,
    apply_cqr_correction,
    evaluate_candidate_grid,
    evaluate_single_candidate,
    pick_best_cqr_candidate,
)


DEFAULT_TRAIN_CSV = Path('ML/reports/entry_path_v1_train_predictions.csv')
DEFAULT_VALIDATION_CSV = Path('ML/reports/entry_path_v1_validation_predictions.csv')
DEFAULT_TEST_CSV = Path('ML/reports/entry_path_test_predictions.csv')
DEFAULT_BASELINE_RULE = Path('ML/reports/entry_path_trade_filter_selected_rule.json')
DEFAULT_OUTPUT_DIR = Path('ML/reports')


def build_report(validation_best: dict, test_row: dict, sequential_summary: dict, rule_path: str) -> str:
    return '\n'.join([
        '# Entry Path CQR Report',
        '',
        f"Победитель: **{validation_best.get('candidate', 'baseline')}**",
        '',
        '## Validation Winner',
        '',
        f"- candidate: `{validation_best.get('candidate', 'baseline')}`",
        f"- pf: **{float(validation_best.get('pf', 0.0)):.4f}**",
        f"- trades: **{int(validation_best.get('trades', 0))}**",
        '',
        '## Test Check',
        '',
        f"- candidate: `{test_row.get('candidate', 'baseline')}`",
        f"- pf: **{float(test_row.get('pf', 0.0)):.4f}**",
        f"- trades: **{int(test_row.get('trades', 0))}**",
        '',
        '## Sequential Check',
        '',
        f"- trades: **{int(sequential_summary.get('trades', 0))}**",
        f"- pf: **{float(sequential_summary.get('pf', 0.0)):.4f}**",
        '',
        '## Frozen Rule',
        '',
        f'- Rule path: `{rule_path}`',
    ])


def run_benchmark(
    train_csv,
    validation_csv,
    test_csv,
    baseline_rule_path,
    output_dir,
    alpha=0.10,
    min_trades=25,
    min_period_trades=10,
    hold_bars=24,
    lb_margins=(0.0, 0.25, 0.5),
    width_caps=(1.0, 1.5),
):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    train_frame = load_prediction_frame(train_csv)
    validation_frame = load_prediction_frame(validation_csv)
    test_frame = load_prediction_frame(test_csv)
    baseline_rule = load_baseline_rule(baseline_rule_path)

    lower_model = fit_quantile_model(train_frame, quantile_alpha=0.1)
    upper_model = fit_quantile_model(train_frame, quantile_alpha=0.9)
    joblib.dump(lower_model, output_dir / 'entry_path_cqr_lower_model.joblib')
    joblib.dump(upper_model, output_dir / 'entry_path_cqr_upper_model.joblib')

    validation_selected = apply_baseline_filter(validation_frame, baseline_rule)
    test_selected = apply_baseline_filter(test_frame, baseline_rule)

    lower_val = predict_quantile(lower_model, validation_selected)
    upper_val = predict_quantile(upper_model, validation_selected)
    correction = compute_cqr_correction(
        compute_cqr_score(
            validation_selected['true_ret_24_dir_atr'].to_numpy(dtype=np.float64),
            lower_val,
            upper_val,
        ),
        alpha=alpha,
    )
    lower_val_adj, upper_val_adj, width_val = apply_cqr_correction(lower_val, upper_val, correction)
    validation_summary = evaluate_candidate_grid(
        frame=validation_selected,
        lower=lower_val_adj,
        upper=upper_val_adj,
        width=width_val,
        correction=correction,
        lb_margins=lb_margins,
        width_caps=width_caps,
        min_period_trades=min_period_trades,
        hold_bars=hold_bars,
    )
    winner = pick_best_cqr_candidate(validation_summary, min_trades=min_trades).to_dict()

    lower_test = predict_quantile(lower_model, test_selected)
    upper_test = predict_quantile(upper_model, test_selected)
    lower_test_adj, upper_test_adj, width_test = apply_cqr_correction(lower_test, upper_test, correction)
    if winner['candidate'] == 'baseline':
        selected_mask = np.ones(len(test_selected), dtype=bool)
        score = np.ones(len(test_selected), dtype=np.float64)
        threshold = float('-inf')
        target_coverage = 1.0
        margin = None
        width_cap = None
    elif pd.isna(winner.get('width_cap')):
        margin = float(winner['margin'])
        selected_mask = lower_test_adj > margin
        score = lower_test_adj
        threshold = margin
        target_coverage = float(selected_mask.mean()) if len(selected_mask) > 0 else 0.0
        width_cap = None
    else:
        margin = float(winner['margin'])
        width_cap = float(winner['width_cap'])
        selected_mask = (lower_test_adj > margin) & (width_test <= width_cap)
        score = np.where(selected_mask, 1.0, -1.0)
        threshold = 0.0
        target_coverage = float(selected_mask.mean()) if len(selected_mask) > 0 else 0.0

    test_row, sequential_summary = evaluate_single_candidate(
        frame=test_selected,
        candidate_name=str(winner['candidate']),
        selected_mask=selected_mask,
        score=score,
        threshold=threshold,
        target_coverage=target_coverage,
        correction=correction,
        margin=margin,
        width_cap=width_cap,
        min_period_trades=min_period_trades,
        hold_bars=hold_bars,
    )

    validation_summary_path = output_dir / 'entry_path_cqr_validation_summary.csv'
    test_summary_path = output_dir / 'entry_path_cqr_test_summary.csv'
    rule_path = output_dir / 'entry_path_cqr_selected_rule.json'
    report_path = output_dir / 'entry_path_cqr_report.md'
    validation_summary.to_csv(validation_summary_path, sep=';', index=False)
    pd.DataFrame([test_row]).to_csv(test_summary_path, sep=';', index=False)

    payload = {
        'winner': winner,
        'alpha': float(alpha),
        'correction': float(correction),
        'train_csv': str(train_csv),
        'validation_csv': str(validation_csv),
        'test_csv': str(test_csv),
        'baseline_rule_path': str(baseline_rule_path),
        'validation_summary_path': str(validation_summary_path),
        'test_summary_path': str(test_summary_path),
        'sequential_summary': sequential_summary,
    }
    rule_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    report_path.write_text(build_report(winner, test_row, sequential_summary, str(rule_path)), encoding='utf-8')
    return payload
```

- [ ] **Step 5: Run the focused test to verify it passes**

Run: `/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_entry_path_cqr.py -q`

Expected: PASS for 7 tests.

- [ ] **Step 6: Commit**

```bash
git add ML/entry_path_cqr.py ML/benchmark_entry_path_cqr.py tests/test_entry_path_cqr.py
git commit -m "feat: add entry path cqr benchmark"
```

---

### Task 3: Выпустить реальные CQR-артефакты и прогнать живой benchmark

**Files:**
- Use: `ML/export_entry_path_predictions.py`
- Use: `ML/benchmark_entry_path_cqr.py`
- Produce: `ML/reports/entry_path_cqr_*`

- [ ] **Step 1: Проверить, что train/validation/test exports существуют**

Run:

```bash
ls -l ML/reports/entry_path_v1_train_predictions.csv \
      ML/reports/entry_path_v1_validation_predictions.csv \
      ML/reports/entry_path_test_predictions.csv
```

Expected: all 3 files exist.

- [ ] **Step 2: If train export is missing, rebuild all exports**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m ML.export_entry_path_predictions \
  --checkpoint ML/checkpoints/transformer_entry_path_v1_best.pt \
  --output-dir ML/reports \
  --splits train validation test \
  --seq-len 20
```

Expected: three `✅` lines for `train`, `validation`, `test`.

- [ ] **Step 3: Run the live CQR benchmark**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m ML.benchmark_entry_path_cqr \
  --train-csv ML/reports/entry_path_v1_train_predictions.csv \
  --validation-csv ML/reports/entry_path_v1_validation_predictions.csv \
  --test-csv ML/reports/entry_path_test_predictions.csv \
  --baseline-rule ML/reports/entry_path_trade_filter_selected_rule.json \
  --output-dir ML/reports
```

Expected: JSON printed to stdout with `winner`, `correction`, and artifact paths.

- [ ] **Step 4: Sanity-check the produced summaries**

Run:

```bash
sed -n '1,40p' ML/reports/entry_path_cqr_validation_summary.csv
sed -n '1,40p' ML/reports/entry_path_cqr_test_summary.csv
sed -n '1,120p' ML/reports/entry_path_cqr_report.md
```

Expected:
- validation summary contains `baseline`, `LB>0`, and width-capped candidates
- test summary contains exactly the frozen winner row
- report names the winner and shows validation/test numbers

- [ ] **Step 5: Run the focused verification suite**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest \
  tests/test_entry_path_export_predictions.py \
  tests/test_entry_path_cqr.py \
  tests/test_entry_path_trade_filter.py \
  tests/test_entry_path_model.py \
  tests/test_entry_path_training.py \
  tests/test_entry_path_reports.py -q
```

Expected: PASS for the full focused `entry_path` suite.

- [ ] **Step 6: Commit**

```bash
git add \
  ML/entry_path_cqr.py \
  ML/benchmark_entry_path_cqr.py \
  tests/test_entry_path_cqr.py \
  ML/reports/entry_path_cqr_selected_rule.json \
  ML/reports/entry_path_cqr_report.md \
  ML/reports/entry_path_cqr_validation_summary.csv \
  ML/reports/entry_path_cqr_test_summary.csv \
  ML/reports/entry_path_cqr_lower_model.joblib \
  ML/reports/entry_path_cqr_upper_model.joblib
git commit -m "feat: add entry path cqr baseline"
```
