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
| [baseline_experiments.py](ML/baseline/baseline_experiments.py) | Baseline-модели (5 алгоритмов) | `*_labeled.csv` → `baseline/reports/baseline_report.md`, `baseline/plots/` | [docs](docs/ml/baseline_experiments.py.md) | ✅ |
| [data_loader.py](ML/data_loader.py) | Dataset/DataLoader для фрактальных последовательностей | `*_labeled.csv` → in-memory tensors, `*.npy` cache | — | ✅ |
| [train.py](ML/train.py) | Единый скрипт обучения нейросетей (--task regression/classification) | DataLoader → `checkpoints/`, `plots/` | — | ✅ |
| [losses.py](ML/losses.py) | Focal Loss для классификации, Huber Loss для регрессии | — | — | ✅ |
| [utils.py](ML/utils.py) | Утилиты: seed, параметры, класификационные и регрессионные метрики | — | — | ✅ |
| [models/bilstm.py](ML/models/bilstm.py) | Bi-LSTM классификатор | (batch, 100, 11) → (batch, 3) | — | ✅ |
| [models/cnn1d.py](ML/models/cnn1d.py) | 1D-CNN классификатор | (batch, 100, 11) → (batch, 3) | — | ✅ |
| [models/transformer.py](ML/models/transformer.py) | Transformer Encoder классификатор | (batch, 100, 11) → (batch, 3) | — | ✅ |
| [models/hybrid_cnn_lstm.py](ML/models/hybrid_cnn_lstm.py) | Hybrid CNN+LSTM классификатор | (batch, 100, 11) → (batch, 3) | — | ✅ |
| [compare_architectures.py](ML/compare_architectures.py) | Сравнение всех 4 архитектур | DataLoader → `reports/architecture_comparison.md` | — | ✅ |
| [optimize.py](ML/optimize.py) | Оптимизация гиперпараметров (Optuna) | DataLoader → `reports/optuna_*.json` | — | ✅ |
| [experiment_logger.py](ML/experiment_logger.py) | Логирование экспериментов в CSV | results → `reports/experiments_log.csv` | — | ✅ |

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
| [neural_networks.md](docs/ml/neural_networks.md) | ML pipeline: архитектуры, обучение, метрики |

## Легенда статусов
✅ Актуален | ⚠️ Требует ревью | 🚧 В разработке | 📁 В архиве

---
**Последнее обновление**: 2026-03-11
