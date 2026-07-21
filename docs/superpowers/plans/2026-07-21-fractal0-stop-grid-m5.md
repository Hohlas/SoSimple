# Fractal0 Stop Grid M5 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Проверить, улучшает ли stop-policy grid систему Fractal0 E3/E2/E1 + текущий ML-exit без открытия `locked_test` и без stress-spread на этапе выбора.

**Architecture:** Расширить существующий `ML/baseline/benchmark_fractal0_entry_exit_grid.py` так, чтобы stop policy была частью grid/run key и влияла на `protective_stop_price`, `R`, ML-exit targets, ML-exit признаки и итоговые метрики. Запускать clean M5 execution contract, выбирать winner только на `val_select`, проверять на `val_eval`; stress-spread вынести в отдельный последующий shortlist-прогон.

**Tech Stack:** Python 3.10+, pandas, numpy, scikit-learn `ExtraTreesClassifier`, pytest, `./.venv/bin/python`, существующий runner `ML/baseline/benchmark_fractal0_entry_exit_grid.py`.

## Global Constraints

- Работать в текущей ветке; worktree не создавать.
- Использовать `./.venv/bin/python` для Python-команд.
- `locked_test` не открывать.
- Максимальный verdict этапа: `research_only`.
- H1 остаётся источником признаков, split и trading rows.
- M5 `MT/MQL4/Files/XAUUSD_M5_OHLC.csv` используется только для порядка исполнения внутри H1-свечи.
- Project CSV читать с `sep=";"`; большие CSV не читать целиком без `nrows`, `usecols` или `chunksize`.
- Stop policy является частью `run_config_hash`, `resume_key`, summary rows, trades rows и JSON artifact.
- Stop policy является частью всех ключей сопоставления: `filter_trades_for_rule`, `compute_attribution`, `evaluate_winner_on_val_eval`, `run_selection_permutation`, stress/shortlist matching и любые groupby для summary/trades.
- ML-exit модель нужно обучать отдельно для каждой stop policy, потому что `R`, признаки в `R` и `target_exit_*` меняются.
- Stress-spread в этом плане не запускать по всей сетке; добавить CLI-флаг для отключения stress и явно записать `stress_spread_status = "deferred_shortlist_only"`.
- Результаты в `R` трактуются как фиксированный риск на сделку, а не фиксированный лот. Wider stop меняет денежный риск при фиксированном лоте; это явно раскрывается в отчёте.
- Preflight обязателен: входные файлы, CSV-разделители, нужные колонки, split-роли, `locked_test=not_opened`, hashes входов.
- После Python-изменений запустить `./.venv/bin/python -m pytest tests/test_fractal0_entry_exit_grid.py -q`; перед отчётом запустить `./.venv/bin/python -m pytest tests/ -q`, если время позволяет.

---

## Research Contract

### Stop Policies

Включить четыре stop policy:

```text
S0_current_0_5:
  BUY  stop = min(fractal0_price, entry_bid_equivalent) - 0.5 * ATR
  SELL stop = max(fractal0_price, entry_bid_equivalent) + 0.5 * ATR

S1_fractal0_buffer_0_5_entry_floor_1:
  BUY  stop = min(fractal0_price - 0.5 * ATR, entry_bid_equivalent - 1.0 * ATR)
  SELL stop = max(fractal0_price + 0.5 * ATR, entry_bid_equivalent + 1.0 * ATR)

S2_fractal0_buffer_0_5_entry_floor_2:
  BUY  stop = min(fractal0_price - 0.5 * ATR, entry_bid_equivalent - 2.0 * ATR)
  SELL stop = max(fractal0_price + 0.5 * ATR, entry_bid_equivalent + 2.0 * ATR)

S3_fractal0_buffer_0_5_entry_floor_3:
  BUY  stop = min(fractal0_price - 0.5 * ATR, entry_bid_equivalent - 3.0 * ATR)
  SELL stop = max(fractal0_price + 0.5 * ATR, entry_bid_equivalent + 3.0 * ATR)
```

### Search Grid

Основной дешёвый grid:

