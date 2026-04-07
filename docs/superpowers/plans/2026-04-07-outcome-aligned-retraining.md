# Outcome-Aligned Retraining Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Запустить новый ML-трек, в котором таргеты ближе к реальному торговому исходу, чем текущие `up/dn`-максимумы.

**Architecture:** План не заменяет существующий `regression_updn`, а создаёт исследовательский стенд для трёх семейств таргетов: `trade_outcome_cls`, `trade_pnl_reg`, `signal_archetype_cls`. Сначала формируются новые метки на основе уже имеющихся `OHLC` и атласных разборов, затем один и тот же `transformer` учится на каждом семействе, а сравнение ведётся на `validation` по одинаковым правилам отбора и на `test` только для финального подтверждения.

**Tech Stack:** Python 3.11+, pandas, numpy, torch, pytest

---

### Task 1: Построить исследовательские метки нового поколения

**Files:**
- Modify: `processing/label_signals.py`
- Modify: `processing/label_main.py`
- Create: `tests/test_trade_target_labels.py`

- [ ] **Step 1: Write the failing test for new label columns**

```python
# tests/test_trade_target_labels.py
import pandas as pd
import processing.label_signals as ls


def test_label_trade_targets_adds_expected_columns():
    frame = pd.DataFrame({
        'time': ['2025.01.01 00:00'],
        'signal': [1],
        'ATR': [10.0],
        'up_12': [20.0],
        'dn_12': [5.0],
        'up_24': [25.0],
        'dn_24': [7.0],
    })
    out = ls.label_trade_targets(frame.copy())
    assert 'trade_outcome_h12' in out.columns
    assert 'trade_pnl_h12_atr' in out.columns
    assert 'archetype_target' in out.columns
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_trade_target_labels.py -q`
Expected: FAIL with `AttributeError`

- [ ] **Step 3: Add the new label builder**

```python
# processing/label_signals.py
def label_trade_targets(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out['trade_outcome_h12'] = np.where(out['up_12'] > out['dn_12'], 1, 0)
    out['trade_pnl_h12_atr'] = (out['up_12'] - out['dn_12']) / out['ATR']
    out['archetype_target'] = np.where(out['trade_pnl_h12_atr'] > 0, 1, 0)
    return out
```

- [ ] **Step 4: Wire the label builder into the pipeline before normalization**

```python
# processing/label_main.py
labeled_df = label_trade_targets(labeled_df)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `./.venv/bin/python -m pytest tests/test_trade_target_labels.py -q`
Expected: PASS


### Task 2: Добавить три новых ML-задачи в training/evaluation stack

**Files:**
- Modify: `ML/data_loader.py`
- Modify: `ML/train.py`
- Modify: `ML/evaluate_test.py`
- Create: `tests/test_outcome_tasks.py`

- [ ] **Step 1: Write the failing tests for task registration**

```python
# tests/test_outcome_tasks.py
from ML.data_loader import TRADE_OUTCOME_TARGET, TRADE_PNL_TARGET, ARCHETYPE_TARGET


def test_new_task_constants_exist():
    assert TRADE_OUTCOME_TARGET == 'trade_outcome_cls'
    assert TRADE_PNL_TARGET == 'trade_pnl_reg'
    assert ARCHETYPE_TARGET == 'signal_archetype_cls'
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_outcome_tasks.py -q`
Expected: FAIL with `ImportError` or `AttributeError`

- [ ] **Step 3: Register the new targets in the data loader**

```python
# ML/data_loader.py
TRADE_OUTCOME_TARGET = 'trade_outcome_cls'
TRADE_PNL_TARGET = 'trade_pnl_reg'
ARCHETYPE_TARGET = 'signal_archetype_cls'
```

- [ ] **Step 4: Add task branches in train.py**

```python
# ML/train.py
parser.add_argument(
    '--task',
    choices=[
        'classification',
        'regression',
        'regression_updn',
        'triple_barrier',
        'trade_outcome_cls',
        'trade_pnl_reg',
        'signal_archetype_cls',
    ],
)
```

- [ ] **Step 5: Add OOS evaluation branches**

```python
# ML/evaluate_test.py
if task == 'trade_outcome_cls':
    # precision, recall, PF proxy from fixed payoff
