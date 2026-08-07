# Аудит плана `docs/superpowers/plans/2026-08-03-mt5-per-expert-ml-tracker.md`

Дата аудита: 2026-08-06. Объект: per-expert plan (2145 строк).
Метод: все цитируемые файлы/строки проверены точечно (`rg`, `Read`, `git log/show`), утверждения о поведении — чтением тел функций. Ниже только подтверждённые факты; гипотезы помечены явно.

---

## 0. Текущее состояние: precondition closeout НЕ исполнен

План сам вводит гейт Task P0. Повторная проверка его команд на текущем HEAD (`mt5-execution-loop`):

| Проверка P0 | Ожидание плана | Факт | Итог |
|---|---|---|---|
| `rg "MT5_TrackedTicket\b" lib_ML_Signal.mqh` | 0 строк | 10 строк (73, 591, 595, 606, 612, 628, 631, 638, 642, 644) | FAIL |
| `rg "MT5_TRACKED_POSITION\|MT5_TrackedPositions\|MT5_LogLifecycleForTicket"` | ≥4 строк | 0 строк | FAIL |
| `rg "(int)OrderTicket()\|(int)ticket\|(int)MT5_TrackedTicket"` | 0 строк | 2 строки (`lib_ML_Signal.mqh:606, 638`: `OrderSelect((int)MT5_TrackedTicket, ...)`) | FAIL |
| `rg "force_rerun" run_mt5_batch.py` | не 0 | 0 строк | FAIL |

Дополнительно:
- Отчёт closeout `docs/reports/2026-08-03-mt5-multi-position-closeout.md` отсутствует (`ls docs/reports/` — последний отчёт `2026-08-02-mt5-multi-position-probe.md`).
- Closeout-план в рабочем дереве модифицирован (`git diff --stat`: +271/−33), 55 чекбоксов `[x]` и 54 `[ ]` — исполнение не завершено и не закоммичено.
- `git show 54b4089` — коммит добавил только документ closeout-плана, без кода.

**Вывод:** по собственной логике плана (Task P0 Step 2) план BLOCKED. Гейт написан корректно и это состояние ловит — но любой исполнитель обязан остановиться на P0. Все дальнейшие замечания относятся к содержанию плана, а не к возможности его запуска сегодня.

---

## 1. Проверено и подтверждено (план точен)

