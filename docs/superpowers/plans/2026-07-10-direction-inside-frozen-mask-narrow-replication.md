# Direction Inside Frozen Mask Narrow Replication Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Проверить seed-stability слабого direction-effect внутри frozen movement-mask на заранее зафиксированной узкой матрице `nearest_k60 / extra_trees / entry_log_ratio` с главным горизонтом `H3` и дополнительными горизонтами `H6`, `H9`.

**Architecture:** План не открывает новый широкий поиск winner-а. Он переиспользует существующий runner `ML/baseline/benchmark_direction_inside_frozen_movement_regime_rich_features.py`, но добавляет отдельный seed-stability mode с новым output prefix, preflight для H9 labels, фиксированную матрицу, отчёт устойчивости seed/year/block и строгий verdict ниже trading candidate. `H3` остаётся primary horizon, `H6` и `H9` являются secondary robustness horizons и не могут заменить H3 задним числом.

**Tech Stack:** Python 3.10+, pandas, numpy, scikit-learn, pytest, существующий rich-features runner, `./.venv/bin/python`.

## Global Constraints

- Работать в текущей ветке; worktree запрещён.
- Использовать `./.venv/bin/python`.
- `locked_test` не открывать.
- `low_n_disclosure` / 2026 не использовать для выбора.
- Frozen movement-mask не менять: `simple_combined / extra_trees_small / H3 / top_fraction=0.05`, `seeds=[42,43,44]`, `rule_hash=56361f12104b55c4cac6bd04426349f71d8944c139563a8c9b68d3b25e97deaf`.
- Обучать direction-модель на полном `train`, а не на строках `frozen_selected=True`.
- Frozen-mask использовать только после fit для evaluation slices.
- Не использовать `score`, `selected`, `frozen_selected` как входные признаки.
- Не использовать top-level future target columns как входные признаки.
- Не тюнить по `val_eval`, `low_n_disclosure` или `locked_test`.
- Не расширять profile/model/target search space после просмотра результата.
- Не делать PnL/PF, BUY/SELL, spread, stop-loss, take-profit или trading claims.
- Максимальный положительный verdict этого этапа: `DIRECTION_REPLICATION_SUPPORTED_RESEARCH_ONLY`.
- Даже при PASS этап остаётся `RESEARCH_ONLY`, не `candidate`.
- После Python-изменений запускать `./.venv/bin/python -m pytest tests/ -q`.

---

## Research Protocol

**Уровень:** проверочный follow-up для гипотезы, порождённой прошлым exploratory full-grid. Это seed-stability check на тех же данных, той же mask и тех же validation-ролях. Это не независимая репликация, не независимое открытие и не торговый кандидат.

**Гипотеза:** direction-effect внутри frozen movement-mask у семьи `nearest_k60 / extra_trees / entry_log_ratio` не является одиночным шумовым попаданием H3, если он воспроизводится на нескольких training seeds и не разваливается на `val_eval_inside_mask`.

**Primary horizon:** `H3`.

**Secondary horizons:** `H6`, `H9`.

**Почему H6/H9 допустимы:** пользователь заранее запросил проверить соседние периоды до запуска репликации. Они раскрываются как robustness horizons, а не как новый выбор лучшего горизонта.

**Почему H9 требует отдельного preflight:** текущий runner разрешает `(3, 6, 12, 24)`, CLI ограничивает `--horizons` этим же списком, а `build_direction_targets()` отклоняет неизвестный горизонт. Готовые `entry_*_9` не подтверждены поиском по коду. Поэтому replication mode сначала выполняет target preflight, затем формирует executable horizons. H9 нельзя передавать в обычный `--horizons 9` до расширения допустимых горизонтов для replication mode и подтверждения `entry_log_ratio_9`, `entry_up_9`, `entry_dn_9`.

**Frozen replication matrix:**

```text
profiles        = [nearest_k60]
models          = [extra_trees]
target_families = [entry_log_ratio]
horizons        = [3, 6, 9]
training_seeds  = [41, 42, 43, 44, 45]
threads         = 24
parallel_workers = 1
```

**Search budget disclosure:**

```text
discovery_search_budget = 240
1 profile x 1 model x 1 target family x 3 horizons x 5 seeds = 15 planned runs
cumulative_search_budget_disclosed = 255
```

If H9 target columns are absent and no target-builder task is implemented, actual executed budget becomes:

```text
1 profile x 1 model x 1 target family x 2 horizons x 5 seeds = 10 executed runs
H9 = skipped by preflight, not failed model quality
cumulative_search_budget_disclosed = 250
```

## Verdict Rules

The report must compute all rules from saved JSON/CSV, not by reading terminal logs.

### PASS-like Research Verdict

Allowed only if all conditions hold:

- contract status is `PASS`;
- no failed model runs;
- `H3` has at least `3/5` seeds with `val_eval_inside_mask balanced_accuracy >= 0.52`;
- median `H3 val_eval_inside_mask balanced_accuracy >= 0.525`;
- `H3 val_select_inside_mask` and `H3 val_eval_inside_mask` have the same sign of improvement over 0.50 for at least `3/5` seeds;
- `H3` sample-size gate passes on `val_select_inside_mask` and `val_eval_inside_mask`;
- if `H6` is executed, it must not be contradictory:
  - median `H6 val_eval_inside_mask balanced_accuracy >= 0.505`;
  - at least `2/5` H6 seeds have `val_eval_inside_mask balanced_accuracy >= 0.50`;
- if `H9` is executed, it is treated by the same secondary rule as H6;
- if `H9` is skipped by preflight, it gives no positive evidence and cannot cover an H6 failure.

