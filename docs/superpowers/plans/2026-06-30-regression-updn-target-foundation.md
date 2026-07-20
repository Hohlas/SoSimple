# Regression Up/Dn Target Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Check whether top-level future `up_*/dn_*` targets can support a clean regression foundation without tying the target to fractal-stop breach or TP/SL touch.

**Architecture:** Add one bounded diagnostic runner in `ML/baseline/` that treats top-level `up_3..dn_48` columns as future regression targets, builds a small fixed feature/profile matrix, compares dummy, linear, tree, forest, and XGBoost baselines, and writes one JSON artifact plus one canonical report. The stage is target/label foundation only: it may identify promising target horizons and side logic, but it must not choose a production trading rule.

**Tech Stack:** Python 3.10+, pandas, numpy, scipy/sklearn metrics, XGBoost, pytest, existing `./.venv/bin/python`, existing `DATA/Nero_XAUUSD_*_labeled.csv`.

## Global Constraints

- Work on the current branch; do not use git worktree.
- Use `./.venv/bin/python` for all Python commands.
- New Python code must be covered by tests before implementation.
- Read only the methodology files needed for this stage: `00-research-management.md`, `03-feature-contract-leakage.md`, `04-labeling.md`, `05-eda-data-quality.md`, `06-temporal-split.md`, `07-baseline-first.md`, `08-model-development.md`, `11-robustness.md`, `16-reporting-audit.md`.
- Do not reopen H6/H12/ATR/TP/SL search from Stage 6.3.
- Do not add a broad new feature search. Use a fixed, small profile set.
- Do not use `diagnostic_holdout` (`2023-2025`) or `low_n_disclosure` (`2026`) for choosing target, profile, seed, threshold, side rule, or gate.
- Use `train_core=2004-2020`, `val_stop=2021-2022`, `diagnostic_holdout=2023-2025`, `low_n_disclosure=2026`.
- Treat top-level `up_3`, `dn_3`, `up_6`, `dn_6`, `up_12`, `dn_12`, `up_24`, `dn_24`, `up_48`, `dn_48` as labels only.
- Feature builders must not read top-level `up_*/dn_*` columns as inputs.
- Use explicit per-profile input allowlists. A denylist alone is not enough.
- Store `feature_source_contract` in JSON for every profile: source columns read, role, producer, transformation, availability, and live-safe verdict.
- `fractal*.up/dn` inside fractal strings are excluded from the main run. They may be used only in a later appendix run because Stage 5.1b already showed weak and uneven signal for this field family, and the foundation question should first answer whether ordinary live-safe features work without near-Up/Dn proxies.
- Result status is capped at `DIAGNOSTIC_ONLY`.
- Final closure of the stage must use `stage-reporting`: report, `CHANGELOG.md`, `CONTEXT_HANDOFF.md`, wiki ingest, and no `git push` unless explicitly requested.

---

## Fixed Research Contract

**Research level:** target foundation / diagnostic.

**Primary question:** can a model predict future favorable and adverse movement magnitudes (`up_h`, `dn_h`) well enough to justify a later, separately frozen trading formulation?

**Target columns:**

- `up_3`, `dn_3`
- `up_6`, `dn_6`
- `up_12`, `dn_12`
- `up_24`, `dn_24`
- `up_48`, `dn_48`

**Horizon policy:** all horizons `3/6/12/24/48` are evaluated as equal target-foundation candidates. H12 is reported as a legacy reference because old `regression_updn` and signal logic historically focused on `up_12/dn_12`, but H12 does not get a privileged gate.

**Foundation gate horizon rule:** a horizon can contribute to `research_gate_status=TARGET_FOUNDATION_PASSED` only if both `up_h` and `dn_h` pass model, normalized-error, seed, yearly, and bootstrap checks. If H12 passes alone, the report must say it is a legacy-H12 diagnostic finding, not proof that the whole Up/Dn target family is generally sound.

**Primary derived diagnostics:**

