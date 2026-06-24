# Stage 5.1 Structural Field Ablation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Реализовать диагностический Stage 5.1: drop-one и add-one абляцию 9 структурных фрактальных полей для `H6_off05 stop broken` на XGBoost.

**Architecture:** Расширяем существующий Stage 5 runner в `ML/baseline/benchmark_stage5_transformer_breach.py`, не создавая новый модуль. Используем существующие primitives Stage 5.0f: `build_flat_features`, `build_row_features`, `train_xgb_baseline`, `compute_metrics`, `compute_yearly_metrics`, `bootstrap_stage5_0f_metric_ci`, `_write_json_atomic`.

**Tech Stack:** Python, pandas, numpy, xgboost, sklearn metrics, pytest, project venv `./.venv/bin/python`.

## Global Constraints

- Работать на текущей ветке `Stage_5.1`; worktree запрещён.
- Stage 5.1 имеет статус `DIAGNOSTIC_ONLY`; нельзя выбирать торгового кандидата, winner или правило.
- Использовать только XGBoost; Transformer и торговую симуляцию не добавлять.
- Цели: `sell_stop_broken_H6_off05_flag`, `buy_stop_broken_H6_off05_flag`.
- Split: `train_core <= 2020`, `val_stop = 2021-2022`, `diagnostic_holdout = 2023-2025`, `low_n_disclosure = 2026` отдельно.
- Профили: `time_only`, `structure_full`, 9 `drop_*`, 9 `add_*`.
- `time_only` должен содержать ровно `hour_sin`, `hour_cos`, `dow_sin`, `dow_cos`; без ATR, `time_pos`, `year`, `month`.
- Token-поля Stage 5.1: `direction`, `front`, `back`, `strong`, `break`, `reverse`, `power`, `count`, `impulse`.
- `price`, `price_coord_atr`, `price_atr_scaled`, `ATR` не входят в Stage 5.1.
- `transform_variant = "asinh"`; для всех Stage 5.1 профилей `transform_params = {}` по смыслу, так как нет price/ATR token-полей.
- Seeds: `[42, 77, 123]`; результат агрегируется median по seed.
- `lift_30` трактовать как bottom-30 risk lift; меньше = лучше.
- JSON: `ML/reports/stage5_1_structural_field_ablation.json`.
- После изменений Python запускать `./.venv/bin/python -m pytest tests/ -q`.

---

## File Structure

- Modify: `ML/baseline/benchmark_stage5_transformer_breach.py`
  - Добавить константы Stage 5.1.
  - Добавить builders профилей и split.
  - Добавить оценку одного profile/target/seed.
  - Добавить summary, delta, paired bootstrap CI, field verdicts.
  - Добавить runner и CLI flag.
- Modify: `tests/test_stage5_transformer_breach.py`
  - Добавить unit/smoke tests для Stage 5.1 рядом с Stage 5.0f tests.
- Later, after real run outside this implementation plan:
  - Create: `ML/reports/stage5_1_structural_field_ablation.json`
  - Create: `docs/reports/YYYY-MM-DD-stage5_1-structural-field-ablation.md`
  - Modify: `CHANGELOG.md`, `CONTEXT_HANDOFF.md`, wiki through stage-reporting.

---

### Task 1: Constants And Profile Builders

**Files:**
- Modify: `ML/baseline/benchmark_stage5_transformer_breach.py`
- Modify: `tests/test_stage5_transformer_breach.py`

**Interfaces:**
- Produces: `STAGE5_1_TARGETS: list[str]`
- Produces: `STAGE5_1_FIELDS: list[str]`
- Produces: `STAGE5_1_PROFILE_KEYS: list[str]`
- Produces: `STAGE5_1_SEEDS: list[int]`
- Produces: `STAGE5_1_JSON_REPORT_PATH: Path`
- Produces: `_stage5_1_profile_for_key(profile_key: str) -> dict`
- Produces: `fit_stage5_1_transform_params(df: pd.DataFrame, profile_key: str, transform_variant: str = "asinh") -> dict`
- Produces: `build_stage5_1_features(df: pd.DataFrame, profile_key: str, transform_variant: str = "asinh", transform_params: dict | None = None) -> np.ndarray`

- [ ] **Step 1: Write failing constants/profile tests**

Add below Stage 5.0f tests in `tests/test_stage5_transformer_breach.py`:

```python
# ───────────────────────────────────────────────────────────────────────────
# Stage 5.1 tests
# ───────────────────────────────────────────────────────────────────────────

def test_stage5_1_constants_are_frozen():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    assert runner.STAGE5_1_TARGETS == [
        "sell_stop_broken_H6_off05_flag",
        "buy_stop_broken_H6_off05_flag",
    ]
    assert runner.STAGE5_1_FIELDS == [
        "direction", "front", "back", "strong", "break",
        "reverse", "power", "count", "impulse",
    ]
    assert runner.STAGE5_1_PROFILE_KEYS == [
        "time_only",
        "structure_full",
        "drop_direction",
        "drop_front",
        "drop_back",
        "drop_strong",
        "drop_break",
        "drop_reverse",
        "drop_power",
        "drop_count",
        "drop_impulse",
        "add_direction",
        "add_front",
        "add_back",
        "add_strong",
        "add_break",
        "add_reverse",
        "add_power",
        "add_count",
        "add_impulse",
    ]
    assert runner.STAGE5_1_SEEDS == [42, 77, 123]
    assert runner.STAGE5_1_BOOTSTRAP_N == 1000
    assert str(runner.STAGE5_1_JSON_REPORT_PATH).endswith(
        "stage5_1_structural_field_ablation.json"
    )


def test_stage5_1_profiles_have_expected_fields():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    time_profile = runner._stage5_1_profile_for_key("time_only")
    full_profile = runner._stage5_1_profile_for_key("structure_full")
    drop_front = runner._stage5_1_profile_for_key("drop_front")
    add_front = runner._stage5_1_profile_for_key("add_front")

    assert time_profile["token_fields"] == []
    assert time_profile["row_fields"] == runner.TIME_ONLY_ROW_FIELDS
    assert time_profile["seq_len"] == 0

    assert full_profile["token_fields"] == runner.STAGE5_1_FIELDS
    assert full_profile["row_fields"] == runner.TIME_ONLY_ROW_FIELDS
    assert full_profile["seq_len"] == 100

    assert "front" not in drop_front["token_fields"]
    assert len(drop_front["token_fields"]) == 8
    assert drop_front["row_fields"] == runner.TIME_ONLY_ROW_FIELDS

    assert add_front["token_fields"] == ["front"]
    assert add_front["row_fields"] == runner.TIME_ONLY_ROW_FIELDS
    assert add_front["seq_len"] == 100
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_stage5_1_constants_are_frozen tests/test_stage5_transformer_breach.py::test_stage5_1_profiles_have_expected_fields -q
```

Expected: FAIL because `STAGE5_1_*` and `_stage5_1_profile_for_key` are not defined.

- [ ] **Step 3: Add constants and profile builders**

In `ML/baseline/benchmark_stage5_transformer_breach.py`, add near Stage 5.0f constants:

```python
STAGE5_1_JSON_REPORT_PATH = REPORTS_DIR / "stage5_1_structural_field_ablation.json"
STAGE5_1_TARGETS = [
    "sell_stop_broken_H6_off05_flag",
    "buy_stop_broken_H6_off05_flag",
]
STAGE5_1_FIELDS = NO_PRICE_TOKEN_FIELDS.copy()
STAGE5_1_PROFILE_KEYS = (
    ["time_only", "structure_full"]
    + [f"drop_{field}" for field in STAGE5_1_FIELDS]
    + [f"add_{field}" for field in STAGE5_1_FIELDS]
)
STAGE5_1_SEEDS = [42, 77, 123]
STAGE5_1_VAL_YEARS = [2021, 2022]
STAGE5_1_HOLDOUT_YEARS = [2023, 2024, 2025]
STAGE5_1_LOW_N_YEAR = 2026
STAGE5_1_BOOTSTRAP_N = 1000
```

