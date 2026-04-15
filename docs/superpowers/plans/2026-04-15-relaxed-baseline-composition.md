# Relaxed Baseline Composition Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Проверить, можно ли ослабить frozen `entry_path_v1_quantile`, увеличить число сделок хотя бы примерно вдвое и затем добиться заметного улучшения через `session` и `pred_adv12` без неконтролируемого перебора.

**Architecture:** Один Python benchmark поверх уже существующих quantile prediction artifacts. Порядок жёсткий: сначала поиск расширенного baseline на `validation`, затем его отдельная проверка, затем `session` отдельно, затем `pred_adv12` отдельно, и только потом ограниченная combined-проверка. `Test` используется только как frozen confirmation после каждого validation verdict.

**Tech Stack:** Python 3.11, pandas, numpy, pytest, существующие helpers из `ML/benchmark_entry_path_v1_quantile_filter.py`, артефакты `ML/reports/entry_path_v1_quantile_selected_rule.json` и `ML/reports/entry_path_v1_quantile_robustness/`.

---

## File Structure

### Read First

- `AGENTS.md`
- `CONTEXT_HANDOFF.md`
- `docs/superpowers/specs/2026-04-15-quantile-next-research-design.md`
- `docs/reports/2026-04-12-quantile-status-decision.md`
- `docs/reports/2026-04-13-pf-uplift-discovery.md`
- `docs/reports/2026-04-13-quantile-forward-validation.md`
- `ML/benchmark_entry_path_v1_quantile_n_boost.py`
- `ML/benchmark_quantile_early_timeout.py`

### Files To Create

- `ML/benchmark_quantile_relaxed_composition.py`
- `tests/test_benchmark_quantile_relaxed_composition.py`
- `ML/reports/quantile_relaxed_composition/validation_baseline_grid.csv`
- `ML/reports/quantile_relaxed_composition/test_baseline_grid.csv`
- `ML/reports/quantile_relaxed_composition/selected_baseline.json`
- `ML/reports/quantile_relaxed_composition/validation_filter_grid.csv`
- `ML/reports/quantile_relaxed_composition/test_filter_grid.csv`
- `ML/reports/quantile_relaxed_composition/final_verdict.json`
- `ML/reports/quantile_relaxed_composition/run_metadata.json`
- `docs/reports/2026-04-15-quantile-relaxed-baseline-composition.md`

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

- `quantile` signal source stays frozen.
- Baseline search is limited to a small relaxed family of the existing rule, not a new signal search.
- Baseline must be selected on `validation` only.
- Baseline is viable only if it reaches the target trade expansion and still passes a minimum quality gate.
- `session` and `pred_adv12` are evaluated separately before any combined run.
- Combined run is allowed only if at least one standalone filter has a meaningful and noticeable validation result.
- Final comparison must include both relaxed baseline and frozen `entry_path_v1_quantile`.
- Final verdict must be only one of:
  - `relaxed_baseline_not_viable`
  - `relaxed_baseline_viable_but_no_significant_filter_uplift`
  - `relaxed_composition_candidate`

---

## Task 1: Build Relaxed Baseline Candidate Grid

**Files:**

- Create: `ML/benchmark_quantile_relaxed_composition.py`
- Create: `tests/test_benchmark_quantile_relaxed_composition.py`

- [ ] **Step 1.1: Write failing tests for baseline candidate enumeration and metrics**

Add:

```python
import pandas as pd

from ML.benchmark_quantile_relaxed_composition import (
    build_relaxed_candidate_grid,
    summarize_selected_trades,
)


def test_build_relaxed_candidate_grid_limits_search_space():
    result = build_relaxed_candidate_grid()

    assert result == [
        ("lb_gt_m", 0.15),
        ("lb_gt_m", 0.20),
        ("lb_gt_m", 0.25),
        ("lb_gt_m", 0.30),
        ("lb_gt_m", 0.35),
    ]


def test_summarize_selected_trades_counts_pf_and_year_failures():
    frame = pd.DataFrame(
        {
            "time": ["2024.01.01 00:00", "2024.02.01 00:00", "2025.01.01 00:00"],
            "true_ret_24_dir_atr": [2.0, -1.0, 3.0],
        }
    )

    result = summarize_selected_trades(frame, min_year_trades=1)

    assert result["trades"] == 3
    assert result["pf"] == 5.0
    assert result["negative_year_slices"] == 0
```