- `MT5_FindEntrySignal(datetime barTime)` — один аргумент, `lib_ML_Signal.mqh:128` ✓ (план: 128).
- `MT5_LogLifecycleForCurrentState(int magic, int &ml_close_order_type)` — строка 582; блок «Было» в Task 6 Step 6 совпадает с фактическим кодом 585–602 ✓.
- `EXPERT::ML_TRADE` — строка 758; вызов `MT5_FindEntrySignal(Time[bar])` на 777; блоки записи singleton на 833–835 и 851–853 ✓.
- `MT5_ENTRY_INIT` (493) читает 11 колонок, `rule_id` — 5-я колонка (чтение 524, хранение 554) ✓. CSV грузится целиком, без фильтра ✓.
- `MT5_DiagSignalsLoaded` — глобальная (`lib_ML_Signal.mqh:68`), загрузка CSV один раз на сессию ✓.
- Событийный лог уже несёт `rule_id` и `magic`: `MT5_LogSignalEvent` (371) передаёт `MT5_RuleIds[idx]`; `MT5_ML_LogEvent` пишет оба поля (612) ✓. Схема event CSV в `docs/methodology/13b-mt5-execution-parity.md:73` содержит `rule_id;...;magic` ✓ — Task 7 опирается на реально существующие колонки.
- `make_run_id` даёт ровно `"fractal0_entry_quality_v1_12h_thr0.5"` для теста Task 1 (`run_mt5_batch.py:46-47`) ✓.
- `rule_id=run_id` в генерации (`run_mt5_batch.py:142`) ✓.
- `export_mt5_entry_signals(source, output_csv, output_json, max_fill_lag_bars, latency_bars=0, *, source_csv, rule_metadata, run_id, label)` (`export_mt5_entry_signals.py:196-207`) — вызовы из Task 4/Task 5 сигнатурно совместимы ✓. `OUTPUT_COLUMNS` содержит `rule_id` (`prepare_mt5_entry_source.py:22-30`) ✓.
- `reconcile_positions` возвращает `dict` с `class_counts` и `unexplained_position_ids` (`parse_mt5_execution_report.py:63-99`) — `sub_recon.get("class_counts", {})` в Task 7 корректно ✓.
- `_event_row(event, time, **overrides)` в `tests/test_parse_mt5_execution_report.py:12` принимает `ticket/magic/rule_id` ✓.
- `MT5_SIGNAL_COLUMNS` (`mt5_signal_schema.py:5-17`) = 11 колонок; `MT5_ENTRY_INIT` скипает 11 заголовочных (`for h < 11`) ✓ — синхронизация Python/MQL5 есть.
- Цитаты 13b: лимитные входы (41), event-схема (73), timing-контракты (79, 85), `broker_history_limited` (139), compile gate «Result: 0 errors, 0 warnings» (161), wine exit-code (164–166), `WINEPREFIX`-команда (149) ✓.
- `SERVICE.mqh`: `Real` в тестере (9), `ExpTotal=1` при `!Real` (47), `MAGIC_GENERATOR` (95–100, `MathAbs(int(MagicLong))`), `INPUT_FILE_READ` (122), 16-я колонка → `EXP[e].Mgc` (178), `EXPERT_SET`-фильтры (240) ✓. `#.csv` при `Real=false` в тестере грузит только строку `BackTest` (149) — ограничение в Task 9 Limitations достоверно.
- `FUNCTIONS.mqh:145` — поле `int Mgc;` экземпляра ✓. `set`/`mem` — поля экземпляра EXPERT (`FUNCTIONS.mqh:150`) ✓ (Open Question 4 плана корректен: `set.BUY` пер-экспертен).
- Цикл экспертов `for (uchar e=0; e<ExpTotal; e++) EXP[e].MAIN();` существует — `$o$imple.mq5:162` ✓ (но см. В-6: план цитирует `MAIN.mqh:162`).
- `MT5_ExportNero` глобальная `$o$imple.mq5:108`, input `InpMT5_NeroFile="Nero_MT5.csv"` (74) ✓; обе `NERO_CSV_CREATE` имеют guard `if(!MT5_ExportNero) return;` (`lib_PIC.mqh:677, 781`) ✓.
- Все тестовые файлы, на которые ссылается план, существуют: `test_mt5_signal_executor_schema.py`, `test_mt5_batch_runtime_contract.py`, `test_parse_mt5_execution_report.py`, `test_mt5_execution_diagnostics.py`, `test_mt5_nero_parity.py` ✓.
- `knowledge-rag` по теме multi-expert/rule_id: противоречащих прошлых решений не найдено (ранее зафиксирован только DIAGNOSTIC_ONLY-статус execution loop).

---

## 2. Замечания

### Критично

**К-1. Task 6: ветка ORDER_EXPIRED мертва — `out_expiry` всегда 0**
- Место: план, Task 6 Step 4 (функция `MT5_PerExpertLastPlaced`, строки 1185–1201) + Step 6 (строка 1307).
- Суть: `MT5_PerExpertLastPlaced` жёстко ставит `out_expiry = 0` («expiry отслеживается отдельно через MT5_MaxFillLagBars[idx]»), но в Step 6 условие экспирации `mt5_last_expiry > 0 && TimeCurrent() > mt5_last_expiry` никогда не истинно. Просроченные незаполнившиеся заявки будут классифицироваться как `OPEN_FAILED` вместо `ORDER_EXPIRED`.
- Доказательство: текст плана 1191 (`out_expiry = 0;`) и 1307 (`mt5_last_expiry > 0`). Текущий код, который это заменяет, экспирацию обрабатывает: `MT5_LastPlacedExpiry` заполняется реальным expiry (`lib_ML_Signal.mqh:811-812, 835`) и проверяется на 597.
- Почему важно: молчаливо ломается контракт классификации событий, ради которого существует lifecycle-лог; smoke «UNEXPLAINED=0» это не поймает (оба события «объясняют» позицию).
- Исправление: хранить expiry в записи трекера (поле struct либо пересчёт `MT5_DecisionTimes[idx] + MT5_MaxFillLagBars[idx]*Period()*60`) и возвращать его из `MT5_PerExpertLastPlaced`.

