# Early Timeout hold_bars=12 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Проверить, можно ли заменить `ML_HoldBars=24` на `ML_HoldBars=12` для frozen `entry_path_v1_quantile` без изменения ML-сигнала и quantile rule.

**Architecture:** Отдельный validation-first benchmark поверх уже замороженного `entry_path_v1_quantile`: сначала выбирается verdict на validation, затем один frozen check на test. Python-контур сравнивает `true_ret_24_dir_atr` и `true_ret_12_dir_atr` на одном и том же наборе quantile-сделок; MT4 parity проверяется только если Python gate проходит.

**Tech Stack:** Python 3.11, pandas/numpy, pytest, существующие artifacts `ML/reports/entry_path_v1_quantile_selected_rule.json`, `ML/reports/entry_path_v1_quantile_robustness/seed_*/entry_path_v1_quantile_{validation,test}_predictions.csv`, MT4 tester logs, `statistics/signal_tracer.py`.

---

## Decision On Cross-Instrument Proposal

Предложение проверить похожий инструмент разумно как **robustness stress-test**, но не как замена forward validation.

Что оно проверяет:

- переносится ли execution-механизм `hold_bars=12` на близкий рынок;
- не является ли uplift чисто локальной особенностью текущего historical test;
- насколько чувствительна логика к другому spread/volatility/session profile.

Что оно не проверяет:

- не подтверждает post-decision forward performance на текущем production-инструменте;
- не заменяет strictly-forward CSV после даты production decision;
- не даёт права повышать статус `entry_path_v1_quantile` выше текущего `production-ready parallel mode`.

Правило для этого плана: cross-instrument проверка допустима только как отдельный optional stage после основного validation-first verdict. В основной gate она не входит, чтобы не смешивать два разных вопроса: time-forward robustness и market-transfer robustness.

## File Structure

### Read First

- `AGENTS.md`
- `CONTEXT_HANDOFF.md`
- `docs/reports/2026-04-13-pf-uplift-discovery.md`
- `docs/reports/2026-04-12-quantile-status-decision.md`
- `docs/superpowers/specs/2026-04-13-quantile-execution-improvement-design.md`
- `ML/reports/entry_path_v1_quantile_selected_rule.json`
- `ML/reports/entry_path_trade_filter_selected_rule.json`
- `ML/benchmark_entry_path_v1_quantile_filter.py`
- `ML/benchmark_entry_path_v1_quantile_n_boost.py`
- `API/export_entry_path_v1_quantile_signals.py`
- `MT/MQL4/Include/lib_ML_Signal.mqh`

### Files To Create

- `ML/benchmark_quantile_early_timeout.py` — Python benchmark for hold 24 vs hold 12 on frozen quantile-selected trades.
- `tests/test_benchmark_quantile_early_timeout.py` — unit and CLI tests for metrics, gate, multi-seed aggregation, and output files.
- `ML/reports/quantile_early_timeout/validation_summary.json` — validation result used to decide whether test may be evaluated.
- `ML/reports/quantile_early_timeout/test_summary.json` — frozen test result after validation pass.
- `ML/reports/quantile_early_timeout/per_seed_summary.csv` — seed-level validation/test comparison.
- `ML/reports/quantile_early_timeout/yearly_breakdown.csv` — yearly PF and trade counts.
- `ML/reports/quantile_early_timeout/run_metadata.json` — command inputs and frozen rule metadata.
- `docs/reports/2026-04-14-quantile-early-timeout.md` — final verdict report.

### Files To Modify After Python Gate Passes

- `MT/tester/$o$imple.ini` — set `ML_HoldBars=12` for parity run only after Python gate passes.
- `docs/MT/trading_strategy.md` — document the tested hold setting if final verdict is `execution_uplift_candidate`.
- `docs/MT/ml_signal_integration.md` — document MT4 settings if final verdict is accepted for productization.
- `CHANGELOG.md` — add result only after benchmark verdict exists.
- `CONTEXT_HANDOFF.md` — update current stage and next step.
- `docs/superpowers/roadmap.md` — update execution-uplift status.
- `wiki/research/execution-tracks.md`, `wiki/index.md`, `wiki/log.md`, `wiki/REPO_integrity.md` — update through wiki ingest/generate after report is written.

## Acceptance Rules

- The quantile signal source is frozen: no retraining, no rule search, no quantile threshold tuning.
- Validation is evaluated before test.
- Test is evaluated only if validation passes the gate.
- The same selected trade set is compared under hold 24 and hold 12.
- `hold_12` must satisfy `N_trades >= 30`, `PF > 2.0`, and `negative_year_slices = 0`.
- `hold_12` must beat or match `hold_24` on validation PF without materially reducing mean PnL stability.
- Multi-seed check must not show a seed-level collapse below `PF <= 1.0`.
- MT4 parity is required before changing production docs.
- Cross-instrument validation is optional and cannot override failure on the canonical instrument.

