# Stage 6.1 H12 Relative Fractal Geometry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Test whether H12 TP/SL touch prediction improves when the model sees the relative price and time geometry of nearby fractal levels around `fractal0`.

**Architecture:** Add a separate Stage 6.1 runner that reuses Stage 6.0 label/simulation helpers, fixes horizon to 12 H1 bars, trains on definitive TP-vs-SL touch rows, and evaluates trading PF on all valid rows. New feature profiles are narrow and predeclared: baseline, price-nearest geometry, time-nearest geometry, narrow 3 ATR corridor, wide 10 ATR corridor, and uniform 10 ATR zone summaries.

**Tech Stack:** Python 3.10+, pandas, numpy, sklearn metrics, xgboost, pytest, existing `./.venv/bin/python`, existing `DATA/*_labeled.csv`, local OHLC source `DATA/XAUUSD_H1_OHLC.csv`.

## Global Constraints

- Work on the current branch; do not use git worktree.
- Use `./.venv/bin/python` for all Python commands.
- New Python code must be covered by tests before implementation.
- After Python changes, run `./.venv/bin/python -m pytest tests/ -q`.
- Stage 6.1 is `DIAGNOSTIC_ONLY` unless runtime timing, spread convention, simulator parity, and independent validation are proven.
- Do not use `2023-2025` or `2026` for winner selection.
- Do not open a broad search over horizon/ATR/TP/SL. Horizon is fixed to `12`; TP/SL contract is inherited from Stage 6.0.
- Do not add raw absolute fractal prices as primary features. Relative price must be encoded as `(price_i - fractal0_price) / ATR`.
- Fractal string format must be verified before model training: 23 colon-separated fields, with Stage 5.1b indices `price=1`, `direction=2`, `front=3`, `back=4`, `impulse=10`, raw `shift=22`. There is no trusted per-fractal `atr` field in `extract_stage5_1b_fields`; do not create `fractal_atr_ratio`.
- Run A7-style feature preflight before interpreting model metrics.
- New Stage 6.1 features must not include any `stage6_` target/outcome columns.
- Record SHA256 and row counts for all input data files used by Stage 6.1. The runner recomputes labels against the current OHLC file, so reproducibility requires exact input hashes in the JSON and report.

---

## Fixed Research Contract

**Instrument/timeframe:** XAUUSD H1.

**Testable hypothesis:** Local support/resistance geometry around `fractal0` carries signal for which barrier is touched first. The primary expected signal is asymmetric crowding of historical fractal levels above versus below `fractal0`, normalized by ATR:

- BUY should be more likely to reach TP before SL when recent or price-near fractal levels below/near `fractal0` indicate local support and the path above has less nearby resistance.
- SELL should be more likely to reach TP before SL under the mirrored configuration.
- If only wide 10 ATR profiles work while 3 ATR and time-nearest profiles fail, treat the result as suspicious until ruled out by feature importance and holdout behavior. A wide profile can capture regime or level-density artifacts, not necessarily actionable local geometry.

**Predeclared geometry comparisons:**

- `nearest_price`: asks whether price-level proximity matters.
- `nearest_time`: asks whether recency matters independently from price proximity.
- `corridor3`: asks whether very local structure around `fractal0` is enough.
- `corridor10`: wide control, not the preferred explanatory result.
- `zones10`: compresses the same wide window into symmetric 1 ATR buckets to test crowding/asymmetry without relying on token order.

**Validation policy:** `val_stop` (`2021-2022`) is the only split used for model selection, threshold selection, best seed/profile summaries, and gate. `diagnostic_holdout` (`2023-2025`) and `low_n_disclosure` (`2026`) are disclosure-only: they may be reported after selection, but they must not change thresholds, selected profile, selected seed, or gate status.

**Decision/entry:** Same as Stage 6.0: decision on row `time`, entry at `Open[row+1]`, still `DIAGNOSTIC_ONLY`.

**Horizon:** `12` H1 bars.

**Barriers:** Same as Stage 6.0:

- BUY stop: `fractal0.price - 0.5 * ATR`
- BUY TP: `entry_price + 2.0 * ATR`
- SELL stop: `fractal0.price + 0.5 * ATR`
- SELL TP: `entry_price - 2.0 * ATR`
- Same-bar ambiguity: `AMBIGUOUS_SL_FIRST`

**Main training target:** `stage6_definitive_tp_vs_sl_flag`.

- Train/evaluate model metrics only on definitive rows: TP=1, SL/AMBIGUOUS=0.
- Timeout rows are excluded from model metric labels.
- Trading simulation still applies score thresholds to all valid rows and includes timeout PnL. This prevents hiding timeout cost.

**Primary profile:** `h12_corridor3_relative_geometry`.

**Control profiles:**

- `h12_clock_shift_back` — current Stage 6.0-style baseline.
- `h12_nearest_price40_relative_geometry`.
- `h12_nearest_time40_relative_geometry`.
- `h12_corridor10_relative_geometry`.
- `h12_zones10_uniform_summary`.

**Gate:** Stage 6.1 can only produce `DIAGNOSTIC_SIGNAL_FOUND` or a failure status, never `CANDIDATE`.

---

## File Structure

**Create**

- `ML/baseline/benchmark_stage6_1_relative_geometry.py` — Stage 6.1 feature builders, preflight, runner and CLI.
- `tests/test_stage6_1_relative_geometry.py` — unit tests for geometry extraction, feature shapes, denylist, preflight, target filtering and gate.

**Modify**

- `docs/reports/2026-06-29-stage6_1-h12-relative-fractal-geometry.md` — created after full run.
- `CHANGELOG.md` — final summary after report.
- `CONTEXT_HANDOFF.md` — next handoff after report.
- `wiki/research/fractal-stop-research.md`, `wiki/index.md`, `wiki/log.md`, `wiki/REPO_integrity.md` — after report ingest.

**Generated**

- `ML/reports/stage6_1_h12_relative_fractal_geometry.json`.

**Read before implementation**

- `docs/methodology/03-feature-contract-leakage.md`
- `docs/methodology/04-labeling.md`
- `docs/methodology/A6-fractal-feature-profile-catalog.md`
- `docs/methodology/A7-feature-distribution-audit.md`
- `docs/reports/2026-06-29-stage6_0-outcome-based-triple-barrier-foundation.md`

---

### Task 1: Stage 6.1 Contract And Skeleton

**Files:**
- Create: `ML/baseline/benchmark_stage6_1_relative_geometry.py`
- Create: `tests/test_stage6_1_relative_geometry.py`

**Interfaces:**
- Produces:
  - `Stage61Config`
  - `STAGE6_1_CONFIG`
  - `STAGE6_1_JSON_REPORT_PATH`
  - `stage61_profile_keys() -> tuple[str, ...]`
  - `stage61_feature_denylist() -> tuple[str, ...]`
  - `stage61_input_file_manifest() -> dict`

