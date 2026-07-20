# Entry-Based Up/Dn Price-Feature Matrix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Проверить, является ли отрицательный результат `next open after signal_time` следствием самой механики входа или следствием недостаточного набора признаков, путём ограниченного сравнения заранее заданных ценовых и `path-reaction` блоков на одном и том же `entry-based` target.

**Architecture:** Новый bounded runner переиспользует уже построенный `entry-based` target и сравнивает небольшой фиксированный набор feature-профилей поверх одного и того же split-контракта. Этап остаётся `DIAGNOSTIC_ONLY`: runner делает preflight, строит несколько матриц признаков, обучает один и тот же XGBoost baseline, пишет JSON после каждого run и поддерживает `resume`.

**Tech Stack:** Python 3.10+, pandas, numpy, scipy, scikit-learn, xgboost, существующий код в `ML/baseline/`, `processing/denormalize_updn.py`, `./.venv/bin/python`.

## Global Constraints

- Work on the current branch; do not use git worktree.
- Use `./.venv/bin/python` for every Python command.
- This stage is `DIAGNOSTIC_ONLY`.
- Reuse the fixed `entry-based` target contract from `next open after signal_time`; do not redesign `decision_time`, `entry_time`, `entry_open`, or label windows inside this stage.
- Primary interpretation split is `val_stop=2021-2022`.
- `diagnostic_holdout=2023-2025` and `low_n_disclosure=2026` are disclosure only.
- Freeze model family to `xgboost_depth3` and seed set to `(42, 77, 123)` unless the plan explicitly says otherwise.
- Keep target columns out of features: `entry_up_*`, `entry_dn_*`, `entry_log_ratio_*`, legacy top-level `up_*/dn_*`, coverage flags, and any rows-CSV disclosure columns.
- Do not mix this stage with `nearest_k`, `corridor_Xatr`, `zones_atr`, or any other fractal-selection ablation.
- `price_atr_scaled` is diagnostic-only evidence, not a primary candidate.
- If a feature block requires normalization or transform, fit it on train only and record the exact transform config in JSON.
- Any `Up/Dn` feature block must prove that it reads MT-accumulated fields from `fractal*` known at `signal_time`, not top-level future-labeled `up_*/dn_*`.
- Run `statistics/data_contract_smoke_check.py` before interpreting any model metric.
- Include the full runtime contract from `docs/methodology/08-model-development.md`: 24-thread usage when possible, heartbeat, `elapsed_sec`, JSON save-after-each-run, `--resume` default, and tests for resume/progress/thread count.

---

## Research Contract

**Main question:** Does any bounded price-feature block add stable predictive value for `entry-based` `Up/Dn` targets after the `next open` foundation already showed that the structural baseline alone has no useful relation to `entry_log_ratio` out of sample?

**Baseline and matrix:**

- `E0`: `structure_full` baseline from the existing `entry-based` runner.
- `E1`: `structure_full + relative_price`
- `E2`: `structure_full + distance_atr`
- `E3`: `structure_full + price_coord_atr`
- `E4`: `structure_full + short_updn_source_audited`
- `E5`: `structure_full + path_reaction`
- `E6`: `structure_full + price_atr_scaled`

**Priority classes:**

- primary: `E1`, `E3`, `E5`
- secondary: `E2`, `E4`
- diagnostic-only: `E6`

**Definitions:**

- `relative_price`: положение цены каждого фрактала относительно `fractal0`, в ATR-масштабе.
- `distance_atr`: signed/absolute distance family from the level anchor, without silently duplicating unrelated fields.
- `price_coord_atr`: ATR-normalized signed coordinate of each fractal price relative to `fractal0.price`.
- `price_atr_scaled`: `price / ATR`, optional transform such as `asinh`, treated only as regime-sensitive control.
- `short_updn_source_audited`: only `Up3/Dn3`, `Up6/Dn6`, `Up12/Dn12`, encoded as features only after explicit source audit proves they come from MT-accumulated `fractal*` fields available at `signal_time`.
- `path_reaction`: aggregate block from `ML/lib_pic_path_reaction_feature_bank.py`.

**Per-block hypotheses:**

- `relative_price`: проверяет, добавляет ли положение уровня в локальной структуре сигнал после фактического входа.
- `distance_atr`: проверяет, важна ли сама signed/absolute удалённость уровней без более богатой ценовой геометрии.
- `price_coord_atr`: проверяет, объясняет ли ATR-нормированная координата уровня ранжирование движения после входа.
- `short_updn_source_audited`: проверяет, переносится ли старая локальная реакция уровня в новую исполнимую точку входа.
- `path_reaction`: проверяет, помогает ли агрегированная историческая реакция похожих уровней после входа.
- `price_atr_scaled`: проверяет, не сидит ли слабый сигнал только в price/volatility regime, а не в механике уровня.

