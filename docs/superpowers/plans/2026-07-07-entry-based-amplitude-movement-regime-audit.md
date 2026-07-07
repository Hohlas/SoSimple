# Entry-Based Amplitude Movement-Regime Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Проверить, есть ли устойчивый и практически полезный signal “будет достаточно движения после `next open`”, не выбирая сторону сделки и не открывая `locked_test`.

**Architecture:** Новый runner строит movement/amplitude targets от уже существующих `entry_up_H` / `entry_dn_H`, сравнивает простые baselines, табличные профили и sequence-профили на одном split. Главный результат — не торговое правило, а audit: объясняется ли amplitude простыми признаками или фрактальная структура добавляет устойчивое ранжирование movement-regime.

**Tech Stack:** Python 3.10+, pandas, numpy, scipy, scikit-learn, PyTorch только если переиспользуется sequence tensor, существующие `ML/baseline/benchmark_entry_based_next_open_closeout.py`, `ML/baseline/benchmark_entry_based_powerful_tabular.py`, `ML/baseline/benchmark_entry_based_sequence_transformer.py`, `./.venv/bin/python`, pytest.

## Global Constraints

- Work on the current branch; do not use git worktree.
- Use `./.venv/bin/python` for every Python command.
- This stage is `DIAGNOSTIC_ONLY` / `RESEARCH_ONLY`; it cannot create a live trading candidate.
- Do not open `locked_test`.
- Do not include EURUSD or cross-pair validation.
- Do not choose trade direction in this plan.
- Do not use `entry_log_ratio` as a primary target or winner metric.
- Do not derive direction from `entry_up - entry_dn` in winner selection.
- `decision_time` for selection-eligible features is `pre_entry_decision`: the model sees only the current row snapshot available at/after `signal_time` and before the actual next `entry_open` price is known.
- Entry rule remains frozen for target/evaluation: signal exists at `signal_time`; evaluated entry is the next available `entry_open`.
- `entry_open`, `entry_price` or any next-open fill price may be used to build/evaluate `entry_up_H`, `entry_dn_H` and `entry_movement_H`, but must not be used as an input feature for selection-eligible profiles.
- Any profile that uses `entry_open` as an input must be named `*_post_entry_diagnostic_only`, excluded from simple/complex baseline comparison, excluded from winner selection, excluded from gates, and excluded from verdict.
- Every feature profile must write `available_at_decision_time` and `feature_contract_verdict` into JSON/CSV metadata.
- Use the same split policy as the latest closeout/powerful/sequence stages:
  - `train <= 2020`;
  - `validation = 2021-2025`, split into `val_select` and `val_eval`;
  - `2026 = low_n_disclosure`, selection-forbidden;
  - `locked_test = not_opened`.
- `val_select` is the only winner-selection split.
- `val_eval` is check-only for the row selected on `val_select`.
- `low_n_disclosure=2026` is disclosure-only and must not affect summary, gates or verdict.
- Top-level target/label/future-derived columns remain forbidden as input features:
  - `up_*`, `dn_*`;
  - `entry_up_*`, `entry_dn_*`, `entry_log_ratio_*`;
  - `ret_*`, `fav_*`, `adv_*`;
  - `target_*`, `label_*`, `outcome_*`;
  - `predict`, `signal`.
- Serialized `Up/Dn` fields inside `fractal1..fractal99` are allowed only as current-row producer state, using the same contract as the sequence-transformer stage.
- `fractal0` `Up/Dn` must be forced to `0.0` in sequence contracts.
- Input normalization/scaler fit only on train; validation and 2026 are transform-only.
- Target thresholds and quantile bins are computed from train only unless explicitly marked disclosure.
- Output prefix: `entry_based_amplitude_movement`.
- Do not overwrite artifacts from previous stages:
  - `entry_based_next_open_closeout.*`;
  - `entry_based_powerful_tabular.*`;
  - `entry_based_sequence_transformer.*`.
- Runner must use `--threads 24` by default on a 32-thread host unless explicitly reduced because parallel workers are running. The JSON must record `requested_threads`, `effective_threads`, and per-model thread settings.
- For sklearn/tree models and any XGBoost-like library, pass thread count explicitly (`n_jobs`, `nthread`, `xgb_threads`, or library equivalent) and write the effective value into each run record.
- Long stages must print heartbeat messages: start, preflight start/end, each run start/end, `done_runs/total_runs`, `elapsed_sec`, and ETA when estimable.
- Runtime metadata must be written to JSON: top-level `started_at`, `finished_at`, `elapsed_sec`, `progress.done_runs`, `progress.total_runs`, and per-run `started_at`, `finished_at`, `elapsed_sec`.
- Save JSON after every completed run.
- Resume key is `profile/model_key/seed/horizon/target_family`. With `--resume`, completed keys are skipped; with `--no-resume`, previous incomplete progress is ignored and a clean run starts.
- Failed runs go into `failed_runs` and do not hide completed results.
- Support `--resume` / `--no-resume`; default is `--resume`.
- `--resume` must compare `run_config_hash` and refuse incompatible scope.

---

## Research Contract

**Main question:** Can the project predict movement-regime after `next open`: “will there be enough movement after entry”, without selecting up/down direction?

**Secondary question:** Is the amplitude trace mostly a simple regime signal explainable by ATR, time, distance to level or fractal density, or does ordered/fractal structure add useful information?

**Interpretation rule:** A positive result is not a trading rule. It can only justify a later plan that defines how movement-regime becomes a filter, how direction is supplied independently, and how execution/backtest is evaluated.

## Target Contract

For each horizon `H in {3, 6, 12, 24}`:

```text
entry_movement_H = max(entry_up_H, entry_dn_H)
movement_flag_q80_H = entry_movement_H >= train_quantile(entry_movement_H, 0.80)
movement_flag_q90_H = entry_movement_H >= train_quantile(entry_movement_H, 0.90)
movement_flag_q95_H = entry_movement_H >= train_quantile(entry_movement_H, 0.95)
```

Target units:

- `entry_movement_H` keeps the exact units of source `entry_up_H` / `entry_dn_H` from the entry-based target builder.
- The runner must write `target_unit_contract` in JSON with source function/file, target columns, and unit description.
- If the source unit cannot be verified from the reused entry-based target builder or artifact metadata, the run may still generate artifacts but `decide_verdict()` must return `ABORT_CONTRACT_FAIL`.
- Do not create a new price/entry target and do not normalize targets inside this plan.
- Add a target-distribution table with p50/p80/p90/p95 for `entry_movement_H` by horizon and split: `train`, `val_select`, `val_eval`, `low_n_disclosure`.

Primary predicted target family:

```text
entry_movement_H
```

Secondary diagnostic classification targets:

```text
movement_flag_q80_H
movement_flag_q90_H
movement_flag_q95_H
```

Primary metrics:

- Spearman for `entry_movement_H`;
- quantile lift table: top predicted 5/10/20% vs the rest, with `top_n` and `rest_n`;
- yearly Spearman and yearly quantile lift for `val_select` and `val_eval`, with yearly `top_n` and `rest_n`.

Secondary metrics:

- ROC AUC and average precision for `movement_flag_q80/q90/q95`;
- calibration by prediction quantile;
- selected top-k coverage and actual mean movement.

Forbidden metrics for winner selection:

- `entry_log_ratio`;
- simple trade PnL;
- any direction proxy derived from `entry_up - entry_dn`;
- any 2026 metric.

## Feature Profiles

The first audit must compare simple controls before complex models.

### Simple Baselines

| Profile | Input | Purpose |
|---|---|---|
| `atr_only` | row `ATR` transformed with train-only scaler | Checks whether movement is just current volatility |
| `time_only_clean` | `hour_sin`, `hour_cos`, `dow_sin`, `dow_cos` | Checks calendar regime |
| `time_plus_atr` | `ATR` + `hour_sin`, `hour_cos`, `dow_sin`, `dow_cos` | Checks whether volatility plus calendar explains movement |
| `distance_to_level_pre_entry_only` | `abs(fractal0.price - decision_price) / ATR`, where `decision_price` is an allowlisted price column available at `decision_time` such as `close`, `Close`, `signal_price` or another documented current-row price | Checks whether pre-entry distance to level explains amplitude |
| `fractal_density_only` | counts of valid fractals within 1/2/5/10 ATR and nearest-distance summary, excluding `fractal0` anchor | Checks whether level density explains movement |
| `simple_combined` | union of `atr_only`, `time_only_clean`, `distance_to_level_pre_entry_only`, and `fractal_density_only` | Strong simple baseline for explanation checks |
| `distance_to_entry_open_post_entry_diagnostic_only` | `abs(fractal0.price - entry_open) / ATR` | Disclosure-only check of actual fill distance after entry |

Rules:

- `distance_to_level_pre_entry_only` must not use `entry_open`, `entry_price`, future OHLC, or any next-open fill column.
- If no allowlisted `decision_price` is present, skip `distance_to_level_pre_entry_only`, write `status=SKIPPED_NO_DECISION_PRICE`, and do not silently substitute another price.
- `distance_to_entry_open_post_entry_diagnostic_only` is allowed only as `post_entry_diagnostic_only=true`; it cannot affect `best_simple_baseline`, selected winner, gates, or verdict.
- `fractal_density_only` must exclude `fractal0`; otherwise nearest distance becomes mechanically zero and counts always include the anchor.

### Tabular Fractal Profiles

