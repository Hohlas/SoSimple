# Stage 5.2 Time To Breach Regression Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Реализовать Stage 5.2: censored proxy target `bars_to_breach`, oracle-preflight через first-touch simulator и XGBoost-регрессию времени до пробоя.

**Architecture:** Расширяем существующую разметку `label_fractal_stop_breach()` без изменения старых breach-флагов. В `benchmark_stage5_transformer_breach.py` добавляем отдельный Stage 5.2 контур: fixed split, профили из Stage 5.1b, constant baseline, oracle-preflight, regression metrics, gates, JSON report и CLI.

**Tech Stack:** Python 3.10, pandas, numpy, scipy, scikit-learn metrics, XGBoost, pytest, JSON reports.

## Global Constraints

- Работать в текущей feature-ветке; worktree запрещён `AGENTS.md`.
- Использовать Python окружение проекта: `./.venv/bin/python`.
- После изменений в Python-коде запускать `./.venv/bin/python -m pytest tests/ -q`.
- Для bugfix/ML-infrastructure изменений применять TDD: сначала failing test, затем код.
- Stage 5.2 статус: `CANDIDATE_HYPOTHESIS` только при прохождении всех gate; настоящий `CANDIDATE` только после независимого frozen test на 2026+ или другом инструменте.
- Основной target — censored proxy: `bars_to_breach = H + 1` означает "не пробит за H баров", а не "пробит на H+1".
- Основной H/off: `H=6`, `off=0.5`, цели `sell_bars_to_breach_H6_off05` и `buy_bars_to_breach_H6_off05`.
- Не использовать `2023-2025` для выбора параметров или winner-а; это diagnostic disclosure only.
- Up/Dn не включать в стартовые Stage 5.2 профили.
- Обязательные профили: `time_only`, `clock_shift`, `clock_shift_back`, `clock_shift_impulse`, `clock_shift_back_impulse`, `structure_full`, `structure_full_without_back`.
- Бюджет полного model-run: `7 профилей × 2 цели × 3 seed = 42` XGBoost-регрессии плюс constant baseline.
- Oracle-preflight обязан использовать один и тот же first-touch simulator для oracle-time и oracle-binary.

---

## File Structure

- Modify: `processing/label_signals.py`
  - Добавить `BR_TIME_TO_BREACH_COLUMNS`, helper вычисления first breach bar и запись `*_bars_to_breach_*` колонок внутри `label_fractal_stop_breach()`.
- Modify: `tests/processing/test_fractal_stop_breach_labels.py`
  - Добавить тесты Stage 5.2 target-контракта и паритета с существующими `*_flag`.
- Modify: `ML/baseline/benchmark_stage5_transformer_breach.py`
  - Добавить Stage 5.2 constants, profiles, feature builder reuse, first-touch oracle simulator, regression metrics, gates, runner and CLI.
- Modify: `tests/test_stage5_transformer_breach.py`
  - Добавить unit/smoke тесты Stage 5.2 рядом с Stage 5.1b тестами.
- Create after full run: `ML/reports/stage5_2_time_to_breach_regression.json`
  - Structured artifact полного Stage 5.2 прогона.
- Create after full run: `docs/reports/YYYY-MM-DD-stage5_2-time-to-breach-regression.md`
- Канонический отчёт после JSON, не в этом implementation-plan.

---

### Task 1B: Regenerate Labeled Data After Labeling

**Files:**
- Read: `processing/label_main.py`
- Read: `processing/normalize.py`
- Output: `DATA/Nero_XAUUSD_train_labeled.csv`
- Output: `DATA/Nero_XAUUSD_validation_labeled.csv`
- Output: `DATA/Nero_XAUUSD_test_labeled.csv`

**Interfaces:**
- Consumes: Task 1 extension of `label_fractal_stop_breach()`.
- Produces: labeled CSV files containing `sell_bars_to_breach_H6_off05` and `buy_bars_to_breach_H6_off05`.

Run this checkpoint after Task 1 and before Task 2. `load_splits()` reads ready `DATA/*_labeled.csv`; it does not recompute labels on the fly.

- [ ] **Step 1: Verify labeled CSV currently lacks Stage 5.2 targets**

Run:

```bash
./.venv/bin/python - <<'PY'
import pandas as pd
df = pd.read_csv("DATA/Nero_XAUUSD_train_labeled.csv", sep=";", nrows=1)
for col in ["sell_bars_to_breach_H6_off05", "buy_bars_to_breach_H6_off05"]:
    print(col, col in df.columns)
PY
```

Expected before Task 1 regeneration:

```text
sell_bars_to_breach_H6_off05 False
buy_bars_to_breach_H6_off05 False
```

- [ ] **Step 2: After Task 1, regenerate labeled data using the existing processing entrypoint**

Inspect the actual CLI before running:

```bash
./.venv/bin/python processing/label_main.py --help
```

Run the same project labeling/split command used for current `DATA/Nero_XAUUSD_*_labeled.csv`, with `--fractal-stop-breach` enabled. Without this flag, `label_fractal_stop_breach()` is not called and Stage 5.2 target columns will not be written.

```bash
./.venv/bin/python processing/label_main.py --input MT/MQL4/Files/Nero.csv --ohlc DATA/XAUUSD_H1_OHLC.csv --fractal-stop-breach
```

Expected: `DATA/Nero_XAUUSD_train_labeled.csv`, `DATA/Nero_XAUUSD_validation_labeled.csv`, and `DATA/Nero_XAUUSD_test_labeled.csv` are rewritten.

- [ ] **Step 3: Verify regenerated CSV contains Stage 5.2 targets**

Run:

```bash
./.venv/bin/python - <<'PY'
import pandas as pd
for path in [
    "DATA/Nero_XAUUSD_train_labeled.csv",
    "DATA/Nero_XAUUSD_validation_labeled.csv",
    "DATA/Nero_XAUUSD_test_labeled.csv",
]:
    df = pd.read_csv(path, sep=";", nrows=1)
    missing = [
        col for col in ["sell_bars_to_breach_H6_off05", "buy_bars_to_breach_H6_off05"]
        if col not in df.columns
    ]
    print(path, "OK" if not missing else f"MISSING {missing}")
PY
```

Expected:

```text
DATA/Nero_XAUUSD_train_labeled.csv OK
DATA/Nero_XAUUSD_validation_labeled.csv OK
DATA/Nero_XAUUSD_test_labeled.csv OK
```

Do not continue to Stage 5.2 runner until this passes.

---

### Task 1: Time-To-Breach Label Contract

**Files:**
- Modify: `processing/label_signals.py`
- Test: `tests/processing/test_fractal_stop_breach_labels.py`

**Interfaces:**
- Produces: `BR_TIME_TO_BREACH_COLUMNS: list[str]`
- Produces: `BR_TIME_TO_BREACH_PRIMARY_COLUMNS: list[str]`
- Produces: `first_fractal_stop_breach_bar(ohlc, times, idx0: int, horizon: int, fractal_dir: float, stop_price: float) -> int | None`
- Extends: `label_fractal_stop_breach(df, ohlc_path, debug=False)` to write both old `*_flag` and new `*_bars_to_breach_*` columns.

- [ ] **Step 1: Write failing tests for columns, first-bar timing, no-breach sentinel, and binary parity**

Append to `tests/processing/test_fractal_stop_breach_labels.py`:

