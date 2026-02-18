# =============================================================================
# Файл: train.py
# Назначение: Единый скрипт обучения нейросетевых моделей
# Язык: Python 3.11+
# Обновлён: 2026-02-18
# Зависимости:
#   Входные данные:
#     - DATA/Nero_train_labeled.csv (откуда: processing/label_main.py)
#     - DATA/Nero_validation_labeled.csv (откуда: processing/label_main.py)
#   Выходные данные:
#     - ML/checkpoints/<model>_best.pt (веса лучшей модели по val F1)
#     - ML/plots/training_curves_<model>.png (кривые обучения)
#     - ML/plots/cm_<model>.png (confusion matrix лучшей эпохи)
# Внешние зависимости:
#   - torch>=2.0
#   - numpy>=1.24
#   - pandas>=2.0
#   - scikit-learn>=1.2
#   - matplotlib>=3.7
#   - seaborn>=0.12
# Использование:
#   python ML/train.py --model bilstm
#   python ML/train.py --model cnn1d --epochs 30 --batch_size 512
#   python ML/train.py --model transformer
#   python ML/train.py --model hybrid
# Примечания:
#   - Early stopping на val macro F1 (НЕ на loss!)
#   - Focal Loss с alpha=[0.45, 0.10, 0.45]
#   - Scheduler: ReduceLROnPlateau на val F1
# =============================================================================

"""
Единый скрипт обучения для всех нейросетевых архитектур.

Принимает --model аргумент и запускает обучение выбранной модели
с единообразными условиями: Focal Loss, AdamW, ReduceLROnPlateau,
early stopping на macro F1.
"""

import argparse
import json
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

from ML.data_loader import create_data_loaders, INV_LABEL_MAP
from ML.losses import FocalLoss
from ML.models import get_model, MODEL_REGISTRY
from ML.utils import set_seed, compute_metrics, count_parameters, get_device


# ─── Пути ────────────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ML_DIR = PROJECT_ROOT / 'ML'
CHECKPOINTS_DIR = ML_DIR / 'checkpoints'
PLOTS_DIR = ML_DIR / 'plots'

# ─── Значения по умолчанию ───────────────────────────────────────────────────

DEFAULTS = {
    'epochs': 50,
    'batch_size': 256,
    'lr': 1e-3,
    'weight_decay': 1e-4,
    'patience': 10,        # Early stopping patience
    'scheduler_patience': 5,
    'scheduler_factor': 0.5,
    'gamma': 2.0,          # Focal Loss gamma
    'alpha': [0.45, 0.10, 0.45],  # Focal Loss class weights
    'seed': 42,
}


# ═══════════════════════════════════════════════════════════════════════════════
# ОБУЧЕНИЕ
# ═══════════════════════════════════════════════════════════════════════════════

def train_one_epoch(
    model: nn.Module,
    train_loader: torch.utils.data.DataLoader,
    loss_fn: nn.Module,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
) -> float:
    """
    Обучение одной эпохи.

    Аргументы:
        model: Модель для обучения
        train_loader: DataLoader с train данными
        loss_fn: Функция потерь (FocalLoss)
        optimizer: Оптимизатор (AdamW)
        device: Устройство (cuda/cpu)

    Возвращает:
        Средний loss за эпоху (float)
    """
    model.train()
    total_loss = 0.0
    n_batches = 0

    for X_batch, y_batch, mask_batch in train_loader:
        X_batch = X_batch.to(device)
        y_batch = y_batch.to(device)
        mask_batch = mask_batch.to(device)

        optimizer.zero_grad()
        logits = model(X_batch, mask=mask_batch)
        loss = loss_fn(logits, y_batch)
        loss.backward()

        # Gradient clipping для стабильности обучения
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)

        optimizer.step()

        total_loss += loss.item()
        n_batches += 1

    return total_loss / n_batches


