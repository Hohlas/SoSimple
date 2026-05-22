# Live-Safe ML Audit Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a repeatable audit that checks all profitable ML systems before any online trading decision.

**Architecture:** Add a small audit layer that reads existing artifacts, writes manifests, traces feature sources, applies the leakage checklist, and produces per-system verdicts. The audit must separate old-result reproduction from live-safe approval.

**Tech Stack:** Python 3.12, pandas, pytest, existing SoSimple ML/API modules, JSON/CSV reports under `ML/reports/live_safe_ml_audit/`.

---

## Read First

- `AGENTS.md`
- `docs/audit/ml_trading_methodology.md#3-feature-contract-и-leakage-gate`
- `docs/superpowers/specs/2026-05-05-live-safe-ml-audit-design.md`
- `docs/reports/2026-04-19-lib-pic-feature-source-audit.md`
- `docs/reports/2026-04-29-online-inference-contract-hardening.md`
- `ML/entry_path_task.py`
- `ML/run_take_skip_original_contour_feature_matrix.py`
- `API/export_entry_path_v1_signals.py`
- `API/export_entry_path_v1_quantile_signals.py`

## Files

- Create: `ML/live_safe_audit.py` — shared dataclasses, verdict logic, feature classification helpers.
- Create: `ML/live_safe_audit_registry.py` — five audited systems and their known artifacts.
- Create: `ML/run_live_safe_ml_audit.py` — CLI runner for inventory, feature trace, legacy reproduction summary, verdicts.
- Create: `tests/test_live_safe_audit.py` — unit tests for classification and verdict rules.
- Create: `ML/reports/live_safe_ml_audit/` — generated audit outputs.
- Create: `docs/reports/YYYY-MM-DD-live-safe-ml-audit.md` — final human-readable report after execution.
- Modify: `docs/superpowers/roadmap.md` — link this plan as the active audit track.
- Modify after execution: `CONTEXT_HANDOFF.md`, `wiki/REPO_integrity.md`, and optionally `wiki/research/execution-tracks.md`.

---

## Task 1: Add Core Audit Types

**Files:**
- Create: `ML/live_safe_audit.py`
- Test: `tests/test_live_safe_audit.py`

- [ ] **Step 1.1: Write tests for verdict rules**

Create tests for these rules:

```python
from ML.live_safe_audit import FeatureTrace, LiveSafeStatus, verdict_from_features


def test_unknown_feature_blocks_online_pass():
    features = [
        FeatureTrace(name="session_hour", live_safe_status=LiveSafeStatus.PASS),
        FeatureTrace(name="ret_dir_atr_lag1", live_safe_status=LiveSafeStatus.UNKNOWN),
    ]
    assert verdict_from_features(features).verdict == "UNKNOWN"


def test_future_feature_fails_live_safe_audit():
    features = [
        FeatureTrace(name="predict", live_safe_status=LiveSafeStatus.FAIL),
    ]
    assert verdict_from_features(features).verdict == "FAIL"
```

- [ ] **Step 1.2: Run tests and confirm they fail**

Run:

```bash
./.venv/bin/python -m pytest tests/test_live_safe_audit.py -q
```

Expected: fail because `ML.live_safe_audit` does not exist.

- [ ] **Step 1.3: Implement minimal audit types**

Add:

- `LiveSafeStatus`: `PASS`, `FAIL`, `UNKNOWN`
- `FeatureTrace`: name, role, source path, producer, consumer, transformation, availability time, status, evidence, notes
- `AuditVerdict`: verdict, reason, failing features, unknown features
- `verdict_from_features(features)`

Rule:

- any `FAIL` feature -> system `FAIL`
- else any `UNKNOWN` feature -> system `UNKNOWN`
- else all `PASS` -> system `PASS`

- [ ] **Step 1.4: Run tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_live_safe_audit.py -q
```

Expected: pass.

- [ ] **Step 1.5: Commit**

```bash
git add ML/live_safe_audit.py tests/test_live_safe_audit.py
git commit -m "feat: add live-safe audit core types"
```

---

## Task 2: Register Audited Systems

**Files:**
- Create: `ML/live_safe_audit_registry.py`
- Test: `tests/test_live_safe_audit.py`

- [ ] **Step 2.1: Add registry tests**

Test that the registry contains exactly:

- `quality`
- `frequency`
- `original_plus_path`
- `entry_path_v1`
- `entry_path_v1_quantile`

Each entry must include:

- system name;
- checkpoint path if known;
- rule path if known;
- prediction CSV paths if known;
- source report paths;
- expected risk note.

- [ ] **Step 2.2: Implement registry**

Known anchors:

- `quality`: `ML/reports/take_skip_trailing_stop_v2_quality_selected_rule.json`
- `frequency`: `ML/reports/take_skip_trailing_stop_v2_frequency_selected_rule.json`
- `original_plus_path`: `ML/reports/take_skip_trailing_stop_v2_original_plus_path_selected_rule.json`
- `entry_path_v1`: `ML/checkpoints/transformer_entry_path_v1_best.pt`, `ML/reports/entry_path_trade_filter_selected_rule.json`
- `entry_path_v1_quantile`: `ML/checkpoints/transformer_entry_path_v1_quantile_best.pt`, `ML/reports/entry_path_v1_quantile_selected_rule.json`

- [ ] **Step 2.3: Run registry tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_live_safe_audit.py -q
```

