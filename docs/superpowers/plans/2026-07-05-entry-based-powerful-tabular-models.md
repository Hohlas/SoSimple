# Entry-Based Powerful Tabular Models Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Проверить, извлекают ли более мощные табличные модели полезный сигнал из уже закрытой ветки `entry-based next open`, не открывая `locked_test` и не меняя механику входа.

**Architecture:** Новый runner расширяет существующий `entry_based_next_open_closeout` без изменения его артефактов: те же профили, split, targets, smoke-check, feature contract и отчётность, но отдельная модельная матрица и отдельные выходные файлы. `all100` участвует в том же прогоне, что и фрактальные профили, но сохраняет отдельную роль контроля: отчёт обязан показать общий winner и candidate-only winner без `all100`.

**Tech Stack:** Python 3.10+, pandas, numpy, scipy, scikit-learn, xgboost, lightgbm, catboost, существующий `ML/baseline/benchmark_entry_based_next_open_closeout.py`, `./.venv/bin/python`, pytest.

## Global Constraints

- Work on the current branch; do not use git worktree.
- Use `./.venv/bin/python` for every Python command.
- Do not run `git commit` during implementation unless the user explicitly asks for commits or the stage is being closed through `stage-reporting`.
- This stage stays `DIAGNOSTIC_ONLY` / `RESEARCH_ONLY`; it cannot create a live trading candidate.
- Do not open `locked_test`.
- Do not include `EURUSD` or any other cross-pair validation.
- Do not change the previous closeout artifacts:
  - `ML/reports/entry_based_next_open_closeout.json`
  - `ML/reports/entry_based_next_open_closeout_metrics.csv`
  - `ML/reports/entry_based_next_open_closeout_rows.csv`
  - `ML/reports/entry_based_next_open_closeout_scale_audit.csv`
- Write new artifacts under the prefix `entry_based_powerful_tabular`.
- Entry rule remains frozen: signal exists at `signal_time`; entry is the next available `entry_open`.
- Use exactly the same split policy as the closeout:
  - `train <= 2020`
  - `validation = 2021-2025`, split into `val_select` and `val_eval`
  - `2026 = low_n_disclosure`, selection-forbidden
  - `locked_test = not_opened`
- Use exactly these representations in one experiment:
  - `all100`
  - `corridor_5atr`
  - `nearest_k60`
  - `nearest_k80`
- `all100` is included in fitting, metrics and overall ranking, but it is a control group for the fractal-selection question.
- If `all100` wins overall, the report must say whether the winner is a general market-context result rather than a fractal-selection result.
- Candidate-only decision tables must exclude `all100`.
- Do not add `nearest_k20` unless the implementer explicitly documents why the user-requested set was expanded. Default scope is the user-requested set above.
- Use the same target horizons as closeout: `H3`, `H6`, `H12`, `H24`.
- For every target horizon, especially `H24`, write `split_horizon_overlap_check` to JSON and the report. If any target horizon can cross a split boundary, apply an embargo gap or explicitly downgrade the affected result to diagnostic-only with a written explanation. Do not silently treat a boundary-crossing horizon as clean validation evidence.
- Use the same predicted target families as closeout:
  - `entry_log_ratio_H`
  - `entry_up_H`
  - `entry_dn_H`
- Use the same derived trading diagnostic as closeout:
  - `simple_trade_H`
- Do not add new target definitions, thresholds, exits, stop-losses, take-profits or position sizing.
- Use the same feature bundle as closeout; no new feature families in this plan.
- Serialized `Up/Dn` fields inside `fractal0..fractal99` remain allowed input features.
- Top-level target/label columns remain forbidden as input features:
  - `up_*`, `dn_*`
  - `entry_up_*`, `entry_dn_*`, `entry_log_ratio_*`
  - `ret_*`, `fav_*`, `adv_*`
  - `target_*`, `label_*`, `outcome_*`
- Before any fit, run the existing entry-based smoke-check and scale/distribution audit.
- If smoke-check status is not `PASS`, abort before fitting.
- If scale/distribution audit contains `ERROR`, abort before fitting and write the blocker to JSON.
- If scale/distribution audit contains `WARNING`, continue only if every warning family is recorded in `audit_decisions` with one of: `accept_as_warning`, `fix_and_rerun`, or `block`.
- If a model needs normalization, its scaler must fit only on `train`; validation and disclosure splits may only be transformed.
- Tree boosting models may use raw numeric inputs, but the report must still disclose `normalization_mode` and scale audit status.
- Write `normalization_contract` to JSON for every model family: `mode`, `fit_split`, transformed splits, scaler type if any, feature count, and proof that `val_select`, `val_eval` and `low_n_disclosure` did not affect scaler parameters.
- Use at least 24 threads for XGBoost/LightGBM/CatBoost when possible and write actual thread count to JSON.
- CatBoost is in scope only as `catboost==1.2.8`. If it is missing from the local environment, add `catboost==1.2.8` to `requirements.txt`, install exactly that version into `./.venv`, and record the installed version in JSON and the report.
- Support `--resume` / `--no-resume`; default is `--resume`.
- `--resume` must compare current `run_config_hash` with the saved JSON and refuse to continue if representations, models, horizons, predicted target families, derived diagnostics, seeds, dependency versions or output schema differ.
- Print heartbeat for long runs.
- Save JSON after every completed run.
- Disclose full search width in the report: representations, models, seeds, horizons, predicted target families and trading diagnostic rules.
- Write `failed_runs` to JSON with model/profile/seed, elapsed time, exception type and text. A single model failure must not delete completed results or hide the failure from the report.
- Write per-run runtime metadata: elapsed time, rows, feature count, actual thread count, status and error text if failed.
- Write `yearly_metrics` for `val_select` and `val_eval` by calendar years 2021, 2022, 2023, 2024 and 2025.
- `yearly_metrics` must include `positive_years`, `best_year_share`, `without_best_year_score`, and `yearly_check_pass` for selected direction and amplitude rows.
- `low_n_disclosure=2026` is disclosure-only. Summary, winner selection, gates and verdict must not read it.

---

## Research Contract

**Main question:** Was the weak direction result caused by insufficient tabular model capacity, or does the current `entry-based next open` formulation still fail after stronger tabular models?

**Secondary question:** If stronger models improve amplitude but not direction, should the next stage pivot to movement-regime / amplitude targets rather than continuing directional search?

**Important interpretation rule:** This is not an independent discovery. The profiles, horizons and model expansion are chosen after reading previous reports, so any positive direction result is a hypothesis only. It cannot by itself become a frozen candidate or justify opening `locked_test`; it can only justify a separate replication plan.

## Model Matrix

The runner must use these model keys:

| Model key | Family | Role |
|---|---|---|
| `xgboost_depth3_baseline` | XGBoost | Same-capacity anchor against closeout |
| `xgboost_depth5_baseline` | XGBoost | Same-capacity anchor against closeout |
| `xgboost_depth7_regularized` | XGBoost | Stronger nonlinear model with regularization |
| `xgboost_depth9_regularized` | XGBoost | High-capacity stress test |
| `lightgbm_depth7_regularized` | LightGBM | Independent boosting implementation |
| `lightgbm_leaves63_regularized` | LightGBM | Higher-capacity leaf-wise boosting |
| `catboost_depth6_regularized` | CatBoost | Independent ordered boosting implementation |
| `catboost_depth8_regularized` | CatBoost | Higher-capacity CatBoost stress test |
| `extra_trees_regressor` | scikit-learn | Bagging-style nonlinear comparison |
| `hist_gradient_boosting_strong` | scikit-learn | Stronger version of existing HGB baseline |

Use one seed for deterministic first pass: `42`.

One seed is sufficient only for this diagnostic pass. If any candidate-only direction row passes diagnostic gates, the verdict must be `DIRECTION_REPLICATION_REQUIRED`, and the follow-up plan must rerun the selected row on at least 3 seeds before any stronger conclusion.

Expected search width:

```text
4 representations * 10 models * 1 seed * 4 horizons * 3 predicted target families
```

There are 40 model/profile jobs. Each job predicts the same 12 target columns used by closeout. `simple_trade_H` is computed from predictions as a trading diagnostic and is disclosed separately, not counted as a fourth predicted target family.

