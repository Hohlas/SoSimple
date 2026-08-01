# MT5 Batch Selection: 32 Candidates

**Date:** 2026-07-31
**Status:** DIAGNOSTIC_ONLY
**Verdict:** BATCH_NO_WINNER
**Plan:** `docs/superpowers/plans/2026-07-31-mt5-batch-selection.md`

## Research-first disclosure

- **lifecycle_status:** DIAGNOSTIC_ONLY
- **origin_bias:** movement-filter shortlist (64 → 32), entry/label/outcome-only; no direction, no entry-exit grid, no fixed11
- **research_priority:** подтверждённая, но низкая: модели дают сигнал на val_select, но не стабильный PF в MT5 tester
- **current_search_budget:** 32 MT5 tester прогона (validation 2021.01–2022.12)
- **cumulative_search_budget:** 64 benchmark → 32 shortlist → 32 tester → 11 eligible
- **next_probe_freeze:** cost model по 12-backtest-costs.md, расширение периода или отдельный val-eval split
- **allowed_max_verdict:** DIAGNOSTIC_ONLY (gross PF без swap/commission, combined split roles, нет locked_test, timing contract diagnostic)
- **forbidden_interpretations:** «прибыльно», «готово», «можно запускать», «live-ready», «tradable», «movement-filter модели не работают», «statistically significant PF > 1.0»

## Context

32 предобранных кандидата (movement-filter конфигурации) прогнаны через MT5
Strategy Tester на validation-периоде 2021.01.04–2022.12.02. Цель: определить
победителя по заранее заданным гейтам с multiple-testing correction.

Шортлист: `ML/reports/entry_based_movement_filter_candidates.csv`.
Все кандидаты `selection_eligible=True`, `yearly_check_pass=True`. Критерий
шортлиста — не Spearman, а movement-lift гейты: годовой `movement_lift > 1.0`
и `selected_p80 > skipped_p80` на каждом годе (`passes_yearly_lift_gate`),
`yearly_lift_pass_rate >= 0.60` на val_eval (ml/baseline/
benchmark_entry_based_movement_filter.py:262-268). Поэтому 24h-конфигурация
`simple_combined` со Spearman val_select 0.270 проходит шортлист: её
movement_lift 1.33–1.51 (> 1.0) удовлетворяет гейту, несмотря на слабый
ранговый коэффициент. `selection_eligible` по умолчанию `True` (нет порога по
Spearman); фильтрация происходит по movement-lift, а не по корреляции с
таргетом.

## Methodology

- **Tester:** MT5 Strategy Tester, Model 1 (1-minute OHLC), XAUUSD H1
- **Период:** 2021.01.04–2022.12.02 (фактический диапазон сигналов
  2021.01.05–2022.11.25; пересечение movement scores и order mechanics)
- **Метрика:** Profit Factor (gross, без swap/commission)
- **Статистика:** Block bootstrap (блоки 15 сделок, 2000 итераций, seed=42)
- **Коррекция:** Holm-Bonferroni (alpha=0.05, N=11 eligible)
- **Гейты:** trades>=100, >=30/side, UNEXPLAINED=0, BS_p05>1.0, Holm reject,
  profit concentration (effective_profit_years>=1.5)

### Tester metadata

Зафиксировано по смежным прогонам (single-rule diagnostic 2026-07-30,
lifecycle 2026-07-31); batch-прогон использует тот же терминал/счёт/INI.
Собственных batch metadata `batch_summary.json` не содержит (проверено:
`jq '.metadata // .tester_metadata // .config // empty' batch_summary.json`
возвращает пустой результат).

- Terminal: MetaTrader 5 под Wine 9.0
- Agent build: 6061 — подтверждён смежным lifecycle artifact
  (`docs/reports/2026-07-31-mt5-ontradetransaction-lifecycle.md:39`),
  не batch artifact
- Server build: 6074 — наблюдение оператора, artifact отсутствует
- Broker/server: MetaQuotes-Demo — observation only, no artifact
- Account mode: demo hedging — observation only, no artifact
- Deposit: 10000 USD; Leverage: 1:500 — из INI
- Spread mode: не указан в INI (`SpreadMode` отсутствует) — значение
  терминала по умолчанию; без явного spread mode post-hoc cost-adjusment
  невозможен
- Contract spec (XAUUSD tick value/size, contract size): не зафиксирован
  артефактом в данном прогоне
- Batch INI, compile log, terminal/agent log: не сохранены как batch
  artifacts

Примечание: metadata частично не покрыта `batch_summary.json` — см. Limitations.

### Cumulative search budget

Полный lineage отбора (раскрыт для прозрачности коррекции на множественное
тестирование):

