# Аудит плана `2026-07-30-mt5-single-rule-diagnostic-run.md`

Проверяемый файл: `docs/superpowers/plans/2026-07-30-mt5-single-rule-diagnostic-run.md`.

Статус аудита: фактическая проверка по связанным первоисточникам. `knowledge-rag` дал пустой результат по похожим документам, поэтому использованы прямые ссылки из плана, `graphify query`, методики, отчёты, код и тесты.

## Замечания

### 1. В плане нет обязательных полей нового roadmap-плана

- Важность: важно.
- Место: `docs/superpowers/plans/2026-07-30-mt5-single-rule-diagnostic-run.md`, начало файла, строки 1-35.
- Суть проблемы: план описывает цель, архитектуру и ограничения, но не содержит обязательные поля `depends_on`, `blocks`, `supersedes`, `exit_decisions`, `locked_test_policy`, которые требуются для нового плана по текущему `roadmap.md`.
- Доказательство: `docs/superpowers/roadmap.md`, строки 153-161: "Новый план должен иметь поля: depends_on, blocks, supersedes, exit_decisions, locked_test_policy". В проверяемом плане `locked_test_policy` есть только внутри будущего JSON-манифеста, строки 98-121, но не как поле самого плана.
- Почему это важно: без этих полей следующий агент не видит, от чего план зависит, что он разблокирует и какие решения закрывают этап. Это повышает риск неверного перехода к batch selection или новой ML-проверке.
- Рекомендуемое исправление: добавить в начало плана отдельный блок:
  - `depends_on: docs/reports/2026-07-29-mt5-execution-loop-migration.md; docs/reports/2026-07-29-mt5-manual-tester-runbook.md`
  - `blocks: MT5 batch selection for 20-50 candidates`
  - `supersedes: none`
  - `exit_decisions: continue | close | unblock`
  - `locked_test_policy: not used for new selection; no winner/threshold/rule/cost/entry/exit/stop selection`.

### 2. Неверная ссылка на задачу обнаружения tester `Files`

- Важность: улучшение.
- Место: `Known Unknowns`, строка 32.
- Суть проблемы: сказано, что фактический каталог MT5 tester `Files` должен быть найден во время Task 2, но сам шаг обнаружения находится в Task 4.
- Доказательство: строка 32 указывает "during Task 2"; строки 286-290 содержат "Task 4 / Step 1: Discover actual MT5 tester Files directory".
- Почему это важно: это не ломает методологию, но сбивает порядок выполнения. Исполнитель может начать искать runtime-каталог до компиляции и экспорта, хотя план сам относит это к упаковке и запуску tester.
- Рекомендуемое исправление: заменить "during Task 2" на "during Task 4".

### 3. Проверка `feature_available_time <= decision_time` заявлена методически, но не выполняется схемой

- Важность: важно.
- Место: `Methodology Map` и `Task 2/Task 5`, строки 24, 178-202, 392-410.
- Суть проблемы: план проверяет `feature_time <= decision_time` и для событий `feature_time <= decision_time <= execution_time`, но не требует проверки `feature_available_time <= decision_time`. При этом методика требует соответствия моменту торгового решения, а поле `feature_available_time` специально входит в CSV-контракт.
- Доказательство: `ML/baseline/mt5_signal_schema.py`, строки 79-120: `validate_mt5_signal_frame()` вызывает `_validate_time_order(frame, ["feature_time", "decision_time"])`; `feature_available_time` не участвует. Для событий строки 123-128 проверяют только `["feature_time", "decision_time", "execution_time"]`. Методика `docs/methodology/03-feature-contract-leakage.md`, строки 1-10 и 19, требует соответствия доступности признаков моменту решения и исполнимой цены после доступности признаков.
- Почему это важно: возможен CSV, где `feature_time <= decision_time`, но фактическая доступность признака позже решения. Такой экспорт пройдёт плановые проверки, хотя торговое решение ещё не могло быть принято честно.
- Рекомендуемое исправление: в плане добавить явную проверку `feature_time <= feature_available_time <= decision_time` для entry CSV и `feature_available_time <= decision_time <= execution_time` для event CSV. Лучше также добавить тест и исправление `validate_mt5_signal_frame()` / `validate_mt5_event_frame()`.

