# SoSimple Research Roadmap

## Назначение

Этот файл хранит только будущие направления и правила переключения между ними.
История, результаты и численные выводы живут в `docs/reports/`. Текущая рабочая
точка живёт в `CONTEXT_HANDOFF.md`.

Главное правило: в работе может быть только один `ACTIVE`-трек. Остальные
направления должны быть явно помечены как `BLOCKED`, `PARKED` или
`CLOSED_OR_SUPERSEDED`.

---

## ACTIVE

### `MT4/tester parity for retained subset`

Цель: доказать, что MT4/tester исполняет те же сигналы и сделки, что Python.

Текущий статус: `ACTIVE`, `DIAGNOSTIC_ONLY`, `parity_in_progress`.

Актуальный отчёт:
`docs/reports/2026-07-27-fractal0-fixed11-retained-subset-mt4-parity.md`.

Актуальный анализ блокера:
`docs/reports/2026-07-29-fixed11-python-mt4-fill-chronology.md`.

Актуальный current-OHLC rerun:
`docs/reports/2026-07-29-fixed11-current-history-rerun.md`.

Актуальный Python chronology-fix rerun:
`docs/reports/2026-07-29-fixed11-python-h1-chronology-fix.md`.

Структурное сравнение old/current OHLC:
`ML/reports/fractal0_fixed11_current_history_comparison.json`.

Сравнение current-history и chronology-fix:
`ML/reports/fractal0_fixed11_h1_chronology_fix_comparison.json`.

Последний ручной tester-run проверял только `ML_RuleSlot=1` после правок
`MLClose`/stale handling:

- artifact: `MT/tester/files/ML_Trade_Events_SoSimple_1709200448.csv`;
- expert version: `260.338`;
- `ORDER_PLACED=1115`, `OPEN=717`, `CLOSE=717`, `OPEN_FAILED=404`;
- close/open-failed reasons: `MLClose=630`, `StaleFillAfterMLClose=66`,
  `StopLoss=15`, `Timeout=6`, `StalePendingAfterMLClose=324`,
  `LimitExpired=74`, `MarketAfterLimitPassedStopInvalid=2`,
  `OrderSendFailed=4`;
- closed profit sum: `87857.69`;
- verdict: `DIAGNOSTIC_ONLY`, because PnL is too good to treat as parity proof
  until fill mismatch is explained.

Python chronology-fix rerun 2026-07-29 устранил прежний внутри-H1 дефект:
`same_h1_ml_close` упал `4070 -> 0`, `hold_bars=0` упал `4495 -> 488`, все
новые сделки имеют `fill_execution_time_source=m5_touch`. Но после исправления
edge исчез: aggregate PnL R `4065.034595 -> -530.513260`, PF range
`2.820656-3.424707 -> 0.819373-0.938880`, `kept_candidates=0`. Это не
торговый вывод, а `DIAGNOSTIC_ONLY`, но старый fixed11 positive locked-test
contract больше нельзя считать валидным тем же frozen chain.

Следующий шаг:

1. Не экспортировать новые fixed11 MT4 signals как candidate.
2. Решить, закрывается ли current fixed11 retained-subset path как invalidated
   by chronology fix.
3. Если продолжать только инженерную parity-проверку: экспортировать corrected
   fixed11 signals/trades с diagnostic маркировкой и перезапустить MT4 slot 1
   reconciliation по `signal_time + direction`, open/fill/close reasons и
   missing opens.
4. Если edge считается уничтоженным: написать post-mortem и перейти к новой
   заранее ограниченной постановке без использования старого locked_test как
   источника выбора.

Запрещено до разблокировки:

- экспортировать все 11 rules как будто они независимы;
- чинить PnL через изменение правил;
- использовать свежий MT4 PnL как новый критерий отбора;
- считать parity доказательством прибыльности.

---

## BLOCKED Until Parity

### `Locked-test stress-spread disclosure`

Цель: показать чувствительность retained subset к ухудшению spread/costs.

Разблокируется только после MT4/tester parity. Stress-spread не должен менять winner и не
должен становиться новым search по spread.

### `Model card for retained subset`

Цель: оформить назначение, split, frozen rules, known risks, execution contract,
monitoring/retraining policy и stop conditions для retained subset.

Разблокируется только после pruning и parity/stress disclosure.

---

## PARKED Research Directions

### `time_only regime interpretation`

Цель: если retained subset окажется time-heavy, отдельно понять, является ли это
режимным фильтром, а не фрактальным сигналом.

Условия возврата:

- pruning показывает, что retained subset в основном `time_only`;
- parity/stress не закрывают ветку;
- есть заранее заданный план без нового выбора по `locked_test`.

Статус: `PARKED`.

### `rich/fractal additive salvage`

Цель: проверить только добавочную пользу rich/fractal признаков поверх
`time_only`, а не искать новый абсолютный winner.

Условия возврата:

- active fixed-11 ветка закрыта или retained subset требует объяснения
  non-time вклада;
- есть новый bounded protocol с заранее заданными profiles, target, model и
  gate;
- `locked_test` не используется.

Статус: `PARKED`.

### `fractal0_price entry mechanics frozen probe`

Цель: отдельно проверить механику входа от зоны `fractal0_price`.

Условия возврата:

- fixed-11 ветка закрыта или признана слишком time-heavy;
- есть новый frozen probe-plan с rule, split roles, horizons, sample-size gate,
  yearly/window contract и `allowed_max_verdict`;
- нет PnL/PF/trading claims без нового проверочного контура.

Статус: `PARKED`.

### `H6 direction inside frozen mask`

Цель: не потерять H6-first гипотезу, но проверять её только как новую заранее
заданную research-гипотезу.

Условия возврата:

- primary fixed-11 / `fractal0_price` направления не дают usable retained
  subset;
- H6 объявлен primary horizon до запуска;
- зафиксированы признаки, модель, target, seeds, split, пороги и
  `allowed_max_verdict`;
- без `locked_test`, PnL/PF и trading-выводов.

Статус: `PARKED_SECOND_QUEUE`.

### `multi-asset / multi-timeframe validation`

Цель: проверить переносимость только после появления retained system или
подтверждённой рабочей механики.

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

- есть retained subset, который реально надо экспортировать/исполнять;
- ручной запуск нескольких процессов становится операционным риском.

Статус: `PARKED_INFRA`.

### `bounded risk filters after system discovery`

Цель: применять risk filters только после того, как найден самостоятельный
источник прибыли или стабильный диагностический сигнал.

Условия возврата:

- retained system уже определён;
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
   `continue`, `close`, `supersede` или `unblock`.
8. `CONTEXT_HANDOFF.md` хранит ближайшую рабочую точку для следующего агента.
9. `docs/reports/*.md` остаются каноническим источником завершённых выводов.
10. `docs/DATA_FLOW.md` не использовать как список задач; это стабильная карта
    pipeline.