| Profile | Source | Purpose |
|---|---|---|
| `nearest_k60_tabular` | reuse closeout/powerful feature builder | Compare to previous best amplitude neighborhood |
| `nearest_k80_tabular` | reuse closeout/powerful feature builder | Compare to previous sequence direction/amplitude neighborhood |
| `nearest_k60_no_price_coord_tabular` | same as nearest_k60 but remove `price_coord_atr`, `abs_price_coord_atr`, `dir_price_coord_atr` and equivalent flat coordinate fields | Tests price-coordinate dependence |
| `nearest_k80_no_price_coord_tabular` | same as nearest_k80 but remove coordinate fields | Tests price-coordinate dependence |

### Sequence Profiles

| Profile | Source | Purpose |
|---|---|---|
| `nearest_k60_sequence_flat` | sequence tensor flattened to HGB | Reuse strong amplitude pattern without attention |
| `nearest_k80_sequence_flat` | sequence tensor flattened to HGB | Compare to sequence-transformer stage |
| `nearest_k60_no_time_sequence_flat` | sequence tensor without calendar fields | Tests calendar dependence |
| `nearest_k60_no_price_coord_sequence_flat` | sequence tensor without `price_coord_atr`, `abs_price_coord_atr`, `dir_price_coord_atr` | Tests tail-coordinate dependence |

Do not train Transformer in this first movement-regime audit. The last sequence stage showed the best amplitude row came from `sequence_flat_hist_gradient_boosting`, while Transformer was expensive. If flat sequence movement-regime survives controls, a later plan may add multi-seed Transformer.

## Model Matrix

Keep the first movement-regime audit bounded:

| Model key | Type | Profiles |
|---|---|---|
| `ridge_regression` | `sklearn.linear_model.Ridge` | simple baselines only |
| `hist_gradient_boosting` | `HistGradientBoostingRegressor` | all profiles |
| `extra_trees_small` | `ExtraTreesRegressor` with bounded trees | all profiles except sequence if too slow |

Classification diagnostics can be produced from regression predictions by thresholding true movement flags. If implementing direct classifiers, use only `hist_gradient_boosting_classifier` and keep them secondary.

`distance_to_entry_open_post_entry_diagnostic_only` may be trained only for disclosure. It is not a simple baseline, not a complex candidate, and not part of the winner matrix.

Seeds:

```text
42, 43, 44
```

Use 3 seeds for all non-deterministic models on the profiles that pass preflight. Deterministic models record `seed = null` or `seed = 42` with `deterministic = true`.

Planned first-pass search width for primary regression:

```text
15 profile keys * up to 3 models * up to 3 seeds * 4 horizons = at most 540 generated primary comparisons before model/profile pruning
```

Actual completed comparisons must be reported from `enumerate_jobs()` because `ridge_regression` is simple-only, deterministic models collapse to one seed, skipped profiles are excluded, and post-entry diagnostic rows are selection-forbidden.

Because this is post-hoc and wide, any positive result remains `DIAGNOSTIC_ONLY` until a separate replication plan. The report must state that the wide search weakens confidence in any single winner.

## Gate Policy

Allowed verdicts:

- `AMPLITUDE_EXPLAINED_BY_SIMPLE_BASELINES`: simple baselines match complex profiles; do not continue to complex movement filter.
- `MOVEMENT_REGIME_TRACE_FOUND`: complex profiles beat simple baselines on `val_select` and survive `val_eval`, yearly and quantile checks; requires replication before trading.
- `REJECT_MOVEMENT_REGIME`: movement/amplitude does not survive controls or `val_eval`.
- `ABORT_CONTRACT_FAIL`: smoke-check, leakage, split, target, normalization or audit contract fails.

Forbidden verdicts:

- `CANDIDATE`;
- `FROZEN`;
- `READY_FOR_LOCKED_TEST`;
- `DIRECTION_FOUND`;
- `TRADING_RULE_FOUND`.

Primary movement-regime gates:

- winner selection unit is `(profile, model_key, horizon, target_family)` seed aggregate, not a single best seed row;
- seed aggregate is selected by median `val_select_spearman`, not by `val_eval` or 2026;
- non-deterministic aggregates require all three seeds to finish or failed seeds to be listed in `failed_runs`;
- selected complex aggregate is not a simple-only control and not `post_entry_diagnostic_only`;
- selected complex aggregate beats `best_simple_baseline` selected by the same protocol on the same horizon by:
  - median Spearman delta `>= 0.03` on `val_select`;
  - median Spearman delta `>= 0.02` on `val_eval`;
- selected aggregate has median `entry_movement_H` Spearman:
  - `val_select >= 0.25`;
  - `val_eval >= 0.15`;
- seed robustness passes:
  - at least 2 of 3 non-deterministic seeds have positive `val_eval_spearman`;
  - at least 2 of 3 non-deterministic seeds have `val_eval_top10_lift >= 1.10`;
  - report includes median/mean/std/min/max for every selected aggregate;
- yearly check passes:
  - at least 2 positive years in `val_select`;
  - at least 2 positive years in `val_eval`;
  - no single year explains the entire aggregate;
- top quantile check passes:
  - median top 10% predicted movement has actual mean movement at least `1.20x` the remaining 90% on `val_select`;
  - same selected aggregate has at least `1.10x` on `val_eval`;
  - quantile rows include `top_n`, `rest_n`, and block-bootstrap confidence interval fields `lift_ci_p05`, `lift_ci_p50`, `lift_ci_p95`;
  - `val_eval` top-10% `lift_ci_p05 >= 1.00`;
- no unresolved `ERROR` in feature/scale/tail audit;
- if `price_coord_atr` warning remains, a no-price-coordinate profile must be reported next to the selected row.

If movement gates pass, the output is still not a trade. It becomes a permitted input to a later `movement_filter_design` plan.

## File Structure

**Create**

- `ML/baseline/benchmark_entry_based_amplitude_movement.py` - runner for movement targets, simple baselines, feature controls, quantile/yearly tables and JSON/CSV artifacts.
- `tests/test_entry_based_amplitude_movement.py` - focused tests for target builder, selection policy, controls, quantile metrics, no-direction rule and output contract.
- `docs/ML/benchmark_entry_based_amplitude_movement.py.md` - module documentation.
- `docs/reports/YYYY-MM-DD-entry-based-amplitude-movement-regime.md` - final report after execution.

**Modify after execution**

- `CHANGELOG.md`;
- `CONTEXT_HANDOFF.md`;
- `docs/tests/tests.md`;
- `MODULE_INDEX.md`;
- `wiki/research/fractal-stop-research.md`;
- `wiki/index.md`;
- `wiki/log.md`;
- `wiki/REPO_integrity.md`.

**Generated**

- `ML/reports/entry_based_amplitude_movement.json`;
- `ML/reports/entry_based_amplitude_movement_metrics.csv`;
- `ML/reports/entry_based_amplitude_movement_seed_aggregate.csv`;
- `ML/reports/entry_based_amplitude_movement_quantiles.csv`;
- `ML/reports/entry_based_amplitude_movement_yearly.csv`;
- `ML/reports/entry_based_amplitude_movement_target_distribution.csv`;
- `ML/reports/entry_based_amplitude_movement_feature_audit.csv`;
- `ML/reports/entry_based_amplitude_movement_rows.csv`;
- `ML/reports/entry_based_amplitude_movement_run.log`.

**Read Before Implementation**

- `docs/methodology/README.md`;
- `docs/methodology/03-feature-contract-leakage.md`;
- `docs/methodology/06-temporal-split.md`;
- `docs/methodology/07-baseline-first.md`;
- `docs/methodology/11-robustness.md`;
- `docs/methodology/16-reporting-audit.md`;
- `docs/methodology/A7-feature-distribution-audit.md`;
- `docs/methodology/A8-feature-target-catalog.md`;
- `docs/reports/2026-07-07-entry-based-fractal-sequence-transformer.md`;
- `docs/reports/2026-07-06-entry-based-powerful-tabular-models.md`;
- `ML/baseline/benchmark_entry_based_next_open_closeout.py`;
- `ML/baseline/benchmark_entry_based_powerful_tabular.py`;
- `ML/baseline/benchmark_entry_based_sequence_transformer.py`;

---

## Task 1: Target And Metric Contract

**Files:**
- Create: `tests/test_entry_based_amplitude_movement.py`
- Create: `ML/baseline/benchmark_entry_based_amplitude_movement.py`

**Interfaces:**
- Produces: `TARGET_HORIZONS: tuple[int, ...]`, `MOVEMENT_QUANTILES: tuple[float, ...]`, `build_movement_targets(frame: pd.DataFrame, train_thresholds: dict[str, float] | None = None) -> tuple[pd.DataFrame, dict[str, float]]`
- Produces: `compute_spearman(y_true: np.ndarray, y_pred: np.ndarray) -> float`
- Produces: `compute_quantile_lift(y_true: np.ndarray, y_pred: np.ndarray, top_fracs: tuple[float, ...]) -> list[dict[str, float]]`
- Produces: `compute_target_distribution(targets_by_split: dict[str, pd.DataFrame]) -> list[dict[str, Any]]`
- Produces: `TARGET_UNIT_CONTRACT: dict[str, str]`

- [ ] **Step 1: Write failing tests for movement target construction**

Add to `tests/test_entry_based_amplitude_movement.py`:

```python
from __future__ import annotations

import numpy as np
import pandas as pd

import ML.baseline.benchmark_entry_based_amplitude_movement as runner


def test_build_movement_targets_uses_max_up_dn_and_train_thresholds():
    frame = pd.DataFrame(
        {
            "entry_up_3": [1.0, 4.0, 2.0, 8.0],
            "entry_dn_3": [3.0, 1.0, 5.0, 2.0],
            "entry_up_6": [2.0, 2.0, 2.0, 9.0],
            "entry_dn_6": [1.0, 3.0, 4.0, 1.0],
            "entry_up_12": [1.0, 1.0, 7.0, 1.0],
            "entry_dn_12": [2.0, 5.0, 1.0, 1.0],
            "entry_up_24": [1.0, 6.0, 1.0, 1.0],
            "entry_dn_24": [1.0, 1.0, 8.0, 1.0],
        }
    )

    targets, thresholds = runner.build_movement_targets(frame)

    assert targets["entry_movement_3"].tolist() == [3.0, 4.0, 5.0, 8.0]
    assert targets["entry_movement_6"].tolist() == [2.0, 3.0, 4.0, 9.0]
    assert "movement_flag_q80_3" in targets
    assert "movement_flag_q90_3" in targets
    assert "movement_flag_q95_3" in targets
    assert thresholds["q80_3"] == np.quantile([3.0, 4.0, 5.0, 8.0], 0.80)


def test_build_movement_targets_can_reuse_train_thresholds():
    frame = pd.DataFrame(
        {
            "entry_up_3": [1.0, 10.0],
            "entry_dn_3": [2.0, 1.0],
            "entry_up_6": [1.0, 1.0],
            "entry_dn_6": [1.0, 1.0],
            "entry_up_12": [1.0, 1.0],
            "entry_dn_12": [1.0, 1.0],
            "entry_up_24": [1.0, 1.0],
            "entry_dn_24": [1.0, 1.0],
        }
    )
    thresholds = {f"q{q}_{h}": 5.0 for q in (80, 90, 95) for h in runner.TARGET_HORIZONS}

    targets, reused = runner.build_movement_targets(frame, thresholds)

    assert reused == thresholds
    assert targets["movement_flag_q80_3"].tolist() == [0, 1]


def test_target_unit_contract_is_explicit():
    assert runner.TARGET_UNIT_CONTRACT["source_columns"] == "entry_up_H/entry_dn_H"
    assert runner.TARGET_UNIT_CONTRACT["movement_formula"] == "max(entry_up_H, entry_dn_H)"
    assert runner.TARGET_UNIT_CONTRACT["normalization"] == "none"


def test_target_distribution_reports_split_quantiles():
    targets_by_split = {
        "train": pd.DataFrame({"entry_movement_3": [1.0, 2.0, 3.0, 4.0]}),
        "val_select": pd.DataFrame({"entry_movement_3": [2.0, 4.0, 6.0, 8.0]}),
    }

    rows = runner.compute_target_distribution(targets_by_split)

    train_h3 = next(row for row in rows if row["split"] == "train" and row["horizon"] == 3)
    assert train_h3["n"] == 4
    assert train_h3["p50"] == 2.5
    assert train_h3["p80"] == np.quantile([1.0, 2.0, 3.0, 4.0], 0.80)
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_amplitude_movement.py::test_build_movement_targets_uses_max_up_dn_and_train_thresholds -q
```

Expected: fail because module or function does not exist.

- [ ] **Step 3: Implement target and metric helpers**

Create `ML/baseline/benchmark_entry_based_amplitude_movement.py`:

```python
# =============================================================================
# Файл: benchmark_entry_based_amplitude_movement.py
# Назначение: DIAGNOSTIC_ONLY runner для проверки movement-regime/amplitude
#   в entry-based next open постановке без выбора направления сделки.
# Язык: Python 3.10+
# Обновлён: 2026-07-07
# =============================================================================

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import os
import sys
import time
from dataclasses import dataclass
from itertools import product
from pathlib import Path
from typing import Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.ensemble import ExtraTreesRegressor, HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.multioutput import MultiOutputRegressor
from sklearn.preprocessing import RobustScaler

from ML.baseline import benchmark_entry_based_next_open_closeout as closeout
from ML.baseline import benchmark_entry_based_powerful_tabular as powerful
from ML.baseline import benchmark_entry_based_sequence_transformer as sequence


AMPLITUDE_MOVEMENT_SCHEMA_VERSION = 1
OUTPUT_PREFIX = "entry_based_amplitude_movement"
REPORT_JSON_PATH = Path(f"ML/reports/{OUTPUT_PREFIX}.json")
REPORT_METRICS_PATH = Path(f"ML/reports/{OUTPUT_PREFIX}_metrics.csv")
REPORT_SEED_AGGREGATE_PATH = Path(f"ML/reports/{OUTPUT_PREFIX}_seed_aggregate.csv")
REPORT_QUANTILES_PATH = Path(f"ML/reports/{OUTPUT_PREFIX}_quantiles.csv")
REPORT_YEARLY_PATH = Path(f"ML/reports/{OUTPUT_PREFIX}_yearly.csv")
REPORT_TARGET_DISTRIBUTION_PATH = Path(f"ML/reports/{OUTPUT_PREFIX}_target_distribution.csv")
REPORT_FEATURE_AUDIT_PATH = Path(f"ML/reports/{OUTPUT_PREFIX}_feature_audit.csv")
REPORT_ROWS_PATH = Path(f"ML/reports/{OUTPUT_PREFIX}_rows.csv")
REPORT_LOG_PATH = Path(f"ML/reports/{OUTPUT_PREFIX}_run.log")

TARGET_HORIZONS = (3, 6, 12, 24)
MOVEMENT_QUANTILES = (0.80, 0.90, 0.95)
TOP_LIFT_FRACS = (0.05, 0.10, 0.20)
SEEDS = (42, 43, 44)
TARGET_UNIT_CONTRACT = {
    "source_columns": "entry_up_H/entry_dn_H",
    "movement_formula": "max(entry_up_H, entry_dn_H)",
    "units": "same_as_entry_based_target_builder",
    "normalization": "none",
    "source_contract_file": "docs/methodology/A8-feature-target-catalog.md",
}


def _required_entry_columns() -> list[str]:
    return [f"entry_{side}_{h}" for h in TARGET_HORIZONS for side in ("up", "dn")]


def build_movement_targets(
    frame: pd.DataFrame,
    train_thresholds: dict[str, float] | None = None,
) -> tuple[pd.DataFrame, dict[str, float]]:
    missing = [column for column in _required_entry_columns() if column not in frame.columns]
    if missing:
        raise ValueError(f"Missing movement source columns: {missing}")

    targets = pd.DataFrame(index=frame.index)
    thresholds = dict(train_thresholds or {})
    for horizon in TARGET_HORIZONS:
        movement = np.maximum(
            frame[f"entry_up_{horizon}"].astype(float).to_numpy(),
            frame[f"entry_dn_{horizon}"].astype(float).to_numpy(),
        )
        targets[f"entry_movement_{horizon}"] = movement
        for quantile in MOVEMENT_QUANTILES:
            q_int = int(quantile * 100)
            key = f"q{q_int}_{horizon}"
            if key not in thresholds:
                thresholds[key] = float(np.quantile(movement, quantile))
            targets[f"movement_flag_q{q_int}_{horizon}"] = (movement >= thresholds[key]).astype(int)
    return targets, thresholds


def compute_spearman(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    if len(y_true) < 3 or len(y_pred) < 3:
        return float("nan")
    if np.nanstd(y_true) == 0 or np.nanstd(y_pred) == 0:
        return float("nan")
    value = spearmanr(y_true, y_pred).correlation
    return float(value) if value is not None and np.isfinite(value) else float("nan")


def _single_quantile_lift(y_true: np.ndarray, y_pred: np.ndarray, frac: float) -> dict[str, float]:
    if len(y_true) == 0:
        return {"top_frac": frac, "top_n": 0, "rest_n": 0, "top_mean": float("nan"), "rest_mean": float("nan"), "lift": float("nan")}
    top_n = max(1, int(math.ceil(len(y_true) * frac)))
    order = np.argsort(y_pred)[::-1]
    top_idx = order[:top_n]
    rest_idx = order[top_n:]
    top_mean = float(np.mean(y_true[top_idx]))
    rest_mean = float(np.mean(y_true[rest_idx])) if len(rest_idx) else float("nan")
    lift = float(top_mean / rest_mean) if rest_mean and np.isfinite(rest_mean) else float("nan")
    return {"top_frac": frac, "top_n": int(top_n), "rest_n": int(len(rest_idx)), "top_mean": top_mean, "rest_mean": rest_mean, "lift": lift}


def _block_bootstrap_lift_ci(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    frac: float,
    block_size: int = 20,
    rounds: int = 200,
    seed: int = 42,
) -> tuple[float, float, float]:
    if len(y_true) < block_size * 2:
        return (float("nan"), float("nan"), float("nan"))
    rng = np.random.default_rng(seed)
    starts = np.arange(0, len(y_true), block_size)
    lifts: list[float] = []
    for _ in range(rounds):
        sampled_parts = []
        for start in rng.choice(starts, size=len(starts), replace=True):
            sampled_parts.append(np.arange(start, min(start + block_size, len(y_true))))
        sampled_idx = np.concatenate(sampled_parts)
        row = _single_quantile_lift(y_true[sampled_idx], y_pred[sampled_idx], frac)
        if np.isfinite(row["lift"]):
            lifts.append(float(row["lift"]))
    if not lifts:
        return (float("nan"), float("nan"), float("nan"))
    return tuple(float(x) for x in np.quantile(lifts, [0.05, 0.50, 0.95]))


def compute_quantile_lift(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    top_fracs: tuple[float, ...] = TOP_LIFT_FRACS,
) -> list[dict[str, float]]:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    valid = np.isfinite(y_true) & np.isfinite(y_pred)
    y_true = y_true[valid]
    y_pred = y_pred[valid]
    rows: list[dict[str, float]] = []
    for frac in top_fracs:
        row = _single_quantile_lift(y_true, y_pred, frac)
        ci_p05, ci_p50, ci_p95 = _block_bootstrap_lift_ci(y_true, y_pred, frac)
        row.update({"lift_ci_p05": ci_p05, "lift_ci_p50": ci_p50, "lift_ci_p95": ci_p95})
        rows.append(row)
    return rows


def compute_target_distribution(targets_by_split: dict[str, pd.DataFrame]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for split_name, targets in targets_by_split.items():
        for horizon in TARGET_HORIZONS:
            column = f"entry_movement_{horizon}"
            if column not in targets.columns:
                continue
            values = pd.to_numeric(targets[column], errors="coerce").dropna().to_numpy(dtype=float)
            rows.append(
                {
                    "split": split_name,
                    "horizon": horizon,
                    "n": int(len(values)),
                    "p50": float(np.quantile(values, 0.50)) if len(values) else float("nan"),
                    "p80": float(np.quantile(values, 0.80)) if len(values) else float("nan"),
                    "p90": float(np.quantile(values, 0.90)) if len(values) else float("nan"),
                    "p95": float(np.quantile(values, 0.95)) if len(values) else float("nan"),
                }
            )
    return rows
```

