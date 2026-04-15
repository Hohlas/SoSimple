# Direct Trade Decision Model Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Запустить отдельный ML-трек, где модель сразу учится решать задачу `торговать / не торговать`, а не только предсказывать свойства движения цены, и проверить, может ли такой подход дать более частую систему при `PF > 2`.

**Architecture:** План не повторяет старый outcome-aligned этап буквально. Вместо этого он создаёт новую target-definition и новый validation-first benchmark. Близкие инструменты, Conformal Prediction и любые внешние фильтры исключены из поиска. Сначала строятся новые target-метки, затем обучается модель, затем selection-бenchmark проверяет частоту, PF и устойчивость.

**Tech Stack:** Python 3.11, pandas, numpy, torch, pytest, существующий training stack `ML/train.py`, `ML/evaluate_test.py`, `ML/data_loader.py`.

---

## File Structure

### Read First

- `AGENTS.md`
- `CONTEXT_HANDOFF.md`
- `docs/superpowers/specs/2026-04-15-quantile-next-research-design.md`
- `docs/reports/2026-04-08-outcome-aligned-retraining.md`
- `ML/benchmark_outcome_targets.py`
- `ML/reports/outcome_target_validation_benchmark.md`

### Files To Create

- `ML/benchmark_trade_decision_model.py`
- `tests/test_benchmark_trade_decision_model.py`
- `ML/reports/trade_decision_model/validation_grid.csv`
- `ML/reports/trade_decision_model/test_grid.csv`
- `ML/reports/trade_decision_model/selected_target.json`
- `ML/reports/trade_decision_model/final_verdict.json`
- `ML/reports/trade_decision_model/run_metadata.json`
- `docs/reports/2026-04-15-trade-decision-model.md`

### Files To Modify

- `processing/label_signals.py`
- `processing/label_main.py`
- `ML/data_loader.py`
- `ML/train.py`
- `ML/evaluate_test.py`
- `ML/utils.py`
- `tests/test_trade_target_labels.py`
- `tests/test_outcome_tasks.py`

### Files To Update At Stage Close

- `CHANGELOG.md`
- `CONTEXT_HANDOFF.md`
- `docs/superpowers/roadmap.md`
- `wiki/research/execution-tracks.md`
- `wiki/index.md`
- `wiki/log.md`
- `wiki/REPO_integrity.md`

---

## Acceptance Rules

- This plan must not reuse the old close-at-fixed-horizon labels as-is.
- Search and target selection happen on `validation` only.
- `test` is used only once after the winner is frozen.
- Empty/no-trade rows stay in the population.
- Cross-instrument checks are forbidden in this plan.
- Conformal Prediction is forbidden in this plan.
- Final candidate must move toward `40–50` trades per year with `PF > 2`.

---

## Task 1: Define A New Direct Trade Decision Target

**Files:**

- Modify: `processing/label_signals.py`
- Modify: `processing/label_main.py`
- Test: `tests/test_trade_target_labels.py`

- [ ] **Step 1: Write the failing test for the new target columns**

Add:

```python
import pandas as pd
import processing.label_signals as ls


def test_label_trade_decision_targets_adds_expected_columns():
    frame = pd.DataFrame(
        {
            "time": ["2025.01.01 00:00"],
            "signal": [1],
            "ATR": [10.0],
            "ret_24_dir_atr": [2.0],
            "adv_24_atr": [0.5],
        }
    )

    out = ls.label_trade_decision_targets(frame.copy())

    assert "trade_decision_target" in out.columns
    assert "trade_direction_target" in out.columns
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_trade_target_labels.py::test_label_trade_decision_targets_adds_expected_columns -q
```

Expected: fail with missing helper.

- [ ] **Step 3: Implement the new target builder**

Add:

