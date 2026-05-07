# run_entry_path_live_safe_retrain.py

`ML/run_entry_path_live_safe_retrain.py` запускает полный проверочный контур
для `entry_path_v1_live_safe` по одному или нескольким seed:

1. обучение `ML.train` с отдельным `--output-dir` для seed;
2. export validation/test predictions из seed-specific checkpoint;
3. `benchmark_entry_path_trade_filter`;
4. сводная таблица `multi_seed_summary.csv/json`.

## Входы

- `DATA/Nero_train_labeled.csv`
- `DATA/Nero_validation_labeled.csv`
- `DATA/Nero_test_labeled.csv`

Перед запуском важно убедиться, что `DATA/Nero_*` указывают на H1 XAUUSD
split, а не на M5 `Nero.csv`.

## Выходы

Для каждого seed создаётся папка `seed_XXX/`:

- `transformer_entry_path_v1_features_entry_path_v1_live_safe_best.pt`;
- `validation_predictions.csv`;
- `test_predictions.csv`;
- `entry_path_trade_filter_selected_rule.json`;
- `entry_path_trade_filter_validation_summary.csv`;
- `entry_path_trade_filter_test_summary.csv`;
- `summary.json`.

В корне `--output-dir`:

- `multi_seed_summary.csv`;
- `multi_seed_summary.json`;
- `manifest.json`.

## Пример

```bash
./.venv/bin/python -m ML.run_entry_path_live_safe_retrain \
  --output-dir ML/reports/entry_path_v1_live_safe_xauusd_no_predict_pool_server_multiseed \
  --seeds 7 17 42 77 123 \
  --epochs 5 \
  --batch-size 256 \
  --clear-cache
```

По умолчанию используется coverage grid для baseline `A`:
`0.05 0.075 0.10 0.125 0.15 0.20 0.25 0.30`.

## Назначение

Этот runner нужен для закрытия риска, когда общий
`ML/checkpoints/*_best.pt` перетирается следующим обучением. Каждый seed
экспортируется только из своего checkpoint.