Expected: pass.

- [ ] **Step 2.4: Commit**

```bash
git add ML/live_safe_audit_registry.py tests/test_live_safe_audit.py
git commit -m "feat: register live-safe audit systems"
```

---

## Task 3: Build Artifact Inventory CLI

**Files:**
- Create: `ML/run_live_safe_ml_audit.py`
- Test: `tests/test_live_safe_audit.py`

- [ ] **Step 3.1: Add tests for inventory output shape**

Test a pure helper that builds inventory dictionaries without touching real MT4 runtime files.

Required output fields:

- `system_name`
- `existing_paths`
- `missing_paths`
- `checkpoint_path`
- `rule_path`
- `prediction_paths`
- `report_paths`

- [ ] **Step 3.2: Implement CLI phase `inventory`**

Command:

```bash
./.venv/bin/python -m ML.run_live_safe_ml_audit --phase inventory --output-dir ML/reports/live_safe_ml_audit
```

Expected outputs:

- `ML/reports/live_safe_ml_audit/manifest.json`
- `ML/reports/live_safe_ml_audit/<system>/artifact_inventory.json`

- [ ] **Step 3.3: Run tests**

```bash
./.venv/bin/python -m pytest tests/test_live_safe_audit.py -q
```

- [ ] **Step 3.4: Run smoke inventory**

```bash
./.venv/bin/python -m ML.run_live_safe_ml_audit --phase inventory --output-dir ML/reports/live_safe_ml_audit_smoke
```

Expected: JSON files created; missing paths are reported, not hidden.

- [ ] **Step 3.5: Commit**

```bash
git add ML/run_live_safe_ml_audit.py tests/test_live_safe_audit.py
git commit -m "feat: add live-safe audit inventory CLI"
```

---

## Task 4: Generate Feature Source Trace

**Files:**
- Modify: `ML/live_safe_audit.py`
- Modify: `ML/run_live_safe_ml_audit.py`
- Test: `tests/test_live_safe_audit.py`

- [ ] **Step 4.1: Add tests for known unsafe row features**

Expected classification:

- `predict` -> `FAIL`
- `ret_6_dir_atr`, `ret_12_dir_atr`, `ret_24_dir_atr` -> `FAIL`
- `fav_*`, `adv_*` -> `FAIL`
- `ret_dir_atr_lag1` -> `UNKNOWN` until source trace proves safety
- `session_hour`, `weekday`, `ATR` -> `PASS` if source path is current/past-only

- [ ] **Step 4.2: Implement source trace builders**

Trace sources:

- old take/skip row features from `ORIGINAL_BASELINE_ROW_FEATURE_COLUMNS` in `ML/run_take_skip_original_contour_feature_matrix.py`;
- entry-path base features from `ENTRY_PATH_V1_BASE_FEATURE_COLUMNS` in `ML/entry_path_task.py`;
- entry-path window features from `ENTRY_PATH_V1_WINDOW_FEATURE_COLUMNS`;
- fractal parser fields from `ML/data_loader.py`;
- source timing notes from `docs/reports/2026-04-19-lib-pic-feature-source-audit.md`.

Each trace row must include:

- `feature_name`
- `raw_field_index`
- `raw_source_field`
- `producer_code_path`
- `consumer_code_path`
- `transformation_path`
- `role`
- `availability_time`
- `live_safe_status`
- `evidence`
- `notes`

- [ ] **Step 4.3: Add CLI phase `feature-contract`**

Command:

```bash
./.venv/bin/python -m ML.run_live_safe_ml_audit --phase feature-contract --output-dir ML/reports/live_safe_ml_audit
```

Expected outputs:

- `ML/reports/live_safe_ml_audit/<system>/feature_contract.csv`
- `ML/reports/live_safe_ml_audit/<system>/source_trace.csv`

- [ ] **Step 4.4: Run tests**

```bash
./.venv/bin/python -m pytest tests/test_live_safe_audit.py -q
```

- [ ] **Step 4.5: Commit**

```bash
git add ML/live_safe_audit.py ML/run_live_safe_ml_audit.py tests/test_live_safe_audit.py
git commit -m "feat: trace live-safe audit feature sources"
```

---

## Task 5: Apply Leakage Checklist Verdicts

**Files:**
- Modify: `ML/live_safe_audit.py`
- Modify: `ML/run_live_safe_ml_audit.py`
- Test: `tests/test_live_safe_audit.py`

- [ ] **Step 5.1: Add tests for system-level verdicts**

Expected initial verdicts:

- `quality`: `FAIL`
- `frequency`: `FAIL`
- `original_plus_path`: `FAIL`
- `entry_path_v1`: `UNKNOWN`
- `entry_path_v1_quantile`: `UNKNOWN` until baseline dependency is resolved

