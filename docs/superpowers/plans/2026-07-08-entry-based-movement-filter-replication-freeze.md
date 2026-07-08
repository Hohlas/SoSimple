# Entry-Based Movement Filter Replication / Freeze Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Проверить и, если gates пройдены, зафиксировать ровно один заранее выбранный movement-filter `simple_combined / extra_trees_small / H3 / top_fraction=0.05` как исследовательскую маску для следующего плана, без расширения поиска, без выбора направления, без PnL/PF и без открытия `locked_test`.

**Architecture:** Новый narrow runner читает результат `entry_based_movement_filter`, восстанавливает тот же score только для одного frozen rule, повторно проверяет rule contract, считает stability diagnostics на разрешённых validation/disclosure split-ах и пишет frozen-rule artifact. Runner не перебирает профили, модели, горизонты или thresholds; любое расхождение с frozen rule даёт contract failure. Это reproducibility/freeze check на уже использованных validation-периодах, а не независимая replication на новом времени.

**Tech Stack:** Python 3.10+, pandas, numpy, scipy, scikit-learn, существующие `ML/baseline/benchmark_entry_based_movement_filter.py` и `ML/baseline/benchmark_entry_based_amplitude_movement.py`, `./.venv/bin/python`, pytest.

## Global Constraints

- Work on the current branch; do not use git worktree.
- Use `./.venv/bin/python` for every Python command.
- This stage is `RESEARCH_ONLY` unless it produces `FROZEN_MOVEMENT_FILTER_FOR_NEXT_RESEARCH_PLAN`; it cannot produce a trading candidate.
- `freeze` here means a fixed research segmentation mask for the next plan, not a live-executable trading rule.
- `top_fraction=0.05` is a batch validation segmentation rule. It is not live-executable because it ranks rows inside a split; any future live plan must convert it into a fixed past-derived `score_cutoff` before trading interpretation.
- Do not open `locked_test`.
- Do not train or select a direction model.
- Do not compute PnL, PF, spread, stop-loss, take-profit, BUY/SELL metrics, drawdown, or side-specific gates in this plan.
- Do not derive direction from `entry_up - entry_dn`, `entry_log_ratio`, score asymmetry, selected rows, or realized side.
- Do not add new feature profiles, models, horizons, seeds, target families, threshold families, selected fractions, instruments, timeframes, entry rules, exit rules, or cost assumptions.
- Frozen rule is exactly:
  - `profile = simple_combined`;
  - `model_key = extra_trees_small`;
  - `horizon = 3`;
  - `target_family = entry_movement`;
  - `threshold_type = top_fraction`;
  - `selected_fraction = 0.05`;
  - `score_aggregation = median_across_rerun_seeds`.
- Frozen training/model contract is exactly:
  - `seeds = [42, 43, 44]`;
  - `profile_feature_set = simple_combined`;
  - `model_key = extra_trees_small`;
  - model hyperparameters must be read from the existing `benchmark_entry_based_amplitude_movement.py` registry and written into JSON as `model_config`;
  - dependency versions must be written into JSON as `dependency_versions`;
  - the complete frozen config must be hashed into `frozen_config_hash`.
- Source movement-filter artifact must be exactly `ML/reports/entry_based_movement_filter.json`.
- Source amplitude artifact must be exactly `ML/reports/entry_based_amplitude_movement.json`.
- Source artifact hash must match the `source_artifact_hash` recorded in `ML/reports/entry_based_movement_filter.json`.
- Canonical source-path guards from `benchmark_entry_based_movement_filter.py` must remain active.
- `val_select` is used only to verify the already frozen rule, not to choose a new rule.
- `val_eval` is check-only for the frozen rule.
- `low_n_disclosure=2026` remains disclosure-only and must not affect verdict.
- `locked_test = not_opened`.
- If frozen rule fails validation checks, verdict is `REJECT_MOVEMENT_FILTER_FREEZE`; do not pick a replacement.
- Output prefix: `entry_based_movement_filter_freeze`.
- The JSON must record `source_movement_filter_hash`, `source_amplitude_hash`, `frozen_rule`, `rule_hash`, `frozen_config`, `frozen_config_hash`, `selection_policy`, `locked_test`, `allowed_verdicts`, `validation_metrics`, `disclosure_metrics`, `contract_status`, `search_budget`, `score_cutoff_diagnostics`, and `random_baseline`.
- The report must explicitly state that the frozen movement filter is not direction, not PnL/PF, not a trading candidate, not a live rule, not independent replication, and not permission to open `locked_test`.

