# MT4 Trailing-Stop Execution

> **Date**: 2026-04-18
> **Goal**: Добавить в прямой MT4-контур `iSignal=3` отдельный режим выхода по простому трейлинг-стопу `X * ATR`, чтобы тестировать новые `take_skip_trailing_stop_v2` входы на той же логике выхода, под которую они отбирались в Python.

## Why

Текущий MT4 parity-check для `quality` и `frequency` проверял только новый слой входа. Выход оставался старым:

- `ML_HoldBars`
- optional `ML_AllowReversal`

Из-за этого MT4-тесты не были чистой проверкой trailing-stop execution.

## Scope

- `MT/MQL4/Experts/$o$imple.mq4`
- `MT/MQL4/Include/lib_ML_Signal.mqh`
- `docs/MT/*.md`

## Plan

1. Добавить новый параметр режима выхода:
   - `ML_ExitMode = 0|1`
   - `0 = timeout`
   - `1 = trailing_stop`
2. Добавить параметр ширины трейлинга:
   - `ML_TrailATR`
3. В `lib_ML_Signal.mqh` хранить лучший ход цены по открытой позиции.
4. Реализовать bar-based trailing-stop:
   - BUY: лучший максимум `High[bar]`, стоп = `best - ATR * X`
   - SELL: лучший минимум `Low[bar]`, стоп = `best + ATR * X`
5. Сохранить старый timeout-контур как default.
6. Добавить явную диагностику в лог:
   - `reason=TrailingStop`
   - `best`
   - `trail`
   - `trail_atr`
7. Обновить MT4 docs и handoff.

## Non-Goals

- не менять старый `OUTPUT()`/`TRAILING_STOP()` контур;
- не трогать Python benchmark;
- не делать новый training-cycle;
- не переносить intrabar tick-logic в MQL4.

## Success

- MT4 direct mode умеет работать в двух режимах выхода;
- старый timeout path остаётся совместимым;
- новый trailing path включается только параметром;
- в логах tester видно, каким именно правилом закрыта сделка.
