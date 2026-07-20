# Entry-Based Next Open Closeout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Добить текущую ветку `entry-based next open` и принять решение `STOP`, `PIVOT` или `CONTINUE` без проверки на `EURUSD`.

**Architecture:** Новый closeout-runner переиспользует исправленный runner абляции отбора фракталов как библиотеку, но пишет отдельные артефакты и не меняет исторический результат этапа 2026-07-03. Этап проверяет только shortlist профилей на новом split-контракте `train`/large `validation`, добавляет независимый entry-based smoke-check, оценивает `H3/H6/H12/H24`, разделяет направленный след и след амплитуды, затем выполняет простую торговую диагностику входа на следующий open.

**Tech Stack:** Python 3.10+, pandas, numpy, scipy, scikit-learn, xgboost, существующий `ML/baseline/benchmark_entry_based_updn_fractal_selection_ablation.py`, `./.venv/bin/python`, pytest.

## Global Constraints

- Work on the current branch; do not use git worktree.
- Use `./.venv/bin/python` for every Python command.
- Do not run `git commit` during implementation unless the user explicitly asks for commits or the stage is being closed through `stage-reporting`.
- This stage stays `DIAGNOSTIC_ONLY`.
- Do not include `EURUSD` or any other cross-pair validation in this plan.
- Do not change the old `entry_based_updn_fractal_selection_ablation` JSON/CSV/report artifacts except by explicit user request.
- Entry rule is frozen: signal exists at `signal_time`; trade entry is the next available `entry_open`.
- Allowed representations are exactly `all100`, `corridor_5atr`, `nearest_k20`, `nearest_k60`, `nearest_k80`.
- `all100` is a control baseline, not a candidate.
- Allowed target horizons are exactly `H3`, `H6`, `H12`, `H24`.
- Do not add new `k`, corridor width, model family, feature family beyond the frozen feature bundle below, or alternative entry rule.
- Use the updated split methodology from `docs/methodology/06-temporal-split.md`: `train`, `validation`, and `locked_test`.
- This plan does not open `locked_test`; it can only produce `RESEARCH_ONLY` / `DIAGNOSTIC_ONLY` evidence and a proposed frozen rule for a later locked-test plan.
- Use one large historical validation window for this closeout. Default calendar policy: `train <= 2020`, `validation = 2021-2025`, `2026 = low-N disclosure only`.
- If implementation can split validation roles without too little data, use `val_stop`, `val_select`, and `val_eval` inside `validation`; if not, combine roles and explicitly cap the result at `RESEARCH_ONLY`.
- Do not use `2026` for winner selection.
- Serialized `Up/Dn` fields inside `fractal0..fractal99` are allowed input features when read from the MT-produced snapshot.
- Top-level Python target/label columns `up_3..dn_48`, `entry_up_*`, `entry_dn_*`, `entry_log_ratio_*`, `ret_*`, `fav_*`, `adv_*`, `target_*`, `label_*`, and `outcome_*` are forbidden as input features.
- Features must use the same feature bundle across all shortlist profiles.
- Before any model fit, run a scale audit and normalization contract check on the final feature matrix.
- Any scaler fitted inside this closeout must fit only on `train`; `validation` and `2026` may only be transformed.
- Input feature normalization groups and target normalization groups must stay separate; target/label columns must not participate in input normalization pools.
- If the current tree model run uses raw numeric features, record `normalization_mode = "none_tree_raw"` and still run scale/dominance audit; do not silently skip the audit.
- Legacy `statistics/data_contract_smoke_check.py` may be reported, but the stage verdict must use the new entry-based smoke-check.
- The final report must disclose search width: representations, models, seeds, horizons, target families, and trading diagnostic rules.
- The stage must end with one of `STOP`, `PIVOT`, or `CONTINUE`; absence of a strong result is a valid outcome.

---

## Research Contract

**Main question:** Does the fixed `entry-based next open` mechanism contain any practically useful signal on the current instrument after the weak `H12` trace found on 2026-07-03, when validation is enlarged and serialized `Up/Dn` history is allowed as a normal input family?

**Decision meanings:**

- `STOP`: no useful directional or trading diagnostic survives validation-role evaluation and disclosure; close this exact entry mechanism.
- `PIVOT`: direction remains weak, but amplitude or movement-regime signal is stronger; next stage should stop asking “up or down” and redesign the target.
- `CONTINUE`: a narrow candidate shows useful direction and simple trading diagnostics on validation and is ready to be frozen for a separate `locked_test` plan.

**Split policy:**

| Period | Role | Calendar default | Selection use |
|---|---|---|---|
| `train` | fit model and fit any train-only scaler | `<= 2020` | allowed |
| `validation` | choose hypothesis, profile, model, horizon, and simple rule | `2021-2025` | allowed |
| `locked_test` | one-time test of a frozen rule | not opened in this plan | forbidden |
| `low_n_disclosure` | newest low-N disclosure | `2026` | forbidden |

If validation is internally split, use:

| Validation role | Purpose |
|---|---|
| `val_stop` | model-facing choices such as ablation winner |
| `val_select` | simple trading rule and horizon selection |
| `val_eval` | final validation readout of the selected rule |

If internal split is not used, all validation roles are combined and the report must say that the result cannot exceed `RESEARCH_ONLY`.

**Candidate shortlist:**

| Profile | Role | Reason |
|---|---|---|
| `all100` | control | Same-run baseline for every comparison |
| `corridor_5atr` | candidate | Best previous `H12` trace before the split-methodology update |
| `nearest_k20` | candidate | Best old disclosure value among shortlist before the split-methodology update |
| `nearest_k60` | candidate | Repeated weak `H12` trace on stronger models |
| `nearest_k80` | candidate | Nearby weak trace; tests whether larger local context matters |

**Model matrix:**

| Model | Role |
|---|---|
| `xgboost_depth3` | main nonlinear control from previous winner |
| `xgboost_depth5` | higher-capacity nonlinear check |
| `hist_gradient_boosting` | independent boosting family |
| `ridge` | linear sanity control, interpreted cautiously |

**Outcome families:**

- `entry_log_ratio_H`: directional balance.
- `entry_up_H` and `entry_dn_H`: amplitude trace.
- `simple_trade_H`: gross signed outcome from the model side decision using the frozen next-open entry.

**Frozen feature bundle:**