**К-2. Task 6: pending-запись с `ticket==0` никогда не удаляется — повторные события на каждом баре**
- Место: план, Task 6 Step 6, строки 1296–1317.
- Суть: после fill вызывается `MT5_AddTrackedPosition(ticket, idx, magic)`, но старая запись с `ticket==0, open_logged=false` не удаляется и не помечается; в ветках OPEN_FAILED/ORDER_EXPIRED комментарий обещает «Compact-remove из tracker», а в коде сбрасывается только singleton. `MT5_PerExpertLastPlaced` ищет запись с `open_logged=false && ticket==0` — она находится каждый следующий бар → `has_pending=true` вечно → OPEN_FAILED/ORDER_EXPIRED логируются повторно на каждом баре.
- Доказательство: текст плана 1303–1316 (нет вызова удаления; `MT5_RemoveTrackedPosition` упомянута в комментарии 1309, но не вызвана); семантика поиска — план 1186–1193.
- Почему важно: загрязнение event CSV дублями, ложные счётчики в `parse_mt5_execution_report`, невозможность честной per-rule reconciliation.
- Исправление: после fill/expire/fail помечать запись потреблённой (`open_logged=true`) или вызывать `MT5_RemoveTrackedPosition(idx, magic)`; добавить static-тест на отсутствие повторного логирования.

**К-3. Task 3 ломает single-expert backcompat, заявленный в Global Constraints**
- Место: план, строка 27 («Backcompat ветка для старого single-expert без rule_id-фильтра сохраняется»), Task 1 тест (179–182), Task 3 Step 3 (429–433), Completion Criteria (2074).
- Суть: Task 3 Step 3 всегда передаёт непустой фильтр `"mt5_rule_" + (string)Mgc`. Все существующие signal CSV сгенерированы с `rule_id=run_id` (подтверждено: `run_mt5_batch.py:142`; 32 батч-каталога в `ML/reports/mt5_execution_loop/batch/`). Ни одна строка не совпадёт с `mt5_rule_<magic>` → `MT5_FindEntrySignal` вернёт −1 на всех барах → без регенерации CSV single-expert smoke не поставит ни одного ордера. Ветка «пустой фильтр» — мёртвый код: ни один call site не передаёт `""`.
- Доказательство: `lib_ML_Signal.mqh:777` (единственный call site, план заменяет его без fallback); `run_mt5_batch.py:142`; `make_run_id` не меняется (тест плана 243–255 сам это фиксирует).
- Почему важно: утверждение Completion Criteria «backcompat гарантирован static-тестами» ложно — статические тесты проверяют лишь допустимость пустого фильтра, а не runtime-поведение. Регрессия проявится как тихий «0 событий» в существующих smoke.
- Исправление: (а) fallback в `ML_TRADE`: при −1 с rule-фильтром повторный поиск с `""`; либо (б) явная миграция: перегенерация всех CSV и снятие claims про backcompat из Global Constraints/Completion Criteria/Task 9 Verification.

**К-4. Task 5: multi-expert tester-ветка неисполнима — smoke и batch используют не те CSV**
- Место: план, Task 5 Step 3 (994–1029), Task 8 Step 6 (1820–1822), Completion Criteria (2071).
- Суть: multi-expert CSV пишется в `BATCH_DIR/mbatch_N/entry_signals.csv` (план 922–925). Но `run_smoke_test` берёт `candidates[0]` и ищет `BATCH_DIR/make_run_id(cand)/entry_signals.csv` (`run_mt5_batch.py:429-434`) — каталога `mbatch_*` там нет → «SMOKE: entry CSV not found» → ABORT; либо (если старый каталог существует) копируется старый single-expert CSV. `run_batch` с фейковым кандидатом `{"profile": batch_id, ...}` строит `run_id = "mbatch_0_multi_0h_thr0.0"` (`run_mt5_batch.py:46-47, 474-475`) → «ERROR: no entry CSV». Комментарий плана «Task 7 доработает per-batch tester» (1024) — ложная ссылка: Task 7 занимается только Python reconciliation.
- Доказательство: `run_mt5_batch.py:425-465` (`run_smoke_test`), `run_mt5_batch.py:467-492` (`run_batch`), текст плана 1022–1026.
- Почему важно: критерий завершения «multi-expert smoke: per_rule_reconciliation содержит оба rule_id с UNEXPLAINED=0» недостижим через заявленную CLI-команду; Task 8 Step 6 провалится или даст ложный PASS на чужих данных.
- Исправление: отдельная multi-expert smoke/batch-функция, которая берёт CSV из `mbatch_*`, копирует его через `copy_entry_signal_file` и передаёт `_smoke`/batch-имя; либо параметризация `run_smoke_test(entry_csv=...)`. Убрать ложную ссылку на Task 7.

