# Fractal Selection Ablation On Entry-Based Target Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Проверить, даёт ли смена способа отбора и группировки фракталов устойчивый сигнал на уже зафиксированном `entry-based next open` target, если матрица добавочных ценовых признаков сама по себе не открыла полезный направленный сигнал.

**Architecture:** Этап переиспользует существующий `entry-based` target, тот же split-контракт и тот же базовый плоский формат входа. Меняется только представление входа до построения признаков: `all100`, `nearest_k`, `corridor_Xatr`, `zones_atr`, `zones_plus_nearest_k`. Для каждого профиля строятся одни и те же табличные признаки, затем выполняется ограниченное сравнение на четырёх заранее замороженных моделях. Runner обязан поддерживать длительный прогон по runtime-контракту benchmark-ов: `resume`, heartbeat, progress JSON, thread disclosure и сохранение результата после каждого run.

**Tech Stack:** Python 3.10+, pandas, numpy, scipy, scikit-learn, xgboost, существующий код `ML/fractal_level_feature_builder.py`, `ML/baseline/`, `statistics/data_contract_smoke_check.py`, `./.venv/bin/python`.

## Global Constraints

- Work on the current branch; do not use git worktree.
- Use `./.venv/bin/python` for every Python command.
- This stage stays `DIAGNOSTIC_ONLY`.
- Reuse the fixed `entry-based` target contract from `docs/reports/2026-07-02-next-open-entry-updn-foundation.md`; do not redesign `decision_time`, `entry_time`, `entry_open`, or target windows inside this stage.
- Target values may be rebuilt inside this runner only through the same canonical `entry-based` target-builder contract as the completed foundation stage; reading pre-existing CSV target columns without contract verification is not enough.
- Primary interpretation split is `val_stop=2021-2022`.
- `diagnostic_holdout=2023-2025` and `low_n_disclosure=2026` are disclosure only.
- Freeze the model matrix to exactly four tabular models:
  - `xgboost_depth3`
  - `xgboost_depth5`
  - `hist_gradient_boosting`
  - `ridge`
- Do not include `transformer` in this stage.
- Keep one flat tabular feature contract across profiles as much as possible; do not mix this stage with sequence input, padding, mask, or token-level training.
- The representation ablation must change only fractal selection/grouping, not the target family.
- Anchor contract is frozen:
  - selection anchor = `fractal0.price`;
  - ATR anchor = row-level current `ATR` of the signal row, not `fractal0` historical ATR;
  - `nearest_k`, `corridor_Xatr`, `zones_atr`, and `zones_plus_nearest_k` must all use this same anchor contract.
- Any new derived feature must be built only from values known at `signal_time`.
- Keep target columns out of features: `entry_up_*`, `entry_dn_*`, `entry_log_ratio_*`, legacy top-level `up_*/dn_*`, disclosure-only coverage columns, and any columns created only for report rows.
- Run `statistics/data_contract_smoke_check.py` before interpreting model metrics.
- Run A7-style distribution audit for every new input representation before interpreting metrics.
- Include the runtime contract from `docs/methodology/08-model-development.md`:
  - use at least `24` threads where applicable and write actual thread count to JSON;
  - print heartbeat at start, preflight, run start/end, progress `done_runs/total_runs`, `elapsed`, and `ETA` when available;
  - write `started_at`, `finished_at`, `elapsed_sec`, and per-run `elapsed_sec`;
  - save JSON after every completed run;
  - support `--resume` / `--no-resume`, default to `--resume`;
  - cover resume, progress JSON, and thread-count propagation by tests.
- This stage must not silently expand after seeing results. Any extra profile, width, or model beyond this plan requires a new plan or an explicit `DIAGNOSTIC_ONLY` amendment.

---

## Research Contract

**Main question:** Если на фиксированном `entry-based next open` target ценовые блоки не дали устойчивого направленного выигрыша, не скрыт ли слабый сигнал в самом способе отбора фракталов: все уровни, ближайшие уровни, коридор вокруг anchor или агрегаты по зонам?