Verdict:

```text
DIRECTION_REPLICATION_SUPPORTED_RESEARCH_ONLY
```

### Weak / Inconclusive Verdict

If H3 is above chance but misses one PASS-like criterion:

```text
DIRECTION_REPLICATION_INCONCLUSIVE
```

### Reject Verdict

If H3 median `val_eval_inside_mask balanced_accuracy < 0.515` or fewer than `2/5` seeds are above `0.52`:

```text
REJECT_DIRECTION_REPLICATION
```

### H9 Handling

- If H9 labels exist and pass preflight, H9 is executed.
- If H9 labels are absent, H9 is recorded as `SKIPPED_MISSING_TARGET_COLUMNS`.
- H9 skip cannot improve verdict.
- If H9 labels exist but target construction fails, status is `TARGET_CONTRACT_FAIL` and the stage contract is not `PASS`.
- If model fitting/evaluation fails after target construction, status is `MODEL_RUN_FAIL`.
- H9 failure can only downgrade interpretation; it must not be used to tune a new target.

---

## Files

**Modify**

- `ML/baseline/benchmark_direction_inside_frozen_movement_regime_rich_features.py` — add replication config helpers, optional H9 support/preflight, replication verdict summary.
- `tests/test_direction_inside_frozen_movement_regime_rich_features.py` — add tests for replication matrix, H9 preflight, seed aggregation, verdict rules.
- `docs/ML/benchmark_direction_inside_frozen_movement_regime_rich_features.py.md` — document replication mode and commands.
- `docs/superpowers/roadmap.md` — after completion, replace this roadmap item with the result and next branch.
- `CHANGELOG.md`, `CONTEXT_HANDOFF.md`, `wiki/*` — update only when the stage is closed by stage-reporting.

**Create**

- `docs/reports/2026-07-10-direction-inside-frozen-mask-narrow-replication.md` — final report after run.

**Generated**

- `ML/reports/direction_inside_frozen_movement_regime_narrow_replication.json`
- `ML/reports/direction_inside_frozen_movement_regime_narrow_replication_metrics.csv`
- `ML/reports/direction_inside_frozen_movement_regime_narrow_replication_rows.csv`

---

### Task 1: Replication Config And Output Prefix

**Files:**
- Modify: `ML/baseline/benchmark_direction_inside_frozen_movement_regime_rich_features.py`
- Modify: `tests/test_direction_inside_frozen_movement_regime_rich_features.py`

**Interfaces:**
- Produces `NARROW_REPLICATION_OUTPUT_PREFIX = "direction_inside_frozen_movement_regime_narrow_replication"`.
- Produces `NARROW_REPLICATION_HORIZONS = (3, 6, 9)`.
- Produces `NARROW_REPLICATION_SEEDS = (41, 42, 43, 44, 45)`.
- Produces `narrow_replication_config() -> dict[str, object]`.

- [ ] **Step 1: Write failing tests**

Add these tests:

```python
def test_narrow_replication_config_freezes_search_space():
    config = runner.narrow_replication_config()

    assert config["stage_name"] == "direction_inside_frozen_mask_narrow_replication"
    assert config["output_prefix_name"] == "direction_inside_frozen_movement_regime_narrow_replication"
    assert config["feature_profiles"] == ["nearest_k60"]
    assert config["model_keys"] == ["extra_trees"]
    assert config["target_families"] == ["entry_log_ratio"]
    assert config["target_horizons"] == [3, 6, 9]
    assert config["replication_seeds"] == [41, 42, 43, 44, 45]
    assert config["primary_horizon"] == 3
    assert config["secondary_horizons"] == [6, 9]
    assert config["selection_policy"] == "pre_registered_no_new_winner_search"
    assert config["max_positive_verdict"] == "DIRECTION_REPLICATION_SUPPORTED_RESEARCH_ONLY"
    assert config["locked_test"] == "not_opened"
```

Run:

```bash
./.venv/bin/python -m pytest tests/test_direction_inside_frozen_movement_regime_rich_features.py::test_narrow_replication_config_freezes_search_space -q
```

Expected: fail because `narrow_replication_config()` does not exist.

- [ ] **Step 2: Implement minimal config**

Add constants and function:

```python
NARROW_REPLICATION_OUTPUT_PREFIX = "direction_inside_frozen_movement_regime_narrow_replication"
NARROW_REPLICATION_HORIZONS = (3, 6, 9)
NARROW_REPLICATION_SEEDS = (41, 42, 43, 44, 45)


def narrow_replication_config() -> dict[str, object]:
    config = rich_direction_config()
    config.update(
        {
            "stage_name": "direction_inside_frozen_mask_narrow_replication",
            "output_prefix_name": NARROW_REPLICATION_OUTPUT_PREFIX,
            "feature_profiles": ["nearest_k60"],
            "model_keys": ["extra_trees"],
            "target_families": ["entry_log_ratio"],
            "target_horizons": list(NARROW_REPLICATION_HORIZONS),
            "replication_seeds": list(NARROW_REPLICATION_SEEDS),
            "primary_horizon": 3,
            "secondary_horizons": [6, 9],
            "selection_policy": "pre_registered_no_new_winner_search",
            "max_positive_verdict": "DIRECTION_REPLICATION_SUPPORTED_RESEARCH_ONLY",
            "locked_test": "not_opened",
            "threads": DEFAULT_THREADS,
            "parallel_workers": 1,
        }
    )
    return config
```

- [ ] **Step 3: Verify**

Run:

