# Stage 5.1b UpDn Field Ablation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Реализовать Stage 5.1b: preflight-аудит Up/Dn и `shift`, затем диагностическую абляцию 19 полей против baseline `clock + shift`.

**Architecture:** Расширяем существующий Stage 5.1 XGBoost runner в `ML/baseline/benchmark_stage5_transformer_breach.py`, но не меняем старые Stage 5.0/5.1 профили. Для Stage 5.1b вводим отдельные константы, извлекатель 20 полей + `log1p(shift)`, отдельный builder профилей, preflight, summary/group/verdict helpers и отдельный CLI-флаг.

**Tech Stack:** Python, pandas, numpy, scipy, scikit-learn metrics, XGBoost, pytest, JSON reports.

## Global Constraints

- Работать в текущей feature-ветке; worktree запрещён `AGENTS.md`.
- Использовать Python окружение проекта: `./.venv/bin/python`.
- После изменений в Python-коде запускать `./.venv/bin/python -m pytest tests/ -q`.
- `knowledge-rag` использовать только для поиска; источником истины являются открытые файлы.
- Stage 5.1b имеет статус `DIAGNOSTIC_ONLY`; не выбирать winner и не объявлять торговый сигнал.
- Не читать top-level колонки `up_3`, `dn_3`, ..., `up_48`, `dn_48` как признаки: это будущие target-метки текущей строки после `label_updn()`.
- Up/Dn признаки брать только из `fractal0..fractal99`, индексы 11-20 по `docs/schemas/fractal_v24_raw_price.schema.json`.
- `shift` брать из `fractalN` index 22 и добавлять как token-level `log1p(max(shift, 0))`.
- Baseline Stage 5.1b: `clock_shift = clock + shift`, где clock это `hour_sin`, `hour_cos`, `dow_sin`, `dow_cos`.
- Основной transform variant: `asinh`; `transform_params = {}` и `transform_params_fit_on = train_core`.
- Split повторяет Stage 5.1: `train_core <= 2020`, `val_stop = 2021-2022`, `diagnostic_holdout = 2023-2025`, `low_n_disclosure = 2026`.
- Бюджет полного прогона: 43 профиля × 2 цели × 3 seed = 258 XGBoost-моделей.

---

## File Structure

- Modify: `ML/baseline/benchmark_stage5_transformer_breach.py`
  - Добавить Stage 5.1b константы, извлечение полей, feature builder, preflight, runner, summary, verdicts, group analysis и CLI.
- Modify: `tests/test_stage5_transformer_breach.py`
  - Добавить unit/smoke тесты Stage 5.1b рядом с текущими Stage 5.1 тестами.
- Create after full run: `ML/reports/stage5_1b_updn_field_ablation.json`
  - Структурированный машинный отчёт Stage 5.1b.
- Create after full run: `docs/reports/YYYY-MM-DD-stage5_1b-updn-field-ablation.md`
  - Канонический текстовый отчёт, пишется после получения JSON, не в этом implementation-плане.

---

### Task 1: Stage 5.1b Constants And Field Extraction

**Files:**
- Modify: `ML/baseline/benchmark_stage5_transformer_breach.py`
- Test: `tests/test_stage5_transformer_breach.py`

**Interfaces:**
- Produces: `STAGE5_1B_TARGETS: list[str]`
- Produces: `STAGE5_1B_STRUCTURE_FIELDS: list[str]`
- Produces: `STAGE5_1B_UPDN_FIELDS: list[str]`
- Produces: `STAGE5_1B_FIELDS: list[str]`
- Produces: `STAGE5_1B_PROFILE_KEYS: list[str]`
- Produces: `STAGE5_1B_JSON_REPORT_PATH: Path`
- Produces: `extract_stage5_1b_fields(fractal_str: str) -> dict[str, float]`

- [ ] **Step 1: Write failing constants and extractor tests**

Add near the Stage 5.1 tests in `tests/test_stage5_transformer_breach.py`:

```python
def test_stage5_1b_constants_are_frozen():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    assert runner.STAGE5_1B_TARGETS == [
        "sell_stop_broken_H6_off05_flag",
        "buy_stop_broken_H6_off05_flag",
    ]
    assert runner.STAGE5_1B_STRUCTURE_FIELDS == [
        "direction", "front", "back", "strong", "break",
        "reverse", "power", "count", "impulse",
    ]
    assert runner.STAGE5_1B_UPDN_FIELDS == [
        "up_3", "dn_3", "up_6", "dn_6", "up_12", "dn_12",
        "up_24", "dn_24", "up_48", "dn_48",
    ]
    assert runner.STAGE5_1B_FIELDS == (
        runner.STAGE5_1B_STRUCTURE_FIELDS + runner.STAGE5_1B_UPDN_FIELDS
    )
    assert len(runner.STAGE5_1B_PROFILE_KEYS) == 43
    assert runner.STAGE5_1B_PROFILE_KEYS[:5] == [
        "clock_shift",
        "structure_full",
        "updn_full",
        "structure_plus_updn",
        "back_impulse_combo",
    ]
    assert str(runner.STAGE5_1B_JSON_REPORT_PATH).endswith(
        "stage5_1b_updn_field_ablation.json"
    )


def test_extract_stage5_1b_fields_reads_fractal_indices_and_log_shift():
    import math
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    fstr = _make_fractal_str([
        (1, 390.5),
        (2, -1),
        (3, 0.3),
        (4, 0.4),
        (5, 1),
        (6, 0),
        (7, 0.7),
        (8, 8.0),
        (9, 9.0),
        (10, 1.5),
        (11, 12.0),
        (12, 13.0),
        (13, 24.0),
        (14, 25.0),
        (15, 48.0),
        (16, 49.0),
        (17, 3.0),
        (18, 4.0),
        (19, 6.0),
        (20, 7.0),
        (22, 48),
    ])

    fields = runner.extract_stage5_1b_fields(fstr)

    assert fields["price"] == pytest.approx(390.5)
    assert fields["direction"] == pytest.approx(-1)
    assert fields["back"] == pytest.approx(0.4)
    assert fields["impulse"] == pytest.approx(1.5)
    assert fields["up_3"] == pytest.approx(3.0)
    assert fields["dn_3"] == pytest.approx(4.0)
    assert fields["up_6"] == pytest.approx(6.0)
    assert fields["dn_6"] == pytest.approx(7.0)
    assert fields["up_12"] == pytest.approx(12.0)
    assert fields["dn_12"] == pytest.approx(13.0)
    assert fields["up_24"] == pytest.approx(24.0)
    assert fields["dn_24"] == pytest.approx(25.0)
    assert fields["up_48"] == pytest.approx(48.0)
    assert fields["dn_48"] == pytest.approx(49.0)
    assert fields["shift"] == pytest.approx(math.log1p(48))


def test_extract_stage5_1b_fields_short_or_bad_fractal_returns_zeroes():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    short_fields = runner.extract_stage5_1b_fields("1:2:3")
    bad_shift = runner.extract_stage5_1b_fields(_make_fractal_str([(22, -10)]))

    assert set(short_fields) >= {"price", "direction", "up_3", "dn_48", "shift"}
    assert all(v == pytest.approx(0.0) for v in short_fields.values())
    assert bad_shift["shift"] == pytest.approx(0.0)
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_stage5_1b_constants_are_frozen tests/test_stage5_transformer_breach.py::test_extract_stage5_1b_fields_reads_fractal_indices_and_log_shift tests/test_stage5_transformer_breach.py::test_extract_stage5_1b_fields_short_or_bad_fractal_returns_zeroes -q
```

Expected: FAIL because Stage 5.1b constants and `extract_stage5_1b_fields` do not exist.

- [ ] **Step 3: Add constants and extractor**

Add near Stage 5.1 constants in `ML/baseline/benchmark_stage5_transformer_breach.py`:

```python
STAGE5_1B_JSON_REPORT_PATH = REPORTS_DIR / "stage5_1b_updn_field_ablation.json"
STAGE5_1B_TARGETS = [
    "sell_stop_broken_H6_off05_flag",
    "buy_stop_broken_H6_off05_flag",
]
STAGE5_1B_STRUCTURE_FIELDS = NO_PRICE_TOKEN_FIELDS.copy()
STAGE5_1B_UPDN_FIELDS = [
    "up_3", "dn_3", "up_6", "dn_6", "up_12", "dn_12",
    "up_24", "dn_24", "up_48", "dn_48",
]
STAGE5_1B_FIELDS = STAGE5_1B_STRUCTURE_FIELDS + STAGE5_1B_UPDN_FIELDS
STAGE5_1B_BASELINE_TOKEN_FIELDS = ["shift"]
STAGE5_1B_SEEDS = SEEDS.copy()
STAGE5_1B_BOOTSTRAP_N = STAGE5_1_BOOTSTRAP_N
STAGE5_1B_VAL_YEARS = STAGE5_1_VAL_YEARS
STAGE5_1B_HOLDOUT_YEARS = STAGE5_1_HOLDOUT_YEARS
STAGE5_1B_LOW_N_YEAR = STAGE5_1_LOW_N_YEAR

STAGE5_1B_BASE_PROFILE_KEYS = [
    "clock_shift",
    "structure_full",
    "updn_full",
    "structure_plus_updn",
    "back_impulse_combo",
]
STAGE5_1B_PROFILE_KEYS = (
    STAGE5_1B_BASE_PROFILE_KEYS
    + [f"drop_{field}" for field in STAGE5_1B_FIELDS]
    + [f"add_{field}" for field in STAGE5_1B_FIELDS]
)

STAGE5_1B_FIELD_TO_FRACTAL_INDEX = {
    "price": 1,
    "direction": 2,
    "front": 3,
    "back": 4,
    "strong": 5,
    "break": 6,
    "reverse": 7,
    "power": 8,
    "count": 9,
    "impulse": 10,
    "up_12": 11,
    "dn_12": 12,
    "up_24": 13,
    "dn_24": 14,
    "up_48": 15,
    "dn_48": 16,
    "up_3": 17,
    "dn_3": 18,
    "up_6": 19,
    "dn_6": 20,
}
```

Add after `extract_full29_fields`:

```python
def extract_stage5_1b_fields(fractal_str: str) -> dict[str, float]:
    """Extract named Stage 5.1b fields from one fractal string.

    Reads only fractalN payload fields, never top-level up_*/dn_* columns.
    """
    names = list(STAGE5_1B_FIELD_TO_FRACTAL_INDEX.keys()) + ["shift"]
    result = {name: 0.0 for name in names}
    parts = fractal_str.split(FRACTAL_SEP)
    if len(parts) < 23:
        return result

    for name, idx in STAGE5_1B_FIELD_TO_FRACTAL_INDEX.items():
        try:
            value = float(parts[idx])
        except (ValueError, IndexError):
            value = 0.0
        result[name] = float(np.nan_to_num(value, nan=0.0))

    try:
        raw_shift = float(parts[22])
    except (ValueError, IndexError):
        raw_shift = 0.0
    raw_shift = float(np.nan_to_num(raw_shift, nan=0.0))
    result["shift"] = float(np.log1p(max(raw_shift, 0.0)))
    return result
```

- [ ] **Step 4: Run focused tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_stage5_1b_constants_are_frozen tests/test_stage5_transformer_breach.py::test_extract_stage5_1b_fields_reads_fractal_indices_and_log_shift tests/test_stage5_transformer_breach.py::test_extract_stage5_1b_fields_short_or_bad_fractal_returns_zeroes -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add ML/baseline/benchmark_stage5_transformer_breach.py tests/test_stage5_transformer_breach.py
git commit -m "feat: add stage5.1b field extraction contract"
```

---

### Task 2: Stage 5.1b Feature Profiles And Feature Matrix Builder

**Files:**
- Modify: `ML/baseline/benchmark_stage5_transformer_breach.py`
- Test: `tests/test_stage5_transformer_breach.py`

**Interfaces:**
- Consumes: `extract_stage5_1b_fields(fractal_str: str) -> dict[str, float]`
- Produces: `_stage5_1b_profile_for_key(profile_key: str) -> dict`
- Produces: `fit_stage5_1b_transform_params(df: pd.DataFrame, profile_key: str, transform_variant: str = "asinh") -> dict`
- Produces: `build_stage5_1b_features(df: pd.DataFrame, profile_key: str, transform_variant: str = "asinh", transform_params: dict | None = None) -> np.ndarray`

- [ ] **Step 1: Write failing profile and shape tests**

Add:

```python
def test_stage5_1b_profiles_have_expected_fields():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    clock = runner._stage5_1b_profile_for_key("clock_shift")
    structure = runner._stage5_1b_profile_for_key("structure_full")
    updn = runner._stage5_1b_profile_for_key("updn_full")
    combined = runner._stage5_1b_profile_for_key("structure_plus_updn")
    combo = runner._stage5_1b_profile_for_key("back_impulse_combo")
    drop_back = runner._stage5_1b_profile_for_key("drop_back")
    drop_up3 = runner._stage5_1b_profile_for_key("drop_up_3")
    add_up3 = runner._stage5_1b_profile_for_key("add_up_3")

    assert clock["token_fields"] == ["shift"]
    assert clock["row_fields"] == runner.TIME_ONLY_ROW_FIELDS
    assert clock["seq_len"] == 100

    assert structure["token_fields"] == runner.STAGE5_1B_STRUCTURE_FIELDS + ["shift"]
    assert updn["token_fields"] == runner.STAGE5_1B_UPDN_FIELDS + ["shift"]
    assert combined["token_fields"] == runner.STAGE5_1B_FIELDS + ["shift"]
    assert combo["token_fields"] == ["shift", "back", "impulse"]

    assert "back" not in drop_back["token_fields"]
    assert "shift" in drop_back["token_fields"]
    assert "up_3" not in drop_up3["token_fields"]
    assert "shift" in drop_up3["token_fields"]
    assert add_up3["token_fields"] == ["shift", "up_3"]


def test_build_stage5_1b_features_shapes_and_log_shift():
    import math
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    df = _make_synthetic_df(6, 100)

    X_clock = runner.build_stage5_1b_features(df, "clock_shift")
    X_structure = runner.build_stage5_1b_features(df, "structure_full")
    X_updn = runner.build_stage5_1b_features(df, "updn_full")
    X_combined = runner.build_stage5_1b_features(df, "structure_plus_updn")
    X_combo = runner.build_stage5_1b_features(df, "back_impulse_combo")
    X_drop = runner.build_stage5_1b_features(df, "drop_back")
    X_add = runner.build_stage5_1b_features(df, "add_up_3")

    assert X_clock.shape == (6, 104)
    assert X_structure.shape == (6, 1004)
    assert X_updn.shape == (6, 1004)
    assert X_combined.shape == (6, 2004)
    assert X_combo.shape == (6, 304)
    assert X_drop.shape == (6, 904)
    assert X_add.shape == (6, 204)
    assert X_clock[0, 0] == pytest.approx(math.log1p(1))
    assert runner.fit_stage5_1b_transform_params(df, "structure_full") == {}


def test_stage5_1b_builder_does_not_read_top_level_updn_columns():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    df = _make_synthetic_df(2, 100)
    df["up_3"] = 999999.0
    df["dn_3"] = 999999.0

    X = runner.build_stage5_1b_features(df, "add_up_3")

    assert np.max(X[:, :200]) < 999999.0
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_stage5_1b_profiles_have_expected_fields tests/test_stage5_transformer_breach.py::test_build_stage5_1b_features_shapes_and_log_shift tests/test_stage5_transformer_breach.py::test_stage5_1b_builder_does_not_read_top_level_updn_columns -q
```

Expected: FAIL because Stage 5.1b profile builder and feature builder do not exist.

- [ ] **Step 3: Add Stage 5.1b profile builder**

Add after `build_stage5_1_features`:

```python
def _stage5_1b_profile_for_key(profile_key: str) -> dict:
    """Build Stage 5.1b profile with clock + token-level shift baseline."""
    if profile_key == "clock_shift":
        token_fields = ["shift"]
    elif profile_key == "structure_full":
        token_fields = STAGE5_1B_STRUCTURE_FIELDS + ["shift"]
    elif profile_key == "updn_full":
        token_fields = STAGE5_1B_UPDN_FIELDS + ["shift"]
    elif profile_key == "structure_plus_updn":
        token_fields = STAGE5_1B_FIELDS + ["shift"]
    elif profile_key == "back_impulse_combo":
        token_fields = ["shift", "back", "impulse"]
    elif profile_key.startswith("drop_"):
        field = profile_key.removeprefix("drop_")
        if field in STAGE5_1B_STRUCTURE_FIELDS:
            token_fields = [name for name in STAGE5_1B_STRUCTURE_FIELDS if name != field] + ["shift"]
        elif field in STAGE5_1B_UPDN_FIELDS:
            token_fields = [name for name in STAGE5_1B_UPDN_FIELDS if name != field] + ["shift"]
        else:
            raise ValueError(f"Unknown Stage 5.1b drop field: {field}")
    elif profile_key.startswith("add_"):
        field = profile_key.removeprefix("add_")
        if field not in STAGE5_1B_FIELDS:
            raise ValueError(f"Unknown Stage 5.1b add field: {field}")
        token_fields = ["shift", field]
    else:
        raise ValueError(f"Unknown Stage 5.1b profile_key: {profile_key}")

    return {
        "name": f"stage5_1b_{profile_key}",
        "selection": "all100",
        "order": "freshness",
        "token_fields": token_fields,
        "row_fields": TIME_ONLY_ROW_FIELDS.copy(),
        "uses_time": True,
        "seq_len": 100,
        "token_dim": len(token_fields),
        "row_dim": len(TIME_ONLY_ROW_FIELDS),
        "stage5_1b": True,
    }
