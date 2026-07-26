# SoSimple Research Roadmap

## Назначение

Этот файл хранит очередь незавершённых исследовательских направлений и правила
переключения между ними. История и окончательные выводы живут в
[`docs/reports/`](../reports/), текущая точка остановки - в
[`CONTEXT_HANDOFF.md`](../../CONTEXT_HANDOFF.md).

Главное правило: в работе может быть только один `ACTIVE`-трек. Остальные
направления должны быть явно помечены как `BLOCKED`, `PARKED` или
`CLOSED_OR_SUPERSEDED`.

---

## Active Research Queue

### ACTIVE: `Fixed-11 candidate audit blocker resolution`

План:

- [`2026-07-25-fractal0-fixed11-candidate-audit.md`](plans/2026-07-25-fractal0-fixed11-candidate-audit.md)
- [report `2026-07-25-fractal0-fixed11-candidate-audit.md`](../reports/2026-07-25-fractal0-fixed11-candidate-audit.md)

Основание: `locked_test` был открыт 2026-07-24 для ровно 11 frozen normalized
rich-entry leaderboard rules по M5 execution contract. Все 11 правил прошли
PF/BS/sample-size gates на `locked_test`: PF range `2.6747-3.3667`, best rule
`rank01_time_only_linear_target_entry_ev_regression_top30`, verdict
`candidate_check_required`.

Текущий результат: аудит выполнен и вернул `candidate_audit_blocked`.
`candidate_audit_passed` не достигнут.

Блокеры:

- отсутствуют pre-open freeze/policy artifacts;
- `split_roles` не раскрывает границы, row count, `val_select`, `val_eval` и
  no-selection disclosure;
- `correlation_pruning_status=FOLLOW_UP_REQUIRED` не записан;
- low-N edge-year slices не помечены `DIAGNOSTIC_ONLY`;
- `movement_plus_time` score restoration раскрыт неполно.

Следующий шаг: только исправление воспроизводимости/disclosure audit-producing
artifacts без изменения frozen candidate rules и без нового выбора по
`locked_test`. Mutual-correlation pruning, MT4/tester parity, stress-spread
pass/fail и trading-status discussion запрещены до снятия блокеров.



### PARKED: остальные направления

Эти ветки сохраняются, но не исполняются параллельно с active-треком:

- `time_only` one-rule replication/probe;
- rich/fractal salvage probe;
- закрытие rich/fractal entry-quality ветки;
- regime filter reformulation;
- frozen probe для механики входа от `fractal0_price`;
- H6 direction inside frozen mask;
- multi-asset / multi-timeframe validation;
- central multi-profile inference service;
- bounded risk filters after system discovery.

## Five Follow-Up Directions

### 1. `time_only` one-rule replication/probe

Связанный черновик плана:

- [`2026-07-22-fractal0-rich-entry-shortlist-replication-probe.md`](plans/2026-07-22-fractal0-rich-entry-shortlist-replication-probe.md)

Важно: этот план был написан под старый rich shortlist и `locked_test`; его
нельзя запускать как есть. Использовать только как исходный материал для нового
frozen protocol после `time_only` robustness audit.

Цель: проверить ровно найденное правило без нового перебора:

```text
S2_fractal0_buffer_0_5_entry_floor_2 /
E3_open_pullback_1_0atr /
M0_no_mask /
X2_ml_opposite_any_p0_50 /
profile=time_only /
model=linear /
target=target_entry_ev_regression /
filter=top30 /
score_cutoff_on_val_select=-0.026718184259660646
```

Старое значение `-0.026392849103777025` superseded normalized audit cutoff.

Когда запускать:

- после `time_only` robustness audit, если устойчивость не провалена;
- только по заранее заданному split protocol;
- без подбора новых filters, targets, models или cutoff.

Что даст:

- ответит, переносится ли найденное календарное правило;
- поможет отделить реальный regime effect от результата широкого validation
  search.

Статус: `PARKED_BY_REGIME_REFORMULATION_REQUIRED`.

### 2. Rich/fractal salvage probe

