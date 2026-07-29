# Аудит плана fixed11 current-history rerun

Дата аудита: 2026-07-29

Проверен полностью:

- `docs/superpowers/plans/2026-07-29-fixed11-current-history-rerun.md`

Точечно проверены связанные первоисточники:

- `docs/superpowers/README.md`
- `docs/reports/2026-07-29-fixed11-python-mt4-fill-chronology.md`
- `docs/methodology/README.md`
- `docs/methodology/01-raw-data-inventory.md`
- `docs/methodology/10-frozen-test-oos.md`
- `docs/methodology/12-backtest-costs.md`
- `docs/methodology/13-export-mt4-parity.md`
- `docs/methodology/16-reporting-audit.md`
- `ML/baseline/run_fractal0_fixed11_rich_entry_locked_test.py`
- `ML/baseline/benchmark_fractal0_entry_exit_grid.py`
- `ML/reports/fractal0_fixed11_retained_mt4_parity/reconcile_fill_chronology.py`
- `ML/reports/fractal0_fixed11_retained_mt4_parity/fill_chronology_manifest.json`
- `ML/reports/fractal0_fixed11_rich_entry_locked_test.json`
- `DATA/XAUUSD_H1_OHLC.csv`
- `DATA/XAUUSD_H1_OHLC_prev_20260701.csv`
- `DATA/Nero_XAUUSD_test_labeled.csv`
- `MT/MQL4/Files/XAUUSD_H1_OHLC.csv`
- `MT/MQL4/Files/XAUUSD_M5_OHLC.csv`

## Вывод

План правильно держит максимальный статус `DIAGNOSTIC_ONLY`, запрещает новый выбор правил и не предлагает менять Python/MT4 логику внутри H1. Но в текущем виде он не гарантирует выполнение собственной цели: "пересчитать fixed11 locked-test на свежей MT4 history". Runner берёт свежий H1 только как OHLC для исполнения, а строки `locked_test` с признаками, `fractal0`, `ATR` и target-полями остаются из `DATA/Nero_XAUUSD_test_labeled.csv`, который не включён в freeze current-history sources и датирован старым состоянием.

## Замечания

### 1. Критично: план не пересобирает locked-test dataset из текущей H1 history

- Место: `docs/superpowers/plans/2026-07-29-fixed11-current-history-rerun.md`, строки 5-8, 16-23, 185-213, 245-253.
- Суть проблемы: цель и архитектура говорят, что текущие H1/M5 CSV становятся источником данных, но команда rerun не передаёт новый `--locked-test-path` и не пересобирает `DATA/Nero_XAUUSD_test_labeled.csv` из текущей H1 history.
- Доказательство:
  - runner по умолчанию читает `--locked-test-path DATA/Nero_XAUUSD_test_labeled.csv`: `ML/baseline/run_fractal0_fixed11_rich_entry_locked_test.py`, строки 322-328;
  - `load_locked_test_split()` берёт строки, признаки и `time` именно из этого CSV: `ML/baseline/run_fractal0_fixed11_rich_entry_locked_test.py`, строки 22-27;
  - команда плана передаёт только `--execution-ohlc-path` и `--output-prefix`, но не `--locked-test-path`: `docs/superpowers/plans/2026-07-29-fixed11-current-history-rerun.md`, строки 249-253;
  - текущий `DATA/Nero_XAUUSD_test_labeled.csv` имеет hash `5beb70f29ee27caa2b20a8cd80376879b64179d4ef0e5197a29357b58483f535` и mtime `2026-07-02`, тогда как `DATA/XAUUSD_H1_OHLC.csv` обновлён `2026-07-29`;
  - `DATA/Nero_XAUUSD_test_labeled.csv` содержит 9463 строки за `2022-12-02 11:00:00` - `2026-06-04 12:00:00`, а текущий H1 CSV содержит 128698 строк до `2026-07-29 13:00:00`.
- Почему это важно: такой rerun смешивает старые labeled/fractal/features rows со свежим H1 execution OHLC. Он может измерить часть эффекта смены execution OHLC, но не эффект полной смены текущей MT4 history как источника данных. Это особенно важно, потому что fixed11 entry/stop зависит от `fractal0`, `ATR`, `signal_time` и split rows, а они приходят из labeled dataset.
- Рекомендуемое исправление: либо переименовать этап в "current execution OHLC rerun" и явно указать, что labeled locked-test rows остаются старыми, либо добавить предварительный шаг пересборки locked-test labeled CSV из текущего H1 source с новым immutable path, hash, split boundaries и schema audit. В любом случае включить `DATA/Nero_XAUUSD_test_labeled.csv` или новый labeled artifact в Task 1 freeze manifest.

