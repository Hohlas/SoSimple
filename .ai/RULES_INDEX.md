# Индекс правил для ИИ-агентов

Каталог всех правил проекта с приоритетами и триггерами.  
**Обновлён**: 2026-02-14

---

## Приоритеты правил

| Приоритет | Правило | Trigger | Файл |
|-----------|---------|---------|------|
| **ALWAYS** | Стандарт документирования | Создание/изменение .py/.mq4/.ipynb | [000-documentation.md](rules/000-documentation.md) |
| **ALWAYS** | Индексирование модулей | Создание нового файла | [001-module-index.md](rules/001-module-index.md) |
| **ALWAYS** | Компактность и отсутствие дублей | Написание/обновление .md | [002-compact-and-no-duplication.md](rules/002-compact-and-no-duplication.md) |
| **CONTEXT** | Зависимости данных | Изменение формата данных | [003-data-dependencies.md](rules/003-data-dependencies.md) |
| **CONTEXT** | Специфика MQL4 | Работа с .mq4/.mqh | [004-mql4-specifics.md](rules/004-mql4-specifics.md) |
| **CONTEXT** | Гигиена Jupyter | Работа с .ipynb | [005-jupyter-hygiene.md](rules/005-jupyter-hygiene.md) |
| **CONTEXT** | Skill перед ручной работой | Перед выполнением рутинной задачи | [006-skill-before-manual.md](rules/006-skill-before-manual.md) |
| **CONTEXT** | Не грузить CSV в контекст | Работа с .csv файлами | [007-no-csv-context.md](rules/007-no-csv-context.md) |
| **CONTEXT** | Работа с файлами | Открытие файлов проекта | [100-file-handling.md](rules/100-file-handling.md) |
| **ON_CHANGE** | Синхронизация документации | После изменения кода | [008-sync-docs.md](rules/008-sync-docs.md) |

---

## Описание приоритетов

- **ALWAYS**: Правило применяется всегда, без исключений (обязательно для всех агентов)
- **CONTEXT**: Правило применяется только в специфических ситуациях (указанных в триггере)
- **ON_CHANGE**: Правило активируется при определённом событии (изменение кода, данных и т.п.)

---

## Система нумерации правил

- **000-099**: Процессные правила (документирование, индексирование, workflow)
- **100-199**: Технические правила (форматы файлов, кодировки, инструменты)
- **200+**: Специализированные правила (зарезервировано для будущего)

---

## Быстрый поиск правила

### По типу файла
- **.py файлы**: [000-documentation](rules/000-documentation.md), [001-module-index](rules/001-module-index.md), [002-compact-and-no-duplication](rules/002-compact-and-no-duplication.md)
- **.mq4/.mqh файлы**: [000-documentation](rules/000-documentation.md), [004-mql4-specifics](rules/004-mql4-specifics.md), [100-file-handling](rules/100-file-handling.md)
- **.ipynb файлы**: [000-documentation](rules/000-documentation.md), [005-jupyter-hygiene](rules/005-jupyter-hygiene.md)
- **.csv файлы**: [007-no-csv-context](rules/007-no-csv-context.md), [100-file-handling](rules/100-file-handling.md)

### По задаче
- **Создание нового модуля**: [000-documentation](rules/000-documentation.md) → [001-module-index](rules/001-module-index.md) → skill `create module`
- **Изменение кода**: [008-sync-docs](rules/008-sync-docs.md) → skill `sync docs`
- **Изменение данных**: [003-data-dependencies](rules/003-data-dependencies.md) → skill `check data impact`
- **Документирование**: [000-documentation](rules/000-documentation.md) → [002-compact-and-no-duplication](rules/002-compact-and-no-duplication.md) → skill `doc this`
- **Работа с большими CSV**: [007-no-csv-context](rules/007-no-csv-context.md) → [100-file-handling](rules/100-file-handling.md)
- **Редактирование MQL4**: [004-mql4-specifics](rules/004-mql4-specifics.md) → [100-file-handling](rules/100-file-handling.md)

---

## Навигация
- **Полные тексты правил**: [.ai/rules/](rules/)
- **Индекс skills**: [SKILLS_INDEX.md](SKILLS_INDEX.md)
- **Индекс модулей**: [../MODULE_INDEX.md](../MODULE_INDEX.md)