```text
stop_policy: S0/S1/S2/S3
entry: E1_simple_limit_at_fractal0, E2_open_pullback_0_5atr, E3_open_pullback_1_0atr
mask: M0_no_mask, M1_frozen_movement_top5
exit shortlist:
  X0_fixed_r_0_7
  X1_ml_opposite_strong_p0_55/p0_65/p0_75
  X2_ml_opposite_any_p0_50/p0_55/p0_60
  X3_ml_hold_close_p0_50/p0_60/p0_70
  X7_time_6
  X7_time_12
```

Budget:

```text
4 stop policies x 3 entries x 2 masks x 12 exits = 288 canonical selection cells
4 stop policies x 12 ML-exit jobs = 48 model jobs
stress-spread = skipped/deferred
```

### Selection Gates

Winner selection remains:

```text
n_trades >= 300
negative_years <= 1
mean_pnl_r > 0
pf_without_best_year >= 1.10
sort by bs_p05 desc, then simpler threshold count, then max_drawdown_r asc
```

Report additional stop diagnostics:

```text
stop_policy_id
stop_source counts: current_entry_or_fractal_anchor / fractal0_buffer / entry_floor
SL-rate by stop_source
median_stop_distance_atr
p10/p90_stop_distance_atr
mean_r_value
median_r_value
risk_distance_atr
tp_distance_atr for fixed-R exits
```

## Files

**Modify**

- `ML/baseline/benchmark_fractal0_entry_exit_grid.py`
- `tests/test_fractal0_entry_exit_grid.py`
- `docs/ML/benchmark_fractal0_entry_exit_grid.py.md`

**Create after run**

- `docs/reports/2026-07-21-fractal0-stop-grid-m5.md`

**Generated**

- `ML/reports/fractal0_stop_grid_m5.json`
- `ML/reports/fractal0_stop_grid_m5_summary.csv`
- `ML/reports/fractal0_stop_grid_m5_trades.csv`
- `ML/reports/fractal0_stop_grid_m5_progress.json`
- `ML/reports/fractal0_stop_grid_m5_permutation.csv`
- `ML/reports/fractal0_stop_grid_m5_stop_diagnostics.csv`

JSON artifact must contain:

```text
input_artifact_hashes
current_search_budget
cumulative_search_budget
stop_policy_grid
stop_policy_id
winner_selection_key = stop_policy_id + entry_id + mask_id + exit_id
permutation_key = stop_policy_id + entry_id + mask_id + exit_id
stress_spread_status
fixed_risk_interpretation = pnl_r assumes equal risk per trade, not equal lot size
```

---

### Task 1: Add Stop Policy Registry And Stop Calculator

**Files:**
- Modify: `ML/baseline/benchmark_fractal0_entry_exit_grid.py`
- Modify: `tests/test_fractal0_entry_exit_grid.py`

**Interfaces:**
- Produces: `stop_policy_grid() -> list[dict[str, object]]`
- Produces: `resolve_protective_stop(side: str, fractal0_price: float, entry_bid_equivalent: float, atr: float, stop_policy: dict[str, object] | None = None) -> dict[str, object]`
- Maintains: `protective_stop_price(...) -> float` as compatibility wrapper.
- Produces stop-policy fields in entry rows: `stop_policy_id`, `stop_family`, `entry_floor_atr`, `fractal0_buffer_atr`.
- Produces diagnostics fields in entry/trade rows: `stop_source`, `stop_distance_atr`, `risk_distance_atr`.

- [ ] **Step 1: Add failing tests for stop policies**

Add tests:

```python
def test_stop_policy_grid_has_current_and_entry_floor_variants():
    ids = [item["stop_policy_id"] for item in runner.stop_policy_grid()]
    assert ids == [
        "S0_current_0_5",
        "S1_fractal0_buffer_0_5_entry_floor_1",
        "S2_fractal0_buffer_0_5_entry_floor_2",
        "S3_fractal0_buffer_0_5_entry_floor_3",
    ]


def test_entry_floor_stop_keeps_buy_stop_at_least_x_atr_from_entry():
    policy = {
        "stop_policy_id": "S2_fractal0_buffer_0_5_entry_floor_2",
        "family": "fractal0_buffer_entry_floor",
        "fractal0_buffer_atr": 0.5,
        "entry_floor_atr": 2.0,
    }
    resolved = runner.resolve_protective_stop("BUY", 100.0, 101.0, 2.0, policy)
    assert resolved["protective_stop_price"] == 97.0
    assert resolved["stop_source"] == "entry_floor"


def test_entry_floor_stop_keeps_sell_stop_at_least_x_atr_from_entry():
    policy = {
        "stop_policy_id": "S3_fractal0_buffer_0_5_entry_floor_3",
        "family": "fractal0_buffer_entry_floor",
        "fractal0_buffer_atr": 0.5,
        "entry_floor_atr": 3.0,
    }
    resolved = runner.resolve_protective_stop("SELL", 100.0, 99.0, 2.0, policy)
    assert resolved["protective_stop_price"] == 105.0
    assert resolved["stop_source"] == "entry_floor"
```