- [ ] **Step 1: Write failing contract tests**

Add to `tests/test_stage6_1_relative_geometry.py`:

```python
import numpy as np
import pandas as pd
import pytest

import ML.baseline.benchmark_stage6_1_relative_geometry as s61


def test_stage61_config_is_fixed_and_narrow():
    cfg = s61.STAGE6_1_CONFIG

    assert cfg.horizon_bars == 12
    assert cfg.stop_offset_atr == 0.5
    assert cfg.take_profit_atr == 2.0
    assert cfg.entry_lag_bars == 1
    assert cfg.primary_profile == "h12_corridor3_relative_geometry"
    assert cfg.profile_keys == (
        "h12_clock_shift_back",
        "h12_nearest_price40_relative_geometry",
        "h12_nearest_time40_relative_geometry",
        "h12_corridor3_relative_geometry",
        "h12_corridor10_relative_geometry",
        "h12_zones10_uniform_summary",
    )
    assert cfg.seeds == (42, 77, 123)


def test_stage61_feature_denylist_includes_stage6_targets():
    denylist = set(s61.stage61_feature_denylist())

    assert "stage6_tp_vs_rest_flag" in denylist
    assert "stage6_definitive_tp_vs_sl_flag" in denylist
    assert "stage6_pnl_r" in denylist
    assert all(col.startswith("stage6_") for col in denylist)


def test_stage61_fractal_field_contract_matches_stage5_1b_parser():
    assert s61.STAGE5_1B_FIELD_TO_FRACTAL_INDEX["price"] == 1
    assert s61.STAGE5_1B_FIELD_TO_FRACTAL_INDEX["direction"] == 2
    assert s61.STAGE5_1B_FIELD_TO_FRACTAL_INDEX["front"] == 3
    assert s61.STAGE5_1B_FIELD_TO_FRACTAL_INDEX["back"] == 4
    assert s61.STAGE5_1B_FIELD_TO_FRACTAL_INDEX["impulse"] == 10
    assert "atr" not in s61.STAGE5_1B_FIELD_TO_FRACTAL_INDEX
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage6_1_relative_geometry.py -q
```

Expected: fail with `ModuleNotFoundError` or missing symbols.

- [ ] **Step 3: Create minimal module**

Create `ML/baseline/benchmark_stage6_1_relative_geometry.py`:

```python
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np
import pandas as pd

from ML.baseline.benchmark_stage5_transformer_breach import (
    FRACTAL_SEP,
    STAGE5_1B_FIELD_TO_FRACTAL_INDEX,
    build_stage5_4_features,
    extract_stage5_1b_fields,
)
from ML.baseline.benchmark_stage6_outcome_based import (
    DATA_DIR,
    OHLC_FILE,
    REPORTS_DIR,
    STAGE6_0_CONFIG,
    Stage60Config,
    stage6_all_trade_baseline,
    stage6_binary_metrics,
    stage6_build_outcome_labels,
    stage6_feature_denylist,
    stage6_load_labeled_splits,
    stage6_outcome_preflight,
    stage6_permutation_threshold_baseline,
    stage6_select_threshold_on_val,
    stage6_simulate_threshold,
)


STAGE6_1_JSON_REPORT_PATH = REPORTS_DIR / "stage6_1_h12_relative_fractal_geometry.json"


@dataclass(frozen=True)
class Stage61Config:
    horizon_bars: int = 12
    stop_offset_atr: float = 0.5
    take_profit_atr: float = 2.0
    entry_lag_bars: int = 1
    primary_profile: str = "h12_corridor3_relative_geometry"
    profile_keys: tuple[str, ...] = (
        "h12_clock_shift_back",
        "h12_nearest_price40_relative_geometry",
        "h12_nearest_time40_relative_geometry",
        "h12_corridor3_relative_geometry",
        "h12_corridor10_relative_geometry",
        "h12_zones10_uniform_summary",
    )
    seeds: tuple[int, ...] = (42, 77, 123)


STAGE6_1_CONFIG = Stage61Config()


def stage61_profile_keys() -> tuple[str, ...]:
    return STAGE6_1_CONFIG.profile_keys


def stage61_feature_denylist() -> tuple[str, ...]:
    return stage6_feature_denylist()


def stage61_input_file_manifest() -> dict:
    paths = {
        "ohlc": OHLC_FILE,
        "train_labeled": DATA_DIR / "Nero_XAUUSD_train_labeled.csv",
        "validation_labeled": DATA_DIR / "Nero_XAUUSD_validation_labeled.csv",
        "test_labeled": DATA_DIR / "Nero_XAUUSD_test_labeled.csv",
    }
    out = {}
    for name, path in paths.items():
        payload = path.read_bytes()
        with path.open("rb") as fh:
            row_count = sum(1 for _ in fh) - 1
        out[name] = {
            "path": str(path),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "bytes": len(payload),
            "row_count": int(max(row_count, 0)),
        }
    return out
```

- [ ] **Step 4: Run contract tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage6_1_relative_geometry.py -q
```

Expected: `2 passed`.

- [ ] **Step 5: Commit**

```bash
git add ML/baseline/benchmark_stage6_1_relative_geometry.py tests/test_stage6_1_relative_geometry.py
git commit -m "feat: add stage 6.1 relative geometry contract"
```

---

### Task 2: Relative Fractal Extraction

**Files:**
- Modify: `ML/baseline/benchmark_stage6_1_relative_geometry.py`
- Modify: `tests/test_stage6_1_relative_geometry.py`

**Interfaces:**
- Produces:
  - `stage61_parse_fractals(row: pd.Series) -> list[dict]`
  - `stage61_relative_fractal_frame(row: pd.Series, mode: str, k: int = 40, corridor_atr: float = 10.0) -> pd.DataFrame`

- [ ] **Step 1: Write failing tests for relative coordinates, nearest-price, nearest-time and corridor**

Add:

```python
def _row_with_fractals():
    return pd.Series({
        "ATR": 2.0,
        "fractal0": "0:100.0:-1:1.0:2.0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:1.0:0",
        "fractal1": "0:104.0:1:1.5:3.0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:1.2:4",
        "fractal2": "0:90.0:-1:2.0:4.0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0.8:8",
        "fractal3": "0:130.0:1:3.0:5.0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:2.0:12",
    })


def test_stage61_relative_fractal_frame_nearest_price_uses_atr_coordinates():
    frame = s61.stage61_relative_fractal_frame(_row_with_fractals(), mode="nearest_price", k=2)

    assert list(frame["fractal_idx"]) == [1, 2]
    assert np.allclose(frame["price_coord_atr"].to_numpy(), [2.0, -5.0])
    assert np.allclose(frame["abs_price_coord_atr"].to_numpy(), [2.0, 5.0])
    assert "price" not in frame.columns


