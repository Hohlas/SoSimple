# Аудит плана `2026-07-29-mt5-execution-loop-migration`

Проверенный документ: `docs/superpowers/plans/2026-07-29-mt5-execution-loop-migration.md`.

Проверенные связанные артефакты: `MT/README.md`, `MT/MQL5/Experts/$o$imple.mq5`, `MT/MQL5/Include/lib_PIC.mqh`, `MT/MQL5/Include/lib_ML_Signal.mqh`, `MT/MQL5/Include/MAIN.mqh`, `MT/MQL5/Include/INPUT.mqh`, `MT/MQL5/Include/ORDERS.mqh`, `MT/MQL5/Include/SERVICE.mqh`, `MT/MQL4/Include/lib_PIC.mqh`, `MT/MQL4/Include/lib_ML_Signal.mqh`, `docs/MT/lib_PIC.mqh.md`, `docs/MT/ml_signal_integration.md`, `docs/DATA_FLOW.md`, `docs/dataset_description.md`, `ML/data_loader.py`, `ML/online_tester_reconciliation.py`, `docs/ML/online_tester_reconciliation.py.md`, `docs/methodology/01-raw-data-inventory.md`, `03-feature-contract-leakage.md`, `06-temporal-split.md`, `09-validation-freeze.md`, `10-frozen-test-oos.md`, `12-backtest-costs.md`, `13-export-mt4-parity.md`, `13b-mt5-execution-parity.md`, `16-reporting-audit.md`, `A4-verdicts-stop-conditions.md`.

Навигация: `knowledge-rag search_similar` по плану вернул `no_results`; `graphify query` использовался только как карта кандидатов, не как источник доказательств.

## Подтверждено

- Основная идея плана методологически верная: MT5 tester может проверять исполнение, но не доказывает честность ML-признаков сам по себе. Это совпадает с `docs/methodology/03-feature-contract-leakage.md:21-30`, `docs/methodology/13b-mt5-execution-parity.md:56-63`.
- Выбор существующего `MT/MQL5/Experts/$o$imple.mq5` как первичного target подтверждён: файл есть, `MT/README.md:17-20` называет `MQL5/` экспериментальным портом, а `docs/methodology/13b-mt5-execution-parity.md:16-17` фиксирует этот expert и `.ex5`.
- MT5 terminal фактически установлен: команда `find '/home/hohla/.mt5/drive_c/Program Files/MetaTrader 5' -maxdepth 1 -type f` показала `MetaEditor64.exe`, `metatester64.exe`, `terminal64.exe`.
- На диске есть свежий compile log: `/tmp/sosimple_mt5_compile.log` содержит `Result: 0 errors, 0 warnings`; `stat` показал `MT/MQL5/Experts/$o$imple.ex5` с датой `2026-07-29 19:22:27`.

## Замечания

### 1. Критично: MT5 `Nero.csv` сейчас не совместим с текущим Python-контрактом

- **Место:** план, Task 1A, строки 220-228 и 267-278.
- **Суть проблемы:** план требует `Nero.csv`-совместимость, но его parity-проверки не проверяют число вложенных полей в `fractal*` и наличие `Shift`.
- **Доказательство:** текущий Python-контракт требует 23 поля: `ML/data_loader.py:94`, `ML/data_loader.py:612-617`, `processing/label_signals.py:57-97`, `docs/dataset_description.md:24-34`. MT4 producer пишет `Shift` как 23-е поле: `MT/MQL4/Include/lib_PIC.mqh:897-901` и `903-919`. MT5 producer сейчас заканчивает строку на `FractalAtr` и `Shift` не пишет: `MT/MQL5/Include/lib_PIC.mqh:878-894` и `896-912`.
- **Почему это важно:** MT5 export может пройти поверхностную проверку по `fractal0.direction` и `fractal0.price`, но затем сломать Python-парсер или silently дать другой набор признаков.
- **Рекомендуемое исправление:** в Task 1A добавить обязательную проверку `len(fractalN.split(':')) == 23` для всех `fractal0..fractal99`, проверку `Shift` и сравнение MT4/MT5 по полному вложенному формату. В MQL5 `NERO_CSV_CREATE(int cur_bar)` добавить `":" + S0(SHIFT(F[f].T) - cur_bar)`.

