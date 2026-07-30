# Audit: MT5 execution-loop migration

Аудируемый план: `docs/superpowers/plans/2026-07-29-mt5-execution-loop-migration.md`.

Проверено точечно: итоговый отчёт, связанные схемы, manifests, runbook, roadmap/changelog/handoff/wiki, MQL5 expert/include-файлы, Python exporter/parser/tests и релевантные разделы `docs/methodology`.

## 1. Критично

Место: `docs/reports/2026-07-29-mt5-execution-loop-migration.md:88-95`, `docs/MT/mt5_signal_executor.md:102-118`, `MT/MQL5/Experts/$o$imple.mq5:151-160`, `MT/MQL5/Include/lib_ML_Signal.mqh:372-431`.

Суть проблемы: отчёт описывает вертикальный контур как готовый для проверки фактического fill/SL/TP/close mechanics в MT5 tester, но диагностический lifecycle сейчас запускается только на новом H1-баре и может пропустить сделку, которая открылась и закрылась внутри одного H1-бара.

Доказательство:
- `OnTick()` при том же `Time[0]` вызывает только `CHECK_OUT()` и сразу выходит: `MT/MQL5/Experts/$o$imple.mq5:154-156`.
- `MT5_LogLifecycleForCurrentState()` вызывается только из `ML_TRADE()`: `MT/MQL5/Include/lib_ML_Signal.mqh:547-555`, а `ML_TRADE()` вызывается из `INPUT()` внутри полного `MAIN()` на новом баре: `MT/MQL5/Include/MAIN.mqh:131-141`.
- После `ORDER_PLACED` код не сохраняет реальный ticket заявки: `MT/MQL5/Include/lib_ML_Signal.mqh:600-603`, `618-621`; ticket в событии заранее равен `0`.
- Если к следующему H1-бару pending уже исчез и market-позиции уже нет, ветка видит только отсутствие active order и пишет `OPEN_FAILED`/`ORDER_EXPIRED`, не восстанавливая fill и SL/TP из history: `MT/MQL5/Include/lib_ML_Signal.mqh:375-391`.
- Ветка history работает только если ранее был установлен `MT5_TrackedTicket`, а он устанавливается только когда позиция была замечена активной: `MT/MQL5/Include/lib_ML_Signal.mqh:380-385`, `427-431`.

Почему это важно: главная цель перехода на MT5 - доверить платформе исполнение внутри бара. Если эксперт не логирует сделки, которые полностью прошли между H1-активациями, MT5 event log будет недосчитывать открытые/закрытые сделки и искажать parity.

Рекомендуемое исправление: перенести диагностическое сопровождение ордера в tick-level путь или `OnTradeTransaction`, сохранять реальный order/deal/position id после `OrderSend`, а при отсутствии active order проверять MT5 history по magic/order id/времени сигнала. До этого в отчёте явно написать: текущий прототип компилируется, но intrabar fill-and-close logging не доказан.

## 2. Важно

Место: `MT/MQL5/Include/lib_ML_Signal.mqh:179-275`, `docs/methodology/13-export-mt4-parity.md:38-39`, `docs/methodology/12-backtest-costs.md:18-26`, `docs/reports/2026-07-29-mt5-execution-loop-migration.md:27-31`.

Суть проблемы: event log schema содержит поля для reconciliation, но MQL5 writer заполняет часть cost/execution-полей заглушками.

Доказательство:
- Header содержит `take_profit`, `swap`, `commission`, `balance`, `equity`: `MT/MQL5/Include/lib_ML_Signal.mqh:217-218`.
- Writer всегда пишет `take_profit=0.0`, `swap=0.0`, `commission=0.0`: `MT/MQL5/Include/lib_ML_Signal.mqh:257-261`.
- В `CLOSE` строке `order_close_price` заполняется `OrderOpenPrice()`, а не ценой закрытия: `MT/MQL5/Include/lib_ML_Signal.mqh:431`.
- Методика требует логировать spread/slippage/Bid/Ask/commission/swap/balance/equity: `docs/methodology/13-export-mt4-parity.md:38-39`; cost model должен включать commission/swap/slippage/position constraints: `docs/methodology/12-backtest-costs.md:18-26`.

Почему это важно: такой event log пока пригоден как диагностика потока событий, но не как источник корректного PnL/cost reconciliation.

Рекомендуемое исправление: либо заполнить поля из MT5 positions/deals/history, либо в отчёте и schema явно пометить эти колонки как `CURRENTLY_STUBBED` до реализации history/deal reconciliation.

