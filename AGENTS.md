# AI Agent Guide
> **Главный индекс проекта SoSimple для ИИ-агентов и разработчиков*

---

## 🎯 Цель проекта

Торговый бот на базе ML для прогнозирования разворотов тренда на Forex (H1 таймфрейм). 

**Подробнее**: [PRD.md](docs/PRD.md)

---

## 🚀 Быстрый старт

Команды и пути: [QUICK_REFERENCE.md](QUICK_REFERENCE.md)

### Основные команды
```bash
# Полный конвейер обработки данных
python processing/label_main.py --input MT/MQL4/Files/Nero.csv --debug


```

---

## 📊 Pipeline данных

Полное описание потока данных: [DATA_FLOW.md](docs/DATA_FLOW.md)

### Краткая схема
```
MT4 → Nero.csv → Сортировка → Маркировка → Нормализация → Split → ATR → train/val/test
```

### Критические правила
- Нормализация **до split** (построчная, нет data leakage)
- ATR fit **только на train** (RobustScaler)
- Split **последовательный** (не shuffle, time series!)

---

## 📂 Структура проекта

```
.
├── MT/MQL4/                 # MetaTrader 4 код
│   └── Include/
│       └── lib_PIC.mqh      # Алгоритм PIC для формирования фракталов
│
├── processing/              # Препроцессинг данных
│   ├── label_main.py        # CLI оркестратор (полный конвейер)
│   ├── label_signals.py     # Маркировка signal/predict
│   └── normalize.py         # Нормализация (построчная + ATR)
│
├── statistics/              # Статистика и EDA
│   ├── statistics.py        # Потоковая статистика (Welford, Reservoir Sampling)
│   ├── EDA.ipynb            # Exploratory Data Analysis
│   └── Nero.csv             # Входные данные для анализа
│
├── ML/                      # Machine Learning (в разработке)
│   └── (будущие модули)
│
├── .ai/                     # Правила и команды для ИИ
│   ├── rules/               # Правила работы с кодом
│   ├── RULES_INDEX.md       # Индекс правил
│   └── SKILLS_INDEX.md      # Автоматизированные команды
│
├── docs/                    # Дополнительная документация
│   ├── dataset_description.md  # Структура Nero.csv
│   └── PRD.md               # Product Requirements Document
│
├── AGENTS.md                # ← Этот файл (главный индекс)
├── README.md                # Краткое описание проекта
└── CHANGELOG.md             # История изменений
```

---

## 🔧 Модули

Детальные описания модулей: [MODULE_INDEX.md](MODULE_INDEX.md)

### Краткий список
- `processing/label_main.py` — CLI для полного конвейера ✅
- `processing/label_signals.py` — Маркировка signal/predict ✅
- `processing/normalize.py` — Нормализация признаков ✅
- `statistics/statistics.py` — Потоковая статистика ✅
- `statistics/EDA.ipynb` — Exploratory Data Analysis ✅
- `MT/MQL4/Include/lib_PIC.mqh` — Алгоритм PIC (legacy) ⚠️

---

## ⚙️ Правила работы

### Критические правила

⚠️ **Всегда читай перед началом**:

1. **[000-documentation.md](.ai/rules/000-documentation.md)**
   - File headers обязательны (формат: назначение, вход, выход, использование)
   - Обновляй при изменении логики

2. **[007-no-csv-context.md](.ai/rules/007-no-csv-context.md)**
   - Запрет загрузки больших CSV в контекст (>100MB)
   - Используй chunking, sampling, статистики

3. **[100-file-handling.md](.ai/rules/100-file-handling.md)**
   - UTF-8 кодировка для всех текстовых файлов
   - CSV separator: `;` для Nero.csv
   - Обрабатывай BOM корректно

**Все правила**: [.ai/RULES_INDEX.md](.ai/RULES_INDEX.md)

### Data Leakage Prevention

✅ **Применённые меры**:
1. Сортировка независима по строкам
2. Построчная нормализация (каждая строка независимо)
3. ATR fit только на train (val/test используют тот же scaler)
4. Split последовательный (не shuffle, time series!)
5. Маркировка до split (маркируем весь датасет, затем делим)

---

## 🛠️ Технологический стек

- **Языки**: Python 3.11+, MQL4
- **Обработка данных**: Pandas, NumPy
- **Статистика**: Scipy, Scikit-learn
- **Визуализация**: Matplotlib, Seaborn
- **ML** (планируется): PyTorch  
- **Инфраструктура** (планируется): Docker

---

## 📋 Workflow для агента

### При изменении кода
1. Обнови file header (если изменились входы/выходы/назначение)
2. Проверь, не нарушены ли правила из `.ai/rules/`
3. Обнови CHANGELOG.md (если major изменение)

### При создании нового модуля
1. Создай file header по шаблону из [000-documentation.md](.ai/rules/000-documentation.md)
2. Добавь запись в этот файл (AGENTS.md) в секцию "Модули"
3. Обнови секцию "Структура проекта" если нужно

### При изучении проекта
1. Прочитай этот файл (AGENTS.md) — главный индекс
2. Изучи [PRD.md](docs/PRD.md) — цели и критерии успеха
3. Просмотри [.ai/RULES_INDEX.md](.ai/RULES_INDEX.md) — правила работы
4. Открой file headers в модулях — детали реализации

---

## 📚 Дополнительные ресурсы

- **[docs/dataset_description.md](docs/dataset_description.md)** — детальное описание структуры Nero.csv
- **[PRD.md](docs/PRD.md)** — Product Requirements Document (цели, критерии успеха)
- **[CHANGELOG.md](CHANGELOG.md)** — история major изменений проекта
- **[.ai/SKILLS_INDEX.md](.ai/SKILLS_INDEX.md)** — автоматизированные команды (если есть)

---

## 🚧 Статус разработки

| Компонент | Статус | Примечание |
|-----------|--------|------------|
| Сбор данных (MT4) | ✅ Готов | lib_PIC.mqh (legacy) |
| Препроцессинг | ✅ Готов | label_main.py, normalize.py |
| Статистика/EDA | ✅ Готов | statistics.py, EDA.ipynb |
| ML модели | 🚧 В разработке | Архитектура в процессе выбора |
| Интеграция с MT4 | 📅 Планируется | DLL/REST API |
| Production deployment | 📅 Планируется | Docker, мониторинг |

---

**Последнее обновление**: 2026-02-13  
**Авторы**: Antigravity (human) + Claude (AI)