def test_stage61_relative_fractal_frame_nearest_time_uses_shift_before_price():
    frame = s61.stage61_relative_fractal_frame(_row_with_fractals(), mode="nearest_time", k=2)

    assert list(frame["fractal_idx"]) == [1, 2]
    assert np.allclose(frame["log_shift"].to_numpy(), [np.log1p(4.0), np.log1p(8.0)])
    assert "price" not in frame.columns


def test_stage61_relative_fractal_frame_corridor_filters_by_atr_width():
    frame = s61.stage61_relative_fractal_frame(_row_with_fractals(), mode="corridor", corridor_atr=3.0)

    assert list(frame["fractal_idx"]) == [1]
    assert frame["price_coord_atr"].min() >= -3.0
    assert frame["price_coord_atr"].max() <= 3.0
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage6_1_relative_geometry.py::test_stage61_relative_fractal_frame_nearest_price_uses_atr_coordinates tests/test_stage6_1_relative_geometry.py::test_stage61_relative_fractal_frame_nearest_time_uses_shift_before_price tests/test_stage6_1_relative_geometry.py::test_stage61_relative_fractal_frame_corridor_filters_by_atr_width -q
```

Expected: fail with missing functions.

- [ ] **Step 3: Implement extraction**

Add:

```python
def stage61_parse_fractals(row: pd.Series) -> list[dict]:
    out: list[dict] = []
    for i in range(100):
        col = f"fractal{i}"
        if col not in row:
            continue
        raw = str(row.get(col, ""))
        parts = raw.split(FRACTAL_SEP)
        if len(parts) < 23:
            continue
        fields = extract_stage5_1b_fields(raw)
        price = float(fields.get("price", 0.0) or 0.0)
        if price <= 0.0:
            continue
        try:
            raw_shift = float(parts[22])
        except (ValueError, IndexError):
            raw_shift = 0.0
        raw_shift = float(np.nan_to_num(raw_shift, nan=0.0))
        out.append({
            "fractal_idx": i,
            "price": price,
            "direction": float(fields.get("direction", 0.0) or 0.0),
            "front": float(fields.get("front", 0.0) or 0.0),
            "back": float(fields.get("back", 0.0) or 0.0),
            "impulse": float(fields.get("impulse", 0.0) or 0.0),
            "shift_bars": max(raw_shift, 0.0),
            "log_shift": float(fields.get("shift", 0.0) or 0.0),
        })
    return out


def stage61_relative_fractal_frame(row: pd.Series, mode: str,
                                   k: int = 40,
                                   corridor_atr: float = 10.0) -> pd.DataFrame:
    atr = float(row.get("ATR", 0.0) or 0.0)
    if atr <= 0.0:
        return pd.DataFrame()
    fractals = stage61_parse_fractals(row)
    if not fractals:
        return pd.DataFrame()
    anchor = next((f for f in fractals if f["fractal_idx"] == 0), None)
    if anchor is None:
        return pd.DataFrame()
    anchor_price = float(anchor["price"])
    rows = []
    for item in fractals:
        if item["fractal_idx"] == 0:
            continue
        coord = (float(item["price"]) - anchor_price) / atr
        row_out = {
            "fractal_idx": int(item["fractal_idx"]),
            "price_coord_atr": float(coord),
            "abs_price_coord_atr": float(abs(coord)),
            "direction": float(item["direction"]),
            "front": float(item["front"]),
            "back": float(item["back"]),
            "impulse": float(item["impulse"]),
            "log_shift": float(item["log_shift"]),
            "selection_rank": 0.0,
        }
        rows.append(row_out)
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    if mode == "nearest_price":
        frame = frame.sort_values(["abs_price_coord_atr", "fractal_idx"]).head(k)
    elif mode == "nearest_time":
        frame = frame.sort_values(["log_shift", "fractal_idx"]).head(k)
    elif mode == "corridor":
        frame = frame.loc[frame["abs_price_coord_atr"] <= corridor_atr]
        frame = frame.sort_values(["abs_price_coord_atr", "fractal_idx"]).head(k)
    else:
        raise ValueError(f"unknown mode: {mode}")
    frame = frame.reset_index(drop=True)
    frame["selection_rank"] = np.arange(len(frame), dtype=np.float32)
    return frame
```

- [ ] **Step 4: Run tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage6_1_relative_geometry.py -q
```

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add ML/baseline/benchmark_stage6_1_relative_geometry.py tests/test_stage6_1_relative_geometry.py
git commit -m "feat: add stage 6.1 relative fractal extraction"
```

---

### Task 3: Flat Feature Builders

**Files:**
- Modify: `ML/baseline/benchmark_stage6_1_relative_geometry.py`
- Modify: `tests/test_stage6_1_relative_geometry.py`

**Interfaces:**
- Consumes: `stage61_relative_fractal_frame()`
- Produces:
  - `stage61_feature_names(profile: str) -> list[str]`
  - `stage61_build_geometry_features(df: pd.DataFrame, profile: str) -> np.ndarray`
  - `stage61_build_features(df: pd.DataFrame, profile: str) -> np.ndarray`

- [ ] **Step 1: Write failing tests for shapes and denylist**

Add:

```python
def test_stage61_build_geometry_features_has_stable_shape_and_no_price():
    df = pd.DataFrame([_row_with_fractals(), _row_with_fractals()])

    X_price = s61.stage61_build_geometry_features(df, "h12_nearest_price40_relative_geometry")
    X_time = s61.stage61_build_geometry_features(df, "h12_nearest_time40_relative_geometry")
    X_corridor3 = s61.stage61_build_geometry_features(df, "h12_corridor3_relative_geometry")
    X_corridor = s61.stage61_build_geometry_features(df, "h12_corridor10_relative_geometry")
    X_zones = s61.stage61_build_geometry_features(df, "h12_zones10_uniform_summary")

    assert X_price.shape == (2, 40 * 8)
    assert X_time.shape == (2, 40 * 8)
    assert X_corridor3.shape == (2, 40 * 8)
    assert X_corridor.shape == (2, 40 * 8)
    assert X_zones.shape == (2, 20 * 5)
    assert np.isfinite(X_price).all()
    assert np.isfinite(X_time).all()
    assert np.isfinite(X_corridor3).all()
    assert np.isfinite(X_corridor).all()
    assert np.isfinite(X_zones).all()
    assert len(s61.stage61_feature_names("h12_corridor3_relative_geometry")) == 40 * 8
    assert len(s61.stage61_feature_names("h12_zones10_uniform_summary")) == 20 * 5
    assert "slot00_price_coord_atr" in s61.stage61_feature_names("h12_corridor3_relative_geometry")
    assert "zone_-01_+00_count" in s61.stage61_feature_names("h12_zones10_uniform_summary")


