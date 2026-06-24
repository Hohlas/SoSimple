# Stage 5.0f Signal Stationarity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Реализовать поисковую диагностику Stage 5.0f, которая различает `weak_signal`, `temporal_decay` и `inconclusive` для H6_off05 breach-сигнала.

**Architecture:** Расширяем существующий runner `ML/baseline/benchmark_stage5_transformer_breach.py`, потому что там уже живут Stage 5.0b-5.0e, XGBoost baselines, profile builders, transform fit и CLI. Добавляем отдельные helpers для Stage 5.0f: профили, временные окна, split manifest, bootstrap CI, агрегатор результатов и decision helper. Не трогаем Transformer и торговую симуляцию.

**Tech Stack:** Python 3.10+, pandas, numpy, scikit-learn metrics, xgboost, pytest, проектное окружение `./.venv/bin/python`.

## Global Constraints

- Уровень этапа: `DIAGNOSTIC_ONLY`; результат не кандидат, не winner, не открывает Transformer.
- Использовать только XGBoost; без Transformer и без trade simulation. Stage 5.0e показал, что регуляризация уменьшает переобучение Transformer, но не закрывает разрыв с XGBoost, поэтому дальнейшая настройка Transformer на `H6_off05` не является приоритетом.
- Цели: `sell_stop_broken_H6_off05_flag`, `buy_stop_broken_H6_off05_flag`.
- Профили: `base_raw_plus_time`, `structure_only`, `time_only`, `all100_relative_price_time`.
- `time_only` в Stage 5.0f = `hour_sin`, `hour_cos`, `dow_sin`, `dow_cos`; нет `time_pos`, `year`, `month`.
- Вывод про отсутствие calendar index относится только к XGBoost-ветке Stage 5.0f; для Transformer это не переносится.
- Центральный тест H2: rolling refit с 8-летним development-window: 7 календарных лет train-core + 1 год val-stop для early stopping.
- Дополнительный тест: anchored expanding.
- Контроль: fixed train-core `<=2019`, val-stop `2020`, test по годам.
- Test-год нельзя использовать для early stopping.
- Transform params fit только на train-core.
- Основной вердикт считать по 2023-2025; 2026 только `low_n_disclosure`.
- Seeds: `[42, 77, 123]`; итоговые AUC/lift_30 — median по seeds.
- Bootstrap CI: 1000 resamples по строкам test, 95% percentile interval. В сводке это median от per-seed bootstrap CI, не pooled CI.
- `lift_30` в этом runner — bottom-30 risk lift: меньше = лучше отсеивается низкорисковая зона; это не top-k enrichment.
- Объём оценки: 4 профиля × 2 цели × (rolling 6 окон + anchored 7 окон + fixed 6 окон) × 3 seeds = 456 XGBoost-моделей.
- Rolling test `2024` означает train-core `2016..2022`, val-stop `2023`, test `2024`; это 8-летнее development-window, а не 8-летний train-core.
- После изменений Python-кода запускать `./.venv/bin/python -m pytest tests/ -q`.
- Не делать `git commit`; по AGENTS.md коммит выполняется только при закрытии этапа через `stage-reporting`.

---

### Task 1: Stage 5.0f Constants And Feature Builder

**Files:**
- Modify: `ML/baseline/benchmark_stage5_transformer_breach.py`
- Test: `tests/test_stage5_transformer_breach.py`

**Interfaces:**
- Consumes: `NO_PRICE_TOKEN_FIELDS`, `TIME_ONLY_ROW_FIELDS`, `find_profile()`, `build_xgb_features()`, `build_xgb_features_for_profile()`, `fit_transform_params_for_profile()`, `parse_split_fractals()`
- Produces: `STAGE5_0F_TARGETS`, `STAGE5_0F_PROFILE_KEYS`, `STAGE5_0F_SEEDS`, `STAGE5_0F_JSON_REPORT_PATH`, `build_stage5_0f_features()`, `fit_stage5_0f_transform_params()`

- [ ] **Step 1: Write failing tests for frozen constants and `time_only` contract**

Add this to the end of `tests/test_stage5_transformer_breach.py`:

```python
# ───────────────────────────────────────────────────────────────────────────
# Stage 5.0f tests
# ───────────────────────────────────────────────────────────────────────────

def test_stage5_0f_constants_are_frozen():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    assert runner.STAGE5_0F_TARGETS == [
        "sell_stop_broken_H6_off05_flag",
        "buy_stop_broken_H6_off05_flag",
    ]
    assert runner.STAGE5_0F_PROFILE_KEYS == [
        "base_raw_plus_time",
        "structure_only",
        "time_only",
        "all100_relative_price_time",
    ]
    assert runner.STAGE5_0F_SEEDS == [42, 77, 123]
    assert runner.STAGE5_0F_DECISION_YEARS == [2023, 2024, 2025]
    assert runner.STAGE5_0F_LOW_N_YEAR == 2026
    assert str(runner.STAGE5_0F_JSON_REPORT_PATH).endswith(
        "stage5_0f_signal_stationarity.json"
    )


def test_stage5_0f_time_only_has_no_calendar_index_fields():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    assert runner.TIME_ONLY_ROW_FIELDS == ["hour_sin", "hour_cos", "dow_sin", "dow_cos"]
    forbidden = {"time_pos", "year", "month", "date_index", "calendar_index"}
    assert forbidden.isdisjoint(set(runner.TIME_ONLY_ROW_FIELDS))
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_stage5_0f_constants_are_frozen tests/test_stage5_transformer_breach.py::test_stage5_0f_time_only_has_no_calendar_index_fields -q
```

Expected: FAIL because `STAGE5_0F_*` constants do not exist yet.

- [ ] **Step 3: Add constants**

Add near the Stage 5.0e constants in `ML/baseline/benchmark_stage5_transformer_breach.py`:

```python
STAGE5_0F_TARGETS = [
    "sell_stop_broken_H6_off05_flag",
    "buy_stop_broken_H6_off05_flag",
]
STAGE5_0F_PROFILE_KEYS = [
    "base_raw_plus_time",
    "structure_only",
    "time_only",
    "all100_relative_price_time",
]
STAGE5_0F_SEEDS = [42, 77, 123]
STAGE5_0F_DECISION_YEARS = [2023, 2024, 2025]
STAGE5_0F_LOW_N_YEAR = 2026
STAGE5_0F_ROLLING_WINDOW_YEARS = 8
STAGE5_0F_BOOTSTRAP_N = 1000
STAGE5_0F_JSON_REPORT_PATH = REPORTS_DIR / "stage5_0f_signal_stationarity.json"
```