```bash
./.venv/bin/python -m pytest tests/test_direction_inside_frozen_movement_regime_rich_features.py::test_narrow_replication_config_freezes_search_space -q
```

Expected: pass.

---

### Task 2: H9 Target Preflight

**Files:**
- Modify: `ML/baseline/benchmark_direction_inside_frozen_movement_regime_rich_features.py`
- Modify: `tests/test_direction_inside_frozen_movement_regime_rich_features.py`

**Interfaces:**
- Produces `preflight_target_horizons(splits: dict[str, pd.DataFrame], horizons: Sequence[int]) -> dict[str, object]`.
- Produces per-horizon status: `PASS`, `SKIPPED_MISSING_TARGET_COLUMNS`, or `TARGET_CONTRACT_FAIL`.
- Produces `executable_horizons`; later tasks must build jobs only from this list.

- [ ] **Step 1: Write failing tests**

Add:

```python
def test_preflight_target_horizons_marks_h9_missing_without_crash():
    splits = {
        "train": pd.DataFrame(
            {
                "entry_log_ratio_3": [0.1],
                "entry_up_3": [2.0],
                "entry_dn_3": [1.0],
                "entry_log_ratio_6": [0.2],
                "entry_up_6": [3.0],
                "entry_dn_6": [1.0],
            }
        ),
        "val_select": pd.DataFrame(
            {
                "entry_log_ratio_3": [0.1],
                "entry_up_3": [2.0],
                "entry_dn_3": [1.0],
                "entry_log_ratio_6": [0.2],
                "entry_up_6": [3.0],
                "entry_dn_6": [1.0],
            }
        ),
    }

    preflight = runner.preflight_target_horizons(splits, horizons=[3, 6, 9])

    assert preflight["status"] == "WARNING"
    assert preflight["horizons"]["3"]["status"] == "PASS"
    assert preflight["horizons"]["6"]["status"] == "PASS"
    assert preflight["horizons"]["9"]["status"] == "SKIPPED_MISSING_TARGET_COLUMNS"
    assert preflight["executable_horizons"] == [3, 6]
    assert preflight["skipped_horizons"] == [9]


def test_preflight_target_horizons_allows_h9_when_columns_exist():
    splits = {
        "train": pd.DataFrame(
            {
                "entry_log_ratio_9": [0.1],
                "entry_up_9": [2.0],
                "entry_dn_9": [1.0],
            }
        )
    }

    preflight = runner.preflight_target_horizons(splits, horizons=[9])

    assert preflight["status"] == "PASS"
    assert preflight["horizons"]["9"]["status"] == "PASS"
    assert preflight["executable_horizons"] == [9]


def test_preflight_target_horizons_on_real_splits_reports_available_columns():
    splits = runner.amplitude.load_entry_based_splits()

    preflight = runner.preflight_target_horizons(splits, horizons=[3, 6, 9])

    assert preflight["horizons"]["3"]["status"] == "PASS"
    assert preflight["horizons"]["6"]["status"] == "PASS"
    assert preflight["status"] in {"PASS", "WARNING"}
    assert set(preflight["executable_horizons"]).issubset({3, 6, 9})
```

Run both tests and confirm failure.

- [ ] **Step 2: Implement preflight**

Implement:

```python
def preflight_target_horizons(
    splits: dict[str, pd.DataFrame],
    horizons: Sequence[int],
) -> dict[str, object]:
    horizon_results: dict[str, dict[str, object]] = {}
    executable: list[int] = []
    skipped: list[int] = []
    for horizon in horizons:
        required = list(_required_target_columns(int(horizon)))
        missing_by_split = {
            split_name: [column for column in required if column not in frame.columns]
            for split_name, frame in splits.items()
        }
        missing_by_split = {key: value for key, value in missing_by_split.items() if value}
        if missing_by_split:
            skipped.append(int(horizon))
            horizon_results[str(horizon)] = {
                "status": "SKIPPED_MISSING_TARGET_COLUMNS",
                "required_columns": required,
                "missing_by_split": missing_by_split,
            }
        else:
            executable.append(int(horizon))
            horizon_results[str(horizon)] = {
                "status": "PASS",
                "required_columns": required,
                "missing_by_split": {},
            }

    return {
        "status": "PASS" if not skipped else "WARNING",
        "horizons": horizon_results,
        "executable_horizons": executable,
        "skipped_horizons": skipped,
    }
```

- [ ] **Step 3: Verify**

Run:

```bash
./.venv/bin/python -m pytest tests/test_direction_inside_frozen_movement_regime_rich_features.py::test_preflight_target_horizons_marks_h9_missing_without_crash tests/test_direction_inside_frozen_movement_regime_rich_features.py::test_preflight_target_horizons_allows_h9_when_columns_exist -q
```

Expected: pass.

---

### Task 3: Run Multiple Seeds Without Expanding Search Space

**Files:**
- Modify: `ML/baseline/benchmark_direction_inside_frozen_movement_regime_rich_features.py`
- Modify: `tests/test_direction_inside_frozen_movement_regime_rich_features.py`

**Interfaces:**
- Modify `run_rich_direction_experiment(...)` to accept `replication_seeds`.
- Resume key already includes `seed`, so no new key format is needed.
- Summary must include `replication_mode`, `planned_search_budget`, `executed_search_budget`, `target_preflight`.

- [ ] **Step 1: Write failing test**

Add:

```python
def test_replication_jobs_use_all_pre_registered_seeds(monkeypatch):
    config = runner.narrow_replication_config()
    config.update(
        {
            "target_horizons": [3, 6],
            "replication_seeds": [41, 42],
        }
    )

    jobs = runner.build_rich_direction_jobs(config)

    assert [job["seed"] for job in jobs] == [41, 41, 42, 42]
    assert [job["horizon"] for job in jobs] == [3, 6, 3, 6]
    assert {job["profile"] for job in jobs} == {"nearest_k60"}
    assert {job["model_key"] for job in jobs} == {"extra_trees"}
    assert {job["target_family"] for job in jobs} == {"entry_log_ratio"}


def test_replication_jobs_use_only_executable_horizons_after_h9_preflight():
    config = runner.narrow_replication_config()
    config.update(
        {
            "target_horizons": [3, 6, 9],
            "executable_horizons": [3, 6],
            "replication_seeds": [41],
        }
    )

    jobs = runner.build_rich_direction_jobs(config)

    assert [job["horizon"] for job in jobs] == [3, 6]
```

Run the test and confirm failure because `build_rich_direction_jobs()` does not exist.

- [ ] **Step 2: Extract job builder**

Add:

```python
def build_rich_direction_jobs(config: dict[str, object]) -> list[dict[str, object]]:
    profiles = tuple(config.get("feature_profiles", RICH_FEATURE_PROFILES))
    horizons = tuple(
        int(value)
        for value in config.get("executable_horizons", config.get("target_horizons", RICH_TARGET_HORIZONS))
    )
    target_families = tuple(config.get("target_families", RICH_TARGET_FAMILIES))
    model_keys = tuple(config.get("model_keys", RICH_MODEL_KEYS))
    seeds = tuple(int(value) for value in config.get("replication_seeds", [config.get("seed", DEFAULT_SEED)]))
    return [
        {
            "profile": str(profile),
            "horizon": int(horizon),
            "target_family": str(target_family),
            "model_key": str(model_key),
            "seed": int(seed),
        }
        for seed in seeds
        for profile in profiles
        for horizon in horizons
        for target_family in target_families
        for model_key in model_keys
    ]
```

Then replace inline job creation inside `run_rich_direction_experiment()` with `build_rich_direction_jobs(config)`.
Before building jobs in replication mode:

- call `preflight_target_horizons(masked_splits, config["target_horizons"])`;
- store it as `summary["target_preflight"]`;
- set `config["executable_horizons"] = preflight["executable_horizons"]`;
- set `planned_search_budget` from original horizons;
- set `executed_search_budget` from executable horizons;
- set `discovery_search_budget = 240`;
- set `cumulative_search_budget_disclosed = discovery_search_budget + executed_search_budget`;
- ensure `progress.total_runs == executed_search_budget`.

- [ ] **Step 3: Verify focused tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_direction_inside_frozen_movement_regime_rich_features.py::test_replication_jobs_use_all_pre_registered_seeds tests/test_direction_inside_frozen_movement_regime_rich_features.py::test_resume_key_and_completed_run_skip_policy -q
```

Expected: pass.

---

### Task 4: Replication Summary And Verdict

**Files:**
- Modify: `ML/baseline/benchmark_direction_inside_frozen_movement_regime_rich_features.py`
- Modify: `tests/test_direction_inside_frozen_movement_regime_rich_features.py`

**Interfaces:**
- Produces `aggregate_narrow_replication(metrics: pd.DataFrame, summary: dict[str, object]) -> dict[str, object]`.
- Produces `narrow_replication_verdict(replication: dict[str, object]) -> str`.

- [ ] **Step 1: Write failing aggregation tests**

Add:

```python
def _replication_metric(run_id, seed, horizon, split, bal_acc, gate="PASS"):
    return {
        "run_id": run_id,
        "resume_key": f"nearest_k60/{seed}/extra_trees/H{horizon}/entry_log_ratio",
        "profile": "nearest_k60",
        "seed": seed,
        "model_key": "extra_trees",
        "horizon": horizon,
        "target_family": "entry_log_ratio",
        "split": split,
        "slice": "frozen_selected",
        "balanced_accuracy": bal_acc,
        "sample_size_gate": gate,
        "gate_reasons": "",
    }


def test_narrow_replication_verdict_supported_when_h3_repeats():
    rows = []
    for seed, score in zip([41, 42, 43, 44, 45], [0.526, 0.531, 0.529, 0.521, 0.533]):
        rows.append(_replication_metric(f"h3-{seed}", seed, 3, "val_select", score + 0.02))
        rows.append(_replication_metric(f"h3-{seed}", seed, 3, "val_eval", score))
    for seed, score in zip([41, 42, 43, 44, 45], [0.507, 0.509, 0.501, 0.506, 0.508]):
        rows.append(_replication_metric(f"h6-{seed}", seed, 6, "val_select", score + 0.01))
        rows.append(_replication_metric(f"h6-{seed}", seed, 6, "val_eval", score))

    replication = runner.aggregate_narrow_replication(pd.DataFrame(rows), {"target_preflight": {"skipped_horizons": [9]}})

    assert replication["primary_horizon"] == 3
    assert replication["horizons"]["3"]["val_eval_median_balanced_accuracy"] == pytest.approx(0.529)
    assert replication["horizons"]["3"]["val_eval_seeds_ge_0_52"] == 5
    assert runner.narrow_replication_verdict(replication) == "DIRECTION_REPLICATION_SUPPORTED_RESEARCH_ONLY"


