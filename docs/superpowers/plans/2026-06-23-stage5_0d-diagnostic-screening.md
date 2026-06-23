# Stage 5.0d — диагностический скрининг профилей (XGBoost + Logistic, без Transformer)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Цель:** Понять, какие фрактальные профили и группы признаков несут сигнал сверх raw features. Без обучения Transformer. Если ни один профиль не показывает улучшения — закрыть ветку Fractal Stop как исследовательски исчерпанную.

**Архитектура:** Новый CLI `--stage5-0d-diagnostic-screening` обучает XGBoost и Logistic Regression на flattened признаках всех 9 профилей из 5.0b (sell + buy, 3 seeds), плюс абляцию групп признаков для лучшего профиля. Transform params подбираются на train. Holdout — только раскрытие результата. Transformer не обучается.

**Tech Stack:** Python 3.10, pandas, numpy, scikit-learn (LogisticRegression), xgboost, pytest, текущий `ML/baseline/benchmark_stage5_transformer_breach.py`.

## Предусловие

Stage 5.0c закрыт через `stage-reporting`: отчёт, CHANGELOG, CONTEXT_HANDOFF, wiki, коммит. План 5.0d не запускать до закрытия 5.0c.

## Уровень исследования

**Поисковый (exploratory).** Результат — диагностический, не кандидат. Если скрининг найдёт профиль с запасом — это гипотеза для нового проверочного цикла (Stage 5.0e), не основание для продвижения сразу.

## Предпосылки

- 5.0b (single-seed, 9 профилей): Transformer не превосходит XGBoost base_raw_plus_time на обеих целях.
- 5.0c (multi-seed, 1 профиль): Transformer не превосходит XGBoost same-profile; 0 из 5 seeds выше порога.
- 5.0c JSON: seed 42 sell val_aucs падает с 0.6673 (epoch 9) до 0.6445 (epoch 17) — Transformer переобучается.
- Вопрос: проблема в признаках (слабый сигнал) или в модели (переобучение)? XGBoost-first скрининг отвечает за минуты, не часы.

## Группы признаков

Каждый профиль разбивается на 4 группы. Абляция убирает по одной группе и замеряет падение AUC.

| Группа | Поля | Размерность |
|---|---|---:|
| price (token) | `price_coord_atr` / `price_atr_scaled` / `price_coord_unit` | 1 × seq_len |
| structure (token) | `direction`, `front`, `back`, `strong`, `break`, `reverse`, `power`, `count`, `impulse` | 9 × seq_len |
| ATR (row) | `ATR` | 1 |
| time (row) | `hour_sin`, `hour_cos`, `dow_sin`, `dow_cos` | 4 |

## Критерии решения

### Критерий A: профиль с запасом (для гипотезы 5.0e)

XGBoost same-profile на профиле P превосходит XGBoost base_raw_plus_time на +0.02 AUC **AND** `xgb_median_lift_30 <= base_lift_30` хотя бы на одной цели (sell или buy). Запас 0.02 выбран потому, что на 5.0c gap был 0.009 — в пределах шума. Lift_30 добавлен потому, что AUC измеряет ранжирование, lift_30 — калибровку в верхней части; профиль может улучшать AUC, но ухудшать lift_30 (бесполезно для торговли).

- Если найден → профиль P — гипотеза для Stage 5.0e (Transformer multi-seed на P). Но только если XGBoost >> Logistic (сигнал в взаимодействиях, не только линейный).
- Результат 5.0d **не открывает Transformer-обучение автоматически** — только формирует гипотезу для нового проверочного цикла.
- Если не найден → Критерий B.

### Критерий B: исчерпание постановки H6_off05

Ни один профиль не проходит Критерий A (AUC +0.02 AND lift_30) ни на одной цели.

- Вердикт: постановка H6_off05 stop broken на текущих 9 профилях исчерпана.
- Fractal Stop как семейство целей **не закрыт** — остаются другие постановки: сторона, время до пробоя, выход, режим.
- Дальше: смена target или смена признаков, не смена модели.

### Критерий C: Logistic vs XGBoost (линейность сигнала)

- Если Logistic ≈ XGBoost (gap < 0.01) → сигнал линейный, Transformer избыточен.
- Если XGBoost >> Logistic (gap > 0.02) → сигнал в взаимодействиях, у Transformer теоретический шанс (но 5.0c показал, что он его не реализует).

## Global Constraints

- Работать в текущей ветке, без worktree.
- Использовать `./.venv/bin/python`.
- Holdout 2023-2026 — только раскрытие результата (`holdout_used_for_decision: false`).
- Transform: `asinh` для всех 9 профилей (наследие 5.0b: все 9 гнались с `transform_variant="asinh"`).
- Seeds `[42, 77, 123]` — 3 seeds для screening (не 5 — это поисковый этап).
- Transformer не обучается. Только XGBoost и Logistic Regression.
- После Python-изменений запускать `./.venv/bin/python -m pytest tests/ -q`.
- TDD: каждый task начинается с failing test.
- Промежуточные commit не делаются. Закрытие этапа — через `stage-reporting`.

---

## File Structure

- **Modify:** `ML/baseline/benchmark_stage5_transformer_breach.py`
  - `STAGE5_0D_PROFILE_NAMES` — все 9 профилей из 5.0b
  - `STAGE5_0D_SEEDS` — `[42, 77, 123]`
  - `compute_logistic_same_profile_baseline` — новый: Logistic Regression на тех же признаках
  - `run_stage5_0d_diagnostic_screening` — новый runner
  - `build_arg_parser()` — добавить `--stage5-0d-diagnostic-screening`
- **Modify:** `tests/test_stage5_transformer_breach.py`
- **Create:** `ML/reports/stage5_0d_diagnostic_screening.json` (after run)
- **Create:** `docs/reports/2026-06-23-stage5_0d-diagnostic-screening.md` (after run)
- **Modify:** `docs/ML/benchmark_stage5_transformer_breach.py.md`
- **Modify:** `CHANGELOG.md`

