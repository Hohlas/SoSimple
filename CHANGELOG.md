# Changelog SoSimple
Хронология значимых изменений проекта (major milestones).
> **Предупреждение**: Читай только первые 200 строк этого файла.

## [2026-05-05] - Live-safe ML audit and entry_path rebuilds

### Добавлено
- `ML/live_safe_audit.py`, `ML/live_safe_audit_registry.py`,
  `ML/run_live_safe_ml_audit.py`.
- Generated audit evidence в `ML/reports/live_safe_ml_audit/`.
- Повторная legacy export replay проверка: старые prediction/rule входы снова
  дают сигналы для пяти систем.
- Новый профиль признаков `entry_path_v1_live_safe`: старый встроенный
  `entry_path_v1` набор без `ret_dir_atr_lag1`.
- Live-safe checkpoint и prediction/signal артефакты в
  `ML/reports/entry_path_v1_live_safe/`.
- Повторный `entry_path_v1_quantile` retrain поверх нового live-safe baseline:
  `ML/reports/entry_path_v1_quantile_live_safe_baseline/`.
- Восстановлен вспомогательный модуль `ML/entry_path_v1_quantile_ensemble.py`,
  который нужен для n-boost проверки quantile-слоя.
- Новый режим `live_safe_baseline` в
  `ML/run_take_skip_original_contour_feature_matrix.py`: старый take/skip
  single-tensor runner без `predict`, `ret_dir_atr_lag1`, `ret_*`, `fav_*`,
  `adv_*` row-признаков.
- Добавлены follow-up режимы `live_safe_path`, `live_safe_geometry`,
  `live_safe_geometry_path`. `Up/Dn` из `fractal*` считаются допустимыми
  входами, если они пришли из MT `Nero.csv` как накопленное состояние `lib_PIC`;
  Python future-label поля остаются запрещены.

### Результаты аудита
- `quality`, `frequency`, `original_plus_path`, `entry_path_v1`,
  `entry_path_v1_quantile` получили verdict `FAIL`.
- `ret_dir_atr_lag1` доказан как future-derived: это лаг от `ret_6_dir_atr`,
  который строится по будущим барам.
- Legacy export replay помечен `diagnostic_only=true`: он подтверждает старую
  механику выгрузки, но не доказывает пригодность модели для online.

### Результаты retrain
- Validation `ret_pearson_r = 0.2681`.
- Validation winner `A @ 7.5%`: 36 trades, PF 2.8881.
- Frozen test: 37 trades, PF 3.6567.
- Sequential test: 25 trades, PF 2.3419, win rate 68.00%.
- Multi-seed follow-up (`7`, `17`, `42`, `77`, `123`):
  median sequential PF 2.3419, min 1.5171, max 4.5985;
  PF > 2.0 у 3/5 seed, PF <= 1.0 у 0/5 seed.
- `entry_path_v1_quantile` поверх live-safe baseline:
  sequential PF > 2.0 у 4/5 seed, но сделок мало (`0..25`) и один seed дал
  0 sequential trades.
- N-boost candidate `lb_gt_m_q40`: frozen test 35 trades, PF 32.4125,
  sequential 14 trades, PF 48.7214, но gate=`fail` из-за stability:
  `same_winner_ratio=0.60 < 0.80`.
- Первый take/skip live-safe probe (`live_safe_baseline_seq50`, seed 42):
  validation winner не найден, verdict=`reject`; лучший validation PF только
  `1.5178` при `3` сделках и `1` отрицательном годовом срезе.

### Вывод
- Старая прибыльность не сохранилась один в один: сделок и PF стало меньше,
  чем у старого `entry_path_v1` sequential результата.
- Но система не развалилась после удаления опасного признака. Результат живой,
  но переменный: перед MT4 parity нужно заморозить поддерживаемую rule-family
  `A` или расширить exporter для `B` / `B_no_path6`.
- Quantile-слой тоже не развалился после замены старого baseline на live-safe
  baseline, но пока не подтвержден как production-кандидат: прибыльность есть,
  правило выбора нестабильно между seed.
- Старый take/skip baseline после удаления future-derived row-признаков пока
  не воспроизвёл прибыльную область. Это усиливает вывод, что старые
  `quality/frequency` результаты нельзя переносить в online как есть.
- Полный `live_safe_path_seq50` переносится на мощный сервер: это не меняет
  обучение или признаки, только место выполнения ресурсоёмкого расчёта.
- Подробности: [docs/reports/2026-05-05-live-safe-ml-audit.md](docs/reports/2026-05-05-live-safe-ml-audit.md)

## [2026-04-29] - Online inference contract hardening

### Добавлено
- `processing.online_causal_preprocessing` теперь проверяет порядок
  `fractal*` после сортировки и запускает `normalize_rowwise(verbose=False)`
  для runtime-процессов.
- `API.telemetry_signal_watcher` получил online contract guard: legacy
  `original_contour/original_baseline` заблокирован по умолчанию, потому что
  его training/test input включает future-derived row features (`predict`,
  `ret_*`, `fav_*`, `adv_*`).
- `API.api_server` переведён на общий live-safe preprocessing вместо прямого
  вызова `normalize_rowwise()`.
- Добавлены тесты на CSV I/O preprocessing, legacy 18-field фракталы,
  validation сортировки, quiet runtime, watcher guard и REST preprocessing path.

### Вывод
- Старый watcher можно использовать с `--allow-unsafe-future-features` только
  для механической диагностики связи MT4 -> Python -> CSV -> MT4.
- ML-корректный online/test этап требует отдельного live-safe retrain без
  future-derived входных признаков.
- Подробности: [docs/reports/2026-04-29-online-inference-contract-hardening.md](docs/reports/2026-04-29-online-inference-contract-hardening.md)

## [2026-04-28] - MQL runtime architecture snapshot

### Добавлено
- Online diagnostic export теперь может брать направление из `fractal0.direction` для raw `Nero.csv`, где `predict` ещё не может быть рассчитан без будущих данных.

### Изменено
- MT4 expert теперь прогревает `PIC()` по истории через `RECOUNT_HISTORY()` при старте, чтобы восстановить массив сильных уровней до online-работы.
- `POC_SIMPLE()` перенесён внутрь `PIC()`, чтобы исторический прогрев и обычный bar-by-bar проход использовали один расчётный шаг.
- Watcher переведён на runtime snapshot из хвоста `Nero.csv` через `--max-runtime-rows`, чтобы не держать весь многолетний CSV в RAM.
- `ML_TRADE()` в online-режиме ждёт не только изменения `ml_signals.csv`, но и того, что последний `time` внутри файла дошёл до текущего `bar_time`; добавлены диагностические логи `MLP NO_SIGNAL` и `MLP ZERO_SIGNAL`.

### Результаты
- `Nero.csv` локально пересобирается по истории и дописывается при новых уровнях.
- Full-vs-12000 проверка на хвосте дала `signal_mismatch_rows=0`, максимальное отличие `pred_* <= 3.37e-7`.
- Локальный watcher rebuild по raw `Nero.csv` сформировал `runtime_ml_signals.csv`: `11459` строк, `500` ненулевых сигналов, `444` BUY, `56` SELL.
- На локальном M5-наблюдении подтверждены ветки `MLP_WAIT file still behind`, `MLP_WAIT timeout`, `MLP NO_SIGNAL` и `MLP ZERO_SIGNAL`; торговый сигнал пока не менялся.

### Вывод
- Следующий этап - оставить M5-наблюдение на несколько часов, собрать статистику `MLP_WAIT/NO_SIGNAL/ZERO_SIGNAL/BUY/SELL`, затем решить, нужен ли баланс diagnostic-сигналов.
- Подробности: [docs/reports/2026-04-28-mql-runtime-architecture-snapshot.md](docs/reports/2026-04-28-mql-runtime-architecture-snapshot.md)

## [2026-04-27] - Telemetry frequency demo launch

### Добавлено
- High-frequency diagnostic export `telemetry_frequency_v1_highfreq500`.
- Runtime reload `ml_signals.csv` в `lib_ML_Signal.mqh`.
- Multi-position diagnostic режим через существующую `EXPERT::ML_TRADE()`.
- Structured MQL logs `MLP BUY/SELL/CLOSE/SKIP`, включая `source=broker_history` для SL/TP.
- Daily reconciliation CLI `ML/telemetry_daily_reconciliation.py`.
- Наблюдаемый watcher `API.telemetry_signal_watcher` для server-режима через `tmux` с heartbeat в stdout.

### Результаты
- MT4 tester proof на `XAUUSD,H1` за 2025:
  - `495` ожидаемых сигналов;
  - `468` открытых сделок;
  - `27` ожидаемых пропусков по `ML_MaxPositions=10`;
  - `77` broker-side TP, `138` broker-side SL;
  - `critical_mismatch_count=0`;
  - `missing_close_count=1` из-за открытой позиции на конце периода.
- `OnTester returns 15064.255859375`.
- Watcher больше не падает на `header-only` `Nero.csv`: это штатное ожидание первого закрытого бара.

### Вывод
- На дату 2026-04-27 diagnostic-контур считался готовым к online demo launch
  как механическая цепочка; 2026-04-29 этот вывод уточнён: legacy
  `original_baseline` не является ML-корректным online-контрактом.
- Операционный запуск watcher-а переведён из скрытого `nohup`-режима в наблюдаемый `tmux`-режим.
- Результат тестера не является production-доказательством прибыльности: профиль выбран для частоты сделок и проверки pipeline.
- Подробности: [docs/reports/2026-04-27-telemetry-frequency-demo-launch.md](docs/reports/2026-04-27-telemetry-frequency-demo-launch.md)

## [2026-04-24] - System correlation and portfolio check

### Добавлено
- `ML/benchmark_system_correlation.py`
- `tests/test_benchmark_system_correlation.py`
- `docs/ML/benchmark_system_correlation.py.md`
- `ML/reports/system_correlation_portfolio/manifest_xauusd_systems.json`
- benchmark-артефакты в `ML/reports/system_correlation_portfolio/xauusd_system_correlation/`

### Изменено
- `ML/README.md`
- `MODULE_INDEX.md`

### Результаты
- Построен канонический pairwise benchmark по пяти зрелым `XAUUSD` системам:
  - `quality`
  - `frequency`
  - `original_plus_path`
  - `entry_path_v1`
  - `entry_path_v1_quantile`
- Для `entry_path_v1` и `entry_path_v1_quantile` trade-level baseline был честно восстановлен из frozen checkpoints и fixed-hold execution, потому что в baseline-каталоге не было готового `trades.csv`.
- Pairwise split на `XAUUSD`:
  - `portfolio_redundant`: `frequency × original_plus_path`
  - `portfolio_complementary`: `quality × entry_path_v1`, `quality × entry_path_v1_quantile`, `original_plus_path × entry_path_v1`, `original_plus_path × entry_path_v1_quantile`
  - `portfolio_partially_overlapping`: ещё 5 пар
- `entry_path_v1_quantile` подтвердился как другой risk-profile относительно `quality` и `original_plus_path`, но не как независимый слой поверх `entry_path_v1`.

### Вывод
- На `XAUUSD` нельзя считать `frequency` и `original_plus_path` двумя независимыми portfolio sleeves.
- Прагматичный первый portfolio-layer: `quality + entry_path_v1_quantile`; baseline `entry_path_v1` не нужно ставить рядом с quantile-версией как отдельный слой.
- Следующий шаг — уже не поиск новой пары систем, а bounded benchmark composite portfolio без новых trading modes.
- Подробности: [docs/reports/2026-04-24-system-correlation-and-portfolio-check.md](docs/reports/2026-04-24-system-correlation-and-portfolio-check.md)

## [2026-04-24] - Entry path cross-instrument robustness

### Добавлено
- `API/export_entry_path_v1_signals.py`
- `ML/export_entry_path_predictions.py`
- `tests/test_export_entry_path_v1_signals.py`
- `tests/test_export_entry_path_predictions.py`
- `docs/ML/export_entry_path_predictions.py.md`
- stage artifacts в `ML/reports/entry_path_cross_instrument_robustness/`

### Изменено
- `ML/benchmark_execution_policy_v2.py`
- `tests/test_benchmark_execution_policy_v2.py`
- `docs/ML/benchmark_execution_policy_v2.py.md`
- `docs/ML/benchmark_cross_instrument_robustness.py.md`
- `docs/MT/ml_signal_integration.md`
- `ML/README.md`
- `API/README.md`
- `MODULE_INDEX.md`

### Результаты
- Для `entry_path_v1` и `entry_path_v1_quantile` введён единый export-contract `time;signal`.
- `XAUUSD MetaQuotes -> Alpari` проверен отдельно как `provider drift baseline`:
  - `entry_path_v1` -> `provider_stable`
  - `entry_path_v1_quantile` -> `provider_stable`
- `cross-instrument transfer` без retraining и без новых порогов:
  - `entry_path_v1`: `1 supported / 0 inconclusive / 3 failed`
  - `entry_path_v1_quantile`: `2 supported / 0 inconclusive / 2 failed`
- Сильнейший положительный перенос:
  - `XAGUSD` для обеих систем
  - `USDCHF` для `entry_path_v1_quantile`
- Явный провал переноса:
  - `EURUSD` и `GBPUSD` для обеих систем

### Вывод
- Provider drift на том же `XAUUSD` не является основной проблемой для `entry_path` execution-систем.
- Перенос baseline `entry_path_v1` узкий; quantile-версия заметно живучее, но тоже не универсальна.
- Следующий этап должен быть portfolio-level: `System correlation and portfolio check`.
- Подробности: [docs/reports/2026-04-24-entry-path-cross-instrument-robustness.md](docs/reports/2026-04-24-entry-path-cross-instrument-robustness.md)

## [2026-04-24] - Cross-instrument robustness check

### Добавлено
- `ML/benchmark_cross_instrument_robustness.py`
- `tests/test_benchmark_cross_instrument_robustness.py`
- `docs/ML/benchmark_cross_instrument_robustness.py.md`
- manifest/run-helpers в `ML/reports/cross_instrument_robustness/`

### Изменено
- `ML/export_take_skip_v2_predictions.py`
- `ML/README.md`
- `MODULE_INDEX.md`

### Результаты
- Этап разделён на `provider_drift_baseline` и `cross_instrument_transfer`, чтобы не смешивать эффект нового провайдера и эффект нового рынка.
- На `XAUUSD MetaQuotes -> Alpari` все три режима сохранили статус `provider_stable`.
- Полная transfer-матрица по `XAGUSD/EURUSD/GBPUSD/USDCHF` завершена без ретюнинга frozen rules.
- Итог transfer verdicts:
  - `quality`: `1 supported / 1 inconclusive / 2 failed`
  - `frequency`: `2 supported / 1 inconclusive / 1 failed`
  - `original_plus_path`: `2 supported / 0 inconclusive / 2 failed`
- `USDCHF` дал лучший перенос: все три режима получили `transfer_supported`.

### Вывод
- Drift котировок сам по себе не ломает текущие системы на `XAUUSD`.
- Реальный перенос на новые инструменты частичный, а не универсальный: `EURUSD` провалился полностью, `USDCHF` прошёл полностью.
- Следующий этап — не новый transfer, а `System correlation and portfolio check`.
- Подробности: [docs/reports/2026-04-24-cross-instrument-robustness-check.md](docs/reports/2026-04-24-cross-instrument-robustness-check.md)

## [2026-04-22] - Signal export parity benchmark

### Добавлено
- `ML/benchmark_signal_export_parity.py`
- `tests/test_signal_export_parity.py`
- `docs/ML/benchmark_signal_export_parity.py.md`

### Результаты
- Добавлен инструмент, который сравнивает exported `ml_signals.csv` с MT4 tester log.
- Для `original_plus_path_20260420`: `51` ненулевая строка export, `37` уникальных `time+signal`, `29` MT4 opened trades.
- Найдено `14` повторов одного `time+signal`; противоположных сигналов на одном времени нет.
- MT4 diagnostics: `Position blocked=0`, `Score filtered=0`, `Opened=29`, `Trailing closes=29`.

