# Context Handoff

Короткий baton для следующего агента. Историю этапов читать в `docs/reports/`, краткую хронологию - в `CHANGELOG.md`, синтез - в `wiki/research/`.

## Current Stage

Этап `telemetry_frequency_demo_launch` завершён 2026-04-27.

Канонический отчёт: [`docs/reports/2026-04-27-telemetry-frequency-demo-launch.md`](docs/reports/2026-04-27-telemetry-frequency-demo-launch.md).

Что зафиксировано:
- high-frequency diagnostic export `telemetry_frequency_v1_highfreq500`;
- `ml_signals.csv` atomic export/copy и runtime reload в MT4;
- multi-position diagnostic режим в существующей `EXPERT::ML_TRADE()`;
- structured MQL logs `MLP BUY/SELL/CLOSE/SKIP`;
- broker-side SL/TP закрытия логируются как `MLP CLOSE ... source=broker_history`;
- daily reconciliation CLI `ML/telemetry_daily_reconciliation.py`;
- документация online pipeline и `#.csv` contract.

Главный вывод:
- diagnostic-контур готов к online demo launch на удалённом сервере;
- свежий MT4 tester proof за 2025 дал `critical_mismatch_count=0`;
- `missing_close_count=1` объясняется открытой позицией на конце периода;
- прибыльный tester result не считать production-доказательством качества стратегии.

## Next Step

1. Слить ветку `telemetry-frequency-demo-launch` в `main`.
2. Синхронизировать удалённый сервер через git.
3. Отдельно скопировать ignored runtime files:
   - `MT/MQL4/Files/ml_signals.csv`
   - `MT/tester/files/#.csv`
   - `MT/tester/files/ml_signals.csv`
4. На сервере перекомпилировать expert и запустить online demo на `XAUUSD,H1`.
5. Ежедневно запускать `ML.telemetry_daily_reconciliation` по свежему MT4 log.

## Read First

1. [`AGENTS.md`](AGENTS.md) - правила агента и карта источников.
2. [`docs/reports/2026-04-27-telemetry-frequency-demo-launch.md`](docs/reports/2026-04-27-telemetry-frequency-demo-launch.md) - итог текущего этапа.
3. [`docs/MT/trading_strategy.md`](docs/MT/trading_strategy.md) - online pipeline, `#.csv`, MQL logging.
4. [`docs/MT/ml_signal_integration.md`](docs/MT/ml_signal_integration.md) - MT4 `ml_signals.csv` contract.
5. [`docs/ML/telemetry_daily_reconciliation.py.md`](docs/ML/telemetry_daily_reconciliation.py.md) - daily reconciliation.

## Open Risks

- Online demo ещё не запущен; online/test соответствие нужно подтвердить на сервере.
- Python watcher/exporter должен быть запущен постоянно или заменён сервисом с тем же atomic write contract.
- Runtime CSV-файлы частично игнорируются git, поэтому их нужно синхронизировать отдельно.
- `knowledge-rag` reindex в конце этапа падал с `Transport closed`; RAG может отставать от последних правок.

## Latest Reports

- [`docs/reports/2026-04-27-telemetry-frequency-demo-launch.md`](docs/reports/2026-04-27-telemetry-frequency-demo-launch.md)
- [`docs/reports/2026-04-24-system-correlation-and-portfolio-check.md`](docs/reports/2026-04-24-system-correlation-and-portfolio-check.md)
- [`docs/reports/2026-04-24-entry-path-cross-instrument-robustness.md`](docs/reports/2026-04-24-entry-path-cross-instrument-robustness.md)
