# MODULE INDEX
> **Живой указатель модулей проекта SoSimple**

---

## Структура документа
- **Цель**: Быстрый навигатор по модулям проекта
- **Формат**: Детальные описания с назначением, входами/выходами, статусом
- **Обновление**: После коммитов, изменяющих структуру

---

## 📂 Processing (Препроцессинг данных)

### `label_main.py` ✅
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

**Документация**: [label_main.py.md](docs/data_preprocessing/label_main.py.md)

**Статус**: ✅ Актуален (2026-02-13)

---

### `label_signals.py` ✅
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

**Документация**: [label_signals.py.md](docs/data_preprocessing/label_signals.py.md)

**Статус**: ✅ Актуален (2026-02-13)

---

### `normalize.py` ✅
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

**Документация**: [normalize.py.md](docs/data_preprocessing/normalize.py.md)

**Статус**: ✅ Актуален (2026-02-13)

---

## 📊 Statistics (Статистика и EDA)

### `statistics.py` ✅
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

**Документация**: [statistics.py.md](docs/data_analysis/statistics.py.md)

**Статус**: ✅ Актуален (2026-02-13)

---

### `EDA.ipynb` ✅
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

**Документация**: [EDA.ipynb.md](docs/data_analysis/EDA.ipynb.md)

**Статус**: ✅ Актуален (2026-02-13)

---

## 🤖 MT/MQL4 (MetaTrader4 компоненты)

### `lib_PIC.mqh` ⚠️
**Назначение**: Библиотека алгоритма PIC (Price in Channel) для формирования фракталов

**Статус**: Legacy код, не приоритет для текущего этапа

**Функции**:
- Формирование фракталов из истории котировок MT4
- Запись в `Nero.csv` (формат: `time:price:direction:front:back:strong:break:reverse:power:count:impulse`)

**Зависимости**: `head_PIC.mqh`, `ERRORs.mqh`, `SERVICE.mqh`, и др.

**Документация**: [lib_PIC.mqh.md](docs/mql4/lib_PIC.mqh.md)

**Статус**: ⚠️ Наследуемый (legacy), не приоритет для текущего этапа

---

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
- **Статус**: ✅ Актуальные (2026-02-13)

### `data_analysis/` 📂
- `statistics.py.md` ✅ — потоковая статистика
- `EDA.ipynb.md` ✅ — разведочный анализ данных
- **Статус**: ✅ Актуальные (2026-02-13)

### `mql4/` 📂
- `lib_PIC.mqh.md` ✅ — библиотека формирования фракталов
- **Статус**: ✅ Актуальная (2026-02-13)

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

**Последнее обновление**: 2026-02-13  
**Автор**: Antigravity + Claude
