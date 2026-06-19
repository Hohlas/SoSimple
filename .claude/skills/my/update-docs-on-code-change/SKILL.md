---
name: update-docs-on-code-change
description: Use when code files change and documentation needs to stay in sync — file headers, docs/, MODULE_INDEX.md, or DATA_FLOW.md are stale relative to implementation
---

# Синхронизация документации

Синхронизация описания модулей с кодом: file headers, `docs/<category>/<module>.md`, `MODULE_INDEX.md`, `docs/DATA_FLOW.md`, wiki integrity. Source of truth для правил обновления `docs/` — `docs/README.md`.

## Когда использовать
- Пользователь просит обновить документацию одного файла (`doc this <path>`).
- Пользователь просит массово синхронизировать docs после изменений (`sync docs`).
- Добавлен новый модуль — нужно создать docs + запись в индексе (`create module`).
- Изменились CLI, входы/выходы или назначение существующего модуля (`doc this`).
- Добавлено несколько файлов или явный запрос пересборки `MODULE_INDEX.md` (`rebuild index`).

## Когда НЕ использовать
- Закрытие этапа, отчёт в `docs/reports/`, запись в `CHANGELOG.md`, перепись `CONTEXT_HANDOFF.md` → `my:stage-reporting`.
- Полный wiki Ingest (синтез отчётов в wiki-страницы) → `my:wiki` (напрямую, либо через `my:stage-reporting` при закрытии этапа).
- Задачи ML-пайплайна (признаки/таргеты/split/leakage) → сначала `docs/methodology/README.md`.

## Область
Код: `*.py`, `*.mq4`, `*.mqh`, `*.ipynb`. `*.md` попадает в обнаружение изменений `git diff` (Mode 2), но header на `.md` не накладывается.

## Mapping: каталог кода → docs/
| Каталог кода | docs/ |
|---|---|
| `processing/` | `docs/processing/` |
| `statistics/` | `docs/statistics/` |
| `API/` | `docs/API/` (ML-сигнальные интеграции — также `docs/MT/`) |
| `ML/` | `docs/ML/` |
| `MT/MQL4/` | `docs/MT/` |
| `tests/` | `docs/tests/` |

Примечание: изменение полей фрактала в `lib_PIC.mqh` → также `docs/schemas/` (контракт MT4↔Python).

## Шаблон file header

### Python (.py)
В проекте сосуществуют два канона. Выбирай по типу файла:

**Расширенный русский** (инфраструктура: `processing/`, `ML/data_loader.py`, `ML/train.py`):
```python
# =============================================================================
# Файл: [filename.py]
# Назначение: [одна строка]
# Язык: Python 3.10+
# Обновлён: [YYYY-MM-DD]
# Входные данные:
#   - [путь/файл] (откуда: [источник])
# Выходные данные:
#   - [путь/файл] (куда: [назначение])
# Использование:
#   python [filename.py] [аргументы]
# =============================================================================
```

**Английский compact** (Stage-раннеры `ML/baseline/benchmark_stage*.py`, diagnostic-скрипты):
```python
# =============================================================================
# File: [path/filename.py]
# Purpose: [one line]
# Input: [path/file]
# Output: [path/file]
# Language: Python 3.10+
# Created: [YYYY-MM-DD]
# Updated: [YYYY-MM-DD]
# =============================================================================
```
Не переделывать существующий header без необходимости — соблюдать канон каталога.

Обновлять header при изменении: назначения, входов/выходов, CLI. Не обновлять при рефакторинге внутренней логики.

### MQL4 (.mqh / .mq4) — только если есть #include-связь с задачей
Box-стиль (большинство `.mqh`):
```cpp
//+------------------------------------------------------------------+
//| Файл: [filename.mqh]                                             |
//| Назначение: [одна строка]                                        |
//| Обновлён: [YYYY-MM-DD]                                           |
//| Зависимости: [файл.mqh]                                          |
//+------------------------------------------------------------------+
```
Doxygen `//!`-стиль также встречается (например `lib_PIC.mqh`) — не переделывать.
Кодировка `.mqh`/`.mq4` в репо — UTF-8 (с кириллицей); `Nero.csv` — ASCII. Проверяй `file` перед правкой, не считать UTF-16LE обязательным (см. `docs/DATA_FLOW.md`).

