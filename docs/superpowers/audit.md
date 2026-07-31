# Аудит плана `2026-07-30-mt5-single-rule-diagnostic-run.md`

**Проверяемый файл:** `docs/superpowers/plans/2026-07-30-mt5-single-rule-diagnostic-run.md`
**Дата аудита:** 2026-07-31
**Метод:** прямое чтение первоисточников, указанных в плане, и связанных артефактов; запуск
Python-проверок на реальных данных репозитория.

---

## Подтверждённые утверждения

Следующие утверждения плана проверены и не содержат ошибок:

- **Обязательные поля плана присутствуют.** Строки 12–16: `depends_on`, `blocks`, `supersedes`,
  `exit_decisions`, `locked_test_policy` — все пять полей, требуемых `docs/superpowers/roadmap.md`
  (строки 153–161), находятся в начале плана.

- **Known Unknowns ссылаются на Task 4, а не на Task 2.** Строка 40: "must be discovered during
  Task 4". Ссылка корректна.

- **Входной CSV-контракт в плане совпадает с кодом.** Столбцы `MT5_SIGNAL_COLUMNS`
  (`ML/baseline/mt5_signal_schema.py`, строки 5–17) совпадают с контрактом плана (строки 56–58).

- **Запрещённые future/result колонки совпадают с кодом.** `MT5_FORBIDDEN_SIGNAL_COLUMNS`
  (`mt5_signal_schema.py`, строки 19–27) совпадают с планом (строки 22–27 Task 2, строки 63–65 Task 5).

- **Схема проверяет `feature_available_time`.** `validate_mt5_signal_frame()` вызывает
  `_validate_time_order(frame, ["feature_time", "feature_available_time", "decision_time"])`
  (`mt5_signal_schema.py`, строка 120). Нарушение `feature_available_time > decision_time` ловится.
  Для событий: строка 130 проверяет цепочку из четырёх колонок включая `feature_available_time`.

- **`open_without_close_estimate` входит в JSON-артефакт парсера.** `compute_mt5_metrics()`
  (`parse_mt5_execution_report.py`, строки 43, 55) возвращает этот показатель. Тест
  `test_compute_mt5_metrics_reports_open_without_close_estimate` его проверяет.

- **Manifest содержит `date_from`, `date_to`, `date_range_policy`.** Шаблон JSON Task 1 (строки
  110–114) включает все три поля.

- **Шаги Task 4 и Task 5 содержат явные `sha256sum` команды.** Строки 373–378 (Task 4 Step 5)
  и строки 486–490 (Task 5 Step 6) требуют hash для event CSV и metrics JSON.

- **Команда поиска source CSV Task 1 Step 1 уже сужена.** Строки 66–68 содержат правило
  `rg '(^|/)(.*fixed11.*|.*entry.*|.*signal.*).*\.csv$'` с явным указанием не считать
  отсутствие `MT/MQL5/Files` ошибкой.

- **Все шесть MQL5 diagnostic inputs присутствуют в эксперте.**
  `MT/MQL5/Experts/$o$imple.mq5`, строки 72–77: `InpMT5_ExportNero`, `InpMT5_NeroFile`,
  `InpMT5_DiagnosticExecutor`, `InpMT5_EntrySignalFile`, `InpMT5_EventFile`,
  `InpMT5_BlockBarsSinceFill0Exit` — все шесть.

- **Report-шаблон Task 6 содержит обязательные секции методики 16.** Строки 522–533 включают
  `Stage Level`, `Multiple Testing Context`, `Changed Files`, `Verification`, `Split Disclosure`,
  `Related Materials`, `forbidden_interpretations`.

- **Цель плана соответствует текущему ACTIVE roadmap.** `docs/superpowers/roadmap.md`,
  строки 17–29: пять шагов MT5 execution-loop совпадают со структурой плана.

- **Команда компиляции и правило не считать `wine` exit code финальным verdict соответствуют
  методике.** `docs/methodology/13b-mt5-execution-parity.md`, раздел "Компиляция": "Не считать
  сам код возврата `wine` verdict-ом компиляции".

- **Статус DIAGNOSTIC_ONLY обоснован фактически.** `docs/reports/2026-07-29-mt5-execution-loop-migration.md`,
  разделы `Verification` и `Results`: "MT5 Strategy Tester runtime-прогон не выполнялся",
  "MT5 Nero.csv producer status: UNKNOWN", "manual_user_run_required".

