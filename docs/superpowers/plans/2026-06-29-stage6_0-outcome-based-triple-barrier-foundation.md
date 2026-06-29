# Stage 6.0 Outcome-Based Triple-Barrier Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a narrow, testable outcome-based baseline that asks whether a trade-like TP/SL/timeout target has more useful signal than the exhausted `H6_off05` Fractal Stop branch.

**Architecture:** Add an isolated Stage 6.0 runner instead of extending the already large Stage 5 runner. The runner builds one fixed execution-aware outcome target, runs label/preflight/oracle checks before training, trains a simple XGBoost baseline on live-safe Stage 5-style features, selects thresholds only on `val_stop`, and writes one JSON artifact plus one report.

**Tech Stack:** Python 3.10+, pandas, numpy, sklearn metrics, xgboost, pytest, existing `./.venv/bin/python`, existing DATA split files, existing OHLC source `MT/MQL4/Files/Nero.csv`.

## Global Constraints

- Work on the current `Stage_6.0` branch; do not use git worktree.
- Use `./.venv/bin/python` for all Python commands.
- New Python code must be covered by tests before implementation.
- After Python changes, run `./.venv/bin/python -m pytest tests/ -q`.
- Do not regenerate `DATA/*.csv` unless a task explicitly says so.
- Do not open a new broad parameter search. Stage 6.0 tests one fixed baseline protocol.
- Do not use `2023-2025` for winner selection. It is diagnostic disclosure only.
- Do not use `2026` for winner selection. It is low-N disclosure only.
- Stage 6.0 result cannot exceed `DIAGNOSTIC_ONLY` unless entry timing, spread convention, and simulator parity are proven.
- Timeout is a separate outcome, not a loss by default.
- New target/outcome columns must use `stage6_` prefix and must not enter feature matrices.
- Main PF must be reported both gross and with diagnostic spread stress. Gross-only PF cannot pass the trading gate by itself.

---

## Fixed Research Contract

Stage 6.0 is intentionally narrow.

**Instrument/timeframe:** XAUUSD H1, existing split.

**Decision time:** row `time` after all `fractal0` fields are available.

**Entry convention:** `Open[row+1]`. This is more realistic than `Close[row]`, but still `DIAGNOSTIC_ONLY` until runtime timing is proven. The entry bar is included in TP/SL scanning because the assumption is: order is filled exactly at that bar open, and the subsequent high/low range of the same bar occurs after entry. This assumption must be tested explicitly.

**Direction convention:**

- `fractal0.direction == -1` -> BUY.
- `fractal0.direction == 1` -> SELL.
- other values -> skip row.

**Barrier convention:**

- Horizon: `24` H1 bars after entry.
- BUY stop: `fractal0.price - 0.5 * ATR`.
- BUY take-profit: `entry_price + 2.0 * ATR`.
- SELL stop: `fractal0.price + 0.5 * ATR`.
- SELL take-profit: `entry_price - 2.0 * ATR`.

**Same-bar ambiguity:** if TP and SL are both touched in the same OHLC bar, classify as `AMBIGUOUS_SL_FIRST` and count as SL for conservative evaluation.

**Outcome columns:**

- `stage6_side`: `buy`, `sell`, or empty.
- `stage6_entry_time`: timestamp of `Open[row+1]`.
- `stage6_entry_price`: entry price.
- `stage6_stop_price`: stop level.
- `stage6_take_price`: take-profit level.
- `stage6_close_reason`: `TP`, `SL`, `TIMEOUT`, `AMBIGUOUS_SL_FIRST`, or `INVALID`.
- `stage6_invalid_reason`: empty for valid rows, otherwise `TIME_NOT_FOUND`, `OHLC_HORIZON_MISSING`, `BAD_FRACTAL_OR_ATR`, or `BAD_DIRECTION`.
- `stage6_bars_held`: number of bars until close.
- `stage6_pnl_r`: realized result in risk units; TP = reward/risk, SL = -1, timeout = signed close-vs-entry move divided by risk.
- `stage6_pnl_r_spread_020`: diagnostic realized result after a fixed 0.20 price-unit spread stress.
- `stage6_pnl_r_spread_040`: diagnostic realized result after a fixed 0.40 price-unit spread stress.
- `stage6_risk_atr`: absolute entry-to-stop distance divided by ATR.
- `stage6_reward_risk`: absolute take-profit distance divided by absolute entry-to-stop distance.
- `stage6_tp_vs_rest_flag`: training target, `1` for `TP`, `0` for `SL`, `AMBIGUOUS_SL_FIRST`, and `TIMEOUT`.
- `stage6_definitive_tp_vs_sl_flag`: disclosure target, `1` for TP, `0` for SL/ambiguous, `NaN` for timeout.

**Feature baseline:** use the strongest narrow Stage 5 signal family without price expansion:

- primary profile: `clock_shift_back`;
- disclosure profile: `clock_shift_back_impulse`.

Rationale: Stage 5.3/5.4 repeatedly found `back` as the only stable structural clue; price/ATR was rejected. The disclosure profile is trained only to show sensitivity to `impulse`. It cannot replace the primary profile in the gate even if its metrics are higher.

**Main model:** XGBoost binary classifier on `stage6_tp_vs_rest_flag`.

**Primary gate:** composite validation trading gate: gross/net PF, minimum frequency, yearly PF, neighboring-threshold stability, and diagnostic-holdout non-catastrophe. PF is necessary but not sufficient because two validation years are too short for PF-only selection.

**Secondary metrics:** AUC, PR AUC lift, trades/year, yearly stability, close-reason mix, timeout share, timeout PnL distribution, risk/reward distribution, prediction distribution.

---

## File Structure

**Create**

- `ML/baseline/benchmark_stage6_outcome_based.py` — isolated Stage 6.0 label/preflight/model/trading runner.
- `tests/test_stage6_outcome_based.py` — unit tests for first-touch labels, timeout PnL, feature denylist, preflight, and threshold logic.
- `docs/reports/2026-06-29-stage6_0-outcome-based-triple-barrier-foundation.md` — final report after full run.

**Modify**

- `CHANGELOG.md` — add final Stage 6.0 summary after report.
- `CONTEXT_HANDOFF.md` — update current state and next step after report.
- `wiki/research/fractal-stop-research.md` or a new outcome/TB wiki page — ingest the conclusion after report.

**Generated**

- `ML/reports/stage6_0_outcome_based_triple_barrier.json` — structured artifact.

**Read before implementation**

- `docs/methodology/04-labeling.md`
- `docs/methodology/06b-oracle-preflight.md`
- `docs/methodology/07-baseline-first.md`
- `docs/methodology/12-backtest-costs.md`
- `docs/reports/2026-04-08-triple-barrier-hardening.md`
- `docs/reports/2026-04-08-triple-barrier-runtime-verdict.md`
- `docs/reports/2026-04-13-label-convention-audit.md`
- `docs/reports/2026-06-26-stage5_3-time-to-breach-target-reformulation.md`
- `docs/reports/2026-06-29-stage5_4-fast-price-atr-ablation.md`

---

### Task 1: Stage 6.0 Skeleton And Fixed Contract

**Files:**
- Create: `ML/baseline/benchmark_stage6_outcome_based.py`
- Create: `tests/test_stage6_outcome_based.py`

**Interfaces:**
- Produces: `Stage60Config`, `STAGE6_0_CONFIG`, `stage6_target_columns()`, `stage6_feature_denylist()`.
- Later tasks rely on the exact column names from `stage6_target_columns()`.

- [ ] **Step 1: Write failing tests for the fixed contract**

Add to `tests/test_stage6_outcome_based.py`:

```python
import numpy as np
import pandas as pd
import pytest

import ML.baseline.benchmark_stage6_outcome_based as s6


def test_stage6_config_is_fixed_and_narrow():
    cfg = s6.STAGE6_0_CONFIG

    assert cfg.horizon_bars == 24
    assert cfg.stop_offset_atr == 0.5
    assert cfg.take_profit_atr == 2.0
    assert cfg.entry_lag_bars == 1
    assert cfg.same_bar_policy == "sl_first"
    assert cfg.primary_profile == "clock_shift_back"
    assert cfg.disclosure_profiles == ("clock_shift_back_impulse",)


def test_stage6_target_columns_are_denied_from_features():
    target_cols = set(s6.stage6_target_columns())
    denylist = set(s6.stage6_feature_denylist())

    assert "stage6_tp_vs_rest_flag" in target_cols
    assert "stage6_pnl_r" in target_cols
    assert target_cols <= denylist
    assert all(col.startswith("stage6_") for col in target_cols)
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage6_outcome_based.py -q
```