### 2. Критично: проверка `execution_ohlc_usage` в новом JSON невыполнима текущим runner-ом

- Место: `docs/superpowers/plans/2026-07-29-fixed11-current-history-rerun.md`, строки 278-305.
- Суть проблемы: Step 5 требует `assert d["execution_ohlc_usage"] == "resolve_same_h1_bar_tp_sl_order_only"`, но `run_fractal0_fixed11_rich_entry_locked_test.py` не записывает top-level поле `execution_ohlc_usage` в JSON artifact.
- Доказательство:
  - artifact writer runner-а пишет `execution_ohlc_path`, `execution_ohlc_sha256`, `h1_ohlc_path`, `h1_ohlc_sha256`, но не `execution_ohlc_usage`: `ML/baseline/run_fractal0_fixed11_rich_entry_locked_test.py`, строки 285-318;
  - поле `execution_ohlc_usage` записывает другой файл, `benchmark_fractal0_entry_exit_grid.py`, внутри `pnl_convention`: строка 1467;
  - `rg -n "execution_ohlc_usage" ML/baseline/run_fractal0_fixed11_rich_entry_locked_test.py ML/baseline/benchmark_fractal0_entry_exit_grid.py` находит это поле только в `benchmark_fractal0_entry_exit_grid.py`.
- Почему это важно: плановый Step 5 упадёт даже при успешном rerun. Это создаст ложный blocker или подтолкнёт исполнителя к незапланированному изменению runner-а, хотя Global Constraints запрещают чинить runner в этом плане при несовместимой schema.
- Рекомендуемое исправление: заменить проверку на фактическую структуру JSON: проверять `d["execution_ohlc_path"]`, `d["execution_ohlc_sha256"]`, `d["h1_ohlc_path"]`, `d["h1_ohlc_sha256"]`; usage фиксировать в отчёте ссылкой на `ML/baseline/benchmark_fractal0_entry_exit_grid.py:1467` или заранее добавить отдельным plan task изменение JSON writer-а, если это действительно нужно.

### 3. Важно: mandatory check "current M5 vs XAUUSD5.hst" не реализован в manifest

- Место: `docs/superpowers/plans/2026-07-29-fixed11-current-history-rerun.md`, строки 60-67, 123-181.
- Суть проблемы: Task 1 требует проверить, что current M5 vs `XAUUSD5.hst` не имеет material historical mismatch, но `reconcile_fill_chronology.py` не считает M5 CSV vs HST diff и manifest не содержит такого раздела.
- Доказательство:
  - обязательная проверка плана: `Current M5 vs XAUUSD5.hst has no material historical mismatch except incomplete/latest edge rows`, строка 63;
  - `reconcile_fill_chronology.py` фиксирует hash `hst_m5` и `m5_csv` в `artifact_hashes`, но сравнение через `h1_vs_hst_summary()` вызывается только для H1: строки 357-360;
  - текущий manifest содержит `current_data_h1_vs_hst`, `previous_python_h1_vs_hst`, `previous_python_h1_vs_current_data_h1`, `current_data_h1_vs_mt4_exported_h1`, но не содержит `current_m5_vs_hst_m5`.
- Почему это важно: M5 используется для execution ordering. Методика требует для младшего таймфрейма зафиксировать source, timezone, price convention, gaps и соответствие H1 source (`docs/methodology/01-raw-data-inventory.md`, строки 29-46; `docs/methodology/12-backtest-costs.md`, строки 96-101). Без M5-vs-HST проверки нельзя подтвердить одну из обязательных предпосылок плана.
- Рекомендуемое исправление: добавить в `reconcile_fill_chronology.py` отдельную функцию `tf_vs_hst_summary(csv_path, hst_path, tolerance, timeframe)` для M5, записывать `current_m5_vs_hst_m5` в manifest и проверять matched rows, gaps/latest edge rows, yearly/monthly diff counts. Либо убрать mandatory check из плана и явно понизить это до unresolved limitation.

