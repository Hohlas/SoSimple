# Time Only Robustness Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Проверить validation-slice устойчивость текущего `time_only` winner без нового перебора и без открытия `locked_test`.

**Architecture:** Добавить отдельный audit-скрипт, который читает уже созданные normalized rich-entry artifacts и анализирует только заранее выбранное правило. Скрипт не обучает новые модели, не выбирает новый cutoff, не открывает `locked_test` и пишет отдельные CSV/JSON artifacts с yearly, quarterly, side, score-shift, stricter-cutoff, top-k, календарными, sequential и stress-cost diagnostics.

**Tech Stack:** Python через `./.venv/bin/python`, pandas, numpy, pytest, существующие helpers из `ML/baseline/benchmark_fractal0_entry_exit_grid.py`; новых зависимостей не добавлять.

## Global Constraints

- Работать на текущей feature-ветке; worktree не создавать.
- Использовать только `./.venv/bin/python`.
- `locked_test` не открывать; все новые artifacts должны явно содержать `locked_test=not_opened`.
- Не запускать новый search: не добавлять profiles, targets, models, filters или новый cutoff.
- Аудируем только fixed rule:

```text
S2_fractal0_buffer_0_5_entry_floor_2 /
E3_open_pullback_1_0atr /
M0_no_mask /
X2_ml_opposite_any_p0_50 /
profile=time_only /
model=linear /
target=target_entry_ev_regression /
filter=top30 /
score_cutoff_on_val_select=-0.026718184259660646
```

- Источник fixed rule: `ML/reports/fractal0_rich_entry_quality_normalized.json`.
- Если artifact содержит другой winner или `locked_test != not_opened`, audit должен завершиться `UNKNOWN` и exit code `1`.
- Maximum verdict: `research_only`; нельзя писать `candidate`, `tradable`, `live_ready`, `production` или `permission_to_open_locked_test`.
- Scope этого плана: `validation_artifact_robustness_slice`.
- `multi_seed_status=NOT_RUN`, `provider_drift_status=NOT_RUN`, `transfer_status=NOT_RUN`, `locked_test_status=not_opened`.
- Итоговое решение должно быть одним из: `TIME_ONLY_ROBUSTNESS_SLICE_OK_FOR_NEXT_PROBE_DESIGN`, `REGIME_REFORMULATION_REQUIRED`, `REJECT_TIME_ONLY_AS_UNSTABLE`, `UNKNOWN_ARTIFACT_CONTRACT`.
- Методический источник: `docs/methodology/11-robustness.md`.
- Decision gate config должен быть записан в JSON: side PF/N/drawdown, concentration, block bootstrap, stress costs, stricter cutoff и top-k diagnostics.
- После Python-изменений запускать `./.venv/bin/python -m pytest tests/ -q`.

---

## File Structure

- Create: `ML/baseline/audit_time_only_robustness.py`
  - Reads normalized rich-entry JSON/CSV artifacts.
  - Verifies fixed winner contract.
  - Computes yearly, quarterly, side, year-side, score-shift, stricter-cutoff, top-k, calendar no-ML, sequential and spread-stress diagnostics.
  - Writes JSON/CSV artifacts under `ML/reports/time_only_robustness_audit*`.
- Create: `tests/test_time_only_robustness_audit.py`
  - Unit tests for contract guard, grouping metrics, concentration metrics, cutoff diagnostics and final decision.
- Create after run: `docs/reports/2026-07-23-time-only-robustness-audit.md`
  - Human report with verdict and next action.
- Modify after run: `docs/superpowers/roadmap.md`
  - Move `time_only robustness audit` from `ACTIVE` to completed/next decision and set the next active branch.
- Modify after run: `CONTEXT_HANDOFF.md`
  - Short baton pass with exact artifacts and next step.
- Modify after run: `docs/ML/benchmark_fractal0_entry_quality_filter.py.md`
  - Add cross-link to the robustness audit script/artifacts.
- Create after run: `docs/ML/audit_time_only_robustness.py.md`
  - Document command, inputs, outputs, constraints and artifact contract for the new module.
- Modify after run: `MODULE_INDEX.md`
  - Add the new audit script and documentation entry.
- Modify after run if stage is closed: `CHANGELOG.md`, `wiki/research/fractal-stop-research.md`, `wiki/index.md`, `wiki/log.md`, `wiki/REPO_integrity.md`
  - Use `stage-reporting` for final synchronization.

New artifacts:

- `ML/reports/time_only_robustness_audit.json`
- `ML/reports/time_only_robustness_audit_yearly.csv`
- `ML/reports/time_only_robustness_audit_quarterly.csv`
- `ML/reports/time_only_robustness_audit_side.csv`
- `ML/reports/time_only_robustness_audit_year_side.csv`
- `ML/reports/time_only_robustness_audit_score_shift.csv`
- `ML/reports/time_only_robustness_audit_stricter_cutoff.csv`
- `ML/reports/time_only_robustness_audit_topk_sensitivity.csv`
- `ML/reports/time_only_robustness_audit_calendar_no_ml_baselines.csv`
- `ML/reports/time_only_robustness_audit_calendar_slices.csv`
- `ML/reports/time_only_robustness_audit_sequential.csv`
- `ML/reports/time_only_robustness_audit_spread_stress.csv`

---

### Task 1: Add Audit Helpers With Contract Guard

**Files:**
- Create: `tests/test_time_only_robustness_audit.py`
- Create: `ML/baseline/audit_time_only_robustness.py`

**Interfaces:**
- Produces:
  - `FixedRule` dataclass with fields `stop_policy_id`, `entry_id`, `mask_id`, `exit_id`, `spread`, `profile_id`, `model_id`, `target_id`, `filter_id`, `entry_filter_score_col`, `score_cutoff_on_val_select`.
  - `load_normalized_artifacts(prefix: Path) -> dict[str, object]`.
  - `verify_fixed_rule_contract(artifact: dict[str, object], expected: FixedRule) -> dict[str, object]`.

- [ ] **Step 1: Write failing contract tests**

Create `tests/test_time_only_robustness_audit.py`:

```python
import pytest

from ML.baseline import audit_time_only_robustness as audit


def _winner_payload(profile_id: str = "time_only") -> dict[str, object]:
    return {
        "stop_policy_id": "S2_fractal0_buffer_0_5_entry_floor_2",
        "entry_id": "E3_open_pullback_1_0atr",
        "mask_id": "M0_no_mask",
        "exit_id": "X2_ml_opposite_any_p0_50",
        "spread": 0.2,
        "profile_id": profile_id,
        "model_id": "linear",
        "target_id": "target_entry_ev_regression",
        "filter_id": "top30",
        "entry_filter_score_col": "rich_entry_score",
        "score_cutoff_on_val_select": -0.026718184259660646,
    }


def test_verify_fixed_rule_contract_accepts_normalized_time_only_winner():
    artifact = {
        "locked_test": "not_opened",
        "feature_contract_variant": "normalized_atr_unit",
        "selected_winner": _winner_payload(),
        "selected_winner_val_eval": _winner_payload(),
    }
    result = audit.verify_fixed_rule_contract(artifact, audit.EXPECTED_RULE)
    assert result["status"] == "PASS"
    assert result["checks"]["selected_winner"]["status"] == "PASS"
    assert result["checks"]["selected_winner_val_eval"]["status"] == "PASS"


def test_verify_fixed_rule_contract_blocks_locked_test_or_changed_rule():
    artifact = {
        "locked_test": "opened",
        "feature_contract_variant": "normalized_atr_unit",
        "selected_winner": _winner_payload(),
        "selected_winner_val_eval": _winner_payload("movement_plus_time"),
    }
    with pytest.raises(ValueError, match="fixed rule contract"):
        audit.verify_fixed_rule_contract(artifact, audit.EXPECTED_RULE)


def test_verify_fixed_rule_contract_blocks_changed_val_select_winner():
    artifact = {
        "locked_test": "not_opened",
        "feature_contract_variant": "normalized_atr_unit",
        "selected_winner": _winner_payload("movement_plus_time"),
        "selected_winner_val_eval": _winner_payload(),
    }
    with pytest.raises(ValueError, match="fixed rule contract"):
        audit.verify_fixed_rule_contract(artifact, audit.EXPECTED_RULE)
```

- [ ] **Step 2: Run test and verify it fails**

Run:

```bash
./.venv/bin/python -m pytest tests/test_time_only_robustness_audit.py::test_verify_fixed_rule_contract_accepts_normalized_time_only_winner -q
```

Expected: `FAIL` with missing module or missing function.

- [ ] **Step 3: Implement minimal contract guard**

Create `ML/baseline/audit_time_only_robustness.py`:

```python
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ML.baseline import benchmark_fractal0_entry_exit_grid as base


DEFAULT_INPUT_PREFIX = Path("ML/reports/fractal0_rich_entry_quality_normalized")
DEFAULT_OUTPUT_PREFIX = Path("ML/reports/time_only_robustness_audit")


@dataclass(frozen=True)
class FixedRule:
    stop_policy_id: str
    entry_id: str
    mask_id: str
    exit_id: str
    spread: float
    profile_id: str
    model_id: str
    target_id: str
    filter_id: str
    entry_filter_score_col: str
    score_cutoff_on_val_select: float


EXPECTED_RULE = FixedRule(
    stop_policy_id="S2_fractal0_buffer_0_5_entry_floor_2",
    entry_id="E3_open_pullback_1_0atr",
    mask_id="M0_no_mask",
    exit_id="X2_ml_opposite_any_p0_50",
    spread=0.2,
    profile_id="time_only",
    model_id="linear",
    target_id="target_entry_ev_regression",
    filter_id="top30",
    entry_filter_score_col="rich_entry_score",
    score_cutoff_on_val_select=-0.026718184259660646,
)


SUMMARY_USECOLS = [
    "stop_policy_id", "entry_id", "mask_id", "exit_id", "split", "spread",
    "n_trades", "gross_profit", "gross_loss", "pf", "mean_pnl_r",
    "median_pnl_r", "max_drawdown_r", "win_rate", "bs_p05",
    "negative_years", "pf_without_best_year", "effective_profit_years",
    "n_years", "filter_id", "score_cutoff_on_val_select",
    "entry_filter_score_col", "profile_id", "model_id", "target_id",
]
TRADES_USECOLS = [
    "position_id", "split", "profile_id", "model_id", "target_id",
    "filter_id", "stop_policy_id", "entry_id", "mask_id", "exit_id",
    "spread", "side", "signal_time", "fill_time", "exit_time",
    "close_reason", "pnl_r", "hold_bars", "ambiguous",
]
SCORES_USECOLS = [
    "position_id", "split", "profile_id", "model_id", "target_id",
    "filter_id", "rich_entry_score",
]


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


def _winner_contract_checks(winner: dict[str, object], expected: FixedRule) -> dict[str, bool]:
    return {
        "stop_policy_id": winner.get("stop_policy_id") == expected.stop_policy_id,
        "entry_id": winner.get("entry_id") == expected.entry_id,
        "mask_id": winner.get("mask_id") == expected.mask_id,
        "exit_id": winner.get("exit_id") == expected.exit_id,
        "spread": np.isclose(float(winner.get("spread")), expected.spread, rtol=0.0, atol=1e-12),
        "profile_id": winner.get("profile_id") == expected.profile_id,
        "model_id": winner.get("model_id") == expected.model_id,
        "target_id": winner.get("target_id") == expected.target_id,
        "filter_id": winner.get("filter_id") == expected.filter_id,
        "entry_filter_score_col": winner.get("entry_filter_score_col") == expected.entry_filter_score_col,
        "score_cutoff_on_val_select": np.isclose(
            float(winner.get("score_cutoff_on_val_select")),
            expected.score_cutoff_on_val_select,
            rtol=0.0,
            atol=1e-12,
        ),
    }


def verify_fixed_rule_contract(artifact: dict[str, object], expected: FixedRule = EXPECTED_RULE) -> dict[str, object]:
    checks: dict[str, object] = {
        "locked_test": artifact.get("locked_test") == "not_opened",
        "feature_contract_variant": artifact.get("feature_contract_variant") == "normalized_atr_unit",
    }
    failed: list[str] = [name for name, ok in checks.items() if not ok]
    actual: dict[str, object] = {}

    for source_name in ("selected_winner", "selected_winner_val_eval"):
        winner = artifact.get(source_name)
        if not isinstance(winner, dict):
            failed.append(f"{source_name}.missing")
            checks[source_name] = {"status": "FAIL", "checks": {}}
            actual[source_name] = None
            continue
        source_checks = _winner_contract_checks(winner, expected)
        source_failed = [f"{source_name}.{name}" for name, ok in source_checks.items() if not ok]
        failed.extend(source_failed)
        checks[source_name] = {"status": "PASS" if not source_failed else "FAIL", "checks": source_checks}
        actual[source_name] = {field.name: winner.get(field.name) for field in fields(FixedRule)}

    if failed:
        raise ValueError(f"fixed rule contract failed: {failed}; expected={expected.__dict__}; actual={actual}")
    return {"status": "PASS", "checks": checks, "expected_rule": expected.__dict__}
```