- [ ] **Step 4: Run constants tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_stage5_0f_constants_are_frozen tests/test_stage5_transformer_breach.py::test_stage5_0f_time_only_has_no_calendar_index_fields -q
```

Expected: PASS.

- [ ] **Step 5: Write failing feature builder tests**

Add:

```python
def test_build_stage5_0f_features_shapes_and_profiles():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    df = _make_synthetic_df(6, 100)

    base_params = runner.fit_stage5_0f_transform_params(
        df, "base_raw_plus_time", transform_variant="asinh"
    )
    X_base = runner.build_stage5_0f_features(
        df, "base_raw_plus_time", transform_variant="asinh", transform_params=base_params
    )
    assert X_base.shape == (6, 1005)

    structure_params = runner.fit_stage5_0f_transform_params(
        df, "structure_only", transform_variant="asinh"
    )
    X_structure = runner.build_stage5_0f_features(
        df, "structure_only", transform_variant="asinh", transform_params=structure_params
    )
    assert X_structure.shape == (6, 904)

    X_time = runner.build_stage5_0f_features(
        df, "time_only", transform_variant="asinh", transform_params=None
    )
    assert X_time.shape == (6, 4)

    rel_params = runner.fit_stage5_0f_transform_params(
        df, "all100_relative_price_time", transform_variant="asinh"
    )
    X_rel = runner.build_stage5_0f_features(
        df, "all100_relative_price_time", transform_variant="asinh", transform_params=rel_params
    )
    assert X_rel.shape == (6, 1005)
```

- [ ] **Step 6: Run feature builder test to verify it fails**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_build_stage5_0f_features_shapes_and_profiles -q
```

Expected: FAIL because `fit_stage5_0f_transform_params()` and `build_stage5_0f_features()` do not exist.

- [ ] **Step 7: Implement transform and feature builders**

Add below `build_xgb_features_for_profile()`:

```python
def _stage5_0f_structure_profile() -> dict:
    """Profile with structural fractal fields + clock fields, without price and ATR."""
    return {
        "name": "stage5_0f_structure_only",
        "selection": "all100",
        "order": "freshness",
        "token_fields": NO_PRICE_TOKEN_FIELDS.copy(),
        "row_fields": TIME_ONLY_ROW_FIELDS.copy(),
        "uses_time": True,
        "seq_len": 100,
        "token_dim": len(NO_PRICE_TOKEN_FIELDS),
        "row_dim": len(TIME_ONLY_ROW_FIELDS),
    }


def _stage5_0f_profile_for_key(profile_key: str) -> dict | None:
    if profile_key == "base_raw_plus_time":
        return find_profile("all100_base10_time")
    if profile_key == "structure_only":
        return _stage5_0f_structure_profile()
    if profile_key == "all100_relative_price_time":
        return find_profile("all100_relative_price_time")
    if profile_key == "time_only":
        return find_profile("time_only_clean")
    raise ValueError(f"Unknown Stage 5.0f profile_key: {profile_key}")


def fit_stage5_0f_transform_params(df: pd.DataFrame, profile_key: str,
                                   transform_variant: str = "asinh",
                                   parsed_cache: dict | None = None,
                                   cache_key: tuple | None = None) -> dict | None:
    """Fit Stage 5.0f transform params on train-core only."""
    if profile_key == "time_only":
        return None
    profile = _stage5_0f_profile_for_key(profile_key)
    if parsed_cache is not None and cache_key is not None:
        if cache_key not in parsed_cache:
            parsed_cache[cache_key] = parse_split_fractals(df)
        parsed = parsed_cache[cache_key]
    else:
        parsed = parse_split_fractals(df)
    return fit_transform_params_for_profile(df, parsed, profile, transform_variant)


def build_stage5_0f_features(df: pd.DataFrame, profile_key: str,
                             transform_variant: str = "asinh",
                             transform_params: dict | None = None) -> np.ndarray:
    """Build XGBoost feature matrix for a Stage 5.0f profile."""
    if profile_key == "time_only":
        profile = _stage5_0f_profile_for_key("time_only")
        return build_row_features(df, profile).astype(np.float32)

    profile = _stage5_0f_profile_for_key(profile_key)
    if transform_params is None:
        transform_params = fit_stage5_0f_transform_params(
            df, profile_key, transform_variant=transform_variant)
    return build_flat_features(
        df, profile, transform_variant=transform_variant, transform_params=transform_params)
```

- [ ] **Step 8: Run feature builder tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_build_stage5_0f_features_shapes_and_profiles -q
```

Expected: PASS.

---

### Task 2: Window Split And Split Manifest

**Files:**
- Modify: `ML/baseline/benchmark_stage5_transformer_breach.py`
- Test: `tests/test_stage5_transformer_breach.py`

**Interfaces:**
- Consumes: DataFrame with `_year` and target columns
- Produces: `build_stage5_0f_window()`, `build_stage5_0f_windows()`, `stage5_0f_split_manifest()`

- [ ] **Step 1: Write failing split tests**

Add:

```python
def _make_stage5_0f_year_df() -> pd.DataFrame:
    """Tiny yearly fixture for split/JSON structure tests, not statistical CI tests."""
    rows = []
    for year in range(2010, 2027):
        for i in range(4):
            rows.append({
                "time": f"{year}.01.{i + 1:02d} 12:00",
                "_year": year,
                "sell_stop_broken_H6_off05_flag": i % 2,
                "buy_stop_broken_H6_off05_flag": (i + 1) % 2,
                "ATR": 1.0,
                "signal": -1,
                **{f"fractal{j}": _make_fractal_str([
                    (0, 10_000_000),
                    (1, 390.0 + j),
                    (2, -1),
                    (3, 0.5),
                    (4, 0.25),
                    (5, 1),
                    (6, 0),
                    (7, 0),
                    (8, 1),
                    (9, 1),
                    (10, 0.5),
                    (21, 1.0),
                    (22, j + 1),
                ]) for j in range(100)},
            })
    return pd.DataFrame(rows)


def test_stage5_0f_build_rolling_window_has_internal_val_stop():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    df = _make_stage5_0f_year_df()
    window = runner.build_stage5_0f_window(df, strategy="rolling", test_year=2024)

    assert sorted(window["train_core"]["_year"].unique().tolist()) == list(range(2016, 2023))
    assert sorted(window["val_stop"]["_year"].unique().tolist()) == [2023]
    assert sorted(window["test"]["_year"].unique().tolist()) == [2024]
    assert window["manifest"]["strategy"] == "rolling"
    assert window["manifest"]["test_year"] == 2024


def test_stage5_0f_build_anchored_window_has_internal_val_stop():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    df = _make_stage5_0f_year_df()
    window = runner.build_stage5_0f_window(df, strategy="anchored", test_year=2022)

    assert window["train_core"]["_year"].max() == 2020
    assert sorted(window["val_stop"]["_year"].unique().tolist()) == [2021]
    assert sorted(window["test"]["_year"].unique().tolist()) == [2022]
    assert window["manifest"]["strategy"] == "anchored"


def test_stage5_0f_build_fixed_window_uses_2020_val_stop():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    df = _make_stage5_0f_year_df()
    window = runner.build_stage5_0f_window(df, strategy="fixed", test_year=2025)

    assert window["train_core"]["_year"].max() == 2019
    assert sorted(window["val_stop"]["_year"].unique().tolist()) == [2020]
    assert sorted(window["test"]["_year"].unique().tolist()) == [2025]
    assert window["manifest"]["strategy"] == "fixed"
```

- [ ] **Step 2: Run split tests to verify they fail**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_stage5_0f_build_rolling_window_has_internal_val_stop tests/test_stage5_transformer_breach.py::test_stage5_0f_build_anchored_window_has_internal_val_stop tests/test_stage5_transformer_breach.py::test_stage5_0f_build_fixed_window_uses_2020_val_stop -q
```

Expected: FAIL because `build_stage5_0f_window()` does not exist.

- [ ] **Step 3: Implement manifest helpers**

Add below Stage 5.0f feature builders:

```python
def _stage5_0f_year_list(df: pd.DataFrame) -> list[int]:
    if "_year" in df.columns:
        return sorted(int(y) for y in df["_year"].dropna().unique().tolist())
    years = pd.to_datetime(df["time"], format="%Y.%m.%d %H:%M", errors="coerce").dt.year
    return sorted(int(y) for y in years.dropna().unique().tolist())


def _stage5_0f_with_year(df: pd.DataFrame) -> pd.DataFrame:
    if "_year" in df.columns:
        return df.copy()
    out = df.copy()
    out["_year"] = pd.to_datetime(out["time"], format="%Y.%m.%d %H:%M", errors="coerce").dt.year
    return out


def _stage5_0f_split_manifest_part(df: pd.DataFrame, target_col: str) -> dict:
    years = _stage5_0f_year_list(df)
    non_null = df[target_col].dropna() if target_col in df.columns else pd.Series(dtype=float)
    return {
        "years": years,
        "n_rows": int(len(df)),
        "positive_rate": float((non_null == 1).mean()) if len(non_null) else None,
    }


def stage5_0f_split_manifest(train_core: pd.DataFrame, val_stop: pd.DataFrame,
                             test: pd.DataFrame, strategy: str, test_year: int,
                             target_col: str) -> dict:
    return {
        "strategy": strategy,
        "test_year": int(test_year),
        "target": target_col,
        "train_core": _stage5_0f_split_manifest_part(train_core, target_col),
        "val_stop": _stage5_0f_split_manifest_part(val_stop, target_col),
        "test": _stage5_0f_split_manifest_part(test, target_col),
    }
```

- [ ] **Step 4: Implement window builder**

Add:

```python
def build_stage5_0f_window(df: pd.DataFrame, strategy: str, test_year: int,
                           target_col: str = STAGE5_0F_TARGETS[0],
                           rolling_window_years: int = STAGE5_0F_ROLLING_WINDOW_YEARS) -> dict:
    """Build train-core / val-stop / test split for one Stage 5.0f window."""
    data = _stage5_0f_with_year(df)
    test_year = int(test_year)

    if strategy == "rolling":
        val_year = test_year - 1
        train_start = test_year - rolling_window_years
        train_end = test_year - 2
        train_core = data[(data["_year"] >= train_start) & (data["_year"] <= train_end)].copy()
        val_stop = data[data["_year"] == val_year].copy()
    elif strategy == "anchored":
        val_year = test_year - 1
        train_core = data[data["_year"] <= test_year - 2].copy()
        val_stop = data[data["_year"] == val_year].copy()
    elif strategy == "fixed":
        train_core = data[data["_year"] <= 2019].copy()
        val_stop = data[data["_year"] == 2020].copy()
    else:
        raise ValueError(f"Unknown Stage 5.0f strategy: {strategy}")

    test = data[data["_year"] == test_year].copy()
    manifest = stage5_0f_split_manifest(
        train_core, val_stop, test, strategy=strategy, test_year=test_year, target_col=target_col)
    return {
        "train_core": train_core,
        "val_stop": val_stop,
        "test": test,
        "manifest": manifest,
    }


def build_stage5_0f_windows(df: pd.DataFrame, target_col: str) -> list[dict]:
    windows = []
    for test_year in [2021, 2022, 2023, 2024, 2025, 2026]:
        windows.append(build_stage5_0f_window(
            df, "rolling", test_year, target_col=target_col))
        windows.append(build_stage5_0f_window(
            df, "fixed", test_year, target_col=target_col))
    for test_year in [2019, 2020, 2021, 2022, 2023, 2024, 2025]:
        windows.append(build_stage5_0f_window(
            df, "anchored", test_year, target_col=target_col))
    return windows
```

- [ ] **Step 5: Run split tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_stage5_0f_build_rolling_window_has_internal_val_stop tests/test_stage5_transformer_breach.py::test_stage5_0f_build_anchored_window_has_internal_val_stop tests/test_stage5_transformer_breach.py::test_stage5_0f_build_fixed_window_uses_2020_val_stop -q
```

Expected: PASS.

---

### Task 3: Bootstrap CI And Single Window Evaluation

**Files:**
- Modify: `ML/baseline/benchmark_stage5_transformer_breach.py`
- Test: `tests/test_stage5_transformer_breach.py`

**Interfaces:**
- Consumes: `train_xgb_baseline()`, `compute_metrics()`, `build_stage5_0f_features()`, `fit_stage5_0f_transform_params()`
- Produces: `bootstrap_stage5_0f_metric_ci()`, `evaluate_stage5_0f_window_seed()`, `summarize_stage5_0f_seed_runs()`

- [ ] **Step 1: Write failing bootstrap tests**

Add:

```python
def test_bootstrap_stage5_0f_metric_ci_is_deterministic():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    y = pd.Series([0, 0, 1, 1, 0, 1, 0, 1])
    p = np.array([0.1, 0.2, 0.8, 0.9, 0.3, 0.7, 0.4, 0.6])

    ci1 = runner.bootstrap_stage5_0f_metric_ci(y, p, metric_name="auc", n_boot=100, seed=42)
    ci2 = runner.bootstrap_stage5_0f_metric_ci(y, p, metric_name="auc", n_boot=100, seed=42)

    assert ci1 == ci2
    assert ci1["metric"] == "auc"
    assert ci1["n_boot"] == 100
    assert ci1["low"] <= ci1["median"] <= ci1["high"]


def test_bootstrap_stage5_0f_metric_ci_handles_single_class():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    y = pd.Series([0, 0, 0, 0])
    p = np.array([0.1, 0.2, 0.3, 0.4])

    ci = runner.bootstrap_stage5_0f_metric_ci(y, p, metric_name="auc", n_boot=100, seed=42)

    assert ci["low"] is None
    assert ci["median"] is None
    assert ci["high"] is None
```

- [ ] **Step 2: Run bootstrap tests to verify they fail**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_bootstrap_stage5_0f_metric_ci_is_deterministic tests/test_stage5_transformer_breach.py::test_bootstrap_stage5_0f_metric_ci_handles_single_class -q
```

Expected: FAIL because `bootstrap_stage5_0f_metric_ci()` does not exist.

- [ ] **Step 3: Implement bootstrap CI**

Add below `compute_metrics()`:

```python
def bootstrap_stage5_0f_metric_ci(y_true: pd.Series, y_pred: np.ndarray,
                                  metric_name: str, n_boot: int = STAGE5_0F_BOOTSTRAP_N,
                                  seed: int = 42) -> dict:
    """Bootstrap 95% CI for AUC or lift_30 by resampling test rows."""
    yt = pd.Series(y_true).reset_index(drop=True)
    yp = np.asarray(y_pred, dtype=float)
    n = len(yt)
    if n == 0 or yt.nunique() < 2:
        return {"metric": metric_name, "n_boot": int(n_boot), "low": None, "median": None, "high": None}

    rng = np.random.default_rng(seed)
    vals = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        sample_y = yt.iloc[idx].reset_index(drop=True)
        if sample_y.nunique() < 2:
            continue
        sample_p = yp[idx]
        metrics = compute_metrics(sample_y, pd.Series(sample_p))
        value = metrics.get(metric_name)
        if value is not None and np.isfinite(value):
            vals.append(float(value))

    if not vals:
        return {"metric": metric_name, "n_boot": int(n_boot), "low": None, "median": None, "high": None}

    arr = np.asarray(vals, dtype=float)
    return {
        "metric": metric_name,
        "n_boot": int(n_boot),
        "low": float(np.percentile(arr, 2.5)),
        "median": float(np.percentile(arr, 50.0)),
        "high": float(np.percentile(arr, 97.5)),
    }
```

