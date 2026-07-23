# Fractal0 Rich Entry Quality Normalized Rerun Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Re-run Fractal0 rich entry-quality search with a corrected feature contract: all price-like inputs are ATR-based and all final model inputs are bounded to `0..1`, then compare the result with the previous rich run.

**Architecture:** Extend `ML/baseline/benchmark_fractal0_entry_quality_filter.py` with an explicit normalized-rich feature mode instead of overwriting the existing rich mode. Keep the existing entry rows, M5 execution ordering, ML-exit layer, simulator, split roles and metrics. Write normalized artifacts under a new prefix and a new report, then add a short backlink from the old report.

**Tech Stack:** Python 3.10+, pandas, numpy, scikit-learn, pytest, existing `./.venv/bin/python`; no new dependency.

## Global Constraints

- Work on the current feature branch; do not create a worktree.
- Use `./.venv/bin/python`.
- Do not open `locked_test`; all artifacts must say `locked_test=not_opened`.
- Do not overwrite `ML/reports/fractal0_rich_entry_quality.*`; normalized rerun uses prefix `ML/reports/fractal0_rich_entry_quality_normalized`.
- Create a new report: `docs/reports/2026-07-22-fractal0-rich-entry-quality-normalized-rerun.md`.
- Add only a short backlink/errata note to `docs/reports/2026-07-21-fractal0-rich-entry-quality.md`.
- Maximum verdict remains `RESEARCH_HINT_RICH_FEATURES`; no trading candidate, no live-ready claim, no permission to open `locked_test`.
- Use the same ranked search budget as the previous corrected rich run: 9 profiles x 3 models x 3 targets x 3 primary filters = 243 ranked configs.
- Full-selection permutation is not required for this rerun; if not implemented, artifact must state `permutation_null_repeats_executed_for_full_selection=0` and `permutation_gate=NOT_RUN_FOR_FULL_SELECTION`.
- Feature builders must use explicit allowlists; no "all numeric columns".
- All final model inputs in normalized mode must be finite and in `[0.0, 1.0]`.
- Price-like raw inputs are forbidden in normalized model input: `fractal*_price`, `h1_open`, `h1_high`, `h1_low`, `h1_close`, and price-difference columns without `_atr` or `_unit`.
- ATR-based fields must be computed before unit scaling: price-like value -> ATR-coordinate -> train-only unit scaler -> clipped `0..1`.
- Unit scaler fit uses `train_core` only. `val_select` and `val_eval` must never affect scaler bounds.
- Missing values are not silently treated as real zero. If a feature can be missing, add an explicit `*_missing` indicator or fail the profile before training.
- Padding, if any, remains `0.0` and must not participate in scaler fit.
- Normalized mode must build a fixed ordered feature schema per profile before fitting any model: raw feature columns, missing indicator columns, final feature columns, scaler columns, token-present columns, and padded-exclusion masks. `train_core`, `val_select`, and `val_eval` must return exactly the same final column names in exactly the same order.
- Missing indicator columns are part of the schema in advance. They must not appear or disappear depending on whether a concrete split happens to contain `NaN`.
- Padded fractal token fields are not data: `fractal{idx}_present=0.0`, every other field for that token is `0.0`, and padded values are excluded from scaler fit by the token-present mask.
- Primary old-vs-normalized comparison must use the protocol path: select the rule on `val_select`, then report its fixed `val_eval`. Any best-on-`val_eval` table is diagnostic-only and not eligible for winner selection.
- Add diagnostic-only control profiles `atr_only`, `time_plus_atr`, and `planned_geometry_no_atr`. They do not change the 243 ranked-config budget unless explicitly made eligible in a later plan.
- `fractal0_up_*` and `fractal0_dn_*` may be used only with an explicit `updn_provenance_gate` artifact proving they are read from serialized `fractal*` snapshots, not recomputed from Python future labels.
- Commit commands in this plan are checkpoints only. Do not run `git commit` during execution unless the user explicitly approves commits in that execution turn.
- Full tests after Python changes: `./.venv/bin/python -m pytest tests/ -q`.

---

## Methodology Contract

This plan implements the normalization requirements from:

- `docs/methodology/03-feature-contract-leakage.md`: feature contract, train-only normalization, no silent fallback, same training/evaluation contract.
- `docs/methodology/A7-feature-distribution-audit.md`: price-like values must first lose raw market scale through ATR normalization, then may be clipped/scaled.
- `docs/methodology/A8-feature-target-catalog.md`: preferred geometric coordinate is `(price_i - anchor_price) / ATR`; raw absolute price is only diagnostic.

Normalized rerun status:

```text
locked_test = not_opened
allowed_max_verdict = RESEARCH_HINT_RICH_FEATURES
old_rich_run = historical baseline for comparison
normalized_rerun = new research run, not a candidate
```

---

## File Structure

- Modify `ML/baseline/benchmark_fractal0_entry_quality_filter.py`
  - Add normalized feature allowlists.
  - Add ATR-coordinate feature construction.
  - Add train-only unit scaler.
  - Add normalized audit gates.
  - Add comparison artifact writer.
  - Add CLI flag `--normalized-rich-features`.
- Modify `tests/test_fractal0_entry_quality_filter.py`
  - Add tests for ATR price coordinates, raw price ban, train-only scaler, `[0,1]` bounds, and normalized artifact schema.
- Create `docs/reports/2026-07-22-fractal0-rich-entry-quality-normalized-rerun.md`
  - Final report after full rerun.
- Modify `docs/reports/2026-07-21-fractal0-rich-entry-quality.md`
  - Add a short backlink to the normalized rerun report.
- Modify `docs/ML/benchmark_fractal0_entry_quality_filter.py.md`
  - Document normalized rich mode and artifact prefix.
- Modify `CHANGELOG.md`, `CONTEXT_HANDOFF.md`, `wiki/research/fractal-stop-research.md`, `wiki/index.md`, `wiki/log.md`
  - Synchronize final status and comparison after rerun.

New artifacts:

- `ML/reports/fractal0_rich_entry_quality_normalized.json`
- `ML/reports/fractal0_rich_entry_quality_normalized_summary.csv`
- `ML/reports/fractal0_rich_entry_quality_normalized_scores.csv`
- `ML/reports/fractal0_rich_entry_quality_normalized_trades.csv`
- `ML/reports/fractal0_rich_entry_quality_normalized_feature_contract.csv`
- `ML/reports/fractal0_rich_entry_quality_normalized_feature_distribution_audit.csv`
- `ML/reports/fractal0_rich_entry_quality_normalized_normalized_feature_distribution_audit.csv`
- `ML/reports/fractal0_rich_entry_quality_normalized_token_coverage.csv`
- `ML/reports/fractal0_rich_entry_quality_normalized_normalization_config.json`
- `ML/reports/fractal0_rich_entry_quality_normalized_forbidden_column_audit.csv`
- `ML/reports/fractal0_rich_entry_quality_normalized_protocol_comparison.csv`
- `ML/reports/fractal0_rich_entry_quality_normalized_diagnostic_best_val_eval_by_profile.csv`
- `ML/reports/fractal0_rich_entry_quality_normalized_updn_provenance_gate.csv`
- `ML/reports/fractal0_rich_entry_quality_normalized_artifact_auto_check.json`

---

### Task 1: Add Normalized Feature Contract Tests

**Files:**
- Modify: `tests/test_fractal0_entry_quality_filter.py`
- Modify later: `ML/baseline/benchmark_fractal0_entry_quality_filter.py`

**Interfaces:**
- Consumes existing `runner.build_rich_feature_frame(entries, ohlc, profile_id)`.
- Produces tests for new functions:
  - `runner.normalized_rich_feature_allowlist(profile_id: str) -> list[str]`
  - `runner.build_normalized_feature_schema(profile_id: str, raw_frame: pd.DataFrame, missing_capable_columns: list[str] | None = None) -> runner.NormalizedFeatureSchema`
  - `runner.build_normalized_rich_feature_frame(entries: pd.DataFrame, ohlc: pd.DataFrame, profile_id: str) -> tuple[pd.DataFrame, list[dict[str, object]]]`
  - `runner.assert_no_raw_price_like_features(columns: list[str]) -> None`

- [ ] **Step 1: Add failing test for raw price-like ban**

Append to `tests/test_fractal0_entry_quality_filter.py`:

```python
def test_normalized_rich_allowlist_excludes_raw_price_like_columns():
    for profile_id in [
        "atr_only",
        "time_plus_atr",
        "planned_geometry_no_atr",
        "planned_geometry_only",
        "time_only",
        "structure_f0_only",
        "structure_nearest_k20",
        "structure_nearest_k40",
        "relative_geometry_k40",
        "price_action_h1",
        "movement_plus_time",
        "rich_combined_k40",
    ]:
        cols = runner.normalized_rich_feature_allowlist(profile_id)
        assert all(not col.endswith("_price") for col in cols)
        assert not {"h1_open", "h1_high", "h1_low", "h1_close"}.intersection(cols)
        assert "fractal0_price" not in cols
        runner.assert_no_raw_price_like_features(cols)

    for raw_name in ["h1_body", "h1_range", "planned_limit_distance", "entry_price_delta", "fractal12_price"]:
        with pytest.raises(ValueError, match="raw price-like"):
            runner.assert_no_raw_price_like_features([raw_name])
```

- [ ] **Step 2: Run test and verify it fails before implementation**

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_entry_quality_filter.py::test_normalized_rich_allowlist_excludes_raw_price_like_columns -q
```

Expected: `FAIL` with missing `normalized_rich_feature_allowlist` or raw-price check.

- [ ] **Step 3: Add failing test for ATR-scaled fractal geometry**

Append:

```python
def test_normalized_fractal_geometry_uses_atr_coordinates():
    raw0 = "1700000000:100.0:1:2:3:1:0:1:4:5:6:0.1:0.2:0.3:0.4:0.5:0.6:0.7:0.8:0.9:1.0:2.5:12"
    raw1 = "1699996400:104.0:-1:1:2:0:1:0:3:4:5:0.2:0.1:0.4:0.3:0.6:0.5:0.8:0.7:1.0:0.9:2.0:24"
    entries = pd.DataFrame(
        {
            "time": pd.to_datetime(["2020-01-01 10:00:00"]),
            "side": ["BUY"],
            "ATR": [2.0],
            "fractal0_price": [100.0],
            "planned_entry_bid_equivalent": [101.0],
            "planned_protective_stop_price": [97.0],
            "planned_r_value": [4.0],
            "fractal0": [raw0],
            "fractal1": [raw1],
        }
    )
    ohlc = pd.DataFrame(columns=["time", "open", "high", "low", "close"])

    frame, _ = runner.build_normalized_rich_feature_frame(entries, ohlc, "structure_nearest_k20")

    assert "fractal0_price_rel_f0_atr" in frame.columns
    assert "fractal0_distance_to_planned_limit_atr" in frame.columns
    assert "fractal0_distance_to_planned_stop_atr" in frame.columns
    assert "fractal0_present" in frame.columns
    assert "fractal0_price_rel_f0" not in frame.columns
    assert "fractal0_distance_to_planned_limit" not in frame.columns
