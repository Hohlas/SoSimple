# Аудит плана `docs/superpowers/plans/2026-08-03-mt5-per-expert-ml-tracker.md`

Дата аудита: 2026-08-08. Файл очищен и заполнен заново по запросу пользователя;
прежнее содержимое не читалось.

Метод: чтение файлов, rg-поиск, сверка с git-состоянием, сверка сигнатур функций,
проверка_cross-ссылок на методологию. Все утверждения проверены по фактическому
состоянию репозитория (ветка `mt5-execution-loop`, HEAD `e06a187`).

---

## Статус: найдены замечания

- 2 критичных
- 5 важных
- 4 улучшения
- 3 вопроса

---

## Критичное

### 1. `MT5_LogLifecycleForCurrentState` — неверная сигнатура в Task 6

- Важность: **критично**
- Место: Task 6 Step 6, строки плана 1552-1617 («Было» и «Стало»)
- Суть: план показывает функцию с 2 параметрами:
  `void MT5_LogLifecycleForCurrentState(int magic, int &ml_close_order_type)`.
  Фактическая сигнатура (post-closeout, коммит `c8dc941`) имеет 3 параметра:
  `void MT5_LogLifecycleForCurrentState(int magic, int &ml_close_order_type, ulong &ml_close_ticket)`.
  Если исполнитель скопирует «Стало» дословно — компиляция не пройдёт:
  вызывающий код `ML_TRADE` передаёт 3 аргумента
  (`MT5_LogLifecycleForCurrentState(Mgc, mt5_close_order_type, mt5_close_ticket)`,
  `lib_ML_Signal.mqh:862`), а новая версия функции примет только 2.
  Аналогично, тест `test_mt5_lifecycle_state_uses_per_magic_lookup` (строка плана
  1207-1208) использует regex с 2 параметрами — тест упадёт сразу,
  т.к. regex не совпадёт с реальной сигнатурой.
- Доказательство: `lib_ML_Signal.mqh:714` — реальная сигнатура с 3 параметрами;
  `lib_ML_Signal.mqh:862` — вызов с 3 аргументами в `ML_TRADE`.
- Почему важно: блок «Стало» — центральный код Task 6; исполнитель
  получит compile error и потратит итерации на отладку.
- Исправление: во всех вхождениях «Было»/«Стало» Task 6 добавить третий
  параметр `ulong &ml_close_ticket`. Тест `test_mt5_lifecycle_state_uses_per_magic_lookup`
  обновить на regex:
  `r"void\s+MT5_LogLifecycleForCurrentState\s*\(\s*int\s+magic\s*,\s*int\s+&ml_close_order_type\s*,\s*ulong\s+&ml_close_ticket\s*\)\s*\{"`.

### 2. `MT5_LogLifecycleForTicket` вызывается с неверным первым аргументом

- Важность: **критично**
- Место: Task 6 Step 6, строка плана 1615
- Суть: план вызывает:
  `MT5_LogLifecycleForTicket(MT5_TrackedPositions[tp].ticket, MT5_TrackedPositions[tp].idx, magic, ml_close_order_type)`.
  Первый аргумент — `ulong ticket`. Но реальная сигнатура
  (`lib_ML_Signal.mqh:492`): `void MT5_LogLifecycleForTicket(int tracked_i, int &ml_close_order_type, ulong &ml_close_ticket)`.
  Первый параметр — `int tracked_i` (индекс в `MT5_TrackedPositions[]`), а не тикет.
  Внутри функции: `ulong ticket = MT5_TrackedPositions[tracked_i].ticket;`
  (`lib_ML_Signal.mqh:493`). Если передать ticket как tracked_i — обращение
  по индексу = огромному числу → выход за границы массива → crash.
  Дополнительно: функция имеет 4 параметра (tracked_i, magic, ml_close_order_type,
  ml_close_ticket), а план передаёт 4 аргумента в другом порядке
  (ticket, idx, magic, ml_close_order_type) — ни один не совпадает с ожидаемым.
- Доказательство: `lib_ML_Signal.mqh:492-493` — сигнатура и первое использование
  параметра.
- Почему важно: crash в tester-прогоне; multi-expert smoke не пройдёт.
- Исправление: заменить вызов на:
  `MT5_LogLifecycleForTicket(tp, magic, ml_close_order_type, ml_close_ticket);`
  где `tp` — индекс в `MT5_TrackedPositions[]`. Добавить `ml_close_ticket`
  (4-й параметр), который Task 6 должен propagate-нуть из `ML_TRADE`.

