# MT/MQL4/

MetaTrader 4 часть проекта: советники, include-библиотеки и файлы обмена с Python.

## Читать

- [`../../docs/MT/ml_signal_integration.md`](../../docs/MT/ml_signal_integration.md) — интеграция ML-сигналов с MT4.
- [`../../docs/MT/lib_PIC.mqh.md`](../../docs/MT/lib_PIC.mqh.md) — формирование PIC-фракталов.
- [`../../docs/MT/trading_strategy.md`](../../docs/MT/trading_strategy.md) — торговая логика эксперта.

## Правило для агентов

Файлы `*.mqh` и `*.mq4` открывать точечно и только при явной связи с задачей или `#include`.