### 4. Важно: план не фиксирует hash source rules и source artifact до rerun

- Место: `docs/superpowers/plans/2026-07-29-fixed11-current-history-rerun.md`, строки 206-213 и 215-228.
- Суть проблемы: mandatory checks говорят, что source rules и source artifact должны остаться unchanged, но Step 1 записывает hash только старых locked-test output artifacts.
- Доказательство:
  - план требует `Source rules and source artifact stay unchanged`, строка 208;
  - Step 1 hash-команда покрывает только `ML/reports/fractal0_fixed11_rich_entry_locked_test.json` и `_trades.csv`, строки 219-222;
  - runner использует `source_rules_csv` и `source_artifact_path`: `ML/baseline/run_fractal0_fixed11_rich_entry_locked_test.py`, строки 121-126; default paths указаны на строках 324-325;
  - методика отчётности требует указать paths, hashes, rules, checkpoints (`docs/methodology/16-reporting-audit.md`, строки 31-32, 96-97).
- Почему это важно: если `leaderboard_closure_audit_rules.csv` или `fractal0_stop_grid_m5.json` поменяются, rerun уже не будет "без изменения rules/cutoffs/entry/exit/stop/spread", но плановая проверка этого не поймает до чтения итогового JSON.
- Рекомендуемое исправление: в Task 2 Step 1 добавить `sha256sum ML/reports/leaderboard_closure_audit_rules.csv ML/reports/fractal0_stop_grid_m5.json DATA/Nero_XAUUSD_test_labeled.csv DATA/XAUUSD_H1_OHLC.csv MT/MQL4/Files/XAUUSD_M5_OHLC.csv`; после rerun сверить эти hashes.

### 5. Важно: report template не соответствует обязательным секциям `docs/methodology/16-reporting-audit.md`

- Место: `docs/superpowers/plans/2026-07-29-fixed11-current-history-rerun.md`, строки 531-595.
- Суть проблемы: шаблон отчёта не содержит обязательные секции `Уровень этапа`, `Multiple Testing Context`, `Changed Files`, `Split Disclosure`, `Related Materials`.
- Доказательство:
  - методика отчётности перечисляет обязательную структуру отчёта: `docs/methodology/16-reporting-audit.md`, строки 18-30;
  - шаблон плана содержит `Context`, `Methodology`, `What Was Done`, `Verification`, `Results`, `Conclusions`, `Limitations`, `Next Step`, но не содержит часть обязательных секций.
- Почему это важно: этап диагностический, но он всё равно показывает PnL/PF и сравнение сделок. Без `Multiple Testing Context` и `Split Disclosure` следующий агент может неверно интерпретировать rerun как новый locked-test или как основание для выбора.
- Рекомендуемое исправление: расширить шаблон отчёта секциями из `16-reporting-audit.md`: `Уровень этапа`, `Multiple Testing Context`, `Changed Files`, `Split Disclosure`, `Related Materials`. В `Multiple Testing Context` явно указать: `new rules/models/profiles/thresholds=0`, `changed_data_source=true`, `allowed_max_verdict=DIAGNOSTIC_ONLY`.

### 6. Важно: план противоречит сам себе по placeholder-фразам

- Место: `docs/superpowers/plans/2026-07-29-fixed11-current-history-rerun.md`, строки 531-595 и 653-661.
- Суть проблемы: Final Self-Review Checklist утверждает, что план не содержит placeholder markers или deferred-content phrases, но шаблон отчёта многократно использует `Указать` и "Вставить".
- Доказательство:
  - строки 545, 555, 564, 568, 572, 580, 584, 592 содержат `Указать` или `Вставить`;
  - строка 661 требует, чтобы план не содержал placeholder markers or deferred-content phrases.
- Почему это важно: для исполнителя неясно, это готовый исполнимый план или черновой шаблон. По методике отчёт должен быть воспроизводимым; placeholders повышают риск ручного переноса чисел без structured verification.
- Рекомендуемое исправление: заменить placeholders на конкретные требования и поля из artifacts, например "Report must include `comparison.aggregate_old.trades`, `comparison.aggregate_current.trades`, ...". Либо убрать пункт 661 из self-review как неприменимый к шаблону.

### 7. Улучшение: comparison artifact не фиксирует hashes входных old/current trades

