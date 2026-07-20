# Entry-Based Movement Filter Design Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Проверить, можно ли заранее зафиксированный простой movement-filter поверх `entry-based next open` устойчиво отделять режимы “ждать движение / не ждать движение”, не выбирая сторону сделки и не открывая `locked_test`.

**Architecture:** Новый bounded runner переиспользует артефакты `entry_based_amplitude_movement` и строит только фильтр допуска входа по заранее ограниченным score-семействам: `time_plus_atr` и `simple_combined`. Порог выбирается только на `val_select`, затем один замороженный фильтр проверяется на `val_eval`; `2026` остаётся disclosure-only.

**Tech Stack:** Python 3.10+, pandas, numpy, scipy, scikit-learn, существующий `ML/baseline/benchmark_entry_based_amplitude_movement.py`, `./.venv/bin/python`, pytest.

## Global Constraints

- Work on the current branch; do not use git worktree.
- Use `./.venv/bin/python` for every Python command.
- This stage is `RESEARCH_ONLY`; it can produce at most `frozen_movement_filter_for_replication`, not a trading candidate.
- Do not open `locked_test`.
- Do not train or select a direction model.
- Do not compute PnL, PF, spread, stop-loss, take-profit, or side-specific trading gates in this plan.
- Do not derive direction from `entry_up - entry_dn`, `entry_log_ratio`, score asymmetry, or future realized side.
- Do not use post-entry diagnostic profiles for selection.
- Use only selection-eligible pre-entry profiles from the previous amplitude audit.
- Primary allowed score families:
  - `time_plus_atr`;
  - `simple_combined`.
- `simple_combined` means the actual safe columns available in the previous audit: ATR + calendar + fractal density; do not silently add `distance_to_level_pre_entry_only` unless a safe decision price exists and is audited again.
- `distance_to_entry_open_post_entry_diagnostic_only` is forbidden for selection and reporting as a candidate.
- `decision_time` remains `pre_entry_decision`: the filter sees only the current row snapshot available at/after `signal_time` and before the actual next `entry_open` price is known.
- Entry/evaluation convention remains diagnostic `next open`; this plan does not assert executable profitability.
- Split policy:
  - `train <= 2020`;
  - `validation = 2021-2025`;
  - `val_select` selects score family, horizon and threshold;
  - `val_eval` evaluates the single selected filter without changes;
  - `2026 = low_n_disclosure`, selection-forbidden;
  - `locked_test = not_opened`.
- Winner selection must not use `val_eval`, `2026`, or `locked_test`.
- Output prefix: `entry_based_movement_filter`.
- The JSON must record `cumulative_search_budget` from the amplitude branch and the new filter search budget.
- Save all selected rule fields in JSON: `profile`, `model_key`, `horizon`, `target_family`, `threshold_type`, `threshold_value`, `selected_fraction`, `selection_split`, `feature_contract_verdict`, `source_artifact_hash`.
- The report must explicitly state that this is a movement/no-movement filter, not a direction signal.

---

## Research Contract

**Hypothesis:** A simple pre-entry movement score can define a stable no-direction filter that selects rows with materially higher realized `entry_movement_H` on `val_eval` than skipped rows.

**Task type:** signal filter.

**Decision unit:** one entry-based dataset row / one signal.

**Allowed input:** prediction scores from the previous amplitude runner for `time_plus_atr` and `simple_combined`, or an exact deterministic rerun of those same score families.

**Forbidden interpretation:** Even a passing filter does not mean trade profitability. It only says: “inside this subset, realized movement was higher.” Direction, exit and costs need a later plan.

## Candidate Filters

Use a deliberately small grid.

| Field | Values |
|---|---|
| `profile` | `time_plus_atr`, `simple_combined` |
| `model_key` | best completed selection-eligible model for that profile from the amplitude artifact |
| `horizon` | `H3`, `H6`, `H12`, `H24` |
| `target_family` | `entry_movement` only |
| `threshold_type` | `top_fraction` |
| `selected_fraction` | `0.05`, `0.10`, `0.20`, `0.30` |

Maximum planned filter search:

```text
2 profiles * 4 horizons * 4 selected_fraction values = 32 threshold candidates
```