**К-5. Task 8 Step 5: ручная подкладка CSV перезаписывается; даты примеров вне окна smoke**
- Место: план, Task 8 Step 5 (1812–1814), примеры строк «2023.01.02 …» в Task 4 (537–553).
- Суть: (1) `run_smoke_test` вызывает `copy_entry_signal_file(entry_csv)` (`run_mt5_batch.py:438`) и стирает вручную подготовленный `mt5_entry_signals.csv`; инструкция Step 5 нейтрализуется. (2) Smoke-окно тестера жёстко задано `from_date="2021.01.04", to_date="2021.03.31"` (`run_mt5_batch.py:440`); образец multi-rule строк датирован 2023.01.02 → сигналы не попадут в окно даже при верном CSV. Окно валидации генерации тоже 2021–2022 (`run_mt5_batch.py:27-28`) — фикстуры 2023 года отбрасываются и в Python-тестах Task 5 (см. В-2).
- Доказательство: `run_mt5_batch.py:438-440`, план 1812, 537–553.
- Почему важно: «smoke PASSED с UNEXPLAINED=0» в таких условиях — артефакт пустого прогона, а не проверка механики.
- Исправление: генерировать smoke-строки внутри окна smoke (2021.01–2021.03) и/или параметризовать даты smoke; CSV подкладывать через код, а не вручную.

**К-6. Магики 163856259/987654321 несовместимы с CHECKSUM; smoke деградирует молчаливо**
- Место: план, Task 8 Step 5 (1810), Completion Criteria (2071), тесты Task 4/5/7 (фиксированные литералы).
- Суть: `EXPERT_SET` → `CHECKSUM` требует `MAGIC_GENERATOR() == EXP[e].Mgc` и при несовпадении `return(false)` — «отключаем торговлю для этого эксперта» (`SERVICE.mqh:250-257`). `MAGIC_GENERATOR` детерминирован от входных параметров эксперта (`SERVICE.mqh:95-100`), произвольные числа не «подбираются». При несовпадении эксперты отключаются, smoke даёт 0 событий и формально проходит (UNEXPLAINED=0) — ложный PASS.
- Доказательство: `SERVICE.mqh:250-257`; Open Question 2 плана сам это признаёт, но классифицирует как «тест-уровневая проблема, не blocker», при том что все критерии завершения захардкодили эти два числа.
- Почему важно: весь smoke-гейт плана может быть пройден при полностью отключённых экспертах.
- Исправление: магики получать из фактического `MAGIC_GENERATOR` (эталонный прогон/лог OnInit: `SERVICE.mqh:106` печатает Magic) и параметризовать их в тестах и критериях; smoke обязан проверять, что ORDER_PLACED/OPEN события существуют (N>0), а не только UNEXPLAINED=0.

**К-7. Task 7: тест вызывает `main(argv)`, но `main()` без параметров; точка вставки метрик указана неверно**
- Место: план, Task 7 Step 2 тест `test_main_writes_per_rule_reconciliation_to_metrics_json` (1439–1453), Step 5 (1517–1524).
- Суть: фактическая сигнатура `def main() -> None` с `parser.parse_args()` из `sys.argv` (`parse_mt5_execution_report.py:143-153`). Вызов `parser_main([...])` → `TypeError`. Кроме того, словарь метрик собирается в `compute_mt5_metrics` (ключ `"reconciliation"` — `parse_mt5_execution_report.py:128-138`), а не в `main`; инструкция Step 5 «найти в main metrics = {...}» неверна.
- Доказательство: `parse_mt5_execution_report.py:115-153`.
- Почему важно: заявленный Step 6 «Expected: PASS (4 теста)» не выполним; per-rule ключ попадёт не в тот уровень кода.
- Исправление: `def main(argv=None)` + `parse_args(argv)`; добавлять `per_rule_reconciliation` в `compute_mt5_metrics`; тесты — через `main([...])` либо monkeypatch `sys.argv`.

