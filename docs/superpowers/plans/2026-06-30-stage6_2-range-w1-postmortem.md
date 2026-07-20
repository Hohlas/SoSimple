# Stage 6.2 Range W1 Post-Mortem Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Explain why `range_w1_atr` dominates Stage 6.2 price-action importance and why the stability check remains weak, without turning the analysis into a new model search.

**Architecture:** Add a bounded diagnostic script that reads the existing Stage 6.2 JSON and labeled/OHLC inputs, rebuilds only the already frozen Stage 6.2 price-action features, and writes one post-mortem JSON plus one short report. The analysis is descriptive: feature distribution, relation to outcome, relation to selected trades, seed disagreement, period drift, and simple sanity checks against leakage-like artifacts.

**Tech Stack:** Python 3.10+, pandas, numpy, scipy optional only if already installed, pytest, existing `./.venv/bin/python`, existing `ML/reports/stage6_2_h12_price_action_feature_family.json`, existing `DATA/Nero_XAUUSD_*_labeled.csv`, existing `DATA/XAUUSD_H1_OHLC.csv`.

## Global Constraints

- Work on the current branch; do not use git worktree.
- Use `./.venv/bin/python` for all Python commands.
- Do not retrain Stage 6.2 models.
- Do not add a new feature family, horizon, ATR, TP/SL, spread, threshold, seed, or profile search.
- Do not promote Stage 6.2 to candidate; this plan can only produce `DIAGNOSTIC_ONLY` conclusions.
- Use the existing Stage 6.2 JSON as the model result source of truth.
- Use `val_stop` (`2021-2022`) for explaining the failed gate; use `diagnostic_holdout` (`2023-2025`) and `low_n_disclosure` (`2026`) only as disclosure.
- Treat `2026` price-action disclosure as weak because many rows have zero-vector price-action features.
- If any finding suggests a new feature idea, record it as a hypothesis only; do not test it inside this plan.
- After this post-mortem is closed, the next roadmap direction is `Regression Up/Dn target foundation`, not another small variant of Stage 6.2 OHLC windows.

---

## Fixed Diagnostic Questions

This plan answers only these questions:

1. Is `range_w1_atr` dominant because it has a real relation to `stage6_definitive_tp_vs_sl_flag`, or because it proxies a data artifact?
2. Does `range_w1_atr` behave similarly across seeds, years, directions, and selected thresholds?
3. Does `range_w1_atr` mostly separate TP from SL, or mostly separate easy/high-activity rows from sparse/noisy rows?
4. Why does the model show weak ranking signal while the permutation check remains above the required limit?
5. Is there enough evidence to justify another OHLC-family plan, or should the project move to `Regression Up/Dn target foundation`?

## File Structure

**Create**

- `ML/baseline/analyze_stage6_2_range_w1_postmortem.py` - bounded post-mortem script.
- `tests/test_stage6_2_range_w1_postmortem.py` - focused tests for analysis helpers and JSON/report shape.
- `docs/reports/2026-06-30-stage6_2-range-w1-postmortem.md` - final human-readable post-mortem.
- `ML/reports/stage6_2_range_w1_postmortem.json` - generated diagnostic artifact.

**Modify after execution**

- `CONTEXT_HANDOFF.md` - record that Stage 6.2 post-mortem is closed and next step is `Regression Up/Dn target foundation`.
- `CHANGELOG.md` - one short entry with verdict.
- `wiki/research/fractal-stop-research.md`, `wiki/index.md`, `wiki/log.md`, `wiki/REPO_integrity.md` - ingest the post-mortem result.

**Read before implementation**

- `docs/methodology/05-eda-data-quality.md`
- `docs/methodology/11-robustness.md`
- `docs/methodology/16-reporting-audit.md`
- `docs/reports/2026-06-30-stage6_2-h12-price-action-feature-family.md`
- `ML/baseline/benchmark_stage6_2_price_action.py`
- `ML/baseline/benchmark_stage6_outcome_based.py`

---

### Task 1: Analysis Contract And Pure Helpers

**Files:**
- Create: `ML/baseline/analyze_stage6_2_range_w1_postmortem.py`
- Create: `tests/test_stage6_2_range_w1_postmortem.py`

**Interfaces:**
- Produces:
  - `POSTMORTEM_JSON_PATH: Path`
  - `POSTMORTEM_REPORT_PATH: Path`
  - `bucketize_quantiles(values: pd.Series, n_bins: int = 5) -> pd.Series`
  - `safe_corr(a: pd.Series, b: pd.Series) -> float | None`
  - `summarize_binary_by_bucket(df: pd.DataFrame, bucket_col: str, target_col: str) -> list[dict]`
  - `summarize_numeric_by_period(df: pd.DataFrame, value_col: str, time_col: str = "time") -> list[dict]`

- [ ] **Step 1: Write failing helper tests**

Create `tests/test_stage6_2_range_w1_postmortem.py`:

