# Context Handoff

**Дата:** 2026-07-06

## Текущий этап

Этап `Entry-Based Powerful Tabular Models` завершён.

Итоговый structured artifact:

- `ML/reports/entry_based_powerful_tabular.json`
- `summary.verdict = PIVOT_AMPLITUDE`
- verdict этапа: `DIAGNOSTIC_ONLY / PIVOT_AMPLITUDE`

Мощные табличные модели не спасли direction в текущей mechanics `entry-based next open`. Amplitude trace подтверждён сильнее и устойчивее.

## Главные артефакты

- `docs/reports/2026-07-06-entry-based-powerful-tabular-models.md`
- `ML/reports/entry_based_powerful_tabular.json`
- `ML/reports/entry_based_powerful_tabular_metrics.csv`
- `ML/reports/entry_based_powerful_tabular_rows.csv`
- `ML/reports/entry_based_powerful_tabular_scale_audit.csv`
- `docs/ML/benchmark_entry_based_powerful_tabular.py.md`
- `tests/test_entry_based_powerful_tabular.py`

## Главный вывод

Технический контракт выполнен:

- `progress.done_runs = 40`
- `failed_runs = []`
- `entry_based_smoke_check.status = PASS`
- `split_horizon_overlap_check.status = PASS`
- `scale_audit.status = WARNING`
- `audit_decisions` записаны
- `normalization_contract.fit_split = train`
- top-level JSON fields present: `schema_version`, `verdict`, `dependency_versions`, `normalization_contract`
- `run_config_hash = 7a67a59aa22a5d153ae541a8f9fc3eb3698ba3172a4217eb8572058d3ebb518e`
- `thread_count = 24`
- `locked_test` не открыт
- `low_n_disclosure=2026` не использовался для verdict

Search width:

- 4 representations;
- 10 models;
- 1 seed;
- 4 horizons;
- 3 predicted target families;
- 480 metric comparisons.

По содержанию:

- лучший candidate direction: `nearest_k80 / hist_gradient_boosting_strong / entry_log_ratio H12`, `val_select=0.0519`, `val_eval=-0.0009`;
- best-by-`val_eval` direction: `corridor_5atr / extra_trees_regressor / H12`, `val_select=0.0042`, `val_eval=0.0475`; это hindsight disclosure, не selectable winner;
- direction gate `0.10` не пройден;
- same-model `all100` лучше на `val_eval`;
- yearly check для direction на `val_eval` не пройден;
- `simple_trade` для лучшего direction: `0.0732 -> -0.0609`;
- лучший amplitude: `nearest_k60 / hist_gradient_boosting_strong / entry_up H3`, `val_select=0.3412`, `val_eval=0.4419`;
- amplitude yearly diagnostics проходят.

## Следующий шаг

Следующий файл читать:

- `docs/reports/2026-07-06-entry-based-powerful-tabular-models.md`
- `docs/ML/benchmark_entry_based_powerful_tabular.py.md`

Если продолжать исследование, писать новый bounded plan для amplitude / movement-regime target:

- основной target заранее формулировать вокруг `entry_up` / `entry_dn` / movement potential;
- не использовать `entry_log_ratio` как главный вопрос;
- не открывать `locked_test` до freeze;
- не использовать 2026 для выбора;
- заранее определить, как amplitude превращается в решение: movement/no-movement filter, горизонт, отдельный gross/backtest слой;
- раскрыть search width и cumulative post-hoc context.

## Запрещённые направления

- Не трактовать `PIVOT_AMPLITUDE` как trading candidate.
- Не трактовать amplitude trace как подтверждённый direction signal.
- Не запускать direction freeze по текущей mechanics.
- Не использовать `low_n_disclosure=2026` для выбора.
- Не открывать `locked_test` без отдельного frozen-rule плана.
