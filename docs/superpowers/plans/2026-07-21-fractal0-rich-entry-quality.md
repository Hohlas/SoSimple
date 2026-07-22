# Fractal0 Rich Entry Quality Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a rich pre-order ML-entry quality research runner for `E3_open_pullback_1_0atr` using live-safe fractal structure, H1 price action, planned execution geometry, and stricter targets.

**Architecture:** Extend the existing `ML/baseline/benchmark_fractal0_entry_quality_filter.py` flow instead of copying the M5 simulator. Keep `ML/baseline/benchmark_fractal0_entry_exit_grid.py` as the source of entry rows, M5 execution ordering, ML-exit scoring, trade simulation, and PF/bootstrap metrics. Add focused helpers for rich features, target contracts, search eligibility, diagnostics, and a separate output prefix.

**Tech Stack:** Python 3.10+, pandas, numpy, scikit-learn, optional xgboost/lightgbm only as diagnostic-only, pytest, existing `./.venv/bin/python`.

## Audit Errata After Corrected Rerun

This plan is the original execution plan. The corrected full rerun changed several expected disclosures:

- Superseded: examples expecting `"diagnostic_best_val_eval_not_eligible": True`. Corrected artifact has `diagnostic_best_val_eval_not_eligible=False` and `diagnostic_best_val_eval_is_selected_winner=True`, because diagnostic best equals the selected fixed `val_eval` row.
- Superseded: report section name `Diagnostic Disclosure: Not Eligible For Winner`. The final report uses `Diagnostic Disclosure: Best Val Eval Row`.
- Added after audit: `cumulative_search_budget`, `report_verdict_note=TIME_ONLY_WINNER`, `feature_importance_status=NOT_PRODUCED`, and `permutation_null_repeats_executed_for_full_selection=0`.
- Added after audit: `feature_distribution_flags.csv` now discloses constant feature names, required live fields, and informational constant fields. PASS means no gross feature-contract break, not proof that every field is informative.
- Clarification: the next step is a pre-registered replication/probe of one rule or a small predefined shortlist. It is not a freeze decision and does not permit opening `locked_test`.

## Global Constraints

- Work on the current feature branch; do not create a worktree.
- Use `./.venv/bin/python`.
- Do not open `locked_test`; artifact must say `locked_test=not_opened`.
- Do not commit or push unless the user explicitly asks.
- Do not read large CSV/log files whole; use `nrows`, `usecols`, chunks, or existing runner loaders.
- M5 is execution ordering only, not a model feature source.
- Decision time is `pre_order_after_signal_before_limit_order_send`.
- OHLC features may use only `last_fully_closed_h1_bar` and older bars.
- `Up/Dn` top-level target columns are forbidden; serialized `Up/Dn` inside `fractal*` are allowed only after producer-contract disclosure.
- Phase A eligible winner excludes `top20`, `top10`, `structure_nearest_k80`, `structure_all100`, XGBoost, and LightGBM.
- Default full run executes only the `243` eligible configurations; diagnostic configurations require a separate flag and separate budget.
- Feature builders must return explicit allowlists per profile, never all numeric columns.
- XGBoost/LightGBM in Phase A are listed diagnostic options only; they are not runnable unless dependency checks pass before job creation.
- Phase A maximum verdict is `RESEARCH_HINT_RICH_FEATURES`.
- Full tests after Python changes: `./.venv/bin/python -m pytest tests/ -q`.

---

## File Structure

- Modify `ML/baseline/benchmark_fractal0_entry_quality_filter.py`: add rich feature profiles, stricter targets, model grid, eligibility, diagnostics, JSON fields, and CLI mode.
- Modify `tests/test_fractal0_entry_quality_filter.py`: add unit tests for feature contract, OHLC availability, target construction, eligibility, and cutoff behavior.
- Modify `docs/ML/benchmark_fractal0_entry_quality_filter.py.md`: document the rich-entry mode and artifacts.
- Create after run `docs/reports/2026-07-21-fractal0-rich-entry-quality.md`: final report.
- Create after run `ML/reports/fractal0_rich_entry_quality*.csv/json`: structured artifacts.

---

### Task 1: Add Rich Config And Eligibility Contract

**Files:**
- Modify: `ML/baseline/benchmark_fractal0_entry_quality_filter.py`
- Test: `tests/test_fractal0_entry_quality_filter.py`

**Interfaces:**
- Produces: `rich_feature_profile_grid() -> list[dict[str, object]]`
- Produces: `rich_model_grid(include_diagnostic_models: bool) -> list[dict[str, object]]`
- Produces: `rich_target_grid() -> list[dict[str, object]]`
- Produces: `rich_filter_grid() -> list[dict[str, object]]`
- Produces: `compute_search_budget(profiles, models, targets, filters) -> dict[str, object]`

- [ ] **Step 1: Write failing tests for Phase A eligibility**

Add to `tests/test_fractal0_entry_quality_filter.py`:

```python
def test_rich_phase_a_search_budget_and_eligibility():
    profiles = runner.rich_feature_profile_grid()
    models = runner.rich_model_grid(include_diagnostic_models=True)
    targets = runner.rich_target_grid()
    filters = runner.rich_filter_grid()
    budget = runner.compute_search_budget(profiles, models, targets, filters)

    assert budget["n_profiles"] == 9
    assert budget["n_models"] == 3
    assert budget["n_targets"] == 3
    assert budget["n_primary_filters"] == 3
    assert budget["n_total_ranked_configs"] == 243

    diagnostic_profiles = {p["profile_id"] for p in profiles if not p["eligible_for_winner"]}
    diagnostic_models = {m["model_id"] for m in models if not m["eligible_for_winner"]}
    diagnostic_filters = {f["filter_id"] for f in filters if not f["eligible_for_winner"]}

    assert {"structure_nearest_k80", "structure_all100"}.issubset(diagnostic_profiles)
    assert {"xgboost_depth3", "xgboost_depth5", "lightgbm_small"}.issubset(diagnostic_models)
    assert {"top20", "top10"}.issubset(diagnostic_filters)
    assert budget["n_total_executed_configs_default"] == 243
    assert all(
        models_by_id["runnable_by_default"] is False
        for model_id, models_by_id in {m["model_id"]: m for m in models}.items()
        if model_id in {"xgboost_depth3", "xgboost_depth5", "lightgbm_small"}
    )
```

- [ ] **Step 2: Run the focused test and verify it fails**

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_entry_quality_filter.py::test_rich_phase_a_search_budget_and_eligibility -q
```

Expected: FAIL because the new functions do not exist.

- [ ] **Step 3: Add constants and grid helpers**

Add near the current `ENTRY_FEATURE_COLUMNS`:

```python
RICH_ALLOWED_MAX_VERDICT = "RESEARCH_HINT_RICH_FEATURES"
RICH_OUTPUT_PREFIX = "ML/reports/fractal0_rich_entry_quality"
RICH_PRIMARY_TOP_FRACTIONS = (0.50, 0.40, 0.30)
RICH_DIAGNOSTIC_TOP_FRACTIONS = (0.20, 0.10)
RICH_TARGET_IDS = (
    "target_entry_ev_regression",
    "target_entry_good_0_5r",
    "target_entry_avoid_sl",
)
```

Add below `entry_filter_grid()`:

```python
def rich_feature_profile_grid() -> list[dict[str, object]]:
    return [
        {"profile_id": "planned_geometry_only", "eligible_for_winner": True},
        {"profile_id": "time_only", "eligible_for_winner": True},
        {"profile_id": "structure_f0_only", "eligible_for_winner": True},
        {"profile_id": "structure_nearest_k20", "eligible_for_winner": True},
        {"profile_id": "structure_nearest_k40", "eligible_for_winner": True},
        {"profile_id": "relative_geometry_k40", "eligible_for_winner": True},
        {"profile_id": "price_action_h1", "eligible_for_winner": True},
        {"profile_id": "movement_plus_time", "eligible_for_winner": True},
        {"profile_id": "rich_combined_k40", "eligible_for_winner": True},
        {"profile_id": "structure_nearest_k80", "eligible_for_winner": False},
        {"profile_id": "structure_all100", "eligible_for_winner": False},
    ]


