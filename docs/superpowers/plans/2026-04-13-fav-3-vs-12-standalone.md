# Fav 3 vs 12 Standalone Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Проверить `fav_3_vs_12` как самостоятельный режим отбора и дать честный verdict: `baseline_candidate` или `reject_as_standalone`.

**Architecture:** Создаётся отдельный research benchmark без MT4-интеграции и без нового обучения. Скрипт использует уже сгенерированный aligned `updn_active_source`, строит сетку порогов, ищет зону устойчивости на `validation`, затем один раз проверяет выбранный порог на `test`.

**Tech Stack:** Python 3.11, pandas/numpy, pytest, существующие функции из `ML.benchmark_quantile_fav_composition` и `ML.benchmark_entry_path_v1_quantile_filter`. Новые зависимости не добавлять.

---

## File Structure

### Read First

- `AGENTS.md`
- `CONTEXT_HANDOFF.md`
- `docs/superpowers/specs/2026-04-13-fav-3-vs-12-standalone-design.md`
- `docs/reports/2026-04-13-quantile-fav-composition.md`
- `ML/benchmark_quantile_fav_composition.py`
- `ML/export_updn_active_predictions.py`
- `tests/test_benchmark_quantile_fav_composition.py`

### Existing Inputs

- `ML/reports/quantile_fav_composition/updn_active_source/validation_active_updn_predictions.csv`
- `ML/reports/quantile_fav_composition/updn_active_source/test_active_updn_predictions.csv`
- `ML/reports/quantile_fav_composition/updn_active_source/metadata.json`
- `ML/reports/entry_path_v1_quantile_robustness/seed_007/entry_path_v1_quantile_validation_predictions.csv`
- `ML/reports/entry_path_v1_quantile_robustness/seed_007/entry_path_v1_quantile_test_predictions.csv`

### Files To Create

- `ML/benchmark_fav_3_vs_12_standalone.py`
- `tests/test_benchmark_fav_3_vs_12_standalone.py`
- `ML/reports/fav_3_vs_12_standalone/threshold_grid_validation.csv`
- `ML/reports/fav_3_vs_12_standalone/threshold_grid_test.csv`
- `ML/reports/fav_3_vs_12_standalone/selected_threshold.json`
- `ML/reports/fav_3_vs_12_standalone/yearly_breakdown_validation.csv`
- `ML/reports/fav_3_vs_12_standalone/yearly_breakdown_test.csv`
- `ML/reports/fav_3_vs_12_standalone/verdict.json`
- `ML/reports/fav_3_vs_12_standalone/run_metadata.json`
- `docs/reports/2026-04-13-fav-3-vs-12-standalone.md`

### Files To Update At Stage Close

- `CONTEXT_HANDOFF.md`
- `CHANGELOG.md`
- `docs/superpowers/roadmap.md`
- `wiki/research/execution-tracks.md`
- `wiki/index.md`
- `wiki/log.md`
- `wiki/REPO_integrity.md`

---

## Acceptance Rules

### Hard Rules

- `fav_3_vs_12 = pred_fav_3 / pred_fav_12`, with safe denominator clipping to avoid division by zero.
- Selection direction: `fav_3_vs_12 <= threshold`.
- Threshold is selected only from `validation`.
- `test` is used only once after threshold selection.
- No `quantile` mask is applied.
- No MT4 files are changed.
- No model training is performed unless the existing aligned source is missing or invalid.

### Suggested Gate Defaults

Use these defaults unless data inspection proves they are inappropriate and the report explains why:

- `min_trades_validation = 30`
- `min_trades_test = 30`
- `min_pf_validation = 2.0`
- `min_pf_test = 1.5`
- `max_negative_year_slices_validation = 0`
- `max_negative_year_slices_test = 0`
- stability window size: `5` neighboring thresholds
- at least `3` thresholds inside the window must pass the basic gates

These values are intentionally weaker than `quantile`, because this stage checks a possible second system, not a replacement for `quantile`.

---

## Task 1: Data Wiring And Core Metrics

**Files:**

- Create: `ML/benchmark_fav_3_vs_12_standalone.py`
- Test: `tests/test_benchmark_fav_3_vs_12_standalone.py`

