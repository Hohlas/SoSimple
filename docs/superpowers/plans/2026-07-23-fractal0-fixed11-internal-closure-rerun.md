# Fractal0 Fixed-11 Internal Closure Rerun Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Довести внутренние проверки fixed normalized leaderboard до конца: producer-level stress-cost, frozen timezone/calendar diagnostics и bounded multi-seed rerun для ровно 11 fixed rule families без нового поиска и без открытия `locked_test`.

**Architecture:** Добавить ограниченный runner `ML/baseline/fractal0_fixed11_internal_closure_rerun.py`, который переиспользует producer-level entry/exit симулятор и normalized rich-entry feature/model pipeline. Существующий `benchmark_fractal0_entry_quality_filter.py` расширяется только параметрами, нужными для честного rerun: fixed manifest, фиксированные saved cutoffs, seed, spread и timezone shift. Runner пишет отдельные structured artifacts и classification, но не выбирает winner и не повышает статус выше `research_only`.

**Tech Stack:** Python через `./.venv/bin/python`, pandas, numpy, sklearn, pytest, существующие helpers из `ML/baseline/benchmark_fractal0_entry_quality_filter.py`, `ML/baseline/benchmark_fractal0_entry_exit_grid.py`, `ML/baseline/audit_leaderboard_robustness.py`, `ML/baseline/audit_leaderboard_closure.py`.

## Global Constraints

- Работать на текущей feature-ветке; worktree не создавать.
- Коммиты не делать без отдельной явной просьбы пользователя.
- Использовать только `./.venv/bin/python`.
- CSV читать с `sep=";"`; большие CSV читать через `usecols`, `nrows` или `chunksize`.
- `locked_test` не открывать; каждый JSON должен содержать `locked_test=not_opened` и `locked_test_status=not_opened`.
- Ровно 11 rule families брать из `ML.baseline.audit_leaderboard_robustness.LEADERBOARD_RULES`.
- Не добавлять profiles, models, targets, filters, cutoff, instruments или selection metrics.
- Не выбирать нового winner; `original_rank` сохранять как исторический порядок.
- Fixed execution contract: `S2_fractal0_buffer_0_5_entry_floor_2 / E3_open_pullback_1_0atr / M0_no_mask / X2_ml_opposite_any_p0_50 / canonical_spread=0.2 / entry_filter_score_col=rich_entry_score`.
- Stress-cost reruns intentionally change only `spread` within the predeclared stress grid. Because spread affects fill/no-fill and labels, stress rows are post-review internal diagnostics, not the same frozen rule for `locked_test`.
- Fixed cutoff policy: primary diagnostics use `score_cutoff_on_val_select` loaded from the `--source-rules-csv` artifact, not recomputed per seed/spread/timezone.
- Multi-seed primary diagnostic is `frozen_cutoff_seed_stress`: each seed reuses the saved seed-42 cutoff. Optional per-seed recalibrated cutoff may be reported only as `DIAGNOSTIC_ONLY` disclosure and must not affect the primary decision.
- Maximum verdict: `research_only`.
- Provider drift and transfer are out of scope: `provider_drift_status=NOT_IN_SCOPE`, `transfer_status=NOT_IN_SCOPE`.
- `stress_spreads = [0.2, 0.4, 0.8]`; `0.2` is canonical, `0.4` is 2x stress, `0.8` is 4x stress.
- `timezone_shift_hours = [0, -8, -4, 4, 8]`; `0` is canonical.
- `multiseed_seeds = [41, 42, 43, 44, 45]`.
- Primary run groups are not fully crossed: stress uses seed `42` and timezone `0`; timezone/calendar uses seed `42` and spread `0.2`; multi-seed uses spread `0.2` and timezone `0`.
- After Python changes run targeted tests and then `./.venv/bin/python -m pytest tests/ -q`.

---

## Roadmap Metadata

```text
depends_on:
  - docs/reports/2026-07-22-fractal0-rich-entry-quality-normalized-rerun.md
  - docs/reports/2026-07-23-time-only-robustness-audit.md
  - docs/reports/2026-07-23-fractal0-rich-entry-leaderboard-robustness-audit.md
  - docs/reports/2026-07-23-fractal0-leaderboard-cost-calendar-sequential-multiseed-closure.md
  - docs/superpowers/roadmap.md ACTIVE: Regime filter reformulation
blocks:
  - locked_test discussion
  - shortlist/freeze discussion
  - provider_drift plan
  - transfer plan
  - rich/fractal branch close decision
supersedes:
  - none; this is the producer/frozen rerun follow-up to the saved-artifact closure
exit_decisions:
  - internal_closure_complete_research_only_then_choose_next_probe
  - internal_closure_failed_close_rich_fractal_entry_quality_as_time_heavy_research_only
  - write_provider_drift_plan_after_internal_closure
  - write_transfer_plan_after_provider_drift
  - do_not_open_locked_test
locked_test_policy:
  - not_opened
```

## Methodology Map

- `docs/methodology/00-research-management.md`: fixed hypothesis, fixed unit of decision, predeclared search budget and maximum `research_only`.
- `docs/methodology/06-temporal-split.md`: `train_core` trains models/scalers, `val_select` supplies saved cutoff, `val_eval` is the only evaluation split, `locked_test` remains closed.
- `docs/methodology/08-model-development.md`: seed, runtime metadata, reproducible runner, heartbeat, resume, train-only scaler metadata.
- `docs/methodology/09-validation-freeze.md`: no new winner, no threshold/top-k tuning, fixed execution contract, no post-hoc elevation to candidate.
- `docs/methodology/11-robustness.md`: multi-seed, calendar/time checks, permutation sensitivity, side/calendar stability disclosures.
- `docs/methodology/12-backtest-costs.md`: producer-level spread stress, executable price convention, no zero-spread gate, no gross-only trading claim.
- `docs/methodology/16-reporting-audit.md`: structured artifacts, commands, hashes, split disclosure, report sections, report↔JSON consistency.
- `docs/methodology/A4-verdicts-stop-conditions.md`: stop conditions and allowed verdicts; result cannot become `candidate` in this stage.

## Fixed Input Rules

Single source of truth: `ML.baseline.audit_leaderboard_robustness.LEADERBOARD_RULES`.

| original_rank | profile_id | model_id | target_id | filter_id |
|---:|---|---|---|---|
| 1 | `time_only` | `linear` | `target_entry_ev_regression` | `top30` |
| 2 | `time_only` | `linear` | `target_entry_ev_regression` | `top40` |
| 3 | `time_only` | `linear` | `target_entry_ev_regression` | `top50` |
| 4 | `time_only` | `linear` | `target_entry_good_0_5r` | `top40` |
| 5 | `time_only` | `linear` | `target_entry_avoid_sl` | `top30` |
| 6 | `time_only` | `linear` | `target_entry_good_0_5r` | `top50` |
| 7 | `movement_plus_time` | `linear` | `target_entry_good_0_5r` | `top40` |
| 8 | `movement_plus_time` | `linear` | `target_entry_good_0_5r` | `top30` |
| 9 | `time_only` | `hist_gradient_boosting` | `target_entry_good_0_5r` | `top50` |
| 10 | `movement_plus_time` | `linear` | `target_entry_ev_regression` | `top50` |
| 11 | `movement_plus_time` | `linear` | `target_entry_good_0_5r` | `top50` |

## Decision Policy

The stage is successful as an internal closure only if all primary artifacts are produced with `status=COMPUTED`:

- stress-cost for all 11 rules and all 3 spreads;
- timezone rescore for all 11 rules and all 5 shifts;
- calendar permutation sensitivity for all 11 rules;
- no-ML calendar baseline for all 11 rules;
- multi-seed for all 11 rules and all 5 seeds.

Risk flags:

- `STRESS_COST_FAIL`: any rule has 2x or 4x spread `pf < 1.20`, `bs_p05 < 1.00`, or `n_trades < 300`; canonical 1x rows get separate `canonical_gate_flag` and anchor the comparison.
- `TIMEZONE_FRAGILE`: any non-zero timezone shift has `pf_drop_from_shift0_ratio > 0.30`, `pf < 1.20`, `bs_p05 < 1.00`, or `n_trades < 300`.
- `CALENDAR_DOMINATED`: calendar permutation causes `pf_drop_ratio > 0.30`, or no-ML calendar baseline reaches `baseline_to_ml_pf_ratio >= 0.80`.
- `MULTISEED_UNSTABLE`: fewer than 4 of 5 seeds pass `pf >= 1.20`, `bs_p05 >= 1.00`, and `n_trades >= 300` for a rule.
- `CONTRACT_FAIL`: fixed manifest, saved cutoffs, feature contract, split, scaler or `locked_test` guard fails.

