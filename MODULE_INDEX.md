# MODULE INDEX
> Живой указатель модулей проекта SoSimple

---

## Processing

| Модуль | Назначение | Вход → Выход | Docs | Статус |
|--------|-----------|--------------|------|--------|
| [label_main.py](processing/label_main.py) | CLI оркестратор pipeline | `Nero.csv` → `*_labeled.csv` | [docs](docs/data_preprocessing/label_main.py.md) | ✅ |
| [label_signals.py](processing/label_signals.py) | Маркировка signal/predict | sorted CSV → labeled CSV | [docs](docs/data_preprocessing/label_signals.py.md) | ✅ |
| [normalize.py](processing/normalize.py) | Нормализация признаков | labeled CSV → normalized CSV | [docs](docs/data_preprocessing/normalize.py.md) | ✅ |

## Statistics

| Модуль | Назначение | Вход → Выход | Docs | Статус |
|--------|-----------|--------------|------|--------|
| [statistics.py](statistics/statistics.py) | Онлайн-расчёт статистики | `Nero.csv` → `.json`, `.csv`, `.md` | [docs](docs/data_analysis/statistics.py.md) | ✅ |
| [EDA.ipynb](statistics/EDA.ipynb) | Разведочный анализ данных | `Nero.csv` → `plots/`, `.csv` | [docs](docs/data_analysis/EDA.ipynb.md) | ✅ |

## MT/MQL4

| Модуль | Назначение | Вход → Выход | Docs | Статус |
|--------|-----------|--------------|------|--------|
| [lib_PIC.mqh](MT/MQL4/Include/lib_PIC.mqh) | Алгоритм формирования фракталов | Tick data → `Nero.csv` | [docs](docs/mql4/lib_PIC.mqh.md) | ⚠️ |
| `Вспомогательные .mqh` | Торговая логика и индикаторы | - | - | 📁 |

## ML

| Модуль | Назначение | Вход → Выход | Docs | Статус |
|--------|-----------|--------------|------|--------|
| Models | Обучение и инференс | - | - | 🚧 |

## Docs

| Файл | Назначение |
|------|------------|
| [DATA_FLOW.md](docs/DATA_FLOW.md) | Визуальная диаграмма потока данных |
| [dataset_description.md](docs/dataset_description.md) | Описание структуры датасета Nero.csv |
| [PRD.md](docs/PRD.md) | Product Requirements Document |
| [label_main.py.md](docs/data_preprocessing/label_main.py.md) | Документация оркестратора |
| [label_signals.py.md](docs/data_preprocessing/label_signals.py.md) | Логика маркировки signal/predict |
| [normalize.py.md](docs/data_preprocessing/normalize.py.md) | Методы нормализации признаков |
| [statistics.py.md](docs/data_analysis/statistics.py.md) | Справка по потоковой статистике |
| [EDA.ipynb.md](docs/data_analysis/EDA.ipynb.md) | Отчет по разведочному анализу |
| [lib_PIC.mqh.md](docs/mql4/lib_PIC.mqh.md) | Описание библиотеки PIC |

## Легенда статусов
✅ Актуален | ⚠️ Требует ревью | 🚧 В разработке | 📁 В архиве

---
**Последнее обновление**: 2026-02-14