- Regression quality per target: MAE, RMSE, normalized MAE, Pearson r, Spearman rho.
- Normalized MAE variants: `mae_over_median_abs_target` and `mae_over_median_atr` where raw ATR is available.
- Baseline comparison: constant median, Ridge, shallow DecisionTreeRegressor, shallow RandomForestRegressor, and XGBoost.
- Direction proxy: `edge_h = up_h - dn_h`, reported as regression and sign-ranking diagnostic.
- Ratio proxy: `log_ratio_h = log1p(up_h) - log1p(dn_h)`, reported as diagnostic only.
- Year/side stability on `val_stop`, with `diagnostic_holdout` disclosure only.
- Block bootstrap confidence intervals for normalized MAE improvement and `edge_h` Spearman on `val_stop`.
- Calendar dependence: permutation importance share for `hour_*` and `dow_*`; if calendar share is above `30%`, report warns that the model may be a calendar filter.

**Fixed profiles:**

| Profile | Purpose |
|---|---|
| `constant_median` | non-ML target baseline |
| `clock_only` | row time baseline: `hour_sin`, `hour_cos`, `dow_sin`, `dow_cos` |
| `clock_shift` | row time + token `log1p(shift)` |
| `clock_shift_back` | compact structural baseline from Stage 5/6 |
| `clock_shift_back_impulse` | compact diagnostic profile because `impulse` was recurring but weaker than `back` |
| `structure_full` | bounded reference profile using Stage 5 structural fields |

**Out-of-main-run appendix profile:**

| Profile | Purpose |
|---|---|
| `updn_token_appendix` | optional separate appendix run using fractal-string Up/Dn fields + shift; cannot affect gate, target choice, or next-step selection |

**Model baselines per non-dummy profile:**

| Model key | Purpose |
|---|---|
| `constant_median` | dummy predictor fit on train target medians |
| `ridge` | linear baseline; shows whether signal is mostly linear |
| `decision_tree_depth3` | simple tree baseline; shows whether a tiny non-linear rule is enough |
| `random_forest_depth4` | constrained ensemble baseline; checks whether stability starts before XGBoost |
| `xgboost_depth3` | stronger tree model; may not pass foundation gate alone unless simpler baselines are also characterized |

**Primary gate for target foundation:**

- top-level target contract passes for all 10 targets;
- no forbidden feature use is detected;
- at least one horizon has both `up_h` and `dn_h` with XGBoost normalized MAE improvement over constant median of at least `5%`;
- the same horizon has both `up_h` and `dn_h` Spearman rho at least `0.15`;
- the same horizon has `edge_h` Spearman rho at least `0.10`;
- block bootstrap p05 for normalized MAE improvement is positive for both `up_h` and `dn_h`;
- block bootstrap p05 for `edge_h` Spearman is positive;
- no year in `val_stop` has a sign reversal for `edge_h` Spearman without being reported as `ROBUSTNESS_GATE_FAILED`;
- seed stability: at least `2/3` seeds pass the metric thresholds for the selected diagnostic horizon/profile;
- calendar feature importance share is reported; if it exceeds `30%`, the gate can pass only with `calendar_warning=true`.

**Status mapping:**

- `research_gate_status`: one of `TARGET_FOUNDATION_PASSED`, `TARGET_CONTRACT_FAILED`, `MODEL_GATE_FAILED`, `ROBUSTNESS_GATE_FAILED`.
- `artifact_status`: always `DIAGNOSTIC_ONLY` for this stage.
- `TARGET_FOUNDATION_PASSED`: contract and horizon-level target foundation gate pass.
- `TARGET_CONTRACT_FAILED`: missing, malformed, leaking, or unusable target contract.
- `MODEL_GATE_FAILED`: contract passes but model does not beat dummy/simple baselines on any horizon.
- `ROBUSTNESS_GATE_FAILED`: model metrics pass but seed/year/bootstrap stability fails.

## File Structure

**Create**

- `ML/baseline/benchmark_regression_updn_target_foundation.py` - bounded target foundation runner.
- `tests/test_regression_updn_target_foundation.py` - focused tests for target contract, feature denylist, profiles, metrics, runner, CLI.
- `docs/reports/2026-06-30-regression-updn-target-foundation.md` - canonical report after execution.

**Generated**

- `ML/reports/regression_updn_target_foundation.json`

**Modify after execution**

