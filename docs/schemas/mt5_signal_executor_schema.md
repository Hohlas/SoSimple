# MT5 Signal Executor CSV Schema

> Status: diagnostic schema for MT5 Strategy Tester prototype.

## Entry Signal CSV

Path pattern:

```text
ML/reports/mt5_execution_loop/mt5_entry_signals_<run_id>.csv
```

Columns:

```text
time;feature_time;feature_available_time;decision_time;rule_id;side;entry_type;limit_price;stop_price;atr;max_fill_lag_bars
```

Forbidden columns:

```text
fill_time;exit_time;future_exit_time;future_favorable_r_3;future_adverse_r_3;hold_3_pnl_r;pnl_r
```

Reason: entry CSV describes a decision before tester fill. It must not contain
the future lifecycle of a Python-simulated trade.

## MT5 Event Log CSV

Path pattern:

```text
ML/reports/mt5_execution_loop/mt5_trade_events_<run_id>.csv
```

Columns:

```text
event;time;feature_time;feature_available_time;decision_time;execution_time;rule_id;signal_time;ticket;side;requested_price;fill_price;order_open_price;order_close_price;stop_price;close_reason;profit;bars_since_fill;bid;ask;spread;spread_atr;bar_open;bar_high;bar_low;bar_close;calculation_open;slippage_points;entry;take_profit;close;swap;commission;hold_bars;open_positions;max_positions;balance;equity;entry_time;exit_time;unrealized_pnl_r_before_decision;max_favorable_r_before_decision;max_adverse_r_before_decision;ml_exit_score;ml_exit_decision;comment
```

## Timing Contract

```text
feature_time <= decision_time <= execution_time
```

For ML-exit:

- `bars_since_fill=0` is not a working ML-exit decision.
- open-position features are computed by the MT5 expert after factual tester fill.
- first working ML-exit decision is allowed only after at least one closed H1 bar after fill.
- `feature_time`, `feature_available_time`, `decision_time` and `execution_time` must be material columns in signal/event CSV, not only prose in this document.
- If a decision is made at H1-open using the previous closed H1 bar, close execution may happen immediately after that decision; do not add an extra H1-bar delay.
