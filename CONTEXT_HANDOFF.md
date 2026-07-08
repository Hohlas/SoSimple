# Context Handoff

**Дата:** 2026-07-08

## Текущее состояние

Direction-inside-frozen-movement этап продолжен после contract fail,
root cause дубликатов найден и repair выполнен. Финальный вердикт:
`REJECT_DIRECTION_INSIDE_MOVEMENT_REGIME`.

Текущая линия:

- amplitude audit: `DIAGNOSTIC_ONLY / AMPLITUDE_EXPLAINED_BY_SIMPLE_BASELINES`;
- movement-filter design: `SIMPLE_MOVEMENT_FILTER_RESEARCH_ONLY`;
- movement-filter freeze: `FROZEN_MOVEMENT_FILTER_FOR_NEXT_RESEARCH_PLAN`;
- direction inside frozen movement: `REJECT_DIRECTION_INSIDE_MOVEMENT_REGIME`.

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

Canonical artifact:

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

## Следующий Шаг

Следующим агентом сначала читать:

- `docs/reports/2026-07-08-direction-inside-frozen-movement-regime.md`
- `docs/ML/benchmark_direction_inside_frozen_movement_regime.py.md`
- `docs/ML/benchmark_entry_based_movement_filter_freeze.py.md`
- `ML/reports/direction_inside_frozen_movement_regime.json`

Практический следующий шаг: закрыть текущую direction-inside-mask ветку как
reject. Новый direction-поиск, если нужен, должен быть отдельным заранее
сформулированным планом, а не тюнингом по этому `val_eval`.

## Запрещённые Направления

- Не трактовать `val_select` uplift как кандидат.
- Не расширять movement mask и не менять `top_fraction` в рамках этого этапа.
- Не тюнить по `val_eval` или `low_n_disclosure`.
- Не добавлять PnL/PF, BUY/SELL или trading claims.
- Не открывать `locked_test`.