```python
import math

import pandas as pd

import ML.baseline.analyze_stage6_2_range_w1_postmortem as pm


def test_bucketize_quantiles_is_stable_with_duplicate_values():
    values = pd.Series([1.0, 1.0, 2.0, 3.0, 4.0, 4.0])

    buckets = pm.bucketize_quantiles(values, n_bins=3)

    assert len(buckets) == 6
    assert buckets.isna().sum() == 0
    assert set(buckets.astype(str)).issubset({"q1", "q2", "q3"})


def test_safe_corr_returns_none_for_constant_input():
    assert pm.safe_corr(pd.Series([1.0, 1.0, 1.0]), pd.Series([0.0, 1.0, 0.0])) is None


def test_safe_corr_returns_float_for_varying_input():
    value = pm.safe_corr(pd.Series([1.0, 2.0, 3.0]), pd.Series([0.0, 0.5, 1.0]))

    assert value is not None
    assert math.isclose(value, 1.0)


def test_summarize_binary_by_bucket_counts_and_rates():
    df = pd.DataFrame({
        "bucket": ["q1", "q1", "q2", "q2"],
        "target": [0, 1, 1, 1],
    })

    rows = pm.summarize_binary_by_bucket(df, "bucket", "target")

    assert rows == [
        {"bucket": "q1", "n": 2, "positive_rate": 0.5},
        {"bucket": "q2", "n": 2, "positive_rate": 1.0},
    ]


def test_summarize_numeric_by_period_uses_calendar_year():
    df = pd.DataFrame({
        "time": ["2021.01.01 00:00", "2021.06.01 00:00", "2022.01.01 00:00"],
        "value": [1.0, 3.0, 5.0],
    })

    rows = pm.summarize_numeric_by_period(df, "value")

    assert rows == [
        {"year": 2021, "n": 2, "mean": 2.0, "median": 2.0},
        {"year": 2022, "n": 1, "mean": 5.0, "median": 5.0},
    ]
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage6_2_range_w1_postmortem.py -q
```

Expected: fail because `ML.baseline.analyze_stage6_2_range_w1_postmortem` does not exist.

- [ ] **Step 3: Implement minimal helper module**

Create `ML/baseline/analyze_stage6_2_range_w1_postmortem.py` with:

```python
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE62_JSON_PATH = REPO_ROOT / "ML/reports/stage6_2_h12_price_action_feature_family.json"
POSTMORTEM_JSON_PATH = REPO_ROOT / "ML/reports/stage6_2_range_w1_postmortem.json"
POSTMORTEM_REPORT_PATH = REPO_ROOT / "docs/reports/2026-06-30-stage6_2-range-w1-postmortem.md"


def bucketize_quantiles(values: pd.Series, n_bins: int = 5) -> pd.Series:
    numeric = pd.to_numeric(values, errors="coerce")
    if numeric.notna().sum() == 0:
        return pd.Series(["missing"] * len(values), index=values.index, dtype="object")
    ranked = numeric.rank(method="first")
    bins = pd.qcut(ranked, q=min(n_bins, int(ranked.notna().sum())), labels=False, duplicates="drop")
    out = bins.astype("Int64").astype("object")
    out = out.where(out.isna(), out.map(lambda x: f"q{int(x) + 1}"))
    return out.fillna("missing").astype(str)


def safe_corr(a: pd.Series, b: pd.Series) -> float | None:
    left = pd.to_numeric(a, errors="coerce")
    right = pd.to_numeric(b, errors="coerce")
    mask = left.notna() & right.notna()
    if int(mask.sum()) < 3:
        return None
    left = left[mask]
    right = right[mask]
    if float(left.std(ddof=0)) == 0.0 or float(right.std(ddof=0)) == 0.0:
        return None
    return float(left.corr(right))


def summarize_binary_by_bucket(df: pd.DataFrame, bucket_col: str, target_col: str) -> list[dict]:
    rows: list[dict] = []
    for bucket, group in df.groupby(bucket_col, sort=True, dropna=False):
        target = pd.to_numeric(group[target_col], errors="coerce").dropna()
        rows.append({
            "bucket": str(bucket),
            "n": int(len(target)),
            "positive_rate": float(target.mean()) if len(target) else None,
        })
    return rows


def summarize_numeric_by_period(
    df: pd.DataFrame,
    value_col: str,
    time_col: str = "time",
) -> list[dict]:
    work = df[[time_col, value_col]].copy()
    work["year"] = pd.to_datetime(work[time_col], format="%Y.%m.%d %H:%M", errors="coerce").dt.year
    work[value_col] = pd.to_numeric(work[value_col], errors="coerce")
    work = work.dropna(subset=["year", value_col])
    rows: list[dict] = []
    for year, group in work.groupby("year", sort=True):
        values = group[value_col]
        rows.append({
            "year": int(year),
            "n": int(len(values)),
            "mean": float(values.mean()),
            "median": float(values.median()),
        })
    return rows
```

