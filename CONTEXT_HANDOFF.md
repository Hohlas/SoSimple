# CONTEXT HANDOFF

## Current Active State

- active track: `MT4/tester parity for retained subset`
- latest report: `docs/reports/2026-07-29-fixed11-current-history-rerun.md`
- blocker analysis: `docs/reports/2026-07-29-fixed11-python-mt4-fill-chronology.md`
- roadmap: `docs/superpowers/roadmap.md`
- latest plan: `docs/superpowers/plans/2026-07-29-fixed11-current-history-rerun.md`
- comparison artifact: `ML/reports/fractal0_fixed11_current_history_comparison.json`
- current-history Python artifact: `ML/reports/fractal0_fixed11_rich_entry_locked_test_current_history.json`
- current-history trades: `ML/reports/fractal0_fixed11_rich_entry_locked_test_current_history_trades.csv`
- unchanged labeled input: `DATA/Nero_XAUUSD_test_labeled.csv`

## Decision

Fixed11 retained-subset MT4 parity remains blocked.

- verdict: `DIAGNOSTIC_ONLY`
- stage_decision: write and execute a separate Python chronology-fix plan
- tested Python scope: all 11 fixed rules on current H1/M5 OHLC
- retained slot 1 current-history trades: `1091`
- retained slot 1 same-H1 fill/exit: `368`
- retained slot 1 `hold_bars=0`: `368`

Changing OHLC source materially changed metrics, but did not remove the
same-H1 chronology risk. Do not treat the current-history rerun as PASS,
candidate proof, live readiness or MT4 parity.

## Current Diagnostic Facts

Old vs current fixed11 aggregate:

- trades: `14507 -> 13039`
- PnL R sum: `4429.782419 -> 4065.034595`
- PF: `3.097520 -> 3.116313`
- `hold_bars=0`: `5100 -> 4495`

Retained slot 1:

- trades: `1196 -> 1091`
- PnL R sum: `395.026902 -> 339.192111`
- PF: `3.295678 -> 3.113871`
- `hold_bars=0`: `406 -> 368`
- current `hold_bars=0` close reasons: `ML_CLOSE=335`, `SL=33`
- current `hold_bars=0` PnL R sum: `-98.196808`

History checks:

- `DATA/XAUUSD_H1_OHLC.csv` equals `MT/MQL4/Files/XAUUSD_H1_OHLC.csv`.
- Current H1 vs `XAUUSD60.hst`: `matched_rows=128679`, `diff_rows=1`.
- Current M5 vs `XAUUSD5.hst`: `matched_rows=1484849`, `diff_rows=1`.
- Old H1 vs current H1: `diff_rows=13504`.

## Do Not Do

- Do not change frozen rules, cutoffs, profiles, models, targets, filters,
  entry rule, exit rule, stop policy, spread or PnL convention.
- Do not use locked-test/current-history PnL as a new selection criterion.
- Do not export current-history signals/exits for MT4 parity before fixing
  Python execution chronology.
- Do not claim MT4 parity from this Python-only rerun.

## Next Step

Create a new chronology-fix plan before touching code.

The plan should decide and test the Python execution contract:

1. after fill on H1 bar `T`, should first `MLClose` be allowed only from the
   next closed H1 bar, or can lower-timeframe timestamps allow same-H1 exit
   when exit decision is after fill;
2. add focused tests for fill at H1 open, fill after H1 open, same-H1
   `MLClose`, and SL/TP same-bar M5 ordering;
3. rerun fixed11 locked-test artifacts after the contract fix;
4. only then regenerate MT4 exports and rerun slot 1 reconciliation.

## Verification

Checks completed for the current-history rerun:

- `./.venv/bin/python ML/reports/fractal0_fixed11_retained_mt4_parity/reconcile_fill_chronology.py`
- current-history locked-test rerun with `--output-prefix ML/reports/fractal0_fixed11_rich_entry_locked_test_current_history`
- comparison JSON validation: `comparison_ok`, `rules 11`
- report/roadmap phrase check from Task 4

Full `./.venv/bin/python -m pytest tests/ -q` was not run because the plan
explicitly forbids the full suite for this workflow.
