# Quantile Execution Improvement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Проверить, можно ли улучшить практический результат вокруг frozen `entry_path_v1_quantile`, сначала через выход, и только затем через вход.

**Architecture:** Отдельный execution benchmark поверх уже замороженного `quantile` baseline. Входной сигнал не меняется; сравниваются несколько простых execution-вариантов. Поиск идёт только на `validation`, затем один frozen check на `test`.

**Tech Stack:** Python 3.11, pandas/numpy, pytest, существующие prediction/report artifacts `entry_path_v1_quantile`.

---

## File Structure

### Read First

- `AGENTS.md`
- `CONTEXT_HANDOFF.md`
- `docs/superpowers/specs/2026-04-13-quantile-execution-improvement-design.md`
- `docs/reports/2026-04-12-quantile-status-decision.md`
- `ML/reports/entry_path_v1_quantile_selected_rule.json`
- `ML/reports/entry_path_v1_quantile_robustness/seed_007/entry_path_v1_quantile_validation_predictions.csv`
- `ML/reports/entry_path_v1_quantile_robustness/seed_007/entry_path_v1_quantile_test_predictions.csv`

### Files To Create

- `ML/benchmark_quantile_execution_improvement.py`
- `tests/test_benchmark_quantile_execution_improvement.py`
- `ML/reports/quantile_execution_improvement/validation_grid.csv`
- `ML/reports/quantile_execution_improvement/test_grid.csv`
- `ML/reports/quantile_execution_improvement/selected_variant.json`
- `ML/reports/quantile_execution_improvement/run_metadata.json`
- `docs/reports/2026-04-13-quantile-execution-improvement.md`

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

- `quantile` signal source is frozen and unchanged.
- Exit variants are evaluated first.
- Entry variants are evaluated only after exit variants are benchmarked.
- Only simple, explainable execution variants are allowed.
- Validation chooses the winner.
- Test is used only once after winner freeze.
- Final verdict is only:
  - `no_execution_uplift`
  - or `execution_uplift_candidate`

---

## Task 1: Baseline And Exit Variant Metrics

**Files:**

- Create: `ML/benchmark_quantile_execution_improvement.py`
- Create: `tests/test_benchmark_quantile_execution_improvement.py`

- [ ] **Step 1.1: Write failing tests for baseline and variant metrics**

Add:

```python
import pandas as pd

from ML.benchmark_quantile_execution_improvement import (
    apply_exit_variant,
    compute_variant_metrics,
)


def test_apply_exit_variant_timeout_shortens_holding_horizon():
    frame = pd.DataFrame(
        {
            "true_ret_24_dir_atr": [2.0, -1.0],
            "true_ret_12_dir_atr": [1.0, -0.4],
        }
    )

    result = apply_exit_variant(frame, variant="timeout_12")

    assert list(result["pnl_atr"]) == [1.0, -0.4]


def test_compute_variant_metrics_counts_pf():
    frame = pd.DataFrame(
        {
            "pnl_atr": [2.0, -1.0, 3.0],
        }
    )

    result = compute_variant_metrics(frame)

    assert result["n_trades"] == 3
    assert result["pf"] == 5.0
```

- [ ] **Step 1.2: Run tests to verify failure**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_quantile_execution_improvement.py -q
```

Expected: import failure because module does not exist yet.

- [ ] **Step 1.3: Implement minimal baseline and exit variant helpers**

Create `ML/benchmark_quantile_execution_improvement.py` with:

```python
from __future__ import annotations

import math
from typing import Any

import pandas as pd


def apply_exit_variant(frame: pd.DataFrame, variant: str) -> pd.DataFrame:
    result = frame.copy()
    if variant == "baseline_24":
        result["pnl_atr"] = result["true_ret_24_dir_atr"].astype(float)
        return result
    if variant == "timeout_12":
        result["pnl_atr"] = result["true_ret_12_dir_atr"].astype(float)
        return result
    raise ValueError(f"unsupported variant: {variant}")


def compute_variant_metrics(frame: pd.DataFrame) -> dict[str, Any]:
    trades = int(len(frame))
    if trades == 0:
        return {
            "n_trades": 0,
            "wins": 0,
            "losses": 0,
            "gross_profit": 0.0,
            "gross_loss": 0.0,
            "pf": None,
            "win_rate": None,
            "mean_pnl_atr": None,
        }

    pnl = frame["pnl_atr"].astype(float)
    wins = int((pnl > 0).sum())
    losses = int((pnl < 0).sum())
    gross_profit = float(pnl[pnl > 0].sum())
    gross_loss = float(-pnl[pnl < 0].sum())
    pf = math.inf if gross_loss == 0.0 and gross_profit > 0.0 else gross_profit / gross_loss if gross_loss > 0.0 else 0.0
    return {
        "n_trades": trades,
        "wins": wins,
        "losses": losses,
        "gross_profit": gross_profit,
        "gross_loss": gross_loss,
        "pf": pf,
        "win_rate": wins / trades,
        "mean_pnl_atr": float(pnl.mean()),
    }
```

- [ ] **Step 1.4: Run tests**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_quantile_execution_improvement.py -q
```

