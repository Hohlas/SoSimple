# Аудит: MT5 Batch Selection 32 Candidates

Аудируемые документы:

- `docs/reports/2026-07-31-mt5-batch-selection.md`
- `docs/superpowers/plans/2026-07-31-mt5-batch-selection.md`

Проверенные первоисточники: `ML/reports/mt5_execution_loop/batch/batch_summary.json`, `ML/reports/entry_based_movement_filter_candidates.csv`, `ML/baseline/run_mt5_batch.py`, `ML/reports/mt5_execution_loop/batch_selection_contract.json`, `CONTEXT_HANDOFF.md`, `CHANGELOG.md`, `docs/reports/2026-07-31-mt5-nero-parity.md`, `docs/reports/2026-07-31-mt5-ontradetransaction-lifecycle.md`, `docs/methodology/09-validation-freeze.md`, `docs/methodology/12-backtest-costs.md`, `docs/methodology/13b-mt5-execution-parity.md`, `docs/methodology/16-reporting-audit.md`.

Навигация: `knowledge-rag` не нашёл `docs/reports/2026-07-31-mt5-batch-selection.md` как проиндексированный документ; `graphify query "MT5 batch selection report methodology validation freeze backtest costs execution parity" --budget 1500` указал на те же связанные источники: `run_mt5_batch.py`, `benchmark_entry_based_movement_filter.py`, `12-backtest-costs.md`, `docs/reports/2026-07-29-mt5-execution-loop-migration.md`, `export_mt5_entry_signals()` и `prepare_entry_quality_source()`.

## Итог

Ключевые числа отчёта в основном совпадают со structured artifact `batch_summary.json`: 32 кандидата, 32 valid, 11 eligible, 16 diagnostic-only, 5 insufficient, `BATCH_NO_WINNER`, bootstrap 2000 итераций, block size 15, seed 42, Holm-Bonferroni по 11 тестам. Главные проблемы не в арифметике результата, а в статусах, воспроизводимости и нескольких неподтверждённых утверждениях.

## Замечания

### 1. Важность: важно

- **Место:** `docs/reports/2026-07-31-mt5-batch-selection.md:4`, `docs/reports/2026-07-31-mt5-batch-selection.md:124-125`, `docs/reports/2026-07-31-mt5-batch-selection.md:157-164`
- **Суть проблемы:** отчёт одновременно ставит `Status: DIAGNOSTIC_ONLY` и пишет, что из-за combined split roles потолок статуса — `RESEARCH_ONLY`. Это разные статусы. В методологии `DIAGNOSTIC_ONLY` означает проверку механики без выводов о качестве, а `RESEARCH_ONLY` — поисковый результат, который не может стать кандидатом без нового проверочного цикла.
- **Доказательство:** `docs/methodology/README.md:46-51` определяет оба статуса отдельно. `docs/methodology/09-validation-freeze.md:20-29` требует понизить результат до `RESEARCH_ONLY`, если validation роли объединены. `docs/methodology/12-backtest-costs.md:52-58` понижает execution-выводы до `DIAGNOSTIC_ONLY`, если неизвестна ценовая конвенция. В `batch_summary.json` поле `status` равно `DIAGNOSTIC_ONLY`.
- **Почему это важно:** смешение статусов делает непонятным, что именно запрещает повышение результата: исследовательская роль split или неполный контур исполнения/издержек. Следующий агент может неверно решить, какой блокер надо закрывать первым.
- **Рекомендуемое исправление:** ввести явное разделение: `lifecycle_status: RESEARCH_ONLY`, `execution_status: DIAGNOSTIC_ONLY`, `allowed_max_verdict: DIAGNOSTIC_ONLY`. Либо оставить один статус, но объяснить, что выбран более строгий потолок из-за gross PF, неполной metadata и timing/cost contract.

### 2. Важность: важно

