# CLAUDE.md
> Инструкции для Claude Code в репозитории SoSimple. Общий codex-first индекс: [AGENTS.md](AGENTS.md).

## Как использовать вместе с AGENTS.md
1. Сначала читать [AGENTS.md](AGENTS.md) для структуры проекта, путей, ограничений по данным и базовых команд.
2. Этот файл использовать для Claude Code-specific workflow и вызова `.claude/skills`.
3. При конфликте приоритет: явный запрос пользователя -> ограничения окружения -> этот файл -> AGENTS.md.

## Workflow для Claude Code

### Паттерны разработки
- Новая фича: `/brainstorming` -> `/writing-plans` -> `/test-driven-development` -> `/requesting-code-review`
- Bugfix: `/systematic-debugging` -> diagnose -> fix -> `/verification-before-completion`
- Завершение ветки: `/finishing-a-development-branch` -> merge/PR -> update `CHANGELOG.md`
- Новый модуль: создать file header -> добавить docs -> добавить запись в `MODULE_INDEX.md`

### Когда использовать skills
| Skill | Когда |
|-------|-------|
| `/brainstorming` | Перед feature/refactor |
| `/writing-plans` | Для многошаговых задач |
| `/test-driven-development` | Перед реализацией фичи |
| `/systematic-debugging` | При ошибке или падении теста |
| `/verification-before-completion` | Перед завершением работы |
| `/requesting-code-review` | При завершении большой работы |
| `/executing-plans` | Если есть письменный план |

### Текстовые команды для документации (.kilocode/skills)
| Команда | Когда |
|---------|-------|
| `обнови документацию` | После правки кода |
| `doc this путь/к/файлу.py` | Добавить docs для файла |
| `create module имя` | Создать новый модуль с docs |
| `rebuild module index` | Обновить `MODULE_INDEX.md` |

## Работа с памятью
- Память проекта: `.claude/memory/MEMORY.md` (индекс ссылок).
- Содержимое памяти считать вспомогательным контекстом: проверять актуальность по текущим docs и запросу пользователя.

## Git и CHANGELOG
- Не делать `git commit`/`git push` без явной просьбы пользователя.
- В `CHANGELOG.md` писать только: новые фичи, breaking changes, багфиксы, результаты экспериментов с выводами.
- Не писать в `CHANGELOG.md`: изменения документации, обновление путей, рефакторинг без изменения поведения.
- Формат: `## [YYYY-MM-DD] - Краткое описание`
- Секции: `### Добавлено`, `### Изменено`, `### Исправлено`, `### Результаты`, `### Вывод`

## Что не делать
- Не добавлять docstrings/comments, если их не было и это не требуется задачей.
- Не рефакторить "заодно" в bugfix-задачах.
- Не добавлять обработку невозможных сценариев.
- Не создавать helper-функции для одноразовых операций.
- Не over-engineer.
