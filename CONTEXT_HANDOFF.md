# Context Handoff

## Current Stage
Этап `multi_horizon_take_skip_feature_track` завершён положительным verdict (2026-04-18).

Что зафиксировано:

- реализован и проверен новый research track `take_skip_trailing_stop_v2`
- целевая постановка:
  - бинарный `take/skip`
  - positive class: `trail_pnl >= 0.5 ATR`
- target grid:
  - горизонты `12 / 24 / 48`
  - trailing-stop `X = 2 / 4 / 8`
- feature representation:
  - полные `100` фракталов
  - multi-scale summaries по окнам `5 / 10 / 20 / 50 / 100`
  - существующие row-wise numeric features
- реализованы:
  - `ML/multi_scale_fractal_features.py`
  - `ML/take_skip_trailing_stop_v2_task.py`
  - `ML/benchmark_take_skip_trailing_stop_v2.py`
  - `ML/run_take_skip_trailing_stop_v2_matrix.py`
- train/evaluate/export stack поддерживает новый task
- локальный smoke-run `transformer_seq20` прошёл весь контур end-to-end
- после первых server run найдены и исправлены два критических дефекта интерпретации:
  - runner переиспользовал кэш между `seq_len`
  - `take_skip_trailing_stop_v2` насильно форсил `seq_len=100`
- после bugfix rerun полный matrix `seq_len = 20 / 50 / 100` дал валидный `go` во всех трёх конфигурациях
- общий winner-pattern:
  - `target = take_24_x8`
  - `candidate = prob_ge_threshold`
- лучший текущий candidate:
  - `seq50`
  - `threshold = 0.70`
  - validation: `27` trades, `PF=inf`, `negative_year_slices=0`
  - test: `41` trades, `PF=39.74`, `trades_per_year=8.2`
- canonical report:
  - `docs/reports/2026-04-18-multi-horizon-take-skip-feature-track.md`

## Previous Stage
Этап `take_skip_trailing_stop_matrix` завершён (2026-04-17).

Что зафиксировано:

- реализован новый research track `take_skip_trailing_stop_v1`
- целевая постановка:
  - `take = 1`, если `trail_48_pnl_atr_xN >= 0.5`
  - `take = 0` иначе
- matrix run для `seq_len = 20 / 50 / 100` завершён на удалённом сервере
- во всех трёх конфигурациях:
  - `verdict = reject`
  - `validation_winner = null`
  - `test_result = null`
- среди всех validation candidates:
  - `PF > 1` не найдено ни разу
  - `prob_ge_threshold` полностью пуст
- canonical report:
  - `docs/reports/2026-04-17-take-skip-trailing-stop-matrix.md`

## Earlier Stage
Этап `trailing_stop_target_quantile_first_wave` завершён (2026-04-16).

Что зафиксировано:

- новый task `trailing_stop_target_quantile_v1` реализован и протянут через train/evaluate/export stack
- bounded run `transformer_seq20_x3_quantile` завершён
- лучший validation candidate `q10_gt_m` дал только `PF=0.1750`, `95` trades
- `PF >= 1.0` не найден, verdict: `reject`
- canonical report:
  - `docs/reports/2026-04-16-trailing-stop-target-quantile-first-wave.md`

## Stable Production Context

- `entry_path_v1_quantile` остаётся подтверждённым production-ready parallel execution mode
- current production rule:
  - `ML/reports/entry_path_v1_quantile_selected_rule.json`
- этот parallel mode не затронут отрицательными результатами новых research-track экспериментов

## Next Step
Следующий шаг уже не в большом retraining, а в короткой диагностике и frozen follow-up вокруг winner-а.

Практический фокус:

1. Разобрать, почему history обучения почти совпадает по `seq20 / 50 / 100`.
2. Отдельно зафиксировать winner:
   - `seq50`
   - `take_24_x8`
   - `prob_ge_threshold >= 0.70`
3. Решить, считать ли это уже candidate-level production path или делать ещё один короткий frozen check.

## Read First

- `docs/reports/2026-04-18-multi-horizon-take-skip-feature-track.md`
- `docs/superpowers/specs/2026-04-17-multi-horizon-take-skip-feature-track-design.md`
- `docs/superpowers/plans/2026-04-17-multi-horizon-take-skip-feature-track.md`
- `CHANGELOG.md`
- `AGENTS.md`

## Open Risks

- **Residual symmetry**: train history и validation BCE у `seq20 / 50 / 100` остались почти одинаковыми; это требует отдельной короткой диагностики.
- **Extreme imbalance**: positive-class в v2 остаётся очень редким, особенно на коротких горизонтах.
- **Infinity PF caution**: validation winner не имеет отрицательных сделок в выбранном окне; это сильный сигнал, но его нужно трактовать осторожно.
- **CSV artifact gap**: `validation_grid.csv` не коммитятся из-за `gitignore`; для итогового этапа их надо переносить вручную или сохранять вне ignore.

## Latest Report

`docs/reports/2026-04-18-multi-horizon-take-skip-feature-track.md`

## Active Roadmap

`docs/superpowers/roadmap.md`
