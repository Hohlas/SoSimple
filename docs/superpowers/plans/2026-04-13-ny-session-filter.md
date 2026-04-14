# NY Session Filter for entry_path_v1_quantile Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Проверить, даёт ли исключение NY-сессии validation-first uplift для frozen `entry_path_v1_quantile`, и только при проходе gate вынести фильтр в Python export path.

**Architecture:** Сначала отдельный benchmark поверх frozen quantile-selected trade set: one-rule, no retrain, no retune, validation decides verdict, test runs only after validation pass. Только после Python gate добавляется session filter в exporter и готовится MT4 parity-check; MQL4 код не меняется до подтверждённого Python verdict.

**Tech Stack:** Python 3.11, pandas/numpy, pytest, существующие quantile artifacts, `API/export_entry_path_v1_quantile_signals.py`, `statistics/signal_tracer.py`, MT4 tester logs.

---

## Decision Notes

- Discovery probe `probe_r_NY_session_exclusion.json` показал сильный uplift на test (`N=34`, `PF=20.276`), но это не production verdict.
- В `trade_enriched.csv` сессии уже размечены как `asia / london / overlap / ny`; текущий кандидат означает **исключить только `ny`** и сохранить остальные session buckets.
- Критический риск этого трека не в PF, а в корректности session tagging: broker time, границы buckets и DST не должны создавать ложный uplift.
- Cross-instrument check не входит в основной gate и не может заменить проверку на canonical instrument.

## Read First

- `AGENTS.md`
- `CONTEXT_HANDOFF.md`
- `docs/reports/2026-04-13-pf-uplift-discovery.md`
- `docs/reports/2026-04-14-quantile-early-timeout.md`
- `ML/reports/pf_uplift_discovery/probe_r_NY_session_exclusion.json`
- `ML/reports/pf_uplift_discovery/trade_enriched.csv`
- `ML/reports/entry_path_v1_quantile_selected_rule.json`
- `ML/benchmark_entry_path_v1_quantile_filter.py`
- `API/export_entry_path_v1_quantile_signals.py`
- `MT/MQL4/Include/lib_ML_Signal.mqh`

## Files To Create

- `ML/benchmark_quantile_ny_session.py` — validation-first benchmark for frozen quantile trades with `session != ny`
- `tests/test_benchmark_quantile_ny_session.py` — metrics, session tagging, gate, CLI, exporter-adjacent tests for benchmark helpers
- `ML/reports/quantile_ny_session/validation_summary.json`
- `ML/reports/quantile_ny_session/test_summary.json`
- `ML/reports/quantile_ny_session/per_seed_summary.csv`
- `ML/reports/quantile_ny_session/yearly_breakdown.csv`
- `ML/reports/quantile_ny_session/run_metadata.json`
- `docs/reports/2026-04-14-quantile-ny-session.md`

## Files To Modify After Python Gate Passes

- `API/export_entry_path_v1_quantile_signals.py` — optional `session` exclusion in production export path
- `tests/test_export_entry_path_v1_quantile_signals.py` — exporter coverage for session filter
- `CHANGELOG.md`
- `CONTEXT_HANDOFF.md`
- `docs/superpowers/roadmap.md`
- `wiki/research/execution-tracks.md`
- `wiki/index.md`
- `wiki/log.md`
- `wiki/REPO_integrity.md`

## Acceptance Rules

- Frozen quantile source only: no retraining, no rule search, no quantile retuning.
- Validation decides whether test is allowed.
- Session bucket definition must be explicit, deterministic, and checked on edge hours.
- `keep_sessions = {asia, london, overlap}` and `drop_session = ny`.
- Validation gate:
  - `N_trades >= 30`
  - `PF > 2.0`
  - `negative_year_slices = 0`
  - `holdout/session-filter PF >= baseline quantile PF`
  - no seed-level collapse `PF <= 1.0`
- MT4 parity and exporter change happen only after Python gate pass.

### Task 1: Session Tagging Helpers And Gate

**Files:**
- Create: `ML/benchmark_quantile_ny_session.py`
- Create: `tests/test_benchmark_quantile_ny_session.py`

- [ ] **Step 1.1: Write failing tests for session tagging and gate helpers**

