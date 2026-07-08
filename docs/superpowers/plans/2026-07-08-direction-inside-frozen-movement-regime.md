# Direction Inside Frozen Movement Regime Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Проверить, появляется ли предсказуемое направление только внутри уже замороженной movement-mask `top_fraction=0.05`, не меняя сам фильтр движения.

**Execution note 2026-07-08:** исходный контракт `split + time` оказался
неверным, потому что один бар может давать несколько entry-строк. В ходе
продолжения этапа frozen score export получил `split_row_id`, join переведён на
`split + split_row_id`, frozen movement rule не менялся. Финальный canonical
verdict после repair: `REJECT_DIRECTION_INSIDE_MOVEMENT_REGIME`.

**Architecture:** Новый runner читает frozen score export, восстанавливает те же split-ы и признаки, оставляет только строки `selected=True`, строит direction target `entry_up_3 > entry_dn_3` / `entry_dn_3 > entry_up_3`, обучает только простые direction baselines и сохраняет JSON/CSV отчёты. Movement-mask считается входным контрактом: профиль, модель, горизонт, доля отбора и score не подбираются заново. Runner разделяет input-признаки, future targets и diagnostic columns: target-derived поля не должны жить в feature frame и не должны проходить через feature builder.

**Tech Stack:** Python 3.10+, pandas, numpy, scikit-learn, pytest, существующие helpers из `ML.baseline.benchmark_entry_based_amplitude_movement` и `ML.baseline.benchmark_entry_based_movement_filter_freeze`.

## Global Constraints

- Работать в текущей ветке; worktree запрещён.
- Использовать окружение `./.venv/bin/python`.
- `locked_test` не открывать.
- `low_n_disclosure` / `2026` не использовать для выбора; только disclosure.
- Не считать PnL/PF, spread, stop-loss, take-profit, BUY/SELL trading claims.
- Не менять frozen movement rule: `simple_combined / extra_trees_small / H3 / top_fraction=0.05 / seeds=[42,43,44]`.
- Direction target не должен попадать во вход модели.
- `score` movement-filter не использовать как признак direction-модели.
- Максимальный verdict этого этапа: `FROZEN_DIRECTION_RULE_FOR_NEXT_PLAN`, не trading candidate.
- `FROZEN_DIRECTION_RULE_FOR_NEXT_PLAN` разрешён только после заранее заданных robustness checks: yearly/block stability, confidence interval lower bound, class-balance disclosure, exact search budget. Без этих checks максимальный verdict: `RESEARCH_ONLY_DIRECTION_SIGNAL`.
- Join frozen mask к split-ам делается только по уникальному ключу `split + time`; дубли, неизвестный формат `selected` или несовпадение количества выбранных строк должны приводить к `ABORT_CONTRACT_FAIL`.

---

## File Structure

- Create: `ML/baseline/benchmark_direction_inside_frozen_movement_regime.py`
  - CLI и чистые функции для загрузки frozen mask, построения target, обучения baselines, метрик, verdict и записи артефактов.
- Create: `tests/test_direction_inside_frozen_movement_regime.py`
  - Unit-тесты контракта, leakage guards, метрик, verdict и CLI smoke на fixture.
- Create: `docs/reports/2026-07-08-direction-inside-frozen-movement-regime.md`
  - Канонический отчёт после выполнения плана.
- Create: `docs/ML/benchmark_direction_inside_frozen_movement_regime.py.md`
  - Module doc для нового runner.
- Modify: `docs/superpowers/roadmap.md`
  - Удалить выполненный пункт после отчёта или заменить на следующий разрешённый шаг.
- Modify: `CHANGELOG.md`, `CONTEXT_HANDOFF.md`, `MODULE_INDEX.md`, `docs/tests/tests.md`, `wiki/research/fractal-stop-research.md`, `wiki/index.md`, `wiki/log.md`
  - Только на этапе закрытия.

---

### Task 1: Contract And Mask Loader

**Files:**
- Create: `ML/baseline/benchmark_direction_inside_frozen_movement_regime.py`
- Test: `tests/test_direction_inside_frozen_movement_regime.py`

**Interfaces:**
- Consumes:
  - `ML/reports/entry_based_movement_filter_freeze.json`
  - `ML/reports/entry_based_movement_filter_freeze_scores.csv`
  - `benchmark_entry_based_movement_filter_freeze.frozen_rule()`
  - `benchmark_entry_based_movement_filter_freeze.stable_rule_hash(rule)`
- Produces:
  - `frozen_direction_config() -> dict[str, object]`
  - `validate_frozen_movement_contract(freeze_report: dict[str, object], scores: pd.DataFrame) -> dict[str, object]`
  - `load_frozen_mask(freeze_report_path: Path, scores_path: Path) -> dict[str, object]`

- [ ] **Step 1: Write failing tests for exact frozen contract**

Add to `tests/test_direction_inside_frozen_movement_regime.py`:

```python
import json
from pathlib import Path

import pandas as pd

from ML.baseline.benchmark_direction_inside_frozen_movement_regime import (
    frozen_direction_config,
    load_frozen_mask,
    validate_frozen_movement_contract,
)
from ML.baseline.benchmark_entry_based_movement_filter_freeze import (
    frozen_rule,
    sha256_file,
    stable_rule_hash,
)


def _freeze_report() -> dict:
    return {
        "verdict": "FROZEN_MOVEMENT_FILTER_FOR_NEXT_RESEARCH_PLAN",
        "frozen_config": {"frozen_rule": frozen_rule()},
        "frozen_rule_hash": stable_rule_hash(frozen_rule()),
        "contract_status": {"locked_test": "not_opened", "status": "PASS"},
    }


def _scores() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "split": ["train", "train", "val_select", "val_eval", "low_n_disclosure"],
            "time": [
                "2020-01-01 00:00:00",
                "2020-01-02 00:00:00",
                "2021-01-01 00:00:00",
                "2024-01-01 00:00:00",
                "2026-01-01 00:00:00",
            ],
            "year": [2020, 2020, 2021, 2024, 2026],
            "score": [10.0, 1.0, 9.0, 8.0, 7.0],
            "entry_movement_3": [5.0, 1.0, 4.0, 3.0, 2.0],
            "selected": [True, False, True, True, True],
        }
    )


def test_frozen_direction_config_keeps_movement_rule_read_only():
    config = frozen_direction_config()

    assert config["movement_rule"] == frozen_rule()
    assert config["movement_rule_hash"] == stable_rule_hash(frozen_rule())
    assert config["direction_horizon"] == 3
    assert config["locked_test"] == "not_opened"
    assert config["forbidden_input_columns"] == [
        "score",
        "entry_movement_3",
        "entry_up_3",
        "entry_dn_3",
        "target_direction_3",
        "target_is_tie_3",
        "target_up_3",
        "target_dn_3",
        "label_direction_3",
    ]


def test_validate_frozen_movement_contract_rejects_changed_rule():
    report = _freeze_report()
    report["frozen_config"]["frozen_rule"] = {**frozen_rule(), "selected_fraction": 0.10}

    result = validate_frozen_movement_contract(report, _scores())

    assert result["status"] == "ABORT_CONTRACT_FAIL"
    assert "movement_rule_mismatch" in result["reasons"]


def test_validate_frozen_movement_contract_rejects_locked_test_opened():
    report = _freeze_report()
    report["contract_status"]["locked_test"] = "opened"

    result = validate_frozen_movement_contract(report, _scores())

    assert result["status"] == "ABORT_CONTRACT_FAIL"
    assert "locked_test" in result["reasons"]


def test_validate_frozen_movement_contract_requires_expected_score_columns():
    scores = _scores().drop(columns=["selected"])

    result = validate_frozen_movement_contract(_freeze_report(), scores)

    assert result["status"] == "ABORT_CONTRACT_FAIL"
    assert "scores_schema" in result["reasons"]


def test_load_frozen_mask_rejects_unknown_selected_values(tmp_path: Path):
    report_path = tmp_path / "freeze.json"
    scores_path = tmp_path / "scores.csv"
    report_path.write_text(json.dumps(_freeze_report()), encoding="utf-8")
    scores = _scores()
    scores.loc[0, "selected"] = "maybe"
    scores.to_csv(scores_path, index=False)

    try:
        load_frozen_mask(report_path, scores_path)
    except ValueError as exc:
        assert "invalid selected values" in str(exc)
    else:
        raise AssertionError("expected invalid selected values to fail")


def test_load_frozen_mask_reads_report_and_scores(tmp_path: Path):
    report_path = tmp_path / "freeze.json"
    scores_path = tmp_path / "scores.csv"
    report_path.write_text(json.dumps(_freeze_report()), encoding="utf-8")
    _scores().to_csv(scores_path, index=False)

    loaded = load_frozen_mask(report_path, scores_path)

    assert loaded["contract"]["status"] == "PASS"
    assert loaded["scores_hash"] == sha256_file(scores_path)
    assert set(loaded["scores"]["split"]) == {"train", "val_select", "val_eval", "low_n_disclosure"}
    assert int(loaded["scores"]["selected"].sum()) == 4
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_direction_inside_frozen_movement_regime.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'ML.baseline.benchmark_direction_inside_frozen_movement_regime'`.

