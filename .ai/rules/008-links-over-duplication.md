---
priority: ALWAYS
trigger: Повторяющаяся информация в нескольких файлах
affects: Все .md файлы, поддерживаемость документации
description: Использование ссылок вместо копирования текста
tags: documentation, links, duplication, maintenance
---

Если информация уже существует в другом документе:
- Добавь ссылку вместо копирования
- Формат: [текст](путь/к/файлу.md#секция)

Исключение: критичная информация для работы (PROJECT_CONTEXT.md).

## Examples

### ✅ Link instead of duplication
```markdown
## Data Flow
Полное описание: [DATA_FLOW.md](docs/DATA_FLOW.md)

## Dataset Structure
Детали: [dataset_description.md](docs/dataset_description.md)
```

