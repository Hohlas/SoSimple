# MT5 Saved-Batch Fill-Rate Probe

> **Дата**: 2026-08-01
> **Статус**: Completed
> **Вердикт**: DIAGNOSTIC_ONLY
> **Цель**: разложить signal-to-trade conversion rate по ветвям отсева (позиционный запрет, настоящий broker no-fill, необъяснённый остаток) по сохранённым артефактам MT5 batch без нового выбора winner.
> **Related plan**: `docs/superpowers/plans/2026-08-01-mt5-saved-batch-fill-rate-probe.md`

## Stage Level

Search/post-mortem diagnostic stage. This report does not create a candidate and cannot raise verdict above `DIAGNOSTIC_ONLY`.

## research-first disclosure

- **lifecycle_status**: DIAGNOSTIC_ONLY
- **origin_bias**: post-mortem after `BATCH_NO_WINNER`
- **research_priority**: conversion_position_policy_dominant (with residual >= 10%)
- **current_search_budget**: 0 new model/search configurations; 3 diagnostic checks over saved batch artifacts (1 fill-rate probe over 32 candidates + 1 Spearman correlation matrix + 1 fixed decision rule check; N=34 total items)
- **cumulative_search_budget**: inherited from 2026-07-31 batch and 2026-08-01 MT5 diagnostics
- **continuation_budget**: 0 новых probe-партий; текущая диагностика — последняя перед пересмотром ветки
- **next_probe_freeze**: trade-count and entry mechanics, not fill rate
- **allowed_max_verdict**: DIAGNOSTIC_ONLY
- **forbidden_interpretations**: profitable, ready, live-ready, tradable, new winner, model-quality proof

## Context

После post-batch диагностики (verdict `BATCH_NO_WINNER`) потребовалось понять, является ли низкая конверсия сигналов в сделки главной причиной неудачи или проблема лежит в другом. Текущий `fill_rate` определён как `trades_count / active_signal_rows` и не является "broker fill rate" в классическом понимании.

Предыдущие отчёты:
- `docs/reports/2026-08-01-mt5-diagnostic-timing-contract.md`: timing contract rerun, `n_valid=32`, `n_eligible=11`.
- `docs/reports/2026-08-01-mt5-execution-hygiene-postbatch.md`: top candidate `time_plus_atr_extra_trees_small_12h_thr0.2` имеет PF 1.2323, BS_p05 0.887, fill rate 0.0944.

## Methodology

Применены обязательные проверки из:
- `A5-post-mortem-diagnostics.md`: decompose result; keep output `DIAGNOSTIC_ONLY`.
- `13b-mt5-execution-parity.md`: event discrepancies classified; tester result is not model quality.
- `11-robustness.md`: side-specific weakness не скрыта.
- `12-backtest-costs.md`: fill/no-fill политики, но не производственная cost model.
- `16-reporting-audit.md`: разделение фактов и гипотез.

## What Was Done

**Task 1**: Добавлены функции `count_event_names`, `_numeric_summary`, `summarize_candidate_fill_rate`, `build_fill_rate_diagnostics` в `ML/baseline/mt5_execution_diagnostics.py`. Написаны failing-тесты, затем реализация.

**Task 2**: Добавлен CLI phase `fill-rate`. Сгенерированы артефакты:
```bash
./.venv/bin/python -m ML.baseline.mt5_execution_diagnostics \
  --phase fill-rate \
  --output-json ML/reports/mt5_execution_loop/diagnostics/fill_rate_diagnostics.json \
  --output-csv ML/reports/mt5_execution_loop/diagnostics/fill_rate_candidates.csv
```

**Task 3**: Анализ decomposition: Spearman correlations, OPEN_FAILED reason buckets, residual reconciliation, decision rule.

## Verification

```bash
./.venv/bin/python -m pytest tests/test_mt5_execution_diagnostics.py -q
```
Результат: `24 passed in 0.37s`. Дополнительно все числовые утверждения отчёта пересчитаны по артефактам (CSV + `batch_summary.json`) в `docs/audit/2026-08-02-saved-batch-fill-rate-probe.md`.

## Artifact Hashes

- `ML/reports/mt5_execution_loop/diagnostics/fill_rate_diagnostics.json`:
  `f97ba0d5662f1ab01fffea38cc3b460bf7b9fcba5d7121b1945a8492a24cd40e`
- `ML/reports/mt5_execution_loop/diagnostics/fill_rate_candidates.csv` (gitignored):
  `7583bd611dc613647ff5ce26f6eb50e9086cdd3e6ebaf795b737417553a5c59f`

## Multiple Testing Context

- `current_search_budget` и `cumulative_search_budget` указаны в `research-first disclosure` выше; новых model/search конфигураций не создано — только диагностика сохранённых артефактов.

## Changed Files

