# MT5 Manual Tester Runbook

> **Дата**: 2026-07-29
> **Статус**: Draft
> **Вердикт**: DIAGNOSTIC_ONLY

## Inputs

- Expert: `MT/MQL5/Experts/$o$imple.mq5`
- Signal CSV: `ML/reports/mt5_execution_loop/mt5_entry_signals_<run_id>.csv`
- Event output CSV: `mt5_trade_events_<run_id>.csv`

## User Steps

1. Compile `MT/MQL5/Experts/$o$imple.mq5` in MetaEditor 5.
2. Discover the actual MT5 file directory before copying CSV:
   - preferred: the expert prints `TerminalInfoString(TERMINAL_DATA_PATH)` and the directory where `FileOpen()` reads or writes tester files;
   - fallback: diagnostic path uses `FILE_COMMON` and the runbook records `TERMINAL_COMMONDATA_PATH`;
   - do not assume repo path `MT/MQL5/Files`, because it may not exist.
3. Copy the signal CSV to the discovered MT5 tester `Files` directory as `mt5_entry_signals.csv`.
4. Run Strategy Tester:
   - symbol: `XAUUSD`;
   - timeframe: `H1`;
   - date range: selected diagnostic interval;
   - model: record exact tester model;
   - expert input `InpMT5_DiagnosticExecutor=true`;
   - expert input `InpMT5_EventFile=mt5_trade_events.csv`.
5. Return `mt5_trade_events.csv` from the discovered output path and tester HTML or XML report if available.

## Exact Source Path

- `MT/MQL5/Experts/$o$imple.mq5`

## Required Metadata

- MT5 build number.
- Broker/server.
- Symbol contract specification.
- Tester model.
- Date range.
- Deposit/currency/leverage.
- Spread mode.
- Whether account mode is netting or hedging.

## Interpretation

This run only validates the MT5 execution loop. It does not prove ML profitability until a real frozen model contract is used and audited.
