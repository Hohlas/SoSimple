# Stage 5.0b Asinh Rerun Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Добавить отдельный Stage 5.0b rerun: Transformer обучается с заранее зафиксированным `asinh`-преобразованием, обязательными проверками перед обучением и честным сравнением с baseline.

**Architecture:** Legacy Stage 5.0 Phase 1-4 не менять. Новый CLI `--stage5-0b-asinh-rerun` запускается только после OHLC label verification, label sanity и XGBoost/time-only baseline. Результат остаётся `DIAGNOSTIC_ONLY`: обучение выполняется, но торговый winner не объявляется.

**Tech Stack:** Python 3.10, pandas, numpy, PyTorch, scikit-learn, pytest, текущий `ML/baseline/benchmark_stage5_transformer_breach.py`.

## Global Constraints

- Работать в текущей ветке, без worktree.
- Использовать `./.venv/bin/python`.
- Holdout 2023-2026 не использовать для выбора профиля, transform-а, target-а или winner-а; holdout только для disclosure.
- `asinh` заранее зафиксирован как основной transform Stage 5.0b.
- Первый Stage 5.0b training использует только `sell_stop_broken_H6_off05_flag`.
- `buy_stop` пока только диагностируется как target-контракт; buy-обучение не запускать.
- Corridor `seq_len` в Stage 5.0b не менять динамически.
- После Python-изменений запускать `./.venv/bin/python -m pytest tests/ -q`.

---

## Decision Policy

Stage 5.0b не объявляет trading winner. Он решает только, есть ли кандидат на следующий multi-seed rerun.

Переход к multi-seed разрешён только по `val_stop`, если профиль выполняет все условия:

- `val_auc >= max(xgb_base_raw_plus_time_val_auc + 0.01, xgb_time_only_val_auc + 0.03)`;
- `val_lift_30 <= min(xgb_base_raw_plus_time_val_lift_30, xgb_time_only_val_lift_30)`;
- `normalized_distribution_audit.status != "ERROR"`;
- профиль относится к confirmatory candidates, а не к diagnostic controls.

Holdout-метрики, включая yearly AUC, записываются в отчёт, но не участвуют в выборе multi-seed кандидата.

Если ни один confirmatory candidate не проходит эти правила, Stage 5.0b заканчивается без multi-seed продолжения. Если diagnostic control выглядит лучше confirmatory candidates, это не winner, а новая гипотеза для отдельного плана.

---

## Profile Sets

Confirmatory candidates:

```python
STAGE5_0B_CONFIRMATORY_PROFILE_NAMES = [
    "all100_relative_price_time",
    "nearest40_relative_price_time",
    "corridor_5atr_relative_price_atr_full",
    "corridor_10atr_relative_price_atr_full",
]
```

Diagnostic controls:

```python
STAGE5_0B_DIAGNOSTIC_PROFILE_NAMES = [
    "all100_relative_price_no_time",
    "nearest40_relative_price_no_time",
    "all100_absolute_price_atr_scaled_time_asinh",
    "corridor_5atr_price_unit_atr_full",
    "corridor_10atr_price_unit_atr_full",
]
```

All Stage 5.0b profiles:

```python
STAGE5_0B_ASINH_PROFILE_NAMES = (
    STAGE5_0B_CONFIRMATORY_PROFILE_NAMES + STAGE5_0B_DIAGNOSTIC_PROFILE_NAMES
)
```

---

## Files

- Modify: `ML/baseline/benchmark_stage5_transformer_breach.py`
  - добавить Stage 5.0b profile sets;
  - добавить transform-aware training path;
  - добавить запрет динамического corridor `seq_len` для Stage 5.0b;
  - добавить target contract summary для sell и buy;
  - добавить Stage 5.0b runner и CLI;
  - включить OHLC, label sanity, XGBoost/time-only baseline в Stage 5.0b JSON.
- Modify: `tests/test_stage5_transformer_breach.py`
  - тесты на profile sets;
  - тесты на передачу `asinh`;
  - тесты на запрет динамического `seq_len`;
  - тесты на baseline/verification в runner;
  - тесты на sell/buy target contract summary.
