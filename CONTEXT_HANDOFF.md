# Context Handoff

**Дата:** 2026-07-07

## Текущий этап

Этап `Entry-Based Fractal Sequence Transformer` завершён.

Итоговый structured artifact:

- `ML/reports/entry_based_sequence_transformer.json`
- `verdict = PIVOT_AMPLITUDE`
- verdict этапа: `DIAGNOSTIC_ONLY / PIVOT_AMPLITUDE`

Sequence Transformer не спас direction в текущей mechanics `entry-based next open`. Более точная граница вывода: текущая ограниченная матрица sequence-признаков/моделей не подтвердила объяснение “плоская таблица потеряла порядок 100 фракталов”. Это не закрывает глобально всю идею фрактальной последовательности. Amplitude trace снова сильнее и устойчивее direction.

## Главные артефакты

- `docs/reports/2026-07-07-entry-based-fractal-sequence-transformer.md`
- `docs/superpowers/plans/2026-07-06-entry-based-fractal-sequence-transformer.md`
- `ML/reports/entry_based_sequence_transformer.json`
- `ML/reports/entry_based_sequence_transformer_metrics.csv`
- `ML/reports/entry_based_sequence_transformer_rows.csv`
- `ML/reports/entry_based_sequence_transformer_tensor_audit.csv`
- `ML/reports/entry_based_sequence_transformer_run.log`
- `ML/baseline/benchmark_entry_based_sequence_transformer.py`
- `docs/ML/benchmark_entry_based_sequence_transformer.py.md`
- `tests/test_entry_based_sequence_transformer.py`

## Главный вывод

Технический контракт выполнен:

- `progress.done_runs = 9`
- `progress.total_runs = 9`
- `failed_runs = []`
- `elapsed_sec = 45477.6`
- `entry_based_smoke_check.status = PASS`
- `split_horizon_overlap_check.status = PASS`
- `tensor_audit.status = WARNING`
- `audit_decisions` записаны
- `normalization_contract.fit_split = train`
- `target_normalization_contract.fit_split = train`
- `run_config_hash = d2b6f0d61cab59409fe7c6b67406599643eb8c3d0b5524cb6f91552d8875fae0`
- `locked_test` не открыт
- `low_n_disclosure=2026` не использовался для verdict

Search width:

- 3 representations;
- 3 models;
- 1 seed;
- 4 horizons;
- 3 predicted target families;
- 108 metric comparisons.

По содержанию:

- лучший candidate direction: `nearest_k80_sequence / transformer_medium / entry_log_ratio H24`, `val_select=0.0539`, `val_eval=0.0050`;
- direction gate `0.10 / 0.05` не пройден;
- yearly check для выбранного direction не пройден;
- best-by-`val_eval` direction `nearest_k80_sequence / transformer_small / H24`, `val_select=0.0167`, `val_eval=0.0374`, это hindsight disclosure;
- лучший amplitude: `nearest_k60_sequence / sequence_flat_hist_gradient_boosting / entry_up H3`, `val_select=0.3229`, `val_eval=0.3337`;
- amplitude yearly diagnostics проходят.

## Следующий шаг

Следующий файл читать:

- `docs/reports/2026-07-07-entry-based-fractal-sequence-transformer.md`
- `docs/ML/benchmark_entry_based_sequence_transformer.py.md`
- `docs/superpowers/roadmap.md`

Ближайший честный исследовательский шаг: отдельный plan для `amplitude / movement-regime`.

Минимальная формулировка:

- не “торговать amplitude”, а сначала определить decision layer: movement/no-movement filter, горизонт, отдельный direction/exit слой;
- не использовать `entry_log_ratio` как главный target;
- не открывать `locked_test`;
- не выбирать по `low_n_disclosure=2026`;
- заранее раскрыть search width;
- обязательно включить `time_only_clean`, `no_time_sequence`, `no_price_coord_sequence`;
- добавить простые amplitude baselines: ATR-only, time-only, distance-to-level-only, last-N-fractal-counts-only;
- отдельно решить `tensor_audit=WARNING` по `price_coord_atr`: сколько значений обрезается, что меняется без этих признаков, и нужен ли другой tail-transform.

## Запрещённые направления

- Не трактовать `PIVOT_AMPLITUDE` как trading candidate.
- Не трактовать amplitude trace как подтверждённый direction signal.
- Не запускать direction freeze по текущей mechanics `entry-based next open`.
- Не выбирать winner по `val_eval` или `low_n_disclosure=2026`.
- Не открывать `locked_test` без отдельного frozen-rule плана.
- Не закрывать всю идею фрактальной последовательности глобально; закрыта только текущая ограниченная `entry-based next open` direction-ветка.