```python
def label_trade_decision_targets(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    ret_24 = pd.to_numeric(out.get("ret_24_dir_atr", 0.0), errors="coerce").fillna(0.0)
    adv_24 = pd.to_numeric(out.get("adv_24_atr", 0.0), errors="coerce").fillna(0.0)
    signal = pd.to_numeric(out.get("signal", 0), errors="coerce").fillna(0).astype(int)

    out["trade_decision_target"] = ((signal != 0) & (ret_24 > 0.0) & (adv_24 <= ret_24.clip(lower=0.0))).astype(int)
    out["trade_direction_target"] = signal.where(out["trade_decision_target"] == 1, 0)
    return out
```

- [ ] **Step 4: Wire the target into `label_main.py`**

Add:

```python
labeled_df = label_signals.label_trade_decision_targets(labeled_df)
```

- [ ] **Step 5: Run the label tests**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_trade_target_labels.py -q
```

Expected: pass.

- [ ] **Step 6: Commit**

Run:

```bash
git add processing/label_signals.py processing/label_main.py tests/test_trade_target_labels.py
git commit -m "trade_decision: add direct trade targets"
```

---

## Task 2: Add The New Task To The ML Stack

**Files:**

- Modify: `ML/data_loader.py`
- Modify: `ML/train.py`
- Modify: `ML/evaluate_test.py`
- Modify: `ML/utils.py`
- Test: `tests/test_outcome_tasks.py`

- [ ] **Step 1: Write the failing test for task registration**

Add:

```python
from ML.data_loader import TRADE_DECISION_TARGET


def test_trade_decision_target_constant_exists():
    assert TRADE_DECISION_TARGET == "trade_decision_cls"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_outcome_tasks.py::test_trade_decision_target_constant_exists -q
```

Expected: fail because constant does not exist.

- [ ] **Step 3: Register the new task constant**

Add to `ML/data_loader.py`:

```python
TRADE_DECISION_TARGET = "trade_decision_cls"
```

- [ ] **Step 4: Add the new task branch in train.py**

Add to parser choices:

```python
"trade_decision_cls"
```

Use binary cross-entropy or cross-entropy on `trade_decision_target`.

- [ ] **Step 5: Add evaluation branch**

In `ML/evaluate_test.py`, add one report block for:

```python
if task == "trade_decision_cls":
    # report AUC, precision/recall, trades_per_year, PF, negative_year_slices
```

- [ ] **Step 6: Run the ML stack tests**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_outcome_tasks.py -q
```

Expected: pass.

- [ ] **Step 7: Commit**

Run:

```bash
git add ML/data_loader.py ML/train.py ML/evaluate_test.py ML/utils.py tests/test_outcome_tasks.py
git commit -m "trade_decision: register direct decision task"
```

---

## Task 3: Build A Validation-First Benchmark For The New Task

**Files:**

- Create: `ML/benchmark_trade_decision_model.py`
- Create: `tests/test_benchmark_trade_decision_model.py`

- [ ] **Step 1: Write the failing test for winner selection**

Add:

```python
import pandas as pd

from ML.benchmark_trade_decision_model import pick_trade_decision_candidate


def test_pick_trade_decision_candidate_uses_pf_and_trades_per_year():
    frame = pd.DataFrame(
        [
            {"candidate": "a", "pf": 2.4, "trades_per_year": 18, "negative_year_slices": 0, "profit_concentration_top_10": 0.12},
            {"candidate": "b", "pf": 2.1, "trades_per_year": 42, "negative_year_slices": 0, "profit_concentration_top_10": 0.14},
            {"candidate": "c", "pf": 1.9, "trades_per_year": 51, "negative_year_slices": 0, "profit_concentration_top_10": 0.10},
        ]
    )

    result = pick_trade_decision_candidate(frame, min_pf=2.0, target_trades_per_year=40)

    assert result["candidate"] == "b"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_trade_decision_model.py -q
```

Expected: import failure because benchmark does not exist yet.

- [ ] **Step 3: Implement the benchmark skeleton**

