# Аудит этапа MT5 multi-position refactor

Дата аудита: 2026-08-03.

Проверяемые коммиты: `6ceb85345237d9021866727ee1980efad3175fc9`, `94ba840acb09ae5dd44e2b8c5a46b8d198da6e57`, `9a96d10f65b6872fc9b5d513c993215d63550e92`, `9d9e64a41b35c986c372d7385eba6ee31a9e8386`, `414236747c693fdc427dd6233927b4d717a81288`, `37470087fe9d0a134134f1a9fd55a04647c45867`, `274d6282aba5e57f289beb71d2735dd5dfe4ea3e`.

Проверенные первоисточники: `docs/superpowers/plans/2026-08-02-mt5-multi-position-refactor.md`, `docs/reports/2026-08-02-mt5-multi-position-probe.md`, `docs/methodology/README.md`, `docs/methodology/00-research-management.md`, `docs/methodology/13b-mt5-execution-parity.md`, `docs/methodology/16-reporting-audit.md`, `docs/superpowers/README.md`, `tests/README.md`, изменённые MQL5/Python/test-файлы, `CHANGELOG.md`, `CONTEXT_HANDOFF.md`, `docs/superpowers/roadmap.md`.

Навигация: `graphify query "MT5 multi-position refactor plan reports commits position lifecycle close policy ticket magic docs/superpowers/plans/2026-08-02-mt5-multi-position-refactor.md" --budget 2000`; `knowledge-rag` для новых плана и отчёта вернул `no_results`, поэтому выводы ниже основаны на первичных файлах и командах.

## Итог

Статус этапа: **FAIL для заявленной цели "full refactoring"**, **DIAGNOSTIC_ONLY/BLOCKED для экспериментального вывода**.

Код компилируется по сохранённому логу с `0 errors, 2 warnings`, а Python-тесты прошли. Но заявленная функция "каждая позиция, включая одновременные same-direction, получает собственное управление" не доказана и частично противоречит коду: установка новых ордеров всё ещё блокируется legacy-полями `BUY.Val`/`SEL.Val`, часть close-path может пометить не ту сторону, а диагностический lifecycle остаётся однотикетным.

## Замечания

### 1. Критично: same-direction multi-position фактически блокируется в `SET_BUY/SET_SEL`

Место: `MT/MQL5/Include/ORDERS.mqh:22`, `MT/MQL5/Include/ORDERS.mqh:46`, `MT/MQL5/Include/ORDERS.mqh:184-187`; план `docs/superpowers/plans/2026-08-02-mt5-multi-position-refactor.md:5`, `:36-38`, `:407-430`.

Суть проблемы: план обещает поддержку одновременных позиций в одну сторону, а `INPUT.mqh` и `lib_ML_Signal.mqh` действительно снимают часть gate-ов. Но фактическая отправка ордера всё ещё выполняется только в циклах `while (repeat>0 && BUY.Val==0)` и `while (repeat>0 && SEL.Val==0)`. `ORDER_CHECK()` при любом существующем BUY/SELL зеркалит последнюю найденную позицию обратно в legacy `BUY`/`SEL`, поэтому при уже открытой BUY-позиции `SET_BUY()` не войдёт в цикл отправки нового BUY-ордера.

Доказательство: `nl -ba MT/MQL5/Include/ORDERS.mqh | sed -n '14,60p;157,190p'` показывает условия цикла на `BUY.Val==0`/`SEL.Val==0` и backcompat-заполнение `BUY=p.data`/`SEL=p.data`. Это противоречит `INPUT.mqh:29-32`, где multi-pos gate разрешает вход при `BuyActiveCnt < MT5_MaxPositions`.

Почему важно: это бьёт в центральную цель этапа. Даже если диагностический логгер починить, советник может не поставить вторую позицию в ту же сторону, поэтому вывод "multi-position не улучшает PF" или "блокер только в диагностике" будет недостоверен.

Рекомендуемое исправление: в `SET_BUY/SET_SEL` заменить legacy-условие цикла на сторону-зависимую проверку лимита при `MT5_MaxPositions>1`: считать активные и pending позиции нужной стороны по `Pos[]`/тикетам и разрешать отправку, пока count `< MT5_MaxPositions`. Для `MT5_MaxPositions==1` оставить старое поведение. Добавить минимальный тест/логовый smoke, где при уже существующей BUY-позиции и `MT5_MaxPositions=2` второй BUY действительно отправляется или хотя бы доходит до `OrderSend`.