```python
def test_time_to_breach_columns_exist_for_all_horizon_offsets():
    assert "buy_bars_to_breach_H6_off05" in ls.BR_TIME_TO_BREACH_COLUMNS
    assert "sell_bars_to_breach_H6_off05" in ls.BR_TIME_TO_BREACH_COLUMNS
    assert "buy_bars_to_breach_H12_off02" in ls.BR_TIME_TO_BREACH_COLUMNS
    assert "sell_bars_to_breach_H12_off05" in ls.BR_TIME_TO_BREACH_COLUMNS
    assert set(ls.BR_TIME_TO_BREACH_PRIMARY_COLUMNS) == {
        "buy_bars_to_breach_H6_off02",
        "sell_bars_to_breach_H6_off02",
        "buy_bars_to_breach_H6_off05",
        "sell_bars_to_breach_H6_off05",
        "buy_bars_to_breach_H12_off02",
        "sell_bars_to_breach_H12_off02",
        "buy_bars_to_breach_H12_off05",
        "sell_bars_to_breach_H12_off05",
    }


def test_buy_bars_to_breach_records_first_touch_and_matches_flag():
    with tempfile.TemporaryDirectory() as tmp:
        ohlc_path = os.path.join(tmp, "ohlc.csv")
        bars = [("2020.01.01 00:00", 1502.0, 1503.0, 1501.0, 1502.0)]
        for k in range(1, 7):
            bars.append((f"2020.01.01 {k:02d}:00", 1501.0, 1502.0, 1500.0, 1501.0))
        bars[3] = ("2020.01.01 03:00", 1501.0, 1502.0, 1495.0, 1498.0)
        bars[5] = ("2020.01.01 05:00", 1501.0, 1502.0, 1490.0, 1492.0)
        _make_ohlc_csv(ohlc_path, bars)
        df = _make_nero_df(
            times=["2020.01.01 00:00"],
            atr_vals=[20.0],
            fractal0_vals=[_fractal_str(1500.0, -1)],
        )

        result = LABEL_FN(df, ohlc_path)

        assert result.at[0, "buy_stop_broken_H6_off02_flag"] == 1.0
        assert result.at[0, "buy_bars_to_breach_H6_off02"] == 3
        assert pd.isna(result.at[0, "sell_bars_to_breach_H6_off02"])


def test_sell_bars_to_breach_records_h_plus_one_when_not_broken():
    with tempfile.TemporaryDirectory() as tmp:
        ohlc_path = os.path.join(tmp, "ohlc.csv")
        bars = [("2020.01.01 00:00", 1498.0, 1499.0, 1497.0, 1498.0)]
        for k in range(1, 7):
            bars.append((f"2020.01.01 {k:02d}:00", 1499.0, 1500.0, 1498.0, 1499.0))
        _make_ohlc_csv(ohlc_path, bars)
        df = _make_nero_df(
            times=["2020.01.01 00:00"],
            atr_vals=[20.0],
            fractal0_vals=[_fractal_str(1500.0, 1)],
        )

        result = LABEL_FN(df, ohlc_path)

        assert result.at[0, "sell_stop_broken_H6_off02_flag"] == 0.0
        assert result.at[0, "sell_bars_to_breach_H6_off02"] == 7


def test_time_to_breach_is_nan_when_future_bars_are_insufficient():
    with tempfile.TemporaryDirectory() as tmp:
        ohlc_path = os.path.join(tmp, "ohlc.csv")
        bars = [("2020.01.01 00:00", 1498.0, 1499.0, 1497.0, 1498.0)]
        for k in range(1, 5):
            bars.append((f"2020.01.01 {k:02d}:00", 1499.0, 1500.0, 1498.0, 1499.0))
        _make_ohlc_csv(ohlc_path, bars)
        df = _make_nero_df(
            times=["2020.01.01 00:00"],
            atr_vals=[20.0],
            fractal0_vals=[_fractal_str(1500.0, 1)],
        )

        result = LABEL_FN(df, ohlc_path)

        assert pd.isna(result.at[0, "sell_stop_broken_H6_off02_flag"])
        assert pd.isna(result.at[0, "sell_bars_to_breach_H6_off02"])
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/processing/test_fractal_stop_breach_labels.py::test_time_to_breach_columns_exist_for_all_horizon_offsets tests/processing/test_fractal_stop_breach_labels.py::test_buy_bars_to_breach_records_first_touch_and_matches_flag tests/processing/test_fractal_stop_breach_labels.py::test_sell_bars_to_breach_records_h_plus_one_when_not_broken tests/processing/test_fractal_stop_breach_labels.py::test_time_to_breach_is_nan_when_future_bars_are_insufficient -q
```

Expected: FAIL because `BR_TIME_TO_BREACH_COLUMNS` and new labels do not exist.

- [ ] **Step 3: Add constants and first-touch helper**

In `processing/label_signals.py`, after `BR_BREACH_COLUMNS` construction:

```python
BR_TIME_TO_BREACH_COLUMNS = []
BR_TIME_TO_BREACH_PRIMARY_COLUMNS = []
for h in BR_BREACH_HORIZONS:
    for off in BR_BREACH_OFFSETS:
        off_str = f"{int(off * 10):02d}"
        buy_col = f"buy_bars_to_breach_H{h}_off{off_str}"
        sell_col = f"sell_bars_to_breach_H{h}_off{off_str}"
        BR_TIME_TO_BREACH_COLUMNS.append(buy_col)
        BR_TIME_TO_BREACH_COLUMNS.append(sell_col)
        if off in BR_BREACH_OFFSETS_PRIMARY:
            BR_TIME_TO_BREACH_PRIMARY_COLUMNS.append(buy_col)
            BR_TIME_TO_BREACH_PRIMARY_COLUMNS.append(sell_col)
```

Add before `label_fractal_stop_breach()`:

```python
def first_fractal_stop_breach_bar(ohlc, times, idx0: int, horizon: int,
                                  fractal_dir: float, stop_price: float):
    """Return first 1-based future bar touching stop, or None if not touched."""
    for k in range(idx0 + 1, idx0 + 1 + horizon):
        if fractal_dir == -1:  # BUY: stop below valley
            if ohlc[times[k]][2] <= stop_price:  # low
                return k - idx0
        elif fractal_dir == 1:  # SELL: stop above peak
            if ohlc[times[k]][1] >= stop_price:  # high
                return k - idx0
    return None
```

- [ ] **Step 4: Extend `label_fractal_stop_breach()`**

In `label_fractal_stop_breach()`, initialize new columns beside old columns:

```python
for col in BR_BREACH_COLUMNS:
    df[col] = np.nan
for col in BR_TIME_TO_BREACH_COLUMNS:
    df[col] = np.nan
```

Replace the duplicated `any(...)` blocks inside BUY/SELL branches with:

```python
first_touch = first_fractal_stop_breach_bar(
    ohlc=ohlc,
    times=times,
    idx0=idx0,
    horizon=h,
    fractal_dir=fractal_dir,
    stop_price=stop_price,
)
breach = first_touch is not None
df.at[i, col] = 1.0 if breach else 0.0
df.at[i, time_col] = int(first_touch if breach else h + 1)
```

For BUY set:

```python
col = f"buy_stop_broken_H{h}_off{off_str}_flag"
time_col = f"buy_bars_to_breach_H{h}_off{off_str}"
```

For SELL set:

```python
col = f"sell_stop_broken_H{h}_off{off_str}_flag"
time_col = f"sell_bars_to_breach_H{h}_off{off_str}"
```

- [ ] **Step 5: Run label tests**

Run:

```bash
./.venv/bin/python -m pytest tests/processing/test_fractal_stop_breach_labels.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add processing/label_signals.py tests/processing/test_fractal_stop_breach_labels.py
git commit -m "feat: add time to breach labels"
```

---

### Task 2: Stage 5.2 Constants, Profiles, Split, And Feature Builder

**Files:**
- Modify: `ML/baseline/benchmark_stage5_transformer_breach.py`
- Test: `tests/test_stage5_transformer_breach.py`

**Interfaces:**
- Produces: `STAGE5_2_JSON_REPORT_PATH: Path`
- Produces: `STAGE5_2_TARGETS: list[str]`
- Produces: `STAGE5_2_TARGET_TO_BINARY: dict[str, str]`
- Produces: `STAGE5_2_PROFILE_KEYS: list[str]`
- Produces: `_stage5_2_profile_for_key(profile_key: str) -> dict`
- Produces: `build_stage5_2_features(df: pd.DataFrame, profile_key: str) -> np.ndarray`
- Reuses: `build_stage5_1_split(df, target_col)`
- Reuses: `extract_stage5_1b_fields(fractal_str)`

