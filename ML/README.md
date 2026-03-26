# ML/

Обучение, оптимизация и оценка нейросетевых моделей для прогнозирования Up/Dn.

Подробная документация: [docs/ML/](../docs/ML/)

## Архитектура зависимостей

```
Слой 1 (Core)        losses.py, utils.py, data_loader.py, experiment_logger.py
Слой 2 (Models)      models/ (bilstm, cnn1d, transformer, hybrid_cnn_lstm)
Слой 3 (Training)    train.py → optimize.py
Слой 4 (Evaluation)  evaluate_test.py, threshold_analysis.py, compare_architectures.py
Отдельные модули     baseline/, conformal/, reproducibility_tests.py
```

## Скрипты

### Core (библиотека — импортируется остальными)

| Файл | Назначение | Статус |
|------|-----------|--------|
| [data_loader.py](data_loader.py) | Dataset/DataLoader: CSV → 3D тензор (N, 100, 20) | ✅ |
| [losses.py](losses.py) | FocalLoss, HuberLoss, AsymmetricLoss | ✅ |
| [utils.py](utils.py) | seed, метрики (Pearson r, MAE, R²), device | ✅ |
| [experiment_logger.py](experiment_logger.py) | CSV-логгер экспериментов | 🏁 |

### Models

| Файл | Архитектура | Статус |
|------|-----------|--------|
| [models/transformer.py](models/transformer.py) | Transformer Encoder (лучшая) | ✅ |
| [models/bilstm.py](models/bilstm.py) | Bi-LSTM | 🏁 |
| [models/cnn1d.py](models/cnn1d.py) | 1D-CNN | 🏁 |
| [models/hybrid_cnn_lstm.py](models/hybrid_cnn_lstm.py) | Hybrid CNN+LSTM | 🏁 |

### Training

| Файл | Назначение | Вход → Выход | Статус |
|------|-----------|--------------|--------|
| [train.py](train.py) | Обучение (--task regression_updn / triple_barrier) | DataLoader → checkpoints/, plots/ | ✅ |
| [optimize.py](optimize.py) | Optuna оптимизация гиперпараметров | DataLoader → reports/optuna_*.json | 🏁 |

### Evaluation

| Файл | Назначение | Вход → Выход | Статус |
|------|-----------|--------------|--------|
| [evaluate_test.py](evaluate_test.py) | OOS оценка на тестовой выборке | checkpoint + test CSV → reports/ | ✅ |
| [threshold_analysis.py](threshold_analysis.py) | Поиск оптимального θ для торговых сигналов | checkpoint + val CSV → reports/ | ✅ |
| [compare_architectures.py](compare_architectures.py) | Сравнение 4 архитектур | DataLoader → reports/ | 🏁 |
| [reproducibility_tests.py](reproducibility_tests.py) | Тесты детерминизма seed | — → reports/ | 🏁 |

### Отдельные эксперименты

| Каталог | Назначение | Статус |
|---------|-----------|--------|
| [baseline/](baseline/) | Baseline-модели: XGBoost, LightGBM, RandomForest, SVM, LogReg | 🏁 |
| [conformal/](conformal/) | Split Conformal Prediction калибровка | 🏁 |

> Легенда: ✅ Активный | 🚧 В разработке | 🏁 Завершён | 📦 Архив | ⚠️ Требует внимания

## Артефакты (генерируемые файлы)

| Каталог | Содержимое |
|---------|-----------|
| `checkpoints/` | Веса моделей (.pt) и параметры Optuna (.json) |
| `plots/` | Кривые обучения, scatter-графики |
| `reports/` | Отчёты экспериментов (.md, .json) |

## Команды

```bash
source ~/git/SoSimple/.venv/bin/activate

# Обучение transformer (regression_updn)
python -m ML.train --model transformer --task regression_updn --epochs 100

# Optuna оптимизация
python -m ML.optimize --model transformer --task regression_updn --trials 50 --epochs 30 --seed 42

# Сравнение 4 архитектур
python -m ML.compare_architectures --task regression_updn

# OOS оценка
python -m ML.evaluate_test --task regression_updn --model transformer

# Threshold analysis
python -m ML.threshold_analysis --task regression_updn --horizon 12

# Triple Barrier (transfer learning обязателен!)
python -m ML.train --model transformer --task triple_barrier --epochs 100 --patience 20 \
  --encoder_ckpt ML/checkpoints/transformer_updn_best.pt
```