**Mandatory comparisons:**

1. `E0` vs every `E1..E6` on `val_stop` for `entry_log_ratio_h`.
2. Same sign check on `diagnostic_holdout` and `low_n_disclosure`.
3. Separate disclosure for `entry_up_h` and `entry_dn_h`, not only `entry_log_ratio_h`.
4. Distribution audit and transform disclosure for every added price block.
5. Feature-count and feature-order contract per profile.
6. `Up/Dn source audit` for every profile that touches `Up/Dn`.
7. Final report must include a block-level interpretation matrix:
   - adds directional balance;
   - adds amplitude only;
   - mostly reconstructs legacy `fractal0_price` target behavior;
   - unstable by years / disclosure splits.

**Stage verdicts:**

- `PASS_DIAGNOSTIC`: runner complete, all required checks recorded, and at least the bounded matrix was executed reproducibly.
- `FEATURE_CONTRACT_FAILED`: one or more price blocks cannot be built reproducibly or leak target data.
- `DISTRIBUTION_AUDIT_FAILED`: required scale/distribution checks failed and were not resolved.
- `MODEL_REPRO_FAILED`: runner, caching, or training loop is not reproducible enough to interpret results.
- `WEAK_TRACE_FOUND`: no block gives stable useful `entry_log_ratio` improvement, but one or more blocks show reproducible non-zero signal on `entry_up_h` and/or `entry_dn_h`, or a small but repeatable trace worth isolated follow-up.
- `NO_SIGNAL_FOUND`: all profiles complete, but no primary or secondary block shows stable useful improvement over `E0`.

## File Structure

**Create**

- `ML/baseline/benchmark_entry_based_updn_price_feature_matrix.py` - isolated bounded runner for the price-feature matrix.
- `tests/test_entry_based_updn_price_feature_matrix.py` - focused tests for profile registry, feature blocks, runner resume/progress/thread contract, and summary logic.
- `docs/reports/2026-07-02-entry-based-updn-price-feature-matrix.md` - canonical report after execution.

**Modify**

- `ML/lib_pic_path_reaction_feature_bank.py` only if a tiny helper export is strictly needed for reuse.
- `docs/methodology/A6-fractal-feature-profile-catalog.md` only if the execution uncovers a missing profile definition that blocks reproducibility.
- `CHANGELOG.md`, `CONTEXT_HANDOFF.md`, `wiki/` only after the stage is complete and the verdict is final.

**Generated**

- `ML/reports/entry_based_updn_price_feature_matrix.json`
- `ML/reports/entry_based_updn_price_feature_matrix_rows.csv`

**Read Before Implementation**

- `docs/methodology/00-research-management.md`
- `docs/methodology/06-temporal-split.md`
- `docs/methodology/07-baseline-first.md`
- `docs/methodology/08-model-development.md`
- `docs/methodology/A6-fractal-feature-profile-catalog.md`
- `docs/reports/2026-07-02-next-open-entry-updn-foundation.md`
- `docs/reports/2026-04-19-lib-pic-path-reaction-feature-bank.md`
- `docs/ML/lib_pic_path_reaction_feature_bank.py.md`
- `ML/baseline/benchmark_next_open_entry_updn_foundation.py`
- `ML/baseline/benchmark_regression_updn_target_foundation.py`
- `ML/lib_pic_path_reaction_feature_bank.py`
- `ML/data_loader.py`

---

### Task 1: Freeze Profile Registry And Runner Runtime Contract

**Files:**
- Create: `tests/test_entry_based_updn_price_feature_matrix.py`
- Create: `ML/baseline/benchmark_entry_based_updn_price_feature_matrix.py`

**Interfaces:**
- Produces `EntryPriceMatrixConfig`.
- Produces `PROFILE_KEYS`, `PRIMARY_PROFILE_KEYS`, `SECONDARY_PROFILE_KEYS`, `DIAGNOSTIC_PROFILE_KEYS`.
- Produces `build_profile_registry() -> dict[str, dict]`.
- Produces `build_arg_parser() -> argparse.ArgumentParser`.
- Produces `should_resume(default: bool = True) -> bool`.

- [ ] **Step 1: Write the failing registry and CLI tests**