### 4. План требует `open_without_close_estimate` в отчёте, но парсер JSON его не создаёт

- Важность: важно.
- Место: Task 5 и Task 6, строки 364-367, 428-435, 466-479.
- Суть проблемы: Task 5 обещает JSON с event counts, open/close counts, close reasons, missing-open estimate и profit sum, а Task 6 требует `Open without close estimate`. Но `ML/baseline.parse_mt5_execution_report` записывает только `missing_open_estimate`; `open_without_close_estimate` считается разовой inline-командой и не попадает в structured artifact.
- Доказательство: `ML/baseline/parse_mt5_execution_report.py`, строки 31-54: возвращаются `status`, `order_counts`, `open_counts`, `close_counts`, `close_reason_counts`, `ml_close_decision_count`, `profit_sum`, `missing_open_estimate`; поля `open_without_close_estimate` нет. План требует этот показатель в отчёте на строке 476.
- Почему это важно: методика отчётности требует сверять ключевые числа с JSON/CSV-артефактами, а не переносить вручную из временного вывода команды. См. `docs/methodology/16-reporting-audit.md`, строки 31 и 97.
- Рекомендуемое исправление: либо добавить `open_without_close_estimate` в `compute_mt5_metrics()` и тест `tests/test_parse_mt5_execution_report.py`, либо изменить Task 6 так, чтобы отчёт ссылался на отдельный сохранённый artifact с этим расчётом.

### 5. Команда выбора source-кандидата шумная и включает не-CSV артефакты

- Важность: улучшение.
- Место: Task 1 Step 1, строки 54-62.
- Суть проблемы: команда ищет `csv|json|npy|pt|md`-подобные артефакты через общий шаблон и реально возвращает сотни нерелевантных файлов, включая `*.npy`, `checkpoint.pt`, отчёты и JSON-метаданные. При этом ожидаемый результат шага: "identify one existing source CSV".
- Доказательство: команда `rg --files ML/reports DATA MT/MQL5/Files MT/MQL4/Files | rg 'entry|signal|fixed11|current|mt5|csv|json'` вернула 575 строк и предупреждение `MT/MQL5/Files: No such file or directory`. Среди результатов есть `DATA/y_val_entry_path_v1_cls.npy`, `ML/reports/track_a_max_out_matrix/.../checkpoint.pt`, многочисленные JSON и MD. Каталог `MT/MQL5/Files` отсутствует: `test -d MT/MQL5/Files` -> `no`.
- Почему это важно: исполнитель может выбрать неподходящий JSON/отчёт вместо CSV или потратить время на ручную фильтрацию. Для плана, который запрещает выбор по прибыльности, важно иметь воспроизводимую процедуру выбора источника.
- Рекомендуемое исправление: сузить команду до CSV и заранее известных семейств, например:
  ```bash
  rg --files ML/reports DATA MT/MQL4/Files | rg '(^|/)(.*fixed11.*|.*entry.*|.*signal.*).*\.csv$'
  ```
  И отдельно указать, что отсутствие `MT/MQL5/Files` не является ошибкой, потому что фактический tester `Files` ищется в Task 4.

### 6. Manifest не фиксирует date range, хотя интерфейс Task 1 обещает это поле

- Важность: важно.
- Место: Task 1 Interface и manifest template, строки 48-50 и 98-121.
- Суть проблемы: интерфейс Task 1 обещает, что manifest производит `date range`, но шаблон JSON не содержит `date_from`, `date_to` или другого поля периода.
- Доказательство: строка 50: "Produces: fixed run_id, selected source path, source hash, date range..."; строки 98-121 показывают точную структуру JSON без периода.
- Почему это важно: Strategy Tester должен запускаться на конкретном периоде, а методика `13b` требует записать `date range`. Без периода нельзя воспроизвести источник сигналов и tester-прогон.
- Рекомендуемое исправление: добавить в manifest поля `date_from` и `date_to`, полученные из выбранного source CSV, либо явно записать `date_range_policy` и `date_range_status=UNKNOWN`, если период будет определён только в Task 4.