Add after `build_stage5_0f_features`:

```python
def _stage5_1_profile_for_key(profile_key: str) -> dict:
    """Build Stage 5.1 feature profile for time-only, full, drop-one, or add-one."""
    if profile_key == "time_only":
        return {
            "name": "stage5_1_time_only",
            "selection": "all100",
            "order": "freshness",
            "token_fields": [],
            "row_fields": TIME_ONLY_ROW_FIELDS.copy(),
            "uses_time": True,
            "seq_len": 0,
            "token_dim": 0,
            "row_dim": len(TIME_ONLY_ROW_FIELDS),
        }

    if profile_key == "structure_full":
        token_fields = STAGE5_1_FIELDS.copy()
    elif profile_key.startswith("drop_"):
        field = profile_key.removeprefix("drop_")
        if field not in STAGE5_1_FIELDS:
            raise ValueError(f"Unknown Stage 5.1 drop field: {field}")
        token_fields = [name for name in STAGE5_1_FIELDS if name != field]
    elif profile_key.startswith("add_"):
        field = profile_key.removeprefix("add_")
        if field not in STAGE5_1_FIELDS:
            raise ValueError(f"Unknown Stage 5.1 add field: {field}")
        token_fields = [field]
    else:
        raise ValueError(f"Unknown Stage 5.1 profile_key: {profile_key}")

    return {
        "name": f"stage5_1_{profile_key}",
        "selection": "all100",
        "order": "freshness",
        "token_fields": token_fields,
        "row_fields": TIME_ONLY_ROW_FIELDS.copy(),
        "uses_time": True,
        "seq_len": 100,
        "token_dim": len(token_fields),
        "row_dim": len(TIME_ONLY_ROW_FIELDS),
    }


def fit_stage5_1_transform_params(df: pd.DataFrame, profile_key: str,
                                  transform_variant: str = "asinh") -> dict:
    """Stage 5.1 has no price/ATR fields, so transform params are intentionally empty."""
    _ = df
    _ = transform_variant
    _stage5_1_profile_for_key(profile_key)
    return {}


def build_stage5_1_features(df: pd.DataFrame, profile_key: str,
                             transform_variant: str = "asinh",
                             transform_params: dict | None = None) -> np.ndarray:
    """Build XGBoost feature matrix for Stage 5.1 without leaking price/ATR fields."""
    profile = _stage5_1_profile_for_key(profile_key)
    if profile_key == "time_only":
        return build_row_features(
            df, profile, transform_variant=transform_variant,
            transform_params=transform_params).astype(np.float32)

    params = {} if transform_params is None else transform_params
    return build_flat_features(
        df, profile, transform_variant=transform_variant, transform_params=params)
```

- [ ] **Step 4: Add feature shape test**

Add:

```python
def test_build_stage5_1_features_shapes_and_no_atr_in_time_only():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    df = _make_synthetic_df(6, 100)

    X_time = runner.build_stage5_1_features(df, "time_only")
    X_full = runner.build_stage5_1_features(df, "structure_full")
    X_drop = runner.build_stage5_1_features(df, "drop_front")
    X_add = runner.build_stage5_1_features(df, "add_front")

    assert X_time.shape == (6, 4)
    assert X_full.shape == (6, 904)
    assert X_drop.shape == (6, 804)
    assert X_add.shape == (6, 104)
    assert runner.fit_stage5_1_transform_params(df, "structure_full") == {}
```

- [ ] **Step 5: Run profile tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_stage5_1_constants_are_frozen tests/test_stage5_transformer_breach.py::test_stage5_1_profiles_have_expected_fields tests/test_stage5_transformer_breach.py::test_build_stage5_1_features_shapes_and_no_atr_in_time_only -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add ML/baseline/benchmark_stage5_transformer_breach.py tests/test_stage5_transformer_breach.py
git commit -m "Add Stage 5.1 structural ablation profiles"
```

---

### Task 2: Stage 5.1 Split Builder

**Files:**
- Modify: `ML/baseline/benchmark_stage5_transformer_breach.py`
- Modify: `tests/test_stage5_transformer_breach.py`

**Interfaces:**
- Consumes: `_stage5_0f_with_year(df: pd.DataFrame) -> pd.DataFrame`
- Produces: `build_stage5_1_split(df: pd.DataFrame, target_col: str) -> dict`
- Produces split dict keys: `train_core`, `val_stop`, `diagnostic_holdout`, `low_n_disclosure`, `manifest`

- [ ] **Step 1: Write failing split test**

Add:

```python
def test_build_stage5_1_split_matches_spec_years():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    df = _make_stage5_0f_year_df()
    split = runner.build_stage5_1_split(df, "sell_stop_broken_H6_off05_flag")

    assert sorted(split["train_core"]["_year"].unique().tolist()) == list(range(2010, 2021))
    assert sorted(split["val_stop"]["_year"].unique().tolist()) == [2021, 2022]
    assert sorted(split["diagnostic_holdout"]["_year"].unique().tolist()) == [2023, 2024, 2025]
    assert sorted(split["low_n_disclosure"]["_year"].unique().tolist()) == [2026]
    assert split["manifest"]["target"] == "sell_stop_broken_H6_off05_flag"
    assert split["manifest"]["train_core"]["years"] == list(range(2010, 2021))
    assert split["manifest"]["val_stop"]["years"] == [2021, 2022]
    assert split["manifest"]["diagnostic_holdout"]["years"] == [2023, 2024, 2025]
    assert split["manifest"]["low_n_disclosure"]["years"] == [2026]
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_build_stage5_1_split_matches_spec_years -q
```

Expected: FAIL because `build_stage5_1_split` is not defined.

- [ ] **Step 3: Implement split builder**

Add near Stage 5.0f split helpers:

```python
def build_stage5_1_split(df: pd.DataFrame, target_col: str) -> dict:
    """Build fixed Stage 5.1 train/val/diagnostic split."""
    data = _stage5_0f_with_year(df)
    train_core = data[data["_year"] <= 2020].copy()
    val_stop = data[data["_year"].isin(STAGE5_1_VAL_YEARS)].copy()
    diagnostic_holdout = data[data["_year"].isin(STAGE5_1_HOLDOUT_YEARS)].copy()
    low_n_disclosure = data[data["_year"] == STAGE5_1_LOW_N_YEAR].copy()

    manifest = {
        "target": target_col,
        "train_core": _stage5_0f_split_manifest_part(train_core, target_col),
        "val_stop": _stage5_0f_split_manifest_part(val_stop, target_col),
        "diagnostic_holdout": _stage5_0f_split_manifest_part(diagnostic_holdout, target_col),
        "low_n_disclosure": _stage5_0f_split_manifest_part(low_n_disclosure, target_col),
        "holdout_disclosure": "2023-2025 are diagnostic disclosure only, already used in Stage 5.0f.",
    }
    return {
        "train_core": train_core,
        "val_stop": val_stop,
        "diagnostic_holdout": diagnostic_holdout,
        "low_n_disclosure": low_n_disclosure,
        "manifest": manifest,
    }
```

- [ ] **Step 4: Run split test**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_build_stage5_1_split_matches_spec_years -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add ML/baseline/benchmark_stage5_transformer_breach.py tests/test_stage5_transformer_breach.py
git commit -m "Add Stage 5.1 fixed diagnostic split"
```

---

### Task 3: Single Profile Evaluation

**Files:**
- Modify: `ML/baseline/benchmark_stage5_transformer_breach.py`
- Modify: `tests/test_stage5_transformer_breach.py`

**Interfaces:**
- Consumes: `build_stage5_1_split`
- Consumes: `build_stage5_1_features`
- Produces: `evaluate_stage5_1_profile_seed(split: dict, profile_key: str, target_col: str, seed: int, transform_variant: str = "asinh") -> dict`
- Produces run keys: `profile`, `target`, `seed`, `transform_variant`, `transform_params`, `train_core`, `val_stop`, `diagnostic_holdout`, `low_n_disclosure`, `yearly_val`, `yearly_diagnostic_holdout`, `split_manifest`, `predictions`

