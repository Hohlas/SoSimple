# Stage 5.3 Time-To-Breach Target Reformulation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Проверить, даёт ли дискретная постановка времени до пробоя (`breach_after_k`, `fast/medium/no breach`) более честный сигнал, чем обычная регрессия `bars_to_breach`.

**Architecture:** Stage 5.3 переиспользует уже созданные Stage 5.2 колонки `*_bars_to_breach_H6_off05`, fixed split Stage 5.x и `build_stage5_2_features()`. Новый код добавляет производные бинарные цели, binary breach baseline в тех же условиях обучения, классификационные метрики, сводку по target-family и отдельный CLI/JSON; новые price-признаки, Up/Dn и новый oracle-PF не входят в этот этап.

**Tech Stack:** Python 3.10, pandas, numpy, scikit-learn metrics, XGBoost classifier, pytest, JSON reports.

## Global Constraints

- Работать в текущей feature-ветке; worktree запрещён `AGENTS.md`.
- Использовать Python окружение проекта: `./.venv/bin/python`.
- После изменений в Python-коде запускать `./.venv/bin/python -m pytest tests/ -q`.
- Для ML-infrastructure изменений применять TDD: сначала failing test, затем код.
- Stage 5.3 не может объявлять торгового кандидата: `2021-2022` используются для выбора winner-а, `2023-2025` только diagnostic disclosure.
- Не добавлять `price`, `price_coord_atr`, `price_atr_scaled`, raw `ATR` и Up/Dn в Stage 5.3. Это отдельный следующий этап после проверки постановки цели.
- Не использовать oracle-time PF как gate. Stage 5.2 показал, что сравнение с binary-oracle в текущем виде невалидно.
- Основные source targets: `sell_bars_to_breach_H6_off05`, `buy_bars_to_breach_H6_off05`.
- Основной горизонт: `H=6`, censored value: `7`, seed list: `[42, 77, 123]`.
- Feature profiles заморожены: `time_only`, `clock_shift`, `clock_shift_back`, `clock_shift_impulse`, `clock_shift_back_impulse`, `structure_full`.
- Main target specs: `breach_after_k` для `k = 2, 3, 4, 5`; bucket one-vs-rest: `fast`, `medium`, `no_breach`.
- Baseline target spec: binary breach (`*_stop_broken_H6_off05_flag`) обучается внутри Stage 5.3 в тех же условиях и не может стать winner-ом.
- Control target specs: `survives_at_least_k` для `k = 2, 3, 4, 5`. Control-цели обучаются и раскрываются, но не могут стать winner-ом этапа, потому что censored observations (`bars_to_breach = 7`, 61-63% строк в Stage 5.2) все становятся positive и модель может учиться "не пробито", а не времени жизни уровня.
- Search budget: `2 source targets × 12 target specs × 6 profiles × 3 seed = 432` XGBoost-классификации. Main budget без controls и binary baseline: `252` классификации.
- XGBoost classifier должен использовать Stage 5.1-compatible режим: `xgb.train`, `max_depth=6`, `num_boost_round=500`, `early_stopping_rounds=20`, `subsample=0.8`, `colsample_bytree=0.8`, `eval_metric=auc`.
- Multiple testing disclosure обязателен: 14 main target/side comparisons, сгруппированные как `breach_after_k` и `bucket`; gate использует conservative thresholds, но отчёт всё равно должен раскрыть отсутствие строгой независимой проверки.
- Статусы JSON: `TARGET_REFORMULATION_FOUND` или `DIAGNOSTIC_ONLY`.

---

## File Structure

- Modify: `ML/baseline/benchmark_stage5_transformer_breach.py`
  - Add Stage 5.3 constants, target builders, binary metrics, Stage 5.1-compatible XGBoost classifier evaluator, summary, gate, runner and CLI fast path.
- Modify: `tests/test_stage5_transformer_breach.py`
  - Add unit/smoke tests for Stage 5.3 target builders, metrics, evaluator, runner and CLI.
- Create after full run: `ML/reports/stage5_3_time_to_breach_target_reformulation.json`
  - Structured artifact полного Stage 5.3 прогона.
- Create after full run: `docs/reports/2026-06-26-stage5_3-time-to-breach-target-reformulation.md`
  - Канонический отчёт после JSON, не в этом implementation-plan.

---

### Task 1: Stage 5.3 Target Specs And Builders

**Files:**
- Modify: `ML/baseline/benchmark_stage5_transformer_breach.py`
- Test: `tests/test_stage5_transformer_breach.py`

**Interfaces:**
- Produces: `STAGE5_3_JSON_REPORT_PATH: Path`
- Produces: `STAGE5_3_SOURCE_TARGETS: list[str]`
- Produces: `STAGE5_3_PROFILE_KEYS: list[str]`
- Produces: `STAGE5_3_MAIN_TARGET_SPECS: list[dict]`
- Produces: `STAGE5_3_BINARY_BASELINE_SPECS: list[dict]`
- Produces: `STAGE5_3_CONTROL_TARGET_SPECS: list[dict]`
- Produces: `stage5_3_target_id(source_target: str, spec: dict) -> str`
- Produces: `stage5_3_make_binary_target(values, spec: dict) -> np.ndarray`
- Produces: `stage5_3_make_binary_target_from_frame(df: pd.DataFrame, source_target: str, spec: dict) -> np.ndarray`
- Produces: `stage5_3_target_distribution(split: dict, source_target: str, spec: dict) -> dict`

- [ ] **Step 1: Write failing tests for constants and target builders**

Append near the Stage 5.2 tests in `tests/test_stage5_transformer_breach.py`:

```python
def test_stage5_3_constants_and_target_specs_are_frozen():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    assert runner.STAGE5_3_SOURCE_TARGETS == [
        "sell_bars_to_breach_H6_off05",
        "buy_bars_to_breach_H6_off05",
    ]
    assert runner.STAGE5_3_PROFILE_KEYS == [
        "time_only",
        "clock_shift",
        "clock_shift_back",
        "clock_shift_impulse",
        "clock_shift_back_impulse",
        "structure_full",
    ]
    assert [s["name"] for s in runner.STAGE5_3_MAIN_TARGET_SPECS] == [
        "breach_after_k2",
        "breach_after_k3",
        "breach_after_k4",
        "breach_after_k5",
        "fast",
        "medium",
        "no_breach",
    ]
    assert [s["name"] for s in runner.STAGE5_3_BINARY_BASELINE_SPECS] == [
        "binary_breach",
    ]
    assert [s["name"] for s in runner.STAGE5_3_CONTROL_TARGET_SPECS] == [
        "survives_at_least_k2",
        "survives_at_least_k3",
        "survives_at_least_k4",
        "survives_at_least_k5",
    ]
    assert str(runner.STAGE5_3_JSON_REPORT_PATH).endswith(
        "stage5_3_time_to_breach_target_reformulation.json"
    )


def test_stage5_3_make_binary_target_for_breach_after_k_and_buckets():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    y = np.array([1, 2, 3, 4, 5, 6, 7, np.nan], dtype=float)

    assert runner.stage5_3_make_binary_target(
        y, {"family": "breach_after_k", "k": 3}
    ).tolist() == [0, 0, 0, 1, 1, 1, 0, -1]
    assert runner.stage5_3_make_binary_target(
        y, {"family": "survives_at_least_k", "k": 3}
    ).tolist() == [0, 0, 0, 1, 1, 1, 1, -1]
    assert runner.stage5_3_make_binary_target(
        y, {"family": "bucket", "bucket": "fast"}
    ).tolist() == [1, 1, 0, 0, 0, 0, 0, -1]
    assert runner.stage5_3_make_binary_target(
        y, {"family": "bucket", "bucket": "medium"}
    ).tolist() == [0, 0, 1, 1, 1, 1, 0, -1]
    assert runner.stage5_3_make_binary_target(
        y, {"family": "bucket", "bucket": "no_breach"}
    ).tolist() == [0, 0, 0, 0, 0, 0, 1, -1]


def test_stage5_3_make_binary_target_from_frame_for_binary_breach_baseline():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    df = pd.DataFrame({
        "sell_bars_to_breach_H6_off05": [1, 7, 4, np.nan],
        "sell_stop_broken_H6_off05_flag": [1.0, 0.0, 1.0, np.nan],
    })

    y = runner.stage5_3_make_binary_target_from_frame(
        df,
        "sell_bars_to_breach_H6_off05",
        {"name": "binary_breach", "family": "binary_breach", "role": "baseline"},
    )

    assert y.tolist() == [1, 0, 1, -1]
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_stage5_3_constants_and_target_specs_are_frozen tests/test_stage5_transformer_breach.py::test_stage5_3_make_binary_target_for_breach_after_k_and_buckets tests/test_stage5_transformer_breach.py::test_stage5_3_make_binary_target_from_frame_for_binary_breach_baseline -q
```

Expected: FAIL because Stage 5.3 constants/functions do not exist yet.

- [ ] **Step 3: Add Stage 5.3 constants and target builders**

Add after the Stage 5.2 constants in `ML/baseline/benchmark_stage5_transformer_breach.py`:

```python
STAGE5_3_JSON_REPORT_PATH = REPORTS_DIR / "stage5_3_time_to_breach_target_reformulation.json"
STAGE5_3_SOURCE_TARGETS = STAGE5_2_TARGETS.copy()
STAGE5_3_HORIZON = STAGE5_2_HORIZON
STAGE5_3_CENSORED_VALUE = STAGE5_2_CENSORED_VALUE
STAGE5_3_SEEDS = STAGE5_2_SEEDS.copy()
STAGE5_3_PROFILE_KEYS = [
    "time_only",
    "clock_shift",
    "clock_shift_back",
    "clock_shift_impulse",
    "clock_shift_back_impulse",
    "structure_full",
]
STAGE5_3_MAIN_TARGET_SPECS = [
    {"name": "breach_after_k2", "family": "breach_after_k", "k": 2, "role": "main"},
    {"name": "breach_after_k3", "family": "breach_after_k", "k": 3, "role": "main"},
    {"name": "breach_after_k4", "family": "breach_after_k", "k": 4, "role": "main"},
    {"name": "breach_after_k5", "family": "breach_after_k", "k": 5, "role": "main"},
    {"name": "fast", "family": "bucket", "bucket": "fast", "role": "main"},
    {"name": "medium", "family": "bucket", "bucket": "medium", "role": "main"},
    {"name": "no_breach", "family": "bucket", "bucket": "no_breach", "role": "main"},
]
STAGE5_3_BINARY_BASELINE_SPECS = [
    {"name": "binary_breach", "family": "binary_breach", "role": "baseline"},
]
STAGE5_3_CONTROL_TARGET_SPECS = [
    {"name": "survives_at_least_k2", "family": "survives_at_least_k", "k": 2, "role": "control"},
    {"name": "survives_at_least_k3", "family": "survives_at_least_k", "k": 3, "role": "control"},
    {"name": "survives_at_least_k4", "family": "survives_at_least_k", "k": 4, "role": "control"},
    {"name": "survives_at_least_k5", "family": "survives_at_least_k", "k": 5, "role": "control"},
]
STAGE5_3_TARGET_SPECS = (
    STAGE5_3_MAIN_TARGET_SPECS
    + STAGE5_3_BINARY_BASELINE_SPECS
    + STAGE5_3_CONTROL_TARGET_SPECS
)
STAGE5_3_XGB_OBJECTIVE = "binary:logistic"
STAGE5_3_TARGET_TO_BINARY = STAGE5_2_TARGET_TO_BINARY.copy()
```

Add near the Stage 5.2 metrics helpers:

```python
def stage5_3_target_id(source_target: str, spec: dict) -> str:
    side = "sell" if source_target.startswith("sell_") else "buy"
    return f"{side}_{spec['name']}"


def stage5_3_make_binary_target(values, spec: dict) -> np.ndarray:
    y = np.asarray(values, dtype=float)
    out = np.full(len(y), -1, dtype=np.int8)
    valid = np.isfinite(y)
    family = spec["family"]
    if family == "breach_after_k":
        k = int(spec["k"])
        out[valid] = ((y[valid] > k) & (y[valid] <= STAGE5_3_HORIZON)).astype(np.int8)
    elif family == "survives_at_least_k":
        k = int(spec["k"])
        out[valid] = (y[valid] > k).astype(np.int8)
    elif family == "bucket":
        bucket = spec["bucket"]
        if bucket == "fast":
            out[valid] = ((y[valid] >= 1) & (y[valid] <= 2)).astype(np.int8)
        elif bucket == "medium":
            out[valid] = ((y[valid] >= 3) & (y[valid] <= STAGE5_3_HORIZON)).astype(np.int8)
        elif bucket == "no_breach":
            out[valid] = (y[valid] >= STAGE5_3_CENSORED_VALUE).astype(np.int8)
        else:
            raise ValueError(f"Unknown Stage 5.3 bucket: {bucket}")
    else:
        raise ValueError(f"Unknown Stage 5.3 target family: {family}")
    return out


def stage5_3_make_binary_target_from_frame(df: pd.DataFrame, source_target: str,
                                           spec: dict) -> np.ndarray:
    if spec["family"] == "binary_breach":
        binary_col = STAGE5_3_TARGET_TO_BINARY[source_target]
        vals = pd.to_numeric(df[binary_col], errors="coerce").to_numpy(dtype=float)
        out = np.full(len(vals), -1, dtype=np.int8)
        valid = np.isfinite(vals)
        out[valid] = vals[valid].astype(np.int8)
        return out
    return stage5_3_make_binary_target(df[source_target].to_numpy(), spec)


def stage5_3_target_distribution(split: dict, source_target: str, spec: dict) -> dict:
    out = {}
    for split_name, df in split.items():
        if not isinstance(df, pd.DataFrame) or source_target not in df:
            continue
        y = stage5_3_make_binary_target_from_frame(df, source_target, spec)
        valid = y >= 0
        yv = y[valid]
        out[split_name] = {
            "n": int(len(yv)),
            "positive_count": int(yv.sum()) if len(yv) else 0,
            "positive_rate": float(yv.mean()) if len(yv) else None,
            "invalid_count": int((~valid).sum()),
        }
    return out
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_stage5_3_constants_and_target_specs_are_frozen tests/test_stage5_transformer_breach.py::test_stage5_3_make_binary_target_for_breach_after_k_and_buckets tests/test_stage5_transformer_breach.py::test_stage5_3_make_binary_target_from_frame_for_binary_breach_baseline -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add ML/baseline/benchmark_stage5_transformer_breach.py tests/test_stage5_transformer_breach.py
git commit -m "feat: add stage 5.3 target specs"
```