**What stays frozen from the previous stage:**

- тот же `entry-based` target;
- тот же split-контракт;
- та же интерпретация `val_stop` как главного решающего окна;
- та же идея bounded diagnostic matrix;
- тот же базовый structural feature family как ядро признаков.

**Target-loading contract:**

- runner не должен слепо доверять уже существующим target-колонкам в CSV;
- допустимы два режима, но только при одинаковом каноническом contract check:
  - пересобрать `entry_up_*`, `entry_dn_*`, `entry_log_ratio_*` тем же target-builder-ом, что использовался в foundation stage;
  - или читать уже существующие колонки, но только если тот же contract check подтверждает совпадение;
- в structured artifact обязательно записать:
  - `entry_based_target_contract_check = PASS|FAIL`;
  - target-builder metadata;
  - target-builder hash или эквивалентный contract fingerprint;
  - какой режим использован: `rebuilt` или `loaded_verified`.

Рекомендация для реализации:

- по умолчанию runner пересобирает target тем же кодовым путём и только потом сверяет/пишет итоговый contract status;
- если пересборка по времени слишком тяжела, допустим режим `loaded_verified`, но только как явно записанное исключение, а не как молчаливая подмена.

**What changes in this stage:**

- представление входа до построения признаков:
  - `all100`
  - `nearest_k`
  - `corridor_Xatr`
  - `zones_atr`
  - `zones_plus_nearest_k`

**Fixed representation grid:**

| Code | Representation | Role | Frozen setting |
|---|---|---|---|
| `S0` | `all100` | baseline | все `fractal0..fractal99` |
| `S1` | `nearest_k` | primary | `k=20`, `k=40`, `k=60`, `k=80` |
| `S2` | `corridor_Xatr` | primary | `5 ATR`, `10 ATR`, `15 ATR` |
| `S3` | `zones_atr` | secondary | стандартный zone summary из текущего builder-а |
| `S4` | `zones_plus_nearest_k` | secondary | `nearest_k=40` + standard zones |

**Frozen selection anchor:**

- `fractal0.price` является единственным anchor для всех representation profile этого этапа;
- расстояния считаются в масштабе row-level current `ATR` на момент строки сигнала;
- запрещено смешивать в одном этапе альтернативные anchor-определения вроде `fractal0.ATR` или иного исторического масштаба;
- если существующий builder использует другой anchor-контракт, это должно быть зафиксировано как блокирующее расхождение, а не “мелкая реализация”.

**Fixed model grid:**

| Code | Model | Purpose |
|---|---|---|
| `M0` | `xgboost_depth3` | якорный baseline, совместимый с прошлым этапом |
| `M1` | `xgboost_depth5` | проверка более ёмкой нелинейности |
| `M2` | `hist_gradient_boosting` | независимый бустинг вне XGBoost |
| `M3` | `ridge` | линейный контроль на том же плоском входе |

**Feature-family freeze inside each representation:**

- база: `structure_full`;
- разрешённый ценовой слой: только тот минимальный набор, который уже был признан допустимым для этого target и одинаково строится на всех представлениях;
- если один и тот же ценовой блок нельзя честно построить на всех представлениях, он должен быть либо исключён из всей матрицы, либо явно вынесен в отдельный secondary disclosure, но не тихо меняться по профилям.
- `all100` baseline обязан использовать ровно тот же feature bundle, что и все сравниваемые representation profile; difference between profiles must come only from selection/grouping, not from a different feature set.

Рекомендация для этого этапа:

- основная матрица: `structure_full + distance_atr + price_coord_atr`;
- `path_reaction`, `short_updn_source_audited` и другие тяжёлые блоки сюда не переносить, чтобы не смешивать абляцию отбора с повторной абляцией признаков.

Интерпретационное ограничение:

- `distance_atr` и `price_coord_atr` частично дублируют друг друга;
- если они дают совпадающий ranking или почти одинаковые выводы, это нельзя трактовать как два независимых подтверждения;
- отчёт обязан раскрыть этот случай явно.

