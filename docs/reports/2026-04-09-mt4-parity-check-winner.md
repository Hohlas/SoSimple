# MT4: замороженный победитель подтверждён на финальном прогоне

> **Date**: 2026-04-09 21:53 MSK
> **Status**: Completed
> **Goal**: Довести прямой режим MT4 до корректного финального прогона уже выбранного победителя и проверить его на `test` ровно один раз
> **Related plan/spec**: `docs/superpowers/plans/2026-04-09-mt4-execution-trade-selection.md`, `docs/reports/2026-04-09-entry-path-trade-filter.md`
> **Related commit**: pending

## Context

После отбора сделок поверх `A @ 7.5%` уже был выбран и заморожен победитель, для которого офлайн-экспорт давал `22` активных сигнала на `test`.

До финального MT4-прогона оставалось убрать три технические проблемы в прямом режиме:

- режим `iSignal=3` мог определяться слишком рано, до подстановки параметров из строки эксперта;
- `SERVICE.mqh` вызывал `ML_DIAG_PRINT()`, а в новом режиме этой функции уже не было;
- при очень большом `ATR` BUY-стоп мог уходить в отрицательную цену и давать `OrderSend error 4107`.

Нужно было исправить эти места, выпустить уже отфильтрованный `ml_signals.csv` для замороженного победителя и сделать один финальный прогон в MT4 без повторного сравнения нескольких семейств на `test`.

## What Was Done

- В [MT/MQL4/Include/MAIN.mqh](/home/hohla/git/SoSimple/MT/MQL4/Include/MAIN.mqh) выбор прямого режима `iSignal=3` перенесён на место после `EXPERT_SET()`, чтобы эксперт использовал уже реальные входные параметры.
- В [MT/MQL4/Include/lib_ML_Signal.mqh](/home/hohla/git/SoSimple/MT/MQL4/Include/lib_ML_Signal.mqh) возвращена функция `ML_DIAG_PRINT()`, которую безусловно вызывает `OnTester()`.
- Там же BUY back-stop зажат снизу минимальной положительной ценой, чтобы не получать ошибку `4107` на больших значениях `ATR`.
- В [docs/MT/trading_strategy.md](/home/hohla/git/SoSimple/docs/MT/trading_strategy.md) уточнена инструкция по тесту и исправлен псевдокод `MAIN()`, чтобы документация совпадала с реальным порядком вызовов.
- Из уже замороженного победителя выпущен предфильтрованный `ml_signals.csv` для тестера и рабочего каталога MT4:
  - `MT/tester/files/ml_signals.csv`
  - `MT/MQL4/Files/ml_signals.csv`
- Пользователь пересобрал эксперта в MT4 и выполнил один финальный прогон на том же тестовом отрезке.

## Changed Files

- `MT/MQL4/Include/MAIN.mqh`
- `MT/MQL4/Include/lib_ML_Signal.mqh`
- `docs/MT/trading_strategy.md`
- `docs/reports/2026-04-09-mt4-parity-check-winner.md`
- `CHANGELOG.md`
- `CONTEXT_HANDOFF.md`

## Verification

```bash
git diff --check -- MT/MQL4/Include/MAIN.mqh MT/MQL4/Include/lib_ML_Signal.mqh docs/MT/trading_strategy.md docs/reports/2026-04-09-mt4-parity-check-winner.md CHANGELOG.md CONTEXT_HANDOFF.md
rg -n "MLP_INIT|pred_ret_24_dir_atr column not found|=== MLP DIAGNOSTICS ===|Opened:           22|Timeout closes:   22|=== TB DIAGNOSTICS ===|  Total signals:    0" MT/tester/logs/20260409.log
rg -c "open #[0-9]+ " MT/tester/logs/20260409.log
rg -c "close #[0-9]+ " MT/tester/logs/20260409.log
rg -n "4107|invalid stoploss|OrderSend error" MT/tester/logs/20260409.log
```

Observed:

- `git diff --check`: без замечаний
- в логе есть `MLP_INIT: Loaded V4.0 8872 rows from ml_signals.csv`
- `MLP` показывает `Opened: 22` и `Timeout closes: 22`
- `TB` в этом прогоне полностью выключен и показывает `0` сигналов
- `open #`: `22`
- `close #`: `22`
- ошибок `4107` и `invalid stoploss` в финальном логе нет
- компиляция эксперта в MT4 выполнена пользователем вручную, без ошибок

## Results

### Экспортный CSV для финального прогона

| Показатель | Значение |
|---|---:|
| Строк в `ml_signals.csv` | `8872` |
| Активных сигналов | `22` |
| Формат | `time;signal` |

### Финальный MT4-прогон замороженного победителя

| Метрика | Значение |
|---|---:|
| Чистая прибыль | `+3077.05` |
| Profit Factor | `8.47` |
| Максимальная просадка | `685.00` |
| Относительная просадка | `5.12%` |
| Всего сделок | `22` |
| Прибыльных сделок | `14` |
| Убыточных сделок | `8` |
| BUY | `18` |
| SELL | `4` |

### Что показал режим в логе

| Счётчик | Значение |
|---|---:|
| `Total signals` | `22` |
| `Score filtered` | `0` |
| `Position blocked` | `0` |
| `Opened` | `22` |
| `Timeout closes` | `22` |
| `Reverse closes` | `0` |
| `TB Total signals` | `0` |

Важно: строка `ScoreCol=false` в этом финальном прогоне является нормальной. В MT4 был подан уже заранее отфильтрованный файл `time;signal`, поэтому дополнительный score-фильтр внутри эксперта не должен был участвовать.

## Conclusions

Финальный однократный прогон в MT4 для уже выбранного победителя прошёл корректно.

Главные выводы:

- прямой режим `iSignal=3` теперь действительно исполняет нужного победителя, а не сваливается обратно в старый путь;
- журнал `MLP` и итоговый отчёт согласованы: `22` сигнала превратились в `22` сделки без потерь и без блокировок;
- баг с отрицательным BUY-стопом устранён;
- правило `test только для победителя` соблюдено: на `test` не сравнивались несколько семейств.

На практическом уровне это означает, что текущего победителя можно считать подтверждённым не только офлайн, но и в реальном торговом контуре MT4.

## Limitations / Open Questions

- Сам слой отбора и скрипт выпуска CSV, из которого был выпущен финальный `ml_signals.csv`, пока живут в черновой ветке `mt4-execution-trade-selection`, а не в `main`.
- В текущем окружении нет `MetaEditor`, поэтому локальная автоматическая компиляция MQL не запускалась.
- Подробная таблица `Python ↔ MT4` сделка-за-сделкой ещё не сохранена как отдельный канонический артефакт, хотя финальный лог уже содержит достаточно данных для такой сверки.

## Next Step

1. Перенести выпуск финального `ml_signals.csv` из черновой ветки в основной кодовый контур `main`, чтобы победителя можно было воспроизводить без ручного обходного пути.
2. При необходимости сохранить отдельную таблицу `Python ↔ MT4` по тем же `22` сделкам.
3. Только после этого решать, нужен ли следующий слой по выходу из сделки или по размеру позиции.

## Related Materials

- `docs/reports/2026-04-09-entry-path-trade-filter.md`
- `docs/superpowers/plans/2026-04-09-mt4-execution-trade-selection.md`
- `docs/MT/trading_strategy.md`
- `MT/tester/logs/20260409.log`