### 2. Критично: нет мостика от `mt5_entry_signals.csv` к MQL5-исполнению

- **Место:** план, Task 3 и Task 4, строки 604-618, 791-800, 916-917.
- **Суть проблемы:** Python exporter создаёт новый entry-only CSV, но план не добавляет MQL5-код, который читает именно этот CSV и применяет `limit_price`, `stop_price`, `max_fill_lag_bars`.
- **Доказательство:** текущий MQL5 `lib_ML_Signal.mqh` читает только `ml_signals.csv`: `MT/MQL5/Include/lib_ML_Signal.mqh:20`, `55-99`. Поиск `rg -n "mt5_entry_signals|limit_price|protective_stop_price|max_fill_lag_bars" MT/MQL5/...` нашёл эти слова только в плане, не в MQL5-коде. `INPUT.mqh` вызывает старый `ML_TRADE()` при `iSignal=3`: `MT/MQL5/Include/INPUT.mqh:14-19`.
- **Почему это важно:** после выполнения Task 3 у MT5 всё ещё нечего исполнять из нового файла. Цель плана про tester-executed limit orders не будет достигнута.
- **Рекомендуемое исправление:** добавить отдельный MQL5 reader для `mt5_entry_signals.csv`: массивы `signal_time/rule_id/side/entry_type/limit_price/stop_price/atr/max_fill_lag_bars`, поиск по времени, постановку именно этих pending/limit orders, истечение заявки и лог `ORDER_PLACED`/`ORDER_EXPIRED`/`OPEN_FAILED`.

### 3. Важно: план не использует MT5-специфическую методологию `13b`

- **Место:** Methodology Map, строки 63-72; Task 1 Unknowns, строки 26-32 и 121-143.
- **Суть проблемы:** план ссылается на MT4 parity как аналог, но пропускает `docs/methodology/13b-mt5-execution-parity.md`, где уже есть конкретный MT5-контур, пути и команда компиляции.
- **Доказательство:** `docs/methodology/13b-mt5-execution-parity.md:14-25` фиксирует terminal path и команду MetaEditor; `13b:34-39` объясняет, как читать compile verdict; `13b:56-63` задаёт обязательные проверки. План при этом пишет `mt5_terminal_executable_path: "UNKNOWN"` и `absolute MT5 terminal executable path` как blocker: `docs/superpowers/plans/2026-07-29-mt5-execution-loop-migration.md:125`, `140`.
- **Почему это важно:** исполнитель может зря остановиться на ручном handoff, хотя часть автоматической проверки уже описана и доступна.
- **Рекомендуемое исправление:** добавить `docs/methodology/13b-mt5-execution-parity.md` в Methodology Map и заменить `UNKNOWN` по terminal path на `/home/hohla/.mt5/drive_c/Program Files/MetaTrader 5/terminal64.exe`; отдельно оставить неизвестным только возможность автоматического tester-run.

### 4. Важно: финальная проверка не компилирует MQL5 после изменений

- **Место:** Final Verification, строки 1523-1549.
- **Суть проблемы:** план меняет `.mq5/.mqh`, но финальная проверка запускает только Python tests и `rg`.
- **Доказательство:** `docs/methodology/13b-mt5-execution-parity.md:19-35` требует компиляцию через MetaEditor и verdict по логу `0 errors, 0 warnings`; `13b:58-59` делает это обязательной проверкой. В плане Final Verification такой команды нет.
- **Почему это важно:** статический поиск символов не доказывает, что MQL5-код компилируется. Для MQL это особенно рискованно из-за include-порядка и отличий MQL4/MQL5 API.
- **Рекомендуемое исправление:** добавить compile check из `13b` в Task 4 и Final Verification. Если агент не может запустить Wine/MetaEditor, отчёт должен явно содержать `compile_status: MANUAL_REQUIRED`, а не только `rg`-проверку.

