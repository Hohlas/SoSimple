# Trailing-Stop Target Retraining Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Построить новый ML-трек, в котором модель учится предсказывать итог сделки при простом исполнимом правиле выхода `stop = trailing_stop = X * ATR`, и проверить матрицу `X={2,3,5} × seq_len={20,50,100}` по strict validation-first benchmark.

**Architecture:** План добавляет новое семейство path-dependent target-ов в labeling layer, протягивает его через `entry_path`-style training/export stack и создаёт короткий benchmark для выбора winner только на validation. Первый проход deliberately ограничен одной архитектурой `EntryPathTransformer`, без нового architecture sweep и без дополнительных objective families.

**Tech Stack:** Python 3.11, pandas, numpy, torch, pytest, существующие модули `processing/label_signals.py`, `processing/label_main.py`, `ML/data_loader.py`, `ML/train.py`, `ML/evaluate_test.py`, `API/generate_signals.py`

---

## File Structure

### Read First

- `docs/superpowers/specs/2026-04-16-trailing-stop-target-design.md`
- `processing/label_signals.py`
- `processing/label_main.py`
- `ML/entry_path_task.py`
- `ML/data_loader.py`
- `ML/train.py`
- `ML/evaluate_test.py`
- `API/generate_signals.py`
- `ML/run_track_a_max_out_matrix.py`

### Files To Create

- `ML/trailing_stop_target_task.py`
- `ML/benchmark_trailing_stop_target.py`
- `ML/run_trailing_stop_target_matrix.py`
- `tests/test_trailing_stop_target_labels.py`
- `tests/test_trailing_stop_target_task.py`
- `tests/test_benchmark_trailing_stop_target.py`
- `tests/test_run_trailing_stop_target_matrix.py`
- `docs/reports/2026-04-16-trailing-stop-target-first-wave.md`

### Files To Modify

- `processing/label_signals.py`
- `processing/label_main.py`
- `ML/data_loader.py`
- `ML/train.py`
- `ML/evaluate_test.py`
- `API/generate_signals.py`
- `MODULE_INDEX.md`

### Files To Update After Implementation

- `DATA/Nero_train_labeled.csv`
- `DATA/Nero_validation_labeled.csv`
- `DATA/Nero_test_labeled.csv`
- `ML/reports/trailing_stop_target_matrix/*`
- `ML/checkpoints/transformer_trailing_stop_target_*.pt`

---

### Task 1: Add Trailing-Stop Label Family To The Labeling Layer

**Files:**
- Modify: `processing/label_signals.py`
- Modify: `processing/label_main.py`
- Create: `tests/test_trailing_stop_target_labels.py`

- [ ] **Step 1: Write the failing test for the new target columns**

```python
# tests/test_trailing_stop_target_labels.py
import pandas as pd
import processing.label_signals as ls


def test_label_trailing_stop_targets_adds_x2_x3_x5_columns():
    frame = pd.DataFrame(
        {
            'time': ['2025.01.01 00:00'],
            'signal': [1],
            'ATR': [10.0],
            'Close': [100.0],
            'High': [100.0],
            'Low': [100.0],
            'Close_1': [103.0],
            'High_1': [105.0],
            'Low_1': [99.0],
            'Close_2': [104.0],
            'High_2': [106.0],
            'Low_2': [102.0],
        }
    )

    out = ls.label_trailing_stop_targets(frame.copy(), hold_bars=2, atr_col='ATR', x_values=(2, 3, 5))

    assert 'trail_48_pnl_atr_x2' in out.columns
    assert 'trail_48_pnl_atr_x3' in out.columns
    assert 'trail_48_pnl_atr_x5' in out.columns
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_trailing_stop_target_labels.py::test_label_trailing_stop_targets_adds_x2_x3_x5_columns -q
```

Expected: FAIL with `AttributeError: module 'processing.label_signals' has no attribute 'label_trailing_stop_targets'`.