- [ ] **Step 2: Run focused failing tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_entry_exit_grid.py -k "stop_policy_grid or entry_floor_stop" -q
```

Expected: FAIL because `stop_policy_grid` and the new signature are not implemented.

- [ ] **Step 3: Implement stop policy registry**

Add near `mask_grid()`:

```python
def stop_policy_grid() -> list[dict[str, object]]:
    return [
        {"stop_policy_id": "S0_current_0_5", "family": "current", "fractal0_buffer_atr": 0.5, "entry_floor_atr": 0.5},
        {"stop_policy_id": "S1_fractal0_buffer_0_5_entry_floor_1", "family": "fractal0_buffer_entry_floor", "fractal0_buffer_atr": 0.5, "entry_floor_atr": 1.0},
        {"stop_policy_id": "S2_fractal0_buffer_0_5_entry_floor_2", "family": "fractal0_buffer_entry_floor", "fractal0_buffer_atr": 0.5, "entry_floor_atr": 2.0},
        {"stop_policy_id": "S3_fractal0_buffer_0_5_entry_floor_3", "family": "fractal0_buffer_entry_floor", "fractal0_buffer_atr": 0.5, "entry_floor_atr": 3.0},
    ]
```

- [ ] **Step 4: Add `resolve_protective_stop` and update `protective_stop_price`**

Add:

```python
def resolve_protective_stop(
    side: str,
    fractal0_price: float,
    entry_bid_equivalent: float,
    atr: float,
    stop_policy: dict[str, object] | None = None,
) -> dict[str, object]:
    policy = stop_policy or stop_policy_grid()[0]
    family = str(policy.get("family", "current"))
    fractal_buffer = float(policy.get("fractal0_buffer_atr", CONFIG.protective_stop_atr))
    entry_floor = float(policy.get("entry_floor_atr", CONFIG.protective_stop_atr))
    if family == "current":
        if side == "BUY":
            stop = float(min(fractal0_price, entry_bid_equivalent) - fractal_buffer * atr)
        else:
            stop = float(max(fractal0_price, entry_bid_equivalent) + fractal_buffer * atr)
        source = "current_entry_or_fractal_anchor"
    elif family == "fractal0_buffer_entry_floor":
        if side == "BUY":
            fractal_stop = float(fractal0_price - fractal_buffer * atr)
            floor_stop = float(entry_bid_equivalent - entry_floor * atr)
            stop = min(fractal_stop, floor_stop)
            source = "fractal0_buffer" if fractal_stop <= floor_stop else "entry_floor"
        else:
            fractal_stop = float(fractal0_price + fractal_buffer * atr)
            floor_stop = float(entry_bid_equivalent + entry_floor * atr)
            stop = max(fractal_stop, floor_stop)
            source = "fractal0_buffer" if fractal_stop >= floor_stop else "entry_floor"
    else:
        raise ValueError(f"unknown stop policy family: {family}")
    distance_atr = abs(entry_bid_equivalent - stop) / atr if atr else float("nan")
    return {"protective_stop_price": stop, "stop_source": source, "stop_distance_atr": distance_atr, "risk_distance_atr": distance_atr}


def protective_stop_price(
    side: str,
    fractal0_price: float,
    entry_bid_equivalent: float,
    atr: float,
    stop_policy: dict[str, object] | None = None,
) -> float:
    return float(resolve_protective_stop(side, fractal0_price, entry_bid_equivalent, atr, stop_policy)["protective_stop_price"])
```

- [ ] **Step 5: Run tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_entry_exit_grid.py -k "stop_policy_grid or entry_floor_stop or protective_stop_uses_fixed_half_atr" -q
```

Expected: PASS.