- [ ] **Step 1: Write failing tests for constants, profiles, and feature shapes**

Add near Stage 5.1b tests in `tests/test_stage5_transformer_breach.py`:

```python
def test_stage5_2_constants_and_profiles_are_frozen():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    assert runner.STAGE5_2_TARGETS == [
        "sell_bars_to_breach_H6_off05",
        "buy_bars_to_breach_H6_off05",
    ]
    assert runner.STAGE5_2_TARGET_TO_BINARY == {
        "sell_bars_to_breach_H6_off05": "sell_stop_broken_H6_off05_flag",
        "buy_bars_to_breach_H6_off05": "buy_stop_broken_H6_off05_flag",
    }
    assert runner.STAGE5_2_PROFILE_KEYS == [
        "time_only",
        "clock_shift",
        "clock_shift_back",
        "clock_shift_impulse",
        "clock_shift_back_impulse",
        "structure_full",
        "structure_full_without_back",
    ]
    assert str(runner.STAGE5_2_JSON_REPORT_PATH).endswith(
        "stage5_2_time_to_breach_regression.json"
    )


def test_stage5_2_profile_token_fields():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    assert runner._stage5_2_profile_for_key("time_only")["token_fields"] == []
    assert runner._stage5_2_profile_for_key("clock_shift")["token_fields"] == ["shift"]
    assert runner._stage5_2_profile_for_key("clock_shift_back")["token_fields"] == ["shift", "back"]
    assert runner._stage5_2_profile_for_key("clock_shift_impulse")["token_fields"] == ["shift", "impulse"]
    assert runner._stage5_2_profile_for_key("clock_shift_back_impulse")["token_fields"] == ["shift", "back", "impulse"]
    assert "back" in runner._stage5_2_profile_for_key("structure_full")["token_fields"]
    assert "back" not in runner._stage5_2_profile_for_key("structure_full_without_back")["token_fields"]


def test_build_stage5_2_features_shapes_and_no_updn():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    df = _make_stage5_0f_year_df()
    df["up_3"] = 999999.0
    X_time = runner.build_stage5_2_features(df, "time_only")
    X_clock_shift = runner.build_stage5_2_features(df, "clock_shift")
    X_back_impulse = runner.build_stage5_2_features(df, "clock_shift_back_impulse")
    X_structure = runner.build_stage5_2_features(df, "structure_full")

    assert X_time.shape == (len(df), 4)
    assert X_clock_shift.shape == (len(df), 104)
    assert X_back_impulse.shape == (len(df), 304)
    assert X_structure.shape == (len(df), 904)
    assert np.isfinite(X_structure).all()
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_stage5_2_constants_and_profiles_are_frozen tests/test_stage5_transformer_breach.py::test_stage5_2_profile_token_fields tests/test_stage5_transformer_breach.py::test_build_stage5_2_features_shapes_and_no_updn -q
```

Expected: FAIL because Stage 5.2 symbols do not exist.

- [ ] **Step 3: Add constants and profile builder**

In `ML/baseline/benchmark_stage5_transformer_breach.py`, near Stage 5.1b constants:

```python
STAGE5_2_JSON_REPORT_PATH = REPORTS_DIR / "stage5_2_time_to_breach_regression.json"
STAGE5_2_TARGETS = [
    "sell_bars_to_breach_H6_off05",
    "buy_bars_to_breach_H6_off05",
]
STAGE5_2_TARGET_TO_BINARY = {
    "sell_bars_to_breach_H6_off05": "sell_stop_broken_H6_off05_flag",
    "buy_bars_to_breach_H6_off05": "buy_stop_broken_H6_off05_flag",
}
STAGE5_2_HORIZON = 6
STAGE5_2_CENSORED_VALUE = STAGE5_2_HORIZON + 1
STAGE5_2_ENTRY_THRESHOLD = 4
STAGE5_2_SEEDS = [42, 77, 123]
STAGE5_2_PROFILE_KEYS = [
    "time_only",
    "clock_shift",
    "clock_shift_back",
    "clock_shift_impulse",
    "clock_shift_back_impulse",
    "structure_full",
    "structure_full_without_back",
]
STAGE5_2_STRUCTURE_FIELDS = STAGE5_1B_STRUCTURE_FIELDS.copy()
```

Add profile builder:

```python
def _stage5_2_profile_for_key(profile_key: str) -> dict:
    if profile_key == "time_only":
        token_fields = []
    elif profile_key == "clock_shift":
        token_fields = ["shift"]
    elif profile_key == "clock_shift_back":
        token_fields = ["shift", "back"]
    elif profile_key == "clock_shift_impulse":
        token_fields = ["shift", "impulse"]
    elif profile_key == "clock_shift_back_impulse":
        token_fields = ["shift", "back", "impulse"]
    elif profile_key == "structure_full":
        token_fields = ["shift"] + STAGE5_2_STRUCTURE_FIELDS
    elif profile_key == "structure_full_without_back":
        token_fields = ["shift"] + [
            field for field in STAGE5_2_STRUCTURE_FIELDS if field != "back"
        ]
    else:
        raise ValueError(f"Unknown Stage 5.2 profile: {profile_key}")

    return {
        "name": f"stage5_2_{profile_key}",
        "token_fields": token_fields,
        "row_fields": TIME_ONLY_ROW_FIELDS,
        "order": "freshness",
        "stage5_2": True,
    }
```

- [ ] **Step 4: Add feature builder**

Add:

```python
def build_stage5_2_features(df: pd.DataFrame, profile_key: str) -> np.ndarray:
    profile = _stage5_2_profile_for_key(profile_key)
    token_fields = profile["token_fields"]
    row_fields = profile["row_fields"]
    n_rows = len(df)
    token_width = len(token_fields) * N_FRACTALS
    X = np.zeros((n_rows, token_width + len(row_fields)), dtype=np.float32)

    for row_idx, (_, row) in enumerate(df.iterrows()):
        offset = 0
        for fractal_idx in range(N_FRACTALS):
            fstr = row.get(f"fractal{fractal_idx}", "")
            fields = extract_stage5_1b_fields(fstr)
            for field in token_fields:
                X[row_idx, offset] = float(fields.get(field, 0.0))
                offset += 1
    row_features = build_row_features(df, profile).astype(np.float32)
    if row_features.shape[1] != len(row_fields):
        raise RuntimeError(
            f"Stage 5.2 row feature width mismatch: got {row_features.shape[1]}, expected {len(row_fields)}"
        )
    X[:, token_width:] = row_features
    return X
```

- [ ] **Step 5: Run tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_stage5_2_constants_and_profiles_are_frozen tests/test_stage5_transformer_breach.py::test_stage5_2_profile_token_fields tests/test_stage5_transformer_breach.py::test_build_stage5_2_features_shapes_and_no_updn -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add ML/baseline/benchmark_stage5_transformer_breach.py tests/test_stage5_transformer_breach.py
git commit -m "feat: add stage 5.2 feature profiles"
```

---

### Task 3: Stage 5.2 Regression Metrics And Gates

**Files:**
- Modify: `ML/baseline/benchmark_stage5_transformer_breach.py`
- Test: `tests/test_stage5_transformer_breach.py`

**Interfaces:**
- Produces: `stage5_2_regression_metrics(y_true, y_pred, threshold=4, censored_value=7) -> dict`
- Produces: `stage5_2_constant_baseline_metrics(y_true, censored_value=7) -> dict`
- Produces: `stage5_2_gate_results(summary: dict, oracle_preflight: dict, censoring: dict) -> dict`
- Produces: `stage5_2_calibration_table(y_true, y_pred) -> list[dict]`

- [ ] **Step 1: Write failing tests for metrics and gates**

Add:

```python
def test_stage5_2_regression_metrics_include_auc_mae_spearman_and_calibration():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    y_true = np.array([1, 2, 3, 4, 5, 7, 7], dtype=float)
    y_pred = np.array([1.2, 2.2, 2.8, 4.2, 5.2, 6.5, 6.8], dtype=float)

    metrics = runner.stage5_2_regression_metrics(y_true, y_pred)

    assert metrics["n"] == 7
    assert metrics["spearman_r"] > 0.9
    assert metrics["mae"] < 0.5
    assert metrics["uncensored_mae"] < 0.5
    assert 0.0 <= metrics["auc_true_ge_4"] <= 1.0
    assert metrics["fixed_threshold"]["threshold"] == 4
    assert metrics["fixed_threshold"]["predicted_entries"] == 4
    assert len(metrics["calibration_table"]) == 3


