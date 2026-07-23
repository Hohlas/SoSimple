# Fractal0 Rich Entry Leaderboard Robustness Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Провести batch-аудит устойчивости строк из normalized rich-entry leaderboard без нового поиска, без переобучения и без открытия `locked_test`.

**Architecture:** Создать отдельный audit-скрипт, который читает saved normalized artifacts, берёт заранее зафиксированные 11 строк leaderboard из отчёта `2026-07-22-fractal0-rich-entry-quality-normalized-rerun.md`, пересчитывает одинаковый набор validation-slice diagnostics для каждой строки и классифицирует строки без выбора нового winner. Скрипт переиспользует helpers из `ML/baseline/audit_time_only_robustness.py`, сохраняет один JSON и набор CSV, а отчёт формулирует только research-only выводы.

**Tech Stack:** Python через `./.venv/bin/python`, pandas, numpy, pytest, существующие helpers из `ML/baseline/audit_time_only_robustness.py` и `ML/baseline/benchmark_fractal0_entry_exit_grid.py`; новых зависимостей не добавлять.

## Global Constraints

- Работать на текущей feature-ветке; worktree не создавать.
- Использовать только `./.venv/bin/python`.
- CSV читать с `sep=";"` и только через `usecols` / `chunksize` / `nrows`; не загружать большие CSV без нужных колонок.
- `locked_test` не открывать. Успешные artifacts должны явно содержать `locked_test=not_opened` и `locked_test_status=not_opened`; `UNKNOWN` artifacts должны содержать `locked_test_status`, `source_locked_test` и не утверждать `locked_test=not_opened`, если входной contract это не подтвердил.
- Не запускать новый search: не добавлять profiles, targets, models, filters, cutoff, seed, instruments или model families.
- Не обучать и не переобучать модели.
- Не выбирать нового winner по результатам этого audit.
- Не считать строки из `Diagnostic best by profile` eligible для выбора; этот план покрывает только 11 строк `Candidate Shortlist / Leaderboard` и использует строку `time_only / linear / target_entry_ev_regression / top30` как anchor/control.
- Источник правил: `docs/reports/2026-07-22-fractal0-rich-entry-quality-normalized-rerun.md`, секция `Candidate Shortlist / Leaderboard`, строки 1-11.
- Машинный источник метрик и cutoff: `ML/reports/fractal0_rich_entry_quality_normalized_summary.csv`, `ML/reports/fractal0_rich_entry_quality_normalized_trades.csv`, `ML/reports/fractal0_rich_entry_quality_normalized_scores.csv`, `ML/reports/fractal0_rich_entry_quality_normalized.json`.
- Fixed execution contract для всех строк: `S2_fractal0_buffer_0_5_entry_floor_2 / E3_open_pullback_1_0atr / M0_no_mask / X2_ml_opposite_any_p0_50 / spread=0.2 / entry_filter_score_col=rich_entry_score`.
- `score_cutoff_on_val_select` для каждой строки берётся из exact `val_select` summary row; это восстановление сохранённого правила, не новый подбор cutoff.
- Maximum verdict: `research_only`.
- Запрещённые интерпретации: `candidate`, `tradable`, `live_ready`, `production`, `permission_to_open_locked_test`, `new_winner`.
- Scope: `validation_artifact_leaderboard_robustness_slice`.
- `multi_seed_status=NOT_RUN`, `provider_drift_status=NOT_RUN`, `transfer_status=NOT_RUN`, `locked_test_status=not_opened`, `stress_costs_status=NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS`, `timezone_shift_status=NOT_RUN`, `calendar_permutation_importance_status=NOT_RUN`, `sequential_position_constraint_status=NOT_RUN`.
- Если normalized artifact имеет `locked_test != not_opened` или `feature_contract_variant != normalized_atr_unit`, audit должен записать JSON со статусом `UNKNOWN`, decision `UNKNOWN_ARTIFACT_CONTRACT` и завершить CLI с кодом `1`.
- Если любая из 11 fixed audit input rows отсутствует в saved summary, audit должен записать JSON со статусом `UNKNOWN`, decision `UNKNOWN_LEADERBOARD_CONTRACT` и завершить CLI с кодом `1`.
- Если отсутствует входной JSON/CSV, audit должен записать JSON со статусом `UNKNOWN`, decision `UNKNOWN_INPUT_ARTIFACTS` и завершить CLI с кодом `1`.
- Если входной JSON/CSV имеет несовместимую схему, audit должен записать JSON со статусом `UNKNOWN`, decision `UNKNOWN_INPUT_SCHEMA` и завершить CLI с кодом `1`.
- После Python-изменений запускать `./.venv/bin/python -m pytest tests/ -q`.
- Для финальной синхронизации report / `CHANGELOG.md` / `CONTEXT_HANDOFF.md` / wiki использовать skill `stage-reporting`.

## Methodology Map

- `docs/methodology/00-research-management.md`: уровень исследования, frozen scope, allowed verdict, search budget и запрет на post-hoc повышение до candidate.
- `docs/methodology/06-temporal-split.md`: split-роли `train_core`, `val_select`, `val_eval`, `locked_test`; sample-size gate после фильтров.
- `docs/methodology/09-validation-freeze.md`: сохранённые правила, execution contract, cutoff, множественный поиск и недопустимость выбора нового winner.
- `docs/methodology/11-robustness.md`: yearly/quarterly/side/year-side, block bootstrap, score/cutoff/top-k sensitivity, calendar/time diagnostics, missing multi-seed/provider/transfer disclosure.
- `docs/methodology/12-backtest-costs.md`: spread/cost stress и sequential position simulation; если не пересчитывается из saved artifacts, статус должен быть `NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS` / `NOT_RUN`.
- `docs/methodology/16-reporting-audit.md`: structured artifact, report sections, commands, paths, hashes, split disclosure, limitations, запрещённые интерпретации.
- `docs/methodology/A4-verdicts-stop-conditions.md`: максимальный verdict `research_only`, stop conditions и запрет превращать поисковый результат в candidate.

## Fixed Audit Input Rows

Эти 11 строк являются зафиксированным входом audit, но не являются `frozen_rule_for_locked_test`. Порядок сохраняется как `original_rank`; сортировать по новым метрикам запрещено.

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

## Known Unknowns

- True stress-cost resimulation is not known to be computable from saved filtered trades alone. This plan records `stress_costs_status=NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS` unless the implementer proves resimulation can be done from existing producer artifacts without changing selection.
- True timezone-shift rescore is not known to be computable from saved scores alone because model scores were produced with original time features. This plan records `timezone_shift_status=NOT_RUN` unless a separate frozen rescore path is implemented without retraining and without new selection.
- Calendar permutation importance is not known to be computable because fitted per-profile estimators are not persisted. This plan records `calendar_permutation_importance_status=NOT_RUN` unless a model-level artifact exists and is verified.

---

## File Structure

- Create: `ML/baseline/audit_leaderboard_robustness.py`
  - Reads normalized rich-entry JSON/CSV artifacts.
  - Verifies global normalized contract and exact 11-rule leaderboard contract.
  - Recomputes per-rule validation-slice diagnostics.
  - Writes `ML/reports/leaderboard_robustness_audit*` JSON/CSV artifacts.
- Create: `tests/test_leaderboard_robustness_audit.py`
  - Unit tests for fixed audit input manifest, contract guard, per-rule audit, no re-ranking, and JSON/CSV output shape.
- Create after run: `docs/ML/audit_leaderboard_robustness.py.md`
  - Documents command, inputs, outputs, constraints and artifact contract.
- Create after run: `docs/reports/2026-07-23-fractal0-rich-entry-leaderboard-robustness-audit.md`
  - Human report with research-only conclusions and next action.
- Modify after run: `docs/superpowers/roadmap.md`
  - Add this audit as the next `ACTIVE` or mark it completed, depending on execution status.
- Modify after run: `CONTEXT_HANDOFF.md`
  - Short baton pass with exact artifacts, limitations and next step.
- Modify after run: `docs/ML/benchmark_fractal0_entry_quality_filter.py.md`
  - Cross-link normalized leaderboard audit.
- Modify after run: `MODULE_INDEX.md`
  - Add the new audit script and docs entry.
- Modify after run if stage is closed: `CHANGELOG.md`, `wiki/research/fractal-stop-research.md`, `wiki/index.md`, `wiki/log.md`, `wiki/REPO_integrity.md`.

New artifacts:

- `ML/reports/leaderboard_robustness_audit.json`
- `ML/reports/leaderboard_robustness_audit_rules.csv`
- `ML/reports/leaderboard_robustness_audit_summary.csv`
- `ML/reports/leaderboard_robustness_audit_yearly.csv`
- `ML/reports/leaderboard_robustness_audit_quarterly.csv`
- `ML/reports/leaderboard_robustness_audit_side.csv`
- `ML/reports/leaderboard_robustness_audit_year_side.csv`
- `ML/reports/leaderboard_robustness_audit_score_shift.csv`
- `ML/reports/leaderboard_robustness_audit_stricter_cutoff.csv`
- `ML/reports/leaderboard_robustness_audit_topk_sensitivity.csv`
- `ML/reports/leaderboard_robustness_audit_calendar_slices.csv`
- `ML/reports/leaderboard_robustness_audit_missing_diagnostics.csv`
- `ML/reports/leaderboard_robustness_audit_classification.csv`

---

### Task 1: Add Fixed Audit Input Manifest And Contract Guard

**Methodology:** `00-research-management.md`, `09-validation-freeze.md`, `16-reporting-audit.md`, `A4-verdicts-stop-conditions.md`.

**Mandatory Checks:**
- Уровень исследования: `research_only`.
- Current search budget: no new search, exactly 11 fixed audit input rows.
- Artifact contract: `locked_test=not_opened`, `feature_contract_variant=normalized_atr_unit`.
- Every fixed audit input row must exist exactly once in `val_select` and exactly once in `val_eval` summary.
- Every fixed audit input row must be source-eligible: `eligible_for_winner=True` and `not_eligible_for_winner=False`.

**Completion Criterion:** Running the targeted contract tests proves the manifest is fixed, complete and fails closed on missing/changed rows.

**Files:**
- Create: `tests/test_leaderboard_robustness_audit.py`
- Create: `ML/baseline/audit_leaderboard_robustness.py`

