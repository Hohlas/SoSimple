# Current Feature Importance Diagnostics

Дата: 2026-04-19  
Ветка: `current-feature-importance-diagnostics`

## Цель

Проверить, какие группы уже экспортируемых признаков `Nero_*_labeled.csv` помогают объяснять торгово-близкую цель `trail_24_pnl_atr_x8`.

Это не новый training track и не торговый benchmark. Цель этапа — понять, куда копать во входных данных перед изменением `lib_PIC.mqh`.

## Метод

Добавлен read-only инструмент:

```bash
python -m ML.feature_importance_diagnostics \
  --target trail_24_pnl_atr_x8 \
  --output-dir ML/reports/current_feature_importance \
  --seq-len 20 \
  --max-train-rows 12000 \
  --max-validation-rows 6000 \
  --chunksize 5000 \
  --n-estimators 120
```

Модель диагностики: `RandomForestRegressor`, не нейросеть.

Признаки сгруппированы по смыслу:

- `price_position`;
- `direction`;
- `geometry`: `front`, `back`, `reverse`;
- `strength`: `strong`, `power`, `count`;
- `break_impulse`: `break`, `impulse`;
- `path_long`: `up_12/dn_12/up_24/dn_24/up_48/dn_48`;
- `path_short`: `up_3/dn_3/up_6/dn_6`;
- `atr`;
- `row_context`.

Важность группы считается через перестановку всей группы на validation: если после перемешивания качество падает, группа несёт полезный сигнал.

## Результат

Конфигурация:

- target: `trail_24_pnl_atr_x8`;
- train rows: `12000`;
- validation rows: `6000`;
- seq_len: `20`;
- feature count: `261`;
- validation R2: `0.058827`;
- validation MAE: `0.281213`;
- directional accuracy: `0.839344`.

Групповая важность:

| group | r2_drop | mae_increase | model_importance_sum |
|-------|--------:|-------------:|---------------------:|
| `geometry` | `0.220496` | `0.043171` | `0.458713` |
| `break_impulse` | `0.007426` | `0.002586` | `0.159924` |
| `row_context` | `0.003668` | `0.002456` | `0.029041` |
| `atr` | `0.000543` | `0.001359` | `0.027655` |
| `direction` | `-0.000088` | `-0.000005` | `0.001811` |
| `path_long` | `-0.000696` | `0.001068` | `0.106403` |
| `strength` | `-0.000829` | `0.000278` | `0.048519` |
| `price_position` | `-0.002289` | `-0.000477` | `0.051333` |
| `path_short` | `-0.005017` | `0.002293` | `0.116601` |

Top individual features:

- `front_last_w20`;
- `front_last_w10`;
- `front_last_w5`;
- `break_std_w10`;
- `back_max_w20`;
- `back_max_w5`;
- `break_std_w20`;
- `impulse_max_w20`;
- `dn_12_max_w20`;
- `impulse_last_w20`.

## Вывод

Главный сигнал идёт не от направления фрактала и не от сырых `Up/Dn`, а от геометрии уровня: прежде всего свежий `front` на окнах 5/10/20.

Это важный результат для следующего этапа:

- вероятно, стоит углублять признаки вокруг формы уровня: `front`, `back`, `reverse`, соотношения между ними, динамика по окнам;
- `break/impulse` тоже выглядит полезным вторым слоем;
- `direction` сам по себе почти ничего не даёт;
- `path_long/path_short` имеют модельную важность, но перестановочная проверка не подтвердила устойчивую пользу; к ним нужно относиться осторожно из-за риска смешать входные признаки с будущим результатом.

Абсолютное качество диагностической модели низкое (`R2 ~= 0.059`), поэтому это не доказательство сильной предсказуемости. Это карта приоритетов для проектирования новых входных признаков.

## Следующий шаг

Сделать feature-design spec вокруг геометрии уровня:

- соотношения `front/back`;
- асимметрия свежих уровней;
- изменение `front/back/reverse` по окнам 5/10/20/50;
- признаки с нормировкой на ATR;
- безопасные внутренние поля `lib_PIC`, которые уточняют геометрию уровня без будущего знания.