- Modify: `docs/ML/benchmark_stage5_transformer_breach.py.md`
- Create: `docs/reports/2026-06-21-stage5_0b-asinh-rerun.md`
- Modify: `CHANGELOG.md`

---

### Task 1: Freeze Stage 5.0b Profile Sets

**Files:**
- Modify: `ML/baseline/benchmark_stage5_transformer_breach.py`
- Test: `tests/test_stage5_transformer_breach.py`

**Interfaces:**
- Produces: `STAGE5_0B_CONFIRMATORY_PROFILE_NAMES: list[str]`
- Produces: `STAGE5_0B_DIAGNOSTIC_PROFILE_NAMES: list[str]`
- Produces: `STAGE5_0B_ASINH_PROFILE_NAMES: list[str]`

- [ ] **Step 1: Write failing test**

Add to `tests/test_stage5_transformer_breach.py`:

```python
def test_stage5_0b_profile_sets_are_frozen_and_separated():
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    assert runner.STAGE5_0B_CONFIRMATORY_PROFILE_NAMES == [
        "all100_relative_price_time",
        "nearest40_relative_price_time",
        "corridor_5atr_relative_price_atr_full",
        "corridor_10atr_relative_price_atr_full",
    ]
    assert runner.STAGE5_0B_DIAGNOSTIC_PROFILE_NAMES == [
        "all100_relative_price_no_time",
        "nearest40_relative_price_no_time",
        "all100_absolute_price_atr_scaled_time_asinh",
        "corridor_5atr_price_unit_atr_full",
        "corridor_10atr_price_unit_atr_full",
    ]
    assert runner.STAGE5_0B_ASINH_PROFILE_NAMES == (
        runner.STAGE5_0B_CONFIRMATORY_PROFILE_NAMES
        + runner.STAGE5_0B_DIAGNOSTIC_PROFILE_NAMES
    )
    for profile_name in runner.STAGE5_0B_ASINH_PROFILE_NAMES:
        assert runner.find_profile(profile_name) is not None
```

- [ ] **Step 2: Run test to verify it fails**

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py -k stage5_0b_profile_sets_are_frozen_and_separated -q
```

Expected: FAIL because constants do not exist.

- [ ] **Step 3: Add constants**

In `ML/baseline/benchmark_stage5_transformer_breach.py`, near `RERUN_CANDIDATE_PROFILE_NAMES`, add the exact constants from the `Profile Sets` section.

- [ ] **Step 4: Run test to verify it passes**

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py -k stage5_0b_profile_sets_are_frozen_and_separated -q
```

Expected: PASS.

---

### Task 2: Make Training Path Transform-Aware And Freeze Corridor Seq Len

**Files:**
- Modify: `ML/baseline/benchmark_stage5_transformer_breach.py`
- Test: `tests/test_stage5_transformer_breach.py`

**Interfaces:**
- Produces: `_train_and_eval_profile(..., transform_variant: str = "current", parsed_splits: dict | None = None, allow_dynamic_seq_len: bool = True) -> float | None`
- Produces result JSON fields: `transform_variant`, `transform_config`, `profile_role`, `training_run`

- [ ] **Step 1: Write failing test for `asinh` propagation**

Add to `tests/test_stage5_transformer_breach.py`:

```python
def test_train_eval_profile_passes_asinh_to_feature_builder(monkeypatch):
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    calls = []
    df = _make_synthetic_df(3, 100)
    df["_year"] = [2020, 2020, 2020]
    y = df[runner.TARGET_COLUMN]
    report = {"transformer_results": {}}

    def fake_build(df_arg, parsed_arg, profile_arg, transform_variant="current", transform_params=None):
        calls.append(transform_variant)
        n = len(df_arg)
        return (
            np.zeros((n, 2, 1), dtype=np.float32),
            np.zeros((n, 1), dtype=np.float32),
            np.ones((n, 2), dtype=bool),
            {"candidate_count_before_cap": np.zeros(n, dtype=np.int32),
             "selected_count_after_cap": np.zeros(n, dtype=np.int32),
             "is_truncated": np.zeros(n, dtype=bool)},
        )

    class DummyModel:
        def eval(self): pass

    monkeypatch.setattr(runner, "build_profile_features_from_parsed", fake_build)
    monkeypatch.setattr(runner, "normalize_profile_features", lambda *args: ((args[0], args[1], args[3], args[4], args[6], args[7]), {}))
    monkeypatch.setattr(runner, "audit_normalized_distribution", lambda *args, **kwargs: {"status": "OK", "flags": [], "by_split": {}})
    monkeypatch.setattr(runner, "train_transformer", lambda *args, **kwargs: (DummyModel(), {"best_val_auc": 0.5, "num_epochs": 1}))
    monkeypatch.setattr(runner, "evaluate_transformer", lambda *args, **kwargs: np.array([0.1, 0.2, 0.3], dtype=np.float32))
    monkeypatch.setattr(runner, "compute_metrics", lambda y_true, pred: {"auc": 0.5, "pr_auc": 0.5, "n": len(y_true), "lift_10": 1.0, "lift_20": 1.0, "lift_30": 1.0})
    monkeypatch.setattr(runner, "compute_yearly_metrics", lambda df_arg, pred: {})

    parsed = {
        "train": runner.parse_split_fractals(df),
        "val_stop": runner.parse_split_fractals(df),
        "holdout": runner.parse_split_fractals(df),
    }
    runner._train_and_eval_profile(
        df, df, df, 42, "cpu", report,
        "all100_relative_price_time", y, y, y,
        transform_variant="asinh",
        parsed_splits=parsed,
        allow_dynamic_seq_len=False,
    )

    assert calls == ["asinh", "asinh", "asinh"]
    result = report["transformer_results"]["all100_relative_price_time"][0]
    assert result["transform_variant"] == "asinh"
    assert result["training_run"] is True
```

- [ ] **Step 2: Write failing test for frozen corridor seq_len**

Add to `tests/test_stage5_transformer_breach.py`:

```python
def test_stage5_0b_can_disable_dynamic_corridor_seq_len(monkeypatch):
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    observed_seq_lens = []
    df = _make_synthetic_df(3, 100)
    df["_year"] = [2020, 2020, 2020]
    y = df[runner.TARGET_COLUMN]
    report = {"transformer_results": {}}

    monkeypatch.setattr(runner, "compute_corridor_stats", lambda df_arg, profile: {
        "n_fractals_median": 10,
        "n_fractals_p80": 10,
    })
    monkeypatch.setattr(runner, "corridor_status", lambda stats: "OK")

    def fake_build(df_arg, parsed_arg, profile_arg, transform_variant="current", transform_params=None):
        observed_seq_lens.append(profile_arg["seq_len"])
        n = len(df_arg)
        return (
            np.zeros((n, profile_arg["seq_len"], 1), dtype=np.float32),
            np.zeros((n, 1), dtype=np.float32),
            np.ones((n, profile_arg["seq_len"]), dtype=bool),
            {"candidate_count_before_cap": np.zeros(n, dtype=np.int32),
             "selected_count_after_cap": np.zeros(n, dtype=np.int32),
             "is_truncated": np.zeros(n, dtype=bool)},
        )

    class DummyModel:
        def eval(self): pass

    monkeypatch.setattr(runner, "build_profile_features_from_parsed", fake_build)
    monkeypatch.setattr(runner, "normalize_profile_features", lambda *args: ((args[0], args[1], args[3], args[4], args[6], args[7]), {}))
    monkeypatch.setattr(runner, "audit_normalized_distribution", lambda *args, **kwargs: {"status": "OK", "flags": [], "by_split": {}})
    monkeypatch.setattr(runner, "train_transformer", lambda *args, **kwargs: (DummyModel(), {"best_val_auc": 0.5, "num_epochs": 1}))
    monkeypatch.setattr(runner, "evaluate_transformer", lambda *args, **kwargs: np.array([0.1, 0.2, 0.3], dtype=np.float32))
    monkeypatch.setattr(runner, "compute_metrics", lambda y_true, pred: {"auc": 0.5, "pr_auc": 0.5, "n": len(y_true), "lift_10": 1.0, "lift_20": 1.0, "lift_30": 1.0})
    monkeypatch.setattr(runner, "compute_yearly_metrics", lambda df_arg, pred: {})

    parsed = {
        "train": runner.parse_split_fractals(df),
        "val_stop": runner.parse_split_fractals(df),
        "holdout": runner.parse_split_fractals(df),
    }
    runner._train_and_eval_profile(
        df, df, df, 42, "cpu", report,
        "corridor_5atr_relative_price_atr_full", y, y, y,
        transform_variant="asinh",
        parsed_splits=parsed,
        allow_dynamic_seq_len=False,
    )

    assert observed_seq_lens == [100, 100, 100]
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py -k "passes_asinh_to_feature_builder or disable_dynamic_corridor_seq_len" -q
```