@torch.no_grad()
def validate(
    model: nn.Module,
    val_loader: torch.utils.data.DataLoader,
    loss_fn: nn.Module,
    device: torch.device,
) -> tuple[float, dict]:
    """
    Валидация модели.

    Аргументы:
        model: Модель для оценки
        val_loader: DataLoader с validation данными
        loss_fn: Функция потерь
        device: Устройство (cuda/cpu)

    Возвращает:
        Кортеж (val_loss, metrics):
        - val_loss: Средний loss на validation (float)
        - metrics: Словарь с метриками из compute_metrics()
    """
    model.eval()
    total_loss = 0.0
    n_batches = 0
    all_preds = []
    all_targets = []

    for X_batch, y_batch, mask_batch in val_loader:
        X_batch = X_batch.to(device)
        y_batch = y_batch.to(device)
        mask_batch = mask_batch.to(device)

        logits = model(X_batch, mask=mask_batch)
        loss = loss_fn(logits, y_batch)

        total_loss += loss.item()
        n_batches += 1

        preds = logits.argmax(dim=1).cpu().numpy()
        targets = y_batch.cpu().numpy()

        all_preds.append(preds)
        all_targets.append(targets)

    all_preds = np.concatenate(all_preds)
    all_targets = np.concatenate(all_targets)

    # Маппинг обратно: {0, 1, 2} → {-1, 0, 1} для вычисления метрик
    all_preds_orig = np.array([INV_LABEL_MAP[p] for p in all_preds])
    all_targets_orig = np.array([INV_LABEL_MAP[t] for t in all_targets])

    metrics = compute_metrics(all_targets_orig, all_preds_orig)

    return total_loss / n_batches, metrics