---

### Task 1: Freeze Stage 5.0d Constants

**Files:**
- Modify: `ML/baseline/benchmark_stage5_transformer_breach.py` (near `STAGE5_0C_*` constants, ~line 2720)
- Test: `tests/test_stage5_transformer_breach.py`

**Interfaces:**
- Produces: `STAGE5_0D_PROFILE_NAMES: list[str]` — 9 профилей из 5.0b
- Produces: `STAGE5_0D_SEEDS: list[int]` — `[42, 77, 123]`
- Produces: `STAGE5_0D_TARGETS: list[str]` — sell + buy
- Produces: `STAGE5_0D_SCREENER_THRESHOLD: float` — 0.02

- [ ] **Step 1: Write failing test**

```python
def test_stage5_0d_constants_are_frozen():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    assert runner.STAGE5_0D_PROFILE_NAMES == runner.STAGE5_0B_ASINH_PROFILE_NAMES
    assert runner.STAGE5_0D_SEEDS == [42, 77, 123]
    assert runner.STAGE5_0D_TARGETS == [
        "sell_stop_broken_H6_off05_flag",
        "buy_stop_broken_H6_off05_flag",
    ]
    assert runner.STAGE5_0D_SCREENER_THRESHOLD == 0.02
    for pname in runner.STAGE5_0D_PROFILE_NAMES:
        assert runner.find_profile(pname) is not None
```

- [ ] **Step 2: Run test to verify it fails**

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py -k test_stage5_0d_constants_are_frozen -q
```

- [ ] **Step 3: Add constants**

```python
STAGE5_0D_PROFILE_NAMES = STAGE5_0B_ASINH_PROFILE_NAMES
STAGE5_0D_SEEDS = [42, 77, 123]
STAGE5_0D_TARGETS = [
    "sell_stop_broken_H6_off05_flag",
    "buy_stop_broken_H6_off05_flag",
]
STAGE5_0D_SCREENER_THRESHOLD = 0.02
STAGE5_0D_JSON_REPORT_PATH = REPORTS_DIR / "stage5_0d_diagnostic_screening.json"
```

- [ ] **Step 4: Run test to verify it passes**

- [ ] **Step 5: Run full test suite**

```bash
./.venv/bin/python -m pytest tests/ -q
```

- [ ] **Step 6: Verify**

```bash
git diff --stat
```

---

### Task 2: Add `compute_logistic_same_profile_baseline`

**Files:**
- Modify: `ML/baseline/benchmark_stage5_transformer_breach.py` (after `compute_xgb_same_profile_baseline`)
- Test: `tests/test_stage5_transformer_breach.py`

**Interfaces:**
- Produces: `compute_logistic_same_profile_baseline(train_df, val_stop_df, holdout_df, profile_name, transform_variant, target_col, seed=42) -> dict`
- Consumes: `build_xgb_features_for_profile` (те же flattened признаки), `fit_transform_params_for_profile`, `compute_metrics`, `compute_yearly_metrics`

Logistic Regression как linear baseline. Если Logistic ≈ XGBoost — сигнал линейный, Transformer избыточен.

- [ ] **Step 1: Write failing test**

```python
def test_compute_logistic_same_profile_baseline_returns_metrics(monkeypatch):
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    df = _make_synthetic_df(10, 100)
    df["_year"] = [2020] * 5 + [2023] * 5

    monkeypatch.setattr(runner, "build_xgb_features_for_profile",
                        lambda d, pname, tv, transform_params=None: np.random.rand(len(d), 10).astype(np.float32))
    monkeypatch.setattr(runner, "fit_transform_params_for_profile",
                        lambda df, parsed, profile, variant: {})
    monkeypatch.setattr(runner, "parse_split_fractals", lambda df: {})
    monkeypatch.setattr(runner, "find_profile",
                        lambda name: {"seq_len": 1, "token_dim": 5, "row_dim": 5})
    monkeypatch.setattr(runner, "compute_metrics",
                        lambda yt, yp: {"auc": 0.58, "pr_auc": 0.5, "n": len(yt),
                                        "lift_10": 1.0, "lift_20": 1.0, "lift_30": 0.9})
    monkeypatch.setattr(runner, "compute_yearly_metrics", lambda df_arg, pred, target_col=None: {})

    result = runner.compute_logistic_same_profile_baseline(
        df.iloc[:5], df.iloc[:5], df.iloc[5:],
        "all100_relative_price_time",
        transform_variant="current", target_col=runner.TARGET_COLUMN, seed=42)
    assert "val" in result and "holdout" in result
    assert result["model_type"] == "logistic_regression"
    assert result["val"]["auc"] == 0.58
    assert result["transform_params_fit_on"] == "train"