def test_stage61_build_features_drops_stage6_columns(monkeypatch):
    captured = {}

    def fake_builder(df, profile):
        captured["columns"] = tuple(df.columns)
        return np.zeros((len(df), 4), dtype=np.float32)

    monkeypatch.setattr(s61, "build_stage5_4_features", fake_builder)
    df = pd.DataFrame({
        "time": ["2025.01.01 00:00"],
        "stage6_pnl_r": [1.0],
        "stage6_definitive_tp_vs_sl_flag": [1.0],
    })

    X = s61.stage61_build_features(df, "h12_clock_shift_back")

    assert X.shape == (1, 4)
    assert "stage6_pnl_r" not in captured["columns"]
    assert "stage6_definitive_tp_vs_sl_flag" not in captured["columns"]
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage6_1_relative_geometry.py::test_stage61_build_geometry_features_has_stable_shape_and_no_price tests/test_stage6_1_relative_geometry.py::test_stage61_build_features_drops_stage6_columns -q
```

Expected: fail with missing functions.

- [ ] **Step 3: Implement geometry builders**

Add:

```python
GEOMETRY_FIELDS = (
    "price_coord_atr",
    "abs_price_coord_atr",
    "direction",
    "front",
    "back",
    "impulse",
    "log_shift",
    "selection_rank",
)

ZONE_BOUNDS = tuple((float(i), float(i + 1)) for i in range(-10, 10))


def _stage61_pad_flat(frame: pd.DataFrame, max_rows: int = 40) -> np.ndarray:
    arr = np.zeros((max_rows, len(GEOMETRY_FIELDS)), dtype=np.float32)
    if frame.empty:
        return arr.reshape(-1)
    values = frame.loc[:, GEOMETRY_FIELDS].to_numpy(dtype=np.float32)
    n = min(len(values), max_rows)
    arr[:n, :] = values[:n, :]
    return arr.reshape(-1)


def _stage61_zone_features(row: pd.Series) -> np.ndarray:
    frame = stage61_relative_fractal_frame(row, mode="corridor", corridor_atr=10.0, k=100)
    out = []
    for low, high in ZONE_BOUNDS:
        zone = frame.loc[(frame["price_coord_atr"] >= low) & (frame["price_coord_atr"] < high)]
        if zone.empty:
            out.extend([0.0, 0.0, 0.0, 0.0, 0.0])
            continue
        out.extend([
            float(len(zone)),
            float(zone["back"].mean()),
            float(zone["back"].max()),
            float(zone["impulse"].mean()),
            float(zone["abs_price_coord_atr"].min()),
        ])
    return np.asarray(out, dtype=np.float32)


def stage61_feature_names(profile: str) -> list[str]:
    if profile in {
        "h12_nearest_price40_relative_geometry",
        "h12_nearest_time40_relative_geometry",
        "h12_corridor3_relative_geometry",
        "h12_corridor10_relative_geometry",
    }:
        return [f"slot{i:02d}_{field}" for i in range(40) for field in GEOMETRY_FIELDS]
    if profile == "h12_zones10_uniform_summary":
        zone_fields = ("count", "back_mean", "back_max", "impulse_mean", "nearest_abs_coord")
        return [
            f"zone_{int(low):+03d}_{int(high):+03d}_{field}"
            for low, high in ZONE_BOUNDS
            for field in zone_fields
        ]
    raise ValueError(f"unknown Stage 6.1 profile: {profile}")


def stage61_build_geometry_features(df: pd.DataFrame, profile: str) -> np.ndarray:
    rows = []
    for _, row in df.iterrows():
        if profile == "h12_nearest_price40_relative_geometry":
            frame = stage61_relative_fractal_frame(row, mode="nearest_price", k=40)
            rows.append(_stage61_pad_flat(frame, max_rows=40))
        elif profile == "h12_nearest_time40_relative_geometry":
            frame = stage61_relative_fractal_frame(row, mode="nearest_time", k=40)
            rows.append(_stage61_pad_flat(frame, max_rows=40))
        elif profile == "h12_corridor3_relative_geometry":
            frame = stage61_relative_fractal_frame(row, mode="corridor", k=40, corridor_atr=3.0)
            rows.append(_stage61_pad_flat(frame, max_rows=40))
        elif profile == "h12_corridor10_relative_geometry":
            frame = stage61_relative_fractal_frame(row, mode="corridor", k=40, corridor_atr=10.0)
            rows.append(_stage61_pad_flat(frame, max_rows=40))
        elif profile == "h12_zones10_uniform_summary":
            rows.append(_stage61_zone_features(row))
        else:
            raise ValueError(f"not a geometry profile: {profile}")
    if not rows:
        width = 20 * 5 if profile == "h12_zones10_uniform_summary" else 40 * len(GEOMETRY_FIELDS)
        return np.zeros((0, width), dtype=np.float32)
    return np.vstack(rows).astype(np.float32)


def stage61_build_features(df: pd.DataFrame, profile: str) -> np.ndarray:
    clean = df.drop(columns=[c for c in stage61_feature_denylist() if c in df.columns])
    if profile == "h12_clock_shift_back":
        return build_stage5_4_features(clean, "clock_shift_back")
    if profile in {
        "h12_nearest_price40_relative_geometry",
        "h12_nearest_time40_relative_geometry",
        "h12_corridor3_relative_geometry",
        "h12_corridor10_relative_geometry",
        "h12_zones10_uniform_summary",
    }:
        return stage61_build_geometry_features(clean, profile)
    raise ValueError(f"unknown Stage 6.1 profile: {profile}")
```

- [ ] **Step 4: Run tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage6_1_relative_geometry.py -q
```

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add ML/baseline/benchmark_stage6_1_relative_geometry.py tests/test_stage6_1_relative_geometry.py
git commit -m "feat: add stage 6.1 geometry feature builders"
```

---

### Task 4: A7-Style Feature Preflight

**Files:**
- Modify: `ML/baseline/benchmark_stage6_1_relative_geometry.py`
- Modify: `tests/test_stage6_1_relative_geometry.py`

**Interfaces:**
- Produces:
  - `stage61_fractal_format_preflight(split: dict[str, pd.DataFrame]) -> dict`
  - `stage61_geometry_coverage(df: pd.DataFrame, profile: str) -> dict`
  - `stage61_feature_preflight(split: dict[str, pd.DataFrame]) -> dict`

- [ ] **Step 1: Write failing coverage tests**

Add:

```python
def test_stage61_geometry_coverage_reports_token_counts():
    df = pd.DataFrame([_row_with_fractals(), _row_with_fractals()])

    cov = s61.stage61_geometry_coverage(df, "h12_corridor3_relative_geometry")

    assert cov["n_rows"] == 2
    assert cov["token_count"]["median"] == 1.0
    assert cov["rows_with_0_tokens_rate"] == 0.0
    assert cov["min_price_coord_atr"] >= -3.0
    assert cov["max_price_coord_atr"] <= 3.0
    assert cov["warnings"] == []


