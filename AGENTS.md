# AI Agent Guide
> **Главный индекс проекта SoSimple для ИИ-агентов и разработчиков**

---

## 🎯 Цель проекта

Торговый бот на базе ML для прогнозирования разворотов тренда на Forex (H1 таймфрейм). 

**Подробнее**: [PRD.md](PRD.md)

---

## 🚀 Быстрый старт

### Обработка данных
```bash
# Полный конвейер: сортировка → маркировка → нормализация → split
python processing/label_main.py --input MT/MQL4/Files/Nero.csv --debug

# Выход:
# - Nero_train_labeled.csv
# - Nero_validation_labeled.csv
# - Nero_test_labeled.csv
# - Nero_atr_scaler.pkl
# - Nero_normalization_stats.csv
```

### Статистика и EDA
```bash
# Потоковая статистика (не загружает весь CSV в память)
cd statistics
python statistics.py

# EDA (Jupyter)
jupyter notebook EDA.ipynb
```

---

## 📊 Pipeline данных

```
MT4 (lib_PIC.mqh)
    ↓
Nero.csv (raw: time, signal, predict, ATR, fractal0...fractal99)
    ↓
processing/label_main.py:
    1. Сортировка фракталов (по time, descending)
    2. Маркировка signal/predict (поиск ближайшего strong=1)
    3. Построчная нормализация (piecewise linear-log)
    4. Split 70/15/15 (train/val/test)
    5. ATR нормализация (RobustScaler: fit на train, transform на val/test)
    ↓
Nero_train_labeled.csv
Nero_validation_labeled.csv
Nero_test_labeled.csv
Nero_atr_scaler.pkl
Nero_normalization_stats.csv
    ↓
statistics/ (анализ)
    ↓
ML/ (обучение, в разработке)
```

**Важно**:
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

## 🔧 Модули (детально)

### processing/label_main.py ✅
**Назначение**: CLI для полного конвейера подготовки данных

**Конвейер**:
1. Сортировка фракталов (`sort_fractals_in_dataframe`)
2. Маркировка (`label_all` из label_signals.py)
3. Построчная нормализация (`normalize_rowwise`)
4. Split 70/15/15 (`split_train_val_test`)
5. ATR нормализация (`normalize_atr_train`, `normalize_atr_inference`)

**Использование**:
```bash
python label_main.py --input MT/MQL4/Files/Nero.csv [--debug]
```

**Вход**: `Nero.csv` (raw)

**Выход**:
- `Nero_train_labeled.csv` (70%)
- `Nero_validation_labeled.csv` (15%)
- `Nero_test_labeled.csv` (15%)
- `Nero_atr_scaler.pkl` (RobustScaler для инференса)
- `Nero_normalization_stats.csv` (статистика до нормализации)

---

### processing/label_signals.py ✅
**Назначение**: Маркировка сигналов (signal + predict)

**Логика**:
1. Поиск ближайшего фрактала с `strong=1` (целевой фрактал)
2. Расчёт `signal`:
   - `0` — цель не найдена
   - `+1` — цель выше текущей цены
   - `-1` — цель ниже текущей цены
3. Расчёт `predict = front × target_direction`

**Ключевая функция**: `label_all(input_path, output_path, debug=False)`

**Формат фрактала**: `time:price:direction:front:back:strong:break:reverse:power:count:impulse`

---

### processing/normalize.py ✅
**Назначение**: Нормализация признаков

**Методы**:

#### 1. Построчная нормализация (`normalize_rowwise`)
**Применяется**: До split (каждая строка независимо)

**Группа A** (Piecewise Linear-Log, совместная):
- `|predict|`, `front`, `back`
- Логика: объединяем → вычисляем lo/brk(85%)/cap(99%) → piecewise transform → возвращаем знак predict

**Группа B** (Piecewise Linear-Log, раздельная):
- `impulse`, `count`, `reverse`, `power`, `break`
- Логика: отдельные параметры для каждого