---

## Важное

### 3. Строки функций в плане не совпадают с фактическими

- Важность: **важно**
- Место: Task 3 (строки плана 395, 414, 444), Task 6 (строки плана 1183, 1369, 1547)
- Суть: план указывает устаревшие диапазоны строк:
  - `MT5_FindEntrySignal`: план говорит «строки 128-133», фактически — строка 207;
  - `ML_TRADE`: план говорит «строки 758-860», фактически — 852-1175;
  - `MT5_LogLifecycleForCurrentState`: план говорит «строки 582-648», фактически — 714;
  - `MT5_LogLifecycleForTicket`: план говорит «строки 68-77» для глобальных
    переменных, фактически — 70-72 (переменные), 89-93 (PosMap).
  Исполнитель «сверяется с фактическим» (план это предусматривает), но
  расхождение в ~200 строк повышает риск ошибки.
- Доказательство: `rg -n "int MT5_FindEntrySignal" MT/MQL5/Include/lib_ML_Signal.mqh`
  → 207; `rg -n "void EXPERT::ML_TRADE" MT/MQL5/Include/lib_ML_Signal.mqh` → 852.
- Почему важно: исполнитель может редактировать не тот блок или пропустить
  зависимости.
- Исправление: обновить номера строк в плане до фактических.

### 4. Ссылки на методологию 13b — сдвиг на 2-5 строк

- Важность: **важно**
- Место: Global Constraints (строки плана 18-21), Task 8 (строки плана 1906, 1912, 1936, 1953)
- Суть: план ссылается на строки методологии `13b-mt5-execution-parity.md`,
  но номера сдвинуты:
  - План: «строки 146-166» (компиляция) → фактически 150-170;
  - План: «строка 161» (0 errors, 0 warnings) → фактически 165;
  - План: «строки 164-166» (wine exit code) → фактически 168-170.
- Доказательство: `Read docs/methodology/13b-mt5-execution-parity.md:146-170`.
- Почему важно: исполнитель будет читать не те строки; в Wine-окружении
  это критично (неправильная интерпретация compile result).
- Исправление: обновить номера строк ссылок на методологию.

### 5. «Было» в Task 6 Step 6 содержит уже удалённый `MT5_TrackedTicket`

- Важность: **важно**
- Место: Task 6 Step 6, строки плана 1561-1562
- Суть: блок «Было» показывает код с `MT5_TrackedTicket = (buy_market > 0 ? buy_market : sell_market);`.
  Переменная `MT5_TrackedTicket` была удалена closeout-планом (коммит `278ab99`):
  `rg "MT5_TrackedTicket" MT/MQL5/Include/` возвращает пусто. Блок «Было»
  описывает состояние ДО closeout, а не текущее post-closeout.
- Доказательство: `rg -n "MT5_TrackedTicket" MT/MQL5/Include/` → пусто;
  коммит `278ab99` удалил все singleton-переменные.
- Почему важно: исполнитель не найдёт этот код в файле и потратит время
  на поиск; может сделать неверный merge.
- Исправление: переписать «Было» с актуальным post-closeout кодом
  (per-ticket loop через `MT5_TrackedPositions[]`, без `MT5_TrackedTicket`).

### 6. K-3 fallback: ложный срабатывание при multi-expert без совпадения magic

- Важность: **важно**
- Место: Task 3 Step 3, строки плана 453-469
- Суть: K-3 fallback: если `MT5_FindEntrySignal(Time[bar], "mt5_rule_<Mgc>")`
  возвращает -1, повторный вызов с `""` берёт первое совпадение по barTime.
  Проблема: если CSV содержит `rule_id` колонку, но magic эксперта A не
  имеет строки на данном barTime (а magic B имеет), fallback снимет фильтр
  и эксперт A возьмёт сигнал эксперта B. Это нарушает per-expert изоляцию.
  Сценарий: 2 эксперта, один CSV, на баре T только эксперт B имеет сигнал.
  Эксперт A: первый поиск → -1 (нет строки с rule_id="mt5_rule_A"),
  fallback → берёт строку эксперта B. Результат: эксперт A размещает
  ордер по чужому сигналу.
- Доказательство: код `MT5_FindEntrySignal` (план, строка 430-439):
  при `rule_id_filter=""` условие `rule_id_filter != ""` ложно → фильтр
  не применяется → первый match по time возвращается.
