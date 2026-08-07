# Аудит плана: 2026-08-03-mt5-multi-position-closeout.md

> Дата аудита: 2026-08-07 · Предмет: `docs/superpowers/plans/2026-08-03-mt5-multi-position-closeout.md` (1299 строк).
> Метод: доказательная проверка каждого утверждения плана по фактическому коду, документам, методикам и git. Каждое замечание содержит важность, место, суть, доказательство, причину и исправление.

## Резюме

План в целом реализуем и корректно диагностирует состояние кода: все базовые предпосылки подтверждены фактами (legacy-гейт открытия, порядок side-check в закрытии, single-ticket трекер, доказательство backcompat через SKIP, битые команды в старом плане). НО обнаружены **2 материальных дефекта** и ряд важных/улучшающих замечаний:

- **КРИТИЧНО**: план ссылается на несуществующее требование методики 16 (`roadmap_track`) и указывает несуществующий трек в roadmap.
- **КРИТИЧНО/ВАЖНО**: команды Task 6 Step 5/6 (`--phase tester`) запускают не только smoke, но и полный batch из 32 кандидатов — ожидания плана о «лёгкой» проверке не соответствуют поведению `main()`.
- **ВАЖНО**: `include_pending` в предлагаемом `CountActiveBySide` фактически не учитывает отложенные ордера (мёртвый параметр).
- **ВАЖНО**: привязка «сигнал → тикет» в `MT5_FindFilledTicketForSignal` может перепутать тикеты между сигналами при мультипозиции.

---

## Проверенные подтверждённые предпосылки (факты, совпадающие с планом)

1. Legacy-гейт открытия существует: `while (repeat>0 && BUY.Val==0)` — `MT/MQL5/Include/ORDERS.mqh:22`; `while (repeat>0 &&  SEL.Val==0)` — `ORDERS.mqh:46` (два пробела, как в тесте плана).
2. Порядок в close-хелперах ошибочен: `if (price == 0) { Pos[i].data.Val = 0; continue; }` стоит **до** `PositionSelectByTicket`/side-check в `OUTPUT.mqh:176` (CloseBuySide) и `OUTPUT.mqh:212` (CloseSellSide) — соответствует аудит-замечанию №2.
3. Single-ticket трекер существует: `MT5_TrackedTicket/MT5_TrackedMagic/MT5_TrackedIdx/MT5_TrackedOpenLogged` — `lib_ML_Signal.mqh:73-76`; касты `OrderSelect((int)MT5_TrackedTicket, ...)` — `lib_ML_Signal.mqh:606,638`; `MT5_TrackedMagic = Mgc;` — `lib_ML_Signal.mqh:764`.
4. `struct POSITION_TRACKER { int ticket; ... }` и helpers с `int ticket` — `FUNCTIONS.mqh:118,162,171`; единственный lossy-каст через helper: `FindPosIndexByTicket(OrderTicket())` — `ORDERS.mqh:77`.
5. Backcompat доказывался через SKIP: `run_batch` пропускает при `UNEXPLAINED==0` — `ML/baseline/run_mt5_batch.py:481-486`; в старом отчёте строка «metrics untouched (SKIPPED paths). PASS» — `docs/reports/2026-08-02-mt5-multi-position-probe.md:167`.
6. Битые команды в старом плане существуют: `ML.baseline.tester` — `plans/2026-08-02...refactor.md:435`; `pythonスス...` — `:436`; `mt5_exec_diagnostic --phase multi-pos-comparison` — `:444`; критерий «102 trades, same events» — `:430`.
7. Оверклеймы старого отчёта существуют: «identical» — `probe.md:26,166`; «Canonical guarantee ... подтверждена» — `probe.md:130-131`; compile-статусы «PASS, 0 errors N warnings» — `probe.md:54-59`.
8. Имя входного параметра `InpMT5_MaxPositions` корректно: `$o$imple.mq5:79`; runtime-глобал `MT5_MaxPositions=1` — `:114`; синк `MT5_MaxPositions=InpMT5_MaxPositions` — `:128`. `create_set_file` пишет именно `InpMT5_MaxPositions=` — `run_mt5_batch.py:278`.
9. Битые/существующие артефакты: `tests/test_mt5_batch_runtime_contract.py`, `tests/test_parse_mt5_execution_report.py`, `tests/test_mt5_signal_executor_schema.py` существуют; файла `tests/test_mt5_mql5_multiposition_contract.py` нет (создаётся).
10. Все helper-символы, на которые опирается новый код Task 4, существуют: `DiagnosticMlExitScore` (`:191`), `MT5_CalculateOpenPositionFeatures` (`:202`), `MT5_FindActiveTicket` (`:118`), `MT5_LogSignalEvent` (`:371`), `MT5_RegisterPosition(ulong,int)` (`:84`), `MT5_ML_LogEvent` (`:253`), массивы `MT5_Sides[]/MT5_DecisionTimes[]/MT5_RuleIds[]` (`:59-61`).
11. Разделитель событий `;` соответствует методике (`docs/methodology/13b-mt5-execution-parity.md:73`) и коду Task 7.

