---
trigger: always_on
globs: ["**/*.mqh", "**/*.csv", "**/*.parquet"]
---

# Правила работы с файлами

**MQL4 (*.mqh *.mq4)**: Читай напрямую в UTF-16LE, не в UTF-8

**Большие CSV** (`*.csv`): НЕ открывай целиком (>10MB), используй `head` или `pd.read_csv(nrows=10)`

**НЕ открывай целиком *.csv** : используй 'head -n 50 file.csv' или 'tail -n 50' или 'pd.read_csv(nrows=10)'

**Используй**:
- запускай скрипты из 'processing/' или 'statistics/'