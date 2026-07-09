# Context Handoff

**Дата:** 2026-07-09

## Текущее состояние

После reject старого direction-inside-frozen-movement этапа был начат rich
features follow-up. Runner исправлен: он подключён к реальным split/freeze
артефактам и пишет непустые metrics/rows. Полный rich-features grid ещё не
запускался; выполнен только ограниченный smoke.

Текущая линия:

- amplitude audit: `DIAGNOSTIC_ONLY / AMPLITUDE_EXPLAINED_BY_SIMPLE_BASELINES`;
- movement-filter design: `SIMPLE_MOVEMENT_FILTER_RESEARCH_ONLY`;
- movement-filter freeze: `FROZEN_MOVEMENT_FILTER_FOR_NEXT_RESEARCH_PLAN`;
- direction inside frozen movement: `REJECT_DIRECTION_INSIDE_MOVEMENT_REGIME`.
- direction inside frozen movement rich features smoke: `REJECT_DIRECTION_INSIDE_MOVEMENT_REGIME`.

## Что выяснено

`split + time` не является уникальным ключом, потому что один бар может дать
несколько entry-строк. Частая причина: на одном баре есть разные фрактальные
события, включая противоположные `direction`; часть дублей имеет одинаковый
видимый `fractal0`, но всё равно остаётся отдельными строками.

Repair:

- `ML/reports/entry_based_movement_filter_freeze_scores.csv` теперь содержит
  `split_row_id`;
- direction join использует `split + split_row_id`;
- `split + time` остаётся только диагностикой.

## Главные артефакты

- `docs/reports/2026-07-09-direction-inside-frozen-movement-regime-rich-features.md`
- `ML/reports/direction_inside_frozen_movement_regime_rich_features.json`
- `ML/reports/direction_inside_frozen_movement_regime_rich_features_metrics.csv`
- `ML/reports/direction_inside_frozen_movement_regime_rich_features_rows.csv`
- `ML/baseline/benchmark_direction_inside_frozen_movement_regime_rich_features.py`
- `tests/test_direction_inside_frozen_movement_regime_rich_features.py`
- `docs/reports/2026-07-08-direction-inside-frozen-movement-regime.md`
- `ML/reports/direction_inside_frozen_movement_regime.json`
- `ML/reports/direction_inside_frozen_movement_regime_rows.csv`
- `ML/reports/entry_based_movement_filter_freeze_scores.csv`
- `ML/baseline/benchmark_direction_inside_frozen_movement_regime.py`
- `ML/baseline/benchmark_entry_based_movement_filter_freeze.py`
- `tests/test_direction_inside_frozen_movement_regime.py`
- `tests/test_entry_based_movement_filter_freeze.py`

## Exact Frozen Rule

Frozen movement rule не менялся:

- `simple_combined / extra_trees_small / H3 / top_fraction=0.05`
- `score_aggregation = median_across_rerun_seeds`
- `seeds = [42, 43, 44]`
- `rule_hash = 56361f12104b55c4cac6bd04426349f71d8944c139563a8c9b68d3b25e97deaf`

## Direction Result

Старый simple direction artifact:

- `verdict = REJECT_DIRECTION_INSIDE_MOVEMENT_REGIME`
- `contract.status = PASS`
- `search_budget.direction_baselines_trained = 3`
- winner by `val_select`: `extra_trees_small`

Key metrics:

- `val_select`: `n=333`, balanced accuracy `0.5792`, MCC `0.1701`;
- `val_eval`: `n=333`, balanced accuracy `0.5287`, MCC `0.0579`;
- `low_n_disclosure`: `n=59`, balanced accuracy `0.4747`, MCC `-0.0506`.

Robustness failed: only one active `val_eval` year, weak `val_eval` metrics,
low confidence lower bound, and block stability remains `NOT_RUN`.

Rich-features smoke artifact:

- `verdict = REJECT_DIRECTION_INSIDE_MOVEMENT_REGIME`
- `contract_status = PASS`
- `training_scope = full_train`
- `frozen_mask_usage = evaluation_only`
- `selection_metric = val_select_inside_mask`
- `train_rows = 44159`
- frozen-mask rows: `train=2208`, `val_select=333`, `val_eval=333`, `low_n_disclosure=59`
- smoke config: `simple_combined / H3 / entry_log_ratio / extra_trees`
- `val_select_inside_mask balanced_accuracy = 0.528851`
- `val_eval_inside_mask balanced_accuracy = 0.472188`
- `low_n_disclosure_inside_mask balanced_accuracy = 0.412069`, sample-size gate `FAIL`
- metrics/rows CSV are non-empty.

Это только smoke direction-result. Полный rich-features grid ещё не выполнен.

## Следующий Шаг

Следующим агентом сначала читать:

- `docs/reports/2026-07-09-direction-inside-frozen-movement-regime-rich-features.md`
- `docs/reports/2026-07-08-direction-inside-frozen-movement-regime.md`
- `docs/ML/benchmark_direction_inside_frozen_movement_regime_rich_features.py.md`
- `docs/ML/benchmark_direction_inside_frozen_movement_regime.py.md`
- `docs/ML/benchmark_entry_based_movement_filter_freeze.py.md`
- `ML/reports/direction_inside_frozen_movement_regime_rich_features.json`
- `ML/reports/direction_inside_frozen_movement_regime.json`

Практический следующий шаг: если branch важен, запустить полный rich-features
grid или разумно ограниченную заранее зафиксированную подматрицу. Если нет,
вернуться к roadmap-направлению `fractal0_price` entry mechanics. Не считать
один smoke-run проверкой всей rich-features гипотезы.

## Запрещённые Направления

- Не трактовать `val_select` uplift как кандидат.
- Не расширять movement mask и не менять `top_fraction` в рамках этого этапа.
- Не тюнить по `val_eval` или `low_n_disclosure`.
- Не добавлять PnL/PF, BUY/SELL или trading claims.
- Не открывать `locked_test`.
- Не выдавать один rich-features smoke-run за полный rich-features closeout.
