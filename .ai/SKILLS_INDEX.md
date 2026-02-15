# Индекс Skills для ИИ-агентов

Каталог автоматизированных команд для рутинных задач проекта.  
**Обновлён**: 2026-02-15

---

## Доступные команды

| Команда | Skill | Назначение | Статус |
|---------|-------|------------|--------|
| `sync docs` | [update-docs-on-code-change](skills/update-docs-on-code-change/SKILL.md) | Синхронизация документации после изменения кода | ✅ Реализован |
| `doc this [файл]` | [create-module-docs](skills/create-module-docs/SKILL.md) | Создать полную документацию для модуля | ✅ Реализован |
| `check docs` | [validate-docs-sync](skills/validate-docs-sync/SKILL.md) | Проверить актуальность документации | ✅ Реализован |
| `create module [имя]` | [add-new-module](skills/add-new-module/SKILL.md) | Создать новый модуль со всей документацией | ✅ Реализован |
| `check data impact [файл]` | [check-data-impact](skills/check-data-impact/SKILL.md) | Показать downstream-зависимости | ✅ Реализован |
| `explain step [название]` | [explain-pipeline-step](skills/explain-pipeline-step/SKILL.md) | Детальное объяснение шага pipeline | ✅ Реализован |
| `rebuild module index` | [generate-module-index](skills/generate-module-index/SKILL.md) | Пересоздать MODULE_INDEX.md из file headers | ✅ Реализован |
| `analyze [файл.csv]` | [create-eda-report](skills/create-eda-report/SKILL.md) | Автоматический EDA для датасета | ✅ Реализован |

---

## Детали реализованных skills

Все skills содержат детальные инструкции и алгоритмы выполнения. Ссылки на конкретные файлы `SKILL.md` доступны в таблице выше.

---

## Как использовать skill

1. **Проверь индекс**: открой `SKILLS_INDEX.md` и найди нужную команду
2. **Запусти команду**: напиши команду в чат с ИИ-агентом (Cursor/Antigravity)
3. **Дождись подтверждения**: агент покажет diff и попросит подтверждение перед применением изменений
4. **Проверь результат**: убедись, что изменения корректны

---

## Как запросить новый skill

Если нужна автоматизация задачи, которой нет в индексе:

1. Опиши задачу: "Мне нужно автоматизировать [описание]"
2. Укажи триггер: "Я хочу запускать это командой `[команда]`"
3. Опиши ожидаемый результат: "Команда должна [что делать]"

ИИ-агент создаст skill по шаблону `SKILL.md` и добавит его в проект.

---

## Навигация

- **Правила проекта**: [RULES_INDEX.md](RULES_INDEX.md)
- **Индекс модулей**: [../MODULE_INDEX.md](../MODULE_INDEX.md)
- **Реализованные skills**: [skills/](skills/)