Overall decisions:

- `FIXED11_INTERNAL_CLOSURE_COMPLETE_RESEARCH_ONLY`: all diagnostics computed and no blocking risk flags.
- `FIXED11_INTERNAL_CLOSURE_RISK_FLAGS_RESEARCH_ONLY`: all diagnostics computed, but at least one risk flag remains.
- `FIXED11_INTERNAL_CLOSURE_FAILED_RESEARCH_ONLY`: contract passed, but stress/multiseed/timezone evidence is weak enough to close the branch as time-heavy research-only.
- `UNKNOWN_INPUT_OR_CONTRACT`: inputs or fixed rule contract cannot be verified; CLI exits `1`.

---

### Task 1: Fixed Manifest And Run Matrix Contract

**Methodology:** `00-research-management.md`, `09-validation-freeze.md`, `16-reporting-audit.md`.

**Mandatory Checks:**
- Exactly 11 rules from `audit_leaderboard_robustness.LEADERBOARD_RULES`.
- Run matrix does not cross stress, timezone and multi-seed unnecessarily.
- Saved cutoffs are loaded from closure rules artifact.
- `locked_test=not_opened` is enforced before any run.

**Completion Criterion:** Unit tests prove the run matrix has 33 stress rows, 55 timezone rows and 55 multi-seed rows, with no provider/transfer rows.

**Files:**
- Create: `ML/baseline/fractal0_fixed11_internal_closure_rerun.py`
- Create: `tests/test_fractal0_fixed11_internal_closure_rerun.py`

**Interfaces:**
- Consumes: `audit_leaderboard_robustness.LEADERBOARD_RULES`, `audit_leaderboard_closure.input_artifacts_for_prefix`.
- Produces:
  - `CLOSURE_OUTPUT_PREFIX = Path("ML/reports/fractal0_fixed11_internal_closure_rerun")`
  - `RunSpec`
  - `fixed_rule_manifest_frame() -> pd.DataFrame`
  - `build_internal_run_matrix(smoke_first_rule_only: bool = False) -> pd.DataFrame`
  - `load_saved_cutoffs(path: Path) -> dict[str, float]`
  - `source_rules_metadata(path: Path) -> dict[str, str]`

- [ ] **Step 1: Write failing manifest tests**

Add to `tests/test_fractal0_fixed11_internal_closure_rerun.py`:

```python
from pathlib import Path

import pandas as pd

from ML.baseline import audit_leaderboard_robustness as leaderboard
from ML.baseline import fractal0_fixed11_internal_closure_rerun as rerun


def test_fixed_rule_manifest_reuses_exact_leaderboard_rules():
    manifest = rerun.fixed_rule_manifest_frame()

    assert len(manifest) == 11
    assert manifest["original_rank"].tolist() == list(range(1, 12))
    assert manifest["rule_id"].tolist() == [rule.rule_id for rule in leaderboard.LEADERBOARD_RULES]
    assert set(manifest["locked_test_policy"]) == {"not_opened"}


def test_internal_run_matrix_is_bounded_not_full_cross_product():
    matrix = rerun.build_internal_run_matrix()

    assert matrix["run_group"].value_counts().to_dict() == {
        "stress_cost": 33,
        "timezone_calendar": 55,
        "multiseed": 55,
    }
    assert set(matrix["provider_drift_status"]) == {"NOT_IN_SCOPE"}
    assert set(matrix["transfer_status"]) == {"NOT_IN_SCOPE"}
    assert matrix.loc[matrix["run_group"].eq("stress_cost"), "seed"].eq(42).all()
    assert matrix.loc[matrix["run_group"].eq("stress_cost"), "timezone_shift_hours"].eq(0).all()
    assert matrix.loc[matrix["run_group"].eq("timezone_calendar"), "seed"].eq(42).all()
    assert matrix.loc[matrix["run_group"].eq("timezone_calendar"), "spread"].eq(0.2).all()
    assert matrix.loc[matrix["run_group"].eq("multiseed"), "spread"].eq(0.2).all()
    assert matrix.loc[matrix["run_group"].eq("multiseed"), "timezone_shift_hours"].eq(0).all()


def test_smoke_run_matrix_keeps_one_rule_per_axis():
    matrix = rerun.build_internal_run_matrix(smoke_first_rule_only=True)

    assert matrix["run_group"].value_counts().to_dict() == {
        "stress_cost": 3,
        "timezone_calendar": 5,
        "multiseed": 5,
    }
    assert set(matrix["original_rank"]) == {1}


def test_load_saved_cutoffs_uses_rule_id_and_cutoff(tmp_path):
    path = tmp_path / "rules.csv"
    pd.DataFrame(
        {
            "rule_id": ["rank01_time_only_linear_target_entry_ev_regression_top30"],
            "score_cutoff_on_val_select": [-0.026718184259660646],
        }
    ).to_csv(path, sep=";", index=False)

    result = rerun.load_saved_cutoffs(path)

    assert result == {"rank01_time_only_linear_target_entry_ev_regression_top30": -0.026718184259660646}
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_fixed11_internal_closure_rerun.py::test_fixed_rule_manifest_reuses_exact_leaderboard_rules -q
```

Expected: FAIL because `fractal0_fixed11_internal_closure_rerun.py` does not exist.

- [ ] **Step 3: Implement manifest and run matrix**

Create `ML/baseline/fractal0_fixed11_internal_closure_rerun.py` with:

```python
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ML.baseline import audit_leaderboard_closure as closure
from ML.baseline import audit_leaderboard_robustness as leaderboard


CLOSURE_OUTPUT_PREFIX = Path("ML/reports/fractal0_fixed11_internal_closure_rerun")
SOURCE_INPUT_PREFIX = Path("ML/reports/fractal0_rich_entry_quality_normalized")
SOURCE_RULES_CSV = Path("ML/reports/leaderboard_closure_audit_rules.csv")
STRESS_SPREADS = (0.2, 0.4, 0.8)
TIMEZONE_SHIFT_HOURS = (0, -8, -4, 4, 8)
MULTISEED_SEEDS = (41, 42, 43, 44, 45)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True)
class RunSpec:
    run_group: str
    original_rank: int
    rule_id: str
    profile_id: str
    model_id: str
    target_id: str
    filter_id: str
    seed: int
    spread: float
    timezone_shift_hours: int


def fixed_rule_manifest_frame() -> pd.DataFrame:
    rows = []
    for rule in leaderboard.LEADERBOARD_RULES:
        rows.append(
            {
                "original_rank": int(rule.original_rank),
                "rule_id": rule.rule_id,
                "profile_id": rule.profile_id,
                "model_id": rule.model_id,
                "target_id": rule.target_id,
                "filter_id": rule.filter_id,
                "locked_test_policy": "not_opened",
            }
        )
    return pd.DataFrame(rows)


def _spec_rows(run_group: str, seed: int, spread: float, timezone_shift_hours: int) -> list[dict[str, object]]:
    rows = []
    for row in fixed_rule_manifest_frame().to_dict(orient="records"):
        rows.append(
            {
                **row,
                "run_group": run_group,
                "seed": int(seed),
                "spread": float(spread),
                "timezone_shift_hours": int(timezone_shift_hours),
                "provider_drift_status": "NOT_IN_SCOPE",
                "transfer_status": "NOT_IN_SCOPE",
            }
        )
    return rows


def build_internal_run_matrix(smoke_first_rule_only: bool = False) -> pd.DataFrame:
    rows = []
    for spread in STRESS_SPREADS:
        rows.extend(_spec_rows("stress_cost", seed=42, spread=spread, timezone_shift_hours=0))
    for shift in TIMEZONE_SHIFT_HOURS:
        rows.extend(_spec_rows("timezone_calendar", seed=42, spread=0.2, timezone_shift_hours=shift))
    for seed in MULTISEED_SEEDS:
        rows.extend(_spec_rows("multiseed", seed=seed, spread=0.2, timezone_shift_hours=0))
    matrix = pd.DataFrame(rows)
    if smoke_first_rule_only:
        matrix = matrix.loc[matrix["original_rank"].eq(1)].copy()
    return matrix.reset_index(drop=True)


def load_saved_cutoffs(path: Path = SOURCE_RULES_CSV) -> dict[str, float]:
    frame = pd.read_csv(path, sep=";", usecols=["rule_id", "score_cutoff_on_val_select"])
    if frame["rule_id"].duplicated().any():
        duplicates = frame.loc[frame["rule_id"].duplicated(), "rule_id"].astype(str).tolist()
        raise ValueError(f"duplicate saved cutoff rule_id values: {duplicates[:5]}")
    return {
        str(row["rule_id"]): float(row["score_cutoff_on_val_select"])
        for _, row in frame.iterrows()
    }


def source_rules_metadata(path: Path) -> dict[str, str]:
    return {
        "source_rules_csv": str(path),
        "source_rules_csv_sha256": _sha256_file(path),
    }
```

