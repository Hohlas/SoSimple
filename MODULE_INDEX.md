# MODULE INDEX
> Живой указатель модулей проекта SoSimple

---

## Processing

| Модуль | Назначение | Вход → Выход | Docs | Статус |
|--------|-----------|--------------|------|--------|
| [label_main.py](processing/label_main.py) | CLI оркестратор pipeline | `Nero.csv` → `*_labeled.csv` | [docs](docs/processing/label_main.py.md) | 🏁 |
| [label_signals.py](processing/label_signals.py) | Маркировка signal/predict/UpDn | sorted CSV → labeled CSV | [docs](docs/processing/label_signals.py.md) | 🏁 |
| [normalize.py](processing/normalize.py) | Построчная нормализация признаков | labeled CSV → normalized CSV + `*.npy` | [docs](docs/processing/normalize.py.md) | 🏁 |

## Statistics

| Модуль | Назначение | Вход → Выход | Docs | Статус |
|--------|-----------|--------------|------|--------|
| [statistics.py](statistics/statistics.py) | Потоковая статистика (Welford, Reservoir sampling) | `Nero.csv` → `.json`, `.csv` | [docs](docs/statistics/statistics.py.md) | 🏁 |
| [EDA.ipynb](statistics/EDA.ipynb) | Разведочный анализ данных | `Nero.csv` → `plots/`, `.csv` | [docs](docs/statistics/EDA.ipynb.md) | 🏁 |
| [signal_tracer.py](statistics/signal_tracer.py) | Trade-level reconciliation: ML vs MT4 | `ml_signals.csv` + `Nero_*_labeled.csv` + `*.npy` + log → dossiers, CSV | [docs](docs/statistics/signal_tracer.py.md) | ✅ |

## API

| Модуль | Назначение | Вход → Выход | Docs | Статус |
|--------|-----------|--------------|------|--------|
| [generate_signals.py](API/generate_signals.py) | Генерация ML-сигналов для MT4 | `Nero_*_labeled.csv` + checkpoint → `ml_signals.csv` | [docs](docs/MT/ml_signal_integration.md) | ✅ |

## MT/MQL4

| Модуль | Назначение | Вход → Выход | Docs | Статус |
|--------|-----------|--------------|------|--------|
| [lib_PIC.mqh](MT/MQL4/Include/lib_PIC.mqh) | Алгоритм формирования фракталов | Tick data → `Nero.csv` | [docs](docs/MT/lib_PIC.mqh.md) | ⚠️ |
| [lib_ML_Signal.mqh](MT/MQL4/Include/lib_ML_Signal.mqh) | Чтение ML-сигналов из CSV, торговля | `ml_signals.csv` → `OPEN_BUY/SELL` | [docs](docs/MT/ml_signal_integration.md) | ✅ |
| `Вспомогательные .mqh` | Торговая логика и индикаторы | — | — | 📦 |

## ML

