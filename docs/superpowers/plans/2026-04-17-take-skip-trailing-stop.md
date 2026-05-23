# Take/Skip Trailing Stop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a binary `take / skip` research track for executable trailing-stop exits with `X = 2, 3, 4, 6, 8` and positive class `trail_48_pnl_atr_xN >= 0.5`.

**Architecture:** Extend the existing trailing-stop target pipeline instead of creating a parallel data path. Labeling creates continuous `trail_48_pnl_atr_xN` columns for the expanded grid, the new ML task converts them into multi-label binary targets, and benchmark uses predicted probabilities to select trades while measuring real continuous PnL.

**Tech Stack:** Python, pandas, NumPy, PyTorch, pytest, existing SoSimple `ML/train.py`, `ML/evaluate_test.py`, `API/generate_signals.py`, and report runners.

---

## Files

Create:

- `ML/take_skip_trailing_stop_task.py`: task constants, target conversion, export helpers, classification metrics.
- `ML/benchmark_take_skip_trailing_stop.py`: validation-first probability benchmark with robust trading metrics.
- `ML/run_take_skip_trailing_stop_matrix.py`: local smoke/full remote-training runner and report manifest.
- `tests/test_take_skip_trailing_stop_task.py`
- `tests/test_benchmark_take_skip_trailing_stop.py`
- `tests/test_run_take_skip_trailing_stop_matrix.py`
- `docs/reports/2026-04-17-take-skip-trailing-stop-handoff.md`: local implementation and remote-training handoff report.

Modify:

- `processing/label_signals.py`: expand trailing-stop labels from `X = 2, 3, 5` to `X = 2, 3, 4, 6, 8`.
- `processing/label_main.py`: no API change expected, only tests may require expected columns.
- `ML/trailing_stop_target_task.py`: update continuous trailing-stop target columns to the expanded grid.
- `ML/data_loader.py`: register `take_skip_trailing_stop_v1`.
- `ML/train.py`: train/validate multi-label BCE task.
- `ML/evaluate_test.py`: evaluate/export take/skip predictions on test.
- `API/generate_signals.py`: research export for validation/test probabilities and true PnL.
- `MODULE_INDEX.md`, `CHANGELOG.md`: update after local implementation.

Do not modify:

- MT4 execution.
- Production signal export defaults.
- Existing `entry_path_v1_quantile` production artifacts.

---

## Task 1: Expand Trailing-Stop Label Grid

**Files:**
- Modify: `processing/label_signals.py`
- Modify: `ML/trailing_stop_target_task.py`
- Modify: `tests/test_trailing_stop_target_labels.py`
- Modify: `tests/test_trailing_stop_target_task.py`

- [ ] **Step 1: Update tests for expanded X grid**

Add or update assertions so the expected continuous columns are exactly:

```python
expected = [
    'trail_48_pnl_atr_x2',
    'trail_48_pnl_atr_x3',
    'trail_48_pnl_atr_x4',
    'trail_48_pnl_atr_x6',
    'trail_48_pnl_atr_x8',
]
```

In `tests/test_trailing_stop_target_task.py`, assert:

```python
from ML.trailing_stop_target_task import TRAILING_STOP_TARGET_COLUMNS


def test_trailing_stop_target_columns_cover_expanded_grid():
    assert TRAILING_STOP_TARGET_COLUMNS == [
        'trail_48_pnl_atr_x2',
        'trail_48_pnl_atr_x3',
        'trail_48_pnl_atr_x4',
        'trail_48_pnl_atr_x6',
        'trail_48_pnl_atr_x8',
    ]
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest \
  tests/test_trailing_stop_target_labels.py \
  tests/test_trailing_stop_target_task.py -q
```

Expected: FAIL because current implementation still uses `X = 2, 3, 5`.

- [ ] **Step 3: Expand label generation**

In `processing/label_signals.py`, update the trailing-stop grid constant or local loop used by `label_trailing_stop_targets()` to:

```python
TRAILING_STOP_ATR_MULTIPLIERS = (2, 3, 4, 6, 8)
```

Ensure output columns are written as:

```python
for x_value in TRAILING_STOP_ATR_MULTIPLIERS:
    out.at[row_label, f'trail_48_pnl_atr_x{x_value}'] = simulate_trailing_stop_exit(
        bars=bars,
        direction=direction,
        entry_price=entry_price,
        atr=atr,
        trail_atr=float(x_value),
    )
```

In `ML/trailing_stop_target_task.py`, update:

```python
TRAILING_STOP_TARGET_COLUMNS = [
    'trail_48_pnl_atr_x2',
    'trail_48_pnl_atr_x3',
    'trail_48_pnl_atr_x4',
    'trail_48_pnl_atr_x6',
    'trail_48_pnl_atr_x8',
]
```