If multiple `model_key` values are available for one profile/horizon, choose the model key before thresholding by the previous amplitude audit's seed-aggregate `val_select_spearman_median`, using only `val_select`. Do not add a new model search.

## Metrics

Primary metrics:

- `selected_n` and `skipped_n`;
- `selected_mean_movement`;
- `skipped_mean_movement`;
- `movement_lift = selected_mean_movement / skipped_mean_movement`;
- `selected_p50`, `selected_p80`, `selected_p90`;
- yearly `movement_lift` for every validation year with enough rows;
- seed-aggregate stability for selected score family.

Secondary diagnostics:

- Spearman between score and `entry_movement_H`;
- target distribution by split;
- selected fraction drift by year;
- comparison against random same-size filters using a fixed seed.

Forbidden metrics:

- PF, PnL, drawdown, win rate;
- BUY/SELL performance;
- any metric using realized direction for selection;
- any `2026` value for selection.

## Gate Policy

Allowed verdicts:

- `MOVEMENT_FILTER_REJECTED`: no simple filter survives gates.
- `SIMPLE_MOVEMENT_FILTER_RESEARCH_ONLY`: one simple filter survives `val_select` and `val_eval`; it may justify a later replication/freeze plan.
- `ABORT_CONTRACT_FAIL`: artifact, split, feature contract, source hash, or leakage audit fails.

Forbidden verdicts:

- `CANDIDATE`;
- `FROZEN`;
- `READY_FOR_LOCKED_TEST`;
- `DIRECTION_FOUND`;
- `TRADING_RULE_FOUND`.

Selection gate on `val_select`:

```text
selected_n >= 200
movement_lift >= 1.25
selected_p80 > skipped_p80
```

Survival gate on `val_eval` for the single selected filter:

```text
selected_n >= 100
movement_lift >= 1.15
selected_p80 > skipped_p80
yearly_lift_pass_rate >= 0.60
```

Tie-breaker, in order:

1. higher `val_select` movement_lift among filters passing all selection gates;
2. higher `selected_n`;
3. simpler profile: `time_plus_atr` before `simple_combined`;
4. shorter horizon: `H3`, then `H6`, then `H12`, then `H24`.

If the selected filter fails `val_eval`, do not pick the second-best filter after seeing `val_eval`. Verdict becomes `MOVEMENT_FILTER_REJECTED`.

## Artifacts

Create:

- `ML/baseline/benchmark_entry_based_movement_filter.py`
- `ML/reports/entry_based_movement_filter.json`
- `ML/reports/entry_based_movement_filter_candidates.csv`
- `ML/reports/entry_based_movement_filter_yearly.csv`
- `ML/reports/entry_based_movement_filter_selected_rows.csv`
- `docs/reports/2026-07-07-entry-based-movement-filter-design.md`
- `docs/ML/benchmark_entry_based_movement_filter.py.md`

Modify:

- `tests/test_entry_based_movement_filter.py`
- `CHANGELOG.md`
- `CONTEXT_HANDOFF.md`
- `MODULE_INDEX.md`
- `docs/tests/tests.md`
- `wiki/research/fractal-stop-research.md`
- `wiki/index.md`
- `wiki/log.md`

## Task 1: Contract and Source Artifact Loading

**Files:**
- Create: `ML/baseline/benchmark_entry_based_movement_filter.py`
- Test: `tests/test_entry_based_movement_filter.py`

**Interfaces:**
- Produces: `load_amplitude_artifact(path: Path) -> dict`
- Produces: `validate_source_artifact(artifact: dict) -> dict`

- [ ] **Step 1: Write failing tests**