---

## Research Contract

**Hypothesis:** The single preselected movement-filter `simple_combined / extra_trees_small / H3 / top 5%` is stable enough on existing validation roles to become a frozen movement segmentation rule for a later plan.

**Task type:** reproducibility/freeze check of a signal filter on already used validation roles.

**Decision unit:** one entry-based dataset row / one signal.

**Allowed input:** only artifacts produced by the previous movement-filter stage and exact deterministic rerun of the same frozen rule.

**Forbidden interpretation:** A passing result says only that this no-direction movement filter is frozen as a research segmentation mask for the next research plan. It does not say trade profitability, BUY/SELL direction, exit quality, live executability, independent replication, or production readiness.

## Frozen Rule

The runner must build this exact rule object and refuse any artifact whose selected rule differs:

```json
{
  "profile": "simple_combined",
  "model_key": "extra_trees_small",
  "horizon": 3,
  "target_family": "entry_movement",
  "threshold_type": "top_fraction",
  "selected_fraction": 0.05,
  "score_aggregation": "median_across_rerun_seeds",
  "seeds": [42, 43, 44]
}
```

`rule_hash` is SHA-256 of this JSON serialized with `sort_keys=True` and compact separators.

`frozen_config_hash` is SHA-256 of a JSON object serialized with `sort_keys=True` and compact separators containing:

- `frozen_rule`;
- `model_config`;
- `profile_feature_contract`;
- `target_contract`;
- `split_contract`;
- `dependency_versions`.

## Metrics

Primary validation metrics:

- `selected_n`;
- `skipped_n`;
- `movement_lift`;
- `selected_p80`;
- `skipped_p80`;
- yearly `movement_lift`;
- `yearly_lift_pass_rate`;
- score Spearman with `entry_movement_3`.

Secondary diagnostics:

- selected fraction by validation year;
- score cutoff by split;
- score cutoff by validation year;
- random same-size baseline with fixed seed `20260708`, `n_repeats=1000`;
- yearly random same-size baseline with fixed seed `20260708`, `n_repeats=1000`;
- source artifact hash check;
- frozen rule hash check.

Forbidden metrics:

- PF, PnL, drawdown, win rate;
- BUY/SELL split;
- direction accuracy;
- spread/cost/stops/take-profit;
- any 2026 value for selection or freeze decision.

## Gate Policy

Allowed verdicts:

- `FROZEN_MOVEMENT_FILTER_FOR_NEXT_RESEARCH_PLAN`: frozen rule survives contract, `val_select`, `val_eval`, yearly and minimum-N checks; may be used only by the next no-direction segmentation plan.
- `RESEARCH_ONLY_REPLICATED`: frozen rule survives core checks but has warnings that prevent freeze.
- `REJECT_MOVEMENT_FILTER_FREEZE`: frozen rule fails gates; do not replace it.
- `ABORT_CONTRACT_FAIL`: source artifact, hash, split, rule, feature contract, source path, or leakage guard fails.

Forbidden verdicts:

- `CANDIDATE`;
- `TRADING_RULE_FOUND`;
- `DIRECTION_FOUND`;
- `READY_FOR_LOCKED_TEST`;
- `LOCKED_TEST_PASS`;
- `PRODUCTION_READY`.

Freeze gates:

```text
contract_status == PASS
frozen_rule_hash_match == true
locked_test == not_opened
val_select.selected_n >= 300
val_select.movement_lift >= 1.80
val_select.selected_p80 > val_select.skipped_p80
val_eval.selected_n >= 300
val_eval.movement_lift >= 1.50
val_eval.selected_p80 > val_eval.skipped_p80
val_eval.yearly_lift_pass_rate >= 0.80
all val_eval yearly selected_n >= 50
low_n_disclosure years == [2026]
```

