# Quantile Forward Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Дать operational verdict `confirmed / watch / revisit` для текущего frozen `entry_path_v1_quantile` на новых данных без перенастройки правила.

**Architecture:** Отдельный frozen benchmark поверх уже существующего production rule `ML/reports/entry_path_v1_quantile_selected_rule.json`. Новый код только применяет текущее правило к следующему по времени куску данных, считает метрики и выдаёт operational verdict; rule search, retune и новый winner запрещены.

**Tech Stack:** Python 3.11, pandas/numpy, pytest, существующие модули `API.export_entry_path_v1_quantile_signals`, `ML.benchmark_entry_path_v1_quantile_filter`.

---

## File Structure

### Read First

- `AGENTS.md`
- `CONTEXT_HANDOFF.md`
- `docs/superpowers/specs/2026-04-13-quantile-forward-validation-design.md`
- `docs/reports/2026-04-12-quantile-status-decision.md`
- `ML/reports/entry_path_v1_quantile_selected_rule.json`
- `ML/benchmark_entry_path_v1_quantile_filter.py`
- `API/export_entry_path_v1_quantile_signals.py`

### Existing Inputs

- `ML/reports/entry_path_v1_quantile_selected_rule.json`
- `ML/reports/entry_path_v1_quantile_robustness/seed_007/entry_path_v1_quantile_test_predictions.csv`
- следующий по времени frozen dataset path, который будет передан в CLI или найден через явный аргумент `--forward-predictions`

### Files To Create

- `ML/benchmark_quantile_forward_validation.py`
- `tests/test_benchmark_quantile_forward_validation.py`
- `ML/reports/quantile_forward_validation/summary.json`
- `ML/reports/quantile_forward_validation/time_slices.csv`
- `ML/reports/quantile_forward_validation/run_metadata.json`
- `docs/reports/2026-04-13-quantile-forward-validation.md`

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

- Rule source is only `ML/reports/entry_path_v1_quantile_selected_rule.json`.
- No quantile parameter is changed.
- No new winner is selected.
- Forward dataset must be strictly after the production decision window.
- Main verdict must be one of:
  - `confirmed`
  - `watch`
  - `revisit`
- Main alarm signal is PF drawdown.
- Time-slice weakness is secondary, but must still be reported.

---

## Task 1: Frozen Rule Loader And Forward Slice Metrics

**Files:**

- Create: `ML/benchmark_quantile_forward_validation.py`
- Create: `tests/test_benchmark_quantile_forward_validation.py`

- [ ] **Step 1.1: Write failing tests for verdict helper and forward metrics**

Add:

```python
import pandas as pd

from ML.benchmark_quantile_forward_validation import (
    compute_forward_metrics,
    decide_operational_verdict,
)


def test_compute_forward_metrics_counts_pf_and_trades():
    frame = pd.DataFrame(
        {
            "true_ret_24_dir_atr": [2.0, -1.0, 3.0],
        }
    )

    result = compute_forward_metrics(frame)

    assert result["n_trades"] == 3
    assert result["gross_profit"] == 5.0
    assert result["gross_loss"] == 1.0
    assert result["pf"] == 5.0


def test_decide_operational_verdict_prefers_pf_drawdown_signal():
    result = decide_operational_verdict(
        historical_pf=8.18,
        forward_pf=3.5,
        n_trades=18,
        negative_slices=1,
    )

    assert result["verdict"] == "watch"
```

- [ ] **Step 1.2: Run tests to verify failure**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_quantile_forward_validation.py -q
```

Expected: import failure because module does not exist yet.

- [ ] **Step 1.3: Implement minimal helpers**

Create `ML/benchmark_quantile_forward_validation.py` with:

```python
from __future__ import annotations

import math
from typing import Any

import pandas as pd


def compute_forward_metrics(frame: pd.DataFrame) -> dict[str, Any]:
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

    pnl = frame["true_ret_24_dir_atr"].astype(float)
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


