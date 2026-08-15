# workflow/

Мульти-агентные workflow для проекта SoSimple. Каждый скрипт — самодостаточная
оркестрация через рантайм Qoder (фазы, параллельные агенты, споры, арбитр).

## Скрипты

| Скрипт | Назначение | Фазы | Модель | Вход | Выход |
|--------|-----------|------|--------|------|-------|
| `retrospective-workflow.js` | Ретроспектива проекта: карта направлений, синтез, верификация фактов | Разведка → Чтение → Синтез → Верификация | любая | `CHANGELOG.md` (Grep-индекс), `docs/reports/`, `ML/reports/` (search_knowledge), `wiki/research/` | `docs/audit/retrospective.md` |
| `idea_brainstorm.js` | Часть 1 брэйншторма: 4 параллельных генератора гипотез по пересекающимся векторам | Генерация → Запись | сильная | `docs/audit/retrospective.md` | `docs/audit/brainstorm-raw.json` |
| `idea_check.js` | Часть 2 брэйншторма: кластеры, споры автор × критик (3 раунда), синтез-арбитр | Чтение → Кластеры → Споры → Арбитр → Верификация | дешёвая | `docs/audit/brainstorm-raw.json`, `docs/audit/retrospective.md` | `docs/audit/brainstorm-ideas.md`, `docs/audit/brainstorm-filtered.md` |
| `brainstorm-workflow.js` | Монолитный брэйншторм (части 1+2 в одном скрипте, без промежуточного JSON) | Генерация → Кластеры → Споры → Арбитр → Верификация | любая | `docs/audit/retrospective.md` | `docs/audit/brainstorm-ideas.md`, `docs/audit/brainstorm-filtered.md` |

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
        |                                    |
        |                                    v
        |                           idea_check.js ---> brainstorm-filtered.md
        |
        +---> brainstorm-workflow.js ---> brainstorm-filtered.md
              (монолитный вариант, без промежуточного JSON)
```