```

- [ ] **Step 4: Add Stage 5.1b feature builder**

Add:

```python
def fit_stage5_1b_transform_params(df: pd.DataFrame, profile_key: str,
                                   transform_variant: str = "asinh") -> dict:
    """Stage 5.1b has fixed raw Up/Dn and log1p shift; no fitted params."""
    _ = df
    _ = transform_variant
    _stage5_1b_profile_for_key(profile_key)
    return {}


def build_stage5_1b_features(df: pd.DataFrame, profile_key: str,
                             transform_variant: str = "asinh",
                             transform_params: dict | None = None) -> np.ndarray:
    """Build flattened XGBoost features for Stage 5.1b profiles."""
    _ = transform_variant
    _ = transform_params
    profile = _stage5_1b_profile_for_key(profile_key)
    token_fields = profile["token_fields"]
    n_samples = len(df)
    seq_len = profile["seq_len"]
    token_dim = profile["token_dim"]
    tokens = np.zeros((n_samples, seq_len, token_dim), dtype=np.float32)
    mask = np.zeros((n_samples, seq_len), dtype=bool)

    for sample_idx in range(n_samples):
        valid_count = 0
        for f_idx in range(N_FRACTALS):
            col = f"fractal{f_idx}"
            if col not in df.columns:
                break
            fstr = str(df[col].iloc[sample_idx])
            if not fstr or fstr == "nan":
                continue
            fields = extract_stage5_1b_fields(fstr)
            values = np.asarray([fields[name] for name in token_fields], dtype=np.float32)
            if not np.any(values != 0):
                continue
            if valid_count < seq_len:
                tokens[sample_idx, valid_count, :] = values
                mask[sample_idx, valid_count] = True
            valid_count += 1

    row_features = build_row_features(df, profile, transform_variant="asinh", transform_params={})
    flat_tokens = tokens.reshape(n_samples, seq_len * token_dim)
    return np.concatenate([flat_tokens, row_features.astype(np.float32)], axis=1).astype(np.float32)
```

- [ ] **Step 5: Run focused tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_stage5_1b_profiles_have_expected_fields tests/test_stage5_transformer_breach.py::test_build_stage5_1b_features_shapes_and_log_shift tests/test_stage5_transformer_breach.py::test_stage5_1b_builder_does_not_read_top_level_updn_columns -q
```

Expected: PASS.

- [ ] **Step 6: Run legacy Stage 5.1 shape tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_stage5_1_profiles_have_expected_fields tests/test_stage5_transformer_breach.py::test_build_stage5_1_features_shapes_and_no_atr_in_time_only -q
```

Expected: PASS. This proves Stage 5.1 profile behavior was not silently changed.

- [ ] **Step 7: Commit**

```bash
git add ML/baseline/benchmark_stage5_transformer_breach.py tests/test_stage5_transformer_breach.py
git commit -m "feat: build stage5.1b feature profiles"
```

---

### Task 3: Stage 5.1b Preflight Audit

**Files:**
- Modify: `ML/baseline/benchmark_stage5_transformer_breach.py`
- Test: `tests/test_stage5_transformer_breach.py`

**Interfaces:**
- Consumes: `extract_stage5_1b_fields(fractal_str: str) -> dict[str, float]`
- Produces: `run_stage5_1b_preflight(split: dict, target_col: str) -> dict`
- Produces: `stage5_1b_preflight_passed(preflight: dict) -> bool`

- [ ] **Step 1: Write failing preflight tests**

Add:

```python
def test_stage5_1b_preflight_reports_contract_maturity_shift_and_correlations():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    df = _make_stage5_0f_year_df()
    split = runner.build_stage5_1_split(df, "sell_stop_broken_H6_off05_flag")

    preflight = runner.run_stage5_1b_preflight(split, "sell_stop_broken_H6_off05_flag")

    assert preflight["source_check"]["uses_fractal_columns_only"] is True
    assert preflight["source_check"]["forbidden_top_level_updn_columns_used"] is False
    assert preflight["contract"]["expected_num_fields"] == 23
    assert preflight["contract"]["short_fractal_count"] == 0
    assert preflight["monotonicity"]["violations_total"] == 0
    assert set(preflight["maturity"]["train_core"].keys()) == {"3", "6", "12", "24", "48"}
    assert "p50" in preflight["shift_distribution"]["train_core"]
    assert "up_3" in preflight["updn_shift_correlation"]["train_core"]
    assert "up_3_over_atr" in preflight["updn_atr_disclosure"]["train_core"]
    assert runner.stage5_1b_preflight_passed(preflight) is True


def test_stage5_1b_preflight_fails_on_monotonicity_violation():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    df = _make_stage5_0f_year_df()
    bad = _make_fractal_str([
        (11, 10.0),
        (13, 5.0),
        (15, 4.0),
        (17, 20.0),
        (19, 15.0),
        (22, 48),
    ])
    df.loc[df.index[0], "fractal0"] = bad
    split = runner.build_stage5_1_split(df, "sell_stop_broken_H6_off05_flag")

    preflight = runner.run_stage5_1b_preflight(split, "sell_stop_broken_H6_off05_flag")

    assert preflight["monotonicity"]["violations_total"] > 0
    assert runner.stage5_1b_preflight_passed(preflight) is False
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_stage5_1b_preflight_reports_contract_maturity_shift_and_correlations tests/test_stage5_transformer_breach.py::test_stage5_1b_preflight_fails_on_monotonicity_violation -q
```

Expected: FAIL because preflight functions do not exist.

- [ ] **Step 3: Add preflight helpers**

Add:

```python
def _stage5_1b_raw_shift(fractal_str: str) -> float:
    parts = fractal_str.split(FRACTAL_SEP)
    if len(parts) < 23:
        return 0.0
    try:
        return float(np.nan_to_num(float(parts[22]), nan=0.0))
    except (ValueError, IndexError):
        return 0.0


def _stage5_1b_collect_fractals(df: pd.DataFrame) -> list[dict]:
    records = []
    for row_idx in range(len(df)):
        atr = pd.to_numeric(pd.Series([df["ATR"].iloc[row_idx]]), errors="coerce").iloc[0] if "ATR" in df.columns else np.nan
        for f_idx in range(N_FRACTALS):
            col = f"fractal{f_idx}"
            if col not in df.columns:
                break
            fstr = str(df[col].iloc[row_idx])
            if not fstr or fstr == "nan":
                continue
            parts = fstr.split(FRACTAL_SEP)
            fields = extract_stage5_1b_fields(fstr)
            raw_shift = max(_stage5_1b_raw_shift(fstr), 0.0)
            records.append({
                "row_idx": int(row_idx),
                "fractal_idx": int(f_idx),
                "num_fields": int(len(parts)),
                "fields": fields,
                "raw_shift": float(raw_shift),
                "atr": float(atr) if np.isfinite(atr) and atr > 0 else None,
            })
    return records


def _stage5_1b_shift_distribution(records: list[dict]) -> dict:
    shifts = np.asarray([r["raw_shift"] for r in records], dtype=float)
    if len(shifts) == 0:
        return {"n": 0, "p50": None, "p90": None, "p95": None, "max": None}
    out = {
        "n": int(len(shifts)),
        "p50": float(np.percentile(shifts, 50)),
        "p90": float(np.percentile(shifts, 90)),
        "p95": float(np.percentile(shifts, 95)),
        "max": float(np.max(shifts)),
    }
    for horizon in [3, 6, 12, 24, 48]:
        out[f"share_shift_ge_{horizon}"] = float(np.mean(shifts >= horizon))
    return out


