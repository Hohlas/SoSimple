# Regression Up/Dn Already Moved Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Measure how much of the apparent `Regression Up/Dn` success is explained by price movement already completed between `fractal0_price` and the possible entry price, rather than by prediction of future movement after entry.

**Architecture:** Add one narrow diagnostic script that reuses the winning `Regression Up/Dn target foundation` setup, reconstructs `up_h/dn_h` timing from OHLC, denormalizes real and predicted `up/dn`, and writes row-level plus summary artifacts. The stage is pure EDA: no spread, no PF, no Stop/Profit, no trading gate.

**Tech Stack:** Python 3.10+, pandas, numpy, scipy, sklearn/XGBoost through existing `ML/baseline/benchmark_regression_updn_target_foundation.py`, existing `./.venv/bin/python`, existing `DATA/Nero_XAUUSD_*_labeled.csv`, existing `DATA/XAUUSD_H1_OHLC.csv`.

## Global Constraints

- Work on the current branch; do not use git worktree.
- Use `./.venv/bin/python` for all Python commands.
- Use project CSV delimiter `;`.
- Do not load large CSV files without `usecols`, `nrows`, or split-aware reads unless an existing runner already does it.
- This stage is `DIAGNOSTIC_ONLY`.
- Do not compute PF, spread, Stop/Profit, trade PnL, or trading pass/fail.
- Do not use `diagnostic_holdout` or 2026 to choose thresholds or rules.
- Primary analysis split is `val_stop=2021-2022`.
- `diagnostic_holdout=2023-2025` may be reported only as disclosure.
- `low_n_disclosure=2026` may be reported only as low-N disclosure.
- Primary profile/model are fixed from foundation: `structure_full` + `xgboost_depth3`.
- Primary horizons are fixed to `H3`, `H6`, `H12`; `H24/H48` are optional disclosure only if runtime remains reasonable.
- Denormalize `up/dn` only through the project contract in `processing/denormalize_updn.py`: per-row `*_updn_params.npy` with shape `(N, 5, 2)`, matched to the original source CSV by row position and checked by `time`.
- Before interpreting movement numbers, run a bounded label-window preflight over a fixed `start_offset` set, choose the first convention that matches CSV `up_h/dn_h` after denormalization, then freeze that convention for the audit. If no convention matches, stop with `LABEL_WINDOW_CONTRACT_FAILED`.
- The report must answer plainly: "How much of `actual_up_h/actual_dn_h` was already present before possible entry?"
- The report must separately answer: "Does `pred_up_h/pred_dn_h` still match the residual movement after possible entry?"
- Final report must avoid presenting the old deleted trading confirmation as evidence.

---

## Research Contract

**Main question:** If the model predicts `up_h/dn_h` well from `fractal0_price`, is that because price already moved from `fractal0_price` before entry?

**Definitions:**

- `fractal0_price`: price field inside `fractal0`.
- `signal_time`: top-level row `time`.
- `entry_time`: first H1 OHLC bar strictly after `signal_time`.
- `entry_open`: OHLC `open` at `entry_time`.
- `already_up`: `max(entry_open - fractal0_price, 0)`.
- `already_dn`: `max(fractal0_price - entry_open, 0)`.
- `actual_up_h`: real `up_h` converted back to price units.
- `actual_dn_h`: real `dn_h` converted back to price units.
- `already_up_share_h`: `already_up / actual_up_h` when `actual_up_h > 0`.
- `already_dn_share_h`: `already_dn / actual_dn_h` when `actual_dn_h > 0`.
- `pred_residual_up_h_by_subtraction`: `max(pred_up_h - already_up, 0)`.
- `pred_residual_dn_h_by_subtraction`: `max(pred_dn_h - already_dn, 0)`.
- `actual_residual_up_h_by_subtraction`: `max(actual_up_h - already_up, 0)`.
- `actual_residual_dn_h_by_subtraction`: `max(actual_dn_h - already_dn, 0)`.
- `future_up_from_entry_h`: highest high in the remaining label window after `entry_time`, measured from `entry_open`.
- `future_dn_from_entry_h`: lowest low in the remaining label window after `entry_time`, measured from `entry_open`.
- `actual_log_ratio_h`: `log1p(actual_up_h) - log1p(actual_dn_h)`.
- `pred_log_ratio_h`: `log1p(pred_up_h) - log1p(pred_dn_h)`.
- `pred_residual_log_ratio_h`: `log1p(pred_residual_up_h_by_subtraction) - log1p(pred_residual_dn_h_by_subtraction)`.
- `actual_residual_log_ratio_h`: `log1p(actual_residual_up_h_by_subtraction) - log1p(actual_residual_dn_h_by_subtraction)`.
- `future_entry_log_ratio_h`: `log1p(future_up_from_entry_h) - log1p(future_dn_from_entry_h)`.

**Core comparisons:**

1. `pred_log_ratio_h` vs `actual_log_ratio_h`: confirms the original target-level signal.
2. `pred_log_ratio_h` vs `future_entry_log_ratio_h`: main check for whether signal survives after entry.
3. `already_up_share_h` / `already_dn_share_h`: measures how much of the target was already consumed before entry.
4. `pred_residual_log_ratio_h` vs `actual_residual_log_ratio_h`: secondary diagnostic only; checks the subtraction view: predicted remaining move after removing `entry_open - fractal0_price`.
5. `actual_residual_*_by_subtraction` vs `future_*_from_entry_h`: secondary diagnostic only; checks whether subtraction is faithful. If they diverge, prefer direct OHLC future-from-entry values because the original maximum/minimum may have happened before entry.
6. Direction by fractal side:
   - for `dir=-1`, check whether `actual_up_h > actual_dn_h` is mostly explained by positive `already_up`;
   - for `dir=1`, check whether `actual_dn_h > actual_up_h` is mostly explained by positive `already_dn`.

**Result statuses:**

- `PASS_DIAGNOSTIC`: label window verified, artifacts written, report answers the main question.
- `LABEL_WINDOW_CONTRACT_FAILED`: OHLC reconstruction does not match CSV targets closely enough.
- `OHLC_ALIGNMENT_FAILED`: row times, entry times, or OHLC coverage are not reliable.
- `MODEL_REPRO_FAILED`: fixed model setup cannot reproduce enough of foundation metrics to trust predictions.

## File Structure

**Create**

- `ML/baseline/analyze_regression_updn_already_moved_audit.py` - one diagnostic runner.
- `tests/test_regression_updn_already_moved_audit.py` - focused unit tests for parsing, OHLC alignment, movement math, ratio summaries, and report shape.
- `docs/reports/2026-07-02-regression-updn-already-moved-audit.md` - canonical report after execution.

**Generated**

- `ML/reports/regression_updn_already_moved_audit.json`
- `ML/reports/regression_updn_already_moved_audit_rows.csv`

**Read**

- `docs/methodology/05-eda-data-quality.md`
- `docs/methodology/06b-oracle-preflight.md`
- `docs/methodology/12-backtest-costs.md` only to avoid accidentally making backtest claims.
- `ML/baseline/benchmark_regression_updn_target_foundation.py`
- `processing/label_signals.py`
- `processing/denormalize_updn.py`
- `docs/reports/2026-06-30-regression-updn-target-foundation.md`
- `docs/reports/2026-07-01-regression-updn-ratio-audit.md`

---

### Task 1: Skeleton, Config, And Pure Helpers

**Files:**
- Create: `ML/baseline/analyze_regression_updn_already_moved_audit.py`
- Create: `tests/test_regression_updn_already_moved_audit.py`