def test_stage5_2_constant_baseline_metrics_are_defined():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    y_true = np.array([1, 2, 7, 7], dtype=float)
    metrics = runner.stage5_2_constant_baseline_metrics(y_true)

    assert metrics["prediction_value"] == 7
    assert metrics["mae"] == pytest.approx((6 + 5 + 0 + 0) / 4)
    assert metrics["spearman_r"] == 0.0


def test_stage5_2_gate_results_require_oracle_model_and_baseline_improvement():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    summary = {
        "best_profile": {
            "profile": "clock_shift_back_impulse",
            "val_stop": {
                "spearman_r": 0.35,
                "mae": 2.5,
                "auc_true_ge_4": 0.72,
                "yearly": {"2021": {"spearman_r": 0.32}, "2022": {"spearman_r": 0.31}},
            },
            "improvement_vs_constant": {
                "spearman_delta": 0.35,
                "mae_improvement_frac": 0.12,
            },
            "improvement_vs_time_only": {"spearman_delta": 0.04},
            "improvement_vs_clock_shift": {"spearman_delta": 0.05},
        }
    }
    oracle = {
        "pass": True,
        "oracle_time_pf": 1.4,
        "oracle_binary_pf": 1.1,
        "trades_per_year": 80,
        "yearly": {"2021": {"pf": 1.2}, "2022": {"pf": 1.4}},
    }
    censoring = {"train_core": {"censoring_rate": 0.60}}

    gates = runner.stage5_2_gate_results(summary, oracle, censoring)

    assert gates["overall_status"] == "CANDIDATE_HYPOTHESIS"
    assert gates["model_gate"]["pass"] is True
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_stage5_2_regression_metrics_include_auc_mae_spearman_and_calibration tests/test_stage5_transformer_breach.py::test_stage5_2_constant_baseline_metrics_are_defined tests/test_stage5_transformer_breach.py::test_stage5_2_gate_results_require_oracle_model_and_baseline_improvement -q
```

Expected: FAIL because metric helpers do not exist.

- [ ] **Step 3: Implement metrics**

Add imports if missing:

```python
from scipy import stats
from sklearn.metrics import roc_auc_score
```

Add helpers:

```python
def _safe_spearman(y_true, y_pred) -> float:
    yt = np.asarray(y_true, dtype=float)
    yp = np.asarray(y_pred, dtype=float)
    if len(yt) < 2 or np.nanstd(yt) == 0 or np.nanstd(yp) == 0:
        return 0.0
    rho, _ = stats.spearmanr(yt, yp)
    return float(rho) if np.isfinite(rho) else 0.0


def stage5_2_calibration_table(y_true, y_pred) -> list[dict]:
    yt = np.asarray(y_true, dtype=float)
    yp = np.asarray(y_pred, dtype=float)
    bins = [
        ("pred_1_2", yp < 3),
        ("pred_3_4", (yp >= 3) & (yp < 5),
        ),
        ("pred_5_7", yp >= 5),
    ]
    rows = []
    for name, mask in bins:
        true_vals = yt[mask]
        rows.append({
            "bucket": name,
            "n": int(mask.sum()),
            "true_median": float(np.nanmedian(true_vals)) if len(true_vals) else None,
            "true_ge_4_rate": float(np.mean(true_vals >= STAGE5_2_ENTRY_THRESHOLD)) if len(true_vals) else None,
        })
    return rows


def stage5_2_regression_metrics(y_true, y_pred,
                                threshold: int = STAGE5_2_ENTRY_THRESHOLD,
                                censored_value: int = STAGE5_2_CENSORED_VALUE) -> dict:
    yt = np.asarray(y_true, dtype=float)
    yp = np.asarray(y_pred, dtype=float)
    valid = np.isfinite(yt) & np.isfinite(yp)
    yt = yt[valid]
    yp = yp[valid]
    true_binary = (yt >= threshold).astype(int)
    pred_binary = yp >= threshold
    uncensored = yt < censored_value
    auc = None
    if len(np.unique(true_binary)) == 2:
        try:
            auc = float(roc_auc_score(true_binary, yp))
        except ValueError:
            auc = 0.5
    return {
        "n": int(len(yt)),
        "spearman_r": _safe_spearman(yt, yp),
        "mae": float(np.mean(np.abs(yp - yt))) if len(yt) else None,
        "uncensored_mae": float(np.mean(np.abs(yp[uncensored] - yt[uncensored]))) if np.any(uncensored) else None,
        "auc_true_ge_4": auc,
        "fixed_threshold": {
            "threshold": int(threshold),
            "predicted_entries": int(pred_binary.sum()),
            "precision": float(np.mean(true_binary[pred_binary])) if np.any(pred_binary) else None,
            "recall": float(np.sum(true_binary[pred_binary]) / max(np.sum(true_binary), 1)),
        },
        "calibration_table": stage5_2_calibration_table(yt, yp),
    }


def stage5_2_constant_baseline_metrics(y_true,
                                       censored_value: int = STAGE5_2_CENSORED_VALUE) -> dict:
    yt = np.asarray(y_true, dtype=float)
    pred = np.full(len(yt), censored_value, dtype=float)
    metrics = stage5_2_regression_metrics(yt, pred)
    metrics["prediction_value"] = int(censored_value)
    metrics["spearman_r"] = 0.0
    return metrics
```

- [ ] **Step 4: Implement gate helper**

Add:

```python
def stage5_2_gate_results(summary: dict, oracle_preflight: dict,
                          censoring: dict) -> dict:
    train_censor = (censoring.get("train_core") or {}).get("censoring_rate")
    censoring_pass = train_censor is not None and train_censor <= 0.70
    best = summary.get("best_profile") or {}
    val = best.get("val_stop") or {}
    improvement_constant = best.get("improvement_vs_constant") or {}
    improvement_time = best.get("improvement_vs_time_only") or {}
    improvement_clock = best.get("improvement_vs_clock_shift") or {}
    yearly = val.get("yearly") or {}
    yearly_pass = (
        len(yearly) >= 2
        and sum(1 for v in yearly.values() if (v.get("spearman_r") or 0.0) > 0.0) >= 2
    )
    model_checks = {
        "spearman_ge_0_30": (val.get("spearman_r") or 0.0) >= 0.30,
        "spearman_delta_constant_ge_0_05": (improvement_constant.get("spearman_delta") or 0.0) >= 0.05,
        "spearman_delta_time_only_ge_0_03": (improvement_time.get("spearman_delta") or 0.0) >= 0.03,
        "spearman_delta_clock_shift_ge_0_03": (improvement_clock.get("spearman_delta") or 0.0) >= 0.03,
        "mae_le_3": val.get("mae") is not None and val["mae"] <= 3.0,
        "mae_improvement_constant_ge_10pct": (improvement_constant.get("mae_improvement_frac") or 0.0) >= 0.10,
        "auc_ge_0_70": val.get("auc_true_ge_4") is not None and val["auc_true_ge_4"] >= 0.70,
        "yearly_not_single_year": yearly_pass,
    }
    model_pass = all(model_checks.values())
    oracle_pass = bool(oracle_preflight.get("pass"))
    if not censoring_pass:
        status = "DIAGNOSTIC_ONLY"
    elif not oracle_pass:
        status = "ORACLE_FAILED"
    elif not model_pass:
        status = "MODEL_GATE_FAILED"
    else:
        status = "CANDIDATE_HYPOTHESIS"
    return {
        "overall_status": status,
        "censoring_gate": {"pass": bool(censoring_pass), "train_censoring_rate": train_censor},
        "oracle_gate": {"pass": oracle_pass},
        "model_gate": {"pass": model_pass, "checks": model_checks},
    }