## 3. Важно

Место: `ML/baseline/mt5_signal_schema.py:79-102`, `docs/schemas/mt5_signal_executor_schema.md:42-54`, `docs/methodology/03-feature-contract-leakage.md:46-77`.

Суть проблемы: timing contract описан в документации, но Python-валидатор проверяет только наличие колонок и не проверяет порядок времени `feature_time <= decision_time <= execution_time`.

Доказательство:
- Схема требует `feature_time <= decision_time <= execution_time`: `docs/schemas/mt5_signal_executor_schema.md:42-54`.
- `validate_mt5_signal_frame()` проверяет missing columns, forbidden columns, side и entry_type, но не парсит время: `ML/baseline/mt5_signal_schema.py:79-96`.
- `validate_mt5_event_frame()` проверяет только missing columns: `ML/baseline/mt5_signal_schema.py:99-102`.
- Методика требует фиксировать `decision_time` и момент доступности признаков: `docs/methodology/03-feature-contract-leakage.md:46-77`.

Почему это важно: можно получить формально валидный CSV, где решение принято раньше доступности признаков или исполнение раньше решения. Это прямо возвращает риск заглядывания вперёд, ради устранения которого делается MT5-контур.

Рекомендуемое исправление: добавить проверки времени в `validate_mt5_signal_frame()` и `validate_mt5_event_frame()`, плюс targeted tests на нарушение порядка.

## 4. Важно

Место: `docs/reports/2026-07-29-mt5-feasibility.md:17-20`.

Суть проблемы: feasibility-отчёт устарел и противоречит итоговому состоянию реализации.

Доказательство:
- Feasibility пишет, что event CSV writer ещё отсутствует: `docs/reports/2026-07-29-mt5-feasibility.md:19`.
- Фактически writer реализован как `MT5_ML_LogEvent(...)`: `MT/MQL5/Include/lib_ML_Signal.mqh:179-277`.
- Feasibility фиксирует `.ex5` mtime `2026-07-30 05:33:50 UTC`: `docs/reports/2026-07-29-mt5-feasibility.md:17`, но текущий `stat` показывает `MT/MQL5/Experts/$o$imple.ex5` обновлён в `2026-07-30 06:12:07.863592194 +0000`.

Почему это важно: следующий агент может принять старый feasibility-вывод за актуальный blocker или не понять, какая версия была скомпилирована.

Рекомендуемое исправление: обновить feasibility как superseded-by final report или убрать/исправить устаревшие строки про отсутствующий writer и старое compile time.

## 5. Улучшение

Место: `ML/reports/mt5_execution_loop/mt5_environment_manifest.json`.

Суть проблемы: compile metadata в manifest устарела относительно фактического `.ex5`.

Доказательство:
- Manifest: `compile_check.checked_at_utc = 2026-07-30T05:33:50Z`, `expert_ex5_mtime_utc = 2026-07-30T05:33:50Z`.
- Команда `stat -c '%y %n' MT/MQL5/Experts/'$o$imple.ex5'` показала `2026-07-30 06:12:07.863592194 +0000`.
- Методика требует фиксировать команды, paths, hashes/artifacts: `docs/methodology/16-reporting-audit.md:31`, `88-97`.

Почему это важно: manifest должен быть машинно-читаемым источником воспроизводимости. Сейчас он не соответствует текущему бинарнику.

Рекомендуемое исправление: обновить compile timestamp и добавить hash `.mq5/.mqh/.ex5` или заменить точное время на статус `latest_compile_log_checked` с командой проверки.

## 6. Важно

Место: `ML/baseline/parse_mt5_execution_report.py:23-59`, `tests/test_parse_mt5_execution_report.py:65-107`.

Суть проблемы: parser смешивает событие решения `ML_CLOSE` с фактической причиной закрытия и считает PnL только по строкам `CLOSE`, хотя текущий MQL5 close logging сам помечен как ограниченный.

Доказательство:
- `_filtered_reason_counts()` добавляет количество `ML_CLOSE` events в `close_reason_counts`: `ML/baseline/parse_mt5_execution_report.py:30-32`.
- `profit_sum` считается только по `event == "CLOSE"`: `ML/baseline/parse_mt5_execution_report.py:45-58`.
- Тест ожидает одновременно `ML_CLOSE` как close reason и `broker_history_limited`: `tests/test_parse_mt5_execution_report.py:96-106`.
- Документация признаёт, что `ML_CLOSE` - диагностическое решение, а фактическое закрытие отдельной history-строкой `CLOSE`, при этом `CLOSE` ограничен: `docs/MT/mt5_signal_executor.md:115-126`.