- [ ] **Step 4: Run manifest tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_fixed11_internal_closure_rerun.py -q
```

Expected: PASS for the first three tests.

---

### Task 2: Parameterize Existing Rich Runner For Fixed Reruns

**Methodology:** `08-model-development.md`, `09-validation-freeze.md`, `11-robustness.md`.

**Mandatory Checks:**
- Seed is no longer hardcoded to `42` inside rich-entry training.
- Fixed manifest mode creates exactly 11 jobs, not the full 243 ranked grid.
- Saved cutoff mode does not recalculate top fraction from current `val_select`.
- Timezone shift changes only time-derived features, not `signal_time`, `fill_time`, split rows or execution OHLC.
- Spread override is explicit, applied consistently to entry construction, label simulation, filtered trade simulation, summaries/trades/scores and recorded in artifact metadata.
- Every output row passes the fixed rule contract verifier before it can be treated as `COMPUTED`.

**Completion Criterion:** Unit tests verify seed plumbing, fixed job filtering, saved cutoff application, timezone feature shift, spread propagation and fixed output contract.

**Files:**
- Modify: `ML/baseline/benchmark_fractal0_entry_quality_filter.py`
- Modify: `tests/test_fractal0_entry_quality_filter.py`

**Interfaces:**
- Produces:
  - `build_fixed_leaderboard_job_list(profiles, models, targets, filters, rules) -> list[tuple[dict, dict, dict, dict, dict]]`
  - `load_fixed_cutoff_table(path: str | Path) -> dict[str, float]`
  - `resolve_fixed_cutoff(rule_id: str, fixed_cutoffs: dict[str, float] | None, selected_val: pd.DataFrame) -> float`
  - `verify_fixed_output_contract(rows: pd.DataFrame, *, expected_spread: float, expected_seed: int, timezone_shift_hours: int, fixed_cutoff_source: str) -> None`
  - `build_normalized_rich_feature_frame(..., timezone_shift_hours: int = 0)`
  - CLI args: `--rich-entry-seed`, `--fixed-leaderboard-rules-only`, `--fixed-cutoffs-csv`, `--spread`, `--timezone-shift-hours`, `--smoke-first-rule-only`

- [ ] **Step 1: Add failing tests for parameterization**

Append to `tests/test_fractal0_entry_quality_filter.py`:

```python
import argparse

import pandas as pd
import pytest

from ML.baseline import audit_leaderboard_robustness as leaderboard
from ML.baseline import benchmark_fractal0_entry_quality_filter as rich


def test_build_fixed_leaderboard_job_list_returns_exact_11_rules():
    jobs = rich.build_fixed_leaderboard_job_list(
        rich.rich_feature_profile_grid(),
        rich.rich_model_grid(include_diagnostic_models=True),
        rich.rich_target_grid(),
        rich.rich_filter_grid(),
        leaderboard.LEADERBOARD_RULES,
    )

    rule_ids = [job[4]["rule_id"] for job in jobs]
    assert len(jobs) == 11
    assert rule_ids == [rule.rule_id for rule in leaderboard.LEADERBOARD_RULES]


def test_resolve_fixed_cutoff_prefers_saved_cutoff():
    selected_val = pd.DataFrame({"rich_entry_score": [0.5, 0.4]})
    selected_val.attrs["score_cutoff_on_val_select"] = 0.4

    result = rich.resolve_fixed_cutoff("rank01", {"rank01": -0.0267}, selected_val)

    assert result == -0.0267


def test_verify_fixed_output_contract_rejects_wrong_spread():
    rows = pd.DataFrame(
        {
            "rule_id": ["rank01_time_only_linear_target_entry_ev_regression_top30"],
            "original_rank": [1],
            "profile_id": ["time_only"],
            "model_id": ["linear"],
            "target_id": ["target_entry_ev_regression"],
            "filter_id": ["top30"],
            "stop_policy_id": ["S2_fractal0_buffer_0_5_entry_floor_2"],
            "entry_id": ["E3_open_pullback_1_0atr"],
            "mask_id": ["M0_no_mask"],
            "exit_id": ["X2_ml_opposite_any_p0_50"],
            "entry_filter_score_col": ["rich_entry_score"],
            "score_cutoff_on_val_select": [-0.026718184259660646],
            "rich_entry_seed": [42],
            "timezone_shift_hours": [0],
            "spread": [0.2],
            "locked_test": ["not_opened"],
            "fixed_cutoff_source": ["tmp_rules.csv"],
        }
    )

    with pytest.raises(ValueError, match="spread"):
        rich.verify_fixed_output_contract(
            rows,
            expected_spread=0.4,
            expected_seed=42,
            timezone_shift_hours=0,
            fixed_cutoff_source="tmp_rules.csv",
        )


def test_normalized_time_features_shift_without_mutating_input_times():
    entries = pd.DataFrame(
        {
            "time": pd.to_datetime(["2021-01-04 22:00:00"]),
            "side": ["BUY"],
            "ATR": [10.0],
            "planned_entry_bid_equivalent": [100.0],
            "planned_protective_stop_price": [99.0],
            "planned_r_value": [1.0],
            "entry_bid_equivalent": [100.0],
            "fractal0_price": [99.5],
        }
    )

    base_frame, _ = rich.build_normalized_rich_feature_frame(entries, pd.DataFrame(), "time_only", timezone_shift_hours=0)
    shifted_frame, _ = rich.build_normalized_rich_feature_frame(entries, pd.DataFrame(), "time_only", timezone_shift_hours=4)

    assert float(base_frame["session_hour_unit"].iloc[0]) == 22.0 / 23.0
    assert float(shifted_frame["session_hour_unit"].iloc[0]) == 2.0 / 23.0
    assert entries["time"].iloc[0] == pd.Timestamp("2021-01-04 22:00:00")
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
./.venv/bin/python -m pytest \
  tests/test_fractal0_entry_quality_filter.py::test_build_fixed_leaderboard_job_list_returns_exact_11_rules \
  tests/test_fractal0_entry_quality_filter.py::test_resolve_fixed_cutoff_prefers_saved_cutoff \
  tests/test_fractal0_entry_quality_filter.py::test_verify_fixed_output_contract_rejects_wrong_spread \
  tests/test_fractal0_entry_quality_filter.py::test_normalized_time_features_shift_without_mutating_input_times -q
```

Expected: FAIL because helpers and timezone parameter are missing.

- [ ] **Step 3: Implement fixed job helpers and CLI args**

In `ML/baseline/benchmark_fractal0_entry_quality_filter.py`, add helpers near rich-grid helpers:

```python
def _by_id(items: list[dict[str, object]], key: str) -> dict[str, dict[str, object]]:
    return {str(item[key]): item for item in items}


def build_fixed_leaderboard_job_list(
    profiles: list[dict[str, object]],
    models: list[dict[str, object]],
    targets: list[dict[str, object]],
    filters: list[dict[str, object]],
    rules: tuple[object, ...],
) -> list[tuple[dict[str, object], dict[str, object], dict[str, object], dict[str, object], dict[str, object]]]:
    profiles_by_id = _by_id(profiles, "profile_id")
    models_by_id = _by_id(models, "model_id")
    targets_by_id = _by_id(targets, "target_id")
    filters_by_id = _by_id(filters, "filter_id")
    jobs = []
    for rule in rules:
        jobs.append(
            (
                dict(profiles_by_id[str(rule.profile_id)]),
                dict(models_by_id[str(rule.model_id)]),
                dict(targets_by_id[str(rule.target_id)]),
                dict(filters_by_id[str(rule.filter_id)]),
                {
                    "original_rank": int(rule.original_rank),
                    "rule_id": str(rule.rule_id),
                },
            )
        )
    return jobs


def load_fixed_cutoff_table(path: str | Path) -> dict[str, float]:
    frame = pd.read_csv(_path(str(path)), sep=";", usecols=["rule_id", "score_cutoff_on_val_select"])
    return {str(row["rule_id"]): float(row["score_cutoff_on_val_select"]) for _, row in frame.iterrows()}


