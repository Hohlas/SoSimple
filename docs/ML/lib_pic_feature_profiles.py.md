# lib_pic_feature_profiles.py

## Назначение

Собирает именованные профили признаков `lib_PIC` из уже готовых fractal-колонок.

Цель — чтобы диагностика признаков и последующее обучение использовали один и тот же код сборки, а не две похожие реализации.

## Профили

- `baseline_full` — все компактные группы из текущих fractal-полей.
- `baseline_clean` — тот же baseline, но без групп `direction`, `price_position`, `path_long`, `path_short`.
- `baseline_full_path` — полный baseline плюс признаки исторической реакции цены `Up/Dn`.
- `baseline_clean_path` — очищенный baseline плюс признаки `Up/Dn`.
- `baseline_clean_geometry_path` — очищенный baseline плюс `Up/Dn` и геометрия уровней.

## Входные данные

`pandas.DataFrame` с колонками:

- `fractal0..fractalN`;
- опционально: `ATR`, `session_hour`, `weekday`, `range_atr_6`, `body_atr_3`, `ret_dir_atr_lag1`, `vol_regime_24`.

## Выходные данные

`pandas.DataFrame` с числовыми признаками выбранного профиля. Индекс строк сохраняется.

## Использование

```python
from ML.lib_pic_feature_profiles import build_lib_pic_feature_profile

features = build_lib_pic_feature_profile(
    frame,
    profile='baseline_clean',
    seq_len=20,
)
```

Для `entry_path_v1` профиль можно выбрать при обучении:

```bash
python -m ML.train \
  --model entry_path_dual_stream \
  --task entry_path_v1 \
  --entry_path_feature_profile baseline_clean \
  --seq_len 20 \
  --clear_cache
```

## Ограничения

- Модуль не читает CSV и не запускает обучение.
- `baseline_clean` — диагностически лучший профиль на короткой проверке, но не торговый вывод сам по себе.
- Для `take_skip_v2` отдельный поток инженерных признаков пока не подключён; этот профиль сейчас напрямую подключён к `entry_path_v1`.