- [ ] **Step 4: Run tests and verify pass**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest \
  tests/test_trailing_stop_target_labels.py \
  tests/test_trailing_stop_target_task.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add processing/label_signals.py ML/trailing_stop_target_task.py \
  tests/test_trailing_stop_target_labels.py tests/test_trailing_stop_target_task.py
git commit -m "labels: expand trailing-stop target grid"
```

---

## Task 2: Add Take/Skip Task Contract

**Files:**
- Create: `ML/take_skip_trailing_stop_task.py`
- Create: `tests/test_take_skip_trailing_stop_task.py`

- [ ] **Step 1: Write task contract tests**

Create `tests/test_take_skip_trailing_stop_task.py`:

```python
import numpy as np
import pandas as pd
import pytest

from ML.take_skip_trailing_stop_task import (
    TAKE_SKIP_TRAILING_STOP_COLUMNS,
    TAKE_SKIP_TRAILING_STOP_TARGET,
    TAKE_SKIP_TRUE_PNL_COLUMNS,
    build_take_skip_export_frame,
    compute_take_skip_metrics,
    split_take_skip_targets,
)


def test_take_skip_columns_match_expanded_trailing_grid():
    assert TAKE_SKIP_TRAILING_STOP_TARGET == 'take_skip_trailing_stop_v1'
    assert TAKE_SKIP_TRAILING_STOP_COLUMNS == [
        'take_48_x2',
        'take_48_x3',
        'take_48_x4',
        'take_48_x6',
        'take_48_x8',
    ]
    assert TAKE_SKIP_TRUE_PNL_COLUMNS == [
        'trail_48_pnl_atr_x2',
        'trail_48_pnl_atr_x3',
        'trail_48_pnl_atr_x4',
        'trail_48_pnl_atr_x6',
        'trail_48_pnl_atr_x8',
    ]


def test_split_take_skip_targets_thresholds_pnl_at_half_atr():
    frame = pd.DataFrame(
        {
            'trail_48_pnl_atr_x2': [0.49, 0.50, 1.20],
            'trail_48_pnl_atr_x3': [-0.10, 0.50, 0.40],
            'trail_48_pnl_atr_x4': [0.00, 0.51, 0.49],
            'trail_48_pnl_atr_x6': [0.50, -2.00, 0.50],
            'trail_48_pnl_atr_x8': [1.00, 0.20, 0.50],
        }
    )

    y = split_take_skip_targets(frame)

    assert y.dtype == np.float32
    assert y.tolist() == [
        [0.0, 0.0, 0.0, 1.0, 1.0],
        [1.0, 1.0, 1.0, 0.0, 0.0],
        [1.0, 0.0, 0.0, 1.0, 1.0],
    ]


def test_split_take_skip_targets_fails_on_missing_columns():
    frame = pd.DataFrame({'trail_48_pnl_atr_x2': [1.0]})

    with pytest.raises(ValueError, match='missing take/skip source columns'):
        split_take_skip_targets(frame)


def test_build_take_skip_export_frame_includes_probabilities_and_true_pnl():
    export = build_take_skip_export_frame(
        times=['2026.01.01 00:00', '2026.01.02 00:00'],
        signals=[1, -1],
        pred_prob=np.array(
            [
                [0.1, 0.2, 0.3, 0.4, 0.5],
                [0.6, 0.7, 0.8, 0.9, 1.0],
            ],
            dtype=np.float32,
        ),
        true_label=np.array(
            [
                [0, 0, 0, 0, 1],
                [1, 1, 1, 1, 1],
            ],
            dtype=np.float32,
        ),
        true_pnl=np.array(
            [
                [-1.0, -0.5, 0.0, 0.4, 0.5],
                [0.6, 0.7, 0.8, 0.9, 1.0],
            ],
            dtype=np.float32,
        ),
    )

    assert list(export.columns) == [
        'time',
        'signal',
        'pred_take_48_x2',
        'pred_take_48_x3',
        'pred_take_48_x4',
        'pred_take_48_x6',
        'pred_take_48_x8',
        'true_take_48_x2',
        'true_take_48_x3',
        'true_take_48_x4',
        'true_take_48_x6',
        'true_take_48_x8',
        'true_trail_48_pnl_atr_x2',
        'true_trail_48_pnl_atr_x3',
        'true_trail_48_pnl_atr_x4',
        'true_trail_48_pnl_atr_x6',
        'true_trail_48_pnl_atr_x8',
    ]
    assert export.loc[1, 'pred_take_48_x8'] == pytest.approx(1.0)
    assert export.loc[0, 'true_trail_48_pnl_atr_x2'] == pytest.approx(-1.0)