---

### Task 2: Stage 5.3 Binary Metrics And Gate

**Files:**
- Modify: `ML/baseline/benchmark_stage5_transformer_breach.py`
- Test: `tests/test_stage5_transformer_breach.py`

**Interfaces:**
- Consumes: `stage5_3_make_binary_target(values, spec)`
- Produces: `stage5_3_binary_metrics(y_true, y_score, threshold: float = 0.5) -> dict`
- Produces: `stage5_3_gate_results(summary: dict) -> dict`

- [ ] **Step 1: Write failing tests for metrics and gate**

Append:

```python
def test_stage5_3_binary_metrics_include_auc_pr_auc_and_threshold_counts():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    y_true = np.array([0, 0, 1, 1], dtype=int)
    y_score = np.array([0.1, 0.3, 0.7, 0.9], dtype=float)

    metrics = runner.stage5_3_binary_metrics(y_true, y_score)

    assert metrics["n"] == 4
    assert metrics["positive_rate"] == pytest.approx(0.5)
    assert metrics["auc"] == pytest.approx(1.0)
    assert metrics["pr_auc"] == pytest.approx(1.0)
    assert metrics["pred_summary"]["std"] > 0.0
    assert metrics["threshold_0_5"]["predicted_positive"] == 2
    assert metrics["threshold_0_5"]["precision"] == pytest.approx(1.0)
    assert metrics["threshold_0_5"]["recall"] == pytest.approx(1.0)


def test_stage5_3_gate_requires_main_target_auc_lift_and_yearly_consistency():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    summary = {
        "best_main": {
            "target_id": "sell_breach_after_k3",
            "spec": {"role": "main"},
            "profile": "clock_shift_back",
            "val_stop": {
                "auc": 0.70,
                "pr_auc": 0.42,
                "positive_rate": 0.30,
                "yearly": {"2021": {"auc": 0.61}, "2022": {"auc": 0.62}},
            },
            "binary_breach_baseline": {"same_profile_val_auc": 0.66, "auc_delta": 0.04},
            "improvement_vs_time_only": {"auc_delta": 0.04},
            "improvement_vs_clock_shift": {"auc_delta": 0.05},
            "seed_consistency": {"auc_delta_vs_binary_positive_count": 2, "n_seeds": 3},
        }
    }

    gate = runner.stage5_3_gate_results(summary)

    assert gate["overall_status"] == "TARGET_REFORMULATION_FOUND"
    assert gate["model_gate"]["pass"] is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_stage5_3_binary_metrics_include_auc_pr_auc_and_threshold_counts tests/test_stage5_transformer_breach.py::test_stage5_3_gate_requires_main_target_auc_lift_and_yearly_consistency -q
```

Expected: FAIL because metrics/gate do not exist.

- [ ] **Step 3: Implement metrics and gate**

Add near Stage 5.2 metrics:

```python
def stage5_3_binary_metrics(y_true, y_score, threshold: float = 0.5) -> dict:
    yt = np.asarray(y_true, dtype=int)
    ys = np.asarray(y_score, dtype=float)
    valid = np.isfinite(ys) & np.isin(yt, [0, 1])
    yt = yt[valid]
    ys = ys[valid]
    pred = ys >= threshold
    positives = int(yt.sum())
    predicted_positive = int(pred.sum())
    auc = None
    pr_auc = None
    if len(np.unique(yt)) == 2:
        try:
            auc = float(roc_auc_score(yt, ys))
        except ValueError:
            auc = 0.5
        try:
            pr_auc = float(average_precision_score(yt, ys))
        except ValueError:
            pr_auc = float(yt.mean()) if len(yt) else None
    return {
        "n": int(len(yt)),
        "positive_count": positives,
        "positive_rate": float(yt.mean()) if len(yt) else None,
        "auc": auc,
        "pr_auc": pr_auc,
        "pred_summary": {
            "min": float(np.min(ys)) if len(ys) else None,
            "median": float(np.median(ys)) if len(ys) else None,
            "max": float(np.max(ys)) if len(ys) else None,
            "std": float(np.std(ys)) if len(ys) else None,
            "unique_rounded_4": int(len(np.unique(np.round(ys, 4)))) if len(ys) else 0,
        },
        "threshold_0_5": {
            "threshold": float(threshold),
            "predicted_positive": predicted_positive,
            "precision": float(np.mean(yt[pred])) if predicted_positive else None,
            "recall": float(np.sum(yt[pred]) / max(positives, 1)),
        },
    }


def stage5_3_gate_results(summary: dict) -> dict:
    best = summary.get("best_main") or {}
    val = best.get("val_stop") or {}
    yearly = val.get("yearly") or {}
    pos_rate = val.get("positive_rate")
    pr_auc = val.get("pr_auc")
    pr_lift = None
    if pr_auc is not None and pos_rate is not None:
        pr_lift = pr_auc - pos_rate
    yearly_pass = (
        len(yearly) >= 2
        and sum(1 for row in yearly.values() if (row.get("auc") or 0.0) >= 0.60) >= 2
    )
    binary = best.get("binary_breach_baseline") or {}
    seed_consistency = best.get("seed_consistency") or {}
    checks = {
        "main_target_only": ((best.get("spec") or {}).get("role") == "main"),
        "positive_rate_between_0_05_0_95": pos_rate is not None and 0.05 <= pos_rate <= 0.95,
        "auc_ge_0_65": (val.get("auc") or 0.0) >= 0.65,
        "pr_auc_lift_ge_0_05": pr_lift is not None and pr_lift >= 0.05,
        "auc_delta_binary_breach_same_profile_ge_0_02": (binary.get("auc_delta") or 0.0) >= 0.02,
        "auc_delta_time_only_ge_0_03": ((best.get("improvement_vs_time_only") or {}).get("auc_delta") or 0.0) >= 0.03,
        "auc_delta_clock_shift_ge_0_03": ((best.get("improvement_vs_clock_shift") or {}).get("auc_delta") or 0.0) >= 0.03,
        "seed_delta_binary_positive_ge_2_of_3": (seed_consistency.get("auc_delta_vs_binary_positive_count") or 0) >= 2,
        "yearly_not_single_year": yearly_pass,
    }
    passed = all(checks.values())
    return {
        "overall_status": "TARGET_REFORMULATION_FOUND" if passed else "DIAGNOSTIC_ONLY",
        "model_gate": {
            "pass": bool(passed),
            "checks": checks,
            "pr_auc_lift": pr_lift,
            "multiple_testing_note": "14 main comparisons across 2 sides; target families are correlated, so this is diagnostic evidence, not candidate validation.",
        },
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_stage5_3_binary_metrics_include_auc_pr_auc_and_threshold_counts tests/test_stage5_transformer_breach.py::test_stage5_3_gate_requires_main_target_auc_lift_and_yearly_consistency -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add ML/baseline/benchmark_stage5_transformer_breach.py tests/test_stage5_transformer_breach.py
git commit -m "feat: add stage 5.3 metrics and gate"
```