Add tests that assert:

```python
import ML.baseline.benchmark_entry_based_updn_price_feature_matrix as runner


def test_profile_registry_is_frozen():
    registry = runner.build_profile_registry()

    assert list(registry) == [
        "structure_full",
        "structure_full_relative_price",
        "structure_full_distance_atr",
        "structure_full_price_coord_atr",
        "structure_full_short_updn_source_audited",
        "structure_full_path_reaction",
        "structure_full_price_atr_scaled",
    ]
    assert runner.PRIMARY_PROFILE_KEYS == [
        "structure_full_relative_price",
        "structure_full_price_coord_atr",
        "structure_full_path_reaction",
    ]
    assert runner.DIAGNOSTIC_PROFILE_KEYS == ["structure_full_price_atr_scaled"]


def test_arg_parser_defaults_to_resume():
    parser = runner.build_arg_parser()
    args = parser.parse_args(["--entry-based-updn-price-feature-matrix"])

    assert args.entry_based_updn_price_feature_matrix is True
    assert args.resume is True
```

- [ ] **Step 2: Run the test to verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_updn_price_feature_matrix.py -k "registry or parser" -q
```

Expected: FAIL because the module or constants do not exist yet.

- [ ] **Step 3: Write minimal implementation**

Create the new runner module with:

- config dataclass with:
  - `profile_keys`
  - `seeds = (42, 77, 123)`
  - `xgb_threads = 24`
  - report paths
  - `resume_default = True`
- frozen profile registry
- CLI with:
  - `--entry-based-updn-price-feature-matrix`
  - `--resume`
  - `--no-resume`

- [ ] **Step 4: Run the registry and CLI tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_updn_price_feature_matrix.py -k "registry or parser" -q
```

Expected: PASS.

---

### Task 2: Define Price Blocks And Their Feature Contracts

**Files:**
- Modify: `ML/baseline/benchmark_entry_based_updn_price_feature_matrix.py`
- Modify: `tests/test_entry_based_updn_price_feature_matrix.py`

**Interfaces:**
- Produces `build_relative_price_block(df: pd.DataFrame) -> pd.DataFrame`.
- Produces `build_distance_atr_block(df: pd.DataFrame) -> pd.DataFrame`.
- Produces `build_price_coord_atr_block(df: pd.DataFrame) -> pd.DataFrame`.
- Produces `audit_updn_feature_source(df: pd.DataFrame) -> dict`.
- Produces `build_short_updn_source_audited_block(df: pd.DataFrame, source_audit: dict) -> pd.DataFrame`.
- Produces `build_price_atr_scaled_block(df: pd.DataFrame) -> pd.DataFrame`.
- Produces `build_path_reaction_block(df: pd.DataFrame) -> pd.DataFrame`.
- Produces `build_profile_features(df: pd.DataFrame, profile_key: str) -> tuple[pd.DataFrame, dict]`.

- [ ] **Step 1: Write failing block-shape tests**

Add tests for:

- `relative_price` adds deterministic columns with no target names.
- `distance_atr` exposes signed and absolute distance columns.
- `audit_updn_feature_source()` fails if the block reads top-level `up_*/dn_*` instead of `fractal*`.
- `short_updn_source_audited` only uses 3/6/12 horizons and records the source audit result in metadata.
- `path_reaction` columns start with `pic_path_`.
- `build_profile_features()` returns metadata with:
  - `profile_key`
  - `feature_names`
  - `feature_count`
  - `added_blocks`
  - `block_hypothesis`
  - `updn_source_audit` when applicable

- [ ] **Step 2: Run the block tests to verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_updn_price_feature_matrix.py -k "relative_price or distance_atr or short_updn or path_reaction or source_audit" -q
```

Expected: FAIL with missing builders.

- [ ] **Step 3: Implement the price blocks**

Implementation rules:

- `relative_price`: derive from fractal price relative to `fractal0`, scaled by row `ATR`.
- `distance_atr`: include signed and absolute distance; do not add directed distance in the first version.
- `price_coord_atr`: keep the same semantic contract used in earlier Stage 5 price work.
- `audit_updn_feature_source`: prove that the block reads `Up/Dn` from MT-accumulated `fractal*` fields available at `signal_time`, not future-labeled top-level target columns.
- `short_updn_source_audited`: parse only `Up3/Dn3`, `Up6/Dn6`, `Up12/Dn12`; keep a local transform config and source-audit result in metadata.
- `path_reaction`: reuse `build_lib_pic_path_reaction_feature_bank()` and select only the generated `pic_path_*` columns.
- `price_atr_scaled`: add as diagnostic-only block and record transform, for example `asinh`, in metadata.

- [ ] **Step 4: Run the block tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_updn_price_feature_matrix.py -k "relative_price or distance_atr or short_updn or path_reaction or source_audit" -q
```

