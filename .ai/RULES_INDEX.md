# Индекс правил для ИИ-агентов

Каталог всех правил проекта с приоритетами и триггерами.  
**Обновлён**: 2026-02-10

---

## Приоритеты правил

| Приоритет | Правило | Когда применять | Файл |
|-----------|---------|-----------------|------|
| **ALWAYS** | Стандарт документирования | Создание/изменение любого .py/.mq4/.ipynb | [000-documentation.md](rules/000-documentation.md) |
| **ALWAYS** | Индексирование модулей | Создание нового файла | [001-module-index.md](rules/001-module-index.md) |
| **ALWAYS** | Компактность документации | Написание/обновление .md | [002-compact-first.md](rules/002-compact-first.md) |
| **ALWAYS** | Использование skills | Перед рутинной задачей | [006-skill-before-manual.md](rules/006-skill-before-manual.md) |
| **ALWAYS** | Запрет CSV в контексте | Работа с .csv файлами | [007-no-csv-context.md](rules/007-no-csv-context.md) |
| **ALWAYS** | Ссылки вместо дублирования | Повторяющаяся информация | [008-links-over-duplication.md](rules/008-links-over-duplication.md) |
| **CONTEXT** | Работа с большими файлами | Открытие файла > 10MB | [100-file-handling.md](rules/100-file-handling.md) |
| **CONTEXT** | Зависимости данных | Изменение формата входных/выходных данных | [003-data-dependencies.md](rules/003-data-dependencies.md) |
| **CONTEXT** | Специфика MQL4 | Работа с .mq4/.mqh файлами | [004-mql4-specifics.md](rules/004-mql4-specifics.md) |
| **CONTEXT** | Гигиена Jupyter | Работа с .ipynb файлами | [005-jupyter-hygiene.md](rules/005-jupyter-hygiene.md) |
| **ON_CHANGE** | Синхронизация документации | После изменения кода | [update-docs-on-code-change.md](rules/update-docs-on-code-change.md) |

---

## Описание приоритетов

- **ALWAYS**: Правило применяется всегда, без исключений (обязательно для всех агентов)
- **CONTEXT**: Правило применяется только в специфических ситуациях (указанных в колонке "Когда применять")
- **ON_CHANGE**: Правило активируется при определённом событии (изменение кода, данных и т.п.)

---

## Быстрый поиск правила

### По типу файла
- **.py файлы**: 000-documentation, 001-module-index, 002-compact-first
- **.mq4/.mqh файлы**: 000-documentation, 004-mql4-specifics
- **.ipynb файлы**: 000-documentation, 005-jupyter-hygiene
- **.csv файлы**: 007-no-csv-context, 100-file-handling

### По задаче
- **Создание нового модуля**: 000-documentation → 001-module-index → skill `create module`
- **Изменение кода**: update-docs-on-code-change → skill `sync docs`
- **Изменение данных**: 003-data-dependencies → skill `check data impact`
- **Документирование**: 000-documentation → 002-compact-first → skill `doc this`

---

## Навигация
- **Полные тексты правил**: [.ai/rules/](.ai/rules/)
- **Индекс skills**: [SKILLS_INDEX.md](SKILLS_INDEX.md)
- **Индекс модулей**: [../MODULE_INDEX.md](../MODULE_INDEX.md)