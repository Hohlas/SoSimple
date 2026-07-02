# Next Open Entry Up/Dn Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove or reject that `Regression Up/Dn` remains predictable when the target is redefined from the first реально исполнимой точки входа `next open after signal_time`, rather than from `fractal0_price`.

**Architecture:** Build one narrow foundation runner that reconstructs an entry-based target from OHLC, verifies the timing contract, trains the same baseline family on the new target, and reports only diagnostic predictive strength. The stage must separate target validity from trading usefulness: no `PF`, no `PnL`, no execution claims.

**Tech Stack:** Python 3.10+, pandas, numpy, scipy, existing baseline code in `ML/baseline/`, existing labeled CSV in `DATA/`, existing OHLC in `DATA/XAUUSD_H1_OHLC.csv`, existing `./.venv/bin/python`.

## Global Constraints

- Work on the current branch; do not use git worktree.
- Use `./.venv/bin/python` for every Python command.
- This stage is `DIAGNOSTIC_ONLY`.
- Do not use `up_h/dn_h` from `fractal0_price` as the trading target or as evidence for the new entry-based target.
- Define `decision_time`, `entry_time`, `entry_open`, label window, and allowed features before training any model.
- `entry_time` for this plan is fixed: first H1 `open` strictly after `signal_time`.
- Any additional delay beyond `signal_time` is out of scope for this plan.
- The new target must be measured from factual `entry_open`, not from idealized `fractal0_price`.
- Parse all labeled and OHLC times through the real project string format `%Y.%m.%d %H:%M`; fail fast on parse errors.
- Sort OHLC by parsed time, verify uniqueness, and resolve `entry_time` with `searchsorted` on the parsed time array.
- Primary interpretation split is `val_stop=2021-2022`.
- `diagnostic_holdout=2023-2025` and `low_n_disclosure=2026` are disclosure only.
- This is a fixed diagnostic model check, not a winner-selection cycle: freeze `structure_full` + `xgboost_depth3` + `seed=42`.
- Compare the new target against naive baselines before interpreting any ML gain.
- If the target contract cannot be reconstructed reliably from OHLC, stop with a failure verdict and do not train.
- If there is no stable predictive signal after factual entry, close this branch; do not rescue it with ad hoc filters or entry tweaks inside the same stage.
- Keep all new target columns out of features: `entry_up_*`, `entry_dn_*`, `entry_log_ratio_*`, coverage flags, and any legacy-denormalized disclosure columns.

---

## Research Contract

**Main question:** If we redefine `up_h/dn_h` from the first executable `entry_open` after `signal_time`, does any useful predictive relation remain?

**Definitions:**

- `signal_time`: top-level row time in the labeled dataset.
- `decision_time`: equal to `signal_time` for this stage.
- `entry_time`: first H1 bar open strictly after `signal_time`.
- `entry_open`: OHLC `open` at `entry_time`.
- `entry_up_h`: maximum favorable move in the window that starts at the `entry_time` bar open and includes exactly bars `entry_index ... entry_index + H - 1`, measured from `entry_open`.
- `entry_dn_h`: maximum adverse move in the same inclusive window, measured from `entry_open`.
- `entry_log_ratio_h`: `log1p(entry_up_h) - log1p(entry_dn_h)`.
- `legacy_up_h/dn_h`: old top-level target measured from `fractal0_price`; use only for comparison and disclosure, never as proof of the new branch.
- `legacy_up_h/dn_h` may be compared with the new target only after denormalization through `processing/denormalize_updn.py` and row-matched `*_updn_params.npy`, so both sides are in the same price-unit scale.

**Mandatory comparisons:**

1. Old target vs new target distribution shift, only after legacy denormalization into the same price-unit scale.
2. Old target predictive strength vs new target predictive strength.
3. Dummy/baseline quality on the new target.
4. ML prediction vs factual `entry_log_ratio_h` on `val_stop`.
5. Same metric on disclosure splits without winner selection.

**Stage verdicts:**