### 5. Важно: event schema недостаточна для cost/reconciliation audit

- **Место:** Task 2, строки 363-367 и 489-505; Task 6, строки 1074-1081.
- **Суть проблемы:** плановый MT5 event-log содержит базовые поля, но не содержит spread, slippage, Bid/Ask, OHLC бара, commission, swap, balance/equity, `order_open_price`, `order_close_price`, `entry_time`, `exit_time`.
- **Доказательство:** методология требует логировать `OPEN_FAILED`, spread, slippage, Bid/Ask, commission, swap, balance/equity: `docs/methodology/13-export-mt4-parity.md:38-40`. Существующий MT4 event-log уже пишет эти поля: `MT/MQL4/Include/lib_ML_Signal.mqh:110-147`, `180-255`; документация это подтверждает: `docs/MT/ml_signal_integration.md:542-549`. Парсер reconciliation ожидает эти числовые поля: `ML/online_tester_reconciliation.py:37-66`.
- **Почему это важно:** без этих полей нельзя честно объяснить разницу PnL, проскальзывание, издержки и причины пропущенных входов.
- **Рекомендуемое исправление:** расширить `MT5_EVENT_COLUMNS` до уровня MT4 event-log или явно сделать `mt5_event_v1_minimal` только debug-схемой, а для parity добавить `mt5_event_v2_reconciliation` с полями cost/execution.

### 6. Важно: плановый event-log не очищается перед tester-run

- **Место:** Task 4 logger, строки 871-885; Task 7 runbook, строки 1236-1247.
- **Суть проблемы:** предложенный logger дописывает в существующий файл и пишет заголовок только если файл пустой; отдельного удаления файла в tester-режиме нет.
- **Доказательство:** `docs/methodology/13-export-mt4-parity.md:77` называет неочищенный event-log типовой ошибкой. Существующий MT4 logger удаляет файл при `IsTesting()`: `MT/MQL4/Include/lib_ML_Signal.mqh:164-167`, а docs фиксируют очистку tester CSV: `docs/MT/ml_signal_integration.md:557-559`.
- **Почему это важно:** старые события смешаются с новым прогоном, и counts/PnL будут неверными.
- **Рекомендуемое исправление:** добавить `MT5_PrepareEventFileIfNeeded()` с `FileDelete(MT5_EventFile)` при `IsTesting()` перед первой записью; добавить тест/ручную проверку, что новый run начинается с чистого файла.

### 7. Важно: timing contract заявлен, но не представлен в данных

- **Место:** Task 2 schema, строки 546-579; Task 5 contract, строки 987-1001.
- **Суть проблемы:** документ пишет `feature_time <= decision_time <= execution_time`, но в signal/event CSV нет отдельных колонок `feature_time`, `decision_time`, `execution_time` или `feature_available_time`.
- **Доказательство:** `MT5_SIGNAL_COLUMNS` содержит только `time`, `rule_id`, `side`, `entry_type`, `limit_price`, `stop_price`, `atr`, `max_fill_lag_bars`: план строки 468-477. `MT5_EVENT_COLUMNS` содержит `time` и `signal_time`, но не decision/execution timestamps: строки 489-505. Методология требует явно фиксировать `decision_time`: `docs/methodology/03-feature-contract-leakage.md:46-56`.
- **Почему это важно:** нельзя доказать, что признаки были известны до решения, а исполнение произошло после решения.
- **Рекомендуемое исправление:** добавить в signal/event schema поля `feature_time`, `feature_available_time`, `decision_time`, `execution_time`; для ML-exit добавить `fill_time`, `decision_bar_time` и `feature_bar_close_time`.

### 8. Улучшение: exporter metadata не выполняет собственный список обязательных полей