elif task == 'trade_pnl_reg':
    # MAE + mean pnl by top slice
elif task == 'signal_archetype_cls':
    # AUC + enrichment of good archetype
```

- [ ] **Step 6: Run tests to verify the stack compiles**

Run: `./.venv/bin/python -m pytest tests/test_outcome_tasks.py -q`
Expected: PASS


### Task 3: Benchmark the three target families on validation

**Files:**
- Create: `ML/benchmark_outcome_targets.py`
- Create: `tests/test_benchmark_outcome_targets.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_benchmark_outcome_targets.py
import pandas as pd
import ML.benchmark_outcome_targets as bot


def test_pick_winner_prefers_higher_pf_with_trade_floor():
    frame = pd.DataFrame([
        {'task': 'a', 'pf': 1.4, 'trades': 120},
        {'task': 'b', 'pf': 1.8, 'trades': 24},
        {'task': 'c', 'pf': 1.6, 'trades': 100},
    ])
    out = bot.pick_winner(frame, min_trades=80)
    assert out['task'] == 'c'
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_benchmark_outcome_targets.py -q`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Add benchmark runner**

```python
# ML/benchmark_outcome_targets.py
def pick_winner(table: pd.DataFrame, min_trades: int = 80) -> pd.Series:
    live = table[table['trades'] >= min_trades].copy()
    live = live.sort_values(['pf', 'trades'], ascending=[False, False])
    return live.iloc[0]
```

- [ ] **Step 4: Run three comparable validation experiments**

Run: `./.venv/bin/python -m ML.train --model transformer --task trade_outcome_cls --epochs 30 --seed 42`
Expected: checkpoint and validation metrics saved

Run: `./.venv/bin/python -m ML.train --model transformer --task trade_pnl_reg --epochs 30 --seed 42`
Expected: checkpoint and validation metrics saved

Run: `./.venv/bin/python -m ML.train --model transformer --task signal_archetype_cls --epochs 30 --seed 42`
Expected: checkpoint and validation metrics saved

- [ ] **Step 5: Save the winner and only then evaluate on test**

Run: `./.venv/bin/python -m ML.benchmark_outcome_targets`
Expected: writes `ML/reports/frozen_outcome_target.json` with the chosen task and threshold settings


### Task 4: Freeze the chosen target family and update handoff

**Files:**
- Modify: `CONTEXT_HANDOFF.md`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Run final test only for the chosen family**

Run: `./.venv/bin/python -m ML.evaluate_test --task trade_outcome_cls --model transformer`
Expected: one OOS report when `frozen_outcome_target.json` says `trade_outcome_cls`; if JSON says another task, replace only the task name and do not rerun multiple tasks on `test`

- [ ] **Step 2: Update handoff with winner, loser and open risks**

```md
### Winner
- Target family: `trade_outcome_cls` или `trade_pnl_reg` или `signal_archetype_cls` — ровно то значение, которое сохранено в `ML/reports/frozen_outcome_target.json`
- Reason for win: highest validation quality after the same trade-floor and yearly-stability filter used for all candidates

### Rejected Families
- Family 1: lower validation PF or weaker yearly stability than the winner at the same trade floor
- Family 2: lower validation PF or weaker yearly stability than the winner at the same trade floor

### Open Risks
- Remaining gap to MT4 execution
- Whether the winner still needs separate exit logic
```

- [ ] **Step 3: Verify nothing regressed in data-loading tests**

Run: `./.venv/bin/python -m pytest tests/test_outcome_tasks.py tests/test_trade_target_labels.py tests/test_benchmark_outcome_targets.py -q`
Expected: PASS
