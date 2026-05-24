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

### Обязательные проверки

- MT4 читает именно проверенный файл.
- Exporter не меняет rule после test.
- Есть reconciliation report.
- Все missing trades объяснены или помечены blocker.
- Механический parity не объявляется forward profitability proof.

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

### Ветвления

- Если сигналы не совпадают: чинить export/runtime, не менять модель.
- Если сигналы совпадают, но PnL отличается: разбирать execution layer.
- Если open failures существенны: улучшать retry/slippage или снижать trading frequency.

---