- [ ] **Step 4: Run focused tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage6_2_range_w1_postmortem.py -q
```

Expected: all tests pass.

- [ ] **Step 5: Checkpoint diff review**

Run:

```bash
git diff -- ML/baseline/analyze_stage6_2_range_w1_postmortem.py tests/test_stage6_2_range_w1_postmortem.py
```

Expected: diff contains only Task 1 helper code and tests. Do not commit here; final commit is done only during stage closure via `stage-reporting`.

---

### Task 2: Rebuild Frozen Diagnostic Frame

**Files:**
- Modify: `ML/baseline/analyze_stage6_2_range_w1_postmortem.py`
- Modify: `tests/test_stage6_2_range_w1_postmortem.py`

**Interfaces:**
- Consumes:
  - `bucketize_quantiles`
  - Stage 6.2 functions from `ML/baseline/benchmark_stage6_2_price_action.py`
- Produces:
  - `build_diagnostic_frame(split: dict[str, pd.DataFrame], ohlc: pd.DataFrame, split_name: str) -> pd.DataFrame`
  - columns: `time`, `split`, `ATR`, `stage6_side`, `stage6_definitive_tp_vs_sl_flag`, `stage6_pnl_r`, `range_w1_atr`, `range_w1_bucket`, `close_to_high_w1_atr`, `close_to_low_w1_atr`, `bar_range_1_atr`, `price_action_zero_vector`

- [ ] **Step 1: Write failing frame test**

Append to `tests/test_stage6_2_range_w1_postmortem.py`:

```python
def test_build_diagnostic_frame_marks_zero_vector_rows():
    split = {
        "val_stop": pd.DataFrame({
            "time": ["2021.01.01 00:00", "2021.01.01 01:00"],
            "ATR": [2.0, 2.0],
            "stage6_side": ["buy", "sell"],
            "stage6_definitive_tp_vs_sl_flag": [1, 0],
            "stage6_pnl_r": [1.5, -1.0],
        })
    }
    ohlc = pd.DataFrame({
        "time": pd.to_datetime(["2021.01.01 00:00"]),
        "open": [100.0],
        "high": [103.0],
        "low": [99.0],
        "close": [102.0],
        "volume": [10.0],
        "atr14": [2.0],
    })

    frame = pm.build_diagnostic_frame(split, ohlc, "val_stop")

    assert list(frame["split"]) == ["val_stop", "val_stop"]
    assert frame.loc[0, "range_w1_atr"] == 2.0
    assert not bool(frame.loc[0, "price_action_zero_vector"])
    assert bool(frame.loc[1, "price_action_zero_vector"])
    assert frame.loc[1, "range_w1_atr"] == 0.0
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage6_2_range_w1_postmortem.py::test_build_diagnostic_frame_marks_zero_vector_rows -q
```

Expected: fail because `build_diagnostic_frame` is missing.

- [ ] **Step 3: Implement frame builder**

Add imports and function to `ML/baseline/analyze_stage6_2_range_w1_postmortem.py`:

```python
from ML.baseline.benchmark_stage6_2_price_action import (
    stage62_build_price_action_features,
    stage62_price_action_feature_names,
)


def build_diagnostic_frame(
    split: dict[str, pd.DataFrame],
    ohlc: pd.DataFrame,
    split_name: str,
) -> pd.DataFrame:
    df = split[split_name].reset_index(drop=True).copy()
    feature_names = stage62_price_action_feature_names("h12_price_action_core")
    features = stage62_build_price_action_features(df, "h12_price_action_core", ohlc=ohlc)
    feature_df = pd.DataFrame(features, columns=feature_names)
    out = pd.concat([df.reset_index(drop=True), feature_df], axis=1)
    out["split"] = split_name
    out["price_action_zero_vector"] = (feature_df.abs().sum(axis=1) == 0.0)
    out["range_w1_bucket"] = bucketize_quantiles(out["range_w1_atr"], n_bins=5)
    keep = [
        "time",
        "split",
        "ATR",
        "stage6_side",
        "stage6_definitive_tp_vs_sl_flag",
        "stage6_pnl_r",
        "range_w1_atr",
        "range_w1_bucket",
        "close_to_high_w1_atr",
        "close_to_low_w1_atr",
        "bar_range_1_atr",
        "price_action_zero_vector",
    ]
    for col in keep:
        if col not in out.columns:
            out[col] = np.nan
    return out[keep]
```

- [ ] **Step 4: Run focused tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage6_2_range_w1_postmortem.py -q
```

Expected: all tests pass.

- [ ] **Step 5: Checkpoint diff review**

Run:

```bash
git diff -- ML/baseline/analyze_stage6_2_range_w1_postmortem.py tests/test_stage6_2_range_w1_postmortem.py
```

Expected: diff contains only Task 2 frame-builder changes. Do not commit here; final commit is done only during stage closure via `stage-reporting`.

---

### Task 3: Explain Dominance And Weak Stability

**Files:**
- Modify: `ML/baseline/analyze_stage6_2_range_w1_postmortem.py`
- Modify: `tests/test_stage6_2_range_w1_postmortem.py`

**Interfaces:**
- Consumes:
  - `build_diagnostic_frame`
  - Stage 6.2 JSON `raw_runs`, `summary`, `gate`
- Produces:
  - `build_postmortem(stage62_report: dict, frames: dict[str, pd.DataFrame]) -> dict`
  - `attach_core_seed_scores(stage62_report: dict, frame: pd.DataFrame) -> pd.DataFrame`
  - JSON sections: `artifact_consistency`, `dominance`, `selected_trade_analysis`, `side_analysis`, `year_side_matrix`, `activity_proxy_checks`, `permutation_context`, `evidence_strength`, `verdict`

