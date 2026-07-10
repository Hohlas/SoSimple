# SoSimple Research Roadmap

## Контекст

Текущая рабочая точка проекта описана в [CONTEXT_HANDOFF.md](../../CONTEXT_HANDOFF.md).
Этот файл хранит только будущие направления, а не историю и не выводы
прошлых этапов. Завершённые исследования см. в [docs/reports/](../reports/).

---

## Ближайшие направления

### 1. Механика входа от `fractal0_price`

**Контекст:** direction внутри frozen movement-mask закрыт как ближайшая ветка.
Rich-features full-grid 2026-07-09 нашёл weak direction-effect
`nearest_k60 / H3 / entry_log_ratio / extra_trees`, но narrow seed-stability
репликация 2026-07-10 отвергла H3:

- `H3 val_eval_inside_mask median balanced_accuracy = 0.499080`;
- только `2/5` H3 seeds достигли `>= 0.52`;
- H6 был сильнее, но был заранее объявлен secondary robustness horizon и не
  может заменить H3 задним числом;
- H9 был пропущен preflight из-за отсутствующих target columns.

Завершённые отчёты:

- [2026-07-09-direction-inside-frozen-movement-regime-rich-features.md](../reports/2026-07-09-direction-inside-frozen-movement-regime-rich-features.md)
- [2026-07-10-direction-inside-frozen-mask-narrow-replication.md](../reports/2026-07-10-direction-inside-frozen-mask-narrow-replication.md)

Параллельно уже есть сильный признак, что исходный Up/Dn target связан с
областью вокруг `fractal0_price`, а не с немедленным входом по следующему open.
Отрицательный результат по `next open` не закрывает гипотезу уровня.

**Задача:** отдельно проверить механику входа, привязанную к `fractal0_price`:
возврат к уровню, ретест, лимитный вход около цены фрактала или вход после
касания/подтверждения.

**Что должно быть в будущем плане:**

- точный `decision_time`;
- точное правило entry eligibility;
- first executable price после доступности признаков;
- oracle-preflight потолка механики;
- новые targets от фактической точки входа;
- отдельный split/audit contract.

**Ограничения:**

- не смешивать с `next open` audit;
- не использовать старые цели от `fractal0_price` как готовую торговую
  разметку без проверки исполнимости;
- не открывать `locked_test` до frozen rule.

Статус: следующий самостоятельный research branch. Не смешивать с закрытым
direction-inside-mask планом.

### 2. Мульти-актив / мульти-таймфрейм валидация

Проверить fractal-концепт на другом инструменте или таймфрейме. Это полезно
только после того, как появится подтверждённая рабочая постановка сигнала или
чёткий повод проверять переносимость результата.

Важно: перенос на другой инструмент не заменяет защиту от переобучения. Сначала
нужны устойчивость внутри исходного инструмента, yearly checks, multi-seed и
чистый split.

Статус: отложено до появления подтверждённой исполнимой механики.

---

## Отложенные инфраструктурные направления

### Central multi-profile inference service

**Контекст:** текущий online-контур исторически опирался на отдельный watcher для
связки `Nero.csv -> ml_signals.csv`. Если снова появится несколько live-safe
runtime-профилей, ручной запуск отдельных процессов станет операционным риском.

**Задача:** заменить ручной single-profile watcher одним управляемым Python-сервисом,
который по конфигу обслуживает несколько runtime-профилей: входной `Nero*.csv`,
checkpoint, frozen rule, output `ml_signals*.csv`, state/log/metadata.

**Выход:** managed service без обязательного `tmux`, при сохранении текущего
Python training/inference pipeline и совместимости с Strategy Tester через CSV
exports.

Design note: [2026-04-28-central-inference-service-design.md](specs/2026-04-28-central-inference-service-design.md)

Статус: есть дизайн, отчёт о реализации центрального multi-profile сервиса не
найден.

### Risk filters only after system discovery

**Контекст:** фильтры поверх уже найденного сигнала часто сокращают сделки и
повышают риск подгонки.

**Задача:** применять риск-фильтры только после того, как найден самостоятельный
источник прибыли или стабильный диагностический сигнал.

**Выход:** отдельный bounded benchmark для фильтра, где заранее ограничены число
правил и критерии успеха.

Статус: отложенный принцип для будущих торговых кандидатов; сейчас не является
ближайшим исследовательским шагом.

---

## Где держать что

- `CONTEXT_HANDOFF.md` — текущая точка остановки, ближайший следующий шаг, риски.
- `docs/superpowers/roadmap.md` — короткая очередь незавершённых направлений между несколькими планами.
- `docs/superpowers/specs/*.md` — проектные решения до реализации.
- `docs/superpowers/plans/*.md` — детальные исполнимые планы по отдельным направлениям.
- `docs/reports/*.md` — канонические отчёты завершённых этапов.
- `docs/DATA_FLOW.md` — стабильная карта пайплайна, не рабочий список исследований.