### Вывод
- Дубли времени в DATA являются ожидаемыми разными пиками одного бара и не должны схлопываться.
- Runtime-формат `time;signal` грубее DATA: он исполняет сигнал на уровне времени бара.
- Parity-хвост закрыт; следующий крупный шаг — cross-instrument robustness check.
- Подробности: [docs/reports/2026-04-22-signal-export-parity.md](docs/reports/2026-04-22-signal-export-parity.md)

## [2026-04-20] - take_skip_v2 original contour feature ablation

### Добавлено
- `ML/run_take_skip_original_contour_feature_matrix.py`
- `tests/test_take_skip_original_contour_feature_matrix.py`
- `docs/ML/run_take_skip_original_contour_feature_matrix.py.md`

### Изменено
- `ML/README.md`
- `MODULE_INDEX.md`

### Результаты
- Реализован отдельный runner для проверки `lib_PIC` path/geometry признаков в старом single-tensor `take_skip_v2` контуре.
- Старый baseline не заменяется на `baseline_clean`: новые признаки добавляются поверх исходного engineered-представления.
- Поддержаны режимы `original_baseline`, `original_plus_path`, `original_plus_geometry_path`.
- Runner пишет checkpoint, validation/test prediction CSV, benchmark и summary.
- Зафиксован executable rule `ML/reports/take_skip_trailing_stop_v2_original_plus_path_selected_rule.json`.
- Фокусные тесты: `15 passed`, одно предупреждение PyTorch про nested tensors.
- Полная серверная матрица `3 feature modes × seq_len 20/50/100` завершилась за `2840.42 sec`; все 9 конфигураций получили `go`.
- Контроль подтвердил восстановление старого контура: `input_features=539`, `take_24_x8`, validation `PF=inf`, test `PF=49.58`.
- Лучший practical candidate: `original_plus_path_seq50`, `take_24_x8`, `prob>=0.60`; validation `9.75` trades/year, `PF=16.07`; test `10.2` trades/year, `PF=38.78`, negative years `0`.
- MT4 подтвердил candidate: `TrailATR=8`, `TP=0`, `29` сделок, net `22294.65`, PF `23.79`, relative DD `14.74%`.
- Осторожный MT4-вариант с `TP=12`: net `15873.12`, PF `17.23`, relative DD `6.64%`.

### Вывод
- `path` признаки дают полезный trade-off: больше сделок, PF остаётся высоким.
- `geometry` не выбран как practical candidate: высокий PF, но test частота только `4.8` trades/year.
- `original_plus_path_seq50` становится третьим MT4-подтверждённым кандидатом рядом с `quality` и `frequency`.
- Перед production packaging нужен короткий parity benchmark: exported rows vs unique timestamps vs MT4 opened trades.
- Подробности: [docs/reports/2026-04-20-take-skip-original-contour-feature-ablation.md](docs/reports/2026-04-20-take-skip-original-contour-feature-ablation.md)

## [2026-04-20] - take_skip_v2 lib_PIC feature training

### Добавлено
- `ML/run_take_skip_lib_pic_feature_matrix.py`
- `ML/models/take_skip_dual_stream_transformer.py`
- `tests/test_take_skip_lib_pic_feature_matrix.py`

### Результаты
- Проверен training track, где модель получает фрактальную последовательность и `lib_PIC` feature profile внутри одной dual-stream модели.
- Полная сетка: `baseline_clean`, `baseline_clean_path`, `baseline_clean_geometry_path` × `seq_len 20/50/100`.
- Все 9 конфигураций получили `verdict=reject`.
- В validation grid найдено `79` строк с `PF > 1`, но `0` строк с `PF > 1` и `trades_per_year >= 6`.
- Лучший practical-area результат при `trades_per_year >= 6`: `baseline_clean_seq20`, `take_12_x2`, `top_k=5%`, validation `PF=0.9476`.

### Вывод
- Простое добавление `lib_PIC`-признаков внутрь этой модели не создало рабочий selection layer.
- `lib_PIC`-признаки пока выглядят полезнее как внешний фильтр, чем как добавка во вход dual-stream модели.
- Следующий шаг — controlled ablation: добавить сильные `lib_PIC`-признаки к исходному baseline-контракту и сравнить с воспроизведённым старым baseline.
- Подробности: [docs/reports/2026-04-20-take-skip-lib-pic-feature-training.md](docs/reports/2026-04-20-take-skip-lib-pic-feature-training.md)

## [2026-04-20] - take_skip_v2 lib_PIC external selection benchmark

### Добавлено
- `ML/benchmark_take_skip_lib_pic_selection.py`
- `tests/test_benchmark_take_skip_lib_pic_selection.py`
- `docs/ML/benchmark_take_skip_lib_pic_selection.py.md`

### Результаты
- Проверен внешний слой отбора поверх готовых `take_skip_trailing_stop_v2` exports без нового обучения.
- Quality-first снова выбрал старый rule без `lib_PIC`-фильтра: test `PF=39.74`, `trades_per_year=8.2`, `negative_year_slices=0`.
- Raw frequency-first без фильтра: test `PF=7.18`, `trades_per_year=19.2`, но `negative_year_slices=1`.
- Лучший feature-frequency вариант: `take_24_x8`, `top_k=20%`, exit `x10`, фильтр `pic_path_win_proxy24_share_w20 >= 0.25`; test `PF=5.30`, `trades_per_year=14.8`, `negative_year_slices=0`.

### Вывод
- `lib_PIC`-фильтр не заменяет текущие `quality` / `frequency` правила.
- Признак `pic_path_win_proxy24_share_w20` выглядит полезным как диагностический фильтр устойчивости: он режет часть сделок, но убирает отрицательный годовой срез.
- Следующий шаг — не усложнять внешний слой, а проверить новые `lib_PIC`-производные признаки внутри нового training track.
- Подробности: [docs/reports/2026-04-20-take-skip-lib-pic-selection.md](docs/reports/2026-04-20-take-skip-lib-pic-selection.md)

## [2026-04-19] - Clean lib_PIC feature profile diagnostic

### Результаты
- В `ML/reports/feature_bank_clean_comparison/report.md` зафиксирована read-only диагностика признаков для цели `trail_24_pnl_atr_x8`.
- Лучший диагностический вариант: `baseline_clean` — 117 признаков, validation R² `0.083736`, MAE `0.238819`, совпадение знака `0.842623`.
- Для сравнения, `baseline_full` — 261 признак, validation R² `0.060763`, MAE `0.280381`, совпадение знака `0.836066`.

### Вывод
- Чистка групп `direction`, `price_position`, `path_long`, `path_short` выглядит полезной на диагностике признаков.
- Follow-up `entry_path_v1` training не подтвердил улучшение: `transformer + baseline_clean seq20` дал validation `ret_pearson_r=0.2920` против старого `0.2921`, но test `ret_pearson_r=0.2269` против старого `0.2681`.
- Вывод ограничен модельными метриками; trading verdict для этого профиля не формировался, потому что test-метрики стали хуже baseline.

## [2026-04-19] - Execution policy v2: Python benchmark + MT4 confirmation

### Добавлено
- `ML/benchmark_execution_policy_v2.py`
- `tests/test_benchmark_execution_policy_v2.py`
- `docs/ML/benchmark_execution_policy_v2.py.md`

### Изменено
- `MT/MQL4/Experts/$o$imple.mq4`
- `MT/MQL4/Include/lib_ML_Signal.mqh`

### Результаты
- Добавлен benchmark вариантов выхода для готовых `quality` и `frequency` ML-сигналов без нового обучения.
- В MT4 добавлен `ML_TakeProfitATR`: take profit в ATR от входа, `0=выключен`.
- Для `quality` MT4 подтвердил, что `TrailATR=8, TP=12` снижает зависимость от одной большой сделки: net `18037.59 -> 11544.89`, PF `51.95 -> 33.61`, DD `11.70% -> 4.97%`.
- Для `frequency` MT4 подтвердил, что take profit режет прибыль: `TrailATR=8, TP=12` дал net `12085.05`, PF `2.37` против `TrailATR=8, TP=0` net `24521.88`, PF `3.77`.
- Узкий Python scan показал лучший practical candidate для `frequency`: `TrailATR=8, TP=0`; осторожная альтернатива — `TrailATR=6, TP=0`.

### Вывод
- Для `frequency` take profit временно снимается: основной выход — чистый trailing.
- `TrailATR=10` не выбран основным, потому что даёт больше прибыли ценой худшей формы equity и высокой концентрации прибыли.
- Подробности: [docs/reports/2026-04-19-execution-policy-v2.md](docs/reports/2026-04-19-execution-policy-v2.md)

## [2026-04-18] - MT4 trailing-stop execution for direct ML mode

### Добавлено
- `docs/superpowers/plans/2026-04-18-mt4-trailing-stop-execution.md`

### Изменено
- `MT/MQL4/Experts/$o$imple.mq4`
- `MT/MQL4/Include/lib_ML_Signal.mqh`
- `docs/MT/ml_signal_integration.md`
- `docs/MT/trading_strategy.md`

### Результаты
- В прямой MT4-контур `iSignal=3` добавлен новый режим выхода:
  - `ML_ExitMode=0` -> timeout
  - `ML_ExitMode=1` -> trailing-stop по `ML_TrailATR * ATR`
- Трейлинг реализован отдельно внутри `ML_TRADE()`, без возврата к старому `OUTPUT()/TRAILING_STOP()`
- В логах tester появились явные закрытия `reason=TrailingStop`

### Вывод
- Теперь MT4 может честно проверять не только новый слой входа, но и новый тип выхода, под который строился `take_skip_trailing_stop_v2`
- Следующий шаг — ручной MT4 прогон `quality` и `frequency` уже в trailing-mode
- Подробности: [docs/reports/2026-04-18-mt4-trailing-stop-execution.md](docs/reports/2026-04-18-mt4-trailing-stop-execution.md)

## [2026-04-18] - Take/skip v2 rule consumer

### Добавлено
- `API/export_take_skip_trailing_stop_v2_signals.py`
- `tests/test_export_take_skip_trailing_stop_v2_signals.py`

### Изменено
- `API/README.md`
- `docs/MT/ml_signal_integration.md`
- `MODULE_INDEX.md`

### Результаты
- Добавлен единый CLI для применения frozen `take_skip_trailing_stop_v2` rules к готовому prediction CSV
- Поддержаны оба зафиксированных режима:
  - `quality`: `prob_ge_threshold`
  - `frequency`: `top_k_probability`
- Exporter умеет:
  - писать sparse `time;signal`;
  - разворачивать результат в полный ряд через `--base-csv`;
  - копировать результат сразу в tester/runtime MT4 paths

### Вывод
- `take_skip_trailing_stop_v2_*_selected_rule.json` теперь стали не только отчётными артефактами, но и рабочим интерфейсом применения
- Следующий шаг уже операционный: сравнивать `quality` и `frequency` режимы на одном и том же prediction CSV без ручного разбора rule JSON
- Подробности: [docs/reports/2026-04-18-take-skip-rule-consumer.md](docs/reports/2026-04-18-take-skip-rule-consumer.md)

## [2026-04-18] - Take/skip frequency follow-up

### Добавлено
- `ML/benchmark_take_skip_trailing_stop.py`
- `ML/benchmark_take_skip_trailing_stop_v2_followup.py`
- `tests/test_benchmark_take_skip_trailing_stop_v2_followup.py`

### Изменено
- `processing/label_signals.py`: trailing-stop grid расширен до `x10 / x12`
- `ML/take_skip_trailing_stop_v2_task.py`: `take_skip_v2` contract расширен до `x10 / x12`

### Результаты
- На базе уже обученного `seq50` без нового training-cycle выполнен follow-up benchmark
- quality-first winner сохранился:
  - `take_24_x8 + prob >= 0.70`
  - test `PF=39.74`, `trades_per_year=8.2`
- frequency-first winner найден:
  - `score=take_24_x4`, `exit=x10`, `top_k=20%`
  - validation `PF=3.92`, `trades_per_year=23.75`
  - test `PF=7.18`, `trades_per_year=19.2`
- follow-up refinement дал лучший frequent-кандидат:
  - `anchor_expansion = take_24_x8 + exit x8 + top_k=20%`
  - test `PF=7.17`, `trades_per_year=19.2`, `negative_year_slices=0`
- узкий frozen-sweep `top_k 16%–20%` дал ещё более сильную рабочую точку:
  - `anchor_sweet_spot = take_24_x8 + exit x8 + top_k=17%`
  - test `PF=13.12`, `trades_per_year=16.4`, `negative_year_slices=0`, `max_drawdown_atr=4.03`
- зафиксированы два канонических frozen rule-артефакта:
  - `ML/reports/take_skip_trailing_stop_v2_quality_selected_rule.json`
  - `ML/reports/take_skip_trailing_stop_v2_frequency_selected_rule.json`

### Вывод
- Частоту сделок удалось резко поднять без падения ниже `PF > 1`
- raw `frequency-first` показал полезную область, но не стал финальным winner-ом
- лучшим frequent-режимом оказался anchored-вариант вокруг уже подтверждённого `take_24_x8`
- внутри anchored-зоны лучший practical compromise сейчас даёт `top_k 17%`, а не `20%`
- чистый quality-first winner остаётся базовым эталоном, а anchored sweet spot становится главным frequent-кандидатом
- Подробности: [docs/reports/2026-04-18-take-skip-frequency-followup.md](docs/reports/2026-04-18-take-skip-frequency-followup.md)

## [2026-04-17] - Trailing-stop target quantile first wave

### Добавлено
- `ML/trailing_stop_target_quantile_task.py`
- `ML/models/trailing_stop_target_quantile_transformer.py`
- `ML/benchmark_trailing_stop_target_quantile.py`
- `ML/run_trailing_stop_target_quantile.py`
- tests для quantile task/model/benchmark/runner

### Изменено
- `ML/train.py`, `ML/evaluate_test.py`, `API/generate_signals.py`, `ML/data_loader.py`: task `trailing_stop_target_quantile_v1` протянут через train/evaluate/export stack
- benchmark hardened: fail-fast date validation, full-split `trades_per_year`, обязательный checkpoint copy без stale reuse

### Результаты
- bounded run: `transformer_seq20_x3_quantile`, `trail_48_pnl_atr_x3`, `q10/q50/q90`
- best val `q50_pearson_r=0.0389`, test `q50_pearson_r=0.0541`
- лучший validation candidate: `q10_gt_m`, `PF=0.1750`, `95` trades
- `PF >= 1.0` на validation не найден, verdict: `reject`

### Вывод
- quantile-постановка не улучшила обычную regression-постановку на том же target-е (`0.1750` против `0.4206` best validation PF)
- дальнейшее расширение этой же family на `seq_len=50/100` без новой идеи не выглядит рациональным
- следующий содержательный ход: другая целевая постановка, например бинарное `брать/не брать` или ranking внутри периода
- Подробности: [docs/reports/2026-04-16-trailing-stop-target-quantile-first-wave.md](docs/reports/2026-04-16-trailing-stop-target-quantile-first-wave.md)

## [2026-04-16] - Trailing-stop target first wave verdict

### Добавлено
- `ML/trailing_stop_target_task.py`, `ML/benchmark_trailing_stop_target.py`, `ML/run_trailing_stop_target_matrix.py`
- `tests/test_trailing_stop_target_labels.py`, `tests/test_trailing_stop_target_task.py`, `tests/test_benchmark_trailing_stop_target.py`, `tests/test_run_trailing_stop_target_matrix.py`
- bounded research contour `trailing_stop_target_v1` для матрицы `seq_len = 20 / 50 / 100`

### Изменено
- `processing/label_signals.py`, `processing/label_main.py`: trailing-stop targets теперь корректно рассчитываются для split CSV через OHLC lookup
- `ML/evaluate_test.py`, `API/generate_signals.py`, `ML/train.py`: зафиксирован `seq_len` contract для trailing-stop matrix run