def decide_operational_verdict(
    *,
    historical_pf: float,
    forward_pf: float | None,
    n_trades: int,
    negative_slices: int,
) -> dict[str, Any]:
    if forward_pf is None or n_trades < 10:
        return {"verdict": "watch", "reason": "low_support"}
    if forward_pf < 1.0:
        return {"verdict": "revisit", "reason": "pf_below_1"}
    if forward_pf < historical_pf * 0.5:
        return {"verdict": "watch", "reason": "pf_drawdown"}
    if negative_slices > 1:
        return {"verdict": "watch", "reason": "weak_time_slices"}
    return {"verdict": "confirmed", "reason": "forward_pf_holds"}
```

- [ ] **Step 1.4: Run tests**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_quantile_forward_validation.py -q
```

Expected: `2 passed`.

- [ ] **Step 1.5: Commit**

Run:

```bash
git add ML/benchmark_quantile_forward_validation.py tests/test_benchmark_quantile_forward_validation.py
git commit -m "quantile: add forward validation helpers"
```

---

## Task 2: Time-Slice Breakdown

**Files:**

- Modify: `ML/benchmark_quantile_forward_validation.py`
- Modify: `tests/test_benchmark_quantile_forward_validation.py`

- [ ] **Step 2.1: Write failing tests for time-slice breakdown**

Add:

```python
from ML.benchmark_quantile_forward_validation import build_time_slices


def test_build_time_slices_groups_by_quarter():
    frame = pd.DataFrame(
        {
            "time": ["2026-01-10", "2026-02-10", "2026-05-10"],
            "true_ret_24_dir_atr": [1.0, -1.0, 2.0],
        }
    )

    result = build_time_slices(frame, mode="quarter")

    assert list(result["slice"]) == ["2026-Q1", "2026-Q2"]
    assert list(result["n_trades"]) == [2, 1]
```

- [ ] **Step 2.2: Run focused test and confirm failure**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_quantile_forward_validation.py::test_build_time_slices_groups_by_quarter -q
```

Expected: missing function.

- [ ] **Step 2.3: Implement time-slice breakdown**

Add:

```python
def build_time_slices(frame: pd.DataFrame, mode: str = "quarter") -> pd.DataFrame:
    working = frame.copy()
    dt = pd.to_datetime(working["time"])
    if mode != "quarter":
        raise ValueError(f"unsupported slice mode: {mode}")
    working["slice"] = dt.dt.to_period("Q").astype(str)
    rows = []
    for key, group in working.groupby("slice", sort=True):
        rows.append({"slice": key, **compute_forward_metrics(group)})
    return pd.DataFrame(rows)
```

- [ ] **Step 2.4: Run tests**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_quantile_forward_validation.py -q
```

Expected: all tests pass.

- [ ] **Step 2.5: Commit**

Run:

```bash
git add ML/benchmark_quantile_forward_validation.py tests/test_benchmark_quantile_forward_validation.py
git commit -m "quantile: add forward time-slice breakdown"
```

---

## Task 3: CLI And Artefacts

**Files:**

- Modify: `ML/benchmark_quantile_forward_validation.py`
- Modify: `tests/test_benchmark_quantile_forward_validation.py`

- [ ] **Step 3.1: Write failing smoke test for CLI**

Add:

```python
import json
from pathlib import Path

from ML.benchmark_quantile_forward_validation import main


def test_main_writes_summary_and_time_slices(tmp_path: Path):
    predictions = tmp_path / "forward.csv"
    output = tmp_path / "out"
    frame = pd.DataFrame(
        {
            "time": ["2026-01-10", "2026-02-10", "2026-05-10"],
            "signal": [1, -1, 1],
            "true_ret_24_dir_atr": [1.0, -1.0, 2.0],
        }
    )
    frame.to_csv(predictions, sep=";", index=False)

    code = main(
        [
            "--forward-predictions",
            str(predictions),
            "--output-dir",
            str(output),
            "--historical-pf",
            "8.18",
        ]
    )

    assert code == 0
    assert (output / "summary.json").exists()
    assert (output / "time_slices.csv").exists()
    payload = json.loads((output / "summary.json").read_text(encoding="utf-8"))
    assert payload["verdict"] in {"confirmed", "watch", "revisit"}
```