- Место: `docs/superpowers/plans/2026-07-29-fixed11-current-history-rerun.md`, строки 344-421.
- Суть проблемы: inline comparison script записывает пути old/current trades, но не записывает их `sha256`.
- Доказательство:
  - output JSON полями `old_trades_path` и `current_trades_path` создаётся на строках 405-406;
  - hash входов в `out` не добавляется;
  - `docs/methodology/16-reporting-audit.md`, строки 31-32 и 96-97, требует paths/hashes и сверку ключевых чисел со structured artifact.
- Почему это важно: если один из CSV будет перезаписан, comparison JSON уже нельзя будет надёжно связать с конкретными входами.
- Рекомендуемое исправление: добавить функцию `sha256(path)` в inline script и поля `old_trades_sha256`, `current_trades_sha256`, а также hashes old/current JSON metadata.

### 8. Улучшение: "no code change before rerun" не проверяется командой состояния рабочей копии

- Место: `docs/superpowers/plans/2026-07-29-fixed11-current-history-rerun.md`, строки 206-213 и 245-253.
- Суть проблемы: mandatory check требует `No code change is made before rerun`, но план не содержит команды, которая фиксирует состояние `ML/baseline/run_fractal0_fixed11_rich_entry_locked_test.py`, `ML/baseline/benchmark_fractal0_entry_exit_grid.py` и зависимого `benchmark_fractal0_entry_quality_filter.py`.
- Доказательство:
  - plan check указан строкой 209;
  - в Task 2 есть только `rg` по CLI arguments и hash старых output artifacts, но нет `git diff --name-only` или hash runner files;
  - runner реально зависит от `benchmark_fractal0_entry_quality_filter.py`: import на строках 18-19.
- Почему это важно: rerun должен отделить эффект data source от эффекта логики. Без фиксации code hash нельзя доказать "logic_change = none".
- Рекомендуемое исправление: перед rerun добавить `git diff -- ML/baseline/run_fractal0_fixed11_rich_entry_locked_test.py ML/baseline/benchmark_fractal0_entry_exit_grid.py ML/baseline/benchmark_fractal0_entry_quality_filter.py` и `sha256sum` этих файлов; записать hashes в final report/comparison artifact.

## Подтверждённые утверждения без замечаний

- Текущие H1 sources `DATA/XAUUSD_H1_OHLC.csv` и `MT/MQL4/Files/XAUUSD_H1_OHLC.csv` существуют и имеют одинаковый hash `affd627e55ad777cd763a4f5105420e38cefdf6e4ae94974f14c33509865029f`.
- Старый H1 backup `DATA/XAUUSD_H1_OHLC_prev_20260701.csv` существует и имеет другой hash `4bf7a23ab79f41824713fa881078d06fb84fd7c484b2840c3cdec0bfdfda5aff`.
- `MT/MQL4/Files/XAUUSD_M5_OHLC.csv` существует и имеет hash `85e6bbc49bc7e4049810cfb4a3d603576b9cd7b363c7b2f52bc43b59ef8c9a9b`.
- HST files `XAUUSD60.hst`, `XAUUSD5.hst`, `XAUUSD1.hst` существуют по path из отчёта и плана.
- `fill_chronology_manifest.json` уже содержит `current_data_h1_vs_hst`, `previous_python_h1_vs_hst`, `previous_python_h1_vs_current_data_h1`, `current_data_h1_vs_mt4_exported_h1`.
- `current_data_h1_vs_hst` из manifest подтверждает `matched_rows=128679` и `large_differences_by_year={'2026': 1}`.
- `previous_python_h1_vs_current_data_h1` из manifest подтверждает `diff_rows=13504`.
- Runner поддерживает `--execution-ohlc-path` и `--output-prefix`: `ML/baseline/run_fractal0_fixed11_rich_entry_locked_test.py`, строки 327-328.
- Новые current-history artifacts на момент аудита ещё не существуют: `ML/reports/fractal0_fixed11_rich_entry_locked_test_current_history.json`, `_trades.csv`, `ML/reports/fractal0_fixed11_current_history_comparison.json`, `docs/reports/2026-07-29-fixed11-current-history-rerun.md`.

## Ошибки мониторинга

- MCP: `knowledge-rag search_similar` по `docs/superpowers/plans/2026-07-29-fixed11-current-history-rerun.md` вернул `no_results`, вероятно план не проиндексирован.
