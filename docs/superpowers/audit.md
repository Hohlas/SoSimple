# Аудит плана `2026-07-29-fixed11-python-h1-chronology-fix`

Проверялся план `docs/superpowers/plans/2026-07-29-fixed11-python-h1-chronology-fix.md`.
Читал только связанные первоисточники: методики `01`, `03`, `06`, `10`,
`12`, `13`, `16`, `docs/DATA_FLOW.md`, отчёты
`2026-07-29-fixed11-python-mt4-fill-chronology.md` и
`2026-07-29-fixed11-current-history-rerun.md`, текущие runner/test-файлы и
минимальные сведения из JSON/CSV-артефактов. `knowledge-rag` использовался как
поиск кандидатов, `graphify query` - как карта связей; выводы ниже проверены по
файлам.

## Итог

Основная постановка плана подтверждена: текущий Python-код действительно хранит
для limit fill только H1 `fill_time`, а M5 используется только для спорного
порядка SL/TP внутри H1. План правильно ограничивает результат статусом
`DIAGNOSTIC_ONLY` и не предлагает менять rules/cutoffs/models.

Найдены замечания, которые стоит исправить до выполнения плана, чтобы не
получить частичное исправление хронологии.

## 1. Команда запуска тестов содержит неправильное имя теста

- **Важность**: важно
- **Место**: `docs/superpowers/plans/2026-07-29-fixed11-python-h1-chronology-fix.md`, Task 1 Step 2 и Step 4, строки 136 и 224-228
- **Суть проблемы**: план предлагает создать тест
  `test_ml_exit_on_h1_open_is_not_processed_before_m5_fill_in_same_h1`, но в
  команде pytest указан другой тест:
  `test_ml_exit_on_h1_open_is_ignored_when_m5_fill_happens_later_in_same_h1`.
- **Доказательство**:
  - определение теста в плане: строка 136;
  - команда pytest в плане: строки 224-228.
- **Почему это важно**: команда не проверит нужный тест и завершится ошибкой
  "not found" или создаст ложное впечатление, что failure относится к
  симулятору, а не к опечатке в плане.
- **Рекомендуемое исправление**: привести имя в команде к фактическому имени
  теста или переименовать сам тест. Лучше использовать одно имя:
  `test_ml_exit_on_h1_open_is_not_processed_before_m5_fill_in_same_h1`.

## 2. План допускает same-H1 `ML_CLOSE` без реального post-fill ML decision timestamp

- **Важность**: критично
- **Место**: `docs/superpowers/plans/2026-07-29-fixed11-python-h1-chronology-fix.md`, Task 2 Step 8, строки 473-482
- **Суть проблемы**: план сам пишет, что same-H1 `ML_CLOSE` может быть валиден
  только при будущем наличии реального post-fill ML decision timestamp внутри H1
  (строка 482), но предложенный predicate разрешит `ML_CLOSE` на fill-H1, если
  `decision_time == fill_execution_time`. В текущем коде такого реального
  внутрибаравого ML decision timestamp нет: `decision_time` строится как H1 time.
- **Доказательство**:
  - текущий `build_exit_decision_rows(...)` задаёт
    `decision_time = pd.Timestamp(times[idx])` и
    `first_exit_execution_time = pd.Timestamp(times[idx + 1])`:
    `ML/baseline/benchmark_fractal0_entry_exit_grid.py:732-736`;
  - отчёт о проблеме фиксирует, что `decision_time` получает H1 timestamp, а не
    M5 timestamp:
    `docs/reports/2026-07-29-fixed11-python-mt4-fill-chronology.md:136-143`;
  - roadmap формулирует это как ещё нерешённый выбор контракта:
    либо первое `MLClose` не раньше следующего закрытого H1, либо нужен настоящий
    lower-timeframe timestamp:
    `docs/superpowers/roadmap.md:70-78`;
  - методика требует исполнимость после доступности признаков и runtime delay:
    `docs/methodology/03-feature-contract-leakage.md:101`,
    `docs/methodology/12-backtest-costs.md:68-70`.