### Важно

**В-1. Task 7b решает несуществующую в scope проблему (Nero в diagnostic-режиме не пишется)**
- Место: план, Task 7b целиком (1555–1742), Motivation (1557).
- Суть: план цитирует `COUNT.mqh:7` как место вызова `PIC()`. Фактически строка 6: `if (MT5_DiagnosticExecutor) return (true); // diagnostic: PIC/Nero не нужны` — в единственном режиме этого плана (`iSignal==3`, `MT5_DiagnosticExecutor=true`) `PIC()` не вызывается, строки Nero не пишутся вообще; `NERO_CSV_CREATE(bar)` (`lib_PIC.mqh:311`) недостижим. Заголовок создаётся в `EXPERT::INIT()` (`lib_PIC.mqh:128`), а не в «PIC_INIT» — символа `PIC_INIT` в кодовой базе нет (`rg PIC_INIT` → 0).
- Доказательство: `COUNT.mqh:6-7`; `rg "PIC_INIT" MT/MQL5` — 0 результатов; `lib_PIC.mqh:95-129` (функция `EXPERT::INIT`).
- Почему важно: Task 7b (+3 static-теста, изменение `lib_PIC.mqh`) расширяет поверхность компиляции ради сценария, который вне заявленного scope; smoke Task 8 Step 7b сам признаёт, что обычно пропускается.
- Исправление: вынести Task 7b из плана (отдельный план для non-diagnostic режимов) либо зафиксировать в Motivation, что в diagnostic-режиме Nero не пишется.

**В-2. Task 5: предложенные тесты не пройдут и после реализации**
- Место: план, Task 5 Step 1 `test_run_mt5_batch_multi_expert_mode_generates_multi_rule_csv` (748–813), Step 4 «Expected: PASS».
- Суть: две независимые причины. (1) Фейковые кандидаты не содержат `score_cutoff`, а предложенная реализация делает `float(cand["score_cutoff"])` (план 943; реальный код-аналог `run_mt5_batch.py:116`) → KeyError. (2) Даты фикстур 2023-01-02 вне окна `VAL_FROM=2021-01-04 … VAL_TO=2022-12-02` (`run_mt5_batch.py:27-28`) → фильтр плана 942 оставляет 0 строк → `source_groups` пуст → SKIP → CSV не создаётся → `assert len(csvs)==1` падает.
- Доказательство: план 758–761, 942–943; `run_mt5_batch.py:27-28, 116`.
- Исправление: добавить `score_cutoff` в фикстуры; даты фикстур — внутри 2021–2022; либо вынести окно в параметр.

**В-3. В тексте 16 zero-width space внутри имён `#.csv` + мусорные вкрапления**
- Место: весь документ; строки 5, 9, 29 (×4), 30, 522, 1938, 1971 и др.
- Суть: все 16 упоминаний `#.csv` содержат `U+200B` между `#` и `.csv`. Копирование такого имени в команду/код даёт несуществующее имя файла. Также встречаются вкрапления: `调试` (1828), `異常` (276), `一行` (1557), `这支` (2121), `在这` (1969), `неўпадает` (384), `defualt` (244), `горaranтирован` (2074), `chanное правило` (1353), `вchest` (2001), `single-expertжд` (1658), «Commit precondition-чекаут» (65).
- Доказательство: подсчёт символов в файле: 16× U+200B, плюс иероглифы 这/调/试/異/常/一/行/支.
- Почему важно: план исполняется агентом дословно; скрытый символ в пути — воспроизводимая ловушка.
- Исправление: вычистить U+200B и мусорные вкрапления; для имён файлов добавить проверку.

