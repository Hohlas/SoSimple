# Direction Inside Frozen Mask Rich Features Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Проверить направление внутри frozen movement-mask заново: учить модель на полном честном `train`, использовать богатые признаки и target-семейства из прошлых исследований, а winner выбирать по `val_select_inside_mask`.

**Architecture:** Новый runner `benchmark_direction_inside_frozen_movement_regime_rich_features.py` переиспользует split, feature builders и targets из entry-based closeout/powerful/amplitude этапов. Он строит признаки для всех строк, обучается на полном `train`, выбирает winner по `val_select_inside_mask`, а затем отдельно считает метрики на full и frozen-selected срезах.

**Tech Stack:** Python 3.10+, pandas, numpy, scikit-learn, optional xgboost, существующие helpers из `ML/baseline/benchmark_entry_based_next_open_closeout.py`, `ML/baseline/benchmark_entry_based_powerful_tabular.py`, `ML/baseline/benchmark_entry_based_amplitude_movement.py`, `ML/baseline/benchmark_entry_based_movement_filter_freeze.py`, `./.venv/bin/python`, pytest.

## Global Constraints

- Работать в текущей ветке; worktree запрещён.
- Использовать `./.venv/bin/python`.
- `locked_test` не открывать.
- `low_n_disclosure` / 2026 не использовать для выбора.
- Не менять frozen movement rule: `simple_combined / extra_trees_small / H3 / top_fraction=0.05 / seeds=[42,43,44]`.
- Обучать direction-модель на полном `train`, а не на `selected=True`.
- Frozen-mask использовать только для evaluation slices после fit.
- Главная метрика выбора: `val_select_inside_mask`, то есть `val_select` с `frozen_selected=True`.
- `val_eval_inside_mask` — обязательное подтверждение выбранного winner.
- Full-split метрики — только диагностика, они не выбирают winner.
- Early stopping и подбор числа итераций по validation запрещены. Если они добавляются, сначала нужно ввести `val-stop`.
- Не использовать `score` и `selected` как входные признаки.
- Не использовать top-level future target columns как входные признаки.
- Разрешить serialized `Up/Dn` внутри `fractal1..fractal99`, как в предыдущих feature contracts.
- До fit доказать доступность `Up/Dn`, `shift`, `fractal0.price`, `ATR` на момент строки.
- Для любого global scaler fit только на `train`.
- Sample-size gate: `val_select_inside_mask >= 100`, `val_eval_inside_mask >= 100`, минимум `30` строк на активный знак в каждом masked-срезе.
- Годовой masked-срез с `N < 30` является diagnostic-only.
- `nearest_k80` участвует как exploratory-control и сам по себе не может создать `DIRECTION_REPLICATION_REQUIRED`.
- Сохранять старый simple runner как контроль; новые артефакты писать под префиксом `direction_inside_frozen_movement_regime_rich_features`.
- Максимальный положительный verdict: `DIRECTION_REPLICATION_REQUIRED`.
- Не делать live/trading claims, PnL/PF, spread, stop-loss, take-profit.
- После Python-изменений запускать `./.venv/bin/python -m pytest tests/ -q`.

---

## Files

**Create**

- `ML/baseline/benchmark_direction_inside_frozen_movement_regime_rich_features.py` — новый runner богатой проверки.
- `tests/test_direction_inside_frozen_movement_regime_rich_features.py` — unit/smoke тесты контракта.
- `docs/ML/benchmark_direction_inside_frozen_movement_regime_rich_features.py.md` — документация runner-а.
- `docs/reports/2026-07-08-direction-inside-frozen-movement-regime-rich-features.md` — итоговый отчёт после запуска.

**Modify**

- `docs/superpowers/roadmap.md` — заменить следующий шаг на вывод нового этапа.
- `CHANGELOG.md` — краткая запись после завершения.
- `CONTEXT_HANDOFF.md` — текущий baton pass.
- `docs/tests/tests.md` — добавить тестовый файл.
- `wiki/research/fractal-stop-research.md`, `wiki/index.md`, `wiki/log.md`, `wiki/REPO_integrity.md` — обновить через wiki tooling.