## Gate Policy

This stage can end with:

- `REJECT_CAPACITY_EXPLANATION`: stronger tabular models do not materially improve direction.
- `PIVOT_AMPLITUDE`: direction remains weak, but amplitude strengthens or stays clearly stronger than direction.
- `DIRECTION_REPLICATION_REQUIRED`: a candidate-only profile passes diagnostic direction gates, but the stage is post-hoc and requires a separate multi-seed replication plan.

Direction gates:

- candidate-only `entry_log_ratio` on `val_select >= 0.10`;
- same selected row on `val_eval >= 0.05`;
- candidate-only profile, not `all100`;
- improvement over the previous closeout candidate-only baseline `nearest_k60 / xgboost_depth5 / H12 = 0.0373 / 0.0274`;
- improvement over `all100` on the same validation role, or explicit report text explaining why the candidate-only result is still meaningful;
- comparison against `all100` on the same model, horizon and target when that matching `all100` row exists;
- stable positive sign and comparable rank between `val_select` and `val_eval`;
- year-by-year check does not show the whole result concentrated in one validation year;
- `simple_trade` mean positive on both `val_select` and `val_eval`;
- `simple_trade` is not worse than the previous closeout candidate-only baseline on the same validation roles, or the report explicitly marks the direction improvement as non-tradable ranking-only evidence;
- no blocker in smoke-check or scale audit.

Amplitude pivot gates:

- best amplitude `entry_up` or `entry_dn` on `val_select >= 0.25`;
- same selected row on `val_eval >= 0.15`;
- direction gates not passed.

If overall winner is `all100`, report it as an overall result, but do not allow any candidate-only direction verdict unless a separate non-`all100` row also passes diagnostic gates.

`FREEZE_PROPOSAL_ONLY` is intentionally not available in this plan. If a future worker sees that status in generated JSON, report or code, treat it as a bug.

Generated JSON and report must not contain any freeze-like verdict status (`FREEZE_PROPOSAL_ONLY`, `CANDIDATE`, `FROZEN`, `READY_FOR_LOCKED_TEST`). The strongest allowed positive direction status is `DIRECTION_REPLICATION_REQUIRED`.

Amplitude confirmation is not a new discovery: closeout already found strong amplitude trace. Passing amplitude gates here only supports the existing `PIVOT` toward movement-regime/amplitude research.

## File Structure

**Create**

- `ML/baseline/benchmark_entry_based_powerful_tabular.py` - runner for stronger tabular models.
- `tests/test_entry_based_powerful_tabular.py` - focused tests for scope, model matrix, control/candidate separation, LightGBM/CatBoost availability handling, output paths and verdict rules.
- `docs/ML/benchmark_entry_based_powerful_tabular.py.md` - module documentation.
- `docs/reports/2026-07-05-entry-based-powerful-tabular-models.md` - final report after execution.

**Modify**

- `CHANGELOG.md` - only after final report is complete.
- `CONTEXT_HANDOFF.md` - only after final report is complete.
- `requirements.txt` - add `catboost==1.2.8` if it is not already present.
- `docs/tests/tests.md` - add focused test command.
- `MODULE_INDEX.md` - add new runner/doc/test entries if current index conventions require it.
- `wiki/research/fractal-stop-research.md`, `wiki/log.md`, `wiki/REPO_integrity.md` - update through wiki tooling after report is final.

**Generated**

- `ML/reports/entry_based_powerful_tabular.json`
- `ML/reports/entry_based_powerful_tabular_metrics.csv`
- `ML/reports/entry_based_powerful_tabular_rows.csv`
- `ML/reports/entry_based_powerful_tabular_scale_audit.csv`

**Read Before Implementation**

- `docs/methodology/README.md`
- `docs/methodology/03-feature-contract-leakage.md`
- `docs/methodology/06-temporal-split.md`
- `docs/methodology/08-model-development.md`
- `docs/methodology/09-validation-freeze.md`
- `docs/methodology/16-reporting-audit.md`
- `docs/reports/2026-07-04-entry-based-next-open-closeout.md`
- `ML/baseline/benchmark_entry_based_next_open_closeout.py`
- `tests/test_entry_based_next_open_closeout.py`

---

### Task 1: Runner Scope And Output Isolation

**Files:**
- Create: `ML/baseline/benchmark_entry_based_powerful_tabular.py`
- Create: `tests/test_entry_based_powerful_tabular.py`

**Interfaces:**
- Produces `POWERFUL_TABULAR_REPRESENTATIONS: tuple[str, ...]`.
- Produces `CONTROL_REPRESENTATIONS: tuple[str, ...]`.
- Produces `CANDIDATE_REPRESENTATIONS: tuple[str, ...]`.
- Produces `POWERFUL_TABULAR_MODEL_KEYS: tuple[str, ...]`.
- Produces `POWERFUL_TABULAR_SEEDS: tuple[int, ...]`.
- Produces `enumerate_powerful_tabular_jobs() -> list[dict[str, object]]`.

- [ ] **Step 1: Write the failing scope test**

```python
from ML.baseline import benchmark_entry_based_next_open_closeout as closeout
import ML.baseline.benchmark_entry_based_powerful_tabular as runner


def test_scope_includes_all100_and_requested_candidates_in_one_experiment():
    assert runner.POWERFUL_TABULAR_REPRESENTATIONS == (
        "all100",
        "corridor_5atr",
        "nearest_k60",
        "nearest_k80",
    )
    assert runner.CONTROL_REPRESENTATIONS == ("all100",)
    assert runner.CANDIDATE_REPRESENTATIONS == (
        "corridor_5atr",
        "nearest_k60",
        "nearest_k80",
    )


def test_output_paths_do_not_overwrite_closeout_artifacts():
    assert str(runner.REPORT_JSON_PATH) == "ML/reports/entry_based_powerful_tabular.json"
    assert str(runner.REPORT_METRICS_PATH) == "ML/reports/entry_based_powerful_tabular_metrics.csv"
    assert str(runner.REPORT_ROWS_PATH) == "ML/reports/entry_based_powerful_tabular_rows.csv"
    assert str(runner.REPORT_SCALE_AUDIT_PATH) == "ML/reports/entry_based_powerful_tabular_scale_audit.csv"
    assert runner.REPORT_JSON_PATH != closeout.REPORT_JSON_PATH
    assert runner.REPORT_METRICS_PATH != closeout.REPORT_METRICS_PATH
    assert runner.REPORT_ROWS_PATH != closeout.REPORT_ROWS_PATH
    assert runner.REPORT_SCALE_AUDIT_PATH != closeout.REPORT_SCALE_AUDIT_PATH


def test_jobs_cover_every_profile_model_seed_once():
    jobs = runner.enumerate_powerful_tabular_jobs()
    assert len(jobs) == 4 * 10 * 1
    assert {job["representation_key"] for job in jobs} == set(runner.POWERFUL_TABULAR_REPRESENTATIONS)
    assert {job["model_key"] for job in jobs} == set(runner.POWERFUL_TABULAR_MODEL_KEYS)
    assert {job["seed"] for job in jobs} == {42}
```

- [ ] **Step 2: Run the failing test**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_powerful_tabular.py::test_scope_includes_all100_and_requested_candidates_in_one_experiment -q
```

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Create minimal isolated runner constants**

Add:

```python
from __future__ import annotations

import argparse
from pathlib import Path

from ML.baseline import benchmark_entry_based_next_open_closeout as closeout


REPORT_JSON_PATH = Path("ML/reports/entry_based_powerful_tabular.json")
REPORT_METRICS_PATH = Path("ML/reports/entry_based_powerful_tabular_metrics.csv")
REPORT_ROWS_PATH = Path("ML/reports/entry_based_powerful_tabular_rows.csv")
REPORT_SCALE_AUDIT_PATH = Path("ML/reports/entry_based_powerful_tabular_scale_audit.csv")

