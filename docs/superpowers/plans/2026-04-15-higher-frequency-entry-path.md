# Higher-Frequency Entry Path Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Построить более частую версию `entry_path_v1`, которая движется к диапазону `40–50` сделок в год при `PF > 2` и приемлемой устойчивости по времени на основном инструменте.

**Architecture:** План не возвращает проект к текущему очень строгому верхнему слою. Вместо этого он развивает сам `entry_path_v1`: добавляет частотно-ориентированные признаки, новый benchmark устойчивости и новый selection layer поверх prediction exports. Поиск и выбор делаются только на `validation`; `test` используется один раз как frozen check.

**Tech Stack:** Python 3.11, pandas, numpy, torch, pytest, существующие модули `processing/label_signals.py`, `ML/entry_path_task.py`, `ML/models/entry_path_transformer.py`, `ML/benchmark_entry_path_trade_filter.py`.

---

## File Structure

### Read First

- `AGENTS.md`
- `CONTEXT_HANDOFF.md`
- `docs/superpowers/specs/2026-04-15-quantile-next-research-design.md`
- `docs/reports/2026-04-08-entry-path-v1-baseline.md`
- `docs/reports/2026-04-09-entry-path-v1-loss-weighting.md`
- `docs/reports/2026-04-09-entry-path-trade-filter.md`
- `ML/entry_path_task.py`
- `ML/benchmark_entry_path_trade_filter.py`
- `ML/reports/entry_path_trade_filter_selected_rule.json`

### Files To Create

- `ML/benchmark_entry_path_v1_frequency.py`
- `tests/test_benchmark_entry_path_v1_frequency.py`
- `ML/feature_screen_entry_path.py`
- `tests/test_feature_screen_entry_path.py`
- `ML/reports/entry_path_v1_frequency/validation_grid.csv`
- `ML/reports/entry_path_v1_frequency/test_grid.csv`
- `ML/reports/entry_path_v1_frequency/selected_candidate.json`
- `ML/reports/entry_path_v1_frequency/final_verdict.json`
- `ML/reports/entry_path_v1_frequency/run_metadata.json`
- `docs/reports/2026-04-15-entry-path-v1-frequency.md`

### Files To Modify

- `processing/label_signals.py`
- `processing/label_main.py`
- `ML/entry_path_task.py`
- `ML/data_loader.py`
- `ML/models/entry_path_transformer.py`
- `ML/train.py`
- `ML/evaluate_test.py`
- `API/generate_signals.py`
- `tests/test_entry_path_labels.py`
- `tests/test_entry_path_task.py`
- `tests/test_entry_path_model.py`
- `tests/test_entry_path_training.py`
- `tests/test_entry_path_reports.py`

### Files To Update At Stage Close

- `CHANGELOG.md`
- `CONTEXT_HANDOFF.md`
- `docs/superpowers/roadmap.md`
- `wiki/research/execution-tracks.md`
- `wiki/index.md`
- `wiki/log.md`
- `wiki/REPO_integrity.md`

---

## Acceptance Rules

- Selection and threshold search happen on `validation` only.
- `test` is used only once after the winner is frozen.
- Candidate quality must include frequency and stability, not just PF.
- Empty/no-trade rows stay in the training population.
- Cross-instrument checks are forbidden in this plan.
- Conformal Prediction is forbidden in this plan.
- Final candidate must move toward `40–50` trades per year and keep `PF > 2`.

---

## Task 1: Add Frequency-Oriented Features To Entry Path Labels

**Files:**

- Modify: `processing/label_signals.py`
- Modify: `processing/label_main.py`
- Test: `tests/test_entry_path_labels.py`

- [ ] **Step 1: Write the failing test for new frequency-oriented columns**

Add:

