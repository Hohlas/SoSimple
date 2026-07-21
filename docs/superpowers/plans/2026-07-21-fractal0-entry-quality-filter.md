# Fractal0 Entry Quality Filter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Добавить ML-entry фильтр для `E3_open_pullback_1_0atr`, который учится на фактическом качестве сделки, и сравнить его с no-mask и мягкими movement masks без открытия `locked_test`.

**Architecture:** Построить отдельный bounded runner поверх выбранной stop-policy из stop-grid: сначала обучить текущий ML-exit на `train_core`, затем получить исторические сделки E3 и по ним обучить ML-entry модели. Новый runner не должен дублировать симулятор, загрузчики, split-логику, метрики или ML-exit; он переиспользует `ML/baseline/benchmark_fractal0_entry_exit_grid.py` и добавляет только entry-filter слой. Фильтр и topX выбираются только на `val_select`; на `val_eval` применяется зафиксированный `score_cutoff_on_val_select`, а не пересчитывается новый topX.

**Tech Stack:** Python 3.10+, pandas, numpy, scikit-learn `ExtraTreesClassifier`, pytest, `./.venv/bin/python`, кодовые утилиты из `ML/baseline/benchmark_fractal0_entry_exit_grid.py`.

## Global Constraints

- Работать в текущей ветке; worktree не создавать.
- Использовать `./.venv/bin/python`.
- `locked_test` не открывать.
- Максимальный verdict этапа: `research_only`.
- Использовать только `E3_open_pullback_1_0atr`.
- Использовать stop-policy, выбранную или явно заданную после плана `2026-07-21-fractal0-stop-grid-m5.md`.
- Не писать новый торговый симулятор с нуля; использовать функции из `ML/baseline/benchmark_fractal0_entry_exit_grid.py`.
- H1 остаётся источником признаков и split.
- M5 используется только для порядка исполнения внутри H1-свечи.
- Entry-filter не имеет права использовать будущие PnL/exit fields как признаки.
- `UpX/DnX` и ratio targets не используются в этом этапе.
- `train_core` обучает ML-exit и ML-entry.
- `val_select` выбирает filter family и topX threshold, затем фиксирует `score_cutoff_on_val_select`.
- `val_eval` проверяет уже выбранный filter без изменений.
- На `val_eval` запрещено пересчитывать topX по распределению самого `val_eval`; применять только `score >= score_cutoff_on_val_select`.
- Для research использовать `topX` только как способ выбора cutoff на `val_select`; в artifact обязательно сохранять фактический `score_cutoff_on_val_select`.
- Project CSV читать с `sep=";"`; report/generated CSV читать через separator detection. В частности, `entry_based_movement_filter_freeze_scores.csv` нельзя жёстко считать `sep=";"`.
- Preflight обязателен: проверить входные файлы, CSV-разделители, нужные колонки, split-роли, `locked_test=not_opened`, stop-grid artifact и hashes входов.
- Full entry-quality run запрещён до завершения stop-grid и явного выбора `stop_policy_id`; fallback `S0_current_0_5` допустим только для smoke/debug.
- После Python-изменений запускать `./.venv/bin/python -m pytest tests/test_fractal0_entry_quality_filter.py -q` и `./.venv/bin/python -m pytest tests/test_fractal0_entry_exit_grid.py -q`.

---

## Research Contract

### Baseline And Comparisons

Compare these filters:

```text
M0_no_mask
movement_top50
movement_top30
movement_top20
movement_top10
simple_stop_distance_top50
simple_stop_distance_top30
simple_r_value_top50
simple_r_value_top30
entry_quality_top50
entry_quality_top30
entry_quality_top20
entry_quality_top10
entry_avoid_sl_top50
entry_avoid_sl_top30
entry_avoid_sl_top20
entry_avoid_sl_top10
```

`movement_topX` uses the frozen movement score from `ML/reports/entry_based_movement_filter_freeze_scores.csv`, but with softer fractions than the old `top5`.