- **Почему это важно**: можно исправить timestamp fill, но оставить в системе
  неподтверждённый выход `ML_CLOSE` на том же H1-баре. Тогда ключевая причина
  `hold_bars=0`/same-H1 риска будет закрыта не полностью.
- **Рекомендуемое исправление**: в текущем H1 ML-exit контракте явно запретить
  `ML_CLOSE` на H1-баре fill, пока не добавлен и не доказан отдельный
  post-fill ML decision timestamp. Альтернатива: добавить в данные и тесты
  отдельное поле реального времени ML-выхода внутри H1 и использовать его вместо
  H1 `decision_time`.

## 3. Missing M5 fill touch превращается в H1-open fallback и теряет статус неизвестности

- **Важность**: важно
- **Место**: `docs/superpowers/plans/2026-07-29-fixed11-python-h1-chronology-fix.md`, Task 2 Step 3, строки 362-367
- **Суть проблемы**: если H1 говорит, что limit fill был, но M5 окно не
  подтверждает касание, план предлагает заменить `fill_execution_time` на H1
  `fill_time`. Это снова делает сделку существующей с открытия H1 и маскирует
  отсутствие доказанного M5 fill.
- **Доказательство**:
  - fallback в плане: строки 362-367;
  - предыдущий аудит уже находил группу `M5 no hit = 135` для hold0
    `ML_CLOSE` сделок:
    `docs/reports/2026-07-29-fixed11-python-mt4-fill-chronology.md:274-284`;
  - методика по младшему таймфрейму требует учитывать отсутствие младших свечей
    и заранее заданный fallback:
    `docs/methodology/12-backtest-costs.md:92-98`;
  - raw-data методика понижает execution-выводы до `DIAGNOSTIC_ONLY`, если
    source/timezone/price convention младшего таймфрейма не доказаны:
    `docs/methodology/01-raw-data-inventory.md:35-46`.
- **Почему это важно**: после исправления невозможно будет отличить "M5 доказал
  fill на открытии H1" от "M5 не подтвердил fill, но мы молча подставили H1".
  Это ухудшает аудит и может оставить часть невозможных same-H1 выходов.
- **Рекомендуемое исправление**: добавить поля вроде
  `fill_execution_time_source` (`m5_touch`, `h1_fallback`, `missing_m5_touch`)
  и `fill_execution_confirmed`. Для `missing_m5_touch` не разрешать same-H1
  `ML_CLOSE`; для SL/TP применять явно описанный fallback и отражать число таких
  случаев в отчёте.

## 4. Не покрыт случай, когда fill и SL/TP попадают в одну M5-свечу

- **Важность**: важно
- **Место**: `docs/superpowers/plans/2026-07-29-fixed11-python-h1-chronology-fix.md`, Task 1 Mandatory Checks и Task 2 Step 7, строки 76-80 и 421-465
- **Суть проблемы**: план проверяет SL после fill на следующей M5-свече, но не
  проверяет случай, где сама M5-свеча fill одновременно содержит SL или TP. M5
  OHLC в таком случае не доказывает, что было раньше внутри этих пяти минут.
- **Доказательство**:
  - обязательные проверки плана перечисляют fill в `10:10` и SL после fill, но
    не содержат теста на double-touch в самой fill-M5 свече: строки 76-80;
  - предложенный lower bound оставляет M5-свечу с `time >= fill_execution_time`,
    то есть включает саму fill-свечу: строки 440-441;
  - текущий resolver при одновременном `stop_hit` и `tp_hit` возвращает SL с
    `ambiguous=True`, но не знает порядок limit fill относительно SL/TP внутри
    той же M5-свечи:
    `ML/baseline/benchmark_fractal0_entry_exit_grid.py:536-545`;
  - методика требует fallback, если младший таймфрейм тоже ambiguous:
    `docs/methodology/12-backtest-costs.md:92-95`.
