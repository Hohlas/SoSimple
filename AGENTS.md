# AI Agent Guide
> **Главный индекс проекта SoSimple для ИИ-агентов и разработчиков**

---

## 🎯 Цель проекта
ML-бот для прогнозирования разворотов Forex (H1). Подробнее: [PRD.md](docs/PRD.md)

---

## 🚀 Быстрый старт

### команды обработки и анализа данных
```bash
source ~/git/SoSimple/.venv/bin/activate
python processing/label_main.py --input MT/MQL4/Files/Nero.csv --debug
python statistics/statistics.py DATA/Nero_train_labeled.csv
cd ~/git/SoSimple/statistics
export NERO_INPUT_PATH="../DATA/Nero_train_labeled.csv"
jupyter nbconvert --execute --to notebook --output EDA_executed --output-dir ./reports EDA.ipynb # Выполнить ноутбук и сохранить результат в отдельный файл
jupyter nbconvert --clear-output --inplace EDA.ipynb # Очистить выходы в исходном файле
jupyter nbconvert --to markdown --no-input --no-prompt --output EDA_report reports/EDA_executed.ipynb # Исключает изображения и исходный код, оставляя только текстовые отчеты
```

### команды обучения моделей
```bash
# Все 4 модели последовательно
python -m ML.compare_architectures --task regression 
python -m ML.compare_architectures --task classification

# Запуск подбора для классификации
python -m ML.optimize --model bilstm --task classification --trials 50 --epochs 30 --seed 42
# Запуск подбора для регрессии
python -m ML.optimize --model cnn1d --task regression --trials 30 --epochs 50 --seed 123

# Для классификации:
python -m ML.experiment_logger --best f1_macro --task classification
# Для регрессии:
python -m ML.experiment_logger --best pearson_r --task regression


```

### Пути к данным
- **Вход**: `MT/MQL4/Files/Nero.csv` (UTF-16LE, `;`)
- **Выход**: `DATA/Nero_{train|validation|test}_labeled.csv`
- **Мета**: `DATA/Nero_normalization_stats.csv`

### Critical Rules Top-3
1. Читай только первые 10 строк в файлах CSV, т.к. их размер >10MB
2. Не грузи файлы >10MB целиком в чат.
3. Файлы *.mqh, *.mq4 из `MT/` открывать только в `encoding='utf-16-le'`.

---

## 📊 Pipeline данных
Схема: `MT4 → Raw → Sort → Label → Norm → Split → Final` ([Детали в DATA_FLOW.md](docs/DATA_FLOW.md))

---