Expected: `2 passed`.

- [ ] **Step 1.5: Commit**

Run:

```bash
git add ML/benchmark_quantile_execution_improvement.py tests/test_benchmark_quantile_execution_improvement.py
git commit -m "quantile: add execution improvement helpers"
```

---

## Task 2: Validation Grid For Exit Variants

**Files:**

- Modify: `ML/benchmark_quantile_execution_improvement.py`
- Modify: `tests/test_benchmark_quantile_execution_improvement.py`

- [ ] **Step 2.1: Write failing test for validation grid**

Add:

```python
from ML.benchmark_quantile_execution_improvement import evaluate_variants


def test_evaluate_variants_returns_one_row_per_variant():
    frame = pd.DataFrame(
        {
            "true_ret_24_dir_atr": [2.0, -1.0],
            "true_ret_12_dir_atr": [1.0, -0.4],
        }
    )

    result = evaluate_variants(frame, variants=["baseline_24", "timeout_12"])

    assert list(result["variant"]) == ["baseline_24", "timeout_12"]
    assert list(result["n_trades"]) == [2, 2]
```

- [ ] **Step 2.2: Run focused test and confirm failure**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_quantile_execution_improvement.py::test_evaluate_variants_returns_one_row_per_variant -q
```

Expected: missing function.

- [ ] **Step 2.3: Implement validation grid**

Add:

```python
def evaluate_variants(frame: pd.DataFrame, variants: list[str]) -> pd.DataFrame:
    rows = []
    for variant in variants:
        variant_frame = apply_exit_variant(frame, variant=variant)
        rows.append({"variant": variant, **compute_variant_metrics(variant_frame)})
    return pd.DataFrame(rows)
```

- [ ] **Step 2.4: Run tests**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_quantile_execution_improvement.py -q
```

Expected: all tests pass.

- [ ] **Step 2.5: Commit**

Run:

```bash
git add ML/benchmark_quantile_execution_improvement.py tests/test_benchmark_quantile_execution_improvement.py
git commit -m "quantile: evaluate execution variants on validation"
```

---

## Task 3: Winner Selection And CLI

**Files:**

- Modify: `ML/benchmark_quantile_execution_improvement.py`
- Modify: `tests/test_benchmark_quantile_execution_improvement.py`

- [ ] **Step 3.1: Write failing tests for winner selection and CLI**

Add:

```python
import json
from pathlib import Path

from ML.benchmark_quantile_execution_improvement import (
    choose_validation_winner,
    main,
)


def test_choose_validation_winner_prefers_pf_uplift():
    grid = pd.DataFrame(
        {
            "variant": ["baseline_24", "timeout_12"],
            "pf": [2.0, 3.0],
            "n_trades": [40, 40],
        }
    )

    result = choose_validation_winner(grid)

    assert result["variant"] == "timeout_12"


def test_main_writes_variant_artifacts(tmp_path: Path):
    validation = tmp_path / "validation.csv"
    test = tmp_path / "test.csv"
    output = tmp_path / "out"

    frame = pd.DataFrame(
        {
            "time": ["2025-01-01", "2025-01-02"],
            "signal": [1, -1],
            "true_ret_12_dir_atr": [1.0, -0.4],
            "true_ret_24_dir_atr": [2.0, -1.0],
        }
    )
    frame.to_csv(validation, sep=";", index=False)
    frame.to_csv(test, sep=";", index=False)

    code = main(
        [
            "--validation-predictions",
            str(validation),
            "--test-predictions",
            str(test),
            "--output-dir",
            str(output),
        ]
    )

    assert code == 0
    assert (output / "validation_grid.csv").exists()
    assert (output / "test_grid.csv").exists()
    assert (output / "selected_variant.json").exists()
    payload = json.loads((output / "selected_variant.json").read_text(encoding="utf-8"))
    assert payload["variant"] in {"baseline_24", "timeout_12"}
```

- [ ] **Step 3.2: Run focused tests and confirm failure**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_quantile_execution_improvement.py -q
```

Expected: missing functions.

- [ ] **Step 3.3: Implement winner selection and CLI**

Add:

```python
def choose_validation_winner(grid: pd.DataFrame) -> dict[str, Any]:
    ordered = grid.sort_values(["pf", "n_trades"], ascending=[False, False], kind="stable").reset_index(drop=True)
    row = ordered.iloc[0]
    return {"variant": row["variant"], "pf": float(row["pf"]), "n_trades": int(row["n_trades"])}
```

CLI behavior:

- read `validation` and `test` CSVs with `sep=";"`
- require columns:
  - `time`
  - `signal`
  - `true_ret_12_dir_atr`
  - `true_ret_24_dir_atr`
- keep only `signal != 0`
- evaluate variants:
  - `baseline_24`
  - `timeout_12`
- choose winner on validation only
- evaluate same winner on test
- write:
  - `validation_grid.csv`
  - `test_grid.csv`
  - `selected_variant.json`
  - `run_metadata.json`

Return:

- `0` for success
- `2` for missing or invalid input

- [ ] **Step 3.4: Run tests**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_quantile_execution_improvement.py -q
```