**Interfaces:**
- Consumes: normalized rich-entry JSON and summary CSV from `ML/reports/fractal0_rich_entry_quality_normalized*`.
- Produces:
  - `RuleSpec` dataclass.
  - `LEADERBOARD_RULES: tuple[RuleSpec, ...]`.
  - `verify_global_artifact_contract(artifact: dict[str, object]) -> dict[str, object]`.
  - `verify_leaderboard_contract(summary: pd.DataFrame, rules: tuple[RuleSpec, ...]) -> pd.DataFrame`.

- [ ] **Step 1: Write failing manifest tests**

Create `tests/test_leaderboard_robustness_audit.py` with:

```python
import pandas as pd
import pytest

from ML.baseline import audit_leaderboard_robustness as audit


def test_fixed_audit_input_manifest_has_exact_11_rows_and_anchor_first():
    assert len(audit.LEADERBOARD_RULES) == 11
    assert audit.LEADERBOARD_RULES[0].original_rank == 1
    assert audit.LEADERBOARD_RULES[0].profile_id == "time_only"
    assert audit.LEADERBOARD_RULES[0].model_id == "linear"
    assert audit.LEADERBOARD_RULES[0].target_id == "target_entry_ev_regression"
    assert audit.LEADERBOARD_RULES[0].filter_id == "top30"
    assert [rule.original_rank for rule in audit.LEADERBOARD_RULES] == list(range(1, 12))


def test_global_artifact_contract_blocks_locked_test_or_legacy_contract():
    good = {"locked_test": "not_opened", "feature_contract_variant": "normalized_atr_unit"}
    assert audit.verify_global_artifact_contract(good)["status"] == "PASS"

    with pytest.raises(ValueError, match="locked_test"):
        audit.verify_global_artifact_contract({"locked_test": "opened", "feature_contract_variant": "normalized_atr_unit"})

    with pytest.raises(ValueError, match="feature_contract_variant"):
        audit.verify_global_artifact_contract({"locked_test": "not_opened", "feature_contract_variant": "legacy_rich"})


def test_leaderboard_contract_requires_exact_val_select_and_val_eval_rows():
    rows = []
    for rule in audit.LEADERBOARD_RULES:
        for split in ["val_select", "val_eval"]:
            rows.append(
                {
                    "stop_policy_id": audit.STOP_POLICY_ID,
                    "entry_id": audit.ENTRY_ID,
                    "mask_id": audit.MASK_ID,
                    "exit_id": audit.EXIT_ID,
                    "spread": audit.CANONICAL_SPREAD,
                    "split": split,
                    "profile_id": rule.profile_id,
                    "model_id": rule.model_id,
                    "target_id": rule.target_id,
                    "filter_id": rule.filter_id,
                    "entry_filter_score_col": "rich_entry_score",
                    "score_cutoff_on_val_select": -0.01 - rule.original_rank / 1000,
                    "n_trades": 100 + rule.original_rank,
                    "pf": 2.0,
                    "bs_p05": 1.5,
                    "mean_pnl_r": 0.1,
                    "max_drawdown_r": 1.0,
                    "pf_without_best_year": 1.2,
                    "effective_profit_years": 2.0,
                    "n_years": 2,
                    "eligible_for_winner": True,
                    "not_eligible_for_winner": False,
                    "not_eligible_reason": "",
                }
            )
    summary = pd.DataFrame(rows)

    result = audit.verify_leaderboard_contract(summary, audit.LEADERBOARD_RULES)

    assert len(result) == 11
    assert set(result["contract_status"]) == {"PASS"}
    assert set(result["split_pair_status"]) == {"PASS"}


def test_leaderboard_contract_fails_when_a_fixed_input_row_is_missing():
    summary = pd.DataFrame(
        [
            {
                "stop_policy_id": audit.STOP_POLICY_ID,
                "entry_id": audit.ENTRY_ID,
                "mask_id": audit.MASK_ID,
                "exit_id": audit.EXIT_ID,
                "spread": audit.CANONICAL_SPREAD,
                "split": "val_select",
                "profile_id": "time_only",
                "model_id": "linear",
                "target_id": "target_entry_ev_regression",
                "filter_id": "top30",
                "entry_filter_score_col": "rich_entry_score",
                "score_cutoff_on_val_select": -0.026718184259660646,
            }
        ]
    )

    with pytest.raises(ValueError, match="missing leaderboard summary row"):
        audit.verify_leaderboard_contract(summary, audit.LEADERBOARD_RULES)


def test_leaderboard_contract_requires_source_eligible_rows():
    rows = []
    for rule in audit.LEADERBOARD_RULES:
        for split in ["val_select", "val_eval"]:
            rows.append(
                {
                    "stop_policy_id": audit.STOP_POLICY_ID,
                    "entry_id": audit.ENTRY_ID,
                    "mask_id": audit.MASK_ID,
                    "exit_id": audit.EXIT_ID,
                    "spread": audit.CANONICAL_SPREAD,
                    "split": split,
                    "profile_id": rule.profile_id,
                    "model_id": rule.model_id,
                    "target_id": rule.target_id,
                    "filter_id": rule.filter_id,
                    "entry_filter_score_col": "rich_entry_score",
                    "score_cutoff_on_val_select": -0.01 - rule.original_rank / 1000,
                    "n_trades": 100 + rule.original_rank,
                    "pf": 2.0,
                    "bs_p05": 1.5,
                    "mean_pnl_r": 0.1,
                    "max_drawdown_r": 1.0,
                    "pf_without_best_year": 1.2,
                    "effective_profit_years": 2.0,
                    "n_years": 2,
                    "eligible_for_winner": True,
                    "not_eligible_for_winner": False,
                    "not_eligible_reason": "",
                }
            )
    rows[0]["eligible_for_winner"] = False
    summary = pd.DataFrame(rows)

    with pytest.raises(ValueError, match="not source-eligible"):
        audit.verify_leaderboard_contract(summary, audit.LEADERBOARD_RULES)
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
./.venv/bin/python -m pytest tests/test_leaderboard_robustness_audit.py -q
```

Expected: FAIL because `ML.baseline.audit_leaderboard_robustness` does not exist.

- [ ] **Step 3: Implement manifest and contract guard**

Create `ML/baseline/audit_leaderboard_robustness.py`:

```python
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ML.baseline import audit_time_only_robustness as base_audit


DEFAULT_INPUT_PREFIX = Path("ML/reports/fractal0_rich_entry_quality_normalized")
DEFAULT_OUTPUT_PREFIX = Path("ML/reports/leaderboard_robustness_audit")

STOP_POLICY_ID = "S2_fractal0_buffer_0_5_entry_floor_2"
ENTRY_ID = "E3_open_pullback_1_0atr"
MASK_ID = "M0_no_mask"
EXIT_ID = "X2_ml_opposite_any_p0_50"
CANONICAL_SPREAD = 0.2
ENTRY_FILTER_SCORE_COL = "rich_entry_score"


class LeaderboardAuditError(ValueError):
    decision = "UNKNOWN"


class GlobalArtifactContractError(LeaderboardAuditError):
    decision = "UNKNOWN_ARTIFACT_CONTRACT"


class LeaderboardContractError(LeaderboardAuditError):
    decision = "UNKNOWN_LEADERBOARD_CONTRACT"


@dataclass(frozen=True)
class RuleSpec:
    original_rank: int
    profile_id: str
    model_id: str
    target_id: str
    filter_id: str

    @property
    def rule_id(self) -> str:
        return f"rank{self.original_rank:02d}_{self.profile_id}_{self.model_id}_{self.target_id}_{self.filter_id}"


LEADERBOARD_RULES: tuple[RuleSpec, ...] = (
    RuleSpec(1, "time_only", "linear", "target_entry_ev_regression", "top30"),
    RuleSpec(2, "time_only", "linear", "target_entry_ev_regression", "top40"),
    RuleSpec(3, "time_only", "linear", "target_entry_ev_regression", "top50"),
    RuleSpec(4, "time_only", "linear", "target_entry_good_0_5r", "top40"),
    RuleSpec(5, "time_only", "linear", "target_entry_avoid_sl", "top30"),
    RuleSpec(6, "time_only", "linear", "target_entry_good_0_5r", "top50"),
    RuleSpec(7, "movement_plus_time", "linear", "target_entry_good_0_5r", "top40"),
    RuleSpec(8, "movement_plus_time", "linear", "target_entry_good_0_5r", "top30"),
    RuleSpec(9, "time_only", "hist_gradient_boosting", "target_entry_good_0_5r", "top50"),
    RuleSpec(10, "movement_plus_time", "linear", "target_entry_ev_regression", "top50"),
    RuleSpec(11, "movement_plus_time", "linear", "target_entry_good_0_5r", "top50"),
)


def verify_global_artifact_contract(artifact: dict[str, object]) -> dict[str, object]:
    checks = {
        "locked_test": artifact.get("locked_test") == "not_opened",
        "feature_contract_variant": artifact.get("feature_contract_variant") == "normalized_atr_unit",
    }
    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        raise GlobalArtifactContractError(f"global artifact contract failed: {failed}")
    return {"status": "PASS", "checks": checks}


def _summary_rows_for_rule(summary: pd.DataFrame, rule: RuleSpec, split: str) -> pd.DataFrame:
    mask = (
        summary["stop_policy_id"].astype(str).eq(STOP_POLICY_ID)
        & summary["entry_id"].astype(str).eq(ENTRY_ID)
        & summary["mask_id"].astype(str).eq(MASK_ID)
        & summary["exit_id"].astype(str).eq(EXIT_ID)
        & pd.to_numeric(summary["spread"], errors="coerce").eq(CANONICAL_SPREAD)
        & summary["split"].astype(str).eq(split)
        & summary["profile_id"].astype(str).eq(rule.profile_id)
        & summary["model_id"].astype(str).eq(rule.model_id)
        & summary["target_id"].astype(str).eq(rule.target_id)
        & summary["filter_id"].astype(str).eq(rule.filter_id)
        & summary["entry_filter_score_col"].astype(str).eq(ENTRY_FILTER_SCORE_COL)
    )
    return summary.loc[mask].copy()


def _as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if pd.isna(value):
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def verify_leaderboard_contract(summary: pd.DataFrame, rules: tuple[RuleSpec, ...] = LEADERBOARD_RULES) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for rule in rules:
        val_select = _summary_rows_for_rule(summary, rule, "val_select")
        val_eval = _summary_rows_for_rule(summary, rule, "val_eval")
        if len(val_select) != 1 or len(val_eval) != 1:
            raise LeaderboardContractError(
                f"missing leaderboard summary row for {rule.rule_id}: "
                f"val_select={len(val_select)}, val_eval={len(val_eval)}"
            )
        selected = val_select.iloc[0].to_dict()
        evaluated = val_eval.iloc[0].to_dict()
        if not _as_bool(selected.get("eligible_for_winner")) or _as_bool(selected.get("not_eligible_for_winner")):
            raise LeaderboardContractError(f"leaderboard row is not source-eligible: {rule.rule_id}")
        if not _as_bool(evaluated.get("eligible_for_winner")) or _as_bool(evaluated.get("not_eligible_for_winner")):
            raise LeaderboardContractError(f"leaderboard val_eval row is not source-eligible: {rule.rule_id}")
        rows.append(
            {
                "original_rank": rule.original_rank,
                "rule_id": rule.rule_id,
                "profile_id": rule.profile_id,
                "model_id": rule.model_id,
                "target_id": rule.target_id,
                "filter_id": rule.filter_id,
                "score_cutoff_on_val_select": float(selected["score_cutoff_on_val_select"]),
                "val_select_n_trades": int(selected["n_trades"]),
                "val_eval_n_trades": int(evaluated["n_trades"]),
                "val_eval_pf": float(evaluated["pf"]),
                "val_eval_bs_p05_source": float(evaluated["bs_p05"]),
                "contract_status": "PASS",
                "split_pair_status": "PASS",
            }
        )
    return pd.DataFrame(rows)
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
./.venv/bin/python -m pytest tests/test_leaderboard_robustness_audit.py -q
```