```

- [ ] **Step 5: Run metrics tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_stage5_2_regression_metrics_include_auc_mae_spearman_and_calibration tests/test_stage5_transformer_breach.py::test_stage5_2_constant_baseline_metrics_are_defined tests/test_stage5_transformer_breach.py::test_stage5_2_gate_results_require_oracle_model_and_baseline_improvement -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add ML/baseline/benchmark_stage5_transformer_breach.py tests/test_stage5_transformer_breach.py
git commit -m "feat: add stage 5.2 regression metrics"
```

---

### Task 4: Oracle Preflight First-Touch Simulator

**Files:**
- Modify: `ML/baseline/benchmark_stage5_transformer_breach.py`
- Test: `tests/test_stage5_transformer_breach.py`

**Interfaces:**
- Produces: `stage5_2_first_touch_trade_result(entry_price: float, stop_price: float, take_price: float, side: str, future_bars: list[dict]) -> dict`
- Produces: `run_stage5_2_oracle_preflight(split: dict, target_col: str, binary_col: str, ohlc_path: Path = OHLC_FILE) -> dict`

- [ ] **Step 1: Write failing first-touch simulator tests**

Add:

```python
def test_stage5_2_first_touch_trade_result_tp_sl_and_timeout():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    buy_tp = runner.stage5_2_first_touch_trade_result(
        entry_price=100.0,
        stop_price=98.0,
        take_price=104.0,
        side="buy",
        future_bars=[
            {"high": 103.0, "low": 99.0},
            {"high": 104.5, "low": 99.5},
        ],
    )
    sell_sl = runner.stage5_2_first_touch_trade_result(
        entry_price=100.0,
        stop_price=102.0,
        take_price=96.0,
        side="sell",
        future_bars=[
            {"high": 102.5, "low": 99.0},
            {"high": 101.0, "low": 95.5},
        ],
    )
    timeout = runner.stage5_2_first_touch_trade_result(
        entry_price=100.0,
        stop_price=98.0,
        take_price=104.0,
        side="buy",
        future_bars=[{"high": 101.0, "low": 99.0}],
    )

    assert buy_tp["outcome"] == "TP"
    assert buy_tp["pnl_r"] == pytest.approx(2.0)
    assert sell_sl["outcome"] == "SL"
    assert sell_sl["pnl_r"] == pytest.approx(-1.0)
    assert timeout["outcome"] == "TIMEOUT"
    assert timeout["pnl_r"] == pytest.approx(0.0)
```

- [ ] **Step 2: Run test and verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_stage5_2_first_touch_trade_result_tp_sl_and_timeout -q
```

Expected: FAIL because simulator does not exist.

- [ ] **Step 3: Implement first-touch simulator**

Add:

```python
def stage5_2_first_touch_trade_result(entry_price: float, stop_price: float,
                                      take_price: float, side: str,
                                      future_bars: list[dict]) -> dict:
    if side not in {"buy", "sell"}:
        raise ValueError(f"side must be buy or sell, got {side}")
    risk = abs(entry_price - stop_price)
    reward = abs(take_price - entry_price)
    for idx, bar in enumerate(future_bars, start=1):
        high = float(bar["high"])
        low = float(bar["low"])
        if side == "buy":
            sl_hit = low <= stop_price
            tp_hit = high >= take_price
        else:
            sl_hit = high >= stop_price
            tp_hit = low <= take_price
        if sl_hit and tp_hit:
            return {"outcome": "AMBIGUOUS_SL_FIRST", "bars": idx, "pnl_r": -1.0}
        if sl_hit:
            return {"outcome": "SL", "bars": idx, "pnl_r": -1.0}
        if tp_hit:
            return {"outcome": "TP", "bars": idx, "pnl_r": float(reward / risk) if risk > 0 else 0.0}
    return {"outcome": "TIMEOUT", "bars": len(future_bars), "pnl_r": 0.0}
```

- [ ] **Step 4: Add oracle preflight with OHLC first-touch replay**

Add `datetime` import near other standard-library imports:

```python
from datetime import datetime, timezone
```

Add `load_ohlc_index` import after the existing `sys.path.insert(...)` line:

```python
from processing.label_signals import load_ohlc_index
```

Implement `run_stage5_2_oracle_preflight(split, target_col, binary_col, ohlc_path=OHLC_FILE)` using `val_stop` rows and `DATA/XAUUSD_H1_OHLC.csv`:

```python
def _stage5_2_pf(pnls: list[float]) -> float | None:
    gains = sum(v for v in pnls if v > 0)
    losses = -sum(v for v in pnls if v < 0)
    if losses == 0:
        return None if gains == 0 else float("inf")
    return float(gains / losses)


def _stage5_2_row_datetime(row: pd.Series):
    try:
        return datetime.strptime(str(row["time"]), "%Y.%m.%d %H:%M").replace(tzinfo=timezone.utc)
    except (KeyError, ValueError, TypeError):
        return None


def _stage5_2_future_bars(ohlc: dict, times: list, idx0: int,
                          horizon: int = STAGE5_2_HORIZON) -> list[dict]:
    bars = []
    for k in range(idx0 + 1, min(idx0 + 1 + horizon, len(times))):
        opn, high, low, close = ohlc[times[k]]
        bars.append({"open": opn, "high": high, "low": low, "close": close})
    return bars


def _stage5_2_oracle_trade_pnl(row: pd.Series, ohlc: dict, times: list,
                               time_idx: dict) -> tuple[float | None, str | None]:
    row_dt = _stage5_2_row_datetime(row)
    if row_dt is None or row_dt not in time_idx:
        return None, None
    idx0 = time_idx[row_dt]
    if idx0 + STAGE5_2_HORIZON >= len(times):
        return None, None
    fields = extract_stage5_1b_fields(row.get("fractal0", ""))
    fractal_dir = fields.get("direction", 0.0)
    fractal_price = fields.get("price", 0.0)
    try:
        atr = float(row["ATR"])
    except (KeyError, TypeError, ValueError):
        return None, None
    if atr <= 0 or fractal_price <= 0:
        return None, None
    entry_price = float(ohlc[times[idx0]][3])
    if fractal_dir == -1:
        side = "buy"
        stop_price = fractal_price - 0.5 * atr
        take_price = entry_price + 2.0 * atr
    elif fractal_dir == 1:
        side = "sell"
        stop_price = fractal_price + 0.5 * atr
        take_price = entry_price - 2.0 * atr
    else:
        return None, None
    result = stage5_2_first_touch_trade_result(
        entry_price=entry_price,
        stop_price=stop_price,
        take_price=take_price,
        side=side,
        future_bars=_stage5_2_future_bars(ohlc, times, idx0),
    )
    return float(result["pnl_r"]), result["outcome"]


