# SoSimple Research Roadmap

## Назначение

Этот файл хранит только будущие направления и правила переключения между ними.
История, результаты и численные выводы живут в `docs/reports/`. Текущая рабочая
точка живёт в `CONTEXT_HANDOFF.md`.

Главное правило: в работе может быть только один `ACTIVE`-трек. Roadmap не
хранит закрытые этапы и ссылки на отчёты; история живёт в `CHANGELOG.md`,
`docs/reports/` и wiki.

---

## ACTIVE

### MT5 execution-loop prototype

Status: OnTradeTransaction lifecycle closed (DIAGNOSTIC_ONLY,
2026-07-31); Nero parity closed as PARITY_PARTIAL (structural PASS,
numeric FAIL — MT4 reference from older build). ERROR-4756 classification
not closed.
Next action:

1. Classify `ERROR-4756` send failures and `ERROR_SoSimple_*.csv`;
   link them to the 15 unexplained cancelled pendings + 9 ORDER_EXPIRED
   remainders from the 2026-07-31 reconciliation.
2. Reconcile event/deal rows before treating tester metrics as usable.
3. (Optional) Regenerate MT4 `Nero_XAUUSD.csv` with current build for
   numeric PARITY_PASS — separate plan.

---

## NEXT_AFTER_MT5_SINGLE_RULE

### MT5 batch selection for 20-50 candidates

Цель: после успешного single-rule MT5-контура проверять 20-50 заранее
отобранных кандидатов через MT5 tester, а не через Python trade PF/PnL.

Условия старта:

- single-rule MT5 execution loop пишет корректные entry/open/close events;
- `Nero.csv` producer parity доказан или явно ограничен диагностическим статусом;
- selection идёт на validation, не на opened locked_test;
- есть отдельный план с fixed rules, split roles, costs и stop conditions.

### `fractal0_price entry mechanics frozen probe`

Цель: отдельно проверить механику входа от зоны `fractal0_price` уже поверх
исправленного execution-контура.

Условия старта:

- MT5 single-rule контур пройден или его ограничения явно приняты;
- есть новый frozen probe-plan с rule, split roles, horizons, sample-size gate,
  yearly/window contract и `allowed_max_verdict`;
- нет PnL/PF/trading claims без MT5 tester/reconciliation.

### `H3/H6 live-safe direction`

Цель: проверить короткий горизонт направления только по признакам, доступным в
момент решения.

Условия старта:

- H3 или H6 выбран до запуска;
- feature contract и forbidden future columns зафиксированы до обучения;
- models/seeds/thresholds/split заранее ограничены;
- `locked_test` не используется для выбора.

---

## PARKED Research Directions

### `time_only regime interpretation`

Цель: отдельно понять, является ли устойчивый календарно-временной эффект
режимным фильтром, а не фрактальным сигналом.

Условия возврата:

- есть заранее заданный план без нового выбора по `locked_test`.
- исследование отделено от торгового verdict.

Статус: `PARKED`.

### `rich/fractal additive salvage`

Цель: проверить только добавочную пользу rich/fractal признаков поверх
`time_only`, а не искать новый абсолютный winner.

Условия возврата:

- есть новый bounded protocol с заранее заданными profiles, target, model и
  gate;
- `locked_test` не используется.

Статус: `PARKED`.

### `H6 direction inside frozen mask`

Цель: не потерять H6-first гипотезу, но проверять её только как новую заранее
заданную research-гипотезу.

Условия возврата:

- H6 объявлен primary horizon до запуска;
- зафиксированы признаки, модель, target, seeds, split, пороги и
  `allowed_max_verdict`;
- без `locked_test`, PnL/PF и trading-выводов.

Статус: `PARKED_SECOND_QUEUE`.

### `multi-asset / multi-timeframe validation`

Цель: проверить переносимость только после появления подтверждённой рабочей
механики.

Условия возврата:

- сначала есть устойчивость внутри XAUUSD;
- yearly/side/multi-seed/parity риски закрыты или явно приняты;
- перенос не используется как замена защите от переобучения.

Статус: `PARKED_UNTIL_CONFIRMED_MECHANIC`.

---

## PARKED Infrastructure

### `central multi-profile inference service`

Цель: заменить ручной single-profile watcher управляемым Python-сервисом для
нескольких runtime-профилей.

Условия возврата:

- есть набор правил или моделей, который реально надо экспортировать/исполнять;
- ручной запуск нескольких процессов становится операционным риском.

Статус: `PARKED_INFRA`.

### `bounded risk filters after system discovery`

Цель: применять risk filters только после того, как найден самостоятельный
источник прибыли или стабильный диагностический сигнал.

Условия возврата:

- рабочая механика уже определена;
- есть заранее ограниченный benchmark фильтра;
- фильтр не используется как скрытый новый search по `locked_test`.

Статус: `PARKED_PRINCIPLE`.

---

## Operating Rules

1. Один `ACTIVE`-трек за раз.
2. `roadmap.md` не хранит историю и выводы завершённых этапов.
3. Перед началом нового ACTIVE-трека создать отдельный план в
   `docs/superpowers/plans/`.
4. Новый план должен иметь поля:

```text
depends_on:
blocks:
supersedes:
exit_decisions:
locked_test_policy:
```

5. Не открывать новый `locked_test` без отдельного frozen/preflight protocol.
6. Не использовать `locked_test` для нового выбора winner, cutoffs, features,
   models, filters, entries, exits, stops, spread или PnL convention.
7. Каждый завершённый ACTIVE-трек обязан создать report и decision memo:
   `continue`, `close` или `unblock`.
8. `CONTEXT_HANDOFF.md` хранит ближайшую рабочую точку для следующего агента.
9. `docs/reports/*.md` остаются каноническим источником завершённых выводов.
10. `docs/DATA_FLOW.md` не использовать как список задач; это стабильная карта
    pipeline.
