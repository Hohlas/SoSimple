# =============================================================================
# Файл: train.py
# Назначение: Единый скрипт обучения нейросетевых моделей
# Язык: Python 3.11+
# Обновлён: 2026-02-27
# Зависимости:
#   Входные данные:
#     - DATA/Nero_train_labeled.csv (откуда: processing/label_main.py)
#     - DATA/Nero_validation_labeled.csv (откуда: processing/label_main.py)
#   Выходные данные:
#     - ML/checkpoints/<model>_best.pt            (classification)
#     - ML/checkpoints/<model>_regression_best.pt (regression)
#     - ML/plots/training_curves_<model>.png      (classification)
#     - ML/plots/training_curves_<model>_regression.png (regression)
#     - ML/plots/cm_<model>.png                   (confusion matrix, classification)
#     - ML/plots/regression_<model>.png           (scatter + residuals, regression)
# Внешние зависимости:
#   - torch>=2.0
#   - numpy>=1.24
#   - pandas>=2.0
#   - scikit-learn>=1.2
#   - scipy>=1.10
#   - matplotlib>=3.7
#   - seaborn>=0.12
# Использование:
#   python -m ML.train --model bilstm --task classification
#   python -m ML.train --model bilstm --task regression
#   python -m ML.train --model cnn1d  --task regression --epochs 30 --batch_size 512
# Примечания:
#   Classification:
#     - Early stopping на val macro F1 (НЕ на loss!)
#     - Focal Loss с alpha=[0.45, 0.10, 0.45]
#   Regression:
#     - Early stopping на val pearson_r (максимизируем корреляцию)
#     - Huber Loss (delta=1.0)
#   - Scheduler: ReduceLROnPlateau на основной метрике (mode='max')
# =============================================================================

"""
Единый скрипт обучения для всех нейросетевых архитектур.

Принимает --model и --task аргументы:
  --task classification (default): Focal Loss, AdamW, early stopping на macro F1
  --task regression:               Huber Loss, AdamW, early stopping на pearson_r
"""

import argparse
import json
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

# Optuna Pruning support (optional)
try:
    from optuna import TrialPruned
    OPTUNA_AVAILABLE = True
except ImportError:
    OPTUNA_AVAILABLE = False
    # Создаем заглушку для случаев, когда Optuna не установлен
    class TrialPruned(Exception):
        pass

from ML.data_loader import create_data_loaders, INV_LABEL_MAP
from ML.losses import FocalLoss, HuberLoss
from ML.models import get_model, MODEL_REGISTRY
from ML.utils import (
    set_seed, compute_metrics, compute_regression_metrics,
    count_parameters, get_device,
)
from ML.experiment_logger import CSVExperimentLogger


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
    # Classification
    'gamma': 2.0,          # Focal Loss gamma
    'alpha': [0.45, 0.10, 0.45],  # Focal Loss class weights
    # Regression
    'huber_delta': 1.0,    # Huber Loss delta
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
    regression: bool = False,
) -> float:
    """
    Обучение одной эпохи.

    Аргументы:
        model: Модель для обучения
        train_loader: DataLoader с train данными
        loss_fn: Функция потерь (FocalLoss или HuberLoss)
        optimizer: Оптимизатор (AdamW)
        device: Устройство (cuda/cpu)
        regression: Если True — squeeze выход модели до (batch,) для регрессии

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

        if regression:
            # Регрессия: модель возвращает (batch, 1) → squeeze → (batch,)
            preds = logits.squeeze(-1)
            loss = loss_fn(preds, y_batch)
        else:
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
    Валидация модели в режиме классификации.

    Аргументы:
        model: Модель для оценки
        val_loader: DataLoader с validation данными
        loss_fn: Функция потерь
        device: Устройство (cuda/cpu)

    Возвращает:
        Кортеж (val_loss, metrics) с классификационными метриками
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


@torch.no_grad()
def validate_regression(
    model: nn.Module,
    val_loader: torch.utils.data.DataLoader,
    loss_fn: nn.Module,
    device: torch.device,
) -> tuple[float, dict]:
    """
    Валидация модели в режиме регрессии.

    Аргументы:
        model: Модель для оценки
        val_loader: DataLoader с validation данными
        loss_fn: HuberLoss
        device: Устройство (cuda/cpu)

    Возвращает:
        Кортеж (val_loss, metrics) с регрессионными метриками:
        mae, rmse, r2, pearson_r, pearson_p, directional_accuracy
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
        preds = logits.squeeze(-1)           # (batch,)
        loss = loss_fn(preds, y_batch)

        total_loss += loss.item()
        n_batches += 1

        all_preds.append(preds.cpu().numpy())
        all_targets.append(y_batch.cpu().numpy())

    all_preds = np.concatenate(all_preds)
    all_targets = np.concatenate(all_targets)

    metrics = compute_regression_metrics(all_targets, all_preds)

    return total_loss / n_batches, metrics