### Результаты
- Первый bounded run нового target-а завершён для `transformer_seq20/50/100`
- Лучший validation candidate всего этапа: `transformer_seq20 + trail_48_pnl_atr_x3`, `PF=0.4206`
- Во всех конфигурациях `validation PF > 1` не найден

### Вывод
- Новый trailing-stop target в текущем виде не вытягивает вход: даже лучший candidate далеко ниже `PF > 1`
- Увеличение длины истории до `50 / 100` не помогло
- Этап дал полезный отрицательный verdict и закрыл два real-world operational defect-а в labeling и export/evaluate wiring
- Подробности: [docs/reports/2026-04-16-trailing-stop-target-first-wave.md](docs/reports/2026-04-16-trailing-stop-target-first-wave.md)

## [2026-04-15] - Track A max-out verdict

### Добавлено
- `ML/entry_path_feature_bank.py`, `ML/models/entry_path_dual_stream_transformer.py`, `ML/run_track_a_max_out_matrix.py`
- bounded research contour для short/deep matrix по `entry_path_v1`

### Результаты
- Short sweep `6 configs x 3 epochs` и deeper rerun лучших `transformer_seq20/seq50` (`10 epochs`) завершены
- Лучший validation candidate всего этапа: `transformer_seq50 + ret24_over_adv24`, `PF=0.4784297662870411`
- Во всех конфигурациях `validation_rows_pf_gt_1 = 0`

### Вывод
- Track A заметно улучшен, но не достиг даже мягкого success gate `PF > 1` на validation
- Следующий шаг должен менять само обучение или постановку задачи, а не повторять ещё один похожий benchmark-only цикл
- Подробности: [docs/reports/2026-04-15-track-a-max-out.md](docs/reports/2026-04-15-track-a-max-out.md)

## [2026-04-13] - Quantile forward validation scaffold

### Добавлено
- `ML/benchmark_quantile_forward_validation.py`: frozen forward benchmark для текущего `entry_path_v1_quantile` rule без перенастройки
- `tests/test_benchmark_quantile_forward_validation.py`: проверки метрик, verdict, квартальных срезов, CLI и ошибочного ввода
- `ML/reports/quantile_forward_validation/`: артефакты текущего состояния forward validation

### Результаты
- Инструмент готов: CLI пишет `summary.json`, `time_slices.csv`, `run_metadata.json`
- Нового strictly-forward prediction CSV в репозитории нет; доступны только historical validation/test prediction-файлы
- Operational verdict текущего этапа: `watch`, reason: `no_forward_data`

### Вывод
- `quantile` не подтверждён и не опровергнут на новых данных: нужна новая forward-выборка после production decision
- Старый frozen test не использован повторно, чтобы не подменять forward validation уже известным окном

## [2026-04-13] - PF uplift discovery beyond ML layer: SHORTLISTED (3)

### Результаты
- Baseline: `entry_path_v1_quantile` test set N=48, PF=8.179, WR=81.25%, negative_year_slices=0
- 20 гипотез по 5 категориям проверены, 6 cheap read-only probes на `trade_enriched.csv`, path-dep check через OHLC simulation
- Shortlisted (3 STRONG):
  - NY session exclusion: PF=20.276, N=34, pf_delta=+12.097 — все Asia-сделки выигрышные (19/19), failure-архетип в NY даёт PF=0.28
  - Early timeout hold_bars=12: PF=13.731, N=48, pf_delta=+5.552 — 0 из 37 wins-at-bar-12 перевернулись к bar-24
  - pred_adv12 ≤ Q75 cap: PF=12.746, N=37, pf_delta=+4.567 — MAE 4x выше для отброшенных сделок (0.35 vs 1.38 ATR)

### Вывод
Три ортогональных механизма (session / hold duration / predicted adverse) дают значимый PF uplift без переобучения. Skeleton plans созданы. Следующий шаг: `/writing-plans` для любой из трёх. Подробности: [docs/reports/2026-04-13-pf-uplift-discovery.md](docs/reports/2026-04-13-pf-uplift-discovery.md)

## [2026-04-13] - Composition track verdict (quantile × fav_3_vs_12)

### Результаты
- `quantile_only` воспроизведён exactly: validation `N=32, PF=11.240091883688192`; test `N=48, PF=8.178675196069868`
- после пересборки правильного источника `pred_fav_3/pred_fav_12` на тех же активных строках composition стал честно измерим: test `N=47`, `PF=7.860844837655267`, `n_boost_composition.verdict = gate_fail`
- composition почти не режет quantile (`47/48` test trades survived), но получает один отрицательный годовой срез в 2023 (`PF=0.47526255177309695`)

### Вывод
- Направление composition закрыто: дополнительный фильтр почти ничего не добавляет к `quantile`, но ломает yearly stability, поэтому усложнение не оправдано

## [2026-04-13] - Fav 3 vs 12 standalone verdict

### Результаты
- самостоятельная проверка `fav_3_vs_12 <= threshold` на active universe не нашла ни одного рабочего порога: на validation лучший порог с `N>=30` дал только `PF=0.1378609915504136` (`threshold=0.22`, `N=36`)
- на test лучшая диагностическая точка с `N>=30` тоже слабая: `PF=0.3129480021818097` (`threshold=0.24`, `N=164`)
- итог benchmark: `selected_threshold = null`, `verdict = reject_as_standalone`

### Вывод
- Направление `fav_3_vs_12` как самостоятельной второй торговой системы закрыто: без `quantile` и без другого базового отбора признак не даёт рабочего standalone-режима

## [2026-04-13] — Label convention audit: timeout больше не штрафуется как SL в TB analytics

### Исправлено
- `ML/tb_signal_logic.py`: `loss_mask = ~win_mask` считал timeout (`0.5`) как loss и завышал `losses`, `loss`, `PF`. Теперь loss считается только по `outcomes == 0.0`, добавлен assert на полное разбиение `TP/SL/Timeout`
- `ML/threshold_analysis.py`: `losses = n_trades - wins` сливал `SL` и `Timeout`; теперь `losses` считаются только по `true == 0.0`
- Восстановлен missing baseline module `ML/benchmark_triple_barrier_mt4_execution.py`, чтобы TB regression suite снова проходил collection

### Добавлено
- `ML/reports/label_convention_audit_inventory.csv`: inventory всех релевантных TB label handling patterns с risk-категориями `R1..R8`
- `ML/reports/label_convention_audit.md`: полный audit report
- `tests/test_tb_label_invariants.py`: permanent guards против смешения timeout и loss в TB analytics

### Вывод
Аудит подтвердил ещё два реальных `R2 not_win_is_loss` бага после уже известного фикса MT4 simulator. Source-of-truth в `processing/label_signals.py` не менялся, frozen `tb_selected_rule.json` не ретюнился. Подробности: [docs/reports/2026-04-13-label-convention-audit.md](docs/reports/2026-04-13-label-convention-audit.md)
Дополнительный frozen rerun на canonical `ml_signals_tb.csv` + `Nero_{validation,test}_labeled.csv` подтвердил, что historical verdict от `2026-04-12` не меняется: validation/test summary совпали exactly.

## [2026-04-12] — Triple Barrier verdict: не production (gate_fail)

### Исправлено
- `ML/triple_barrier_mt4_execution.py`: симулятор кастовал outcome через `int(...)` и терял дискриминацию между SL (`0.0`) и Timeout (`0.5`) в float-конвенции labels из `processing/label_signals.py:919`. Обе ветки падали в `else` (HoldOverTime, pnl_atr=+0.5), из-за чего все прогоны давали `losses=0, pf=inf`. Заменено на `_classify_tb_outcome` с порогами `>=0.75` → TP, `<=0.25` → SL, else → Timeout; фикс применён в обеих точках закрытия позиции (регулярная и финальная)
- `tests/test_triple_barrier_mt4_execution.py`: тесты использовали старую `{1, -1, 0}` int-схему и проходили ложно; переведены на float `{1.0, 0.0, 0.5}`. 6/6 зелёные

### Результаты
После фикса прогон на `tb_selected_rule.json` (`theta=0.475`, `min_ev=0.1`):
- **Validation (2019–2022)**: 28 trades, PF=4.33, win_rate=57.1%, все годы положительные
- **Test (2023–2026)**: 69 trades, PF=1.28, win_rate=42.0%, годовые срезы 2023 (PF=0.55, N=6) и 2026 (PF=0.00, N=8) отрицательные

Gate-проверка (унифицированно с quantile: N≥30, PF>2.0, `negative_year_slices=0`):
- N_trades: ✅ (69)
- PF: ❌ (1.28 < 2.0)
- negative_year_slices: ❌ (2023, 2026)

### Вывод
TB-слой **не** подключается к MT4 как production или parallel execution mode — gate_fail на test, явный regime shift между validation и test. Production-опора остаётся `regression_updn` baseline + `entry_path_v1_quantile` parallel. `tb_selected_rule.json` зафиксирован как frozen исторический артефакт; пересмотр возможен только после накопления forward-данных post-2026-06. Подробности: [docs/reports/2026-04-12-tb-verdict.md](docs/reports/2026-04-12-tb-verdict.md)

## [2026-04-12] — Entry Path v1 Quantile: production-ready через n-boost gate

### Добавлено
- `ML/entry_path_v1_quantile_ensemble.py`: `load_seed_predictions`, `aggregate_mean_quantile`, `majority_vote` для multi-seed агрегации
- `ML/benchmark_entry_path_v1_quantile_n_boost.py`: full n-boost orchestration (relax quantile sweep + ensemble benchmark + strict go/no-go gate)
- `ML/export_entry_path_v1_quantile_rule.py`: production rule export через median m/w/correction по 5 сидам
- `ML/reports/entry_path_v1_quantile_selected_rule.json`: production rule с winner `lb_gt_m_q35`
- `ML/reports/n_boost_result.json`, `n_boost_validation_sweep.csv`: артефакты gate
- tests: `test_entry_path_v1_quantile_ensemble.py` (3), `test_entry_path_v1_quantile_n_boost.py` (8), `test_export_entry_path_v1_quantile_rule.py` (2); +1 тест в `test_export_entry_path_v1_quantile_signals.py`

### Изменено
- `ML/benchmark_entry_path_v1_quantile_filter.py`: добавлен `compute_m_at_quantile(frame, quantile)` для sweep
- `API/export_entry_path_v1_quantile_signals.py`: новый `--rule-path` режим с production rule; baseline_score теперь берётся из baseline-модели через inner join, а не из quantile frame; дедупликация по `time` с приоритетом non-zero signal
- `docs/MT/ml_signal_integration.md`, `docs/MT/trading_strategy.md`: актуализированы под production rule, seed_007, `ML_UseScoreFilter=false` и expected 22 trades

### Исправлено
- `pick_winner` не уважал `GATE_MIN_TRADES` — pool предфильтруется по `trades ≥ 30` до сортировки по PF
- Strict `same_winner_ratio` ловил FP-шум в квантильной полосе — stability tolerance ±0.05 для quantile при сохранении требования same rule
- Экспортёр терял 2 сделки на mixed-signal bars (`2023.11.22`, `2025.03.10`) из-за `drop_duplicates(keep='last')` до применения правила

### Результаты
- Gate PASS на frozen test (seed 007, production параметры median):
  - `n_trades=48`, `pf=8.18`, `win_rate=0.8125`
  - `negative_year_slices=0`, `same_winner_ratio=1.0`
  - sequential (hold_bars=24): 22 trades, PF=3.64, win_rate=0.73
- MT4 parity (tester лог `20260412.log`, period 2023.01.03 — 2025.11.03):
  - **20/20 сделок совпадают** по (time, signal, direction)
  - win rate 80.00% exact match, направление pnl совпадает у всех сделок
  - mean pnl_atr: Python 2.37 vs MT4 2.55 (~8% diff из-за ATR/spread/exit timing)
  - MT4 money metrics: net=4477.25, PF=11.91, DD=4.01%
  - Пропущено 2 сигнала (2022.10.13, 2022.11.22) — усечение периода тестера, не логическое расхождение

### Вывод
`entry_path_v1_quantile` подтверждён как **production-ready parallel execution mode** для MT4. Winner `lb_gt_m_q35` стабилен по 5 сидам (все выбирают `lb_gt_m` с q∈{30,35,40}). Production rule зафиксирован в `entry_path_v1_quantile_selected_rule.json` через median параметры. Старый plan `2026-04-11-entry-path-v1-quantile-production-path.md` superseded. Подробности: [docs/reports/2026-04-12-quantile-status-decision.md](docs/reports/2026-04-12-quantile-status-decision.md)

## [2026-04-11] — Entry Path v1 Quantile: MT4 parity подтверждён

### Добавлено
- `API/export_entry_path_v1_quantile_signals.py`: канонический exporter frozen quantile winner `lb_gt_m` в `time;signal` для MT4
- `tests/test_export_entry_path_v1_quantile_signals.py`
- `tests/test_signal_tracer_mlp.py`
- `ML/reports/entry_path_v1_quantile_mt4_reconciliation.csv`: trade-level сверка direct `MLP`-прогона

### Изменено
- `statistics/signal_tracer.py`: добавлена поддержка direct `MLP CLOSE BUY/SELL` логов и отдельный `mlp` dossier path
- `docs/MT/trading_strategy.md` и `docs/MT/ml_signal_integration.md`: синхронизированы с реальной логикой `ML_TRADE()` и новым quantile export path
- `MT/tester/$o$imple.ini`: quantile parity зафиксирован на `ML_HoldBars=24`, `ML_AllowReversal=0`, `ML_UseScoreFilter=0`

### Исправлено
- `API/export_entry_path_v1_quantile_signals.py`: дубликаты `time` теперь схлопываются как в MT4 (`keep='last'`), поэтому Python export и MQL execution больше не расходятся по числу сигналов

### Результаты
- после исправления exporter-а канонический `ml_signals.csv` для quantile-layer содержит `8872` строк и `8` активных сигналов (`4 BUY`, `4 SELL`)
- MT4 tester по `20260411.log` показал:
  - `8` сделок
  - `PF=58.88`
  - `net=2951.63`
  - `DD=2.85%`
  - `7W / 1L`
- log counters и reconciliation полностью согласованы:
  - `Opened=8`
  - `Timeout closes=8`
  - `Position blocked=0`
  - `Score filtered=0`

### Вывод
`entry_path_v1_quantile` теперь подтверждён и по multi-seed robustness, и в реальном MT4-контуре. Следующий практический вопрос уже не в новом поиске, а в решении, становится ли quantile-layer основным execution mode. Синтез: [wiki/research/execution-tracks.md](wiki/research/execution-tracks.md)

## [2026-04-11] — Entry Path v1 Quantile: multi-seed robustness pass подтверждён

### Добавлено
- `ML/entry_path_v1_quantile_robustness.py` и `ML/benchmark_entry_path_v1_quantile_robustness.py`: repeatable multi-seed robustness-оценка для `entry_path_v1_quantile`
- seed-scoped artifact layout для `entry_path_v1_quantile_robustness/seed_{007,017,042,077,123}`
- `ML/triple_barrier_mt4_execution.py` и `ML/benchmark_triple_barrier_mt4_execution.py`: Python-контур для будущей MT4-matched оценки Triple Barrier

### Изменено
- `ML/train.py`: добавлены `--checkpoint-dir` и `--result-dir` для изоляции run-артефактов
- `ML/evaluate_test.py`: добавлен `--output-dir`
- `ML/export_entry_path_v1_quantile_predictions.py`: экспорт больше не строит лишние split/loaders для незапрошенных наборов
- yearly/rolling robustness summary теперь считаются по winner-selected сделкам, а не по всей active universe

### Результаты
- Полный 5-seed pass (`7, 17, 42, 77, 123`) дал:
  - `same_rule_count = 5`
  - `median_test_pf = inf`
  - `median_sequential_pf = inf`
  - `worst_seed_test_trades = 20`
  - `negative_year_slices = 0`
  - final verdict: `go_mt4`