- `PASS_DIAGNOSTIC`: entry-based target reconstructed, audited, baseline reproduced, and report written.
- `ENTRY_CONTRACT_FAILED`: `signal_time -> entry_time -> entry_open -> next H bars` contract is not reliable enough.
- `TARGET_RECON_FAILED`: reconstructed `entry_up_h/dn_h` artifacts are incomplete or inconsistent.
- `MODEL_REPRO_FAILED`: baseline setup cannot be reproduced reliably enough to interpret results.
- `NO_SIGNAL_FOUND`: target is valid, but predictive relation after factual entry is not materially above dummy/baseline.

## File Structure

**Create**

- `ML/baseline/benchmark_next_open_entry_updn_foundation.py` - main diagnostic runner for the new target foundation.
- `tests/test_next_open_entry_updn_foundation.py` - focused tests for entry timing, target reconstruction, split safety, and summary metrics.
- `docs/reports/2026-07-02-next-open-entry-updn-foundation.md` - canonical stage report after execution.

**Modify**

- `processing/` files only if a small reusable helper is strictly needed for target reconstruction.
- `CHANGELOG.md`, `CONTEXT_HANDOFF.md`, `wiki/` only after the stage is complete and only if the verdict is final.

**Generated**

- `ML/reports/next_open_entry_updn_foundation.json`
- `ML/reports/next_open_entry_updn_rows.csv`
- optional plots only if they are generated by the runner and actually used in the report

**Rows CSV Required Columns**

- `split_name`
- source row `time`
- parsed `signal_time`
- `entry_time`
- `entry_index`
- `entry_open`
- `has_full_h3`, `has_full_h6`, `has_full_h12`
- `entry_up_3/dn_3`, `entry_up_6/dn_6`, `entry_up_12/dn_12`
- `entry_log_ratio_3`, `entry_log_ratio_6`, `entry_log_ratio_12`
- legacy-denormalized `up/dn` columns only for disclosure and comparison

**Read Before Implementation**

- `docs/methodology/00-research-management.md`
- `docs/methodology/04-labeling.md`
- `docs/methodology/06-temporal-split.md`
- `docs/methodology/07-baseline-first.md`
- `docs/methodology/11-robustness.md`
- `docs/reports/2026-06-30-regression-updn-target-foundation.md`
- `docs/reports/2026-07-01-regression-updn-ratio-audit.md`
- `docs/reports/2026-07-02-regression-updn-already-moved-audit.md`
- `ML/baseline/benchmark_regression_updn_target_foundation.py`
- `processing/label_signals.py`
- `processing/denormalize_updn.py`

---

### Task 1: Freeze The Entry Contract And Failing Tests

**Files:**
- Create: `tests/test_next_open_entry_updn_foundation.py`
- Create: `ML/baseline/benchmark_next_open_entry_updn_foundation.py`

**Interfaces:**
- Produces `NextOpenEntryConfig`.
- Produces `parse_project_time(value: object) -> pd.Timestamp`.
- Produces `resolve_entry_bar(signal_time: pd.Timestamp, ohlc_times: np.ndarray) -> int | None`.
- Produces `compute_entry_updn_from_ohlc(entry_index: int, horizon: int, highs: np.ndarray, lows: np.ndarray, entry_open: float) -> tuple[float, float]`.
- Produces `safe_log_ratio(up: np.ndarray, dn: np.ndarray) -> np.ndarray`.

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_next_open_entry_updn_foundation.py`:

```python
import numpy as np
import pandas as pd

import ML.baseline.benchmark_next_open_entry_updn_foundation as foundation


def test_parse_project_time_uses_real_dataset_format():
    parsed = foundation.parse_project_time("2019.06.20 16:00")

    assert parsed == pd.Timestamp("2019-06-20 16:00:00")


