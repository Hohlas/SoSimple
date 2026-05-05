# Context Handoff

Короткий baton для следующего агента. Историю этапов читать в `docs/reports/`, краткую хронологию - в `CHANGELOG.md`, синтез - в `wiki/research/`.

## Current Stage

Этап `telemetry_frequency_demo_launch` дополнен 2026-04-28 архитектурным снимком MQL runtime, 2026-04-29 online inference contract hardening, 2026-05-05 live-safe ML audit и 2026-05-05 `entry_path_v1` live-safe retrain.

Канонические отчёты:
- [`docs/reports/2026-04-27-telemetry-frequency-demo-launch.md`](docs/reports/2026-04-27-telemetry-frequency-demo-launch.md)
- [`docs/reports/2026-04-28-mql-runtime-architecture-snapshot.md`](docs/reports/2026-04-28-mql-runtime-architecture-snapshot.md)
- [`docs/reports/2026-05-05-live-safe-ml-audit.md`](docs/reports/2026-05-05-live-safe-ml-audit.md)
- [`docs/reports/2026-05-05-entry-path-v1-live-safe-retrain.md`](docs/reports/2026-05-05-entry-path-v1-live-safe-retrain.md)

Что было зафиксировано 2026-04-27:
- high-frequency diagnostic export `telemetry_frequency_v1_highfreq500`;
- `ml_signals.csv` atomic export/copy и runtime reload в MT4;
- multi-position diagnostic режим в существующей `EXPERT::ML_TRADE()`;
- structured MQL logs `MLP BUY/SELL/CLOSE/SKIP`;
- broker-side SL/TP закрытия логируются как `MLP CLOSE ... source=broker_history`;
- daily reconciliation CLI `ML/telemetry_daily_reconciliation.py`;
- документация online pipeline и `#.csv` contract;
- watcher переведён в наблюдаемый `tmux`-режим с heartbeat в stdout;
- `header-only` `Nero.csv` считается штатным ожиданием первого бара.

Что добавлено 2026-04-28:
- MQL expert при старте прогревает `PIC()` по истории через `RECOUNT_HISTORY()`;
- `POC_SIMPLE()` теперь вызывается внутри `PIC()`, чтобы historical warmup и online bar-by-bar проход совпадали;
- `Nero.csv` локально пересобирается по истории и дописывается при новых уровнях;
- watcher использует `runtime_input_snapshot.csv` из хвоста `Nero.csv` (`--max-runtime-rows`, default `12000`), а не весь файл в RAM;
- full-vs-12000 проверка на хвосте дала `signal_mismatch_rows=0`, `pred_*` отличаются только на уровне float-шума (`<=3.37e-7`);
- найдено текущее расхождение online pipeline: live `Nero.csv` содержит `signal=0` и `predict=0` во всех строках;
- причина: offline `predict` формируется через future-derived разметку (`predict = -back * direction`) и не может честно вычисляться в live-момент;
- diagnostic online-export переведён на текущий доступный источник направления: `fractal0.direction` с обратным знаком (`-1 -> BUY`, `1 -> SELL`);
- локальная проверка после изменения дала `nonzero_rows=500`, `buy_rows=444`, `sell_rows=56`, `duplicate_time_rows=0`, `same_time_opposite_signal_groups=0`.

Что добавлено 2026-04-29:
- watcher строит raw `runtime_input_snapshot.csv`, затем
  `runtime_input_preprocessed.csv` через sorting + validation +
  `normalize_rowwise(verbose=False)`;
- `API.api_server` использует тот же `preprocess_online_frame()`, а не прямой
  `normalize_rowwise()`;
- найден критичный ML-contract разрыв: legacy `original_baseline` обучался и
  проверялся с future-derived row features (`predict`, `ret_*`, `fav_*`,
  `adv_*`) как входом модели;
- `API.telemetry_signal_watcher` теперь блокирует
  `original_contour/original_baseline` online по умолчанию через
  `OnlineInferenceContractError`;
- `--allow-unsafe-future-features` оставлен только для старой механической
  диагностики связи MT4 -> Python -> CSV -> MT4.

Главный вывод:
- механическая цепочка diagnostic-контурa была доведена до наблюдаемого вида,
  но legacy ML-контракт `original_baseline` больше не считается online-ready;
- свежий MT4 tester proof за 2025 дал `critical_mismatch_count=0`;
- `missing_close_count=1` объясняется открытой позицией на конце периода;
- прибыльный tester result не считать production-доказательством качества стратегии.
- online diagnostic больше не зависит от future-derived `predict` для
  направления, но сам checkpoint `original_baseline` требует future-derived
  row features и поэтому заблокирован для ML-корректной online-проверки;
- перед production-переходом нужен live-safe retrain: один и тот же набор
  признаков в training/test и online, без future-derived входов.
- live-safe ML audit зафиксировал verdict:
  `quality`, `frequency`, `original_plus_path`, `entry_path_v1`,
  `entry_path_v1_quantile` = `FAIL`.
- legacy export replay выполнен по старым prediction/rule входам:
  старый путь генерации сигналов воспроизводится для всех пяти систем, но
  помечен `diagnostic_only=true` и не доказывает online-valid качество.
