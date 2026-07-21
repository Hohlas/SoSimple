# Fractal0 Entry Exit Grid Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Построить исследовательский runner, который проверяет исполнимые отложенные входы около `fractal0_price`, deterministic exit и ML-exit, считает PnL/PF с издержками и пишет полный audit artifact без открытия `locked_test`.

**Architecture:** Один новый runner строит сделки из существующего `fractal0_price` entry-preflight, применяет единую bid/ask execution convention, симулирует раскрытую entry/exit/mask сетку и выбирает winner только на `val_select`. ML-exit обучается отдельным внутренним слоем на `train_core`, но торговые threshold, entry, exit и mask выбираются только на `val_select`; итог проверяется на `val_eval` без изменения правила. Проверка на новом инструменте не входит в этот план.

**Tech Stack:** Python 3.10+, pandas, numpy, scikit-learn ExtraTrees/HistGradientBoosting, pytest, существующие `ML/baseline/benchmark_fractal0_price_entry_mechanics.py`, `ML/baseline/diagnose_stage4_5_exit_mechanics.py`, `ML/baseline/benchmark_entry_based_movement_filter_freeze.py`, `./.venv/bin/python`.

## Global Constraints

- Работать в текущей ветке; worktree запрещён.
- Использовать `./.venv/bin/python` для всех Python-команд.
- `locked_test` не открывать.
- Уровень этапа: `research_scan`.
- `allowed_max_verdict = research_only`.
- `research_hint` ниже `research_hypothesis`: метрики интересные, но не хватает сделок, коррекции перебора или исполнимого контракта.
- Проверка на новом инструменте или таймфрейме не входит в этот этап.
- Все project CSV из `DATA/` читать с `sep=";"`; report CSV из `ML/reports/` читать с их фактическим separator preflight-а.
- Используются только отложенные ордера.
- Сторона сделки: `fractal0.dir == -1 -> BUY`, `fractal0.dir == 1 -> SELL`.
- Старые `up_*`/`dn_*` от `fractal0_price` не использовать как торговую разметку.
- `train_core` используется только для обучения моделей и инженерной отладки pipeline.
- `val_select` выбирает одну торговую конфигурацию из заранее раскрытой сетки.
- `val_eval` проверяет выбранную конфигурацию без изменения правила.
- `diagnostic_holdout` и `low_n_disclosure` только disclosure.
- OHLC price convention: `ohlc_price_type = bid`.
- Spread convention: `spread = full bid-ask spread`.
- `canonical_spread = 0.20`; `stress_spread = 0.40`; zero-spread не участвует в gates.
- BUY limit заполняется, если `low_bid + spread <= limit_price`.
- SELL limit заполняется, если `high_bid >= limit_price`.
- BUY закрывается по Bid.
- SELL закрывается по Ask, то есть OHLC для exit сдвигается на `+spread`.
- Эта BUY/SELL fill/exit convention является offline OHLC simulation; это не MT4 tester parity и не доказательство broker execution.
- `same_bar_tp_sl_policy = SL first`.
- Считать `ambiguous_same_bar_rate`; если у winner rate `> 0.05`, статус не выше `research_hint`, если `> 0.10`, результат не выше `diagnostic_only`.
- `timeout_policy = close at next executable Open after timeout decision`.
- `R = abs(entry_effective_price - protective_stop_price)`.
- `protective_stop_atr = 0.5`; protective stop не подбирается в первой партии.
- No-fill учитывается в `no_fill_rate`, но не входит в PF/PnL сделок.
- Любой `target_exit_*` является future-derived и не попадает во входные признаки.
- Если сетка больше `10` конфигураций, результат без отдельного `val_eval` или permutation-test с повторением выбора winner не выше `research_hint`.
- Gate A для `research_hypothesis`: PF `>= 1.50`, `BS_p05 >= 1.10`, stress PF `>= 1.20`, минимум `300` сделок, минимум `50` сделок в активном году, не больше одного отрицательного года, PF без лучшего года `>= 1.10`, BUY/SELL раскрыты.
- Gate B для сильной локальной системы: PF `>= 2.00`, `BS_p05 >= 1.30`, stress PF `>= 1.50`, средний `pnl_r > 0`, PF без лучшего года `>= 1.30`, `effective_profit_years >= max(1.5, 0.6 * n_years)`, минимум `3` активных года или заранее заданные окна.
- Если сделок меньше `300`, статус не выше `research_hint`.
- Если `M1_frozen_movement_top5` улучшает PF, но нет absolute live cutoff, winner не может быть финальной системой.
- `stress_spread` не участвует в выборе winner; он используется только как stress-gate/disclosure после canonical-spread selection.
- Агент не выполняет `git commit` без явной просьбы пользователя; checkpoint commits в задачах ниже являются optional.
- После Python-изменений запускать focused pytest; перед закрытием плана запускать `./.venv/bin/python -m pytest tests/ -q`.

---

## Research Contract

**Hypothesis:** Отложенный вход около `fractal0_price`, дополненный чувствительным exit-rule и опциональной frozen movement mask, может дать торговую постановку с PF выше простого fixed-exit baseline.

**Decision unit:** заполненная или незаполненная отложенная заявка, построенная из одной entry-based строки.

**Entry grid:**

| ID | Contract |
|---|---|
| `E0_selected_zone_edge` | `zone_edge / 0.5 ATR / lag 6 / H3 / spread 0.2` |
| `E1_simple_limit_at_fractal0` | `limit_at_fractal0 / 0.0 ATR / lag 6 / H3 / spread 0.2` |
| `E2_open_pullback_0_5atr` | BUY limit ниже `calculation_open` на `0.5 ATR`, SELL limit выше `calculation_open` на `0.5 ATR` |
| `E3_open_pullback_1_0atr` | BUY limit ниже `calculation_open` на `1.0 ATR`, SELL limit выше `calculation_open` на `1.0 ATR` |

`calculation_open` — `Open` бара сразу после `Close`, на котором `fractal0` считается сформированным и доступны расчёты.

**Mask grid:**

| ID | Contract |
|---|---|
| `M0_no_mask` | все заполненные entry-события |
| `M1_frozen_movement_top5` | `simple_combined / extra_trees_small / H3 / top_fraction=0.05` из `ML/reports/entry_based_movement_filter_freeze.json` и `ML/reports/entry_based_movement_filter_freeze_scores.csv` |

**Exit grid:**

| Family | Count | Parameters |
|---|---:|---|
| `X0_fixed_r_0_7` | 1 | TP `0.7R`, fixed SL |
| `X1_ml_opposite_strong` | 3 | `prob_threshold = 0.55 / 0.65 / 0.75` |
| `X2_ml_opposite_any` | 3 | `prob_threshold = 0.50 / 0.55 / 0.60` |
| `X3_ml_hold_close` | 3 | `prob_threshold = 0.50 / 0.60 / 0.70` |
| `X4_ml_movement_exhaustion` | 3 | `prob_threshold = 0.55 / 0.65 / 0.75` |
| `X5_fixed_sl_ml_profit_exit` | 6 | `model = hold_close / movement_exhaustion`, `prob_threshold = 0.55 / 0.65 / 0.75`, close only if `unrealized_pnl_r >= 0` |
| `X6_trail_atr_grid` | 16 | `trail_distance_atr = 0.2 / 2 / 3 / 5`, `activation_atr = 0 / 1 / 2 / 3` |
| `X7_time_exit_grid` | 4 | `hold_bars = 1 / 2 / 6 / 12` |
| `X8_profit_giveback` | 9 | `giveback_fraction = 0.30 / 0.50 / 0.70`, `activation_atr = 1 / 2 / 3` |

**Search budget:**

```text
4 entry rules x 2 mask states x 48 exit configurations = 384 canonical-spread selection cells
384 stress-spread cells are disclosure/stress, not winner selection
ML-exit model jobs = 4 target families x 3 seeds = 12 training jobs
permutation correction = 200 repeats of the val_select selection policy
```

**Allowed verdicts:**

- `research_hypothesis`;
- `research_hint`;
- `research_only`;
- `diagnostic_only`;
- `reject`.

Forbidden verdicts: `candidate`, `tradable`, `live-ready`, `production`, `ready_for_locked_test`.

## Preflight Contract

Перед Task 1 runner обязан проверить входы и остановиться с понятной ошибкой,
если артефакт отсутствует или несовместим.

**Required input artifacts:**

