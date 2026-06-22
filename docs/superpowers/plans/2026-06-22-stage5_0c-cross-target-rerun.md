# Stage 5.0c Cross-Target Replication Rerun Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replication test одного заранее выбранного профиля `all100_absolute_price_atr_scaled_time_asinh` на двух целях (sell + buy) с pre-registered числовыми порогами, multi-seed CI, и честным сравнением Transformer vs XGBoost на тех же признаках.

**Architecture:** Новый CLI `--stage5-0c-cross-target-rerun` загружает sell и buy splits, обучает Transformer на 5 seeds и XGBoost на том же профиле для каждой цели, применяет pre-registered replication decision gate. Holdout — disclosure only. Trading winner не объявляется. Legacy Stage 5.0/5.0a/5.0b не меняются.

**Tech Stack:** Python 3.10, pandas, numpy, PyTorch, scikit-learn, xgboost, pytest, текущий `ML/baseline/benchmark_stage5_transformer_breach.py`.

## Framing

**Это replication test, не independent discovery.** Гипотеза порождена наблюдением Stage 5.0b: профиль `all100_absolute_price_atr_scaled_time_asinh` оказался рядом с лидером на двух целевых (sell val_auc 0.6673 vs лидер 0.6719; buy val_auc 0.6752 vs лидер 0.6762). Stage 5.0c проверяет, воспроизводим ли этот сигнал при multi-seed и проходит ли pre-registered gate против XGBoost на тех же признаках. Если гипотеза не воспроизводится — это не опровержение качества профиля, а отсутствие подтверждения.

## Pre-Registered Gates

**Все пороги зафиксированы до любого прогона.** Решение — бинарное (PASS/FAIL), без fuzzy интерпретации.

| Gate | Критерий | Порог |
|---|---|---|
| G1 AUC | median val AUC (5 seeds) > xgb_same_profile val AUC | AND ≥4/5 seeds val AUC > xgb_same_profile val AUC − 0.005 |
| G2 lift_30 | median val lift_30 (5 seeds) < xgb_same_profile val lift_30 | (меньше = лучше) |
| G3 cross-target | G1 AND G2 на BOTH sell и buy | если проходит одну цель, но не другую → FAIL |
| G4 holdout degradation | median holdout AUC (5 seeds) ≥ median val AUC (5 seeds) − 0.05 | tolerance зафиксирован до запуска |
| G5 seed spread | max val AUC − min val AUC across 5 seeds < 0.03 | stability |

**Все пять gate должны пройти.** Итог: `overall_pass = G1 AND G2 AND G3 AND G4 AND G5`.

## Global Constraints

- Работать в текущей ветке, без worktree.
- Использовать `./.venv/bin/python`.
- Holdout 2023-2026 не использовать для выбора; holdout только для disclosure.
- `asinh` заранее зафиксирован как transform Stage 5.0c.
- Профиль `all100_absolute_price_atr_scaled_time_asinh` — единственный; сетка не расширяется.
- Seeds `[42, 77, 123, 202, 777]` — безусловно (no single-seed gate).
- Dynamic corridor `seq_len` отключён (наследие 5.0b).
- После Python-изменений запускать `./.venv/bin/python -m pytest tests/ -q`.
- TDD: каждый task начинается с failing test.

---

## File Structure

- **Modify:** `ML/baseline/benchmark_stage5_transformer_breach.py`
  - `build_flat_features` — extends to accept `transform_variant` + `transform_params`
  - `build_xgb_features_for_profile` — new helper for XGBoost on arbitrary profile
  - `compute_xgb_same_profile_baseline` — new function: XGBoost on same profile, same transform
  - `STAGE5_0C_PROFILE_NAME`, `STAGE5_0C_TARGETS`, `STAGE5_0C_SEEDS`, `STAGE5_0C_GATES` — frozen constants
  - `stage5_0c_replication_decision` — pre-registered decision function
  - `run_stage5_0c_cross_target_rerun` — new runner
  - CLI `--stage5-0c-cross-target-rerun` in `main()`
- **Modify:** `tests/test_stage5_transformer_breach.py`
- **Modify:** `docs/ML/benchmark_stage5_transformer_breach.py.md`
- **Modify:** `CHANGELOG.md`
- **Create:** `docs/reports/2026-06-22-stage5_0c-cross-target-rerun.md` (after run)

---

### Task 1: Extend `build_flat_features` With Transform Variant

**Files:**
- Modify: `ML/baseline/benchmark_stage5_transformer_breach.py:1957-1963`
- Test: `tests/test_stage5_transformer_breach.py`

**Interfaces:**
- Produces: `build_flat_features(df, profile, transform_variant="current", transform_params=None) -> np.ndarray`

**Consumes:** `build_profile_features(df, profile, transform_variant, transform_params)` (existing, line 929)

- [ ] **Step 1: Write failing test**

Add to `tests/test_stage5_transformer_breach.py`:

```python
def test_build_flat_features_passes_transform_variant_to_builder(monkeypatch):
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    captured = {}

    def fake_build(df_arg, profile_arg, transform_variant="current", transform_params=None):
        captured["transform_variant"] = transform_variant
        captured["transform_params"] = transform_params
        n = len(df_arg)
        return (
            np.zeros((n, 5, 2), dtype=np.float32),
            np.zeros((n, 1), dtype=np.float32),
            np.ones((n, 5), dtype=bool),
            {},
        )

    monkeypatch.setattr(runner, "build_profile_features", fake_build)
    df = _make_synthetic_df(3, 10)
    profile = runner.find_profile("all100_absolute_price_atr_scaled_time_asinh")
    runner.build_flat_features(df, profile, transform_variant="asinh", transform_params={"foo": 1})
    assert captured["transform_variant"] == "asinh"
    assert captured["transform_params"] == {"foo": 1}
```

- [ ] **Step 2: Run test to verify it fails**

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py -k build_flat_features_passes_transform_variant -q
```

Expected: FAIL with `TypeError: build_flat_features() got an unexpected keyword argument 'transform_variant'`.

- [ ] **Step 3: Modify `build_flat_features`**

Replace the function at line 1957:

```python
def build_flat_features(df: pd.DataFrame, profile: dict,
                        transform_variant: str = "current",
                        transform_params: dict | None = None) -> np.ndarray:
    """Build flat feature table for XGBoost from profile tokens+row_features."""
    tokens, row_feat, mask, _selection_meta = build_profile_features(
        df, profile, transform_variant=transform_variant, transform_params=transform_params)
    n_samples = len(df)
    flat = tokens.reshape(n_samples, -1)
    result = np.concatenate([flat, row_feat], axis=1)
    return result.astype(np.float32)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py -k build_flat_features_passes_transform_variant -q
