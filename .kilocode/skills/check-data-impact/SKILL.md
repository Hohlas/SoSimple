---
name: check-data-impact
description: Use when changing data formats to analyze downstream dependencies and prevent breaking changes in the pipeline
---

# Анализ влияния изменений данных

## Overview

Анализ downstream-зависимостей при изменении форматов данных для предотвращения breaking changes в конвейере обработки.

## When to Use

- Изменение формата выходных данных скрипта
- Рефакторинг processing-скриптов
- Команды: "check data impact [file]", "impact analysis [file]"

Applies to: `*.csv`, `*.parquet` файлы

## The Workflow

**Команда**: `check data impact [файл]` или `impact analysis [файл]`
**Назначение**: Показать, какие скрипты будут затронуты при изменении формата данных

Шаги:
1. Прочитать file header файла (секция "Выходные данные")
2. Найти в MODULE_INDEX.md все скрипты, использующие эти файлы
3. Рекурсивно найти downstream-зависимости
4. Вывести граф зависимостей

Пример:
> check data impact processing/normalize.py

Изменение processing/normalize.py повлияет на:
⬇️ Nero_normalized.csv
  └─ processing/label_main.py
      ├─ Nero_train_labeled.csv
      │   └─ ML/train.py
      ├─ Nero_val_labeled.csv
      │   └─ ML/validate.py
      └─ Nero_test_labeled.csv
          └─ ML/test.py

## Quick Reference

| Category | Values |
|----------|--------|
| Tags | analysis, impact, data |

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Not checking dependencies before changing output format | Always run impact analysis first |
| Forgetting recursive dependencies | Check all levels of downstream scripts |
| Ignoring MODULE_INDEX.md | Keep index updated for accurate analysis |
