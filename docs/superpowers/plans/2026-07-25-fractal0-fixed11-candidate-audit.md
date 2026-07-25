# Fractal0 Fixed-11 Candidate Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Independently audit the `fractal0_fixed11_rich_entry_locked_test` artifacts before any status increase beyond `candidate_check_required`.

**Architecture:** Add a read-only audit script that validates the locked-test JSON and CSV artifacts against the frozen 11-rule contract, pre-open freeze/policy evidence, split boundaries, source hashes and predefined gates. The script must not rerun model selection, tune thresholds, change rules or recompute a new winner; it writes audit artifacts and a final report with either `candidate_audit_passed`, `candidate_audit_blocked` or `research_only_downgrade_required`.

**Tech Stack:** Python via `./.venv/bin/python`, pandas, json, hashlib, pytest, existing Fractal0 artifacts in `ML/reports/`, canonical docs in `docs/reports/`.

## Global Constraints

- Work on the current branch; do not create a separate worktree.
- Use only `./.venv/bin/python` for Python commands.
- Do not run a new search over profiles, models, targets, filters, entries, exits, stops, spreads or cutoffs.
- Do not reopen `locked_test` for new selection. Only read the already produced `ML/reports/fractal0_fixed11_rich_entry_locked_test*` artifacts.
- Do not choose a new winner by `locked_test`; preserve `original_rank` and report candidate status per frozen rule.
- This audit checks all 11 individual candidate rules. Mutual correlation pruning and the final number of portfolio candidates are a separate follow-up stage.
- Do not raise status above `candidate_check_required` inside this audit. The highest audit decision is `candidate_audit_passed`.
- Any artifact inconsistency, missing source hash, split leak, changed frozen rule, missing CSV row, impossible metric, or undocumented movement-score restoration must block follow-up parity.
- Missing pre-open freeze/policy artifacts block `candidate_audit_passed`. A retroactive freeze artifact may be recorded only as disclosure, not as proof of pre-open freeze.
- MT4/tester parity, locked-test stress-spread disclosure and model card are follow-up stages, not part of this audit.
- After Python changes, run targeted tests and then `./.venv/bin/python -m pytest tests/ -q`.

---

## Roadmap Metadata

```text
depends_on:
  - docs/reports/2026-07-24-fractal0-fixed11-locked-test.md
  - docs/superpowers/plans/2026-07-23-fractal0-fixed11-locked-test-protocol.md
  - ML/reports/fractal0_fixed11_locked_test_freeze.json
  - ML/reports/fractal0_fixed11_locked_test_selection_policy.json
  - ML/reports/fractal0_fixed11_rich_entry_locked_test.json
  - ML/reports/fractal0_fixed11_rich_entry_locked_test_summary.csv
  - ML/reports/fractal0_fixed11_rich_entry_locked_test_trades.csv
  - ML/reports/fractal0_fixed11_rich_entry_locked_test_yearly.csv
  - ML/reports/fractal0_fixed11_rich_entry_locked_test_side.csv
  - ML/reports/fractal0_fixed11_rich_entry_locked_test_selection.csv
blocks:
  - MT4/tester parity
  - locked-test stress-spread disclosure
  - mutual-correlation pruning and final portfolio candidate count decision
  - model card
  - any candidate/trading-status discussion
supersedes_prior_roadmap_snapshot:
  - regime filter reformulation was previously next immediate action before the 2026-07-24 locked-test report; current roadmap already points to this audit
exit_decisions:
  - candidate_audit_passed_then_run_mt4_tester_parity
  - candidate_audit_blocked_then_fix_artifact_or_downgrade
  - research_only_downgrade_required
locked_test_policy:
  - already_opened_once_on_2026-07-24_for_11_frozen_rules
  - no_new_locked_test_selection
```

## Methodology Map

- `docs/methodology/06-temporal-split.md`: verify locked-test boundaries and no train/validation reuse for selection.
- `docs/methodology/09-validation-freeze.md`: verify frozen rules, saved cutoffs and no post-open changes.
- `docs/methodology/10-frozen-test-oos.md`: verify locked-test metrics, side/yearly disclosure and predefined gates.
- `docs/methodology/11-robustness.md`: check side/yearly concentration and candidate fragility flags.
- `docs/methodology/12-backtest-costs.md`: verify canonical spread disclosure and mark stress-spread as follow-up.
- `docs/methodology/13-export-mt4-parity.md`: define parity handoff after audit pass.
- `docs/methodology/16-reporting-audit.md`: structured audit JSON, hashes, commands, limitations and report consistency.

