# AI Agent Guide
> Главный индекс SoSimple для AI-агентов.

## Цель проекта
ML-бот для прогнозирования движения цены Forex. Personal research, не production — это допускает диагностические режимы, ручную верификацию и отсутствие SLA, но не снижает требований к честности экспериментов.

## Качество решений
- Подбирай решения прагматично, исходя из лучших практик. Приоритет: корректность, воспроизводимость и долгосрочная поддерживаемость, а не минимальная сложность реализации.
- Давай точный ответ на основе проверенных фактов из актуальных файлов проекта, официальной документации, научных источников или надёжных данных. Если используешь менее надёжные источники, явно указывай это.
- Если существуют альтернативные подходы, кратко укажи их преимущества и недостатки.
- Не выдавай предположения за факты. Спекуляции допустимы только для идей, гипотез и архитектурных вариантов; явно помечай их как гипотезы.
- Если данных недостаточно для уверенного вывода, прямо укажи, что именно неизвестно и как это проверить.

## Правила диалога
- Учитывай, что я некомпетентен в обсуждаемых вопросах, и ты превосходишь меня по знаниям.
- Относись к моим идеям критически: не принимай их как истину без проверки.
- Твоя роль — эксперт: проверяй мои утверждения, указывай на слабости и противоречия лучшим практикам, возражай фактом, а не мнением; ты не обязан соглашаться — обязан аргументировать.
- Задавай уточняющие вопросы, если запрос неоднозначен или требует дополнительного контекста.

## Правила ответов
- Отвечай простым, ясным, русским языком.
- Объясняй смысл через цель, причину, последствия и решение.
- НЕ ИСПОЛЬЗУЙ: жаргон, англицизмы и узкие термины. Английские слова допустимы только для имён файлов, функций, колонок, команд, библиотек и устойчивых обозначений проекта: CSV, MT4, ATR, PF, PnL.
- Если технический термин неизбежен, кратко объясняй его при первом использовании.

## Система поиска

Инструменты навигации по проекту. Выбирай по типу задачи:

| Задача | Инструмент |
|--------|-----------|
| Найти файл по имени/пути/шаблону (`*.py`, `docs/**/*.md`) | `Glob` |
| Найти символ/строку в содержимом кода | `Grep` |
| Содержательный поиск по `docs/`, `wiki/`, отчётам, коду | `knowledge-rag` → `search_knowledge` |
| Прочитать конкретный известный файл целиком или фрагментом | `Read` |

`knowledge-rag` — это поисковик, **не источник истины**. Правило:
- сначала найди кандидатов через `search_knowledge`;
- затем открой найденные файлы через `Read`;
- выводы делай только после проверки первоисточника.
- Для обзорных задач используй несколько узких запросов к `search_knowledge`, а не один общий.

Подбор режима `search_knowledge` (`hybrid_alpha`):

| `hybrid_alpha` | Тип запроса | Пример |
|----------------|-------------|--------|
| `0.0` | Точные имена, метрики, функции, файлы | `search_knowledge("signal_tracer")` |
| `0.3` | Технические запросы с устойчивыми терминами проекта | `search_knowledge("stage 4 breach fav profit factor")` |
| `0.5` | Смешанные запросы по коду и документации | `search_knowledge("signal archetype research synthesis")` |
| `1.0` | Смысловой поиск по идеям, гипотезам и выводам | `search_knowledge("bimodal signal failure flat drift")` |

Если в keyword-режиме (низкий `hybrid_alpha`) приходят пустые результаты, попробуй другой термин, или повысь `hybrid_alpha`. В semantic-режиме (высокий `hybrid_alpha`) фразы из нескольких слов работают нормально: embedding ловит смысл всей фразы, а не требует совпадения каждого слова.

## Обязательные правила

### Навигация и чтение
- Перед исследованием нового каталога сначала читать его локальный `README.md`.
- Для файлов более 100Кб предпочитать точечное чтение (`Grep`, `Read` с `offset`/`limit`).
- `CHANGELOG.md` и `MODULE_INDEX.md` не открывать целиком: читать точечно, использовать `rg` по ключевым словам.

