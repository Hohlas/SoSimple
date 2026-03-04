---
name: add-new-module
description: >
  Create a new module or add documentation to an existing module. Includes file header, markdown docs, module index and data flow entries.
tags:
  - documentation
  - automation
  - scaffold
triggers:
  - create module [name]
  - new script [name]
  - doc this [file]
  - document [file]
  - создай модуль [name]
  - новый скрипт [name]
  - задокументируй [file]
  - документация [file]
applies_to:
  - "*.py"
  - "*.mq4"
  - "*.mqh"
  - "*.ipynb"
alwaysApply: false
---

## Режим 1: Создание нового модуля

**Команда**: `create module [имя]` или `new script [имя]`
**Назначение**: Создать новый модуль со всей необходимой документацией

### Шаг 0: Проверить правила

Перед созданием модуля загрузить соответствующие rules:
- Для .py: @.kilocode/rules/000-documentation.md
- Для .mqh/.mq4: @.kilocode/rules/004-mql4-specifics.md, @.kilocode/skills/mql4-processing/
- Для .ipynb: @.kilocode/rules/005-jupyter-hygiene.md

### Шаг 1: Определить параметры
- Директория (processing/statistics/ML)
- Назначение (одна строка)
- Входные/выходные данные

### Шаг 2: Создать file header
Использовать точный шаблон из 000-documentation.md:
- Для Python: `# ====` рамка
- Для MQL4: `//+--+` рамка (UTF-16LE!)
- Для Jupyter: Markdown ячейка

### Шаг 3: Создать документацию
Создать `docs/[category]/[filename].md` по шаблону из 000-documentation.md.

### Шаг 4: Обновить индексы
- Добавить в MODULE_INDEX.md по шаблону 001-module-index.md
- Обновить DATA_FLOW.md если участвует в pipeline
- Обновить AGENTS.md если критичный компонент

### Шаг 5: Валидация
- Проверить file header: все поля заполнены?
- Проверить кодировку (особенно для MQL4)
- Проверить ссылки в документации

### Шаг 6: Открыть файл в редакторе

Пример:
> create module feature_engineering
Директория: processing
Назначение: Создание дополнительных признаков из фракталов
Входы: Nero_normalized.csv
Выходы: Nero_features.csv
✅ Создан processing/feature_engineering.py
✅ Создан docs/data_preprocessing/feature_engineering.py.md
✅ Обновлён MODULE_INDEX.md
✅ File header проверен
✅ Кодировка UTF-8 (Python)

Пример:
> create module feature_engineering
Директория: processing
Назначение: Создание дополнительных признаков из фракталов
Входы: Nero_normalized.csv
Выходы: Nero_features.csv
✅ Создан processing/feature_engineering.py
✅ Создан docs/data_preprocessing/feature_engineering.py.md
✅ Обновлён MODULE_INDEX.md

## Режим 2: Документирование существующего модуля

**Команда**: `doc this [файл]` или `document [файл]`
**Назначение**: Создать полную документацию для существующего недокументированного модуля

Шаги:
1. Проверить наличие file header в коде
   - Если нет → создать по шаблону 000-documentation.md
2. Создать docs/[категория]/[модуль].md
   - Использовать шаблон из 000-documentation.md
3. Добавить запись в MODULE_INDEX.md
4. Обновить DATA_FLOW.md (если участвует в pipeline)
5. Показать diff и запросить подтверждение

Пример:
> doc this processing/normalize.py
Создаю документацию...
- ✅ File header добавлен
- ✅ docs/data_preprocessing/normalize.py.md создан
- ✅ MODULE_INDEX.md обновлён
