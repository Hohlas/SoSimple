# CONTEXT HANDOFF

## Current Completed Stage

- report: `docs/reports/2026-07-23-fractal0-rich-entry-leaderboard-robustness-audit.md`
- script: `ML/baseline/audit_leaderboard_robustness.py`
- artifacts: `ML/reports/leaderboard_robustness_audit*`

## Decision

`LEADERBOARD_ROBUSTNESS_INCOMPLETE_NEEDS_COST_TIME_CHECKS`.

Verdict: `research_only`.
locked_test: `not_opened`.

## Key Result

The audit checked 11 fixed normalized rich-entry leaderboard rows without new
search and without opening `locked_test`. All 11 rows remain
`RULE_ROBUSTNESS_INCOMPLETE`: 7 are `time_only`, 4 are `movement_plus_time`.
No standalone non-time/fractal additive evidence was established.

Main blockers:

- `stress_costs_status=NOT_COMPUTABLE_FROM_SAVED_ARTIFACTS`
- `timezone_shift_status=NOT_RUN`
- `calendar_permutation_importance_status=NOT_RUN`
- `sequential_position_constraint_status=NOT_RUN`
- `multi_seed_status=NOT_RUN`
- `provider_drift_status=NOT_RUN`
- `transfer_status=NOT_RUN`

## Next Step

`Regime filter reformulation`.

First write a bounded stress-cost/time-calendar/sequential-position robustness
closure plan before any new shortlist, freeze or `locked_test` discussion.
