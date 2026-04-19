# Feature Bank Clean Comparison

Дата: 2026-04-19  
Ветка: `feature-bank-clean-comparison`

## Цель

Проверить гипотезу, что старый baseline стоит не только расширять, но и чистить от слабых/шумных групп признаков.

Сравнивались:

- `baseline_full`;
- `baseline_clean`;
- `baseline_full_path`;
- `baseline_clean_path`;
- `baseline_clean_geometry_path`.

## Clean-логика

`baseline_clean` удаляет из текущих grouped features:

- `direction`;
- `price_position`;
- `path_long`;
- `path_short`.

Причина:

- `direction` и `price_position` выглядели слабо в importance diagnostics;
- raw `path_long/path_short` дублируют смысл `Up/Dn`, но хуже выражены, чем новый `path-reaction-bank`;
- цель clean-варианта — уменьшить шум и риск подгонки.

## Метод

Команда:

```bash
python -m ML.feature_bank_comparison_diagnostics \
  --target trail_24_pnl_atr_x8 \
  --output-dir ML/reports/feature_bank_clean_comparison \
  --seq-len 20 \
  --max-train-rows 12000 \
  --max-validation-rows 6000 \
  --chunksize 5000 \
  --n-estimators 80
```

Модель диагностики: `RandomForestRegressor`.

Это read-only диагностика, не trading benchmark и не новое нейрообучение.

## Результат

| variant | feature_count | validation_r2 | validation_mae | directional_accuracy |
|---------|--------------:|--------------:|---------------:|---------------------:|
| `baseline_clean` | 117 | `0.083736` | `0.238819` | `0.842623` |
| `baseline_clean_path` | 422 | `0.081836` | `0.250021` | `0.836066` |
| `baseline_clean_geometry_path` | 567 | `0.076765` | `0.249481` | `0.829508` |
| `baseline_full_path` | 566 | `0.074359` | `0.267621` | `0.839344` |
| `baseline_full` | 261 | `0.060763` | `0.280381` | `0.836066` |

## Вывод

Самый сильный результат дала не добавка feature-bank, а чистка baseline.

`baseline_clean`:

- уменьшил число признаков с `261` до `117`;
- дал лучший R2;
- дал лучший MAE;
- дал лучшую directional accuracy.

Новые feature-bank остаются полезными как кандидаты, но по этой диагностике они не должны быть первым вариантом в training track. Приоритет меняется:

1. `baseline_clean`;
2. `baseline_clean_path`;
3. `baseline_clean_geometry_path`;
4. `baseline_full` как контроль.

## Практическое решение

Следующий bounded training/benchmark должен начинаться с `baseline_clean`, а не с `baseline_full + все новые признаки`.

Минимальный набор вариантов для обучения:

- `baseline_full`;
- `baseline_clean`;
- `baseline_clean_path`;
- `baseline_clean_geometry_path`.

Если `baseline_clean` выиграет и в торговом benchmark, это будет сильный аргумент, что часть старых признаков ухудшала модель.