```python
from pathlib import Path

import pytest

from ML.baseline.benchmark_entry_based_movement_filter import (
    load_amplitude_artifact,
    validate_source_artifact,
)


def test_validate_source_artifact_requires_not_opened_locked_test():
    artifact = {
        "selection_policy": {"locked_test": "opened"},
        "feature_audit_rows": [],
        "run_config_hash": "abc",
    }

    verdict = validate_source_artifact(artifact)

    assert verdict["status"] == "ABORT_CONTRACT_FAIL"
    assert "locked_test" in verdict["reasons"]


def test_validate_source_artifact_accepts_expected_source_contract():
    artifact = {
        "selection_policy": {"locked_test": "not_opened"},
        "run_config_hash": "abc",
        "feature_audit_rows": [
            {"profile": "time_plus_atr", "split": "train", "family": "metadata", "decision": "PASS"},
            {"profile": "time_plus_atr", "split": "val_select", "family": "metadata", "decision": "PASS"},
            {"profile": "time_plus_atr", "split": "val_eval", "family": "metadata", "decision": "PASS"},
            {"profile": "time_plus_atr", "split": "low_n_disclosure", "family": "metadata", "decision": "PASS"},
            {"profile": "simple_combined", "split": "train", "family": "metadata", "decision": "PASS"},
            {"profile": "simple_combined", "split": "val_select", "family": "metadata", "decision": "PASS"},
            {"profile": "simple_combined", "split": "val_eval", "family": "metadata", "decision": "PASS"},
            {"profile": "simple_combined", "split": "low_n_disclosure", "family": "metadata", "decision": "PASS"},
        ],
    }

    verdict = validate_source_artifact(artifact)

    assert verdict == {"status": "PASS", "reasons": []}
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_movement_filter.py::test_validate_source_artifact_requires_not_opened_locked_test -q
```

Expected: FAIL because `ML.baseline.benchmark_entry_based_movement_filter` does not exist.

- [ ] **Step 3: Implement source loading and contract validation**

Implement:

```python
def load_amplitude_artifact(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def validate_source_artifact(artifact: dict) -> dict:
    reasons: list[str] = []
    selection_policy = artifact.get("selection_policy", {})
    if selection_policy.get("locked_test") != "not_opened":
        reasons.append("locked_test")

    audit_rows = artifact.get("feature_audit_rows", [])
    for required in ("time_plus_atr", "simple_combined"):
        metadata_passes = {
            row.get("split")
            for row in audit_rows
            if row.get("profile") == required
            and row.get("family") == "metadata"
            and row.get("decision") == "PASS"
        }
        if metadata_passes != {"train", "val_select", "val_eval", "low_n_disclosure"}:
            reasons.append(f"feature_contract:{required}")

    if not artifact.get("run_config_hash"):
        reasons.append("run_config_hash")

    return {
        "status": "ABORT_CONTRACT_FAIL" if reasons else "PASS",
        "reasons": reasons,
    }
```

- [ ] **Step 4: Run focused tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_movement_filter.py -q
```

Expected: PASS for Task 1 tests.

## Task 2: Candidate Enumeration

**Files:**
- Modify: `ML/baseline/benchmark_entry_based_movement_filter.py`
- Modify: `tests/test_entry_based_movement_filter.py`

**Interfaces:**
- Produces: `enumerate_filter_candidates(artifact: dict) -> list[dict]`

- [ ] **Step 1: Write failing test**

```python
from ML.baseline.benchmark_entry_based_movement_filter import enumerate_filter_candidates


def test_enumerate_filter_candidates_is_bounded_to_simple_profiles():
    artifact = {
        "seed_aggregate": [
            {
                "profile": "time_plus_atr",
                "model_key": "extra_trees_small",
                "horizon": 3,
                "target_family": "entry_movement",
                "val_select_spearman_median": 0.50,
            },
            {
                "profile": "nearest_k80_sequence_flat",
                "model_key": "hist_gradient_boosting",
                "horizon": 3,
                "target_family": "entry_movement",
                "val_select_spearman_median": 0.80,
            },
        ]
    }

    candidates = enumerate_filter_candidates(artifact)

    assert {row["profile"] for row in candidates} == {"time_plus_atr"}
    assert {row["selected_fraction"] for row in candidates} == {0.05, 0.10, 0.20, 0.30}
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_movement_filter.py::test_enumerate_filter_candidates_is_bounded_to_simple_profiles -q
```

Expected: FAIL because `enumerate_filter_candidates` is not implemented.

- [ ] **Step 3: Implement bounded candidate enumeration**

Implement selection from `artifact["seed_aggregate"]`, keeping only:

```python
ALLOWED_PROFILES = ("time_plus_atr", "simple_combined")
ALLOWED_FRACTIONS = (0.05, 0.10, 0.20, 0.30)
ALLOWED_TARGET_FAMILY = "entry_movement"
```

For each `(profile, horizon)`, keep the row with highest `val_select_spearman_median`, then expand the four `selected_fraction` values.

- [ ] **Step 4: Run focused tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_movement_filter.py -q
```

