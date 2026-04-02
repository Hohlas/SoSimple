# Context Handoff

## Current Stage
Phase B research continues after the Variant 3 robustness pass.

## Last Completed Stage
Signal Research Variant 3 robustness pass completed on 2026-04-02.

## Next Step
If work moves beyond Python research, prototype only the filtered winner first: `ratio 4-5 × ATR Q4 + pullback entry_close-2ATR`. Keep `pullback entry_close-3ATR` on `ratio 4-5` / `BUY` / `ATR Q4` as a benchmark family, but not as equally clean cohort-specific rules. Before any EA change, the safest extra check is another Python-only pass on yearly stability and nearby barrier sensitivity for that `entry_close-2ATR` winner.

## Read First
- `AGENTS.md`
- `docs/reports/2026-04-02-signal-research-variant-3.md`
- `docs/reports/2026-04-02-signal-research-variant-3-prep.md`
- `docs/reports/2026-04-01-signal-research-variant-2.md`
- `docs/superpowers/specs/2026-03-27-pf-improvement-design.md`
- `docs/superpowers/plans/2026-03-27-pf-improvement-phase-b.md`
- `API/signal_research.py`

## Open Risks
- The winner `ratio 4-5 × ATR Q4 + pullback entry_close-2ATR` still has only `36` fills in the OOS slice, so support is improved but not large-sample.
- The broader `pullback entry_close-3ATR` family remains partly generic because `ratio 3-4` also improves under it (`PF=1.62`).
- The fixed baseline `12H / SL=5 / TP=50` still keeps `TP_FIRST%` low and may mask part of the entry effect.
- Broad `SELL` remains weak and regime-sensitive.

## Latest Report
`docs/reports/2026-04-02-signal-research-variant-3.md`