- [ ] **Step 3: Implement minimal contract loader**

Create `ML/baseline/benchmark_direction_inside_frozen_movement_regime.py`:

```python
"""Direction diagnostics inside the frozen entry-based movement regime."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from ML.baseline.benchmark_entry_based_movement_filter_freeze import (
    frozen_rule,
    sha256_file,
    stable_rule_hash,
)

REQUIRED_SCORE_COLUMNS = ("split", "time", "year", "score", "entry_movement_3", "selected")
ALLOWED_VERDICTS = (
    "FROZEN_DIRECTION_RULE_FOR_NEXT_PLAN",
    "RESEARCH_ONLY_DIRECTION_SIGNAL",
    "REJECT_DIRECTION_INSIDE_MOVEMENT_REGIME",
    "ABORT_CONTRACT_FAIL",
)


def frozen_direction_config() -> dict[str, object]:
    rule = frozen_rule()
    return {
        "movement_rule": rule,
        "movement_rule_hash": stable_rule_hash(rule),
        "direction_horizon": 3,
        "locked_test": "not_opened",
        "selection_policy": {
            "mask_source": "entry_based_movement_filter_freeze_scores.csv:selected",
            "val_select": "direction_rule_selection",
            "val_eval": "check_only",
            "low_n_disclosure": "disclosure_only",
            "locked_test": "not_opened",
        },
        "forbidden_input_columns": [
            "score",
            "entry_movement_3",
            "entry_up_3",
            "entry_dn_3",
            "target_direction_3",
            "target_is_tie_3",
            "target_up_3",
            "target_dn_3",
            "label_direction_3",
        ],
    }


def validate_frozen_movement_contract(
    freeze_report: dict[str, object],
    scores: pd.DataFrame,
) -> dict[str, object]:
    reasons: list[str] = []
    config = frozen_direction_config()

    report_rule = ((freeze_report.get("frozen_config") or {}).get("frozen_rule") or {})
    if report_rule != config["movement_rule"]:
        reasons.append("movement_rule_mismatch")
    if freeze_report.get("frozen_rule_hash") not in (None, config["movement_rule_hash"]):
        reasons.append("movement_rule_hash")

    contract_status = freeze_report.get("contract_status") or {}
    if contract_status.get("locked_test", "not_opened") != "not_opened":
        reasons.append("locked_test")
    if contract_status.get("status", "PASS") != "PASS":
        reasons.append("movement_contract_status")

    missing = [column for column in REQUIRED_SCORE_COLUMNS if column not in scores.columns]
    if missing:
        reasons.append("scores_schema")

    if "split" in scores.columns and "selected" in scores.columns:
        selected_by_split = scores.loc[scores["selected"].astype(bool)].groupby("split").size().to_dict()
        for split_name in ("train", "val_select", "val_eval"):
            if int(selected_by_split.get(split_name, 0)) == 0:
                reasons.append(f"{split_name}.selected_n")

    return {
        "status": "ABORT_CONTRACT_FAIL" if reasons else "PASS",
        "reasons": reasons,
        "movement_rule_hash": config["movement_rule_hash"],
    }


def load_frozen_mask(freeze_report_path: Path, scores_path: Path) -> dict[str, object]:
    freeze_report = json.loads(Path(freeze_report_path).read_text(encoding="utf-8"))
    scores = pd.read_csv(scores_path)
    if "selected" in scores.columns:
        selected_raw = scores["selected"].astype(str).str.strip().str.lower()
        selected_map = {"true": True, "1": True, "yes": True, "false": False, "0": False, "no": False}
        invalid = sorted(set(selected_raw) - set(selected_map))
        if invalid:
            raise ValueError(f"invalid selected values: {invalid}")
        scores["selected"] = selected_raw.map(selected_map).astype(bool)
    contract = validate_frozen_movement_contract(freeze_report, scores)
    return {
        "freeze_report": freeze_report,
        "scores": scores,
        "scores_hash": sha256_file(Path(scores_path)),
        "contract": contract,
    }
```

- [ ] **Step 4: Run tests to verify pass**

Run:

```bash
./.venv/bin/python -m pytest tests/test_direction_inside_frozen_movement_regime.py -q
```

Expected: PASS for Task 1 tests.

- [ ] **Step 5: Review**

Ask a review subagent to check only Task 1 for:

- exact frozen rule guard;
- no `locked_test` opening;
- no use of `score` as future direction input.

---

### Task 2: Direction Target And Masked Dataset

**Files:**
- Modify: `ML/baseline/benchmark_direction_inside_frozen_movement_regime.py`
- Modify: `tests/test_direction_inside_frozen_movement_regime.py`

**Interfaces:**
- Consumes:
  - `amplitude.load_entry_based_splits() -> dict[str, pd.DataFrame]`
  - frozen scores from Task 1
