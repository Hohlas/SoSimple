# Context Handoff

## Current Stage
Этап `multi_horizon_take_skip_feature_track` подготовлен к полному server run (2026-04-17).

Что зафиксировано:

- реализован новый research track `take_skip_trailing_stop_v2`
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
- smoke verdict:
  - `verdict = go`
  - validation winner: `take_48_x4 + top_k_probability 0.05`
  - `PF=6.39`, `24` trades, `negative_year_slices=0`
- важное operational условие:
  - в `DATA/Nero_{train,validation,test}_labeled.csv` уже должны быть колонки `trail_12_*`, `trail_24_*`, `trail_48_*` для `X = 2 / 4 / 8`
- canonical handoff report:
  - `docs/reports/2026-04-17-multi-horizon-take-skip-feature-track-handoff.md`

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
Следующий шаг уже не в проектировании, а в полном remote matrix run для `take_skip_trailing_stop_v2`.

Практический фокус:

1. Синхронизировать `DATA/` на сервере в уже пересчитанном виде.
2. Запустить `ML.run_take_skip_trailing_stop_v2_matrix` для `seq_len = 20 / 50 / 100`.
3. Вернуть `manifest.json`, `summary.json`, `final_verdict.json`, `validation_grid.csv`.
4. После этого закрыть этап stage-report + wiki ingest по итоговому verdict.

## Read First

- `docs/reports/2026-04-17-take-skip-trailing-stop-matrix.md`
- `docs/reports/2026-04-17-multi-horizon-take-skip-feature-track-handoff.md`
- `docs/superpowers/specs/2026-04-17-multi-horizon-take-skip-feature-track-design.md`
- `docs/superpowers/plans/2026-04-17-multi-horizon-take-skip-feature-track.md`
- `CHANGELOG.md`
- `AGENTS.md`

## Open Risks

- **No full verdict yet**: есть только локальный smoke-run, итоговый исследовательский вывод ещё не получен.
- **Server data dependency**: без новых `trail_12_*` и `trail_24_*` колонок matrix run не стартует.
- **Extreme imbalance**: positive-class в v2 остаётся очень редким, особенно на коротких горизонтах.
- **Smoke optimism risk**: локальный `go` на `seq20` и `1 epoch` может быть случайным и не обязан воспроизводиться в полном bounded run.
- **CSV artifact gap**: `validation_grid.csv` не коммитятся из-за `gitignore`; для итогового этапа их надо переносить вручную или сохранять вне ignore.

## Latest Report

`docs/reports/2026-04-17-multi-horizon-take-skip-feature-track-handoff.md`

## Active Roadmap

`docs/superpowers/roadmap.md`