Expected: fail with `ModuleNotFoundError` or missing symbols.

- [ ] **Step 3: Create the minimal Stage 6.0 module**

Add `ML/baseline/benchmark_stage6_outcome_based.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "DATA"
REPORTS_DIR = ROOT / "ML" / "reports"
OHLC_FILE = ROOT / "MT" / "MQL4" / "Files" / "Nero.csv"
STAGE6_0_JSON_REPORT_PATH = REPORTS_DIR / "stage6_0_outcome_based_triple_barrier.json"


@dataclass(frozen=True)
class Stage60Config:
    horizon_bars: int = 24
    stop_offset_atr: float = 0.5
    take_profit_atr: float = 2.0
    entry_lag_bars: int = 1
    same_bar_policy: str = "sl_first"
    primary_profile: str = "clock_shift_back"
    disclosure_profiles: tuple[str, ...] = ("clock_shift_back_impulse",)
    seeds: tuple[int, ...] = (42, 77, 123)


STAGE6_0_CONFIG = Stage60Config()


def stage6_target_columns() -> tuple[str, ...]:
    return (
        "stage6_side",
        "stage6_entry_time",
        "stage6_entry_price",
        "stage6_stop_price",
        "stage6_take_price",
        "stage6_close_reason",
        "stage6_invalid_reason",
        "stage6_bars_held",
        "stage6_pnl_r",
        "stage6_pnl_r_spread_020",
        "stage6_pnl_r_spread_040",
        "stage6_risk_atr",
        "stage6_reward_risk",
        "stage6_tp_vs_rest_flag",
        "stage6_definitive_tp_vs_sl_flag",
    )


def stage6_feature_denylist() -> tuple[str, ...]:
    return stage6_target_columns()
```

- [ ] **Step 4: Run tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage6_outcome_based.py -q
```

Expected: `2 passed`.

- [ ] **Step 5: Commit**

```bash
git add ML/baseline/benchmark_stage6_outcome_based.py tests/test_stage6_outcome_based.py
git commit -m "feat: add stage 6 outcome contract"
```

---

### Task 2: First-Touch Outcome Labeler

**Files:**
- Modify: `ML/baseline/benchmark_stage6_outcome_based.py`
- Modify: `tests/test_stage6_outcome_based.py`

**Interfaces:**
- Consumes: `STAGE6_0_CONFIG`.
- Produces:
  - `stage6_first_touch_trade_result(entry_price: float, stop_price: float, take_price: float, side: str, future_bars: list[dict], timeout_close: float | None = None) -> dict`
  - result dict keys: `close_reason`, `bars_held`, `pnl_r`.

- [ ] **Step 1: Write failing tests for TP, SL, same-bar ambiguity, and timeout PnL**

Add:

```python
def test_stage6_first_touch_tp_sl_ambiguous_and_timeout():
    buy_tp = s6.stage6_first_touch_trade_result(
        entry_price=100.0,
        stop_price=98.0,
        take_price=104.0,
        side="buy",
        future_bars=[{"open": 100.0, "high": 104.5, "low": 99.0, "close": 104.0}],
    )
    sell_sl = s6.stage6_first_touch_trade_result(
        entry_price=100.0,
        stop_price=102.0,
        take_price=96.0,
        side="sell",
        future_bars=[{"open": 100.0, "high": 102.5, "low": 99.0, "close": 101.0}],
    )
    ambiguous = s6.stage6_first_touch_trade_result(
        entry_price=100.0,
        stop_price=98.0,
        take_price=104.0,
        side="buy",
        future_bars=[{"open": 100.0, "high": 105.0, "low": 97.5, "close": 100.0}],
    )
    timeout = s6.stage6_first_touch_trade_result(
        entry_price=100.0,
        stop_price=98.0,
        take_price=104.0,
        side="buy",
        future_bars=[{"open": 100.0, "high": 101.0, "low": 99.0, "close": 101.0}],
    )

    assert buy_tp == {"close_reason": "TP", "bars_held": 1, "pnl_r": 2.0}
    assert sell_sl == {"close_reason": "SL", "bars_held": 1, "pnl_r": -1.0}
    assert ambiguous == {"close_reason": "AMBIGUOUS_SL_FIRST", "bars_held": 1, "pnl_r": -1.0}
    assert timeout == {"close_reason": "TIMEOUT", "bars_held": 1, "pnl_r": 0.5}
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage6_outcome_based.py::test_stage6_first_touch_tp_sl_ambiguous_and_timeout -q
```

Expected: fail with missing function.

- [ ] **Step 3: Implement first-touch helper**

Add:

```python
def stage6_first_touch_trade_result(entry_price: float, stop_price: float,
                                    take_price: float, side: str,
                                    future_bars: list[dict],
                                    timeout_close: float | None = None) -> dict:
    if side not in {"buy", "sell"}:
        raise ValueError(f"side must be buy or sell, got {side}")
    risk = abs(entry_price - stop_price)
    reward = abs(take_price - entry_price)
    if risk <= 0.0:
        return {"close_reason": "INVALID", "bars_held": 0, "pnl_r": np.nan}

    for idx, bar in enumerate(future_bars, start=1):
        high = float(bar["high"])
        low = float(bar["low"])
        close = float(bar["close"])
        if side == "buy":
            sl_hit = low <= stop_price
            tp_hit = high >= take_price
        else:
            sl_hit = high >= stop_price
            tp_hit = low <= take_price
        if sl_hit and tp_hit:
            return {"close_reason": "AMBIGUOUS_SL_FIRST", "bars_held": idx, "pnl_r": -1.0}
        if sl_hit:
            return {"close_reason": "SL", "bars_held": idx, "pnl_r": -1.0}
        if tp_hit:
            return {"close_reason": "TP", "bars_held": idx, "pnl_r": float(reward / risk)}

    if not future_bars:
        return {"close_reason": "INVALID", "bars_held": 0, "pnl_r": np.nan}
    close = float(timeout_close if timeout_close is not None else future_bars[-1]["close"])
    if side == "buy":
        pnl_r = (close - entry_price) / risk
    else:
        pnl_r = (entry_price - close) / risk
    return {"close_reason": "TIMEOUT", "bars_held": len(future_bars), "pnl_r": float(pnl_r)}
```

- [ ] **Step 4: Run tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage6_outcome_based.py -q
```

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add ML/baseline/benchmark_stage6_outcome_based.py tests/test_stage6_outcome_based.py
git commit -m "feat: add stage 6 first-touch outcome helper"
```

---

### Task 3: OHLC Index And Stage 6 Label Builder

**Files:**
- Modify: `ML/baseline/benchmark_stage6_outcome_based.py`
- Modify: `tests/test_stage6_outcome_based.py`

**Interfaces:**
- Consumes: `stage6_first_touch_trade_result()`.
- Produces:
  - `stage6_load_ohlc_index(path: Path) -> tuple[dict, list[pd.Timestamp], dict[pd.Timestamp, int]]`
  - `stage6_build_outcome_labels(df: pd.DataFrame, ohlc_path: Path = OHLC_FILE, config: Stage60Config = STAGE6_0_CONFIG) -> pd.DataFrame`

- [ ] **Step 1: Write failing test for entry on `Open[row+1]` and row-time alignment**

Add:

```python
def test_stage6_build_outcome_labels_uses_next_bar_open_and_row_time(tmp_path):
    ohlc_path = tmp_path / "ohlc.csv"
    pd.DataFrame([
        {"time": "2025.01.01 00:00", "open": 100.0, "high": 100.0, "low": 100.0, "close": 100.0},
        {"time": "2025.01.01 01:00", "open": 101.0, "high": 101.0, "low": 100.0, "close": 100.5},
        {"time": "2025.01.01 02:00", "open": 101.0, "high": 105.5, "low": 100.8, "close": 105.0},
    ]).to_csv(ohlc_path, sep=";", index=False)

    fractal0 = "0:100.0:-1:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:1.0:0"
    df = pd.DataFrame([{
        "time": "2025.01.01 01:00",
        "ATR": 2.0,
        "fractal0": fractal0,
    }])

    out = s6.stage6_build_outcome_labels(df, ohlc_path=ohlc_path)

    assert out.loc[0, "stage6_side"] == "buy"
    assert out.loc[0, "stage6_entry_price"] == 101.0
    assert out.loc[0, "stage6_stop_price"] == 99.0
    assert out.loc[0, "stage6_take_price"] == 105.0
    assert out.loc[0, "stage6_close_reason"] == "TP"
    assert out.loc[0, "stage6_tp_vs_rest_flag"] == 1