Warnings that force `RESEARCH_ONLY_REPLICATED` instead of freeze:

```text
val_eval.spearman < 0.50
any val_eval yearly movement_lift < 1.25
random_same_size_p95 >= frozen_rule_movement_lift
any val_eval yearly random_same_size_p95 >= yearly frozen_rule_movement_lift
score_cutoff_diagnostics.status == WARNING
```

If any freeze gate fails, verdict is `REJECT_MOVEMENT_FILTER_FREEZE`.

## Artifacts

Create:

- `ML/baseline/benchmark_entry_based_movement_filter_freeze.py`
- `ML/reports/entry_based_movement_filter_freeze.json`
- `ML/reports/entry_based_movement_filter_freeze_yearly.csv`
- `ML/reports/entry_based_movement_filter_freeze_selected_rows.csv`
- `ML/reports/entry_based_movement_filter_freeze_scores.csv`
- `ML/reports/entry_based_movement_filter_freeze_random_baseline.csv`
- `ML/reports/entry_based_movement_filter_freeze_score_cutoffs.csv`
- `docs/reports/2026-07-08-entry-based-movement-filter-replication-freeze.md`
- `docs/ML/benchmark_entry_based_movement_filter_freeze.py.md`
- `tests/test_entry_based_movement_filter_freeze.py`

Modify:

- `CHANGELOG.md`
- `CONTEXT_HANDOFF.md`
- `MODULE_INDEX.md`
- `docs/tests/tests.md`
- `docs/superpowers/roadmap.md`
- `wiki/research/fractal-stop-research.md`
- `wiki/index.md`
- `wiki/log.md`
- `wiki/REPO_integrity.md`

## Task 1: Frozen Rule Contract

**Files:**
- Create: `ML/baseline/benchmark_entry_based_movement_filter_freeze.py`
- Create: `tests/test_entry_based_movement_filter_freeze.py`

**Interfaces:**
- Produces: `frozen_rule() -> dict[str, object]`
- Produces: `stable_rule_hash(rule: dict[str, object]) -> str`
- Produces: `frozen_config_hash(config: dict[str, object]) -> str`
- Produces: `validate_frozen_rule(source_artifact: dict) -> dict[str, object]`

- [ ] **Step 1: Write the failing tests**

```python
from ML.baseline.benchmark_entry_based_movement_filter_freeze import (
    frozen_rule,
    stable_rule_hash,
    validate_frozen_rule,
)


def test_frozen_rule_is_exactly_the_preselected_filter():
    assert frozen_rule() == {
        "profile": "simple_combined",
        "model_key": "extra_trees_small",
        "horizon": 3,
        "target_family": "entry_movement",
        "threshold_type": "top_fraction",
        "selected_fraction": 0.05,
        "score_aggregation": "median_across_rerun_seeds",
        "seeds": [42, 43, 44],
    }


def test_validate_frozen_rule_rejects_changed_threshold():
    artifact = {
        "selected_filter": {
            "profile": "simple_combined",
            "model_key": "extra_trees_small",
            "horizon": 3,
            "target_family": "entry_movement",
            "threshold_type": "top_fraction",
            "selected_fraction": 0.10,
            "score_aggregation": "median_across_rerun_seeds",
            "seeds": [42, 43, 44],
        },
        "locked_test": "not_opened",
    }

    verdict = validate_frozen_rule(artifact)

    assert verdict["status"] == "ABORT_CONTRACT_FAIL"
    assert "frozen_rule_mismatch" in verdict["reasons"]


def test_stable_rule_hash_is_order_independent():
    rule = frozen_rule()
    reversed_rule = dict(reversed(list(rule.items())))

    assert stable_rule_hash(rule) == stable_rule_hash(reversed_rule)


def test_validate_frozen_rule_rejects_changed_seed_contract():
    artifact = {
        "selected_filter": {
            "profile": "simple_combined",
            "model_key": "extra_trees_small",
            "horizon": 3,
            "target_family": "entry_movement",
            "threshold_type": "top_fraction",
            "selected_fraction": 0.05,
            "score_aggregation": "median_across_rerun_seeds",
            "seeds": [42, 43],
        },
        "locked_test": "not_opened",
    }

    verdict = validate_frozen_rule(artifact)

    assert verdict["status"] == "ABORT_CONTRACT_FAIL"
    assert "frozen_rule_mismatch" in verdict["reasons"]
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_movement_filter_freeze.py -q
```

