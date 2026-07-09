# Context Handoff

**Дата:** 2026-07-09

## Текущее состояние

Direction внутри frozen movement-mask проверен повторно с rich features и
full-train политикой. Полный grid завершён: `240/240`, `failed_runs=0`,
`verdict=DIRECTION_REPLICATION_REQUIRED`.

Текущая линия:

- amplitude audit: `DIAGNOSTIC_ONLY / AMPLITUDE_EXPLAINED_BY_SIMPLE_BASELINES`;
- movement-filter design: `SIMPLE_MOVEMENT_FILTER_RESEARCH_ONLY`;
- movement-filter freeze: `FROZEN_MOVEMENT_FILTER_FOR_NEXT_RESEARCH_PLAN`;
- old direction inside frozen movement: `REJECT_DIRECTION_INSIDE_MOVEMENT_REGIME`;
- rich direction inside frozen movement: `DIAGNOSTIC_ONLY / DIRECTION_REPLICATION_REQUIRED`.

## Главный вывод

Rich features нашли слабый direction-effect внутри заранее замороженной
movement-mask, но этого недостаточно для кандидата:

- winner: `nearest_k60|H3|entry_log_ratio|extra_trees`;
- `val_select_inside_mask balanced_accuracy = 0.570170`;
- `val_eval_inside_mask balanced_accuracy = 0.529056`;
- `val_select`/`val_eval` sample-size gates: `PASS`;
- `low_n_disclosure` frozen rows: `59`, disclosure-only, low-N;
- full-split diagnostics около случайного уровня.

Интерпретация: нужна заранее зафиксированная репликация. Это не trading signal.

## Главные артефакты

- `docs/reports/2026-07-09-direction-inside-frozen-movement-regime-rich-features.md`
- `ML/reports/direction_inside_frozen_movement_regime_rich_features.json`
- `ML/reports/direction_inside_frozen_movement_regime_rich_features_metrics.csv`
- `ML/reports/direction_inside_frozen_movement_regime_rich_features_rows.csv`
- `ML/baseline/benchmark_direction_inside_frozen_movement_regime_rich_features.py`
- `tests/test_direction_inside_frozen_movement_regime_rich_features.py`
- `docs/ML/benchmark_direction_inside_frozen_movement_regime_rich_features.py.md`

## Runner Status

Runner поддерживает:

- `--resume` / `--no-resume`, default `--resume`;
- progress JSON после каждого run;
- heartbeat: загрузка split/scores, start, preflight, run start/end, ETA;
- per-run `elapsed_sec`;
- default `--threads 24`;
- `n_jobs=24` для `ExtraTrees` и `XGBoost`;
- `xgb_threads` / `nthread` в JSON для XGBoost;
- очистку legacy resume rows без текущего `resume_key`.

Тесты:

- focused: `30 passed`;
- full suite after implementation: `1254 passed, 30 warnings`.

## Exact Frozen Rule

Frozen movement rule не менялся:

- `simple_combined / extra_trees_small / H3 / top_fraction=0.05`
- `score_aggregation = median_across_rerun_seeds`
- `seeds = [42, 43, 44]`
- `rule_hash = 56361f12104b55c4cac6bd04426349f71d8944c139563a8c9b68d3b25e97deaf`

## Следующий Шаг

Следующим агентом сначала читать:

- `docs/reports/2026-07-09-direction-inside-frozen-movement-regime-rich-features.md`
- `docs/ML/benchmark_direction_inside_frozen_movement_regime_rich_features.py.md`
- `ML/reports/direction_inside_frozen_movement_regime_rich_features.json`
- `docs/reports/2026-07-08-direction-inside-frozen-movement-regime.md`
- `docs/reports/2026-07-08-entry-based-movement-filter-replication-freeze.md`

Практический следующий шаг: написать narrow replication plan. Не выбирать
новый winner по `val_eval`; сначала freeze допустимой репликационной матрицы,
например вокруг `nearest_k60 / H3 / extra_trees`, затем проверять seed/year/block
robustness без открытия `locked_test`.

## Запрещённые Направления

- Не трактовать `DIRECTION_REPLICATION_REQUIRED` как candidate.
- Не тюнить по `val_eval` или `low_n_disclosure`.
- Не менять frozen movement-mask в рамках этой ветки.
- Не добавлять PnL/PF, BUY/SELL или trading claims.
- Не открывать `locked_test`.
- Не выдавать weak direction-effect за production/live rule.