### Task 2: Thread Stop Policy Through Entry Cache, Runs, Resume, And Artifacts

**Files:**
- Modify: `ML/baseline/benchmark_fractal0_entry_exit_grid.py`
- Modify: `tests/test_fractal0_entry_exit_grid.py`

**Interfaces:**
- `entry_grid` remains unchanged.
- `expanded_grid(active_stop_policies=None, active_entries=None, active_masks=None, active_exits=None)`.
- `resume_key` includes `stop_policy_id`.
- `build_entry_rows(..., stop_policy: dict[str, object] | None = None)`.
- `filter_trades_for_rule`, `compute_attribution`, `evaluate_winner_on_val_eval`, `run_selection_permutation` and stress/shortlist matching include `stop_policy_id`.

- [ ] **Step 1: Add failing tests**

Add:

```python
def test_expanded_grid_includes_stop_policy_id():
    grid = runner.expanded_grid(
        active_stop_policies=[{"stop_policy_id": "S0_current_0_5", "family": "current", "fractal0_buffer_atr": 0.5, "entry_floor_atr": 0.5}],
        active_entries=[runner.entry_grid()[0]],
        active_masks=[runner.mask_grid()[0]],
        active_exits=[runner.exit_grid()[0]],
    )
    assert grid[0]["stop_policy_id"] == "S0_current_0_5"


def test_resume_key_distinguishes_stop_policy():
    base = {"entry_id": "E3", "mask_id": "M0", "exit_id": "X2", "spread": 0.2, "stop_policy_id": "S0"}
    changed = {**base, "stop_policy_id": "S1"}
    assert runner.resume_key(base) != runner.resume_key(changed)


def test_evaluate_winner_on_val_eval_matches_stop_policy():
    winner = {"stop_policy_id": "S1", "entry_id": "E3", "mask_id": "M0", "exit_id": "X2"}
    rows = pd.DataFrame(
        [
            {"stop_policy_id": "S0", "entry_id": "E3", "mask_id": "M0", "exit_id": "X2", "pf": 9.0, "bs_p05": 9.0, "n_trades": 350},
            {"stop_policy_id": "S1", "entry_id": "E3", "mask_id": "M0", "exit_id": "X2", "pf": 1.5, "bs_p05": 1.2, "n_trades": 350},
        ]
    )
    assert runner.evaluate_winner_on_val_eval(winner, rows)["pf"] == 1.5


def test_filter_trades_for_rule_matches_stop_policy():
    trades = pd.DataFrame(
        [
            {"stop_policy_id": "S0", "entry_id": "E3", "mask_id": "M0", "exit_id": "X2", "split": "val_eval", "spread": 0.2, "pnl_r": 9.0},
            {"stop_policy_id": "S1", "entry_id": "E3", "mask_id": "M0", "exit_id": "X2", "split": "val_eval", "spread": 0.2, "pnl_r": 1.0},
        ]
    )
    selected = runner.filter_trades_for_rule(trades, {"stop_policy_id": "S1", "entry_id": "E3", "mask_id": "M0", "exit_id": "X2"}, split="val_eval", spread=0.2)
    assert selected["pnl_r"].tolist() == [1.0]
```

- [ ] **Step 2: Run failing tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_entry_exit_grid.py -k "expanded_grid_includes_stop_policy_id or resume_key_distinguishes_stop_policy" -q
```

Expected: FAIL.

- [ ] **Step 3: Update grid and resume**

Modify `expanded_grid` and `resume_key`:

```python
def expanded_grid(
    active_stop_policies: list[dict[str, object]] | None = None,
    active_entries: list[dict[str, object]] | None = None,
    active_masks: list[dict[str, object]] | None = None,
    active_exits: list[dict[str, object]] | None = None,
) -> list[dict[str, object]]:
    stops = active_stop_policies or stop_policy_grid()
    entries = active_entries or entry_grid()
    masks = active_masks or mask_grid()
    exits = active_exits or exit_grid()
    return [{**stop, **entry, **mask, **exit_rule, "spread": CONFIG.canonical_spread} for stop in stops for entry in entries for mask in masks for exit_rule in exits]


def resume_key(run: dict[str, object]) -> str:
    keys = ("stop_policy_id", "entry_id", "mask_id", "exit_id", "spread")
    if "split" in run:
        keys = (*keys, "split")
    return stable_json_hash({key: run.get(key) for key in keys})