def test_compute_take_skip_metrics_reports_positive_rates():
    y_true = np.array([[0, 1, 1, 0, 1], [1, 1, 0, 0, 0]], dtype=np.float32)
    y_prob = np.array([[0.2, 0.8, 0.7, 0.1, 0.9], [0.9, 0.6, 0.2, 0.3, 0.4]], dtype=np.float32)

    metrics = compute_take_skip_metrics(y_true, y_prob)

    assert metrics['positive_rate_take_48_x2'] == pytest.approx(0.5)
    assert metrics['positive_rate_take_48_x6'] == pytest.approx(0.0)
    assert 'brier_take_48_x3' in metrics
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_take_skip_trailing_stop_task.py -q
```

Expected: FAIL because `ML/take_skip_trailing_stop_task.py` does not exist.

- [ ] **Step 3: Implement task contract**

Create `ML/take_skip_trailing_stop_task.py`:

```python
from __future__ import annotations

import numpy as np
import pandas as pd


TAKE_SKIP_TRAILING_STOP_TARGET = 'take_skip_trailing_stop_v1'
TAKE_SKIP_THRESHOLD_ATR = 0.5
TAKE_SKIP_X_VALUES = (2, 3, 4, 6, 8)
TAKE_SKIP_TRAILING_STOP_COLUMNS = [f'take_48_x{x}' for x in TAKE_SKIP_X_VALUES]
TAKE_SKIP_TRUE_PNL_COLUMNS = [f'trail_48_pnl_atr_x{x}' for x in TAKE_SKIP_X_VALUES]


def split_take_skip_targets(df: pd.DataFrame) -> np.ndarray:
    missing = [column for column in TAKE_SKIP_TRUE_PNL_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f'missing take/skip source columns: {missing}')
    pnl = df[TAKE_SKIP_TRUE_PNL_COLUMNS].to_numpy(dtype=np.float32)
    return (pnl >= TAKE_SKIP_THRESHOLD_ATR).astype(np.float32)


def build_take_skip_export_frame(
    times,
    signals,
    pred_prob: np.ndarray,
    true_label: np.ndarray | None = None,
    true_pnl: np.ndarray | None = None,
) -> pd.DataFrame:
    pred_prob = np.asarray(pred_prob, dtype=np.float32)
    if pred_prob.ndim != 2 or pred_prob.shape[1] != len(TAKE_SKIP_TRAILING_STOP_COLUMNS):
        raise ValueError(f'pred_prob must have shape (n, {len(TAKE_SKIP_TRAILING_STOP_COLUMNS)})')

    frame = pd.DataFrame({'time': times, 'signal': signals})
    for idx, column in enumerate(TAKE_SKIP_TRAILING_STOP_COLUMNS):
        frame[f'pred_{column}'] = pred_prob[:, idx]

    if true_label is not None:
        true_label = np.asarray(true_label, dtype=np.float32)
        if true_label.shape != pred_prob.shape:
            raise ValueError(f'true_label shape {true_label.shape} does not match pred_prob shape {pred_prob.shape}')
        for idx, column in enumerate(TAKE_SKIP_TRAILING_STOP_COLUMNS):
            frame[f'true_{column}'] = true_label[:, idx]

    if true_pnl is not None:
        true_pnl = np.asarray(true_pnl, dtype=np.float32)
        if true_pnl.shape != pred_prob.shape:
            raise ValueError(f'true_pnl shape {true_pnl.shape} does not match pred_prob shape {pred_prob.shape}')
        for idx, column in enumerate(TAKE_SKIP_TRUE_PNL_COLUMNS):
            frame[f'true_{column}'] = true_pnl[:, idx]

    return frame


def compute_take_skip_metrics(y_true: np.ndarray, y_prob: np.ndarray) -> dict[str, float]:
    y_true = np.asarray(y_true, dtype=np.float32)
    y_prob = np.asarray(y_prob, dtype=np.float32)
    if y_true.shape != y_prob.shape:
        raise ValueError(f'y_true shape {y_true.shape} does not match y_prob shape {y_prob.shape}')
    if y_true.ndim != 2 or y_true.shape[1] != len(TAKE_SKIP_TRAILING_STOP_COLUMNS):
        raise ValueError(f'y_true must have shape (n, {len(TAKE_SKIP_TRAILING_STOP_COLUMNS)})')

    metrics: dict[str, float] = {}
    clipped = np.clip(y_prob, 1e-7, 1.0 - 1e-7)
    bce = -(y_true * np.log(clipped) + (1.0 - y_true) * np.log(1.0 - clipped))
    metrics['bce'] = float(np.mean(bce))
    for idx, column in enumerate(TAKE_SKIP_TRAILING_STOP_COLUMNS):
        yt = y_true[:, idx]
        yp = y_prob[:, idx]
        metrics[f'positive_rate_{column}'] = float(np.mean(yt))
        metrics[f'brier_{column}'] = float(np.mean((yp - yt) ** 2))
    return metrics