---

## Замечания

### КРИТИЧНО

#### К1. Выдуманное требование методики: `roadmap_track` не входит в disclosure методики 16
- **Место**: Task 8 Step 3 (`:1121-1130`), шаблон отчёта Task 9 Step 1 (`:1169`), Completion Criteria (`:1280`).
- **Суть**: план утверждает: «`roadmap_track` is required by `docs/methodology/16-reporting-audit.md` disclosure; it references the named track in `docs/superpowers/roadmap.md`». Это не подтверждено фактом — в методике 16 нет такого поля.
- **Доказательство**: `rg -c "roadmap_track" docs/methodology/16-reporting-audit.md` → 0 совпадений (exit=1). Блок disclosure в методике (`docs/methodology/16-reporting-audit.md:64-77`) содержит ровно: `lifecycle_status`, `origin_bias`, `research_priority`, `current_search_budget`, `cumulative_search_budget`, `next_probe_freeze`, `allowed_max_verdict`, `forbidden_interpretations`. `roadmap_track` отсутствует.
- **Почему важно**: ложное обоснование вносит в отчёт обязательное поле, которое (а) не требуется методикой и (б) ссылается на трек, которого нет в roadmap (см. К2). Это противоречит требованию AGENTS.md давать «точный ответ на основе проверенных фактов» и создаёт рассинхрон между отчётом и roadmap.
- **Исправление**: либо удалить `roadmap_track` из шаблона, критериев и Task 8 Step 3; либо — если оставить — добавить реальный именованный трек в `roadmap.md` (Task 9 Step 4) и указать существующее имя, а не выдуманное.

#### К2. Значение `roadmap_track: mt5-execution-closeout` ссылается на несуществующий трек
- **Место**: Task 8 Step 3 (`:1127`), Task 9 Step 1 (`:1169`), Task 9 Step 4 (`:1247`).
- **Суть**: поле заполняется значением `mt5-execution-closeout`, однако в `docs/superpowers/roadmap.md` такого трека нет; ACTIVE-трек называется «MT5 entry mechanics / trade-count frozen probe» (`roadmap.md:15-17`).
- **Доказательство**: `rg -n "mt5-execution|closeout" docs/superpowers/roadmap.md` → 0 совпадений. При этом Task 9 Step 4: «Update roadmap only if the closeout changes the ACTIVE track. If only smoke passed, do not change the roadmap direction» — то есть при закрытии только smoke-результатом roadmap не меняется, и значение `roadmap_track: mt5-execution-closeout` остаётся висячей ссылкой. Дополнительно правило roadmap — «только один ACTIVE-трек за раз» (`roadmap.md:9,162`).
- **Почему важно**: отчёт закрытия этапа со ссылкой на несуществующий трек нарушает целостность навигации проекта (STRUCT-несоответствие по классификации AGENTS.md) и противоречит собственной ссылке плана «references the named track in roadmap.md».
- **Исправление**: согласовать с К1: либо убрать поле, либо ввести в roadmap именованный трек `mt5-execution-closeout` и явно указать, в каком статусе он находится (ACTIVE/BACKLOG), не нарушая правило одного ACTIVE.

### ВАЖНО