---

### Task 3: Stage 5.3 Evaluator And Summary

**Files:**
- Modify: `ML/baseline/benchmark_stage5_transformer_breach.py`
- Test: `tests/test_stage5_transformer_breach.py`

**Interfaces:**
- Consumes: `build_stage5_2_features(df, profile_key)`
- Consumes: `stage5_3_binary_metrics(y_true, y_score)`
- Produces: `evaluate_stage5_3_profile_seed(split: dict, source_target: str, spec: dict, profile_key: str, seed: int, xgb_threads: int = 1) -> dict`
- Produces: `summarize_stage5_3_source(raw_runs: list[dict], source_target: str) -> dict`

- [ ] **Step 1: Write failing evaluator and summary tests**

Append:

```python
def test_evaluate_stage5_3_profile_seed_returns_binary_metrics(monkeypatch):
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    df = _make_stage5_0f_year_df()
    df["sell_bars_to_breach_H6_off05"] = np.where(
        df["sell_stop_broken_H6_off05_flag"] == 1.0, 4, 7
    )
    split = runner.build_stage5_1_split(df, "sell_bars_to_breach_H6_off05")
    spec = {"name": "breach_after_k3", "family": "breach_after_k", "k": 3, "role": "main"}

    result = runner.evaluate_stage5_3_profile_seed(
        split,
        "sell_bars_to_breach_H6_off05",
        spec,
        "clock_shift_back",
        seed=42,
    )

    assert result["source_target"] == "sell_bars_to_breach_H6_off05"
    assert result["target_id"] == "sell_breach_after_k3"
    assert result["profile"] == "clock_shift_back"
    assert result["seed"] == 42
    assert "auc" in result["val_stop"]
    assert "pr_auc" in result["val_stop"]
    assert "yearly_val" in result
    assert "predictions" in result
    assert "labels" in result
    assert "feature_importance_gain_top20" in result


def test_summarize_stage5_3_source_selects_best_main_and_keeps_controls():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    source = "sell_bars_to_breach_H6_off05"
    raw_runs = []
    for target_id, role, profile, auc in [
        ("sell_breach_after_k3", "main", "time_only", 0.58),
        ("sell_breach_after_k3", "main", "clock_shift_back", 0.69),
        ("sell_binary_breach", "baseline", "clock_shift_back", 0.66),
        ("sell_survives_at_least_k3", "control", "clock_shift_back", 0.75),
    ]:
        raw_runs.append({
            "source_target": source,
            "target_id": target_id,
            "spec": {"name": target_id.replace("sell_", ""), "role": role},
            "profile": profile,
            "seed": 42,
            "val_stop": {"auc": auc, "pr_auc": 0.40, "positive_rate": 0.30},
            "diagnostic_holdout": {"auc": auc - 0.05, "pr_auc": 0.35, "positive_rate": 0.30},
            "yearly_val": {"2021": {"auc": 0.61}, "2022": {"auc": 0.62}},
        })

    summary = runner.summarize_stage5_3_source(raw_runs, source)

    assert summary["best_main"]["target_id"] == "sell_breach_after_k3"
    assert summary["best_main"]["profile"] == "clock_shift_back"
    assert summary["best_control"]["target_id"] == "sell_survives_at_least_k3"
    assert summary["best_main"]["improvement_vs_time_only"]["auc_delta"] == pytest.approx(0.11)
    assert summary["best_main"]["binary_breach_baseline"]["auc_delta"] == pytest.approx(0.03)
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_evaluate_stage5_3_profile_seed_returns_binary_metrics tests/test_stage5_transformer_breach.py::test_summarize_stage5_3_source_selects_best_main_and_keeps_controls -q
```

Expected: FAIL because evaluator/summary do not exist.

- [ ] **Step 3: Implement evaluator helpers**

Add near Stage 5.2 evaluator:

```python
def _stage5_3_yearly_metrics(df: pd.DataFrame, source_target: str,
                             spec: dict, score: np.ndarray) -> dict:
    if "_year" not in df:
        return {}
    out = {}
    score = np.asarray(score, dtype=float)
    for year, idx in df.groupby("_year").groups.items():
        positions = df.index.get_indexer(idx)
        y = stage5_3_make_binary_target_from_frame(df.loc[idx], source_target, spec)
        out[str(int(year))] = stage5_3_binary_metrics(y, score[positions])
    return out


def _stage5_3_feature_importance_top20(model) -> list[dict]:
    score = model.get_score(importance_type="gain")
    rows = [
        {"feature": str(feature), "gain": float(gain)}
        for feature, gain in score.items()
    ]
    rows.sort(key=lambda row: row["gain"], reverse=True)
    return rows[:20]


def evaluate_stage5_3_profile_seed(split: dict, source_target: str, spec: dict,
                                   profile_key: str, seed: int,
                                   xgb_threads: int = 1) -> dict:
    started_at = time.time()
    train = split["train_core"]
    val = split["val_stop"]
    holdout = split["diagnostic_holdout"]
    low_n = split["low_n_disclosure"]
    X_train = build_stage5_2_features(train, profile_key)
    X_val = build_stage5_2_features(val, profile_key)
    X_holdout = build_stage5_2_features(holdout, profile_key)
    X_low_n = build_stage5_2_features(low_n, profile_key) if len(low_n) else None

    y_train = stage5_3_make_binary_target_from_frame(train, source_target, spec)
    train_valid = y_train >= 0
    X_train = X_train[train_valid]
    y_train = y_train[train_valid]
    positives = int(y_train.sum())
    negatives = int(len(y_train) - positives)
    scale_pos_weight = float(negatives / max(positives, 1))

    y_val = stage5_3_make_binary_target_from_frame(val, source_target, spec)
    val_valid = y_val >= 0
    dtrain = xgb.DMatrix(X_train, label=y_train)
    dval = xgb.DMatrix(X_val[val_valid], label=y_val[val_valid])
    params = {
        "objective": STAGE5_3_XGB_OBJECTIVE,
        "eval_metric": "auc",
        "max_depth": 6,
        "learning_rate": 0.05,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "scale_pos_weight": scale_pos_weight,
        "seed": seed,
        "n_jobs": int(xgb_threads),
        "verbosity": 0,
    }
    model = xgb.train(
        params,
        dtrain,
        num_boost_round=500,
        evals=[(dtrain, "train"), (dval, "val")],
        early_stopping_rounds=20,
        verbose_eval=False,
    )
    val_score = model.predict(xgb.DMatrix(X_val))
    holdout_score = model.predict(xgb.DMatrix(X_holdout))
    low_n_score = model.predict(xgb.DMatrix(X_low_n)) if X_low_n is not None else np.asarray([])

    y_holdout = stage5_3_make_binary_target_from_frame(holdout, source_target, spec)
    y_low_n = stage5_3_make_binary_target_from_frame(low_n, source_target, spec) if len(low_n) else np.asarray([])
    return {
        "source_target": source_target,
        "target_id": stage5_3_target_id(source_target, spec),
        "spec": dict(spec),
        "profile": profile_key,
        "seed": int(seed),
        "elapsed_sec": round(time.time() - started_at, 3),
        "train_core": {
            "n": int(len(y_train)),
            "positive_rate": float(y_train.mean()) if len(y_train) else None,
            "scale_pos_weight": scale_pos_weight,
            "best_iteration": int(model.best_iteration) if model.best_iteration is not None else None,
        },
        "val_stop": stage5_3_binary_metrics(y_val, val_score),
        "diagnostic_holdout": stage5_3_binary_metrics(y_holdout, holdout_score),
        "low_n_disclosure": stage5_3_binary_metrics(y_low_n, low_n_score) if len(y_low_n) else {"n": 0},
        "yearly_val": _stage5_3_yearly_metrics(val, source_target, spec, val_score),
        "yearly_diagnostic_holdout": _stage5_3_yearly_metrics(holdout, source_target, spec, holdout_score),
        "predictions": {
            "val_stop": [float(v) for v in val_score],
            "diagnostic_holdout": [float(v) for v in holdout_score],
            "low_n_disclosure": [float(v) for v in low_n_score],
        },
        "labels": {
            "val_stop": [int(v) for v in y_val.tolist()],
            "diagnostic_holdout": [int(v) for v in y_holdout.tolist()],
            "low_n_disclosure": [int(v) for v in y_low_n.tolist()],
        },
        "feature_importance_gain_top20": _stage5_3_feature_importance_top20(model),
    }
```