- [ ] **Step 1: Write failing evaluation test**

Add:

```python
def test_evaluate_stage5_1_profile_seed_returns_metrics_and_predictions(monkeypatch):
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    df = _make_stage5_0f_year_df()
    split = runner.build_stage5_1_split(df, "sell_stop_broken_H6_off05_flag")

    class DummyDMatrix:
        def __init__(self, X, label=None):
            self.X = X
            self.label = label

    class DummyModel:
        def predict(self, dmat):
            return np.linspace(0.05, 0.95, len(dmat.X))

    monkeypatch.setattr(runner.xgb, "DMatrix", DummyDMatrix)
    monkeypatch.setattr(runner, "train_xgb_baseline", lambda *a, **k: (DummyModel(), 0.61))
    monkeypatch.setattr(runner, "STAGE5_1_BOOTSTRAP_N", 20)

    result = runner.evaluate_stage5_1_profile_seed(
        split,
        profile_key="time_only",
        target_col="sell_stop_broken_H6_off05_flag",
        seed=42,
    )

    assert result["profile"] == "time_only"
    assert result["target"] == "sell_stop_broken_H6_off05_flag"
    assert result["seed"] == 42
    assert result["transform_params"] == {}
    assert result["val_stop"]["n"] == 8
    assert result["diagnostic_holdout"]["n"] == 12
    assert set(result["yearly_val"].keys()) == {"2021", "2022"}
    assert set(result["yearly_diagnostic_holdout"].keys()) == {"2023", "2024", "2025"}
    assert "auc_ci" in result["val_stop"]
    assert "auc_ci" in result["diagnostic_holdout"]
    assert len(result["predictions"]["val_stop"]) == 8
    assert len(result["predictions"]["diagnostic_holdout"]) == 12
    assert "split_manifest" in result
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_evaluate_stage5_1_profile_seed_returns_metrics_and_predictions -q
```

Expected: FAIL because `evaluate_stage5_1_profile_seed` is not defined.

- [ ] **Step 3: Implement profile evaluation**

Add after `evaluate_stage5_0f_window_seed`:

```python
def _stage5_1_metrics_with_ci(y_true: pd.Series, probs: np.ndarray, seed: int) -> dict:
    metrics = compute_metrics(y_true, pd.Series(probs))
    return {
        **{k: _safe(v) for k, v in metrics.items()},
        "auc_ci": bootstrap_stage5_0f_metric_ci(
            y_true, probs, "auc", n_boot=STAGE5_1_BOOTSTRAP_N, seed=seed),
        "lift_30_ci": bootstrap_stage5_0f_metric_ci(
            y_true, probs, "lift_30", n_boot=STAGE5_1_BOOTSTRAP_N, seed=seed),
    }


def evaluate_stage5_1_profile_seed(split: dict, profile_key: str, target_col: str,
                                   seed: int, transform_variant: str = "asinh") -> dict:
    """Train one Stage 5.1 XGBoost model for one profile/target/seed."""
    train_core = split["train_core"]
    val_stop = split["val_stop"]
    diagnostic_holdout = split["diagnostic_holdout"]
    low_n_disclosure = split["low_n_disclosure"]
    transform_params = fit_stage5_1_transform_params(
        train_core, profile_key, transform_variant=transform_variant)

    X_train = build_stage5_1_features(
        train_core, profile_key, transform_variant=transform_variant, transform_params=transform_params)
    X_val = build_stage5_1_features(
        val_stop, profile_key, transform_variant=transform_variant, transform_params=transform_params)
    X_holdout = build_stage5_1_features(
        diagnostic_holdout, profile_key, transform_variant=transform_variant, transform_params=transform_params)
    X_low_n = build_stage5_1_features(
        low_n_disclosure, profile_key, transform_variant=transform_variant, transform_params=transform_params)

    y_train = train_core[target_col]
    y_val = val_stop[target_col]
    y_holdout = diagnostic_holdout[target_col]
    y_low_n = low_n_disclosure[target_col]

    model, val_auc = train_xgb_baseline(X_train, y_train, X_val, y_val, seed=seed)
    train_probs = model.predict(xgb.DMatrix(X_train))
    val_probs = model.predict(xgb.DMatrix(X_val))
    holdout_probs = model.predict(xgb.DMatrix(X_holdout))
    low_n_probs = model.predict(xgb.DMatrix(X_low_n)) if len(low_n_disclosure) else np.asarray([])

    return {
        "profile": profile_key,
        "target": target_col,
        "seed": int(seed),
        "transform_variant": transform_variant,
        "transform_params": transform_params,
        "transform_params_fit_on": "train_core",
        "train_core": {k: _safe(v) for k, v in compute_metrics(y_train, pd.Series(train_probs)).items()},
        "val_stop": _stage5_1_metrics_with_ci(y_val, val_probs, seed),
        "diagnostic_holdout": _stage5_1_metrics_with_ci(y_holdout, holdout_probs, seed),
        "low_n_disclosure": _stage5_1_metrics_with_ci(y_low_n, low_n_probs, seed),
        "yearly_val": compute_yearly_metrics(val_stop, val_probs, target_col=target_col),
        "yearly_diagnostic_holdout": compute_yearly_metrics(
            diagnostic_holdout, holdout_probs, target_col=target_col),
        "split_manifest": split["manifest"],
        "val_auc_from_training": _safe(val_auc),
        "predictions": {
            "val_stop": [float(v) for v in val_probs],
            "diagnostic_holdout": [float(v) for v in holdout_probs],
            "low_n_disclosure": [float(v) for v in low_n_probs],
        },
        "labels": {
            "val_stop": [int(v) for v in y_val.tolist()],
            "diagnostic_holdout": [int(v) for v in y_holdout.tolist()],
            "low_n_disclosure": [int(v) for v in y_low_n.tolist()],
        },
    }
```

- [ ] **Step 4: Run evaluation test**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_evaluate_stage5_1_profile_seed_returns_metrics_and_predictions -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add ML/baseline/benchmark_stage5_transformer_breach.py tests/test_stage5_transformer_breach.py
git commit -m "Add Stage 5.1 profile seed evaluation"
```

---

### Task 4: Summary, Deltas, And Paired Bootstrap

**Files:**
- Modify: `ML/baseline/benchmark_stage5_transformer_breach.py`
- Modify: `tests/test_stage5_transformer_breach.py`

**Interfaces:**
- Consumes: seed runs from `evaluate_stage5_1_profile_seed`
- Produces: `bootstrap_stage5_1_delta_ci(y_true: list[int] | pd.Series, pred_a: list[float] | np.ndarray, pred_b: list[float] | np.ndarray, n_boot: int = STAGE5_1_BOOTSTRAP_N, seed: int = 42) -> dict`
- Produces: `summarize_stage5_1_seed_runs(runs: list[dict]) -> dict`
- Produces: `summarize_stage5_1_target(raw_runs: list[dict], target_col: str) -> dict`

- [ ] **Step 1: Write failing summary/delta tests**

Add:

```python
def test_bootstrap_stage5_1_delta_ci_is_deterministic():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    y = pd.Series([0, 0, 1, 1, 0, 1, 0, 1])
    a = np.array([0.1, 0.2, 0.8, 0.9, 0.3, 0.7, 0.4, 0.6])
    b = np.array([0.2, 0.3, 0.7, 0.8, 0.4, 0.6, 0.5, 0.55])

    ci1 = runner.bootstrap_stage5_1_delta_ci(y, a, b, n_boot=100, seed=42)
    ci2 = runner.bootstrap_stage5_1_delta_ci(y, a, b, n_boot=100, seed=42)

    assert ci1 == ci2
    assert ci1["metric"] == "auc_delta"
    assert ci1["low"] <= ci1["median"] <= ci1["high"]


