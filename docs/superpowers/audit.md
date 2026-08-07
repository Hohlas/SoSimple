# Аудит плана `docs/superpowers/plans/2026-08-03-mt5-multi-position-closeout.md`

Дата аудита: 2026-08-07. Файл очищен и заполнен заново по запросу пользователя;
прежнее содержимое не читалось.

Все утверждения ниже проверены по фактическому состоянию репозитория
(ветка `mt5-execution-loop`, HEAD `8a85a87`). Метод: чтение файлов,
`rg`-поиск, запуск pytest, сверка с методикой.

## Статус выполнения плана (факт)

- Коммиты `4b7eddd` (Task 1), `b1a714d` (Task 2), `c9563fa` (Task 3) присутствуют.
- Task 4 НЕ выполнен: `MT/MQL5/Include/lib_ML_Signal.mqh:73` всё ещё содержит
  singleton `ulong MT5_TrackedTicket`; тест
  `test_diagnostic_lifecycle_uses_multi_ticket_tracker` падает.
- Task 5 НЕ выполнен: в `ML/baseline/run_mt5_batch.py` нет `build_arg_parser()`,
  `--force-rerun`, `--smoke-only`; `run_batch()` не принимает `force_rerun`
  (4 теста в `tests/test_mt5_batch_runtime_contract.py` падают с
  `TypeError: run_batch() got an unexpected keyword argument 'force_rerun'`).
- Tasks 6–9 НЕ выполнены: отчёт
  `docs/reports/2026-08-03-mt5-multi-position-closeout.md` отсутствует.
- Итог прогона: `./.venv/bin/python -m pytest tests/test_mt5_mql5_multiposition_contract.py tests/test_mt5_batch_runtime_contract.py -q`
  → 5 failed, 10 passed.

## Подтверждённые факты плана (сверено, замечаний нет)

- Task 2/3 уже отражены в коде: гейты `while (repeat>0 && CanPlaceBuyOrder())` /
  `CanPlaceSellOrder()` (`ORDERS.mqh:22,46`), `struct POSITION_TRACKER { ulong ticket; ... }`
  (`FUNCTIONS.mqh:118`), `FindPosIndexByTicket(ulong)` / `RemovePositionByTicket(ulong)`
  (`FUNCTIONS.mqh:171,162`), side-проверка до `if (price == 0)` в `CloseBuySide`/`CloseSellSide`
  (`OUTPUT.mqh:173-214`), `BuyPosCnt` и `CountActiveByType` удалены.
- Остаточные ticket-касты ровно там, где план обещает: только
  `(int)MT5_TrackedTicket` в `lib_ML_Signal.mqh:606,638`
  (команда `rg -n "\(int\)OrderTicket\(\)|\(int\)Pos\[|\(int\)ticket|\(int\)MT5_" MT/MQL5/Include/`).
- Утверждения Task 5 о текущем коде точны: skip-guard в `run_batch`
  (`run_mt5_batch.py:479-486`), smoke падает без entry CSV (`run_mt5_batch.py:431-434`),
  `--phase tester` всегда идёт в FULL BATCH (`run_mt5_batch.py:800-807`),
  `--phase`/`--max-positions` уже есть в `main()` (строки 771-773).
- Ограничения CLOSE-события соответствуют `docs/methodology/13b-mt5-execution-parity.md`
  (раздел «Ограничения прототипа»: `broker_history_limited`, ручная сверка
  `order_close_price`/`take_profit`/`swap`/`commission`). Ссылка на строки 138-141
  по порядку текста верна.
- Disclosure-блок методики 16 — ровно 8 полей без `roadmap_track`
  (`docs/methodology/16-reporting-audit.md:69-76`); решение плана НЕ добавлять
  `roadmap_track` корректно.
- Поломанные команды в старом плане существуют именно там, где заявлено
  (`docs/superpowers/plans/2026-08-02-mt5-multi-position-refactor.md:430,435,436,444`:
  `ML.baseline.tester`, `pythonスス...`, `mt5_exec_diagnostic --phase multi-pos-comparison`,
  «102 trades, same events»).