### 7. План не требует hash для event CSV и metrics JSON

- Важность: улучшение.
- Место: Task 4, Task 5, Task 6, строки 336-352, 380-390, 466-479.
- Суть проблемы: план требует hash для source CSV и entry CSV, но не требует hash для возвращённого `mt5_trade_events_<run_id>.csv` и `mt5_execution_metrics_<run_id>.json`.
- Доказательство: Task 1 строки 98-128 фиксирует `source_csv_sha256`; Task 2 JSON sidecar по коду содержит `output_csv_sha256` (`ML/baseline/export_mt5_entry_signals.py`, строки 180-182). В Task 4-6 нет требования записать `sha256` для event CSV и metrics JSON. Методика `16-reporting-audit.md`, строка 31, требует paths и hashes.
- Почему это важно: event CSV является главным доказательством tester-прогона. Без hash труднее отличить текущий прогон от устаревшего файла, хотя сам план требует не принимать stale event file.
- Рекомендуемое исправление: добавить в Task 4/5 команду `sha256sum ML/reports/mt5_execution_loop/mt5_trade_events_<run_id>.csv ML/reports/mt5_execution_loop/mt5_execution_metrics_<run_id>.json` и включить эти hash в отчёт.

### 8. Event lifecycle limitation не имеет измеримой проверки same-H1 open-and-close

- Важность: вопрос.
- Место: Known Unknowns и Task 5 Step 4, строки 35, 412-439.
- Суть проблемы: план честно признаёт риск same-H1 open-and-close, но проверка считает только агрегаты `ORDER_PLACED`, `OPEN`, `CLOSE`, `ML_CLOSE`. Она не даёт способа отличить обычную незакрытую позицию на конце периода от сделки, которая открылась и закрылась внутри одного H1-бара и не была восстановлена логом.
- Доказательство: `docs/methodology/13b-mt5-execution-parity.md`, строки 74-83, описывает ограничение прототипа: сопровождение работает на H1-баре, не через `OnTradeTransaction`, поэтому pending-order, открытый и закрытый внутри одного H1-бара, может не восстановить полный lifecycle. Плановые строки 428-435 считают только разность агрегатов.
- Почему это важно: один из главных заявленных рисков плана может остаться только текстовой оговоркой, а не измеренным или явно заблокированным расхождением.
- Рекомендуемое исправление: добавить в Task 5 требование сверить агрегаты с MT5 history/deals или tester HTML/XML report, если он доступен. Если такой источник недоступен, отчёт должен поставить `same_h1_lifecycle_status=UNKNOWN` и не считать event lifecycle доказанным.

### 9. Финальный report-шаблон не покрывает обязательные секции методики 16

- Важность: улучшение.
- Место: Task 6 Step 1, строки 462-480.
- Суть проблемы: список обязательного содержимого отчёта полезен, но не требует явно указать `Stage Level`, `Multiple Testing Context`, `Changed Files`, `Verification`, `Split Disclosure`, `Related Materials` и `forbidden_interpretations`.
- Доказательство: `docs/methodology/16-reporting-audit.md`, строки 18-30, перечисляет обязательные секции отчёта; строки 88-104 задают обязательные проверки, включая уровень этапа, запрет выбора по holdout, количество строк/событий/сигналов/сделок и запреты на дальнейшую интерпретацию. Плановые строки 466-479 покрывают только часть этих требований.
- Почему это важно: итоговый отчёт может оказаться фактическим, но неполным по методике, и следующий агент не увидит полный контекст множественных проверок и split/holdout-ограничений.
- Рекомендуемое исправление: расширить Task 6 шаблон отчёта секциями из методики 16. Для этого диагностического этапа явно записывать `Multiple Testing Context: no new ML search`, `Split Disclosure: locked_test not used`, `forbidden_interpretations`, `Changed Files`, `Verification`, `Related Materials`.

### 10. Команда проверки diagnostic inputs не проверяет количество совпадений по каждому input