1. Benchmark оценил 64 конфигурации
   (2 профиля × 2 модели × 4 горизонта × 4 порога).
2. 32 прошли фильтры `selection_eligible` + `yearly_check_pass` (шортлист).
3. 11 прошли sample_size_gate (trades>=100 И >=30/side в MT5 tester).
4. Holm-Bonferroni применён к N=11 (фактическое число eligible), alpha=0.05.
   Из 32 прогонов 21 (16 diagnostic-only + 5 insufficient) исключены
   заранее заданным sample-size gate до коррекции; они не участвовали
   в winner family и не могут использоваться для выбора без нового плана
   коррекции.

Порядок «gate trades>=100 ДО коррекции» заранее зафиксирован в плане
(`docs/superpowers/plans/2026-07-31-mt5-batch-selection.md:104-108`) и не
подгонялся по результату. Коррекция делалась на N=11, а не на 32/64: critics
того, что кандидаты с N<100 исключены до коррекции — заранее заданный
sample_size_gate, а не post-hoc отбор.

### Cost model status

Canonical-spread gate из `docs/methodology/12-backtest-costs.md:72` НЕ
активирован. PF считается gross (без swap/commission, в TX-строках обе = 0).
Spread mode INI не указан, поэтому post-hoc cost-adjusment без дополнительных
предположений невозможен. Статус ограничен DIAGNOSTIC_ONLY до применения cost
model (Next Steps п. 3).

## Results

| # | run_id | PF | N | WR | DD | Buy | Sell | BS_p05 | PC |
|---|--------|-----|---|------|------|-----|------|--------|----|
| 1 | time_plus_atr_extra_trees_small_12h_thr0.2 | 1.232 | 102 | 0.412 | 760 | 55 | 47 | 0.887 | + |
| 2 | simple_combined_extra_trees_small_12h_thr0.2 | 1.165 | 101 | 0.416 | 1008 | 56 | 45 | 0.728 | − |
| 3 | simple_combined_extra_trees_small_3h_thr0.3 | 0.855 | 143 | 0.364 | 1434 | 70 | 73 | 0.696 | + |
| 4 | simple_combined_extra_trees_small_6h_thr0.3 | 0.963 | 151 | 0.384 | 1345 | 93 | 58 | 0.695 | + |
| 5 | simple_combined_extra_trees_small_6h_thr0.2 | 0.990 | 123 | 0.390 | 1157 | 69 | 54 | 0.693 | + |

Полная таблица: `ML/reports/mt5_execution_loop/batch/batch_summary.json`

Колонка `PC` — profit concentration gate (`effective_profit_years >= 1.5`):
`+` pass, `−` fail. Источник: `batch_summary.json`
`winners_ranked[*].profit_concentration_pass`.

### Gate failures

Все 11 eligible-кандидатов провалили гейт **BS_p05 > 1.0**: нижняя граница
block bootstrap CI для PF ниже 1.0 у всех. Ни один кандидат не имеет
статистически значимого свидетельства PF > 1.0.