- `structure_fields`: `direction`, `front`, `back`, `strong`, `break`, `reverse`, `power`, `count`, `impulse`.
- `shift_age`: `shift`, `log_shift`, and neighbor shift gap where the existing builder can produce it consistently.
- `atr_ratio`: `log(fractal_atr / row_ATR)` or the equivalent existing builder field.
- `price_coord_atr` / `distance_atr`: price location relative to `fractal0.price`, scaled by row `ATR`.
- `updn_full`: serialized MT snapshot fields `up_3/dn_3`, `up_6/dn_6`, `up_12/dn_12`, `up_24/dn_24`, `up_48/dn_48` inside `fractal*`.
- `row_context_time`: `session_hour`, `weekday`, or derived `hour_sin/hour_cos/dow_sin/dow_cos` if available from `time` without future data.

Do not add `path_reaction`, limit-order labels, trailing-stop labels, `signal`, `predict`, top-level `up_*/dn_*`, or top-level entry path columns to this closeout. Those are separate feature/target families and would turn the closeout into a wider search.

**Primary stop rules:**

- If best `entry_log_ratio` score on validation is below `0.10` and simple trading diagnostics are not positive after validation-role evaluation, return `STOP`.
- If `entry_log_ratio` remains weak but amplitude trace is materially stronger and consistent, return `PIVOT`.
- If a candidate exceeds `0.10` on validation, passes the simple trading diagnostics on validation-role evaluation, and has enough trades by `sample_size_gate`, return `CONTINUE` as a proposal for a later frozen `locked_test` plan.

## File Structure

**Create**

- `ML/baseline/benchmark_entry_based_next_open_closeout.py` - closeout runner that imports and reuses the corrected selection-ablation runner.
- `tests/test_entry_based_next_open_closeout.py` - focused tests for shortlist scope, `H24` target handling, entry smoke-check, simple trading diagnostics, and verdict rules.
- `docs/reports/2026-07-04-entry-based-next-open-closeout.md` - canonical report after execution.

**Modify**

- `docs/ML/benchmark_entry_based_next_open_closeout.py.md` - module documentation for the new runner.
- `CHANGELOG.md` - stage completion entry after execution.
- `CONTEXT_HANDOFF.md` - next-session summary after execution.
- `MODULE_INDEX.md` - add new runner and test documentation entry if required by current index conventions.
- `docs/tests/tests.md` - add new focused test command.
- `wiki/research/fractal-stop-research.md`, `wiki/index.md`, `wiki/log.md`, `wiki/REPO_integrity.md` - update through wiki tooling after report is final.

**Generated**

- `ML/reports/entry_based_next_open_closeout.json`
- `ML/reports/entry_based_next_open_closeout_metrics.csv`
- `ML/reports/entry_based_next_open_closeout_rows.csv`
- `ML/reports/entry_based_next_open_closeout_scale_audit.csv`

**Read Before Implementation**

- `docs/methodology/README.md`
- `docs/methodology/03-feature-contract-leakage.md`
- `docs/methodology/05-eda-data-quality.md`
- `docs/methodology/06-temporal-split.md`
- `docs/methodology/08-model-development.md`
- `docs/methodology/09-validation-freeze.md`
- `docs/methodology/12-backtest-costs.md`
- `docs/methodology/16-reporting-audit.md`
- `docs/reports/2026-07-02-next-open-entry-updn-foundation.md`
- `docs/reports/2026-07-03-fractal-selection-ablation-entry-based-target.md`
- `ML/baseline/benchmark_entry_based_updn_fractal_selection_ablation.py`
- `tests/test_entry_based_updn_fractal_selection_ablation.py`

---

### Task 1: Create Closeout Runner Scope

**Files:**
- Create: `ML/baseline/benchmark_entry_based_next_open_closeout.py`
- Create: `tests/test_entry_based_next_open_closeout.py`

**Interfaces:**
- Produces `SHORTLIST_REPRESENTATIONS: tuple[str, ...]`.
- Produces `CLOSEOUT_HORIZONS: tuple[str, ...]`.
- Produces `SPLIT_POLICY: dict[str, object]`.
- Produces `build_closeout_arg_parser() -> argparse.ArgumentParser`.
- Produces `enumerate_closeout_jobs(...) -> list[dict]`.

- [ ] **Step 1: Write the failing scope test**

```python
import ML.baseline.benchmark_entry_based_next_open_closeout as runner


def test_closeout_scope_is_frozen_and_excludes_cross_pair_validation():
    assert runner.SHORTLIST_REPRESENTATIONS == (
        "all100",
        "corridor_5atr",
        "nearest_k20",
        "nearest_k60",
        "nearest_k80",
    )
    assert runner.CLOSEOUT_HORIZONS == ("3", "6", "12", "24")
    assert runner.CROSS_PAIR_VALIDATION == "excluded_by_plan"


def test_closeout_jobs_use_shortlist_models_and_single_seed():
    jobs = runner.enumerate_closeout_jobs()
    assert len(jobs) == 5 * 4 * 1
    assert {job["representation_key"] for job in jobs} == set(runner.SHORTLIST_REPRESENTATIONS)
    assert {job["model_key"] for job in jobs} == {
        "xgboost_depth3",
        "xgboost_depth5",
        "hist_gradient_boosting",
        "ridge",
    }
    assert {job["seed"] for job in jobs} == {42}


def test_closeout_split_policy_uses_large_validation_and_no_locked_test():
    assert runner.SPLIT_POLICY == {
        "train": {"source": ["train_core"], "calendar": "<=2020"},
        "validation": {"source": ["val_stop", "diagnostic_holdout"], "calendar": "2021-2025"},
        "locked_test": {"source": [], "calendar": "not_opened"},
        "low_n_disclosure": {"source": ["low_n_disclosure"], "calendar": "2026", "selection_use": "forbidden"},
    }
```

- [ ] **Step 2: Run the failing test**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_next_open_closeout.py::test_closeout_scope_is_frozen_and_excludes_cross_pair_validation -q
```

Expected: FAIL with `ModuleNotFoundError` or missing attribute.

- [ ] **Step 3: Add minimal runner scope**

```python
from __future__ import annotations

import argparse
from pathlib import Path

from ML.baseline import benchmark_entry_based_updn_fractal_selection_ablation as base


REPORT_JSON_PATH = Path("ML/reports/entry_based_next_open_closeout.json")
REPORT_METRICS_PATH = Path("ML/reports/entry_based_next_open_closeout_metrics.csv")
REPORT_ROWS_PATH = Path("ML/reports/entry_based_next_open_closeout_rows.csv")

