# MT4 Trailing-Stop Execution

> **Date**: 2026-04-18 21:10
> **Status**: Completed
> **Goal**: Добавить в прямой MT4-контур `iSignal=3` отдельный режим выхода по простому трейлинг-стопу `X * ATR`, чтобы проверять `take_skip_trailing_stop_v2` на той же логике выхода, под которую этот трек отбирался в Python.
> **Related plan/spec**: `docs/superpowers/plans/2026-04-18-mt4-trailing-stop-execution.md`
> **Related commit**: pending

## Context

Перед этим этапом MT4 уже умел исполнять новые CSV-сигналы `quality` и `frequency`, но закрывал сделки старым способом:

- по `ML_HoldBars`;
- либо по обратному сигналу при `ML_AllowReversal=true`.

Это позволяло проверить новый слой входа, но не давало честной проверки чистого trailing-stop execution. Получался методологический разрыв: Python-отбор строился под одну логику выхода, а MT4 исполнял другую.

## What Was Done

- Добавлен новый параметр `ML_ExitMode` в `MT/MQL4/Experts/$o$imple.mq4`:
  - `0 = timeout`
  - `1 = trailing_stop`
- Добавлен параметр `ML_TrailATR` как единый размер стартового стопа и trailing-gap.
- В `MT/MQL4/Include/lib_ML_Signal.mqh` реализован отдельный bar-based trailing-stop:
  - BUY: лучший максимум по `High[bar]`, выход при пробое `best_high - ATR * X`
  - SELL: лучший минимум по `Low[bar]`, выход при пробое `best_low + ATR * X`
- Старая timeout-логика сохранена как default path и не ломает прежние parity-check сценарии.
- Добавлены явные причины и поля в лог:
  - `reason=TrailingStop`
  - `best`
  - `trail`
  - `trail_atr`
- Обновлены MT4 docs для нового direct execution режима.

## Changed Files

- `MT/MQL4/Experts/$o$imple.mq4` (обновлён)
- `MT/MQL4/Include/lib_ML_Signal.mqh` (обновлён)
- `docs/MT/ml_signal_integration.md` (обновлён)
- `docs/MT/trading_strategy.md` (обновлён)
- `docs/superpowers/plans/2026-04-18-mt4-trailing-stop-execution.md` (создан)

## Verification

```bash
git diff --check
rg -n "ML_ExitMode|ML_TrailATR|TrailingStop" MT/MQL4/Experts/\$o\$imple.mq4 MT/MQL4/Include/lib_ML_Signal.mqh docs/MT
```

Ручной MT4 runtime-check на новом trailing-mode в этот этап не входил.

## Results

- Direct MT4-контур `iSignal=3` теперь поддерживает два независимых режима выхода:
  - timeout parity-check;
  - отдельный trailing-stop execution.
- Новый trailing-stop не использует старый `OUTPUT()`/`TRAILING_STOP()`.
- Журнал MT4 теперь позволяет различать:
  - `Timeout`
  - `TrailingStop`
  - `ReverseSignal`
- Для `take_skip_trailing_stop_v2` появился способ проверить в MT4 именно тот тип выхода, под который строились последние research-режимы `quality` и `frequency`.

## Conclusions

Главная цель этапа достигнута: MT4 больше не привязан только к timeout execution при прямом исполнении CSV-сигналов. Теперь можно отдельно тестировать:

- новый вход + старый timeout;
- новый вход + новый trailing-stop.

Это снимает главный методологический разрыв между последними Python-результатами и MT4 parity-check.

## Limitations / Open Questions

- Текущая реализация bar-based, а не tick-based: лучший ход внутри бара берётся через `High[bar] / Low[bar]`.
- Параметр `ML_TrailATR` пока один; режимы с отдельным стартовым стопом и отдельной шириной trailing не добавлялись.
- MT4 runtime-verdict для `quality` и `frequency` в новом trailing-mode ещё не получен.

## Next Step

Прогнать в MT4 минимум два сценария на одном и том же периоде:

1. `quality` rule + `ML_ExitMode=1` + `ML_TrailATR=8`
2. `frequency` rule + `ML_ExitMode=1` + `ML_TrailATR=8`

И сравнить их уже не на timeout, а на чистом trailing-stop execution.

## Related Materials

- `docs/reports/2026-04-18-take-skip-frequency-followup.md`
- `docs/reports/2026-04-18-take-skip-rule-consumer.md`
- `MT/MQL4/Include/lib_ML_Signal.mqh`
- `docs/MT/ml_signal_integration.md`