| ID | Path | Role | Required columns/keys |
|---|---|---|---|
| `ohlc` | `DATA/XAUUSD_H1_OHLC.csv` | H1 OHLC, offline bid convention | `time`, `open`, `high`, `low`, `close`, `atr14`; read with `sep=";"` |
| `train_core` | `DATA/Nero_XAUUSD_train_labeled.csv` | train rows for ML-exit models | `time`, `ATR`, `fractal0`; read with `sep=";"` |
| `validation` | `DATA/Nero_XAUUSD_validation_labeled.csv` | source rows split into `val_select` and `val_eval` | `time`, `ATR`, `fractal0`; read with `sep=";"` |
| `movement_freeze_json` | `ML/reports/entry_based_movement_filter_freeze.json` | frozen mask contract | `verdict`, `locked_test`, `frozen_rule`, `scores_csv` |
| `movement_freeze_scores` | `ML/reports/entry_based_movement_filter_freeze_scores.csv` | M1 mask scores | `split`, `split_row_id`, `time`, `year`, `score`, `entry_movement_3`, `selected` |

Preflight outputs written to JSON:

```text
input_artifacts
input_artifact_hashes
preflight_status
preflight_errors
csv_separator_contract
split_role_manifest
movement_mask_coverage
```

If `movement_freeze_scores` is missing but `movement_freeze_json.scores_csv`
points to an existing file, use that path and record
`input_path_resolution = from_freeze_json_scores_csv`. If both are missing,
abort before matrix execution.

## Files

**Create**

- `ML/baseline/benchmark_fractal0_entry_exit_grid.py` — основной runner.
- `tests/test_fractal0_entry_exit_grid.py` — тесты конфигурации, исполнения, exit, метрик, resume и selection.
- `docs/ML/benchmark_fractal0_entry_exit_grid.py.md` — документация runner-а и команд запуска.
- `docs/reports/2026-07-20-fractal0-entry-exit-grid.md` — итоговый отчёт после полного прогона.

**Generated**

- `ML/reports/fractal0_entry_exit_grid.json`
- `ML/reports/fractal0_entry_exit_grid_summary.csv`
- `ML/reports/fractal0_entry_exit_grid_trades.csv`
- `ML/reports/fractal0_entry_exit_grid_yearly.csv`
- `ML/reports/fractal0_entry_exit_grid_spread_stress.csv`
- `ML/reports/fractal0_entry_exit_grid_attribution.csv`
- `ML/reports/fractal0_entry_exit_grid_permutation.csv`
- `ML/reports/fractal0_entry_exit_grid_progress.json`

`ML/reports/fractal0_entry_exit_grid.json` must contain:

```text
input_artifacts
input_artifact_hashes
rows_by_split_before_after_mask
fill_rate_by_entry
ambiguous_same_bar_rate
ml_feature_columns_used
ml_target_positive_rate_by_split
current_search_budget
cumulative_search_budget
exact_grid
multiple_testing_correction
selected_winner
val_select_winner_metrics
val_eval_winner_metrics
stress_spread
attribution_status
forbidden_interpretations
allowed_max_verdict
locked_test
```

**Modify after stage completion**

- `docs/superpowers/roadmap.md`
- `CONTEXT_HANDOFF.md`
- `CHANGELOG.md`, if the result changes project knowledge
- wiki files only through the project wiki/stage-reporting flow

---

### Task 1: Config, Grid Registry, Hash, Resume Skeleton

**Files:**
- Create: `ML/baseline/benchmark_fractal0_entry_exit_grid.py`
- Create: `tests/test_fractal0_entry_exit_grid.py`

**Interfaces:**
- Produces: `Fractal0EntryExitGridConfig`
- Produces: `entry_grid() -> list[dict[str, object]]`
- Produces: `exit_grid() -> list[dict[str, object]]`
- Produces: `mask_grid() -> list[dict[str, object]]`
- Produces: `expanded_grid() -> list[dict[str, object]]`
- Produces: `stable_json_hash(payload: dict[str, object]) -> str`
- Produces: `run_config_hash(config: dict[str, object]) -> str`
- Produces: `resume_key(run: dict[str, object]) -> str`
- Produces: `load_progress(path: Path, expected_hash: str) -> dict[str, object]`
- Produces: `write_progress_atomic(path: Path, progress: dict[str, object]) -> None`
- Produces: `preflight_inputs(config: Fractal0EntryExitGridConfig) -> dict[str, object]`
- Produces: `sha256_file(path: Path) -> str`

- [ ] **Step 1: Write failing tests**

Add these tests to `tests/test_fractal0_entry_exit_grid.py`:

```python
from pathlib import Path

import pytest

import ML.baseline.benchmark_fractal0_entry_exit_grid as runner


def test_grid_has_disclosed_size_and_required_controls():
    entries = runner.entry_grid()
    exits = runner.exit_grid()
    masks = runner.mask_grid()
    grid = runner.expanded_grid()

    assert [item["entry_id"] for item in entries] == [
        "E0_selected_zone_edge",
        "E1_simple_limit_at_fractal0",
        "E2_open_pullback_0_5atr",
        "E3_open_pullback_1_0atr",
    ]
    assert len(exits) == 48
    assert {item["exit_id"] for item in exits} >= {
        "X0_fixed_r_0_7",
        "X6_trail_atr_0_2_activation_0",
        "X6_trail_atr_5_activation_3",
        "X7_time_1",
        "X7_time_12",
    }
    assert [item["mask_id"] for item in masks] == ["M0_no_mask", "M1_frozen_movement_top5"]
    assert len(grid) == 384


def test_hash_is_stable_and_resume_key_ignores_runtime_order():
    payload = {"b": 2, "a": {"x": 1}}
    assert runner.stable_json_hash(payload) == runner.stable_json_hash({"a": {"x": 1}, "b": 2})

    left = {"entry_id": "E1", "exit_id": "X0", "mask_id": "M0", "spread": 0.2}
    right = {"spread": 0.2, "mask_id": "M0", "exit_id": "X0", "entry_id": "E1"}
    assert runner.resume_key(left) == runner.resume_key(right)


def test_load_progress_rejects_hash_mismatch(tmp_path: Path):
    path = tmp_path / "progress.json"
    runner.write_progress_atomic(path, {"run_config_hash": "old", "completed": {}})

    with pytest.raises(ValueError, match="run_config_hash mismatch"):
        runner.load_progress(path, expected_hash="new")


def test_preflight_reports_missing_input_with_clear_label(tmp_path: Path):
    config = runner.Fractal0EntryExitGridConfig(
        ohlc_path=str(tmp_path / "missing_ohlc.csv"),
        train_path=str(tmp_path / "train.csv"),
        validation_path=str(tmp_path / "validation.csv"),
        movement_freeze_json=str(tmp_path / "freeze.json"),
        movement_freeze_scores=str(tmp_path / "scores.csv"),
    )

    result = runner.preflight_inputs(config)

    assert result["status"] == "FAIL"
    assert any(item["id"] == "ohlc" for item in result["errors"])
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_entry_exit_grid.py -q
```

Expected: import failure because `ML.baseline.benchmark_fractal0_entry_exit_grid` does not exist.

- [ ] **Step 3: Implement config and grid registry**

Create `ML/baseline/benchmark_fractal0_entry_exit_grid.py` with these public objects:

```python
from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORTS_DIR = PROJECT_ROOT / "ML" / "reports"


@dataclasses.dataclass(frozen=True)
class Fractal0EntryExitGridConfig:
    experiment: str = "fractal0_entry_exit_grid"
    lifecycle_status: str = "research_scan"
    allowed_max_verdict: str = "research_only"
    locked_test: str = "not_opened"
    canonical_spread: float = 0.20
    stress_spread: float = 0.40
    protective_stop_atr: float = 0.5
    same_bar_tp_sl_policy: str = "SL first"
    default_threads: int = 24
    permutation_repeats: int = 200
    permutation_seed: int = 20260720
    output_prefix: str = "ML/reports/fractal0_entry_exit_grid"
    movement_freeze_json: str = "ML/reports/entry_based_movement_filter_freeze.json"
    movement_freeze_scores: str = "ML/reports/entry_based_movement_filter_freeze_scores.csv"
    ohlc_path: str = "DATA/XAUUSD_H1_OHLC.csv"
    train_path: str = "DATA/Nero_XAUUSD_train_labeled.csv"
    validation_path: str = "DATA/Nero_XAUUSD_validation_labeled.csv"


CONFIG = Fractal0EntryExitGridConfig()


def entry_grid() -> list[dict[str, object]]:
    return [
        {"entry_id": "E0_selected_zone_edge", "entry_mode": "zone_edge", "anchor": "fractal0_price", "zone_atr": 0.5, "lag_bars": 6, "horizon": 3},
        {"entry_id": "E1_simple_limit_at_fractal0", "entry_mode": "limit_at_fractal0", "anchor": "fractal0_price", "zone_atr": 0.0, "lag_bars": 6, "horizon": 3},
        {"entry_id": "E2_open_pullback_0_5atr", "entry_mode": "open_pullback", "anchor": "calculation_open", "pullback_atr": 0.5, "lag_bars": 6, "horizon": 3},
        {"entry_id": "E3_open_pullback_1_0atr", "entry_mode": "open_pullback", "anchor": "calculation_open", "pullback_atr": 1.0, "lag_bars": 6, "horizon": 3},
    ]


def exit_grid() -> list[dict[str, object]]:
    out: list[dict[str, object]] = [{"exit_id": "X0_fixed_r_0_7", "family": "fixed_r", "tp_r": 0.7}]
    for threshold in (0.55, 0.65, 0.75):
        out.append({"exit_id": f"X1_ml_opposite_strong_p{threshold:.2f}".replace(".", "_"), "family": "ml_opposite_strong", "prob_threshold": threshold})
    for threshold in (0.50, 0.55, 0.60):
        out.append({"exit_id": f"X2_ml_opposite_any_p{threshold:.2f}".replace(".", "_"), "family": "ml_opposite_any", "prob_threshold": threshold})
    for threshold in (0.50, 0.60, 0.70):
        out.append({"exit_id": f"X3_ml_hold_close_p{threshold:.2f}".replace(".", "_"), "family": "ml_hold_close", "prob_threshold": threshold})
    for threshold in (0.55, 0.65, 0.75):
        out.append({"exit_id": f"X4_ml_movement_exhaustion_p{threshold:.2f}".replace(".", "_"), "family": "ml_movement_exhaustion", "prob_threshold": threshold})
    for model in ("hold_close", "movement_exhaustion"):
        for threshold in (0.55, 0.65, 0.75):
            out.append({"exit_id": f"X5_fixed_sl_ml_profit_exit_{model}_p{threshold:.2f}".replace(".", "_"), "family": "fixed_sl_ml_profit_exit", "model": model, "prob_threshold": threshold})
    for distance in (0.2, 2.0, 3.0, 5.0):
        for activation in (0.0, 1.0, 2.0, 3.0):
            out.append({"exit_id": f"X6_trail_atr_{distance:g}_activation_{activation:g}".replace(".", "_"), "family": "trail_atr", "trail_distance_atr": distance, "activation_atr": activation})
    for hold_bars in (1, 2, 6, 12):
        out.append({"exit_id": f"X7_time_{hold_bars}", "family": "time_exit", "hold_bars": hold_bars})
    for giveback in (0.30, 0.50, 0.70):
        for activation in (1.0, 2.0, 3.0):
            out.append({"exit_id": f"X8_giveback_{int(giveback * 100)}_activation_{activation:g}".replace(".", "_"), "family": "profit_giveback", "giveback_fraction": giveback, "activation_atr": activation})
    return out


def mask_grid() -> list[dict[str, object]]:
    return [
        {"mask_id": "M0_no_mask", "kind": "none"},
        {"mask_id": "M1_frozen_movement_top5", "kind": "frozen_movement_top_fraction", "selected_fraction": 0.05},
    ]


def expanded_grid() -> list[dict[str, object]]:
    runs = []
    for entry in entry_grid():
        for mask in mask_grid():
            for exit_rule in exit_grid():
                runs.append({**entry, **mask, **exit_rule, "spread": CONFIG.canonical_spread})
    return runs


def stable_json_hash(payload: dict[str, object]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def run_config_hash(config: dict[str, object]) -> str:
    return stable_json_hash(config)


def resume_key(run: dict[str, object]) -> str:
    keys = ("entry_id", "mask_id", "exit_id", "spread")
    return stable_json_hash({key: run.get(key) for key in keys})


def write_progress_atomic(path: Path, progress: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", delete=False, dir=path.parent, encoding="utf-8") as handle:
        json.dump(progress, handle, ensure_ascii=True, indent=2, default=str)
        tmp_name = handle.name
    Path(tmp_name).replace(path)


def load_progress(path: Path, expected_hash: str) -> dict[str, object]:
    if not path.exists():
        return {"run_config_hash": expected_hash, "completed": {}, "failed": {}}
    progress = json.loads(path.read_text(encoding="utf-8"))
    if progress.get("run_config_hash") != expected_hash:
        raise ValueError("run_config_hash mismatch")
    progress.setdefault("completed", {})
    progress.setdefault("failed", {})
    return progress


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def preflight_inputs(config: Fractal0EntryExitGridConfig) -> dict[str, object]:
    errors: list[dict[str, object]] = []
    artifacts: list[dict[str, object]] = []
    input_path_resolution = {"movement_freeze_scores": "from_config"}

    freeze_json = Path(config.movement_freeze_json)
    freeze_data: dict[str, object] = {}
    if not freeze_json.exists():
        errors.append({"id": "movement_freeze_json", "path": str(freeze_json), "reason": "missing"})
    else:
        freeze_data = json.loads(freeze_json.read_text(encoding="utf-8"))
        missing_keys = sorted({"verdict", "locked_test", "frozen_rule", "scores_csv"} - set(freeze_data))
        if missing_keys:
            errors.append({"id": "movement_freeze_json", "path": str(freeze_json), "reason": "missing_keys", "missing_keys": missing_keys})
        artifacts.append({"id": "movement_freeze_json", "path": str(freeze_json), "sha256": sha256_file(freeze_json)})

    scores_path = Path(config.movement_freeze_scores)
    if not scores_path.exists() and freeze_data.get("scores_csv"):
        candidate = Path(str(freeze_data["scores_csv"]))
        if candidate.exists():
            scores_path = candidate
            input_path_resolution["movement_freeze_scores"] = "from_freeze_json_scores_csv"

    required = [
        ("ohlc", Path(config.ohlc_path), {"time", "open", "high", "low", "close", "atr14"}, ";"),
        ("train_core", Path(config.train_path), {"time", "ATR", "fractal0"}, ";"),
        ("validation", Path(config.validation_path), {"time", "ATR", "fractal0"}, ";"),
        ("movement_freeze_scores", scores_path, {"split", "split_row_id", "time", "year", "score", "entry_movement_3", "selected"}, ","),
    ]
    for artifact_id, path, columns, sep in required:
        if not path.exists():
            errors.append({"id": artifact_id, "path": str(path), "reason": "missing"})
            continue
        header = pd.read_csv(path, nrows=0, sep=sep).columns.tolist()
        missing = sorted(columns - set(header))
        if missing:
            errors.append({"id": artifact_id, "path": str(path), "reason": "missing_columns", "missing_columns": missing})
        artifacts.append({"id": artifact_id, "path": str(path), "sha256": sha256_file(path), "columns": header})
    return {
        "status": "FAIL" if errors else "PASS",
        "errors": errors,
        "input_artifacts": artifacts,
        "input_artifact_hashes": {item["id"]: item["sha256"] for item in artifacts},
        "input_path_resolution": input_path_resolution,
    }
```

- [ ] **Step 4: Run focused tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_entry_exit_grid.py -q
```

Expected: Task 1 tests pass.

- [ ] **Step 5: Optional checkpoint commit if explicitly requested**

```bash
git add ML/baseline/benchmark_fractal0_entry_exit_grid.py tests/test_fractal0_entry_exit_grid.py
git commit -m "Add fractal0 entry exit grid skeleton"
```

---

### Task 2: Executable Entry Contract And Synthetic Fill Tests

**Files:**
- Modify: `ML/baseline/benchmark_fractal0_entry_exit_grid.py`
- Modify: `tests/test_fractal0_entry_exit_grid.py`

**Interfaces:**
- Consumes: `entry_grid()`
- Produces: `parse_fractal0(value: object) -> dict | None`
- Produces: `side_from_fractal_dir(direction: object) -> str | None`
- Produces: `resolve_limit_price(row: pd.Series, entry_rule: dict[str, object], calculation_open: float) -> float`
- Produces: `resolve_executable_fill(...) -> dict[str, object]`
- Produces: `protective_stop_price(...) -> float`
- Produces: `build_entry_rows(...) -> pd.DataFrame`

- [ ] **Step 1: Add failing entry tests**

Append:

```python
import pandas as pd


