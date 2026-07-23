# Fractal0 Leaderboard Cost Calendar Sequential Multiseed Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Закрыть те внутренние robustness-блокеры для 11 fixed normalized rich-entry leaderboard rows, которые честно вычислимы из текущих artifacts, и явно вывести отдельные follow-up планы для stress-cost, timezone или multi-seed, если их нельзя закрыть без producer-level rerun; новый поиск и `locked_test` запрещены.

**Architecture:** Расширить текущий saved-artifact audit отдельным closure/disclosure-скриптом, который переиспользует fixed 11-rule manifest из `ML/baseline/audit_leaderboard_robustness.py`, сохраняет contract-first JSON/CSV artifacts и никогда не меняет порядок `original_rank`. Sequential-position считается по реальному интервалу позиции `[fill_time, exit_time]`; stress-cost, timezone-shift, calendar permutation и multi-seed либо вычисляются честно, либо получают явный blocking status и отдельный next-plan decision без имитации проверки.

**Tech Stack:** Python через `./.venv/bin/python`, pandas, numpy, pytest, существующие helpers из `ML/baseline/audit_leaderboard_robustness.py`, `ML/baseline/audit_time_only_robustness.py`, `ML/baseline/benchmark_fractal0_entry_quality_filter.py` и `ML/baseline/benchmark_fractal0_entry_exit_grid.py`; новых зависимостей не добавлять.

## Global Constraints

- Работать на текущей feature-ветке; worktree не создавать.
- Использовать только `./.venv/bin/python`.
- CSV читать с `sep=";"` и только через `usecols` / `chunksize` / `nrows`; не загружать большие CSV без нужных колонок.
- `locked_test` не открывать. Все successful artifacts должны содержать `locked_test=not_opened` и `locked_test_status=not_opened`.
- Не запускать новый leaderboard search: не добавлять profiles, targets, models, filters, cutoff, instruments, model families или selection metrics.
- Не выбирать нового winner по результатам этого closure.
- Тестировать ровно 11 строк из `audit_leaderboard_robustness.LEADERBOARD_RULES` с сохранением `original_rank`.
- Fixed execution contract: `S2_fractal0_buffer_0_5_entry_floor_2 / E3_open_pullback_1_0atr / M0_no_mask / X2_ml_opposite_any_p0_50 / canonical_spread=0.2 / entry_filter_score_col=rich_entry_score`.
- `score_cutoff_on_val_select` для каждой строки берётся только из saved `val_select` summary row.
- Maximum verdict: `research_only`.
- Запрещённые интерпретации: `candidate`, `tradable`, `live_ready`, `production`, `permission_to_open_locked_test`, `new_winner`.
- Scope: `validation_artifact_leaderboard_cost_calendar_sequential_multiseed_closure`.
- Provider drift и transfer не входят в этот план: `provider_drift_status=NOT_IN_SCOPE`, `transfer_status=NOT_IN_SCOPE`.
- Multi-seed входит в этот план, но только для тех же 11 fixed rule families; если persisted seed artifacts отсутствуют и rerun невозможен без расширения search space, записать `multi_seed_status=NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS`.
- Если любой input artifact имеет `locked_test != not_opened` или `feature_contract_variant != normalized_atr_unit`, записать JSON со статусом `UNKNOWN`, decision `UNKNOWN_ARTIFACT_CONTRACT` и завершить CLI с кодом `1`.
- Если любая из 11 fixed input rows отсутствует в saved summary, записать JSON со статусом `UNKNOWN`, decision `UNKNOWN_LEADERBOARD_CONTRACT` и завершить CLI с кодом `1`.
- Если stress-cost, timezone-shift, sequential-position или multi-seed не могут быть честно вычислены из доступных artifacts, записывать `NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS` / `NOT_RUN`, а не имитировать проверку.
- После Python-изменений запускать `./.venv/bin/python -m pytest tests/ -q`.
- Для финальной синхронизации report / `CHANGELOG.md` / `CONTEXT_HANDOFF.md` / wiki использовать skill `stage-reporting`.

---

## Roadmap Metadata

```text
depends_on:
  - docs/reports/2026-07-22-fractal0-rich-entry-quality-normalized-rerun.md
  - docs/reports/2026-07-23-time-only-robustness-audit.md
  - docs/reports/2026-07-23-fractal0-rich-entry-leaderboard-robustness-audit.md
  - docs/superpowers/roadmap.md ACTIVE: Regime filter reformulation
blocks:
  - locked_test discussion
  - shortlist/freeze discussion
  - rich/fractal branch close decision
supersedes:
  - none; this plan closes/discloses blockers left by leaderboard robustness audit
exit_decisions:
  - continue regime-filter reformulation
  - write explicit producer-level stress-cost resimulation plan
  - write explicit frozen timezone-rescore plan
  - write bounded multi-seed rerun plan for exactly the 11 fixed rule families
  - close rich/fractal entry-quality branch as time-heavy research-only
locked_test_policy:
  - not_opened
```

## Methodology Map

- `docs/methodology/00-research-management.md`: research-only уровень, fixed scope, запрет post-hoc повышения до candidate.
- `docs/methodology/06-temporal-split.md`: роли `train_core`, `val_select`, `val_eval`, `locked_test`; sample-size gate после фильтров.
- `docs/methodology/09-validation-freeze.md`: сохранённые правила, cutoff, execution contract, множественный поиск и запрет нового winner.
- `docs/methodology/11-robustness.md`: yearly/quarterly/side/year-side, block bootstrap, calendar/time diagnostics, multi-seed disclosure.
- `docs/methodology/12-backtest-costs.md`: stress grid по spread/costs, sequential simulation, price convention disclosure.
- `docs/methodology/16-reporting-audit.md`: structured artifact, report sections, commands, hashes, split disclosure, limitations.
- `docs/methodology/A4-verdicts-stop-conditions.md`: maximum verdict `research_only`, stop conditions, forbidden interpretations.

## Fixed Audit Input Rows

Use `ML.baseline.audit_leaderboard_robustness.LEADERBOARD_RULES` as the single source of truth. The plan covers ranks 1-11 exactly:

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

## File Structure

- Create: `ML/baseline/audit_leaderboard_closure.py`
  - Verifies normalized artifact contract and 11-row leaderboard contract.
  - Computes stress-cost feasibility/results, time-calendar diagnostics, timezone-shift feasibility, sequential-position diagnostics and multi-seed diagnostics.
  - Writes `ML/reports/leaderboard_closure_audit*` JSON/CSV artifacts.
- Create: `tests/test_leaderboard_closure_audit.py`
  - Unit tests for fixed manifest reuse, stress-cost math/statuses, calendar diagnostics, sequential-position simulation, multi-seed status and no re-ranking.
- Create after run: `docs/ML/audit_leaderboard_closure.py.md`
  - Module docs for command, inputs, outputs and limitations.