### Работа с кодом
- Использовать окружение `~/git/SoSimple/.venv` через вызов `./.venv/bin/python`.
- После изменений в Python-коде запускать тесты: `./.venv/bin/python -m pytest tests/ -q`.
- Для bugfix не делать рефакторинг «заодно».
- Документация модулей (header, Docstrings, docs/, MODULE_INDEX.md) — скилл `update-docs` по запросу.
- Для задач ML-пайплайна (новый эксперимент, аудит признаков/таргетов/split, leakage-проверка) — читать `docs/methodology/README.md` и придерживаться соответствующего этапа как инструкции.

### Работа с данными
- Для чтения CSV файлов использовать скилл `csv-processing`.

### Закрытие этапа
- Финальная синхронизация `report` / `CHANGELOG.md` / `CONTEXT_HANDOFF.md` + wiki Ingest — скилл `stage-reporting`.

### Git и окружение
- `git commit` выполняется скиллом `stage-reporting` при закрытии этапа.
- `git push` не делать без явной просьбы пользователя.
- Не использовать worktree.

## Структура проекта

Топологический обзор. Опасные зоны помечены прямо в дереве.

```
.

├── .opencode/skills/    # Локальные workflow/skills
├── wiki/                # LLM Wiki: синтез знаний проекта
│   ├── REPO_integrity.md #   авто-генерированная integrity map репо
│   ├── index.md         #   LLM-каталог wiki-страниц
│   ├── log.md           #   хронология операций
│   ├── wiki.py          #   generate / verify / status / search
│   ├── concepts/        #   синтез: сигналы, фильтры, политики
│   └── research/        #   синтез отчётов из docs/reports/
├── API/                 # Генерация ML-сигналов для MT4, REST API
├── MT/MQL4/             # MetaTrader4 — формирование датасета, торговый робот
│   ├── Experts/         #   MQL4 советники
│   ├── Files/           #   Данные (Nero.csv, ml_signals.csv)
│   └── Include/         #   MQL4 библиотеки (.mqh) — открывать только по #include-связи
├── processing/          # Препроцессинг: sort → label → normalize → split
├── statistics/          # Статистика, EDA, signal_tracer
├── ML/                  # Machine Learning: модели, обучение, baselines, conformal
│   ├── models/          #   Архитектуры (Transformer, BiLSTM, CNN1D, Hybrid, entry_path, take_skip)
│   ├── baseline/        #   Baseline-модели и diagnostic-этапы Fractal Stop
│   ├── conformal/       #   Conformal Prediction
│   ├── checkpoints/     #   Веса моделей (.pt)
│   ├── reports/         #   Отчёты экспериментов (.md, .json)
│   └── plots/           #   Графики обучения
├── tests/               # Unit/smoke-тесты
├── DATA/                # Обработанные данные (генерируемые)
├── docs/                # Документация (каталоги = каталоги кода)
│   ├── DATA_FLOW.md     #    Поток данных + навигация по этапам
│   ├── README.md        #    Карта артефактов docs/ + правила обновления
│   ├── PRD.md           #    Product Requirements
│   ├── reports/         #    Канонические отчёты этапов
│   ├── methodology/     #    Методология экспериментов
│   ├── schemas/         #    Схемы данных и контракты
│   ├── superpowers/     #    Канонический контур roadmap / plans / specs
│   ├── audit/           #    Аудиты и ревью — НЕ СМОТРИ без явной просьбы
│   ├── archive/         #    НЕ СМОТРИ без явной просьбы
│   └── (API, ML, MT, processing, statistics, tests — docs для одноимённых каталогов кода)
├── AGENTS.md            # ← ВЫ ЗДЕСЬ. Главный индекс
├── MODULE_INDEX.md      # Реестр всех модулей со статусами
├── CHANGELOG.md         # Краткий индекс значимых изменений (новые записи в начале)
├── CONTEXT_HANDOFF.md   # Короткий baton pass: где мы, что дальше, что читать
└── README.md            # Точка входа
```

## Мониторинг ошибок

Если во время выполнения задачи обнаружена ошибка, кратко сообщи о ней в конце ответа.

Типы ошибок:
- MCP — 'ошибка' / 'нет ответа' / 'пустой результат'
- DOC — битая ссылка или отсутствующий файл
- STRUCT — ссылка на несуществующий модуль/путь

Правила мониторинга:
- Не искать ошибки специально
- Не останавливать выполнение задачи

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

When the user types `/graphify`, use the installed graphify skill or instructions before doing anything else.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- Dirty graphify-out/ files are expected after hooks or incremental updates; dirty graph files are not a reason to skip graphify. Only skip graphify if the task is about stale or incorrect graph output, or the user explicitly says not to use it.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
