# fractal_preprocessing.py

## Назначение
Общая библиотечная сортировка фракталов внутри строки `Nero.csv`.

## Входные данные
- `pandas.DataFrame` с колонками `fractal0`...`fractalN`.

## Выходные данные
- `DataFrame`, где в каждой строке фракталы отсортированы по первому полю `fractal_time` в порядке убывания: свежие слева.

## Где используется
- `processing/label_main.py` — training/test pipeline.
- `processing/online_causal_preprocessing.py` — online preprocessing перед inference.

## Ограничения
- Сортировка независима по строкам.
- Будущие строки и future labels не используются.