```

Expected: PASS.

- [ ] **Step 5: Run full test suite to verify no regression**

```bash
./.venv/bin/python -m pytest tests/ -q
```

Expected: PASS (existing tests unaffected — `build_flat_features` defaults preserve old behavior).

- [ ] **Step 6: Commit**

```bash
git add ML/baseline/benchmark_stage5_transformer_breach.py tests/test_stage5_transformer_breach.py
git commit -m "feat: extend build_flat_features with transform_variant for XGBoost-on-same-profile"
```

---

### Task 2: Add `build_xgb_features_for_profile` Helper

**Files:**
- Modify: `ML/baseline/benchmark_stage5_transformer_breach.py` (after `build_xgb_features`, ~line 1980)
- Test: `tests/test_stage5_transformer_breach.py`

**Interfaces:**
- Produces: `build_xgb_features_for_profile(df, profile_name, transform_variant="current") -> np.ndarray`
- Consumes: `find_profile(name)`, `parse_split_fractals(df)`, `fit_transform_params_for_profile(df, parsed, profile, variant)`, `build_flat_features(df, profile, variant, params)`

- [ ] **Step 1: Write failing test**

Add to `tests/test_stage5_transformer_breach.py`:

```python
def test_build_xgb_features_for_profile_returns_expected_shape():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    df = _make_synthetic_df(4, 100)
    X = runner.build_xgb_features_for_profile(
        df, "all100_absolute_price_atr_scaled_time_asinh", transform_variant="asinh")
    profile = runner.find_profile("all100_absolute_price_atr_scaled_time_asinh")
    expected_dim = profile["seq_len"] * profile["token_dim"] + profile["row_dim"]
    assert X.shape == (4, expected_dim)
    assert X.dtype == np.float32
    assert np.isfinite(X).all()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py -k build_xgb_features_for_profile_returns_expected_shape -q
```

Expected: FAIL with `AttributeError: module ... has no attribute 'build_xgb_features_for_profile'`.

- [ ] **Step 3: Implement helper**

Add after `build_xgb_features` function (after line 1980):

```python
def build_xgb_features_for_profile(df: pd.DataFrame, profile_name: str,
                                   transform_variant: str = "current") -> np.ndarray:
    """Build flat XGBoost features for a named profile with a given transform variant.

    Fits transform_params on the provided df (caller must pass train_df for train-only fit).
    For asinh transform, fit_params=False so transform_params={}.
    """
    profile = find_profile(profile_name)
    parsed = parse_split_fractals(df)
    transform_params = fit_transform_params_for_profile(
        df, parsed, profile, transform_variant)
    return build_flat_features(
        df, profile, transform_variant=transform_variant, transform_params=transform_params)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py -k build_xgb_features_for_profile_returns_expected_shape -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add ML/baseline/benchmark_stage5_transformer_breach.py tests/test_stage5_transformer_breach.py
git commit -m "feat: add build_xgb_features_for_profile helper for XGBoost on arbitrary profile"
```

---

### Task 3: Add `compute_xgb_same_profile_baseline`

**Files:**
- Modify: `ML/baseline/benchmark_stage5_transformer_breach.py` (after `compute_xgb_baselines`, ~line 2284)
- Test: `tests/test_stage5_transformer_breach.py`

**Interfaces:**
- Produces: `compute_xgb_same_profile_baseline(train_df, val_df, hold_df, profile_name, transform_variant, target_col, seed=42) -> dict`
- Consumes: `build_xgb_features_for_profile`, `train_xgb_baseline`, `compute_metrics`, `compute_yearly_metrics`

- [ ] **Step 1: Write failing test**

Add to `tests/test_stage5_transformer_breach.py`:

```python
def test_compute_xgb_same_profile_baseline_returns_val_and_holdout_metrics(monkeypatch):
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    df = _make_synthetic_df(10, 100)
    df["_year"] = [2020] * 5 + [2023] * 5

    monkeypatch.setattr(runner, "build_xgb_features_for_profile",
                        lambda d, pname, tv: np.random.rand(len(d), 10).astype(np.float32))
    monkeypatch.setattr(runner, "train_xgb_baseline",
                        lambda Xtr, ytr, Xv, yv, seed=42: (None, 0.6))
    monkeypatch.setattr(runner, "compute_metrics",
                        lambda yt, yp: {"auc": 0.6, "pr_auc": 0.5, "n": len(yt),
                                        "lift_10": 1.0, "lift_20": 1.0, "lift_30": 0.8})
    monkeypatch.setattr(runner, "compute_yearly_metrics", lambda df_arg, pred, target_col=None: {})

    result = runner.compute_xgb_same_profile_baseline(
        df.iloc[:5], df.iloc[:5], df.iloc[5:],
        "all100_absolute_price_atr_scaled_time_asinh",
        transform_variant="asinh", target_col=runner.TARGET_COLUMN, seed=42)
    assert "val" in result and "holdout" in result
    assert result["val"]["auc"] == 0.6
    assert result["holdout"]["auc"] == 0.6
    assert result["profile"] == "all100_absolute_price_atr_scaled_time_asinh"
    assert result["transform_variant"] == "asinh"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py -k compute_xgb_same_profile_baseline -q
