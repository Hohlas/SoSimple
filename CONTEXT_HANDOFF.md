# Context Handoff

## Current Stage
Phase B research continues after Signal Research Variant 3 implementation.

## Last Completed Stage
Signal Research Variant 3 completed on 2026-04-02.

## Next Step
Do a robustness pass on the completed Variant 3 matrix. Tighten the current auto-verdict with explicit support floors such as minimum `N_filled` and/or minimum `fill_pct`, then compare the shortlisted cohorts against `ratio 3-4` and `non-Q4` again under those floors before choosing any candidate rules for EA prototyping.

## Read First
- `AGENTS.md`
- `docs/reports/2026-04-02-signal-research-variant-3.md`
- `docs/reports/2026-04-02-signal-research-variant-3-prep.md`
- `docs/reports/2026-04-01-signal-research-variant-2.md`
- `docs/superpowers/specs/2026-03-27-pf-improvement-design.md`
- `docs/superpowers/plans/2026-03-27-pf-improvement-phase-b.md`
- `API/signal_research.py`

## Open Risks
- The top cohort `ratio 4-5 × ATR Q4` is still relatively small (`N=101`), so the strongest PF rows can become thin very quickly.
- The current `Variant 3 Shortlist Verdict` is low-fill-biased and can promote rows with only a handful of fills.
- Negative controls also improve under some deeper-entry scenarios, so the current uplift is not yet clearly cohort-specific.
- The fixed baseline `12H / SL=5 / TP=50` still keeps `TP_FIRST%` low and may mask part of the entry effect.
- Broad `SELL` remains weak and regime-sensitive.

## Latest Report
`docs/reports/2026-04-02-signal-research-variant-3.md`