**Per-representation hypotheses:**

- `all100`: дальний хвост уровней нужен, и шум не доминирует.
- `nearest_k`: ценовая близость важнее свежести и дальнего хвоста.
- `corridor_Xatr`: модели нужен не набор ближайших уровней, а локальная структура вокруг `fractal0`.
- `zones_atr`: конкретный порядок уровней не нужен, достаточно агрегированной плотности и распределения по зонам.
- `zones_plus_nearest_k`: лучшая комбинация может состоять из локальной плотности плюс несколько конкретных уровней.

**Mandatory comparisons:**

1. Каждый `S1..S4` сравнивается с `S0` на одном и том же target и split.
2. Для `nearest_k` сравниваются `k=20/40/60/80`; нельзя объявлять winner по одному `k`.
3. Для `corridor_Xatr` сравниваются `5/10/15 ATR`; нельзя объявлять `corridor` проваленным без отчёта о покрытии.
4. Все сравнения делаются сначала внутри каждой модели, а уже потом сводятся поперёк моделей.
5. Отчёт обязан разделять:
   - directional balance (`entry_log_ratio_h`);
   - amplitude trace (`entry_up_h`, `entry_dn_h`);
   - устойчивость по `val_stop` против disclosure split.
6. Нельзя оценивать только “overall best”. Нужна матрица выводов:
   - какой способ отбора добавляет направление;
   - какой добавляет только амплитуду;
   - какой нестабилен по моделям;
   - какой на деле просто ухудшает покрытие.

**Stage verdicts:**

- `PASS_DIAGNOSTIC`: runner complete, preflight/distribution checks recorded, and full frozen matrix executed reproducibly.
- `FEATURE_CONTRACT_FAILED`: хотя бы один профиль не может быть построен без нарушения feature contract или без несогласованной схемы полей.
- `DISTRIBUTION_AUDIT_FAILED`: хотя бы один профиль имеет нерешённые `ERROR` из A7.
- `MODEL_REPRO_FAILED`: runner не обеспечивает воспроизводимый прогон, `resume`, progress JSON или thread disclosure.
- `WEAK_TRACE_FOUND`: направленный winner не найден, но есть воспроизводимый слабый след в части моделей или представлений, который превосходит baseline по заранее оговорённому ограниченному критерию.
- `NO_SIGNAL_FOUND`: frozen matrix complete, but no representation gives stable useful uplift over `all100`.

**Weak-trace rule for this stage:**

`WEAK_TRACE_FOUND` разрешён только если одновременно выполнены все условия:

- uplift есть относительно `all100` внутри той же модели;
- uplift повторяется хотя бы на двух моделях из четырёх;
- uplift не исчезает полностью на disclosure split;
- эффект либо виден в `entry_log_ratio_h`, либо честно маркирован как amplitude-only trace.

Без этих условий использовать `WEAK_TRACE_FOUND` запрещено.

## File Structure

**Create**

- `ML/baseline/benchmark_entry_based_updn_fractal_selection_ablation.py` - bounded runner for representation ablation on fixed `entry-based` target.
- `tests/test_entry_based_updn_fractal_selection_ablation.py` - focused tests for profile registry, preflight coverage, resume/progress/thread contract, summary logic, and report artifacts.
- `docs/reports/2026-07-03-fractal-selection-ablation-entry-based-target.md` - canonical report after execution.

**Modify**

- `ML/fractal_level_feature_builder.py` only if current builders lack one of the frozen representations or metadata required for coverage audit.
- `docs/methodology/A6-fractal-feature-profile-catalog.md` only if the implementation uncovers a missing canonical definition that blocks reproducibility.
- `CHANGELOG.md`, `CONTEXT_HANDOFF.md`, `wiki/` only after stage completion and final verdict.

**Generated**

- `ML/reports/entry_based_updn_fractal_selection_ablation.json`
- `ML/reports/entry_based_updn_fractal_selection_ablation_metrics.csv`
- `ML/reports/entry_based_updn_fractal_selection_ablation_rows.csv`