def rich_model_grid(include_diagnostic_models: bool = False) -> list[dict[str, object]]:
    models = [
        {"model_id": "linear", "eligible_for_winner": True},
        {"model_id": "hist_gradient_boosting", "eligible_for_winner": True},
        {"model_id": "extra_trees_shallow", "eligible_for_winner": True},
    ]
    if include_diagnostic_models:
        models.extend(
            [
                {"model_id": "extra_trees_current", "eligible_for_winner": False, "runnable_by_default": True},
                {"model_id": "random_forest_shallow", "eligible_for_winner": False, "runnable_by_default": True},
                {"model_id": "xgboost_depth3", "eligible_for_winner": False, "runnable_by_default": False, "listed_but_not_runnable": True},
                {"model_id": "xgboost_depth5", "eligible_for_winner": False, "runnable_by_default": False, "listed_but_not_runnable": True},
                {"model_id": "lightgbm_small", "eligible_for_winner": False, "runnable_by_default": False, "listed_but_not_runnable": True},
            ]
        )
    return models


def rich_target_grid() -> list[dict[str, object]]:
    return [
        {"target_id": "target_entry_ev_regression", "kind": "regression", "eligible_for_winner": True},
        {"target_id": "target_entry_good_0_5r", "kind": "classification", "eligible_for_winner": True},
        {"target_id": "target_entry_avoid_sl", "kind": "classification", "eligible_for_winner": True},
        {"target_id": "target_entry_filled", "kind": "classification", "eligible_for_winner": False},
        {"target_id": "target_entry_good_0_25r", "kind": "classification", "eligible_for_winner": False},
        {"target_id": "target_entry_good_1r", "kind": "classification", "eligible_for_winner": False},
        {"target_id": "target_entry_avoid_bad", "kind": "classification", "eligible_for_winner": False},
    ]


def rich_filter_grid() -> list[dict[str, object]]:
    filters = [{"filter_id": "M0_no_mask", "top_fraction": 1.0, "eligible_for_winner": False}]
    for fraction in RICH_PRIMARY_TOP_FRACTIONS:
        filters.append({"filter_id": f"top{int(fraction * 100)}", "top_fraction": fraction, "eligible_for_winner": True})
    for fraction in RICH_DIAGNOSTIC_TOP_FRACTIONS:
        filters.append({"filter_id": f"top{int(fraction * 100)}", "top_fraction": fraction, "eligible_for_winner": False})
    return filters


def compute_search_budget(
    profiles: list[dict[str, object]],
    models: list[dict[str, object]],
    targets: list[dict[str, object]],
    filters: list[dict[str, object]],
) -> dict[str, object]:
    eligible_profiles = [p for p in profiles if p.get("eligible_for_winner")]
    eligible_models = [m for m in models if m.get("eligible_for_winner")]
    eligible_targets = [t for t in targets if t.get("eligible_for_winner")]
    eligible_filters = [f for f in filters if f.get("eligible_for_winner")]
    return {
        "n_profiles": len(eligible_profiles),
        "n_models": len(eligible_models),
        "n_targets": len(eligible_targets),
        "n_primary_filters": len(eligible_filters),
        "n_seeds": 1,
        "n_total_ranked_configs": len(eligible_profiles) * len(eligible_models) * len(eligible_targets) * len(eligible_filters),
        "n_diagnostic_configs": (
            len(profiles) * len(models) * len(targets) * len(filters)
            - len(eligible_profiles) * len(eligible_models) * len(eligible_targets) * len(eligible_filters)
        ),
        "n_total_executed_configs_default": len(eligible_profiles) * len(eligible_models) * len(eligible_targets) * len(eligible_filters),
    }
```

- [ ] **Step 4: Run the focused test and verify it passes**

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_entry_quality_filter.py::test_rich_phase_a_search_budget_and_eligibility -q
```

Expected: PASS.

---

### Task 2: Add Rich Target And Planned-Order Diagnostics

**Files:**
- Modify: `ML/baseline/benchmark_fractal0_entry_quality_filter.py`
- Test: `tests/test_fractal0_entry_quality_filter.py`

**Interfaces:**
- Produces: `build_rich_entry_labels(planned_orders: pd.DataFrame, trades: pd.DataFrame) -> pd.DataFrame`
- Produces: `planned_order_diagnostics(planned_orders: pd.DataFrame, trades: pd.DataFrame, split: str) -> dict[str, object]`
- Consumes: `position_id`, `filled`, `pnl_r`, `close_reason`

- [ ] **Step 1: Write failing target tests**

Add:

```python
def test_build_rich_entry_labels_keeps_no_fill_and_stronger_targets():
    planned = pd.DataFrame(
        [
            {"position_id": "a", "filled": True},
            {"position_id": "b", "filled": True},
            {"position_id": "c", "filled": False},
        ]
    )
    trades = pd.DataFrame(
        [
            {"position_id": "a", "pnl_r": 0.6, "close_reason": "ML_CLOSE"},
            {"position_id": "b", "pnl_r": -1.0, "close_reason": "SL"},
        ]
    )
    labels = runner.build_rich_entry_labels(planned, trades).set_index("position_id")
    assert bool(labels.loc["a", "order_filled"]) is True
    assert labels.loc["a", "target_entry_good_0_5r"] == 1
    assert labels.loc["a", "target_entry_avoid_sl"] == 1
    assert labels.loc["b", "target_entry_good_0_5r"] == 0
    assert labels.loc["b", "target_entry_avoid_sl"] == 0
    assert bool(labels.loc["c", "order_filled"]) is False
    assert labels.loc["c", "target_entry_filled"] == 0
    assert pd.isna(labels.loc["c", "target_entry_ev_regression"])


def test_planned_order_diagnostics_reports_fill_rate_and_expected_pnl():
    planned = pd.DataFrame({"position_id": ["a", "b", "c"], "filled": [True, True, False]})
    trades = pd.DataFrame({"position_id": ["a", "b"], "pnl_r": [0.5, -0.25]})
    diag = runner.planned_order_diagnostics(planned, trades, "val_select")
    assert diag["split"] == "val_select"
    assert diag["planned_orders"] == 3
    assert diag["filled_orders"] == 2
    assert diag["fill_rate"] == pytest.approx(2 / 3)
    assert diag["expected_pnl_per_filled_trade"] == pytest.approx(0.125)
    assert diag["expected_pnl_per_planned_order"] == pytest.approx(0.25 / 3)
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_entry_quality_filter.py::test_build_rich_entry_labels_keeps_no_fill_and_stronger_targets tests/test_fractal0_entry_quality_filter.py::test_planned_order_diagnostics_reports_fill_rate_and_expected_pnl -q
```

Expected: FAIL because helpers are missing.

- [ ] **Step 3: Implement labels and diagnostics**

Add below `build_entry_labels()`:

```python
def build_rich_entry_labels(planned_orders: pd.DataFrame, trades: pd.DataFrame) -> pd.DataFrame:
    out = planned_orders[["position_id", "filled"]].copy()
    out = out.rename(columns={"filled": "order_filled"})
    realized = trades[["position_id", "pnl_r", "close_reason"]].copy()
    realized["pnl_r_if_filled"] = pd.to_numeric(realized["pnl_r"], errors="coerce")
    out = out.merge(realized[["position_id", "pnl_r_if_filled", "close_reason"]], on="position_id", how="left")
    pnl = pd.to_numeric(out["pnl_r_if_filled"], errors="coerce")
    out["target_entry_ev_regression"] = pnl
    out["target_entry_good_0_5r"] = np.where(pnl.notna(), (pnl >= 0.5).astype(int), pd.NA)
    out["target_entry_good_0_25r"] = np.where(pnl.notna(), (pnl >= 0.25).astype(int), pd.NA)
    out["target_entry_good_1r"] = np.where(pnl.notna(), (pnl >= 1.0).astype(int), pd.NA)
    out["target_entry_avoid_bad"] = np.where(pnl.notna(), (pnl > -0.5).astype(int), pd.NA)
    out["target_entry_avoid_sl"] = np.where(
        out["close_reason"].notna(),
        (~out["close_reason"].astype(str).eq("SL")).astype(int),
        pd.NA,
    )
    out["target_entry_filled"] = out["order_filled"].astype(bool).astype(int)
    return out


def planned_order_diagnostics(planned_orders: pd.DataFrame, trades: pd.DataFrame, split: str) -> dict[str, object]:
    planned_n = int(len(planned_orders))
    filled_n = int(planned_orders.get("filled", pd.Series(dtype=bool)).fillna(False).astype(bool).sum())
    pnl = pd.to_numeric(trades.get("pnl_r"), errors="coerce").dropna()
    total_pnl = float(pnl.sum()) if len(pnl) else 0.0
    return {
        "split": split,
        "planned_orders": planned_n,
        "filled_orders": filled_n,
        "no_fill_orders": int(planned_n - filled_n),
        "fill_rate": float(filled_n / planned_n) if planned_n else 0.0,
        "no_fill_rate": float((planned_n - filled_n) / planned_n) if planned_n else 0.0,
        "expected_pnl_per_filled_trade": float(pnl.mean()) if len(pnl) else None,
        "expected_pnl_per_planned_order": float(total_pnl / planned_n) if planned_n else None,
    }
```

- [ ] **Step 4: Run target tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_entry_quality_filter.py::test_build_rich_entry_labels_keeps_no_fill_and_stronger_targets tests/test_fractal0_entry_quality_filter.py::test_planned_order_diagnostics_reports_fill_rate_and_expected_pnl -q
```

Expected: PASS.

---

### Task 3: Add Feature Builders For Rich Profiles

**Files:**
- Modify: `ML/baseline/benchmark_fractal0_entry_quality_filter.py`
- Test: `tests/test_fractal0_entry_quality_filter.py`

**Interfaces:**
- Produces: `build_rich_feature_frame(entries: pd.DataFrame, ohlc: pd.DataFrame, profile_id: str) -> tuple[pd.DataFrame, list[dict[str, object]]]`
- Produces: `parse_serialized_fractal(value: object) -> dict[str, object] | None`
- Produces: `rich_feature_allowlist(profile_id: str) -> list[str]`
- Consumes: `base.build_entry_rows()` output, `DATA/XAUUSD_H1_OHLC.csv` loaded by `base.load_ohlc()`

- [ ] **Step 1: Write failing feature-contract tests**

Add:

```python
def test_rich_feature_frame_uses_closed_h1_and_forbids_top_level_targets():
    entries = pd.DataFrame(
        {
            "time": pd.to_datetime(["2020-01-01 10:00:00"]),
            "side": ["BUY"],
            "ATR": [2.0],
            "fractal0_price": [100.0],
            "planned_entry_bid_equivalent": [101.0],
            "planned_protective_stop_price": [97.0],
            "planned_r_value": [4.0],
            "signal": [1],
            "predict": [0],
            "up_3": [999.0],
            "dn_3": [999.0],
            "ret_3": [999.0],
            "fav_3": [999.0],
            "adv_3": [999.0],
            "pnl_r": [999.0],
            "close_reason": ["SL"],
            "fill_lag": [3],
            "exit_time": pd.to_datetime(["2020-01-01 13:00:00"]),
            "target_leak": [1],
        }
    )
    ohlc = pd.DataFrame(
        {
            "time": pd.to_datetime(["2020-01-01 08:00:00", "2020-01-01 09:00:00"]),
            "open": [90.0, 95.0],
            "high": [98.0, 103.0],
            "low": [89.0, 94.0],
            "close": [96.0, 102.0],
        }
    )
    features, audit = runner.build_rich_feature_frame(entries, ohlc, "price_action_h1")
    forbidden = {"signal", "predict", "up_3", "dn_3", "ret_3", "fav_3", "adv_3", "pnl_r", "close_reason", "fill_lag", "exit_time", "target_leak"}
    assert forbidden.isdisjoint(features.columns)
    assert features.loc[0, "h1_close"] == 102.0
    assert all(item["live_safe"] for item in audit)


def test_closed_h1_excludes_exact_open_time():
    entries = pd.DataFrame(
        {
            "time": pd.to_datetime(["2020-01-01 10:00:00"]),
            "side": ["BUY"],
            "ATR": [2.0],
            "fractal0_price": [100.0],
            "planned_entry_bid_equivalent": [101.0],
            "planned_protective_stop_price": [97.0],
            "planned_r_value": [4.0],
        }
    )
    ohlc = pd.DataFrame(
        {
            "time": pd.to_datetime(["2020-01-01 09:00:00", "2020-01-01 10:00:00"]),
            "open": [90.0, 200.0],
            "high": [98.0, 210.0],
            "low": [89.0, 190.0],
            "close": [96.0, 205.0],
        }
    )
    features, _ = runner.build_rich_feature_frame(entries, ohlc, "price_action_h1")
    assert features.loc[0, "h1_close"] == 96.0


def test_parse_serialized_fractal_and_nonzero_structure_features():
    raw0 = "1700000000:100.5:1:2:3:1:0:1:4:5:6:0.1:0.2:0.3:0.4:0.5:0.6:0.7:0.8:0.9:1.0:2.5:12"
    raw1 = "1699996400:99.0:-1:1:2:0:1:0:3:4:5:0.2:0.1:0.4:0.3:0.6:0.5:0.8:0.7:1.0:0.9:2.0:24"
    entries = pd.DataFrame(
        {
            "time": pd.to_datetime(["2020-01-01 10:00:00"]),
            "side": ["BUY"],
            "ATR": [2.0],
            "fractal0": [raw0],
            "fractal1": [raw1],
            "fractal0_price": [100.5],
            "planned_entry_bid_equivalent": [101.0],
            "planned_protective_stop_price": [97.0],
            "planned_r_value": [4.0],
        }
    )
    parsed = runner.parse_serialized_fractal(raw0)
    assert parsed["price"] == 100.5
    assert parsed["direction"] == 1
    assert parsed["up_3"] == 0.7
    assert parsed["dn_48"] == 0.6
    features, _ = runner.build_rich_feature_frame(entries, pd.DataFrame(), "structure_f0_only")
    assert features.loc[0, "fractal0_power"] == 4.0
    assert features.loc[0, "fractal0_shift"] == 12.0
    rel, _ = runner.build_rich_feature_frame(entries, pd.DataFrame(), "relative_geometry_k40")
    assert rel.loc[0, "fractal1_price_rel_f0"] == -1.5
    assert rel.loc[0, "fractal1_direction"] == -1.0


def test_structure_all100_is_diagnostic_only():
    profiles = {p["profile_id"]: p for p in runner.rich_feature_profile_grid()}
    assert profiles["structure_all100"]["eligible_for_winner"] is False
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_entry_quality_filter.py::test_rich_feature_frame_uses_closed_h1_and_forbids_top_level_targets tests/test_fractal0_entry_quality_filter.py::test_structure_all100_is_diagnostic_only -q
```

Expected: first test FAIL because rich feature builder is missing.

- [ ] **Step 3: Implement real allowlist-based rich feature builder**

Add imports:

```python
from sklearn.ensemble import ExtraTreesClassifier, ExtraTreesRegressor, RandomForestClassifier, RandomForestRegressor
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.linear_model import LogisticRegression, Ridge
```

Add forbidden-column guard and exact profile allowlists:

```python
FORBIDDEN_FEATURE_PREFIXES = (
    "up_",
    "dn_",
    "ret_",
    "fav_",
    "adv_",
    "entry_up_",
    "entry_dn_",
    "entry_log_ratio_",
    "trail_",
    "target_",
    "label_",
    "outcome_",
)
FORBIDDEN_FEATURE_EXACT = {"pnl_r", "close_reason", "hold_bars", "exit_time", "target_leak"}


def _assert_no_forbidden_feature_columns(columns: list[str]) -> None:
    bad = [
        col for col in columns
        if col in FORBIDDEN_FEATURE_EXACT or col.startswith(FORBIDDEN_FEATURE_PREFIXES) or "_pnl_" in col
    ]
    if bad:
        raise ValueError(f"forbidden feature columns: {bad[:10]}")