- [ ] **Step 4: Run target tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_amplitude_movement.py -q
```

Expected: target tests pass; later tests do not exist yet.

- [ ] **Step 5: Leave changes uncommitted until closure**

Do not commit this task separately. Keep the working tree changes for the stage-level closeout handled by `stage-reporting`.

## Task 2: Feature Profiles And Controls

**Files:**
- Modify: `tests/test_entry_based_amplitude_movement.py`
- Modify: `ML/baseline/benchmark_entry_based_amplitude_movement.py`

**Interfaces:**
- Consumes: `build_movement_targets`
- Produces: `build_simple_feature_frame(frame: pd.DataFrame, profile: str) -> tuple[pd.DataFrame, dict[str, Any]]`
- Produces: `build_feature_profile(splits: dict[str, pd.DataFrame], profile: str) -> dict[str, pd.DataFrame]`
- Produces: `is_forbidden_input_column(column: str) -> bool`

- [ ] **Step 1: Add tests for forbidden inputs and simple controls**

Add:

```python
def test_forbidden_target_columns_are_rejected():
    forbidden = [
        "entry_up_3",
        "entry_dn_24",
        "entry_log_ratio_12",
        "target_future",
        "label_win",
        "ret_6",
        "fav_12",
        "adv_12",
        "predict",
        "signal",
    ]
    assert all(runner.is_forbidden_input_column(column) for column in forbidden)
    assert not runner.is_forbidden_input_column("ATR")
    assert not runner.is_forbidden_input_column("hour_sin")


def test_time_only_clean_profile_contains_only_calendar_features():
    frame = pd.DataFrame({"time": ["2021-01-04 03:00:00"], "ATR": [1.2]})
    features, meta = runner.build_simple_feature_frame(frame, "time_only_clean")

    assert features.columns.tolist() == ["hour_sin", "hour_cos", "dow_sin", "dow_cos"]
    assert meta["profile"] == "time_only_clean"


def test_atr_only_profile_contains_only_atr():
    frame = pd.DataFrame({"time": ["2021-01-04 03:00:00"], "ATR": [1.2]})
    features, meta = runner.build_simple_feature_frame(frame, "atr_only")

    assert features.columns.tolist() == ["ATR"]
    assert features.iloc[0]["ATR"] == 1.2
    assert meta["profile"] == "atr_only"


def test_time_plus_atr_profile_contains_calendar_and_atr():
    frame = pd.DataFrame({"time": ["2021-01-04 03:00:00"], "ATR": [1.2]})
    features, meta = runner.build_simple_feature_frame(frame, "time_plus_atr")

    assert features.columns.tolist() == ["ATR", "hour_sin", "hour_cos", "dow_sin", "dow_cos"]
    assert meta["feature_contract_verdict"] == "PASS"


def test_pre_entry_distance_rejects_entry_open_as_input():
    frame = pd.DataFrame(
        {
            "time": ["2021-01-04 03:00:00"],
            "ATR": [0.5],
            "entry_open": [1.2300],
            "fractal0": ["0,1.2200,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0"],
        }
    )

    features, meta = runner.build_simple_feature_frame(frame, "distance_to_level_pre_entry_only")

    assert features.empty
    assert meta["status"] == "SKIPPED_NO_DECISION_PRICE"
    assert meta["used_entry_open_as_input"] is False


def test_post_entry_distance_is_selection_forbidden():
    frame = pd.DataFrame(
        {
            "time": ["2021-01-04 03:00:00"],
            "ATR": [0.5],
            "entry_open": [1.2300],
            "fractal0": ["0,1.2200,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0"],
        }
    )

    features, meta = runner.build_simple_feature_frame(frame, "distance_to_entry_open_post_entry_diagnostic_only")

    assert features.columns.tolist() == ["distance_to_entry_open_atr"]
    assert meta["post_entry_diagnostic_only"] is True
    assert meta["selection_eligible"] is False


def test_fractal_density_excludes_fractal0_anchor(monkeypatch):
    frame = pd.DataFrame(
        {
            "ATR": [0.05],
            "fractal0": ["f0"],
            "fractal1": ["f1"],
            "fractal2": ["f2"],
        }
    )
    prices = {"f0": [0.0, 1.20], "f1": [0.0, 1.25], "f2": [0.0, 1.40]}
    monkeypatch.setattr(runner, "_parse_fractal_values", lambda raw: prices.get(raw))

    features, meta = runner.build_simple_feature_frame(frame, "fractal_density_only")

    assert meta["excludes_fractal0"] is True
    assert features.iloc[0]["valid_fractal_count"] == 2
    assert features.iloc[0]["nearest_distance_atr"] == 1.0
    assert features.iloc[0]["count_within_1atr"] == 1
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_amplitude_movement.py::test_time_only_clean_profile_contains_only_calendar_features -q
```

Expected: fail because `build_simple_feature_frame` does not exist.

- [ ] **Step 3: Implement feature control helpers**

Add to runner:

```python
FORBIDDEN_INPUT_COLUMN_PATTERNS = (
    "up_",
    "dn_",
    "entry_up_",
    "entry_dn_",
    "entry_log_ratio_",
    "ret_",
    "fav_",
    "adv_",
    "target_",
    "label_",
    "outcome_",
    "predict",
    "signal",
)

SIMPLE_PROFILES = (
    "atr_only",
    "time_only_clean",
    "time_plus_atr",
    "distance_to_level_pre_entry_only",
    "fractal_density_only",
    "simple_combined",
)
POST_ENTRY_DIAGNOSTIC_PROFILES = ("distance_to_entry_open_post_entry_diagnostic_only",)
SELECTION_FORBIDDEN_PROFILES = POST_ENTRY_DIAGNOSTIC_PROFILES


def is_forbidden_input_column(column: str) -> bool:
    return any(column == pattern or column.startswith(pattern) for pattern in FORBIDDEN_INPUT_COLUMN_PATTERNS)


def _calendar_frame(frame: pd.DataFrame) -> pd.DataFrame:
    timestamp = pd.to_datetime(frame["time"], errors="coerce")
    hour = timestamp.dt.hour.fillna(0).astype(float)
    dow = timestamp.dt.dayofweek.fillna(0).astype(float)
    return pd.DataFrame(
        {
            "hour_sin": np.sin(2 * np.pi * hour / 24.0),
            "hour_cos": np.cos(2 * np.pi * hour / 24.0),
            "dow_sin": np.sin(2 * np.pi * dow / 7.0),
            "dow_cos": np.cos(2 * np.pi * dow / 7.0),
        },
        index=frame.index,
    )


def _parse_fractal_values(raw: object) -> list[float] | None:
    values = sequence._parse_fractal(raw)
    return values


def _fractal0_price(frame: pd.DataFrame) -> pd.Series:
    prices = []
    for raw in frame["fractal0"]:
        values = _parse_fractal_values(raw)
        prices.append(values[1] if values else np.nan)
    return pd.Series(prices, index=frame.index, dtype=float)


def _decision_price_series(frame: pd.DataFrame) -> tuple[pd.Series | None, str | None]:
    for column in ("signal_price", "close", "Close", "bid_snapshot", "ask_snapshot"):
        if column in frame.columns:
            return frame[column].astype(float), column
    return None, None


def _entry_open_series(frame: pd.DataFrame) -> tuple[pd.Series, str]:
    for column in ("entry_open", "entry_price", "open"):
        if column in frame.columns:
            return frame[column].astype(float), column
    raise ValueError("post-entry distance diagnostic requires entry_open, entry_price or open")


