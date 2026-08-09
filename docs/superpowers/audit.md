# Аудит: docs/reports/2026-08-01-mt5-diagnostic-timing-contract.md

**Дата аудита**: 2026-08-08
**Аудитор**: Qoder
**Объект**: отчёт этапа MT5 Diagnostic Timing Contract

---

## Резюме

Отчёт достоверен. Все ключевые фактические утверждения подтверждены сверкой с кодом, тестами, артефактами и методологией. Критических и важных проблем не обнаружено. Обнаружены 3 замечания уровня «улучшение» и 2 вопроса.

---

## Проверенные утверждения (все подтверждены)

### Timing contract в коде

| Утверждение отчёта | Подтверждение |
|---|---|
| Python schema проверяет `feature_time <= time < feature_available_time <= decision_time` | `mt5_signal_schema.py:180-184`: `_validate_strict_timing_chain` с `strict_pairs={("time", "feature_available_time")}` |
| Event schema проверяет `feature_time <= signal_time < feature_available_time <= decision_time <= execution_time` | `mt5_signal_schema.py:228-238`: аналогичный вызов для 5 колонок с `strict_pairs={("signal_time", "feature_available_time")}` |
| MQL5 reader матчится только по `time` | `lib_ML_Signal.mqh:207-212`: `MT5_FindEntrySignal` использует только `MT5_EntryTimes[i] == barTime`, без OR с `decision_time` |
| MQL5 отклоняет неверные строки через `TIMING_VIOLATION` | `lib_ML_Signal.mqh:664-678`: `MT5_IsEntryTimingValid` + `MT5_LogTimingViolation` + `continue` |
| Entry source bridge формирует H1 timing | `prepare_mt5_entry_source.py:89-92`: `feature_time=signal_dt`, `feature_available_time=signal_dt+1h`, `decision_time=feature_available_time+latency_bars*h`, `match_time=decision_time-1h` |
| Export metadata пишет `timing_contract`, `latency_bars` и включает их в `run_config_hash` | `export_mt5_entry_signals.py:153-184`: `run_config` содержит оба ключа, `run_config_hash` вычисляется из полного `run_config` |
| `TIMING_VIOLATION` добавлен в `MT5_EVENT_NAMES` | `mt5_signal_schema.py:196` |

### Числовые данные в отчёте

| Утверждение | Фактическое значение | Источник |
|---|---|---|
| `batch_summary.json`: `n_candidates=32` | 32 | `batch_summary.json` |
| `n_valid=32` | 32 | `batch_summary.json` |
| `n_eligible=11` | 11 | `batch_summary.json` |
| `n_diagnostic_only=16` | 16 | `batch_summary.json` |
| `status=DIAGNOSTIC_ONLY` | DIAGNOSTIC_ONLY | `batch_summary.json` |
| `verdict=BATCH_NO_WINNER` | BATCH_NO_WINNER | `batch_summary.json` |
| `batch_runs.total_rows=54078` | 54078 | `event_anomaly_summary.json` |
| `batch_runs.timing_contract.checked_rows=49030` | 49030 | `event_anomaly_summary.json` |
| `batch_runs.timing_contract.violation_rows=0` | 0 | `event_anomaly_summary.json` |
| `batch_runs.timing_contract.timing_violation_event_count=0` | 0 | `event_anomaly_summary.json` |
| `reference_runs.timing_contract.checked_rows=22510` | 22510 | `event_anomaly_summary.json` |
| `reference_runs.timing_contract.violation_rows=22510` | 22510 | `event_anomaly_summary.json` |
| 32/32 `entry_signals.json` включают `timing_contract` и `latency_bars=0` | 32/32 подтверждено | Прямая проверка `entry_signals.json` |
| 32/32 кандидатских директорий содержат `events.csv` | 32 подтверждено | Прямая проверка `batch/*/events.csv` |
| `validation: 2021-01-04..2022-12-02` | `{'from': '2021-01-04', 'to': '2022-12-02'}` | `batch_summary.json` |

### Методология 13b синхронизирована

| Требование | Статус |
|---|---|
| Единый ключ матчинга `time` (не OR) | Подтверждено: `13b-mt5-execution-parity.md:35` — «Строка выбирается только по колонке `time`» |
| Timing contract for signal CSV | Подтверждено: `13b-mt5-execution-parity.md:79` — `feature_time <= time < feature_available_time <= decision_time` |
| Timing contract for event rows | Подтверждено: `13b-mt5-execution-parity.md:85` — `feature_time <= signal_time < feature_available_time <= decision_time <= execution_time` |
| `TIMING_VIOLATION` в списке событий | Подтверждено: `13b-mt5-execution-parity.md:111` |

### LiveUpdate mitigation