- `CHANGELOG.md`
- `CONTEXT_HANDOFF.md`
- `wiki/research/fractal-stop-research.md`, `wiki/index.md`, `wiki/log.md`, `wiki/REPO_integrity.md`

**Modify only with explicit module-docs request**

- `MODULE_INDEX.md`
- `docs/ML/benchmark_regression_updn_target_foundation.py.md`

**Read before implementation**

- `docs/DATA_FLOW.md`
- `docs/dataset_description.md`
- `docs/methodology/00-research-management.md`
- `docs/methodology/03-feature-contract-leakage.md`
- `docs/methodology/04-labeling.md`
- `docs/methodology/05-eda-data-quality.md`
- `docs/methodology/06-temporal-split.md`
- `docs/methodology/07-baseline-first.md`
- `docs/methodology/08-model-development.md`
- `docs/methodology/11-robustness.md`
- `docs/methodology/16-reporting-audit.md`
- `docs/reports/2026-06-25-stage5_1b-updn-field-ablation.md`
- `docs/reports/2026-06-30-stage6_2-range-w1-postmortem.md`
- `docs/reports/2026-06-30-stage6_3-h6-feature-parity-check.md`
- `ML/baseline/benchmark_stage5_transformer_breach.py`
- `ML/data_loader.py`

---

### Task 1: Target Contract And Skeleton

**Files:**
- Create: `ML/baseline/benchmark_regression_updn_target_foundation.py`
- Create: `tests/test_regression_updn_target_foundation.py`

**Interfaces:**
- Produces `UPDN_TARGET_COLUMNS: tuple[str, ...]`.
- Produces `RegressionUpDnConfig`.
- Produces `REGRESSION_UPDN_CONFIG`.
- Produces `REGRESSION_UPDN_JSON_REPORT_PATH`.
- Produces `updn_profile_keys() -> tuple[str, ...]`.
- Produces `updn_model_keys() -> tuple[str, ...]`.
- Produces `updn_feature_denylist() -> tuple[str, ...]`.
- Produces `updn_feature_source_contract(profile: str) -> dict`.
- Produces `updn_allowed_input_sources(profile: str) -> dict`.
- Produces `validate_updn_target_contract(splits: dict[str, pd.DataFrame]) -> dict`.

- [ ] **Step 1: Write failing contract tests**

Add tests:

```python
import pandas as pd

import ML.baseline.benchmark_regression_updn_target_foundation as updn


def test_updn_config_is_fixed_and_bounded():
    cfg = updn.REGRESSION_UPDN_CONFIG

    assert cfg.horizons == (3, 6, 12, 24, 48)
    assert cfg.legacy_reference_horizon == 12
    assert cfg.seeds == (42, 77, 123)
    assert cfg.primary_profile == "clock_shift_back"
    assert cfg.artifact_status == "DIAGNOSTIC_ONLY"
    assert cfg.train_max_year == 2020
    assert cfg.val_years == (2021, 2022)
    assert cfg.holdout_years == (2023, 2024, 2025)
    assert cfg.low_n_years == (2026,)


def test_updn_target_columns_are_top_level_labels_only():
    assert updn.UPDN_TARGET_COLUMNS == (
        "up_3", "dn_3", "up_6", "dn_6", "up_12", "dn_12",
        "up_24", "dn_24", "up_48", "dn_48",
    )


def test_updn_feature_denylist_blocks_top_level_targets_and_future_labels():
    denylist = set(updn.updn_feature_denylist())

    for col in updn.UPDN_TARGET_COLUMNS:
        assert col in denylist
    assert "predict" in denylist
    assert "signal" in denylist
    assert "stage6_definitive_tp_vs_sl_flag" in denylist
    assert "sell_stop_broken_H6_off05_flag" in denylist
    assert "buy_bars_to_breach_H6_off05" in denylist


def test_updn_baselines_include_dummy_linear_tree_forest_and_xgboost():
    assert updn.updn_model_keys() == (
        "constant_median",
        "ridge",
        "decision_tree_depth3",
        "random_forest_depth4",
        "xgboost_depth3",
    )


def test_updn_profiles_exclude_token_updn_from_main_run():
    assert "updn_token_diagnostic" not in updn.updn_profile_keys()
    assert "updn_token_appendix" not in updn.updn_profile_keys()


def test_feature_source_contract_is_allowlist_based():
    contract = updn.updn_feature_source_contract("clock_shift_back")

    assert contract["profile"] == "clock_shift_back"
    assert contract["input_selection"] == "allowlist"
    assert "top_level_updn_targets" not in contract["allowed_sources"]
    assert contract["forbidden_sources"]["top_level_updn_targets"] == list(updn.UPDN_TARGET_COLUMNS)


def test_validate_updn_target_contract_rejects_missing_target():
    splits = {
        "train_core": pd.DataFrame({"time": ["2021.01.01 00:00"], "up_3": [1.0]}),
        "val_stop": pd.DataFrame({"time": ["2021.01.01 00:00"], "up_3": [1.0]}),
    }

    result = updn.validate_updn_target_contract(splits)

    assert result["status"] == "FAIL"
    assert "dn_3" in result["missing_columns"]["train_core"]
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_regression_updn_target_foundation.py -q
```