def test_stage61_fractal_format_preflight_rejects_short_fractal0():
    split = {
        "train_core": pd.DataFrame({
            "fractal0": ["1:2:3", "0:100:-1:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:1:0"],
        })
    }

    audit = s61.stage61_fractal_format_preflight(split)

    assert audit["train_core"]["non_empty_fractal0_rows"] == 2
    assert audit["train_core"]["short_fractal0_rows"] == 1
    assert "SHORT_FRACTAL0_ROWS" in audit["train_core"]["warnings"]
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage6_1_relative_geometry.py::test_stage61_geometry_coverage_reports_token_counts -q
```

Expected: fail with missing function.

- [ ] **Step 3: Implement coverage preflight**

Add:

```python
def _stage61_quantiles(values) -> dict:
    arr = np.asarray(values, dtype=np.float64)
    arr = arr[np.isfinite(arr)]
    if len(arr) == 0:
        return {"p5": None, "p25": None, "median": None, "p75": None, "p95": None}
    return {
        "p5": float(np.percentile(arr, 5)),
        "p25": float(np.percentile(arr, 25)),
        "median": float(np.median(arr)),
        "p75": float(np.percentile(arr, 75)),
        "p95": float(np.percentile(arr, 95)),
    }


def stage61_fractal_format_preflight(split: dict[str, pd.DataFrame]) -> dict:
    out = {}
    for name, df in split.items():
        if not isinstance(df, pd.DataFrame) or "fractal0" not in df.columns:
            continue
        non_empty = df["fractal0"].dropna().astype(str)
        non_empty = non_empty.loc[non_empty.str.len() > 0]
        field_counts = non_empty.map(lambda value: len(value.split(FRACTAL_SEP)))
        short_rows = int((field_counts < 23).sum())
        warnings = []
        if short_rows:
            warnings.append("SHORT_FRACTAL0_ROWS")
        out[name] = {
            "non_empty_fractal0_rows": int(len(non_empty)),
            "short_fractal0_rows": short_rows,
            "min_field_count": int(field_counts.min()) if len(field_counts) else None,
            "median_field_count": float(field_counts.median()) if len(field_counts) else None,
            "warnings": warnings,
        }
    return out


def stage61_geometry_coverage(df: pd.DataFrame, profile: str) -> dict:
    token_counts = []
    min_coords = []
    max_coords = []
    above_counts = []
    below_counts = []
    for _, row in df.iterrows():
        if profile == "h12_nearest_price40_relative_geometry":
            frame = stage61_relative_fractal_frame(row, mode="nearest_price", k=40)
        elif profile == "h12_nearest_time40_relative_geometry":
            frame = stage61_relative_fractal_frame(row, mode="nearest_time", k=40)
        elif profile == "h12_corridor3_relative_geometry":
            frame = stage61_relative_fractal_frame(row, mode="corridor", k=100, corridor_atr=3.0)
        elif profile in {"h12_corridor10_relative_geometry", "h12_zones10_uniform_summary"}:
            frame = stage61_relative_fractal_frame(row, mode="corridor", k=100, corridor_atr=10.0)
        else:
            continue
        token_counts.append(len(frame))
        if frame.empty:
            continue
        min_coords.append(float(frame["price_coord_atr"].min()))
        max_coords.append(float(frame["price_coord_atr"].max()))
        above_counts.append(int((frame["price_coord_atr"] > 0).sum()))
        below_counts.append(int((frame["price_coord_atr"] < 0).sum()))
    warnings = []
    if token_counts and profile == "h12_corridor3_relative_geometry" and np.median(token_counts) < 1:
        warnings.append("CORRIDOR3_MEDIAN_LT_1")
    if token_counts and profile in {"h12_corridor10_relative_geometry", "h12_zones10_uniform_summary"} and np.median(token_counts) < 3:
        warnings.append("CORRIDOR10_MEDIAN_LT_3")
    rows_0 = float(np.mean(np.asarray(token_counts) == 0)) if token_counts else 1.0
    if rows_0 > 0.05:
        warnings.append("ROWS_WITH_0_TOKENS_GT_5PCT")
    min_coord = min(min_coords) if min_coords else None
    max_coord = max(max_coords) if max_coords else None
    corridor_bound = 3.0 if profile == "h12_corridor3_relative_geometry" else 10.0
    if profile in {"h12_corridor3_relative_geometry", "h12_corridor10_relative_geometry", "h12_zones10_uniform_summary"}:
        if min_coord is not None and min_coord < -corridor_bound - 0.0001:
            warnings.append("CORRIDOR_MIN_BELOW_BOUND")
        if max_coord is not None and max_coord > corridor_bound + 0.0001:
            warnings.append("CORRIDOR_MAX_ABOVE_BOUND")
    return {
        "n_rows": int(len(df)),
        "token_count": _stage61_quantiles(token_counts),
        "rows_with_0_tokens_rate": rows_0,
        "rows_with_1_2_tokens_rate": float(np.mean((np.asarray(token_counts) >= 1) & (np.asarray(token_counts) <= 2))) if token_counts else 0.0,
        "rows_with_3plus_tokens_rate": float(np.mean(np.asarray(token_counts) >= 3)) if token_counts else 0.0,
        "min_price_coord_atr": min_coord,
        "max_price_coord_atr": max_coord,
        "above_count": _stage61_quantiles(above_counts),
        "below_count": _stage61_quantiles(below_counts),
        "warnings": warnings,
    }


def stage61_feature_preflight(split: dict[str, pd.DataFrame]) -> dict:
    out = {}
    for profile in stage61_profile_keys():
        if profile == "h12_clock_shift_back":
            continue
        out[profile] = {
            name: stage61_geometry_coverage(df, profile)
            for name, df in split.items()
            if isinstance(df, pd.DataFrame)
        }
    return out
```

- [ ] **Step 4: Run tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage6_1_relative_geometry.py -q
```

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add ML/baseline/benchmark_stage6_1_relative_geometry.py tests/test_stage6_1_relative_geometry.py
git commit -m "feat: add stage 6.1 geometry preflight"
```

---

### Task 5: Definitive Touch Model Evaluation

**Files:**
- Modify: `ML/baseline/benchmark_stage6_1_relative_geometry.py`
- Modify: `tests/test_stage6_1_relative_geometry.py`

**Interfaces:**
- Produces:
  - `stage61_definitive_mask(df: pd.DataFrame) -> np.ndarray`
  - `stage61_permutation_feature_importance(model, X: np.ndarray, y: np.ndarray, profile: str, seed: int, top_n: int = 25) -> list[dict]`
  - `evaluate_stage61_profile_seed(split, feature_split, profile, seed) -> dict`

- [ ] **Step 1: Write failing tests for definitive mask**

Add:

```python
def test_stage61_definitive_mask_excludes_timeout_and_invalid():
    df = pd.DataFrame({
        "stage6_close_reason": ["TP", "SL", "AMBIGUOUS_SL_FIRST", "TIMEOUT", "INVALID"],
        "stage6_definitive_tp_vs_sl_flag": [1.0, 0.0, 0.0, np.nan, np.nan],
    })

    mask = s61.stage61_definitive_mask(df)

    assert mask.tolist() == [True, True, True, False, False]
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage6_1_relative_geometry.py::test_stage61_definitive_mask_excludes_timeout_and_invalid -q
```

Expected: fail with missing function.

- [ ] **Step 3: Implement definitive mask and evaluator**

Add:

```python
from sklearn.metrics import roc_auc_score
from xgboost import XGBClassifier