- Файл эксперта `$o$imple.mq5` существует; `InpiSignal=3` по умолчанию (строка 41).
- Monkeypatch-имена в тестах Task 1 Step 3 (`BATCH_DIR`, `TESTER_FILES`,
  `make_run_id`, `create_set_file`, `create_ini_file`, `wait_for_liveupdate_clear`,
  `copy_entry_signal_file`, `run_tester`, `parse_events`) существуют в модуле.

---

## Замечания

### 1. КРИТИЧНО — Task 7 Step 5: проверка связки сигнал→тикет использует несуществующую колонку `idx`

- Место: план, Task 7 Step 5 (строки ~1225-1243).
- Суть: скрипт делает `sig = events[["event", "ticket", "idx"]]` и
  `lifecycle.groupby("ticket")["idx"].nunique()`. Колонки `idx` в CSV событий нет:
  заголовок writer-а — `event,time,feature_time,...,request_seq,...,comment`
  (`MT/MQL5/Include/lib_ML_Signal.mqh:300`). Сигнальный индекс пишется в колонку
  `request_seq`: все вызовы `MT5_ML_LogEvent(..., idx, magic, Symbol(), ...)`
  попадают в параметр `request_seq` (сигнатура `lib_ML_Signal.mqh:253-289`,
  хвостовые параметры по умолчанию: `error_code, error_class, retcode,
  retcode_text, request_seq, magic, symbol_name, entry_type`; существующие
  вызовы — строки 612, 628, 631, 642).
- Доказательство: `lib_ML_Signal.mqh:300` (заголовок без `idx`); вызовы 612/628/631/642;
  `ML/baseline/parse_mt5_execution_report.py:17` (`"request_seq": -1` в схеме).
- Почему важно: это единственная проверка пункта аудита V3 (уникальность связки
  сигнал→тикет при multi-position). В текущем виде скрипт упадёт с `KeyError`,
  и пункт Completion Criteria про `binding_violations: 0` невыполним.
- Исправление: зафиксировать в Task 4, что сигнальный индекс читается из
  `request_seq`, и переписать Task 7 Step 5 на колонку `request_seq`
  (с фильтром `request_seq >= 0`); либо добавить настоящую колонку `idx`
  в writer и в заголовок (тогда нужен отдельный шаг про перезапись заголовка,
  т.к. он пишется только при `FileSize(handle) == 0`).

### 2. КРИТИЧНО — Task 4: удаление singleton-состояния не покрывает все места использования `MT5_TrackedMagic`

- Место: план, Task 4 Step 1 и Step 6.
- Суть: Step 1 заменяет блок из четырёх переменных, включая `int MT5_TrackedMagic = 0;`,
  а Step 6 удаляет лишь присваивание `MT5_TrackedMagic = Mgc;` (нынешняя строка 764).
  Переменная используется ещё в местах, которые план не трогает:
  `lib_ML_Signal.mqh:185`, `308` (`MT5_OpenPositionsForMagic(MT5_TrackedMagic)` —
  от этого зависит колонка `open_positions` каждого события), `309` (fallback
  `event_magic`), `407`.
- Доказательство: `rg -n "MT5_TrackedMagic" MT/MQL5/Include/` → строки 74, 185, 308, 309, 407, 592, 764.
- Почему важно: после Step 1 код не скомпилируется (неопределённый идентификатор),
  т.е. compile gate Task 6 Step 3 провалится. Если же «тихо» оставить переменную,
  `open_positions` будет считаться для magic=0 и колонка будет давать неверные
  значения в multi-pos режиме.
- Исправление: добавить в Task 4 шаг «обновить `MT5_ML_LogEvent` и прочие точки
  использования `MT5_TrackedMagic` на per-event `magic`» и перечислить строки
  185, 308, 309, 407 явно.

### 3. ВАЖНО — «0 warnings» недостижим без правки `MQL4Compat.mqh`, а план её не включает

- Место: план, Global Constraints (строка 18), Task 4 Step 4/4b; факт —
  `MT/MQL5/Include/MQL4Compat.mqh:309,313,456`.