- Во всех пяти seed validation winner совпал: `lb_gt_m`
- `seed_123` подтвердил, что линия держится и без `PF=inf`: frozen test `26 trades`, `PF=25.17`

### Вывод
`entry_path_v1_quantile` вышел из статуса single-run гипотезы и прошёл multi-seed robustness-pass. Следующий главный шаг теперь не новый поиск, а `MT4 parity-check` для quantile-layer. Синтез: [wiki/research/execution-tracks.md](wiki/research/execution-tracks.md)
## [2026-04-10] — Entry Path v1 Quantile: гибридный трек прошёл success gate

### Добавлено
- Новый task `entry_path_v1_quantile`: сохранены головы `entry_path_v1`, добавлены quantile-головы `ret_24_q10/q90`
- `ML/export_entry_path_v1_quantile_predictions.py`: отдельный экспорт `train/validation/test` для нового трека
- `ML/benchmark_entry_path_v1_quantile_filter.py`: quantile-layer поверх frozen базы `A @ 7.5%`

### Изменено
- `ML/evaluate_test.py`: добавлена CLI-поддержка `--task entry_path_v1_quantile`
- Усилен quantile benchmark:
  - finite-sample conformal correction
  - frozen test check только для validation winner
  - sequential check с `hold_bars` из frozen baseline
- Quantile report summary переведён на active-only строки и теперь явно показывает `crossed_quantile_rows`

### Результаты
- Validation (`entry_path_v1_quantile`): `ret_pearson_r=0.1981`, `interval_coverage=0.8013`, `median_interval_width=7.1442`
- Test: `ret_pearson_r=0.1455`, `interval_coverage=0.7562`, `median_interval_width=7.0826`
- Quantile filter winner: `lb_gt_m`
  - validation: `25 trades`, `PF=11.0465`
  - frozen test: `24 trades`, `PF=inf`
  - sequential: `11 trades`, `PF=inf`

### Вывод
`entry_path_v1_quantile` в текущем run проходит success gate и даёт рабочий confidence-layer поверх `A @ 7.5%`. Подробности: [docs/reports/2026-04-10-entry-path-v1-quantile.md](docs/reports/2026-04-10-entry-path-v1-quantile.md)

## [2026-04-09] — MT4-сверка: замороженный победитель подтверждён одним финальным прогоном

### Изменено
- `MT/MQL4/Include/MAIN.mqh`: прямой режим `iSignal=3` теперь определяется только после `EXPERT_SET()`, чтобы тестер не сваливался в старый путь из-за раннего чтения параметров
- `docs/MT/trading_strategy.md`: инструкция по финальной сверке и псевдокод `MAIN()` приведены в соответствие с реальным порядком вызовов

### Исправлено
- `MT/MQL4/Include/lib_ML_Signal.mqh`: возвращена `ML_DIAG_PRINT()`, которую вызывает `OnTester()`
- `MT/MQL4/Include/lib_ML_Signal.mqh`: BUY back-stop больше не может уходить в отрицательную цену и давать `OrderSend error 4107`

### Результаты
- Финальный MT4-прогон по уже отфильтрованному `ml_signals.csv` дал:
  - `8872` строк в CSV, `22` активных сигнала
  - `22` сделки, `PF=8.47`, `net=+3077.05`, `DD=5.12%`
  - `TB` в этом прогоне не участвовал, `Position blocked=0`, `Timeout closes=22`

### Вывод
Финальный победитель подтверждён в MT4 по одному честному прогону на `test`. Теперь главный технический долг не в новом выборе победителя, а в переносе скрипта выпуска CSV и слоя отбора из черновой ветки в основной контур. Подробности: [docs/reports/2026-04-09-mt4-parity-check-winner.md](docs/reports/2026-04-09-mt4-parity-check-winner.md)

## [2026-04-09] — Entry Path v1: добавлен слой отбора сделок и выбран рабочий базовый вариант

### Добавлено
- `ML/entry_path_trade_filter.py`: простой фильтр `A`, составной фильтр `B`, проверка по периодам и последовательная проверка
- `ML/benchmark_entry_path_trade_filter.py`: подбор порога только на validation и замороженная проверка на test
- `tests/test_entry_path_trade_filter.py`

### Изменено
- `ML/models/entry_path_transformer.py`: для `path_cls` добавлен отдельный путь по последовательности, чтобы эта голова смотрела не только на общий итоговый вектор
- `ML/entry_path_task.py` и `ML/train.py`: уточнены active-only метрики для `path_6_class`
- скрипт проверки теперь защищён от слишком маленького и неустойчивого хвоста: победитель выбирается только среди более рабочих режимов, если такие есть

### Результаты
- После доработки модели:
  - validation: `ret_pearson_r=0.2758`, `path_reg_pearson_r=0.2987`, `path_cls_f1_macro=0.4074`
  - test: `ret_pearson_r=0.2507`, `path_reg_pearson_r=0.2667`, `path_cls_f1_macro=0.4013`
- Составной фильтр `B` перестал быть почти точной копией `A`: на validation в зоне `7.5%–12.5%` наборы сделок уже расходятся
- Финальный рабочий winner после защитного правила:
  - validation: `A @ 7.5%`, `36` сделок, `PF=2.67`, `stability_ratio=1.00`
  - test: `44` сделки, `PF=4.29`
  - последовательная проверка: `30` сделок, `PF=2.87`

### Вывод
Слой `торговать / не торговать` для `entry_path_v1` теперь есть и уже даёт рабочий базовый вариант. Текущий лучший практический вариант — простой фильтр `A` в зоне `7.5%`. Следующий шаг — строить conformal-слой поверх этого базового варианта, а `B` пока держать как вторую исследовательскую ветку. Подробности: [docs/reports/2026-04-09-entry-path-trade-filter.md](docs/reports/2026-04-09-entry-path-trade-filter.md)

## [2026-04-09] — Entry Path v1: проверено перевзвешивание функции потерь, выбран рабочий базовый вариант

### Изменено
- `ML/data_loader.py`: `entry_path_v1` dataset и test-loader теперь передают `signal`, чтобы цикл обучения видел активные BUY/SELL строки
- `ML.train`: для `entry_path_v1` добавлена перевзвешенная функция потерь по активным строкам
- `ML.evaluate_test` и `ML.entry_path_task`: test-report теперь явно показывает `Checkpoint epoch` и лучший `val`-результат, по которому собран отчёт

### Результаты
- Проверены три режима:
  - только активные строки: провал (`test ret_pearson_r=0.0112`)
  - вес `5.0` только для `path_6_class`: частичное улучшение, но не лучший итог
  - вес `5.0` для `ret_*` и `path_6_class`: лучший общий результат
- Выбранный базовый вариант теперь такой:
  - validation: `ret_pearson_r=0.2736`, `path_reg_pearson_r=0.3006`, `path_cls_f1_macro=0.4059`
  - test: `ret_pearson_r=0.2494`, `path_reg_pearson_r=0.2722`, `path_cls_f1_macro=0.4160`
  - test в срезе только по активным сделкам: `ret_pearson_r=0.2285`

### Вывод
Лучший рабочий вариант для `entry_path_v1` сейчас — перевзвешивание активных строк с весом `5.0` сразу в `ret_*` и `path_6_class`. Следующий шаг уже не в новом подборе весов, а в слое `торговать / не торговать` поверх этого базового варианта. Подробности: [docs/reports/2026-04-09-entry-path-v1-loss-weighting.md](docs/reports/2026-04-09-entry-path-v1-loss-weighting.md)

## [2026-04-08] — Entry Path v1: baseline очищен от старого кэша, результаты пересчитаны

### Добавлено
- Новый трек `entry_path_v1`: новая разметка `ret_*`, `fav/adv`, `path_6_class`, новый dataset contract, multitask transformer, test-отчёт и research-only exports
- Новый набор тестов: `tests/test_entry_path_labels.py`, `tests/test_entry_path_task.py`, `tests/test_entry_path_model.py`, `tests/test_entry_path_reports.py`, `tests/test_entry_path_training.py`
- Baseline artifacts: `transformer_entry_path_v1_best.pt`, `transformer_entry_path_v1_result.json`, `evaluate_test_entry_path_v1.md`, `entry_path_v1_validation_predictions.csv`, `entry_path_v1_test_predictions.csv`

### Исправлено
- `ML.train`: флаг `--clear_cache` теперь действительно доходит до `train_model()`
- После этого train/validation cache для `entry_path_v1` был честно пересобран; старые ложные цели у строк `signal=0` исчезли

### Результаты
- Старые числа `best_ret_pearson_r=0.5253` и `test ret_pearson_r=-0.0216` оказались неактуальны: они были получены на старом cache
- После чистого retrain новый baseline стал таким:
  - validation: `ret_pearson_r=0.2656`, `path_reg_pearson_r=0.3004`, `path_cls_f1_macro=0.3261`
  - test: `ret_pearson_r=0.2450`, `path_reg_pearson_r=0.2745`, `path_cls_f1_macro=0.3259`
- Active-only test по реальным BUY/SELL строкам тоже живой:
  - `active ret_pearson_r=0.2039`
  - top 10% по `pred_ret_24_dir_atr` дают `mean true_ret_24 = 0.2442`
  - bottom 10% дают `mean true_ret_24 = -2.2741`
- `path_6_class` остаётся слабым: на активных строках модель почти всегда предсказывает класс `0`

### Вывод
Теперь baseline выглядит честно: `ret_*` не сломан, а просто заметно слабее старого ложного результата. `entry_path_v1` можно сохранять как рабочий исследовательский трек. Следующий шаг уже уже не в поиске “почему test упал”, а в том, как учить этот трек на реальных сделках при том, что активных строк всего около `5%`. Подробный отчёт: [docs/reports/2026-04-08-entry-path-v1-baseline.md](docs/reports/2026-04-08-entry-path-v1-baseline.md)

## [2026-04-08] — Outcome-aligned retraining: validation-first verdict = no winner

### Добавлено
- Новый validation benchmark `ML/benchmark_outcome_targets.py` для трёх outcome-aligned family с общим trade-floor и yearly-stability filter
- Outcome task tests: `tests/test_trade_target_labels.py`, `tests/test_outcome_tasks.py`, `tests/test_benchmark_outcome_targets.py`
- Канонический отчёт этапа: [docs/reports/2026-04-08-outcome-aligned-retraining.md](docs/reports/2026-04-08-outcome-aligned-retraining.md)

### Изменено
- `processing/label_signals.py` и `processing/label_main.py`: добавлены `trade_outcome_h12`, `trade_pnl_h12_atr`, `archetype_target`
- `ML/data_loader.py`, `ML/train.py`, `ML/evaluate_test.py`, `ML/utils.py`: outcome-aligned задачи встроены в training/evaluation stack
- Outcome-task loaders переведены на `signal != 0` rows с отдельным signal-only кэшем после отладки objective mismatch
- `ML/benchmark_outcome_targets.py` теперь умеет корректно фиксировать семьи без viable slice и сценарий “winner отсутствует”

### Результаты
- После signal-only retraining на `2208` train / `473` validation signal rows:
  - `trade_outcome_cls`: best val `AUC=0.6534`
  - `trade_pnl_reg`: best val `pearson_r=0.1099`
  - `signal_archetype_cls`: best val `AUC=0.6260`
- Validation benchmark по единым правилам отбора не дал winner-а:
  - `trade_outcome_cls`: best rejected slice `PF=0.1983`, `N=24`
  - `trade_pnl_reg`: best rejected slice `PF=0.1105`, `N=24`
  - `signal_archetype_cls`: best rejected slice `PF=0.1369`, `N=48`
- Ни одно семейство не прошло shared `min_trades=80` и `stability_ratio>=0.75`
- `frozen_outcome_target.json` не создан; финальный запуск на `test` не выполнялся

### Вывод
Validation-first protocol отработал правильно: outcome-aligned track в текущем виде не дал ни одного target family, который можно честно переносить на `test`. Это не “лучший из плохих”, а явный сигнал пересмотреть саму label definition ближе к реальному execution loop MT4. Подробности: [docs/reports/2026-04-08-outcome-aligned-retraining.md](docs/reports/2026-04-08-outcome-aligned-retraining.md)

## [2026-04-08] — Triple Barrier: найдена причина старого расхождения Python ↔ MT4

### Исправлено
- `processing/label_signals.py`: TB-разметка теперь считает исход от времени строки сигнала, а не от `fractal0.time`
- `statistics/signal_tracer.py`: исправлены разбор 22-польного `fractal0`, расчёт времени в UTC и TB-сверка сделка за сделкой
- `MT/MQL4/Include/OUTPUT.mqh`: в лог добавлены понятные причины рыночного закрытия TB-сделок

### Результаты
- Старый отрицательный вывод по MT4 оказался ложным: главная причина была в сдвиге времени в TB-разметке
- После полной пересборки зафиксированное правило стало таким: `theta=0.475`, `min_ev=0.10`, validation `PF=1.53`, test `PF=1.11`
- Новый MT4-прогон по свежему `ml_signals_tb.csv` дал `PF=1.27`, `net=2932.44`, `N=92`
- В новой сверке уровни SL/TP почти совпали с Python, а жёсткие исходы `TP/SL` совпали в `61 из 65` случаев
- Основная оставшаяся разница теперь связана не с ошибкой разметки, а с правилами торговли в MT4: `PosBlock=113`, `HoldOverTime=22`, `TB_Reversal=4`

### Вывод
Triple Barrier больше нельзя считать треком, который “ломается” при переносе в MT4. Главная старая ошибка найдена и исправлена. Теперь следующий шаг не в новых порогах, а в оценке вне MT4, которая повторяет правила торговли MT4 один в один. Подробный отчёт: [docs/reports/2026-04-08-triple-barrier-runtime-verdict.md](docs/reports/2026-04-08-triple-barrier-runtime-verdict.md)

## [2026-04-08] — Triple Barrier: усиление схемы и исправленная база вне MT4

### Добавлено
- `ML/tb_signal_logic.py`: общая TB логика выбора сигнала по calibrated probability + expected value, итоговая оценка rules и no-trade gate по `min_ev`
- `ML/tb_probability_calibration.py`: validation-only isotonic calibration для `triple_barrier`
- Новый набор TB-тестов: `tests/test_triple_barrier_first_touch.py`, `tests/test_triple_barrier_calibration.py`, `tests/test_generate_signals_research.py`, `tests/test_signal_tracer_tb.py`, `tests/test_triple_barrier_training.py`
- Frozen artifacts: `ML/reports/tb_probability_calibrator.joblib`, `ML/reports/tb_selected_rule.json`, `ML/reports/tb_validation_logits.npy`, `ML/reports/tb_validation_targets.npy`

### Изменено
- TB-разметка переведена на реальное первое касание барьеров по OHLC-path; timeouts теперь хранятся отдельно как `0.5`
- Исправлена привязка времени в TB-разметке: исход теперь считается от времени строки сигнала
- `ML.train`, `ML.threshold_analysis`, `ML.evaluate_test` и `API.generate_signals` переведены на calibrated TB probabilities и validation-first freeze
- Исправлен transfer-learning path для TB: модель теперь наследует недостающие encoder `model_kwargs` из source checkpoint и реально загружает `40` слоёв вместо прежнего частичного матча
- `statistics/signal_tracer.py` теперь понимает TB-логи `TB BUY/SELL prob=... ev=... SL=...ATR TP=...ATR ...` и умеет строить TB dossier поверх labeled CSV

### Результаты
- Validation зафиксированное правило:
  - `theta=0.475`, `min_ev=0.10`, `N=121`, `wins=70`, `losses=51`, `timeouts=14`, `PF=1.53`
- Final one-shot `test` confirmation:
  - `theta=0.475`, `min_ev=0.10`, `N=253`, `wins=128`, `losses=125`, `timeouts=24`, `PF=1.11`, `win_rate=50.6%`
- Fresh `ml_signals_tb.csv` regenerated from calibrated probabilities: `BUY=670`, `SELL=46`, `FLAT=58050`