- source audit закрыл `ret_dir_atr_lag1` как future-derived:
  это `ret_6_dir_atr.shift(1)`, а `ret_6_dir_atr` строится по будущим барам
  в `label_entry_path_targets()`.
- audit evidence лежит в `ML/reports/live_safe_ml_audit/`.
- live-safe retrain `entry_path_v1_live_safe` удалил `ret_dir_atr_lag1` и дал:
  validation `ret_pearson_r=0.2681`, frozen test PF `3.6567`,
  sequential test `25` trades, PF `2.3419`, win rate `68.00%`.
- вывод: прибыльность не сохранилась один в один, но система не развалилась и
  остаётся кандидатом для multi-seed и MT4 parity.

## Next Step

1. Повторить `entry_path_v1_live_safe` на нескольких seed, чтобы проверить
   устойчивость результата после удаления `ret_dir_atr_lag1`.
2. Выполнить MT4 parity для `entry_path_v1_live_safe_test_signals.csv`.
3. После нового baseline повторно оценить `entry_path_v1_quantile`, потому что
   production rule зависит от baseline score.
4. Только после PASS по feature contract переходить к MT4 parity,
   forward validation и online dry-run.

## Read First

1. [`AGENTS.md`](AGENTS.md) - правила агента и карта источников.
2. [`docs/ML/ml_leakage_preflight_checklist.md`](docs/ML/ml_leakage_preflight_checklist.md) - обязательный leakage/preflight gate для всех ML test/MT4/online выводов.
3. [`docs/reports/2026-05-05-live-safe-ml-audit.md`](docs/reports/2026-05-05-live-safe-ml-audit.md) - текущий verdict по прибыльным ML-системам.
4. [`docs/reports/2026-05-05-entry-path-v1-live-safe-retrain.md`](docs/reports/2026-05-05-entry-path-v1-live-safe-retrain.md) - первый retrain без `ret_dir_atr_lag1`.
5. [`ML/reports/live_safe_ml_audit/`](ML/reports/live_safe_ml_audit/) - generated audit evidence.
6. [`docs/reports/2026-04-27-telemetry-frequency-demo-launch.md`](docs/reports/2026-04-27-telemetry-frequency-demo-launch.md) - итог online telemetry этапа.
7. [`docs/reports/2026-04-28-mql-runtime-architecture-snapshot.md`](docs/reports/2026-04-28-mql-runtime-architecture-snapshot.md) - текущая MQL/runtime архитектура и открытый вопрос `signal/predict`.
8. [`docs/MT/trading_strategy.md`](docs/MT/trading_strategy.md) - online pipeline, `#.csv`, MQL logging.
9. [`docs/MT/ml_signal_integration.md`](docs/MT/ml_signal_integration.md) - MT4 `ml_signals.csv` contract.
10. [`docs/ML/telemetry_daily_reconciliation.py.md`](docs/ML/telemetry_daily_reconciliation.py.md) - daily reconciliation.

## Open Risks

- Legacy `original_baseline` нельзя считать online-ready: historical test был
  загрязнён future-derived входными признаками, а live `Nero.csv` этих признаков
  не имеет.
- `entry_path_v1` и `entry_path_v1_quantile` теперь `FAIL`, не `UNKNOWN`.
  Причина: `ret_dir_atr_lag1` доказан как future-derived, а quantile зависит
  от baseline score.
- `entry_path_v1_live_safe` пока проверен только одним seed и ещё не прошёл MT4
  parity; это кандидат, не production approval.
- Diagnostic online demo больше не требует ненулевого `predict/signal` в live `Nero.csv`, но unsafe override проверяет только механику цепочки.
- Python watcher/exporter должен быть запущен постоянно или заменён сервисом с тем же atomic write contract; текущий штатный режим - отдельное окно `tmux`.
- Runtime CSV-файлы частично игнорируются git, поэтому их нужно синхронизировать отдельно.
- `knowledge-rag` reindex в конце этапа ранее падал с `Transport closed`; RAG может отставать от части последних правок.

## Latest Reports

- [`docs/reports/2026-04-27-telemetry-frequency-demo-launch.md`](docs/reports/2026-04-27-telemetry-frequency-demo-launch.md)
- [`docs/reports/2026-04-28-mql-runtime-architecture-snapshot.md`](docs/reports/2026-04-28-mql-runtime-architecture-snapshot.md)
- [`docs/reports/2026-05-05-live-safe-ml-audit.md`](docs/reports/2026-05-05-live-safe-ml-audit.md)
- [`docs/reports/2026-05-05-entry-path-v1-live-safe-retrain.md`](docs/reports/2026-05-05-entry-path-v1-live-safe-retrain.md)
- [`docs/reports/2026-04-24-system-correlation-and-portfolio-check.md`](docs/reports/2026-04-24-system-correlation-and-portfolio-check.md)
- [`docs/reports/2026-04-24-entry-path-cross-instrument-robustness.md`](docs/reports/2026-04-24-entry-path-cross-instrument-robustness.md)