`simple_stop_distance_topX` and `simple_r_value_topX` are non-ML baselines.
They test whether any improvement comes from simple geometry rather than the
entry model.

`entry_quality_topX` uses a new ML-entry model trained on:

```text
target_entry_good = 1 if pnl_r > 0 else 0
```

`entry_avoid_sl_topX` uses a new ML-entry model trained on:

```text
target_entry_avoid_sl = 1 if close_reason != "SL" else 0
```

Primary target for selection:

```text
entry_quality_topX
```

`entry_avoid_sl_topX` is secondary/diagnostic unless it clearly dominates PnL gates on `val_select` and remains stable on `val_eval`.

### Entry Label Definition

For each filled E3 entry:

```text
entry row -> chosen stop policy -> exit_policy_id from stop-grid winner -> simulated trade
```

`X2_ml_opposite_any` can be added as diagnostic comparison, but it is not the
default label exit if stop-grid winner uses another exit. Current M5 full-grid
leader is `X0_fixed_r_0_7`, so the plan must not hard-code X2.

Then labels:

```text
target_entry_good = pnl_r > 0
target_entry_avoid_sl = close_reason != "SL"
```

Important: `target_entry_good` and `target_entry_avoid_sl` are not equivalent.
A trade can avoid SL and still lose money through `ML_CLOSE` or `TIME`.

### Entry Feature Contract

Allowed features must be available at entry decision time:

```text
ATR
side encoded as BUY/SELL
fractal0_price relative to calculation_open
limit_price relative to calculation_open
entry_bid_equivalent relative to fractal0_price
distance_to_stop_atr
r_value_atr
time features already allowed by methodology, if present in source rows
current fractal profile fields that are known in the row
```

Forbidden features:

```text
pnl_r
close_reason
hold_bars
future_favorable_r_3
future_adverse_r_3
target_exit_*
target_entry_*
any post-fill future OHLC outcome
locked_test fields
```

## Files

**Create**

- `ML/baseline/benchmark_fractal0_entry_quality_filter.py` — bounded wrapper для ML-entry фильтра; не самостоятельная копия текущего симулятора.
- `tests/test_fractal0_entry_quality_filter.py`
- `docs/ML/benchmark_fractal0_entry_quality_filter.py.md`
- `docs/reports/2026-07-21-fractal0-entry-quality-filter.md`

**Modify if needed**

- `ML/baseline/benchmark_fractal0_entry_exit_grid.py` only for reusable helper extraction with no behavior change.
- `tests/test_fractal0_entry_exit_grid.py` only if helper extraction requires import adjustments.

**Generated**

- `ML/reports/fractal0_entry_quality_filter.json`
- `ML/reports/fractal0_entry_quality_filter_summary.csv`
- `ML/reports/fractal0_entry_quality_filter_trades.csv`
- `ML/reports/fractal0_entry_quality_filter_scores.csv`
- `ML/reports/fractal0_entry_quality_filter_yearly.csv`
- `ML/reports/fractal0_entry_quality_filter_permutation.csv`

JSON artifact must contain:

```text
input_artifact_hashes
current_search_budget
cumulative_search_budget
stop_policy_id
exit_policy_id_used_for_entry_labels
filter_id
score_cutoff_on_val_select
actual_val_eval_selected_fraction
actual_val_eval_selected_trades
locked_test = not_opened
```

---

### Task 1: Create Entry Filter Registry And TopX Selection

**Files:**
- Create: `ML/baseline/benchmark_fractal0_entry_quality_filter.py`
- Create: `tests/test_fractal0_entry_quality_filter.py`

**Interfaces:**
- Produces: `entry_filter_grid() -> list[dict[str, object]]`
- Produces: `select_top_fraction(rows: pd.DataFrame, score_col: str, fraction: float) -> pd.DataFrame`
- Produces: `score_cutoff_for_top_fraction(rows: pd.DataFrame, score_col: str, fraction: float) -> float`

- [x] **Step 1: Add tests**

Create `tests/test_fractal0_entry_quality_filter.py`:

```python
import pandas as pd

import ML.baseline.benchmark_fractal0_entry_quality_filter as runner


def test_entry_filter_grid_contains_baseline_movement_and_entry_quality_filters():
    ids = [item["filter_id"] for item in runner.entry_filter_grid()]
    assert ids == [
        "M0_no_mask",
        "movement_top50",
        "movement_top30",
        "movement_top20",
        "movement_top10",
        "simple_stop_distance_top50",
        "simple_stop_distance_top30",
        "simple_r_value_top50",
        "simple_r_value_top30",
        "entry_quality_top50",
        "entry_quality_top30",
        "entry_quality_top20",
        "entry_quality_top10",
        "entry_avoid_sl_top50",
        "entry_avoid_sl_top30",
        "entry_avoid_sl_top20",
        "entry_avoid_sl_top10",
    ]


def test_select_top_fraction_keeps_highest_scores_and_cutoff():
    rows = pd.DataFrame({"score": [0.1, 0.9, 0.5, 0.7], "id": [1, 2, 3, 4]})
    selected = runner.select_top_fraction(rows, "score", 0.5)
    assert selected["id"].tolist() == [2, 4]
    assert runner.score_cutoff_for_top_fraction(rows, "score", 0.5) == 0.7
```

- [x] **Step 2: Run failing tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_entry_quality_filter.py -q
```

Expected: FAIL because module does not exist.

- [x] **Step 3: Implement module skeleton**

Create `ML/baseline/benchmark_fractal0_entry_quality_filter.py`:

```python
from __future__ import annotations

import math

import pandas as pd


def entry_filter_grid() -> list[dict[str, object]]:
    filters: list[dict[str, object]] = [{"filter_id": "M0_no_mask", "family": "none", "score_col": None, "top_fraction": 1.0}]
    for fraction in (0.50, 0.30, 0.20, 0.10):
        filters.append({"filter_id": f"movement_top{int(fraction * 100)}", "family": "movement", "score_col": "movement_score", "top_fraction": fraction})
    for fraction in (0.50, 0.30):
        filters.append({"filter_id": f"simple_stop_distance_top{int(fraction * 100)}", "family": "simple_stop_distance", "score_col": "stop_distance_atr", "top_fraction": fraction})
    for fraction in (0.50, 0.30):
        filters.append({"filter_id": f"simple_r_value_top{int(fraction * 100)}", "family": "simple_r_value", "score_col": "r_value_atr", "top_fraction": fraction})
    for fraction in (0.50, 0.30, 0.20, 0.10):
        filters.append({"filter_id": f"entry_quality_top{int(fraction * 100)}", "family": "entry_quality", "score_col": "entry_quality_score", "top_fraction": fraction})
    for fraction in (0.50, 0.30, 0.20, 0.10):
        filters.append({"filter_id": f"entry_avoid_sl_top{int(fraction * 100)}", "family": "entry_avoid_sl", "score_col": "entry_avoid_sl_score", "top_fraction": fraction})
    return filters


def score_cutoff_for_top_fraction(rows: pd.DataFrame, score_col: str, fraction: float) -> float:
    if rows.empty:
        return math.nan
    count = max(1, int(math.ceil(len(rows) * float(fraction))))
    return float(rows[score_col].sort_values(ascending=False).iloc[count - 1])


def select_top_fraction(rows: pd.DataFrame, score_col: str, fraction: float) -> pd.DataFrame:
    if rows.empty:
        return rows.copy()
    count = max(1, int(math.ceil(len(rows) * float(fraction))))
    return rows.sort_values(score_col, ascending=False).head(count).copy()
```

- [x] **Step 4: Run tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_entry_quality_filter.py -q
```

Expected: PASS.

### Task 2: Build Entry Labels From E3 Trades

**Files:**
- Modify: `ML/baseline/benchmark_fractal0_entry_quality_filter.py`
- Modify: `tests/test_fractal0_entry_quality_filter.py`

**Interfaces:**
- Produces: `build_entry_labels(trades: pd.DataFrame) -> pd.DataFrame`