SHORTLIST_REPRESENTATIONS = (
    "all100",
    "corridor_5atr",
    "nearest_k20",
    "nearest_k60",
    "nearest_k80",
)
CLOSEOUT_HORIZONS = ("3", "6", "12", "24")
CROSS_PAIR_VALIDATION = "excluded_by_plan"
SPLIT_POLICY = {
    "train": {"source": ["train_core"], "calendar": "<=2020"},
    "validation": {"source": ["val_stop", "diagnostic_holdout"], "calendar": "2021-2025"},
    "locked_test": {"source": [], "calendar": "not_opened"},
    "low_n_disclosure": {"source": ["low_n_disclosure"], "calendar": "2026", "selection_use": "forbidden"},
}
CLOSEOUT_MODEL_KEYS = (
    "xgboost_depth3",
    "xgboost_depth5",
    "hist_gradient_boosting",
    "ridge",
)
CLOSEOUT_SEEDS = (42,)


def build_closeout_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Entry-based next-open closeout runner")
    parser.add_argument("--entry-based-next-open-closeout", action="store_true")
    parser.add_argument("--resume", dest="resume", action="store_true", default=True)
    parser.add_argument("--no-resume", dest="resume", action="store_false")
    return parser


def enumerate_closeout_jobs(
    representation_keys: tuple[str, ...] = SHORTLIST_REPRESENTATIONS,
    model_keys: tuple[str, ...] = CLOSEOUT_MODEL_KEYS,
    seeds: tuple[int, ...] = CLOSEOUT_SEEDS,
) -> list[dict]:
    return [
        {"representation_key": representation_key, "model_key": model_key, "seed": seed}
        for representation_key in representation_keys
        for model_key in model_keys
        for seed in seeds
    ]
```

- [ ] **Step 4: Run the scope tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_next_open_closeout.py -q
```

Expected: PASS for the new scope tests.

- [ ] **Step 5: Checkpoint**

```bash
git status --short
```

Expected: only files related to this task are changed.

---

### Task 2: Add Entry-Based Smoke Check

**Files:**
- Modify: `ML/baseline/benchmark_entry_based_next_open_closeout.py`
- Modify: `tests/test_entry_based_next_open_closeout.py`

**Interfaces:**
- Produces `run_entry_based_smoke_check(splits: dict[str, pandas.DataFrame]) -> dict`.
- Consumes `base.validate_entry_based_target_contract`.

- [ ] **Step 1: Write the failing smoke-check tests**

```python
import pandas as pd


def _minimal_entry_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "time": ["2021.01.01 00:00", "2021.01.01 01:00"],
            "entry_time": ["2021.01.01 01:00", "2021.01.01 02:00"],
            "entry_open": [100.0, 101.0],
            "entry_up_3": [0.5, 0.6],
            "entry_dn_3": [0.4, 0.5],
            "entry_log_ratio_3": [0.01, -0.01],
            "entry_up_6": [0.7, 0.8],
            "entry_dn_6": [0.6, 0.7],
            "entry_log_ratio_6": [0.02, -0.02],
            "entry_up_12": [0.9, 1.0],
            "entry_dn_12": [0.8, 0.9],
            "entry_log_ratio_12": [0.03, -0.03],
            "entry_up_24": [1.1, 1.2],
            "entry_dn_24": [1.0, 1.1],
            "entry_log_ratio_24": [0.04, -0.04],
        }
    )


def test_entry_based_smoke_check_passes_without_legacy_target_columns():
    splits = {"train": _minimal_entry_frame(), "validation": _minimal_entry_frame()}
    result = runner.run_entry_based_smoke_check(splits)
    assert result["status"] == "PASS"
    assert result["legacy_target_columns_required"] is False
    assert result["horizons"] == ["3", "6", "12", "24"]


def test_entry_based_smoke_check_fails_when_h24_target_is_missing():
    frame = _minimal_entry_frame().drop(columns=["entry_log_ratio_24"])
    result = runner.run_entry_based_smoke_check({"train": frame})
    assert result["status"] == "FAIL"
    assert "entry_log_ratio_24" in result["missing_columns"]["train"]
```

- [ ] **Step 2: Run the smoke-check tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_next_open_closeout.py::test_entry_based_smoke_check_passes_without_legacy_target_columns tests/test_entry_based_next_open_closeout.py::test_entry_based_smoke_check_fails_when_h24_target_is_missing -q
```

Expected: FAIL because `run_entry_based_smoke_check` is not implemented.

- [ ] **Step 3: Implement the smoke check**

```python
def _required_entry_target_columns() -> list[str]:
    columns: list[str] = []
    for horizon in CLOSEOUT_HORIZONS:
        columns.extend(
            [
                f"entry_up_{horizon}",
                f"entry_dn_{horizon}",
                f"entry_log_ratio_{horizon}",
            ]
        )
    return columns


def run_entry_based_smoke_check(splits: dict[str, "pd.DataFrame"]) -> dict:
    required = _required_entry_target_columns()
    missing_columns: dict[str, list[str]] = {}
    row_counts: dict[str, int] = {}
    for split_name, frame in splits.items():
        row_counts[split_name] = int(len(frame))
        missing = [column for column in required if column not in frame.columns]
        if missing:
            missing_columns[split_name] = missing

    return {
        "status": "FAIL" if missing_columns else "PASS",
        "legacy_target_columns_required": False,
        "horizons": list(CLOSEOUT_HORIZONS),
        "required_columns": required,
        "missing_columns": missing_columns,
        "row_counts": row_counts,
    }
```

- [ ] **Step 4: Run focused tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_next_open_closeout.py -q
```

Expected: PASS.

- [ ] **Step 5: Checkpoint**

```bash
git status --short
```

Expected: only files related to this task are changed.

---

### Task 3: Add H24 Targets And Serialized UpDn Full Features

**Files:**
- Modify: `ML/baseline/benchmark_entry_based_updn_fractal_selection_ablation.py`
- Modify: `ML/baseline/benchmark_entry_based_next_open_closeout.py`
- Modify: `tests/test_entry_based_next_open_closeout.py`

**Interfaces:**
- Produces `closeout_target_matrix(df: pandas.DataFrame) -> numpy.ndarray`.
- Produces `closeout_predictions_frame(preds: numpy.ndarray) -> pandas.DataFrame`.
- Produces `build_closeout_representation_features(df, profile_key) -> tuple[pandas.DataFrame, dict]`.
- Modifies base feature builder defaults carefully: old ablation default remains `3/6/12`; closeout can request serialized `3/6/12/24/48` Up/Dn fields.

- [ ] **Step 1: Write the failing feature and target tests**

