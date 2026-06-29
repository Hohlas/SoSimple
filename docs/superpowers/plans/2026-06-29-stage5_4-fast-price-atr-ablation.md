# Stage 5.4 Fast Price/ATR Ablation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Проверить, усиливают ли физически обоснованные price/ATR-признаки фиксированную Stage 5.3 цель `fast` без нового поиска целей.

**Architecture:** Stage 5.4 переиспользует Stage 5.2/5.3 `bars_to_breach` labels, fixed split Stage 5.x, XGBoost-классификатор Stage 5.3 и отдельный JSON artifact. Новый код добавляет только Stage 5.4 feature profiles, A7-аудит финальных матриц до обучения, summary/gate вокруг fixed target `fast` и CLI fast path; Stage 5.3 не изменяется по смыслу.

**Tech Stack:** Python 3.10, pandas, numpy, scikit-learn metrics, XGBoost, pytest, JSON reports.

## Global Constraints

- Работать в текущей feature-ветке; worktree запрещён `AGENTS.md`.
- Использовать Python окружение проекта: `./.venv/bin/python`.
- После изменений в Python-коде запускать `./.venv/bin/python -m pytest tests/ -q`.
- Для ML-infrastructure изменений применять TDD: сначала failing test, затем код.
- Stage 5.4 имеет статус `DIAGNOSTIC_ONLY`; `2023-2025` остаются diagnostic disclosure, не независимое подтверждение.
- Цель фиксирована: `fast`, то есть `bars_to_breach ∈ {1,2}`.
- Нельзя добавлять новый target search, `survives_at_least_k`, `medium`, `no_breach` или `breach_after_k`.
- Sell — primary side, потому что Stage 5.3 sell `fast` прошёл gate.
- Buy — borderline disclosure, потому что Stage 5.3 buy `fast` прошёл порог `delta ≥ 0.02` только в `1/3` seed.
- Основной baseline сравнения внутри Stage 5.4: `clock_shift_back` для sell, `clock_shift_back_impulse` для buy.
- Primary feature addition: `price_coord_atr = (price - f0_price) / ATR`, transformed as `signed_log1p`.
- Secondary feature addition: `price_atr_scaled = price / ATR`, transformed as `asinh`.
- Diagnostic-only additions: `ATR` row feature (`log1p` and `asinh` variants) and Up/Dn group.
- Raw identity `ATR` не является primary candidate из-за известного regime shift; если обучается, только как diagnostic negative control и с явным A7 warning.
- A7 feature distribution audit обязателен до обучения для каждого нового Stage 5.4 profile. Если есть `ERROR`, training блокируется. Если есть `WARNING`, JSON должен содержать решение `accept_as_diagnostic`, `reject_profile` или `transform_and_rerun`.
- Gate по улучшению считается per-seed, не только по median: `delta_vs_side_baseline >= 0.02` должен пройти минимум `2/3` seed; `3/3` отмечается как strong.
- Holdout не является gate, но report должен раскрыть `holdout_drop = val_auc - holdout_auc`; drop больше `0.06` — красный флаг.
- Search budget должен быть раскрыт в JSON и отчёте; итог не может стать trading candidate без нового независимого периода.

---

## File Structure

- Modify: `ML/baseline/benchmark_stage5_transformer_breach.py`
  - Add Stage 5.4 constants, profile definitions, feature-name helper, A7 matrix audit, evaluator/summary/gate, runner and CLI fast path.
- Modify: `tests/test_stage5_transformer_breach.py`
  - Add unit/smoke tests for Stage 5.4 profiles, feature shapes, A7 audit, evaluator, gate, runner and CLI.
- Create after full run: `ML/reports/stage5_4_fast_price_atr_ablation.json`
  - Structured artifact полного Stage 5.4 прогона.
- Create after full run: `docs/reports/2026-06-29-stage5_4-fast-price-atr-ablation.md`
  - Канонический отчёт после JSON, не в этом implementation-plan.

---

## Stage 5.4 Fixed Design

### Target

Use existing Stage 5.3 target builder:

```python
STAGE5_4_TARGET_SPEC = {
    "name": "fast",
    "family": "bucket",
    "bucket": "fast",
    "role": "main",
}
```

No other target specs are allowed in Stage 5.4.

### Profiles

Evaluate both baseline families on both sides, but gate each side against its own Stage 5.3 winner baseline:

| Profile | Role | Token fields | Row fields | Transform intent |
|---|---|---|---|---|
| `clock_shift_back` | baseline | `shift`, `back` | time | existing baseline |
| `clock_shift_back_price_coord_atr` | primary | `shift`, `back`, `price_coord_atr` | time | signed distance to level |
| `clock_shift_back_price_coord_atr_price_atr_scaled` | secondary | `shift`, `back`, `price_coord_atr`, `price_atr_scaled` | time | coordinate + price/ATR control |
| `clock_shift_back_atr_log1p` | diagnostic | `shift`, `back` | time + `ATR` | volatility regime check |
| `clock_shift_back_atr_asinh` | diagnostic | `shift`, `back` | time + `ATR` | alternative tail compression |
| `clock_shift_back_updn` | diagnostic | `shift`, `back`, all Up/Dn | time | Up/Dn group control |
| `clock_shift_back_impulse` | baseline | `shift`, `back`, `impulse` | time | existing buy baseline |
| `clock_shift_back_impulse_price_coord_atr` | primary | `shift`, `back`, `impulse`, `price_coord_atr` | time | signed distance to level |
| `clock_shift_back_impulse_price_coord_atr_price_atr_scaled` | secondary | `shift`, `back`, `impulse`, `price_coord_atr`, `price_atr_scaled` | time | coordinate + price/ATR control |
| `clock_shift_back_impulse_atr_log1p` | diagnostic | `shift`, `back`, `impulse` | time + `ATR` | volatility regime check |
| `clock_shift_back_impulse_atr_asinh` | diagnostic | `shift`, `back`, `impulse` | time + `ATR` | alternative tail compression |
| `clock_shift_back_impulse_updn` | diagnostic | `shift`, `back`, `impulse`, all Up/Dn | time | Up/Dn group control |

Total run budget: `2 source targets × 1 target × 12 profiles × 3 seeds = 72` XGBoost classifications.

Primary comparisons:

- sell: `clock_shift_back_price_coord_atr` vs `clock_shift_back`;
- buy: `clock_shift_back_impulse_price_coord_atr` vs `clock_shift_back_impulse`.

Secondary/diagnostic profiles cannot promote Stage 5.4 to candidate status. They only explain what to inspect next.

---

### Task 1: Stage 5.4 Constants And Profile Contract

**Files:**
- Modify: `ML/baseline/benchmark_stage5_transformer_breach.py`
- Test: `tests/test_stage5_transformer_breach.py`

**Interfaces:**
- Produces: `STAGE5_4_JSON_REPORT_PATH: Path`
- Produces: `STAGE5_4_SOURCE_TARGETS: list[str]`
- Produces: `STAGE5_4_TARGET_SPEC: dict`
- Produces: `STAGE5_4_PROFILE_KEYS: list[str]`
- Produces: `STAGE5_4_PROFILE_ROLES: dict[str, str]`
- Produces: `STAGE5_4_SIDE_BASELINE_PROFILE: dict[str, str]`
- Produces: `_stage5_4_profile_for_key(profile_key: str) -> dict`
- Produces: `stage5_4_feature_names(profile_key: str) -> list[str]`

- [ ] **Step 1: Write failing tests for constants and profile contracts**

Append near Stage 5.3 tests in `tests/test_stage5_transformer_breach.py`:

```python
def test_stage5_4_constants_and_profiles_are_frozen():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    assert runner.STAGE5_4_SOURCE_TARGETS == [
        "sell_bars_to_breach_H6_off05",
        "buy_bars_to_breach_H6_off05",
    ]
    assert runner.STAGE5_4_TARGET_SPEC == {
        "name": "fast",
        "family": "bucket",
        "bucket": "fast",
        "role": "main",
    }
    assert runner.STAGE5_4_SIDE_BASELINE_PROFILE == {
        "sell": "clock_shift_back",
        "buy": "clock_shift_back_impulse",
    }
    assert runner.STAGE5_4_PROFILE_KEYS == [
        "clock_shift_back",
        "clock_shift_back_price_coord_atr",
        "clock_shift_back_price_coord_atr_price_atr_scaled",
        "clock_shift_back_atr_log1p",
        "clock_shift_back_atr_asinh",
        "clock_shift_back_updn",
        "clock_shift_back_impulse",
        "clock_shift_back_impulse_price_coord_atr",
        "clock_shift_back_impulse_price_coord_atr_price_atr_scaled",
        "clock_shift_back_impulse_atr_log1p",
        "clock_shift_back_impulse_atr_asinh",
        "clock_shift_back_impulse_updn",
    ]
    assert runner.STAGE5_4_PROFILE_ROLES["clock_shift_back_price_coord_atr"] == "primary"
    assert runner.STAGE5_4_PROFILE_ROLES["clock_shift_back_atr_log1p"] == "diagnostic"
    assert str(runner.STAGE5_4_JSON_REPORT_PATH).endswith(
        "stage5_4_fast_price_atr_ablation.json"
    )


def test_stage5_4_profile_for_key_and_feature_names():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    profile = runner._stage5_4_profile_for_key("clock_shift_back_price_coord_atr")
    assert profile["token_fields"] == ["shift", "back", "price_coord_atr"]
    assert profile["row_fields"] == runner.TIME_ONLY_ROW_FIELDS
    assert profile["price_coord_atr_transform"] == "signed_log1p"

    names = runner.stage5_4_feature_names("clock_shift_back_price_coord_atr")
    assert names[0] == "fractal0.shift"
    assert names[1] == "fractal0.back"
    assert names[2] == "fractal0.price_coord_atr"
    assert names[-4:] == ["hour_sin", "hour_cos", "dow_sin", "dow_cos"]
    assert len(names) == 3 * runner.N_FRACTALS + 4

    atr_profile = runner._stage5_4_profile_for_key("clock_shift_back_atr_asinh")
    assert atr_profile["row_fields"] == runner.TIME_ONLY_ROW_FIELDS + ["ATR"]
    assert atr_profile["atr_transform"] == "asinh"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_stage5_4_constants_and_profiles_are_frozen tests/test_stage5_transformer_breach.py::test_stage5_4_profile_for_key_and_feature_names -q
```

Expected: FAIL because Stage 5.4 constants/functions do not exist.

- [ ] **Step 3: Add constants and profile contract**

Add after Stage 5.3 constants in `ML/baseline/benchmark_stage5_transformer_breach.py`:

```python
STAGE5_4_JSON_REPORT_PATH = REPORTS_DIR / "stage5_4_fast_price_atr_ablation.json"
STAGE5_4_SOURCE_TARGETS = STAGE5_3_SOURCE_TARGETS.copy()
STAGE5_4_TARGET_SPEC = {
    "name": "fast",
    "family": "bucket",
    "bucket": "fast",
    "role": "main",
}
STAGE5_4_SEEDS = STAGE5_3_SEEDS.copy()
STAGE5_4_PROFILE_KEYS = [
    "clock_shift_back",
    "clock_shift_back_price_coord_atr",
    "clock_shift_back_price_coord_atr_price_atr_scaled",
    "clock_shift_back_atr_log1p",
    "clock_shift_back_atr_asinh",
    "clock_shift_back_updn",
    "clock_shift_back_impulse",
    "clock_shift_back_impulse_price_coord_atr",
    "clock_shift_back_impulse_price_coord_atr_price_atr_scaled",
    "clock_shift_back_impulse_atr_log1p",
    "clock_shift_back_impulse_atr_asinh",
    "clock_shift_back_impulse_updn",
]
STAGE5_4_PROFILE_ROLES = {
    "clock_shift_back": "baseline",
    "clock_shift_back_price_coord_atr": "primary",
    "clock_shift_back_price_coord_atr_price_atr_scaled": "secondary",
    "clock_shift_back_atr_log1p": "diagnostic",
    "clock_shift_back_atr_asinh": "diagnostic",
    "clock_shift_back_updn": "diagnostic",
    "clock_shift_back_impulse": "baseline",
    "clock_shift_back_impulse_price_coord_atr": "primary",
    "clock_shift_back_impulse_price_coord_atr_price_atr_scaled": "secondary",
    "clock_shift_back_impulse_atr_log1p": "diagnostic",
    "clock_shift_back_impulse_atr_asinh": "diagnostic",
    "clock_shift_back_impulse_updn": "diagnostic",
}
STAGE5_4_SIDE_BASELINE_PROFILE = {
    "sell": "clock_shift_back",
    "buy": "clock_shift_back_impulse",
}
STAGE5_4_SIDE_PRIMARY_PROFILE = {
    "sell": "clock_shift_back_price_coord_atr",
    "buy": "clock_shift_back_impulse_price_coord_atr",
}
```

Add near `_stage5_2_profile_for_key()`:

```python
def _stage5_4_profile_for_key(profile_key: str) -> dict:
    if profile_key.startswith("clock_shift_back_impulse"):
        token_fields = ["shift", "back", "impulse"]
        suffix = profile_key.removeprefix("clock_shift_back_impulse")
    elif profile_key.startswith("clock_shift_back"):
        token_fields = ["shift", "back"]
        suffix = profile_key.removeprefix("clock_shift_back")
    else:
        raise ValueError(f"Unknown Stage 5.4 profile: {profile_key}")

    row_fields = TIME_ONLY_ROW_FIELDS.copy()
    atr_transform = None
    price_coord_atr_transform = None
    price_atr_scaled_transform = None

    if suffix == "":
        pass
    elif suffix == "_price_coord_atr":
        token_fields = token_fields + ["price_coord_atr"]
        price_coord_atr_transform = "signed_log1p"
    elif suffix == "_price_coord_atr_price_atr_scaled":
        token_fields = token_fields + ["price_coord_atr", "price_atr_scaled"]
        price_coord_atr_transform = "signed_log1p"
        price_atr_scaled_transform = "asinh"
    elif suffix == "_atr_log1p":
        row_fields = row_fields + ["ATR"]
        atr_transform = "log1p"
    elif suffix == "_atr_asinh":
        row_fields = row_fields + ["ATR"]
        atr_transform = "asinh"
    elif suffix == "_updn":
        token_fields = token_fields + STAGE5_1B_UPDN_FIELDS.copy()
    else:
        raise ValueError(f"Unknown Stage 5.4 profile: {profile_key}")

    return {
        "name": f"stage5_4_{profile_key}",
        "token_fields": token_fields,
        "row_fields": row_fields,
        "order": "freshness",
        "stage5_4": True,
        "role": STAGE5_4_PROFILE_ROLES[profile_key],
        "atr_transform": atr_transform,
        "price_coord_atr_transform": price_coord_atr_transform,
        "price_atr_scaled_transform": price_atr_scaled_transform,
    }


def stage5_4_feature_names(profile_key: str) -> list[str]:
    profile = _stage5_4_profile_for_key(profile_key)
    names = []
    for fractal_idx in range(N_FRACTALS):
        for field in profile["token_fields"]:
            names.append(f"fractal{fractal_idx}.{field}")
    names.extend(profile["row_fields"])
    return names
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_stage5_4_constants_and_profiles_are_frozen tests/test_stage5_transformer_breach.py::test_stage5_4_profile_for_key_and_feature_names -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add ML/baseline/benchmark_stage5_transformer_breach.py tests/test_stage5_transformer_breach.py
git commit -m "feat: add stage 5.4 profile contract"
```

