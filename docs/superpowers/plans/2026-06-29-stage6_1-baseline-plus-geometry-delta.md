# Stage 6.1 Baseline Plus Geometry Delta Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Test whether the three strongest Stage 6.1 geometry profiles add incremental value on top of `h12_clock_shift_back`.

**Architecture:** Extend the existing Stage 6.1 runner with three fixed combined profiles. Each combined profile concatenates `clock_shift_back` features with one predeclared geometry feature matrix, reuses the existing evaluator/gate mechanics, and reports a dedicated baseline-plus-geometry delta section.

**Tech Stack:** Python 3.10+, pandas, numpy, xgboost, pytest, existing `./.venv/bin/python`, existing Stage 6.1 JSON/report paths.

## Global Constraints

- Work on the current branch; do not use git worktree.
- Use `./.venv/bin/python` for all Python commands.
- Use TDD for deterministic runner/profile logic.
- Do not change H12 horizon, TP/SL formula, target, split policy, or holdout policy.
- Add exactly three combined profiles:
  - `h12_clock_shift_back_plus_nearest_time40_geometry`
  - `h12_clock_shift_back_plus_corridor3_geometry`
  - `h12_clock_shift_back_plus_corridor10_geometry`
- Do not add `nearest_price40` or `zones10` combined profiles.
- Keep Stage 6.1 `DIAGNOSTIC_ONLY`.
- Runtime contract remains required: `xgb_n_jobs=24`, heartbeat, checkpoint before preflight, checkpoint after every run, `--resume` / `--no-resume`, top-level and per-run `elapsed_sec`.
- After Python changes run `./.venv/bin/python -m pytest tests/ -q`.

---

## File Structure

**Modify**

- `ML/baseline/benchmark_stage6_1_relative_geometry.py`
  - Add combined profile keys to `Stage61Config.profile_keys`.
  - Add profile mapping from combined profile to geometry source profile.
  - Add combined feature builder by concatenating baseline and geometry matrices.
  - Add delta summary against `h12_clock_shift_back`.

- `tests/test_stage6_1_relative_geometry.py`
  - Add tests for fixed combined profile list.
  - Add tests for combined feature shape and target denylist.
  - Add tests for baseline delta summary.

- `docs/reports/2026-06-29-stage6_1-h12-relative-fractal-geometry.md`
  - Add `Baseline + Geometry Delta Test` section after the existing geometry-only results.

- `CHANGELOG.md`, `CONTEXT_HANDOFF.md`, `wiki/research/fractal-stop-research.md`, `wiki/index.md`, `wiki/log.md`, `wiki/REPO_integrity.md`
  - Update after the full rerun.

**Generated**

- `ML/reports/stage6_1_h12_relative_fractal_geometry.json`

---

## Task 1: Combined Profile Contract

**Files:**
- Modify: `tests/test_stage6_1_relative_geometry.py`
- Modify: `ML/baseline/benchmark_stage6_1_relative_geometry.py`

**Interfaces:**
- Produces:
  - `STAGE6_1_COMBINED_PROFILE_TO_GEOMETRY: dict[str, str]`
  - `stage61_combined_profile_keys() -> tuple[str, ...]`

- [ ] **Step 1: Write failing contract tests**

Append to `tests/test_stage6_1_relative_geometry.py`:

```python
def test_stage61_combined_profiles_are_fixed_to_top_three_geometry_profiles():
    assert s61.stage61_combined_profile_keys() == (
        "h12_clock_shift_back_plus_nearest_time40_geometry",
        "h12_clock_shift_back_plus_corridor3_geometry",
        "h12_clock_shift_back_plus_corridor10_geometry",
    )
    assert s61.STAGE6_1_COMBINED_PROFILE_TO_GEOMETRY == {
        "h12_clock_shift_back_plus_nearest_time40_geometry": "h12_nearest_time40_relative_geometry",
        "h12_clock_shift_back_plus_corridor3_geometry": "h12_corridor3_relative_geometry",
        "h12_clock_shift_back_plus_corridor10_geometry": "h12_corridor10_relative_geometry",
    }


def test_stage61_profile_keys_include_baseline_geometry_and_combined_profiles():
    keys = s61.stage61_profile_keys()

    assert keys[-3:] == s61.stage61_combined_profile_keys()
    assert "h12_clock_shift_back_plus_nearest_time40_geometry" in keys
    assert "h12_clock_shift_back_plus_corridor3_geometry" in keys
    assert "h12_clock_shift_back_plus_corridor10_geometry" in keys
    assert "h12_clock_shift_back_plus_nearest_price40_geometry" not in keys
    assert "h12_clock_shift_back_plus_zones10_geometry" not in keys
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage6_1_relative_geometry.py -q
```

