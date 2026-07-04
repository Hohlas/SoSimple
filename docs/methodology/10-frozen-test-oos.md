## 10. Locked test, OOS и walk-forward

### Цель

Проверить уже выбранного кандидата на исторических данных, не использованных для выбора.

### Входы

- frozen checkpoint/rule;
- locked test split;
- split manifest;
- cost model;
- baseline locked-test metrics, если они заранее допустимы.

### Пошаговые действия

1. Перед `locked_test` проверить, что rule/checkpoint/exporter не менялись после validation.
2. Проверить, что `locked_test` запускается с тем же execution contract, который был заморожен на validation.
3. Запустить `locked_test` один раз для `frozen_rule_for_locked_test`.
4. Считать модельные и торговые метрики.
5. Считать time slices: год, квартал или regime buckets.
6. Считать BUY/SELL отдельно.
7. Сравнить с baseline.
8. Если есть заранее заданный walk-forward: выполнить rolling/expanding evaluation без ретюнинга на `locked_test`.
9. Сохранить predictions, trades, summary и limitations.

### Обязательные проверки

- `locked_test` не используется для подбора нового правила.
- `locked_test` проходит `sample_size_gate` из [06-temporal-split.md](06-temporal-split.md) после всех фильтров.
- Execution contract содержит first executable price и latency proof; иначе verdict `INVALID` или `DIAGNOSTIC_ONLY`.
- Aggregate PF не скрывает отрицательные годы.
- Aggregate PF не скрывает слабую сторону BUY/SELL.
- SeqPF не используется как gate-критерий на `locked_test` (допустим diagnostic-only).
- Walk-forward не подменяется повторным `locked_test`.
- Кандидат проходит заранее заданные gates.
- Verdict получает `INVALID`, если после freeze изменились `entry_price`, first executable price, latency proof, spread, fill policy, PnL convention или checkpoint/rule hash.
- `locked_test` на `spread=0` может иметь только `DIAGNOSTIC_ONLY`, если production execution имеет ненулевой spread.

### Критерии успешного завершения

- Есть locked test report.
- Есть verdict: `reject`, `research_only`, `candidate`.
- Все слабые срезы перечислены.
- Известно, какие проверки нужны перед MT4/forward.

### Типовые ошибки

- Считать PF > 1 достаточным без учёта издержек и стабильности.
- Игнорировать два отрицательных года, если aggregate PF положительный.
- После слабого SELL результата объявлять BUY-only без нового validation cycle.
- Перезапускать `locked_test` после каждой правки.
- Считать `locked_test` валидным после смены execution convention без нового validation freeze.
- Выдавать zero-spread `locked_test` PF за evidence production-качества.

### Ветвления

- Если `locked_test` fail: reject или новый cycle, но не подстройка на `locked_test`.
- Если aggregate pass, но side fail: оформить side-specific стратегию как новый кандидат.
- Если `locked_test` pass, но нет forward: статус не выше `candidate`.

---