def _distance_to_level_pre_entry_frame(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    decision_price, source = _decision_price_series(frame)
    if decision_price is None:
        return pd.DataFrame(index=frame.index), {
            "status": "SKIPPED_NO_DECISION_PRICE",
            "available_at_decision_time": False,
            "feature_contract_verdict": "SKIPPED",
            "used_entry_open_as_input": False,
        }
    f0_price = _fractal0_price(frame)
    atr = frame["ATR"].astype(float).replace(0, np.nan)
    values = (f0_price - decision_price).abs() / atr
    return pd.DataFrame({"distance_to_fractal0_pre_entry_atr": values.fillna(0.0)}, index=frame.index), {
        "status": "PASS",
        "distance_price_source": source,
        "available_at_decision_time": True,
        "feature_contract_verdict": "PASS",
        "used_entry_open_as_input": False,
    }


def _distance_to_entry_open_post_entry_frame(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    entry_price, source = _entry_open_series(frame)
    f0_price = _fractal0_price(frame)
    atr = frame["ATR"].astype(float).replace(0, np.nan)
    values = (f0_price - entry_price).abs() / atr
    return pd.DataFrame({"distance_to_entry_open_atr": values.fillna(0.0)}, index=frame.index), {
        "status": "PASS",
        "distance_price_source": source,
        "available_at_decision_time": False,
        "feature_contract_verdict": "POST_ENTRY_DIAGNOSTIC_ONLY",
        "used_entry_open_as_input": True,
        "post_entry_diagnostic_only": True,
        "selection_eligible": False,
    }


def _fractal_density_frame(frame: pd.DataFrame) -> pd.DataFrame:
    f0_price = _fractal0_price(frame)
    atr = frame["ATR"].astype(float).replace(0, np.nan)
    out = {
        "valid_fractal_count": [],
        "count_within_1atr": [],
        "count_within_2atr": [],
        "count_within_5atr": [],
        "count_within_10atr": [],
        "nearest_distance_atr": [],
    }
    for row_idx, row in frame.iterrows():
        distances: list[float] = []
        for idx in range(1, 100):
            values = _parse_fractal_values(row.get(f"fractal{idx}"))
            if values is None or not np.isfinite(f0_price.loc[row_idx]) or not np.isfinite(atr.loc[row_idx]):
                continue
            distances.append(abs(values[1] - f0_price.loc[row_idx]) / atr.loc[row_idx])
        arr = np.asarray(distances, dtype=float)
        out["valid_fractal_count"].append(int(len(arr)))
        out["count_within_1atr"].append(int(np.sum(arr <= 1.0)) if len(arr) else 0)
        out["count_within_2atr"].append(int(np.sum(arr <= 2.0)) if len(arr) else 0)
        out["count_within_5atr"].append(int(np.sum(arr <= 5.0)) if len(arr) else 0)
        out["count_within_10atr"].append(int(np.sum(arr <= 10.0)) if len(arr) else 0)
        out["nearest_distance_atr"].append(float(np.min(arr)) if len(arr) else 0.0)
    return pd.DataFrame(out, index=frame.index)


def build_simple_feature_frame(frame: pd.DataFrame, profile: str) -> tuple[pd.DataFrame, dict[str, Any]]:
    meta: dict[str, Any] = {"profile": profile}
    if profile == "atr_only":
        meta.update({"available_at_decision_time": True, "feature_contract_verdict": "PASS", "selection_eligible": True})
        return pd.DataFrame({"ATR": frame["ATR"].astype(float)}, index=frame.index), meta
    if profile == "time_only_clean":
        meta.update({"available_at_decision_time": True, "feature_contract_verdict": "PASS", "selection_eligible": True})
        return _calendar_frame(frame), meta
    if profile == "time_plus_atr":
        meta.update({"available_at_decision_time": True, "feature_contract_verdict": "PASS", "selection_eligible": True})
        return pd.concat([pd.DataFrame({"ATR": frame["ATR"].astype(float)}, index=frame.index), _calendar_frame(frame)], axis=1), meta
    if profile == "distance_to_level_pre_entry_only":
        features, distance_meta = _distance_to_level_pre_entry_frame(frame)
        meta.update(distance_meta)
        return features, meta
    if profile == "fractal_density_only":
        meta.update({"available_at_decision_time": True, "feature_contract_verdict": "PASS", "selection_eligible": True, "excludes_fractal0": True})
        return _fractal_density_frame(frame), meta
    if profile == "simple_combined":
        parts = []
        for child in ("atr_only", "time_only_clean", "distance_to_level_pre_entry_only", "fractal_density_only"):
            child_features, child_meta = build_simple_feature_frame(frame, child)
            if child_features.empty:
                continue
            parts.append(child_features)
            meta.update({f"{child}_{key}": value for key, value in child_meta.items() if key != "profile"})
        meta.update({"available_at_decision_time": True, "feature_contract_verdict": "PASS", "selection_eligible": True})
        return pd.concat(parts, axis=1), meta
    if profile == "distance_to_entry_open_post_entry_diagnostic_only":
        features, distance_meta = _distance_to_entry_open_post_entry_frame(frame)
        meta.update(distance_meta)
        return features, meta
    raise ValueError(f"Unknown simple profile: {profile}")
```

- [ ] **Step 4: Run tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_amplitude_movement.py -q
```

Expected: all current tests pass.

- [ ] **Step 5: Leave changes uncommitted until closure**

Do not commit this task separately. Keep the working tree changes for the stage-level closeout handled by `stage-reporting`.

## Task 3: Model Runner, Resume And Artifacts

**Files:**
- Modify: `tests/test_entry_based_amplitude_movement.py`
- Modify: `ML/baseline/benchmark_entry_based_amplitude_movement.py`

**Interfaces:**
- Consumes: feature builders and target builders
- Produces: CLI `--entry-based-amplitude-movement`, `--resume`, `--no-resume`, `--threads`
- Produces: JSON/CSV artifacts under `ML/reports/entry_based_amplitude_movement*`
- Produces: `RunProgress`/runtime JSON with `started_at`, `finished_at`, `elapsed_sec`, `done_runs`, `total_runs`, `requested_threads`, `effective_threads`, per-run elapsed time, and completed resume keys

- [ ] **Step 1: Add tests for job matrix and selection policy**

Add:

```python
def test_scope_and_selection_policy_are_bounded():
    assert runner.OUTPUT_PREFIX == "entry_based_amplitude_movement"
    assert runner.SELECTION_POLICY == {
        "winner_metric": "val_select",
        "winner_unit": "seed_aggregate",
        "val_eval": "check_only",
        "low_n_disclosure_2026": "disclosure_only",
        "locked_test": "not_opened",
        "direction_selection": "forbidden",
        "decision_time": "pre_entry_decision",
    }
    jobs = runner.enumerate_jobs()
    assert jobs
    assert all(job["target_family"] == "entry_movement" for job in jobs)
    assert all(job["horizon"] in runner.TARGET_HORIZONS for job in jobs)


def test_config_hash_changes_when_scope_changes():
    base = runner.build_run_config()
    changed = dict(base)
    changed["profiles"] = list(base["profiles"]) + ["new_profile"]
    assert runner.compute_config_hash(base) != runner.compute_config_hash(changed)


def test_make_model_passes_thread_count_to_parallel_estimators():
    model = runner.make_model("extra_trees_small", seed=42, threads=24)

    assert model.n_jobs == 24


def test_progress_json_contains_runtime_and_thread_metadata():
    progress = runner.build_initial_progress(total_runs=7, requested_threads=24, effective_threads=24)

    assert progress["total_runs"] == 7
    assert progress["done_runs"] == 0
    assert progress["requested_threads"] == 24
    assert progress["effective_threads"] == 24
    assert "started_at" in progress
    assert "elapsed_sec" in progress


def test_resume_key_and_completed_run_skip_policy():
    job = {"profile": "atr_only", "model_key": "hist_gradient_boosting", "seed": 42, "horizon": 3, "target_family": "entry_movement"}
    completed = {runner.resume_key(job)}

    assert runner.resume_key(job) == "atr_only/hist_gradient_boosting/42/3/entry_movement"
    assert runner.should_skip_job(job, completed_keys=completed, resume=True) is True
    assert runner.should_skip_job(job, completed_keys=completed, resume=False) is False


def test_aggregate_seed_metrics_uses_median_and_best_simple_baseline():
    rows = [
        {"profile": "atr_only", "model_key": "hist_gradient_boosting", "seed": seed, "horizon": 3, "target_family": "entry_movement", "val_select_spearman": value, "val_eval_spearman": 0.15, "val_select_top10_lift": 1.15, "val_eval_top10_lift": 1.08, "selection_eligible": True, "yearly_check_pass": True}
        for seed, value in zip([42, 43, 44], [0.20, 0.21, 0.19])
    ]
    rows += [
        {"profile": "nearest_k60_sequence_flat", "model_key": "hist_gradient_boosting", "seed": seed, "horizon": 3, "target_family": "entry_movement", "val_select_spearman": value, "val_eval_spearman": eval_value, "val_select_top10_lift": 1.25, "val_eval_top10_lift": 1.12, "val_eval_top10_lift_ci_p05": 1.01, "selection_eligible": True, "yearly_check_pass": True}
        for seed, value, eval_value in zip([42, 43, 44], [0.60, 0.24, 0.26], [0.18, 0.19, -0.01])
    ]

    aggregates = runner.aggregate_seed_metrics(rows)
    complex_row = next(row for row in aggregates if row["profile"] == "nearest_k60_sequence_flat")

    assert complex_row["val_select_spearman_median"] == 0.26
    assert complex_row["best_simple_profile"] == "atr_only"
    assert complex_row["val_eval_positive_seed_count"] == 2
    assert complex_row["beats_best_simple_val_select"] is True
```

- [ ] **Step 2: Implement config, jobs, model factory and run shell**

Add:

```python
SELECTION_POLICY = {
    "winner_metric": "val_select",
    "winner_unit": "seed_aggregate",
    "val_eval": "check_only",
    "low_n_disclosure_2026": "disclosure_only",
    "locked_test": "not_opened",
    "direction_selection": "forbidden",
    "decision_time": "pre_entry_decision",
}

PROFILE_KEYS = (
    "atr_only",
    "time_only_clean",
    "time_plus_atr",
    "distance_to_level_pre_entry_only",
    "fractal_density_only",
    "simple_combined",
    "distance_to_entry_open_post_entry_diagnostic_only",
    "nearest_k60_tabular",
    "nearest_k80_tabular",
    "nearest_k60_no_price_coord_tabular",
    "nearest_k80_no_price_coord_tabular",
    "nearest_k60_sequence_flat",
    "nearest_k80_sequence_flat",
    "nearest_k60_no_time_sequence_flat",
    "nearest_k60_no_price_coord_sequence_flat",
)
MODEL_KEYS = ("ridge_regression", "hist_gradient_boosting", "extra_trees_small")


def build_run_config() -> dict[str, Any]:
    return {
        "schema_version": AMPLITUDE_MOVEMENT_SCHEMA_VERSION,
        "profiles": PROFILE_KEYS,
        "models": MODEL_KEYS,
        "seeds": SEEDS,
        "horizons": TARGET_HORIZONS,
        "target_family": "entry_movement",
        "target_unit_contract": TARGET_UNIT_CONTRACT,
        "selection_policy": SELECTION_POLICY,
        "split_policy": {
            "train": "<=2020",
            "validation": "2021-2025 split into val_select/val_eval",
            "low_n_disclosure": "2026 disclosure_only",
            "locked_test": "not_opened",
            "embargo_hours": max(TARGET_HORIZONS),
        },
        "output_prefix": OUTPUT_PREFIX,
    }


def compute_config_hash(config: dict[str, Any]) -> str:
    payload = json.dumps(config, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def enumerate_jobs() -> list[dict[str, Any]]:
    jobs: list[dict[str, Any]] = []
    for profile, model_key, seed, horizon in product(PROFILE_KEYS, MODEL_KEYS, SEEDS, TARGET_HORIZONS):
        if model_key == "ridge_regression" and profile not in SIMPLE_PROFILES:
            continue
        jobs.append(
            {
                "profile": profile,
                "model_key": model_key,
                "seed": seed,
                "horizon": horizon,
                "target_family": "entry_movement",
            }
        )
    return jobs


def make_model(model_key: str, seed: int, threads: int):
    if model_key == "ridge_regression":
        return Ridge(alpha=1.0)
    if model_key == "hist_gradient_boosting":
        return HistGradientBoostingRegressor(max_iter=250, learning_rate=0.04, l2_regularization=0.05, random_state=seed)
    if model_key == "extra_trees_small":
        return ExtraTreesRegressor(n_estimators=240, max_depth=10, min_samples_leaf=20, random_state=seed, n_jobs=threads)
    raise ValueError(f"Unknown model_key: {model_key}")


def resolve_effective_threads(requested_threads: int | None, parallel_workers: int = 1) -> int:
    default_threads = 24
    threads = int(requested_threads or default_threads)
    if parallel_workers > 1:
        threads = max(1, threads // parallel_workers)
    return max(1, threads)


def resume_key(job: dict[str, Any]) -> str:
    return f"{job['profile']}/{job['model_key']}/{job['seed']}/{job['horizon']}/{job['target_family']}"


def should_skip_job(job: dict[str, Any], completed_keys: set[str], resume: bool) -> bool:
    return bool(resume and resume_key(job) in completed_keys)


def build_initial_progress(total_runs: int, requested_threads: int, effective_threads: int) -> dict[str, Any]:
    return {
        "started_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "finished_at": None,
        "elapsed_sec": 0.0,
        "done_runs": 0,
        "total_runs": int(total_runs),
        "requested_threads": int(requested_threads),
        "effective_threads": int(effective_threads),
        "completed_keys": [],
    }
```

- [ ] **Step 3: Implement split loading by reusing the powerful-tabular split contract**

Add:

```python
def load_entry_based_splits() -> dict[str, pd.DataFrame]:
    old_splits = powerful._add_h24_targets_if_missing(closeout.base.load_entry_based_splits(target_mode="rebuilt"))
    splits = powerful._convert_splits(old_splits)
    role_splits = powerful._split_validation_roles(splits["validation"])
    splits.update(role_splits)
    return powerful.apply_horizon_embargo(splits, max_horizon_hours=max(TARGET_HORIZONS))
```

Do not change split dates. This plan intentionally reuses the exact helper chain from `benchmark_entry_based_powerful_tabular.py` so the movement audit stays comparable to the powerful-tabular and sequence stages.

- [ ] **Step 4: Implement training/evaluation loop**

Add implementation that:

1. Loads splits.
2. Builds train thresholds with `build_movement_targets(splits["train"])`.
3. Reuses those thresholds for validation/disclosure.
4. Builds feature profile per split.
5. Fits a train-only `RobustScaler` for input features.
6. Fits each model on `train`.
7. Predicts `val_select`, `val_eval`, `low_n_disclosure`.
8. Writes metrics rows with profile/model/seed/horizon/split Spearman.
9. Writes quantile lift rows for top 5/10/20%.
10. Writes yearly rows for 2021-2025.
11. Writes target distribution rows for p50/p80/p90/p95.
12. Writes seed aggregate rows grouped by profile/model/horizon/target_family.
13. Resolves requested/effective thread count before model creation and records it in top-level `progress`, `run_config`, and every run record.
14. Prints heartbeat before/after preflight and for every run start/end with `done_runs/total_runs`, `elapsed_sec`, and ETA when enough run durations exist.
15. Saves JSON after every completed or failed run.
16. On `--resume`, loads completed resume keys and skips them after verifying `run_config_hash`; on `--no-resume`, starts a clean progress state.

Use these output column names exactly:

```text
profile, model_key, seed, horizon, target_family,
val_select_spearman, val_eval_spearman, low_n_disclosure_spearman,
val_select_top10_lift, val_eval_top10_lift,
post_entry_diagnostic_only, selection_eligible,
yearly_check_pass, selected_by,
resume_key, requested_threads, effective_threads,
started_at, finished_at, elapsed_sec, status
```

Use these seed-aggregate output column names exactly:

```text
profile, model_key, horizon, target_family, deterministic, n_seeds,
val_select_spearman_median, val_select_spearman_mean, val_select_spearman_std,
val_select_spearman_min, val_select_spearman_max,
val_eval_spearman_median, val_eval_spearman_mean, val_eval_spearman_std,
val_eval_spearman_min, val_eval_spearman_max,
val_eval_positive_seed_count,
val_select_top10_lift_median, val_eval_top10_lift_median,
val_eval_top10_lift_pass_seed_count,
best_simple_profile, best_simple_model_key,
best_simple_val_select_spearman_median, best_simple_val_eval_spearman_median,
beats_best_simple_val_select, beats_best_simple_val_eval,
post_entry_diagnostic_only, selection_eligible,
yearly_check_pass, selected_by
```

Implement aggregate helper:

```python
SIMPLE_BASELINE_PROFILES = {
    "atr_only",
    "time_only_clean",
    "time_plus_atr",
    "distance_to_level_pre_entry_only",
    "fractal_density_only",
    "simple_combined",
}


def _float_values(rows: list[dict[str, Any]], key: str) -> np.ndarray:
    values = [float(row[key]) for row in rows if key in row and np.isfinite(float(row[key]))]
    return np.asarray(values, dtype=float)


def _nanmin_or_nan(values: list[object]) -> float:
    numeric = [float(value) for value in values if value is not None and np.isfinite(float(value))]
    return float(np.min(numeric)) if numeric else float("nan")


def aggregate_seed_metrics(metric_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, int, str], list[dict[str, Any]]] = {}
    for row in metric_rows:
        key = (str(row["profile"]), str(row["model_key"]), int(row["horizon"]), str(row["target_family"]))
        grouped.setdefault(key, []).append(row)

    aggregates: list[dict[str, Any]] = []
    by_horizon_simple: dict[int, dict[str, Any]] = {}
    for (profile, model_key, horizon, target_family), rows in grouped.items():
        val_select = _float_values(rows, "val_select_spearman")
        val_eval = _float_values(rows, "val_eval_spearman")
        select_lift = _float_values(rows, "val_select_top10_lift")
        eval_lift = _float_values(rows, "val_eval_top10_lift")
        deterministic = all(bool(row.get("deterministic", False)) for row in rows)
        aggregate = {
            "profile": profile,
            "model_key": model_key,
            "horizon": horizon,
            "target_family": target_family,
            "deterministic": deterministic,
            "n_seeds": int(len({row.get("seed") for row in rows})),
            "val_select_spearman_median": float(np.median(val_select)) if len(val_select) else float("nan"),
            "val_select_spearman_mean": float(np.mean(val_select)) if len(val_select) else float("nan"),
            "val_select_spearman_std": float(np.std(val_select, ddof=0)) if len(val_select) else float("nan"),
            "val_select_spearman_min": float(np.min(val_select)) if len(val_select) else float("nan"),
            "val_select_spearman_max": float(np.max(val_select)) if len(val_select) else float("nan"),
            "val_eval_spearman_median": float(np.median(val_eval)) if len(val_eval) else float("nan"),
            "val_eval_spearman_mean": float(np.mean(val_eval)) if len(val_eval) else float("nan"),
            "val_eval_spearman_std": float(np.std(val_eval, ddof=0)) if len(val_eval) else float("nan"),
            "val_eval_spearman_min": float(np.min(val_eval)) if len(val_eval) else float("nan"),
            "val_eval_spearman_max": float(np.max(val_eval)) if len(val_eval) else float("nan"),
            "val_eval_positive_seed_count": int(np.sum(val_eval > 0.0)) if len(val_eval) else 0,
            "val_select_top10_lift_median": float(np.median(select_lift)) if len(select_lift) else float("nan"),
            "val_eval_top10_lift_median": float(np.median(eval_lift)) if len(eval_lift) else float("nan"),
            "val_eval_top10_lift_pass_seed_count": int(np.sum(eval_lift >= 1.10)) if len(eval_lift) else 0,
            "val_eval_top10_lift_ci_p05": _nanmin_or_nan([row.get("val_eval_top10_lift_ci_p05") for row in rows]),
            "post_entry_diagnostic_only": any(bool(row.get("post_entry_diagnostic_only", False)) for row in rows),
            "selection_eligible": all(bool(row.get("selection_eligible", True)) for row in rows),
            "yearly_check_pass": all(bool(row.get("yearly_check_pass", False)) for row in rows),
            "selected_by": "val_select_seed_median",
        }
        aggregates.append(aggregate)
        if profile in SIMPLE_BASELINE_PROFILES and aggregate["selection_eligible"]:
            current = by_horizon_simple.get(horizon)
            if current is None or aggregate["val_select_spearman_median"] > current["val_select_spearman_median"]:
                by_horizon_simple[horizon] = aggregate

    for aggregate in aggregates:
        simple = by_horizon_simple.get(int(aggregate["horizon"]))
        if simple is None:
            aggregate.update(
                {
                    "best_simple_profile": None,
                    "best_simple_model_key": None,
                    "best_simple_val_select_spearman_median": float("nan"),
                    "best_simple_val_eval_spearman_median": float("nan"),
                    "beats_best_simple_val_select": False,
                    "beats_best_simple_val_eval": False,
                }
            )
            continue
        aggregate.update(
            {
                "best_simple_profile": simple["profile"],
                "best_simple_model_key": simple["model_key"],
                "best_simple_val_select_spearman_median": simple["val_select_spearman_median"],
                "best_simple_val_eval_spearman_median": simple["val_eval_spearman_median"],
                "beats_best_simple_val_select": aggregate["val_select_spearman_median"] - simple["val_select_spearman_median"] >= 0.03,
                "beats_best_simple_val_eval": aggregate["val_eval_spearman_median"] - simple["val_eval_spearman_median"] >= 0.02,
            }
        )
    return aggregates
```

- [ ] **Step 5: Run focused tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_amplitude_movement.py -q
```

Expected: pass.

- [ ] **Step 6: Leave changes uncommitted until closure**

Do not commit this task separately. Keep the working tree changes for the stage-level closeout handled by `stage-reporting`.

## Task 4: Audit Policy, Verdict And Report JSON

**Files:**
- Modify: `tests/test_entry_based_amplitude_movement.py`
- Modify: `ML/baseline/benchmark_entry_based_amplitude_movement.py`

**Interfaces:**
- Produces: `decide_verdict(report: dict[str, Any]) -> str`
- Produces: top-level JSON fields `schema_version`, `verdict`, `selection_policy`, `normalization_contract`, `target_contract`, `target_unit_contract`, `decision_time`, `feature_audit`, `seed_aggregate`, `target_distribution`, `summary`

- [ ] **Step 1: Add tests for aggregate-based verdict and selection exclusions**

Add:

```python
def test_verdict_uses_seed_aggregate_not_best_single_seed_or_2026():
    report = {
        "seed_aggregate": [
            {
                "profile": "nearest_k60_sequence_flat",
                "model_key": "hist_gradient_boosting",
                "horizon": 3,
                "target_family": "entry_movement",
                "deterministic": False,
                "n_seeds": 3,
                "val_select_spearman_median": 0.31,
                "val_eval_spearman_median": 0.20,
                "low_n_disclosure_spearman": -0.99,
                "val_eval_positive_seed_count": 2,
                "val_select_top10_lift_median": 1.25,
                "val_eval_top10_lift_median": 1.12,
                "val_eval_top10_lift_pass_seed_count": 2,
                "val_eval_top10_lift_ci_p05": 1.01,
                "best_simple_val_select_spearman_median": 0.20,
                "best_simple_val_eval_spearman_median": 0.15,
                "beats_best_simple_val_select": True,
                "beats_best_simple_val_eval": True,
                "yearly_check_pass": True,
                "selection_eligible": True,
                "post_entry_diagnostic_only": False,
            }
        ],
        "feature_audit": {"status": "PASS", "errors": []},
        "target_unit_contract": {"verdict": "PASS"},
    }
    assert runner.decide_verdict(report) == "MOVEMENT_REGIME_TRACE_FOUND"


def test_best_single_seed_does_not_drive_verdict():
    report = {
        "metrics": [
            {
                "profile": "nearest_k60_sequence_flat",
                "model_key": "hist_gradient_boosting",
                "seed": 42,
                "horizon": 3,
                "target_family": "entry_movement",
                "val_select_spearman": 0.60,
                "val_eval_spearman": 0.30,
            }
        ],
        "seed_aggregate": [],
        "feature_audit": {"status": "PASS", "errors": []},
        "target_unit_contract": {"verdict": "PASS"},
    }
    assert runner.decide_verdict(report) == "REJECT_MOVEMENT_REGIME"


def test_best_simple_baseline_matching_complex_explains_amplitude():
    report = {
        "seed_aggregate": [
            {
                "profile": "nearest_k60_sequence_flat",
                "model_key": "hist_gradient_boosting",
                "horizon": 3,
                "target_family": "entry_movement",
                "deterministic": False,
                "n_seeds": 3,
                "val_select_spearman_median": 0.31,
                "val_eval_spearman_median": 0.20,
                "val_eval_positive_seed_count": 3,
                "val_select_top10_lift_median": 1.25,
                "val_eval_top10_lift_median": 1.12,
                "val_eval_top10_lift_pass_seed_count": 3,
                "val_eval_top10_lift_ci_p05": 1.03,
                "best_simple_val_select_spearman_median": 0.30,
                "best_simple_val_eval_spearman_median": 0.19,
                "beats_best_simple_val_select": False,
                "beats_best_simple_val_eval": False,
                "yearly_check_pass": True,
                "selection_eligible": True,
                "post_entry_diagnostic_only": False,
            }
        ],
        "feature_audit": {"status": "PASS", "errors": []},
        "target_unit_contract": {"verdict": "PASS"},
    }
    assert runner.decide_verdict(report) == "AMPLITUDE_EXPLAINED_BY_SIMPLE_BASELINES"


def test_post_entry_diagnostic_profile_cannot_win():
    report = {
        "seed_aggregate": [
            {
                "profile": "distance_to_entry_open_post_entry_diagnostic_only",
                "model_key": "hist_gradient_boosting",
                "horizon": 3,
                "target_family": "entry_movement",
                "deterministic": False,
                "n_seeds": 3,
                "val_select_spearman_median": 0.80,
                "val_eval_spearman_median": 0.70,
                "val_eval_positive_seed_count": 3,
                "val_select_top10_lift_median": 1.60,
                "val_eval_top10_lift_median": 1.50,
                "val_eval_top10_lift_pass_seed_count": 3,
                "val_eval_top10_lift_ci_p05": 1.20,
                "best_simple_val_select_spearman_median": 0.10,
                "best_simple_val_eval_spearman_median": 0.10,
                "beats_best_simple_val_select": True,
                "beats_best_simple_val_eval": True,
                "yearly_check_pass": True,
                "selection_eligible": False,
                "post_entry_diagnostic_only": True,
            }
        ],
        "feature_audit": {"status": "PASS", "errors": []},
        "target_unit_contract": {"verdict": "PASS"},
    }
    assert runner.decide_verdict(report) == "REJECT_MOVEMENT_REGIME"
```

- [ ] **Step 2: Implement verdict policy**

Add:

```python
FORBIDDEN_VERDICTS = {"CANDIDATE", "FROZEN", "READY_FOR_LOCKED_TEST", "DIRECTION_FOUND", "TRADING_RULE_FOUND"}


def decide_verdict(report: dict[str, Any]) -> str:
    audit = report.get("feature_audit", {})
    if audit.get("status") == "ERROR" or audit.get("errors"):
        return "ABORT_CONTRACT_FAIL"
    target_contract = report.get("target_unit_contract", {})
    if target_contract.get("verdict", "PASS") != "PASS":
        return "ABORT_CONTRACT_FAIL"
    aggregates = [
        row
        for row in report.get("seed_aggregate", [])
        if row.get("target_family") == "entry_movement"
        and bool(row.get("selection_eligible", True))
        and not bool(row.get("post_entry_diagnostic_only", False))
    ]
    if not aggregates:
        return "REJECT_MOVEMENT_REGIME"
    best = max(aggregates, key=lambda row: float(row.get("val_select_spearman_median", float("-inf"))))
    select = float(best.get("val_select_spearman_median", float("nan")))
    eval_score = float(best.get("val_eval_spearman_median", float("nan")))
    top10_select = float(best.get("val_select_top10_lift_median", float("nan")))
    top10_eval = float(best.get("val_eval_top10_lift_median", float("nan")))
    top10_eval_ci_p05 = float(best.get("val_eval_top10_lift_ci_p05", float("nan")))
    deterministic = bool(best.get("deterministic", False))
    seed_gate = deterministic or (
        int(best.get("n_seeds", 0)) == 3
        and int(best.get("val_eval_positive_seed_count", 0)) >= 2
        and int(best.get("val_eval_top10_lift_pass_seed_count", 0)) >= 2
    )
    beats_simple = bool(best.get("beats_best_simple_val_select", False)) and bool(best.get("beats_best_simple_val_eval", False))
    movement_gate = (
        select >= 0.25
        and eval_score >= 0.15
        and top10_select >= 1.20
        and top10_eval >= 1.10
        and top10_eval_ci_p05 >= 1.00
        and seed_gate
        and bool(best.get("yearly_check_pass", False))
    )
    if movement_gate and beats_simple:
        return "MOVEMENT_REGIME_TRACE_FOUND"
    if movement_gate and not beats_simple:
        return "AMPLITUDE_EXPLAINED_BY_SIMPLE_BASELINES"
    return "REJECT_MOVEMENT_REGIME"
```

- [ ] **Step 3: Add feature audit for price-coordinate tails**

Implement `audit_feature_frame(profile, split_name, features)` that writes rows:

```text
profile, split, feature, family, rate, decision
```

Rules:

- `TAIL_GT10` if `abs(value) > 10` rate is above `0.05`;
- decision is `requires_no_price_coord_comparison` for any feature containing `price_coord`;
- decision is `accept_as_warning` only for non-coordinate diagnostic tails;
- status is `ERROR` only for NaN/inf or missing required profile.

- [ ] **Step 4: Run tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_amplitude_movement.py -q
```

Expected: pass.

- [ ] **Step 5: Leave changes uncommitted until closure**

Do not commit this task separately. Keep the working tree changes for the stage-level closeout handled by `stage-reporting`.

## Task 5: Execute Clean Run

**Files:**
- Generated: `ML/reports/entry_based_amplitude_movement.*`

**Interfaces:**
- Consumes: runner CLI
- Produces: complete JSON/CSV artifacts

- [ ] **Step 1: Run focused tests before full run**

```bash
./.venv/bin/python -m pytest tests/test_entry_based_amplitude_movement.py -q
```

Expected: all tests pass.

- [ ] **Step 2: Start clean run**

```bash
./.venv/bin/python ML/baseline/benchmark_entry_based_amplitude_movement.py \
  --entry-based-amplitude-movement --no-resume --threads 24
```

Expected:

- JSON is created at `ML/reports/entry_based_amplitude_movement.json`;
- `progress.done_runs == progress.total_runs`;
- `progress.started_at`, `progress.finished_at` and `progress.elapsed_sec` are present;
- `progress.requested_threads == 24` and `progress.effective_threads >= 24` unless the run explicitly records parallel-worker reduction;
- `failed_runs == []` or failures are explicitly listed without hiding completed runs.

- [ ] **Step 3: Inspect artifacts**

Run:

```bash
./.venv/bin/python - <<'PY'
import json, pathlib, pandas as pd
p = pathlib.Path("ML/reports/entry_based_amplitude_movement.json")
d = json.loads(p.read_text())
print("verdict", d.get("verdict"))
print("progress", d.get("progress"))
print("failed", len(d.get("failed_runs", [])))
print("summary", d.get("summary"))
print("runtime", {k: d.get("progress", {}).get(k) for k in ["started_at", "finished_at", "elapsed_sec", "requested_threads", "effective_threads"]})
for name in ["metrics", "seed_aggregate", "quantiles", "yearly", "target_distribution", "feature_audit"]:
    path = pathlib.Path(f"ML/reports/entry_based_amplitude_movement_{name}.csv")
    print(path, pd.read_csv(path).shape if path.exists() else "MISSING")
PY
```

Expected:

- no missing required CSV;
- summary selected aggregate matches `seed_aggregate` CSV;
- selected aggregate is not `post_entry_diagnostic_only`;
- runtime fields are present and non-null after completion;
- each completed run row has `resume_key`, `status=completed`, `started_at`, `finished_at`, `elapsed_sec`, `requested_threads`, and `effective_threads`;
- verdict is one of the allowed verdicts.

- [ ] **Step 4: Leave generated artifacts uncommitted until closure**

CSV/log files may be ignored by `.gitignore`; do not force-add or commit them inside this task. Record the final artifact list in the report and let `stage-reporting` handle the stage-level git closeout.

## Task 6: Report, Docs And Wiki Closure

**Files:**
- Create: `docs/reports/YYYY-MM-DD-entry-based-amplitude-movement-regime.md`
- Create: `docs/ML/benchmark_entry_based_amplitude_movement.py.md`
- Modify: `CHANGELOG.md`
- Modify: `CONTEXT_HANDOFF.md`
- Modify: `docs/tests/tests.md`
- Modify: `MODULE_INDEX.md`
- Modify: `wiki/research/fractal-stop-research.md`
- Modify: `wiki/index.md`
- Modify: `wiki/log.md`
- Modify: `wiki/REPO_integrity.md`

**Interfaces:**
- Consumes: final JSON/CSV artifacts
- Produces: canonical report and updated project navigation

- [ ] **Step 1: Write report with required sections**

Use `docs/reports/README.md` and `docs/methodology/16-reporting-audit.md`.

Report must include:

- `Context`;
- `Уровень этапа`;
- `What Was Done`;
- `Multiple Testing Context`;
- `Validation Split Disclosure`;
- `Target Contract`;
- `Feature / Tail Audit`;
- `Changed Files`;
- `Verification`;
- `Results`;
- `Conclusions`;
- `Limitations / Open Questions`;
- `Next Step`;
- `Related Materials`.

Required tables:

- target distribution p50/p80/p90/p95 by split and horizon;
- simple baselines vs complex selected aggregates;
- explanation table: `ATR`, time, `time_plus_atr`, pre-entry distance, density, `simple_combined`, and best complex aggregate;
- selected aggregate by median `val_select`;
- seed spread table: median/mean/std/min/max and positive seed counts;
- best-by-`val_eval` disclosure-only rows;
- quantile lift top 5/10/20% with `top_n`, `rest_n`, `lift_ci_p05`, `lift_ci_p50`, `lift_ci_p95`;
- yearly metrics 2021-2025;
- no-price-coordinate comparison;
- no-time comparison;
- post-entry distance diagnostic clearly marked selection-forbidden;
- feature-audit warnings and decisions.

- [ ] **Step 2: Write module docs**

Create `docs/ML/benchmark_entry_based_amplitude_movement.py.md` with:

- purpose;
- CLI;
- target contract;
- feature profiles;
- output artifacts;
- fairness rules;
- tests.

- [ ] **Step 3: Update navigation**

Update:

- `CHANGELOG.md` with fixed fields;
- `CONTEXT_HANDOFF.md` as current state, not historical append;
- `docs/tests/tests.md` with focused test command;
- `MODULE_INDEX.md` with runner/test docs rows.

- [ ] **Step 4: Wiki ingest**

Run:

```bash
./.venv/bin/python wiki/wiki.py status
./.venv/bin/python wiki/wiki.py generate
./.venv/bin/python wiki/wiki.py status
```

Expected final status:

```text
Wiki is up to date. No gaps found.
```

- [ ] **Step 5: Final verification**

Run:

```bash
./.venv/bin/python -m pytest tests/test_entry_based_amplitude_movement.py -q
./.venv/bin/python -m pytest tests/ -q
git diff --check
```

Expected:

- focused tests pass;
- full tests pass;
- `git diff --check` prints no errors.

- [ ] **Step 6: Stage-reporting closeout**

Use the `stage-reporting` skill after verification to decide whether to commit all code, artifacts, report, docs and wiki updates together. Do not create task-level commits before that closeout.

---

## Out Of Scope For This Plan

These items are important but must not be mixed into this audit:

- new fractal-price entry mechanics;
- limit/retest/touch entry labels;
- direction inside movement regimes;
- trade simulation with spread/slippage;
- EURUSD or cross-pair validation;
- `locked_test`;
- Transformer rerun for amplitude before flat/simple baselines survive controls.

They are tracked in `docs/superpowers/roadmap.md`.

## Self-Review Checklist

- The plan includes simple baselines before complex models.
- The plan includes `time_only_clean`, `no_time_sequence` equivalent, and no-price-coordinate checks.
- The plan includes `time_plus_atr` and compares complex profiles to the best simple baseline, not only to `simple_combined`.
- The plan fixes `decision_time=pre_entry_decision` and forbids `entry_open` as a selection-eligible input.
- The plan treats `distance_to_entry_open_post_entry_diagnostic_only` as disclosure-only.
- The plan selects seed aggregates by median `val_select`, not a best single seed.
- The plan never selects direction.
- The plan never uses 2026 for selection.
- The plan does not open `locked_test`.
- The plan includes quantile movement analysis with sample sizes and block-bootstrap confidence intervals.
- The plan includes target-distribution p50/p80/p90/p95 by split.
- The plan includes yearly checks.
- The plan treats `price_coord_atr` tails as a serious follow-up risk.
- The plan routes new entry mechanics and direction revival to roadmap, not this audit.
