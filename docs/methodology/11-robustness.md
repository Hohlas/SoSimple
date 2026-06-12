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
9. Оценить временную корреляцию сделок. Если соседние сделки принадлежат одному рыночному режиму — использовать block bootstrap (блоки по 10-20 последовательных сделок), stationary bootstrap или timestamp-cluster bootstrap вместо iid bootstrap для расчёта CI.
10. При использовании календарных признаков (hour, day-of-week sin/cos) проверить permutation importance. Если >30% важности модели приходится на календарные признаки — модель может быть календарным фильтром, а не фрактальным классификатором. Проверить устойчивость PF к сдвигу часового пояса.
11. Выполнить permutation test breach/fav: сравнить PF из реальных предсказаний с распределением PF при случайной перестановке breach-вероятностей (и/или fav-предсказаний) при сохранении структуры данных. Если winner был выбран через grid/search, permutation test должен повторять тот же процесс выбора или результат помечается diagnostic-only.

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
- Iid bootstrap на temporally correlated сделках — занижает истинную дисперсию PF, завышает BS_p05.
- Интерпретировать календарные признаки как фрактальный сигнал без проверки их доли в важности модели.

### Ветвления

- Если один side fail: новый BUY-only/SELL-filter cycle, не post-test tweak.
- Если один год fail: проверить regime, но не исключать год без заранее заданного правила.
- Если provider stable, но instruments fail: ограничить scope инструментом.

---
