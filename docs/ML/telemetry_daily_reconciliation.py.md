# telemetry_daily_reconciliation.py

## Назначение

`ML/telemetry_daily_reconciliation.py` делает ежедневную сверку между ожидаемыми ML-сигналами и фактическими строками MT4 `MLP BUY/SELL/CLOSE`.

Инструмент нужен для demo-этапа, где важно быстро находить расхождения в цепочке:

- сигнал есть в `ml_signals.csv`, но сделка не открылась;
- сделка открылась не в ту сторону;
- MT4 открыл сделку без ожидаемого сигнала;
- открытая сделка не имеет закрытия в логе.

## Входные данные

- `ml_signals.csv` в формате `time;signal`.
- MT4 tester/runtime log со строками `MLP BUY`, `MLP SELL`, `MLP CLOSE BUY`, `MLP CLOSE SELL`.
- Опционально `export_metadata.json` от `API.export_take_skip_trailing_stop_v2_signals`.

## Запуск

```bash
python -m ML.telemetry_daily_reconciliation \
  --signals MT/tester/files/ml_signals.csv \
  --mt4-log MT/tester/logs/20260427.log \
  --export-metadata ML/reports/telemetry_frequency_v1/export_metadata.json \
  --output-dir ML/reports/telemetry_frequency_v1/daily/2026-04-27 \
  --label telemetry_frequency_v1 \
  --start-time "2025.01.01 00:00" \
  --end-time "2025.12.31 23:59"
```

Если есть критичные расхождения, CLI завершится с кодом `1`. Это позволяет использовать его в ежедневной автоматической проверке.

`--start-time` и `--end-time` необязательны, но для tester-сверок их нужно
задавать явно, если `ml_signals.csv` покрывает более широкий период, чем лог.

## Выходные файлы

- `signals_diff.csv` - сверка ожидаемых сигналов с фактическими открытиями.
- `trades_reconciliation.csv` - связь open/close по `ticket`.
- `summary.json` - машинно-читаемые счётчики.
- `summary.md` - краткая таблица.

## Что считается критичным

Критичными считаются:

- `missing_open` - ненулевой сигнал был, но сделки нет;
- `wrong_direction` - сделка есть, но направление не совпало;
- `unexpected_open` - сделка есть без ожидаемого сигнала.

`missing_close` считается отдельно: на demo это может быть нормой, если день закончился с открытой позицией.

## Ограничения

Парсер опирается на текущий формат `MLP`-строк из `MT/MQL4/Include/lib_ML_Signal.mqh`. Если формат логов меняется, нужно одновременно обновлять этот CLI и его тесты.

При чтении `ml_signals.csv` инструмент повторяет поведение MQL-библиотеки:
если есть несколько строк с одним `time`, оставляет последнюю.
