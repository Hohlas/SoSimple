# Neural Networks Pipeline

> **Обновлено**: 2026-04-09 — `regression_updn` описан в текущем виде: 10 Up/Dn таргетов на горизонтах 3, 6, 12, 24, 48.

## Назначение
Обучение и сравнение 4 архитектур нейронных сетей для решения трёх задач:
1. **Классификация** (`--task classification`): `signal ∈ {-1, 0, 1}` (направление и сила движения)
2. **Регрессия** (`--task regression`): `predict ∈ [-p..p]` (непрерывная нормализованная величина ожидаемого движения цены)
3. **Multi-task регрессия** (`--task regression_updn`): 10 таргетов (`up_3`, `dn_3`, `up_6`, `dn_6`, `up_12`, `dn_12`, `up_24`, `dn_24`, `up_48`, `dn_48`) — движение цены вверх/вниз на 5 горизонтах. Торговый сигнал в legacy-контуре строится из отношения `pred_up / pred_dn`.
Фреймворк: PyTorch.

### ⚠️ Важно: Ловушка дисбаланса классов

В датасете наблюдается сильный дисбаланс: **neutral (0) ≈ 95%**, **сигналы (-1, 1) ≈ 5%**.

При использовании стандартной метрики `macro F1` модель может показывать "хороший" результат (~0.57), фактически не умея предсказывать сигналы:
- F1(0) ≈ 0.95 (отлично — majority класс)
- F1(-1) и F1(1) ≈ 0.35 (плохо — торгово-значимые классы)
- Precision сигналов: 0.25–0.30 → **70-75% ложных торговых сигналов**

**Решение**: Используйте `--metric_mode f1_minority` или `--metric_mode signal_precision` для честной оценки качества сигналов.

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
├── optimize.py               # Оптимизация гиперпараметров с Optuna
├── losses.py                 # Focal Loss
├── utils.py                  # Seed, метрики, подсчёт параметров
├── compare_architectures.py  # Скрипт сравнения всех моделей
├── evaluate_test.py          # OOS оценка обученной модели на тестовой выборке
├── checkpoints/              # Веса моделей (.pt) и метрики (.json)
├── plots/                    # Training curves, confusion matrices, residuals
└── reports/
    ├── architecture_comparison.md
    ├── threshold_analysis_*.md # Отчеты по подбору порогов для торговых сигналов
    ├── evaluate_test_*.md      # Отчеты по тестированию Out-of-Sample
    └── optuna_*.json         # Отчёты оптимизации гиперпараметров
```

## Входные данные
- **Файл**: `DATA/Nero_train_labeled.csv`, `DATA/Nero_validation_labeled.csv`
- **Формат**: CSV (`;`), 100 фракталов × 18 полей через `:`
- **Источник**: `processing/label_main.py`

## Выходные данные
- **Файл**: `ML/checkpoints/<model>_best.pt` или `<model>_regression_best.pt` или `<model>_updn_best.pt`
- **Файл**: `ML/checkpoints/<model>_result.json`
- **Файл**: `ML/plots/training_curves_*.png`
- **Файл**: `ML/plots/cm_*.png` (классификация), `ML/plots/regression_*.png` (регрессия), `ML/plots/regression_*_updn.png` (multi-target)

## Ключевые отчеты по торговым сигналам
После обучения модели `regression_updn` формируются следующие отчеты в каталоге `ML/reports/`:
- `threshold_analysis_12H.md` (а также `24H` и `48H`): Результаты подбора оптимального торгового порога `θ` на валидации.
- `evaluate_test_H12.md`: Окончательный результат симуляции торговли на отложенных данных (Test).
- [walkthrough.md](../archive/03.10_audit_answers/walkthrough.md): Сводная документация по OOS-тестированию и достигнутому Profit Factor.

## Использование

### Сравнение всех архитектур (`compare_architectures.py`)
Запускает последовательное обучение всех 4 моделей и генерирует сводный отчет.
```bash
# Массовое обучение для классификации
python -m ML.compare_architectures --task classification

# Массовое обучение для регрессии (старый predict таргет)
python -m ML.compare_architectures --task regression