```

- [ ] **Step 4: Update `build_entry_rows` call chain**

Change signature:

```python
def build_entry_rows(rows: pd.DataFrame, ohlc: pd.DataFrame, entry_rule: dict[str, object], spread: float, stop_policy: dict[str, object] | None = None) -> pd.DataFrame:
```

Use:

```python
policy = stop_policy or stop_policy_grid()[0]
stop_info = resolve_protective_stop(side, fractal["price"], float(fill["entry_bid_equivalent"]) if fill["filled"] else limit_price, atr, policy)
stop = float(stop_info["protective_stop_price"])
```

Append fields:

```python
"stop_policy_id": policy["stop_policy_id"],
"stop_family": policy["family"],
"entry_floor_atr": policy["entry_floor_atr"],
"fractal0_buffer_atr": policy["fractal0_buffer_atr"],
"stop_source": stop_info["stop_source"],
"stop_distance_atr": stop_info["stop_distance_atr"],
"risk_distance_atr": stop_info["risk_distance_atr"],
```

- [ ] **Step 5: Update `_entry_cache_for_spread`**

Add `stop_policies` argument and include stop id in cache key:

```python
cache: dict[tuple[str, str, str, str], pd.DataFrame] = {}
...
for stop_policy in stop_policies:
    entry_rows = build_entry_rows(rows, ohlc, entry, spread, stop_policy)
    ...
    cache[(split, str(stop_policy["stop_policy_id"]), str(entry["entry_id"]), str(mask["mask_id"]))] = masked
```

Rows disclosure key:

```python
f"{stop_policy['stop_policy_id']}:{entry['entry_id']}:{mask['mask_id']}"
```

- [ ] **Step 6: Update all matching keys**

Change all selection/evaluation matching from:

```text
entry_id + mask_id + exit_id
```

to:

```text
stop_policy_id + entry_id + mask_id + exit_id
```

Required places:

```text
filter_trades_for_rule
compute_attribution
evaluate_winner_on_val_eval
run_selection_permutation key_cols
stress_match / shortlist_match
selected_winner / val_select_winner_metrics / val_eval_winner_metrics serialization
```

- [ ] **Step 7: Run focused tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_entry_exit_grid.py -q
```

Expected: PASS.

### Task 3: Add Stop Shortlist CLI And Disable Full Stress

**Files:**
- Modify: `ML/baseline/benchmark_fractal0_entry_exit_grid.py`
- Modify: `tests/test_fractal0_entry_exit_grid.py`

**Interfaces:**
- CLI:
  - `--stop-grid-mode full|current-only`
  - `--exit-shortlist stop_grid`
  - `--skip-stress-spread`
  - `--output-prefix ML/reports/fractal0_stop_grid_m5`

- [ ] **Step 1: Add tests for shortlist contents**

Add:

```python
def test_stop_grid_exit_shortlist_is_bounded():
    exits = runner.exit_grid(shortlist="stop_grid")
    ids = {item["exit_id"] for item in exits}
    assert ids == {
        "X0_fixed_r_0_7",
        "X1_ml_opposite_strong_p0_55",
        "X1_ml_opposite_strong_p0_65",
        "X1_ml_opposite_strong_p0_75",
        "X2_ml_opposite_any_p0_50",
        "X2_ml_opposite_any_p0_55",
        "X2_ml_opposite_any_p0_60",
        "X3_ml_hold_close_p0_50",
        "X3_ml_hold_close_p0_60",
        "X3_ml_hold_close_p0_70",
        "X7_time_6",
        "X7_time_12",
    }
```

- [ ] **Step 2: Run failing test**

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_entry_exit_grid.py -k stop_grid_exit_shortlist -q
```

Expected: FAIL.

- [ ] **Step 3: Implement `exit_grid(shortlist=None)`**

Keep existing full grid as default. Add:

```python
if shortlist == "stop_grid":
    return [item for item in out if item["exit_id"] in STOP_GRID_EXIT_IDS]