- [ ] **Step 4: Run bootstrap tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_bootstrap_stage5_0f_metric_ci_is_deterministic tests/test_stage5_transformer_breach.py::test_bootstrap_stage5_0f_metric_ci_handles_single_class -q
```

Expected: PASS.

- [ ] **Step 5: Write failing evaluation test with monkeypatched model**

Add:

```python
def test_evaluate_stage5_0f_window_seed_returns_manifest_and_metrics(monkeypatch):
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    df = _make_stage5_0f_year_df()
    window = runner.build_stage5_0f_window(
        df, "fixed", 2023, target_col="sell_stop_broken_H6_off05_flag")

    class DummyDMatrix:
        def __init__(self, X, label=None):
            self.X = X
            self.label = label

    class DummyModel:
        def predict(self, dmat):
            return np.linspace(0.05, 0.95, len(dmat.X))

    monkeypatch.setattr(runner.xgb, "DMatrix", DummyDMatrix)
    monkeypatch.setattr(runner, "train_xgb_baseline", lambda *a, **k: (DummyModel(), 0.61))
    monkeypatch.setattr(runner, "STAGE5_0F_BOOTSTRAP_N", 50)

    result = runner.evaluate_stage5_0f_window_seed(
        window,
        profile_key="time_only",
        target_col="sell_stop_broken_H6_off05_flag",
        seed=42,
    )

    assert result["strategy"] == "fixed"
    assert result["profile"] == "time_only"
    assert result["target"] == "sell_stop_broken_H6_off05_flag"
    assert result["seed"] == 42
    assert result["test_year"] == 2023
    assert result["test"]["n"] == 4
    assert "auc_ci" in result["test"]
    assert "lift_30_ci" in result["test"]
    assert "split_manifest" in result
```

- [ ] **Step 6: Run evaluation test to verify it fails**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_evaluate_stage5_0f_window_seed_returns_manifest_and_metrics -q
```

Expected: FAIL because `evaluate_stage5_0f_window_seed()` does not exist.

- [ ] **Step 7: Implement single-window evaluator**

Add:

```python
def evaluate_stage5_0f_window_seed(window: dict, profile_key: str, target_col: str,
                                   seed: int, transform_variant: str = "asinh",
                                   parsed_cache: dict | None = None) -> dict:
    """Train one XGBoost model for one Stage 5.0f window/profile/target/seed."""
    train_core = window["train_core"]
    val_stop = window["val_stop"]
    test = window["test"]

    cache_key = (
        target_col,
        window["manifest"]["strategy"],
        int(window["manifest"]["test_year"]),
        "train_core",
    )
    transform_params = fit_stage5_0f_transform_params(
        train_core, profile_key, transform_variant=transform_variant,
        parsed_cache=parsed_cache, cache_key=cache_key)
    X_train = build_stage5_0f_features(
        train_core, profile_key, transform_variant=transform_variant, transform_params=transform_params)
    X_val = build_stage5_0f_features(
        val_stop, profile_key, transform_variant=transform_variant, transform_params=transform_params)
    X_test = build_stage5_0f_features(
        test, profile_key, transform_variant=transform_variant, transform_params=transform_params)

    y_train = train_core[target_col]
    y_val = val_stop[target_col]
    y_test = test[target_col]

    model, val_auc = train_xgb_baseline(X_train, y_train, X_val, y_val, seed=seed)
    train_probs = model.predict(xgb.DMatrix(X_train))
    val_probs = model.predict(xgb.DMatrix(X_val))
    test_probs = model.predict(xgb.DMatrix(X_test))

    train_metrics = compute_metrics(y_train, pd.Series(train_probs))
    val_metrics = compute_metrics(y_val, pd.Series(val_probs))
    test_metrics = compute_metrics(y_test, pd.Series(test_probs))

    return {
        "strategy": window["manifest"]["strategy"],
        "test_year": int(window["manifest"]["test_year"]),
        "profile": profile_key,
        "target": target_col,
        "seed": int(seed),
        "transform_variant": transform_variant,
        "train_core": {k: _safe(v) for k, v in train_metrics.items()},
        "val_stop": {k: _safe(v) for k, v in val_metrics.items()},
        "test": {
            **{k: _safe(v) for k, v in test_metrics.items()},
            "auc_ci": bootstrap_stage5_0f_metric_ci(
                y_test, test_probs, "auc", n_boot=STAGE5_0F_BOOTSTRAP_N, seed=seed),
            "lift_30_ci": bootstrap_stage5_0f_metric_ci(
                y_test, test_probs, "lift_30", n_boot=STAGE5_0F_BOOTSTRAP_N, seed=seed),
        },
        "split_manifest": window["manifest"],
        "val_auc_from_training": _safe(val_auc),
    }
```

- [ ] **Step 8: Run evaluation test**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_evaluate_stage5_0f_window_seed_returns_manifest_and_metrics -q
```

Expected: PASS.

---

### Task 4: Multi-Seed Summary And Decision Helper

**Files:**
- Modify: `ML/baseline/benchmark_stage5_transformer_breach.py`
- Test: `tests/test_stage5_transformer_breach.py`

**Interfaces:**
- Consumes: raw seed-level results from Task 3
- Produces: `summarize_stage5_0f_seed_runs()`, `stage5_0f_stationarity_decision()`

- [ ] **Step 1: Write failing summary and decision tests**

Add:

```python
def test_summarize_stage5_0f_seed_runs_uses_median():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    runs = [
        {"test": {"auc": 0.60, "lift_30": 0.80, "n": 100}, "train_core": {"auc": 0.70}},
        {"test": {"auc": 0.66, "lift_30": 0.70, "n": 100}, "train_core": {"auc": 0.74}},
        {"test": {"auc": 0.63, "lift_30": 0.75, "n": 100}, "train_core": {"auc": 0.72}},
    ]

    summary = runner.summarize_stage5_0f_seed_runs(runs)

    assert summary["test"]["auc_median"] == pytest.approx(0.63)
    assert summary["test"]["lift_30_median"] == pytest.approx(0.75)
    assert summary["train_core"]["auc_median"] == pytest.approx(0.72)
    assert summary["n_seed_runs"] == 3