### 2. Критично: `CloseBuySide(0)` / `CloseSellSide(0)` помечают все позиции, а не только свою сторону

Место: `MT/MQL5/Include/OUTPUT.mqh:173-180`, `MT/MQL5/Include/OUTPUT.mqh:209-215`, вызовы `CLOSE_BUY(0)`/`CLOSE_SEL(0)` в `MT/MQL5/Include/OUTPUT.mqh:400-406`.

Суть проблемы: в multi-position helpers проверка `if (price == 0) { Pos[i].data.Val = 0; continue; }` стоит до `PositionSelectByTicket()` и проверки стороны. Значит `CloseBuySide(0, ...)` пометит к удалению/закрытию и SELL-позиции, а `CloseSellSide(0, ...)` пометит BUY-позиции.

Доказательство: `rg -n "CLOSE_BUY\\(0|CLOSE_SEL\\(0" MT/MQL5/Include` находит реальные вызовы с `price=0`; `nl -ba MT/MQL5/Include/OUTPUT.mqh | sed -n '169,220p;392,408p'` показывает порядок операций.

Почему важно: это краевой, но принципиальный дефект управления жизненным циклом. При включении веток POC/near pending logic в multi-pos режиме side-specific close может закрывать противоположную сторону.

Рекомендуемое исправление: в `CloseBuySide`/`CloseSellSide` сначала выбрать тикет и проверить сторону, и только затем обрабатывать `price == 0`. Добавить синтетическую проверку на массив из BUY+SELL: `CloseBuySide(0)` не меняет SELL.

### 3. Важно: диагностический blocker описан как "не баг рефакторинга", но это неподтверждённое утверждение

Место: `docs/reports/2026-08-02-mt5-multi-position-probe.md:139-162`; код `MT/MQL5/Include/lib_ML_Signal.mqh:582-648`.

Суть проблемы: отчёт говорит, что timing-contract сбой в max=2 - это "архитектурное ограничение диагностического слоя executor-а, а не баг рефакторинга плана". Фактически плановая цель включает "life-cycle management" для каждой позиции, а изменённый этап оставил `MT5_TrackedTicket`, `MT5_TrackedIdx`, `MT5_TrackedOpenLogged` однотикетными. Это не внешний шум, а несоответствие реализации заявленному multi-position lifecycle.

Доказательство: `rg -n "MT5_TrackedTicket|MT5_LastPlacedIdx|MT5_FindActiveTicket" MT/MQL5/Include/lib_ML_Signal.mqh` показывает один глобальный tracked ticket. `MT5_LogLifecycleForCurrentState()` выбирает один `buy_market` или `sell_market` и записывает его в один `MT5_TrackedTicket` (`lib_ML_Signal.mqh:582-596`). Методика `docs/methodology/13b-mt5-execution-parity.md:65-73` требует timing contract `decision_time <= execution_time` для signal-linked events.

Почему важно: отчёт снижает серьёзность причины BLOCKED. Пока lifecycle logger однотикетный, нельзя проверить ни fill-rate, ни PF, ни корректность multi-position исполнения.

Рекомендуемое исправление: переформулировать отчёт: это блокирующий дефект покрытия multi-position lifecycle в рамках заявленной цели. Исправить через per-ticket/per-signal tracker и повторить max=2 smoke до batch.

### 4. Важно: backcompat "identical" не доказан

Место: `docs/reports/2026-08-02-mt5-multi-position-probe.md:25-27`, `:113-131`, `:165-167`; план `docs/superpowers/plans/2026-08-02-mt5-multi-position-refactor.md:23`, `:430`.

Суть проблемы: отчёт утверждает, что `--max-positions=1` "identical to previous baseline" и "canonical guarantee подтверждена". Но приведённое доказательство - только smoke `positions=3, UNEXPLAINED=0`; полный batch был `SKIP` по уже существующим метрикам, а план требовал совпадения всех `batch_summary.json` для max=1 и "same events"/"102 trades".

Доказательство: отчёт `docs/reports/2026-08-02-mt5-multi-position-probe.md:119-127` показывает `32/32 SKIP`, то есть новые метрики для 32 кандидатов не пересчитаны. Текущий smoke artifact `ML/reports/mt5_execution_loop/batch/_smoke/metrics.json:3-42` содержит только агрегаты `position_count=3`, `UNEXPLAINED=0`; это не сверка всех событий, цен, tickets, side, PnL и close reasons. План `:430` ожидает "102 trades, same events", что само противоречит отчётному `positions=3`.