def test_narrow_replication_verdict_rejects_weak_h3():
    rows = []
    for seed, score in zip([41, 42, 43, 44, 45], [0.501, 0.511, 0.514, 0.509, 0.506]):
        rows.append(_replication_metric(f"h3-{seed}", seed, 3, "val_select", score + 0.02))
        rows.append(_replication_metric(f"h3-{seed}", seed, 3, "val_eval", score))

    replication = runner.aggregate_narrow_replication(pd.DataFrame(rows), {"target_preflight": {"skipped_horizons": [9]}})

    assert runner.narrow_replication_verdict(replication) == "REJECT_DIRECTION_REPLICATION"


def test_narrow_replication_verdict_inconclusive_when_val_select_eval_sign_disagree():
    rows = []
    for seed, eval_score in zip([41, 42, 43, 44, 45], [0.526, 0.531, 0.529, 0.521, 0.533]):
        select_score = 0.499 if seed in {41, 42, 43} else 0.551
        rows.append(_replication_metric(f"h3-{seed}", seed, 3, "val_select", select_score))
        rows.append(_replication_metric(f"h3-{seed}", seed, 3, "val_eval", eval_score))
    for seed, score in zip([41, 42, 43, 44, 45], [0.507, 0.509, 0.501, 0.506, 0.508]):
        rows.append(_replication_metric(f"h6-{seed}", seed, 6, "val_select", score + 0.01))
        rows.append(_replication_metric(f"h6-{seed}", seed, 6, "val_eval", score))

    replication = runner.aggregate_narrow_replication(pd.DataFrame(rows), {"target_preflight": {"skipped_horizons": [9]}})

    assert replication["horizons"]["3"]["same_positive_sign_seed_count"] == 2
    assert runner.narrow_replication_verdict(replication) == "DIRECTION_REPLICATION_INCONCLUSIVE"


def test_narrow_replication_verdict_inconclusive_when_h6_contradicts_and_h9_skipped():
    rows = []
    for seed, score in zip([41, 42, 43, 44, 45], [0.526, 0.531, 0.529, 0.521, 0.533]):
        rows.append(_replication_metric(f"h3-{seed}", seed, 3, "val_select", score + 0.02))
        rows.append(_replication_metric(f"h3-{seed}", seed, 3, "val_eval", score))
    for seed, score in zip([41, 42, 43, 44, 45], [0.491, 0.498, 0.501, 0.494, 0.499]):
        rows.append(_replication_metric(f"h6-{seed}", seed, 6, "val_select", score + 0.01))
        rows.append(_replication_metric(f"h6-{seed}", seed, 6, "val_eval", score))

    replication = runner.aggregate_narrow_replication(pd.DataFrame(rows), {"target_preflight": {"skipped_horizons": [9]}})

    assert runner.narrow_replication_verdict(replication) == "DIRECTION_REPLICATION_INCONCLUSIVE"
```

Run and confirm failure.

- [ ] **Step 2: Implement aggregation**

Implementation rules:

- filter only `slice == "frozen_selected"`;
- aggregate by horizon and split;
- compute median, mean, min, max balanced accuracy;
- count seeds with `val_eval >= 0.52`;
- count seeds where both `val_select` and `val_eval` are above `0.50`;
- carry sample-size gate failures;
- preserve skipped horizon information from target preflight.

- [ ] **Step 3: Implement verdict**

Use exact thresholds from `Verdict Rules`:

```text
H3 median val_eval >= 0.525
H3 seeds_ge_0_52 >= 3
H3 same_positive_sign_seed_count >= 3
H3 gate failures == 0
H6 median val_eval >= 0.505 if H6 executed
H6 seeds_ge_0_50 >= 2 if H6 executed
H9 skip gives no positive evidence
```

Return one of:

```text
DIRECTION_REPLICATION_SUPPORTED_RESEARCH_ONLY
DIRECTION_REPLICATION_INCONCLUSIVE
REJECT_DIRECTION_REPLICATION
```

- [ ] **Step 4: Verify**

Run:

```bash
./.venv/bin/python -m pytest tests/test_direction_inside_frozen_movement_regime_rich_features.py::test_narrow_replication_verdict_supported_when_h3_repeats tests/test_direction_inside_frozen_movement_regime_rich_features.py::test_narrow_replication_verdict_rejects_weak_h3 -q
```

Expected: pass.

---

### Task 5: Year And Block Diagnostics

**Files:**
- Modify: `ML/baseline/benchmark_direction_inside_frozen_movement_regime_rich_features.py`
- Modify: `tests/test_direction_inside_frozen_movement_regime_rich_features.py`

**Interfaces:**
- Produces `compute_narrow_time_diagnostics(rows: pd.DataFrame, block_count: int = 4) -> dict[str, object]`.
- Diagnostics are report-only and do not choose winner.

- [ ] **Step 1: Write failing test for year/block diagnostics**

Add:

```python
def test_compute_narrow_time_diagnostics_reports_year_and_blocks():
    rows = pd.DataFrame(
        {
            "resume_key": ["nearest_k60/41/extra_trees/H3/entry_log_ratio"] * 8,
            "split": ["val_eval"] * 8,
            "row_id": list(range(8)),
            "time": [
                "2021-01-01", "2021-02-01", "2021-03-01", "2021-04-01",
                "2022-01-01", "2022-02-01", "2022-03-01", "2022-04-01",
            ],
            "prediction": [1, 1, -1, -1, 1, -1, 1, -1],
            "target_direction": [1, -1, -1, -1, 1, -1, -1, -1],
            "frozen_selected": [True] * 8,
        }
    )

    diagnostics = runner.compute_narrow_time_diagnostics(rows, block_count=4)

    assert diagnostics["status"] == "PASS"
    assert diagnostics["scope"] == "diagnostic_only_not_verdict_gate"
    assert set(diagnostics["by_year"].keys()) == {"2021", "2022"}
    assert len(diagnostics["by_block"]) == 4
    assert diagnostics["by_year"]["2021"]["n"] == 4