Expected: PASS for Tasks 1-2.

## Task 3: Threshold Evaluation

**Files:**
- Modify: `ML/baseline/benchmark_entry_based_movement_filter.py`
- Modify: `tests/test_entry_based_movement_filter.py`

**Interfaces:**
- Produces: `evaluate_top_fraction_filter(frame: pd.DataFrame, score_col: str, target_col: str, selected_fraction: float) -> dict`

- [ ] **Step 1: Write failing test**

```python
import pandas as pd

from ML.baseline.benchmark_entry_based_movement_filter import evaluate_top_fraction_filter


def test_evaluate_top_fraction_filter_reports_lift_and_counts():
    frame = pd.DataFrame(
        {
            "score": [0.9, 0.8, 0.2, 0.1],
            "entry_movement_3": [10.0, 8.0, 2.0, 1.0],
        }
    )

    metrics = evaluate_top_fraction_filter(
        frame,
        score_col="score",
        target_col="entry_movement_3",
        selected_fraction=0.50,
    )

    assert metrics["selected_n"] == 2
    assert metrics["skipped_n"] == 2
    assert metrics["selected_mean_movement"] == 9.0
    assert metrics["skipped_mean_movement"] == 1.5
    assert metrics["movement_lift"] == 6.0
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_movement_filter.py::test_evaluate_top_fraction_filter_reports_lift_and_counts -q
```

Expected: FAIL because `evaluate_top_fraction_filter` is not implemented.

- [ ] **Step 3: Implement filter evaluation**

Implementation rules:

- sort by score descending;
- select `ceil(n * selected_fraction)` rows;
- compute selected/skipped counts, means, p50/p80/p90 and lift;
- return `movement_lift = None` when skipped mean is `0` or missing.

- [ ] **Step 4: Run focused tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_movement_filter.py -q
```

Expected: PASS for Tasks 1-3.

## Task 4: Selection and No-Replacement Eval Protocol

**Files:**
- Modify: `ML/baseline/benchmark_entry_based_movement_filter.py`
- Modify: `tests/test_entry_based_movement_filter.py`

**Interfaces:**
- Produces: `select_filter(candidates: list[dict]) -> dict | None`
- Produces: `decide_verdict(selected: dict | None, val_eval_metrics: dict | None, contract_status: dict) -> str`

- [ ] **Step 1: Write failing tests**

```python
from ML.baseline.benchmark_entry_based_movement_filter import decide_verdict, select_filter


def test_select_filter_uses_declared_tie_breaker():
    candidates = [
        {
            "profile": "simple_combined",
            "horizon": 12,
            "selected_fraction": 0.10,
            "selected_n": 250,
            "movement_lift": 1.30,
            "selected_p80": 9.0,
            "skipped_p80": 7.0,
        },
        {
            "profile": "time_plus_atr",
            "horizon": 12,
            "selected_fraction": 0.10,
            "selected_n": 250,
            "movement_lift": 1.30,
            "selected_p80": 9.0,
            "skipped_p80": 7.0,
        },
    ]

    selected = select_filter(candidates)

    assert selected["profile"] == "time_plus_atr"


def test_decide_verdict_rejects_when_selected_filter_fails_val_eval():
    selected = {"profile": "time_plus_atr"}
    val_eval_metrics = {
        "selected_n": 120,
        "movement_lift": 1.10,
        "selected_p80": 9.0,
        "skipped_p80": 7.0,
        "yearly_lift_pass_rate": 0.80,
    }

    verdict = decide_verdict(selected, val_eval_metrics, {"status": "PASS", "reasons": []})

    assert verdict == "MOVEMENT_FILTER_REJECTED"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_movement_filter.py::test_select_filter_uses_declared_tie_breaker tests/test_entry_based_movement_filter.py::test_decide_verdict_rejects_when_selected_filter_fails_val_eval -q
```

Expected: FAIL because selection and verdict functions are not implemented.

- [ ] **Step 3: Implement gates and verdict**

Implement the exact gates from `Gate Policy`. `select_filter()` sees only `val_select` candidate metrics. `decide_verdict()` must never replace the selected filter after seeing `val_eval`.

- [ ] **Step 4: Run focused tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_movement_filter.py -q
```

