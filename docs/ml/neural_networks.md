# Neural Networks Pipeline

## Назначение
Обучение и сравнение 4 архитектур нейронных сетей для классификации `signal ∈ {-1, 0, 1}` на последовательностях фракталов. Фреймворк: PyTorch.

## Структура модулей

```
ML/
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
├── checkpoints/              # Веса лучших моделей
├── plots/                    # Training curves, confusion matrices
└── reports/
    └── architecture_comparison.md
```

## Входные данные
- **Файл**: `DATA/Nero_train_labeled.csv`, `DATA/Nero_validation_labeled.csv`
- **Формат**: CSV (`;`), 100 фракталов × 11 полей через `:`
- **Источник**: `processing/label_main.py`

## Выходные данные
- **Файл**: `ML/checkpoints/<model>_best.pt` (веса лучшей модели)
- **Файл**: `ML/reports/architecture_comparison.md` (сводный отчёт)
- **Файл**: `ML/plots/training_curves_*.png`, `ML/plots/cm_*.png`

## Использование

```bash
# Обучение одной модели:
python ML/train.py --model bilstm
python ML/train.py --model cnn1d --epochs 30 --batch_size 512
python ML/train.py --model transformer
python ML/train.py --model hybrid

# Сравнение всех архитектур:
python ML/compare_architectures.py
```

## Data Pipeline

### 1. Парсинг (`data_loader.py`)
CSV → 3D тензор `(n_samples, 100, 11)`:
- 10 фрактальных features: price, direction, front, back, strong, break, reverse, power, count, impulse
- `fractal_time` **исключён** — data leakage через абсолютное время
- ATR broadcast как 11-й признак
- Padding mask для NaN-позиций

### 2. Нормализация (`data_loader.py`)
- StandardScaler: **fit на train** (flatten `n_samples*100 × 11`), transform на val
- Обязательна: разные масштабы — price ~1.0, front/impulse ~0.001-0.01, power/count — целые числа

### 3. Маппинг меток
`{-1, 0, 1}` → `{0, 1, 2}` для PyTorch

## Архитектуры

| Модель | Вход | Ключевая идея | Параметры |
|--------|------|---------------|-----------|
| **Bi-LSTM** | (batch, 100, 11) | Временные зависимости в обоих направлениях, concat pooling | 147,203 |
| **1D-CNN** | (batch, 100, 11)→транспоз | Локальные паттерны между соседними фракталами, GAP | 41,603 |
| **Transformer** | (batch, 100, 11) | Self-attention + CLS token + padding mask | 69,955 |
| **Hybrid CNN+LSTM** | (batch, 100, 11)→транспоз | CNN (локальные) → Bi-LSTM (глобальные) | 83,203 |

Все модели: `forward(x, mask=None) → logits (batch, 3)`

## Обучение (`train.py`)

| Параметр | Значение | Обоснование |
|----------|----------|-------------|
| Loss | Focal Loss (γ=2, α=[0.45, 0.10, 0.45]) | Дисбаланс 95%/2.5%/2.5%; CrossEntropy недостаточен |
| Optimizer | AdamW (lr=1e-3, wd=1e-4) | Стандарт для трансформеров и LSTM |
| Scheduler | ReduceLROnPlateau (patience=5, factor=0.5) | Мониторит val macro F1 |
| Early stopping | patience=10 на val macro F1 | **НЕ на loss** — loss может улучшаться за счёт majority |
| Batch size | 256 | Оптимально при 43K сэмплах |
| Seed | 42 | torch, numpy, random, cudnn deterministic |

## Метрики
- **Основная**: macro F1-score (early stopping + выбор лучшей модели)
- **Per-class F1**: особенно для minority-классов -1 и 1
- **Confusion matrix**: best epoch
- **Training curves**: loss и F1 по эпохам

## Примечания
- `fractal_time` исключён из features — его смысл уже отражён порядком позиций
- Focal Loss: alpha=[0.45, 0.10, 0.45] = больший вес minority-классам (-1 и 1)
- Маппинг alpha: индекс 0→class -1, индекс 1→class 0, индекс 2→class 1
- Gradient clipping (max_norm=1.0) для стабильности LSTM/Transformer