- Produces:
  - `build_direction_targets(frame: pd.DataFrame, horizon: int = 3) -> pd.DataFrame`
  - `validate_mask_join_keys(splits: dict[str, pd.DataFrame], scores: pd.DataFrame) -> dict[str, object]`
  - `join_mask_to_splits(splits: dict[str, pd.DataFrame], scores: pd.DataFrame) -> dict[str, pd.DataFrame]`
  - `build_masked_direction_dataset(splits: dict[str, pd.DataFrame], scores: pd.DataFrame) -> dict[str, pd.DataFrame]`

- [ ] **Step 1: Write failing tests for target convention and selected-only rows**

Add:

```python
def test_build_direction_targets_drops_ties_and_labels_up_down():
    from ML.baseline.benchmark_direction_inside_frozen_movement_regime import build_direction_targets

    frame = pd.DataFrame(
        {
            "entry_up_3": [5.0, 1.0, 2.0, float("nan")],
            "entry_dn_3": [1.0, 4.0, 2.0, 3.0],
        }
    )

    targets = build_direction_targets(frame)

    assert targets["target_direction_3"].tolist() == [1, -1, pd.NA, pd.NA]
    assert targets["target_is_tie_3"].tolist() == [False, False, True, True]


def test_build_masked_direction_dataset_keeps_only_selected_rows_by_split():
    from ML.baseline.benchmark_direction_inside_frozen_movement_regime import build_masked_direction_dataset

    splits = {
        "train": pd.DataFrame(
            {
                "time": ["2020-01-01 00:00:00", "2020-01-02 00:00:00"],
                "entry_up_3": [3.0, 1.0],
                "entry_dn_3": [1.0, 3.0],
                "ATR": [0.5, 0.6],
            }
        ),
        "val_select": pd.DataFrame(
            {
                "time": ["2021-01-01 00:00:00"],
                "entry_up_3": [4.0],
                "entry_dn_3": [1.0],
                "ATR": [0.7],
            }
        ),
    }
    scores = pd.DataFrame(
        {
            "split": ["train", "train", "val_select"],
            "time": ["2020-01-01 00:00:00", "2020-01-02 00:00:00", "2021-01-01 00:00:00"],
            "selected": [True, False, True],
            "score": [10.0, 1.0, 9.0],
            "entry_movement_3": [3.0, 3.0, 4.0],
            "year": [2020, 2020, 2021],
        }
    )

    dataset = build_masked_direction_dataset(splits, scores)

    assert len(dataset["train"]) == 1
    assert len(dataset["val_select"]) == 1
    assert dataset["train"]["target_direction_3"].tolist() == [1]
    assert "score" not in dataset["train"].columns
    assert "entry_up_3" not in dataset["train"].columns
    assert "entry_dn_3" not in dataset["train"].columns
    assert "entry_movement_3" not in dataset["train"].columns
    assert "target_up_3" in dataset["train"].columns
    assert "target_dn_3" in dataset["train"].columns


def test_validate_mask_join_keys_rejects_duplicate_split_time():
    from ML.baseline.benchmark_direction_inside_frozen_movement_regime import validate_mask_join_keys

    splits = {
        "train": pd.DataFrame(
            {
                "time": ["2020-01-01 00:00:00", "2020-01-01 00:00:00"],
                "entry_up_3": [3.0, 1.0],
                "entry_dn_3": [1.0, 3.0],
            }
        )
    }
    scores = pd.DataFrame(
        {
            "split": ["train", "train"],
            "time": ["2020-01-01 00:00:00", "2020-01-01 00:00:00"],
            "selected": [True, False],
            "score": [10.0, 1.0],
            "entry_movement_3": [3.0, 3.0],
            "year": [2020, 2020],
        }
    )

    result = validate_mask_join_keys(splits, scores)

    assert result["status"] == "ABORT_CONTRACT_FAIL"
    assert "scores.duplicate_split_time" in result["reasons"]
    assert "splits.train.duplicate_time" in result["reasons"]
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_direction_inside_frozen_movement_regime.py -q
```

Expected: FAIL with missing functions.

- [ ] **Step 3: Implement target and mask join**

Append to runner:

```python
def build_direction_targets(frame: pd.DataFrame, horizon: int = 3) -> pd.DataFrame:
    up = pd.to_numeric(frame[f"entry_up_{horizon}"], errors="coerce")
    dn = pd.to_numeric(frame[f"entry_dn_{horizon}"], errors="coerce")
    direction = pd.Series(pd.array([pd.NA] * len(frame), dtype="Int64"), index=frame.index)
    valid = up.notna() & dn.notna()
    direction.loc[valid & (up > dn)] = 1
    direction.loc[valid & (dn > up)] = -1
    target = pd.DataFrame(index=frame.index)
    target[f"target_direction_{horizon}"] = direction
    target[f"target_is_tie_{horizon}"] = ~(valid & (up != dn))
    target[f"target_up_{horizon}"] = up
    target[f"target_dn_{horizon}"] = dn
    return target


def _time_key(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce").dt.strftime("%Y-%m-%d %H:%M:%S")


def validate_mask_join_keys(
    splits: dict[str, pd.DataFrame],
    scores: pd.DataFrame,
) -> dict[str, object]:
    reasons: list[str] = []
    if {"split", "time"} <= set(scores.columns):
        score_keys = scores[["split", "time"]].copy()
        score_keys["_time_key"] = _time_key(score_keys["time"])
        if score_keys[["split", "_time_key"]].duplicated().any():
            reasons.append("scores.duplicate_split_time")
        if score_keys["_time_key"].isna().any():
            reasons.append("scores.invalid_time")
    for split_name, frame in splits.items():
        if "time" not in frame.columns:
            reasons.append(f"splits.{split_name}.missing_time")
            continue
        split_keys = pd.DataFrame({"_time_key": _time_key(frame["time"])})
        if split_keys["_time_key"].duplicated().any():
            reasons.append(f"splits.{split_name}.duplicate_time")
        if split_keys["_time_key"].isna().any():
            reasons.append(f"splits.{split_name}.invalid_time")
    return {"status": "ABORT_CONTRACT_FAIL" if reasons else "PASS", "reasons": reasons}


def join_mask_to_splits(
    splits: dict[str, pd.DataFrame],
    scores: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    key_contract = validate_mask_join_keys(splits, scores)
    if key_contract["status"] != "PASS":
        raise ValueError(f"mask join key validation failed: {key_contract['reasons']}")
    joined: dict[str, pd.DataFrame] = {}
    selected_scores = scores.loc[scores["selected"].astype(bool)].copy()
    selected_scores["_time_key"] = _time_key(selected_scores["time"])
    for split_name, frame in splits.items():
        split_scores = selected_scores.loc[selected_scores["split"] == split_name, ["_time_key"]].copy()
        split_scores["_mask_selected"] = True
        working = frame.copy()
        working["_time_key"] = _time_key(working["time"])
        merged = working.merge(split_scores.drop_duplicates(), on="_time_key", how="left")
        merged = merged.loc[merged["_mask_selected"].fillna(False)].drop(columns=["_time_key", "_mask_selected"])
        if len(merged) != len(split_scores):
            raise ValueError(f"mask join count mismatch for {split_name}: expected {len(split_scores)}, got {len(merged)}")
        joined[split_name] = merged.reset_index(drop=True)
    return joined


def build_masked_direction_dataset(
    splits: dict[str, pd.DataFrame],
    scores: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    masked = join_mask_to_splits(splits, scores)
    result: dict[str, pd.DataFrame] = {}
    forbidden = set(frozen_direction_config()["forbidden_input_columns"])
    for split_name, frame in masked.items():
        targets = build_direction_targets(frame)
        feature_frame = frame.drop(columns=[column for column in forbidden if column in frame.columns])
        combined = pd.concat([feature_frame.reset_index(drop=True), targets.reset_index(drop=True)], axis=1)
        combined = combined.loc[combined["target_direction_3"].notna()].reset_index(drop=True)
        result[split_name] = combined
    return result
```