def test_stage5_0f_stationarity_decision_returns_known_status():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    report = {
        "summary": {
            "sell_stop_broken_H6_off05_flag": {
                "base_raw_plus_time": {
                    "fixed": {
                        "2023": {"test": {"auc_median": 0.60, "auc_ci_high": 0.62}},
                        "2024": {"test": {"auc_median": 0.61, "auc_ci_high": 0.63}},
                        "2025": {"test": {"auc_median": 0.60, "auc_ci_high": 0.62}},
                    },
                    "rolling": {
                        "2023": {"test": {"auc_median": 0.70, "auc_ci_low": 0.68}},
                        "2024": {"test": {"auc_median": 0.71, "auc_ci_low": 0.69}},
                        "2025": {"test": {"auc_median": 0.72, "auc_ci_low": 0.70}},
                    },
                }
            }
        }
    }

    decision = runner.stage5_0f_stationarity_decision(report)

    assert decision["status"] == "DIAGNOSTIC_ONLY"
    assert decision["overall_verdict"] in {"temporal_decay", "weak_signal", "inconclusive"}
    assert "target_verdicts" in decision
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_summarize_stage5_0f_seed_runs_uses_median tests/test_stage5_transformer_breach.py::test_stage5_0f_stationarity_decision_returns_known_status -q
```

Expected: FAIL because helper functions do not exist.

- [ ] **Step 3: Implement multi-seed summary**

Add:

```python
def _median_or_none(values: list) -> float | None:
    clean = [float(v) for v in values if v is not None and np.isfinite(v)]
    if not clean:
        return None
    return float(np.median(clean))


def summarize_stage5_0f_seed_runs(runs: list[dict]) -> dict:
    """Summarize seed-level Stage 5.0f runs by median."""
    auc_lows = [r["test"].get("auc_ci", {}).get("low") for r in runs]
    auc_highs = [r["test"].get("auc_ci", {}).get("high") for r in runs]
    lift_lows = [r["test"].get("lift_30_ci", {}).get("low") for r in runs]
    lift_highs = [r["test"].get("lift_30_ci", {}).get("high") for r in runs]
    return {
        "n_seed_runs": int(len(runs)),
        "train_core": {
            "auc_median": _median_or_none([r["train_core"].get("auc") for r in runs]),
        },
        "val_stop": {
            "auc_median": _median_or_none([r["val_stop"].get("auc") for r in runs]),
            "lift_30_median": _median_or_none([r["val_stop"].get("lift_30") for r in runs]),
        },
        "test": {
            "n": runs[0]["test"].get("n") if runs else 0,
            "auc_median": _median_or_none([r["test"].get("auc") for r in runs]),
            "lift_30_median": _median_or_none([r["test"].get("lift_30") for r in runs]),
            "auc_ci_low": _median_or_none(auc_lows),
            "auc_ci_high": _median_or_none(auc_highs),
            "lift_30_ci_low": _median_or_none(lift_lows),
            "lift_30_ci_high": _median_or_none(lift_highs),
        },
        "split_manifest": runs[0].get("split_manifest") if runs else None,
    }
```

- [ ] **Step 4: Implement decision helper**

Add:

```python
def _stage5_0f_get_summary(report: dict, target: str, profile: str,
                           strategy: str, year: int) -> dict | None:
    return (
        report.get("summary", {})
        .get(target, {})
        .get(profile, {})
        .get(strategy, {})
        .get(str(year))
    )


def _stage5_0f_auc(summary: dict | None) -> float | None:
    if not summary:
        return None
    return summary.get("test", {}).get("auc_median")


def _stage5_0f_ci_low(summary: dict | None) -> float | None:
    if not summary:
        return None
    return summary.get("test", {}).get("auc_ci_low")


def _stage5_0f_ci_high(summary: dict | None) -> float | None:
    if not summary:
        return None
    return summary.get("test", {}).get("auc_ci_high")


def _stage5_0f_rolling_fixed_deltas(report: dict, target: str, profile: str) -> list[float]:
    deltas = []
    for year in STAGE5_0F_DECISION_YEARS:
        fixed = _stage5_0f_auc(_stage5_0f_get_summary(report, target, profile, "fixed", year))
        rolling = _stage5_0f_auc(_stage5_0f_get_summary(report, target, profile, "rolling", year))
        if fixed is not None and rolling is not None:
            deltas.append(float(rolling - fixed))
    return deltas


def _stage5_0f_anchored_spearman(report: dict, target: str, profile: str) -> dict:
    from scipy.stats import spearmanr

    years = []
    aucs = []
    for year in STAGE5_0F_DECISION_YEARS:
        summary = _stage5_0f_get_summary(report, target, profile, "anchored", year)
        auc = _stage5_0f_auc(summary)
        if auc is not None:
            years.append(year)
            aucs.append(float(auc))
    if len(years) < 3:
        return {"rho": None, "pvalue": None, "pass": False}
    res = spearmanr(years, aucs)
    rho = float(res.statistic) if np.isfinite(res.statistic) else None
    pvalue = float(res.pvalue) if np.isfinite(res.pvalue) else None
    return {
        "rho": rho,
        "pvalue": pvalue,
        "pass": bool(rho is not None and pvalue is not None and rho > 0 and pvalue < 0.1),
    }


def _stage5_0f_time_only_not_worse(report: dict, target: str) -> bool:
    time_deltas = _stage5_0f_rolling_fixed_deltas(report, target, "time_only")
    fractal_profiles = ["base_raw_plus_time", "structure_only", "all100_relative_price_time"]
    fractal_deltas = []
    for profile in fractal_profiles:
        fractal_deltas.extend(_stage5_0f_rolling_fixed_deltas(report, target, profile))
    if not time_deltas or not fractal_deltas:
        return False
    # If time_only improves more than fractal profiles under rolling refit, the
    # effect is more consistent with clock/session drift than fractal decay.
    return float(np.median(time_deltas)) <= float(np.median(fractal_deltas))


def _stage5_0f_all_profiles_low_auc(report: dict, target: str) -> bool:
    for profile in STAGE5_0F_PROFILE_KEYS:
        for strategy in ["fixed", "rolling"]:
            for year in STAGE5_0F_DECISION_YEARS:
                auc = _stage5_0f_auc(_stage5_0f_get_summary(report, target, profile, strategy, year))
                if auc is None or not (0.55 <= auc <= 0.68):
                    return False
    return True


def _stage5_0f_structure_close_to_base(report: dict, target: str, tolerance: float = 0.02) -> bool:
    diffs = []
    for strategy in ["fixed", "rolling"]:
        for year in STAGE5_0F_DECISION_YEARS:
            base = _stage5_0f_auc(_stage5_0f_get_summary(report, target, "base_raw_plus_time", strategy, year))
            structure = _stage5_0f_auc(_stage5_0f_get_summary(report, target, "structure_only", strategy, year))
            if base is not None and structure is not None:
                diffs.append(abs(float(structure - base)))
    return bool(diffs and max(diffs) <= tolerance)


def _stage5_0f_structure_base_deltas(report: dict, target: str) -> dict:
    deltas = {}
    for strategy in ["fixed", "rolling"]:
        deltas[strategy] = {}
        for year in STAGE5_0F_DECISION_YEARS:
            base = _stage5_0f_auc(_stage5_0f_get_summary(report, target, "base_raw_plus_time", strategy, year))
            structure = _stage5_0f_auc(_stage5_0f_get_summary(report, target, "structure_only", strategy, year))
            deltas[strategy][str(year)] = (
                float(structure - base) if base is not None and structure is not None else None
            )
    return deltas