def test_summarize_stage5_1_seed_runs_uses_median_and_seed_spread():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    runs = [
        {
            "train_core": {"auc": 0.70},
            "val_stop": {"auc": 0.62, "lift_30": 0.82, "auc_ci": {"low": 0.55, "high": 0.68}},
            "diagnostic_holdout": {"auc": 0.60, "lift_30": 0.80, "auc_ci": {"low": 0.53, "high": 0.66}},
            "low_n_disclosure": {"auc": 0.59, "lift_30": 0.78},
            "yearly_val": {"2021": {"auc": 0.61}, "2022": {"auc": 0.63}},
            "yearly_diagnostic_holdout": {"2023": {"auc": 0.59}, "2024": {"auc": 0.60}, "2025": {"auc": 0.61}},
            "split_manifest": {"target": "sell_stop_broken_H6_off05_flag"},
        },
        {
            "train_core": {"auc": 0.74},
            "val_stop": {"auc": 0.66, "lift_30": 0.72, "auc_ci": {"low": 0.60, "high": 0.70}},
            "diagnostic_holdout": {"auc": 0.64, "lift_30": 0.70, "auc_ci": {"low": 0.58, "high": 0.69}},
            "low_n_disclosure": {"auc": 0.62, "lift_30": 0.74},
            "yearly_val": {"2021": {"auc": 0.65}, "2022": {"auc": 0.67}},
            "yearly_diagnostic_holdout": {"2023": {"auc": 0.63}, "2024": {"auc": 0.64}, "2025": {"auc": 0.65}},
            "split_manifest": {"target": "sell_stop_broken_H6_off05_flag"},
        },
        {
            "train_core": {"auc": 0.72},
            "val_stop": {"auc": 0.64, "lift_30": 0.76, "auc_ci": {"low": 0.57, "high": 0.69}},
            "diagnostic_holdout": {"auc": 0.62, "lift_30": 0.75, "auc_ci": {"low": 0.55, "high": 0.67}},
            "low_n_disclosure": {"auc": 0.60, "lift_30": 0.76},
            "yearly_val": {"2021": {"auc": 0.63}, "2022": {"auc": 0.65}},
            "yearly_diagnostic_holdout": {"2023": {"auc": 0.61}, "2024": {"auc": 0.62}, "2025": {"auc": 0.63}},
            "split_manifest": {"target": "sell_stop_broken_H6_off05_flag"},
        },
    ]

    summary = runner.summarize_stage5_1_seed_runs(runs)

    assert summary["n_seed_runs"] == 3
    assert summary["val_stop"]["auc_median"] == pytest.approx(0.64)
    assert summary["diagnostic_holdout"]["auc_median"] == pytest.approx(0.62)
    assert summary["val_stop"]["auc_seed_min"] == pytest.approx(0.62)
    assert summary["val_stop"]["auc_seed_max"] == pytest.approx(0.66)
    assert summary["yearly_val"]["2021"]["auc_median"] == pytest.approx(0.63)
    assert summary["yearly_diagnostic_holdout"]["2025"]["auc_median"] == pytest.approx(0.63)
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_bootstrap_stage5_1_delta_ci_is_deterministic tests/test_stage5_transformer_breach.py::test_summarize_stage5_1_seed_runs_uses_median_and_seed_spread -q
```

Expected: FAIL because functions are not defined.

- [ ] **Step 3: Implement paired delta CI and seed summary**

Add:

```python
def bootstrap_stage5_1_delta_ci(y_true, pred_a, pred_b,
                                n_boot: int = STAGE5_1_BOOTSTRAP_N,
                                seed: int = 42) -> dict:
    """Paired bootstrap CI for AUC(profile_a) - AUC(profile_b)."""
    yt = pd.Series(y_true).reset_index(drop=True)
    pa = np.asarray(pred_a, dtype=float)
    pb = np.asarray(pred_b, dtype=float)
    n = len(yt)
    if n == 0 or yt.nunique() < 2:
        return {"metric": "auc_delta", "n_boot": int(n_boot), "low": None, "median": None, "high": None}

    rng = np.random.default_rng(seed)
    vals = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        sample_y = yt.iloc[idx].reset_index(drop=True)
        if sample_y.nunique() < 2:
            continue
        try:
            auc_a = roc_auc_score(sample_y, pa[idx])
            auc_b = roc_auc_score(sample_y, pb[idx])
        except ValueError:
            continue
        vals.append(float(auc_a - auc_b))

    if not vals:
        return {"metric": "auc_delta", "n_boot": int(n_boot), "low": None, "median": None, "high": None}

    arr = np.asarray(vals, dtype=float)
    return {
        "metric": "auc_delta",
        "n_boot": int(n_boot),
        "low": float(np.percentile(arr, 2.5)),
        "median": float(np.percentile(arr, 50.0)),
        "high": float(np.percentile(arr, 97.5)),
    }


def _min_or_none(values: list) -> float | None:
    clean = [float(v) for v in values if v is not None and np.isfinite(v)]
    return float(np.min(clean)) if clean else None


def _max_or_none(values: list) -> float | None:
    clean = [float(v) for v in values if v is not None and np.isfinite(v)]
    return float(np.max(clean)) if clean else None


def _stage5_1_period_summary(runs: list[dict], period_key: str) -> dict:
    aucs = [r[period_key].get("auc") for r in runs]
    lifts = [r[period_key].get("lift_30") for r in runs]
    auc_lows = [r[period_key].get("auc_ci", {}).get("low") for r in runs]
    auc_highs = [r[period_key].get("auc_ci", {}).get("high") for r in runs]
    return {
        "n": runs[0][period_key].get("n") if runs else 0,
        "auc_median": _median_or_none(aucs),
        "auc_seed_min": _min_or_none(aucs),
        "auc_seed_max": _max_or_none(aucs),
        "lift_30_median": _median_or_none(lifts),
        "lift_30_seed_min": _min_or_none(lifts),
        "lift_30_seed_max": _max_or_none(lifts),
        "auc_ci_low": _median_or_none(auc_lows),
        "auc_ci_high": _median_or_none(auc_highs),
    }


def _stage5_1_yearly_summary(runs: list[dict], yearly_key: str) -> dict:
    years = sorted({
        year
        for run in runs
        for year in run.get(yearly_key, {}).keys()
    })
    out = {}
    for year in years:
        aucs = [run.get(yearly_key, {}).get(year, {}).get("auc") for run in runs]
        lifts = [run.get(yearly_key, {}).get(year, {}).get("lift_30") for run in runs]
        out[year] = {
            "auc_median": _median_or_none(aucs),
            "auc_seed_min": _min_or_none(aucs),
            "auc_seed_max": _max_or_none(aucs),
            "lift_30_median": _median_or_none(lifts),
        }
    return out


def summarize_stage5_1_seed_runs(runs: list[dict]) -> dict:
    """Summarize Stage 5.1 seed-level runs by median and seed spread."""
    return {
        "n_seed_runs": int(len(runs)),
        "train_core": {
            "auc_median": _median_or_none([r["train_core"].get("auc") for r in runs]),
        },
        "val_stop": _stage5_1_period_summary(runs, "val_stop"),
        "diagnostic_holdout": _stage5_1_period_summary(runs, "diagnostic_holdout"),
        "low_n_disclosure": _stage5_1_period_summary(runs, "low_n_disclosure"),
        "yearly_val": _stage5_1_yearly_summary(runs, "yearly_val"),
        "yearly_diagnostic_holdout": _stage5_1_yearly_summary(runs, "yearly_diagnostic_holdout"),
        "split_manifest": runs[0].get("split_manifest") if runs else None,
    }
```

- [ ] **Step 4: Implement target summary with deltas**

Add:

```python
def _stage5_1_seed_auc_by_profile(raw_runs: list[dict], profile: str,
                                  period_key: str) -> dict[int, float | None]:
    return {
        int(run["seed"]): run[period_key].get("auc")
        for run in raw_runs
        if run["profile"] == profile
    }


def _stage5_1_run_by_profile_seed(raw_runs: list[dict], profile: str) -> dict[int, dict]:
    return {
        int(run["seed"]): run
        for run in raw_runs
        if run["profile"] == profile
    }