```python
import numpy as np


def test_closeout_target_matrix_includes_h24():
    frame = _minimal_entry_frame()
    matrix = runner.closeout_target_matrix(frame)
    assert matrix.shape == (2, 12)


def test_closeout_features_include_serialized_h24_updn_but_not_top_level_targets():
    frame = _minimal_entry_frame()
    frame["ATR"] = 1.0
    frame["fractal0"] = "1:100:1:1:1:0:0:0:1:1:1:0.5:0.4:0.7:0.6:0.9:0.8:0.2:0.1:0.3:0.2:1:1"
    features, metadata = runner.build_closeout_representation_features(frame, "all100")
    serialized_h24 = [column for column in features.columns if "_up_24" in column or "_dn_24" in column]
    assert serialized_h24
    assert "entry_up_24" not in features.columns
    assert "entry_dn_24" not in features.columns
    assert "entry_log_ratio_24" not in features.columns
    assert metadata["target_horizons"] == ["3", "6", "12", "24"]
    assert metadata["feature_horizons"] == ["3", "6", "12", "24", "48"]


def test_closeout_features_add_live_safe_row_context_time():
    frame = _minimal_entry_frame()
    frame["ATR"] = 1.0
    frame["fractal0"] = "1:100:1:1:1:0:0:0:1:1:1:0.5:0.4:0.7:0.6:0.9:0.8:0.2:0.1:0.3:0.2:1:1"
    features, metadata = runner.build_closeout_representation_features(frame, "all100")
    assert {"row_hour_sin", "row_hour_cos", "row_dow_sin", "row_dow_cos"}.issubset(features.columns)
    assert "row_context_time" in metadata["feature_families"]
```

- [ ] **Step 2: Run the failing target tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_next_open_closeout.py::test_closeout_target_matrix_includes_h24 tests/test_entry_based_next_open_closeout.py::test_closeout_features_include_serialized_h24_updn_but_not_top_level_targets -q
```

Expected: FAIL because the closeout functions are missing.

- [ ] **Step 3: Add optional serialized Up/Dn horizon control to the base builder**

Modify `ML/baseline/benchmark_entry_based_updn_fractal_selection_ablation.py` without changing its default behavior:

```python
DEFAULT_SERIALIZED_UPDN_FEATURE_HORIZONS = ("3", "6", "12")
FULL_SERIALIZED_UPDN_FEATURE_HORIZONS = ("3", "6", "12", "24", "48")
```

Change the base representation interface to accept an optional horizon tuple:

```python
def build_representation_features(
    df: pd.DataFrame,
    profile_key: str,
    serialized_updn_horizons: tuple[str, ...] = DEFAULT_SERIALIZED_UPDN_FEATURE_HORIZONS,
) -> tuple[pd.DataFrame, dict]:
    ...
```

Replace the hardcoded drop behavior with allowlist behavior:

```python
def _filter_serialized_updn_horizon_columns(features: pd.DataFrame, allowed_horizons: tuple[str, ...]) -> pd.DataFrame:
    allowed_parts = tuple(f"_{side}_{horizon}" for horizon in allowed_horizons for side in ("up", "dn"))
    filtered_columns = []
    for column in features.columns:
        is_updn = any(f"_{side}_" in column for side in ("up", "dn"))
        if not is_updn or any(part in column for part in allowed_parts):
            filtered_columns.append(column)
    return features.loc[:, filtered_columns].copy()
```

The old 2026-07-03 runner must still call the function without the new argument and therefore keep `3/6/12` only. The new closeout runner is the only caller that requests `3/6/12/24/48`.

- [ ] **Step 4: Implement closeout target and feature wrappers**

Add these imports to `ML/baseline/benchmark_entry_based_next_open_closeout.py`:

```python
import numpy as np
import pandas as pd
```

```python
def closeout_target_matrix(df: "pd.DataFrame") -> "np.ndarray":
    columns: list[str] = []
    for horizon in CLOSEOUT_HORIZONS:
        columns.extend(
            [
                f"entry_up_{horizon}",
                f"entry_dn_{horizon}",
                f"entry_log_ratio_{horizon}",
            ]
        )
    return df[columns].to_numpy(dtype=float)


def closeout_predictions_frame(preds: "np.ndarray") -> "pd.DataFrame":
    columns: list[str] = []
    for horizon in CLOSEOUT_HORIZONS:
        columns.extend(
            [
                f"pred_entry_up_{horizon}",
                f"pred_entry_dn_{horizon}",
                f"pred_entry_log_ratio_{horizon}",
            ]
        )
    return pd.DataFrame(preds, columns=columns)


def _row_context_time_features(df: "pd.DataFrame") -> "pd.DataFrame":
    timestamps = pd.to_datetime(df["time"], errors="coerce")
    hour = timestamps.dt.hour.fillna(0).astype(float)
    dow = timestamps.dt.dayofweek.fillna(0).astype(float)
    return pd.DataFrame(
        {
            "row_hour_sin": np.sin(2.0 * np.pi * hour / 24.0),
            "row_hour_cos": np.cos(2.0 * np.pi * hour / 24.0),
            "row_dow_sin": np.sin(2.0 * np.pi * dow / 7.0),
            "row_dow_cos": np.cos(2.0 * np.pi * dow / 7.0),
        },
        index=df.index,
    )


def build_closeout_representation_features(df: "pd.DataFrame", profile_key: str) -> tuple["pd.DataFrame", dict]:
    features, metadata = base.build_representation_features(
        df,
        profile_key,
        serialized_updn_horizons=("3", "6", "12", "24", "48"),
    )
    features = pd.concat([features.reset_index(drop=True), _row_context_time_features(df).reset_index(drop=True)], axis=1)
    forbidden_top_level = [
        column
        for column in features.columns
        if column.startswith(("entry_up_", "entry_dn_", "entry_log_ratio_", "target_", "label_", "outcome_"))
    ]
    if forbidden_top_level:
        raise ValueError(f"Top-level target columns leaked into features: {forbidden_top_level[:10]}")
    metadata = dict(metadata)
    metadata["target_horizons"] = list(CLOSEOUT_HORIZONS)
    metadata["feature_horizons"] = ["3", "6", "12", "24", "48"]
    metadata["feature_families"] = sorted(set(metadata.get("feature_families", [])) | {"row_context_time", "updn_full"})
    return features, metadata
```

- [ ] **Step 5: Run focused tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_next_open_closeout.py -q
```

Expected: PASS.

- [ ] **Step 6: Checkpoint**

```bash
git status --short
```

Expected: only files related to this task are changed.

---

### Task 4: Add Feature Scale Audit And Normalization Contract

**Files:**
- Modify: `ML/baseline/benchmark_entry_based_next_open_closeout.py`
- Modify: `tests/test_entry_based_next_open_closeout.py`