Expected: FAIL because `ML.baseline.benchmark_entry_based_movement_filter_freeze` does not exist.

- [ ] **Step 3: Implement the contract helpers**

Implement:

```python
import hashlib
import json
from typing import Any


FROZEN_RULE = {
    "profile": "simple_combined",
    "model_key": "extra_trees_small",
    "horizon": 3,
    "target_family": "entry_movement",
    "threshold_type": "top_fraction",
    "selected_fraction": 0.05,
    "score_aggregation": "median_across_rerun_seeds",
    "seeds": [42, 43, 44],
}


def frozen_rule() -> dict[str, object]:
    return dict(FROZEN_RULE)


def stable_rule_hash(rule: dict[str, object]) -> str:
    payload = json.dumps(rule, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def frozen_config_hash(config: dict[str, object]) -> str:
    payload = json.dumps(config, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _rule_subset(row: dict[str, Any]) -> dict[str, object]:
    observed = {key: row.get(key) for key in FROZEN_RULE if key != "seeds"}
    observed["seeds"] = [42, 43, 44] if row.get("seed_count") == 3 else row.get("seeds")
    return observed


def validate_frozen_rule(source_artifact: dict) -> dict[str, object]:
    reasons: list[str] = []
    if source_artifact.get("locked_test") != "not_opened":
        reasons.append("locked_test")
    if _rule_subset(source_artifact.get("selected_filter") or {}) != FROZEN_RULE:
        reasons.append("frozen_rule_mismatch")
    return {
        "status": "ABORT_CONTRACT_FAIL" if reasons else "PASS",
        "reasons": reasons,
        "rule_hash": stable_rule_hash(FROZEN_RULE),
    }
```

- [ ] **Step 4: Run focused tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_movement_filter_freeze.py -q
```

Expected: PASS for Task 1 tests.

## Task 2: Source Artifact and Hash Guards

**Files:**
- Modify: `ML/baseline/benchmark_entry_based_movement_filter_freeze.py`
- Modify: `tests/test_entry_based_movement_filter_freeze.py`

**Interfaces:**
- Produces: `load_source_artifacts(movement_filter_path: Path, amplitude_path: Path) -> dict[str, object]`
- Produces: `sha256_file(path: Path) -> str`
- Produces: `validate_source_hashes(movement_filter_artifact: dict, amplitude_path: Path) -> dict[str, object]`

- [ ] **Step 1: Write the failing tests**

```python
import json
from pathlib import Path

from ML.baseline.benchmark_entry_based_movement_filter_freeze import (
    load_source_artifacts,
    sha256_file,
    validate_source_hashes,
)


def test_validate_source_hashes_rejects_amplitude_hash_mismatch(tmp_path: Path):
    amplitude = tmp_path / "entry_based_amplitude_movement.json"
    amplitude.write_text('{"changed": true}', encoding="utf-8")
    movement_artifact = {"source_artifact_hash": "not-the-real-hash"}

    verdict = validate_source_hashes(movement_artifact, amplitude)

    assert verdict["status"] == "ABORT_CONTRACT_FAIL"
    assert "source_amplitude_hash_mismatch" in verdict["reasons"]