- [x] **Step 1: Add label tests**

Add:

```python
def test_build_entry_labels_distinguishes_good_from_avoid_sl():
    trades = pd.DataFrame(
        [
            {"position_id": "a", "pnl_r": -1.0, "close_reason": "SL"},
            {"position_id": "b", "pnl_r": -0.2, "close_reason": "ML_CLOSE"},
            {"position_id": "c", "pnl_r": 0.4, "close_reason": "ML_CLOSE"},
        ]
    )
    labels = runner.build_entry_labels(trades).set_index("position_id")
    assert labels.loc["a", "target_entry_good"] == 0
    assert labels.loc["a", "target_entry_avoid_sl"] == 0
    assert labels.loc["b", "target_entry_good"] == 0
    assert labels.loc["b", "target_entry_avoid_sl"] == 1
    assert labels.loc["c", "target_entry_good"] == 1
    assert labels.loc["c", "target_entry_avoid_sl"] == 1
```

- [x] **Step 2: Implement labels**

Add:

```python
def build_entry_labels(trades: pd.DataFrame) -> pd.DataFrame:
    out = trades.copy()
    out["target_entry_good"] = (pd.to_numeric(out["pnl_r"], errors="coerce") > 0.0).astype(int)
    out["target_entry_avoid_sl"] = (~out["close_reason"].astype(str).eq("SL")).astype(int)
    return out
```

- [x] **Step 3: Run tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_entry_quality_filter.py -q
```

Expected: PASS.

### Task 3: Build Entry Feature Matrix

**Files:**
- Modify: `ML/baseline/benchmark_fractal0_entry_quality_filter.py`
- Modify: `tests/test_fractal0_entry_quality_filter.py`

**Interfaces:**
- Produces: `ENTRY_FEATURE_COLUMNS: list[str]`
- Produces: `build_entry_feature_frame(entries: pd.DataFrame) -> pd.DataFrame`

- [x] **Step 1: Add tests forbidding future columns**

Add:

```python
def test_entry_features_exclude_future_and_target_columns():
    assert not any(col.startswith(("future_", "target_", "pnl_")) for col in runner.ENTRY_FEATURE_COLUMNS)
    assert {"close_reason", "hold_bars", "exit_time"}.isdisjoint(runner.ENTRY_FEATURE_COLUMNS)


def test_build_entry_feature_frame_adds_direction_and_distance_features():
    entries = pd.DataFrame(
        {
            "side": ["BUY", "SELL"],
            "ATR": [2.0, 2.0],
            "fractal0_price": [100.0, 100.0],
            "entry_bid_equivalent": [101.0, 99.0],
            "protective_stop_price": [97.0, 103.0],
            "r_value": [4.0, 4.0],
        }
    )
    frame = runner.build_entry_feature_frame(entries)
    assert frame["side_buy"].tolist() == [1, 0]
    assert frame["entry_to_fractal0_atr"].tolist() == [0.5, -0.5]
    assert frame["r_value_atr"].tolist() == [2.0, 2.0]
```

- [x] **Step 2: Implement features**

Add:

```python
ENTRY_FEATURE_COLUMNS = [
    "side_buy",
    "ATR",
    "entry_to_fractal0_atr",
    "stop_distance_atr",
    "r_value_atr",
]


def build_entry_feature_frame(entries: pd.DataFrame) -> pd.DataFrame:
    out = entries.copy()
    atr = pd.to_numeric(out["ATR"], errors="coerce").replace(0, pd.NA)
    out["side_buy"] = out["side"].astype(str).eq("BUY").astype(int)
    out["entry_to_fractal0_atr"] = (pd.to_numeric(out["entry_bid_equivalent"], errors="coerce") - pd.to_numeric(out["fractal0_price"], errors="coerce")) / atr
    out["stop_distance_atr"] = (pd.to_numeric(out["entry_bid_equivalent"], errors="coerce") - pd.to_numeric(out["protective_stop_price"], errors="coerce")).abs() / atr
    out["r_value_atr"] = pd.to_numeric(out["r_value"], errors="coerce") / atr
    return out