# Массовое обучение multi-task regression (10 Up/Dn таргетов)
python -m ML.compare_architectures --task regression_updn
```

### Обучение конкретной модели (`train.py`)
```bash
# Классификация с дефолтным F1 macro
python -m ML.train --model bilstm --task classification

# Регрессия с кастомными параметрами
python -m ML.train --model cnn1d --task regression --epochs 30 --batch_size 512

# Multi-task regression (10 Up/Dn таргетов)
python -m ML.train --model transformer --task regression_updn --epochs 50

# Классификация с оптимизированными параметрами (из Optuna)
python -m ML.train --model cnn1d --task classification \
  --lr 0.004012 --batch_size 64 --patience 7 \
  --weight_decay 6.95e-6 --scheduler_patience 4 --scheduler_factor 0.42 \
  --focal_gamma 1.74 --focal_minority_weight 0.445 \
  --epochs 100 --seed 123

# Классификация, ориентированная на precision сигналов с ограничением на recall
python -m ML.train --model cnn1d --task classification \
  --metric_mode signal_precision --min_signal_recall 0.3 \
  --use_weighted_sampler --epochs 50 --seed 42

# Классификация со средним F1 для minority классов (-1 и 1)
python -m ML.train --model transformer --task classification \
  --metric_mode f1_minority --use_weighted_sampler --epochs 50 --seed 42
