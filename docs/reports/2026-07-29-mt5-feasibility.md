# MT5 Execution Loop Feasibility

> **Дата**: 2026-07-29
> **Статус**: Draft
> **Вердикт**: DIAGNOSTIC_ONLY

## Goal

Проверить, можно ли использовать MT5 Strategy Tester как источник торговых метрик вместо Python-симулятора исполнения.

## Findings

- MT5 source directory exists: `MT/MQL5/`.
- Existing MT5 source root: `MT/MQL5`.
- Existing MT5 expert path: `MT/MQL5/Experts/$o$imple.mq5`.
- Existing MT5 ML include: `MT/MQL5/Include/lib_ML_Signal.mqh`.
- Existing `$o$imple.mq5` was compiled on 2026-07-30 with MetaEditor 5; compile log `/tmp/sosimple_mt5_compile.log` reports `Result: 0 errors, 0 warnings`, and `MT/MQL5/Experts/$o$imple.ex5` was refreshed at 2026-07-30 05:33:50 UTC.
- `lib_ML_Signal.mqh` already reads frozen CSV signals, matches by bar time, applies entry filters, and supports reverse-signal exits via `ML_ExitEnabled` and `CLOSE_BUY/CLOSE_SEL("ML_Exit")`.
- Current `lib_ML_Signal.mqh` has no dedicated MT5 execution-loop event CSV writer yet, so execution logging and post-fill feature export still require additional implementation.
- First migration target remains the existing `$o$imple.mq5` port because it compiles and already contains the ML signal path; a new minimal `SoSimpleMT5SignalExecutor.mq5` should stay fallback-only.

## Unknowns

- MT5 terminal path is known: `/home/hohla/.mt5/drive_c/Program Files/MetaTrader 5/terminal64.exe`.
- MetaEditor path is known: `/home/hohla/.mt5/drive_c/Program Files/MetaTrader 5/MetaEditor64.exe`.
- Automated tester launch by agent is not yet proven in this task; treat tester execution as a manual user step for now.
- MT5 tester `Files` data path for signal/event exchange is not yet fixed and must be discovered from terminal runtime data.
- ONNX or alternative local model-scoring path inside MT5 is not yet proven.
- Methodology `13b` states terminal `MQL5` should be a symlink to repo `MT/MQL5`, but in the current environment `/home/hohla/.mt5/drive_c/Program Files/MetaTrader 5/MQL5` appears as a normal directory; compile was executed directly against the repo source path.

## Decision

Proceed with source-level prototype and manual tester handoff until MT5 terminal automation and runtime file layout are confirmed.