def _stage5_1_delta_summary(raw_runs: list[dict], profile: str,
                            baseline_profile: str, period_key: str) -> dict:
    profile_by_seed = _stage5_1_seed_auc_by_profile(raw_runs, profile, period_key)
    baseline_by_seed = _stage5_1_seed_auc_by_profile(raw_runs, baseline_profile, period_key)
    profile_runs = _stage5_1_run_by_profile_seed(raw_runs, profile)
    baseline_runs = _stage5_1_run_by_profile_seed(raw_runs, baseline_profile)
    deltas = []
    ci_lows = []
    ci_highs = []
    signs = []
    for seed, auc in profile_by_seed.items():
        base_auc = baseline_by_seed.get(seed)
        if auc is None or base_auc is None:
            continue
        delta = float(auc - base_auc)
        deltas.append(delta)
        signs.append(1 if delta > 0 else -1 if delta < 0 else 0)
        profile_run = profile_runs.get(seed)
        baseline_run = baseline_runs.get(seed)
        if profile_run and baseline_run:
            ci = bootstrap_stage5_1_delta_ci(
                profile_run["labels"][period_key],
                profile_run["predictions"][period_key],
                baseline_run["predictions"][period_key],
                n_boot=STAGE5_1_BOOTSTRAP_N,
                seed=seed,
            )
            ci_lows.append(ci.get("low"))
            ci_highs.append(ci.get("high"))
    return {
        "baseline_profile": baseline_profile,
        "period": period_key,
        "delta_median": _median_or_none(deltas),
        "delta_seed_min": _min_or_none(deltas),
        "delta_seed_max": _max_or_none(deltas),
        "delta_ci_low": _median_or_none(ci_lows),
        "delta_ci_high": _median_or_none(ci_highs),
        "delta_ci_method": "median_of_per_seed_paired_bootstrap_bounds",
        "positive_seed_count": int(sum(1 for s in signs if s > 0)),
        "negative_seed_count": int(sum(1 for s in signs if s < 0)),
        "zero_seed_count": int(sum(1 for s in signs if s == 0)),
    }


def summarize_stage5_1_target(raw_runs: list[dict], target_col: str) -> dict:
    """Summarize one Stage 5.1 target across profiles and add drop/add deltas."""
    target_runs = [r for r in raw_runs if r["target"] == target_col]
    summary = {}
    for profile in STAGE5_1_PROFILE_KEYS:
        runs = [r for r in target_runs if r["profile"] == profile]
        summary[profile] = summarize_stage5_1_seed_runs(runs)

    for field in STAGE5_1_FIELDS:
        drop_profile = f"drop_{field}"
        add_profile = f"add_{field}"
        summary[drop_profile]["delta_vs_structure_full"] = {
            "val_stop": _stage5_1_delta_summary(target_runs, drop_profile, "structure_full", "val_stop"),
            "diagnostic_holdout": _stage5_1_delta_summary(
                target_runs, drop_profile, "structure_full", "diagnostic_holdout"),
        }
        summary[add_profile]["delta_vs_time_only"] = {
            "val_stop": _stage5_1_delta_summary(target_runs, add_profile, "time_only", "val_stop"),
            "diagnostic_holdout": _stage5_1_delta_summary(
                target_runs, add_profile, "time_only", "diagnostic_holdout"),
        }
    return summary
```

- [ ] **Step 5: Run summary tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_bootstrap_stage5_1_delta_ci_is_deterministic tests/test_stage5_transformer_breach.py::test_summarize_stage5_1_seed_runs_uses_median_and_seed_spread -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add ML/baseline/benchmark_stage5_transformer_breach.py tests/test_stage5_transformer_breach.py
git commit -m "Add Stage 5.1 summary and delta helpers"
```

---

### Task 5: Field Verdicts

**Files:**
- Modify: `ML/baseline/benchmark_stage5_transformer_breach.py`
- Modify: `tests/test_stage5_transformer_breach.py`

**Interfaces:**
- Consumes: `summary[target][profile]`
- Produces: `stage5_1_field_verdicts(report: dict) -> dict`

- [ ] **Step 1: Write failing verdict test**

Add:

```python
def test_stage5_1_field_verdicts_classify_useful_noise_and_unclear():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    target = "sell_stop_broken_H6_off05_flag"
    report = {
        "summary": {
            target: {
                "drop_front": {
                    "delta_vs_structure_full": {
                        "val_stop": {
                            "delta_median": -0.02,
                            "delta_ci_low": -0.04,
                            "delta_ci_high": -0.01,
                            "negative_seed_count": 3,
                            "positive_seed_count": 0,
                        },
                    },
                    "yearly_val": {
                        "2021": {"auc_median": 0.60},
                        "2022": {"auc_median": 0.61},
                    },
                    "yearly_diagnostic_holdout": {
                        "2023": {"auc_median": 0.60},
                        "2024": {"auc_median": 0.61},
                        "2025": {"auc_median": 0.62},
                    },
                },
                "add_front": {
                    "delta_vs_time_only": {
                        "val_stop": {"delta_median": 0.03},
                        "diagnostic_holdout": {"delta_median": 0.01},
                    }
                },
                "drop_back": {
                    "delta_vs_structure_full": {
                        "val_stop": {
                            "delta_median": 0.02,
                            "delta_ci_low": 0.01,
                            "delta_ci_high": 0.04,
                            "negative_seed_count": 0,
                            "positive_seed_count": 3,
                        },
                    },
                    "yearly_val": {
                        "2021": {"auc_median": 0.64},
                        "2022": {"auc_median": 0.65},
                    },
                    "yearly_diagnostic_holdout": {
                        "2023": {"auc_median": 0.62},
                        "2024": {"auc_median": 0.63},
                        "2025": {"auc_median": 0.64},
                    },
                },
                "add_back": {
                    "delta_vs_time_only": {
                        "val_stop": {"delta_median": 0.0},
                        "diagnostic_holdout": {"delta_median": -0.01},
                    }
                },
                "structure_full": {
                    "yearly_val": {
                        "2021": {"auc_median": 0.62},
                        "2022": {"auc_median": 0.63},
                    },
                    "yearly_diagnostic_holdout": {
                        "2023": {"auc_median": 0.63},
                        "2024": {"auc_median": 0.62},
                        "2025": {"auc_median": 0.63},
                    }
                },
            }
        }
    }

    verdicts = runner.stage5_1_field_verdicts(report)

    assert verdicts["front"]["overall_verdict"] == "likely_useful"
    assert verdicts["back"]["overall_verdict"] == "likely_noise"
    assert verdicts["direction"]["overall_verdict"] == "mixed_or_unclear"
    assert verdicts["front"]["targets"][target]["drop_val_delta_ci_high"] == pytest.approx(-0.01)


def test_stage5_1_field_verdicts_conflicting_targets_are_unclear():
    import copy
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    sell = "sell_stop_broken_H6_off05_flag"
    buy = "buy_stop_broken_H6_off05_flag"
    useful_target_summary = {
        "drop_front": {
            "delta_vs_structure_full": {
                "val_stop": {
                    "delta_median": -0.02,
                    "delta_ci_low": -0.04,
                    "delta_ci_high": -0.01,
                    "negative_seed_count": 3,
                    "positive_seed_count": 0,
                },
            },
            "yearly_diagnostic_holdout": {
                "2023": {"auc_median": 0.60},
                "2024": {"auc_median": 0.61},
                "2025": {"auc_median": 0.62},
            },
        },
        "add_front": {
            "delta_vs_time_only": {
                "val_stop": {"delta_median": 0.03},
                "diagnostic_holdout": {"delta_median": 0.01},
            },
        },
        "structure_full": {
            "yearly_diagnostic_holdout": {
                "2023": {"auc_median": 0.63},
                "2024": {"auc_median": 0.62},
                "2025": {"auc_median": 0.63},
            },
        },
    }
    noise_target_summary = copy.deepcopy(useful_target_summary)
    noise_target_summary["drop_front"]["delta_vs_structure_full"]["val_stop"] = {
        "delta_median": 0.02,
        "delta_ci_low": 0.01,
        "delta_ci_high": 0.04,
        "negative_seed_count": 0,
        "positive_seed_count": 3,
    }
    noise_target_summary["drop_front"]["yearly_diagnostic_holdout"] = {
        "2023": {"auc_median": 0.64},
        "2024": {"auc_median": 0.63},
        "2025": {"auc_median": 0.65},
    }
    noise_target_summary["add_front"]["delta_vs_time_only"]["val_stop"] = {"delta_median": 0.0}

    report = {"summary": {sell: useful_target_summary, buy: noise_target_summary}}

    verdicts = runner.stage5_1_field_verdicts(report)

    assert verdicts["front"]["targets"][sell]["verdict"] == "likely_useful"
    assert verdicts["front"]["targets"][buy]["verdict"] == "likely_noise"
    assert verdicts["front"]["overall_verdict"] == "mixed_or_unclear"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_stage5_1_field_verdicts_classify_useful_noise_and_unclear tests/test_stage5_transformer_breach.py::test_stage5_1_field_verdicts_conflicting_targets_are_unclear -q
```

