# feature_bank_comparison_diagnostics.py

## Назначение

Сравнивает четыре набора входных признаков на одной read-only диагностике:

- `baseline`;
- `baseline + geometry-bank`;
- `baseline + path-reaction-bank`;
- `baseline + geometry-bank + path-reaction-bank`.

Цель — быстро понять, дают ли новые feature-bank дополнительную информацию сверх уже существующих агрегатов, до запуска нового training track.

## Входные данные

- `DATA/Nero_train_labeled.csv`
- `DATA/Nero_validation_labeled.csv`

CSV читается чанками через существующий `load_sample()`.

## Выходные данные

```text
ML/reports/feature_bank_comparison/summary.csv
ML/reports/feature_bank_comparison/summary.json
ML/reports/feature_bank_comparison/report.md
```

## Использование

```bash
python -m ML.feature_bank_comparison_diagnostics \
  --target trail_24_pnl_atr_x8 \
  --seq-len 20 \
  --max-train-rows 12000 \
  --max-validation-rows 6000 \
  --n-estimators 80
```

## Метод

Для каждого варианта обучается лёгкая `RandomForestRegressor` с одинаковыми параметрами и одинаковой выборкой.

Метрики:

- validation R2;
- validation MAE;
- directional accuracy.

## Ограничения

- Это не торговый benchmark.
- Это не новое обучение нейросети.
- Хороший результат здесь означает только, что признаки несут дополнительную информацию для выбранной цели.
- Перед production-выводами нужен validation-first trading benchmark и frozen test check.
