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
| Найти файл по имени/пути/шаблону (`*.py`, `docs/**/*.md`) | `rg --files` / `Glob` |
| Найти точную строку, символ, колонку, метрику | `rg` / `Grep` |
| Найти прошлые выводы, отчёты, планы, wiki-контекст | `knowledge-rag` → `search_knowledge` |
| Понять связи, соседние понятия, путь между сущностями | `graphify query/path/explain` |
| Прочитать конкретный известный файл целиком или фрагментом | `Read` |

## Обязательные правила

### Навигация и чтение
- Перед исследованием нового каталога сначала читать его локальный `README.md`.
- Для файлов более 100Кб предпочитать точечное чтение (`Grep`, `Read` с `offset`/`limit`).
- `CHANGELOG.md` и `MODULE_INDEX.md` не открывать целиком: читать точечно, использовать `rg` по ключевым словам.

### Работа с кодом и документацией
- Использовать окружение `~/git/SoSimple/.venv` через вызов `./.venv/bin/python`.
- После изменений в Python-коде запускать тесты: `./.venv/bin/python -m pytest tests/ -q`.
- Для bugfix не делать рефакторинг «заодно».
- Для задач ML-пайплайна (новый эксперимент, аудит признаков/таргетов/split, leakage-проверка) — скилл `methodology-processing`.
- Для чтения CSV файлов - скилл `csv-processing`.
- Финальная синхронизация `report` / `CHANGELOG.md` / `CONTEXT_HANDOFF.md` + wiki Ingest — скилл `stage-reporting`.
- `git push` не делать без явной просьбы пользователя.

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

This project has a knowledge graph.

Use the installed graphify skill for document/code navigation and relationship discovery, not as the source of truth.
Verify important conclusions in original project files before changing code or making final claims.

Rules:
- Use Graphify for relationships, paths, neighboring concepts, and architecture navigation when the graph is available.
- Use `graphify path "<A>" "<B>"` for relationships between two concepts.
- Use `graphify explain "<concept>"` for focused concept lookup.
- Skip Graphify only when the task is about stale/incorrect graph output or the user explicitly says not to use it.
- Do not treat Graphify as a replacement for reading original files, local `README.md`, tests, or methodology rules.

## knowledge-rag

Use `knowledge-rag` skill first for project memory: reports, wiki, plans, prior decisions, and cross-document context.