- Суть: план утверждает «MT5 `OrderSelect` принимает `ulong` напрямую» и требует
  убрать явные касты `(int)ticket`. Но весь код компилируется через макрос
  `#define OrderSelect OrderSelect_MQL4` (`MQL4Compat.mqh:456`), а сигнатура
  `bool OrderSelect_MQL4(int index, ...)` принимает ticket как `int`.
  Передача `ulong ticket` без каста — неявное сужение `ulong → int`,
  тот же класс предупреждений «possible loss of data». `MQL4Compat.mqh`
  отсутствует в File Structure плана.
- Доказательство: `MQL4Compat.mqh:309` (`int index`), `:313` (`ulong ticket = (ulong)index;`), `:456` (макрос).
- Почему важно: критерий Completion Criteria «0 errors, 0 warnings» логически
  невыполним в рамках заявленного набора файлов; исполнитель упрётся в
  неразрешимое противоречие или молча примет предупреждения.
- Исправление: добавить в Task 4 модификацию `MQL4Compat.mqh` (вариант
  `OrderSelect` с `ulong ticket` для `SELECT_BY_TICKET`) и включить файл в
  File Structure; либо честно разрешить статус `PASS_WITH_WARNINGS` для этого
  класса предупреждений и снять требование «0 warnings».

### 4. ВАЖНО — код теста в тексте Task 1 Step 1 содержит синтаксическую ошибку Python

- Место: план, Task 1 Step 1, строки ~141-142.
- Суть: regex-литералы в тексте плана сломаны:
  `re.compile(r"while\s*\(\s*repeat\s*>\s*0\s*&&\s*BUY\.Val\s*==\s*0'")`
  (лишняя `'` перед закрывающей `"`, скобка паттерна не закрыта).
  Коммит `4b7eddd` записал корректную версию
  (`...==\s*0\s*\)`, см. `tests/test_mt5_mql5_multiposition_contract.py:67-68`),
  т.е. исполнитель уже исправлял план на ходу, но текст плана не обновлён.
- Доказательство: сравнение строк 141-142 плана и строк 67-68 коммитнутого теста.
- Почему важно: план перечитывается исполнителями; буквальный перенос кода
  даст `SyntaxError` на этапе сбора тестов, а расхождение «план vs коммит»
  подрывает воспроизводимость.
- Исправление: заменить обе строки в плане на фактически закоммиченный вариант.

### 5. ВАЖНО — sentinel `DATETIME_MAX` не определён в дереве MT, а предложенные альтернативы неверны

- Место: план, Task 4 Step 3 (строки ~654-691).
- Суть: `MT5_FindFilledTicketForSignal` использует `DATETIME_MAX` как «верхней
  границы нет», а примечание плана предлагает «использовать `(datetime)0` или
  `TimeCurrent()+PERIOD_*`» как эквиваленты. `(datetime)0` — нижняя граница
  времени, а не верхняя; подстановка его как sentinela «без ограничения»
  инвертирует условие `if (hi < DATETIME_MAX && ot >= hi) continue;`.
- Доказательство: `rg -n "DATETIME_MAX" MT/` → 0 совпадений (факт). Отсутствие
  такого предопределённого идентификатора в самом языке MQL5 — моя проверка по
  документации не выполнялась, помечаю как гипотезу; но в репо константы нет,
  значит компиляция предложенного кода упадёт в любом случае.
- Почему важно: функция — ядро mitigation пункта V3 (окно привязки fill→signal);
  неверный sentinel ломает фильтрацию кандидатов.
- Исправление: определить локальную константу (например
  `const datetime MT5_NO_HI_BOUND = D'2100.01.01';`) и использовать её, либо
  отдельный флаг `bool has_hi`; убрать вариант с `(datetime)0`.

### 6. УЛУЧШЕНИЕ — Task 1 Step 1: усиление A5 фактически не проверяет компакцию

- Место: план, строка ~181; тест `tests/test_mt5_mql5_multiposition_contract.py:107`.
- Суть: `assert "MT5_TrackedPositionCount--" in ml_signal or "close_logged" in ml_signal`
  проходит, если в файле есть просто слово `close_logged` (оно появляется уже
  в объявлении структуры из Task 4 Step 1), т.е. swap-remove компакция не проверяется.
