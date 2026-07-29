# Аудит отчётов fixed11 Python/MT4 fill chronology

Дата аудита: 2026-07-29

Проверены полностью:

- `docs/reports/2026-07-27-fractal0-fixed11-retained-subset-mt4-parity.md`
- `docs/reports/2026-07-29-fixed11-python-mt4-fill-chronology.md`

Точечно проверены связанные первоисточники:

- `docs/superpowers/plans/2026-07-27-fixed11-retained-subset-mt4-parity.md`
- `docs/superpowers/roadmap.md`
- `docs/methodology/README.md`
- `docs/methodology/10-frozen-test-oos.md`
- `docs/methodology/12-backtest-costs.md`
- `docs/methodology/13-export-mt4-parity.md`
- `docs/methodology/A4-verdicts-stop-conditions.md`
- `ML/baseline/benchmark_fractal0_entry_exit_grid.py`
- `ML/reports/fractal0_fixed11_rich_entry_locked_test.json`
- `ML/reports/fractal0_fixed11_rich_entry_locked_test_trades.csv`
- `MT/tester/files/ML_Trade_Events_SoSimple_1709200448.csv`

## Вывод

Последний отчёт от 2026-07-29 в целом фактически подтверждается текущими кодом и CSV-артефактами. Главный вывод о статусе `DIAGNOSTIC_ONLY` и о неполном execution contract между Python и MT4 соответствует методологии.

Основные проблемы не в логике последнего вывода, а в воспроизводимости доказательств: часть чисел получена одноразовыми inline-скриптами, а один MT4 event-log path используется в двух отчётах для разных прогонов.

## Замечания

### 1. Важно: один и тот же MT4 event-log path используется как доказательство двух разных прогонов

- Место: `docs/reports/2026-07-27-fractal0-fixed11-retained-subset-mt4-parity.md`, строки 89-129; `docs/reports/2026-07-29-fixed11-python-mt4-fill-chronology.md`, строки 13 и 135-142.
- Суть проблемы: оба отчёта ссылаются на `MT/tester/files/ML_Trade_Events_SoSimple_1709200448.csv`, но описывают разные counts.
- Доказательство:
  - отчёт 2026-07-27 утверждает `ORDER_PLACED=1132`, `OPEN=1072`, `CLOSE=1072`, `OPEN_FAILED=5`;
  - отчёт 2026-07-29 утверждает `ORDER_PLACED=1115`, `OPEN=717`, `CLOSE=717`, `OPEN_FAILED=404`;
  - текущий файл даёт второй набор: команда `./.venv/bin/python` с `csv.DictReader(..., delimiter=";")` по `MT/tester/files/ML_Trade_Events_SoSimple_1709200448.csv` вернула `{'ORDER_PLACED': 1115, 'OPEN': 717, 'CLOSE': 717, 'OPEN_FAILED': 404}`.
- Почему это важно: отчёт 2026-07-27 сейчас нельзя воспроизвести по указанному артефакту. Это снижает доказательную силу предыстории и может привести к неверной сверке, если читатель использует текущий файл как "fresh MLClose run" из старого отчёта.
- Рекомендуемое исправление: в отчёте 2026-07-27 явно пометить, что файл был перезаписан новым stale-handling прогоном, либо добавить сохранённый snapshot старого event-log с уникальным именем и ссылкой. Для будущих прогонов сохранять immutable path, например с датой, настройкой и кратким hash.

### 2. Важно: численные проверки последнего отчёта не воспроизводимы как отдельный артефакт

- Место: `docs/reports/2026-07-29-fixed11-python-mt4-fill-chronology.md`, строки 87-92, 135-149, 157-174, 180-193, 242-249.
- Суть проблемы: отчёт сообщает важные counts по stale-категориям, H1-vs-HST отличиям, M5 first touch и PnL buckets, но вместо кода проверки сохранён только заглушечный inline-блок.
- Доказательство:
  - строки 87-92 показывают только комментарий внутри `./.venv/bin/python - <<'PY'`, без реального скрипта;
  - методология требует reconciliation tool как вход (`docs/methodology/13-export-mt4-parity.md`, строки 7-13) и reconciliation report как обязательную проверку (строки 50-55);
  - сам отчёт признаёт, что reusable reconciliation script ещё не создан (`docs/reports/2026-07-29-fixed11-python-mt4-fill-chronology.md`, строки 281-282).
- Почему это важно: выводы выглядят правдоподобно и частично проверяются текущими CSV, но будущий аудит не сможет точно повторить HST/M1/M5 проверки, offset-поиск и классификацию `M5 no hit` без восстановления логики вручную.
- Рекомендуемое исправление: добавить read-only reconciliation script или notebook-free Python-модуль, который воспроизводит таблицы отчёта: event counts, stale counts, PnL по stale keys, H1-vs-HST diff by year, first M5/M1 touch для examples и агрегаты `hold_bars=0`.