**Interfaces:**
- Produces `ALREADY_MOVED_JSON_PATH: Path`.
- Produces `ALREADY_MOVED_ROWS_PATH: Path`.
- Produces `AlreadyMovedConfig`.
- Produces `parse_fractal0(fractal_value: object) -> dict | None`.
- Produces `safe_log_ratio(up: np.ndarray, dn: np.ndarray) -> np.ndarray`.
- Produces `movement_from_fractal_to_entry(fractal_price: float, entry_open: float) -> dict`.

- [ ] **Step 1: Write failing helper tests**

Add to `tests/test_regression_updn_already_moved_audit.py`:

```python
import numpy as np

import ML.baseline.analyze_regression_updn_already_moved_audit as audit


def test_parse_fractal0_extracts_time_price_and_direction():
    value = "1700000000:2030.5:-1:0.1:0.2:0:0:0:0.3:1:0.4:1:2:3:4:5:6:0.7:0.8:0.9:1.0:2.5:2"

    parsed = audit.parse_fractal0(value)

    assert parsed == {
        "time": 1700000000,
        "price": 2030.5,
        "direction": -1,
        "shift": 2,
    }


def test_safe_log_ratio_is_finite_for_zero_denominator():
    result = audit.safe_log_ratio(np.array([2.0, 0.0]), np.array([0.0, 3.0]))

    assert np.isfinite(result).all()
    assert result[0] > 0
    assert result[1] < 0


def test_movement_from_fractal_to_entry_separates_up_and_down():
    up = audit.movement_from_fractal_to_entry(fractal_price=100.0, entry_open=103.0)
    down = audit.movement_from_fractal_to_entry(fractal_price=100.0, entry_open=97.5)

    assert up["already_up"] == 3.0
    assert up["already_dn"] == 0.0
    assert down["already_up"] == 0.0
    assert down["already_dn"] == 2.5
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_regression_updn_already_moved_audit.py -q
```

Expected: FAIL because the module does not exist.

- [ ] **Step 3: Add minimal module and helpers**

Create `ML/baseline/analyze_regression_updn_already_moved_audit.py`:

```python
import argparse
import dataclasses
import datetime as dt
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from ML.baseline import benchmark_regression_updn_target_foundation as foundation
from processing.label_signals import parse_fractal


PROJECT_ROOT = foundation.PROJECT_ROOT
REPORTS_DIR = foundation.REPORTS_DIR
DATA_DIR = PROJECT_ROOT / "DATA"
ALREADY_MOVED_JSON_PATH = REPORTS_DIR / "regression_updn_already_moved_audit.json"
ALREADY_MOVED_ROWS_PATH = REPORTS_DIR / "regression_updn_already_moved_audit_rows.csv"
OHLC_PATH = DATA_DIR / "XAUUSD_H1_OHLC.csv"


@dataclasses.dataclass(frozen=True)
class AlreadyMovedConfig:
    profile: str = "structure_full"
    model_key: str = "xgboost_depth3"
    seed: int = 42
    horizons: tuple[int, ...] = (3, 6, 12)
    primary_split: str = "val_stop"
    disclosure_splits: tuple[str, ...] = ("diagnostic_holdout", "low_n_disclosure")
    label_match_abs_tolerance: float = 0.05
    label_match_min_rate: float = 0.98
    label_window_start_offsets: tuple[int, ...] = (0, 1, 2, 3)
    strong_pred_quantile: float = 0.90


CONFIG = AlreadyMovedConfig()


def parse_fractal0(fractal_value: object) -> dict | None:
    parsed = parse_fractal(fractal_value)
    if parsed is None:
        return None
    return {
        "time": int(parsed["time"]),
        "price": float(parsed["price"]),
        "direction": int(parsed["direction"]),
        "shift": int(parsed["shift"]),
    }


def safe_log_ratio(up: np.ndarray, dn: np.ndarray) -> np.ndarray:
    return np.log1p(np.clip(up, 0.0, None)) - np.log1p(np.clip(dn, 0.0, None))


def movement_from_fractal_to_entry(fractal_price: float, entry_open: float) -> dict:
    delta = float(entry_open) - float(fractal_price)
    return {
        "already_up": max(delta, 0.0),
        "already_dn": max(-delta, 0.0),
        "entry_minus_fractal": delta,
    }
```

- [ ] **Step 4: Run tests to verify pass**

Run:

```bash
./.venv/bin/python -m pytest tests/test_regression_updn_already_moved_audit.py -q
```

Expected: PASS.

---

### Task 2: OHLC Alignment And Label Window Verification

**Files:**
- Modify: `ML/baseline/analyze_regression_updn_already_moved_audit.py`
- Modify: `tests/test_regression_updn_already_moved_audit.py`

**Interfaces:**
- Produces `parse_labeled_time(series: pd.Series) -> pd.Series`.
- Produces `load_ohlc(path: Path = OHLC_PATH) -> pd.DataFrame`.
- Produces `attach_entry_open(rows: pd.DataFrame, ohlc: pd.DataFrame) -> tuple[pd.DataFrame, dict]`.
- Produces `reconstruct_window_moves(rows: pd.DataFrame, ohlc: pd.DataFrame, horizon: int, start_offset: int) -> pd.DataFrame`.
- Produces `verify_label_window(rows: pd.DataFrame, ohlc: pd.DataFrame, horizon: int) -> dict`.

- [ ] **Step 1: Write failing alignment tests**

Append:

```python
import pandas as pd


def test_attach_entry_open_uses_first_bar_after_signal_time():
    rows = pd.DataFrame({
        "time": ["2021.01.01 10:00"],
        "fractal0": ["1609491600:100.0:-1:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:1.0:2"],
    })
    ohlc = pd.DataFrame({
        "time": pd.to_datetime(["2021.01.01 10:00", "2021.01.01 11:00"]),
        "open": [101.0, 102.0],
        "high": [102.0, 103.0],
        "low": [99.0, 101.0],
        "close": [101.5, 102.5],
    })

    enriched, report = audit.attach_entry_open(rows, ohlc)

    assert report["missing_entry_open"] == 0
    assert enriched.loc[0, "entry_time"] == pd.Timestamp("2021.01.01 11:00")
    assert enriched.loc[0, "entry_open"] == 102.0


def test_reconstruct_window_moves_measures_from_fractal_price():
    rows = pd.DataFrame({
        "time": ["2021.01.01 10:00"],
        "fractal0_price": [100.0],
        "fractal0_time": [pd.Timestamp("2021.01.01 09:00")],
    })
    ohlc = pd.DataFrame({
        "time": pd.to_datetime([
            "2021.01.01 09:00", "2021.01.01 10:00",
            "2021.01.01 11:00", "2021.01.01 12:00",
        ]),
        "open": [100.0, 101.0, 102.0, 101.0],
        "high": [101.0, 103.0, 104.0, 102.0],
        "low": [99.0, 100.5, 101.5, 98.0],
        "close": [100.5, 102.0, 102.5, 99.0],
    })

    result = audit.reconstruct_window_moves(rows, ohlc, horizon=3, start_offset=1)

    assert result.loc[0, "reconstructed_up_3"] == 4.0
    assert result.loc[0, "reconstructed_dn_3"] == 2.0
    assert result.loc[0, "bars_in_window_3"] == 3
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_regression_updn_already_moved_audit.py -q
```

Expected: FAIL because alignment functions are missing.

- [ ] **Step 3: Implement alignment and reconstruction**

Add:

```python
def parse_labeled_time(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, format="%Y.%m.%d %H:%M", errors="coerce")


def load_ohlc(path: Path = OHLC_PATH) -> pd.DataFrame:
    ohlc = pd.read_csv(
        path,
        sep=";",
        usecols=["time", "open", "high", "low", "close"],
    )
    ohlc["time"] = pd.to_datetime(ohlc["time"], format="%Y.%m.%d %H:%M", errors="coerce")
    ohlc = ohlc.dropna(subset=["time"]).sort_values("time").drop_duplicates("time")
    return ohlc.reset_index(drop=True)


def _add_fractal0_columns(rows: pd.DataFrame) -> pd.DataFrame:
    out = rows.copy()
    parsed = out["fractal0"].map(parse_fractal0)
    out["fractal0_time_unix"] = parsed.map(lambda x: x["time"] if x else np.nan)
    out["fractal0_time"] = pd.to_datetime(out["fractal0_time_unix"], unit="s", errors="coerce")
    out["fractal0_price"] = parsed.map(lambda x: x["price"] if x else np.nan)
    out["fractal0_direction"] = parsed.map(lambda x: x["direction"] if x else np.nan)
    out["fractal0_shift"] = parsed.map(lambda x: x["shift"] if x else np.nan)
    out["signal_time"] = parse_labeled_time(out["time"])
    return out


def attach_entry_open(rows: pd.DataFrame, ohlc: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    out = _add_fractal0_columns(rows)
    entry = ohlc.loc[:, ["time", "open"]].rename(columns={"time": "entry_time", "open": "entry_open"})
    out["entry_time"] = out["signal_time"] + pd.Timedelta(hours=1)
    out = out.merge(entry, on="entry_time", how="left")
    report = {
        "rows": int(len(out)),
        "missing_signal_time": int(out["signal_time"].isna().sum()),
        "missing_fractal0": int(out["fractal0_price"].isna().sum()),
        "missing_entry_open": int(out["entry_open"].isna().sum()),
        "entry_match_rate": float(out["entry_open"].notna().mean()) if len(out) else 0.0,
    }
    return out, report


def reconstruct_window_moves(rows: pd.DataFrame, ohlc: pd.DataFrame, horizon: int, start_offset: int) -> pd.DataFrame:
    values = []
    indexed = ohlc.set_index("time", drop=False)
    for row in rows.itertuples(index=False):
        start_time = row.fractal0_time + pd.Timedelta(hours=start_offset)
        end_time = start_time + pd.Timedelta(hours=horizon - 1)
        window = indexed.loc[(indexed.index >= start_time) & (indexed.index <= end_time)]
        if window.empty or pd.isna(row.fractal0_price):
            values.append({
                f"reconstructed_up_{horizon}": np.nan,
                f"reconstructed_dn_{horizon}": np.nan,
                f"bars_in_window_{horizon}": 0,
                f"label_start_time_{horizon}": start_time,
                f"label_end_time_{horizon}": end_time,
            })
            continue
        price = float(row.fractal0_price)
        values.append({
            f"reconstructed_up_{horizon}": max(float(window["high"].max()) - price, 0.0),
            f"reconstructed_dn_{horizon}": max(price - float(window["low"].min()), 0.0),
            f"bars_in_window_{horizon}": int(len(window)),
            f"label_start_time_{horizon}": start_time,
            f"label_end_time_{horizon}": end_time,
        })
    return pd.DataFrame(values)
```

- [ ] **Step 4: Run tests to verify pass**

Run:

```bash
./.venv/bin/python -m pytest tests/test_regression_updn_already_moved_audit.py -q
```

Expected: PASS.

---

### Task 3: Source-Row Denormalization And Prediction Table

**Files:**
- Modify: `ML/baseline/analyze_regression_updn_already_moved_audit.py`
- Modify: `tests/test_regression_updn_already_moved_audit.py`

**Interfaces:**
- Produces `load_split_frames_with_source() -> dict[str, pd.DataFrame]`.
- Produces `load_source_updn_params() -> dict[str, np.ndarray]`.
- Produces `denormalize_updn_matrix(values: np.ndarray, source_split: pd.Series, source_row_idx: pd.Series, params: dict[str, np.ndarray]) -> np.ndarray`.
- Produces `validate_source_row_alignment(source_frames: dict[str, pd.DataFrame], split_frames: dict[str, pd.DataFrame], params: dict[str, np.ndarray]) -> dict`.

- [ ] **Step 1: Write failing denormalization test**

Append:

```python
def test_denormalize_updn_matrix_uses_source_row_params(monkeypatch):
    values = np.array([
        [0.85, 0.425, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.85, 0.425, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    ], dtype=np.float32)
    params = {
        "train": np.array([[[10.0, 20.0]] * 5], dtype=np.float64),
        "validation": np.array([[[100.0, 200.0]] * 5], dtype=np.float64),
    }
    source = pd.Series(["train", "validation"])
    source_row_idx = pd.Series([0, 0])

    out = audit.denormalize_updn_matrix(values, source, source_row_idx, params)

    np.testing.assert_allclose(out[0, :2], [10.0, 5.0])
    np.testing.assert_allclose(out[1, :2], [100.0, 50.0])
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_regression_updn_already_moved_audit.py -q
```

Expected: FAIL because source-row denormalization is missing.

- [ ] **Step 3: Implement source-row denormalization through project helper**

Add:

```python
from processing.denormalize_updn import denormalize_updn_pairs, load_updn_params


def _params_path_for_source(source_name: str) -> Path:
    if source_name == "train":
        return DATA_DIR / "Nero_XAUUSD_train_updn_params.npy"
    if source_name == "validation":
        return DATA_DIR / "Nero_XAUUSD_validation_updn_params.npy"
    if source_name == "test":
        return DATA_DIR / "Nero_XAUUSD_test_updn_params.npy"
    raise ValueError(f"Unknown source split: {source_name}")


def load_source_updn_params() -> dict[str, np.ndarray]:
    return {
        source: load_updn_params(_params_path_for_source(source))
        for source in ("train", "validation", "test")
    }


def denormalize_updn_matrix(
    values: np.ndarray,
    source_split: pd.Series,
    source_row_idx: pd.Series,
    params: dict[str, np.ndarray],
) -> np.ndarray:
    out = np.zeros((len(values), len(foundation.UPDN_TARGET_COLUMNS)), dtype=np.float64)
    source_values = source_split.reset_index(drop=True)
    row_values = source_row_idx.reset_index(drop=True).astype(int)
    for row_idx, source_name in enumerate(source_values):
        source_name = str(source_name)
        original_idx = int(row_values.iloc[row_idx])
        out[row_idx, :] = denormalize_updn_pairs(values[row_idx, :], params[source_name][original_idx])
    return out
```

- [ ] **Step 4: Implement source-aware split loading**

Add:

```python
def _read_labeled_source(path: Path, source_name: str) -> pd.DataFrame:
    df = pd.read_csv(path, sep=";")
    df["source_split"] = source_name
    df["source_row_idx"] = np.arange(len(df), dtype=int)
    return df


def load_source_frames() -> dict[str, pd.DataFrame]:
    return {
        "train": _read_labeled_source(foundation.XAUUSD_SPLIT_FILES["train_core"], "train"),
        "validation": _read_labeled_source(foundation.XAUUSD_SPLIT_FILES["val_stop"], "validation"),
        "test": _read_labeled_source(foundation.XAUUSD_SPLIT_FILES["diagnostic_holdout"], "test"),
    }


def load_split_frames_with_source() -> dict[str, pd.DataFrame]:
    sources = load_source_frames()
    train = sources["train"]
    validation = sources["validation"]
    test = sources["test"]

    train_year = foundation._parse_years(train["time"])
    validation_year = foundation._parse_years(validation["time"])
    test_year = foundation._parse_years(test["time"])

    return {
        "train_core": train.loc[train_year <= foundation.REGRESSION_UPDN_CONFIG.train_max_year].reset_index(drop=True),
        "val_stop": pd.concat(
            [
                train.loc[train_year.isin(foundation.REGRESSION_UPDN_CONFIG.val_years)],
                validation.loc[validation_year.isin(foundation.REGRESSION_UPDN_CONFIG.val_years)],
            ],
            ignore_index=True,
        ),
        "diagnostic_holdout": pd.concat(
            [
                train.loc[train_year.isin(foundation.REGRESSION_UPDN_CONFIG.holdout_years)],
                validation.loc[validation_year.isin(foundation.REGRESSION_UPDN_CONFIG.holdout_years)],
                test.loc[test_year.isin(foundation.REGRESSION_UPDN_CONFIG.holdout_years)],
            ],
            ignore_index=True,
        ),
        "low_n_disclosure": pd.concat(
            [
                train.loc[train_year.isin(foundation.REGRESSION_UPDN_CONFIG.low_n_years)],
                validation.loc[validation_year.isin(foundation.REGRESSION_UPDN_CONFIG.low_n_years)],
                test.loc[test_year.isin(foundation.REGRESSION_UPDN_CONFIG.low_n_years)],
            ],
            ignore_index=True,
        ),
    }


def validate_source_row_alignment(
    source_frames: dict[str, pd.DataFrame],
    split_frames: dict[str, pd.DataFrame],
    params: dict[str, np.ndarray],
) -> dict:
    report = {"status": "PASS", "sources": {}}
    for source_name, frame in source_frames.items():
        n_rows = len(frame)
        n_params = len(params[source_name])
        ok = n_rows == n_params
        report["sources"][source_name] = {
            "csv_rows": int(n_rows),
            "params_rows": int(n_params),
            "row_count_match": bool(ok),
        }
        if not ok:
            report["status"] = "PARAM_ROW_ALIGNMENT_FAILED"
    for split_name, split_frame in split_frames.items():
        mismatches = 0
        for row in split_frame.loc[:, ["time", "source_split", "source_row_idx"]].itertuples(index=False):
            source_frame = source_frames[str(row.source_split)]
            if int(row.source_row_idx) >= len(source_frame):
                mismatches += 1
                continue
            if str(source_frame.iloc[int(row.source_row_idx)]["time"]) != str(row.time):
                mismatches += 1
        report.setdefault("splits", {})[split_name] = {
            "rows": int(len(split_frame)),
            "time_position_mismatches": int(mismatches),
        }
        if mismatches:
            report["status"] = "PARAM_ROW_ALIGNMENT_FAILED"
    return report
```

- [ ] **Step 5: Run tests to verify pass**

Run:

```bash
./.venv/bin/python -m pytest tests/test_regression_updn_already_moved_audit.py -q
```

Expected: PASS.

---

### Task 4: Already-Moved And Residual-Move Metrics

**Files:**
- Modify: `ML/baseline/analyze_regression_updn_already_moved_audit.py`
- Modify: `tests/test_regression_updn_already_moved_audit.py`

**Interfaces:**
- Produces `attach_already_moved_columns(rows: pd.DataFrame, horizons: tuple[int, ...]) -> pd.DataFrame`.
- Produces `attach_future_from_entry_columns(rows: pd.DataFrame, ohlc: pd.DataFrame, horizons: tuple[int, ...]) -> pd.DataFrame`.
- Produces `summarize_already_moved(rows: pd.DataFrame, horizons: tuple[int, ...]) -> dict`.

- [ ] **Step 1: Write failing metric tests**

Append:

```python
def test_attach_already_moved_columns_reports_unclipped_share():
    rows = pd.DataFrame({
        "fractal0_price": [100.0],
        "entry_open": [103.0],
        "actual_up_3_price": [2.0],
        "actual_dn_3_price": [4.0],
        "pred_up_3_price": [5.0],
        "pred_dn_3_price": [1.0],
    })

    out = audit.attach_already_moved_columns(rows, horizons=(3,))

    assert out.loc[0, "already_up"] == 3.0
    assert out.loc[0, "already_dn"] == 0.0
    assert out.loc[0, "already_up_share_3"] == 1.5
    assert out.loc[0, "already_dn_share_3"] == 0.0
    assert out.loc[0, "actual_residual_up_3_by_subtraction"] == 0.0
    assert out.loc[0, "actual_residual_dn_3_by_subtraction"] == 4.0
    assert out.loc[0, "pred_residual_up_3_by_subtraction"] == 2.0
    assert out.loc[0, "pred_residual_dn_3_by_subtraction"] == 1.0


def test_summary_reports_direction_groups():
    rows = pd.DataFrame({
        "fractal0_direction": [-1, -1, 1, 1],
        "already_up_share_3": [0.8, 0.2, 0.0, 0.1],
        "already_dn_share_3": [0.0, 0.1, 0.7, 0.3],
        "pred_log_ratio_3": [2.0, 1.0, -2.0, -1.0],
        "actual_log_ratio_3": [2.1, 0.8, -2.2, -0.9],
        "future_entry_log_ratio_3": [0.1, -0.1, 0.0, 0.2],
        "pred_residual_log_ratio_3": [0.2, 0.1, -0.2, -0.1],
        "actual_residual_log_ratio_3": [0.1, -0.1, -0.1, 0.1],
    })

    summary = audit.summarize_already_moved(rows, horizons=(3,))

    assert "h3" in summary
    assert summary["h3"]["rows"] == 4
    assert summary["h3"]["dir_-1"]["rows"] == 2
    assert summary["h3"]["dir_1"]["rows"] == 2


def test_attach_future_from_entry_columns_measures_remaining_window():
    rows = pd.DataFrame({
        "entry_time": [pd.Timestamp("2021.01.01 11:00")],
        "entry_open": [102.0],
        "label_end_time_3": [pd.Timestamp("2021.01.01 12:00")],
    })
    ohlc = pd.DataFrame({
        "time": pd.to_datetime(["2021.01.01 11:00", "2021.01.01 12:00"]),
        "open": [102.0, 101.0],
        "high": [103.0, 104.0],
        "low": [101.5, 99.0],
        "close": [102.5, 100.0],
    })

    out = audit.attach_future_from_entry_columns(rows, ohlc, horizons=(3,))

    assert out.loc[0, "future_up_from_entry_3"] == 2.0
    assert out.loc[0, "future_dn_from_entry_3"] == 3.0
    assert out.loc[0, "bars_after_entry_3"] == 2


def test_subtraction_residual_can_differ_from_direct_future_move():
    rows = pd.DataFrame({
        "fractal0_price": [100.0],
        "entry_open": [103.0],
        "actual_up_3_price": [5.0],
        "actual_dn_3_price": [1.0],
        "pred_up_3_price": [5.0],
        "pred_dn_3_price": [1.0],
        "entry_time": [pd.Timestamp("2021.01.01 11:00")],
        "label_end_time_3": [pd.Timestamp("2021.01.01 12:00")],
    })
    ohlc = pd.DataFrame({
        "time": pd.to_datetime(["2021.01.01 11:00", "2021.01.01 12:00"]),
        "open": [103.0, 102.0],
        "high": [103.2, 103.1],
        "low": [102.5, 101.0],
        "close": [102.8, 101.5],
    })

    rows = audit.attach_already_moved_columns(rows, horizons=(3,))
    rows = audit.attach_future_from_entry_columns(rows, ohlc, horizons=(3,))

    assert rows.loc[0, "actual_residual_up_3_by_subtraction"] == 2.0
    assert rows.loc[0, "future_up_from_entry_3"] == 0.2
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_regression_updn_already_moved_audit.py -q
```

Expected: FAIL because metric functions are missing.

- [ ] **Step 3: Implement already-moved and summary metrics**

Add:

```python
def _safe_div(num: pd.Series, den: pd.Series) -> pd.Series:
    den = den.replace(0, np.nan)
    return num / den


def attach_already_moved_columns(rows: pd.DataFrame, horizons: tuple[int, ...]) -> pd.DataFrame:
    out = rows.copy()
    move = out.apply(lambda r: movement_from_fractal_to_entry(r["fractal0_price"], r["entry_open"]), axis=1, result_type="expand")
    out = pd.concat([out, move], axis=1)
    for h in horizons:
        out[f"already_up_share_{h}"] = _safe_div(out["already_up"], out[f"actual_up_{h}_price"])
        out[f"already_dn_share_{h}"] = _safe_div(out["already_dn"], out[f"actual_dn_{h}_price"])
        out[f"already_abs_share_max_{h}"] = out[[f"already_up_share_{h}", f"already_dn_share_{h}"]].max(axis=1)
        out[f"actual_residual_up_{h}_by_subtraction"] = np.clip(out[f"actual_up_{h}_price"] - out["already_up"], 0.0, None)
        out[f"actual_residual_dn_{h}_by_subtraction"] = np.clip(out[f"actual_dn_{h}_price"] - out["already_dn"], 0.0, None)
        out[f"pred_residual_up_{h}_by_subtraction"] = np.clip(out[f"pred_up_{h}_price"] - out["already_up"], 0.0, None)
        out[f"pred_residual_dn_{h}_by_subtraction"] = np.clip(out[f"pred_dn_{h}_price"] - out["already_dn"], 0.0, None)
        out[f"actual_residual_log_ratio_{h}"] = safe_log_ratio(
            out[f"actual_residual_up_{h}_by_subtraction"].to_numpy(),
            out[f"actual_residual_dn_{h}_by_subtraction"].to_numpy(),
        )
        out[f"pred_residual_log_ratio_{h}"] = safe_log_ratio(
            out[f"pred_residual_up_{h}_by_subtraction"].to_numpy(),
            out[f"pred_residual_dn_{h}_by_subtraction"].to_numpy(),
        )
    return out


def attach_future_from_entry_columns(rows: pd.DataFrame, ohlc: pd.DataFrame, horizons: tuple[int, ...]) -> pd.DataFrame:
    out = rows.copy()
    indexed = ohlc.set_index("time", drop=False)
    for h in horizons:
        future_up = []
        future_dn = []
        bars_after = []
        for row in out.itertuples(index=False):
            if pd.isna(row.entry_time) or pd.isna(row.entry_open) or pd.isna(getattr(row, f"label_end_time_{h}")):
                future_up.append(np.nan)
                future_dn.append(np.nan)
                bars_after.append(0)
                continue
            end_time = getattr(row, f"label_end_time_{h}")
            window = indexed.loc[(indexed.index >= row.entry_time) & (indexed.index <= end_time)]
            if window.empty:
                future_up.append(np.nan)
                future_dn.append(np.nan)
                bars_after.append(0)
                continue
            entry_open = float(row.entry_open)
            future_up.append(max(float(window["high"].max()) - entry_open, 0.0))
            future_dn.append(max(entry_open - float(window["low"].min()), 0.0))
            bars_after.append(int(len(window)))
        out[f"future_up_from_entry_{h}"] = future_up
        out[f"future_dn_from_entry_{h}"] = future_dn
        out[f"bars_after_entry_{h}"] = bars_after
        out[f"future_entry_log_ratio_{h}"] = safe_log_ratio(
            out[f"future_up_from_entry_{h}"].to_numpy(),
            out[f"future_dn_from_entry_{h}"].to_numpy(),
        )
    return out


def _corr(a: pd.Series, b: pd.Series) -> float | None:
    valid = pd.DataFrame({"a": a, "b": b}).replace([np.inf, -np.inf], np.nan).dropna()
    if len(valid) < 3:
        return None
    if valid["a"].nunique() <= 1 or valid["b"].nunique() <= 1:
        return None
    return float(stats.spearmanr(valid["a"], valid["b"])[0])


def _summarize_subset(subset: pd.DataFrame, h: int) -> dict:
    strong_threshold = subset[f"pred_log_ratio_{h}"].abs().quantile(CONFIG.strong_pred_quantile) if len(subset) else np.nan
    strong_subset = subset.loc[subset[f"pred_log_ratio_{h}"].abs() >= strong_threshold] if len(subset) else subset
    return {
        "rows": int(len(subset)),
        "median_already_up_share": float(subset[f"already_up_share_{h}"].median()) if len(subset) else None,
        "median_already_dn_share": float(subset[f"already_dn_share_{h}"].median()) if len(subset) else None,
        "p90_already_up_share": float(subset[f"already_up_share_{h}"].quantile(0.90)) if len(subset) else None,
        "p90_already_dn_share": float(subset[f"already_dn_share_{h}"].quantile(0.90)) if len(subset) else None,
        "p75_already_abs_share_max": float(subset[f"already_abs_share_max_{h}"].quantile(0.75)) if len(subset) else None,
        "share_already_abs_over_50pct": float((subset[f"already_abs_share_max_{h}"] >= 0.50).mean()) if len(subset) else None,
        "share_already_abs_over_100pct": float((subset[f"already_abs_share_max_{h}"] >= 1.00).mean()) if len(subset) else None,
        "share_future_up_zero": float((subset[f"future_up_from_entry_{h}"] <= 0.0).mean()) if len(subset) else None,
        "share_future_dn_zero": float((subset[f"future_dn_from_entry_{h}"] <= 0.0).mean()) if len(subset) else None,
        "pred_vs_actual_log_ratio_spearman": _corr(subset[f"pred_log_ratio_{h}"], subset[f"actual_log_ratio_{h}"]),
        "pred_vs_future_entry_log_ratio_spearman": _corr(subset[f"pred_log_ratio_{h}"], subset[f"future_entry_log_ratio_{h}"]),
        "pred_residual_vs_actual_residual_log_ratio_spearman": _corr(subset[f"pred_residual_log_ratio_{h}"], subset[f"actual_residual_log_ratio_{h}"]),
        "actual_residual_vs_direct_future_log_ratio_spearman": _corr(subset[f"actual_residual_log_ratio_{h}"], subset[f"future_entry_log_ratio_{h}"]),
        "strong_abs_pred_log_ratio": {
            "threshold": float(strong_threshold) if len(subset) else None,
            "rows": int(len(strong_subset)),
            "median_already_abs_share_max": float(strong_subset[f"already_abs_share_max_{h}"].median()) if len(strong_subset) else None,
            "share_already_abs_over_100pct": float((strong_subset[f"already_abs_share_max_{h}"] >= 1.00).mean()) if len(strong_subset) else None,
            "pred_vs_future_entry_log_ratio_spearman": _corr(strong_subset[f"pred_log_ratio_{h}"], strong_subset[f"future_entry_log_ratio_{h}"]),
        },
    }


def summarize_already_moved(rows: pd.DataFrame, horizons: tuple[int, ...]) -> dict:
    summary = {}
    for h in horizons:
        entry = _summarize_subset(rows, h)
        for direction in (-1, 1):
            entry[f"dir_{direction}"] = _summarize_subset(rows.loc[rows["fractal0_direction"] == direction], h)
        summary[f"h{h}"] = entry
    return summary
```

- [ ] **Step 4: Run tests to verify pass**

Run:

```bash
./.venv/bin/python -m pytest tests/test_regression_updn_already_moved_audit.py -q
```

Expected: PASS.

---

### Task 5: End-To-End Runner, JSON, CSV, CLI

**Files:**
- Modify: `ML/baseline/analyze_regression_updn_already_moved_audit.py`
- Modify: `tests/test_regression_updn_already_moved_audit.py`

**Interfaces:**
- Produces `run_already_moved_audit(output_json: Path = ALREADY_MOVED_JSON_PATH, output_rows: Path = ALREADY_MOVED_ROWS_PATH) -> dict`.
- Produces `build_arg_parser() -> argparse.ArgumentParser`.
- Produces CLI flag `--regression-updn-already-moved-audit`.