- [ ] **Step 1.2: Run tests to confirm failure**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_quantile_relaxed_composition.py -q
```

Expected: import failure because module does not exist yet.

- [ ] **Step 1.3: Implement minimal candidate-grid helpers**

Create `ML/benchmark_quantile_relaxed_composition.py` with:

```python
from __future__ import annotations

import math

import pandas as pd


def build_relaxed_candidate_grid() -> list[tuple[str, float]]:
    return [
        ("lb_gt_m", 0.15),
        ("lb_gt_m", 0.20),
        ("lb_gt_m", 0.25),
        ("lb_gt_m", 0.30),
        ("lb_gt_m", 0.35),
    ]


def summarize_selected_trades(frame: pd.DataFrame, min_year_trades: int) -> dict:
    work = frame.copy()
    work["time"] = pd.to_datetime(work["time"], format="%Y.%m.%d %H:%M", errors="raise")
    pnl = work["true_ret_24_dir_atr"].astype(float)
    gross_profit = float(pnl[pnl > 0].sum())
    gross_loss = float(-pnl[pnl < 0].sum())
    if gross_loss == 0.0:
        pf = math.inf if gross_profit > 0.0 else 0.0
    else:
        pf = gross_profit / gross_loss
    work["year"] = work["time"].dt.year
    negative_year_slices = 0
    for _, group in work.groupby("year"):
        if len(group) < min_year_trades:
            continue
        if float(group["true_ret_24_dir_atr"].sum()) < 0.0:
            negative_year_slices += 1
    return {
        "trades": int(len(work)),
        "pf": pf,
        "win_rate": float((pnl > 0).mean()) if len(work) else 0.0,
        "mean_pnl_atr": float(pnl.mean()) if len(work) else 0.0,
        "negative_year_slices": negative_year_slices,
    }
```

- [ ] **Step 1.4: Run tests**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_quantile_relaxed_composition.py -q
```

Expected: `2 passed`.

- [ ] **Step 1.5: Commit**

Run:

```bash
git add ML/benchmark_quantile_relaxed_composition.py tests/test_benchmark_quantile_relaxed_composition.py
git commit -m "quantile: add relaxed baseline benchmark helpers"
```

---

## Task 2: Select A Viable Relaxed Baseline On Validation

**Files:**

- Modify: `ML/benchmark_quantile_relaxed_composition.py`
- Modify: `tests/test_benchmark_quantile_relaxed_composition.py`

- [ ] **Step 2.1: Write failing tests for baseline selection**

Add:

```python
from ML.benchmark_quantile_relaxed_composition import (
    choose_relaxed_baseline,
    evaluate_relaxed_baselines,
)


def test_choose_relaxed_baseline_prefers_first_candidate_that_hits_trade_target():
    grid = pd.DataFrame(
        [
            {"candidate": "a", "trades": 40, "pf": 4.0, "negative_year_slices": 1, "mean_pnl_atr": 1.2},
            {"candidate": "b", "trades": 64, "pf": 3.0, "negative_year_slices": 0, "mean_pnl_atr": 1.1},
            {"candidate": "c", "trades": 70, "pf": 2.8, "negative_year_slices": 0, "mean_pnl_atr": 0.9},
        ]
    )

    result = choose_relaxed_baseline(
        grid,
        frozen_validation_trades=32,
        trade_multiplier=2.0,
        min_pf=2.0,
    )

    assert result["candidate"] == "b"


def test_choose_relaxed_baseline_returns_not_viable_when_target_is_missed():
    grid = pd.DataFrame(
        [
            {"candidate": "a", "trades": 40, "pf": 3.0, "negative_year_slices": 0, "mean_pnl_atr": 1.0},
        ]
    )

    result = choose_relaxed_baseline(
        grid,
        frozen_validation_trades=32,
        trade_multiplier=2.0,
        min_pf=2.0,
    )

    assert result["verdict"] == "relaxed_baseline_not_viable"
```

- [ ] **Step 2.2: Run focused tests**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_quantile_relaxed_composition.py::test_choose_relaxed_baseline_prefers_first_candidate_that_hits_trade_target -q
```

Expected: missing functions.

- [ ] **Step 2.3: Implement validation grid and baseline selector**

Extend `ML/benchmark_quantile_relaxed_composition.py` with:

```python
from ML.benchmark_entry_path_v1_quantile_filter import (
    apply_conformal_correction,
    attach_baseline_score,
    build_rule_mask,
    compute_conformal_correction,
    compute_m_at_quantile,
    load_baseline_rule,
    load_prediction_frame,
)