- [ ] **Step 4: Run tests to verify pass**

Run:

```bash
./.venv/bin/python -m pytest tests/test_direction_inside_frozen_movement_regime.py -q
```

Expected: PASS for Tasks 1-2 tests.

- [ ] **Step 5: Review**

Ask a review subagent to check only Task 2 for:

- target labels are future labels only;
- ties are excluded from supervised rows;
- mask join cannot select rows by direction outcome.

---

### Task 3: Baselines And Metrics

**Files:**
- Modify: `ML/baseline/benchmark_direction_inside_frozen_movement_regime.py`
- Modify: `tests/test_direction_inside_frozen_movement_regime.py`

**Interfaces:**
- Consumes:
  - masked dataset from Task 2
  - `amplitude.build_feature_profile_with_metadata`
  - `amplitude._align_feature_frames_to_train`
  - `amplitude._numeric_frame`
- Produces:
  - `build_feature_matrices(masked: dict[str, pd.DataFrame], profile: str = "simple_combined") -> dict[str, pd.DataFrame]`
  - `evaluate_direction_predictions(y_true: pd.Series, y_pred: pd.Series) -> dict[str, object]`
  - `run_direction_baselines(masked: dict[str, pd.DataFrame]) -> dict[str, object]`

- [ ] **Step 1: Write failing tests for leakage guard and metric behavior**

Add:

```python
def test_evaluate_direction_predictions_reports_balanced_metrics():
    from ML.baseline.benchmark_direction_inside_frozen_movement_regime import evaluate_direction_predictions

    metrics = evaluate_direction_predictions(
        pd.Series([1, 1, -1, -1]),
        pd.Series([1, -1, -1, -1]),
    )

    assert metrics["total_n"] == 4
    assert metrics["accuracy"] == 0.75
    assert metrics["up_recall"] == 0.5
    assert metrics["dn_recall"] == 1.0


def test_build_feature_matrices_excludes_direction_targets_and_movement_score():
    from ML.baseline.benchmark_direction_inside_frozen_movement_regime import build_feature_matrices

    masked = {
        "train": pd.DataFrame(
            {
                "time": ["2020-01-01 00:00:00", "2020-01-02 00:00:00"],
                "ATR": [0.5, 0.6],
                "score": [10.0, 1.0],
                "entry_up_3": [3.0, 1.0],
                "entry_dn_3": [1.0, 3.0],
                "entry_movement_3": [3.0, 3.0],
                "target_direction_3": [1, -1],
            }
        ),
        "val_select": pd.DataFrame(
            {
                "time": ["2021-01-01 00:00:00", "2021-01-02 00:00:00"],
                "ATR": [0.7, 0.8],
                "score": [9.0, 8.0],
                "entry_up_3": [4.0, 1.0],
                "entry_dn_3": [1.0, 4.0],
                "entry_movement_3": [4.0, 4.0],
                "target_direction_3": [1, -1],
            }
        ),
    }

    matrices = build_feature_matrices(masked, profile="time_plus_atr")

    for frame in matrices["features"].values():
        assert "score" not in frame.columns
        assert "entry_up_3" not in frame.columns
        assert "entry_dn_3" not in frame.columns
        assert "entry_movement_3" not in frame.columns
        assert "target_direction_3" not in frame.columns
        assert "target_up_3" not in frame.columns
        assert "target_dn_3" not in frame.columns


def test_fit_direction_models_fits_once_and_predicts_each_split():
    from ML.baseline.benchmark_direction_inside_frozen_movement_regime import fit_direction_models

    class CountingModel:
        def __init__(self):
            self.fit_calls = 0

        def fit(self, train_x, train_y):
            self.fit_calls += 1
            return self

        def predict(self, eval_x):
            return [1] * len(eval_x)

    model = CountingModel()
    fitted = fit_direction_models(
        {"counting": model},
        pd.DataFrame({"ATR": [0.5, 0.6]}),
        pd.Series([1, -1]),
    )

    assert fitted["counting"] is model
    assert model.fit_calls == 1
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_direction_inside_frozen_movement_regime.py -q
```

Expected: FAIL with missing functions.

- [ ] **Step 3: Implement feature matrices and simple baselines**

Append imports:

```python
import numpy as np
from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score, matthews_corrcoef, precision_score, recall_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import RobustScaler

from ML.baseline import benchmark_entry_based_amplitude_movement as amplitude
```

Append functions:

```python
def build_feature_matrices(
    masked: dict[str, pd.DataFrame],
    profile: str = "simple_combined",
) -> dict[str, object]:
    sanitized: dict[str, pd.DataFrame] = {}
    forbidden = set(frozen_direction_config()["forbidden_input_columns"])
    for split_name, frame in masked.items():
        sanitized[split_name] = frame.drop(columns=[column for column in forbidden if column in frame.columns])
    profile_bundle = amplitude.build_feature_profile_with_metadata(sanitized, profile)
    features = amplitude._align_feature_frames_to_train(profile_bundle["features"])
    return {"features": features, "metadata": profile_bundle["metadata"], "profile": profile}


def evaluate_direction_predictions(y_true: pd.Series, y_pred: pd.Series) -> dict[str, object]:
    truth = pd.to_numeric(y_true, errors="coerce")
    pred = pd.to_numeric(y_pred, errors="coerce")
    valid = truth.notna() & pred.notna()
    truth_np = truth.loc[valid].astype(int).to_numpy()
    pred_np = pred.loc[valid].astype(int).to_numpy()
    if len(truth_np) == 0:
        return {"total_n": 0, "accuracy": None, "balanced_accuracy": None}
    return {
        "total_n": int(len(truth_np)),
        "up_support": int(np.sum(truth_np == 1)),
        "dn_support": int(np.sum(truth_np == -1)),
        "accuracy": float(accuracy_score(truth_np, pred_np)),
        "balanced_accuracy": float(balanced_accuracy_score(truth_np, pred_np)),
        "macro_f1": float(f1_score(truth_np, pred_np, average="macro", zero_division=0)),
        "mcc": float(matthews_corrcoef(truth_np, pred_np)) if len(set(truth_np)) > 1 and len(set(pred_np)) > 1 else 0.0,
        "up_precision": float(precision_score(truth_np, pred_np, pos_label=1, zero_division=0)),
        "up_recall": float(recall_score(truth_np, pred_np, pos_label=1, zero_division=0)),
        "dn_precision": float(precision_score(truth_np, pred_np, pos_label=-1, zero_division=0)),
        "dn_recall": float(recall_score(truth_np, pred_np, pos_label=-1, zero_division=0)),
    }


def _majority_prediction(train_y: pd.Series, n_rows: int) -> pd.Series:
    majority = int(train_y.value_counts().sort_values(ascending=False).index[0])
    return pd.Series([majority] * n_rows)


def fit_direction_models(
    models: dict[str, object],
    train_x: pd.DataFrame,
    train_y: pd.Series,
) -> dict[str, object]:
    fitted: dict[str, object] = {}
    for model_name, model in models.items():
        model.fit(train_x, train_y.astype(int))
        fitted[model_name] = model
    return fitted


def _predict_classifier(model, eval_x: pd.DataFrame) -> pd.Series:
    return pd.Series(model.predict(eval_x))


def run_direction_baselines(masked: dict[str, pd.DataFrame]) -> dict[str, object]:
    matrices = build_feature_matrices(masked, profile="simple_combined")
    features: dict[str, pd.DataFrame] = matrices["features"]
    train_y = masked["train"]["target_direction_3"].astype(int)
    models = {
        "logistic_regression": make_pipeline(RobustScaler(), LogisticRegression(max_iter=500, class_weight="balanced")),
        "random_forest_small": RandomForestClassifier(
            n_estimators=64,
            max_depth=6,
            min_samples_leaf=20,
            random_state=42,
            n_jobs=24,
            class_weight="balanced_subsample",
        ),
        "extra_trees_small": ExtraTreesClassifier(
            n_estimators=64,
            max_depth=6,
            min_samples_leaf=20,
            random_state=42,
            n_jobs=24,
            class_weight="balanced",
        ),
    }
    fitted_models = fit_direction_models(models, features["train"], train_y)
    results: dict[str, object] = {}
    for model_name in ("majority_class", *fitted_models.keys()):
        split_metrics: dict[str, object] = {}
        for split_name in ("train", "val_select", "val_eval", "low_n_disclosure"):
            if split_name not in masked or split_name not in features:
                continue
            if model_name == "majority_class":
                pred = _majority_prediction(train_y, len(masked[split_name]))
            else:
                pred = _predict_classifier(fitted_models[model_name], features[split_name])
            split_metrics[split_name] = evaluate_direction_predictions(masked[split_name]["target_direction_3"], pred)
        results[model_name] = split_metrics
    return {
        "profile": "simple_combined",
        "target": "target_direction_3",
        "baselines": results,
    }
```

- [ ] **Step 4: Run tests to verify pass**

Run:

```bash
./.venv/bin/python -m pytest tests/test_direction_inside_frozen_movement_regime.py -q
```

Expected: PASS for Tasks 1-3 tests.

- [ ] **Step 5: Review**

Ask a review subagent to check only Task 3 for:

- no forbidden target columns in feature matrices;
- no `score` as input;
- baselines are simple and bounded.

---

### Task 4: Winner Selection, Verdict, And Artifacts

**Files:**
- Modify: `ML/baseline/benchmark_direction_inside_frozen_movement_regime.py`
- Modify: `tests/test_direction_inside_frozen_movement_regime.py`

**Interfaces:**
- Produces:
  - `select_direction_rule(results: dict[str, object]) -> dict[str, object]`
  - `compute_direction_robustness(masked: dict[str, pd.DataFrame], baseline_results: dict[str, object], selection: dict[str, object]) -> dict[str, object]`
  - `decide_direction_verdict(contract: dict[str, object], selection: dict[str, object], robustness: dict[str, object] | None = None) -> str`
  - `build_report(...) -> dict[str, object]`
  - `write_artifacts(report: dict[str, object], rows: pd.DataFrame, output_prefix: Path) -> None`

- [ ] **Step 1: Write failing tests for bounded selection and reject gates**

Add:

```python
def test_decide_direction_verdict_rejects_weak_val_eval():
    from ML.baseline.benchmark_direction_inside_frozen_movement_regime import decide_direction_verdict

    contract = {"status": "PASS"}
    selection = {
        "status": "SELECTED",
        "winner": "extra_trees_small",
        "val_select": {"total_n": 120, "balanced_accuracy": 0.58, "mcc": 0.12},
        "val_eval": {"total_n": 120, "balanced_accuracy": 0.51, "mcc": 0.01},
        "beats_majority_on_val_eval": False,
    }

    assert decide_direction_verdict(contract, selection) == "REJECT_DIRECTION_INSIDE_MOVEMENT_REGIME"


def test_select_direction_rule_uses_val_select_not_val_eval():
    from ML.baseline.benchmark_direction_inside_frozen_movement_regime import select_direction_rule

    results = {
        "baselines": {
            "model_a": {
                "val_select": {"total_n": 100, "balanced_accuracy": 0.60, "mcc": 0.20},
                "val_eval": {"total_n": 100, "balanced_accuracy": 0.52, "mcc": 0.01},
            },
            "model_b": {
                "val_select": {"total_n": 100, "balanced_accuracy": 0.55, "mcc": 0.10},
                "val_eval": {"total_n": 100, "balanced_accuracy": 0.90, "mcc": 0.80},
            },
            "majority_class": {
                "val_select": {"total_n": 100, "balanced_accuracy": 0.50, "mcc": 0.0},
                "val_eval": {"total_n": 100, "balanced_accuracy": 0.50, "mcc": 0.0},
            },
        }
    }

    selection = select_direction_rule(results)

    assert selection["winner"] == "model_a"


def test_select_direction_rule_ignores_low_n_disclosure():
    from ML.baseline.benchmark_direction_inside_frozen_movement_regime import select_direction_rule

    base_results = {
        "baselines": {
            "model_a": {
                "val_select": {"total_n": 100, "balanced_accuracy": 0.60, "mcc": 0.20},
                "val_eval": {"total_n": 100, "balanced_accuracy": 0.56, "mcc": 0.08},
                "low_n_disclosure": {"total_n": 100, "balanced_accuracy": 0.10, "mcc": -0.80},
            },
            "model_b": {
                "val_select": {"total_n": 100, "balanced_accuracy": 0.55, "mcc": 0.10},
                "val_eval": {"total_n": 100, "balanced_accuracy": 0.56, "mcc": 0.08},
                "low_n_disclosure": {"total_n": 100, "balanced_accuracy": 0.99, "mcc": 0.95},
            },
            "majority_class": {"val_eval": {"total_n": 100, "balanced_accuracy": 0.50, "mcc": 0.0}},
        }
    }

    selection = select_direction_rule(base_results)

    assert selection["winner"] == "model_a"


def test_decide_direction_verdict_needs_robustness_for_frozen_status():
    from ML.baseline.benchmark_direction_inside_frozen_movement_regime import decide_direction_verdict

    contract = {"status": "PASS"}
    selection = {
        "status": "SELECTED",
        "val_select": {"total_n": 120, "balanced_accuracy": 0.58, "mcc": 0.12},
        "val_eval": {"total_n": 120, "balanced_accuracy": 0.57, "mcc": 0.10},
        "beats_majority_on_val_eval": True,
    }

    assert decide_direction_verdict(contract, selection, robustness=None) == "RESEARCH_ONLY_DIRECTION_SIGNAL"
    assert (
        decide_direction_verdict(contract, selection, robustness={"status": "PASS"})
        == "FROZEN_DIRECTION_RULE_FOR_NEXT_PLAN"
    )


def test_compute_direction_robustness_reports_research_only_on_single_year():
    from ML.baseline.benchmark_direction_inside_frozen_movement_regime import compute_direction_robustness

    masked = {
        "val_eval": pd.DataFrame(
            {
                "time": ["2024-01-01 00:00:00"] * 120,
                "target_direction_3": [1, -1] * 60,
            }
        )
    }
    baseline_results = {
        "baselines": {
            "extra_trees_small": {
                "val_eval": {
                    "total_n": 120,
                    "balanced_accuracy": 0.57,
                    "mcc": 0.10,
                    "up_recall": 0.58,
                    "dn_recall": 0.56,
                    "up_support": 60,
                    "dn_support": 60,
                }
            }
        }
    }
    selection = {"winner": "extra_trees_small"}

    robustness = compute_direction_robustness(masked, baseline_results, selection)

    assert robustness["status"] == "RESEARCH_ONLY"
    assert "val_eval.active_years" in robustness["reasons"]
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_direction_inside_frozen_movement_regime.py -q
```

