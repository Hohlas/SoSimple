# Context Handoff

## Current Stage
Outcome-aligned retraining по плану `2026-04-07-outcome-aligned-retraining.md` завершён, но winner не найден. Построены три новых family (`trade_outcome_cls`, `trade_pnl_reg`, `signal_archetype_cls`), все они добавлены в preprocessing/training/evaluation stack и переобучены на signal-only rows после отладки objective mismatch. Validation-first benchmark завершён честно: ни одно семейство не прошло общий `trade floor + yearly stability` filter, поэтому `frozen_outcome_target.json` не создан и `test` не запускался.

## Last Completed Stage
Outcome-aligned retraining: validation-first verdict = no winner (2026-04-08).

## Next Step
Следующий шаг для outcome-aligned track не в запуске `test`, а в пересборке самих таргетов ближе к реальной торговой механике.

1. Не запускать `test` для outcome-aligned family, пока на validation не появится хотя бы один winner, прошедший shared filters.
2. Следующую итерацию строить вокруг execution-aware label definition:
   - вход на следующем баре;
   - только одна открытая позиция;
   - явная логика выхода;
   - при необходимости `HoldOverTime` / `PosBlock` как часть target construction.
3. Проверить, не нужно ли отказаться от `close[t+12]` как основного outcome proxy в пользу trade simulation, которая ближе к MT4 decision loop.
4. `regression_updn`, `triple_barrier` и новый outcome-aligned track держать раздельно: это разные hypotheses и разные критерии успеха.

Roadmap doc: `docs/superpowers/roadmap.md`

## Read First
- `AGENTS.md`
- `docs/superpowers/roadmap.md`
- `docs/reports/2026-04-08-outcome-aligned-retraining.md`
- `ML/reports/outcome_target_validation_benchmark.md`
- `docs/reports/2026-04-04-signal-path-atlas-readout.md`
- `docs/reports/2026-04-04-archetype-filter-bridge.md`
- `docs/reports/2026-04-04-signal-quality-filter.md`

## Open Risks
- Текущие outcome labels всё ещё не повторяют реальный MT4 execution loop и завязаны на `close-to-close` proxy за 12 баров.
- `trade_outcome_h12` и `archetype_target` на текущих split-файлах почти схлопываются в одну бинарную задачу.
- После signal-only retraining ни одно семейство не прошло общий validation filter; риск в том, что новые targets просто описывают “плохой universe”, а не отбор хороших сигналов.
- Любой переход к `test` без нового validation winner-а будет нарушением validation-first discipline.

## Latest Report
`docs/reports/2026-04-08-outcome-aligned-retraining.md`

## Active Roadmap
`docs/superpowers/roadmap.md`
