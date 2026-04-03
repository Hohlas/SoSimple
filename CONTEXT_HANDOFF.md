# Context Handoff

## Current Stage
Phase B research now continues through the new Signal Path Atlas workflow.

## Last Completed Stage
Signal Path Atlas tooling and stage close completed on 2026-04-03.

## Next Step
Use `API/signal_path_atlas.py` as the primary research entry point and turn its frozen tables into the first canonical atlas readout. The immediate task is not EA prototyping and not another narrow PF pass around the old winner. Instead:
- review global path quantiles, first-passage and ordering as the main signal description;
- identify only those atlas claims that truly replicate on holdout;
- decide whether any replicated cohort/archetype evidence supports a future `market`, `pullback`, both or neither;
- keep the old Variant 3 winner `ratio 4-5 × ATR Q4 + pullback entry_close-2ATR` only as a benchmark, not as the default next implementation target.

## Read First
- `AGENTS.md`
- `docs/reports/2026-04-03-signal-path-atlas.md`
- `docs/reports/2026-04-02-signal-research-variant-3.md`
- `docs/reports/2026-04-02-signal-research-variant-3-prep.md`
- `docs/reports/2026-04-01-signal-research-variant-2.md`
- `docs/superpowers/specs/2026-04-03-signal-path-atlas-design.md`
- `docs/superpowers/plans/2026-04-03-signal-path-atlas.md`
- `API/signal_path_atlas.py`

## Open Risks
- The path-atlas layer is now implemented, but its research interpretation still needs a canonical readout; tooling exists before conclusions are fully stabilized.
- The current smoke run ends with `execution_implications = neither`, so no downstream execution path is justified yet by atlas evidence alone.
- `API/signal_path_atlas.py` is already a fairly large single-file research module; future growth may require splitting orchestration from analysis helpers.
- The old Variant 3 winner still exists as a benchmark, but its low-support nature remains unresolved and should not quietly retake the roadmap without atlas-based evidence.

## Latest Report
`docs/reports/2026-04-03-signal-path-atlas.md`