## Docstrings (Google Style)
Писать: публичные функции с нетривиальной логикой, все классы, публичные методы. Не писать: приватные хелперы (`_foo`), функции с говорящим именем и ≤3 строками тела. Описание shape массивов обязательно: `shape (N, 20)`.
```python
def compute_quantile_score(predictions: np.ndarray, threshold: float) -> np.ndarray:
    """Вычисляет бинарный сигнал по квантильному порогу.

    Аргументы:
        predictions: Массив предсказаний, shape (N,).
        threshold: Квантильный порог [0.0, 1.0].

    Возвращает:
        Бинарный массив сигналов shape (N,), 1 = активная позиция.
    """
```
Классы — аналогично с секцией `Атрибуты:`. Однострочный docstring — для очевидных хелперов.

## Режимы

### 1) `doc this <path>` / `document <path>`
1. Проверить header; если нет — создать по шаблону.
2. Создать/обновить `docs/<category>/<module>.md` (mapping выше).
3. Добавить/обновить строку в `MODULE_INDEX.md`.
4. Если модуль в pipeline — синхронизировать `docs/DATA_FLOW.md`.

### 2) `sync docs` / `обнови документацию`
1. `git diff --name-only -- '*.py' '*.mq4' '*.mqh' '*.ipynb' '*.md'`
2. Для каждого кодового файла (`*.py`/`*.mq4`/`*.mqh`/`*.ipynb`) обновить связанный `.md` по mapping. Для `.md`-файлов в diff — проверить актуальность содержания, header не накладывается.
3. В docs отразить: назначение, входы/выходы, запуск, ограничения.

### 3) `create module <name>`
1. Создать кодовый файл с header.
2. Создать `docs/<category>/<name>.md`.
3. Добавить в `MODULE_INDEX.md`.
4. При необходимости — шаг в `docs/DATA_FLOW.md`.

### 4) `rebuild index` / пересборка MODULE_INDEX.md
При добавлении нескольких файлов или явном запросе.
1. Glob: `**/*.py`, `**/*.mq4`, `**/*.mqh`, `**/*.ipynb`; исключить `.venv/`, `__pycache__/`, `.git/`, `docs/archive/`.
2. Извлечь из header: `Назначение`, `Вход → Выход`, `Docs` (по mapping, если файл существует).
3. Обновить секции `MODULE_INDEX.md` (`processing`, `statistics`, `API`, `MT/MQL4`, `ML`, `tests`); колонки `Модуль | Назначение | Вход → Выход | Docs | Статус`.
4. Валидация Grep: найти `^\| \[` в `MODULE_INDEX.md`, проверить отсутствие битых ссылок.

Правила:
- Статусы переносить из текущего `MODULE_INDEX.md` или ставить `⚠️`; не придумывать.
- Header неполный → `-`, не блокировать обновление.

## Правила качества
- Не дублировать подробные docstrings в `.md`; в `.md` — обзор и ссылки.
- `CHANGELOG.md`, `docs/reports/`, `CONTEXT_HANDOFF.md` — зона `my:stage-reporting`; здесь не ведутся.

## Wiki integrity
После docs-правок проверь целостность wiki:
- `python wiki/wiki.py status` — coverage gaps (непокрытые отчёты), staleness, **broken wiki links**.
- `python wiki/wiki.py verify` — целостность против файловой системы (изменённые/добавленные/удалённые файлы по хешам `REPO_integrity.md`).
- `python wiki/wiki.py generate` — обновить `REPO_integrity.md` после docs-правок (иначе `verify` репортит ложные «Changed»). При закрытии этапа это делает `my:wiki` Ingest; для standalone-запуска выполни вручную.

Если изменение затрагивает выводы/поведение, описанные в `wiki/index.md` — не выполнять частичный Ingest здесь; предложить `my:wiki` Ingest (напрямую, либо через `my:stage-reporting` при закрытии этапа).

## Common mistakes
| Ошибка | Исправление |
|---|---|
| docs не обновлены после изменения CLI | Обновить секцию `Использование` в header и в docs |
| новый модуль есть в коде, но нет в `MODULE_INDEX.md` | Добавить строку в соответствующий раздел |
| дублирование описаний между несколькими docs | Оставить одну source-of-truth страницу, в остальных ссылки |
| правка `.mqh` «как UTF-16LE» ломает кодировку | Проверить `file` перед правкой; фактическая кодировка UTF-8 |
| broken links проверяют через `wiki.py verify` | broken links → `status`; `verify` = целостность (хеши `REPO_integrity.md`) |
| `verify` репортит «Changed» после docs-правок | Выполни `wiki.py generate` для обновления `REPO_integrity.md` |