def _ohlc():
    return pd.DataFrame(
        {
            "time": pd.to_datetime([
                "2021-01-01 10:00",
                "2021-01-01 11:00",
                "2021-01-01 12:00",
                "2021-01-01 13:00",
            ]),
            "open": [100.0, 101.0, 102.0, 103.0],
            "high": [101.0, 102.0, 104.0, 105.0],
            "low": [99.0, 100.0, 100.5, 102.5],
            "close": [100.5, 101.5, 103.5, 104.0],
        }
    )


def test_buy_limit_fill_uses_ask_side_with_full_spread():
    fill = runner.resolve_executable_fill(
        side="BUY",
        signal_time=pd.Timestamp("2021-01-01 10:00"),
        limit_price=100.7,
        max_fill_lag_bars=2,
        spread=0.2,
        ohlc=_ohlc(),
        first_order_eligible_bar_offset=1,
    )

    assert fill["filled"] is True
    assert fill["fill_index"] == 2
    assert fill["entry_effective_price"] == 100.7
    assert fill["entry_bid_equivalent"] == 100.5


def test_sell_limit_fill_uses_bid_side():
    fill = runner.resolve_executable_fill(
        side="SELL",
        signal_time=pd.Timestamp("2021-01-01 10:00"),
        limit_price=103.0,
        max_fill_lag_bars=2,
        spread=0.2,
        ohlc=_ohlc(),
        first_order_eligible_bar_offset=1,
    )

    assert fill["filled"] is True
    assert fill["fill_index"] == 2
    assert fill["entry_effective_price"] == 103.0
    assert fill["entry_bid_equivalent"] == 103.0


def test_protective_stop_uses_fixed_half_atr():
    assert runner.protective_stop_price("BUY", fractal0_price=100.0, entry_bid_equivalent=100.5, atr=2.0) == 99.0
    assert runner.protective_stop_price("SELL", fractal0_price=100.0, entry_bid_equivalent=99.5, atr=2.0) == 101.0
```

- [ ] **Step 2: Run tests and verify failure**

```bash
./.venv/bin/python -m pytest tests/test_fractal0_entry_exit_grid.py -q
```

Expected: missing functions fail.

- [ ] **Step 3: Implement executable entry helpers**

Add helpers that reuse parsing ideas from `benchmark_fractal0_price_entry_mechanics.py`, but do not reuse its `bid-touch` fill as PF-gate logic:

```python
def parse_fractal0(value: object) -> dict | None:
    parts = str(value).split(":")
    if len(parts) < 23:
        return None
    try:
        return {"time": int(float(parts[0])), "price": float(parts[1]), "direction": int(float(parts[2])), "shift": int(float(parts[22]))}
    except (TypeError, ValueError):
        return None


def side_from_fractal_dir(direction: object) -> str | None:
    value = float(direction)
    if np.isnan(value) or value == 0:
        return None
    return "BUY" if value < 0 else "SELL"


def _first_eligible_index(signal_time: pd.Timestamp, ohlc: pd.DataFrame, offset: int) -> int | None:
    times = pd.to_datetime(ohlc["time"]).to_numpy()
    idx = int(times.searchsorted(pd.Timestamp(signal_time).to_datetime64(), side="right")) + int(offset)
    return idx if idx < len(ohlc) else None


def resolve_executable_fill(
    side: str,
    signal_time: pd.Timestamp,
    limit_price: float,
    max_fill_lag_bars: int,
    spread: float,
    ohlc: pd.DataFrame,
    first_order_eligible_bar_offset: int = 1,
) -> dict[str, object]:
    start = _first_eligible_index(signal_time, ohlc, first_order_eligible_bar_offset)
    if start is None:
        return {"filled": False, "fill_index": None, "fill_time": pd.NaT, "entry_effective_price": np.nan, "entry_bid_equivalent": np.nan}
    end = min(start + int(max_fill_lag_bars), len(ohlc))
    for pos in range(start, end):
        low_bid = float(ohlc.iloc[pos]["low"])
        high_bid = float(ohlc.iloc[pos]["high"])
        if side == "BUY" and low_bid + float(spread) <= float(limit_price):
            return {"filled": True, "fill_index": pos, "fill_time": pd.Timestamp(ohlc.iloc[pos]["time"]), "entry_effective_price": float(limit_price), "entry_bid_equivalent": float(limit_price) - float(spread)}
        if side == "SELL" and high_bid >= float(limit_price):
            return {"filled": True, "fill_index": pos, "fill_time": pd.Timestamp(ohlc.iloc[pos]["time"]), "entry_effective_price": float(limit_price), "entry_bid_equivalent": float(limit_price)}
    return {"filled": False, "fill_index": None, "fill_time": pd.NaT, "entry_effective_price": np.nan, "entry_bid_equivalent": np.nan}


def protective_stop_price(side: str, fractal0_price: float, entry_bid_equivalent: float, atr: float) -> float:
    if side == "BUY":
        return float(min(fractal0_price, entry_bid_equivalent) - CONFIG.protective_stop_atr * atr)
    return float(max(fractal0_price, entry_bid_equivalent) + CONFIG.protective_stop_atr * atr)
```

- [ ] **Step 4: Run focused tests**

```bash
./.venv/bin/python -m pytest tests/test_fractal0_entry_exit_grid.py -q
```

Expected: entry tests pass.

- [ ] **Step 5: Optional checkpoint commit if explicitly requested**

```bash
git add ML/baseline/benchmark_fractal0_entry_exit_grid.py tests/test_fractal0_entry_exit_grid.py
git commit -m "Add executable fractal0 pending entry contract"
```

---

### Task 3: Trade Simulator, Deterministic Exits, Metrics

**Files:**
- Modify: `ML/baseline/benchmark_fractal0_entry_exit_grid.py`
- Modify: `tests/test_fractal0_entry_exit_grid.py`

**Interfaces:**
- Consumes: `resolve_executable_fill(...)`
- Produces: `simulate_trade(entry: dict[str, object], ohlc: pd.DataFrame, exit_rule: dict[str, object], spread: float, ml_scores: dict[int, float] | None = None) -> dict[str, object]`
- Produces: `compute_trade_metrics(trades: pd.DataFrame) -> dict[str, object]`
- Produces: `yearly_metrics(trades: pd.DataFrame) -> list[dict[str, object]]`
- Produces: `block_bootstrap_pf(trades: pd.DataFrame, seed: int = 20260720, n_bootstrap: int = 1000, block_size: int = 20) -> dict[str, object]`

- [ ] **Step 1: Add failing simulator tests**

Append:

```python
def test_simulator_tp_only_returns_positive_pnl_r():
    entry = {"side": "BUY", "fill_index": 0, "entry_effective_price": 100.2, "entry_bid_equivalent": 100.0, "protective_stop_price": 99.0, "r_value": 1.2, "atr": 2.0}
    bars = pd.DataFrame({"open": [100.0, 100.8], "high": [100.9, 101.1], "low": [100.0, 100.7], "close": [100.8, 101.0], "time": pd.to_datetime(["2021-01-01 10:00", "2021-01-01 11:00"])})
    result = runner.simulate_trade(entry, bars, {"family": "fixed_r", "tp_r": 0.7}, spread=0.2)
    assert result["close_reason"] == "TP"
    assert result["pnl_r"] > 0


def test_simulator_sl_first_when_tp_and_sl_same_bar():
    entry = {"side": "BUY", "fill_index": 0, "entry_effective_price": 100.2, "entry_bid_equivalent": 100.0, "protective_stop_price": 99.0, "r_value": 1.2, "atr": 2.0}
    bars = pd.DataFrame({"open": [100.0], "high": [101.2], "low": [98.9], "close": [100.5], "time": pd.to_datetime(["2021-01-01 10:00"])})
    result = runner.simulate_trade(entry, bars, {"family": "fixed_r", "tp_r": 0.7}, spread=0.2)
    assert result["close_reason"] == "SL"
    assert result["ambiguous"] is True
    assert result["pnl_r"] < 0


def test_sell_exit_uses_ask_shift_for_stop():
    entry = {"side": "SELL", "fill_index": 0, "entry_effective_price": 100.0, "entry_bid_equivalent": 100.0, "protective_stop_price": 101.0, "r_value": 1.0, "atr": 2.0}
    bars = pd.DataFrame({"open": [100.0], "high": [100.9], "low": [99.5], "close": [100.2], "time": pd.to_datetime(["2021-01-01 10:00"])})
    result = runner.simulate_trade(entry, bars, {"family": "fixed_r", "tp_r": 0.7}, spread=0.2)
    assert result["close_reason"] == "SL"