**Группа C** (Min-Max):
- `price` → нормализация в [0, 1]

**Группа D** (Без нормализации):
- `direction`, `strong`, `fractal_time`

#### 2. ATR нормализация
**Train**: `normalize_atr_train(df, scaler_path)`
- RobustScaler.fit(train['ATR'])
- RobustScaler.transform(train['ATR'])
- Сохраняет scaler в `.pkl`

**Val/Test**: `normalize_atr_inference(df, scaler_path)`
- Загружает scaler из `.pkl`
- RobustScaler.transform(df['ATR'])

**Важно**: Fit только на train — нет data leakage!

---

### statistics/statistics.py ✅
**Назначение**: Потоковая обработка Nero.csv с онлайн-расчётом статистики

**Алгоритмы**:
- **Метод Уэлфорда** (Welford's algorithm) — онлайн-расчёт mean/variance без хранения всех значений
- **Reservoir Sampling** — несмещённая выборка для квантилей

**Использование**:
```bash
cd statistics
python statistics.py
```

**Вход**: `statistics/Nero.csv`

**Выход**:
- `statistics_summary.json` — сводная статистика по всем признакам (mean, std, min, max, квантили)
- `class_balance_report.csv` — баланс классов signal {-1, 0, 1}
- `feature_distributions.csv` — распределения признаков фракталов + predict/ATR
- `nero_sample_stratified.csv` — стратифицированная выборка (100% редких + 10% нормальных)
- `class_statistics.json` — статистика по классам для первого фрактала

**Класс**: `StreamingStats` — накопление онлайн-статистики без загрузки всех данных в память

---

### statistics/EDA.ipynb ✅
**Назначение**: Exploratory Data Analysis — комплексный разведочный анализ датасета Nero

**Анализ**:
- Описательные статистики по классам signal
- Тесты на нормальность (Shapiro-Wilk, D'Agostino-Pearson)
- Попарные сравнения (t-test / Mann-Whitney U)
- Размер эффекта (Cohen's d)
- Корреляционный анализ (по классам, между соседними фракталами)
- Детекция выбросов (IQR, квантильный метод)
- Снижение размерности (t-SNE, PCA)

**Артефакты**:
- `plots/` — визуализации (гистограммы, boxplots, heatmaps, проекции)
- `feature_stats_by_class.csv` — статистика по классам
- `statistical_tests_results.csv` — результаты тестов

**Основные выводы**:
1. Экстремальный дисбаланс классов (signal=0 доминирует ~95%+)
2. Ключевые признаки: `back`, `front`, `power`, `reverse` (по Cohen's d)
3. Частичная разделимость классов в t-SNE
4. Рекомендации: weighted loss, SMOTE, focal loss

---

### MT/MQL4/Include/lib_PIC.mqh ⚠️
**Назначение**: Библиотека алгоритма PIC (Price in Channel) для формирования фракталов

**Статус**: Legacy код, не приоритет для текущего этапа

**Функции**:
- Формирование фракталов из истории котировок MT4
- Запись в `Nero.csv` (формат: `time:price:direction:front:back:strong:break:reverse:power:count:impulse`)

**Зависимости**: `head_PIC.mqh`, `ERRORs.mqh`, `SERVICE.mqh`, и др.

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
2. Изучи [PRD.md](PRD.md) — цели и критерии успеха
3. Просмотри [.ai/RULES_INDEX.md](.ai/RULES_INDEX.md) — правила работы
4. Открой file headers в модулях — детали реализации

---

## 📚 Дополнительные ресурсы

- **[docs/dataset_description.md](docs/dataset_description.md)** — детальное описание структуры Nero.csv
- **[PRD.md](PRD.md)** — Product Requirements Document (цели, критерии успеха)
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

**Последнее обновление**: 2026-02-11  
**Авторы**: Antigravity (human) + Claude (AI)