def _stage5_1b_maturity(records: list[dict]) -> dict:
    shifts = np.asarray([r["raw_shift"] for r in records], dtype=float)
    out = {}
    for horizon in [3, 6, 12, 24, 48]:
        out[str(horizon)] = {
            "n": int(len(shifts)),
            "mature_count": int(np.sum(shifts >= horizon)) if len(shifts) else 0,
            "mature_share": float(np.mean(shifts >= horizon)) if len(shifts) else None,
            "non_mature_share": float(np.mean(shifts < horizon)) if len(shifts) else None,
        }
    return out


def _stage5_1b_monotonicity(records: list[dict]) -> dict:
    violations = []
    for r in records:
        f = r["fields"]
        up = [f["up_3"], f["up_6"], f["up_12"], f["up_24"], f["up_48"]]
        dn = [f["dn_3"], f["dn_6"], f["dn_12"], f["dn_24"], f["dn_48"]]
        if any(up[i] > up[i + 1] for i in range(len(up) - 1)):
            violations.append({"row_idx": r["row_idx"], "fractal_idx": r["fractal_idx"], "side": "up"})
        if any(dn[i] > dn[i + 1] for i in range(len(dn) - 1)):
            violations.append({"row_idx": r["row_idx"], "fractal_idx": r["fractal_idx"], "side": "dn"})
    return {
        "violations_total": int(len(violations)),
        "examples": violations[:20],
    }


def _stage5_1b_updn_shift_correlation(records: list[dict]) -> dict:
    from scipy.stats import pearsonr, spearmanr

    out = {}
    shifts = np.asarray([np.log1p(r["raw_shift"]) for r in records], dtype=float)
    for field in STAGE5_1B_UPDN_FIELDS:
        vals = np.asarray([r["fields"][field] for r in records], dtype=float)
        if len(vals) < 3 or np.nanstd(vals) == 0 or np.nanstd(shifts) == 0:
            out[field] = {"pearson": None, "spearman": None, "n": int(len(vals))}
            continue
        pear = pearsonr(vals, shifts)
        spear = spearmanr(vals, shifts)
        out[field] = {
            "pearson": float(pear.statistic) if np.isfinite(pear.statistic) else None,
            "spearman": float(spear.statistic) if np.isfinite(spear.statistic) else None,
            "n": int(len(vals)),
        }
    return out


def _stage5_1b_updn_atr_disclosure(records: list[dict]) -> dict:
    out = {}
    for field in STAGE5_1B_UPDN_FIELDS:
        vals = [
            r["fields"][field] / r["atr"]
            for r in records
            if r["atr"] is not None and r["atr"] > 0
        ]
        arr = np.asarray(vals, dtype=float)
        key = f"{field}_over_atr"
        out[key] = {
            "n": int(len(arr)),
            "p50": float(np.percentile(arr, 50)) if len(arr) else None,
            "p90": float(np.percentile(arr, 90)) if len(arr) else None,
            "p95": float(np.percentile(arr, 95)) if len(arr) else None,
            "max": float(np.max(arr)) if len(arr) else None,
        }
    return out
```

- [ ] **Step 4: Add public preflight functions**

Add:

```python
def run_stage5_1b_preflight(split: dict, target_col: str) -> dict:
    """Audit Stage 5.1b field contract before full model training."""
    sections = {
        "train_core": split["train_core"],
        "val_stop": split["val_stop"],
        "diagnostic_holdout": split["diagnostic_holdout"],
        "low_n_disclosure": split["low_n_disclosure"],
    }
    collected = {name: _stage5_1b_collect_fractals(df) for name, df in sections.items()}
    all_records = [r for records in collected.values() for r in records]
    short_count = sum(1 for r in all_records if r["num_fields"] < 23)
    monotonicity = _stage5_1b_monotonicity(all_records)

    return {
        "target": target_col,
        "source_check": {
            "uses_fractal_columns_only": True,
            "forbidden_top_level_updn_columns_used": False,
            "fractal_field_indices": STAGE5_1B_FIELD_TO_FRACTAL_INDEX.copy(),
            "shift_index": 22,
        },
        "contract": {
            "expected_num_fields": 23,
            "observed_fractal_count": int(len(all_records)),
            "short_fractal_count": int(short_count),
            "short_fractal_rate": float(short_count / len(all_records)) if all_records else None,
        },
        "monotonicity": monotonicity,
        "maturity": {name: _stage5_1b_maturity(records) for name, records in collected.items()},
        "shift_distribution": {name: _stage5_1b_shift_distribution(records) for name, records in collected.items()},
        "updn_shift_correlation": {
            "train_core": _stage5_1b_updn_shift_correlation(collected["train_core"]),
        },
        "updn_atr_disclosure": {
            name: _stage5_1b_updn_atr_disclosure(records) for name, records in collected.items()
        },
        "pass": bool(short_count == 0 and monotonicity["violations_total"] == 0),
    }


def stage5_1b_preflight_passed(preflight: dict) -> bool:
    return bool(
        preflight.get("source_check", {}).get("uses_fractal_columns_only") is True
        and preflight.get("source_check", {}).get("forbidden_top_level_updn_columns_used") is False
        and preflight.get("contract", {}).get("short_fractal_count") == 0
        and preflight.get("monotonicity", {}).get("violations_total") == 0
    )
```

- [ ] **Step 5: Run focused tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_stage5_1b_preflight_reports_contract_maturity_shift_and_correlations tests/test_stage5_transformer_breach.py::test_stage5_1b_preflight_fails_on_monotonicity_violation -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add ML/baseline/benchmark_stage5_transformer_breach.py tests/test_stage5_transformer_breach.py
git commit -m "feat: add stage5.1b preflight audit"
```

---

### Task 4: Stage 5.1b Training, Summary, Deltas, Verdicts, And Group Analysis

**Files:**
- Modify: `ML/baseline/benchmark_stage5_transformer_breach.py`
- Test: `tests/test_stage5_transformer_breach.py`

**Interfaces:**
- Consumes: `build_stage5_1_split(df: pd.DataFrame, target_col: str) -> dict`
- Consumes: `build_stage5_1b_features(...) -> np.ndarray`
- Consumes: `_stage5_1_metrics_with_ci(...) -> dict`
- Consumes: `_stage5_1_delta_summary(...) -> dict`
- Produces: `evaluate_stage5_1b_profile_seed(split: dict, profile_key: str, target_col: str, seed: int, transform_variant: str = "asinh") -> dict`
- Produces: `summarize_stage5_1b_target(raw_runs: list[dict], target_col: str) -> dict`
- Produces: `stage5_1b_field_verdicts(report: dict) -> dict`
- Produces: `stage5_1b_group_analysis(report: dict) -> dict`

- [ ] **Step 1: Write failing evaluation and summary tests**

Add:

```python
def test_evaluate_stage5_1b_profile_seed_returns_metrics_and_predictions(monkeypatch):
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
    monkeypatch.setattr(runner, "STAGE5_1B_BOOTSTRAP_N", 20)

    result = runner.evaluate_stage5_1b_profile_seed(
        split,
        profile_key="clock_shift",
        target_col="sell_stop_broken_H6_off05_flag",
        seed=42,
    )

    assert result["profile"] == "clock_shift"
    assert result["target"] == "sell_stop_broken_H6_off05_flag"
    assert result["seed"] == 42
    assert result["transform_params"] == {}
    assert result["transform_params_fit_on"] == "train_core"
    assert result["val_stop"]["n"] == 8
    assert set(result["yearly_val"].keys()) == {"2021", "2022"}
    assert set(result["yearly_diagnostic_holdout"].keys()) == {"2023", "2024", "2025"}
    assert len(result["predictions"]["val_stop"]) == 8
    assert len(result["labels"]["diagnostic_holdout"]) == 12


def test_summarize_stage5_1b_target_adds_expected_delta_blocks(monkeypatch):
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    raw_runs = []
    target = "sell_stop_broken_H6_off05_flag"
    for profile in ["clock_shift", "structure_full", "updn_full", "drop_back", "drop_up_3", "add_back", "add_up_3"]:
        for seed, auc in [(42, 0.60), (77, 0.62), (123, 0.64)]:
            raw_runs.append({
                "profile": profile,
                "target": target,
                "seed": seed,
                "train_core": {"auc": auc},
                "val_stop": {"auc": auc, "lift_30": 0.8, "auc_ci": {"low": auc - 0.01, "high": auc + 0.01}},
                "diagnostic_holdout": {"auc": auc - 0.02, "lift_30": 0.82, "auc_ci": {"low": auc - 0.03, "high": auc}},
                "low_n_disclosure": {"auc": auc - 0.03, "lift_30": 0.84},
                "yearly_val": {"2021": {"auc": auc}, "2022": {"auc": auc}},
                "yearly_diagnostic_holdout": {"2023": {"auc": auc}, "2024": {"auc": auc}, "2025": {"auc": auc}},
                "split_manifest": {"target": target},
                "predictions": {
                    "val_stop": [0.1, 0.2, 0.8, 0.9],
                    "diagnostic_holdout": [0.1, 0.2, 0.8, 0.9],
                },
                "labels": {
                    "val_stop": [0, 0, 1, 1],
                    "diagnostic_holdout": [0, 0, 1, 1],
                },
            })
    monkeypatch.setattr(runner, "STAGE5_1B_PROFILE_KEYS", [
        "clock_shift", "structure_full", "updn_full", "drop_back", "drop_up_3", "add_back", "add_up_3"
    ])

    summary = runner.summarize_stage5_1b_target(raw_runs, target)

    assert "delta_vs_structure_full" in summary["drop_back"]
    assert "delta_vs_updn_full" in summary["drop_up_3"]
    assert "delta_vs_clock_shift" in summary["add_back"]
    assert "delta_vs_clock_shift" in summary["add_up_3"]
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_evaluate_stage5_1b_profile_seed_returns_metrics_and_predictions tests/test_stage5_transformer_breach.py::test_summarize_stage5_1b_target_adds_expected_delta_blocks -q
```

