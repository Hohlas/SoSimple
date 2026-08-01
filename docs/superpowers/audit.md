# Аудит отчёта `docs/reports/2026-08-01-mt5-diagnostic-timing-contract.md`

Дата аудита: 2026-08-01

Проверенный объём:

- полный отчёт `docs/reports/2026-08-01-mt5-diagnostic-timing-contract.md`;
- артефакты последнего комита `ef6672d fix: harden mt5 diagnostic runtime checks`;
- связанные первичные файлы: `ML/baseline/mt5_signal_schema.py`, `ML/baseline/prepare_mt5_entry_source.py`, `ML/baseline/export_mt5_entry_signals.py`, `ML/baseline/run_mt5_batch.py`, `ML/baseline/mt5_execution_diagnostics.py`, `MT/MQL5/Include/lib_ML_Signal.mqh`, связанные тесты, `docs/methodology/03-feature-contract-leakage.md`, `docs/methodology/13b-mt5-execution-parity.md`, `docs/methodology/16-reporting-audit.md`;
- structured artifacts: `ML/reports/mt5_execution_loop/batch/batch_summary.json`, `ML/reports/mt5_execution_loop/diagnostics/event_anomaly_summary.json`, `ML/reports/mt5_execution_loop/batch/*/entry_signals.json`, `ML/reports/mt5_execution_loop/batch/*/entry_signals.csv`, `/tmp/sosimple_mt5_compile.log`.

## 1. В методологии `13b` осталась противоречивая формулировка event timing contract

- **Важность:** важно
- **Место:** `docs/reports/2026-08-01-mt5-diagnostic-timing-contract.md`, `What Was Done`, строка 28; `docs/methodology/13b-mt5-execution-parity.md`, `CSV contract`, строки 76-84.
- **Суть проблемы:** отчёт утверждает, что методология `13b` синхронизирована с новым `time`-only matching, но в самой методологии блок `Timing contract` пишет `feature_time <= time < feature_available_time <= decision_time <= execution_time`. В этом же разделе ниже сказано, что в event log колонка `time` означает время события, а исходная signal CSV `time` записывается как `signal_time`.
- **Доказательство:** `docs/methodology/13b-mt5-execution-parity.md:73` содержит event header с отдельными `time` и `signal_time`; `docs/methodology/13b-mt5-execution-parity.md:79` использует `time` в timing chain; `docs/methodology/13b-mt5-execution-parity.md:82-84` объясняет, что event `time` уже не signal time. Код проверяет другую цепочку: `ML/baseline/mt5_signal_schema.py:228-237` и `ML/baseline/mt5_execution_diagnostics.py:340-383` используют `signal_time`.
- **Почему это важно:** следующий исполнитель может внедрить проверку по event `time` и получить ложные нарушения: для `OPEN`/`ML_EVAL` event `time` является временем события, а не временем исходного сигнала.
- **Рекомендуемое исправление:** в `13b` разделить два контракта:
  - signal CSV: `feature_time <= time < feature_available_time <= decision_time`;
  - event CSV для signal-linked rows: `feature_time <= signal_time < feature_available_time <= decision_time <= execution_time`.
  Отдельно указать, что event column `time` не участвует в этой цепочке как signal time.

## 2. Отчёт завышает строгость event schema для signal-linked rows

- **Важность:** важно
- **Место:** `docs/reports/2026-08-01-mt5-diagnostic-timing-contract.md`, `What Was Done`, строка 24.
- **Суть проблемы:** формулировка говорит, что event schema и diagnostics проверяют `feature_time <= signal_time < feature_available_time <= decision_time <= execution_time` для signal-linked rows. Фактически Python-схема применяет строгую цепочку только к signal-linked rows, у которых все timing-поля непустые; строка signal-linked event с пустым `signal_time` проходит `validate_mt5_event_frame`.
- **Доказательство:** `ML/baseline/mt5_signal_schema.py:216-228` строит `timing_mask` через `_nonempty_timestamp_mask` и передаёт в strict-check только `frame.loc[linked_mask & timing_mask]`; `ML/baseline/mt5_execution_diagnostics.py:356-358` отдельно обрабатывает complete timing rows и legacy rows without `signal_time`. Команда:

```bash
./.venv/bin/python - <<'PY'
import pandas as pd
from ML.baseline.mt5_signal_schema import MT5_EVENT_COLUMNS, validate_mt5_event_frame
from tests.test_parse_mt5_execution_report import _event_row
frame = pd.DataFrame([_event_row('OPEN','2023.01.02 10:05', signal_time='')], columns=MT5_EVENT_COLUMNS)
try:
    validate_mt5_event_frame(frame)
    print('accepted_empty_signal_time')
except Exception as e:
    print(type(e).__name__, e)
PY
```

выводит `accepted_empty_signal_time`.

- **Почему это важно:** отчёт создаёт впечатление, что новый event contract полностью enforced для всех signal-linked rows. На деле часть legacy-tolerance остаётся, и это нужно явно раскрыть, иначе можно принять неполный event log за полностью проверенный.
- **Рекомендуемое исправление:** либо ужесточить `validate_mt5_event_frame` для новых signal-linked rows и отдельно оставить legacy-loader в diagnostics, либо уточнить отчёт: strict chain проверяется для signal-linked rows with complete timing fields; rows without `signal_time` считаются legacy/partial и должны получать отдельный статус.

## 3. `Changed Files` не отражает файлы последнего комита