**Read Before Implementation**

- `docs/methodology/00-research-management.md`
- `docs/methodology/03-feature-contract-leakage.md`
- `docs/methodology/06-temporal-split.md`
- `docs/methodology/07-baseline-first.md`
- `docs/methodology/08-model-development.md`
- `docs/methodology/A6-fractal-feature-profile-catalog.md`
- `docs/methodology/A7-feature-distribution-audit.md`
- `docs/methodology/A8-feature-target-catalog.md`
- `docs/reports/2026-07-02-next-open-entry-updn-foundation.md`
- `docs/reports/2026-07-02-entry-based-updn-price-feature-matrix.md`
- `ML/fractal_level_feature_builder.py`
- `ML/baseline/benchmark_next_open_entry_updn_foundation.py`
- `ML/baseline/benchmark_entry_based_updn_price_feature_matrix.py`

---

### Task 1: Freeze Matrix Scope And Runtime Contract

**Files:**
- Create: `tests/test_entry_based_updn_fractal_selection_ablation.py`
- Create: `ML/baseline/benchmark_entry_based_updn_fractal_selection_ablation.py`

**Interfaces:**
- Produces `SelectionAblationConfig`.
- Produces `build_representation_registry() -> dict[str, dict]`.
- Produces `build_model_registry() -> dict[str, dict]`.
- Produces `build_arg_parser() -> argparse.ArgumentParser`.
- Produces `load_or_init_report(path: Path, resume: bool) -> dict`.

- [ ] **Step 1: Write failing tests for frozen registries and CLI**

Add tests that assert:

```python
import ML.baseline.benchmark_entry_based_updn_fractal_selection_ablation as runner


def test_representation_registry_is_frozen():
    registry = runner.build_representation_registry()
    assert list(registry) == [
        "all100",
        "nearest_k20",
        "nearest_k40",
        "nearest_k60",
        "nearest_k80",
        "corridor_5atr",
        "corridor_10atr",
        "corridor_15atr",
        "zones_atr",
        "zones_plus_nearest_k40",
    ]


def test_model_registry_is_frozen():
    registry = runner.build_model_registry()
    assert list(registry) == [
        "xgboost_depth3",
        "xgboost_depth5",
        "hist_gradient_boosting",
        "ridge",
    ]


def test_arg_parser_defaults_to_resume():
    parser = runner.build_arg_parser()
    args = parser.parse_args(["--entry-based-updn-fractal-selection-ablation"])
    assert args.entry_based_updn_fractal_selection_ablation is True
    assert args.resume is True
```

- [ ] **Step 2: Run the tests to verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_updn_fractal_selection_ablation.py -k "registry or parser" -q
```

Expected: FAIL because the runner module and registries do not exist yet.

- [ ] **Step 3: Write minimal runner skeleton**

Implement:

- frozen representation registry with the exact keys above;
- frozen model registry with the exact four models above;
- config dataclass with:
  - `seeds=(42, 77, 123)`;
  - `xgb_threads=24`;
  - report paths;
  - `resume_default=True`;
  - `primary_split="val_stop"`;
- CLI with:
  - `--entry-based-updn-fractal-selection-ablation`;
  - `--resume`;
  - `--no-resume`.

- [ ] **Step 4: Run the registry tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_updn_fractal_selection_ablation.py -k "registry or parser" -q
```

Expected: PASS.

---

### Task 2: Freeze Shared Data Source, Split Contract, And Target Contract

**Files:**
- Modify: `ML/baseline/benchmark_entry_based_updn_fractal_selection_ablation.py`
- Modify: `tests/test_entry_based_updn_fractal_selection_ablation.py`

**Interfaces:**
- Produces `load_entry_based_splits() -> dict[str, pd.DataFrame]`.
- Produces `validate_entry_based_target_contract(splits: dict[str, pd.DataFrame]) -> dict`.
- Produces `build_split_summary(splits: dict[str, pd.DataFrame]) -> dict`.

- [ ] **Step 1: Write failing tests for split loading and target contract**

Add tests that assert:

- runner loads the same split names:
- runner records whether targets were `rebuilt` or `loaded_verified`;
- runner writes `entry_based_target_contract_check`;
- runner writes target-builder fingerprint/hash metadata;
- runner loads the same split names:
  - `train_core`
  - `val_stop`
  - `diagnostic_holdout`
  - `low_n_disclosure`
- required target columns exist:
  - `entry_up_3`, `entry_dn_3`
  - `entry_up_6`, `entry_dn_6`
  - `entry_up_12`, `entry_dn_12`
  - `entry_log_ratio_3`, `entry_log_ratio_6`, `entry_log_ratio_12`
- target columns are not reused as features.

- [ ] **Step 2: Run the tests to verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_updn_fractal_selection_ablation.py -k "split or target_contract" -q
```

Expected: FAIL with missing helpers.

- [ ] **Step 3: Implement shared split loading**

Implementation rules:

- reuse the same source and split logic as the completed `next open` foundation and price-feature matrix stages;
- rebuild targets through the same canonical foundation contract by default, or read them only in explicit `loaded_verified` mode with the same contract check;
- store split row counts in report JSON;
- record exact input files used by the runner.

- [ ] **Step 4: Run the split and target-contract tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_updn_fractal_selection_ablation.py -k "split or target_contract" -q
```

Expected: PASS.

---

### Task 3: Build Representation Profiles And Coverage Preflight

**Files:**
- Modify: `ML/baseline/benchmark_entry_based_updn_fractal_selection_ablation.py`
- Modify: `tests/test_entry_based_updn_fractal_selection_ablation.py`

**Interfaces:**
- Produces `build_representation_features(df: pd.DataFrame, profile_key: str) -> tuple[pd.DataFrame, dict]`.
- Produces `run_representation_preflight(df: pd.DataFrame, profile_key: str) -> dict`.
- Produces `run_all_preflight(splits: dict[str, pd.DataFrame]) -> dict`.

- [ ] **Step 1: Write failing tests for representation builders**

Add tests that assert:

- `all100` keeps all fractals in baseline form;
- `nearest_k20/40/60/80` build features with deterministic column order;
- every representation uses the same frozen anchor contract:
  - anchor price = `fractal0.price`;
  - ATR scale = row-level current `ATR`;
- `corridor_5atr/10atr/15atr` record:
  - count distribution of selected fractals;
  - share of rows with `0`, `1`, `2`, `3+` selected fractals;
  - truncation share if applicable;
  - `min_price_coord_atr` and `max_price_coord_atr`;
- `zones_atr` and `zones_plus_nearest_k40` expose stable feature counts;
- metadata includes:
  - `profile_key`
  - `selection_family`
  - `feature_names`
  - `feature_count`
  - `coverage_summary`.

- [ ] **Step 2: Run the representation-builder tests to verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_updn_fractal_selection_ablation.py -k "representation or coverage or corridor or nearest or zones" -q
```

Expected: FAIL with missing builders or metadata.

- [ ] **Step 3: Implement representation builders**

Implementation rules:

- reuse `ML/fractal_level_feature_builder.py` where possible instead of re-implementing selection logic;
- keep a consistent flat table output for all profiles;
- if a representation naturally yields fewer selected fractals, expose that via deterministic padding or aggregation already used by the existing builder, and record the exact rule in metadata;
- do not silently change feature families per profile;
- for `corridor_Xatr`, enforce the declared corridor width in metadata and preflight;
- for `nearest_k`, record `k` explicitly in metadata.
- if an existing builder uses a different anchor or ATR scale, stop and fix or explicitly fail the stage with `FEATURE_CONTRACT_FAILED`.

- [ ] **Step 4: Add preflight status logic**

Preflight must return one of:

- `PASS`
- `WARNING`
- `ERROR`

With blocking rules:

- corridor values outside declared bounds -> `ERROR`;
- meaningful share of rows with no valid selected fractals -> `ERROR`;
- corridor median selected fractals below `3` -> `WARNING`;
- extreme truncation -> `WARNING`.

- [ ] **Step 5: Run the representation-builder tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_updn_fractal_selection_ablation.py -k "representation or coverage or corridor or nearest or zones" -q
```

