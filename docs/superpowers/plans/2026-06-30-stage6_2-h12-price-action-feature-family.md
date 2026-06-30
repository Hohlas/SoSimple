# Stage 6.2 H12 Price Action Feature Family Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Test whether recent OHLC price action adds useful H12 TP/SL touch signal beyond the existing `h12_clock_shift_back` baseline.

**Architecture:** Add a separate Stage 6.2 runner that reuses Stage 6.0 labels, threshold simulation, permutation check, and Stage 6.1 runtime pattern. The new feature family joins each labeled row to historical OHLC bars ending at the row `time`, builds fixed price-action features, trains XGBoost over fixed profiles, and reports standalone plus baseline-delta results.

**Tech Stack:** Python 3.10+, pandas, numpy, sklearn metrics, xgboost, pytest, existing `./.venv/bin/python`, existing `DATA/Nero_XAUUSD_*_labeled.csv`, OHLC source `DATA/XAUUSD_H1_OHLC.csv`.

## Global Constraints

- Work on the current branch; do not use git worktree.
- Use `./.venv/bin/python` for all Python commands.
- New Python code must be covered by tests before implementation.
- After Python changes, run focused Stage 6.2 tests. Run the full suite before final closure only after confirming it does not trigger long training jobs.
- Stage 6.2 is exploratory and maximum artifact status is `DIAGNOSTIC_ONLY` until execution timing, spread convention, simulator parity, and independent validation are proven.
- Use fixed Stage 6.1 trading contract: XAUUSD H1, H12, entry `Open[row+1]`, stop `0.5 ATR`, take `2.0 ATR`, same-bar ambiguity as SL-first.
- Do not open a broad search over horizon/ATR/TP/SL. H12 and barrier values are frozen. H12 is used because this is the fixed continuation of the current H12 branch, not because H12 is assumed to be the best horizon.
- Do not use `2023-2025` or `2026` for profile, seed, threshold, or gate selection.
- Use `val_stop` (`2021-2022`) only for selection and gates; `diagnostic_holdout` (`2023-2025`) and `low_n_disclosure` (`2026`) are disclosure-only.
- New features must not include `stage6_*`, `trade_*`, `fav_*`, `adv_*`, `ret_*`, `path_*`, stop-breach labels, bars-to-breach labels, or other future-derived columns.
- Price-action features may use only OHLC bars with timestamp `<= row.time`. `row.time` must match a closed OHLC bar. Features must not read `Open[row+1]`, the entry bar, future H12 bars, or labels.
- Use fixed XGBoost `n_jobs=24`, heartbeat, top-level and per-run `elapsed_sec`, initial checkpoint, checkpoint after every run, and `--resume` / `--no-resume`.
- Record SHA256, row count, and byte count for all input files in JSON.
- Save `feature_names` and `feature_names_sha256` for every profile in JSON.
- Report top validation permutation feature importance for each non-baseline profile.

---

## Fixed Research Contract

**Research level:** exploratory. Result may justify a later confirmatory plan, but cannot become production candidate in this stage.

**Testable hypothesis:** recent price path and candle structure before `fractal0` confirmation carry information about which H12 barrier is touched first. The expected mechanism is simple:

- strong movement into `fractal0`, compressed or expanded recent range, and close position near recent extremes may change the probability of immediate continuation versus reversal;
- ATR and source volume state may distinguish quiet setups from unstable ones. In Forex this is treated as broker/source volume, not real exchange volume, unless the data source proves otherwise;
- if this information is real, it should either work standalone or add a visible improvement over `h12_clock_shift_back`.

**Primary profile:** `h12_price_action_core`.

**Profiles:**

| Profile | Purpose |
|---|---|
| `h12_clock_shift_back` | Existing Stage 6.1 baseline/control |
| `h12_price_action_core` | Primary OHLC-only price-action family |
| `h12_price_action_regime` | Same family plus ATR/volume state |
| `h12_clock_shift_back_plus_price_action_core` | Delta test against baseline |
| `h12_clock_shift_back_plus_price_action_regime` | Delta test against baseline with regime fields |

**Search budget:** 5 profiles × 3 seeds `(42, 77, 123)` = 15 model runs.

**Feature windows:** `(1, 3, 6, 12, 24)` H1 bars ending at `row.time`. Rows with fewer than 24 historical OHLC bars are allowed but counted in preflight as incomplete-window rows.

**Core features per window:**

- `ret_close_w{w}_atr`: `(close_t - close_{t-w}) / ATR_row`
- `range_w{w}_atr`: `(max(high) - min(low)) / ATR_row`
- `close_to_high_w{w}_atr`: `(max(high) - close_t) / ATR_row`
- `close_to_low_w{w}_atr`: `(close_t - min(low)) / ATR_row`
- `close_pos_w{w}`: `(close_t - min(low)) / max(max(high)-min(low), eps)`

**Single-bar candle features:**

- `body_1_atr`: `(close_t - open_t) / ATR_row`
- `abs_body_1_atr`: `abs(close_t - open_t) / ATR_row`
- `upper_wick_1_atr`: `(high_t - max(open_t, close_t)) / ATR_row`
- `lower_wick_1_atr`: `(min(open_t, close_t) - low_t) / ATR_row`
- `bar_range_1_atr`: `(high_t - low_t) / ATR_row`

**Regime add-on features:**

- `atr14_to_atr_row`: `atr14_t / ATR_row`
- `atr14_to_atr14_mean_24`: `atr14_t / mean(atr14 over last 24 bars)`
- `source_volume_to_source_volume_mean_24`: `volume_t / mean(volume over last 24 bars)`
- `range_24_to_atr14`: `(max(high_24)-min(low_24)) / atr14_t`

**Gate:**

Primary standalone gate for `h12_price_action_core`:

- median `val_stop` AUC >= `0.60`;
- median `val_stop` PR AUC lift >= `0.05`;
- threshold selected on `val_stop`;
- permutation `empirical_p_value <= 0.10`;
- median selected PF >= `1.15`;
- selected trades per year >= `25`;
- spread `0.20` PF >= `1.05`.

Delta gate for combined profiles against `h12_clock_shift_back`:

- AUC delta >= `+0.02`;
- PR AUC lift delta >= `0.00`;
- threshold selected;
- median selected PF not worse than baseline;
- permutation `empirical_p_value <= 0.10`.

Overall status:

- `DIAGNOSTIC_SIGNAL_FOUND` only if standalone gate or delta gate passes. If only standalone passes while combined profiles do not improve `h12_clock_shift_back`, the report must state: `standalone signal exists, but no additive value over baseline was found`.
- `MODEL_GATE_FAILED` if model metrics fail.
- `TRADING_GATE_FAILED` if model metrics pass but no acceptable threshold/PF exists.

**Baseline comparison rule:** all Stage 6.2 comparisons must use the `h12_clock_shift_back` baseline recomputed inside the same Stage 6.2 JSON. Do not compare gates against Stage 6.1 numbers by eye.

---

## File Structure

**Create**

- `ML/baseline/benchmark_stage6_2_price_action.py` — Stage 6.2 feature builders, preflight, runner, summary, gate, CLI.
- `tests/test_stage6_2_price_action.py` — unit tests for feature contract, OHLC joining, no-future windows, feature names, gate, runtime metadata, resume.

**Modify after execution**

- `docs/reports/2026-06-30-stage6_2-h12-price-action-feature-family.md` — canonical report after full run.
- `CHANGELOG.md` — final short result.
- `CONTEXT_HANDOFF.md` — current state and next step.
- `wiki/research/fractal-stop-research.md`, `wiki/index.md`, `wiki/log.md`, `wiki/REPO_integrity.md` — after report ingest.

**Generated**

- `ML/reports/stage6_2_h12_price_action_feature_family.json`.

**Read before implementation**

