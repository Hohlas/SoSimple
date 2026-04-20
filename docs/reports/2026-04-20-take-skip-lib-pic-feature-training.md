# Take/Skip lib_PIC Feature Training

Дата: 2026-04-20
Ветка: `lib-pic-feature-training-track`
Статус: completed
Related commit: pending

## Цель

Проверить, помогает ли добавление производных признаков `lib_PIC` внутрь модели `take_skip_v2`.

Предыдущий этап показал, что `lib_PIC`-признаки могут быть полезны как внешний фильтр. Этот этап проверял более сильную гипотезу: сможет ли модель сама использовать эти признаки при обучении и дать лучший торговый отбор.

## Метод

Добавлен отдельный research runner:

- `ML/run_take_skip_lib_pic_feature_matrix.py`;
- `ML/models/take_skip_dual_stream_transformer.py`;
- `tests/test_take_skip_lib_pic_feature_matrix.py`;
- `docs/ML/run_take_skip_lib_pic_feature_matrix.py.md`.

Модель получает два входа:

- последовательность фракталов `fractal0..fractal99`;
- профиль производных признаков `lib_PIC`.

Проверенная сетка:

| profile | seq_len |
|---|---|
| `baseline_clean` | 20 / 50 / 100 |
| `baseline_clean_path` | 20 / 50 / 100 |
| `baseline_clean_geometry_path` | 20 / 50 / 100 |

Данные на момент запуска содержали старую сетку `take_skip_v2`:

- `take_12_x2`, `take_12_x4`, `take_12_x8`;
- `take_24_x2`, `take_24_x4`, `take_24_x8`;
- `take_48_x2`, `take_48_x4`, `take_48_x8`.

Runner был исправлен так, чтобы автоматически использовать только те цели, для которых в CSV есть source-колонки `trail_*_pnl_atr_x*`.

Полный серверный запуск:

```bash
PYTHONUNBUFFERED=1 MPLCONFIGDIR=/tmp/matplotlib python \
  -m ML.run_take_skip_lib_pic_feature_matrix \
  --output-dir ML/reports/take_skip_lib_pic_feature_matrix \
  --feature-profiles baseline_clean baseline_clean_path baseline_clean_geometry_path \
  --seq-lens 20 50 100 \
  --epochs 10 \
  --patience 4 \
  --batch-size 256 \
  --min-pf 1.0 \
  --min-trades-per-year 6 \
  --jobs 4 \
  --torch-threads 4
```

Runtime: `3123.32 sec` (~52 min).

## Результаты

Все 9 конфигураций получили `verdict=reject`.

| run | verdict | best_epoch | best_bce |
|---|---|---:|---:|
| `baseline_clean_seq20` | reject | 8 | 0.031465 |
| `baseline_clean_seq50` | reject | 7 | 0.031599 |
| `baseline_clean_seq100` | reject | 8 | 0.031356 |
| `baseline_clean_path_seq20` | reject | 10 | 0.031820 |
| `baseline_clean_path_seq50` | reject | 10 | 0.031805 |
| `baseline_clean_path_seq100` | reject | 7 | 0.032048 |
| `baseline_clean_geometry_path_seq20` | reject | 10 | 0.033288 |
| `baseline_clean_geometry_path_seq50` | reject | 7 | 0.033735 |
| `baseline_clean_geometry_path_seq100` | reject | 10 | 0.033097 |

Главная причина reject:

```text
validation grid rows: 1377
PF > 1 rows: 79
PF > 1 and trades_per_year >= 6: 0
```

То есть редкие точки с `PF > 1` есть, но они дают слишком мало сделок.

Лучшие редкие validation-точки:

| run | target | selector | trades/year | validation PF | test PF |
|---|---|---|---:|---:|---:|
| `baseline_clean_path_seq20` | `take_48_x8` | `top_k=0.5%` | 0.75 | 20.96 | inf |
| `baseline_clean_path_seq20` | `take_48_x8` | `top_k=1%` | 1.25 | 9.28 | inf |
| `baseline_clean_path_seq50` | `take_24_x8` | `top_k=0.5%` | 0.75 | 8.50 | inf |

Эти точки нельзя считать практическими: 3-5 сделок за весь validation.

Лучшие строки при минимальной частоте `trades_per_year >= 6`:

| run | target | selector | trades/year | validation PF |
|---|---|---|---:|---:|
| `baseline_clean_seq20` | `take_12_x2` | `top_k=5%` | 6.0 | 0.9476 |
| `baseline_clean_seq100` | `take_12_x2` | `top_k=5%` | 6.0 | 0.9020 |
| `baseline_clean_seq20` | `take_24_x2` | `top_k=5%` | 6.0 | 0.8416 |
| `baseline_clean_path_seq100` | `take_12_x2` | `top_k=10%` | 12.0 | 0.8350 |

## Выводы

`lib_PIC`-признаки внутри этой модели не дали торгового улучшения.

Фактическая картина:

- `baseline_clean_path` лучше всего ловит очень редкие хорошие сделки;
- при расширении потока до хотя бы 6 сделок/год PF падает ниже 1;
- `baseline_clean_geometry_path` не улучшил результат;
- простой `baseline_clean` оказался ближе всего к рабочей частоте, но тоже не прошёл `PF > 1`.

Практический вывод: в текущем виде `lib_PIC`-признаки полезнее как внешний слой отбора, чем как простая добавка во вход модели.

## Важное ограничение интерпретации

Этот прогон не является строгим повторением старой прибыльной `take_skip_v2` модели.

Отличия:

- использован новый dual-stream runner;
- обучение шло по доступной старой сетке `x2/x4/x8`, без `x10/x12`;
- проверялись очищенные `lib_PIC`-профили, а не полный исходный baseline feature set;
- оптимизация всё ещё идёт по BCE, а торговый выбор оценивается уже после обучения через PF / trades per year.

Поэтому нельзя утверждать: “новые признаки испортили старую модель”.

Корректный вывод: “в новом training contour простое добавление `lib_PIC`-профилей внутрь модели не создало рабочий selection layer”.

## Возможные причины провала

1. Целевая функция обучения не совпадает с торговой целью.

Модель учится улучшать среднюю бинарную ошибку по всем строкам, а торговый успех зависит от качества верхнего хвоста ранжирования. Если верхние 5-10% предсказаний ранжируются плохо, PF будет слабым даже при нормальном BCE.

2. Положительные события редкие.

`best_bce` около `0.031-0.034` говорит, что задача сильно несбалансирована. В такой ситуации модель может хорошо предсказывать “не брать”, но плохо выделять достаточно широкий поток хороших входов.

3. Внешний фильтр и вход модели решают разные задачи.

Внешний фильтр жёстко отсекает сделки по понятному правилу после того, как основной score уже найден. Добавление тех же признаков внутрь модели не гарантирует, что модель будет использовать их именно как фильтр устойчивости.

4. Очищенный профиль мог убрать контекст, который нужен новым признакам.

`baseline_clean` сам по себе был разумным сокращением, но новые path/geometry-признаки могут работать только вместе с частью старого полного контекста. Это нужно проверить отдельным controlled ablation.

5. Сравнение пока не полностью “яблоко к яблоку”.

Старый сильный результат был получен в другом training/export контуре. Перед окончательным выводом по признакам нужно воспроизвести старый baseline в том же runner-е или добавить новые признаки к исходному baseline-контракту.

## Следующий шаг

Проверить гипотезу пользователя: “добавить новые признаки к исходному baseline”.

Делать это нужно не как один большой blind run, а как controlled ablation:

1. Воспроизвести исходный прибыльный baseline в максимально близком к старому контуре.
2. Добавить к нему только сильные `lib_PIC` path-признаки.
3. Отдельно проверить полный набор `baseline + path + geometry`.
4. Сравнивать только validation-first:
   - `PF`;
   - `trades_per_year`;
   - `negative_year_slices`;
   - `profit_concentration_top_10`;
   - сохранение результата на frozen test.

Если исходный baseline воспроизводится, а `baseline + lib_PIC` не улучшает его, направление “добавлять признаки внутрь модели” можно закрывать. Если улучшает — тогда стоит переобучать уже расширенный production-кандидат.

## Артефакты

- `ML/reports/take_skip_lib_pic_feature_matrix/manifest.json`
- `ML/reports/take_skip_lib_pic_feature_matrix/*/summary.json`
- `ML/reports/take_skip_lib_pic_feature_matrix/*/benchmark/final_verdict.json`
- `ML/reports/take_skip_lib_pic_feature_matrix/*/benchmark/validation_grid.csv`
