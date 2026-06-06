# label_main.py

## Назначение
CLI-оркестратор для полного конвейера подготовки данных: сортировка, маркировка, нормализация и разделение.

## Входные данные
- **Файл**: `MT/MQL4/Files/Nero.csv` (по умолчанию)
- **Формат**: CSV с разделителем `;`
- **Колонки**: `time`, `signal`, `predict`, `ATR`, `fractal0`...`fractal99`
- **Источник**: MetaTrader 4 (экспорт через `lib_PIC.mqh`)

## Выходные данные
- **Файл**: `DATA/{stem}_train_labeled.csv`
- **Файл**: `DATA/{stem}_validation_labeled.csv`
- **Файл**: `DATA/{stem}_test_labeled.csv`
- **Файл**: `DATA/{stem}_atr_scaler.pkl`
- **Файл**: `DATA/{stem}_normalization_stats.csv`
- **Файл**: `DATA/{stem}_train_updn_params.npy` — per-row per-pair `[brk, cap]` нормализации up/dn (5 пар), shape `(N_train, 5, 2)`
- **Файл**: `DATA/{stem}_validation_updn_params.npy` — аналогично для val, shape `(N_val, 5, 2)`
- **Файл**: `DATA/{stem}_test_updn_params.npy` — аналогично для test, shape `(N_test, 5, 2)`
- **Limit-order режим**: при `--limit-order` базовый путь выхода меняется на `DATA/limit_order/Nero_*`.

## Использование
```bash
# Полный pipeline
python label_main.py

# С указанием входного файла
python label_main.py --input MT/MQL4/Files/Nero.csv

# Режим отладки
python label_main.py --debug

# Без нормализации
python label_main.py --no-normalize

# С явным OHLC-файлом для path-ordered targets
python label_main.py --ohlc DATA/XAUUSD_H1_OHLC.csv

# Limit-order разметка: pending BUY/SELL LIMIT на Close[row]
python label_main.py --limit-order --spread 0.20

# Legacy-режим: predict в пуле front/back (воспроизведение старых экспериментов)
python label_main.py --input MT/MQL4/Files/Nero.csv --include-predict-in-front-back-pool
```

## CLI параметры

| Параметр | Назначение |
|---|---|
| `--input`, `-i` | Входной CSV, по умолчанию `MT/MQL4/Files/Nero.csv` |
| `--debug`, `-d` | Подробный отладочный вывод |
| `--no-normalize` | Пропустить rowwise/global нормализацию |
| `--include-predict-in-front-back-pool` | Legacy-режим: добавлять `|predict|` в пул нормализации `front/back` для воспроизведения старых экспериментов |
| `--ohlc` | H1 OHLC CSV для path-ordered Triple Barrier, entry_path и trailing-stop targets; по умолчанию `DATA/XAUUSD_H1_OHLC.csv` |
| `--limit-order` | Использовать limit-order Triple Barrier вместо immediate-entry Triple Barrier |
| `--spread` | Спред в price units для limit-order разметки, по умолчанию `0.0` |

## Ключевые функции
- `main()`: Точка входа, оркестрация этапов.
- `processing.fractal_preprocessing.sort_row_fractals()`: Парсинг и сортировка фракталов в строке.
- `processing.fractal_preprocessing.sort_fractals_in_dataframe()`: Применение сортировки ко всему датасету.
- `verify_sorting_quality()`: Проверка хронологии фракталов.
- `split_train_val_test()`: Разделение данных (70/15/15%).
- `save_datasets()`: Сохранение CSV файлов.

## Поток данных
1. **Загрузка**: Чтение Raw CSV (23 поля на фрактал).
2. **Сортировка**: Упорядочивание фракталов по времени (descending).
3. **Маркировка**: `label_all()` — signal + predict (forward-scan до пробоя/вытеснения).
4. **Up/Dn таргеты**: `label_updn()` — up_3..dn_48 для fractal0 каждой строки.
5. **Нормализация (Rowwise)**: `normalize.py` — признаки каждой строки + up/dn таргеты. Сохраняет per-row per-pair `[brk, cap]` (p85/p99 из фракталов, без таргетов). Для live-safe retrain не включать legacy-флаг `--include-predict-in-front-back-pool`, чтобы `predict`, рассчитанный из будущего, не менял масштаб `front/back`.
6. **Разделение**: Split на Train/Val/Test (70/15/15%).
7. **Нормализация (Global)**: RobustScaler для ATR (fit на train).
8. **Сохранение**: Запись выходных CSV + `*_updn_params.npy` (по одному на каждый split).