- Create after run: `docs/reports/2026-07-23-fractal0-leaderboard-cost-calendar-sequential-multiseed-closure.md`
  - Human report with research-only conclusion.
- Modify after run: `docs/superpowers/roadmap.md`
  - Keep exactly one `ACTIVE` track and record closure result.
- Modify after run: `CONTEXT_HANDOFF.md`
  - Short current baton pass.
- Modify after run: `CHANGELOG.md`, `wiki/research/fractal-stop-research.md`, `wiki/index.md`, `wiki/log.md`, `wiki/REPO_integrity.md`.
- Modify after run: `MODULE_INDEX.md`, `docs/ML/audit_leaderboard_robustness.py.md`.

New artifacts:

- `ML/reports/leaderboard_closure_audit.json`
- `ML/reports/leaderboard_closure_audit_rules.csv`
- `ML/reports/leaderboard_closure_audit_stress_cost.csv`
- `ML/reports/leaderboard_closure_audit_calendar.csv`
- `ML/reports/leaderboard_closure_audit_calendar_permutation_importance.csv`
- `ML/reports/leaderboard_closure_audit_calendar_no_ml_baselines.csv`
- `ML/reports/leaderboard_closure_audit_timezone_shift.csv`
- `ML/reports/leaderboard_closure_audit_sequential_positions.csv`
- `ML/reports/leaderboard_closure_audit_multiseed.csv`
- `ML/reports/leaderboard_closure_audit_classification.csv`

---

### Task 1: Reuse Fixed Leaderboard Manifest And Contract Guard

**Files:**
- Create: `tests/test_leaderboard_closure_audit.py`
- Create: `ML/baseline/audit_leaderboard_closure.py`

**Interfaces:**
- Consumes: `audit_leaderboard_robustness.LEADERBOARD_RULES`, `verify_global_artifact_contract`, `verify_leaderboard_contract`, `load_normalized_artifacts`.
- Produces:
  - `CLOSURE_SCOPE = "validation_artifact_leaderboard_cost_calendar_sequential_multiseed_closure"`.
  - `CLOSURE_OUTPUT_PREFIX = Path("ML/reports/leaderboard_closure_audit")`.
  - `verify_closure_inputs(input_prefix: Path) -> dict[str, object]`.

- [ ] **Step 1: Write failing tests**

Create `tests/test_leaderboard_closure_audit.py`:

```python
from pathlib import Path

import pandas as pd

from ML.baseline import audit_leaderboard_closure as closure
from ML.baseline import audit_leaderboard_robustness as leaderboard


def test_closure_reuses_exact_11_leaderboard_rules():
    assert closure.LEADERBOARD_RULES is leaderboard.LEADERBOARD_RULES
    assert len(closure.LEADERBOARD_RULES) == 11
    assert [rule.original_rank for rule in closure.LEADERBOARD_RULES] == list(range(1, 12))
    assert closure.CLOSURE_SCOPE == "validation_artifact_leaderboard_cost_calendar_sequential_multiseed_closure"


def test_closure_global_statuses_exclude_provider_and_transfer():
    statuses = closure.default_closure_statuses()

    assert statuses["locked_test_status"] == "not_opened"
    assert statuses["provider_drift_status"] == "NOT_IN_SCOPE"
    assert statuses["transfer_status"] == "NOT_IN_SCOPE"
    assert statuses["allowed_max_verdict"] == "research_only"


def test_contract_result_preserves_original_rank_order():
    rows = []
    for rule in leaderboard.LEADERBOARD_RULES:
        for split in ["val_select", "val_eval"]:
            rows.append(
                {
                    "stop_policy_id": leaderboard.STOP_POLICY_ID,
                    "entry_id": leaderboard.ENTRY_ID,
                    "mask_id": leaderboard.MASK_ID,
                    "exit_id": leaderboard.EXIT_ID,
                    "spread": leaderboard.CANONICAL_SPREAD,
                    "split": split,
                    "profile_id": rule.profile_id,
                    "model_id": rule.model_id,
                    "target_id": rule.target_id,
                    "filter_id": rule.filter_id,
                    "entry_filter_score_col": leaderboard.ENTRY_FILTER_SCORE_COL,
                    "score_cutoff_on_val_select": -0.02,
                    "n_trades": 500,
                    "pf": 2.0,
                    "bs_p05": 1.5,
                    "eligible_for_winner": True,
                    "not_eligible_for_winner": False,
                    "not_eligible_reason": "",
                }
            )
    contract = closure.verify_leaderboard_contract(pd.DataFrame(rows), closure.LEADERBOARD_RULES)

    assert contract["original_rank"].tolist() == list(range(1, 12))
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
./.venv/bin/python -m pytest tests/test_leaderboard_closure_audit.py -q
```

Expected: FAIL because `ML.baseline.audit_leaderboard_closure` does not exist.

- [ ] **Step 3: Implement minimal closure scaffold**

Create `ML/baseline/audit_leaderboard_closure.py`:

```python
from __future__ import annotations

# =============================================================================
# Файл: audit_leaderboard_closure.py
# Назначение: Closure audit for 11 fixed normalized leaderboard rows.
# Обновлён: 2026-07-23
# Зависимости:
#   Входные данные:
#     - ML/reports/fractal0_rich_entry_quality_normalized.json/csv
#   Выходные данные:
#     - ML/reports/leaderboard_closure_audit*.json/csv
# Использование:
#   ./.venv/bin/python ML/baseline/audit_leaderboard_closure.py --input-prefix ML/reports/fractal0_rich_entry_quality_normalized --output-prefix ML/reports/leaderboard_closure_audit
# Примечания:
#   - locked_test не открывается; provider drift и transfer не входят в scope.
# =============================================================================

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ML.baseline import audit_leaderboard_robustness as leaderboard


DEFAULT_INPUT_PREFIX = leaderboard.DEFAULT_INPUT_PREFIX
CLOSURE_OUTPUT_PREFIX = Path("ML/reports/leaderboard_closure_audit")
CLOSURE_SCOPE = "validation_artifact_leaderboard_cost_calendar_sequential_multiseed_closure"
LEADERBOARD_RULES = leaderboard.LEADERBOARD_RULES
verify_leaderboard_contract = leaderboard.verify_leaderboard_contract


def default_closure_statuses() -> dict[str, object]:
    return {
        "locked_test_status": "not_opened",
        "stress_costs_status": "PENDING",
        "time_calendar_status": "PENDING",
        "timezone_shift_status": "PENDING",
        "sequential_position_constraint_status": "PENDING",
        "multi_seed_status": "PENDING",
        "provider_drift_status": "NOT_IN_SCOPE",
        "transfer_status": "NOT_IN_SCOPE",
        "allowed_max_verdict": "research_only",
    }


def verify_closure_inputs(input_prefix: Path = DEFAULT_INPUT_PREFIX) -> dict[str, object]:
    loaded = leaderboard.load_normalized_artifacts(input_prefix)
    global_contract = leaderboard.verify_global_artifact_contract(loaded["artifact"])
    rule_contract = leaderboard.verify_leaderboard_contract(loaded["summary"], LEADERBOARD_RULES)
    return {"loaded": loaded, "global_contract": global_contract, "rule_contract": rule_contract}
```