- [ ] **Step 4: Implement summary**

Add:

```python
def _stage5_3_profile_summary(runs: list[dict]) -> dict:
    return {
        "n_seed_runs": len(runs),
        "val_stop": {
            "auc": _median_metric(runs, "val_stop", "auc"),
            "pr_auc": _median_metric(runs, "val_stop", "pr_auc"),
            "positive_rate": _median_metric(runs, "val_stop", "positive_rate"),
            "yearly": _median_yearly_metric(runs, "yearly_val", "auc"),
        },
        "diagnostic_holdout": {
            "auc": _median_metric(runs, "diagnostic_holdout", "auc"),
            "pr_auc": _median_metric(runs, "diagnostic_holdout", "pr_auc"),
            "positive_rate": _median_metric(runs, "diagnostic_holdout", "positive_rate"),
            "yearly": _median_yearly_metric(runs, "yearly_diagnostic_holdout", "auc"),
        },
    }


def summarize_stage5_3_source(raw_runs: list[dict], source_target: str) -> dict:
    source_runs = [r for r in raw_runs if r.get("source_target") == source_target]
    targets = {}
    for target_id in sorted({r.get("target_id") for r in source_runs}):
        target_runs = [r for r in source_runs if r.get("target_id") == target_id]
        if not target_runs:
            continue
        spec = target_runs[0].get("spec") or {}
        profiles = {}
        for profile in STAGE5_3_PROFILE_KEYS:
            runs = [r for r in target_runs if r.get("profile") == profile]
            if runs:
                row = _stage5_3_profile_summary(runs)
                row["profile"] = profile
                profiles[profile] = row
        best_profile = max(
            profiles.values(),
            key=lambda row: (row.get("val_stop") or {}).get("auc") or -999.0,
        ) if profiles else {}
        if best_profile:
            best_auc = (best_profile.get("val_stop") or {}).get("auc")
            time_auc = ((profiles.get("time_only") or {}).get("val_stop") or {}).get("auc")
            clock_auc = ((profiles.get("clock_shift") or {}).get("val_stop") or {}).get("auc")
            best_profile["target_id"] = target_id
            best_profile["spec"] = spec
            best_profile["improvement_vs_time_only"] = {
                "auc_delta": None if best_auc is None or time_auc is None else best_auc - time_auc
            }
            best_profile["improvement_vs_clock_shift"] = {
                "auc_delta": None if best_auc is None or clock_auc is None else best_auc - clock_auc
            }
        targets[target_id] = {
            "target_id": target_id,
            "spec": spec,
            "profiles": profiles,
            "best_profile": best_profile,
        }

    best_main = max(
        [t["best_profile"] for t in targets.values()
         if ((t.get("spec") or {}).get("role") == "main") and t.get("best_profile")],
        key=lambda row: (row.get("val_stop") or {}).get("auc") or -999.0,
        default={},
    )
    best_control = max(
        [t["best_profile"] for t in targets.values()
         if ((t.get("spec") or {}).get("role") == "control") and t.get("best_profile")],
        key=lambda row: (row.get("val_stop") or {}).get("auc") or -999.0,
        default={},
    )
    binary_target = next(
        (t for t in targets.values() if ((t.get("spec") or {}).get("role") == "baseline")),
        {},
    )
    if best_main and binary_target:
        profile = best_main.get("profile")
        binary_profile = ((binary_target.get("profiles") or {}).get(profile) or {})
        binary_auc = ((binary_profile.get("val_stop") or {}).get("auc"))
        best_auc = ((best_main.get("val_stop") or {}).get("auc"))
        best_main["binary_breach_baseline"] = {
            "same_profile_val_auc": binary_auc,
            "auc_delta": None if best_auc is None or binary_auc is None else best_auc - binary_auc,
        }
        main_seed_runs = [
            r for r in source_runs
            if r.get("target_id") == best_main.get("target_id") and r.get("profile") == profile
        ]
        binary_seed_runs = {
            int(r.get("seed")): r
            for r in source_runs
            if r.get("target_id") == binary_target.get("target_id") and r.get("profile") == profile
        }
        positive = 0
        comparable = 0
        for run in main_seed_runs:
            seed = int(run.get("seed"))
            base = binary_seed_runs.get(seed)
            if not base:
                continue
            main_auc = ((run.get("val_stop") or {}).get("auc"))
            base_auc = ((base.get("val_stop") or {}).get("auc"))
            if main_auc is None or base_auc is None:
                continue
            comparable += 1
            if main_auc > base_auc:
                positive += 1
        best_main["seed_consistency"] = {
            "auc_delta_vs_binary_positive_count": int(positive),
            "n_seeds": int(comparable),
        }
    return {
        "source_target": source_target,
        "targets": targets,
        "best_main": best_main,
        "best_control": best_control,
    }
```

