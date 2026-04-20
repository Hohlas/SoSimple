# benchmark_take_skip_lib_pic_selection.py

## Назначение

Read-only benchmark внешнего слоя отбора для уже готовых `take_skip_trailing_stop_v2` prediction CSV.

Модуль проверяет, можно ли улучшить или стабилизировать текущие `quality` / `frequency` правила, добавив простые фильтры по производным признакам `lib_PIC`.

## Входные данные

- validation/test prediction CSV `take_skip_trailing_stop_v2`;
- validation/test source CSV с `fractal0..fractal99`;
- профиль признаков из [`ML/lib_pic_feature_profiles.py`](../../ML/lib_pic_feature_profiles.py).

## Выходные данные

```text
ML/reports/take_skip_lib_pic_selection/validation_grid.csv
ML/reports/take_skip_lib_pic_selection/final_verdict.json
```

## Логика

1. Prediction CSV соединяется с source CSV строго по порядку строк и колонке `time`.
2. На source CSV строятся признаки `lib_PIC`.
3. На validation перебирается ограниченная сетка:
   - score-target: например `take_24_x8`, `take_24_x4`;
   - selector: `prob_ge_threshold` или `top_k_probability`;
   - exit PnL: например `x8`, `x10`;
   - внешний фильтр: `feature >= validation_quantile`.
4. Победитель выбирается только на validation.
5. На test применяется тот же score-selector и тот же числовой порог признака, без пересчёта по test.

## Команда

```bash
MPLCONFIGDIR=/tmp/matplotlib /home/hohla/git/SoSimple/.venv/bin/python \
  -m ML.benchmark_take_skip_lib_pic_selection \
  --validation-predictions ML/reports/take_skip_trailing_stop_v2_followup_tmp/seq50_exports/validation.csv \
  --test-predictions ML/reports/take_skip_trailing_stop_v2_followup_tmp/seq50_exports/test.csv \
  --validation-source DATA/Nero_validation_labeled.csv \
  --test-source DATA/Nero_test_labeled.csv \
  --output-dir ML/reports/take_skip_lib_pic_selection \
  --seq-len 100 \
  --score-target take_24_x8 \
  --score-target take_24_x4 \
  --eval-x 8 \
  --eval-x 10 \
  --min-pf 1.0 \
  --min-trades-per-year 6
```

## Ограничения

- Это не обучение и не дообучение модели.
- Фильтры проверяются как внешний слой отбора поверх готовых вероятностей.
- Если фильтр выигрывает, это аргумент для последующего переобучения на новых признаках, но не замена переобучения.