- **Важность:** улучшение
- **Место:** `docs/reports/2026-08-01-mt5-diagnostic-timing-contract.md`, `Changed Files`, строки 39-52.
- **Суть проблемы:** раздел не упоминает `CHANGELOG.md` и `tests/test_mt5_batch_runtime_contract.py`, хотя оба файла входят в последний комит с этим отчётом и прямо связаны с финальным hardening.
- **Доказательство:** команда `git show --name-only --format='' HEAD` выводит:

```text
CHANGELOG.md
ML/baseline/mt5_execution_diagnostics.py
ML/baseline/run_mt5_batch.py
docs/methodology/13b-mt5-execution-parity.md
docs/reports/2026-08-01-mt5-diagnostic-timing-contract.md
tests/test_mt5_batch_runtime_contract.py
```

`tests/test_mt5_batch_runtime_contract.py:11-19` проверяет reject ненулевого tester exit code; `tests/test_mt5_batch_runtime_contract.py:22-48` проверяет удаление stale tester event file перед batch run.

- **Почему это важно:** handoff по отчёту теряет новый runtime regression-test и обновление changelog. Это затрудняет проверку, что именно было добавлено последним hardening-комитом.
- **Рекомендуемое исправление:** добавить `CHANGELOG.md` и `tests/test_mt5_batch_runtime_contract.py` в `Changed Files` или разделить список на `Stage changed files` и `Final hardening commit artifacts`.

## 4. Verification counts устарели после добавления runtime-теста

- **Важность:** важно
- **Место:** `docs/reports/2026-08-01-mt5-diagnostic-timing-contract.md`, `Verification`, строки 93-120.
- **Суть проблемы:** отчёт фиксирует targeted subset как `50 passed` и full suite как `1565 passed, 1 failed, 52 warnings`. В финальном состоянии последнего комита добавлен `tests/test_mt5_batch_runtime_contract.py` с тремя тестами, поэтому актуальная проверка связанных тестов даёт `53 passed`, а полный набор даёт `1568 passed, 1 failed, 52 warnings`.
- **Доказательство:** команда

```bash
./.venv/bin/python -m pytest tests/test_mt5_signal_executor_schema.py tests/test_parse_mt5_execution_report.py tests/test_mt5_execution_diagnostics.py tests/test_mt5_batch_runtime_contract.py -q
```

выводит `53 passed in 0.60s`. Команда

```bash
./.venv/bin/python -m pytest tests/ -q
```

выводит `1 failed, 1568 passed, 52 warnings in 415.77s`. Сбой тот же, что указан в отчёте: `tests/test_mql_telemetry_params_csv_contract.py::test_tester_ini_selects_telemetry_backtest_row`; тест ждёт `BackTest=2` на `tests/test_mql_telemetry_params_csv_contract.py:182`, а `MT/tester/$o$imple.ini:10` содержит `BackTest=0`.

- **Почему это важно:** отчёт претендует на финальную проверку после hardening, но числа соответствуют состоянию до добавления трёх runtime-тестов. Это не меняет verdict, но делает verification-блок неточным.
- **Рекомендуемое исправление:** обновить Verification:
  - добавить `tests/test_mt5_batch_runtime_contract.py` в targeted command;
  - заменить `50 passed` на `53 passed`;
  - заменить full suite count на `1568 passed, 1 failed, 52 warnings`, если отчёт должен описывать текущее состояние `HEAD`.

## 5. `Split Disclosure` короче обязательного раскрытия по методологии

- **Важность:** улучшение
- **Место:** `docs/reports/2026-08-01-mt5-diagnostic-timing-contract.md`, `Split Disclosure`, строки 171-177.
- **Суть проблемы:** раздел указывает только `VAL_FROM`, `VAL_TO` и `locked_test: not opened`. По методологии отчёта нужно раскрыть границы `train`/`validation`/`locked_test`, роли `val-stop`/`val-select`/`val-eval` и `sample_size_gate`, либо явно написать, что часть пунктов неприменима для diagnostic-only rerun.
- **Доказательство:** `docs/methodology/16-reporting-audit.md:28` требует Split Disclosure с границами split, ролями validation и `sample_size_gate`; `docs/methodology/16-reporting-audit.md:94` требует количество строк, событий, сигналов и сделок после фильтров по каждому split. В текущем отчёте `docs/reports/2026-08-01-mt5-diagnostic-timing-contract.md:171-177` есть только validation dates и locked_test. Границы validation в коде подтверждаются `ML/baseline/run_mt5_batch.py:27-28`; использование `val_select` видно в `ML/baseline/run_mt5_batch.py:100-109`.
- **Почему это важно:** этап помечен `DIAGNOSTIC_ONLY`, но он повторно прогоняет 32 ранее выбранных validation-кандидата. Без явного split-role disclosure следующий агент может спутать diagnostic rerun с новым selection или не увидеть, какие части split-протокола не применялись.
- **Рекомендуемое исправление:** расширить `Split Disclosure` минимум так:
  - `train: not used in this stage; inherited candidate training/search context from prior batch report`;
  - `validation: 2021-01-04..2022-12-02; source role used by runner is val_select`;
  - `val-stop/val-eval: not used by this timing-contract rerun, inherited/unchanged if applicable`;
  - `locked_test: not opened`;
  - `sample_size_gate: no winner selection in this stage; batch artifact reports n_candidates=32, n_valid=2, n_eligible=0`.
