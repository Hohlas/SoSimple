# Context Handoff

## Current Stage
Этап финальной MT4-сверки для уже выбранного победителя завершён.

Что теперь зафиксировано:

- прямой режим `iSignal=3` в MT4 стабилизирован;
- финальный `ml_signals.csv` для победителя был подан в `MT/tester/files/ml_signals.csv`;
- MT4 отработал именно `MLP`, без участия `TB`;
- финальный однократный прогон на `test` дал:
  - `8872` строк в `ml_signals.csv`
  - `22` активных сигнала
  - `22` сделки
  - `PF=8.47`
  - `net=+3077.05`
  - `DD=5.12%`

Технические правки, которые понадобились для этого этапа:

- `MAIN.mqh`: `ml_direct_mode` теперь определяется только после `EXPERT_SET()`;
- `lib_ML_Signal.mqh`: возвращена `ML_DIAG_PRINT()`;
- `lib_ML_Signal.mqh`: BUY back-stop зажат снизу и больше не даёт `OrderSend error 4107`.

Важно: в финальном прогоне `ScoreCol=false` было нормальным состоянием, потому что в MT4 использовался уже заранее отфильтрованный файл `time;signal`, а не полный prediction CSV.

## Last Completed Stage
Финальная MT4-сверка для замороженного победителя (2026-04-09).

## Next Step
Следующий шаг уже не в новом выборе победителя и не в повторном прогоне `test`.

1. Перенести скрипт выпуска CSV и слой отбора из черновой ветки `mt4-execution-trade-selection` в `main`, чтобы победителя можно было выпускать без ручного обходного пути.
2. При необходимости сохранить отдельную таблицу `Python ↔ MT4` по тем же `22` сделкам.
3. Только потом решать, нужен ли следующий слой по выходу из сделки или по размеру позиции.

Roadmap doc: `docs/superpowers/roadmap.md`

## Read First
- `AGENTS.md`
- `docs/reports/2026-04-09-mt4-parity-check-winner.md`
- `docs/reports/2026-04-09-entry-path-trade-filter.md`
- `docs/superpowers/plans/2026-04-09-mt4-execution-trade-selection.md`
- `docs/MT/trading_strategy.md`
- `MT/tester/logs/20260409.log`

## Open Risks
- Скрипт выпуска CSV и слой отбора, из которых был выпущен финальный CSV, пока ещё живут в черновой ветке, а не в `main`.
- В текущем окружении нет автоматической компиляции MQL через `MetaEditor`.
- Подробная таблица `Python ↔ MT4` сделка-за-сделкой ещё не сохранена как отдельный канонический артефакт.

## Latest Report
`docs/reports/2026-04-09-mt4-parity-check-winner.md`

## Active Roadmap
`docs/superpowers/roadmap.md`
