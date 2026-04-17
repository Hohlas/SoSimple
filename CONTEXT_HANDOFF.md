# Context Handoff

## Current Stage
Этап `take_skip_trailing_stop_matrix` завершён (2026-04-17).

Что зафиксировано:

- реализован новый research track `take_skip_trailing_stop_v1`
- целевая постановка:
  - `take = 1`, если `trail_48_pnl_atr_xN >= 0.5`
  - `take = 0` иначе
- проверена широкая сетка trailing-stop параметров:
  - `X = 2, 3, 4, 6, 8`
- реализованы:
  - `ML/take_skip_trailing_stop_task.py`
  - `ML/benchmark_take_skip_trailing_stop.py`
  - `ML/run_take_skip_trailing_stop_matrix.py`
- train/evaluate/export stack поддерживает новый task
- matrix run для `seq_len = 20 / 50 / 100` завершён на удалённом сервере
- во всех трёх конфигурациях:
  - `verdict = reject`
  - `validation_winner = null`
  - `test_result = null`
- среди всех validation candidates:
  - `PF > 1` не найдено ни разу
  - `prob_ge_threshold` полностью пуст: на всех порогах `0.50..0.95` число сделок равно нулю
  - benchmark жил только на `top_k_probability`
- лучшие validation candidates среди `trades_per_year >= 6`:
  - `seq20`: `take_48_x2 + top_k_probability 0.05`, `PF=0.274`, `24` trades
  - `seq50`: `take_48_x2 + top_k_probability 0.05`, `PF=0.202`, `24` trades
  - `seq100`: `take_48_x8 + top_k_probability 0.10`, `PF=0.153`, `48` trades
- canonical report:
  - `docs/reports/2026-04-17-take-skip-trailing-stop-matrix.md`

## Previous Stage
Этап `trailing_stop_target_quantile_first_wave` завершён (2026-04-16).

Что зафиксировано:

- новый task `trailing_stop_target_quantile_v1` реализован и протянут через train/evaluate/export stack
- bounded run `transformer_seq20_x3_quantile` завершён
- лучший validation candidate `q10_gt_m` дал только `PF=0.1750`, `95` trades
- `PF >= 1.0` не найден, verdict: `reject`
- canonical report:
  - `docs/reports/2026-04-16-trailing-stop-target-quantile-first-wave.md`

## Earlier Stage
Этап `trailing_stop_target_first_wave` завершён (2026-04-16).

Что зафиксировано:

- новый target `trailing_stop_target_v1` реализован для сетки `seq_len = 20 / 50 / 100`
- лучший validation candidate всего этапа:
  - `transformer_seq20 + trail_48_pnl_atr_x3`, `PF=0.4206`
- `validation PF > 1` не найден ни в одной конфигурации
- canonical report:
  - `docs/reports/2026-04-16-trailing-stop-target-first-wave.md`

## Stable Production Context

- `entry_path_v1_quantile` остаётся подтверждённым production-ready parallel execution mode
- current production rule:
  - `ML/reports/entry_path_v1_quantile_selected_rule.json`
- этот parallel mode не затронут отрицательными результатами новых research-track экспериментов

## Next Step
Следующий этап должен менять не selection layer, а само представление данных и обучающий сигнал.

Практический фокус:

1. Спроектировать новый training track на обновлённом наборе признаков.
2. Использовать все 100 доступных фракталов вместо текущего урезанного представления.
3. Добавить multi-scale summaries по нескольким длинам истории.
4. Сохранить простую торговую логику без лишнего усложнения execution layer.
5. Только после этого запускать новый тяжёлый train.

## Read First

- `docs/reports/2026-04-17-take-skip-trailing-stop-matrix.md`
- `docs/reports/2026-04-16-trailing-stop-target-quantile-first-wave.md`
- `docs/reports/2026-04-16-trailing-stop-target-first-wave.md`
- `docs/superpowers/specs/2026-04-17-take-skip-trailing-stop-design.md`
- `docs/superpowers/plans/2026-04-17-take-skip-trailing-stop.md`
- `CHANGELOG.md`
- `AGENTS.md`

## Open Risks

- **Signal weakness**: ни regression, ни quantile, ни binary take/skip не дали даже `PF > 1` на validation.
- **Feature bottleneck**: текущий research stack, вероятно, упёрся не в benchmark, а в бедное представление входной последовательности.
- **Extreme imbalance**: positive-class для `take_skip_trailing_stop_v1` лежит в диапазоне `0.37% .. 0.92%`, что само по себе затрудняет обучение.
- **CSV artifact gap**: `validation_grid.csv` не коммитятся из-за `gitignore`; для последующих этапов полезно либо явно сохранять их вне ignore, либо добавлять агрегированные diagnostics в `summary.json`.

## Latest Report

`docs/reports/2026-04-17-take-skip-trailing-stop-matrix.md`

## Active Roadmap

`docs/superpowers/roadmap.md`