- Важность: улучшение.
- Место: Task 3 Step 1, строки 223-231.
- Суть проблемы: команда `rg -n "A|B|C..."` может вывести часть совпадений, а исполнитель визуально решит, что "all six inputs are present". Формально команда не падает, если найден только один из шести input.
- Доказательство: `rg` с общей альтернативой возвращает код 0 при любом совпадении. Связанный файл сейчас содержит все шесть input: `MT/MQL5/Experts/$o$imple.mq5`, строки 72-77, что подтверждает корректность факта для текущего состояния, но сама проверка плана слабая.
- Почему это важно: при будущей правке MQL5 можно пропустить отсутствие одного параметра и всё равно перейти к компиляции.
- Рекомендуемое исправление: заменить на маленькую проверку цикла по ожидаемым именам, где отсутствие любого input завершает команду ошибкой.

## Подтверждённые утверждения без замечаний

- Цель single-rule MT5 diagnostic соответствует текущему `ACTIVE` roadmap: `docs/superpowers/roadmap.md`, строки 17-29.
- Статус `DIAGNOSTIC_ONLY` обоснован: предыдущий отчёт фиксирует, что MT5 tester runtime-прогон не выполнялся, MT5 `Nero.csv` parity остаётся `UNKNOWN`, а terminal file directory должен быть подтверждён пользователем (`docs/reports/2026-07-29-mt5-execution-loop-migration.md`, разделы `Verification`, `Results`, `Limitations / Open Questions`).
- Команда компиляции и правило не считать `wine` exit code финальным verdict совпадают с `docs/methodology/13b-mt5-execution-parity.md`, раздел `Компиляция`.
- Входной MT5 CSV-контракт в плане совпадает с кодом `ML/baseline/mt5_signal_schema.py`, строки 5-17.
- Запрещённые future/result колонки в плане совпадают с кодом `ML/baseline/mt5_signal_schema.py`, строки 19-27.
- MQL5 diagnostic inputs реально присутствуют в `MT/MQL5/Experts/$o$imple.mq5`, строки 72-77.

## Использованные проверки

```bash
sed -n '1,260p' docs/superpowers/plans/2026-07-30-mt5-single-rule-diagnostic-run.md
sed -n '261,620p' docs/superpowers/plans/2026-07-30-mt5-single-rule-diagnostic-run.md
graphify query "MT5 single rule diagnostic run execution parity event lifecycle Nero parity export mt5 entry signals" --budget 2000
sed -n '1,220p' docs/methodology/README.md
sed -n '1,260p' docs/methodology/00-research-management.md
sed -n '1,260p' docs/methodology/03-feature-contract-leakage.md
sed -n '1,260p' docs/methodology/12-backtest-costs.md
sed -n '1,300p' docs/methodology/13-export-mt4-parity.md
sed -n '1,320p' docs/methodology/13b-mt5-execution-parity.md
sed -n '1,260p' docs/methodology/16-reporting-audit.md
sed -n '1,260p' docs/reports/2026-07-29-mt5-execution-loop-migration.md
sed -n '1,240p' docs/reports/2026-07-29-mt5-manual-tester-runbook.md
sed -n '1,220p' docs/reports/2026-07-29-mt5-feasibility.md
nl -ba ML/baseline/mt5_signal_schema.py | sed -n '1,260p'
nl -ba ML/baseline/export_mt5_entry_signals.py | sed -n '1,320p'
nl -ba ML/baseline/parse_mt5_execution_report.py | sed -n '1,320p'
nl -ba tests/test_mt5_signal_executor_schema.py | sed -n '1,260p'
nl -ba tests/test_parse_mt5_execution_report.py | sed -n '1,260p'
rg -n "InpMT5_DiagnosticExecutor|InpMT5_EntrySignalFile|InpMT5_EventFile|InpMT5_BlockBarsSinceFill0Exit|InpMT5_ExportNero|InpMT5_NeroFile|TerminalInfoString|FileOpen|FILE_COMMON|FileDelete|mt5_trade_events" MT/MQL5/Experts/'$o$imple.mq5' MT/MQL5/Include/lib_ML_Signal.mqh MT/MQL5/Include/lib_PIC.mqh
test -d MT/MQL5/Files
```

## Ошибки мониторинга

- MCP: `knowledge-rag` вернул пустой результат для похожих документов по проверяемому плану и связанному отчёту; аудит продолжен по первичным файлам.
