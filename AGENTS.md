# AI Agent Guide (Codex First)
> Главный индекс SoSimple для Codex.

## Цель проекта
ML-бот для прогнозирования разворотов Forex (H1). Детали: [PRD.md](docs/PRD.md).

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
- Отвечай простым, ясным, деловым языком.
- Объясняй смысл через цель, причину, последствия и решение.
- Избегай жаргона, англицизмов и узких терминов, но не теряй точность. - Если термин необходим, кратко объясняй его в скобках при первом использовании.

## using search_knowledge (RAG system)
`knowledge-rag` — retrieval layer для быстрого поиска по проекту. Он помогает найти кандидаты, но не заменяет canonical files и wiki-синтез: после RAG-результата открывай найденный файл и проверяй контекст.

- Pure keyword search — exact names / paths / metrics: `search_knowledge("gtfobins suid", hybrid_alpha=0.0)`
- Balanced hybrid — both engines equally weighted: `search_knowledge("SQL injection techniques", hybrid_alpha=0.5)`
- Pure semantic — embedding similarity only: `search_knowledge("lateral movement strategies", hybrid_alpha=1.0)`

После значимых изменений кода/доков, влияющих на поиск: `reindex_documents(force=True)`.



## Обязательные правила
- Для чтения CSV файлов используй скилл .codex/skills/csv-processing/SKILL.md
- При добавлении нового файла добавить его в индекс: использовать Mode 4 скилла [`.codex/skills/update-docs-on-code-change/SKILL.md`](.codex/skills/update-docs-on-code-change/SKILL.md)
- Рутинная синхронизация после каждого изменения кода [`.codex/skills/update-docs-on-code-change/SKILL.md`](.codex/skills/update-docs-on-code-change/SKILL.md).
- Не загружать в контекст файлы больше 1MB целиком.
- Файлы `*.mqh`, `*.mq4` из `MT/` открывать только если есть явная `#include`-связь с текущим файлом.
- Перед обращением к содержимому каталог сначала читать локальный `README.md` этого каталога.
- Предпочитать точечное чтение: `rg`, `head`, `sed`, а не полный вывод больших файлов.
- Не трогать `docs/archive/` и архивные модули без явной просьбы.
- `MODULE_INDEX.md` читать точечно через `rg`/`sed`; целиком открывать только при пересборке индекса или аудите всей структуры.
- Всегда создавай новую feature-ветку для каждой задачи.
- Не используй worktree.
- Используй окружение: ~/git/SoSimple/.venv/bin/activate
- `git push` не делать без явной просьбы пользователя.
- Для bugfix не делать рефакторинг "заодно".
- При закрытии этапа финальная синхронизация `report` / `CHANGELOG.md` / `CONTEXT_HANDOFF.md` использовать [`.codex/skills/stage-reporting/SKILL.md`](.codex/skills/stage-reporting/SKILL.md).
- После закрытия этапа выполнить wiki **Ingest**: синтезировать новые отчёты из `docs/reports/` в страницы `wiki/research/` (см. [`.codex/skills/wiki/SKILL.md`](.codex/skills/wiki/SKILL.md)).


## Память проекта

| Слой | Назначение | Точка входа |
|------|-----------|-------------|
| `wiki/index.md` | Каталог синтезированных wiki-страниц: research + concepts. Не дублирует MODULE_INDEX, DATA_FLOW, CONTEXT_HANDOFF | [`wiki/index.md`](wiki/index.md) |
| `wiki/REPO_integrity.md` | Карта всех файлов репо с хешами — для обнаружения изменений. Не для навигации по коду | `python wiki/wiki.py generate` |
| `knowledge-rag` | Поиск кандидатов по docs/wiki/code; не source of truth | MCP server `knowledge-rag`, tool `search_knowledge` |
| `CONTEXT_HANDOFF.md` | Текущее состояние: где мы, что дальше, открытые риски | [`CONTEXT_HANDOFF.md`](CONTEXT_HANDOFF.md) |
| `docs/reports/` | Канонические отчёты завершённых этапов с результатами и выводами | [`docs/reports/`](docs/reports/) |
| `CHANGELOG.md` | История значимых изменений: фичи, багфиксы, результаты экспериментов | [`CHANGELOG.md`](CHANGELOG.md) — первые 300 строк |
| `MODULE_INDEX.md` | Реестр всех модулей со статусами, назначением и точками входа | [`MODULE_INDEX.md`](MODULE_INDEX.md) |
| `docs/DATA_FLOW.md` | Схема потока данных MT4→ML→MT4 и навигация по этапам pipeline | [`docs/DATA_FLOW.md`](docs/DATA_FLOW.md) |
| `docs/README.md` | Карта артефактов внутри `docs/` и правила их обновления | [`docs/README.md`](docs/README.md) |
| `.claude/memory/` | Стабильные правила, предпочтения, долгоживущие инварианты | [`.claude/memory/MEMORY.md`](.claude/memory/MEMORY.md) |

**В начале каждой сессии** (wiki Query-workflow, см. [`.codex/skills/wiki/SKILL.md`](.codex/skills/wiki/SKILL.md)):
1. Прочитай `wiki/index.md` — понять существующий синтез.
2. Прочитай `CONTEXT_HANDOFF.md` — текущее состояние и следующий шаг.
3. Через `search_knowledge` найти релевантные `wiki/`, `docs/`, `docs/reports/`, код → открыть первоисточники.
4. Если новые отчёты из `docs/reports/` не покрыты в `wiki/index.md` → выполнить wiki **Ingest**.

## Приоритет источников
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
│   ├── README.md        #    Карта артефактов docs/ + правила обновления
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
├── CHANGELOG.md         # Краткая история значимых изменений
├── CONTEXT_HANDOFF.md   # Короткий baton pass: где мы, что дальше, что читать
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


## Мониторинг ошибок

Если во время выполнения задачи обнаружена ошибка, кратко сообщи о ней в конце ответа.

Типы ошибок:
- MCP — 'ошибка' / 'нет ответа' / 'пустой результат'
- DOC — битая ссылка или отсутствующий файл
- STRUCT — ссылка на несуществующий модуль/путь

Правила мониторинга:
- Не искать ошибки специально
- Не останавливать выполнение задачи 

---

Последнее обновление: 2026-04-27
Авторы: human + AI agents