- `docs/methodology/00-research-management.md`
- `docs/methodology/03-feature-contract-leakage.md`
- `docs/methodology/05-eda-data-quality.md`
- `docs/methodology/08-model-development.md`
- `docs/methodology/09-validation-freeze.md`
- `docs/methodology/11-robustness.md`
- `docs/methodology/16-reporting-audit.md`
- `docs/reports/2026-06-29-stage6_1-h12-relative-fractal-geometry.md`
- `ML/baseline/benchmark_stage6_1_relative_geometry.py`
- `ML/baseline/benchmark_stage6_outcome_based.py`

---

### Task 1: Stage 6.2 Contract And Skeleton

**Files:**
- Create: `ML/baseline/benchmark_stage6_2_price_action.py`
- Create: `tests/test_stage6_2_price_action.py`

**Interfaces:**
- Produces:
  - `Stage62Config`
  - `STAGE6_2_CONFIG`
  - `STAGE6_2_JSON_REPORT_PATH`
  - `stage62_profile_keys() -> tuple[str, ...]`
  - `stage62_feature_denylist() -> tuple[str, ...]`
  - `stage62_input_file_manifest() -> dict`

- [ ] **Step 1: Write failing contract tests**

Add to `tests/test_stage6_2_price_action.py`:

```python
import inspect
import json
import subprocess
import sys

import numpy as np
import pandas as pd

import ML.baseline.benchmark_stage6_2_price_action as s62


def test_stage62_config_is_fixed_and_narrow():
    cfg = s62.STAGE6_2_CONFIG

    assert cfg.horizon_bars == 12
    assert cfg.stop_offset_atr == 0.5
    assert cfg.take_profit_atr == 2.0
    assert cfg.entry_lag_bars == 1
    assert cfg.primary_profile == "h12_price_action_core"
    assert cfg.profile_keys == (
        "h12_clock_shift_back",
        "h12_price_action_core",
        "h12_price_action_regime",
        "h12_clock_shift_back_plus_price_action_core",
        "h12_clock_shift_back_plus_price_action_regime",
    )
    assert cfg.seeds == (42, 77, 123)
    assert cfg.windows == (1, 3, 6, 12, 24)
    assert cfg.xgb_n_jobs == 24


def test_stage62_feature_denylist_blocks_future_columns():
    denylist = set(s62.stage62_feature_denylist())

    assert "stage6_definitive_tp_vs_sl_flag" in denylist
    assert "stage6_pnl_r" in denylist
    assert "trade_fav_h12" in denylist
    assert "fav_12_atr" in denylist
    assert "ret_12_dir_atr" in denylist
    assert "buy_bars_to_breach_H12_off05" in denylist
    assert "sell_stop_broken_H12_off05_flag" in denylist
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage6_2_price_action.py -q
```

Expected: fail with `ModuleNotFoundError` or missing symbols.

- [ ] **Step 3: Create minimal module**

Create `ML/baseline/benchmark_stage6_2_price_action.py`:

```python
from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np
import pandas as pd
from xgboost import XGBClassifier

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ML.baseline.benchmark_stage5_transformer_breach import (
    build_stage5_4_features,
    stage5_4_feature_names,
)
from ML.baseline.benchmark_stage6_outcome_based import (
    DATA_DIR,
    OHLC_FILE,
    REPORTS_DIR,
    STAGE6_0_CONFIG,
    stage6_all_trade_baseline,
    stage6_binary_metrics,
    stage6_feature_denylist,
    stage6_load_labeled_splits,
    stage6_outcome_preflight,
    stage6_permutation_threshold_baseline,
    stage6_select_threshold_on_val,
    stage6_simulate_threshold,
)


STAGE6_2_JSON_REPORT_PATH = REPORTS_DIR / "stage6_2_h12_price_action_feature_family.json"


@dataclass(frozen=True)
class Stage62Config:
    horizon_bars: int = 12
    stop_offset_atr: float = 0.5
    take_profit_atr: float = 2.0
    entry_lag_bars: int = 1
    primary_profile: str = "h12_price_action_core"
    profile_keys: tuple[str, ...] = (
        "h12_clock_shift_back",
        "h12_price_action_core",
        "h12_price_action_regime",
        "h12_clock_shift_back_plus_price_action_core",
        "h12_clock_shift_back_plus_price_action_regime",
    )
    seeds: tuple[int, ...] = (42, 77, 123)
    windows: tuple[int, ...] = (1, 3, 6, 12, 24)
    xgb_n_jobs: int = 24


STAGE6_2_CONFIG = Stage62Config()
```

Add the denylist and manifest:

```python
def stage62_profile_keys() -> tuple[str, ...]:
    return STAGE6_2_CONFIG.profile_keys


def stage62_feature_denylist() -> tuple[str, ...]:
    prefixes = (
        "stage6_",
        "trade_",
        "fav_",
        "adv_",
        "ret_",
        "path_",
    )
    explicit = (
        "predict",
        "signal",
        "archetype_target",
        "trade_fav_h12",
        "trade_adv_h12",
        "trade_fav_h12_atr",
        "trade_adv_h12_atr",
        "trade_outcome_h12",
        "trade_pnl_h12_atr",
        "ret_6_dir_atr",
        "ret_12_dir_atr",
        "ret_24_dir_atr",
        "fav_3_atr",
        "adv_3_atr",
        "fav_6_atr",
        "adv_6_atr",
        "fav_12_atr",
        "adv_12_atr",
        "fav_24_atr",
        "adv_24_atr",
        "path_6_class",
        "buy_sl2_tp3",
        "buy_sl2_tp6",
        "buy_sl2_tp9",
        "buy_sl3_tp3",
        "buy_sl3_tp6",
        "buy_sl3_tp9",
        "sell_sl2_tp3",
        "sell_sl2_tp6",
        "sell_sl2_tp9",
        "sell_sl3_tp3",
        "sell_sl3_tp6",
        "sell_sl3_tp9",
    )
    breach_flags = tuple(
        f"{side}_stop_broken_H{h}_off{off}_flag"
        for side in ("buy", "sell")
        for h in (6, 12)
        for off in ("00", "02", "05")
    )
    breach_bars = tuple(
        f"{side}_bars_to_breach_H{h}_off{off}"
        for side in ("buy", "sell")
        for h in (6, 12)
        for off in ("00", "02", "05")
    )
    return tuple(stage6_feature_denylist()) + explicit + breach_flags + breach_bars + prefixes
```

```python
def stage62_input_file_manifest() -> dict:
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
./.venv/bin/python -m pytest tests/test_stage6_2_price_action.py -q
```

Expected: current contract tests pass.

- [ ] **Step 5: Checkpoint / review**

```bash
git diff -- ML/baseline/benchmark_stage6_2_price_action.py tests/test_stage6_2_price_action.py
```

---

### Task 2: Live-Safe OHLC Feature Builder

**Files:**
- Modify: `ML/baseline/benchmark_stage6_2_price_action.py`
- Modify: `tests/test_stage6_2_price_action.py`

**Interfaces:**
- Produces:
  - `stage62_load_ohlc_frame(path: Path = OHLC_FILE) -> pd.DataFrame`
  - `stage62_price_action_feature_names(profile: str) -> list[str]`
  - `stage62_build_price_action_features(df: pd.DataFrame, profile: str, ohlc: pd.DataFrame | None = None) -> np.ndarray`
  - `stage62_build_features(df: pd.DataFrame, profile: str, ohlc: pd.DataFrame | None = None) -> np.ndarray`

- [ ] **Step 1: Write failing no-future feature tests**

Add:

```python
def _tiny_ohlc():
    return pd.DataFrame({
        "time": pd.date_range("2021-01-01 00:00", periods=30, freq="h"),
        "open": np.arange(100.0, 130.0),
        "high": np.arange(101.0, 131.0),
        "low": np.arange(99.0, 129.0),
        "close": np.arange(100.5, 130.5),
        "volume": np.arange(1000.0, 1030.0),
        "atr14": np.full(30, 2.0),
    })


def test_stage62_price_action_uses_only_bars_at_or_before_row_time():
    ohlc = _tiny_ohlc()
    row_time = ohlc.loc[24, "time"].strftime("%Y.%m.%d %H:%M")
    df = pd.DataFrame({"time": [row_time], "ATR": [2.0]})

    X_before = s62.stage62_build_price_action_features(df, "h12_price_action_core", ohlc=ohlc)
    ohlc_future_changed = ohlc.copy()
    ohlc_future_changed.loc[25:, ["open", "high", "low", "close"]] = 9999.0
    X_after = s62.stage62_build_price_action_features(df, "h12_price_action_core", ohlc=ohlc_future_changed)

    np.testing.assert_allclose(X_before, X_after)


def test_stage62_price_action_does_not_read_entry_open_row_plus_one():
    ohlc = _tiny_ohlc()
    row_time = ohlc.loc[24, "time"].strftime("%Y.%m.%d %H:%M")
    df = pd.DataFrame({"time": [row_time], "ATR": [2.0]})

    X_before = s62.stage62_build_price_action_features(df, "h12_price_action_core", ohlc=ohlc)
    ohlc_entry_open_changed = ohlc.copy()
    ohlc_entry_open_changed.loc[25, "open"] = 9999.0
    X_after = s62.stage62_build_price_action_features(df, "h12_price_action_core", ohlc=ohlc_entry_open_changed)

    np.testing.assert_allclose(X_before, X_after)


def test_stage62_price_action_features_have_stable_names_and_shape():
    ohlc = _tiny_ohlc()
    df = pd.DataFrame({
        "time": [ohlc.loc[24, "time"].strftime("%Y.%m.%d %H:%M")],
        "ATR": [2.0],
    })

    X_core = s62.stage62_build_price_action_features(df, "h12_price_action_core", ohlc=ohlc)
    X_regime = s62.stage62_build_price_action_features(df, "h12_price_action_regime", ohlc=ohlc)

    assert X_core.shape == (1, len(s62.stage62_price_action_feature_names("h12_price_action_core")))
    assert X_regime.shape == (1, len(s62.stage62_price_action_feature_names("h12_price_action_regime")))
    assert "ret_close_w12_atr" in s62.stage62_price_action_feature_names("h12_price_action_core")
    assert "source_volume_to_source_volume_mean_24" in s62.stage62_price_action_feature_names("h12_price_action_regime")
    assert np.isfinite(X_core).all()
    assert np.isfinite(X_regime).all()
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage6_2_price_action.py -q
```

Expected: fail on missing feature builder functions.

- [ ] **Step 3: Implement OHLC loader and feature names**

Add:

```python
CORE_WINDOWS = STAGE6_2_CONFIG.windows
CORE_WINDOW_FIELDS = (
    "ret_close",
    "range",
    "close_to_high",
    "close_to_low",
    "close_pos",
)
CANDLE_FIELDS = (
    "body_1_atr",
    "abs_body_1_atr",
    "upper_wick_1_atr",
    "lower_wick_1_atr",
    "bar_range_1_atr",
)
REGIME_FIELDS = (
    "atr14_to_atr_row",
    "atr14_to_atr14_mean_24",
    "source_volume_to_source_volume_mean_24",
    "range_24_to_atr14",
)


def stage62_load_ohlc_frame(path: Path = OHLC_FILE) -> pd.DataFrame:
    df = pd.read_csv(path, sep=";")
    df["time"] = pd.to_datetime(df["time"], format="%Y.%m.%d %H:%M", errors="coerce")
    df = df.dropna(subset=["time"]).sort_values("time").reset_index(drop=True)
    for col in ("open", "high", "low", "close", "volume", "atr14"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def stage62_price_action_feature_names(profile: str) -> list[str]:
    names = [
        f"{field}_w{window}_atr" if field != "close_pos" else f"{field}_w{window}"
        for window in CORE_WINDOWS
        for field in CORE_WINDOW_FIELDS
    ]
    names.extend(CANDLE_FIELDS)
    if profile == "h12_price_action_regime":
        names.extend(REGIME_FIELDS)
    if profile == "h12_price_action_core":
        return names
    if profile == "h12_price_action_regime":
        return names
    raise ValueError(f"not a price-action profile: {profile}")
```

- [ ] **Step 4: Implement row feature extraction**

Add:

```python
def _stage62_parse_time(value) -> pd.Timestamp | None:
    ts = pd.to_datetime(value, format="%Y.%m.%d %H:%M", errors="coerce")
    if pd.isna(ts):
        return None
    return pd.Timestamp(ts)


def _stage62_safe_div(num: float, den: float) -> float:
    if not np.isfinite(num) or not np.isfinite(den) or abs(den) < 1e-12:
        return 0.0
    return float(num / den)


def _stage62_ohlc_position(row_time: pd.Timestamp, ohlc: pd.DataFrame) -> int | None:
    times = ohlc["time"].to_numpy(dtype="datetime64[ns]")
    pos = int(np.searchsorted(times, np.datetime64(row_time), side="right") - 1)
    if pos < 0:
        return None
    if pd.Timestamp(ohlc.iloc[pos]["time"]) != row_time:
        return None
    return pos


def _stage62_price_action_row(row: pd.Series, ohlc: pd.DataFrame, profile: str) -> list[float]:
    row_time = _stage62_parse_time(row.get("time"))
    atr_row = float(row.get("ATR", 0.0) or 0.0)
    if row_time is None or atr_row <= 0.0:
        return [0.0] * len(stage62_price_action_feature_names(profile))

    pos = _stage62_ohlc_position(row_time, ohlc)
    if pos is None:
        return [0.0] * len(stage62_price_action_feature_names(profile))
    start = max(0, pos - max(CORE_WINDOWS))
    hist = ohlc.iloc[start:pos + 1]

    current = hist.iloc[-1]
    close_t = float(current["close"])
    open_t = float(current["open"])
    high_t = float(current["high"])
    low_t = float(current["low"])

    out: list[float] = []
    for window in CORE_WINDOWS:
        segment = hist.tail(window + 1)
        if len(segment) < window + 1:
            out.extend([0.0, 0.0, 0.0, 0.0, 0.0])
            continue
        prev_close = float(segment.iloc[0]["close"])
        max_high = float(segment["high"].max())
        min_low = float(segment["low"].min())
        width = max_high - min_low
        out.extend([
            _stage62_safe_div(close_t - prev_close, atr_row),
            _stage62_safe_div(width, atr_row),
            _stage62_safe_div(max_high - close_t, atr_row),
            _stage62_safe_div(close_t - min_low, atr_row),
            _stage62_safe_div(close_t - min_low, width),
        ])

    out.extend([
        _stage62_safe_div(close_t - open_t, atr_row),
        _stage62_safe_div(abs(close_t - open_t), atr_row),
        _stage62_safe_div(high_t - max(open_t, close_t), atr_row),
        _stage62_safe_div(min(open_t, close_t) - low_t, atr_row),
        _stage62_safe_div(high_t - low_t, atr_row),
    ])

    if profile == "h12_price_action_regime":
        hist24 = hist.tail(24)
        atr14_t = float(current.get("atr14", 0.0) or 0.0)
        volume_t = float(current.get("volume", 0.0) or 0.0)
        atr14_mean_24 = float(hist24["atr14"].mean()) if len(hist24) else 0.0
        volume_mean_24 = float(hist24["volume"].mean()) if len(hist24) else 0.0
        range_24 = float(hist24["high"].max() - hist24["low"].min()) if len(hist24) else 0.0
        out.extend([
            _stage62_safe_div(atr14_t, atr_row),
            _stage62_safe_div(atr14_t, atr14_mean_24),
            _stage62_safe_div(volume_t, volume_mean_24),
            _stage62_safe_div(range_24, atr14_t),
        ])
    return [float(np.nan_to_num(v, nan=0.0, posinf=0.0, neginf=0.0)) for v in out]
```

- [ ] **Step 5: Implement matrix builders**

Add:

```python
def stage62_build_price_action_features(
    df: pd.DataFrame,
    profile: str,
    ohlc: pd.DataFrame | None = None,
) -> np.ndarray:
    if profile not in {"h12_price_action_core", "h12_price_action_regime"}:
        raise ValueError(f"not a price-action profile: {profile}")
    frame = stage62_load_ohlc_frame() if ohlc is None else ohlc.copy()
    rows = [_stage62_price_action_row(row, frame, profile) for _, row in df.iterrows()]
    width = len(stage62_price_action_feature_names(profile))
    if not rows:
        return np.zeros((0, width), dtype=np.float32)
    return np.asarray(rows, dtype=np.float32)
```

Add baseline/combined dispatcher:

```python
COMBINED_TO_PRICE_ACTION = {
    "h12_clock_shift_back_plus_price_action_core": "h12_price_action_core",
    "h12_clock_shift_back_plus_price_action_regime": "h12_price_action_regime",
}


def _stage62_drop_forbidden(df: pd.DataFrame) -> pd.DataFrame:
    forbidden_prefixes = ("stage6_", "trade_", "fav_", "adv_", "ret_", "path_")
    explicit = set(stage62_feature_denylist())
    cols = [
        c for c in df.columns
        if c in explicit or any(c.startswith(prefix) for prefix in forbidden_prefixes)
    ]
    return df.drop(columns=cols, errors="ignore")


def stage62_build_features(
    df: pd.DataFrame,
    profile: str,
    ohlc: pd.DataFrame | None = None,
) -> np.ndarray:
    clean = _stage62_drop_forbidden(df)
    if profile == "h12_clock_shift_back":
        return build_stage5_4_features(clean, "clock_shift_back")
    if profile in {"h12_price_action_core", "h12_price_action_regime"}:
        return stage62_build_price_action_features(clean, profile, ohlc=ohlc)
    if profile in COMBINED_TO_PRICE_ACTION:
        baseline = build_stage5_4_features(clean, "clock_shift_back")
        price_action = stage62_build_price_action_features(clean, COMBINED_TO_PRICE_ACTION[profile], ohlc=ohlc)
        return np.hstack([baseline, price_action]).astype(np.float32)
    raise ValueError(f"unknown Stage 6.2 profile: {profile}")
```

- [ ] **Step 6: Run feature tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage6_2_price_action.py -q
```

Expected: all current Stage 6.2 tests pass.

- [ ] **Step 7: Checkpoint / review**

```bash
git diff -- ML/baseline/benchmark_stage6_2_price_action.py tests/test_stage6_2_price_action.py
```

---

### Task 3: Preflight, Feature Audit, And Leakage Guards

**Files:**
- Modify: `ML/baseline/benchmark_stage6_2_price_action.py`
- Modify: `tests/test_stage6_2_price_action.py`

**Interfaces:**
- Produces:
  - `stage62_feature_names(profile: str) -> list[str]`
  - `stage62_ohlc_contract_preflight(df: pd.DataFrame, ohlc: pd.DataFrame) -> dict`
  - `stage62_feature_distribution_audit(split, feature_split, profile) -> dict`
  - `stage62_feature_preflight(split, ohlc=None) -> dict`
  - `stage62_definitive_mask(df: pd.DataFrame) -> np.ndarray`

- [ ] **Step 1: Write failing tests**

Add:

```python
def test_stage62_feature_names_for_combined_profiles_are_prefixed(monkeypatch):
    monkeypatch.setattr(s62, "stage5_4_feature_names", lambda profile: ["shift", "back"])

    names = s62.stage62_feature_names("h12_clock_shift_back_plus_price_action_core")

    assert names[:2] == ["baseline.shift", "baseline.back"]
    assert "price_action.ret_close_w12_atr" in names


def test_stage62_feature_name_count_matches_matrix_for_all_profiles(monkeypatch):
    ohlc = _tiny_ohlc()
    df = pd.DataFrame({
        "time": [ohlc.loc[24, "time"].strftime("%Y.%m.%d %H:%M")],
        "ATR": [2.0],
    })
    monkeypatch.setattr(s62, "build_stage5_4_features", lambda clean, profile: np.ones((len(clean), 2), dtype=np.float32))
    monkeypatch.setattr(s62, "stage5_4_feature_names", lambda profile: ["shift", "back"])

    for profile in s62.stage62_profile_keys():
        X = s62.stage62_build_features(df, profile, ohlc=ohlc)
        assert X.shape[1] == len(s62.stage62_feature_names(profile)), profile


def test_stage62_feature_preflight_flags_nonfinite_values(monkeypatch):
    split = {"train_core": pd.DataFrame({"time": ["2021.01.02 00:00"], "ATR": [2.0]})}
    monkeypatch.setattr(
        s62,
        "stage62_build_features",
        lambda df, profile, ohlc=None: np.asarray([[1.0, np.nan]], dtype=np.float32),
    )

    audit = s62.stage62_feature_preflight(split, ohlc=_tiny_ohlc())

    assert audit["h12_price_action_core"]["feature_distribution"]["train_core"]["status"] == "ERROR"


def test_stage62_ohlc_contract_preflight_counts_missing_and_incomplete_windows():
    ohlc = _tiny_ohlc()
    df = pd.DataFrame({
        "time": [
            ohlc.loc[10, "time"].strftime("%Y.%m.%d %H:%M"),
            "2021.01.10 00:00",
        ],
        "ATR": [2.0, 2.0],
    })

    audit = s62.stage62_ohlc_contract_preflight(df, ohlc)

    assert audit["rows"] == 2
    assert audit["missing_exact_ohlc_rows"] == 1
    assert audit["incomplete_window_24_rows"] == 1
    assert audit["status"] == "WARNING"


def test_stage62_ohlc_preflight_requires_unique_monotonic_closed_bars():
    ohlc = _tiny_ohlc()
    bad = pd.concat([ohlc, ohlc.iloc[[5]]], ignore_index=True)

    audit = s62.stage62_ohlc_contract_preflight(
        pd.DataFrame({"time": [ohlc.loc[24, "time"].strftime("%Y.%m.%d %H:%M")]}),
        bad,
    )

    assert audit["status"] == "ERROR"
    assert "OHLC_TIME_NOT_UNIQUE" in audit["warnings"]


def test_stage62_definitive_mask_excludes_timeout_and_invalid():
    df = pd.DataFrame({
        "stage6_close_reason": ["TP", "SL", "AMBIGUOUS_SL_FIRST", "TIMEOUT", "INVALID"],
        "stage6_definitive_tp_vs_sl_flag": [1.0, 0.0, 0.0, np.nan, np.nan],
    })

    mask = s62.stage62_definitive_mask(df)

    assert mask.tolist() == [True, True, True, False, False]
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage6_2_price_action.py -q
```

Expected: fail on missing audit and mask functions.

- [ ] **Step 3: Implement feature names and mask**

Add:

```python
def stage62_feature_names(profile: str) -> list[str]:
    if profile == "h12_clock_shift_back":
        return stage5_4_feature_names("clock_shift_back")
    if profile in {"h12_price_action_core", "h12_price_action_regime"}:
        return stage62_price_action_feature_names(profile)
    if profile in COMBINED_TO_PRICE_ACTION:
        baseline_names = [f"baseline.{name}" for name in stage5_4_feature_names("clock_shift_back")]
        price_names = [
            f"price_action.{name}"
            for name in stage62_price_action_feature_names(COMBINED_TO_PRICE_ACTION[profile])
        ]
        return baseline_names + price_names
    raise ValueError(f"unknown Stage 6.2 profile: {profile}")


def stage62_definitive_mask(df: pd.DataFrame) -> np.ndarray:
    y = df["stage6_definitive_tp_vs_sl_flag"].to_numpy(dtype=np.float64)
    reason = df["stage6_close_reason"].astype(str)
    return np.isfinite(y) & reason.isin(["TP", "SL", "AMBIGUOUS_SL_FIRST"]).to_numpy()
