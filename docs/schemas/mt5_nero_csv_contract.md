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
- Encoding: MT5 `FileWrite` produces UTF-16LE with BOM (`\ufeff`). MT4 reference
  file is UTF-8/ASCII. Consumers must handle encoding explicitly.

## Nested Field Count

- MT5 producer writes **23** nested fields per non-empty fractal (field 23 =
  Shift, confirmed by `lib_PIC.mqh:918`).
- The legacy MT4 reference file (`MT/MQL4/Files/Nero_XAUUSD.csv`, generated
  2004–2026 by an older build) contains **22** fields (no Shift).
- Current MT4 code in git (`MT/MQL4/Include/lib_PIC.mqh:919`) also writes 23.
- Parity comparison uses the first `min(N_mt4, N_mt5)` common fields (22).
- Field 23 (Shift) is checked for MT5 internal consistency only: integer >= 1
  for non-empty fractals (bar offset into the past, always positive).

## Parity Checks

Compare MT5-generated `Nero.csv` against current MT4/Python source on the same
symbol, timeframe and interval:

- row count;
- min/max time;
- duplicate time count;
- column names/order;
- `fractal0..fractal99` parse success;
- `len(fractalN.split(':')) == 23` for every non-empty MT5 fractal field;
- `len(fractalN.split(':')) == 22` expected for legacy MT4 reference;
- 23rd nested field is `Shift` (MT5 only, internal consistency);
- full nested format agreement against MT4 on first 22 fields, sampled rows;
- `fractal0.direction` agreement rate;
- `fractal0.price` difference summary.

## Verdict

If MT5 `Nero.csv` parity is not proven, any downstream MT5 ML result remains
`DIAGNOSTIC_ONLY`.