---

## Task 1: Metrics And Gate Helpers

**Files:**

- Create: `ML/benchmark_quantile_early_timeout.py`
- Create: `tests/test_benchmark_quantile_early_timeout.py`

- [ ] **Step 1.1: Write failing tests for hold metrics and gate**

Add to `tests/test_benchmark_quantile_early_timeout.py`:

```python
import math

import pandas as pd

from ML.benchmark_quantile_early_timeout import (
    compute_metrics,
    decide_hold12_gate,
)


def test_compute_metrics_counts_pf_from_named_pnl_column():
    frame = pd.DataFrame({"pnl_atr": [2.0, -1.0, 3.0, 0.0]})

    result = compute_metrics(frame, pnl_column="pnl_atr")

    assert result["n_trades"] == 4
    assert result["wins"] == 2
    assert result["losses"] == 1
    assert result["gross_profit"] == 5.0
    assert result["gross_loss"] == 1.0
    assert result["pf"] == 5.0
    assert result["win_rate"] == 0.5
    assert result["mean_pnl_atr"] == 1.0


def test_compute_metrics_returns_inf_pf_without_losses():
    frame = pd.DataFrame({"pnl_atr": [1.0, 2.0]})

    result = compute_metrics(frame, pnl_column="pnl_atr")

    assert result["pf"] == math.inf
    assert result["losses"] == 0


def test_decide_hold12_gate_passes_when_hold12_is_stable():
    result = decide_hold12_gate(
        hold24_pf=8.0,
        hold12_pf=10.0,
        hold12_n_trades=48,
        hold12_negative_year_slices=0,
        seed_pf_values=[9.0, 8.0, 7.5, 11.0, 6.0],
    )

    assert result == {"verdict": "gate_pass", "reasons": []}


def test_decide_hold12_gate_rejects_pf_collapse():
    result = decide_hold12_gate(
        hold24_pf=8.0,
        hold12_pf=0.9,
        hold12_n_trades=48,
        hold12_negative_year_slices=0,
        seed_pf_values=[9.0, 8.0, 7.5, 11.0, 6.0],
    )

    assert result["verdict"] == "gate_fail"
    assert "hold12_pf=0.9000 <= 2.0" in result["reasons"]
```

- [ ] **Step 1.2: Run tests to verify failure**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_quantile_early_timeout.py -q
```

Expected: `ModuleNotFoundError: No module named 'ML.benchmark_quantile_early_timeout'`.

- [ ] **Step 1.3: Implement metrics and gate helpers**

Create `ML/benchmark_quantile_early_timeout.py`:

```python
from __future__ import annotations

import math
from typing import Any

import pandas as pd


GATE_MIN_TRADES = 30
GATE_MIN_PF = 2.0
GATE_MAX_NEGATIVE_YEAR_SLICES = 0
GATE_MIN_SEED_PF = 1.0


def compute_metrics(frame: pd.DataFrame, pnl_column: str) -> dict[str, Any]:
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

    pnl = pd.to_numeric(frame[pnl_column], errors="raise").astype(float)
    wins = int((pnl > 0).sum())
    losses = int((pnl < 0).sum())
    gross_profit = float(pnl[pnl > 0].sum())
    gross_loss = float(-pnl[pnl < 0].sum())
    if gross_loss == 0.0 and gross_profit > 0.0:
        pf = math.inf
    elif gross_loss > 0.0:
        pf = gross_profit / gross_loss
    else:
        pf = 0.0
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


def decide_hold12_gate(
    *,
    hold24_pf: float | None,
    hold12_pf: float | None,
    hold12_n_trades: int,
    hold12_negative_year_slices: int,
    seed_pf_values: list[float],
) -> dict[str, Any]:
    reasons: list[str] = []
    if hold12_n_trades < GATE_MIN_TRADES:
        reasons.append(f"hold12_n_trades={hold12_n_trades} < {GATE_MIN_TRADES}")
    if hold12_pf is None or hold12_pf <= GATE_MIN_PF:
        value = "None" if hold12_pf is None else f"{hold12_pf:.4f}"
        reasons.append(f"hold12_pf={value} <= {GATE_MIN_PF}")
    if hold24_pf is not None and hold12_pf is not None and hold12_pf < hold24_pf:
        reasons.append(f"hold12_pf={hold12_pf:.4f} < hold24_pf={hold24_pf:.4f}")
    if hold12_negative_year_slices > GATE_MAX_NEGATIVE_YEAR_SLICES:
        reasons.append(
            f"hold12_negative_year_slices={hold12_negative_year_slices} > "
            f"{GATE_MAX_NEGATIVE_YEAR_SLICES}"
        )
    weak_seed_values = [value for value in seed_pf_values if value <= GATE_MIN_SEED_PF]
    if weak_seed_values:
        reasons.append(f"seed_pf_values_contain_pf<=1.0: {weak_seed_values}")
    return {"verdict": "gate_pass" if not reasons else "gate_fail", "reasons": reasons}