def stage61_definitive_mask(df: pd.DataFrame) -> np.ndarray:
    y = df["stage6_definitive_tp_vs_sl_flag"].to_numpy(dtype=np.float64)
    return np.isfinite(y)


def stage61_permutation_feature_importance(model,
                                           X: np.ndarray,
                                           y: np.ndarray,
                                           profile: str,
                                           seed: int,
                                           top_n: int = 25) -> list[dict]:
    if len(np.unique(y)) < 2:
        return []
    rng = np.random.default_rng(seed)
    names = stage61_feature_names(profile)
    baseline_score = float(roc_auc_score(y, model.predict_proba(X)[:, 1]))
    rows = []
    for col_idx, name in enumerate(names):
        X_perm = X.copy()
        X_perm[:, col_idx] = rng.permutation(X_perm[:, col_idx])
        perm_score = float(roc_auc_score(y, model.predict_proba(X_perm)[:, 1]))
        rows.append({
            "feature": name,
            "auc_drop": float(baseline_score - perm_score),
            "baseline_auc": baseline_score,
            "permuted_auc": perm_score,
        })
    rows.sort(key=lambda item: item["auc_drop"], reverse=True)
    return rows[:top_n]


def evaluate_stage61_profile_seed(split: dict[str, pd.DataFrame],
                                  feature_split: dict[str, np.ndarray],
                                  profile: str,
                                  seed: int) -> dict:
    train = split["train_core"]
    val = split["val_stop"]
    train_mask = stage61_definitive_mask(train)
    val_mask = stage61_definitive_mask(val)
    X_train = feature_split["train_core"]
    X_val = feature_split["val_stop"]
    y_train = train["stage6_definitive_tp_vs_sl_flag"].to_numpy(dtype=np.float64)
    y_val = val["stage6_definitive_tp_vs_sl_flag"].to_numpy(dtype=np.float64)
    clf = XGBClassifier(
        max_depth=6,
        learning_rate=0.03,
        n_estimators=500,
        subsample=0.8,
        colsample_bytree=0.8,
        early_stopping_rounds=20,
        random_state=seed,
        eval_metric="logloss",
        verbosity=0,
    )
    clf.fit(
        X_train[train_mask],
        y_train[train_mask],
        eval_set=[(X_val[val_mask], y_val[val_mask])],
        verbose=False,
    )
    val_score_def = clf.predict_proba(X_val[val_mask])[:, 1]
    val_score_all = clf.predict_proba(X_val)[:, 1]
    threshold = stage6_select_threshold_on_val(val.copy(), val_score_all)
    out = {
        "profile": profile,
        "seed": int(seed),
        "train_definitive_n": int(train_mask.sum()),
        "val_definitive_n": int(val_mask.sum()),
        "val_stop": stage6_binary_metrics(y_val[val_mask], val_score_def),
        "threshold_selection": threshold,
        "predictions": {
            "val_stop": {
                "y_true_definitive": y_val[val_mask].astype(int).tolist(),
                "y_score_definitive": val_score_def.tolist(),
                "y_score_all": val_score_all.tolist(),
                "pnl_r_all": val["stage6_pnl_r"].astype(float).tolist(),
            }
        },
        "feature_importance": [] if profile == "h12_clock_shift_back" else stage61_permutation_feature_importance(
            clf,
            X_val[val_mask],
            y_val[val_mask],
            profile,
            seed=seed,
        ),
    }
    for split_name in ("diagnostic_holdout", "low_n_disclosure"):
        df = split[split_name]
        X = feature_split[split_name]
        mask = stage61_definitive_mask(df)
        y = df["stage6_definitive_tp_vs_sl_flag"].to_numpy(dtype=np.float64)
        score_all = clf.predict_proba(X)[:, 1]
        score_def = score_all[mask]
        out[split_name] = stage6_binary_metrics(y[mask], score_def) if mask.any() else {}
        if threshold.get("status") == "SELECTED" and threshold.get("selected"):
            out[f"threshold_on_{split_name}"] = stage6_simulate_threshold(
                df.copy(), score_all, threshold["selected"]["threshold"]
            )
        else:
            out[f"threshold_on_{split_name}"] = None
    return out
```

- [ ] **Step 4: Run tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage6_1_relative_geometry.py -q
```

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add ML/baseline/benchmark_stage6_1_relative_geometry.py tests/test_stage6_1_relative_geometry.py
git commit -m "feat: add stage 6.1 definitive touch evaluator"
```

---

### Task 6: Runner, Gate And CLI

**Files:**
- Modify: `ML/baseline/benchmark_stage6_1_relative_geometry.py`
- Modify: `tests/test_stage6_1_relative_geometry.py`

**Interfaces:**
- Produces:
  - `stage61_gate_results(report: dict) -> dict`
  - `run_stage6_1_relative_geometry(output_path: Path = STAGE6_1_JSON_REPORT_PATH) -> dict`
  - CLI `./.venv/bin/python -m ML.baseline.benchmark_stage6_1_relative_geometry --stage6-1-relative-geometry`

- [ ] **Step 1: Write failing gate test**

Add:

```python
def test_stage61_gate_fails_when_no_threshold_even_if_auc_passes():
    report = {
        "summary": {
            "h12_corridor3_relative_geometry": {
                "val_stop": {"auc_median": 0.68, "pr_auc_lift_median": 0.12},
                "threshold_selection": {"status": "NO_THRESHOLD", "selected": None},
                "permutation_baseline": {"p_value": 0.03},
            }
        }
    }

    gate = s61.stage61_gate_results(report)

    assert gate["overall_status"] == "TRADING_GATE_FAILED"
    assert gate["artifact_status"] == "DIAGNOSTIC_ONLY"
    assert gate["checks"]["model_gate_pass"] is True
    assert gate["checks"]["threshold_selected"] is False


def test_stage61_gate_fails_when_permutation_p_value_is_high():
    report = {
        "summary": {
            "h12_corridor3_relative_geometry": {
                "val_stop": {"auc_median": 0.68, "pr_auc_lift_median": 0.12},
                "threshold_selection": {
                    "status": "SELECTED",
                    "selected": {
                        "pf": 1.2,
                        "trades_per_year": 30,
                        "pf_spread_020": 1.1,
                    },
                },
                "permutation_baseline": {"p_value": 0.50},
            }
        }
    }

    gate = s61.stage61_gate_results(report)

    assert gate["overall_status"] == "MODEL_GATE_FAILED"
    assert gate["checks"]["permutation_p_value_le_0_10"] is False
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage6_1_relative_geometry.py::test_stage61_gate_fails_when_no_threshold_even_if_auc_passes -q
```

Expected: fail with missing function.

- [ ] **Step 3: Implement gate and runner**

Add:

```python
def _stage61_median(values) -> float | None:
    vals = [v for v in values if v is not None and np.isfinite(v)]
    return float(np.median(vals)) if vals else None