- [ ] **Step 4: Run contract tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_time_only_robustness_audit.py::test_verify_fixed_rule_contract_accepts_normalized_time_only_winner tests/test_time_only_robustness_audit.py::test_verify_fixed_rule_contract_blocks_locked_test_or_changed_rule -q
```

Expected: `2 passed`.

---

### Task 2: Add Robustness Diagnostics

**Files:**
- Modify: `tests/test_time_only_robustness_audit.py`
- Modify: `ML/baseline/audit_time_only_robustness.py`

**Interfaces:**
- Consumes:
  - `trades` with columns `split`, `profile_id`, `model_id`, `target_id`, `filter_id`, `side`, `pnl_r`, `exit_time`, `spread`.
  - `scores` with columns `split`, `profile_id`, `model_id`, `target_id`, `filter_id`, `rich_entry_score`.
- Produces:
  - `filter_fixed_rule_rows(frame: pd.DataFrame, rule: FixedRule, split: str | None = None) -> pd.DataFrame`.
  - `metrics_by_period(trades: pd.DataFrame, freq: str) -> pd.DataFrame`.
  - `metrics_by_side(trades: pd.DataFrame) -> pd.DataFrame`.
  - `profit_concentration(trades: pd.DataFrame) -> dict[str, object]`.
  - `sequential_block_bootstrap_pf(trades: pd.DataFrame, seed: int, n_bootstrap: int, block_size: int) -> dict[str, object]`.
  - `score_shift(scores: pd.DataFrame, rule: FixedRule) -> pd.DataFrame`.
  - `stricter_cutoff_sensitivity(scores: pd.DataFrame, trades: pd.DataFrame, rule: FixedRule) -> pd.DataFrame`.
  - `topk_sensitivity(trades: pd.DataFrame, rule: FixedRule) -> pd.DataFrame`.

- [ ] **Step 1: Write failing tests for grouping and concentration**

Append:

```python
import pandas as pd


def test_period_side_and_profit_concentration_metrics():
    trades = pd.DataFrame(
        {
            "split": ["val_eval"] * 6,
            "profile_id": ["time_only"] * 6,
            "model_id": ["linear"] * 6,
            "target_id": ["target_entry_ev_regression"] * 6,
            "filter_id": ["top30"] * 6,
            "side": ["BUY", "BUY", "SELL", "SELL", "BUY", "SELL"],
            "exit_time": pd.to_datetime(["2021-01-02", "2021-02-03", "2021-04-04", "2022-01-05", "2022-05-06", "2022-07-07"]),
            "pnl_r": [1.0, -0.5, 0.8, 0.6, -0.2, 0.4],
            "close_reason": ["TP", "SL", "TP", "ML_CLOSE", "SL", "TP"],
        }
    )
    yearly = audit.metrics_by_period(trades, "Y")
    side = audit.metrics_by_side(trades)
    concentration = audit.profit_concentration(trades)

    assert set(yearly["period"]) == {"2021", "2022"}
    assert set(side["side"]) == {"BUY", "SELL"}
    assert concentration["n_years"] == 2
    assert concentration["effective_profit_years"] > 1.0
    assert concentration["best_year_share"] < 1.0
```

- [ ] **Step 2: Write failing tests for score shift and cutoff sensitivity**

Append:

```python
def test_score_shift_and_stricter_cutoff_use_fixed_rule_only():
    scores = pd.DataFrame(
        {
            "split": ["val_select", "val_select", "val_eval", "val_eval"],
            "profile_id": ["time_only"] * 4,
            "model_id": ["linear"] * 4,
            "target_id": ["target_entry_ev_regression"] * 4,
            "filter_id": ["top30"] * 4,
            "position_id": ["a", "b", "c", "d"],
            "rich_entry_score": [-0.01, -0.04, -0.02, -0.05],
        }
    )
    trades = pd.DataFrame(
        {
            "split": ["val_eval", "val_eval"],
            "profile_id": ["time_only", "time_only"],
            "model_id": ["linear", "linear"],
            "target_id": ["target_entry_ev_regression", "target_entry_ev_regression"],
            "filter_id": ["top30", "top30"],
            "position_id": ["c", "d"],
            "side": ["BUY", "SELL"],
            "exit_time": pd.to_datetime(["2022-01-01", "2022-01-02"]),
            "pnl_r": [1.0, -0.5],
            "close_reason": ["TP", "SL"],
        }
    )

    shift = audit.score_shift(scores, audit.EXPECTED_RULE)
    sensitivity = audit.stricter_cutoff_sensitivity(scores, trades, audit.EXPECTED_RULE, offsets=[0.0, 0.02])

    assert set(shift["split"]) == {"val_select", "val_eval"}
    assert set(sensitivity["cutoff_offset"]) == {0.0, 0.02}
    assert sensitivity.loc[sensitivity["cutoff_offset"].eq(0.0), "n_trades"].iloc[0] == 1


def test_sequential_block_bootstrap_preserves_adjacent_blocks():
    trades = pd.DataFrame({"pnl_r": [1.0, 2.0, -1.0, -2.0, 3.0, -3.0]})
    sample = audit._sequential_block_sample_indices(len(trades), seed=7, block_size=2)
    assert len(sample) == len(trades)
    assert all((sample[i + 1] - sample[i]) % len(trades) == 1 for i in range(0, len(sample), 2))


def test_topk_sensitivity_uses_saved_top30_top40_top50_trades():
    base_cols = {
        "stop_policy_id": "S2_fractal0_buffer_0_5_entry_floor_2",
        "entry_id": "E3_open_pullback_1_0atr",
        "mask_id": "M0_no_mask",
        "exit_id": "X2_ml_opposite_any_p0_50",
        "spread": 0.2,
        "split": "val_eval",
        "profile_id": "time_only",
        "model_id": "linear",
        "target_id": "target_entry_ev_regression",
    }
    trades = pd.DataFrame(
        {
            **{key: [value, value, value] for key, value in base_cols.items()},
            "filter_id": ["top30", "top40", "top50"],
            "pnl_r": [1.0, 0.5, -0.25],
            "close_reason": ["TP", "TP", "SL"],
        }
    )
    result = audit.topk_sensitivity(trades, audit.EXPECTED_RULE)
    assert set(result["filter_id"]) == {"top30", "top40", "top50"}
```

- [ ] **Step 3: Run tests and verify they fail**

Run:

```bash
./.venv/bin/python -m pytest tests/test_time_only_robustness_audit.py -q
```

Expected: new tests fail with missing functions.

- [ ] **Step 4: Implement diagnostics**

Append to `ML/baseline/audit_time_only_robustness.py`:

```python
def filter_fixed_rule_rows(frame: pd.DataFrame, rule: FixedRule = EXPECTED_RULE, split: str | None = None) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    mask = pd.Series(True, index=frame.index)
    exact_fields = {
        "stop_policy_id": rule.stop_policy_id,
        "entry_id": rule.entry_id,
        "mask_id": rule.mask_id,
        "exit_id": rule.exit_id,
        "profile_id": rule.profile_id,
        "model_id": rule.model_id,
        "target_id": rule.target_id,
        "filter_id": rule.filter_id,
    }
    for column, expected in exact_fields.items():
        if column in frame.columns:
            mask &= frame[column].astype(str).eq(str(expected))
    if "spread" in frame.columns:
        mask &= pd.to_numeric(frame["spread"], errors="coerce").eq(rule.spread)
    if split is not None and "split" in frame.columns:
        mask &= frame["split"].astype(str).eq(split)
    return frame.loc[mask].copy()


def _period_series(values: pd.Series, freq: str) -> pd.Series:
    dates = pd.to_datetime(values, errors="coerce")
    if freq == "Y":
        return dates.dt.year.astype("Int64").astype(str)
    if freq == "Q":
        return dates.dt.to_period("Q").astype(str)
    raise ValueError(f"unsupported freq: {freq}")


def _metrics_row(group: pd.DataFrame) -> dict[str, object]:
    return base.compute_trade_metrics(group)


