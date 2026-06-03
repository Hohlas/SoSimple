## 10. Frozen test, OOS и walk-forward

### Цель

Проверить уже выбранного кандидата на данных, не использованных для выбора.

### Входы

- frozen checkpoint/rule;
- test split;
- split manifest;
- cost model;
- baseline test metrics, если они заранее допустимы.

### Пошаговые действия

1. Перед test проверить, что rule/checkpoint/exporter не менялись после validation.
2. Проверить, что test запускается с тем же execution contract, который был заморожен на validation.
3. Запустить test один раз для frozen candidate.
4. Считать модельные и торговые метрики.
5. Считать time slices: год, квартал или regime buckets.
6. Считать BUY/SELL отдельно.
7. Сравнить с baseline.
8. Если есть заранее заданный walk-forward: выполнить rolling/expanding evaluation без ретюнинга на test.
9. Сохранить predictions, trades, summary и limitations.

### Обязательные проверки

- Test не используется для подбора нового правила.
- Aggregate PF не скрывает отрицательные годы.
- Aggregate PF не скрывает слабую сторону BUY/SELL.
- SeqPF не используется как gate-критерий на test (допустим diagnostic-only).
- Walk-forward не подменяется повторным test.
- Кандидат проходит заранее заданные gates.
- Test verdict получает `INVALID`, если после freeze изменились `entry_price`, spread, fill policy, PnL convention или checkpoint/rule hash.
- Test на `spread=0` может иметь только `DIAGNOSTIC_ONLY`, если production execution имеет ненулевой spread.

### Критерии успешного завершения

- Есть frozen test report.
- Есть verdict: `reject`, `research_only`, `candidate`.
- Все слабые срезы перечислены.
- Известно, какие проверки нужны перед MT4/forward.

### Типовые ошибки

- Считать PF > 1 достаточным без учёта издержек и стабильности.
- Игнорировать два отрицательных года, если aggregate PF положительный.
- После слабого SELL результата объявлять BUY-only без нового validation cycle.
- Перезапускать test после каждой правки.
- Считать test валидным после смены execution convention без нового validation freeze.
- Выдавать zero-spread test PF за evidence production-качества.

### Ветвления

- Если test fail: reject или новый cycle, но не подстройка на test.
- Если aggregate pass, но side fail: оформить side-specific стратегию как новый кандидат.
- Если test pass, но нет forward: статус не выше `candidate`.

---
