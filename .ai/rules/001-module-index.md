---
priority: ALWAYS
trigger: Создание нового исполняемого файла
affects: MODULE_INDEX.md
description: Правило индексирования модулей в MODULE_INDEX.md
tags: module-index, navigation, discovery
---

При создании нового .py/.mqh/.ipynb файла:
1. Добавь file header по стандарту 000-documentation.md
2. Добавь запись в MODULE_INDEX.md
3. Обнови DATA_FLOW.md, если файл участвует в pipeline

Формат записи в MODULE_INDEX:
## [путь/файл]
**Назначение**: [одна строка]
**Входы**: [файлы] | **Выходы**: [файлы]
**Использует**: [библиотеки] | **Используется в**: [скрипты]