Expected: PASS.

---

### Task 3: Reuse Entry-Based Target Splits And Build Model Inputs

**Files:**
- Modify: `ML/baseline/benchmark_entry_based_updn_price_feature_matrix.py`
- Modify: `tests/test_entry_based_updn_price_feature_matrix.py`

**Interfaces:**
- Consumes: the split/target helpers from `ML/baseline/benchmark_next_open_entry_updn_foundation.py`.
- Produces `load_entry_based_splits() -> dict[str, pd.DataFrame]`.
- Produces `target_matrix(df: pd.DataFrame) -> np.ndarray`.
- Produces `profile_matrix(df: pd.DataFrame, profile_key: str) -> tuple[np.ndarray, dict]`.

- [ ] **Step 1: Write failing integration-style tests for split reuse**

Add tests that verify:

- the runner reuses the existing `entry-based` split contract instead of rebuilding a new target definition;
- `profile_matrix()` excludes all forbidden target/disclosure columns;
- the feature count recorded in metadata equals the actual matrix width.

- [ ] **Step 2: Run the split/matrix tests to verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_updn_price_feature_matrix.py -k "split reuse or forbidden or feature_count" -q
```

Expected: FAIL before the helpers exist.

- [ ] **Step 3: Implement split reuse and matrix builders**

Implementation rules:

- import and reuse the already proven target reconstruction path where possible;
- do not silently rebuild a different rows CSV contract;
- record `feature_names_sha256` or equivalent hash in per-profile metadata;
- fail fast if any forbidden target column is present in the feature set.

- [ ] **Step 4: Run the split/matrix tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_updn_price_feature_matrix.py -k "split reuse or forbidden or feature_count" -q
```

Expected: PASS.

---

### Task 4: Add Preflight, Scale Audit, And Runtime Contract

**Files:**
- Modify: `ML/baseline/benchmark_entry_based_updn_price_feature_matrix.py`
- Modify: `tests/test_entry_based_updn_price_feature_matrix.py`

**Interfaces:**
- Produces `run_preflight(...) -> dict`.
- Produces `write_report_atomic(report: dict, path: Path) -> None`.
- Produces `load_existing_report(path: Path) -> dict | None`.
- Produces `completed_run_keys(report: dict) -> set[tuple[str, int]]`.

- [ ] **Step 1: Write failing tests for runtime contract**

Add tests that verify:

- `xgb_threads` or equivalent thread count is passed into the model config;
- `--resume` skips already completed `profile/seed` keys;
- JSON is updated after each completed run;
- `progress.done_runs`, `progress.total_runs`, `progress.elapsed_sec`, `started_at`, `finished_at` appear in the report;
- heartbeat helper prints at least stage start and per-run progress.

- [ ] **Step 2: Run the runtime-contract tests to verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_updn_price_feature_matrix.py -k "resume or progress or threads or heartbeat" -q
```

Expected: FAIL.

- [ ] **Step 3: Implement preflight and runtime contract**

Implementation rules:

- call `statistics/data_contract_smoke_check.py` before model interpretation and store the result in JSON;
- include per-profile feature audit and scale/distribution disclosure;
- include `Up/Dn source audit` in JSON for any profile that touches `Up/Dn`;
- use at least `24` threads unless explicitly reduced for a documented reason;
- print heartbeat on:
  - runner start
  - preflight start/end
  - each run start
  - each run end
  - progress `done_runs/total_runs`
- save JSON after every run so resume can continue from partial progress;
- default to `--resume`.

- [ ] **Step 4: Run the runtime-contract tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_updn_price_feature_matrix.py -k "resume or progress or threads or heartbeat" -q
```

Expected: PASS.

---

### Task 5: Implement Training Loop, Summary Logic, And Rows CSV

**Files:**
- Modify: `ML/baseline/benchmark_entry_based_updn_price_feature_matrix.py`
- Modify: `tests/test_entry_based_updn_price_feature_matrix.py`

**Interfaces:**
- Produces `evaluate_profile_seed(profile_key: str, seed: int, split_frames: dict[str, pd.DataFrame]) -> dict`.
- Produces `summarize_profiles(report: dict) -> dict`.
- Produces `run_entry_based_updn_price_feature_matrix(...) -> dict`.