```

- [ ] **Step 1.4: Run tests**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_quantile_early_timeout.py -q
```

Expected: `4 passed`.

- [ ] **Step 1.5: Commit**

Run:

```bash
git add ML/benchmark_quantile_early_timeout.py tests/test_benchmark_quantile_early_timeout.py
git commit -m "quantile: add early timeout metric helpers"
```

---

## Task 2: Frozen Quantile Trade Selection

**Files:**

- Modify: `ML/benchmark_quantile_early_timeout.py`
- Modify: `tests/test_benchmark_quantile_early_timeout.py`

- [ ] **Step 2.1: Write failing test for frozen rule selection**

Add:

```python
from ML.benchmark_quantile_early_timeout import select_quantile_trades


def test_select_quantile_trades_uses_baseline_and_lb_rule():
    frame = pd.DataFrame(
        {
            "time": ["2023.01.01 00:00", "2023.01.01 01:00", "2023.01.01 02:00"],
            "signal": [1, 1, 1],
            "pred_ret_24_q10": [-1.0, -5.0, -1.0],
            "pred_ret_24_q90": [3.0, 1.0, 3.0],
            "true_ret_12_dir_atr": [1.0, 2.0, 3.0],
            "true_ret_24_dir_atr": [1.5, 2.5, 3.5],
        }
    )
    baseline_frame = pd.DataFrame(
        {
            "time": ["2023.01.01 00:00", "2023.01.01 01:00", "2023.01.01 02:00"],
            "signal": [1, 1, 1],
            "pred_ret_24_dir_atr": [0.5, 0.5, -0.5],
        }
    )
    rule = {
        "baseline_threshold": 0.0,
        "winner": {
            "rule": "lb_gt_m",
            "m": -3.0,
            "w": 10.0,
            "correction": 1.0,
        },
    }

    result = select_quantile_trades(frame, baseline_frame, rule)

    assert list(result["time"]) == ["2023.01.01 00:00"]
    assert list(result["pnl_hold12_atr"]) == [1.0]
    assert list(result["pnl_hold24_atr"]) == [1.5]
```

- [ ] **Step 2.2: Run test to verify failure**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_quantile_early_timeout.py::test_select_quantile_trades_uses_baseline_and_lb_rule -q
```

Expected: import failure for `select_quantile_trades`.

- [ ] **Step 2.3: Implement frozen selection**

Append imports and function:

```python
from ML.benchmark_entry_path_v1_quantile_filter import (
    apply_conformal_correction,
    attach_baseline_score,
    build_rule_mask,
)


def select_quantile_trades(
    frame: pd.DataFrame,
    baseline_frame: pd.DataFrame,
    selected_rule: dict[str, Any],
) -> pd.DataFrame:
    required_columns = {
        "time",
        "signal",
        "pred_ret_24_q10",
        "pred_ret_24_q90",
        "true_ret_12_dir_atr",
        "true_ret_24_dir_atr",
    }
    missing = required_columns.difference(frame.columns)
    if missing:
        raise ValueError(f"missing columns: {sorted(missing)}")

    winner = selected_rule["winner"]
    baseline_threshold = float(selected_rule["baseline_threshold"])
    working = attach_baseline_score(frame.copy(), baseline_frame.copy())
    working["baseline_selected"] = (
        (pd.to_numeric(working["signal"], errors="raise") != 0)
        & (pd.to_numeric(working["baseline_score"], errors="raise") >= baseline_threshold)
    )
    working = apply_conformal_correction(working, float(winner["correction"]))
    selected_mask = build_rule_mask(
        working,
        rule=str(winner["rule"]),
        m=float(winner["m"]),
        w=float(winner["w"]),
    )
    selected = working.loc[selected_mask].copy()
    selected["pnl_hold12_atr"] = pd.to_numeric(selected["true_ret_12_dir_atr"], errors="raise").astype(float)
    selected["pnl_hold24_atr"] = pd.to_numeric(selected["true_ret_24_dir_atr"], errors="raise").astype(float)
    return selected
```

- [ ] **Step 2.4: Run tests**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_quantile_early_timeout.py -q
```

Expected: all tests pass.

- [ ] **Step 2.5: Commit**

Run:

```bash
git add ML/benchmark_quantile_early_timeout.py tests/test_benchmark_quantile_early_timeout.py
git commit -m "quantile: select frozen early timeout trades"
```

---

## Task 3: Validation And Test Split Evaluation

**Files:**

