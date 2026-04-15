# AI Agent Guide (Codex First)
> Главный индекс SoSimple для Codex.

## Цель проекта
ML-бот для прогнозирования разворотов Forex (H1). Детали: [PRD.md](docs/PRD.md).

## using search_knowledge (RAG system)
`knowledge-rag` — retrieval layer для быстрого поиска по проекту. Он помогает найти кандидаты, но не заменяет canonical files и wiki-синтез: после RAG-результата открывай найденный файл и проверяй контекст.

- Exact names / paths / metrics: `search_knowledge("entry_path_v1_quantile", hybrid_alpha=0.0)`
- Technical search: `search_knowledge("triple barrier label convention", hybrid_alpha=0.3)`
- Conceptual search: `search_knowledge("why quantile execution filter works", hybrid_alpha=0.7)`

Индексация: `reindex_documents()` — только изменённые файлы; `reindex_documents(force=True)` — smart rebuild BM25.


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
- Перед обращением к содержимому каталог сначала читать локальный `README.md` этого каталога.
- Предпочитать точечное чтение: `rg`, `head`, `sed`, а не полный вывод больших файлов.
- Не трогать `docs/archive/` и архивные модули без явной просьбы.
- Всегда создавай новую feature-ветку для каждой задачи.
- `git push` не делать без явной просьбы пользователя.
- Для bugfix не делать рефакторинг "заодно".
- Для закрытия этапа и синхронизации `report` / `CHANGELOG.md` / `CONTEXT_HANDOFF.md` использовать [`.codex/skills/stage-reporting/SKILL.md`](.codex/skills/stage-reporting/SKILL.md).


### Память проекта

| Слой | Назначение | Точка входа |
|------|-----------|-------------|
| `wiki/` | Синтез знаний: эволюция исследований, ключевые концепты | [`wiki/index.md`](wiki/index.md) |
| `knowledge-rag` | Поиск кандидатов по docs/wiki/code; не source of truth | MCP server `knowledge-rag`, tool `search_knowledge` |
| `CONTEXT_HANDOFF.md` | Текущее состояние: где мы, что дальше, открытые риски | [`CONTEXT_HANDOFF.md`](CONTEXT_HANDOFF.md) |
| `docs/reports/` | Канонические отчёты завершённых этапов с результатами и выводами | [`docs/reports/`](docs/reports/) |
| `CHANGELOG.md` | История значимых изменений: фичи, багфиксы, результаты экспериментов | [`CHANGELOG.md`](CHANGELOG.md) — первые 300 строк |
| `MODULE_INDEX.md` | Реестр всех модулей со статусами, назначением и точками входа | [`MODULE_INDEX.md`](MODULE_INDEX.md) |
| `docs/DATA_FLOW.md` | Схема потока данных MT4→ML→MT4 и навигация по этапам pipeline | [`docs/DATA_FLOW.md`](docs/DATA_FLOW.md) |
| `.claude/memory/` | Стабильные правила, предпочтения, долгоживущие инварианты | [`.claude/memory/MEMORY.md`](.claude/memory/MEMORY.md) |

**В начале каждой сессии читать**: `wiki/index.md` → `CONTEXT_HANDOFF.md` → через `search_knowledge` найти релевантные `wiki/`, `docs/`, `docs/reports/`, код → открыть первоисточники.
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
