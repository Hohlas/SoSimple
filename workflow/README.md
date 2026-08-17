# workflow/

Мульти-агентные workflow для проекта SoSimple. Каждый скрипт — самодостаточная
оркестрация через рантайм Qoder (фазы, параллельные агенты, споры, арбитр).

## Скрипты

| Скрипт | Назначение | Фазы | Модель | Вход | Выход |
|--------|-----------|------|--------|------|-------|
| `retrospective-workflow.js` | Ретроспектива проекта: карта направлений, синтез, верификация фактов | Разведка → Чтение → Синтез → Верификация | любая | `CHANGELOG.md` (Grep-индекс), `docs/reports/`, `ML/reports/` (search_knowledge), `wiki/research/` | `docs/audit/retrospective.md` |
| `idea_brainstorm.js` | Часть 1 брэйншторма: 4 параллельных генератора гипотез по пересекающимся векторам (4–6 идей на вектор) | Генерация → Запись | сильная | `docs/audit/retrospective.md` | `docs/audit/brainstorm-raw.json` |
| `idea_check.js` | Часть 2 брэйншторма: фильтр жёсткого запрета, споры автор × критик на каждую гипотезу (3 раунда), синтез-арбитр | Чтение входа → Фильтр → Споры → Арбитр → Верификация | дешёвая | `docs/audit/brainstorm-raw.json`, `docs/audit/retrospective.md` | `docs/audit/brainstorm-protocols.md`, `docs/audit/brainstorm-filtered.md` |

`idea_check.md` — та же процедура, что `idea_check.js`, транслированная под
opencode (Task / Write / bash / TodoWrite вместо рантайма Qoder).

## Цепочка запуска

```
retrospective-workflow.js
        |
        v
  docs/audit/retrospective.md
        |
        +---> idea_brainstorm.js ---> docs/audit/brainstorm-raw.json
                                             |
                                             v
                                    idea_check.js ---> brainstorm-protocols.md
                                                       brainstorm-filtered.md
```

## Использование

- **Запуск.** Скрипты `.js` — через рантайм Qoder (Workflow по имени скрипта).
  `idea_check.md` — вручную: отдать файл агенту opencode как инструкцию.
- **Модель выбирается в запускающей сессии.** Часть 1 — сильная модель,
  часть 2 — дешёвая (все вызовы, включая арбитр).
- **Перед повторным прогоном** перенести прежние `brainstorm-*` из
  `docs/audit/` в `docs/archive/` и дать индексу knowledge-rag обновиться:
  иначе агенты цитируют прошлые прогоны как прецедент.
- **Порядок строгий**: часть 2 не запускать без свежего
  `docs/audit/brainstorm-raw.json`; каждый скрипт сам проверяет вход и
  собственные выходы (фаза «Верификация»).
- **Стоимость части 2** = гипотезы × 2–3 вызова агента; аварийный потолок —
  `MAX_IDEAS = 30`, хвост сверх него не спорится и помечается «не оценивались».
- **Итог для чтения** — `brainstorm-filtered.md` (короткий список, таблица,
  убитые, понижения арбитра); `brainstorm-protocols.md` — дословные протоколы
  споров для аудита вердиктов.