def test_load_source_artifacts_reads_both_json_files(tmp_path: Path):
    movement = tmp_path / "entry_based_movement_filter.json"
    amplitude = tmp_path / "entry_based_amplitude_movement.json"
    movement.write_text(json.dumps({"selected_filter": {}}), encoding="utf-8")
    amplitude.write_text(json.dumps({"schema_version": 1}), encoding="utf-8")

    loaded = load_source_artifacts(movement, amplitude)

    assert loaded["movement_filter_artifact"]["selected_filter"] == {}
    assert loaded["amplitude_artifact"]["schema_version"] == 1
    assert loaded["movement_filter_path"] == str(movement)
    assert loaded["amplitude_path"] == str(amplitude)
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_movement_filter_freeze.py::test_validate_source_hashes_rejects_amplitude_hash_mismatch -q
```

Expected: FAIL because hash helpers are not implemented.

- [ ] **Step 3: Implement source artifact loading and hash validation**

Implementation requirements:

- read JSON using UTF-8;
- compute SHA-256 from raw file bytes;
- compare `movement_filter_artifact["source_artifact_hash"]` with `sha256_file(amplitude_path)`;
- return `{"status": "PASS", "reasons": [], "source_amplitude_hash": ...}` on success;
- return `ABORT_CONTRACT_FAIL` on mismatch.

- [ ] **Step 4: Run focused tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_movement_filter_freeze.py -q
```

Expected: PASS for Tasks 1-2.

## Task 3: Reuse Frozen Scoring Without Search

**Files:**
- Modify: `ML/baseline/benchmark_entry_based_movement_filter_freeze.py`
- Modify: `tests/test_entry_based_movement_filter_freeze.py`

**Interfaces:**
- Produces: `materialize_frozen_score_frames(movement_filter_artifact: dict) -> dict[str, object]`
- Produces: `evaluate_frozen_rule(frames: dict[str, pd.DataFrame]) -> dict[str, object]`
- Produces: `build_score_export(frames: dict[str, pd.DataFrame]) -> pd.DataFrame`
- Produces: `score_cutoff_diagnostics(frames: dict[str, pd.DataFrame]) -> dict[str, object]`

- [ ] **Step 1: Write the failing test**

```python
import pandas as pd

from ML.baseline.benchmark_entry_based_movement_filter_freeze import evaluate_frozen_rule
from ML.baseline.benchmark_entry_based_movement_filter_freeze import (
    build_score_export,
    score_cutoff_diagnostics,
)


def test_evaluate_frozen_rule_uses_fixed_top_five_percent():
    frame = pd.DataFrame(
        {
            "score": list(range(100, 0, -1)),
            "entry_movement_3": [10.0] * 5 + [2.0] * 95,
            "time": ["2024-01-01 00:00:00"] * 100,
        }
    )
    frames = {
        "val_select": frame.copy(),
        "val_eval": frame.copy(),
        "low_n_disclosure": pd.DataFrame(
            {
                "score": list(range(20, 0, -1)),
                "entry_movement_3": [10.0] + [2.0] * 19,
                "time": ["2026-01-01 00:00:00"] * 20,
            }
        ),
    }

    result = evaluate_frozen_rule(frames)

    assert result["val_select"]["selected_n"] == 5
    assert result["val_eval"]["selected_n"] == 5
    assert result["val_eval"]["movement_lift"] > 4.0
    assert result["low_n_disclosure_2026"]["years"] == [2026]


def test_build_score_export_contains_all_splits_and_selected_flag():
    frame = pd.DataFrame(
        {
            "score": list(range(100, 0, -1)),
            "entry_movement_3": [10.0] * 5 + [2.0] * 95,
            "time": ["2024-01-01 00:00:00"] * 100,
        }
    )
    frames = {
        "train": frame.copy(),
        "val_select": frame.copy(),
        "val_eval": frame.copy(),
        "low_n_disclosure": frame.copy(),
    }

    exported = build_score_export(frames)

    assert set(exported["split"]) == {"train", "val_select", "val_eval", "low_n_disclosure"}
    assert {"split", "time", "year", "score", "entry_movement_3", "selected"}.issubset(exported.columns)
    assert int(exported.loc[exported["split"] == "val_eval", "selected"].sum()) == 5


def test_score_cutoff_diagnostics_reports_split_and_year_cutoffs():
    frame = pd.DataFrame(
        {
            "score": list(range(100, 0, -1)),
            "entry_movement_3": [10.0] * 5 + [2.0] * 95,
            "time": ["2024-01-01 00:00:00"] * 50 + ["2025-01-01 00:00:00"] * 50,
        }
    )
    diagnostics = score_cutoff_diagnostics({"val_eval": frame})

    assert diagnostics["status"] in {"PASS", "WARNING"}
    assert diagnostics["by_split"][0]["split"] == "val_eval"
    assert {row["year"] for row in diagnostics["by_year"]} == {2024, 2025}
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_movement_filter_freeze.py::test_evaluate_frozen_rule_uses_fixed_top_five_percent -q
```