- **Почему это важно**: цель плана - восстановить порядок
  `limit fill -> SL/TP/MLClose/timeout`. M5 даёт только порядок между M5-свечами,
  но не внутри одной M5-свечи. Без отдельного правила часть сделок получит
  недоказанный порядок.
- **Рекомендуемое исправление**: добавить синтетический тест на fill-M5 candle
  double-touch и явно выбрать fallback: например `SL first` с `ambiguous=True`,
  либо помечать сделку отдельным reason/flag. В отчёт добавить счётчик таких
  случаев.

## 5. В плане нет обновления machine-readable execution contract в JSON

- **Важность**: важно
- **Место**: `docs/superpowers/plans/2026-07-29-fixed11-python-h1-chronology-fix.md`, Task 3 Step 2 и Task 4, строки 563-581 и 703-745
- **Суть проблемы**: план патчит только top-level `verdict`/`decision`, но не
  требует записать в JSON новый execution contract: как именно используется M5,
  что означает `fill_execution_time`, какой fallback применяется при missing M5
  и как ограничены same-H1 выходы.
- **Доказательство**:
  - текущий grid JSON writer для M5 пишет старый режим
    `execution_ohlc_usage = resolve_same_h1_bar_tp_sl_order_only`:
    `ML/baseline/benchmark_fractal0_entry_exit_grid.py:1467`;
  - fixed11 runner JSON сейчас содержит `execution_contract` только с
    stop/entry/mask/exit/spread, но не содержит `execution_ohlc_usage`:
    `ML/baseline/run_fractal0_fixed11_rich_entry_locked_test.py:304-310`;
  - методика требует paths, hashes, rules и воспроизводимый отчёт:
    `docs/methodology/16-reporting-audit.md:31`,
    а backtest-методика требует зафиксировать price/execution convention:
    `docs/methodology/12-backtest-costs.md:52-58`.
- **Почему это важно**: следующий агент не сможет по structured artifact
  отличить старый fixed11 rerun от исправленного, кроме наличия новой колонки.
  Это повышает риск неверного сравнения и неверной MT4 parity постановки.
- **Рекомендуемое исправление**: изменить runner так, чтобы новый JSON содержал,
  например:
  `execution_ohlc_usage=limit_fill_timestamp_and_same_h1_post_fill_event_order`,
  `fill_execution_time_contract`, `same_h1_ml_close_policy`,
  `missing_m5_fill_policy`, `fill_m5_double_touch_policy` и счётчики по каждой
  категории.

## 6. `_entry_cache_for_spread` и общий grid CLI останутся без M5 fill timestamp

- **Важность**: важно
- **Место**: `docs/superpowers/plans/2026-07-29-fixed11-python-h1-chronology-fix.md`, Task 2 Step 4, строки 369-395
- **Суть проблемы**: план меняет fixed11 wrapper и два rich/current-history
  вызова, но не меняет общий `_entry_cache_for_spread(...)`. При запуске
  `benchmark_fractal0_entry_exit_grid.py` с `--execution-ohlc-path` entry cache
  всё равно будет строиться без M5 fill timestamp.
- **Доказательство**:
  - текущий `_entry_cache_for_spread(...)` вызывает `build_entry_rows(...)` без
    `execution_ohlc`:
    `ML/baseline/benchmark_fractal0_entry_exit_grid.py:955-977`;
  - `run_matrix(...)` загружает `execution_ohlc`:
    `ML/baseline/benchmark_fractal0_entry_exit_grid.py:1312-1316`;
  - затем симуляция получает `execution_ohlc`, но entry rows уже не содержат
    фактического M5 fill timestamp:
    `ML/baseline/benchmark_fractal0_entry_exit_grid.py:1361-1369`;
  - план в self-review заявляет, что code exposes `fill_execution_time` в
    entries/trades и scope включает `ML/baseline/benchmark_fractal0_entry_exit_grid.py`:
    `docs/superpowers/plans/2026-07-29-fixed11-python-h1-chronology-fix.md:828-831`.