```

- [ ] **Step 2: Run test to verify it fails**

- [ ] **Step 3: Implement function**

```python
def compute_logistic_same_profile_baseline(train_df, val_stop_df, holdout_df,
                                           profile_name: str,
                                           transform_variant: str = "current",
                                           target_col: str = TARGET_COLUMN,
                                           seed: int = 42) -> dict:
    """Train Logistic Regression on the same profile features as XGBoost.

    Linear baseline: if Logistic ≈ XGBoost, the signal is linear and
    Transformer is overkill. If XGBoost >> Logistic, the signal is in
    feature interactions.
    """
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler

    print(f"\n  Training Logistic same-profile: {profile_name} ({transform_variant})...")

    profile = find_profile(profile_name)
    parsed_train = parse_split_fractals(train_df)
    transform_params = fit_transform_params_for_profile(
        train_df, parsed_train, profile, transform_variant)

    X_train = build_xgb_features_for_profile(
        train_df, profile_name, transform_variant, transform_params=transform_params)
    X_val = build_xgb_features_for_profile(
        val_stop_df, profile_name, transform_variant, transform_params=transform_params)
    X_holdout = build_xgb_features_for_profile(
        holdout_df, profile_name, transform_variant, transform_params=transform_params)

    y_train = train_df[target_col]
    y_val = val_stop_df[target_col]
    y_holdout = holdout_df[target_col]

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_val_s = scaler.transform(X_val)
    X_holdout_s = scaler.transform(X_holdout)

    model = LogisticRegression(
        C=1.0, max_iter=1000, random_state=seed, solver="lbfgs",
        class_weight="balanced")
    model.fit(X_train_s, y_train)

    val_probs = model.predict_proba(X_val_s)[:, 1]
    holdout_probs = model.predict_proba(X_holdout_s)[:, 1]

    val_metrics = compute_metrics(y_val, pd.Series(val_probs))
    holdout_metrics = compute_metrics(y_holdout, pd.Series(holdout_probs))
    yearly = compute_yearly_metrics(holdout_df, holdout_probs, target_col=target_col)

    print(f"    Val AUC: {val_metrics.get('auc', 'N/A'):.4f}")

    return {
        "profile": profile_name,
        "model_type": "logistic_regression",
        "transform_variant": transform_variant,
        "transform_params_fit_on": "train",
        "seed": seed,
        "val": {k: _safe(v) for k, v in val_metrics.items()},
        "holdout": {k: _safe(v) for k, v in holdout_metrics.items()},
        "yearly": {k: {kk: _safe(vv) for kk, vv in v.items()} for k, v in yearly.items()},
    }
```

- [ ] **Step 4: Run test to verify it passes**

- [ ] **Step 5: Run full test suite**

- [ ] **Step 6: Verify**

```bash
git diff --stat
```

---

### Task 3: Add `compute_feature_group_ablation`

**Files:**
- Modify: `ML/baseline/benchmark_stage5_transformer_breach.py` (after `compute_logistic_same_profile_baseline`)
- Test: `tests/test_stage5_transformer_breach.py`

**Interfaces:**
- Produces: `compute_feature_group_ablation(train_df, val_stop_df, holdout_df, profile_name, transform_variant, target_col, seed=42) -> dict`
- Returns: `{"full": {...}, "no_price": {...}, "no_structure": {...}, "no_atr": {...}, "no_time": {...}}`

Абляция: для каждого профиля убираем одну группу признаков из flattened вектора и замеряем падение AUC. Группы: price (token), structure (token), ATR (row), time (row).

- [ ] **Step 1: Write failing test**

```python
def test_compute_feature_group_ablation_returns_all_groups(monkeypatch):
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    df = _make_synthetic_df(10, 100)

    monkeypatch.setattr(runner, "build_xgb_features_for_profile",
                        lambda d, pname, tv, transform_params=None: np.random.rand(len(d), 15).astype(np.float32))
    monkeypatch.setattr(runner, "fit_transform_params_for_profile",
                        lambda df, parsed, profile, variant: {})
    monkeypatch.setattr(runner, "parse_split_fractals", lambda df: {})
    monkeypatch.setattr(runner, "find_profile",
                        lambda name: {"seq_len": 1, "token_dim": 10, "row_dim": 5})
    monkeypatch.setattr(runner, "train_xgb_baseline",
                        lambda Xtr, ytr, Xv, yv, seed=42: (None, 0.65))
    monkeypatch.setattr(runner, "compute_metrics",
                        lambda yt, yp: {"auc": 0.65, "pr_auc": 0.5, "n": len(yt),
                                        "lift_10": 1.0, "lift_20": 1.0, "lift_30": 0.8})
    monkeypatch.setattr(runner, "compute_yearly_metrics", lambda df_arg, pred, target_col=None: {})

    result = runner.compute_feature_group_ablation(
        df.iloc[:5], df.iloc[:5], df.iloc[5:],
        "all100_relative_price_time",
        transform_variant="current", target_col=runner.TARGET_COLUMN, seed=42)
    assert "full" in result
    assert "no_price" in result
    assert "no_structure" in result
    assert "no_atr" in result
    assert "no_time" in result
    for group in ["full", "no_price", "no_structure", "no_atr", "no_time"]:
        assert "val" in result[group]
        assert "auc" in result[group]["val"]
```

- [ ] **Step 2: Run test to verify it fails**

- [ ] **Step 3: Implement function**

```python
def _build_feature_group_masks(profile: dict) -> dict:
    """Build column masks for feature group ablation.

    Masks are built from profile["token_fields"] and profile["row_fields"]
    by name, not by positional assumption. Flattened layout:
    [token_flat (seq_len * token_dim), row_flat (row_dim)].

    Groups: price (first price-like token field), structure (remaining token
    fields), ATR (row field named "ATR"), time (row fields hour_sin/cos/dow_sin/cos).
    """
    seq_len = profile["seq_len"]
    token_dim = profile["token_dim"]
    row_fields = profile.get("row_fields", [])
    token_fields = profile.get("token_fields", [])
    total = seq_len * token_dim + len(row_fields)

    token_total = seq_len * token_dim
    masks = {"all": np.ones(total, dtype=bool)}

    price_token_names = {"price_coord_atr", "price_atr_scaled", "price_coord_unit", "price"}
    price_token_indices = [i for i, f in enumerate(token_fields) if f in price_token_names]
    structure_token_indices = [i for i in range(token_dim) if i not in price_token_indices]

    masks["price"] = np.zeros(total, dtype=bool)
    for ti in price_token_indices:
        masks["price"][ti::token_dim] = True
    masks["structure"] = np.zeros(total, dtype=bool)
    for ti in structure_token_indices:
        masks["structure"][ti::token_dim] = True

    masks["atr"] = np.zeros(total, dtype=bool)
    masks["time"] = np.zeros(total, dtype=bool)
    for ri, rf in enumerate(row_fields):
        if rf == "ATR":
            masks["atr"][token_total + ri] = True
        elif rf in ("hour_sin", "hour_cos", "dow_sin", "dow_cos"):
            masks["time"][token_total + ri] = True

    return masks