def test_stage6_entry_bar_high_low_are_counted_after_open(tmp_path):
    ohlc_path = tmp_path / "ohlc.csv"
    pd.DataFrame([
        {"time": "2025.01.01 00:00", "open": 100.0, "high": 100.0, "low": 100.0, "close": 100.0},
        {"time": "2025.01.01 01:00", "open": 100.0, "high": 100.0, "low": 100.0, "close": 100.0},
        {"time": "2025.01.01 02:00", "open": 101.0, "high": 105.2, "low": 100.9, "close": 104.0},
    ]).to_csv(ohlc_path, sep=";", index=False)

    fractal0 = "0:100.0:-1:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:1.0:0"
    df = pd.DataFrame([{
        "time": "2025.01.01 01:00",
        "ATR": 2.0,
        "fractal0": fractal0,
    }])

    out = s6.stage6_build_outcome_labels(df, ohlc_path=ohlc_path)

    assert out.loc[0, "stage6_entry_time"] == pd.Timestamp("2025-01-01 02:00:00")
    assert out.loc[0, "stage6_entry_price"] == 101.0
    assert out.loc[0, "stage6_close_reason"] == "TP"
    assert out.loc[0, "stage6_bars_held"] == 1
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage6_outcome_based.py::test_stage6_build_outcome_labels_uses_next_bar_open_and_row_time -q
```

Expected: fail with missing function.

- [ ] **Step 3: Implement OHLC parsing, fractal0 parsing, and label builder**

Implementation requirements:

- Reuse `extract_stage5_1b_fields()` from `ML.baseline.benchmark_stage5_transformer_breach` instead of writing a new fractal parser.
- Parse `time` with `pd.to_datetime(..., format="%Y.%m.%d %H:%M", errors="coerce")`.
- If `entry_idx + horizon_bars` exceeds available OHLC, mark row `INVALID`.
- Include the entry bar in `future_bars` and document this as "entry at bar open, then same-bar high/low can trigger TP/SL".
- Do not mutate input frame in place.
- Fill all `stage6_` columns for every row.

Add imports:

```python
from ML.baseline.benchmark_stage5_transformer_breach import extract_stage5_1b_fields
```

Add implementation:

```python
def _stage6_parse_time(value) -> pd.Timestamp | None:
    ts = pd.to_datetime(value, format="%Y.%m.%d %H:%M", errors="coerce")
    if pd.isna(ts):
        return None
    return pd.Timestamp(ts)


def stage6_load_ohlc_index(path: Path = OHLC_FILE):
    df = pd.read_csv(path, sep=";")
    df["time"] = pd.to_datetime(df["time"], format="%Y.%m.%d %H:%M", errors="coerce")
    df = df.dropna(subset=["time"]).copy()
    df = df.sort_values("time").reset_index(drop=True)
    times = [pd.Timestamp(v) for v in df["time"]]
    ohlc = {
        times[i]: {
            "open": float(df.at[i, "open"]),
            "high": float(df.at[i, "high"]),
            "low": float(df.at[i, "low"]),
            "close": float(df.at[i, "close"]),
        }
        for i in range(len(df))
    }
    time_idx = {ts: i for i, ts in enumerate(times)}
    return ohlc, times, time_idx


def _stage6_invalid_row() -> dict:
    return {
        "stage6_side": "",
        "stage6_entry_time": pd.NaT,
        "stage6_entry_price": np.nan,
        "stage6_stop_price": np.nan,
        "stage6_take_price": np.nan,
        "stage6_close_reason": "INVALID",
        "stage6_invalid_reason": "UNKNOWN",
        "stage6_bars_held": 0,
        "stage6_pnl_r": np.nan,
        "stage6_pnl_r_spread_020": np.nan,
        "stage6_pnl_r_spread_040": np.nan,
        "stage6_risk_atr": np.nan,
        "stage6_reward_risk": np.nan,
        "stage6_tp_vs_rest_flag": np.nan,
        "stage6_definitive_tp_vs_sl_flag": np.nan,
    }


def stage6_build_outcome_labels(df: pd.DataFrame,
                                ohlc_path: Path = OHLC_FILE,
                                config: Stage60Config = STAGE6_0_CONFIG) -> pd.DataFrame:
    out = df.copy()
    ohlc, times, time_idx = stage6_load_ohlc_index(ohlc_path)
    rows = []
    for _, row in out.iterrows():
        labels = _stage6_invalid_row()
        row_time = _stage6_parse_time(row.get("time"))
        if row_time is None or row_time not in time_idx:
            labels["stage6_invalid_reason"] = "TIME_NOT_FOUND"
            rows.append(labels)
            continue
        source_idx = time_idx[row_time]
        entry_idx = source_idx + config.entry_lag_bars
        end_idx = entry_idx + config.horizon_bars
        if entry_idx >= len(times) or end_idx > len(times):
            labels["stage6_invalid_reason"] = "OHLC_HORIZON_MISSING"
            rows.append(labels)
            continue
        fields = extract_stage5_1b_fields(str(row.get("fractal0", "")))
        direction = fields.get("direction", 0.0)
        fractal_price = float(fields.get("price", 0.0) or 0.0)
        atr = float(row.get("ATR", 0.0) or 0.0)
        if atr <= 0.0 or fractal_price <= 0.0:
            labels["stage6_invalid_reason"] = "BAD_FRACTAL_OR_ATR"
            rows.append(labels)
            continue
        entry_time = times[entry_idx]
        entry_price = float(ohlc[entry_time]["open"])
        if direction == -1:
            side = "buy"
            stop_price = fractal_price - config.stop_offset_atr * atr
            take_price = entry_price + config.take_profit_atr * atr
        elif direction == 1:
            side = "sell"
            stop_price = fractal_price + config.stop_offset_atr * atr
            take_price = entry_price - config.take_profit_atr * atr
        else:
            labels["stage6_invalid_reason"] = "BAD_DIRECTION"
            rows.append(labels)
            continue
        future = [ohlc[t] for t in times[entry_idx:end_idx]]
        result = stage6_first_touch_trade_result(
            entry_price=entry_price,
            stop_price=stop_price,
            take_price=take_price,
            side=side,
            future_bars=future,
        )
        reason = result["close_reason"]
        risk = abs(entry_price - stop_price)
        reward = abs(take_price - entry_price)
        labels.update({
            "stage6_side": side,
            "stage6_entry_time": entry_time,
            "stage6_entry_price": entry_price,
            "stage6_stop_price": stop_price,
            "stage6_take_price": take_price,
            "stage6_close_reason": reason,
            "stage6_invalid_reason": "",
            "stage6_bars_held": int(result["bars_held"]),
            "stage6_pnl_r": float(result["pnl_r"]) if np.isfinite(result["pnl_r"]) else np.nan,
            "stage6_pnl_r_spread_020": float(result["pnl_r"] - 0.20 / risk) if risk > 0 else np.nan,
            "stage6_pnl_r_spread_040": float(result["pnl_r"] - 0.40 / risk) if risk > 0 else np.nan,
            "stage6_risk_atr": float(risk / atr) if atr > 0 else np.nan,
            "stage6_reward_risk": float(reward / risk) if risk > 0 else np.nan,
        })
        if reason == "TP":
            labels["stage6_tp_vs_rest_flag"] = 1
            labels["stage6_definitive_tp_vs_sl_flag"] = 1
        elif reason in {"SL", "AMBIGUOUS_SL_FIRST"}:
            labels["stage6_tp_vs_rest_flag"] = 0
            labels["stage6_definitive_tp_vs_sl_flag"] = 0
        elif reason == "TIMEOUT":
            labels["stage6_tp_vs_rest_flag"] = 0
            labels["stage6_definitive_tp_vs_sl_flag"] = np.nan
        rows.append(labels)
    labels_df = pd.DataFrame(rows, index=out.index)
    for col in stage6_target_columns():
        out[col] = labels_df[col]
    return out
