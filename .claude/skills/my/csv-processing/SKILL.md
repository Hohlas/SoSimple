---
name: csv-processing
description: Use when working with CSV files
---

# Работа с CSV файлами

Проектные CSV — разделитель `;`. Никогда не загружать целиком —
использовать `nrows` / `chunksize` / `usecols` для нужных колонок и строк.

## Рецепты

### Быстрый обзор
```python
import pandas as pd
df10 = pd.read_csv("MT/MQL4/Files/Nero.csv", nrows=10, sep=";")
print(df10.columns.tolist()); print(df10.dtypes)
```
Размер: `wc -l MT/MQL4/Files/Nero.csv` (bash, быстро).

### Выборка для EDA
```python
df = pd.read_csv("DATA/Nero_train_labeled.csv", nrows=5000, sep=";",
                 usecols=["time", "signal", "ATR"])
print(df.describe(include="all")); print(df.isna().sum())
```

### Потоковая агрегация (chunks)
```python
total = pos = 0
for chunk in pd.read_csv("DATA/Nero_train_labeled.csv", sep=";",
                         chunksize=10000, usecols=["signal"]):
    total += len(chunk); pos += (chunk["signal"] > 0).sum()
print({"rows": total, "positive": int(pos)})
```

### Запись по чанкам
```python
first = True
for chunk in pd.read_csv("DATA/Nero_train_labeled.csv", sep=";", chunksize=10000):
    out = chunk[chunk["signal"] != 0]
    out.to_csv("DATA/Nero_signal_only.csv", mode="w" if first else "a",
               header=first, index=False, sep=";")
    first = False
```

## Частые ошибки
| Ошибка | Исправление |
|---|---|
| `pd.read_csv(path)` без ограничений | `nrows` или `chunksize` |
| `print(df)` на большой таблице | `head`, `info`, `describe` |
| `sep` не задан → одна колонка | Явно `sep=";"` |