```python
def test_label_entry_path_targets_adds_frequency_features():
    frame = pd.DataFrame(
        {
            "time": ["2024.01.01 00:00"],
            "signal": [1],
            "ATR": [1.0],
        }
    )

    result = ls.add_entry_path_frequency_features(frame.copy())

    expected = {
        "session_hour",
        "weekday",
        "range_atr_6",
        "body_atr_3",
        "ret_dir_atr_lag1",
        "vol_regime_24",
    }
    assert expected.issubset(result.columns)
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_entry_path_labels.py::test_label_entry_path_targets_adds_frequency_features -q
```

Expected: fail with missing helper.

- [ ] **Step 3: Implement the new feature builder**

Add to `processing/label_signals.py`:

```python
def add_entry_path_frequency_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["time"] = pd.to_datetime(out["time"], format="%Y.%m.%d %H:%M", errors="coerce")
    out["session_hour"] = out["time"].dt.hour.fillna(0).astype(int)
    out["weekday"] = out["time"].dt.weekday.fillna(0).astype(int)
    out["range_atr_6"] = (
        pd.to_numeric(out.get("high_rolling_6", 0.0), errors="coerce").fillna(0.0)
        - pd.to_numeric(out.get("low_rolling_6", 0.0), errors="coerce").fillna(0.0)
    ) / pd.to_numeric(out["ATR"], errors="coerce").replace(0.0, np.nan)
    out["body_atr_3"] = (
        pd.to_numeric(out.get("close_lag_3", 0.0), errors="coerce").fillna(0.0)
        - pd.to_numeric(out.get("open_lag_3", 0.0), errors="coerce").fillna(0.0)
    ).abs() / pd.to_numeric(out["ATR"], errors="coerce").replace(0.0, np.nan)
    out["ret_dir_atr_lag1"] = pd.to_numeric(out.get("ret_6_dir_atr", 0.0), errors="coerce").shift(1).fillna(0.0)
    out["vol_regime_24"] = pd.to_numeric(out.get("ATR", 0.0), errors="coerce").rolling(24, min_periods=1).mean()
    out = out.fillna(0.0)
    return out
```

- [ ] **Step 4: Wire feature builder into the label pipeline**

Add in `processing/label_main.py` after entry-path targets are created:

```python
labeled_df = label_signals.add_entry_path_frequency_features(labeled_df)
```

- [ ] **Step 5: Run focused tests**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_entry_path_labels.py -q
```

Expected: pass with the new feature test included.

- [ ] **Step 6: Commit**

Run:

```bash
git add processing/label_signals.py processing/label_main.py tests/test_entry_path_labels.py
git commit -m "entry_path: add frequency-oriented label features"
```

---

## Task 2: Add Early Feature Screening With Mutual Information

**Files:**

- Create: `ML/feature_screen_entry_path.py`
- Create: `tests/test_feature_screen_entry_path.py`

- [ ] **Step 1: Write the failing test for feature screening**

Add:

```python
import pandas as pd

from ML.feature_screen_entry_path import rank_features_by_mutual_information


def test_rank_features_by_mutual_information_orders_columns():
    frame = pd.DataFrame(
        {
            "f_good": [0, 0, 1, 1],
            "f_noise": [0, 1, 0, 1],
            "target": [0, 0, 1, 1],
        }
    )

    result = rank_features_by_mutual_information(frame, feature_cols=["f_good", "f_noise"], target_col="target")

    assert list(result["feature"]) == ["f_good", "f_noise"]
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_feature_screen_entry_path.py -q
```

Expected: import failure because module does not exist yet.

- [ ] **Step 3: Implement the feature screener**

Create `ML/feature_screen_entry_path.py`:

```python
from __future__ import annotations

import pandas as pd
from sklearn.feature_selection import mutual_info_classif, mutual_info_regression