```

- [ ] **Step 4: Add failing test for padded fractal tokens**

Append:

```python
def test_normalized_fractal_padding_is_zero_and_explicitly_masked():
    raw0 = "1700000000:100.0:1:2:3:1:0:1:4:5:6:0.1:0.2:0.3:0.4:0.5:0.6:0.7:0.8:0.9:1.0:2.5:12"
    entries = pd.DataFrame(
        {
            "time": pd.to_datetime(["2020-01-01 10:00:00"]),
            "side": ["BUY"],
            "ATR": [2.0],
            "fractal0_price": [100.0],
            "planned_entry_bid_equivalent": [101.0],
            "planned_protective_stop_price": [97.0],
            "planned_r_value": [4.0],
            "fractal0": [raw0],
        }
    )
    ohlc = pd.DataFrame(columns=["time", "open", "high", "low", "close"])

    frame, _ = runner.build_normalized_rich_feature_frame(entries, ohlc, "structure_nearest_k20")

    padded_cols = [col for col in frame.columns if col.startswith("fractal1_") and col != "fractal1_present"]
    assert frame.loc[0, "fractal0_present"] == 1.0
    assert frame.loc[0, "fractal1_present"] == 0.0
    assert frame.loc[0, padded_cols].eq(0.0).all()
```

- [ ] **Step 5: Add failing test for stable missing-indicator schema**

Append:

```python
def test_normalized_schema_keeps_missing_indicator_columns_stable_across_splits():
    train = pd.DataFrame({"a": [0.0, 10.0], "b": [5.0, 6.0]})
    val = pd.DataFrame({"a": [1.0, None], "b": [5.0, 7.0]})
    schema = runner.build_normalized_feature_schema("unit_test_profile", train, missing_capable_columns=["a"])
    scaler = runner.fit_unit_scaler({"train_core": train}, schema)

    out_train = runner.apply_unit_scaler(train, scaler, schema)
    out_val = runner.apply_unit_scaler(val, scaler, schema)

    assert list(out_train.columns) == list(out_val.columns)
    assert "a_missing" in out_train.columns
    assert out_train["a_missing"].tolist() == [0.0, 0.0]
    assert out_val["a_missing"].tolist() == [0.0, 1.0]
```

- [ ] **Step 6: Run focused tests and keep expected failures**

Run:

```bash
./.venv/bin/python -m pytest \
  tests/test_fractal0_entry_quality_filter.py::test_normalized_rich_allowlist_excludes_raw_price_like_columns \
  tests/test_fractal0_entry_quality_filter.py::test_normalized_fractal_geometry_uses_atr_coordinates \
  tests/test_fractal0_entry_quality_filter.py::test_normalized_fractal_padding_is_zero_and_explicitly_masked \
  tests/test_fractal0_entry_quality_filter.py::test_normalized_schema_keeps_missing_indicator_columns_stable_across_splits -q
```

Expected: `FAIL`.

- [ ] **Step 7: Commit tests after implementation passes**

Do not commit yet. This task's commit happens after Task 2 makes these tests pass and only if the user has explicitly approved commits.

---

### Task 2: Build ATR-Based Normalized Feature Frames

**Files:**
- Modify: `ML/baseline/benchmark_fractal0_entry_quality_filter.py`
- Test: `tests/test_fractal0_entry_quality_filter.py`

**Interfaces:**
- Produces:
  - `PRICE_LIKE_RAW_FEATURE_PATTERNS: tuple[str, ...]`
  - `assert_no_raw_price_like_features(columns: list[str]) -> None`
  - `normalized_rich_feature_allowlist(profile_id: str) -> list[str]`
  - `extract_normalized_fractal_feature_dict(row: pd.Series, k: int, selection_basis: str = "recent") -> tuple[dict[str, float], dict[str, object]]`
  - `build_normalized_rich_feature_frame(entries: pd.DataFrame, ohlc: pd.DataFrame, profile_id: str) -> tuple[pd.DataFrame, list[dict[str, object]]]`

- [ ] **Step 1: Implement raw price-like feature guard**

In `ML/baseline/benchmark_fractal0_entry_quality_filter.py`, near `_assert_no_forbidden_feature_columns`, add:

```python
RAW_PRICE_LIKE_EXACT = {"h1_open", "h1_high", "h1_low", "h1_close", "h1_body", "h1_range", "fractal0_price"}
RAW_PRICE_LIKE_WORDS = ("open", "high", "low", "close", "body", "range", "price", "distance", "delta")
RAW_PRICE_LIKE_ALLOWED_SUFFIXES = ("_atr", "_unit", "_missing", "_present")


def assert_no_raw_price_like_features(columns: list[str]) -> None:
    bad = []
    for col in columns:
        if col in RAW_PRICE_LIKE_EXACT:
            bad.append(col)
            continue
        lower = col.lower()
        if any(word in lower for word in RAW_PRICE_LIKE_WORDS) and not lower.endswith(RAW_PRICE_LIKE_ALLOWED_SUFFIXES):
            bad.append(col)
    if bad:
        raise ValueError(f"raw price-like features are forbidden in normalized rich mode: {bad[:10]}")
```

- [ ] **Step 2: Add normalized allowlist**

Add:

```python
def normalized_rich_feature_allowlist(profile_id: str) -> list[str]:
    atr_cols = ["ATR"]
    planned_no_atr = ["side_buy", "entry_to_fractal0_atr", "stop_distance_atr", "r_value_atr"]
    planned = ["side_buy", "ATR", "entry_to_fractal0_atr", "stop_distance_atr", "r_value_atr"]
    time_cols = ["session_hour_unit", "weekday_unit", "hour_sin_unit", "hour_cos_unit", "weekday_sin_unit", "weekday_cos_unit"]
    h1_cols = [
        "h1_open_to_planned_limit_atr",
        "h1_high_to_planned_limit_atr",
        "h1_low_to_planned_limit_atr",
        "h1_close_to_planned_limit_atr",
        "h1_body_atr",
        "h1_range_atr",
        "h1_close_position_in_range_unit",
    ]
    movement = ["movement_score"]
    if profile_id == "atr_only":
        return atr_cols
    if profile_id == "time_plus_atr":
        return time_cols + atr_cols
    if profile_id == "planned_geometry_no_atr":
        return planned_no_atr
    if profile_id == "planned_geometry_only":
        return planned
    if profile_id == "time_only":
        return time_cols
    if profile_id == "price_action_h1":
        return h1_cols
    if profile_id == "movement_plus_time":
        return movement + time_cols
    if profile_id == "structure_f0_only":
        return [
            "fractal0_price_to_planned_limit_atr",
            "fractal0_direction_unit",
            "fractal0_front",
            "fractal0_back",
            "fractal0_strong",
            "fractal0_break",
            "fractal0_reverse",
            "fractal0_power",
            "fractal0_count",
            "fractal0_impulse",
            "fractal0_fractal_atr",
            "fractal0_shift",
            "fractal0_up_3",
            "fractal0_dn_3",
            "fractal0_up_6",
            "fractal0_dn_6",
            "fractal0_up_12",
            "fractal0_dn_12",
            "fractal0_up_24",
            "fractal0_dn_24",
            "fractal0_up_48",
            "fractal0_dn_48",
        ]
    if profile_id in {"structure_nearest_k20", "structure_nearest_k40", "relative_geometry_k40", "rich_combined_k40"}:
        k = 20 if profile_id == "structure_nearest_k20" else 40
        fractal_cols: list[str] = []
        for idx in range(k):
            fractal_cols.extend(
                [
                    f"fractal{idx}_present",
                    f"fractal{idx}_price_rel_f0_atr",
                    f"fractal{idx}_direction_unit",
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
                    f"fractal{idx}_distance_to_planned_limit_atr",
                    f"fractal{idx}_distance_to_planned_stop_atr",
                ]
            )
        if profile_id == "relative_geometry_k40":
            return fractal_cols
        if profile_id == "rich_combined_k40":
            return planned + time_cols + h1_cols + fractal_cols
        return fractal_cols
    raise ValueError(f"unknown normalized rich feature profile: {profile_id}")
```

- [ ] **Step 2b: Add diagnostic-only control profiles to the rich profile grid**

Extend `rich_feature_profile_grid()` with these rows and keep `eligible_for_winner=False`:

```python
{"profile_id": "atr_only", "eligible_for_winner": False, "selection_basis": "diagnostic_atr_only"},
{"profile_id": "time_plus_atr", "eligible_for_winner": False, "selection_basis": "diagnostic_time_plus_atr"},
{"profile_id": "planned_geometry_no_atr", "eligible_for_winner": False, "selection_basis": "diagnostic_planned_geometry_no_atr"},
```

The ranked budget remains 243 because these profiles are diagnostic-only. The report must show their `val_select` and fixed `val_eval` metrics separately from eligible winner selection.

- [ ] **Step 3: Implement ATR-based fractal extraction**

Add:

```python
def _safe_atr(row: pd.Series) -> float:
    atr = pd.to_numeric(pd.Series([row.get("ATR")]), errors="coerce").iloc[0]
    if pd.isna(atr) or float(atr) <= 0.0:
        raise ValueError("normalized rich mode requires positive ATR")
    return float(atr)


def extract_normalized_fractal_feature_dict(row: pd.Series, k: int, selection_basis: str = "recent") -> tuple[dict[str, float], dict[str, object]]:
    result: dict[str, float] = {}
    atr = _safe_atr(row)
    fractal0 = parse_serialized_fractal(row.get("fractal0"))
    base_price = float(row.get("fractal0_price", fractal0.get("price") if fractal0 else 0.0) or 0.0)
    planned_limit = float(row.get("planned_entry_bid_equivalent") or 0.0)
    planned_stop = float(row.get("planned_protective_stop_price") or 0.0)
    parsed_items: list[dict[str, object]] = []
    for source_idx in range(100):
        parsed = parse_serialized_fractal(row.get(f"fractal{source_idx}"))
        if parsed:
            parsed_items.append({**parsed, "_source_idx": source_idx})
    if selection_basis == "nearest_to_planned_limit":
        parsed_items = sorted(parsed_items, key=lambda item: (abs(float(item["price"]) - planned_limit), int(item["_source_idx"])))
    else:
        parsed_items = sorted(parsed_items, key=lambda item: int(item["_source_idx"]))
    valid_count = len(parsed_items)
    truncated_count = max(0, valid_count - k)
    for idx in range(k):
        prefix = f"fractal{idx}_"
        parsed = parsed_items[idx] if idx < len(parsed_items) else None
        if parsed is None:
            result[f"{prefix}present"] = 0.0
            for field in (
                "price_rel_f0_atr",
                "direction_unit",
                "front",
                "back",
                "strong",
                "break",
                "reverse",
                "power",
                "count",
                "impulse",
                "fractal_atr",
                "shift",
                "distance_to_planned_limit_atr",
                "distance_to_planned_stop_atr",
            ):
                result[f"{prefix}{field}"] = 0.0
            continue
        price = float(parsed["price"])
        direction = float(parsed.get("direction", 0.0))
        result[f"{prefix}present"] = 1.0
        result[f"{prefix}direction_unit"] = (direction + 1.0) / 2.0
        for field in ("front", "back", "strong", "break", "reverse", "power", "count", "impulse", "fractal_atr", "shift"):
            result[f"{prefix}{field}"] = float(parsed.get(field, 0.0)) if parsed else 0.0
        result[f"{prefix}price_rel_f0_atr"] = (price - base_price) / atr
        result[f"{prefix}distance_to_planned_limit_atr"] = (price - planned_limit) / atr
        result[f"{prefix}distance_to_planned_stop_atr"] = (price - planned_stop) / atr
    token_audit = {
        "valid_token_count": min(valid_count, k),
        "raw_valid_token_count": valid_count,
        "padding_count": max(0, k - valid_count),
        "truncation_count": truncated_count,
        "selection_basis": selection_basis,
        "anchor_for_coordinate": "fractal0_price",
        "anchor_for_selection": "planned_limit" if selection_basis == "nearest_to_planned_limit" else "source_order",
    }
    return result, token_audit