```

### Аргументы командной строки
Для обоих скриптов доступны следующие основные аргументы:

| Аргумент | Описание | Значение по умолчанию |
|----------|----------|-----------------------|
| `--task` | Тип задачи: `classification`, `regression` или `regression_updn` | `classification` (в `train.py`) |
| `--model`| Архитектура модели (только для `train.py`) | **обязательный** |
| `--use_scaler` | Включить математический `StandardScaler` | `False` (выключено) |
| `--batch_size` | Размер батча | `256` |
| `--epochs` | Лимит эпох обучения | `50` |
| `--lr` | Скорость обучения (Learning Rate) | `1e-3` |
| `--weight_decay` | L2 регуляризация (AdamW) | `1e-4` |
| `--patience` | Patience для раннего останова | `10` |
| `--scheduler_patience` | Patience для ReduceLROnPlateau | `5` |
| `--scheduler_factor` | Factor уменьшения LR | `0.5` |
| `--focal_gamma` | Gamma параметр Focal Loss (classification) | `2.0` |
| `--focal_minority_weight` | Вес классов -1 и 1 для Focal Loss | `0.495` |
| `--seed` | Random Seed | `42` |
| `--metric_mode` | Целевая метрика для early stopping (classification): `f1_macro`, `f1_minority`, `signal_precision` | `f1_macro` |
| `--min_signal_recall` | Минимальный recall для сигнальных классов (-1 и 1), используется только при `--metric_mode=signal_precision` | `0.3` |
| `--regression_loss` | Функция потерь для регрессии: `huber` или `asymmetric` | `huber` |
| `--asym_over_penalty` | Штраф за перепрогноз (over-prediction) в `asymmetric` | `1.0` |
| `--asym_under_penalty` | Штраф за недопрогноз (under-prediction) в `asymmetric` | `10.0` |
| `--use_weighted_sampler` | Использовать WeightedRandomSampler для балансировки train-батчей (классификация только) | `False` (выключено) |

**Примечание:** Для Focal Loss веса классов вычисляются как:
- alpha[-1] = focal_minority_weight
- alpha[0] = 1 - 2 * focal_minority_weight
- alpha[1] = focal_minority_weight

## Data Pipeline

### 1. Парсинг (`data_loader.py`)
CSV → 3D тензор `(n_samples, 100, 20)`:
- 17 фрактальных features из CSV (fields 1-17): price, direction, front, back, strong, break, reverse, power, count, impulse, up_12, dn_12, up_24, dn_24, up_48, dn_48, ATR_ratio
- `fractal_time` (field 0) — исключён как сырое, но используется для вычисления time-фич
- `fractal_atr` (field 17) → `log(ATR_ratio)` = log(fractal_atr / ATR_raw)
- 3 вычисляемые time-фичи: `hour_sin`, `hour_cos` (sin/cos часа суток), `time_pos` (позиция на оси строки [0..1])
- Padding mask для NaN-позиций

### 2. Нормализация (`data_loader.py`)
- StandardScaler: математическая нормализация (Z-score). **По умолчанию выключена** (флаг `--use_scaler`), так как достаточно предметной нормализации в `normalize.py`.
- Обязательна (при включении): приводит разные масштабы признаков к среднему 0 и std 1.

### 3. Маппинг меток
`{-1, 0, 1}` → `{0, 1, 2}` для PyTorch

## Архитектуры

| Модель | Вход | Ключевая идея | Параметры |
|--------|------|---------------|-----------|
| **Bi-LSTM** | (batch, 100, 20) | Временные зависимости в обоих направлениях, concat pooling | ~150K |
| **1D-CNN** | (batch, 100, 20)→транспоз | Локальные паттерны между соседними фракталами, GAP | ~44K |
| **Transformer** | (batch, 100, 20) | Self-attention + CLS token + padding mask | ~72K |
| **Hybrid CNN+LSTM** | (batch, 100, 20)→транспоз | CNN (локальные) → Bi-LSTM (глобальные) | ~86K |

Все модели возвращают тензор `(batch, num_classes)`.
- Для классификации: `num_classes=3`.
- Для регрессии: `num_classes=1`, тензор сжимается до размера `(batch,)`.

## Обучение (`train.py`)

| Параметр | Значение | Обоснование |
|----------|----------|-------------|
| Loss | Focal Loss (γ=2, α=[0.45, 0.10, 0.45]) или HuberLoss (δ=1.0) / AsymmetricLoss | Focal Loss для несбалансированной классификации; Huber/Asymmetric для устойчивой или направленной регрессии |
| Optimizer | AdamW (lr=1e-3, wd=1e-4) | Стандарт для трансформеров и LSTM |
| Scheduler | ReduceLROnPlateau (patience=5, factor=0.5) | Мониторит основную метрику (max) |
| Early stopping | patience=10 на F1 или pearson_r | Classification: val macro F1; Regression: pearson_r correlation. **НЕ по val_loss** |
| Batch size | 256 | Оптимально при 43K сэмплах |
| Seed | 42 | torch, numpy, random, cudnn deterministic |
| Device | CUDA | Автоопределение через `torch.cuda.is_available()` |

## Оптимизация гиперпараметров (`optimize.py`)

Автоматический подбор гиперпараметров с использованием фреймворка [Optuna](https://optuna.org/).
Поддерживает early stopping (pruning) для экономии времени на неперспективных trials.

### Пространство поиска гиперпараметров

| Параметр | Диапазон | Описание | Применимость |
|----------|----------|----------|--------------|
| `lr` | [1e-5, 1e-2] log | Learning rate | Все задачи |
| `batch_size` | {64, 128, 256, 512} | Размер батча | Все задачи |
| `patience` | [3, 10] | Early stopping patience | Все задачи |
| `weight_decay` | [1e-6, 1e-3] log | L2 регуляризация | Все задачи |
| `scheduler_patience` | [3, 7] | Patience для ReduceLROnPlateau | Все задачи |
| `scheduler_factor` | [0.3, 0.7] | Factor уменьшения LR | Все задачи |
| `focal_gamma` | [1.0, 3.0] | Фокусирующий параметр Focal Loss | Только classification |
| `focal_minority_weight` | [0.2, 0.7] | Вес классов -1 и 1 | Только classification |
| `huber_delta` | [0.5, 2.0] | Параметр δ для Huber Loss | Только regression |
| `asym_under_penalty` | [1.0, 20.0] | Штраф за FN (недопрогноз) | Только regression |

### Примеры команд запуска

```bash
# Базовая оптимизация CNN1D для классификации (50 trials)
python -m ML.optimize --model cnn1d --task classification --trials 50

# Оптимизация с увеличенным числом эпох и кастомным seed
python -m ML.optimize --model cnn1d --task classification --trials 50 --epochs 50 --seed 123