Expected: FAIL because `stage61_combined_profile_keys` and `STAGE6_1_COMBINED_PROFILE_TO_GEOMETRY` do not exist.

- [ ] **Step 3: Implement combined profile constants**

In `ML/baseline/benchmark_stage6_1_relative_geometry.py`, add after `STAGE6_1_JSON_REPORT_PATH`:

```python
STAGE6_1_COMBINED_PROFILE_TO_GEOMETRY = {
    "h12_clock_shift_back_plus_nearest_time40_geometry": "h12_nearest_time40_relative_geometry",
    "h12_clock_shift_back_plus_corridor3_geometry": "h12_corridor3_relative_geometry",
    "h12_clock_shift_back_plus_corridor10_geometry": "h12_corridor10_relative_geometry",
}
```

Extend `Stage61Config.profile_keys` by appending:

```python
"h12_clock_shift_back_plus_nearest_time40_geometry",
"h12_clock_shift_back_plus_corridor3_geometry",
"h12_clock_shift_back_plus_corridor10_geometry",
```

Add:

```python
def stage61_combined_profile_keys() -> tuple[str, ...]:
    return tuple(STAGE6_1_COMBINED_PROFILE_TO_GEOMETRY.keys())
```

- [ ] **Step 4: Run focused tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage6_1_relative_geometry.py -q
```

Expected: PASS for the new contract tests.

---

## Task 2: Combined Feature Builder

**Files:**
- Modify: `tests/test_stage6_1_relative_geometry.py`
- Modify: `ML/baseline/benchmark_stage6_1_relative_geometry.py`

**Interfaces:**
- Consumes:
  - `STAGE6_1_COMBINED_PROFILE_TO_GEOMETRY`
  - `stage61_build_features(df: pd.DataFrame, profile: str) -> np.ndarray`
- Produces:
  - `stage61_build_combined_features(df: pd.DataFrame, profile: str) -> np.ndarray`

- [ ] **Step 1: Write failing combined feature tests**

Append to `tests/test_stage6_1_relative_geometry.py`:

```python
def test_stage61_combined_features_concat_baseline_and_geometry(monkeypatch):
    df = pd.DataFrame({
        "time": ["2025.01.01 00:00", "2025.01.01 01:00"],
        "stage6_pnl_r": [1.0, -1.0],
        "stage6_definitive_tp_vs_sl_flag": [1.0, 0.0],
        "dummy": [0.1, 0.2],
    })
    captured = {}

    def fake_baseline_builder(clean_df, profile):
        captured["baseline_columns"] = tuple(clean_df.columns)
        assert profile == "clock_shift_back"
        return np.asarray([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)

    def fake_geometry_builder(clean_df, profile):
        captured["geometry_columns"] = tuple(clean_df.columns)
        assert profile == "h12_corridor3_relative_geometry"
        return np.asarray([[5.0, 6.0, 7.0], [8.0, 9.0, 10.0]], dtype=np.float32)

    monkeypatch.setattr(s61, "build_stage5_4_features", fake_baseline_builder)
    monkeypatch.setattr(s61, "stage61_build_geometry_features", fake_geometry_builder)

    X = s61.stage61_build_features(df, "h12_clock_shift_back_plus_corridor3_geometry")

    assert X.dtype == np.float32
    assert X.shape == (2, 5)
    assert X.tolist() == [[1.0, 2.0, 5.0, 6.0, 7.0], [3.0, 4.0, 8.0, 9.0, 10.0]]
    assert "stage6_pnl_r" not in captured["baseline_columns"]
    assert "stage6_definitive_tp_vs_sl_flag" not in captured["geometry_columns"]
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage6_1_relative_geometry.py::test_stage61_combined_features_concat_baseline_and_geometry -q
```

Expected: FAIL because combined profiles are not implemented in `stage61_build_features`.

- [ ] **Step 3: Implement combined feature builder**

Add to `ML/baseline/benchmark_stage6_1_relative_geometry.py` before `stage61_build_features`:

```python
def stage61_build_combined_features(df: pd.DataFrame, profile: str) -> np.ndarray:
    geometry_profile = STAGE6_1_COMBINED_PROFILE_TO_GEOMETRY[profile]
    clean = df.drop(columns=[c for c in stage61_feature_denylist() if c in df.columns])
    baseline = build_stage5_4_features(clean, "clock_shift_back")
    geometry = stage61_build_geometry_features(clean, geometry_profile)
    if len(baseline) != len(geometry):
        raise ValueError(
            f"combined feature row mismatch for {profile}: baseline={len(baseline)} geometry={len(geometry)}"
        )
    return np.concatenate([baseline.astype(np.float32), geometry.astype(np.float32)], axis=1)
```

Update `stage61_build_features`:

```python
    if profile in STAGE6_1_COMBINED_PROFILE_TO_GEOMETRY:
        return stage61_build_combined_features(clean, profile)
```

Place this branch before the final `raise ValueError`.

- [ ] **Step 4: Run focused tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage6_1_relative_geometry.py -q
```

Expected: all focused tests pass.

---

## Task 3: Baseline Delta Summary

**Files:**
- Modify: `tests/test_stage6_1_relative_geometry.py`
- Modify: `ML/baseline/benchmark_stage6_1_relative_geometry.py`

**Interfaces:**
- Consumes:
  - `report["summary"]`
  - `stage61_combined_profile_keys()`
- Produces:
  - `stage61_baseline_delta_summary(report: dict) -> dict`
  - `report["baseline_plus_geometry_delta"]`

- [ ] **Step 1: Write failing delta summary test**

Append to `tests/test_stage6_1_relative_geometry.py`:

```python
def test_stage61_baseline_delta_summary_uses_val_stop_only():
    report = {
        "summary": {
            "h12_clock_shift_back": {
                "val_stop": {"auc_median": 0.61, "pr_auc_lift_median": 0.10},
                "threshold_selection": {
                    "status": "SELECTED",
                    "selected": {"pf": 1.20},
                },
                "permutation_baseline": {"empirical_p_value": 0.20},
            },
            "h12_clock_shift_back_plus_corridor3_geometry": {
                "val_stop": {"auc_median": 0.64, "pr_auc_lift_median": 0.11},
                "threshold_selection": {
                    "status": "SELECTED",
                    "selected": {"pf": 1.25},
                },
                "permutation_baseline": {"empirical_p_value": 0.05},
            },
        }
    }

    delta = s61.stage61_baseline_delta_summary(report)

    row = delta["profiles"]["h12_clock_shift_back_plus_corridor3_geometry"]
    assert row["auc_delta_vs_baseline"] == pytest.approx(0.03)
    assert row["pr_auc_lift_delta_vs_baseline"] == pytest.approx(0.01)
    assert row["pf_delta_vs_baseline"] == pytest.approx(0.05)
    assert row["passes_delta_gate"] is True
    assert delta["best_profile"] == "h12_clock_shift_back_plus_corridor3_geometry"
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage6_1_relative_geometry.py::test_stage61_baseline_delta_summary_uses_val_stop_only -q
```

Expected: FAIL because `stage61_baseline_delta_summary` does not exist.

- [ ] **Step 3: Implement delta summary**

Add to `ML/baseline/benchmark_stage6_1_relative_geometry.py` before `run_stage6_1_relative_geometry`:

```python
def stage61_baseline_delta_summary(report: dict) -> dict:
    summary = report.get("summary", {})
    baseline = summary.get("h12_clock_shift_back", {})
    baseline_val = baseline.get("val_stop", {})
    baseline_threshold = baseline.get("threshold_selection", {})
    baseline_selected = baseline_threshold.get("selected") or {}
    baseline_auc = baseline_val.get("auc_median")
    baseline_pr = baseline_val.get("pr_auc_lift_median")
    baseline_pf = baseline_selected.get("pf")
    rows = {}
    best_profile = None
    best_auc_delta = None
    for profile in stage61_combined_profile_keys():
        item = summary.get(profile, {})
        val = item.get("val_stop", {})
        selected = (item.get("threshold_selection", {}) or {}).get("selected") or {}
        perm = item.get("permutation_baseline") or {}
        auc = val.get("auc_median")
        pr = val.get("pr_auc_lift_median")
        pf = selected.get("pf")
        auc_delta = None if auc is None or baseline_auc is None else float(auc - baseline_auc)
        pr_delta = None if pr is None or baseline_pr is None else float(pr - baseline_pr)
        pf_delta = None if pf is None or baseline_pf is None else float(pf - baseline_pf)
        passes = (
            auc_delta is not None and auc_delta >= 0.02
            and pr_delta is not None and pr_delta >= 0.0
            and item.get("threshold_selection", {}).get("status") == "SELECTED"
            and pf_delta is not None and pf_delta >= 0.0
            and perm.get("empirical_p_value") is not None
            and perm["empirical_p_value"] <= 0.10
        )
        rows[profile] = {
            "auc_delta_vs_baseline": auc_delta,
            "pr_auc_lift_delta_vs_baseline": pr_delta,
            "pf_delta_vs_baseline": pf_delta,
            "permutation_p_value": perm.get("empirical_p_value"),
            "passes_delta_gate": bool(passes),
        }
        if auc_delta is not None and (best_auc_delta is None or auc_delta > best_auc_delta):
            best_profile = profile
            best_auc_delta = auc_delta
    return {
        "baseline_profile": "h12_clock_shift_back",
        "best_profile": best_profile,
        "profiles": rows,
        "delta_gate": {
            "auc_delta_ge_0_02": 0.02,
            "pr_auc_lift_delta_ge_0": 0.0,
            "pf_delta_ge_0": 0.0,
            "permutation_p_value_le_0_10": 0.10,
        },
    }
```

In `run_stage6_1_relative_geometry`, after `report["summary"] = summary`, add:

```python
    report["baseline_plus_geometry_delta"] = stage61_baseline_delta_summary(report)
```

- [ ] **Step 4: Run focused tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage6_1_relative_geometry.py -q
```

Expected: all focused tests pass.

---

## Task 4: Full Rerun And Report Update

**Files:**
- Modify: `ML/reports/stage6_1_h12_relative_fractal_geometry.json`
- Modify: `docs/reports/2026-06-29-stage6_1-h12-relative-fractal-geometry.md`
- Modify: `CHANGELOG.md`
- Modify: `CONTEXT_HANDOFF.md`
- Modify: wiki files

**Interfaces:**
- Consumes:
  - Stage 6.1 CLI
  - `baseline_plus_geometry_delta` JSON section
- Produces:
  - Updated Stage 6.1 JSON/report/handoff/wiki.

- [ ] **Step 1: Run full Stage 6.1 with no resume**

Run:

```bash
./.venv/bin/python ML/baseline/benchmark_stage6_1_relative_geometry.py --stage6-1-relative-geometry --no-resume
```

Expected:

- `done_runs == total_runs == 27`
- existing six profiles plus three combined profiles
- JSON contains `baseline_plus_geometry_delta`
- status remains `MODEL_GATE_FAILED`, `TRADING_GATE_FAILED`, or diagnostic delta status according to gate logic, never `CANDIDATE`

- [ ] **Step 2: Inspect JSON invariants**

Run:

```bash
./.venv/bin/python - <<'PY'
import json
from pathlib import Path
data = json.loads(Path("ML/reports/stage6_1_h12_relative_fractal_geometry.json").read_text())
assert data["done_runs"] == data["total_runs"] == 27
assert len(data["raw_runs"]) == 27
assert data["config"]["xgb_n_jobs"] == 24
assert "baseline_plus_geometry_delta" in data
for profile in (
    "h12_clock_shift_back_plus_nearest_time40_geometry",
    "h12_clock_shift_back_plus_corridor3_geometry",
    "h12_clock_shift_back_plus_corridor10_geometry",
):
    assert profile in data["summary"]
    assert profile in data["baseline_plus_geometry_delta"]["profiles"]
print(data["status"])
print(data["baseline_plus_geometry_delta"])
PY
```

Expected: assertions pass and print status plus delta summary.

- [ ] **Step 3: Update report**

Add a section to `docs/reports/2026-06-29-stage6_1-h12-relative-fractal-geometry.md`:

```markdown
### Baseline + Geometry Delta Test

Purpose: test whether the top three geometry-only profiles add value on top of `h12_clock_shift_back`.

Selection rule: top three geometry-only profiles by Stage 6.1 median `val_stop` AUC:

- `h12_nearest_time40_relative_geometry`
- `h12_corridor3_relative_geometry`
- `h12_corridor10_relative_geometry`

| Profile | Val AUC med | Delta vs baseline | PR lift med | PF med | permutation p-value | Delta gate |
|---------|-------------|-------------------|-------------|--------|---------------------|------------|
| `h12_clock_shift_back_plus_nearest_time40_geometry` | value from JSON | value from JSON | value from JSON | value from JSON or `N/A` | value from JSON or `N/A` | PASS/FAIL from JSON |
| `h12_clock_shift_back_plus_corridor3_geometry` | value from JSON | value from JSON | value from JSON | value from JSON or `N/A` | value from JSON or `N/A` | PASS/FAIL from JSON |
| `h12_clock_shift_back_plus_corridor10_geometry` | value from JSON | value from JSON | value from JSON | value from JSON or `N/A` | value from JSON or `N/A` | PASS/FAIL from JSON |

Conclusion line must state one of:

- `The three combined profiles failed the delta gate; geometry did not add useful value over baseline.`
- `At least one combined profile passed the delta gate; geometry may add incremental value, but the result remains DIAGNOSTIC_ONLY.`
```

Use exact numbers from JSON. Do not choose winner from diagnostic holdout.

- [ ] **Step 4: Update changelog, handoff and wiki**

Update:

- `CHANGELOG.md`
- `CONTEXT_HANDOFF.md`
- `wiki/research/fractal-stop-research.md`
- `wiki/index.md`
- `wiki/log.md`

Run:

```bash
./.venv/bin/python wiki/wiki.py generate
./.venv/bin/python wiki/wiki.py status
```

Expected: `Wiki is up to date. No gaps found.`

- [ ] **Step 5: Run verification**

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage6_1_relative_geometry.py -q
./.venv/bin/python -m pytest tests/ -q
git diff --check
```

Expected:

- focused tests pass
- full tests pass
- `git diff --check` has no output

- [ ] **Step 6: Commit**

Run:

```bash
git add ML/baseline/benchmark_stage6_1_relative_geometry.py tests/test_stage6_1_relative_geometry.py ML/reports/stage6_1_h12_relative_fractal_geometry.json docs/reports/2026-06-29-stage6_1-h12-relative-fractal-geometry.md CHANGELOG.md CONTEXT_HANDOFF.md wiki/REPO_integrity.md wiki/index.md wiki/log.md wiki/research/fractal-stop-research.md docs/superpowers/plans/2026-06-29-stage6_1-baseline-plus-geometry-delta.md
git commit -m "feat: test stage 6.1 baseline geometry delta"
```

---

## Self-Review

- Spec coverage: all spec requirements map to Tasks 1-4.
- Placeholder scan: no `TBD`, `TODO`, or unspecified profile names.
- Scope check: exactly three combined profiles; no horizon/ATR/TP/SL search.
- Type consistency: combined profile map keys match config keys and report invariant checks.