def resolve_fixed_cutoff(rule_id: str, fixed_cutoffs: dict[str, float] | None, selected_val: pd.DataFrame) -> float:
    if fixed_cutoffs is not None:
        if rule_id not in fixed_cutoffs:
            raise ValueError(f"fixed cutoff missing for rule_id={rule_id}")
        return float(fixed_cutoffs[rule_id])
    cutoff = selected_val.attrs.get("score_cutoff_on_val_select")
    if cutoff is None:
        raise ValueError(f"score_cutoff_on_val_select missing for rule_id={rule_id}")
    return float(cutoff)
```

Update `parse_args()`:

```python
parser.add_argument("--rich-entry-seed", type=int, default=42)
parser.add_argument("--fixed-leaderboard-rules-only", action="store_true")
parser.add_argument("--fixed-cutoffs-csv", default="")
parser.add_argument("--spread", type=float, default=base.CONFIG.canonical_spread)
parser.add_argument("--timezone-shift-hours", type=int, default=0)
parser.add_argument("--smoke-first-rule-only", action="store_true")
```

- [ ] **Step 4: Implement timezone shift and fixed runner wiring**

Change `build_normalized_rich_feature_frame` signature:

```python
def build_normalized_rich_feature_frame(
    entries: pd.DataFrame,
    ohlc: pd.DataFrame,
    profile_id: str,
    timezone_shift_hours: int = 0,
) -> tuple[pd.DataFrame, list[dict[str, object]]]:
```

Inside the time feature block, use shifted timestamps for feature values only:

```python
times = pd.to_datetime(out["time"]) + pd.to_timedelta(int(timezone_shift_hours), unit="h")
```

In `run_rich_entry_quality(args)`:

- compute `active_spread` once near config/preflight setup:

```python
active_spread = float(getattr(args, "spread", base.CONFIG.canonical_spread))
```

- replace every `base.CONFIG.canonical_spread` used for rich entry construction/simulation with `active_spread`, specifically:
  - `run_base["spread"]`;
  - `base.build_entry_rows(...)`;
  - label simulation via `base._simulate_entries(...)`;
  - `_simulate_for_filter(...)`;
  - `_summary_for_filter(...)`;
  - `trades["spread"]`;
  - `summary["spread"]`;
  - score rows and JSON metadata.
- pass `timezone_shift_hours=int(args.timezone_shift_hours)` into `build_normalized_rich_feature_frame`;
- replace `seed=42` in `train_rich_entry_model(...)` with:

```python
seed=int(getattr(args, "rich_entry_seed", 42))
```

- if `args.fixed_leaderboard_rules_only` is true, import `audit_leaderboard_robustness` and build `job_list` with `build_fixed_leaderboard_job_list(...)`; otherwise preserve existing behavior;
- if `args.smoke_first_rule_only` is true, pass only the first fixed rule to `build_fixed_leaderboard_job_list(...)`;
- load fixed cutoffs when `args.fixed_cutoffs_csv` is non-empty;
- for each job, use `resolve_fixed_cutoff(rule_id, fixed_cutoffs, selected_val)` and apply it with `mode="eval"` to both `val_select` and `val_eval`;
- add `original_rank`, `rule_id`, `stop_policy_id`, `entry_id`, `mask_id`, `exit_id`, `rich_entry_seed`, `timezone_shift_hours`, `spread`, `locked_test`, and `fixed_cutoff_source` to summary, trades and scores rows;
- call `verify_fixed_output_contract(...)` for summary/trades/scores before writing artifacts; contract mismatch exits through structured `UNKNOWN_INPUT_OR_CONTRACT`;
- write those fields into the main JSON artifact.

Add targeted tests:

```python
def test_spread_override_is_consistent_in_fixed_rerun_smoke(tmp_path):
    prefix = tmp_path / "fixed_spread_smoke"
    args = argparse.Namespace(
        threads=1,
        no_resume=True,
        output_prefix=str(prefix),
        execution_ohlc_path="MT/MQL4/Files/XAUUSD_M5_OHLC.csv",
        stop_policy_id="",
        stop_grid_artifact="ML/reports/fractal0_entry_exit_grid_stop_policy.json",
        permutation_repeats=0,
        smoke_limit_filters=1,
        smoke_first_rule_only=True,
        rich_entry_quality=True,
        include_diagnostic_models=True,
        normalized_rich_features=True,
        rich_entry_seed=42,
        fixed_leaderboard_rules_only=True,
        fixed_cutoffs_csv="ML/reports/leaderboard_closure_audit_rules.csv",
        spread=0.4,
        timezone_shift_hours=0,
    )

    rich.run_rich_entry_quality(args)

    summary = pd.read_csv(prefix.with_name(prefix.name + "_summary.csv"), sep=";")
    trades = pd.read_csv(prefix.with_name(prefix.name + "_trades.csv"), sep=";")
    assert set(summary["spread"].dropna().astype(float)) == {0.4}
    assert set(trades["spread"].dropna().astype(float)) == {0.4}
```

- [ ] **Step 5: Run targeted tests**

Run:

```bash
./.venv/bin/python -m pytest \
  tests/test_fractal0_entry_quality_filter.py::test_build_fixed_leaderboard_job_list_returns_exact_11_rules \
  tests/test_fractal0_entry_quality_filter.py::test_resolve_fixed_cutoff_prefers_saved_cutoff \
  tests/test_fractal0_entry_quality_filter.py::test_verify_fixed_output_contract_rejects_wrong_spread \
  tests/test_fractal0_entry_quality_filter.py::test_spread_override_is_consistent_in_fixed_rerun_smoke \
  tests/test_fractal0_entry_quality_filter.py::test_normalized_time_features_shift_without_mutating_input_times -q
```

Expected: PASS.

---

### Task 3: Producer-Level Stress-Cost Rerun

**Methodology:** `12-backtest-costs.md`, `09-validation-freeze.md`, `16-reporting-audit.md`.

**Mandatory Checks:**
- Stress rows are computed by rebuilding producer-level entries and trades, not by editing saved realized `pnl_r`.
- Canonical `spread=0.2` run is present as the anchor.
- `spread=0.4` and `spread=0.8` are computed for all 11 rules.
- `entry_effective_price`, `fill_time`, `exit_time`, `close_reason`, `r_value`, `pnl_r`, `spread` are present in stress trades.
- JSON/report record `ohlc_price_convention`, `spread_definition`, `entry_price_rule`, `sl_trigger_rule`, `tp_rule` and `timeout_pnl_rule`.
- Synthetic simulator tests cover BUY/SELL outcomes under `spread=0.2`, `0.4` and `0.8`.
- Because spread affects fill/no-fill and labels, report must say this is internal stress evidence, not a frozen-rule candidate proof.

**Completion Criterion:** `ML/reports/fractal0_fixed11_internal_closure_rerun_stress_cost.csv` has 33 `COMPUTED` rows and no `NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS`.

**Files:**
- Modify: `ML/baseline/fractal0_fixed11_internal_closure_rerun.py`
- Modify: `tests/test_fractal0_fixed11_internal_closure_rerun.py`

**Interfaces:**
- Produces:
  - `run_rich_fixed_once(...) -> dict[str, object]`
  - `collect_stress_cost(prefix: Path, matrix: pd.DataFrame) -> pd.DataFrame`

- [ ] **Step 1: Add failing stress collection test**

Append:

```python
def test_collect_stress_cost_requires_computed_rows(tmp_path):
    run_prefix = tmp_path / "run"
    pd.DataFrame(
        {
            "run_group": ["stress_cost"],
            "original_rank": [1],
            "rule_id": ["rank01"],
            "spread": [0.4],
            "split": ["val_eval"],
            "n_trades": [400],
            "pf": [1.5],
            "bs_p05": [1.1],
            "max_drawdown_r": [5.0],
        }
    ).to_csv(run_prefix.with_name(run_prefix.name + "_summary.csv"), sep=";", index=False)

    result = rerun.collect_stress_cost(run_prefix, pd.DataFrame({"rule_id": ["rank01"]}))

    assert result["status"].tolist() == ["COMPUTED"]
    assert result["spread"].tolist() == [0.4]
    assert result["pf"].tolist() == [1.5]
    assert result["stress_2x_4x_flag"].tolist() == [False]
```

Add simulator convention tests around existing simulator helpers in `tests/test_fractal0_entry_exit_grid.py` or this module's targeted test file:

```python
def test_stress_spread_simulator_contract_buy_sell_synthetic_cases():
    cases = make_synthetic_spread_cases()
    for spread in (0.2, 0.4, 0.8):
        result = simulate_synthetic_spread_cases(cases, spread=spread)
        assert set(result["close_reason"]) == {"TP", "SL", "timeout"}
        assert result.loc[result["close_reason"].eq("TP"), "pnl_r"].gt(0).all()
        assert result.loc[result["close_reason"].eq("SL"), "pnl_r"].lt(0).all()
        assert result["spread"].astype(float).eq(spread).all()