- [ ] **Step 1: Write failing post-mortem shape test**

Append to `tests/test_stage6_2_range_w1_postmortem.py`:

```python
def test_build_postmortem_reports_dominance_and_stability_shape():
    report = {
        "summary": {
            "h12_price_action_core": {
                "top_feature_importance": [
                    {"feature": "range_w1_atr", "auc_drop": 0.0525},
                    {"feature": "close_to_low_w1_atr", "auc_drop": 0.0069},
                ],
                "seed_runs": [
                    {"seed": 42, "val_auc": 0.6233, "permutation_p_value": 0.160, "threshold": 0.700, "pf": 1.307},
                    {"seed": 77, "val_auc": 0.6213, "permutation_p_value": 0.350, "threshold": 0.725, "pf": 1.180},
                    {"seed": 123, "val_auc": 0.6238, "permutation_p_value": 0.155, "threshold": 0.725, "pf": 1.359},
                ],
                "permutation_baseline": {
                    "empirical_p_value": 0.16,
                    "observed_pf_median": 1.307,
                    "per_seed": [
                        {"seed": 42, "observed_pf": 1.307, "permuted_pf_median": 1.100, "permuted_pf_p95": 1.420},
                        {"seed": 77, "observed_pf": 1.180, "permuted_pf_median": 1.080, "permuted_pf_p95": 1.390},
                        {"seed": 123, "observed_pf": 1.359, "permuted_pf_median": 1.120, "permuted_pf_p95": 1.460},
                    ],
                },
            }
        },
        "gate": {"status": "TRADING_GATE_FAILED"},
    }
    frame = pd.DataFrame({
        "time": ["2021.01.01 00:00", "2021.01.01 01:00", "2022.01.01 00:00"],
        "stage6_side": ["buy", "buy", "sell"],
        "stage6_definitive_tp_vs_sl_flag": [0, 1, 1],
        "stage6_pnl_r": [-1.0, 2.0, 1.5],
        "range_w1_atr": [0.5, 2.0, 3.0],
        "range_w1_bucket": ["q1", "q2", "q3"],
        "bar_range_1_atr": [0.5, 2.0, 3.0],
        "ATR": [1.0, 2.0, 3.0],
        "y_score_core_seed42": [0.65, 0.72, 0.80],
        "price_action_zero_vector": [False, False, False],
    })

    result = pm.build_postmortem(report, {"val_stop": frame})

    assert result["source_stage62_status"] == "TRADING_GATE_FAILED"
    assert result["artifact_consistency"]["primary_p_value"] == 0.16
    assert result["dominance"]["top_feature"] == "range_w1_atr"
    assert result["dominance"]["top_to_second_auc_drop_ratio"] > 1.0
    assert result["stability"]["seed_count"] == 3
    assert result["selected_trade_analysis"]["seed_count"] == 3
    assert result["side_analysis"][0]["side"] in {"buy", "sell"}
    assert result["year_side_matrix"][0]["year"] in {2021, 2022}
    assert "range_w1_vs_bar_range_1_corr" in result["activity_proxy_checks"]
    assert result["permutation_context"]["primary_p_value"] == 0.16
    assert result["evidence_strength"] in {"weak", "insufficient", "artifact_suspected", "not_artifact_detected"}
    assert result["verdict"]["artifact_status"] == "DIAGNOSTIC_ONLY"
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage6_2_range_w1_postmortem.py::test_build_postmortem_reports_dominance_and_stability_shape -q
```

Expected: fail because `build_postmortem` is missing.

- [ ] **Step 3: Implement post-mortem builder**

Add to `ML/baseline/analyze_stage6_2_range_w1_postmortem.py`:

```python
def _top_importance_ratio(items: list[dict]) -> float | None:
    if len(items) < 2:
        return None
    first = float(items[0].get("auc_drop", items[0].get("auc_drop_mean", 0.0)) or 0.0)
    second = float(items[1].get("auc_drop", items[1].get("auc_drop_mean", 0.0)) or 0.0)
    if second == 0.0:
        return None
    return float(first / second)


def _mean_or_none(values: pd.Series) -> float | None:
    values = pd.to_numeric(values, errors="coerce").dropna()
    return float(values.mean()) if len(values) else None


def _summarize_group(df: pd.DataFrame, group_cols: list[str]) -> list[dict]:
    work = df.copy()
    work["year"] = pd.to_datetime(work["time"], format="%Y.%m.%d %H:%M", errors="coerce").dt.year
    rows: list[dict] = []
    for keys, group in work.dropna(subset=group_cols).groupby(group_cols, sort=True):
        if not isinstance(keys, tuple):
            keys = (keys,)
        row = {col: int(val) if col == "year" else str(val) for col, val in zip(group_cols, keys)}
        row.update({
            "n": int(len(group)),
            "tp_rate": _mean_or_none(group["stage6_definitive_tp_vs_sl_flag"]),
            "mean_pnl_r": _mean_or_none(group["stage6_pnl_r"]),
            "range_w1_target_corr": safe_corr(group["range_w1_atr"], group["stage6_definitive_tp_vs_sl_flag"]),
            "range_w1_pnl_corr": safe_corr(group["range_w1_atr"], group["stage6_pnl_r"]),
        })
        rows.append(row)
    return rows


def _seed_stability(seed_runs: list[dict]) -> dict:
    p_values = [float(row["permutation_p_value"]) for row in seed_runs if row.get("permutation_p_value") is not None]
    auc_values = [float(row["val_auc"]) for row in seed_runs if row.get("val_auc") is not None]
    return {
        "seed_count": int(len(seed_runs)),
        "permutation_p_value_min": float(min(p_values)) if p_values else None,
        "permutation_p_value_max": float(max(p_values)) if p_values else None,
        "permutation_p_value_spread": float(max(p_values) - min(p_values)) if p_values else None,
        "val_auc_min": float(min(auc_values)) if auc_values else None,
        "val_auc_max": float(max(auc_values)) if auc_values else None,
        "val_auc_spread": float(max(auc_values) - min(auc_values)) if auc_values else None,
    }


def _selected_trade_analysis(df: pd.DataFrame, seed_runs: list[dict]) -> dict:
    rows: list[dict] = []
    for run in seed_runs:
        seed = int(run["seed"])
        score_col = f"y_score_core_seed{seed}"
        threshold = run.get("threshold")
        if score_col not in df.columns or threshold is None:
            continue
        selected = df[pd.to_numeric(df[score_col], errors="coerce") >= float(threshold)]
        non_selected = df[pd.to_numeric(df[score_col], errors="coerce") < float(threshold)]
        rows.append({
            "seed": seed,
            "threshold": float(threshold),
            "selected_n": int(len(selected)),
            "non_selected_n": int(len(non_selected)),
            "selected_tp_rate": _mean_or_none(selected["stage6_definitive_tp_vs_sl_flag"]),
            "non_selected_tp_rate": _mean_or_none(non_selected["stage6_definitive_tp_vs_sl_flag"]),
            "selected_mean_pnl_r": _mean_or_none(selected["stage6_pnl_r"]),
            "non_selected_mean_pnl_r": _mean_or_none(non_selected["stage6_pnl_r"]),
            "selected_bucket_target_rates": summarize_binary_by_bucket(
                selected,
                "range_w1_bucket",
                "stage6_definitive_tp_vs_sl_flag",
            ),
        })
    return {"seed_count": int(len(seed_runs)), "available_seed_count": int(len(rows)), "per_seed": rows}


def _permutation_context(primary: dict) -> dict:
    baseline = primary.get("permutation_baseline", {})
    per_seed = []
    for row in baseline.get("per_seed", []):
        observed = row.get("observed_pf")
        p95 = row.get("permuted_pf_p95")
        per_seed.append({
            "seed": row.get("seed"),
            "observed_pf": observed,
            "permuted_pf_median": row.get("permuted_pf_median"),
            "permuted_pf_p95": p95,
            "observed_minus_permuted_p95": (
                float(observed) - float(p95)
                if observed is not None and p95 is not None
                else None
            ),
        })
    return {
        "primary_p_value": baseline.get("empirical_p_value"),
        "required_p_value": 0.10,
        "observed_pf_median": baseline.get("observed_pf_median"),
        "per_seed": per_seed,
    }


def attach_core_seed_scores(stage62_report: dict, frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    for run in stage62_report.get("raw_runs", []):
        if run.get("profile") != "h12_price_action_core":
            continue
        seed = int(run["seed"])
        scores = run.get("predictions", {}).get("val_stop", {}).get("y_score_all", [])
        if len(scores) == len(out):
            out[f"y_score_core_seed{seed}"] = pd.to_numeric(pd.Series(scores), errors="coerce")
    return out


def _evidence_strength(post: dict) -> str:
    p_value = post["permutation_context"]["primary_p_value"]
    side_rows = post["side_analysis"]
    if p_value is None:
        return "insufficient"
    if float(p_value) > 0.10:
        return "weak"
    if any(row.get("range_w1_target_corr") is None for row in side_rows):
        return "insufficient"
    return "not_artifact_detected"


def build_postmortem(stage62_report: dict, frames: dict[str, pd.DataFrame]) -> dict:
    primary = stage62_report["summary"]["h12_price_action_core"]
    importance = primary.get("top_feature_importance", [])
    seed_runs = primary.get("seed_runs", [])
    val_frame = attach_core_seed_scores(stage62_report, frames["val_stop"])
    non_zero_val = val_frame[~val_frame["price_action_zero_vector"].astype(bool)].copy()

    post = {
        "source_stage62_status": stage62_report.get("gate", {}).get("status", stage62_report.get("status")),
        "artifact_consistency": {
            "primary_profile": "h12_price_action_core",
            "primary_p_value": primary.get("permutation_baseline", {}).get("empirical_p_value"),
            "top_feature_from_stage62_json": importance[0]["feature"] if importance else None,
            "gate_status_from_stage62_json": stage62_report.get("gate", {}).get("status", stage62_report.get("status")),
        },
        "dominance": {
            "top_feature": importance[0]["feature"] if importance else None,
            "top_to_second_auc_drop_ratio": _top_importance_ratio(importance),
            "range_w1_target_corr": safe_corr(
                non_zero_val["range_w1_atr"],
                non_zero_val["stage6_definitive_tp_vs_sl_flag"],
            ),
            "range_w1_pnl_corr": safe_corr(non_zero_val["range_w1_atr"], non_zero_val["stage6_pnl_r"]),
            "bucket_target_rates": summarize_binary_by_bucket(
                non_zero_val,
                "range_w1_bucket",
                "stage6_definitive_tp_vs_sl_flag",
            ),
            "yearly_range_w1": summarize_numeric_by_period(non_zero_val, "range_w1_atr"),
            "zero_vector_rows": int(val_frame["price_action_zero_vector"].sum()),
            "rows": int(len(val_frame)),
        },
        "stability": _seed_stability(seed_runs),
        "selected_trade_analysis": _selected_trade_analysis(non_zero_val, seed_runs),
        "side_analysis": _summarize_group(non_zero_val, ["stage6_side"]),
        "year_side_matrix": _summarize_group(non_zero_val, ["year", "stage6_side"]),
        "activity_proxy_checks": {
            "range_w1_vs_atr_corr": safe_corr(non_zero_val["range_w1_atr"], non_zero_val["ATR"]) if "ATR" in non_zero_val.columns else None,
            "range_w1_vs_bar_range_1_corr": safe_corr(non_zero_val["range_w1_atr"], non_zero_val["bar_range_1_atr"]),
            "range_w1_by_year": summarize_numeric_by_period(non_zero_val, "range_w1_atr"),
            "zero_vector_share": float(val_frame["price_action_zero_vector"].mean()) if len(val_frame) else None,
        },
        "permutation_context": _permutation_context(primary),
        "verdict": {
            "artifact_status": "DIAGNOSTIC_ONLY",
            "promote_stage6_2": False,
            "next_research_step": "Regression Up/Dn target foundation",
        },
    }
    post["evidence_strength"] = _evidence_strength(post)
    return post
```