FRACTAL_FIELD_NAMES = (
    "time",
    "price",
    "direction",
    "front",
    "back",
    "strong",
    "break",
    "reverse",
    "power",
    "count",
    "impulse",
    "up_12",
    "dn_12",
    "up_24",
    "dn_24",
    "up_48",
    "dn_48",
    "up_3",
    "dn_3",
    "up_6",
    "dn_6",
    "fractal_atr",
    "shift",
)


def parse_serialized_fractal(value: object) -> dict[str, object] | None:
    if pd.isna(value) or value == "":
        return None
    parts = str(value).split(":")
    if len(parts) != len(FRACTAL_FIELD_NAMES):
        return None
    parsed: dict[str, object] = {}
    for name, raw in zip(FRACTAL_FIELD_NAMES, parts):
        if name == "time":
            parsed[name] = raw
        else:
            parsed[name] = float(raw)
    return parsed


def rich_feature_allowlist(profile_id: str) -> list[str]:
    planned = ["side_buy", "ATR", "entry_to_fractal0_atr", "stop_distance_atr", "r_value_atr"]
    time_cols = ["session_hour", "weekday", "hour_sin", "hour_cos", "weekday_sin", "weekday_cos"]
    h1_cols = ["h1_open", "h1_high", "h1_low", "h1_close", "h1_body", "h1_range", "h1_close_position_in_range"]
    movement = ["movement_score"]
    if profile_id == "planned_geometry_only":
        return planned
    if profile_id == "time_only":
        return time_cols
    if profile_id == "price_action_h1":
        return h1_cols
    if profile_id == "movement_plus_time":
        return movement + time_cols
    if profile_id == "structure_f0_only":
        return [f"fractal0_{field}" for field in ("price", "direction", "front", "back", "strong", "break", "reverse", "power", "count", "impulse", "fractal_atr", "shift", "up_3", "dn_3", "up_6", "dn_6", "up_12", "dn_12", "up_24", "dn_24", "up_48", "dn_48")]
    if profile_id in {"structure_nearest_k20", "structure_nearest_k40", "relative_geometry_k40", "rich_combined_k40"}:
        k = 20 if profile_id == "structure_nearest_k20" else 40
        fractal_cols: list[str] = []
        for idx in range(k):
            fractal_cols.extend(
                [
                    f"fractal{idx}_price_rel_f0",
                    f"fractal{idx}_direction",
                    f"fractal{idx}_front",
                    f"fractal{idx}_back",
                    f"fractal{idx}_strong",
                    f"fractal{idx}_break",
                    f"fractal{idx}_reverse",
                    f"fractal{idx}_power",
                    f"fractal{idx}_count",
                    f"fractal{idx}_impulse",
                    f"fractal{idx}_fractal_atr",
                    f"fractal{idx}_shift",
                    f"fractal{idx}_distance_to_planned_limit",
                    f"fractal{idx}_distance_to_planned_stop",
                ]
            )
        if profile_id == "relative_geometry_k40":
            return fractal_cols
        if profile_id == "rich_combined_k40":
            return planned + time_cols + h1_cols + fractal_cols
        return fractal_cols
    raise ValueError(f"unknown rich feature profile: {profile_id}")
```

Add the allowlist-based builder below `build_entry_feature_frame()`:

```python
def _attach_closed_h1_features(out: pd.DataFrame, ohlc: pd.DataFrame) -> tuple[pd.DataFrame, list[dict[str, object]]]:
    audit: list[dict[str, object]] = []
    if ohlc.empty or "time" not in ohlc:
        return out, audit
    bars = ohlc.copy()
    bars["time"] = pd.to_datetime(bars["time"])
    bars = bars.sort_values("time")
    base_cols = ["open", "high", "low", "close"]
    right = bars[["time", *base_cols]].rename(columns={col: f"h1_{col}" for col in base_cols})
    left = out.sort_values("time").copy()
    left["_lookup_time"] = pd.to_datetime(left["time"]) - pd.Timedelta(nanoseconds=1)
    merged = pd.merge_asof(
        left,
        right,
        left_on="_lookup_time",
        right_on="time",
        direction="backward",
        allow_exact_matches=True,
    ).sort_index()
    for col in base_cols:
        name = f"h1_{col}"
        out[name] = merged[name].to_numpy()
        audit.append(
            {
                "feature": name,
                "source": "DATA/XAUUSD_H1_OHLC.csv",
                "bar_offset": 0,
                "requires_bar_close": True,
                "available_at": "last_fully_closed_h1_bar",
                "live_safe": True,
            }
        )
    out["h1_body"] = out["h1_close"] - out["h1_open"]
    out["h1_range"] = out["h1_high"] - out["h1_low"]
    out["h1_close_position_in_range"] = (out["h1_close"] - out["h1_low"]) / out["h1_range"].replace(0, pd.NA)
    return out, audit


def extract_fractal_feature_dict(row: pd.Series, k: int) -> dict[str, float]:
    result: dict[str, float] = {}
    fractal0 = parse_serialized_fractal(row.get("fractal0"))
    base_price = float(row.get("fractal0_price", fractal0.get("price") if fractal0 else 0.0) or 0.0)
    planned_limit = float(row.get("planned_entry_bid_equivalent") or 0.0)
    planned_stop = float(row.get("planned_protective_stop_price") or 0.0)
    for idx in range(k):
        prefix = f"fractal{idx}_"
        parsed = parse_serialized_fractal(row.get(f"fractal{idx}"))
        price = float(parsed["price"]) if parsed else base_price
        for field in ("direction", "front", "back", "strong", "break", "reverse", "power", "count", "impulse", "fractal_atr", "shift"):
            result[f"{prefix}{field}"] = float(parsed.get(field, 0.0)) if parsed else 0.0
        result[f"{prefix}price_rel_f0"] = price - base_price
        result[f"{prefix}distance_to_planned_limit"] = price - planned_limit
        result[f"{prefix}distance_to_planned_stop"] = price - planned_stop
    return result


def build_rich_feature_frame(entries: pd.DataFrame, ohlc: pd.DataFrame, profile_id: str) -> tuple[pd.DataFrame, list[dict[str, object]]]:
    out = build_entry_feature_frame(entries)
    audit: list[dict[str, object]] = [
        {"feature": col, "source": "planned_execution_geometry", "available_at": "pre_order", "live_safe": True}
        for col in ENTRY_FEATURE_COLUMNS
    ]
    if profile_id in {"time_only", "movement_plus_time", "rich_combined_k40"}:
        times = pd.to_datetime(out["time"])
        out["session_hour"] = times.dt.hour.astype(float)
        out["weekday"] = times.dt.weekday.astype(float)
        out["hour_sin"] = np.sin(2 * np.pi * out["session_hour"] / 24.0)
        out["hour_cos"] = np.cos(2 * np.pi * out["session_hour"] / 24.0)
        out["weekday_sin"] = np.sin(2 * np.pi * out["weekday"] / 7.0)
        out["weekday_cos"] = np.cos(2 * np.pi * out["weekday"] / 7.0)
    if profile_id in {"price_action_h1", "rich_combined_k40"}:
        out, ohlc_audit = _attach_closed_h1_features(out, ohlc)
        audit.extend(ohlc_audit)
    if profile_id in {"structure_f0_only", "structure_nearest_k20", "structure_nearest_k40", "relative_geometry_k40", "rich_combined_k40"}:
        k = 1 if profile_id == "structure_f0_only" else 20 if profile_id == "structure_nearest_k20" else 40
        fractal_features = pd.DataFrame([extract_fractal_feature_dict(row, k) for _, row in entries.iterrows()], index=out.index)
        out = pd.concat([out, fractal_features], axis=1)
        if profile_id == "structure_f0_only":
            parsed_f0 = [parse_serialized_fractal(value) for value in entries.get("fractal0", pd.Series(index=entries.index, dtype=object))]
            for field in ("price", "up_3", "dn_3", "up_6", "dn_6", "up_12", "dn_12", "up_24", "dn_24", "up_48", "dn_48"):
                out[f"fractal0_{field}"] = [float(item.get(field, 0.0)) if item else 0.0 for item in parsed_f0]
    if profile_id == "movement_plus_time":
        if "movement_score" not in out:
            raise ValueError("movement_plus_time requires movement_score provenance; do not fill with zero")
    feature_columns = rich_feature_allowlist(profile_id)
    missing = [col for col in feature_columns if col not in out.columns]
    if missing:
        raise ValueError(f"missing feature columns for {profile_id}: {missing[:10]}")
    _assert_no_forbidden_feature_columns(feature_columns)
    return out[feature_columns].copy(), audit