```

- [ ] **Step 4: Implement normalized rich frame builder**

Add:

```python
def build_normalized_rich_feature_frame(entries: pd.DataFrame, ohlc: pd.DataFrame, profile_id: str) -> tuple[pd.DataFrame, list[dict[str, object]]]:
    out = build_entry_feature_frame(entries)
    audit: list[dict[str, object]] = []
    atr = pd.to_numeric(out["ATR"], errors="coerce").replace(0, pd.NA)
    planned_limit = pd.to_numeric(out["planned_entry_bid_equivalent"], errors="coerce")
    if profile_id in {"time_only", "time_plus_atr", "movement_plus_time", "rich_combined_k40"}:
        times = pd.to_datetime(out["time"])
        hour = times.dt.hour.astype(float)
        weekday = times.dt.weekday.astype(float)
        out["session_hour_unit"] = hour / 23.0
        out["weekday_unit"] = weekday / 6.0
        out["hour_sin_unit"] = (np.sin(2 * np.pi * hour / 24.0) + 1.0) / 2.0
        out["hour_cos_unit"] = (np.cos(2 * np.pi * hour / 24.0) + 1.0) / 2.0
        out["weekday_sin_unit"] = (np.sin(2 * np.pi * weekday / 7.0) + 1.0) / 2.0
        out["weekday_cos_unit"] = (np.cos(2 * np.pi * weekday / 7.0) + 1.0) / 2.0
    if profile_id in {"price_action_h1", "rich_combined_k40"}:
        out, _ = _attach_closed_h1_features(out, ohlc)
        for col in ("open", "high", "low", "close"):
            out[f"h1_{col}_to_planned_limit_atr"] = (pd.to_numeric(out[f"h1_{col}"], errors="coerce") - planned_limit) / atr
        out["h1_body_atr"] = pd.to_numeric(out["h1_body"], errors="coerce") / atr
        out["h1_range_atr"] = pd.to_numeric(out["h1_range"], errors="coerce") / atr
        out["h1_close_position_in_range_unit"] = pd.to_numeric(out["h1_close_position_in_range"], errors="coerce")
    if profile_id in {"structure_f0_only", "structure_nearest_k20", "structure_nearest_k40", "relative_geometry_k40", "rich_combined_k40"}:
        k = 1 if profile_id == "structure_f0_only" else 40
        basis = "recent" if profile_id == "structure_f0_only" else "nearest_to_planned_limit"
        extracted = [extract_normalized_fractal_feature_dict(row, k, selection_basis=basis) for _, row in entries.iterrows()]
        fractal_features = pd.DataFrame([features for features, _ in extracted], index=out.index)
        audit.extend([{**token_audit, "profile_id": profile_id, "row_index": idx} for idx, (_, token_audit) in enumerate(extracted)])
        out = pd.concat([out, fractal_features], axis=1)
        if profile_id == "structure_f0_only":
            parsed_f0 = [parse_serialized_fractal(value) for value in entries.get("fractal0", pd.Series(index=entries.index, dtype=object))]
            out["fractal0_price_to_planned_limit_atr"] = (pd.to_numeric(out["fractal0_price"], errors="coerce") - planned_limit) / atr
            for field in ("up_3", "dn_3", "up_6", "dn_6", "up_12", "dn_12", "up_24", "dn_24", "up_48", "dn_48"):
                out[f"fractal0_{field}"] = [float(item.get(field, 0.0)) if item else 0.0 for item in parsed_f0]
    if profile_id == "movement_plus_time" and ("movement_score" not in out or pd.to_numeric(out["movement_score"], errors="coerce").isna().any()):
        raise ValueError("movement_plus_time requires movement_score provenance; do not fill with zero")
    feature_columns = normalized_rich_feature_allowlist(profile_id)
    missing = [col for col in feature_columns if col not in out.columns]
    if missing:
        raise ValueError(f"missing normalized feature columns for {profile_id}: {missing[:10]}")
    _assert_no_forbidden_feature_columns(feature_columns)
    assert_no_raw_price_like_features(feature_columns)
    audit.extend([{"feature": col, "normalization_stage": "pre_scaler_atr_or_unit", "live_safe": True} for col in feature_columns])
    return out[feature_columns].copy(), audit
```

- [ ] **Step 5: Run focused tests**

Run:

```bash
./.venv/bin/python -m pytest \
  tests/test_fractal0_entry_quality_filter.py::test_normalized_rich_allowlist_excludes_raw_price_like_columns \
  tests/test_fractal0_entry_quality_filter.py::test_normalized_fractal_geometry_uses_atr_coordinates \
  tests/test_fractal0_entry_quality_filter.py::test_normalized_fractal_padding_is_zero_and_explicitly_masked \
  tests/test_fractal0_entry_quality_filter.py::test_normalized_schema_keeps_missing_indicator_columns_stable_across_splits -q
```

Expected: `4 passed`.

- [ ] **Step 6: Commit Task 1-2**

If the user explicitly approved commits for execution, run:

```bash
git add ML/baseline/benchmark_fractal0_entry_quality_filter.py tests/test_fractal0_entry_quality_filter.py
git commit -m "Add normalized rich feature contract"
```

If commit approval was not explicit in the execution turn, leave the changes uncommitted and continue.

---

### Task 3: Add Train-Only Unit Scaling And Range Gates

**Files:**
- Modify: `ML/baseline/benchmark_fractal0_entry_quality_filter.py`
- Modify: `tests/test_fractal0_entry_quality_filter.py`

**Interfaces:**
- Produces:
  - `NormalizedFeatureSchema`
  - `build_normalized_feature_schema(profile_id: str, raw_frame: pd.DataFrame, missing_capable_columns: list[str] | None = None) -> NormalizedFeatureSchema`
  - `fit_unit_scaler(frames: dict[str, pd.DataFrame], schema: NormalizedFeatureSchema) -> dict[str, dict[str, float]]`
  - `apply_unit_scaler(frame: pd.DataFrame, scaler: dict[str, dict[str, float]], schema: NormalizedFeatureSchema) -> pd.DataFrame`
  - `assert_unit_scaled_frame(frame: pd.DataFrame, profile_id: str) -> None`
  - `normalized_feature_distribution_audit(frames: dict[tuple[str, str], pd.DataFrame]) -> pd.DataFrame`
  - `token_coverage_audit(token_rows: list[dict[str, object]]) -> pd.DataFrame`

- [ ] **Step 1: Add failing test for train-only scaler**

Append:

```python
def test_unit_scaler_fits_train_only_and_clips_validation():
    train = pd.DataFrame({"a": [0.0, 10.0], "b": [5.0, 5.0]})
    val = pd.DataFrame({"a": [-100.0, 100.0], "b": [5.0, 7.0]})
    schema = runner.build_normalized_feature_schema("unit_test_profile", train)
    scaler = runner.fit_unit_scaler({"train_core": train}, schema)

    out_train = runner.apply_unit_scaler(train, scaler, schema)
    out_val = runner.apply_unit_scaler(val, scaler, schema)

    assert out_train["a"].tolist() == [0.0, 1.0]
    assert out_train["b"].tolist() == [0.0, 0.0]
    assert out_val["a"].tolist() == [0.0, 1.0]
    assert out_val["b"].tolist() == [0.0, 0.0]
    assert scaler["a"]["fit_split"] == "train_core"
    assert scaler["b"]["constant"] is True
```

- [ ] **Step 2: Add failing test for final `[0,1]` contract**

Append:

```python
def test_assert_unit_scaled_frame_rejects_out_of_range_values():
    frame = pd.DataFrame({"ok": [0.0, 0.5, 1.0], "bad": [0.0, 1.2, 0.3]})
    with pytest.raises(ValueError, match="outside 0..1"):
        runner.assert_unit_scaled_frame(frame, "unit_test_profile")
```

- [ ] **Step 3: Implement scaler functions**

At the top of `ML/baseline/benchmark_fractal0_entry_quality_filter.py`, add:

```python
from dataclasses import asdict, dataclass
```

Then add near feature-audit helpers:

```python
@dataclass(frozen=True)
class NormalizedFeatureSchema:
    profile_id: str
    raw_feature_columns: tuple[str, ...]
    missing_indicator_columns: tuple[str, ...]
    final_feature_columns: tuple[str, ...]
    scaler_columns: tuple[str, ...]
    non_scaled_columns: tuple[str, ...]
    token_present_columns: tuple[str, ...]
    padded_exclusion_masks: dict[str, str]


def build_normalized_feature_schema(
    profile_id: str,
    raw_frame: pd.DataFrame,
    missing_capable_columns: list[str] | None = None,
) -> NormalizedFeatureSchema:
    raw_columns = tuple(str(col) for col in raw_frame.columns)
    missing_source = set(missing_capable_columns or raw_columns)
    missing_columns = tuple(f"{col}_missing" for col in raw_columns if col in missing_source)
    token_present_columns = tuple(col for col in raw_columns if col.startswith("fractal") and col.endswith("_present"))
    padded_exclusion_masks: dict[str, str] = {}
    for col in raw_columns:
        if not col.startswith("fractal") or col.endswith("_present"):
            continue
        token_id = col.split("_", 1)[0]
        present_col = f"{token_id}_present"
        if present_col in raw_columns:
            padded_exclusion_masks[col] = present_col
    non_scaled_columns = tuple(
        col
        for col in raw_columns
        if col == "side_buy" or col.endswith("_unit") or col.endswith("_present")
    )
    scaler_columns = tuple(col for col in raw_columns if col not in set(non_scaled_columns))
    final_columns = raw_columns + missing_columns
    return NormalizedFeatureSchema(
        profile_id=profile_id,
        raw_feature_columns=raw_columns,
        missing_indicator_columns=missing_columns,
        final_feature_columns=final_columns,
        scaler_columns=scaler_columns,
        non_scaled_columns=non_scaled_columns,
        token_present_columns=token_present_columns,
        padded_exclusion_masks=padded_exclusion_masks,
    )


