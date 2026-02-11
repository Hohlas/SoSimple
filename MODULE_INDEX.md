# MODULE INDEX
> **Живой указатель модулей проекта SoSimple**

---

## Структура документа
- **Цель**: Быстрый навигатор по модулям проекта
- **Формат**: Список с кратким описанием и статусом
- **Обновление**: После коммитов, изменяющих структуру

---

## 📂 Processing (Препроцессинг данных)

### `label_main.py` ✅
- **Назначение**: CLI для полного конвейера подготовки данных
- **Конвейер**: Сортировка → Маркировка → Нормализация → Разделение → ATR
- **Вход**: `MT/MQL4/Files/Nero.csv`
- **Выход**: `{stem}_train_labeled.csv`, `{stem}_validation_labeled.csv`, `{stem}_test_labeled.csv`
- **Использование**: `python label_main.py --input MT/MQL4/Files/Nero.csv --debug`
- **Статус**: ✅ Актуален (2026-02-11)

### `label_signals.py` ✅
- **Назначение**: Маркировка сигналов (signal + predict) с учетом направления целевого фрактала
- **Ключевая функция**: `label_all(input_path, output_path, debug=False)`
- **Логика**: Поиск ближайшего сильного фрактала → расчёт signal → predict с учётом direction
- **Статус**: ✅ Актуален (2026-02-11)

### `normalize.py` ✅
- **Назначение**: Нормализация признаков (построчная + глобальная ATR)
- **Методы**:
  - `normalize_rowwise()` — piecewise linear-log для predict/front/back/impulse/etc, min-max для price
  - `normalize_atr_train()` — RobustScaler fit+transform (train)
  - `normalize_atr_inference()` — RobustScaler transform only (val/test)
- **Артефакты**: `{stem}_atr_scaler.pkl`, `{stem}_normalization_stats.csv`
- **Статус**: ✅ Актуален (2026-02-11)

---

## 📊 Statistics (Статистика и EDA)

### `statistics.py` ✅
- **Назначение**: Потоковая обработка Nero.csv с онлайн-расчётом статистики (метод Уэлфорда, Reservoir Sampling)
- **Вход**: `statistics/Nero.csv`
- **Выход**: 
  - `statistics_summary.json` — сводная статистика по всем признакам
  - `class_balance_report.csv` — баланс классов signal
  - `feature_distributions.csv` — распределения признаков
  - `nero_sample_stratified.csv` — стратифицированная выборка
  - `class_statistics.json` — статистика по классам
- **Использование**: `python statistics/statistics.py`
- **Документация**: [statistics.py.md](docs/data_analysis/statistics.py.md)
- **Статус**: ✅ Актуален (2026-02-11)

### `EDA.ipynb` ✅
- **Назначение**: Exploratory Data Analysis — комплексный разведочный анализ датасета Nero
- **Анализ**: Описательные статистики, тесты на нормальность, попарные сравнения (t-test/Mann-Whitney), корреляции, выбросы, t-SNE/PCA
- **Артефакты**: 
  - `plots/` — визуализации (гистограммы, boxplots, heatmaps, проекции)
  - `feature_stats_by_class.csv` — статистика по классам
  - `statistical_tests_results.csv` — результаты тестов
- **Документация**: [EDA.ipynb.md](docs/data_analysis/EDA.ipynb.md)
- **Статус**: ✅ Актуален (2026-02-11)

---

## 🤖 MT/MQL4 (MetaTrader4 компоненты)

### `lib_PIC.mqh` ⚠️
- **Назначение**: Библиотека алгоритма PIC (Price in Channel) для формирования фракталов
- **Размер**: ~41KB
- **Путь**: `MT/MQL4/Include/lib_PIC.mqh` ([Документация](docs/mql4/lib_PIC.mqh.md))
- **Зависимости**: `head_PIC.mqh`, `ERRORs.mqh`, `SERVICE.mqh`, и др.
- **Статус**: ⚠️ Наследуемый (legacy), не приоритет для текущего этапа

### Другие `.mqh` библиотеки 📁
- `FUNCTIONS.mqh`, `ORDERS.mqh`, `SERVICE.mqh`, `MM.mqh`, `INPUT.mqh`, `OUTPUT.mqh` — вспомогательные модули торговой логики
- `lib_ATR.mqh`, `lib_Flat.mqh`, `lib_POC.mqh` — индикаторные библиотеки
- **Статус**: 📁 В архиве (не требуется для ML pipeline)

---

## 📄 Docs (Документация)

### `data_preprocessing/` 📂
- `label_main.py.md` ✅ — документация оркестратора
- `label_signals.py.md` ✅ — логика маркировки
- `normalize.py.md` ✅ — методы нормализации
- **Статус**: ✅ Актуальные (2026-02-11)

### `data_analysis/` 📂
- `statistics.py.md` ✅ — потоковая статистика
- `EDA.ipynb.md` ✅ — разведочный анализ данных
- **Статус**: ✅ Актуальные (2026-02-11)

### `mql4/` 📂
- `lib_PIC.mqh.md` ✅ — библиотека формирования фракталов
- **Статус**: ✅ Актуальная (2026-02-11)

### `dataset_description.md` ✅
- **Назначение**: Подробное описание структуры датасета Nero.csv
- **Местоположение**: `docs/dataset_description.md`

### `DATA_FLOW.md` ✅
- **Назначение**: Визуальная диаграмма потока данных через все этапы pipeline
- **Местоположение**: `docs/DATA_FLOW.md`

---


## 🔮 ML (Machine Learning компоненты)

### Статус: 🚧 В разработке
Модули для обучения и инференса модели будут добавлены на следующем этапе.

---

## ⚙️ .ai/ (AI/LLM контекст)

- `RULES_INDEX.md` — правила работы с проектом для LLM
- `SKILLS_INDEX.md` — список навыков/возможностей AI для проекта

---

## 📝 Корневые файлы


### `PRD.md` ⚠️
- **Статус**: ⚠️ Предложено интегрировать в другие документы

### `README.md` ⚠️
- **Статус**: ⚠️ Предложено заменить на `PROJECT_CONTEXT.md`

### `CHANGELOG.md` ✅ 
- **Назначение**: Major milestones и ключевые изменения

---

## 🏷️ Легенда статусов
- ✅ **Актуален** — модуль работает и документирован
- ⚠️ **Требует ревью** — модуль может быть устаревшим
- 🚧 **В разработке** — модуль в процессе создания
- 📁 **В архиве** — модуль больше не активен, но сохранён для справки
- 📂 **Директория** — группа модулей

---

**Последнее обновление**: 2026-02-11  
**Автор**: Antigravity + Claude
