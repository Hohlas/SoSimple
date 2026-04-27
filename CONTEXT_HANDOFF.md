# Context Handoff

Короткий baton для следующего агента. Историю этапов читать в `docs/reports/`, краткую хронологию — в `CHANGELOG.md`, синтез — в `wiki/research/`.

## Current Stage

Этап `system_correlation_and_portfolio_check` завершён 2026-04-24.

Канонический отчёт: [`docs/reports/2026-04-24-system-correlation-and-portfolio-check.md`](docs/reports/2026-04-24-system-correlation-and-portfolio-check.md).

Что зафиксировано:
- добавлен `ML/benchmark_system_correlation.py`;
- добавлены тесты `tests/test_benchmark_system_correlation.py`;
- добавлена документация `docs/ML/benchmark_system_correlation.py.md`;
- создан manifest `ML/reports/system_correlation_portfolio/manifest_xauusd_systems.json`;
- собраны pairwise benchmark-артефакты в `ML/reports/system_correlation_portfolio/xauusd_system_correlation/`.

Главный вывод:
- `frequency` и `original_plus_path` не считать независимыми portfolio sleeves;
- `entry_path_v1_quantile` считать новым risk-profile относительно `quality` и `original_plus_path`;
- `entry_path_v1` не ставить рядом с `entry_path_v1_quantile` как отдельный слой;
- первый portfolio-layer проверять как `quality + entry_path_v1_quantile`.

## Next Step

По [`docs/superpowers/roadmap.md`](docs/superpowers/roadmap.md):

1. Собрать bounded portfolio-layer benchmark для `quality + entry_path_v1_quantile`.
2. Отдельно сравнить третий sleeve: `frequency` vs `original_plus_path`.
3. Измерить composite equity / drawdown / concentration без добавления новых trading modes.

## Read First

1. [`AGENTS.md`](AGENTS.md) — правила агента и карта источников.
2. [`docs/README.md`](docs/README.md) — карта и границы документации.
3. [`docs/superpowers/roadmap.md`](docs/superpowers/roadmap.md) — активный порядок работ.
4. [`docs/reports/2026-04-24-system-correlation-and-portfolio-check.md`](docs/reports/2026-04-24-system-correlation-and-portfolio-check.md) — последний завершённый этап.
5. [`wiki/index.md`](wiki/index.md) — синтез research-линий.

## Open Risks

- Portfolio verdict пока подтверждён только на `XAUUSD`.
- `entry_path_v1_quantile` сильнее baseline, но остаётся низкочастотным режимом.
- Cross-instrument transfer частичный: не переносить выводы на все инструменты без отдельного benchmark.
- Любой новый TB/label consumer должен явно различать `1.0 / 0.5 / 0.0` или документированно бинаризовать timeout.

## Latest Reports

- [`docs/reports/2026-04-24-system-correlation-and-portfolio-check.md`](docs/reports/2026-04-24-system-correlation-and-portfolio-check.md)
- [`docs/reports/2026-04-24-entry-path-cross-instrument-robustness.md`](docs/reports/2026-04-24-entry-path-cross-instrument-robustness.md)
- [`docs/reports/2026-04-24-cross-instrument-robustness-check.md`](docs/reports/2026-04-24-cross-instrument-robustness-check.md)