```

- [ ] **Step 4: Implement OHLC contract and distribution audit**

Add:

```python
def stage62_ohlc_contract_preflight(df: pd.DataFrame, ohlc: pd.DataFrame) -> dict:
    warnings = []
    times = ohlc["time"]
    if not times.is_monotonic_increasing:
        warnings.append("OHLC_TIME_NOT_MONOTONIC")
    if times.duplicated().any():
        warnings.append("OHLC_TIME_NOT_UNIQUE")

    missing = 0
    incomplete_24 = 0
    for value in df["time"]:
        row_time = _stage62_parse_time(value)
        if row_time is None:
            missing += 1
            continue
        pos = _stage62_ohlc_position(row_time, ohlc)
        if pos is None:
            missing += 1
            continue
        if pos < 24:
            incomplete_24 += 1

    status = "PASS"
    if missing > 0 or incomplete_24 > 0:
        status = "WARNING"
    if "OHLC_TIME_NOT_MONOTONIC" in warnings or "OHLC_TIME_NOT_UNIQUE" in warnings:
        status = "ERROR"
    return {
        "status": status,
        "rows": int(len(df)),
        "missing_exact_ohlc_rows": int(missing),
        "incomplete_window_24_rows": int(incomplete_24),
        "warnings": warnings,
    }


def _stage62_quantiles(values) -> dict:
    arr = np.asarray(values, dtype=np.float64)
    arr = arr[np.isfinite(arr)]
    if len(arr) == 0:
        return {"n": 0, "min": None, "p50": None, "p95": None, "p99": None, "max": None}
    return {
        "n": int(len(arr)),
        "min": float(np.min(arr)),
        "p50": float(np.percentile(arr, 50)),
        "p95": float(np.percentile(arr, 95)),
        "p99": float(np.percentile(arr, 99)),
        "max": float(np.max(arr)),
    }


def stage62_feature_distribution_audit(
    split: dict[str, pd.DataFrame],
    feature_split: dict[str, np.ndarray],
    profile: str,
) -> dict:
    out = {}
    names = stage62_feature_names(profile)
    for split_name, X in feature_split.items():
        finite = np.isfinite(X)
        status = "PASS" if finite.all() else "ERROR"
        zero_rate = float(np.mean(X == 0.0)) if X.size else 0.0
        tail_abs = np.abs(X[np.isfinite(X)])
        warnings = []
        if tail_abs.size and float(np.percentile(tail_abs, 99)) > 20.0:
            warnings.append("TAIL_ABS_P99_GT_20")
        if X.shape[1] != len(names):
            status = "ERROR"
            warnings.append("FEATURE_NAME_COUNT_MISMATCH")
        out[split_name] = {
            "status": status,
            "rows": int(X.shape[0]),
            "cols": int(X.shape[1]) if X.ndim == 2 else 0,
            "finite_rate": float(np.mean(finite)) if finite.size else 1.0,
            "zero_rate": zero_rate,
            "all_zero_rows": int(np.sum(np.all(X == 0.0, axis=1))) if X.ndim == 2 and X.size else 0,
            "abs_value": _stage62_quantiles(tail_abs),
            "warnings": warnings,
        }
    return out
```

- [ ] **Step 5: Implement preflight across profiles**

Add:

```python
def stage62_feature_preflight(
    split: dict[str, pd.DataFrame],
    ohlc: pd.DataFrame | None = None,
) -> dict:
    frame = stage62_load_ohlc_frame() if ohlc is None else ohlc
    out = {}
    for profile in stage62_profile_keys():
        feature_split = {
            name: stage62_build_features(df, profile, ohlc=frame)
            for name, df in split.items()
            if isinstance(df, pd.DataFrame)
        }
        out[profile] = {
            "ohlc_contract": {
                name: stage62_ohlc_contract_preflight(df, frame)
                for name, df in split.items()
                if isinstance(df, pd.DataFrame)
            },
            "feature_distribution": stage62_feature_distribution_audit(split, feature_split, profile),
        }
    return out
```

- [ ] **Step 6: Run audit tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage6_2_price_action.py -q
```

Expected: all current Stage 6.2 tests pass.

- [ ] **Step 7: Checkpoint / review**

```bash
git diff -- ML/baseline/benchmark_stage6_2_price_action.py tests/test_stage6_2_price_action.py
```

---

### Task 4: Model Evaluation, Summary, And Gates

**Files:**
- Modify: `ML/baseline/benchmark_stage6_2_price_action.py`
- Modify: `tests/test_stage6_2_price_action.py`

**Interfaces:**
- Produces:
  - `evaluate_stage62_profile_seed(split, feature_split, profile, seed) -> dict`
  - `stage62_permutation_feature_importance(model, X_val, y_val, profile, seed, top_n=10) -> list[dict]`
  - `stage62_summary(report: dict, split: dict[str, pd.DataFrame]) -> dict`
  - `stage62_baseline_delta_summary(report: dict) -> dict`
  - `stage62_gate_results(report: dict) -> dict`

- [ ] **Step 1: Write failing model/gate tests**

Add:

```python
def test_stage62_xgboost_uses_n_jobs_24():
    src = inspect.getsource(s62.evaluate_stage62_profile_seed)
    assert "n_jobs=STAGE6_2_CONFIG.xgb_n_jobs" in src


def test_stage62_gate_fails_when_primary_model_is_weak():
    report = {
        "summary": {
            "h12_price_action_core": {
                "val_stop": {"auc_median": 0.55, "pr_auc_lift_median": 0.02},
                "threshold_selection": {"status": "NO_THRESHOLD", "selected": None},
                "permutation_baseline": {"empirical_p_value": 0.5},
            }
        },
        "baseline_plus_price_action_delta": {"any_delta_gate_pass": False},
    }

    gate = s62.stage62_gate_results(report)

    assert gate["overall_status"] == "MODEL_GATE_FAILED"
    assert gate["artifact_status"] == "DIAGNOSTIC_ONLY"


def test_stage62_gate_marks_standalone_without_additive_value():
    report = {
        "summary": {
            "h12_price_action_core": {
                "val_stop": {"auc_median": 0.61, "pr_auc_lift_median": 0.06},
                "threshold_selection": {
                    "status": "SELECTED",
                    "selected": {"pf": 1.2, "trades_per_year": 30, "pf_spread_020": 1.1},
                },
                "permutation_baseline": {"empirical_p_value": 0.05},
            }
        },
        "baseline_plus_price_action_delta": {"any_delta_gate_pass": False},
    }

    gate = s62.stage62_gate_results(report)

    assert gate["overall_status"] == "DIAGNOSTIC_SIGNAL_FOUND"
    assert gate["interpretation"] == "STANDALONE_ONLY_NO_ADDITIVE_VALUE_CONFIRMED"


def test_stage62_delta_gate_requires_auc_and_pf_improvement():
    report = {
        "summary": {
            "h12_clock_shift_back": {
                "val_stop": {"auc_median": 0.617, "pr_auc_lift_median": 0.13},
                "threshold_selection": {"status": "SELECTED", "selected": {"pf": 1.25}},
            },
            "h12_clock_shift_back_plus_price_action_core": {
                "val_stop": {"auc_median": 0.622, "pr_auc_lift_median": 0.14},
                "threshold_selection": {"status": "SELECTED", "selected": {"pf": 1.20}},
                "permutation_baseline": {"empirical_p_value": 0.05},
            },
        }
    }

    delta = s62.stage62_baseline_delta_summary(report)

    row = delta["profiles"]["h12_clock_shift_back_plus_price_action_core"]
    assert row["passes_delta_gate"] is False
    assert row["auc_delta_vs_baseline"] < 0.02
    assert row["pf_delta_vs_baseline"] < 0.0
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage6_2_price_action.py -q
```

Expected: fail on missing evaluation/gate functions.

- [ ] **Step 3: Implement evaluation**

Add:

```python
def stage62_permutation_feature_importance(
    model,
    X_val: np.ndarray,
    y_val: np.ndarray,
    profile: str,
    seed: int,
    top_n: int = 10,
) -> list[dict]:
    if len(np.unique(y_val)) < 2:
        return []
    rng = np.random.default_rng(seed)
    baseline_score = float(stage6_binary_metrics(y_val, model.predict_proba(X_val)[:, 1])["auc"])
    names = stage62_feature_names(profile)
    rows = []
    for idx, name in enumerate(names):
        X_perm = X_val.copy()
        X_perm[:, idx] = rng.permutation(X_perm[:, idx])
        perm_score = float(stage6_binary_metrics(y_val, model.predict_proba(X_perm)[:, 1])["auc"])
        rows.append({
            "feature": name,
            "auc_drop": float(baseline_score - perm_score),
            "baseline_auc": baseline_score,
            "permuted_auc": perm_score,
        })
    rows.sort(key=lambda item: item["auc_drop"], reverse=True)
    return rows[:top_n]
```

```python
def evaluate_stage62_profile_seed(
    split: dict[str, pd.DataFrame],
    feature_split: dict[str, np.ndarray],
    profile: str,
    seed: int,
) -> dict:
    train = split["train_core"]
    val = split["val_stop"]
    train_mask = stage62_definitive_mask(train)
    val_mask = stage62_definitive_mask(val)
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
        n_jobs=STAGE6_2_CONFIG.xgb_n_jobs,
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
        "feature_importance": [] if profile == "h12_clock_shift_back" else stage62_permutation_feature_importance(
            clf, X_val[val_mask], y_val[val_mask], profile, seed=seed
        ),
    }
    for split_name in ("diagnostic_holdout", "low_n_disclosure"):
        df = split[split_name]
        X = feature_split[split_name]
        mask = stage62_definitive_mask(df)
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

- [ ] **Step 4: Implement summary and delta gates**

Add:

```python
def _stage62_median(values) -> float | None:
    vals = [v for v in values if v is not None and np.isfinite(v)]
    return float(np.median(vals)) if vals else None


def stage62_baseline_delta_summary(report: dict) -> dict:
    summary = report.get("summary", {})
    baseline = summary.get("h12_clock_shift_back", {})
    baseline_auc = baseline.get("val_stop", {}).get("auc_median")
    baseline_pr = baseline.get("val_stop", {}).get("pr_auc_lift_median")
    baseline_selected = (baseline.get("threshold_selection", {}) or {}).get("selected") or {}
    baseline_pf = baseline.get("threshold_selection", {}).get("val_pf_median", baseline_selected.get("pf"))
    rows = {}
    any_pass = False
    for profile in (
        "h12_clock_shift_back_plus_price_action_core",
        "h12_clock_shift_back_plus_price_action_regime",
    ):
        item = summary.get(profile, {})
        auc = item.get("val_stop", {}).get("auc_median")
        pr = item.get("val_stop", {}).get("pr_auc_lift_median")
        threshold = item.get("threshold_selection", {}) or {}
        selected = threshold.get("selected") or {}
        pf = threshold.get("val_pf_median", selected.get("pf"))
        perm = item.get("permutation_baseline") or {}
        auc_delta = None if auc is None or baseline_auc is None else float(auc - baseline_auc)
        pr_delta = None if pr is None or baseline_pr is None else float(pr - baseline_pr)
        pf_delta = None if pf is None or baseline_pf is None else float(pf - baseline_pf)
        passes = (
            auc_delta is not None and auc_delta >= 0.02
            and pr_delta is not None and pr_delta >= 0.0
            and threshold.get("status") == "SELECTED"
            and pf_delta is not None and pf_delta >= 0.0
            and perm.get("empirical_p_value") is not None
            and perm["empirical_p_value"] <= 0.10
        )
        rows[profile] = {
            "auc_delta_vs_baseline": auc_delta,
            "pr_auc_lift_delta_vs_baseline": pr_delta,
            "pf_delta_vs_baseline": pf_delta,
            "permutation_p_value": perm.get("empirical_p_value"),
            "passes_delta_gate": bool(passes),
        }
        any_pass = any_pass or bool(passes)
    return {
        "baseline_profile": "h12_clock_shift_back",
        "profiles": rows,
        "any_delta_gate_pass": bool(any_pass),
        "delta_gate": {
            "auc_delta_ge_0_02": 0.02,
            "pr_auc_lift_delta_ge_0": 0.0,
            "pf_delta_ge_0": 0.0,
            "permutation_p_value_le_0_10": 0.10,
        },
    }
```

```python
def stage62_gate_results(report: dict) -> dict:
    summary = report.get("summary", {})
    primary = summary.get(STAGE6_2_CONFIG.primary_profile, {})
    val = primary.get("val_stop", {})
    threshold = primary.get("threshold_selection", {})
    selected = threshold.get("selected") or {}
    perm = primary.get("permutation_baseline") or {}
    checks = {
        "primary_auc_ge_0_60": bool(val.get("auc_median") is not None and val["auc_median"] >= 0.60),
        "primary_pr_auc_lift_ge_0_05": bool(
            val.get("pr_auc_lift_median") is not None and val["pr_auc_lift_median"] >= 0.05
        ),
        "primary_threshold_selected": bool(threshold.get("status") == "SELECTED" and selected),
        "primary_permutation_p_value_le_0_10": bool(
            perm.get("empirical_p_value") is not None and perm["empirical_p_value"] <= 0.10
        ),
        "primary_pf_ge_1_15": bool(selected.get("pf") is not None and selected["pf"] >= 1.15),
        "primary_trades_per_year_ge_25": bool(selected.get("trades_per_year", 0) >= 25),
        "primary_spread_020_pf_ge_1_05": bool(
            selected.get("pf_spread_020") is not None and selected["pf_spread_020"] >= 1.05
        ),
        "any_delta_gate_pass": bool(
            (report.get("baseline_plus_price_action_delta") or {}).get("any_delta_gate_pass", False)
        ),
    }
    primary_model_pass = checks["primary_auc_ge_0_60"] and checks["primary_pr_auc_lift_ge_0_05"]
    primary_trading_pass = (
        primary_model_pass
        and checks["primary_threshold_selected"]
        and checks["primary_permutation_p_value_le_0_10"]
        and checks["primary_pf_ge_1_15"]
        and checks["primary_trades_per_year_ge_25"]
        and checks["primary_spread_020_pf_ge_1_05"]
    )
    if checks["any_delta_gate_pass"]:
        return {
            "overall_status": "DIAGNOSTIC_SIGNAL_FOUND",
            "artifact_status": "DIAGNOSTIC_ONLY",
            "interpretation": "ADDITIVE_VALUE_OVER_BASELINE_FOUND",
            "checks": checks,
        }
    if primary_trading_pass:
        return {
            "overall_status": "DIAGNOSTIC_SIGNAL_FOUND",
            "artifact_status": "DIAGNOSTIC_ONLY",
            "interpretation": "STANDALONE_ONLY_NO_ADDITIVE_VALUE_CONFIRMED",
            "checks": checks,
        }
    if not primary_model_pass and not checks["any_delta_gate_pass"]:
        return {"overall_status": "MODEL_GATE_FAILED", "artifact_status": "DIAGNOSTIC_ONLY", "checks": checks}
    return {"overall_status": "TRADING_GATE_FAILED", "artifact_status": "DIAGNOSTIC_ONLY", "checks": checks}
```

- [ ] **Step 5: Run tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage6_2_price_action.py -q
```

Expected: all current Stage 6.2 tests pass.

- [ ] **Step 6: Checkpoint / review**

```bash
git diff -- ML/baseline/benchmark_stage6_2_price_action.py tests/test_stage6_2_price_action.py
```

---

### Task 5: Runner, Resume, CLI, And JSON Artifact

**Files:**
- Modify: `ML/baseline/benchmark_stage6_2_price_action.py`
- Modify: `tests/test_stage6_2_price_action.py`

**Interfaces:**
- Produces:
  - `run_stage6_2_price_action(output_path=STAGE6_2_JSON_REPORT_PATH, resume=True) -> dict`
  - `main(argv: list[str] | None = None) -> int`