Дополнительно: 1 из 11 (`simple_combined_extra_trees_small_12h_thr0.2`,
позиция #2 таблицы) провалил profit concentration
(`effective_profit_years < 1.5`, `profit_concentration_pass=False`). Остальные
10 провалили только BS_p05.

Holm-Bonferroni: 0 отклонённых гипотез (ни один p-value не прошёл коррекцию).

### Summary statistics

- Valid (UNEXPLAINED=0): 32/32
- Eligible (trades>=100, >=30/side): 11
- Diagnostic only (30<=trades<100): 16
- Insufficient (<30 trades): 5

## Reconciliation

Все 32 прогона: UNEXPLAINED=0 (CLOSED_TX reconciled). Events уникальны
(32 различных хеша).

## Limitations

1. **Combined split roles:** validation период используется и для select, и
   для eval. Потолок статуса — RESEARCH_ONLY. Однако фактический статус
   понижен до DIAGNOSTIC_ONLY по более строгому blocker: gross PF без
   swap/commission, неполная tester metadata и timing contract diagnostic
   (см. Research-first disclosure).
2. **Gross PF:** без swap и commission (в TX-строках оба = 0). Canonical-spread
   gate из `docs/methodology/12-backtest-costs.md` не активирован (см.
   Methodology → Cost model status). Полный список отсутствующих cost
   assumptions: commission, slippage, swap, latency (row materialization,
   polling, inference/export, order-send), missed opens,
   requote/open failure, position limits. Spread mode не указан в INI,
   canonical spread gate не задействован — post-hoc cost-adjusment невозможен
   без дополнительных предположений. Gross PF нельзя сравнивать с будущим
   net PF как один и тот же frozen result.
3. **Период:** пересечение movement scores и order mechanics. Фактический
   диапазон сигналов 2021.01.05–2022.11.25 (~1080 сигналов у top-кандидата).
   Число H1-баров пересечения: `run_mt5_batch.py:50-55` фильтрует
   период 2021-01-04 — 2022-12-02 из movement scores и EQ scores;
   точное число строк/баров пересечения можно получить командой
   по `val_select` score frame и EQ CSV (см. `run_mt5_batch.py:50-55`).
   Прежняя оценка «~4947 баров» из плана не воспроизводится по артефактам
   и не является зафиксированным ограничением данного отчёта.
4. **Fill rate:** значительная часть сигналов не исполняется (OPEN_FAILED).
   Реальное число сделок существенно меньше числа сигналов.
5. **LiveUpdate (гипотеза, не подтверждённая артефактом):** по наблюдению
   оператора, после ~14-го кандидата терминал мог попытаться автообновиться;
   оставшиеся прогоны перезапускались после блокировки liveupdate-каталога.
   Событие не зафиксировано в `batch_summary.json` и не подкреплено логом
   терминала; нет артефакта `ls/stat` заблокированного каталога. Влияние на
   результаты 15–32 не подтверждено. Resume-by-skip (при наличии валидного
   `metrics.json` прогон пропускается) обеспечивает независимость
   перезапусков.
6. **Timing contract:** bridge копирует signal_time во все временные поля
   (diagnostic). Не является доказательством leakage-free.
7. **Tester metadata неполна:** build/broker/spread mode/contract spec частично
   не покрыты в `batch_summary.json` (см. Methodology → Tester metadata), что
   не соответствует `docs/methodology/13b-mt5-execution-parity.md:169-177`.

## Artifacts

- Entry signals: `ML/reports/mt5_execution_loop/batch/{run_id}/entry_signals.csv`
- Events: `ML/reports/mt5_execution_loop/batch/{run_id}/events.csv`
- Metrics: `ML/reports/mt5_execution_loop/batch/{run_id}/metrics.json`
- Summary: `ML/reports/mt5_execution_loop/batch/batch_summary.json`
- Script: `ML/baseline/run_mt5_batch.py` (все фазы: export, loop, aggregate)
- Compile log: `/tmp/sosimple_mt5_compile.log` (не сохранён в repo; verify: `iconv -f UTF-16LE -t UTF-8 /tmp/sosimple_mt5_compile.log | tail -5`)
- Smoke artifact: `ML/reports/mt5_execution_loop/batch/_smoke/` (plan Task 2, Step 1; verify: `ls ML/reports/mt5_execution_loop/batch/_smoke/`)
- Batch INI/.set files: `/tmp/mt5_batch_{run_id}.ini`, `~/.mt5/.../Profiles/Tester/{run_id}.set` (не сохранены в repo; см. `run_mt5_batch.py:244-267` для шаблона INI)

## Decision

**BATCH_NO_WINNER.** Ни один из 32 кандидатов не прошёл гейты победителя.
В этом diagnostic MT5 validation batch с combined split roles, gross PF и
diagnostic timing contract ни один из 32 заранее отобранных movement-filter
кандидатов не прошёл winner gates; это не закрывает семейство моделей вне
данного периода, cost model и split protocol. Результат согласуется с
ожиданиями: movement-filter модели демонстрируют предиктивную способность на
val_select — Spearman val_select у 11 eligible в диапазоне 0.48–0.57 (по всем
32 шортлиста — 0.27–0.57; слабые 24h-горизонты 0.270 включены через
movement-lift гейт, а не через Spearman), но это не транслируется в стабильный
PF > 1.0 через механику limit orders на XAUUSD H1.

## Next Steps

1. Диагностический анализ: почему top-кандидаты (PF 1.17–1.23) не проходят
   bootstrap — мало сделок (100–102) или высокая дисперсия.
2. Рассмотреть расширение периода (полный order mechanics 2019.06–2022.12)
   для увеличения выборки.
3. Cost model: применить swap/commission по docs/methodology/12-backtest-costs.md.
4. Отдельный val-eval split для снятия потолка RESEARCH_ONLY.

## Appendix: Full 32-row table

Команда для извлечения полной таблицы из structured artifact:

```bash
jq -r '.table[] | [.run_id, .trades_count, .profit_factor, .pf_buy, .pf_sell, .unexplained] | @tsv' \
  ML/reports/mt5_execution_loop/batch/batch_summary.json | sort -t$'\t' -k2 -nr
```