- Почему важно: нарушение per-expert изоляции — два эксперта могут
  разместить ордера по одному сигналу.
- Исправление: в K-3 fallback проверять, содержит ли CSV вообще колонку
  `rule_id` (например, `MT5_RuleIds[0] == ""` для всех → legacy CSV).
  Если `MT5_RuleIds` содержит непустые значения → CSV новый, fallback
  не применять. Альтернатива: добавить флаг `MT5_HasRuleIds` (bool),
  устанавливаемый в `MT5_ENTRY_INIT` при первом непустом `rule_id`.

### 7. Отчёт-шаблон (Task 9) не содержит секцию «Conclusions»

- Важность: **важно**
- Место: Task 9 Step 1, строки плана 2058-2139
- Суть: шаблон отчёта содержит: Context, Implementation Summary,
  Verification, Results, Limitations, Split Disclosure, Forbidden
  Interpretations, Next Step, Related Materials. Методология 16
  (`16-reporting-audit.md:18-30`) требует секцию «Conclusions» между
  Results и Limitations. В шаблоне она отсутствует.
- Доказательство: `docs/methodology/16-reporting-audit.md:26` — «Conclusions»
  в списке обязательных секций; grep «Conclusions» в Task 9 → 0 совпадений.
- Почему важно: отчёт не будет соответствовать методологии.
- Исправление: добавить секцию «Conclusions» в шаблон между Results и
  Limitations.

---

## Улучшения

### 8. Regex для извлечения тела функции — слабый паттерн

- Важность: **улучшение**
- Место: тесты в Task 1 (строки плана 127-129, 143-145, 157-159, 186-188),
  Task 6 (строки плана 1207-1209, 1247-1249, 1306-1308, 1333-1335)
- Суть: regex `r"void\s+FUNC\s*\([^)]*\)\s*\{(?P<body>.*?)\n\}"` с `re.S`
  ищет первый `\n}` — это может быть закрывающая скобка внутреннего блока
  (for/if/while), а не функции. Для `ML_TRADE` (~300 строк с множеством
  вложенных блоков) regex остановится на первом `\n}` внутри функции,
  не дойдя до реального конца. Тесты будут проверять только верхнюю часть
  функции.
- Доказательство: regex `.*?` ленивый + `\n}` матчится на первом же
  переводе строки с `}` — это стандартное ограничение regex без
  balanced-matching.
- Почему важно: тесты могут дать ложный PASS — assertion проверяется
  только в части тела до первого внутреннего `}`.
- Исправление: использовать более надёжный парсер (подсчёт скобок) или
  искать конкретные подстроки без извлечения тела через regex.

### 9. Тест `test_run_mt5_batch_main_has_multi_expert_cli_flag` ссылается на `parse_args`

- Важность: **улучшение**
- Место: Task 5 Step 1, строки плана 916-918
- Суть: тест проверяет `inspect.getsource(run_mt5_batch.parse_args)`,
  но функция называется `build_arg_parser` (`run_mt5_batch.py:777`).
  Fallback через `hasattr` не упадёт, но первая ветка всегда пуста.
  Тест полагается на fallback: `"--multi-expert" in inspect.getsource(run_mt5_batch.main)`.
- Доказательство: `rg "def parse_args" ML/baseline/run_mt5_batch.py` → пусто;
  `rg "def build_arg_parser" ML/baseline/run_mt5_batch.py` → 777.
- Почему важно: тест работает, но первая проверка бессмысленна.
- Исправление: заменить `parse_args` на `build_arg_parser`.

### 10. `main_multi_expert` не передаёт `ml_close_ticket` в цепочке вызовов

- Важность: **улучшение**
- Место: Task 5 Step 3, строки плана 996-1095
- Суть: функция `main_multi_expert` вызывает `materialize_candidate_score_frames`
  и `export_mt5_entry_signals`, но не передаёт `ml_close_ticket` через цепочку
  (это MQL5-параметр, не Python). Однако `export_mt5_entry_signals` принимает
  `rule_metadata` и `run_id` — план их передаёт. Замечание: функция
  `_runtime_ctx_or_empty()` (строка плана 1086-1094) импортирует `json`,
  который не импортирован на уровне модуля `run_mt5_batch.py`.
- Доказательство: `rg "^import json" ML/baseline/run_mt5_batch.py` — проверить;
  если нет — `NameError` при вызове `_runtime_ctx_or_empty`.