def train_model(
    model_name: str,
    task: str = 'classification',
    use_scaler: bool = False,
    epochs: int = DEFAULTS['epochs'],
    batch_size: int = DEFAULTS['batch_size'],
    lr: float = DEFAULTS['lr'],
    weight_decay: float = DEFAULTS['weight_decay'],
    patience: int = DEFAULTS['patience'],
    seed: int = DEFAULTS['seed'],
    # Focal Loss параметры (classification)
    focal_alpha: list[float] | None = None,
    focal_gamma: float = DEFAULTS['gamma'],
    # Huber Loss параметр (regression)
    huber_delta: float = DEFAULTS['huber_delta'],
    # Scheduler параметры
    scheduler_patience: int = DEFAULTS['scheduler_patience'],
    scheduler_factor: float = DEFAULTS['scheduler_factor'],
    # Metrique mode для classification
    metric_mode: str = 'f1_macro',
    min_signal_recall: float = 0.3,
    use_weighted_sampler: bool = False,
    # Optuna Pruning
    trial=None,
    # Режим без вывода в консоль (для Optuna)
    silent: bool = False,
) -> dict:
    """
    Полный цикл обучения модели.

    Аргументы:
        model_name: Имя модели из MODEL_REGISTRY
        task: 'classification' (signal, FocalLoss, F1) или
              'regression' (predict, HuberLoss, pearson_r)
        epochs: Максимальное количество эпох
        batch_size: Размер батча
        lr: Learning rate
        weight_decay: L2 регуляризация
        patience: Early stopping patience
        seed: Random seed
        focal_alpha: Веса классов для Focal Loss (classification)
        focal_gamma: Gamma параметр Focal Loss (classification)
        huber_delta: Delta параметр Huber Loss (regression)
        scheduler_patience: Patience для ReduceLROnPlateau
        scheduler_factor: Factor для ReduceLROnPlateau
        trial: Optuna trial объект для Pruning (опционально)
        silent: Если True — минимальный вывод в консоль

    Возвращает:
        Словарь с результатами обучения:
        - model_name, task, best_metric, best_epoch, num_parameters,
          training_time, history, best_metrics
    """
    regression = (task == 'regression')

    # ── Setup ────────────────────────────────────────────────────────────────
    set_seed(seed)
    device = get_device()

    CHECKPOINTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    # ── Данные ───────────────────────────────────────────────────────────────
    target_col = 'predict' if regression else 'signal'
    train_loader, val_loader, scaler = create_data_loaders(
        batch_size=batch_size,
        target=target_col,
        use_scaler=use_scaler,
        use_weighted_sampler=use_weighted_sampler if not regression else False,
    )

    # ── Модель ───────────────────────────────────────────────────────────────
    # Для регрессии: 1 выход; для классификации: 3 выхода
    num_classes = 1 if regression else 3
    model = get_model(model_name, num_classes=num_classes)
    model = model.to(device)
    n_params = count_parameters(model)

    if not silent:
        print(f"\n{'═' * 60}")
        print(f"  Модель: {model_name.upper()}  |  Задача: {task.upper()}")
        print(f"  Параметров: {n_params:,}")
        print(f"{'═' * 60}")

    # ── Loss, Optimizer, Scheduler ───────────────────────────────────────────
    if regression:
        loss_fn = HuberLoss(delta=huber_delta).to(device)
    else:
        # Используем переданный focal_alpha или дефолт
        alpha = focal_alpha if focal_alpha is not None else DEFAULTS['alpha']
        loss_fn = FocalLoss(
            alpha=alpha,
            gamma=focal_gamma,
        ).to(device)

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=lr,
        weight_decay=weight_decay,
    )

    # ReduceLROnPlateau — максимизируем основную метрику (F1 или pearson_r)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer,
        mode='max',
        patience=scheduler_patience,
        factor=scheduler_factor,
    )

    # ── Training loop ────────────────────────────────────────────────────────
    if regression:
        history = {
            'train_loss': [], 'val_loss': [],
            'val_pearson_r': [], 'val_mae': [], 'val_rmse': [],
            'val_r2': [], 'val_dir_acc': [], 'lr': [],
        }
        metric_name = 'pearson_r'
        if not silent:
            print(f"\n{'Epoch':>5} | {'Train Loss':>10} | {'Val Loss':>10} | "
                  f"{'pearson_r':>10} | {'MAE':>8} | {'RMSE':>8} | {'DirAcc':>7} | {'LR':>10}")
    else:
        history = {
            'train_loss': [], 'val_loss': [], 'val_f1_macro': [],
            'val_f1_class_neg': [], 'val_f1_class_zero': [],
            'val_f1_class_pos': [], 'lr': [],
        }
        metric_name = metric_mode  # Используем переданный режим метрики
        if not silent:
            print(f"\n{'Epoch':>5} | {'Train Loss':>10} | {'Val Loss':>10} | "
                  f"{'Val F1 (macro)':>14} | {'F1(-1)':>7} | {'F1(0)':>7} | {'F1(1)':>7} | {'LR':>10}")

    if not silent:
        print(f"{'─' * 90}")

    best_metric = -1.0
    best_epoch = 0
    best_metrics = {}
    epochs_without_improvement = 0

    start_time = time.time()

    for epoch in range(1, epochs + 1):
        # Train
        train_loss = train_one_epoch(
            model, train_loader, loss_fn, optimizer, device, regression=regression
        )

        # Validate
        if regression:
            val_loss, metrics = validate_regression(model, val_loader, loss_fn, device)
            val_metric = metrics['pearson_r']

            history['train_loss'].append(train_loss)
            history['val_loss'].append(val_loss)
            history['val_pearson_r'].append(metrics['pearson_r'])
            history['val_mae'].append(metrics['mae'])
            history['val_rmse'].append(metrics['rmse'])
            history['val_r2'].append(metrics['r2'])
            history['val_dir_acc'].append(metrics['directional_accuracy'])
            history['lr'].append(optimizer.param_groups[0]['lr'])

            current_lr = optimizer.param_groups[0]['lr']
            if not silent:
                print(f"{epoch:>5} | {train_loss:>10.4f} | {val_loss:>10.4f} | "
                      f"{metrics['pearson_r']:>10.4f} | {metrics['mae']:>8.4f} | "
                      f"{metrics['rmse']:>8.4f} | {metrics['directional_accuracy']:>7.4f} | "
                      f"{current_lr:>10.6f}")
        else:
            val_loss, metrics = validate(model, val_loader, loss_fn, device)
            f1_per = metrics['f1_per_class']

            # Выбираем метрику для early stopping в зависимости от metric_mode
            if metric_mode == 'signal_precision':
                # Проверяем ограничение на recall
                if metrics['signal_recall'] >= min_signal_recall:
                    val_metric = metrics['signal_precision']
                else:
                    val_metric = 0.0  # Штраф за невыполнение условия
            elif metric_mode == 'f1_minority':
                val_metric = metrics['f1_minority']
            else:  # 'f1_macro'
                val_metric = metrics['f1_macro']

            current_lr = optimizer.param_groups[0]['lr']

            history['train_loss'].append(train_loss)
            history['val_loss'].append(val_loss)
            history['val_f1_macro'].append(metrics['f1_macro'])
            history['val_f1_class_neg'].append(f1_per.get(-1, 0.0))
            history['val_f1_class_zero'].append(f1_per.get(0, 0.0))
            history['val_f1_class_pos'].append(f1_per.get(1, 0.0))
            history['lr'].append(current_lr)

            if not silent:
                print(f"{epoch:>5} | {train_loss:>10.4f} | {val_loss:>10.4f} | "
                      f"{val_metric:>14.4f} | {f1_per.get(-1, 0):>7.4f} | {f1_per.get(0, 0):>7.4f} | "
                      f"{f1_per.get(1, 0):>7.4f} | {current_lr:>10.6f}")

        # Scheduler step (на основной метрике)
        scheduler.step(val_metric)

        # ── Optuna Pruning ─────────────────────────────────────────────────────
        if trial is not None:
            trial.report(val_metric, epoch)
            # Прерываем trial, если Optuna считает его неуспешным
            if trial.should_prune():
                if not silent:
                    print(f"\n  🚫 Optuna Pruning на epoch {epoch}")
                raise TrialPruned()

        # ── Early stopping ───────────────────────────────────────────────────
        if val_metric > best_metric:
            best_metric = val_metric
            best_epoch = epoch
            best_metrics = metrics.copy()
            epochs_without_improvement = 0

            # Суффикс чекпойнта: _regression для регрессии
            suffix = '_regression' if regression else ''
            checkpoint_path = CHECKPOINTS_DIR / f'{model_name}{suffix}_best.pt'
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'best_metric': best_metric,
                'metric_name': metric_name,
                'model_name': model_name,
                'task': task,
                'num_classes': num_classes,
            }, checkpoint_path)
            if not silent:
                print(f"      ✅ Новый лучший {metric_name}={best_metric:.4f}, "
                      f"сохранено: {checkpoint_path.name}")
        else:
            epochs_without_improvement += 1
            if epochs_without_improvement >= patience:
                if not silent:
                    print(f"\n  ⏹️  Early stopping: {patience} эпох без улучшения {metric_name}")
                break

    training_time = time.time() - start_time

    # ── Результаты ───────────────────────────────────────────────────────────
    if not silent:
        print(f"\n{'═' * 60}")
        print(f"  РЕЗУЛЬТАТ: {model_name.upper()} ({task.upper()})")
        print(f"{'═' * 60}")
        print(f"  Лучший epoch: {best_epoch}")
        print(f"  Best val {metric_name}: {best_metric:.4f}")
        print(f"  Время обучения: {training_time:.1f}с")
        print(f"  Параметров: {n_params:,}")

        if not regression:
            print(f"\n{best_metrics.get('classification_report', '')}")
        else:
            print(f"  MAE:  {best_metrics.get('mae', 0):.4f}")
            print(f"  RMSE: {best_metrics.get('rmse', 0):.4f}")
            print(f"  R²:   {best_metrics.get('r2', 0):.4f}")
            print(f"  DirAcc: {best_metrics.get('directional_accuracy', 0):.4f}")

    # ── Plots (только если не silent) ────────────────────────────────────────
    if not silent:
        _plot_training_curves(history, model_name, regression=regression)

        if regression:
            # Для scatter нужны предсказания на val — пересчитываем
            all_preds, all_targets = _collect_regression_preds(model, val_loader, device)
            _plot_regression_results(all_targets, all_preds, model_name)
        else:
            _plot_confusion_matrix(best_metrics['confusion_matrix'], model_name)

    return {
        'model_name': model_name,
        'task': task,
        'best_metric': best_metric,
        'metric_name': metric_name,
        'best_epoch': best_epoch,
        'num_parameters': n_params,
        'training_time': training_time,
        'history': history,
        'best_metrics': best_metrics,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ═══════════════════════════════════════════════════════════════════════════════

@torch.no_grad()
def _collect_regression_preds(
    model: nn.Module,
    val_loader: torch.utils.data.DataLoader,
    device: torch.device,
) -> tuple[np.ndarray, np.ndarray]:
    """Собрать предсказания регрессионной модели для построения графиков."""
    model.eval()
    all_preds, all_targets = [], []
    for X_batch, y_batch, mask_batch in val_loader:
        X_batch = X_batch.to(device)
        mask_batch = mask_batch.to(device)
        preds = model(X_batch, mask=mask_batch).squeeze(-1).cpu().numpy()
        all_preds.append(preds)
        all_targets.append(y_batch.numpy())
    return np.concatenate(all_preds), np.concatenate(all_targets)


# ═══════════════════════════════════════════════════════════════════════════════
# ВИЗУАЛИЗАЦИЯ
# ═══════════════════════════════════════════════════════════════════════════════

def _plot_training_curves(history: dict, model_name: str, regression: bool = False):
    """
    Построение кривых обучения: loss и основная метрика по эпохам.

    Classification: F1 по классам.
    Regression: pearson_r, MAE.
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    epochs_range = range(1, len(history['train_loss']) + 1)

    # Loss
    axes[0].plot(epochs_range, history['train_loss'], label='Train Loss', color='#2196F3')
    axes[0].plot(epochs_range, history['val_loss'], label='Val Loss', color='#F44336')
    axes[0].set_xlabel('Epoch')
    axes[0].set_ylabel('Huber Loss' if regression else 'Focal Loss')
    axes[0].set_title(f'{model_name}: Loss')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    if regression:
        # Правый: pearson_r + MAE
        axes[1].plot(epochs_range, history['val_pearson_r'],
                     label='Pearson r', color='#4CAF50', linewidth=2)
        ax2 = axes[1].twinx()
        ax2.plot(epochs_range, history['val_mae'],
                 label='MAE', color='#FF9800', linestyle='--')
        ax2.plot(epochs_range, history['val_dir_acc'],
                 label='Dir.Acc', color='#03A9F4', linestyle=':')
        ax2.set_ylabel('MAE / DirAcc')
        axes[1].set_xlabel('Epoch')
        axes[1].set_ylabel('Pearson r')
        axes[1].set_title(f'{model_name}: Validation Metrics (Regression)')
        # Объединённая легенда
        lines1, labels1 = axes[1].get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        axes[1].legend(lines1 + lines2, labels1 + labels2, loc='best')
    else:
        # Правый: F1 по классам
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

    suffix = '_regression' if regression else ''
    save_path = PLOTS_DIR / f'training_curves_{model_name}{suffix}.png'
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  📊 Кривые обучения: {save_path.name}")


def _plot_confusion_matrix(cm: np.ndarray, model_name: str):
    """
    Сохранение confusion matrix лучшей эпохи (classification).

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


def _plot_regression_results(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    model_name: str,
):
    """
    Построение scatter plot и гистограммы residuals для регрессии.

    Сохраняет в ML/plots/regression_<model>.png
    """
    residuals = y_pred - y_true

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Scatter: y_true vs y_pred
    axes[0].scatter(y_true, y_pred, alpha=0.3, s=10, color='#2196F3')
    lim = max(abs(y_true).max(), abs(y_pred).max()) * 1.05
    axes[0].plot([-lim, lim], [-lim, lim], 'r--', linewidth=1.5, label='Ideal')
    axes[0].set_xlim(-lim, lim)
    axes[0].set_ylim(-lim, lim)
    axes[0].set_xlabel('y_true (predict)')
    axes[0].set_ylabel('y_pred')
    axes[0].set_title(f'{model_name}: Scatter (val)')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # Histogram residuals
    axes[1].hist(residuals, bins=60, color='#FF9800', edgecolor='none', alpha=0.8)
    axes[1].axvline(0, color='red', linestyle='--', linewidth=1.5)
    axes[1].set_xlabel('Residual (y_pred - y_true)')
    axes[1].set_ylabel('Count')
    axes[1].set_title(f'{model_name}: Residuals (val)')
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    save_path = PLOTS_DIR / f'regression_{model_name}.png'
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  📊 Regression результаты: {save_path.name}")


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

def parse_args() -> argparse.Namespace:
    """Парсинг аргументов командной строки."""
    parser = argparse.ArgumentParser(
        description='Обучение нейросетевых моделей (классификация или регрессия)'
    )
    parser.add_argument(
        '--model', type=str, required=True,
        choices=list(MODEL_REGISTRY.keys()),
        help=f"Модель для обучения: {', '.join(MODEL_REGISTRY.keys())}"
    )
    parser.add_argument(
        '--task', type=str, default='classification',
        choices=['classification', 'regression'],
        help="Задача: 'classification' (signal, FocalLoss) или 'regression' (predict, HuberLoss). "
             "Default: classification"
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
    
    # Focal Loss параметры (только для classification)
    parser.add_argument('--focal_gamma', type=float, default=DEFAULTS['gamma'],
                        help=f"Focal Loss gamma (default: {DEFAULTS['gamma']})")
    parser.add_argument('--focal_minority_weight', type=float, default=0.45,
                        help=f"Вес minority классов (-1 и 1) для Focal Loss. Neutral будет (1-2*weight). (default: 0.45)")
    
    # Optimizer и Scheduler параметры
    parser.add_argument('--weight_decay', type=float, default=DEFAULTS['weight_decay'],
                        help=f"L2 weight decay (default: {DEFAULTS['weight_decay']})")
    parser.add_argument('--scheduler_patience', type=int, default=DEFAULTS['scheduler_patience'],
                        help=f"Patience для ReduceLROnPlateau (default: {DEFAULTS['scheduler_patience']})")
    parser.add_argument('--scheduler_factor', type=float, default=DEFAULTS['scheduler_factor'],
                        help=f"Factor для ReduceLROnPlateau (default: {DEFAULTS['scheduler_factor']})")
    
    # Флаг для включения StandardScaler (по дефолту False)
    parser.add_argument('--use_scaler', action='store_true',
                        help="Включить дополнительную нормализацию (StandardScaler). По умолчанию выключено.")
    
    # Параметры для выбора целевой метрики и WeightedRandomSampler
    parser.add_argument('--metric_mode', type=str, default='f1_macro',
                        choices=['f1_macro', 'f1_minority', 'signal_precision'],
                        help="Целевая метрика для early stopping: f1_macro | f1_minority | signal_precision (default: f1_macro)")
    parser.add_argument('--min_signal_recall', type=float, default=0.3,
                        help="Минимальный recall сигнальных классов (для metric_mode=signal_precision). Default: 0.3")
    parser.add_argument('--use_weighted_sampler', action='store_true',
                        help="Использовать WeightedRandomSampler для балансировки train-батчей. По умолчанию выключено.")
    
    return parser.parse_args()


def main():
    """Точка входа: парсинг аргументов → обучение модели."""
    args = parse_args()

    print("=" * 60)
    print("  NEURAL NETWORK TRAINING")
    print(f"  Модель: {args.model}  |  Задача: {args.task}")
    print(f"  Epochs: {args.epochs}, Batch: {args.batch_size}, LR: {args.lr}")
    print("=" * 60)

    # Формируем focal_alpha из focal_minority_weight
    # [weight_minority, 1-2*weight_minority, weight_minority]
    focal_alpha = [args.focal_minority_weight,
                   1.0 - 2 * args.focal_minority_weight,
                   args.focal_minority_weight]
    
    result = train_model(
        model_name=args.model,
        task=args.task,
        use_scaler=args.use_scaler,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        weight_decay=args.weight_decay,
        patience=args.patience,
        seed=args.seed,
        focal_alpha=focal_alpha,
        focal_gamma=args.focal_gamma,
        scheduler_patience=args.scheduler_patience,
        scheduler_factor=args.scheduler_factor,
        metric_mode=args.metric_mode,
        min_signal_recall=args.min_signal_recall,
        use_weighted_sampler=args.use_weighted_sampler,
    )

    # Сохраняем результат как JSON
    regression = (args.task == 'regression')

    if regression:
        result_serializable = {
            'model_name': result['model_name'],
            'task': result['task'],
            'best_pearson_r': result['best_metric'],
            'best_epoch': result['best_epoch'],
            'num_parameters': result['num_parameters'],
            'training_time': result['training_time'],
            'val_metrics': {
                k: v for k, v in result['best_metrics'].items()
                if isinstance(v, float)
            },
        }
        suffix = '_regression'
    else:
        result_serializable = {
            'model_name': result['model_name'],
            'task': result['task'],
            'best_f1_macro': result['best_metric'],
            'best_epoch': result['best_epoch'],
            'num_parameters': result['num_parameters'],
            'training_time': result['training_time'],
            'f1_per_class': {
                str(k): v for k, v in result['best_metrics']['f1_per_class'].items()
            },
            'metric_mode': args.metric_mode,
            'signal_precision': result['best_metrics'].get('signal_precision'),
            'signal_recall': result['best_metrics'].get('signal_recall'),
            'f1_minority': result['best_metrics'].get('f1_minority'),
        }
        suffix = ''

    result_path = CHECKPOINTS_DIR / f'{args.model}{suffix}_result.json'
    with open(result_path, 'w', encoding='utf-8') as f:
        json.dump(result_serializable, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Результат сохранён: {result_path}")

    # ── Логирование эксперимента ─────────────────────────────────────────────
    config_dict = {
        'model': args.model,
        'task': args.task,
        'epochs': args.epochs,
        'batch_size': args.batch_size,
        'lr': args.lr,
        'weight_decay': args.weight_decay,
        'patience': args.patience,
        'focal_gamma': args.focal_gamma if not regression else None,
        'focal_minority_weight': args.focal_minority_weight if not regression else None,
        'scheduler_patience': args.scheduler_patience,
        'scheduler_factor': args.scheduler_factor,
        'use_scaler': args.use_scaler,
    }

    metrics_dict = {
        'metric_name': result.get('metric_name', 'f1_macro' if not regression else 'pearson_r'),
        'best_metric': result['best_metric'],
        'best_epoch': result['best_epoch'],
        'training_time': result['training_time'],
    }

    # Добавляем метрики в зависимости от задачи
    if regression:
        metrics_dict['mae'] = result['best_metrics'].get('mae')
        metrics_dict['rmse'] = result['best_metrics'].get('rmse')
        metrics_dict['r2'] = result['best_metrics'].get('r2')
        metrics_dict['dir_acc'] = result['best_metrics'].get('directional_accuracy')
    else:
        metrics_dict['f1_macro'] = result['best_metric']
        f1_per_class = result['best_metrics'].get('f1_per_class', {})
        metrics_dict['f1_sell'] = f1_per_class.get(-1)
        metrics_dict['f1_neutral'] = f1_per_class.get(0)
        metrics_dict['f1_buy'] = f1_per_class.get(1)

    checkpoint_path = str(CHECKPOINTS_DIR / f'{args.model}{suffix}_best.pt')

    logger = CSVExperimentLogger()
    logger.log_experiment(config_dict, metrics_dict, checkpoint_path=checkpoint_path)

    print("\n" + "=" * 60)
    print("  ✅ ОБУЧЕНИЕ ЗАВЕРШЕНО")
    print("=" * 60)


if __name__ == '__main__':
    main()
