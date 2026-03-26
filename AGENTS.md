# AI Agent Guide
> **Главный индекс проекта SoSimple для ИИ-агентов и разработчиков**

---

## 🎯 Цель проекта
ML-бот для прогнозирования разворотов Forex (H1). Подробнее: [PRD.md](docs/PRD.md)

---

## 🚀 Быстрый старт

### Команды
| Этап | Команды |
|------|---------|
| Препроцессинг данных | [DATA_FLOW.md#⚙️-этап-1-сортировка-фракталов](docs/DATA_FLOW.md#-этап-1-сортировка-фракталов) |
| Обучение ML моделей | [DATA_FLOW.md#🚧-этап-6-ml-training-regression_updn](docs/DATA_FLOW.md#-этап-6-ml-training-regression_updn) |
| Генерация сигналов | [DATA_FLOW.md#🔄-этап-8-генерация-ml-сигналов-для-mt4](docs/DATA_FLOW.md#-этап-8-генерация-ml-сигналов-для-mt4) |
| Triple Barrier | [DATA_FLOW.md#🎯-этап-8b-triple-barrier-training-signals-параллельный-трек](docs/DATA_FLOW.md#-этап-8b-triple-barrier-training-signals-параллельный-трек) |

### Пути к данным
- **Вход**: `MT/MQL4/Files/Nero.csv` (UTF-16LE, `;`)
- **Выход**: `DATA/Nero_{train|validation|test}_labeled.csv`
- **Мета**: `DATA/Nero_normalization_stats.csv`

### Critical Rules Top-3
1. Читай только первые 10 строк в файлах CSV, т.к. их размер >10MB
2. Не грузи файлы >2MB целиком в чат.
3. Файлы *.mqh, *.mq4 из `MT/` открывать ТОЛЬКО если в основном файле, или в уже открытых файлах на них есть явная директива #include <*.mqh>.

---

## 📊 Pipeline данных
Схема: `MT4 → Raw → Sort → Label → Norm → Split → Train → Signals → MT4` ([Детали в DATA_FLOW.md](docs/DATA_FLOW.md))

---

## 📂 Структура проекта

**Легенда статусов** (единая для всех документов)
✅ Активный — читай, можешь менять
🚧 В разработке
🏁 Завершён — стабилен, не меняй без причины
📦 Архив — смотри только если явно попросили
⚠️ Требует внимания

```
.
├── API/                 # ✅ Генерация ML-сигналов для MT4 (README.md внутри)
├── MT/MQL4/             # ✅ MetaTrader4 — формирование датасета, торговый робот
│   ├── Experts/         #    MQL4 советники
│   ├── Files/           #    Данные (Nero.csv, ml_signals.csv)
│   └── Include/         #    MQL4 библиотеки (.mqh)
├── processing/          # 🏁 Препроцессинг: sort → label → normalize → split (README.md внутри)
├── statistics/          # ✅/🏁 Статистика, EDA, signal_tracer (README.md внутри)
├── ML/                  # ✅ Machine Learning — 18 скриптов по слоям (README.md внутри)
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
│   ├── plans/           #    Планы работы
│   └── archive/         # 📦 НЕ СМОТРИ без явной просьбы
├── AGENTS.md            # ← ВЫ ЗДЕСЬ. Главный индекс
├── MODULE_INDEX.md      # Детальный реестр всех модулей со статусами
├── CHANGELOG.md         # История изменений
└── README.md            # Точка входа
```

> **Навигация**: Каждый каталог с кодом содержит README.md с описанием файлов, командами и статусами. Детали по модулям: [MODULE_INDEX.md](MODULE_INDEX.md). Этапы pipeline: [DATA_FLOW.md](docs/DATA_FLOW.md).

---

### Data Leakage Prevention
Детали: [DATA_FLOW.md § Data Leakage Prevention](docs/DATA_FLOW.md#-data-leakage-prevention)

---

## 🛠️ Технологический стек
- **Языки**: Python 3.11+, MQL4; **Библиотеки**: Pandas, NumPy, Scikit-learn, Scipy
- **Визуализация**: Matplotlib, Seaborn; **ML**: PyTorch, XGBoost, LightGBM, Optuna

---

## 📋 Workflow для агента

### Паттерны разработки
- **Новая фича**: `/brainstorming` → `/writing-plans` → `/test-driven-development` → `/requesting-code-review`
- **Bugfix**: `/systematic-debugging` → diagnose → fix → `/verification-before-completion`
- **Завершение**: `/finishing-a-development-branch` → merge/PR → update CHANGELOG.md
- **Новый модуль**: создай header → docs → добавь в MODULE_INDEX.md → обнови AGENTS.md

### Когда использовать skills

| Skill | Когда |
|-------|-------|
| `/brainstorming` | Перед любым feature/refactor |
| `/writing-plans` | Для многошаговых задач — план перед кодом |
| `/test-driven-development` | Перед реализацией фичи |
| `/systematic-debugging` | При ошибке или падении теста |
| `/verification-before-completion` | Перед commit/PR |
| `/requesting-code-review` | При завершении большой работы |
| `/executing-plans` | Если есть письменный план |

**Документация (.kilocode/skills — вызов текстом):**

| Команда | Когда |
|---------|-------|
| `обнови документацию` | После правки кода |
| `doc this путь/к/файлу.py` | Добавить docs для существующего файла |
| `create module имя` | Создать новый модуль с docs |
| `rebuild module index` | Обновить MODULE_INDEX.md |

### Git workflow
- ❌ Не делай `git commit` и `git push` без явной просьбы пользователя

### CHANGELOG.md
Добавляй запись **только** при: новых фичах, breaking changes, багфиксах, результатах экспериментов с выводами.
**НЕ добавляй** при: правках документации, рефакторинге без изменения поведения, обновлении путей.
Формат: `## [YYYY-MM-DD] — Краткое описание`
Секции: `### Добавлено`, `### Изменено`, `### Исправлено`, `### Результаты`, `### Вывод`

### Что НЕ делать
- ❌ Не добавляй docstrings/comments если их не было в исходном коде
- ❌ Не рефакторься "заодно" (bug fix = только fix, не cleanup)
- ❌ Не добавляй error handling для невозможных сценариев
- ❌ Не создавай helper-функции для one-time операций
- ❌ Не over-engineer: три строки кода лучше, чем абстракция
- ❌ Не добавляй подробности в AGENTS.md — детали идут в README.md каталога или docs/, здесь только короткая ссылка

### Память проекта
- `.claude/memory/MEMORY.md` — индекс памяти (синхронизируется через git)
- Читай перед началом работы, обновляй при появлении новых паттернов

---

## 📚 Доп. ресурсы
- [docs/dataset_description.md](docs/dataset_description.md) — структура данных.
- [CHANGELOG.md](CHANGELOG.md) — история изменений.

---

## 🚧 Статус разработки
| Компонент | Статус | Примечание |
|-----------|--------|------------|
| Сбор данных (MT4) | 🏁 | lib_PIC.mqh, NERO_CSV_CREATE() — 18 полей на фрактал |
| Препроцессинг | 🏁 | label_main.py, normalize.py (Piecewise Linear-Log) |
| Статистика/EDA | 🏁 | statistics.py, EDA.ipynb |
| ML модели | ✅ | Transformer (лучший); regression_updn (6 таргетов) |
| Triple Barrier | 🚧 | 12 бинарных таргетов, BCEWithLogitsLoss, iSignal=5 |
| Генерация сигналов | ✅ | [generate_signals.py](API/generate_signals.py) → ml_signals.csv / ml_signals_tb.csv |
| Интеграция с MT4 | ✅ | ML_TRADE() (iSignal=3) + ML_TRADE_TB() (iSignal=5) |
| Торговый робот | ✅ | OOS PF=4.50 (θ=2.665, 12H). Тестер: PF=0.85 ([trading_strategy](docs/MT/trading_strategy.md)) |
| Conformal Prediction | 🏁 | При θ=2.665 эффект нейтральный ([docs](docs/ML/conformal_prediction.md)) |
| Reconciliation | ✅ | signal_tracer.py — диагностика Python PF vs MT4 PF |

---

**Последнее обновление**: 2026-03-26 (рефакторинг структуры проекта)
**Авторы**: Antigravity (human) + Claude (AI)