```

Run and confirm failure.

- [ ] **Step 2: Implement diagnostics**

Rules:

- use only `frozen_selected=True` rows;
- use only `val_select` and `val_eval`;
- parse `time` if present;
- if `time` is missing, return `status="WARNING"` and still compute ordered row blocks;
- year diagnostics: n, accuracy, balanced_accuracy when both signs exist;
- block diagnostics: split each `(resume_key, split)` ordered row sequence into `block_count` contiguous blocks;
- mark any year/block with `n < 30` as `LOW_N_DIAGNOSTIC_ONLY`.

- [ ] **Step 3: Attach diagnostics to summary**

Add to JSON summary:

```text
time_diagnostics.by_year
time_diagnostics.by_block
time_diagnostics.scope = diagnostic_only_not_verdict_gate
```

The final report must include these tables even if they are noisy.

- [ ] **Step 4: Verify**

Run:

```bash
./.venv/bin/python -m pytest tests/test_direction_inside_frozen_movement_regime_rich_features.py::test_compute_narrow_time_diagnostics_reports_year_and_blocks -q
```

Expected: pass.

---

### Task 6: CLI Replication Mode

**Files:**
- Modify: `ML/baseline/benchmark_direction_inside_frozen_movement_regime_rich_features.py`
- Modify: `tests/test_direction_inside_frozen_movement_regime_rich_features.py`
- Modify: `docs/ML/benchmark_direction_inside_frozen_movement_regime_rich_features.py.md`

**Interfaces:**
- Add CLI flag `--replication-mode narrow`.
- Add CLI flag `--replication-seeds`.
- In narrow mode, allow H9 only through replication preflight/executable horizons; ordinary non-replication `--horizons 9` remains invalid unless general target support is added.
- Keep default behavior unchanged when `--replication-mode` is absent.

- [ ] **Step 1: Write failing parser test**

Add:

```python
def test_arg_parser_accepts_narrow_replication_mode_and_seeds():
    parser = runner.build_arg_parser()
    args = parser.parse_args(["--replication-mode", "narrow", "--replication-seeds", "41", "42", "43"])

    assert args.replication_mode == "narrow"
    assert args.replication_seeds == [41, 42, 43]


def test_narrow_smoke_horizons_override_limits_to_one_horizon():
    parser = runner.build_arg_parser()
    args = parser.parse_args(["--replication-mode", "narrow", "--horizons", "3", "--replication-seeds", "41"])
    config = runner.config_from_args(args)

    assert config["target_horizons"] == [3]
    assert config["replication_seeds"] == [41]
```

Run and confirm failure.

- [ ] **Step 2: Add parser flags**

Add:

```python
parser.add_argument("--replication-mode", choices=["none", "narrow"], default="none")
parser.add_argument("--replication-seeds", nargs="+", type=int, default=None)
```

Change `--horizons` parsing so argparse accepts integers without `choices`.
Then validate manually:

```python
def validate_horizon_args(replication_mode: str, horizons: Sequence[int]) -> None:
    allowed = set(RICH_TARGET_HORIZONS)
    if replication_mode == "narrow":
        allowed = allowed.union(NARROW_REPLICATION_HORIZONS)
    invalid = sorted(set(int(value) for value in horizons).difference(allowed))
    if invalid:
        raise ValueError(f"unsupported horizons for {replication_mode}: {invalid}")
```

This is required because `--replication-mode narrow --horizons 9` must reach
target preflight, while ordinary mode must not silently accept unsupported
horizons.

- [ ] **Step 3: Wire config with a helper**

Add:

```python
def config_from_args(args: argparse.Namespace) -> dict[str, object]:
    if args.replication_mode == "narrow":
        config = narrow_replication_config()
        config["target_horizons"] = list(args.horizons)
        config["threads"] = args.threads
        config["parallel_workers"] = args.parallel_workers
        config["min_masked_rows"] = args.min_masked_rows
        config["min_active_sign_rows"] = args.min_active_sign_rows
        if args.replication_seeds is not None:
            config["replication_seeds"] = args.replication_seeds
        return config

    return {
        "feature_profiles": args.profiles,
        "target_horizons": args.horizons,
        "target_families": args.target_families,
        "model_keys": args.model_keys,
        "min_masked_rows": args.min_masked_rows,
        "min_active_sign_rows": args.min_active_sign_rows,
        "threads": args.threads,
        "parallel_workers": args.parallel_workers,
    }
```

In `main()`:

```python
if args.replication_mode == "narrow":
    config = config_from_args(args)
    output_prefix = Path(args.output_prefix)
    if str(output_prefix) == str(DEFAULT_OUTPUT_PREFIX):
        output_prefix = Path(f"ML/reports/{NARROW_REPLICATION_OUTPUT_PREFIX}")
else:
    config = config_from_args(args)
    output_prefix = Path(args.output_prefix)
```

Then pass `output_prefix` and `config` to `run_rich_direction_cli()`.

- [ ] **Step 4: Update module docs**

Add a section:

```markdown
## Narrow Replication Mode

Run:

```bash
MPLCONFIGDIR=/tmp/matplotlib \
./.venv/bin/python ML/baseline/benchmark_direction_inside_frozen_movement_regime_rich_features.py \
  --replication-mode narrow \
  --threads 24 \
  --no-resume
```

