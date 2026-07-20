# SoSimple Research Roadmap

## Контекст

Текущая рабочая точка проекта описана в [CONTEXT_HANDOFF.md](../../CONTEXT_HANDOFF.md).
Этот файл хранит только будущие направления, а не историю и не выводы
прошлых этапов. Завершённые исследования см. в [docs/reports/](../reports/).

---

## Ближайшие направления

### 1. Frozen probe для механики входа от `fractal0_price`

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

Oracle-preflight 2026-07-10 проверил механику входа через возврат цены к зоне
около `fractal0_price`:

- selected train rule: `entry_zone_edge_zone_0.5_lag_6_h3_spread_0.2`;
- `val_stop favorable_to_adverse_ratio = 1.2421118400499844`;
- `stress_favorable_to_adverse_ratio = 1.1895354754041108`;
- simple baseline ratio `= 1.061228066744197`, comparison `PASS`;
- side contract `PASS`;
- gate не прошёл из-за `active_years = 2` при требовании `3`.

Отчёт:

- [2026-07-10-fractal0-price-entry-mechanics.md](../reports/2026-07-10-fractal0-price-entry-mechanics.md)

**Задача:** если продолжать эту ветку, оформить отдельный frozen probe-plan.
План должен заранее зафиксировать rule, split-роли, горизонты, sample-size
gate, yearly/window contract и `allowed_max_verdict`.

**Ограничения:**

- текущий результат остаётся `diagnostic_only`;
- не открывать `locked_test`;
- не делать PnL/PF/trading claims;
- не тюнить правило по `val_stop` без нового плана.

Статус: потенциальный следующий research branch, но только через новый frozen
probe-plan.

### 2. H6 direction inside frozen mask

**Контекст:** narrow replication 2026-07-10 отвергла primary H3, но H6 в том
же фиксированном срезе выглядел заметно сильнее:

- `H6 val_eval_inside_mask median balanced_accuracy = 0.528590`;
- `5/5` seeds были выше `0.50`;
- H6 был заранее объявлен secondary robustness horizon, поэтому не может
  заменить H3 задним числом и не является кандидатом.

**Задача:** не потерять эту зацепку. Если основная ветка `fractal0_price`
entry mechanics не даст полезного потолка или будет закрыта, можно оформить
отдельный H6-first research plan.

**Обязательные условия будущего плана:**

- `origin_bias = horizon`, потому что идея выделена после просмотра H3/H6;
- статус не выше `research_hypothesis` до нового заранее замороженного probe;
- H6 должен быть primary horizon с самого начала, а не заменой H3;
- нельзя переиспользовать H3-fail как доказательство H6;
- нужен новый `next_probe_freeze`: признаки, модель, target, seeds, split,
  пороги и `allowed_max_verdict`;
- без `locked_test`, PnL/PF и trading-выводов.

Статус: отложенная исследовательская зацепка второй очереди.

### 3. Мульти-актив / мульти-таймфрейм валидация

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