### 3. Важно: вывод о рассинхроне Python H1 и текущей MT4 history недостаточно привязан к конкретным файлам HST

- Место: `docs/reports/2026-07-29-fixed11-python-mt4-fill-chronology.md`, строки 157-174.
- Суть проблемы: отчёт ссылается на ручную проверку `XAUUSD60.hst`, `XAUUSD5.hst`, `XAUUSD1.hst`, но не указывает точные пути, размеры, время изменения, hash или команду чтения `.hst`.
- Доказательство:
  - в `Context` указаны только имена файлов без пути (`docs/reports/2026-07-29-fixed11-python-mt4-fill-chronology.md`, строка 18);
  - результат по годам указан численно, но в `Verification` нет кода для чтения HST, есть только общий комментарий (`строки 87-92`);
  - методология требует зафиксировать execution contract и источник младшего таймфрейма; если broker/source/timezone/price convention не совпадают, результат не выше `DIAGNOSTIC_ONLY` (`docs/methodology/12-backtest-costs.md`, строки 96-98).
- Почему это важно: рассинхрон истории с 2023 года является одним из трёх объяснений высокого MT4 PnL. Без точной фиксации HST-источников нельзя отличить реальный data drift от ошибки чтения файла, другой папки tester, другого broker history или последующего обновления истории.
- Рекомендуемое исправление: добавить в отчёт или отдельный JSON manifest точные пути HST, `sha256`, `mtime`, период, timezone/offset-проверку, формат парсера и команду, которая считает yearly diff.

### 4. Улучшение: в отчёте не раскрыты hash экспортов и проверяемого event-log

- Место: `docs/reports/2026-07-29-fixed11-python-mt4-fill-chronology.md`, разделы `Context`, `Verification`, `Related Materials`.
- Суть проблемы: отчёт перечисляет CSV/JSON пути, но не фиксирует hash для `ML_Trade_Events_SoSimple_1709200448.csv`, `ml_signals_fixed11_ruleNN.csv`, `ml_exits_fixed11_ruleNN.csv`, H1/M5 CSV и Python trades CSV.
- Доказательство:
  - методология `docs/methodology/13-export-mt4-parity.md` требует зафиксировать hash экспортированного файла, строка 18;
  - отчёт 2026-07-29 не содержит `sha256` для связанных файлов;
  - Python metadata содержит hash для M5 execution OHLC (`ML/reports/fractal0_fixed11_rich_entry_locked_test.json`, строки 12-13), но отчёт не переносит его в проверочный manifest.
- Почему это важно: parity-аудит чувствителен к перезаписи CSV и tester history. Без hash нельзя доказать, что отчёт, Python trades и MT4 event-log относятся к одному состоянию данных.
- Рекомендуемое исправление: добавить секцию `Artifact hashes` или отдельный manifest в `ML/reports/fractal0_fixed11_retained_mt4_parity/`, включив hash всех входов и выходов, которые участвуют в сверке.

### 5. Вопрос: "код и CSV-артефакты этим анализом не менялись" конфликтует с текущим состоянием event-log, если stale handling был частью того же шага

- Место: `docs/reports/2026-07-29-fixed11-python-mt4-fill-chronology.md`, строки 69-74 и 135-142.
- Суть проблемы: отчёт утверждает, что код и CSV-артефакты не менялись, но результат `ORDER_PLACED=1115`, `OPEN_FAILED=404` содержится в том же CSV path, который в отчёте 2026-07-27 ранее содержал `ORDER_PLACED=1132`, `OPEN_FAILED=5`.
- Доказательство:
  - текущее содержимое `MT/tester/files/ML_Trade_Events_SoSimple_1709200448.csv` подтверждает counts отчёта 2026-07-29;
  - отчёт 2026-07-27, строки 89-129, использует тот же path для другого результата;
  - по имеющимся файлам нельзя установить, был ли CSV перезаписан до начала анализа 2026-07-29 или в ходе анализа. Это именно вопрос, а не доказанная ошибка.
- Почему это важно: формулировка может быть понята как "текущие артефакты не затрагивались", хотя фактически проверяемый event-log уже отличается от предшествующего отчёта.
- Рекомендуемое исправление: уточнить фразу: "в рамках написания отчёта не менялись Python code/trades/export CSV; анализ использовал уже созданный stale-handling MT4 event-log". Если stale-handling требовал изменения MQL4 до этого анализа, добавить ссылку на соответствующий commit/report.

### 6. Улучшение: статус `DIAGNOSTIC_ONLY` корректен, но стоит явно связать его с методическим blocker

