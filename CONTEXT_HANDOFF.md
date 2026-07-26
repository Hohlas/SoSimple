# CONTEXT HANDOFF

## Current Completed Stage

- report: `docs/reports/2026-07-25-fractal0-fixed11-candidate-audit.md`
- script: `ML/baseline/audit_fractal0_fixed11_candidate.py`
- artifacts: `ML/reports/fractal0_fixed11_candidate_audit.json`, `ML/reports/fractal0_fixed11_candidate_audit_findings.csv`
- audited input: `ML/reports/fractal0_fixed11_rich_entry_locked_test*`

## Decision

Independent fixed-11 candidate audit is complete and passed for 11 individual fixed rules.

- overall_decision: `candidate_audit_passed`
- finding_count: `14`
- error_count: `0`
- warning_count: `13`
- info_count: `1`

## Evidence Basis

Audit accepts forensic evidence from project primary sources:

- `docs/reports/2026-07-24-fractal0-fixed11-locked-test.md`
- `docs/superpowers/plans/2026-07-23-fractal0-fixed11-locked-test-protocol.md`
- `ML/reports/leaderboard_closure_audit_rules.csv`
- `ML/reports/fractal0_fixed11_rich_entry_locked_test.json`
- companion locked-test CSV artifacts
- git history for prior fixed11 artifacts and locked-test report commits

## Remaining Warnings

- Separate machine-readable freeze/policy JSON files are absent; freeze/no-new-selection evidence is accepted from report/plan/CSV/git history.
- Source locked-test JSON has sparse `split_roles`; full boundaries are reconstructed from local CSV and recorded in audit JSON.
- `BS_p05` is diagnostic iid bootstrap, not block/stationary/timestamp-cluster bootstrap.
- `correlation_pruning_status=FOLLOW_UP_REQUIRED` is reconstructed from report/plan.
- Six low-N 2022 yearly slices are treated as incomplete edge-year diagnostic disclosure.
- `movement_plus_time` restoration protocol is accepted from locked-test execution log; future runners should write this as structured JSON.

## Verified Facts

- Targeted tests: `./.venv/bin/python -m pytest tests/test_fractal0_fixed11_candidate_audit.py -q` -> `23 passed`.
- Audit command exited with code `0`.
- Audit recorded source runner SHA256 for `ML/baseline/benchmark_fractal0_entry_quality_filter.py`: `793f18b49e06f815f8144ac6ec1fb9eff1acb67d264a002874b00039e2f0911f`.
- Computed split boundaries are recorded for `train_core`, `val_select`, `val_eval`, `locked_test`.

## Next Step

Run mutual-correlation pruning for the 11 individual passed rules.

Do not run MT4/tester parity, stress-spread pass/fail or model card before pruning selects the retained subset. Do not change frozen rules, cutoffs, model/profile/target/filter choices or use `locked_test` for a new winner search.