**Interfaces:**
- Produces `build_normalization_contract() -> dict`.
- Produces `compute_feature_scale_audit(features_by_split: dict[str, pandas.DataFrame], feature_metadata: dict) -> dict`.
- Produces `assert_no_target_columns_in_normalization(features: pandas.DataFrame, contract: dict) -> None`.
- Produces `write_scale_audit_csv(scale_audit: dict, path: pathlib.Path) -> None`.

- [ ] **Step 1: Write the failing normalization contract tests**

```python
def test_normalization_contract_keeps_inputs_and_targets_separate():
    contract = runner.build_normalization_contract()
    assert contract["normalization_mode"] == "none_tree_raw"
    assert contract["scaler_fit_split"] == "train"
    assert contract["target_columns_forbidden_in_input_pools"] is True
    assert "updn_full" in contract["feature_groups"]
    assert contract["feature_groups"]["updn_full"]["source"] == "serialized_fractal_snapshot"


def test_normalization_contract_rejects_target_columns_in_feature_matrix():
    contract = runner.build_normalization_contract()
    features = pd.DataFrame(
        {
            "slot000_price_coord_atr": [0.0, 1.0],
            "entry_up_24": [1.0, 2.0],
        }
    )
    try:
        runner.assert_no_target_columns_in_normalization(features, contract)
    except ValueError as exc:
        assert "entry_up_24" in str(exc)
    else:
        raise AssertionError("target column was not rejected")


def test_feature_scale_audit_reports_distribution_and_dominance_flags():
    features_by_split = {
        "train": pd.DataFrame(
            {
                "slot000_price_coord_atr": [0.0, 1.0, 2.0, 3.0],
                "slot000_up_24": [0.1, 0.2, 0.3, 100.0],
                "row_hour_sin": [0.0, 0.5, -0.5, 0.0],
            }
        ),
        "validation": pd.DataFrame(
            {
                "slot000_price_coord_atr": [0.0, 1.0],
                "slot000_up_24": [0.2, 0.4],
                "row_hour_sin": [0.0, 1.0],
            }
        ),
    }
    audit = runner.compute_feature_scale_audit(features_by_split, {"profile_key": "all100"})
    assert audit["status"] in {"PASS", "WARNING"}
    assert "slot000_up_24" in audit["features"]
    assert "p99" in audit["features"]["slot000_up_24"]["train"]
    assert "dominance_checks" in audit
```

- [ ] **Step 2: Run the failing normalization tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_next_open_closeout.py::test_normalization_contract_keeps_inputs_and_targets_separate tests/test_entry_based_next_open_closeout.py::test_normalization_contract_rejects_target_columns_in_feature_matrix tests/test_entry_based_next_open_closeout.py::test_feature_scale_audit_reports_distribution_and_dominance_flags -q
```

Expected: FAIL because normalization audit functions are missing.

- [ ] **Step 3: Implement normalization contract**

Add this code to `ML/baseline/benchmark_entry_based_next_open_closeout.py`:

```python
TARGET_COLUMN_PREFIXES = (
    "entry_up_",
    "entry_dn_",
    "entry_log_ratio_",
    "target_",
    "label_",
    "outcome_",
    "ret_",
    "fav_",
    "adv_",
)


def build_normalization_contract() -> dict:
    return {
        "normalization_mode": "none_tree_raw",
        "reason": "Tree and linear diagnostic models receive the final numeric feature matrix directly; scale audit is still mandatory.",
        "scaler_fit_split": "train",
        "target_columns_forbidden_in_input_pools": True,
        "feature_groups": {
            "structure_fields": {"normalization": "as_produced", "source": "serialized_fractal_snapshot"},
            "shift_age": {"normalization": "as_produced_or_log", "source": "serialized_fractal_snapshot"},
            "atr_ratio": {"normalization": "log_ratio", "source": "row_ATR_and_fractal_atr"},
            "price_coord_atr": {"normalization": "atr_scaled", "source": "row_ATR_and_fractal_price"},
            "distance_atr": {"normalization": "atr_scaled", "source": "row_ATR_and_fractal_price"},
            "updn_full": {"normalization": "as_produced", "source": "serialized_fractal_snapshot"},
            "row_context_time": {"normalization": "sin_cos", "source": "row_time"},
        },
        "target_groups": {
            "entry_based_updn": {
                "columns": [f"entry_{kind}_{horizon}" for horizon in CLOSEOUT_HORIZONS for kind in ("up", "dn")]
                + [f"entry_log_ratio_{horizon}" for horizon in CLOSEOUT_HORIZONS],
                "normalization": "target_only_not_input",
            }
        },
    }


def assert_no_target_columns_in_normalization(features: "pd.DataFrame", contract: dict) -> None:
    offenders = [column for column in features.columns if column.startswith(TARGET_COLUMN_PREFIXES)]
    if offenders:
        raise ValueError(f"Target/label columns are forbidden in input normalization pools: {offenders[:20]}")
    if not contract["target_columns_forbidden_in_input_pools"]:
        raise ValueError("normalization contract must forbid target columns in input pools")
```

- [ ] **Step 4: Implement scale audit**

Add this code to `ML/baseline/benchmark_entry_based_next_open_closeout.py`:

```python
def _feature_scale_stats(series: "pd.Series") -> dict:
    numeric = pd.to_numeric(series, errors="coerce").replace([np.inf, -np.inf], np.nan)
    clean = numeric.dropna()
    if clean.empty:
        return {
            "n": int(len(series)),
            "nan_rate": float(numeric.isna().mean()),
            "zero_rate": None,
            "unique_count": 0,
            "min": None,
            "p1": None,
            "p50": None,
            "p99": None,
            "max": None,
            "std": None,
        }
    return {
        "n": int(len(series)),
        "nan_rate": float(numeric.isna().mean()),
        "zero_rate": float((clean == 0.0).mean()),
        "unique_count": int(clean.nunique(dropna=True)),
        "min": float(clean.min()),
        "p1": float(clean.quantile(0.01)),
        "p50": float(clean.quantile(0.50)),
        "p99": float(clean.quantile(0.99)),
        "max": float(clean.max()),
        "std": float(clean.std(ddof=0)),
    }


def _feature_group_for_column(column: str) -> str:
    if "_up_" in column or "_dn_" in column:
        return "updn_full"
    if "price_coord_atr" in column or "distance_atr" in column:
        return "price_coord_atr"
    if column.startswith("row_"):
        return "row_context_time"
    if "shift" in column:
        return "shift_age"
    if "atr" in column.lower():
        return "atr_ratio"
    return "structure_fields"