**Generated**

- `ML/reports/direction_inside_frozen_movement_regime_rich_features.json`
- `ML/reports/direction_inside_frozen_movement_regime_rich_features_metrics.csv`
- `ML/reports/direction_inside_frozen_movement_regime_rich_features_rows.csv`

---

### Task 1: Contract And Frozen Mask Join

**Files:**
- Create: `ML/baseline/benchmark_direction_inside_frozen_movement_regime_rich_features.py`
- Create: `tests/test_direction_inside_frozen_movement_regime_rich_features.py`

**Interfaces:**
- Produces `RICH_DIRECTION_OUTPUT_PREFIX = "direction_inside_frozen_movement_regime_rich_features"`.
- Produces `rich_direction_config() -> dict[str, object]`.
- Produces `load_rich_direction_inputs(...) -> dict[str, object]`.
- Produces `attach_frozen_mask_by_row_id(splits: dict[str, pd.DataFrame], scores: pd.DataFrame) -> dict[str, pd.DataFrame]`.

- [ ] **Step 1: Write failing tests for full-train and row identity**

Add tests proving:

```python
def test_config_uses_full_train_not_selected_train():
    config = runner.rich_direction_config()
    assert config["training_scope"] == "full_train"
    assert config["frozen_mask_usage"] == "evaluation_only"
    assert "score" in config["forbidden_input_columns"]
    assert "selected" in config["forbidden_input_columns"]


def test_attach_frozen_mask_uses_split_row_id_not_time():
    splits = {
        "train": pd.DataFrame(
            {
                "time": ["2020-01-01 00:00:00", "2020-01-01 00:00:00"],
                "entry_up_3": [2.0, 1.0],
                "entry_dn_3": [1.0, 2.0],
            }
        )
    }
    scores = pd.DataFrame(
        {
            "split": ["train", "train"],
            "split_row_id": [0, 1],
            "time": ["2020-01-01 00:00:00", "2020-01-01 00:00:00"],
            "selected": [True, False],
            "score": [10.0, 1.0],
        }
    )
    out = runner.attach_frozen_mask_by_row_id(splits, scores)
    assert out["train"]["frozen_selected"].tolist() == [True, False]
```

Run:

```bash
./.venv/bin/python -m pytest tests/test_direction_inside_frozen_movement_regime_rich_features.py -q
```

Expected: fail because the new module does not exist.

- [ ] **Step 2: Implement the contract**

Implement:

- config with frozen rule hash from `benchmark_entry_based_movement_filter_freeze`;
- required score columns: `split`, `split_row_id`, `selected`;
- strict join by `split + split_row_id`;
- abort if row counts differ after join;
- abort if `split_row_id` is missing;
- convert `selected` to boolean `frozen_selected`.
- add `selection_metric = "val_select_inside_mask"` to config;
- add `validation_roles = {"val_stop": "not_used_no_early_stopping", "val_select": "selection", "val_eval": "confirmation"}`.

- [ ] **Step 3: Verify task**

Run:

```bash
./.venv/bin/python -m pytest tests/test_direction_inside_frozen_movement_regime_rich_features.py -q
```

Expected: pass for Task 1 tests.

---

### Task 2: Feature Profiles From Previous Studies

**Files:**
- Modify: `ML/baseline/benchmark_direction_inside_frozen_movement_regime_rich_features.py`
- Modify: `tests/test_direction_inside_frozen_movement_regime_rich_features.py`

**Interfaces:**
- Produces `RICH_FEATURE_PROFILES = ("simple_combined", "nearest_k60", "nearest_k80", "corridor_5atr", "all100")`.
- Produces `build_rich_feature_frames(splits, profile) -> dict[str, pd.DataFrame]`.
- Produces `audit_forbidden_feature_columns(features: pd.DataFrame) -> dict[str, object]`.

- [ ] **Step 1: Write failing feature profile tests**

Add tests proving:

```python
def test_feature_profiles_include_old_control_and_borrowed_profiles():
    assert runner.RICH_FEATURE_PROFILES == (
        "simple_combined",
        "nearest_k60",
        "nearest_k80",
        "corridor_5atr",
        "all100",
    )


def test_nearest_k80_is_exploratory_control_not_positive_verdict_source():
    config = runner.rich_direction_config()
    assert "nearest_k80" in runner.RICH_FEATURE_PROFILES
    assert config["exploratory_only_profiles"] == ["nearest_k80"]


def test_forbidden_feature_audit_rejects_top_level_targets_and_mask_columns():
    features = pd.DataFrame(
        {
            "ATR": [1.0],
            "entry_up_3": [2.0],
            "selected": [True],
            "score": [10.0],
        }
    )
    audit = runner.audit_forbidden_feature_columns(features)
    assert audit["status"] == "ERROR"
    assert set(audit["forbidden_present"]) == {"entry_up_3", "selected", "score"}
```

Run the focused test and confirm failure.

- [ ] **Step 2: Implement feature reuse**

Implement `build_rich_feature_frames` by reusing existing builders from:

- `benchmark_entry_based_next_open_closeout.py` for `nearest_k60`, `nearest_k80`, `corridor_5atr`, `all100`;
- the current simple direction runner for `simple_combined`.

Rules:

- build features for all rows in each split;
- do not filter by `frozen_selected`;
- preserve row order;
- return only numeric model inputs;
- write feature column list into JSON.
- write feature availability audit for `Up/Dn`, `shift`, `fractal0.price`, `ATR`;
- abort before fit if `Up/Dn` are sourced from top-level target/postprocessing columns.

- [ ] **Step 3: Verify feature task**

Run:

```bash
./.venv/bin/python -m pytest tests/test_direction_inside_frozen_movement_regime_rich_features.py -q
```

Expected: pass.

---

### Task 3: Multi-Horizon Targets

**Files:**
- Modify: `ML/baseline/benchmark_direction_inside_frozen_movement_regime_rich_features.py`
- Modify: `tests/test_direction_inside_frozen_movement_regime_rich_features.py`

**Interfaces:**
- Produces `RICH_TARGET_HORIZONS = (3, 6, 12, 24)`.
- Produces `RICH_TARGET_FAMILIES = ("entry_log_ratio", "entry_up_dn_delta", "entry_up_dn_classifier")`.
- Produces `build_direction_targets(frame: pd.DataFrame, horizon: int) -> pd.DataFrame`.

- [ ] **Step 1: Write failing target tests**

Add tests proving:

```python
def test_target_families_and_horizons_are_borrowed_from_previous_studies():
    assert runner.RICH_TARGET_HORIZONS == (3, 6, 12, 24)
    assert runner.RICH_TARGET_FAMILIES == (
        "entry_log_ratio",
        "entry_up_dn_delta",
        "entry_up_dn_classifier",
    )


def test_build_direction_targets_uses_log_ratio_and_up_dn_comparison():
    frame = pd.DataFrame(
        {
            "entry_log_ratio_12": [0.4, -0.2, 0.0],
            "entry_up_12": [5.0, 1.0, 2.0],
            "entry_dn_12": [1.0, 3.0, 2.0],
        }
    )
    targets = runner.build_direction_targets(frame, 12)
    assert targets["direction_from_log_ratio"].tolist() == [1, -1, 0]
    assert targets["direction_from_up_dn"].tolist() == [1, -1, 0]


def test_dead_zone_marks_small_log_ratio_as_neutral():
    frame = pd.DataFrame(
        {
            "entry_log_ratio_3": [0.2, 0.000001, -0.3],
            "entry_up_3": [3.0, 2.0, 1.0],
            "entry_dn_3": [1.0, 2.0, 4.0],
        }
    )
    targets = runner.build_direction_targets(frame, 3, dead_zone=0.01)
    assert targets["direction_from_log_ratio"].tolist() == [1, 0, -1]
```

Run the focused test and confirm failure.

- [ ] **Step 2: Implement targets**

Implement:

- `entry_log_ratio_H` regression target;
- `entry_up_H - entry_dn_H` regression target;
- binary direction classification target from `entry_up_H > entry_dn_H`;
- tie rows marked and excluded from classification metrics, but still disclosed.
- dead-zone rows marked neutral and excluded from direction accuracy metrics, but disclosed.

- [ ] **Step 3: Verify target task**

Run:

```bash
./.venv/bin/python -m pytest tests/test_direction_inside_frozen_movement_regime_rich_features.py -q
```

Expected: pass.

---

### Task 4: Full-Train Fitting And Frozen Evaluation Slices

**Files:**
- Modify: `ML/baseline/benchmark_direction_inside_frozen_movement_regime_rich_features.py`
- Modify: `tests/test_direction_inside_frozen_movement_regime_rich_features.py`

**Interfaces:**
- Produces `fit_direction_models(train_features, train_targets, config) -> dict[str, object]`.
- Produces `evaluate_direction_predictions(predictions, targets, frozen_selected) -> dict[str, object]`.
- Produces metrics for `full` and `frozen_selected` slices.

- [ ] **Step 1: Write failing full-train test**

Add a test proving the model sees all train rows:

```python
def test_training_scope_counts_full_train_and_selected_separately():
    frame = pd.DataFrame({"frozen_selected": [True, False, True, False]})
    counts = runner.training_scope_counts(frame)
    assert counts == {
        "train_rows_used_for_fit": 4,
        "train_frozen_selected_rows": 2,
        "training_scope": "full_train",
    }


def test_sample_size_gate_blocks_tiny_masked_validation():
    metrics_input = pd.DataFrame(
        {
            "split": ["val_select"] * 50,
            "frozen_selected": [True] * 50,
            "target_direction": [1, -1] * 25,
        }
    )
    gate = runner.masked_sample_size_gate(metrics_input, split="val_select")
    assert gate["status"] == "FAIL"
    assert "min_masked_rows" in gate["reasons"]
```

Run the focused test and confirm failure.

- [ ] **Step 2: Implement model matrix**

Implement model keys:

- `hist_gradient_boosting`;
- `extra_trees`;
- optional `xgboost_depth3`;
- optional `xgboost_depth5`.

Fit only on full `train`. For each profile, horizon and target family:

- train model;
- predict `val_select`, `val_eval`, `low_n_disclosure`;
- compute metrics on full split;
- compute metrics on `frozen_selected=True` subset;
- write `failed_runs` instead of aborting on optional dependency errors.
- write `cumulative_search_budget`;
- write majority/sign-prior, old `simple_combined`, and no-direction baselines inside mask.

- [ ] **Step 3: Verify fitting task**

Run:

```bash
./.venv/bin/python -m pytest tests/test_direction_inside_frozen_movement_regime_rich_features.py -q
```

Expected: pass.

---

### Task 5: Winner Selection, Verdict, CLI, And Artifacts

**Files:**
- Modify: `ML/baseline/benchmark_direction_inside_frozen_movement_regime_rich_features.py`
- Modify: `tests/test_direction_inside_frozen_movement_regime_rich_features.py`

**Interfaces:**
- Produces `select_rich_direction_winner(metrics: pd.DataFrame) -> dict[str, object]`.
- Produces `rich_direction_verdict(summary: dict[str, object]) -> str`.
- Produces CLI `main()`.

- [ ] **Step 1: Write failing selection tests**

Add tests proving:

```python
def test_winner_selection_uses_val_select_inside_mask_not_val_eval_or_full_split():
    metrics = pd.DataFrame(
        [
            {"run_id": "a", "split": "val_select", "slice": "frozen_selected", "balanced_accuracy": 0.60},
            {"run_id": "c", "split": "val_select", "slice": "full", "balanced_accuracy": 0.95},
            {"run_id": "a", "split": "val_eval", "slice": "frozen_selected", "balanced_accuracy": 0.40},
            {"run_id": "b", "split": "val_select", "slice": "frozen_selected", "balanced_accuracy": 0.55},
            {"run_id": "b", "split": "val_eval", "slice": "frozen_selected", "balanced_accuracy": 0.80},
        ]
    )
    winner = runner.select_rich_direction_winner(metrics)
    assert winner["run_id"] == "a"
    assert winner["selection_split"] == "val_select"
    assert winner["selection_slice"] == "frozen_selected"
```