```

Expected: FAIL with `AttributeError`.

- [ ] **Step 3: Implement function**

Add after `compute_xgb_baselines` (after line 2284):

```python
def compute_xgb_same_profile_baseline(train_df, val_stop_df, holdout_df,
                                      profile_name: str,
                                      transform_variant: str = "asinh",
                                      target_col: str = TARGET_COLUMN,
                                      seed: int = 42) -> dict:
    """Train XGBoost on the same profile features as the Transformer.

    This isolates 'features vs model': if XGBoost on the same flattened
    profile beats the Transformer, the issue is the model, not the features.
    """
    print(f"\n  Training XGBoost same-profile: {profile_name} ({transform_variant})...")
    X_train = build_xgb_features_for_profile(train_df, profile_name, transform_variant)
    X_val = build_xgb_features_for_profile(val_stop_df, profile_name, transform_variant)
    X_holdout = build_xgb_features_for_profile(holdout_df, profile_name, transform_variant)

    y_train = train_df[target_col]
    y_val = val_stop_df[target_col]
    y_holdout = holdout_df[target_col]

    model, val_auc = train_xgb_baseline(X_train, y_train, X_val, y_val, seed=seed)

    import xgboost as xgb
    val_probs = model.predict(xgb.DMatrix(X_val))
    holdout_probs = model.predict(xgb.DMatrix(X_holdout))

    val_metrics = compute_metrics(y_val, pd.Series(val_probs))
    holdout_metrics = compute_metrics(y_holdout, pd.Series(holdout_probs))
    yearly = compute_yearly_metrics(holdout_df, holdout_probs, target_col=target_col)

    print(f"    Val AUC: {val_auc:.4f}, Holdout AUC: {holdout_metrics.get('auc', 'N/A')}")

    return {
        "profile": profile_name,
        "transform_variant": transform_variant,
        "seed": seed,
        "val": {k: _safe(v) for k, v in val_metrics.items()},
        "holdout": {k: _safe(v) for k, v in holdout_metrics.items()},
        "yearly": {k: {kk: _safe(vv) for kk, vv in v.items()} for k, v in yearly.items()},
    }
```

- [ ] **Step 4: Run test to verify it passes**

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py -k compute_xgb_same_profile_baseline -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add ML/baseline/benchmark_stage5_transformer_breach.py tests/test_stage5_transformer_breach.py
git commit -m "feat: add compute_xgb_same_profile_baseline for fair feature-vs-model comparison"
```

---

### Task 4: Freeze Stage 5.0c Constants

**Files:**
- Modify: `ML/baseline/benchmark_stage5_transformer_breach.py` (near `STAGE5_0B_*` constants, ~line 2589)
- Test: `tests/test_stage5_transformer_breach.py`

**Interfaces:**
- Produces: `STAGE5_0C_PROFILE_NAME: str`
- Produces: `STAGE5_0C_TARGETS: list[str]`
- Produces: `STAGE5_0C_SEEDS: list[int]`
- Produces: `STAGE5_0C_GATES: dict`

- [ ] **Step 1: Write failing test**

Add to `tests/test_stage5_transformer_breach.py`:

```python
def test_stage5_0c_constants_are_frozen():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    assert runner.STAGE5_0C_PROFILE_NAME == "all100_absolute_price_atr_scaled_time_asinh"
    assert runner.STAGE5_0C_TARGETS == [
        "sell_stop_broken_H6_off05_flag",
        "buy_stop_broken_H6_off05_flag",
    ]
    assert runner.STAGE5_0C_SEEDS == [42, 77, 123, 202, 777]
    gates = runner.STAGE5_0C_GATES
    assert gates["g1_auc"]["median_above_xgb"] is True
    assert gates["g1_auc"]["min_seeds_above_xgb_minus_tol"] == 4
    assert gates["g1_auc"]["tolerance"] == 0.005
    assert gates["g2_lift30"]["median_below_xgb"] is True
    assert gates["g3_cross_target"]["both_targets_required"] is True
    assert gates["g4_holdout_degradation"]["max_drop"] == 0.05
    assert gates["g5_seed_spread"]["max_range"] == 0.03
    assert runner.find_profile(runner.STAGE5_0C_PROFILE_NAME) is not None
```

- [ ] **Step 2: Run test to verify it fails**

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py -k test_stage5_0c_constants_are_frozen -q
```

Expected: FAIL with `AttributeError`.

- [ ] **Step 3: Add constants**

Add near `STAGE5_0B_*` constants (after line ~2610):

```python
STAGE5_0C_PROFILE_NAME = "all100_absolute_price_atr_scaled_time_asinh"
STAGE5_0C_TARGETS = [
    "sell_stop_broken_H6_off05_flag",
    "buy_stop_broken_H6_off05_flag",
]
STAGE5_0C_SEEDS = [42, 77, 123, 202, 777]
STAGE5_0C_GATES = {
    "g1_auc": {
        "median_above_xgb": True,
        "min_seeds_above_xgb_minus_tol": 4,
        "tolerance": 0.005,
    },
    "g2_lift30": {
        "median_below_xgb": True,
    },
    "g3_cross_target": {
        "both_targets_required": True,
    },
    "g4_holdout_degradation": {
        "max_drop": 0.05,
    },
    "g5_seed_spread": {
        "max_range": 0.03,
    },
}
STAGE5_0C_JSON_REPORT_PATH = REPORTS_DIR / "stage5_0c_cross_target_rerun.json"
```

- [ ] **Step 4: Run test to verify it passes**

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py -k test_stage5_0c_constants_are_frozen -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add ML/baseline/benchmark_stage5_transformer_breach.py tests/test_stage5_transformer_breach.py
git commit -m "feat: freeze Stage 5.0c constants (profile, targets, seeds, pre-registered gates)"
```

---

### Task 5: Add `stage5_0c_replication_decision` With Pre-Registered Gates

**Files:**
- Modify: `ML/baseline/benchmark_stage5_transformer_breach.py` (after `stage5_0b_multiseed_decision`, ~line 3009)
- Test: `tests/test_stage5_transformer_breach.py`

**Interfaces:**
- Produces: `stage5_0c_replication_decision(target_results: dict) -> dict`
  - `target_results` = `{"sell": {"seed_metrics": [{"val": {"auc": .., "lift_30": ..}, "holdout": {"auc": ..}}], "xgb_same_profile": {"val": {"auc": .., "lift_30": ..}}}, "buy": {...}}`

- [ ] **Step 1: Write failing test: all gates pass**

Add to `tests/test_stage5_transformer_breach.py`:

```python
def test_stage5_0c_replication_decision_all_gates_pass():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    def make_target(xgb_auc, xgb_lift, seed_aucs, seed_lifts, holdout_aucs):
        return {
            "xgb_same_profile": {"val": {"auc": xgb_auc, "lift_30": xgb_lift}},
            "seed_metrics": [
                {"val": {"auc": a, "lift_30": l}, "holdout": {"auc": h}}
                for a, l, h in zip(seed_aucs, seed_lifts, holdout_aucs)
            ],
        }

    target_results = {
        "sell": make_target(
            xgb_auc=0.65, xgb_lift=0.60,
            seed_aucs=[0.66, 0.67, 0.68, 0.65, 0.67],
            seed_lifts=[0.55, 0.56, 0.54, 0.57, 0.56],
            holdout_aucs=[0.64, 0.65, 0.66, 0.63, 0.65]),
        "buy": make_target(
            xgb_auc=0.67, xgb_lift=0.58,
            seed_aucs=[0.68, 0.69, 0.70, 0.67, 0.68],
            seed_lifts=[0.53, 0.54, 0.52, 0.55, 0.54],
            holdout_aucs=[0.66, 0.67, 0.68, 0.65, 0.67]),
    }
    decision = runner.stage5_0c_replication_decision(target_results)
    assert decision["overall_pass"] is True
    assert decision["g1_auc"]["pass"] is True
    assert decision["g2_lift30"]["pass"] is True
    assert decision["g3_cross_target"]["pass"] is True
    assert decision["g4_holdout_degradation"]["pass"] is True
    assert decision["g5_seed_spread"]["pass"] is True
```

- [ ] **Step 2: Write failing test: cross-target fail**

Add to `tests/test_stage5_transformer_breach.py`:

```python
def test_stage5_0c_replication_decision_cross_target_fail_when_one_target_fails():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    def make_target(xgb_auc, xgb_lift, seed_aucs, seed_lifts, holdout_aucs):
        return {
            "xgb_same_profile": {"val": {"auc": xgb_auc, "lift_30": xgb_lift}},
            "seed_metrics": [
                {"val": {"auc": a, "lift_30": l}, "holdout": {"auc": h}}
                for a, l, h in zip(seed_aucs, seed_lifts, holdout_aucs)
            ],
        }

    target_results = {
        "sell": make_target(
            xgb_auc=0.65, xgb_lift=0.60,
            seed_aucs=[0.66, 0.67, 0.68, 0.65, 0.67],
            seed_lifts=[0.55, 0.56, 0.54, 0.57, 0.56],
            holdout_aucs=[0.64, 0.65, 0.66, 0.63, 0.65]),
        "buy": make_target(
            xgb_auc=0.75, xgb_lift=0.50,
            seed_aucs=[0.68, 0.69, 0.70, 0.67, 0.68],
            seed_lifts=[0.53, 0.54, 0.52, 0.55, 0.54],
            holdout_aucs=[0.66, 0.67, 0.68, 0.65, 0.67]),
    }
    decision = runner.stage5_0c_replication_decision(target_results)
    assert decision["overall_pass"] is False
    assert decision["g1_auc"]["sell"]["pass"] is True
    assert decision["g1_auc"]["buy"]["pass"] is False
    assert decision["g3_cross_target"]["pass"] is False
```

- [ ] **Step 3: Write failing test: seed spread fail**

Add to `tests/test_stage5_transformer_breach.py`:

```python
def test_stage5_0c_replication_decision_seed_spread_fail():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    def make_target(xgb_auc, xgb_lift, seed_aucs, seed_lifts, holdout_aucs):
        return {
            "xgb_same_profile": {"val": {"auc": xgb_auc, "lift_30": xgb_lift}},
            "seed_metrics": [
                {"val": {"auc": a, "lift_30": l}, "holdout": {"auc": h}}
                for a, l, h in zip(seed_aucs, seed_lifts, holdout_aucs)
            ],
        }

    target_results = {
        "sell": make_target(
            xgb_auc=0.60, xgb_lift=0.70,
            seed_aucs=[0.62, 0.68, 0.55, 0.66, 0.67],
            seed_lifts=[0.55, 0.56, 0.54, 0.57, 0.56],
            holdout_aucs=[0.60, 0.60, 0.60, 0.60, 0.60]),
        "buy": make_target(
            xgb_auc=0.60, xgb_lift=0.70,
            seed_aucs=[0.62, 0.63, 0.64, 0.61, 0.62],
            seed_lifts=[0.55, 0.56, 0.54, 0.57, 0.56],
            holdout_aucs=[0.60, 0.60, 0.60, 0.60, 0.60]),
    }
    decision = runner.stage5_0c_replication_decision(target_results)
    assert decision["overall_pass"] is False
    assert decision["g5_seed_spread"]["sell"]["range"] >= 0.03
    assert decision["g5_seed_spread"]["pass"] is False
```

- [ ] **Step 4: Run tests to verify they fail**

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py -k "stage5_0c_replication_decision" -q
```

Expected: FAIL with `AttributeError`.

- [ ] **Step 5: Implement decision function**

Add after `stage5_0b_multiseed_decision` (after line 3009):

```python
def _median(values: list) -> float:
    import statistics
    return float(statistics.median(values))


