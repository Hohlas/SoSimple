# Context Handoff

Короткий baton для следующего агента. Историю этапов читать в `docs/reports/`, краткую хронологию - в `CHANGELOG.md`, синтез - в `wiki/research/`.

## Current Stage

Этап `telemetry_frequency_demo_launch` дополнен 2026-04-28 архитектурным снимком MQL runtime и online diagnostic direction update.

Канонические отчёты:
- [`docs/reports/2026-04-27-telemetry-frequency-demo-launch.md`](docs/reports/2026-04-27-telemetry-frequency-demo-launch.md)
- [`docs/reports/2026-04-28-mql-runtime-architecture-snapshot.md`](docs/reports/2026-04-28-mql-runtime-architecture-snapshot.md)

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

Главный вывод:
- diagnostic-контур готов к online demo launch / наблюдению на удалённом сервере;
- свежий MT4 tester proof за 2025 дал `critical_mismatch_count=0`;
- `missing_close_count=1` объясняется открытой позицией на конце периода;
- прибыльный tester result не считать production-доказательством качества стратегии.
- online diagnostic больше не зависит от future-derived `predict`;
- перед production-переходом нужно отдельно проверить, соответствует ли `fractal0.direction` финальной обучающей постановке, а не только задаче набора telemetry-событий.

## Next Step

1. Оставить M5-наблюдение примерно на 10 часов без изменения diagnostic-сигнала.
2. Собрать статистику runtime-строк:
   - `MLP_WAIT: file changed after ...`;
   - `MLP_WAIT: timeout ...`;
   - `MLP NO_SIGNAL`;
   - `MLP ZERO_SIGNAL`;
   - `MLP BUY` / `MLP SELL`;
   - `MLP CLOSE` / `MLP SKIP`.
3. По статистике решить, достаточно ли текущей частоты и баланса сигналов для diagnostic demo.
4. Затем вернуть профиль на H1/server либо продолжить M5 online-наблюдение на удалённом сервере.

## Read First

1. [`AGENTS.md`](AGENTS.md) - правила агента и карта источников.
2. [`docs/reports/2026-04-27-telemetry-frequency-demo-launch.md`](docs/reports/2026-04-27-telemetry-frequency-demo-launch.md) - итог текущего этапа.
3. [`docs/reports/2026-04-28-mql-runtime-architecture-snapshot.md`](docs/reports/2026-04-28-mql-runtime-architecture-snapshot.md) - текущая MQL/runtime архитектура и открытый вопрос `signal/predict`.
4. [`docs/MT/trading_strategy.md`](docs/MT/trading_strategy.md) - online pipeline, `#.csv`, MQL logging.
5. [`docs/MT/ml_signal_integration.md`](docs/MT/ml_signal_integration.md) - MT4 `ml_signals.csv` contract.
6. [`docs/ML/telemetry_daily_reconciliation.py.md`](docs/ML/telemetry_daily_reconciliation.py.md) - daily reconciliation.

## Open Risks

- Diagnostic online demo больше не требует ненулевого `predict/signal` в live `Nero.csv`, но зависит от корректного парсинга `fractal0.direction`.
- Python watcher/exporter должен быть запущен постоянно или заменён сервисом с тем же atomic write contract; текущий штатный режим - отдельное окно `tmux`.
- Runtime CSV-файлы частично игнорируются git, поэтому их нужно синхронизировать отдельно.
- `knowledge-rag` reindex в конце этапа ранее падал с `Transport closed`; RAG может отставать от части последних правок.

## Latest Reports

- [`docs/reports/2026-04-27-telemetry-frequency-demo-launch.md`](docs/reports/2026-04-27-telemetry-frequency-demo-launch.md)
- [`docs/reports/2026-04-28-mql-runtime-architecture-snapshot.md`](docs/reports/2026-04-28-mql-runtime-architecture-snapshot.md)
- [`docs/reports/2026-04-24-system-correlation-and-portfolio-check.md`](docs/reports/2026-04-24-system-correlation-and-portfolio-check.md)
- [`docs/reports/2026-04-24-entry-path-cross-instrument-robustness.md`](docs/reports/2026-04-24-entry-path-cross-instrument-robustness.md)
