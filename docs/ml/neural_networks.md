# Neural Networks Pipeline

## Назначение
Обучение и сравнение 4 архитектур нейронных сетей для решения двух задач:
1. **Классификация** (`--task classification`): `signal ∈ {-1, 0, 1}` (направление и сила движения)
2. **Регрессия** (`--task regression`): `predict ∈ [-p..p]` (непрерывная нормализованная величина ожидаемого движения цены).
Фреймворк: PyTorch.

## Структура модулей

```
ML/
├── baseline/                 # Baseline-модели (Dummy, LogReg, RF, XGB, LGBM)
├── data_loader.py            # Dataset и DataLoader для фрактальных последовательностей
├── models/
│   ├── __init__.py           # Реестр моделей + get_model()
│   ├── bilstm.py             # Bi-LSTM (147K параметров)
│   ├── cnn1d.py              # 1D-CNN (42K параметров)
│   ├── transformer.py        # Transformer Encoder (70K параметров)
│   └── hybrid_cnn_lstm.py    # Hybrid CNN+LSTM (83K параметров)
├── train.py                  # Единый скрипт обучения (CLI: --model arg)
├── losses.py                 # Focal Loss
├── utils.py                  # Seed, метрики, подсчёт параметров
├── compare_architectures.py  # Скрипт сравнения всех моделей
├── checkpoints/              # Веса лучших моделей (*_best.pt или *_regression_best.pt)
├── plots/                    # Training curves, confusion matrices, residuals
└── reports/
    └── architecture_comparison.md
```

## Входные данные
- **Файл**: `DATA/Nero_train_labeled.csv`, `DATA/Nero_validation_labeled.csv`
- **Формат**: CSV (`;`), 100 фракталов × 11 полей через `:`
- **Источник**: `processing/label_main.py`

## Выходные данные
- **Файл**: `ML/checkpoints/<model>_best.pt` или `ML/checkpoints/<model>_regression_best.pt` (веса лучшей модели)
- **Файл**: `ML/checkpoints/<model>_result.json` или `<model>_regression_result.json` (лучшие метрики)
- **Файл**: `ML/plots/training_curves_*.png`
- **Файл**: `ML/plots/cm_*.png` (для классификации) или `ML/plots/regression_*.png` (для регрессии)

## Использование

### Сравнение всех архитектур (`compare_architectures.py`)
Запускает последовательное обучение всех 4 моделей и генерирует сводный отчет.
```bash
# Массовое обучение для классификации
python ML/compare_architectures.py --task classification

# Массовое обучение для регрессии
python ML/compare_architectures.py --task regression
```

### Обучение конкретной модели (`train.py`)
```bash
# Классификация
python ML/train.py --model bilstm --task classification

# Регрессия с кастомными параметрами
python ML/train.py --model cnn1d --task regression --epochs 30 --batch_size 512
```

### Аргументы командной строки
Для обоих скриптов доступны следующие основные аргументы:

| Аргумент | Описание | Значение по умолчанию |
|----------|----------|-----------------------|
| `--task` | Тип задачи: `classification` или `regression` | `classification` (в `train.py`) |
| `--model`| Архитектура модели (только для `train.py`) | **обязательный** |
| `--use_scaler` | Включить математический `StandardScaler` | `False` (выключено) |
| `--batch_size` | Размер батча | `256` |
| `--epochs` | Лимит эпох обучения | `50` |
| `--lr` | Скорость обучения (Learning Rate) | `1e-3` |
| `--patience` | Patience для раннего останова | `10` |
| `--seed` | Random Seed | `42` |

## Data Pipeline

### 1. Парсинг (`data_loader.py`)
CSV → 3D тензор `(n_samples, 100, 11)`:
- 10 фрактальных features: price, direction, front, back, strong, break, reverse, power, count, impulse
- `fractal_time` **исключён** — data leakage через абсолютное время
- ATR broadcast как 11-й признак
- Padding mask для NaN-позиций

### 2. Нормализация (`data_loader.py`)
- StandardScaler: математическая нормализация (Z-score). **По умолчанию выключена** (флаг `--use_scaler`), так как достаточно предметной нормализации в `normalize.py`.
- Обязательна (при включении): приводит разные масштабы признаков к среднему 0 и std 1.

### 3. Маппинг меток
`{-1, 0, 1}` → `{0, 1, 2}` для PyTorch

## Архитектуры

| Модель | Вход | Ключевая идея | Параметры |
|--------|------|---------------|-----------|
| **Bi-LSTM** | (batch, 100, 11) | Временные зависимости в обоих направлениях, concat pooling | 147,203 |
| **1D-CNN** | (batch, 100, 11)→транспоз | Локальные паттерны между соседними фракталами, GAP | 41,603 |
| **Transformer** | (batch, 100, 11) | Self-attention + CLS token + padding mask | 69,955 |
| **Hybrid CNN+LSTM** | (batch, 100, 11)→транспоз | CNN (локальные) → Bi-LSTM (глобальные) | 83,203 |

Все модели возвращают тензор `(batch, num_classes)`.
- Для классификации: `num_classes=3`.
- Для регрессии: `num_classes=1`, тензор сжимается до размера `(batch,)`.

## Обучение (`train.py`)

| Параметр | Значение | Обоснование |
|----------|----------|-------------|
| Loss | Focal Loss (γ=2, α=[0.45, 0.10, 0.45]) или HuberLoss (δ=1.0) | Focal Loss для несбалансированной классификации; Huber Loss для устойчивой к выбросам регрессии |
| Optimizer | AdamW (lr=1e-3, wd=1e-4) | Стандарт для трансформеров и LSTM |
| Scheduler | ReduceLROnPlateau (patience=5, factor=0.5) | Мониторит основную метрику (max) |
| Early stopping | patience=10 на F1 или pearson_r | Classification: val macro F1; Regression: pearson_r correlation. **НЕ по val_loss** |
| Batch size | 256 | Оптимально при 43K сэмплах |
| Seed | 42 | torch, numpy, random, cudnn deterministic |

## Метрики
### Задача классификации
- **Основная**: `macro F1-score` (early stopping + выбор лучшей модели)
- **Дополнительные**: `Per-class F1` (особенно для minority-классов -1 и 1), Precision, Recall
- **Графики**: Confusion matrix, Training curves (loss + F1)

### Задача регрессии
- **Основная**: Коэффициент корреляции Пирсона `pearson_r` (early stopping + выбор лучшей модели)
- **Дополнительные**: `MAE`, `RMSE`, `R²`, `Directional Accuracy` (Доля правильных предсказаний знака таргета)
- **Графики**: Scatter (y_true / y_pred), Резидуалы, Training curves (loss + Pearson r + MAE)

## Примечания
- `fractal_time` исключён из features — его смысл уже отражён порядком позиций
- Focal Loss: alpha=[0.45, 0.10, 0.45] = больший вес minority-классам (-1 и 1)
- Маппинг alpha: индекс 0→class -1, индекс 1→class 0, индекс 2→class 1
- Gradient clipping (max_norm=1.0) для стабильности LSTM/Transformer