```

- [ ] **Step 4: Run tests and verify pass**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_take_skip_trailing_stop_task.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add ML/take_skip_trailing_stop_task.py tests/test_take_skip_trailing_stop_task.py
git commit -m "ml: add take-skip trailing-stop task contract"
```

---

## Task 3: Wire Data Loader, Train, Evaluate, Export

**Files:**
- Modify: `ML/data_loader.py`
- Modify: `ML/train.py`
- Modify: `ML/evaluate_test.py`
- Modify: `API/generate_signals.py`
- Test: `tests/test_take_skip_trailing_stop_task.py`

- [ ] **Step 1: Add wiring tests**

Extend `tests/test_take_skip_trailing_stop_task.py` with these tests:

```python
def test_data_loader_task_suffix_for_take_skip():
    from ML.data_loader import task_checkpoint_suffix

    assert task_checkpoint_suffix('take_skip_trailing_stop_v1') == '_take_skip_trailing_stop_v1'


def test_generate_signals_accepts_take_skip_research_task_constant():
    from API.generate_signals import RESEARCH_EXPORT_TASKS

    assert 'take_skip_trailing_stop_v1' in RESEARCH_EXPORT_TASKS
```

If `RESEARCH_EXPORT_TASKS` does not exist yet, Task 3 must create it as a small explicit set in `API/generate_signals.py` near the CLI task validation logic.

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_take_skip_trailing_stop_task.py -q
```

Expected: FAIL because the new task is not registered.

- [ ] **Step 3: Register task in data loader**

In `ML/data_loader.py`:

Import:

```python
from ML.take_skip_trailing_stop_task import (
    TAKE_SKIP_TRAILING_STOP_TARGET,
    split_take_skip_targets,
)
```

Add to task alias/checkpoint suffix sections:

```python
TAKE_SKIP_TRAILING_STOP_TARGET: TAKE_SKIP_TRAILING_STOP_TARGET
```

and:

```python
TAKE_SKIP_TRAILING_STOP_TARGET: '_take_skip_trailing_stop_v1'
```

In train/validation/test load paths, add:

```python
take_skip_trailing_stop = (target == TAKE_SKIP_TRAILING_STOP_TARGET)
```

Use:

```python
elif take_skip_trailing_stop:
    y = split_take_skip_targets(df)
```

Cache validation for this task must require:

```python
y.ndim == 2 and y.shape[1] == 5
```

Weighted sampler should be disabled for this task in the first implementation:

```python
if use_weighted_sampler and not regression and not entry_path and not trailing_stop_quantile and not take_skip_trailing_stop:
    ...
```

- [ ] **Step 4: Add train loop support**

In `ML/train.py`:

Import:

```python
from ML.take_skip_trailing_stop_task import (
    TAKE_SKIP_TRAILING_STOP_COLUMNS,
    TAKE_SKIP_TRAILING_STOP_TARGET,
    compute_take_skip_metrics,
)
```

Treat task as multi-label classification:

```python
take_skip_trailing_stop = (task == TAKE_SKIP_TRAILING_STOP_TARGET)
```

For model creation:

```python
elif take_skip_trailing_stop:
    num_classes = len(TAKE_SKIP_TRAILING_STOP_COLUMNS)
```

Use existing transformer output shape `(batch, num_classes)`.

Add training/validation helpers:

```python
def train_one_epoch_take_skip(model, loader, criterion, optimizer, device):
    model.train()
    total_loss = 0.0
    for batch in loader:
        if len(batch) == 3:
            x_batch, y_batch, mask = batch
        else:
            x_batch, y_batch = batch
            mask = None
        x_batch = x_batch.to(device)
        y_batch = y_batch.to(device).float()
        mask = mask.to(device) if mask is not None else None
        optimizer.zero_grad()
        logits = model(x_batch, mask=mask) if mask is not None else model(x_batch)
        loss = criterion(logits, y_batch)
        loss.backward()
        optimizer.step()
        total_loss += float(loss.item())
    return total_loss / max(1, len(loader))
```

```python
def validate_take_skip(model, loader, criterion, device):
    model.eval()
    total_loss = 0.0
    y_true_parts = []
    y_prob_parts = []
    with torch.no_grad():
        for batch in loader:
            if len(batch) == 3:
                x_batch, y_batch, mask = batch
            else:
                x_batch, y_batch = batch
                mask = None
            x_batch = x_batch.to(device)
            y_batch = y_batch.to(device).float()
            mask = mask.to(device) if mask is not None else None
            logits = model(x_batch, mask=mask) if mask is not None else model(x_batch)
            loss = criterion(logits, y_batch)
            total_loss += float(loss.item())
            y_true_parts.append(y_batch.cpu().numpy())
            y_prob_parts.append(torch.sigmoid(logits).cpu().numpy())
    metrics = compute_take_skip_metrics(np.vstack(y_true_parts), np.vstack(y_prob_parts))
    metrics['val_score'] = -metrics['bce']
    return total_loss / max(1, len(loader)), metrics