Expected: FAIL because `_train_and_eval_profile` does not accept the new parameters.

- [ ] **Step 4: Modify `_train_and_eval_profile` signature**

Change signature to:

```python
def _train_and_eval_profile(train_df, val_stop_df, holdout_df, seed, device, report,
                            pname, y_train, y_val, y_holdout, diagnostic_only=False,
                            transform_variant: str = "current",
                            parsed_splits: dict | None = None,
                            allow_dynamic_seq_len: bool = True,
                            profile_role: str = "legacy"):
```

- [ ] **Step 5: Gate dynamic corridor seq_len**

Wrap the existing seq_len adjustment:

```python
        if allow_dynamic_seq_len:
            combined_stats = compute_corridor_stats(
                pd.concat([train_df, val_stop_df]), profile)
            combined_p80 = combined_stats.get("n_fractals_p80", profile["seq_len"])
            if combined_p80 < profile["seq_len"]:
                new_seq = max(int(combined_p80), 3)
                print(f"    Adjusting seq_len: {profile['seq_len']} -> {new_seq} (P80={combined_p80:.1f})")
                profile = deepcopy(profile)
                profile["seq_len"] = new_seq
```

Do not compute `combined_stats` when `allow_dynamic_seq_len=False`.

- [ ] **Step 6: Use parsed transform-aware builder**

Replace direct `build_profile_features(...)` calls inside `_train_and_eval_profile` with:

```python
    parsed_splits = parsed_splits or {
        "train": parse_split_fractals(train_df),
        "val_stop": parse_split_fractals(val_stop_df),
        "holdout": parse_split_fractals(holdout_df),
    }
    transform_params = fit_transform_params_for_profile(
        train_df, parsed_splits["train"], profile, transform_variant)

    tokens_train, rf_train, mask_train, _meta_train = build_profile_features_from_parsed(
        train_df, parsed_splits["train"], profile, transform_variant, transform_params)
    tokens_val, rf_val, mask_val, _meta_val = build_profile_features_from_parsed(
        val_stop_df, parsed_splits["val_stop"], profile, transform_variant, transform_params)
    tokens_hold, rf_hold, mask_hold, _meta_hold = build_profile_features_from_parsed(
        holdout_df, parsed_splits["holdout"], profile, transform_variant, transform_params)
```

- [ ] **Step 7: Add result metadata**

Add to result dict:

```python
        "transform_variant": transform_variant,
        "transform_config": {
            "variant": transform_variant,
            "fit_params": transform_params,
            "fit_params_policy": "train only; val_stop/holdout are disclosure only",
        },
        "profile_role": profile_role,
        "training_run": True,
```

- [ ] **Step 8: Run targeted tests**

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py -k "passes_asinh_to_feature_builder or disable_dynamic_corridor_seq_len or relative_price_formula_verified" -q
```

Expected: PASS.

---

### Task 3: Add Target Contract Summary For Sell And Buy

**Files:**
- Modify: `ML/baseline/benchmark_stage5_transformer_breach.py`
- Test: `tests/test_stage5_transformer_breach.py`

**Interfaces:**
- Produces: `find_buy_stop_target_columns(df: pd.DataFrame) -> list[str]`
- Produces: `summarize_target_contract(df_by_split: dict[str, pd.DataFrame], target_col: str) -> dict`

- [ ] **Step 1: Write failing tests**

Add to `tests/test_stage5_transformer_breach.py`:

```python
def test_find_buy_stop_target_columns_returns_sorted_candidates():
    import ML.baseline.benchmark_stage5_transformer_breach as runner
    df = pd.DataFrame({
        "buy_stop_broken_H6_off05_flag": [0, 1],
        "sell_stop_broken_H6_off05_flag": [1, 0],
        "buy_stop_broken_H12_off05_flag": [0, 0],
    })
    assert runner.find_buy_stop_target_columns(df) == [
        "buy_stop_broken_H12_off05_flag",
        "buy_stop_broken_H6_off05_flag",
    ]


