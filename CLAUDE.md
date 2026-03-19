# CLAUDE.md
> **Инструкции для Claude Code. Главный индекс проекта SoSimple**

---

## 🎯 Цель проекта
ML-бот для прогнозирования разворотов Forex (H1). Подробнее: [PRD.md](docs/PRD.md)

---

## ⚠️ Critical Rules (обязательно!)
1. **Файлы CSV >10MB**: Читай только первые 10 строк (`head -10 file.csv`). Никогда не грузи целиком.
2. **Файлы MQL4**: Открывай `*.mqh`, `*.mq4` только с `encoding='utf-16-le'`.
3. **Большие файлы**: Любые файлы >10MB — только read с limit/offset.

---

## 📋 Инструкции для Claude Code

### Как я работаю с этим проектом
1. **Начинаю с CLAUDE.md** — этот файл содержит все инструкции
2. **Использую skills** — `/brainstorming`, `/writing-plans`, `/test-driven-development` и т.д.
3. **Обновляю код** — добавляю header с датой и версией, обновляю CHANGELOG.md
4. **Коммитить правильно** — коммиты с понятными сообщениями, перед пушем проверю с пользователем
5. **Читаю feedback** — есть memory система в `.claude/projects/-home-hohla-git-SoSimple/memory/`

### Когда использовать skills
- **`/brainstorming`** → перед любым feature/refactor (исследовать идеи, требования)
- **`/writing-plans`** → для многошаговых задач (создать план перед кодом)
- **`/test-driven-development`** → перед реализацией фичи (написать тесты первыми)
- **`/systematic-debugging`** → при ошибке/падении теста (диагностика перед фиксом)
- **`/verification-before-completion`** → перед commit/PR (проверить, что всё работает)
- **`/requesting-code-review`** → при завершении большой работы (ревью перед мержом)
- **`/executing-plans`** → если есть письменный план (выполнить по шагам)

### Работа с памятью (синхронизируется через git)
- Память проекта: `.claude/memory/MEMORY.md` ⬅️ в репозитории
- **MEMORY.md** — индекс (ссылки на файлы памяти)
- **user_profile.md**, **feedback_*.md**, **project_*.md** — сами память-файлы
- Память **синхронизируется через git** → одинакова на всех ПК
- Claude Code автоматически читает эту папку при загрузке проекта

### Git workflow
- ✅ Коммиты: да, регулярно обновляю код
- ✅ Пуши: да, но спрошу confirmation перед пушем на main
- ✅ Ветки: используй если нужна изоляция (или `/using-git-worktrees`)
- ✅ CHANGELOG.md: обновляй при каждой значительной смене

### Что НЕ нужно делать
- ❌ Не делай `git commit` и `git push` без явной просьбы — пользователь контролирует историю сам
- ❌ Не добавляй docstrings/comments если их не было в исходном коде
- ❌ Не рефакторься "заодно" (bug fix = только fix, не cleanup)
- ❌ Не добавляй error handling для невозможных сценариев
- ❌ Не создавай helper-функции для one-time операций
- ❌ Не over-engineer: три строки кода лучше, чем абстракция

---

## 🚀 Быстрый старт

### Команды обработки и анализа данных
```bash
source ~/git/SoSimple/.venv/bin/activate
python processing/label_main.py --input MT/MQL4/Files/Nero.csv --debug
python statistics/statistics.py DATA/Nero_train_labeled.csv
cd ~/git/SoSimple/statistics
export NERO_INPUT_PATH="../DATA/Nero_train_labeled.csv"
jupyter nbconvert --execute --to notebook --output EDA_executed --output-dir ./reports EDA.ipynb
jupyter nbconvert --clear-output --inplace EDA.ipynb
jupyter nbconvert --to markdown --no-input --no-prompt --output EDA_report reports/EDA_executed.ipynb
```

### Команды обучения моделей
```bash
# Все 4 модели последовательно
python -m ML.compare_architectures --task regression
python -m ML.compare_architectures --task classification

# Подбор гиперпараметров
python -m ML.optimize --model bilstm --task classification --trials 50 --epochs 30 --seed 42
python -m ML.optimize --model cnn1d --task regression --trials 30 --epochs 50 --seed 123

# Логгирование лучших результатов
python -m ML.experiment_logger --best f1_macro --task classification
python -m ML.experiment_logger --best pearson_r --task regression
```

### Пути к данным
- **Вход**: `MT/MQL4/Files/Nero.csv` (UTF-16LE, `;`)
- **Выход**: `DATA/Nero_{train|validation|test}_labeled.csv`
- **Мета**: `DATA/Nero_normalization_stats.csv`

---

## 📊 Pipeline данных
Схема: `MT4 → Raw → Sort → Label → Norm → Split → Final` ([Детали в DATA_FLOW.md](docs/DATA_FLOW.md))

---

## 📂 Структура проекта (до 2-го уровня вложенности)
```
.
├── MT/MQL4              # MetaTrader4 - Формирование датасета Nero.csv
│   ├── Experts/        # MQL4 советники
│   ├── Files/          # Файлы данных (Nero.csv)
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
│   │   └── neural_networks.md
│   ├── mql4/           # Документация MQL4
│   │   └── lib_PIC.mqh.md # Библиотека анализа фракталов, классификации уровней и экспорта данных
│   └── plans/          # Планы работы
├── .kilocode/          # Конфигурация IDE: MCP, skills, rules
├── .claude/            # Конфигурация Claude Code
│   ├── commands/       # Симлинки на skills из .kilocode/
│   └── memory/         # Память проекта (синхронизируется через git)
├── AGENTS.md           # Главный индекс для ИИ-агентов
├── CLAUDE.md           # Инструкции для Claude Code ⬅️ ВЫ ЗДЕСЬ
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

## 📋 Workflow для разработки
- **Новое feature**: `/brainstorming` → `/writing-plans` → `/test-driven-development` → `/requesting-code-review`
- **Bugfix**: `/systematic-debugging` → diagnose → fix → `/verification-before-completion`
- **Завершение**: `/finishing-a-development-branch` → merge/PR → update CHANGELOG.md
- **Новый модуль**: Add to structure → Create docs → Add to AGENTS.md → Update this file

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

**Последнее обновление**: 2026-03-19
**Авторы**: Antigravity (human) + Claude (AI)

