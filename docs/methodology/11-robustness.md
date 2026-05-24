## 11. Устойчивость и robustness

### Цель

Понять, является ли результат устойчивым или держится на одном периоде, стороне, провайдере, seed или редких сделках.

### Входы

- frozen test trades;
- validation/test predictions;
- multi-seed runs;
- provider/instrument data, если применимо;
- portfolio/correlation context.

### Пошаговые действия

1. Проверить устойчивость по годам и кварталам.
2. Проверить BUY и SELL отдельно.
3. Проверить sequential simulation при ограничении числа позиций.
4. Проверить sensitivity к threshold, top-k, hold, SL/TP, costs.
5. Проверить multi-seed для training и rule selection.
6. Проверить provider drift на том же инструменте.
7. Только после provider drift проверять transfer на другие инструменты.
8. Проверить correlation с существующими системами, если кандидат идёт в portfolio.

### Обязательные проверки

- Устойчивость не доказывается одним aggregate PF.
- Transfer не заявляется без отдельного теста.
- Provider drift и instrument transfer не смешиваются.
- Side-specific failure не скрывается balance metric.
- SeqPF sequential simulation — только diagnostic для position-constraint анализа, не доказательство качества модели.

### Критерии успешного завершения

- Известно, какие режимы рынка кандидат переносит плохо.
- Есть решение: reject, narrow-scope, research-only или candidate.
- Есть список stress conditions, которые убивают edge.

### Типовые ошибки

- Считать одну удачную конфигурацию доказательством family stability.
- Игнорировать слабую SELL сторону.
- Считать provider-stable систему универсальной для других инструментов.
- Использовать старые до-audit transfer выводы для live-safe версии.

### Ветвления

- Если один side fail: новый BUY-only/SELL-filter cycle, не post-test tweak.
- Если один год fail: проверить regime, но не исключать год без заранее заданного правила.
- Если provider stable, но instruments fail: ограничить scope инструментом.

---

