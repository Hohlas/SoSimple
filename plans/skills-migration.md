# План миграции русскоязычных скиллов

## Правила миграции

На основе ваших ответов:
1. ✅ `tags` → перенести в "Quick Reference"
2. ✅ `alwaysApply` → удалить
3. ✅ Добавить отсутствующие разделы (`## Overview`, `## When to Use`, `## Common Mistakes`)
4. ✅ Оставить русский язык

---

## Скилл 1: add-new-module

### Текущий frontmatter:
```yaml
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
```

### Новый frontmatter:
```yaml
---
name: add-new-module
description: Use when creating a new module, adding documentation to existing files, or scaffolding scripts with proper headers
---
```

### Новая структура SKILL.md:

```markdown
---
name: add-new-module