def stage61_gate_results(report: dict) -> dict:
    summary = report.get("summary", {})
    primary = summary.get(STAGE6_1_CONFIG.primary_profile, {})
    val = primary.get("val_stop", {})
    threshold = primary.get("threshold_selection", {})
    checks = {
        "auc_ge_0_60": bool(val.get("auc_median") is not None and val["auc_median"] >= 0.60),
        "pr_auc_lift_ge_0_05": bool(val.get("pr_auc_lift_median") is not None and val["pr_auc_lift_median"] >= 0.05),
        "permutation_p_value_le_0_10": bool(
            primary.get("permutation_baseline", {}).get("p_value") is not None
            and primary["permutation_baseline"]["p_value"] <= 0.10
        ),
        "threshold_selected": bool(threshold.get("status") == "SELECTED" and threshold.get("selected") is not None),
    }
    checks["model_gate_pass"] = (
        checks["auc_ge_0_60"]
        and checks["pr_auc_lift_ge_0_05"]
        and checks["permutation_p_value_le_0_10"]
    )
    if not checks["model_gate_pass"]:
        return {"overall_status": "MODEL_GATE_FAILED", "artifact_status": "DIAGNOSTIC_ONLY", "checks": checks}
    if not checks["threshold_selected"]:
        return {"overall_status": "TRADING_GATE_FAILED", "artifact_status": "DIAGNOSTIC_ONLY", "checks": checks}
    selected = threshold["selected"]
    checks["val_pf_ge_1_15"] = bool(selected.get("pf") is not None and selected["pf"] >= 1.15)
    checks["val_trades_per_year_ge_25"] = bool(selected.get("trades_per_year", 0) >= 25)
    checks["spread_020_pf_ge_1_05"] = bool(selected.get("pf_spread_020") is not None and selected["pf_spread_020"] >= 1.05)
    if all(checks.values()):
        return {"overall_status": "DIAGNOSTIC_SIGNAL_FOUND", "artifact_status": "DIAGNOSTIC_ONLY", "checks": checks}
    return {"overall_status": "TRADING_GATE_FAILED", "artifact_status": "DIAGNOSTIC_ONLY", "checks": checks}