def _stage5_0f_target_verdict(report: dict, target: str) -> dict:
    decisive_improvements = 0
    comparable_years = 0
    all_overlap = True

    for year in STAGE5_0F_DECISION_YEARS:
        fixed = _stage5_0f_get_summary(report, target, "base_raw_plus_time", "fixed", year)
        rolling = _stage5_0f_get_summary(report, target, "base_raw_plus_time", "rolling", year)
        if not fixed or not rolling:
            continue
        f_high = _stage5_0f_ci_high(fixed)
        r_low = _stage5_0f_ci_low(rolling)
        f_auc = _stage5_0f_auc(fixed)
        r_auc = _stage5_0f_auc(rolling)
        if f_auc is not None and r_auc is not None:
            comparable_years += 1
        if f_high is not None and r_low is not None and r_low > f_high:
            decisive_improvements += 1
            all_overlap = False

    anchored = _stage5_0f_anchored_spearman(report, target, "base_raw_plus_time")
    time_only_not_worse = _stage5_0f_time_only_not_worse(report, target)
    all_profiles_low_auc = _stage5_0f_all_profiles_low_auc(report, target)
    structure_close_to_base = _stage5_0f_structure_close_to_base(report, target)

    if decisive_improvements >= 1 and anchored["pass"] and time_only_not_worse:
        verdict = "temporal_decay"
    elif (
        comparable_years == len(STAGE5_0F_DECISION_YEARS)
        and all_overlap
        and all_profiles_low_auc
        and structure_close_to_base
    ):
        verdict = "weak_signal"
    else:
        verdict = "inconclusive"

    return {
        "verdict": verdict,
        "comparable_years": int(comparable_years),
        "rolling_ci_above_fixed_years": int(decisive_improvements),
        "anchored_spearman": anchored,
        "time_only_not_worse_than_fractals": bool(time_only_not_worse),
        "all_profiles_low_auc": bool(all_profiles_low_auc),
        "structure_close_to_base": bool(structure_close_to_base),
        "structure_minus_base_auc": _stage5_0f_structure_base_deltas(report, target),
        "decision_years": list(STAGE5_0F_DECISION_YEARS),
        "low_n_disclosure_year": STAGE5_0F_LOW_N_YEAR,
    }


def stage5_0f_stationarity_decision(report: dict) -> dict:
    target_verdicts = {
        target: _stage5_0f_target_verdict(report, target)
        for target in STAGE5_0F_TARGETS
    }
    unique = {v["verdict"] for v in target_verdicts.values()}
    if len(unique) == 1:
        overall = next(iter(unique))
    else:
        overall = "inconclusive"
    return {
        "status": "DIAGNOSTIC_ONLY",
        "overall_verdict": overall,
        "target_verdicts": target_verdicts,
        "holdout_burned": "2023-2025 used for diagnostic management decision; future confirmatory work needs 2026+ or explicit disclosure.",
    }
```

- [ ] **Step 5: Run summary and decision tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_summarize_stage5_0f_seed_runs_uses_median tests/test_stage5_transformer_breach.py::test_stage5_0f_stationarity_decision_returns_known_status -q
```

Expected: PASS.

---

### Task 5: Stage 5.0f Runner And CLI

**Files:**
- Modify: `ML/baseline/benchmark_stage5_transformer_breach.py`
- Test: `tests/test_stage5_transformer_breach.py`

**Interfaces:**
- Consumes: Tasks 1-4 helpers
- Produces: `run_stage5_0f_signal_stationarity()`, CLI flag `--stage5-0f-signal-stationarity`

- [ ] **Step 1: Write failing runner and CLI tests**

Add:

```python
def test_stage5_0f_runner_writes_json(monkeypatch, tmp_path):
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    df = _make_stage5_0f_year_df()
    monkeypatch.setattr(runner, "STAGE5_0F_PROFILE_KEYS", ["time_only"])
    monkeypatch.setattr(runner, "STAGE5_0F_SEEDS", [42])
    monkeypatch.setattr(runner, "STAGE5_0F_BOOTSTRAP_N", 20)

    class DummyDMatrix:
        def __init__(self, X, label=None):
            self.X = X
            self.label = label

    class DummyModel:
        def predict(self, dmat):
            return np.linspace(0.05, 0.95, len(dmat.X))

    monkeypatch.setattr(runner.xgb, "DMatrix", DummyDMatrix)
    monkeypatch.setattr(runner, "train_xgb_baseline", lambda *a, **k: (DummyModel(), 0.61))

    report = runner.run_stage5_0f_signal_stationarity(
        target_splits={
            "sell_stop_broken_H6_off05_flag": (df, df, df),
            "buy_stop_broken_H6_off05_flag": (df, df, df),
        },
        output_path=tmp_path / "stage5_0f.json",
    )

    assert report["stage"] == "5.0f_signal_stationarity"
    assert report["status"] == "DIAGNOSTIC_ONLY"
    assert report["holdout_used_for_diagnostic_decision"] is True
    assert report["decision"]["overall_verdict"] in {"temporal_decay", "weak_signal", "inconclusive"}
    assert (tmp_path / "stage5_0f.json").exists()


def test_stage5_0f_cli_argument_exists_in_build_arg_parser():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    parser = runner.build_arg_parser()
    args = parser.parse_args(["--stage5-0f-signal-stationarity"])
    assert args.stage5_0f_signal_stationarity is True
```

- [ ] **Step 2: Run runner and CLI tests to verify they fail**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_stage5_0f_runner_writes_json tests/test_stage5_transformer_breach.py::test_stage5_0f_cli_argument_exists_in_build_arg_parser -q
```

Expected: FAIL because runner and CLI flag do not exist.

- [ ] **Step 3: Implement runner**

Add below `run_stage5_0e_small_transformer_check()`:

```python
def run_stage5_0f_signal_stationarity(target_splits: dict,
                                      output_path=STAGE5_0F_JSON_REPORT_PATH) -> dict:
    """Run Stage 5.0f XGBoost signal stationarity diagnostics."""
    report = {
        "stage": "5.0f_signal_stationarity",
        "status": "DIAGNOSTIC_ONLY",
        "level": "exploratory",
        "holdout_used_for_diagnostic_decision": True,
        "holdout_burned_after_stage": "2023-2025",
        "targets": list(STAGE5_0F_TARGETS),
        "profiles": list(STAGE5_0F_PROFILE_KEYS),
        "seeds": list(STAGE5_0F_SEEDS),
        "strategies": ["rolling", "fixed", "anchored"],
        "raw_runs": [],
        "summary": {},
        "low_n_disclosure": {"year": STAGE5_0F_LOW_N_YEAR},
    }
    parsed_cache = {}

    for target_col in STAGE5_0F_TARGETS:
        train_df, val_df, hold_df = target_splits[target_col]
        combined = pd.concat([train_df, val_df, hold_df], ignore_index=True)
        combined = _stage5_0f_with_year(combined)
        report["summary"].setdefault(target_col, {})

        windows = build_stage5_0f_windows(combined, target_col)
        grouped_runs = {}
        for profile_key in STAGE5_0F_PROFILE_KEYS:
            report["summary"][target_col].setdefault(profile_key, {})
            for window in windows:
                strategy = window["manifest"]["strategy"]
                test_year = int(window["manifest"]["test_year"])
                seed_runs = []
                for seed in STAGE5_0F_SEEDS:
                    run = evaluate_stage5_0f_window_seed(
                        window, profile_key=profile_key, target_col=target_col,
                        seed=seed, parsed_cache=parsed_cache)
                    seed_runs.append(run)
                    report["raw_runs"].append(run)
                grouped_runs[(profile_key, strategy, test_year)] = seed_runs

        for (profile_key, strategy, test_year), seed_runs in grouped_runs.items():
            report["summary"][target_col].setdefault(profile_key, {}).setdefault(strategy, {})
            report["summary"][target_col][profile_key][strategy][str(test_year)] = (
                summarize_stage5_0f_seed_runs(seed_runs)
            )

    report["decision"] = stage5_0f_stationarity_decision(report)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    return report
