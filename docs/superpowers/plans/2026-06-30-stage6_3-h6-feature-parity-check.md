# Stage 6.3 H6 Feature Parity Check Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Check whether Stage 6.1 geometry features and Stage 6.2 price-action features work better on H6 than on H12, using the same TP/SL contract and same-run H6 baseline.

**Architecture:** Add one bounded Stage 6.3 runner that reuses existing Stage 6.1/6.2 feature builders, changes only `horizon_bars=6`, and writes one JSON plus one canonical report. The run is diagnostic-only and compares every feature family against a same-run H6 `clock_shift_back` baseline.

**Tech Stack:** Python 3.10+, pandas, numpy, XGBoost, pytest, existing `./.venv/bin/python`, existing `DATA/Nero_XAUUSD_*_labeled.csv`, existing `DATA/XAUUSD_H1_OHLC.csv`.

## Global Constraints

- Work on the current branch; do not use git worktree.
- Use `./.venv/bin/python` for all Python commands.
- Do not change SL/TP: SL `0.5 ATR`, TP `2.0 ATR`, entry `Open[row+1]`, same-bar ambiguity = SL-first.
- Change only the horizon from H12 to H6 for Stage 6.1/6.2 feature-family parity.
- Do not add a new feature family, ATR, TP/SL, spread, threshold grid, seed list, or holdout selection rule.
- Use `val_stop` (`2021-2022`) for model/threshold/gate decisions.
- Use `diagnostic_holdout` (`2023-2025`) and `low_n_disclosure` (`2026`) only as disclosure.
- Compare Stage 6.3 profiles only to same-run H6 baseline, not directly to Stage 5 metrics.
- Show H6 vs H12 results as disclosure, not as a gate.
- Result status is capped at `DIAGNOSTIC_ONLY`.
- Final documentation should create a separate Stage 6.3 report, then add short cross-links to Stage 6.1/6.2 reports if needed.

---

## Fixed Diagnostic Questions

1. Did Stage 6.1/6.2 feature families fail mainly because H12 is too hard?
2. Do geometry or price-action features add value over a same-run H6 `clock_shift_back` baseline?
3. Does H6 make threshold selection and permutation stability materially better?
4. Does any H6 result justify a follow-up, or should the project continue to `Regression Up/Dn target foundation`?

## File Structure

**Create**

- `ML/baseline/benchmark_stage6_3_h6_feature_parity.py` - bounded H6 parity runner.
- `tests/test_stage6_3_h6_feature_parity.py` - focused tests for config, profile list, feature reuse, gate shape, CLI.
- `ML/reports/stage6_3_h6_feature_parity.json` - generated structured artifact.
- `docs/reports/2026-06-30-stage6_3-h6-feature-parity-check.md` - canonical report.

**Modify after execution**

- `CHANGELOG.md` - short Stage 6.3 entry.
- `CONTEXT_HANDOFF.md` - update next step and status.
- `docs/reports/2026-06-29-stage6_1-h12-relative-fractal-geometry.md` - add short note that H6 parity was checked separately.
- `docs/reports/2026-06-30-stage6_2-h12-price-action-feature-family.md` - add short note that H6 parity was checked separately.
- `wiki/research/fractal-stop-research.md`, `wiki/index.md`, `wiki/log.md`, `wiki/REPO_integrity.md` - ingest Stage 6.3.

**Read before implementation**

- `docs/methodology/05-eda-data-quality.md`
- `docs/methodology/11-robustness.md`
- `docs/methodology/16-reporting-audit.md`
- `docs/reports/2026-06-29-stage6_0-outcome-based-triple-barrier-foundation.md`
- `docs/reports/2026-06-29-stage6_1-h12-relative-fractal-geometry.md`
- `docs/reports/2026-06-30-stage6_2-h12-price-action-feature-family.md`
- `ML/baseline/benchmark_stage6_outcome_based.py`
- `ML/baseline/benchmark_stage6_1_relative_geometry.py`
- `ML/baseline/benchmark_stage6_2_price_action.py`

---

## Task 1: Runner Contract And Tests

**Files:**
- Create: `ML/baseline/benchmark_stage6_3_h6_feature_parity.py`
- Create: `tests/test_stage6_3_h6_feature_parity.py`

**Interfaces:**
- Produces `STAGE6_3_CONFIG` with `horizon_bars=6`.
- Produces `stage63_profile_keys() -> tuple[str, ...]`.
- Produces `stage63_feature_names(profile: str) -> list[str]`.
- Produces `stage63_build_features(df: pd.DataFrame, profile: str, ohlc: pd.DataFrame | None = None) -> np.ndarray`.

- [x] **Step 1: Write failing tests**

Create tests that assert:

- `STAGE6_3_CONFIG.horizon_bars == 6`;
- stop/take/entry contract matches Stage 6.0/6.2;
- profile keys include:
  - `h6_clock_shift_back`;
  - Stage 6.1 geometry profiles renamed with `h6_`;
  - Stage 6.2 price-action profiles renamed with `h6_`;
  - bounded combined profiles: baseline + geometry, baseline + price-action core, baseline + price-action regime;
- feature builders reuse existing Stage 6.1/6.2 builders and preserve feature widths.

Run:

```bash
./.venv/bin/python -m pytest tests/test_stage6_3_h6_feature_parity.py -q
```