def run_stage5_2_oracle_preflight(split: dict, target_col: str,
                                  binary_col: str,
                                  ohlc_path: Path = OHLC_FILE) -> dict:
    val = split["val_stop"].copy()
    if target_col not in val or binary_col not in val:
        return {"pass": False, "reason": "missing_target_or_binary_column"}
    valid = val[target_col].notna() & val[binary_col].notna()
    val = val.loc[valid].copy()
    ohlc, times, time_idx = load_ohlc_index(str(ohlc_path))
    time_entries = val[target_col] >= STAGE5_2_ENTRY_THRESHOLD
    binary_entries = val[binary_col] == 0.0

    time_pnls = []
    time_outcomes = defaultdict(int)
    for _, row in val.loc[time_entries].iterrows():
        pnl, outcome = _stage5_2_oracle_trade_pnl(row, ohlc, times, time_idx)
        if pnl is not None:
            time_pnls.append(pnl)
            time_outcomes[outcome] += 1

    binary_pnls = []
    binary_outcomes = defaultdict(int)
    for _, row in val.loc[binary_entries].iterrows():
        pnl, outcome = _stage5_2_oracle_trade_pnl(row, ohlc, times, time_idx)
        if pnl is not None:
            binary_pnls.append(pnl)
            binary_outcomes[outcome] += 1

    time_pf = _stage5_2_pf(time_pnls)
    binary_pf = _stage5_2_pf(binary_pnls)
    years = sorted(int(y) for y in val["_year"].dropna().unique()) if "_year" in val else []
    result = {
        "oracle_time_pf": time_pf,
        "oracle_binary_pf": binary_pf,
        "oracle_time_outcomes": dict(time_outcomes),
        "oracle_binary_outcomes": dict(binary_outcomes),
        "trades": int(len(time_pnls)),
        "trades_per_year": float(len(time_pnls) / max(len(years), 1)),
        "yearly": {},
    }
    if "_year" in val:
        for year, sub in val.loc[time_entries].groupby("_year"):
            pnls = []
            for _, row in sub.iterrows():
                pnl, _ = _stage5_2_oracle_trade_pnl(row, ohlc, times, time_idx)
                if pnl is not None:
                    pnls.append(pnl)
            result["yearly"][str(int(year))] = {
                "trades": int(len(pnls)),
                "pf": _stage5_2_pf(pnls),
            }
    pf_delta = None
    if time_pf is not None and binary_pf is not None and np.isfinite(time_pf) and np.isfinite(binary_pf):
        pf_delta = time_pf - binary_pf
    result["pf_delta_vs_binary"] = pf_delta
    yearly_pfs = [
        row.get("pf") for row in result["yearly"].values()
        if row.get("pf") is not None and np.isfinite(row.get("pf"))
    ]
    result["pass"] = (
        time_pf is not None
        and (np.isinf(time_pf) or time_pf >= 1.3)
        and (pf_delta is None or pf_delta >= 0.2)
        and result["trades_per_year"] >= 50
        and len(yearly_pfs) >= 2
        and max(yearly_pfs) < sum(yearly_pfs)
    )
    return result
```

- [ ] **Step 5: Run simulator test**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_stage5_2_first_touch_trade_result_tp_sl_and_timeout -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add ML/baseline/benchmark_stage5_transformer_breach.py tests/test_stage5_transformer_breach.py
git commit -m "feat: add stage 5.2 oracle simulator"
```

---

### Task 5: Profile-Seed Regression Evaluation And Summary

**Files:**
- Modify: `ML/baseline/benchmark_stage5_transformer_breach.py`
- Test: `tests/test_stage5_transformer_breach.py`

**Interfaces:**
- Produces: `evaluate_stage5_2_profile_seed(split: dict, profile_key: str, target_col: str, seed: int) -> dict`
- Produces: `summarize_stage5_2_target(raw_runs: list[dict], target_col: str) -> dict`
- Consumes: `build_stage5_2_features()`, `stage5_2_regression_metrics()`

- [ ] **Step 1: Write failing evaluation and summary tests**

Add:

```python
def test_evaluate_stage5_2_profile_seed_returns_regression_metrics(monkeypatch):
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    df = _make_stage5_0f_year_df()
    df["sell_bars_to_breach_H6_off05"] = np.where(
        df["sell_stop_broken_H6_off05_flag"] == 1.0, 2, 7
    )
    split = runner.build_stage5_1_split(df, "sell_bars_to_breach_H6_off05")

    result = runner.evaluate_stage5_2_profile_seed(
        split,
        "clock_shift_back",
        "sell_bars_to_breach_H6_off05",
        seed=42,
    )

    assert result["profile"] == "clock_shift_back"
    assert result["target"] == "sell_bars_to_breach_H6_off05"
    assert result["seed"] == 42
    assert "spearman_r" in result["val_stop"]
    assert "mae" in result["val_stop"]
    assert "auc_true_ge_4" in result["val_stop"]


def test_summarize_stage5_2_target_selects_best_profile_and_baselines():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    target = "sell_bars_to_breach_H6_off05"
    raw_runs = []
    for profile, rho, mae in [
        ("time_only", 0.10, 3.5),
        ("clock_shift", 0.12, 3.4),
        ("clock_shift_back", 0.35, 2.7),
    ]:
        raw_runs.append({
            "target": target,
            "profile": profile,
            "seed": 42,
            "val_stop": {"spearman_r": rho, "mae": mae, "auc_true_ge_4": 0.71},
            "diagnostic_holdout": {"spearman_r": rho - 0.05, "mae": mae + 0.2},
        })

    summary = runner.summarize_stage5_2_target(raw_runs, target)

    assert summary["best_profile"]["profile"] == "clock_shift_back"
    assert summary["best_profile"]["improvement_vs_time_only"]["spearman_delta"] == pytest.approx(0.25)
    assert summary["best_profile"]["improvement_vs_clock_shift"]["spearman_delta"] == pytest.approx(0.23)
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_evaluate_stage5_2_profile_seed_returns_regression_metrics tests/test_stage5_transformer_breach.py::test_summarize_stage5_2_target_selects_best_profile_and_baselines -q
```

Expected: FAIL because evaluation and summary helpers do not exist.

- [ ] **Step 3: Implement evaluation**

Add:

```python
def evaluate_stage5_2_profile_seed(split: dict, profile_key: str,
                                   target_col: str, seed: int) -> dict:
    train = split["train_core"]
    val = split["val_stop"]
    holdout = split["diagnostic_holdout"]
    low_n = split["low_n_disclosure"]
    X_train = build_stage5_2_features(train, profile_key)
    X_val = build_stage5_2_features(val, profile_key)
    X_holdout = build_stage5_2_features(holdout, profile_key)
    X_low_n = build_stage5_2_features(low_n, profile_key) if len(low_n) else None
    y_train = train[target_col].astype(float).to_numpy()
    y_val = val[target_col].astype(float).to_numpy()
    y_holdout = holdout[target_col].astype(float).to_numpy()
    y_low_n = low_n[target_col].astype(float).to_numpy() if len(low_n) else np.asarray([])

    model = xgb.XGBRegressor(
        objective="reg:pseudohubererror",
        n_estimators=300,
        max_depth=3,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=0.9,
        random_state=seed,
        n_jobs=1,
        tree_method="hist",
    )
    model.fit(X_train, y_train)
    val_pred = np.clip(model.predict(X_val), 1.0, STAGE5_2_CENSORED_VALUE)
    holdout_pred = np.clip(model.predict(X_holdout), 1.0, STAGE5_2_CENSORED_VALUE)
    low_n_pred = (
        np.clip(model.predict(X_low_n), 1.0, STAGE5_2_CENSORED_VALUE)
        if X_low_n is not None else np.asarray([])
    )
    return {
        "profile": profile_key,
        "target": target_col,
        "seed": int(seed),
        "train_core": {"n": int(len(train))},
        "val_stop": stage5_2_regression_metrics(y_val, val_pred),
        "diagnostic_holdout": stage5_2_regression_metrics(y_holdout, holdout_pred),
        "low_n_disclosure": stage5_2_regression_metrics(y_low_n, low_n_pred) if len(y_low_n) else {"n": 0},
        "yearly_val": _stage5_2_yearly_metrics(val, target_col, val_pred),
        "yearly_diagnostic_holdout": _stage5_2_yearly_metrics(holdout, target_col, holdout_pred),
    }
```

Add yearly helper:

```python
def _stage5_2_yearly_metrics(df: pd.DataFrame, target_col: str,
                             pred: np.ndarray) -> dict:
    if "_year" not in df:
        return {}
    out = {}
    pred = np.asarray(pred, dtype=float)
    for year, idx in df.groupby("_year").groups.items():
        positions = df.index.get_indexer(idx)
        y = df.loc[idx, target_col].astype(float).to_numpy()
        out[str(int(year))] = stage5_2_regression_metrics(y, pred[positions])
    return out
```

- [ ] **Step 4: Implement summary**

Add:

```python
def _median_metric(runs: list[dict], period: str, metric: str):
    vals = [((r.get(period) or {}).get(metric)) for r in runs]
    vals = [v for v in vals if v is not None and np.isfinite(v)]
    return float(np.median(vals)) if vals else None


def _median_yearly_metric(runs: list[dict], period: str, metric: str) -> dict:
    years = sorted({
        year for run in runs
        for year in (run.get(period) or {}).keys()
    })
    out = {}
    for year in years:
        vals = [
            ((run.get(period) or {}).get(year) or {}).get(metric)
            for run in runs
        ]
        vals = [v for v in vals if v is not None and np.isfinite(v)]
        out[year] = {metric: float(np.median(vals)) if vals else None}
    return out


def summarize_stage5_2_target(raw_runs: list[dict], target_col: str) -> dict:
    target_runs = [r for r in raw_runs if r.get("target") == target_col]
    by_profile = {}
    for profile in STAGE5_2_PROFILE_KEYS:
        runs = [r for r in target_runs if r.get("profile") == profile]
        if not runs:
            continue
        by_profile[profile] = {
            "profile": profile,
            "n_seed_runs": len(runs),
            "val_stop": {
                "spearman_r": _median_metric(runs, "val_stop", "spearman_r"),
                "mae": _median_metric(runs, "val_stop", "mae"),
                "auc_true_ge_4": _median_metric(runs, "val_stop", "auc_true_ge_4"),
                "yearly": _median_yearly_metric(runs, "yearly_val", "spearman_r"),
            },
            "diagnostic_holdout": {
                "spearman_r": _median_metric(runs, "diagnostic_holdout", "spearman_r"),
                "mae": _median_metric(runs, "diagnostic_holdout", "mae"),
                "auc_true_ge_4": _median_metric(runs, "diagnostic_holdout", "auc_true_ge_4"),
                "yearly": _median_yearly_metric(runs, "yearly_diagnostic_holdout", "spearman_r"),
            },
        }
    best = max(
        by_profile.values(),
        key=lambda item: (item["val_stop"].get("spearman_r") or -999.0),
    ) if by_profile else {}
    if best:
        time_rho = (by_profile.get("time_only") or {}).get("val_stop", {}).get("spearman_r")
        clock_rho = (by_profile.get("clock_shift") or {}).get("val_stop", {}).get("spearman_r")
        best_rho = best["val_stop"].get("spearman_r")
        best["improvement_vs_time_only"] = {
            "spearman_delta": None if time_rho is None or best_rho is None else best_rho - time_rho
        }
        best["improvement_vs_clock_shift"] = {
            "spearman_delta": None if clock_rho is None or best_rho is None else best_rho - clock_rho
        }
    return {"profiles": by_profile, "best_profile": best}
```

- [ ] **Step 5: Run tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_evaluate_stage5_2_profile_seed_returns_regression_metrics tests/test_stage5_transformer_breach.py::test_summarize_stage5_2_target_selects_best_profile_and_baselines -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add ML/baseline/benchmark_stage5_transformer_breach.py tests/test_stage5_transformer_breach.py
git commit -m "feat: evaluate stage 5.2 regressors"
```

---

### Task 6: Stage 5.2 Runner, JSON Report, And CLI

**Files:**
- Modify: `ML/baseline/benchmark_stage5_transformer_breach.py`
- Test: `tests/test_stage5_transformer_breach.py`

**Interfaces:**
- Produces: `run_stage5_2_time_to_breach_regression(target_splits: dict, output_path: Path = STAGE5_2_JSON_REPORT_PATH) -> dict`
- Adds CLI flag: `--stage5-2-time-to-breach-regression`
- Output: `ML/reports/stage5_2_time_to_breach_regression.json`

- [ ] **Step 1: Write failing runner and CLI tests**

Add:

```python
def test_stage5_2_runner_writes_json(monkeypatch, tmp_path):
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    df = _make_stage5_0f_year_df()
    df["sell_bars_to_breach_H6_off05"] = np.where(
        df["sell_stop_broken_H6_off05_flag"] == 1.0, 2, 7
    )
    df["buy_bars_to_breach_H6_off05"] = np.where(
        df["buy_stop_broken_H6_off05_flag"] == 1.0, 2, 7
    )
    target_splits = {"sell": (df, df, df), "buy": (df, df, df)}

    monkeypatch.setattr(
        runner,
        "run_stage5_2_oracle_preflight",
        lambda split, target_col, binary_col: {
            "pass": True,
            "oracle_time_pf": 1.5,
            "oracle_binary_pf": 1.1,
            "trades_per_year": 80,
            "yearly": {"2021": {"pf": 1.2}, "2022": {"pf": 1.4}},
        },
    )
    monkeypatch.setattr(
        runner,
        "evaluate_stage5_2_profile_seed",
        lambda split, profile, target, seed: {
            "profile": profile,
            "target": target,
            "seed": seed,
            "val_stop": {"spearman_r": 0.35, "mae": 2.5, "auc_true_ge_4": 0.72},
            "diagnostic_holdout": {"spearman_r": 0.30, "mae": 2.8, "auc_true_ge_4": 0.69},
        },
    )
    monkeypatch.setattr(
        runner,
        "summarize_stage5_2_target",
        lambda raw_runs, target: {
            "profiles": {},
            "best_profile": {
                "profile": "clock_shift_back_impulse",
                "val_stop": {
                    "spearman_r": 0.35,
                    "mae": 2.5,
                    "auc_true_ge_4": 0.72,
                    "yearly": {"2021": {"spearman_r": 0.31}, "2022": {"spearman_r": 0.32}},
                },
                "improvement_vs_constant": {
                    "spearman_delta": 0.35,
                    "mae_improvement_frac": 0.12,
                },
                "improvement_vs_time_only": {"spearman_delta": 0.04},
                "improvement_vs_clock_shift": {"spearman_delta": 0.04},
            },
        },
    )

    report = runner.run_stage5_2_time_to_breach_regression(
        target_splits,
        output_path=tmp_path / "stage5_2.json",
    )

    assert report["stage"] == "5.2_time_to_breach_regression"
    assert report["status"] in {"CANDIDATE_HYPOTHESIS", "MODEL_GATE_FAILED", "ORACLE_FAILED", "DIAGNOSTIC_ONLY"}
    assert report["progress"]["done_runs"] == 42
    assert (tmp_path / "stage5_2.json").exists()


def test_stage5_2_cli_argument_exists_in_build_arg_parser():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    parser = runner.build_arg_parser()
    args = parser.parse_args(["--stage5-2-time-to-breach-regression"])

    assert args.stage5_2_time_to_breach_regression is True
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_stage5_2_runner_writes_json tests/test_stage5_transformer_breach.py::test_stage5_2_cli_argument_exists_in_build_arg_parser -q
```

Expected: FAIL because runner and CLI flag do not exist.

- [ ] **Step 3: Implement censoring helper and runner**

Add:

```python
def _stage5_2_censoring(split: dict, target_col: str) -> dict:
    out = {}
    for name, df in split.items():
        vals = df[target_col].dropna().astype(float)
        out[name] = {
            "n": int(len(vals)),
            "censored_count": int((vals >= STAGE5_2_CENSORED_VALUE).sum()),
            "censoring_rate": float((vals >= STAGE5_2_CENSORED_VALUE).mean()) if len(vals) else None,
        }
    return out