**В-4. Task 6 игнорирует существующий механизм `MT5_PosMap*`, вводится третий параллельный трекер**
- Место: план, Task 6 целиком; фактический код `lib_ML_Signal.mqh:78-94`.
- Суть: в коде уже есть `MT5_PosMapIds[]/MT5_PosMapIdx[]` + `MT5_RegisterPosition(position_id, idx)` (карта position→signal-idx, используется на 595) и singleton-триада `MT5_TrackedMagic/Idx/OpenLogged` (74–76). План вводит `MT5_TrackedPositions[]`, не упоминая существующие структуры и не описывая миграцию/сосуществование (Task 6 Step 6 «Стало» молча выбрасывает `MT5_RegisterPosition`).
- Почему важно: два параллельных реестра позиций — источник рассинхронизации; план обязан явно сказать, что заменяется, а что удаляется.
- Исправление: раздел «Миграция существующего состояния» в Task 6: судьба `MT5_PosMap*`, `MT5_RegisterPosition`, `MT5_TrackedMagic/Idx/OpenLogged`.

**В-5. Task P0 ссылается на несуществующие идентификаторы замечаний «А1–А14»**
- Место: план, Task P0 Step 2 (строка 63).
- Суть: `rg "А1|А2|А14" docs/superpowers/audit.md` → 0 совпадений: в audit.md нумерации А1–А14 нет (проверено до очистки файла). Ссылка не проверяема.
- Исправление: ссылаться на конкретные секции closeout-плана/audit.md по заголовкам, а не на несуществующие номера.

**В-6. Неверные места-ссылки: `MAIN.mqh:162`, «PIC_INIT», `ORDERS.mqh:11`**
- Место: план, строки 1081, 1557 (`MAIN.mqh:162`), 1573, 1865 («PIC_INIT»), 2141 (`ORDERS.mqh:11`).
- Суть: цикл экспертов — `$o$imple.mq5:162` (`EXPERT::MAIN` определена в `MAIN.mqh:133`); `PIC_INIT` не существует (см. В-1); `ORDERS_SET` — `ORDERS.mqh:5`, не `:11`.
- Почему важно: агент-исполнитель навигирует по этим ссылкам; часть ведёт не туда.
- Исправление: поправить все ссылки.

**В-7. Disclosure-список в Global Constraints не совпадает с методологией 16**
- Место: план, строки 22–25; эталон `docs/methodology/16-reporting-audit.md:69-76`.
- Суть: методология требует 8 полей: `lifecycle_status, origin_bias, research_priority, current_search_budget, cumulative_search_budget, next_probe_freeze, allowed_max_verdict, forbidden_interpretations`. План перечисляет `lifecycle_status, origin_bias, roadmap_track, research_priority, verdict, forbidden_interpretations`: `roadmap_track` и `verdict` в методологии отсутствуют, три budget-поля опущены. Шаблон отчёта Task 9 при этом полный (все 8 + roadmap_track) — внутреннее противоречие плана.
- Исправление: привести список Global Constraints к методологии; `roadmap_track` оставить как добровольное расширение проекта.

**В-8. Task 8 Step 3: путь `$o$imple.mq5` не экранирован в shell-команде**
- Место: план, строки 1781–1784.
- Суть: аргумент `/compile:'/home/.../Experts/$o$imple.mq5'` содержит `$o` и `$imple`, которые bash раскрывает как переменные, если команду выполнить в двойных кавычках/без внешнего экранирования → путь ломается. Методология (13b:149-153) даёт тот же шаблон, но для агентного исполнения команда должна быть безопасной.
- Исправление: экранировать путь целиком одинарными кавычками либо через `\$`.

### Улучшения

**У-1. Task 1 Interfaces обещает `rule_id_prefix` в `prepare_entry_quality_source` — Task 2 этого не делает.** План 85 противоречит Task 2 (287–335, только type-guard) и телу теста 197–219 (проверяется только передача готовой строки). Убрать упоминание параметра из Interfaces.

