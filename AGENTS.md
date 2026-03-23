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
# Сравнение 4 архитектур (regression_updn — основной режим)
python -m ML.compare_architectures --task regression_updn

# Optuna оптимизация (transformer — лучшая архитектура)
python -m ML.optimize --model transformer --task regression_updn --trials 50 --epochs 30 --seed 42

# Оценка на тестовой выборке (OOS)
python -m ML.evaluate_test --task regression_updn --model transformer

# Threshold analysis: поиск оптимального θ для торговых сигналов
python -m ML.threshold_analysis --task regression_updn --horizon 12

# Логгер экспериментов
python -m ML.experiment_logger --best pearson_r --task regression_updn

# === Triple Barrier (параллельный трек) ===
python -m ML.train --model transformer --task triple_barrier --epochs 50
python -m ML.evaluate_test --task triple_barrier --model transformer
python -m ML.threshold_analysis --task triple_barrier --model transformer
python -m ML.compare_architectures --task triple_barrier
```

### команды генерации ML-сигналов для MT4
```bash
# Генерация ml_signals.csv (regression_updn, transformer, H12, θ=2.665)
python -m API.generate_signals
python -m API.generate_signals --horizon 24 --theta 3.0  # кастомные параметры

# Генерация ml_signals_tb.csv (triple_barrier, фиксированные SL/TP)
python -m API.generate_signals --task triple_barrier --theta 0.6
```

### Пути к данным
- **Вход**: `MT/MQL4/Files/Nero.csv` (UTF-16LE, `;`)
- **Выход**: `DATA/Nero_{train|validation|test}_labeled.csv`
- **Мета**: `DATA/Nero_normalization_stats.csv`

### Critical Rules Top-3
1. Читай только первые 10 строк в файлах CSV, т.к. их размер >10MB
2. Не грузи файлы >2MB целиком в чат.
3. Файлы *.mqh, *.mq4 из `MT/` открывать только в `encoding='utf-16-le'`.

---

## 📊 Pipeline данных
Схема: `MT4 → Raw → Sort → Label → Norm → Split → Train → Signals → MT4` ([Детали в DATA_FLOW.md](docs/DATA_FLOW.md))

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
│   ├── reports/        # Отчёты экспериментов (threshold_analysis, evaluate_test)
│   ├── conformal/      # Conformal Prediction: calibrate.py, quantiles, report
│   ├── train.py        # Скрипт обучения (classification, regression, regression_updn)
│   ├── optimize.py     # Optuna оптимизация гиперпараметров
│   ├── compare_architectures.py # Сравнение 4 архитектур
│   ├── evaluate_test.py # OOS оценка на тестовой выборке
│   ├── threshold_analysis.py # Поиск оптимального θ для торговых сигналов
│   ├── data_loader.py  # Dataset и DataLoader (20 фич на фрактал, 100 фракталов)
│   ├── losses.py       # AsymmetricLoss для регрессии
│   ├── utils.py        # Метрики: Pearson r, MAE, R², multi-target metrics
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
│   │   ├── ml_signal_integration.md # Файловый обмен ML ↔ MT4
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
- **Визуализация**: Matplotlib, Seaborn; **ML**: PyTorch, XGBoost, LightGBM, Optuna

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
| Сбор данных (MT4) | ✅ Готов | lib_PIC.mqh, NERO_CSV_CREATE() — 18 полей на фрактал |
| Препроцессинг | ✅ Готов | label_main.py, normalize.py (Piecewise Linear-Log) |
| Статистика/EDA | ✅ Готов | statistics.py, EDA.ipynb |
| ML модели | ✅ Готов | Transformer (лучший), BiLSTM, CNN1D, Hybrid; regression_updn (6 таргетов) |
| Triple Barrier | 🔧 Код готов | 12 бинарных таргетов, BCEWithLogitsLoss, iSignal=5, lib_ML_Signal_TB.mqh |
| Генерация сигналов | ✅ Готов | [generate_signals.py](API/generate_signals.py) → ml_signals.csv / ml_signals_tb.csv |
| Интеграция с MT4 | ✅ Готов | Файловый обмен CSV, ML_TRADE() (iSignal=3) + ML_TRADE_TB() (iSignal=5) |
| Торговый робот | ✅ Работает | OOS PF=4.50 (θ=2.665, 12H). В тестере: PF=0.85 при ML_MinRatio=5.0 ([trading_strategy](docs/mql4/trading_strategy.md)) |
| Conformal Prediction | ✅ Готов | Инфраструктура готова; при θ=2.665 эффект нейтральный ([docs](docs/ml/conformal_prediction.md)) |


---


## 🧪 Артефакты statistics/
Скрипты `statistics.py` и `EDA.ipynb` генерируют консолидированные отчеты (`.json`, `.md`), таблицы статистик и визуализации (каталог `plots/`) для оценки качества маркировки и распределения признаков.
Подробности: [docs/data_analysis/statistics.py.md](docs/data_analysis/statistics.py.md)

---

**Последнее обновление**: 2026-03-22
**Авторы**: Antigravity (human) + Claude (AI)