def test_time_exit_closes_after_declared_bars():
    entry = {"side": "BUY", "fill_index": 0, "entry_effective_price": 100.2, "entry_bid_equivalent": 100.0, "protective_stop_price": 99.0, "r_value": 1.2, "atr": 2.0}
    bars = pd.DataFrame({"open": [100.0, 100.4, 100.6], "high": [100.3, 100.5, 100.7], "low": [99.8, 100.1, 100.3], "close": [100.2, 100.5, 100.6], "time": pd.to_datetime(["2021-01-01 10:00", "2021-01-01 11:00", "2021-01-01 12:00"])})
    result = runner.simulate_trade(entry, bars, {"family": "time_exit", "hold_bars": 2}, spread=0.2)
    assert result["close_reason"] == "TIME"
    assert result["hold_bars"] == 2


def test_compute_trade_metrics_reports_ambiguous_same_bar_rate():
    trades = pd.DataFrame({"pnl_r": [1.0, -1.0, -0.5, 0.3], "close_reason": ["TP", "SL", "SL", "TIME"], "ambiguous": [False, True, False, False]})

    metrics = runner.compute_trade_metrics(trades)

    assert metrics["ambiguous_same_bar_rate"] == 0.25
```

- [ ] **Step 2: Run tests and verify failure**

```bash
./.venv/bin/python -m pytest tests/test_fractal0_entry_exit_grid.py -q
```

Expected: simulator functions missing.

- [ ] **Step 3: Implement simulator**

Implement first-touch SL/TP, trailing, time exit and profit giveback in `simulate_trade`. Use this exact behavior:

```python
def _effective_exit_bars(side: str, bars: pd.DataFrame, spread: float) -> pd.DataFrame:
    if side == "BUY":
        return bars.copy()
    shifted = bars.copy()
    for col in ("open", "high", "low", "close"):
        shifted[col] = pd.to_numeric(shifted[col], errors="coerce") + float(spread)
    return shifted


def _pnl_r(side: str, entry_price: float, exit_price: float, r_value: float) -> float:
    raw = exit_price - entry_price if side == "BUY" else entry_price - exit_price
    return float(raw / r_value)


def compute_trade_metrics(trades: pd.DataFrame) -> dict[str, object]:
    pnl = pd.to_numeric(trades.get("pnl_r"), errors="coerce").dropna()
    wins = pnl[pnl > 0]
    losses = pnl[pnl < 0]
    gross_profit = float(wins.sum())
    gross_loss = float(-losses.sum())
    equity = pnl.cumsum()
    drawdown = equity.cummax() - equity
    return {
        "n_trades": int(len(pnl)),
        "gross_profit": gross_profit,
        "gross_loss": gross_loss,
        "pf": float(gross_profit / gross_loss) if gross_loss > 0 else None,
        "mean_pnl_r": float(pnl.mean()) if len(pnl) else None,
        "median_pnl_r": float(pnl.median()) if len(pnl) else None,
        "max_drawdown_r": float(drawdown.max()) if len(drawdown) else 0.0,
        "win_rate": float((pnl > 0).mean()) if len(pnl) else None,
        "ambiguous_same_bar_rate": float(trades.get("ambiguous", pd.Series(dtype=bool)).fillna(False).astype(bool).mean()) if len(trades) else 0.0,
        "exit_reason_counts": trades.get("close_reason", pd.Series(dtype=object)).value_counts().to_dict(),
    }
```

Gate rule: if winner `ambiguous_same_bar_rate > 0.05`, lifecycle is no higher
than `research_hint`; if `ambiguous_same_bar_rate > 0.10`, verdict is no higher
than `diagnostic_only`.

The full `simulate_trade` must return:

```python
{
    "filled": True,
    "close_reason": "TP" | "SL" | "TRAIL" | "TIME" | "GIVEBACK" | "ML_CLOSE",
    "pnl_r": float,
    "hold_bars": int,
    "ambiguous": bool,
    "exit_price": float,
    "exit_time": str,
}
```

- [ ] **Step 4: Run focused tests**

```bash
./.venv/bin/python -m pytest tests/test_fractal0_entry_exit_grid.py -q
```

Expected: simulator and metric tests pass.

- [ ] **Step 5: Optional checkpoint commit if explicitly requested**

```bash
git add ML/baseline/benchmark_fractal0_entry_exit_grid.py tests/test_fractal0_entry_exit_grid.py
git commit -m "Add fractal0 entry exit trade simulator"
```

---

### Task 4: Movement Mask And Attribution

**Files:**
- Modify: `ML/baseline/benchmark_fractal0_entry_exit_grid.py`
- Modify: `tests/test_fractal0_entry_exit_grid.py`

**Interfaces:**
- Consumes: `mask_grid()`
- Produces: `load_frozen_movement_mask(report_path: Path, scores_path: Path) -> dict[str, object]`
- Produces: `apply_mask(rows: pd.DataFrame, mask_id: str, frozen_scores: pd.DataFrame | None) -> pd.DataFrame`
- Produces: `validate_movement_mask_coverage(rows: pd.DataFrame, scores: pd.DataFrame) -> dict[str, object]`
- Produces: `compute_attribution(summary: pd.DataFrame, winner: dict[str, object]) -> list[dict[str, object]]`

- [ ] **Step 1: Add failing mask and attribution tests**

Append:

```python
def test_apply_movement_mask_keeps_only_selected_rows():
    rows = pd.DataFrame({"split_row_id": [1, 2, 3], "value": [10, 20, 30]})
    scores = pd.DataFrame({"split_row_id": [1, 2, 3], "selected": [True, False, True], "score": [0.9, 0.1, 0.8]})

    masked = runner.apply_mask(rows, "M1_frozen_movement_top5", scores)

    assert masked["split_row_id"].tolist() == [1, 3]
    assert masked["movement_score"].tolist() == [0.9, 0.8]


def test_validate_movement_mask_coverage_fails_missing_rows():
    rows = pd.DataFrame({"split_row_id": [1, 2, 3]})
    scores = pd.DataFrame({"split_row_id": [1, 3], "selected": [True, True], "score": [0.9, 0.8]})

    coverage = runner.validate_movement_mask_coverage(rows, scores)

    assert coverage["status"] == "FAIL"
    assert coverage["missing_score_rows"] == 1


def test_compute_attribution_reports_entry_mask_and_exit_effects():
    summary = pd.DataFrame(
        [
            {"entry_id": "E3", "mask_id": "M1_frozen_movement_top5", "exit_id": "X4_ml_movement_exhaustion_p0_65", "pf": 2.1},
            {"entry_id": "E3", "mask_id": "M1_frozen_movement_top5", "exit_id": "X0_fixed_r_0_7", "pf": 1.4},
            {"entry_id": "E3", "mask_id": "M0_no_mask", "exit_id": "X4_ml_movement_exhaustion_p0_65", "pf": 1.6},
            {"entry_id": "E1_simple_limit_at_fractal0", "mask_id": "M1_frozen_movement_top5", "exit_id": "X4_ml_movement_exhaustion_p0_65", "pf": 1.5},
            {"entry_id": "E3", "mask_id": "M1_frozen_movement_top5", "exit_id": "X7_time_6", "pf": 1.3},
        ]
    )
    winner = {"entry_id": "E3", "mask_id": "M1_frozen_movement_top5", "exit_id": "X4_ml_movement_exhaustion_p0_65"}

    attribution = {row["check_id"]: row for row in runner.compute_attribution(summary, winner)}

    assert attribution["A0_matched_entry_mask_baseline_exit"]["baseline_pf"] == 1.4
    assert attribution["A1_same_exit_no_mask"]["baseline_pf"] == 1.6
    assert attribution["A2_same_exit_simple_entry"]["baseline_pf"] == 1.5
    assert attribution["A4_same_entry_mask_time_exit"]["baseline_pf"] == 1.3