def rank_features_by_mutual_information(
    frame: pd.DataFrame,
    feature_cols: list[str],
    target_col: str,
    task: str = "regression",
) -> pd.DataFrame:
    x = frame[feature_cols].astype(float)
    y = frame[target_col].astype(float)
    if task == "classification":
        scores = mutual_info_classif(x, y, discrete_features=False, random_state=42)
    else:
        scores = mutual_info_regression(x, y, discrete_features=False, random_state=42)
    return pd.DataFrame({"feature": feature_cols, "mi_score": scores}).sort_values(
        ["mi_score", "feature"], ascending=[False, True]
    ).reset_index(drop=True)
```

- [ ] **Step 4: Run tests**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_feature_screen_entry_path.py -q
```

Expected: pass.

- [ ] **Step 5: Commit**

Run:

```bash
git add ML/feature_screen_entry_path.py tests/test_feature_screen_entry_path.py
git commit -m "entry_path: add mutual information feature screen"
```

---

## Task 3: Extend The Entry Path Model And Reports

**Files:**

- Modify: `ML/entry_path_task.py`
- Modify: `ML/data_loader.py`
- Modify: `ML/models/entry_path_transformer.py`
- Modify: `ML/train.py`
- Modify: `ML/evaluate_test.py`
- Modify: `API/generate_signals.py`
- Test: `tests/test_entry_path_task.py`
- Test: `tests/test_entry_path_model.py`
- Test: `tests/test_entry_path_training.py`
- Test: `tests/test_entry_path_reports.py`

- [ ] **Step 1: Write failing tests for the new feature columns in the task contract**

Add:

```python
from ML.entry_path_task import ENTRY_PATH_V1_FEATURE_COLUMNS


def test_entry_path_task_exposes_frequency_feature_columns():
    expected = {
        "session_hour",
        "weekday",
        "range_atr_6",
        "body_atr_3",
        "ret_dir_atr_lag1",
        "vol_regime_24",
    }
    assert expected.issubset(set(ENTRY_PATH_V1_FEATURE_COLUMNS))
```

- [ ] **Step 2: Run focused tests**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_entry_path_task.py::test_entry_path_task_exposes_frequency_feature_columns -q
```

Expected: fail because constant is not updated.

- [ ] **Step 3: Update task contract and loaders**

Add in `ML/entry_path_task.py`:

```python
ENTRY_PATH_V1_FEATURE_COLUMNS = [
    "session_hour",
    "weekday",
    "range_atr_6",
    "body_atr_3",
    "ret_dir_atr_lag1",
    "vol_regime_24",
]
```

Ensure `ML/data_loader.py` uses these columns when `task == "entry_path_v1"`.

- [ ] **Step 4: Add a wider head before the final prediction layers**

Update `ML/models/entry_path_transformer.py`:

```python
self.entry_path_projection = nn.Sequential(
    nn.Linear(hidden_dim + len(ENTRY_PATH_V1_FEATURE_COLUMNS), hidden_dim),
    nn.ReLU(),
    nn.Dropout(dropout),
)
```

Feed the concatenated engineered features into the shared trunk before prediction heads.

- [ ] **Step 5: Update train/eval/report code**

Add one report block in `ML/evaluate_test.py` and `tests/test_entry_path_reports.py` that prints:

```text
- trades_per_year
- PF
- profit_concentration_top_10
- negative_year_slices
```

- [ ] **Step 6: Run the relevant test suite**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_entry_path_task.py tests/test_entry_path_model.py tests/test_entry_path_training.py tests/test_entry_path_reports.py -q
```

Expected: pass.

- [ ] **Step 7: Commit**

Run:

```bash
git add ML/entry_path_task.py ML/data_loader.py ML/models/entry_path_transformer.py ML/train.py ML/evaluate_test.py API/generate_signals.py tests/test_entry_path_task.py tests/test_entry_path_model.py tests/test_entry_path_training.py tests/test_entry_path_reports.py
git commit -m "entry_path: extend model for higher-frequency features"
```

---

## Task 4: Build A Frequency And Stability Benchmark

**Files:**

- Create: `ML/benchmark_entry_path_v1_frequency.py`
- Create: `tests/test_benchmark_entry_path_v1_frequency.py`

