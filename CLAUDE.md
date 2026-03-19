# CLAUDE.md
> **Инструкции для Claude Code. Источник истины — [AGENTS.md](AGENTS.md)**

## 📋 Инструкции для Claude Code

### Как я работаю с этим проектом
1. **Начинаю с AGENTS.md** — этот файл содержит все инструкции
2. **Использую skills** — `/brainstorming`, `/writing-plans`, `/test-driven-development` и т.д.
3. **Обновляю код** — добавляю header с датой и версией, обновляю CHANGELOG.md
4. **Читаю feedback** — есть memory система в `.claude/memory/`

### Когда использовать skills
- **`/brainstorming`** → перед любым feature/refactor (исследовать идеи, требования)
- **`/writing-plans`** → для многошаговых задач (создать план перед кодом)
- **`/test-driven-development`** → перед реализацией фичи (написать тесты первыми)
- **`/systematic-debugging`** → при ошибке/падении теста (диагностика перед фиксом)
- **`/verification-before-completion`** → перед commit/PR (проверить, что всё работает)
- **`/requesting-code-review`** → при завершении большой работы (ревью перед мержом)
- **`/executing-plans`** → если есть письменный план (выполнить по шагам)

### Работа с памятью (синхронизируется через git)
- Память проекта: `.claude/memory/MEMORY.md` ⬅️ в репозитории
- **MEMORY.md** — индекс (ссылки на файлы памяти)
- **user_profile.md**, **feedback_*.md**, **project_*.md** — сами память-файлы
- Claude Code автоматически читает эту папку при загрузке проекта

### Git workflow
- ❌ Не делай `git commit` и `git push` без явной просьбы — пользователь контролирует историю сам

### CHANGELOG.md: обновляй при каждой значительной смене
- хронология результатов исследований, выводы по проведённым работам, новые фичи, breaking changes, багфиксы.
- Добавь запись ТОЛЬКО при: новых фичах, breaking changes, багфиксах, результатах экспериментов и исследований с выводами.
- НЕ добавляй записи, если: проведены правки документации, обновление путей сохранения, рефакторинг без изменения поведения, обновление AGENTS.md/MODULE_INDEX.md.
- Используй формат: `## [YYYY-MM-DD] — Краткое описание`
- Структурируй изменения секциями: ### Добавлено, ### Изменено, ### Исправлено, ### Результаты, ### Вывод
- Укажи ключевые изменения с точки зрения продукта/исследования; НЕ упоминай обновление документации и пути к файлам


### Что НЕ нужно делать
- ❌ Не добавляй docstrings/comments если их не было в исходном коде
- ❌ Не рефакторься "заодно" (bug fix = только fix, не cleanup)
- ❌ Не добавляй error handling для невозможных сценариев
- ❌ Не создавай helper-функции для one-time операций
- ❌ Не over-engineer: три строки кода лучше, чем абстракция

## 📋 Workflow для разработки
- **Новое feature**: `/brainstorming` → `/writing-plans` → `/test-driven-development` → `/requesting-code-review`
- **Bugfix**: `/systematic-debugging` → diagnose → fix → `/verification-before-completion`
- **Завершение**: `/finishing-a-development-branch` → merge/PR → update CHANGELOG.md
- **Новый модуль**: Add to structure → Create docs → Add to AGENTS.md → Update this file