- [ ] **Step 3.2: Run focused test and confirm failure**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_quantile_forward_validation.py::test_main_writes_summary_and_time_slices -q
```

Expected: missing `main`.

- [ ] **Step 3.3: Implement CLI**

Add CLI:

- `--forward-predictions`
- `--output-dir`
- `--historical-pf`
- `--slice-mode`

Behavior:

- read forward predictions CSV with `sep=";"`
- require columns `time`, `signal`, `true_ret_24_dir_atr`
- keep only `signal != 0`
- compute global metrics
- compute time slices
- count negative slices with `pf < 1.0`
- call `decide_operational_verdict(...)`
- write:
  - `summary.json`
  - `time_slices.csv`
  - `run_metadata.json`

Return:

- `0` for success
- `2` for missing or invalid input

- [ ] **Step 3.4: Run tests**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_quantile_forward_validation.py -q
```

Expected: all tests pass.

- [ ] **Step 3.5: Commit**

Run:

```bash
git add ML/benchmark_quantile_forward_validation.py tests/test_benchmark_quantile_forward_validation.py
git commit -m "quantile: add forward validation cli"
```

---

## Task 4: Run Benchmark And Write Verdict Report

**Files:**

- Create artefacts under: `ML/reports/quantile_forward_validation/`
- Create: `docs/reports/2026-04-13-quantile-forward-validation.md`

- [ ] **Step 4.1: Run frozen benchmark**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m ML.benchmark_quantile_forward_validation \
  --forward-predictions <forward_predictions_csv> \
  --output-dir ML/reports/quantile_forward_validation \
  --historical-pf 8.178675196069868
```

Expected:

- command exits `0`
- `summary.json`, `time_slices.csv`, `run_metadata.json` are written
- verdict is one of `confirmed / watch / revisit`

- [ ] **Step 4.2: Inspect artefacts**

Run:

```bash
sed -n '1,160p' ML/reports/quantile_forward_validation/summary.json
head -n 20 ML/reports/quantile_forward_validation/time_slices.csv
```

Expected:

- verdict is present
- PF and trades are visible
- time slices are populated or explicitly empty due to low support

- [ ] **Step 4.3: Write verdict report**

Create `docs/reports/2026-04-13-quantile-forward-validation.md` with:

- цель;
- frozen rule source;
- forward data window;
- metrics;
- time-slice breakdown;
- operational verdict;
- practical decision;
- limitations.

- [ ] **Step 4.4: Commit**

Run:

```bash
git add ML/reports/quantile_forward_validation docs/reports/2026-04-13-quantile-forward-validation.md
git commit -m "quantile: record forward validation verdict"
```

---

## Task 5: Stage Close

**Files:**

- Modify: `CHANGELOG.md`
- Modify: `CONTEXT_HANDOFF.md`
- Modify: `docs/superpowers/roadmap.md`
- Modify: `wiki/research/execution-tracks.md`
- Modify generated wiki files as needed

- [ ] **Step 5.1: Update project state**

Update:

- `CHANGELOG.md`
- `CONTEXT_HANDOFF.md`
- `docs/superpowers/roadmap.md`

with the forward validation verdict and next operational action.

- [ ] **Step 5.2: Update wiki**

Add the new report into `wiki/research/execution-tracks.md`, update `wiki/index.md`, append `wiki/log.md`, then run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python wiki/wiki.py generate
```

- [ ] **Step 5.3: Final verification**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_quantile_forward_validation.py -q
```

Expected: all tests pass.

- [ ] **Step 5.4: Commit**

Run:

```bash
git add CHANGELOG.md CONTEXT_HANDOFF.md docs/superpowers/roadmap.md wiki docs/reports/2026-04-13-quantile-forward-validation.md
git commit -m "docs: close quantile forward validation stage"
```

---

## Definition Of Done

- Frozen forward benchmark exists.
- No rule retune happened.
- Operational verdict is written.
- Report and stage documents are synced.
- Tests pass.

---

## Self-Review

- Spec coverage: frozen rule, PF-first verdict, time-slice diagnostics, and operational status are covered.
- Placeholder scan: no placeholders remain.
- Scope check: execution improvement is not mixed into this plan.