- **Почему это важно**: fixed11 path может быть исправлен, но базовый runner,
  который создаёт исходные stop-grid/M5 артефакты, останется с прежним
  неполным контрактом. Это создаст два несовместимых режима с одинаковым
  названием `execution_ohlc_path`.
- **Рекомендуемое исправление**: расширить `_entry_cache_for_spread(...)`
  параметром `execution_ohlc` и передавать его из `run_matrix(...)` для
  canonical и stress cache. Обновить monkeypatch-тест
  `tests/test_fractal0_entry_exit_grid.py:254-264`, чтобы fake function
  принимала новый параметр.

## 7. Selection CSV продолжит писать `KEEP_CANDIDATE`, хотя rerun должен быть diagnostic-only

- **Важность**: улучшение
- **Место**: `docs/superpowers/plans/2026-07-29-fixed11-python-h1-chronology-fix.md`, Task 3 Step 2, строки 563-581
- **Суть проблемы**: план принудительно меняет top-level JSON verdict на
  `DIAGNOSTIC_ONLY`, но не уточняет, что делать с
  `_selection.csv`, где runner продолжает писать `KEEP_CANDIDATE`/`REJECT`.
- **Доказательство**:
  - текущий fixed11 runner создаёт `selection_df["decision"]` как
    `KEEP_CANDIDATE` по PF/BS/N gate:
    `ML/baseline/run_fractal0_fixed11_rich_entry_locked_test.py:256-267`;
  - проверка текущего current-history selection CSV показала первые строки с
    `decision=KEEP_CANDIDATE`;
  - методика требует явно запрещать неверные интерпретации и отделять
    diagnostic PnL/PF:
    `docs/methodology/16-reporting-audit.md:79-86`,
    `docs/methodology/16-reporting-audit.md:90-103`.
- **Почему это важно**: даже при правильном JSON следующий агент может открыть
  `_selection.csv` и ошибочно воспринять `KEEP_CANDIDATE` как новый candidate
  verdict после изменения execution convention.
- **Рекомендуемое исправление**: либо изменить selection CSV для этого output
  prefix на `DIAGNOSTIC_KEEP_GATE_PASSED`/`DIAGNOSTIC_REJECT_GATE_FAILED`, либо
  добавить рядом отдельную колонку `allowed_max_verdict=DIAGNOSTIC_ONLY` и
  явно описать в отчёте, что `KEEP_CANDIDATE` является legacy gate output, а не
  итоговым verdict.

## 8. Отчётный шаблон не содержит обязательного уровня этапа и changed files

- **Важность**: улучшение
- **Место**: `docs/superpowers/plans/2026-07-29-fixed11-python-h1-chronology-fix.md`, Task 4 Step 1, строки 707-738
- **Суть проблемы**: план требует секции `Methodology`, `What Changed`,
  `Commands`, `Artifacts`, но не требует отдельные секции "уровень этапа" и
  "changed files", которые прямо перечислены в методике отчётности.
- **Доказательство**:
  - обязательный шаблон плана: строки 707-738;
  - методика отчётности требует указать уровень этапа и секцию `Changed Files`:
    `docs/methodology/16-reporting-audit.md:18-30`;
  - она также требует отличать поисковый/проверочный уровень:
    `docs/methodology/16-reporting-audit.md:88-92`.
- **Почему это важно**: этот план меняет execution convention после уже
  открытого locked_test. Без явного уровня этапа и списка changed files отчёт
  будет хуже защищать от неверного повышения статуса.
- **Рекомендуемое исправление**: добавить в шаблон секции `## Stage Level` и
  `## Changed Files`, где зафиксировать:
  `diagnostic verification rerun`, `allowed_max_verdict=DIAGNOSTIC_ONLY`,
  список изменённых code/docs/artifact files и запрет трактовать rerun как
  новый locked-test PASS.