- `ML/baseline/mt5_execution_diagnostics.py` — добавлены `count_event_names`, `_numeric_summary`, `summarize_candidate_fill_rate`, `build_fill_rate_diagnostics`, CLI-фаза `fill-rate`.
- `tests/test_mt5_execution_diagnostics.py` — добавлены `test_summarize_candidate_fill_rate_uses_entry_signal_denominator`, `test_build_fill_rate_diagnostics_preserves_no_winner_and_no_selection`, `test_cli_phase_choices_include_fill_rate`.
- `ML/reports/mt5_execution_loop/diagnostics/fill_rate_diagnostics.json` — новый артефакт.
- `ML/reports/mt5_execution_loop/diagnostics/fill_rate_candidates.csv` — новый артефакт (.gitignore'd).

## Structured Artifact Cross-Check

Ключевые числа из `fill_rate_diagnostics.json`:
- `candidate_count`: 32
- `verdict`: `BATCH_NO_WINNER`
- `n_eligible`: 11, `n_diagnostic_only`: 16
- `total_active_signal_rows`: 28,808
- `total_trades`: 2,508
- `total_open_failed`: 22,767
- `total_order_expired`: 67
- `fill_rate_by_status.eligible_top.count`: 11
- `fill_rate_by_status.eligible_top.median`: 0.0943
- `fill_rate_by_status.eligible_top.low_fill_rate_count_lt_0_20`: 11 (все элигибль-кандидаты)
- `fill_rate_by_status.diagnostic_only.count`: 21 (все не-элигибль кандидаты; из них 16 — `DIAGNOSTIC_ONLY`, 5 — не прошли gates, вычислено как 21 − 16; пометка `FAIL` в артефактах отсутствует)

Из `fill_rate_candidates.csv` (32 строки, `;`-разделитель):
- Элигибль-кандидаты: 11, все с `fill_rate` < 0.20.
- `position_or_pending_order_exists` = 99.19% от OPEN_FAILED для элигибль-группы.
- Парный регрессионный остаток(`active_signal_rows - ORDER_PLACED - OPEN_FAILED`) для элигибль = 1,874 (12.53% от `active_signal_rows` по суммам; по правилу плана медиана/медиана — 14.3%).
- `pending_order_not_found_after_order_placed` = 94 события из 11,616 (0.81%) для элигибль-группы.
- `ORDER_EXPIRED` = 31 событие для элигибль-группы (по всем 32 кандидатам — 67).

Spearman rank correlations (32 строки):
```
fill_rate ⇔ trades_count:           0.2275 (слабая положительная)
fill_rate ⇔ profit_factor:        -0.4575 (отрицательная)
fill_rate ⇔ open_failed_count:    -0.6364 (умеренно отрицательная)
trades_count ⇔ open_failed_count:  0.5694 (положительная)
trades_count ⇔ order_expired:      0.6469 (положительная)
```

## Results

1. **Position-policy dominates**: `position_or_pending_order_exists` составляет 99.2% от OPEN_FAILED для элигибльных кандидатов. Для каждого из 11 элигибль-кандидатов count `position_or_pending_order_exists` много больше, чем `pending_order_not_found_after_order_placed` + `ORDER_EXPIRED`. Advisor single-position, поэтому это ожидаемо.

2. **Broker no-fill вклада нет**: `pending_order_not_found_after_order_placed` (94 события) и `ORDER_EXPIRED` (31 событие) практически отсутствуют.

3. **Significant residual**: `active_signal_rows - ORDER_PLACED - OPEN_FAILED` идентифицирует 12.53% от сигналов элигибль-кандидатов (по суммам; по правилу плана медиана/медиана — 14.3%), которые не были учтены ни как выставленные, ни как невыставленные. Этот остаток может возникать из-за внутренних duplicate сигналов, `ML_CLOSE` pre-emptions или `TIMING_VIOLATION`, но сохранённые артефакты не позволяют его полностью декомпозировать.

4. **Fill rate association**: Spearman correlation между `fill_rate` и `profit_factor` отрицательный (−0.4575). Это кросс-секционная ассоциация между разными кандидатами, а не причинный эффект снятия ограничения внутри одного кандидата; на её основе нельзя утверждать, что устранение позиционного ограничения автоматически улучшит или ухудшит PF. `fill_rate` и `trades_count` слабо положительно ассоциированы (0.2275) — это ожидаемо.

5. **Side-specific breakdown**: по каждой стороне отдельно (batch_summary `trades_buy`/`trades_sell` vs CSV `buy_signal_rows`/`sell_signal_rows`, элигибль-11): медианный fill rate BUY = 0.1092, SELL = 0.0827; суммарно BUY = 0.1083, SELL = 0.0833. У 10 из 11 элигибль-кандидатов fill BUY > fill SELL. Разрыв между сторонами (≈26% относительно SELL) ниже, чем масштаб эффекта позиционной политики (99.19% от OPEN_FAILED), поэтому вывод о доминировании position policy не меняется, но асимметрия BUY/SELL фиксируется как особенность.

## Conclusions

**Decision**: `conversion_position_policy_dominant` (per plan rule: >= 80% of OPEN_FAILED, median fill < 0.20, every candidate policy > non-policy). Дополнительно `conversion_residual_dominant` действует как вторичный факт: по правилу плана (медиана/медиана) остаток = 14.3% >= 10% (по суммам — 12.53%).

**Fill rate hypothesis rejected**: Всякий вывод о "broker fill rate" как доминирующей проблеме отвергнут. Низкий сигнал-в-сделку conversion rate ОПРЕДЕЛЁН single-position policy советника, и попытка изменить политику (multi-position или сокращённый горизонт) не может быть основана только на fill rate данных этого проба.

**Next probe direction**: Исследовать trade-count dynamics как причину `BATCH_NO_WINNER`. Только у 2 из 11 элигибль-кандидатов PF > 1.0 (1.2323, 1.1655); у 9 из 11 PF <= 1.0 (минимум 0.5412), и все 11 провалили BS_p05 >= 1.0. Вопрос «почему прибыльное, но нестабильное» применим лишь к 2 кандидатам, а доминирующая картина — убыточность; шум с малым числом сделок как причина `BATCH_NO_WINNER` остаётся гипотезой, требующей проверки trade-count и entry mechanics. План должен покрыть entry mechanics и batch-size для следующего frozen probe.

**Recommendation**: Proceed with `fractal0_price entry mechanics frozen probe` (pre-existing in NEXT_AFTER_MT5_HYGIENE roadmap), но с revised priority на trade-count consolidation, а не on fill-rate decomposition.

## Limitations / Open Questions

- Нет по-сигнального ключа, связывающего каждый активный сигнал с `ORDER_PLACED`, `OPEN_FAILED`, `ORDER_EXPIRED`, `OPEN` или `CLOSE`.
- Связь между событиями и ошибками журнала остаётся `UNKNOWN`.
- 12.53% residual (`active_signal_rows - ORDER_PLACED - OPEN_FAILED`; по правилу медиана/медиана — 14.3%) не может быть полностью объяснён сохранёнными артефактами. Возможные причины: дублирующие сигналы одинакового времени (`several active signals per bar`), `ML_CLOSE` pre-emptions, `TIMING_VIOLATION`. Рекомендуем следующую probe: row-level signal-parity для полной развязки.
- `metrics.json` присутствовал у всех 32 кандидатов и в `_smoke` (итого 33 файла); `unknowns.missing_per_run_inputs` в `fill_rate_diagnostics.json` пуст, поэтому этот факт не является ограничением.
- `BS_p05` не декодируется в CSV-колонку: колонка `bs_p05` пуста у всех 32 строк, включая 11 элигибль-строк, т.к. значение живёт в `winners_ranked` (не в `table`) в `batch_summary.json`. Значения BS_p05 для элигибль-кандидатов берутся из `winners_ranked` / post-batch отчёта; на вывод это не влияет.
- Стресс-тест стоимости не был выполнен и не может быть выведен из fill rate.
- Spearman-корреляции и residual рассчитаны внешним кодом (ad-hoc), а не в `build_fill_rate_diagnostics`; команда `--phase fill-rate` их не воспроизводит. Воспроизводимость: перечисленные в `Artifact Hashes` файлы + пересчёт в `docs/audit/2026-08-02-saved-batch-fill-rate-probe.md`.
- По годам breakdown не выполнен: в `batch_summary.json` есть `pf_by_year`/`gross_profit_by_year`, но нет разбивки `active_signal_rows`/`trades` по годам, поэтому fill rate по годам (требование A5-78) рассчитать нельзя; фиксируется как gap для следующей probe.

## Split Disclosure

Была использована только сохранённая batch: XAUUSD H1 2021-01-04..2022-12-02. `locked_test` не открывался; holdout/locked_test не использовался для выбора model, threshold, feature, entry/exit, stop, spread, cost или PnL-конвенции (подтверждение по `16-reporting-audit.md`).

## Forbidden Interpretations

Никто не должен использовать этот отчёт как:
- новый winner selection;их winner уже `BATCH_NO_WINNER` и не изменён;
- сигнал, что конверсию можно исправить изменением параметра (позиция-метрика это structural constraint);
- evidence что любой кандидат tradeable.

## Next Step

Выбрать следующую диагностику.

1. **Primary**: entry mechanics / trade-count probe — определить, почему у 2 из 11 элигибль-кандидатов PF > 1.0 при BS_p05 < 1.0, и подтвердить/опровергнуть гипотезу шума при малом числе сделок. Открыть новый frozen probe plan с замороженной single-position политикой (принимая её как design-constraint).
2. **Secondary**: После (или параллельно) — row-level candidate-signal linkage + по-сигнальный exit quality аудит из `events.csv`.

## Related Materials

- `docs/reports/2026-08-01-mt5-diagnostic-timing-contract.md`
- `docs/reports/2026-08-01-mt5-execution-hygiene-postbatch.md`
- `ML/reports/mt5_execution_loop/diagnostics/fill_rate_diagnostics.json`
- `ML/reports/mt5_execution_loop/diagnostics/fill_rate_candidates.csv`