POWERFUL_TABULAR_REPRESENTATIONS = (
    "all100",
    "corridor_5atr",
    "nearest_k60",
    "nearest_k80",
)
CONTROL_REPRESENTATIONS = ("all100",)
CANDIDATE_REPRESENTATIONS = tuple(
    key for key in POWERFUL_TABULAR_REPRESENTATIONS if key not in CONTROL_REPRESENTATIONS
)
POWERFUL_TABULAR_MODEL_KEYS = (
    "xgboost_depth3_baseline",
    "xgboost_depth5_baseline",
    "xgboost_depth7_regularized",
    "xgboost_depth9_regularized",
    "lightgbm_depth7_regularized",
    "lightgbm_leaves63_regularized",
    "catboost_depth6_regularized",
    "catboost_depth8_regularized",
    "extra_trees_regressor",
    "hist_gradient_boosting_strong",
)
POWERFUL_TABULAR_SEEDS = (42,)


def enumerate_powerful_tabular_jobs() -> list[dict[str, object]]:
    jobs: list[dict[str, object]] = []
    for representation_key in POWERFUL_TABULAR_REPRESENTATIONS:
        for model_key in POWERFUL_TABULAR_MODEL_KEYS:
            for seed in POWERFUL_TABULAR_SEEDS:
                jobs.append(
                    {
                        "representation_key": representation_key,
                        "model_key": model_key,
                        "seed": seed,
                    }
                )
    return jobs
```

- [ ] **Step 4: Run the scope tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_powerful_tabular.py -q
```

Expected: PASS for the tests added in this task.

### Task 2: Model Factory For Stronger Tabular Models

**Files:**
- Modify: `ML/baseline/benchmark_entry_based_powerful_tabular.py`
- Modify: `tests/test_entry_based_powerful_tabular.py`

**Interfaces:**
- Produces `build_powerful_tabular_model(model_key: str, seed: int, thread_count: int) -> tuple[object, dict[str, object]]`.
- Produces metadata with `model_key`, `family`, `seed`, `thread_count`, and hyperparameters.

- [ ] **Step 1: Verify CatBoost dependency and version pin**

Run:

```bash
./.venv/bin/python - <<'PY'
import importlib.util
print("catboost:", bool(importlib.util.find_spec("catboost")))
PY
```

Expected if already installed:

```text
catboost: True
```

If output is `catboost: False`, first add this exact dependency to `requirements.txt`:

```text
catboost==1.2.8
```

Then install it into the project virtualenv:

```bash
./.venv/bin/python -m pip install catboost==1.2.8
```

Do not install unpinned `catboost`. Rerun the import check and record the installed `catboost` version in JSON and the final report.

- [ ] **Step 2: Write model factory tests**

```python
def test_model_factory_exposes_expected_families_and_thread_count():
    expected_families = {
        "xgboost_depth3_baseline": "xgboost",
        "xgboost_depth5_baseline": "xgboost",
        "xgboost_depth7_regularized": "xgboost",
        "xgboost_depth9_regularized": "xgboost",
        "lightgbm_depth7_regularized": "lightgbm",
        "lightgbm_leaves63_regularized": "lightgbm",
        "catboost_depth6_regularized": "catboost",
        "catboost_depth8_regularized": "catboost",
        "extra_trees_regressor": "extra_trees",
        "hist_gradient_boosting_strong": "hist_gradient_boosting",
    }
    for model_key, family in expected_families.items():
        model, metadata = runner.build_powerful_tabular_model(model_key, seed=42, thread_count=24)
        assert model is not None
        assert metadata["model_key"] == model_key
        assert metadata["family"] == family
        assert metadata["seed"] == 42
        assert metadata["thread_count"] == 24


def test_model_factory_rejects_unknown_model_key():
    try:
        runner.build_powerful_tabular_model("unknown_model_not_in_scope", seed=42, thread_count=24)
    except ValueError as exc:
        assert "unknown powerful tabular model" in str(exc)
    else:
        raise AssertionError("unknown model key was not rejected")
```

- [ ] **Step 3: Run the failing tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_powerful_tabular.py::test_model_factory_exposes_expected_families_and_thread_count -q
```

Expected: FAIL with missing `build_powerful_tabular_model`.

- [ ] **Step 4: Implement the model factory**

Add imports and implementation:

```python
import lightgbm as lgb
import xgboost as xgb
from catboost import CatBoostRegressor
from sklearn.ensemble import ExtraTreesRegressor, HistGradientBoostingRegressor
from sklearn.multioutput import MultiOutputRegressor


def build_powerful_tabular_model(model_key: str, seed: int, thread_count: int) -> tuple[object, dict[str, object]]:
    if model_key.startswith("xgboost_"):
        depth_by_key = {
            "xgboost_depth3_baseline": 3,
            "xgboost_depth5_baseline": 5,
            "xgboost_depth7_regularized": 7,
            "xgboost_depth9_regularized": 9,
        }
        if model_key not in depth_by_key:
            raise ValueError(f"unknown powerful tabular model: {model_key}")
        max_depth = depth_by_key[model_key]
        base_model = xgb.XGBRegressor(
            n_estimators=700,
            max_depth=max_depth,
            learning_rate=0.025,
            subsample=0.80,
            colsample_bytree=0.80,
            reg_alpha=0.10 if max_depth >= 7 else 0.0,
            reg_lambda=3.0 if max_depth >= 7 else 1.0,
            objective="reg:squarederror",
            random_state=seed,
            n_jobs=thread_count,
            tree_method="hist",
        )
        metadata = {
            "model_key": model_key,
            "family": "xgboost",
            "seed": seed,
            "thread_count": thread_count,
            "max_depth": max_depth,
            "n_estimators": 700,
            "learning_rate": 0.025,
            "subsample": 0.80,
            "colsample_bytree": 0.80,
            "reg_alpha": 0.10 if max_depth >= 7 else 0.0,
            "reg_lambda": 3.0 if max_depth >= 7 else 1.0,
        }
        return MultiOutputRegressor(base_model, n_jobs=1), metadata

    if model_key == "lightgbm_depth7_regularized":
        base_model = lgb.LGBMRegressor(
            n_estimators=900,
            max_depth=7,
            num_leaves=63,
            learning_rate=0.02,
            subsample=0.80,
            colsample_bytree=0.80,
            reg_alpha=0.10,
            reg_lambda=3.0,
            random_state=seed,
            n_jobs=thread_count,
            verbosity=-1,
        )
        return MultiOutputRegressor(base_model, n_jobs=1), {
            "model_key": model_key,
            "family": "lightgbm",
            "seed": seed,
            "thread_count": thread_count,
            "max_depth": 7,
            "num_leaves": 63,
            "n_estimators": 900,
            "learning_rate": 0.02,
        }

    if model_key == "lightgbm_leaves63_regularized":
        base_model = lgb.LGBMRegressor(
            n_estimators=900,
            max_depth=-1,
            num_leaves=63,
            learning_rate=0.02,
            subsample=0.80,
            colsample_bytree=0.80,
            min_child_samples=80,
            reg_alpha=0.10,
            reg_lambda=5.0,
            random_state=seed,
            n_jobs=thread_count,
            verbosity=-1,
        )
        return MultiOutputRegressor(base_model, n_jobs=1), {
            "model_key": model_key,
            "family": "lightgbm",
            "seed": seed,
            "thread_count": thread_count,
            "max_depth": -1,
            "num_leaves": 63,
            "n_estimators": 900,
            "learning_rate": 0.02,
            "min_child_samples": 80,
        }

    if model_key.startswith("catboost_"):
        depth_by_key = {
            "catboost_depth6_regularized": 6,
            "catboost_depth8_regularized": 8,
        }
        if model_key not in depth_by_key:
            raise ValueError(f"unknown powerful tabular model: {model_key}")
        depth = depth_by_key[model_key]
        base_model = CatBoostRegressor(
            iterations=900,
            depth=depth,
            learning_rate=0.025,
            loss_function="RMSE",
            l2_leaf_reg=6.0 if depth >= 8 else 3.0,
            random_seed=seed,
            thread_count=thread_count,
            verbose=False,
            allow_writing_files=False,
        )
        return MultiOutputRegressor(base_model, n_jobs=1), {
            "model_key": model_key,
            "family": "catboost",
            "seed": seed,
            "thread_count": thread_count,
            "iterations": 900,
            "depth": depth,
            "learning_rate": 0.025,
            "l2_leaf_reg": 6.0 if depth >= 8 else 3.0,
        }

    if model_key == "extra_trees_regressor":
        model = ExtraTreesRegressor(
            n_estimators=600,
            max_features=0.70,
            min_samples_leaf=20,
            random_state=seed,
            n_jobs=thread_count,
        )
        return model, {
            "model_key": model_key,
            "family": "extra_trees",
            "seed": seed,
            "thread_count": thread_count,
            "n_estimators": 600,
            "max_features": 0.70,
            "min_samples_leaf": 20,
        }

    if model_key == "hist_gradient_boosting_strong":
        base_model = HistGradientBoostingRegressor(
            max_iter=700,
            learning_rate=0.025,
            max_leaf_nodes=63,
            l2_regularization=1.0,
            random_state=seed,
        )
        return MultiOutputRegressor(base_model, n_jobs=1), {
            "model_key": model_key,
            "family": "hist_gradient_boosting",
            "seed": seed,
            "thread_count": thread_count,
            "max_iter": 700,
            "learning_rate": 0.025,
            "max_leaf_nodes": 63,
            "l2_regularization": 1.0,
        }

    raise ValueError(f"unknown powerful tabular model: {model_key}")