- [ ] **Step 1.1: Write failing tests for feature construction and metrics**

Add tests:

```python
import pandas as pd

from ML.benchmark_fav_3_vs_12_standalone import (
    add_fav_ratio,
    compute_metrics,
)


def test_add_fav_ratio_uses_safe_denominator():
    frame = pd.DataFrame(
        {
            "pred_fav_3": [1.0, 2.0],
            "pred_fav_12": [2.0, 0.0],
        }
    )

    result = add_fav_ratio(frame)

    assert result.loc[0, "fav_3_vs_12"] == 0.5
    assert result.loc[1, "fav_3_vs_12"] > 1_000_000


def test_compute_metrics_counts_trades_and_pf():
    frame = pd.DataFrame(
        {
            "pnl_atr": [2.0, -1.0, 3.0],
        }
    )

    result = compute_metrics(frame)

    assert result["n_trades"] == 3
    assert result["gross_profit"] == 5.0
    assert result["gross_loss"] == 1.0
    assert result["pf"] == 5.0
```

- [ ] **Step 1.2: Run tests and confirm failure**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_fav_3_vs_12_standalone.py -q
```

Expected: import failure because `ML/benchmark_fav_3_vs_12_standalone.py` does not exist yet.

- [ ] **Step 1.3: Implement minimal metric helpers**

Create `ML/benchmark_fav_3_vs_12_standalone.py` with:

```python
from __future__ import annotations

import math
from pathlib import Path

import pandas as pd


EPS = 1e-9