Run the focused test and confirm failure.

- [ ] **Step 2: Implement selection and verdict**

Selection policy:

- choose by `val_select_inside_mask`;
- report matching `val_eval_inside_mask`;
- disclose full-split metrics beside frozen metrics;
- never use `low_n_disclosure` for selection.

Verdict policy:

- `ABORT_CONTRACT_FAIL` if contract/audit fails;
- `DIRECTION_REPLICATION_REQUIRED` only if selected frozen-slice metric beats defined gates on `val_select_inside_mask` and does not collapse on `val_eval_inside_mask`;
- `nearest_k80` alone cannot produce `DIRECTION_REPLICATION_REQUIRED`; it can only suggest a follow-up replication plan;
- positive verdict requires masked sample-size gate PASS and `val_eval_inside_mask` confirmation;
- `PIVOT_AMPLITUDE_OR_ENTRY_MECHANICS` if direction fails but amplitude target diagnostics are stronger;
- otherwise `REJECT_DIRECTION_INSIDE_MOVEMENT_REGIME`.

- [ ] **Step 3: Implement CLI and artifact writing**

CLI defaults:

```bash
./.venv/bin/python ML/baseline/benchmark_direction_inside_frozen_movement_regime_rich_features.py
```

Write:

- JSON summary;
- metrics CSV;
- row-level prediction CSV.

- [ ] **Step 4: Verify task**

Run:

```bash
./.venv/bin/python -m pytest tests/test_direction_inside_frozen_movement_regime_rich_features.py -q
```

Expected: pass.

---

### Task 6: Execute Experiment And Close Stage

**Files:**
- Create: `docs/ML/benchmark_direction_inside_frozen_movement_regime_rich_features.py.md`
- Create: `docs/reports/2026-07-08-direction-inside-frozen-movement-regime-rich-features.md`
- Modify: `CHANGELOG.md`
- Modify: `CONTEXT_HANDOFF.md`
- Modify: `docs/superpowers/roadmap.md`
- Modify: `docs/tests/tests.md`
- Modify wiki files through `wiki/wiki.py generate`

- [ ] **Step 1: Run full tests**

Run:

```bash
./.venv/bin/python -m pytest tests/ -q
```

Expected: pass.

- [ ] **Step 2: Run canonical experiment**

Run:

```bash
./.venv/bin/python ML/baseline/benchmark_direction_inside_frozen_movement_regime_rich_features.py
```

Expected:

- JSON exists;
- metrics CSV exists;
- rows CSV exists;
- summary includes `training_scope = full_train`;
- summary includes `frozen_mask_usage = evaluation_only`;
- summary includes no forbidden live verdict.

- [ ] **Step 3: Write report**

Report must explain in plain language:

- what was wrong with the old feature/target setup;
- which previous studies supplied the new features and targets;
- how many rows were used for training;
- how many rows were inside frozen-mask for evaluation;
- best `val_select_inside_mask` result;
- matching `val_eval_inside_mask` result;
- 2026 disclosure result;
- final verdict and why it is not a trading candidate.

- [ ] **Step 4: Update docs and wiki**

Run:

```bash
graphify update .
./.venv/bin/python wiki/wiki.py generate
./.venv/bin/python wiki/wiki.py status
```

Expected: wiki status clean.

- [ ] **Step 5: Final verification**

Run:

```bash
git diff --check
./.venv/bin/python -m pytest tests/ -q
```

Expected: no whitespace errors, tests pass.

---

## Execution Choice

Recommended execution mode: `subagent-driven-development`.

Use one focused subagent per task:

1. contract and row identity;
2. feature-profile reuse;
3. target construction;
4. fitting/evaluation slices;
5. selection/verdict/CLI;
6. report/docs/wiki verification.

Main agent reviews every task before moving to the next one.