#### В1. Команды Task 6 Step 5/6 запускают полный batch, а не только smoke
- **Место**: Task 6 Step 4-6 (`:920-959`), Task 5 Step 3 (`:793-794`).
- **Суть**: план ожидает от `--phase tester --max-positions=2 --force-rerun` «smoke metrics parse successfully» и «If this fails, stop. Do not run max=16 or aggregate» — как от лёгкой проверки. Реально `main()` для `--phase tester` выполняет compile + smoke **и затем полный batch всех кандидатов** (`run_batch`), а с `--force-rerun` SKIP-гейт инертен для всех 32 кандидатов.
- **Доказательство**: `ML/baseline/run_mt5_batch.py:789-807` — блок `if args.phase in ("tester","all")`: smoke, затем `print("--- FULL BATCH ---"); run_batch(candidates, max_positions=...)`. `--force-rerun` (Task 5 Step 4) как раз отключает SKIP, то есть заставляет каждый кандидат прогонять тестер. Task 6 Step 5 «If this fails, stop» физически невозможно остановить на границе smoke без прерывания batch.
- **Почему важно**: исполнитель либо потеряет часы на 32 тестерных прогона на каждом max=2 и max=16, либо не сможет выполнить инструкцию «остановиться после smoke»; ожидания плана не соответствуют поведению кода.
- **Исправление**: ввести smoke-only режим (например, флаг `--smoke-only` или фазу `--phase smoke` в `main()`), либо переформулировать Task 6 Step 5/6 так, чтобы они явно требовали только smoke (отдельной командой), а полный batch выносился в Task 7 Step 4 как осознанное отдельное решение с указанием стоимости.

#### В2. `include_pending` в `CountActiveBySide` — мёртвый параметр: отложенные ордера не учитываются
- **Место**: Task 2 Step 2 (`:334-345`), Task 2 Step 3 (`:352-361`).
- **Суть**: `CanPlaceBuyOrder()` вызывает `CountActiveBySide(POSITION_TYPE_BUY, true)` с намерением учитывать отложенные ордера (pending) в лимит. Но `PositionSelectByTicket()` выбирает только **позиции** (market), отложенный **ордер** (OP_BUYLIMIT/OP_BUYSTOP/…) этой функцией не выбирается → `continue`, и pending не засчитывается при любом значении `include_pending`.
- **Доказательство**: код плана `if (!PositionSelectByTicket(Pos[i].ticket)) continue;` для pending-записи с `data.Typ != MARKET` всегда вернёт false (MT5: PositionSelectByTicket по тикету ордера не находит позицию). Семантика «include_pending=true» ни на что не влияет. Параллельно существующие счётчики считают только MARKET: `INPUT.mqh:20-27` (`Pos[i].data.Typ != MARKET`), `lib_ML_Signal.mqh` (`mt5_buy_cnt`, `same_dir_cnt`).
- **Почему важно**: расхождение между заявленной и фактической семантикой гейта: при висящем отложенном ордере + открытой market-позиции в ту же сторону вход может быть разрешён (пока market < MaxPositions), хотя по замыслу pending должен занимать слот. Влияет на интерпретацию smoke max=2 (количество одновременных позиций) и честность вывода.
- **Исправление**: реализовать учёт pending через `OrdersTotal()/OrderSelect(SELECT_BY_POS, MODE_TRADES)` + `OrderType()` в наборе `{OP_BUYLIMIT, OP_BUYSTOP, OP_SELLLIMIT, OP_SELLSTOP}` и сторону, либо убрать параметр и явно задокументировать «только market-позиции».

#### В3. Привязка «сигнал → тикет» в `MT5_FindFilledTicketForSignal` может перепутать тикеты между сигналами
- **Место**: Task 4 Step 3 (`:587-603`).
- **Суть**: функция возвращает первый **неотслеженный** market-ордер с подходящим magic и типом, открытый после `MT5_DecisionTimes[idx]`. При нескольких одновременных сигналах одного magic (мультипозиция) порядок обхода `OrdersTotal()` не гарантирует соответствие порядку сигналов, поэтому тикет сигнала N может быть привязан к позиции сигнала N+1 (и наоборот).
- **Доказательство**: код плана `for (int i = 0; i < OrdersTotal(); i++) { if (OrderSelect(i, ...) != true) continue; ... if (OrderOpenTime() < MT5_DecisionTimes[idx]) continue; return ticket; }` — выбирается первый по порядку обхода, порядок тикетов не обязан совпадать с порядком решений. Отфильтровываются только уже отслеженные (`FindTrackedIndexByTicket >= 0`).
- **Почему важно**: весь диагностический вывод (timing-contract `decision_time <= execution_time`, выравнивание фич) зависит от корректной связки сигнал→тикет. При неверной привязке smoke max=2/max=16 может дать ложные нарушения или ложное их отсутствие, а отчёт не сможет это отличить.
- **Исправление**: либо привязываться к уникальному идентификатору из комментария ордера/сигнала, либо валидировать попадание `OrderOpenTime()` в окно `[DecisionTimes[idx], следующий decision_time)` и фиксировать неоднозначности в отчёте; добавить в Task 7 сверку «каждый tracked тикет соответствует ровно одному сигналу».

