# CONTEXT HANDOFF

## Current Completed Stage

- report: `docs/reports/2026-07-23-fractal0-fixed11-internal-closure-rerun.md`
- script: `ML/baseline/fractal0_fixed11_internal_closure_rerun.py`
- artifacts: `ML/reports/fractal0_fixed11_internal_closure_rerun*`

## Decision

`FIXED11_INTERNAL_CLOSURE_RISK_FLAGS_RESEARCH_ONLY`.

Verdict: `research_only`.
locked_test: `not_opened`.
provider_drift_status: `NOT_IN_SCOPE`.
transfer_status: `NOT_IN_SCOPE`.

## Key Result

The producer-level rerun checked the exact 11 fixed normalized leaderboard
rule families with `--threads 24`, saved cutoffs and no new winner selection.

Computed:

- `stress_cost_status=COMPUTED` with `33` rows, `12` risk flags.
- `timezone_rescore_status=COMPUTED` with `55` rows, `0` risk flags.
- `calendar_permutation_status=COMPUTED` with `11` rows, `4` risk flags.
- `calendar_no_ml_baseline_status=COMPUTED` with `11` rows, `11` risk flags.
- `multiseed_status=COMPUTED` with `55` rows; aggregate has `11` rows and `0` risk flags.
- classification: `11/11 INTERNAL_CLOSURE_RISK_FLAGGED`.

Main interpretation: rich/fractal entry-quality remains time-heavy
`research_only`; calendar baseline dominance and stress-cost fragility block
any provider/transfer/locked-test discussion.

## Next Step

`Regime filter reformulation` remains the only active track.

Next allowed action: close rich/fractal entry-quality branch as time-heavy
research-only, then write a narrower regime-filter reformulation plan. Do not
open `locked_test`.
