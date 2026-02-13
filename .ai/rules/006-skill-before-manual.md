---
priority: ALWAYS
trigger: Перед выполнением рутинной задачи
affects: Workflow ИИ-агента
description: Проверка наличия skill перед ручным выполнением задачи
tags: skills, automation, efficiency
---

Перед выполнением рутинной задачи проверь SKILLS_INDEX.md.

Существующие команды:
- `sync docs` — синхронизация документации
- `doc this` — документирование файла (если реализован)
- `check docs` — проверка актуальности (если реализован)

Если skill не реализован:
1. Выполни задачу вручную
2. Предложи создать skill для автоматизации

## Examples

### ✅ Check SKILLS_INDEX before manual work
```markdown
# Перед обновлением документации:
1. Проверь .ai/SKILLS_INDEX.md
2. Найдена команда: `sync docs`
3. Выполни: sync docs processing/normalize.py
```

