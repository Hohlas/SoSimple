# AI Agent Guide (Codex First)
> Главный индекс SoSimple для Codex.

## Цель проекта
ML-бот для прогнозирования разворотов Forex (H1). Детали: [PRD.md](docs/PRD.md).

## using search_knowledge (RAG system)
При поиске текста и документов используй инструменты MCP сервера knowledge-rag

### Pure keyword search — instant, no embedding needed
search_knowledge("gtfobins suid", hybrid_alpha=0.0)

### Balanced hybrid — both engines equally weighted
search_knowledge("SQL injection techniques", hybrid_alpha=0.5)

### Pure semantic — embedding similarity only
search_knowledge("lateral movement strategies", hybrid_alpha=1.0)

### Incremental Indexing: only re-index changed files (fast)
reindex_documents()

### Smart reindex: detect changes + rebuild BM25
reindex_documents(force=True)


## Быстрый старт

### Пути к данным
- Вход: `MT/MQL4/Files/Nero.csv` (UTF-16LE, `;`)
- Выход: `DATA/Nero_{train|validation|test}_labeled.csv`
- Мета: `DATA/Nero_normalization_stats.csv`

### Critical Rules Top-3
1. Для CSV сначала читать только первые 10 строк.
2. Не загружать в контекст файлы больше 1MB целиком.
3. Файлы `*.mqh`, `*.mq4` из `MT/` открывать только если есть явная `#include`-связь с текущим файлом.

## Pipeline данных
Схема: `MT4 -> Raw -> Sort -> Label -> Norm -> Split -> Train -> Signals -> MT4`.
Детали: [docs/DATA_FLOW.md](docs/DATA_FLOW.md)

## Как работать в этом репозитории (Codex)

### Обязательные правила
- Перед правками в каталоге сначала читать локальный `README.md` этого каталога.
- Предпочитать точечное чтение: `rg`, `head`, `sed`, а не полный вывод больших файлов.
- Не трогать `docs/archive/` и архивные модули без явной просьбы.
- Всегда создавай новую feature-ветку для каждой задачи.
- `git push` не делать без явной просьбы пользователя.
- Для bugfix не делать рефакторинг "заодно".

### Качество изменений
- Изменения должны быть минимальными и по задаче.
- Не добавлять docstrings/comments, если их не было и это не требуется для понимания сложного кода.
- Если у `*.py` файла есть header/docstring с описанием назначения, входов/выходов или секций отчёта, обновлять его вместе с функционалом файла.
- Не добавлять обработку невозможных сценариев.
- Не создавать helper-функции для одноразовой логики.

### Документация, отчёты и handoff
- `CHANGELOG.md` обновлять только при: новых фичах, breaking changes, багфиксах, результатах экспериментов с выводами.
- Не добавлять запись в `CHANGELOG.md` для: правок документации, обновления путей, рефакторинга без изменения поведения.
- Формат записи: `## [YYYY-MM-DD] — Краткое описание`
- Секции: `### Добавлено`, `### Изменено`, `### Исправлено`, `### Результаты`, `### Вывод`
- `docs/reports/` хранит подробные отчёты завершённых этапов.
- `CONTEXT_HANDOFF.md` хранит текущее состояние работ: где мы, что дальше, что читать первым и какие риски открыты.
- При добавлении нового модуля или изменении его назначения/интерфейса обновлять `MODULE_INDEX.md`.
- Для закрытия этапа и синхронизации `report` / `CHANGELOG.md` / `CONTEXT_HANDOFF.md` использовать [`.codex/skills/stage-reporting/SKILL.md`](.codex/skills/stage-reporting/SKILL.md).

### Память проекта

| Слой | Назначение | Точка входа |
|------|-----------|-------------|
| `wiki/` | Синтез знаний: эволюция исследований, ключевые концепты | [`wiki/index.md`](wiki/index.md) |
| `CONTEXT_HANDOFF.md` | Текущее состояние: где мы, что дальше, открытые риски | [`CONTEXT_HANDOFF.md`](CONTEXT_HANDOFF.md) |
| `.claude/memory/` | Стабильные правила, предпочтения, долгоживущие инварианты | [`.claude/memory/MEMORY.md`](.claude/memory/MEMORY.md) |

**В начале каждой сессии читать**: `wiki/index.md` → релевантные страницы `wiki/research/` и `wiki/concepts/` → `CONTEXT_HANDOFF.md`.
Для операций с вики (ingest, save, lint) — см. `.codex/skills/wiki/SKILL.md`.