Expected: FAIL because `stage5_1_field_verdicts` is not defined.

- [ ] **Step 3: Implement verdict helper**

Add:

```python
def _stage5_1_yearly_drop_signs(target_summary: dict, field: str) -> list[int]:
    return _stage5_1_yearly_drop_signs_for_key(
        target_summary, field, "yearly_diagnostic_holdout", ["2023", "2024", "2025"])


def _stage5_1_yearly_val_drop_signs(target_summary: dict, field: str) -> list[int]:
    return _stage5_1_yearly_drop_signs_for_key(
        target_summary, field, "yearly_val", ["2021", "2022"])


def _stage5_1_yearly_drop_signs_for_key(target_summary: dict, field: str,
                                        yearly_key: str, years: list[str]) -> list[int]:
    drop = target_summary.get(f"drop_{field}", {})
    full = target_summary.get("structure_full", {})
    signs = []
    for year in years:
        drop_auc = drop.get(yearly_key, {}).get(year, {}).get("auc_median")
        full_auc = full.get(yearly_key, {}).get(year, {}).get("auc_median")
        if drop_auc is None or full_auc is None:
            continue
        delta = float(drop_auc - full_auc)
        signs.append(1 if delta > 0 else -1 if delta < 0 else 0)
    return signs


def _stage5_1_field_target_verdict(target_summary: dict, field: str) -> dict:
    drop = target_summary.get(f"drop_{field}", {})
    add = target_summary.get(f"add_{field}", {})
    drop_val = (
        drop.get("delta_vs_structure_full", {})
        .get("val_stop", {})
    )
    add_val = (
        add.get("delta_vs_time_only", {})
        .get("val_stop", {})
        .get("delta_median")
    )
    add_holdout = (
        add.get("delta_vs_time_only", {})
        .get("diagnostic_holdout", {})
        .get("delta_median")
    )
    drop_delta = drop_val.get("delta_median")
    drop_ci_low = drop_val.get("delta_ci_low")
    drop_ci_high = drop_val.get("delta_ci_high")
    yearly_signs = _stage5_1_yearly_drop_signs(target_summary, field)
    yearly_val_signs = _stage5_1_yearly_val_drop_signs(target_summary, field)
    yearly_negative = sum(1 for s in yearly_signs if s < 0)
    yearly_positive = sum(1 for s in yearly_signs if s > 0)
    negative_seed_count = int(drop_val.get("negative_seed_count") or 0)
    positive_seed_count = int(drop_val.get("positive_seed_count") or 0)
    useful_ci_or_seed_confirmed = (
        (drop_ci_high is not None and drop_ci_high < 0)
        or negative_seed_count == 3
    )
    noise_ci_or_seed_confirmed = (
        (drop_ci_low is not None and drop_ci_low > 0)
        or positive_seed_count == 3
    )

    useful = (
        drop_delta is not None
        and drop_delta < 0
        and yearly_negative >= 2
        and negative_seed_count >= 2
        and useful_ci_or_seed_confirmed
        and (
            (add_val is not None and add_val > 0)
            or (add_holdout is not None and add_holdout > 0)
        )
    )
    noise = (
        drop_delta is not None
        and drop_delta > 0
        and yearly_positive >= 2
        and positive_seed_count >= 2
        and noise_ci_or_seed_confirmed
        and add_val is not None
        and add_val <= 0
    )

    if useful:
        verdict = "likely_useful"
    elif noise:
        verdict = "likely_noise"
    else:
        verdict = "mixed_or_unclear"

    return {
        "verdict": verdict,
        "drop_val_delta_median": drop_delta,
        "drop_val_delta_ci_low": drop_ci_low,
        "drop_val_delta_ci_high": drop_ci_high,
        "drop_val_negative_seed_count": negative_seed_count,
        "drop_val_positive_seed_count": positive_seed_count,
        "yearly_val_drop_signs_2021_2022": yearly_val_signs,
        "yearly_drop_signs_2023_2025": yearly_signs,
        "add_val_delta_median": add_val,
        "add_holdout_delta_median": add_holdout,
    }


def stage5_1_field_verdicts(report: dict) -> dict:
    """Classify Stage 5.1 fields as diagnostic likely useful/noise/unclear."""
    verdicts = {}
    for field in STAGE5_1_FIELDS:
        per_target = {}
        target_verdicts = []
        for target in STAGE5_1_TARGETS:
            target_summary = report.get("summary", {}).get(target, {})
            target_result = _stage5_1_field_target_verdict(target_summary, field)
            per_target[target] = target_result
            target_verdicts.append(target_result["verdict"])

        if "likely_useful" in target_verdicts and "likely_noise" in target_verdicts:
            overall = "mixed_or_unclear"
        elif "likely_useful" in target_verdicts:
            overall = "likely_useful"
        elif "likely_noise" in target_verdicts:
            overall = "likely_noise"
        else:
            overall = "mixed_or_unclear"

        verdicts[field] = {
            "overall_verdict": overall,
            "targets": per_target,
            "diagnostic_only": True,
        }
    return verdicts
```

- [ ] **Step 4: Run verdict test**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_stage5_1_field_verdicts_classify_useful_noise_and_unclear tests/test_stage5_transformer_breach.py::test_stage5_1_field_verdicts_conflicting_targets_are_unclear -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add ML/baseline/benchmark_stage5_transformer_breach.py tests/test_stage5_transformer_breach.py
git commit -m "Add Stage 5.1 field verdict helper"
```

---

### Task 6: Runner And JSON Output

**Files:**
- Modify: `ML/baseline/benchmark_stage5_transformer_breach.py`
- Modify: `tests/test_stage5_transformer_breach.py`

**Interfaces:**
- Consumes: `build_stage5_1_split`
- Consumes: `evaluate_stage5_1_profile_seed`
- Consumes: `summarize_stage5_1_target`
- Consumes: `stage5_1_field_verdicts`
- Produces: `run_stage5_1_structural_field_ablation(target_splits: dict, output_path=STAGE5_1_JSON_REPORT_PATH) -> dict`

- [ ] **Step 1: Write failing runner test**

Add:

```python
def test_stage5_1_runner_writes_json(monkeypatch, tmp_path):
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    df = _make_stage5_0f_year_df()
    monkeypatch.setattr(runner, "STAGE5_1_PROFILE_KEYS", ["time_only", "structure_full"])
    monkeypatch.setattr(runner, "STAGE5_1_SEEDS", [42])
    monkeypatch.setattr(runner, "STAGE5_1_BOOTSTRAP_N", 20)

    class DummyDMatrix:
        def __init__(self, X, label=None):
            self.X = X
            self.label = label

    class DummyModel:
        def predict(self, dmat):
            return np.linspace(0.05, 0.95, len(dmat.X))

    monkeypatch.setattr(runner.xgb, "DMatrix", DummyDMatrix)
    monkeypatch.setattr(runner, "train_xgb_baseline", lambda *a, **k: (DummyModel(), 0.61))

    # Same fixture is passed three times intentionally: this is a JSON structure smoke test,
    # not a statistical correctness test.
    report = runner.run_stage5_1_structural_field_ablation(
        target_splits={
            "sell_stop_broken_H6_off05_flag": (df, df, df),
            "buy_stop_broken_H6_off05_flag": (df, df, df),
        },
        output_path=tmp_path / "stage5_1.json",
    )

    assert report["stage"] == "5.1_structural_field_ablation"
    assert report["status"] == "DIAGNOSTIC_ONLY"
    assert report["profiles"] == ["time_only", "structure_full"]
    assert report["fields"] == runner.STAGE5_1_FIELDS
    assert report["raw_runs"]
    assert "predictions" not in report["raw_runs"][0]
    assert "labels" not in report["raw_runs"][0]
    assert report["summary"]
    assert "field_verdicts" in report
    assert "multiple_testing_context" in report
    assert "holdout_disclosure" in report
    assert "transform_config" in report
    assert report["progress"]["done_runs"] == 4
    assert (tmp_path / "stage5_1.json").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_stage5_1_runner_writes_json -q