Expected: FAIL because evaluation and summary helpers do not exist.

- [ ] **Step 3: Add evaluator**

Add:

```python
def evaluate_stage5_1b_profile_seed(split: dict, profile_key: str, target_col: str,
                                    seed: int, transform_variant: str = "asinh") -> dict:
    """Train one Stage 5.1b XGBoost model for one profile/target/seed."""
    train_core = split["train_core"]
    val_stop = split["val_stop"]
    diagnostic_holdout = split["diagnostic_holdout"]
    low_n_disclosure = split["low_n_disclosure"]
    transform_params = fit_stage5_1b_transform_params(
        train_core, profile_key, transform_variant=transform_variant)

    X_train = build_stage5_1b_features(train_core, profile_key, transform_variant, transform_params)
    X_val = build_stage5_1b_features(val_stop, profile_key, transform_variant, transform_params)
    X_holdout = build_stage5_1b_features(diagnostic_holdout, profile_key, transform_variant, transform_params)
    X_low_n = build_stage5_1b_features(low_n_disclosure, profile_key, transform_variant, transform_params)

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
        "yearly_diagnostic_holdout": compute_yearly_metrics(diagnostic_holdout, holdout_probs, target_col=target_col),
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

- [ ] **Step 4: Add summary and delta helpers**

Add:

```python
def summarize_stage5_1b_target(raw_runs: list[dict], target_col: str) -> dict:
    """Summarize one Stage 5.1b target across profiles and add drop/add deltas."""
    target_runs = [r for r in raw_runs if r["target"] == target_col]
    summary = {}
    for profile in STAGE5_1B_PROFILE_KEYS:
        runs = [r for r in target_runs if r["profile"] == profile]
        summary[profile] = summarize_stage5_1_seed_runs(runs)

    for field in STAGE5_1B_FIELDS:
        drop_profile = f"drop_{field}"
        add_profile = f"add_{field}"
        if drop_profile in summary:
            baseline = "structure_full" if field in STAGE5_1B_STRUCTURE_FIELDS else "updn_full"
            delta_key = "delta_vs_structure_full" if baseline == "structure_full" else "delta_vs_updn_full"
            summary[drop_profile][delta_key] = {
                "val_stop": _stage5_1_delta_summary(target_runs, drop_profile, baseline, "val_stop"),
                "diagnostic_holdout": _stage5_1_delta_summary(target_runs, drop_profile, baseline, "diagnostic_holdout"),
            }
        if add_profile in summary:
            summary[add_profile]["delta_vs_clock_shift"] = {
                "val_stop": _stage5_1_delta_summary(target_runs, add_profile, "clock_shift", "val_stop"),
                "diagnostic_holdout": _stage5_1_delta_summary(target_runs, add_profile, "clock_shift", "diagnostic_holdout"),
            }

    for profile, baseline, key in [
        ("updn_full", "clock_shift", "delta_updn_group"),
        ("structure_full", "clock_shift", "delta_structure_group"),
        ("structure_plus_updn", "structure_full", "delta_combined"),
        ("back_impulse_combo", "clock_shift", "delta_back_impulse"),
        ("back_impulse_combo", "structure_full", "gap_back_impulse_full"),
    ]:
        if profile in summary:
            summary[profile][key] = {
                "val_stop": _stage5_1_delta_summary(target_runs, profile, baseline, "val_stop"),
                "diagnostic_holdout": _stage5_1_delta_summary(target_runs, profile, baseline, "diagnostic_holdout"),
            }
    return summary
```

- [ ] **Step 5: Write failing verdict and group tests**

Add:

```python
def test_stage5_1b_field_verdicts_require_both_targets_for_overall_useful():
    import copy
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    sell = "sell_stop_broken_H6_off05_flag"
    buy = "buy_stop_broken_H6_off05_flag"
    target_summary = {
        "drop_back": {
            "delta_vs_structure_full": {
                "val_stop": {
                    "delta_median": -0.02,
                    "delta_ci_low": -0.04,
                    "delta_ci_high": -0.01,
                    "negative_seed_count": 3,
                    "positive_seed_count": 0,
                },
            },
        },
        "add_back": {
            "delta_vs_clock_shift": {
                "val_stop": {"delta_median": 0.03},
                "diagnostic_holdout": {"delta_median": 0.01},
            },
        },
    }
    report = {"summary": {sell: copy.deepcopy(target_summary), buy: copy.deepcopy(target_summary)}}

    verdicts = runner.stage5_1b_field_verdicts(report)

    assert verdicts["back"]["targets"][sell]["verdict"] == "target_likely_useful"
    assert verdicts["back"]["overall_verdict"] == "overall_likely_useful"

    report["summary"][buy]["drop_back"]["delta_vs_structure_full"]["val_stop"]["delta_median"] = 0.0
    report["summary"][buy]["drop_back"]["delta_vs_structure_full"]["val_stop"]["negative_seed_count"] = 1
    verdicts = runner.stage5_1b_field_verdicts(report)
    assert verdicts["back"]["overall_verdict"] == "target_specific_signal"


def test_stage5_1b_group_analysis_reports_direction_horizon_and_group_deltas():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    target = "sell_stop_broken_H6_off05_flag"
    summary = {
        "updn_full": {"delta_updn_group": {"val_stop": {"delta_median": 0.02}}},
        "structure_full": {"delta_structure_group": {"val_stop": {"delta_median": 0.03}}},
        "structure_plus_updn": {"delta_combined": {"val_stop": {"delta_median": 0.01}}},
    }
    for field in runner.STAGE5_1B_UPDN_FIELDS:
        summary[f"add_{field}"] = {
            "delta_vs_clock_shift": {"val_stop": {"delta_median": 0.01}}
        }
        summary[f"drop_{field}"] = {
            "delta_vs_updn_full": {"val_stop": {"delta_median": -0.005}}
        }
    report = {"summary": {target: summary}}

    analysis = runner.stage5_1b_group_analysis(report)

    assert target in analysis
    assert "direction" in analysis[target]
    assert "horizon" in analysis[target]
    assert "group_deltas" in analysis[target]
    assert analysis[target]["group_deltas"]["delta_updn_group_val"] == pytest.approx(0.02)
```

- [ ] **Step 6: Run tests and verify they fail**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_stage5_1b_field_verdicts_require_both_targets_for_overall_useful tests/test_stage5_transformer_breach.py::test_stage5_1b_group_analysis_reports_direction_horizon_and_group_deltas -q
```

Expected: FAIL because verdict and group analysis helpers do not exist.

- [ ] **Step 7: Add verdict and group analysis helpers**

Add:

```python
def _stage5_1b_drop_delta_block(target_summary: dict, field: str) -> dict:
    drop = target_summary.get(f"drop_{field}", {})
    key = "delta_vs_structure_full" if field in STAGE5_1B_STRUCTURE_FIELDS else "delta_vs_updn_full"
    return drop.get(key, {}).get("val_stop", {})


def _stage5_1b_field_target_verdict(target_summary: dict, field: str) -> dict:
    drop_val = _stage5_1b_drop_delta_block(target_summary, field)
    add_val = (
        target_summary.get(f"add_{field}", {})
        .get("delta_vs_clock_shift", {})
        .get("val_stop", {})
        .get("delta_median")
    )
    drop_delta = drop_val.get("delta_median")
    drop_ci_low = drop_val.get("delta_ci_low")
    drop_ci_high = drop_val.get("delta_ci_high")
    negative_seed_count = int(drop_val.get("negative_seed_count") or 0)
    positive_seed_count = int(drop_val.get("positive_seed_count") or 0)

    useful = (
        drop_delta is not None
        and drop_delta < 0
        and ((drop_ci_high is not None and drop_ci_high < 0) or negative_seed_count == 3)
        and add_val is not None
        and add_val > 0
    )
    noise = (
        drop_delta is not None
        and drop_delta > 0
        and ((drop_ci_low is not None and drop_ci_low > 0) or positive_seed_count == 3)
        and add_val is not None
        and add_val <= 0
    )
    if useful:
        verdict = "target_likely_useful"
    elif noise:
        verdict = "target_likely_noise"
    else:
        verdict = "mixed_or_unclear"
    return {
        "verdict": verdict,
        "drop_val_delta_median": drop_delta,
        "drop_val_delta_ci_low": drop_ci_low,
        "drop_val_delta_ci_high": drop_ci_high,
        "drop_val_negative_seed_count": negative_seed_count,
        "drop_val_positive_seed_count": positive_seed_count,
        "add_val_delta_median": add_val,
    }


def stage5_1b_field_verdicts(report: dict) -> dict:
    verdicts = {}
    for field in STAGE5_1B_FIELDS:
        per_target = {}
        labels = []
        for target in STAGE5_1B_TARGETS:
            target_summary = report.get("summary", {}).get(target, {})
            target_result = _stage5_1b_field_target_verdict(target_summary, field)
            per_target[target] = target_result
            labels.append(target_result["verdict"])

        if labels.count("target_likely_useful") == 2:
            overall = "overall_likely_useful"
        elif labels.count("target_likely_noise") == 2:
            overall = "overall_likely_noise"
        elif (
            labels.count("target_likely_useful") == 1
            and labels.count("mixed_or_unclear") == 1
        ) or (
            labels.count("target_likely_noise") == 1
            and labels.count("mixed_or_unclear") == 1
        ):
            overall = "target_specific_signal"
        else:
            overall = "mixed_or_unclear"

        verdicts[field] = {
            "overall_verdict": overall,
            "targets": per_target,
            "diagnostic_only": True,
        }
    return verdicts


def _stage5_1b_median(values: list[float | None]) -> float | None:
    clean = [float(v) for v in values if v is not None and np.isfinite(v)]
    return float(np.median(clean)) if clean else None


def stage5_1b_group_analysis(report: dict) -> dict:
    out = {}
    horizons = {
        "3": ["up_3", "dn_3"],
        "6": ["up_6", "dn_6"],
        "12": ["up_12", "dn_12"],
        "24": ["up_24", "dn_24"],
        "48": ["up_48", "dn_48"],
    }
    for target, summary in report.get("summary", {}).items():
        direction = {}
        for side, fields in {"up": ["up_3", "up_6", "up_12", "up_24", "up_48"], "dn": ["dn_3", "dn_6", "dn_12", "dn_24", "dn_48"]}.items():
            direction[side] = {
                "add_delta_val_median": _stage5_1b_median([
                    summary.get(f"add_{field}", {}).get("delta_vs_clock_shift", {}).get("val_stop", {}).get("delta_median")
                    for field in fields
                ]),
                "drop_delta_val_median": _stage5_1b_median([
                    summary.get(f"drop_{field}", {}).get("delta_vs_updn_full", {}).get("val_stop", {}).get("delta_median")
                    for field in fields
                ]),
            }
        horizon = {}
        for h, fields in horizons.items():
            horizon[h] = {
                "add_delta_val_median": _stage5_1b_median([
                    summary.get(f"add_{field}", {}).get("delta_vs_clock_shift", {}).get("val_stop", {}).get("delta_median")
                    for field in fields
                ]),
                "drop_delta_val_median": _stage5_1b_median([
                    summary.get(f"drop_{field}", {}).get("delta_vs_updn_full", {}).get("val_stop", {}).get("delta_median")
                    for field in fields
                ]),
            }
        out[target] = {
            "direction": direction,
            "horizon": horizon,
            "group_deltas": {
                "delta_updn_group_val": summary.get("updn_full", {}).get("delta_updn_group", {}).get("val_stop", {}).get("delta_median"),
                "delta_structure_group_val": summary.get("structure_full", {}).get("delta_structure_group", {}).get("val_stop", {}).get("delta_median"),
                "delta_combined_val": summary.get("structure_plus_updn", {}).get("delta_combined", {}).get("val_stop", {}).get("delta_median"),
            },
            "maturity_aware_note": "Use preflight maturity shares to interpret horizon 12/24/48 effects; no subgroup retraining is performed in Stage 5.1b.",
        }
    return out
```

- [ ] **Step 8: Run focused tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_evaluate_stage5_1b_profile_seed_returns_metrics_and_predictions tests/test_stage5_transformer_breach.py::test_summarize_stage5_1b_target_adds_expected_delta_blocks tests/test_stage5_transformer_breach.py::test_stage5_1b_field_verdicts_require_both_targets_for_overall_useful tests/test_stage5_transformer_breach.py::test_stage5_1b_group_analysis_reports_direction_horizon_and_group_deltas -q
```

Expected: PASS.

- [ ] **Step 9: Commit**

```bash
git add ML/baseline/benchmark_stage5_transformer_breach.py tests/test_stage5_transformer_breach.py
git commit -m "feat: summarize stage5.1b ablation diagnostics"
```

---

### Task 5: Stage 5.1b Runner And CLI

**Files:**
- Modify: `ML/baseline/benchmark_stage5_transformer_breach.py`
- Test: `tests/test_stage5_transformer_breach.py`

**Interfaces:**
- Consumes: `run_stage5_1b_preflight(split: dict, target_col: str) -> dict`
- Consumes: `stage5_1b_preflight_passed(preflight: dict) -> bool`
- Consumes: `evaluate_stage5_1b_profile_seed(...) -> dict`
- Consumes: `summarize_stage5_1b_target(...) -> dict`
- Consumes: `stage5_1b_field_verdicts(report: dict) -> dict`
- Consumes: `stage5_1b_group_analysis(report: dict) -> dict`
- Produces: `run_stage5_1b_updn_field_ablation(target_splits: dict, output_path=STAGE5_1B_JSON_REPORT_PATH) -> dict`
- Produces: CLI flag `--stage5-1b-updn-field-ablation`

- [ ] **Step 1: Write failing runner and CLI tests**

Add:

```python
def test_stage5_1b_runner_writes_json_and_stops_after_preflight_failure(monkeypatch, tmp_path):
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    df = _make_stage5_0f_year_df()
    monkeypatch.setattr(runner, "STAGE5_1B_PROFILE_KEYS", ["clock_shift"])
    monkeypatch.setattr(runner, "STAGE5_1B_SEEDS", [42])
    monkeypatch.setattr(runner, "run_stage5_1b_preflight", lambda split, target: {
        "target": target,
        "source_check": {"uses_fractal_columns_only": True, "forbidden_top_level_updn_columns_used": False},
        "contract": {"short_fractal_count": 0},
        "monotonicity": {"violations_total": 1},
        "pass": False,
    })

    called = {"train": False}
    def fail_if_called(*args, **kwargs):
        called["train"] = True
        raise AssertionError("training must not run when preflight fails")
    monkeypatch.setattr(runner, "evaluate_stage5_1b_profile_seed", fail_if_called)

    report = runner.run_stage5_1b_updn_field_ablation(
        target_splits={
            "sell_stop_broken_H6_off05_flag": (df, df, df),
            "buy_stop_broken_H6_off05_flag": (df, df, df),
        },
        output_path=tmp_path / "stage5_1b.json",
    )

    assert report["stage"] == "5.1b_updn_field_ablation"
    assert report["status"] == "PREFLIGHT_FAILED"
    assert called["train"] is False
    assert (tmp_path / "stage5_1b.json").exists()


