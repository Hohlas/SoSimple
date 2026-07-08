# Context Handoff

**Дата:** 2026-07-08

## Текущее состояние

Direction-inside-frozen-movement план выполнен и закрыт с вердиктом
`ABORT_CONTRACT_FAIL`.

Это не отрицательный результат direction-модели. Baseline-модели не запускались,
потому что входной frozen score export нельзя честно соединить со split-ами по
заданному контракту `split + time`.

Текущая линия:

- amplitude audit: `DIAGNOSTIC_ONLY / AMPLITUDE_EXPLAINED_BY_SIMPLE_BASELINES`;
- movement-filter design: `SIMPLE_MOVEMENT_FILTER_RESEARCH_ONLY`;
- movement-filter freeze: `FROZEN_MOVEMENT_FILTER_FOR_NEXT_RESEARCH_PLAN`;
- direction inside frozen movement: `ABORT_CONTRACT_FAIL`.

## Главные артефакты

- `docs/reports/2026-07-08-direction-inside-frozen-movement-regime.md`
- `ML/reports/direction_inside_frozen_movement_regime.json`
- `ML/reports/direction_inside_frozen_movement_regime_rows.csv`
- `ML/baseline/benchmark_direction_inside_frozen_movement_regime.py`
- `docs/ML/benchmark_direction_inside_frozen_movement_regime.py.md`
- `tests/test_direction_inside_frozen_movement_regime.py`

Source artifacts:

- `docs/reports/2026-07-08-entry-based-movement-filter-replication-freeze.md`
- `ML/reports/entry_based_movement_filter_freeze.json`
- `ML/reports/entry_based_movement_filter_freeze_scores.csv`

## Exact frozen rule

Frozen movement rule не менялся:

- `simple_combined / extra_trees_small / H3 / top_fraction=0.05`
- `score_aggregation = median_across_rerun_seeds`
- `seeds = [42, 43, 44]`
- `rule_hash = 56361f12104b55c4cac6bd04426349f71d8944c139563a8c9b68d3b25e97deaf`

## Contract Failure

Canonical artifact:

- `verdict = ABORT_CONTRACT_FAIL`
- `contract.status = ABORT_CONTRACT_FAIL`
- `search_budget.direction_baselines_trained = 0`

Reasons:

- `scores.duplicate_split_time`
- `splits.train.duplicate_time`
- `splits.validation.duplicate_time`
- `splits.low_n_disclosure.duplicate_time`
- `splits.val_select.duplicate_time`
- `splits.val_eval.duplicate_time`

## Следующий шаг

Следующим агентом сначала читать:

- `docs/reports/2026-07-08-direction-inside-frozen-movement-regime.md`
- `docs/ML/benchmark_direction_inside_frozen_movement_regime.py.md`
- `ML/reports/direction_inside_frozen_movement_regime.json`

Практический следующий шаг:

- создать отдельный repair-plan для stable unique row id в frozen score export;
- перегенерировать frozen score artifacts без изменения movement rule;
- только после успешного join-contract повторить direction-inside-mask проверку.

## Запрещённые направления

- Не трактовать `ABORT_CONTRACT_FAIL` как слабость direction-сигнала.
- Не расширять movement mask и не менять `top_fraction`.
- Не чинить join через direction outcome.
- Не добавлять PnL/PF, BUY/SELL или trading claims.
- Не открывать `locked_test`.