- [ ] **Step 4: Run focused tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage6_2_range_w1_postmortem.py -q
```

Expected: all tests pass.

- [ ] **Step 5: Checkpoint diff review**

Run:

```bash
git diff -- ML/baseline/analyze_stage6_2_range_w1_postmortem.py tests/test_stage6_2_range_w1_postmortem.py
```

Expected: diff contains only Task 3 analysis changes. Do not commit here; final commit is done only during stage closure via `stage-reporting`.

---

### Task 4: CLI, Artifact, And Report

**Files:**
- Modify: `ML/baseline/analyze_stage6_2_range_w1_postmortem.py`
- Create: `docs/reports/2026-06-30-stage6_2-range-w1-postmortem.md`
- Generate: `ML/reports/stage6_2_range_w1_postmortem.json`

**Interfaces:**
- Consumes:
  - `build_postmortem`
  - `stage6_load_labeled_splits`
  - `stage62_load_ohlc_frame`
- Produces:
  - CLI command `./.venv/bin/python ML/baseline/analyze_stage6_2_range_w1_postmortem.py`
  - `write_report(postmortem: dict) -> str`

- [ ] **Step 1: Add CLI and report writer**

Append to `ML/baseline/analyze_stage6_2_range_w1_postmortem.py`:

```python
from dataclasses import replace

from ML.baseline.benchmark_stage6_outcome_based import STAGE6_0_CONFIG, stage6_load_labeled_splits
from ML.baseline.benchmark_stage6_2_price_action import STAGE6_2_CONFIG, stage62_load_ohlc_frame