def test_stage5_1b_runner_writes_diagnostic_json(monkeypatch, tmp_path):
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    df = _make_stage5_0f_year_df()
    monkeypatch.setattr(runner, "STAGE5_1B_PROFILE_KEYS", ["clock_shift", "structure_full", "updn_full"])
    monkeypatch.setattr(runner, "STAGE5_1B_SEEDS", [42])
    monkeypatch.setattr(runner, "STAGE5_1B_BOOTSTRAP_N", 20)

    class DummyDMatrix:
        def __init__(self, X, label=None):
            self.X = X
            self.label = label

    class DummyModel:
        def predict(self, dmat):
            return np.linspace(0.05, 0.95, len(dmat.X))

    monkeypatch.setattr(runner.xgb, "DMatrix", DummyDMatrix)
    monkeypatch.setattr(runner, "train_xgb_baseline", lambda *a, **k: (DummyModel(), 0.61))

    report = runner.run_stage5_1b_updn_field_ablation(
        target_splits={
            "sell_stop_broken_H6_off05_flag": (df, df, df),
            "buy_stop_broken_H6_off05_flag": (df, df, df),
        },
        output_path=tmp_path / "stage5_1b.json",
    )

    assert report["stage"] == "5.1b_updn_field_ablation"
    assert report["status"] == "DIAGNOSTIC_ONLY"
    assert report["baseline"] == "clock + shift (log1p)"
    assert report["profiles"] == ["clock_shift", "structure_full", "updn_full"]
    assert report["raw_runs"]
    assert "predictions" not in report["raw_runs"][0]
    assert "labels" not in report["raw_runs"][0]
    assert "preflight" in report
    assert "group_analysis" in report
    assert "field_verdicts" in report
    assert report["progress"]["done_runs"] == 6


