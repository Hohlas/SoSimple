# Быстрый справочник SoSimple

Шпаргалка команд, путей и соглашений для ИИ-агентов.  
**Обновлён**: 2026-02-10

---

## Команды запуска

### Python-скрипты

```bash
# Нормализация данных
python processing/normalize.py

# Маркировка и разделение на выборки
python processing/label_main.py --input Nerod.csv

# Статистический анализ
python statistics/statistics.py --input Nero_train_labeled.csv

# Проверка путей
python test_paths.py
```


### Jupyter Notebooks

```bash
# Запуск Jupyter Lab
jupyter lab

# Экспорт notebook в Python (для анализа кода)
jupyter nbconvert --to script statistics/EDA.ipynb
```


### Skills ИИ-агента

```bash
sync docs                    # Синхронизация документации после изменений
doc this [файл]              # Создать документацию для модуля (⏸️ не реализован)
check docs                   # Проверить актуальность документации (⏸️)
create module [имя]          # Создать новый модуль (⏸️)
check data impact [файл]     # Показать downstream-зависимости (⏸️)
explain step [название]      # Объяснить шаг pipeline (⏸️)
rebuild module index         # Пересоздать MODULE_INDEX.md (⏸️)
refresh module index         # Пересоздать MODULE_INDEX.md (⏸️)
analyze [файл.csv]           # Запустить EDA для датасета (⏸️)
```


---

## Расположение ключевых файлов

### Данные

```
Nero.csv                       # Сырые данные из MT4
Nero_normalized.csv            # Нормализованные данные
Nero_atr_scaler.pkl            # Scaler для ATR (RobustScaler)
Nero_normalization_stats.csv   # Статистика признаков до нормализации

Nero_train_labeled.csv         # Train выборка (до 2024-06-01)
Nero_validation_labeled.csv    # Validation выборка (2024-06-01 - 2024-09-01)
Nero_test_labeled.csv          # Test выборка (после 2024-09-01)
```


### Код

```
MT/MQL4/Include/lib_PIC.mqh    # Библиотека структурирования фракталов (MQL4)

processing/normalize.py         # Нормализация признаков
processing/label_main.py        # Маркировка и разделение
processing/label_signals.py     # Вспомогательные функции маркировки

statistics/statistics.py        # Статистический анализ
statistics/EDA.ipynb            # Exploratory Data Analysis

ML/                             # ML-модели (в разработке)
```


### Документация

```
MODULE_INDEX.md                 # Индекс всех модулей (главный справочник)
DATA_FLOW.md                    # Визуальный граф потока данных
QUICK_REFERENCE.md              # Этот файл
CHANGELOG.md                    # Хронология major milestones

docs/DATA_FLOW.md               # Архитектура проекта
docs/dataset_description.md     # Структура датасета
docs/data_preprocessing/        # Детали скриптов preprocessing
docs/data_analysis/             # Детали статистического анализа

.ai/RULES_INDEX.md              # Индекс правил для агентов
.ai/SKILLS_INDEX.md             # Индекс skills (команд агента)
.ai/rules/                      # Полные тексты правил
.ai/skills/                     # Реализованные skills
```


---

## Соглашения именования

### Файлы данных

```
{base}_{stage}_{variant}.csv

base:    Nero (основной датасет проекта)
stage:   normalized, labeled
variant: train, val, test

Примеры:
  Nero_normalized.csv
  Nero_train_labeled.csv
  Nero_val_labeled.csv
```


### Скрипты

```
{action}_{object}.py

action: normalize, label, analyze, train, validate, test
object: data, signals, model, results

Примеры:
  normalize.py
  label_main.py
  label_signals.py
```


### Документация

```
docs/{category}/{script}.md

category: data_preprocessing, data_analysis, models

Примеры:
  docs/data_preprocessing/normalize.py.md
  docs/data_analysis/statistics.py.md
```


---

## Форматы данных

### CSV (Nero.csv)

**Структура**: См. [dataset_description.md](docs/dataset_description.md)

**Кратко**:
- Колонки: `time_open`, `signal`, `predict`, `ATR`, `fractal0`...`fractal99`
- Формат фрактала: 11 признаков, разделитель `:`


### PKL (Nero_atr_scaler.pkl)

```
Формат: Pickle-сериализованный sklearn.RobustScaler
Использование:
  import pickle
  with open('Nero_atr_scaler.pkl', 'rb') as f:
      scaler = pickle.load(f)
  atr_normalized = scaler.transform(atr_values)
```


---

## Зависимости проекта

### Python (requirements.txt)

```
pandas>=2.0.0
numpy>=1.24.0
scikit-learn>=1.3.0
scipy>=1.11.0
matplotlib>=3.7.0
seaborn>=0.12.0
jupyter>=1.0.0
```


### MQL4

```
Кодировка: UTF-16LE (не UTF-8!)
Стандартная библиотека MetaTrader 4
```


---

## Критические ограничения

### Работа с CSV

```bash
❌ НЕ ДЕЛАЙ:
  df = pd.read_csv('Nero.csv')  # Загрузка всего файла в память

✅ ДЕЛАЙ:
  df = pd.read_csv('Nero.csv', nrows=20)  # Sampling для анализа
  
  # Или streaming для больших операций
  for chunk in pd.read_csv('Nero.csv', chunksize=10000):
      process(chunk)
```


### Кодировка MQL4

```bash
❌ НЕ ДЕЛАЙ:
  Открывать .mq4/.mqh в редакторе с кодировкой UTF-8

✅ ДЕЛАЙ:
  Использовать кодировку UTF-16LE
  Редактировать только в MetaEditor или совместимом редакторе
```


### Data Leakage

```bash
❌ НЕ ДЕЛАЙ:
  # Нормализация по всему датасету перед разделением
  df_normalized = normalize(df)
  train, val, test = split(df_normalized)

✅ ДЕЛАЙ:
  # Сначала разделить, потом fit на train
  train, val, test = split(df)
  scaler.fit(train)
  train_normalized = scaler.transform(train)
  val_normalized = scaler.transform(val)
  test_normalized = scaler.transform(test)
```


---

## Горячие клавиши (Cursor/Antigravity)

```
Cmd/Ctrl + K      — Открыть чат с агентом
Cmd/Ctrl + L      — Включить текущий файл в контекст
Cmd/Ctrl + Shift + L — Включить выделенный код в контекст
@файл              — Ссылка на конкретный файл в промпте
```


---

## Навигация

- **Индекс модулей**: [MODULE_INDEX.md](MODULE_INDEX.md)
- **Поток данных**: [DATA_FLOW.md](DATA_FLOW.md)
- **Правила**: [.ai/RULES_INDEX.md](.ai/RULES_INDEX.md)
- **Skills**: [.ai/SKILLS_INDEX.md](.ai/SKILLS_INDEX.md)