```

- [x] **Step 3: Run tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_entry_quality_filter.py -q
```

Expected: PASS.

### Task 4: Train And Score Entry Models

**Files:**
- Modify: `ML/baseline/benchmark_fractal0_entry_quality_filter.py`
- Modify: `tests/test_fractal0_entry_quality_filter.py`

**Interfaces:**
- Produces: `train_entry_models(train_rows: pd.DataFrame, threads: int, seeds: tuple[int, ...]) -> dict[str, object]`
- Produces: `score_entry_models(models: dict[str, object], rows: pd.DataFrame) -> pd.DataFrame`

- [x] **Step 1: Add smoke model test**

Add:

```python
def test_train_and_score_entry_models_adds_scores():
    rows = pd.DataFrame(
        {
            "side": ["BUY", "SELL", "BUY", "SELL"],
            "ATR": [2.0, 2.0, 3.0, 3.0],
            "fractal0_price": [100.0, 100.0, 100.0, 100.0],
            "entry_bid_equivalent": [101.0, 99.0, 103.0, 97.0],
            "protective_stop_price": [97.0, 103.0, 96.0, 104.0],
            "r_value": [4.0, 4.0, 7.0, 7.0],
            "target_entry_good": [1, 0, 1, 0],
            "target_entry_avoid_sl": [1, 0, 1, 0],
        }
    )
    models = runner.train_entry_models(rows, threads=1, seeds=(1,), n_estimators=5)
    scored = runner.score_entry_models(models, rows)
    assert "entry_quality_score" in scored
    assert "entry_avoid_sl_score" in scored
```

- [x] **Step 2: Implement train/score**

Add:

```python
from sklearn.ensemble import ExtraTreesClassifier


def train_entry_models(
    train_rows: pd.DataFrame,
    threads: int,
    seeds: tuple[int, ...] = (42, 43, 44),
    n_estimators: int = 200,
) -> dict[str, object]:
    frame = build_entry_feature_frame(train_rows)
    x = frame[ENTRY_FEATURE_COLUMNS].fillna(0.0)
    models: dict[str, object] = {}
    targets = {"entry_quality_score": "target_entry_good", "entry_avoid_sl_score": "target_entry_avoid_sl"}
    for score_col, target_col in targets.items():
        y = frame[target_col].astype(int)
        fitted = []
        if y.nunique() < 2:
            models[score_col] = [float(y.iloc[0]) if len(y) else 0.0]
            continue
        for seed in seeds:
            clf = ExtraTreesClassifier(n_estimators=n_estimators, max_depth=8, min_samples_leaf=50, random_state=seed, n_jobs=threads)
            clf.fit(x, y)
            fitted.append(clf)
        models[score_col] = fitted
    return models


def score_entry_models(models: dict[str, object], rows: pd.DataFrame) -> pd.DataFrame:
    out = build_entry_feature_frame(rows)
    x = out[ENTRY_FEATURE_COLUMNS].fillna(0.0)
    for score_col, fitted in models.items():
        values = []
        for model in fitted:
            if isinstance(model, float):
                values.append([model] * len(out))
            else:
                values.append(model.predict_proba(x)[:, 1])
        out[score_col] = pd.DataFrame(values).median(axis=0).to_numpy() if values else 0.0
    return out
```