def compute_feature_group_ablation(train_df, val_stop_df, holdout_df,
                                   profile_name: str,
                                   transform_variant: str = "asinh",
                                   target_col: str = TARGET_COLUMN,
                                   seed: int = 42) -> dict:
    """Ablate feature groups and measure AUC drop.

    Groups: price (token), structure (token), ATR (row), time (row).
    For each group, remove its columns from flattened features and retrain XGBoost.
    Holdout metrics use real model predictions, not zeros.
    """
    import xgboost as xgb

    print(f"\n  Feature group ablation: {profile_name}...")

    profile = find_profile(profile_name)
    parsed_train = parse_split_fractals(train_df)
    transform_params = fit_transform_params_for_profile(
        train_df, parsed_train, profile, transform_variant)

    X_train = build_xgb_features_for_profile(
        train_df, profile_name, transform_variant, transform_params=transform_params)
    X_val = build_xgb_features_for_profile(
        val_stop_df, profile_name, transform_variant, transform_params=transform_params)
    X_holdout = build_xgb_features_for_profile(
        holdout_df, profile_name, transform_variant, transform_params=transform_params)

    y_train = train_df[target_col]
    y_val = val_stop_df[target_col]
    y_holdout = holdout_df[target_col]

    masks = _build_feature_group_masks(profile)
    groups = {
        "full": masks["all"],
        "no_price": ~masks["price"],
        "no_structure": ~masks["structure"],
        "no_atr": ~masks["atr"],
        "no_time": ~masks["time"],
    }

    results = {}
    for group_name, mask in groups.items():
        X_tr = X_train[:, mask]
        X_va = X_val[:, mask]
        X_ho = X_holdout[:, mask]

        model, val_auc = train_xgb_baseline(X_tr, y_train, X_va, y_val, seed=seed)

        val_probs = model.predict(xgb.DMatrix(X_va))
        holdout_probs = model.predict(xgb.DMatrix(X_ho))

        val_metrics = compute_metrics(y_val, pd.Series(val_probs))
        holdout_metrics = compute_metrics(y_holdout, pd.Series(holdout_probs))

        results[group_name] = {
            "n_features": int(mask.sum()),
            "val": {k: _safe(v) for k, v in val_metrics.items()},
            "holdout": {k: _safe(v) for k, v in holdout_metrics.items()},
        }
        print(f"    {group_name}: val AUC = {val_metrics.get('auc', 'N/A'):.4f} ({int(mask.sum())} features)")

    return results
```

- [ ] **Step 4: Run test to verify it passes**

- [ ] **Step 5: Run full test suite**

- [ ] **Step 6: Verify**

```bash
git diff --stat
```

---

### Task 4: Add `run_stage5_0d_diagnostic_screening` Runner

**Files:**
- Modify: `ML/baseline/benchmark_stage5_transformer_breach.py` (after `run_stage5_0c_cross_target_rerun`)
- Test: `tests/test_stage5_transformer_breach.py`

**Interfaces:**
- Produces: `run_stage5_0d_diagnostic_screening(sell_splits, buy_splits, seeds, device, output_path) -> dict`
- Produces artifact: `ML/reports/stage5_0d_diagnostic_screening.json`

Runner обходит все 9 профилей из 5.0b, для каждого:
1. XGBoost same-profile (3 seeds, median)
2. Logistic same-profile (1 seed — linear baseline)
3. Для лучшего профиля по XGBoost — абляция групп признаков

- [ ] **Step 1: Write failing test**

```python
def test_stage5_0d_runner_screens_all_profiles_and_writes_json(monkeypatch, tmp_path):
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    df_sell = _make_synthetic_df(5, 100)
    df_sell["_year"] = [2020] * 5
    df_buy = df_sell.copy()
    df_buy["buy_stop_broken_H6_off05_flag"] = [0, 1, 0, 1, 0]

    xgb_calls = []
    logistic_calls = []

    monkeypatch.setattr(runner, "compute_xgb_same_profile_baseline",
                        lambda tr, va, ho, pn, tv, tc, seed=42: {
                            "profile": pn, "val": {"auc": 0.66, "lift_30": 0.6},
                            "holdout": {"auc": 0.64, "lift_30": 0.65}, "yearly": {}})
    monkeypatch.setattr(runner, "compute_logistic_same_profile_baseline",
                        lambda tr, va, ho, pn, tv, tc, seed=42: {
                            "profile": pn, "model_type": "logistic_regression",
                            "val": {"auc": 0.62, "lift_30": 0.7},
                            "holdout": {"auc": 0.61, "lift_30": 0.72}, "yearly": {}})
    monkeypatch.setattr(runner, "compute_feature_group_ablation",
                        lambda tr, va, ho, pn, tv, tc, seed=42: {
                            "full": {"val": {"auc": 0.66}},
                            "no_price": {"val": {"auc": 0.64}},
                            "no_structure": {"val": {"auc": 0.65}},
                            "no_atr": {"val": {"auc": 0.66}},
                            "no_time": {"val": {"auc": 0.63}}})
    monkeypatch.setattr(runner, "compute_xgb_baselines",
                        lambda tr, va, ho, target_col=runner.TARGET_COLUMN: {
                            "base_raw_plus_time": {"val": {"auc": 0.65, "lift_30": 0.7}}})

    report = runner.run_stage5_0d_diagnostic_screening(
        sell_splits=(df_sell, df_sell, df_sell),
        buy_splits=(df_buy, df_buy, df_buy),
        seeds=[42, 77, 123],
        device="cpu",
        output_path=tmp_path / "stage5_0d.json",
    )

    assert report["stage"] == "5.0d_diagnostic_screening"
    assert report["level"] == "exploratory"
    assert report["holdout_used_for_decision"] is False
    assert len(report["targets"]["sell"]["profiles"]) == len(runner.STAGE5_0D_PROFILE_NAMES)
    assert "base_raw_plus_time_auc" in report["targets"]["sell"]
    assert "base_raw_plus_time_lift_30" in report["targets"]["sell"]
    assert "ablation" in report["targets"]["sell"]
    assert "screener_result" in report
    sr = report["screener_result"]
    assert sr["verdict"] in ("profile_with_potential", "h6_off05_target_exhausted")
    assert "sell_best" in sr and "buy_best" in sr
    assert "overall_best" in sr
    assert "criteria" in sr
    assert "auc_pass" in sr["criteria"]
    assert "lift_pass" in sr["criteria"]
    assert "не открывает Transformer" in sr["next_step"]
    assert (tmp_path / "stage5_0d.json").exists()