```

- [ ] **Step 5: Run model factory tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_powerful_tabular.py::test_model_factory_exposes_expected_families_and_thread_count tests/test_entry_based_powerful_tabular.py::test_model_factory_rejects_unknown_model_key -q
```

Expected: PASS.

### Task 3: Reuse Closeout Data Contract And Fit Pipeline

**Files:**
- Modify: `ML/baseline/benchmark_entry_based_powerful_tabular.py`
- Modify: `tests/test_entry_based_powerful_tabular.py`

**Interfaces:**
- Produces `fit_and_predict_powerful_tabular(model_key: str, seed: int, train_features: pd.DataFrame, train_targets: np.ndarray, eval_features: dict[str, pd.DataFrame], thread_count: int) -> dict[str, object]`.
- Produces `evaluate_powerful_tabular_job(job: dict[str, object], splits: dict[str, pd.DataFrame], report: dict[str, object]) -> dict[str, object]`.

- [ ] **Step 1: Write reuse tests**

```python
def test_powerful_runner_reuses_closeout_horizons_and_targets():
    assert runner.CLOSEOUT_HORIZONS == closeout.CLOSEOUT_HORIZONS
    assert runner.closeout_target_matrix is closeout.closeout_target_matrix
    assert runner.compute_closeout_split_metrics is closeout.compute_closeout_split_metrics


def test_job_key_is_stable_and_includes_profile_model_seed():
    job = {"representation_key": "nearest_k60", "model_key": "xgboost_depth7_regularized", "seed": 42}
    assert runner.job_key(job) == "nearest_k60/xgboost_depth7_regularized/42"
```

- [ ] **Step 2: Run the failing tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_powerful_tabular.py::test_powerful_runner_reuses_closeout_horizons_and_targets -q
```

Expected: FAIL until aliases and `job_key` exist.

- [ ] **Step 3: Add closeout aliases and fit function**

Add:

```python
import time

import numpy as np
import pandas as pd


CLOSEOUT_HORIZONS = closeout.CLOSEOUT_HORIZONS
closeout_target_matrix = closeout.closeout_target_matrix
closeout_predictions_frame = closeout.closeout_predictions_frame
compute_closeout_split_metrics = closeout.compute_closeout_split_metrics
build_closeout_representation_features = closeout.build_closeout_representation_features


def job_key(job: dict[str, object]) -> str:
    return f"{job['representation_key']}/{job['model_key']}/{job['seed']}"


def fit_and_predict_powerful_tabular(
    model_key: str,
    seed: int,
    train_features: pd.DataFrame,
    train_targets: np.ndarray,
    eval_features: dict[str, pd.DataFrame],
    thread_count: int,
) -> dict[str, object]:
    model, metadata = build_powerful_tabular_model(model_key, seed=seed, thread_count=thread_count)
    model.fit(train_features.to_numpy(dtype=np.float32), train_targets)
    predictions_by_split: dict[str, pd.DataFrame] = {}
    for split_name, features in eval_features.items():
        preds = np.asarray(model.predict(features.to_numpy(dtype=np.float32)), dtype=np.float32)
        predictions_by_split[split_name] = closeout_predictions_frame(preds)
    return {"predictions_by_split": predictions_by_split, "model_metadata": metadata}
```

- [ ] **Step 4: Add job evaluation by copying closeout metric flow with new model factory**

Implement `evaluate_powerful_tabular_job()` by following `closeout.evaluate_closeout_job()` and changing only:

```python
fitted = fit_and_predict_powerful_tabular(
    model_key=model_key,
    seed=seed,
    train_features=train_features,
    train_targets=closeout_target_matrix(splits["train"]),
    eval_features=eval_features,
    thread_count=thread_count,
)
```

The function must return the same keys as closeout:

```python
{
    "job_key": job_key(job),
    "representation_key": rep_key,
    "model_key": model_key,
    "seed": seed,
    "elapsed_sec": time.time() - started,
    "representation_metadata": train_meta,
    "model_metadata": fitted["model_metadata"],
    "split_metrics": split_metrics,
    "rows_preview": preview,
    "metrics_rows": metrics_rows,
}
```

- [ ] **Step 5: Run tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_powerful_tabular.py -q
```

Expected: PASS for tests added so far.

### Task 4: Summary And Verdict With Control/Candidate Separation

**Files:**
- Modify: `ML/baseline/benchmark_entry_based_powerful_tabular.py`
- Modify: `tests/test_entry_based_powerful_tabular.py`

**Interfaces:**
- Produces `summarize_powerful_tabular_runs(runs: list[dict[str, object]]) -> dict[str, object]`.
- Produces `decide_powerful_tabular_verdict(summary: dict[str, object]) -> str`.
- Produces `compute_yearly_metrics(...) -> dict[str, object]` for `val_select` and `val_eval`.
- Produces `validate_powerful_tabular_feature_names(feature_names: Sequence[str]) -> None`.
- Produces `compare_candidate_against_all100_same_model(runs: list[dict[str, object]], selected: dict[str, object]) -> dict[str, object]`.
- Produces `compare_simple_trade_against_closeout_baseline(selected: dict[str, object]) -> dict[str, object]`.
- Produces `selected_yearly_metrics(runs: list[dict[str, object]], selected: dict[str, object], target_name: str) -> dict[str, object]`.

- [ ] **Step 1: Write verdict tests**