```

- [ ] **Step 4: Add CLI flag**

In `build_arg_parser()`, add:

```python
    parser.add_argument("--stage5-0f-signal-stationarity", action="store_true",
                        help="Stage 5.0f: диагностика стационарности H6_off05 breach-сигнала")
```

- [ ] **Step 5: Wire CLI in `main()`**

Add after Stage 5.0e block or before default Stage 5.0 runner:

```python
    if args.stage5_0f_signal_stationarity:
        print("\n" + "=" * 60)
        print("Загрузка buy splits для Stage 5.0f...")
        print("=" * 60)
        buy_train, buy_val, buy_hold = load_splits(target_col="buy_stop_broken_H6_off05_flag")
        report = run_stage5_0f_signal_stationarity(
            target_splits={
                "sell_stop_broken_H6_off05_flag": (train_df, val_stop_df, holdout_df),
                "buy_stop_broken_H6_off05_flag": (buy_train, buy_val, buy_hold),
            },
            output_path=STAGE5_0F_JSON_REPORT_PATH,
        )
        print("\n" + "=" * 60)
        print("Stage 5.0f: диагностика стационарности завершена")
        print(json.dumps(report["decision"], indent=2))
        print(json.dumps({"json": str(STAGE5_0F_JSON_REPORT_PATH)}, indent=2))
        print("=" * 60)
        return
```

- [ ] **Step 6: Run runner and CLI tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_stage5_0f_runner_writes_json tests/test_stage5_transformer_breach.py::test_stage5_0f_cli_argument_exists_in_build_arg_parser -q
```

Expected: PASS.

---

### Task 6: Execute Real Stage 5.0f Experiment

**Files:**
- Generate: `ML/reports/stage5_0f_signal_stationarity.json`
- No source edits expected unless a verified bug appears.

**Interfaces:**
- Consumes: CLI `--stage5-0f-signal-stationarity`
- Produces: structured JSON with `raw_runs`, `summary`, `split_manifest`, `low_n_disclosure`, `decision`

**Runtime note:** Full run trains 456 XGBoost models. At roughly 5-10 seconds per model, expected wall time is about 40-80 minutes on CPU. Run it as a long foreground diagnostic job and do not interpret lack of output for several minutes as a hang unless CPU/disk activity is also absent.

- [ ] **Step 1: Run focused Stage 5.0f tests before experiment**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py -q
```

Expected: PASS for the file-level test suite.

- [ ] **Step 2: Run real experiment**

Run:

```bash
./.venv/bin/python -m ML.baseline.benchmark_stage5_transformer_breach --stage5-0f-signal-stationarity
```

Expected: command exits `0` and prints JSON path ending with `ML/reports/stage5_0f_signal_stationarity.json`.

- [ ] **Step 3: Inspect structured artifact**

Run:

```bash
./.venv/bin/python - <<'PY'
import json
from pathlib import Path

path = Path("ML/reports/stage5_0f_signal_stationarity.json")
data = json.loads(path.read_text())
print(data["stage"])
print(data["status"])
print(data["decision"]["overall_verdict"])
print(len(data["raw_runs"]))
print(sorted(data["summary"].keys()))
PY
```

Expected output includes:

```text
5.0f_signal_stationarity
DIAGNOSTIC_ONLY
```

Expected `overall_verdict`: one of `temporal_decay`, `weak_signal`, `inconclusive`.

- [ ] **Step 4: Verify artifact has required sections**

Run:

```bash
./.venv/bin/python - <<'PY'
import json
from pathlib import Path

data = json.loads(Path("ML/reports/stage5_0f_signal_stationarity.json").read_text())
required = ["raw_runs", "summary", "decision", "low_n_disclosure"]
missing = [k for k in required if k not in data]
assert not missing, missing
for target in data["targets"]:
    assert target in data["summary"], target
    for profile in data["profiles"]:
        assert profile in data["summary"][target], (target, profile)
print("artifact_ok")
PY
```

Expected:

```text
artifact_ok
```

---

### Task 7: Report And Documentation Sync

**Files:**
- Create: `docs/reports/2026-06-23-stage5_0f-signal-stationarity.md`
- Modify: `CHANGELOG.md`
- Modify: `CONTEXT_HANDOFF.md`
- Modify: `docs/ML/benchmark_stage5_transformer_breach.py.md`
- Modify: `wiki/research/fractal-stop-research.md`
- Modify: `wiki/index.md` if the coverage summary needs updating
- Modify: `wiki/log.md`
- Generate: `wiki/REPO_integrity.md`

**Interfaces:**
- Consumes: `ML/reports/stage5_0f_signal_stationarity.json`
- Produces: canonical report and handoff state

- [ ] **Step 1: Read report rules**

Run:

```bash
sed -n '1,220p' docs/reports/README.md
```

Expected: confirms report requires header plus sections `Context`, `What Was Done`, `Changed Files`, `Verification`, `Results`, `Conclusions`, `Limitations / Open Questions`, `Next Step`, `Related Materials`.

- [ ] **Step 2: Extract decision numbers for report**

Run:

```bash
./.venv/bin/python - <<'PY'
import json
from pathlib import Path

data = json.loads(Path("ML/reports/stage5_0f_signal_stationarity.json").read_text())
print(json.dumps(data["decision"], indent=2))
PY
```

Expected: prints the final Stage 5.0f decision block.

- [ ] **Step 3: Create canonical report**

Create `docs/reports/2026-06-23-stage5_0f-signal-stationarity.md` with this structure and replace the bracketed values with exact values copied from the JSON artifact:

```markdown
# Stage 5.0f — диагностика стационарности сигнала

> **Дата**: 2026-06-23
> **Статус**: Completed
> **Вердикт**: [overall_verdict из JSON]
> **Цель**: Разделить H1 weak_signal и H2 temporal_decay для H6_off05 breach-сигнала
> **Уровень этапа**: поисковый
> **Related spec**: `docs/superpowers/specs/2026-06-23-stage5_0f-signal-stationarity-design.md`

## Context

Stage 5.0d исчерпал H6_off05 stop broken на 9 профилях, но не различил слабый сигнал и устаревание сигнала. Stage 5.0e показал, что уменьшение Transformer почти убирает overfit-drop, но не переоткрывает H6_off05. Stage 5.0f проверяет стационарность только на XGBoost, без Transformer и без торговой симуляции.

## What Was Done

- Rolling refit 8 лет → следующий год.
- Fixed baseline train-core ≤2019, val-stop 2020 → test по годам.
- Anchored expanding train≤T−1, val-stop T → test T+1.
- Профили: `base_raw_plus_time`, `structure_only`, `time_only`, `all100_relative_price_time`.
- Цели: sell и buy `H6_off05`.
- 3 seeds, median AUC/lift_30, bootstrap CI по строкам test.

## Changed Files

- `ML/baseline/benchmark_stage5_transformer_breach.py`
- `tests/test_stage5_transformer_breach.py`
- `ML/reports/stage5_0f_signal_stationarity.json`

## Verification

