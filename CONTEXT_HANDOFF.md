# Context Handoff

**Дата:** 2026-07-03

## Текущий этап

Этап `Fractal Selection Ablation On Entry-Based Target` завершён.

Итоговый structured artifact:

- `ML/reports/entry_based_updn_fractal_selection_ablation.json`
- статус runner: `WEAK_TRACE_FOUND`
- verdict этапа: `DIAGNOSTIC_ONLY`

Это не reversal предыдущего вывода про `next open after signal_time`. После исправления честности сравнения слабый след остаётся только диагностическим: лучший directional trace находится на `H12`, но не достигает уровня подтверждённого winner.

## Главные артефакты

- `docs/reports/2026-07-03-fractal-selection-ablation-entry-based-target.md`
- `ML/reports/entry_based_updn_fractal_selection_ablation.json`
- `ML/reports/entry_based_updn_fractal_selection_ablation_metrics.csv`
- `ML/reports/entry_based_updn_fractal_selection_ablation_rows.csv`
- `docs/ML/benchmark_entry_based_updn_fractal_selection_ablation.py.md`

## Главный вывод

Технический контракт этапа выполнен:

- `target_mode = rebuilt`
- `entry_based_target_contract_check = PASS`
- `anchor_contract` и `same_feature_bundle` записаны в artifact
- `updn_horizons = 3/6/12` для всех representation profile
- запрещённые `up_24/dn_24/up_48/dn_48` в `feature_names`: `0`
- `smoke_check_disclosure = LEGACY_SMOKE_FAIL_STAGE_CONTRACT_PASS`
- `thread_count = 24`
- чистый полный прогон `120/120`, `elapsed_sec = 12525.8`

По содержанию результат слабый:

- устойчивого направленного winner нет;
- лучший `val_stop` trace: `corridor_5atr / xgboost_depth3 / H12 = 0.0795`, uplift к `all100` `+0.0498`;
- дополнительные слабые H12-следы:
  - `nearest_k20`
  - `nearest_k60`
  - `nearest_k80`
- эти следы в основном `amplitude-only`, а не directional.

`all100` не выглядит обязательным baseline-победителем, но результат остаётся exploratory и не создаёт trading candidate.

## Следующий шаг

Если продолжать эту ветку, сначала нужен методический preflight:

- решить, имеет ли `H12` практический смысл для механики `next open after signal_time`;
- если `H12` не подходит, остановить ветку или задать короткий-horizon stop condition;
- добавить отдельный entry-based smoke-check, чтобы не зависеть от legacy `statistics/data_contract_smoke_check.py`.

Только после этого можно обсуждать узкий rerun:

- shortlist:
  - `corridor_5atr`
  - `nearest_k20`
  - `nearest_k60`
  - `nearest_k80`
- без расширения model grid;
- без новых `k` и новых corridor width;
- без выбора по disclosure split.

## Запрещённые направления

- Не трактовать `WEAK_TRACE_FOUND` как подтверждённый торговый сигнал.
- Не использовать `diagnostic_holdout` или `low_n_disclosure` для выбора representation winner.
- Не расширять representation matrix задним числом по итогам этого же прогона.
- Не смешивать amplitude-only trace с directional uplift.