```python
def _run_with_direction(rep, model, select, eval_score):
    return {
        "representation_key": rep,
        "model_key": model,
        "seed": 42,
        "split_metrics": {
            "val_select": {
                "entry_log_ratio_12": {"spearman": select},
                "entry_up_3": {"spearman": 0.10},
                "entry_dn_3": {"spearman": 0.10},
                "simple_trade_12": {"mean": 0.01, "trade_count": 100, "long_count": 50, "short_count": 50},
            },
            "val_eval": {
                "entry_log_ratio_12": {"spearman": eval_score},
                "entry_up_3": {"spearman": 0.10},
                "entry_dn_3": {"spearman": 0.10},
                "simple_trade_12": {"mean": 0.01, "trade_count": 100, "long_count": 50, "short_count": 50},
            },
        },
    }


def _mark_direction_replication_ready(summary):
    candidate = summary["best_direction_candidate_only"]
    candidate["yearly_check_pass"] = True
    candidate["simple_trade_vs_closeout_baseline"] = {
        "select_delta": 0.01,
        "eval_delta": 0.01,
        "ranking_only_evidence": False,
    }
    candidate["same_model_all100_comparison"] = {
        "available": True,
        "candidate_minus_all100_val_select": 0.04,
        "candidate_minus_all100_val_eval": 0.02,
        "all100_underperformance_explained": False,
    }


def test_all100_can_win_overall_but_cannot_create_direction_replication_required():
    summary = runner.summarize_powerful_tabular_runs([
        _run_with_direction("all100", "xgboost_depth9_regularized", 0.20, 0.10)
    ])
    assert summary["best_direction_overall"]["representation_key"] == "all100"
    assert summary["best_direction_candidate_only"]["score"] == 0.0
    assert runner.decide_powerful_tabular_verdict(summary) != "DIRECTION_REPLICATION_REQUIRED"


def test_candidate_direction_requires_replication_instead_of_freeze():
    summary = runner.summarize_powerful_tabular_runs([
        _run_with_direction("nearest_k60", "xgboost_depth7_regularized", 0.12, 0.06),
        _run_with_direction("all100", "xgboost_depth7_regularized", 0.08, 0.04),
    ])
    _mark_direction_replication_ready(summary)
    assert runner.decide_powerful_tabular_verdict(summary) == "DIRECTION_REPLICATION_REQUIRED"


def test_candidate_direction_without_yearly_confirmation_is_rejected():
    summary = runner.summarize_powerful_tabular_runs([
        _run_with_direction("nearest_k60", "xgboost_depth7_regularized", 0.12, 0.06),
        _run_with_direction("all100", "xgboost_depth7_regularized", 0.08, 0.04),
    ])
    candidate = summary["best_direction_candidate_only"]
    candidate["yearly_check_pass"] = False
    candidate["simple_trade_vs_closeout_baseline"] = {
        "select_delta": 0.01,
        "eval_delta": 0.01,
        "ranking_only_evidence": False,
    }
    assert runner.decide_powerful_tabular_verdict(summary) != "DIRECTION_REPLICATION_REQUIRED"


def test_candidate_direction_must_not_underperform_same_model_all100():
    summary = runner.summarize_powerful_tabular_runs([
        _run_with_direction("nearest_k60", "xgboost_depth7_regularized", 0.12, 0.06),
        _run_with_direction("all100", "xgboost_depth7_regularized", 0.13, 0.07),
    ])
    _mark_direction_replication_ready(summary)
    summary["best_direction_candidate_only"]["same_model_all100_comparison"] = {
        "available": True,
        "candidate_minus_all100_val_select": -0.01,
        "candidate_minus_all100_val_eval": -0.01,
        "all100_underperformance_explained": False,
    }
    assert runner.decide_powerful_tabular_verdict(summary) != "DIRECTION_REPLICATION_REQUIRED"


def test_candidate_direction_must_not_have_weaker_simple_trade_than_closeout():
    summary = runner.summarize_powerful_tabular_runs([
        _run_with_direction("nearest_k60", "xgboost_depth7_regularized", 0.12, 0.06),
        _run_with_direction("all100", "xgboost_depth7_regularized", 0.08, 0.04),
    ])
    _mark_direction_replication_ready(summary)
    summary["best_direction_candidate_only"]["simple_trade_vs_closeout_baseline"] = {
        "select_delta": -0.01,
        "eval_delta": -0.01,
        "ranking_only_evidence": False,
    }
    assert runner.decide_powerful_tabular_verdict(summary) != "DIRECTION_REPLICATION_REQUIRED"


def test_amplitude_without_direction_returns_pivot_amplitude():
    run = _run_with_direction("nearest_k80", "lightgbm_depth7_regularized", 0.04, 0.02)
    run["split_metrics"]["val_select"]["entry_up_3"]["spearman"] = 0.35
    run["split_metrics"]["val_eval"]["entry_up_3"]["spearman"] = 0.22
    summary = runner.summarize_powerful_tabular_runs([run])
    assert runner.decide_powerful_tabular_verdict(summary) == "PIVOT_AMPLITUDE"


def test_low_n_disclosure_does_not_affect_verdict():
    run = _run_with_direction("nearest_k60", "xgboost_depth7_regularized", 0.01, 0.01)
    run["split_metrics"]["low_n_disclosure"] = {
        "entry_log_ratio_12": {"spearman": 0.99},
        "simple_trade_12": {"mean": 1.0, "trade_count": 10, "long_count": 5, "short_count": 5},
    }
    summary = runner.summarize_powerful_tabular_runs([run])
    assert runner.decide_powerful_tabular_verdict(summary) == "REJECT_CAPACITY_EXPLANATION"


def test_forbidden_target_columns_are_rejected_by_powerful_runner():
    feature_names = [
        "slot_0_price_atr",
        "entry_log_ratio_12",
        "entry_up_12",
        "target_buy_H6_val",
    ]
    try:
        runner.validate_powerful_tabular_feature_names(feature_names)
    except ValueError as exc:
        assert "forbidden target/label columns" in str(exc)
    else:
        raise AssertionError("forbidden target columns were accepted")


def test_candidate_summary_includes_same_model_all100_comparison():
    candidate = _run_with_direction("nearest_k60", "xgboost_depth7_regularized", 0.12, 0.06)
    control = _run_with_direction("all100", "xgboost_depth7_regularized", 0.08, 0.04)
    summary = runner.summarize_powerful_tabular_runs([candidate, control])
    comparison = summary["best_direction_candidate_only"]["same_model_all100_comparison"]
    assert comparison["available"] is True
    assert comparison["all100_val_select_score"] == 0.08
    assert comparison["candidate_minus_all100_val_select"] == 0.04


def test_candidate_summary_populates_yearly_metrics_from_runs():
    run = _run_with_direction("nearest_k60", "xgboost_depth7_regularized", 0.12, 0.06)
    run["yearly_metrics"] = {
        "val_select": {
            "entry_log_ratio_12": {
                "positive_years": 3,
                "best_year_share": 0.40,
                "without_best_year_score": 0.04,
                "yearly_check_pass": True,
            }
        },
        "val_eval": {
            "entry_log_ratio_12": {
                "positive_years": 2,
                "best_year_share": 0.45,
                "without_best_year_score": 0.03,
                "yearly_check_pass": True,
            }
        },
    }
    summary = runner.summarize_powerful_tabular_runs([run])
    selected = summary["best_direction_candidate_only"]
    assert selected["yearly_metrics"]["val_select"]["positive_years"] == 3
    assert selected["yearly_check_pass"] is True


def test_freeze_like_verdicts_are_rejected_from_summary_artifact():
    summary = {"verdict": "FREEZE_PROPOSAL_ONLY"}
    try:
        runner.validate_allowed_powerful_tabular_verdicts(summary)
    except ValueError as exc:
        assert "freeze-like verdict is not allowed" in str(exc)
    else:
        raise AssertionError("freeze-like verdict was accepted")
```

- [ ] **Step 2: Run the failing tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_powerful_tabular.py::test_all100_can_win_overall_but_cannot_create_direction_replication_required -q
```

Expected: FAIL until summary/verdict functions exist.

- [ ] **Step 3: Implement summary helpers**

Implement helpers that scan `runs`:

```python
def _best_metric_from_runs(
    runs: list[dict[str, object]],
    split_name: str,
    target_names: tuple[str, ...],
    allowed_representations: tuple[str, ...] | None = None,
) -> dict[str, object]:
    best: dict[str, object] = {
        "representation_key": "",
        "model_key": "",
        "seed": 0,
        "target_name": target_names[0],
        "horizon": "H3",
        "score": 0.0,
    }
    allowed = set(allowed_representations) if allowed_representations is not None else None
    for run in runs:
        rep = str(run.get("representation_key", ""))
        if allowed is not None and rep not in allowed:
            continue
        metrics = run.get("split_metrics", {}).get(split_name, {})
        for target_name in target_names:
            for horizon in CLOSEOUT_HORIZONS:
                payload = metrics.get(f"{target_name}_{horizon}", {})
                score = float(payload.get("spearman") or 0.0)
                if score > float(best["score"]):
                    best = {
                        "representation_key": rep,
                        "model_key": run["model_key"],
                        "seed": int(run["seed"]),
                        "target_name": target_name,
                        "horizon": f"H{horizon}",
                        "score": score,
                    }
    return best
```

Then implement:

```python
CLOSEOUT_CANDIDATE_ONLY_BASELINE = {
    "representation_key": "nearest_k60",
    "model_key": "xgboost_depth5",
    "horizon": "H12",
    "val_select": 0.0373,
    "val_eval": 0.0274,
}


