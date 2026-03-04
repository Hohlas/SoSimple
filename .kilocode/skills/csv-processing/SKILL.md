---
name: csv-processing
description: Use when working with CSV files - reading, exploring, analyzing large datasets
triggers:
  - csv file
  - read csv
  - large csv
  - sampling csv
  - читать csv
  - большой csv
  - анализ csv
  - обработка csv
applies_to:
  - "**/*.csv"
alwaysApply: false
---

# Работа с CSV файлами

## Overview

CSV файлы часто содержат большие объёмы данных. Неправильная обработка приводит к:
- Переполнению контекста (token limit)
- Высокому потреблению памяти
- Медленной работе

**Ключевые принципы обработки CSV:**
- **Sampling** — загружай только часть данных для исследования
- **Streaming** — обрабатывай данные порциями (chunks)
- **No full load** — никогда не загружай весь файл в контекст

## The Workflow

### Phase 1: Explore (Исследование структуры)

**Шаг 1.1: Быстрая проверка структуры**
```python
import pandas as pd

# Загружаем только первые 10 строк для просмотра структуры
df_sample = pd.read_csv('DATA/Nero.csv', nrows=10, sep=';')
print(df_sample.head())
print(df_sample.columns.tolist())
print(df_sample.dtypes)
```

**Шаг 1.2: Статистика по выборке**
```python
# Загружаем 1000 строк для базовой статистики
df_explore = pd.read_csv('DATA/Nero.csv', nrows=1000, sep=';')
print(df_explore.describe())
print(df_explore.info())

# Проверка пропущенных значений
print(df_explore.isnull().sum())
```

**Шаг 1.3: Определение размера файла**
```bash
# Проверка размера файла
wc -l DATA/Nero.csv
ls -lh DATA/Nero.csv

# В Python
import os
file_size = os.path.getsize('DATA/Nero.csv')
print(f"File size: {file_size / (1024*1024):.2f} MB")
```

### Phase 2: Sample (Выборка для анализа)

**Шаг 2.1: Случайная выборка**
```python
# Читаем файл с пропуском строк для случайной выборки
df_full = pd.read_csv('DATA/Nero.csv', sep=';')
df_sample = df_full.sample(n=1000, random_state=42)  # 1000 случайных строк
```

**Шаг 2.2: Выборка по времени (для временных рядов)**
```python
# Загружаем только последние N строк (актуально для временных рядов)
df = pd.read_csv('DATA/Nero.csv', sep=';')
df_tail = df.tail(5000)  # Последние 5000 записей
```

**Шаг 2.3: Выборка с условием**
```python
# Читаем весь файл, но фильтруем нужные строки
df = pd.read_csv('DATA/Nero.csv', sep=';')
df_filtered = df[df['volume'] > 1000]  # Только строки с volume > 1000
```

### Phase 3: Stream (Потоковая обработка)

**Шаг 3.1: Обработка по чанкам**
```python
# Обработка большого файла порциями
chunk_size = 10000
results = []

for chunk in pd.read_csv('DATA/Nero.csv', chunksize=chunk_size, sep=';'):
    # Обрабатываем каждый чанк
    processed = chunk[chunk['close'] > chunk['open']]  # Пример фильтрации
    results.append(processed)

# Объединяем результаты
df_result = pd.concat(results, ignore_index=True)
```

**Шаг 3.2: Агрегация при потоковой обработке**
```python
# Суммирование значений без загрузки всего файла
chunk_size = 10000
total_volume = 0
row_count = 0

for chunk in pd.read_csv('DATA/Nero.csv', chunksize=chunk_size, sep=';'):
    total_volume += chunk['volume'].sum()
    row_count += len(chunk)

avg_volume = total_volume / row_count
print(f"Average volume: {avg_volume}")
```

**Шаг 3.3: Фильтрация с сохранением**
```python
# Фильтрация большого файла с записью результатов на лету
chunk_size = 10000
first_chunk = True

for chunk in pd.read_csv('DATA/Nero.csv', chunksize=chunk_size, sep=';'):
    filtered = chunk[chunk['signal'] != 0]  # Только строки с сигналами
    
    mode = 'w' if first_chunk else 'a'
    header = first_chunk
    
    filtered.to_csv('DATA/Nero_signals_only.csv', 
                    mode=mode, 
                    header=header, 
                    index=False,
                    sep=';')
    first_chunk = False
```