- **Место:** `docs/reports/2026-07-31-mt5-batch-selection.md:26-35`, `docs/reports/2026-07-31-mt5-batch-selection.md:81-109`
- **Суть проблемы:** отчёт с PF/PnL-метриками не содержит обязательный research-first disclosure-блок: `lifecycle_status`, `origin_bias`, `current_search_budget`, `cumulative_search_budget`, `allowed_max_verdict`, `forbidden_interpretations`.
- **Доказательство:** `docs/methodology/16-reporting-audit.md:64-87` требует этот блок для исследовательских отчётов и требует рядом с PnL/PF указать `allowed_max_verdict`, причину, почему это не торговый вывод, непройденные проверки и запрещённые интерпретации. Поиск `rg -n "lifecycle_status|allowed_max_verdict|forbidden_interpretations" docs/reports/2026-07-31-mt5-batch-selection.md` не нашёл совпадений.
- **Почему это важно:** без такого блока таблица PF выглядит как торговая оценка, хотя сам отчёт признаёт gross PF, combined split roles, отсутствие locked_test и неполный timing/cost contract.
- **Рекомендуемое исправление:** добавить короткий блок disclosure перед Results и повторить рядом с таблицей PF: `allowed_max_verdict: DIAGNOSTIC_ONLY`, причина: gross MT5 tester PF без swap/commission, совмещённые validation-роли, нет locked_test, timing contract diagnostic.

### 3. Важность: важно

- **Место:** `docs/reports/2026-07-31-mt5-batch-selection.md:31`, `docs/reports/2026-07-31-mt5-batch-selection.md:73-79`, `docs/reports/2026-07-31-mt5-batch-selection.md:172`
- **Суть проблемы:** cost model описан как будущий шаг, но методология запрещает оставлять spread/commission/slippage "на потом" для final verdict. Отчёт правильно понижает статус, но не фиксирует полный список отсутствующих cost assumptions: commission, slippage, swap, latency, missed opens, position limits.
- **Доказательство:** `docs/methodology/12-backtest-costs.md:16-26` требует описать spread, commission, swap, slippage, requote/open failure, latency, next-bar entry и position limits. `docs/methodology/12-backtest-costs.md:66-75` требует, чтобы cost assumptions были указаны до final verdict, canonical spread был основным gate, а пропущенные входы не считались нулевым риском без обоснования. В отчёте есть только gross PF, swap/commission и spread mode.
- **Почему это важно:** при PF около 1.17-1.23 даже небольшие издержки могут изменить ранжирование и вывод. Кроме того, fill rate низкий, а это отдельный execution-риск, не только статистическая слабость модели.
- **Рекомендуемое исправление:** расширить Limitations/Next Steps отдельным списком отсутствующих издержек и явно запретить сравнивать gross PF с будущим net PF как один и тот же frozen result.

### 4. Важность: важно

- **Место:** `docs/reports/2026-07-31-mt5-batch-selection.md:37-54`, `docs/reports/2026-07-31-mt5-batch-selection.md:145-147`
- **Суть проблемы:** tester metadata неполна, и часть полей названа "зафиксировано по смежным прогонам", но не указаны конкретные артефакты для batch-прогона. Сам `batch_summary.json` metadata не содержит.
- **Доказательство:** команда `jq '.metadata // .tester_metadata // .config // empty' ML/reports/mt5_execution_loop/batch/batch_summary.json` возвращает пустой результат. `docs/methodology/13b-mt5-execution-parity.md:169-177` требует зафиксировать MT5 build, broker/server, symbol contract specification, tester model, date range, deposit/currency/leverage, spread mode, account mode. `run_mt5_batch.py:244-267` фиксирует в INI только Symbol, Period, Model, FromDate, ToDate, Deposit, Currency, Leverage и ExecutionMode; broker, build, contract spec, spread mode и account mode там не сохраняются.
- **Почему это важно:** без metadata нельзя уверенно воспроизвести tester run и нельзя отличить изменение результата из-за модели от изменения условий брокера/терминала.
- **Рекомендуемое исправление:** добавить в отчёт и JSON ссылку на batch INI, compile log, terminal/agent log, server/build и contract spec snapshot. Если артефактов нет, явно пометить эти поля как `UNKNOWN`, а не "зафиксировано".