def compute_feature_scale_audit(features_by_split: dict[str, "pd.DataFrame"], feature_metadata: dict) -> dict:
    contract = build_normalization_contract()
    for features in features_by_split.values():
        assert_no_target_columns_in_normalization(features, contract)

    feature_stats: dict[str, dict] = {}
    flags: list[dict] = []
    for column in features_by_split["train"].columns:
        feature_stats[column] = {}
        for split_name, features in features_by_split.items():
            stats = _feature_scale_stats(features[column])
            feature_stats[column][split_name] = stats
            if stats["unique_count"] <= 1:
                flags.append({"feature": column, "split": split_name, "flag": "NEAR_CONSTANT"})
            if stats["nan_rate"] is not None and stats["nan_rate"] > 0.05:
                flags.append({"feature": column, "split": split_name, "flag": "NAN_GT5"})

    dominance_checks: dict[str, dict] = {}
    grouped: dict[str, list[float]] = {}
    for column, stats_by_split in feature_stats.items():
        group = _feature_group_for_column(column)
        p99 = stats_by_split["train"]["p99"]
        if p99 is not None:
            grouped.setdefault(group, []).append(abs(float(p99)))
    for group, p99_values in grouped.items():
        max_p99 = max(p99_values) if p99_values else 0.0
        median_p99 = float(np.median(p99_values)) if p99_values else 0.0
        ratio = None if median_p99 == 0.0 else max_p99 / median_p99
        dominance_checks[group] = {
            "max_abs_p99": max_p99,
            "median_abs_p99": median_p99,
            "max_to_median_p99": ratio,
            "status": "WARNING" if ratio is not None and ratio > 100.0 else "PASS",
        }

    status = "WARNING" if flags or any(item["status"] == "WARNING" for item in dominance_checks.values()) else "PASS"
    return {
        "status": status,
        "normalization_contract": contract,
        "profile_key": feature_metadata.get("profile_key"),
        "features": feature_stats,
        "flags": flags,
        "dominance_checks": dominance_checks,
    }


def write_scale_audit_csv(scale_audit: dict, path: "Path") -> None:
    rows = []
    for feature_name, stats_by_split in scale_audit["features"].items():
        group = _feature_group_for_column(feature_name)
        for split_name, stats in stats_by_split.items():
            rows.append({"feature": feature_name, "group": group, "split": split_name, **stats})
    pd.DataFrame(rows).to_csv(path, sep=";", index=False)
```

- [ ] **Step 5: Wire audit into runner before model jobs**

Implementation requirements:

- Build final features for `train`, `validation`, and `low_n_disclosure` before model fitting.
- Run `compute_feature_scale_audit(...)` for every shortlist representation.
- Save the combined audit in JSON under `scale_audit`.
- Write `ML/reports/entry_based_next_open_closeout_scale_audit.csv`.
- If any scale audit returns `ERROR`, stop before model fit with `status = FEATURE_SCALE_AUDIT_FAILED`.
- If status is `WARNING`, continue but report warnings in JSON and final report.

- [ ] **Step 6: Run focused tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_next_open_closeout.py -q
```

Expected: PASS.

- [ ] **Step 7: Checkpoint**

```bash
git status --short
```

Expected: only files related to this task are changed.

---

### Task 5: Add Direction, Amplitude, And Simple Trading Diagnostics

**Files:**
- Modify: `ML/baseline/benchmark_entry_based_next_open_closeout.py`
- Modify: `tests/test_entry_based_next_open_closeout.py`

**Interfaces:**
- Produces `compute_closeout_split_metrics(y_true, predictions, frame) -> dict`.
- Produces `compute_simple_trade_metrics(frame, predictions, horizon: str) -> dict`.

- [ ] **Step 1: Write the failing metric tests**

```python
def test_simple_trade_metrics_use_prediction_sign_as_side():
    frame = _minimal_entry_frame()
    predictions = pd.DataFrame(
        {
            "pred_entry_log_ratio_3": [0.5, -0.5],
            "pred_entry_up_3": [1.0, 1.0],
            "pred_entry_dn_3": [1.0, 1.0],
        }
    )
    result = runner.compute_simple_trade_metrics(frame, predictions, horizon="3")
    assert result["trade_count"] == 2
    assert result["long_count"] == 1
    assert result["short_count"] == 1
    assert result["mean_signed_log_ratio"] == 0.01


def test_closeout_split_metrics_contains_direction_amplitude_and_trade_blocks():
    frame = _minimal_entry_frame()
    predictions = pd.DataFrame(
        {
            f"pred_entry_up_{h}": [0.5, 0.6] for h in runner.CLOSEOUT_HORIZONS
        }
    )
    for h in runner.CLOSEOUT_HORIZONS:
        predictions[f"pred_entry_dn_{h}"] = [0.4, 0.5]
        predictions[f"pred_entry_log_ratio_{h}"] = [0.1, -0.1]
    metrics = runner.compute_closeout_split_metrics(frame, predictions)
    assert "entry_log_ratio_24" in metrics
    assert "entry_up_24" in metrics
    assert "simple_trade_24" in metrics
```

- [ ] **Step 2: Run the failing metric tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_next_open_closeout.py::test_simple_trade_metrics_use_prediction_sign_as_side tests/test_entry_based_next_open_closeout.py::test_closeout_split_metrics_contains_direction_amplitude_and_trade_blocks -q
```

Expected: FAIL because metric functions are missing.

- [ ] **Step 3: Implement simple trading diagnostics**

```python
def _safe_mean(values: "np.ndarray") -> float | None:
    clean = values[np.isfinite(values)]
    if len(clean) == 0:
        return None
    return float(np.mean(clean))


def compute_simple_trade_metrics(frame: "pd.DataFrame", predictions: "pd.DataFrame", horizon: str) -> dict:
    pred = predictions[f"pred_entry_log_ratio_{horizon}"].to_numpy(dtype=float)
    actual = frame[f"entry_log_ratio_{horizon}"].to_numpy(dtype=float)
    side = np.where(pred >= 0.0, 1.0, -1.0)
    signed = side * actual
    wins = signed > 0.0
    return {
        "trade_count": int(len(signed)),
        "long_count": int(np.sum(side > 0.0)),
        "short_count": int(np.sum(side < 0.0)),
        "mean_signed_log_ratio": _safe_mean(signed),
        "median_signed_log_ratio": float(np.median(signed)) if len(signed) else None,
        "win_rate": float(np.mean(wins)) if len(wins) else None,
        "gross_positive_sum": float(np.sum(signed[signed > 0.0])) if len(signed) else 0.0,
        "gross_negative_sum": float(np.sum(signed[signed < 0.0])) if len(signed) else 0.0,
    }