```

Use:

```python
criterion = torch.nn.BCEWithLogitsLoss()
```

The first version does not need `pos_weight`; add `pos_weight` only if it is already easy to calculate cleanly from train labels.

- [ ] **Step 5: Add evaluate/export support**

In `ML/evaluate_test.py`, for `TAKE_SKIP_TRAILING_STOP_TARGET`:

- load test labels with `target=TAKE_SKIP_TRAILING_STOP_TARGET`;
- run model logits;
- convert to probabilities with `torch.sigmoid`;
- compute `compute_take_skip_metrics`;
- write a compact markdown report named:

```text
ML/reports/evaluate_test_take_skip_trailing_stop_v1.md
```

In `API/generate_signals.py`, add research export support:

```python
if task == TAKE_SKIP_TRAILING_STOP_TARGET:
    if not research_out_prefix:
        raise ValueError('Для take_skip_trailing_stop_v1 нужен --research-out-prefix')
    ...
```

Export validation/test CSVs with:

- `pred_take_48_xN`;
- `true_take_48_xN`;
- `true_trail_48_pnl_atr_xN`.

Use `build_take_skip_export_frame()`.

- [ ] **Step 6: Run focused tests**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_take_skip_trailing_stop_task.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add ML/data_loader.py ML/train.py ML/evaluate_test.py API/generate_signals.py tests/test_take_skip_trailing_stop_task.py
git commit -m "ml: wire take-skip trailing-stop task"
```

---

## Task 4: Add Probability Benchmark

**Files:**
- Create: `ML/benchmark_take_skip_trailing_stop.py`
- Create: `tests/test_benchmark_take_skip_trailing_stop.py`

- [ ] **Step 1: Write benchmark tests**

Create `tests/test_benchmark_take_skip_trailing_stop.py`:

```python
import pandas as pd
import pytest

from ML.benchmark_take_skip_trailing_stop import (
    build_candidate_table,
    pick_validation_winner,
    run_benchmark,
    summarize_candidate,
)


def _frame():
    return pd.DataFrame(
        {
            'time': ['2024.01.01 00:00', '2025.01.01 00:00', '2026.01.01 00:00'],
            'signal': [0, 1, 0],
            'pred_take_48_x4': [0.1, 0.9, 0.2],
            'true_take_48_x4': [0, 1, 0],
            'true_trail_48_pnl_atr_x4': [0.0, 1.2, 0.0],
        }
    )


def test_summarize_candidate_uses_full_split_coverage():
    row = summarize_candidate(
        _frame(),
        target_column='take_48_x4',
        candidate='prob_ge_threshold',
        threshold=0.8,
        coverage_years=3,
    )

    assert row['trades'] == 1
    assert row['pf'] == float('inf')
    assert row['trades_per_year'] == pytest.approx(1.0 / 3.0)
    assert row['positive_rate_selected'] == pytest.approx(1.0)


def test_build_candidate_table_contains_threshold_and_topk_candidates():
    table = build_candidate_table(_frame(), target_column='take_48_x4')

    assert {'prob_ge_threshold', 'top_k_probability'} <= set(table['candidate'])
    assert 'profit_concentration_top_10' in table.columns
    assert 'max_drawdown_atr' in table.columns


def test_benchmark_fails_fast_on_bad_dates(tmp_path):
    validation = _frame()
    test = _frame()
    test.loc[2, 'time'] = 'bad-date'
    validation_csv = tmp_path / 'validation.csv'
    test_csv = tmp_path / 'test.csv'
    validation.to_csv(validation_csv, sep=';', index=False)
    test.to_csv(test_csv, sep=';', index=False)

    with pytest.raises(ValueError, match='unparseable time'):
        run_benchmark(
            validation_csv=validation_csv,
            test_csv=test_csv,
            output_dir=tmp_path / 'benchmark',
            min_pf=1.0,
            min_trades_per_year=0.1,
        )


def test_run_benchmark_selects_on_validation_and_freezes_to_test(tmp_path):
    validation = pd.DataFrame(
        {
            'time': ['2025.01.01 00:00', '2025.01.02 00:00'],
            'signal': [1, 1],
            'pred_take_48_x4': [0.9, 0.2],
            'true_take_48_x4': [1, 0],
            'true_trail_48_pnl_atr_x4': [1.0, -1.0],
        }
    )
    test = pd.DataFrame(
        {
            'time': ['2026.01.01 00:00', '2026.01.02 00:00'],
            'signal': [1, 1],
            'pred_take_48_x4': [0.95, 0.1],
            'true_take_48_x4': [1, 0],
            'true_trail_48_pnl_atr_x4': [0.8, -0.6],
        }
    )
    validation_csv = tmp_path / 'validation.csv'
    test_csv = tmp_path / 'test.csv'
    validation.to_csv(validation_csv, sep=';', index=False)
    test.to_csv(test_csv, sep=';', index=False)

    result = run_benchmark(
        validation_csv=validation_csv,
        test_csv=test_csv,
        output_dir=tmp_path / 'benchmark',
        min_pf=1.0,
        min_trades_per_year=0.1,
        targets=('take_48_x4',),
    )

    assert result['final_verdict']['verdict'] == 'go'
    assert result['final_verdict']['validation_winner']['target_column'] == 'take_48_x4'
    assert result['final_verdict']['test_result']['trades'] == 1
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_take_skip_trailing_stop.py -q
```

