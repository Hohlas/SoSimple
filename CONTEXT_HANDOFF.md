# Context Handoff

**Дата:** 2026-07-07

## Текущий этап

Этап `Entry-Based Amplitude Movement Regime Audit` завершён.

Итоговый structured artifact:

- `ML/reports/entry_based_amplitude_movement.json`
- `verdict = AMPLITUDE_EXPLAINED_BY_SIMPLE_BASELINES`
- verdict этапа: `DIAGNOSTIC_ONLY / AMPLITUDE_EXPLAINED_BY_SIMPLE_BASELINES`

Amplitude / movement-regime связь сильная, но лучший результат объясняется простыми baseline-признаками. Это не trading signal и не freeze-кандидат.

После ревью отчёта исправлено:

- `ML/reports/entry_based_amplitude_movement_yearly.csv` теперь содержит идентификатор запуска: `profile`, `model_key`, `seed`, `target_family`;
- `yearly` artifact имеет размер `2136 x 11`;
- `distance_to_level_pre_entry_only` явно зафиксирован как `SKIPPED_NO_DECISION_PRICE`;
- в отчёт добавлены таблицы simple-vs-complex, feature audit, target-distribution interpretation и winner disclosure по `low_n_disclosure`.

## Главные артефакты

- `docs/reports/2026-07-07-entry-based-amplitude-movement-regime.md`
- `docs/superpowers/plans/2026-07-07-entry-based-amplitude-movement-regime-audit.md`
- `ML/reports/entry_based_amplitude_movement.json`
- `ML/reports/entry_based_amplitude_movement_metrics.csv`
- `ML/reports/entry_based_amplitude_movement_seed_aggregate.csv`
- `ML/reports/entry_based_amplitude_movement_quantiles.csv`
- `ML/reports/entry_based_amplitude_movement_yearly.csv`
- `ML/reports/entry_based_amplitude_movement_target_distribution.csv`
- `ML/reports/entry_based_amplitude_movement_feature_audit.csv`
- `ML/baseline/benchmark_entry_based_amplitude_movement.py`
- `docs/ML/benchmark_entry_based_amplitude_movement.py.md`
- `tests/test_entry_based_amplitude_movement.py`

## Главный вывод

Технический контракт выполнен:

- `progress.done_runs = 384`
- `progress.total_runs = 384`
- `failed_runs = []`
- `elapsed_sec = 4008.4`
- `effective_threads = 24`
- `target_contract.status = PASS`
- `target_unit_contract.verdict = PASS`
- `run_config_hash = 772528c243fc8485fe0a9d290de851078123631f7040687cf5e0b80c010d0795`
- `locked_test` не открыт
- `low_n_disclosure=2026` не использовался для verdict

Лучший eligible профиль:

- `simple_combined / extra_trees_small / H3`
- `val_select_spearman_median = 0.571142`
- `val_eval_spearman_median = 0.693452`
- `val_select_top10_lift_median = 2.076212`
- `val_eval_top10_lift_median = 2.289916`
- `yearly_check_pass = True`

No-price/no-time sequence не побил simple baseline:

- лучший `nearest_k60_no_price_coord_sequence_flat / extra_trees_small / H3`;
- `val_select_spearman_median = 0.544603`;
- `val_eval_spearman_median = 0.436387`.

Post-entry diagnostic исключён из выбора:

- лучший `distance_to_entry_open_post_entry_diagnostic_only / extra_trees_small / H3`;
- `selection_eligible = False`;
- `val_select_spearman_median = 0.200225`.

Ограничения интерпретации:

- `simple_combined` фактически = `ATR + time + fractal_density`, потому что безопасный distance-control без цены решения не выполнен;
- `entry_movement_3` p50 сдвигается `3.00 train -> 5.01 val_select -> 7.99 val_eval -> 28.59 low_n_disclosure`;
- у winner на `low_n_disclosure` Spearman только `0.154219..0.169164`, при top10 lift `1.567015..1.676254`.

## Следующий шаг

Следующий файл читать:

- `docs/reports/2026-07-07-entry-based-amplitude-movement-regime.md`
- `docs/ML/benchmark_entry_based_amplitude_movement.py.md`
- `ML/reports/entry_based_amplitude_movement.json`

Ближайший честный исследовательский шаг: отдельный bounded plan для decision layer поверх movement regime.

Минимальная формулировка:

- заранее зафиксировать movement threshold;
- отделить movement/no-movement filter от direction/exit policy;
- сравнивать с `time_plus_atr` и `simple_combined`;
- не выбирать winner по `val_eval` или `low_n_disclosure=2026`;
- не открывать `locked_test`;
- не трактовать amplitude как direction signal.

## Запрещённые направления

- Не запускать freeze по amplitude audit.
- Не трактовать `AMPLITUDE_EXPLAINED_BY_SIMPLE_BASELINES` как торговый сигнал.
- Не открывать `locked_test` без отдельного frozen-rule плана.
- Не продолжать wide-search усложнение модели без простой репликации.
- Не использовать post-entry diagnostic profiles для выбора политики.