Expected: FAIL because `evaluate_frozen_rule` is not implemented.

- [ ] **Step 3: Implement frozen evaluation**

Implementation requirements:

- import and reuse `evaluate_top_fraction_filter`, `_yearly_filter_rows`, and `validate_low_n_disclosure_years` from `ML.baseline.benchmark_entry_based_movement_filter`;
- use `score_col = "score"`;
- use `target_col = "entry_movement_3"`;
- use `selected_fraction = 0.05`;
- compute `val_select`, `val_eval`, `low_n_disclosure_2026`, and yearly rows for `val_eval`;
- build `scores.csv` rows for `train`, `val_select`, `val_eval`, and `low_n_disclosure`;
- `scores.csv` must include `split`, `time`, `year`, `score`, `entry_movement_3`, `selected`;
- compute split/year score cutoff diagnostics, because `top_fraction=0.05` is not live-executable without a future fixed cutoff;
- never call `select_filter`;
- never enumerate candidates.

- [ ] **Step 4: Run focused tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_movement_filter_freeze.py -q
```

Expected: PASS for Tasks 1-3.

## Task 4: Gate and Verdict Logic

**Files:**
- Modify: `ML/baseline/benchmark_entry_based_movement_filter_freeze.py`
- Modify: `tests/test_entry_based_movement_filter_freeze.py`

**Interfaces:**
- Produces: `decide_freeze_verdict(contract: dict, metrics: dict) -> str`
- Produces: `freeze_gate_failures(metrics: dict) -> list[str]`

- [ ] **Step 1: Write the failing tests**

```python
from ML.baseline.benchmark_entry_based_movement_filter_freeze import decide_freeze_verdict


def passing_metrics():
    return {
        "val_select": {
            "selected_n": 333,
            "movement_lift": 2.15,
            "selected_p80": 17.5,
            "skipped_p80": 8.2,
        },
        "val_eval": {
            "selected_n": 333,
            "movement_lift": 2.48,
            "selected_p80": 35.6,
            "skipped_p80": 14.4,
            "spearman": 0.69,
            "yearly_lift_pass_rate": 1.0,
            "yearly": [
                {"year": 2023, "selected_n": 62, "movement_lift": 2.10},
                {"year": 2024, "selected_n": 137, "movement_lift": 1.88},
                {"year": 2025, "selected_n": 135, "movement_lift": 1.77},
            ],
        },
        "low_n_disclosure_2026": {"years": [2026]},
        "random_baseline": {
            "seed": 20260708,
            "n_repeats": 1000,
            "p95_movement_lift": 1.20,
            "yearly": [
                {"year": 2023, "p95_movement_lift": 1.12},
                {"year": 2024, "p95_movement_lift": 1.10},
                {"year": 2025, "p95_movement_lift": 1.09},
            ],
        },
        "score_cutoff_diagnostics": {"status": "PASS"},
    }


def test_decide_freeze_verdict_passes_only_frozen_rule_gates():
    verdict = decide_freeze_verdict({"status": "PASS", "reasons": []}, passing_metrics())

    assert verdict == "FROZEN_MOVEMENT_FILTER_FOR_NEXT_RESEARCH_PLAN"


def test_decide_freeze_verdict_rejects_weak_val_eval_without_replacement():
    metrics = passing_metrics()
    metrics["val_eval"]["movement_lift"] = 1.10

    verdict = decide_freeze_verdict({"status": "PASS", "reasons": []}, metrics)

    assert verdict == "REJECT_MOVEMENT_FILTER_FREEZE"


def test_decide_freeze_verdict_aborts_on_contract_failure():
    verdict = decide_freeze_verdict({"status": "ABORT_CONTRACT_FAIL", "reasons": ["hash"]}, passing_metrics())

    assert verdict == "ABORT_CONTRACT_FAIL"