Expected: PASS.

---

### Task 4: Add A7-Style Distribution Audit For New Representations

**Files:**
- Modify: `ML/baseline/benchmark_entry_based_updn_fractal_selection_ablation.py`
- Modify: `tests/test_entry_based_updn_fractal_selection_ablation.py`

**Interfaces:**
- Produces `audit_feature_distribution(train_df: pd.DataFrame, other_df: pd.DataFrame, profile_key: str) -> dict`.
- Produces `run_distribution_audit(splits: dict[str, pd.DataFrame], profile_keys: list[str]) -> dict`.

- [ ] **Step 1: Write failing tests for distribution audit**

Add tests that assert:

- the audit reports feature-level statistics:
  - `missing_pct`
  - `zero_pct`
  - `p1`, `p5`, `p50`, `p95`, `p99`
  - `frac_abs_gt3`, `frac_abs_gt5`, `frac_abs_gt10`, `frac_abs_gt20`
- the audit stores train-to-validation and train-to-holdout shift summaries;
- the audit can flag:
  - `NaN` / `Inf`
  - `TAIL_GT10`
  - near-constant features
  - corridor out-of-range.

- [ ] **Step 2: Run the distribution-audit tests to verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_updn_fractal_selection_ablation.py -k "distribution_audit or tail or shift or nan" -q
```

Expected: FAIL because the audit helpers are missing.

- [ ] **Step 3: Implement distribution audit**

Implementation rules:

- decisions are taken on train/validation diagnostics, not on disclosure metrics;
- if any profile has unresolved `ERROR`, the runner must stop with `DISTRIBUTION_AUDIT_FAILED`;
- warnings must be recorded explicitly in JSON, not only printed;
- store one compact summary for report text and one detailed structure for JSON.

- [ ] **Step 4: Run the distribution-audit tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_updn_fractal_selection_ablation.py -k "distribution_audit or tail or shift or nan" -q
```

Expected: PASS.

---

### Task 5: Build Four Frozen Model Adapters

**Files:**
- Modify: `ML/baseline/benchmark_entry_based_updn_fractal_selection_ablation.py`
- Modify: `tests/test_entry_based_updn_fractal_selection_ablation.py`

**Interfaces:**
- Produces `build_model(model_key: str, seed: int, thread_count: int) -> object`.
- Produces `fit_and_predict(...) -> dict`.
- Produces `thread_config_for(model_key: str) -> dict`.

- [ ] **Step 1: Write failing tests for model registry**

Add tests that assert:

- `xgboost_depth3` and `xgboost_depth5` receive thread count `24`;
- `hist_gradient_boosting` has frozen key parameters in metadata;
- `ridge` runs with a deterministic linear setup;
- all four models return a unified result schema with:
  - `pred_entry_up_3/6/12`
  - `pred_entry_dn_3/6/12`
  - `pred_entry_log_ratio_3/6/12`
  - model metadata.

- [ ] **Step 2: Run the model-adapter tests to verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_updn_fractal_selection_ablation.py -k "model_registry or thread_count or fit_and_predict" -q
```

Expected: FAIL because the adapters do not exist yet.

- [ ] **Step 3: Implement the model adapters**

Implementation rules:

- use one unified target order across all models;
- if a model cannot natively emit multi-target outputs in the same way, wrap it explicitly and record the wrapper logic in metadata;
- keep preprocessing train-only;
- do not hand-tune parameters after seeing results.

- [ ] **Step 4: Run the model-adapter tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_updn_fractal_selection_ablation.py -k "model_registry or thread_count or fit_and_predict" -q
```

Expected: PASS.

---

### Task 6: Implement Runner Loop, Resume, Heartbeat, And Artifact Writing

**Files:**
- Modify: `ML/baseline/benchmark_entry_based_updn_fractal_selection_ablation.py`
- Modify: `tests/test_entry_based_updn_fractal_selection_ablation.py`

