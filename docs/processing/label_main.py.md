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
- **Файл**: `DATA/{stem}_train_updn_params.npy` — per-row `[brk, cap]` нормализации up/dn, shape `(N_train, 2)`
- **Файл**: `DATA/{stem}_validation_updn_params.npy` — аналогично для val, shape `(N_val, 2)`
- **Файл**: `DATA/{stem}_test_updn_params.npy` — аналогично для test, shape `(N_test, 2)`

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
```

## Ключевые функции
- `main()`: Точка входа, оркестрация этапов.
- `processing.fractal_preprocessing.sort_row_fractals()`: Парсинг и сортировка фракталов в строке.
- `processing.fractal_preprocessing.sort_fractals_in_dataframe()`: Применение сортировки ко всему датасету.
- `verify_sorting_quality()`: Проверка хронологии фракталов.
- `split_train_val_test()`: Разделение данных (70/15/15%).
- `save_datasets()`: Сохранение CSV файлов.

## Поток данных
1. **Загрузка**: Чтение Raw CSV (22 поля на фрактал).
2. **Сортировка**: Упорядочивание фракталов по времени (descending).
3. **Маркировка**: `label_all()` — signal + predict (forward-scan до пробоя/вытеснения).
4. **Up/Dn таргеты**: `label_updn()` — up_3..dn_48 для fractal0 каждой строки.
5. **Нормализация (Rowwise)**: `normalize.py` — признаки каждой строки + up/dn таргеты. Сохраняет per-row `[brk, cap]` (p85/p99 из пула 606 значений).
6. **Разделение**: Split на Train/Val/Test (70/15/15%).
7. **Нормализация (Global)**: RobustScaler для ATR (fit на train).
8. **Сохранение**: Запись выходных CSV + `*_updn_params.npy` (по одному на каждый split).