#### В4. Task 5 выдаёт `--max-positions` и `--phase` за новые, хотя они уже существуют
- **Место**: Task 5 Step 1 (`:754-773`), Task 1 Step 4 (`:284-287`).
- **Суть**: план строит `build_arg_parser()` с `--phase` и `--max-positions` как часть «нового» кода и ожидает FAIL на их отсутствие. Фактически `--phase`, `--max-positions`, `max_positions` у `run_smoke_test`/`run_batch` и инъекция `InpMT5_MaxPositions` уже реализованы; новыми являются только `--force-rerun` и сам `build_arg_parser`.
- **Доказательство**: `run_mt5_batch.py:771-778` (уже есть `--phase`, `--max-positions`), `:425` и `:467` (уже `*, max_positions=1`), `:278` (уже `InpMT5_MaxPositions=`). Формулировка Task 1 Step 3/4 «`build_arg_parser()` / `--force-rerun` do not exist yet» верна только для этих двух сущностей.
- **Почему важно**: исполнитель может запутаться в объёме работ; при буквальном выполнении «добавить build_arg_parser» рядом с уже существующим инлайн-парсером появится дублирование (хотя Step 2 и предписывает замену).
- **Исправление**: в Task 5 явно указать: «уже существуют — только добавить `--force-rerun` и вынести парсер в `build_arg_parser()`».

### УЛУЧШЕНИЕ

#### У1. Тайпографика/опечатки
- **Место**: Completion Criteria (`:1281`).
- **Суть**: «Catss `(int)` not found» — опечатка (должно быть «Casts»).
- **Исправление**: поправить слово.

#### У2. Жёсткость строковых тестов на пробелы
- **Место**: Task 1 Step 1 (`:133-134`).
- **Суть**: негативные проверки опираются на точные строки `while (repeat>0 && BUY.Val==0)` и `while (repeat>0 &&  SEL.Val==0)` (разное число пробелов). Это корректно для текущего кода, но при переформатировании (например, `while(repeat>0 && BUY.Val==0)`) тест «пройдёт вхолостую», а регресс гейта останется незамеченным.
- **Доказательство**: `ORDERS.mqh:22` (один пробел) и `:46` (два пробела) — совпадает с тестом сегодня, но хрупко по дизайну.
- **Исправление**: использовать нормализованное регулярное выражение (например, `while\s*\(\s*repeat\s*>\s*0\s*&&\s*BUY\.Val\s*==\s*0`) для негативной проверки; позитивная проверка (`CanPlaceBuyOrder()`) уже устойчива.

#### У3. Прекондиция smoke: требуются заранее сгенерированные сигналы
- **Место**: Task 6 Step 4 (`:920-932`).
- **Суть**: `run_smoke_test` возвращает False «entry CSV not found», если `BATCH_DIR/<run_id>/entry_signals.csv` отсутствует (`run_mt5_batch.py:431-434`). План не указывает, что перед `--phase tester` нужно выполнить `--phase signals`.
- **Исправление**: добавить в Task 6 прекондицию (сгенерировать сигналы) либо отметить зависимость от ранее сохранённых сигналов.

#### У4. Мёртвый `CountActiveByType` после удаления `BuyPosCnt`
- **Место**: Task 3 Step 3 (`:468-482`).
- **Суть**: единственная точка использования `CountActiveByType(MARKET)` — удаляемая строка `INPUT.mqh:18`. После удаления метод `FUNCTIONS.mqh:176` остаётся неиспользуемым.
- **Исправление**: либо удалить `CountActiveByType`, либо явно указать, что он сохраняется намеренно (риск предупреждения компилятора на «0 warnings»-гейте).