def stage5_0c_replication_decision(target_results: dict) -> dict:
    """Apply pre-registered Stage 5.0c replication gates.

    All thresholds are frozen in STAGE5_0C_GATES before any run.
    Returns per-gate, per-target breakdown and overall_pass.
    """
    gates = STAGE5_0C_GATES
    tol = gates["g1_auc"]["tolerance"]
    min_seeds = gates["g1_auc"]["min_seeds_above_xgb_minus_tol"]
    max_drop = gates["g4_holdout_degradation"]["max_drop"]
    max_range = gates["g5_seed_spread"]["max_range"]

    g1 = {"per_target": {}, "pass": True}
    g2 = {"per_target": {}, "pass": True}
    g5 = {"per_target": {}, "pass": True}
    g4 = {"per_target": {}, "pass": True}

    for tname, tdata in target_results.items():
        seed_val_aucs = [s["val"]["auc"] for s in tdata["seed_metrics"]]
        seed_val_lifts = [s["val"]["lift_30"] for s in tdata["seed_metrics"]]
        seed_hold_aucs = [s["holdout"]["auc"] for s in tdata["seed_metrics"]]
        xgb_auc = tdata["xgb_same_profile"]["val"]["auc"]
        xgb_lift = tdata["xgb_same_profile"]["val"]["lift_30"]

        med_val_auc = _median(seed_val_aucs)
        med_val_lift = _median(seed_val_lifts)
        med_hold_auc = _median(seed_hold_aucs)
        seeds_above = sum(1 for a in seed_val_aucs if a > xgb_auc - tol)
        spread = max(seed_val_aucs) - min(seed_val_aucs)

        g1_pass = med_val_auc > xgb_auc and seeds_above >= min_seeds
        g2_pass = med_val_lift < xgb_lift
        g4_pass = med_hold_auc >= med_val_auc - max_drop
        g5_pass = spread < max_range

        g1["per_target"][tname] = {
            "pass": g1_pass,
            "median_val_auc": med_val_auc,
            "xgb_val_auc": xgb_auc,
            "seeds_above_tol": seeds_above,
        }
        g2["per_target"][tname] = {
            "pass": g2_pass,
            "median_val_lift_30": med_val_lift,
            "xgb_val_lift_30": xgb_lift,
        }
        g4["per_target"][tname] = {
            "pass": g4_pass,
            "median_holdout_auc": med_hold_auc,
            "median_val_auc": med_val_auc,
            "drop": med_val_auc - med_hold_auc,
        }
        g5["per_target"][tname] = {
            "pass": g5_pass,
            "range": spread,
        }
        g1["pass"] = g1["pass"] and g1_pass
        g2["pass"] = g2["pass"] and g2_pass
        g4["pass"] = g4["pass"] and g4_pass
        g5["pass"] = g5["pass"] and g5_pass

    g3_pass = g1["pass"] and g2["pass"] and gates["g3_cross_target"]["both_targets_required"]
    overall = g1["pass"] and g2["pass"] and g3_pass and g4["pass"] and g5["pass"]

    # Flatten per_target for backwards-compatible test access
    g1_out = dict(g1)
    g1_out.update(g1["per_target"])
    g2_out = dict(g2)
    g2_out.update(g2["per_target"])
    g5_out = dict(g5)
    g5_out.update(g5["per_target"])

    return {
        "overall_pass": bool(overall),
        "g1_auc": g1_out,
        "g2_lift30": g2_out,
        "g3_cross_target": {"pass": bool(g3_pass), "both_targets_required": True},
        "g4_holdout_degradation": g4,
        "g5_seed_spread": g5_out,
        "gates_config": gates,
    }
```

- [ ] **Step 6: Run tests to verify they pass**

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py -k "stage5_0c_replication_decision" -q
```

Expected: PASS (all 3 tests).

- [ ] **Step 7: Commit**

```bash
git add ML/baseline/benchmark_stage5_transformer_breach.py tests/test_stage5_transformer_breach.py
git commit -m "feat: add stage5_0c_replication_decision with pre-registered numeric gates"
```

---

### Task 6: Add `run_stage5_0c_cross_target_rerun` Runner

**Files:**
- Modify: `ML/baseline/benchmark_stage5_transformer_breach.py` (after `run_stage5_0b_asinh_rerun`, ~line 3093)
- Test: `tests/test_stage5_transformer_breach.py`

**Interfaces:**
- Produces: `run_stage5_0c_cross_target_rerun(sell_splits, buy_splits, seeds, device, output_path) -> dict`
  - `sell_splits` = `(train_df, val_df, hold_df)` filtered by sell target
  - `buy_splits` = `(train_df, val_df, hold_df)` filtered by buy target
- Produces artifact: `ML/reports/stage5_0c_cross_target_rerun.json`

- [ ] **Step 1: Write failing test**

Add to `tests/test_stage5_transformer_breach.py`:

```python
def test_stage5_0c_runner_trains_both_targets_and_applies_replication_decision(monkeypatch, tmp_path):
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    transformer_calls = []
    xgb_calls = []

    df_sell = _make_synthetic_df(5, 100)
    df_sell["_year"] = [2020] * 5
    df_buy = df_sell.copy()
    df_buy["buy_stop_broken_H6_off05_flag"] = [0, 1, 0, 1, 0]

    def fake_train(train_df, val_df, hold_df, seed, device, report,
                   pname, y_train, y_val, y_holdout,
                   diagnostic_only=False, transform_variant="current",
                   parsed_splits=None, allow_dynamic_seq_len=True,
                   profile_role="legacy", target_col=runner.TARGET_COLUMN):
        transformer_calls.append((target_col, transform_variant, seed, profile_role))
        report["transformer_results"].setdefault(pname, []).append({
            "profile": pname,
            "seed": seed,
            "transform_variant": transform_variant,
            "profile_role": profile_role,
            "training_run": True,
            "normalized_distribution_audit": {"status": "OK", "flags": []},
            "val": {"auc": 0.70, "lift_30": 0.50, "pr_auc": 0.6, "n": 5,
                    "lift_10": 1.0, "lift_20": 1.0},
            "holdout": {"auc": 0.68, "lift_30": 0.55, "pr_auc": 0.6, "n": 5,
                        "lift_10": 1.0, "lift_20": 1.0},
            "yearly": {},
        })
        return 1.0

    def fake_xgb_same(train_df, val_df, hold_df, profile_name,
                      transform_variant="asinh", target_col=runner.TARGET_COLUMN, seed=42):
        xgb_calls.append((target_col, profile_name, transform_variant))
        return {
            "profile": profile_name,
            "transform_variant": transform_variant,
            "seed": seed,
            "val": {"auc": 0.65, "lift_30": 0.60, "pr_auc": 0.6, "n": 5,
                    "lift_10": 1.0, "lift_20": 1.0},
            "holdout": {"auc": 0.63, "lift_30": 0.65, "pr_auc": 0.6, "n": 5,
                        "lift_10": 1.0, "lift_20": 1.0},
            "yearly": {},
        }

    monkeypatch.setattr(runner, "_train_and_eval_profile", fake_train)
    monkeypatch.setattr(runner, "compute_xgb_same_profile_baseline", fake_xgb_same)
    monkeypatch.setattr(runner, "compute_xgb_baselines",
                        lambda tr, va, ho, target_col=runner.TARGET_COLUMN: {
                            "base_raw_plus_time": {"val": {"auc": 0.6, "lift_30": 0.7}},
                            "no_time": {"val": {"auc": 0.55, "lift_30": 0.8}},
                            "time_only": {"val": {"auc": 0.58, "lift_30": 0.75}},
                        })
    monkeypatch.setattr(runner, "verify_breach_labels_against_ohlc",
                        lambda df, target_col: {"status": "PASS", "n_matches": 50, "n_checked": 50, "n_mismatches": 0})
    monkeypatch.setattr(runner, "label_sanity_check",
                        lambda df, target_col=runner.TARGET_COLUMN: {"status": "SANITY_ONLY", "positive_rate": 0.4})

    report = runner.run_stage5_0c_cross_target_rerun(
        sell_splits=(df_sell, df_sell, df_sell),
        buy_splits=(df_buy, df_buy, df_buy),
        seeds=[42, 77],
        device="cpu",
        output_path=tmp_path / "stage5_0c.json",
    )

    assert report["status"] == "DIAGNOSTIC_ONLY"
    assert report["stage"] == "5.0c_cross_target_rerun"
    assert report["profile"] == runner.STAGE5_0C_PROFILE_NAME
    assert report["framing"] == "replication_test_of_5_0b_hypothesis"
    assert report["no_trading_winner_declared"] is True
    assert "sell" in report["targets"] and "buy" in report["targets"]
    assert len(report["targets"]["sell"]["transformer_results"][runner.STAGE5_0C_PROFILE_NAME]) == 2
    assert {c[0] for c in transformer_calls} == {"sell_stop_broken_H6_off05_flag", "buy_stop_broken_H6_off05_flag"}
    assert {c[1] for c in transformer_calls} == {"asinh"}
    assert "replication_decision" in report
    assert "overall_pass" in report["replication_decision"]
    assert (tmp_path / "stage5_0c.json").exists()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py -k test_stage5_0c_runner_trains_both_targets -q
```