---

### Task 2: Stage 5.4 Feature Builder Extensions

**Files:**
- Modify: `ML/baseline/benchmark_stage5_transformer_breach.py`
- Test: `tests/test_stage5_transformer_breach.py`

**Interfaces:**
- Consumes: `_stage5_4_profile_for_key(profile_key: str) -> dict`
- Produces: `build_stage5_4_features(df: pd.DataFrame, profile_key: str) -> np.ndarray`
- Produces: `_stage5_4_row_features(df: pd.DataFrame, profile: dict) -> np.ndarray`

- [ ] **Step 1: Write failing tests for feature shapes and transforms**

Append:

```python
def test_build_stage5_4_features_shapes_and_price_transforms():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    df = _make_stage5_0f_year_df().head(3).copy()
    df["ATR"] = [2.0, 4.0, 8.0]

    # Override first row to make expected price_coord deterministic:
    # fractal0 price=100, fractal1 price=104, ATR=2 => raw coord=2.
    parts0 = str(df.loc[df.index[0], "fractal0"]).split(runner.FRACTAL_SEP)
    parts1 = str(df.loc[df.index[0], "fractal1"]).split(runner.FRACTAL_SEP)
    parts0[1] = "100.0"
    parts1[1] = "104.0"
    df.loc[df.index[0], "fractal0"] = runner.FRACTAL_SEP.join(parts0)
    df.loc[df.index[0], "fractal1"] = runner.FRACTAL_SEP.join(parts1)

    X_base = runner.build_stage5_4_features(df, "clock_shift_back")
    X_coord = runner.build_stage5_4_features(df, "clock_shift_back_price_coord_atr")
    X_both = runner.build_stage5_4_features(
        df, "clock_shift_back_price_coord_atr_price_atr_scaled"
    )
    X_atr = runner.build_stage5_4_features(df, "clock_shift_back_atr_log1p")
    X_updn = runner.build_stage5_4_features(df, "clock_shift_back_updn")

    assert X_base.shape == (3, 2 * runner.N_FRACTALS + 4)
    assert X_coord.shape == (3, 3 * runner.N_FRACTALS + 4)
    assert X_both.shape == (3, 4 * runner.N_FRACTALS + 4)
    assert X_atr.shape == (3, 2 * runner.N_FRACTALS + 5)
    assert X_updn.shape == (3, (2 + len(runner.STAGE5_1B_UPDN_FIELDS)) * runner.N_FRACTALS + 4)

    names = runner.stage5_4_feature_names("clock_shift_back_price_coord_atr")
    coord_idx = names.index("fractal1.price_coord_atr")
    assert np.isclose(X_coord[0, coord_idx], np.sign(2.0) * np.log1p(abs(2.0)))

    atr_names = runner.stage5_4_feature_names("clock_shift_back_atr_log1p")
    assert atr_names[-1] == "ATR"
    assert np.isclose(X_atr[0, -1], np.log1p(2.0))


def test_stage5_4_feature_builder_rejects_unknown_profile():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    df = _make_stage5_0f_year_df().head(2)
    with pytest.raises(ValueError, match="Unknown Stage 5.4 profile"):
        runner.build_stage5_4_features(df, "clock_shift_back_raw_price")
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_build_stage5_4_features_shapes_and_price_transforms tests/test_stage5_transformer_breach.py::test_stage5_4_feature_builder_rejects_unknown_profile -q
```

Expected: FAIL because `build_stage5_4_features()` does not exist.

- [ ] **Step 3: Implement Stage 5.4 row and flat feature builders**

Add near `build_stage5_2_features()`:

```python
def _stage5_4_row_features(df: pd.DataFrame, profile: dict) -> np.ndarray:
    row_fields = profile["row_fields"]
    base_profile = {"row_fields": [f for f in row_fields if f != "ATR"]}
    base = build_row_features(df, base_profile).astype(np.float32)
    if "ATR" not in row_fields:
        return base

    atr_raw = pd.to_numeric(df["ATR"], errors="coerce").fillna(0.0).clip(lower=0.0).to_numpy(dtype=np.float32)
    method = profile.get("atr_transform") or "log1p"
    if method == "log1p":
        atr_col = np.log1p(atr_raw).astype(np.float32)
    elif method == "asinh":
        atr_col = np.arcsinh(atr_raw).astype(np.float32)
    elif method == "identity":
        atr_col = atr_raw.astype(np.float32)
    else:
        raise ValueError(f"Unknown Stage 5.4 ATR transform: {method}")
    return np.column_stack([base, atr_col]).astype(np.float32)


def build_stage5_4_features(df: pd.DataFrame, profile_key: str) -> np.ndarray:
    profile = _stage5_4_profile_for_key(profile_key)
    token_fields = profile["token_fields"]
    row_fields = profile["row_fields"]
    n_rows = len(df)
    token_width = len(token_fields) * N_FRACTALS
    X = np.zeros((n_rows, token_width + len(row_fields)), dtype=np.float32)
    field_indices = {
        field: STAGE5_1B_FIELD_TO_FRACTAL_INDEX.get(field)
        for field in token_fields
        if field not in {"price_coord_atr", "price_atr_scaled"}
    }

    for row_idx, (_, row) in enumerate(df.iterrows()):
        atr = pd.to_numeric(row.get("ATR", 0.0), errors="coerce")
        safe_atr = max(float(atr) if not pd.isna(atr) else 0.0, 0.001)
        f0_parts = str(row.get("fractal0", "")).split(FRACTAL_SEP)
        try:
            f0_price = float(f0_parts[1])
        except (ValueError, IndexError):
            f0_price = 0.0

        offset = 0
        for fractal_idx in range(N_FRACTALS):
            parts = str(row.get(f"fractal{fractal_idx}", "")).split(FRACTAL_SEP)
            try:
                price = float(parts[1])
            except (ValueError, IndexError):
                price = 0.0
            for field in token_fields:
                if field == "price_coord_atr":
                    raw_coord = (price - f0_price) / safe_atr
                    value = float(_signed_log1p(np.asarray([raw_coord], dtype=np.float32))[0])
                elif field == "price_atr_scaled":
                    value = float(np.arcsinh(price / safe_atr))
                else:
                    idx = field_indices[field]
                    try:
                        value = float(parts[idx])
                    except (ValueError, IndexError, TypeError):
                        value = 0.0
                    value = float(np.nan_to_num(value, nan=0.0))
                    if field == "shift":
                        value = float(np.log1p(max(value, 0.0)))
                X[row_idx, offset] = value
                offset += 1

    row_features = _stage5_4_row_features(df, profile).astype(np.float32)
    if row_features.shape[1] != len(row_fields):
        raise RuntimeError(
            f"Stage 5.4 row feature width mismatch: got {row_features.shape[1]}, expected {len(row_fields)}"
        )
    X[:, token_width:] = row_features
    return X
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_build_stage5_4_features_shapes_and_price_transforms tests/test_stage5_transformer_breach.py::test_stage5_4_feature_builder_rejects_unknown_profile -q
```

Expected: PASS.