def summarize_powerful_tabular_runs(runs: list[dict[str, object]]) -> dict[str, object]:
    best_direction_overall = _best_metric_from_runs(runs, "val_select", ("entry_log_ratio",))
    best_direction_candidate_only = _best_metric_from_runs(
        runs,
        "val_select",
        ("entry_log_ratio",),
        allowed_representations=CANDIDATE_REPRESENTATIONS,
    )
    best_amplitude_overall = _best_metric_from_runs(runs, "val_select", ("entry_up", "entry_dn"))
    summary = {
        "search_width": {
            "representations": len(POWERFUL_TABULAR_REPRESENTATIONS),
            "models": len(POWERFUL_TABULAR_MODEL_KEYS),
            "seeds": len(POWERFUL_TABULAR_SEEDS),
            "horizons": len(CLOSEOUT_HORIZONS),
            "predicted_target_families": 3,
            "derived_trading_diagnostics": 1,
            "jobs": len(runs),
            "metric_comparisons": len(POWERFUL_TABULAR_REPRESENTATIONS)
            * len(POWERFUL_TABULAR_MODEL_KEYS)
            * len(POWERFUL_TABULAR_SEEDS)
            * len(CLOSEOUT_HORIZONS)
            * 3,
        },
        "best_direction_overall": best_direction_overall,
        "best_direction_candidate_only": best_direction_candidate_only,
        "best_amplitude_overall": best_amplitude_overall,
        "best_direction_candidate_only_vs_closeout_baseline": {
            "baseline": CLOSEOUT_CANDIDATE_ONLY_BASELINE,
            "val_select_delta": float(best_direction_candidate_only["score"])
            - CLOSEOUT_CANDIDATE_ONLY_BASELINE["val_select"],
            "val_eval_delta": float(best_direction_candidate_only.get("eval_score", 0.0))
            - CLOSEOUT_CANDIDATE_ONLY_BASELINE["val_eval"],
        },
        "replication_required": False,
    }
    summary["best_direction_candidate_only"]["same_model_all100_comparison"] = (
        compare_candidate_against_all100_same_model(runs, best_direction_candidate_only)
    )
    summary["best_direction_candidate_only"]["simple_trade_vs_closeout_baseline"] = (
        compare_simple_trade_against_closeout_baseline(best_direction_candidate_only)
    )
    summary["best_direction_candidate_only"]["yearly_metrics"] = selected_yearly_metrics(
        runs,
        best_direction_candidate_only,
        target_name="entry_log_ratio",
    )
    summary["best_direction_candidate_only"]["yearly_check_pass"] = (
        summary["best_direction_candidate_only"]["yearly_metrics"]["val_select"]["yearly_check_pass"]
        and summary["best_direction_candidate_only"]["yearly_metrics"]["val_eval"]["yearly_check_pass"]
    )
    summary["best_amplitude_overall"]["yearly_metrics"] = selected_yearly_metrics(
        runs,
        best_amplitude_overall,
        target_name=str(best_amplitude_overall["target_name"]),
    )
    summary["verdict"] = decide_powerful_tabular_verdict(summary)
    summary["replication_required"] = summary["verdict"] == "DIRECTION_REPLICATION_REQUIRED"
    validate_allowed_powerful_tabular_verdicts(summary)
    return summary
```

- [ ] **Step 4: Implement verdict**

```python
def _eval_score_for_selected(summary_row: dict[str, object], runs: list[dict[str, object]] | None = None) -> float:
    return float(summary_row.get("eval_score", 0.0) or 0.0)


def decide_powerful_tabular_verdict(summary: dict[str, object]) -> str:
    candidate = summary.get("best_direction_candidate_only", {})
    amplitude = summary.get("best_amplitude_overall", {})
    candidate_select = float(candidate.get("score", 0.0) or 0.0)
    candidate_eval = float(candidate.get("eval_score", 0.0) or 0.0)
    candidate_trade_select = float(candidate.get("simple_trade_select_mean", 0.0) or 0.0)
    candidate_trade_eval = float(candidate.get("simple_trade_eval_mean", 0.0) or 0.0)
    amplitude_select = float(amplitude.get("score", 0.0) or 0.0)
    amplitude_eval = float(amplitude.get("eval_score", 0.0) or 0.0)
    candidate_baseline = summary.get("best_direction_candidate_only_vs_closeout_baseline", {})
    beats_closeout = (
        float(candidate_baseline.get("val_select_delta", 0.0) or 0.0) > 0.0
        and float(candidate_baseline.get("val_eval_delta", 0.0) or 0.0) > 0.0
    )
    yearly_check_pass = bool(candidate.get("yearly_check_pass", False))
    all100_comparison = candidate.get("same_model_all100_comparison", {})
    beats_or_explains_all100 = (
        not bool(all100_comparison.get("available", False))
        or (
            float(all100_comparison.get("candidate_minus_all100_val_select", 0.0) or 0.0) > 0.0
            and float(all100_comparison.get("candidate_minus_all100_val_eval", 0.0) or 0.0) >= 0.0
        )
        or bool(all100_comparison.get("all100_underperformance_explained", False))
    )
    simple_trade_comparison = candidate.get("simple_trade_vs_closeout_baseline", {})
    simple_trade_beats_closeout = (
        (
            float(simple_trade_comparison.get("select_delta", 0.0) or 0.0) >= 0.0
            and float(simple_trade_comparison.get("eval_delta", 0.0) or 0.0) >= 0.0
        )
        or bool(simple_trade_comparison.get("ranking_only_evidence", False))
    )

    if (
        candidate.get("representation_key") in CANDIDATE_REPRESENTATIONS
        and candidate_select >= 0.10
        and candidate_eval >= 0.05
        and beats_closeout
        and beats_or_explains_all100
        and yearly_check_pass
        and candidate_trade_select > 0.0
        and candidate_trade_eval > 0.0
        and simple_trade_beats_closeout
    ):
        return "DIRECTION_REPLICATION_REQUIRED"
    if amplitude_select >= 0.25 and amplitude_eval >= 0.15:
        return "PIVOT_AMPLITUDE"
    return "REJECT_CAPACITY_EXPLANATION"
```

Add:

```python
FORBIDDEN_POWERFUL_TABULAR_VERDICTS = {
    "FREEZE_PROPOSAL_ONLY",
    "CANDIDATE",
    "FROZEN",
    "READY_FOR_LOCKED_TEST",
}


def validate_allowed_powerful_tabular_verdicts(summary: dict[str, object]) -> None:
    verdict = str(summary.get("verdict", ""))
    if verdict in FORBIDDEN_POWERFUL_TABULAR_VERDICTS:
        raise ValueError(f"freeze-like verdict is not allowed in this stage: {verdict}")
```

While implementing, populate `eval_score`, `simple_trade_select_mean`, `simple_trade_eval_mean`, `simple_trade_vs_closeout_baseline`, `yearly_metrics`, `positive_years`, `best_year_share`, `without_best_year_score` and `yearly_check_pass` for selected summary rows by looking up the matching run/model/horizon in `val_eval` and year slices. The yearly check fails when one validation year accounts for the whole positive result, the selected row flips sign in most validation years, or `without_best_year_score <= 0`.

- [ ] **Step 5: Run verdict tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_powerful_tabular.py -q
```

Expected: PASS.

### Task 5: CLI, Resume, Artifacts And Full Run

**Files:**
- Modify: `ML/baseline/benchmark_entry_based_powerful_tabular.py`
- Modify: `tests/test_entry_based_powerful_tabular.py`

**Interfaces:**
- Produces `build_arg_parser() -> argparse.ArgumentParser`.
- Produces `build_run_config(thread_count: int, dependency_versions: dict[str, str]) -> dict[str, object]`.
- Produces `compute_run_config_hash(config: dict[str, object]) -> str`.
- Produces `validate_resume_compatibility(saved: dict[str, object], current: dict[str, object]) -> None`.
- Produces `build_normalization_contract(model_key: str, feature_names: Sequence[str]) -> dict[str, object]`.
- Produces `compute_split_horizon_overlap_check(splits: dict[str, pd.DataFrame]) -> dict[str, object]`.
- Produces `validate_audit_decisions(scale_audit: dict[str, object], audit_decisions: dict[str, object]) -> None`.
- Produces `validate_allowed_powerful_tabular_verdicts(summary: dict[str, object]) -> None`.
- Produces `run_powerful_tabular(args: argparse.Namespace) -> dict[str, object]`.
- Produces `main(argv: list[str] | None = None) -> int`.