def test_resolve_entry_bar_uses_first_open_strictly_after_signal_time():
    ohlc_times = np.array(pd.to_datetime(
        ["2019-06-20 15:00", "2019-06-20 16:00", "2019-06-20 17:00", "2019-06-20 18:00"]
    ))

    assert foundation.resolve_entry_bar(pd.Timestamp("2019-06-20 16:00"), ohlc_times) == 2
    assert foundation.resolve_entry_bar(pd.Timestamp("2019-06-20 16:30"), ohlc_times) == 2
    assert foundation.resolve_entry_bar(pd.Timestamp("2019-06-20 18:00"), ohlc_times) is None


def test_compute_entry_updn_from_ohlc_measures_from_entry_open():
    highs = np.array([0.0, 0.0, 106.0, 107.5, 104.0])
    lows = np.array([0.0, 0.0, 99.5, 98.0, 101.0])

    up, dn = foundation.compute_entry_updn_from_ohlc(
        entry_index=2,
        horizon=2,
        highs=highs,
        lows=lows,
        entry_open=100.0,
    )

    assert up == 7.5
    assert dn == 2.0
```

- [ ] **Step 2: Run the test to verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_next_open_entry_updn_foundation.py -q
```

Expected: FAIL because the module does not exist yet.

- [ ] **Step 3: Write minimal implementation**

Create `ML/baseline/benchmark_next_open_entry_updn_foundation.py` with:

```python
import dataclasses
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORTS_DIR = PROJECT_ROOT / "ML" / "reports"


@dataclasses.dataclass(frozen=True)
class NextOpenEntryConfig:
    horizons: tuple[int, ...] = (3, 6, 12)
    primary_split: str = "val_stop"
    disclosure_splits: tuple[str, ...] = ("diagnostic_holdout", "low_n_disclosure")
    profile: str = "structure_full"
    model_key: str = "xgboost_depth3"
    seed: int = 42
    project_time_format: str = "%Y.%m.%d %H:%M"


def parse_project_time(value: object) -> pd.Timestamp:
    return pd.to_datetime(str(value), format=NextOpenEntryConfig().project_time_format, errors="raise")


def resolve_entry_bar(signal_time: pd.Timestamp, ohlc_times: np.ndarray) -> int | None:
    pos = int(ohlc_times.searchsorted(signal_time.to_datetime64(), side="right"))
    if pos >= len(ohlc_times):
        return None
    return pos


def compute_entry_updn_from_ohlc(
    entry_index: int,
    horizon: int,
    highs: np.ndarray,
    lows: np.ndarray,
    entry_open: float,
) -> tuple[float, float]:
    end = entry_index + horizon
    future_high = float(np.max(highs[entry_index:end]))
    future_low = float(np.min(lows[entry_index:end]))
    up = max(future_high - entry_open, 0.0)
    dn = max(entry_open - future_low, 0.0)
    return up, dn


def safe_log_ratio(up: np.ndarray, dn: np.ndarray) -> np.ndarray:
    return np.log1p(np.clip(up, 0.0, None)) - np.log1p(np.clip(dn, 0.0, None))
```

- [ ] **Step 4: Run the test to verify pass**

Run:

```bash
./.venv/bin/python -m pytest tests/test_next_open_entry_updn_foundation.py -q
```

Expected: PASS.

### Task 2: Reconstruct The Entry-Based Target And Audit Coverage

**Files:**
- Modify: `ML/baseline/benchmark_next_open_entry_updn_foundation.py`
- Modify: `tests/test_next_open_entry_updn_foundation.py`

**Interfaces:**
- Produces `load_ohlc() -> pd.DataFrame`.
- Produces `load_labeled_source(name: str) -> pd.DataFrame`.
- Produces `build_research_splits(...) -> dict[str, pd.DataFrame]`.
- Produces `rebuild_entry_targets(df: pd.DataFrame, ohlc: pd.DataFrame, horizons: tuple[int, ...]) -> pd.DataFrame`.
- Produces runner status `ENTRY_CONTRACT_FAILED` and `TARGET_RECON_FAILED`.

- [ ] **Step 1: Write failing reconstruction tests**

Extend `tests/test_next_open_entry_updn_foundation.py`:

```python
import pandas as pd


def test_rebuild_entry_targets_adds_entry_columns_for_each_horizon():
    df = pd.DataFrame(
        {
            "time": ["2019.06.20 15:30"],
            "fractal0": ["100:2000.0:1:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0"],
        }
    ).set_index(pd.Index([10]))
    ohlc = pd.DataFrame(
        {
            "time": ["2019.06.20 15:00", "2019.06.20 16:00", "2019.06.20 17:00", "2019.06.20 18:00"],
            "open": [10.0, 11.0, 12.0, 13.0],
            "high": [10.5, 12.5, 15.0, 14.0],
            "low": [9.5, 10.0, 11.5, 12.0],
        }
    )

    rebuilt = foundation.rebuild_entry_targets(df, ohlc, horizons=(1, 2))

    assert str(rebuilt.loc[10, "entry_time"]) == "2019-06-20 16:00:00"
    assert rebuilt.loc[10, "entry_open"] == 11.0
    assert rebuilt.loc[10, "entry_up_1"] == 1.5
    assert rebuilt.loc[10, "entry_dn_1"] == 1.0
    assert rebuilt.loc[10, "entry_up_2"] == 4.0
    assert rebuilt.loc[10, "entry_dn_2"] == 1.0
```

- [ ] **Step 2: Run the test to verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_next_open_entry_updn_foundation.py -q
```

Expected: FAIL because `rebuild_entry_targets` does not exist.

- [ ] **Step 3: Implement reconstruction**

Add to `ML/baseline/benchmark_next_open_entry_updn_foundation.py`:

```python
import pandas as pd
OHLC_PATH = PROJECT_ROOT / "DATA" / "XAUUSD_H1_OHLC.csv"
LABELED_PATHS = {
    "train": PROJECT_ROOT / "DATA" / "Nero_XAUUSD_train_labeled.csv",
    "validation": PROJECT_ROOT / "DATA" / "Nero_XAUUSD_validation_labeled.csv",
    "test": PROJECT_ROOT / "DATA" / "Nero_XAUUSD_test_labeled.csv",
}


def load_ohlc() -> pd.DataFrame:
    ohlc = pd.read_csv(OHLC_PATH, sep=";", usecols=["time", "open", "high", "low"])
    ohlc["parsed_time"] = ohlc["time"].map(parse_project_time)
    if ohlc["parsed_time"].isna().any():
        raise ValueError("OHLC time parse failed")
    ohlc = ohlc.sort_values("parsed_time").reset_index(drop=True)
    if not ohlc["parsed_time"].is_unique:
        raise ValueError("OHLC times are not unique")
    return ohlc


def load_labeled_source(name: str) -> pd.DataFrame:
    return pd.read_csv(LABELED_PATHS[name], sep=";")