### 5. Важность: улучшение

- **Место:** `docs/reports/2026-07-31-mt5-batch-selection.md:67-71`, `docs/superpowers/plans/2026-07-31-mt5-batch-selection.md:104-108`
- **Суть проблемы:** исключение кандидатов с `trades_count < 100` до Holm-Bonferroni действительно заранее задано в плане, но отчёт не раскрывает, что это меняет семейство проверяемых гипотез с 32 на 11 и оставляет 21 кандидата как диагностические/недостаточные результаты.
- **Доказательство:** план `docs/superpowers/plans/2026-07-31-mt5-batch-selection.md:78-88` задаёт sample-size gate и коррекцию по кандидатам, прошедшим trades gate. `batch_summary.json` показывает `n_candidates=32`, `n_eligible=11`, `multiple_testing.n_tests=11`; команда `jq '.table as $t | {len: ($t|length), eligible: ($t | map(select(.trades_count >= 100 and .trades_buy >= 30 and .trades_sell >= 30)) | length), diagnostic_only: ($t | map(select(.trades_count >= 30 and .trades_count < 100)) | length), insufficient: ($t | map(select(.trades_count < 30)) | length)}' ...` вернула `32/11/16/5`.
- **Почему это важно:** читатель может решить, что multiple-testing correction покрыла все 32 MT5-прогона. Фактически она покрыла только подмножество, допущенное к winner selection.
- **Рекомендуемое исправление:** добавить формулировку: "Holm-Bonferroni применён только к 11 candidate tests после заранее заданного sample-size gate; 21 результат не участвовал в winner family и не может использоваться для выбора без нового плана коррекции".

### 6. Важность: улучшение

- **Место:** `docs/reports/2026-07-31-mt5-batch-selection.md:91-95`, `docs/reports/2026-07-31-mt5-batch-selection.md:157-164`
- **Суть проблемы:** в отчёте приведена только top-5 таблица, хотя plan Task 4 обещал "таблицу 32 метрик". Есть ссылка на JSON, но нет команды/сводки, позволяющей быстро проверить все 32 строки.
- **Доказательство:** `docs/superpowers/plans/2026-07-31-mt5-batch-selection.md:237` требует "таблица 32 метрик". `docs/methodology/16-reporting-audit.md:94-97` требует количества raw rows, событий, сигналов и сделок после фильтров и сверку ключевых чисел со structured artifact. В отчёте строки 83-90 содержат только 5 кандидатов.
- **Почему это важно:** отчёт становится менее воспроизводимым: чтобы проверить низкий fill rate, распределение по статусам и кандидатов с высоким PF при малом N, надо самостоятельно разбирать JSON.
- **Рекомендуемое исправление:** добавить компактную полную таблицу 32 строк или appendix с командой `jq -r '.table[] | [...] | @tsv' ML/reports/mt5_execution_loop/batch/batch_summary.json`.

### 7. Важность: улучшение

- **Место:** `docs/reports/2026-07-31-mt5-batch-selection.md:129-133`, `docs/superpowers/plans/2026-07-31-mt5-batch-selection.md:57-60`
- **Суть проблемы:** отчёт корректно признаёт, что прежняя оценка "~4947 баров" не воспроизводится, но не заменяет её проверяемым числом H1-баров или командой расчёта.
- **Доказательство:** план `docs/superpowers/plans/2026-07-31-mt5-batch-selection.md:57-60` содержит "~4947 баров"; отчёт `docs/reports/2026-07-31-mt5-batch-selection.md:129-133` говорит, что источник оценки не воспроизводится. `run_mt5_batch.py:50-55` фильтрует EQ scores по `2021-01-04` - `2022-12-02`, но отчёт не даёт проверочную команду по исходному CSV.
- **Почему это важно:** размер периода влияет на интерпретацию sample size и на объяснение провала bootstrap.
- **Рекомендуемое исправление:** либо убрать число из плана как устаревшее, либо добавить в отчёт команду расчёта пересечения movement scores и order mechanics с точным числом строк/баров.