### Вывод
Это усиление было нужно и полезно, но старые слишком сильные TB-цифры больше не актуальны: после исправления времени старта сделки база вне MT4 стала заметно слабее, зато честнее. Теперь смысл TB определяется не “бумажным PF”, а тем, что после новой проверки в MT4 он больше не расходится с торговой системой по самой сути сделки. Подробный отчёт: [docs/reports/2026-04-08-triple-barrier-hardening.md](docs/reports/2026-04-08-triple-barrier-hardening.md)

## [2026-04-08] — Validation-first ML Exit Research: frozen winner = timeout-only

### Добавлено
- Новый standalone research tool `API/exit_policy_research.py` для offline-симуляции выходов и position blocking поверх существующего `MT/MQL4/Files/ml_signals.csv`, с жёстким split по `DATA/Nero_validation_labeled.csv` / `DATA/Nero_test_labeled.csv`
- `tests/test_exit_policy_research.py` (10 тестов) на exit triggers, split boundary, same-bar reversal, ranking и guard против search-loop на `test_final`
- Frozen policy artifact `ML/reports/frozen_exit_policy.json`

### Результаты
- Validation grid-search по exit-policy library (`reverse`, `weak_edge`, `profit_guard`, layered) не обогнал baseline:
  - `timeout_only`: `PF=1.17`, `N=567`, `win_rate=50.97%`, `avg_hold_bars=12.0`
  - лучший новый кандидат `profit_guard_p1.5_k1.8_h2`: `PF=1.16`, `N=777`
- Final one-shot check на `test` по frozen JSON:
  - `timeout_only`: `PF=1.12`, `N=558`, `win_rate=50.72%`, `avg_hold_bars=11.98`

### Вывод
Validation-first protocol отработал как intended: ни одно новое ML-exit правило не прошло честную проверку против уже существующего `ML_Timeout(12H)` baseline. Поэтому новый exit rule в MQL4 не переносился; замороженной политикой остаётся `timeout_only`, уже реализованный в `MT/MQL4/Include/OUTPUT.mqh`.
Подробный отчёт: [docs/reports/2026-04-08-ml-exit-validation-first.md](docs/reports/2026-04-08-ml-exit-validation-first.md)


## [2026-04-04] — Archetype × Filter Bridge: fav_3_vs_12 обогащает winning архетип, pullback не нужен

### Результаты
- `fav_3_vs_12 <= 0.653` повышает долю winning архетипа на holdout: 44.0% vs 37.4% baseline (+6.6 pp)
- `ratio_3_vs_12 > 4.751` НЕ обогащает winning архетип: 33.5% на holdout (хуже baseline)
- Pullback 1ATR заполняет 84% failure vs 20% winning сигналов; pullback 3ATR + фильтр = 0 winning fills
- `fav_3_vs_12 <= 0.653` + market: PF=1.78, N=84, 44% winning — лучшая комбинация
- `ratio_3_vs_12 > 4.751` + market: PF=0.81 — не работает без pullback

### Вывод
`fav_3_vs_12 <= 0.653` — единственный фильтр, коррелирующий с winning архетипом. С ним market entry достаточен (PF=1.78). Pullback поверх фильтра теряет winning сигналы (они не откатываются). `ratio_3_vs_12 > 4.751` работает только через pullback + mechanical price improvement, не через archetype selection. Оба фильтра ортогональны.
Подробный отчёт: [docs/reports/2026-04-04-archetype-filter-bridge.md](docs/reports/2026-04-04-archetype-filter-bridge.md)

---

## [2026-04-04] — Signal Path Atlas Readout: двумодальная структура сигнала, edge = selection, не timing

### Результаты
- Первый канонический atlas readout на 1752 discovery + 851 holdout signals
- Глобальный сигнал direction-neutral: медиана signed_ret_12 = -0.064 ATR, first-passage и ordering практически симметричны
- Двумодальная архетипная структура реплицирована на holdout: 64% failure (ret Q50 = -0.80 ATR) vs 36% flat_or_noisy_drift (ret Q50 = +1.73 ATR)
- Winning архетип имеет минимальный adverse excursion (adv Q50 = 0.48 ATR) — у winning signals нет отката для pullback entry
- ATR Q4 failed holdout replication (N=530) — ATR bucket conditioning нестабильно из-за volatility regime shift
- ratio_bin_12=4-5 только directionally consistent, не fully replicated
- 31 artifact Replicated, 45 Failed: spread features переносятся лучше ratio features
- Execution implications: `neither` — ни market ни pullback не поддержаны как самостоятельные направления; edge — в signal selection

### Вывод
Atlas переформулирует задачу: проблема edge — в отборе 36% winning signals (flat_or_noisy_drift), а не в оптимизации entry timing на population из 64% failures. Pullback «работает» через mechanical price improvement + selection filtering, а не через direction-level dip-then-rally pattern. Locked Variant 3 winner ослаблен (оба pillar — ratio 4-5 и ATR Q4 — weakly supported). Следующий шаг — проверить, предсказывают ли quality filters принадлежность к winning архетипу.
Подробный отчёт: [docs/reports/2026-04-04-signal-path-atlas-readout.md](docs/reports/2026-04-04-signal-path-atlas-readout.md)

---

## [2026-04-04] — Signal Quality Filter Research (Variant 4): multi-horizon quality filters × pullback entry

### Добавлено
- Создан новый standalone research tool `API/signal_quality_research.py` с 6-step pipeline: variance check → univariate response maps → shallow tree → pairwise combinations с negative control → score holdout validation → cross-analysis quality filters × pullback entry
- Реализованы 3 filter feature families (17 features): `ratio_h`, `spread_h`, `short_vs_long` divergence из multi-horizon predictions (up_3..dn_48)
- Добавлен cross-analysis: quality filters × Variant 3 pullback entry scenarios на discovery и holdout отдельно
- `tests/test_signal_quality_research.py` (19 тестов)

### Результаты
- Score-based подход (additive score из нескольких features) не работает — holdout не подтверждает (7/8 NOT CONFIRMED)
- Индивидуальные правила работают: 7/10 top rules подтверждены на holdout
- Shallow tree выделил `fav_3_vs_12` (pred_fav_3/pred_fav_12) как доминирующий discriminator (100% importance)
- Два discovery-confirmed filter axis: `fav_3_vs_12 <= 0.653` и `ratio_3_vs_12 > 4.751`
- Cross-analysis выявил два holdout-confirmed кандидата:
  - Агрессивный: `ratio_3_vs_12 > 4.751 + pullback entry_close-1ATR` — PF=1.62, N=94 (holdout)
  - Консервативный: `ratio_3_vs_12 > 4.751 + pullback entry_close-3ATR` — PF=3.52, N=24 (holdout)

### Вывод
Multi-horizon predictions дают лучшую фильтрацию, чем ratio_12 alone, но через индивидуальные правила, а не additive scores. Pullback entry без фильтра — generic "better price" effect; quality filter добавляет cohort-specific uplift поверх. Следующий шаг — верификация кандидатов через Signal Path Atlas pipeline.
Подробный отчёт: [docs/reports/2026-04-04-signal-quality-filter.md](docs/reports/2026-04-04-signal-quality-filter.md)

---

## [2026-04-03] — Signal Path Atlas: standalone research CLI, frozen holdout replication и stage close

### Добавлено
- Добавлен новый standalone research tool `API/signal_path_atlas.py` для ATR-normalized `discovery / holdout` path atlas без возврата к прямому `PF`-ranking rule search
- Добавлены discovery-atlas outputs: `path_quantiles`, `first_passage`, `ordering`, numeric/categorical slices, path archetypes, holdout verdicts и optional CSV export
- `tests/test_signal_path_atlas.py` покрывает split semantics, path tensor, feature screen, slice merging, archetypes, holdout verdicts и CLI smoke
- Обновлён `API/README.md` с командой запуска path atlas CLI

### Исправлено
- Убран holdout leakage из `atr_bucket`: ATR bucket edges теперь фиксируются только по discovery и переиспользуются на holdout
- Исправлен holdout numeric slice matching: повторяющиеся bin boundaries больше не double-count строки между соседними slices
- `main()` больше не падает, если feature screen убирает все live numeric features
- Archetype naming стабилизирован для collapsed / role-collision случаев, чтобы нейтральные кластеры не получали ложные recovery labels

### Результаты
- Новый atlas CLI успешно проходит верификацию:
  - `pytest tests/test_signal_path_atlas.py -q` → `38 passed`
  - `python -m API.signal_path_atlas --test-only` → успешно
  - `python -m API.signal_path_atlas --test-only --export-dir /tmp/signal_path_atlas` → успешно
- Экспортируемый atlas surface теперь включает `split_summary`, `feature_screen`, `path_quantiles`, `first_passage`, `ordering`, `numeric_slices`, `categorical_slices`, `archetype_summary`, `holdout_verdicts`, `execution_implications`
- На текущем smoke run path-atlas слой не даёт немедленной execution-рекомендации: `execution_implications = neither`

### Вывод
Stage B research сместился с narrow winner-specific PF follow-up к reusable path-atlas workflow. Следующий шаг — читать atlas outputs как канонический research artefact и уже из replicated path claims решать, оправдан ли будущий `market`, `pullback`, оба или ни один.
Подробный отчёт: [docs/reports/2026-04-03-signal-path-atlas.md](docs/reports/2026-04-03-signal-path-atlas.md)

---

## [2026-04-02] — signal_research Variant 3 robustness pass: support ladder и stricter shortlist

### Добавлено
- В `API/signal_research.py` добавлен robustness-layer поверх полной Variant 3 matrix: support ladder `10/5 -> 20/10 -> 30/10 -> 40/15`, baseline deltas против `market` (`PF_delta`, `AvgPnL_delta`) и helpers для filtered verdict
- `Variant 3 Shortlist Verdict` теперь требует не только положительный uplift против `market`, но и support tier не ниже `Supported` (`30/10` или `40/15`), поэтому tiny-fill rows больше не могут выигрывать по голому `PF`
- `tests/test_signal_research.py` расширен тестами на robustness annotation, floor-by-floor support ladder и новый shortlist verdict

### Результаты
- Low-fill artefacts удалены из shortlist: `cancel-window entry_close-3ATR@1b` / `@3b` больше не становятся “победителями”, а `ratio 4-5 × ATR Q4 + pullback pic_price-1ATR` понижен до exploratory/standard-only варианта
- После фильтра robust survivors для primary cohorts: `ratio 4-5 × ATR Q4 + pullback entry_close-2ATR` (`PF=3.69`, `36` fill-ов, `35.6%`), `ratio 4-5 + pullback entry_close-3ATR` (`PF=3.55`), `BUY + pullback entry_close-3ATR` (`PF=2.35`), `ATR Q4 + pullback entry_close-3ATR` (`PF=2.57`)
- Negative controls под тем же фильтром тоже улучшаются, но слабее: `ratio 3-4 + pullback entry_close-3ATR` (`PF=1.62`, `ΔPF=+0.69`), `non-Q4 + cancel-window entry_close-1ATR@1b` (`PF=1.41`, `ΔPF=+0.39`)
- Самый чистый transportable survivor — `ratio 4-5 × ATR Q4 + pullback entry_close-2ATR`: на тех же controls его uplift почти исчезает (`ratio 3-4: PF=1.13`, `non-Q4: PF=1.04`)

### Вывод
Robustness pass оставил один действительно интересный кандидат для будущего EA-прототипа: `ratio 4-5 × ATR Q4 + pullback entry_close-2ATR`. Более глубокий `entry_close-3ATR` остаётся сильным research-эффектом на primary cohorts, но уже не выглядит чисто cohort-specific, потому что заметно улучшает и controls.
Подробный отчёт: [docs/reports/2026-04-02-signal-research-variant-3.md](docs/reports/2026-04-02-signal-research-variant-3.md)

---

## [2026-04-02] — signal_research Variant 3: scenario matrix, raw pic_price и OHLC validation

### Добавлено
- `API/signal_research.py` расширен до full Variant 3: `market`, `pullback`, `delayed`, `cancel-window`, общая матрица `cohort x scenario x params`, новые секции `Variant 3 Scenario Matrix`, `Variant 3 Shortlist Verdict`, `Variant 3 Negative Controls`
- `pic_price` теперь извлекается из raw `MT/MQL4/Files/Nero.csv` как цена самого позднего embedded fractal внутри строки, а не по порядку колонок и не через OHLC proxy
- `tests/test_signal_research.py` расширен тестами на raw fractal parsing, row-level latest-fractal extraction, OHLC validation, fill logic и Variant 3 report smoke

### Исправлено
- Исправлена критичная ошибка research-layer: `pic_price` теперь протягивается в excursion/matrix pipeline, поэтому pic-relative Variant 3 scenarios больше не падают в ложный `0 fill`

### Результаты
- OOS CLI run (`2022-07-18 11:00:00` — `2026-03-20 06:00:00`) дал `2603` реальных сигналов с excursion-данными и полную Variant 3 matrix на shortlist/controls
- OOS `pic_price` validation: `9403/9403` test-slice rows matched expected OHLC `High/Low` side within tolerance
- Deep pullback entries заметно улучшают primary cohorts на бумаге: например, `ratio 4-5 × ATR Q4` вырос от `market PF=1.34` до `pullback pic_price-1ATR PF=6.20` (`22` fill-а), а `ATR Q4` от `1.12` до `pullback entry_close-3ATR PF=2.57` (`106` fill-ов)
- Но negative controls тоже улучшаются: `ratio 3-4` от `market PF=0.92` до `pullback entry_close-3ATR PF=1.62`, `non-Q4` от `1.02` до `cancel-window entry_close-1ATR@1b PF=1.41`

### Вывод
Variant 3 tooling и каноническая execution matrix готовы, но финальный winner ещё не зафиксирован: текущий auto-verdict слишком чувствителен к low-fill сценариям, а uplift частично переносится и на negative controls. Следующий шаг — ужесточить robustness-фильтр и только потом выбирать кандидатов для EA.
Подробный отчёт: [docs/reports/2026-04-02-signal-research-variant-3.md](docs/reports/2026-04-02-signal-research-variant-3.md)

---

## [2026-04-02] — signal_research Variant 3 prep: canonical ATR, cohort map и shortlist для Variant 3

### Добавлено
- `MT/MQL4/Scripts/ExportOHLC.mq4` теперь экспортирует `time;open;high;low;close;volume;atr14`, а `API/signal_research.py` использует канонический `atr14` из CSV с Python fallback для старых файлов
- `API/signal_research.py` расширен секциями `Cohort Map`, `Entry Opportunity Profile`, `Stability Split`, `Priority Cohorts`
- В исследовательский слой добавлена baseline-аннотация фиксированного сетапа `12H / SL=5 / TP=50`
- `tests/test_signal_research.py` расширен тестами на ATR source selection, cohort summaries, entry-opportunity метрики и новые секции отчёта

### Результаты
- OOS `2022-07-18 11:00:00` — `2026-03-20 06:00:00`: `2603` реальных сигналов с excursion-данными
- Лучший кандидат для Variant 3: `ratio 4-5 × ATR Q4` (`N=101`, `PF_12=2.62`, `Net_12 mean=22.2`, `AvgPnL_baseline=1.4`)
- Лучший широкий ratio-бакет не изменился: `ratio 4-5` (`PF_12=1.95`), а `ratio 3-4` остался устойчивым анти-паттерном (`PF_12=0.87`)
- `pic_price` validated against OHLC on the full deduplicated `Nero.csv` universe: `58766` rows, `100%` match to fractal-bar `High/Low` within `0.05` tolerance (`max abs error = 0.05`)
- После пересчёта prep path profile в ATR-единицы старое преимущество Q4 по раннему pullback почти исчезло; surviving edge остался в favorable continuation, особенно у `ratio 4-5 × ATR Q4`
- Broad `SELL` по-прежнему слабый (`PF_12=0.95`), а `BUY` и `ATR Q4` выглядят лучшими общими группами для следующего этапа