- [ ] **Step 5: Regression-check old Stage 5.2/5.3 feature tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py -q -k "build_stage5_2_features or stage5_3"
```

Expected: PASS. This protects closed stages from accidental feature-builder drift.

- [ ] **Step 6: Commit**

```bash
git add ML/baseline/benchmark_stage5_transformer_breach.py tests/test_stage5_transformer_breach.py
git commit -m "feat: build stage 5.4 price atr features"
```

---

### Task 3: A7 Matrix Audit Before Training

**Files:**
- Modify: `ML/baseline/benchmark_stage5_transformer_breach.py`
- Test: `tests/test_stage5_transformer_breach.py`

**Interfaces:**
- Consumes: `build_stage5_4_features(df, profile_key) -> np.ndarray`
- Consumes: `stage5_4_feature_names(profile_key) -> list[str]`
- Produces: `stage5_4_feature_distribution_audit(feature_split: dict, profile_key: str) -> dict`
- Produces: `_stage5_4_audit_feature_matrix(X: np.ndarray, feature_names: list[str]) -> dict`

- [ ] **Step 1: Write failing tests for A7 audit flags and pass case**

Append:

```python
def test_stage5_4_feature_distribution_audit_flags_nan_inf_and_tail():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    feature_split = {
        "train_core": np.array([[0.0, 1.0], [np.nan, 2.0]], dtype=np.float32),
        "val_stop": np.array([[0.0, np.inf]], dtype=np.float32),
        "diagnostic_holdout": np.array([[0.0, 100.0]], dtype=np.float32),
        "low_n_disclosure": np.array([[0.0, 1.0]], dtype=np.float32),
    }
    audit = runner.stage5_4_feature_distribution_audit(
        feature_split,
        "clock_shift_back",
        feature_names=["f0", "f1"],
    )

    assert audit["status"] == "ERROR"
    assert "NaN_OR_INF" in audit["flags"]
    assert "TAIL_GT20" in audit["flags"]
    assert audit["decisions"]["NaN_OR_INF"] == "block_training"


def test_stage5_4_feature_distribution_audit_passes_small_clean_matrix():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    feature_split = {
        "train_core": np.array([[0.0, 1.0], [0.2, 2.0], [0.3, 3.0]], dtype=np.float32),
        "val_stop": np.array([[0.1, 1.5], [0.2, 2.5]], dtype=np.float32),
        "diagnostic_holdout": np.array([[0.1, 1.2], [0.2, 2.2]], dtype=np.float32),
        "low_n_disclosure": np.array([[0.1, 1.1]], dtype=np.float32),
    }
    audit = runner.stage5_4_feature_distribution_audit(
        feature_split,
        "clock_shift_back",
        feature_names=["f0", "f1"],
    )

    assert audit["status"] == "PASS"
    assert audit["flags"] == []
    assert audit["by_split"]["train_core"]["f1"]["p95"] > 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_stage5_4_feature_distribution_audit_flags_nan_inf_and_tail tests/test_stage5_transformer_breach.py::test_stage5_4_feature_distribution_audit_passes_small_clean_matrix -q
```

Expected: FAIL because audit helpers do not exist.

- [ ] **Step 3: Implement compact A7 audit for final matrices**

Add near Stage 5.3 feature helpers:

```python
def _stage5_4_feature_stats(values: np.ndarray) -> dict:
    arr = np.asarray(values, dtype=np.float64)
    finite = arr[np.isfinite(arr)]
    if len(finite) == 0:
        return {
            "n_valid": 0,
            "missing_or_inf_count": int(len(arr)),
            "min": None,
            "p1": None,
            "p5": None,
            "p25": None,
            "p50": None,
            "p75": None,
            "p95": None,
            "p99": None,
            "max": None,
            "mean": None,
            "std": None,
            "frac_abs_gt10": None,
            "frac_abs_gt20": None,
            "zero_rate": None,
            "unique_rounded_6": 0,
        }
    p1, p5, p25, p50, p75, p95, p99 = np.percentile(finite, [1, 5, 25, 50, 75, 95, 99])
    return {
        "n_valid": int(len(finite)),
        "missing_or_inf_count": int(len(arr) - len(finite)),
        "min": float(np.min(finite)),
        "p1": float(p1),
        "p5": float(p5),
        "p25": float(p25),
        "p50": float(p50),
        "p75": float(p75),
        "p95": float(p95),
        "p99": float(p99),
        "max": float(np.max(finite)),
        "mean": float(np.mean(finite)),
        "std": float(np.std(finite)),
        "frac_abs_gt10": float(np.mean(np.abs(finite) > 10.0)),
        "frac_abs_gt20": float(np.mean(np.abs(finite) > 20.0)),
        "zero_rate": float(np.mean(finite == 0.0)),
        "unique_rounded_6": int(len(np.unique(np.round(finite, 6)))),
    }


def _stage5_4_audit_feature_matrix(X: np.ndarray, feature_names: list[str]) -> dict:
    arr = np.asarray(X, dtype=np.float32)
    if arr.ndim != 2:
        raise ValueError(f"Stage 5.4 audit expects 2D matrix, got shape={arr.shape}")
    if arr.shape[1] != len(feature_names):
        raise ValueError(
            f"Stage 5.4 feature name mismatch: matrix_width={arr.shape[1]} names={len(feature_names)}"
        )
    return {
        name: _stage5_4_feature_stats(arr[:, idx])
        for idx, name in enumerate(feature_names)
    }