- [ ] **Step 1: Write failing runner shape test**

Append:

```python
def test_cli_flag_is_registered():
    parser = audit.build_arg_parser()
    args = parser.parse_args(["--regression-updn-already-moved-audit"])

    assert args.regression_updn_already_moved_audit is True
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_regression_updn_already_moved_audit.py -q
```

Expected: FAIL because CLI is missing.

- [ ] **Step 3: Implement runner orchestration**

Add:

```python
def _target_indices_for_horizons(horizons: tuple[int, ...]) -> tuple[int, ...]:
    indices = []
    for h in horizons:
        up_name, dn_name = foundation.TARGET_PAIRS_BY_HORIZON[h]
        indices.extend([
            foundation.UPDN_TARGET_COLUMNS.index(up_name),
            foundation.UPDN_TARGET_COLUMNS.index(dn_name),
        ])
    return tuple(indices)


def _fit_fixed_model(train_frame: pd.DataFrame, eval_frame: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    train_x = foundation.build_updn_features(train_frame, CONFIG.profile)
    eval_x = foundation.build_updn_features(eval_frame, CONFIG.profile)
    train_y = foundation.extract_updn_targets(train_frame)
    eval_y = foundation.extract_updn_targets(eval_frame)
    pred, _ = foundation._train_predict_model(CONFIG.model_key, CONFIG.seed, train_x, train_y, eval_x)
    return eval_y, pred


def _attach_denormalized_targets(rows: pd.DataFrame, y_true: np.ndarray, y_pred: np.ndarray, params: dict) -> pd.DataFrame:
    out = rows.copy()
    true_price = denormalize_updn_matrix(y_true, out["source_split"], out["source_row_idx"], params)
    pred_price = denormalize_updn_matrix(y_pred, out["source_split"], out["source_row_idx"], params)
    for idx, name in enumerate(foundation.UPDN_TARGET_COLUMNS):
        out[f"actual_{name}_price"] = true_price[:, idx]
        out[f"pred_{name}_price"] = pred_price[:, idx]
    for h in CONFIG.horizons:
        out[f"actual_log_ratio_{h}"] = safe_log_ratio(out[f"actual_up_{h}_price"].to_numpy(), out[f"actual_dn_{h}_price"].to_numpy())
        out[f"pred_log_ratio_{h}"] = safe_log_ratio(out[f"pred_up_{h}_price"].to_numpy(), out[f"pred_dn_{h}_price"].to_numpy())
    return out


def run_already_moved_audit(
    output_json: Path = ALREADY_MOVED_JSON_PATH,
    output_rows: Path = ALREADY_MOVED_ROWS_PATH,
) -> dict:
    started_at = dt.datetime.now(dt.timezone.utc).isoformat()
    output_json.parent.mkdir(parents=True, exist_ok=True)
    source_frames = load_source_frames()
    split_frames = load_split_frames_with_source()
    ohlc = load_ohlc()
    params = load_source_updn_params()
    source_alignment = validate_source_row_alignment(source_frames, split_frames, params)
    if source_alignment["status"] != "PASS":
        report = {
            "experiment": "regression_updn_already_moved_audit",
            "status": source_alignment["status"],
            "artifact_status": "DIAGNOSTIC_ONLY",
            "config": dataclasses.asdict(CONFIG),
            "preflight": {"source_row_alignment": source_alignment},
        }
        output_json.write_text(json.dumps(report, indent=2, default=str))
        return report

    train_frame = split_frames["train_core"]
    all_summaries = {}
    all_preflight = {}
    csv_frames = []

    for split_name in (CONFIG.primary_split, *CONFIG.disclosure_splits):
        frame = split_frames[split_name].reset_index(drop=True)
        y_true, y_pred = _fit_fixed_model(train_frame, frame)
        rows, entry_report = attach_entry_open(frame, ohlc)
        rows = _attach_denormalized_targets(rows, y_true, y_pred, params)

        selected_contract = select_label_window_contract(rows, ohlc, CONFIG.horizons)
        all_preflight[split_name] = {
            **entry_report,
            "source_row_alignment": source_alignment,
            "label_window_selection": selected_contract,
        }
        if selected_contract["status"] != "PASS" and split_name == CONFIG.primary_split:
            report = {
                "experiment": "regression_updn_already_moved_audit",
                "status": "LABEL_WINDOW_CONTRACT_FAILED",
                "artifact_status": "DIAGNOSTIC_ONLY",
                "config": dataclasses.asdict(CONFIG),
                "preflight": all_preflight,
            }
            output_json.write_text(json.dumps(report, indent=2, default=str))
            return report
        start_offset = int(selected_contract["selected_start_offset"])

        for h in CONFIG.horizons:
            reconstructed = reconstruct_window_moves(rows, ohlc, horizon=h, start_offset=start_offset)
            rows = pd.concat([rows, reconstructed], axis=1)

        rows = attach_already_moved_columns(rows, CONFIG.horizons)
        rows = attach_future_from_entry_columns(rows, ohlc, CONFIG.horizons)
        coverage = coverage_disclosure(rows, CONFIG.horizons)
        used_rows = rows.loc[rows["used_in_summary"]].copy()
        all_preflight[split_name]["coverage_disclosure"] = coverage
        all_summaries[split_name] = {
            "coverage_disclosure": coverage,
            "already_moved": summarize_already_moved(used_rows, CONFIG.horizons),
        }
        rows["analysis_split"] = split_name
        csv_frames.append(rows)

    row_table = pd.concat(csv_frames, ignore_index=True)
    row_table.to_csv(output_rows, index=False)
    report = {
        "experiment": "regression_updn_already_moved_audit",
        "status": "PASS_DIAGNOSTIC",
        "artifact_status": "DIAGNOSTIC_ONLY",
        "started_at": started_at,
        "finished_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "config": dataclasses.asdict(CONFIG),
        "preflight": all_preflight,
        "summary": all_summaries,
        "row_artifact": str(output_rows),
    }
    output_json.write_text(json.dumps(report, indent=2, default=str))
    return report


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--regression-updn-already-moved-audit", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    if args.regression_updn_already_moved_audit:
        report = run_already_moved_audit()
        print({"status": report["status"], "json": str(ALREADY_MOVED_JSON_PATH)})
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run focused tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_regression_updn_already_moved_audit.py -q
```

Expected: PASS.

---

### Task 6: Contract Hardening Before Full Interpretation

**Files:**
- Modify: `ML/baseline/analyze_regression_updn_already_moved_audit.py`
- Modify: `tests/test_regression_updn_already_moved_audit.py`

**Interfaces:**
- Produces `label_window_contract_report(rows: pd.DataFrame, horizons: tuple[int, ...]) -> dict`.
- Produces `select_label_window_contract(rows: pd.DataFrame, ohlc: pd.DataFrame, horizons: tuple[int, ...]) -> dict`.
- Produces `ohlc_alignment_report(ohlc: pd.DataFrame) -> dict`.
- Produces `coverage_disclosure(rows: pd.DataFrame, horizons: tuple[int, ...]) -> dict`.
- Runner status changes to `LABEL_WINDOW_CONTRACT_FAILED` or `OHLC_ALIGNMENT_FAILED` when required.

- [ ] **Step 1: Add contract checks**

Implement checks:

```python
def ohlc_alignment_report(ohlc: pd.DataFrame) -> dict:
    diffs = ohlc["time"].sort_values().diff().dropna()
    one_hour = pd.Timedelta(hours=1)
    return {
        "rows": int(len(ohlc)),
        "timestamps_unique": bool(ohlc["time"].is_unique),
        "timestamps_monotonic": bool(ohlc["time"].is_monotonic_increasing),
        "non_1h_gap_count": int((diffs != one_hour).sum()),
    }


def label_window_contract_report(rows: pd.DataFrame, horizons: tuple[int, ...]) -> dict:
    report = {"status": "PASS", "per_horizon": {}}
    for h in horizons:
        up_diff = (rows[f"actual_up_{h}_price"] - rows[f"reconstructed_up_{h}"]).abs()
        dn_diff = (rows[f"actual_dn_{h}_price"] - rows[f"reconstructed_dn_{h}"]).abs()
        up_match = float((up_diff <= CONFIG.label_match_abs_tolerance).mean())
        dn_match = float((dn_diff <= CONFIG.label_match_abs_tolerance).mean())
        entry = {
            "up_match_rate": up_match,
            "dn_match_rate": dn_match,
            "max_up_abs_diff": float(up_diff.max()),
            "max_dn_abs_diff": float(dn_diff.max()),
        }
        if up_match < CONFIG.label_match_min_rate or dn_match < CONFIG.label_match_min_rate:
            report["status"] = "LABEL_WINDOW_CONTRACT_FAILED"
        report["per_horizon"][f"h{h}"] = entry
    return report


def select_label_window_contract(rows: pd.DataFrame, ohlc: pd.DataFrame, horizons: tuple[int, ...]) -> dict:
    attempts = []
    for start_offset in CONFIG.label_window_start_offsets:
        candidate = rows.copy()
        for h in horizons:
            reconstructed = reconstruct_window_moves(candidate, ohlc, horizon=h, start_offset=int(start_offset))
            candidate = pd.concat([candidate, reconstructed], axis=1)
        report = label_window_contract_report(candidate, horizons)
        attempts.append({"start_offset": int(start_offset), **report})
        if report["status"] == "PASS":
            return {
                "status": "PASS",
                "selected_start_offset": int(start_offset),
                "attempts": attempts,
            }
    return {
        "status": "LABEL_WINDOW_CONTRACT_FAILED",
        "selected_start_offset": None,
        "attempts": attempts,
    }


def coverage_disclosure(rows: pd.DataFrame, horizons: tuple[int, ...]) -> dict:
    full_window_mask = np.ones(len(rows), dtype=bool)
    for h in horizons:
        full_window_mask &= rows[f"bars_in_window_{h}"].to_numpy() >= h
        full_window_mask &= rows[f"bars_after_entry_{h}"].to_numpy() > 0
    used = (
        rows["fractal0_price"].notna().to_numpy()
        & rows["entry_open"].notna().to_numpy()
        & full_window_mask
    )
    rows["used_in_summary"] = used
    return {
        "rows_total": int(len(rows)),
        "rows_with_fractal0": int(rows["fractal0_price"].notna().sum()),
        "rows_with_entry": int(rows["entry_open"].notna().sum()),
        "rows_with_full_label_window": int(full_window_mask.sum()),
        "rows_used_in_summary": int(used.sum()),
        "dropped_missing_fractal0": int(rows["fractal0_price"].isna().sum()),
        "dropped_missing_entry": int(rows["entry_open"].isna().sum()),
        "dropped_missing_full_window": int((~full_window_mask).sum()),
    }
```

- [ ] **Step 2: Wire checks into `run_already_moved_audit`**

After building each split row table, the runner must:

```python
# See Task 5 runner orchestration:
# - run select_label_window_contract() before final reconstruction;
# - stop if primary split cannot match a label window;
# - store coverage_disclosure in preflight and summary;
# - build metric summary only from rows where used_in_summary is true.
```

- [ ] **Step 3: Run focused tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_regression_updn_already_moved_audit.py -q
```

Expected: PASS.

---

### Task 7: Execute Audit And Write Report

**Files:**
- Create: `docs/reports/2026-07-02-regression-updn-already-moved-audit.md`
- Generated: `ML/reports/regression_updn_already_moved_audit.json`
- Generated: `ML/reports/regression_updn_already_moved_audit_rows.csv`

**Interfaces:**
- Produces final report sections: Context, Method, Preflight, Results, Interpretation, Limitations, Next Step.

- [ ] **Step 1: Run smoke-check and record status**

Run:

```bash
./.venv/bin/python statistics/data_contract_smoke_check.py \
  --train DATA/Nero_XAUUSD_train_labeled.csv \
  --val DATA/Nero_XAUUSD_validation_labeled.csv \
  --test DATA/Nero_XAUUSD_test_labeled.csv
```

Expected: If it still fails on known `target_buy_H6_val`, record this as existing data-contract debt. Do not treat it as a new failure of this audit unless the failure changes.

- [ ] **Step 2: Run the audit**

Run:

```bash
./.venv/bin/python ML/baseline/analyze_regression_updn_already_moved_audit.py \
  --regression-updn-already-moved-audit
```

Expected: writes JSON and CSV. Status is either `PASS_DIAGNOSTIC` or a named contract failure.

- [ ] **Step 3: Inspect JSON summary**

Run:

```bash
./.venv/bin/python - <<'PY'
import json
from pathlib import Path
p = Path("ML/reports/regression_updn_already_moved_audit.json")
obj = json.loads(p.read_text())
print(obj["status"])
print(json.dumps(obj.get("summary", {}).get("val_stop", {}), indent=2)[:4000])
PY
```

Expected: summary has `coverage_disclosure` and `already_moved.h3/h6/h12` entries for `val_stop`.

- [ ] **Step 4: Write canonical report**

Create `docs/reports/2026-07-02-regression-updn-already-moved-audit.md` with:

```markdown
# Regression Up/Dn Already Moved Audit

> **Дата**: 2026-07-02
> **Статус**: Completed
> **Вердикт**: DIAGNOSTIC_ONLY
> **Цель**: Проверить, какая часть успеха `Regression Up/Dn` объясняется движением, уже случившимся между `fractal0_price` и возможным входом.

## Context

`Regression Up/Dn target foundation` показал сильный сигнал для `up_h/dn_h`, но эти цели измеряются от `fractal0_price`. Возможный торговый вход происходит позже, на следующем `open` после строки сигнала. Поэтому нужно отделить уже случившееся движение от будущего движения после входа.

## Method

- Основной split: `val_stop=2021-2022`.
- Модель: `structure_full` + `xgboost_depth3`.
- Горизонты: H3, H6, H12.
- Без spread, PF, Stop/Profit и PnL.
- Для каждой строки считались:
  - `already_up` / `already_dn`;
  - доля уже случившегося движения относительно `actual_up_h` / `actual_dn_h`;
  - остаток через вычитание: `actual_up_h - already_up`, `pred_up_h - already_up` и симметрично для `dn`;
  - прямой будущий ход после `entry_open` по OHLC;
  - связь `pred_log_ratio_h` с реальным отношением от `fractal0_price`;
  - связь остаточного предсказанного отношения с остаточным фактическим отношением через вычитание;
  - связь `pred_log_ratio_h` с остаточным отношением после `entry_open`.

## Results

### Coverage Disclosure

Эта таблица строится строго из `summary.val_stop.coverage_disclosure`:

| Rows total | With fractal0 | With entry | With full label window | Used in summary |
|---:|---:|---:|---:|---:|
| `rows_total` | `rows_with_fractal0` | `rows_with_entry` | `rows_with_full_label_window` | `rows_used_in_summary` |

Если `rows_used_in_summary` заметно меньше `rows_total`, выводы ограничены подмножеством строк и это нужно явно сказать в Interpretation.

### Already Moved And Future After Entry

Основная таблица строится строго из `summary.val_stop.already_moved.h3`, `summary.val_stop.already_moved.h6` и `summary.val_stop.already_moved.h12`:

| Horizon | Rows | Median already up share | P90 already up share | Median already dn share | P90 already dn share | Share already >= 50% | Share already >= 100% | Future up zero | Future dn zero | Pred vs actual from fractal | Pred from fractal vs direct future after entry |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| H3 | `summary.val_stop.already_moved.h3.rows` | `summary.val_stop.already_moved.h3.median_already_up_share` | `summary.val_stop.already_moved.h3.p90_already_up_share` | `summary.val_stop.already_moved.h3.median_already_dn_share` | `summary.val_stop.already_moved.h3.p90_already_dn_share` | `summary.val_stop.already_moved.h3.share_already_abs_over_50pct` | `summary.val_stop.already_moved.h3.share_already_abs_over_100pct` | `summary.val_stop.already_moved.h3.share_future_up_zero` | `summary.val_stop.already_moved.h3.share_future_dn_zero` | `summary.val_stop.already_moved.h3.pred_vs_actual_log_ratio_spearman` | `summary.val_stop.already_moved.h3.pred_vs_future_entry_log_ratio_spearman` |
| H6 | `summary.val_stop.already_moved.h6.rows` | `summary.val_stop.already_moved.h6.median_already_up_share` | `summary.val_stop.already_moved.h6.p90_already_up_share` | `summary.val_stop.already_moved.h6.median_already_dn_share` | `summary.val_stop.already_moved.h6.p90_already_dn_share` | `summary.val_stop.already_moved.h6.share_already_abs_over_50pct` | `summary.val_stop.already_moved.h6.share_already_abs_over_100pct` | `summary.val_stop.already_moved.h6.share_future_up_zero` | `summary.val_stop.already_moved.h6.share_future_dn_zero` | `summary.val_stop.already_moved.h6.pred_vs_actual_log_ratio_spearman` | `summary.val_stop.already_moved.h6.pred_vs_future_entry_log_ratio_spearman` |
| H12 | `summary.val_stop.already_moved.h12.rows` | `summary.val_stop.already_moved.h12.median_already_up_share` | `summary.val_stop.already_moved.h12.p90_already_up_share` | `summary.val_stop.already_moved.h12.median_already_dn_share` | `summary.val_stop.already_moved.h12.p90_already_dn_share` | `summary.val_stop.already_moved.h12.share_already_abs_over_50pct` | `summary.val_stop.already_moved.h12.share_already_abs_over_100pct` | `summary.val_stop.already_moved.h12.share_future_up_zero` | `summary.val_stop.already_moved.h12.share_future_dn_zero` | `summary.val_stop.already_moved.h12.pred_vs_actual_log_ratio_spearman` | `summary.val_stop.already_moved.h12.pred_vs_future_entry_log_ratio_spearman` |

### Secondary Subtraction Diagnostics

Этот блок вторичен. Он нужен только чтобы проверить, насколько формула `up_h - already_up` / `dn_h - already_dn` согласуется с прямым OHLC-движением после входа:

| Horizon | Pred residual vs actual residual by subtraction | Subtraction residual vs direct future |
|---:|---:|---:|
| H3 | `summary.val_stop.already_moved.h3.pred_residual_vs_actual_residual_log_ratio_spearman` | `summary.val_stop.already_moved.h3.actual_residual_vs_direct_future_log_ratio_spearman` |
| H6 | `summary.val_stop.already_moved.h6.pred_residual_vs_actual_residual_log_ratio_spearman` | `summary.val_stop.already_moved.h6.actual_residual_vs_direct_future_log_ratio_spearman` |
| H12 | `summary.val_stop.already_moved.h12.pred_residual_vs_actual_residual_log_ratio_spearman` | `summary.val_stop.already_moved.h12.actual_residual_vs_direct_future_log_ratio_spearman` |

Отдельная таблица по `dir=-1` и `dir=1` строится из `summary.val_stop.already_moved.h*.dir_-1` и `summary.val_stop.already_moved.h*.dir_1` с теми же колонками.

Отдельно для сильных строк строится блок из `summary.val_stop.already_moved.h*.strong_abs_pred_log_ratio`.

## Interpretation

Ответить прямо:

1. Сколько target-успеха уже было известно до возможного входа.
2. Улучшает ли сравнение через вычитание `up_h - already_up` / `dn_h - already_dn` понимание остаточного сигнала.
3. Совпадает ли остаток через вычитание с прямым будущим ходом после `entry_open`.
4. Сохраняется ли связь предсказанного отношения с будущим ходом после входа.
5. Можно ли строить немедленный вход по рынку на следующем `open`.
6. Нужен ли следующий план про вход от уровня `fractal0_price` / ретест.

## Limitations

- Это не торговый тест.
- Здесь нет spread, PF, Stop/Profit и PnL.
- Если label-window contract не совпал с OHLC, любые численные выводы по долям движения запрещены.

## Related Materials

- [JSON](../../ML/reports/regression_updn_already_moved_audit.json)
- [Rows CSV](../../ML/reports/regression_updn_already_moved_audit_rows.csv)
- [Regression Up/Dn target foundation](2026-06-30-regression-updn-target-foundation.md)
- [Regression Up/Dn ratio audit](2026-07-01-regression-updn-ratio-audit.md)
```

- [ ] **Step 5: Run tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_regression_updn_already_moved_audit.py -q
```

Expected: PASS.

- [ ] **Step 6: Run broader tests only if code touches shared foundation helpers**

Run if shared helpers were modified:

```bash
./.venv/bin/python -m pytest tests/test_regression_updn_target_foundation.py tests/test_regression_updn_already_moved_audit.py -q
```

Expected: PASS.

---

### Task 8: Final Verification And Handoff

**Files:**
- Modify: `CHANGELOG.md`
- Modify: `CONTEXT_HANDOFF.md`
- Modify via wiki tooling if requested by stage closure: `wiki/index.md`, `wiki/log.md`, `wiki/REPO_integrity.md`, relevant `wiki/research/*.md`

**Interfaces:**
- Produces final synchronized project memory only after the report is accepted.

- [ ] **Step 1: Verify artifacts exist**

Run:

```bash
test -f ML/reports/regression_updn_already_moved_audit.json
test -f ML/reports/regression_updn_already_moved_audit_rows.csv
test -f docs/reports/2026-07-02-regression-updn-already-moved-audit.md
```

Expected: no output and exit code 0.

- [ ] **Step 2: Verify old invalid trading report is still absent**

Run:

```bash
test ! -f docs/reports/2026-07-01-regression-updn-trading-confirmation.md
test ! -f ML/reports/regression_updn_trading_confirmation.json
```

Expected: no output and exit code 0.

- [ ] **Step 3: Run final focused verification**

Run:

```bash
./.venv/bin/python -m pytest tests/test_regression_updn_already_moved_audit.py -q
```

Expected: PASS.

- [ ] **Step 4: Update handoff only after the report is final**

`CONTEXT_HANDOFF.md` must say:

```markdown
Current next step: review `docs/reports/2026-07-02-regression-updn-already-moved-audit.md`.

Do not revive the deleted `Regression Up/Dn Trading Confirmation` report. The next trading plan is allowed only after the already-moved audit answers whether the signal survives after entry.
```

- [ ] **Step 5: If wiki is updated, regenerate and verify**

Run:

```bash
./.venv/bin/python wiki/wiki.py generate
./.venv/bin/python wiki/wiki.py verify
```

Expected: wiki verify reports OK.

## Self-Review Checklist

- The plan has a single purpose: quantify already-completed movement before entry.
- It does not calculate PF, PnL, spread, Stop/Profit, or trading pass/fail.
- It requires OHLC alignment before interpretation.
- It requires label-window reconstruction before interpretation.
- It keeps `diagnostic_holdout` and 2026 out of rule choice.
- It preserves the old invalid trading report as absent.
- It gives the future implementer exact file paths, commands, function names, and expected outputs.