def test_stage5_1b_cli_argument_exists_in_build_arg_parser():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    parser = runner.build_arg_parser()
    args = parser.parse_args(["--stage5-1b-updn-field-ablation"])
    assert args.stage5_1b_updn_field_ablation is True
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_stage5_1b_runner_writes_json_and_stops_after_preflight_failure tests/test_stage5_transformer_breach.py::test_stage5_1b_runner_writes_diagnostic_json tests/test_stage5_transformer_breach.py::test_stage5_1b_cli_argument_exists_in_build_arg_parser -q
```

Expected: FAIL because runner and CLI flag do not exist.

- [ ] **Step 3: Add runner**

Add after `run_stage5_1_structural_field_ablation`:

```python
def run_stage5_1b_updn_field_ablation(target_splits: dict,
                                      output_path=STAGE5_1B_JSON_REPORT_PATH) -> dict:
    """Run Stage 5.1b Up/Dn field ablation diagnostics."""
    started_at = time.time()
    total_runs = len(STAGE5_1B_TARGETS) * len(STAGE5_1B_PROFILE_KEYS) * len(STAGE5_1B_SEEDS)
    report = {
        "stage": "5.1b_updn_field_ablation",
        "status": "RUNNING",
        "level": "exploratory",
        "verdict_scope": "DIAGNOSTIC_ONLY",
        "baseline": "clock + shift (log1p)",
        "targets": list(STAGE5_1B_TARGETS),
        "fields": list(STAGE5_1B_FIELDS),
        "seeds": list(STAGE5_1B_SEEDS),
        "profiles": list(STAGE5_1B_PROFILE_KEYS),
        "raw_runs": [],
        "summary": {},
        "field_verdicts": {},
        "group_analysis": {},
        "preflight": {},
        "multiple_testing_context": {
            "diagnostic_only": True,
            "correction_applied": None,
            "comparison_count": 76,
            "note": "19 fields × 2 ablation modes × 2 targets; likely_* labels are preliminary diagnostic categories.",
        },
        "holdout_disclosure": {
            "val_stop": "2021-2022 pooled primary diagnostic validation plus yearly disclosure.",
            "diagnostic_holdout": "2023-2025 already used in Stage 5.0f/5.1; disclosure only.",
            "low_n_disclosure": "2026 optional low-N disclosure, not used for verdict.",
        },
        "transform_config": {
            "transform_variant": "asinh",
            "transform_params_fit_on": "train_core",
            "transform_params": {},
            "shift_transform": "log1p(max(raw_shift, 0))",
            "updn_units": "raw price units",
        },
        "sanity_checks": {
            "time_only_stage5_1_reference": "clock_shift is not directly comparable with Stage 5.1 time_only because shift is added.",
            "expected_model_count": int(total_runs),
            "excluded_top_level_updn_columns": [f"{side}_{h}" for h in [3, 6, 12, 24, 48] for side in ["up", "dn"]],
            "stage5_1b_structure_full_actual": {},
            "clock_shift_actual": {},
            "updn_full_vs_structure_full": {},
            "back_impulse_combo_vs_structure_full": {},
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

    splits_by_target = {}
    for target_col in STAGE5_1B_TARGETS:
        train_df, val_df, hold_df = target_splits[target_col]
        combined = pd.concat([train_df, val_df, hold_df], ignore_index=True)
        split = build_stage5_1_split(combined, target_col)
        splits_by_target[target_col] = split
        preflight = run_stage5_1b_preflight(split, target_col)
        report["preflight"][target_col] = preflight
        _write_json_atomic(output_path, report)
        if not stage5_1b_preflight_passed(preflight):
            report["status"] = "PREFLIGHT_FAILED"
            report["progress"]["finished_at_unix"] = time.time()
            report["progress"]["elapsed_sec"] = round(report["progress"]["finished_at_unix"] - started_at, 1)
            _write_json_atomic(output_path, report)
            return report

    for target_col in STAGE5_1B_TARGETS:
        split = splits_by_target[target_col]
        report["summary"].setdefault(target_col, {})
        target_runs = []
        for profile_key in STAGE5_1B_PROFILE_KEYS:
            for seed in STAGE5_1B_SEEDS:
                run = evaluate_stage5_1b_profile_seed(
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

        report["summary"][target_col] = summarize_stage5_1b_target(target_runs, target_col)
        target_summary = report["summary"][target_col]
        report["sanity_checks"]["stage5_1b_structure_full_actual"][target_col] = {
            "val_auc_median": target_summary.get("structure_full", {}).get("val_stop", {}).get("auc_median"),
            "diagnostic_holdout_auc_median": target_summary.get("structure_full", {}).get("diagnostic_holdout", {}).get("auc_median"),
        }
        report["sanity_checks"]["clock_shift_actual"][target_col] = {
            "val_auc_median": target_summary.get("clock_shift", {}).get("val_stop", {}).get("auc_median"),
            "diagnostic_holdout_auc_median": target_summary.get("clock_shift", {}).get("diagnostic_holdout", {}).get("auc_median"),
        }
        report["sanity_checks"]["updn_full_vs_structure_full"][target_col] = {
            "updn_val_auc_median": target_summary.get("updn_full", {}).get("val_stop", {}).get("auc_median"),
            "structure_val_auc_median": target_summary.get("structure_full", {}).get("val_stop", {}).get("auc_median"),
        }
        report["sanity_checks"]["back_impulse_combo_vs_structure_full"][target_col] = {
            "back_impulse_val_auc_median": target_summary.get("back_impulse_combo", {}).get("val_stop", {}).get("auc_median"),
            "structure_val_auc_median": target_summary.get("structure_full", {}).get("val_stop", {}).get("auc_median"),
        }
        _write_json_atomic(output_path, report)

    report["field_verdicts"] = stage5_1b_field_verdicts(report)
    report["group_analysis"] = stage5_1b_group_analysis(report)
    report["status"] = "DIAGNOSTIC_ONLY"
    report["progress"]["finished_at_unix"] = time.time()
    report["progress"]["elapsed_sec"] = round(report["progress"]["finished_at_unix"] - started_at, 1)
    _write_json_atomic(output_path, report)
    return report
```

- [ ] **Step 4: Add CLI flag**

In `build_arg_parser()` add after Stage 5.1 flag:

```python
    parser.add_argument("--stage5-1b-updn-field-ablation", action="store_true",
                        help="Run Stage 5.1b Up/Dn field ablation with clock+shift baseline")
```

In `main()` add after Stage 5.1 branch:

```python
    if args.stage5_1b_updn_field_ablation:
        print("\n" + "=" * 60)
        print("Загрузка buy splits для Stage 5.1b...")
        print("=" * 60)
        buy_train, buy_val, buy_hold = load_splits(target_col="buy_stop_broken_H6_off05_flag")
        report = run_stage5_1b_updn_field_ablation(
            target_splits={
                "sell_stop_broken_H6_off05_flag": (train_df, val_stop_df, holdout_df),
                "buy_stop_broken_H6_off05_flag": (buy_train, buy_val, buy_hold),
            },
            output_path=STAGE5_1B_JSON_REPORT_PATH,
        )
        print("\n" + "=" * 60)
        print("Stage 5.1b: абляция Up/Dn полей завершена")
        print(json.dumps({
            "json": str(STAGE5_1B_JSON_REPORT_PATH),
            "status": report.get("status"),
            "field_verdicts": report.get("field_verdicts", {}),
        }, indent=2))
        print("=" * 60)
        return
```

- [ ] **Step 5: Run focused tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_stage5_1b_runner_writes_json_and_stops_after_preflight_failure tests/test_stage5_transformer_breach.py::test_stage5_1b_runner_writes_diagnostic_json tests/test_stage5_transformer_breach.py::test_stage5_1b_cli_argument_exists_in_build_arg_parser -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add ML/baseline/benchmark_stage5_transformer_breach.py tests/test_stage5_transformer_breach.py
git commit -m "feat: add stage5.1b runner"
```

---

### Task 6: Full Regression Tests And Dry CLI Check

**Files:**
- Modify: none expected.

**Interfaces:**
- Consumes all previous tasks.

- [ ] **Step 1: Run full project tests**

Run:

```bash
./.venv/bin/python -m pytest tests/ -q
```

Expected: PASS.

- [ ] **Step 2: Run CLI help check**

Run:

```bash
./.venv/bin/python -m ML.baseline.benchmark_stage5_transformer_breach --help
```

Expected: output contains `--stage5-1b-updn-field-ablation`.

- [ ] **Step 3: Run preflight-only smoke through monkeypatched tests, not full training**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py -q
```

Expected: PASS.

- [ ] **Step 4: Commit if any fixes were needed**

If Step 1-3 required fixes:

```bash
git add ML/baseline/benchmark_stage5_transformer_breach.py tests/test_stage5_transformer_breach.py
git commit -m "test: stabilize stage5.1b diagnostics"
```

If no fixes were needed, do not create an empty commit.

---

### Task 7: Run Stage 5.1b Experiment

**Files:**
- Create/Modify: `ML/reports/stage5_1b_updn_field_ablation.json`

**Interfaces:**
- Consumes: CLI flag `--stage5-1b-updn-field-ablation`
- Produces: `ML/reports/stage5_1b_updn_field_ablation.json`

- [ ] **Step 1: Start full Stage 5.1b run**

Run:

```bash
PYTHONUNBUFFERED=1 ./.venv/bin/python -m ML.baseline.benchmark_stage5_transformer_breach --stage5-1b-updn-field-ablation
```

Expected:
- If preflight fails: JSON status is `PREFLIGHT_FAILED`; no XGBoost training runs occur.
- If preflight passes: 258 model runs complete and JSON status is `DIAGNOSTIC_ONLY`.

- [ ] **Step 2: Inspect final JSON status**

Run:

```bash
./.venv/bin/python - <<'PY'
import json
from pathlib import Path
p = Path("ML/reports/stage5_1b_updn_field_ablation.json")
r = json.loads(p.read_text())
print({
    "status": r.get("status"),
    "stage": r.get("stage"),
    "raw_runs": len(r.get("raw_runs", [])),
    "profiles": len(r.get("profiles", [])),
    "fields": len(r.get("fields", [])),
    "done_runs": r.get("progress", {}).get("done_runs"),
})
PY
```

Expected after successful full run:

```text
{'status': 'DIAGNOSTIC_ONLY', 'stage': '5.1b_updn_field_ablation', 'raw_runs': 258, 'profiles': 43, 'fields': 19, 'done_runs': 258}
```

If status is `PREFLIGHT_FAILED`, stop and write a short failure note instead of forcing training.

- [ ] **Step 3: Commit JSON result**

```bash
git add ML/reports/stage5_1b_updn_field_ablation.json
git commit -m "data: add stage5.1b updn ablation results"
```

---

### Task 8: Write Stage 5.1b Report And Sync Project Docs

**Files:**
- Create: `docs/reports/YYYY-MM-DD-stage5_1b-updn-field-ablation.md`
- Modify: `CHANGELOG.md`
- Modify: `CONTEXT_HANDOFF.md`
- Modify: `wiki/research/fractal-stop-research.md`
- Modify: `wiki/index.md`
- Modify: `wiki/log.md`
- Modify: `wiki/REPO_integrity.md`

**Interfaces:**
- Consumes: `ML/reports/stage5_1b_updn_field_ablation.json`
- Consumes: stage-reporting skill.
- Consumes: wiki skill.

- [ ] **Step 1: Read reporting skills**

Read:

```bash
sed -n '1,260p' .claude/skills/my/stage-reporting/SKILL.md
sed -n '1,220p' .claude/skills/my/wiki/SKILL.md
```

Expected: instructions loaded before docs/wiki edits.

- [ ] **Step 2: Draft canonical report from JSON**

Create `docs/reports/YYYY-MM-DD-stage5_1b-updn-field-ablation.md` with these required sections:

```markdown
# Stage 5.1b — Up/Dn Field Ablation With Clock+Shift Baseline

> **Status**: DIAGNOSTIC_ONLY
> **Verdict scope**: no winner, no trading rule
> **JSON**: `ML/reports/stage5_1b_updn_field_ablation.json`

## Executive Summary

State whether preflight passed, whether Up/Dn adds signal above `clock_shift`, whether structural fields changed after adding `shift`, and whether `back_impulse_combo` is close to `structure_full`.

## Preflight

Report source check, fractal contract, monotonicity, maturity shares, shift distribution, Up/Dn correlation with shift, and Up/Dn/ATR disclosure.

## Experiment Design

Explain 43 profiles, 19 fields, 2 targets, 3 seeds, split, and diagnostic-only status.

## Main Metrics

Summarize `clock_shift`, `structure_full`, `updn_full`, `structure_plus_updn`, and `back_impulse_combo` for sell and buy.

## Field Verdicts

Summarize `overall_likely_useful`, `overall_likely_noise`, `target_specific_signal`, and `mixed_or_unclear`.

## Group Analysis

Summarize up vs dn direction, horizon pattern, group deltas, and maturity caveat.

## Interpretation Limits

State that 2023-2025 are burned diagnostic disclosure, multiple testing has no correction, and useful fields do not imply trading profit.

## Decision For Next Stage

Give management conclusion for Stage 5.2.
```

- [ ] **Step 3: Update changelog and handoff**

Update:
- `CHANGELOG.md`: add Stage 5.1b result near top.
- `CONTEXT_HANDOFF.md`: update current state and next recommended action.

- [ ] **Step 4: Update wiki**

Run:

```bash
./.venv/bin/python wiki/wiki.py generate
./.venv/bin/python wiki/wiki.py status
```

Expected: `Wiki is up to date. No gaps found.`

- [ ] **Step 5: Run docs status verification**

Run:

```bash
git status --short
```

Expected: only intended report, changelog, handoff, wiki, and JSON files are modified/added.

- [ ] **Step 6: Commit reporting artifacts**

```bash
git add docs/reports/YYYY-MM-DD-stage5_1b-updn-field-ablation.md CHANGELOG.md CONTEXT_HANDOFF.md wiki/research/fractal-stop-research.md wiki/index.md wiki/log.md wiki/REPO_integrity.md
git commit -m "docs: report stage5.1b updn ablation"
```

---

## Self-Review Checklist

- [ ] The plan implements every spec requirement: preflight, Up/Dn source safety, `shift` baseline, 43 profiles, 258 runs, deltas, verdicts, group analysis, JSON, report, wiki sync.
- [ ] Stage 5.1 legacy constants and builders are not changed.
- [ ] `clock_shift` is token-level `shift` plus row-level clock, not row-only.
- [ ] Drop-one structural fields compare to `structure_full`.
- [ ] Drop-one Up/Dn fields compare to `updn_full`.
- [ ] Add-one fields compare to `clock_shift`.
- [ ] Full drop-one from `structure_plus_updn` is not implemented.
- [ ] `field_verdicts` require both targets to agree for `overall_likely_useful` or `overall_likely_noise`.
- [ ] The full run stops if preflight fails.
- [ ] No code reads top-level `up_3..dn_48` as features.
- [ ] Full test command `./.venv/bin/python -m pytest tests/ -q` is run after Python changes.