- Modify: `ML/benchmark_quantile_early_timeout.py`
- Modify: `tests/test_benchmark_quantile_early_timeout.py`

- [ ] **Step 3.1: Write failing tests for yearly breakdown and split evaluation**

Add:

```python
from ML.benchmark_quantile_early_timeout import (
    build_yearly_breakdown,
    evaluate_split,
)


def test_build_yearly_breakdown_ignores_small_years_for_negative_count():
    frame = pd.DataFrame(
        {
            "time": ["2023.01.01 00:00", "2023.02.01 00:00", "2023.03.01 00:00", "2024.01.01 00:00"],
            "pnl_hold12_atr": [-1.0, -2.0, 1.0, -10.0],
            "pnl_hold24_atr": [1.0, 1.0, 1.0, -10.0],
        }
    )

    table, negative_years = build_yearly_breakdown(frame, min_year_trades=3)

    assert negative_years == 1
    assert list(table["year"]) == [2023, 2024]
    assert list(table["n_trades_hold12"]) == [3, 1]


def test_evaluate_split_compares_hold12_and_hold24():
    frame = pd.DataFrame(
        {
            "time": ["2023.01.01 00:00", "2023.02.01 00:00", "2023.03.01 00:00"],
            "pnl_hold12_atr": [2.0, -1.0, 3.0],
            "pnl_hold24_atr": [1.0, -1.0, 1.0],
        }
    )

    result = evaluate_split(frame, split="validation")

    assert result["split"] == "validation"
    assert result["hold12"]["pf"] == 5.0
    assert result["hold24"]["pf"] == 2.0
    assert result["negative_year_slices_hold12"] == 0
```

- [ ] **Step 3.2: Run tests to verify failure**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_quantile_early_timeout.py::test_evaluate_split_compares_hold12_and_hold24 -q
```

Expected: import failure for `evaluate_split`.

- [ ] **Step 3.3: Implement yearly breakdown and split evaluation**

Append:

```python
def build_yearly_breakdown(frame: pd.DataFrame, min_year_trades: int = 3) -> tuple[pd.DataFrame, int]:
    if frame.empty:
        return pd.DataFrame(
            columns=[
                "year",
                "n_trades_hold12",
                "pf_hold12",
                "mean_pnl_hold12_atr",
                "n_trades_hold24",
                "pf_hold24",
                "mean_pnl_hold24_atr",
            ]
        ), 0

    working = frame.copy()
    working["year"] = pd.to_datetime(working["time"], format="%Y.%m.%d %H:%M", errors="coerce").dt.year
    rows: list[dict[str, Any]] = []
    negative_years = 0
    for year, group in working.groupby("year", sort=True):
        hold12 = compute_metrics(group, "pnl_hold12_atr")
        hold24 = compute_metrics(group, "pnl_hold24_atr")
        if int(hold12["n_trades"]) >= min_year_trades:
            pf_value = hold12["pf"]
            if pf_value is not None and pf_value < 1.0:
                negative_years += 1
        rows.append(
            {
                "year": int(year),
                "n_trades_hold12": hold12["n_trades"],
                "pf_hold12": hold12["pf"],
                "mean_pnl_hold12_atr": hold12["mean_pnl_atr"],
                "n_trades_hold24": hold24["n_trades"],
                "pf_hold24": hold24["pf"],
                "mean_pnl_hold24_atr": hold24["mean_pnl_atr"],
            }
        )
    return pd.DataFrame(rows), negative_years


def evaluate_split(frame: pd.DataFrame, split: str, min_year_trades: int = 3) -> dict[str, Any]:
    yearly, negative_years = build_yearly_breakdown(frame, min_year_trades=min_year_trades)
    return {
        "split": split,
        "hold12": compute_metrics(frame, "pnl_hold12_atr"),
        "hold24": compute_metrics(frame, "pnl_hold24_atr"),
        "negative_year_slices_hold12": negative_years,
        "yearly": yearly.to_dict(orient="records"),
    }
```

- [ ] **Step 3.4: Run tests**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_quantile_early_timeout.py -q
```

Expected: all tests pass.

- [ ] **Step 3.5: Commit**

Run:

```bash
git add ML/benchmark_quantile_early_timeout.py tests/test_benchmark_quantile_early_timeout.py
git commit -m "quantile: evaluate early timeout splits"
```

---

## Task 4: CLI, Multi-Seed Run, And Artifacts

**Files:**

- Modify: `ML/benchmark_quantile_early_timeout.py`
- Modify: `tests/test_benchmark_quantile_early_timeout.py`
- Create output files under: `ML/reports/quantile_early_timeout/`

- [ ] **Step 4.1: Write failing CLI test**

Add:

```python
import json
from pathlib import Path

from ML.benchmark_quantile_early_timeout import main


def test_main_writes_summary_files(tmp_path: Path):
    predictions = tmp_path / "predictions.csv"
    predictions.write_text(
        "time;signal;pred_ret_24_q10;pred_ret_24_q90;true_ret_12_dir_atr;true_ret_24_dir_atr\n"
        "2023.01.01 00:00;1;-1.0;3.0;2.0;1.0\n"
        "2023.02.01 00:00;1;-1.0;3.0;-1.0;-1.0\n"
        "2023.03.01 00:00;1;-1.0;3.0;3.0;1.0\n",
        encoding="utf-8",
    )
    baseline = tmp_path / "baseline.csv"
    baseline.write_text(
        "time;signal;pred_ret_24_dir_atr\n"
        "2023.01.01 00:00;1;0.5\n"
        "2023.02.01 00:00;1;0.5\n"
        "2023.03.01 00:00;1;0.5\n",
        encoding="utf-8",
    )
    rule = tmp_path / "rule.json"
    rule.write_text(
        json.dumps(
            {
                "baseline_threshold": 0.0,
                "winner": {
                    "rule": "lb_gt_m",
                    "m": -3.0,
                    "w": 10.0,
                    "correction": 1.0,
                },
            }
        ),
        encoding="utf-8",
    )
    output_dir = tmp_path / "out"

    code = main(
        [
            "--validation-predictions",
            str(predictions),
            "--test-predictions",
            str(predictions),
            "--baseline-validation-predictions",
            str(baseline),
            "--baseline-test-predictions",
            str(baseline),
            "--selected-rule",
            str(rule),
            "--output-dir",
            str(output_dir),
        ]
    )

    assert code == 0
    assert (output_dir / "validation_summary.json").exists()
    assert (output_dir / "test_summary.json").exists()
    validation = json.loads((output_dir / "validation_summary.json").read_text(encoding="utf-8"))
    assert validation["split"] == "validation"
```

- [ ] **Step 4.2: Run test to verify failure**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_quantile_early_timeout.py::test_main_writes_summary_files -q
```

Expected: import failure for `main`.

- [ ] **Step 4.3: Implement CLI**

Add imports:

```python
import argparse
import json
from pathlib import Path
```

Append:

```python
def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def _load_predictions(path: str | Path) -> pd.DataFrame:
    return pd.read_csv(path, sep=";")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(_json_safe(payload), handle, indent=2, ensure_ascii=False, allow_nan=False)
        handle.write("\n")