Почему важно: backcompat - главный предохранитель рефакторинга. Совпадение двух счётчиков в smoke не доказывает, что single-position режим не изменился.

Рекомендуемое исправление: заменить формулировку на "частичный smoke PASS". Для канонической гарантии прогнать выбранный baseline заново в отдельный output path, сравнить event CSV/metrics с предыдущим эталоном по ключевым колонкам и явно указать, какие поля совпали. Если полный batch намеренно не пересчитывался, не писать "identical".

### 5. Важно: отчёт о компиляции противоречит методике и фактическим артефактам

Место: `docs/reports/2026-08-02-mt5-multi-position-probe.md:92-103`; методика `docs/methodology/13b-mt5-execution-parity.md:136-151`.

Суть проблемы: методика требует успех компиляции как `0 errors, 0 warnings` и проверку обновления `.ex5`. Отчёт фиксирует `0 errors, 2 warnings` и называет это PASS, объясняя warnings как pre-existing. Но warning всё равно нарушает буквальный критерий методики, а текущее время файлов не доказывает связь сохранённого лога с актуальным `.ex5`.

Доказательство: команда `iconv -f UTF-16LE -t UTF-8 /tmp/sosimple_mt5_compile.log | tail -n 20` даёт `Result: 0 errors, 2 warnings`. Команда `ls -l /tmp/sosimple_mt5_compile.log MT/MQL5/Experts/'$o$imple.ex5'` показала лог `Aug 2 18:40`, а `.ex5` `Aug 3 03:47`, то есть сохранённый лог старше текущего бинарника.

Почему важно: для parity-контуров нельзя ссылаться на лог, который не подтверждает текущий скомпилированный файл. Warnings можно принять как риск, но не как PASS по критерию "0 warnings".

Рекомендуемое исправление: пересобрать эксперт, сохранить лог в репозитории или отчётном каталоге, указать `mtime` `.ex5`. Если warnings остаются, статус проверки должен быть `PASS_WITH_WARNINGS`/`DIAGNOSTIC_ONLY`, а не чистый PASS; лучше исправить тип `ticket` на `ulong` или документировать, почему это невозможно.

### 6. Важно: в research-first disclosure отсутствует `research_priority`

Место: `docs/superpowers/plans/2026-08-02-mt5-multi-position-refactor.md:14-24`, `docs/reports/2026-08-02-mt5-multi-position-probe.md:6-23`; методика `docs/methodology/00-research-management.md:55-64`, `docs/methodology/16-reporting-audit.md:64-74`.

Суть проблемы: для `research_hypothesis` методика требует `research_priority`, но в плане и отчёте его нет.

Доказательство: в disclosure блоках перечислены `lifecycle_status`, `origin_bias`, `roadmap_track`, `current_search_budget`, `cumulative_search_budget`, `next_probe_freeze`, `allowed_max_verdict`, `forbidden_interpretations`, но нет `research_priority`.

Почему важно: priority нужен для управления очередью исследований и предотвращения бесконтрольного расширения поиска после просмотра результатов.

Рекомендуемое исправление: добавить `research_priority: low|medium|high` с причиной. Для этого этапа разумно указать `medium` или `high` только если он прямо разблокирует проверку fill-rate гипотезы; иначе `medium` с ограничением "diagnostic blocker".

### 7. Важно: план Task 6 содержит неверные команды и критерии

Место: `docs/superpowers/plans/2026-08-02-mt5-multi-position-refactor.md:422-444`.

Суть проблемы: в плане есть команда `./.venv/bin/python -m ML.baseline.tester`, которой нет среди изменённых модулей, и повреждённая строка `./.venv/bin/pythonスス... root … --max-positions=16 ...`. Там же критерий "102 trades, same events" не совпадает с отчётным smoke `positions=3`.

Доказательство: `sed -n '420,444p' docs/superpowers/plans/2026-08-02-mt5-multi-position-refactor.md` показывает эти строки; `rg -n "def main|argparse" ML/baseline/run_mt5_batch.py` показывает фактический CLI `ML.baseline.run_mt5_batch`.

Почему важно: план должен быть воспроизводимым. Повреждённые команды и неверный ожидаемый результат делают последующий аудит и повторный запуск неоднозначными.

Рекомендуемое исправление: исправить команды на `./.venv/bin/python -m ML.baseline.run_mt5_batch --phase tester --max-positions=2` и аналогично для 16; заменить ожидаемые числа на проверяемые артефакты или явно указать, какой baseline даёт 102 сделки.