Expected: PASS for the five tests in this task.

---

### Task 2: Load Saved Artifacts With `usecols` And Build `FixedRule` Objects

**Methodology:** `06-temporal-split.md`, `09-validation-freeze.md`, `16-reporting-audit.md`.

**Mandatory Checks:**
- Large CSV reads use explicit `usecols`.
- Summary `usecols` includes `eligible_for_winner`, `not_eligible_for_winner` and `not_eligible_reason`.
- Each row uses saved `score_cutoff_on_val_select`; no recomputed threshold.
- `val_select` and `val_eval` roles stay separate.

**Completion Criterion:** Tests prove that each fixed audit input row becomes a full `FixedRule` with execution contract, saved cutoff and source eligibility fields available to the guard.

**Files:**
- Modify: `ML/baseline/audit_leaderboard_robustness.py`
- Modify: `tests/test_leaderboard_robustness_audit.py`

**Interfaces:**
- Consumes: `verify_leaderboard_contract(...) -> pd.DataFrame`.
- Produces:
  - `load_normalized_artifacts(prefix: Path) -> dict[str, object]`.
  - `fixed_rule_from_contract_row(row: pd.Series | dict[str, object]) -> base_audit.FixedRule`.

- [ ] **Step 1: Add failing tests for full rule conversion**

Append to `tests/test_leaderboard_robustness_audit.py`:

```python
def test_fixed_rule_from_contract_row_preserves_execution_contract_and_cutoff():
    row = {
        "original_rank": 7,
        "profile_id": "movement_plus_time",
        "model_id": "linear",
        "target_id": "target_entry_good_0_5r",
        "filter_id": "top40",
        "score_cutoff_on_val_select": -0.0123,
    }

    rule = audit.fixed_rule_from_contract_row(row)

    assert rule.stop_policy_id == audit.STOP_POLICY_ID
    assert rule.entry_id == audit.ENTRY_ID
    assert rule.mask_id == audit.MASK_ID
    assert rule.exit_id == audit.EXIT_ID
    assert rule.spread == audit.CANONICAL_SPREAD
    assert rule.profile_id == "movement_plus_time"
    assert rule.model_id == "linear"
    assert rule.target_id == "target_entry_good_0_5r"
    assert rule.filter_id == "top40"
    assert rule.entry_filter_score_col == "rich_entry_score"
    assert rule.score_cutoff_on_val_select == -0.0123


def test_summary_usecols_include_source_eligibility_fields():
    assert "eligible_for_winner" in audit.SUMMARY_USECOLS
    assert "not_eligible_for_winner" in audit.SUMMARY_USECOLS
    assert "not_eligible_reason" in audit.SUMMARY_USECOLS
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
./.venv/bin/python -m pytest tests/test_leaderboard_robustness_audit.py::test_fixed_rule_from_contract_row_preserves_execution_contract_and_cutoff -q
```

Expected: FAIL because `fixed_rule_from_contract_row` is missing.

- [ ] **Step 3: Implement artifact loading and rule conversion**

Append to `ML/baseline/audit_leaderboard_robustness.py`:

```python
SUMMARY_USECOLS = list(
    dict.fromkeys(
        [
            *base_audit.SUMMARY_USECOLS,
            "eligible_for_winner",
            "not_eligible_for_winner",
            "not_eligible_reason",
        ]
    )
)
TRADES_USECOLS = base_audit.TRADES_USECOLS
SCORES_USECOLS = base_audit.SCORES_USECOLS


def _csv(path: Path, usecols: list[str]) -> pd.DataFrame:
    return pd.read_csv(path, sep=";", usecols=usecols)


def load_normalized_artifacts(prefix: Path = DEFAULT_INPUT_PREFIX) -> dict[str, object]:
    json_path = prefix.with_suffix(".json")
    with json_path.open("r", encoding="utf-8") as handle:
        artifact = json.load(handle)
    return {
        "artifact": artifact,
        "summary": _csv(prefix.with_name(prefix.name + "_summary.csv"), SUMMARY_USECOLS),
        "trades": _csv(prefix.with_name(prefix.name + "_trades.csv"), TRADES_USECOLS),
        "scores": _csv(prefix.with_name(prefix.name + "_scores.csv"), SCORES_USECOLS),
    }


def fixed_rule_from_contract_row(row: pd.Series | dict[str, object]) -> base_audit.FixedRule:
    data = row.to_dict() if isinstance(row, pd.Series) else dict(row)
    return base_audit.FixedRule(
        stop_policy_id=STOP_POLICY_ID,
        entry_id=ENTRY_ID,
        mask_id=MASK_ID,
        exit_id=EXIT_ID,
        spread=CANONICAL_SPREAD,
        profile_id=str(data["profile_id"]),
        model_id=str(data["model_id"]),
        target_id=str(data["target_id"]),
        filter_id=str(data["filter_id"]),
        entry_filter_score_col=ENTRY_FILTER_SCORE_COL,
        score_cutoff_on_val_select=float(data["score_cutoff_on_val_select"]),
    )
```

- [ ] **Step 4: Run targeted tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_leaderboard_robustness_audit.py -q
```

Expected: PASS.

---

### Task 3: Compute Per-Rule Robustness Diagnostics

**Methodology:** `06-temporal-split.md`, `09-validation-freeze.md`, `11-robustness.md`.

**Mandatory Checks:**
- Robustness is not based on aggregate PF only.
- Each rule has yearly, quarterly, side, year-side, entry/fill/exit calendar, score-shift, stricter cutoff, top-k and sequential block bootstrap diagnostics.
- `BS_p05` used for robustness is recomputed with sequential block bootstrap.
- Small-N stricter cutoff rows are warnings/reasons, not winner selectors.

**Completion Criterion:** `audit_one_rule(...)` returns complete diagnostics and replaces source `bs_p05` with `sequential_block_bs_p05`.

**Files:**
- Modify: `ML/baseline/audit_leaderboard_robustness.py`
- Modify: `tests/test_leaderboard_robustness_audit.py`

**Interfaces:**
- Consumes: `fixed_rule_from_contract_row(...) -> base_audit.FixedRule`.
- Produces:
  - `audit_one_rule(summary, trades, scores, contract_row) -> dict[str, object]`.
  - DataFrames under keys: `summary`, `yearly`, `quarterly`, `side`, `year_side`, `score_shift`, `stricter_cutoff`, `topk_sensitivity`, `calendar_slices`.

- [ ] **Step 1: Add failing test for one-rule diagnostics**

Append to `tests/test_leaderboard_robustness_audit.py`:

```python
def test_audit_one_rule_recomputes_block_bootstrap_and_tags_all_rows():
    contract_row = {
        "original_rank": 1,
        "rule_id": "rank01_time_only_linear_target_entry_ev_regression_top30",
        "profile_id": "time_only",
        "model_id": "linear",
        "target_id": "target_entry_ev_regression",
        "filter_id": "top30",
        "score_cutoff_on_val_select": -0.02,
    }
    base_cols = {
        "stop_policy_id": audit.STOP_POLICY_ID,
        "entry_id": audit.ENTRY_ID,
        "mask_id": audit.MASK_ID,
        "exit_id": audit.EXIT_ID,
        "spread": audit.CANONICAL_SPREAD,
        "profile_id": "time_only",
        "model_id": "linear",
        "target_id": "target_entry_ev_regression",
    }
    summary = pd.DataFrame(
        [
            {
                **base_cols,
                "split": "val_eval",
                "filter_id": "top30",
                "n_trades": 4,
                "gross_profit": 2.2,
                "gross_loss": 0.7,
                "pf": 3.142857,
                "mean_pnl_r": 0.375,
                "median_pnl_r": 0.25,
                "max_drawdown_r": 0.5,
                "win_rate": 0.5,
                "bs_p05": 2.0,
                "negative_years": 0,
                "pf_without_best_year": 1.5,
                "effective_profit_years": 2.0,
                "n_years": 2,
                "score_cutoff_on_val_select": -0.02,
                "entry_filter_score_col": "rich_entry_score",
            }
        ]
    )
    trades = pd.DataFrame(
        [
            {**base_cols, "split": "val_eval", "filter_id": "top30", "position_id": "a", "side": "BUY", "signal_time": "2021-01-01", "fill_time": "2021-01-01 01:00", "exit_time": "2021-01-02", "pnl_r": 1.0, "close_reason": "TP", "hold_bars": 3, "ambiguous": False},
            {**base_cols, "split": "val_eval", "filter_id": "top30", "position_id": "b", "side": "SELL", "signal_time": "2021-02-01", "fill_time": "2021-02-01 01:00", "exit_time": "2021-02-02", "pnl_r": -0.5, "close_reason": "SL", "hold_bars": 2, "ambiguous": False},
            {**base_cols, "split": "val_eval", "filter_id": "top30", "position_id": "c", "side": "BUY", "signal_time": "2022-01-01", "fill_time": "2022-01-01 01:00", "exit_time": "2022-01-02", "pnl_r": 1.2, "close_reason": "ML_CLOSE", "hold_bars": 5, "ambiguous": False},
            {**base_cols, "split": "val_eval", "filter_id": "top30", "position_id": "d", "side": "SELL", "signal_time": "2022-02-01", "fill_time": "2022-02-01 01:00", "exit_time": "2022-02-02", "pnl_r": -0.2, "close_reason": "TIME", "hold_bars": 4, "ambiguous": False},
        ]
    )
    scores = pd.DataFrame(
        [
            {"split": "val_select", "profile_id": "time_only", "model_id": "linear", "target_id": "target_entry_ev_regression", "filter_id": "top30", "position_id": "s1", "rich_entry_score": -0.01},
            {"split": "val_eval", "profile_id": "time_only", "model_id": "linear", "target_id": "target_entry_ev_regression", "filter_id": "top30", "position_id": "a", "rich_entry_score": -0.01},
            {"split": "val_eval", "profile_id": "time_only", "model_id": "linear", "target_id": "target_entry_ev_regression", "filter_id": "top30", "position_id": "b", "rich_entry_score": -0.03},
        ]
    )

    result = audit.audit_one_rule(summary, trades, scores, contract_row)

    assert result["summary"]["rule_id"] == contract_row["rule_id"]
    assert result["summary"]["original_rank"] == 1
    assert result["summary"]["sequential_block_bs_p05"] is not None
    assert set(result["yearly"]["rule_id"]) == {contract_row["rule_id"]}
    assert set(result["side"]["side"]) == {"BUY", "SELL"}
    assert {"signal_time", "fill_time", "exit_time"}.issubset(set(result["calendar_slices"]["time_basis"]))
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
./.venv/bin/python -m pytest tests/test_leaderboard_robustness_audit.py::test_audit_one_rule_recomputes_block_bootstrap_and_tags_all_rows -q
```

Expected: FAIL because `audit_one_rule` is missing.

- [ ] **Step 3: Implement one-rule diagnostics**

Append to `ML/baseline/audit_leaderboard_robustness.py`:

```python
def _tag_frame(frame: pd.DataFrame, contract_row: dict[str, object]) -> pd.DataFrame:
    out = frame.copy()
    if out.empty:
        return out
    insert_cols = {
        "original_rank": int(contract_row["original_rank"]),
        "rule_id": str(contract_row["rule_id"]),
        "profile_id": str(contract_row["profile_id"]),
        "model_id": str(contract_row["model_id"]),
        "target_id": str(contract_row["target_id"]),
        "filter_id": str(contract_row["filter_id"]),
    }
    for column, value in reversed(list(insert_cols.items())):
        if column not in out.columns:
            out.insert(0, column, value)
        else:
            out[column] = value
    return out