def build_research_splits(train_df: pd.DataFrame, validation_df: pd.DataFrame, test_df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """
    Rebuild `train_core`, `val_stop`, `diagnostic_holdout`, `low_n_disclosure`
    from the real source CSVs using the same year-based logic as the old baseline.
    Do not treat a single file as a ready-made split without this explicit mapping.
    """


def rebuild_entry_targets(
    df: pd.DataFrame,
    ohlc: pd.DataFrame,
    horizons: tuple[int, ...],
) -> pd.DataFrame:
    ohlc_times = ohlc["parsed_time"].to_numpy()
    highs = ohlc["high"].to_numpy(dtype=float)
    lows = ohlc["low"].to_numpy(dtype=float)
    opens = ohlc["open"].to_numpy(dtype=float)
    out = df.copy()
    out["entry_time"] = pd.NA
    out["entry_open"] = np.nan
    out["entry_index"] = pd.NA

    for horizon in horizons:
        out[f"entry_up_{horizon}"] = np.nan
        out[f"entry_dn_{horizon}"] = np.nan
        out[f"has_full_h{horizon}"] = False

    for row_index, signal_raw in out["time"].items():
        signal_time = parse_project_time(signal_raw)
        entry_idx = resolve_entry_bar(signal_time=signal_time, ohlc_times=ohlc_times)
        if entry_idx is None:
            continue
        out.at[row_index, "entry_time"] = pd.Timestamp(ohlc_times[entry_idx])
        out.at[row_index, "entry_open"] = float(opens[entry_idx])
        out.at[row_index, "entry_index"] = int(entry_idx)
        for horizon in horizons:
            if entry_idx + horizon > len(ohlc):
                continue
            out.at[row_index, f"has_full_h{horizon}"] = True
            up, dn = compute_entry_updn_from_ohlc(
                entry_index=entry_idx,
                horizon=horizon,
                highs=highs,
                lows=lows,
                entry_open=float(opens[entry_idx]),
            )
            out.at[row_index, f"entry_up_{horizon}"] = up
            out.at[row_index, f"entry_dn_{horizon}"] = dn
    return out
```

- [ ] **Step 4: Run the test to verify pass**

Run:

```bash
./.venv/bin/python -m pytest tests/test_next_open_entry_updn_foundation.py -q
```

Expected: PASS.

### Task 3: Build The Foundation Runner With Dummy Baselines

**Files:**
- Modify: `ML/baseline/benchmark_next_open_entry_updn_foundation.py`
- Modify: `tests/test_next_open_entry_updn_foundation.py`

**Interfaces:**
- Produces `run_next_open_entry_foundation() -> dict`.
- Produces JSON artifact `ML/reports/next_open_entry_updn_foundation.json`.
- Produces row artifact `ML/reports/next_open_entry_updn_rows.csv`.

- [ ] **Step 1: Write failing summary test**

Extend `tests/test_next_open_entry_updn_foundation.py`:

```python
def test_validate_summary_rejects_missing_required_fields():
    summary = {"status": "PASS_DIAGNOSTIC"}

    missing = foundation.validate_summary(summary)

    assert "target_contract" in missing
    assert "primary_split" in missing
    assert "horizons" in missing
```

- [ ] **Step 2: Run the test to verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_next_open_entry_updn_foundation.py -q
```

Expected: FAIL because `validate_summary` does not exist yet.

- [ ] **Step 3: Implement the runner**

In `ML/baseline/benchmark_next_open_entry_updn_foundation.py`, implement:

```python
def validate_summary(summary: dict) -> list[str]:
    required = [
        "status",
        "target_contract",
        "decision_time",
        "entry_rule",
        "horizons",
        "primary_split",
        "disclosure_splits",
        "coverage",
        "dummy_metrics",
        "model_metrics",
    ]
    return [key for key in required if key not in summary]


def run_next_open_entry_foundation() -> dict:
    """
    1. Load `train`, `validation`, `test`, then rebuild `train_core`, `val_stop`,
       `diagnostic_holdout`, `low_n_disclosure` with the same year logic as the old baseline.
    2. Rebuild `entry_up_h/entry_dn_h` for H3/H6/H12.
    3. Run preflight:
       - all times parsed
       - OHLC sorted and unique
       - entry_match_rate
       - H1 gap count
       - rows without full H3/H6/H12 window
    4. Denormalize legacy `up/dn` only for disclosure comparison.
    4. Compute dummy metrics for `entry_log_ratio_h`:
       - constant-zero predictor
       - train-median predictor
       - simple direction heuristic if already present in existing baseline code
    5. Train the same fixed diagnostic model as the old `Regression Up/Dn target foundation`.
    6. Compare ML vs dummy on `val_stop`, then disclose the other splits.
    7. Write JSON + rows CSV.
    """
```

Minimum required JSON fields:

```python
{
    "status": "PASS_DIAGNOSTIC",
    "target_contract": "next_open_after_signal_time",
    "decision_time": "signal_time",
    "entry_rule": "first_open_strictly_after_signal_time",
    "horizons": [3, 6, 12],
    "primary_split": "val_stop",
    "disclosure_splits": ["diagnostic_holdout", "low_n_disclosure"],
    "target_scale": "price_units_from_entry_open",
    "coverage": {},
    "preflight": {},
    "distribution_shift_vs_legacy": {},
    "dummy_metrics": {},
    "model_metrics": {},
}
```

- [ ] **Step 4: Run the tests to verify pass**

Run:

```bash
./.venv/bin/python -m pytest tests/test_next_open_entry_updn_foundation.py -q
```

Expected: PASS.

### Task 4: Run The Stage And Write The Report

**Files:**
- Modify: `docs/reports/2026-07-02-next-open-entry-updn-foundation.md`
- Read: `ML/reports/next_open_entry_updn_foundation.json`
- Read: `ML/reports/next_open_entry_updn_rows.csv`

**Interfaces:**
- Consumes `run_next_open_entry_foundation()` artifacts.
- Produces canonical report and final verdict.

- [ ] **Step 1: Run the stage**

Run:

```bash
./.venv/bin/python ML/baseline/benchmark_next_open_entry_updn_foundation.py
```

Expected: JSON and CSV artifacts written to `ML/reports/`.

- [ ] **Step 2: Verify outputs exist and are readable**

Run:

```bash
./.venv/bin/python -m pytest tests/test_next_open_entry_updn_foundation.py -q
```

Expected: PASS.

- [ ] **Step 3: Write the report**

Create `docs/reports/2026-07-02-next-open-entry-updn-foundation.md` with these mandatory sections:

```md
# Next Open Entry Up/Dn Foundation

> **Дата**: 2026-07-02
> **Статус**: Completed
> **Вердикт**: `DIAGNOSTIC_ONLY`
> **Итоговый статус runner**: `...`
> **Цель**: Проверить, существует ли предсказуемость `up_h/dn_h`, если движение считается от первого реально исполнимого `open` после `signal_time`.

## Context
## Method
## Preflight
## Results
## Interpretation
## Stop Condition
## Limitations
## Next Step
## Related Materials
```
```

Required conclusions:

- whether the new target contract is technically valid;
- whether target distributions materially changed vs legacy `fractal0_price` target;
- whether ML beats dummy in a stable enough way on `val_stop`;
- whether disclosure splits support or weaken the interpretation;
- whether this branch stays alive or is closed with `NO_SIGNAL_FOUND`;
- that the result closes or keeps open only the `next open` branch and does not decide the separate `fractal0_price` zone branch.

- [ ] **Step 4: Prepare stage-close sync only after final verdict**

Do not add intermediate commits inside this plan. In SoSimple, commit and final sync belong to stage closing after the stage verdict is complete.

### Task 5: Close Or Escalate The Branch

**Files:**
- Modify only if the stage verdict is final: `CHANGELOG.md`, `CONTEXT_HANDOFF.md`, `wiki/index.md`, `wiki/log.md`, `wiki/research/fractal-stop-research.md`

**Interfaces:**
- Consumes final report verdict.
- Produces synchronized project memory.

- [ ] **Step 1: Decide branch outcome**

Use this rule:

```text
If target contract failed -> stop with ENTRY_CONTRACT_FAILED or TARGET_RECON_FAILED.
If target is valid but ML does not beat dummy materially/stably -> stop with NO_SIGNAL_FOUND.
If target is valid and ML shows stable predictive relation -> keep branch open for next plan.
```

- [ ] **Step 2: Sync project memory only after final verdict**

Run the usual stage-close updates:

```bash
./.venv/bin/python wiki/wiki.py generate
```

Then update the canonical docs mentioned above.

## Self-Review

- Spec coverage: the plan covers the frozen `next open after signal_time` contract, reconstruction of factual entry-based targets, dummy-first evaluation, narrow baseline training, canonical reporting, and branch close criteria.
- Placeholder scan: no `TODO`/`TBD` markers remain; every task has explicit files, commands, and expected outputs.
- Type consistency: `resolve_entry_bar`, `compute_entry_updn_from_ohlc`, `rebuild_entry_targets`, and `run_next_open_entry_foundation` are introduced before later tasks rely on them.

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-07-02-next-open-entry-updn-foundation.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