def stage5_4_feature_distribution_audit(feature_split: dict, profile_key: str,
                                        feature_names: list[str] | None = None) -> dict:
    names = feature_names or stage5_4_feature_names(profile_key)
    by_split = {
        split_name: _stage5_4_audit_feature_matrix(X, names)
        for split_name, X in feature_split.items()
        if X is not None
    }
    flags = []
    for split_stats in by_split.values():
        for stats in split_stats.values():
            if stats["missing_or_inf_count"] > 0:
                flags.append("NaN_OR_INF")
            if (stats["frac_abs_gt20"] or 0.0) > 0.0:
                flags.append("TAIL_GT20")
            if (stats["frac_abs_gt10"] or 0.0) > 0.01:
                flags.append("TAIL_GT10")
            if stats["zero_rate"] is not None and stats["zero_rate"] > 0.95:
                flags.append("ZERO_GT95")

    train = by_split.get("train_core", {})
    hold = by_split.get("diagnostic_holdout", {})
    for name, train_stats in train.items():
        hold_stats = hold.get(name)
        if not hold_stats:
            continue
        train_std = train_stats.get("std") or 0.0
        if train_std > 1e-8 and train_stats.get("p95") is not None and hold_stats.get("p95") is not None:
            if abs(hold_stats["p95"] - train_stats["p95"]) > 3.0 * train_std:
                flags.append("REGIME_SHIFT")

    flags = sorted(set(flags))
    status = "ERROR" if "NaN_OR_INF" in flags else ("WARNING" if flags else "PASS")
    decisions = {}
    for flag in flags:
        if flag == "NaN_OR_INF":
            decisions[flag] = "block_training"
        elif flag in {"TAIL_GT20", "TAIL_GT10", "ZERO_GT95", "REGIME_SHIFT"}:
            decisions[flag] = "accept_as_diagnostic"
    return {
        "profile": profile_key,
        "status": status,
        "flags": flags,
        "decisions": decisions,
        "by_split": by_split,
        "thresholds": {
            "tail_gt10_warn_fraction": 0.01,
            "tail_gt20_warn_any": True,
            "regime_shift_p95_delta_train_std": 3.0,
        },
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_stage5_4_feature_distribution_audit_flags_nan_inf_and_tail tests/test_stage5_transformer_breach.py::test_stage5_4_feature_distribution_audit_passes_small_clean_matrix -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add ML/baseline/benchmark_stage5_transformer_breach.py tests/test_stage5_transformer_breach.py
git commit -m "feat: add stage 5.4 feature audit"
```

---

### Task 4: Stage 5.4 Evaluator, Summary, Gate

**Files:**
- Modify: `ML/baseline/benchmark_stage5_transformer_breach.py`
- Test: `tests/test_stage5_transformer_breach.py`

**Interfaces:**
- Consumes: `stage5_3_make_binary_target_from_frame(...)`
- Consumes: `stage5_3_binary_metrics(...)`
- Consumes: `build_stage5_4_features(...)`
- Produces: `_build_stage5_4_feature_split(split: dict, profile_key: str) -> dict`
- Produces: `evaluate_stage5_4_profile_seed(split, source_target, profile_key, seed, xgb_threads=1, feature_split=None) -> dict`
- Produces: `summarize_stage5_4_source(raw_runs: list[dict], source_target: str) -> dict`
- Produces: `stage5_4_gate_results(summary: dict, source_target: str) -> dict`

- [ ] **Step 1: Write failing evaluator and gate tests**

Append:

```python
def test_evaluate_stage5_4_profile_seed_returns_fast_metrics(monkeypatch):
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    df = _make_stage5_0f_year_df().copy()
    df["sell_bars_to_breach_H6_off05"] = np.where(np.arange(len(df)) % 3 == 0, 1, 7)
    split = runner.build_stage5_1_split(df, "sell_bars_to_breach_H6_off05")

    result = runner.evaluate_stage5_4_profile_seed(
        split,
        "sell_bars_to_breach_H6_off05",
        "clock_shift_back",
        seed=42,
        xgb_threads=1,
    )

    assert result["stage"] == "5.4"
    assert result["target_id"] == "sell_fast"
    assert result["profile"] == "clock_shift_back"
    assert result["profile_role"] == "baseline"
    assert result["val_stop"]["auc"] is not None
    assert result["yearly_val"]
    assert "feature_importance_gain_top20" in result


def test_stage5_4_gate_uses_per_seed_threshold_not_median_only():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    summary = {
        "side": "buy",
        "side_baseline_profile": "clock_shift_back_impulse",
        "side_primary_profile": "clock_shift_back_impulse_price_coord_atr",
        "profiles": {
            "clock_shift_back_impulse": {"val_stop": {"auc": 0.6900}},
            "clock_shift_back_impulse_price_coord_atr": {
                "profile": "clock_shift_back_impulse_price_coord_atr",
                "profile_role": "primary",
                "val_stop": {"auc": 0.7101, "yearly": {"2021": {"auc": 0.70}, "2022": {"auc": 0.71}}},
                "diagnostic_holdout": {"auc": 0.6600},
                "delta_vs_side_baseline": {
                    "median_auc_delta": 0.0201,
                    "per_seed": [
                        {"seed": 42, "auc_delta": 0.0210, "passes_0_02": True},
                        {"seed": 77, "auc_delta": 0.0190, "passes_0_02": False},
                        {"seed": 123, "auc_delta": 0.0180, "passes_0_02": False},
                    ],
                    "pass_count_ge_0_02": 1,
                    "n_seeds": 3,
                },
            },
        },
        "best_primary": {
            "profile": "clock_shift_back_impulse_price_coord_atr",
            "profile_role": "primary",
            "val_stop": {"auc": 0.7101, "yearly": {"2021": {"auc": 0.70}, "2022": {"auc": 0.71}}},
            "diagnostic_holdout": {"auc": 0.6600},
            "delta_vs_side_baseline": {
                "median_auc_delta": 0.0201,
                "pass_count_ge_0_02": 1,
                "n_seeds": 3,
            },
        },
    }

    gate = runner.stage5_4_gate_results(summary, "buy_bars_to_breach_H6_off05")
    checks = gate["model_gate"]["checks"]
    assert checks["per_seed_delta_ge_0_02_at_least_2_of_3"] is False
    assert gate["overall_status"] == "DIAGNOSTIC_ONLY"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_evaluate_stage5_4_profile_seed_returns_fast_metrics tests/test_stage5_transformer_breach.py::test_stage5_4_gate_uses_per_seed_threshold_not_median_only -q
```

Expected: FAIL because evaluator/gate do not exist.

- [ ] **Step 3: Implement evaluator, summary and gate**

Add near Stage 5.3 evaluator:

```python
def _build_stage5_4_feature_split(split: dict, profile_key: str) -> dict:
    return {
        "train_core": build_stage5_4_features(split["train_core"], profile_key),
        "val_stop": build_stage5_4_features(split["val_stop"], profile_key),
        "diagnostic_holdout": build_stage5_4_features(split["diagnostic_holdout"], profile_key),
        "low_n_disclosure": (
            build_stage5_4_features(split["low_n_disclosure"], profile_key)
            if len(split["low_n_disclosure"]) else None
        ),
    }


def evaluate_stage5_4_profile_seed(split: dict, source_target: str, profile_key: str,
                                   seed: int, xgb_threads: int = 1,
                                   feature_split: dict | None = None) -> dict:
    started_at = time.time()
    train = split["train_core"]
    val = split["val_stop"]
    holdout = split["diagnostic_holdout"]
    low_n = split["low_n_disclosure"]
    if feature_split is None:
        feature_split = _build_stage5_4_feature_split(split, profile_key)

    X_train = feature_split["train_core"]
    X_val = feature_split["val_stop"]
    X_holdout = feature_split["diagnostic_holdout"]
    X_low_n = feature_split["low_n_disclosure"]

    y_train = stage5_3_make_binary_target_from_frame(train, source_target, STAGE5_4_TARGET_SPEC)
    train_valid = y_train >= 0
    X_train = X_train[train_valid]
    y_train = y_train[train_valid]
    positives = int(y_train.sum())
    negatives = int(len(y_train) - positives)
    scale_pos_weight = float(negatives / max(positives, 1))

    y_val = stage5_3_make_binary_target_from_frame(val, source_target, STAGE5_4_TARGET_SPEC)
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
    y_holdout = stage5_3_make_binary_target_from_frame(holdout, source_target, STAGE5_4_TARGET_SPEC)
    y_low_n = stage5_3_make_binary_target_from_frame(low_n, source_target, STAGE5_4_TARGET_SPEC) if len(low_n) else np.asarray([])

    return {
        "stage": "5.4",
        "source_target": source_target,
        "target_id": stage5_3_target_id(source_target, STAGE5_4_TARGET_SPEC),
        "spec": dict(STAGE5_4_TARGET_SPEC),
        "profile": profile_key,
        "profile_role": STAGE5_4_PROFILE_ROLES[profile_key],
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
        "yearly_val": _stage5_3_yearly_metrics(val, source_target, STAGE5_4_TARGET_SPEC, val_score),
        "yearly_diagnostic_holdout": _stage5_3_yearly_metrics(holdout, source_target, STAGE5_4_TARGET_SPEC, holdout_score),
        "feature_importance_gain_top20": _stage5_3_feature_importance_top20(model),
    }
```

Add summary/gate:

```python
def summarize_stage5_4_source(raw_runs: list[dict], source_target: str) -> dict:
    side = "sell" if source_target.startswith("sell_") else "buy"
    source_runs = [r for r in raw_runs if r.get("source_target") == source_target]
    profiles = {}
    for profile in STAGE5_4_PROFILE_KEYS:
        runs = [r for r in source_runs if r.get("profile") == profile]
        if not runs:
            continue
        row = _stage5_3_profile_summary(runs)
        row["profile"] = profile
        row["profile_role"] = STAGE5_4_PROFILE_ROLES[profile]
        profiles[profile] = row

    baseline_profile = STAGE5_4_SIDE_BASELINE_PROFILE[side]
    baseline_runs = [r for r in source_runs if r.get("profile") == baseline_profile]
    baseline_by_seed = {
        int(r["seed"]): ((r.get("val_stop") or {}).get("auc"))
        for r in baseline_runs
    }
    baseline_auc = ((profiles.get(baseline_profile) or {}).get("val_stop") or {}).get("auc")
    for profile, row in profiles.items():
        auc = (row.get("val_stop") or {}).get("auc")
        per_seed = []
        for run in [r for r in source_runs if r.get("profile") == profile]:
            seed = int(run["seed"])
            run_auc = ((run.get("val_stop") or {}).get("auc"))
            base_auc = baseline_by_seed.get(seed)
            delta = None if run_auc is None or base_auc is None else run_auc - base_auc
            per_seed.append({
                "seed": seed,
                "auc": run_auc,
                "baseline_auc": base_auc,
                "auc_delta": delta,
                "passes_0_02": bool(delta is not None and delta >= 0.02),
            })
        pass_count = sum(1 for item in per_seed if item["passes_0_02"])
        row["delta_vs_side_baseline"] = {
            "baseline_profile": baseline_profile,
            "baseline_val_auc": baseline_auc,
            "median_auc_delta": None if auc is None or baseline_auc is None else auc - baseline_auc,
            "per_seed": sorted(per_seed, key=lambda item: item["seed"]),
            "pass_count_ge_0_02": int(pass_count),
            "n_seeds": len(per_seed),
        }
        hold_auc = (row.get("diagnostic_holdout") or {}).get("auc")
        row["holdout_drop"] = None if auc is None or hold_auc is None else auc - hold_auc

    primary_profiles = [
        row for row in profiles.values()
        if row.get("profile_role") == "primary"
    ]
    best_primary = max(
        primary_profiles,
        key=lambda row: (row.get("val_stop") or {}).get("auc") or -999.0,
        default={},
    )
    return {
        "source_target": source_target,
        "side": side,
        "target": "fast",
        "side_baseline_profile": baseline_profile,
        "side_primary_profile": STAGE5_4_SIDE_PRIMARY_PROFILE[side],
        "profiles": profiles,
        "best_primary": best_primary,
    }


def stage5_4_gate_results(summary: dict, source_target: str) -> dict:
    best = summary.get("best_primary") or {}
    val = best.get("val_stop") or {}
    yearly = val.get("yearly") or {}
    delta = best.get("delta_vs_side_baseline") or {}
    yearly_pass = (
        len(yearly) >= 2
        and sum(1 for row in yearly.values() if (row.get("auc") or 0.0) >= 0.60) >= 2
    )
    checks = {
        "target_is_fast": summary.get("target") == "fast",
        "best_profile_is_primary": best.get("profile_role") == "primary",
        "auc_ge_0_65": (val.get("auc") or 0.0) >= 0.65,
        "median_delta_vs_side_baseline_ge_0_02": (delta.get("median_auc_delta") or 0.0) >= 0.02,
        "per_seed_delta_ge_0_02_at_least_2_of_3": (delta.get("pass_count_ge_0_02") or 0) >= 2,
        "yearly_not_single_year": yearly_pass,
    }
    passed = all(checks.values())
    return {
        "overall_status": "PRICE_ATR_SIGNAL_FOUND" if passed else "DIAGNOSTIC_ONLY",
        "model_gate": {
            "pass": bool(passed),
            "checks": checks,
            "holdout_drop_warning": bool((best.get("holdout_drop") or 0.0) > 0.06),
            "note": "Stage 5.4 is diagnostic; holdout is disclosure only and cannot promote candidate status.",
        },
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_evaluate_stage5_4_profile_seed_returns_fast_metrics tests/test_stage5_transformer_breach.py::test_stage5_4_gate_uses_per_seed_threshold_not_median_only -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add ML/baseline/benchmark_stage5_transformer_breach.py tests/test_stage5_transformer_breach.py
git commit -m "feat: evaluate stage 5.4 fast ablation"
```

---

### Task 5: Stage 5.4 Runner, CLI, And JSON Artifact

**Files:**
- Modify: `ML/baseline/benchmark_stage5_transformer_breach.py`
- Test: `tests/test_stage5_transformer_breach.py`

**Interfaces:**
- Consumes: `run_stage5_3_target_reformulation(...)` patterns
- Produces: `run_stage5_4_fast_price_atr_ablation(target_splits: dict, output_path: Path = STAGE5_4_JSON_REPORT_PATH, workers: int = 1, xgb_threads: int = 1) -> dict`
- Produces CLI flags: `--stage5-4-fast-price-atr-ablation`, `--stage5-4-workers`, `--stage5-4-xgb-threads`

- [ ] **Step 1: Write failing runner and CLI tests**

Append:

```python
def test_stage5_4_runner_writes_json(monkeypatch, tmp_path):
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    df = _make_stage5_0f_year_df().copy()
    df["sell_bars_to_breach_H6_off05"] = np.where(np.arange(len(df)) % 3 == 0, 1, 7)
    df["buy_bars_to_breach_H6_off05"] = np.where(np.arange(len(df)) % 4 == 0, 2, 7)
    monkeypatch.setattr(runner, "STAGE5_4_PROFILE_KEYS", ["clock_shift_back"])
    monkeypatch.setattr(runner, "STAGE5_4_SEEDS", [42])

    report = runner.run_stage5_4_fast_price_atr_ablation(
        {"sell": (df, df, df), "buy": (df, df, df)},
        output_path=tmp_path / "stage5_4.json",
        workers=1,
        xgb_threads=1,
    )

    assert report["stage"] == "5.4_fast_price_atr_ablation"
    assert report["progress"]["done_runs"] == 2
    assert report["progress"]["total_runs"] == 2
    assert "feature_distribution_audit" in report
    assert (tmp_path / "stage5_4.json").exists()


def test_stage5_4_cli_arguments_exist_in_build_arg_parser():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    parser = runner.build_arg_parser()
    args = parser.parse_args([
        "--stage5-4-fast-price-atr-ablation",
        "--stage5-4-workers", "8",
        "--stage5-4-xgb-threads", "4",
    ])

    assert args.stage5_4_fast_price_atr_ablation is True
    assert args.stage5_4_workers == 8
    assert args.stage5_4_xgb_threads == 4
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_stage5_4_runner_writes_json tests/test_stage5_transformer_breach.py::test_stage5_4_cli_arguments_exist_in_build_arg_parser -q
```

Expected: FAIL because runner/CLI do not exist.

- [ ] **Step 3: Implement runner with pre-training A7 audit**

Add worker globals/functions by copying Stage 5.3 pattern with Stage 5.4 names:

```python
_STAGE5_4_WORKER_SPLITS = None
_STAGE5_4_WORKER_FEATURES = None


def _init_stage5_4_worker(splits_by_source: dict, features_by_source_profile: dict) -> None:
    global _STAGE5_4_WORKER_SPLITS, _STAGE5_4_WORKER_FEATURES
    _STAGE5_4_WORKER_SPLITS = splits_by_source
    _STAGE5_4_WORKER_FEATURES = features_by_source_profile


def _run_stage5_4_job(job: dict) -> dict:
    split = job.get("split")
    feature_split = job.get("feature_split")
    if split is None:
        split = _STAGE5_4_WORKER_SPLITS[job["source_target"]]
    if feature_split is None and _STAGE5_4_WORKER_FEATURES is not None:
        feature_split = _STAGE5_4_WORKER_FEATURES[job["source_target"]][job["profile"]]
    return evaluate_stage5_4_profile_seed(
        split,
        job["source_target"],
        job["profile"],
        int(job["seed"]),
        xgb_threads=int(job.get("xgb_threads", 1)),
        feature_split=feature_split,
    )
```

Add runner:

```python
def run_stage5_4_fast_price_atr_ablation(target_splits: dict,
                                         output_path: Path = STAGE5_4_JSON_REPORT_PATH,
                                         workers: int = 1,
                                         xgb_threads: int = 1) -> dict:
    started_at = time.time()
    total_runs = len(STAGE5_4_SOURCE_TARGETS) * len(STAGE5_4_PROFILE_KEYS) * len(STAGE5_4_SEEDS)
    report = {
        "stage": "5.4_fast_price_atr_ablation",
        "status": "RUNNING",
        "level": "diagnostic_only",
        "source_targets": STAGE5_4_SOURCE_TARGETS,
        "target_spec": dict(STAGE5_4_TARGET_SPEC),
        "profiles": STAGE5_4_PROFILE_KEYS,
        "profile_roles": STAGE5_4_PROFILE_ROLES,
        "side_baseline_profile": STAGE5_4_SIDE_BASELINE_PROFILE,
        "side_primary_profile": STAGE5_4_SIDE_PRIMARY_PROFILE,
        "seeds": STAGE5_4_SEEDS,
        "feature_distribution_audit": {},
        "raw_runs": [],
        "summary": {},
        "gate_results": {},
        "notes": {
            "target_fixed": "fast only; no target search in Stage 5.4",
            "sell_primary": "sell passed Stage 5.3 target-reformulation gate",
            "buy_borderline": "buy passed delta >= 0.02 in only 1/3 seed in Stage 5.3",
            "raw_atr": "not a primary candidate; ATR profiles are diagnostic because ATR has known regime shift",
            "updn": "diagnostic group only, not included by default",
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
    features_by_source_profile = {}
    for source_target in STAGE5_4_SOURCE_TARGETS:
        split = build_stage5_1_split(combined_by_name[source_target], source_target)
        splits_by_source[source_target] = split
        features_by_source_profile[source_target] = {}
        report["feature_distribution_audit"][source_target] = {}
        for profile in STAGE5_4_PROFILE_KEYS:
            feature_split = _build_stage5_4_feature_split(split, profile)
            audit = stage5_4_feature_distribution_audit(feature_split, profile)
            report["feature_distribution_audit"][source_target][profile] = audit
            if audit["status"] == "ERROR":
                report["status"] = "PREFLIGHT_FAILED"
                report["progress"]["finished_at_unix"] = time.time()
                report["progress"]["elapsed_sec"] = round(report["progress"]["finished_at_unix"] - started_at, 3)
                _write_json_atomic(output_path, report)
                return report
            features_by_source_profile[source_target][profile] = feature_split
            report["progress"]["updated_at_unix"] = time.time()
            _write_json_atomic(output_path, report)

    jobs = [
        {
            "source_target": source_target,
            "profile": profile,
            "seed": int(seed),
            "xgb_threads": int(xgb_threads),
        }
        for source_target in STAGE5_4_SOURCE_TARGETS
        for profile in STAGE5_4_PROFILE_KEYS
        for seed in STAGE5_4_SEEDS
    ]

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
        print(
            f"[{report['progress']['done_runs']}/{report['progress']['total_runs']}] "
            f"{run['source_target']} | {run['profile']} | seed={run['seed']} | "
            f"auc={report['progress']['last_completed']['auc']} | eta_sec={report['progress']['eta_sec']}",
            flush=True,
        )
        _write_json_atomic(output_path, report)

    if workers <= 1:
        for job in jobs:
            job["split"] = splits_by_source[job["source_target"]]
            job["feature_split"] = features_by_source_profile[job["source_target"]][job["profile"]]
            consume_run(_run_stage5_4_job(job))
    else:
        with ProcessPoolExecutor(
            max_workers=int(workers),
            initializer=_init_stage5_4_worker,
            initargs=(splits_by_source, features_by_source_profile),
        ) as executor:
            futures = [executor.submit(_run_stage5_4_job, job) for job in jobs]
            for future in as_completed(futures):
                consume_run(future.result())

    statuses = []
    for source_target in STAGE5_4_SOURCE_TARGETS:
        summary = summarize_stage5_4_source(report["raw_runs"], source_target)
        report["summary"][source_target] = summary
        gate = stage5_4_gate_results(summary, source_target)
        report["gate_results"][source_target] = gate
        statuses.append(gate["overall_status"])
        _write_json_atomic(output_path, report)

    report["status"] = (
        "PRICE_ATR_SIGNAL_FOUND"
        if statuses and any(s == "PRICE_ATR_SIGNAL_FOUND" for s in statuses)
        else "DIAGNOSTIC_ONLY"
    )
    report["progress"]["finished_at_unix"] = time.time()
    report["progress"]["updated_at_unix"] = report["progress"]["finished_at_unix"]
    report["progress"]["elapsed_sec"] = round(report["progress"]["finished_at_unix"] - started_at, 3)
    report["progress"]["eta_sec"] = 0.0
    _write_json_atomic(output_path, report)
    return report
```

- [ ] **Step 4: Add CLI flags and fast path**

In `build_arg_parser()` add near Stage 5.3 flags:

```python
parser.add_argument("--stage5-4-fast-price-atr-ablation", action="store_true",
                    help="Run Stage 5.4 fixed fast target price/ATR feature ablation.")
parser.add_argument("--stage5-4-workers", type=int, default=1,
                    help="Number of worker processes for Stage 5.4")
parser.add_argument("--stage5-4-xgb-threads", type=int, default=1,
                    help="XGBoost threads per Stage 5.4 worker")
```

In `main()` add before the generic Stage 5 prelude:

```python
if args.stage5_4_fast_price_atr_ablation:
    print("\n" + "=" * 60)
    print("Stage 5.4 fast path: fixed fast target price/ATR ablation")
    print("=" * 60)
    print("Загрузка sell splits для Stage 5.4...")
    sell_train, sell_val, sell_hold = load_splits(target_col="sell_bars_to_breach_H6_off05")
    print("Загрузка buy splits для Stage 5.4...")
    buy_train, buy_val, buy_hold = load_splits(target_col="buy_bars_to_breach_H6_off05")
    report = run_stage5_4_fast_price_atr_ablation(
        {"sell": (sell_train, sell_val, sell_hold), "buy": (buy_train, buy_val, buy_hold)},
        output_path=STAGE5_4_JSON_REPORT_PATH,
        workers=args.stage5_4_workers,
        xgb_threads=args.stage5_4_xgb_threads,
    )
    print("Stage 5.4: fast price/ATR ablation completed")
    print(json.dumps({
        "status": report["status"],
        "json": str(STAGE5_4_JSON_REPORT_PATH),
        "done_runs": report["progress"]["done_runs"],
        "total_runs": report["progress"]["total_runs"],
    }, indent=2))
    return
```

- [ ] **Step 5: Run tests to verify they pass**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py::test_stage5_4_runner_writes_json tests/test_stage5_transformer_breach.py::test_stage5_4_cli_arguments_exist_in_build_arg_parser -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add ML/baseline/benchmark_stage5_transformer_breach.py tests/test_stage5_transformer_breach.py
git commit -m "feat: add stage 5.4 runner"
```

---

### Task 6: Full Verification And Full Run

**Files:**
- Read: `DATA/Nero_XAUUSD_train_labeled.csv`
- Read: `DATA/Nero_XAUUSD_validation_labeled.csv`
- Read: `DATA/Nero_XAUUSD_test_labeled.csv`
- Create: `ML/reports/stage5_4_fast_price_atr_ablation.json`

**Interfaces:**
- Consumes: CLI `--stage5-4-fast-price-atr-ablation`
- Produces: completed JSON with `progress.done_runs == progress.total_runs == 72`

- [ ] **Step 1: Run targeted tests**

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py -q -k "stage5_4 or build_stage5_4"
```

Expected: all selected tests PASS.

- [ ] **Step 2: Run full test suite**

```bash
./.venv/bin/python -m pytest tests/ -q
```

Expected: full suite PASS.

- [ ] **Step 3: Run CSV contract check for required Stage 5.4 columns**

```bash
./.venv/bin/python - <<'PY'
import pandas as pd
from pathlib import Path

required = [
    "time",
    "ATR",
    "fractal0",
    "fractal99",
    "sell_bars_to_breach_H6_off05",
    "buy_bars_to_breach_H6_off05",
]
for path in [
    Path("DATA/Nero_XAUUSD_train_labeled.csv"),
    Path("DATA/Nero_XAUUSD_validation_labeled.csv"),
    Path("DATA/Nero_XAUUSD_test_labeled.csv"),
]:
    df = pd.read_csv(path, nrows=5)
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise SystemExit(f"{path}: missing {missing}")
print("stage5_4_csv_contract_ok")
PY
```

Expected: `stage5_4_csv_contract_ok`.

- [ ] **Step 4: Run full Stage 5.4**

Recommended server command:

```bash
./.venv/bin/python -u ML/baseline/benchmark_stage5_transformer_breach.py \
  --stage5-4-fast-price-atr-ablation \
  --stage5-4-workers 12 \
  --stage5-4-xgb-threads 1
```

Expected:

- JSON path: `ML/reports/stage5_4_fast_price_atr_ablation.json`;
- `progress.done_runs = 72`;
- `progress.total_runs = 72`;
- `status` is `PRICE_ATR_SIGNAL_FOUND` or `DIAGNOSTIC_ONLY`;
- no `PREFLIGHT_FAILED`.

- [ ] **Step 5: Verify JSON consistency**

```bash
./.venv/bin/python - <<'PY'
import json
from pathlib import Path

p = Path("ML/reports/stage5_4_fast_price_atr_ablation.json")
d = json.loads(p.read_text())
assert d["stage"] == "5.4_fast_price_atr_ablation"
assert d["target_spec"]["name"] == "fast"
assert d["progress"]["done_runs"] == d["progress"]["total_runs"] == 72
assert d["status"] in {"PRICE_ATR_SIGNAL_FOUND", "DIAGNOSTIC_ONLY"}
for source in d["source_targets"]:
    assert source in d["feature_distribution_audit"]
    assert source in d["summary"]
    assert source in d["gate_results"]
    for profile, audit in d["feature_distribution_audit"][source].items():
        assert audit["status"] in {"PASS", "WARNING"}
print("stage5_4_json_consistency_ok")
PY
```

Expected: `stage5_4_json_consistency_ok`.

- [ ] **Step 6: Commit**

```bash
git add ML/reports/stage5_4_fast_price_atr_ablation.json
git commit -m "test: run stage 5.4 fast price atr ablation"
```

---

### Task 7: Report And Project Knowledge Sync

**Files:**
- Create: `docs/reports/2026-06-29-stage5_4-fast-price-atr-ablation.md`
- Modify if stage closes: `CHANGELOG.md`
- Modify if stage closes: `CONTEXT_HANDOFF.md`
- Modify if stage closes: `wiki/research/fractal-stop-research.md`
- Modify if stage closes: `wiki/index.md`
- Modify if wiki changes: `wiki/log.md`, `wiki/REPO_integrity.md`

**Interfaces:**
- Consumes: `ML/reports/stage5_4_fast_price_atr_ablation.json`
- Produces: canonical Stage 5.4 report

- [ ] **Step 1: Read reporting/wiki skills**

```bash
sed -n '1,260p' .claude/skills/my/stage-reporting/SKILL.md
sed -n '1,220p' .claude/skills/my/wiki/SKILL.md
```

Expected: both files exist. If `.claude/skills/...` is missing in a future environment, use `.opencode/skills/my/...` if present and record the path change.

- [ ] **Step 2: Write report from JSON, not memory**

Report must include:

- Context: Stage 5.4 fixed target `fast` after Stage 5.3.
- What Was Done: 12 profiles, 2 sides, 3 seeds, 72 runs.
- A7 Preflight: table of `PASS`/`WARNING` by profile; decisions for `TAIL`, `REGIME_SHIFT`, `ZERO_GT95`; explicit statement that `ERROR` blocks training.
- Results: per-side baseline and primary profile table.
- Per-seed delta table: each seed delta vs side baseline, not only median.
- Gate: `delta >= 0.02` must pass at least `2/3` seed.
- Buy disclosure: buy remains borderline unless it passes per-seed gate.
- Holdout disclosure: holdout drop and warning if drop > `0.06`.
- Secondary/diagnostic results: `price_atr_scaled`, `ATR`, Up/Dn cannot become primary winner.
- Multiple Testing Context: fixed target, 12 profiles, 72 model runs; no independent candidate validation.
- Limitations: `2023-2025` burned diagnostic disclosure, no trading PF, no new independent period, no survival-loss.
- Next Step: depends on result:
  - if sell primary passes: consider narrow trading/execution mapping or confirmation on new period;
  - if only diagnostic profiles pass: do not promote; design narrower follow-up;
  - if none pass: price/ATR does not explain missing `fast` signal.

- [ ] **Step 3: Verify report numbers against JSON**

```bash
./.venv/bin/python - <<'PY'
import json
from pathlib import Path

d = json.loads(Path("ML/reports/stage5_4_fast_price_atr_ablation.json").read_text())
report = Path("docs/reports/2026-06-29-stage5_4-fast-price-atr-ablation.md").read_text()
checks = [
    str(d["progress"]["done_runs"]),
    str(d["progress"]["total_runs"]),
    d["status"],
    "fast",
]
missing = [item for item in checks if item not in report]
if missing:
    raise SystemExit(f"report_missing_values={missing}")
print("stage5_4_report_basic_json_check_ok")
PY
```

Expected: `stage5_4_report_basic_json_check_ok`.

- [ ] **Step 4: Sync changelog/handoff/wiki if Stage 5.4 changes project knowledge**

If report closes the stage, update:

```bash
sed -n '1,180p' CHANGELOG.md
sed -n '1,220p' CONTEXT_HANDOFF.md
sed -n '1,120p' wiki/index.md
rg -n "Stage 5\\.4|price_coord_atr|fast" wiki/research/fractal-stop-research.md
```

Then edit the relevant files and run:

```bash
./.venv/bin/python wiki/wiki.py generate
./.venv/bin/python wiki/wiki.py status
```

Expected: `Wiki is up to date. No gaps found.`

- [ ] **Step 5: Commit documentation sync**

```bash
git add docs/reports/2026-06-29-stage5_4-fast-price-atr-ablation.md CHANGELOG.md CONTEXT_HANDOFF.md wiki/research/fractal-stop-research.md wiki/index.md wiki/log.md wiki/REPO_integrity.md
git commit -m "docs: report stage 5.4 fast price atr ablation"
```

---

## Self-Review Checklist

- Spec coverage: fixed `fast` target, primary `price_coord_atr`, secondary `price_atr_scaled`, diagnostic raw/ATR and Up/Dn, A7 preflight, per-seed gate, buy borderline disclosure and holdout warning are covered.
- Placeholder scan: no unresolved placeholders, copy-forward shortcuts or unspecified test steps.
- Type consistency: Stage 5.4 functions use existing Stage 5.3 target/metric helpers; profile keys match constants and tests.
- Scope control: no new target search, no trading PF gate, no Transformer, no survival-loss in Stage 5.4.
- Known limitation: the implementation extends the compact Stage 5.2/5.3 feature builder instead of migrating to the older generic profile builder; this is intentional to reduce regression risk.