| Модуль | Назначение | Вход → Выход | Docs | Статус |
|--------|-----------|--------------|------|--------|
| [data_loader.py](ML/data_loader.py) | Dataset/DataLoader: CSV → 3D тензор (N, 100, 20) | `*_labeled.csv` → in-memory tensors, `*.npy` cache | — | ✅ |
| [losses.py](ML/losses.py) | FocalLoss, HuberLoss, AsymmetricLoss | — | — | ✅ |
| [utils.py](ML/utils.py) | seed, метрики (Pearson r, MAE, R²), device | — | — | ✅ |
| [experiment_logger.py](ML/experiment_logger.py) | CSV-логгер экспериментов | results → `reports/experiments_log.csv` | — | 🏁 |
| [models/transformer.py](ML/models/transformer.py) | Transformer Encoder (лучшая архитектура) | (batch, 100, 20) → (batch, 6) | [docs](docs/ML/neural_networks.md) | ✅ |
| [models/bilstm.py](ML/models/bilstm.py) | Bi-LSTM | (batch, 100, 20) → (batch, 6) | [docs](docs/ML/neural_networks.md) | 🏁 |
| [models/cnn1d.py](ML/models/cnn1d.py) | 1D-CNN | (batch, 100, 20) → (batch, 6) | [docs](docs/ML/neural_networks.md) | 🏁 |
| [models/hybrid_cnn_lstm.py](ML/models/hybrid_cnn_lstm.py) | Hybrid CNN+LSTM | (batch, 100, 20) → (batch, 6) | [docs](docs/ML/neural_networks.md) | 🏁 |
| [train.py](ML/train.py) | Обучение (--task regression_updn / triple_barrier) | DataLoader → `checkpoints/`, `plots/` | — | ✅ |
| [optimize.py](ML/optimize.py) | Optuna оптимизация гиперпараметров | DataLoader → `reports/optuna_*.json` | — | 🏁 |
| [compare_architectures.py](ML/compare_architectures.py) | Сравнение 4 архитектур | DataLoader → `reports/architecture_comparison.md` | — | 🏁 |
| [evaluate_test.py](ML/evaluate_test.py) | OOS оценка (profit factor, precision) на тестовой выборке | checkpoint + test CSV → `reports/evaluate_test_*.md` | — | ✅ |
| [threshold_analysis.py](ML/threshold_analysis.py) | Поиск оптимального порога θ (regression → signal) | checkpoint + val CSV → `reports/threshold_analysis.md` | — | ✅ |
| [reproducibility_tests.py](ML/reproducibility_tests.py) | Тесты детерминизма и стабильности seed | — → `reports/reproducibility_report.md` | — | 🏁 |
| [baseline_experiments.py](ML/baseline/baseline_experiments.py) | Baseline-модели (XGBoost, LightGBM, RF, SVM, LogReg) | `*_labeled.csv` → `baseline/reports/`, `baseline/plots/` | [docs](docs/ML/baseline_experiments.py.md) | 🏁 |
| [conformal/calibrate.py](ML/conformal/calibrate.py) | Split Conformal Prediction калибровка | val CSV + checkpoint → `conformal/conformal_quantiles.json` | [docs](docs/ML/conformal_prediction.md) | 🏁 |

## Docs

| Файл | Назначение |
|------|------------|
| [DATA_FLOW.md](docs/DATA_FLOW.md) | Поток данных + навигация по этапам |
| [dataset_description.md](docs/dataset_description.md) | Описание структуры датасета Nero.csv |
| [PRD.md](docs/PRD.md) | Product Requirements Document |
| [label_main.py.md](docs/processing/label_main.py.md) | Документация оркестратора |
| [label_signals.py.md](docs/processing/label_signals.py.md) | Логика маркировки signal/predict |
| [normalize.py.md](docs/processing/normalize.py.md) | Методы нормализации признаков |
| [statistics.py.md](docs/statistics/statistics.py.md) | Справка по потоковой статистике |
| [EDA.ipynb.md](docs/statistics/EDA.ipynb.md) | Отчет по разведочному анализу |
| [signal_tracer.py.md](docs/statistics/signal_tracer.py.md) | Trade-level reconciliation: диагностика Python PF vs MT4 PF |
| [neural_networks.md](docs/ML/neural_networks.md) | ML pipeline: архитектуры, обучение, метрики |
| [conformal_prediction.md](docs/ML/conformal_prediction.md) | Conformal Prediction: реализация, результаты, выводы |
| [walkthrough.md](docs/ML/walkthrough.md) | Multi-target regression & OOS evaluation walkthrough |
| [lib_PIC.mqh.md](docs/MT/lib_PIC.mqh.md) | Описание библиотеки PIC |
| [ml_signal_integration.md](docs/MT/ml_signal_integration.md) | Архитектура ML ↔ MT4 (файловый обмен) |
| [trading_strategy.md](docs/MT/trading_strategy.md) | Полный алгоритм торгового эксперта MAIN() |

## Легенда статусов
✅ Активный | 🚧 В разработке | 🏁 Завершён | 📦 Архив | ⚠️ Требует внимания

---
**Последнее обновление**: 2026-03-26