## Expected Files

- Create: `ML/baseline/audit_fractal0_fixed11_candidate.py`
- Create: `tests/test_fractal0_fixed11_candidate_audit.py`
- Create: `docs/ML/audit_fractal0_fixed11_candidate.py.md`
- Create after execution: `ML/reports/fractal0_fixed11_candidate_audit.json`
- Create after execution: `ML/reports/fractal0_fixed11_candidate_audit_findings.csv`
- Create after execution: `docs/reports/2026-07-25-fractal0-fixed11-candidate-audit.md`
- Modify after execution: `CHANGELOG.md`
- Modify after execution: `CONTEXT_HANDOFF.md`
- Modify after execution: `docs/superpowers/roadmap.md`
- Modify after execution: `MODULE_INDEX.md`
- Sync wiki only during final stage-reporting.

## Audit Policy

Audit pass requires all checks below:

- JSON and every linked CSV exist and have non-empty rows.
- Pre-open freeze/policy artifacts exist, are read before declaring pass, and include `rule_hash_sha256`, frozen execution contract and selection policy. If they are missing, emit `ERROR pre_open_freeze_artifact_missing`; do not recreate them as proof.
- Source hashes in JSON match current local files for rules CSV, source M5 stop-grid artifact, H1 OHLC, M5 OHLC and locked-test CSV.
- Audit artifact records `source_runner_sha256` for `ML/baseline/run_fractal0_fixed11_rich_entry_locked_test.py` and `source_runner_declared_path` from the locked-test JSON. If the locked-test JSON lacks a runner hash, emit `WARNING source_runner_hash_missing_from_locked_test_json`.
- `rule_count=11`, `evaluated_rule_count=11`, `gate_pass_count=11`, `kept_candidates=11`, and all rule identities match `ML/reports/leaderboard_closure_audit_rules.csv`.
- `correlation_pruning_status=FOLLOW_UP_REQUIRED`; `kept_candidates=11` means individual gate pass count, not final portfolio size.
- Every selected rule has `PF >= 1.20`, diagnostic `BS_p05 >= 1.00`, `n_trades >= 100`, and `bs_p05_method` recorded.
- Until a true block/stationary/timestamp-cluster bootstrap is implemented, current `BS_p05` is diagnostic and must produce `WARNING bs_p05_iid_bootstrap_limitation`; `candidate_audit_passed` may not rely on `BS_p05` as the sole uncertainty gate.
- BUY and SELL side rows exist for every rule; side PF below `1.20` blocks candidate pass unless the report explicitly downgrades to side-specific research-only.
- Yearly rows exist for every rule. Full-year slices need `n_trades >= 30` for yearly PASS; incomplete edge-year slices with `n_trades < 30` must be marked `DIAGNOSTIC_ONLY` and cannot be used as yearly stability evidence. Any non-diagnostic yearly PF below `1.20`, negative year, missing year, or unclassified low-N year blocks candidate pass.
- `locked_test` period in artifacts is `2022-12-02` to `2026-06-04` with `9463` source rows and no overlap with `train_core`, `val_select` or `val_eval`.
- Audit output includes `split_boundaries` and `split_roles` for `train_core`, `val_select`, `val_eval` and `locked_test`, including row counts, min/max time and source of each value.
- Report states that `locked_test` was not used for choosing winner, thresholds, features, models or filters.
- `movement_plus_time` rows disclose restored movement scores with `affected_rule_count=4`, target, profile, model family, seeds, fit split, locked-test label usage, scaler fit split and source config/hashes or `UNKNOWN`. If these fields are `UNKNOWN`, time-only rules may pass, but movement-plus-time rules are downgraded or blocked until disclosure is complete.
- Stress-spread and MT4/tester parity remain `FOLLOW_UP_REQUIRED`, not silently passed.