### Приоритет источников
1. Явный запрос пользователя в текущем диалоге.
2. Актуальные документы проекта: `AGENTS.md`, `README.md`, `docs/` (кроме `docs/archive/`).
3. Рабочие планы и исследовательские материалы: `docs/superpowers/roadmap.md`, `docs/superpowers/plans/`, `docs/superpowers/specs/`.
4. Синтезированные знания: `wiki/`.
5. Вспомогательная память: `.claude/memory/`.

## Структура проекта

Легенда статусов:
`✅` активный, `🚧` в разработке, `🏁` завершен, `📦` архив, `⚠️` требует внимания.

```
.
├── .claude/memory/      # Долговечная память проекта
├── .codex/skills/       # Локальные workflow/skills для Codex
├── wiki/                # LLM Wiki: синтез знаний проекта
│   ├── REPO_integrity.md #   авто-генерированная integrity map репо
│   ├── index.md         #   LLM-каталог wiki-страниц
│   ├── log.md           #   хронология операций
│   ├── wiki.py          #   generate / verify
│   ├── concepts/        #   синтез: сигналы, фильтры, политики (пусто → ingest)
│   └── research/        #   синтез отчётов из docs/reports/ (пусто → ingest)
├── API/                 # ✅ Генерация ML-сигналов для MT4
├── MT/MQL4/             # ✅ MetaTrader4 — формирование датасета, торговый робот
│   ├── Experts/         #    MQL4 советники
│   ├── Files/           #    Данные (Nero.csv, ml_signals.csv)
│   └── Include/         #    MQL4 библиотеки (.mqh)
├── processing/          # 🏁 Препроцессинг: sort → label → normalize → split
├── statistics/          # ✅/🏁 Статистика, EDA, signal_tracer
├── ML/                  # ✅ Machine Learning — 18 скриптов по слоям
│   ├── models/          # ✅ Transformer (лучший), BiLSTM, CNN1D, Hybrid
│   ├── baseline/        # 🏁 Baseline-модели (5 алгоритмов)
│   ├── conformal/       # 🏁 Conformal Prediction
│   ├── checkpoints/     #    Веса моделей (.pt)
│   ├── reports/         #    Отчёты экспериментов (.md, .json)
│   └── plots/           #    Графики обучения
├── tests/               # ✅ Unit/smoke-тесты: processing, API, statistics
├── DATA/                #    Обработанные данные
├── docs/                # Документация (каталоги = каталоги кода)
│   ├── DATA_FLOW.md     #    Поток данных + навигация по этапам
│   ├── PRD.md           #    Product Requirements
│   ├── reports/         #    Канонические отчёты этапов
│   ├── statistics/      #    Docs для statistics/
│   ├── processing/      #    Docs для processing/
│   ├── ML/              #    Docs для ML/
│   ├── MT/              #    Работа с тестером MT4 и ключевые библиотеки для взаимодействия с ML
│   ├── superpowers/     #    Канонический контур roadmap / plans / specs
│   └── archive/         # 📦 НЕ СМОТРИ без явной просьбы
├── AGENTS.md            # ← ВЫ ЗДЕСЬ. Главный индекс
├── MODULE_INDEX.md      # Реестр всех модулей со статусами
├── CHANGELOG.md         # История значимых изменений
├── CONTEXT_HANDOFF.md   # Текущий baton pass: где мы, что дальше, что читать
└── README.md            # Точка входа

```

## Навигация (быстрые точки входа):
- [MODULE_INDEX.md](MODULE_INDEX.md)
- [docs/DATA_FLOW.md](docs/DATA_FLOW.md)
- [CONTEXT_HANDOFF.md](CONTEXT_HANDOFF.md)
- [CHANGELOG.md](CHANGELOG.md) — последние значимые изменения (читать первые 300 строк)

## Статус разработки
| Компонент | Статус | Примечание |
|-----------|--------|------------|
| Сбор данных (MT4) | 🏁 | `lib_PIC.mqh`, `NERO_CSV_CREATE()` |
| Препроцессинг | 🏁 | `label_main.py`, `normalize.py` |
| Статистика/EDA | 🏁 | `statistics.py`, `EDA.ipynb` |
| ML модели | ✅ | Transformer (лучший), regression_updn |
| Triple Barrier | 🚧 | 12 бинарных таргетов, `iSignal=5` |
| Генерация сигналов | ✅ | [API/generate_signals.py](API/generate_signals.py) |
| Интеграция с MT4 | ✅ | `ML_TRADE()` + `ML_TRADE_TB()` |
| Reconciliation | ✅ | `signal_tracer.py` |



---

Последнее обновление: 2026-04-02
Авторы: human + AI agents