```python
import pandas as pd

from ML.benchmark_quantile_ny_session import (
    assign_session_bucket,
    count_negative_year_slices,
    decide_session_gate,
)


def test_assign_session_bucket_maps_known_hours():
    assert assign_session_bucket(2) == "asia"
    assert assign_session_bucket(9) == "london"
    assert assign_session_bucket(15) == "overlap"
    assert assign_session_bucket(21) == "ny"


def test_count_negative_year_slices_ignores_tiny_years():
    frame = pd.DataFrame(
        [
            {"year": 2023, "pnl_atr": -1.0},
            {"year": 2023, "pnl_atr": 3.0},
            {"year": 2024, "pnl_atr": -2.0},
            {"year": 2024, "pnl_atr": -1.0},
            {"year": 2025, "pnl_atr": -1.0},
            {"year": 2025, "pnl_atr": 2.0},
            {"year": 2025, "pnl_atr": 2.0},
        ]
    )

    assert count_negative_year_slices(frame, pnl_column="pnl_atr") == 0


def test_decide_session_gate_rejects_support_and_seed_collapse():
    result = decide_session_gate(
        baseline_pf=8.0,
        filtered_pf=20.0,
        filtered_n_trades=29,
        filtered_negative_year_slices=0,
        seed_pf_values=[2.0, 3.0, 0.9],
    )

    assert result["verdict"] == "gate_fail"
    assert "filtered_n_trades=29 < 30" in result["reasons"]
    assert "seed_pf_values_contain_pf<=1.0: [0.9]" in result["reasons"]
```

- [ ] **Step 1.2: Run test to verify it fails**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_quantile_ny_session.py -q
```

Expected: `ModuleNotFoundError: No module named 'ML.benchmark_quantile_ny_session'`.

- [ ] **Step 1.3: Write minimal implementation for helpers**

```python
from __future__ import annotations

import math
from typing import Any

import pandas as pd


GATE_MIN_TRADES = 30
GATE_MIN_PF = 2.0
GATE_MIN_SEED_PF = 1.0


def assign_session_bucket(hour: int) -> str:
    hour = int(hour)
    if 0 <= hour <= 6:
        return "asia"
    if 7 <= hour <= 12:
        return "london"
    if 13 <= hour <= 18:
        return "overlap"
    return "ny"


def compute_pf(values: pd.Series) -> float | None:
    gains = float(values[values > 0].sum())
    losses = float(-values[values < 0].sum())
    if gains == 0.0 and losses == 0.0:
        return None
    if losses == 0.0:
        return math.inf
    return gains / losses


def count_negative_year_slices(frame: pd.DataFrame, pnl_column: str) -> int:
    count = 0
    for _, yearly in frame.groupby("year"):
        if len(yearly) < 3:
            continue
        pf = compute_pf(pd.to_numeric(yearly[pnl_column], errors="raise"))
        if pf is not None and pf < 1.0:
            count += 1
    return count


def decide_session_gate(
    *,
    baseline_pf: float | None,
    filtered_pf: float | None,
    filtered_n_trades: int,
    filtered_negative_year_slices: int,
    seed_pf_values: list[float],
) -> dict[str, Any]:
    reasons: list[str] = []
    if filtered_n_trades < GATE_MIN_TRADES:
        reasons.append(f"filtered_n_trades={filtered_n_trades} < {GATE_MIN_TRADES}")
    if filtered_pf is None or filtered_pf <= GATE_MIN_PF:
        reasons.append(f"filtered_pf={filtered_pf} <= {GATE_MIN_PF}")
    if baseline_pf is not None and filtered_pf is not None and filtered_pf < baseline_pf:
        reasons.append(f"filtered_pf={filtered_pf:.4f} < baseline_pf={baseline_pf:.4f}")
    if filtered_negative_year_slices > 0:
        reasons.append(
            f"filtered_negative_year_slices={filtered_negative_year_slices} > 0"
        )
    weak = [value for value in seed_pf_values if value <= GATE_MIN_SEED_PF]
    if weak:
        reasons.append(f"seed_pf_values_contain_pf<=1.0: {weak}")
    return {"verdict": "gate_pass" if not reasons else "gate_fail", "reasons": reasons}
```

- [ ] **Step 1.4: Run tests**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_quantile_ny_session.py -q
```

Expected: helper tests pass.

- [ ] **Step 1.5: Commit**

```bash
git add ML/benchmark_quantile_ny_session.py tests/test_benchmark_quantile_ny_session.py
git commit -m "quantile: add ny-session gate helpers"
```

### Task 2: Frozen Trade Selection And Split Evaluation

**Files:**
- Modify: `ML/benchmark_quantile_ny_session.py`
- Modify: `tests/test_benchmark_quantile_ny_session.py`