def test_decide_freeze_verdict_ignores_2026_metric_values_for_freeze():
    metrics = passing_metrics()
    metrics["low_n_disclosure_2026"]["movement_lift"] = 0.01
    metrics["low_n_disclosure_2026"]["spearman"] = -0.50

    verdict = decide_freeze_verdict({"status": "PASS", "reasons": []}, metrics)

    assert verdict == "FROZEN_MOVEMENT_FILTER_FOR_NEXT_RESEARCH_PLAN"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_movement_filter_freeze.py::test_decide_freeze_verdict_passes_only_frozen_rule_gates -q
```

Expected: FAIL because verdict helpers are not implemented.

- [ ] **Step 3: Implement gates and verdict**

Implementation requirements:

- apply exactly the Freeze gates from `Gate Policy`;
- if contract fails, return `ABORT_CONTRACT_FAIL`;
- if any hard gate fails, return `REJECT_MOVEMENT_FILTER_FREEZE`;
- if hard gates pass but warning conditions trigger, return `RESEARCH_ONLY_REPLICATED`;
- otherwise return `FROZEN_MOVEMENT_FILTER_FOR_NEXT_RESEARCH_PLAN`;
- do not read any 2026 metric value except `low_n_disclosure_2026["years"]` for the disclosure-year contract;
- do not inspect or create alternative filters.

- [ ] **Step 4: Run focused tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_movement_filter_freeze.py -q
```

Expected: PASS for Tasks 1-4.

## Task 5: CLI, Artifacts and Real Run

**Files:**
- Modify: `ML/baseline/benchmark_entry_based_movement_filter_freeze.py`
- Modify: `tests/test_entry_based_movement_filter_freeze.py`
- Create: `ML/reports/entry_based_movement_filter_freeze.json`
- Create: `ML/reports/entry_based_movement_filter_freeze_yearly.csv`
- Create: `ML/reports/entry_based_movement_filter_freeze_selected_rows.csv`
- Create: `ML/reports/entry_based_movement_filter_freeze_scores.csv`
- Create: `ML/reports/entry_based_movement_filter_freeze_random_baseline.csv`
- Create: `ML/reports/entry_based_movement_filter_freeze_score_cutoffs.csv`

**Interfaces:**
- Produces CLI:

```bash
./.venv/bin/python ML/baseline/benchmark_entry_based_movement_filter_freeze.py \
  --movement-filter-source ML/reports/entry_based_movement_filter.json \
  --amplitude-source ML/reports/entry_based_amplitude_movement.json \
  --output-prefix ML/reports/entry_based_movement_filter_freeze
```

- [ ] **Step 1: Add CLI smoke test**

Add a fixture test that monkeypatches `materialize_frozen_score_frames()` and calls `main()` with fixture JSON artifacts.

Expected assertions:

```python
assert exit_code == 0
assert (tmp_path / "entry_based_movement_filter_freeze.json").exists()
assert (tmp_path / "entry_based_movement_filter_freeze_yearly.csv").exists()
assert (tmp_path / "entry_based_movement_filter_freeze_scores.csv").exists()
assert (tmp_path / "entry_based_movement_filter_freeze_score_cutoffs.csv").exists()
```

- [ ] **Step 2: Implement CLI**

CLI requirements:

- reject non-canonical source paths unless `--allow-noncanonical-source` is present for fixture tests;
- load both source artifacts;
- validate source hashes;
- validate frozen rule;
- materialize frozen score frames by reusing the movement-filter runner's bounded rerun path for the frozen selected filter only;
- compute frozen metrics;
- compute fixed-seed random same-size baseline with `seed=20260708` and `n_repeats=1000`;
- compute yearly fixed-seed random same-size baseline with `seed=20260708` and `n_repeats=1000`;
- compute score cutoff diagnostics by split and validation year;
- write full score export for `train`, `val_select`, `val_eval`, and `low_n_disclosure`;
- decide verdict;
- write JSON and CSV artifacts;
- record `locked_test: not_opened`.

