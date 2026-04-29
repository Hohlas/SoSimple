# online_causal_preprocessing.py

## Назначение
Live-safe подготовка runtime `Nero.csv` перед online inference.

## Входные данные
- Raw или snapshot CSV формата `Nero.csv`.

## Выходные данные
- CSV с теми же строками, где:
  - `fractal0..fractalN` отсортированы по времени убыванию;
  - сортировка проверена: `fractal_time[i] >= fractal_time[i+1]`;
  - признаки нормализованы через `processing.normalize.normalize_rowwise()`;
  - future-derived разметка не создаётся.

## Использование
```python
from processing.online_causal_preprocessing import preprocess_online_csv

preprocess_online_csv(
    input_csv="ML/reports/telemetry_frequency_v1/runtime/runtime_input_snapshot.csv",
    output_csv="ML/reports/telemetry_frequency_v1/runtime/runtime_input_preprocessed.csv",
)
```

## Ограничения
- Не вызывает `label_all()`, `label_updn()` и другие функции, которым нужны будущие строки.
- Ожидает, что вход содержит колонки, необходимые `normalize_rowwise()`: `time`, `signal`, `predict`, `ATR`, `fractal*`.
- По умолчанию вызывает `normalize_rowwise(verbose=False)`, чтобы watcher не
  засорял runtime log служебным progress-выводом.
- Если вход уже выглядит как rowwise-normalized snapshot, повторная
  нормализация пропускается. Это защищает от случайного двойного запуска
  preprocessing на `runtime_input_preprocessed.csv`.

## Ключевые функции
- `preprocess_online_frame(df, debug=False)` - сортировка, validation,
  rowwise-нормализация без future labels.
- `preprocess_online_csv(input_csv, output_csv, debug=False)` - файловая
  обёртка для watcher-а.
- `validate_fractal_sorting(df)` - проверяет убывающий порядок времени внутри
  `fractal*` колонок; равные timestamps допустимы.