Expected: fail because the module does not exist.

- [ ] **Step 3: Implement minimal module skeleton**

Create the module with constants, dataclass config, denylist, profile keys, model keys, source allowlists, feature source contract, and target contract validation. Do not implement training yet.

- [ ] **Step 4: Run focused tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_regression_updn_target_foundation.py -q
```

Expected: contract tests pass.

---

### Task 2: Split Loader And Feature Builders

**Files:**
- Modify: `ML/baseline/benchmark_regression_updn_target_foundation.py`
- Modify: `tests/test_regression_updn_target_foundation.py`

**Interfaces:**
- Produces `load_updn_labeled_splits() -> dict[str, pd.DataFrame]`.
- Produces `build_updn_features(df: pd.DataFrame, profile: str) -> np.ndarray`.
- Produces `updn_feature_names(profile: str) -> list[str]`.
- Produces `extract_updn_targets(df: pd.DataFrame) -> np.ndarray`.

- [ ] **Step 1: Add tests for split and feature contracts**

Add tests:

```python
import numpy as np
import pandas as pd
import pytest


def _tiny_labeled_frame():
    base = {
        "time": ["2021.01.04 10:00", "2021.01.04 11:00"],
        "ATR": [1.0, 2.0],
    }
    for col in updn.UPDN_TARGET_COLUMNS:
        base[col] = [0.1, 0.2]
    for i in range(100):
        base[f"fractal{i}"] = [
            "1:10:1:0.1:0.2:0:0:0:0.3:1:0.4:0.01:0.02:0.03:0.04:0.05:0.06:0.001:0.002:0.003:0.004:1.0:0",
            "2:11:-1:0.2:0.3:0:0:0:0.4:2:0.5:0.02:0.03:0.04:0.05:0.06:0.07:0.002:0.003:0.004:0.005:1.0:1",
        ]
    return pd.DataFrame(base)


def test_build_features_does_not_depend_on_top_level_updn_targets():
    df = _tiny_labeled_frame()
    baseline = updn.build_updn_features(df, "clock_shift_back")

    mutated = df.copy()
    for col in updn.UPDN_TARGET_COLUMNS:
        mutated[col] = 9999.0

    after = updn.build_updn_features(mutated, "clock_shift_back")
    np.testing.assert_allclose(after, baseline)


def test_extract_updn_targets_preserves_declared_order():
    df = _tiny_labeled_frame()

    y = updn.extract_updn_targets(df)

    assert y.shape == (2, 10)
    assert list(updn.UPDN_TARGET_COLUMNS) == [
        "up_3", "dn_3", "up_6", "dn_6", "up_12", "dn_12",
        "up_24", "dn_24", "up_48", "dn_48",
    ]


@pytest.mark.parametrize("profile", updn.updn_profile_keys())
def test_feature_names_match_feature_width(profile):
    df = _tiny_labeled_frame()

    X = updn.build_updn_features(df, profile)
    names = updn.updn_feature_names(profile)

    assert X.shape[1] == len(names)
    assert len(names) == len(set(names))