def _summary_for_rule(summary: pd.DataFrame, rule: base_audit.FixedRule) -> dict[str, object]:
    row = base_audit.filter_fixed_rule_rows(summary, rule, split="val_eval")
    if len(row) != 1:
        raise ValueError(f"val_eval summary expected once for {rule}, got {len(row)}")
    return row.iloc[0].to_dict()


def audit_one_rule(
    summary: pd.DataFrame,
    trades: pd.DataFrame,
    scores: pd.DataFrame,
    contract_row: pd.Series | dict[str, object],
) -> dict[str, object]:
    row = contract_row.to_dict() if isinstance(contract_row, pd.Series) else dict(contract_row)
    rule = fixed_rule_from_contract_row(row)
    fixed_trades = base_audit.filter_fixed_rule_rows(trades, rule, split="val_eval")
    selected_summary = _summary_for_rule(summary, rule)
    bootstrap = base_audit.sequential_block_bootstrap_pf(
        fixed_trades,
        seed=20260723 + int(row["original_rank"]),
        n_bootstrap=1000,
        block_size=20,
    )
    selected_summary["source_bs_p05"] = selected_summary.get("bs_p05")
    selected_summary["sequential_block_bs_p05"] = bootstrap.get("bs_p05")
    selected_summary["bs_p05"] = bootstrap.get("bs_p05")
    selected_summary["original_rank"] = int(row["original_rank"])
    selected_summary["rule_id"] = str(row["rule_id"])
    selected_summary["rule_family_tag"] = "time_heavy" if "time" in str(row["profile_id"]) else "non_time"

    concentration = base_audit.profit_concentration(fixed_trades)
    selected_summary.update({f"concentration_{key}": value for key, value in concentration.items()})

    diagnostics = {
        "summary": selected_summary,
        "yearly": _tag_frame(base_audit.metrics_by_period(fixed_trades, "Y"), row),
        "quarterly": _tag_frame(base_audit.metrics_by_period(fixed_trades, "Q"), row),
        "side": _tag_frame(base_audit.metrics_by_side(fixed_trades), row),
        "year_side": _tag_frame(base_audit.metrics_by_year_side(fixed_trades), row),
        "score_shift": _tag_frame(base_audit.score_shift(scores, rule), row),
        "stricter_cutoff": _tag_frame(base_audit.stricter_cutoff_sensitivity(scores, trades, rule), row),
        "topk_sensitivity": _tag_frame(base_audit.topk_sensitivity(trades, rule), row),
        "calendar_slices": _tag_frame(base_audit.calendar_slices(trades, rule), row),
        "block_bootstrap": bootstrap,
    }
    return diagnostics
```

- [ ] **Step 4: Run targeted tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_leaderboard_robustness_audit.py -q
```

Expected: PASS.

---

### Task 4: Add Missing-Diagnostics Statuses And Per-Rule Decisions

**Methodology:** `11-robustness.md`, `12-backtest-costs.md`, `A4-verdicts-stop-conditions.md`.

**Mandatory Checks:**
- Missing stress-cost resimulation blocks any stronger conclusion.
- Missing sequential position simulation is disclosure unless made a required gate.
- Missing timezone/calendar importance is explicit for time-heavy rules.
- Decision labels do not contain `PASS` as a trading/candidate implication.

**Completion Criterion:** Every rule gets a decision and disclosures, but no decision can become `candidate` or `permission_to_open_locked_test`.

**Files:**
- Modify: `ML/baseline/audit_leaderboard_robustness.py`
- Modify: `tests/test_leaderboard_robustness_audit.py`

**Interfaces:**
- Consumes: `audit_one_rule(...) -> dict[str, object]`.
- Produces:
  - `missing_diagnostics_for_rule(contract_row) -> pd.DataFrame`.
  - `rule_decision(summary_row, side, stricter_cutoff, topk, missing) -> dict[str, object]`.
  - `aggregate_limitation_statuses(missing: pd.DataFrame) -> dict[str, object]`.

- [ ] **Step 1: Add failing decision test**

Append to `tests/test_leaderboard_robustness_audit.py`:

```python
def test_rule_decision_discloses_missing_cost_and_time_checks_without_candidate_language():
    summary_row = {
        "rule_id": "rank07_movement_plus_time_linear_target_entry_good_0_5r_top40",
        "n_trades": 979,
        "pf": 3.3,
        "bs_p05": 2.8,
        "sequential_block_bs_p05": 2.8,
        "pf_without_best_year": 2.0,
        "concentration_n_years": 2,
        "concentration_effective_profit_years": 1.9,
    }
    side = pd.DataFrame({"side": ["BUY", "SELL"], "n_trades": [500, 479], "mean_pnl_r": [0.2, 0.1], "pf": [2.0, 1.5], "max_drawdown_r": [2.0, 3.0]})
    stricter = pd.DataFrame({"cutoff_offset": [0.0, 0.005, 0.01, 0.02], "n_trades": [979, 800, 610, 340], "pf": [3.3, 3.1, 2.8, 2.0]})
    topk = pd.DataFrame({"filter_id": ["top30", "top40", "top50"], "n_trades": [760, 979, 1223], "pf": [3.4, 3.3, 3.2]})
    missing = audit.missing_diagnostics_for_rule({"rule_id": summary_row["rule_id"], "profile_id": "movement_plus_time"})

    result = audit.rule_decision(summary_row, side, stricter, topk, missing)

    assert result["decision"] == "RULE_ROBUSTNESS_INCOMPLETE"
    assert "stress_costs_not_computable" in result["reasons"]
    assert "timezone_shift_not_run" in result["disclosures"]
    assert result["allowed_max_verdict"] == "research_only"
    assert "candidate" not in result["decision"].lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
./.venv/bin/python -m pytest tests/test_leaderboard_robustness_audit.py::test_rule_decision_discloses_missing_cost_and_time_checks_without_candidate_language -q
```

Expected: FAIL because `missing_diagnostics_for_rule` and `rule_decision` are missing.

- [ ] **Step 3: Implement decision helpers**

Append to `ML/baseline/audit_leaderboard_robustness.py`:

```python
LEADERBOARD_DECISION_GATE_CONFIG = {
    "min_bs_p05": 1.0,
    "min_pf_without_best_year": 1.0,
    "min_side_pf": 1.0,
    "min_side_n_trades": 30,
    "max_side_drawdown_r": 8.5,
    "stricter_cutoff_min_n_trades": 300,
    "topk_min_pf": 1.0,
    "topk_min_n_trades": 300,
    "effective_profit_years_formula": "max(1.5, 0.6 * n_years)",
}


def missing_diagnostics_for_rule(contract_row: pd.Series | dict[str, object]) -> pd.DataFrame:
    row = contract_row.to_dict() if isinstance(contract_row, pd.Series) else dict(contract_row)
    profile_id = str(row["profile_id"])
    records = [
        {
            "rule_id": str(row["rule_id"]),
            "diagnostic": "stress_costs",
            "status": "NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS",
            "reason": "saved trades contain realized pnl for canonical spread only; stress spread requires explicit resimulation",
        },
        {
            "rule_id": str(row["rule_id"]),
            "diagnostic": "sequential_position_constraint",
            "status": "NOT_RUN",
            "reason": "position-overlap simulation is not implemented in this saved-artifact audit",
        },
    ]
    if "time" in profile_id:
        records.extend(
            [
                {
                    "rule_id": str(row["rule_id"]),
                    "diagnostic": "timezone_shift",
                    "status": "NOT_RUN",
                    "reason": "requires frozen rescore of time features under predefined timezone shifts",
                },
                {
                    "rule_id": str(row["rule_id"]),
                    "diagnostic": "calendar_permutation_importance",
                    "status": "NOT_RUN",
                    "reason": "fitted per-profile estimator is not persisted for model-level permutation importance",
                },
            ]
        )
    return pd.DataFrame(records)


def rule_decision(
    summary_row: dict[str, object],
    side: pd.DataFrame,
    stricter_cutoff: pd.DataFrame,
    topk: pd.DataFrame,
    missing: pd.DataFrame,
) -> dict[str, object]:
    gate = LEADERBOARD_DECISION_GATE_CONFIG
    reasons: list[str] = []
    disclosures: list[str] = []
    n_years = int(summary_row.get("concentration_n_years") or summary_row.get("n_years") or 0)
    effective_years = float(summary_row.get("concentration_effective_profit_years") or summary_row.get("effective_profit_years") or 0.0)
    if effective_years < max(1.5, 0.6 * n_years):
        reasons.append("profit_concentration_fail")
    if float(summary_row.get("sequential_block_bs_p05") or summary_row.get("bs_p05") or 0.0) < gate["min_bs_p05"]:
        reasons.append("block_bootstrap_fail")
    if float(summary_row.get("pf_without_best_year") or 0.0) < gate["min_pf_without_best_year"]:
        reasons.append("pf_without_best_year_fail")
    if side.empty or (pd.to_numeric(side.get("pf"), errors="coerce") < gate["min_side_pf"]).any():
        reasons.append("side_pf_fail")
    if side.empty or (pd.to_numeric(side.get("n_trades"), errors="coerce") < gate["min_side_n_trades"]).any():
        reasons.append("side_sample_fail")
    if side.empty or (pd.to_numeric(side.get("max_drawdown_r"), errors="coerce") > gate["max_side_drawdown_r"]).any():
        reasons.append("side_drawdown_warning")
    if stricter_cutoff.empty or pd.to_numeric(stricter_cutoff.get("n_trades"), errors="coerce").min() < gate["stricter_cutoff_min_n_trades"]:
        reasons.append("stricter_cutoff_sample_fragile")
    if topk.empty or (pd.to_numeric(topk.get("pf"), errors="coerce") < gate["topk_min_pf"]).any():
        reasons.append("topk_pf_fragile")
    if topk.empty or (pd.to_numeric(topk.get("n_trades"), errors="coerce") < gate["topk_min_n_trades"]).any():
        reasons.append("topk_sample_fragile")

    missing_status = {(str(row["diagnostic"]), str(row["status"])) for _, row in missing.iterrows()}
    if ("stress_costs", "NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS") in missing_status:
        reasons.append("stress_costs_not_computable")
    if ("sequential_position_constraint", "NOT_RUN") in missing_status:
        disclosures.append("sequential_position_constraint_not_run")
    if ("timezone_shift", "NOT_RUN") in missing_status:
        disclosures.append("timezone_shift_not_run")
    if ("calendar_permutation_importance", "NOT_RUN") in missing_status:
        disclosures.append("calendar_permutation_importance_not_run")

    if "block_bootstrap_fail" in reasons or "pf_without_best_year_fail" in reasons:
        decision = "REJECT_RULE_AS_UNSTABLE"
    elif reasons:
        decision = "RULE_ROBUSTNESS_INCOMPLETE"
    else:
        decision = "RULE_ROBUSTNESS_SLICE_OK_FOR_RESEARCH_COMPARISON"
    return {
        "decision": decision,
        "reasons": reasons,
        "disclosures": disclosures,
        "allowed_max_verdict": "research_only",
        "decision_gate_config": gate,
    }


def aggregate_limitation_statuses(missing: pd.DataFrame) -> dict[str, object]:
    statuses = {
        "locked_test_status": "not_opened",
        "stress_costs_status": "NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS",
        "timezone_shift_status": "NOT_RUN",
        "calendar_permutation_importance_status": "NOT_RUN",
        "sequential_position_constraint_status": "NOT_RUN",
        "multi_seed_status": "NOT_RUN",
        "provider_drift_status": "NOT_RUN",
        "transfer_status": "NOT_RUN",
    }
    if not missing.empty:
        for diagnostic, group in missing.groupby("diagnostic"):
            statuses[f"{diagnostic}_status"] = ",".join(sorted(set(group["status"].astype(str))))
    statuses["limitations"] = [
        "locked_test remains closed",
        "broad-search origin bias remains",
        "stress-cost resimulation is not computed from saved filtered artifacts",
        "timezone-shift rescore is not run for time-heavy profiles",
        "calendar permutation importance is not run because fitted estimators are not persisted",
        "multi-seed, provider-drift and transfer checks are not run",
    ]
    return statuses
```

- [ ] **Step 4: Run targeted tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_leaderboard_robustness_audit.py -q
```

Expected: PASS.

---

### Task 5: Run Batch Audit And Write Structured Artifacts

**Methodology:** `00-research-management.md`, `06-temporal-split.md`, `11-robustness.md`, `16-reporting-audit.md`.

**Mandatory Checks:**
- Batch preserves `original_rank`; no re-ranking by new metrics.
- Output JSON includes input artifact hashes, source normalized artifact hashes, rule manifest and limitations.
- Output JSON includes source `normalization_config`, normalized audit artifact paths and `scale_contract`.
- `UNKNOWN` failures are structured and machine-readable.
- Contract, missing-input and schema failures use distinct decisions.
- `overall_decision` is derived from per-rule decisions and missing diagnostics; `run_status` records whether the CLI completed.
- Reported metrics come from generated JSON/CSV.

**Completion Criterion:** CLI produces all declared artifacts with 11 rules and exits `0`; contract failure path exits `1`.

**Files:**
- Modify: `ML/baseline/audit_leaderboard_robustness.py`
- Modify: `tests/test_leaderboard_robustness_audit.py`

**Interfaces:**
- Consumes: `audit_one_rule(...)`, `rule_decision(...)`.
- Produces:
  - `run_audit(input_prefix: Path, output_prefix: Path) -> dict[str, object]`.
  - `overall_decision_from_classification(classification: pd.DataFrame, missing: pd.DataFrame) -> dict[str, object]`.
  - `source_scale_contract(artifact: dict[str, object]) -> dict[str, object]`.
  - CLI with `--input-prefix` and `--output-prefix`.

- [ ] **Step 1: Add failing run-level test**

Append to `tests/test_leaderboard_robustness_audit.py`:

```python
def test_build_classification_preserves_original_rank_and_never_selects_new_winner():
    summaries = pd.DataFrame(
        [
            {"original_rank": 2, "rule_id": "rank02", "profile_id": "time_only", "pf": 9.0, "sequential_block_bs_p05": 8.0},
            {"original_rank": 1, "rule_id": "rank01", "profile_id": "time_only", "pf": 4.0, "sequential_block_bs_p05": 3.0},
        ]
    )
    decisions = {
        "rank01": {"decision": "RULE_ROBUSTNESS_INCOMPLETE", "reasons": ["stress_costs_not_computable"], "disclosures": [], "allowed_max_verdict": "research_only"},
        "rank02": {"decision": "RULE_ROBUSTNESS_INCOMPLETE", "reasons": ["stress_costs_not_computable"], "disclosures": [], "allowed_max_verdict": "research_only"},
    }

    result = audit.build_classification(summaries, decisions)

    assert result["original_rank"].tolist() == [1, 2]
    assert set(result["new_winner_selected"]) == {False}
    assert set(result["allowed_max_verdict"]) == {"research_only"}


