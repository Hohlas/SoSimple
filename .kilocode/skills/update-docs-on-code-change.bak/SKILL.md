---
name: update-docs-on-code-change
description: Use when creating new modules, adding documentation to existing files, syncing docs after code changes, validating documentation currency, or when AGENTS.md exceeds 200 lines and needs refactoring
---

# Управление документацией

## Overview

Комплексное управление документацией: создание новых модулей с правильными headers, добавление документации к существующим файлам, синхронизация при изменениях кода и валидация актуальности.

## When to Use

- Создание новых Python, MQL4 или Jupyter модулей
- Добавление документации к существующим недокументированным файлам
- После изменений в коде нужно обновить документацию
- Проверка актуальности документации
- AGENTS.md превышает 200 строк или появился task-specific контент
- Команды: "create module [name]", "new script [name]", "doc this [file]", "document [file]", "sync docs", "обнови документацию", "check docs", "validate docs", "refactor agents.md"

Applies to: `*.py`, `*.mq4`, `*.mqh`, `*.ipynb`, `*.md` файлы

---

## File Header Templates

**Полные шаблоны**: См. [templates/file-headers.md](templates/file-headers.md)

- **Python (.py)**: `# ===...===` рамка с зависимостями, входами/выходами
- **MQL4 (.mqh/.mq4)**: `//+--...--+` рамка (**UTF-16LE кодировка!**)
- **Jupyter (.ipynb)**: Markdown-ячейка с метаданными
- **Docstrings**: Google-style для Python (module-level, functions, classes)
- **Языковые соглашения**: Русский для docs, английский для кода
- **Markdown docs template**: Стандартная структура для `docs/[category]/[file].md`

---

## Принципы компактности документации

- Одна мысль = одно предложение
- Избегай повторений между файлами — используй ссылки: `[текст](путь/к/файлу.md#секция)`
- Используй таблицы вместо списков для сравнений
- Максимум 250 строк на документ (кроме справочников)
- Если информация уже существует в другом документе — добавь ссылку, не копируй
- Исключение: критичная информация (AGENTS.md) может дублироваться
- Если документ > 300 строк: вынеси детали в отдельный файл, оставь резюме + ссылку

### Примеры

#### ✅ Link to detailed documentation
```markdown
## Data Flow
Полное описание потока данных: [DATA_FLOW.md](docs/DATA_FLOW.md)

### Краткая схема
MT4 → Nero.csv → Сортировка → Маркировка → Нормализация
```

#### ✅ Link instead of duplication
```markdown
## Dataset Structure
Детали: [dataset_description.md](docs/dataset_description.md)
```

---

## MODULE_INDEX.md Format

**Формат записи в MODULE_INDEX.md:**
```markdown
## [путь/файл]
**Назначение**: [одна строка]
**Входы**: [файлы] | **Выходы**: [файлы]
**Использует**: [библиотеки] | **Используется в**: [скрипты]
```

**Пример:**
```markdown
## processing/label_main.py
**Назначение**: CLI оркестратор для полного конвейера обработки данных
**Входы**: MT/MQL4/Files/Nero.csv | **Выходы**: data/Nero_train_labeled.csv
**Использует**: pandas, numpy | **Используется в**: ML training pipeline
```

---

## Режим 1: Создание нового модуля

**Команда**: `create module [имя]` или `new script [имя]`
**Назначение**: Создать новый модуль со всей необходимой документацией

### Когда использовать

- Создание новых Python, MQL4 или Jupyter модулей
- Команды: "create module [name]", "new script [name]"

### Шаги

#### Шаг 0: Проверить связанные skills

Перед созданием модуля загрузить соответствующие skills:
- Для .py: данный skill (шаблоны выше)
- Для .mqh/.mq4: ссылаться на .kilocode/skills/mql4-processing/
- Для .ipynb: ссылаться на .kilocode/skills/jupyter-processing/

#### Шаг 1: Определить параметры

- Директория (processing/statistics/ML)
- Назначение (одна строка)
- Входные/выходные данные

#### Шаг 2: Создать file header

Использовать точный шаблон из [templates/file-headers.md](templates/file-headers.md):
- Для Python: `# ====` рамка
- Для MQL4: `//+--+` рамка (UTF-16LE!)
- Для Jupyter: Markdown ячейка

