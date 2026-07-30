# MT5 Nero.csv Producer Contract

> **Status**: required for MT5 execution-loop migration.

## Goal

MT5 must be able to generate a `Nero.csv`-compatible market feature stream.
Without this producer, MT5 can only test execution of already prepared Python
signals and cannot become the source of truth for the full live/test cycle.

## Required Properties

- Producer: `MT/MQL5/Experts/$o$imple.mq5` via MQL5 `lib_PIC.mqh`.
- Output role: raw/runtime input for Python processing.
- Forbidden output: Python labels, Python simulated fill, Python exit time, PnL.
- Time convention: H1 row time must match the current MT4/Python convention and be documented in parity manifest.
- Delimiter: semicolon.

## Parity Checks

Compare MT5-generated `Nero.csv` against current MT4/Python source on the same
symbol, timeframe and interval:

- row count;
- min/max time;
- duplicate time count;
- column names/order;
- `fractal0..fractal99` parse success;
- `len(fractalN.split(':')) == 23` for every non-empty fractal field;
- 23rd nested field is `Shift`;
- full nested format agreement against MT4 on sampled rows;
- `fractal0.direction` agreement rate;
- `fractal0.price` difference summary.

## Verdict

If MT5 `Nero.csv` parity is not proven, any downstream MT5 ML result remains
`DIAGNOSTIC_ONLY`.