def train_model(
    model_name: str,
    epochs: int = DEFAULTS['epochs'],
    batch_size: int = DEFAULTS['batch_size'],
    lr: float = DEFAULTS['lr'],
    weight_decay: float = DEFAULTS['weight_decay'],
    patience: int = DEFAULTS['patience'],
    seed: int = DEFAULTS['seed'],
) -> dict:
    """
    Полный цикл обучения модели.

    Аргументы:
        model_name: Имя модели из MODEL_REGISTRY
        epochs: Максимальное количество эпох
        batch_size: Размер батча
        lr: Learning rate
        weight_decay: L2 регуляризация
        patience: Early stopping patience (по val macro F1)
        seed: Random seed

    Возвращает:
        Словарь с результатами обучения:
        - model_name: str
        - best_f1_macro: float
        - best_epoch: int
        - num_parameters: int
        - training_time: float (секунды)
        - history: dict с train_loss, val_loss, val_f1 по эпохам
        - best_metrics: dict с метриками лучшей эпохи
    """
    # ── Setup ────────────────────────────────────────────────────────────────
    set_seed(seed)
    device = get_device()

    CHECKPOINTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    # ── Данные ───────────────────────────────────────────────────────────────
    train_loader, val_loader, scaler = create_data_loaders(
        batch_size=batch_size,
    )

    # ── Модель ───────────────────────────────────────────────────────────────
    model = get_model(model_name)
    model = model.to(device)
    n_params = count_parameters(model)

    print(f"\n{'═' * 60}")
    print(f"  Модель: {model_name.upper()}")
    print(f"  Параметров: {n_params:,}")
    print(f"{'═' * 60}")

    # ── Loss, Optimizer, Scheduler ───────────────────────────────────────────
    loss_fn = FocalLoss(
        alpha=DEFAULTS['alpha'],
        gamma=DEFAULTS['gamma'],
    ).to(device)

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=lr,
        weight_decay=weight_decay,
    )

    # ReduceLROnPlateau мониторит val_f1_macro (mode='max')
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer,
        mode='max',          # Максимизируем F1
        patience=DEFAULTS['scheduler_patience'],
        factor=DEFAULTS['scheduler_factor'],
        verbose=True,
    )

    # ── Training loop ────────────────────────────────────────────────────────
    history = {
        'train_loss': [],
        'val_loss': [],
        'val_f1_macro': [],
        'val_f1_class_neg': [],
        'val_f1_class_zero': [],
        'val_f1_class_pos': [],
        'lr': [],
    }

    best_f1 = -1.0
    best_epoch = 0
    best_metrics = {}
    epochs_without_improvement = 0

    start_time = time.time()

    print(f"\n{'Epoch':>5} | {'Train Loss':>10} | {'Val Loss':>10} | "
          f"{'Val F1 (macro)':>14} | {'F1(-1)':>7} | {'F1(0)':>7} | {'F1(1)':>7} | {'LR':>10}")
    print(f"{'─' * 90}")

    for epoch in range(1, epochs + 1):
        # Train
        train_loss = train_one_epoch(model, train_loader, loss_fn, optimizer, device)

        # Validate
        val_loss, metrics = validate(model, val_loader, loss_fn, device)
        val_f1 = metrics['f1_macro']
        f1_per = metrics['f1_per_class']

        current_lr = optimizer.param_groups[0]['lr']

        # Scheduler step (на val F1)
        scheduler.step(val_f1)

        # History
        history['train_loss'].append(train_loss)
        history['val_loss'].append(val_loss)
        history['val_f1_macro'].append(val_f1)
        history['val_f1_class_neg'].append(f1_per.get(-1, 0.0))
        history['val_f1_class_zero'].append(f1_per.get(0, 0.0))
        history['val_f1_class_pos'].append(f1_per.get(1, 0.0))
        history['lr'].append(current_lr)

        # Logline
        print(f"{epoch:>5} | {train_loss:>10.4f} | {val_loss:>10.4f} | "
              f"{val_f1:>14.4f} | {f1_per.get(-1, 0):>7.4f} | {f1_per.get(0, 0):>7.4f} | "
              f"{f1_per.get(1, 0):>7.4f} | {current_lr:>10.6f}")

        # ── Early stopping на val macro F1 ───────────────────────────────────
        if val_f1 > best_f1:
            best_f1 = val_f1
            best_epoch = epoch
            best_metrics = metrics.copy()
            epochs_without_improvement = 0

            # Сохраняем лучшую модель
            checkpoint_path = CHECKPOINTS_DIR / f'{model_name}_best.pt'
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'best_f1_macro': best_f1,
                'model_name': model_name,
            }, checkpoint_path)
            print(f"      ✅ Новый лучший F1={best_f1:.4f}, сохранено: {checkpoint_path.name}")
        else:
            epochs_without_improvement += 1
            if epochs_without_improvement >= patience:
                print(f"\n  ⏹️  Early stopping: {patience} эпох без улучшения F1")
                break

    training_time = time.time() - start_time

    # ── Результаты ───────────────────────────────────────────────────────────
    print(f"\n{'═' * 60}")
    print(f"  РЕЗУЛЬТАТ: {model_name.upper()}")
    print(f"{'═' * 60}")
    print(f"  Лучший epoch: {best_epoch}")
    print(f"  Best val macro F1: {best_f1:.4f}")
    print(f"  Время обучения: {training_time:.1f}с")
    print(f"  Параметров: {n_params:,}")
    print(f"\n{best_metrics.get('classification_report', '')}")

    # ── Plots ────────────────────────────────────────────────────────────────
    _plot_training_curves(history, model_name)
    _plot_confusion_matrix(best_metrics['confusion_matrix'], model_name)

    return {
        'model_name': model_name,
        'best_f1_macro': best_f1,
        'best_epoch': best_epoch,
        'num_parameters': n_params,
        'training_time': training_time,
        'history': history,
        'best_metrics': best_metrics,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# ВИЗУАЛИЗАЦИЯ
# ═══════════════════════════════════════════════════════════════════════════════

def _plot_training_curves(history: dict, model_name: str):
    """
    Построение кривых обучения: loss и F1 по эпохам.

    Сохраняет в ML/plots/training_curves_<model>.png
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    epochs_range = range(1, len(history['train_loss']) + 1)

    # Loss
    axes[0].plot(epochs_range, history['train_loss'], label='Train Loss', color='#2196F3')
    axes[0].plot(epochs_range, history['val_loss'], label='Val Loss', color='#F44336')
    axes[0].set_xlabel('Epoch')
    axes[0].set_ylabel('Focal Loss')
    axes[0].set_title(f'{model_name}: Loss')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # F1 scores
    axes[1].plot(epochs_range, history['val_f1_macro'],
                 label='Macro F1', color='#4CAF50', linewidth=2)
    axes[1].plot(epochs_range, history['val_f1_class_neg'],
                 label='F1 (class -1)', color='#FF9800', linestyle='--')
    axes[1].plot(epochs_range, history['val_f1_class_zero'],
                 label='F1 (class 0)', color='#9E9E9E', linestyle='--')
    axes[1].plot(epochs_range, history['val_f1_class_pos'],
                 label='F1 (class 1)', color='#03A9F4', linestyle='--')
    axes[1].set_xlabel('Epoch')
    axes[1].set_ylabel('F1-Score')
    axes[1].set_title(f'{model_name}: Validation F1')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    save_path = PLOTS_DIR / f'training_curves_{model_name}.png'
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  📊 Кривые обучения: {save_path.name}")


def _plot_confusion_matrix(cm: np.ndarray, model_name: str):
    """
    Сохранение confusion matrix лучшей эпохи.

    Сохраняет в ML/plots/cm_<model>.png
    """
    fig, ax = plt.subplots(figsize=(8, 6))
    labels = ['Sell (-1)', 'Neutral (0)', 'Buy (1)']

    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax,
                xticklabels=labels, yticklabels=labels)
    ax.set_xlabel('Predicted', fontsize=12)
    ax.set_ylabel('Actual', fontsize=12)
    ax.set_title(f'Confusion Matrix: {model_name} (best epoch)', fontsize=14)

    plt.tight_layout()
    save_path = PLOTS_DIR / f'cm_{model_name}.png'
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  📊 Confusion matrix: {save_path.name}")


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

def parse_args() -> argparse.Namespace:
    """Парсинг аргументов командной строки."""
    parser = argparse.ArgumentParser(
        description='Обучение нейросетевых моделей для классификации фракталов'
    )
    parser.add_argument(
        '--model', type=str, required=True,
        choices=list(MODEL_REGISTRY.keys()),
        help=f"Модель для обучения: {', '.join(MODEL_REGISTRY.keys())}"
    )
    parser.add_argument('--epochs', type=int, default=DEFAULTS['epochs'],
                        help=f"Макс. эпох (default: {DEFAULTS['epochs']})")
    parser.add_argument('--batch_size', type=int, default=DEFAULTS['batch_size'],
                        help=f"Batch size (default: {DEFAULTS['batch_size']})")
    parser.add_argument('--lr', type=float, default=DEFAULTS['lr'],
                        help=f"Learning rate (default: {DEFAULTS['lr']})")
    parser.add_argument('--patience', type=int, default=DEFAULTS['patience'],
                        help=f"Early stopping patience (default: {DEFAULTS['patience']})")
    parser.add_argument('--seed', type=int, default=DEFAULTS['seed'],
                        help=f"Random seed (default: {DEFAULTS['seed']})")
    return parser.parse_args()


def main():
    """Точка входа: парсинг аргументов → обучение модели."""
    args = parse_args()

    print("=" * 60)
    print("  NEURAL NETWORK TRAINING")
    print(f"  Модель: {args.model}")
    print(f"  Epochs: {args.epochs}, Batch: {args.batch_size}, LR: {args.lr}")
    print("=" * 60)

    result = train_model(
        model_name=args.model,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        patience=args.patience,
        seed=args.seed,
    )

    # Сохраняем результат как JSON (без numpy/torch объектов)
    result_serializable = {
        'model_name': result['model_name'],
        'best_f1_macro': result['best_f1_macro'],
        'best_epoch': result['best_epoch'],
        'num_parameters': result['num_parameters'],
        'training_time': result['training_time'],
        'f1_per_class': {
            str(k): v for k, v in result['best_metrics']['f1_per_class'].items()
        },
    }

    result_path = CHECKPOINTS_DIR / f'{args.model}_result.json'
    with open(result_path, 'w', encoding='utf-8') as f:
        json.dump(result_serializable, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Результат сохранён: {result_path}")

    print("\n" + "=" * 60)
    print("  ✅ ОБУЧЕНИЕ ЗАВЕРШЕНО")
    print("=" * 60)


if __name__ == '__main__':
    main()