Expected: FAIL with missing functions.

- [ ] **Step 3: Implement selection and verdict**

Append:

```python
def _metric(metrics: dict[str, object], name: str) -> float:
    value = metrics.get(name)
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("-inf")


def _recall_ci_lower(recall: float, support: float) -> float:
    if support <= 0:
        return float("-inf")
    standard_error = np.sqrt(max(recall * (1.0 - recall), 0.0) / support)
    return float(recall - 1.96 * standard_error)


def select_direction_rule(results: dict[str, object]) -> dict[str, object]:
    baselines = results.get("baselines") or {}
    candidates: list[tuple[float, float, str, dict[str, object]]] = []
    for model_name, split_metrics in baselines.items():
        if model_name == "majority_class" or not isinstance(split_metrics, dict):
            continue
        val_select = split_metrics.get("val_select") or {}
        candidates.append(
            (
                _metric(val_select, "balanced_accuracy"),
                _metric(val_select, "mcc"),
                str(model_name),
                split_metrics,
            )
        )
    if not candidates:
        return {"status": "NO_CANDIDATE", "winner": None}
    candidates.sort(reverse=True)
    _, _, winner, winner_metrics = candidates[0]
    majority_eval = ((baselines.get("majority_class") or {}).get("val_eval") or {})
    val_eval = winner_metrics.get("val_eval") or {}
    return {
        "status": "SELECTED",
        "winner": winner,
        "selection_metric": "val_select.balanced_accuracy_then_mcc",
        "val_select": winner_metrics.get("val_select") or {},
        "val_eval": val_eval,
        "low_n_disclosure": winner_metrics.get("low_n_disclosure") or {},
        "beats_majority_on_val_eval": _metric(val_eval, "balanced_accuracy") > _metric(majority_eval, "balanced_accuracy"),
    }


def compute_direction_robustness(
    masked: dict[str, pd.DataFrame],
    baseline_results: dict[str, object],
    selection: dict[str, object],
) -> dict[str, object]:
    reasons: list[str] = []
    winner = selection.get("winner")
    if not winner:
        reasons.append("winner")
    val_eval_frame = masked.get("val_eval")
    if val_eval_frame is None or val_eval_frame.empty:
        reasons.append("val_eval.rows")
    else:
        years = pd.to_datetime(val_eval_frame["time"], errors="coerce").dt.year
        yearly_counts = years.value_counts().sort_index().to_dict()
        active_years = {int(year): int(count) for year, count in yearly_counts.items() if int(count) >= 30}
        if len(active_years) < 2:
            reasons.append("val_eval.active_years")
    selected_metrics = ((baseline_results.get("baselines") or {}).get(winner) or {}) if winner else {}
    val_eval = selected_metrics.get("val_eval") or {}
    if _metric(val_eval, "balanced_accuracy") < 0.56:
        reasons.append("val_eval.balanced_accuracy")
    if _metric(val_eval, "mcc") < 0.08:
        reasons.append("val_eval.mcc")
    up_lower = _recall_ci_lower(_metric(val_eval, "up_recall"), _metric(val_eval, "up_support"))
    dn_lower = _recall_ci_lower(_metric(val_eval, "dn_recall"), _metric(val_eval, "dn_support"))
    balanced_accuracy_ci95_lower = (up_lower + dn_lower) / 2.0
    if balanced_accuracy_ci95_lower < 0.52:
        reasons.append("val_eval.balanced_accuracy_ci95_lower")
    return {
        "status": "PASS" if not reasons else "RESEARCH_ONLY",
        "reasons": reasons,
        "checks": {
            "minimum_active_val_eval_years": 2,
            "minimum_rows_per_active_year": 30,
            "val_eval_balanced_accuracy_gate": 0.56,
            "val_eval_mcc_gate": 0.08,
            "val_eval_balanced_accuracy_ci95_lower_gate": 0.52,
        },
        "confidence_interval": {
            "method": "normal_approximation_per_class_recall",
            "balanced_accuracy_ci95_lower": balanced_accuracy_ci95_lower,
        },
    }


def decide_direction_verdict(
    contract: dict[str, object],
    selection: dict[str, object],
    robustness: dict[str, object] | None = None,
) -> str:
    if contract.get("status") != "PASS":
        return "ABORT_CONTRACT_FAIL"
    if selection.get("status") != "SELECTED":
        return "REJECT_DIRECTION_INSIDE_MOVEMENT_REGIME"
    val_select = selection.get("val_select") or {}
    val_eval = selection.get("val_eval") or {}
    if _metric(val_select, "total_n") < 100 or _metric(val_eval, "total_n") < 100:
        return "REJECT_DIRECTION_INSIDE_MOVEMENT_REGIME"
    if _metric(val_select, "balanced_accuracy") < 0.56 or _metric(val_select, "mcc") < 0.08:
        return "REJECT_DIRECTION_INSIDE_MOVEMENT_REGIME"
    if _metric(val_eval, "balanced_accuracy") < 0.54 or _metric(val_eval, "mcc") < 0.05:
        return "REJECT_DIRECTION_INSIDE_MOVEMENT_REGIME"
    if selection.get("beats_majority_on_val_eval") is not True:
        return "REJECT_DIRECTION_INSIDE_MOVEMENT_REGIME"
    if (
        _metric(val_eval, "balanced_accuracy") >= 0.56
        and _metric(val_eval, "mcc") >= 0.08
        and robustness is not None
        and robustness.get("status") == "PASS"
    ):
        return "FROZEN_DIRECTION_RULE_FOR_NEXT_PLAN"
    return "RESEARCH_ONLY_DIRECTION_SIGNAL"
```

- [ ] **Step 4: Add artifact functions**

Append:

```python
def build_report(
    contract: dict[str, object],
    baseline_results: dict[str, object],
    selection: dict[str, object],
    robustness: dict[str, object],
    verdict: str,
) -> dict[str, object]:
    config = frozen_direction_config()
    trained_baseline_count = int(
        sum(1 for model_name in (baseline_results.get("baselines") or {}) if model_name != "majority_class")
    )
    return {
        "schema_version": 1,
        "stage_status": "RESEARCH_ONLY",
        "verdict": verdict,
        "allowed_verdicts": list(ALLOWED_VERDICTS),
        "frozen_direction_config": config,
        "contract": contract,
        "baseline_results": baseline_results,
        "selection": selection,
        "robustness": robustness,
        "search_budget": {
            "direction_baselines_trained": trained_baseline_count,
            "selection_split": "val_select",
            "disclosure_splits_not_used_for_selection": ["val_eval", "low_n_disclosure"],
        },
        "forbidden_interpretations": [
            "not_pnl",
            "not_pf",
            "not_trading_candidate",
            "not_live_rule",
            "not_locked_test_permission",
        ],
    }


def build_rows_export(masked: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    for split_name, frame in masked.items():
        if frame.empty:
            continue
        export = frame[["time", "target_direction_3", "target_up_3", "target_dn_3"]].copy()
        export.insert(0, "split", split_name)
        rows.append(export)
    if not rows:
        return pd.DataFrame(columns=["split", "time", "target_direction_3", "target_up_3", "target_dn_3"])
    return pd.concat(rows, ignore_index=True)


def write_artifacts(
    report: dict[str, object],
    rows: pd.DataFrame,
    output_prefix: Path,
) -> None:
    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    Path(f"{output_prefix}.json").write_text(json.dumps(report, ensure_ascii=True, indent=2, default=str), encoding="utf-8")
    rows.to_csv(Path(f"{output_prefix}_rows.csv"), index=False)
```

- [ ] **Step 5: Run tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_direction_inside_frozen_movement_regime.py -q
```

Expected: PASS for Tasks 1-4 tests.

- [ ] **Step 6: Review**

Ask a review subagent to check only Task 4 for:

- winner selected only by `val_select`;
- `val_eval` check-only;
- gates are numeric and predeclared;
- verdict cannot become trading candidate.

---

### Task 5: CLI And Canonical Run

**Files:**
- Modify: `ML/baseline/benchmark_direction_inside_frozen_movement_regime.py`
- Modify: `tests/test_direction_inside_frozen_movement_regime.py`
- Create artifacts:
  - `ML/reports/direction_inside_frozen_movement_regime.json`
  - `ML/reports/direction_inside_frozen_movement_regime_rows.csv`

**Interfaces:**
- Produces:
  - `build_arg_parser() -> argparse.ArgumentParser`
  - `run_cli(args: argparse.Namespace) -> dict[str, object]`
  - `main(argv: list[str] | None = None) -> int`

- [ ] **Step 1: Write CLI smoke test**

Add:

```python
def test_cli_smoke_writes_direction_artifacts(tmp_path: Path, monkeypatch):
    import ML.baseline.benchmark_direction_inside_frozen_movement_regime as module

    freeze_report_path = tmp_path / "freeze.json"
    scores_path = tmp_path / "scores.csv"
    output_prefix = tmp_path / "direction"
    freeze_report_path.write_text(json.dumps(_freeze_report()), encoding="utf-8")
    scores = pd.DataFrame(
        {
            "split": ["train", "train", "val_select", "val_select", "val_eval", "val_eval"],
            "time": [
                "2020-01-01 00:00:00",
                "2020-01-02 00:00:00",
                "2021-01-01 00:00:00",
                "2021-01-02 00:00:00",
                "2024-01-01 00:00:00",
                "2024-01-02 00:00:00",
            ],
            "year": [2020, 2020, 2021, 2021, 2024, 2024],
            "score": [10, 9, 8, 7, 6, 5],
            "entry_movement_3": [3, 3, 3, 3, 3, 3],
            "selected": [True, True, True, True, True, True],
        }
    )
    scores.to_csv(scores_path, index=False)
    splits = {
        "train": pd.DataFrame(
            {
                "time": ["2020-01-01 00:00:00", "2020-01-02 00:00:00"],
                "entry_up_3": [3.0, 1.0],
                "entry_dn_3": [1.0, 3.0],
                "ATR": [0.5, 0.6],
            }
        ),
        "val_select": pd.DataFrame(
            {
                "time": ["2021-01-01 00:00:00", "2021-01-02 00:00:00"],
                "entry_up_3": [3.0, 1.0],
                "entry_dn_3": [1.0, 3.0],
                "ATR": [0.5, 0.6],
            }
        ),
        "val_eval": pd.DataFrame(
            {
                "time": ["2024-01-01 00:00:00", "2024-01-02 00:00:00"],
                "entry_up_3": [3.0, 1.0],
                "entry_dn_3": [1.0, 3.0],
                "ATR": [0.5, 0.6],
            }
        ),
    }
    monkeypatch.setattr(module.amplitude, "load_entry_based_splits", lambda: splits)
    monkeypatch.setattr(
        module,
        "run_direction_baselines",
        lambda masked: {
            "profile": "simple_combined",
            "target": "target_direction_3",
            "baselines": {
                "majority_class": {"val_eval": {"total_n": 2, "balanced_accuracy": 0.5, "mcc": 0.0}},
                "extra_trees_small": {
                    "val_select": {"total_n": 120, "balanced_accuracy": 0.60, "mcc": 0.20},
                    "val_eval": {"total_n": 120, "balanced_accuracy": 0.57, "mcc": 0.10},
                },
            },
        },
    )

    exit_code = module.main(
        [
            "--freeze-report",
            str(freeze_report_path),
            "--freeze-scores",
            str(scores_path),
            "--output-prefix",
            str(output_prefix),
        ]
    )

    assert exit_code == 0
    assert Path(f"{output_prefix}.json").exists()
    assert Path(f"{output_prefix}_rows.csv").exists()
```

- [ ] **Step 2: Implement CLI**

Append:

```python
import argparse
import sys


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Direction diagnostics inside frozen movement regime")
    parser.add_argument("--freeze-report", required=True, help="Path to entry_based_movement_filter_freeze.json")
    parser.add_argument("--freeze-scores", required=True, help="Path to entry_based_movement_filter_freeze_scores.csv")
    parser.add_argument("--output-prefix", required=True, help="Output prefix for JSON/CSV artifacts")
    return parser