- [ ] **Step 3: Add a second failing test for the path-dependent exit rule**

```python
def test_simulate_trailing_stop_exit_buy_closes_on_retrace_from_best_high():
    bars = [
        {'high': 105.0, 'low': 99.0, 'close': 104.0},
        {'high': 112.0, 'low': 103.0, 'close': 111.0},
        {'high': 110.0, 'low': 101.0, 'close': 102.0},
    ]

    pnl_atr = ls.simulate_trailing_stop_exit(
        bars=bars,
        direction=1,
        entry_price=100.0,
        atr=2.0,
        trail_atr=3.0,
    )

    assert pnl_atr == 3.5
```

- [ ] **Step 4: Run the test to verify it fails**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_trailing_stop_target_labels.py::test_simulate_trailing_stop_exit_buy_closes_on_retrace_from_best_high -q
```

Expected: FAIL with `AttributeError`.

- [ ] **Step 5: Implement the minimal simulator helpers**

Add to `processing/label_signals.py`:

```python
TRAILING_STOP_X_VALUES = (2, 3, 5)
TRAILING_STOP_HOLD_BARS = 48


def simulate_trailing_stop_exit(bars, direction, entry_price, atr, trail_atr):
    if atr <= 0:
        return 0.0
    trail_distance = float(trail_atr) * float(atr)
    best_move = 0.0
    exit_price = entry_price

    for bar in bars:
        high = float(bar['high'])
        low = float(bar['low'])
        close = float(bar['close'])
        if direction == 1:
            best_move = max(best_move, high - entry_price)
            stop_price = entry_price + best_move - trail_distance
            if low <= stop_price:
                exit_price = stop_price
                break
            exit_price = close
        else:
            best_move = max(best_move, entry_price - low)
            stop_price = entry_price - best_move + trail_distance
            if high >= stop_price:
                exit_price = stop_price
                break
            exit_price = close

    return float((exit_price - entry_price) / atr) if direction == 1 else float((entry_price - exit_price) / atr)
```

- [ ] **Step 6: Implement the label builder**

Add to `processing/label_signals.py`:

```python
def label_trailing_stop_targets(
    df: pd.DataFrame,
    hold_bars: int = TRAILING_STOP_HOLD_BARS,
    atr_col: str = 'ATR',
    x_values: tuple[int, ...] = TRAILING_STOP_X_VALUES,
) -> pd.DataFrame:
    out = df.copy()
    for x_value in x_values:
        out[f'trail_48_pnl_atr_x{x_value}'] = 0.0

    for row_idx in range(len(out)):
        signal = int(pd.to_numeric(out.at[row_idx, 'signal'], errors='coerce') or 0)
        if signal == 0:
            continue
        atr = float(pd.to_numeric(out.at[row_idx, atr_col], errors='coerce') or 0.0)
        entry_price = float(pd.to_numeric(out.at[row_idx, 'Close'], errors='coerce') or 0.0)
        bars = []
        for step in range(1, hold_bars + 1):
            suffix = f'_{step}'
            high_col = f'High{suffix}'
            low_col = f'Low{suffix}'
            close_col = f'Close{suffix}'
            if high_col not in out.columns or low_col not in out.columns or close_col not in out.columns:
                break
            bars.append(
                {
                    'high': float(pd.to_numeric(out.at[row_idx, high_col], errors='coerce') or entry_price),
                    'low': float(pd.to_numeric(out.at[row_idx, low_col], errors='coerce') or entry_price),
                    'close': float(pd.to_numeric(out.at[row_idx, close_col], errors='coerce') or entry_price),
                }
            )
        for x_value in x_values:
            out.at[row_idx, f'trail_48_pnl_atr_x{x_value}'] = simulate_trailing_stop_exit(
                bars=bars,
                direction=signal,
                entry_price=entry_price,
                atr=atr,
                trail_atr=float(x_value),
            )
    return out