```

Define:

```python
STOP_GRID_EXIT_IDS = {
    "X0_fixed_r_0_7",
    "X1_ml_opposite_strong_p0_55",
    "X1_ml_opposite_strong_p0_65",
    "X1_ml_opposite_strong_p0_75",
    "X2_ml_opposite_any_p0_50",
    "X2_ml_opposite_any_p0_55",
    "X2_ml_opposite_any_p0_60",
    "X3_ml_hold_close_p0_50",
    "X3_ml_hold_close_p0_60",
    "X3_ml_hold_close_p0_70",
    "X7_time_6",
    "X7_time_12",
}
```

- [ ] **Step 4: Add CLI arguments**

In `main` parser add:

```python
parser.add_argument("--stop-grid-mode", choices=("full", "current-only"), default="full")
parser.add_argument("--exit-shortlist", choices=("full", "stop_grid"), default="full")
parser.add_argument("--skip-stress-spread", action="store_true")
```

Build active lists:

```python
active_stop_policies = stop_policy_grid() if args.stop_grid_mode == "full" else [stop_policy_grid()[0]]
active_exits = exit_grid(None if args.exit_shortlist == "full" else args.exit_shortlist)
```

If `args.skip_stress_spread`, do not create stress entry cache and do not run stress loop; write:

```python
"stress_spread_status": "deferred_shortlist_only"
```

- [ ] **Step 5: Run tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_entry_exit_grid.py -q
```

Expected: PASS.

### Task 4: Add Stop Diagnostics

**Files:**
- Modify: `ML/baseline/benchmark_fractal0_entry_exit_grid.py`
- Modify: `tests/test_fractal0_entry_exit_grid.py`

**Interfaces:**
- Produces: `compute_stop_diagnostics(trades: pd.DataFrame) -> list[dict[str, object]]`
- Output CSV: `<prefix>_stop_diagnostics.csv`

- [ ] **Step 1: Add failing diagnostic test**

Add:

```python
def test_compute_stop_diagnostics_reports_source_sl_rate():
    trades = pd.DataFrame(
        [
            {"stop_policy_id": "S0", "split": "val_eval", "stop_source": "entry_floor", "close_reason": "SL", "stop_distance_atr": 0.5, "r_value": 1.0},
            {"stop_policy_id": "S0", "split": "val_eval", "stop_source": "entry_floor", "close_reason": "ML_CLOSE", "stop_distance_atr": 0.5, "r_value": 1.0},
            {"stop_policy_id": "S0", "split": "val_eval", "stop_source": "fractal0_buffer", "close_reason": "ML_CLOSE", "stop_distance_atr": 1.2, "r_value": 2.4},
        ]
    )
    rows = runner.compute_stop_diagnostics(trades)
    by_source = {(row["stop_policy_id"], row["stop_source"]): row for row in rows}
    assert by_source[("S0", "entry_floor")]["n_trades"] == 2
    assert by_source[("S0", "entry_floor")]["sl_rate"] == 0.5
```

- [ ] **Step 2: Implement diagnostics**

Carry these fields from entry rows into trade rows in `_simulate_entries`:

```text
stop_policy_id
stop_family
entry_floor_atr
fractal0_buffer_atr
stop_source
stop_distance_atr
risk_distance_atr
```

Add:

```python
def compute_stop_diagnostics(trades: pd.DataFrame) -> list[dict[str, object]]:
    if trades.empty:
        return []
    rows: list[dict[str, object]] = []
    group_cols = ["stop_policy_id", "split", "stop_source"]
    for keys, group in trades.groupby(group_cols, dropna=False):
        stop_policy_id, split, stop_source = keys
        close_reason = group["close_reason"].astype(str)
        rows.append(
            {
                "stop_policy_id": stop_policy_id,
                "split": split,
                "stop_source": stop_source,
                "n_trades": int(len(group)),
                "sl_count": int(close_reason.eq("SL").sum()),
                "sl_rate": float(close_reason.eq("SL").mean()),
                "median_stop_distance_atr": float(pd.to_numeric(group["stop_distance_atr"], errors="coerce").median()),
                "p10_stop_distance_atr": float(pd.to_numeric(group["stop_distance_atr"], errors="coerce").quantile(0.10)),
                "p90_stop_distance_atr": float(pd.to_numeric(group["stop_distance_atr"], errors="coerce").quantile(0.90)),
                "mean_r_value": float(pd.to_numeric(group["r_value"], errors="coerce").mean()),
                "median_r_value": float(pd.to_numeric(group["r_value"], errors="coerce").median()),
            }
        )
    return rows
```

