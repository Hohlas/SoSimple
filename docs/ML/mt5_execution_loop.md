# MT5 Diagnostic Execution Loop

## Назначение

Набор Python и MQL5 модулей для диагностической проверки MT5 Strategy Tester:
подготовка `mt5_entry_signals.csv`, запуск batch-кандидатов, разбор `events.csv`
и проверка временного контракта исполнения.

Контур имеет статус `DIAGNOSTIC_ONLY`. Его результаты нельзя трактовать как
готовность к торговле, качество модели или новый PnL/PF вывод.

## Основные Модули

- `ML/baseline/mt5_signal_schema.py` задаёт executable schema source для signal
  CSV и event CSV.
- `ML/baseline/prepare_mt5_entry_source.py` переводит entry-quality rows в H1
  timing contract.
- `ML/baseline/export_mt5_entry_signals.py` экспортирует `entry_signals.csv` и
  `entry_signals.json`.
- `ML/baseline/run_mt5_batch.py` регенерирует сигналы, запускает MT5 tester и
  собирает `batch_summary.json`.
- `ML/baseline/mt5_execution_diagnostics.py` строит read-only diagnostics по
  event logs.
- `MT/MQL5/Include/lib_ML_Signal.mqh` читает signal CSV, проверяет timing guard
  и пишет event log.

## Timing Contract

Signal CSV:

```text
feature_time <= time < feature_available_time <= decision_time
```

Для текущего H1 diagnostic bridge:

```text
feature_time=signal_time
feature_available_time=signal_time+1h
decision_time=feature_available_time+latency_bars*h
time=decision_time-1h
```

Значение по умолчанию: `latency_bars=0`. В этом режиме `time=signal_time`, а
MQL5 эксперт с `bar=1` ставит заявку на первом тике следующего бара.

Event CSV для signal-linked rows:

```text
feature_time <= signal_time < feature_available_time <= decision_time <= execution_time
```

`TX_OPEN` и `TX_CLOSE` могут оставлять timing-поля пустыми: они связываются с
сигналом позже в Python reconciliation.

## Запуск

```bash
./.venv/bin/python -m ML.baseline.run_mt5_batch --phase signals
./.venv/bin/python -m ML.baseline.run_mt5_batch --phase all
./.venv/bin/python -m ML.baseline.mt5_execution_diagnostics \
  --phase events \
  --output-json ML/reports/mt5_execution_loop/diagnostics/event_anomaly_summary.json \
  --output-csv ML/reports/mt5_execution_loop/diagnostics/event_anomalies.csv
```

## Артефакты

- `ML/reports/mt5_execution_loop/batch/{run_id}/entry_signals.csv`
- `ML/reports/mt5_execution_loop/batch/{run_id}/entry_signals.json`
- `ML/reports/mt5_execution_loop/batch/{run_id}/events.csv`
- `ML/reports/mt5_execution_loop/batch/{run_id}/metrics.json`
- `ML/reports/mt5_execution_loop/batch/batch_summary.json`
- `ML/reports/mt5_execution_loop/diagnostics/event_anomaly_summary.json`
- `ML/reports/mt5_execution_loop/diagnostics/event_anomalies.csv`

## Ограничения

- `locked_test` не открывать для диагностических timing/rerun задач.
- `latency_bars>0` разрешён только как отдельный diagnostic export mode и не
  участвует в winner selection.
- `TIMING_VIOLATION` означает, что MQL5 увидел строку signal CSV с нарушением
  timing contract; такая строка не должна размещать ордер.
- Full batch зависит от MT5/Wine окружения. Если tester не пишет ожидаемые
  event-файлы, runtime verification получает статус `UNKNOWN`.
