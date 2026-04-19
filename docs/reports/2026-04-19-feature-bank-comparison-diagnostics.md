# Feature Bank Comparison Diagnostics

Дата: 2026-04-19  
Ветка: `feature-bank-comparison-diagnostics`

## Цель

Проверить, дают ли новые feature-bank дополнительную информацию сверх текущего baseline-набора признаков.

Сравнивались четыре варианта:

- `baseline`;
- `baseline_geometry`;
- `baseline_path`;
- `baseline_geometry_path`.

Это read-only диагностика, не торговый benchmark и не новое нейрообучение.

## Метод

Команда:

```bash
python -m ML.feature_bank_comparison_diagnostics \
  --target trail_24_pnl_atr_x8 \
  --output-dir ML/reports/feature_bank_comparison \
  --seq-len 20 \
  --max-train-rows 12000 \
  --max-validation-rows 6000 \
  --chunksize 5000 \
  --n-estimators 80
```

Модель диагностики: `RandomForestRegressor`.

Цель: `trail_24_pnl_atr_x8`.

## Результат

| variant | feature_count | validation_r2 | validation_mae | directional_accuracy |
|---------|--------------:|--------------:|---------------:|---------------------:|
| `baseline_path` | 566 | `0.074359` | `0.267621` | `0.839344` |
| `baseline_geometry_path` | 711 | `0.072829` | `0.261340` | `0.832787` |
| `baseline_geometry` | 406 | `0.069316` | `0.266884` | `0.826230` |
| `baseline` | 261 | `0.060763` | `0.280381` | `0.836066` |

## Вывод

Оба новых слоя добавляют информацию сверх baseline:

- `path-reaction-bank` дал лучший R2 и лучшую directional accuracy;
- `geometry-bank` тоже улучшил R2 и MAE относительно baseline;
- сочетание `geometry + path` дало лучший MAE, но не лучший R2.

Абсолютное качество всё ещё невысокое: R2 остаётся около `0.06–0.07`. Поэтому это не доказательство торговой пригодности. Но как диагностика входов результат полезен: новые feature-bank не выглядят мусорными и заслуживают bounded training/benchmark проверки.

## Практическое решение

Следующий training/benchmark track должен сравнить минимум три варианта:

- текущий baseline;
- baseline + path-reaction-bank;
- baseline + geometry + path-reaction-bank.

`geometry-only` можно оставить как контрольный вариант, но приоритет ниже: по этой диагностике `path-reaction` сильнее.

## Риск

Чем больше feature-bank, тем выше риск подгонки. Поэтому следующий этап должен быть строго bounded:

- заранее фиксированный набор вариантов;
- отбор только на validation;
- test только один раз как frozen check;
- обязательно смотреть не только R2/BCE, но и торговые метрики: PF, сделки в год, просадка, концентрация прибыли, отрицательные годы.