def evaluate_relaxed_baselines(
    prediction_frame: pd.DataFrame,
    baseline_frame: pd.DataFrame,
    baseline_threshold: float,
    min_year_trades: int,
) -> pd.DataFrame:
    work = attach_baseline_score(prediction_frame, baseline_frame)
    work["baseline_selected"] = (
        (work["signal"].to_numpy() != 0)
        & (work["baseline_score"].to_numpy(dtype=float) >= baseline_threshold)
    )
    selected = work.loc[work["baseline_selected"]].copy()
    correction = compute_conformal_correction(
        selected["true_ret_24_dir_atr"].to_numpy(dtype=float),
        selected["pred_ret_24_q10"].to_numpy(dtype=float),
        selected["pred_ret_24_q90"].to_numpy(dtype=float),
        alpha=0.10,
    )
    work = apply_conformal_correction(work, correction)
    rows = []
    for rule, quantile in build_relaxed_candidate_grid():
        m = compute_m_at_quantile(work, quantile)
        mask = build_rule_mask(work, rule=rule, m=m, w=0.0)
        summary = summarize_selected_trades(work.loc[mask, ["time", "true_ret_24_dir_atr"]], min_year_trades)
        rows.append(
            {
                "candidate": f"{rule}_q{int(quantile * 100):02d}",
                "rule": rule,
                "quantile": quantile,
                "m": m,
                **summary,
            }
        )
    return pd.DataFrame(rows)


def choose_relaxed_baseline(
    grid: pd.DataFrame,
    frozen_validation_trades: int,
    trade_multiplier: float,
    min_pf: float,
) -> dict:
    target_trades = int(math.ceil(frozen_validation_trades * trade_multiplier))
    viable = grid.loc[
        (grid["trades"] >= target_trades)
        & (grid["pf"] >= min_pf)
        & (grid["negative_year_slices"] == 0)
    ].sort_values(["pf", "mean_pnl_atr", "trades"], ascending=[False, False, False])
    if viable.empty:
        return {
            "verdict": "relaxed_baseline_not_viable",
            "target_trades": target_trades,
            "candidate": None,
        }
    row = viable.iloc[0]
    return {
        "verdict": "baseline_candidate",
        "target_trades": target_trades,
        "candidate": row["candidate"],
        "rule": row["rule"],
        "quantile": float(row["quantile"]),
        "m": float(row["m"]),
    }
```

- [ ] **Step 2.4: Run tests**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_quantile_relaxed_composition.py -q
```

Expected: all tests pass.

- [ ] **Step 2.5: Run validation baseline benchmark**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m ML.benchmark_quantile_relaxed_composition \
  --mode baseline_only \
  --validation-predictions ML/reports/entry_path_v1_quantile_validation_predictions.csv \
  --baseline-validation-predictions ML/reports/entry_path_v1_validation_predictions.csv \
  --selected-rule ML/reports/entry_path_v1_quantile_selected_rule.json \
  --output-dir ML/reports/quantile_relaxed_composition
```

Expected:

```text
validation_baseline_grid.csv written
selected_baseline.json written
```

- [ ] **Step 2.6: Commit**

Run:

```bash
git add ML/benchmark_quantile_relaxed_composition.py tests/test_benchmark_quantile_relaxed_composition.py
git commit -m "quantile: select relaxed baseline candidate"
```

---

## Task 3: Evaluate Session And pred_adv12 Separately

**Files:**

- Modify: `ML/benchmark_quantile_relaxed_composition.py`
- Modify: `tests/test_benchmark_quantile_relaxed_composition.py`

- [ ] **Step 3.1: Write failing tests for filter evaluation order**

Add:

```python
from ML.benchmark_quantile_relaxed_composition import (
    apply_pred_adv_filter,
    apply_session_filter,
    evaluate_filters,
)


def test_apply_session_filter_excludes_ny_rows():
    frame = pd.DataFrame(
        {
            "session": ["asia", "ny", "overlap"],
            "pred_adv_12_atr": [0.1, 0.2, 0.3],
        }
    )

    result = apply_session_filter(frame)

    assert list(result["session"]) == ["asia", "overlap"]


def test_apply_pred_adv_filter_keeps_values_below_threshold():
    frame = pd.DataFrame(
        {
            "pred_adv_12_atr": [0.01, 0.02, 0.03],
        }
    )

    result = apply_pred_adv_filter(frame, threshold=0.02)

    assert list(result["pred_adv_12_atr"]) == [0.01, 0.02]
