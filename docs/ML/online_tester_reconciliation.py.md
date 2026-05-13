# online_tester_reconciliation.py

## Назначение

`ML/online_tester_reconciliation.py` сверяет online `ml_trade_events.csv` с ожидаемыми `ml_signals.csv` и, при наличии tester event-log, сравнивает online/tester сделки.

Это основной документ для повторных online/tester diagnostic-сверок. Отчёты в `docs/reports/` должны фиксировать конкретный результат прогона, а не дублировать здесь описание входов, команды запуска и метрик.

Инструмент нужен для проверки цепочки `MT4 -> ML -> MT4` перед реальным счетом:

- сигнал есть, но сделки нет;
- открытие не удалось и записано как `OPEN_FAILED`;
- сделка открылась не в ту сторону;
- online/tester сделки расходятся по PnL, причине закрытия или наличию пары.

## Входные данные

- online `ml_trade_events.csv` с событиями `OPEN`, `OPEN_FAILED`, `CLOSE`;
- `ml_signals.csv` в формате `time;signal`;
- опционально tester `ml_trade_events.csv`.

Сравнение online/tester выполняется по `signal_time + direction`. `ticket` используется только для связи `OPEN`/`CLOSE` внутри одного event-log.

## Запуск

```bash
./.venv/bin/python -m ML.online_tester_reconciliation \
  --events MT/MQL4/Files/ML_Trade_Events_SoSimple_662427296.csv \
  --signals MT/MQL4/Files/ml_signals.csv \
  --tester-events MT/tester/files/ML_Trade_Events_SoSimple_662427296.csv \
  --output-dir ML/reports/online_tester_reconciliation/2026-05-12 \
  --start-time "2026.05.12 00:10" \
  --end-time "2026.05.12 13:05"
```

`--start-time` и `--end-time` нужны для отсечения неполных краев online/tester логов.

## Выходные файлы

- `signals_diff.csv` - ожидаемые сигналы против `OPEN`/`OPEN_FAILED`.
- `online_trades.csv` - online OPEN/CLOSE, связанные по ticket, включая открытый хвост.
- `online_closed_trades.csv` - только закрытые online-сделки.
- `tester_trades.csv` и `tester_closed_trades.csv` - аналогичные tester-файлы, если передан `--tester-events`.
- `trades_comparison.csv` - online/tester сравнение по `signal_time + direction`.
- `summary.json` - машинно-читаемые счетчики и матожидание.
- `summary.md` - краткая Markdown-сводка.

## Метрики

В `summary.json` есть два основных среза:

- `closed_trades` - матожидание только по закрытым сделкам;
- `signal_basis` - матожидание на ожидаемый сигнал, где пропуск и открытый хвост считаются как `0`.

Блок `paired` считает только сделки, закрытые и в online, и в tester. Он показывает разницу PnL и матожидания без влияния пропущенных входов.

## Ограничения

Старые event-log файлы без `OPEN_FAILED` не позволяют отличить ошибку открытия от обычного отсутствия сделки. В таком случае причину нужно искать в текстовом MT4-логе.

Цены и PnL online/tester не обязаны совпадать до пункта: online и tester могут использовать разные тики/спред. Для строгой проверки исполнения важнее сначала сверять наличие сделки, направление, время входа и причину закрытия.