| Утверждение | Подтверждение |
|---|---|
| Копирование в terminal и tester Files | `run_mt5_batch.py:400-403`: `copy_entry_signal_file` копирует в `TERMINAL_FILES` и `TESTER_FILES` |
| Отказ при LiveUpdate redirect | `run_mt5_batch.py:362-366`: проверка `"LiveUpdate\tstart" in line` |
| Retry после LiveUpdate | `run_mt5_batch.py:385-396`: цикл retry с `wait_for_liveupdate_clear()` |
| Тесты на LiveUpdate behavior | `test_mt5_batch_runtime_contract.py:22-77`: тесты reject/retry |

### Pre-existing failure

| Утверждение | Подтверждение |
|---|---|
| `test_tester_ini_selects_telemetry_backtest_row` fails | Запуск `pytest` подтвердил: `1 failed in 0.02s` |
| Причина: `BackTest=0` vs ожидаемое `BackTest=2` | Не менялся этим этапом |

---

## Замечания

### 1. Улучшение: количество тестов в Verification неактуально

- **Важность**: улучшение
- **Место**: раздел Verification, строка «Results: targeted final subset passed (`55 passed`)»
- **Суть**: Отчёт утверждает 55 пройденных тестов для 4 файлов, но текущий запуск тех же 4 файлов даёт 62 passed.
- **Доказательство**: `pytest tests/test_mt5_signal_executor_schema.py tests/test_parse_mt5_execution_report.py tests/test_mt5_execution_diagnostics.py tests/test_mt5_batch_runtime_contract.py -q` → `62 passed in 0.47s`
- **Почему важно**: Последующий коммит `ed2fd9c` (MT5 per-expert ML tracker) добавил тесты в эти файлы. Отчёт был точен на момент написания, но число 55 теперь не воспроизводится.
- **Рекомендация**: Можно добавить сноску «число тестов может отличаться в последующих коммитах» или зафиксировать хеш коммита, на котором проводилась проверка.

### 2. Улучшение: источник `checked_signal_files=32, bad_files=0` не трассируется из артефактов

- **Важность**: улучшение
- **Место**: раздел Results, строка «signal timing check: `checked_signal_files=32`, `bad_files=0`»
- **Суть**: Этот результат не присутствует в `event_anomaly_summary.json` или `batch_summary.json`. Он логически следует из того, что `run_mt5_batch --phase signals` успешно завершается для всех 32 кандидатов (экспорт вызывает `validate_mt5_signal_frame`, и любая ошибка прервала бы пайплайн), но прямой артефакт отсутствует.
- **Доказательство**: Поиск по `ML/reports/mt5_execution_loop/` не содержит поля `checked_signal_files` или `bad_files`.
- **Почему важно**: Для воспроизводимости аудита каждый числовой результат должен иметь прямой источник.
- **Рекомендация**: Либо ссылаться на stdout `run_mt5_batch --phase signals`, либо добавить явную проверку в `run_mt5_batch.py`, которая записывает результат валидации сигналов в артефакт.

### 3. Улучшение: неясность вокруг 5 кандидатов (32 - 11 - 16 = 5)

- **Важность**: улучшение
- **Место**: раздел Results, `batch_summary.json` числа
- **Суть**: `n_candidates=32`, `n_eligible=11`, `n_diagnostic_only=16`. Разница `32 - 11 - 16 = 5` не объяснена. Это кандидаты, которые не прошли eligibility gates и не помечены как diagnostic-only.
- **Доказательство**: `batch_summary.json` содержит только агрегированные числа без покандидатного объяснения.
- **Почему важно**: Читатель отчёта не может понять, почему 5 кандидатов выпали из обеих категорий.
- **Рекомендация**: Добавить одно предложение в Results или Limitations, объясняющее эти 5 кандидатов (например, «5 кандидатов не прошли gate по bootstrap p-value или profit concentration»).

### 4. Вопрос: `latency_bars>0` и сигналный timing contract

- **Важность**: вопрос
- **Место**: раздел What Was Done, описание H1 timing
- **Суть**: Формула `time=decision_time-1h` при `latency_bars>0` даёт `time > feature_available_time`, что нарушает контракт `time < feature_available_time`. Это корректно защищено валидацией (`validate_mt5_signal_frame` отвергнет такой фрейм), но отчёт не упоминает, что контракт signal CSV справедлив только при `latency_bars=0`.
- **Доказательство**: `prepare_mt5_entry_source.py:89-92` при `latency_bars=2`: `time=12:00`, `feature_available_time=11:00` → `12:00 < 11:00` ложно. Тест `test_prepare_mt5_entry_source_latency_bars_shifts_match_time_to_decision_minus_one_bar` проверяет значения, но не вызывает `validate_mt5_signal_frame`.
- **Почему важно**: Если кто-то попытается экспортировать сигналы с `latency_bars>0` через полный пайплайн, экспорт упадёт с `ValueError`. Это защитный механизм, но он не описан в отчёте.
- **Рекомендация**: Добавить в Limitations предложение: «Контракт `feature_time <= time < feature_available_time <= decision_time` справедлив при `latency_bars=0`; при `latency_bars>0` экспорт будет отклонён валидатором, что является защитным механизмом.»

