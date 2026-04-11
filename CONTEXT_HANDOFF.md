# Context Handoff

## Current Stage
Этап `entry_path_v1_quantile_robustness` завершён.

Что зафиксировано:

- `entry_path_v1_quantile` прошёл полный multi-seed robustness-pass на `seed = 7, 17, 42, 77, 123`;
- во всех пяти seed winner один и тот же: `lb_gt_m` поверх frozen baseline `A @ 7.5%`;
- финальный aggregate verdict: `go_mt4`;
- выпущены полные robustness-артефакты:
  - `ML/checkpoints/entry_path_v1_quantile_robustness/seed_*/`
  - `ML/reports/entry_path_v1_quantile_robustness/seed_*/`
  - `ML/reports/entry_path_v1_quantile_robustness/aggregate_5seed/{runs,yearly,rolling,summary}.*`
- реализован secondary tooling для `triple_barrier`:
  - `ML/triple_barrier_mt4_execution.py`
  - `ML/benchmark_triple_barrier_mt4_execution.py`
  но реальные TB benchmark-артефакты ещё не выпущены.

## Last Completed Stage
Entry Path v1 Quantile Robustness (2026-04-11).

## Next Step
1. Выполнить `MT4 parity-check` именно для `entry_path_v1_quantile` и frozen winner `lb_gt_m`.
2. Сверить MT4-результат с Python robustness verdict `go_mt4`.
3. После этого решить, становится ли quantile-layer основным execution mode.
4. Отдельным secondary stage прогнать `ML/benchmark_triple_barrier_mt4_execution.py` на `validation/test`.

Roadmap doc: `docs/superpowers/roadmap.md`

## Read First
- `AGENTS.md`
- `docs/reports/2026-04-11-entry-path-v1-quantile-robustness.md`
- `docs/reports/2026-04-10-entry-path-v1-quantile.md`
- `docs/reports/2026-04-09-entry-path-trade-filter.md`
- `ML/reports/entry_path_v1_quantile_robustness/aggregate_5seed/summary.json`
- `ML/reports/entry_path_v1_quantile_robustness/aggregate_5seed/runs.csv`

## Open Risks
- MT4 parity-check для quantile-layer ещё не проводился.
- Линия остаётся low-frequency режимом: support устойчивый, но число сделок ниже, чем у базового `A @ 7.5%`.
- `triple_barrier_mt4_execution` пока подтверждён только на уровне кода и тестов, без реального benchmark verdict.

## Latest Report
`docs/reports/2026-04-11-entry-path-v1-quantile-robustness.md`

## Active Roadmap
`docs/superpowers/roadmap.md`
