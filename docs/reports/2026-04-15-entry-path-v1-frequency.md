# Entry Path v1 Frequency

> **Date**: 2026-04-15
> **Status**: Partial
> **Goal**: Реализовать higher-frequency слой для `entry_path_v1`, добавить benchmark частоты/устойчивости и проверить, движется ли кандидат к диапазону `40-50` сделок в год при `PF > 2`.
> **Related plan/spec**: `docs/superpowers/plans/2026-04-15-higher-frequency-entry-path.md`
> **Related commit**: pending

## Context

План требовал расширить `entry_path_v1` frequency-oriented признаками, протащить их через train/eval/export pipeline, добавить feature screening и отдельный benchmark частоты/устойчивости. Целью было уйти от слишком редкого текущего режима без возврата к старому quantile-слою.

## What Was Done

- В `processing/label_signals.py` добавлен `add_entry_path_frequency_features()` с колонками `session_hour`, `weekday`, `range_atr_6`, `body_atr_3`, `ret_dir_atr_lag1`, `vol_regime_24`.
- В `processing/label_main.py` новый feature-builder подключён после `label_entry_path_targets()`.
- Добавлен `ML/feature_screen_entry_path.py` для ранжирования признаков по mutual information.
- Контракт `entry_path_v1` расширен canonical списком `ENTRY_PATH_V1_FEATURE_COLUMNS`.
- `ML/data_loader.py`, `ML/models/entry_path_transformer.py`, `ML/train.py`, `ML/evaluate_test.py`, `API/generate_signals.py` обновлены так, чтобы engineered features шли отдельным тензором от датасета до heads модели.
- В `ML/entry_path_task.py` report для active trades дополнен агрегатами `trades_per_year`, `PF`, `profit_concentration_top_10`, `negative_year_slices`.
- Добавлен новый benchmark `ML/benchmark_entry_path_v1_frequency.py` и его тест.
- Прогнан benchmark CLI на уже существующих prediction exports `ML/reports/entry_path_v1_validation_predictions.csv` и `ML/reports/entry_path_v1_test_predictions.csv`.

## Changed Files

- `processing/label_signals.py`
- `processing/label_main.py`
- `ML/feature_screen_entry_path.py`
- `ML/entry_path_task.py`
- `ML/data_loader.py`
- `ML/models/entry_path_transformer.py`
- `ML/train.py`
- `ML/evaluate_test.py`
- `API/generate_signals.py`
- `ML/benchmark_entry_path_v1_frequency.py`
- `tests/test_entry_path_labels.py`
- `tests/test_feature_screen_entry_path.py`
- `tests/test_entry_path_task.py`
- `tests/test_entry_path_model.py`
- `tests/test_entry_path_training.py`
- `tests/test_entry_path_reports.py`
- `tests/test_benchmark_entry_path_v1_frequency.py`

## Verification

- `./.venv/bin/python -m pytest tests/test_entry_path_labels.py tests/test_feature_screen_entry_path.py tests/test_entry_path_task.py tests/test_entry_path_model.py tests/test_entry_path_training.py tests/test_entry_path_reports.py tests/test_benchmark_entry_path_v1_frequency.py -q`
- Result: `26 passed`
- `./.venv/bin/python -m py_compile ML/entry_path_task.py ML/data_loader.py ML/models/entry_path_transformer.py ML/train.py ML/evaluate_test.py API/generate_signals.py ML/benchmark_entry_path_v1_frequency.py`
- `./.venv/bin/python -m ML.benchmark_entry_path_v1_frequency --validation-csv ML/reports/entry_path_v1_validation_predictions.csv --test-csv ML/reports/entry_path_v1_test_predictions.csv --output-dir ML/reports/entry_path_v1_frequency`

## Results

Benchmark на существующих prediction exports дал reject verdict:

- validation winner: `path6_prob`
- validation trades/year: `41.5`
- validation PF: `0.2185`
- validation negative_year_slices: `4`
- test trades/year: `96.0`
- test PF: `0.1900`
- test negative_year_slices: `5`

Артефакты benchmark записаны в:

- `ML/reports/entry_path_v1_frequency/validation_grid.csv`
- `ML/reports/entry_path_v1_frequency/test_grid.csv`
- `ML/reports/entry_path_v1_frequency/selected_candidate.json`
- `ML/reports/entry_path_v1_frequency/final_verdict.json`
- `ML/reports/entry_path_v1_frequency/run_metadata.json`

## Conclusions

Кодовая часть плана доведена до рабочего состояния и покрыта тестами, но исследовательская цель плана не подтверждена. На имеющихся historical prediction exports более частый кандидат не держит даже базовый `PF > 2`, хотя по частоте формально попадает в целевой диапазон на validation.

## Limitations / Open Questions

- План в текущем виде пропускает обязательный operational шаг: после добавления frequency-features нужно заново прогнать `processing/label_main.py`, иначе train/export не увидят новые колонки.
- В рабочем дереве отсутствуют `DATA/Nero_{train,validation,test}_labeled.csv`, поэтому full retrain/export по новому коду не был выполнен.
- Benchmark-артефакты выше рассчитаны на старых prediction CSV, а не на модели, переобученной с новыми feature columns.
- Task 5 про SHAP-review не запускался: без свежего viable candidate это не даёт надёжного сигнала.

## Next Step

1. Восстановить или сгенерировать `DATA/Nero_{train,validation,test}_labeled.csv` с новыми frequency-features через обновлённый `processing/label_main.py`.
2. Выполнить retrain `ML.train --task entry_path_v1`, затем `ML.evaluate_test` и `API.generate_signals` для свежих prediction exports.
3. Перезапустить `ML.benchmark_entry_path_v1_frequency` уже на новых exports.
4. Если verdict снова `reject`, пересмотреть сам selection layer или список frequency-features до запуска SHAP.

## Related Materials

- `docs/superpowers/plans/2026-04-15-higher-frequency-entry-path.md`
- `docs/superpowers/specs/2026-04-15-quantile-next-research-design.md`
- `ML/reports/entry_path_v1_validation_predictions.csv`
- `ML/reports/entry_path_v1_test_predictions.csv`
- `ML/reports/entry_path_v1_frequency/final_verdict.json`