- [ ] **Step 5: Run tests to verify they pass**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_evaluate_stage5_3_profile_seed_returns_binary_metrics tests/test_stage5_transformer_breach.py::test_summarize_stage5_3_source_selects_best_main_and_keeps_controls -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add ML/baseline/benchmark_stage5_transformer_breach.py tests/test_stage5_transformer_breach.py
git commit -m "feat: add stage 5.3 classifier evaluator"
```

---

### Task 4: Stage 5.3 Runner, JSON And CLI

**Files:**
- Modify: `ML/baseline/benchmark_stage5_transformer_breach.py`
- Test: `tests/test_stage5_transformer_breach.py`

**Interfaces:**
- Consumes: `evaluate_stage5_3_profile_seed(...)`
- Consumes: `summarize_stage5_3_source(...)`
- Produces: `run_stage5_3_target_reformulation(target_splits: dict, output_path: Path = STAGE5_3_JSON_REPORT_PATH, workers: int = 1, xgb_threads: int = 1) -> dict`
- Adds CLI flags: `--stage5-3-target-reformulation`, `--stage5-3-workers`, `--stage5-3-xgb-threads`

- [ ] **Step 1: Write failing runner and CLI tests**

Append:

```python
def test_stage5_3_runner_writes_json(monkeypatch, tmp_path):
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    df = _make_stage5_0f_year_df()
    df["sell_bars_to_breach_H6_off05"] = np.where(
        df["sell_stop_broken_H6_off05_flag"] == 1.0, 4, 7
    )
    df["buy_bars_to_breach_H6_off05"] = np.where(
        df["buy_stop_broken_H6_off05_flag"] == 1.0, 4, 7
    )
    monkeypatch.setattr(runner, "STAGE5_3_MAIN_TARGET_SPECS", [
        {"name": "breach_after_k3", "family": "breach_after_k", "k": 3, "role": "main"}
    ])
    monkeypatch.setattr(runner, "STAGE5_3_CONTROL_TARGET_SPECS", [])
    monkeypatch.setattr(runner, "STAGE5_3_BINARY_BASELINE_SPECS", [])
    monkeypatch.setattr(runner, "STAGE5_3_TARGET_SPECS", runner.STAGE5_3_MAIN_TARGET_SPECS)
    monkeypatch.setattr(runner, "STAGE5_3_PROFILE_KEYS", ["time_only", "clock_shift_back"])
    monkeypatch.setattr(runner, "STAGE5_3_SEEDS", [42])
    monkeypatch.setattr(
        runner,
        "evaluate_stage5_3_profile_seed",
        lambda split, source_target, spec, profile, seed, xgb_threads=1: {
            "source_target": source_target,
            "target_id": runner.stage5_3_target_id(source_target, spec),
            "spec": dict(spec),
            "profile": profile,
            "seed": seed,
            "elapsed_sec": 0.5,
            "val_stop": {"auc": 0.68, "pr_auc": 0.42, "positive_rate": 0.30},
            "diagnostic_holdout": {"auc": 0.62, "pr_auc": 0.36, "positive_rate": 0.30},
            "yearly_val": {"2021": {"auc": 0.61}, "2022": {"auc": 0.62}},
            "yearly_diagnostic_holdout": {},
        },
    )

    report = runner.run_stage5_3_target_reformulation(
        {"sell": (df, df, df), "buy": (df, df, df)},
        output_path=tmp_path / "stage5_3.json",
    )

    assert report["stage"] == "5.3_time_to_breach_target_reformulation"
    assert report["progress"]["done_runs"] == 4
    assert report["progress"]["total_runs"] == 4
    assert set(report["summary"]) == set(runner.STAGE5_3_SOURCE_TARGETS)
    assert (tmp_path / "stage5_3.json").exists()


def test_stage5_3_cli_arguments_exist_in_build_arg_parser():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    parser = runner.build_arg_parser()
    args = parser.parse_args([
        "--stage5-3-target-reformulation",
        "--stage5-3-workers", "8",
        "--stage5-3-xgb-threads", "4",
    ])

    assert args.stage5_3_target_reformulation is True
    assert args.stage5_3_workers == 8
    assert args.stage5_3_xgb_threads == 4
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_stage5_3_runner_writes_json tests/test_stage5_transformer_breach.py::test_stage5_3_cli_arguments_exist_in_build_arg_parser -q
```

Expected: FAIL because runner/CLI do not exist.

- [ ] **Step 3: Implement runner**

Add near `run_stage5_2_time_to_breach_regression`:

```python
def _run_stage5_3_job(job: dict) -> dict:
    started_at = time.time()
    started_wall = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(started_at))
    print(
        f"[heartbeat] ts={started_wall}Z | stage5.3 job | source={job['source_target']} "
        f"target={job['spec']['name']} profile={job['profile']} seed={job['seed']} "
        f"xgb_threads={job['xgb_threads']} start"
    )
    run = evaluate_stage5_3_profile_seed(
        job["split"], job["source_target"], job["spec"], job["profile"], job["seed"],
        xgb_threads=job["xgb_threads"],
    )
    finished_at = time.time()
    finished_wall = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(finished_at))
    print(
        f"[heartbeat] ts={finished_wall}Z | stage5.3 job | source={job['source_target']} "
        f"target={job['spec']['name']} profile={job['profile']} seed={job['seed']} done"
    )
    run["started_at_unix"] = started_at
    run["finished_at_unix"] = finished_at
    return run