#### У5. Область поиска кастов в Task 2/Task 4 неполна по файлам
- **Место**: Task 2 Step 5b (`:401-409`), Task 4 Step 4b (`:666-676`).
- **Суть**: greps проверяют `ORDERS.mqh`, `ERRORs.mqh` и `lib_ML_Signal.mqh`. Остальные потребители `Pos[i].ticket` (`OUTPUT.mqh`, `COUNT.mqh`, `lib_ML_Signal_TB.mqh`, `INPUT.mqh`, `MODIFY`) не перечислены. По факту lossy-касты тикетов найдены только в `lib_ML_Signal.mqh:606,638` (остальные `(int)` — это `(int)OrderMagicNumber()`, не тикет: `SERVICE.mqh:761`, `ORDERS.mqh:258`, `MQL4Compat.mqh:491`), поэтому риск низкий, но покрытие стоит расширить.
- **Исправление**: в Step 4b использовать `rg -n "\(int\)OrderTicket\(\)|\(int\)Pos\[|\(int\)ticket|\(int\)MT5_" MT/MQL5/Include/` и добавить сверку после миграции `ulong ticket`.

---

## Семантические проверки предлагаемого кода (смысловой уровень)

### S1. `test_run_batch_force_rerun_overrides_skip_when_unexplained_zero` (Task 1 Step 3) — корректен
- Фикстура создаёт `entry_signals.csv` в `out_dir` (`:222`), поэтому после удаления metrics/events поток `run_batch` доходит до `run_tester`. Утверждение `calls["run_tester"] == 1` достижимо. Обратный тест (SKIP без force_rerun) также корректен: SKIP-гейт `run_mt5_batch.py:481-486` совпадает с ожиданием.
- Вывод: TDD-цикл Task 1 Step 3/4 выполним.

### S2. Компактирование массива в `MT5_LogLifecycleForTicket` + цикл Step 5 — согласованы
- Swap-remove (`last` на `tracked_i`, `MT5_TrackedPositionCount--`) и повторная проверка индекса `if (MT5_TrackedPositionCount < before) i--` корректны: после удаления слот `i` содержит перемещённый элемент, и он перепроверяется.

### S3. `_body()` в статическом тесте — рабочий для целевых функций
- Якоря `void EXPERT::CloseBuySide`, `void EXPERT::CloseSellSide`, `void EXPERT::CLOSE_BUY` и `SET_BUY/SET_SEL/MODIFY` соседствуют без промежуточных функций, поэтому поиск «первой сигнатуры после якоря» возвращает корректное тело (`OUTPUT.mqh:173-208-245`, `ORDERS.mqh:22-46-?`).

### S4. Прямая проверка side-before-zero (Task 3) — тест сегодня падает, после фикса пройдёт
- `output.index("pt != POSITION_TYPE_BUY")` (после фикса — до `price == 0`) соответствует новому порядку. Текущий код: `price == 0` на `OUTPUT.mqh:176` раньше side-check на `:179`. TDD-предпосылка верна.

### S5. Барьер `0 warnings` достижим
- Установлено: единственные lossy-касты тикетов — `lib_ML_Signal.mqh:606,638` и передача `OrderTicket()` (ulong) в `FindPosIndexByTicket(int)` (`ORDERS.mqh:77`). После Task 2 Step 1/Step 5 и Task 4 Step 4b гейт `0 errors, 0 warnings` правдоподобен; пункт про `PASS_WITH_WARNINGS`/`FAIL` в Task 6 Step 3 предусмотрен.

### S6. Предложенная логика входного гейта не ломает single-position (обратная совместимость)
- `CanPlaceBuyOrder()` при `MT5_MaxPositions==1` возвращает `BUY.Val == 0`, то есть воспроизводит legacy-условие цикла (`ORDERS.mqh:22`). Соответствует Global Constraint «`=1` обязан сохранить single-position поведение».

---

## Вывод

План можно исполнять после устранения К1/К2 (согласование `roadmap_track` с методикой и roadmap) и уточнения В1 (smoke vs full batch в Task 6). Замечания В2-В4, У1-У5 не блокируют, но должны быть отражены в отчёте Task 9 как ограничения/решения. Базовый диагноз плана подтверждён кодом; архитектура исправлений (четыре слоя) корректна.