---

## Замечания

---

### 1. Единственный доступный source CSV не имеет `feature_time`, `feature_available_time`, `decision_time` — план не описывает обязательный промежуточный шаг `prepare_mt5_entry_source`

**Важность:** критично.

**Место:** Task 1, строки 57–58, 77–98.

**Суть проблемы:** план описывает source как "existing source CSV with columns accepted by
`export_mt5_entry_signals.py`: `time`, `feature_time`, `feature_available_time`, `decision_time`..."
Но единственный готовый кандидат, уже преобразованный к тестеру —
`ML/reports/fractal0_entry_quality_filter_scores.csv` — не содержит `feature_time`,
`feature_available_time`, `decision_time`. Это подтверждено Python-проверкой на реальном файле.

Task 1 Step 2 содержит скрипт с проверкой именно этих трёх колонок, и он упадёт с ошибкой
`missing feature_time`, если применить его к исходному CSV.

Для преодоления этого зазора уже создан скрипт `ML/baseline/prepare_mt5_entry_source.py`,
который заполняет timing-поля из `signal_time`. Он уже применялся: в репозитории существует
`ML/reports/mt5_execution_loop/mt5_entry_source_20260730_entry_quality_filter.csv`.
Но в плане этот шаг и скрипт вообще не упоминаются.

**Доказательство:**
```bash
python3 -c "
import pandas as pd
df = pd.read_csv('ML/reports/fractal0_entry_quality_filter_scores.csv', sep=';', nrows=2)
print('feature_time' in df.columns, 'feature_available_time' in df.columns, 'decision_time' in df.columns)
# -> False False False
"
```
`ML/baseline/prepare_mt5_entry_source.py` существует и уже описан в тестах
`tests/test_mt5_signal_executor_schema.py`, строки 298–332, а результат его работы
`mt5_entry_source_20260730_entry_quality_filter.csv` уже есть в
`ML/reports/mt5_execution_loop/`.

**Почему это важно:** исполнитель, следующий плану, применит Task 1 Step 2 к
`fractal0_entry_quality_filter_scores.csv`, получит ошибку, и либо выберет другой
(потенциально неверный) source, либо будет вынужден остановиться без понимания причины.
Более важно: `prepare_mt5_entry_source` устанавливает все три timing-поля равными `signal_time`.
Этот факт фиксирован в `time_policy: "feature_time, feature_available_time and decision_time
are copied from signal_time; diagnostic bridge only"`. Но план не обязывает записывать
`time_policy` в manifest, не требует явно раскрыть это в разделе Limitations отчёта,
и не упоминает риск тривиального timing contract (все три временные метки одинаковы для
каждой строки, что означает: реальный момент доступности признаков не зафиксирован независимо).

**Рекомендуемое исправление:**
1. Вставить в Task 1 Step 1 явное примечание: если source CSV не содержит `feature_time` /
   `feature_available_time` / `decision_time`, применить
   `ML/baseline/prepare_mt5_entry_source.py` и использовать получившийся `mt5_entry_source_*.csv`
   как source для дальнейших шагов.
2. Добавить в manifest обязательное поле `time_policy` (уже присутствует в
   `mt5_single_rule_run_manifest_20260730_entry_quality_filter.json`; добавить в шаблон плана).
3. Добавить в Limitations отчёта (Task 6 Step 1) явное раскрытие: timing contract является
   тривиальным для источника `entry_quality_filter` — `feature_time == feature_available_time
   == decision_time == signal_time`.

---

### 2. Task 4 Step 3 (tester run) не включает `InpMT5_ExportNero` в параметры запуска

**Важность:** важно.

**Место:** Task 4 Step 3, строки 330–354.

**Суть проблемы:** план описывает параметры запуска Strategy Tester (строки 330–342): Expert,
Symbol, Timeframe, и четыре `InpMT5_*` параметра. `InpMT5_ExportNero` и `InpMT5_NeroFile`
в этом списке отсутствуют.

Между тем архитектура плана (строка 7) прямо называет проверку `MT5 Nero.csv parity` одним
из незакрытых условий для выхода из `DIAGNOSTIC_ONLY`. Отчёт Task 6 (строка 545) требует
зафиксировать "Whether MT5 Nero.csv parity is PASS, FAIL, UNKNOWN, or not tested". Но если
тестер запустить без `InpMT5_ExportNero=true`, файл `Nero_MT5.csv` не будет создан, и
оценить parity в рамках одного прогона окажется невозможно.