def metrics_by_period(trades: pd.DataFrame, freq: str) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame()
    frame = trades.copy()
    frame["period"] = _period_series(frame["exit_time"], freq)
    rows = [{"period": str(period), **_metrics_row(group)} for period, group in frame.groupby("period", dropna=False)]
    return pd.DataFrame(rows).sort_values("period").reset_index(drop=True)


def metrics_by_side(trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame()
    rows = [{"side": str(side), **_metrics_row(group)} for side, group in trades.groupby("side", dropna=False)]
    return pd.DataFrame(rows).sort_values("side").reset_index(drop=True)


def metrics_by_year_side(trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame()
    frame = trades.copy()
    frame["year"] = _period_series(frame["exit_time"], "Y")
    rows = [{"year": str(year), "side": str(side), **_metrics_row(group)} for (year, side), group in frame.groupby(["year", "side"], dropna=False)]
    return pd.DataFrame(rows).sort_values(["year", "side"]).reset_index(drop=True)


def profit_concentration(trades: pd.DataFrame) -> dict[str, object]:
    yearly = base.yearly_metrics(trades)
    gross = np.array([max(0.0, float(row.get("gross_profit") or 0.0)) for row in yearly], dtype=float)
    total = float(gross.sum())
    shares = gross / total if total > 0 else np.zeros_like(gross)
    best_year_share = float(shares.max()) if len(shares) else 0.0
    return {
        "n_years": int(len(yearly)),
        "effective_profit_years": base.effective_profit_years_from_yearly(yearly),
        "best_year_share": best_year_share,
        "profitable_years": int(sum(float(row.get("mean_pnl_r") or 0.0) > 0.0 for row in yearly)),
        "min_year_pf": min([float(row["pf"]) for row in yearly if row.get("pf") is not None], default=None),
    }


def _sequential_block_sample_indices(n: int, seed: int, block_size: int) -> np.ndarray:
    if n <= 0:
        return np.array([], dtype=int)
    rng = np.random.default_rng(seed)
    starts = rng.integers(0, n, size=int(np.ceil(n / block_size)))
    blocks = [np.arange(start, start + block_size, dtype=int) % n for start in starts]
    return np.concatenate(blocks)[:n]


def sequential_block_bootstrap_pf(
    trades: pd.DataFrame,
    seed: int = 20260723,
    n_bootstrap: int = 1000,
    block_size: int = 20,
) -> dict[str, object]:
    pnl = pd.to_numeric(trades.get("pnl_r"), errors="coerce").dropna().to_numpy()
    if len(pnl) == 0:
        return {"bs_p05": None, "samples": 0, "bootstrap_method": "sequential_block", "block_size": block_size}
    values = []
    for i in range(n_bootstrap):
        idx = _sequential_block_sample_indices(len(pnl), seed + i, block_size)
        sample = pnl[idx]
        gross_profit = sample[sample > 0].sum()
        gross_loss = -sample[sample < 0].sum()
        values.append(float(gross_profit / gross_loss) if gross_loss > 0 else 99.0)
    return {
        "bs_p05": float(np.quantile(values, 0.05)),
        "samples": int(n_bootstrap),
        "bootstrap_method": "sequential_block",
        "block_size": int(block_size),
        "seed": int(seed),
    }


def score_shift(scores: pd.DataFrame, rule: FixedRule = EXPECTED_RULE) -> pd.DataFrame:
    fixed = filter_fixed_rule_rows(scores, rule)
    rows = []
    for split, group in fixed.groupby("split", dropna=False):
        values = pd.to_numeric(group["rich_entry_score"], errors="coerce").dropna()
        rows.append({
            "split": str(split),
            "rows": int(len(group)),
            "valid_rows": int(len(values)),
            "mean_score": float(values.mean()) if len(values) else None,
            "p10": float(values.quantile(0.10)) if len(values) else None,
            "p50": float(values.quantile(0.50)) if len(values) else None,
            "p90": float(values.quantile(0.90)) if len(values) else None,
            "fraction_above_fixed_cutoff": float((values >= rule.score_cutoff_on_val_select).mean()) if len(values) else None,
        })
    return pd.DataFrame(rows)


def stricter_cutoff_sensitivity(
    scores: pd.DataFrame,
    trades: pd.DataFrame,
    rule: FixedRule = EXPECTED_RULE,
    offsets: list[float] | None = None,
) -> pd.DataFrame:
    offsets = offsets or [0.0, 0.005, 0.01, 0.02]
    fixed_scores = filter_fixed_rule_rows(scores, rule, split="val_eval")
    fixed_trades = filter_fixed_rule_rows(trades, rule, split="val_eval")
    rows = []
    for offset in offsets:
        if offset < 0.0:
            raise ValueError("saved top30 trades cannot support looser cutoff; use topk_sensitivity instead")
        cutoff = rule.score_cutoff_on_val_select + float(offset)
        keep_ids = set(fixed_scores.loc[pd.to_numeric(fixed_scores["rich_entry_score"], errors="coerce") >= cutoff, "position_id"].astype(str))
        selected = fixed_trades.loc[fixed_trades["position_id"].astype(str).isin(keep_ids)].copy()
        rows.append({"cutoff": cutoff, "cutoff_offset": float(offset), **base.compute_trade_metrics(selected)})
    return pd.DataFrame(rows)


def topk_sensitivity(trades: pd.DataFrame, rule: FixedRule = EXPECTED_RULE) -> pd.DataFrame:
    rows = []
    for filter_id in ["top30", "top40", "top50"]:
        top_rule = FixedRule(**{**rule.__dict__, "filter_id": filter_id})
        group = filter_fixed_rule_rows(trades, top_rule, split="val_eval")
        rows.append({"filter_id": filter_id, **base.compute_trade_metrics(group)})
    return pd.DataFrame(rows)
```

- [ ] **Step 5: Run diagnostics tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_time_only_robustness_audit.py -q
```

Expected: all tests in this file pass.

---

### Task 3: Add Decision Logic And CLI

**Files:**
- Modify: `tests/test_time_only_robustness_audit.py`
- Modify: `ML/baseline/audit_time_only_robustness.py`

**Interfaces:**
- Produces:
  - `calendar_slices(trades: pd.DataFrame, rule: FixedRule) -> pd.DataFrame`.
  - `calendar_no_ml_baselines(trades: pd.DataFrame, rule: FixedRule) -> pd.DataFrame`.
  - `spread_stress_status() -> pd.DataFrame`.
  - `sequential_position_status() -> pd.DataFrame`.
  - `robustness_decision(selected_summary: dict[str, object], concentration: dict[str, object], side: pd.DataFrame, stricter_cutoff: pd.DataFrame, topk: pd.DataFrame, spread_stress: pd.DataFrame, sequential: pd.DataFrame) -> dict[str, object]`.
  - `run_audit(input_prefix: Path, output_prefix: Path) -> dict[str, object]`.
  - CLI: `./.venv/bin/python ML/baseline/audit_time_only_robustness.py --input-prefix ... --output-prefix ...`.

- [ ] **Step 1: Write failing decision test**

Append:

```python
def test_robustness_decision_requires_stress_and_catches_bad_side():
    selected_summary = {"n_trades": 660, "pf": 4.0, "bs_p05": 3.3, "pf_without_best_year": 3.5}
    concentration = {"n_years": 2, "effective_profit_years": 1.99, "best_year_share": 0.55}
    side = pd.DataFrame({"side": ["BUY", "SELL"], "n_trades": [330, 330], "mean_pnl_r": [0.2, 0.3], "pf": [2.0, 3.0]})
    stricter_cutoff = pd.DataFrame({"cutoff_offset": [0.0, 0.01], "pf": [4.0, 3.2], "n_trades": [660, 620]})
    topk = pd.DataFrame({"filter_id": ["top30", "top40", "top50"], "pf": [4.0, 3.4, 3.0], "n_trades": [660, 880, 1100]})
    spread_stress = pd.DataFrame({"status": ["NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS"]})
    sequential = pd.DataFrame({"status": ["NOT_RUN"]})

    result = audit.robustness_decision(selected_summary, concentration, side, stricter_cutoff, topk, spread_stress, sequential)
    assert result["decision"] == "REGIME_REFORMULATION_REQUIRED"
    assert "stress_costs_not_computable" in result["reasons"]
    assert "sequential_position_constraint_not_run" not in result["reasons"]
    assert "sequential_position_constraint_not_run" in result["disclosures"]

    bad_side = pd.DataFrame({"side": ["BUY", "SELL"], "n_trades": [620, 40], "mean_pnl_r": [0.2, -0.1], "pf": [3.0, 0.8]})
    result = audit.robustness_decision(selected_summary, concentration, bad_side, stricter_cutoff, topk, spread_stress, sequential)
    assert result["decision"] == "REGIME_REFORMULATION_REQUIRED"
```

- [ ] **Step 2: Implement decision and CLI**

Append:

```python
DECISION_GATE_CONFIG = {
    "min_bs_p05": 1.0,
    "min_pf_without_best_year": 1.0,
    "min_side_pf": 1.0,
    "min_side_n_trades": 30,
    "max_side_drawdown_r": 8.5,
    "min_stricter_cutoff_n_trades": 300,
    "stress_costs_required_for_slice_ok": True,
    "sequential_position_constraint_required_for_slice_ok": False,
}


def calendar_slices(trades: pd.DataFrame, rule: FixedRule = EXPECTED_RULE) -> pd.DataFrame:
    fixed_trades = filter_fixed_rule_rows(trades, rule, split="val_eval").copy()
    if fixed_trades.empty:
        return pd.DataFrame()
    fixed_trades["exit_dt"] = pd.to_datetime(fixed_trades["exit_time"], errors="coerce")
    fixed_trades["month"] = fixed_trades["exit_dt"].dt.month
    fixed_trades["quarter"] = fixed_trades["exit_dt"].dt.quarter
    rows = []
    for field in ["month", "quarter"]:
        for value, group in fixed_trades.groupby(field, dropna=False):
            rows.append({"calendar_field": field, "calendar_value": int(value) if pd.notna(value) else None, **base.compute_trade_metrics(group)})
    return pd.DataFrame(rows)


def calendar_no_ml_baselines(trades: pd.DataFrame, rule: FixedRule = EXPECTED_RULE) -> pd.DataFrame:
    no_ml_rule = FixedRule(**{**rule.__dict__, "filter_id": "M0_no_mask"})
    rows = filter_fixed_rule_rows(trades, no_ml_rule).copy()
    if rows.empty:
        return pd.DataFrame([{"status": "NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS", "reason": "M0_no_mask trades not found in saved artifacts"}])
    rows["exit_dt"] = pd.to_datetime(rows["exit_time"], errors="coerce")
    rows["month"] = rows["exit_dt"].dt.month
    rows["weekday"] = rows["exit_dt"].dt.weekday
    rows["hour"] = rows["exit_dt"].dt.hour
    out = [{"baseline": "all_no_ml_entries", **base.compute_trade_metrics(rows)}]
    for field in ["hour", "weekday", "month"]:
        for value, group in rows.groupby(field, dropna=False):
            out.append({"baseline": f"no_ml_{field}", "calendar_value": int(value) if pd.notna(value) else None, **base.compute_trade_metrics(group)})
    return pd.DataFrame(out)


def spread_stress_status() -> pd.DataFrame:
    return pd.DataFrame([{
        "status": "NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS",
        "reason": "saved trades contain realized pnl for canonical spread only; stress spread requires explicit resimulation",
    }])


def sequential_position_status() -> pd.DataFrame:
    return pd.DataFrame([{
        "status": "NOT_RUN",
        "reason": "plan records this diagnostic as missing unless an implementation adds position-overlap simulation",
    }])


def robustness_decision(
    selected_summary: dict[str, object],
    concentration: dict[str, object],
    side: pd.DataFrame,
    stricter_cutoff: pd.DataFrame,
    topk: pd.DataFrame,
    spread_stress: pd.DataFrame,
    sequential: pd.DataFrame,
) -> dict[str, object]:
    reasons: list[str] = []
    disclosures: list[str] = []
    gate = DECISION_GATE_CONFIG
    n_years = int(concentration.get("n_years") or 0)
    min_effective_years = max(1.5, 0.6 * n_years)
    if float(concentration.get("effective_profit_years") or 0.0) < min_effective_years:
        reasons.append("profit_concentration_fail")
    if float(selected_summary.get("bs_p05") or 0.0) < gate["min_bs_p05"]:
        reasons.append("block_bootstrap_fail")
    if float(selected_summary.get("pf_without_best_year") or 0.0) < gate["min_pf_without_best_year"]:
        reasons.append("pf_without_best_year_fail")
    if side.empty or (pd.to_numeric(side.get("mean_pnl_r"), errors="coerce") <= 0.0).any():
        reasons.append("side_mean_fail")
    if side.empty or (pd.to_numeric(side.get("pf"), errors="coerce") < gate["min_side_pf"]).any():
        reasons.append("side_pf_fail")
    if side.empty or (pd.to_numeric(side.get("n_trades"), errors="coerce") < gate["min_side_n_trades"]).any():
        reasons.append("side_sample_fail")
    if side.empty or (pd.to_numeric(side.get("max_drawdown_r"), errors="coerce") > gate["max_side_drawdown_r"]).any():
        reasons.append("side_drawdown_warning")
    if stricter_cutoff.empty or pd.to_numeric(stricter_cutoff.get("n_trades"), errors="coerce").min() < gate["min_stricter_cutoff_n_trades"]:
        reasons.append("stricter_cutoff_sample_fragile")
    if topk.empty:
        reasons.append("topk_sensitivity_missing")
    if not spread_stress.empty and str(spread_stress.iloc[0].get("status")) == "NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS":
        reasons.append("stress_costs_not_computable")
    if not sequential.empty and str(sequential.iloc[0].get("status")) == "NOT_RUN":
        if gate["sequential_position_constraint_required_for_slice_ok"]:
            reasons.append("sequential_position_constraint_not_run")
        else:
            disclosures.append("sequential_position_constraint_not_run")

    if any(reason in reasons for reason in ["block_bootstrap_fail", "pf_without_best_year_fail"]):
        decision = "REJECT_TIME_ONLY_AS_UNSTABLE"
    elif reasons:
        decision = "REGIME_REFORMULATION_REQUIRED"
    else:
        decision = "TIME_ONLY_ROBUSTNESS_SLICE_OK_FOR_NEXT_PROBE_DESIGN"
    return {"decision": decision, "reasons": reasons, "disclosures": disclosures, "decision_gate_config": gate}


def _selected_summary(summary: pd.DataFrame, rule: FixedRule = EXPECTED_RULE) -> dict[str, object]:
    fixed = filter_fixed_rule_rows(summary, rule, split="val_eval")
    if len(fixed) != 1:
        raise ValueError(f"fixed rule summary row expected once, got {len(fixed)}")
    return fixed.iloc[0].to_dict()


def run_audit(input_prefix: Path = DEFAULT_INPUT_PREFIX, output_prefix: Path = DEFAULT_OUTPUT_PREFIX) -> dict[str, object]:
    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    try:
        loaded = load_normalized_artifacts(input_prefix)
        artifact = loaded["artifact"]
        summary = loaded["summary"]
        trades = loaded["trades"]
        scores = loaded["scores"]
        contract = verify_fixed_rule_contract(artifact, EXPECTED_RULE)
    except Exception as exc:
        unknown = {
            "experiment": "time_only_robustness_audit",
            "status": "UNKNOWN",
            "verdict": "research_only",
            "locked_test": None,
            "decision": {"decision": "UNKNOWN_ARTIFACT_CONTRACT", "reasons": [str(exc)]},
            "contract_errors": [str(exc)],
        }
        output_prefix.with_suffix(".json").write_text(json.dumps(unknown, indent=2, ensure_ascii=False), encoding="utf-8")
        return unknown
    fixed_trades = filter_fixed_rule_rows(trades, EXPECTED_RULE, split="val_eval")
    yearly = metrics_by_period(fixed_trades, "Y")
    quarterly = metrics_by_period(fixed_trades, "Q")
    side = metrics_by_side(fixed_trades)
    year_side = metrics_by_year_side(fixed_trades)
    shift = score_shift(scores, EXPECTED_RULE)
    stricter_cutoff = stricter_cutoff_sensitivity(scores, trades, EXPECTED_RULE)
    topk = topk_sensitivity(trades, EXPECTED_RULE)
    calendar_no_ml = calendar_no_ml_baselines(trades, EXPECTED_RULE)
    calendar = calendar_slices(trades, EXPECTED_RULE)
    spread_stress = spread_stress_status()
    sequential = sequential_position_status()
    selected_summary = _selected_summary(summary, EXPECTED_RULE)
    concentration = profit_concentration(fixed_trades)
    bootstrap = sequential_block_bootstrap_pf(fixed_trades, seed=20260723, n_bootstrap=1000, block_size=20)
    selected_summary["bs_p05"] = bootstrap.get("bs_p05")
    decision = robustness_decision(selected_summary, concentration, side, stricter_cutoff, topk, spread_stress, sequential)

    yearly.to_csv(output_prefix.with_name(output_prefix.name + "_yearly.csv"), sep=";", index=False)
    quarterly.to_csv(output_prefix.with_name(output_prefix.name + "_quarterly.csv"), sep=";", index=False)
    side.to_csv(output_prefix.with_name(output_prefix.name + "_side.csv"), sep=";", index=False)
    year_side.to_csv(output_prefix.with_name(output_prefix.name + "_year_side.csv"), sep=";", index=False)
    shift.to_csv(output_prefix.with_name(output_prefix.name + "_score_shift.csv"), sep=";", index=False)
    stricter_cutoff.to_csv(output_prefix.with_name(output_prefix.name + "_stricter_cutoff.csv"), sep=";", index=False)
    topk.to_csv(output_prefix.with_name(output_prefix.name + "_topk_sensitivity.csv"), sep=";", index=False)
    calendar_no_ml.to_csv(output_prefix.with_name(output_prefix.name + "_calendar_no_ml_baselines.csv"), sep=";", index=False)
    calendar.to_csv(output_prefix.with_name(output_prefix.name + "_calendar_slices.csv"), sep=";", index=False)
    spread_stress.to_csv(output_prefix.with_name(output_prefix.name + "_spread_stress.csv"), sep=";", index=False)
    sequential.to_csv(output_prefix.with_name(output_prefix.name + "_sequential.csv"), sep=";", index=False)

    result = {
        "experiment": "time_only_robustness_audit",
        "status": "completed",
        "verdict": "research_only",
        "locked_test": "not_opened",
        "fixed_rule_contract": contract,
        "selected_summary": selected_summary,
        "profit_concentration": concentration,
        "block_bootstrap": bootstrap,
        "scope": "validation_artifact_robustness_slice",
        "multi_seed_status": "NOT_RUN",
        "provider_drift_status": "NOT_RUN",
        "transfer_status": "NOT_RUN",
        "stress_costs_status": str(spread_stress.iloc[0]["status"]) if not spread_stress.empty else "UNKNOWN",
        "sequential_position_constraint_status": str(sequential.iloc[0]["status"]) if not sequential.empty else "UNKNOWN",
        "decision": decision,
        "forbidden_interpretations": ["candidate", "tradable", "live_ready", "production", "permission_to_open_locked_test"],
        "artifacts": {
            "yearly_csv": str(output_prefix.with_name(output_prefix.name + "_yearly.csv")),
            "quarterly_csv": str(output_prefix.with_name(output_prefix.name + "_quarterly.csv")),
            "side_csv": str(output_prefix.with_name(output_prefix.name + "_side.csv")),
            "year_side_csv": str(output_prefix.with_name(output_prefix.name + "_year_side.csv")),
            "score_shift_csv": str(output_prefix.with_name(output_prefix.name + "_score_shift.csv")),
            "stricter_cutoff_csv": str(output_prefix.with_name(output_prefix.name + "_stricter_cutoff.csv")),
            "topk_sensitivity_csv": str(output_prefix.with_name(output_prefix.name + "_topk_sensitivity.csv")),
            "calendar_no_ml_baselines_csv": str(output_prefix.with_name(output_prefix.name + "_calendar_no_ml_baselines.csv")),
            "calendar_slices_csv": str(output_prefix.with_name(output_prefix.name + "_calendar_slices.csv")),
            "spread_stress_csv": str(output_prefix.with_name(output_prefix.name + "_spread_stress.csv")),
            "sequential_csv": str(output_prefix.with_name(output_prefix.name + "_sequential.csv")),
        },
    }
    output_prefix.with_suffix(".json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit robustness of the fixed normalized time_only winner.")
    parser.add_argument("--input-prefix", default=str(DEFAULT_INPUT_PREFIX))
    parser.add_argument("--output-prefix", default=str(DEFAULT_OUTPUT_PREFIX))
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    result = run_audit(Path(args.input_prefix), Path(args.output_prefix))
    print(json.dumps({"status": result["status"], "decision": result["decision"]}, ensure_ascii=False))
    if result.get("status") == "UNKNOWN":
        sys.exit(1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Run tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_time_only_robustness_audit.py -q
```

Expected: all tests pass.

---

### Task 4: Run Audit And Verify Artifacts

**Files:**
- Generate: `ML/reports/time_only_robustness_audit*`
- No code changes expected.

**Interfaces:**
- Consumes fixed normalized artifacts.
- Produces completed audit artifacts.

- [ ] **Step 1: Run the audit**

Run:

```bash
./.venv/bin/python ML/baseline/audit_time_only_robustness.py \
  --input-prefix ML/reports/fractal0_rich_entry_quality_normalized \
  --output-prefix ML/reports/time_only_robustness_audit
```

Expected: exit code `0`, printed JSON with `status=completed` and one allowed decision.

- [ ] **Step 2: Verify artifact contract**

Run:

```bash
./.venv/bin/python - <<'PY'
import json
from pathlib import Path

path = Path("ML/reports/time_only_robustness_audit.json")
data = json.loads(path.read_text(encoding="utf-8"))
allowed = {
    "TIME_ONLY_ROBUSTNESS_SLICE_OK_FOR_NEXT_PROBE_DESIGN",
    "REGIME_REFORMULATION_REQUIRED",
    "REJECT_TIME_ONLY_AS_UNSTABLE",
    "UNKNOWN_ARTIFACT_CONTRACT",
}
print({
    "locked_test": data.get("locked_test"),
    "verdict": data.get("verdict"),
    "decision": data.get("decision", {}).get("decision"),
})
raise SystemExit(
    0
    if data.get("locked_test") == "not_opened"
    and data.get("verdict") == "research_only"
    and data.get("decision", {}).get("decision") in allowed
    else 1
)
PY
```

Expected: `locked_test=not_opened`, `verdict=research_only`, decision in allowed set.

- [ ] **Step 3: Run full tests after Python changes**

Run:

```bash
./.venv/bin/python -m pytest tests/ -q
```

Expected: full test suite passes.

---

### Task 5: Write Report And Update Handoff

**Files:**
- Create: `docs/reports/2026-07-23-time-only-robustness-audit.md`
- Create: `docs/ML/audit_time_only_robustness.py.md`
- Modify: `docs/superpowers/roadmap.md`
- Modify: `CONTEXT_HANDOFF.md`
- Modify: `docs/ML/benchmark_fractal0_entry_quality_filter.py.md`
- Modify: `MODULE_INDEX.md`

**Interfaces:**
- Consumes: `ML/reports/time_only_robustness_audit.json` and CSV artifacts.
- Produces: final human-readable stage report and next active roadmap decision.

- [ ] **Step 1: Extract audit summary for report**

Run:

```bash
./.venv/bin/python - <<'PY'
import json
import pandas as pd

data = json.load(open("ML/reports/time_only_robustness_audit.json", encoding="utf-8"))
yearly = pd.read_csv("ML/reports/time_only_robustness_audit_yearly.csv", sep=";")
side = pd.read_csv("ML/reports/time_only_robustness_audit_side.csv", sep=";")
print("decision:", data["decision"])
print("selected_summary:", data["selected_summary"])
print("profit_concentration:", data["profit_concentration"])
print("yearly:")
print(yearly.to_string(index=False))
print("side:")
print(side.to_string(index=False))
PY
```

Expected: console output contains enough numbers to write the report without reopening `locked_test`.

- [ ] **Step 2: Create report**

Create `docs/reports/2026-07-23-time-only-robustness-audit.md` with this structure:

````markdown
# Time Only Robustness Audit

> **Дата**: 2026-07-23
> **Статус**: Completed
> **Вердикт**: research_only
> **locked_test**: not_opened
> **Decision**: <copy from ML/reports/time_only_robustness_audit.json>

## Уровень Этапа

Проверочный audit поверх validation artifacts, not `locked_test`.
`scope=validation_artifact_robustness_slice`.

Research-first disclosure:

```text
lifecycle_status: research_only
origin_bias: broad normalized rich-entry validation search
research_priority: проверить устойчивость fixed time_only rule перед новым probe design
current_search_budget: no new search, one fixed rule
cumulative_search_budget: inherited from normalized rich-entry search, 243 ranked configs plus diagnostic controls
next_probe_freeze: not created in this stage
allowed_max_verdict: research_only
forbidden_interpretations: candidate, tradable, live_ready, production, permission_to_open_locked_test
```

## Context

Аудит проверяет только заранее выбранный normalized winner:

```text
S2_fractal0_buffer_0_5_entry_floor_2 /
E3_open_pullback_1_0atr /
M0_no_mask /
X2_ml_opposite_any_p0_50 /
profile=time_only /
model=linear /
target=target_entry_ev_regression /
filter=top30
```

Нового перебора не было. `locked_test` не открыт.

## Multiple Testing Context

Этот audit не добавляет новый model/profile/target/filter search. Он наследует
origin bias из normalized rich-entry search, где winner был выбран после
широкой validation-партии. Поэтому метрики PF/PnL ниже не являются торговым
выводом и не дают права открывать `locked_test`.

## What Was Done

- Проверена неизменность fixed rule contract.
- Посчитаны yearly, quarterly, side и year-side slices.
- Посчитаны profit concentration, sequential block bootstrap, PF без лучшего года.
- Проверены score-shift между `val_select` и `val_eval`, stricter-cutoff sensitivity и top30/top40/top50 sensitivity.
- Добавлены calendar no-ML baselines, если они вычислимы из saved artifacts.
- Зафиксированы `spread_stress_status` и `sequential_position_constraint_status`.

## Changed Files

Перечислить все изменённые файлы и новые artifacts.

## Results

Вставить ключевые числа из JSON/CSV:

- aggregate PF;
- `BS_p05`;
- `pf_without_best_year`;
- `effective_profit_years`;
- `best_year_share`;
- BUY/SELL metrics;
- худший квартал/год;
- stricter-cutoff и top-k sensitivity;
- calendar no-ML baselines или `NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS`;
- `spread_stress_status`;
- `sequential_position_constraint_status`.

Рядом с любыми PF/PnL числами написать:

```text
allowed_max_verdict=research_only
not_trading_evidence_reason=validation artifact slice, locked_test not opened, inherited broad-search origin bias
forbidden_interpretations=candidate/tradable/live_ready/production/permission_to_open_locked_test
```

## Interpretation

Объяснить, является ли `time_only` устойчивым правилом, узким календарным режимом или нестабильной validation-находкой.

## Conclusions

Сформулировать решение из JSON и запретить выводы, которые не следуют из audit-slice.

## Limitations / Open Questions

- `multi_seed_status=NOT_RUN`.
- `provider_drift_status=NOT_RUN`.
- `transfer_status=NOT_RUN`.
- `locked_test_status=not_opened`.
- Если `spread_stress_status=NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS`, указать, что нужен отдельный stress-cost прогон перед повышением статуса.
- Если `sequential_position_constraint_status=NOT_RUN`, указать, что SeqPF не использовался как доказательство.

## Split Disclosure

- `train_core`: обучение исходной normalized модели.
- `val_select`: исходный выбор `score_cutoff_on_val_select`.
- `val_eval`: fixed-rule audit.
- `locked_test`: not_opened.
- Указать raw rows/events/trades по split из `split_manifest` и audit artifacts.

## Next Step

Если decision = `TIME_ONLY_ROBUSTNESS_SLICE_OK_FOR_NEXT_PROBE_DESIGN`: написать новый one-rule probe protocol без старого rich shortlist.

Если decision = `REGIME_REFORMULATION_REQUIRED`: написать план regime-filter reformulation без открытия `locked_test`.

Если decision = `REJECT_TIME_ONLY_AS_UNSTABLE`: закрыть rich/fractal entry-quality branch как superseded.

## Artifacts

- `ML/reports/time_only_robustness_audit.json`
- `ML/reports/time_only_robustness_audit_yearly.csv`
- `ML/reports/time_only_robustness_audit_quarterly.csv`
- `ML/reports/time_only_robustness_audit_side.csv`
- `ML/reports/time_only_robustness_audit_year_side.csv`
- `ML/reports/time_only_robustness_audit_score_shift.csv`
- `ML/reports/time_only_robustness_audit_stricter_cutoff.csv`
- `ML/reports/time_only_robustness_audit_topk_sensitivity.csv`
- `ML/reports/time_only_robustness_audit_calendar_no_ml_baselines.csv`
- `ML/reports/time_only_robustness_audit_calendar_slices.csv`
- `ML/reports/time_only_robustness_audit_spread_stress.csv`
- `ML/reports/time_only_robustness_audit_sequential.csv`

## Related Materials

- `docs/reports/2026-07-22-fractal0-rich-entry-quality-normalized-rerun.md`
- `docs/superpowers/roadmap.md`
- `docs/methodology/09-validation-freeze.md`
- `docs/methodology/11-robustness.md`
- `docs/methodology/16-reporting-audit.md`

## Verification

```bash
./.venv/bin/python -m pytest tests/test_time_only_robustness_audit.py -q
./.venv/bin/python -m pytest tests/ -q
```
````

- [ ] **Step 3: Update roadmap**

Modify `docs/superpowers/roadmap.md`:

- Change `ACTIVE: time_only robustness audit` to completed status with link to the new report.
- In the parked `time_only one-rule replication/probe` block, replace old cutoff `-0.026392849103777025` with normalized audited cutoff `-0.026718184259660646`, or mark the old value as superseded.
- Set the next `ACTIVE` branch based only on audit decision:
  - `TIME_ONLY_ROBUSTNESS_SLICE_OK_FOR_NEXT_PROBE_DESIGN` -> `time_only one-rule replication/probe`.
  - `REGIME_REFORMULATION_REQUIRED` -> `Regime filter reformulation`.
  - `REJECT_TIME_ONLY_AS_UNSTABLE` -> `Close rich/fractal entry-quality branch`.

- [ ] **Step 4: Update handoff**

Modify `CONTEXT_HANDOFF.md`:

- Record exact command used.
- Record decision.
- Record `locked_test=not_opened`.
- Record next plan to write or execute.

- [ ] **Step 5: Create module doc and add cross-link**

Create `docs/ML/audit_time_only_robustness.py.md`:

````markdown
# audit_time_only_robustness.py

## Назначение

Validation-slice audit для fixed normalized `time_only` winner. Скрипт читает
saved artifacts, не обучает модель, не выбирает новое правило и не открывает
`locked_test`.

## Команда

```bash
./.venv/bin/python ML/baseline/audit_time_only_robustness.py \
  --input-prefix ML/reports/fractal0_rich_entry_quality_normalized \
  --output-prefix ML/reports/time_only_robustness_audit
```

## Входы

- `ML/reports/fractal0_rich_entry_quality_normalized.json`
- `ML/reports/fractal0_rich_entry_quality_normalized_summary.csv`
- `ML/reports/fractal0_rich_entry_quality_normalized_trades.csv`
- `ML/reports/fractal0_rich_entry_quality_normalized_scores.csv`

## Выходы

Перечислить все `ML/reports/time_only_robustness_audit*` artifacts.

## Ограничения

- `locked_test=not_opened`.
- `scope=validation_artifact_robustness_slice`.
- `multi_seed_status=NOT_RUN`.
- `provider_drift_status=NOT_RUN`.
- `transfer_status=NOT_RUN`.
- Maximum verdict: `research_only`.
````

Append a short section to `docs/ML/benchmark_fractal0_entry_quality_filter.py.md`:

```markdown
## Time Only Robustness Audit

After normalized rich-entry rerun, `ML/baseline/audit_time_only_robustness.py`
audits the fixed `time_only / linear / target_entry_ev_regression / top30`
winner from saved normalized artifacts. It does not retrain, does not select a
new rule and does not open `locked_test`.
```

Update `MODULE_INDEX.md` with the new script and docs entry.

---

### Task 6: Stage Reporting Sync

**Files:**
- Modify: `CHANGELOG.md`
- Modify: `wiki/research/fractal-stop-research.md`
- Modify: `wiki/index.md`
- Modify: `wiki/log.md`
- Modify: `wiki/REPO_integrity.md`

**Interfaces:**
- Consumes completed report and artifacts.
- Produces synchronized project memory.

- [ ] **Step 1: Use required skill**

Before doing this task, use `stage-reporting`.

- [ ] **Step 2: Update changelog**

Add a new top entry to `CHANGELOG.md`:

```markdown
## [2026-07-23] — Time-only robustness audit

- Added `ML/baseline/audit_time_only_robustness.py` and `ML/reports/time_only_robustness_audit*`.
- Audited the fixed normalized `time_only / linear / target_entry_ev_regression / top30` winner without opening `locked_test`.
- Decision: `<copy exact decision from JSON>`.
```

- [ ] **Step 3: Update wiki and integrity**

Run the project wiki update commands documented in `wiki/README.md`. If the command is unavailable, update `wiki/research/fractal-stop-research.md`, `wiki/index.md`, `wiki/log.md` and `wiki/REPO_integrity.md` manually with the new report/artifacts.

- [ ] **Step 4: Final verification**

Run:

```bash
git status --short
./.venv/bin/python -m pytest tests/ -q
```

Expected: tests pass; changed files are limited to the audit script, tests, generated artifacts and documentation for this stage.

---

## Self-Review

- Spec coverage: covers roadmap `ACTIVE: time_only robustness audit`, keeps `locked_test` closed, avoids new search, checks yearly/quarterly/side/stricter-cutoff/top-k/score/calendar diagnostics, records missing stress/sequential/provider/multi-seed scope, and produces a next decision.
- Placeholder scan: no `TBD`, no generic "add tests" without concrete test code, no unspecified output paths.
- Type consistency: `FixedRule`, `EXPECTED_RULE`, `filter_fixed_rule_rows`, `run_audit`, and artifact paths are consistent across tasks.
