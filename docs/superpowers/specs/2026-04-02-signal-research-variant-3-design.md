# Signal Research Variant 3: entry-scenario execution research

> **Date**: 2026-04-02
> **Status**: Approved for implementation
> **Scope**: Python-only statistical research in `API/signal_research.py`
> **Out of scope**: EA changes, model retraining, MT4 execution logic

## Context

Variant 2 established that the current ML signal is closer to weak drift than to impulse. Variant 3 Prep then narrowed the search space to a shortlist of cohorts where entry timing is worth testing:

- `ratio 4-5 x ATR Q4`
- `ratio 4-5`
- `BUY`
- `ATR Q4`

The mandatory negative controls are:

- `ratio 3-4`
- `non-Q4`

The fixed comparison baseline remains `12H / SL=5 / TP=50`.

## Goal

Extend `API/signal_research.py` so it can compare entry mechanics explicitly on the shortlisted cohorts and negative controls, using the same trading geometry and a common deadline.

The new stage must answer:

- whether `pullback` improves the strongest cohorts over `market`;
- whether `delayed` entry improves the path profile enough to offset lost time;
- whether `cancel-window` improves quality by skipping stale setups;
- whether any apparent improvement survives the negative controls.

## Data sources

- `MT/MQL4/Files/ml_signals.csv`
- `DATA/XAUUSD_H1_OHLC.csv`
- `MT/MQL4/Files/Nero.csv`

`pic_price` must come from the real fractal `price` feature in raw `Nero.csv`, but raw fractals inside each row are not chronologically ordered. So Variant 3 must first mirror `label_main.py` row-level sorting logic: find the fractal with the maximum embedded fractal-time inside the row, take its `price` as `pic_price`, then mirror `generate_signals.py` dedupe by `time` with `keep='last'`.

## Scenario semantics

All scenarios use the same fixed baseline geometry:

- horizon: `12H`
- stop-loss: `5`
- take-profit: `50`

All scenarios share the same deadline: the trade always expires at the original `t+12` relative to the signal time, not `12` bars after fill.

### `market`

- entry time: signal bar
- entry price: `entry_close`

### `delayed`

- entry modes:
  - `delay=1`
  - `delay=3`
- entry price: `close[t+delay]`

### `pullback`

Limit-order research only. The order is placed after the signal and monitored on future OHLC bars.

Close-relative levels:

- `entry_close - 1 * ATR14`
- `entry_close - 2 * ATR14`
- `entry_close - 3 * ATR14`

for `BUY`, mirrored upward for `SELL`.

Pic-relative levels:

- `pic_price`
- `pic_price + 1 * ATR14`
- `pic_price - 1 * ATR14`

for `BUY`, mirrored naturally by direction handling for `SELL`.

### `cancel-window`

Uses the same limit levels as `pullback`, but the pending order is cancelled if not filled within:

- `1` bar
- `3` bars
- `6` bars

If the order is not filled before expiry, the result is `SKIP`.

## Fill approximation

Pending-order fill uses future OHLC bars only:

- `BUY` limit:
  - if bar `open <= limit_price`, fill at `open`;
  - else if `low <= limit_price`, fill at `limit_price`;
- `SELL` limit:
  - if bar `open >= limit_price`, fill at `open`;
  - else if `high >= limit_price`, fill at `limit_price`.

This keeps the research closer to real pending-order execution than simply checking whether the limit was touched.

## Required outputs

The report must add Variant 3 sections after the existing Variant 2 / Prep output:

1. `Variant 3 Scenario Matrix`
2. `Variant 3 Shortlist Verdict`
3. `Variant 3 Negative Controls`

The scenario matrix must include at least:

- `cohort`
- `scenario`
- `params`
- `N_signals`
- `N_filled`
- `fill_pct`
- `skip_pct`
- `PF`
- `AvgPnL`
- `TP_FIRST_pct`
- `SL_FIRST_pct`
- `NEITHER_pct`

## Success criteria

- `pic_price` is loaded from raw Nero rows after row-level fractal-time ordering, not proxied from OHLC.
- Scenario simulation is covered by pytest before implementation claims.
- The CLI report can compare primary cohorts and negative controls without changing EA code.
- The research can be run with `python -m API.signal_research --test-only`.