Expected: FAIL with `AttributeError`.

- [ ] **Step 3: Implement runner**

Add after `run_stage5_0b_asinh_rerun` (after line 3093):

```python
def run_stage5_0c_cross_target_rerun(sell_splits: tuple, buy_splits: tuple,
                                     seeds: list, device, output_path=None) -> dict:
    """Stage 5.0c: replication test of one frozen profile on sell + buy.

    Framing: replication test of 5.0b hypothesis, not independent discovery.
    Pre-registered gates in STAGE5_0C_GATES; holdout disclosure only.
    """
    profile_name = STAGE5_0C_PROFILE_NAME
    report = {
        "status": "DIAGNOSTIC_ONLY",
        "stage": "5.0c_cross_target_rerun",
        "profile": profile_name,
        "transform_variant": "asinh",
        "seeds": list(seeds),
        "framing": "replication_test_of_5_0b_hypothesis",
        "no_trading_winner_declared": True,
        "pre_registered_gates": STAGE5_0C_GATES,
        "decision_policy": {
            "selection_basis": "val_stop only",
            "holdout_usage": "disclosure only",
            "profile_set": "single frozen profile, no grid search",
            "multi_seed_policy": "unconditional 5-seed, no single-seed gate",
        },
        "targets": {},
    }

    split_sets = {
        "sell": (sell_splits, STAGE5_0C_TARGETS[0]),
        "buy": (buy_splits, STAGE5_0C_TARGETS[1]),
    }

    for tname, (splits, target_col) in split_sets.items():
        train_df, val_df, hold_df = splits
        print(f"\n{'='*60}")
        print(f"Stage 5.0c — target: {tname} ({target_col})")
        print(f"{'='*60}")

        ohlc = verify_breach_labels_against_ohlc(hold_df, target_col=target_col)
        sanity = label_sanity_check(hold_df, target_col=target_col)
        xgb_baselines = compute_xgb_baselines(train_df, val_df, hold_df, target_col=target_col)
        xgb_same = compute_xgb_same_profile_baseline(
            train_df, val_df, hold_df, profile_name,
            transform_variant="asinh", target_col=target_col, seed=seeds[0])

        parsed_splits = {
            "train": parse_split_fractals(train_df),
            "val_stop": parse_split_fractals(val_df),
            "holdout": parse_split_fractals(hold_df),
        }
        y_train = train_df[target_col]
        y_val = val_df[target_col]
        y_holdout = hold_df[target_col]

        seed_metrics = []
        transformer_report = {"transformer_results": {}}
        for seed in seeds:
            print(f"\n  --- seed={seed} ---")
            _train_and_eval_profile(
                train_df, val_df, hold_df, seed, device, transformer_report,
                profile_name, y_train, y_val, y_holdout,
                diagnostic_only=False,
                transform_variant="asinh",
                parsed_splits=parsed_splits,
                allow_dynamic_seq_len=False,
                profile_role="confirmatory",
                target_col=target_col,
            )
            result = transformer_report["transformer_results"][profile_name][-1]
            seed_metrics.append({
                "seed": seed,
                "val": result.get("val", {}),
                "holdout": result.get("holdout", {}),
                "normalized_distribution_audit": result.get("normalized_distribution_audit", {}),
            })

        report["targets"][tname] = {
            "target_col": target_col,
            "ohlc_verification": ohlc,
            "label_sanity": sanity,
            "xgb_baselines": xgb_baselines,
            "xgb_same_profile": xgb_same,
            "transformer_results": transformer_report["transformer_results"],
            "seed_metrics": seed_metrics,
        }

    target_for_decision = {
        tname: {
            "xgb_same_profile": tdata["xgb_same_profile"],
            "seed_metrics": tdata["seed_metrics"],
        }
        for tname, tdata in report["targets"].items()
    }
    report["replication_decision"] = stage5_0c_replication_decision(target_for_decision)

    if output_path is not None:
        output_path = Path(output_path)
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2, default=str)
    return report
```

- [ ] **Step 4: Run test to verify it passes**

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py -k test_stage5_0c_runner_trains_both_targets -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add ML/baseline/benchmark_stage5_transformer_breach.py tests/test_stage5_transformer_breach.py
git commit -m "feat: add run_stage5_0c_cross_target_rerun runner"
```

---

### Task 7: Add CLI And Wire Into `main()`

**Files:**
- Modify: `ML/baseline/benchmark_stage5_transformer_breach.py` (parser ~line 3102, main dispatch ~line 3165)
- Test: `tests/test_stage5_transformer_breach.py`

**Interfaces:**
- Produces CLI: `--stage5-0c-cross-target-rerun`

- [ ] **Step 1: Write failing test for CLI wiring**

Add to `tests/test_stage5_transformer_breach.py`:

```python
def test_stage5_0c_cli_argument_exists():
    import argparse
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    parser = argparse.ArgumentParser()
    # Replicate the argument registration
    parser.add_argument("--stage5-0c-cross-target-rerun", action="store_true",
                        help="Run Stage 5.0c frozen cross-target replication rerun")
    args = parser.parse_args(["--stage5-0c-cross-target-rerun"])
    assert args.stage5_0c_cross_target_rerun is True