- Почему важно: `NameError` при первом вызове `_runtime_ctx_or_empty`.
- Исправление: убедиться, что `import json` есть на уровне модуля, или
  добавить его в начало `_runtime_ctx_or_empty`.

### 11. Task P0 Step 2: список Tasks closeout-плана — жёстко закодирован

- Важность: **улучшение**
- Место: Task P0 Step 2, строки плана 63
- Суть: шаг перечисляет 9 задач closeout-плана по названиям. Если
  closeout-план был обновлён (а он обновлялся — коммит `c8dc941` добавил
  Full Batch 32×2), названия могут не совпасть.
- Доказательство: closeout-план `docs/superpowers/plans/2026-08-03-mt5-multi-position-closeout.md`
  содержит Tasks 1-9, но нумерация и названия могли измениться.
- Почему важно: исполнитель не найдёт задачу по названию.
- Исправление: ссылаться на задачи по номерам, а не по названиям, или
  добавить «сверить с актуальной версией closeout-плана».

---

## Вопросы

### 12. `MT5_PosMapIds[]` vs `MT5_TrackedPositions[]` — дублирование или нет?

- Важность: **вопрос**
- Место: Task 6 Step 3, строки плана 1405-1412
- Суть: план утверждает «две параллельные структуры» без дублирования:
  `MT5_PosMapIds[]` для Python-linkage, `MT5_TrackedPositions[]` для
  lifecycle. Но обе структуры хранят `ticket → idx` mapping. При fill
  `MT5_AddTrackedPosition` добавляет в `MT5_TrackedPositions[]`, а
  `MT5_RegisterPosition` — в `MT5_PosMapIds[]`. Если одна из таблиц
  рассинхронизируется (например, swap-remove в `MT5_TrackedPositions[]`
  при закрытии), Python-linkage через `MT5_PosMapIds[]` может указать
  на неверный idx.
- Доказательство: `lib_ML_Signal.mqh:89-93` — PosMap; `lib_ML_Signal.mqh:73-81` —
  TrackedPositions. Swap-remove в `MT5_LogLifecycleForTicket` меняет индексы
  в `MT5_TrackedPositions[]`, но не в `MT5_PosMapIds[]`.
- Почему важно: рассинхронизация → неверный idx в Python reconciliation.
- Рекомендуемое действие: проверить, что `MT5_PosMapIds[]` обновляется
  при swap-remove, или объединить таблицы.

### 13. `compile_expert()` — что делает?

- Важность: **вопрос**
- Место: Task 5 Step 3, строки плана 982, 1112
- Суть: план вызывает `compile_expert()` в smoke-multi-expert и в
  multi-expert branch. Функция существует (`run_mt5_batch.py:166`), но
  план не описывает, что она проверяет и какие файлы компилирует.
  Если `compile_expert` компилирует `$o$imple.mq5` — это тот же путь,
  что и Task 8 Step 3. Двойная компиляция (в Step 5 и Step 8) —
  потеря времени.
- Доказательство: `run_mt5_batch.py:166` — `compile_expert` существует.
- Почему важно: дублирование компиляции замедляет прогон.
- Рекомендуемое действие: уточнить, нужна ли компиляция в Task 5 Step 3,
  если Task 8 Step 3 уже компилирует.

### 14. Multi-expert grouping: `batch_size=2` — почему именно 2?

- Важность: **вопрос**
- Место: Task 5 Step 3, строки плана 996, 1000-1003
- Суть: `main_multi_expert` группирует candidates по `batch_size=2`
  (по умолчанию). При 32 кандидатах это 16 батчей. Каждый батч —
  отдельный tester-прогон с 2 экспертами. План не объясняет, почему
  именно 2, а не N экспертов на прогон. MT5 tester поддерживает
  несколько экспертов одновременно (ExpTotal из `#.csv`).
- Доказательство: строка плана 996: `batch_size: int = 2`.
- Почему важно: 16 прогонов × время tester = существенное время;
  увеличение batch_size сократит число прогонов.
- Рекомендуемое действие: документировать ограничение или сделать
  batch_size настраиваемым через CLI.

---

## Подтверждённые факты (замечаний нет)

Следующие утверждения плана проверены и подтверждены:

- Precondition closeout-плана выполнен: `MT5_TrackedTicket` singleton удалён
  (grep → пусто), `MT5_TRACKED_POSITION` struct + `MT5_TrackedPositions[]`
  + `MT5_LogLifecycleForTicket` существуют, `(int)ticket` касты удалены,
  `force_rerun` в `run_mt5_batch.py` присутствует.