- [ ] **Step 1: Write failing runtime tests**

Add:

```python
def _fake_split():
    base = pd.DataFrame({
        "time": ["2021.01.02 00:00", "2021.01.02 01:00", "2021.01.02 02:00", "2021.01.02 03:00"],
        "ATR": [2.0, 2.0, 2.0, 2.0],
        "stage6_close_reason": ["TP", "SL", "TP", "SL"],
        "stage6_definitive_tp_vs_sl_flag": [1.0, 0.0, 1.0, 0.0],
        "stage6_pnl_r": [4.0, -1.0, 4.0, -1.0],
    })
    return {
        "train_core": base.copy(),
        "val_stop": base.copy(),
        "diagnostic_holdout": base.copy(),
        "low_n_disclosure": base.copy(),
    }


def test_stage62_runner_writes_initial_checkpoint_and_elapsed(monkeypatch, tmp_path):
    out = tmp_path / "stage62.json"

    monkeypatch.setattr(s62, "stage62_input_file_manifest", lambda: {"dummy": {"sha256": "a" * 64}})
    monkeypatch.setattr(s62, "stage6_load_labeled_splits", lambda config: _fake_split())
    monkeypatch.setattr(s62, "stage62_load_ohlc_frame", lambda: _tiny_ohlc())
    monkeypatch.setattr(s62, "stage6_outcome_preflight", lambda split: {"ok": True})
    monkeypatch.setattr(s62, "stage62_feature_preflight", lambda split, ohlc=None: {"ok": True})
    monkeypatch.setattr(s62, "stage6_all_trade_baseline", lambda df: {"pf": 1.0})
    monkeypatch.setattr(s62, "stage62_build_features", lambda df, profile, ohlc=None: np.ones((len(df), 2), dtype=np.float32))
    monkeypatch.setattr(
        s62,
        "evaluate_stage62_profile_seed",
        lambda split, feature_split, profile, seed: {
            "profile": profile,
            "seed": seed,
            "val_stop": {"auc": 0.51, "pr_auc_lift": 0.01},
            "threshold_selection": {"status": "NO_THRESHOLD", "selected": None},
            "predictions": {"val_stop": {"y_score_all": [0.1, 0.2, 0.3, 0.4]}},
            "feature_importance": [],
        },
    )

    report = s62.run_stage6_2_price_action(output_path=out, resume=False)

    assert out.exists()
    assert report["done_runs"] == report["total_runs"]
    assert report["config"]["xgb_n_jobs"] == 24
    assert "started_at" in report
    assert "finished_at" in report
    assert "elapsed_sec" in report
    assert all("elapsed_sec" in run for run in report["raw_runs"])


def test_stage62_cli_has_resume_flags():
    src = inspect.getsource(s62.main)
    assert "--stage6-2-price-action" in src
    assert "--resume" in src
    assert "--no-resume" in src
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage6_2_price_action.py -q
```

Expected: fail on missing runner/CLI.

- [ ] **Step 3: Implement runner**

Add:

```python
def run_stage6_2_price_action(
    output_path: Path = STAGE6_2_JSON_REPORT_PATH,
    resume: bool = True,
) -> dict:
    import datetime
    import time

    started_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    wall0 = time.time()
    if resume and output_path.exists():
        report = json.loads(output_path.read_text())
        done_set = {(r["profile"], int(r["seed"])) for r in report.get("raw_runs", [])}
        print(f"[stage6.2] RESUME existing report: {output_path}", flush=True)
        print(f"[stage6.2] Already done: {len(done_set)} runs ({report.get('done_runs', 0)}/{report.get('total_runs', '?')})", flush=True)
        report["resumed_at"] = started_at
    else:
        feature_contract = {
            profile: {
                "feature_names": stage62_feature_names(profile),
                "feature_names_sha256": hashlib.sha256(
                    "\n".join(stage62_feature_names(profile)).encode("utf-8")
                ).hexdigest(),
                "feature_count": len(stage62_feature_names(profile)),
            }
            for profile in STAGE6_2_CONFIG.profile_keys
        }
        report = {
            "stage": "6.2",
            "status": "RUNNING",
            "started_at": started_at,
            "config": {
                "horizon_bars": STAGE6_2_CONFIG.horizon_bars,
                "stop_offset_atr": STAGE6_2_CONFIG.stop_offset_atr,
                "take_profit_atr": STAGE6_2_CONFIG.take_profit_atr,
                "entry_lag_bars": STAGE6_2_CONFIG.entry_lag_bars,
                "profiles": list(STAGE6_2_CONFIG.profile_keys),
                "primary_profile": STAGE6_2_CONFIG.primary_profile,
                "seeds": list(STAGE6_2_CONFIG.seeds),
                "windows": list(STAGE6_2_CONFIG.windows),
                "target": "stage6_definitive_tp_vs_sl_flag",
                "ohlc_file": str(OHLC_FILE),
                "xgb_n_jobs": STAGE6_2_CONFIG.xgb_n_jobs,
            },
            "feature_contract": feature_contract,
            "input_manifest": stage62_input_file_manifest(),
            "raw_runs": [],
            "done_runs": 0,
            "total_runs": len(STAGE6_2_CONFIG.profile_keys) * len(STAGE6_2_CONFIG.seeds),
        }
        done_set = set()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2, default=str))
        print(f"[stage6.2] Started fresh report: {output_path}", flush=True)

    cfg = replace(
        STAGE6_0_CONFIG,
        horizon_bars=STAGE6_2_CONFIG.horizon_bars,
        stop_offset_atr=STAGE6_2_CONFIG.stop_offset_atr,
        take_profit_atr=STAGE6_2_CONFIG.take_profit_atr,
        entry_lag_bars=STAGE6_2_CONFIG.entry_lag_bars,
    )
    ohlc = stage62_load_ohlc_frame()
    split = stage6_load_labeled_splits(config=cfg)

    if "preflight" not in report:
        print("[stage6.2] Running preflight ...", flush=True)
        report["preflight"] = stage6_outcome_preflight(split)
        report["feature_preflight"] = stage62_feature_preflight(split, ohlc=ohlc)
        report["oracle_preflight"] = {
            name: stage6_all_trade_baseline(df)
            for name, df in split.items()
            if isinstance(df, pd.DataFrame)
        }
        output_path.write_text(json.dumps(report, indent=2, default=str))
        print("[stage6.2] Preflight done, saved checkpoint.", flush=True)

    total_runs = int(report["total_runs"])
    done_runs = int(report.get("done_runs", 0))
    for profile in STAGE6_2_CONFIG.profile_keys:
        print(f"[stage6.2] Building features for profile={profile} ...", flush=True)
        t0_profile = time.time()
        feature_split = {
            name: stage62_build_features(df, profile, ohlc=ohlc)
            for name, df in split.items()
            if isinstance(df, pd.DataFrame)
        }
        print(f"[stage6.2] Features built in {time.time() - t0_profile:.1f}s", flush=True)
        for seed in STAGE6_2_CONFIG.seeds:
            key = (profile, int(seed))
            if key in done_set:
                print(f"[stage6.2] SKIP profile={profile} seed={seed} (already done)", flush=True)
                continue
            t0_run = time.time()
            print(f"[stage6.2] Training profile={profile} seed={seed} ({done_runs + 1}/{total_runs}) ...", flush=True)
            result = evaluate_stage62_profile_seed(split, feature_split, profile, seed)
            result["elapsed_sec"] = float(time.time() - t0_run)
            report["raw_runs"].append(result)
            done_runs += 1
            report["done_runs"] = done_runs
            elapsed = time.time() - wall0
            remaining = (total_runs - done_runs) * (elapsed / max(done_runs, 1))
            print(f"[stage6.2] done {done_runs}/{total_runs} elapsed={elapsed:.0f}s ETA={remaining:.0f}s", flush=True)
            output_path.write_text(json.dumps(report, indent=2, default=str))

    report["summary"] = stage62_summary(report, split)
    report["baseline_plus_price_action_delta"] = stage62_baseline_delta_summary(report)
    report["gate"] = stage62_gate_results(report)
    report["status"] = report["gate"]["overall_status"]
    report["finished_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    report["elapsed_sec"] = float(time.time() - wall0)
    output_path.write_text(json.dumps(report, indent=2, default=str))
    return report
```

