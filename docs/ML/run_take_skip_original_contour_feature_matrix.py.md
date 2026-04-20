# run_take_skip_original_contour_feature_matrix.py

## Назначение

Исследовательский runner для проверки `lib_PIC` path/geometry признаков в старом `take_skip_v2` контуре.

Главное отличие от `run_take_skip_lib_pic_feature_matrix.py`: здесь нет отдельной ветки модели для engineered-признаков. Все признаки добавляются в один sequence tensor:

- `fractal0..fractal99` парсятся в базовый tensor `(N, seq_len, 20)`;
- старые engineered-признаки повторяются на каждом шаге sequence;
- выбранные `lib_PIC` path/geometry признаки тоже повторяются на каждом шаге;
- `TransformerClassifier` получает один общий вход.

Цель: проверить, помогают ли новые признаки именно старому прибыльному контуру, а не новому dual-stream варианту.

## Входные данные

- `DATA/Nero_train_labeled.csv`
- `DATA/Nero_validation_labeled.csv`
- `DATA/Nero_test_labeled.csv`

CSV должны содержать:

- `time`, `signal`, `predict`, `ATR`;
- `fractal0..fractal99`;
- source-колонки `trail_*_pnl_atr_x*` для `take_skip_v2`.

Если `--target-columns` не задан, runner использует только цели, для которых в CSV есть соответствующие source-колонки.

## Режимы признаков

- `original_baseline` — старый baseline: multi-scale summaries по parsed fractals + старые row-wise признаки.
- `original_plus_path` — `original_baseline` + path-reaction признаки из `lib_PIC`.
- `original_plus_geometry_path` — `original_baseline` + path-reaction + geometry признаки.

Важно: `baseline_clean` здесь не используется как замена старого baseline. Новые признаки добавляются поверх исходного представления.

## Выходные данные

По каждой конфигурации создаётся каталог:

```text
ML/reports/take_skip_original_contour_feature_matrix/<feature_mode>_seq<seq_len>/
```

Внутри:

- `checkpoint.pt`;
- `take_skip_trailing_stop_v2_validation_predictions.csv`;
- `take_skip_trailing_stop_v2_test_predictions.csv`;
- `benchmark/validation_grid.csv`;
- `benchmark/final_verdict.json`;
- `summary.json`.

Общий файл:

- `ML/reports/take_skip_original_contour_feature_matrix/manifest.json`.

## Контрольный запуск

Сначала нужно проверить только `original_baseline_seq50`:

```bash
PYTHONUNBUFFERED=1 MPLCONFIGDIR=/tmp/matplotlib /home/hohla/git/SoSimple/.venv/bin/python \
  -m ML.run_take_skip_original_contour_feature_matrix \
  --output-dir ML/reports/take_skip_original_contour_feature_matrix_control \
  --feature-modes original_baseline \
  --seq-lens 50 \
  --epochs 10 \
  --patience 4 \
  --batch-size 256 \
  --min-pf 1.0 \
  --min-trades-per-year 6 \
  --jobs 1 \
  --torch-threads auto \
  --cpu-load 0.5 \
  --clear-cache \
  2>&1 | tee ML/reports/take_skip_original_contour_feature_matrix_control/run.log
```

Если контроль не воспроизводит старую прибыльную область, feature-addition matrix запускать нельзя: сначала нужно выяснить, чем восстановленный контур отличается от старого.

## Полная матрица

```bash
PYTHONUNBUFFERED=1 MPLCONFIGDIR=/tmp/matplotlib /home/hohla/git/SoSimple/.venv/bin/python \
  -m ML.run_take_skip_original_contour_feature_matrix \
  --output-dir ML/reports/take_skip_original_contour_feature_matrix \
  --feature-modes original_baseline original_plus_path original_plus_geometry_path \
  --seq-lens 20 50 100 \
  --epochs 10 \
  --patience 4 \
  --batch-size 256 \
  --min-pf 1.0 \
  --min-trades-per-year 6 \
  --jobs auto \
  --torch-threads auto \
  --cpu-load 0.5 \
  --clear-cache \
  2>&1 | tee ML/reports/take_skip_original_contour_feature_matrix/run.log
```

## Ограничения

- `--clear-cache` сохранён для симметрии с предыдущими командами, но runner читает CSV напрямую и не использует `.npy` cache.
- Это research runner; общий `ML.train` не меняется.
- Выбор winner-а делается по validation. Test используется только как frozen-проверка.
- Сравнение имеет смысл только если `original_baseline` сначала воспроизводит старую область результата.