Expected: all tests pass.

- [ ] **Step 3.5: Commit**

Run:

```bash
git add ML/benchmark_quantile_execution_improvement.py tests/test_benchmark_quantile_execution_improvement.py
git commit -m "quantile: add execution improvement cli"
```

---

## Task 4: Run Exit Benchmark And Verdict Report

**Files:**

- Create artefacts under: `ML/reports/quantile_execution_improvement/`
- Create: `docs/reports/2026-04-13-quantile-execution-improvement.md`

- [ ] **Step 4.1: Run execution benchmark**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m ML.benchmark_quantile_execution_improvement \
  --validation-predictions ML/reports/entry_path_v1_quantile_robustness/seed_007/entry_path_v1_quantile_validation_predictions.csv \
  --test-predictions ML/reports/entry_path_v1_quantile_robustness/seed_007/entry_path_v1_quantile_test_predictions.csv \
  --output-dir ML/reports/quantile_execution_improvement
```

Expected:

- command exits `0`
- exit-variant grids are written
- selected exit variant is frozen from validation

- [ ] **Step 4.2: Inspect artefacts**

Run:

```bash
sed -n '1,160p' ML/reports/quantile_execution_improvement/selected_variant.json
head -n 20 ML/reports/quantile_execution_improvement/validation_grid.csv
```

Expected:

- selected variant is visible
- validation and test numbers can be compared

- [ ] **Step 4.3: Write verdict report**

Create `docs/reports/2026-04-13-quantile-execution-improvement.md` with:

- baseline definition;
- tested exit variants;
- selected exit winner;
- validation/test comparison;
- verdict:
  - `no_execution_uplift`
  - or `execution_uplift_candidate`
- explicit note whether entry-stage exploration is still needed.

- [ ] **Step 4.4: Commit**

Run:

```bash
git add ML/reports/quantile_execution_improvement docs/reports/2026-04-13-quantile-execution-improvement.md
git commit -m "quantile: record execution improvement verdict"
```

---

## Task 5: Optional Entry Follow-Up

**Files:**

- Modify: `ML/benchmark_quantile_execution_improvement.py`
- Modify: `tests/test_benchmark_quantile_execution_improvement.py`

- [ ] **Step 5.1: Only continue if exit stage did not already produce enough uplift**

Decision rule:

- if exit winner already gives clear practical uplift, stop here and do not add entry variants in this plan;
- if exit stage gives no clear uplift, continue with simple entry variants.

- [ ] **Step 5.2: Add one failing test for simple entry variant handling**

Add:

```python
def test_apply_entry_delay_variant_reduces_trade_count_when_fill_missing():
    frame = pd.DataFrame(
        {
            "signal": [1, 1],
            "true_ret_24_dir_atr": [2.0, 1.0],
            "entry_delay_fill": [1, 0],
        }
    )

    result = apply_entry_variant(frame, variant="delay_if_fill")

    assert len(result) == 1
```

- [ ] **Step 5.3: Implement only one or two simple entry variants**

Allowed examples:

- `market_entry`
- `delay_if_fill`

No complex multi-condition logic.

- [ ] **Step 5.4: Run tests**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_quantile_execution_improvement.py -q
```

- [ ] **Step 5.5: Commit**

Run:

```bash
git add ML/benchmark_quantile_execution_improvement.py tests/test_benchmark_quantile_execution_improvement.py
git commit -m "quantile: add simple entry execution variants"
```

---

## Task 6: Stage Close

**Files:**

- Modify: `CHANGELOG.md`
- Modify: `CONTEXT_HANDOFF.md`
- Modify: `docs/superpowers/roadmap.md`
- Modify: `wiki/research/execution-tracks.md`
- Modify generated wiki files as needed

- [ ] **Step 6.1: Update project state**

Update:

- `CHANGELOG.md`
- `CONTEXT_HANDOFF.md`
- `docs/superpowers/roadmap.md`

with the execution verdict and the practical next step.

- [ ] **Step 6.2: Update wiki**

Ingest the new report into `wiki/research/execution-tracks.md`, update `wiki/index.md`, append `wiki/log.md`, then run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python wiki/wiki.py generate
```

- [ ] **Step 6.3: Final verification**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_quantile_execution_improvement.py -q
```

Expected: all tests pass.

- [ ] **Step 6.4: Commit**

Run:

```bash
git add CHANGELOG.md CONTEXT_HANDOFF.md docs/superpowers/roadmap.md wiki docs/reports/2026-04-13-quantile-execution-improvement.md
git commit -m "docs: close quantile execution improvement stage"
```

---

## Definition Of Done

- Frozen quantile signal is unchanged.
- Exit variants are benchmarked first.
- Entry variants are only added if still needed.
- Validation chooses the winner.
- Test confirms or rejects the frozen winner.
- Report and stage docs are synced.

---

## Self-Review

- Spec coverage: frozen signal, exit-first ordering, simple variants, validation-first discipline, and verdict are all covered.
- Placeholder scan: no placeholders remain.
- Scope check: this plan does not mix with forward-validation stage.