## 📂 Структура проекта (до 2-го уровня вложенности)
```
.
├── API/                 # Python ML API и генерация сигналов
│   └── generate_signals.py  # Генерация ml_signals.csv для MT4
├── MT/MQL4              # MetaTrader4 - Формирование датасета Nero.csv
│   ├── Experts/        # MQL4 советники
│   ├── Files/          # Файлы данных (Nero.csv, ml_signals.csv)
│   └── Include/        # MQL4 библиотеки (.mqh)
├── processing/         # Препроцессинг данных: Маркировка signal/predict, Нормализация признаков
├── statistics/         # Статистика и EDA
│   ├── statistics.py   # расчёт статистики по фракталам и сигналам
│   ├── EDA.ipynb       # Разведочный анализ данных
│   ├── plots/          # Визуализации
│   ├── reports/        # Отчёты
│   └── EDA_files/      # Файлы EDA
├── ML/                 # Machine Learning
│   ├── baseline/       # Baseline-модели (5 алгоритмов)
│   ├── models/         # Neural Network модели: Bi-LSTM, 1D-CNN, Transformer, Hybrid CNN+LSTM
│   ├── checkpoints/    # Чекпоинты моделей (.pt)
│   ├── plots/          # Графики обучения
│   ├── reports/        # Отчёты экспериментов
│   ├── conformal/      # Conformal Prediction: calibrate.py, quantiles, report
│   ├── old/            # Архив старого кода
│   ├── train.py        # Скрипт обучения
│   ├── optimize.py     # Optuna оптимизация
│   ├── compare_architectures.py # Сравнение архитектур
│   ├── data_loader.py  # Dataset и DataLoader для фрактальных последовательностей
│   └── experiment_logger.py # CSV-логгер для ML-экспериментов
├── DATA/               # Обрабатывамые данные
│   ├── Nero_train_labeled.csv
│   ├── Nero_validation_labeled.csv
│   ├── Nero_test_labeled.csv
│   └── Nero_normalization_stats.csv
├── docs/               # Документация
│   ├── DATA_FLOW.md    # Поток данных
│   ├── dataset_description.md # Описание структуры датасета
│   ├── PRD.md          # Product Requirements
│   ├── archive/        # Архив НЕ актуальных заметок. НЕ СМОТРИ этот каталог!
│   ├── data_analysis/  # Документация анализа
│   │   ├── statistics.py.md
│   │   └── EDA.ipynb.md
│   ├── data_preprocessing/ # Документация препроцессинга
│   │   ├── label_main.py.md
│   │   ├── label_signals.py.md
│   │   └── normalize.py.md
│   ├── ml/             # Документация ML
│   │   ├── baseline_experiments.py.md
│   │   ├── neural_networks.md
│   │   └── conformal_prediction.md
│   ├── mql4/           # Документация MQL4
│   │   ├── lib_PIC.mqh.md # Библиотека анализа фракталов
│   │   ├── ml_signal_integration.md # Архитектура ML ↔ MT4
│   │   └── trading_strategy.md # Полный алгоритм торгового эксперта MAIN()
│   └── plans/          # Планы работы
├── .kilocode/          # Конфигурация IDE: MCP, skills, rules
├── AGENTS.md           # Главный индекс для ИИ-агентов
├── CHANGELOG.md        # Основные этапы, История изменений
├── MODULE_INDEX.md     # Детальные описания модулей
└── README.md           # Точка входа в проект
```

> **Примечание**: Полный рекурсивный список см. в `environment_details` при запуске.

---

### Data Leakage Prevention
Детали: [DATA_FLOW.md § Data Leakage Prevention](docs/DATA_FLOW.md#-data-leakage-prevention)

---

## 🛠️ Технологический стек
- **Языки**: Python 3.11+, MQL4; **Библиотеки**: Pandas, NumPy, Scikit-learn, Scipy
- **Визуализация**: Matplotlib, Seaborn; **ML**: XGBoost, LightGBM, PyTorch (план)

---

## 📋 Workflow для агента
- **Код**: Обнови header, используй skills, обнови CHANGELOG.md.
- **Новый модуль**: Header -> Добавить в AGENTS.md -> Обновить структуру.
- **Изучение**: AGENTS.md (индекс) -> PRD.md (цели) -> .kilocode/skills/ (workflow).

---

## 📚 Доп. ресурсы
- [docs/dataset_description.md](docs/dataset_description.md) — структура данных.
- [CHANGELOG.md](CHANGELOG.md) — история изменений.

---

## 🚧 Статус разработки
| Компонент | Статус | Примечание |
|-----------|--------|------------|
| Сбор данных (MT4) | ✅ Готов | lib_PIC.mqh (legacy) |
| Препроцессинг | ✅ Готов | label_main.py, normalize.py |
| Статистика/EDA | ✅ Готов | statistics.py, EDA.ipynb |
| ML модели | ✅ Готов | Baseline и 4 NN архитектуры реализованы |
| Интеграция с MT4 | ✅ Готов | Файловый обмен CSV ([docs](docs/mql4/ml_signal_integration.md)) |
| Conformal Prediction | ✅ Готов | Инфраструктура готова; при θ=2.665 эффект нейтральный ([docs](docs/ml/conformal_prediction.md)) |


---


## 🧪 Артефакты statistics/
Скрипты `statistics.py` и `EDA.ipynb` генерируют консолидированные отчеты (`.json`, `.md`), таблицы статистик и визуализации (каталог `plots/`) для оценки качества маркировки и распределения признаков.
Подробности: [docs/data_analysis/statistics.py.md](docs/data_analysis/statistics.py.md)

---

**Последнее обновление**: 2026-03-20
**Авторы**: Antigravity (human) + Claude (AI)