Overall decisions:

- `candidate_audit_passed`: all audit checks pass for the 11 individual rules; next stage is mutual-correlation pruning, then MT4/tester parity for the retained subset.
- `candidate_audit_blocked`: artifact/report inconsistency or missing disclosure; fix or rerun only the broken audit-producing step.
- `research_only_downgrade_required`: locked-test evidence itself violates gates or freeze/split integrity.

---

### Task 1: Artifact Contract Tests

**Files:**
- Create: `tests/test_fractal0_fixed11_candidate_audit.py`
- Create: `ML/baseline/audit_fractal0_fixed11_candidate.py`

**Interfaces:**
- Consumes: locked-test JSON/CSV paths under `ML/reports/`.
- Produces: `load_artifacts(prefix: Path) -> AuditArtifacts`, `validate_artifact_contract(artifacts: AuditArtifacts) -> list[AuditFinding]`.

- [ ] **Step 1: Write failing tests**

Create tests that assert the audit module loads JSON, summary, selection, yearly and side CSV files, rejects missing files, and requires exactly 11 unique `rule_id` values.

- [ ] **Step 2: Run the failing tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_fixed11_candidate_audit.py -q
```

Expected: FAIL because `ML/baseline/audit_fractal0_fixed11_candidate.py` does not exist.

- [ ] **Step 3: Implement read-only artifact loading**

Implement dataclasses:

```python
@dataclass(frozen=True)
class AuditFinding:
    severity: str
    check_id: str
    message: str
    rule_id: str | None = None


@dataclass(frozen=True)
class AuditArtifacts:
    payload: dict[str, Any]
    summary: pd.DataFrame
    selection: pd.DataFrame
    yearly: pd.DataFrame
    side: pd.DataFrame
    trades: pd.DataFrame
```

- [ ] **Step 4: Verify tests pass**

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_fixed11_candidate_audit.py -q
```

Expected: PASS for contract-loading tests.

### Task 2: Freeze, Hash And Split Audit

**Files:**
- Modify: `ML/baseline/audit_fractal0_fixed11_candidate.py`
- Modify: `tests/test_fractal0_fixed11_candidate_audit.py`

**Interfaces:**
- Produces: `audit_hashes(artifacts: AuditArtifacts) -> list[AuditFinding]`, `audit_split_policy(artifacts: AuditArtifacts) -> list[AuditFinding]`, `audit_pre_open_freeze(artifacts: AuditArtifacts) -> list[AuditFinding]`.

- [ ] **Step 1: Add tests for freeze, source hash and split failures**

Use temporary artifact copies to prove missing pre-open freeze/policy files, changed SHA256, missing hash, wrong `locked_test` row count, missing `val_select`/`val_eval` roles, or missing split disclosure creates `ERROR` findings.

- [ ] **Step 2: Implement freeze, hash and split checks**

Check pre-open freeze/policy files if present; if absent, emit `pre_open_freeze_artifact_missing`. Check source paths/hashes recorded in JSON, including `source_artifact_sha256`; compute and record `source_runner_sha256`. Verify locked-test source row count, period, `train_core`/`val_select`/`val_eval`/`locked_test` roles, and disclosure that train/validation roles were not used for new choice.

- [ ] **Step 3: Run targeted tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_fixed11_candidate_audit.py -q
```

Expected: PASS.

### Task 3: Metric And Candidate Gate Audit

**Files:**
- Modify: `ML/baseline/audit_fractal0_fixed11_candidate.py`
- Modify: `tests/test_fractal0_fixed11_candidate_audit.py`

**Interfaces:**
- Produces: `audit_candidate_gates(artifacts: AuditArtifacts) -> list[AuditFinding]`.

- [ ] **Step 1: Add tests for PF, BS, trade-count, side, yearly and movement-score failures**

Construct small DataFrame fixtures where one rule violates each gate. Include fixtures for yearly `n_trades < 30`, diagnostic edge-year classification, `bs_p05_iid_bootstrap_limitation`, missing movement-score restoration fields and unknown movement-score source hashes. Assert the audit emits `ERROR` or `WARNING` with stable `check_id` values.

- [ ] **Step 2: Implement gate checks**

Validate summary/selection consistency, `PF >= 1.20`, diagnostic `BS_p05 >= 1.00`, `n_trades >= 100`, BUY/SELL side coverage, yearly coverage, low-N yearly classification, correlation-pruning handoff and movement-score restoration disclosure. Record `bs_p05_method=current_iid_trade_bootstrap_despite_block_bootstrap_pf_name` unless a true block/stationary/timestamp-cluster bootstrap replaces it before execution.

- [ ] **Step 3: Run targeted tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_fixed11_candidate_audit.py -q
```