### Phase 4: Export (Сохранение результатов)

**Шаг 4.1: Сохранение в CSV**
```python
# Сохранение с правильными параметрами
df_processed.to_csv('DATA/Nero_processed.csv', 
                    index=False,      # Без индекса
                    sep=';',          # Разделитель
                    encoding='utf-8', # Кодировка
                    float_format='%.6f')  # Формат чисел
```

**Шаг 4.2: Сохранение в Parquet (для больших файлов)**
```python
# Parquet эффективнее для больших файлов
df_processed.to_parquet('DATA/Nero_processed.parquet', index=False)

# Чтение обратно
df = pd.read_parquet('DATA/Nero_processed.parquet')
```

## Common Operations

### ✅ Прочитать структуру (без загрузки данных)
```python
df = pd.read_csv('file.csv', nrows=10)
print(df.columns.tolist())
print(df.dtypes)
```

### ✅ Получить статистику по выборке
```python
df = pd.read_csv('file.csv', nrows=1000)
print(df.describe())
print(df.isnull().sum())
```

### ✅ Отфильтровать перед загрузкой
```python
# Нельзя фильтровать напрямую при чтении,
# но можно использовать usecols для выбора колонок
df = pd.read_csv('file.csv', 
                 usecols=['time', 'open', 'close', 'signal'],
                 nrows=5000)
```

### ✅ Обработать большой файл по частям
```python
for chunk in pd.read_csv('large_file.csv', chunksize=10000):
    process(chunk)  # Обработка каждого чанка
```

### ✅ Проверить уникальные значения
```python
df = pd.read_csv('file.csv', nrows=10000)
print(df['category'].value_counts())
print(df['signal'].unique())
```

### ✅ Работа с разными кодировками
```python
# UTF-8 (по умолчанию)
df = pd.read_csv('file.csv', encoding='utf-8')

# UTF-16LE (для MT4 файлов)
df = pd.read_csv('file.csv', encoding='utf-16-le')

# Windows-1251 (кириллица)
df = pd.read_csv('file.csv', encoding='cp1251')
```

## Red Flags

| НЕ делай | Почему | Что делать вместо |
|----------|--------|-------------------|
| `pd.read_csv('large.csv')` без `nrows` | Загрузит весь файл в память | Используй `nrows=100` для исследования |
| `print(df)` для большого DataFrame | Выводит всё в контекст | Используй `df.head()`, `df.describe()` |
| `df.to_string()` | Создаёт огромную строку | Используй `df.head(10).to_string()` |
| Загружать >100MB CSV целиком | Переполнение контекста | Используй `chunksize` для обработки |
| `df.values` или `df.to_numpy()` для больших данных | Конвертирует всё в массив | Работай с DataFrame напрямую |
| Игнорировать `sep` параметр | Неправильный парсинг | Всегда указывай `sep=';'` или `sep=','` |

## Integration with Other Skills

- После исследования: использовать `create-eda-report` для генерации отчёта
- Для обработки конвейера: использовать `check-data-impact` для анализа зависимостей
- Перед сохранением результатов: использовать `verification-before-completion` для проверки
- Для добавления модуля: использовать `add-new-module` для обновления документации

## Project-Specific Notes

### Формат данных Nero.csv
- **Кодировка**: UTF-16LE (для файлов из MT4)
- **Разделитель**: `;` (точка с запятой)
- **Колонки**: time, open, high, low, close, volume, signal, predict, и др.
- **Путь**: `MT/MQL4/Files/Nero.csv` (исходные), `DATA/Nero_*.csv` (обработанные)

### Пример для Nero.csv
```python
# Чтение файла из MT4
df = pd.read_csv('MT/MQL4/Files/Nero.csv', 
                 nrows=1000,
                 encoding='utf-16-le',
                 sep=';')

# Чтение обработанного файла
df = pd.read_csv('DATA/Nero_train_labeled.csv',
                 nrows=1000,
                 sep=';')
```