Expected: FAIL because benchmark module does not exist.

- [ ] **Step 3: Implement benchmark**

Create `ML/benchmark_take_skip_trailing_stop.py` with:

- fail-fast `_parse_time_column(frame)`;
- `_coverage_years(frame)` from full split;
- `_active_rows(frame)` using `signal != 0`;
- `_profit_factor(pnl)`;
- `_profit_concentration_top_10(pnl)`;
- `_max_drawdown_atr(pnl)`;
- `summarize_candidate(frame, target_column, candidate, threshold, coverage_years)`;
- `build_candidate_table(frame, target_column, thresholds, top_k_values)`;
- `pick_validation_winner(table, min_pf, min_trades_per_year)`;
- `run_benchmark(validation_csv, test_csv, output_dir, min_pf, min_trades_per_year, targets)`.

Required column naming:

```python
score_col = f'pred_{target_column}'
label_col = f'true_{target_column}'
pnl_col = f"true_trail_48_pnl_atr_x{target_column.rsplit('x', 1)[1]}"
```

Default candidate grids:

```python
DEFAULT_THRESHOLDS = (0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95)
DEFAULT_TOP_K = (0.005, 0.01, 0.02, 0.03, 0.05, 0.075, 0.10)
```

Selection sort:

```python
eligible.sort_values(
    ['pf', 'negative_year_slices', 'max_drawdown_atr', 'trades'],
    ascending=[False, True, True, False],
)
```

- [ ] **Step 4: Run tests and verify pass**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_take_skip_trailing_stop.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add ML/benchmark_take_skip_trailing_stop.py tests/test_benchmark_take_skip_trailing_stop.py
git commit -m "ml: add take-skip trailing-stop benchmark"
```

---

## Task 5: Add Matrix Runner And Smoke Handoff

**Files:**
- Create: `ML/run_take_skip_trailing_stop_matrix.py`
- Create: `tests/test_run_take_skip_trailing_stop_matrix.py`
- Create: `docs/reports/2026-04-17-take-skip-trailing-stop-handoff.md`
- Modify: `MODULE_INDEX.md`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Write runner tests**

Create `tests/test_run_take_skip_trailing_stop_matrix.py`:

```python
import json

import pandas as pd
import pytest

from ML.run_take_skip_trailing_stop_matrix import config_slug, run_single_config


def test_config_slug():
    assert config_slug(20) == 'transformer_seq20'