def fit_unit_scaler(frames: dict[str, pd.DataFrame], schema: NormalizedFeatureSchema) -> dict[str, dict[str, float]]:
    train = frames.get("train_core")
    if train is None or train.empty:
        raise ValueError("unit scaler requires non-empty train_core frame")
    scaler: dict[str, dict[str, float]] = {}
    for col in schema.scaler_columns:
        if col not in train:
            raise ValueError(f"train_core missing feature required by schema: {col}")
        values = pd.to_numeric(train[col], errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
        mask_col = schema.padded_exclusion_masks.get(col)
        if mask_col:
            mask = pd.to_numeric(train[mask_col], errors="coerce").fillna(0.0).eq(1.0)
            values = pd.to_numeric(train.loc[mask, col], errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
        if values.empty:
            scaler[col] = {"low": 0.0, "high": 0.0, "constant": True, "fit_split": "train_core"}
            continue
        low = float(values.quantile(0.01))
        high = float(values.quantile(0.99))
        if not np.isfinite(low) or not np.isfinite(high) or high <= low:
            low = float(values.min())
            high = float(values.max())
        constant = bool(not np.isfinite(low) or not np.isfinite(high) or high <= low)
        scaler[col] = {"low": low, "high": high, "constant": constant, "fit_split": "train_core"}
    return scaler


def apply_unit_scaler(frame: pd.DataFrame, scaler: dict[str, dict[str, float]], schema: NormalizedFeatureSchema) -> pd.DataFrame:
    out = pd.DataFrame(index=frame.index)
    missing_cols = {name[:-8] for name in schema.missing_indicator_columns if name.endswith("_missing")}
    for col in schema.raw_feature_columns:
        if col not in frame:
            raise ValueError(f"frame missing feature required by schema: {col}")
        values = pd.to_numeric(frame[col], errors="coerce")
        if col in missing_cols:
            out[f"{col}_missing"] = values.isna().astype(float)
        values = values.fillna(0.0)
        if col in schema.non_scaled_columns:
            out[col] = values.clip(lower=0.0, upper=1.0).astype(float)
            continue
        cfg = scaler.get(col)
        if cfg is None:
            raise ValueError(f"missing unit scaler config for feature: {col}")
        if bool(cfg.get("constant")):
            out[col] = 0.0
            continue
        low = float(cfg["low"])
        high = float(cfg["high"])
        scaled = (values.clip(lower=low, upper=high) - low) / (high - low)
        out[col] = scaled.astype(float)
    return out.loc[:, list(schema.final_feature_columns)]


def assert_unit_scaled_frame(frame: pd.DataFrame, profile_id: str) -> None:
    numeric = frame.apply(pd.to_numeric, errors="coerce")
    if numeric.isna().any().any():
        bad = numeric.columns[numeric.isna().any()].tolist()
        raise ValueError(f"normalized profile {profile_id} contains NaN features: {bad[:10]}")
    if np.isinf(numeric.to_numpy(dtype=float)).any():
        raise ValueError(f"normalized profile {profile_id} contains Inf features")
    low = float(numeric.min().min()) if not numeric.empty else 0.0
    high = float(numeric.max().max()) if not numeric.empty else 0.0
    if low < -1e-12 or high > 1.0 + 1e-12:
        raise ValueError(f"normalized profile {profile_id} has features outside 0..1: min={low}, max={high}")
```

- [ ] **Step 4: Add normalized feature distribution audit**

Add:

```python
def normalized_feature_distribution_audit(frames: dict[tuple[str, str], pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    train_stats: dict[tuple[str, str], dict[str, float | None]] = {}
    for (split, profile_id), frame in frames.items():
        numeric = frame.apply(pd.to_numeric, errors="coerce")
        for col in numeric.columns:
            series = numeric[col]
            valid = series.replace([np.inf, -np.inf], np.nan).dropna()
            stats = {
                "min": float(valid.min()) if len(valid) else None,
                "p1": float(valid.quantile(0.01)) if len(valid) else None,
                "p5": float(valid.quantile(0.05)) if len(valid) else None,
                "p25": float(valid.quantile(0.25)) if len(valid) else None,
                "p50": float(valid.quantile(0.50)) if len(valid) else None,
                "p75": float(valid.quantile(0.75)) if len(valid) else None,
                "p95": float(valid.quantile(0.95)) if len(valid) else None,
                "p99": float(valid.quantile(0.99)) if len(valid) else None,
                "max": float(valid.max()) if len(valid) else None,
                "mean": float(valid.mean()) if len(valid) else None,
                "std": float(valid.std(ddof=0)) if len(valid) else None,
            }
            if split == "train_core":
                train_stats[(profile_id, col)] = stats
            train = train_stats.get((profile_id, col), {})
            train_p95 = train.get("p95")
            train_std = train.get("std")
            p95_shift_vs_train = None
            if split != "train_core" and train_p95 is not None and train_std not in (None, 0.0):
                p95_shift_vs_train = (stats["p95"] - train_p95) / train_std if stats["p95"] is not None else None
            rows.append(
                {
                    "split": split,
                    "profile_id": profile_id,
                    "feature": col,
                    "rows": int(len(series)),
                    "n_valid": int(len(valid)),
                    "missing_rate": float(series.isna().mean()) if len(series) else 0.0,
                    "zero_rate": float(series.fillna(np.nan).eq(0.0).mean()) if len(series) else 0.0,
                    "inf_rate": float(np.isinf(series.to_numpy(dtype=float, na_value=np.nan)).mean()) if len(series) else 0.0,
                    "below_zero_rate": float(series.lt(0.0).mean()) if len(series) else 0.0,
                    "above_one_rate": float(series.gt(1.0).mean()) if len(series) else 0.0,
                    **stats,
                    "frac_abs_gt3": float(valid.abs().gt(3.0).mean()) if len(valid) else 0.0,
                    "frac_abs_gt5": float(valid.abs().gt(5.0).mean()) if len(valid) else 0.0,
                    "frac_abs_gt10": float(valid.abs().gt(10.0).mean()) if len(valid) else 0.0,
                    "frac_abs_gt20": float(valid.abs().gt(20.0).mean()) if len(valid) else 0.0,
                    "unique_count": int(series.nunique(dropna=True)),
                    "constant": bool(valid.nunique(dropna=True) <= 1),
                    "near_constant": bool(valid.nunique(dropna=True) <= 2 or (len(valid) and valid.value_counts(normalize=True, dropna=True).iloc[0] >= 0.99)),
                    "p95_shift_vs_train_std": p95_shift_vs_train,
                    "flag": "ERROR" if series.isna().any() or float(series.lt(0.0).mean()) > 0.0 or float(series.gt(1.0).mean()) > 0.0 else ("WARNING" if valid.nunique(dropna=True) <= 1 or float(series.eq(0.0).mean()) > 0.95 else "PASS"),
                }
            )
    return pd.DataFrame(rows)


def token_coverage_audit(token_rows: list[dict[str, object]]) -> pd.DataFrame:
    if not token_rows:
        return pd.DataFrame(columns=["split", "profile_id", "rows", "p50_valid_token_count", "padding_rate", "truncation_rate", "anchor_for_coordinate", "anchor_for_selection"])
    frame = pd.DataFrame(token_rows)
    rows: list[dict[str, object]] = []
    for (split, profile_id), group in frame.groupby(["split", "profile_id"], dropna=False):
        valid = pd.to_numeric(group["valid_token_count"], errors="coerce")
        padding = pd.to_numeric(group["padding_count"], errors="coerce")
        raw_valid = pd.to_numeric(group["raw_valid_token_count"], errors="coerce")
        truncation = pd.to_numeric(group["truncation_count"], errors="coerce")
        denom = (valid + padding).replace(0, np.nan)
        rows.append(
            {
                "split": split,
                "profile_id": profile_id,
                "rows": int(len(group)),
                "p5_valid_token_count": float(valid.quantile(0.05)),
                "p25_valid_token_count": float(valid.quantile(0.25)),
                "p50_valid_token_count": float(valid.quantile(0.50)),
                "p75_valid_token_count": float(valid.quantile(0.75)),
                "p95_valid_token_count": float(valid.quantile(0.95)),
                "rows_with_zero_tokens_rate": float(raw_valid.eq(0).mean()),
                "padding_rate": float((padding / denom).mean()),
                "truncation_rate": float(truncation.gt(0).mean()),
                "anchor_for_coordinate": str(group["anchor_for_coordinate"].iloc[0]),
                "anchor_for_selection": str(group["anchor_for_selection"].iloc[0]),
                "flag": "ERROR" if raw_valid.eq(0).any() else ("WARNING" if truncation.gt(0).any() else "PASS"),
            }
        )
    return pd.DataFrame(rows)
```

- [ ] **Step 5: Run focused tests**

Run:

```bash
./.venv/bin/python -m pytest \
  tests/test_fractal0_entry_quality_filter.py::test_unit_scaler_fits_train_only_and_clips_validation \
  tests/test_fractal0_entry_quality_filter.py::test_assert_unit_scaled_frame_rejects_out_of_range_values -q
```

Expected: `2 passed`.

- [ ] **Step 6: Commit**

If the user explicitly approved commits for execution, run:

```bash
git add ML/baseline/benchmark_fractal0_entry_quality_filter.py tests/test_fractal0_entry_quality_filter.py
git commit -m "Add train-only unit scaling for rich features"
```

If commit approval was not explicit in the execution turn, leave the changes uncommitted and continue.

---

### Task 4: Wire Normalized Mode Into Rich Runner

**Files:**
- Modify: `ML/baseline/benchmark_fractal0_entry_quality_filter.py`
- Modify: `tests/test_fractal0_entry_quality_filter.py`

**Interfaces:**
- Consumes Task 2-3 functions.
- Produces CLI flag `--normalized-rich-features`.
- Produces JSON fields:
  - `feature_contract_variant="normalized_atr_unit"`
  - `normalization_config`
  - `normalized_feature_distribution_audit_csv`
  - `token_coverage_csv`
  - `updn_provenance_gate_csv`
  - `legacy_rich_artifact_for_comparison`

- [ ] **Step 1: Add CLI flag**

In `parse_args()` add:

```python
parser.add_argument("--normalized-rich-features", action="store_true")
```

- [ ] **Step 2: Choose output prefix safely**

In `run_rich_entry_quality(args)`, after prefix is computed, add:

```python
if args.normalized_rich_features and args.output_prefix == "ML/reports/fractal0_entry_quality_filter":
    args.output_prefix = "ML/reports/fractal0_rich_entry_quality_normalized"
```

If the code currently rewrites default rich prefix, preserve that behavior and make normalized mode use:

```python
DEFAULT_NORMALIZED_RICH_OUTPUT_PREFIX = "ML/reports/fractal0_rich_entry_quality_normalized"
```

- [ ] **Step 3: Build raw frames, fit scaler on train, transform every split**

In the section where rich feature frames are built per profile/split, use:

```python
schemas_by_profile: dict[str, NormalizedFeatureSchema] = {}
all_token_rows: list[dict[str, object]] = []

if args.normalized_rich_features:
    raw_profile_frames: dict[str, pd.DataFrame] = {}
    for split_name, entries_for_split in entries_by_split.items():
        raw_frame, raw_contract_rows = build_normalized_rich_feature_frame(entries_for_split, h1_ohlc, profile_id)
        raw_profile_frames[split_name] = raw_frame
        for row in raw_contract_rows:
            if "valid_token_count" in row:
                all_token_rows.append({**row, "split": split_name})
    schema = build_normalized_feature_schema(profile_id, raw_profile_frames["train_core"])
    schemas_by_profile[profile_id] = schema
    scaler = fit_unit_scaler({"train_core": raw_profile_frames["train_core"]}, schema)
    for split_name, raw_frame in raw_profile_frames.items():
        scaled = apply_unit_scaler(raw_frame, scaler, schema)
        assert_unit_scaled_frame(scaled, profile_id)
        if list(scaled.columns) != list(schema.final_feature_columns):
            raise ValueError(f"normalized schema mismatch for {profile_id}/{split_name}")
        feature_frames[(split_name, profile_id)] = scaled
else:
    frame, contract_rows = build_rich_feature_frame(entries_for_split, h1_ohlc, profile_id)
```

Adjust this snippet to the actual loop structure, but keep the invariant: scaler is fitted once per profile on `train_core`, then applied to `val_select` and `val_eval`.

- [ ] **Step 4: Save normalization metadata**

Collect:

```python
normalization_config = {
    "mode": "normalized_atr_unit",
    "fit_split": "train_core",
    "price_like_policy": "price-like inputs converted to ATR coordinates before unit scaling",
    "unit_scaler": scalers_by_profile,
    "feature_schemas": {profile_id: asdict(schema) for profile_id, schema in schemas_by_profile.items()},
    "clip_policy": "train_core q01/q99, clipped to 0..1",
    "missing_policy": "missing indicators are schema columns, not split-dependent columns; no silent missing-as-real-zero",
    "padding_policy": "padded fractal token fields remain 0.0 and are excluded from scaler fit by fractalN_present",
}
```

Write:

```python
prefix.with_name(prefix.name + "_normalization_config.json").write_text(
    json.dumps(normalization_config, ensure_ascii=True, indent=2, default=str),
    encoding="utf-8",
	)
```

- [ ] **Step 5: Write normalized audit artifacts**

After all `feature_frames` are available in normalized mode, write:

```python
if args.normalized_rich_features:
    normalized_audit = normalized_feature_distribution_audit(feature_frames)
    normalized_audit_path = prefix.with_name(prefix.name + "_normalized_feature_distribution_audit.csv")
    normalized_audit.to_csv(normalized_audit_path, sep=";", index=False)

    token_coverage = token_coverage_audit(all_token_rows)
    token_coverage_path = prefix.with_name(prefix.name + "_token_coverage.csv")
    token_coverage.to_csv(token_coverage_path, sep=";", index=False)

    updn_gate = normalized_updn_provenance_gate()
    updn_gate_path = prefix.with_name(prefix.name + "_updn_provenance_gate.csv")
    updn_gate.to_csv(updn_gate_path, sep=";", index=False)
```

The existing `*_feature_distribution_audit.csv` remains the pre-scaler ATR/unit audit. The new `*_normalized_feature_distribution_audit.csv` is the final matrix audit after train-only scaling and clipping.

- [ ] **Step 6: Implement normalized feature-contract rows**

Add:

```python
def normalized_rich_feature_contract_rows(profile_ids: list[str], schemas_by_profile: dict[str, NormalizedFeatureSchema]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for profile_id in profile_ids:
        schema = schemas_by_profile.get(profile_id)
        feature_columns = list(schema.final_feature_columns) if schema else normalized_rich_feature_allowlist(profile_id)
        for order, feature in enumerate(feature_columns):
            if feature.endswith("_missing"):
                source = "missing_indicator_from_schema"
                transformation = "1.0 when source feature is missing else 0.0"
                normalization = "already_unit"
            elif feature.startswith("h1_"):
                source = "DATA/XAUUSD_H1_OHLC.csv"
                transformation = "last closed H1 value converted to ATR coordinate or unit value"
                normalization = "ATR coordinate before train-only unit scaling"
            elif feature.startswith("fractal"):
                source = "serialized_fractal_fields"
                transformation = "serialized snapshot field; price-like values converted to ATR coordinates; padded token fields stay zero"
                normalization = "train_core unit scaler, padded values excluded by fractalN_present"
            elif feature == "movement_score":
                source = "frozen_movement_score"
                transformation = "frozen diagnostic score"
                normalization = "train_core unit scaler"
            elif feature in {"session_hour_unit", "weekday_unit", "hour_sin_unit", "hour_cos_unit", "weekday_sin_unit", "weekday_cos_unit"}:
                source = "entry_time"
                transformation = "calendar value mapped to 0..1"
                normalization = "already_unit"
            else:
                source = "planned_execution_geometry"
                transformation = "planned entry geometry converted to ATR coordinate where price-like"
                normalization = "train_core unit scaler"
            rows.append(
                {
                    "profile_id": profile_id,
                    "feature_order": order,
                    "feature": feature,
                    "role": "input",
                    "source": source,
                    "producer": "benchmark_fractal0_entry_quality_filter.py normalized mode",
                    "transformation": transformation,
                    "normalization": normalization,
                    "available_at": "pre_order_after_signal_before_limit_order_send",
                    "decision_time": "pre_order_after_signal_before_limit_order_send",
                    "live_safe": True,
                    "scaler_fit_split": "train_core",
                }
            )
    assert_no_raw_price_like_features([row["feature"] for row in rows])
    return rows
```

In normalized mode, write `*_feature_contract.csv` from `normalized_rich_feature_contract_rows(profile_ids, schemas_by_profile)`, not from legacy `rich_feature_contract_rows(profile_ids)`.

- [ ] **Step 7: Implement `Up/Dn` provenance gate**

Add:

```python
def normalized_updn_provenance_gate() -> pd.DataFrame:
    rows = []
    for horizon in (3, 6, 12, 24, 48):
        for side in ("up", "dn"):
            rows.append(
                {
                    "feature_family": "fractal0_updn",
                    "feature": f"fractal0_{side}_{horizon}",
                    "source": "serialized_fractal_fields",
                    "producer": "lib_PIC",
                    "python_recomputed": False,
                    "top_level_target_column_used": False,
                    "allowed_only_from_fractal_snapshot": True,
                    "status": "PASS",
                }
            )
    return pd.DataFrame(rows)
```

Also add a code assertion before training normalized `structure_f0_only`: no source column matching top-level `up_*`, `dn_*`, `entry_up_*`, or `entry_dn_*` is used as model input.

- [ ] **Step 8: Add artifact fields**

In artifact update add:

```python
"feature_contract_variant": "normalized_atr_unit" if args.normalized_rich_features else "legacy_rich",
"normalization_config": normalization_config if args.normalized_rich_features else None,
"legacy_rich_artifact_for_comparison": str(_path("ML/reports/fractal0_rich_entry_quality.json")) if args.normalized_rich_features else None,
"artifacts": {
    "summary_csv": str(prefix.with_name(prefix.name + "_summary.csv")),
    "scores_csv": str(prefix.with_name(prefix.name + "_scores.csv")),
    "trades_csv": str(prefix.with_name(prefix.name + "_trades.csv")),
    "feature_contract_csv": str(prefix.with_name(prefix.name + "_feature_contract.csv")),
    "feature_distribution_audit_csv": str(prefix.with_name(prefix.name + "_feature_distribution_audit.csv")),
    "normalization_config_json": str(prefix.with_name(prefix.name + "_normalization_config.json")) if args.normalized_rich_features else None,
    "normalized_feature_distribution_audit_csv": str(prefix.with_name(prefix.name + "_normalized_feature_distribution_audit.csv")) if args.normalized_rich_features else None,
    "token_coverage_csv": str(prefix.with_name(prefix.name + "_token_coverage.csv")) if args.normalized_rich_features else None,
    "updn_provenance_gate_csv": str(prefix.with_name(prefix.name + "_updn_provenance_gate.csv")) if args.normalized_rich_features else None,
    "artifact_auto_check_json": str(prefix.with_name(prefix.name + "_artifact_auto_check.json")) if args.normalized_rich_features else None,
}
```

- [ ] **Step 9: Add normalized artifact schema test**

Append:

```python
def test_normalized_artifact_fields_are_explicit():
    artifact = runner.empty_rich_artifact(
        search_budget={"n_total_ranked_configs": 243},
        feature_contract=[{"feature": "side_buy", "live_safe": True}],
    )
    artifact.update(
        {
            "feature_contract_variant": "normalized_atr_unit",
            "normalization_config": {"mode": "normalized_atr_unit", "fit_split": "train_core"},
            "legacy_rich_artifact_for_comparison": "ML/reports/fractal0_rich_entry_quality.json",
            "artifacts": {
                "normalized_feature_distribution_audit_csv": "ML/reports/fractal0_rich_entry_quality_normalized_normalized_feature_distribution_audit.csv",
                "token_coverage_csv": "ML/reports/fractal0_rich_entry_quality_normalized_token_coverage.csv",
                "updn_provenance_gate_csv": "ML/reports/fractal0_rich_entry_quality_normalized_updn_provenance_gate.csv",
            },
            "permutation_null_repeats_executed_for_full_selection": 0,
        }
    )

    assert artifact["feature_contract_variant"] == "normalized_atr_unit"
    assert artifact["normalization_config"]["fit_split"] == "train_core"
    assert artifact["legacy_rich_artifact_for_comparison"].endswith("fractal0_rich_entry_quality.json")
    assert artifact["artifacts"]["token_coverage_csv"].endswith("_token_coverage.csv")
    assert artifact["artifacts"]["updn_provenance_gate_csv"].endswith("_updn_provenance_gate.csv")
```

- [ ] **Step 10: Run focused tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_entry_quality_filter.py -q
```

Expected: all tests pass.

- [ ] **Step 11: Commit**

If the user explicitly approved commits for execution, run:

```bash
git add ML/baseline/benchmark_fractal0_entry_quality_filter.py tests/test_fractal0_entry_quality_filter.py
git commit -m "Wire normalized rich feature mode"
```

If commit approval was not explicit in the execution turn, leave the changes uncommitted and continue.

---

### Task 5: Add Comparison Artifact

**Files:**
- Modify: `ML/baseline/benchmark_fractal0_entry_quality_filter.py`
- Modify: `tests/test_fractal0_entry_quality_filter.py`

**Interfaces:**
- Produces:
  - `compare_rich_runs_protocol(old_summary: pd.DataFrame, new_summary: pd.DataFrame) -> pd.DataFrame`
  - `diagnostic_best_val_eval_by_profile(summary: pd.DataFrame, prefix: str) -> pd.DataFrame`
  - `*_protocol_comparison.csv`
  - `*_diagnostic_best_val_eval_by_profile.csv`

- [ ] **Step 1: Add failing comparison test**

Append:

```python
def test_compare_rich_runs_protocol_uses_val_select_then_fixed_val_eval():
    old = pd.DataFrame(
        [
            {"split": "val_select", "profile_id": "time_only", "model_id": "linear", "target_id": "target_entry_ev_regression", "filter_id": "top30", "eligible_for_winner": True, "bs_p05": 3.0, "pf": 4.0, "n_trades": 600},
            {"split": "val_eval", "profile_id": "time_only", "model_id": "linear", "target_id": "target_entry_ev_regression", "filter_id": "top30", "eligible_for_winner": True, "bs_p05": 2.7, "pf": 3.7, "n_trades": 610},
            {"split": "val_eval", "profile_id": "time_only", "model_id": "linear", "target_id": "target_entry_good_0_5r", "filter_id": "top10", "eligible_for_winner": True, "bs_p05": 9.9, "pf": 10.0, "n_trades": 120},
        ]
    )
    new = pd.DataFrame(
        [
            {"split": "val_select", "profile_id": "time_only", "model_id": "linear", "target_id": "target_entry_ev_regression", "filter_id": "top30", "eligible_for_winner": True, "bs_p05": 2.5, "pf": 3.5, "n_trades": 600},
            {"split": "val_eval", "profile_id": "time_only", "model_id": "linear", "target_id": "target_entry_ev_regression", "filter_id": "top30", "eligible_for_winner": True, "bs_p05": 2.4, "pf": 3.3, "n_trades": 610},
            {"split": "val_eval", "profile_id": "time_only", "model_id": "linear", "target_id": "target_entry_good_0_5r", "filter_id": "top10", "eligible_for_winner": True, "bs_p05": 8.8, "pf": 9.0, "n_trades": 120},
        ]
    )

    comparison = runner.compare_rich_runs_protocol(old, new)

    row = comparison.loc[comparison["profile_id"].eq("time_only")].iloc[0]
    assert row["old_eval_bs_p05"] == 2.7
    assert row["new_eval_bs_p05"] == 2.4
    assert row["delta_eval_bs_p05"] == pytest.approx(-0.3)
    assert row["old_filter_id"] == "top30"
    assert row["new_filter_id"] == "top30"
```

- [ ] **Step 2: Implement comparison**

Add:

```python
def _selected_val_select_by_profile(summary: pd.DataFrame, prefix: str) -> pd.DataFrame:
    work = summary.loc[summary["split"].astype(str).eq("val_select")].copy()
    if "eligible_for_winner" in work:
        work = work.loc[work["eligible_for_winner"].astype(bool)]
    work = work.loc[pd.to_numeric(work["n_trades"], errors="coerce") >= 300]
    if work.empty:
        return pd.DataFrame(columns=["profile_id"])
    work["_bs"] = pd.to_numeric(work["bs_p05"], errors="coerce").fillna(-np.inf)
    work["_dd"] = pd.to_numeric(work.get("max_drawdown_r", pd.Series(np.inf, index=work.index)), errors="coerce").fillna(np.inf)
    idx = work.sort_values(["profile_id", "_bs", "_dd", "model_id"], ascending=[True, False, True, True]).groupby("profile_id", sort=False).head(1).index
    cols = ["profile_id", "model_id", "target_id", "filter_id", "n_trades", "pf", "bs_p05", "mean_pnl_r", "max_drawdown_r"]
    available = [col for col in cols if col in work.columns]
    out = work.loc[idx, available].copy()
    return out.rename(columns={col: f"{prefix}_{col}" for col in available if col != "profile_id"})


def _fixed_val_eval_for_selected(summary: pd.DataFrame, selected: pd.DataFrame, prefix: str) -> pd.DataFrame:
    val_eval = summary.loc[summary["split"].astype(str).eq("val_eval")].copy()
    rows = []
    for _, selected_row in selected.iterrows():
        mask = val_eval["profile_id"].eq(selected_row["profile_id"])
        for key in ("model_id", "target_id", "filter_id"):
            selected_key = f"{prefix}_{key}"
            if key in val_eval and selected_key in selected_row:
                mask &= val_eval[key].eq(selected_row[selected_key])
        fixed = val_eval.loc[mask]
        if fixed.empty:
            continue
        eval_row = fixed.iloc[0].to_dict()
        rows.append(
            {
                "profile_id": selected_row["profile_id"],
                f"{prefix}_eval_n_trades": eval_row.get("n_trades"),
                f"{prefix}_eval_pf": eval_row.get("pf"),
                f"{prefix}_eval_bs_p05": eval_row.get("bs_p05"),
                f"{prefix}_eval_mean_pnl_r": eval_row.get("mean_pnl_r"),
                f"{prefix}_eval_max_drawdown_r": eval_row.get("max_drawdown_r"),
            }
        )
    return selected.merge(pd.DataFrame(rows), on="profile_id", how="left")


def diagnostic_best_val_eval_by_profile(summary: pd.DataFrame, prefix: str) -> pd.DataFrame:
    work = summary.loc[summary["split"].astype(str).eq("val_eval")].copy()
    if "eligible_for_winner" in work:
        work = work.loc[work["eligible_for_winner"].astype(bool)]
    if work.empty:
        return pd.DataFrame(columns=["profile_id"])
    idx = work.groupby("profile_id")["bs_p05"].idxmax()
    cols = ["profile_id", "model_id", "target_id", "filter_id", "n_trades", "pf", "bs_p05", "mean_pnl_r", "max_drawdown_r"]
    available = [col for col in cols if col in work.columns]
    out = work.loc[idx, available].copy()
    return out.rename(columns={col: f"{prefix}_{col}" for col in available if col != "profile_id"})


def compare_rich_runs_protocol(old_summary: pd.DataFrame, new_summary: pd.DataFrame) -> pd.DataFrame:
    old_selected = _fixed_val_eval_for_selected(old_summary, _selected_val_select_by_profile(old_summary, "old"), "old")
    new_selected = _fixed_val_eval_for_selected(new_summary, _selected_val_select_by_profile(new_summary, "new"), "new")
    comparison = old_selected.merge(new_selected, on="profile_id", how="outer")
    if {"old_eval_bs_p05", "new_eval_bs_p05"}.issubset(comparison.columns):
        comparison["delta_eval_bs_p05"] = comparison["new_eval_bs_p05"] - comparison["old_eval_bs_p05"]
    if {"old_eval_pf", "new_eval_pf"}.issubset(comparison.columns):
        comparison["delta_eval_pf"] = comparison["new_eval_pf"] - comparison["old_eval_pf"]
    comparison["comparison_kind"] = "selected_on_val_select_then_fixed_val_eval"
    return comparison.sort_values("new_eval_bs_p05", ascending=False, na_position="last")
```

- [ ] **Step 3: Write comparison after normalized run**

After saving new summary:

```python
if args.normalized_rich_features:
    old_summary_path = _path("ML/reports/fractal0_rich_entry_quality_summary.csv")
    if old_summary_path.exists():
        old_summary = pd.read_csv(old_summary_path, sep=";")
        protocol = compare_rich_runs_protocol(old_summary, summary)
        protocol.to_csv(prefix.with_name(prefix.name + "_protocol_comparison.csv"), sep=";", index=False)
        diagnostic_old = diagnostic_best_val_eval_by_profile(old_summary, "old")
        diagnostic_new = diagnostic_best_val_eval_by_profile(summary, "new")
        diagnostic = diagnostic_old.merge(diagnostic_new, on="profile_id", how="outer")
        diagnostic["comparison_kind"] = "diagnostic_best_val_eval_not_eligible_for_selection"
        diagnostic.to_csv(prefix.with_name(prefix.name + "_diagnostic_best_val_eval_by_profile.csv"), sep=";", index=False)
```

- [ ] **Step 4: Run focused test**

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_entry_quality_filter.py::test_compare_rich_runs_protocol_uses_val_select_then_fixed_val_eval -q
```

Expected: `1 passed`.

- [ ] **Step 5: Commit**

If the user explicitly approved commits for execution, run:

```bash
git add ML/baseline/benchmark_fractal0_entry_quality_filter.py tests/test_fractal0_entry_quality_filter.py
git commit -m "Add rich run comparison artifact"
```

If commit approval was not explicit in the execution turn, leave the changes uncommitted and continue.

---

### Task 6: Smoke Run Normalized Mode

**Files:**
- Read/write temporary artifacts under `/tmp`
- No report updates yet

**Interfaces:**
- Consumes `--normalized-rich-features`.
- Produces smoke JSON under `/tmp/fractal0_rich_entry_quality_normalized_smoke.json`.

- [ ] **Step 1: Run focused tests before smoke**

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_entry_quality_filter.py tests/test_fractal0_entry_exit_grid.py -q
```

Expected: all tests pass.

- [ ] **Step 2: Run smoke**

Run:

```bash
PYTHONUNBUFFERED=1 ./.venv/bin/python ML/baseline/benchmark_fractal0_entry_quality_filter.py \
  --rich-entry-quality \
  --normalized-rich-features \
  --threads 2 \
  --no-resume \
  --output-prefix /tmp/fractal0_rich_entry_quality_normalized_smoke \
  --execution-ohlc-path MT/MQL4/Files/XAUUSD_M5_OHLC.csv \
  --stop-policy-id S2_fractal0_buffer_0_5_entry_floor_2 \
  --smoke-limit-filters 1 \
  --permutation-repeats 3
```

Expected:

```text
preflight PASS
finished fractal0_rich_entry_quality
```

- [ ] **Step 3: Verify smoke artifact contract**

Run:

```bash
./.venv/bin/python - <<'PY'
import json
from pathlib import Path
import pandas as pd

base = Path("/tmp/fractal0_rich_entry_quality_normalized_smoke")
d = json.loads(base.with_suffix(".json").read_text())
assert d["locked_test"] == "not_opened"
assert d["feature_contract_variant"] == "normalized_atr_unit"
assert d["normalization_config"]["fit_split"] == "train_core"
assert d["permutation_null_repeats_executed_for_full_selection"] == 0
audit = pd.read_csv(Path(str(base) + "_normalized_feature_distribution_audit.csv"), sep=";")
assert float(audit["below_zero_rate"].max()) == 0.0
assert float(audit["above_one_rate"].max()) == 0.0
assert {"p1", "p5", "p25", "p75", "p95", "p99", "mean", "std", "zero_rate", "flag"}.issubset(audit.columns)
token = pd.read_csv(Path(str(base) + "_token_coverage.csv"), sep=";")
assert {"padding_rate", "truncation_rate", "anchor_for_coordinate", "anchor_for_selection", "flag"}.issubset(token.columns)
updn = pd.read_csv(Path(str(base) + "_updn_provenance_gate.csv"), sep=";")
assert set(updn["status"]) == {"PASS"}
forbidden = pd.read_csv(Path(str(base) + "_forbidden_column_audit.csv"), sep=";")
assert int(forbidden["forbidden"].sum()) == 0
print("normalized smoke contract PASS")
PY
```

Expected:

```text
normalized smoke contract PASS
```

- [ ] **Step 4: Commit if smoke required code fixes**

If Task 6 required code changes and the user explicitly approved commits for execution, run:

```bash
git add ML/baseline/benchmark_fractal0_entry_quality_filter.py tests/test_fractal0_entry_quality_filter.py
git commit -m "Fix normalized rich smoke contract"
```

If no code changes were needed, do not create an empty commit. If commit approval was not explicit in the execution turn, leave any fixes uncommitted and continue.

---

### Task 7: Full Normalized Rerun

**Files:**
- Create: `ML/reports/fractal0_rich_entry_quality_normalized*.json/csv`

**Interfaces:**
- Consumes all previous tasks.
- Produces full normalized artifact set.

- [ ] **Step 1: Start full run**

Run:

```bash
PYTHONUNBUFFERED=1 ./.venv/bin/python ML/baseline/benchmark_fractal0_entry_quality_filter.py \
  --rich-entry-quality \
  --normalized-rich-features \
  --threads 24 \
  --no-resume \
  --output-prefix ML/reports/fractal0_rich_entry_quality_normalized \
  --execution-ohlc-path MT/MQL4/Files/XAUUSD_M5_OHLC.csv \
  --stop-policy-id S2_fractal0_buffer_0_5_entry_floor_2 \
  --permutation-repeats 200
```

Expected:

```text
preflight PASS
finished fractal0_rich_entry_quality
```

- [ ] **Step 2: Verify full artifact contract**

Run:

```bash
./.venv/bin/python - <<'PY'
import json
from pathlib import Path
import pandas as pd
import ML.baseline.benchmark_fractal0_entry_quality_filter as runner

base = Path("ML/reports/fractal0_rich_entry_quality_normalized")
d = json.loads(base.with_suffix(".json").read_text())
assert d["status"] == "completed"
assert d["locked_test"] == "not_opened"
assert d["allowed_max_verdict"] == "RESEARCH_HINT_RICH_FEATURES"
assert d["feature_contract_variant"] == "normalized_atr_unit"
assert d["normalization_config"]["fit_split"] == "train_core"
assert d["ranked_search_budget"]["n_total_ranked_configs"] == 243
assert d["permutation_null_repeats_executed_for_full_selection"] == 0
audit = pd.read_csv(Path(str(base) + "_normalized_feature_distribution_audit.csv"), sep=";")
assert float(audit["below_zero_rate"].max()) == 0.0
assert float(audit["above_one_rate"].max()) == 0.0
protocol = pd.read_csv(Path(str(base) + "_protocol_comparison.csv"), sep=";")
assert len(protocol) > 0
assert set(protocol["comparison_kind"]) == {"selected_on_val_select_then_fixed_val_eval"}
diagnostic = pd.read_csv(Path(str(base) + "_diagnostic_best_val_eval_by_profile.csv"), sep=";")
assert len(diagnostic) > 0
assert set(diagnostic["comparison_kind"]) == {"diagnostic_best_val_eval_not_eligible_for_selection"}
token = pd.read_csv(Path(str(base) + "_token_coverage.csv"), sep=";")
assert {"padding_rate", "truncation_rate", "anchor_for_coordinate", "anchor_for_selection", "flag"}.issubset(token.columns)
updn = pd.read_csv(Path(str(base) + "_updn_provenance_gate.csv"), sep=";")
assert set(updn["status"]) == {"PASS"}
print("normalized full artifact contract PASS")
PY
```

Expected:

```text
normalized full artifact contract PASS
```

- [ ] **Step 3: Capture main numbers**

Run:

```bash
./.venv/bin/python - <<'PY'
import json
from pathlib import Path
import pandas as pd
import ML.baseline.benchmark_fractal0_entry_quality_filter as runner

base = Path("ML/reports/fractal0_rich_entry_quality_normalized")
d = json.loads(base.with_suffix(".json").read_text())
for name in ["selected_winner", "selected_winner_val_eval", "diagnostic_best_val_eval"]:
    print("\n" + name)
    row = d.get(name, {})
    for key in ["profile_id", "model_id", "target_id", "filter_id", "split", "n_trades", "pf", "bs_p05", "mean_pnl_r", "max_drawdown_r", "selected_fraction", "sl_rate"]:
        print(key, row.get(key))
protocol = pd.read_csv(Path(str(base) + "_protocol_comparison.csv"), sep=";")
diagnostic = pd.read_csv(Path(str(base) + "_diagnostic_best_val_eval_by_profile.csv"), sep=";")
print("\nprotocol comparison")
print(protocol.head(20).to_string(index=False))
print("\ndiagnostic best val_eval by profile")
print(diagnostic.head(20).to_string(index=False))
PY
```

Expected: printed winner, fixed `val_eval`, diagnostic best, and top comparison rows.

- [ ] **Step 4: Do not interpret yet**

Do not update report from memory. Use the captured JSON/CSV values only.

---

### Task 8: Write Normalized Rerun Report

**Files:**
- Create: `docs/reports/2026-07-22-fractal0-rich-entry-quality-normalized-rerun.md`
- Modify: `docs/reports/2026-07-21-fractal0-rich-entry-quality.md`
- Modify: `docs/ML/benchmark_fractal0_entry_quality_filter.py.md`

**Interfaces:**
- Consumes normalized artifacts from Task 7.
- Produces final human-readable report.

- [ ] **Step 1: Create report skeleton**

Create `docs/reports/2026-07-22-fractal0-rich-entry-quality-normalized-rerun.md` with:

```markdown
# Fractal0 Rich Entry Quality Normalized Rerun

> **Дата**: 2026-07-22
> **Статус**: Completed
> **Вердикт**: RESEARCH_HINT_RICH_FEATURES
> **Цель**: Проверить, меняется ли rich-entry result после исправления feature contract: price-like признаки переводятся в ATR-координаты и final model inputs ограничены диапазоном `0..1`.
> **Previous report**: `docs/reports/2026-07-21-fractal0-rich-entry-quality.md`

## Context

Previous corrected rich run selected `time_only / linear / target_entry_ev_regression / top30`, but rich/fractal profiles used a weaker scale contract: some price-like fields were raw or price-point differences, and model input used simple `fillna(0.0)`.

This rerun keeps the same search grid and split roles, but changes the feature contract.

## Feature Contract Correction

Normalized mode applies this contract:

- price-like model inputs are converted to ATR coordinates before dataset-level scaling;
- final model inputs are finite and bounded to `0..1`;
- scaler bounds are fitted on `train_core` only;
- missing indicators are fixed schema columns, not split-dependent columns;
- padded fractal token fields stay `0.0` and are excluded from scaler fit by `fractalN_present`;
- `selection_basis=nearest_to_planned_limit` means entry-nearest selection, while `anchor_for_coordinate=fractal0_price` remains the coordinate anchor;
- `fractal0_up_*` and `fractal0_dn_*` are accepted only from serialized `fractal*` snapshots, with `updn_provenance_gate=PASS`.

Artifact paths:

- JSON: `ML/reports/fractal0_rich_entry_quality_normalized.json`
- Summary: `ML/reports/fractal0_rich_entry_quality_normalized_summary.csv`
- Feature contract: `ML/reports/fractal0_rich_entry_quality_normalized_feature_contract.csv`
- Final matrix audit: `ML/reports/fractal0_rich_entry_quality_normalized_normalized_feature_distribution_audit.csv`
- Token coverage: `ML/reports/fractal0_rich_entry_quality_normalized_token_coverage.csv`
- Protocol comparison: `ML/reports/fractal0_rich_entry_quality_normalized_protocol_comparison.csv`
- Diagnostic best-by-profile: `ML/reports/fractal0_rich_entry_quality_normalized_diagnostic_best_val_eval_by_profile.csv`
```

- [ ] **Step 2: Add mandatory tables**

Include these sections using exact values from artifacts:

```markdown
## Normalized Winner

## Old vs Normalized Winner

## Best By Profile Comparison

Use `*_protocol_comparison.csv` as the primary table. Use `*_diagnostic_best_val_eval_by_profile.csv` only in a clearly labelled diagnostic subsection.

## Feature Contract Gates

Include:

- raw price-like guard result;
- schema consistency result for `train_core`, `val_select`, `val_eval`;
- missing indicator policy;
- padding/mask result;
- `Up/Dn` provenance result;
- scale contract verdict: `PASS`, `FAIL`, or `DIAGNOSTIC_ONLY`.

## Normalized Feature Distribution

Summarize A7 artifact flags: number of `PASS`, `WARNING`, and `ERROR` rows. For every `WARNING` or `ERROR`, state the decision: block, fix, rerun, or accept-as-warning.

## Token Coverage And Diagnostic Controls

Report token coverage by profile and the diagnostic-only controls `atr_only`, `time_plus_atr`, and `planned_geometry_no_atr`.

## Yearly And Side Disclosure

## Multiple Testing And Search Budget

## Conclusions

## Next Step
```

- [ ] **Step 3: Required conclusion logic**

Use one of these conclusion branches:

```text
If normalized winner remains time_only:
  Conclude that strict feature scaling did not make rich/fractal profiles beat the formal time_only winner.

If normalized winner becomes rich/fractal:
  Conclude that old rich/fractal comparison was materially limited by feature preparation. Still no candidate; next step is a pre-registered probe of the new rule.

If normalized metrics broadly degrade:
  Conclude that raw price-like fields may have been carrying price-regime/calendar information rather than stable market structure.
```

- [ ] **Step 4: Add backlink to old report**

In `docs/reports/2026-07-21-fractal0-rich-entry-quality.md`, add near the top:

```markdown
> **Follow-up**: `docs/reports/2026-07-22-fractal0-rich-entry-quality-normalized-rerun.md` reruns the same rich search with price-like inputs converted to ATR/unit features. Use that report for the final comparison of rich/fractal profiles under the corrected feature contract.
```

- [ ] **Step 5: Update module docs**

In `docs/ML/benchmark_fractal0_entry_quality_filter.py.md`, add:

```markdown
### Normalized Rich Entry Quality Mode

Use `--rich-entry-quality --normalized-rich-features` to run the same rich grid with corrected feature contract:

- price-like inputs are converted to ATR coordinates;
- final model inputs are scaled to `0..1` using train-only bounds;
- raw absolute prices are blocked from normalized model input;
- output prefix: `ML/reports/fractal0_rich_entry_quality_normalized`.
```

- [ ] **Step 6: Commit report/docs after verification in Task 10**

Do not commit yet. Documentation must be synchronized after Task 9 and Task 10.

---

### Task 9: Sync Changelog, Handoff, Wiki

**Files:**
- Modify: `CHANGELOG.md`
- Modify: `CONTEXT_HANDOFF.md`
- Modify: `wiki/research/fractal-stop-research.md`
- Modify: `wiki/index.md`
- Modify: `wiki/log.md`

**Interfaces:**
- Consumes report from Task 8.
- Produces project-level memory.

- [ ] **Step 1: Add changelog entry**

Add a new top entry to `CHANGELOG.md`:

```markdown
## [2026-07-22] — Fractal0 Rich Entry Quality Normalized Rerun (RESEARCH_HINT_RICH_FEATURES)
- **report**: `docs/reports/2026-07-22-fractal0-rich-entry-quality-normalized-rerun.md`
- **topics**: `fractal0`, `rich_entry_quality`, `feature_contract`, `normalization`, `research_hint`
- **summary**: Re-ran rich-entry search with price-like features converted to ATR coordinates and final model inputs scaled to `0..1` from train-only bounds.
- **decision**: Record the normalized selected winner, fixed `val_eval` `PF`/`BS_p05`/`n_trades`, and one of the three predefined comparison outcomes: `time_only_still_wins`, `normalized_rich_or_fractal_wins`, or `normalized_results_degrade`.
- **notes**: `locked_test=not_opened`; full-selection permutation not run unless explicitly implemented; old rich artifacts preserved for comparison.
```

Replace bracketed text with actual artifact values before saving.

- [ ] **Step 2: Update handoff**

In `CONTEXT_HANDOFF.md`, add:

```markdown
## Normalized rich-entry follow-up

- report: `docs/reports/2026-07-22-fractal0-rich-entry-quality-normalized-rerun.md`
- artifacts prefix: `ML/reports/fractal0_rich_entry_quality_normalized`
- feature contract: price-like -> ATR coordinate -> train-only unit scaling to `0..1`
- result: copy `selected_winner` and `selected_winner_val_eval` from `ML/reports/fractal0_rich_entry_quality_normalized.json`
- interpretation: use exactly one branch from the report section `Conclusions`
- next step: pre-registered replication/probe only; not freeze, not `locked_test`.
```

- [ ] **Step 3: Update wiki research page**

Append one concise numbered result to `wiki/research/fractal-stop-research.md`. Include:

- normalized winner;
- old winner;
- whether rich/fractal profiles improved after corrected contract;
- `locked_test=not_opened`;
- no candidate claim.

- [ ] **Step 4: Update wiki index/log**

Update `wiki/index.md` summary for `fractal-stop-research.md`.

Add to `wiki/log.md`:

```markdown
### 2026-07-22: Fractal0 rich entry-quality normalized rerun
- Added normalized rich feature contract and reran rich-entry search under `ML/reports/fractal0_rich_entry_quality_normalized`.
- Updated report/changelog/handoff/wiki with old-vs-normalized comparison.
```

---

### Task 10: Final Verification

**Files:**
- All touched files

**Interfaces:**
- Consumes all previous tasks.
- Produces verified final state.

- [ ] **Step 1: Run focused tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_entry_quality_filter.py tests/test_fractal0_entry_exit_grid.py -q
```

Expected: all tests pass.

- [ ] **Step 2: Run full tests**

Run:

```bash
./.venv/bin/python -m pytest tests/ -q
```

Expected: all tests pass.

- [ ] **Step 3: Verify normalized artifacts**

Run:

```bash
./.venv/bin/python - <<'PY'
import json
from pathlib import Path
import pandas as pd
import ML.baseline.benchmark_fractal0_entry_quality_filter as runner

base = Path("ML/reports/fractal0_rich_entry_quality_normalized")
d = json.loads(base.with_suffix(".json").read_text())
assert d["status"] == "completed"
assert d["locked_test"] == "not_opened"
assert d["feature_contract_variant"] == "normalized_atr_unit"
assert d["normalization_config"]["fit_split"] == "train_core"
assert d["allowed_max_verdict"] == "RESEARCH_HINT_RICH_FEATURES"
audit = pd.read_csv(Path(str(base) + "_normalized_feature_distribution_audit.csv"), sep=";")
assert float(audit["below_zero_rate"].max()) == 0.0
assert float(audit["above_one_rate"].max()) == 0.0
assert {"p1", "p5", "p25", "p75", "p95", "p99", "mean", "std", "zero_rate", "flag"}.issubset(audit.columns)
contract = pd.read_csv(Path(str(base) + "_feature_contract.csv"), sep=";")
runner.assert_no_raw_price_like_features(contract["feature"].astype(str).tolist())
protocol = pd.read_csv(Path(str(base) + "_protocol_comparison.csv"), sep=";")
assert len(protocol) > 0
assert set(protocol["comparison_kind"]) == {"selected_on_val_select_then_fixed_val_eval"}
diagnostic = pd.read_csv(Path(str(base) + "_diagnostic_best_val_eval_by_profile.csv"), sep=";")
assert len(diagnostic) > 0
token = pd.read_csv(Path(str(base) + "_token_coverage.csv"), sep=";")
assert {"padding_rate", "truncation_rate", "anchor_for_coordinate", "anchor_for_selection", "flag"}.issubset(token.columns)
updn = pd.read_csv(Path(str(base) + "_updn_provenance_gate.csv"), sep=";")
assert set(updn["status"]) == {"PASS"}
auto_check = {
    "status": "PASS",
    "checked_paths": [
        str(base.with_suffix(".json")),
        str(Path(str(base) + "_feature_contract.csv")),
        str(Path(str(base) + "_normalized_feature_distribution_audit.csv")),
        str(Path(str(base) + "_token_coverage.csv")),
        str(Path(str(base) + "_protocol_comparison.csv")),
        str(Path(str(base) + "_diagnostic_best_val_eval_by_profile.csv")),
        str(Path(str(base) + "_updn_provenance_gate.csv")),
    ],
    "locked_test": d["locked_test"],
    "feature_contract_variant": d["feature_contract_variant"],
    "scale_contract": "PASS",
}
for path in auto_check["checked_paths"]:
    assert Path(path).exists(), path
Path(str(base) + "_artifact_auto_check.json").write_text(json.dumps(auto_check, ensure_ascii=True, indent=2), encoding="utf-8")
print("final normalized artifact verification PASS")
PY
```

Expected:

```text
final normalized artifact verification PASS
```

- [ ] **Step 4: Generate and check wiki**

Run:

```bash
./.venv/bin/python wiki/wiki.py generate
./.venv/bin/python wiki/wiki.py status
```

Expected:

```text
Wiki is up to date. No gaps found.
```

- [ ] **Step 5: Commit final docs/artifacts**

Run this step only if the user explicitly approved commits for execution:

```bash
git add \
  ML/baseline/benchmark_fractal0_entry_quality_filter.py \
  tests/test_fractal0_entry_quality_filter.py \
  ML/reports/fractal0_rich_entry_quality_normalized.json \
  ML/reports/fractal0_rich_entry_quality_normalized_summary.csv \
  ML/reports/fractal0_rich_entry_quality_normalized_scores.csv \
  ML/reports/fractal0_rich_entry_quality_normalized_trades.csv \
  ML/reports/fractal0_rich_entry_quality_normalized_feature_contract.csv \
  ML/reports/fractal0_rich_entry_quality_normalized_feature_distribution_audit.csv \
  ML/reports/fractal0_rich_entry_quality_normalized_normalized_feature_distribution_audit.csv \
  ML/reports/fractal0_rich_entry_quality_normalized_token_coverage.csv \
  ML/reports/fractal0_rich_entry_quality_normalized_normalization_config.json \
  ML/reports/fractal0_rich_entry_quality_normalized_forbidden_column_audit.csv \
  ML/reports/fractal0_rich_entry_quality_normalized_protocol_comparison.csv \
  ML/reports/fractal0_rich_entry_quality_normalized_diagnostic_best_val_eval_by_profile.csv \
  ML/reports/fractal0_rich_entry_quality_normalized_updn_provenance_gate.csv \
  ML/reports/fractal0_rich_entry_quality_normalized_artifact_auto_check.json \
  docs/reports/2026-07-21-fractal0-rich-entry-quality.md \
  docs/reports/2026-07-22-fractal0-rich-entry-quality-normalized-rerun.md \
  docs/ML/benchmark_fractal0_entry_quality_filter.py.md \
  CHANGELOG.md \
  CONTEXT_HANDOFF.md \
  wiki/REPO_integrity.md \
  wiki/index.md \
  wiki/log.md \
  wiki/research/fractal-stop-research.md
git commit -m "Add normalized fractal0 rich entry quality rerun"
```

If commit approval was not explicit in the execution turn, leave the final changes uncommitted. Do not add `docs/superpowers/audit.md` unless the user explicitly asks.

---

## Expected Interpretation Rules

Use these rules in the final report. Do not improvise after seeing numbers.

### Case A: Normalized winner remains `time_only`

Conclusion:

```text
Correcting the feature contract did not make rich/fractal profiles beat the formal time_only winner. The current branch supports entry-quality filtering mostly as a calendar/time hypothesis, not as proven fractal structure.
```

Allowed next step:

```text
Pre-registered replication/probe of time_only rule or close the branch.
```

### Case B: Normalized winner becomes rich/fractal

Conclusion:

```text
The previous rich/fractal comparison was materially limited by feature preparation. The normalized rich/fractal rule is a new research hint and requires its own pre-registered replication/probe.
```

Allowed next step:

```text
Pre-registered replication/probe of exactly the normalized rule; no locked_test yet.
```

### Case C: All normalized results degrade

Conclusion:

```text
Raw price-like features likely carried price-regime/calendar information or helped specific models through unstable scale effects. The normalized contract weakens that signal.
```

Allowed next step:

```text
Prefer time_only replication or pivot away from this rich/fractal entry-quality branch.
```

---

## Self-Review Checklist

- [ ] Plan uses a new artifact prefix and does not overwrite old rich artifacts.
- [ ] Plan creates a new report rather than rewriting the old report.
- [ ] Raw price-like features are explicitly banned in normalized input.
- [ ] ATR conversion happens before `0..1` scaling.
- [ ] Unit scaler fit uses only `train_core`.
- [ ] Validation splits never affect scaler bounds.
- [ ] Final normalized model inputs are checked for finite `[0,1]` range.
- [ ] Missing values are not silently treated as real zeros.
- [ ] Comparison artifact explicitly compares old and normalized runs.
- [ ] `locked_test` remains closed.
- [ ] Maximum verdict remains `RESEARCH_HINT_RICH_FEATURES`.
- [ ] Final report has predetermined interpretation branches.