#### Шаг 3: Создать markdown документацию

Создать `docs/[category]/[filename].md` по шаблону из [templates/file-headers.md](templates/file-headers.md#markdown-documentation-template)

#### Шаг 4: Обновить MODULE_INDEX.md

Добавить запись в MODULE_INDEX.md по формату выше.

**Также обновить:**
- DATA_FLOW.md если участвует в pipeline
- AGENTS.md если критичный компонент

#### Шаг 5: Валидация

- Проверить file header: все поля заполнены?
- Проверить кодировку (особенно для MQL4: UTF-16LE)
- Проверить ссылки в документации

**Пример:**
```
> create module feature_engineering
Директория: processing
Назначение: Создание дополнительных признаков из фракталов
Входы: Nero_normalized.csv
Выходы: Nero_features.csv
✅ Создан processing/feature_engineering.py
✅ Создан docs/data_preprocessing/feature_engineering.py.md
✅ Обновлён MODULE_INDEX.md
✅ File header проверен
✅ Кодировка UTF-8 (Python)
```

---

## Режим 2: Документирование существующего модуля

**Команда**: `doc this [файл]` или `document [файл]`
**Назначение**: Создать полную документацию для существующего недокументированного модуля

### Шаги

1. Проверить наличие file header в коде
   - Если нет → создать по File Header шаблоны
2. Создать `docs/[категория]/[модуль].md` по шаблону из Режим 1, Шаг 3
3. Добавить запись в MODULE_INDEX.md
4. Обновить DATA_FLOW.md (если участвует в pipeline)
5. Показать diff и запросить подтверждение

**Пример:**
```
> doc this processing/normalize.py
Создаю документацию...
- ✅ File header добавлен
- ✅ docs/data_preprocessing/normalize.py.md создан
- ✅ MODULE_INDEX.md обновлён
```

---

## Режим 3: Синхронизация документации (sync docs)

**Команда**: `sync docs`, `обнови документацию`, `синхронизируй docs`
**Назначение**: Обновить документацию после изменений в коде

### Когда использовать

- Пользователь говорит: `sync docs`, «обнови документацию», «синхронизируй docs».
- Пользователь сообщает, что изменил конкретный файл и просит обновить документацию.
- После серии изменений в коде перед подготовкой PR/merge.

### Высокоуровневый алгоритм

1. Определить изменённые файлы.
2. Найти соответствующую им документацию (см. references/file-mappings.md).
3. Обновить элементы документации в коде и .md‑файлах.
4. Проверить размеры файлов и при необходимости предложить разбиение.
5. Показать diff и запросить подтверждение перед внесением изменений.

### Подробные шаги

#### Шаг 1. Найди изменённые файлы

1. Если пользователь явно указал файлы — используй их.
2. Иначе выполни в корне репозитория:

   ```bash
   git diff --cached --name-only | grep -E '\.(py|mq4|mqh|ipynb|md)$'
   ```
3. Игнорируй файлы вне указанных расширений.

#### Шаг 2. Определи соответствующую документацию
Для каждого изменённого файла определи связанный .md/архитектурный файл:

- processing/[script].py → docs/data_preprocessing/[script].md
- statistics/[script].py → docs/data_analysis/[script].md
- MT/MQL4/Include/[lib].mqh → docs/DATA_FLOW.md (секция Pipeline)

Если соответствующий .md ещё не существует, предложи его создать.

#### Шаг 3. Обнови элементы документации

В коде:

- В file header обнови поле Обновлён: на текущую дату в формате YYYY-MM-DD.
- Обнови docstrings, если изменились сигнатуры функций, аргументы, возвращаемые значения или исключения.

В связанном .md‑файле (если существует):

- Назначение — обнови, если изменилась функциональность.
- Входные данные — обнови, если изменились форматы или источники.
- Выходные данные — обнови, если изменились форматы или потребители.
- Использование — обнови пример запуска и параметры, если они изменились.
- Примечания — добавь новые ограничения или важные особенности.

**Принцип Single Source of Truth**: Не дублируй информацию между docstrings и .md файлами.
- Детальная документация API → храни в docstrings кода
- В .md файле дай общее описание модуля и используй `@file` ссылки:
  ```markdown
  ## API Reference
  Детали реализации: @ML/train.py:150
  ```

В docs/DATA_FLOW.md (если нужно):

- Обнови секцию Pipeline, если изменились входы/выходы шагов конвейера или их связи.

В CHANGELOG.md (только при значимых изменениях продукта):

- Добавь запись ТОЛЬКО при значимых изменениях функциональности: новые фичи, breaking changes, багфиксы, изменения, влияющие на совместимость.
- НЕ добавляй записи, если: проведены правки документации или рефакторинг без изменения поведения.
- Используй формат: `## [YYYY-MM-DD] — Краткое описание`
- Структурируй изменения секциями: ### Добавлено, ### Изменено, ### Исправлено
- Укажи затронутые файлы и ключевые изменения с точки зрения продукта

#### Шаг 4. Проверь размеры файлов

Для каждого обновляемого .md файла:

```bash
wc -l <файл>
```
Если файл >500 строк:
1. Предложи разбить на логические части
2. Для каждой части создай отдельный .md файл:
3. В исходном файле оставь оглавление со ссылками @

#### Шаг 5. Покажи diff и запроси подтверждение

1. Сгенерируй сводку изменений в стиле:

```bash
Файл: docs/data_preprocessing/normalize.py.md
+ ## Входные данные
+ - **Файл**: `Nero.csv` (было: `data.csv`)
```

2. Явно спроси пользователя: Применить изменения? (yes/no)

3. Только после явного подтверждения внеси изменения в файлы.

---

## Режим 4: Валидация документации (check docs)

**Команда**: `check docs`, `validate docs`
**Назначение**: Проверить актуальность документации относительно кода

### Шаги

1. Найти все .py/.mqh/.ipynb .md с file headers
2. Для каждого:
   - Проверить наличие соответствующего .md
   - Сравнить дату "Обновлён" в header с git log
   - Проверить наличие в MODULE_INDEX.md
   - Проверить соответствие ссылок @ в .md
   - Проверить размер .md файла (< 500 строк)
   - Проверить наличие дублирования docstrings в .md (искать полные описания функций)
3. Вывести отчёт:
   - ❌ Нет документации
   - ⚠️ Документация устарела (код изменён позже)
   - ⚠️ Файл слишком большой (> 500 строк)
   - ✅ Документация актуальна

Пример отчёта:
```
📊 ОТЧЕТ ПО ДОКУМЕНТАЦИИ:

📄 AGENTS.md:
   ✅ Размер: 187/200 строк
   ✅ Структура: оптимальная

📚 Документация к коду:
   ❌ processing/new_script.py — нет docs/data_preprocessing/new_script.py.md
   ⚠️  processing/normalize.py — дублирование docstrings в .md
   ✅ processing/label_main.py — актуально, ссылки @

📏 Размеры .md файлов:
   ⚠️  docs/advanced/ml_models.md — 623/500 строк (нужен рефакторинг)

📋 CHANGELOG.md:
   ⚠️  Есть 3 записи об изменениях документации (не соответствуют назначению)

📋 ИТОГОВЫЙ ЧЕКЛИСТ:
   ✅ AGENTS.md < 200 строк? ✅
   ✅ Нет дублирования docstrings? ⚠️ (1 файл)
   ❌ CHANGELOG.md только для значимых изменений? ❌ (3 лишних записи)
```

---

## Режим 5: Рефакторинг AGENTS.md (refactor agents.md)

**Команда**: `refactor agents.md`, `split agents.md`
**Назначение**: Структурированный рефакторинг AGENTS.md при превышении лимита строк или появлении task-specific контента

### Когда использовать

- AGENTS.md > 200 строк
- Появился task-specific контент (ML, MQL4, deploy)
- Дублирование между AGENTS.md и другими документами
- Нужно добавить новый компонент в проект

### Архитектура документации (3-Tier System)

| Tier | Файл | Размер | Содержание |
|------|------|--------|------------|
| 1 | AGENTS.md | < 200 строк | Критическая информация, quick start, архитектура |
| 2 | .kilocode/skills/*/SKILL.md | < 500 строк | Домен-специфичные workflow (skills) |
| 3 | docs/**/*.md | По необходимости | Детальная документация компонентов |

### Что оставлять в AGENTS.md

| Содержание | Где разместить |
|------------|----------------|
| Описание проекта (1 строка) | AGENTS.md |
| Quick start (3 команды) | AGENTS.md |
| Critical constraints | AGENTS.md (в начале!) |
| Архитектура (overview) | AGENTS.md |
| Ключевые паттерны (1 строка) | AGENTS.md |
| Workflow для ML | skill `ml-pipeline` |
| Workflow для MQL4 | skill `mql4-processing` |
| Детали API | docs/ml/neural_networks.md |
| Deployment инструкции | docs/deploy.md |

### Phase 1: Audit (Обязательно!)

**Шаг 1.1: Подсчитать строки**
```bash
wc -l AGENTS.md
wc -l .kilocode/rules/*.md
```

**Шаг 1.2: Найти task-specific контент**
Разметить каждую секцию AGENTS.md:
| Секция | Тип | Действие |
|--------|-----|----------|
| Quick start | Foundation | Оставить |
| ML pipeline details | Component | Вынести в rules/ml.md |
| MQL4 encoding | Component | Вынести в rules/mql4.md |
| Deployment | Feature | Вынести в docs/deploy.md |

**Шаг 1.3: Найти дублирование**
Сравнить с:
- README.md
- docs/DATA_FLOW.md
- MODULE_INDEX.md

### Phase 2: Extract (Вынести компоненты)

**Шаг 2.1: Создать component rules**

Для каждого task-specific раздела создать `.kilocode/rules/[component].md`:
- Добавить YAML frontmatter с `triggers:`
- Включить `globs` для автозагрузки
- Убедиться что размер < 500 строк

**Шаг 2.2: Создать feature docs**
```bash
mkdir -p docs/[feature]
cat > docs/[feature]/guide.md << 'EOF'
# [Feature] Guide

@AGENTS.md:[line]  # Ссылка на архитектуру

## Quick Start
...
EOF
```

**Шаг 2.3: Обновить AGENTS.md**
- Удалить вынесенные секции
- Добавить ссылки:
```markdown
## ML Pipeline
Детали: [.kilocode/rules/ml.md](.kilocode/rules/ml.md)
Руководство: [docs/ml/training_guide.md](docs/ml/training_guide.md)
```

### Phase 3: Validate (Проверить)

**Шаг 3.1: Проверить размеры**
```bash
wc -l AGENTS.md  # Должно быть < 200
wc -l .kilocode/rules/*.md  # Каждый < 500
```

**Шаг 3.2: Проверить ссылки**
```bash
# Проверить все markdown ссылки
grep -r '\[.*\](.*\.md)' AGENTS.md .kilocode/rules/ | head -20
```

**Шаг 3.3: Проверить @ ссылки**
Убедиться, что используются `@file` вместо копирования.

### Phase 4: Commit

**Шаг 4.1: Создать коммит**
```bash
git add AGENTS.md .kilocode/rules/ docs/
git commit -m "refactor: split AGENTS.md into modular rules

- Extract [component] rules to .kilocode/rules/[component].md
- Reduce AGENTS.md from XXX to < 200 lines
- Add cross-references with @ syntax"
```

### Работа со skills

При создании нового skill в `.kilocode/skills/`:

1. Добавь YAML frontmatter с `triggers:` для активации:

```markdown
---
name: ml-pipeline
description: Use when working with ML pipeline, training models, or evaluating experiments
triggers:
  - ml pipeline
  - train model
alwaysApply: false
---
```

2. Примеры triggers:
   - `ml pipeline` — активация при упоминании ML
   - `train model` — активация при обучении моделей
   - `mql4` — активация для MQL4 файлов

3. Размер: каждый skill должен быть < 500 строк

---

## Примеры использования

**Пример 1**: Пользователь: `create module feature_engineering`
- Действия:
  - Запросить параметры: директория, назначение, входы/выходы
  - Создать файл с file header по шаблону
  - Создать docs/[category]/feature_engineering.py.md
  - Обновить MODULE_INDEX.md
  - Валидировать header и кодировку

**Пример 2**: Пользователь: `doc this processing/normalize.py`
- Действия:
  - Проверить наличие file header, добавить если нет
  - Создать docs/data_preprocessing/normalize.py.md
  - Добавить в MODULE_INDEX.md
  - Показать diff и запросить подтверждение

**Пример 3**: Пользователь: «Я изменил normalize.py, обнови документацию».
- Действия:
  - Обновить header и docstrings в processing/normalize.py, отражая новые аргументы/поведение.
  - Обновить docs/data_preprocessing/normalize.py.md (назначение, входы/выходы, использование, примечания).
  - Использовать `@processing/normalize.py` вместо дублирования docstrings.
  - Показать diff и запросить подтверждение.

**Пример 4**: Пользователь: `sync docs`
- Действия:
  - Найти все staged файлы через git diff --cached --name-only | grep -E '\.(py|mq4|mqh|ipynb)$'.
  - Для каждого файла найти соответствующий .md/архитектурный документ.
  - Обновить документацию по правилам выше.
  - Проверить размеры файлов (< 500 строк).
  - Показать сводный diff и запросить подтверждение перед применением.

**Пример 5**: Пользователь: `check docs`
- Действия:
  - Проверить все файлы на наличие документации.
  - Сравнить даты с git history.
  - Проверить размеры .md файлов.
  - Вывести отчёт с рекомендациями.

**Пример 6**: Создание нового skill `.kilocode/skills/ml-pipeline/SKILL.md`
- Действия:
  - Добавить YAML frontmatter с `triggers:` для активации.
  - Убедиться, что файл < 500 строк.
  - Использовать `@` ссылки на код вместо дублирования.
  - Обновить AGENTS.md ссылкой на новый skill (не дублируя содержание).

**Пример 7**: Пользователь: `refactor agents.md`
- Действия:
  - Проверить размер AGENTS.md (`wc -l`)
  - Найти task-specific контент (ML, MQL4, deploy)
  - Phase 1: Audit — разметить секции, найти дублирование
  - Phase 2: Extract — создать component rules в `.kilocode/rules/`
  - Phase 3: Validate — проверить размеры (< 200 для AGENTS.md, < 500 для skills)
  - Phase 4: Commit — создать коммит с изменениями

---

## Quality Checklist

Перед завершением работы:

- [ ] File headers обновлены (поле Обновлён)?
- [ ] Docstrings актуальны (совпадают с сигнатурами)?
- [ ] Markdown docs обновлены без дублирования (используются @ ссылки)?
- [ ] AGENTS.md < 200 строк? Если нет — вынеси в skills
- [ ] Каждый skill < 500 строк?
- [ ] Для skills добавлен YAML frontmatter с triggers?
- [ ] CHANGELOG.md обновлён ТОЛЬКО для значимых изменений продукта?
- [ ] MODULE_INDEX.md актуален?
- [ ] DATA_FLOW.md актуален (если изменился pipeline)?
- [ ] Нет дублирования между docstrings и .md файлами?
- [ ] Critical info размещены в начале AGENTS.md?

---

## Common Mistakes to Avoid

| Ошибка | Исправление |
|--------|-------------|
| AGENTS.md > 200 строк | Разбить на skills |
| Task-specific контент в AGENTS.md | Вынести в отдельные rules |
| SQL/API docs в AGENTS.md | Перенести в docs/ или skills |
| Дублирование контента | Использовать `@file` ссылки вместо копирования |
| Дублирование docstrings в .md | Использовать `@file` ссылки |
| CHANGELOG для каждого коммита | Только значимые изменения продукта |
| Skill без triggers | Добавить YAML frontmatter с triggers |
| Skill без globs | Добавить globs для автозагрузки |
| Файлы > 500 строк | Разбить на несколько файлов |
| Не проверять размеры после рефакторинга | Всегда проверять `wc -l` |
| Отрицательные правила без альтернатив | Добавить: "Не X; используй Y" |

---

## Полезные команды

```bash
# Проверить размер AGENTS.md
wc -l AGENTS.md

# Проверить размеры всех .md файлов
find .kilocode/skills docs -name "*.md" -exec wc -l {} \;

# Найти файлы > 500 строк
find .kilocode/skills docs -name "*.md" -exec sh -c 'lines=$(wc -l < "$1"); [ $lines -gt 500 ] && echo "$lines $1"' _ {} \;
```