def test_single_config_writes_summary_and_benchmark(monkeypatch, tmp_path):
    import ML.run_take_skip_trailing_stop_matrix as runner

    checkpoint_dir = tmp_path / 'checkpoints'
    reports_dir = tmp_path / 'reports'
    checkpoint_dir.mkdir()
    reports_dir.mkdir()
    monkeypatch.setattr(runner, 'CHECKPOINTS_DIR', checkpoint_dir)
    monkeypatch.setattr(runner, 'REPORTS_DIR', reports_dir)

    def fake_train_model(**kwargs):
        assert kwargs['task'] == 'take_skip_trailing_stop_v1'
        assert kwargs['seq_len'] == 20
        (checkpoint_dir / 'transformer_take_skip_trailing_stop_v1_best.pt').write_bytes(b'checkpoint')
        return {'best_metric': -0.1, 'task': kwargs['task']}

    def fake_run_evaluation(**kwargs):
        assert kwargs['task'] == 'take_skip_trailing_stop_v1'
        assert kwargs['seq_len_override'] == 20
        (reports_dir / 'evaluate_test_take_skip_trailing_stop_v1.md').write_text('ok', encoding='utf-8')

    def fake_generate_signals(**kwargs):
        prefix = runner.Path(kwargs['research_out_prefix'])
        frame = pd.DataFrame(
            {
                'time': ['2025.01.01 00:00', '2025.01.02 00:00'],
                'signal': [1, 1],
                'pred_take_48_x2': [0.9, 0.1],
                'pred_take_48_x3': [0.9, 0.1],
                'pred_take_48_x4': [0.9, 0.1],
                'pred_take_48_x6': [0.9, 0.1],
                'pred_take_48_x8': [0.9, 0.1],
                'true_take_48_x2': [1, 0],
                'true_take_48_x3': [1, 0],
                'true_take_48_x4': [1, 0],
                'true_take_48_x6': [1, 0],
                'true_take_48_x8': [1, 0],
                'true_trail_48_pnl_atr_x2': [1.0, -1.0],
                'true_trail_48_pnl_atr_x3': [1.0, -1.0],
                'true_trail_48_pnl_atr_x4': [1.0, -1.0],
                'true_trail_48_pnl_atr_x6': [1.0, -1.0],
                'true_trail_48_pnl_atr_x8': [1.0, -1.0],
            }
        )
        frame.to_csv(prefix.parent / f'{prefix.name}_validation_predictions.csv', sep=';', index=False)
        frame.to_csv(prefix.parent / f'{prefix.name}_test_predictions.csv', sep=';', index=False)

    monkeypatch.setattr(runner, 'train_model', fake_train_model)
    monkeypatch.setattr(runner, 'run_evaluation', fake_run_evaluation)
    monkeypatch.setattr(runner, 'generate_signals', fake_generate_signals)

    result = run_single_config(
        seq_len=20,
        output_dir=tmp_path / 'matrix',
        epochs=1,
        patience=1,
        batch_size=8,
        seed=42,
        min_pf=1.0,
        min_trades_per_year=0.1,
        skip_existing=False,
    )

    summary = tmp_path / 'matrix' / 'transformer_seq20' / 'summary.json'
    assert summary.exists()
    saved = json.loads(summary.read_text(encoding='utf-8'))
    assert saved['config']['seq_len'] == 20
    assert result['benchmark']['final_verdict']['verdict'] == 'go'


def test_single_config_fails_when_checkpoint_missing(monkeypatch, tmp_path):
    import ML.run_take_skip_trailing_stop_matrix as runner

    checkpoint_dir = tmp_path / 'checkpoints'
    reports_dir = tmp_path / 'reports'
    checkpoint_dir.mkdir()
    reports_dir.mkdir()
    monkeypatch.setattr(runner, 'CHECKPOINTS_DIR', checkpoint_dir)
    monkeypatch.setattr(runner, 'REPORTS_DIR', reports_dir)
    monkeypatch.setattr(runner, 'train_model', lambda **kwargs: {'best_metric': -0.1})

    with pytest.raises(FileNotFoundError, match='required checkpoint'):
        run_single_config(
            seq_len=20,
            output_dir=tmp_path / 'matrix',
            epochs=1,
            patience=1,
            batch_size=8,
            seed=42,
            min_pf=1.0,
            min_trades_per_year=0.1,
            skip_existing=False,
        )
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_run_take_skip_trailing_stop_matrix.py -q
```

Expected: FAIL because runner does not exist.

- [ ] **Step 3: Implement runner**

Create `ML/run_take_skip_trailing_stop_matrix.py`.

Required CLI:

```text
--output-dir
--seq-lens
--epochs
--patience
--batch-size
--seed
--min-pf
--min-trades-per-year
--skip-existing
```

Use task:

```python
TAKE_SKIP_TRAILING_STOP_TARGET
```

Use required checkpoint copy:

```python
def _copy_required(source: Path, destination: Path, label: str) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        destination.unlink()
    if not source.exists():
        raise FileNotFoundError(f'required {label} missing: {source}')
    shutil.copy2(source, destination)
```

Run sequence:

1. `train_model(model_name='transformer', task=TAKE_SKIP_TRAILING_STOP_TARGET, seq_len=seq_len, ...)`
2. copy checkpoint to run dir
3. `run_evaluation(..., seq_len_override=seq_len)`
4. `generate_signals(..., research_out_prefix=run_dir / 'take_skip_trailing_stop', seq_len_override=seq_len)`
5. `run_benchmark(...)`
6. write `summary.json`
7. top-level `main()` writes `manifest.json`

- [ ] **Step 4: Update docs indexes**

Add to `MODULE_INDEX.md`:

```md
| [take_skip_trailing_stop_task.py](ML/take_skip_trailing_stop_task.py) | Take/skip task для trailing-stop exits `X=2/3/4/6/8` | trailing PnL columns → binary labels/probability exports | — | ✅ |
| [benchmark_take_skip_trailing_stop.py](ML/benchmark_take_skip_trailing_stop.py) | Validation-first benchmark для take/skip trailing-stop probabilities | prediction CSVs → validation/test verdict | — | ✅ |
| [run_take_skip_trailing_stop_matrix.py](ML/run_take_skip_trailing_stop_matrix.py) | Оркестратор локального smoke и серверного matrix run | config → `reports/take_skip_trailing_stop_matrix` | — | ✅ |
```

Add to `CHANGELOG.md`:

```md
## [2026-04-17] - Take/skip trailing-stop track scaffold

