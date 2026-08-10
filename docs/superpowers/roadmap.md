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

### MT5 entry mechanics / trade-count frozen probe

Status: entry-mechanics probe plan pending. Fill-rate probe completed — fill rate
is NOT the primary cause of BATCH_NO_WINNER.

Current facts:

- Fill-rate probe rejected conversion rate as primary cause:
  OPEN_FAILED is 99.2% single-position policy, not broker no-fill.
- Median fill_rate=0.094, all 11 eligible candidates < 0.20.
- 12.5% residual unexplained (saved artifacts lack per-signal linkage).
- PF > 1.0 for all 11 eligible candidates; BS_p05 < 1.0 for all.
- `locked_test` remains unopened.
- Signal timing diagnostics layer добавлен (2026-08-09, `8c2d9ea`):
  `ML/reports/mt5_execution_loop/diagnostics/signal_timing_check.json` —
  `checked_signal_files=32, bad_files=0`, `contract=feature_time <= time <
  feature_available_time <= decision_time`, `latency_bars=0`. Канонический
  источник для цитирования timing-проверки.

Next action:

1. Create frozen probe plan targeting entry mechanics / trade-count
   consolidation:
   - Accept single-position policy as design constraint.
   - Focus on why PF > 1.0 coexists with BS_p05 < 1.0.
   - Use only saved batch artifacts for planning.
   - No MT5 rerun for planning step.
2. Allowed max verdict for any output: `DIAGNOSTIC_ONLY`.
3. No threshold, model, profile, side, horizon, entry/exit rule, stop,
   spread, cost or PnL convention may be selected from the sole output of
   this stage.
4. Optionally — use row-level event linkage breakdown to resolve 12.5% residual.

---

## NEXT_AFTER_MT5_HYGIENE

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

`docs/superpowers/plans/2026-08-03-mt5-per-magic-multiplexing.md`. 

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