- [ ] **Step 4: Run tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_leaderboard_closure_audit.py -q
```

Expected: PASS for Task 1 tests.

---

### Task 2: Stress-Cost Feasibility And Conservative Cost Disclosure

**Files:**
- Modify: `ML/baseline/audit_leaderboard_closure.py`
- Modify: `tests/test_leaderboard_closure_audit.py`

**Interfaces:**
- Consumes: fixed `val_eval` trades for each `FixedRule`.
- Produces:
  - `stress_cost_grid_for_rule(trades: pd.DataFrame, contract_row: pd.Series | dict[str, object]) -> pd.DataFrame`.
  - `cost_model_disclosure_for_rule(contract_row: pd.Series | dict[str, object]) -> pd.DataFrame`.
  - Columns: `original_rank`, `rule_id`, `cost_component`, `spread`, `stress_multiplier`, `status`, `n_trades`, `pf`, `mean_pnl_r`, `max_drawdown_r`, `reason`.

- [ ] **Step 1: Add failing tests**

Append:

```python
def test_stress_cost_grid_marks_uncomputable_without_resimulation_path():
    contract_row = {"original_rank": 1, "rule_id": "rank01", "profile_id": "time_only"}
    trades = pd.DataFrame({"position_id": ["a"], "pnl_r": [1.0], "spread": [0.2], "entry_effective_price": [100.0], "exit_price": [101.0], "side": ["BUY"]})

    result = closure.stress_cost_grid_for_rule(trades, contract_row)

    assert set(result["stress_multiplier"]) == {1.0, 2.0, 3.0, 4.0}
    assert set(result["status"]) == {"PRODUCER_LEVEL_RESIMULATION_REQUIRED"}
    assert "requires explicit resimulation" in result["reason"].iloc[0]


def test_cost_model_disclosure_lists_non_spread_costs():
    result = closure.cost_model_disclosure_for_rule({"original_rank": 1, "rule_id": "rank01"})

    assert {"commission", "swap", "slippage", "requote_open_failure", "latency", "position_limits"}.issubset(set(result["cost_component"]))
    assert set(result.loc[result["cost_component"].ne("spread"), "status"]) == {"NOT_IN_SCOPE"}
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
./.venv/bin/python -m pytest tests/test_leaderboard_closure_audit.py::test_stress_cost_grid_marks_uncomputable_without_resimulation_path -q
```

Expected: FAIL because `stress_cost_grid_for_rule` is missing.

- [ ] **Step 3: Implement conservative stress-cost status**

Add:

```python
STRESS_MULTIPLIERS = (1.0, 2.0, 3.0, 4.0)
CANONICAL_SPREAD = leaderboard.CANONICAL_SPREAD


def stress_cost_grid_for_rule(trades: pd.DataFrame, contract_row: pd.Series | dict[str, object]) -> pd.DataFrame:
    row = contract_row.to_dict() if isinstance(contract_row, pd.Series) else dict(contract_row)
    required_price_columns = {"entry_effective_price", "exit_price", "protective_stop_price", "r_value", "fill_index", "side"}
    has_price_inputs = required_price_columns.issubset(set(trades.columns))
    records = []
    for multiplier in STRESS_MULTIPLIERS:
        spread = CANONICAL_SPREAD * multiplier
        if not has_price_inputs:
            records.append(
                {
                    "original_rank": int(row["original_rank"]),
                    "rule_id": str(row["rule_id"]),
                    "cost_component": "spread",
                    "spread": float(spread),
                    "stress_multiplier": float(multiplier),
                    "status": "NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS",
                    "n_trades": int(len(trades)),
                    "pf": None,
                    "mean_pnl_r": None,
                    "max_drawdown_r": None,
                    "reason": "saved filtered trades contain realized pnl only; stress spread requires explicit resimulation from producer execution artifacts",
                }
            )
            continue
        records.append(
            {
                "original_rank": int(row["original_rank"]),
                "rule_id": str(row["rule_id"]),
                "cost_component": "spread",
                "spread": float(spread),
                "stress_multiplier": float(multiplier),
                "status": "PRODUCER_LEVEL_RESIMULATION_REQUIRED",
                "n_trades": int(len(trades)),
                "pf": None,
                "mean_pnl_r": None,
                "max_drawdown_r": None,
                "reason": "price columns exist, but honest spread stress requires explicit resimulation because spread can change fill/no-fill, SL trigger and exit path",
            }
        )
    return pd.DataFrame(records)


def cost_model_disclosure_for_rule(contract_row: pd.Series | dict[str, object]) -> pd.DataFrame:
    row = contract_row.to_dict() if isinstance(contract_row, pd.Series) else dict(contract_row)
    records = []
    for component in ["commission", "swap", "slippage", "requote_open_failure", "latency", "next_bar_entry", "position_limits"]:
        records.append(
            {
                "original_rank": int(row["original_rank"]),
                "rule_id": str(row["rule_id"]),
                "cost_component": component,
                "status": "NOT_IN_SCOPE",
                "reason": "this closure records non-spread cost disclosure; concrete values require a separate execution-cost model source",
            }
        )
    return pd.DataFrame(records)
```

- [ ] **Step 4: Run tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_leaderboard_closure_audit.py -q
```

Expected: PASS.

---

### Task 3: Time-Calendar Robustness For All 11 Rows

**Files:**
- Modify: `ML/baseline/audit_leaderboard_closure.py`
- Modify: `tests/test_leaderboard_closure_audit.py`

**Interfaces:**
- Consumes: fixed `val_eval` trades.
- Produces:
  - `time_calendar_for_rule(trades: pd.DataFrame, contract_row: pd.Series | dict[str, object]) -> pd.DataFrame`.
  - `calendar_permutation_importance_for_rule(artifact: dict[str, object], contract_row: pd.Series | dict[str, object]) -> pd.DataFrame`.
  - `calendar_no_ml_baseline_for_rule(trades: pd.DataFrame, contract_row: pd.Series | dict[str, object]) -> pd.DataFrame`.
  - Time bases: `signal_time`, `fill_time`, `exit_time`.
  - Calendar fields: `year`, `quarter`, `month`, `weekday`, `hour`.

- [ ] **Step 1: Add failing tests**

Append:

```python
def test_time_calendar_for_rule_covers_signal_fill_exit_and_hour_month():
    contract_row = {"original_rank": 1, "rule_id": "rank01"}
    trades = pd.DataFrame(
        [
            {"signal_time": "2021-01-01 02:00", "fill_time": "2021-01-01 03:00", "exit_time": "2021-01-02 04:00", "pnl_r": 1.0},
            {"signal_time": "2021-02-01 02:00", "fill_time": "2021-02-01 03:00", "exit_time": "2021-02-02 04:00", "pnl_r": -0.5},
        ]
    )

    result = closure.time_calendar_for_rule(trades, contract_row)

    assert {"signal_time", "fill_time", "exit_time"}.issubset(set(result["time_basis"]))
    assert {"month", "weekday", "hour"}.issubset(set(result["calendar_field"]))
    assert set(result["rule_id"]) == {"rank01"}


def test_calendar_permutation_importance_is_explicitly_uncomputable_without_fitted_estimator():
    result = closure.calendar_permutation_importance_for_rule({}, {"original_rank": 1, "rule_id": "rank01"})

    assert result["status"].tolist() == ["NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS"]
    assert "fitted estimator" in result["reason"].iloc[0]
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
./.venv/bin/python -m pytest tests/test_leaderboard_closure_audit.py::test_time_calendar_for_rule_covers_signal_fill_exit_and_hour_month -q
```

Expected: FAIL because `time_calendar_for_rule` is missing.

- [ ] **Step 3: Implement calendar diagnostics**

Add:

```python
from ML.baseline import benchmark_fractal0_entry_exit_grid as entry_exit


def _calendar_values(frame: pd.DataFrame, time_column: str) -> pd.DataFrame:
    out = frame.copy()
    dt = pd.to_datetime(out[time_column], errors="coerce")
    out["_year"] = dt.dt.year
    out["_quarter"] = dt.dt.to_period("Q").astype(str)
    out["_month"] = dt.dt.month
    out["_weekday"] = dt.dt.weekday
    out["_hour"] = dt.dt.hour
    return out


def time_calendar_for_rule(trades: pd.DataFrame, contract_row: pd.Series | dict[str, object]) -> pd.DataFrame:
    row = contract_row.to_dict() if isinstance(contract_row, pd.Series) else dict(contract_row)
    records = []
    for time_basis in ["signal_time", "fill_time", "exit_time"]:
        if time_basis not in trades.columns:
            records.append(
                {
                    "original_rank": int(row["original_rank"]),
                    "rule_id": str(row["rule_id"]),
                    "time_basis": time_basis,
                    "calendar_field": "missing",
                    "calendar_value": None,
                    "status": "NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS",
                    "reason": f"{time_basis} missing from saved trades",
                }
            )
            continue
        frame = _calendar_values(trades, time_basis)
        for field in ["year", "quarter", "month", "weekday", "hour"]:
            column = f"_{field}"
            for value, group in frame.groupby(column, dropna=False):
                records.append(
                    {
                        "original_rank": int(row["original_rank"]),
                        "rule_id": str(row["rule_id"]),
                        "time_basis": time_basis,
                        "calendar_field": field,
                        "calendar_value": str(value),
                        "status": "COMPUTED",
                        **entry_exit.compute_trade_metrics(group),
                    }
                )
    return pd.DataFrame(records)


def calendar_permutation_importance_for_rule(artifact: dict[str, object], contract_row: pd.Series | dict[str, object]) -> pd.DataFrame:
    row = contract_row.to_dict() if isinstance(contract_row, pd.Series) else dict(contract_row)
    return pd.DataFrame(
        [
            {
                "original_rank": int(row["original_rank"]),
                "rule_id": str(row["rule_id"]),
                "diagnostic": "calendar_permutation_importance",
                "status": "NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS",
                "reason": "fitted estimator and frozen rescore path are not persisted in saved normalized artifacts",
            }
        ]
    )


def calendar_no_ml_baseline_for_rule(trades: pd.DataFrame, contract_row: pd.Series | dict[str, object]) -> pd.DataFrame:
    row = contract_row.to_dict() if isinstance(contract_row, pd.Series) else dict(contract_row)
    return pd.DataFrame(
        [
            {
                "original_rank": int(row["original_rank"]),
                "rule_id": str(row["rule_id"]),
                "diagnostic": "calendar_no_ml_baseline",
                "status": "NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS",
                "reason": "saved filtered leaderboard trades do not include unfiltered no-ML calendar baseline rows",
                "rows_available": int(len(trades)),
            }
        ]
    )
```

- [ ] **Step 4: Run tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_leaderboard_closure_audit.py -q
```

Expected: PASS.

---

### Task 4: Timezone-Shift Feasibility Guard

**Files:**
- Modify: `ML/baseline/audit_leaderboard_closure.py`
- Modify: `tests/test_leaderboard_closure_audit.py`

**Interfaces:**
- Produces:
  - `timezone_shift_for_rule(scores: pd.DataFrame, contract_row: pd.Series | dict[str, object]) -> pd.DataFrame`.
  - Fixed shifts: `[-8, -4, 4, 8]`.

- [ ] **Step 1: Add failing tests**

Append:

```python
def test_timezone_shift_is_not_faked_from_saved_scores():
    result = closure.timezone_shift_for_rule(pd.DataFrame({"rich_entry_score": [0.1]}), {"original_rank": 1, "rule_id": "rank01"})

    assert set(result["shift_hours"]) == {-8, -4, 4, 8}
    assert set(result["status"]) == {"NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS"}
    assert "requires frozen rescore" in result["reason"].iloc[0]
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
./.venv/bin/python -m pytest tests/test_leaderboard_closure_audit.py::test_timezone_shift_is_not_faked_from_saved_scores -q
```

Expected: FAIL because `timezone_shift_for_rule` is missing.

- [ ] **Step 3: Implement honest feasibility status**

Add:

```python
TIMEZONE_SHIFT_HOURS = (-8, -4, 4, 8)


def timezone_shift_for_rule(scores: pd.DataFrame, contract_row: pd.Series | dict[str, object]) -> pd.DataFrame:
    row = contract_row.to_dict() if isinstance(contract_row, pd.Series) else dict(contract_row)
    return pd.DataFrame(
        [
            {
                "original_rank": int(row["original_rank"]),
                "rule_id": str(row["rule_id"]),
                "shift_hours": int(shift),
                "status": "NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS",
                "reason": "timezone-shift check requires frozen rescore of time features; saved scores cannot be shifted honestly",
                "rows_available": int(len(scores)),
            }
            for shift in TIMEZONE_SHIFT_HOURS
        ]
    )
```

- [ ] **Step 4: Run tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_leaderboard_closure_audit.py -q
```

Expected: PASS.

---

### Task 5: Sequential-Position Constraint Diagnostics

**Files:**
- Modify: `ML/baseline/audit_leaderboard_closure.py`
- Modify: `tests/test_leaderboard_closure_audit.py`

**Interfaces:**
- Produces:
  - `sequential_positions_for_rule(trades: pd.DataFrame, contract_row: pd.Series | dict[str, object]) -> pd.DataFrame`.
  - Policies: `single_position`, `max_positions_2`, `max_positions_3`.

