# Entry Path v1 Live-Safe MT4 Parity

Дата: 2026-05-07

## Цель

Проверить, что MT4 исполняет тот же набор сигналов, который был подготовлен
для live-safe кандидата `entry_path_v1_live_safe + A @ 7.5%`.

Эта проверка отвечает на механический вопрос: совпадают ли Python export,
`ml_signals.csv` и реальные открытия сделок в MT4. Она не заменяет forward
торговлю.

## Входы

- Система: `entry_path_v1_live_safe + A @ 7.5%`.
- Экспорт: `ML.prepare_entry_path_mt4_parity`.
- Rule: `ML/reports/mt4_entry_path_v1_live_safe_parity/entry_path_v1_live_safe_a075_rule.json`.
- Metadata: `ML/reports/mt4_entry_path_v1_live_safe_parity/metadata.json`.
- MT4 signal CSV: `MT/tester/files/ml_signals.csv`.
- SHA256 signal CSV: `f213a8689bcac8fee0f7294bc56c5fc647e63cf58ab83321eda505d82d2af852`.

Сигнальный файл содержит `8911` строк и `29` ненулевых сигналов:

- `21` BUY;
- `8` SELL;
- диапазон строк: `2022.10.28 16:00` - `2026.04.22 12:00`.

## MT4 прогон

Проверенный прогон был запущен на `XAUUSD,H1` до `2025.12.31`.

MT4 подтвердил, что использовался исправленный эксперт:

- `OnInit() SoSimple.V260.332`;
- `ML_BackStopATR=999.00000000`;
- `ML_MaxPositions=1`;
- `ML_HoldBars=24`;
- `ML_TakeProfitATR=0`;
- `ML_UseScoreFilter=0`.

Итог отчета MT4:

| Метрика | Значение |
|---|---:|
| Чистая прибыль | 5217.70 |
| Profit Factor | 9.03 |
| Всего сделок | 26 |
| BUY / SELL | 18 / 8 |
| Прибыльные сделки | 20 / 26 |
| Максимальная просадка | 660.35 |
| Ошибки рассогласования графиков | 0 |

## Reconciliation

Команда:

```bash
./.venv/bin/python -m ML.telemetry_daily_reconciliation \
  --signals MT/tester/files/ml_signals.csv \
  --mt4-log MT/tester/logs/20260507.log \
  --output-dir ML/reports/mt4_entry_path_v1_live_safe_parity/reconciliation_2022_2025 \
  --label entry_path_v1_live_safe_a075_mt4_parity_2022_2025 \
  --export-metadata ML/reports/mt4_entry_path_v1_live_safe_parity/metadata.json \
  --start-time "2022.10.28 00:00" \
  --end-time "2025.12.31 23:59"
```

Итог:

| Метрика | Значение |
|---|---:|
| expected_signals | 26 |
| opened_trades | 26 |
| closed_trades | 26 |
| parsed_close_events | 52 |
| critical_mismatch_count | 0 |
| missing_close_count | 0 |

`parsed_close_events=52` не означает 52 сделки. MT4 пишет две строки закрытия
на одну сделку: решение закрыть позицию и подтверждение закрытия из истории.
Связанные закрытые сделки считаются в `closed_trades`.

`signals_diff.csv` показал, что все 26 ожидаемых сигналов за проверенный период
имеют статус `opened`.

## Ограничение проверки

Этот MT4-прогон не покрывает весь диапазон `ml_signals.csv`.

В файле есть еще 3 ненулевых сигнала после `2025.12.31`:

- `2026.01.21 22:00` BUY;
- `2026.03.24 05:00` BUY;
- `2026.03.27 00:00` BUY.

Значит, текущий результат закрывает MT4 parity для периода
`2022.10.28` - `2025.12.31`. Три оставшихся сигнала можно проверить отдельным
полным прогоном, но это больше не считается блокером: 26 совпавших сделок
достаточно, чтобы принять механическую цепочку как рабочую.

## Вывод

Для проверенного периода механическая цепочка подтверждена:

`Python rule -> ml_signals.csv -> MT4 open/close -> reconciliation`.

Критических расхождений нет: `critical_mismatch_count=0`.

Следующий шаг: перейти к online/forward diagnostic. Полный прогон до конца
`ml_signals.csv` остаётся optional closure, а не обязательным gate.