def run_stage5_2_time_to_breach_regression(target_splits: dict,
                                           output_path: Path = STAGE5_2_JSON_REPORT_PATH) -> dict:
    report = {
        "stage": "5.2_time_to_breach_regression",
        "status": "RUNNING",
        "level": "candidate_hypothesis",
        "targets": STAGE5_2_TARGETS,
        "profiles": STAGE5_2_PROFILE_KEYS,
        "seeds": STAGE5_2_SEEDS,
        "oracle_preflight": {},
        "censoring": {},
        "constant_baseline": {},
        "raw_runs": [],
        "summary": {},
        "gate_results": {},
        "progress": {"done_runs": 0, "total_runs": len(STAGE5_2_TARGETS) * len(STAGE5_2_PROFILE_KEYS) * len(STAGE5_2_SEEDS)},
    }
    combined_by_name = {
        "sell_bars_to_breach_H6_off05": pd.concat(target_splits["sell"], ignore_index=True),
        "buy_bars_to_breach_H6_off05": pd.concat(target_splits["buy"], ignore_index=True),
    }
    for target_col in STAGE5_2_TARGETS:
        binary_col = STAGE5_2_TARGET_TO_BINARY[target_col]
        split = build_stage5_1_split(combined_by_name[target_col], target_col)
        report["censoring"][target_col] = _stage5_2_censoring(split, target_col)
        oracle = run_stage5_2_oracle_preflight(split, target_col, binary_col)
        report["oracle_preflight"][target_col] = oracle
        y_val = split["val_stop"][target_col].astype(float).to_numpy()
        report["constant_baseline"][target_col] = stage5_2_constant_baseline_metrics(y_val)
        for profile in STAGE5_2_PROFILE_KEYS:
            for seed in STAGE5_2_SEEDS:
                run = evaluate_stage5_2_profile_seed(split, profile, target_col, seed)
                report["raw_runs"].append(run)
                report["progress"]["done_runs"] += 1
        summary = summarize_stage5_2_target(report["raw_runs"], target_col)
        best = summary.get("best_profile") or {}
        const = report["constant_baseline"][target_col]
        if best:
            best.setdefault("improvement_vs_constant", {})
            best["improvement_vs_constant"]["spearman_delta"] = (
                (best.get("val_stop", {}).get("spearman_r") or 0.0)
                - (const.get("spearman_r") or 0.0)
            )
            if best.get("val_stop", {}).get("mae") is not None and const.get("mae"):
                best["improvement_vs_constant"]["mae_improvement_frac"] = (
                    (const["mae"] - best["val_stop"]["mae"]) / const["mae"]
                )
        report["summary"][target_col] = summary
        report["gate_results"][target_col] = stage5_2_gate_results(
            summary, oracle, report["censoring"][target_col]
        )
    statuses = [v["overall_status"] for v in report["gate_results"].values()]
    report["status"] = "CANDIDATE_HYPOTHESIS" if all(s == "CANDIDATE_HYPOTHESIS" for s in statuses) else "DIAGNOSTIC_ONLY"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    return report
```

- [ ] **Step 4: Add CLI flag and fast path**

In `build_arg_parser()`:

```python
parser.add_argument("--stage5-2-time-to-breach-regression", action="store_true",
                    help="Run Stage 5.2 time-to-breach regression candidate-hypothesis.")
```

In `main()` near Stage 5.1b fast path:

```python
if args.stage5_2_time_to_breach_regression:
    sell_df, val_df, test_df = load_splits(target_col="sell_bars_to_breach_H6_off05")
    buy_train, buy_val, buy_test = load_splits(target_col="buy_bars_to_breach_H6_off05")
    report = run_stage5_2_time_to_breach_regression(
        {"sell": (sell_df, val_df, test_df), "buy": (buy_train, buy_val, buy_test)}
    )
    print(json.dumps({"status": report["status"], "progress": report["progress"]}, indent=2))
    return
```

- [ ] **Step 5: Run runner tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_stage5_2_runner_writes_json tests/test_stage5_transformer_breach.py::test_stage5_2_cli_argument_exists_in_build_arg_parser -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add ML/baseline/benchmark_stage5_transformer_breach.py tests/test_stage5_transformer_breach.py
git commit -m "feat: add stage 5.2 runner"
```

---

### Task 7: Verification, Full Run, And Stage Closure

**Files:**
- Modify after run: `ML/reports/stage5_2_time_to_breach_regression.json`
- Create after run: `docs/reports/YYYY-MM-DD-stage5_2-time-to-breach-regression.md`
- Modify after report: `CHANGELOG.md`
- Modify after report: `CONTEXT_HANDOFF.md`
- Modify after report: `wiki/research/fractal-stop-research.md`
- Modify after report: `wiki/index.md`
- Modify after report: `wiki/log.md`
- Modify after report: `wiki/REPO_integrity.md`

**Interfaces:**
- Consumes: CLI `--stage5-2-time-to-breach-regression`
- Produces: final structured JSON and canonical report.

- [ ] **Step 1: Run focused tests**

Run:

```bash
./.venv/bin/python -m pytest tests/processing/test_fractal_stop_breach_labels.py tests/test_stage5_transformer_breach.py -k "stage5_2 or fractal_stop_breach" -q
```

Expected: PASS.

- [ ] **Step 2: Run full tests**

Run:

```bash
./.venv/bin/python -m pytest tests/ -q
```

Expected: PASS.

- [ ] **Step 3: Run Stage 5.2**

Run:

```bash
./.venv/bin/python -m ML.baseline.benchmark_stage5_transformer_breach --stage5-2-time-to-breach-regression
```

Expected:

```text
ML/reports/stage5_2_time_to_breach_regression.json exists
progress.done_runs = 42
status is one of DIAGNOSTIC_ONLY, CANDIDATE_HYPOTHESIS
```

- [ ] **Step 4: Validate JSON**

Run:

```bash
./.venv/bin/python -m json.tool ML/reports/stage5_2_time_to_breach_regression.json >/tmp/stage5_2_json_check.out
```

Expected: exit code 0.

- [ ] **Step 5: Write report with stage-reporting skill**

Read:

```bash
sed -n '1,260p' .opencode/skills/my/stage-reporting/SKILL.md
sed -n '1,260p' docs/reports/README.md
sed -n '1,260p' docs/methodology/16-reporting-audit.md
```

Create `docs/reports/YYYY-MM-DD-stage5_2-time-to-breach-regression.md` with:

```markdown
# Stage 5.2 — регрессия времени до пробоя

> **Дата**: YYYY-MM-DD
> **Статус**: Completed
> **Вердикт**: CANDIDATE_HYPOTHESIS | DIAGNOSTIC_ONLY
> **Цель**: Проверить, даёт ли censored proxy времени до пробоя больше торгово полезного сигнала, чем бинарный `H6_off05`.
> **Уровень этапа**: кандидат-гипотеза
> **Related plan/spec**: `docs/superpowers/specs/2026-06-25-stage5_2-time-to-breach-regression-design.md`
```

Report must include:

- Oracle-preflight result.
- Censoring rates.
- Constant/time_only/clock_shift comparisons.
- Best profile and gate pass/fail table.
- Explicit statement that `2023-2025` are diagnostic disclosure only.
- Explicit statement that `CANDIDATE_HYPOTHESIS` is not production/trading candidate.

- [ ] **Step 6: Update changelog, handoff, wiki**

Use `stage-reporting` and `wiki` skills:

```bash
./.venv/bin/python wiki/wiki.py status
./.venv/bin/python wiki/wiki.py generate
./.venv/bin/python wiki/wiki.py verify
```

Expected:

```text
Wiki is up to date. No gaps found.
OK — index is up to date.
```

- [ ] **Step 7: Final commit**

```bash
git add ML/reports/stage5_2_time_to_breach_regression.json docs/reports/YYYY-MM-DD-stage5_2-time-to-breach-regression.md CHANGELOG.md CONTEXT_HANDOFF.md wiki/REPO_integrity.md wiki/index.md wiki/log.md wiki/research/fractal-stop-research.md
git commit -m "docs: report stage 5.2 time to breach"
```

---

## Self-Review

Spec coverage:

- `CANDIDATE_HYPOTHESIS` status: Task 3 gates and Task 6 runner.
- H+1 censored proxy: Task 1 labels and Task 3 metrics.
- BUY/SELL OHLC direction correctness: Task 1 helper and tests.
- AUC from continuous score: Task 3 metrics.
- Constant, `time_only`, `clock_shift` baselines: Tasks 2, 3, 5, 6.
- Oracle-preflight through first-touch simulator: Task 4.
- 42 model budget: Task 6 runner.
- JSON/report artifacts: Task 7.