def test_feature_builder_records_real_columns_read():
    df = _tiny_labeled_frame()

    X, audit = updn.build_updn_features(df, "clock_shift_back", return_audit=True)

    assert X.shape[0] == len(df)
    assert audit["profile"] == "clock_shift_back"
    assert audit["input_selection"] == "allowlist"
    assert not set(updn.UPDN_TARGET_COLUMNS).intersection(audit["top_level_columns_read"])
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_regression_updn_target_foundation.py -q
```

Expected: fail on missing feature functions.

- [ ] **Step 3: Implement feature builders**

Reuse existing Stage 5 feature parsing helpers where practical:

- `clock_only`: row calendar only.
- `clock_shift`: row calendar + `log1p(shift)` for 100 fractals.
- `clock_shift_back`: Stage 5 compact baseline.
- `clock_shift_back_impulse`: Stage 5 compact diagnostic baseline.
- `structure_full`: Stage 5 structural reference.

Required implementation checks:

- raise `ValueError` on unknown profile;
- raise `ValueError` if top-level target columns appear in feature names;
- each builder returns or records `top_level_columns_read`, `fractal_fields_read`, and `row_fields_read`;
- each profile validates actual reads against `updn_allowed_input_sources(profile)`;
- JSON stores `feature_source_contract` and per-run `feature_read_audit`;
- coerce non-finite feature values to `0.0` only after recording counts in preflight.

Do not implement `updn_token_appendix` in the main runner. If the user later asks for the appendix, add a separate CLI flag and a separate JSON section that cannot affect `research_gate_status`.

- [ ] **Step 4: Run focused tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_regression_updn_target_foundation.py -q
```

Expected: split and feature tests pass.

---

### Task 3: Metrics, Baselines, And Gate

**Files:**
- Modify: `ML/baseline/benchmark_regression_updn_target_foundation.py`
- Modify: `tests/test_regression_updn_target_foundation.py`

**Interfaces:**
- Produces `updn_regression_metrics(y_true: np.ndarray, y_pred: np.ndarray, target_names: tuple[str, ...]) -> dict`.
- Produces `updn_constant_median_predict(train_y: np.ndarray, eval_n: int) -> np.ndarray`.
- Produces `evaluate_edge_diagnostics(y_true: np.ndarray, y_pred: np.ndarray) -> dict`.
- Produces `block_bootstrap_updn_metrics(y_true: np.ndarray, y_pred: np.ndarray, baseline_pred: np.ndarray, target_names: tuple[str, ...], block_size: int = 20, n_boot: int = 500, seed: int = 42) -> dict`.
- Produces `evaluate_updn_gate(summary: dict) -> dict`.

- [ ] **Step 1: Add tests for metrics and gate**

Add tests:

```python
import numpy as np


def test_constant_median_predict_uses_train_only_values():
    train_y = np.array([[1.0, 4.0], [3.0, 8.0], [5.0, 12.0]])

    pred = updn.updn_constant_median_predict(train_y, eval_n=2)

    np.testing.assert_allclose(pred, np.array([[3.0, 8.0], [3.0, 8.0]]))


def test_regression_metrics_include_primary_targets_and_improvement():
    y_true = np.array([[1.0, 2.0], [2.0, 1.0], [3.0, 0.5]])
    y_pred = np.array([[1.1, 1.9], [2.2, 1.1], [2.8, 0.6]])

    metrics = updn.updn_regression_metrics(
        y_true,
        y_pred,
        ("up_12", "dn_12"),
        atr=np.array([1.0, 1.0, 1.0]),
        baseline_pred=np.array([[2.0, 1.0], [2.0, 1.0], [2.0, 1.0]]),
    )

    assert "up_12" in metrics["targets"]
    assert "dn_12" in metrics["targets"]
    assert metrics["targets"]["up_12"]["mae"] >= 0.0
    assert metrics["targets"]["up_12"]["normalized_mae_over_median_abs_target"] >= 0.0
    assert metrics["targets"]["up_12"]["normalized_mae_over_median_atr"] >= 0.0
    assert "mae_improvement_vs_constant" in metrics["targets"]["up_12"]
    assert metrics["targets"]["up_12"]["spearman"] is not None


def test_edge_diagnostics_reports_up_minus_dn_for_each_horizon():
    y_true = np.array([[2.0, 1.0], [1.0, 3.0], [4.0, 1.0]])
    y_pred = np.array([[1.8, 1.2], [1.1, 2.8], [3.5, 1.2]])

    result = updn.evaluate_edge_diagnostics(
        y_true,
        y_pred,
        target_names=("up_12", "dn_12"),
    )

    assert result["edge_12"]["spearman"] is not None
    assert result["edge_12"]["sign_accuracy"] >= 0.0


def test_block_bootstrap_reports_ci_for_improvement_and_edge():
    y_true = np.array([[2.0, 1.0], [1.0, 3.0], [4.0, 1.0], [3.0, 2.0]])
    y_pred = np.array([[1.8, 1.2], [1.1, 2.8], [3.5, 1.2], [2.7, 2.1]])
    baseline = np.array([[2.5, 1.5], [2.5, 1.5], [2.5, 1.5], [2.5, 1.5]])

    result = updn.block_bootstrap_updn_metrics(
        y_true,
        y_pred,
        baseline,
        target_names=("up_12", "dn_12"),
        block_size=2,
        n_boot=20,
        seed=42,
    )

    assert "up_12" in result["mae_improvement_ci"]
    assert "edge_12" in result["edge_spearman_ci"]
    assert {"p05", "p50", "p95"}.issubset(result["mae_improvement_ci"]["up_12"])


def test_gate_passes_only_with_contract_model_and_stability():
    summary = {
        "target_contract": {"status": "PASS"},
        "primary": {
            "profile": "clock_shift_back",
            "horizon": 12,
            "seed_pass_count": 2,
            "target_metrics": {
                "up_12": {"normalized_mae_improvement_vs_constant": 0.06, "spearman": 0.16},
                "dn_12": {"normalized_mae_improvement_vs_constant": 0.07, "spearman": 0.18},
            },
            "edge_12": {"spearman": 0.11, "val_year_sign_reversal": False},
            "bootstrap": {
                "mae_improvement_ci": {
                    "up_12": {"p05": 0.01},
                    "dn_12": {"p05": 0.02},
                },
                "edge_spearman_ci": {"edge_12": {"p05": 0.01}},
            },
            "calendar_importance_share": 0.20,
        },
    }

    gate = updn.evaluate_updn_gate(summary)

    assert gate["research_gate_status"] == "TARGET_FOUNDATION_PASSED"
    assert gate["artifact_status"] == "DIAGNOSTIC_ONLY"
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_regression_updn_target_foundation.py -q
```

Expected: fail on missing metric functions.

- [ ] **Step 3: Implement metrics and gate**

Use:

- MAE and RMSE for scale-sensitive regression quality;
- normalized MAE over median absolute target for cross-horizon comparison;
- normalized MAE over median ATR when raw `ATR` exists and is positive;
- Pearson r for linear relation;
- Spearman rho for ranking relation;
- `edge_h = up_h - dn_h`;
- `log_ratio_h = log1p(up_h) - log1p(dn_h)`.
- block bootstrap with blocks of `20` sequential rows on `val_stop`; use `n_boot=500` for full benchmark and smaller values only in unit tests.

Store `None` instead of `nan` in JSON-facing dictionaries.

- [ ] **Step 4: Run focused tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_regression_updn_target_foundation.py -q
```

Expected: metric and gate tests pass.

---

### Task 4: Runner, Resume, JSON Artifact, CLI

**Files:**
- Modify: `ML/baseline/benchmark_regression_updn_target_foundation.py`
- Modify: `tests/test_regression_updn_target_foundation.py`

**Interfaces:**
- Produces `run_regression_updn_target_foundation(output_path: Path = REGRESSION_UPDN_JSON_REPORT_PATH, resume: bool = True, profile_keys: tuple[str, ...] | None = None) -> dict`.
- Produces CLI:

```bash
./.venv/bin/python ML/baseline/benchmark_regression_updn_target_foundation.py --regression-updn-target-foundation --no-resume
```

- Writes `ML/reports/regression_updn_target_foundation.json`.

- [ ] **Step 1: Add tests for runner shape and CLI**

Add tests that monkeypatch the heavy training path and assert JSON shape:

```python
import json
import subprocess
import sys