Почему это важно: в отчёте о tester-прогоне легко перепутать "модель попросила закрыть" и "позиция реально закрылась по этой причине". Для parity это разные факты.

Рекомендуемое исправление: разделить `ml_close_decision_count` и actual `close_reason_counts`; не добавлять `ML_CLOSE` decision events в причины фактического закрытия. Для PnL явно требовать реальные `CLOSE`/deal rows.

## 7. Улучшение

Место: `docs/superpowers/plans/2026-07-29-mt5-execution-loop-migration.md`.

Суть проблемы: план заявлен как выполненный, но чекбоксы задач остались незакрытыми.

Доказательство:
- В плане есть требование использовать checkbox syntax for tracking: `docs/superpowers/plans/2026-07-29-mt5-execution-loop-migration.md:3`.
- Поиск по плану показывает шаги вида `- [ ]`, например `Task 1` начинается с незакрытого `Step 1`: `docs/superpowers/plans/2026-07-29-mt5-execution-loop-migration.md:104`.

Почему это важно: для handoff непонятно, какие пункты реально выполнены, какие заменены, а какие остались ручными.

Рекомендуемое исправление: либо отметить выполненные пункты, либо добавить отдельный execution status block с `done/manual/blocked` по задачам 1-9.

## 8. Вопрос

Место: `docs/reports/2026-07-29-mt5-execution-loop-migration.md:118-125`, `ML/reports/mt5_execution_loop/`.

Суть проблемы: следующий шаг требует подать `mt5_entry_signals.csv` в tester, но в каталоге артефактов нет готового `mt5_entry_signals.csv` или `mt5_entry_signals_<run_id>.csv`.

Доказательство:
- Итоговый отчёт говорит: "Подать `mt5_entry_signals.csv` в MT5 tester": `docs/reports/2026-07-29-mt5-execution-loop-migration.md:120-122`.
- `find ML/reports/mt5_execution_loop -maxdepth 1 -type f` показывает только manifests/README/sample events; entry-signal CSV отсутствует.

Почему это важно: если это ожидаемый ручной шаг, всё нормально. Если этап должен был подготовить файл для single-rule прогона, артефакт не создан.

Рекомендуемое исправление: уточнить в отчёте/runbook: entry CSV ещё должен быть сгенерирован отдельной командой `ML/baseline/export_mt5_entry_signals.py` из выбранного frozen source, либо создать диагностический sample entry CSV и manifest.

## Выполненные проверки

```bash
./.venv/bin/python -m pytest tests/test_mt5_signal_executor_schema.py tests/test_parse_mt5_execution_report.py -q
```

Результат: `6 passed in 0.21s`.

```bash
iconv -f UTF-16LE -t UTF-8 /tmp/sosimple_mt5_compile.log | tail -n 30
```

Результат: лог содержит `Result: 0 errors, 0 warnings, 5018 ms elapsed, cpu='X64 Regular'`.

```bash
stat -c '%y %n' MT/MQL5/Experts/'$o$imple.mq5' MT/MQL5/Include/lib_ML_Signal.mqh MT/MQL5/Include/lib_PIC.mqh MT/MQL5/Experts/'$o$imple.ex5'
```

Результат: `.ex5` новее проверенных MQL5 source-файлов.

```bash
rg -n "future_exit_time|pnl_r|fill_time" ML/baseline/export_mt5_entry_signals.py docs/schemas/mt5_signal_executor_schema.md
```

Результат: совпадения только в forbidden-column checks/schema и event schema, не как экспортируемые entry columns.

```bash
rg -n "DIAGNOSTIC_ONLY|feature_time <= decision_time <= execution_time|bars_since_fill=0|Nero.csv|MT5_PrepareEventFileIfNeeded|mt5_entry_signals.csv|Result: 0 errors, 0 warnings" docs/superpowers/plans/2026-07-29-mt5-execution-loop-migration.md docs/schemas/mt5_signal_executor_schema.md docs/schemas/mt5_open_position_feature_contract.md docs/schemas/mt5_nero_csv_contract.md
```

Результат: обязательные contract terms найдены.

Полный `./.venv/bin/python -m pytest tests/ -q` не запускался по правилу пользователя.