### Вывод
Этап подтвердил, что Variant 3 нужно запускать не по всей выборке, а по shortlist когорт. При этом ATR-нормализация убрала иллюзию “очевидного pullback edge” у Q4, поэтому главный приоритет теперь — прямое сравнение `market / pullback / delayed / cancel-window` на `ratio 4-5 × ATR Q4`, `ratio 4-5`, `BUY`, `ATR Q4`, с `ratio 3-4` и `non-Q4` как отрицательными контролями.
Подробный отчёт: [docs/reports/2026-04-02-signal-research-variant-3-prep.md](docs/reports/2026-04-02-signal-research-variant-3-prep.md)

---

## [2026-04-01] — signal_research Variant 2: path-dependent профили сигнала и торговые выводы

### Добавлено
- `API/signal_research.py` расширен до Variant 2: `Signal Passport`, `Pullback Profile`, `First-Hit Barrier Matrix`, `Amplitude Filters`, `Regime Split`, `Practical Conclusions`
- Path-dependent анализ барьеров по OHLC: для каждой пары `SL/TP` фиксируется `TP_FIRST` / `SL_FIRST` / `NEITHER`, а не только итоговый MFE/MAE
- Расчёт `ATR(14)` внутри Python и regime split по квартилям волатильности
- Новые unit-тесты `tests/test_signal_research.py` для ATR, pullback-метрик, barrier logic, отчётных секций и регрессии по `ratio_bin`

### Исправлено
- `report_by_ratio()` больше не мутирует `ratio_bin` и не создаёт ложную строку `ALL` в последующих секциях отчёта

### Результаты
- OOS `2022-07-18` — `2026-03-20`: `2603` реальных сигналов с excursion-данными
- Ранний откат после входа существенный: `adv_1=5.6`, `adv_3=8.8`, `adv_6=12.2` пункта по всей выборке
- По first-hit матрице лучший базовый сетап на горизонте `12H`: `SL=5`, `TP=50`, `PF=1.05`, `AvgPnL=0.2`
- По режимам: `BUY PF_12=1.35`, `SELL PF_12=0.95`; лучший ratio-бакет `4-5` (`PF_12=1.95`), бакет `3-4` остаётся убыточным (`PF_12=0.87`)
- По волатильности: `ATR Q4` даёт `PF_12=1.23`, тогда как `Q1/Q3` близки к нулевому edge

### Вывод
Исследование подтвердило, что сигнал даёт не сильный импульс, а слабый статистический дрейф, который легко теряется неудачной механикой входа. Для Variant 3 нужно тестировать не только `SL/TP`, но и сам способ входа: `market`, вход на откате, задержанный вход и окна отмены сигнала.
Подробный отчёт: [docs/reports/2026-04-01-signal-research-variant-2.md](docs/reports/2026-04-01-signal-research-variant-2.md)

---

## [2026-04-01] — 10-target модель, новый CSV формат, исследование фильтров

### Добавлено
- 10-target регрессия (up_3..dn_48): pearson_r=0.5625 (+28% vs 6-target)
- CSV v3.0: `time;signal;up_3;dn_3;up_6;dn_6;up_12;dn_12;up_24;dn_24;up_48;dn_48` (ratio удалён)
- EA: параметры ML_Filter3, ML_Filter6 (фильтры по коротким горизонтам)
- `API/signal_research.py` — статистика MFE/MAE/PF по горизонтам, ratio-бакетам, SL/TP сетке

### Результаты
- MT4 PF=1.18 (идентично 6-target — сигнал по-прежнему на up_12/dn_12)
- Filter3/Filter6 как ratio-threshold **бесполезны**: 96% сигналов имеют ratio_3 > 5.0
- Аномалия: ratio_12 бакет 3-4 убыточен (PF=0.87), бакет 4-5 лучший (PF=1.95)
- Лучший фиксированный SL/TP: SL=5, TP=30, R:R=6x, PF=1.43

### Вывод
Короткие горизонты (up_3 r=0.80, up_6 r=0.67) предсказываются отлично, но как фильтр направления не работают — модель всегда согласна по направлению на всех горизонтах. Нужен другой подход: амплитудный фильтр, исключение убыточного ratio-бакета 3-4, или оптимизация SL/TP.

---

## [2026-03-31] — Bugfix: ATR-индекс сдвинулся при добавлении полей B.1 — PF восстановлен 1.24

### Исправлено
- **Корневая причина падения PF**: в `data_loader.py` проверка `split.shape[1] == 18` стала ложной после расширения формата фрактала с 18 до 22 полей. Все фракталы помечались как padding → X = нули → модель обучалась на пустых данных.
- `data_loader.py`: `split.shape[1] == N_RAW_FEATURES` → `>= N_RAW_FEATURES`; добавлен `FRACTAL_ATR_RAW_IDX=21`; поля 17-20 (up_3/dn_3/up_6/dn_6) пропускаются в X
- `processing/normalize.py`: `FRACTAL_INDICES['fractal_atr']` = 17 → 21; `parse_fractal` читает до 22 полей; `n_features` = 18 → 22

### Результаты
- Старый чекпоинт (из `cfeacfc`) на исправленном пайплайне: **PF=1.24** ✓ (baseline воспроизведён)
- BUY=8460, SELL=7962 — баланс сигналов восстановлен (~1:1)
- Все предыдущие эксперименты этой сессии (pearson_r=0.43-0.45, PF=0.87-0.97) были испорчены этим багом

### Вывод
Добавление полей up_3/dn_3/up_6/dn_6 в формат фрактала (Phase B.1) сдвинуло `fractal_atr` с индекса 17 на 21. Python-код не был обновлён синхронно → единственный символ `==` убил все результаты. Гипотезы о нормализации и capacity dilution были ложными.

После исправления свежеобученная модель (pearson_r=0.437): **PF=1.18, 584 сделки, просадка 12.66%** — лучше старого чекпоинта по числу сделок и прибыли. Добавлены три уровня валидации в `data_loader.py` для предотвращения повторных рассинхронов формата.

---

## [2026-03-31] — Phase B.1: Добавлены 3H/6H таргеты — pearson_r вырос, PF упал

### Добавлено
- Новые горизонты up_3/dn_3/up_6/dn_6 в MQL4 (LEVELS_FIND_AROUND, NERO_CSV) и Python-пайплайне
- UPDN_TARGETS расширен с 6 до 10 таргетов
- N_FRACTAL_FEATURES: 20 → 24 (4 новых фичи в X)

### Результаты
- **pearson_r: 0.433 → 0.565** (+30%) — значительное улучшение качества модели
- **PF: 1.20 → 0.87** — результат в тестере хуже baseline
- BUY=12986, SELL=6349 (дисбаланс 2:1, раньше было ближе к равному)
- Win rate: BUY=50%, SELL=35% — SELL-сигналы нерабочие

### Гипотеза причины провала
Короткие таргеты up_3/dn_3 (34% нулей, мелкие значения) попали в общий пул нормализации с up_12..dn_48. Это сдвинуло перцентили brk/cap вниз, изменив масштаб нормализации всех updn-значений. Модель обучилась лучше предсказывать короткий горизонт, но сигналы по 12H ухудшились.

### Вывод
Добавление 3H/6H таргетов без раздельной нормализации не работает. Возможные направления: (1) нормализовать up_3/dn_3/up_6/dn_6 отдельным пулом от up_12..dn_48; (2) использовать 3H/6H только как фичи, не как таргеты; (3) откатить B.1 и пробовать другой подход.


## [2026-03-31] — Phase B.4: Directional Asymmetric Loss — эксперимент провален

### Результаты
- **Directional α=2.5**: PF=1.04, 352 сделки (baseline: PF=1.20, 366 сделок)
- **Directional α=5.0**: PF=0.97, 533 сделки (убыточно)
- Все варианты хуже production модели (huber loss, r=0.56)

### Вывод
Directional asymmetric loss не работает. Снижение r с 0.56 до 0.43 не компенсируется консервативностью на adverse direction — модель теряет предсказательную силу сильнее, чем выигрывает от асимметрии. Production модель восстановлена (`git checkout ML/checkpoints/transformer_updn_best.pt`).

**Не повторять**: directional asymmetric loss на regression_updn с текущими фичами не даёт прироста PF.


## [2026-03-27] — Phase A EA Optimization: финал PF=1.23, лучшая конфигурация найдена

### Добавлено
- **`ML_MaxRatio`** параметр: фильтр ratio>4.5 убирает 72% SL-сделок (321→91)
- **`ML_CalcRR()`**: динамический R:R — Mode 1 (log+cap=2.5) вместо жёсткого cap
- **`ML_RR_Mode`, `ML_RR_Cap`, `ML_ExitEnabled`, `ML_ExitThreshold`** — новые extern параметры EA
- **`ExportOHLC.mq4`**: скрипт экспорта 126,637 H1 баров XAUUSD → DATA/XAUUSD_H1_OHLC.csv
- **`signal_tracer.py`**: поля `close_price`, `mt4_pnl_pips`, `mt4_pnl_atr` в CSV
- **`analyze_path_ordering.py`**: bar-by-bar scan OHLC, определение SL_FIRST vs TP_FIRST

### Результаты тестов
- **PF: 0.53 → 1.23** — лучший конфиг: ML_MaxRatio=4.5, ML_RR_Mode=1, ML_ExitEnabled=1, ExitThreshold=2.0
- ML_Exit OFF + T1=7 (21 баров): PF=1.20 — хуже: avg loss растёт ($85→$95) сильнее avg win ($108→$114)
- ML_Exit даёт +0.03 PF за счёт 94 ранних выходов из losers до SL
- T1 (hold time) неважен при ML_Exit ON — HoldOverTime=0, ML_Exit закрывает всё первым

### Path-ordering анализ (analyze_path_ordering.py)
- BOTH_HIT: 92% SL_FIRST — подтверждено, но теперь только 24 сделки (7%)
- TP_CLEAR + SL_FIRST: 33 сделки — цель для first-barrier-hit лейблинга
- TP_CLEAR + TIMEOUT: 100 сделок; 83% достигают TP за ≤24 бара (текущее окно = 12)
- Главный вывод: модель правильно предсказывает направление, но TP слишком далеко и/или путь идёт через SL

### Вывод
- Phase A потолок достигнут — дальнейший рост требует переобучения модели
- Phase B план: [docs/superpowers/plans/2026-03-27-pf-improvement-phase-b.md](docs/superpowers/plans/2026-03-27-pf-improvement-phase-b.md)
- Приоритет Phase B: first-barrier-hit лейблинг → asymmetric loss → лимитный вход


## [2026-03-26] — ME-13 Diagnostics: анализ 922 сделок MT4 Strategy Tester

### Результаты
- **PF(SL/TP) = 0.53** при текущих параметрах (922 сделки, WR=37.3%). 51% сделок закрываются по MARKET-таймауту, не достигая ни SL, ни TP
- **Ratio > 4.5 — убыточная зона**: TP = 8 ATR недостижим, PF падает до 0.08–0.40. Прибыльный диапазон — ratio [3.5, 4.5) с PF=1.05–1.13
- **Рекомендация**: ограничить ML_MaxRR ≤ 2.0 или ввести ML_MaxRatio ≤ 4.5

### Вывод
- Полный отчёт: [docs/archive/signal_tracer/trade_analysis_20260324.md](docs/archive/signal_tracer/trade_analysis_20260324.md)


## [2026-03-25] — ME-13 Diagnostics: per-row updn_params + точная денормализация ground truth

### Добавлено
- **`DATA/Nero_{train,validation,test}_updn_params.npy`**: per-row `(brk, cap)` параметры нормализации, сохраняются pipeline-ом при каждом запуске `label_main.py`
- **`processing/normalize.py`**: параметр `return_updn_params=True` → возвращает `(df, updn_params)` с shape `(N, 2)`
- **`statistics/signal_tracer.py`** v2.2: денормализация up_12/dn_12 через per-row brk/cap (точный inverse piecewise_linear_log), 4-категорийная классификация теперь работает корректно
- **`tests/test_inverse_piecewise.py`**: 6 round-trip тестов для `inverse_piecewise_linear_log` + тест `normalize_rowwise(return_updn_params=True)`

### Исправлено
- **Классификация TP_CLEAR/SL_CLEAR/BOTH_HIT/TIMEOUT**: ранее up_12/dn_12 брались из fractal[0] (всегда 0) → все сделки падали в TIMEOUT. Теперь правильно денормализуются из строки labeled CSV.

### Вывод
- Инструмент `signal_tracer.py` теперь способен выдавать реальные категории расхождения Python/MT4: какой % сделок — BOTH_HIT (MFE/MAE иллюзия), какой — SL_CLEAR (реальные убытки)


## [2026-03-24] — ME-13 Diagnostics: signal_tracer.py v2.0 (Trade-level reconciliation)

### Добавлено
- **`statistics/signal_tracer.py`**: инструмент разбора полётов — сравнивает ML-предсказание с реальным ходом цены.
  - **`--time`**: полное досье одного сигнала
  - **`--batch`**: top-N высокорейтинговых сигналов, сводная таблица + CSV
  - **`--from-log`**: разбор реальных сделок из лога MT4 Strategy Tester
- **Точная реплика формулы MT4 SL/TP** (lib_ML_Signal.mqh): `SL = max(pred * ScaleK * ATR, ATR * Min_SL_ATR)`, `TP = SL * min(ratio / MinRatio, MaxRR)`
- **INI-парсер**: параметры ML читаются из `$o$imple.ini`
- **4-категорийная классификация**: `TP_CLEAR` / `SL_CLEAR` / `BOTH_HIT` / `TIMEOUT`

### Результаты (--from-log --losses-only, 321 убыточная SL-сделка, 2023–2026)
| Категория | Кол-во | % | Смысл |
|-----------|--------|---|-------|
| TIMEOUT | 161 | 50% | Ни SL ни TP за 12H |
| SL_CLEAR | 108 | 34% | SL был неизбежен |
| **TP_CLEAR** | **33** | **10%** | **TP достижим, но MT4 выбил SL раньше** |
| BOTH_HIT | 13 | 4% | Оба барьера, порядок неизвестен |

Погрешность формулы: `SL Δ = −3.91`, `TP Δ = −7.40` (причина: fractal_atr < ATR на баре входа).

### Вывод
1. **MFE/MAE иллюзия подтверждена**: 33 сделки — Python видел TP достижимым, MT4 выбило SL первым.
2. **SL от пола (Min_SL_ATR)**: `pred_dn * ScaleK * ATR` ≪ `ATR * 2.0` — модель предсказывает dn близко к нулю при высоком ratio, но реальный ход вниз превышает SL.
3. **Формула недооценивает SL/TP**: ATR фрактала ниже ATR на баре входа при росте волатильности.

## [2026-03-23] — Triple Barrier Classification (параллельный ML-трек)

### Добавлено
- **Triple Barrier таргет**: 12 бинарных таргетов (6 SL/TP комбо × 2 направления), предсказывающих P(TP hit before SL). SL grid: [2, 3] ATR, TP grid: [3, 6, 9] ATR, timeout: 24 бара.
- **`label_triple_barrier()`**: Маркировка на сырых up_24/dn_24 до нормализации. Неоднозначные случаи (оба барьера) → label=0 (консервативно).
- **`--task triple_barrier`**: Поддержка во всех ML-скриптах (train, evaluate_test, threshold_analysis, compare_architectures, optimize, generate_signals).
- **BCEWithLogitsLoss с pos_weight**: Автоматически вычисляемый вес для компенсации дисбаланса классов.
- **Реалистичный PF**: `PF = (wins × TP) / (losses × SL)`, timeouts = полный SL loss (консервативная нижняя граница).
- **`generate_tb_signals()`**: Выбор лучшей SL/TP комбинации по Expected Value: `EV = P × TP - (1-P) × SL`.
- **`lib_ML_Signal_TB.mqh`**: MT4 интеграция (iSignal=5), фиксированные SL/TP из CSV вместо адаптивных.
- **`ml_signals_tb.csv`**: Формат `time;signal;sl_atr;tp_atr;prob;ev`.