```

Expected: FAIL because `run_stage5_1_structural_field_ablation` is not defined.

- [ ] **Step 3: Implement runner**

Add:

```python
def _stage5_1_public_run(run: dict) -> dict:
    """Return JSON-safe run metadata without arrays used only for local delta CI."""
    return {
        key: value
        for key, value in run.items()
        if key not in {"predictions", "labels"}
    }


def run_stage5_1_structural_field_ablation(target_splits: dict,
                                           output_path=STAGE5_1_JSON_REPORT_PATH) -> dict:
    """Run Stage 5.1 structural fractal field ablation diagnostics."""
    started_at = time.time()
    total_runs = len(STAGE5_1_TARGETS) * len(STAGE5_1_PROFILE_KEYS) * len(STAGE5_1_SEEDS)
    report = {
        "stage": "5.1_structural_field_ablation",
        "status": "RUNNING",
        "level": "exploratory",
        "verdict_scope": "DIAGNOSTIC_ONLY",
        "targets": list(STAGE5_1_TARGETS),
        "fields": list(STAGE5_1_FIELDS),
        "profiles": list(STAGE5_1_PROFILE_KEYS),
        "seeds": list(STAGE5_1_SEEDS),
        "raw_runs": [],
        "summary": {},
        "field_verdicts": {},
        "multiple_testing_context": {
            "diagnostic_only": True,
            "correction_applied": None,
            "note": "No Bonferroni/FDR correction; likely_* labels are preliminary diagnostic categories.",
        },
        "holdout_disclosure": {
            "val_stop": "2021-2022 pooled primary diagnostic validation plus yearly disclosure.",
            "diagnostic_holdout": "2023-2025 already used in Stage 5.0f; disclosure only.",
            "low_n_disclosure": "2026 optional low-N disclosure, not used for verdict.",
        },
        "transform_config": {
            "transform_variant": "asinh",
            "transform_params_fit_on": "train_core",
            "stage5_1_transform_params": {},
            "reason": "Stage 5.1 excludes price/ATR fields; only structural tokens and clock row fields remain.",
        },
        "sanity_checks": {
            "time_only_row_fields": TIME_ONLY_ROW_FIELDS.copy(),
            "excluded_fields": ["price", "price_coord_atr", "price_atr_scaled", "ATR"],
            "expected_model_count": int(total_runs),
            "stage5_0d_no_price_reference": {
                "source": "docs/reports/2026-06-23-stage5_0d-diagnostic-screening.md",
                "sell_val_auc": 0.6693,
                "sell_holdout_auc": 0.6592,
                "comparison_note": "Compare to Stage 5.1 structure_full; not a PASS/FAIL gate.",
            },
            "stage5_1_structure_full_actual": {},
        },
        "progress": {
            "started_at_unix": started_at,
            "done_runs": 0,
            "total_runs": int(total_runs),
            "last_completed": None,
        },
    }

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    _write_json_atomic(output_path, report)

    for target_col in STAGE5_1_TARGETS:
        train_df, val_df, hold_df = target_splits[target_col]
        combined = pd.concat([train_df, val_df, hold_df], ignore_index=True)
        split = build_stage5_1_split(combined, target_col)
        report["summary"].setdefault(target_col, {})

        target_runs = []
        for profile_key in STAGE5_1_PROFILE_KEYS:
            for seed in STAGE5_1_SEEDS:
                run = evaluate_stage5_1_profile_seed(
                    split, profile_key=profile_key, target_col=target_col, seed=seed)
                run["elapsed_sec"] = round(time.time() - started_at, 1)
                target_runs.append(run)
                report["raw_runs"].append(_stage5_1_public_run(run))
                report["progress"]["done_runs"] += 1
                report["progress"]["last_completed"] = {
                    "target": target_col,
                    "profile": profile_key,
                    "seed": int(seed),
                    "val_auc": _safe(run["val_stop"].get("auc")),
                    "holdout_auc": _safe(run["diagnostic_holdout"].get("auc")),
                    "elapsed_sec": run["elapsed_sec"],
                }
                done_runs = report["progress"]["done_runs"]
                total = report["progress"]["total_runs"]
                last = report["progress"]["last_completed"]
                print(
                    f"[{done_runs}/{total}] {target_col} | {profile_key} | "
                    f"seed={seed} | val_auc={last['val_auc']} | "
                    f"holdout_auc={last['holdout_auc']}"
                )
                _write_json_atomic(output_path, report)

        report["summary"][target_col] = summarize_stage5_1_target(target_runs, target_col)
        structure_summary = report["summary"][target_col].get("structure_full", {})
        report["sanity_checks"]["stage5_1_structure_full_actual"][target_col] = {
            "val_auc_median": structure_summary.get("val_stop", {}).get("auc_median"),
            "diagnostic_holdout_auc_median": structure_summary.get("diagnostic_holdout", {}).get("auc_median"),
        }
        _write_json_atomic(output_path, report)

    report["field_verdicts"] = stage5_1_field_verdicts(report)
    report["status"] = "DIAGNOSTIC_ONLY"
    report["progress"]["finished_at_unix"] = time.time()
    report["progress"]["elapsed_sec"] = round(report["progress"]["finished_at_unix"] - started_at, 1)
    _write_json_atomic(output_path, report)
    return report
```

- [ ] **Step 4: Run runner test**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_stage5_1_runner_writes_json -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add ML/baseline/benchmark_stage5_transformer_breach.py tests/test_stage5_transformer_breach.py
git commit -m "Add Stage 5.1 structural ablation runner"
```

---

### Task 7: CLI Wiring

**Files:**
- Modify: `ML/baseline/benchmark_stage5_transformer_breach.py`
- Modify: `tests/test_stage5_transformer_breach.py`

**Interfaces:**
- Consumes: `run_stage5_1_structural_field_ablation`
- Produces CLI flag: `--stage5-1-structural-field-ablation`

- [ ] **Step 1: Write failing CLI parser test**

Add:

```python
def test_stage5_1_cli_argument_exists_in_build_arg_parser():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    parser = runner.build_arg_parser()
    args = parser.parse_args(["--stage5-1-structural-field-ablation"])
    assert args.stage5_1_structural_field_ablation is True
```

- [ ] **Step 2: Run parser test to verify it fails**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_stage5_1_cli_argument_exists_in_build_arg_parser -q
```

Expected: FAIL because CLI argument is missing.

- [ ] **Step 3: Add parser argument**

In `build_arg_parser()`, add after Stage 5.0f flag:

```python
parser.add_argument("--stage5-1-structural-field-ablation", action="store_true",
                    help="Stage 5.1: абляция структурных фрактальных полей H6_off05")
