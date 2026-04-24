# export_entry_path_predictions.py

## Назначение

`ML/export_entry_path_predictions.py` делает inference уже обученных `entry_path` моделей на произвольном labeled CSV без переобучения и без смены frozen rules.

Модуль нужен для research- и benchmark-сценариев, где надо прогнать:

- `entry_path_v1`
- `entry_path_v1_quantile`

на новых split-файлах или новых инструментах, но сохранить тот же prediction contract, что используется в существующих benchmark/report pipelines.

## Поддерживаемые задачи

- `entry_path_v1`
- `entry_path_v1_quantile`

## Входные данные

- labeled CSV в формате `DATA/Nero_*_labeled.csv`
- checkpoint:
  - `ML/checkpoints/transformer_entry_path_v1_best.pt`
  - или `ML/checkpoints/transformer_entry_path_v1_quantile_best.pt`

CSV должен содержать:

- `time`
- `signal`
- `ATR`
- `fractal0..fractal99`
- entry-path target columns (`ret_*`, `fav_*`, `adv_*`, `path_6_class`)

## Что делает

1. Загружает labeled CSV.
2. Парсит fractal sequence в 3D tensor через существующий loader.
3. Для `entry_path_v1` дополнительно строит engineered feature profile.
4. Загружает frozen checkpoint.
5. Делает inference без shuffle и без retraining.
6. Пишет prediction CSV в том же контракте, который уже понимают:
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

## Выходные данные

- prediction CSV с research-compatible колонками:
  - baseline `pred_ret_24_dir_atr`, `pred_path_*`
  - для quantile дополнительно `pred_ret_24_q10`, `pred_ret_24_q90`

## Ограничения

- Модуль не подбирает новые thresholds и не меняет frozen selection rules.
- Он ожидает уже подготовленный labeled CSV с полным набором entry-path target columns.
- Если в input-файле нет этих колонок, ошибка должна исправляться на уровне data preparation, а не через silent fallback внутри inference.