- [ ] **Step 1: Add failing tests**

Append:

```python
def test_sequential_positions_uses_fill_time_not_signal_time():
    contract_row = {"original_rank": 1, "rule_id": "rank01"}
    trades = pd.DataFrame(
        [
            {"position_id": "a", "signal_time": "2021-01-01 00:00", "fill_time": "2021-01-01 02:00", "exit_time": "2021-01-01 03:00", "pnl_r": 1.0},
            {"position_id": "b", "signal_time": "2021-01-01 01:00", "fill_time": "2021-01-01 03:30", "exit_time": "2021-01-01 04:00", "pnl_r": 1.0},
            {"position_id": "c", "signal_time": "2021-01-01 04:00", "exit_time": "2021-01-01 05:00", "pnl_r": -0.5},
        ]
    )

    result = closure.sequential_positions_for_rule(trades, contract_row)
    single = result.loc[result["position_policy"].eq("single_position")].iloc[0]

    assert single["n_trades"] == 3
    assert single["dropped_trades"] == 0
    assert single["status"] == "COMPUTED"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
./.venv/bin/python -m pytest tests/test_leaderboard_closure_audit.py::test_sequential_positions_uses_fill_time_not_signal_time -q
```

Expected: FAIL because `sequential_positions_for_rule` is missing.

- [ ] **Step 3: Implement deterministic overlap simulation**

Add:

```python
POSITION_POLICIES = {"single_position": 1, "max_positions_2": 2, "max_positions_3": 3}


def _select_non_overlapping(trades: pd.DataFrame, max_positions: int) -> pd.DataFrame:
    frame = trades.copy()
    frame["_signal_dt"] = pd.to_datetime(frame["signal_time"], errors="coerce")
    frame["_fill_dt"] = pd.to_datetime(frame["fill_time"], errors="coerce")
    frame["_exit_dt"] = pd.to_datetime(frame["exit_time"], errors="coerce")
    frame = frame.sort_values(["_fill_dt", "_signal_dt", "_exit_dt", "position_id"], kind="mergesort")
    active_exits: list[pd.Timestamp] = []
    keep_indices = []
    for idx, row in frame.iterrows():
        fill_dt = row["_fill_dt"]
        active_exits = [exit_dt for exit_dt in active_exits if pd.notna(exit_dt) and exit_dt > fill_dt]
        if len(active_exits) < max_positions:
            keep_indices.append(idx)
            active_exits.append(row["_exit_dt"])
    return trades.loc[keep_indices].copy()


def sequential_positions_for_rule(trades: pd.DataFrame, contract_row: pd.Series | dict[str, object]) -> pd.DataFrame:
    row = contract_row.to_dict() if isinstance(contract_row, pd.Series) else dict(contract_row)
    required = {"signal_time", "fill_time", "exit_time", "position_id", "pnl_r"}
    records = []
    for policy, max_positions in POSITION_POLICIES.items():
        if not required.issubset(set(trades.columns)):
            records.append(
                {
                    "original_rank": int(row["original_rank"]),
                    "rule_id": str(row["rule_id"]),
                    "position_policy": policy,
                    "max_positions": int(max_positions),
                    "status": "NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS",
                    "n_trades": 0,
                    "dropped_trades": None,
                    "reason": "signal_time, fill_time, exit_time, position_id and pnl_r are required; position interval starts at fill_time",
                }
            )
            continue
        selected = _select_non_overlapping(trades, max_positions)
        records.append(
            {
                "original_rank": int(row["original_rank"]),
                "rule_id": str(row["rule_id"]),
                "position_policy": policy,
                "max_positions": int(max_positions),
                "status": "COMPUTED",
                "dropped_trades": int(len(trades) - len(selected)),
                "reason": "",
                **entry_exit.compute_trade_metrics(selected),
            }
        )
    return pd.DataFrame(records)
```

- [ ] **Step 4: Run tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_leaderboard_closure_audit.py -q
```

Expected: PASS.

---

### Task 6: Multi-Seed Closure For Fixed 11 Rule Families

**Files:**
- Modify: `ML/baseline/audit_leaderboard_closure.py`
- Modify: `tests/test_leaderboard_closure_audit.py`

**Interfaces:**
- Produces:
  - `multiseed_for_rule(artifact: dict[str, object], contract_row: pd.Series | dict[str, object]) -> pd.DataFrame`.
  - `bounded_multiseed_rerun_contract() -> dict[str, object]`.
  - Seeds: `41, 42, 43, 44, 45`.

- [ ] **Step 1: Add failing tests**

Append:

```python
def test_multiseed_status_is_not_computable_when_seed_artifacts_absent():
    result = closure.multiseed_for_rule({}, {"original_rank": 1, "rule_id": "rank01"})

    assert set(result["seed"]) == {41, 42, 43, 44, 45}
    assert set(result["status"]) == {"NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS"}
    assert "persisted per-seed" in result["reason"].iloc[0]


def test_bounded_multiseed_rerun_contract_has_fixed_11_rule_universe():
    contract = closure.bounded_multiseed_rerun_contract()

    assert contract["seeds"] == [41, 42, 43, 44, 45]
    assert contract["rule_count"] == 11
    assert contract["new_search_allowed"] is False
    assert contract["locked_test"] == "not_opened"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
./.venv/bin/python -m pytest tests/test_leaderboard_closure_audit.py::test_multiseed_status_is_not_computable_when_seed_artifacts_absent -q
```

Expected: FAIL because `multiseed_for_rule` is missing.

- [ ] **Step 3: Implement multi-seed artifact guard**

Add:

```python
MULTISEED_SEEDS = (41, 42, 43, 44, 45)


def bounded_multiseed_rerun_contract() -> dict[str, object]:
    return {
        "seeds": [int(seed) for seed in MULTISEED_SEEDS],
        "rule_count": len(LEADERBOARD_RULES),
        "rule_ids": [rule.rule_id for rule in LEADERBOARD_RULES],
        "new_search_allowed": False,
        "locked_test": "not_opened",
        "fixed_universe": "same 11 LEADERBOARD_RULES, same profiles/models/targets/filters, saved val_select cutoff only",
        "required_outputs": [
            "per_seed_summary_csv",
            "per_seed_trades_csv",
            "per_seed_scores_csv",
            "per_rule_seed_aggregate_csv",
        ],
    }