def run_stage5_3_target_reformulation(target_splits: dict,
                                      output_path: Path = STAGE5_3_JSON_REPORT_PATH,
                                      workers: int = 1,
                                      xgb_threads: int = 1) -> dict:
    started_at = time.time()
    target_specs = (
        STAGE5_3_MAIN_TARGET_SPECS
        + STAGE5_3_BINARY_BASELINE_SPECS
        + STAGE5_3_CONTROL_TARGET_SPECS
    )
    total_runs = (
        len(STAGE5_3_SOURCE_TARGETS)
        * len(target_specs)
        * len(STAGE5_3_PROFILE_KEYS)
        * len(STAGE5_3_SEEDS)
    )
    report = {
        "stage": "5.3_time_to_breach_target_reformulation",
        "status": "RUNNING",
        "level": "diagnostic_only",
        "source_targets": STAGE5_3_SOURCE_TARGETS,
        "target_specs": target_specs,
        "profiles": STAGE5_3_PROFILE_KEYS,
        "seeds": STAGE5_3_SEEDS,
        "target_distribution": {},
        "raw_runs": [],
        "summary": {},
        "gate_results": {},
        "notes": {
            "oracle_pf_gate": "disabled; Stage 5.2 binary-oracle comparison is invalid",
            "price_features": "excluded; target formulation is isolated before feature expansion",
            "multiple_testing": "14 main target/side comparisons; report must disclose correlated target families and no independent candidate validation",
            "survives_at_least_k": "control only because censored rows all become positive",
        },
        "progress": {
            "done_runs": 0,
            "total_runs": total_runs,
            "run_elapsed_sec": [],
            "started_at_unix": started_at,
            "updated_at_unix": started_at,
            "workers": int(workers),
            "xgb_threads": int(xgb_threads),
            "eta_sec": None,
            "last_completed": None,
        },
    }
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    combined_by_name = {
        "sell_bars_to_breach_H6_off05": pd.concat(target_splits["sell"], ignore_index=True),
        "buy_bars_to_breach_H6_off05": pd.concat(target_splits["buy"], ignore_index=True),
    }
    splits_by_source = {}
    for source_target in STAGE5_3_SOURCE_TARGETS:
        split = build_stage5_1_split(combined_by_name[source_target], source_target)
        splits_by_source[source_target] = split
        report["target_distribution"][source_target] = {
            spec["name"]: stage5_3_target_distribution(split, source_target, spec)
            for spec in target_specs
        }
        for spec_name, dist in report["target_distribution"][source_target].items():
            train_rate = ((dist.get("train_core") or {}).get("positive_rate"))
            if train_rate is not None and (train_rate < 0.05 or train_rate > 0.95):
                dist["distribution_warning"] = "positive_rate_outside_0_05_0_95"
    _write_json_atomic(output_path, report)

    jobs = []
    for source_target in STAGE5_3_SOURCE_TARGETS:
        for spec in target_specs:
            for profile in STAGE5_3_PROFILE_KEYS:
                for seed in STAGE5_3_SEEDS:
                    jobs.append({
                        "source_target": source_target,
                        "spec": spec,
                        "profile": profile,
                        "seed": int(seed),
                        "split": splits_by_source[source_target],
                        "xgb_threads": int(xgb_threads),
                    })

    heartbeat = HeartbeatLogger("stage5.3 runner")
    heartbeat.emit(
        f"pending_jobs={len(jobs)} workers={workers} xgb_threads={xgb_threads}",
        force=True,
    )

    def consume_run(run: dict) -> None:
        report["raw_runs"].append(run)
        report["progress"]["done_runs"] += 1
        report["progress"]["run_elapsed_sec"].append(run.get("elapsed_sec"))
        report["progress"]["updated_at_unix"] = time.time()
        elapsed = report["progress"]["updated_at_unix"] - report["progress"]["started_at_unix"]
        remaining = report["progress"]["total_runs"] - report["progress"]["done_runs"]
        report["progress"]["eta_sec"] = round((elapsed / max(report["progress"]["done_runs"], 1)) * remaining, 1)
        report["progress"]["last_completed"] = {
            "source_target": run["source_target"],
            "target_id": run["target_id"],
            "profile": run["profile"],
            "seed": int(run["seed"]),
            "auc": _safe((run.get("val_stop") or {}).get("auc")),
            "pr_auc": _safe((run.get("val_stop") or {}).get("pr_auc")),
            "elapsed_sec": run.get("elapsed_sec"),
        }
        done_runs = report["progress"]["done_runs"]
        total = report["progress"]["total_runs"]
        last = report["progress"]["last_completed"]
        print(
            f"[{done_runs}/{total}] {run['source_target']} | {run['target_id']} | "
            f"{run['profile']} | seed={run['seed']} | auc={last['auc']} | pr_auc={last['pr_auc']}"
        )
        heartbeat.emit(f"progress={done_runs}/{total}")
        _write_json_atomic(output_path, report)

    if workers <= 1:
        for job in jobs:
            consume_run(_run_stage5_3_job(job))
    else:
        with ProcessPoolExecutor(max_workers=int(workers)) as executor:
            futures = [executor.submit(_run_stage5_3_job, job) for job in jobs]
            for future in as_completed(futures):
                consume_run(future.result())

    statuses = []
    for source_target in STAGE5_3_SOURCE_TARGETS:
        summary = summarize_stage5_3_source(report["raw_runs"], source_target)
        report["summary"][source_target] = summary
        gate = stage5_3_gate_results(summary)
        report["gate_results"][source_target] = gate
        statuses.append(gate["overall_status"])
        _write_json_atomic(output_path, report)

    report["status"] = (
        "TARGET_REFORMULATION_FOUND"
        if statuses and any(s == "TARGET_REFORMULATION_FOUND" for s in statuses)
        else "DIAGNOSTIC_ONLY"
    )
    report["progress"]["finished_at_unix"] = time.time()
    report["progress"]["updated_at_unix"] = report["progress"]["finished_at_unix"]
    report["progress"]["elapsed_sec"] = round(report["progress"]["finished_at_unix"] - started_at, 3)
    report["progress"]["eta_sec"] = 0.0
    _write_json_atomic(output_path, report)
    return report
```

- [ ] **Step 4: Add CLI arguments and fast path**

In `build_arg_parser()`, add near Stage 5.2 args:

```python
    parser.add_argument("--stage5-3-target-reformulation", action="store_true",
                        help="Run Stage 5.3 time-to-breach target reformulation diagnostics.")
    parser.add_argument("--stage5-3-workers", type=int, default=1,
                        help="Number of worker processes for Stage 5.3")
    parser.add_argument("--stage5-3-xgb-threads", type=int, default=1,
                        help="XGBoost threads per Stage 5.3 worker")
```

In `main()`, add a fast path before the generic Stage 5 prelude, following the Stage 5.2 pattern:

```python
    if args.stage5_3_target_reformulation:
        print("Stage 5.3 fast path: skipping generic Stage 5 prelude")
        print("Загрузка sell splits для Stage 5.3...")
        sell_train, sell_val, sell_hold = load_splits(target_col="sell_bars_to_breach_H6_off05")
        print("Загрузка buy splits для Stage 5.3...")
        buy_train, buy_val, buy_hold = load_splits(target_col="buy_bars_to_breach_H6_off05")
        report = run_stage5_3_target_reformulation(
            {"sell": (sell_train, sell_val, sell_hold), "buy": (buy_train, buy_val, buy_hold)},
            output_path=STAGE5_3_JSON_REPORT_PATH,
            workers=args.stage5_3_workers,
            xgb_threads=args.stage5_3_xgb_threads,
        )
        print("Stage 5.3: target reformulation diagnostics completed")
        print(json.dumps({
            "status": report["status"],
            "json": str(STAGE5_3_JSON_REPORT_PATH),
            "done_runs": report["progress"]["done_runs"],
            "total_runs": report["progress"]["total_runs"],
        }, indent=2))
        return
```

- [ ] **Step 5: Run runner and CLI tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_stage5_3_runner_writes_json tests/test_stage5_transformer_breach.py::test_stage5_3_cli_arguments_exist_in_build_arg_parser -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add ML/baseline/benchmark_stage5_transformer_breach.py tests/test_stage5_transformer_breach.py
git commit -m "feat: add stage 5.3 runner"
```

---

### Task 5: Full Verification And Stage 5.3 Run

**Files:**
- Read: `DATA/Nero_XAUUSD_train_labeled.csv`
- Read: `DATA/Nero_XAUUSD_validation_labeled.csv`
- Read: `DATA/Nero_XAUUSD_test_labeled.csv`
- Output: `ML/reports/stage5_3_time_to_breach_target_reformulation.json`