This mode fixes `nearest_k60 / extra_trees / entry_log_ratio`, runs seeds
`41..45`, checks horizons `H3/H6/H9`, and writes
`ML/reports/direction_inside_frozen_movement_regime_narrow_replication.*`.
```

- [ ] **Step 5: Verify**

Run:

```bash
./.venv/bin/python -m pytest tests/test_direction_inside_frozen_movement_regime_rich_features.py::test_arg_parser_accepts_narrow_replication_mode_and_seeds -q
```

Expected: pass.

---

### Task 7: Smoke Run And Full Verification

**Files:**
- Generated artifacts under `ML/reports/`
- No source edits unless smoke exposes a bug.

**Interfaces:**
- Produces valid JSON with `replication_mode`, `target_preflight`, `replication_summary`, `replication_verdict`, `time_diagnostics`.

- [ ] **Step 1: Run focused tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_direction_inside_frozen_movement_regime_rich_features.py -q
```

Expected: all tests pass.

- [ ] **Step 2: Run full tests after Python changes**

Run:

```bash
./.venv/bin/python -m pytest tests/ -q
```

Expected: full suite passes.

- [ ] **Step 3: Run one-run smoke without overwriting full-grid artifacts**

Run:

```bash
MPLCONFIGDIR=/tmp/matplotlib \
./.venv/bin/python ML/baseline/benchmark_direction_inside_frozen_movement_regime_rich_features.py \
  --replication-mode narrow \
  --replication-seeds 41 \
  --horizons 3 \
  --threads 24 \
  --output-prefix ML/reports/direction_inside_frozen_movement_regime_narrow_replication_smoke \
  --no-resume
```

Expected:

- output prefix is `*_smoke`, not the canonical full replication prefix;
- `done_runs=1/1`;
- JSON includes `target_preflight`;
- `progress.total_runs == 1`;
- `executed_search_budget == 1`;
- no writes to `direction_inside_frozen_movement_regime_rich_features.*`.

- [ ] **Step 4: Inspect smoke JSON**

Run:

```bash
./.venv/bin/python - <<'PY'
import json
from pathlib import Path

path = Path("ML/reports/direction_inside_frozen_movement_regime_narrow_replication_smoke.json")
data = json.loads(path.read_text())
print(data["contract_status"])
print(data["progress"]["done_runs"], data["progress"]["total_runs"])
print(data.get("target_preflight", {}).get("status"))
print(data.get("executed_search_budget"))
print(data.get("replication_summary", {}).get("primary_horizon"))
PY
```

Expected:

```text
PASS
1 1
PASS
1
3
```

If H9 is not part of this smoke, no H9 conclusion is made.

---

### Task 8: Full Narrow Replication Run

**Files:**
- Generated:
  - `ML/reports/direction_inside_frozen_movement_regime_narrow_replication.json`
  - `ML/reports/direction_inside_frozen_movement_regime_narrow_replication_metrics.csv`
  - `ML/reports/direction_inside_frozen_movement_regime_narrow_replication_rows.csv`

**Interfaces:**
- Full run must not overwrite `direction_inside_frozen_movement_regime_rich_features.*`.

- [ ] **Step 1: Start full run**

Run:

```bash
MPLCONFIGDIR=/tmp/matplotlib \
./.venv/bin/python ML/baseline/benchmark_direction_inside_frozen_movement_regime_rich_features.py \
  --replication-mode narrow \
  --threads 24 \
  --no-resume
```

Expected:

- heartbeat prints start/preflight/run progress;
- planned total is `15` if H9 labels exist;
- planned total is `10` if H9 labels are skipped by preflight;
- `progress.total_runs == executed_search_budget`;
- output prefix is `ML/reports/direction_inside_frozen_movement_regime_narrow_replication`.

- [ ] **Step 2: If interrupted, resume safely**

Run:

```bash
MPLCONFIGDIR=/tmp/matplotlib \
./.venv/bin/python ML/baseline/benchmark_direction_inside_frozen_movement_regime_rich_features.py \
  --replication-mode narrow \
  --threads 24 \
  --resume
```

Expected: completed `resume_key` values are skipped.

- [ ] **Step 3: Audit generated artifacts**

Run:

```bash
./.venv/bin/python - <<'PY'
import json
import pandas as pd
from pathlib import Path

prefix = Path("ML/reports/direction_inside_frozen_movement_regime_narrow_replication")
data = json.loads(prefix.with_suffix(".json").read_text())
metrics = pd.read_csv(f"{prefix}_metrics.csv")
rows = pd.read_csv(f"{prefix}_rows.csv")

print("contract", data["contract_status"])
print("progress", data["progress"]["done_runs"], data["progress"]["total_runs"])
print("budget", data["discovery_search_budget"], data["replication_search_budget_planned"], data["replication_search_budget_executed"], data["cumulative_search_budget_disclosed"])
print("failed", len(data.get("failed_runs", [])))
print("verdict", data.get("replication_verdict") or data.get("verdict"))
print("preflight", data.get("target_preflight", {}).get("status"))
print("skipped", data.get("target_preflight", {}).get("skipped_horizons"))
print("metrics_rows", len(metrics))
print("row_resume_keys", rows["resume_key"].nunique() if "resume_key" in rows else "missing")
print("metric_resume_keys", metrics["resume_key"].nunique() if "resume_key" in metrics else "missing")
print("time_diag", data.get("time_diagnostics", {}).get("status"))
PY
```

Expected:

