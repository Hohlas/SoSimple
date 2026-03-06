# AI Agent Guide
> **Главный индекс проекта SoSimple для ИИ-агентов и разработчиков**

---

## 🎯 Цель проекта
ML-бот для прогнозирования разворотов Forex (H1). Подробнее: [PRD.md](docs/PRD.md)

---

## 🚀 Быстрый старт

### Основные команды
```bash
# Формирование датасета: MetaTrader4 -> MT/MQL4/Files/Nero.csv
source ~/git/SoSimple/.venv/bin/activate
python processing/label_main.py --input MT/MQL4/Files/Nero.csv --debug
python statistics/statistics.py DATA/Nero_train_labeled.csv
cd ~/git/SoSimple/statistics
export NERO_INPUT_PATH="../DATA/Nero_train_labeled.csv"
jupyter nbconvert --execute --to notebook --output EDA_executed --output-dir ./reports EDA.ipynb
```

### Пути к данным
- **Вход**: `MT/MQL4/Files/Nero.csv` (UTF-16LE, `;`)
- **Выход**: `DATA/Nero_{train|validation|test}_labeled.csv`
- **Мета**: `DATA/Nero_atr_scaler.pkl`, `DATA/Nero_normalization_stats.csv`

### Critical Rules Top-3
1. Читай только первые 10 строк в файлах CSV, т.к. их размер >10MB
2. Не грузи файлы >10MB целиком в чат.
3. Файлы *.mqh, *.mq4 из `MT/` открывать только в `encoding='utf-16-le'`.

---

## 📊 Pipeline данных
Схема: `MT4 → Raw → Sort → Label → Norm → Split → ATR → Final` ([Детали в DATA_FLOW.md](docs/DATA_FLOW.md))

---

## 📂 Структура проекта
```
.
├── MT/MQL4           # MetaTrader4 код. 
├── processing/       # Препроцессинг: label_main.py (CLI), label_signals.py, normalize.py
├── statistics/       # Статистика: statistics.py, EDA.ipynb, файлы статистических характеристик датасета
├── plans/            # Планы работы для ИИ агентов
├── ML/               # Machine Learning: модели, эксперименты, отчеты и графики
│   ├── baseline/     # Baseline-модели: эксперименты, отчеты и графики
│   └── models/       # Другие модели: 
├── .kilocode/        # Правила и скиллы проекта
├── docs/             # Документация: DATA_FLOW.md, PRD.md, dataset_description.md
└── AGENTS.md, CHANGELOG.md, MODULE_INDEX.md, README.md
```

---

## 🔧 Модули
Детальные описания: [MODULE_INDEX.md](MODULE_INDEX.md)
- `processing/label_main.py` — CLI полного конвейера ✅
- `processing/label_signals.py` — Маркировка signal/predict ✅
- `processing/normalize.py` — Нормализация признаков ✅
- `statistics/statistics.py` — Потоковая статистика ✅
- `ML/baseline/baseline_experiments.py` — Baseline-модели (Dummy, LogReg, RF, XGBoost, LightGBM) ✅
- `ML/train.py` — Единый скрипт обучения нейросетей (PyTorch) ✅
- `ML/models/` — 4 архитектуры: Bi-LSTM, 1D-CNN, Transformer, Hybrid CNN+LSTM ✅
- `ML/compare_architectures.py` — Сравнение всех архитектур ✅
- `MT/MQL4/Include/lib_PIC.mqh` — Основная библиотека создания датасета Nero.csv ⚠️

---

## ⚙️ Правила работы
Все правила: [.kilocode/rules/](.kilocode/rules/)

### Data Leakage Prevention
Детали: [DATA_FLOW.md § Data Leakage Prevention](docs/DATA_FLOW.md#-data-leakage-prevention)

---

## 🛠️ Технологический стек
- **Языки**: Python 3.11+, MQL4; **Библиотеки**: Pandas, NumPy, Scikit-learn, Scipy
- **Визуализация**: Matplotlib, Seaborn; **ML**: XGBoost, LightGBM, PyTorch (план)

---

## 📋 Workflow для агента
- **Код**: Обнови header ([rule 000](docs/plans/000-documentation.md)), используй skills, обнови CHANGELOG.md.
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
| Интеграция с MT4 | 📅 Планируется | DLL/REST API |


---


## 🧪 Артефакты statistics/
Скрипты `statistics.py` и `EDA.ipynb` генерируют консолидированные отчеты (`.json`, `.md`), таблицы статистик и визуализации (каталог `plots/`) для оценки качества маркировки и распределения признаков.
Подробности: [docs/data_analysis/statistics.py.md](docs/data_analysis/statistics.py.md)

---

**Последнее обновление**: 2026-02-18
**Авторы**: Antigravity (human) + Claude (AI)