def test_summarize_target_contract_reports_balance_and_nulls_for_sell_and_buy():
    import ML.baseline.benchmark_stage5_transformer_breach as runner
    train = pd.DataFrame({"sell_stop_broken_H6_off05_flag": [0, 1, 1, None]})
    val = pd.DataFrame({"sell_stop_broken_H6_off05_flag": [0, 0, 1]})
    result = runner.summarize_target_contract(
        {"train": train, "val_stop": val},
        "sell_stop_broken_H6_off05_flag",
    )
    assert result["target"] == "sell_stop_broken_H6_off05_flag"
    assert result["splits"]["train"]["exists"] is True
    assert result["splits"]["train"]["n_rows"] == 4
    assert result["splits"]["train"]["n_non_null"] == 3
    assert result["splits"]["train"]["positive_rate"] == pytest.approx(2 / 3)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py -k "buy_stop_target_columns or target_contract_reports" -q
```

Expected: FAIL because helpers do not exist.

- [ ] **Step 3: Implement helpers**

Add near target constants:

```python
def find_buy_stop_target_columns(df: pd.DataFrame) -> list[str]:
    return sorted([
        col for col in df.columns
        if col.startswith("buy_stop_broken_") and col.endswith("_flag")
    ])


def summarize_target_contract(df_by_split: dict[str, pd.DataFrame], target_col: str) -> dict:
    splits = {}
    for split_name, df in df_by_split.items():
        if target_col not in df.columns:
            splits[split_name] = {"exists": False}
            continue
        series = pd.to_numeric(df[target_col], errors="coerce")
        non_null = series.dropna()
        splits[split_name] = {
            "exists": True,
            "n_rows": int(len(series)),
            "n_non_null": int(len(non_null)),
            "null_rate": float(series.isna().mean()) if len(series) else None,
            "positive_rate": float((non_null == 1).mean()) if len(non_null) else None,
            "unique_values": sorted([_safe(v) for v in non_null.unique().tolist()]),
        }
    return {"target": target_col, "splits": splits}
```

- [ ] **Step 4: Run targeted tests**

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py -k "buy_stop_target_columns or target_contract_reports" -q
```

Expected: PASS.

---

### Task 4: Add Stage 5.0b Runner After Mandatory Checks

**Files:**
- Modify: `ML/baseline/benchmark_stage5_transformer_breach.py`
- Test: `tests/test_stage5_transformer_breach.py`

**Interfaces:**
- Produces: `run_stage5_0b_asinh_rerun(train_df, val_stop_df, holdout_df, seed, device, ohlc_verification: dict, label_sanity: dict, xgb_results: dict) -> dict`
- Produces artifact: `ML/reports/stage5_0b_asinh_rerun.json`
- Produces CLI: `--stage5-0b-asinh-rerun`

- [ ] **Step 1: Write failing runner test**

Add to `tests/test_stage5_transformer_breach.py`:

```python
def test_stage5_0b_runner_records_checks_baselines_and_profile_roles(monkeypatch):
    import ML.baseline.benchmark_stage5_transformer_breach as runner

    calls = []
    df = _make_synthetic_df(3, 100)
    df["_year"] = [2020, 2020, 2020]
    ohlc = {"status": "PASS"}
    sanity = {"status": "PASS", "positive_rate": 0.5}
    xgb = {
        "base_raw_plus_time": {"val": {"auc": 0.5, "lift_30": 1.0}},
        "time_only": {"val": {"auc": 0.5, "lift_30": 1.0}},
    }

    def fake_train(train_df, val_df, hold_df, seed, device, report, pname,
                   y_train, y_val, y_holdout, diagnostic_only=False,
                   transform_variant="current", parsed_splits=None,
                   allow_dynamic_seq_len=True, profile_role="legacy"):
        calls.append((pname, transform_variant, allow_dynamic_seq_len, profile_role))
        report["transformer_results"].setdefault(pname, []).append({
            "profile": pname,
            "seed": seed,
            "transform_variant": transform_variant,
            "profile_role": profile_role,
            "training_run": True,
            "normalized_distribution_audit": {"status": "OK"},
            "val": {"auc": 0.51, "lift_30": 0.9},
            "holdout": {"auc": 0.51, "lift_30": 0.9},
            "yearly": {},
        })
        return 1.0

    monkeypatch.setattr(runner, "_train_and_eval_profile", fake_train)
    report = runner.run_stage5_0b_asinh_rerun(
        df, df, df, seed=42, device="cpu",
        ohlc_verification=ohlc,
        label_sanity=sanity,
        xgb_results=xgb,
    )

    assert report["status"] == "DIAGNOSTIC_ONLY"
    assert report["no_trading_winner_declared"] is True
    assert report["ohlc_verification"] == ohlc
    assert report["label_sanity"] == sanity
    assert report["xgb_baselines"] == xgb
    assert report["decision_policy"]["holdout_usage"] == "disclosure only"
    assert {c[1] for c in calls} == {"asinh"}
    assert {c[2] for c in calls} == {False}
    assert calls[0][3] == "confirmatory"
    assert calls[-1][3] == "diagnostic_control"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py -k stage5_0b_runner_records_checks_baselines_and_profile_roles -q
```

Expected: FAIL because runner does not exist.

- [ ] **Step 3: Implement decision helper**

Add:

```python
def stage5_0b_multiseed_decision(result: dict, xgb_results: dict, profile_role: str) -> dict:
    if profile_role != "confirmatory":
        return {"eligible": False, "reason": "diagnostic_control"}
    val = result.get("val", {})
    audit = result.get("normalized_distribution_audit", {})
    base = xgb_results.get("base_raw_plus_time", {}).get("val", {})
    time_only = xgb_results.get("time_only", {}).get("val", {})
    auc_gate = max((base.get("auc") or 0) + 0.01, (time_only.get("auc") or 0) + 0.03)
    lift_gate = min(base.get("lift_30") or float("inf"), time_only.get("lift_30") or float("inf"))
    eligible = (
        audit.get("status") != "ERROR"
        and (val.get("auc") or 0) >= auc_gate
        and (val.get("lift_30") or float("inf")) <= lift_gate
    )
    return {
        "eligible": bool(eligible),
        "auc_gate": float(auc_gate),
        "lift_30_gate": float(lift_gate),
        "reason": "passes_val_policy" if eligible else "fails_val_policy",
    }
```

- [ ] **Step 4: Implement runner**

Add after `run_transform_comparison(...)`:

```python
STAGE5_0B_JSON_REPORT_PATH = REPORTS_DIR / "stage5_0b_asinh_rerun.json"


def run_stage5_0b_asinh_rerun(train_df, val_stop_df, holdout_df, seed, device,
                              ohlc_verification: dict, label_sanity: dict,
                              xgb_results: dict) -> dict:
    y_train = train_df[TARGET_COLUMN]
    y_val = val_stop_df[TARGET_COLUMN]
    y_holdout = holdout_df[TARGET_COLUMN]
    parsed_splits = {
        "train": parse_split_fractals(train_df),
        "val_stop": parse_split_fractals(val_stop_df),
        "holdout": parse_split_fractals(holdout_df),
    }
    report = {
        "status": "DIAGNOSTIC_ONLY",
        "stage": "5.0b_asinh_rerun",
        "target": TARGET_COLUMN,
        "transform_variant": "asinh",
        "no_trading_winner_declared": True,
        "confirmatory_profiles": STAGE5_0B_CONFIRMATORY_PROFILE_NAMES,
        "diagnostic_control_profiles": STAGE5_0B_DIAGNOSTIC_PROFILE_NAMES,
        "ohlc_verification": ohlc_verification,
        "label_sanity": label_sanity,
        "xgb_baselines": xgb_results,
        "target_contracts": {
            "sell": summarize_target_contract(
                {"train": train_df, "val_stop": val_stop_df, "holdout": holdout_df},
                TARGET_COLUMN,
            ),
            "buy_candidates": {
                col: summarize_target_contract(
                    {"train": train_df, "val_stop": val_stop_df, "holdout": holdout_df},
                    col,
                )
                for col in find_buy_stop_target_columns(train_df)
            },
        },
        "decision_policy": {
            "profile_set": "frozen before training",
            "selection_basis": "val_stop only",
            "holdout_usage": "disclosure only",
            "multi_seed_rules": {
                "val_auc": ">= max(xgb_base_raw_plus_time + 0.01, xgb_time_only + 0.03)",
                "val_lift_30": "<= min(xgb_base_raw_plus_time, xgb_time_only)",
                "audit": "normalized_distribution_audit.status != ERROR",
                "profile_role": "confirmatory only",
            },
        },
        "transformer_results": {},
        "multi_seed_candidates": [],
    }

    for profile_name in STAGE5_0B_ASINH_PROFILE_NAMES:
        role = "confirmatory" if profile_name in STAGE5_0B_CONFIRMATORY_PROFILE_NAMES else "diagnostic_control"
        _train_and_eval_profile(
            train_df, val_stop_df, holdout_df, seed, device, report,
            profile_name, y_train, y_val, y_holdout,
            diagnostic_only=(role == "diagnostic_control"),
            transform_variant="asinh",
            parsed_splits=parsed_splits,
            allow_dynamic_seq_len=False,
            profile_role=role,
        )
        result = report["transformer_results"][profile_name][-1]
        decision = stage5_0b_multiseed_decision(result, xgb_results, role)
        result["multi_seed_decision"] = decision
        if decision["eligible"]:
            report["multi_seed_candidates"].append(profile_name)

    with open(STAGE5_0B_JSON_REPORT_PATH, "w") as f:
        json.dump(report, f, indent=2, default=str)
    return report
```