- [ ] **Step 1: Write CLI and resume tests**

```python
from argparse import Namespace


def test_arg_parser_defaults_to_resume():
    parser = runner.build_arg_parser()
    args = parser.parse_args(["--entry-based-powerful-tabular"])
    assert args.entry_based_powerful_tabular is True
    assert args.resume is True


def test_arg_parser_accepts_no_resume():
    parser = runner.build_arg_parser()
    args = parser.parse_args(["--entry-based-powerful-tabular", "--no-resume"])
    assert args.resume is False


def test_run_config_hash_changes_when_scope_changes():
    config = runner.build_run_config(thread_count=24, dependency_versions={"catboost": "1.2.8"})
    changed = dict(config)
    changed["models"] = tuple(list(config["models"]) + ["extra_model_not_in_scope"])
    assert runner.compute_run_config_hash(config) != runner.compute_run_config_hash(changed)


def test_resume_rejects_incompatible_run_config():
    saved = {"run_config_hash": "old-hash"}
    current = {"run_config_hash": "new-hash"}
    try:
        runner.validate_resume_compatibility(saved, current)
    except RuntimeError as exc:
        assert "run_config_hash mismatch" in str(exc)
    else:
        raise AssertionError("resume accepted incompatible run config")


def test_normalization_contract_declares_train_only_fit():
    contract = runner.build_normalization_contract(
        model_key="xgboost_depth7_regularized",
        feature_names=("slot_0_price_atr", "slot_0_up_24"),
    )
    assert contract["mode"] == "raw_numeric"
    assert contract["fit_split"] == "train"
    assert contract["validation_splits_do_not_fit"] == ("val_select", "val_eval", "low_n_disclosure")
    assert contract["feature_count"] == 2


def test_horizon_overlap_check_reports_every_horizon():
    splits = {
        "train": runner._test_frame_for_overlap_check(("2020-12-30", "2020-12-31")),
        "val_select": runner._test_frame_for_overlap_check(("2021-01-01", "2023-06-30")),
        "val_eval": runner._test_frame_for_overlap_check(("2023-07-01", "2025-12-31")),
        "low_n_disclosure": runner._test_frame_for_overlap_check(("2026-01-01", "2026-03-31")),
    }
    check = runner.compute_split_horizon_overlap_check(splits)
    assert set(check["horizons"]) == {"H3", "H6", "H12", "H24"}
    assert "H24" in check["boundary_checks"]
    assert check["status"] in {"PASS", "DIAGNOSTIC_ONLY"}


def test_audit_warning_requires_recorded_decision():
    scale_audit = {"status": "WARNING", "warnings": [{"family": "TAIL_GT10"}]}
    try:
        runner.validate_audit_decisions(scale_audit, audit_decisions={})
    except RuntimeError as exc:
        assert "missing audit decision" in str(exc)
    else:
        raise AssertionError("audit warning without decision was accepted")
```

- [ ] **Step 2: Run failing CLI tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_powerful_tabular.py::test_arg_parser_defaults_to_resume -q
```

Expected: FAIL until parser exists.

- [ ] **Step 3: Implement parser and run loop**

Parser:

```python
def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Entry-based powerful tabular model runner")
    parser.add_argument("--entry-based-powerful-tabular", action="store_true")
    parser.add_argument("--resume", dest="resume", action="store_true", default=True)
    parser.add_argument("--no-resume", dest="resume", action="store_false")
    parser.add_argument("--thread-count", type=int, default=24)
    return parser
```

Add contract helpers:

```python
import hashlib
import json
from collections.abc import Sequence


POWERFUL_TABULAR_SCHEMA_VERSION = 1


def build_run_config(thread_count: int, dependency_versions: dict[str, str]) -> dict[str, object]:
    return {
        "schema_version": POWERFUL_TABULAR_SCHEMA_VERSION,
        "representations": POWERFUL_TABULAR_REPRESENTATIONS,
        "control_representations": CONTROL_REPRESENTATIONS,
        "candidate_representations": CANDIDATE_REPRESENTATIONS,
        "models": POWERFUL_TABULAR_MODEL_KEYS,
        "seeds": POWERFUL_TABULAR_SEEDS,
        "horizons": tuple(f"H{h}" for h in CLOSEOUT_HORIZONS),
        "predicted_target_families": ("entry_log_ratio", "entry_up", "entry_dn"),
        "derived_trading_diagnostics": ("simple_trade",),
        "output_paths": {
            "json": str(REPORT_JSON_PATH),
            "metrics": str(REPORT_METRICS_PATH),
            "rows": str(REPORT_ROWS_PATH),
            "scale_audit": str(REPORT_SCALE_AUDIT_PATH),
        },
        "thread_count": thread_count,
        "dependency_versions": dict(sorted(dependency_versions.items())),
    }


def compute_run_config_hash(config: dict[str, object]) -> str:
    payload = json.dumps(config, sort_keys=True, default=list).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def validate_resume_compatibility(saved: dict[str, object], current: dict[str, object]) -> None:
    if saved.get("run_config_hash") != current.get("run_config_hash"):
        raise RuntimeError("run_config_hash mismatch; refuse to resume incompatible run")


def build_normalization_contract(model_key: str, feature_names: Sequence[str]) -> dict[str, object]:
    return {
        "model_key": model_key,
        "mode": "raw_numeric",
        "fit_split": "train",
        "validation_splits_do_not_fit": ("val_select", "val_eval", "low_n_disclosure"),
        "scaler_type": None,
        "feature_count": len(tuple(feature_names)),
    }


def _test_frame_for_overlap_check(date_pair: tuple[str, str]) -> pd.DataFrame:
    timestamps = pd.to_datetime([date_pair[0], date_pair[1]])
    return pd.DataFrame({"time": timestamps, "entry_time": timestamps + pd.Timedelta(hours=1)})


def compute_split_horizon_overlap_check(splits: dict[str, pd.DataFrame]) -> dict[str, object]:
    boundary_checks: dict[str, dict[str, object]] = {}
    status = "PASS"
    ordered = ("train", "val_select", "val_eval", "low_n_disclosure")
    boundaries = []
    basis = "entry_time"
    for left_name, right_name in zip(ordered, ordered[1:]):
        if left_name not in splits or right_name not in splits:
            continue
        if "entry_time" in splits[left_name].columns:
            left_end = pd.to_datetime(splits[left_name]["entry_time"]).max()
        else:
            left_end = pd.to_datetime(splits[left_name]["time"]).max()
            basis = "signal_time_fallback"
            status = "DIAGNOSTIC_ONLY"
        right_start = pd.to_datetime(splits[right_name]["time"]).min()
        boundaries.append((left_name, right_name, left_end, right_start))
    for horizon in CLOSEOUT_HORIZONS:
        horizon_key = f"H{horizon}"
        horizon_delta = pd.Timedelta(hours=int(horizon))
        issues = []
        for left_name, right_name, left_end, right_start in boundaries:
            crosses = left_end + horizon_delta >= right_start
            if crosses:
                issues.append(
                    {
                        "left_split": left_name,
                        "right_split": right_name,
                        "left_end": str(left_end),
                        "right_start": str(right_start),
                    }
                )
        if issues:
            status = "DIAGNOSTIC_ONLY"
        boundary_checks[horizon_key] = {"crosses_boundary": bool(issues), "issues": issues}
    return {
        "status": status,
        "basis": basis,
        "horizons": tuple(f"H{h}" for h in CLOSEOUT_HORIZONS),
        "boundary_checks": boundary_checks,
    }


