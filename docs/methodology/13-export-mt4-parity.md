## 13. Export, MT4 parity и reconciliation

### Цель

Доказать, что торговая платформа исполняет тот же сигнал, который был проверен в Python.

### Входы

- frozen export CSV;
- rule metadata;
- MT4 tester log;
- trade event-log;
- reconciliation tool.

### Пошаговые действия

1. Зафиксировать export format.
2. Зафиксировать hash экспортированного файла.
3. Проверить counts:
   - rows total;
   - nonzero rows;
   - unique time;
   - unique time+signal;
   - duplicate time;
   - opposite signals on same time.
4. Запустить MT4 tester на заданном периоде.
   - Стандартные строки MT4 tester вида `unmatched data error (...)` не считать
     ошибкой MQL/runtime и не использовать как blocker для проверки загрузки
     сигналов, открытия сделок и логики советника.
5. Сверить:
   - expected signals;
   - opened trades;
   - closed trades;
   - missing opens;
   - wrong direction;
   - critical mismatches;
   - close reasons.
6. В online/tester сверке сопоставлять по `signal_time + direction`, а не по ticket.
7. Логировать `OPEN_FAILED`, spread, slippage, Bid/Ask, commission, swap, balance/equity.
8. Исключить неполные края периода из строгого verdict.
9. Если offline backtest использовал M1/M5 для порядка TP/SL внутри H1,
   зафиксировать этот execution contract и сверить с MT4 tester/runtime:
   младший таймфрейм помогает offline-симулятору, но не заменяет tester parity.

### Обязательные проверки

- MT4 читает именно проверенный файл.
- Exporter не меняет rule после `locked_test`.
- Есть reconciliation report.
- Все missing trades объяснены или помечены blocker.
- Механический parity не объявляется forward profitability proof.
- Offline M1/M5 ordering не объявляется MT4 parity: tester/runtime всё равно
  должен подтвердить opened trades, close reasons и PnL.

### Критерии успешного завершения

- `critical_mismatch_count = 0` или расхождения классифицированы и приняты как non-blocking.
- Разница строк export и opened trades объяснена.
- Известен effect duplicate timestamps.
- Online/tester diagnostic не объявляется proof of profitability.

### Типовые ошибки

- Сравнивать число строк CSV с числом сделок без учёта duplicate time.
- Игнорировать границы tester interval.
- Не писать `OPEN_FAILED`.
- Смешивать mechanical parity и ML quality.
- Не очищать tester event-log перед новым прогоном.
- Считать совпадение offline M5 ordering достаточным доказательством MT4
  исполнения без tester/reconciliation.
- Принимать стандартный `unmatched data error` за ошибку советника. Это
  предупреждение качества tester-истории; MQL/runtime ошибки искать отдельно:
  `array out of range`, `Cannot open`, `OPEN_FAILED`, wrong direction,
  missing open, close mismatch.

### Ветвления

- Если сигналы не совпадают: чинить export/runtime, не менять модель.
- Если сигналы совпадают, но PnL отличается: разбирать execution layer.
- Если open failures существенны: улучшать retry/slippage или снижать trading frequency.

---
