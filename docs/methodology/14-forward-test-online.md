## 14. Forward-test и online diagnostic

### Цель

Проверить candidate на новых данных после принятия решения.

### Входы

- frozen checkpoint/rule;
- новые raw или prediction данные после decision date;
- online event-log;
- monitoring metrics;
- risk limits.

### Пошаговые действия

1. Зафиксировать дату production decision.
2. Собирать forward data только после этой даты.
3. Не менять rule на forward window.
4. Считать metrics и time slices.
5. Разделять:
   - signal quality;
   - execution quality;
   - infrastructure health.
6. Контролировать delays, missed opens, requotes, spread spikes.
7. Если данных нет, выставить `watch/no_forward_data`.

### Обязательные проверки

- Forward window строго новее validation/locked_test.
- Forward проходит заранее заданный minimum N; если сделок/сигналов мало, verdict только `watch`.
- Нет ретюнинга на forward до verdict.
- Online preprocessing проходит leakage preflight.
- Diagnostic timeframe не подменяет production timeframe.
- Forward результат не смешивается с historical test.

### Критерии успешного завершения

- Есть verdict: `confirmed`, `watch`, `revisit`, `reject`.
- Есть next action на основе forward.
- Есть список execution issues отдельно от signal issues.

### Типовые ошибки

- Называть старый `locked_test` forward validation.
- Менять threshold после нескольких online сделок.
- Делать вывод о H1-модели по M5 diagnostic.
- Не отделять пропущенный вход от плохого сигнала.

### Ветвления

- Если forward нет: продолжать сбор, не повышать статус.
- Если N мало: `watch`, если это было задано заранее.
- Если risk limits нарушены: остановить торговлю и открыть audit.
- Если signal ok, execution fail: чинить execution layer.

---