def validate_audit_decisions(scale_audit: dict[str, object], audit_decisions: dict[str, object]) -> None:
    status = str(scale_audit.get("status", "PASS"))
    if status == "ERROR":
        raise RuntimeError("scale/distribution audit ERROR blocks fitting")
    warnings = scale_audit.get("warnings", [])
    if status == "WARNING":
        for warning in warnings:
            family = str(warning.get("family", ""))
            if family not in audit_decisions:
                raise RuntimeError(f"missing audit decision for warning family: {family}")
            decision = str(audit_decisions[family])
            if decision not in {"accept_as_warning", "fix_and_rerun", "block"}:
                raise RuntimeError(f"invalid audit decision for warning family {family}: {decision}")
            if decision == "block":
                raise RuntimeError(f"audit decision blocks fitting for warning family: {family}")
```

Run loop must:

1. Load splits through closeout utilities.
2. Check imports and versions for `xgboost`, `lightgbm`, `catboost`, and `sklearn`.
3. Build `run_config` and `run_config_hash` from representations, models, horizons, predicted target families, derived trading diagnostics, seeds, dependency versions, output paths and schema version.
4. Run `closeout.run_entry_based_smoke_check(splits)`.
5. Abort with `RuntimeError` if smoke-check status is not `PASS`.
6. Compute `split_horizon_overlap_check` for `H3`, `H6`, `H12`, and `H24`; write it to JSON before fitting.
7. If `split_horizon_overlap_check.status` is not `PASS`, continue only with stage status `DIAGNOSTIC_ONLY` and explain the horizon boundary issue in the final report.
8. Split validation roles exactly as closeout does.
9. Build features and run `closeout.compute_feature_scale_audit()` for every representation.
10. If scale/distribution audit has `ERROR`, abort before fitting and save JSON with the blocker.
11. If scale/distribution audit has `WARNING`, call `validate_audit_decisions()` and require one explicit decision per warning family.
12. Validate feature names with `validate_powerful_tabular_feature_names()` before any fit.
13. Add `normalization_contract` for each model/profile run before fitting. For raw tree models it must say `mode=raw_numeric`, `fit_split=train`, and `validation_splits_do_not_fit=("val_select", "val_eval", "low_n_disclosure")`.
14. Write `REPORT_SCALE_AUDIT_PATH` via `closeout.write_scale_audit_csv()`.
15. Enumerate jobs.
16. If `--resume`, load existing `REPORT_JSON_PATH`, validate matching `run_config_hash`, and skip completed successful `job_key`s.
17. Wrap each job in `try/except`; append failures to `failed_runs` with elapsed time, model/profile/seed, exception type and error text.
18. Save JSON after every completed or failed run.
19. Write metrics CSV and rows CSV using the same shape as closeout artifacts.
20. Add `yearly_metrics` for `val_select` and `val_eval`, including `positive_years`, `best_year_share`, `without_best_year_score`, and `yearly_check_pass`.
21. Add summary from `summarize_powerful_tabular_runs()`.
22. Call `validate_allowed_powerful_tabular_verdicts()` before writing the final JSON/report.

Use closeout helpers where possible instead of duplicating logic.

- [ ] **Step 4: Run targeted tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_powerful_tabular.py -q
```

Expected: all focused tests PASS.

- [ ] **Step 5: Run clean experiment**

Run:

```bash
./.venv/bin/python ML/baseline/benchmark_entry_based_powerful_tabular.py --entry-based-powerful-tabular --no-resume
```

Expected:

- 40/40 jobs completed;
- `run_config_hash` exists and matches the executed matrix;
- `entry_based_smoke_check.status = PASS`;
- JSON contains `summary.verdict`;
- JSON contains `failed_runs` even if empty;
- JSON contains `yearly_metrics` for `val_select` and `val_eval`;
- metrics CSV contains all profiles, models, splits, targets and horizons;
- scale audit CSV exists.

### Task 6: Report, Documentation And Verification

**Files:**
- Create: `docs/reports/2026-07-05-entry-based-powerful-tabular-models.md`
- Create: `docs/ML/benchmark_entry_based_powerful_tabular.py.md`
- Modify: `docs/tests/tests.md`
- Modify: `MODULE_INDEX.md` if required by current index conventions.
- Modify: `CHANGELOG.md`
- Modify: `CONTEXT_HANDOFF.md`
- Modify: `wiki/research/fractal-stop-research.md`
- Modify: `wiki/log.md`
- Modify: `wiki/REPO_integrity.md`

**Interfaces:**
- Produces canonical report with reproducibility commands and artifact links.

- [ ] **Step 1: Write module documentation**

Create `docs/ML/benchmark_entry_based_powerful_tabular.py.md` with:

```markdown
# benchmark_entry_based_powerful_tabular.py

## Назначение

Runner проверяет, помогает ли рост мощности табличных моделей ветке `entry-based next open`.

## Ключевое ограничение

`all100` обучается и сравнивается в том же прогоне, что и `corridor_5atr`, `nearest_k60`, `nearest_k80`, но остаётся control. Отчёт обязан показывать общий winner и candidate-only winner.

## Запуск

```bash
./.venv/bin/python ML/baseline/benchmark_entry_based_powerful_tabular.py --entry-based-powerful-tabular --resume
```

## Артефакты

- `ML/reports/entry_based_powerful_tabular.json`
- `ML/reports/entry_based_powerful_tabular_metrics.csv`
- `ML/reports/entry_based_powerful_tabular_rows.csv`
- `ML/reports/entry_based_powerful_tabular_scale_audit.csv`
```

- [ ] **Step 2: Write report after the clean run**

The report must include:

- exact search width;
- model matrix;
- installed versions for `xgboost`, `lightgbm`, `catboost`, and `scikit-learn`;
- split sizes;
- `split_horizon_overlap_check`, with explicit H24 boundary conclusion;
- smoke-check result;
- scale/distribution audit summary;
- `audit_decisions` for every scale/distribution warning family;
- `normalization_contract`, including `fit_split=train` and confirmation that validation/disclosure did not fit any scaler;
- overall best direction table including `all100`;
- candidate-only best direction table excluding `all100`;
- same-model/same-horizon candidate-vs-`all100` comparison where available;
- amplitude table;
- simple_trade table;
- simple_trade comparison versus the previous closeout candidate-only baseline;
- yearly diagnostics with `positive_years`, `best_year_share`, `without_best_year_score`, and `yearly_check_pass`;
- 2026 low-N disclosure table;
- verdict and why;
- explicit statement that any positive direction result is only `DIRECTION_REPLICATION_REQUIRED`, not freeze/candidate;
- limitations;
- reproduction command;
- focused test result;
- full regression result if run.

- [ ] **Step 3: Run focused tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_powerful_tabular.py -q
```

Expected: PASS.

- [ ] **Step 4: Run full regression after Python changes**

Run:

```bash
./.venv/bin/python -m pytest tests/ -q
```

Expected: PASS, with known warnings only.

- [ ] **Step 5: Check formatting and wiki**

Run:

```bash
git diff --check
```

Expected: no output.

Run:

```bash
./.venv/bin/python wiki/wiki.py status
```

Expected: `Wiki is up to date. No gaps found.` after wiki updates.

---

## Self-Review Checklist

- [ ] Plan keeps `all100` in the same run as requested.
- [ ] Plan separates overall winner from candidate-only winner.
- [ ] Plan does not open `locked_test`.
- [ ] Plan does not add `EURUSD`.
- [ ] Plan does not add transformer or sequence data; that is a separate plan.
- [ ] Plan includes `CatBoost` and records how missing dependency is handled.
- [ ] Plan uses separate artifact names and cannot overwrite closeout results.
- [ ] Plan requires full disclosure of search width.
- [ ] Plan requires `split_horizon_overlap_check` for every horizon, especially `H24`.
- [ ] Plan blocks smoke-check failures and scale/distribution `ERROR` before fitting.
- [ ] Plan requires `audit_decisions` for every scale/distribution `WARNING`.
- [ ] Plan records `normalization_contract` and train-only scaler fitting.
- [ ] Plan compares candidate-only direction against same-model `all100` where available.
- [ ] Plan reports yearly concentration diagnostics, not only aggregate validation metrics.
- [ ] Plan forbids freeze-like verdicts in JSON/report/code.
- [ ] Plan requires full project tests after Python changes.