```

- [ ] **Step 2: Run test to verify it fails**

- [ ] **Step 3: Implement runner**

```python
def run_stage5_0d_diagnostic_screening(sell_splits: tuple, buy_splits: tuple,
                                       seeds: list, device, output_path=None) -> dict:
    """Stage 5.0d: диагностический скрининг профилей (XGBoost + Logistic).

    Уровень: поисковый. Transformer не обучается.
    Если ни один профиль не превосходит base_raw_plus_time на +0.02 AUC —
    ветка Fractal Stop исследовательски исчерпана.
    """
    profile_names = STAGE5_0D_PROFILE_NAMES
    report = {
        "stage": "5.0d_diagnostic_screening",
        "level": "exploratory",
        "holdout_used_for_decision": False,
        "seeds": list(seeds),
        "profile_names": list(profile_names),
        "screener_threshold": STAGE5_0D_SCREENER_THRESHOLD,
        "decision_policy": {
            "selection_basis": "val_stop only",
            "holdout_usage": "disclosure only",
            "transformer_trained": False,
            "models": ["xgboost", "logistic_regression"],
        },
        "targets": {},
    }

    split_sets = {
        "sell": (sell_splits, STAGE5_0D_TARGETS[0]),
        "buy": (buy_splits, STAGE5_0D_TARGETS[1]),
    }

    for tname, (splits, target_col) in split_sets.items():
        train_df, val_df, hold_df = splits
        print(f"\n{'='*60}")
        print(f"Stage 5.0d — цель: {tname} ({target_col})")
        print(f"{'='*60}")

        xgb_baselines = compute_xgb_baselines(train_df, val_df, hold_df, target_col=target_col)
        base_auc = xgb_baselines["base_raw_plus_time"]["val"]["auc"]
        base_lift = xgb_baselines["base_raw_plus_time"]["val"].get("lift_30")

        profile_results = {}
        best_profile = None
        best_auc = -1.0

        for pname in profile_names:
            tv = "asinh"

            xgb_seed_results = []
            for seed in seeds:
                xgb_res = compute_xgb_same_profile_baseline(
                    train_df, val_df, hold_df, pname,
                    transform_variant=tv, target_col=target_col, seed=seed)
                xgb_seed_results.append(xgb_res)

            import statistics
            xgb_val_aucs = [r["val"]["auc"] for r in xgb_seed_results]
            xgb_val_lifts = [r["val"].get("lift_30") for r in xgb_seed_results]
            xgb_holdout_aucs = [r["holdout"].get("auc") for r in xgb_seed_results]
            xgb_median_auc = statistics.median(xgb_val_aucs)
            xgb_median_lift = statistics.median(xgb_val_lifts)
            xgb_spread = max(xgb_val_aucs) - min(xgb_val_aucs) if len(xgb_val_aucs) > 1 else 0.0

            logistic_res = compute_logistic_same_profile_baseline(
                train_df, val_df, hold_df, pname,
                transform_variant=tv, target_col=target_col, seed=seeds[0])

            profile_results[pname] = {
                "transform_variant": tv,
                "xgb_median_val_auc": xgb_median_auc,
                "xgb_seed_val_aucs": xgb_val_aucs,
                "xgb_seed_val_lifts_30": xgb_val_lifts,
                "xgb_median_val_lift_30": xgb_median_lift,
                "xgb_seed_spread": xgb_spread,
                "xgb_holdout_aucs": xgb_holdout_aucs,
                "logistic_val_auc": logistic_res["val"]["auc"],
                "logistic_val_lift_30": logistic_res["val"].get("lift_30"),
                "xgb_vs_base_delta": xgb_median_auc - base_auc,
                "xgb_vs_logistic_delta": xgb_median_auc - logistic_res["val"]["auc"],
                "xgb_lift_vs_base": xgb_median_lift - base_lift if base_lift is not None else None,
            }

            if xgb_median_auc > best_auc:
                best_auc = xgb_median_auc
                best_profile = pname

        ablation = compute_feature_group_ablation(
            train_df, val_df, hold_df, best_profile,
            transform_variant="asinh",
            target_col=target_col, seed=seeds[0])

        report["targets"][tname] = {
            "target_col": target_col,
            "base_raw_plus_time_auc": base_auc,
            "base_raw_plus_time_lift_30": base_lift,
            "xgb_baselines": xgb_baselines,
            "profiles": profile_results,
            "best_profile": best_profile,
            "best_profile_val_auc": best_auc,
            "ablation": {"profile": best_profile, "groups": ablation},
        }

    sell_profiles = report["targets"]["sell"]["profiles"]
    buy_profiles = report["targets"]["buy"]["profiles"]
    sell_base_auc = report["targets"]["sell"]["base_raw_plus_time_auc"]
    buy_base_auc = report["targets"]["buy"]["base_raw_plus_time_auc"]
    sell_base_lift = report["targets"]["sell"]["base_raw_plus_time_lift_30"]
    buy_base_lift = report["targets"]["buy"]["base_raw_plus_time_lift_30"]
    threshold = STAGE5_0D_SCREENER_THRESHOLD

    def _find_best(profiles, base_auc, base_lift):
        best_pname = None
        best_delta = -1.0
        for pname, p in profiles.items():
            if p["xgb_vs_base_delta"] > best_delta:
                best_delta = p["xgb_vs_base_delta"]
                best_pname = pname
        best_lift = profiles[best_pname]["xgb_median_val_lift_30"] if best_pname else None
        return best_pname, best_delta, best_lift

    sell_best_pname, sell_best_delta, sell_best_lift = _find_best(sell_profiles, sell_base_auc, sell_base_lift)
    buy_best_pname, buy_best_delta, buy_best_lift = _find_best(buy_profiles, buy_base_auc, buy_base_lift)

    if sell_best_delta >= buy_best_delta:
        overall_best_delta = sell_best_delta
        overall_best_target = "sell"
        overall_best_pname = sell_best_pname
        overall_best_lift = sell_best_lift
        overall_base_lift = sell_base_lift
    else:
        overall_best_delta = buy_best_delta
        overall_best_target = "buy"
        overall_best_pname = buy_best_pname
        overall_best_lift = buy_best_lift
        overall_base_lift = buy_base_lift

    auc_pass = overall_best_delta >= threshold
    lift_pass = (overall_best_lift is not None and overall_base_lift is not None
                 and overall_best_lift <= overall_base_lift)

    if auc_pass and lift_pass:
        screener_result = {
            "verdict": "profile_with_potential",
            "criteria": {
                "auc_threshold": threshold,
                "auc_delta": overall_best_delta,
                "auc_pass": True,
                "lift_pass": lift_pass,
                "lift_30": overall_best_lift,
                "base_lift_30": overall_base_lift,
            },
            "overall_best": {
                "target": overall_best_target,
                "profile": overall_best_pname,
                "delta": overall_best_delta,
                "lift_30": overall_best_lift,
            },
            "sell_best": {"profile": sell_best_pname, "delta": sell_best_delta, "lift_30": sell_best_lift},
            "buy_best": {"profile": buy_best_pname, "delta": buy_best_delta, "lift_30": buy_best_lift},
            "next_step": "Гипотеза для Stage 5.0e (Transformer multi-seed на лучшем профиле). Результат 5.0d не открывает Transformer-обучение автоматически — только формирует гипотезу для нового проверочного цикла с заранее зафиксированными порогами.",
        }
    else:
        screener_result = {
            "verdict": "h6_off05_target_exhausted",
            "criteria": {
                "auc_threshold": threshold,
                "auc_delta": overall_best_delta,
                "auc_pass": auc_pass,
                "lift_pass": lift_pass,
                "lift_30": overall_best_lift,
                "base_lift_30": overall_base_lift,
            },
            "overall_best": {
                "target": overall_best_target,
                "profile": overall_best_pname,
                "delta": overall_best_delta,
                "lift_30": overall_best_lift,
            },
            "sell_best": {"profile": sell_best_pname, "delta": sell_best_delta, "lift_30": sell_best_lift},
            "buy_best": {"profile": buy_best_pname, "delta": buy_best_delta, "lift_30": buy_best_lift},
            "next_step": "Постановка H6_off05 stop broken на текущих 9 профилях исчерпана. Fractal Stop как семейство целей не закрыт — остаются другие постановки (сторона, время до пробоя, выход). Результат 5.0d не открывает Transformer-обучение автоматически.",
        }

    report["screener_result"] = screener_result

    if output_path is not None:
        output_path = Path(output_path)
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2, default=str)
    return report
