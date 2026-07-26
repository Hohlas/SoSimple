# audit_fractal0_fixed11_candidate.py

## Purpose

Read-only audit for `fractal0_fixed11_rich_entry_locked_test` artifacts.

The script checks the frozen 11-rule locked-test package before any status
increase beyond `candidate_check_required`. It does not search new profiles,
models, targets, filters, entries, exits, stops, spreads or cutoffs.

## Inputs

Default input prefix:

```bash
ML/reports/fractal0_fixed11_rich_entry_locked_test
```

The script reads:

- `*_summary.csv`
- `*_selection.csv`
- `*_yearly.csv`
- `*_side.csv`
- `*_trades.csv`
- `*.json`

It also verifies pre-open freeze and policy artifacts when available:

- `ML/reports/fractal0_fixed11_locked_test_freeze.json`
- `ML/reports/fractal0_fixed11_locked_test_selection_policy.json`

## Outputs

Default output prefix:

```bash
ML/reports/fractal0_fixed11_candidate_audit
```

The script writes:

- `ML/reports/fractal0_fixed11_candidate_audit.json`
- `ML/reports/fractal0_fixed11_candidate_audit_findings.csv`

The JSON contains the final decision, finding counts, full findings list,
source hashes, source runner hash, split roles from the locked-test JSON and
computed split boundaries from local CSV files. Computed boundaries are
disclosure for audit handoff; they do not prove that the source locked-test
JSON contained complete pre-open split disclosure.

The auditor also reads primary project evidence from `docs/reports/`, the
locked-test protocol plan, CSV artifacts and git history. This forensic evidence
can satisfy sparse source JSON disclosure when the facts are exact and
reproducible. Missing standalone machine-readable freeze/policy JSON files then
remain warnings, not blocking errors.

## Command

```bash
./.venv/bin/python ML/baseline/audit_fractal0_fixed11_candidate.py \
  --input-prefix ML/reports/fractal0_fixed11_rich_entry_locked_test \
  --output-prefix ML/reports/fractal0_fixed11_candidate_audit
```

Exit code is `0` only for `candidate_audit_passed`. Exit code `2` means the
audit is blocked or downgraded and follow-up parity must not start.

## Scope Limits

This module preserves `original_rank` and the frozen rules. It does not choose
a new winner by locked-test results.

Stress-spread disclosure, mutual-correlation pruning, MT4/tester parity and a
model card are follow-up stages.