- [ ] **Step 5: Add CLI after mandatory checks**

In `main()`, add parser argument:

```python
parser.add_argument("--stage5-0b-asinh-rerun", action="store_true",
                    help="Run Stage 5.0b frozen asinh Transformer rerun")
```

After `xgb_results = compute_xgb_baselines(...)`, before legacy report init, add:

```python
if args.stage5_0b_asinh_rerun:
    report = run_stage5_0b_asinh_rerun(
        train_df, val_stop_df, holdout_df, seeds[0], device,
        ohlc_verification=ohlc_verification,
        label_sanity=sanity,
        xgb_results=xgb_results,
    )
    print("\n" + "=" * 60)
    print("Stage 5.0b asinh rerun completed")
    print(json.dumps({"json": str(STAGE5_0B_JSON_REPORT_PATH)}, indent=2))
    print("=" * 60)
    return
```

- [ ] **Step 6: Run targeted tests**

```bash
./.venv/bin/python -m pytest tests/test_stage5_transformer_breach.py -k "stage5_0b_runner_records_checks_baselines_and_profile_roles or stage5_0b_profile_sets" -q
```

Expected: PASS.

---

### Task 5: Execute Stage 5.0b Single-Seed Run

**Files:**
- Generated/Modify: `ML/reports/stage5_0b_asinh_rerun.json`
- Create: `docs/reports/2026-06-21-stage5_0b-asinh-rerun.md`

- [ ] **Step 1: Run full tests before training**

```bash
./.venv/bin/python -m pytest tests/ -q
```

Expected: PASS.

- [ ] **Step 2: Run Stage 5.0b**

```bash
./.venv/bin/python -m ML.baseline.benchmark_stage5_transformer_breach --stage5-0b-asinh-rerun --single-seed
```

Expected:

```text
Stage 5.0b asinh rerun completed
```

- [ ] **Step 3: Extract result tables**

Confirmatory candidates:

```bash
./.venv/bin/python -c "import json; d=json.load(open('ML/reports/stage5_0b_asinh_rerun.json')); print('| Profile | val_auc | val_lift_30 | holdout_auc | holdout_lift_30 | multi_seed |'); print('|---|---:|---:|---:|---:|---|');\
for name in d['confirmatory_profiles']:\
 r=d['transformer_results'][name][0]; print(f\"| `{name}` | {r['val'].get('auc')} | {r['val'].get('lift_30')} | {r['holdout'].get('auc')} | {r['holdout'].get('lift_30')} | {r['multi_seed_decision']['eligible']} |\")"
```

Diagnostic controls:

```bash
./.venv/bin/python -c "import json; d=json.load(open('ML/reports/stage5_0b_asinh_rerun.json')); print('| Profile | val_auc | val_lift_30 | holdout_auc | holdout_lift_30 |'); print('|---|---:|---:|---:|---:|');\
for name in d['diagnostic_control_profiles']:\
 r=d['transformer_results'][name][0]; print(f\"| `{name}` | {r['val'].get('auc')} | {r['val'].get('lift_30')} | {r['holdout'].get('auc')} | {r['holdout'].get('lift_30')} |\")"
```

Target contracts:

```bash
./.venv/bin/python -c "import json; d=json.load(open('ML/reports/stage5_0b_asinh_rerun.json')); print(json.dumps(d['target_contracts'], indent=2, ensure_ascii=False))"
```

- [ ] **Step 4: Write report**

Create `docs/reports/2026-06-21-stage5_0b-asinh-rerun.md` with:

```markdown
# Stage 5.0b Asinh Rerun

## Status

`DIAGNOSTIC_ONLY`

`no_trading_winner_declared: true`

## Setup

- Target: `sell_stop_broken_H6_off05_flag`
- Transform: `asinh`
- Scaler: train-only `StandardScaler`
- Dynamic corridor `seq_len`: disabled
- Holdout: 2023-2026, disclosure only

## Decision Policy

Multi-seed candidate only if confirmatory profile passes predefined `val_stop` AUC/lift/audit gates. Holdout is not used for selection.

## Mandatory Checks

Include exact `status`, `positive_rate`, and baseline `val.auc` / `val.lift_30` values from `ML/reports/stage5_0b_asinh_rerun.json`.

## Confirmatory Candidates

Insert the confirmatory table generated in Task 5 Step 3.

## Diagnostic Controls

Insert the diagnostic controls table generated in Task 5 Step 3.

## Target Contracts

Include sell target `n_non_null`, `null_rate`, `positive_rate`; include buy candidate columns and the same per-split fields.

## Decision

List `multi_seed_candidates` from JSON. If empty, state that Stage 5.0b has no multi-seed continuation.
```

---

### Task 6: Documentation Sync

**Files:**
- Modify: `docs/ML/benchmark_stage5_transformer_breach.py.md`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Update module documentation**

Add:

```markdown
- `--stage5-0b-asinh-rerun` — Stage 5.0b diagnostic training run: `asinh`, frozen profile sets, mandatory label checks, XGBoost/time-only baselines, no trading winner.
- `ML/reports/stage5_0b_asinh_rerun.json` — structured artifact Stage 5.0b.
```

- [ ] **Step 2: Update CHANGELOG**

At top of `CHANGELOG.md`, add:

```markdown
## [2026-06-21] — Stage 5.0b: Asinh Transformer rerun

### Добавлено
- `--stage5-0b-asinh-rerun`
- `ML/reports/stage5_0b_asinh_rerun.json`
- `docs/reports/2026-06-21-stage5_0b-asinh-rerun.md`

### Методика
- Статус `DIAGNOSTIC_ONLY`; holdout не используется для выбора.
- Confirmatory candidates отделены от diagnostic controls.
- Dynamic corridor `seq_len` отключён.
```

- [ ] **Step 3: Final verification**

```bash
./.venv/bin/python -m pytest tests/ -q
git status --short
git diff --stat
```

Expected: tests PASS; diff limited to Stage 5.0b code, tests, report, docs, changelog, generated JSON.

---

## Self-Review

- Spec coverage: mandatory checks kept before Stage 5.0b, XGBoost/time-only baselines included, profile sets separated, dynamic `seq_len` disabled, sell and buy target contracts summarized, result status stays `DIAGNOSTIC_ONLY`.
- Placeholder scan: no placeholder markers remain; report values are generated from JSON after the run.
- Type consistency: `transform_variant`, `parsed_splits`, `allow_dynamic_seq_len`, `profile_role`, `STAGE5_0B_CONFIRMATORY_PROFILE_NAMES`, `STAGE5_0B_DIAGNOSTIC_PROFILE_NAMES`, `run_stage5_0b_asinh_rerun`, `find_buy_stop_target_columns`, and `summarize_target_contract` are consistently named.