```

- [ ] **Step 4: Wire main branch**

In `main()`, after Stage 5.0f branch and before default Stage 5 logic, add:

```python
if args.stage5_1_structural_field_ablation:
    print("\n" + "=" * 60)
    print("Загрузка buy splits для Stage 5.1...")
    print("=" * 60)
    buy_train, buy_val, buy_hold = load_splits(target_col="buy_stop_broken_H6_off05_flag")
    report = run_stage5_1_structural_field_ablation(
        target_splits={
            "sell_stop_broken_H6_off05_flag": (train_df, val_stop_df, holdout_df),
            "buy_stop_broken_H6_off05_flag": (buy_train, buy_val, buy_hold),
        },
        output_path=STAGE5_1_JSON_REPORT_PATH,
    )
    print("\n" + "=" * 60)
    print("Stage 5.1: абляция структурных фрактальных полей завершена")
    print(json.dumps({
        "json": str(STAGE5_1_JSON_REPORT_PATH),
        "field_verdicts": report.get("field_verdicts", {}),
    }, indent=2))
    print("=" * 60)
    return
```

- [ ] **Step 5: Run CLI test**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_stage5_1_cli_argument_exists_in_build_arg_parser -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add ML/baseline/benchmark_stage5_transformer_breach.py tests/test_stage5_transformer_breach.py
git commit -m "Wire Stage 5.1 structural ablation CLI"
```

---

### Task 8: Full Verification

**Files:**
- No source edits unless tests expose a real bug.

**Interfaces:**
- Verifies all Stage 5.1 implementation tasks.

- [ ] **Step 1: Run focused Stage 5.1 tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py -q
```

Expected: PASS.

- [ ] **Step 2: Run full test suite**

Run:

```bash
./.venv/bin/python -m pytest tests/ -q
```

Expected: PASS.

- [ ] **Step 3: Commit fixes if needed**

If Step 1 or Step 2 exposed fixes, commit only those fixes:

```bash
git add ML/baseline/benchmark_stage5_transformer_breach.py tests/test_stage5_transformer_breach.py
git commit -m "Fix Stage 5.1 verification issues"
```

If no fixes were needed, do not create an empty commit.

---

### Task 9: Execute Diagnostic Experiment

**Files:**
- Create: `ML/reports/stage5_1_structural_field_ablation.json`

**Interfaces:**
- Consumes CLI flag: `--stage5-1-structural-field-ablation`
- Produces diagnostic JSON consumed by stage report.

- [ ] **Step 1: Run Stage 5.1 experiment**

Run:

```bash
./.venv/bin/python ML/baseline/benchmark_stage5_transformer_breach.py --stage5-1-structural-field-ablation
```

Expected:

```text
Stage 5.1: абляция структурных фрактальных полей завершена
```

Expected JSON exists:

```text
ML/reports/stage5_1_structural_field_ablation.json
```

Expected model count in JSON:

```text
progress.done_runs = 120
progress.total_runs = 120
status = DIAGNOSTIC_ONLY
```

- [ ] **Step 2: Inspect JSON sanity**

Run:

```bash
./.venv/bin/python - <<'PY'
import json
from pathlib import Path

path = Path("ML/reports/stage5_1_structural_field_ablation.json")
report = json.loads(path.read_text())
print("status", report["status"])
print("done", report["progress"]["done_runs"], "total", report["progress"]["total_runs"])
print("targets", report["targets"])
print("profiles", len(report["profiles"]))
print("raw_runs", len(report["raw_runs"]))
print("field_verdicts", report["field_verdicts"])
print("sanity_checks", report["sanity_checks"])
assert report["status"] == "DIAGNOSTIC_ONLY"
assert report["progress"]["done_runs"] == report["progress"]["total_runs"] == 120
assert len(report["profiles"]) == 20
assert len(report["raw_runs"]) == 120
assert "predictions" not in report["raw_runs"][0]
assert "labels" not in report["raw_runs"][0]
assert "stage5_0d_no_price_reference" in report["sanity_checks"]
assert "stage5_1_structure_full_actual" in report["sanity_checks"]
PY
```

Expected: command exits with code 0 and prints field verdicts.

- [ ] **Step 3: Commit experiment JSON**

```bash
git add ML/reports/stage5_1_structural_field_ablation.json
git commit -m "Run Stage 5.1 structural field ablation"
```

---

### Task 10: Stage Report And Documentation Sync

**Files:**
- Create: `docs/reports/YYYY-MM-DD-stage5_1-structural-field-ablation.md`
- Modify: `CHANGELOG.md`
- Modify: `CONTEXT_HANDOFF.md`
- Modify: wiki files through `python3 wiki/wiki.py generate` or project wiki ingest flow

**Interfaces:**
- Consumes: `ML/reports/stage5_1_structural_field_ablation.json`
- Produces canonical report and handoff updates.

- [ ] **Step 1: Use stage-reporting skill**

Before writing this task, read and follow:

```bash
sed -n '1,220p' .claude/skills/my/stage-reporting/SKILL.md
```

Required report content:

```text
Stage 5.1 is DIAGNOSTIC_ONLY.
It does not reopen H6_off05 as a trading candidate.
2023-2025 are diagnostic disclosure only.
time_only is the add-zero baseline.
drop-one answers whether a field can be removed from the full structure profile.
add-one answers whether a field adds standalone signal above clock features.
lift_30 is bottom-30 risk lift, lower is better.
No multiple-testing correction was applied; likely_* verdicts are preliminary.
```

- [ ] **Step 2: Write report from JSON**

Create:

```text
docs/reports/YYYY-MM-DD-stage5_1-structural-field-ablation.md
```

Include:

```text
JSON artifact: ML/reports/stage5_1_structural_field_ablation.json
Model budget: 120 XGBoost models
Profiles: time_only, structure_full, 9 drop-one, 9 add-one
Targets: sell_stop_broken_H6_off05_flag, buy_stop_broken_H6_off05_flag
Verdict table: one row per field with likely_useful / likely_noise / mixed_or_unclear
Top diagnostic observations by target
Limitations and prohibited conclusions
Next recommended step
```

- [ ] **Step 3: Update baton files**

Update:

```text
CHANGELOG.md
CONTEXT_HANDOFF.md
```

Keep entries concise. Include exact JSON/report paths and final Stage 5.1 status.

- [ ] **Step 4: Update wiki**

Run the project wiki flow used in previous stages:

```bash
python3 wiki/wiki.py generate
```

If the wiki skill requires a different ingest command, follow the skill instead.

- [ ] **Step 5: Final verification**

Run:

```bash
./.venv/bin/python -m pytest tests/ -q
python3 wiki/wiki.py verify
git status --short
```

Expected:

```text
pytest passes
wiki verify passes or reports only known generated-file differences
git status shows only intended Stage 5.1 report/docs/wiki files before final commit
```

- [ ] **Step 6: Commit stage report bundle**

```bash
git add docs/reports/ CHANGELOG.md CONTEXT_HANDOFF.md wiki/
git commit -m "Document Stage 5.1 structural field ablation"
```

---

## Self-Review Checklist

- Spec coverage: профили `time_only`, `structure_full`, `drop_*`, `add_*` покрыты Task 1.
- Spec coverage: fixed split `<=2020`, `2021-2022`, `2023-2025`, `2026` покрыт Task 2.
- Spec coverage: XGBoost-only evaluation, yearly metrics, CI, predictions для paired delta покрыты Task 3.
- Spec coverage: seed median/spread, deltas, paired bootstrap helper покрыты Task 4.
- Spec coverage: `likely_useful`, `likely_noise`, `mixed_or_unclear` покрыты Task 5.
- Spec coverage: JSON structure, multiple testing context, holdout disclosure, transform config covered Task 6.
- Spec coverage: CLI and real run covered Tasks 7 and 9.
- Spec coverage: canonical report/changelog/handoff/wiki covered Task 10.
- Known limitation: `drop_all_noise` is not implemented in the first pass. If 2-3 fields get `likely_noise`, create a follow-up mini-plan for one extra profile rather than mixing it into this implementation.