### Результаты
- **Transfer learning**: Энкодер из regression_updn checkpoint обязателен — обучение с нуля даёт AUC=0.5000 (коллапс энкодера при BCE+pos_weight=n_neg/n_pos создаёт нейтральную точку sigma=0.5).
- **Val Mean AUC = 0.7172** (transformer, 104k params, epoch 5, LR=0.001).
- **OOS Mean AUC = 0.7002**: buy_sl2_tp3 AUC=0.68 PF=1.41, buy_sl3_tp3 PF=1.11. SELL-таргеты на тестовой выборке PF < 1.0 (период теста — преимущественно бычий рынок).
- Threshold θ=0.5: BUY сигналов 14,865, SELL 19,623 из 58,766 строк в ml_signals_tb.csv.

### Вывод
Цель: устранить разрыв между Python PF (MFE-based, 4.50) и MT4 PF (фиксированные SL/TP, 1.03). Triple Barrier считает PF из фиксированных уровней — Python PF напрямую соответствует торговой механике MT4. Ожидаемый gap < 20%.

## [2026-03-23] — ME-14 & ME-15: Адаптивная фиксация прибыли и Оптимизация (R:R и Trailing Stop)

### Добавлено
- **Жесткий Trailing Stop**: Внедрен отдельный ML-трал (по умолчанию поджим `0.5 ATR`), чтобы фиксировать пиковые рывки (MFE) до истечения горизонта 12 баров.
- **Физическая реализация Асимметричного R:R**: Концепция из этапа ME-13 теперь полноценно прописана в коде `lib_ML_Signal.mqh`, заменив временный хардкод `R:R=1:1`.
- **Внешние параметры оптимизации**: Глобальные константы ML вынесены в `SoSimple.mq4` (раздел `inputs`) для генетической оптимизации тестером: `ML_Trl_Start_ATR`, `ML_Trl_Step_ATR`, `ML_MinRatio`, `ML_MaxRR`, `ML_ScaleK`, `ML_Min_SL_ATR`, `ML_BypassTrend`. В файл `SoSimple.ini` добавлены диапазоны оптимизации.

### Изменено
- **Защита от MT4-выходов**: ML-сделки (iSignal == 3) больше не закрываются преждевременно до срабатывания SL/TP по общим правилам эксперта (например, `ImpulseOver`, `Global<0`, NearBuy).
- **Переворот позиций (Reversal)**: При поступлении уверенного (> ML_MinRatio) противоположного сигнала, текущая позиция немедленно закрывается с причиной `ML_Reversal`, вместо блокировки нового сигнала (`PosBlock` снизился с 51% до 2%).

### Результаты (XAUUSD H1, 2023-2026, Базовый Trailing=0.5 ATR)
- Проблема блокировки сигналов решена: исполнено **762** сделки.
- Экстремальный рост доли прибыльных сделок (Win Rate): с 34.55% до **54.07%**.
- Profit Factor (PF) практически достиг точки безубыточности: **0.99** (ранее 0.93).
- *Открытие (до глобальной оптимизации)*: Чем жестче шаг трала (`0.5 ATR` vs `1.5 ATR`), тем выше оборачиваемость и PF (0.96 vs 0.91), так как цена почти всегда откатывается перед 12-м часом, а трал успевает "прихватить" пик (MFE) задолго до окончания таймаута.

### Итоги Глобальной Генетической Оптимизации (Holistic Optimization)
После выноса метрик во внешние переменные (`SoSimple.mq4`) мы пробили долгожданный порог прибыльности в MT4! 
**Лучший сет (PF=1.03, Сделок=922, Profit=+1207.61)**:
- `ML_MinRatio = 3.5` (Чуть более мягкий фильтр входов, повысил количество сделок)
- `ML_Min_SL_ATR = 2.0` (Широкий стоп-лосс, дающий цене "подышать" без случайных выбиваний рыночным шумом)
- `ML_Trl_Start_ATR = 1.0` (Трал включается только после достижения уверенного профита в 1 ATR)
- `ML_Trl_Step_ATR = 1.5` (Широкий и "ленивый" трал, позволяющий прибыли расти)

Как видно, когда мы позволили MT4 искать баланс среди всех параметров сразу (вместо жестко фиксированного Stop Loss в `1.5 ATR`), лучшим вариантом оказалась стратегия **"Дать прибыли расти"**. При широком стопе (`2.0`) и широком трале (`1.5`) общая прибыльность перекрывает стратегию жесткой мгновенной фиксации пиков. Впервые сырая ML-модель стала прибыльной в условиях сурового симулятора MT4!
Прогон генетического алгоритма в значительно более широких диапазонах параметров (`ML_Min_SL_ATR` до 6.0, `ML_ScaleK` до 30, `ML_MaxRR` до 16, `ML_Trl_Start` до 6.0) показал, что:
1. Максимум **PF=1.03** является *устойчивым глобальным экстремумом* в данном пространстве.
2. Экстремально широкие стопы (например, `4.0+ ATR`) и сниженные фильтры (`ML_MinRatio=3`) приводят к 1165 сделкам, но снижают Profit Factor обратно до уровня безубыточности `PF=1.00` (max Profit=+169).

## [2026-03-22] — ME-13: Асимметричный R:R и диагностика ML-интеграции

### Добавлено
- **Асимметричный R:R**: TP = SL × min(ratio / ML_MinRatio, ML_MaxRR). Вместо фиксированного R:R=1:1 TP масштабируется по уверенности модели (ratio). При ratio=10 и ML_MinRatio=2.665 → R:R=1:3.75
- **Диагностические счётчики**: ML_cnt_total/trend/lowratio/posblock/executed — количественная оценка потерь на каждом фильтре
- **ML_DIAG_PRINT()**: Итоговый отчёт в OnTester() — показывает разбивку фильтрации

### Изменено
- `ML_MinRatio`: 5.0 → 2.665 (совпадает с Python θ)
- `lib_ML_Signal.mqh`: v1.1 → v2.0

### Результаты (XAUUSD H1, 2023-2026, ML_MinRatio=2.665, ML_MaxRR=4.0, ML_BypassTrend=true)

**ML DIAGNOSTICS:**
| Фильтр | Сигналов | % от Total |
|---|---|---|
| Total (non-FLAT) | 1749 | 100% |
| Trend blocked | 382 | 21.8% (bypass — считаются, не блокируют) |
| LowRatio blocked | 0 | 0% |
| **Position blocked** | **898** | **51.3%** |
| Executed | 851 | 48.7% (BUY=410, SELL=441) |

**Strategy Tester Report:**
| Метрика | Значение |
|---|---|
| Сделок | 851 |
| **PF** | **0.93** |
| Win Rate | 34.55% (294 win / 557 loss) |
| Чистая прибыль | -4461.72 |
| Общая прибыль / убыток | 61836 / -66298 |
| Средняя прибыльная сделка | 210.33 |
| Средняя убыточная сделка | -119.03 |
| **Фактический R:R** | **1:1.77** (210.33 / 119.03) |
| Макс. просадка | 64.08% (7649) |
| Long win rate | **41.22%** |
| Short win rate | **28.34%** |

**Ключевое наблюдение**: Асимметричный R:R работает — средний выигрыш 1.77× среднего проигрыша. Но win rate 34.55% ниже порога безубыточности 36.1% (для R:R=1:1.77). SELL-сигналы значительно хуже: 28.34% vs 41.22% у BUY.

### Вывод
1. **Первопричина расхождения PF=4.50 (OOS) → PF<1 (MT4)**: Python PF считает суммы сырых экскурсий (true_up vs true_dn) без SL/TP, а MT4 использует фиксированный SL=TP=1.6×ATR. Ошибка заглядывания в будущее (Look-ahead bias) в Python забирает идеальный пик прибыли (MFE), тогда как MT4 выходит по закрытию 12-го бара (HoldOverTime), когда цена уже откатилась.
2. **Главный bottleneck — Position blocking (51.3%)**: больше половины сигналов теряются из-за уже открытой позиции. В Python все сигналы независимы. В логе видно: модель генерирует противоположный сигнал (ratio=25.49), но он отклоняется, текущая позиция потом hit SL.
3. **Слабые сигналы доминируют**: большинство ratio≈2.7-3.0 дают R:R≈1:1.0-1:1.1 — асимметрия несущественна. Высокие ratio (7+, R:R=1:2.6+) — меньшинство.
4. **Решение проблемы (Look-ahead bias)**: Чтобы реализовать "пиковый" профит (`true_up`), заложенный в оценку модели, необходим агрессивный **Trailing Stop** для фиксации прибыли на выбросах цены, не дожидаясь отката к 12-му бару.
5. **Следующие шаги**: (a) разрешить переворот позиции при противоположном сигнале; (b) повысить ML_MinRatio для фильтрации слабых сигналов; (c) внедрить математику Trailing Stop'а для удержания MFE.



## [2026-03-21] — ME-12: Отладка ML_TRADE() в MT4 Strategy Tester

### Результаты (XAUUSD H1, 2023-2026, Stp=Prf=3, R:R=1:1)
| Конфигурация | Сделок | PF | Итог |
|---|---|---|---|
| Базовый (Target=1, одновременные позиции) | 602 | 0.77 | -3735 |
| Target=0 | ~500 | — | -3511 |
| + fix одновременных позиций | 424 | — | -2663 |
| + ML_MinRatio=5.0 | **182** | **0.85** | **-1097** |

### Вывод
Модель генерирует сигналы, механика торговли работает корректно. Фундаментальная проблема: win rate ~46% при симметричном R:R=1:1 → PF < 1. Следующий шаг: асимметричный R:R на основе `ratio` (TP = SL × ratio / ML_MinRatio), либо повышение порога ML_MinRatio.

## [2026-03-20] — ME-11: Conformal Prediction — Исследование и Инфраструктура

### Добавлено
- `ML/conformal/calibrate.py`: Split Conformal Prediction калибровка на validation set. Вычисляет nonconformity scores (|y_true − y_pred|) и квантили 90% на 6 Up/Dn таргетах.
- `ML/conformal/conformal_quantiles.json`: Откалиброванные квантили (q_up_12=0.217, q_dn_12=0.231 и т.д.).
- `API/generate_signals.py`: Флаг `--conformal` для фильтрации сигналов по минимальной величине предсказания (magnitude filter).

### Результаты (Test Set OOS, θ=2.665, 12H)
| Метрика | Без CP | С CP |
|---------|--------|------|
| Сделок | 2203 | 2187 (−16) |
| Win Rate | 86.20% | 86.15% |
| **Profit Factor** | **4.5056** | **4.4891** |

### Вывод
**Split Conformal Prediction не добавляет ценности при θ=2.665.** Причина: порог θ уже настолько агрессивен, что пропускает только 23.6% фракталов — все высококачественные сигналы. Глобальный квантиль не может отличить хорошие сигналы от плохих внутри этой группы. Из 16 отфильтрованных сигналов 15 оказались прибыльными. CP будет полезен при более мягком θ, для управления размером позиции или при переходе на CQR (Conformalized Quantile Regression). Инфраструктура готова для будущих экспериментов.

## [2026-03-20] — ME-10: MT4 ↔ ML Integration (File-Based Signals)

### Добавлено
- **`API/generate_signals.py`**: Генерация предрассчитанных ML-сигналов. Прогоняет все три датасета через `transformer_updn_best.pt`, применяет порог θ=2.665 на горизонте 12H, записывает `ml_signals.csv` (58,540 строк, 2004–2026).
- **`MT/MQL4/Include/lib_ML_Signal.mqh`**: Библиотека файлового обмена сигналами. Загружает CSV при первом вызове (lazy init), бинарный поиск по `Time[bar]`, вызов `OPEN_BUY`/`OPEN_SELL`.
- **`MT/MQL4/Include/MAIN.mqh`**: Интеграция `ML_TRADE()` в основной цикл после `COUNT()` — 3 строки изменений.

### Изменено
- Отказ от HTTP/WebRequest (`lib_ML_API.mqh`, `api_server.py`, `SoSimple_ML.mq4`) в пользу файлового обмена. WebRequest не работает в Strategy Tester и ненадёжен под Wine (error 5200).

### Результат
- ✅ Полная цепочка работает: `Python → ml_signals.csv → MQL4 → торговые сигналы в тестере`
- Логи тестера подтверждают: `ML_INIT: Loaded 58540 signals`, `ML Signal=1/−1` с корректными pred_up/pred_dn
- Документация: [docs/MT/ml_signal_integration.md](docs/MT/ml_signal_integration.md)


## [2026-03-19] — ME-9: Out-of-Sample Evaluation & Threshold Analysis

### Добавлено
- Скрипт `ML/evaluate_test.py`: Запуск обученной модели на отложенной (Test) выборке `Nero_test_labeled.csv`.
- `ML/data_loader.py`: Поддержка загрузки и кэширования тестовой выборки (`TEST_FILE`).

### Обновлено
- **`threshold_analysis.py`**: нативная поддержка таргета `regression_updn`. Внедрена логика конвертации выходов `(N, 6)` в торговые сигналы путем оценки отношения `pred_up / pred_dn > θ`. Добавлен параметр `--horizon` (12, 24, 48).

### Зафиксированные Отчеты
- [`ML/reports/threshold_analysis_12H.md`](ML/reports/threshold_analysis_12H.md): Оптимальный горизонт. PF = **2.94**, Precision = 78.3%, Trades = 2502.
- [`ML/reports/threshold_analysis_24H.md`](ML/reports/threshold_analysis_24H.md): Хороший результат. PF = **2.34**, Precision = 73.3%, Trades = 2115.
- [`ML/reports/threshold_analysis_48H.md`](ML/reports/threshold_analysis_48H.md): Удовлетворительный результат. PF = **1.97**, Precision = 69.6%, Trades = 1870.
- [`ML/reports/evaluate_test_H12.md`](ML/reports/evaluate_test_H12.md): Результаты OOS тестирования.

### Прорывной Результат (Out-Of-Sample)
Применение порога `θ=2.665` (выявленного на валидации 12H) к новой отложенной выборке (Test) показало феноменальный результат:
- Сделок: **2203**
- Win Rate (Precision): **86.20%**
- **Profit Factor: 4.50**

Этот результат подтверждает устойчивость выявленных (Transformer) рыночных паттернов на новых данных и открывает дорогу к интеграции модели в торговый эксперт MQL4.

## [2026-03-19] — ME-8: Multi-Task Regression (6 Up/Dn targets)

### Добавлено
- **`data_loader.py`**: `target='updn'` — загрузка 6 таргетов (up_12, dn_12, up_24, dn_24, up_48, dn_48), y shape (N, 6).
- **`train.py`**: `--task regression_updn` — multi-target обучение, HuberLoss на 6 выходов, per-target Pearson r.
- **`utils.py`**: `compute_multitarget_regression_metrics()` — per-target и средние метрики.
- **`compare_architectures.py`**: поддержка `--task regression_updn`.
- **`train.py`**: Multi-target scatter/residual графики (6 subplots).
- **`statistics/statistics.py`**: статистика по Up/Dn таргетам (колонки строки).
- **`statistics/EDA.ipynb`**: Секция 10 — анализ таргетов Up/Dn (гистограммы, scatter, по классам).

### Обновлено
- **`statistics/statistics.py`**: парсинг 18-полевых фракталов (было 11).
- **`statistics/EDA.ipynb`**: парсинг 18-полевых фракталов, `n_features=18`.

### Результат: Transformer regression_updn
- **Per-target Pearson r**: up_12=0.502, dn_12=0.538, up_24=0.406, dn_24=0.421, up_48=0.333, dn_48=0.359
- **Средний Pearson r**: 0.427 | MAE: 0.169 | R²: 0.183