```

- [ ] **Step 4: Run feature tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_entry_quality_filter.py::test_rich_feature_frame_uses_closed_h1_and_forbids_top_level_targets tests/test_fractal0_entry_quality_filter.py::test_structure_all100_is_diagnostic_only -q
```

Expected: PASS.

---

### Task 4: Add Model Training For Rich Targets

**Files:**
- Modify: `ML/baseline/benchmark_fractal0_entry_quality_filter.py`
- Test: `tests/test_fractal0_entry_quality_filter.py`

**Interfaces:**
- Produces: `train_rich_entry_model(x_train: pd.DataFrame, y_train: pd.Series, target_kind: str, model_id: str, threads: int, seed: int) -> object`
- Produces: `score_rich_entry_model(model: object, x_rows: pd.DataFrame, target_kind: str) -> np.ndarray`

- [ ] **Step 1: Write failing tests for regression and classification scoring**

Add:

```python
def test_train_rich_entry_model_scores_classification_and_regression():
    x = pd.DataFrame({"a": [0.0, 1.0, 2.0, 3.0], "b": [1.0, 1.0, 0.0, 0.0]})
    y_cls = pd.Series([0, 0, 1, 1])
    y_reg = pd.Series([-1.0, -0.5, 0.5, 1.0])

    cls_model = runner.train_rich_entry_model(x, y_cls, "classification", "extra_trees_shallow", threads=1, seed=42)
    reg_model = runner.train_rich_entry_model(x, y_reg, "regression", "linear", threads=1, seed=42)

    cls_score = runner.score_rich_entry_model(cls_model, x, "classification")
    reg_score = runner.score_rich_entry_model(reg_model, x, "regression")

    assert cls_score.shape == (4,)
    assert reg_score.shape == (4,)
    assert ((cls_score >= 0.0) & (cls_score <= 1.0)).all()
```

- [ ] **Step 2: Run test and verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_entry_quality_filter.py::test_train_rich_entry_model_scores_classification_and_regression -q
```

Expected: FAIL because functions are missing.

- [ ] **Step 3: Implement model helpers**

Add below `train_entry_models()`:

```python
def train_rich_entry_model(
    x_train: pd.DataFrame,
    y_train: pd.Series,
    target_kind: str,
    model_id: str,
    threads: int,
    seed: int,
) -> object:
    x = x_train.fillna(0.0)
    y = y_train.dropna()
    x = x.loc[y.index]
    if target_kind == "classification":
        y = y.astype(int)
        if y.nunique() < 2:
            return float(y.iloc[0]) if len(y) else 0.0
        if model_id == "linear":
            model = LogisticRegression(max_iter=500, random_state=seed)
        elif model_id == "hist_gradient_boosting":
            model = HistGradientBoostingClassifier(max_iter=100, max_leaf_nodes=15, min_samples_leaf=50, random_state=seed)
        elif model_id == "extra_trees_shallow":
            model = ExtraTreesClassifier(n_estimators=160, max_depth=6, min_samples_leaf=60, random_state=seed, n_jobs=threads)
        elif model_id == "extra_trees_current":
            model = ExtraTreesClassifier(n_estimators=200, max_depth=8, min_samples_leaf=50, random_state=seed, n_jobs=threads)
        elif model_id == "random_forest_shallow":
            model = RandomForestClassifier(n_estimators=120, max_depth=6, min_samples_leaf=60, random_state=seed, n_jobs=threads)
        else:
            raise ValueError(f"unsupported rich classification model_id: {model_id}")
    else:
        if model_id == "linear":
            model = Ridge(alpha=1.0, random_state=seed)
        elif model_id == "hist_gradient_boosting":
            model = HistGradientBoostingRegressor(max_iter=100, max_leaf_nodes=15, min_samples_leaf=50, random_state=seed)
        elif model_id == "extra_trees_shallow":
            model = ExtraTreesRegressor(n_estimators=160, max_depth=6, min_samples_leaf=60, random_state=seed, n_jobs=threads)
        elif model_id == "extra_trees_current":
            model = ExtraTreesRegressor(n_estimators=200, max_depth=8, min_samples_leaf=50, random_state=seed, n_jobs=threads)
        elif model_id == "random_forest_shallow":
            model = RandomForestRegressor(n_estimators=120, max_depth=6, min_samples_leaf=60, random_state=seed, n_jobs=threads)
        else:
            raise ValueError(f"unsupported rich regression model_id: {model_id}")
    model.fit(x, y)
    return model


def score_rich_entry_model(model: object, x_rows: pd.DataFrame, target_kind: str) -> np.ndarray:
    if isinstance(model, float):
        return np.full(len(x_rows), model, dtype=float)
    x = x_rows.fillna(0.0)
    if target_kind == "classification":
        return np.asarray(model.predict_proba(x)[:, 1], dtype=float)
    return np.asarray(model.predict(x), dtype=float)
```

- [ ] **Step 4: Run model helper test**

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_entry_quality_filter.py::test_train_rich_entry_model_scores_classification_and_regression -q
```

Expected: PASS.

---

### Task 5: Add Winner Eligibility And Summary Selection

**Files:**
- Modify: `ML/baseline/benchmark_fractal0_entry_quality_filter.py`
- Test: `tests/test_fractal0_entry_quality_filter.py`

**Interfaces:**
- Produces: `select_rich_winner(summary: pd.DataFrame) -> dict[str, object]`
- Produces: `evaluate_rich_verdict(selected_val_eval: dict[str, object], controls: dict[str, object]) -> str`

- [ ] **Step 1: Write failing selection tests**

Add:

```python
def test_select_rich_winner_ignores_diagnostic_rows_and_low_n():
    summary = pd.DataFrame(
        [
            {"profile_id": "structure_all100", "model_id": "extra_trees_current", "target_id": "target_entry_good_0_5r", "filter_id": "top10", "split": "val_select", "bs_p05": 9.0, "max_drawdown_r": 1.0, "n_trades": 50, "eligible_for_winner": False},
            {"profile_id": "rich_combined_k40", "model_id": "hist_gradient_boosting", "target_id": "target_entry_good_0_5r", "filter_id": "top30", "split": "val_select", "bs_p05": 2.5, "max_drawdown_r": 2.0, "n_trades": 500, "eligible_for_winner": True},
            {"profile_id": "time_only", "model_id": "linear", "target_id": "target_entry_avoid_sl", "filter_id": "top50", "split": "val_select", "bs_p05": 2.4, "max_drawdown_r": 1.5, "n_trades": 500, "eligible_for_winner": True},
        ]
    )
    winner = runner.select_rich_winner(summary)
    assert winner["profile_id"] == "rich_combined_k40"
    assert winner["filter_id"] == "top30"


def test_rich_verdict_ignores_diagnostic_best_val_eval():
    selected = {"profile_id": "rich_combined_k40", "split": "val_eval", "n_trades": 400, "bs_p05": 2.6}
    diagnostic_best = {"profile_id": "structure_all100", "split": "val_eval", "n_trades": 30, "bs_p05": 99.0, "not_eligible_for_winner": True}
    controls = {"s2_no_mask": {"bs_p05": 2.3}, "s0_x0": {"bs_p05": 2.5}}
    verdict = runner.evaluate_rich_verdict(selected, controls, diagnostic_best_val_eval=diagnostic_best)
    assert verdict == "RESEARCH_HINT_RICH_FEATURES"
```

