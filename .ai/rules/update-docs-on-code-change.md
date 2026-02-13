---
priority: ON_CHANGE
trigger: После изменения кода (перед коммитом)
affects: File headers в коде, соответствующие .md файлы, MODULE_INDEX.md
description: Синхронизация документации при изменении кода
tags: sync, git-hooks, automation
---

# Правило: Синхронизация документации

## Триггер
Пользователь говорит: `sync docs`, `обнови документацию`, `синхронизируй docs`

## Алгоритм

### 1. Найди изменённые файлы
```bash
git diff --cached --name-only | grep -E '\.(py|mq4|mqh|ipynb)$'
```

Или используй текущий открытый файл, если пользователь его упомянул.

### 2. Определи соответствующую документацию
Маппинг:

processing/[script].py → docs/data_preprocessing/[script].md

statistics/[script].py → docs/data_analysis/[script].md

MT/MQL4/Include/[lib].mqh → docs/architecture.md (секция Pipeline)

### 3. Обнови элементы документации
В коде:

- File header → Обновлён: [сегодняшняя дата]

- Docstrings → если изменились сигнатуры функций

В .md файле (если существует):

- Назначение — если изменилась функциональность

- Входные/Выходные данные — если изменились форматы

- Использование — если изменились параметры запуска

- Примечания — если появились ограничения

В architecture.md (если нужно):

- Секция Pipeline — если изменились входы/выходы

### 4. Покажи diff и запроси подтверждение
Формат вывода:
```bash
Файл: docs/data_preprocessing/normalize.py.md
+ ## Входные данные
+ - **Файл**: `Nero.csv` (было: `data.csv`)
```
Вопрос: "Применить изменения? (yes/no)"

## Примеры использования
- Пользователь: "Я изменил normalize.py, обнови документацию"
  - Действие: Обнови processing/normalize.py (file header) + docs/data_preprocessing/normalize.py.md

- Пользователь: "sync docs"
  - Действие: Найди все staged файлы через git diff --cached, обнови их документацию

## Examples

### ✅ Sync documentation after code change
```bash
# User changed normalize.py
$ git diff --cached --name-only
processing/normalize.py

# Agent updates:
1. File header in normalize.py (Обновлён: 2026-02-13)
2. docs/data_preprocessing/normalize.py.md (Входные/Выходные данные)
3. MODULE_INDEX.md (если изменились зависимости)
```