### 8. Важность: важно

- **Место:** `docs/reports/2026-07-31-mt5-batch-selection.md:136-142`, `CONTEXT_HANDOFF.md:32-33`
- **Суть проблемы:** LiveUpdate описан как гипотеза без артефакта, но handoff уже утверждает более сильный факт: "каталог заблокирован (chmod 555)" и "терминал скачивает обновление". Сам отчёт не ссылается на проверочный лог или команду.
- **Доказательство:** `docs/reports/2026-07-31-mt5-batch-selection.md:136-140` прямо говорит, что событие не зафиксировано в `batch_summary.json` и не подкреплено логом терминала. `CONTEXT_HANDOFF.md:32-33` формулирует состояние как факт. `run_mt5_batch.py:187-197` только проверяет наличие liveupdate-файлов; он не сохраняет результат проверки в batch artifact.
- **Почему это важно:** неподтверждённый внешний фактор может стать ложным объяснением качества или нестабильности batch-прогонов.
- **Рекомендуемое исправление:** синхронизировать формулировки: либо добавить артефакт команды `ls/stat` и terminal log, либо в handoff тоже писать "гипотеза/наблюдение оператора, не покрыто артефактом".

### 9. Важность: важно

- **Место:** `docs/reports/2026-07-31-mt5-batch-selection.md:159-164`, `CHANGELOG.md:23`
- **Суть проблемы:** вывод "movement-filter модели не дают статистически значимого PF > 1.0 через механику limit orders" сильнее, чем позволяют ограничения. Проверка была только на одном validation-периоде, gross PF, без separate val-eval, без locked_test и без полного cost model.
- **Доказательство:** `docs/methodology/09-validation-freeze.md:28` говорит, что объединённые validation роли дают результат не выше `RESEARCH_ONLY`; `docs/methodology/12-backtest-costs.md:112-119` запрещает выдавать gross-only результат за production; `docs/methodology/16-reporting-audit.md:79-87` требует запретить trading-интерпретации рядом с PnL/PF.
- **Почему это важно:** формулировка может быть прочитана как общий отрицательный вывод о классе моделей, а не как результат конкретного diagnostic batch.
- **Рекомендуемое исправление:** сузить вывод: "в этом diagnostic MT5 validation batch ни один из 32 заранее отобранных movement-filter кандидатов не прошёл winner gates; это не закрывает семейство моделей вне данного периода, cost model и split protocol".

### 10. Важность: улучшение

- **Место:** `docs/superpowers/plans/2026-07-31-mt5-batch-selection.md:203-208`, `docs/reports/2026-07-31-mt5-batch-selection.md:155`
- **Суть проблемы:** план обещал новый `ML/baseline/aggregate_mt5_batch.py`, но фактическая агрегация реализована внутри `ML/baseline/run_mt5_batch.py`. Это не ломает результат, но план остался неточным.
- **Доказательство:** `rg -n "aggregate_mt5_batch" ML/baseline docs/superpowers/plans/2026-07-31-mt5-batch-selection.md` показывает упоминание в плане и отсутствие файла `ML/baseline/aggregate_mt5_batch.py`; `run_mt5_batch.py:515-637` содержит `aggregate_batch()` и запись `batch_summary.json`.
- **Почему это важно:** следующий агент может искать несуществующий entrypoint для воспроизведения summary.
- **Рекомендуемое исправление:** обновить план или отчёт: "агрегация выполнена фазой `--phase aggregate` в `ML/baseline/run_mt5_batch.py`; отдельный `aggregate_mt5_batch.py` не создавался".

### 11. Важность: улучшение