### 8. Улучшение: тесты не покрывают новую смысловую MQL5-логику

Место: `tests/test_mt5_batch_runtime_contract.py`, изменённые MQL5-файлы.

Суть проблемы: единственный изменённый Python-тест адаптирует mock `create_set_file` под новый аргумент. Нет теста/статического guard-а, который ловит legacy-блокер `while (... && BUY.Val==0)` в multi-pos режиме, side leak в `Close*Side(0)` или однотикетный lifecycle tracker.

Доказательство: `./.venv/bin/python -m pytest tests/test_mt5_batch_runtime_contract.py tests/test_parse_mt5_execution_report.py tests/test_mt5_signal_executor_schema.py -q` прошёл: `34 passed`. При этом найденные дефекты остаются в MQL5-коде, который эти тесты не исполняют.

Почему важно: прохождение текущих тестов создаёт ложное чувство завершённости этапа.

Рекомендуемое исправление: добавить хотя бы статические contract-тесты на текст MQL5 до появления полноценного MT5 integration test: запрет `while (... BUY.Val==0)` без ветки `MT5_MaxPositions`, проверка порядка side selection в `Close*Side`, проверка отсутствия одиночного `MT5_TrackedTicket` в multi-pos диагностике после следующего исправления.

### 9. Улучшение: `BuyPosCnt` в `INPUT.mqh` мёртвый и вводит в заблуждение

Место: `MT/MQL5/Include/INPUT.mqh:18-19`.

Суть проблемы: переменная `BuyPosCnt = CountActiveByType(MARKET)` не используется и комментарий признаёт, что это грубая оценка обеих сторон.

Доказательство: `rg -n "BuyPosCnt" MT/MQL5/Include/INPUT.mqh` находит только объявление.

Почему важно: в зоне gate-логики лишняя переменная мешает аудиту и может быть ошибочно принята за часть ограничения.

Рекомендуемое исправление: удалить `BuyPosCnt` и комментарий, оставить только `BuyActiveCnt`/`SelActiveCnt`.

### 10. Вопрос: тип `POSITION_TRACKER.ticket` остаётся `int`, хотя MT5 ticket - `ulong`

Место: `MT/MQL5/Include/FUNCTIONS.mqh:118`, `MT/MQL5/Include/ORDERS.mqh:77`, `MT/MQL5/Include/ORDERS.mqh:167`.

Суть проблемы: предупреждения компилятора связаны с преобразованием `ulong` в `int`. Отчёт называет это pre-existing, но новая структура `POSITION_TRACKER` закрепляет `int ticket` в центральном multi-position массиве.

Доказательство: compile log показывает `0 errors, 2 warnings`; `FUNCTIONS.mqh:118` задаёт `int ticket`, а `ORDERS.mqh:167` присваивает `OrderTicket()`.

Почему важно: если ticket выйдет за диапазон `int`, поиск позиции по ticket и lifecycle-связь сломаются. Даже если в текущем tester это маловероятно, multi-position refactor усиливает зависимость от ticket как основного ключа.

Рекомендуемое исправление: проверить совместимость MQL4Compat и, если возможно, перевести `ticket` и helper-аргументы на `ulong`. Если невозможно, явно оставить риск в отчёте с границами применимости.

## Проверки, выполненные аудитором

```bash
graphify query "MT5 multi-position refactor plan reports commits position lifecycle close policy ticket magic docs/superpowers/plans/2026-08-02-mt5-multi-position-refactor.md" --budget 2000
```

```bash
./.venv/bin/python -m pytest tests/test_mt5_batch_runtime_contract.py tests/test_parse_mt5_execution_report.py tests/test_mt5_signal_executor_schema.py -q
# 34 passed in 0.34s
```

```bash
git diff --check
# без вывода
```

```bash
iconv -f UTF-16LE -t UTF-8 /tmp/sosimple_mt5_compile.log | tail -n 20
# Result: 0 errors, 2 warnings, 5384 ms elapsed, cpu='X64 Regular'
```

## Что не удалось подтвердить

- Не подтверждён полный backcompat `InpMT5_MaxPositions=1`: доступный smoke подтверждает только `position_count=3` и `UNEXPLAINED=0`, а не идентичность всех событий и метрик.
- Не подтверждена работоспособность same-direction multi-position: max=2 остановлен на диагностическом слое, а код отправки ордеров содержит legacy-блокер.
- Не подтверждён `0 warnings` compile gate из методики: сохранённый лог содержит 2 warnings.