- `contract PASS`;
- `failed 0`;
- `progress done == total`;
- `progress total == replication_search_budget_executed`;
- `cumulative_search_budget_disclosed` is `250` if H9 skipped, `255` if H9 executed;
- `metric_resume_keys == total`;
- rows have no empty `resume_key`.

---

### Task 9: Stage Report And Documentation Closeout

**Files:**
- Create: `docs/reports/2026-07-10-direction-inside-frozen-mask-narrow-replication.md`
- Modify: `docs/ML/benchmark_direction_inside_frozen_movement_regime_rich_features.py.md`
- Modify: `docs/tests/tests.md`
- Modify: `docs/superpowers/roadmap.md`
- Modify: `CHANGELOG.md`
- Modify: `CONTEXT_HANDOFF.md`
- Modify: `wiki/research/fractal-stop-research.md`, `wiki/index.md`, `wiki/log.md`, `wiki/REPO_integrity.md`

**Interfaces:**
- Use `stage-reporting` and `wiki` skills for closeout.

- [ ] **Step 1: Write report**

The report must include:

- context from `2026-07-09` full-grid result;
- exact replication matrix;
- discovery budget `240`;
- whether H9 was executed or skipped by preflight;
- `replication_search_budget_planned`, `replication_search_budget_executed`, `cumulative_search_budget_disclosed`;
- `H3` seed table;
- `H6` seed table;
- `H9` seed table or skip reason;
- year/block diagnostic tables;
- verdict from pre-registered rules;
- forbidden interpretations;
- next step.

- [ ] **Step 2: Update docs**

Update module docs with:

- replication CLI;
- output files;
- H9 preflight rule;
- verdict thresholds.

- [ ] **Step 3: Update roadmap**

If verdict is `DIRECTION_REPLICATION_SUPPORTED_RESEARCH_ONLY`:

- roadmap next direction becomes either:
  - independent clean replication on a new period/instrument; or
  - design of execution-aware `fractal0_price` entry mechanics.

If verdict is `DIRECTION_REPLICATION_INCONCLUSIVE`:

- roadmap should say no wider direction search yet;
- recommend `fractal0_price` mechanics unless there is a concrete bug or data gap.

If verdict is `REJECT_DIRECTION_REPLICATION`:

- remove direction-inside-mask as a near-term branch;
- move `fractal0_price` mechanics to top.

- [ ] **Step 4: Run wiki tooling**

Run:

```bash
./.venv/bin/python wiki/wiki.py generate
./.venv/bin/python wiki/wiki.py status
```

Expected: wiki status reports no gaps.

- [ ] **Step 5: Final verification**

Run:

```bash
git diff --check
./.venv/bin/python -m pytest tests/test_direction_inside_frozen_movement_regime_rich_features.py -q
```

Expected:

- `git diff --check` has no output;
- focused tests pass.

- [ ] **Step 6: Commit**

Run:

```bash
git status --short
git add ML/baseline/benchmark_direction_inside_frozen_movement_regime_rich_features.py \
  tests/test_direction_inside_frozen_movement_regime_rich_features.py \
  docs/ML/benchmark_direction_inside_frozen_movement_regime_rich_features.py.md \
  docs/tests/tests.md \
  docs/superpowers/roadmap.md \
  docs/reports/2026-07-10-direction-inside-frozen-mask-narrow-replication.md \
  CHANGELOG.md CONTEXT_HANDOFF.md \
  wiki/research/fractal-stop-research.md wiki/index.md wiki/log.md wiki/REPO_integrity.md
git commit -m "Add narrow direction replication inside frozen mask"
```

Do not commit large generated rows CSV unless the project owner explicitly asks for generated experiment artifacts in git.

---

## Execution Command Summary

Focused development tests:

```bash
./.venv/bin/python -m pytest tests/test_direction_inside_frozen_movement_regime_rich_features.py -q
```

Full test suite after Python changes:

```bash
./.venv/bin/python -m pytest tests/ -q
```

Smoke:

```bash
MPLCONFIGDIR=/tmp/matplotlib \
./.venv/bin/python ML/baseline/benchmark_direction_inside_frozen_movement_regime_rich_features.py \
  --replication-mode narrow \
  --replication-seeds 41 \
  --horizons 3 \
  --threads 24 \
  --output-prefix ML/reports/direction_inside_frozen_movement_regime_narrow_replication_smoke \
  --no-resume
```

Full narrow replication:

```bash
MPLCONFIGDIR=/tmp/matplotlib \
./.venv/bin/python ML/baseline/benchmark_direction_inside_frozen_movement_regime_rich_features.py \
  --replication-mode narrow \
  --threads 24 \
  --no-resume
```

Resume:

```bash
MPLCONFIGDIR=/tmp/matplotlib \
./.venv/bin/python ML/baseline/benchmark_direction_inside_frozen_movement_regime_rich_features.py \
  --replication-mode narrow \
  --threads 24 \
  --resume
```

---

## Self-Review

- Spec coverage: план фиксирует гипотезу, горизонты H3/H6/H9, H9 preflight, seed robustness, sample-size gates, forbidden interpretations, output prefix and closeout docs.
- Placeholder scan: нет незаполненных мест, отложенной реализации или fuzzy "add tests" без конкретных тестов.
- Type consistency: новые функции названы одинаково в задачах и тестах: `narrow_replication_config`, `preflight_target_horizons`, `build_rich_direction_jobs`, `aggregate_narrow_replication`, `narrow_replication_verdict`.
- Methodology status before execution: `DIAGNOSTIC_ONLY / RESEARCH_ONLY` until the full narrow replication run is complete and reported.