def write_report(postmortem: dict) -> str:
    consistency = postmortem["artifact_consistency"]
    dominance = postmortem["dominance"]
    stability = postmortem["stability"]
    selected = postmortem["selected_trade_analysis"]
    activity = postmortem["activity_proxy_checks"]
    permutation = postmortem["permutation_context"]
    verdict = postmortem["verdict"]
    lines = [
        "# Stage 6.2 Range W1 Post-Mortem",
        "",
        "> **Status**: Completed",
        "> **Verdict**: DIAGNOSTIC_ONLY",
        "> **Goal**: Check why `range_w1_atr` dominates Stage 6.2 and why the stability check remains weak.",
        "",
        "## Sources And Commands",
        "",
        "- Source Stage 6.2 JSON: `ML/reports/stage6_2_h12_price_action_feature_family.json`.",
        "- Generated JSON: `ML/reports/stage6_2_range_w1_postmortem.json`.",
        "- Command: `./.venv/bin/python ML/baseline/analyze_stage6_2_range_w1_postmortem.py`.",
        "- Scope: no retraining, no new horizon/ATR/TP/SL/profile search.",
        "",
        "## Artifact Consistency",
        "",
        f"- Primary profile: `{consistency['primary_profile']}`.",
        f"- Stage 6.2 gate status: `{consistency['gate_status_from_stage62_json']}`.",
        f"- Stage 6.2 primary p-value: `{consistency['primary_p_value']}`.",
        f"- Top feature from Stage 6.2 JSON: `{consistency['top_feature_from_stage62_json']}`.",
        "",
        "## Facts",
        "",
        f"- Top feature: `{dominance['top_feature']}`.",
        f"- Top/second importance ratio: `{dominance['top_to_second_auc_drop_ratio']}`.",
        f"- Primary permutation p-value: `{permutation['primary_p_value']}`; required `<= {permutation['required_p_value']}`.",
        f"- Seed p-value range: `{stability['permutation_p_value_min']}` to `{stability['permutation_p_value_max']}`.",
        f"- Zero-vector rows on `val_stop`: `{dominance['zero_vector_rows']}/{dominance['rows']}`.",
        f"- Evidence strength: `{postmortem['evidence_strength']}`.",
        "",
        "## Selected Trade Analysis",
        "",
        f"- Seeds available for selected-trade analysis: `{selected['available_seed_count']}/{selected['seed_count']}`.",
        "- See JSON section `selected_trade_analysis.per_seed` for selected vs non-selected TP-rate, PnL, and bucket rates.",
        "",
        "## Side And Year Disclosure",
        "",
        "- See JSON section `side_analysis` for BUY/SELL counts, TP-rate, PnL, and correlations.",
        "- See JSON section `year_side_matrix` for year x side breakdown.",
        "",
        "## Activity Proxy Checks",
        "",
        f"- `range_w1_atr` vs `ATR` correlation: `{activity['range_w1_vs_atr_corr']}`.",
        f"- `range_w1_atr` vs `bar_range_1_atr` correlation: `{activity['range_w1_vs_bar_range_1_corr']}`.",
        f"- Zero-vector share: `{activity['zero_vector_share']}`.",
        "",
        "## Permutation Context",
        "",
        f"- Observed median PF: `{permutation['observed_pf_median']}`.",
        "- See JSON section `permutation_context.per_seed` for observed PF vs median and p95 random PF by seed.",
        "",
        "## Interpretation Rules",
        "",
        "- Facts above are measurements from the frozen Stage 6.2 artifacts.",
        "- Any causal explanation is a hypothesis unless the report explicitly marks evidence as sufficient.",
        "- `diagnostic_holdout` and `low_n_disclosure` remain disclosure-only.",
        "",
        "This post-mortem does not change the Stage 6.2 verdict and does not promote the feature family.",
        "",
        "## Forbidden Next Steps",
        "",
        "- Do not reopen H12/ATR/TP/SL search from this result.",
        "- Do not create another small OHLC-window variant unless this report provides concrete evidence for a materially new family.",
        "",
        "## Decision",
        "",
        f"- Promote Stage 6.2: `{verdict['promote_stage6_2']}`.",
        f"- Next research step: `{verdict['next_research_step']}`.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    stage62_report = json.loads(STAGE62_JSON_PATH.read_text())
    cfg = replace(
        STAGE6_0_CONFIG,
        horizon_bars=STAGE6_2_CONFIG.horizon_bars,
        stop_offset_atr=STAGE6_2_CONFIG.stop_offset_atr,
        take_profit_atr=STAGE6_2_CONFIG.take_profit_atr,
        entry_lag_bars=STAGE6_2_CONFIG.entry_lag_bars,
    )
    split = stage6_load_labeled_splits(config=cfg)
    ohlc = stage62_load_ohlc_frame()
    frames = {
        "val_stop": build_diagnostic_frame(split, ohlc, "val_stop"),
        "diagnostic_holdout": build_diagnostic_frame(split, ohlc, "diagnostic_holdout"),
        "low_n_disclosure": build_diagnostic_frame(split, ohlc, "low_n_disclosure"),
    }
    postmortem = build_postmortem(stage62_report, frames)
    POSTMORTEM_JSON_PATH.write_text(json.dumps(postmortem, indent=2, ensure_ascii=False) + "\n")
    POSTMORTEM_REPORT_PATH.write_text(write_report(postmortem), encoding="utf-8")
    print(f"wrote {POSTMORTEM_JSON_PATH}")
    print(f"wrote {POSTMORTEM_REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Run focused tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage6_2_range_w1_postmortem.py -q
```

Expected: all tests pass.

- [ ] **Step 3: Run post-mortem script**

Run:

```bash
./.venv/bin/python ML/baseline/analyze_stage6_2_range_w1_postmortem.py
```

Expected output:

```text
wrote /home/hohla/git/SoSimple/ML/reports/stage6_2_range_w1_postmortem.json
wrote /home/hohla/git/SoSimple/docs/reports/2026-06-30-stage6_2-range-w1-postmortem.md
```

- [ ] **Step 4: Inspect generated report**

Run:

```bash
sed -n '1,220p' docs/reports/2026-06-30-stage6_2-range-w1-postmortem.md
```

Expected:

- report states `DIAGNOSTIC_ONLY`;
- report says Stage 6.2 is not promoted;
- report names `Regression Up/Dn target foundation` as next research step;
- report does not propose another minor OHLC-window variant.

- [ ] **Step 5: Checkpoint diff review**

Run:

```bash
git diff -- ML/baseline/analyze_stage6_2_range_w1_postmortem.py tests/test_stage6_2_range_w1_postmortem.py ML/reports/stage6_2_range_w1_postmortem.json docs/reports/2026-06-30-stage6_2-range-w1-postmortem.md
```

Expected: diff contains the generated post-mortem artifact and report. Do not commit here; final commit is done only during stage closure via `stage-reporting`.

---

### Task 5: Close Documentation And Handoff

**Files:**
- Modify: `CHANGELOG.md`
- Modify: `CONTEXT_HANDOFF.md`
- Modify: `wiki/research/fractal-stop-research.md`
- Modify: `wiki/index.md`
- Modify: `wiki/log.md`
- Modify: `wiki/REPO_integrity.md`

**Interfaces:**
- Consumes:
  - `docs/reports/2026-06-30-stage6_2-range-w1-postmortem.md`
  - `ML/reports/stage6_2_range_w1_postmortem.json`
- Produces:
  - project handoff that points next to `Regression Up/Dn target foundation`

- [ ] **Step 1: Update `CHANGELOG.md`**

Add one entry near the top:

```markdown
- 2026-06-30: Added Stage 6.2 `range_w1_atr` post-mortem. Stage 6.2 remains `DIAGNOSTIC_ONLY`; next research direction is `Regression Up/Dn target foundation`.
```

- [ ] **Step 2: Update `CONTEXT_HANDOFF.md`**

Add or replace the current next-step section with:

```markdown
## Current State

Stage 6.2 H12 price-action feature family remains `DIAGNOSTIC_ONLY / TRADING_GATE_FAILED`.
The bounded `range_w1_atr` post-mortem is complete. Evidence strength is recorded in `ML/reports/stage6_2_range_w1_postmortem.json`.

## Next Step

Proceed to `Regression Up/Dn target foundation`.
Do not reopen H12/ATR/TP/SL search from Stage 6.2 results.
```

- [ ] **Step 3: Update wiki research synthesis**

In `wiki/research/fractal-stop-research.md`, add a short dated note:

```markdown
### 2026-06-30: Stage 6.2 range_w1_atr post-mortem

The post-mortem checked whether dominant `range_w1_atr` evidence is robust or artifact-like. Stage 6.2 remains `DIAGNOSTIC_ONLY`; the next research direction is `Regression Up/Dn target foundation`.
```

- [ ] **Step 4: Update wiki index and log**

Add the new report to `wiki/index.md` under research reports, and add this line to `wiki/log.md`:

```markdown
- 2026-06-30: Added Stage 6.2 `range_w1_atr` post-mortem; result recorded from `ML/reports/stage6_2_range_w1_postmortem.json`; next research direction is `Regression Up/Dn target foundation`.
```

- [ ] **Step 5: Regenerate integrity map**

Run:

```bash
./.venv/bin/python wiki/wiki.py generate --repo-root .
```

Expected: `wiki/REPO_integrity.md` is updated.

- [ ] **Step 6: Verify documentation references**

Run:

```bash
rg -n "range_w1_atr post-mortem|Regression Up/Dn target foundation|stage6_2_range_w1_postmortem" CHANGELOG.md CONTEXT_HANDOFF.md wiki docs/reports
```

Expected: finds the new report, JSON artifact, changelog entry, handoff entry, and wiki note.

- [ ] **Step 7: Checkpoint diff review**

Run:

```bash
git diff -- CHANGELOG.md CONTEXT_HANDOFF.md wiki/research/fractal-stop-research.md wiki/index.md wiki/log.md wiki/REPO_integrity.md
```

Expected: diff contains only documentation and wiki closure changes. Do not commit here; final commit is done only during stage closure via `stage-reporting`.

---

### Task 6: Final Verification

**Files:**
- No new files.

**Interfaces:**
- Consumes all prior tasks.
- Produces final readiness evidence.

- [ ] **Step 1: Run focused post-mortem tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage6_2_range_w1_postmortem.py -q
```

Expected: all tests pass.

- [ ] **Step 2: Run Stage 6.2 focused tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage6_2_price_action.py tests/test_stage6_2_range_w1_postmortem.py -q
```

Expected: all tests pass.

- [ ] **Step 3: Run full test suite**

Run:

```bash
./.venv/bin/python -m pytest tests/ -q
```

Expected: all tests pass.

- [ ] **Step 4: Check diff hygiene**

Run:

```bash
git diff --check
```

Expected: no output.

- [ ] **Step 5: Final stage-reporting closure**

Use the `stage-reporting` skill to close the stage, synchronize report/CHANGELOG/CONTEXT_HANDOFF/wiki, and create the single final commit if the stage is accepted. Do not create task-by-task commits.

## Completion Criteria

- The post-mortem report answers why `range_w1_atr` dominated, or explicitly states which evidence is insufficient.
- The post-mortem explains why the stability check stayed weak.
- The result does not promote Stage 6.2.
- The handoff says the next research step is `Regression Up/Dn target foundation`.
- No broad search over H12/ATR/TP/SL or minor OHLC-window variants is introduced.