- `[вставить точный pytest command/output]`
- `[вставить команду реального эксперимента и факт успешного завершения]`
- JSON artifact: `ML/reports/stage5_0f_signal_stationarity.json`

## Results

Вставить краткую таблицу по sell/buy:

| Target | Verdict | Key Evidence |
|---|---|---|
| sell | `[sell verdict]` | `[коротко: rolling vs fixed по 2023-2025]` |
| buy | `[buy verdict]` | `[коротко: rolling vs fixed по 2023-2025]` |

2026 год показан только как `low_n_disclosure` и не входит в решение.

## Conclusions

Сформулировать вывод строго по JSON:

- Если `temporal_decay`: старые данные вредят или сигнал устаревает; следующий этап может проверять rolling 8yr development-window (7yr train-core + 1yr val-stop) + новый target, но 2023-2025 уже прожжены.
- Если `weak_signal`: H6_off05 слаб на текущих признаках; Stage 5.0d корректен как отрицательный вывод.
- Если `inconclusive`: природа отрицательного результата не установлена; закрытие ветки или один дополнительный diagnostic остаются управленческим решением.

## Limitations / Open Questions

- Stage 5.0f — diagnostic-only.
- 2023-2025 использованы для управленческого решения и больше не являются чистым holdout.
- 2026 — low-n disclosure.
- AUC/lift_30 не являются торговым PF.
- CI в JSON — median от per-seed bootstrap CI, не pooled CI.
- `lift_30` — bottom-30 risk lift; меньше = лучше для safe-zone фильтра.
- Вывод `time_only` относится только к XGBoost-ветке без `time_pos`.

## Next Step

Вставить следующий шаг из `decision.overall_verdict`.

## Related Materials

- `ML/reports/stage5_0f_signal_stationarity.json`
- `docs/superpowers/specs/2026-06-23-stage5_0f-signal-stationarity-design.md`
- `docs/reports/2026-06-23-stage5_0e-small-transformer-check.md`
- `docs/reports/2026-06-23-stage5_0d-diagnostic-screening.md`
```

- [ ] **Step 4: Update module documentation**

In `docs/ML/benchmark_stage5_transformer_breach.py.md`, add to outputs:

```markdown
- `ML/reports/stage5_0f_signal_stationarity.json` — structured artifact Stage 5.0f stationarity diagnostics.
```

Add to usage:

```bash
python -m ML.baseline.benchmark_stage5_transformer_breach --stage5-0f-signal-stationarity
```

Add bullet:

```markdown
- `--stage5-0f-signal-stationarity` — Stage 5.0f: XGBoost-only диагностика стационарности H6_off05 breach-сигнала через rolling/fixed/anchored windows, bootstrap CI и split manifest.
```

- [ ] **Step 5: Update `CHANGELOG.md`**

Add a new top entry:

```markdown
## [2026-06-23] — Stage 5.0f: диагностика стационарности сигнала

### Добавлено
- `--stage5-0f-signal-stationarity`
- `ML/reports/stage5_0f_signal_stationarity.json`
- `docs/reports/2026-06-23-stage5_0f-signal-stationarity.md`

### Методика
- XGBoost-only, без Transformer и без trade simulation.
- Rolling 8yr, fixed train≤2020 control, anchored expanding.
- Профили: `base_raw_plus_time`, `structure_only`, `time_only`, `all100_relative_price_time`.
- 3 seeds + bootstrap CI; 2026 только `low_n_disclosure`.
- 2023-2025 использованы для diagnostic management decision и больше не являются чистым holdout.

### Результаты
- **Вердикт:** `[overall_verdict из JSON]`.
- `[1-3 строки ключевого результата из отчёта]`
```

- [ ] **Step 6: Update `CONTEXT_HANDOFF.md`**

Replace current stage summary with Stage 5.0f outcome:

```markdown
## Текущий этап

Stage 5.0f завершён. Вердикт: **[overall_verdict]** — [краткое объяснение].

Статус проекта: **DIAGNOSTIC_ONLY**. 2023-2025 использованы для diagnostic management decision и больше не являются чистым holdout для будущих кандидатов.
```

Keep key files and next step aligned with the report.

- [ ] **Step 7: Update wiki**

Update `wiki/research/fractal-stop-research.md`:

- add Stage 5.0f to chronology;
- add conclusion after Stage 5.0e/5.0d conclusions;
- update open questions according to final verdict;
- add source link to `docs/reports/2026-06-23-stage5_0f-signal-stationarity.md`.

Update `wiki/log.md` with:

```markdown
## [2026-06-23] ingest | Stage 5.0f signal stationarity
- Обновлён `wiki/research/fractal-stop-research.md`: добавлен Stage 5.0f, verdict `[overall_verdict]`, последствия для holdout 2023-2025 и следующий шаг.
```

Update `wiki/index.md` only if the Fractal Stop coverage line still says coverage ends at 5.0e or 5.0d.

- [ ] **Step 8: Regenerate wiki integrity**

Run:

```bash
./.venv/bin/python wiki/wiki.py generate
```

Expected: command exits `0` and updates `wiki/REPO_integrity.md`.

---

### Task 8: Final Verification

**Files:**
- All modified files from Tasks 1-7

**Interfaces:**
- Consumes: implemented Stage 5.0f code, JSON artifact, report/docs/wiki
- Produces: final verification evidence

- [ ] **Step 1: Run full test suite**

Run:

```bash
./.venv/bin/python -m pytest tests/ -q
```

Expected: all tests pass. Previous baseline after Stage 5.0e was `795 passed`; new count should be higher by the Stage 5.0f tests.

- [ ] **Step 2: Verify Stage 5.0f JSON still loads**

Run:

```bash
./.venv/bin/python - <<'PY'
import json
from pathlib import Path

path = Path("ML/reports/stage5_0f_signal_stationarity.json")
data = json.loads(path.read_text())
assert data["stage"] == "5.0f_signal_stationarity"
assert data["status"] == "DIAGNOSTIC_ONLY"
assert data["decision"]["overall_verdict"] in {"temporal_decay", "weak_signal", "inconclusive"}
print("stage5_0f_json_ok")
PY
```

Expected:

```text
stage5_0f_json_ok
```

- [ ] **Step 3: Check diff summary**

Run:

```bash
git diff --stat
```

Expected: includes code, tests, JSON report, canonical report, docs, handoff, changelog, wiki updates. Do not revert unrelated existing changes.

- [ ] **Step 4: Record known errors if encountered**

If any MCP, DOC, or STRUCT errors were observed during the task, add a short note to the final response. Do not invent errors and do not search for them specially.

---

## Self-Review

- Spec coverage: rolling/fixed/anchored, 4 profiles, 2 targets, val-stop anti-leakage, transform train-core fit, split manifest, bootstrap CI, low-n 2026 disclosure, diagnostic-only status, holdout-burn disclosure, report/docs/wiki sync are each covered by tasks above.
- Placeholder scan: plan contains no unresolved placeholder markers, no unspecified test-writing step, and each implementation step names exact functions and paths.
- Type consistency: `build_stage5_0f_features()`, `fit_stage5_0f_transform_params()`, `build_stage5_0f_window()`, `evaluate_stage5_0f_window_seed()`, `summarize_stage5_0f_seed_runs()`, `stage5_0f_stationarity_decision()`, and `run_stage5_0f_signal_stationarity()` are introduced before later tasks consume them.