def add_fav_ratio(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    denom = result["pred_fav_12"].clip(lower=EPS)
    result["fav_3_vs_12"] = result["pred_fav_3"] / denom
    return result


def compute_metrics(frame: pd.DataFrame) -> dict[str, float | int | None]:
    n_trades = int(len(frame))
    if n_trades == 0:
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
    pf = math.inf if gross_loss == 0 and gross_profit > 0 else gross_profit / gross_loss if gross_loss > 0 else None
    return {
        "n_trades": n_trades,
        "wins": wins,
        "losses": losses,
        "gross_profit": gross_profit,
        "gross_loss": gross_loss,
        "pf": pf,
        "win_rate": wins / n_trades,
        "mean_pnl_atr": float(pnl.mean()),
    }
```

- [ ] **Step 1.4: Run tests and confirm pass**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_fav_3_vs_12_standalone.py -q
```

Expected: `2 passed`.

- [ ] **Step 1.5: Commit**

Run:

```bash
git add ML/benchmark_fav_3_vs_12_standalone.py tests/test_benchmark_fav_3_vs_12_standalone.py
git commit -m "fav_3_vs_12: add standalone metric helpers"
```

---

## Task 2: Threshold Grid

**Files:**

- Modify: `ML/benchmark_fav_3_vs_12_standalone.py`
- Modify: `tests/test_benchmark_fav_3_vs_12_standalone.py`

- [ ] **Step 2.1: Write failing test for threshold grid**

Add:

```python
from ML.benchmark_fav_3_vs_12_standalone import evaluate_threshold_grid


def test_evaluate_threshold_grid_selects_ratio_lte_threshold():
    frame = pd.DataFrame(
        {
            "fav_3_vs_12": [0.2, 0.5, 0.8],
            "pnl_atr": [1.0, -1.0, 2.0],
            "time": ["2022-01-01", "2022-01-02", "2022-01-03"],
        }
    )

    result = evaluate_threshold_grid(frame, thresholds=[0.3, 0.6])

    assert list(result["threshold"]) == [0.3, 0.6]
    assert list(result["n_trades"]) == [1, 2]
    assert list(result["pf"]) == [float("inf"), 1.0]
```

- [ ] **Step 2.2: Run test and confirm failure**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_fav_3_vs_12_standalone.py::test_evaluate_threshold_grid_selects_ratio_lte_threshold -q
```

Expected: import failure for `evaluate_threshold_grid`.

- [ ] **Step 2.3: Implement threshold grid**

Add:

```python
def evaluate_threshold_grid(frame: pd.DataFrame, thresholds: list[float]) -> pd.DataFrame:
    rows = []
    for threshold in thresholds:
        selected = frame[frame["fav_3_vs_12"] <= threshold]
        metrics = compute_metrics(selected)
        rows.append({"threshold": float(threshold), **metrics})
    return pd.DataFrame(rows)
```

- [ ] **Step 2.4: Run tests**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_fav_3_vs_12_standalone.py -q
```

Expected: all tests pass.

- [ ] **Step 2.5: Commit**

Run:

```bash
git add ML/benchmark_fav_3_vs_12_standalone.py tests/test_benchmark_fav_3_vs_12_standalone.py
git commit -m "fav_3_vs_12: evaluate standalone threshold grid"
```

---

## Task 3: Yearly Stability And Window Selection

**Files:**

- Modify: `ML/benchmark_fav_3_vs_12_standalone.py`
- Modify: `tests/test_benchmark_fav_3_vs_12_standalone.py`

- [ ] **Step 3.1: Write failing tests for yearly breakdown and stable window**

Add:

```python
from ML.benchmark_fav_3_vs_12_standalone import (
    compute_yearly_breakdown,
    select_stable_threshold,
)


def test_compute_yearly_breakdown_reports_negative_years():
    frame = pd.DataFrame(
        {
            "time": ["2022-01-01", "2022-01-02", "2023-01-01", "2023-01-02"],
            "pnl_atr": [2.0, 1.0, -2.0, 1.0],
        }
    )

    result = compute_yearly_breakdown(frame)

    assert list(result["year"]) == [2022, 2023]
    assert result.loc[result["year"] == 2023, "pf"].iloc[0] == 0.5


def test_select_stable_threshold_prefers_passing_window_over_peak():
    grid = pd.DataFrame(
        {
            "threshold": [0.1, 0.2, 0.3, 0.4, 0.5],
            "n_trades": [35, 36, 37, 38, 39],
            "pf": [2.1, 2.2, 2.3, 10.0, 1.0],
            "negative_year_slices": [0, 0, 0, 1, 0],
        }
    )

    selected = select_stable_threshold(
        grid,
        min_trades=30,
        min_pf=2.0,
        max_negative_year_slices=0,
        window_size=3,
        min_passing_in_window=3,
    )

    assert selected["verdict"] == "selected"
    assert selected["threshold"] == 0.3
```

- [ ] **Step 3.2: Run tests and confirm failure**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_fav_3_vs_12_standalone.py -q
```

Expected: missing functions.

- [ ] **Step 3.3: Implement yearly breakdown and stable selection**

Add:

```python
def compute_yearly_breakdown(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=["year", "n_trades", "wins", "losses", "gross_profit", "gross_loss", "pf", "win_rate", "mean_pnl_atr"])

    working = frame.copy()
    working["year"] = pd.to_datetime(working["time"]).dt.year
    rows = []
    for year, group in working.groupby("year", sort=True):
        rows.append({"year": int(year), **compute_metrics(group)})
    return pd.DataFrame(rows)


def count_negative_year_slices(frame: pd.DataFrame) -> int:
    yearly = compute_yearly_breakdown(frame)
    if yearly.empty:
        return 0
    pf = pd.to_numeric(yearly["pf"], errors="coerce")
    return int((pf < 1.0).sum())


def annotate_grid_with_yearly_failures(frame: pd.DataFrame, grid: pd.DataFrame) -> pd.DataFrame:
    result = grid.copy()
    result["negative_year_slices"] = [
        count_negative_year_slices(frame[frame["fav_3_vs_12"] <= threshold])
        for threshold in result["threshold"]
    ]
    return result


def select_stable_threshold(
    grid: pd.DataFrame,
    *,
    min_trades: int,
    min_pf: float,
    max_negative_year_slices: int,
    window_size: int,
    min_passing_in_window: int,
) -> dict[str, float | int | str | None]:
    working = grid.copy().reset_index(drop=True)
    pf = pd.to_numeric(working["pf"], errors="coerce").fillna(-1.0)
    working["passes_basic_gate"] = (
        (working["n_trades"] >= min_trades)
        & (pf >= min_pf)
        & (working["negative_year_slices"] <= max_negative_year_slices)
    )

    best = None
    half = window_size // 2
    for idx, row in working.iterrows():
        start = max(0, idx - half)
        stop = min(len(working), idx + half + 1)
        window = working.iloc[start:stop]
        passing = int(window["passes_basic_gate"].sum())
        if passing < min_passing_in_window or not bool(row["passes_basic_gate"]):
            continue
        score = (passing, float(row["pf"]), int(row["n_trades"]))
        if best is None or score > best["score"]:
            best = {"idx": idx, "score": score}

    if best is None:
        return {"verdict": "no_stable_threshold", "threshold": None}

    row = working.iloc[best["idx"]]
    return {
        "verdict": "selected",
        "threshold": float(row["threshold"]),
        "n_trades": int(row["n_trades"]),
        "pf": float(row["pf"]),
        "negative_year_slices": int(row["negative_year_slices"]),
    }
```

- [ ] **Step 3.4: Run tests**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_fav_3_vs_12_standalone.py -q
```

Expected: all tests pass.

- [ ] **Step 3.5: Commit**

Run:

```bash
git add ML/benchmark_fav_3_vs_12_standalone.py tests/test_benchmark_fav_3_vs_12_standalone.py
git commit -m "fav_3_vs_12: select stable threshold zone"
```

---

## Task 4: CLI And Artefacts

**Files:**

- Modify: `ML/benchmark_fav_3_vs_12_standalone.py`
- Modify: `tests/test_benchmark_fav_3_vs_12_standalone.py`

- [ ] **Step 4.1: Write failing smoke test for CLI outputs**

Add a test using `tmp_path`:

```python
from pathlib import Path

from ML.benchmark_fav_3_vs_12_standalone import main


def test_main_writes_expected_artefacts(tmp_path: Path):
    source = tmp_path / "updn"
    source.mkdir()
    output = tmp_path / "out"

    validation = pd.DataFrame(
        {
            "time": ["2022-01-01", "2022-01-02", "2023-01-01", "2023-01-02"],
            "signal": [1, -1, 1, -1],
            "pred_fav_3": [0.2, 0.3, 0.2, 0.3],
            "pred_fav_12": [1.0, 1.0, 1.0, 1.0],
            "pnl_atr": [1.0, 1.0, 1.0, 1.0],
        }
    )
    test = validation.copy()
    validation.to_csv(source / "validation_active_updn_predictions.csv", index=False)
    test.to_csv(source / "test_active_updn_predictions.csv", index=False)

    code = main(
        [
            "--updn-active-dir",
            str(source),
            "--output-dir",
            str(output),
            "--thresholds",
            "0.2,0.3,0.4",
            "--min-trades-validation",
            "2",
            "--min-trades-test",
            "2",
            "--min-pf-validation",
            "1.0",
            "--min-pf-test",
            "1.0",
        ]
    )

    assert code == 0
    assert (output / "threshold_grid_validation.csv").exists()
    assert (output / "threshold_grid_test.csv").exists()
    assert (output / "selected_threshold.json").exists()
    assert (output / "verdict.json").exists()
```

- [ ] **Step 4.2: Run smoke test and confirm failure**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_fav_3_vs_12_standalone.py::test_main_writes_expected_artefacts -q
```

Expected: failure because `main` does not exist.

- [ ] **Step 4.3: Implement CLI**

Add CLI that:

- reads `validation_active_updn_predictions.csv` and `test_active_updn_predictions.csv`;
- calls `add_fav_ratio`;
- evaluates the grid on both splits;
- annotates validation grid with yearly failures;
- selects threshold on validation;
- evaluates selected threshold on test;
- writes all artefacts listed in `File Structure`.

Use these defaults:

```python
DEFAULT_UPDN_ACTIVE_DIR = Path("ML/reports/quantile_fav_composition/updn_active_source")
DEFAULT_OUTPUT_DIR = Path("ML/reports/fav_3_vs_12_standalone")
DEFAULT_THRESHOLDS = [round(x / 100, 2) for x in range(20, 121, 2)]
```

The `main(argv: list[str] | None = None) -> int` function must return:

- `0` for successful run;
- `2` for missing input files.

- [ ] **Step 4.4: Run tests**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_fav_3_vs_12_standalone.py -q
```

Expected: all tests pass.

- [ ] **Step 4.5: Commit**

Run:

```bash
git add ML/benchmark_fav_3_vs_12_standalone.py tests/test_benchmark_fav_3_vs_12_standalone.py
git commit -m "fav_3_vs_12: add standalone benchmark cli"
```

---

## Task 5: Run Benchmark And Write Verdict Report

**Files:**

- Create artefacts under: `ML/reports/fav_3_vs_12_standalone/`
- Create: `docs/reports/2026-04-13-fav-3-vs-12-standalone.md`

- [ ] **Step 5.1: Run benchmark**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m ML.benchmark_fav_3_vs_12_standalone
```

Expected:

- command exits `0`;
- all artefacts in `ML/reports/fav_3_vs_12_standalone/` are written;
- `selected_threshold.json` has either `verdict=selected` or `verdict=no_stable_threshold`;
- `verdict.json` has either `baseline_candidate` or `reject_as_standalone`.

- [ ] **Step 5.2: Inspect artefacts**

Run:

```bash
sed -n '1,160p' ML/reports/fav_3_vs_12_standalone/verdict.json
sed -n '1,160p' ML/reports/fav_3_vs_12_standalone/selected_threshold.json
```

Expected:

- selected threshold is chosen only from validation;
- report explains if no stable zone exists.

- [ ] **Step 5.3: Write verdict report**

Create `docs/reports/2026-04-13-fav-3-vs-12-standalone.md` with:

- цель;
- источник данных;
- метод выбора порога;
- validation grid summary;
- selected threshold;
- validation metrics for selected threshold;
- test metrics for selected threshold;
- yearly breakdown;
- verdict;
- limitations;
- next step.

- [ ] **Step 5.4: Commit**

Run:

```bash
git add ML/reports/fav_3_vs_12_standalone docs/reports/2026-04-13-fav-3-vs-12-standalone.md
git commit -m "fav_3_vs_12: record standalone verdict"
```

---

## Task 6: Stage Close

**Files:**

- Modify: `CONTEXT_HANDOFF.md`
- Modify: `CHANGELOG.md`
- Modify: `docs/superpowers/roadmap.md`
- Modify: `wiki/research/execution-tracks.md`
- Modify generated wiki files as required by `wiki/wiki.py generate`

- [ ] **Step 6.1: Update project state**

Update:

- `CONTEXT_HANDOFF.md` with current status, report link, verdict, and next step.
- `CHANGELOG.md` with one `## [2026-04-13]` entry under `### Результаты` and `### Вывод`.
- `docs/superpowers/roadmap.md` with the standalone verdict and link to the report.

- [ ] **Step 6.2: Update wiki**

Use the wiki skill and ingest the new report into `wiki/research/execution-tracks.md`.

Then run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python wiki/wiki.py generate
```

Expected: `wiki/index.md`, `wiki/log.md`, and `wiki/REPO_integrity.md` update if needed.

- [ ] **Step 6.3: Final verification**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_fav_3_vs_12_standalone.py -q
```

Expected: all tests pass.

- [ ] **Step 6.4: Commit**

Run:

```bash
git add CONTEXT_HANDOFF.md CHANGELOG.md docs/superpowers/roadmap.md wiki docs/reports/2026-04-13-fav-3-vs-12-standalone.md
git commit -m "docs: close fav_3_vs_12 standalone stage"
```

---

## Definition Of Done

- New benchmark exists and is covered by tests.
- Threshold is chosen from `validation` only.
- `test` is used only for final confirmation.
- Verdict report exists with `baseline_candidate` or `reject_as_standalone`.
- Project state, changelog, roadmap, and wiki are updated.
- Final test command passes.
- No MT4 files are changed.
- No model training is performed unless explicitly approved after input validation fails.

---

## Self-Review

- Spec coverage: standalone check, threshold zone, yearly stability, test-only confirmation, and verdict are all covered.
- Placeholder scan: no `TBD`, `TODO`, or unspecified implementation steps remain.
- Scope check: plan does not include diversification or production integration.
- Type consistency: core helper names are defined before later tasks use them.