def run_cli(args: argparse.Namespace) -> dict[str, object]:
    loaded = load_frozen_mask(Path(args.freeze_report), Path(args.freeze_scores))
    contract = loaded["contract"]
    splits = amplitude.load_entry_based_splits()
    masked = build_masked_direction_dataset(splits, loaded["scores"])
    baseline_results = run_direction_baselines(masked) if contract["status"] == "PASS" else {"baselines": {}}
    selection = select_direction_rule(baseline_results)
    robustness = compute_direction_robustness(masked, baseline_results, selection) if selection.get("status") == "SELECTED" else {"status": "NOT_RUN"}
    verdict = decide_direction_verdict(contract, selection, robustness)
    report = build_report(contract, baseline_results, selection, robustness, verdict)
    report["artifact_hashes"] = {"freeze_scores_sha256": loaded["scores_hash"]}
    write_artifacts(report, build_rows_export(masked), Path(args.output_prefix))
    return report


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    report = run_cli(args)
    print(json.dumps({"verdict": report["verdict"]}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
```

- [ ] **Step 3: Run focused tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_direction_inside_frozen_movement_regime.py -q
```

Expected: all focused tests pass.

- [ ] **Step 4: Run canonical experiment**

Run:

```bash
./.venv/bin/python ML/baseline/benchmark_direction_inside_frozen_movement_regime.py \
  --freeze-report ML/reports/entry_based_movement_filter_freeze.json \
  --freeze-scores ML/reports/entry_based_movement_filter_freeze_scores.csv \
  --output-prefix ML/reports/direction_inside_frozen_movement_regime
```

Expected:

- `ML/reports/direction_inside_frozen_movement_regime.json` exists;
- `ML/reports/direction_inside_frozen_movement_regime_rows.csv` exists;
- JSON verdict is one of `ALLOWED_VERDICTS`;
- no `locked_test` artifact is created.

- [ ] **Step 5: Run full tests and graph update**

Run:

```bash
./.venv/bin/python -m pytest tests/ -q
graphify update .
```

Expected: full tests pass; graph update completes. Do not stage incidental `graphify-out/` churn unless explicitly required by project practice at that point.

- [ ] **Step 6: Review**

Ask a review subagent to check Task 5 and whole runner for:

- canonical paths and artifacts;
- no hidden `locked_test`;
- no PnL/PF;
- no direction winner chosen on `val_eval`.

---

### Task 6: Report, Docs, Wiki, And Branch Closure

**Files:**
- Create: `docs/reports/2026-07-08-direction-inside-frozen-movement-regime.md`
- Create: `docs/ML/benchmark_direction_inside_frozen_movement_regime.py.md`
- Modify: `CHANGELOG.md`
- Modify: `CONTEXT_HANDOFF.md`
- Modify: `MODULE_INDEX.md`
- Modify: `docs/tests/tests.md`
- Modify: `docs/superpowers/roadmap.md`
- Modify: `wiki/research/fractal-stop-research.md`
- Modify: `wiki/index.md`
- Modify: `wiki/log.md`

**Interfaces:**
- Consumes:
  - `ML/reports/direction_inside_frozen_movement_regime.json`
  - `ML/reports/direction_inside_frozen_movement_regime_rows.csv`
- Produces:
  - канонический отчёт с verdict, split disclosure, sample size, forbidden interpretations, next step.

- [ ] **Step 1: Write report from structured artifact**

Report must include:

- Context: previous movement filter freeze.
- Research level: `RESEARCH_ONLY`.
- Multiple Testing Context:
  - current search budget: exact number of direction baselines actually run;
  - cumulative lineage: amplitude search + movement filter search + movement freeze + current direction check.
- Split Disclosure:
  - train;
  - `val_select`;
  - `val_eval`;
  - `low_n_disclosure`;
  - `locked_test = not_opened`.
- Results:
  - selected N after removing ties by split;
  - class balance by split;
  - baseline metrics by split;
  - winner chosen on `val_select`;
  - `val_eval` check-only metrics.
- Robustness:
  - yearly/block stability checks for `val_eval`;
  - reasons if status is `RESEARCH_ONLY`;
  - exact `freeze_scores_sha256`;
  - exact count of baselines actually trained.
- Forbidden interpretations:
  - not trading candidate;
  - not PnL/PF;
  - not live rule;
  - no permission to open `locked_test` unless separate freeze contract says so.

- [ ] **Step 2: Update module docs**

Create `docs/ML/benchmark_direction_inside_frozen_movement_regime.py.md` with:

- purpose;
- inputs;
- outputs;
- target convention;
- forbidden input columns;
- CLI command;
- test command;
- limitations.

- [ ] **Step 3: Update project docs**

Use `update-docs` and `stage-reporting` skills for this task. Update only facts that changed:

- `CHANGELOG.md`: one entry for the new direction-inside-mask result.
- `CONTEXT_HANDOFF.md`: current state and next allowed step.
- `MODULE_INDEX.md`: add runner and tests.
- `docs/tests/tests.md`: add focused test file.
- `docs/superpowers/roadmap.md`: remove completed direction-inside-mask item if closed; add next step based on verdict.

- [ ] **Step 4: Update wiki**

Update:

- `wiki/research/fractal-stop-research.md`
- `wiki/index.md`
- `wiki/log.md`

Then run:

```bash
./.venv/bin/python wiki/wiki.py status
./.venv/bin/python wiki/wiki.py generate
./.venv/bin/python wiki/wiki.py status
```

Expected final status: `Wiki is up to date. No gaps found.`

- [ ] **Step 5: Final verification**

Run:

```bash
./.venv/bin/python -m pytest tests/test_direction_inside_frozen_movement_regime.py -q
./.venv/bin/python -m pytest tests/ -q
git diff --check
```

Expected:

- focused tests pass;
- full tests pass;
- whitespace check passes.

- [ ] **Step 6: Close stage and commit**

Use `stage-reporting` for closure and commit. Stage only files from this plan and required generated artifacts. Do not stage unrelated dirty files.

Run:

```bash
git status --short
git add ML/baseline/benchmark_direction_inside_frozen_movement_regime.py \
  tests/test_direction_inside_frozen_movement_regime.py \
  ML/reports/direction_inside_frozen_movement_regime.json \
  ML/reports/direction_inside_frozen_movement_regime_rows.csv \
  docs/reports/2026-07-08-direction-inside-frozen-movement-regime.md \
  docs/ML/benchmark_direction_inside_frozen_movement_regime.py.md \
  docs/superpowers/plans/2026-07-08-direction-inside-frozen-movement-regime.md \
  CHANGELOG.md CONTEXT_HANDOFF.md MODULE_INDEX.md docs/tests/tests.md \
  docs/superpowers/roadmap.md wiki/research/fractal-stop-research.md \
  wiki/index.md wiki/log.md wiki/REPO_integrity.md
git commit -m "Add direction inside frozen movement regime check"
```

Expected: `stage-reporting` closure is complete and commit succeeds. Do not push.

---

## Stop Conditions

- If contract validation fails: stop with `ABORT_CONTRACT_FAIL`; do not train direction baselines.
- If selected rows after tie removal are `<100` on `val_select` or `val_eval`: stop with reject; do not widen mask.
- If all simple baselines fail gates: close this direction branch; do not tune more models.
- If result only passes on `val_select` and fails `val_eval`: reject; do not reinterpret `val_eval`.
- If result passes point metrics but robustness is not `PASS`: maximum verdict is `RESEARCH_ONLY_DIRECTION_SIGNAL`.
- If result passes point metrics and robustness is `PASS`: create a separate freeze plan for direction rule before any `locked_test`.

## Self-Review Notes

- Scope covers only one subsystem: direction diagnostics inside the frozen movement mask.
- No task changes movement segmentation rule.
- No task opens `locked_test`.
- No task computes PnL/PF or claims trading readiness.
- Type names are consistent across tasks:
  - `target_direction_3`;
  - `build_masked_direction_dataset`;
  - `run_direction_baselines`;
  - `select_direction_rule`;
  - `decide_direction_verdict`.
