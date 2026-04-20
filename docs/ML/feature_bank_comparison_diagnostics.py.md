# feature_bank_comparison_diagnostics.py

## Назначение

Сравнивает несколько наборов входных признаков на одной read-only диагностике:

- `baseline_full`;
- `baseline_clean`;
- `baseline_full + path-reaction-bank`;
- `baseline_clean + path-reaction-bank`;
- `baseline_clean + geometry-bank + path-reaction-bank`.

Цель — быстро понять, дают ли чистка старых групп и новые feature-bank дополнительную информацию сверх уже существующих агрегатов, до запуска нового training track.

Сборка профилей вынесена в общий модуль [`ML/lib_pic_feature_profiles.py`](../../ML/lib_pic_feature_profiles.py), чтобы диагностика и обучение `entry_path_v1` использовали одинаковую логику признаков.

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

Для clean-сравнения можно указать отдельный `--output-dir`, например:

```text
ML/reports/feature_bank_clean_comparison/
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
- Хороший результат здесь означает только, что признаки или чистка признаков улучшают диагностику выбранной цели.
- Перед production-выводами нужен validation-first trading benchmark и frozen test check.