**Interfaces:**
- Produces `run_benchmark(args: argparse.Namespace) -> dict`.
- Produces `enumerate_jobs(...) -> list[dict]`.
- Produces `save_report_json(report: dict, path: Path) -> None`.
- Produces `write_metrics_csv(rows: list[dict], path: Path) -> None`.
- Produces `write_rows_csv(rows: pd.DataFrame, path: Path) -> None`.

- [ ] **Step 1: Write failing tests for resume and artifacts**

Add tests that assert:

- runner writes JSON after each completed job;
- rerun with `--resume` skips completed `representation/model/seed` jobs;
- `metrics.csv` uses `sep=";"` and contains:
  - `representation_key`
  - `model_key`
  - `seed`
  - `split_name`
  - `target_name`
  - `horizon`
  - `spearman`
  - `elapsed_sec`
- `rows.csv` is disclosure-only preview and contains:
  - `representation_key`
  - `model_key`
  - `seed`
  - `split_name`
  - `time`
  - `entry_time`
  - `entry_up_*`
  - `entry_dn_*`
  - predictions used in the preview.

- [ ] **Step 2: Run the resume/artifact tests to verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_updn_fractal_selection_ablation.py -k "resume or progress or metrics_csv or rows_csv" -q
```

Expected: FAIL because the runner loop and artifact writers are incomplete.

- [ ] **Step 3: Implement the runner loop**

Implementation rules:

- total job count must be fixed before training starts;
- each job key is exactly `representation/model/seed`;
- print heartbeat:
  - at runner start;
  - after preflight;
  - before each job;
  - after each job;
  - at finish;
- update:
  - `done_runs`
  - `total_runs`
  - `started_at`
  - `finished_at`
  - `elapsed_sec`
  - per-job `elapsed_sec`
  - `eta_sec` when enough jobs are done.

- [ ] **Step 4: Run the resume/artifact tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_updn_fractal_selection_ablation.py -k "resume or progress or metrics_csv or rows_csv" -q
```

Expected: PASS.

---

### Task 7: Add Summary Logic And Verdict Rules

**Files:**
- Modify: `ML/baseline/benchmark_entry_based_updn_fractal_selection_ablation.py`
- Modify: `tests/test_entry_based_updn_fractal_selection_ablation.py`

**Interfaces:**
- Produces `summarize_results(report: dict) -> dict`.
- Produces `decide_stage_status(summary: dict) -> str`.

- [ ] **Step 1: Write failing tests for summary logic**

Add tests that assert:

- `WEAK_TRACE_FOUND` is not emitted when only one model shows uplift;
- `WEAK_TRACE_FOUND` is not emitted when uplift is only on disclosure and not on `val_stop`;
- `NO_SIGNAL_FOUND` is emitted when all representations fail to improve over `all100`;
- summary reports:
  - best representation by model on `val_stop`;
  - best representation by model on disclosure;
  - whether uplift is directional or amplitude-only;
  - coverage penalties for corridor profiles.

- [ ] **Step 2: Run the summary tests to verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_updn_fractal_selection_ablation.py -k "summary or verdict or weak_trace" -q
```

Expected: FAIL because summary rules are missing.

- [ ] **Step 3: Implement summary logic**

Implementation rules:

- baseline is `all100` inside the same model family;
- do not compare raw scores across different models as if they were on the same scale;
- keep separate tables for:
  - directional bests;
  - amplitude-only bests;
  - coverage warnings;
- if the only apparent uplift comes from profiles with poor coverage, mark it explicitly.

- [ ] **Step 4: Run the summary tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_updn_fractal_selection_ablation.py -k "summary or verdict or weak_trace" -q
```

Expected: PASS.

---

### Task 8: Run Focused Tests And The Full Runner

**Files:**
- Modify: `ML/baseline/benchmark_entry_based_updn_fractal_selection_ablation.py`
- Modify: `tests/test_entry_based_updn_fractal_selection_ablation.py`

