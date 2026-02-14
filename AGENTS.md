# AI Agent Guide
> **Главный индекс проекта SoSimple для ИИ-агентов и разработчиков**

---

## 🎯 Цель проекта
ML-бот для прогнозирования разворотов Forex (H1). Подробнее: [PRD.md](docs/PRD.md)

---

## 🚀 Быстрый старт

### Основные команды
```bash
# Препроцессинг: MT4 -> train/val/test
python processing/label_main.py --input MT/MQL4/Files/Nero.csv --debug
# Статистика (из statistics/): cd statistics && python statistics.py
# Jupyter: jupyter nbconvert --execute --to notebook --output EDA_executed EDA.ipynb
```

### Пути к данным
- **Вход**: `MT/MQL4/Files/Nero.csv` (UTF-16LE, `;`)
- **Выход**: `Nero_{train|validation|test}_labeled.csv`
- **Мета**: `Nero_atr_scaler.pkl`, `Nero_normalization_stats.csv`

### Critical Rules Top-3
1. **[000] Headers first**: Читай первые 10 строк CSV перед работой.
2. **[007] No CSV in context**: Не грузи файлы >100MB целиком в чат.
3. **[100] MQL4 encoding**: Файлы из `MT/` открывать только в `encoding='utf-16-le'`.

---

## 📊 Pipeline данных
Схема: `MT4 → Raw → Sort → Label → Norm → Split → ATR → Final` ([Детали в DATA_FLOW.md](docs/DATA_FLOW.md))

---

## 📂 Структура проекта
```
.
├── MT/MQL4/          # MT4 код: lib_PIC.mqh (алгоритм PIC)
├── processing/       # Препроцессинг: label_main.py (CLI), label_signals.py, normalize.py
├── statistics/       # Статистика: statistics.py, EDA.ipynb
├── ML/               # Machine Learning (в разработке)
├── .ai/              # Правила (.ai/rules/) и команды (.ai/SKILLS_INDEX.md)
├── docs/             # Документация: DATA_FLOW.md, PRD.md, dataset_description.md
└── AGENTS.md, CHANGELOG.md, README.md
```

---

## 🔧 Модули
Детальные описания: [MODULE_INDEX.md](MODULE_INDEX.md)
- `processing/label_main.py` — CLI полного конвейера ✅
- `processing/label_signals.py` — Маркировка signal/predict ✅
- `processing/normalize.py` — Нормализация признаков ✅
- `statistics/statistics.py` — Потоковая статистика ✅
- `MT/MQL4/Include/lib_PIC.mqh` — Алгоритм PIC (legacy) ⚠️

---

## ⚙️ Правила работы
Все правила: [.ai/RULES_INDEX.md](.ai/RULES_INDEX.md)

### Data Leakage Prevention
Детали: [DATA_FLOW.md § Data Leakage Prevention](docs/DATA_FLOW.md#-data-leakage-prevention)

---

## 🛠️ Технологический стек
- **Языки**: Python 3.11+, MQL4; **Библиотеки**: Pandas, NumPy, Scikit-learn, Scipy
- **Визуализация**: Matplotlib, Seaborn; **ML**: PyTorch (план)

---

## 📋 Workflow для агента
- **Код**: Обнови header ([rule 000](.ai/rules/000-documentation.md)), проверь правила, обнови CHANGELOG.md.
- **Новый модуль**: Header -> Добавить в AGENTS.md -> Обновить структуру.
- **Изучение**: AGENTS.md (индекс) -> PRD.md (цели) -> RULES_INDEX.md (правила).

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
| ML модели | 🚧 В разработке | Архитектура в процессе выбора |
| Интеграция с MT4 | 📅 Планируется | DLL/REST API |


---


## 🧪 Артефакты statistics/
Скрипты `statistics.py` и `EDA.ipynb` генерируют консолидированные отчеты (`.json`, `.md`), таблицы статистик и визуализации (каталог `plots/`) для оценки качества маркировки и распределения признаков.
Подробности: [docs/data_analysis/statistics.py.md](docs/data_analysis/statistics.py.md)

---

**Последнее обновление**: 2026-02-14
**Авторы**: Antigravity (human) + Claude (AI)