def compute_closeout_split_metrics(frame: "pd.DataFrame", predictions: "pd.DataFrame") -> dict:
    metrics: dict[str, dict] = {}
    for horizon in CLOSEOUT_HORIZONS:
        for target_name in ("entry_log_ratio", "entry_up", "entry_dn"):
            actual = frame[f"{target_name}_{horizon}"].to_numpy(dtype=float)
            pred = predictions[f"pred_{target_name}_{horizon}"].to_numpy(dtype=float)
            metrics[f"{target_name}_{horizon}"] = {"spearman": base._corr_or_none(actual, pred)}
        metrics[f"simple_trade_{horizon}"] = compute_simple_trade_metrics(frame, predictions, horizon)
    return metrics
```

- [ ] **Step 4: Run focused tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_next_open_closeout.py -q
```

Expected: PASS.

- [ ] **Step 5: Checkpoint**

```bash
git status --short
```

Expected: only files related to this task are changed.

---

### Task 6: Implement Closeout Runner And Summary Verdict

**Files:**
- Modify: `ML/baseline/benchmark_entry_based_next_open_closeout.py`
- Modify: `tests/test_entry_based_next_open_closeout.py`

**Interfaces:**
- Produces `evaluate_closeout_job(job, splits, report) -> dict`.
- Produces `summarize_closeout_results(report: dict) -> dict`.
- Produces `decide_closeout_verdict(summary: dict) -> str`.
- Produces `run_closeout_benchmark(args, report_path, metrics_path, rows_path) -> dict`.

- [ ] **Step 1: Write the failing summary verdict tests**

```python
def test_closeout_verdict_stop_when_direction_and_trade_fail():
    summary = {
        "best_directional": {"selection_score": 0.079, "eval_score": 0.009},
        "best_amplitude": {"selection_score": 0.16, "eval_score": 0.01},
        "best_trade": {"select_mean": -0.001, "eval_mean": -0.001},
        "validation_roles_combined": False,
    }
    assert runner.decide_closeout_verdict(summary) == "STOP"


def test_closeout_verdict_pivot_when_amplitude_survives_but_direction_does_not():
    summary = {
        "best_directional": {"selection_score": 0.07, "eval_score": 0.01},
        "best_amplitude": {"selection_score": 0.18, "eval_score": 0.12},
        "best_trade": {"select_mean": 0.0, "eval_mean": -0.001},
        "validation_roles_combined": False,
    }
    assert runner.decide_closeout_verdict(summary) == "PIVOT"


def test_closeout_verdict_continue_requires_direction_and_trade_eval():
    summary = {
        "best_directional": {"selection_score": 0.12, "eval_score": 0.04},
        "best_amplitude": {"selection_score": 0.18, "eval_score": 0.12},
        "best_trade": {"select_mean": 0.002, "eval_mean": 0.001},
        "validation_roles_combined": False,
    }
    assert runner.decide_closeout_verdict(summary) == "CONTINUE"


def test_closeout_verdict_cannot_continue_when_validation_roles_are_combined():
    summary = {
        "best_directional": {"selection_score": 0.12, "eval_score": 0.04},
        "best_amplitude": {"selection_score": 0.18, "eval_score": 0.12},
        "best_trade": {"select_mean": 0.002, "eval_mean": 0.001},
        "validation_roles_combined": True,
    }
    assert runner.decide_closeout_verdict(summary) == "PIVOT"
```

- [ ] **Step 2: Run the failing summary tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_next_open_closeout.py::test_closeout_verdict_stop_when_direction_and_trade_fail tests/test_entry_based_next_open_closeout.py::test_closeout_verdict_pivot_when_amplitude_survives_but_direction_does_not tests/test_entry_based_next_open_closeout.py::test_closeout_verdict_continue_requires_direction_and_trade_eval tests/test_entry_based_next_open_closeout.py::test_closeout_verdict_cannot_continue_when_validation_roles_are_combined -q
```

Expected: FAIL because verdict logic is missing.

- [ ] **Step 3: Implement verdict logic**

```python
DIRECTIONAL_SCORE_GATE = 0.10
VALIDATION_EVAL_NONZERO_GATE = 0.02
AMPLITUDE_SCORE_GATE = 0.15
TRADE_MEAN_GATE = 0.0


def decide_closeout_verdict(summary: dict) -> str:
    direction = summary["best_directional"]
    amplitude = summary["best_amplitude"]
    trade = summary["best_trade"]

    direction_survives = (
        direction["selection_score"] >= DIRECTIONAL_SCORE_GATE
        and direction["eval_score"] >= VALIDATION_EVAL_NONZERO_GATE
    )
    trade_survives = (
        trade["select_mean"] is not None
        and trade["eval_mean"] is not None
        and trade["select_mean"] > TRADE_MEAN_GATE
        and trade["eval_mean"] > TRADE_MEAN_GATE
    )
    amplitude_survives = (
        amplitude["selection_score"] >= AMPLITUDE_SCORE_GATE
        and amplitude["eval_score"] >= VALIDATION_EVAL_NONZERO_GATE
    )

    if direction_survives and trade_survives and not summary["validation_roles_combined"]:
        return "CONTINUE"
    if amplitude_survives:
        return "PIVOT"
    return "STOP"
```

- [ ] **Step 4: Implement runner by reusing base runtime contract**

Implementation requirements:

- Use `base.load_or_init_report`.
- Use `base.load_entry_based_splits(target_mode="rebuilt")`.
- Convert the old loaded split names to the new methodology roles:
  - old `train_core` -> `train`;
  - old `val_stop` + old `diagnostic_holdout` -> one large `validation`;
  - old `low_n_disclosure` -> `low_n_disclosure`.
- If a validation-role split is implemented, derive `val_stop`/`val_select`/`val_eval` only inside `validation` before looking at metrics; otherwise set `validation_roles_combined = True`.
- Run `run_entry_based_smoke_check` before model jobs.
- Run `base.run_all_preflight_with_progress` only for `SHORTLIST_REPRESENTATIONS`.
- Run `base.run_distribution_audit_with_progress` only for `SHORTLIST_REPRESENTATIONS`.
- Save JSON after every completed job.
- Write separate metrics and rows CSV.
- Preserve heartbeat messages from the base runner style.

- [ ] **Step 5: Run focused tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_next_open_closeout.py -q
```

Expected: PASS.

- [ ] **Step 6: Checkpoint**

```bash
git status --short
```

Expected: only files related to this task are changed.

---

### Task 7: Execute Clean Closeout Run

**Files:**
- Generate: `ML/reports/entry_based_next_open_closeout.json`
- Generate: `ML/reports/entry_based_next_open_closeout_metrics.csv`
- Generate: `ML/reports/entry_based_next_open_closeout_rows.csv`
- Generate: `ML/reports/entry_based_next_open_closeout_scale_audit.csv`