def test_runner_report_shape_with_tiny_data(monkeypatch, tmp_path):
    splits = {
        "train_core": _tiny_labeled_frame(),
        "val_stop": _tiny_labeled_frame(),
        "diagnostic_holdout": _tiny_labeled_frame(),
        "low_n_disclosure": _tiny_labeled_frame(),
    }
    monkeypatch.setattr(updn, "load_updn_labeled_splits", lambda: splits)

    output_path = tmp_path / "updn.json"
    report = updn.run_regression_updn_target_foundation(
        output_path=output_path,
        resume=False,
        profile_keys=("constant_median", "clock_only"),
    )

    assert output_path.exists()
    assert report["experiment"] == "regression_updn_target_foundation"
    assert report["artifact_status"] == "DIAGNOSTIC_ONLY"
    assert "research_gate_status" in report
    assert "target_contract" in report
    assert "runs" in report
    assert "summary" in report
    assert "gate" in report


def test_cli_flag_is_registered():
    parser = updn.build_arg_parser()
    args = parser.parse_args(["--regression-updn-target-foundation", "--no-resume"])

    assert args.regression_updn_target_foundation is True
    assert args.resume is False
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_regression_updn_target_foundation.py -q
```

Expected: fail on missing runner/CLI.

- [ ] **Step 3: Implement runner**

Runner requirements:

- record `started_at`, `finished_at`, top-level `elapsed_sec`, and per-run `elapsed_sec`;
- write an initial checkpoint before training;
- checkpoint after target preflight;
- checkpoint after each profile/seed run;
- support `--resume` and `--no-resume`;
- store input file manifest with path, row count, byte count, and SHA256;
- store `feature_names` and `feature_names_sha256` for each profile;
- store `feature_source_contract` and `feature_read_audit` for each profile;
- train `ridge`, `decision_tree_depth3`, `random_forest_depth4`, and `xgboost_depth3` regressors with fixed seeds `(42, 77, 123)` where the model is stochastic;
- standardize features using train-only fit where needed;
- never fit preprocessing on validation, diagnostic holdout, or 2026;
- store constant baseline metrics for every target and split;
- store model metrics for `train_core`, `val_stop`, `diagnostic_holdout`, `low_n_disclosure`;
- store calendar permutation importance share for every non-dummy run;
- store mature/non-mature disclosure per horizon. A row is mature for horizon `h` only if the corresponding top-level `up_h/dn_h` target is known and non-null/non-negative by contract.

- [ ] **Step 4: Run focused tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_regression_updn_target_foundation.py -q
```

Expected: all focused tests pass.

- [ ] **Step 5: Run full benchmark**

Run:

```bash
./.venv/bin/python ML/baseline/benchmark_regression_updn_target_foundation.py --regression-updn-target-foundation --no-resume
```

Expected:

- `ML/reports/regression_updn_target_foundation.json` exists;
- all configured profile/seed runs complete;
- top-level `artifact_status == "DIAGNOSTIC_ONLY"`;
- top-level `research_gate_status` is one of the declared research statuses;
- no selection uses `diagnostic_holdout` or `low_n_disclosure`.

---

### Task 5: Report And Documentation

**Files:**
- Create: `docs/reports/2026-06-30-regression-updn-target-foundation.md`
- Modify: `CHANGELOG.md`
- Modify: `CONTEXT_HANDOFF.md`
- Modify: wiki files through stage-reporting ingest.

**Interfaces:**
- Produces canonical report linked to JSON.
- Produces updated operational handoff.

- [ ] **Step 1: Run report-source checks before writing**

Run:

```bash
./.venv/bin/python - <<'PY'
import json
from pathlib import Path
p = Path("ML/reports/regression_updn_target_foundation.json")
d = json.loads(p.read_text())
print(d["experiment"])
print(d["artifact_status"])
print(len(d["runs"]))
PY
```

Expected: prints `regression_updn_target_foundation`, `DIAGNOSTIC_ONLY`, and a positive run count.

