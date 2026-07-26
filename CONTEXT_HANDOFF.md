# CONTEXT HANDOFF

## Current Completed Stage

- report: `docs/reports/2026-07-25-fractal0-fixed11-candidate-audit.md`
- script: `ML/baseline/audit_fractal0_fixed11_candidate.py`
- artifacts: `ML/reports/fractal0_fixed11_candidate_audit.json`, `ML/reports/fractal0_fixed11_candidate_audit_findings.csv`
- audited input: `ML/reports/fractal0_fixed11_rich_entry_locked_test*`

## Decision

Independent fixed-11 candidate audit is complete and blocked.

- overall_decision: `candidate_audit_blocked`
- finding_count: `20`
- error_count: `18`
- warning_count: `2`
- candidate status must not be raised above `candidate_check_required`

## Main Blockers

- Missing pre-open freeze/policy artifacts: `ML/reports/fractal0_fixed11_locked_test_freeze.json`, `ML/reports/fractal0_fixed11_locked_test_selection_policy.json`.
- `split_roles` in locked-test JSON lacks row counts, min/max time, `val_select`, `val_eval` and explicit no-selection disclosure.
- `correlation_pruning_status` is not recorded as `FOLLOW_UP_REQUIRED`.
- Several low-N yearly edge slices are not marked `DIAGNOSTIC_ONLY`.
- `movement_plus_time` movement-score restoration disclosure is incomplete.

## Verified Facts

- Targeted tests: `./.venv/bin/python -m pytest tests/test_fractal0_fixed11_candidate_audit.py -q` → `17 passed`.
- Audit command exited with code `2`, as expected for blocked decision.
- Audit recorded source runner SHA256 for `ML/baseline/benchmark_fractal0_entry_quality_filter.py`: `793f18b49e06f815f8144ac6ec1fb9eff1acb67d264a002874b00039e2f0911f`.
- Audit JSON now records full `findings`, `finding_counts`, source hashes and computed split boundaries from local CSV. These computed boundaries are disclosure, not proof that source locked-test JSON had complete pre-open split disclosure.
- `BS_p05` is disclosed as diagnostic iid bootstrap, not block/stationary/timestamp-cluster bootstrap.

## Next Step

Do not start mutual-correlation pruning, MT4/tester parity, stress-spread pass/fail or trading-status discussion.

Allowed next work: fix reproducibility/disclosure of the audit-producing artifacts without changing frozen candidate rules and without using `locked_test` for new selection. If pre-open freeze/policy evidence cannot be proven, keep blocked status or downgrade to research-only.
