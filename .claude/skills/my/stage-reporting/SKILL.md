---
name: stage-reporting
description: Используй, когда пользователь просит: «закрой этап», «создай отчёт этапа», «напиши отчёт», «синхронизируй report/changelog/handoff»
---

# Отчёт по этапу

Workflow для фиксации завершённого этапа без потери контекста. Если скилл применим (см. «Когда НЕ использовать»), отчёт создаётся обязательно.

## Когда использовать

- Пользователь просит закрыть этап.
- Пользователь просит создать или написать отчёт завершённого этапа.
- Пользователь просит синхронизировать `report`, `CHANGELOG.md` и `CONTEXT_HANDOFF.md`.

## Когда НЕ использовать

- Чисто документационные правки без продуктового изменения → `my:update-docs-on-code-change`.
- Середина этапа, работа ещё не завершена.
- Одиночный bugfix без завершения этапа.
- Статус-репорт, ревью, краткая заметка — это не отчёт этапа.

Критерии, когда этап заслуживает отчёта, — в `docs/reports/README.md` (раздел «Когда отчёт обязателен»).

## Workflow

1. Определи дату (`YYYY-MM-DD`) и короткую тему этапа.
2. Создай или обнови `docs/reports/YYYY-MM-DD-topic.md` по шаблону `docs/reports/README.md`. Для ML/исследовательских результатов дополнительно примени требования `docs/methodology/16-reporting-audit.md`: секции `Multiple Testing Context` и `Validation Split Disclosure`.
3. Обнови `CHANGELOG.md`: добавь краткую запись — главные изменения, результаты, вывод, ссылка на report.
4. Перепиши `CONTEXT_HANDOFF.md` до актуального состояния — не дополняй старое, а сжимай до текущего контекста.
5. Синхронизируй документацию модулей — скилл `my:update-docs-on-code-change` (режим `sync docs`), если этап изменял кодовые модули (новые файлы, изменённые CLI/входы/выходы/назначение): обнови headers, `docs/<category>/<module>.md`, `MODULE_INDEX.md`, `docs/DATA_FLOW.md`.
6. Выполни wiki Ingest — скилл `my:wiki`. Ingest обновит `wiki/research/`, `wiki/concepts/`, `wiki/index.md`, `wiki/log.md`, `wiki/REPO_integrity.md`.
7. Проверь `git status`. Отдели файлы этого этапа от посторонних изменений. Закоммить только файлы этапа (включая wiki-изменения из шага 6). `git push` не делать.

## Правила

- `report = полный итог`
- `CHANGELOG = краткая история`
- `handoff = текущее состояние` (переписывается, не дополняется)
- Не обновлять `CHANGELOG.md` для чисто документационных правок без продуктового изменения.
- `CONTEXT_HANDOFF.md` — рабочий handoff для следующего агента, не история проекта.
- Расхождение чисел отчёт ↔ structured artifact (JSON/CSV) — блокирующая ошибка (`docs/methodology/16-reporting-audit.md`).

## Common Mistakes

| Ошибка | Исправление |
|---|---|
| Header отчёта не по шаблону | Следовать `docs/reports/README.md`: русские поля `**Дата:**` / `**Статус:**` / `**Вердикт:**` / `**Цель:**`, дата без времени |
| `Статус` и `Вердикт` смешаны | `Статус` = факт завершения (`Completed`); `Вердикт` = исход (`PASS`/`FAIL`/`DIAGNOSTIC_ONLY`/`UNKNOWN`, см. `docs/methodology/README.md`) |
| Для ML-этапа пропущены секции `methodology/16` | Добавить `Multiple Testing Context` и `Validation Split Disclosure` (`docs/methodology/16-reporting-audit.md`) |

## Образец CHANGELOG.md

~~~markdown

## [YYYY-MM-DD] — Краткое описание
### Добавлено/Изменено/Исправлено
### Результаты
### Вывод
<!-- docs/reports/YYYY-MM-DD-topic.md -->
~~~
