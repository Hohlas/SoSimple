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
- `process_row_fractals()`: Парсинг и сортировка фракталов в строке.
- `sort_fractals_in_dataframe()`: Применение сортировки ко всему датасету.
- `verify_sorting_quality()`: Проверка хронологии фракталов.
- `split_train_val_test()`: Разделение данных (70/15/15%).
- `save_datasets()`: Сохранение CSV файлов.

## Поток данных
1. **Загрузка**: Чтение Raw CSV (18 полей на фрактал).
2. **Сортировка**: Упорядочивание фракталов по времени (descending).
3. **Маркировка**: `label_all()` — signal + predict (forward-scan до пробоя/вытеснения).
4. **Up/Dn таргеты**: `label_updn()` — up_12..dn_48 для fractal0 каждой строки.
5. **Нормализация (Rowwise)**: `normalize.py` — признаки каждой строки (не затрагивает up/dn).
6. **Разделение**: Split на Train/Val/Test (70/15/15%).
7. **Нормализация (Global)**: RobustScaler для ATR (fit на train).
8. **Сохранение**: Запись выходных CSV.