**Interfaces:**
- Consumes: CLI `--stage5-3-target-reformulation`
- Produces: completed JSON with `progress.done_runs == progress.total_runs == 432`

- [ ] **Step 1: Verify Stage 5.2 source targets exist in labeled CSV**

Run:

```bash
./.venv/bin/python - <<'PY'
import pandas as pd
paths = [
    "DATA/Nero_XAUUSD_train_labeled.csv",
    "DATA/Nero_XAUUSD_validation_labeled.csv",
    "DATA/Nero_XAUUSD_test_labeled.csv",
]
cols = [
    "sell_bars_to_breach_H6_off05",
    "buy_bars_to_breach_H6_off05",
    "sell_stop_broken_H6_off05_flag",
    "buy_stop_broken_H6_off05_flag",
]
for path in paths:
    df = pd.read_csv(path, sep=";", nrows=1)
    missing = [col for col in cols if col not in df.columns]
    print(path, "OK" if not missing else f"MISSING {missing}")
PY
```

Expected:

```text
DATA/Nero_XAUUSD_train_labeled.csv OK
DATA/Nero_XAUUSD_validation_labeled.csv OK
DATA/Nero_XAUUSD_test_labeled.csv OK
```

- [ ] **Step 2: Run focused Stage 5.3 tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py -q -k "stage5_3"
```

Expected: all Stage 5.3 tests PASS.

- [ ] **Step 3: Run full test suite**

Run:

```bash
./.venv/bin/python -m pytest tests/ -q
```

Expected: PASS.

- [ ] **Step 4: Run full Stage 5.3 diagnostics**

Run:

```bash
./.venv/bin/python -u ML/baseline/benchmark_stage5_transformer_breach.py \
  --stage5-3-target-reformulation \
  --stage5-3-workers 8 \
  --stage5-3-xgb-threads 4
```

Expected:

```text
Stage 5.3: target reformulation diagnostics completed
```

- [ ] **Step 5: Verify JSON consistency**

Run:

```bash
./.venv/bin/python - <<'PY'
import json
from pathlib import Path
p = Path("ML/reports/stage5_3_time_to_breach_target_reformulation.json")
d = json.loads(p.read_text())
assert d["stage"] == "5.3_time_to_breach_target_reformulation"
assert d["progress"]["done_runs"] == d["progress"]["total_runs"] == 432
assert d["progress"]["workers"] == 8
assert d["progress"]["xgb_threads"] == 4
assert d["status"] in {"TARGET_REFORMULATION_FOUND", "DIAGNOSTIC_ONLY"}
for source in d["source_targets"]:
    assert source in d["summary"]
    assert source in d["gate_results"]
    best = d["summary"][source]["best_main"]
    assert best
    assert "binary_breach_baseline" in best
    assert "seed_consistency" in best
print("stage5_3_json_consistency_ok")
PY
```

Expected:

```text
stage5_3_json_consistency_ok
```

- [ ] **Step 6: Commit**

```bash
git add ML/baseline/benchmark_stage5_transformer_breach.py tests/test_stage5_transformer_breach.py ML/reports/stage5_3_time_to_breach_target_reformulation.json
git commit -m "run: complete stage 5.3 target reformulation"
```

---

### Task 6: Report, Changelog, Handoff And Wiki

**Files:**
- Create: `docs/reports/2026-06-26-stage5_3-time-to-breach-target-reformulation.md`
- Modify: `CHANGELOG.md`
- Modify: `CONTEXT_HANDOFF.md`
- Modify/Create: `wiki/research/...`

**Interfaces:**
- Consumes: `ML/reports/stage5_3_time_to_breach_target_reformulation.json`
- Produces: final synchronized documentation for the stage.

- [ ] **Step 1: Read reporting instructions**

Run:

```bash
sed -n '1,260p' .claude/skills/my/stage-reporting/SKILL.md
sed -n '1,220p' .claude/skills/my/wiki/SKILL.md
```

Expected: both files exist and define report/wiki synchronization workflow.

- [ ] **Step 2: Write report from JSON, not from memory**

The report must include:

```text
1. Stage 5.3 scope: target reformulation only, no new price features, no Up/Dn.
2. Search budget: 432 classifier runs, main budget 252, binary baseline and controls disclosed separately.
3. Target distributions for every derived target on train/val/holdout, including warnings for positive_rate outside [0.05, 0.95].
4. Full table of main targets by source side, best profile, val AUC, val PR AUC, positive rate, yearly AUC, holdout AUC.
5. Same-profile binary breach baseline table and delta vs best main target.
6. Seed consistency table: how many seeds beat binary breach for the selected target/profile.
7. Separate table for control survives_at_least_k targets, explicitly marked non-winning.
8. Feature importance top-20 for selected winner profiles.
9. Prediction distribution/calibration notes from saved predictions/labels.
10. Gate result: TARGET_REFORMULATION_FOUND or DIAGNOSTIC_ONLY.
11. Explicit warning: 2023-2025 are diagnostic disclosure, not independent confirmation.
12. Explicit warning: 14 main comparisons are correlated; no strict multiple-testing correction can turn this into candidate validation.
13. Next decision:
   - If target reformulation found: design Stage 5.4 price_coord_atr ablation.
   - If not found: deprioritize time-to-breach branch or move to survival-loss research.
```

- [ ] **Step 3: Update `CHANGELOG.md` and `CONTEXT_HANDOFF.md`**

Add only concise entries:

```text
Stage 5.3 completed target reformulation diagnostics for time-to-breach; status is taken from ML/reports/stage5_3_time_to_breach_target_reformulation.json; artifact ML/reports/stage5_3_time_to_breach_target_reformulation.json.
```

- [ ] **Step 4: Update wiki**

Use the project wiki workflow. The wiki page must preserve these facts:

```text
Stage 5.3 isolates target formulation from feature expansion.
No price/ATR/UpDn features were added.
Control survives_at_least_k targets are disclosure-only and cannot define the winner.
Any next feature ablation starts from the selected target family only.
```

- [ ] **Step 5: Verify docs references**

Run:

```bash
./.venv/bin/python wiki/wiki.py verify
```

Expected: wiki verification passes or reports only pre-existing unrelated warnings.

- [ ] **Step 6: Commit**

```bash
git add docs/reports/ CHANGELOG.md CONTEXT_HANDOFF.md wiki/
git commit -m "docs: report stage 5.3 target reformulation"
```

---

## Self-Review Checklist

- Spec coverage: plan implements target-only Stage 5.3, excludes price features and Up/Dn, includes `breach_after_k`, buckets, `survives_at_least_k` control, fixed profiles, yearly consistency and full disclosure.
- Placeholder scan: no `TBD`, no unspecified "write tests", no undefined function names.
- Type consistency: target builders return `np.ndarray` with `-1` for invalid rows; evaluator filters invalid train rows; metrics ignore invalid labels; summary only lets `role == "main"` win the stage.
- Known limitation: `TARGET_REFORMULATION_FOUND` is not a trading candidate. It only permits the next diagnostic stage: price/ATR feature ablation on the selected target family.