- [ ] **Step 1: Write failing runner-summary tests**

Add tests that verify:

- one report run is created per `profile × seed`;
- `entry_log_ratio` metrics are written for `H3/H6/H12`;
- separate `entry_up` and `entry_dn` metrics are preserved;
- profile summary labels primary/secondary/diagnostic-only correctly;
- summary can return `WEAK_TRACE_FOUND` when `entry_log_ratio` stays weak but `entry_up`/`entry_dn` show reproducible traces;
- rows CSV stays narrow and disclosure-only.

- [ ] **Step 2: Run the runner-summary tests to verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_updn_price_feature_matrix.py -k "runner or summary or rows csv" -q
```

Expected: FAIL.

- [ ] **Step 3: Implement the evaluation loop**

Implementation rules:

- train the same XGBoost family for every profile and seed;
- compare against `structure_full` baseline in the report summary;
- summarize not only the best profile, but every block against `E0` in a matrix-style interpretation table;
- store per-run:
  - `profile_key`
  - `profile_role`
  - `block_hypothesis`
  - `seed`
  - `elapsed_sec`
  - feature metadata
  - `train_core`, `val_stop`, `diagnostic_holdout`, `low_n_disclosure` metrics
- write a narrow rows CSV with:
  - split identifiers
  - target disclosure columns
  - minimal feature-disclosure columns needed for later audit
- final summary must state whether any primary or secondary block improved over `E0`.

- [ ] **Step 4: Run the runner-summary tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_updn_price_feature_matrix.py -k "runner or summary or rows csv" -q
```

Expected: PASS.

---

### Task 6: Execute The Matrix And Write The Stage Report

**Files:**
- Modify: `docs/reports/2026-07-02-entry-based-updn-price-feature-matrix.md`
- Generated: `ML/reports/entry_based_updn_price_feature_matrix.json`
- Generated: `ML/reports/entry_based_updn_price_feature_matrix_rows.csv`

**Interfaces:**
- Consumes: completed runner and JSON artifact.
- Produces: canonical report with final verdict and next-step decision.

- [ ] **Step 1: Run focused tests for the new runner**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_updn_price_feature_matrix.py -q
```

Expected: PASS.

- [ ] **Step 2: Run broader regression coverage**

Run:

```bash
./.venv/bin/python -m pytest tests/test_next_open_entry_updn_foundation.py tests/test_entry_based_updn_price_feature_matrix.py -q
```

Expected: PASS.

- [ ] **Step 3: Execute the full matrix runner**

Run:

```bash
PYTHONUNBUFFERED=1 ./.venv/bin/python ML/baseline/benchmark_entry_based_updn_price_feature_matrix.py --entry-based-updn-price-feature-matrix --resume
```

Expected:

- heartbeat in terminal;
- JSON grows after each `profile/seed` run;
- final report contains `done_runs = total_runs`;
- `started_at`, `finished_at`, `elapsed_sec` filled;
- summary clearly shows whether any primary or secondary block improved over `structure_full`.

- [ ] **Step 4: Write the final report**

The report must include:

- why this matrix was run after the negative `next open` foundation;
- exact profile set and roles;
- whether each block improved `entry_log_ratio` on `val_stop`;
- whether a block improved `entry_up` and/or `entry_dn` even if `entry_log_ratio` stayed weak;
- whether the sign persisted on disclosure splits;
- why `price_atr_scaled` is only diagnostic;
- `Up/Dn source audit` result for every block that uses `Up/Dn`;
- a matrix of conclusions by block, not only a single best-profile summary;
- explicit statement that `nearest_k`, `corridor_Xatr`, and `zones_atr` were intentionally not part of this stage.

- [ ] **Step 5: Stop-condition decision**

If all primary and secondary blocks fail to show stable improvement and no reproducible weak trace remains:

- verdict stays `DIAGNOSTIC_ONLY`;
- runner status should end in `NO_SIGNAL_FOUND`;
- next recommendation must not be “add more filters to next open”.

If no useful `entry_log_ratio` winner exists, but one block leaves a reproducible weak trace:

- verdict stays `DIAGNOSTIC_ONLY`;
- runner status should end in `WEAK_TRACE_FOUND`;
- next recommendation should be an isolated follow-up of that block with frozen target and explicit gate, not an ad hoc filter.

If one primary block shows stable improvement:

- keep status `DIAGNOSTIC_ONLY`;
- nominate only that block for a narrower follow-up stage.
