# AI Agent Guide
> Главный индекс SoSimple для AI-агентов.

## Цель проекта
ML-бот для прогнозирования движения цены Forex. Personal research, не production — это допускает диагностические режимы, ручную верификацию и отсутствие SLA, но не снижает требований к честности экспериментов.

## Качество решений
- Если входных данных недостаточно или они противоречивы — прямо укажи на это.
- Опирайся на проверяемые первоисточники — документы, содержащие информацию в исходном виде: официальная документация, научные публикации, стандарты и спецификации. При использовании вторичных источников явно указывай их тип и происхождение.
- Подбирай решения прагматично, исходя из лучших практик. Отдавай приоритет обоснованности и точности решения, а не простоте реализации.
- При наличии альтернатив перечисли и аргументируй.
- Отдавай приоритет фактам и обоснованным выводам. Предположения, гипотезы и идеи помечай явно. Домыслы и спекуляции не приводи.

## Правила диалога
- Относись к моим идеям критически: не принимай их как истину без проверки — я могу быть некомпетентен.
- Возражай фактом, а не мнением. Ты не обязан соглашаться — обязан аргументировать.
- Задавай уточняющие вопросы, если запрос неоднозначен или требует дополнительного контекста.

## Правила ответов
- Отвечай простым русским языком.
- Объясняй через цель, причину и последствия.
- Избегай жаргона, англицизмов и узких терминов. Если термин необходим — объясни его при первом использовании.

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
- Для широких вопросов сначала используй скиллы `knowledge-rag`/`graphify` как карту кандидатов; читай только найденные первоисточники точечно.
- Перед исследованием нового каталога сначала читать его локальный `README.md`.
- Для файлов более 60Кб предпочитать точечное чтение (`Grep`, `Read` с `offset`/`limit`), использовать `rg` по ключевым словам.

### Работа с кодом и документацией
- Использовать окружение `~/git/SoSimple/.venv` через вызов `./.venv/bin/python`.
- После изменений для Python запускать минимально достаточные проверки Python `pytest`.
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