- [ ] **Step 2.1: Add failing tests for selecting quantile trades and filtering out NY rows**

```python
def test_select_quantile_trades_keeps_non_ny_sessions(tmp_path):
    ...
    selected = select_quantile_trades(
        frame=quantile_frame,
        baseline_frame=baseline_frame,
        selected_rule=rule_payload,
    )
    assert selected["session"].tolist() == ["asia", "overlap"]
    assert selected["time"].tolist() == ["2025.01.01 02:00", "2025.01.01 15:00"]
```

- [ ] **Step 2.2: Run targeted test and confirm failure**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_quantile_ny_session.py::test_select_quantile_trades_keeps_non_ny_sessions -q
```

Expected: missing `select_quantile_trades`.

- [ ] **Step 2.3: Implement selection and split evaluation**

```python
def select_quantile_trades(frame, baseline_frame, selected_rule):
    joined = attach_baseline_score(_parse_time(frame), _parse_time(baseline_frame))
    joined["baseline_selected"] = (
        (joined["signal"].to_numpy() != 0)
        & (joined["baseline_score"].to_numpy(dtype=float) >= float(selected_rule["baseline_threshold"]))
    )
    corrected = apply_conformal_correction(joined, float(selected_rule["winner"]["correction"]))
    mask = build_rule_mask(
        corrected,
        rule=selected_rule["winner"]["rule"],
        m=float(selected_rule["winner"]["m"]),
        w=float(selected_rule["winner"]["w"]),
    )
    selected = corrected.loc[mask].copy()
    selected["session"] = selected["time"].dt.hour.map(assign_session_bucket)
    selected["year"] = selected["time"].dt.year
    return selected
```

- [ ] **Step 2.4: Run full test file**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_quantile_ny_session.py -q
```

Expected: selection tests pass.

- [ ] **Step 2.5: Commit**

```bash
git add ML/benchmark_quantile_ny_session.py tests/test_benchmark_quantile_ny_session.py
git commit -m "quantile: select non-ny quantile trades"
```

### Task 3: CLI Benchmark And Multi-Seed Diagnostics

**Files:**
- Modify: `ML/benchmark_quantile_ny_session.py`
- Modify: `tests/test_benchmark_quantile_ny_session.py`

- [ ] **Step 3.1: Add failing CLI test**

```python
def test_cli_writes_validation_and_skips_test_when_gate_fails(tmp_path):
    ...
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ML.benchmark_quantile_ny_session",
            "--validation-predictions",
            str(validation_csv),
            "--test-predictions",
            str(test_csv),
            "--baseline-validation-predictions",
            str(baseline_validation_csv),
            "--baseline-test-predictions",
            str(baseline_test_csv),
            "--selected-rule",
            str(rule_json),
            "--output-dir",
            str(output_dir),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert (output_dir / "validation_summary.json").exists()
    assert (output_dir / "test_summary.json").exists()
```

- [ ] **Step 3.2: Implement CLI, artifact writers, and multi-seed summary**

```python
def run_benchmark(...):
    validation_selected = select_quantile_trades(...)
    validation_filtered = validation_selected.loc[validation_selected["session"] != "ny"].copy()
    validation_summary = evaluate_split(...)
    if validation_summary["gate"]["verdict"] != "gate_pass":
        test_summary = build_skipped_test_summary()
    else:
        test_selected = select_quantile_trades(...)
        test_filtered = test_selected.loc[test_selected["session"] != "ny"].copy()
        test_summary = evaluate_split(...)
    ...
```

- [ ] **Step 3.3: Run test suite**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_quantile_ny_session.py -q
```

Expected: benchmark suite passes.

- [ ] **Step 3.4: Run canonical benchmark**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m ML.benchmark_quantile_ny_session \
  --validation-predictions ML/reports/entry_path_v1_quantile_validation_predictions.csv \
  --test-predictions ML/reports/entry_path_v1_quantile_test_predictions.csv \
  --baseline-validation-predictions ML/reports/entry_path_v1_validation_predictions.csv \
  --baseline-test-predictions ML/reports/entry_path_test_predictions.csv \
  --selected-rule ML/reports/entry_path_v1_quantile_selected_rule.json \
  --output-dir ML/reports/quantile_ny_session \
  --root-dir /home/hohla/git/SoSimple/ML/reports/entry_path_v1_quantile_robustness \
  --seeds 7,17,42,77,123
```

