---
name: module-index
description: Module indexing reminder - use add-new-module skill for automated indexing
globs:
  - "*.py"
  - "*.mqh"
  - "*.ipynb"
alwaysApply: true
---

При создании модуля используй skill: `create module [name]`

Этот skill автоматически:
1. Добавит file header по стандарту 000-documentation.md
2. Добавит запись в MODULE_INDEX.md
3. Обновит DATA_FLOW.md при необходимости