```

- [ ] **Step 4: Run tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage6_outcome_based.py -q
```

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add ML/baseline/benchmark_stage6_outcome_based.py tests/test_stage6_outcome_based.py
git commit -m "feat: add stage 6 outcome labels"
```

---

### Task 4: Split Loading, Preflight, And Oracle Mechanics Check

**Files:**
- Modify: `ML/baseline/benchmark_stage6_outcome_based.py`
- Modify: `tests/test_stage6_outcome_based.py`

**Interfaces:**
- Consumes: `stage6_build_outcome_labels()`.
- Produces:
  - `stage6_load_labeled_splits() -> dict[str, pd.DataFrame]`
  - `stage6_outcome_preflight(split: dict[str, pd.DataFrame]) -> dict`
  - `stage6_oracle_preflight(split: dict[str, pd.DataFrame]) -> dict`

- [ ] **Step 1: Write failing tests for preflight and PF partition**

Add:

```python
def test_stage6_preflight_counts_outcomes_and_pf_without_timeout_as_loss():
    split = {
        "train_core": pd.DataFrame({
            "stage6_close_reason": ["TP", "SL", "TIMEOUT", "AMBIGUOUS_SL_FIRST"],
            "stage6_tp_vs_rest_flag": [1, 0, 0, 0],
            "stage6_pnl_r": [2.0, -1.0, 0.25, -1.0],
            "stage6_risk_atr": [1.0, 1.2, 0.8, 1.1],
            "stage6_reward_risk": [2.0, 1.7, 2.5, 1.8],
            "_year": [2020, 2020, 2020, 2020],
            "stage6_side": ["buy", "buy", "sell", "sell"],
        }),
        "val_stop": pd.DataFrame({
            "stage6_close_reason": ["TP", "TIMEOUT"],
            "stage6_tp_vs_rest_flag": [1, 0],
            "stage6_pnl_r": [2.0, -0.2],
            "stage6_risk_atr": [1.0, 1.0],
            "stage6_reward_risk": [2.0, 2.0],
            "_year": [2021, 2021],
            "stage6_side": ["buy", "sell"],
        }),
    }

    preflight = s6.stage6_outcome_preflight(split)
    oracle = s6.stage6_oracle_preflight(split)

    assert preflight["train_core"]["n"] == 4
    assert preflight["train_core"]["tp_rate"] == 0.25
    assert preflight["train_core"]["timeout_rate"] == 0.25
    assert preflight["train_core"]["risk_atr"]["max"] == 1.2
    assert preflight["train_core"]["reward_risk"]["median"] == 1.9
    assert preflight["train_core"]["by_side"]["buy"]["n"] == 2
    assert oracle["train_core"]["all_trade_pf"] == 2.0 / 2.2
    assert oracle["train_core"]["tp_only_oracle_trades"] == 1
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage6_outcome_based.py::test_stage6_preflight_counts_outcomes_and_pf_without_timeout_as_loss -q
```

Expected: fail with missing functions.

- [ ] **Step 3: Implement split loading and preflight**

Implementation rules:

- Load existing `DATA/Nero_XAUUSD_train_labeled.csv`, `DATA/Nero_XAUUSD_validation_labeled.csv`, `DATA/Nero_XAUUSD_test_labeled.csv`.
- Build Stage 6 labels in memory; do not write them into DATA in this stage.
- Split years:
  - `train_core`: `<= 2020`
  - `val_stop`: `2021-2022`
  - `diagnostic_holdout`: `2023-2025`
  - `low_n_disclosure`: `2026`
- Preflight must report valid rows, invalid rows, TP/SL/TIMEOUT/ambiguous shares, yearly counts, and warnings.
- Preflight must report `risk_atr`, `reward_risk`, and `stage6_pnl_r` distribution before any training.
- Preflight must report buy/sell side metrics separately, not only aggregate metrics.
- Split/OHLC integrity must be checked before training:
  - no duplicate `time` values after concatenating old train/validation/test CSV files;
  - years are routed only to the expected groups;
  - no split contains rows outside its assigned year range;
  - invalid rows caused by missing OHLC horizon are counted separately from invalid rows caused by bad fractal/ATR data.
- Warnings:
  - `TP_RATE_OUTSIDE_0_05_0_70` if TP rate is below 5% or above 70%.
  - `TIMEOUT_GT_0_70` if timeout rate is above 70%.
  - `VALID_ROWS_LT_1000` if split has fewer than 1000 valid rows.
  - `YEARLY_VALID_LT_200` for any year with fewer than 200 valid rows.
  - `RISK_ATR_P01_LE_0` if the 1st percentile of `stage6_risk_atr` is <= 0.
  - `RISK_ATR_P99_GT_10` if the 99th percentile of `stage6_risk_atr` is > 10.
  - `REWARD_RISK_P99_GT_20` if the 99th percentile of `stage6_reward_risk` is > 20.
  - `PNL_R_ABS_MAX_GT_20` if `abs(stage6_pnl_r).max()` is > 20.
  - `DUPLICATE_TIME_VALUES` if concatenated source rows duplicate `time`.

Add:

```python
def _stage6_pf_from_pnl(values) -> float | None:
    arr = np.asarray(values, dtype=np.float64)
    arr = arr[np.isfinite(arr)]
    profit = float(arr[arr > 0.0].sum())
    loss = float(-arr[arr < 0.0].sum())
    if loss == 0.0:
        return None if profit == 0.0 else float("inf")
    return profit / loss


