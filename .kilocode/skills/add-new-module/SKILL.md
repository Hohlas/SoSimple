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

## Стандарты документирования (из rules/000-documentation.md)

### File Header шаблоны

**Для Python (.py):**
```python
# =============================================================================
# Файл: [filename.py]
# Назначение: [одна строка]
# Язык: Python
# Обновлён: [YYYY-MM-DD]
# Зависимости:
#   Входные данные:
#     - [путь/файл] (откуда: [источник])
#   Выходные данные:
#     - [путь/файл] (куда: [назначение])
# Внешние зависимости:
#   - [библиотека>=версия]
# Использование:
#   [команда запуска]
# Примечания:
#   - [важные ограничения]
# =============================================================================
```

**Для MQL4 (.mqh/.mq4):**
```cpp
//+------------------------------------------------------------------+
//| Файл: [filename.mqh]
//| Назначение: [одна строка]
//| Язык: MQL4
//| Обновлён: [YYYY-MM-DD]
//| Зависимости:
//|   - [файл.mqh]
//+------------------------------------------------------------------+
```

**Для Jupyter (.ipynb):**
Первая ячейка (Markdown):
```markdown
# [Название]

**Файл**: `path/notebook.ipynb`
**Назначение**: [что делает]
**Обновлён**: YYYY-MM-DD

## Входные/Выходные данные
- **Вход**: [файлы]
- **Выход**: [файлы]
```

### Docstrings (Python)

**Module-level** (после file header):
```python
"""
Краткое описание модуля (1-2 предложения).

Более детальное описание функциональности, если нужно.
"""
```

**Функции и классы:**
```python
def function_name(param: type) -> return_type:
    """
    Краткое описание функции.
    
    Аргументы:
        param: Описание параметра
        
    Возвращает:
        Описание возвращаемого значения
        
    Исключения:
        ExceptionType: Когда возникает
        
    Пример:
        >>> function_name(value)
    """
```

### Markdown документация

Создать `docs/[category]/[filename].md`:
```markdown
# Название модуля

## Назначение
[одна строка]

## Входные данные
- **Файл**: `path/to/input.csv`
- **Формат**: [описание]
- **Источник**: [откуда]

## Выходные данные
- **Файл**: `path/to/output.csv`
- **Формат**: [описание]
- **Используется в**: [следующий скрипт]

## Использование
\`\`\`bash
python script.py --input data.csv
\`\`\`

## Примечания
- [особенности]
```

### Языковые соглашения
- ✅ **На русском**: docstrings, комментарии, file headers, документация
- ✅ **На английском**: имена переменных, функций, классов, файлов
- ✅ Комментируй «почему», не «что»
- ✅ НЕ комментируй очевидное

---

## Режим 1: Создание нового модуля

**Команда**: `create module [имя]` или `new script [имя]`
**Назначение**: Создать новый модуль со всей необходимой документацией

### Шаг 0: Проверить связанные skills

Перед созданием модуля загрузить соответствующие skills:
- Для .py: данный skill (шаблоны выше)
- Для .mqh/.mq4: @.kilocode/skills/mql4-processing/
- Для .ipynb: @.kilocode/skills/jupyter-processing/

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

### Шаг 4: Обновить MODULE_INDEX.md

**Формат записи в MODULE_INDEX.md:**
```markdown
## [путь/файл]
**Назначение**: [одна строка]
**Входы**: [файлы] | **Выходы**: [файлы]
**Использует**: [библиотеки] | **Используется в**: [скрипты]
```

**Пример:**
```markdown
## processing/label_main.py
**Назначение**: CLI оркестратор для полного конвейера обработки данных
**Входы**: MT/MQL4/Files/Nero.csv | **Выходы**: data/Nero_train_labeled.csv
**Использует**: pandas, numpy | **Используется в**: ML training pipeline
```

**Также обновить:**
- DATA_FLOW.md если участвует в pipeline
- AGENTS.md если критичный компонент

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