- **Место:** `docs/reports/2026-07-31-mt5-batch-selection.md:149-155`
- **Суть проблемы:** раздел Artifacts не перечисляет batch compile log, INI/.set файлы и smoke artifact, хотя план и методика execution parity считают их важными для воспроизводимости.
- **Доказательство:** `docs/superpowers/plans/2026-07-31-mt5-batch-selection.md:172-199` включает compile, smoke, INI/.set и loop progress. `docs/methodology/13b-mt5-execution-parity.md:181-183` требует `.ex5` из текущего `$o$imple.mq5` и сохранённый MetaEditor log. `CONTEXT_HANDOFF.md:57-61` утверждает, что compile и smoke выполнены, но отчёт не даёт пути к их артефактам.
- **Почему это важно:** воспроизведение batch зависит не только от JSON и events CSV, но и от фактических настроек tester.
- **Рекомендуемое исправление:** добавить paths к compile log, smoke `_smoke`, сохранённым INI/.set или явно написать, что эти артефакты не сохранены.

### 12. Важность: вопрос

- **Место:** `docs/reports/2026-07-31-mt5-batch-selection.md:39-44`
- **Суть проблемы:** "Agent build: 6061; серверный build 6074 наблюдение сессии, без артефакта" сформулировано с синтаксическим пропуском и неясным уровнем доказанности.
- **Доказательство:** смежный lifecycle report фиксирует `agent build 6061` в `docs/reports/2026-07-31-mt5-ontradetransaction-lifecycle.md:37-39`, но batch report сам признаёт отсутствие batch artifact для части metadata в строках 54 и 145-147.
- **Почему это важно:** build терминала может влиять на Strategy Tester, а строка сейчас смешивает подтверждённый и неподтверждённый факт.
- **Рекомендуемое исправление:** переписать как два пункта: `Agent build 6061: подтверждён смежным lifecycle artifact, не batch artifact`; `Server build 6074: наблюдение оператора, artifact отсутствует`.

## Подтверждённые утверждения

- `batch_summary.json` подтверждает `n_candidates=32`, `n_valid=32`, `n_eligible=11`, `n_diagnostic_only=16`, `verdict=BATCH_NO_WINNER`, `status=DIAGNOSTIC_ONLY`.
- `batch_summary.json` подтверждает Holm-Bonferroni: `method=Holm-Bonferroni`, `alpha=0.05`, `n_tests=11`, все `holm_rejected=false`.
- `batch_summary.json` и команда по `.table` подтверждают 5 insufficient candidates: 32 total минус 11 eligible минус 16 diagnostic-only.
- `ML/reports/entry_based_movement_filter_candidates.csv` содержит 32 строки данных: `wc -l` вернул 33 с заголовком; все `selection_eligible=True` и `yearly_check_pass=True`.
- Для 24h `simple_combined` Spearman `val_select_spearman_median=0.2698047684294034`, `movement_lift=1.330488` - `1.509332`, `selection_eligible=True`, `yearly_check_pass=True`; это подтверждает пояснение отчёта о прохождении шортлиста через movement-lift, а не Spearman.
- `run_mt5_batch.py:417-432` подтверждает block bootstrap с `n_iter=2000`, `block_size=15`, `seed=42`; `run_mt5_batch.py:435-445` подтверждает Holm-Bonferroni.
- `run_mt5_batch.py:544-545` подтверждает разделение `trades_count >= 100` и `30 <= trades_count < 100`; `run_mt5_batch.py:576-582` подтверждает gates `trades_total`, `trades_per_side`, `unexplained_zero`, `bs_p05_above_1`, `holm_rejected`.
- `ML/reports/mt5_execution_loop/batch_selection_contract.json:2-5` подтверждает, что contract обновлён до `EXECUTED`, `BATCH_NO_WINNER` и ссылается на отчёт.

## Ошибки выполнения аудита

- MCP: `knowledge-rag search_similar` вернул `no_results` для `docs/reports/2026-07-31-mt5-batch-selection.md`; использован только как навигационная проверка, не как источник фактов.
- Процедурная ошибка: при поиске связанных упоминаний команда `rg` случайно вернула строки из старого `docs/superpowers/audit.md`, хотя пользователь запретил читать его содержимое. Эти строки не использованы как доказательство; файл полностью удалён и создан заново этим аудитом.