- **Место:** Task 3, строки 624-627 и 726-735.
- **Суть проблемы:** Mandatory Checks требуют `nonzero counts`, но JSON meta их не пишет. Также нет hash входного source CSV, rule/model metadata и run config.
- **Доказательство:** план требует `Hash, row counts, nonzero counts and duplicate times are written to JSON`: строка 627. Реальный шаблон meta содержит `rows`, `unique_times`, `duplicate_time_rows`, `side_counts`, `output_csv_sha256`, но не `nonzero_rows`, `source_csv_sha256`, `rule_hash`: строки 726-735. Методология требует paths, hashes, rules, checkpoints: `docs/methodology/16-reporting-audit.md:31`.
- **Почему это важно:** следующий агент не сможет проверить, из каких входов получен signal CSV и сколько реально активных сигналов экспортировано.
- **Рекомендуемое исправление:** добавить `source_csv`, `source_csv_sha256`, `rule_id`, `rule_hash`, `active_signal_rows`, `buy_rows`, `sell_rows`, `run_config_hash`.

### 9. Улучшение: `InpMT5_ExportNero=false -> no producer side effect` недоказуемо текущей статической проверкой

- **Место:** Task 1A, строки 315-340.
- **Суть проблемы:** план задаёт guard для Nero export, но проверяет только наличие строк через `rg`, а не то, что оба overload-а `NERO_CSV_CREATE()` и все вызовы реально защищены.
- **Доказательство:** текущий MQL5 код вызывает `NERO_CSV_CREATE()` в `EXPERT::INIT()`: `MT/MQL5/Include/lib_PIC.mqh:96-129`, и пишет строки через `NERO_CSV_CREATE(bar)` при обновлении уровней: `MT/MQL5/Include/lib_PIC.mqh:312`, `677-692`, `779-922`. Плановая проверка `rg` на строки `InpMT5_ExportNero|...` не доказывает отсутствие записи файла: план строки 329-340.
- **Почему это важно:** при default `false` эксперт всё равно может удалить/создать `Nero.csv`, если guard вставлен не во все нужные места.
- **Рекомендуемое исправление:** явно прописать: оба `NERO_CSV_CREATE` должны начинаться с `if(!MT5_ExportNero) return;`, имя файла должно использовать `MT5_NeroFile`, а проверка должна включать compile plus source grep по обоим overload-ам.

### 10. Вопрос: runbook не даёт точный путь к MT5 tester `Files`

- **Место:** Task 1 manifest, строка 137; Task 7 runbook, строки 1236-1247.
- **Суть проблемы:** обязательная проверка говорит, что runbook должен точно сказать, куда копировать файлы, но шаблон пишет только `MT5 tester Files directory`.
- **Доказательство:** `MT/MQL5/Files` сейчас не существует: команда `test -d MT/MQL5/Files` вернула exit code `1`; `find MT/MQL5 -maxdepth 2 -type d` показал `Experts`, `Include`, `Profiles`, но не `Files`. План при этом указывает `"mt5_files_dir_planned": "MT/MQL5/Files"` и шаг `Copy signal CSV to MT5 tester Files directory`: строки 137, 1239.
- **Почему это важно:** пользователь может положить CSV не туда, эксперт не найдёт файл, и tester-run будет ошибочно интерпретирован как проблема стратегии.
- **Рекомендуемое исправление:** добавить шаг discovery: записать `TerminalInfoString(TERMINAL_DATA_PATH)`, tester agent files path или использовать `FILE_COMMON` с явно указанным common path. В manifest хранить фактический путь входного и выходного CSV.

## Итог

План правильный по направлению, но в текущем виде его нельзя исполнять как надёжный implementation plan без правок. Главные блокеры: несовместимый MT5 `Nero.csv` без `Shift`, отсутствие MQL5 reader/executor для нового `mt5_entry_signals.csv`, слишком бедный event-log для reconciliation и отсутствие обязательной MT5 compile verification в финальных проверках.