Expected: artifact directory is populated.

- [ ] **Step 3.5: Commit**

```bash
git add ML/benchmark_quantile_ny_session.py tests/test_benchmark_quantile_ny_session.py
git add -f ML/reports/quantile_ny_session/per_seed_summary.csv ML/reports/quantile_ny_session/yearly_breakdown.csv
git add ML/reports/quantile_ny_session/validation_summary.json ML/reports/quantile_ny_session/test_summary.json ML/reports/quantile_ny_session/run_metadata.json
git commit -m "quantile: benchmark ny-session filter"
```

### Task 4: Exporter Integration After Gate Pass Only

**Files:**
- Modify: `API/export_entry_path_v1_quantile_signals.py`
- Modify: `tests/test_export_entry_path_v1_quantile_signals.py`

- [ ] **Step 4.1: Only if Task 3 validation verdict is `gate_pass`, add failing exporter test**

```python
def test_export_signals_excludes_ny_session_when_requested(tmp_path):
    ...
    out = pd.read_csv(output_path, sep=";")
    assert out["time"].tolist() == ["2025.01.01 02:00", "2025.01.01 15:00", "2025.01.01 21:00"]
    assert out["signal"].tolist() == [1, -1, 0]
```

- [ ] **Step 4.2: Implement exporter-side session filter without changing default behavior**

```python
def export_signals(..., excluded_sessions: set[str] | None = None):
    ...
    if excluded_sessions:
        selected_rows = raw_frame.copy()
        selected_rows["time"] = pd.to_datetime(selected_rows["time"], format="%Y.%m.%d %H:%M", errors="coerce")
        selected_rows["session"] = selected_rows["time"].dt.hour.map(assign_session_bucket)
        selected_mask = selected_mask & ~selected_rows["session"].isin(excluded_sessions)
```

- [ ] **Step 4.3: Run exporter tests**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_export_entry_path_v1_quantile_signals.py -q
```

Expected: exporter suite passes.

- [ ] **Step 4.4: Commit**

```bash
git add API/export_entry_path_v1_quantile_signals.py tests/test_export_entry_path_v1_quantile_signals.py
git commit -m "quantile: add optional ny-session export filter"
```

### Task 5: MT4 Parity, Report, And Project Sync

**Files:**
- Create: `docs/reports/2026-04-14-quantile-ny-session.md`
- Modify: `CHANGELOG.md`
- Modify: `CONTEXT_HANDOFF.md`
- Modify: `docs/superpowers/roadmap.md`
- Modify: `wiki/research/execution-tracks.md`
- Modify: `wiki/index.md`
- Modify: `wiki/log.md`
- Modify: `wiki/REPO_integrity.md`

- [ ] **Step 5.1: Only if Task 4 completed, export parity signals and run MT4 reconciliation workflow**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m API.export_entry_path_v1_quantile_signals \
  --seed-dir ML/reports/entry_path_v1_quantile_robustness/seed_007 \
  --split test \
  --output MT/tester/files/ml_signals.csv \
  --copy-to-mt4 \
  --rule-path ML/reports/entry_path_v1_quantile_selected_rule.json
```

Expected: parity input prepared; next MT4 tester run happens manually in existing project workflow.

- [ ] **Step 5.2: Write stage report and sync project docs**

Include in report:
- validation verdict
- whether test ran or was skipped
- multi-seed summary
- whether exporter integration happened
- whether MT4 parity ran or was intentionally skipped

- [ ] **Step 5.3: Run verification**

```bash
git diff --check
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_quantile_ny_session.py -q
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_export_entry_path_v1_quantile_signals.py -q
/home/hohla/git/SoSimple/.venv/bin/python wiki/wiki.py generate
/home/hohla/git/SoSimple/.venv/bin/python wiki/wiki.py verify
```

- [ ] **Step 5.4: Commit**

```bash
git add CHANGELOG.md CONTEXT_HANDOFF.md docs/superpowers/roadmap.md
git add docs/reports/2026-04-14-quantile-ny-session.md
git add wiki/index.md wiki/log.md wiki/research/execution-tracks.md wiki/REPO_integrity.md
git commit -m "docs: record quantile ny-session verdict"
```

## Done Criteria

- Benchmark exists and is covered by tests.
- Canonical validation verdict is recorded.
- Test is skipped if validation fails.
- Exporter behavior changes only if gate passes.
- Final report states clearly whether NY session filter is accepted, rejected, or still awaiting parity.
