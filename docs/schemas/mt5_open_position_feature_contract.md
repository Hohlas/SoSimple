# MT5 Open Position Feature Contract

## Decision Timing

For H1 prototype:

```text
fill happens inside tester -> wait until at least one H1 bar after fill is closed -> compute ML-exit features -> close immediately after decision
```

The first working diagnostic ML-exit decision starts at `bars_since_fill=1`.
Rows with `bars_since_fill=0` may be logged for diagnostics, but must not
trigger `ML_CLOSE`.

## Working Features

- `bars_since_fill`: number of completed H1 bars after factual fill.
- `unrealized_pnl_r_before_decision`: PnL at the last known H1 close,
  normalized by factual entry risk `abs(order_open_price - stop_price)`.
- `max_favorable_r_before_decision`: favorable movement after factual fill,
  using only completed H1 bars before the decision.
- `max_adverse_r_before_decision`: adverse movement after factual fill, using
  only completed H1 bars before the decision.
- `ATR`: entry-time ATR from `mt5_entry_signals.csv`.

## Diagnostic Scorer

`DiagnosticMlExitScore(...)` is a mechanical diagnostic rule, not a final
trained model and not ML-quality evidence:

```text
bars_since_fill <= 0 -> 0.0
adverse_r >= 0.75 and unrealized_r <= 0.0 -> 1.0
bars_since_fill >= 24 -> 1.0
otherwise -> 0.0
```

`ml_exit_decision=1` writes an `ML_CLOSE` event and requests close through the
existing `MQL4Compat` order path.

## Event Log Fields

`ML_EVAL` and `ML_CLOSE` rows include:

```text
bars_since_fill
unrealized_pnl_r_before_decision
max_favorable_r_before_decision
max_adverse_r_before_decision
ml_exit_score
ml_exit_decision
```

## Forbidden

- `bars_since_fill=0` ML-close.
- Future exit time from Python.
- Python-simulated fill or Python-simulated trade PnL as MT5 input.

## Compatibility Limits

The current MT5 port uses `MQL4Compat`. The expert can compute post-fill
features from visible closed H1 bars and can request `ML_CLOSE`, but deep
history reconciliation and exact broker close reason remain limited by the
current compatibility layer. Final `CLOSE` rows may still use
`close_reason=broker_history_limited`; `ML_CLOSE` rows are the diagnostic
decision event.