```

`make_synthetic_spread_cases()` and `simulate_synthetic_spread_cases()` must be local test helpers with explicit BUY and SELL fixtures. The fixtures must include separate TP-only, SL-only, timeout and same-window TP+SL rows and assert the documented same-window convention.

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_fixed11_internal_closure_rerun.py::test_collect_stress_cost_requires_computed_rows -q
```

Expected: FAIL because `collect_stress_cost` is missing.

- [ ] **Step 3: Implement stress runner plumbing**

Add to `fractal0_fixed11_internal_closure_rerun.py`:

```python
from types import SimpleNamespace

from ML.baseline import benchmark_fractal0_entry_quality_filter as rich


def _run_prefix(output_prefix: Path, group: str, seed: int, spread: float, shift: int) -> Path:
    spread_tag = str(spread).replace(".", "p")
    return output_prefix.with_name(f"{output_prefix.name}_{group}_seed{seed}_spread{spread_tag}_tz{shift:+d}")


def run_rich_fixed_once(
    output_prefix: Path,
    seed: int,
    spread: float,
    timezone_shift_hours: int,
    fixed_cutoffs_csv: Path,
    threads: int,
    smoke_first_rule_only: bool = False,
) -> dict[str, object]:
    args = SimpleNamespace(
        threads=int(threads),
        no_resume=False,
        output_prefix=str(output_prefix),
        execution_ohlc_path="MT/MQL4/Files/XAUUSD_M5_OHLC.csv",
        stop_policy_id="",
        stop_grid_artifact="ML/reports/fractal0_entry_exit_grid_stop_policy.json",
        permutation_repeats=0,
        smoke_limit_filters=0,
        rich_entry_quality=True,
        include_diagnostic_models=True,
        normalized_rich_features=True,
        rich_entry_seed=int(seed),
        fixed_leaderboard_rules_only=True,
        fixed_cutoffs_csv=str(fixed_cutoffs_csv),
        spread=float(spread),
        timezone_shift_hours=int(timezone_shift_hours),
        smoke_first_rule_only=bool(smoke_first_rule_only),
    )
    return rich.run_rich_entry_quality(args)


def collect_stress_cost(run_prefix: Path, matrix: pd.DataFrame) -> pd.DataFrame:
    summary_path = run_prefix.with_name(run_prefix.name + "_summary.csv")
    summary = pd.read_csv(
        summary_path,
        sep=";",
        usecols=[
            "run_group",
            "original_rank",
            "rule_id",
            "spread",
            "split",
            "n_trades",
            "pf",
            "bs_p05",
            "max_drawdown_r",
        ],
    )
    frame = summary.loc[summary["split"].astype(str).eq("val_eval")].copy()
    frame["status"] = "COMPUTED"
    base_gate = (
        (pd.to_numeric(frame["n_trades"], errors="coerce") < 300)
        | (pd.to_numeric(frame["pf"], errors="coerce") < 1.20)
        | (pd.to_numeric(frame["bs_p05"], errors="coerce") < 1.00)
    )
    frame["canonical_gate_flag"] = frame["spread"].astype(float).eq(0.2) & base_gate
    frame["stress_2x_4x_flag"] = frame["spread"].astype(float).isin([0.4, 0.8]) & base_gate
    frame["risk_flag"] = frame["stress_2x_4x_flag"]
    return frame.sort_values(["original_rank", "spread"]).reset_index(drop=True)
```

- [ ] **Step 4: Add stress group to batch runner**

Add `run_internal_closure(args)` that:

- verifies source closure JSON has `locked_test=not_opened`;
- writes `build_internal_run_matrix(smoke_first_rule_only=args.smoke_first_rule_only)` to `<prefix>_run_matrix.csv`;
- loads cutoffs from `Path(args.source_rules_csv)`, not from the module constant;
- writes `source_rules_csv`, `source_rules_csv_sha256` and `fixed_cutoff_source` into JSON/CSV metadata;
- loops over unique stress run specs:

```python
source_rules_csv = Path(args.source_rules_csv)
for spread in STRESS_SPREADS:
    run_prefix = _run_prefix(output_prefix, "stress_cost", 42, spread, 0)
    run_rich_fixed_once(
        run_prefix,
        seed=42,
        spread=spread,
        timezone_shift_hours=0,
        fixed_cutoffs_csv=source_rules_csv,
        threads=args.threads,
        smoke_first_rule_only=bool(args.smoke_first_rule_only),
    )
```

- concatenates stress summaries into `<prefix>_stress_cost.csv`.

- [ ] **Step 5: Run stress smoke command**

Run a smoke-limited command first:

```bash
./.venv/bin/python ML/baseline/fractal0_fixed11_internal_closure_rerun.py \
  --output-prefix /tmp/fractal0_fixed11_internal_closure_smoke \
  --run-groups stress_cost \
  --smoke-first-rule-only \
  --threads 24
```

Expected: exit `0`, JSON says `stress_cost_status=COMPUTED_SMOKE`.

---

### Task 4: Frozen Timezone Rescore And Calendar Diagnostics

**Methodology:** `11-robustness.md`, `08-model-development.md`, `16-reporting-audit.md`.

**Mandatory Checks:**
- Timezone shift is a feature rescore, not a fake edit of saved `scores.csv`.
- Saved cutoffs remain fixed.
- Calendar permutation sensitivity preserves row count and uses deterministic seed.
- No-ML calendar baseline is disclosed as diagnostic baseline search with bounded family count, not a new winner.
- Canonical run persists enough per-rule model/feature state to recompute calendar diagnostics without reading or mutating saved `scores.csv`.
- Calendar bucket selection is done on `val_select` only, with predefined metrics and minimum-trade gates.

**Completion Criterion:** timezone, calendar permutation and no-ML calendar baseline CSVs have 55, 11 and 11 computed primary rows respectively.

**Files:**
- Modify: `ML/baseline/fractal0_fixed11_internal_closure_rerun.py`
- Modify: `tests/test_fractal0_fixed11_internal_closure_rerun.py`

**Interfaces:**
- Produces:
  - `collect_timezone_rescore(...) -> pd.DataFrame`
  - `calendar_feature_columns(profile_id: str) -> list[str]`
  - `calendar_permutation_sensitivity(...) -> pd.DataFrame`
  - `calendar_no_ml_baseline(...) -> pd.DataFrame`

- [ ] **Step 1: Add failing tests for calendar helpers**

Append:

```python
def test_calendar_feature_columns_are_profile_specific():
    assert rerun.calendar_feature_columns("time_only") == [
        "session_hour_unit",
        "weekday_unit",
        "hour_sin_unit",
        "hour_cos_unit",
        "weekday_sin_unit",
        "weekday_cos_unit",
    ]
    assert rerun.calendar_feature_columns("movement_plus_time") == [
        "session_hour_unit",
        "weekday_unit",
        "hour_sin_unit",
        "hour_cos_unit",
        "weekday_sin_unit",
        "weekday_cos_unit",
    ]


def test_timezone_risk_flag_uses_shift0_anchor():
    frame = pd.DataFrame(
        {
            "rule_id": ["rank01", "rank01"],
            "timezone_shift_hours": [0, 4],
            "pf": [4.0, 2.0],
            "n_trades": [500, 500],
            "bs_p05": [3.0, 1.5],
        }
    )

    result = rerun.add_timezone_risk_flags(frame)

    shifted = result.loc[result["timezone_shift_hours"].eq(4)].iloc[0]
    assert shifted["pf_drop_from_shift0_ratio"] == 0.5
    assert bool(shifted["risk_flag"]) is True
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
./.venv/bin/python -m pytest \
  tests/test_fractal0_fixed11_internal_closure_rerun.py::test_calendar_feature_columns_are_profile_specific \
  tests/test_fractal0_fixed11_internal_closure_rerun.py::test_timezone_risk_flag_uses_shift0_anchor -q
```

Expected: FAIL because helpers are missing.

- [ ] **Step 3: Implement timezone collection**

Add:

```python
def add_timezone_risk_flags(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    anchors = (
        out.loc[out["timezone_shift_hours"].eq(0), ["rule_id", "pf"]]
        .rename(columns={"pf": "pf_shift0"})
    )
    out = out.merge(anchors, on="rule_id", how="left")
    out["pf_drop_from_shift0_ratio"] = (
        (pd.to_numeric(out["pf_shift0"], errors="coerce") - pd.to_numeric(out["pf"], errors="coerce"))
        / pd.to_numeric(out["pf_shift0"], errors="coerce")
    ).clip(lower=0.0)
    out["risk_flag"] = (
        out["timezone_shift_hours"].ne(0)
        & (
            (out["pf_drop_from_shift0_ratio"] > 0.30)
            | (pd.to_numeric(out["pf"], errors="coerce") < 1.20)
            | (pd.to_numeric(out["bs_p05"], errors="coerce") < 1.00)
            | (pd.to_numeric(out["n_trades"], errors="coerce") < 300)
        )
    )
    return out
```

For each shift in `TIMEZONE_SHIFT_HOURS`, run:

```python
source_rules_csv = Path(args.source_rules_csv)
run_prefix = _run_prefix(output_prefix, "timezone_calendar", 42, 0.2, shift)
run_rich_fixed_once(
    run_prefix,
    seed=42,
    spread=0.2,
    timezone_shift_hours=shift,
    fixed_cutoffs_csv=source_rules_csv,
    threads=args.threads,
    smoke_first_rule_only=bool(args.smoke_first_rule_only),
)
```

Collect `val_eval` summary rows into `<prefix>_timezone_rescore.csv`.

- [ ] **Step 4: Implement calendar permutation sensitivity**

Implement as downstream PF sensitivity:

- use only canonical timezone run: seed `42`, spread `0.2`, shift `0`;
- for each rule, persist or recompute within the same function call the train-fitted model, train-fitted scaler, `val_select` feature frame, `val_eval` feature frame and selected entry rows needed for rescore;
- save canonical diagnostic state to `<prefix>_canonical_feature_state_manifest.csv` with `rule_id`, `split`, `profile_id`, `model_id`, `target_id`, `feature_frame_path`, `scaler_scope=train_core_only`, `model_seed`, and `status`;
- permute only `calendar_feature_columns(profile_id)` after scaling, using deterministic seed `1000 + original_rank + repeat_index`;
- preserve row count, index alignment, non-calendar feature values, split membership, `signal_time`, `fill_time` and execution OHLC;
- group permutation by `year` and `side` when both columns exist; if `year` is absent derive it from `time`; if a group has fewer than 5 rows, keep that group unchanged and record `small_group_skipped_count`;
- rescore with the same trained model, apply saved cutoff, simulate trades with unchanged execution OHLC and unchanged `active_spread=0.2`;
- write one row per rule with `status=COMPUTED`, `pf_original`, `pf_permuted_median`, `pf_drop_ratio`, `risk_flag`.

Add helper:

```python
def calendar_feature_columns(profile_id: str) -> list[str]:
    if profile_id not in {"time_only", "movement_plus_time"}:
        return []
    return [
        "session_hour_unit",
        "weekday_unit",
        "hour_sin_unit",
        "hour_cos_unit",
        "weekday_sin_unit",
        "weekday_cos_unit",
    ]
```

Use `permutation_repeats=50` by default. This check is in scope and must be computed. If the existing runner boundaries do not expose enough model/feature state, extend them minimally so the diagnostic can rescore the same fixed rule. Only input corruption or an unverifiable fixed-rule contract may produce `UNKNOWN_INPUT_OR_CONTRACT`.

- [ ] **Step 5: Implement no-ML calendar baseline**

Define a bounded diagnostic baseline:

- baseline families: `hour`, `weekday`, `hour_weekday`;
- build bucket values from unshifted canonical `time` only:
  - `hour`: integer hour;
  - `weekday`: integer weekday;
  - `hour_weekday`: `weekday` plus hour pair;
- select allowed calendar buckets on `val_select` only;
- for each family, evaluate all buckets with `n_trades_val_select >= 30`; eligible buckets must have `pf_val_select >= 1.20` and `bs_p05_val_select >= 1.00`;
- select the family by highest `bs_p05_val_select`, then higher `pf_val_select`, then larger `n_trades_val_select`; do not inspect `val_eval` during selection;
- apply the selected bucket rule to `val_eval`;
- do not use ML score;
- report `baseline_family_count=3`;
- report `baseline_to_ml_pf_ratio`;
- if `gross_loss == 0`, set PF through the existing project PF convention and record `pf_zero_loss_policy`;
- if no bucket passes minimum gates, write `status=COMPUTED`, `baseline_selection_status=NO_ELIGIBLE_BUCKETS`, `risk_flag=False`, and do not treat it as missing evidence;
- mark `risk_flag=True` if `baseline_to_ml_pf_ratio >= 0.80`.

Output: `<prefix>_calendar_no_ml_baselines.csv`.

- [ ] **Step 6: Run timezone/calendar smoke command**

Run:

```bash
./.venv/bin/python ML/baseline/fractal0_fixed11_internal_closure_rerun.py \
  --output-prefix /tmp/fractal0_fixed11_timezone_calendar_smoke \
  --run-groups timezone_calendar \
  --smoke-first-rule-only \
  --threads 24
```

Expected: exit `0`, JSON says `timezone_rescore_status=COMPUTED_SMOKE`.

---

### Task 5: Bounded Multi-Seed Rerun And Aggregation

**Methodology:** `08-model-development.md`, `11-robustness.md`, `09-validation-freeze.md`.

**Mandatory Checks:**
- Seeds are exactly `[41, 42, 43, 44, 45]`.
- Spread is canonical `0.2`.
- Timezone shift is `0`.
- Fixed saved cutoffs are used as the primary `frozen_cutoff_seed_stress`.
- Optional per-seed recalibrated cutoffs may be reported only as `DIAGNOSTIC_ONLY` disclosure and must not change primary classification.
- Per-seed rows include `seed`, `rule_id`, `pf`, `bs_p05`, `n_trades`, `status`.
- Aggregation does not select a winner; it only flags stability.

**Completion Criterion:** `ML/reports/fractal0_fixed11_internal_closure_rerun_multiseed.csv` has 55 `COMPUTED` rows and aggregate CSV has 11 rows.

**Files:**
- Modify: `ML/baseline/fractal0_fixed11_internal_closure_rerun.py`
- Modify: `tests/test_fractal0_fixed11_internal_closure_rerun.py`

**Interfaces:**
- Produces:
  - `collect_multiseed(...) -> pd.DataFrame`
  - `aggregate_multiseed(multiseed: pd.DataFrame) -> pd.DataFrame`

- [ ] **Step 1: Add failing aggregation test**

Append:

```python
def test_aggregate_multiseed_flags_unstable_rule():
    frame = pd.DataFrame(
        {
            "rule_id": ["rank01"] * 5,
            "seed": [41, 42, 43, 44, 45],
            "pf": [1.3, 1.4, 0.9, 1.5, 1.6],
            "bs_p05": [1.1, 1.2, 0.8, 1.1, 1.2],
            "n_trades": [400, 400, 400, 400, 400],
            "status": ["COMPUTED"] * 5,
        }
    )

    result = rerun.aggregate_multiseed(frame)

    row = result.iloc[0]
    assert row["computed_seed_count"] == 5
    assert row["passing_seed_count"] == 4
    assert bool(row["risk_flag"]) is False
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_fixed11_internal_closure_rerun.py::test_aggregate_multiseed_flags_unstable_rule -q
```

Expected: FAIL because `aggregate_multiseed` is missing.

- [ ] **Step 3: Implement multi-seed collector and aggregation**

Add:

```python
def aggregate_multiseed(multiseed: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for rule_id, group in multiseed.groupby("rule_id", sort=False):
        computed = group.loc[group["status"].astype(str).eq("COMPUTED")].copy()
        passing = computed.loc[
            pd.to_numeric(computed["pf"], errors="coerce").ge(1.20)
            & pd.to_numeric(computed["bs_p05"], errors="coerce").ge(1.00)
            & pd.to_numeric(computed["n_trades"], errors="coerce").ge(300)
        ]
        rows.append(
            {
                "rule_id": str(rule_id),
                "computed_seed_count": int(len(computed)),
                "passing_seed_count": int(len(passing)),
                "pf_min": float(pd.to_numeric(computed["pf"], errors="coerce").min()) if len(computed) else None,
                "pf_median": float(pd.to_numeric(computed["pf"], errors="coerce").median()) if len(computed) else None,
                "bs_p05_min": float(pd.to_numeric(computed["bs_p05"], errors="coerce").min()) if len(computed) else None,
                "risk_flag": bool(len(computed) != 5 or len(passing) < 4),
            }
        )
    return pd.DataFrame(rows)
```

For each seed in `MULTISEED_SEEDS`, run:

```python
source_rules_csv = Path(args.source_rules_csv)
run_prefix = _run_prefix(output_prefix, "multiseed", seed, 0.2, 0)
run_rich_fixed_once(
    run_prefix,
    seed=seed,
    spread=0.2,
    timezone_shift_hours=0,
    fixed_cutoffs_csv=source_rules_csv,
    threads=args.threads,
    smoke_first_rule_only=bool(args.smoke_first_rule_only),
)
```

Collect `val_eval` summary rows into `<prefix>_multiseed.csv` and aggregate into `<prefix>_multiseed_aggregate.csv`. If per-seed recalibrated cutoff disclosure is implemented, write it to a separate `<prefix>_multiseed_recalibrated_cutoff_diagnostic.csv` with `diagnostic_only=True`.

- [ ] **Step 4: Run multi-seed smoke command**

Run:

```bash
./.venv/bin/python ML/baseline/fractal0_fixed11_internal_closure_rerun.py \
  --output-prefix /tmp/fractal0_fixed11_multiseed_smoke \
  --run-groups multiseed \
  --smoke-first-rule-only \
  --threads 24
```

Expected: exit `0`, JSON says `multi_seed_status=COMPUTED_SMOKE`.

---

### Task 6: Classification, CLI, Resume And Structured Artifacts

**Methodology:** `00-research-management.md`, `08-model-development.md`, `16-reporting-audit.md`, `A4-verdicts-stop-conditions.md`.

**Mandatory Checks:**
- CLI supports `--run-groups stress_cost,timezone_calendar,multiseed`.
- CLI `--source-rules-csv` is the only source of saved cutoffs for child rich reruns.
- CLI `--smoke-first-rule-only` reduces the fixed universe to `original_rank=1` for smoke only; full mode remains exact 11 rules.
- Resume skips run prefixes whose JSON has `status=completed`.
- Unknown contract writes JSON and exits `1`.
- Classification is fail-closed if any expected diagnostic row is missing.
- Overall JSON contains input hashes, run matrix, statuses, risk flags and artifacts.

**Completion Criterion:** Full CLI writes all expected artifacts and exits `0` when all diagnostics are computed; exits `1` only on input/contract failure.

**Files:**
- Modify: `ML/baseline/fractal0_fixed11_internal_closure_rerun.py`
- Modify: `tests/test_fractal0_fixed11_internal_closure_rerun.py`

**Interfaces:**
- Produces:
  - `build_classification(...) -> pd.DataFrame`
  - `run_internal_closure(args: argparse.Namespace) -> dict[str, object]`
  - `parse_args(argv: list[str] | None = None) -> argparse.Namespace`
  - `main(argv: list[str] | None = None) -> int`

- [ ] **Step 1: Add failing classification test**

Append:

```python
def test_build_classification_is_fail_closed_on_missing_rows():
    manifest = pd.DataFrame({"rule_id": ["rank01", "rank02"], "original_rank": [1, 2]})
    stress = pd.DataFrame({"rule_id": ["rank01"], "status": ["COMPUTED"], "risk_flag": [False]})
    timezone = pd.DataFrame({"rule_id": ["rank01"], "status": ["COMPUTED"], "risk_flag": [False]})
    permutation = pd.DataFrame({"rule_id": ["rank01"], "status": ["COMPUTED"], "risk_flag": [False]})
    baseline = pd.DataFrame({"rule_id": ["rank01"], "status": ["COMPUTED"], "risk_flag": [False]})
    multiseed = pd.DataFrame({"rule_id": ["rank01"], "status": ["COMPUTED"], "risk_flag": [False]})

    result = rerun.build_classification(manifest, stress, timezone, permutation, baseline, multiseed)

    missing = result.loc[result["rule_id"].eq("rank02")].iloc[0]
    assert missing["decision"] == "INTERNAL_CLOSURE_INCOMPLETE"
    assert "missing_stress_cost" in missing["reasons"]


def test_source_rules_csv_argument_is_recorded_and_used(tmp_path):
    rules_csv = tmp_path / "rules.csv"
    pd.DataFrame(
        {
            "rule_id": ["rank01_time_only_linear_target_entry_ev_regression_top30"],
            "score_cutoff_on_val_select": [-0.123],
        }
    ).to_csv(rules_csv, sep=";", index=False)

    cutoffs = rerun.load_saved_cutoffs(rules_csv)
    metadata = rerun.source_rules_metadata(rules_csv)

    assert cutoffs["rank01_time_only_linear_target_entry_ev_regression_top30"] == -0.123
    assert metadata["source_rules_csv"] == str(rules_csv)
    assert metadata["source_rules_csv_sha256"]
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
./.venv/bin/python -m pytest \
  tests/test_fractal0_fixed11_internal_closure_rerun.py::test_build_classification_is_fail_closed_on_missing_rows \
  tests/test_fractal0_fixed11_internal_closure_rerun.py::test_source_rules_csv_argument_is_recorded_and_used -q
```

Expected: FAIL because `build_classification` and/or `source_rules_metadata` are missing.

- [ ] **Step 3: Implement classification**

Rules:

- if any artifact lacks a row for `rule_id`, decision `INTERNAL_CLOSURE_INCOMPLETE`;
- if any status is not `COMPUTED`, decision `INTERNAL_CLOSURE_INCOMPLETE`;
- if any risk flag true, decision `INTERNAL_CLOSURE_RISK_FLAGGED`;
- otherwise `INTERNAL_CLOSURE_COMPUTED_RESEARCH_ONLY`;
- always set `allowed_max_verdict=research_only`, `new_winner_selected=False`, `locked_test=not_opened`.

- [ ] **Step 4: Implement CLI**

CLI:

```bash
./.venv/bin/python ML/baseline/fractal0_fixed11_internal_closure_rerun.py \
  --source-prefix ML/reports/fractal0_rich_entry_quality_normalized \
  --source-rules-csv ML/reports/leaderboard_closure_audit_rules.csv \
  --output-prefix ML/reports/fractal0_fixed11_internal_closure_rerun \
  --run-groups stress_cost,timezone_calendar,multiseed \
  --threads 24
```

Implement parser options:

```python
parser.add_argument("--source-prefix", default=str(SOURCE_INPUT_PREFIX))
parser.add_argument("--source-rules-csv", default=str(SOURCE_RULES_CSV))
parser.add_argument("--output-prefix", default=str(CLOSURE_OUTPUT_PREFIX))
parser.add_argument("--run-groups", default="stress_cost,timezone_calendar,multiseed")
parser.add_argument("--threads", type=int, default=24)
parser.add_argument("--smoke-first-rule-only", action="store_true")
parser.add_argument("--no-resume", action="store_true")
```

`run_internal_closure(args)` must pass `Path(args.source_rules_csv)` to every `run_rich_fixed_once(...)` call and must write `source_rules_csv` plus `source_rules_csv_sha256` into the top-level JSON. Do not read `SOURCE_RULES_CSV` directly inside run loops.

Expected outputs:

- `ML/reports/fractal0_fixed11_internal_closure_rerun.json`
- `ML/reports/fractal0_fixed11_internal_closure_rerun_run_matrix.csv`
- `ML/reports/fractal0_fixed11_internal_closure_rerun_stress_cost.csv`
- `ML/reports/fractal0_fixed11_internal_closure_rerun_timezone_rescore.csv`
- `ML/reports/fractal0_fixed11_internal_closure_rerun_canonical_feature_state_manifest.csv`
- `ML/reports/fractal0_fixed11_internal_closure_rerun_calendar_permutation_importance.csv`
- `ML/reports/fractal0_fixed11_internal_closure_rerun_calendar_no_ml_baselines.csv`
- `ML/reports/fractal0_fixed11_internal_closure_rerun_multiseed.csv`
- `ML/reports/fractal0_fixed11_internal_closure_rerun_multiseed_aggregate.csv`
- `ML/reports/fractal0_fixed11_internal_closure_rerun_multiseed_recalibrated_cutoff_diagnostic.csv` if optional disclosure is implemented
- `ML/reports/fractal0_fixed11_internal_closure_rerun_classification.csv`

- [ ] **Step 5: Run full internal closure**

Run:

```bash
./.venv/bin/python ML/baseline/fractal0_fixed11_internal_closure_rerun.py \
  --source-prefix ML/reports/fractal0_rich_entry_quality_normalized \
  --source-rules-csv ML/reports/leaderboard_closure_audit_rules.csv \
  --output-prefix ML/reports/fractal0_fixed11_internal_closure_rerun \
  --run-groups stress_cost,timezone_calendar,multiseed \
  --threads 24
```

Expected: exit `0`, `status=completed`, `locked_test=not_opened`.

---

### Task 7: Tests, Module Docs And Final Report