- [ ] **Step 5.2: Implement verdict writer**

Each `verdict.json` must contain:

- `system_name`
- `verdict`
- `reason`
- `failed_checks`
- `unknown_checks`
- `forbidden_features`
- `unknown_features`
- `allowed_next_step`
- `leakage_gate_path`: `docs/audit/ml_trading_methodology.md#3-feature-contract-и-leakage-gate`

- [ ] **Step 5.3: Run full audit dry run**

```bash
./.venv/bin/python -m ML.run_live_safe_ml_audit --phase all --output-dir ML/reports/live_safe_ml_audit
```

Expected: every system gets inventory, feature trace, and verdict.

- [ ] **Step 5.4: Run tests**

```bash
./.venv/bin/python -m pytest tests/test_live_safe_audit.py -q
```

- [ ] **Step 5.5: Commit**

```bash
git add ML/live_safe_audit.py ML/run_live_safe_ml_audit.py tests/test_live_safe_audit.py ML/reports/live_safe_ml_audit
git commit -m "feat: write live-safe audit verdicts"
```

---

## Task 6: Reproduce Legacy Results as Diagnostic Evidence

**Files:**
- Modify: `ML/run_live_safe_ml_audit.py`
- Create generated: `ML/reports/live_safe_ml_audit/<system>/legacy_reproduction.json`

- [ ] **Step 6.1: Collect old metrics without changing thresholds**

For each system, read existing JSON/CSV artifacts and record:

- old validation/test PF;
- trade count;
- MT4/tester evidence path if present;
- source report path;
- whether reproduction is exact, approximate, or artifact-only.

- [ ] **Step 6.2: Do not retrain in this task**

This phase must not change model weights or rules. It only reproduces or records old evidence.

- [ ] **Step 6.3: Run legacy summary**

```bash
./.venv/bin/python -m ML.run_live_safe_ml_audit --phase legacy-reproduction --output-dir ML/reports/live_safe_ml_audit
```

Expected: old high-PF results are visible, but unsafe systems remain `FAIL` or `UNKNOWN`.

- [ ] **Step 6.4: Commit**

```bash
git add ML/run_live_safe_ml_audit.py ML/reports/live_safe_ml_audit
git commit -m "feat: summarize legacy ML audit reproduction"
```

---

## Task 7: Write Audit Report

**Files:**
- Create: `docs/reports/YYYY-MM-DD-live-safe-ml-audit.md`
- Modify: `CONTEXT_HANDOFF.md`
- Modify: `docs/superpowers/roadmap.md`
- Modify: `wiki/REPO_integrity.md`

- [ ] **Step 7.1: Write final report**

Report sections:

- context;
- checklist gate used;
- systems audited;
- old result summary;
- feature-source findings;
- verdict table;
- systems eligible for live-safe rebuild/retrain;
- systems blocked from online;
- next step.

- [ ] **Step 7.2: Update handoff**

`CONTEXT_HANDOFF.md` must point to:

- the audit report;
- the audit output directory;
- the checklist;
- the selected next system, if any.

- [ ] **Step 7.3: Update roadmap**

Mark the audit as the active blocker before any new online trading test.

- [ ] **Step 7.4: Regenerate wiki integrity**

```bash
./.venv/bin/python wiki/wiki.py generate
./.venv/bin/python wiki/wiki.py verify
```

Expected: `OK — index is up to date.`

- [ ] **Step 7.5: Commit**

```bash
git add docs/reports CONTEXT_HANDOFF.md docs/superpowers/roadmap.md wiki/REPO_integrity.md
git commit -m "docs: report live-safe ML audit verdicts"
```

---

## Task 8: Decide the Next Execution Track

**Files:**
- No code changes unless a follow-up plan is created.

- [ ] **Step 8.1: Present decision table**

For each system:

- `PASS`: proceed to MT4 parity and forward validation;
- `FAIL`: reject old checkpoint or retrain with live-safe features;
- `UNKNOWN`: inspect source code further before testing;
- `DIAGNOSTIC_ONLY`: use only for mechanical chain checks.

- [ ] **Step 8.2: Choose one next plan**

Likely choices:

- audit deeper into `entry_path_v1` and `ret_dir_atr_lag1`;
- live-safe retrain for the best failed take/skip idea;
- forward validation for any system that reaches `PASS`;
- online dry-run only after `PASS`, MT4 parity, and forward validation.

Do not start online trading from this plan.

---

## Verification Summary

Run before final response:

```bash
./.venv/bin/python -m pytest tests/test_live_safe_audit.py -q
./.venv/bin/python -m ML.run_live_safe_ml_audit --phase all --output-dir ML/reports/live_safe_ml_audit
./.venv/bin/python wiki/wiki.py verify
git status --short --branch
```

Expected:

- tests pass;
- audit files exist for all five systems;
- wiki verify passes;
- worktree contains only intended generated outputs before commit, then is clean after commit.