```

- [ ] **Step 2: Run tests and verify failure**

```bash
./.venv/bin/python -m pytest tests/test_fractal0_entry_exit_grid.py -q
```

Expected: mask/attribution functions missing.

- [ ] **Step 3: Implement mask and attribution helpers**

Use `split_row_id` as the join key. If source score files do not contain it, create it before export as the original split-local row index and record `mask_join_key = split_row_id` in JSON.

```python
def apply_mask(rows: pd.DataFrame, mask_id: str, frozen_scores: pd.DataFrame | None) -> pd.DataFrame:
    if mask_id == "M0_no_mask":
        out = rows.copy()
        out["movement_mask_selected"] = True
        return out
    if frozen_scores is None:
        raise ValueError("frozen movement scores required for M1_frozen_movement_top5")
    selected = frozen_scores.loc[frozen_scores["selected"].astype(bool), ["split_row_id", "score"]].rename(columns={"score": "movement_score"})
    out = rows.merge(selected, on="split_row_id", how="inner")
    out["movement_mask_selected"] = True
    return out


def validate_movement_mask_coverage(rows: pd.DataFrame, scores: pd.DataFrame) -> dict[str, object]:
    row_ids = set(rows["split_row_id"].tolist())
    score_ids = set(scores["split_row_id"].tolist())
    missing = row_ids - score_ids
    return {
        "status": "PASS" if not missing else "FAIL",
        "rows": len(row_ids),
        "score_rows": len(score_ids),
        "missing_score_rows": len(missing),
        "coverage": 1.0 if not row_ids else (len(row_ids) - len(missing)) / len(row_ids),
    }
```

- [ ] **Step 4: Run focused tests**

```bash
./.venv/bin/python -m pytest tests/test_fractal0_entry_exit_grid.py -q
```

Expected: movement mask and attribution tests pass.

- [ ] **Step 5: Optional checkpoint commit if explicitly requested**

```bash
git add ML/baseline/benchmark_fractal0_entry_exit_grid.py tests/test_fractal0_entry_exit_grid.py
git commit -m "Add movement mask attribution for fractal0 grid"
```

---

### Task 5: ML-Exit Dataset, Targets, And Models

**Files:**
- Modify: `ML/baseline/benchmark_fractal0_entry_exit_grid.py`
- Modify: `tests/test_fractal0_entry_exit_grid.py`

**Interfaces:**
- Produces: `build_exit_decision_rows(trades: pd.DataFrame, ohlc: pd.DataFrame) -> pd.DataFrame`
- Produces: `build_exit_targets(decision_rows: pd.DataFrame) -> pd.DataFrame`
- Produces: `exit_feature_columns(mask_id: str) -> list[str]`
- Produces: `train_exit_models(train_rows: pd.DataFrame, threads: int, seeds: tuple[int, ...]) -> dict[str, object]`
- Produces: `score_exit_models(models: dict[str, object], decision_rows: pd.DataFrame) -> pd.DataFrame`

- [ ] **Step 1: Add failing ML-exit contract tests**

Append:

```python
def test_exit_decision_rows_use_next_open_execution_time():
    trades = pd.DataFrame([{"position_id": "p1", "side": "BUY", "fill_index": 0, "entry_effective_price": 100.2, "entry_bid_equivalent": 100.0, "protective_stop_price": 99.0, "r_value": 1.2, "atr": 2.0}])
    bars = pd.DataFrame({"time": pd.to_datetime(["2021-01-01 10:00", "2021-01-01 11:00", "2021-01-01 12:00"]), "open": [100.0, 100.4, 100.6], "high": [100.3, 100.5, 100.7], "low": [99.8, 100.1, 100.3], "close": [100.2, 100.5, 100.6]})

    decisions = runner.build_exit_decision_rows(trades, bars)

    assert decisions.loc[0, "decision_time"] == pd.Timestamp("2021-01-01 10:00")
    assert decisions.loc[0, "first_exit_execution_time"] == pd.Timestamp("2021-01-01 11:00")
    assert "target_exit_hold_close" not in decisions.columns


def test_exit_decision_rows_create_sequence_until_last_executable_bar():
    trades = pd.DataFrame([{"position_id": "p1", "side": "BUY", "fill_index": 0, "entry_effective_price": 100.2, "entry_bid_equivalent": 100.0, "protective_stop_price": 99.0, "r_value": 1.2, "atr": 2.0}])
    bars = pd.DataFrame({"time": pd.to_datetime(["2021-01-01 10:00", "2021-01-01 11:00", "2021-01-01 12:00", "2021-01-01 13:00"]), "open": [100.0, 100.4, 100.6, 100.7], "high": [100.3, 100.5, 100.7, 100.8], "low": [99.8, 100.1, 100.3, 100.5], "close": [100.2, 100.5, 100.6, 100.7]})

    decisions = runner.build_exit_decision_rows(trades, bars)

    assert decisions["bars_since_fill"].tolist() == [0, 1, 2]
    assert decisions["decision_time"].tolist() == list(bars["time"].iloc[:3])
    assert decisions["first_exit_execution_time"].tolist() == list(bars["time"].iloc[1:4])


def test_exit_targets_are_named_as_future_derived_targets():
    decisions = pd.DataFrame(
        {
            "side": ["BUY"],
            "entry_effective_price": [100.2],
            "r_value": [1.2],
            "future_favorable_r_3": [0.1],
            "future_adverse_r_3": [0.8],
            "close_now_pnl_r": [0.2],
            "hold_3_pnl_r": [-0.4],
        }
    )

    targets = runner.build_exit_targets(decisions)

    assert targets.loc[0, "target_exit_opposite_any"] == 1
    assert targets.loc[0, "target_exit_opposite_strong"] == 0
    assert targets.loc[0, "target_exit_hold_close"] == 1
    assert targets.loc[0, "target_exit_movement_exhaustion"] == 1


def test_exit_features_do_not_include_future_or_target_columns():
    cols = runner.exit_feature_columns("M1_frozen_movement_top5")

    forbidden_prefixes = ("future_", "target_")
    forbidden_exact = {"hold_3_pnl_r", "close_now_pnl_r", "target_exit_hold_close"}
    assert not any(col.startswith(forbidden_prefixes) for col in cols)
    assert forbidden_exact.isdisjoint(cols)
    assert "movement_score" in cols
    assert "movement_score_available" in cols


def test_exit_features_for_no_mask_do_not_use_movement_score():
    cols = runner.exit_feature_columns("M0_no_mask")

    assert "movement_score" not in cols
    assert "movement_score_available" not in cols