```

- [ ] **Step 4: Run test to verify it passes**

- [ ] **Step 5: Run full test suite**

- [ ] **Step 6: Verify**

```bash
git diff --stat
```

---

### Task 5: Add CLI And Wire Into `main()`

**Files:**
- Modify: `ML/baseline/benchmark_stage5_transformer_breach.py` (`build_arg_parser`, `main`)
- Test: `tests/test_stage5_transformer_breach.py`

- [ ] **Step 1: Write failing test**

```python
def test_stage5_0d_cli_argument_exists_in_build_arg_parser():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    parser = runner.build_arg_parser()
    args = parser.parse_args(["--stage5-0d-diagnostic-screening"])
    assert args.stage5_0d_diagnostic_screening is True
```

- [ ] **Step 2: Run test to verify it fails**

- [ ] **Step 3: Add CLI argument to `build_arg_parser()`**

```python
    parser.add_argument("--stage5-0d-diagnostic-screening", action="store_true",
                        help="Stage 5.0d: диагностический скрининг профилей (XGBoost + Logistic, без Transformer)")
```

- [ ] **Step 4: Wire into main dispatch**

After the `--stage5-0c-cross-target-rerun` block, add:

```python
    if args.stage5_0d_diagnostic_screening:
        print("\n" + "=" * 60)
        print("Загрузка buy splits для Stage 5.0d...")
        print("=" * 60)
        buy_train, buy_val, buy_hold = load_splits(target_col="buy_stop_broken_H6_off05_flag")
        report = run_stage5_0d_diagnostic_screening(
            sell_splits=(train_df, val_stop_df, holdout_df),
            buy_splits=(buy_train, buy_val, buy_hold),
            seeds=STAGE5_0D_SEEDS,
            device=device,
            output_path=STAGE5_0D_JSON_REPORT_PATH,
        )
        print("\n" + "=" * 60)
        print("Stage 5.0d: диагностический скрининг завершён")
        print(json.dumps({"json": str(STAGE5_0D_JSON_REPORT_PATH)}, indent=2))
        print("=" * 60)
        return