def multiseed_for_rule(artifact: dict[str, object], contract_row: pd.Series | dict[str, object]) -> pd.DataFrame:
    row = contract_row.to_dict() if isinstance(contract_row, pd.Series) else dict(contract_row)
    seed_artifacts = artifact.get("multiseed_artifacts") if isinstance(artifact, dict) else None
    if not isinstance(seed_artifacts, dict):
        return pd.DataFrame(
            [
                {
                    "original_rank": int(row["original_rank"]),
                    "rule_id": str(row["rule_id"]),
                    "seed": int(seed),
                    "status": "NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS",
                    "pf": None,
                    "bs_p05": None,
                    "n_trades": None,
                    "reason": "persisted per-seed artifacts are absent; rerun must be explicitly bounded to the same 11 fixed rule families",
                }
                for seed in MULTISEED_SEEDS
            ]
        )
    records = []
    for seed in MULTISEED_SEEDS:
        seed_key = str(seed)
        seed_row = seed_artifacts.get(seed_key)
        if not isinstance(seed_row, dict):
            records.append(
                {
                    "original_rank": int(row["original_rank"]),
                    "rule_id": str(row["rule_id"]),
                    "seed": int(seed),
                    "status": "MISSING_SEED_ARTIFACT",
                    "pf": None,
                    "bs_p05": None,
                    "n_trades": None,
                    "reason": f"missing persisted seed artifact {seed_key}",
                }
            )
            continue
        records.append(
            {
                "original_rank": int(row["original_rank"]),
                "rule_id": str(row["rule_id"]),
                "seed": int(seed),
                "status": "LOADED",
                "pf": seed_row.get("pf"),
                "bs_p05": seed_row.get("bs_p05"),
                "n_trades": seed_row.get("n_trades"),
                "reason": "",
            }
        )
    return pd.DataFrame(records)
```

- [ ] **Step 4: Run tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_leaderboard_closure_audit.py -q
```

Expected: PASS.

---

### Task 7: Batch Runner And Structured Artifacts

**Files:**
- Modify: `ML/baseline/audit_leaderboard_closure.py`
- Modify: `tests/test_leaderboard_closure_audit.py`

**Interfaces:**
- Produces:
  - `run_closure(input_prefix: Path, output_prefix: Path) -> dict[str, object]`.
  - `build_closure_classification(...) -> pd.DataFrame`.
  - CLI with `--input-prefix` and `--output-prefix`.

- [ ] **Step 1: Add failing batch tests**

Append:

```python
def test_build_closure_classification_preserves_rank_and_blocks_winner_selection():
    rules = pd.DataFrame(
        [
            {"original_rank": 2, "rule_id": "rank02"},
            {"original_rank": 1, "rule_id": "rank01"},
        ]
    )
    stress = pd.DataFrame({"rule_id": ["rank01"], "status": ["NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS"]})
    calendar = pd.DataFrame({"rule_id": ["rank01"], "status": ["COMPUTED"]})
    calendar_permutation = pd.DataFrame({"rule_id": ["rank01"], "status": ["NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS"]})
    calendar_no_ml = pd.DataFrame({"rule_id": ["rank01"], "status": ["NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS"]})
    timezone = pd.DataFrame({"rule_id": ["rank01"], "status": ["NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS"]})
    sequential = pd.DataFrame({"rule_id": ["rank01"], "status": ["COMPUTED"]})
    multiseed = pd.DataFrame({"rule_id": ["rank01"], "status": ["NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS"]})

    result = closure.build_closure_classification(rules, stress, calendar, calendar_permutation, calendar_no_ml, timezone, sequential, multiseed)

    assert result["original_rank"].tolist() == [1, 2]
    assert set(result["new_winner_selected"]) == {False}
    assert set(result["allowed_max_verdict"]) == {"research_only"}
    assert "stress_costs_missing" in result.loc[result["rule_id"].eq("rank02"), "reasons"].iloc[0]
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
./.venv/bin/python -m pytest tests/test_leaderboard_closure_audit.py::test_build_closure_classification_preserves_rank_and_blocks_winner_selection -q
```

Expected: FAIL because `build_closure_classification` is missing.

- [ ] **Step 3: Implement runner and JSON/CSV writes**

Add:

```python
def _concat(frames: list[pd.DataFrame]) -> pd.DataFrame:
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def _statuses_for_rule(rule_id: str, frame: pd.DataFrame) -> set[str]:
    if frame.empty or "rule_id" not in frame.columns or "status" not in frame.columns:
        return {"UNKNOWN"}
    values = set(frame.loc[frame["rule_id"].astype(str).eq(rule_id), "status"].astype(str))
    return values if values else {"MISSING_DIAGNOSTIC_ROW"}


def build_closure_classification(
    rules: pd.DataFrame,
    stress: pd.DataFrame,
    calendar: pd.DataFrame,
    calendar_permutation: pd.DataFrame,
    calendar_no_ml: pd.DataFrame,
    timezone: pd.DataFrame,
    sequential: pd.DataFrame,
    multiseed: pd.DataFrame,
) -> pd.DataFrame:
    records = []
    for _, row in rules.sort_values("original_rank").iterrows():
        rule_id = str(row["rule_id"])
        reasons = []
        disclosures = []
        if "NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS" in _statuses_for_rule(rule_id, stress):
            reasons.append("stress_costs_not_computable")
        if _statuses_for_rule(rule_id, stress) & {"MISSING_DIAGNOSTIC_ROW", "UNKNOWN"}:
            reasons.append("stress_costs_missing")
        if "NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS" in _statuses_for_rule(rule_id, calendar_permutation):
            disclosures.append("calendar_permutation_importance_not_computable")
        if "NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS" in _statuses_for_rule(rule_id, calendar_no_ml):
            disclosures.append("calendar_no_ml_baseline_not_computable")
        if _statuses_for_rule(rule_id, calendar) & {"MISSING_DIAGNOSTIC_ROW", "UNKNOWN"}:
            disclosures.append("time_calendar_missing")
        if "NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS" in _statuses_for_rule(rule_id, timezone):
            disclosures.append("timezone_shift_not_computable")
        if "NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS" in _statuses_for_rule(rule_id, multiseed):
            disclosures.append("multi_seed_not_computable")
        if _statuses_for_rule(rule_id, sequential) & {"MISSING_DIAGNOSTIC_ROW", "UNKNOWN"}:
            disclosures.append("sequential_position_missing")
        elif "COMPUTED" not in _statuses_for_rule(rule_id, sequential):
            disclosures.append("sequential_position_not_computed")
        decision = "CLOSURE_INCOMPLETE" if reasons or disclosures else "CLOSURE_DIAGNOSTICS_COMPUTED_RESEARCH_ONLY"
        records.append(
            {
                "original_rank": int(row["original_rank"]),
                "rule_id": rule_id,
                "decision": decision,
                "reasons": ",".join(reasons),
                "disclosures": ",".join(disclosures),
                "allowed_max_verdict": "research_only",
                "new_winner_selected": False,
            }
        )
    return pd.DataFrame(records)


def _write_csv(frame: pd.DataFrame, path: Path) -> None:
    frame.to_csv(path, sep=";", index=False)


def run_closure(input_prefix: Path = DEFAULT_INPUT_PREFIX, output_prefix: Path = CLOSURE_OUTPUT_PREFIX) -> dict[str, object]:
    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    try:
        verified = verify_closure_inputs(input_prefix)
    except leaderboard.LeaderboardAuditError as exc:
        result = {
            "experiment": "leaderboard_closure_audit",
            "status": "UNKNOWN",
            "run_status": "failed",
            "decision": getattr(exc, "decision", "UNKNOWN_INPUT_OR_CONTRACT"),
            "locked_test_status": "UNKNOWN",
            "error": str(exc),
        }
        output_prefix.with_suffix(".json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        return result
    except Exception as exc:
        result = {
            "experiment": "leaderboard_closure_audit",
            "status": "UNKNOWN",
            "run_status": "failed",
            "decision": "UNKNOWN_INPUT_OR_CONTRACT",
            "locked_test_status": "UNKNOWN",
            "error": str(exc),
        }
        output_prefix.with_suffix(".json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        return result

    loaded = verified["loaded"]
    artifact = loaded["artifact"]
    trades = loaded["trades"]
    scores = loaded["scores"]
    rules = verified["rule_contract"]
    stress_frames = []
    cost_disclosure_frames = []
    calendar_frames = []
    calendar_permutation_frames = []
    calendar_no_ml_frames = []
    timezone_frames = []
    sequential_frames = []
    multiseed_frames = []
    for _, contract_row in rules.iterrows():
        fixed_rule = leaderboard.fixed_rule_from_contract_row(contract_row)
        fixed_trades = leaderboard.base_audit.filter_fixed_rule_rows(trades, fixed_rule, split="val_eval")
        fixed_scores = leaderboard.base_audit.filter_fixed_rule_rows(scores, fixed_rule)
        stress_frames.append(stress_cost_grid_for_rule(fixed_trades, contract_row))
        cost_disclosure_frames.append(cost_model_disclosure_for_rule(contract_row))
        calendar_frames.append(time_calendar_for_rule(fixed_trades, contract_row))
        calendar_permutation_frames.append(calendar_permutation_importance_for_rule(artifact, contract_row))
        calendar_no_ml_frames.append(calendar_no_ml_baseline_for_rule(fixed_trades, contract_row))
        timezone_frames.append(timezone_shift_for_rule(fixed_scores, contract_row))
        sequential_frames.append(sequential_positions_for_rule(fixed_trades, contract_row))
        multiseed_frames.append(multiseed_for_rule(artifact, contract_row))

    stress = _concat(stress_frames)
    cost_disclosure = _concat(cost_disclosure_frames)
    calendar = _concat(calendar_frames)
    calendar_permutation = _concat(calendar_permutation_frames)
    calendar_no_ml = _concat(calendar_no_ml_frames)
    timezone = _concat(timezone_frames)
    sequential = _concat(sequential_frames)
    multiseed = _concat(multiseed_frames)
    classification = build_closure_classification(rules, stress, calendar, calendar_permutation, calendar_no_ml, timezone, sequential, multiseed)
    artifacts = {
        "rules_csv": output_prefix.with_name(output_prefix.name + "_rules.csv"),
        "stress_cost_csv": output_prefix.with_name(output_prefix.name + "_stress_cost.csv"),
        "cost_model_disclosure_csv": output_prefix.with_name(output_prefix.name + "_cost_model_disclosure.csv"),
        "calendar_csv": output_prefix.with_name(output_prefix.name + "_calendar.csv"),
        "calendar_permutation_importance_csv": output_prefix.with_name(output_prefix.name + "_calendar_permutation_importance.csv"),
        "calendar_no_ml_baselines_csv": output_prefix.with_name(output_prefix.name + "_calendar_no_ml_baselines.csv"),
        "timezone_shift_csv": output_prefix.with_name(output_prefix.name + "_timezone_shift.csv"),
        "sequential_positions_csv": output_prefix.with_name(output_prefix.name + "_sequential_positions.csv"),
        "multiseed_csv": output_prefix.with_name(output_prefix.name + "_multiseed.csv"),
        "classification_csv": output_prefix.with_name(output_prefix.name + "_classification.csv"),
    }
    for frame, path in [
        (rules, artifacts["rules_csv"]),
        (stress, artifacts["stress_cost_csv"]),
        (cost_disclosure, artifacts["cost_model_disclosure_csv"]),
        (calendar, artifacts["calendar_csv"]),
        (calendar_permutation, artifacts["calendar_permutation_importance_csv"]),
        (calendar_no_ml, artifacts["calendar_no_ml_baselines_csv"]),
        (timezone, artifacts["timezone_shift_csv"]),
        (sequential, artifacts["sequential_positions_csv"]),
        (multiseed, artifacts["multiseed_csv"]),
        (classification, artifacts["classification_csv"]),
    ]:
        _write_csv(frame, path)
    result = {
        "experiment": "leaderboard_closure_audit",
        "status": "completed",
        "run_status": "completed",
        "verdict": "research_only",
        "locked_test": "not_opened",
        "scope": CLOSURE_SCOPE,
        "leaderboard_rule_count": int(len(rules)),
        **default_closure_statuses(),
        "stress_costs_status": ",".join(sorted(set(stress["status"].astype(str)))) if not stress.empty else "UNKNOWN",
        "cost_model_disclosure_status": ",".join(sorted(set(cost_disclosure["status"].astype(str)))) if not cost_disclosure.empty else "UNKNOWN",
        "time_calendar_status": ",".join(sorted(set(calendar["status"].astype(str)))) if not calendar.empty else "UNKNOWN",
        "calendar_permutation_importance_status": ",".join(sorted(set(calendar_permutation["status"].astype(str)))) if not calendar_permutation.empty else "UNKNOWN",
        "calendar_no_ml_baseline_status": ",".join(sorted(set(calendar_no_ml["status"].astype(str)))) if not calendar_no_ml.empty else "UNKNOWN",
        "timezone_shift_status": ",".join(sorted(set(timezone["status"].astype(str)))) if not timezone.empty else "UNKNOWN",
        "sequential_position_constraint_status": ",".join(sorted(set(sequential["status"].astype(str)))) if not sequential.empty else "UNKNOWN",
        "multi_seed_status": ",".join(sorted(set(multiseed["status"].astype(str)))) if not multiseed.empty else "UNKNOWN",
        "overall_decision": "LEADERBOARD_CLOSURE_INCOMPLETE_RESEARCH_ONLY"
        if (
            "CLOSURE_INCOMPLETE" in set(classification["decision"].astype(str))
            or any(status in json.dumps(classification.to_dict(orient="records")) for status in ["UNKNOWN", "MISSING_DIAGNOSTIC_ROW", "NOT_RUN", "NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS"])
        )
        else "LEADERBOARD_CLOSURE_DIAGNOSTICS_COMPUTED_RESEARCH_ONLY",
        "artifacts": {key: str(value) for key, value in artifacts.items()},
    }
    output_prefix.with_suffix(".json").write_text(json.dumps(result, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    return result


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Closure audit for fixed normalized leaderboard rows.")
    parser.add_argument("--input-prefix", default=str(DEFAULT_INPUT_PREFIX))
    parser.add_argument("--output-prefix", default=str(CLOSURE_OUTPUT_PREFIX))
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    result = run_closure(Path(args.input_prefix), Path(args.output_prefix))
    print(json.dumps({"status": result["status"], "overall_decision": result.get("overall_decision")}, ensure_ascii=False))
    if result.get("status") == "UNKNOWN":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests and CLI**

Run:

```bash
./.venv/bin/python -m pytest tests/test_leaderboard_closure_audit.py -q
./.venv/bin/python ML/baseline/audit_leaderboard_closure.py --input-prefix ML/reports/fractal0_rich_entry_quality_normalized --output-prefix ML/reports/leaderboard_closure_audit
```

Expected: tests PASS; CLI exit `0`, JSON status `completed`.

---

### Task 8: Module Docs, Report, Stage Sync

**Files:**
- Create: `docs/ML/audit_leaderboard_closure.py.md`
- Create: `docs/reports/2026-07-23-fractal0-leaderboard-cost-calendar-sequential-multiseed-closure.md`
- Modify: `MODULE_INDEX.md`
- Modify: `docs/ML/audit_leaderboard_robustness.py.md`
- Modify: `docs/superpowers/roadmap.md`
- Modify: `CONTEXT_HANDOFF.md`
- Modify: `CHANGELOG.md`
- Modify: `wiki/research/fractal-stop-research.md`
- Modify: `wiki/index.md`
- Modify: `wiki/log.md`
- Modify: `wiki/REPO_integrity.md`

**Interfaces:**
- Consumes: `ML/reports/leaderboard_closure_audit.json` and CSV artifacts.
- Produces: canonical report and synchronized project state.

- [ ] **Step 1: Run verification commands**

Run:

```bash
./.venv/bin/python -m pytest tests/test_leaderboard_closure_audit.py -q
./.venv/bin/python ML/baseline/audit_leaderboard_closure.py --input-prefix ML/reports/fractal0_rich_entry_quality_normalized --output-prefix ML/reports/leaderboard_closure_audit
./.venv/bin/python -m pytest tests/ -q
```

Expected: targeted tests pass; CLI exits `0`; full suite exits `0`.

- [ ] **Step 2: Extract report numbers**

Run:

```bash
./.venv/bin/python -c 'import json, pandas as pd; data=json.loads(open("ML/reports/leaderboard_closure_audit.json", encoding="utf-8").read()); cls=pd.read_csv("ML/reports/leaderboard_closure_audit_classification.csv", sep=";"); print("status:", data["status"]); print("verdict:", data["verdict"]); print("locked_test:", data["locked_test"]); print("rule_count:", data["leaderboard_rule_count"]); print("overall_decision:", data["overall_decision"]); print("stress:", data["stress_costs_status"]); print("cost_model:", data["cost_model_disclosure_status"]); print("calendar:", data["time_calendar_status"]); print("calendar_permutation:", data["calendar_permutation_importance_status"]); print("calendar_no_ml:", data["calendar_no_ml_baseline_status"]); print("timezone:", data["timezone_shift_status"]); print("sequential:", data["sequential_position_constraint_status"]); print("multi_seed:", data["multi_seed_status"]); print("decisions:", cls["decision"].value_counts().to_dict())'
```

Expected: concrete values printed from artifacts.

- [ ] **Step 3: Create module docs**

Create `docs/ML/audit_leaderboard_closure.py.md` with command, inputs, outputs and limitations. It must say:

```md
`locked_test` remains closed. Provider drift and transfer are not in scope.
The script checks all 11 fixed leaderboard rows and never performs winner selection.
Maximum verdict is `research_only`.
```

- [ ] **Step 4: Create stage report**

Create `docs/reports/2026-07-23-fractal0-leaderboard-cost-calendar-sequential-multiseed-closure.md`. Required sections:

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
research_priority=medium; close/disclose internal robustness blockers before any freeze discussion
current_search_budget=no new search, 11 fixed audit input rows, 5 predefined multi-seed seeds only if bounded rerun is implemented
cumulative_search_budget=inherited from normalized rich-entry search, 243 ranked configs plus diagnostic controls
next_probe_freeze=not created in this stage
allowed_max_verdict=research_only
locked_test=not_opened
provider_drift_status=NOT_IN_SCOPE
transfer_status=NOT_IN_SCOPE
cost_model_disclosure_status=reported for spread, commission, swap, slippage, requote/open failure, latency, next-bar entry and position limits
calendar_permutation_importance_status=COMPUTED or NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS
calendar_no_ml_baseline_status=COMPUTED or NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS
forbidden_interpretations=candidate/tradable/live_ready/production/permission_to_open_locked_test/new_winner
```