- [ ] **Step 3: Write diagnostics CSV**

After trades concat:

```python
stop_diagnostics = pd.DataFrame(compute_stop_diagnostics(trades))
stop_diagnostics.to_csv(prefix.with_name(prefix.name + "_stop_diagnostics.csv"), index=False, sep=";")
```

Add to JSON:

```python
"stop_policy_grid": stop_policy_grid(),
"stop_diagnostics_status": "computed",
```

- [ ] **Step 4: Run tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_entry_exit_grid.py -q
```

Expected: PASS.

### Task 5: Run Smoke And Full Stop Grid

**Files:**
- Generated: `ML/reports/fractal0_stop_grid_m5*`

- [ ] **Step 1: Run smoke**

Run:

```bash
PYTHONUNBUFFERED=1 ./.venv/bin/python ML/baseline/benchmark_fractal0_entry_exit_grid.py \
  --threads 2 \
  --no-resume \
  --smoke-limit-runs 8 \
  --output-prefix /tmp/fractal0_stop_grid_m5_smoke \
  --execution-ohlc-path MT/MQL4/Files/XAUUSD_M5_OHLC.csv \
  --stop-grid-mode full \
  --exit-shortlist stop_grid \
  --skip-stress-spread \
  --permutation-repeats 5
```

Expected:

```text
finished fractal0_entry_exit_grid
```

- [ ] **Step 2: Run full stop-grid**

Run and return to chat after launch if user asks not to wait:

```bash
PYTHONUNBUFFERED=1 ./.venv/bin/python ML/baseline/benchmark_fractal0_entry_exit_grid.py \
  --threads 24 \
  --no-resume \
  --output-prefix ML/reports/fractal0_stop_grid_m5 \
  --execution-ohlc-path MT/MQL4/Files/XAUUSD_M5_OHLC.csv \
  --stop-grid-mode full \
  --exit-shortlist stop_grid \
  --skip-stress-spread \
  --permutation-repeats 200
```

- [ ] **Step 3: Monitor without reading large logs**

Use:

```bash
pgrep -af "benchmark_fractal0_entry_exit_grid.py"
du -h ML/reports/fractal0_stop_grid_m5*
./.venv/bin/python - <<'PY'
import json
from pathlib import Path
p = Path("ML/reports/fractal0_stop_grid_m5_progress.json")
if p.exists():
    d = json.load(p.open())
    print({"completed": len(d.get("completed", {})), "failed": len(d.get("failed", {}))})
PY
```

Expected final:

```text
completed = 576
failed = 0
```

`576` = `288 canonical configs x 2 roles (val_select/val_eval)`. If the runner reports a different expected total, stop and explain the accounting in the report.

### Task 6: Report, Docs, And Wiki

**Files:**
- Modify: `docs/ML/benchmark_fractal0_entry_exit_grid.py.md`
- Create: `docs/reports/2026-07-21-fractal0-stop-grid-m5.md`
- Modify: `CHANGELOG.md`
- Modify: `CONTEXT_HANDOFF.md`
- Modify: `wiki/research/fractal-stop-research.md`
- Modify: `wiki/index.md`
- Modify: `wiki/log.md`
- Modify: `wiki/REPO_integrity.md`

- [ ] **Step 1: Update runner docs**

Document new CLI:

```text
--stop-grid-mode full|current-only
--exit-shortlist full|stop_grid
--skip-stress-spread
```

Document that stop-grid reruns ML-exit per stop policy.

- [ ] **Step 2: Write stage report**

Report must include:

```text
winner by val_select
val_eval winner metrics
best result per stop_policy_id
SL-rate by stop_source
median_stop_distance_atr
mean/median r_value
risk_distance_atr
tp_distance_atr for fixed-R exits
comparison to M5 full rerun S0_current_0_5
stress_spread_status = deferred_shortlist_only
locked_test = not_opened
allowed_max_verdict = research_only
fixed-risk interpretation for pnl_r
```

- [ ] **Step 3: Run tests and wiki status**

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_entry_exit_grid.py -q
./.venv/bin/python wiki/wiki.py status
```

Expected:

```text
tests pass
Wiki is up to date. No gaps found.
```

If `wiki.py status` reports gaps, update wiki and run:

```bash
./.venv/bin/python wiki/wiki.py generate
```