- `MT5_FindEntrySignal` принимает 1 аргумент (`datetime barTime`) — план
  корректно описывает текущее состояние и необходимость изменения.
- `MT5_RuleIds[]` существует (`lib_ML_Signal.mqh:60`), заполняется в
  `MT5_ENTRY_INIT` (`lib_ML_Signal.mqh:686`).
- `MT5_AddTrackedPosition(ulong ticket, int magic, int idx)` имеет guard
  `ticket==0` (`lib_ML_Signal.mqh:113`) — план корректно описывает
  необходимость нового `MT5_RegisterPendingSignal`.
- `MT5_LastPlacedIdx/Magic/Expiry` существуют как глобальные переменные
  (`lib_ML_Signal.mqh:70-72`) — план корректно описывает необходимость
  per-expert lookup.
- `Mgc` доступно в `ML_TRADE` как поле `EXPERT_PARENT_CLASS`
  (`FUNCTIONS.mqh:145`).
- `prepare_entry_quality_source` имеет параметр `rule_id: str` без type guard —
  план корректно описывает необходимость guard (Task 2).
- `make_run_id`, `VAL_FROM`/`VAL_TO`, `build_arg_parser`, `compile_expert`,
  `materialize_candidate_score_frames`, `SOURCE_ARTIFACT_JSON`, `EQ_SCORES_CSV`
  существуют в `run_mt5_batch.py`.
- `--multi-expert`, `main_multi_expert`, `run_smoke_test_multi_expert`
  НЕ существуют — план корректно описывает необходимость (Tasks 5, 8).
- `reconcile_positions` существует в `parse_mt5_execution_report.py:63`.
- `reconcile_positions_per_rule` НЕ существует — план корректно описывает
  необходимость (Task 7).
- `main()` в `parse_mt5_execution_report.py` не принимает `argv` — план
  корректно описывает необходимость изменения (Task 7 Step 5, К-7).
- `export_mt5_entry_signals` существует с параметрами `rule_metadata`,
  `run_id`, `label`.
- `prepare_mt5_multi_expert_source.py` НЕ существует — план корректно
  описывает необходимость (Task 4).
- `test_mt5_find_entry_signal_uses_entry_time_only` существует
  (`test_mt5_signal_executor_schema.py:349-356`) с regex на 1-аргументную
  сигнатуру — план корректно предсказывает FAIL и адаптацию (Task 3 Step 6).
- Методология 16: disclosure блок содержит ровно 8 полей, `roadmap_track`
  НЕ входит в обязательные — план корректно описывает (строка плана 23).
- `MAGIC_GENERATOR` (`SERVICE.mqh:95-100`), `INPUT_FILE_READ` (122-221),
  `CHECKSUM` (251) — существуют; magic — 16-я колонка `#.csv` (строка 178).
- EXP[] цикл на строке 162 `$o$imple.mq5` — подтверждено.
- `InpMT5_DiagnosticExecutor` default = `false` (строка 75).
- Event CSV header содержит `rule_id` колонку (`lib_ML_Signal.mqh:379`).
- `MT5_ML_LogEvent` принимает и записывает `rule_id` (строки 332-398).
- `tests/test_mt5_execution_diagnostics.py` и `tests/test_mt5_nero_parity.py`
  существуют.
- `docs/superpowers/plans/2026-08-03-mt5-multi-position-closeout.md`
  существует (precondition).
- `docs/superpowers/roadmap.md` существует.

---

## Итог

План структурно корректен: TDD-подход (failing tests → implementation → commit),
backcompat-стратегия (K-3 fallback), per-expert изоляция через `rule_id`,
диагностические ограничения (DIAGNOSTIC_ONLY). Однако содержит 2 критичных
дефекта в центральном коде Task 6: неверная сигнатура `MT5_LogLifecycleForCurrentState`
(2 вместо 3 параметров) и неверный вызов `MT5_LogLifecycleForTicket` (ticket
вместо index). Без исправления этих дефектов исполнитель получит compile error
и crash в tester. Дополнительно: 5 важных замечаний (устаревшие номера строк,
сдвиг ссылок на методологию, K-3 fallback с ложным срабатыванием, отсутствие
«Conclusions» в шаблоне отчёта, «Было» с удалённой переменной).