- [x] **Step 3: Run tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_entry_quality_filter.py -q
```

Expected: PASS.

### Task 5: Integrate With E3 Simulation

**Files:**
- Modify: `ML/baseline/benchmark_fractal0_entry_quality_filter.py`
- Modify: `tests/test_fractal0_entry_quality_filter.py`

**Interfaces:**
- Reuses from `ML.baseline.benchmark_fractal0_entry_exit_grid`:
  - `load_ohlc`
  - `load_role_splits`
  - `build_entry_rows`
  - `_train_ml_exit_layer`
  - `_simulate_entries`
  - `compute_trade_metrics`
  - `block_bootstrap_pf`
  - `simulate_trade`
  - `prepare_execution_ohlc_index`

- [x] **Step 1: Add runner preflight smoke test with tiny frames**

Add a pure-function test for applying filters:

```python
def test_apply_entry_filter_no_mask_and_top_fraction():
    rows = pd.DataFrame({"position_id": ["a", "b", "c"], "entry_quality_score": [0.2, 0.9, 0.6]})
    no_mask = runner.apply_entry_filter(rows, {"filter_id": "M0_no_mask", "family": "none", "top_fraction": 1.0, "score_col": None})
    top = runner.apply_entry_filter(rows, {"filter_id": "entry_quality_top50", "family": "entry_quality", "top_fraction": 0.5, "score_col": "entry_quality_score"}, mode="select")
    assert no_mask["position_id"].tolist() == ["a", "b", "c"]
    assert top["position_id"].tolist() == ["b", "c"]
    assert top.attrs["score_cutoff_on_val_select"] == 0.6


def test_apply_entry_filter_uses_val_select_cutoff_on_val_eval():
    val_eval = pd.DataFrame({"position_id": ["a", "b", "c"], "entry_quality_score": [0.95, 0.61, 0.59]})
    selected = runner.apply_entry_filter(
        val_eval,
        {"filter_id": "entry_quality_top50", "family": "entry_quality", "top_fraction": 0.5, "score_col": "entry_quality_score"},
        mode="eval",
        score_cutoff=0.60,
    )
    assert selected["position_id"].tolist() == ["a", "b"]
```

- [x] **Step 2: Implement `apply_entry_filter`**

Add:

```python
def apply_entry_filter(entries: pd.DataFrame, filter_rule: dict[str, object], mode: str = "select", score_cutoff: float | None = None) -> pd.DataFrame:
    if filter_rule["family"] == "none":
        out = entries.copy()
        out["entry_filter_selected"] = True
        out["entry_filter_score_cutoff"] = None
        return out
    score_col = str(filter_rule["score_col"])
    if mode == "select":
        cutoff = score_cutoff_for_top_fraction(entries, score_col, float(filter_rule["top_fraction"]))
        out = entries.loc[pd.to_numeric(entries[score_col], errors="coerce") >= cutoff].copy()
    elif mode == "eval":
        if score_cutoff is None:
            raise ValueError("score_cutoff is required when applying filter in eval mode")
        cutoff = float(score_cutoff)
        out = entries.loc[pd.to_numeric(entries[score_col], errors="coerce") >= cutoff].copy()
    else:
        raise ValueError(f"unknown filter mode: {mode}")
    out["entry_filter_selected"] = True
    out["entry_filter_score_cutoff"] = cutoff
    out.attrs["score_cutoff_on_val_select"] = cutoff
    return out
```

- [x] **Step 3: Implement CLI skeleton**

Add `main()` with:

```text
--threads
--no-resume
--output-prefix ML/reports/fractal0_entry_quality_filter
--execution-ohlc-path MT/MQL4/Files/XAUUSD_M5_OHLC.csv
--stop-policy-id
--permutation-repeats
--smoke-limit-filters
```

The runner must:

1. Load H1, M5, train/validation splits.
2. Build E3 entries for `train_core`, `val_select`, `val_eval` using selected stop policy.
3. Train ML-exit on `train_core`.
4. Simulate unfiltered E3 trades to build entry labels.
5. Train entry models on labelled `train_core` entries.
6. Score `val_select` and `val_eval` entries.
7. Add movement scores from frozen movement artifact.
8. Apply each filter on `val_select` in `mode="select"` and save `score_cutoff_on_val_select`.
9. Apply the same filter on `val_eval` in `mode="eval"` with saved cutoff.
10. Simulate filtered trades using `exit_policy_id` from stop-grid winner.
11. Select winner on `val_select`, evaluate on `val_eval`.

- [x] **Step 4: Run smoke**

Run:

```bash
PYTHONUNBUFFERED=1 ./.venv/bin/python ML/baseline/benchmark_fractal0_entry_quality_filter.py \
  --threads 2 \
  --no-resume \
  --output-prefix /tmp/fractal0_entry_quality_filter_smoke \
  --execution-ohlc-path MT/MQL4/Files/XAUUSD_M5_OHLC.csv \
  --stop-policy-id S0_current_0_5 \
  --smoke-limit-filters 3 \
  --permutation-repeats 5