```

- [ ] **Step 2: Run tests and verify failure**

```bash
./.venv/bin/python -m pytest tests/test_fractal0_entry_exit_grid.py -q
```

Expected: ML-exit functions missing.

- [ ] **Step 3: Implement target contract**

Target definitions:

```text
exit_horizon_bars = 3
target_exit_opposite_any = 1 if future_adverse_r_3 >= 0.5 else 0
target_exit_opposite_strong = 1 if future_adverse_r_3 >= 1.0 else 0
target_exit_hold_close = 1 if close_now_pnl_r >= hold_3_pnl_r + 0.1 else 0
target_exit_movement_exhaustion = 1 if future_favorable_r_3 < 0.3 and future_adverse_r_3 >= 0.5 else 0
```

Feature allowlist for ML-exit:

```python
EXIT_FEATURE_COLUMNS_BASE = [
    "bars_since_fill",
    "unrealized_pnl_r_before_decision",
    "max_favorable_r_before_decision",
    "max_adverse_r_before_decision",
    "ATR",
]
EXIT_FEATURE_COLUMNS_M1_ONLY = [
    "movement_score",
    "movement_score_available",
]
```

ML-exit models are trained separately for `M0_no_mask` and
`M1_frozen_movement_top5`. `movement_score` is allowed only for M1 models. Do
not fill missing M0 score with zero; that would let the model learn the mask
state as a hidden regime.

Training contract:

```python
EXIT_TARGETS = (
    "target_exit_opposite_any",
    "target_exit_opposite_strong",
    "target_exit_hold_close",
    "target_exit_movement_exhaustion",
)
EXIT_MODEL_SEEDS = (42, 43, 44)
```

Use `ExtraTreesClassifier(n_estimators=200, max_depth=8, min_samples_leaf=50, random_state=seed, n_jobs=threads)` for each target/seed. Store median probability across seeds as `score_<target>`.

- [ ] **Step 4: Run focused tests**

```bash
./.venv/bin/python -m pytest tests/test_fractal0_entry_exit_grid.py -q
```

Expected: ML-exit contract tests pass.

- [ ] **Step 5: Optional checkpoint commit if explicitly requested**

```bash
git add ML/baseline/benchmark_fractal0_entry_exit_grid.py tests/test_fractal0_entry_exit_grid.py
git commit -m "Add ML exit target and scoring contract"
```

---

### Task 6: Full Matrix Runner, Selection, Stress, Permutation

**Files:**
- Modify: `ML/baseline/benchmark_fractal0_entry_exit_grid.py`
- Modify: `tests/test_fractal0_entry_exit_grid.py`

**Interfaces:**
- Consumes: all previous task interfaces
- Produces: `run_one_config(run: dict[str, object], split_rows: dict[str, pd.DataFrame], ohlc: pd.DataFrame, ml_scores: dict[str, pd.DataFrame], spread: float) -> dict[str, object]`
- Produces: `select_winner(summary: pd.DataFrame) -> dict[str, object]`
- Produces: `evaluate_winner_on_val_eval(winner: dict[str, object], val_eval_summary: pd.DataFrame) -> dict[str, object]`
- Produces: `decide_research_verdict(val_eval_metrics: dict[str, object], permutation: dict[str, object]) -> dict[str, object]`
- Produces: `permutation_verdict(observed_bs_p05: float, null_best_bs_p05: list[float]) -> dict[str, object]`
- Produces: `run_selection_permutation(summary: pd.DataFrame, repeats: int, seed: int) -> dict[str, object]`
- Produces: `run_matrix(args: argparse.Namespace) -> dict[str, object]`

- [ ] **Step 1: Add failing selection and permutation tests**

Append:

```python
def test_select_winner_requires_sample_size_and_prefers_bs_p05():
    summary = pd.DataFrame(
        [
            {"entry_id": "E1", "mask_id": "M0", "exit_id": "X0", "n_trades": 299, "pf": 3.0, "bs_p05": 2.0, "stress_pf": 2.0, "negative_years": 0, "mean_pnl_r": 0.2, "max_drawdown_r": 3.0, "effective_profit_years": 2.0, "pf_without_best_year": 1.5},
            {"entry_id": "E2", "mask_id": "M0", "exit_id": "X1", "n_trades": 350, "pf": 1.8, "bs_p05": 1.3, "stress_pf": 1.3, "negative_years": 0, "mean_pnl_r": 0.1, "max_drawdown_r": 5.0, "effective_profit_years": 2.0, "pf_without_best_year": 1.2},
            {"entry_id": "E3", "mask_id": "M0", "exit_id": "X2", "n_trades": 360, "pf": 1.7, "bs_p05": 1.4, "stress_pf": 1.3, "negative_years": 0, "mean_pnl_r": 0.1, "max_drawdown_r": 5.0, "effective_profit_years": 2.0, "pf_without_best_year": 1.2},
        ]
    )

    winner = runner.select_winner(summary)

    assert winner["entry_id"] == "E3"
    assert winner["selection_metric"] == "BS_p05"


def test_evaluate_winner_on_val_eval_uses_eval_metrics_not_select_metrics():
    winner = {"entry_id": "E3", "mask_id": "M0_no_mask", "exit_id": "X2", "val_select_pf": 2.5}
    val_eval_summary = pd.DataFrame(
        [
            {"entry_id": "E3", "mask_id": "M0_no_mask", "exit_id": "X2", "pf": 1.2, "bs_p05": 0.9, "n_trades": 350, "stress_pf": 1.1, "negative_years": 0, "mean_pnl_r": 0.01, "pf_without_best_year": 1.0, "effective_profit_years": 2.0}
        ]
    )

    evaluated = runner.evaluate_winner_on_val_eval(winner, val_eval_summary)
    verdict = runner.decide_research_verdict(evaluated, {"status": "PASS", "empirical_p_value": 0.05})

    assert evaluated["pf"] == 1.2
    assert verdict["lifecycle_status"] == "research_hint"
    assert "val_eval_gate_failed" in verdict["reasons"]


def test_permutation_verdict_passes_when_tail_probability_is_small():
    result = runner.permutation_verdict(observed_bs_p05=1.50, null_best_bs_p05=[1.00] * 99)

    assert result["empirical_p_value"] == 0.01
    assert result["status"] == "PASS"


def test_permutation_verdict_returns_research_hint_when_tail_probability_is_large():
    result = runner.permutation_verdict(observed_bs_p05=1.10, null_best_bs_p05=[1.20] * 20 + [1.00] * 79)

    assert result["empirical_p_value"] == 0.21
    assert result["status"] == "RESEARCH_HINT"


def test_stress_spread_does_not_choose_winner():
    canonical = pd.DataFrame(
        [
            {"entry_id": "E1", "mask_id": "M0_no_mask", "exit_id": "X0", "n_trades": 350, "pf": 1.6, "bs_p05": 1.20, "stress_pf": 0.80, "negative_years": 0, "mean_pnl_r": 0.1, "max_drawdown_r": 5.0, "effective_profit_years": 2.0, "pf_without_best_year": 1.2},
            {"entry_id": "E2", "mask_id": "M0_no_mask", "exit_id": "X1", "n_trades": 350, "pf": 1.5, "bs_p05": 1.10, "stress_pf": 2.50, "negative_years": 0, "mean_pnl_r": 0.1, "max_drawdown_r": 5.0, "effective_profit_years": 2.0, "pf_without_best_year": 1.2},
        ]
    )

    winner = runner.select_winner(canonical)

    assert winner["entry_id"] == "E1"
```

- [ ] **Step 2: Run tests and verify failure**

```bash
./.venv/bin/python -m pytest tests/test_fractal0_entry_exit_grid.py -q
```

Expected: selection/permutation functions missing.

- [ ] **Step 3: Implement matrix execution**

Runner requirements:

```text
--threads 24 default
--resume default
--no-resume for clean rerun
--output-prefix ML/reports/fractal0_entry_exit_grid default
heartbeat: start, preflight, each run start/end, done_runs/total_runs, elapsed, ETA when available
atomic progress JSON after every run
failed runs are recorded and do not stop the matrix
```

Selection policy:

```text
1. On val_select canonical-spread rows, keep only configs with n_trades >= 300.
2. Keep only configs with negative_years <= 1.
3. Keep only configs with mean_pnl_r > 0.
4. Keep only configs with pf_without_best_year >= 1.10.
5. Keep only configs with effective_profit_years >= max(1.5, 0.6 * n_years), or mark concentration_warning.
6. Pick max val_select BS_p05.
7. If BS_p05 tie within 0.03, pick fewer ML thresholds and then lower max_drawdown_r.
8. Evaluate the selected rule once on val_eval.
9. Attach stress-spread metrics after selection; if winner stress_pf < 1.20, cap lifecycle_status at research_hint and record stress_warning.
10. Gate A, Gate B and final lifecycle_status are computed from val_eval metrics, not val_select metrics.
```

Permutation correction:

```text
permutation_repeats = 200
permutation unit = block-shuffled pnl_r values inside val_select, grouped by year and side when both columns exist
each repeat rebuilds config-level metrics and reruns select_winner
empirical_p_value = (1 + count(null_best_bs_p05 >= observed_winner_bs_p05)) / (1 + repeats)
PASS if empirical_p_value <= 0.10 else RESEARCH_HINT
```

Implementation rule: `select_winner()` receives only canonical-spread
`val_select` rows. Stress rows must never improve rank, remove a better
canonical winner, or replace it with a lower canonical candidate. Stress is a
post-selection robustness disclosure/gate only.

- [ ] **Step 4: Run focused tests**

```bash
./.venv/bin/python -m pytest tests/test_fractal0_entry_exit_grid.py -q
```

Expected: selection, progress and permutation tests pass.

- [ ] **Step 5: Run smoke matrix on tiny fixture mode**

Add CLI argument `--smoke-limit-runs 8` for tests only. Then run:

```bash
./.venv/bin/python ML/baseline/benchmark_fractal0_entry_exit_grid.py \
  --threads 2 \
  --smoke-limit-runs 8 \
  --output-prefix /tmp/fractal0_entry_exit_grid_smoke