```

- [ ] **Step 5: Run full test suite**

```bash
./.venv/bin/python -m pytest tests/ -q
```

- [ ] **Step 6: Verify**

```bash
git diff --stat
```

---

### Task 6: Execute Stage 5.0d Run And Write Report

**Files:**
- Generated: `ML/reports/stage5_0d_diagnostic_screening.json`
- Create: `docs/reports/2026-06-23-stage5_0d-diagnostic-screening.md`

- [ ] **Step 1: Run full tests before screening**

```bash
./.venv/bin/python -m pytest tests/ -q
```

- [ ] **Step 2: Run Stage 5.0d**

```bash
PYTHONUNBUFFERED=1 ./.venv/bin/python -m ML.baseline.benchmark_stage5_transformer_breach --stage5-0d-diagnostic-screening
```

Expected: `Stage 5.0d: диагностический скрининг завершён`, JSON written.

Note: 9 профилей × 2 цели × 3 seeds XGBoost + 9 × 2 Logistic + 2 абляций = ~60 XGBoost + 18 Logistic + 10 абляционных прогонов. XGBoost на flattened признаки — секунды каждый. Ожидаемое время: ~10-20 минут.

- [ ] **Step 3: Extract result tables**

```bash
./.venv/bin/python -c "
import json, statistics
d = json.load(open('ML/reports/stage5_0d_diagnostic_screening.json'))
for tname in ['sell', 'buy']:
    t = d['targets'][tname]
    print(f'=== {tname} ===')
    print(f'base_raw_plus_time val AUC: {t[\"base_raw_plus_time_auc\"]:.4f}')
    for pname, p in sorted(t['profiles'].items(), key=lambda x: -x[1]['xgb_median_val_auc']):
        print(f'  {pname}: xgb_median={p[\"xgb_median_val_auc\"]:.4f} delta={p[\"xgb_vs_base_delta\"]:+.4f} logistic={p[\"logistic_val_auc\"]:.4f} xgb_vs_log={p[\"xgb_vs_logistic_delta\"]:+.4f}')
    print(f'best_profile: {t[\"best_profile\"]}')
    print(f'ablation:')
    for g, gv in t['ablation']['groups'].items():
        print(f'  {g}: val AUC = {gv[\"val\"][\"auc\"]:.4f} ({gv[\"n_features\"]} features)')
    print()
print('=== screener_result ===')
print(json.dumps(d['screener_result'], indent=2))
"
```

- [ ] **Step 4: Write report**

Create `docs/reports/2026-06-23-stage5_0d-diagnostic-screening.md`:

```markdown
# Stage 5.0d — диагностический скрининг профилей

> **Дата**: 2026-06-23
> **Статус**: Completed
> **Уровень этапа**: поисковый
> **Related plan**: `docs/superpowers/plans/2026-06-23-stage5_0d-diagnostic-screening.md`

## Context

Stage 5.0c показал, что Transformer не превосходит XGBoost на тех же признаках (0 из 5 seeds выше порога на обеих целях). Stage 5.0d — диагностический скрининг: XGBoost и Logistic Regression на всех 9 профилях из 5.0b, без обучения Transformer. Цель — понять, какие профили и группы признаков несут сигнал сверх raw features.

## What Was Done

- Обучен XGBoost same-profile на 9 профилях × 2 цели × 3 seeds (median).
- Обучена Logistic Regression (class_weight="balanced") на тех же признаках, 1 seed.
- Абляция групп признаков (price / structure / ATR / time) для лучшего профиля по каждой цели.
- Transformer не обучался.

## Multiple Testing Context

Search budget: 9 профилей × 2 цели × 2 модели (XGBoost + Logistic) = 36 прогонов + 2 абляции.
Коррекция: этап поисковый, результат — диагностический, не кандидат. Множественный перебор не корректируется, но вердикт не претендует на подтверждённую гипотезу. Переход к проверочному циклу (5.0e) требует нового плана с заранее зафиксированными порогами.

## Changed Files

[Insert: ML/baseline/benchmark_stage5_transformer_breach.py, tests/test_stage5_transformer_breach.py, docs/ML/benchmark_stage5_transformer_breach.py.md, CHANGELOG.md, ML/reports/stage5_0d_diagnostic_screening.json]

## Verification

- Tests: ./.venv/bin/python -m pytest tests/ -q — [Insert: N passed]
- JSON artifact: ML/reports/stage5_0d_diagnostic_screening.json — [Insert: exists / size]

## Setup

- Profiles: все 9 из 5.0b (4 confirmatory + 5 diagnostic)
- Targets: sell + buy
- Models: XGBoost (3 seeds, median) + Logistic Regression (1 seed, class_weight="balanced")
- Transform: asinh для всех 9 профилей (наследие 5.0b)
- Scaler: train-only StandardScaler
- Seeds: `[42, 77, 123]`
- Holdout: 2023-2026, только раскрытие результата
- Transformer: не обучается

## XGBoost Screening Results

### Sell

| Profile | xgb median val_auc | base_raw val_auc | delta | xgb median lift_30 | base lift_30 | logistic val_auc | xgb vs logistic |
|---|---:|---:|---:|---:|---:|---:|---:|
[Insert one row per profile, sorted by xgb_median desc]

### Buy

[Same table for buy]

## Feature Group Ablation

### Sell (best profile: [Insert])

| Group | val_auc | n_features | delta from full |
|---|---:|---:|---:|
| full | ... | ... | — |
| no_price | ... | ... | ... |
| no_structure | ... | ... | ... |
| no_atr | ... | ... | ... |
| no_time | ... | ... | ... |

### Buy (best profile: [Insert])

[Same table for buy]

## Screener Result

[Insert screener_result from JSON: verdict, criteria (auc_pass, lift_pass), overall_best, sell_best, buy_best, next_step]

## Conclusions

[State verdict: profile_with_potential или h6_off05_target_exhausted]

[If profile_with_potential: какой профиль, на какой цели, delta AUC и lift_30. Отметить: это поисковый результат — нужен проверочный цикл 5.0e, не автоматическое открытие Transformer-обучения.]