```

- [ ] **Step 3.2: Run focused tests**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_quantile_relaxed_composition.py::test_apply_session_filter_excludes_ny_rows -q
```

Expected: missing functions.

- [ ] **Step 3.3: Implement standalone filter helpers and validation evaluation**

Extend `ML/benchmark_quantile_relaxed_composition.py` with:

```python
def label_session_bucket(frame: pd.DataFrame) -> pd.DataFrame:
    work = frame.copy()
    work["time"] = pd.to_datetime(work["time"], format="%Y.%m.%d %H:%M", errors="raise")
    hours = work["time"].dt.hour
    work["session"] = "ny"
    work.loc[hours.between(0, 6), "session"] = "asia"
    work.loc[hours.between(7, 12), "session"] = "london"
    work.loc[hours.between(13, 18), "session"] = "overlap"
    return work


def apply_session_filter(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.loc[frame["session"] != "ny"].copy()


def apply_pred_adv_filter(frame: pd.DataFrame, threshold: float) -> pd.DataFrame:
    return frame.loc[frame["pred_adv_12_atr"].astype(float) <= threshold].copy()


def evaluate_filters(selected_frame: pd.DataFrame, min_year_trades: int) -> pd.DataFrame:
    session_frame = apply_session_filter(label_session_bucket(selected_frame))
    pred_adv_threshold = float(selected_frame["pred_adv_12_atr"].astype(float).quantile(0.75))
    pred_adv_frame = apply_pred_adv_filter(selected_frame, threshold=pred_adv_threshold)
    rows = []
    rows.append({"filter_name": "session_only", "threshold": None, **summarize_selected_trades(session_frame, min_year_trades)})
    rows.append({"filter_name": "pred_adv12_only", "threshold": pred_adv_threshold, **summarize_selected_trades(pred_adv_frame, min_year_trades)})
    return pd.DataFrame(rows)
```

- [ ] **Step 3.4: Run tests**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_quantile_relaxed_composition.py -q
```

Expected: all tests pass.

- [ ] **Step 3.5: Run validation filter benchmark**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m ML.benchmark_quantile_relaxed_composition \
  --mode filters_only \
  --validation-predictions ML/reports/entry_path_v1_quantile_validation_predictions.csv \
  --baseline-validation-predictions ML/reports/entry_path_v1_validation_predictions.csv \
  --selected-rule ML/reports/entry_path_v1_quantile_selected_rule.json \
  --output-dir ML/reports/quantile_relaxed_composition
```

Expected:

```text
validation_filter_grid.csv written
```

- [ ] **Step 3.6: Commit**

Run:

```bash
git add ML/benchmark_quantile_relaxed_composition.py tests/test_benchmark_quantile_relaxed_composition.py
git commit -m "quantile: evaluate relaxed baseline filters separately"
```

---

## Task 4: Allow Combined Filter Only When Justified

**Files:**

- Modify: `ML/benchmark_quantile_relaxed_composition.py`
- Modify: `tests/test_benchmark_quantile_relaxed_composition.py`

- [ ] **Step 4.1: Write failing test for combination gate**

Add:

```python
from ML.benchmark_quantile_relaxed_composition import should_run_combined_filter


def test_should_run_combined_filter_requires_meaningful_standalone_result():
    grid = pd.DataFrame(
        [
            {"filter_name": "session_only", "trades": 70, "pf": 3.5, "negative_year_slices": 0, "pf_delta_vs_baseline": 0.8},
            {"filter_name": "pred_adv12_only", "trades": 30, "pf": 1.1, "negative_year_slices": 2},
        ]
    )

    assert should_run_combined_filter(grid) is True
```

- [ ] **Step 4.2: Run focused test**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_quantile_relaxed_composition.py::test_should_run_combined_filter_requires_meaningful_standalone_result -q
```

Expected: missing function.

- [ ] **Step 4.3: Implement combination gate and final verdict logic**

Extend `ML/benchmark_quantile_relaxed_composition.py` with:

```python
def should_run_combined_filter(grid: pd.DataFrame) -> bool:
    meaningful = grid.loc[
        (grid["trades"] >= 30)
        & (grid["pf"] >= 2.0)
        & (grid["negative_year_slices"] == 0)
        & (grid["pf_delta_vs_baseline"] >= 0.5)
    ]
    return not meaningful.empty