```

Expected files:

```text
/tmp/fractal0_entry_exit_grid_smoke.json
/tmp/fractal0_entry_exit_grid_smoke_summary.csv
/tmp/fractal0_entry_exit_grid_smoke_trades.csv
/tmp/fractal0_entry_exit_grid_smoke_progress.json
```

- [ ] **Step 6: Optional checkpoint commit if explicitly requested**

```bash
git add ML/baseline/benchmark_fractal0_entry_exit_grid.py tests/test_fractal0_entry_exit_grid.py
git commit -m "Add fractal0 entry exit matrix runner"
```

---

### Task 7: Full Run Artifacts And Report

**Files:**
- Modify: `ML/baseline/benchmark_fractal0_entry_exit_grid.py`
- Create: `docs/ML/benchmark_fractal0_entry_exit_grid.py.md`
- Create: `docs/reports/2026-07-20-fractal0-entry-exit-grid.md`

**Interfaces:**
- Consumes: `run_matrix(args: argparse.Namespace) -> dict[str, object]`
- Produces: all report CSV/JSON artifacts listed in this plan

- [ ] **Step 1: Run focused tests**

```bash
./.venv/bin/python -m pytest tests/test_fractal0_entry_exit_grid.py -q
```

Expected: all tests in the file pass.

- [ ] **Step 2: Run full matrix**

```bash
PYTHONUNBUFFERED=1 ./.venv/bin/python ML/baseline/benchmark_fractal0_entry_exit_grid.py \
  --threads 24 \
  --output-prefix ML/reports/fractal0_entry_exit_grid
```

Expected heartbeat includes:

```text
start fractal0_entry_exit_grid
preflight PASS
progress done_runs=
finished fractal0_entry_exit_grid
```

- [ ] **Step 3: Verify structured artifacts**

```bash
./.venv/bin/python - <<'PY'
import json
from pathlib import Path

base = Path("ML/reports/fractal0_entry_exit_grid")
required = [
    base.with_suffix(".json"),
    Path("ML/reports/fractal0_entry_exit_grid_summary.csv"),
    Path("ML/reports/fractal0_entry_exit_grid_trades.csv"),
    Path("ML/reports/fractal0_entry_exit_grid_yearly.csv"),
    Path("ML/reports/fractal0_entry_exit_grid_spread_stress.csv"),
    Path("ML/reports/fractal0_entry_exit_grid_attribution.csv"),
    Path("ML/reports/fractal0_entry_exit_grid_permutation.csv"),
]
missing = [str(path) for path in required if not path.exists()]
assert not missing, missing
report = json.loads(base.with_suffix(".json").read_text())
for key in [
    "input_artifacts",
    "input_artifact_hashes",
    "rows_by_split_before_after_mask",
    "fill_rate_by_entry",
    "ambiguous_same_bar_rate",
    "ml_feature_columns_used",
    "ml_target_positive_rate_by_split",
    "current_search_budget",
    "cumulative_search_budget",
    "exact_grid",
    "multiple_testing_correction",
    "ml_exit_target_contracts",
    "pnl_convention",
    "simulator_test_status",
    "attribution_status",
    "movement_mask_live_cutoff_status",
    "sample_size_warning_status",
    "selected_winner",
    "val_select_winner_metrics",
    "val_eval_winner_metrics",
    "rejected_alternatives",
    "split_roles",
    "canonical_spread",
    "stress_spread",
    "forbidden_interpretations",
    "allowed_max_verdict",
]:
    assert key in report, key
assert report["locked_test"] == "not_opened"
assert report["allowed_max_verdict"] == "research_only"
print("artifact contract PASS")
PY
```

Expected: `artifact contract PASS`.

- [ ] **Step 4: Write module docs**

Create `docs/ML/benchmark_fractal0_entry_exit_grid.py.md`:

````markdown
# benchmark_fractal0_entry_exit_grid.py

## Назначение

`ML/baseline/benchmark_fractal0_entry_exit_grid.py` запускает исследовательскую сетку для исполнимого `fractal0_price` pending-entry, deterministic exit и ML-exit.

## Команда

```bash
PYTHONUNBUFFERED=1 ./.venv/bin/python ML/baseline/benchmark_fractal0_entry_exit_grid.py \
  --threads 24 \
  --output-prefix ML/reports/fractal0_entry_exit_grid
```

## Входы

- `DATA/XAUUSD_H1_OHLC.csv`
- `DATA/Nero_XAUUSD_train_labeled.csv`
- `DATA/Nero_XAUUSD_validation_labeled.csv`
- `ML/reports/entry_based_movement_filter_freeze.json`
- `ML/reports/entry_based_movement_filter_freeze_scores.csv`

## Выходы

- `ML/reports/fractal0_entry_exit_grid.json`
- `ML/reports/fractal0_entry_exit_grid_summary.csv`
- `ML/reports/fractal0_entry_exit_grid_trades.csv`
- `ML/reports/fractal0_entry_exit_grid_yearly.csv`
- `ML/reports/fractal0_entry_exit_grid_spread_stress.csv`
- `ML/reports/fractal0_entry_exit_grid_attribution.csv`
- `ML/reports/fractal0_entry_exit_grid_permutation.csv`

## Ограничения

- `locked_test` не открывается.
- Максимальный verdict: `research_only`.
- Проверка на новом инструменте не входит в runner.
- `M1_frozen_movement_top5` является research segmentation mask, не live-rule.
- PF/PnL являются исследовательскими метриками до отдельного freeze-плана.
- `DATA/*.csv` читаются с `sep=";"`.
- Execution model is offline OHLC simulation, not MT4 tester parity.
````

- [ ] **Step 5: Write research report**

Create `docs/reports/2026-07-20-fractal0-entry-exit-grid.md` from the JSON. Required sections:

```markdown
# Fractal0 Entry Exit Grid

> **Дата**: 2026-07-20
> **Статус**: Completed
> **Уровень**: research_scan
> **Вердикт**: скопировать поле `verdict` из `ML/reports/fractal0_entry_exit_grid.json`
> **Related spec**: `docs/superpowers/specs/2026-07-20-fractal0-entry-exit-grid-design.md`

## Context

## Multiple Testing Context

## Execution Contract

## Split Disclosure

## Results

## Winner Attribution

## Stress Spread

## Permutation Correction

## Limitations / Non-Conclusions

## Next Step
```

The report must state that `locked_test` was not opened and that a new instrument check is a later final step only after a future frozen final-system plan.

- [ ] **Step 6: Run report-to-artifact consistency check**

```bash
./.venv/bin/python - <<'PY'
import json
import re
from pathlib import Path

report_path = sorted(Path("docs/reports").glob("*fractal0-entry-exit-grid.md"))[-1]
artifact = json.loads(Path("ML/reports/fractal0_entry_exit_grid.json").read_text())
text = report_path.read_text(encoding="utf-8")
for key in ("allowed_max_verdict", "locked_test", "current_search_budget"):
    assert str(artifact[key]) in text, key
for forbidden in ("production ready", "live-ready", "tradable"):
    assert forbidden not in text.lower(), forbidden
assert re.search(r"PF", text), "PF table missing"
print("report consistency PASS")
PY
```

Expected: `report consistency PASS`.

- [ ] **Step 7: Run full test suite**

```bash
./.venv/bin/python -m pytest tests/ -q
```

Expected: all tests pass.

- [ ] **Step 8: Optional checkpoint commit if explicitly requested**

```bash
git add ML/baseline/benchmark_fractal0_entry_exit_grid.py tests/test_fractal0_entry_exit_grid.py docs/ML/benchmark_fractal0_entry_exit_grid.py.md docs/reports/*fractal0-entry-exit-grid.md ML/reports/fractal0_entry_exit_grid*
git commit -m "Run fractal0 entry exit grid research"
```

---

## Self-Review Checklist For Implementer

- [ ] Spec section "Исследовательский уровень" maps to Global Constraints and Task 7 report.
- [ ] Spec section "Entry Contract" maps to Task 2.
- [ ] Spec section "PnL И Контракт Исполнения" maps to Task 2 and Task 3.
- [ ] Spec section "Exit Grid" maps to Task 1 and Task 3.
- [ ] Spec section "Контракт ML-Exit Target" maps to Task 5.
- [ ] Spec section "Movement Mask Grid" maps to Task 4.
- [ ] Spec section "Полная первая сетка" maps to Task 1 and Task 6.
- [ ] Spec section "Runtime Contract" maps to Task 1 and Task 6.
- [ ] Spec section "Split Protocol" maps to Task 5 and Task 6.
- [ ] Spec section "Profit Gates" maps to Task 6.
- [ ] Spec section "Selection Policy" maps to Task 6.
- [ ] Spec section "Attribution Checks" maps to Task 4 and Task 7.
- [ ] Spec section "Simulator Test Requirements" maps to Task 3.
- [ ] Spec section "Последующая Проверка На Новом Инструменте" maps to Task 7 report.
- [ ] Spec section "Артефакты" maps to Task 7.
- [ ] Spec section "Stop Rules" maps to Task 6 verdict logic and Task 7 report.