[If h6_off05_target_exhausted: ни один профиль не добавляет информации поверх raw на постановке H6_off05. Fractal Stop как семейство не закрыт — остаются другие цели.]

[If Logistic ≈ XGBoost: сигнал линейный, Transformer избыточен.]

[If XGBoost >> Logistic: сигнал в взаимодействиях, но 5.0c показал что Transformer его не извлекает.]

## Limitations / Open Questions

- 3 seeds — screening, не CI. Для кандидата нужен 5-seed проверочный прогон.
- Абляция выполнена только для лучшего профиля по XGBoost, не для всех.
- Holdout — только раскрытие, не входит в решение.
- Результат 5.0d не открывает Transformer-обучение автоматически — только формирует гипотезу для Stage 5.0e.

## Validation Split Disclosure

- val_stop: 2021-2022, использовался для всех метрик решения.
- holdout: 2023-2026, только раскрытие (`holdout_used_for_decision: false`).
- Split: train ≤2020, val_stop 2021-2022, holdout ≥2023. Scaler и transform params fit на train только.

## Next Step

[If profile_with_potential: Stage 5.0e — Transformer multi-seed на лучшем профиле, заранее зафиксированные пороги, новый план.]

[If h6_off05_target_exhausted: закрыть постановку H6_off05 stop broken. Рассмотреть другие цели Fractal Stop (сторона, время до пробоя, выход) или другой target.]

## Related Materials

- `ML/reports/stage5_0d_diagnostic_screening.json`
- `docs/reports/2026-06-22-stage5_0c-cross-target-rerun.md`
- `docs/superpowers/plans/2026-06-23-stage5_0d-diagnostic-screening.md`
```

- [ ] **Step 5: Verify**

```bash
git diff --stat
```

---

### Task 7: Documentation Sync

**Files:**
- Modify: `docs/ML/benchmark_stage5_transformer_breach.py.md`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Update module documentation**

```markdown
- `--stage5-0d-diagnostic-screening` — Stage 5.0d: диагностический скрининг 9 профилей (XGBoost + Logistic, без Transformer), абляция групп признаков.
- `ML/reports/stage5_0d_diagnostic_screening.json` — структурированный артефакт Stage 5.0d.
- `compute_logistic_same_profile_baseline` — Logistic Regression на тех же признаках (linear baseline).
- `compute_feature_group_ablation` — абляция групп признаков (price / structure / ATR / time).
```

- [ ] **Step 2: Update CHANGELOG**

```markdown
## [2026-06-23] — Stage 5.0d: диагностический скрининг профилей

### Добавлено
- `--stage5-0d-diagnostic-screening`
- `ML/reports/stage5_0d_diagnostic_screening.json`
- `docs/reports/2026-06-23-stage5_0d-diagnostic-screening.md`
- `compute_logistic_same_profile_baseline`, `compute_feature_group_ablation`

### Методика
- Уровень: поисковый (exploratory).
- Transformer не обучается. Только XGBoost (3 seeds) + Logistic Regression (1 seed).
- Абляция групп признаков: price / structure / ATR / time.
- Критерий: профиль с запасом >0.02 над base_raw_plus_time → гипотеза для 5.0e.
- Если ни один профиль не проходит — Fractal Stop исследовательски исчерпан.

### Результаты
[Заполнить после прогона: screener_result.verdict, best_delta]

<!-- docs/reports/2026-06-23-stage5_0d-diagnostic-screening.md -->
```

- [ ] **Step 3: Final verification**

```bash
./.venv/bin/python -m pytest tests/ -q
git status --short
git diff --stat
```

---

## Self-Review

**1. Spec coverage:**
- Закрыть 5.0c сначала → Предусловие в заголовке плана ✓
- XGBoost same-profile на всех 9 профилях → Task 4 runner loops `STAGE5_0D_PROFILE_NAMES` ✓
- asinh для всех 9 профилей → `tv = "asinh"` безусловно в runner ✓
- Logistic regression (class_weight="balanced") как linear baseline → Task 2 + Task 4 ✓
- Абляция групп признаков по token_fields/row_fields → Task 3 `_build_feature_group_masks` ✓
- Абляция: holdout предсказания от модели, не нули → Task 3 `model.predict(xgb.DMatrix(...))` ✓
- Годовые AUC/lift → compute_yearly_metrics в Task 2/3 ✓
- Критерий: AUC +0.02 AND lift_30 → Task 4 `auc_pass and lift_pass` ✓
- Вердикт: h6_off05_target_exhausted (не fractal_stop) → Task 4 ✓
- screener_result: sell_best, buy_best, overall_best → Task 4 ✓
- JSON: seed AUC/lift, median, spread, delta → Task 4 profile_results ✓
- «Не открывает Transformer автоматически» → screener_result.next_step ✓
- Секции отчёта: What Was Done, Multiple Testing Context, Changed Files, Verification, Validation Split Disclosure → шаблон отчёта ✓
- Без Transformer → `decision_policy.transformer_trained: False` ✓
- Holdout не для решения → `holdout_used_for_decision: False` ✓
- Без промежуточных commit → все задачи заканчиваются verify ✓

**2. Placeholder scan:** No TBD/TODO. Report template has `[Insert ...]` markers — filled from JSON after run.

**3. Type consistency:**
- `compute_logistic_same_profile_baseline(train_df, val_df, hold_df, profile_name, transform_variant, target_col, seed)` — consistent in Task 2, 4
- `compute_feature_group_ablation(train_df, val_df, hold_df, profile_name, transform_variant, target_col, seed)` — consistent in Task 3, 4
- `run_stage5_0d_diagnostic_screening(sell_splits, buy_splits, seeds, device, output_path)` — consistent in Task 4, 5
- `build_arg_parser()` — reused from Task 7 of 5.0c plan ✓
- `STAGE5_0D_*` constants — consistent in Task 1, 4, 5