def run_benchmark(
    *,
    validation_predictions: str | Path,
    test_predictions: str | Path,
    baseline_validation_predictions: str | Path,
    baseline_test_predictions: str | Path,
    selected_rule: str | Path,
    output_dir: str | Path,
) -> dict[str, Any]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    rule = json.loads(Path(selected_rule).read_text(encoding="utf-8"))

    validation_trades = select_quantile_trades(
        _load_predictions(validation_predictions),
        _load_predictions(baseline_validation_predictions),
        rule,
    )
    validation_summary = evaluate_split(validation_trades, split="validation")
    validation_gate = decide_hold12_gate(
        hold24_pf=validation_summary["hold24"]["pf"],
        hold12_pf=validation_summary["hold12"]["pf"],
        hold12_n_trades=validation_summary["hold12"]["n_trades"],
        hold12_negative_year_slices=validation_summary["negative_year_slices_hold12"],
        seed_pf_values=[],
    )
    validation_summary["gate"] = validation_gate

    test_trades = select_quantile_trades(
        _load_predictions(test_predictions),
        _load_predictions(baseline_test_predictions),
        rule,
    )
    test_summary = evaluate_split(test_trades, split="test")
    test_gate = decide_hold12_gate(
        hold24_pf=test_summary["hold24"]["pf"],
        hold12_pf=test_summary["hold12"]["pf"],
        hold12_n_trades=test_summary["hold12"]["n_trades"],
        hold12_negative_year_slices=test_summary["negative_year_slices_hold12"],
        seed_pf_values=[],
    )
    test_summary["gate"] = test_gate

    yearly = pd.DataFrame(validation_summary["yearly"] + test_summary["yearly"])
    yearly.to_csv(out / "yearly_breakdown.csv", sep=";", index=False)
    _write_json(out / "validation_summary.json", validation_summary)
    _write_json(out / "test_summary.json", test_summary)
    _write_json(
        out / "run_metadata.json",
        {
            "validation_predictions": str(validation_predictions),
            "test_predictions": str(test_predictions),
            "baseline_validation_predictions": str(baseline_validation_predictions),
            "baseline_test_predictions": str(baseline_test_predictions),
            "selected_rule": str(selected_rule),
            "output_dir": str(output_dir),
        },
    )
    return {"validation": validation_summary, "test": test_summary}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validation-predictions", required=True)
    parser.add_argument("--test-predictions", required=True)
    parser.add_argument("--baseline-validation-predictions", required=True)
    parser.add_argument("--baseline-test-predictions", required=True)
    parser.add_argument("--selected-rule", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args(argv)

    try:
        run_benchmark(
            validation_predictions=args.validation_predictions,
            test_predictions=args.test_predictions,
            baseline_validation_predictions=args.baseline_validation_predictions,
            baseline_test_predictions=args.baseline_test_predictions,
            selected_rule=args.selected_rule,
            output_dir=args.output_dir,
        )
    except (OSError, ValueError, KeyError, pd.errors.ParserError):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4.4: Run tests**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_quantile_early_timeout.py -q
```

Expected: all tests pass.

- [ ] **Step 4.5: Run canonical seed_007 benchmark**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m ML.benchmark_quantile_early_timeout \
  --validation-predictions ML/reports/entry_path_v1_quantile_robustness/seed_007/entry_path_v1_quantile_validation_predictions.csv \
  --test-predictions ML/reports/entry_path_v1_quantile_robustness/seed_007/entry_path_v1_quantile_test_predictions.csv \
  --baseline-validation-predictions ML/reports/entry_path_v1_validation_predictions.csv \
  --baseline-test-predictions ML/reports/entry_path_test_predictions.csv \
  --selected-rule ML/reports/entry_path_v1_quantile_selected_rule.json \
  --output-dir ML/reports/quantile_early_timeout
```

Expected: command exits `0`; JSON and CSV artifacts exist in `ML/reports/quantile_early_timeout/`.

- [ ] **Step 4.6: Commit**

Run:

```bash
git add ML/benchmark_quantile_early_timeout.py tests/test_benchmark_quantile_early_timeout.py ML/reports/quantile_early_timeout
git commit -m "quantile: benchmark early timeout candidate"
```

---

## Task 5: Multi-Seed Robustness

**Files:**

- Modify: `ML/benchmark_quantile_early_timeout.py`
- Modify: `tests/test_benchmark_quantile_early_timeout.py`
- Modify output: `ML/reports/quantile_early_timeout/per_seed_summary.csv`

- [ ] **Step 5.1: Write failing test for per-seed aggregation**

Add:

```python
from ML.benchmark_quantile_early_timeout import summarize_seed_results


def test_summarize_seed_results_builds_seed_table_and_gate_values():
    rows = [
        {"seed": 7, "split": "validation", "hold12_pf": 4.0, "hold24_pf": 3.0, "hold12_n_trades": 40},
        {"seed": 17, "split": "validation", "hold12_pf": 2.5, "hold24_pf": 2.0, "hold12_n_trades": 38},
    ]

    result = summarize_seed_results(rows)

    assert list(result["seed"]) == [7, 17]
    assert list(result["split"]) == ["validation", "validation"]
    assert list(result["hold12_pf"]) == [4.0, 2.5]
```

- [ ] **Step 5.2: Run test to verify failure**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_quantile_early_timeout.py::test_summarize_seed_results_builds_seed_table_and_gate_values -q
```

Expected: import failure for `summarize_seed_results`.

- [ ] **Step 5.3: Implement aggregation helper**

Append:

```python
def summarize_seed_results(rows: list[dict[str, Any]]) -> pd.DataFrame:
    columns = ["seed", "split", "hold12_pf", "hold24_pf", "hold12_n_trades"]
    return pd.DataFrame(rows, columns=columns)
```

- [ ] **Step 5.4: Extend CLI with `--root-dir` and `--seeds`**

Modify parser:

```python
parser.add_argument("--root-dir", default=None)
parser.add_argument("--seeds", default="")
```

Update `run_benchmark` signature:

```python
def run_benchmark(
    *,
    validation_predictions: str | Path,
    test_predictions: str | Path,
    baseline_validation_predictions: str | Path,
    baseline_test_predictions: str | Path,
    selected_rule: str | Path,
    output_dir: str | Path,
    root_dir: str | Path | None = None,
    seeds: list[int] | None = None,
) -> dict[str, Any]:
```

Inside `run_benchmark`, after writing single seed summaries, add this concrete seed iteration:

```python
    baseline_frames = {
        "validation": _load_predictions(baseline_validation_predictions),
        "test": _load_predictions(baseline_test_predictions),
    }
    seed_rows: list[dict[str, Any]] = []
    if root_dir is not None and seeds:
        root = Path(root_dir)
        for seed in seeds:
            seed_dir = root / f"seed_{seed:03d}"
            for split in ["validation", "test"]:
                seed_path = seed_dir / f"entry_path_v1_quantile_{split}_predictions.csv"
                seed_trades = select_quantile_trades(_load_predictions(seed_path), baseline_frames[split], rule)
                seed_summary = evaluate_split(seed_trades, split=split)
                seed_rows.append(
                    {
                        "seed": seed,
                        "split": split,
                        "hold12_pf": seed_summary["hold12"]["pf"],
                        "hold24_pf": seed_summary["hold24"]["pf"],
                        "hold12_n_trades": seed_summary["hold12"]["n_trades"],
                    }
                )
    summarize_seed_results(seed_rows).to_csv(out / "per_seed_summary.csv", sep=";", index=False)
```

And pass values from `main`:

```python
seed_values = [int(item) for item in args.seeds.split(",") if item]
run_benchmark(
    validation_predictions=args.validation_predictions,
    test_predictions=args.test_predictions,
    baseline_validation_predictions=args.baseline_validation_predictions,
    baseline_test_predictions=args.baseline_test_predictions,
    selected_rule=args.selected_rule,
    output_dir=args.output_dir,
    root_dir=args.root_dir,
    seeds=seed_values,
)
```

- [ ] **Step 5.5: Run tests**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_quantile_early_timeout.py -q
```

Expected: all tests pass.

- [ ] **Step 5.6: Run canonical multi-seed benchmark**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m ML.benchmark_quantile_early_timeout \
  --validation-predictions ML/reports/entry_path_v1_quantile_robustness/seed_007/entry_path_v1_quantile_validation_predictions.csv \
  --test-predictions ML/reports/entry_path_v1_quantile_robustness/seed_007/entry_path_v1_quantile_test_predictions.csv \
  --baseline-validation-predictions ML/reports/entry_path_v1_validation_predictions.csv \
  --baseline-test-predictions ML/reports/entry_path_test_predictions.csv \
  --selected-rule ML/reports/entry_path_v1_quantile_selected_rule.json \
  --root-dir ML/reports/entry_path_v1_quantile_robustness \
  --seeds 7,17,42,77,123 \
  --output-dir ML/reports/quantile_early_timeout
```

Expected: `per_seed_summary.csv` contains 10 rows: 5 seeds × 2 splits.

- [ ] **Step 5.7: Commit**

Run:

```bash
git add ML/benchmark_quantile_early_timeout.py tests/test_benchmark_quantile_early_timeout.py ML/reports/quantile_early_timeout/per_seed_summary.csv
git commit -m "quantile: add early timeout multi-seed check"
```

---

## Task 6: MT4 Parity Check

**Files:**

- Modify only after Python gate pass: `MT/tester/$o$imple.ini`
- Read: `MT/MQL4/Include/lib_ML_Signal.mqh`
- Read/run: `statistics/signal_tracer.py`
- Create/update: MT4 tester log artifact and reconciliation output

- [ ] **Step 6.1: Inspect current MT4 hold setting**

Run:

```bash
rg "ML_HoldBars|iSignal|ML_UseScoreFilter" MT/tester MT/MQL4/Include/lib_ML_Signal.mqh docs/MT
```

Expected: current quantile parity configuration is visible, including `ML_HoldBars=24` or equivalent tester setting.

- [ ] **Step 6.2: Set tester hold bars to 12 for parity run**

Edit `MT/tester/$o$imple.ini` only for the parity branch so that quantile mode uses:

```ini
ML_HoldBars=12
ML_AllowReversal=0
ML_UseScoreFilter=0
```

- [ ] **Step 6.3: Run MT4 tester manually**

Run the MT4 tester for the same period used by the previous quantile parity check.

Expected:

- tester completes without EA errors;
- log contains quantile trade open/close events;
- no unexpected `Position blocked` surge;
- timeout closes reflect 12-bar hold.

- [ ] **Step 6.4: Run signal tracer reconciliation**

Run the existing tracer command pattern used in the previous MT4 parity stage, adjusted for the new tester log path.

Expected:

- Python selected signals and MT4 opened trades match by `(time, signal, direction)` for the tester period;
- mismatches are explained by tester period truncation only;
- PnL direction matches for all reconciled trades.

- [ ] **Step 6.5: Commit parity config and reconciliation artifacts only if verdict remains valid**

Run:

```bash
git add MT/tester/$o$imple.ini statistics/reports docs/reports
git commit -m "quantile: verify early timeout mt4 parity"
```

If MT4 parity fails, do not commit production docs; record the failure in the verdict report.

---

## Task 7: Verdict Report And Project Memory

**Files:**

- Create: `docs/reports/2026-04-14-quantile-early-timeout.md`
- Modify: `CHANGELOG.md`
- Modify: `CONTEXT_HANDOFF.md`
- Modify: `docs/superpowers/roadmap.md`
- Modify through wiki ingest: `wiki/research/execution-tracks.md`, `wiki/index.md`, `wiki/log.md`, `wiki/REPO_integrity.md`

- [ ] **Step 7.1: Write verdict report**

Before writing, inspect the artifact values:

```bash
sed -n '1,220p' ML/reports/quantile_early_timeout/validation_summary.json
sed -n '1,220p' ML/reports/quantile_early_timeout/test_summary.json
head -n 20 ML/reports/quantile_early_timeout/per_seed_summary.csv
head -n 40 ML/reports/quantile_early_timeout/yearly_breakdown.csv
```

Create `docs/reports/2026-04-14-quantile-early-timeout.md` with concrete metrics from those artifacts. The report must include these sections:

```markdown
# Quantile Early Timeout hold_bars=12

> **Date**: 2026-04-14
> **Status**: Completed
> **Goal**: Проверить `ML_HoldBars=12` для frozen `entry_path_v1_quantile`

## Context

Baseline `entry_path_v1_quantile` uses frozen rule `lb_gt_m_q35` and historical test PF `8.178675196069868` at hold 24.

## Method

- Signal source frozen.
- Quantile rule frozen.
- Validation evaluated before test.
- Hold 12 compared against hold 24 on the same selected trades.
- Multi-seed robustness checked on seeds `7, 17, 42, 77, 123`.
- MT4 parity checked only after Python gate pass.

## Results

Report the exact validation and test values for:

- hold 24: N, PF, win_rate, mean_pnl_atr, negative_year_slices.
- hold 12: N, PF, win_rate, mean_pnl_atr, negative_year_slices.
- multi-seed: per-seed PF table and minimum hold12 PF.
- MT4 parity: trade count, matched trade count, PF, win_rate, and mismatch explanation.

## Verdict

State exactly one:

- `execution_uplift_candidate`
- `no_execution_uplift`

## Cross-Instrument Note

Cross-instrument testing is useful as a separate robustness stress-test, but it does not replace forward validation on the production instrument. If this stage passes, a follow-up plan may test EURUSD or another highly correlated instrument using the same frozen data contract and no threshold retuning on test.
```

- [ ] **Step 7.2: Update `CHANGELOG.md`**

Add a `2026-04-14` entry only if the benchmark produced a real verdict. Include concrete metric values; do not leave any metric unspecified.

```markdown
## [2026-04-14] — Quantile early timeout verdict

### Добавлено
- `ML/benchmark_quantile_early_timeout.py`: validation-first benchmark для `ML_HoldBars=12` поверх frozen `entry_path_v1_quantile`.

### Результаты
- Validation result for hold 12 vs hold 24.
- Frozen test result for hold 12 vs hold 24.
- Multi-seed minimum PF and weak seed count.
- MT4 parity result or explicit statement that MT4 parity was not run because Python gate failed.

### Вывод
- Verdict: `execution_uplift_candidate` or `no_execution_uplift`.
```

- [ ] **Step 7.3: Update `CONTEXT_HANDOFF.md` and roadmap**

Update:

- current stage;
- latest report;
- next step;
- open risks;
- PF uplift shortlist status.

- [ ] **Step 7.4: Update wiki**

Use `.codex/skills/wiki/SKILL.md` and run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python wiki/wiki.py generate
```

Expected:

- `wiki/research/execution-tracks.md` includes the early-timeout verdict;
- `wiki/index.md` still lists correct coverage;
- `wiki/log.md` has an append-only operation entry;
- `wiki/REPO_integrity.md` regenerates.

- [ ] **Step 7.5: Run verification**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_quantile_early_timeout.py -q
/home/hohla/git/SoSimple/.venv/bin/python wiki/wiki.py verify
```

Expected:

- benchmark tests pass;
- wiki verify exits `0`.

- [ ] **Step 7.6: Commit**

Run:

```bash
git add docs/reports/2026-04-14-quantile-early-timeout.md CHANGELOG.md CONTEXT_HANDOFF.md docs/superpowers/roadmap.md wiki
git commit -m "docs: record quantile early timeout verdict"
```

---

## Optional Follow-Up: Cross-Instrument Robustness Stress-Test

This follow-up must be a separate plan, not part of the hold-12 gate.

Recommended scope:

- choose one instrument only, preferably the closest market by structure and available data quality;
- rebuild the same labeled dataset contract for that instrument;
- run frozen `entry_path_v1_quantile` inference if feature schema is identical;
- do not tune thresholds on the new test set;
- compare hold 24 vs hold 12 as transfer robustness, not as production validation;
- report verdict as `transfer_supported`, `transfer_inconclusive`, or `transfer_failed`.

Critical warning:

- A correlated instrument can still have different spread, session liquidity, volatility tails, and broker execution behavior.
- Passing cross-instrument does not confirm future performance on the original instrument.
- Failing cross-instrument does not automatically invalidate the production instrument, but it lowers confidence in mechanism universality.
