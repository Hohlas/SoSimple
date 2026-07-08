# Context Handoff

**Дата:** 2026-07-08

## Текущее состояние

Task 6 завершён: replication/freeze ветка для entry-based movement filter
синхронизирована по report/docs/wiki/handoff.

Текущий финальный статус этой подветки:

- amplitude audit: `DIAGNOSTIC_ONLY / AMPLITUDE_EXPLAINED_BY_SIMPLE_BASELINES`;
- movement-filter design: `SIMPLE_MOVEMENT_FILTER_RESEARCH_ONLY`;
- movement-filter freeze: `FROZEN_MOVEMENT_FILTER_FOR_NEXT_RESEARCH_PLAN`.

Это означает: заморожено одно research segmentation rule для следующего плана.
Это не direction, не PnL/PF, не trading candidate, не live rule и не permission
to open `locked_test`.

## Главные артефакты

- `docs/reports/2026-07-08-entry-based-movement-filter-replication-freeze.md`
- `ML/reports/entry_based_movement_filter_freeze.json`
- `ML/reports/entry_based_movement_filter_freeze_yearly.csv`
- `ML/reports/entry_based_movement_filter_freeze_selected_rows.csv`
- `ML/reports/entry_based_movement_filter_freeze_scores.csv`
- `ML/reports/entry_based_movement_filter_freeze_random_baseline.csv`
- `ML/reports/entry_based_movement_filter_freeze_score_cutoffs.csv`
- `ML/baseline/benchmark_entry_based_movement_filter_freeze.py`
- `docs/ML/benchmark_entry_based_movement_filter_freeze.py.md`
- `tests/test_entry_based_movement_filter_freeze.py`

Нужные source artifacts:

- `docs/reports/2026-07-07-entry-based-movement-filter-design.md`
- `ML/reports/entry_based_movement_filter.json`
- `docs/reports/2026-07-07-entry-based-amplitude-movement-regime.md`
- `ML/reports/entry_based_amplitude_movement.json`

## Exact frozen rule

Заморожено только это правило:

- `simple_combined / extra_trees_small / H3 / top_fraction=0.05`
- `score_aggregation = median_across_rerun_seeds`
- `seeds = [42, 43, 44]`
- `rule_hash = 56361f12104b55c4cac6bd04426349f71d8944c139563a8c9b68d3b25e97deaf`
- `frozen_config_hash = ee2701d0566e910e8a0fb10c6d4f5a8916d2b4e5b903e9dc50f39354344e86b6`

Ключевые числа:

- `val_select`: `selected_n=333`, `movement_lift=2.1528`
- `val_eval`: `selected_n=333`, `movement_lift=2.4806`, `yearly_lift_pass_rate=1.0`
- `2026 disclosure`: `selected_n=59`, `movement_lift=1.6292`

## Что уже синхронизировано

- `CHANGELOG.md`
- `CONTEXT_HANDOFF.md`
- `MODULE_INDEX.md`
- `docs/tests/tests.md`
- `docs/superpowers/roadmap.md`
- `wiki/research/fractal-stop-research.md`
- `wiki/index.md`
- `wiki/log.md`
- `wiki/REPO_integrity.md`

## Следующий шаг

Следующим агентом сначала читать:

- `docs/reports/2026-07-08-entry-based-movement-filter-replication-freeze.md`
- `docs/ML/benchmark_entry_based_movement_filter_freeze.py.md`
- `ML/reports/entry_based_movement_filter_freeze.json`

Практический следующий шаг:

- не расширять search space этой ветки;
- использовать freeze только как входной segmentation contract для нового
  отдельного research plan;
- если проверять direction, делать это только как новую узкую постановку с
  заранее фиксированным scope и без открытия `locked_test`.

## Запрещённые направления

- Не трактовать freeze как direction signal.
- Не добавлять BUY/SELL или торговые выводы задним числом.
- Не добавлять PnL/PF интерпретацию.
- Не считать результат independent replication.
- Не открывать `locked_test`.
- Не возвращаться к wide search по новым профилям, моделям, горизонтам или
  threshold в этой же ветке.
