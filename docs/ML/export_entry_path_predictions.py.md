# export_entry_path_predictions.py

## Назначение

`ML/export_entry_path_predictions.py` делает inference уже обученных
`entry_path` моделей на произвольном CSV без переобучения и без смены frozen
rules.

Модуль нужен для research- и benchmark-сценариев, где надо прогнать:

- `entry_path_v1`
- `entry_path_v1_quantile`

на новых split-файлах или новых инструментах, но сохранить тот же prediction contract, что используется в существующих benchmark/report pipelines.

## Поддерживаемые задачи

- `entry_path_v1`
- `entry_path_v1_quantile`

## Входные данные

- labeled CSV в формате `DATA/Nero_*_labeled.csv` для offline benchmark;
- live-safe runtime CSV после `processing.online_causal_preprocessing` для
  online watcher, если используется `--no-true-targets`;
- checkpoint:
  - `ML/checkpoints/transformer_entry_path_v1_best.pt`
  - или `ML/checkpoints/transformer_entry_path_v1_quantile_best.pt`

CSV для offline benchmark должен содержать:

- `time`
- `signal`
- `ATR`
- `fractal0..fractal99`
- entry-path target columns (`ret_*`, `fav_*`, `adv_*`, `path_6_class`)

Runtime CSV для watcher должен содержать минимум:

- `time`
- `signal`
- `ATR`
- `fractal0..fractal99`

При `--no-true-targets` future target columns не требуются и не пишутся в
prediction output как `true_*`.

## Что делает

1. Загружает input CSV.
2. Добавляет live-safe row features через `add_entry_path_frequency_features`:
   `session_hour`, `weekday`, `range_atr_6`, `body_atr_3`, `vol_regime_24`.
   `ret_dir_atr_lag1` не используется в profile `entry_path_v1_live_safe`.
3. Парсит fractal sequence в 3D tensor через существующий loader.
4. Для `entry_path_v1` дополнительно строит engineered feature profile.
5. Загружает frozen checkpoint.
6. Делает inference без shuffle и без retraining.
7. Пишет prediction CSV в том же контракте, который уже понимают:
   - benchmark-модули;
   - export-layer для MT4 `time;signal`.

## Запуск

```bash
./.venv/bin/python -m ML.export_entry_path_predictions \
  --task entry_path_v1 \
  --input-csv DATA/Nero_XAUUSD_test_labeled.csv \
  --checkpoint ML/checkpoints/transformer_entry_path_v1_best.pt \
  --output ML/reports/entry_path_cross_instrument_robustness/generated/XAUUSD_ALPARI/entry_path_v1_test_predictions.csv
```

Для quantile:

```bash
./.venv/bin/python -m ML.export_entry_path_predictions \
  --task entry_path_v1_quantile \
  --input-csv DATA/Nero_XAGUSD_test_labeled.csv \
  --checkpoint ML/checkpoints/transformer_entry_path_v1_quantile_best.pt \
  --output ML/reports/entry_path_cross_instrument_robustness/generated/XAGUSD/entry_path_v1_quantile_test_predictions.csv
```

Для online watcher:

```bash
./.venv/bin/python -m ML.export_entry_path_predictions \
  --task entry_path_v1 \
  --input-csv ML/reports/entry_path_v1_live_safe/runtime/runtime_input_preprocessed.csv \
  --checkpoint ML/reports/entry_path_v1_live_safe_xauusd_no_predict_pool_server_multiseed/seed_042/transformer_entry_path_v1_features_entry_path_v1_live_safe_best.pt \
  --feature-profile entry_path_v1_live_safe \
  --vol-regime-24-mode atr \
  --no-true-targets \
  --output ML/reports/entry_path_v1_live_safe/runtime/runtime_predictions.csv
```

`--vol-regime-24-mode`:

- `rolling` - training/offline default, сохраняет исходный контракт
  `vol_regime_24 = rolling_mean(ATR, 24 rows)`;
- `atr` - runtime compatibility mode: колонка `vol_regime_24` остаётся в том
  же месте feature vector, но заполняется текущим `ATR`.

Для текущего frozen checkpoint/rule режим `atr` проверен на validation/test:
выбранные сигналы не изменились (`signal_mismatch_rows=0`), поэтому watcher
может использовать latest-row inference без чтения 24 строк истории.

## Выходные данные

- prediction CSV с research-compatible колонками:
  - baseline `pred_ret_24_dir_atr`, `pred_path_*`
  - для quantile дополнительно `pred_ret_24_q10`, `pred_ret_24_q90`

## Ограничения

- Модуль не подбирает новые thresholds и не меняет frozen selection rules.
- Без `--no-true-targets` модуль ожидает уже подготовленный labeled CSV с
  полным набором entry-path target columns.
- `--no-true-targets` предназначен для online inference; он не подходит для
  расчёта offline метрик.
