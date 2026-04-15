---
name: csv-processing
description: Use when working with CSV files - reading, exploring, analyzing large datasets
---

# Работа с CSV файлами (Codex-friendly)

## Когда использовать
- Любая задача с `*.csv`.
- Исследование структуры или валидация данных без полной загрузки файла.

## Project guardrails (SoSimple)
- Сначала читать только первые 10 строк CSV.
- Не печатать и не загружать файл целиком в контекст.

## Workflow

### 1) Быстрый обзор
```bash
wc -l MT/MQL4/Files/Nero.csv
head -n 10 MT/MQL4/Files/Nero.csv
```

```python
import pandas as pd

df10 = pd.read_csv(
    "MT/MQL4/Files/Nero.csv",
    nrows=10,
    encoding="utf-16-le",
    sep=";"
)
print(df10.columns.tolist())
print(df10.dtypes)
```

### 2) Выборка без full load
```python
df_sample = pd.read_csv(
    "DATA/Nero_train_labeled.csv",
    nrows=2000,
    sep=";"
)
print(df_sample.describe(include="all"))
print(df_sample.isna().sum().head(20))
```

### 3) Потоковая обработка (chunks)
```python
import pandas as pd

total_rows = 0
positive_signals = 0

for chunk in pd.read_csv("DATA/Nero_train_labeled.csv", sep=";", chunksize=10000):
    total_rows += len(chunk)
    positive_signals += (chunk["signal"] > 0).sum()

print({"rows": total_rows, "positive_signals": int(positive_signals)})
```

### 4) Запись результата без перегрузки памяти
```python
import pandas as pd

first = True
for chunk in pd.read_csv("DATA/Nero_train_labeled.csv", sep=";", chunksize=10000):
    out = chunk[chunk["signal"] != 0]
    out.to_csv(
        "DATA/Nero_train_signal_only.csv",
        mode="w" if first else "a",
        header=first,
        index=False,
        sep=";"
    )
    first = False
```

## Best practices
- Использовать `usecols` для ограничения колонок.
- Для EDA начинать с `nrows=1000..10000`.
- Для больших файлов сначала считать агрегаты по чанкам, потом решать, нужен ли полный датасет.

## Частые ошибки
| Ошибка | Как исправить |
|---|---|
| `pd.read_csv("large.csv")` без ограничений | Добавить `nrows` или `chunksize` |
| `print(df)` на большой таблице | Использовать `head`, `info`, `describe` |
| Неверная кодировка MT4 CSV | `encoding='utf-16-le'` |
| Неверный разделитель | Явно задавать `sep=';'` |