Expected: PASS.

### Task 4: CLI And Audit Artifacts

**Files:**
- Modify: `ML/baseline/audit_fractal0_fixed11_candidate.py`
- Modify: `tests/test_fractal0_fixed11_candidate_audit.py`
- Create: `docs/ML/audit_fractal0_fixed11_candidate.py.md`

**Interfaces:**
- Produces CLI:

```bash
./.venv/bin/python ML/baseline/audit_fractal0_fixed11_candidate.py \
  --input-prefix ML/reports/fractal0_fixed11_rich_entry_locked_test \
  --output-prefix ML/reports/fractal0_fixed11_candidate_audit
```

- [ ] **Step 1: Add CLI smoke test**

Use a temporary output prefix and assert JSON/CSV audit files are written with `overall_decision` and findings.

- [ ] **Step 2: Implement CLI**

Write `*_audit.json` and `*_audit_findings.csv`. Exit code `0` only for `candidate_audit_passed`; exit code `2` for blocked or downgrade decisions.

- [ ] **Step 3: Add module documentation**

Document purpose, inputs, outputs, command, no-new-selection constraint and follow-up stages in `docs/ML/audit_fractal0_fixed11_candidate.py.md`.

- [ ] **Step 4: Run targeted tests**

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_fixed11_candidate_audit.py -q
```

Expected: PASS.

### Task 5: Execute Audit And Close The Stage

**Files:**
- Create: `ML/reports/fractal0_fixed11_candidate_audit.json`
- Create: `ML/reports/fractal0_fixed11_candidate_audit_findings.csv`
- Create: `docs/reports/2026-07-25-fractal0-fixed11-candidate-audit.md`
- Modify: `CHANGELOG.md`
- Modify: `CONTEXT_HANDOFF.md`
- Modify: `docs/superpowers/roadmap.md`
- Modify: `MODULE_INDEX.md`
- Modify: `wiki/` via stage-reporting only

**Interfaces:**
- Consumes: CLI from Task 4.
- Produces: final decision and next-stage handoff.

- [ ] **Step 1: Run the audit**

Run:

```bash
./.venv/bin/python ML/baseline/audit_fractal0_fixed11_candidate.py \
  --input-prefix ML/reports/fractal0_fixed11_rich_entry_locked_test \
  --output-prefix ML/reports/fractal0_fixed11_candidate_audit
```

Expected: JSON and CSV are produced. If exit code is `2`, inspect findings and do not proceed to correlation pruning or parity.

- [ ] **Step 2: Run verification**

Run:

```bash
./.venv/bin/python -m pytest tests/test_fractal0_fixed11_candidate_audit.py -q
./.venv/bin/python -m pytest tests/ -q
```

Expected: targeted tests pass, then full suite passes.

- [ ] **Step 3: Write the stage report**

Create `docs/reports/2026-07-25-fractal0-fixed11-candidate-audit.md` with: goal, inputs, hashes, split boundaries, pre-open freeze evidence, BS method disclosure, movement-score restoration disclosure, checks, findings table, overall decision, limitations, forbidden interpretations and next step.

- [ ] **Step 4: Sync project status**

Update `CHANGELOG.md`, `CONTEXT_HANDOFF.md`, `docs/superpowers/roadmap.md`, `MODULE_INDEX.md` and wiki through `stage-reporting`.

- [ ] **Step 5: Stop condition**

If decision is `candidate_audit_passed`, next plan is mutual-correlation pruning for the 11 individually passed rules; MT4/tester parity follows only for the retained subset. If decision is blocked or downgrade, next work is limited to explaining the blocker or fixing a reproducibility error without changing frozen candidate rules.