def run_stage6_1_relative_geometry(output_path: Path = STAGE6_1_JSON_REPORT_PATH) -> dict:
    import time
    started = time.time()
    cfg = replace(
        STAGE6_0_CONFIG,
        horizon_bars=STAGE6_1_CONFIG.horizon_bars,
        stop_offset_atr=STAGE6_1_CONFIG.stop_offset_atr,
        take_profit_atr=STAGE6_1_CONFIG.take_profit_atr,
        entry_lag_bars=STAGE6_1_CONFIG.entry_lag_bars,
    )
    split = stage6_load_labeled_splits(config=cfg)
    report = {
        "stage": "6.1",
        "status": "RUNNING",
        "config": {
            "horizon_bars": STAGE6_1_CONFIG.horizon_bars,
            "profiles": list(STAGE6_1_CONFIG.profile_keys),
            "primary_profile": STAGE6_1_CONFIG.primary_profile,
            "seeds": list(STAGE6_1_CONFIG.seeds),
            "target": "stage6_definitive_tp_vs_sl_flag",
            "ohlc_file": str(OHLC_FILE),
        },
        "input_manifest": stage61_input_file_manifest(),
        "fractal_format_preflight": stage61_fractal_format_preflight(split),
        "preflight": stage6_outcome_preflight(split),
        "feature_preflight": stage61_feature_preflight(split),
        "oracle_preflight": {
            name: stage6_all_trade_baseline(df)
            for name, df in split.items()
            if isinstance(df, pd.DataFrame)
        },
        "raw_runs": [],
        "done_runs": 0,
        "total_runs": len(STAGE6_1_CONFIG.profile_keys) * len(STAGE6_1_CONFIG.seeds),
    }
    for profile in STAGE6_1_CONFIG.profile_keys:
        feature_split = {
            name: stage61_build_features(df, profile)
            for name, df in split.items()
            if isinstance(df, pd.DataFrame)
        }
        for seed in STAGE6_1_CONFIG.seeds:
            result = evaluate_stage61_profile_seed(split, feature_split, profile, seed)
            report["raw_runs"].append(result)
            report["done_runs"] += 1
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps(report, indent=2, default=str))
    summary = {}
    for profile in STAGE6_1_CONFIG.profile_keys:
        runs = [r for r in report["raw_runs"] if r["profile"] == profile]
        aucs = [r["val_stop"].get("auc") for r in runs]
        lifts = [r["val_stop"].get("pr_auc_lift") for r in runs]
        selected = [
            r["threshold_selection"]["selected"]
            for r in runs
            if r["threshold_selection"].get("status") == "SELECTED" and r["threshold_selection"].get("selected")
        ]
        best_run = max(runs, key=lambda r: r["val_stop"].get("auc") or 0.0)
        perm = None
        val_scores = best_run.get("predictions", {}).get("val_stop", {}).get("y_score_all", [])
        if val_scores:
            perm = stage6_permutation_threshold_baseline(split["val_stop"].copy(), np.asarray(val_scores), seed=42)
        summary[profile] = {
            "val_stop": {
                "auc_median": _stage61_median(aucs),
                "pr_auc_lift_median": _stage61_median(lifts),
            },
            "threshold_selection": {
                "status": "SELECTED" if selected else "NO_THRESHOLD",
                "selected": selected[len(selected) // 2] if selected else None,
                "n_selected": len(selected),
                "val_pf_median": _stage61_median([s.get("pf") for s in selected]),
            },
            "threshold_on_diagnostic": best_run.get("threshold_on_diagnostic_holdout"),
            "permutation_baseline": perm,
        }
    report["summary"] = summary
    report["gate"] = stage61_gate_results(report)
    report["status"] = report["gate"]["overall_status"]
    report["elapsed_sec"] = float(time.time() - started)
    output_path.write_text(json.dumps(report, indent=2, default=str))
    return report


def main(argv: list[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage6-1-relative-geometry", action="store_true")
    args = parser.parse_args(argv)
    if args.stage6_1_relative_geometry:
        report = run_stage6_1_relative_geometry()
        print({"status": report.get("status"), "json": str(STAGE6_1_JSON_REPORT_PATH)})
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run focused tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage6_1_relative_geometry.py -q
```

Expected: pass.

- [ ] **Step 5: Run full tests**

Run:

```bash
./.venv/bin/python -m pytest tests/ -q
```

Expected: pass.

- [ ] **Step 6: Commit**

```bash
git add ML/baseline/benchmark_stage6_1_relative_geometry.py tests/test_stage6_1_relative_geometry.py
git commit -m "feat: add stage 6.1 relative geometry runner"
```

---

### Task 7: Full Run, Report, Handoff And Wiki

**Files:**
- Generated: `ML/reports/stage6_1_h12_relative_fractal_geometry.json`
- Create: `docs/reports/2026-06-29-stage6_1-h12-relative-fractal-geometry.md`
- Modify: `CHANGELOG.md`
- Modify: `CONTEXT_HANDOFF.md`
- Modify: `wiki/research/fractal-stop-research.md`, `wiki/index.md`, `wiki/log.md`, `wiki/REPO_integrity.md`

**Interfaces:**
- Consumes: Stage 6.1 CLI and JSON artifact.
- Produces: final report and current handoff.

- [ ] **Step 1: Run Stage 6.1**

Run:

```bash
./.venv/bin/python -u -m ML.baseline.benchmark_stage6_1_relative_geometry --stage6-1-relative-geometry
```

Expected:

- JSON exists at `ML/reports/stage6_1_h12_relative_fractal_geometry.json`.
- `done_runs == total_runs == 18`.
- command prints final status.

- [ ] **Step 2: Inspect JSON invariants**

Run:

```bash
./.venv/bin/python - <<'PY'
import json
from pathlib import Path

path = Path("ML/reports/stage6_1_h12_relative_fractal_geometry.json")
data = json.loads(path.read_text())
assert data["done_runs"] == data["total_runs"] == 18
assert len(data["raw_runs"]) == 18
assert set(data["summary"]) == {
    "h12_clock_shift_back",
    "h12_nearest_price40_relative_geometry",
    "h12_nearest_time40_relative_geometry",
    "h12_corridor3_relative_geometry",
    "h12_corridor10_relative_geometry",
    "h12_zones10_uniform_summary",
}
assert "feature_preflight" in data
assert set(data["input_manifest"]) == {"ohlc", "train_labeled", "validation_labeled", "test_labeled"}
assert all(len(item["sha256"]) == 64 for item in data["input_manifest"].values())
assert "fractal_format_preflight" in data
assert all(not item["warnings"] for item in data["fractal_format_preflight"].values())
assert "gate" in data
print({
    "status": data["status"],
    "primary_auc": data["summary"]["h12_corridor3_relative_geometry"]["val_stop"]["auc_median"],
    "primary_threshold": data["summary"]["h12_corridor3_relative_geometry"]["threshold_selection"]["status"],
})
PY
```

Expected: prints status and primary metrics without assertion error.

- [ ] **Step 3: Write report from JSON**

Create `docs/reports/2026-06-29-stage6_1-h12-relative-fractal-geometry.md` with these required sections:

- Context
- What Was Done
- Multiple Testing Context
- Changed Files
- Verification
- Results
- Conclusions
- Limitations / Open Questions
- Validation Split Disclosure
- Next Step
- Related Materials

Report must state:

- H12 was fixed before training.
- Main target is definitive TP-vs-SL touch; timeout is excluded from model labels but included in trading PF.
- Feature profiles and search budget: 6 profiles × 3 seeds = 18.
- Input file manifest: path, row count, byte size, SHA256 for OHLC/train/validation/test CSV.
- A7 coverage for nearest/corridor/zones.
- Primary gate result for `h12_corridor3_relative_geometry`.
- Top validation permutation feature importance for every non-baseline geometry profile.
- Diagnostic holdout is disclosure only and did not influence profile selection, seed selection, threshold selection, or gate.

- [ ] **Step 4: Update handoff and changelog**

Update:

- `CONTEXT_HANDOFF.md`: current Stage 6.1 status, artifact/report paths, next step, prohibited next actions.
- `CHANGELOG.md`: one top entry with changed files, run size, key numbers, status, next direction.

- [ ] **Step 5: Update wiki**

Update `wiki/research/fractal-stop-research.md`, `wiki/index.md`, and `wiki/log.md`, then run:

```bash
./.venv/bin/python wiki/wiki.py generate
./.venv/bin/python wiki/wiki.py status
```

Expected: `Wiki is up to date. No gaps found.`

- [ ] **Step 6: Final verification**

Run:

```bash
./.venv/bin/python -m pytest tests/ -q
```

Expected: pass.

- [ ] **Step 7: Commit**

```bash
git add ML/reports/stage6_1_h12_relative_fractal_geometry.json \
  docs/reports/2026-06-29-stage6_1-h12-relative-fractal-geometry.md \
  CHANGELOG.md CONTEXT_HANDOFF.md wiki
git commit -m "docs: report stage 6.1 relative geometry"
```

---

## Stop Conditions

Stop before training and report if any condition holds:

- Fractal parser contract does not match Stage 5.1b indices, or real rows have fewer than 23 colon-separated fields in non-empty `fractal0`.
- `input_manifest` cannot record SHA256 and row counts for OHLC/train/validation/test input files.
- H12 `val_stop` timeout rate remains above `35%`.
- `h12_corridor3_relative_geometry` median token count is below `1`.
- `h12_corridor10_relative_geometry` median token count is below `3`.
- Any corridor profile has `min_price_coord_atr < -10.0001` or `max_price_coord_atr > 10.0001`.
- Any Stage 6 target column appears in feature matrices.
- A7 preflight has `ERROR`.

Stop after training and report if:

- primary profile median val AUC is below `0.60`;
- no threshold reaches minimum validation trades;
- selected threshold exists only in one validation year;
- spread 0.20 PF is below `1.05`;
- permutation p-value is above `0.10`.

---

## Self-Review Checklist

- Testable hypothesis is stated before implementation.
- H12 is fixed; H6/H24 are not tuned in this plan.
- Fractal string contract is explicit and tested against Stage 5.1b field indices.
- Raw absolute fractal price is not used as primary input.
- No per-fractal ATR ratio is used; the known parser does not expose a trusted per-fractal ATR field.
- Relative price coordinate is ATR-normalized against `fractal0`.
- Price-nearest and time-nearest profiles are separate, so price proximity is not confused with recency.
- 3 ATR corridor is the primary local geometry profile; 10 ATR remains a wide control.
- Zone summary uses uniform 1 ATR buckets from -10 ATR to +10 ATR.
- Timeout is excluded from model labels but included in trading PF.
- Corridor/nearest/zones pass A7 coverage before model interpretation.
- Gate requires permutation p-value `<= 0.10`, not only AUC and PR lift.
- Report includes top validation permutation feature importance for every geometry profile.
- Report includes input file hashes and row counts, because Stage 6 labels are recomputed from the current OHLC file.
- `2023-2025` and `2026` are disclosure only.
- Stage 6.1 cannot emit `CANDIDATE`.
