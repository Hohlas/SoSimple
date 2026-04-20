# run_take_skip_lib_pic_feature_matrix.py

## Назначение

Отдельный исследовательский запуск обучения `take_skip_v2`, где модель получает два набора входов:

- последовательность фракталов `fractal0..fractal99`;
- производные признаки `lib_PIC`, собранные через `ML/lib_pic_feature_profiles.py`.

Цель этапа: проверить, даёт ли добавление признаков `lib_PIC` внутрь модели преимущество по сравнению с внешним отбором уже готовых prediction CSV.

## Входные данные

- `DATA/Nero_train_labeled.csv`
- `DATA/Nero_validation_labeled.csv`
- `DATA/Nero_test_labeled.csv`

CSV должны содержать исходные фракталы и колонки `take_skip_v2`, включая `trail_*_pnl_atr_x*`.

Runner поддерживает два формата `take_skip_v2`:

- старую сетку `x2/x4/x8`;
- расширенную сетку `x2/x4/x8/x10/x12`.

Если `--target-columns` не задан, используются только те цели, для которых в CSV реально есть source-колонки `trail_*_pnl_atr_x*`.

## Выходные данные

По каждой конфигурации создаётся каталог:

```text
ML/reports/take_skip_lib_pic_feature_matrix/<feature_profile>_seq<seq_len>/
```

Внутри:

- `checkpoint.pt` — лучший вес модели по validation loss;
- `take_skip_trailing_stop_v2_validation_predictions.csv`;
- `take_skip_trailing_stop_v2_test_predictions.csv`;
- `benchmark/validation_grid.csv`;
- `benchmark/final_verdict.json`;
- `summary.json`.

Общий файл:

- `ML/reports/take_skip_lib_pic_feature_matrix/manifest.json`.

## Проверяемые конфигурации

По умолчанию:

- профили признаков: `baseline_clean`, `baseline_clean_path`, `baseline_clean_geometry_path`;
- длины истории: `20`, `50`, `100`.

Это ограниченная сетка: она нужна для диагностики, а не для бесконтрольного перебора.

## Запуск

```bash
MPLCONFIGDIR=/tmp/matplotlib /home/hohla/git/SoSimple/.venv/bin/python \
  -m ML.run_take_skip_lib_pic_feature_matrix \
  --output-dir ML/reports/take_skip_lib_pic_feature_matrix \
  --feature-profiles baseline_clean baseline_clean_path baseline_clean_geometry_path \
  --seq-lens 20 50 100 \
  --epochs 10 \
  --patience 4 \
  --batch-size 256 \
  --min-pf 1.0 \
  --min-trades-per-year 6
```

Для принудительного запуска только старой сетки:

```bash
MPLCONFIGDIR=/tmp/matplotlib /home/hohla/git/SoSimple/.venv/bin/python \
  -m ML.run_take_skip_lib_pic_feature_matrix \
  --output-dir ML/reports/take_skip_lib_pic_feature_matrix \
  --feature-profiles baseline_clean baseline_clean_path baseline_clean_geometry_path \
  --seq-lens 20 50 100 \
  --target-columns take_12_x2 take_12_x4 take_12_x8 take_24_x2 take_24_x4 take_24_x8 take_48_x2 take_48_x4 take_48_x8 \
  --epochs 10 \
  --patience 4 \
  --batch-size 256 \
  --min-pf 1.0 \
  --min-trades-per-year 6
```

## Ограничения

- Это отдельный research runner, общий `ML.train` не меняется.
- Полная сетка читает большие CSV и обучает несколько моделей, поэтому её лучше запускать на удалённом сервере.
- Если в DATA нет `x10/x12`, это не ошибка: runner обучится только на доступных целях.
- Результат нужно оценивать не только по PF, но и по числу сделок в год, отрицательным годовым срезам и концентрации прибыли.