### 5. Вопрос: `docs/schemas/mt5_signal_executor_schema.md` упомянут в плане, но не создан

- **Важность**: вопрос
- **Место**: `docs/superpowers/plans/2026-08-01-mt5-diagnostic-timing-contract.md` (Task 6)
- **Суть**: План содержит условную инструкцию: «If `docs/schemas/mt5_signal_executor_schema.md` was not created, run...». Файл не существует. Отчёт не упоминает его в Changed Files, что согласовано.
- **Доказательство**: `test -f docs/schemas/mt5_signal_executor_schema.md` → MISSING
- **Почему важно**: План предполагал возможность создания этого файла. Его отсутствие не является ошибкой отчёта, но создаёт неполноту в документации схемы.
- **Рекомендация**: Решить, нужен ли отдельный файл схемы для signal/event CSV, или достаточно `mt5_signal_schema.py` как executable source of truth. Если нужен — создать в отдельном этапе.

---

## Проверка корректности кода

### Алгоритмическая корректность timing computation

Для `latency_bars=0`, `signal_time = T`:
- `feature_time = T`
- `feature_available_time = T + 1h`
- `decision_time = T + 1h`
- `time = T + 1h - 1h = T`

Контракт: `T <= T < T+1h <= T+1h` → выполнено.

Для `latency_bars=2`, `signal_time = T`:
- `feature_time = T`
- `feature_available_time = T + 1h`
- `decision_time = T + 3h`
- `time = T + 2h`

Контракт: `T <= T+2h < T+1h` → **нарушено** (защищено валидатором).

Контрольный пример из теста `test_prepare_mt5_entry_source_from_entry_quality_scores_contract`:
- Вход: `signal_time = "2023.01.02 10:00"`, `side = "SELL"`
- Ожидаемый выход: `time = "2023.01.02 10:00"`, `feature_available_time = "2023.01.02 11:00"`, `decision_time = "2023.01.02 11:00"`
- Фактический выход: совпадает ✓

### MQL5 timing validation

`MT5_IsEntryTimingValid` (`lib_ML_Signal.mqh:214-218`):
```c
return (feature_time <= entry_time &&
        entry_time < feature_available_time &&
        feature_available_time <= decision_time);
```
Соответствует контракту `feature_time <= time < feature_available_time <= decision_time`. ✓

### Edge cases

- Пустой DataFrame: `_validate_strict_timing_chain` проверяет `if frame.empty: return` (`mt5_signal_schema.py:147`). ✓
- Строки без `signal_time`: `summarize_timing_contract` имеет отдельный legacy-путь (`mt5_execution_diagnostics.py:332-337`). ✓
- `TX_OPEN`/`TX_CLOSE` с пустыми timing-полями: исключены из проверки через `TIMING_CHECK_EVENT_NAMES` и `_nonempty_timestamp_mask`. ✓
- Невалидные timestamp: `summarize_timing_contract` считает их отдельно (`invalid_timestamp_rows`). ✓

---

## Согласованность артефактов

| Артефакт | Статус |
|---|---|
| `ML/reports/mt5_execution_loop/batch/batch_summary.json` | Существует, числа совпадают |
| `ML/reports/mt5_execution_loop/diagnostics/event_anomaly_summary.json` | Существует, числа совпадают |
| `docs/superpowers/specs/2026-08-01-mt5-diagnostic-timing-contract-design.md` | Существует |
| `docs/superpowers/plans/2026-08-01-mt5-diagnostic-timing-contract.md` | Существует |
| `docs/methodology/13b-mt5-execution-parity.md` | Синхронизирован |
| `docs/ML/mt5_execution_loop.md` | Синхронизирован |
| `docs/methodology/03-feature-contract-leakage.md` | Существует |
| `docs/methodology/16-reporting-audit.md` | Существует |
| `docs/reports/2026-07-31-mt5-batch-selection.md` | Существует |
| `docs/reports/2026-08-01-mt5-execution-hygiene-postbatch.md` | Существует |
| `docs/schemas/mt5_signal_executor_schema.md` | **Отсутствует** (опциональный, см. вопрос 5) |

---

## Итог

Отчёт качественно выполнен, фактологически точен и методологически корректен. Все изменения в коде соответствуют описанию. Timing contract реализован последовательно в Python, MQL5 и документации. LiveUpdate mitigation работает и покрыт тестами. DIAGNOSTIC_ONLY вердикт соблюдён, winner selection не проводился.

Замечания не влияют на корректность выводов отчёта и относятся к уровню документальной полноты.
