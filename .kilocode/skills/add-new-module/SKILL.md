---
name: add-new-module
description: >
  Create a new module with complete documentation scaffold including file header, markdown docs, module index and data flow entries.
tags:
  - documentation
  - automation
  - scaffold
triggers:
  - create module [name]
  - new script [name]
always_apply: false
---

**Команда**: `create module [имя]` или `new script [имя]`
**Назначение**: Создать новый модуль со всей необходимой документацией

Шаги:
1. Спросить параметры:
   - Директория (processing/statistics/ML)
   - Назначение (одна строка)
   - Входные/выходные данные
2. Создать файл с file header
3. Создать docs/[категория]/[имя].md
4. Добавить в MODULE_INDEX.md
5. Добавить в DATA_FLOW.md (если нужно)
6. Открыть файл в редакторе

Пример:
> create module feature_engineering
Директория: processing
Назначение: Создание дополнительных признаков из фракталов
Входы: Nero_normalized.csv
Выходы: Nero_features.csv
✅ Создан processing/feature_engineering.py
✅ Создан docs/data_preprocessing/feature_engineering.py.md
✅ Обновлён MODULE_INDEX.md