def evaluate_combined_filter(selected_frame: pd.DataFrame, min_year_trades: int) -> dict:
    session_frame = apply_session_filter(label_session_bucket(selected_frame))
    threshold = float(selected_frame["pred_adv_12_atr"].astype(float).quantile(0.75))
    combined = apply_pred_adv_filter(session_frame, threshold=threshold)
    return {
        "filter_name": "session_plus_pred_adv12",
        "threshold": threshold,
        **summarize_selected_trades(combined, min_year_trades),
    }
```

- [ ] **Step 4.4: Run tests**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_quantile_relaxed_composition.py -q
```

Expected: all tests pass.

- [ ] **Step 4.5: Run full benchmark with frozen test check**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m ML.benchmark_quantile_relaxed_composition \
  --mode full \
  --validation-predictions ML/reports/entry_path_v1_quantile_validation_predictions.csv \
  --test-predictions ML/reports/entry_path_v1_quantile_test_predictions.csv \
  --baseline-validation-predictions ML/reports/entry_path_v1_validation_predictions.csv \
  --baseline-test-predictions ML/reports/entry_path_test_predictions.csv \
  --selected-rule ML/reports/entry_path_v1_quantile_selected_rule.json \
  --output-dir ML/reports/quantile_relaxed_composition
```

Expected:

```text
test_baseline_grid.csv written
test_filter_grid.csv written
final_verdict.json written
```

- [ ] **Step 4.6: Commit**

Run:

```bash
git add ML/benchmark_quantile_relaxed_composition.py tests/test_benchmark_quantile_relaxed_composition.py
git commit -m "quantile: gate combined relaxed composition check"
```

---

## Task 5: Report And Project Memory Sync

**Files:**

- Create: `docs/reports/2026-04-15-quantile-relaxed-baseline-composition.md`
- Modify: `CHANGELOG.md`
- Modify: `CONTEXT_HANDOFF.md`
- Modify: `docs/superpowers/roadmap.md`
- Modify: `wiki/research/execution-tracks.md`
- Modify: `wiki/index.md`
- Modify: `wiki/log.md`
- Modify: `wiki/REPO_integrity.md`

- [ ] **Step 5.1: Write the report template with fixed verdict slots**

Create `docs/reports/2026-04-15-quantile-relaxed-baseline-composition.md` with:

```md
# Quantile Relaxed Baseline Composition

> **Date**: 2026-04-15
> **Status**: Completed
> **Goal**: Проверить relaxed baseline и отдельно оценить `session`, `pred_adv12`, а затем их сочетание только при наличии оснований

## Results

- frozen quantile baseline: `TBD`
- relaxed baseline: `TBD`
- session-only over relaxed baseline: `TBD`
- pred_adv12-only over relaxed baseline: `TBD`
- combined filter: `TBD or skipped`

## Verdict

- `relaxed_baseline_not_viable`
- или `relaxed_baseline_viable_but_no_significant_filter_uplift`
- или `relaxed_composition_candidate`
```

- [ ] **Step 5.2: Fill report from generated artifacts**

Use:

```bash
sed -n '1,220p' ML/reports/quantile_relaxed_composition/final_verdict.json
sed -n '1,220p' ML/reports/quantile_relaxed_composition/selected_baseline.json
```

Expected: enough numbers to replace every `TBD`.

- [ ] **Step 5.3: Sync changelog and handoff**

Update:

- `CHANGELOG.md` with one experiment entry
- `CONTEXT_HANDOFF.md` with the new verdict and next step
- `docs/superpowers/roadmap.md` with the track status

- [ ] **Step 5.4: Run wiki ingest and integrity refresh**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python wiki/wiki.py generate
```

Expected:

```text
wiki/REPO_integrity.md updated
```

- [ ] **Step 5.5: Verification**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_quantile_relaxed_composition.py -q
```

Expected: full suite green.

- [ ] **Step 5.6: Commit**

Run:

```bash
git add docs/reports/2026-04-15-quantile-relaxed-baseline-composition.md CHANGELOG.md CONTEXT_HANDOFF.md docs/superpowers/roadmap.md wiki/research/execution-tracks.md wiki/index.md wiki/log.md wiki/REPO_integrity.md
git commit -m "docs: record relaxed baseline composition verdict"
```

---

## Self-Review

- Spec coverage: plan includes relaxed baseline search, standalone filter checks, combined-gate restriction, frozen test confirmation, and comparison against frozen quantile.
- Placeholder scan: implementation steps are concrete; only the final report template intentionally uses `TBD`, which must be replaced during execution before completion.
- Type consistency: plan uses one benchmark module, one report directory, one verdict file, and one fixed set of verdict values throughout.