def test_overall_decision_reflects_incomplete_missing_checks_not_only_run_completion():
    classification = pd.DataFrame(
        [
            {"original_rank": 1, "rule_id": "rank01", "profile_id": "time_only", "decision": "RULE_ROBUSTNESS_INCOMPLETE"},
            {"original_rank": 2, "rule_id": "rank02", "profile_id": "movement_plus_time", "decision": "RULE_ROBUSTNESS_INCOMPLETE"},
        ]
    )
    missing = pd.DataFrame(
        [
            {"rule_id": "rank01", "diagnostic": "stress_costs", "status": "NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS"},
            {"rule_id": "rank01", "diagnostic": "timezone_shift", "status": "NOT_RUN"},
        ]
    )

    result = audit.overall_decision_from_classification(classification, missing)

    assert result["overall_decision"] == "LEADERBOARD_ROBUSTNESS_INCOMPLETE_NEEDS_COST_TIME_CHECKS"
    assert "stress_costs_not_computable" in result["overall_decision_reasons"]
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
./.venv/bin/python -m pytest tests/test_leaderboard_robustness_audit.py::test_build_classification_preserves_original_rank_and_never_selects_new_winner -q
```

Expected: FAIL because `build_classification` is missing.

- [ ] **Step 3: Implement batch classification and artifact writing**

Append to `ML/baseline/audit_leaderboard_robustness.py`:

```python
def build_classification(summaries: pd.DataFrame, decisions: dict[str, dict[str, object]]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for _, row in summaries.sort_values("original_rank").iterrows():
        rule_id = str(row["rule_id"])
        decision = decisions[rule_id]
        profile_id = str(row["profile_id"])
        if profile_id == "time_only":
            interpretation = "stable_but_time_explained"
        elif "time" in profile_id:
            interpretation = "time_heavy_not_additive_evidence"
        else:
            interpretation = "non_time_profile_not_in_top11"
        if decision["decision"] == "REJECT_RULE_AS_UNSTABLE":
            interpretation = "fragile_by_robustness_gate"
        elif "stress_costs_not_computable" in decision.get("reasons", []):
            interpretation = f"{interpretation}_needs_cost_resimulation"
        rows.append(
            {
                "original_rank": int(row["original_rank"]),
                "rule_id": rule_id,
                "profile_id": profile_id,
                "model_id": str(row["model_id"]),
                "target_id": str(row["target_id"]),
                "filter_id": str(row["filter_id"]),
                "decision": str(decision["decision"]),
                "interpretation": interpretation,
                "reasons": ",".join(str(x) for x in decision.get("reasons", [])),
                "disclosures": ",".join(str(x) for x in decision.get("disclosures", [])),
                "allowed_max_verdict": "research_only",
                "new_winner_selected": False,
            }
        )
    return pd.DataFrame(rows)


def overall_decision_from_classification(classification: pd.DataFrame, missing: pd.DataFrame) -> dict[str, object]:
    decisions = set(classification["decision"].astype(str))
    profiles = set(classification["profile_id"].astype(str))
    missing_pairs = {(str(row["diagnostic"]), str(row["status"])) for _, row in missing.iterrows()}
    reasons: list[str] = []
    if decisions == {"REJECT_RULE_AS_UNSTABLE"}:
        return {
            "overall_decision": "ALL_RULES_REJECTED_AS_UNSTABLE_RESEARCH_ONLY",
            "overall_decision_reasons": ["all_rules_rejected_as_unstable"],
        }
    if ("stress_costs", "NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS") in missing_pairs:
        reasons.append("stress_costs_not_computable")
    if ("timezone_shift", "NOT_RUN") in missing_pairs:
        reasons.append("timezone_shift_not_run")
    if reasons:
        return {
            "overall_decision": "LEADERBOARD_ROBUSTNESS_INCOMPLETE_NEEDS_COST_TIME_CHECKS",
            "overall_decision_reasons": reasons,
        }
    if profiles.issubset({"time_only", "movement_plus_time"}):
        return {
            "overall_decision": "NO_STANDALONE_NON_TIME_EVIDENCE_RESEARCH_ONLY",
            "overall_decision_reasons": ["leaderboard_contains_only_time_heavy_profiles"],
        }
    return {
        "overall_decision": "LEADERBOARD_ROBUSTNESS_SLICE_REVIEW_REQUIRED_RESEARCH_ONLY",
        "overall_decision_reasons": ["non_time_profile_present_requires_manual_comparator_review"],
    }


def source_scale_contract(artifact: dict[str, object]) -> dict[str, object]:
    source_artifacts = artifact.get("artifacts", {}) if isinstance(artifact.get("artifacts"), dict) else {}
    flags = artifact.get("feature_distribution_flags") or []
    statuses = {str(row.get("status", "")).upper() for row in flags if isinstance(row, dict)}
    if {"FAIL", "ERROR"} & statuses:
        status = "FAIL"
    elif "WARNING" in statuses:
        status = "DIAGNOSTIC_ONLY"
    else:
        status = "PASS"
    return {
        "status": status,
        "feature_contract_variant": artifact.get("feature_contract_variant"),
        "normalization_config": artifact.get("normalization_config"),
        "normalization_config_json": source_artifacts.get("normalization_config_json"),
        "normalized_feature_distribution_audit_csv": source_artifacts.get("normalized_feature_distribution_audit_csv"),
        "scale_contract_source": "source normalized artifact",
        "flag_statuses": sorted(status for status in statuses if status),
    }


def _write_csv(frame: pd.DataFrame, path: Path) -> None:
    frame.to_csv(path, sep=";", index=False)


def _unknown(
    output_prefix: Path,
    decision: str,
    exc: Exception,
    source_artifact: dict[str, object] | None = None,
) -> dict[str, object]:
    source_locked_test = source_artifact.get("locked_test") if source_artifact else None
    if source_artifact is None:
        locked_test_status = "UNKNOWN_SOURCE_NOT_LOADED"
    elif source_locked_test == "not_opened":
        locked_test_status = "not_opened"
    else:
        locked_test_status = "SOURCE_CONTRACT_FAILED"
    result = {
        "experiment": "leaderboard_robustness_audit",
        "status": "UNKNOWN",
        "run_status": "failed",
        "verdict": "research_only",
        "locked_test": None,
        "locked_test_status": locked_test_status,
        "source_locked_test": source_locked_test,
        "allowed_max_verdict": "research_only",
        "decision": {"decision": decision, "reasons": [str(exc)]},
        "overall_decision": decision,
        "contract_errors": [str(exc)],
        "limitations": ["input or contract failure blocked leaderboard robustness audit"],
    }
    output_prefix.with_suffix(".json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result


def run_audit(input_prefix: Path = DEFAULT_INPUT_PREFIX, output_prefix: Path = DEFAULT_OUTPUT_PREFIX) -> dict[str, object]:
    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    artifact: dict[str, object] | None = None
    try:
        loaded = load_normalized_artifacts(input_prefix)
        artifact = loaded["artifact"]
        summary = loaded["summary"]
        trades = loaded["trades"]
        scores = loaded["scores"]
        global_contract = verify_global_artifact_contract(artifact)
        rule_contract = verify_leaderboard_contract(summary, LEADERBOARD_RULES)
        input_artifacts = base_audit.input_artifact_metadata(input_prefix)
    except GlobalArtifactContractError as exc:
        return _unknown(output_prefix, exc.decision, exc, artifact)
    except LeaderboardContractError as exc:
        return _unknown(output_prefix, exc.decision, exc, artifact)
    except FileNotFoundError as exc:
        return _unknown(output_prefix, "UNKNOWN_INPUT_ARTIFACTS", exc, artifact)
    except (json.JSONDecodeError, pd.errors.ParserError, ValueError) as exc:
        return _unknown(output_prefix, "UNKNOWN_INPUT_SCHEMA", exc, artifact)

    collected = {
        "summary": [],
        "yearly": [],
        "quarterly": [],
        "side": [],
        "year_side": [],
        "score_shift": [],
        "stricter_cutoff": [],
        "topk_sensitivity": [],
        "calendar_slices": [],
        "missing_diagnostics": [],
    }
    decisions: dict[str, dict[str, object]] = {}
    for _, contract_row in rule_contract.iterrows():
        diagnostics = audit_one_rule(summary, trades, scores, contract_row)
        missing = missing_diagnostics_for_rule(contract_row)
        decision = rule_decision(
            diagnostics["summary"],
            diagnostics["side"],
            diagnostics["stricter_cutoff"],
            diagnostics["topk_sensitivity"],
            missing,
        )
        decisions[str(contract_row["rule_id"])] = decision
        collected["summary"].append(pd.DataFrame([diagnostics["summary"]]))
        for key in ["yearly", "quarterly", "side", "year_side", "score_shift", "stricter_cutoff", "topk_sensitivity", "calendar_slices"]:
            collected[key].append(diagnostics[key])
        collected["missing_diagnostics"].append(missing)

    frames = {key: pd.concat(value, ignore_index=True) if value else pd.DataFrame() for key, value in collected.items()}
    classification = build_classification(frames["summary"], decisions)
    limitation_statuses = aggregate_limitation_statuses(frames["missing_diagnostics"])
    overall = overall_decision_from_classification(classification, frames["missing_diagnostics"])
    artifacts = {
        "rules_csv": output_prefix.with_name(output_prefix.name + "_rules.csv"),
        "summary_csv": output_prefix.with_name(output_prefix.name + "_summary.csv"),
        "yearly_csv": output_prefix.with_name(output_prefix.name + "_yearly.csv"),
        "quarterly_csv": output_prefix.with_name(output_prefix.name + "_quarterly.csv"),
        "side_csv": output_prefix.with_name(output_prefix.name + "_side.csv"),
        "year_side_csv": output_prefix.with_name(output_prefix.name + "_year_side.csv"),
        "score_shift_csv": output_prefix.with_name(output_prefix.name + "_score_shift.csv"),
        "stricter_cutoff_csv": output_prefix.with_name(output_prefix.name + "_stricter_cutoff.csv"),
        "topk_sensitivity_csv": output_prefix.with_name(output_prefix.name + "_topk_sensitivity.csv"),
        "calendar_slices_csv": output_prefix.with_name(output_prefix.name + "_calendar_slices.csv"),
        "missing_diagnostics_csv": output_prefix.with_name(output_prefix.name + "_missing_diagnostics.csv"),
        "classification_csv": output_prefix.with_name(output_prefix.name + "_classification.csv"),
    }
    _write_csv(rule_contract, artifacts["rules_csv"])
    for key, csv_key in [
        ("summary", "summary_csv"),
        ("yearly", "yearly_csv"),
        ("quarterly", "quarterly_csv"),
        ("side", "side_csv"),
        ("year_side", "year_side_csv"),
        ("score_shift", "score_shift_csv"),
        ("stricter_cutoff", "stricter_cutoff_csv"),
        ("topk_sensitivity", "topk_sensitivity_csv"),
        ("calendar_slices", "calendar_slices_csv"),
        ("missing_diagnostics", "missing_diagnostics_csv"),
    ]:
        _write_csv(frames[key], artifacts[csv_key])
    _write_csv(classification, artifacts["classification_csv"])

    result = {
        "experiment": "leaderboard_robustness_audit",
        "status": "completed",
        "run_status": "completed",
        "verdict": "research_only",
        "locked_test": "not_opened",
        "locked_test_status": "not_opened",
        "scope": "validation_artifact_leaderboard_robustness_slice",
        "global_contract": global_contract,
        "leaderboard_rule_count": len(LEADERBOARD_RULES),
        "leaderboard_rules": [asdict(rule) | {"rule_id": rule.rule_id} for rule in LEADERBOARD_RULES],
        "input_artifacts": input_artifacts,
        "source_input_artifact_hashes": artifact.get("input_artifact_hashes"),
        "scale_contract": source_scale_contract(artifact),
        "source_search_budget": {
            "ranked_configs": 243,
            "executed_jobs": artifact.get("n_total_executed_configs"),
            "diagnostic_configs": artifact.get("diagnostic_budget", {}).get("listed_diagnostic_configs"),
        },
        "allowed_max_verdict": "research_only",
        "forbidden_interpretations": ["candidate", "tradable", "live_ready", "production", "permission_to_open_locked_test", "new_winner"],
        **limitation_statuses,
        "decisions_by_rule": decisions,
        **overall,
        "artifacts": {name: str(path) for name, path in artifacts.items()},
    }
    output_prefix.with_suffix(".json").write_text(json.dumps(result, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    return result


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit robustness of fixed normalized rich-entry leaderboard rows.")
    parser.add_argument("--input-prefix", default=str(DEFAULT_INPUT_PREFIX))
    parser.add_argument("--output-prefix", default=str(DEFAULT_OUTPUT_PREFIX))
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    result = run_audit(Path(args.input_prefix), Path(args.output_prefix))
    print(json.dumps({"status": result["status"], "overall_decision": result.get("overall_decision"), "decision": result.get("decision")}, ensure_ascii=False))
    if result.get("status") == "UNKNOWN":
        sys.exit(1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_leaderboard_robustness_audit.py -q
```

Expected: PASS.

- [ ] **Step 5: Run CLI**

Run:

```bash
./.venv/bin/python ML/baseline/audit_leaderboard_robustness.py \
  --input-prefix ML/reports/fractal0_rich_entry_quality_normalized \
  --output-prefix ML/reports/leaderboard_robustness_audit
```

Expected: exit code `0`, printed JSON with `status=completed` and `overall_decision=LEADERBOARD_ROBUSTNESS_INCOMPLETE_NEEDS_COST_TIME_CHECKS`.

---

### Task 6: Add Module Documentation

**Methodology:** `16-reporting-audit.md`.

**Mandatory Checks:**
- Docs list command, inputs, outputs, limitations and allowed verdict.
- Docs say this script does not choose a new winner.
- Docs say `locked_test` remains closed.

**Completion Criterion:** `docs/ML/audit_leaderboard_robustness.py.md` exists and is linked from `MODULE_INDEX.md`.

**Files:**
- Create: `docs/ML/audit_leaderboard_robustness.py.md`
- Modify: `MODULE_INDEX.md`
- Modify: `docs/ML/benchmark_fractal0_entry_quality_filter.py.md`

**Interfaces:**
- Consumes: CLI and artifact names from Task 5.
- Produces: module-level documentation for future agents.

- [ ] **Step 1: Create module docs**

Create `docs/ML/audit_leaderboard_robustness.py.md`:

```md
# audit_leaderboard_robustness.py

## Назначение

Validation-slice audit для 11 fixed audit input rows из normalized rich-entry leaderboard.
Скрипт читает saved artifacts, не обучает модель, не выбирает новый winner и
не открывает `locked_test`.

## Команда

```bash
./.venv/bin/python ML/baseline/audit_leaderboard_robustness.py \
  --input-prefix ML/reports/fractal0_rich_entry_quality_normalized \
  --output-prefix ML/reports/leaderboard_robustness_audit
```

## Входы

- `ML/reports/fractal0_rich_entry_quality_normalized.json`
- `ML/reports/fractal0_rich_entry_quality_normalized_summary.csv`
- `ML/reports/fractal0_rich_entry_quality_normalized_trades.csv`
- `ML/reports/fractal0_rich_entry_quality_normalized_scores.csv`

## Выходы

- `ML/reports/leaderboard_robustness_audit.json`
- `ML/reports/leaderboard_robustness_audit_rules.csv`
- `ML/reports/leaderboard_robustness_audit_summary.csv`
- `ML/reports/leaderboard_robustness_audit_yearly.csv`
- `ML/reports/leaderboard_robustness_audit_quarterly.csv`
- `ML/reports/leaderboard_robustness_audit_side.csv`
- `ML/reports/leaderboard_robustness_audit_year_side.csv`
- `ML/reports/leaderboard_robustness_audit_score_shift.csv`
- `ML/reports/leaderboard_robustness_audit_stricter_cutoff.csv`
- `ML/reports/leaderboard_robustness_audit_topk_sensitivity.csv`
- `ML/reports/leaderboard_robustness_audit_calendar_slices.csv`
- `ML/reports/leaderboard_robustness_audit_missing_diagnostics.csv`
- `ML/reports/leaderboard_robustness_audit_classification.csv`

## Ограничения

- `locked_test=not_opened`.
- `scope=validation_artifact_leaderboard_robustness_slice`.
- `allowed_max_verdict=research_only`.
- `multi_seed_status=NOT_RUN`.
- `provider_drift_status=NOT_RUN`.
- `transfer_status=NOT_RUN`.
- Stress-cost resimulation, timezone-shift rescore and model-level calendar
  permutation importance are not computed from saved filtered artifacts unless
  a later implementation adds an explicitly frozen resimulation/rescore path.
- The script preserves `original_rank` and never selects a new winner.
```

- [ ] **Step 2: Update `MODULE_INDEX.md`**

Use `rg -n "audit_time_only_robustness|benchmark_fractal0_entry_quality_filter" MODULE_INDEX.md`, then add a row near related ML baseline entries:

```md
| [audit_leaderboard_robustness.py](ML/baseline/audit_leaderboard_robustness.py) | Validation-slice audit 11 fixed normalized rich-entry leaderboard input rows без нового поиска и без `locked_test` | normalized rich-entry JSON/CSV → `leaderboard_robustness_audit*` JSON/CSV | [docs](docs/ML/audit_leaderboard_robustness.py.md) | ✅ |
```

- [ ] **Step 3: Update benchmark module docs cross-link**

In `docs/ML/benchmark_fractal0_entry_quality_filter.py.md`, add a short section near the existing robustness-audit note:

```md
## Leaderboard Robustness Audit

`ML/baseline/audit_leaderboard_robustness.py` checks the 11 fixed audit input rows from
the normalized `Candidate Shortlist / Leaderboard`. It does not retrain, does
not select a new winner and does not open `locked_test`.
```

- [ ] **Step 4: Verify docs references**

Run:

```bash
rg -n "audit_leaderboard_robustness|leaderboard_robustness_audit" docs/ML MODULE_INDEX.md
```

Expected: hits in `docs/ML/audit_leaderboard_robustness.py.md`, `docs/ML/benchmark_fractal0_entry_quality_filter.py.md`, and `MODULE_INDEX.md`.

---

### Task 7: Run Verification And Write Stage Report

**Methodology:** `16-reporting-audit.md`, `A4-verdicts-stop-conditions.md`.

**Mandatory Checks:**
- Report contains all required reporting sections.
- Report includes research-first disclosure and current/cumulative search budget.
- Report includes split roles and sample-size gate.
- Report includes input artifact hashes and generated artifact paths.
- Report states no trading/candidate/locked-test conclusion.
- Key report numbers are copied from JSON/CSV and verified by command.

**Completion Criterion:** Report exists, references generated artifacts, and its key numbers match JSON/CSV.

**Files:**
- Create: `docs/reports/2026-07-23-fractal0-rich-entry-leaderboard-robustness-audit.md`

**Interfaces:**
- Consumes: artifacts from Task 5.
- Produces: canonical stage report.

- [ ] **Step 1: Run all verification commands**

Run:

```bash
./.venv/bin/python -m pytest tests/test_leaderboard_robustness_audit.py -q
./.venv/bin/python ML/baseline/audit_leaderboard_robustness.py --input-prefix ML/reports/fractal0_rich_entry_quality_normalized --output-prefix ML/reports/leaderboard_robustness_audit
./.venv/bin/python -m pytest tests/ -q
```

Expected:

- targeted test file passes;
- CLI exits `0`;
- full test suite exits `0`.

- [ ] **Step 2: Extract report numbers from artifacts**

Run:

```bash
./.venv/bin/python - <<'PY'
import json
import pandas as pd

data = json.loads(open("ML/reports/leaderboard_robustness_audit.json", encoding="utf-8").read())
summary = pd.read_csv(
    "ML/reports/leaderboard_robustness_audit_summary.csv",
    sep=";",
    usecols=["original_rank", "rule_id", "n_trades", "pf", "sequential_block_bs_p05"],
)
classification = pd.read_csv(
    "ML/reports/leaderboard_robustness_audit_classification.csv",
    sep=";",
    usecols=["decision", "interpretation"],
)
print("status:", data["status"])
print("verdict:", data["verdict"])
print("locked_test:", data["locked_test"])
print("rule_count:", data["leaderboard_rule_count"])
print("overall_decision:", data["overall_decision"])
print("scale_contract:", data["scale_contract"]["status"])
print("decisions:", classification["decision"].value_counts().to_dict())
print("interpretations:", classification["interpretation"].value_counts().to_dict())
print("anchor:", summary.loc[summary["original_rank"].eq(1), ["rule_id", "n_trades", "pf", "sequential_block_bs_p05"]].to_dict(orient="records")[0])
PY
```

Expected: `rule_count=11`, `locked_test=not_opened`, `verdict=research_only`, `scale_contract=DIAGNOSTIC_ONLY` when the final normalized feature distribution audit contains accepted `WARNING` rows.

- [ ] **Step 3: Write report**

Create `docs/reports/2026-07-23-fractal0-rich-entry-leaderboard-robustness-audit.md` with:

```md
# Fractal0 Rich Entry Leaderboard Robustness Audit

> **Дата**: 2026-07-23
> **Статус**: Completed
> **Вердикт**: research_only
> **Цель**: Проверить validation-slice устойчивость 11 fixed normalized rich-entry leaderboard input rows без нового поиска и без открытия `locked_test`.
> **Related plan/spec**: `docs/superpowers/plans/2026-07-23-fractal0-rich-entry-leaderboard-robustness-audit.md`

## Context

Audit covers the 11 rows from `Candidate Shortlist / Leaderboard` in
`docs/reports/2026-07-22-fractal0-rich-entry-quality-normalized-rerun.md`.
The original rank is preserved. No new winner is selected.

## Уровень Этапа

Research-only validation artifact audit.
`scope=validation_artifact_leaderboard_robustness_slice`.

```text
lifecycle_status: research_only
origin_bias: normalized rich-entry validation leaderboard selected after broad search
research_priority: compare robustness profiles before deciding whether regime reformulation or a narrower additive probe is justified
current_search_budget: no new search, 11 fixed audit input rows
cumulative_search_budget: inherited from normalized rich-entry search, 243 ranked configs plus diagnostic controls
next_probe_freeze: not created in this stage
allowed_max_verdict: research_only
forbidden_interpretations: candidate, tradable, live_ready, production, permission_to_open_locked_test, new_winner
```

## What Was Done

- Added `ML/baseline/audit_leaderboard_robustness.py`.
- Added `tests/test_leaderboard_robustness_audit.py`.
- Recomputed per-rule validation-slice robustness diagnostics.
- Preserved original leaderboard order and did not select a new winner.
- Wrote `ML/reports/leaderboard_robustness_audit*` artifacts.

## Multiple Testing Context

This audit inherits origin bias from the normalized rich-entry validation search.
The 11 rows were already chosen by a practical `val_eval` screen. Metrics below
are diagnostics only and do not authorize `locked_test`.

## Scale Contract / Normalization Disclosure

Use `scale_contract` from `ML/reports/leaderboard_robustness_audit.json` and
the source normalized artifact. The section must include:

- `normalization_config.mode`.
- `normalization_config.fit_split=train_core`.
- `normalization_config_json`.
- `normalized_feature_distribution_audit_csv`.
- `scale_contract.status`.
- Each `WARNING` or `ERROR` flag and the action taken: block, fix, rerun or
  accept-as-warning.
- Confirmation that `locked_test` was not used to choose normalization, scaler,
  clipping or transformations.

If `scale_contract.status=FAIL`, report status must be `Blocked` and final
stage sync must not run. If `scale_contract.status=DIAGNOSTIC_ONLY`, keep the
stage verdict `research_only` and explicitly state that preprocessing risk
blocks a stronger interpretation.

## Changed Files

Build this section from actual file changes after execution:

```bash
git status --short
git diff --name-only
```

Include generated `ML/reports/leaderboard_robustness_audit*.json/csv` artifacts.
Include `CHANGELOG.md`, wiki files, roadmap and handoff only if final stage sync
actually ran and those files changed.

## Verification

Record the three verification commands from Task 7 Step 1 and their observed
terminal outcomes. The report must include the targeted pytest result, CLI exit
status and full pytest result. If any command fails, set report status to
`Blocked`, keep the generated artifacts that explain the failure, and do not
perform final stage sync.

## Results

Use only values printed by Task 7 Step 2 or values read directly from generated
CSV artifacts. Include:

- JSON status, verdict, locked-test status, rule count and overall decision.
- Classification decision counts and interpretation counts.
- Anchor row rank 1 metrics: `rule_id`, `n_trades`, `pf`,
  `sequential_block_bs_p05`.
- Per-rule classification table with `original_rank`, `rule_id`, `decision`,
  `interpretation`, `reasons`, `disclosures`.
- Any side, stricter-cutoff or missing-diagnostic row that changes the
  interpretation of a rule.

```text
allowed_max_verdict=research_only
not_trading_evidence_reason=validation artifact leaderboard slice, locked_test not opened, inherited broad-search origin bias
forbidden_interpretations=candidate/tradable/live_ready/production/permission_to_open_locked_test/new_winner
```

## Conclusions

State conclusions using this rule:

- If all 11 rows are `time_only` or `movement_plus_time`, say that the checked
  leaderboard remains time-heavy.
- If no non-time profile exists in the checked 11 rows, say that this audit
  cannot establish standalone fractal/additive non-time evidence.
- If cost stress, timezone shift, calendar permutation, multi-seed, provider
  drift or transfer checks remain unavailable, say that stronger interpretation
  is blocked by those missing checks.
- Do not state that a new winner was selected.

## Limitations / Open Questions

- `multi_seed_status=NOT_RUN`.
- `provider_drift_status=NOT_RUN`.
- `transfer_status=NOT_RUN`.
- `locked_test_status=not_opened`.
- `stress_costs_status=NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS`.
- `timezone_shift_status=NOT_RUN` for time-heavy profiles unless implemented.
- `calendar_permutation_importance_status=NOT_RUN` unless implemented.
- `sequential_position_constraint_status=NOT_RUN`.

## Split Disclosure

Include split dates and row counts from
`docs/reports/2026-07-22-fractal0-rich-entry-quality-normalized-rerun.md` and
the generated `leaderboard_robustness_audit_summary.csv`. The section must name
`train_core`, `val_select`, `val_eval`, `locked_test` roles and the
sample-size gate after filters. Do not infer missing split values; if the value
is not present in the source report or generated artifacts, mark that field
`UNKNOWN_IN_SOURCE_ARTIFACTS`.

## Next Step

Set exactly one next step using the decision rule from Task 8:

- write a bounded stress-cost/time-calendar/sequential-position robustness closure plan;
- write a regime-filter reformulation plan;
- write a narrow additive non-time probe plan;
- close the rich/fractal entry-quality branch as superseded.

## Related Materials

- `docs/reports/2026-07-22-fractal0-rich-entry-quality-normalized-rerun.md`
- `docs/reports/2026-07-23-time-only-robustness-audit.md`
- `ML/reports/leaderboard_robustness_audit.json`
- `docs/ML/audit_leaderboard_robustness.py.md`
```

- [ ] **Step 4: Verify report numbers against artifacts**

Run:

```bash
./.venv/bin/python - <<'PY'
import json
import re
from pathlib import Path

report = Path("docs/reports/2026-07-23-fractal0-rich-entry-leaderboard-robustness-audit.md").read_text(encoding="utf-8")
data = json.loads(Path("ML/reports/leaderboard_robustness_audit.json").read_text(encoding="utf-8"))
assert "research_only" in report
assert "permission_to_open_locked_test" in report
assert data["locked_test"] == "not_opened"
assert str(data["leaderboard_rule_count"]) in report
assert data["overall_decision"] in report
assert data["scale_contract"]["status"] in report
assert not re.search(r"\bnew winner\b.*selected", report, flags=re.IGNORECASE)
print("report artifact consistency PASS")
PY
```

Expected: `report artifact consistency PASS`.

---

### Task 8: Final Stage Sync

**Methodology:** `16-reporting-audit.md`, project `stage-reporting` skill.

**Mandatory Checks:**
- `CHANGELOG.md`, `CONTEXT_HANDOFF.md`, roadmap and wiki reflect the same next step.
- `roadmap.md` has exactly one `ACTIVE` track.
- `locked_test` remains closed everywhere.

**Completion Criterion:** Handoff points to the generated report, artifacts and next action; docs search finds no stale next-step conflict.

**Files:**
- Modify: `docs/superpowers/roadmap.md`
- Modify: `CONTEXT_HANDOFF.md`
- Modify: `CHANGELOG.md`
- Modify: `wiki/research/fractal-stop-research.md`
- Modify: `wiki/index.md`
- Modify: `wiki/log.md`
- Modify: `wiki/REPO_integrity.md`

**Interfaces:**
- Consumes: report and artifacts from Task 7.
- Produces: synchronized project handoff.

- [ ] **Step 1: Update roadmap**

First read the current next-step sources:

```bash
rg -n "ACTIVE|Next Step|Regime filter|leaderboard_robustness" docs/superpowers/roadmap.md CONTEXT_HANDOFF.md
```

Use this decision rule:

```text
If classification contains only time-heavy rules with missing stress/time checks:
  ACTIVE = stress-cost/time-calendar/sequential-position robustness closure or regime filter reformulation.
If at least one non-time/additive rule survives materially better than its time-only comparator:
  ACTIVE = narrow additive non-time probe plan, without locked_test.
If all non-time/additive evidence is weak and time-heavy explanation remains dominant:
  ACTIVE = close rich/fractal entry-quality branch or regime-filter reformulation.
```

Ensure `docs/superpowers/roadmap.md` contains exactly one `ACTIVE` heading.
If the current `ACTIVE` remains correct, keep its title and add the leaderboard
audit as supporting evidence. If the current `ACTIVE` changes, record the
supersede reason in the report, roadmap and `CONTEXT_HANDOFF.md` using the same
wording.

- [ ] **Step 2: Update handoff**

Set `CONTEXT_HANDOFF.md` to include:

```md
Current completed stage:
- report: `docs/reports/2026-07-23-fractal0-rich-entry-leaderboard-robustness-audit.md`
- script: `ML/baseline/audit_leaderboard_robustness.py`
- artifacts: `ML/reports/leaderboard_robustness_audit*`

Decision: value from `ML/reports/leaderboard_robustness_audit.json` key `overall_decision`.
Verdict: `research_only`.
locked_test: `not_opened`.
Next step: exact `ACTIVE` branch title from `docs/superpowers/roadmap.md`.
```

- [ ] **Step 3: Update changelog and wiki**

Add a top entry to `CHANGELOG.md` and update wiki research/index/log using `stage-reporting`. The changelog entry must include:

```md
- **summary**: Added validation-slice robustness audit for 11 fixed normalized rich-entry leaderboard input rows without new search and without opening `locked_test`.
- **decision**: value from `ML/reports/leaderboard_robustness_audit.json` key `overall_decision`.
- **notes**: `verdict=research_only`; no new winner selected; `locked_test=not_opened`; missing stress/time/provider/multi-seed checks disclosed.
```

- [ ] **Step 4: Final verification**

Run:

```bash
rg -n "leaderboard_robustness_audit|fractal0-rich-entry-leaderboard-robustness-audit|locked_test=not_opened|new winner" \
  docs/reports/2026-07-23-fractal0-rich-entry-leaderboard-robustness-audit.md \
  docs/ML/audit_leaderboard_robustness.py.md \
  docs/superpowers/roadmap.md \
  CONTEXT_HANDOFF.md \
  CHANGELOG.md \
  MODULE_INDEX.md
./.venv/bin/python -m pytest tests/ -q
```

Expected:

- `rg` shows consistent paths and no statement that a new winner was selected.
- Full tests pass.

---

## Self-Review Checklist

- Spec coverage: covers 11 fixed audit input leaderboard rows, no new search, no new winner, no `locked_test`, per-rule robustness diagnostics, missing stress/time disclosures, documentation and stage sync.
- Completeness scan: the plan must not contain unfinished template markers or instructions that require guessing missing implementation details.
- Type consistency: `RuleSpec`, `LEADERBOARD_RULES`, `fixed_rule_from_contract_row`, `audit_one_rule`, `rule_decision`, `build_classification`, and `run_audit` use the same `rule_id` / `original_rank` contract across tasks.
- Methodology coverage: each task lists applicable methodology, mandatory checks and completion criterion.
