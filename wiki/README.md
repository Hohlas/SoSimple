# wiki/

Карта wiki-слоя для AI-агентов. Полный workflow работы с wiki живёт в
[`../.claude/skills/my/wiki/SKILL.md`](../.claude/skills/my/wiki/SKILL.md).

Wiki хранит синтезированные выводы по исследованиям и устойчивые концепты. Это
не source of truth для кода, контрактов данных, текущего состояния задачи или
сырых результатов экспериментов.

## Артефакты

| Артефакт | Роль | Когда читать |
|---|---|---|
| [`index.md`](index.md) | Каталог wiki-страниц | Всегда первым при работе с wiki |
| [`research/`](research/) | Синтез линий исследований по нескольким отчётам | Нужен контекст прошлых экспериментов и решений |
| [`concepts/`](concepts/) | Устойчивые проектные концепты | Нужны определения и практические следствия |
| [`log.md`](log.md) | Хронология операций wiki | Нужно понять, что и когда обновлялось |
| [`REPO_integrity.md`](REPO_integrity.md) | Сгенерированная integrity map репозитория | Нужно проверить покрытие и хеши после генерации |
| [`wiki.py`](wiki.py) | Утилита wiki | Проверка статуса, поиск, генерация integrity map |

## Порядок чтения

1. `wiki/index.md`.
2. Релевантная страница из `wiki/research/` или `wiki/concepts/`.
3. Первичные источники по ссылкам: `docs/reports/*.md`, structured artifacts
   или код.

## Команды

```bash
./.venv/bin/python wiki/wiki.py status
./.venv/bin/python wiki/wiki.py search "<term>"
./.venv/bin/python wiki/wiki.py generate
```