- Исправление: убрать ветку `or`, оставить только `"MT5_TrackedPositionCount--"`,
  либо проверять `ArrayResize(MT5_TrackedPositions, MT5_TrackedPositionCount)`.

### 7. УЛУЧШЕНИЕ — Task 8 Step 2: строка для замены цитируется неточно

- Место: план, Task 8 Step 2.
- Суть: план предлагает заменить «not a bug refactoring plan», но фактическая
  формулировка в отчёте на русском: «Это архитектурное ограничение диагностического
  слоя executor-а, а не баг» (`docs/reports/2026-08-02-mt5-multi-position-probe.md:158`).
  Буквальный поиск строки из плана ничего не найдёт.
- Исправление: привести точную цитату и номер строки.

### 8. УЛУЧШЕНИЕ — мелкий сдвиг номеров строк `INPUT.mqh`

- Место: план, Scope (строка 26), Task 2 Step 2 (комментарий про «INPUT.mqh:18-32»).
- Суть: MARKET-фильтр фактически в `INPUT.mqh:16-27` (сброс `set.BUY`/`set.SEL` —
  строки 13-14, тут план точен; условие `Pos[i].data.Typ != MARKET` — строка 18,
  верхняя граница 27, а не 32).
- Доказательство: чтение `MT/MQL5/Include/INPUT.mqh`.
- Исправление: поправить диапазон на 16-27 либо убрать конкретные номера.

### 9. ВОПРОС — где физически искать `ambiguous_fills_in_window`

- Место: план, Task 7 Step 5 (последний абзац).
- Суть: «grep the MT5 tester log / journal» — в Wine-окружении журнал тестера
  лежит внутри `WINEPREFIX` (`/home/hohla/.mt5/...`), точный путь не указан.
  `Print()` в тестере попадает в journal, а не в событийный CSV, поэтому без
  явного пути шаг невыполним «как написано».
- Исправление: зафиксировать точный путь к журналу тестера
  либо дублировать WARN-строки в событийный CSV (например `event=WARN`).

### 10. ВОПРОС — воспроизводимость ссылок на `docs/superpowers/audit.md`

- Место: план, строки 5, 1356; Completion Criteria; Task 9 Step 2.
- Суть: план ссылается на пункты прежнего аудита U2/U4/U5, V1-V3, A4-A14, K1/K2
  и «audit items 1-10» из `docs/superpowers/audit.md`. По требованию пользователя
  этот файл полностью очищен данным аудитом; старые идентификаторы пунктов
  больше не читаются из репо (восстановимы только из git-истории).
- Почему важно: будущий исполнитель плана не сможет сопоставить строки
  «Audit Findings Addressed» с исходными формулировками без обращения к истории.
- Исправление: в Task 9 Step 2 отчёта closeout встраивать краткую цитату каждого
  пункта аудита, а не только номер; либо зафиксировать SHA коммита со старым audit.md.

## Вне плана (наблюдение, не замечание плану)

В истории ветки присутствуют коммиты, выглядящие как служебные/шаблонные и не
относящиеся к задаче: `f0d2067 "Implement new feature for user authentication..."`,
`7a27666 "fix: enhance MT5 multi-position close helpers..."` (дубль содержания
`c9563fa`). При закрытии ветки стоит решить, оставлять ли их в истории
(решение за пользователем; самостоятельно историю не трогаю).

## Итог

- Структура плана, покрытие пунктов прежнего аудита, дисциплина DIAGNOSTIC_ONLY и
  соответствие методикам 13b/16 — корректны; большинство фактических утверждений
  о коде подтверждено (см. раздел «Подтверждённые факты»).
- Два критичных дефекта делают план невыполнимым «как написано»: проверка V3
  ссылается на несуществующую колонку `idx` (фактически данные лежат в
  `request_seq`), а удаление `MT5_TrackedMagic` оставляет незакрытые
  использования (компиляция упадёт).
- Одно важное противоречие: gate «0 warnings» требует правки `MQL4Compat.mqh`,
  которая не входит в File Structure плана.
- Tasks 4-9 на момент аудита не выполнены; фактическое состояние репозитория
  соответствует завершённым Tasks 1-3 (тесты Task 1 Step 3 написаны вперёд и
  закономерно падают до Task 5).