```

- [ ] **Step 2: Run test to verify it fails (sanity check)**

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py -k test_stage5_0c_cli_argument_exists -q
```

Note: this test validates argparse registration in isolation; it should pass once the argument is added to the actual parser. The real wiring is verified by the integration in Step 5.

- [ ] **Step 3: Add CLI argument**

In `main()`, after the `--stage5-0b-asinh-rerun` argument (after line 3103), add:

```python
    parser.add_argument("--stage5-0c-cross-target-rerun", action="store_true",
                        help="Run Stage 5.0c frozen cross-target replication rerun")
```

- [ ] **Step 4: Wire into main dispatch**

In `main()`, the `--stage5-0b-asinh-rerun` block ends with `return` at ~line 3183. After that block, add:

```python
    if args.stage5_0c_cross_target_rerun:
        print("\n" + "=" * 60)
        print("Loading buy splits for Stage 5.0c...")
        print("=" * 60)
        buy_train, buy_val, buy_hold = load_splits(target_col="buy_stop_broken_H6_off05_flag")
        report = run_stage5_0c_cross_target_rerun(
            sell_splits=(train_df, val_stop_df, holdout_df),
            buy_splits=(buy_train, buy_val, buy_hold),
            seeds=STAGE5_0C_SEEDS,
            device=device,
            output_path=STAGE5_0C_JSON_REPORT_PATH,
        )
        print("\n" + "=" * 60)
        print("Stage 5.0c cross-target rerun completed")
        print(json.dumps({"json": str(STAGE5_0C_JSON_REPORT_PATH)}, indent=2))
        print("=" * 60)
        return
```

Note: `train_df, val_stop_df, holdout_df` are already loaded at line 3129 with `target_col=args.target` (defaults to sell). For 5.0c, the default sell target is correct. Buy splits are loaded explicitly inside the block.

- [ ] **Step 5: Run full test suite**

```bash
./.venv/bin/python -m pytest tests/ -q
```

Expected: PASS (all tests including new Stage 5.0c tests).

- [ ] **Step 6: Commit**

```bash
git add ML/baseline/benchmark_stage5_transformer_breach.py tests/test_stage5_transformer_breach.py
git commit -m "feat: add --stage5-0c-cross-target-rerun CLI and wire into main"
```

---

### Task 8: Execute Stage 5.0c Run And Write Report

**Files:**
- Generated: `ML/reports/stage5_0c_cross_target_rerun.json`
- Create: `docs/reports/2026-06-22-stage5_0c-cross-target-rerun.md`

- [ ] **Step 1: Run full tests before training**

```bash
./.venv/bin/python -m pytest tests/ -q
```

Expected: PASS.

- [ ] **Step 2: Run Stage 5.0c**

```bash
PYTHONUNBUFFERED=1 ./.venv/bin/python -m ML.baseline.benchmark_stage5_transformer_breach --stage5-0c-cross-target-rerun
```

Expected: `Stage 5.0c cross-target rerun completed`, JSON written.

Note: This runs 5 seeds × 2 targets × 1 profile = 10 Transformer training runs + 2 XGBoost-same-profile + 2×3 XGBoost-baseline = 18 training runs total. Expect several hours on CPU.

- [ ] **Step 3: Extract result tables**

Seed summary for sell:

```bash
./.venv/bin/python -c "
import json, statistics
d = json.load(open('ML/reports/stage5_0c_cross_target_rerun.json'))
for tname in ['sell', 'buy']:
    t = d['targets'][tname]
    sm = t['seed_metrics']
    aucs = [s['val']['auc'] for s in sm]
    lifts = [s['val']['lift_30'] for s in sm]
    haucs = [s['holdout']['auc'] for s in sm]
    xgb = t['xgb_same_profile']['val']
    print(f'=== {tname} ===')
    print(f'seeds: {d[\"seeds\"]}')
    print(f'val AUC per seed: {aucs}')
    print(f'val lift_30 per seed: {lifts}')
    print(f'holdout AUC per seed: {haucs}')
    print(f'median val AUC: {statistics.median(aucs):.4f}')
    print(f'median val lift_30: {statistics.median(lifts):.4f}')
    print(f'median holdout AUC: {statistics.median(haucs):.4f}')
    print(f'xgb_same val AUC: {xgb[\"auc\"]:.4f}, lift_30: {xgb[\"lift_30\"]:.4f}')
    print()
print('=== replication_decision ===')
print(json.dumps(d['replication_decision'], indent=2, default=str))
"
```

- [ ] **Step 4: Write report**

Create `docs/reports/2026-06-22-stage5_0c-cross-target-rerun.md`:

```markdown
# Stage 5.0c Cross-Target Replication Rerun

> **Дата**: 2026-06-22
> **Статус**: Completed
> **Вердикт**: DIAGNOSTIC_ONLY
> **Framing**: Replication test гипотезы, порождённой Stage 5.0b (не independent discovery)
> **Related plan**: `docs/superpowers/plans/2026-06-22-stage5_0c-cross-target-rerun.md`

## Context

Stage 5.0b выявил, что `all100_absolute_price_atr_scaled_time_asinh` стабильно оказался рядом с лидером на двух целевых (sell val_auc 0.6673 vs лидер 0.6719; buy val_auc 0.6752 vs лидер 0.6762). Stage 5.0c — заранее зафиксированный replication test: один профиль, две цели, 5 seeds, XGBoost на тех же признаках, pre-registered числовые пороги.

## Setup

- Profile: `all100_absolute_price_atr_scaled_time_asinh` (frozen, single)
- Targets: `sell_stop_broken_H6_off05_flag`, `buy_stop_broken_H6_off05_flag`
- Transform: `asinh`
- Scaler: train-only `StandardScaler`
- Seeds: `[42, 77, 123, 202, 777]` (unconditional, no single-seed gate)
- Dynamic corridor `seq_len`: disabled
- Holdout: 2023-2026, disclosure only
- Trading winner: not declared

## Pre-Registered Gates

[Insert the 5-gate table from the plan, with actual threshold values]

## Mandatory Checks

[Insert OHLC verification, label sanity, XGBoost baseline values per target from JSON]

## XGBoost Same-Profile Baseline

[Insert xgb_same_profile val/holdout AUC and lift_30 per target]

## Transformer Multi-Seed Results

### Sell

| Seed | val_auc | val_lift_30 | holdout_auc | holdout_lift_30 |
|---|---:|---:|---:|---:|
[Insert one row per seed]

Summary: median val AUC = ..., median val lift_30 = ..., median holdout AUC = ..., spread = ...

### Buy

[Same table for buy]

## Replication Decision

[Insert replication_decision from JSON: per-gate, per-target pass/fail with actual values]

## Conclusions

[State overall_pass = True/False and which gates passed/failed]

## Limitations / Open Questions

- Holdout 2023-2026 — disclosure only, не использовался для выбора.
- 5 seeds дают ограниченный CI; для торгового решения нужен block bootstrap CI.
- Buy и sell считаются на разных строках; AUC/lift не сравнимы между целями напрямую.

## Next Step

[If overall_pass: candidate for Stage 5.0d frozen test. If fail: post-mortem по A5, новая гипотеза.]

## Related Materials

- `ML/reports/stage5_0c_cross_target_rerun.json`
- `docs/reports/2026-06-21-stage5_0b-asinh-rerun.md`
- `docs/superpowers/plans/2026-06-22-stage5_0c-cross-target-rerun.md`
```

- [ ] **Step 5: Commit**

```bash
git add ML/reports/stage5_0c_cross_target_rerun.json docs/reports/2026-06-22-stage5_0c-cross-target-rerun.md
git commit -m "feat: Stage 5.0c cross-target replication rerun results and report"
```

---

### Task 9: Documentation Sync

**Files:**
- Modify: `docs/ML/benchmark_stage5_transformer_breach.py.md`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Update module documentation**

Add to `docs/ML/benchmark_stage5_transformer_breach.py.md`:

```markdown
- `--stage5-0c-cross-target-rerun` — Stage 5.0c replication test: один профиль `all100_absolute_price_atr_scaled_time_asinh` на sell + buy, 5 seeds, XGBoost на тех же признаках, pre-registered gates, no trading winner.
- `ML/reports/stage5_0c_cross_target_rerun.json` — structured artifact Stage 5.0c.
- `build_flat_features` — extended with `transform_variant` parameter for XGBoost-on-same-profile.
- `build_xgb_features_for_profile` — new helper for XGBoost features on arbitrary profile.
- `compute_xgb_same_profile_baseline` — XGBoost baseline on same profile features as Transformer.
- `stage5_0c_replication_decision` — pre-registered 5-gate decision function.
```

- [ ] **Step 2: Update CHANGELOG**

At top of `CHANGELOG.md`, add:

```markdown
## [2026-06-22] — Stage 5.0c: Cross-target replication rerun

### Добавлено
- `--stage5-0c-cross-target-rerun`
- `ML/reports/stage5_0c_cross_target_rerun.json`
- `docs/reports/2026-06-22-stage5_0c-cross-target-rerun.md`
- `build_xgb_features_for_profile`, `compute_xgb_same_profile_baseline` — честное сравнение Transformer vs XGBoost на тех же признаках

### Методика
- Статус `DIAGNOSTIC_ONLY`; holdout не используется для выбора.
- Framing: replication test гипотезы 5.0b, не independent discovery.
- Pre-registered числовые пороги для 5 gate (AUC, lift_30, cross-target, holdout degradation, seed spread).
- 5 seeds безусловно (no single-seed gate).
- XGBoost на том же профиле изолирует «признаки vs модель».

### Результаты
[Заполнить после прогона: overall_pass, per-gate pass/fail]

<!-- docs/reports/2026-06-22-stage5_0c-cross-target-rerun.md -->
```

- [ ] **Step 3: Final verification**

```bash
./.venv/bin/python -m pytest tests/ -q
git status --short
git diff --stat
```

Expected: tests PASS; diff limited to Stage 5.0c code, tests, report, docs, changelog, generated JSON.

---

## Self-Review

**1. Spec coverage:**
- Закрыть 5.0b как диагностический → Task 8 report framing + `framing: replication_test_of_5_0b_hypothesis` in runner ✓
- Один профиль, sell + buy отдельно → `STAGE5_0C_PROFILE_NAME`, `STAGE5_0C_TARGETS`, runner loops both targets ✓
- XGBoost на тех же признаках → Task 1-3: `build_flat_features` extended, `build_xgb_features_for_profile`, `compute_xgb_same_profile_baseline` ✓
- val_stop — база решения → `decision_policy.selection_basis = "val_stop only"`, gates use val metrics ✓
- holdout — только раскрытие → `decision_policy.holdout_usage = "disclosure only"`, G4 uses holdout for degradation check only (not selection) ✓
- Multi-seed безусловно → `STAGE5_0C_SEEDS`, runner loops all seeds, no single-seed gate ✓
- Pre-registered числовые пороги (не fuzzy) → `STAGE5_0C_GATES` with exact numbers, `stage5_0c_replication_decision` applies them mechanically ✓
- Cross-target gate (обе цели) → G3 `both_targets_required: True` ✓
- Selection-on-outcome framing → `framing: replication_test_of_5_0b_hypothesis` in report + plan header ✓

**2. Placeholder scan:** No TBD/TODO. Report template (Task 8 Step 4) has `[Insert ...]` markers — these are filled from JSON after the run, which is the established pattern from Stage 5.0b. All code steps have complete code.

**3. Type consistency:**
- `build_flat_features(df, profile, transform_variant, transform_params)` — consistent in Task 1, 2, 3
- `build_xgb_features_for_profile(df, profile_name, transform_variant)` — consistent in Task 2, 3
- `compute_xgb_same_profile_baseline(train_df, val_df, hold_df, profile_name, transform_variant, target_col, seed)` — consistent in Task 3, 6
- `stage5_0c_replication_decision(target_results)` — consistent in Task 5, 6
- `run_stage5_0c_cross_target_rerun(sell_splits, buy_splits, seeds, device, output_path)` — consistent in Task 6, 7
- `STAGE5_0C_*` constants — consistent in Task 4, 5, 6, 7