def _stage6_add_year(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    ts = pd.to_datetime(out["time"], format="%Y.%m.%d %H:%M", errors="coerce")
    out["_year"] = ts.dt.year
    return out


def _stage6_distribution_summary(values) -> dict:
    arr = np.asarray(values, dtype=np.float64)
    arr = arr[np.isfinite(arr)]
    if len(arr) == 0:
        return {"n": 0, "min": None, "p01": None, "median": None, "p99": None, "max": None}
    return {
        "n": int(len(arr)),
        "min": float(np.min(arr)),
        "p01": float(np.percentile(arr, 1)),
        "median": float(np.median(arr)),
        "p99": float(np.percentile(arr, 99)),
        "max": float(np.max(arr)),
    }


def stage6_split_integrity_audit(full: pd.DataFrame, labeled: pd.DataFrame) -> dict:
    warnings = []
    duplicate_times = int(full["time"].duplicated().sum()) if "time" in full else 0
    if duplicate_times:
        warnings.append("DUPLICATE_TIME_VALUES")
    expected_years = {
        "train_core": lambda y: y <= 2020,
        "val_stop": lambda y: 2021 <= y <= 2022,
        "diagnostic_holdout": lambda y: 2023 <= y <= 2025,
        "low_n_disclosure": lambda y: y == 2026,
    }
    year_counts = labeled["_year"].value_counts(dropna=False).sort_index().to_dict()
    invalid_reasons = labeled.get("stage6_invalid_reason", pd.Series(["unknown"] * len(labeled))).value_counts().to_dict()
    return {
        "duplicate_times": duplicate_times,
        "year_counts": {str(k): int(v) for k, v in year_counts.items()},
        "expected_year_rules": list(expected_years.keys()),
        "invalid_reasons": {str(k): int(v) for k, v in invalid_reasons.items()},
        "warnings": warnings,
    }


def stage6_load_labeled_splits(ohlc_path: Path = OHLC_FILE) -> dict[str, pd.DataFrame]:
    train = pd.read_csv(DATA_DIR / "Nero_XAUUSD_train_labeled.csv", sep=";")
    val = pd.read_csv(DATA_DIR / "Nero_XAUUSD_validation_labeled.csv", sep=";")
    test = pd.read_csv(DATA_DIR / "Nero_XAUUSD_test_labeled.csv", sep=";")
    full = pd.concat([train, val, test], ignore_index=True)
    labeled = _stage6_add_year(stage6_build_outcome_labels(full, ohlc_path=ohlc_path))
    splits = {
        "train_core": labeled.loc[labeled["_year"] <= 2020].copy(),
        "val_stop": labeled.loc[labeled["_year"].between(2021, 2022)].copy(),
        "diagnostic_holdout": labeled.loc[labeled["_year"].between(2023, 2025)].copy(),
        "low_n_disclosure": labeled.loc[labeled["_year"] == 2026].copy(),
    }
    splits["_integrity"] = stage6_split_integrity_audit(full, labeled)
    return splits


def _stage6_split_preflight(df: pd.DataFrame) -> dict:
    valid = df["stage6_close_reason"] != "INVALID"
    sub = df.loc[valid]
    n = int(len(sub))
    counts = sub["stage6_close_reason"].value_counts().to_dict()
    tp = int(counts.get("TP", 0))
    sl = int(counts.get("SL", 0) + counts.get("AMBIGUOUS_SL_FIRST", 0))
    timeout = int(counts.get("TIMEOUT", 0))
    yearly = {}
    warnings = []
    for year, group in sub.groupby("_year"):
        yearly[str(int(year))] = int(len(group))
        if len(group) < 200:
            warnings.append(f"YEARLY_VALID_LT_200:{int(year)}")
    tp_rate = float(tp / n) if n else 0.0
    timeout_rate = float(timeout / n) if n else 0.0
    risk = sub["stage6_risk_atr"].to_numpy(dtype=np.float64) if "stage6_risk_atr" in sub else np.asarray([])
    reward_risk = sub["stage6_reward_risk"].to_numpy(dtype=np.float64) if "stage6_reward_risk" in sub else np.asarray([])
    pnl = sub["stage6_pnl_r"].to_numpy(dtype=np.float64) if "stage6_pnl_r" in sub else np.asarray([])
    timeout_pnl = sub.loc[sub["stage6_close_reason"] == "TIMEOUT", "stage6_pnl_r"].to_numpy(dtype=np.float64)
    by_side = {}
    if "stage6_side" in sub:
        for side, group in sub.groupby("stage6_side"):
            by_side[str(side)] = {
                "n": int(len(group)),
                "tp_rate": float((group["stage6_close_reason"] == "TP").mean()) if len(group) else 0.0,
                "pf": _stage6_pf_from_pnl(group["stage6_pnl_r"]),
            }
    if tp_rate < 0.05 or tp_rate > 0.70:
        warnings.append("TP_RATE_OUTSIDE_0_05_0_70")
    if timeout_rate > 0.70:
        warnings.append("TIMEOUT_GT_0_70")
    if n < 1000:
        warnings.append("VALID_ROWS_LT_1000")
    if len(risk) and np.nanpercentile(risk, 1) <= 0:
        warnings.append("RISK_ATR_P01_LE_0")
    if len(risk) and np.nanpercentile(risk, 99) > 10:
        warnings.append("RISK_ATR_P99_GT_10")
    if len(reward_risk) and np.nanpercentile(reward_risk, 99) > 20:
        warnings.append("REWARD_RISK_P99_GT_20")
    if len(pnl) and np.nanmax(np.abs(pnl)) > 20:
        warnings.append("PNL_R_ABS_MAX_GT_20")
    return {
        "n": n,
        "invalid": int((~valid).sum()),
        "counts": {str(k): int(v) for k, v in counts.items()},
        "tp_rate": tp_rate,
        "sl_or_ambiguous_rate": float(sl / n) if n else 0.0,
        "timeout_rate": timeout_rate,
        "risk_atr": _stage6_distribution_summary(risk),
        "reward_risk": _stage6_distribution_summary(reward_risk),
        "pnl_r": _stage6_distribution_summary(pnl),
        "timeout_pnl_r": {
            **_stage6_distribution_summary(timeout_pnl),
            "profitable_timeout_rate": float((timeout_pnl > 0).mean()) if len(timeout_pnl) else None,
            "total_timeout_pnl_r": float(np.nansum(timeout_pnl)) if len(timeout_pnl) else 0.0,
        },
        "by_side": by_side,
        "yearly_valid_rows": yearly,
        "warnings": warnings,
    }


def stage6_outcome_preflight(split: dict[str, pd.DataFrame]) -> dict:
    out = {
        name: _stage6_split_preflight(df)
        for name, df in split.items()
        if isinstance(df, pd.DataFrame)
    }
    if "_integrity" in split:
        out["_integrity"] = split["_integrity"]
    return out


def stage6_oracle_preflight(split: dict[str, pd.DataFrame]) -> dict:
    out = {}
    for name, df in split.items():
        if not isinstance(df, pd.DataFrame):
            continue
        valid = df["stage6_close_reason"] != "INVALID"
        sub = df.loc[valid].copy()
        tp_only = sub["stage6_close_reason"] == "TP"
        out[name] = {
            "all_trade_pf": _stage6_pf_from_pnl(sub["stage6_pnl_r"]),
            "all_trade_trades": int(len(sub)),
            "tp_only_oracle_pf": _stage6_pf_from_pnl(sub.loc[tp_only, "stage6_pnl_r"]),
            "tp_only_oracle_trades": int(tp_only.sum()),
            "trades_per_year": float(len(sub) / max(sub["_year"].nunique(), 1)) if len(sub) else 0.0,
        }
    return out
```

- [ ] **Step 4: Run tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage6_outcome_based.py -q
```

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add ML/baseline/benchmark_stage6_outcome_based.py tests/test_stage6_outcome_based.py
git commit -m "feat: add stage 6 preflight"
```

---

### Task 5: Feature Builder With Explicit Denylist

**Files:**
- Modify: `ML/baseline/benchmark_stage6_outcome_based.py`
- Modify: `tests/test_stage6_outcome_based.py`

**Interfaces:**
- Consumes: Stage 5 feature builders.
- Produces:
  - `stage6_build_features(df: pd.DataFrame, profile: str) -> np.ndarray`
  - `stage6_build_feature_split(split: dict[str, pd.DataFrame], profile: str) -> dict[str, np.ndarray]`

- [ ] **Step 1: Write failing test proving target columns do not affect features**

Add:

```python
def test_stage6_build_features_ignores_stage6_target_columns(monkeypatch):
    captured = {}

    def fake_builder(df, profile_key):
        captured["columns"] = tuple(df.columns)
        return np.zeros((len(df), 3), dtype=np.float32)

    monkeypatch.setattr(s6, "build_stage5_4_features", fake_builder)
    df = pd.DataFrame({
        "time": ["2025.01.01 00:00"],
        "stage6_tp_vs_rest_flag": [1],
        "stage6_pnl_r": [2.0],
    })

    X = s6.stage6_build_features(df, "clock_shift_back")

    assert X.shape == (1, 3)
    assert "stage6_tp_vs_rest_flag" not in captured["columns"]
    assert "stage6_pnl_r" not in captured["columns"]


def test_stage6_assert_feature_names_rejects_stage6_targets():
    with pytest.raises(AssertionError, match="stage6_"):
        s6.stage6_assert_no_target_feature_names(["fractal0.back", "stage6_pnl_r"])
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage6_outcome_based.py::test_stage6_build_features_ignores_stage6_target_columns -q
```

Expected: fail with missing function or import.

- [ ] **Step 3: Implement feature wrapper**

Add imports:

```python
from ML.baseline.benchmark_stage5_transformer_breach import build_stage5_4_features
```

Add:

```python
def stage6_assert_no_target_feature_names(feature_names: list[str] | tuple[str, ...] | None) -> None:
    if not feature_names:
        return
    bad = [name for name in feature_names if str(name).startswith("stage6_")]
    assert not bad, f"stage6 target leaked into feature names: {bad[:5]}"


def stage6_build_features(df: pd.DataFrame, profile: str) -> np.ndarray:
    clean = df.drop(columns=[c for c in stage6_feature_denylist() if c in df.columns])
    X = build_stage5_4_features(clean, profile)
    feature_names = getattr(X, "feature_names", None)
    stage6_assert_no_target_feature_names(feature_names)
    return X


def stage6_build_feature_split(split: dict[str, pd.DataFrame], profile: str) -> dict[str, np.ndarray]:
    return {
        name: stage6_build_features(df, profile)
        for name, df in split.items()
        if isinstance(df, pd.DataFrame)
    }
```

- [ ] **Step 4: Run tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage6_outcome_based.py -q
```

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add ML/baseline/benchmark_stage6_outcome_based.py tests/test_stage6_outcome_based.py
git commit -m "feat: add stage 6 feature wrapper"
```

---

### Task 6: XGBoost Baseline Metrics

**Files:**
- Modify: `ML/baseline/benchmark_stage6_outcome_based.py`
- Modify: `tests/test_stage6_outcome_based.py`

**Interfaces:**
- Produces:
  - `stage6_binary_metrics(y_true, y_score) -> dict`
  - `evaluate_stage6_profile_seed(split, feature_split, profile, seed) -> dict`

- [ ] **Step 1: Write failing tests for metrics edge cases**

Add:

```python
def test_stage6_binary_metrics_handles_constant_or_single_class():
    single = s6.stage6_binary_metrics(np.array([0, 0, 0]), np.array([0.2, 0.2, 0.2]))
    constant = s6.stage6_binary_metrics(np.array([0, 1, 0, 1]), np.array([0.5, 0.5, 0.5, 0.5]))

    assert single["auc"] is None
    assert single["pr_auc"] is None
    assert constant["auc"] == 0.5
    assert 0.0 <= constant["brier"] <= 1.0
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage6_outcome_based.py::test_stage6_binary_metrics_handles_constant_or_single_class -q
```

Expected: fail with missing function.

- [ ] **Step 3: Implement metrics and evaluator**

Implementation requirements:

- Use `xgboost.XGBClassifier` or `xgboost.train` with Stage 5.1 classification-like parameters:
  - `max_depth=6`
  - `learning_rate=0.03`
  - `n_estimators` or boosting rounds equivalent to `500`
  - `subsample=0.8`
  - `colsample_bytree=0.8`
  - `early_stopping_rounds=20`
- Filter rows where `stage6_tp_vs_rest_flag` is not finite.
- Store predictions and labels for `val_stop`, `diagnostic_holdout`, and `low_n_disclosure`.
- Store top feature importances if the model exposes them.

Add:

```python
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from xgboost import XGBClassifier


def stage6_binary_metrics(y_true, y_score) -> dict:
    y = np.asarray(y_true, dtype=np.int8)
    score = np.asarray(y_score, dtype=np.float64)
    out = {
        "n": int(len(y)),
        "positive_rate": float(y.mean()) if len(y) else None,
        "auc": None,
        "pr_auc": None,
        "pr_auc_lift": None,
        "brier": None,
        "pred_min": float(score.min()) if len(score) else None,
        "pred_median": float(np.median(score)) if len(score) else None,
        "pred_max": float(score.max()) if len(score) else None,
        "pred_std": float(score.std()) if len(score) else None,
    }
    if len(y) == 0:
        return out
    if len(np.unique(y)) == 2:
        try:
            out["auc"] = float(roc_auc_score(y, score))
        except ValueError:
            out["auc"] = None
        try:
            out["pr_auc"] = float(average_precision_score(y, score))
            out["pr_auc_lift"] = float(out["pr_auc"] - y.mean())
        except ValueError:
            out["pr_auc"] = None
            out["pr_auc_lift"] = None
    try:
        out["brier"] = float(brier_score_loss(y, score))
    except ValueError:
        out["brier"] = None
    return out
```

Then implement `evaluate_stage6_profile_seed()` using the same output shape as Stage 5.3/5.4: seed, profile, `val_stop`, `diagnostic_holdout`, `low_n_disclosure`, predictions, labels.

- [ ] **Step 4: Run focused tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage6_outcome_based.py -q
```

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add ML/baseline/benchmark_stage6_outcome_based.py tests/test_stage6_outcome_based.py
git commit -m "feat: add stage 6 xgboost baseline metrics"
```

---

### Task 7: Threshold Selection And Trading Simulation

**Files:**
- Modify: `ML/baseline/benchmark_stage6_outcome_based.py`
- Modify: `tests/test_stage6_outcome_based.py`

**Interfaces:**
- Produces:
  - `stage6_simulate_threshold(df, y_score, threshold) -> dict`
  - `stage6_select_threshold_on_val(df, y_score) -> dict`

- [ ] **Step 1: Write failing test for threshold PF and trade frequency**

Add:

```python
def test_stage6_threshold_simulation_uses_realized_pnl_and_min_trades():
    df = pd.DataFrame({
        "stage6_pnl_r": [2.0, -1.0, 0.5, -0.25],
        "stage6_pnl_r_spread_020": [1.8, -1.2, 0.3, -0.45],
        "stage6_pnl_r_spread_040": [1.6, -1.4, 0.1, -0.65],
        "stage6_close_reason": ["TP", "SL", "TIMEOUT", "TIMEOUT"],
        "stage6_side": ["buy", "buy", "sell", "sell"],
        "_year": [2021, 2021, 2022, 2022],
    })
    scores = np.array([0.9, 0.8, 0.7, 0.1])

    result = s6.stage6_simulate_threshold(df, scores, threshold=0.65)

    assert result["trades"] == 3
    assert result["wins"] == 1
    assert result["losses"] == 1
    assert result["timeouts"] == 1
    assert result["pf"] == 2.5
    assert result["pf_spread_020"] == 2.1 / 1.2
    assert result["by_side"]["buy"]["trades"] == 2
    assert result["trades_per_year"] == 1.5


def test_stage6_threshold_plateau_rejects_single_point_spike():
    candidates = [
        {"threshold": 0.50, "pf": 1.05, "trades": 120, "passes_min_trades": True},
        {"threshold": 0.525, "pf": 1.80, "trades": 52, "passes_min_trades": True},
        {"threshold": 0.55, "pf": 1.02, "trades": 110, "passes_min_trades": True},
    ]

    plateau = s6.stage6_threshold_plateau_check(candidates, selected_threshold=0.525)

    assert plateau["pass"] is False
    assert plateau["reason"] == "neighbor_pf_or_trades_drop"
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage6_outcome_based.py::test_stage6_threshold_simulation_uses_realized_pnl_and_min_trades -q
```

Expected: fail with missing function.

- [ ] **Step 3: Implement threshold simulation**

Rules:

- Threshold grid: `0.50..0.90` inclusive, step `0.025`.
- Select on `val_stop` only.
- Minimum validation trades: `50` total and `20` per validation year if possible; if no threshold passes, return `status=NO_THRESHOLD`.
- Maximize PF, tie-break by higher trades, then lower threshold.
- PF is based on realized `stage6_pnl_r`, so timeout can be profit or loss.
- Also compute PF for `stage6_pnl_r_spread_020` and `stage6_pnl_r_spread_040`.
- Also compute buy/sell metrics separately.
- Add `all_trade_baseline` for every split: metrics if every valid row is traded without using model scores.
- Add threshold plateau check: selected threshold must not be a single-point spike. Neighboring thresholds `threshold ± 0.025`, when they exist and pass minimum trades, must keep PF >= `selected_pf - 0.15` and trades >= `0.70 * selected_trades`.
- Add permutation baseline on `val_stop`: 200 deterministic permutations of scores per seed. Store selected PF distribution and empirical p-value `mean(permuted_pf >= selected_pf)`.

Add:

```python
def stage6_simulate_threshold(df: pd.DataFrame, y_score, threshold: float) -> dict:
    score = np.asarray(y_score, dtype=np.float64)
    selected = df.loc[score >= threshold].copy()
    pnl = selected["stage6_pnl_r"].to_numpy(dtype=np.float64)
    pnl = pnl[np.isfinite(pnl)]
    pnl_spread_020 = selected.get("stage6_pnl_r_spread_020", pd.Series(dtype=float)).to_numpy(dtype=np.float64)
    pnl_spread_040 = selected.get("stage6_pnl_r_spread_040", pd.Series(dtype=float)).to_numpy(dtype=np.float64)
    reasons = selected["stage6_close_reason"].value_counts().to_dict()
    years = selected["_year"].dropna().astype(int)
    yearly = {}
    for year, group in selected.groupby("_year"):
        yearly[str(int(year))] = {
            "trades": int(len(group)),
            "pf": _stage6_pf_from_pnl(group["stage6_pnl_r"]),
        }
    by_side = {}
    if "stage6_side" in selected:
        for side, group in selected.groupby("stage6_side"):
            by_side[str(side)] = {
                "trades": int(len(group)),
                "pf": _stage6_pf_from_pnl(group["stage6_pnl_r"]),
                "pf_spread_020": _stage6_pf_from_pnl(group.get("stage6_pnl_r_spread_020", [])),
                "pf_spread_040": _stage6_pf_from_pnl(group.get("stage6_pnl_r_spread_040", [])),
            }
    return {
        "threshold": float(threshold),
        "trades": int(len(pnl)),
        "wins": int(reasons.get("TP", 0)),
        "losses": int(reasons.get("SL", 0) + reasons.get("AMBIGUOUS_SL_FIRST", 0)),
        "timeouts": int(reasons.get("TIMEOUT", 0)),
        "pf": _stage6_pf_from_pnl(pnl),
        "pf_spread_020": _stage6_pf_from_pnl(pnl_spread_020),
        "pf_spread_040": _stage6_pf_from_pnl(pnl_spread_040),
        "mean_pnl_r": float(np.mean(pnl)) if len(pnl) else 0.0,
        "total_pnl_r": float(np.sum(pnl)) if len(pnl) else 0.0,
        "trades_per_year": float(len(pnl) / max(years.nunique(), 1)) if len(pnl) else 0.0,
        "by_side": by_side,
        "yearly": yearly,
    }


def stage6_threshold_plateau_check(candidates: list[dict], selected_threshold: float) -> dict:
    by_threshold = {float(row["threshold"]): row for row in candidates}
    selected = by_threshold[float(selected_threshold)]
    selected_pf = float(selected["pf"])
    selected_trades = int(selected["trades"])
    neighbors = [
        by_threshold[t]
        for t in (round(selected_threshold - 0.025, 3), round(selected_threshold + 0.025, 3))
        if t in by_threshold and by_threshold[t].get("passes_min_trades")
    ]
    if not neighbors:
        return {"pass": False, "reason": "no_valid_neighbors"}
    for row in neighbors:
        if float(row["pf"]) < selected_pf - 0.15 or int(row["trades"]) < 0.70 * selected_trades:
            return {"pass": False, "reason": "neighbor_pf_or_trades_drop"}
    return {"pass": True, "reason": "stable_neighbors"}


def stage6_all_trade_baseline(df: pd.DataFrame) -> dict:
    score = np.ones(len(df), dtype=np.float64)
    return stage6_simulate_threshold(df, score, threshold=0.5)


def stage6_permutation_threshold_baseline(df: pd.DataFrame, y_score, seed: int, n_perm: int = 200) -> dict:
    rng = np.random.default_rng(seed)
    score = np.asarray(y_score, dtype=np.float64)
    observed = stage6_select_threshold_on_val(df, score)
    observed_pf = None if observed["selected"] is None else observed["selected"]["pf"]
    permuted_pfs = []
    for _ in range(n_perm):
        perm = rng.permutation(score)
        selected = stage6_select_threshold_on_val(df, perm)["selected"]
        if selected is not None and selected["pf"] is not None:
            permuted_pfs.append(float(selected["pf"]))
    p_value = None
    if observed_pf is not None and permuted_pfs:
        p_value = float(np.mean(np.asarray(permuted_pfs) >= float(observed_pf)))
    return {
        "n_perm": int(n_perm),
        "observed_pf": observed_pf,
        "permuted_pf_median": float(np.median(permuted_pfs)) if permuted_pfs else None,
        "permuted_pf_p95": float(np.percentile(permuted_pfs, 95)) if permuted_pfs else None,
        "empirical_p_value": p_value,
    }


def stage6_select_threshold_on_val(df: pd.DataFrame, y_score) -> dict:
    candidates = []
    for threshold in np.round(np.arange(0.50, 0.9001, 0.025), 3):
        row = stage6_simulate_threshold(df, y_score, float(threshold))
        yearly_counts = [v["trades"] for v in row["yearly"].values()]
        row["passes_min_trades"] = row["trades"] >= 50 and all(v >= 20 for v in yearly_counts)
        candidates.append(row)
    valid = [row for row in candidates if row["passes_min_trades"] and row["pf"] is not None]
    if not valid:
        return {"status": "NO_THRESHOLD", "candidates": candidates, "selected": None}
    selected = sorted(
        valid,
        key=lambda row: (
            -float(row["pf"]) if np.isfinite(row["pf"]) else -1e9,
            -int(row["trades"]),
            float(row["threshold"]),
        ),
    )[0]
    plateau = stage6_threshold_plateau_check(candidates, selected["threshold"])
    return {"status": "SELECTED", "candidates": candidates, "selected": selected, "plateau": plateau}
```

- [ ] **Step 4: Run tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage6_outcome_based.py -q
```

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add ML/baseline/benchmark_stage6_outcome_based.py tests/test_stage6_outcome_based.py
git commit -m "feat: add stage 6 threshold simulation"
```

---

### Task 8: Full Runner, Gate, CLI, And JSON Artifact

**Files:**
- Modify: `ML/baseline/benchmark_stage6_outcome_based.py`
- Modify: `tests/test_stage6_outcome_based.py`

**Interfaces:**
- Produces:
  - `run_stage6_0_outcome_based(output_path: Path = STAGE6_0_JSON_REPORT_PATH) -> dict`
  - CLI: `./.venv/bin/python -m ML.baseline.benchmark_stage6_outcome_based --stage6-0-outcome-based`

- [ ] **Step 1: Write failing smoke test for report shape**

Add:

```python
def test_stage6_gate_marks_missing_threshold_as_trading_gate_failed():
    report = {
        "preflight": {"val_stop": {"warnings": []}},
        "oracle_preflight": {"val_stop": {"all_trade_pf": 0.8}},
        "summary": {
            "clock_shift_back": {
                "val_stop": {"auc": 0.61, "pr_auc_lift": 0.06},
                "threshold_selection": {"status": "NO_THRESHOLD", "selected": None},
            }
        },
    }

    gate = s6.stage6_gate_results(report)

    assert gate["overall_status"] == "TRADING_GATE_FAILED"
    assert gate["artifact_status"] == "DIAGNOSTIC_ONLY"
    assert gate["checks"]["threshold_selected"] is False
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage6_outcome_based.py::test_stage6_gate_marks_missing_threshold_as_trading_gate_failed -q
```

Expected: fail with missing function.

- [ ] **Step 3: Implement summary and gate**

Gate rules:

- `preflight_pass`: no `TP_RATE_OUTSIDE_0_05_0_70`, no `TIMEOUT_GT_0_70`, no `VALID_ROWS_LT_1000` on `train_core` and `val_stop`.
- `auc_ge_0_60`: primary profile median val AUC >= `0.60`.
- `pr_auc_lift_ge_0_05`: primary profile median PR AUC lift >= `0.05`.
- `threshold_selected`: threshold exists on `val_stop`.
- `threshold_plateau_pass`: selected threshold has stable neighboring thresholds.
- `threshold_seed_dispersion_le_0_10`: max selected threshold minus min selected threshold across seeds is <= `0.10`.
- `val_pf_ge_1_15`: selected val PF >= `1.15`.
- `val_pf_spread_020_ge_1_05`: selected val PF under 0.20 spread stress >= `1.05`.
- `val_pf_spread_040_disclosure`: 0.40 spread stress is reported, but does not block Stage 6.0 by itself.
- `val_trades_per_year_ge_25`: selected val trades/year >= `25`.
- `yearly_val_pf_not_single_year`: every `val_stop` year has at least `20` trades and PF >= `1.0`.
- `holdout_disclosure_not_catastrophic`: diagnostic only; flag if holdout PF < `0.95` or holdout trades/year < `15`.
- `permutation_p_value_le_0_10`: selected PF beats permuted-score threshold selection with empirical p-value <= `0.10`.

Status:

- `PREFLIGHT_FAILED` if preflight fails.
- `MODEL_GATE_FAILED` if AUC/PR checks fail.
- `TRADING_GATE_FAILED` if threshold/PF/frequency/yearly/plateau/permutation checks fail.
- `DIAGNOSTIC_SIGNAL_FOUND` if all validation checks pass but execution convention remains diagnostic.
- `gate.overall_status` may be `PREFLIGHT_FAILED`, `MODEL_GATE_FAILED`, `TRADING_GATE_FAILED`, or `DIAGNOSTIC_SIGNAL_FOUND`.
- Top-level artifact `status` must remain `DIAGNOSTIC_ONLY` for every Stage 6.0 outcome. Never emit `CANDIDATE` in Stage 6.0.

Implement `stage6_gate_results(report)` and full runner. The full runner must:

- load splits;
- write preflight before training;
- train profiles `clock_shift_back` and `clock_shift_back_impulse`;
- run seeds `(42, 77, 123)`;
- select threshold for each seed on `val_stop`;
- store selected threshold separately for every seed and report threshold dispersion;
- run 200 score permutations per seed on `val_stop`;
- summarize median AUC/PR/PF and per-seed threshold results;
- summarize all-trade baseline by split;
- apply threshold to `diagnostic_holdout` and `low_n_disclosure`;
- write JSON after each seed to survive long runs;
- include `done_runs`, `total_runs`, `elapsed_sec`.

- [ ] **Step 4: Add CLI**

Add:

```python
def main(argv: list[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage6-0-outcome-based", action="store_true")
    args = parser.parse_args(argv)
    if args.stage6_0_outcome_based:
        report = run_stage6_0_outcome_based()
        print({"status": report.get("status"), "json": str(STAGE6_0_JSON_REPORT_PATH)})
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Run focused tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage6_outcome_based.py -q
```

Expected: pass.

- [ ] **Step 6: Run full test suite**

Run:

```bash
./.venv/bin/python -m pytest tests/ -q
```

Expected: pass.

- [ ] **Step 7: Commit**

```bash
git add ML/baseline/benchmark_stage6_outcome_based.py tests/test_stage6_outcome_based.py
git commit -m "feat: add stage 6 outcome runner"
```

---

### Task 9: Full Stage 6.0 Run And Diagnostics

**Files:**
- Generated: `ML/reports/stage6_0_outcome_based_triple_barrier.json`

**Interfaces:**
- Consumes: CLI from Task 8.
- Produces: completed JSON artifact.

- [ ] **Step 1: Run Stage 6.0**

Run:

```bash
./.venv/bin/python -u -m ML.baseline.benchmark_stage6_outcome_based --stage6-0-outcome-based
```

Expected:

- JSON exists at `ML/reports/stage6_0_outcome_based_triple_barrier.json`.
- `done_runs == total_runs == 6` for `2 profiles × 3 seeds`.
- The command prints final status.

- [ ] **Step 2: Inspect JSON invariants**

Run:

```bash
./.venv/bin/python - <<'PY'
import json
from pathlib import Path

path = Path("ML/reports/stage6_0_outcome_based_triple_barrier.json")
data = json.loads(path.read_text())
assert data["done_runs"] == data["total_runs"], (data["done_runs"], data["total_runs"])
assert data["total_runs"] == 6, data["total_runs"]
assert "preflight" in data
assert "oracle_preflight" in data
assert "raw_runs" in data and len(data["raw_runs"]) == 6
assert "gate" in data
print({
    "status": data.get("status"),
    "runs": data["done_runs"],
    "gate": data["gate"]["overall_status"],
})
PY
```

Expected: prints status/runs/gate without assertion error.

- [ ] **Step 3: If run fails, capture diagnostics before editing**

If the command fails, save:

```bash
./.venv/bin/python - <<'PY'
import json
from pathlib import Path
path = Path("ML/reports/stage6_0_outcome_based_triple_barrier.json")
if path.exists():
    data = json.loads(path.read_text())
    print("done_runs", data.get("done_runs"))
    print("total_runs", data.get("total_runs"))
    print("status", data.get("status"))
    print("last_error", data.get("last_error"))
else:
    print("json_missing")
PY
```

Then fix only the failing issue with a targeted test first.

- [ ] **Step 4: Commit JSON artifact**

```bash
git add ML/reports/stage6_0_outcome_based_triple_barrier.json
git commit -m "exp: run stage 6 outcome baseline"
```

---

### Task 10: Report, Handoff, Wiki, And Final Verification

**Files:**
- Create: `docs/reports/2026-06-29-stage6_0-outcome-based-triple-barrier-foundation.md`
- Modify: `CHANGELOG.md`
- Modify: `CONTEXT_HANDOFF.md`
- Modify: `wiki/research/fractal-stop-research.md` or create a focused outcome wiki page if the wiki skill recommends it.

**Interfaces:**
- Consumes: `ML/reports/stage6_0_outcome_based_triple_barrier.json`.
- Produces: human-readable result and updated baton pass.

- [ ] **Step 1: Read reporting skills**

Run:

```bash
sed -n '1,260p' .opencode/skills/my/stage-reporting/SKILL.md
sed -n '1,220p' .opencode/skills/my/wiki/SKILL.md
```

Expected: both files exist. If `.opencode/skills/...` is unavailable, use the equivalent `.claude/skills/my/...` files and record the path mismatch in the final answer.

- [ ] **Step 2: Write report from JSON, not memory**

Report must include:

- fixed target contract;
- why old `up_24/dn_24` shortcut is not enough;
- preflight class distribution;
- oracle/all-trade mechanics;
- model metrics by profile/seed;
- selected threshold and trading metrics on `val_stop`;
- threshold plateau check and threshold dispersion across seeds;
- random/permutation baseline for threshold PF;
- all-trade baseline without model scores;
- buy/sell metrics separately;
- spread stress metrics for 0.20 and 0.40;
- diagnostic holdout and low-N disclosure;
- timeout handling, including timeout PnL median, profitable-timeout rate, and total timeout PnL contribution;
- `risk_atr` and `reward_risk` distributions;
- execution limitations;
- final status and next step.

Minimum report conclusion rules:

- If preflight fails: conclude `PREFLIGHT_FAILED`; do not interpret model metrics.
- If model gate fails: conclude target is not learnable with current baseline features.
- If trading gate fails but AUC passes: conclude ranking exists but does not convert to executable rule.
- If validation trading gate passes: conclude `DIAGNOSTIC_SIGNAL_FOUND`, not candidate.

- [ ] **Step 3: Update handoff**

`CONTEXT_HANDOFF.md` must state:

- current Stage 6.0 status;
- what artifact/report to read;
- whether to continue outcome-based TB, redesign target, or move to regression Up/Dn;
- what not to do next.

- [ ] **Step 4: Update changelog**

Add one top entry with:

- files changed;
- run size;
- status;
- key numbers from JSON;
- next direction.

- [ ] **Step 5: Update wiki**

Run:

```bash
./.venv/bin/python wiki/wiki.py generate
./.venv/bin/python wiki/wiki.py status
```

Expected: `Wiki is up to date. No gaps found.`

- [ ] **Step 6: Run final verification**

Run:

```bash
./.venv/bin/python -m pytest tests/ -q
```

Expected: pass.

- [ ] **Step 7: Commit docs**

```bash
git add docs/reports/2026-06-29-stage6_0-outcome-based-triple-barrier-foundation.md CHANGELOG.md CONTEXT_HANDOFF.md wiki
git commit -m "docs: report stage 6 outcome baseline"
```

---

## Stop Conditions

Stop and report before training if any of these happen:

- More than 30% of rows are `INVALID` due to OHLC/time alignment.
- `train_core` or `val_stop` TP rate is below 5%.
- `train_core` or `val_stop` timeout rate is above 70%.
- Any Stage 6 target column appears in the feature matrix.
- First-touch tests disagree with expected TP/SL/TIMEOUT behavior.

Stop after training if:

- no threshold reaches minimum validation trades;
- selected threshold exists only in one validation year;
- validation PF is infinite because losses are zero and trades are below 50;
- holdout trade frequency collapses below 15 trades/year.

---

## Self-Review Checklist

- Stage 6.0 uses one fixed target protocol, not a broad search.
- Entry is `Open[row+1]`, not `Close[row]`.
- Timeout is a distinct outcome and has realized `pnl_r`.
- Same-bar ambiguity is conservative.
- Preflight and oracle happen before model interpretation.
- `2023-2025` and `2026` are not used for selection.
- JSON stores predictions/labels for post-mortem.
- Final status cannot become production/candidate without later execution parity.