- [ ] **Step 2: Write canonical report**

The report must follow `docs/reports/README.md` and include:

- Context;
- What Was Done;
- Changed Files;
- Verification;
- Results;
- Gate;
- Conclusions;
- Limitations / Open Questions;
- Next Step;
- Related Materials.

Required tables:

- target contract summary for all 10 targets;
- constant, Ridge, shallow tree, shallow random forest, and XGBoost comparison for every horizon;
- normalized error table by horizon: raw MAE, normalized MAE over median target, normalized MAE over median ATR;
- mature/non-mature disclosure by horizon;
- profile summary on `val_stop`;
- seed stability for primary profile;
- `edge_h` diagnostics for horizons `3/6/12/24/48`;
- block bootstrap CI table for normalized MAE improvement and `edge_h` Spearman;
- calendar dependence table: `hour_*` / `dow_*` importance share by profile/model;
- disclosure-only table for `diagnostic_holdout` and `low_n_disclosure`.

Required wording:

- This stage does not select a trading rule.
- Top-level `up_*/dn_*` columns are labels, not model inputs.
- `diagnostic_holdout` and `low_n_disclosure` were not used for selecting target, profile, seed, or threshold.
- Old `regression_updn` production history is background only; this stage is a clean target foundation check.
- H12 is a legacy reference, not an automatically privileged winner.
- If H12 passes and other horizons fail, the next step is not production or threshold search; it is a narrow legacy-H12 confirmation plan with a predeclared reason for ignoring other horizons.
- If a shorter or longer horizon passes while H12 fails, the next step is a separate target-specific design for that horizon, not retrofitting old H12 logic.

- [ ] **Step 3: Optional module documentation and registry row**

Do this step only if the user explicitly asks to update module documentation, and use the `update-docs` skill before editing. If requested, create `docs/ML/benchmark_regression_updn_target_foundation.py.md` with:

- purpose;
- inputs;
- outputs;
- CLI command;
- fixed split;
- target/feature leakage rules;
- status cap.

If requested, update `MODULE_INDEX.md` with one row for the new module. Without that explicit request, mention the missing module-doc update as a follow-up in the final stage response.

- [ ] **Step 4: Update changelog and handoff**

Update:

- `CHANGELOG.md` with a short result entry at the top;
- `CONTEXT_HANDOFF.md` with current stage status, main artifacts, conclusion, next step, and forbidden directions.

- [ ] **Step 5: Run documentation and wiki closure through stage-reporting**

Use the `stage-reporting` skill for final synchronization:

```bash
./.venv/bin/python wiki/wiki.py status
./.venv/bin/python wiki/wiki.py generate
./.venv/bin/python wiki/wiki.py verify
```

Expected: wiki has no uncovered report gaps for the new report after ingest/generate.

---

### Task 6: Verification Before Completion

**Files:**
- All files changed in Tasks 1-5.

**Interfaces:**
- Produces final verification evidence.

- [ ] **Step 1: Run focused tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_regression_updn_target_foundation.py -q
```

Expected: all focused tests pass.

- [ ] **Step 2: Run related tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_label_updn.py tests/test_regression_updn_target_foundation.py -q
```

Expected: all related tests pass.

- [ ] **Step 3: Run full test suite**

Run:

```bash
./.venv/bin/python -m pytest tests/ -q
```

Expected: full suite passes. If runtime is too long or an unrelated historical test fails, record the exact failure and do not claim full verification.

- [ ] **Step 4: Run diff hygiene**

Run:

```bash
git diff --check
```

Expected: no output.

- [ ] **Step 5: Final self-review**

Check:

- no top-level `up_*/dn_*` target column appears in feature names;
- JSON and report agree on run count, gate, status, and key metrics;
- report does not promote diagnostic results into a trading candidate;
- handoff names the next step and forbidden directions clearly;
- no `docs/audit/` file was changed unless explicitly requested.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-06-30-regression-updn-target-foundation.md`. Two execution options:

1. **Subagent-Driven (recommended)** - dispatch a fresh subagent per task, review between tasks, fast iteration.
2. **Inline Execution** - execute tasks in this session using `executing-plans`, with checkpoints for review.

Which approach?
