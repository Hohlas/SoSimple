# CONTEXT HANDOFF

## Current Active State

- active track: `MT4/tester parity for retained subset`
- report: `docs/reports/2026-07-27-fractal0-fixed11-retained-subset-mt4-parity.md`
- roadmap: `docs/superpowers/roadmap.md`
- plan: `docs/superpowers/plans/2026-07-27-fixed11-retained-subset-mt4-parity.md`
- current MT4 event artifact: `MT/tester/files/ML_Trade_Events_SoSimple_1709200448.csv`
- retained subset: `ML/reports/fractal0_fixed11_mutual_correlation_pruning_retained_subset.json`
- Python locked-test contract: `ML/reports/fractal0_fixed11_rich_entry_locked_test.json`
- Python trades: `ML/reports/fractal0_fixed11_rich_entry_locked_test_trades.csv`

## Decision

Fixed11 retained-subset MT4 parity is still in progress.

- verdict: `DIAGNOSTIC_ONLY`
- stage_decision: `parity_in_progress`
- tested slot: `ML_RuleSlot=1`
- parity status: closer, not passed

Do not change frozen rules, cutoffs, profiles, models, targets, filters, entry
rule, exit rule, stop policy, spread or PnL convention.

Do not use the latest MT4 profit as a new selection criterion.

## Current MT4 Result

Latest manual tester run for `ML_RuleSlot=1`:

- `ORDER_PLACED=1132`
- `OPEN=1072`
- `CLOSE=1072`
- `OPEN_FAILED=5`
- `MLClose=826`
- `Timeout=223`
- `StopLoss=23`
- closed profit sum: `62238.59`

The five failed opens are all `MarketAfterLimitPassedStopInvalid`. They should
be treated as explicit skipped cases unless the execution policy is changed by a
new plan.

## Implemented Runtime Shape

- retained rules are run one slot at a time;
- signal files: `ml_signals_fixed11_rule01.csv` ... `ml_signals_fixed11_rule05.csv`;
- exit files: `ml_exits_fixed11_rule01.csv` ... `ml_exits_fixed11_rule05.csv`;
- fixed11 entry uses `E3_open_pullback_1_0atr` limit orders;
- stop comes from CSV as Python `S2` `protective_stop_price`;
- raw reversal is disabled: `ML_AllowReversal=0`;
- Python-style exit is represented by `MLClose` from exported exit files.

## Remaining Blocker

`MLClose` timing is still shifted: most uniquely matched MT4 closes happen about
one H1 bar later than Python.

Known reconciliation facts for slot 1:

- Python filled rows for rule: `1196`
- MT4 closes: `1072`
- matched unique `signal_time + direction`: `1015`
- duplicate Python `signal_time + direction` groups: `57`
- exit-time mismatches: `798 / 1015`, usually one H1 bar late in MT4

## Next Step

1. Fix one-bar `MLClose` timing in `MT/MQL4/Include/lib_ML_Signal.mqh`.
2. Ask the user to recompile `$o$imple.mq4` and rerun tester for `ML_RuleSlot=1`.
3. Reconcile exit times, close reasons and R-sum against Python.
4. Only after slot 1 timing is acceptable, run retained slots 2-5.

Stress-spread disclosure and model card remain blocked until retained-subset MT4
parity is passed or explicitly replaced by a documented lower-status diagnostic.

## Verification

- Targeted test used for MT4 CSV/settings contract:
  `./.venv/bin/python -m pytest tests/test_mql_telemetry_params_csv_contract.py -q`
- Last observed result: `28 passed`

Full `tests/` must not be run for this workflow unless the user explicitly
changes that instruction.