```

- [ ] **Step 7: Wire the label builder into the main labeling pipeline**

In `processing/label_main.py`, immediately after existing entry-path labels are added:

```python
from processing.label_signals import label_trailing_stop_targets


labeled_df = label_trailing_stop_targets(labeled_df)
```

- [ ] **Step 8: Run the new tests**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_trailing_stop_target_labels.py -q
```

Expected: PASS.

- [ ] **Step 9: Commit**

```bash
git add processing/label_signals.py processing/label_main.py tests/test_trailing_stop_target_labels.py
git commit -m "labels: add trailing-stop target family"
```

### Task 2: Register A Dedicated Training Task For The New Target Family

**Files:**
- Create: `ML/trailing_stop_target_task.py`
- Modify: `ML/data_loader.py`
- Modify: `ML/train.py`
- Modify: `ML/evaluate_test.py`
- Modify: `API/generate_signals.py`
- Create: `tests/test_trailing_stop_target_task.py`

- [ ] **Step 1: Write the failing test for task constants and export contract**

```python
# tests/test_trailing_stop_target_task.py
import numpy as np
import pandas as pd

from ML.trailing_stop_target_task import (
    TRAILING_STOP_TARGET,
    TRAILING_STOP_TARGET_COLUMNS,
    build_trailing_stop_export_frame,
)


def test_trailing_stop_task_constants_match_design():
    assert TRAILING_STOP_TARGET == 'trailing_stop_target_v1'
    assert TRAILING_STOP_TARGET_COLUMNS == [
        'trail_48_pnl_atr_x2',
        'trail_48_pnl_atr_x3',
        'trail_48_pnl_atr_x5',
    ]


def test_build_trailing_stop_export_frame_adds_pred_columns():
    frame = build_trailing_stop_export_frame(
        times=np.array(['2025.01.01 00:00']),
        signals=np.array([1]),
        pred=np.array([[0.1, 0.2, 0.3]], dtype=np.float32),
        true=np.array([[0.4, 0.5, 0.6]], dtype=np.float32),
    )
    assert list(frame.columns) == [
        'time',
        'signal',
        'pred_trail_48_pnl_atr_x2',
        'pred_trail_48_pnl_atr_x3',
        'pred_trail_48_pnl_atr_x5',
        'true_trail_48_pnl_atr_x2',
        'true_trail_48_pnl_atr_x3',
        'true_trail_48_pnl_atr_x5',
    ]
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_trailing_stop_target_task.py::test_trailing_stop_task_constants_match_design -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'ML.trailing_stop_target_task'`.

- [ ] **Step 3: Create the task helper module**

Create `ML/trailing_stop_target_task.py`:

```python
import numpy as np
import pandas as pd


TRAILING_STOP_TARGET = 'trailing_stop_target_v1'
TRAILING_STOP_TARGET_COLUMNS = [
    'trail_48_pnl_atr_x2',
    'trail_48_pnl_atr_x3',
    'trail_48_pnl_atr_x5',
]


def split_trailing_stop_targets(df: pd.DataFrame) -> np.ndarray:
    return df[TRAILING_STOP_TARGET_COLUMNS].values.astype(np.float32)


def build_trailing_stop_export_frame(times, signals, pred, true=None) -> pd.DataFrame:
    frame = pd.DataFrame({'time': times, 'signal': signals})
    for idx, column in enumerate(TRAILING_STOP_TARGET_COLUMNS):
        frame[f'pred_{column}'] = pred[:, idx]
    if true is not None:
        for idx, column in enumerate(TRAILING_STOP_TARGET_COLUMNS):
            frame[f'true_{column}'] = true[:, idx]
    return frame
```

- [ ] **Step 4: Register the new task in the data loader**

Add to `ML/data_loader.py`:

```python
from ML.trailing_stop_target_task import TRAILING_STOP_TARGET, split_trailing_stop_targets

TASK_CHECKPOINT_SUFFIXES[TRAILING_STOP_TARGET] = '_trailing_stop_target_v1'
TASK_TARGET_COLUMNS[TRAILING_STOP_TARGET] = TRAILING_STOP_TARGET
SIGNAL_ONLY_TARGET_COLUMNS.add(TRAILING_STOP_TARGET)
SINGLE_REGRESSION_COLUMNS.add(TRAILING_STOP_TARGET)
```

In `create_data_loaders()`, add:

```python
if target == TRAILING_STOP_TARGET:
    y_train = split_trailing_stop_targets(train_df)
    y_val = split_trailing_stop_targets(val_df)
```

- [ ] **Step 5: Register the task in training and evaluation CLIs**

In `ML/train.py` parser choices:

```python
from ML.trailing_stop_target_task import TRAILING_STOP_TARGET, TRAILING_STOP_TARGET_COLUMNS

parser.add_argument(
    '--task',
    choices=[
        'classification',
        'regression',
        'regression_updn',
        'triple_barrier',
        'entry_path_v1',
        'entry_path_v1_quantile',
        'trade_outcome_cls',
        'trade_pnl_reg',
        'signal_archetype_cls',
        TRAILING_STOP_TARGET,
    ],
)
```

In the task-specific branch:

```python
if task == TRAILING_STOP_TARGET:
    model = build_entry_path_model(model_name, model_kwargs)
    regression = True
```

In `ML/evaluate_test.py` and `API/generate_signals.py`, add the same task import and route to `build_trailing_stop_export_frame(...)`.

- [ ] **Step 6: Run the task tests**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_trailing_stop_target_task.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add ML/trailing_stop_target_task.py ML/data_loader.py ML/train.py ML/evaluate_test.py API/generate_signals.py tests/test_trailing_stop_target_task.py
git commit -m "ml: register trailing-stop target task"
```

### Task 3: Build A Validation-First Benchmark For The New Target

**Files:**
- Create: `ML/benchmark_trailing_stop_target.py`
- Create: `tests/test_benchmark_trailing_stop_target.py`

- [ ] **Step 1: Write the failing test for winner selection**

```python
# tests/test_benchmark_trailing_stop_target.py
import pandas as pd

from ML.benchmark_trailing_stop_target import pick_validation_winner


def test_pick_validation_winner_prefers_pf_then_lower_ulcer():
    frame = pd.DataFrame(
        [
            {'candidate': 'a', 'pf': 1.10, 'ulcer_index_atr': 50.0, 'trades': 120},
            {'candidate': 'b', 'pf': 1.10, 'ulcer_index_atr': 40.0, 'trades': 120},
            {'candidate': 'c', 'pf': 0.95, 'ulcer_index_atr': 10.0, 'trades': 120},
        ]
    )

    winner = pick_validation_winner(frame)

    assert winner['candidate'] == 'b'
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_trailing_stop_target.py::test_pick_validation_winner_prefers_pf_then_lower_ulcer -q
```

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Add the benchmark module**

Create `ML/benchmark_trailing_stop_target.py`:

```python
import pandas as pd


def summarize_candidate(frame: pd.DataFrame, score_col: str, threshold: float) -> dict[str, float]:
    live = frame.loc[frame[score_col] >= threshold].copy()
    pnl = live['true_trail_48_pnl_atr_x3'].to_numpy(dtype=float)
    gross_profit = float(pnl[pnl > 0].sum())
    gross_loss = float(-pnl[pnl < 0].sum())
    pf = gross_profit / gross_loss if gross_loss > 0 else (float('inf') if gross_profit > 0 else 0.0)
    return {
        'candidate': score_col,
        'threshold': float(threshold),
        'trades': int(len(live)),
        'pf': float(pf),
        'ulcer_index_atr': float(abs(pnl.cumsum()).mean()) if len(pnl) else 0.0,
    }