- [ ] **Step 4: Implement summary helper and CLI**

Add:

```python
def stage62_summary(report: dict, split: dict[str, pd.DataFrame]) -> dict:
    summary = {}
    for profile in STAGE6_2_CONFIG.profile_keys:
        runs = [r for r in report["raw_runs"] if r["profile"] == profile]
        aucs = [r["val_stop"].get("auc") for r in runs]
        lifts = [r["val_stop"].get("pr_auc_lift") for r in runs]
        selected = [
            r["threshold_selection"]["selected"]
            for r in runs
            if r["threshold_selection"].get("status") == "SELECTED" and r["threshold_selection"].get("selected")
        ]
        best_run = max(runs, key=lambda r: r["val_stop"].get("auc") or 0.0)
        val_scores = best_run.get("predictions", {}).get("val_stop", {}).get("y_score_all", [])
        perm = None
        if val_scores:
            perm = stage6_permutation_threshold_baseline(split["val_stop"].copy(), np.asarray(val_scores), seed=42)
        summary[profile] = {
            "val_stop": {
                "auc_median": _stage62_median(aucs),
                "pr_auc_lift_median": _stage62_median(lifts),
            },
            "threshold_selection": {
                "status": "SELECTED" if selected else "NO_THRESHOLD",
                "selected": selected[len(selected) // 2] if selected else None,
                "n_selected": len(selected),
                "val_pf_median": _stage62_median([s.get("pf") for s in selected]),
            },
            "diagnostic_holdout": {
                "auc_median": _stage62_median([r.get("diagnostic_holdout", {}).get("auc") for r in runs]),
                "pr_auc_lift_median": _stage62_median([r.get("diagnostic_holdout", {}).get("pr_auc_lift") for r in runs]),
            },
            "permutation_baseline": perm,
            "top_feature_importance": best_run.get("feature_importance", []),
        }
    return summary


def main(argv: list[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage6-2-price-action", action="store_true")
    parser.add_argument("--resume", action="store_true", default=True, dest="resume")
    parser.add_argument("--no-resume", action="store_false", dest="resume")
    args = parser.parse_args(argv)
    if args.stage6_2_price_action:
        report = run_stage6_2_price_action(resume=args.resume)
        print({"status": report.get("status"), "json": str(STAGE6_2_JSON_REPORT_PATH)})
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Run runtime tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage6_2_price_action.py -q
```

Expected: all Stage 6.2 tests pass.

- [ ] **Step 6: Checkpoint / review**

```bash
git diff -- ML/baseline/benchmark_stage6_2_price_action.py tests/test_stage6_2_price_action.py
```

---

### Task 6: Full Run, Report, And Project Sync

**Files:**
- Modify: `docs/reports/2026-06-30-stage6_2-h12-price-action-feature-family.md`
- Modify: `CHANGELOG.md`
- Modify: `CONTEXT_HANDOFF.md`
- Modify: `wiki/research/fractal-stop-research.md`
- Modify: `wiki/index.md`
- Modify: `wiki/log.md`
- Modify: `wiki/REPO_integrity.md`
- Generated: `ML/reports/stage6_2_h12_price_action_feature_family.json`

**Interfaces:**
- Consumes: completed Stage 6.2 runner and tests.
- Produces: canonical report and updated handoff/wiki.

- [ ] **Step 1: Run focused tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage6_2_price_action.py -q
```

Expected: all Stage 6.2 tests pass.

- [ ] **Step 2: Check whether full suite is safe before long training**

Run:

```bash
rg -n "benchmark_stage6_2|stage6-2-price-action|--no-resume|--stage6" tests/
```

Expected: no tests start long benchmark execution. If this check shows only unit/smoke coverage, optionally run:

```bash
./.venv/bin/python -m pytest tests/ -q
```

Expected: full suite passes. If the scan shows a heavy scenario, skip the full suite before training and run only the focused Stage 6.2 tests here.

- [ ] **Step 3: Run Stage 6.2 benchmark**

Run:

```bash
./.venv/bin/python ML/baseline/benchmark_stage6_2_price_action.py --stage6-2-price-action --no-resume
```

Expected:

- JSON written to `ML/reports/stage6_2_h12_price_action_feature_family.json`;
- `done_runs == total_runs == 15`;
- `config.xgb_n_jobs == 24`;
- `started_at`, `finished_at`, top-level `elapsed_sec`, and per-run `elapsed_sec` present;
- `summary` contains all 5 profiles;
- `baseline_plus_price_action_delta` present;
- `gate.overall_status` present.

- [ ] **Step 4: If interrupted, resume**

Run:

```bash
./.venv/bin/python ML/baseline/benchmark_stage6_2_price_action.py --stage6-2-price-action --resume
```

Expected: completed profile/seed pairs are skipped; only missing runs execute.

- [ ] **Step 5: Write canonical report**

Create `docs/reports/2026-06-30-stage6_2-h12-price-action-feature-family.md` with:

- objective and fixed hypothesis;
- input file SHA256 table from JSON;
- feature family definition and explicit no-future window rule;
- explicit row-time contract result: `row.time` matched closed OHLC bars, features did not read `Open[row+1]`;
- OHLC coverage table: missing exact OHLC rows, incomplete 24-bar windows, all-zero feature rows, monotonic/unique time status;
- split policy: `val_stop` selection only, holdout disclosure-only;
- preflight and feature audit summary;
- all-profile validation table;
- standalone vs same-run baseline vs combined comparison table;
- top-5 validation permutation feature importance per non-baseline profile;
- baseline-plus-price-action delta table;
- diagnostic holdout AUC/PR lift disclosure;
- gate table;
- source/tick volume caveat: `volume` in `DATA/XAUUSD_H1_OHLC.csv` is treated as source volume unless producer documentation proves real exchange volume;
- conclusion written narrowly: this stage supports or rejects the tested price-action feature family, not every possible OHLC-derived representation;
- comparison caveat: use only the `h12_clock_shift_back` baseline from the same Stage 6.2 JSON for deltas and conclusions.

- [ ] **Step 6: Sync changelog, handoff, and wiki**

Update:

- `CHANGELOG.md` with one dated Stage 6.2 entry near the top;
- `CONTEXT_HANDOFF.md` with current verdict, artifacts, and next step;
- wiki using the project wiki workflow for new report ingestion.

- [ ] **Step 7: Run verification**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage6_2_price_action.py -q
rg -n "benchmark_stage6_2|stage6-2-price-action|--no-resume|--stage6" tests/
./.venv/bin/python -m pytest tests/ -q
git diff --check
```

Expected: focused tests pass; full tests pass if the scan confirms no long benchmark execution; no whitespace errors.

- [ ] **Step 8: Stage-reporting closure**

Use the project `stage-reporting` procedure to close the stage. The final commit, if requested by that procedure, belongs to stage closure and must not include unrelated files.

---

## Plan Self-Review

- Spec coverage: the plan implements the roadmap item “new feature family for H12”, compares standalone and additive value against `h12_clock_shift_back`, keeps H12/ATR/TP/SL fixed, and preserves the Stage 6 runtime contract.
- Leakage control: features use only OHLC bars with `time <= row.time`; future-derived labeled columns are blocked; holdout is disclosure-only.
- Scope control: no horizon search, no barrier search, no additional fractal geometry variants, no model family search.
- Reproducibility: JSON contains input hashes, run timing, seed/profile grid, raw runs, summaries, gate, and feature importance.
- Execution risk: feature building joins OHLC history for every split. If it is slow, optimize by pre-indexing OHLC times, but do not change feature definitions after seeing metrics.