**Interfaces:**
- Consumes `run_closeout_benchmark`.
- Produces complete closeout artifacts.

- [ ] **Step 1: Run focused tests before the long run**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_next_open_closeout.py -q
```

Expected: all tests PASS.

- [ ] **Step 2: Execute clean runner**

Run:

```bash
./.venv/bin/python ML/baseline/benchmark_entry_based_next_open_closeout.py --entry-based-next-open-closeout --no-resume
```

Expected:

- `progress.done_runs = 20`
- `progress.total_runs = 20`
- `entry_based_smoke_check.status = PASS`
- `split_policy.train` and `split_policy.validation` are recorded
- `summary.validation_roles_combined` is recorded
- `scale_audit.status` is `PASS` or `WARNING`
- `representation_preflight.status` is recorded
- `distribution_audit.status` is recorded
- `summary.verdict` is one of `STOP`, `PIVOT`, `CONTINUE`

- [ ] **Step 3: Inspect generated JSON**

Run:

```bash
./.venv/bin/python -m json.tool ML/reports/entry_based_next_open_closeout.json >/tmp/entry_based_next_open_closeout.pretty.json
```

Expected: command exits with status `0`.

- [ ] **Step 4: Verify CSV artifact shape**

Run:

```bash
./.venv/bin/python - <<'PY'
import pandas as pd
metrics = pd.read_csv("ML/reports/entry_based_next_open_closeout_metrics.csv", sep=";")
rows = pd.read_csv("ML/reports/entry_based_next_open_closeout_rows.csv", sep=";")
scale = pd.read_csv("ML/reports/entry_based_next_open_closeout_scale_audit.csv", sep=";")
print({"metrics_rows": len(metrics), "rows_rows": len(rows), "scale_rows": len(scale)})
assert len(metrics) > 0
assert len(rows) > 0
assert len(scale) > 0
PY
```

Expected: prints positive row counts and exits with status `0`.

- [ ] **Step 5: Checkpoint**

```bash
git status --short
```

Expected: generated closeout JSON/CSV files are present. Do not commit unless the user explicitly asks.

---

### Task 8: Write Report And Sync Documentation

**Files:**
- Create: `docs/reports/2026-07-04-entry-based-next-open-closeout.md`
- Create: `docs/ML/benchmark_entry_based_next_open_closeout.py.md`
- Modify: `CHANGELOG.md`
- Modify: `CONTEXT_HANDOFF.md`
- Modify: `MODULE_INDEX.md`
- Modify: `docs/tests/tests.md`
- Modify: `wiki/research/fractal-stop-research.md`
- Modify: `wiki/index.md`
- Modify: `wiki/log.md`
- Modify: `wiki/REPO_integrity.md`

**Interfaces:**
- Consumes closeout JSON/CSV.
- Produces final closeout verdict and next-step recommendation.

- [ ] **Step 1: Write report from artifacts**

The report must include these sections:

- `Context`
- `What Was Tested`
- `Search Width Disclosure`
- `Entry-Based Smoke Check`
- `Feature Contract`
- `Scale Audit And Normalization Contract`
- `Split Policy`
- `Best Directional Results`
- `Direction Versus Amplitude`
- `Simple Trading Diagnostic`
- `Validation Role Check`
- `2026 Low-N Disclosure`
- `Verdict: STOP/PIVOT/CONTINUE`
- `Limitations`
- `Next Step`

- [ ] **Step 2: Add module documentation**

Document:

- command line usage;
- input artifacts;
- output artifacts;
- shortlist scope;
- why `EURUSD` is excluded from this plan;
- why `locked_test` is not opened in this plan;
- normalization mode, scale audit CSV, and target/input normalization separation;
- how verdicts are decided.

- [ ] **Step 3: Update project docs**

Update:

- `CHANGELOG.md` with a short stage entry;
- `CONTEXT_HANDOFF.md` with current verdict and next file to read;
- `MODULE_INDEX.md` if the repository index requires every new runner/test to be listed;
- `docs/tests/tests.md` with the new focused test command.

- [ ] **Step 4: Update wiki**

Run:

```bash
./.venv/bin/python wiki/wiki.py generate
./.venv/bin/python wiki/wiki.py status
```

Expected:

- `wiki/wiki.py status` reports no gaps.

- [ ] **Step 5: Checkpoint**

```bash
git status --short
```

Expected: report, docs, and wiki changes are visible. Do not commit unless the user explicitly asks or this is run through `stage-reporting`.

---

### Task 9: Final Verification

**Files:**
- Read: all files changed by Tasks 1-8.

**Interfaces:**
- Produces final verification evidence.

- [ ] **Step 1: Run focused tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_next_open_closeout.py -q
```

Expected: all tests PASS.

- [ ] **Step 2: Run full test suite**

Run:

```bash
./.venv/bin/python -m pytest tests/ -q
```

Expected: all tests PASS.

- [ ] **Step 3: Run formatting whitespace check**

Run:

```bash
git diff --check
```

Expected: no output.

- [ ] **Step 4: Verify wiki status**

Run:

```bash
./.venv/bin/python wiki/wiki.py status
```

Expected: `Wiki is up to date. No gaps found.`

- [ ] **Step 5: Verify final JSON verdict is present**

Run:

```bash
./.venv/bin/python - <<'PY'
import json
from pathlib import Path
path = Path("ML/reports/entry_based_next_open_closeout.json")
report = json.loads(path.read_text(encoding="utf-8"))
assert report["summary"]["verdict"] in {"STOP", "PIVOT", "CONTINUE"}
assert report["entry_based_smoke_check"]["status"] == "PASS"
assert report["scale_audit"]["status"] in {"PASS", "WARNING"}
assert report["progress"]["done_runs"] == report["progress"]["total_runs"] == 20
print(report["summary"]["verdict"])
PY
```

Expected: prints one of `STOP`, `PIVOT`, `CONTINUE`.

- [ ] **Step 6: Check final file state**

```bash
git status --short
```

If verification changed generated wiki or report files, leave them in the working tree and report them to the user. Do not create an empty commit.

## Self-Review

- Spec coverage: the plan covers the closeout scope, no `EURUSD`, entry smoke-check, updated `train`/large `validation` split policy, unopened `locked_test`, `H3/H6/H12/H24`, direction/amplitude separation, simple trading diagnostic, 2026 low-N disclosure, report, docs, wiki, and final verification.
- Placeholder scan: no unfinished placeholder text, deferred implementation, or unspecified runner path remains.
- Type consistency: public names used in later tasks are introduced before use.
- Scope check: this is one bounded closeout stage, not a broad search stage.