- [ ] **Step 5: Stage sync**

Update `CHANGELOG.md`, `CONTEXT_HANDOFF.md`, `docs/superpowers/roadmap.md`, `MODULE_INDEX.md` and wiki. Keep exactly one active track in `docs/superpowers/roadmap.md`.

If closure still returns incomplete statuses, next step must be one of:

```text
write explicit producer-level stress-cost resimulation plan
write explicit frozen timezone-rescore plan
write bounded multi-seed rerun plan for exactly the 11 fixed rule families
close rich/fractal entry-quality branch as time-heavy research-only
```

- [ ] **Step 6: Final verification**

Run:

```bash
rg -n "leaderboard_closure_audit|fractal0-leaderboard-cost-calendar-sequential-multiseed-closure|locked_test=not_opened|provider_drift_status=NOT_IN_SCOPE|transfer_status=NOT_IN_SCOPE" \
  docs/reports/2026-07-23-fractal0-leaderboard-cost-calendar-sequential-multiseed-closure.md \
  docs/ML/audit_leaderboard_closure.py.md \
  docs/superpowers/roadmap.md \
  CONTEXT_HANDOFF.md \
  CHANGELOG.md \
  MODULE_INDEX.md
./.venv/bin/python -m pytest tests/ -q
```

Expected: `rg` shows consistent paths/statuses; full tests pass.

---

## Self-Review Checklist

- Spec coverage: all 11 fixed leaderboard rows, stress-cost, time-calendar, timezone feasibility, sequential-position and multi-seed covered.
- Scope control: provider drift and transfer explicitly out of scope.
- No `locked_test`: every task keeps `locked_test=not_opened`.
- No new search: no new profile/model/target/filter/cutoff/instrument; `original_rank` preserved.
- Type consistency: `rule_id`, `original_rank`, `contract_row`, output artifact names and status strings match across tasks.
- Reporting: final report must copy key numbers from JSON/CSV, not from memory.
