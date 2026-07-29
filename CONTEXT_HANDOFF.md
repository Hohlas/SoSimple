# CONTEXT HANDOFF

## Current Active State

- active track: `MT4/tester parity for retained subset`
- latest report: `docs/reports/2026-07-29-fixed11-python-h1-chronology-fix.md`
- superseded blocker analysis: `docs/reports/2026-07-29-fixed11-python-mt4-fill-chronology.md`
- current-history rerun: `docs/reports/2026-07-29-fixed11-current-history-rerun.md`
- latest plan: `docs/superpowers/plans/2026-07-29-fixed11-python-h1-chronology-fix.md`
- chronology-fix artifact: `ML/reports/fractal0_fixed11_rich_entry_locked_test_h1_chronology_fix.json`
- chronology-fix trades: `ML/reports/fractal0_fixed11_rich_entry_locked_test_h1_chronology_fix_trades.csv`
- comparison artifact: `ML/reports/fractal0_fixed11_h1_chronology_fix_comparison.json`

## Decision

Fixed11 retained-subset MT4 parity remains unresolved, and the old positive
fixed11 locked-test/current-history interpretation is invalidated as the same
frozen chain.

- verdict: `DIAGNOSTIC_ONLY`
- runner original verdict before diagnostic override: `reject`
- best PF after chronology fix: `0.9388800897177361`
- kept candidates: `0`
- reason: ML-exit feature contract and execution convention changed after
  fixed11 locked_test; rerun is simulator chronology validation, not candidate
  selection.

## Current Diagnostic Facts

Current-history -> H1 chronology fix aggregate:

- trades: `13039 -> 14387`
- PnL R sum: `4065.034595 -> -530.513260`
- PF range: `2.820656-3.424707 -> 0.819373-0.938880`
- `hold_bars=0`: `4495 -> 488`
- same-H1 fill/exit: `4495 -> 72`
- same-H1 `ML_CLOSE`: `4070 -> 0`
- fill confirmation: `14387` confirmed, all `fill_execution_time_source=m5_touch`
- ambiguous trades: `150`

Python contract now says:

- `bars_since_fill=0` is excluded from working ML-exit train/score rows;
- future exit fields are target/diagnostic only;
- `ML_CLOSE` is executed at next H1 open after the decision bar;
- M5 is execution ordering only, not ML input.

## Do Not Do

- Do not claim fixed11 is profitable, live-ready, production-ready or MT4 parity
  passed.
- Do not treat old fixed11 locked-test/current-history PF as still valid under
  the corrected chronology contract.
- Do not change retained rules, cutoffs, profiles, models, targets, filters,
  entry rule, exit rule, stop policy, spread or MQL4 code without a new plan.
- Do not use locked_test or chronology-fix PnL as a new selection criterion.

## Next Step

Choose one narrow path:

1. Close the current fixed11 retained-subset path with a post-mortem because
   chronology-fix destroyed the edge.
2. Or export corrected fixed11 signals/trades only as `DIAGNOSTIC_ONLY` and run
   MT4 slot 1 parity to verify mechanics by `signal_time + direction`,
   open/fill/close reasons and missing opens.

## Verification

Completed:

- `./.venv/bin/python -m pytest tests/test_fractal0_entry_exit_grid.py -q`
- `./.venv/bin/python -m pytest tests/test_fractal0_fixed11_rich_entry_locked_test.py -q`
- fixed11 chronology-fix rerun with output prefix
  `ML/reports/fractal0_fixed11_rich_entry_locked_test_h1_chronology_fix`
- comparison artifact generation:
  `ML/reports/fractal0_fixed11_h1_chronology_fix_comparison.json`

Full `./.venv/bin/python -m pytest tests/ -q` was not run because this plan
explicitly forbids the full suite.