Цель: проверить не абсолютную победу rich/fractal профилей, а их добавочную
пользу поверх `time_only`.

Минимальная постановка:

- `time_only`;
- один лучший structural профиль;
- один `time_only + structural_delta` профиль;
- один target;
- один model family;
- один-два top-фильтра максимум.

Когда запускать:

- только если появится новый frozen additive protocol; текущий normalized
  leaderboard не даёт достаточного non-time shortlist;
- не открывать `locked_test`;
- заранее зафиксировать additive gate.

Статус: `PARKED_OR_SUPERSEDED`.

### 3. Regime filter reformulation

Цель: переосмыслить `time_only` winner как режимный фильтр, а не как модель
качества конкретного фрактального входа.

Возможные проверки:

- торговать / не торговать в заданный временной режим;
- отдельные BUY/SELL режимы;
- режимы по времени, волатильности, плотности сигналов;
- сравнение с текущим `S2/E3/M0/X2 no-mask`.

Когда запускать:

- если normalized rerun снова подтверждает доминирование `time_only`;
- если `time_only` robustness audit не показывает явной концентрации на одном
  узком участке.

Статус: `PARKED_AFTER_LOCKED_TEST_CANDIDATE_CHECK`.

### 4. Close rich/fractal entry-quality branch

Цель: не тратить новые циклы на ветку, если она не даёт добавочной пользы.

Условие закрытия:

- normalized rerun не даёт rich/fractal winner;
- non-time shortlist не сохраняет убедительную добавочную пользу;
- `time_only` остаётся лучшим объяснением результата;
- нет заранее сформулированного нового target/model контракта, который меняет
  постановку.

Выход:

- финальная запись в report/wiki/changelog;
- rich/fractal entry-quality переводится в `CLOSED_OR_SUPERSEDED`;
- следующий `ACTIVE` выбирается из roadmap: `time_only`/regime filter или
  `fractal0_price` mechanics.

Статус: `PARKED_DECISION`.

---

## Existing Roadmap Branches

### Frozen probe для механики входа от `fractal0_price`

Контекст: direction внутри frozen movement-mask закрыт как ближайшая ветка.
Rich-features full-grid 2026-07-09 нашёл weak direction-effect
`nearest_k60 / H3 / entry_log_ratio / extra_trees`, но narrow seed-stability
репликация 2026-07-10 отвергла H3:

- `H3 val_eval_inside_mask median balanced_accuracy = 0.499080`;
- только `2/5` H3 seeds достигли `>= 0.52`;
- H6 был сильнее, но был заранее объявлен secondary robustness horizon и не
  может заменить H3 задним числом;
- H9 был пропущен preflight из-за отсутствующих target columns.

Oracle-preflight 2026-07-10 проверил механику входа через возврат цены к зоне
около `fractal0_price`:

- selected train rule: `entry_zone_edge_zone_0.5_lag_6_h3_spread_0.2`;
- `val_stop favorable_to_adverse_ratio = 1.2421118400499844`;
- `stress_favorable_to_adverse_ratio = 1.1895354754041108`;
- simple baseline ratio `= 1.061228066744197`, comparison `PASS`;
- side contract `PASS`;
- gate не прошёл из-за `active_years = 2` при требовании `3`.

Отчёты:

- [2026-07-09-direction-inside-frozen-movement-regime-rich-features.md](../reports/2026-07-09-direction-inside-frozen-movement-regime-rich-features.md)
- [2026-07-10-direction-inside-frozen-mask-narrow-replication.md](../reports/2026-07-10-direction-inside-frozen-mask-narrow-replication.md)
- [2026-07-10-fractal0-price-entry-mechanics.md](../reports/2026-07-10-fractal0-price-entry-mechanics.md)

Задача: если продолжать эту ветку, оформить отдельный frozen probe-plan.
План должен заранее зафиксировать rule, split-роли, горизонты, sample-size gate,
yearly/window contract и `allowed_max_verdict`.

Ограничения:

- текущий результат остаётся `diagnostic_only`;
- не открывать `locked_test`;
- не делать PnL/PF/trading claims;
- не тюнить правило по `val_stop` без нового плана.