**Доказательство:**
- `MT/MQL5/Experts/$o$imple.mq5`, строка 72: `input bool InpMT5_ExportNero = false;` — по
  умолчанию экспорт отключён.
- Task 4 Step 3 не содержит строки `InpMT5_ExportNero=...`.
- `docs/reports/2026-07-29-mt5-execution-loop-migration.md`, строка 26: "default-off MT5
  Nero.csv producer: `InpMT5_ExportNero=false`".

**Почему это важно:** план ставит задачу одновременно проверить event lifecycle и продвинуться
в понимании `Nero.csv` parity. Без явного включения `InpMT5_ExportNero=true` второй результат
автоматически попадает в `UNKNOWN: not tested`, а не `UNKNOWN: tested but insufficient`.
Это разные диагностические выводы.

**Рекомендуемое исправление:** добавить в Task 4 Step 3 параметры:
```text
InpMT5_ExportNero=true
InpMT5_NeroFile=Nero_MT5.csv
```
и в Task 6 отчёт — шаг сверки `Nero_MT5.csv` с текущим `MT/MQL4/Files/Nero.csv` по строкам
(или явную оговорку, что Nero parity в этом прогоне не проверялась).

---

### 3. `OPEN_FAILED` не включён в контролируемые показатели отчёта

**Важность:** важно.

**Место:** Task 5 Step 4, строки 428–468; Task 6 Step 1, строки 519–548.

**Суть проблемы:** план требует явно классифицировать `ORDER_PLACED`, `OPEN`, `CLOSE`,
`ML_CLOSE` и вычислять `missing_open_estimate`. Но `OPEN_FAILED` — самостоятельное событие,
которое MQL5-код логирует в нескольких ветвях (например: ордер не найден после `ORDER_PLACED`,
некорректная цена, уже есть открытая позиция). Ни Task 5, ни Task 6 не требуют явно считать
количество `OPEN_FAILED` строк и включать это число в отчёт.

`missing_open_estimate` в парсере считается как `max(ORDER_PLACED − OPEN, 0)`. Это корректная
нижняя оценка, но не то же самое, что `OPEN_FAILED` count: возможны ситуации, когда
`OPEN_FAILED` записан без соответствующего `ORDER_PLACED`, или наоборот. Методика
`docs/methodology/13-export-mt4-parity.md`, строка 39, явно требует: "Логировать `OPEN_FAILED`".

**Доказательство:**
- `MT/MQL5/Include/lib_ML_Signal.mqh`, строки 390, 569, 585, 591, 609, 625: шесть
  различных путей к `OPEN_FAILED`.
- `ML/baseline/parse_mt5_execution_report.py`: `_event_counts()` считает все ключи из
  `value_counts()`, то есть `OPEN_FAILED` попадёт в `order_counts`, но этот факт не
  отражён в структуре `compute_mt5_metrics()` и не требуется в отчёте.
- Task 6 список (строки 519–548) не содержит `OPEN_FAILED count`.

**Почему это важно:** `OPEN_FAILED` является основным сигналом о проблемах с исполнением.
Если tester логирует 50% сигналов как `OPEN_FAILED`, а отчёт этого не показывает явно, вывод
"execution parity diagnostic" будет неполным.

**Рекомендуемое исправление:** добавить в Task 5 Step 4 и в Task 6 отчёт явный показатель
`open_failed_count` (из `order_counts.get("OPEN_FAILED", 0)`) и требование прокомментировать
его в разделе Limitations.

---

### 4. Task 3 Step 1 — один вызов `rg` с альтернативами не гарантирует наличие каждого отдельного input

**Важность:** улучшение.

**Место:** Task 3 Step 1, строки 238–250.

**Суть проблемы:** команда `rg -n "$name" ... >/dev/null || exit 1` работает корректно: она
проверяет каждое имя по отдельности в цикле `for`, и скрипт завершится с кодом 1, если хотя
бы одно имя не найдено. Это правильно.

Однако, ожидаемый результат в плане — "Expected: all six inputs are present" — не описывает,
что именно нужно сделать при провале: выйти, зафиксировать blocker в manifest, или остановить
задачу. Без явного действия исполнитель может попытаться скомпилировать Expert с отсутствующим
параметром.

