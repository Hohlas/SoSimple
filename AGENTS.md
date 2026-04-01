# AI Agent Guide (Codex First)
> Главный индекс SoSimple для Codex. Инструкции для Claude Code вынесены в [CLAUDE.md](CLAUDE.md).

## Цель проекта
ML-бот для прогнозирования разворотов Forex (H1). Детали: [PRD.md](docs/PRD.md).

## Быстрый старт

### Базовые команды
```bash
# 1) Активировать окружение
source ~/git/SoSimple/.venv/bin/activate

# 2) Подготовить датасет (sort -> label -> normalize -> split)
python processing/label_main.py --input MT/MQL4/Files/Nero.csv --debug

# 3) Обучить модель regression_updn (пример)
python -m ML.train --model transformer --task regression_updn

# 4) Сгенерировать сигналы для MT4
python -m API.generate_signals --theta 2.665 --horizon 12

# 5) Диагностика расхождения Python vs MT4
python statistics/signal_tracer.py --batch --top 10 --min-ratio 5.0 --csv-out batch.csv
```

### Пути к данным
- Вход: `MT/MQL4/Files/Nero.csv` (UTF-16LE, `;`)
- Выход: `DATA/Nero_{train|validation|test}_labeled.csv`
- Мета: `DATA/Nero_normalization_stats.csv`

### Critical Rules Top-3
1. Для CSV сначала читать только первые 10 строк.
2. Не загружать в контекст файлы больше 2MB целиком.
3. Файлы `*.mqh`, `*.mq4` из `MT/` открывать только если есть явная `#include`-связь с текущим файлом.

## Pipeline данных
Схема: `MT4 -> Raw -> Sort -> Label -> Norm -> Split -> Train -> Signals -> MT4`.
Детали: [docs/DATA_FLOW.md](docs/DATA_FLOW.md)

## Как работать в этом репозитории (Codex)

### Обязательные правила
- Перед правками в каталоге сначала читать локальный `README.md` этого каталога.
- Предпочитать точечное чтение: `rg`, `head`, `sed`, а не полный вывод больших файлов.
- Не трогать `docs/archive/` и архивные модули без явной просьбы.
- Не делать `git commit` и `git push` без явной просьбы пользователя.
- Для bugfix не делать рефакторинг "заодно".

### Качество изменений
- Изменения должны быть минимальными и по задаче.
- Не добавлять docstrings/comments, если их не было и это не требуется для понимания сложного кода.
- Если у `*.py` файла есть header/docstring с описанием назначения, входов/выходов или секций отчёта, обновлять его вместе с функционалом файла.
- Не добавлять обработку невозможных сценариев.
- Не создавать helper-функции для одноразовой логики.

### Документация и CHANGELOG
- `CHANGELOG.md` обновлять только при: новых фичах, breaking changes, багфиксах, результатах экспериментов с выводами.
- Не добавлять запись в `CHANGELOG.md` для: правок документации, обновления путей, рефакторинга без изменения поведения.
- Формат записи: `## [YYYY-MM-DD] - Краткое описание`
- Секции: `### Добавлено`, `### Изменено`, `### Исправлено`, `### Результаты`, `### Вывод`

### Память проекта
- `.claude/memory/` использовать для поддержания актуального контекста.
- Источником актуальных требований считать текущую задачу пользователя и профильные docs в `docs/`.

### Приоритет источников
1. Явный запрос пользователя в текущем диалоге.
2. Актуальные документы проекта: `AGENTS.md`, `README.md`, `docs/` (кроме `docs/archive/`).
3. Рабочие планы и исследовательские материалы: `docs/plans/`, `docs/superpowers/`, `docs/specs/`.
4. Вспомогательная память и архив: `.claude/memory/`, `docs/archive/`.

## Структура проекта

Легенда статусов:
`✅` активный, `🚧` в разработке, `🏁` завершен, `📦` архив, `⚠️` требует внимания.

```
.
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
├── DATA/                #    Обработанные данные
├── docs/                # Документация (каталоги = каталоги кода)
│   ├── DATA_FLOW.md     #    Поток данных + навигация по этапам
│   ├── PRD.md           #    Product Requirements
│   ├── statistics/      #    Docs для statistics/
│   ├── processing/      #    Docs для processing/
│   ├── ML/              #    Docs для ML/
│   ├── MT/              #    Docs для MT/
│   ├── plans/           #    Планы работы (исследовательские/временные)
│   ├── superpowers/     #    Планы и спецификации superpowers (исследовательские/временные)
│   └── archive/         # 📦 НЕ СМОТРИ без явной просьбы
├── AGENTS.md            # ← ВЫ ЗДЕСЬ. Главный индекс
├── MODULE_INDEX.md      # Реестр всех модулей со статусами
├── CHANGELOG.md         # История значимых изменений
└── README.md            # Точка входа

```

Навигация:
- [MODULE_INDEX.md](MODULE_INDEX.md)
- [docs/DATA_FLOW.md](docs/DATA_FLOW.md)
- [docs/dataset_description.md](docs/dataset_description.md)

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

Последнее обновление: 2026-04-01
Авторы: human + AI agents
