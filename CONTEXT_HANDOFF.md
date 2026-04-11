# Context Handoff

## Current Stage
Этап `entry_path_v1_quantile_mt4_parity` завершён.

Что зафиксировано:

- `entry_path_v1_quantile` уже прошёл оба ключевых этапа:
  - multi-seed robustness-pass на `seed = 7, 17, 42, 77, 123`;
  - MT4 parity-check для frozen winner `lb_gt_m`;
- во всех пяти seed winner один и тот же: `lb_gt_m` поверх frozen baseline `A @ 7.5%`;
- финальный robustness verdict остаётся `go_mt4`, и теперь он подтверждён реальным MT4 run;
- для quantile-layer реализован канонический exporter:
  - `API/export_entry_path_v1_quantile_signals.py`
  - frozen `seed-dir -> time;signal` без re-fit
  - дедупликация `time` совпадает с реальной MQL-семантикой `keep='last'`
- выпущен trade-level reconciliation artifact:
  - `ML/reports/entry_path_v1_quantile_mt4_reconciliation.csv`
- MT4-результат по `MT/tester/logs/20260411.log`:
  - `8` сделок
  - `PF=58.88`
  - `net=2951.63`
  - `DD=2.85%`
  - `7W / 1L`
- реализован и протестирован secondary tooling для `triple_barrier`:
  - `ML/triple_barrier_mt4_execution.py`
  - `ML/benchmark_triple_barrier_mt4_execution.py`
  но реальные TB benchmark-артефакты ещё не выпущены.

## Last Completed Stage
Entry Path v1 Quantile MT4 Parity (2026-04-11).

## Next Step
1. Принять решение, становится ли `entry_path_v1_quantile` основным execution mode поверх `entry_path_v1`.
2. Если да, выделить для него основной export/runtime path без research-only обвязки.
3. Отдельным secondary stage прогнать `ML/benchmark_triple_barrier_mt4_execution.py` на `validation/test`.
4. После TB benchmark решить, нужен ли TB как backup execution track или достаточно держать его как контрольный эталон MT4-matched логики.

Roadmap doc: `docs/superpowers/roadmap.md`

## Read First
- `AGENTS.md`
- `docs/reports/2026-04-11-entry-path-v1-quantile-mt4-parity.md`
- `docs/reports/2026-04-11-entry-path-v1-quantile-robustness.md`
- `docs/reports/2026-04-10-entry-path-v1-quantile.md`
- `docs/reports/2026-04-09-entry-path-trade-filter.md`
- `ML/reports/entry_path_v1_quantile_mt4_reconciliation.csv`
- `MT/tester/logs/20260411.log`

## Open Risks
- Линия остаётся low-frequency режимом: support устойчивый, но число сделок ниже, чем у базового `A @ 7.5%`.
- MT4 parity подтверждён на одном честном run с `8` сделками; это достаточно для execution-сверки, но не отменяет low-N nature режима.
- `triple_barrier_mt4_execution` пока подтверждён только на уровне кода и тестов, без реального benchmark verdict.

## Latest Report
`docs/reports/2026-04-11-entry-path-v1-quantile-mt4-parity.md`

## Active Roadmap
`docs/superpowers/roadmap.md`