def pick_validation_winner(table: pd.DataFrame) -> pd.Series:
    ranked = table.sort_values(['pf', 'ulcer_index_atr', 'trades'], ascending=[False, True, False])
    return ranked.iloc[0]
```

- [ ] **Step 4: Add a CLI smoke test**

Append to `tests/test_benchmark_trailing_stop_target.py`:

```python
def test_pick_validation_winner_ignores_sub_pf_one_rows_when_any_pf_one_exists():
    frame = pd.DataFrame(
        [
            {'candidate': 'a', 'pf': 0.90, 'ulcer_index_atr': 20.0, 'trades': 140},
            {'candidate': 'b', 'pf': 1.05, 'ulcer_index_atr': 80.0, 'trades': 140},
        ]
    )
    winner = pick_validation_winner(frame)
    assert winner['candidate'] == 'b'
```

- [ ] **Step 5: Run the benchmark tests**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_trailing_stop_target.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add ML/benchmark_trailing_stop_target.py tests/test_benchmark_trailing_stop_target.py
git commit -m "benchmark: add trailing-stop target validation benchmark"
```

### Task 4: Add A Bounded Matrix Runner For X And Sequence Length

**Files:**
- Create: `ML/run_trailing_stop_target_matrix.py`
- Create: `tests/test_run_trailing_stop_target_matrix.py`

- [ ] **Step 1: Write the failing test for config slugs**

```python
# tests/test_run_trailing_stop_target_matrix.py
from ML.run_trailing_stop_target_matrix import DEFAULT_MATRIX_CONFIGS, config_slug


def test_default_matrix_covers_three_x_values_and_three_sequence_lengths():
    slugs = {config_slug(row['target_column'], row['seq_len']) for row in DEFAULT_MATRIX_CONFIGS}
    assert slugs == {
        'trail_48_pnl_atr_x2_seq20',
        'trail_48_pnl_atr_x2_seq50',
        'trail_48_pnl_atr_x2_seq100',
        'trail_48_pnl_atr_x3_seq20',
        'trail_48_pnl_atr_x3_seq50',
        'trail_48_pnl_atr_x3_seq100',
        'trail_48_pnl_atr_x5_seq20',
        'trail_48_pnl_atr_x5_seq50',
        'trail_48_pnl_atr_x5_seq100',
    }
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_run_trailing_stop_target_matrix.py::test_default_matrix_covers_three_x_values_and_three_sequence_lengths -q
```

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Create the matrix runner**

Create `ML/run_trailing_stop_target_matrix.py`:

```python
from __future__ import annotations

DEFAULT_MATRIX_CONFIGS = [
    {'target_column': 'trail_48_pnl_atr_x2', 'seq_len': 20},
    {'target_column': 'trail_48_pnl_atr_x2', 'seq_len': 50},
    {'target_column': 'trail_48_pnl_atr_x2', 'seq_len': 100},
    {'target_column': 'trail_48_pnl_atr_x3', 'seq_len': 20},
    {'target_column': 'trail_48_pnl_atr_x3', 'seq_len': 50},
    {'target_column': 'trail_48_pnl_atr_x3', 'seq_len': 100},
    {'target_column': 'trail_48_pnl_atr_x5', 'seq_len': 20},
    {'target_column': 'trail_48_pnl_atr_x5', 'seq_len': 50},
    {'target_column': 'trail_48_pnl_atr_x5', 'seq_len': 100},
]


def config_slug(target_column: str, seq_len: int) -> str:
    return f'{target_column}_seq{seq_len}'
```

- [ ] **Step 4: Add the orchestration contract**

Append to `ML/run_trailing_stop_target_matrix.py`:

```python
def run_single_config(*, target_column, seq_len, output_dir, epochs, patience, batch_size, seed):
    # 1. train_model(... task='trailing_stop_target_v1', model='transformer', seq_len=seq_len, ...)
    # 2. evaluate_test for the saved checkpoint
    # 3. generate_signals with research prefix under output_dir / config_slug(...)
    # 4. benchmark_trailing_stop_target.run_benchmark(...)
    # 5. persist summary.json
    return {
        'target_column': target_column,
        'seq_len': seq_len,
        'output_dir': str(output_dir),
    }
```

- [ ] **Step 5: Run the matrix tests**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_run_trailing_stop_target_matrix.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add ML/run_trailing_stop_target_matrix.py tests/test_run_trailing_stop_target_matrix.py
git commit -m "ml: add trailing-stop target matrix runner"
```

### Task 5: Run The First Validation Wave And Freeze The Verdict

**Files:**
- Modify: `MODULE_INDEX.md`
- Create: `docs/reports/2026-04-16-trailing-stop-target-first-wave.md`

- [ ] **Step 1: Rebuild labeled datasets with the new target columns**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m processing.label_main
```

Expected: regenerated `DATA/Nero_{train,validation,test}_labeled.csv` now contain `trail_48_pnl_atr_x2/x3/x5`.

- [ ] **Step 2: Run the targeted test suite**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest \
  tests/test_trailing_stop_target_labels.py \
  tests/test_trailing_stop_target_task.py \
  tests/test_benchmark_trailing_stop_target.py \
  tests/test_run_trailing_stop_target_matrix.py -q
```

Expected: PASS.

- [ ] **Step 3: Launch the first bounded matrix**

Run:

```bash
MPLCONFIGDIR=/tmp/matplotlib /home/hohla/git/SoSimple/.venv/bin/python \
  -m ML.run_trailing_stop_target_matrix \
  --output-dir ML/reports/trailing_stop_target_matrix \
  --epochs 5 \
  --patience 3 \
  --batch-size 256
```

Expected: writes nine run directories and one `manifest.json`.

- [ ] **Step 4: Freeze the winner from validation and run one test check**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python - <<'PY'
import json
from pathlib import Path

manifest = json.loads(Path('ML/reports/trailing_stop_target_matrix/manifest.json').read_text())
print(manifest['configs'])
PY
```

Expected: exactly nine configs listed; one validation winner recorded inside the manifest summaries.

- [ ] **Step 5: Write the stage report**

Create `docs/reports/2026-04-16-trailing-stop-target-first-wave.md` with:

```md
# Trailing-Stop Target First Wave

> **Date**: 2026-04-16
> **Status**: Completed
> **Goal**: Проверить первую bounded волну нового target-а `trail_48_pnl_atr`
> **Related plan/spec**: `docs/superpowers/specs/2026-04-16-trailing-stop-target-design.md`, `docs/superpowers/plans/2026-04-16-trailing-stop-target-retraining.md`
> **Related commit**: pending
```

The report body must include:

- the winning `(X, seq_len)` pair from validation;
- whether any candidate crossed `PF > 1`;
- the frozen test result for the validation winner;
- the conclusion `track_alive` or `track_rejected_first_wave`.

- [ ] **Step 6: Update module index**

Add entries for:

- `ML/trailing_stop_target_task.py`
- `ML/benchmark_trailing_stop_target.py`
- `ML/run_trailing_stop_target_matrix.py`
- `tests/test_trailing_stop_target_labels.py`
- `tests/test_trailing_stop_target_task.py`
- `tests/test_benchmark_trailing_stop_target.py`
- `tests/test_run_trailing_stop_target_matrix.py`

- [ ] **Step 7: Final verification**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest \
  tests/test_trailing_stop_target_labels.py \
  tests/test_trailing_stop_target_task.py \
  tests/test_benchmark_trailing_stop_target.py \
  tests/test_run_trailing_stop_target_matrix.py -q
```

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add MODULE_INDEX.md docs/reports/2026-04-16-trailing-stop-target-first-wave.md
git commit -m "research: run trailing-stop target first wave"
```