# Оптимизация Bi-LSTM для регрессии
python -m ML.optimize --model bilstm --task regression --trials 30 --epochs 40

# Быстрая оптимизация для тестирования
python -m ML.optimize --model transformer --task classification --trials 10 --epochs 20

# Оптимизация под f1_minority (рекомендуется для дисбаланса)
python -m ML.optimize --model cnn1d --task classification --trials 50 \
  --metric_mode f1_minority --use_weighted_sampler

# Оптимизация под signal_precision с порогом recall
python -m ML.optimize --model cnn1d --task classification --trials 50 \
  --metric_mode signal_precision --min_signal_recall 0.3 --use_weighted_sampler
```

### Аргументы командной строки

| Аргумент | Описание | Значение по умолчанию |
|----------|----------|-----------------------|
| `--model` | Архитектура модели (cnn1d, bilstm, transformer, hybrid) | **обязательный** |
| `--task` | Задача: `classification` или `regression` | `classification` |
| `--trials` | Количество Optuna trials | `50` |
| `--epochs` | Максимум эпох на один trial | `30` |
| `--seed` | Random seed для воспроизводимости | `42` |
| `--metric_mode` | Целевая метрика (f1_macro, f1_minority, signal_precision) | `f1_macro` |
| `--min_signal_recall` | Минимальный recall для signal_precision mode | `0.3` |
| `--use_weighted_sampler` | Использовать WeightedRandomSampler (классификация) | `False` |

### Форматы выходных файлов

Оптимизация создаёт два типа отчётов в `ML/reports/`:

#### 1. `optuna_best_params_<model>_<task>.json`
Содержит только лучшие найденные параметры:
```json
{
  "model": "cnn1d",
  "task": "classification",
  "best_value": 0.5714740408592095,
  "best_params": {
    "lr": 0.004012297247120644,
    "batch_size": 64,
    "patience": 7,
    "weight_decay": 6.948873436259482e-06,
    "scheduler_patience": 4,
    "scheduler_factor": 0.4198421272800256,
    "focal_minority_weight": 0.44496228644304736,
    "focal_gamma": 1.7416605655953168
  },
  "best_trial": 47,
  "n_trials": 50,
  "timestamp": "20260226_134119"
}
```

#### 2. `optuna_study_<model>_<task>_<timestamp>.json`
Полная история всех trials с параметрами, метриками и временем выполнения:
```json
{
  "study_name": "cnn1d_classification",
  "direction": "MAXIMIZE",
  "best_trial": 47,
  "best_value": 0.5714740408592095,
  "best_params": { ... },
  "trials": [
    {
      "number": 0,
      "value": 0.5511695473555203,
      "params": { ... },
      "state": "TrialState.COMPLETE",
      "datetime_start": "2026-02-26 12:19:35.217733",
      "datetime_complete": "2026-02-26 12:22:38.129134",
      "duration": "0:03:02.911401"
    }
  ]
}
```

Состояния trial:
- `COMPLETE` — успешно завершён
- `PRUNED` — остановлен early (неперспективная конфигурация)
- `FAIL` — произошла ошибка

## Метрики
### Задача классификации

#### Режимы целевой метрики (`--metric_mode`)

При дисбалансе классов (95% neutral, 5% сигналы) стандартная метрика `macro F1` может быть обманчивой — высокое значение достигается за счёт отличного предсказания neutral класса, в то время как качество сигналов (-1 и 1) остаётся низким.

| Режим | Формула | Когда использовать |
|-------|---------|-------------------|
| `f1_macro` | (F1(-1) + F1(0) + F1(1)) / 3 | Базовый режим, когда все классы равнозначны |
| `f1_minority` | (F1(-1) + F1(1)) / 2 | **Рекомендуется** — фокус на торговых сигналах с балансом precision/recall |
| `signal_precision` | (Precision(-1) + Precision(1)) / 2 | Когда критично минимизировать ложные сигналы (штраф за recall < min_signal_recall) |

#### Дополнительные метрики сигналов

Все метрики доступны в выводе и логах:

| Метрика | Описание | Интерпретация для торговли |
|---------|----------|---------------------------|
| `signal_precision` | Средний precision классов -1 и 1 | Доля правильных сигналов (выше = меньше ложных входов) |
| `signal_recall` | Средний recall классов -1 и 1 | Процент найденных реальных сигналов (выше = меньше пропущенных возможностей) |
| `f1_minority` | Средний F1 классов -1 и 1 | Баланс precision/recall для сигналов |
| `precision_neg` / `precision_pos` | Precision отдельно для Sell/Buy | Контроль качества каждого направления |
| `recall_neg` / `recall_pos` | Recall отдельно для Sell/Buy | Полнота покрытия каждого направления |

#### Графики
- Confusion matrix — визуализация ошибок по классам
- Training curves — loss + выбранная целевая метрика

### WeightedRandomSampler (`--use_weighted_sampler`)

При включении создаёт сбалансированные батчи для обучения:
- Вес каждого примера = 1 / частота_класса
- minority классы (-1, 1) попадают в батчи чаще
- Только для train; validation/test сохраняют реальное распределение
- Помогает модели лучше учиться на сигнальных классах

**Примечание**: sampler работает только для классификации, для регрессии игнорируется.

### Задача регрессии
- **Основная**: Коэффициент корреляции Пирсона `pearson_r` (early stopping + выбор лучшей модели)
- **Дополнительные**: `MAE`, `RMSE`, `R²`, `Directional Accuracy` (Доля правильных предсказаний знака таргета)
- **Графики**: Scatter (y_true / y_pred), Резидуалы, Training curves (loss + Pearson r + MAE)

## Содержимое каталога `ML/checkpoints/`

Каталог `ML/checkpoints/` хранит артефакты обучения моделей:

### Файлы весов (`.pt`)
Сохранённые state_dict моделей PyTorch, загружаемые через `torch.load()`:

| Файл | Описание |
|------|----------|
| `<model>_best.pt` | Лучшая модель для классификации (по выбранной метрике: f1_macro / f1_minority / signal_precision) |
| `<model>_regression_best.pt` | Лучшая модель для регрессии (по pearson_r) |

Где `<model>` ∈ {`bilstm`, `cnn1d`, `transformer`, `hybrid`}

### Файлы метрик (`.json`)
Результаты обучения в JSON-формате:

| Файл | Описание |
|------|----------|
| `<model>_result.json` | Метрики классификации |
| `<model>_regression_result.json` | Метрики регрессии |

Пример содержимого `cnn1d_result.json`:
```json
{
  "model": "cnn1d",
  "task": "classification",
  "best_metric": 0.5698,
  "best_epoch": 24,
  "train_loss": 0.8234,
  "val_loss": 0.9123
}
```

### Структура каталога
```
ML/checkpoints/
├── bilstm_best.pt                    # Bi-LSTM classification
├── bilstm_regression_best.pt         # Bi-LSTM regression
├── bilstm_result.json
├── bilstm_regression_result.json
├── cnn1d_best.pt                     # 1D-CNN classification
├── cnn1d_regression_best.pt          # 1D-CNN regression
├── cnn1d_result.json
├── cnn1d_regression_result.json
├── transformer_best.pt               # Transformer classification
├── transformer_regression_best.pt    # Transformer regression
├── transformer_result.json
├── transformer_regression_result.json
├── hybrid_best.pt                    # Hybrid CNN+LSTM classification
├── hybrid_regression_best.pt         # Hybrid CNN+LSTM regression
├── hybrid_result.json
└── hybrid_regression_result.json
```

## Примечания
- `fractal_time` не подаётся как сырое абсолютное время — вместо него вычисляются `hour_sin`, `hour_cos`, `time_pos`
- Focal Loss: alpha=[0.45, 0.10, 0.45] = больший вес minority-классам (-1 и 1)
- Маппинг alpha: индекс 0→class -1, индекс 1→class 0, индекс 2→class 1
- Gradient clipping (max_norm=1.0) для стабильности LSTM/Transformer