**У-2. Task 6 Step 1 тесты слабее своих docstring.** `test_mt5_lifecycle_state_uses_per_magic_lookup` проверяет лишь сигнатуру (1093–1097), `test_ml_trade_calls_per_expert_lookup_not_singletons` допускает OR-условие и не проверяет отсутствие записи в singleton (1126–1128). Добавить: тело `MT5_LogLifecycleForCurrentState` содержит вызов `MT5_PerExpertLastPlaced`; в `ML_TRADE` нет безусловных присваиваний `MT5_LastPlacedIdx =`.

**У-3. Task 3 Step 6 ослабляет существующий контракт-тест.** Было: `assert "MT5_EntryTimes[i] == barTime" in body`; стало: `assert "MT5_EntryTimes[i]" in body` (план 488). Новая реализация (`if (MT5_EntryTimes[i] != barTime) continue;`) проходит и более сильную формулировку `!= barTime`. Сохранить силу assertion.

**У-4. Конвенция «глобальная `MT5_RuleIdFilter`» противоречит реализации.** Global Constraints (30) говорит о переменной `MT5_RuleIdFilter`, Task 3 Step 3 вводит локальную `mt5_rule_filter`. Унифицировать.

**У-5. `--multi-expert-magics` «или `auto`» (план 741) нигде не реализован.** Мёртвая документация — убрать либо реализовать.

**У-6. Task 7 тест `test_reconcile_positions_per_rule_classifies_unexplained` не проверяет UNEXPLAINED.** Имя обещает одно, assertion проверяет OPEN_AT_END (1427). По фактической логике `reconcile_positions` (`parse_mt5_execution_report.py:79-88`) UNEXPLAINED получает только позиция без TX_OPEN (например, лишь TX_CLOSE) — добавить такой кейс отдельно, комментарий исправить.

**У-7. Дрейф цитат 13b в таблице применимости.** План: «13b:209» → фактически 208; «13b:217» → 216 (215 — верно). Поправить.

**У-8. Заголовок Task 6 «`MT5_LOG_MT5_LastPlaced*` field-bound к magic» (1071) — бессмысленный идентификатор.** Переименовать в «per-expert lifecycle state by magic».

### Вопросы

**Q-1. Task 7b regex `[^}]*` хрупкий.** Тесты 1613–1619 ищут `MT5_NeroFileName` до первой `}` тела функции. Сейчас вызов стоит первой строкой (замена на 679/783) — работает; любое вложение фигурных скобок до вызова сломает тест. Заменить на ленивый `.*?` с `re.S`?

**Q-2. Поведение при совпадении строк двух правил на одном баре.** Если multi-rule CSV содержит два rule_id с одинаковым `time`, порядок строк после сортировки в `prepare_mt5_multi_expert_source` детерминирован, но план не фиксирует, что каждый эксперт берёт именно свою строку, а не «первую по времени». Теста на коллизию нет. Требуется ли явный контракт и тест?

**Q-3. Ограничение отчёта Task 9 про backcompat.** Шаблон Verification (1953) утверждает «Backcompat single-expert smoke унаследован от closeout». С учётом К-3 это утверждение к моменту исполнения будет ложным — переписать блок Verification под выбранный вариант миграции?

---

## 3. Итог

Структура плана (P0-гейт → TDD-контракты → реализация → compile gate → smoke → отчёт с disclosure) корректна и согласована с методологией 13b/16; большинство цитат строк и сигнатур проверены и точны (раздел 1). Блокирующее внешнее обстоятельство: closeout-план не исполнен (раздел 0), и по собственному гейту план BLOCKED.

До разблокировки необходимо закрыть 7 критичных замечаний: К-1/К-2 (дефекты lifecycle-логики в самом тексте Task 6), К-3 (сломанный single-expert backcompat), К-4/К-5 (tester-ветка multi-expert использует не те каталоги/CSV/даты), К-6 (магики vs CHECKSUM — риск ложного PASS smoke), К-7 (тест Task 7 падает по сигнатуре `main`). После этого — важные В-1…В-8, из которых В-1 (Task 7b вне scope) и В-3 (U+200B в именах файлов) наиболее практичны.

Отдельно: smoke-критерий «UNEXPLAINED=0» сам по себе недостаточен (К-5, К-6) — Completion Criteria нужен положительный сигнал (`ORDER_PLACED>0`, `CLOSED_TX>0` по каждому rule_id), иначе пустой прогон считается успехом.