### Profit Factor (ratio = pred_up/pred_dn)
| Горизонт | Порог | PF (val) | PF (test) | Сделок (%) |
|----------|-------|----------|-----------|------------|
| **12H** | 1.5 | 2.54 | **2.53** | 77% |
| **12H** | 2.0 | 3.14 | **3.21** | 47% |
| **12H** | 3.0 | 4.97 | **4.51** | 20% |
| **24H** | 1.5 | 2.22 | **2.21** | 55% |
| **24H** | 2.0 | 2.93 | **2.85** | 24% |
| **48H** | 1.5 | 2.00 | **1.98** | 37% |
| **48H** | 2.0 | 2.85 | **2.66** | 10% |

**Per-target Pearson r (test)**: up_12=0.514, dn_12=0.535, up_24=0.407, dn_24=0.430, up_48=0.322, dn_48=0.364

**Критерий успеха PF > 1.0 при ratio_min=1.5 — выполнен с запасом.**
Val и test PF совпадают (нет переобучения). Прорыв: от PF=0.728 (старый `predict` таргет) до PF=2.0+ (multi-target Up/Dn).

### Compare Architectures (regression_updn)
| Модель | Val Pearson r | MAE | Параметры | Best Epoch | Время (с) |
|--------|---------------|-------|-----------|------------|-----------|
| **transformer** ⭐ | **0.4265** | 0.1691 | 70,630 | 23 | 256 |
| bilstm | 0.4262 | 0.1659 | 152,006 | 6 | 44 |
| hybrid | 0.4099 | 0.1706 | 84,838 | 3 | 28 |
| cnn1d | 0.3751 | 0.1722 | 43,238 | 3 | 30 |

Transformer и BiLSTM практически идентичны. Transformer выбран для Optuna-оптимизации.

### Обновлено
- **`optimize.py`**: поддержка `--task regression_updn`, архитектурные параметры для transformer (d_model, nhead, num_layers, dim_feedforward, dropout).

---

## [2026-03-19] — ME-7: Time Features + Up/Dn Normalization + ATR_ratio Fix

### Добавлено
- **`data_loader.py`**: 3 новые time-фичи на фрактал (вычисляются из fractal_time на лету):
  - `hour_sin` = sin(2π·hour/24) — циклическое кодирование часа суток
  - `hour_cos` = cos(2π·hour/24) — вторая координата цикла
  - `time_pos` = позиция фрактала на временной оси строки [0..1] (newest=1, oldest=0)
- **`normalize.py`**: Joint Piecewise Linear-Log нормализация для Up/Dn (606 значений на строку = 100 фракталов × 6 полей + 6 таргетов).
- **`data_loader.py`**: `N_FRACTAL_FEATURES=20` (17 исходных + 3 time-фичи). Автоинвалидация кэша при изменении shape.
- **`train.py`**: `input_features=N_FRACTAL_FEATURES` передаётся в модели автоматически.

### Исправлено
- **`data_loader.py`**: ATR_ratio теперь вычисляется как `log(fractal_Atr.Fast / Atr.Slow)`.
- **`label_main.py`**: Убрана ATR нормализация (RobustScaler). Atr.Slow сохраняется в CSV сырым — используется только как знаменатель для ATR_ratio в data_loader.

### Удалено
- Артефакт `DATA/Nero_atr_scaler.pkl` больше не создаётся.
- Вызовы `normalize_atr_train()` / `normalize_atr_inference()` убраны из pipeline.

## [2026-03-18] — ME-6: Up/Dn Fixed-Horizon Targets + ATR_ratio
### Причина
Все 4 модели убыточны (PF=0.728). Решение: заменить таргет `predict` шумный (переменный горизонт, зависимость от `direction`) на — direction-independent таргеты с фиксированным горизонтом.
up_12 = max(High[i] - price) за 12 баров от момента формирования фрактала.
- dn_12 = max(price - Low[i]) за 12 баров.
- up_24, dn_24 (float) – аналогично за 24 бара.
- up_48, dn_48 (float) – аналогично за 48 баров. 

### Добавлено
- **`dataset_description.md`**: Добавлены признаки `Up/Dn` (12/24/48 баров) и Atr.Fast для каждого фрактала. 
`up_N` = max(High - P), `dn_N` = max(P - Low) за первые N баров после формирования фрактала. Оба ≥ 0, не зависят от направления.
Строка-ATR переключена на `Atr.Slow` - общий для всей строки.
- **`label_signals.py`**: `parse_fractal()` расширен до 18 полей (поле 17 = `fractal_atr`). Новая функция `label_updn()`: для каждой строки сканирует вперёд до вытеснения fractal0, берёт последние накопленные Up/Dn.
- **`label_main.py`**: шаг `label_updn` добавлен в pipeline после `label_all`.


## [2026-03-16] — ME-5: Custom Trading Loss (AsymmetricLoss)
### Добавлено
- `ML/losses.py`: Реализован класс `AsymmetricLoss`, позволяющий задавать разные штрафы за перепрогноз (over-prediction, FP) и недопрогноз (under-prediction, FN).
- `ML/train.py`: Добавлена поддержка `--regression_loss asymmetric` с параметрами `--asym_over_penalty` и `--asym_under_penalty`.
- `ML/optimize.py`: Добавлена поддержка оптимизации асимметричного штрафа (`asym_under_penalty`) через Optuna.
- **Логика**: По умолчанию штраф за "пропуск" тренда (under-prediction) в 10 раз выше, чем за "ложный сигнал" (over-prediction), чтобы заставить модель не бояться предсказывать крупные движения в хвосте распределения.
- **Результат (Threshold Analysis)**: Profit Factor вырос с **0.61** (baseline) до **0.728**. Асимметричный лосс и более глубокая архитектура (3 слоя BiLSTM) дали прирост ~19%, но модель все еще убыточна (PF < 1.0).
- **Вывод**: Изменение функции потерь помогает, но основной лимит — в слабых признаках или шумном таргете.
- **Инфраструктура**: Скрипт `ML/threshold_analysis.py` теперь автоматически адаптируется под архитектуру чекпоинта (число слоев и т.д.).

## [2026-03-12] — ME-3: Feature Engineering (Динамические признаки)
### Добавлено
- `ML/feature_engineering.py`: динамические признаки (price momentum), относительные фичи (нормировка front/back/impulse и momentum на ATR) и скользящие средние (MA3).
- Интеграция в пайплайн загрузки `ML/data_loader.py` — теперь сеть получает 16 признаков вместо сырых 11, что должно усилить сигнал тренда.

### Результат оценки (Threshold Analysis)
- Profit Factor остался **ниже 1.0 (0.5908)**. Ни подбор гиперпараметров (ME-1), ни усечение истории (ME-2), ни новые динамические признаки (ME-3) не смогли вытянуть прибыльную модель регрессии. 

## [2026-03-12] — ME-2: Ablation Study (Влияние длины истории)
### Исследование
- Создан скрипт `ML/ablation_study.py` для оценки влияния длины подаваемой истории фракталов (`seq_len`).
- **Критический вывод**: Усечение `seq_len` со 100 до 20 последних фракталов сохраняет и даже чуть улучшает качество модели (Pearson r = 0.328 vs 0.324), при этом сокращая время обучения в 2.5 раза (18 с вместо 46 с). Огромный пласт "старых" данных признан шумом.
- `seq_len=20` установлена как дефолтная длина признакового окна для будущих экспериментов.

## [2026-03-12] — Оптимизация regression завершена!
HPO для BiLSTM успешно отработал, найдя параметры (lr=0.004, batch=256, dropout=0.36), которые позволили поднять best_value (Pearson r) с 0.323 до 0.342
"сырые" данные фракталов (цены + базовый ATR) исчерпали свой потенциал
✅ Лучшие параметры сохранены: [optuna_best_params_bilstm_regression.json](ML/reports/optuna_best_params_bilstm_regression.json)
✅ История trials сохранена: [optuna_study_bilstm_regression_20260312_003636.json](ML/reports/optuna_study_bilstm_regression_20260312_003636.json)


## [2026-03-11] — ME-1: Подготовка к Optuna HPO для регрессии
### Изменено
- `ML/train.py`: функция `train_model` теперь принимает `model_kwargs` и прокидывает их в `get_model()` для инициализации параметров архитектуры. Добавлено сохранение этих параметров в логи `experiments_log.csv`.
- `ML/optimize.py`: добавлена поддержка функции генерации гиперпараметров архитектуры `hidden_size`, `num_layers`, `dropout` для `bilstm`.

## [2026-03-11] — QW-4: Threshold Analysis (Regression → Trading Signal)
### Добавлено
- Новый скрипт `ML/threshold_analysis.py`: поиск оптимального порога θ для конвертации регрессионных предсказаний `|predict|` в торговые сигналы
- Генерация Precision-Recall curve, Metrics vs θ, Profit Factor vs θ графиков
- Markdown-отчёт `ML/reports/threshold_analysis.md`

### Результат
- При Pearson r ≈ 0.32 (BiLSTM): лучший PF = 0.618, precision = 23%, recall = 20%
- **Вывод**: сигнал слишком слаб для торговли → необходим HPO (ME-1) или feature engineering (ME-3)

## [2026-03-11] — Обеспечение 100% воспроизводимости экспериментов
### Добавлено
- В `experiments_log.csv` теперь логируются все гиперпараметры, влияющие на результат: `seed`, `weight_decay`, `huber_delta`, `scheduler_patience`, `scheduler_factor`, `focal_gamma`, `use_weighted_sampler`, `num_parameters`.
- Автоматический сбор текущего `git_commit` при каждом запуске для точной привязки чекпоинта к кодовой базе.

### Тесты на воспроизводимость очень позитивные!

Скрипт ML/reproducibility_tests.py успешно отработал и сгенерировал отчёт ML/reports/reproducibility_report.md. Вот главные выводы:
Тест 1 Выполнили задачу полного переобучения с фиксированным seed и исправленными метриками. Вот честные результаты (до настройки гиперпараметров):

🏆 Лучшая модель: BiLSTM

Pearson r: 0.3236 (Корреляция с реальным predict = ~32.3%)
MAE: 0.1083
Время обучения: 408 секунд
Результаты из аудита (Pearson r = 0.555) оказались невоспроизводимым артефактом (возможно, из-за случайного seed, отсутствия dropout или "удачного" локального минимума в тот конкретный запуск). Текущая честная (reproducible) корреляция — 0.32. 
Тест 2 (Детерминизм): Три запуска с seed=42 выдали абсолютно идентичный результат вплоть до 5-го знака: Pearson r = 0.32255. Это подтверждает, что при фиксированном seed проект строго детерминирован.
Тест 3 (Чувствительность к seed): Пять запусков с разными сидами (42, 123, 456, 789, 1000) показали средний Pearson r = 0.32072 со стандартным отклонением 0.00228. Это означает, что модель очень стабильна: изменение seed'а почти не влияет на результат (отклонение крошечное, значительно меньше допустимых 0.03). Результат ~0.32 — это истинная характеристика модели, а не случайность рандома.
Хэши данных (Тест 4): Сгенерированы и зафиксированы MD5 хэши датасетов для будущих сверок.

## [2026-03-11] — Ускорение загрузки данных
### Добавлено
- Кэширование распарсенных тензоров в `.npy` файлы в `data_loader.py` для значительного ускорения повторных запусков обучения.

## [2026-03-10] — Ключевые находки аудита проекта ([opus-project_audit_and_plan.md](docs/archive/03.10_audit_answers/opus-project_audit_and_plan.md))
- **DirAcc = 97.5% — НЕ data leakage.** Это артефакт кода. В [`ML/data_loader.py`](ML/data_loader.py) (строка 270) регрессионный таргет берётся как `np.abs(df_train[target])` — все значения ≥ 0. Метрика `directional_accuracy` в [`ML/utils.py`](ML/utils.py) (строка 145) вычисляет `sign(y_true) == sign(y_pred)`. Поскольку y_true ≥ 0 и модель обучена предсказывать неотрицательные значения, DirAcc тривиально высок.
- **`direction` как feature**: `fractal[0].direction` ∈ {-1, 1} напрямую коррелирует со знаком `predict` (по определению: `predict = -back * direction`). Для задачи классификации `signal` это может быть мягкая форма leakage — direction определяет **направление** сигнала, хотя не его **наличие**. Для регрессии `|predict|` проблемы нет, т.к. знак удалён.
- Классификация уперлась в потолок данных — 5 архитектур (RF + 4 NN) дают F1_minority 0.35-0.39, разброс в пределах стат. ошибки. ~1000 сигнальных примеров недостаточно для deep learning.
- Регрессия показывает потенциал — Pearson r=0.56, R²=0.30. Все 43K примеров работают.
- **Для классификации**: ~1000 примеров Sell и ~1100 Buy в train — это порог выживания для deep learning. При 11 features × 100 timesteps даже простой BiLSTM имеет 147K параметров. Ratio параметров к сигнальным примерам ≈ 67:1 — катастрофический оверфиттинг неизбежен.
- **Дисбаланс 95:2.5:2.5 — экстремальный.**
- **Для регрессии**: все 43 593 примера вносят вклад (регрессия на `|predict|`). Ratio параметров к примерам ≈ 3.4:1 — приемлемо.
- **Validation**: 232 Sell + 244 Buy = 476 примеров для оценки. Стандартная ошибка F1 при таком размере: ±0.03-0.05. Разница между моделями (0.017 F1) **статистически незначима**.


## [2026-02-27] — Оптимизация под торговые сигналы: метрики и балансировка
### Добавлено
- Новые метрики для оценки качества сигнальных классов: `signal_precision`, `signal_recall`, `f1_minority`
- Поддержка WeightedRandomSampler для балансировки train-батчей

### Изменено
- Early stopping теперь может использовать Precision сигнальных классов вместо Macro F1

### Примечание
- WeightedRandomSampler используется только для train; val/test сохраняют реальное распределение
- Для `metric_mode=signal_precision` применяется штраф, если recall < min_signal_recall

### Исправлено
- Ошибка в WeightedRandomSampler: преобразование меток {-1, 0, 1} → {0, 1, 2} через `y_train + 1` вместо list comprehension

## [2026-02-27] — Критический анализ: ловушка дисбаланса классов
### Проблема
- **Macro F1 = 0.57 — обманчивая метрика**: высокое значение достигается за счёт F1(0)=0.95 (neutral, 95% данных)
- **Торгово-значимые классы (-1 и 1) имеют F1 ≈ 0.35** — катастрофически низкое качество
- **Precision сигнальных классов**: 0.25–0.30 → 70-75% ложных торговых сигналов
- Веса Focal Loss [0.445, 0.11, 0.445] недостаточны для компенсации дисбаланса 5%/95%

### Вывод
- Модели с "хорошим" Macro F1 фактически непригодны для торговли
- Требуется смена целевой метрики (F1 minority, MCC) и балансировка батчей (WeightedRandomSampler)

## [2026-02-27] — Сравнение архитектур нейросетей (регрессия)
### Результаты
- **Bi-LSTM**: лучший Pearson r = 0.3236, 147K параметров
- **Hybrid CNN+LSTM**: Pearson r = 0.2825, 83K параметров
- **1D-CNN**: Pearson r = 0.2518, 42K параметров (самая быстрая)
- **Transformer**: Pearson r = 0.1143, 70K параметров

## [2026-02-25] — Оптимизация гиперпараметров (Optuna)
### Добавлено
- Автоматический подбор гиперпараметров с помощью Optuna
- Поддержка pruning (досрочная остановка неперспективных trials)
- Оптимизация для classification (macro F1) и regression (pearson_r)

## [2026-02-23] — Поддержка обучения в режиме регрессии (predict target)
### Добавлено
- Поддержка раннего останова по корреляции Пирсона (`pearson_r`)
- HuberLoss (δ=1.0) для робастной функции ошибок при регрессии
- Метрики регрессии: MAE, RMSE, R², pearson_r, DirAcc

## [2026-02-18] — Baseline ML эксперименты
### Добавлено
- 5 baseline-моделей: Dummy, LogReg, RF, XGBoost, LightGBM

## [2026-02-07] — Исправление нормализации predict
### Исправлено
- Обработка знакового `predict` в `normalize.py`
- `predict` теперь корректно нормализуется: модуль → нормализация → восстановление знака