- [ ] **Step 2: Run test and verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_entry_quality_filter.py::test_select_rich_winner_ignores_diagnostic_rows_and_low_n -q
```

Expected: FAIL because selector is missing.

- [ ] **Step 3: Implement selector**

Add near `select_entry_filter_winner()`:

```python
def select_rich_winner(summary: pd.DataFrame) -> dict[str, object]:
    candidates = summary.loc[
        summary["split"].eq("val_select")
        & summary["eligible_for_winner"].astype(bool)
        & (pd.to_numeric(summary["n_trades"], errors="coerce") >= 300)
    ].copy()
    if candidates.empty:
        return {"status": "no_eligible_winner"}
    candidates["_bs"] = pd.to_numeric(candidates["bs_p05"], errors="coerce").fillna(-np.inf)
    candidates["_dd"] = pd.to_numeric(candidates["max_drawdown_r"], errors="coerce").fillna(np.inf)
    candidates = candidates.sort_values(["_bs", "_dd", "profile_id", "model_id"], ascending=[False, True, True, True])
    return candidates.drop(columns=["_bs", "_dd"]).iloc[0].to_dict()


def evaluate_rich_verdict(
    selected_val_eval: dict[str, object],
    controls: dict[str, object],
    diagnostic_best_val_eval: dict[str, object] | None = None,
) -> str:
    if selected_val_eval.get("status") == "no_eligible_winner":
        return "REJECT_RICH_ENTRY_QUALITY"
    if int(selected_val_eval.get("n_trades") or 0) < 300:
        return "REJECT_RICH_ENTRY_QUALITY"
    selected_bs = float(selected_val_eval.get("bs_p05") or 0.0)
    baseline_bs = max(float(value.get("bs_p05") or 0.0) for value in controls.values() if isinstance(value, dict))
    if selected_bs <= baseline_bs:
        return "REJECT_RICH_ENTRY_QUALITY"
    return RICH_ALLOWED_MAX_VERDICT
```

- [ ] **Step 4: Run selector test**

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_entry_quality_filter.py::test_select_rich_winner_ignores_diagnostic_rows_and_low_n tests/test_fractal0_entry_quality_filter.py::test_rich_verdict_ignores_diagnostic_best_val_eval -q
```

Expected: PASS.

---

### Task 6: Add Rich Runner CLI And Artifacts

**Files:**
- Modify: `ML/baseline/benchmark_fractal0_entry_quality_filter.py`
- Test: `tests/test_fractal0_entry_quality_filter.py`

**Interfaces:**
- Produces: `run_rich_entry_quality(args: argparse.Namespace) -> dict[str, object]`
- CLI: `--rich-entry-quality`
- CLI: `--include-diagnostic-models`
- CLI output prefix default remains unchanged unless `--output-prefix ML/reports/fractal0_rich_entry_quality` is passed.

- [ ] **Step 1: Write smoke test for artifact schema**

Add:

```python
def test_rich_artifact_schema_contains_required_disclosures():
    artifact = runner.empty_rich_artifact(
        search_budget={"n_total_ranked_configs": 243},
        feature_contract=[{"feature": "side_buy", "live_safe": True}],
    )
    assert artifact["experiment"] == "fractal0_rich_entry_quality"
    assert artifact["locked_test"] == "not_opened"
    assert artifact["allowed_max_verdict"] == "RESEARCH_HINT_RICH_FEATURES"
    assert "forbidden_interpretations" in artifact
    assert artifact["selection_policy"]["val_eval"] == "fixed selected_rule only"
```

- [ ] **Step 2: Run test and verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_entry_quality_filter.py::test_rich_artifact_schema_contains_required_disclosures -q
```

Expected: FAIL because `empty_rich_artifact` is missing.

- [ ] **Step 3: Implement artifact helper and CLI flags**

Add:

```python
def empty_rich_artifact(search_budget: dict[str, object], feature_contract: list[dict[str, object]]) -> dict[str, object]:
    return {
        "status": "initialized",
        "experiment": "fractal0_rich_entry_quality",
        "verdict": "research_only",
        "lifecycle_status": "research_hint",
        "allowed_max_verdict": RICH_ALLOWED_MAX_VERDICT,
        "locked_test": "not_opened",
        "selection_policy": {
            "train_core": "trains ML-exit and ML-entry",
            "val_select": "selects exactly one eligible rule",
            "val_eval": "fixed selected_rule only",
            "diagnostic_grid": "not eligible for winner",
        },
        "forbidden_interpretations": ["candidate", "tradable", "live_ready", "production", "permission_to_open_locked_test"],
        "current_search_budget": search_budget,
        "feature_contract": feature_contract,
    }
```

Modify `parse_args()`:

```python
parser.add_argument("--rich-entry-quality", action="store_true")
parser.add_argument("--include-diagnostic-models", action="store_true")
```

Modify `main()`:

```python
def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.rich_entry_quality:
        run_rich_entry_quality(args)
    else:
        run_entry_quality(args)
    return 0
```

Add a first runnable `run_rich_entry_quality()` that performs preflight, builds grids, writes an initialized JSON, and returns it. It must not open `locked_test`.

- [ ] **Step 4: Run schema test**

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_entry_quality_filter.py::test_rich_artifact_schema_contains_required_disclosures -q
```

Expected: PASS.

---

### Task 7: Wire Full Rich Training Loop

**Files:**
- Modify: `ML/baseline/benchmark_fractal0_entry_quality_filter.py`
- Test: `tests/test_fractal0_entry_quality_filter.py`

**Interfaces:**
- Consumes: `build_rich_entry_labels`, `build_rich_feature_frame`, `train_rich_entry_model`, `score_rich_entry_model`, `select_rich_winner`
- Produces CSV artifacts with prefix `ML/reports/fractal0_rich_entry_quality`

- [ ] **Step 1: Add smoke integration test using `--smoke-limit-filters`**

Add a test that calls `parse_args()` only, not the full expensive runner:

```python
def test_parse_args_accepts_rich_entry_quality_flags():
    args = runner.parse_args(
        [
            "--rich-entry-quality",
            "--include-diagnostic-models",
            "--output-prefix",
            "/tmp/fractal0_rich_entry_quality_smoke",
            "--smoke-limit-filters",
            "1",
        ]
    )
    assert args.rich_entry_quality is True
    assert args.include_diagnostic_models is True
    assert args.output_prefix == "/tmp/fractal0_rich_entry_quality_smoke"
```

- [ ] **Step 2: Run the focused test**

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_entry_quality_filter.py::test_parse_args_accepts_rich_entry_quality_flags -q
```

Expected: PASS after Task 6.

- [ ] **Step 3: Implement full loop**

In `run_rich_entry_quality()`:

1. Reuse the existing preflight and stop-grid choice logic from `run_entry_quality()`.
2. Build `entry_cache` for all roles through `base.build_entry_rows()`.
3. Simulate train trades once with `base._simulate_entries()` and create rich labels.
4. Build the default job list from eligible profiles, eligible runnable models, eligible targets, and primary filters only. This default list must contain `243` ranked configurations before split expansion.
5. If `--include-diagnostic-models` is passed, add only diagnostic jobs with `runnable_by_default=true`; keep XGBoost/LightGBM out of the job list unless dependency checks explicitly mark them runnable before the run starts.
6. For every job:
   - build train features;
   - join labels on `position_id`;
   - train model;
   - score `val_select` and `val_eval`;
   - apply the job's filter with cutoff from `val_select`;
   - simulate selected trades with `_simulate_for_filter()`;
   - write one summary row per split.
7. Mark every row with:
   - `eligible_for_winner`;
   - `not_eligible_reason`;
   - `not_eligible_for_winner`;
   - `profile_id`;
   - `model_id`;
   - `target_id`;
   - `filter_id`;
   - `score_cutoff_on_val_select`.
8. Build rich labels for `train_core`, `val_select`, and `val_eval` from `entry_cache[split]` plus simulated filled trades. Regression and quality targets train only on filled rows; `target_entry_filled` uses all planned rows and remains diagnostic-only.
9. Use `select_rich_winner(summary)` only on `val_select`.
10. Evaluate only that selected rule and fixed baselines on `val_eval`.
11. Keep any non-selected `val_eval` rows as diagnostic disclosure only; they must not affect verdict.

Required heartbeat prints:

```python
print(f"rich job start {done + 1}/{total_jobs} profile={profile_id} model={model_id} target={target_id}", flush=True)
print(f"rich job done {done + 1}/{total_jobs} elapsed={time.time() - started:.1f}", flush=True)
```

JSON must include:

```python
"ranked_search_budget": ranked_search_budget,
"diagnostic_budget": diagnostic_budget,
"n_total_executed_configs": len(job_list),
"selected_winner_val_eval": selected_val_eval,
"diagnostic_best_val_eval": diagnostic_best_val_eval,
"diagnostic_best_val_eval_not_eligible": True,
"split_manifest": split_manifest,
"movement_provenance": movement_provenance,
```

- [ ] **Step 4: Run a tiny smoke command**

Run:

```bash
PYTHONUNBUFFERED=1 ./.venv/bin/python ML/baseline/benchmark_fractal0_entry_quality_filter.py \
  --rich-entry-quality \
  --threads 2 \
  --no-resume \
  --output-prefix /tmp/fractal0_rich_entry_quality_smoke \
  --execution-ohlc-path MT/MQL4/Files/XAUUSD_M5_OHLC.csv \
  --stop-policy-id S2_fractal0_buffer_0_5_entry_floor_2 \
  --smoke-limit-filters 1 \
  --permutation-repeats 3