- [ ] **Step 1: Write failing tests for benchmark selection**

Add:

```python
import pandas as pd

from ML.benchmark_entry_path_v1_frequency import pick_candidate


def test_pick_candidate_requires_pf_and_trades_per_year():
    frame = pd.DataFrame(
        [
            {"candidate": "a", "pf": 2.4, "trades_per_year": 22, "negative_year_slices": 0, "profit_concentration_top_10": 0.20},
            {"candidate": "b", "pf": 2.1, "trades_per_year": 44, "negative_year_slices": 0, "profit_concentration_top_10": 0.18},
            {"candidate": "c", "pf": 1.8, "trades_per_year": 55, "negative_year_slices": 0, "profit_concentration_top_10": 0.15},
        ]
    )

    result = pick_candidate(frame, min_pf=2.0, target_trades_per_year=40)

    assert result["candidate"] == "b"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_entry_path_v1_frequency.py -q
```

Expected: import failure because benchmark does not exist yet.

- [ ] **Step 3: Implement the benchmark**

Create `ML/benchmark_entry_path_v1_frequency.py`:

```python
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from ML.entry_path_trade_filter import compute_pf, run_sequential_check


def compute_profit_concentration(pnl: np.ndarray, top_frac: float = 0.10) -> float:
    if len(pnl) == 0:
        return 1.0
    positive = np.sort(np.asarray(pnl, dtype=float))[::-1]
    top_k = max(1, int(np.ceil(len(positive) * top_frac)))
    gross_profit = float(positive[positive > 0].sum())
    if gross_profit <= 0.0:
        return 1.0
    return float(positive[:top_k].sum() / gross_profit)


def pick_candidate(table: pd.DataFrame, min_pf: float, target_trades_per_year: int) -> pd.Series:
    live = table.loc[
        (table["pf"] >= min_pf)
        & (table["trades_per_year"] >= target_trades_per_year)
        & (table["negative_year_slices"] == 0)
    ].copy()
    if live.empty:
        live = table.copy()
    return live.sort_values(
        ["pf", "trades_per_year", "profit_concentration_top_10"],
        ascending=[False, False, True],
    ).iloc[0]
```

- [ ] **Step 4: Run tests**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_benchmark_entry_path_v1_frequency.py -q
```

Expected: pass.

- [ ] **Step 5: Run train + export + benchmark**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m ML.train --model transformer --task entry_path_v1 --epochs 30 --seed 42
/home/hohla/git/SoSimple/.venv/bin/python -m ML.evaluate_test --task entry_path_v1 --checkpoint ML/checkpoints/transformer_entry_path_v1_best.pt
/home/hohla/git/SoSimple/.venv/bin/python -m API.generate_signals --task entry_path_v1 --model transformer --research-out-prefix ML/reports/entry_path_v1
/home/hohla/git/SoSimple/.venv/bin/python -m ML.benchmark_entry_path_v1_frequency --validation-csv ML/reports/entry_path_v1_validation_predictions.csv --test-csv ML/reports/entry_path_v1_test_predictions.csv --output-dir ML/reports/entry_path_v1_frequency
```

Expected: writes `validation_grid.csv`, `test_grid.csv`, `selected_candidate.json`, `final_verdict.json`.

- [ ] **Step 6: Commit**

Run:

```bash
git add ML/benchmark_entry_path_v1_frequency.py tests/test_benchmark_entry_path_v1_frequency.py
git commit -m "entry_path: benchmark frequency and stability"
```

---

## Task 5: SHAP Review For The Strongest Candidate

**Files:**

- Modify: `docs/reports/2026-04-15-entry-path-v1-frequency.md`

