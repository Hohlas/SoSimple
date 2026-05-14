# benchmark_entry_path_all_rows_ranking.py

`ML/benchmark_entry_path_all_rows_ranking.py` проверяет вариант
`entry_path_v1_live_safe`, где модель ранжирует все строки, а не только строки
с offline `signal != 0`.

## Назначение

Модуль нужен для проверки гипотезы:

```text
all rows -> direction from fractal0 -> score threshold -> trade
```

Порог выбирается только на validation. Test использует уже замороженный порог.

## Входы

По умолчанию:

- validation predictions:
  `ML/reports/entry_path_v1_live_safe_xauusd_no_predict_pool_server_multiseed/seed_042/validation_predictions.csv`
- validation source:
  `DATA/Nero_XAUUSD_validation_labeled.csv`
- test predictions:
  `ML/reports/entry_path_v1_live_safe_xauusd_no_predict_pool_server_multiseed/seed_042/test_predictions.csv`
- test source:
  `DATA/Nero_XAUUSD_test_labeled.csv`
- OHLC:
  `DATA/XAUUSD_H1_OHLC.csv`

Prediction CSV даёт score `pred_ret_24_dir_atr`. Source CSV даёт `fractal0`
и `ATR`. Результат сделки пересчитывается заново по OHLC для направления,
полученного из `fractal0.direction`.

## Выходы

По умолчанию:

```text
ML/reports/entry_path_v1_all_rows_ranking/
```

Файлы:

- `summary.json`
- `summary.md`
- `validation_summary.csv`
- `test_selected_rows.csv`

## Запуск

```bash
./.venv/bin/python -m ML.benchmark_entry_path_all_rows_ranking
```

## Ограничение

Это исследовательская проверка, а не production approval. Модель была обучена
на постановке с offline candidate-сигналом, поэтому all-rows результат требует
отдельного вывода и, при положительном результате, нового обучения или
forward-проверки.