```

Expected: command exits 0 and writes `/tmp/fractal0_rich_entry_quality_smoke.json`.

---

### Task 8: Add Diagnostics And Full Correction Fields

**Files:**
- Modify: `ML/baseline/benchmark_fractal0_entry_quality_filter.py`
- Test: `tests/test_fractal0_entry_quality_filter.py`

**Interfaces:**
- Produces CSVs:
  - `_feature_contract.csv`
  - `_target_distribution.csv`
  - `_planned_order_diagnostics.csv`
  - `_split_manifest.csv`
  - `_feature_distribution_audit.csv`
  - `_score_diagnostics.csv`
  - `_permutation.csv`
  - `_winner_yearly.csv`

- [ ] **Step 1: Write tests for diagnostics shape**

Add:

```python
def test_target_distribution_audit_counts_classes_and_regression_stats_by_split():
    labels = pd.DataFrame(
        {
            "split": ["train_core", "train_core", "val_select", "val_select", "val_select"],
            "side": ["BUY", "SELL", "BUY", "SELL", "SELL"],
            "target_entry_good_0_5r": [1, 0, 1, 1, 0],
            "target_entry_ev_regression": [0.6, -1.0, 0.7, 0.2, -0.3],
        }
    )
    target_contract = {
        "target_entry_good_0_5r": "classification",
        "target_entry_ev_regression": "regression",
    }
    audit = runner.target_distribution_audit(labels, target_contract)
    assert {"split", "side", "target_id", "target_kind", "rows"}.issubset(audit.columns)
    cls = audit.loc[audit["target_id"].eq("target_entry_good_0_5r")]
    reg = audit.loc[audit["target_id"].eq("target_entry_ev_regression")]
    assert {"class_0_count", "class_1_count", "positive_rate", "minority_count"}.issubset(cls.columns)
    assert {"mean", "median", "p05", "p50", "p95", "std", "nan_rate"}.issubset(reg.columns)


def test_split_manifest_has_dates_and_order():
    entries = {
        "val_select": pd.DataFrame({"time": pd.to_datetime(["2020-01-01", "2020-01-02"]), "filled": [True, False]}),
        "val_eval": pd.DataFrame({"time": pd.to_datetime(["2020-02-01", "2020-02-02"]), "filled": [True, True]}),
    }
    manifest = runner.build_split_manifest(entries)
    assert manifest.loc[manifest["split"].eq("val_select"), "max_time"].iloc[0] < manifest.loc[manifest["split"].eq("val_eval"), "min_time"].iloc[0]
    assert int(manifest.loc[manifest["split"].eq("val_eval"), "filled_trades"].iloc[0]) == 2


def test_movement_provenance_blocks_missing_score_contract():
    with pytest.raises(ValueError, match="movement_score provenance"):
        runner.validate_movement_provenance(pd.DataFrame({"position_id": ["a"], "movement_score": [pd.NA]}), {"movement_artifact_path": ""})