**Methodology:** `16-reporting-audit.md`, project `stage-reporting` skill.

**Mandatory Checks:**
- Report has all sections required by `docs/reports/README.md` plus ML-specific sections from `docs/methodology/16-reporting-audit.md`.
- Research-first block includes current/cumulative search budget and forbidden interpretations.
- Report states why this is not a trading conclusion.
- Report states OHLC price convention, spread definition, entry price rule, SL trigger rule, TP rule and timeout PnL rule used by the stress-cost rerun.
- Key numbers are copied from JSON/CSV, not memory.
- `CHANGELOG.md`, `CONTEXT_HANDOFF.md`, `docs/superpowers/roadmap.md`, `MODULE_INDEX.md` and wiki agree on next step.

**Completion Criterion:** Documentation points to the new report and artifacts; roadmap still has exactly one `ACTIVE` track.

**Files:**
- Create: `docs/ML/fractal0_fixed11_internal_closure_rerun.py.md`
- Create: `docs/reports/2026-07-23-fractal0-fixed11-internal-closure-rerun.md`
- Modify: `CHANGELOG.md`
- Modify: `CONTEXT_HANDOFF.md`
- Modify: `docs/superpowers/roadmap.md`
- Modify: `MODULE_INDEX.md`
- Modify: `wiki/research/fractal-stop-research.md`
- Modify: `wiki/index.md`
- Modify: `wiki/log.md`
- Modify: `wiki/REPO_integrity.md`

- [ ] **Step 1: Run targeted tests**

Run:

```bash
./.venv/bin/python -m pytest \
  tests/test_fractal0_fixed11_internal_closure_rerun.py \
  tests/test_fractal0_entry_quality_filter.py -q
```

Expected: PASS.

- [ ] **Step 2: Run full test suite**

Run:

```bash
./.venv/bin/python -m pytest tests/ -q
```

Expected: PASS.

- [ ] **Step 3: Extract report numbers from artifacts**

Run:

```bash
./.venv/bin/python -c 'import json, pandas as pd; p="ML/reports/fractal0_fixed11_internal_closure_rerun"; data=json.loads(open(p+".json", encoding="utf-8").read()); cls=pd.read_csv(p+"_classification.csv", sep=";"); print("status:", data["status"]); print("overall_decision:", data["overall_decision"]); print("locked_test:", data["locked_test"]); print("stress:", data["stress_cost_status"]); print("timezone:", data["timezone_rescore_status"]); print("calendar_permutation:", data["calendar_permutation_importance_status"]); print("calendar_no_ml:", data["calendar_no_ml_baseline_status"]); print("multiseed:", data["multi_seed_status"]); print("decisions:", cls["decision"].value_counts().to_dict())'
```

Expected: concrete values printed from artifacts.

- [ ] **Step 4: Create module documentation**

Create `docs/ML/fractal0_fixed11_internal_closure_rerun.py.md` with:

```md
# fractal0_fixed11_internal_closure_rerun.py

## Назначение

Bounded internal closure rerun for the exact 11 normalized leaderboard rule families.
The module computes producer-level stress-cost, frozen timezone/calendar diagnostics
and bounded multi-seed diagnostics without opening `locked_test` and without winner
selection.

## Command

```bash
./.venv/bin/python ML/baseline/fractal0_fixed11_internal_closure_rerun.py \
  --source-prefix ML/reports/fractal0_rich_entry_quality_normalized \
  --source-rules-csv ML/reports/leaderboard_closure_audit_rules.csv \
  --output-prefix ML/reports/fractal0_fixed11_internal_closure_rerun \
  --run-groups stress_cost,timezone_calendar,multiseed \
  --threads 24
```

## Scope

- `locked_test=not_opened`
- `provider_drift_status=NOT_IN_SCOPE`
- `transfer_status=NOT_IN_SCOPE`
- `allowed_max_verdict=research_only`
- fixed 11 `LEADERBOARD_RULES`
- saved `score_cutoff_on_val_select` only

## Outputs

- `ML/reports/fractal0_fixed11_internal_closure_rerun.json`
- `ML/reports/fractal0_fixed11_internal_closure_rerun_run_matrix.csv`
- `ML/reports/fractal0_fixed11_internal_closure_rerun_stress_cost.csv`
- `ML/reports/fractal0_fixed11_internal_closure_rerun_timezone_rescore.csv`
- `ML/reports/fractal0_fixed11_internal_closure_rerun_canonical_feature_state_manifest.csv`
- `ML/reports/fractal0_fixed11_internal_closure_rerun_calendar_permutation_importance.csv`
- `ML/reports/fractal0_fixed11_internal_closure_rerun_calendar_no_ml_baselines.csv`
- `ML/reports/fractal0_fixed11_internal_closure_rerun_multiseed.csv`
- `ML/reports/fractal0_fixed11_internal_closure_rerun_multiseed_aggregate.csv`
- `ML/reports/fractal0_fixed11_internal_closure_rerun_multiseed_recalibrated_cutoff_diagnostic.csv` if optional disclosure is implemented
- `ML/reports/fractal0_fixed11_internal_closure_rerun_classification.csv`
```

- [ ] **Step 5: Create final report**

Create `docs/reports/2026-07-23-fractal0-fixed11-internal-closure-rerun.md` with required sections:

- Context
- Уровень этапа
- What Was Done
- Multiple Testing Context
- Changed Files
- Verification
- Results
- Conclusions
- Limitations / Open Questions
- Split Disclosure
- Next Step
- Related Materials

The report must include:

```text
lifecycle_status=research_only
origin_bias=normalized rich-entry validation leaderboard selected after broad search
research_priority=medium; close internal robustness blockers before any provider/transfer/locked-test discussion
current_search_budget=no new winner search; exact 11 fixed rule families; stress_spreads=3; timezone_shifts=5; multiseed_seeds=5; diagnostic calendar baseline families=3
cumulative_search_budget=inherited from normalized rich-entry search, 243 ranked configs plus diagnostic controls and this fixed internal closure rerun
next_probe_freeze=not created in this stage
allowed_max_verdict=research_only
locked_test=not_opened
provider_drift_status=NOT_IN_SCOPE
transfer_status=NOT_IN_SCOPE
forbidden_interpretations=candidate/tradable/live_ready/production/permission_to_open_locked_test/new_winner
not_trading_evidence_reason=validation artifact rerun on broad-search descendants; no locked_test, no provider drift, no transfer, no MT4 parity
```

- [ ] **Step 6: Stage sync**

Use `stage-reporting` before editing final sync docs.

Update:

- `CHANGELOG.md`
- `CONTEXT_HANDOFF.md`
- `docs/superpowers/roadmap.md`
- `MODULE_INDEX.md`
- `wiki/research/fractal-stop-research.md`
- `wiki/index.md`
- `wiki/log.md`
- `wiki/REPO_integrity.md`

Roadmap next step must be one of:

```text
write provider_drift plan only if internal closure has no blocking risk flags
write transfer plan only after provider_drift
close rich/fractal entry-quality branch as time-heavy research-only
write narrower regime-filter reformulation plan
```

Do not write permission to open `locked_test`.

---

## Final Verification

Run:

```bash
rg -n "fractal0_fixed11_internal_closure_rerun|fixed11-internal-closure-rerun|locked_test=not_opened|provider_drift_status=NOT_IN_SCOPE|transfer_status=NOT_IN_SCOPE" \
  docs/reports/2026-07-23-fractal0-fixed11-internal-closure-rerun.md \
  docs/ML/fractal0_fixed11_internal_closure_rerun.py.md \
  docs/superpowers/roadmap.md \
  CONTEXT_HANDOFF.md \
  CHANGELOG.md \
  MODULE_INDEX.md
./.venv/bin/python -m pytest tests/ -q
```

Expected: `rg` shows consistent paths/statuses; full tests pass.

## Self-Review Checklist

- Spec coverage: stress-cost, timezone rescore, calendar permutation, no-ML calendar baseline and multi-seed are implemented as computed diagnostics, not disclosures.
- Scope control: provider drift and transfer remain out of scope.
- No `locked_test`: every JSON/report path says `locked_test=not_opened`.
- No new winner: all outputs preserve `original_rank`; no ranking-based decision promotes a new row.
- Fixed cutoffs: primary diagnostics use saved `score_cutoff_on_val_select`; per-seed/top-fraction recalibration is not used for the primary decision.
- Type consistency: `rule_id`, `original_rank`, `seed`, `spread`, `timezone_shift_hours`, `run_group`, status strings and artifact paths match across code/tests/report.
- Reporting: report key numbers are extracted from JSON/CSV after the run.