Expected: fail because the module does not exist.

- [x] **Step 2: Implement minimal config/profile/feature layer**

Implement the Stage 6.3 module by wrapping existing Stage 6.1/6.2 builders. Do not duplicate feature logic unless imports make wrapping impossible.

- [x] **Step 3: Run focused tests**

```bash
./.venv/bin/python -m pytest tests/test_stage6_3_h6_feature_parity.py -q
```

Expected: pass.

---

## Task 2: Benchmark Execution And Gate

**Files:**
- Modify: `ML/baseline/benchmark_stage6_3_h6_feature_parity.py`
- Modify: `tests/test_stage6_3_h6_feature_parity.py`

**Interfaces:**
- Produces CLI:

```bash
./.venv/bin/python ML/baseline/benchmark_stage6_3_h6_feature_parity.py --stage6-3-h6-feature-parity --no-resume
```

- Produces JSON: `ML/reports/stage6_3_h6_feature_parity.json`.

- [x] **Step 1: Add tests for CLI, resume/no-resume, gate shape, and report path**

Use existing Stage 6.1/6.2 tests as pattern. Required JSON sections:

- `config`;
- `raw_runs`;
- `summary`;
- `baseline_plus_feature_delta`;
- `h6_vs_h12_disclosure`;
- `gate`;
- `status`;
- `elapsed_sec`.

- [x] **Step 2: Implement runner**

Use Stage 6.0 outcome labeling with `horizon_bars=6`. Use the same seeds as Stage 6.1/6.2: `42`, `77`, `123`.

Gate rules:

- primary comparison is each non-baseline profile vs same-run `h6_clock_shift_back`;
- AUC delta must be at least `+0.02`;
- PR lift delta must be non-negative;
- selected PF must not be worse than baseline;
- permutation p-value must be `<= 0.10`;
- profile can only be considered diagnostic, never candidate.

- [x] **Step 3: Run focused tests**

```bash
./.venv/bin/python -m pytest tests/test_stage6_3_h6_feature_parity.py -q
```

- [x] **Step 4: Run benchmark**

```bash
./.venv/bin/python ML/baseline/benchmark_stage6_3_h6_feature_parity.py --stage6-3-h6-feature-parity --no-resume
```

Expected: JSON is written with all runs completed.

---

## Task 3: Report And Documentation

**Files:**
- Create: `docs/reports/2026-06-30-stage6_3-h6-feature-parity-check.md`
- Modify: `CHANGELOG.md`
- Modify: `CONTEXT_HANDOFF.md`
- Modify: Stage 6.1/6.2 reports with short cross-link notes.
- Modify: wiki files.

- [x] **Step 1: Write canonical report**

The report must follow `docs/reports/README.md`:

- Context;
- What Was Done;
- Changed Files;
- Verification;
- Results;
- Conclusions;
- Limitations / Open Questions;
- Next Step;
- Related Materials.

Required result tables:

- same-run H6 summary by profile;
- H6 baseline vs H6 geometry/price-action delta;
- H6 vs H12 disclosure table;
- per-seed table for any profile that looks strong;
- permutation context.

Required wording:

- H6 parity does not make Stage 5 and Stage 6 fully identical, because Stage 5 uses breach/time-to-breach targets and Stage 6 uses TP/SL touch target.
- H6 parity only tests whether Stage 6 features behave differently on a shorter horizon.

- [x] **Step 2: Update Stage 6.1/6.2 reports**

Add one short note near `Limitations` or `Related Materials`:

```markdown
Follow-up: H6 parity for this feature family is reported separately in `docs/reports/2026-06-30-stage6_3-h6-feature-parity-check.md`.
```

Do not rewrite old H12 results.

- [x] **Step 3: Update changelog, handoff, wiki**

Record the Stage 6.3 result and next step.

- [x] **Step 4: Regenerate wiki integrity**

```bash
./.venv/bin/python wiki/wiki.py generate
```

---

## Task 4: Final Verification

- [x] **Step 1: Run focused tests**

```bash
./.venv/bin/python -m pytest tests/test_stage6_3_h6_feature_parity.py -q
```

- [x] **Step 2: Run Stage 6 focused tests**

```bash
./.venv/bin/python -m pytest tests/test_stage6_outcome_based.py tests/test_stage6_1_relative_geometry.py tests/test_stage6_2_price_action.py tests/test_stage6_3_h6_feature_parity.py -q
```

- [x] **Step 3: Run full tests**

```bash
./.venv/bin/python -m pytest tests/ -q
```

- [x] **Step 4: Check diff hygiene**

```bash
git diff --check
./.venv/bin/python wiki/wiki.py verify
./.venv/bin/python wiki/wiki.py status
```

- [ ] **Step 5: Final commit**

Use `stage-reporting` to close the stage and create one final commit. Do not push.

## Completion Criteria

- Stage 6.1/6.2 feature families are evaluated on H6 with the same TP/SL contract.
- H6 results are compared only against same-run H6 baseline for gate decisions.
- H6 vs H12 is reported as disclosure, not as a gate.
- Stage 5 comparison is clearly qualified: same horizon helps, but targets still differ.
- A separate Stage 6.3 report exists; old Stage 6.1/6.2 reports only receive short cross-links.