```

- [ ] **Step 2: Implement `target_distribution_audit()` and manifest helpers**

Add:

```python
def target_distribution_audit(labels: pd.DataFrame, target_contract: dict[str, str]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for target_id, target_kind in target_contract.items():
        if target_id not in labels:
            continue
        for keys, group in labels.groupby(["split", "side"], dropna=False):
            values = pd.to_numeric(group[target_id], errors="coerce").dropna()
            row = {"split": keys[0], "side": keys[1], "target_id": target_id, "target_kind": target_kind, "rows": int(len(values))}
            if target_kind == "classification":
                ones = int((values == 1).sum())
                zeros = int((values == 0).sum())
                row.update({"class_0_count": zeros, "class_1_count": ones, "positive_rate": float(ones / len(values)) if len(values) else None, "minority_count": min(zeros, ones)})
            else:
                row.update(
                    {
                        "mean": float(values.mean()) if len(values) else None,
                        "median": float(values.median()) if len(values) else None,
                        "p05": float(values.quantile(0.05)) if len(values) else None,
                        "p50": float(values.quantile(0.50)) if len(values) else None,
                        "p95": float(values.quantile(0.95)) if len(values) else None,
                        "std": float(values.std(ddof=0)) if len(values) else None,
                        "nan_rate": float(pd.to_numeric(group[target_id], errors="coerce").isna().mean()) if len(group) else 0.0,
                    }
                )
            rows.append(row)
    return pd.DataFrame(rows)


def build_split_manifest(entry_cache: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for split, entries in entry_cache.items():
        times = pd.to_datetime(entries["time"], errors="coerce")
        filled = entries.get("filled", pd.Series(False, index=entries.index)).fillna(False).astype(bool)
        rows.append(
            {
                "split": split,
                "min_time": times.min(),
                "max_time": times.max(),
                "raw_rows": int(len(entries)),
                "planned_orders": int(len(entries)),
                "filled_trades": int(filled.sum()),
                "fill_rate": float(filled.mean()) if len(filled) else 0.0,
            }
        )
    return pd.DataFrame(rows)


def validate_movement_provenance(entries: pd.DataFrame, provenance: dict[str, object]) -> dict[str, object]:
    required = [
        "movement_artifact_path",
        "movement_artifact_sha256",
        "movement_rule_id",
        "movement_train_period",
        "movement_locked_before_rich_entry_quality",
    ]
    missing = [key for key in required if not provenance.get(key)]
    scores = pd.to_numeric(entries.get("movement_score"), errors="coerce") if "movement_score" in entries else pd.Series(dtype=float)
    if missing or scores.isna().any():
        raise ValueError("movement_score provenance is incomplete or scores contain missing values")
    return {**provenance, "status": "PASS"}
```

- [ ] **Step 3: Add artifact writes**

In `run_rich_entry_quality()`, write:

```python
pd.DataFrame(feature_contract_rows).to_csv(prefix.with_name(prefix.name + "_feature_contract.csv"), sep=";", index=False)
target_distribution.to_csv(prefix.with_name(prefix.name + "_target_distribution.csv"), sep=";", index=False)
pd.DataFrame(planned_diagnostics).to_csv(prefix.with_name(prefix.name + "_planned_order_diagnostics.csv"), sep=";", index=False)
split_manifest.to_csv(prefix.with_name(prefix.name + "_split_manifest.csv"), sep=";", index=False)
feature_distribution_audit.to_csv(prefix.with_name(prefix.name + "_feature_distribution_audit.csv"), sep=";", index=False)
summary.to_csv(prefix.with_name(prefix.name + "_summary.csv"), sep=";", index=False)
scores.to_csv(prefix.with_name(prefix.name + "_scores.csv"), sep=";", index=False)
trades.to_csv(prefix.with_name(prefix.name + "_trades.csv"), sep=";", index=False)
winner_yearly.to_csv(prefix.with_name(prefix.name + "_winner_yearly.csv"), sep=";", index=False)
```

JSON must include:

```python
"selection_protocol_replayed_in_permutation": False,
"permutation_scope": "selected_rule_only",
"permutation_verdict": "diagnostic_only",
"diagnostic_best_val_eval": diagnostic_best,
"diagnostic_best_val_eval_not_eligible": True,
"selected_winner_val_eval": selected_val_eval,
"comparison_controls": controls,
"split_manifest": split_manifest.to_dict(orient="records"),
"movement_provenance": movement_provenance,
```

- [ ] **Step 4: Run focused diagnostics test**

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_entry_quality_filter.py::test_target_distribution_audit_counts_classes_and_regression_stats_by_split tests/test_fractal0_entry_quality_filter.py::test_split_manifest_has_dates_and_order tests/test_fractal0_entry_quality_filter.py::test_movement_provenance_blocks_missing_score_contract -q
```

Expected: PASS.

---

### Task 9: Update Docs And Report Template

**Files:**
- Modify: `docs/ML/benchmark_fractal0_entry_quality_filter.py.md`
- Create after run: `docs/reports/2026-07-21-fractal0-rich-entry-quality.md`

**Interfaces:**
- Consumes final JSON and CSV artifacts from Task 8.

- [ ] **Step 1: Update module docs**

Add a section to `docs/ML/benchmark_fractal0_entry_quality_filter.py.md`:

```markdown
## Rich Entry Quality Mode

Команда:

```bash
PYTHONUNBUFFERED=1 ./.venv/bin/python ML/baseline/benchmark_fractal0_entry_quality_filter.py \
  --rich-entry-quality \
  --threads 24 \
  --no-resume \
  --output-prefix ML/reports/fractal0_rich_entry_quality \
  --execution-ohlc-path MT/MQL4/Files/XAUUSD_M5_OHLC.csv \
  --stop-policy-id S2_fractal0_buffer_0_5_entry_floor_2 \
  --permutation-repeats 200
```

Phase A eligible winner uses 9 feature profiles, 3 models, 3 targets and
3 primary filters: `243` ranked configurations. XGBoost/LightGBM can be run
only as diagnostic-only in Phase A, or as eligible models in a separate
pre-registered Phase B.

Maximum verdict: `RESEARCH_HINT_RICH_FEATURES`. `locked_test` is not opened.
```
```

- [ ] **Step 2: Create report after full run**

Report sections:

```markdown
# Fractal0 Rich Entry Quality

## Context
## Methodology Level
## What Was Done
## Multiple Testing Context
## Feature Contract
## Target Contract
## Split Disclosure
## Results
## Selected Winner On val_select
## Fixed val_eval Check
## Diagnostic Best val_eval
## Baselines
## Limitations
## Verdict
## Next Step
## Related Materials
```

- [ ] **Step 3: Verify docs do not overclaim**

Run:

```bash
rg -n "candidate|live-ready|production|готово|можно запускать" docs/ML/benchmark_fractal0_entry_quality_filter.py.md docs/reports/2026-07-21-fractal0-rich-entry-quality.md
```

Expected: any match is in a forbidden-interpretations block, not in conclusion text.

---

### Task 10: Final Verification And Launch Full Run

**Files:**
- No code edits unless verification exposes a bug.

- [ ] **Step 1: Run focused tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_entry_quality_filter.py -q
```

Expected: all tests in this file pass.

- [ ] **Step 2: Run related regression tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_entry_exit_grid.py -q
```

Expected: all tests pass.

- [ ] **Step 3: Run full test suite**

Run:

```bash
./.venv/bin/python -m pytest tests/ -q
```

Expected: full suite passes.

- [ ] **Step 4: Start full rich-entry run and return to chat**

Run as background terminal:

```bash
PYTHONUNBUFFERED=1 ./.venv/bin/python ML/baseline/benchmark_fractal0_entry_quality_filter.py \
  --rich-entry-quality \
  --threads 24 \
  --no-resume \
  --output-prefix ML/reports/fractal0_rich_entry_quality \
  --execution-ohlc-path MT/MQL4/Files/XAUUSD_M5_OHLC.csv \
  --stop-policy-id S2_fractal0_buffer_0_5_entry_floor_2 \
  --permutation-repeats 200
```

Expected: process starts, heartbeat prints progress. Do not wait for completion; return to chat after confirming it started.

---

### Task 11: Finalize Completed Full Run

**Files:**
- Modify: `docs/ML/benchmark_fractal0_entry_quality_filter.py.md`
- Create: `docs/reports/2026-07-21-fractal0-rich-entry-quality.md`
- Read: `ML/reports/fractal0_rich_entry_quality.json`
- Read: `ML/reports/fractal0_rich_entry_quality_summary.csv`

**Interfaces:**
- Consumes finished artifacts from Task 10.
- Produces final report only after the process exits successfully.

- [ ] **Step 1: Confirm the background process finished**

Use terminal/session status or log tail. Do not read large logs whole.

Expected: runner process exited with code 0 and JSON status is `completed`.

- [ ] **Step 2: Verify required artifacts exist and are non-empty**

Run:

```bash
ls -lh ML/reports/fractal0_rich_entry_quality.json ML/reports/fractal0_rich_entry_quality_summary.csv ML/reports/fractal0_rich_entry_quality_feature_contract.csv ML/reports/fractal0_rich_entry_quality_target_distribution.csv ML/reports/fractal0_rich_entry_quality_split_manifest.csv
```

Expected: all listed files exist. Large trade/scores files may be too large for git and must be disclosed separately.

- [ ] **Step 3: Check artifact consistency without opening large CSVs whole**

Run a bounded Python check:

```bash
./.venv/bin/python - <<'PY'
import json
from pathlib import Path
import pandas as pd

prefix = Path("ML/reports/fractal0_rich_entry_quality")
data = json.loads(prefix.with_suffix(".json").read_text())
summary = pd.read_csv(prefix.with_name(prefix.name + "_summary.csv"), sep=";", nrows=1000)
assert data["locked_test"] == "not_opened"
assert data["allowed_max_verdict"] == "RESEARCH_HINT_RICH_FEATURES"
assert data["diagnostic_best_val_eval_not_eligible"] is True
assert "selected_winner_val_eval" in data
assert "val_eval" in set(summary["split"])
print("rich artifact consistency PASS")
PY
```

Expected: prints `rich artifact consistency PASS`.

- [ ] **Step 4: Write final report**

Create `docs/reports/2026-07-21-fractal0-rich-entry-quality.md` only from finished artifacts. Required conclusion rules:

- report `selected_winner_val_eval`, not diagnostic best, as the checked rule;
- print `diagnostic_best_val_eval` only in a section named `Diagnostic Disclosure: Not Eligible For Winner`;
- state `locked_test=not_opened`;
- state `allowed_max_verdict=RESEARCH_HINT_RICH_FEATURES`;
- compare against `S2/E3/M0/X2 no-mask` and `S0/E3/M0/X0_fixed_r_0_7`;
- include split manifest, planned-vs-filled diagnostics, target distribution, feature contract, and search budget.

- [ ] **Step 5: Run final tests**

Run:

```bash
./.venv/bin/python -m pytest tests/ -q
```

Expected: full suite passes.

---

## Self-Review

Spec coverage:

- Rich feature families are covered by Task 3.
- Planned vs filled universe and no-fill disclosure are covered by Task 2.
- Model matrix and XGBoost/LightGBM diagnostic-only handling are covered by Tasks 1 and 4.
- `val_select` selection and fixed `val_eval` are covered by Task 5.
- Search budget and multiple-testing disclosure are covered by Tasks 1 and 8.
- Report/artifact disclosure is covered by Tasks 8, 9 and 11.
- Test requirements are covered by Tasks 1-8, Task 10 and Task 11.

Known implementation note:

- Task 3 now blocks full execution until real serialized `fractal*` parsing and profile allowlists are implemented. A zero-filled structural placeholder is not acceptable for this plan.