- [ ] **Step 1: Run focused tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_updn_fractal_selection_ablation.py -q
```

Expected: PASS.

- [ ] **Step 2: Run smoke-check before the long benchmark**

Run:

```bash
./.venv/bin/python statistics/data_contract_smoke_check.py
```

Expected:

- if smoke-check passes for the stage contract, proceed;
- if it fails only on legacy columns irrelevant to this stage, record that explicitly and keep the stage `DIAGNOSTIC_ONLY`;
- if it fails on current target or feature contract, stop the stage.

- [ ] **Step 3: Run the long benchmark**

Run:

```bash
./.venv/bin/python ML/baseline/benchmark_entry_based_updn_fractal_selection_ablation.py --entry-based-updn-fractal-selection-ablation --resume
```

Expected:

- JSON is updated after each run;
- heartbeats are visible during the run;
- final JSON contains `progress.done_runs == progress.total_runs`.

- [ ] **Step 4: Run full test suite after Python changes**

Run:

```bash
./.venv/bin/python -m pytest tests/ -q
```

Expected: PASS.

---

### Task 9: Write Report And Close The Stage

**Files:**
- Create: `docs/reports/2026-07-03-fractal-selection-ablation-entry-based-target.md`
- Modify: `CHANGELOG.md`
- Modify: `CONTEXT_HANDOFF.md`
- Modify: `wiki/index.md`
- Modify: `wiki/log.md`
- Modify: `wiki/research/fractal-stop-research.md`
- Modify: `wiki/REPO_integrity.md`

**Interfaces:**
- Consumes `ML/reports/entry_based_updn_fractal_selection_ablation.json`
- Consumes `ML/reports/entry_based_updn_fractal_selection_ablation_metrics.csv`
- Consumes `ML/reports/entry_based_updn_fractal_selection_ablation_rows.csv`

- [ ] **Step 1: Write the report from artifacts**

The report must include:

- why this stage follows the completed price-feature matrix;
- frozen target/split/model/representation contract;
- representation coverage preflight;
- A7-style distribution audit summary;
- main `val_stop` comparison by representation inside each model;
- disclosure table for `diagnostic_holdout` and `low_n_disclosure`;
- separate interpretation for:
  - `entry_log_ratio`
  - `entry_up`
  - `entry_dn`
- explicit statement whether any winner is:
  - robust across models;
  - weak and model-specific;
  - amplitude-only;
  - invalidated by poor coverage.
- explicit disclosure that `distance_atr` and `price_coord_atr` are not counted as two independent confirmations when they produce the same or near-identical ranking.

- [ ] **Step 2: State a formal stop condition**

The report must explicitly decide one of:

- `next open` branch remains closed for fractal-selection follow-up;
- one narrow representation family deserves a separate follow-up;
- result is too artifact-limited to interpret and needs infrastructure repair first.

- [ ] **Step 3: Sync docs and wiki**

After the report is written:

- update `CHANGELOG.md`;
- update `CONTEXT_HANDOFF.md`;
- sync the relevant wiki pages;
- regenerate `wiki/REPO_integrity.md`.

- [ ] **Step 4: Verify whitespace and repo-level tests**

Run:

```bash
git diff --check
./.venv/bin/python wiki/wiki.py status
```

Expected: no whitespace errors; wiki status clean or with intentional documented changes only.

## Expected Artifacts

- `ML/reports/entry_based_updn_fractal_selection_ablation.json`
- `ML/reports/entry_based_updn_fractal_selection_ablation_metrics.csv`
- `ML/reports/entry_based_updn_fractal_selection_ablation_rows.csv`
- `docs/reports/2026-07-03-fractal-selection-ablation-entry-based-target.md`

## Out Of Scope

- `transformer`, sequence-input, token padding, mask, and other non-tabular model classes.
- New target families or any change to `entry-based next open` target definition.
- New price-feature matrix beyond the minimal frozen common feature contract.
- Live trading rules, thresholds, or backtest mechanics.
- Follow-up rescue filters on top of a weak `next open` signal.