Create `ML/benchmark_trade_decision_model.py`:

```python
from __future__ import annotations

import pandas as pd


def pick_trade_decision_candidate(table: pd.DataFrame, min_pf: float, target_trades_per_year: int) -> pd.Series:
    live = table.loc[
        (table["pf"] >= min_pf)
        & (table["trades_per_year"] >= target_trades_per_year)
        & (table["negative_year_slices"] == 0)
    ].copy()
    if live.empty:
        live = table.copy()
    return live.sort_values(
        ["pf", "trades_per_year", "profit_concentration_top_10"],
        ascending=[False, False, True],
    ).iloc[0]
```

- [ ] **Step 4: Run tests**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_trade_decision_model.py -q
```

Expected: pass.

- [ ] **Step 5: Train the new task and run the benchmark**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m ML.train --model transformer --task trade_decision_cls --epochs 30 --seed 42
/home/hohla/git/SoSimple/.venv/bin/python -m ML.evaluate_test --task trade_decision_cls --checkpoint ML/checkpoints/transformer_trade_decision_cls_best.pt
/home/hohla/git/SoSimple/.venv/bin/python -m ML.benchmark_trade_decision_model --model transformer --output-dir ML/reports/trade_decision_model
```

Expected: writes `validation_grid.csv`, `test_grid.csv`, `selected_target.json`, `final_verdict.json`.

- [ ] **Step 6: Commit**

Run:

```bash
git add ML/benchmark_trade_decision_model.py tests/test_benchmark_trade_decision_model.py
git commit -m "trade_decision: benchmark direct decision model"
```

---

## Task 4: Record The Final Verdict And Sync Project Memory

**Files:**

- Create: `docs/reports/2026-04-15-trade-decision-model.md`
- Modify: `CHANGELOG.md`
- Modify: `CONTEXT_HANDOFF.md`
- Modify: `docs/superpowers/roadmap.md`
- Modify: `wiki/research/execution-tracks.md`
- Modify: `wiki/index.md`
- Modify: `wiki/log.md`
- Modify: `wiki/REPO_integrity.md`

- [ ] **Step 1: Write the report template**

Create:

```md
# Direct Trade Decision Model

> **Date**: 2026-04-15
> **Status**: Completed
> **Goal**: Проверить прямую модель `торговать / не торговать`

## Results

- validation winner: `TBD`
- test check: `TBD`
- trades_per_year: `TBD`
- PF: `TBD`
- negative_year_slices: `TBD`
- profit_concentration_top_10: `TBD`

## Verdict

- `viable_trade_decision_candidate`
- или `reject_trade_decision_track`
```

- [ ] **Step 2: Fill the report from artifacts**

Use:

```bash
sed -n '1,220p' ML/reports/trade_decision_model/final_verdict.json
sed -n '1,220p' ML/reports/trade_decision_model/selected_target.json
```

- [ ] **Step 3: Sync handoff and changelog**

Update project memory with:

- what the new direct-decision target was,
- whether it passed,
- what remains open.

- [ ] **Step 4: Refresh integrity**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python wiki/wiki.py generate
```

- [ ] **Step 5: Verification**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_trade_target_labels.py tests/test_outcome_tasks.py tests/test_benchmark_trade_decision_model.py -q
```

Expected: pass.

- [ ] **Step 6: Commit**

Run:

```bash
git add docs/reports/2026-04-15-trade-decision-model.md CHANGELOG.md CONTEXT_HANDOFF.md docs/superpowers/roadmap.md wiki/research/execution-tracks.md wiki/index.md wiki/log.md wiki/REPO_integrity.md
git commit -m "docs: record trade decision model verdict"
```

---

## Self-Review

- Spec coverage: plan covers a new direct decision target, validation-first benchmark, and project-memory sync.
- Placeholder scan: only the report template contains `TBD`, which must be replaced during execution.
- Type consistency: one target family, one benchmark, one report directory, one verdict flow.