- [ ] **Step 3: Run focused tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_movement_filter_freeze.py -q
```

Expected: all freeze tests pass.

- [ ] **Step 4: Run real CLI**

Run:

```bash
./.venv/bin/python ML/baseline/benchmark_entry_based_movement_filter_freeze.py --movement-filter-source ML/reports/entry_based_movement_filter.json --amplitude-source ML/reports/entry_based_amplitude_movement.json --output-prefix ML/reports/entry_based_movement_filter_freeze
```

Expected:

- command exits `0`;
- JSON verdict is one of allowed verdicts;
- artifacts exist;
- JSON contains `locked_test = not_opened`;
- `source_movement_filter_hash`, `source_amplitude_hash`, `frozen_rule`, `rule_hash`, `frozen_config_hash`, `score_cutoff_diagnostics`, and `random_baseline` are present.

## Task 6: Report, Docs, Wiki and Final Verification

**Files:**
- Create: `docs/reports/2026-07-08-entry-based-movement-filter-replication-freeze.md`
- Create: `docs/ML/benchmark_entry_based_movement_filter_freeze.py.md`
- Modify: `CHANGELOG.md`
- Modify: `CONTEXT_HANDOFF.md`
- Modify: `MODULE_INDEX.md`
- Modify: `docs/tests/tests.md`
- Modify: `docs/superpowers/roadmap.md`
- Modify: `wiki/research/fractal-stop-research.md`
- Modify: `wiki/index.md`
- Modify: `wiki/log.md`
- Modify: `wiki/REPO_integrity.md`

**Interfaces:**
- Produces final stage report and handoff for next agent.

- [ ] **Step 1: Write report**

Report must include:

- `Research Level`;
- `Multiple Testing Context`;
- `Validation Split Disclosure`;
- exact frozen rule and rule hash;
- frozen config hash and exact seeds/model/profile contract;
- source artifact hashes;
- gate table;
- random baseline table;
- score cutoff diagnostics by split and validation year;
- `top_fraction=0.05` limitation: batch segmentation, not live-executable fixed cutoff;
- verdict;
- explicit forbidden interpretations: no direction, no PnL/PF, no trading candidate, no live rule, no independent replication, no locked_test.

- [ ] **Step 2: Update module docs**

Create `docs/ML/benchmark_entry_based_movement_filter_freeze.py.md` with:

- purpose;
- inputs;
- outputs;
- frozen rule;
- frozen config hash;
- score export schema;
- source guards;
- allowed verdicts;
- launch command;
- limitations.

- [ ] **Step 3: Update stage reporting files**

Update:

- `CHANGELOG.md`;
- `CONTEXT_HANDOFF.md`;
- `MODULE_INDEX.md`;
- `docs/tests/tests.md`;
- `docs/superpowers/roadmap.md`.

Remove the completed replication/freeze item from nearest roadmap only if the stage verdict is final and a next unresolved direction is added.

- [ ] **Step 4: Wiki ingest**

Run:

```bash
./.venv/bin/python wiki/wiki.py status
./.venv/bin/python wiki/wiki.py generate
./.venv/bin/python wiki/wiki.py status
```

Expected final status:

```text
Wiki is up to date. No gaps found.
```

- [ ] **Step 5: Final verification**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_movement_filter_freeze.py -q
./.venv/bin/python -m pytest tests/ -q
git diff --check
```

Expected:

- focused freeze tests pass;
- full test suite passes;
- whitespace check is clean.

- [ ] **Step 6: Commit only related files**

Commit message:

```bash
git commit -m "Add entry-based movement filter freeze check"
```

Include only files related to this freeze stage. Do not include unrelated settings, package files, or incidental `graphify-out` churn unless the stage explicitly changed them.

## Self-Review

- Spec coverage: the plan freezes exactly one filter, forbids search expansion, keeps direction/PnL/PF out of scope, keeps 2026 disclosure-only, and preserves `locked_test = not_opened`.
- Placeholder scan: no banned placeholder patterns are used.
- Type consistency: helper names introduced in Tasks 1-4 are reused by Task 5.
- Risk note: this plan may produce only a frozen movement segmentation rule for a later plan; it cannot produce a trading candidate.