- [ ] **Step 1: Run SHAP only if `final_verdict.json` says the candidate is viable**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -c "import json; from pathlib import Path; verdict=json.loads(Path('ML/reports/entry_path_v1_frequency/final_verdict.json').read_text()); print(verdict['verdict'])"
```

Expected: continue only if verdict is not `reject`.

- [ ] **Step 2: Produce a SHAP ranking snapshot**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -c "import json, torch, shap, pandas as pd; from ML.models.entry_path_transformer import EntryPathTransformer; from ML.data_loader import load_test_dataframe_for_task; frame=load_test_dataframe_for_task('entry_path_v1').head(256); print(frame.shape)"
```

Expected: usable sample frame for SHAP follow-up. If SHAP integration is too heavy in this stage, record that and stop at the sample-preparation checkpoint rather than improvising a new optimization loop.

- [ ] **Step 3: Record the SHAP-based conclusion**

Add to `docs/reports/2026-04-15-entry-path-v1-frequency.md` one conclusion block:

```md
## SHAP Follow-Up

- strongest features: `...`
- suspicious features: `...`
- action: keep / drop / review
- next action: allow exactly one more retraining cycle or stop
```

- [ ] **Step 4: Commit**

Run:

```bash
git add docs/reports/2026-04-15-entry-path-v1-frequency.md
git commit -m "docs: record entry path frequency review"
```

---

## Task 6: Close The Stage And Sync Project Memory

**Files:**

- Create: `docs/reports/2026-04-15-entry-path-v1-frequency.md`
- Modify: `CHANGELOG.md`
- Modify: `CONTEXT_HANDOFF.md`
- Modify: `docs/superpowers/roadmap.md`
- Modify: `wiki/research/execution-tracks.md`
- Modify: `wiki/index.md`
- Modify: `wiki/log.md`
- Modify: `wiki/REPO_integrity.md`

- [ ] **Step 1: Write the report template**

Create:

```md
# Entry Path v1 Frequency Track

> **Date**: 2026-04-15
> **Status**: Completed
> **Goal**: Повысить частоту `entry_path_v1` без развала прибыльности и устойчивости

## Results

- validation winner: `TBD`
- test check: `TBD`
- trades_per_year: `TBD`
- PF: `TBD`
- negative_year_slices: `TBD`
- profit_concentration_top_10: `TBD`

## Verdict

- `viable_higher_frequency_candidate`
- или `reject_frequency_track`
```

- [ ] **Step 2: Fill the report from artifacts**

Use:

```bash
sed -n '1,220p' ML/reports/entry_path_v1_frequency/final_verdict.json
sed -n '1,220p' ML/reports/entry_path_v1_frequency/selected_candidate.json
```

- [ ] **Step 3: Sync changelog and handoff**

Update the project memory files with:

- what changed,
- whether Track A produced a viable candidate,
- what the next step is.

- [ ] **Step 4: Refresh repo integrity**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python wiki/wiki.py generate
```

- [ ] **Step 5: Verification**

Run:

```bash
/home/hohla/git/SoSimple/.venv/bin/python -m pytest tests/test_entry_path_labels.py tests/test_feature_screen_entry_path.py tests/test_entry_path_task.py tests/test_entry_path_model.py tests/test_entry_path_training.py tests/test_entry_path_reports.py tests/test_benchmark_entry_path_v1_frequency.py -q
```

Expected: full suite green.

- [ ] **Step 6: Commit**

Run:

```bash
git add docs/reports/2026-04-15-entry-path-v1-frequency.md CHANGELOG.md CONTEXT_HANDOFF.md docs/superpowers/roadmap.md wiki/research/execution-tracks.md wiki/index.md wiki/log.md wiki/REPO_integrity.md
git commit -m "docs: record higher-frequency entry path verdict"
```

---

## Self-Review

- Spec coverage: plan covers higher-frequency `entry_path`, feature work, training, benchmark, SHAP follow-up, and stage close.
- Placeholder scan: the only `TBD` values are in the report template and must be replaced during execution.
- Type consistency: one benchmark, one report directory, one verdict flow.
