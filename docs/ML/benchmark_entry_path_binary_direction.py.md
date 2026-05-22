# benchmark_entry_path_binary_direction.py

## Назначение
Validation-first benchmark для direct-direction BUY/SELL binary моделей. Обучает две независимые модели `BUY-vs-REST` и `SELL-vs-REST`, строит grid по порогам и margin rule, считает side-specific PF и sequential PF.

## Входы
- `DATA/Nero_XAUUSD_train_labeled.csv` и `DATA/Nero_XAUUSD_validation_labeled.csv` — train/validation target и фрактальные поля.
- `MT/MQL4/Files/Nero.csv` через `--raw-feature-source` — raw/current-row price source для расчёта distance/ATR. Читаются только первые train+validation строки.
- `DATA/XAUUSD_H1_OHLC.csv` — Target D и PnL validation.
- validation prediction CSV — только diagnostic score для `old_score_diagnostic`, не primary selection.

## Выходы
- `validation_grid.csv` — полный validation grid.
- `summary.json` — итог validation stage.
- `selection_decision.json` — машинно-воспроизводимое решение по winner.
- `feature_manifest.json` — разделение `feature_source`, `target_source`, `diagnostic_source`.
- `side_policy_summary.json` — BUY/SELL/combined gate summary для текущего stage artifact.

## Selection policy
Primary metric: `validation_sequential_pf`. Candidate должен быть `standalone`, иметь минимум 100 сделок, `validation_pf >= 1.15`, `validation_sequential_pf >= 1.10`, `negative_years == 0`, `one_sided_candidate == False`, `overfitting_risk == False`.

Если выбран не automatic winner, нужен explicit reason в `selection_decision.json`. Frozen test не должен запускаться без заранее выбранного validation winner.

## Использование
```bash
./.venv/bin/python -m ML.benchmark_entry_path_binary_direction \
  --stage validation-matrix \
  --output-dir ML/reports/direct_direction_corrected_validation_baseline \
  --train-source DATA/Nero_XAUUSD_train_labeled.csv \
  --validation-source DATA/Nero_XAUUSD_validation_labeled.csv \
  --validation-predictions ML/reports/entry_path_v1_live_safe_xauusd_no_predict_pool_server_multiseed/seed_042/validation_predictions.csv \
  --ohlc DATA/XAUUSD_H1_OHLC.csv \
  --raw-feature-source MT/MQL4/Files/Nero.csv \
  --k 4
```

## Ограничения
Test split не используется для selection. `--stage frozen-test` допустим только после final validation winner.