**Доказательство:** проверка `for ... rg ... || exit 1` прошла успешно для текущего
`$o$imple.mq5` (все шесть inputs найдены). Но плановый шаг не содержит инструкции для случая
провала.

**Рекомендуемое исправление:** добавить: "If check fails — stop this task and record the
missing input(s) as a blocker in the run manifest under `unknowns`; do not proceed to compile."

---

### 5. Тривиальный timing contract не раскрыт как ограничение диагностики

**Важность:** вопрос.

**Место:** Task 2 Step 3, строка 211; Known Unknowns, строка 43.

**Суть проблемы:** план требует, чтобы validator прошёл `feature_time <= feature_available_time
<= decision_time`. Но для уже созданного source (через `prepare_mt5_entry_source`) все три
временные метки идентичны на каждой строке. Validator прошёл бы даже если бы `feature_available_time`
было выставлено неверно — потому что нет независимого источника для проверки.

Это означает, что timing contract этого диагностического прогона доказывает только отсутствие
явного нарушения порядка, но не реальную доступность признаков до decision_time.

**Доказательство:**
```bash
python3 -c "
import pandas as pd
df = pd.read_csv('ML/reports/mt5_execution_loop/mt5_entry_signals_20260730_entry_quality_filter.csv', sep=';')
same = (df['feature_time'] == df['feature_available_time']).all() and (df['feature_available_time'] == df['decision_time']).all()
print(same)  # True: все три поля идентичны
"
```

**Почему это важно:** это не ошибка — такой подход правомерен для диагностики механики
исполнения. Но `docs/methodology/03-feature-contract-leakage.md` (строка 77) явно требует
для этого случая пометки `DIAGNOSTIC_ONLY` и запрещает интерпретировать результат как
доказательство качества ML. Если в отчёте написать "timing contract PASS" без оговорки о
тривиальности, следующий агент может неверно интерпретировать это как полноценную leakage-проверку.

**Рекомендуемое исправление:** добавить в Task 2 Mandatory checks (строка 213) и в Known
Unknowns (строка 43) явную оговорку: для источников, где `feature_time == feature_available_time
== decision_time` (результат `prepare_mt5_entry_source`), timing contract является тривиальным
и не доказывает, что признаки доступны раньше момента решения; это нужно явно указать в
разделе Limitations отчёта.

---

## Использованные первоисточники

Все замечания опираются только на следующие реально прочитанные файлы:

- `docs/superpowers/plans/2026-07-30-mt5-single-rule-diagnostic-run.md` — проверяемый план
- `docs/superpowers/roadmap.md` — правила структуры планов
- `docs/reports/2026-07-29-mt5-execution-loop-migration.md` — родительский отчёт
- `docs/methodology/03-feature-contract-leakage.md` — leakage gate
- `docs/methodology/12-backtest-costs.md` — backtest costs
- `docs/methodology/13-export-mt4-parity.md` — parity и reconciliation
- `docs/methodology/13b-mt5-execution-parity.md` — основная методика плана
- `docs/methodology/16-reporting-audit.md` — требования к отчёту
- `ML/baseline/mt5_signal_schema.py` — схема и валидаторы
- `ML/baseline/export_mt5_entry_signals.py` — экспортёр
- `ML/baseline/parse_mt5_execution_report.py` — парсер событий
- `ML/baseline/prepare_mt5_entry_source.py` — мост для источников без timing-полей
- `tests/test_mt5_signal_executor_schema.py`, `tests/test_parse_mt5_execution_report.py`
- `MT/MQL5/Experts/$o$imple.mq5` — строки 72–77
- `MT/MQL5/Include/lib_ML_Signal.mqh` — строки 390, 569, 585, 591, 609, 625
- `ML/reports/fractal0_entry_quality_filter_scores.csv` — реальный source-кандидат
- `ML/reports/mt5_execution_loop/mt5_entry_source_20260730_entry_quality_filter.{csv,json}`
- `ML/reports/mt5_execution_loop/mt5_entry_signals_20260730_entry_quality_filter.{csv,json}`
- `ML/reports/mt5_execution_loop/mt5_single_rule_run_manifest_20260730_entry_quality_filter.json`
- Python-проверки, запущенные непосредственно на перечисленных файлах репозитория