Статус: `PARKED`.

### H6 direction inside frozen mask

Контекст: narrow replication 2026-07-10 отвергла primary H3, но H6 в том же
фиксированном срезе выглядел заметно сильнее:

- `H6 val_eval_inside_mask median balanced_accuracy = 0.528590`;
- `5/5` seeds были выше `0.50`;
- H6 был заранее объявлен secondary robustness horizon, поэтому не может
  заменить H3 задним числом и не является кандидатом.

Задача: не потерять эту зацепку. Если основная ветка `fractal0_price` entry
mechanics не даст полезного потолка или будет закрыта, можно оформить отдельный
H6-first research plan.

Обязательные условия будущего плана:

- `origin_bias = horizon`, потому что идея выделена после просмотра H3/H6;
- статус не выше `research_hypothesis` до нового заранее замороженного probe;
- H6 должен быть primary horizon с самого начала, а не заменой H3;
- нельзя переиспользовать H3-fail как доказательство H6;
- нужен новый `next_probe_freeze`: признаки, модель, target, seeds, split,
  пороги и `allowed_max_verdict`;
- без `locked_test`, PnL/PF и trading-выводов.

Статус: `PARKED_SECOND_QUEUE`.

### Multi-asset / multi-timeframe validation

Проверить fractal-концепт на другом инструменте или таймфрейме. Это полезно
только после того, как появится подтверждённая рабочая постановка сигнала или
чёткий повод проверять переносимость результата.

Важно: перенос на другой инструмент не заменяет защиту от переобучения. Сначала
нужны устойчивость внутри исходного инструмента, yearly checks, multi-seed и
чистый split.

Статус: `PARKED_UNTIL_CONFIRMED_MECHANIC`.

---

## Deferred Infrastructure

### Central multi-profile inference service

Контекст: текущий online-контур исторически опирался на отдельный watcher для
связки `Nero.csv -> ml_signals.csv`. Если снова появится несколько live-safe
runtime-профилей, ручной запуск отдельных процессов станет операционным риском.

Задача: заменить ручной single-profile watcher одним управляемым Python-сервисом,
который по конфигу обслуживает несколько runtime-профилей: входной `Nero*.csv`,
checkpoint, frozen rule, output `ml_signals*.csv`, state/log/metadata.

Выход: managed service без обязательного `tmux`, при сохранении текущего Python
training/inference pipeline и совместимости с Strategy Tester через CSV exports.

Design note:

- [2026-04-28-central-inference-service-design.md](specs/2026-04-28-central-inference-service-design.md)

Статус: `PARKED_INFRA`, есть дизайн, отчёт о реализации центрального сервиса не
найден.

### Risk filters only after system discovery

Контекст: фильтры поверх уже найденного сигнала часто сокращают сделки и
повышают риск подгонки.

Задача: применять risk filters только после того, как найден самостоятельный
источник прибыли или стабильный диагностический сигнал.

Выход: отдельный bounded benchmark для фильтра, где заранее ограничены число
правил и критерии успеха.

Статус: `PARKED_PRINCIPLE`, сейчас не является ближайшим исследовательским
шагом.

---

## Operating Rules

1. Один `ACTIVE`-трек за раз.
2. Не открывать `locked_test`, пока открыт upstream-вопрос контракта признаков,
   split protocol или состава shortlist.
3. Каждый завершённый `ACTIVE`-трек обязан создать report и decision memo:
   `continue`, `close`, `supersede`, `unblock`.
4. Новый план должен иметь поля:

```text
depends_on:
blocks:
supersedes:
exit_decisions:
locked_test_policy:
```

5. `roadmap.md` хранит очередь и статусы, но не заменяет отчёты.
6. `CONTEXT_HANDOFF.md` хранит ближайшую рабочую точку для следующего агента.
7. `docs/superpowers/plans/*.md` хранит исполнимые шаги только по одному
   направлению.
8. `docs/reports/*.md` остаются каноническим источником завершённых выводов.
9. `docs/DATA_FLOW.md` не использовать как список задач; это стабильная карта
   пайплайна.