- Место: `docs/reports/2026-07-29-fixed11-python-mt4-fill-chronology.md`, строки 260-274 и 276-287.
- Суть проблемы: вывод правильный, но отчёт не цитирует конкретные stop conditions, из-за которых нельзя продолжать проверочный cycle как будто parity почти пройден.
- Доказательство:
  - `docs/methodology/A4-verdicts-stop-conditions.md`, строки 40-51, требует остановить проверочный cycle, если MT4 parity показывает critical mismatch;
  - `docs/methodology/10-frozen-test-oos.md`, строки 31 и 37, ограничивает verdict при неполном или изменённом execution contract;
  - `docs/methodology/13-export-mt4-parity.md`, строки 60-64, требует либо `critical_mismatch_count = 0`, либо явно принятые non-blocking расхождения.
- Почему это важно: следующий шаг должен быть не "докрутить текущий кандидат", а исправить contract и заново пересчитать locked-test artifacts. Отчёт это говорит, но методическая привязка сделает запрет сильнее и менее двусмысленным.
- Рекомендуемое исправление: добавить в `Conclusions` или `Next Step` короткую ссылку: "по A4 stop condition это blocker проверочного cycle; до пересчёта artifacts статус не выше `DIAGNOSTIC_ONLY`".

### 7. Улучшение: примеры нарушения хронологии подтверждаются Python trades, но M5 first-touch доказательство не приложено

- Место: `docs/reports/2026-07-29-fixed11-python-mt4-fill-chronology.md`, строки 210-240.
- Суть проблемы: строки Python trades подтверждают `signal_time`, `fill_time`, `exit_time`, `limit`, `close_reason` и `pnl_r` для обоих примеров, но первое M5-касание `03:10` и `03:15` не воспроизводится из отчёта.
- Доказательство:
  - `rg` по `ML/reports/fractal0_fixed11_rich_entry_locked_test_trades.csv` подтверждает пример 1 для rule `rank05_time_only_linear_target_entry_avoid_sl_top30`: `signal_time=2022-12-05 23:00:00`, `fill_time=2022-12-06 03:00:00`, `ML_CLOSE`, `pnl_r=-0.3085365853658486`, `limit=1772.28`;
  - тот же CSV подтверждает пример 2: `signal_time=2022-12-14 22:00:00`, `fill_time=2022-12-15 03:00:00`, `ML_CLOSE`, `pnl_r=-0.3793478260869556`, `limit=1802.05`;
  - команда или сохранённая таблица, доказывающая first M5 touch, отсутствует.
- Почему это важно: именно M5 first-touch делает эти примеры доказательством нарушения хронологии, а не просто сделками с одинаковым H1 `fill_time == exit_time`.
- Рекомендуемое исправление: сохранить небольшой CSV `chronology_examples.csv` с колонками `signal_time`, `side`, `limit`, `python_fill_time`, `python_exit_time`, `first_m5_touch_time`, `first_m5_bar_ohlc`, `source_m5_sha256`.

## Подтверждённые утверждения без замечаний

- `execution_ohlc_path = MT/MQL4/Files/XAUUSD_M5_OHLC.csv` подтверждён в `ML/reports/fractal0_fixed11_rich_entry_locked_test.json`, строка 12.
- `execution_ohlc_usage = resolve_same_h1_bar_tp_sl_order_only` подтверждён в `ML/baseline/benchmark_fractal0_entry_exit_grid.py`, строка 1467.
- M5 используется в `_resolve_same_bar_with_execution_ohlc(...)` только для порядка SL/TP: функция проверяет `stop_hit` и `tp_hit` на строках 536-545, а вызывается при ambiguous SL/TP на строках 571-577.
- Python fill фиксируется H1 timestamp: `build_entry_rows(...)` пишет `fill_time = pd.Timestamp(ohlc_times[pos])` на строках 443-455.
- `build_exit_decision_rows(...)` начинает решения с `idx = fill_index` и пишет H1 `decision_time` на строках 708-735.
- PnL buckets по `hold_bars` для `rank05_time_only_linear_target_entry_avoid_sl_top30` воспроизведены из `ML/reports/fractal0_fixed11_rich_entry_locked_test_trades.csv`: `0: n=406, sum=-113.0071, PF=0.0481`; `1: n=85, sum=-10.9074`; `2: n=60, sum=-3.7852`; `3..5: n=121, sum=+4.1459`; `>5: n=524, sum=+518.5808`. Для `hold_bars=0`: `ML_CLOSE=374`, `SL=32`.
- Locked-test interval `2022-12-02 11:00:00` to `2026-06-04 12:00:00` подтверждён в `docs/reports/2026-07-27-fractal0-fixed11-mutual-correlation-pruning.md`, строки 140-141.

## Ошибки мониторинга

- MCP: `knowledge-rag search_similar` по `docs/reports/2026-07-29-fixed11-python-mt4-fill-chronology.md` вернул `no_results`, вероятно документ не проиндексирован.