```

Expected:

```text
finished fractal0_entry_quality_filter
```

### Task 6: Full Entry Quality Run

**Files:**
- Generated: `ML/reports/fractal0_entry_quality_filter*`

- [x] **Step 1: Choose stop policy**

Use the winner or explicitly chosen policy from `ML/reports/fractal0_stop_grid_m5.json`.

For full research run, stop if stop-grid is not finished:

```python
raise SystemExit("entry-quality full run requires completed stop-grid and explicit stop_policy_id")
```

For smoke/debug only, allow the historical current policy:

```text
S0_current_0_5
```

and write `stop_policy_source = smoke_fallback_current_policy` in JSON.
Artifacts with this fallback are not eligible for final ranking, report
conclusions, or handoff recommendations.

- [x] **Step 2: Launch full run**

Run and return to chat after launch if user asks not to wait:

```bash
PYTHONUNBUFFERED=1 ./.venv/bin/python ML/baseline/benchmark_fractal0_entry_quality_filter.py \
  --threads 24 \
  --no-resume \
  --output-prefix ML/reports/fractal0_entry_quality_filter \
  --execution-ohlc-path MT/MQL4/Files/XAUUSD_M5_OHLC.csv \
  --stop-policy-id <STOP_POLICY_ID_FROM_STOP_GRID> \
  --permutation-repeats 200
```

- [x] **Step 3: Verify artifacts**

Use bounded reads:

```bash
./.venv/bin/python - <<'PY'
import json
from pathlib import Path
import pandas as pd
p = Path("ML/reports/fractal0_entry_quality_filter.json")
d = json.load(p.open())
print(d["selected_winner"])
print(d["val_eval_winner_metrics"])
print(pd.read_csv("ML/reports/fractal0_entry_quality_filter_summary.csv", sep=";", nrows=5).to_string())
PY
```

Expected:

```text
JSON contains selected_winner, val_select_winner_metrics, val_eval_winner_metrics
summary includes 13 filter rows per split
```

### Task 7: Report, Docs, And Wiki

**Files:**
- Create: `docs/ML/benchmark_fractal0_entry_quality_filter.py.md`
- Create: `docs/reports/2026-07-21-fractal0-entry-quality-filter.md`
- Modify: `CHANGELOG.md`
- Modify: `CONTEXT_HANDOFF.md`
- Modify: `wiki/research/fractal-stop-research.md`
- Modify: `wiki/index.md`
- Modify: `wiki/log.md`
- Modify: `wiki/REPO_integrity.md`

- [x] **Step 1: Write runner docs**

Document:

```text
purpose
inputs
outputs
entry target definitions
entry feature contract
forbidden future-derived columns
CLI command
research-only verdict limit
```

- [x] **Step 2: Write stage report**

Report must include:

```text
M0_no_mask baseline
movement_top50/top30/top20/top10 results
entry_quality_top50/top30/top20/top10 results
entry_avoid_sl_top50/top30/top20/top10 results
winner chosen on val_select
val_eval metrics without changing winner
score_cutoff_on_val_select for winner
actual_val_eval_selected_fraction for winner
trade count and yearly stability
SL-rate change versus no-mask
locked_test = not_opened
allowed_max_verdict = research_only
```

- [x] **Step 3: Run verification**

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_entry_quality_filter.py -q
./.venv/bin/python -m pytest tests/test_fractal0_entry_exit_grid.py -q
./.venv/bin/python wiki/wiki.py status
```

Expected:

```text
tests pass
Wiki is up to date. No gaps found.
```

If wiki has gaps:

```bash
./.venv/bin/python wiki/wiki.py generate
```