### Добавлено
- `take_skip_trailing_stop_v1` для бинарного отбора сделок по `trail_48_pnl_atr_xN >= 0.5`
- широкая сетка `X = 2, 3, 4, 6, 8`
- benchmark и runner для удалённого обучения

### Статус
- локальный smoke готов
- heavy matrix должен запускаться на удалённом сервере
```

Create `docs/reports/2026-04-17-take-skip-trailing-stop-handoff.md`:

```md
# Take/Skip Trailing Stop Handoff

> **Date**: 2026-04-17
> **Status**: Ready for remote training

## Local Verification

Commands and results:

- `pytest ...`

## Remote Command

```bash
MPLCONFIGDIR=/tmp/matplotlib /path/to/.venv/bin/python \
  -m ML.run_take_skip_trailing_stop_matrix \
  --output-dir ML/reports/take_skip_trailing_stop_matrix \
  --seq-lens 20 50 100 \
  --epochs 10 \
  --patience 4 \
  --batch-size 256 \
  --min-pf 1.0 \
  --min-trades-per-year 6
```

## Expected Artifacts

- `ML/reports/take_skip_trailing_stop_matrix/manifest.json`
- per-run `summary.json`
- per-run `benchmark/final_verdict.json`
- per-run `benchmark/validation_grid.csv`
- prediction CSVs for validation/test
```

- [ ] **Step 5: Run focused tests**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest \
  tests/test_take_skip_trailing_stop_task.py \
  tests/test_benchmark_take_skip_trailing_stop.py \
  tests/test_run_take_skip_trailing_stop_matrix.py -q
```

Expected: PASS.

- [ ] **Step 6: Run local smoke**

Run:

```bash
MPLCONFIGDIR=/tmp/matplotlib /home/hohla/git/SoSimple/.venv/bin/python \
  -m ML.run_take_skip_trailing_stop_matrix \
  --output-dir ML/reports/take_skip_trailing_stop_matrix_smoke \
  --seq-lens 20 \
  --epochs 1 \
  --patience 1 \
  --batch-size 256 \
  --min-pf 1.0 \
  --min-trades-per-year 6
```

Expected:

- command exits 0;
- `ML/reports/take_skip_trailing_stop_matrix_smoke/manifest.json` exists;
- no claim is made about trading quality from this smoke run.

- [ ] **Step 7: Commit**

```bash
git add ML/run_take_skip_trailing_stop_matrix.py \
  tests/test_run_take_skip_trailing_stop_matrix.py \
  MODULE_INDEX.md CHANGELOG.md \
  docs/reports/2026-04-17-take-skip-trailing-stop-handoff.md
git commit -m "ml: add take-skip trailing-stop matrix runner"
```

---

## Task 6: Stop Before Heavy Remote Training

**Files:**
- No code changes unless smoke artifacts are intentionally recorded.

- [ ] **Step 1: Run final local verification**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest \
  tests/test_trailing_stop_target_labels.py \
  tests/test_trailing_stop_target_task.py \
  tests/test_take_skip_trailing_stop_task.py \
  tests/test_benchmark_take_skip_trailing_stop.py \
  tests/test_run_take_skip_trailing_stop_matrix.py -q
```

Expected: PASS.

- [ ] **Step 2: Check git status**

Run:

```bash
git status --short
```

Expected: no uncommitted source changes, except ignored/generated smoke artifacts if intentionally left out.

- [ ] **Step 3: Stop and hand off to user**

Report exactly:

```text
Код готов к удалённому обучению.

Нужно:
1. git push
2. На сервере: git pull
3. Проверить, что DATA/ актуальна
4. Запустить:

MPLCONFIGDIR=/tmp/matplotlib /path/to/.venv/bin/python \
  -m ML.run_take_skip_trailing_stop_matrix \
  --output-dir ML/reports/take_skip_trailing_stop_matrix \
  --seq-lens 20 50 100 \
  --epochs 10 \
  --patience 4 \
  --batch-size 256 \
  --min-pf 1.0 \
  --min-trades-per-year 6
```

Do not run the full matrix locally.