Expected: PASS for Tasks 1-4.

## Task 5: Runner, Artifacts and Report

**Files:**
- Modify: `ML/baseline/benchmark_entry_based_movement_filter.py`
- Create: `ML/reports/entry_based_movement_filter.json`
- Create: `ML/reports/entry_based_movement_filter_candidates.csv`
- Create: `ML/reports/entry_based_movement_filter_yearly.csv`
- Create: `ML/reports/entry_based_movement_filter_selected_rows.csv`
- Create: `docs/reports/2026-07-07-entry-based-movement-filter-design.md`

**Interfaces:**
- Produces CLI:

```bash
./.venv/bin/python ML/baseline/benchmark_entry_based_movement_filter.py \
  --source ML/reports/entry_based_amplitude_movement.json \
  --output-prefix ML/reports/entry_based_movement_filter
```

- [ ] **Step 1: Add CLI smoke test**

Add a small temporary-artifact test that runs `main()` with a fixture artifact and verifies JSON + candidate CSV are written.

- [ ] **Step 2: Implement CLI**

CLI requirements:

- refuse incompatible source artifact with `ABORT_CONTRACT_FAIL`;
- write candidate metrics for `val_select`;
- select one filter only on `val_select`;
- evaluate that filter on `val_eval`;
- write 2026 disclosure separately;
- write source artifact path and hash;
- write `locked_test: not_opened`.

- [ ] **Step 3: Generate real artifacts**

Run:

```bash
./.venv/bin/python ML/baseline/benchmark_entry_based_movement_filter.py --source ML/reports/entry_based_amplitude_movement.json --output-prefix ML/reports/entry_based_movement_filter
```

Expected: JSON and CSV artifacts exist, and the top-level verdict is one of the allowed verdicts.

- [ ] **Step 4: Write report**

Report must include:

- exact selected filter or rejection reason;
- candidate search budget;
- source amplitude artifact hash;
- `val_select` table;
- single selected filter on `val_eval`;
- yearly table;
- 2026 disclosure table;
- explicit statement: no direction, no PnL, no `locked_test`.

## Task 6: Documentation, Wiki and Final Verification

**Files:**
- Create: `docs/ML/benchmark_entry_based_movement_filter.py.md`
- Modify: `CHANGELOG.md`
- Modify: `CONTEXT_HANDOFF.md`
- Modify: `MODULE_INDEX.md`
- Modify: `docs/tests/tests.md`
- Modify: `wiki/research/fractal-stop-research.md`
- Modify: `wiki/index.md`
- Modify: `wiki/log.md`

**Interfaces:**
- Produces final stage handoff and documented artifact map.

- [ ] **Step 1: Update module docs**

Document CLI, inputs, outputs, verdicts, and forbidden interpretations.

- [ ] **Step 2: Update stage reporting files**

Use `stage-reporting` when closing the stage. Keep the report, `CHANGELOG.md`, `CONTEXT_HANDOFF.md`, docs and wiki synchronized.

- [ ] **Step 3: Run verification**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_movement_filter.py -q
./.venv/bin/python -m pytest tests/ -q
./.venv/bin/python wiki/wiki.py status
git diff --check
```

Expected:

- focused tests pass;
- full tests pass;
- wiki status has no gaps;
- whitespace check is clean.

- [ ] **Step 4: Commit only related files**

Commit message:

```bash
git commit -m "Add entry-based movement filter design"
```

Include only files related to this movement-filter stage. Do not include unrelated settings, package files, or incidental `graphify-out` churn unless the stage explicitly changed them.

## Self-Review

- Spec coverage: the plan covers the no-direction filter, simple baseline comparison, fixed threshold grid, `val_select` selection, `val_eval` survival, 2026 disclosure, and locked-test prohibition.
- Placeholder scan: no banned placeholder patterns are used.
- Type consistency: function names introduced in Tasks 1-4 are reused consistently by later tasks.
- Risk note: because the hypothesis comes from a previous diagnostic audit, a pass here remains `RESEARCH_ONLY`; it cannot become a candidate without a later replication or freeze plan.
