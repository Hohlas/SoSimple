# =============================================================================
# Файл: train.py
# Назначение: Единый скрипт обучения нейросетевых моделей
# Язык: Python 3.11+
# Обновлён: 2026-04-09
# Зависимости:
#   Входные данные:
#     - DATA/Nero_train_labeled.csv (откуда: processing/label_main.py)
#     - DATA/Nero_validation_labeled.csv (откуда: processing/label_main.py)
#   Выходные данные:
#     - ML/checkpoints/<model>_best.pt            (classification)
#     - ML/checkpoints/<model>_regression_best.pt (regression)
#     - ML/checkpoints/<model>_entry_path_v1_best.pt (entry_path_v1)
#     - ML/checkpoints/<model>_entry_path_v1_quantile_best.pt (entry_path_v1_quantile)
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
#   python -m ML.train --model bilstm --task regression --regression_loss asymmetric
#   python -m ML.train --model cnn1d  --task regression --epochs 30 --batch_size 512
# Примечания:
#   Classification:
#     - Early stopping на val macro F1 (или f1_minority/signal_precision)
#     - Focal Loss с alpha=[0.45, 0.10, 0.45]
#   Regression:
#     - Early stopping на val pearson_r (максимизируем корреляцию)
#     - Huber Loss (delta=1.0) или Asymmetric Loss (penalizing FP/FN differently)
#   - Scheduler: ReduceLROnPlateau на основной метрике (mode='max')
# =============================================================================

"""
Единый скрипт обучения для всех нейросетевых архитектур.

Принимает --model и --task аргументы:
  --task classification (default): Focal Loss, AdamW, early stopping на macro F1
  --task regression:               Huber Loss, AdamW, early stopping на pearson_r
  --task entry_path_v1:            Multi-task Transformer, early stopping на ret_pearson_r
  --task entry_path_v1_quantile:    Multi-task Transformer, early stopping на val_score
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

from ML.data_loader import (
    ARCHETYPE_TARGET,
    BINARY_CLASSIFICATION_TARGETS,
    INV_LABEL_MAP,
    N_FRACTAL_FEATURES,
    REGRESSION_TARGET,
    TB_TARGET,
    TB_TARGET_NAMES,
    TRADE_OUTCOME_TARGET,
    TRADE_PNL_TARGET,
    UPDN_REGRESSION_TARGET,
    UPDN_TARGETS,
    create_data_loaders,
    task_checkpoint_suffix,
    task_target_column,
)
from ML.entry_path_task import (
    ENTRY_PATH_MODEL_NAMES,
    ENTRY_PATH_INV_CLASS_MAP,
    ENTRY_PATH_PATH_REG_TARGETS,
    ENTRY_PATH_RET_TARGETS,
    ENTRY_PATH_TARGET,
    ENTRY_PATH_V1_FEATURE_COLUMNS,
    build_entry_path_model,
)
from ML.entry_path_v1_quantile_task import (
    ENTRY_PATH_V1_QUANTILE_TARGET,
    compute_entry_path_v1_quantile_metrics,
)
from ML.take_skip_trailing_stop_task import (
    TAKE_SKIP_TRAILING_STOP_COLUMNS,
    TAKE_SKIP_TRAILING_STOP_TARGET,
    compute_take_skip_metrics,
)
from ML.trailing_stop_target_quantile_task import (
    TRAILING_STOP_TARGET_QUANTILE_TARGET,
    compute_trailing_stop_quantile_metrics,
)
from ML.trailing_stop_target_task import (
    TRAILING_STOP_TARGET,
    TRAILING_STOP_TARGET_COLUMNS,
)
from ML.losses import FocalLoss, HuberLoss, AsymmetricLoss, DirectionalAsymmetricLoss
from ML.models import get_model, MODEL_REGISTRY
from ML.models.entry_path_v1_quantile_transformer import EntryPathV1QuantileTransformer
from ML.models.trailing_stop_target_quantile_transformer import TrailingStopTargetQuantileTransformer
from ML.tb_probability_calibration import (
    fit_tb_probability_calibrator,
    save_tb_probability_calibrator,
)
from ML.utils import (
    set_seed, compute_metrics, compute_regression_metrics,
    compute_multitarget_regression_metrics,
    compute_binary_classification_metrics,
    compute_single_binary_classification_metrics,
    count_parameters, get_device,
)
from ML.experiment_logger import CSVExperimentLogger


# ─── Пути ────────────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ML_DIR = PROJECT_ROOT / 'ML'
CHECKPOINTS_DIR = ML_DIR / 'checkpoints'
PLOTS_DIR = ML_DIR / 'plots'
REPORTS_DIR = ML_DIR / 'reports'

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
ENTRY_PATH_ACTIVE_WEIGHT = 5.0
ENTRY_PATH_PATH_CLS_ACTIVE_WEIGHT = 20.0


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

    for batch in train_loader:
        if len(batch) == 4:
            X_batch, y_batch, mask_batch, signal_batch = batch
            signal_batch = signal_batch.to(device)
        else:
            X_batch, y_batch, mask_batch = batch
            signal_batch = None
        X_batch = X_batch.to(device)
        y_batch = y_batch.to(device)
        mask_batch = mask_batch.to(device)

        optimizer.zero_grad()
        logits = model(X_batch, mask=mask_batch)

        if regression:
            # Регрессия: multi-target (batch, 6) или single (batch, 1) → squeeze
            if logits.shape[-1] > 1 and y_batch.dim() > 1:
                if signal_batch is not None and isinstance(loss_fn, DirectionalAsymmetricLoss):
                    loss = loss_fn(logits, y_batch, signal_batch)
                else:
                    loss = loss_fn(logits, y_batch)
            else:
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
    target_names: list[str] | None = None,
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
        mae, rmse, r2, pearson_r, pearson_p
    """
    model.eval()
    total_loss = 0.0
    n_batches = 0
    all_preds = []
    all_targets = []

    for batch in val_loader:
        if len(batch) == 4:
            X_batch, y_batch, mask_batch, signal_batch = batch
            signal_batch = signal_batch.to(device)
        else:
            X_batch, y_batch, mask_batch = batch
            signal_batch = None
        X_batch = X_batch.to(device)
        y_batch = y_batch.to(device)
        mask_batch = mask_batch.to(device)

        logits = model(X_batch, mask=mask_batch)

        # Multi-target: (batch, 6) vs (batch, 6); single: squeeze
        if logits.shape[-1] > 1 and y_batch.dim() > 1:
            if signal_batch is not None and isinstance(loss_fn, DirectionalAsymmetricLoss):
                loss = loss_fn(logits, y_batch, signal_batch)
            else:
                loss = loss_fn(logits, y_batch)
            all_preds.append(logits.cpu().numpy())
        else:
            preds = logits.squeeze(-1)
            loss = loss_fn(preds, y_batch)
            all_preds.append(preds.cpu().numpy())

        total_loss += loss.item()
        n_batches += 1
        all_targets.append(y_batch.cpu().numpy())

    all_preds = np.concatenate(all_preds)
    all_targets = np.concatenate(all_targets)

    # Multi-target: per-target metrics + average
    if all_preds.ndim == 2 and all_preds.shape[1] > 1:
        if target_names is not None:
            metrics = compute_named_multitarget_regression_metrics(all_targets, all_preds, target_names)
        else:
            metrics = compute_multitarget_regression_metrics(all_targets, all_preds)
    else:
        metrics = compute_regression_metrics(all_targets, all_preds)

    return total_loss / n_batches, metrics


@torch.no_grad()
def validate_triple_barrier(
    model: nn.Module,
    val_loader: torch.utils.data.DataLoader,
    loss_fn: nn.Module,
    device: torch.device,
) -> tuple[float, dict]:
    """Validation for triple_barrier task."""
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

        proba = torch.sigmoid(logits).cpu().numpy()
        all_preds.append(proba)
        all_targets.append(y_batch.cpu().numpy())

    all_preds = np.concatenate(all_preds)
    all_targets = np.concatenate(all_targets)

    metrics = compute_binary_classification_metrics(
        all_targets, all_preds, TB_TARGET_NAMES
    )

    return total_loss / n_batches, metrics


@torch.no_grad()
def validate_binary(
    model: nn.Module,
    val_loader: torch.utils.data.DataLoader,
    loss_fn: nn.Module,
    device: torch.device,
) -> tuple[float, dict]:
    """Validation for single-target binary classification tasks."""
    model.eval()
    total_loss = 0.0
    n_batches = 0
    all_probs = []
    all_targets = []

    for X_batch, y_batch, mask_batch in val_loader:
        X_batch = X_batch.to(device)
        y_batch = y_batch.to(device)
        mask_batch = mask_batch.to(device)

        logits = model(X_batch, mask=mask_batch)
        loss = loss_fn(logits, y_batch)

        probs = torch.softmax(logits, dim=1)[:, 1].cpu().numpy()
        all_probs.append(probs)
        all_targets.append(y_batch.cpu().numpy())

        total_loss += loss.item()
        n_batches += 1

    metrics = compute_single_binary_classification_metrics(
        np.concatenate(all_targets),
        np.concatenate(all_probs),
    )

    return total_loss / n_batches, metrics


def compute_named_multitarget_regression_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    target_names: list[str],
) -> dict:
    per_target = {}
    pearson_rs = []

    for idx, name in enumerate(target_names):
        target_metrics = compute_regression_metrics(y_true[:, idx], y_pred[:, idx])
        if not np.isfinite(target_metrics['pearson_r']):
            target_metrics['pearson_r'] = 0.0
            target_metrics['pearson_p'] = 1.0
        per_target[name] = target_metrics
        pearson_rs.append(target_metrics['pearson_r'])

    return {
        'mae': float(np.mean([per_target[name]['mae'] for name in target_names])),
        'rmse': float(np.mean([per_target[name]['rmse'] for name in target_names])),
        'r2': float(np.mean([per_target[name]['r2'] for name in target_names])),
        'pearson_r': float(np.mean(pearson_rs)),
        'pearson_p': 0.0,
        'per_target': per_target,
    }


def reduce_entry_path_weighted_loss(
    loss_tensor: torch.Tensor,
    signal_batch: torch.Tensor | None = None,
    active_weight: float = 1.0,
) -> torch.Tensor:
    if loss_tensor.ndim > 1:
        loss_tensor = loss_tensor.mean(dim=tuple(range(1, loss_tensor.ndim)))
    if signal_batch is None or active_weight == 1.0:
        return loss_tensor.mean()
    weights = torch.ones_like(signal_batch, dtype=loss_tensor.dtype)
    weights = torch.where(signal_batch != 0, weights * active_weight, weights)
    return (loss_tensor * weights).sum() / weights.sum().clamp_min(1.0)


def train_one_epoch_entry_path(
    model: nn.Module,
    train_loader: torch.utils.data.DataLoader,
    ret_loss_fn: nn.Module,
    path_reg_loss_fn: nn.Module,
    path_cls_loss_fn: nn.Module,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
) -> float:
    model.train()
    total_loss = 0.0
    n_batches = 0

    for X_batch, engineered_batch, y_reg_batch, y_cls_batch, mask_batch, signal_batch in train_loader:
        X_batch = X_batch.to(device)
        engineered_batch = engineered_batch.to(device)
        y_reg_batch = y_reg_batch.to(device)
        y_cls_batch = y_cls_batch.to(device)
        mask_batch = mask_batch.to(device)
        signal_batch = signal_batch.to(device)

        optimizer.zero_grad()
        outputs = model(X_batch, engineered_batch, mask=mask_batch)
        loss_ret = reduce_entry_path_weighted_loss(
            ret_loss_fn(outputs['ret'], y_reg_batch[:, :len(ENTRY_PATH_RET_TARGETS)]),
            signal_batch,
            active_weight=ENTRY_PATH_ACTIVE_WEIGHT,
        )
        loss_path_cls = reduce_entry_path_weighted_loss(
            path_cls_loss_fn(outputs['path_cls'], y_cls_batch),
            signal_batch,
            active_weight=ENTRY_PATH_PATH_CLS_ACTIVE_WEIGHT,
        )
        loss_path_reg = path_reg_loss_fn(outputs['path_reg'], y_reg_batch[:, len(ENTRY_PATH_RET_TARGETS):])
        loss = loss_ret + 0.5 * loss_path_reg + 0.5 * loss_path_cls

        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()

        total_loss += loss.item()
        n_batches += 1

    return total_loss / n_batches


@torch.no_grad()
def validate_entry_path(
    model: nn.Module,
    val_loader: torch.utils.data.DataLoader,
    ret_loss_fn: nn.Module,
    path_reg_loss_fn: nn.Module,
    path_cls_loss_fn: nn.Module,
    device: torch.device,
) -> tuple[float, dict]:
    model.eval()
    total_loss = 0.0
    n_batches = 0
    all_ret_preds = []
    all_path_reg_preds = []
    all_path_cls_preds = []
    all_reg_targets = []
    all_cls_targets = []
    all_signals = []

    for X_batch, engineered_batch, y_reg_batch, y_cls_batch, mask_batch, signal_batch in val_loader:
        X_batch = X_batch.to(device)
        engineered_batch = engineered_batch.to(device)
        y_reg_batch = y_reg_batch.to(device)
        y_cls_batch = y_cls_batch.to(device)
        mask_batch = mask_batch.to(device)
        signal_batch = signal_batch.to(device)

        outputs = model(X_batch, engineered_batch, mask=mask_batch)
        loss_ret = reduce_entry_path_weighted_loss(
            ret_loss_fn(outputs['ret'], y_reg_batch[:, :len(ENTRY_PATH_RET_TARGETS)]),
            signal_batch,
            active_weight=ENTRY_PATH_ACTIVE_WEIGHT,
        )
        loss_path_cls = reduce_entry_path_weighted_loss(
            path_cls_loss_fn(outputs['path_cls'], y_cls_batch),
            signal_batch,
            active_weight=ENTRY_PATH_PATH_CLS_ACTIVE_WEIGHT,
        )
        loss_path_reg = path_reg_loss_fn(outputs['path_reg'], y_reg_batch[:, len(ENTRY_PATH_RET_TARGETS):])
        loss = loss_ret + 0.5 * loss_path_reg + 0.5 * loss_path_cls

        total_loss += loss.item()
        n_batches += 1

        all_ret_preds.append(outputs['ret'].cpu().numpy())
        all_path_reg_preds.append(outputs['path_reg'].cpu().numpy())
        all_path_cls_preds.append(outputs['path_cls'].argmax(dim=1).cpu().numpy())
        all_reg_targets.append(y_reg_batch.cpu().numpy())
        all_cls_targets.append(y_cls_batch.cpu().numpy())
        all_signals.append(signal_batch.cpu().numpy())

    all_ret_preds = np.concatenate(all_ret_preds)
    all_path_reg_preds = np.concatenate(all_path_reg_preds)
    all_path_cls_preds = np.concatenate(all_path_cls_preds)
    all_reg_targets = np.concatenate(all_reg_targets)
    all_cls_targets = np.concatenate(all_cls_targets)
    all_signals = np.concatenate(all_signals)

    ret_targets = all_reg_targets[:, :len(ENTRY_PATH_RET_TARGETS)]
    path_reg_targets = all_reg_targets[:, len(ENTRY_PATH_RET_TARGETS):]

    ret_metrics = compute_named_multitarget_regression_metrics(
        ret_targets,
        all_ret_preds,
        ENTRY_PATH_RET_TARGETS,
    )
    path_reg_metrics = compute_named_multitarget_regression_metrics(
        path_reg_targets,
        all_path_reg_preds,
        ENTRY_PATH_PATH_REG_TARGETS,
    )

    unknown_pred = sorted({int(label) for label in all_path_cls_preds if int(label) not in ENTRY_PATH_INV_CLASS_MAP})
    unknown_true = sorted({int(label) for label in all_cls_targets if int(label) not in ENTRY_PATH_INV_CLASS_MAP})
    if unknown_pred or unknown_true:
        raise ValueError(
            f'Unsupported entry_path class ids: pred={unknown_pred or "ok"}, true={unknown_true or "ok"}'
        )
    y_pred_orig = np.array([ENTRY_PATH_INV_CLASS_MAP[int(label)] for label in all_path_cls_preds])
    y_true_orig = np.array([ENTRY_PATH_INV_CLASS_MAP[int(label)] for label in all_cls_targets])
    path_cls_metrics = compute_metrics(y_true_orig, y_pred_orig)
    active_mask = all_signals != 0
    if np.any(active_mask):
        active_path_cls_metrics = compute_metrics(y_true_orig[active_mask], y_pred_orig[active_mask])
    else:
        active_path_cls_metrics = {
            'f1_macro': 0.0,
            'f1_per_class': {-1: 0.0, 0: 0.0, 1: 0.0},
        }

    metrics = {
        'ret_pearson_r': ret_metrics['pearson_r'],
        'pearson_r': ret_metrics['pearson_r'],
        'mae': ret_metrics['mae'],
        'rmse': ret_metrics['rmse'],
        'r2': ret_metrics['r2'],
        'ret_metrics': ret_metrics['per_target'],
        'ret_per_target': ret_metrics['per_target'],
        'path_reg_pearson_r': path_reg_metrics['pearson_r'],
        'path_reg_metrics': path_reg_metrics['per_target'],
        'path_reg_per_target': path_reg_metrics['per_target'],
        'path_cls_f1_macro': path_cls_metrics['f1_macro'],
        'path_cls_metrics': path_cls_metrics,
        'path_cls_per_class': path_cls_metrics['f1_per_class'],
        'active_path_cls_f1_macro': active_path_cls_metrics['f1_macro'],
        'active_path_cls_per_class': active_path_cls_metrics['f1_per_class'],
    }

    return total_loss / n_batches, metrics


def _pinball_loss_torch(preds: torch.Tensor, targets: torch.Tensor, quantile: float) -> torch.Tensor:
    diff = targets - preds
    return torch.maximum(quantile * diff, (quantile - 1.0) * diff)


def compute_entry_path_v1_quantile_losses(
    outputs: dict[str, torch.Tensor],
    y_reg_batch: torch.Tensor,
    y_cls_batch: torch.Tensor,
    signal_batch: torch.Tensor,
    ret_loss_fn: nn.Module | None = None,
    path_reg_loss_fn: nn.Module | None = None,
    path_cls_loss_fn: nn.Module | None = None,
) -> dict[str, torch.Tensor | float | int]:
    if ret_loss_fn is None:
        ret_loss_fn = nn.HuberLoss(delta=1.0, reduction='none')
    if path_reg_loss_fn is None:
        path_reg_loss_fn = nn.HuberLoss(delta=1.0)
    if path_cls_loss_fn is None:
        path_cls_loss_fn = nn.CrossEntropyLoss(reduction='none')

    ret_true = y_reg_batch[:, :len(ENTRY_PATH_RET_TARGETS)]
    path_reg_true = y_reg_batch[:, len(ENTRY_PATH_RET_TARGETS):]

    loss_ret = reduce_entry_path_weighted_loss(
        ret_loss_fn(outputs['ret'], ret_true),
        signal_batch,
        active_weight=ENTRY_PATH_ACTIVE_WEIGHT,
    )
    loss_path_cls = reduce_entry_path_weighted_loss(
        path_cls_loss_fn(outputs['path_cls'], y_cls_batch),
        signal_batch,
        active_weight=ENTRY_PATH_PATH_CLS_ACTIVE_WEIGHT,
    )
    loss_path_reg = path_reg_loss_fn(outputs['path_reg'], path_reg_true)

    active_mask = signal_batch != 0 if signal_batch is not None else torch.ones(
        y_reg_batch.size(0), dtype=torch.bool, device=y_reg_batch.device
    )
    true_ret24 = ret_true[:, 2:3]
    if active_mask.any():
        loss_q10_tensor = _pinball_loss_torch(
            outputs['ret_q10'][active_mask],
            true_ret24[active_mask],
            0.1,
        )
        loss_q90_tensor = _pinball_loss_torch(
            outputs['ret_q90'][active_mask],
            true_ret24[active_mask],
            0.9,
        )
        loss_q10 = loss_q10_tensor.mean()
        loss_q90 = loss_q90_tensor.mean()
        active_count = int(active_mask.sum().item())
    else:
        loss_q10 = outputs['ret_q10'].sum() * 0.0
        loss_q90 = outputs['ret_q90'].sum() * 0.0
        active_count = 0

    loss = loss_ret + 0.5 * loss_path_reg + 0.5 * loss_path_cls + 0.5 * (loss_q10 + loss_q90)
    return {
        'loss': loss,
        'loss_ret': float(loss_ret.detach().item()),
        'loss_path_reg': float(loss_path_reg.detach().item()),
        'loss_path_cls': float(loss_path_cls.detach().item()),
        'loss_q10': float(loss_q10.detach().item()),
        'loss_q90': float(loss_q90.detach().item()),
        'active_count': active_count,
    }


def train_one_epoch_entry_path_v1_quantile(
    model: nn.Module,
    train_loader: torch.utils.data.DataLoader,
    ret_loss_fn: nn.Module,
    path_reg_loss_fn: nn.Module,
    path_cls_loss_fn: nn.Module,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
) -> float:
    model.train()
    total_loss = 0.0
    n_batches = 0

    for X_batch, y_reg_batch, y_cls_batch, mask_batch, signal_batch in train_loader:
        X_batch = X_batch.to(device)
        y_reg_batch = y_reg_batch.to(device)
        y_cls_batch = y_cls_batch.to(device)
        mask_batch = mask_batch.to(device)
        signal_batch = signal_batch.to(device)

        optimizer.zero_grad()
        outputs = model(X_batch, mask=mask_batch)
        losses = compute_entry_path_v1_quantile_losses(
            outputs,
            y_reg_batch,
            y_cls_batch,
            signal_batch,
            ret_loss_fn=ret_loss_fn,
            path_reg_loss_fn=path_reg_loss_fn,
            path_cls_loss_fn=path_cls_loss_fn,
        )
        loss = losses['loss']
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()

        total_loss += float(loss.item())
        n_batches += 1

    return total_loss / n_batches


@torch.no_grad()
def validate_entry_path_v1_quantile(
    model: nn.Module,
    val_loader: torch.utils.data.DataLoader,
    ret_loss_fn: nn.Module | None = None,
    path_reg_loss_fn: nn.Module | None = None,
    path_cls_loss_fn: nn.Module | None = None,
    device: torch.device | None = None,
) -> tuple[float, dict]:
    model.eval()
    if device is None:
        device = torch.device('cpu')

    total_loss = 0.0
    n_batches = 0
    all_ret_preds = []
    all_path_reg_preds = []
    all_path_cls_preds = []
    all_q10_preds = []
    all_q90_preds = []
    all_reg_targets = []
    all_cls_targets = []
    all_signals = []

    for X_batch, y_reg_batch, y_cls_batch, mask_batch, signal_batch in val_loader:
        X_batch = X_batch.to(device)
        y_reg_batch = y_reg_batch.to(device)
        y_cls_batch = y_cls_batch.to(device)
        mask_batch = mask_batch.to(device)
        signal_batch = signal_batch.to(device)

        outputs = model(X_batch, mask=mask_batch)
        losses = compute_entry_path_v1_quantile_losses(
            outputs,
            y_reg_batch,
            y_cls_batch,
            signal_batch,
            ret_loss_fn=ret_loss_fn,
            path_reg_loss_fn=path_reg_loss_fn,
            path_cls_loss_fn=path_cls_loss_fn,
        )
        total_loss += float(losses['loss'].item())
        n_batches += 1

        all_ret_preds.append(outputs['ret'].cpu().numpy())
        all_path_reg_preds.append(outputs['path_reg'].cpu().numpy())
        all_path_cls_preds.append(outputs['path_cls'].argmax(dim=1).cpu().numpy())
        all_q10_preds.append(outputs['ret_q10'].cpu().numpy())
        all_q90_preds.append(outputs['ret_q90'].cpu().numpy())
        all_reg_targets.append(y_reg_batch.cpu().numpy())
        all_cls_targets.append(y_cls_batch.cpu().numpy())
        all_signals.append(signal_batch.cpu().numpy())

    all_ret_preds = np.concatenate(all_ret_preds)
    all_path_reg_preds = np.concatenate(all_path_reg_preds)
    all_path_cls_preds = np.concatenate(all_path_cls_preds)
    all_q10_preds = np.concatenate(all_q10_preds)
    all_q90_preds = np.concatenate(all_q90_preds)
    all_reg_targets = np.concatenate(all_reg_targets)
    all_cls_targets = np.concatenate(all_cls_targets)
    all_signals = np.concatenate(all_signals)

    ret_targets = all_reg_targets[:, :len(ENTRY_PATH_RET_TARGETS)]
    path_reg_targets = all_reg_targets[:, len(ENTRY_PATH_RET_TARGETS):]

    ret_metrics = compute_named_multitarget_regression_metrics(
        ret_targets,
        all_ret_preds,
        ENTRY_PATH_RET_TARGETS,
    )
    path_reg_metrics = compute_named_multitarget_regression_metrics(
        path_reg_targets,
        all_path_reg_preds,
        ENTRY_PATH_PATH_REG_TARGETS,
    )

    unknown_pred = sorted({int(label) for label in all_path_cls_preds if int(label) not in ENTRY_PATH_INV_CLASS_MAP})
    unknown_true = sorted({int(label) for label in all_cls_targets if int(label) not in ENTRY_PATH_INV_CLASS_MAP})
    if unknown_pred or unknown_true:
        raise ValueError(
            f'Unsupported entry_path class ids: pred={unknown_pred or "ok"}, true={unknown_true or "ok"}'
        )
    y_pred_orig = np.array([ENTRY_PATH_INV_CLASS_MAP[int(label)] for label in all_path_cls_preds])
    y_true_orig = np.array([ENTRY_PATH_INV_CLASS_MAP[int(label)] for label in all_cls_targets])
    path_cls_metrics = compute_metrics(y_true_orig, y_pred_orig)

    active_mask = all_signals != 0
    if np.any(active_mask):
        active_path_reg_metrics = compute_named_multitarget_regression_metrics(
            path_reg_targets[active_mask],
            all_path_reg_preds[active_mask],
            ENTRY_PATH_PATH_REG_TARGETS,
        )
        active_path_cls_metrics = compute_metrics(y_true_orig[active_mask], y_pred_orig[active_mask])
        quantile_metrics = compute_entry_path_v1_quantile_metrics(
            true_ret=ret_targets[active_mask, 2],
            pred_ret24=all_ret_preds[active_mask, 2],
            pred_q10=all_q10_preds[active_mask, 0],
            pred_q90=all_q90_preds[active_mask, 0],
            path_reg_pearson_r=active_path_reg_metrics['pearson_r'],
            path_cls_f1_macro=active_path_cls_metrics['f1_macro'],
        )
    else:
        active_path_reg_metrics = {
            'pearson_r': 0.0,
            'per_target': {},
        }
        active_path_cls_metrics = {
            'f1_macro': 0.0,
            'f1_per_class': {-1: 0.0, 0: 0.0, 1: 0.0},
        }
        quantile_metrics = {
            'ret_pearson_r': 0.0,
            'interval_coverage': 0.0,
            'median_interval_width': 0.0,
            'coverage_error': 0.0,
            'q10_pinball_loss': 0.0,
            'q90_pinball_loss': 0.0,
            'val_score': 0.0,
        }

    metrics = {
        'ret_pearson_r': ret_metrics['pearson_r'],
        'pearson_r': ret_metrics['pearson_r'],
        'mae': ret_metrics['mae'],
        'rmse': ret_metrics['rmse'],
        'r2': ret_metrics['r2'],
        'ret_metrics': ret_metrics['per_target'],
        'ret_per_target': ret_metrics['per_target'],
        'path_reg_pearson_r': active_path_reg_metrics['pearson_r'],
        'path_reg_metrics': active_path_reg_metrics['per_target'],
        'path_reg_per_target': active_path_reg_metrics['per_target'],
        'path_cls_f1_macro': active_path_cls_metrics['f1_macro'],
        'path_cls_metrics': path_cls_metrics,
        'path_cls_per_class': active_path_cls_metrics['f1_per_class'],
        'active_path_cls_f1_macro': active_path_cls_metrics['f1_macro'],
        'active_path_cls_per_class': active_path_cls_metrics['f1_per_class'],
        'interval_coverage': quantile_metrics['interval_coverage'],
        'median_interval_width': quantile_metrics['median_interval_width'],
        'coverage_error': quantile_metrics['coverage_error'],
        'q10_pinball_loss': quantile_metrics['q10_pinball_loss'],
        'q90_pinball_loss': quantile_metrics['q90_pinball_loss'],
        'val_score': quantile_metrics['val_score'],
    }

    return total_loss / n_batches, metrics


def _pinball_loss_torch(preds: torch.Tensor, targets: torch.Tensor, quantile: float) -> torch.Tensor:
    diff = targets - preds
    return torch.maximum(quantile * diff, (quantile - 1.0) * diff)


def _order_trailing_stop_quantiles(
    pred_q10: np.ndarray,
    pred_q50: np.ndarray,
    pred_q90: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    ordered = np.sort(
        np.stack(
            [
                np.asarray(pred_q10, dtype=np.float64).reshape(-1),
                np.asarray(pred_q50, dtype=np.float64).reshape(-1),
                np.asarray(pred_q90, dtype=np.float64).reshape(-1),
            ],
            axis=1,
        ),
        axis=1,
    )
    return ordered[:, 0], ordered[:, 1], ordered[:, 2]


def compute_trailing_stop_target_quantile_losses(
    outputs: dict[str, torch.Tensor],
    y_batch: torch.Tensor,
) -> dict[str, torch.Tensor | float]:
    target = y_batch.reshape(-1, 1)
    loss_q10 = _pinball_loss_torch(outputs['q10'], target, 0.10).mean()
    loss_q50 = _pinball_loss_torch(outputs['q50'], target, 0.50).mean()
    loss_q90 = _pinball_loss_torch(outputs['q90'], target, 0.90).mean()
    loss = (loss_q10 + loss_q50 + loss_q90) / 3.0
    return {
        'loss': loss,
        'loss_q10': float(loss_q10.detach().item()),
        'loss_q50': float(loss_q50.detach().item()),
        'loss_q90': float(loss_q90.detach().item()),
    }


def train_one_epoch_trailing_stop_target_quantile(
    model: nn.Module,
    train_loader: torch.utils.data.DataLoader,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
) -> float:
    model.train()
    total_loss = 0.0
    n_batches = 0

    for X_batch, y_batch, mask_batch in train_loader:
        X_batch = X_batch.to(device)
        y_batch = y_batch.to(device)
        mask_batch = mask_batch.to(device)

        optimizer.zero_grad()
        outputs = model(X_batch, mask=mask_batch)
        losses = compute_trailing_stop_target_quantile_losses(outputs, y_batch)
        loss = losses['loss']
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()

        total_loss += float(loss.item())
        n_batches += 1

    return total_loss / n_batches


@torch.no_grad()
def validate_trailing_stop_target_quantile(
    model: nn.Module,
    val_loader: torch.utils.data.DataLoader,
    device: torch.device,
) -> tuple[float, dict]:
    model.eval()
    total_loss = 0.0
    n_batches = 0
    all_targets = []
    all_q10 = []
    all_q50 = []
    all_q90 = []

    for X_batch, y_batch, mask_batch in val_loader:
        X_batch = X_batch.to(device)
        y_batch = y_batch.to(device)
        mask_batch = mask_batch.to(device)

        outputs = model(X_batch, mask=mask_batch)
        losses = compute_trailing_stop_target_quantile_losses(outputs, y_batch)
        total_loss += float(losses['loss'].item())
        n_batches += 1

        all_targets.append(y_batch.cpu().numpy())
        all_q10.append(outputs['q10'].cpu().numpy())
        all_q50.append(outputs['q50'].cpu().numpy())
        all_q90.append(outputs['q90'].cpu().numpy())

    true_target = np.concatenate(all_targets).reshape(-1)
    pred_q10, pred_q50, pred_q90 = _order_trailing_stop_quantiles(
        np.concatenate(all_q10),
        np.concatenate(all_q50),
        np.concatenate(all_q90),
    )

    metrics = compute_trailing_stop_quantile_metrics(
        true_target=true_target,
        pred_q10=pred_q10,
        pred_q50=pred_q50,
        pred_q90=pred_q90,
    )
    metrics['val_score'] = metrics['q50_pearson_r']
    return total_loss / n_batches, metrics


def train_one_epoch_take_skip(
    model: nn.Module,
    train_loader: torch.utils.data.DataLoader,
    loss_fn: nn.Module,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
) -> float:
    """Train one epoch for multi-label take/skip classification."""
    model.train()
    total_loss = 0.0
    n_batches = 0

    for X_batch, y_batch, mask_batch in train_loader:
        X_batch = X_batch.to(device)
        y_batch = y_batch.to(device).float()
        mask_batch = mask_batch.to(device)

        optimizer.zero_grad()
        logits = model(X_batch, mask=mask_batch)
        loss = loss_fn(logits, y_batch)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()

        total_loss += float(loss.item())
        n_batches += 1

    return total_loss / max(1, n_batches)


@torch.no_grad()
def validate_take_skip(
    model: nn.Module,
    val_loader: torch.utils.data.DataLoader,
    loss_fn: nn.Module,
    device: torch.device,
) -> tuple[float, dict]:
    """Validate multi-label take/skip task using sigmoid probabilities."""
    model.eval()
    total_loss = 0.0
    n_batches = 0
    y_true_parts = []
    y_prob_parts = []

    for X_batch, y_batch, mask_batch in val_loader:
        X_batch = X_batch.to(device)
        y_batch = y_batch.to(device).float()
        mask_batch = mask_batch.to(device)

        logits = model(X_batch, mask=mask_batch)
        loss = loss_fn(logits, y_batch)
        total_loss += float(loss.item())
        n_batches += 1

        y_true_parts.append(y_batch.cpu().numpy())
        y_prob_parts.append(torch.sigmoid(logits).cpu().numpy())

    metrics = compute_take_skip_metrics(np.vstack(y_true_parts), np.vstack(y_prob_parts))
    metrics['val_score'] = -metrics['bce']
    return total_loss / max(1, n_batches), metrics


def resolve_model_kwargs_for_encoder_transfer(
    model_kwargs: dict | None,
    encoder_model_kwargs: dict | None,
) -> dict:
    resolved = dict(encoder_model_kwargs or {})
    if model_kwargs:
        resolved.update(model_kwargs)
    return resolved


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
    # Asymmetric Loss параметры (regression)
    regression_loss: str = 'huber',
    asym_over_penalty: float = 1.0,
    asym_under_penalty: float = 10.0,
    # Scheduler параметры
    scheduler_patience: int = DEFAULTS['scheduler_patience'],
    scheduler_factor: float = DEFAULTS['scheduler_factor'],
    # Metrique mode для classification
    metric_mode: str = 'f1_macro',
    min_signal_recall: float = 0.3,
    use_weighted_sampler: bool = False,
    seq_len: int = 20,
    # Гиперпараметры архитектуры модели
    model_kwargs: dict | None = None,
    # Optuna Pruning
    trial=None,
    # Режим без вывода в консоль (для Optuna)
    silent: bool = False,
    # Очистка кэша
    clear_cache: bool = False,
    # Transfer learning: загрузить encoder из другого checkpoint
    encoder_ckpt: str | None = None,
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
        model_kwargs: Дополнительные гиперпараметры архитектуры модели
        trial: Optuna trial объект для Pruning (опционально)
        silent: Если True — минимальный вывод в консоль

    Возвращает:
        Словарь с результатами обучения:
        - model_name, task, best_metric, best_epoch, num_parameters,
          training_time, history, best_metrics
    """
    binary_classification = (task in BINARY_CLASSIFICATION_TARGETS)
    multi_target = (task == 'regression_updn')
    triple_barrier = (task == 'triple_barrier')
    entry_path = (task == ENTRY_PATH_TARGET)
    entry_path_quantile = (task == ENTRY_PATH_V1_QUANTILE_TARGET)
    entry_path_like = entry_path or entry_path_quantile
    trailing_stop = (task == TRAILING_STOP_TARGET)
    trailing_stop_quantile = (task == TRAILING_STOP_TARGET_QUANTILE_TARGET)
    take_skip_trailing_stop = (task == TAKE_SKIP_TRAILING_STOP_TARGET)
    regression = (task in ['regression', TRADE_PNL_TARGET]) or multi_target or trailing_stop

    if entry_path and model_name not in ENTRY_PATH_MODEL_NAMES:
        supported = ', '.join(ENTRY_PATH_MODEL_NAMES)
        raise ValueError(f'{ENTRY_PATH_TARGET} supports only models: {supported}')
    if entry_path_quantile and model_name != 'transformer':
        raise ValueError(f'{ENTRY_PATH_V1_QUANTILE_TARGET} supports only model=transformer')
    if trailing_stop_quantile and model_name != 'transformer':
        raise ValueError(f'{TRAILING_STOP_TARGET_QUANTILE_TARGET} supports only model=transformer')
    if take_skip_trailing_stop and model_name != 'transformer':
        raise ValueError(f'{TAKE_SKIP_TRAILING_STOP_TARGET} supports only model=transformer')

    # ── Setup ────────────────────────────────────────────────────────────────
    set_seed(seed)
    device = get_device()

    CHECKPOINTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # ── Данные ───────────────────────────────────────────────────────────────
    target_col = ENTRY_PATH_V1_QUANTILE_TARGET if entry_path_quantile else task_target_column(task)
    train_loader, val_loader, scaler = create_data_loaders(
        batch_size=batch_size,
        target=target_col,
        use_scaler=use_scaler,
        use_weighted_sampler=use_weighted_sampler if not (regression or triple_barrier or trailing_stop_quantile or take_skip_trailing_stop) else False,
        seq_len=seq_len,
        clear_cache=clear_cache,
    )

    # ── Модель ───────────────────────────────────────────────────────────────
    src_ckpt = None
    if model_kwargs is None:
        model_kwargs = {}
    else:
        model_kwargs = dict(model_kwargs)

    if encoder_ckpt:
        src_ckpt = torch.load(encoder_ckpt, map_location=device, weights_only=False)
        model_kwargs = resolve_model_kwargs_for_encoder_transfer(
            model_kwargs=model_kwargs,
            encoder_model_kwargs=src_ckpt.get('model_kwargs', {}),
        )

    # Multi-target: 6 выходов; single regression: 1 выход; classification: 3 выхода
    if triple_barrier:
        num_classes = len(TB_TARGET_NAMES)  # 12
    elif entry_path_like:
        num_classes = len(ENTRY_PATH_INV_CLASS_MAP)
    elif multi_target:
        num_classes = len(UPDN_TARGETS)     # 6
    elif trailing_stop:
        num_classes = len(TRAILING_STOP_TARGET_COLUMNS)
    elif trailing_stop_quantile:
        num_classes = 1
    elif take_skip_trailing_stop:
        num_classes = len(TAKE_SKIP_TRAILING_STOP_COLUMNS)
    elif regression:
        num_classes = 1
    elif binary_classification:
        num_classes = 2
    else:
        num_classes = 3
    model_kwargs.setdefault('input_features', N_FRACTAL_FEATURES)
    if entry_path:
        model_kwargs.setdefault('seq_len', seq_len)
        model_kwargs.setdefault('engineered_feature_dim', len(ENTRY_PATH_V1_FEATURE_COLUMNS))
    if entry_path:
        model = build_entry_path_model(model_name, model_kwargs)
    elif entry_path_quantile:
        model = EntryPathV1QuantileTransformer(**model_kwargs)
    elif trailing_stop_quantile:
        model = TrailingStopTargetQuantileTransformer(**model_kwargs)
    else:
        model = get_model(model_name, num_classes=num_classes, **model_kwargs)
    model = model.to(device)

    # ── Transfer learning: загрузка encoder из другого checkpoint ────────────
    if encoder_ckpt and src_ckpt is not None:
        src_state = src_ckpt['model_state_dict']
        dst_state = model.state_dict()
        encoder_parts = ('input_projection', 'pos_encoding', 'transformer_encoder', 'cls_token')
        copied = 0
        for key, val in src_state.items():
            if key.startswith(encoder_parts) and key in dst_state and dst_state[key].shape == val.shape:
                dst_state[key] = val
                copied += 1
        model.load_state_dict(dst_state)
        if not silent:
            print(f"  🔁 Transfer learning: загружено {copied} слоёв из {encoder_ckpt}")

    n_params = count_parameters(model)

    if not silent:
        print(f"\n{'═' * 60}")
        print(f"  Модель: {model_name.upper()}  |  Задача: {task.upper()}")
        print(f"  Параметров: {n_params:,}")
        print(f"{'═' * 60}")

    # ── Loss, Optimizer, Scheduler ───────────────────────────────────────────
    if triple_barrier:
        # Compute pos_weight from training data for class imbalance
        y_train_all = []
        for batch in train_loader:
            y_train_all.append(batch[1].numpy())
        y_train_np = np.concatenate(y_train_all)
        n_pos = (y_train_np == 1).sum(axis=0).astype(float)
        n_neg = (y_train_np == 0).sum(axis=0).astype(float)
        pos_weight = torch.tensor(n_neg / (n_pos + 1e-6), dtype=torch.float32).to(device)
        loss_fn = nn.BCEWithLogitsLoss(pos_weight=pos_weight).to(device)
    elif binary_classification:
        y_train_all = []
        for batch in train_loader:
            y_train_all.append(batch[1].numpy())
        y_train_np = np.concatenate(y_train_all).astype(np.int64)
        class_counts = np.bincount(y_train_np, minlength=2).astype(float)
        class_weights = class_counts.sum() / (2.0 * np.maximum(class_counts, 1.0))
        weight = torch.tensor(class_weights, dtype=torch.float32).to(device)
        loss_fn = nn.CrossEntropyLoss(weight=weight).to(device)
    elif entry_path:
        ret_loss_fn = HuberLoss(delta=huber_delta, reduction='none').to(device)
        path_reg_loss_fn = HuberLoss(delta=huber_delta).to(device)
        path_cls_loss_fn = nn.CrossEntropyLoss(reduction='none').to(device)
    elif entry_path_quantile:
        ret_loss_fn = HuberLoss(delta=huber_delta, reduction='none').to(device)
        path_reg_loss_fn = HuberLoss(delta=huber_delta).to(device)
        path_cls_loss_fn = nn.CrossEntropyLoss(reduction='none').to(device)
    elif trailing_stop_quantile:
        loss_fn = None
    elif take_skip_trailing_stop:
        loss_fn = nn.BCEWithLogitsLoss().to(device)
    elif regression:
        if regression_loss == 'directional':
            loss_fn = DirectionalAsymmetricLoss(
                alpha=asym_over_penalty,  # reuse param as alpha
            ).to(device)
        elif regression_loss == 'asymmetric':
            loss_fn = AsymmetricLoss(
                over_penalty=asym_over_penalty,
                under_penalty=asym_under_penalty
            ).to(device)
        else:
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
    if triple_barrier:
        history = {
            'train_loss': [], 'val_loss': [],
            'val_mean_auc': [], 'lr': [],
        }
        metric_name = 'mean_auc'
        if not silent:
            print(f"\n{'Epoch':>5} | {'Train Loss':>10} | {'Val Loss':>10} | "
                  f"{'Mean AUC':>10} | {'LR':>10}")
    elif binary_classification:
        history = {
            'train_loss': [], 'val_loss': [],
            'val_auc': [], 'val_precision': [], 'val_recall': [], 'lr': [],
        }
        metric_name = 'auc'
        if not silent:
            print(f"\n{'Epoch':>5} | {'Train Loss':>10} | {'Val Loss':>10} | "
                  f"{'AUC':>8} | {'Prec':>8} | {'Recall':>8} | {'LR':>10}")
    elif entry_path:
        history = {
            'train_loss': [], 'val_loss': [],
            'val_pearson_r': [], 'val_mae': [], 'val_rmse': [],
            'val_r2': [], 'val_path_reg_pearson_r': [],
            'val_path_cls_f1_macro': [], 'val_active_path_cls_f1_macro': [], 'lr': [],
        }
        metric_name = 'ret_pearson_r'
        if not silent:
            print(f"\n{'Epoch':>5} | {'Train Loss':>10} | {'Val Loss':>10} | "
                  f"{'ret_r':>10} | {'path_r':>10} | {'cls_f1':>8} | {'LR':>10}")
    elif entry_path_quantile:
        history = {
            'train_loss': [], 'val_loss': [],
            'val_score': [], 'val_pearson_r': [], 'val_mae': [], 'val_rmse': [],
            'val_r2': [], 'val_path_reg_pearson_r': [], 'val_path_cls_f1_macro': [],
            'val_active_path_cls_f1_macro': [], 'val_interval_coverage': [],
            'val_median_interval_width': [], 'val_q10_pinball_loss': [],
            'val_q90_pinball_loss': [], 'lr': [],
        }
        metric_name = 'val_score'
        if not silent:
            print(f"\n{'Epoch':>5} | {'Train Loss':>10} | {'Val Loss':>10} | "
                  f"{'val_score':>10} | {'path_r':>10} | {'cls_f1':>8} | {'LR':>10}")
    elif trailing_stop_quantile:
        history = {
            'train_loss': [], 'val_loss': [],
            'val_score': [], 'val_q50_pearson_r': [], 'val_q50_mae': [],
            'val_interval_coverage': [], 'val_median_interval_width': [],
            'val_q10_pinball_loss': [], 'val_q50_pinball_loss': [], 'val_q90_pinball_loss': [],
            'lr': [],
        }
        metric_name = 'val_score'
        if not silent:
            print(f"\n{'Epoch':>5} | {'Train Loss':>10} | {'Val Loss':>10} | "
                  f"{'val_score':>10} | {'q50_r':>10} | {'coverage':>10} | {'LR':>10}")
    elif take_skip_trailing_stop:
        history = {
            'train_loss': [], 'val_loss': [],
            'val_score': [], 'val_bce': [], 'lr': [],
        }
        metric_name = 'val_score'
        if not silent:
            print(f"\n{'Epoch':>5} | {'Train Loss':>10} | {'Val Loss':>10} | "
                  f"{'val_score':>10} | {'BCE':>10} | {'LR':>10}")
    elif regression:
        history = {
            'train_loss': [], 'val_loss': [],
            'val_pearson_r': [], 'val_mae': [], 'val_rmse': [],
            'val_r2': [], 'lr': [],
        }
        metric_name = 'pearson_r'
        if not silent:
            print(f"\n{'Epoch':>5} | {'Train Loss':>10} | {'Val Loss':>10} | "
                  f"{'pearson_r':>10} | {'MAE':>8} | {'RMSE':>8} | {'LR':>10}")
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
        if entry_path:
            train_loss = train_one_epoch_entry_path(
                model,
                train_loader,
                ret_loss_fn,
                path_reg_loss_fn,
                path_cls_loss_fn,
                optimizer,
                device,
            )
        elif entry_path_quantile:
            train_loss = train_one_epoch_entry_path_v1_quantile(
                model,
                train_loader,
                ret_loss_fn,
                path_reg_loss_fn,
                path_cls_loss_fn,
                optimizer,
                device,
            )
        elif trailing_stop_quantile:
            train_loss = train_one_epoch_trailing_stop_target_quantile(
                model,
                train_loader,
                optimizer,
                device,
            )
        elif take_skip_trailing_stop:
            train_loss = train_one_epoch_take_skip(
                model,
                train_loader,
                loss_fn,
                optimizer,
                device,
            )
        else:
            train_loss = train_one_epoch(
                model, train_loader, loss_fn, optimizer, device,
                regression=(regression or triple_barrier),
            )

        # Validate
        if triple_barrier:
            val_loss, metrics = validate_triple_barrier(model, val_loader, loss_fn, device)
            val_metric = metrics['mean_auc']

            history['train_loss'].append(train_loss)
            history['val_loss'].append(val_loss)
            history['val_mean_auc'].append(metrics['mean_auc'])
            history['lr'].append(optimizer.param_groups[0]['lr'])

            if not silent:
                print(f"{epoch:>5} | {train_loss:>10.4f} | {val_loss:>10.4f} | "
                      f"{metrics['mean_auc']:>10.4f} | "
                      f"{optimizer.param_groups[0]['lr']:>10.6f}")
        elif binary_classification:
            val_loss, metrics = validate_binary(model, val_loader, loss_fn, device)
            val_metric = metrics['auc']

            history['train_loss'].append(train_loss)
            history['val_loss'].append(val_loss)
            history['val_auc'].append(metrics['auc'])
            history['val_precision'].append(metrics['precision'])
            history['val_recall'].append(metrics['recall'])
            history['lr'].append(optimizer.param_groups[0]['lr'])

            if not silent:
                print(f"{epoch:>5} | {train_loss:>10.4f} | {val_loss:>10.4f} | "
                      f"{metrics['auc']:>8.4f} | {metrics['precision']:>8.4f} | "
                      f"{metrics['recall']:>8.4f} | {optimizer.param_groups[0]['lr']:>10.6f}")
        elif entry_path:
            val_loss, metrics = validate_entry_path(
                model,
                val_loader,
                ret_loss_fn,
                path_reg_loss_fn,
                path_cls_loss_fn,
                device,
            )
            val_metric = metrics['ret_pearson_r']

            history['train_loss'].append(train_loss)
            history['val_loss'].append(val_loss)
            history['val_pearson_r'].append(metrics['ret_pearson_r'])
            history['val_mae'].append(metrics['mae'])
            history['val_rmse'].append(metrics['rmse'])
            history['val_r2'].append(metrics['r2'])
            history['val_path_reg_pearson_r'].append(metrics['path_reg_pearson_r'])
            history['val_path_cls_f1_macro'].append(metrics['path_cls_f1_macro'])
            history['val_active_path_cls_f1_macro'].append(metrics['active_path_cls_f1_macro'])
            history['lr'].append(optimizer.param_groups[0]['lr'])

            current_lr = optimizer.param_groups[0]['lr']
            if not silent:
                print(f"{epoch:>5} | {train_loss:>10.4f} | {val_loss:>10.4f} | "
                      f"{metrics['ret_pearson_r']:>10.4f} | {metrics['path_reg_pearson_r']:>10.4f} | "
                      f"{metrics['path_cls_f1_macro']:>8.4f} | {current_lr:>10.6f}")
        elif entry_path_quantile:
            val_loss, metrics = validate_entry_path_v1_quantile(
                model,
                val_loader,
                ret_loss_fn,
                path_reg_loss_fn,
                path_cls_loss_fn,
                device,
            )
            val_metric = metrics['val_score']

            history['train_loss'].append(train_loss)
            history['val_loss'].append(val_loss)
            history['val_score'].append(metrics['val_score'])
            history['val_pearson_r'].append(metrics['ret_pearson_r'])
            history['val_mae'].append(metrics['mae'])
            history['val_rmse'].append(metrics['rmse'])
            history['val_r2'].append(metrics['r2'])
            history['val_path_reg_pearson_r'].append(metrics['path_reg_pearson_r'])
            history['val_path_cls_f1_macro'].append(metrics['path_cls_f1_macro'])
            history['val_active_path_cls_f1_macro'].append(metrics.get('active_path_cls_f1_macro', 0.0))
            history['val_interval_coverage'].append(metrics.get('interval_coverage', 0.0))
            history['val_median_interval_width'].append(metrics.get('median_interval_width', 0.0))
            history['val_q10_pinball_loss'].append(metrics.get('q10_pinball_loss', 0.0))
            history['val_q90_pinball_loss'].append(metrics.get('q90_pinball_loss', 0.0))
            history['lr'].append(optimizer.param_groups[0]['lr'])

            current_lr = optimizer.param_groups[0]['lr']
            if not silent:
                print(f"{epoch:>5} | {train_loss:>10.4f} | {val_loss:>10.4f} | "
                      f"{metrics['val_score']:>10.4f} | {metrics['path_reg_pearson_r']:>10.4f} | "
                      f"{metrics['path_cls_f1_macro']:>8.4f} | {current_lr:>10.6f}")
        elif trailing_stop_quantile:
            val_loss, metrics = validate_trailing_stop_target_quantile(
                model,
                val_loader,
                device,
            )
            val_metric = metrics['val_score']

            history['train_loss'].append(train_loss)
            history['val_loss'].append(val_loss)
            history['val_score'].append(metrics['val_score'])
            history['val_q50_pearson_r'].append(metrics['q50_pearson_r'])
            history['val_q50_mae'].append(metrics['q50_mae'])
            history['val_interval_coverage'].append(metrics['interval_coverage'])
            history['val_median_interval_width'].append(metrics['median_interval_width'])
            history['val_q10_pinball_loss'].append(metrics['q10_pinball_loss'])
            history['val_q50_pinball_loss'].append(metrics['q50_pinball_loss'])
            history['val_q90_pinball_loss'].append(metrics['q90_pinball_loss'])
            history['lr'].append(optimizer.param_groups[0]['lr'])

            current_lr = optimizer.param_groups[0]['lr']
            if not silent:
                print(f"{epoch:>5} | {train_loss:>10.4f} | {val_loss:>10.4f} | "
                      f"{metrics['val_score']:>10.4f} | {metrics['q50_pearson_r']:>10.4f} | "
                      f"{metrics['interval_coverage']:>10.4f} | {current_lr:>10.6f}")
        elif take_skip_trailing_stop:
            val_loss, metrics = validate_take_skip(model, val_loader, loss_fn, device)
            val_metric = metrics['val_score']

            history['train_loss'].append(train_loss)
            history['val_loss'].append(val_loss)
            history['val_score'].append(metrics['val_score'])
            history['val_bce'].append(metrics['bce'])
            history['lr'].append(optimizer.param_groups[0]['lr'])

            current_lr = optimizer.param_groups[0]['lr']
            if not silent:
                print(f"{epoch:>5} | {train_loss:>10.4f} | {val_loss:>10.4f} | "
                      f"{metrics['val_score']:>10.4f} | {metrics['bce']:>10.4f} | {current_lr:>10.6f}")
        elif regression:
            val_loss, metrics = validate_regression(
                model,
                val_loader,
                loss_fn,
                device,
                target_names=TRAILING_STOP_TARGET_COLUMNS if trailing_stop else None,
            )
            val_metric = metrics['pearson_r']

            history['train_loss'].append(train_loss)
            history['val_loss'].append(val_loss)
            history['val_pearson_r'].append(metrics['pearson_r'])
            history['val_mae'].append(metrics['mae'])
            history['val_rmse'].append(metrics['rmse'])
            history['val_r2'].append(metrics['r2'])
            history['lr'].append(optimizer.param_groups[0]['lr'])

            current_lr = optimizer.param_groups[0]['lr']
            if not silent:
                print(f"{epoch:>5} | {train_loss:>10.4f} | {val_loss:>10.4f} | "
                      f"{metrics['pearson_r']:>10.4f} | {metrics['mae']:>8.4f} | "
                      f"{metrics['rmse']:>8.4f} | "
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
        if not np.isfinite(val_metric):
            val_metric = -1.0
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

            # Суффикс чекпойнта
            suffix = task_checkpoint_suffix(task)
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
                'seq_len': seq_len,
                'model_kwargs': model_kwargs,
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

        if triple_barrier:
            print(f"  Mean AUC: {best_metrics.get('mean_auc', 0):.4f}")
            if 'per_target' in best_metrics:
                for name, tm in best_metrics['per_target'].items():
                    print(f"    {name}: AUC={tm['auc']:.4f}, pos_rate={tm['pos_rate']:.1%}")
        elif binary_classification:
            print(f"  AUC:       {best_metrics.get('auc', 0):.4f}")
            print(f"  Precision: {best_metrics.get('precision', 0):.4f}")
            print(f"  Recall:    {best_metrics.get('recall', 0):.4f}")
            print(f"  F1:        {best_metrics.get('f1', 0):.4f}")
        elif trailing_stop_quantile:
            print(f"  Val score: {best_metrics.get('val_score', 0):.4f}")
            print(f"  Q50 Pearson r: {best_metrics.get('q50_pearson_r', 0):.4f}")
            print(f"  Q50 MAE: {best_metrics.get('q50_mae', 0):.4f}")
            print(f"  Interval coverage: {best_metrics.get('interval_coverage', 0):.4f}")
            print(f"  Median interval width: {best_metrics.get('median_interval_width', 0):.4f}")
        elif take_skip_trailing_stop:
            print(f"  Val score: {best_metrics.get('val_score', 0):.4f}")
            print(f"  BCE: {best_metrics.get('bce', 0):.4f}")
        elif not regression and not entry_path:
            print(f"\n{best_metrics.get('classification_report', '')}")
        else:
            print(f"  MAE:  {best_metrics.get('mae', 0):.4f}")
            print(f"  RMSE: {best_metrics.get('rmse', 0):.4f}")
            print(f"  R²:   {best_metrics.get('r2', 0):.4f}")
        if entry_path:
            print(f"  Ret Pearson r: {best_metrics.get('ret_pearson_r', 0):.4f}")
            print(f"  PathReg Pearson r: {best_metrics.get('path_reg_pearson_r', 0):.4f}")
            print(f"  PathCls F1 macro: {best_metrics.get('path_cls_f1_macro', 0):.4f}")
            print(f"  Active PathCls F1 macro: {best_metrics.get('active_path_cls_f1_macro', 0):.4f}")
            if 'ret_per_target' in best_metrics:
                print(f"\n  Return-head Pearson r:")
                for tname, tm in best_metrics['ret_per_target'].items():
                    print(f"    {tname:16s}: r={tm['pearson_r']:.4f}  MAE={tm['mae']:.4f}")
            if 'path_reg_per_target' in best_metrics:
                print(f"\n  Path-reg Pearson r:")
                for tname, tm in best_metrics['path_reg_per_target'].items():
                    print(f"    {tname:16s}: r={tm['pearson_r']:.4f}  MAE={tm['mae']:.4f}")
        elif entry_path_quantile:
            print(f"  Val score: {best_metrics.get('val_score', 0):.4f}")
            print(f"  Ret Pearson r: {best_metrics.get('ret_pearson_r', 0):.4f}")
            print(f"  PathReg Pearson r: {best_metrics.get('path_reg_pearson_r', 0):.4f}")
            print(f"  PathCls F1 macro: {best_metrics.get('path_cls_f1_macro', 0):.4f}")
            print(f"  Active PathCls F1 macro: {best_metrics.get('active_path_cls_f1_macro', 0):.4f}")
            print(f"  Interval coverage: {best_metrics.get('interval_coverage', 0):.4f}")
            print(f"  Median interval width: {best_metrics.get('median_interval_width', 0):.4f}")
        elif 'per_target' in best_metrics:
            print(f"\n  Per-target Pearson r:")
            for tname, tm in best_metrics['per_target'].items():
                print(f"    {tname:8s}: r={tm['pearson_r']:.4f}  MAE={tm['mae']:.4f}")

    # ── Plots (только если не silent) ────────────────────────────────────────
    if not silent:
        _plot_training_curves(
            history,
            model_name,
            task=task,
            regression=(regression or entry_path_like),
            binary_classification=binary_classification,
        )

        if triple_barrier:
            pass  # No confusion matrix for TB — just training curves
        elif binary_classification:
            _plot_confusion_matrix(
                best_metrics['confusion_matrix'],
                model_name,
                labels=['Bad (0)', 'Good (1)'],
                task=task,
            )
        elif entry_path or entry_path_quantile or trailing_stop_quantile or take_skip_trailing_stop:
            pass
        elif regression:
            # Для scatter нужны предсказания на val — пересчитываем
            all_preds, all_targets = _collect_regression_preds(model, val_loader, device)
            _plot_regression_results(all_targets, all_preds, model_name, task=task)
        else:
            _plot_confusion_matrix(best_metrics['confusion_matrix'], model_name, task=task)

    # Логируем эксперимент в CSV
    _log_experiment(
        model_name=model_name,
        task=task,
        epochs=epochs,
        batch_size=batch_size,
        lr=lr,
        weight_decay=weight_decay,
        patience=patience,
        seed=seed,
        scheduler_patience=scheduler_patience,
        scheduler_factor=scheduler_factor,
        focal_alpha=focal_alpha if focal_alpha is not None else DEFAULTS['alpha'],
        focal_gamma=focal_gamma,
        huber_delta=huber_delta,
        use_scaler=use_scaler,
        use_weighted_sampler=use_weighted_sampler,
        n_params=n_params,
        result={
            'model_name': model_name,
            'task': task,
            'best_metric': best_metric,
            'metric_name': metric_name,
            'best_epoch': best_epoch,
            'num_parameters': n_params,
            'training_time': training_time,
            'history': history,
            'best_metrics': best_metrics,
        },
        regression=(regression or entry_path_like),
        triple_barrier=triple_barrier,
        binary_classification=binary_classification,
        model_kwargs=model_kwargs,
    )

    if triple_barrier:
        best_ckpt_path = CHECKPOINTS_DIR / f'{model_name}_tb_best.pt'
        if best_ckpt_path.exists():
            best_ckpt = torch.load(best_ckpt_path, map_location=device, weights_only=False)
            model.load_state_dict(best_ckpt['model_state_dict'])

        val_logits, val_targets = _collect_tb_logits(model, val_loader, device)
        val_proba = 1.0 / (1.0 + np.exp(-val_logits))

        logits_path = REPORTS_DIR / 'tb_validation_logits.npy'
        targets_path = REPORTS_DIR / 'tb_validation_targets.npy'
        calibrator_path = REPORTS_DIR / 'tb_probability_calibrator.joblib'

        np.save(logits_path, val_logits)
        np.save(targets_path, val_targets)

        calibrator_bundle = fit_tb_probability_calibrator(
            y_pred_proba=val_proba,
            y_true=val_targets,
            target_names=TB_TARGET_NAMES,
        )
        save_tb_probability_calibrator(calibrator_bundle, calibrator_path)

        if not silent:
            print(f"  🛡️  TB calibration saved: {calibrator_path.name}")
            print(f"  📦 Validation logits: {logits_path.name}")
            print(f"  📦 Validation targets: {targets_path.name}")

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


def _log_experiment(
    model_name: str,
    task: str,
    epochs: int,
    batch_size: int,
    lr: float,
    weight_decay: float,
    patience: int,
    seed: int,
    scheduler_patience: int,
    scheduler_factor: float,
    focal_alpha: list[float] | None,
    focal_gamma: float | None,
    huber_delta: float | None,
    use_scaler: bool,
    use_weighted_sampler: bool,
    n_params: int,
    result: dict,
    regression: bool,
    triple_barrier: bool = False,
    binary_classification: bool = False,
    model_kwargs: dict | None = None,
) -> None:
    """Логирует эксперимент в CSV файл."""
    from ML.experiment_logger import CSVExperimentLogger
    
    # Строим config_dict
    config_dict = {
        'model': model_name,
        'task': task,
        'seed': seed,
        'epochs': epochs,
        'batch_size': batch_size,
        'lr': lr,
        'weight_decay': weight_decay,
        'patience': patience,
        'scheduler_patience': scheduler_patience,
        'scheduler_factor': scheduler_factor,
        'focal_weights': focal_alpha if not (regression or binary_classification) else None,
        'focal_gamma': focal_gamma if not (regression or binary_classification) else None,
        'huber_delta': huber_delta if regression else None,
        'use_scaler': use_scaler,
        'use_weighted_sampler': use_weighted_sampler,
        'num_parameters': n_params,
    }
    
    if model_kwargs:
        config_dict.update(model_kwargs)
    
    # Строим metrics_dict
    metrics_dict = {
        'metric_name': result.get(
            'metric_name',
            'auc' if binary_classification else ('f1_macro' if not regression else 'pearson_r'),
        ),
        'best_metric': result['best_metric'],
        'best_epoch': result['best_epoch'],
        'training_time': result['training_time'],
    }
    
    if triple_barrier:
        metrics_dict['val_mean_auc'] = result['best_metrics'].get('mean_auc')
    elif binary_classification:
        metrics_dict['val_auc'] = result['best_metrics'].get('auc')
        metrics_dict['precision'] = result['best_metrics'].get('precision')
        metrics_dict['recall'] = result['best_metrics'].get('recall')
        metrics_dict['f1'] = result['best_metrics'].get('f1')
    elif task == ENTRY_PATH_TARGET:
        metrics_dict['ret_pearson_r'] = result['best_metrics'].get('ret_pearson_r')
        metrics_dict['mae'] = result['best_metrics'].get('mae')
        metrics_dict['rmse'] = result['best_metrics'].get('rmse')
        metrics_dict['r2'] = result['best_metrics'].get('r2')
        metrics_dict['path_reg_pearson_r'] = result['best_metrics'].get('path_reg_pearson_r')
        metrics_dict['path_cls_f1_macro'] = result['best_metrics'].get('path_cls_f1_macro')
    elif task == ENTRY_PATH_V1_QUANTILE_TARGET:
        metrics_dict['val_score'] = result['best_metrics'].get('val_score')
        metrics_dict['ret_pearson_r'] = result['best_metrics'].get('ret_pearson_r')
        metrics_dict['mae'] = result['best_metrics'].get('mae')
        metrics_dict['rmse'] = result['best_metrics'].get('rmse')
        metrics_dict['r2'] = result['best_metrics'].get('r2')
        metrics_dict['path_reg_pearson_r'] = result['best_metrics'].get('path_reg_pearson_r')
        metrics_dict['path_cls_f1_macro'] = result['best_metrics'].get('path_cls_f1_macro')
        metrics_dict['active_path_cls_f1_macro'] = result['best_metrics'].get('active_path_cls_f1_macro')
        metrics_dict['interval_coverage'] = result['best_metrics'].get('interval_coverage')
        metrics_dict['median_interval_width'] = result['best_metrics'].get('median_interval_width')
        metrics_dict['q10_pinball_loss'] = result['best_metrics'].get('q10_pinball_loss')
        metrics_dict['q90_pinball_loss'] = result['best_metrics'].get('q90_pinball_loss')
    elif task == TRAILING_STOP_TARGET_QUANTILE_TARGET:
        metrics_dict['val_score'] = result['best_metrics'].get('val_score')
        metrics_dict['q50_pearson_r'] = result['best_metrics'].get('q50_pearson_r')
        metrics_dict['q50_mae'] = result['best_metrics'].get('q50_mae')
        metrics_dict['interval_coverage'] = result['best_metrics'].get('interval_coverage')
        metrics_dict['median_interval_width'] = result['best_metrics'].get('median_interval_width')
        metrics_dict['q10_pinball_loss'] = result['best_metrics'].get('q10_pinball_loss')
        metrics_dict['q50_pinball_loss'] = result['best_metrics'].get('q50_pinball_loss')
        metrics_dict['q90_pinball_loss'] = result['best_metrics'].get('q90_pinball_loss')
    elif task == TAKE_SKIP_TRAILING_STOP_TARGET:
        metrics_dict['val_score'] = result['best_metrics'].get('val_score')
        metrics_dict['bce'] = result['best_metrics'].get('bce')
    elif regression:
        metrics_dict['mae'] = result['best_metrics'].get('mae')
        metrics_dict['rmse'] = result['best_metrics'].get('rmse')
        metrics_dict['r2'] = result['best_metrics'].get('r2')
    else:
        metrics_dict['f1_macro'] = result['best_metric']
        f1_per_class = result['best_metrics'].get('f1_per_class', {})
        metrics_dict['f1_sell'] = f1_per_class.get(-1)
        metrics_dict['f1_neutral'] = f1_per_class.get(0)
        metrics_dict['f1_buy'] = f1_per_class.get(1)

    log_suffix = task_checkpoint_suffix(task)
    checkpoint_path = str(CHECKPOINTS_DIR / f'{model_name}{log_suffix}_best.pt')
    
    logger = CSVExperimentLogger()
    logger.log_experiment(config_dict, metrics_dict, checkpoint_path=checkpoint_path)


@torch.no_grad()
def _collect_regression_preds(
    model: nn.Module,
    val_loader: torch.utils.data.DataLoader,
    device: torch.device,
) -> tuple[np.ndarray, np.ndarray]:
    """Собрать предсказания регрессионной модели для построения графиков."""
    model.eval()
    all_preds, all_targets = [], []
    for batch in val_loader:
        X_batch, y_batch, mask_batch = batch[0], batch[1], batch[2]
        X_batch = X_batch.to(device)
        mask_batch = mask_batch.to(device)
        logits = model(X_batch, mask=mask_batch)
        # Multi-target: keep shape (batch, 6); single: squeeze to (batch,)
        if logits.shape[-1] == 1:
            logits = logits.squeeze(-1)
        all_preds.append(logits.cpu().numpy())
        all_targets.append(y_batch.numpy())
    return np.concatenate(all_preds), np.concatenate(all_targets)


@torch.no_grad()
def _collect_tb_logits(
    model: nn.Module,
    val_loader: torch.utils.data.DataLoader,
    device: torch.device,
) -> tuple[np.ndarray, np.ndarray]:
    model.eval()
    all_logits, all_targets = [], []
    for X_batch, y_batch, mask_batch in val_loader:
        X_batch = X_batch.to(device)
        mask_batch = mask_batch.to(device)
        logits = model(X_batch, mask=mask_batch)
        all_logits.append(logits.cpu().numpy())
        all_targets.append(y_batch.numpy())
    return np.concatenate(all_logits), np.concatenate(all_targets)


# ═══════════════════════════════════════════════════════════════════════════════
# ВИЗУАЛИЗАЦИЯ
# ═══════════════════════════════════════════════════════════════════════════════

def _plot_training_curves(
    history: dict,
    model_name: str,
    task: str | None = None,
    regression: bool = False,
    binary_classification: bool = False,
):
    """
    Построение кривых обучения: loss и основная метрика по эпохам.

    Classification: F1 по классам.
    Regression: pearson_r, MAE.
    """
    # TB has different history keys — skip classification/regression curves
    if 'val_mean_auc' in history:
        fig, axes = plt.subplots(1, 2, figsize=(12, 4))
        epochs_range = range(1, len(history['train_loss']) + 1)
        axes[0].plot(epochs_range, history['train_loss'], label='Train')
        axes[0].plot(epochs_range, history['val_loss'], label='Val')
        axes[0].set_title('Loss'); axes[0].legend()
        axes[1].plot(epochs_range, history['val_mean_auc'], label='Mean AUC')
        axes[1].set_title('Validation Mean AUC'); axes[1].legend()
        for ax in axes:
            ax.grid(True, alpha=0.3)
        plt.tight_layout()
        fig.savefig(PLOTS_DIR / f'training_curves_{model_name}_tb.png', dpi=150, bbox_inches='tight')
        plt.close(fig)
        print(f"  Кривые обучения: training_curves_{model_name}_tb.png")
        return
    if 'val_q50_pearson_r' in history:
        fig, axes = plt.subplots(1, 2, figsize=(12, 4))
        epochs_range = range(1, len(history['train_loss']) + 1)
        axes[0].plot(epochs_range, history['train_loss'], label='Train')
        axes[0].plot(epochs_range, history['val_loss'], label='Val')
        axes[0].set_title('Loss')
        axes[0].legend()
        axes[1].plot(epochs_range, history['val_q50_pearson_r'], label='Q50 Pearson r')
        axes[1].plot(epochs_range, history['val_interval_coverage'], label='Coverage')
        axes[1].set_title('Validation Quantile Metrics')
        axes[1].legend()
        for ax in axes:
            ax.grid(True, alpha=0.3)
        plt.tight_layout()
        save_path = PLOTS_DIR / f'training_curves_{model_name}{task_checkpoint_suffix(task or TRAILING_STOP_TARGET_QUANTILE_TARGET)}.png'
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        print(f"  📊 Кривые обучения: {save_path.name}")
        return

    if 'val_bce' in history:
        fig, axes = plt.subplots(1, 2, figsize=(12, 4))
        epochs_range = range(1, len(history['train_loss']) + 1)
        axes[0].plot(epochs_range, history['train_loss'], label='Train')
        axes[0].plot(epochs_range, history['val_loss'], label='Val')
        axes[0].set_title('BCE Loss')
        axes[0].legend()
        axes[1].plot(epochs_range, history['val_score'], label='Val Score')
        axes[1].plot(epochs_range, history['val_bce'], label='BCE')
        axes[1].set_title('Validation Take/Skip Metrics')
        axes[1].legend()
        for ax in axes:
            ax.grid(True, alpha=0.3)
        plt.tight_layout()
        save_path = PLOTS_DIR / f'training_curves_{model_name}{task_checkpoint_suffix(task or TAKE_SKIP_TRAILING_STOP_TARGET)}.png'
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        print(f"  📊 Кривые обучения: {save_path.name}")
        return

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    epochs_range = range(1, len(history['train_loss']) + 1)

    # Loss
    axes[0].plot(epochs_range, history['train_loss'], label='Train Loss', color='#2196F3')
    axes[0].plot(epochs_range, history['val_loss'], label='Val Loss', color='#F44336')
    axes[0].set_xlabel('Epoch')
    axes[0].set_ylabel('Huber Loss' if regression else 'Classification Loss')
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
        ax2.set_ylabel('MAE')
        axes[1].set_xlabel('Epoch')
        axes[1].set_ylabel('Pearson r')
        axes[1].set_title(f'{model_name}: Validation Metrics (Regression)')
        # Объединённая легенда
        lines1, labels1 = axes[1].get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        axes[1].legend(lines1 + lines2, labels1 + labels2, loc='best')
    elif binary_classification:
        axes[1].plot(epochs_range, history['val_auc'],
                     label='AUC', color='#4CAF50', linewidth=2)
        axes[1].plot(epochs_range, history['val_precision'],
                     label='Precision', color='#FF9800', linestyle='--')
        axes[1].plot(epochs_range, history['val_recall'],
                     label='Recall', color='#03A9F4', linestyle='--')
        axes[1].set_xlabel('Epoch')
        axes[1].set_ylabel('Score')
        axes[1].set_title(f'{model_name}: Validation Binary Metrics')
        axes[1].legend()
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

    suffix = task_checkpoint_suffix(task) if task is not None else ('_regression' if regression else '')
    save_path = PLOTS_DIR / f'training_curves_{model_name}{suffix}.png'
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  📊 Кривые обучения: {save_path.name}")


def _plot_confusion_matrix(
    cm: np.ndarray,
    model_name: str,
    labels: list[str] | None = None,
    task: str | None = None,
):
    """
    Сохранение confusion matrix лучшей эпохи (classification).

    Сохраняет в ML/plots/cm_<model>.png
    """
    fig, ax = plt.subplots(figsize=(8, 6))
    labels = labels or ['Sell (-1)', 'Neutral (0)', 'Buy (1)']

    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax,
                xticklabels=labels, yticklabels=labels)
    ax.set_xlabel('Predicted', fontsize=12)
    ax.set_ylabel('Actual', fontsize=12)
    ax.set_title(f'Confusion Matrix: {model_name} (best epoch)', fontsize=14)

    plt.tight_layout()
    save_path = PLOTS_DIR / f'cm_{model_name}{task_checkpoint_suffix(task or "classification")}.png'
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  📊 Confusion matrix: {save_path.name}")


def _plot_regression_results(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    model_name: str,
    task: str | None = None,
):
    """
    Построение scatter plot и гистограммы residuals для регрессии.

    Поддерживает single-target (1D) и multi-target (2D).
    Сохраняет в ML/plots/regression_<model>.png
    """
    from ML.utils import UPDN_TARGET_NAMES

    # Multi-target: per-target subplots
    if y_true.ndim == 2 and y_true.shape[1] > 1:
        n_targets = y_true.shape[1]
        fig, axes = plt.subplots(2, n_targets, figsize=(4 * n_targets, 8))

        for i in range(n_targets):
            name = UPDN_TARGET_NAMES[i] if i < len(UPDN_TARGET_NAMES) else f't{i}'
            yt, yp = y_true[:, i], y_pred[:, i]
            residuals = yp - yt

            # Scatter
            axes[0, i].scatter(yt, yp, alpha=0.15, s=3, color='#2196F3')
            lim = max(abs(yt).max(), abs(yp).max()) * 1.05
            axes[0, i].plot([0, lim], [0, lim], 'r--', linewidth=1)
            axes[0, i].set_title(name, fontsize=10)
            axes[0, i].set_xlabel('true')
            axes[0, i].set_ylabel('pred')
            axes[0, i].grid(True, alpha=0.3)

            # Residuals
            axes[1, i].hist(residuals, bins=40, color='#FF9800', edgecolor='none', alpha=0.8)
            axes[1, i].axvline(0, color='red', linestyle='--', linewidth=1)
            axes[1, i].set_xlabel('residual')
            axes[1, i].grid(True, alpha=0.3)

        fig.suptitle(f'{model_name}: Multi-target regression (val)', fontsize=12)
        plt.tight_layout()
        save_path = PLOTS_DIR / f'regression_{model_name}{task_checkpoint_suffix(task or UPDN_REGRESSION_TARGET)}.png'
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        print(f"  📊 Multi-target regression: {save_path.name}")
        return

    # Single-target (original)
    residuals = y_pred - y_true
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

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

    axes[1].hist(residuals, bins=60, color='#FF9800', edgecolor='none', alpha=0.8)
    axes[1].axvline(0, color='red', linestyle='--', linewidth=1.5)
    axes[1].set_xlabel('Residual (y_pred - y_true)')
    axes[1].set_ylabel('Count')
    axes[1].set_title(f'{model_name}: Residuals (val)')
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    save_path = PLOTS_DIR / f'regression_{model_name}{task_checkpoint_suffix(task or REGRESSION_TARGET)}.png'
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
        choices=list(MODEL_REGISTRY.keys()) + list(ENTRY_PATH_MODEL_NAMES[1:]),
        help=f"Модель для обучения: {', '.join(list(MODEL_REGISTRY.keys()) + list(ENTRY_PATH_MODEL_NAMES[1:]))}"
    )
    parser.add_argument(
        '--task', type=str, default='classification',
        choices=[
            'classification',
            'regression',
            'regression_updn',
            'triple_barrier',
            ENTRY_PATH_TARGET,
            ENTRY_PATH_V1_QUANTILE_TARGET,
            TRADE_OUTCOME_TARGET,
            TRADE_PNL_TARGET,
            ARCHETYPE_TARGET,
            TRAILING_STOP_TARGET,
            TRAILING_STOP_TARGET_QUANTILE_TARGET,
            TAKE_SKIP_TRAILING_STOP_TARGET,
        ],
        help="Задача: 'classification' | 'regression' (predict) | 'regression_updn' | "
             "'triple_barrier' | 'entry_path_v1' | 'entry_path_v1_quantile' | outcome-aligned targets | "
             f"'{TRAILING_STOP_TARGET}' | '{TRAILING_STOP_TARGET_QUANTILE_TARGET}' | "
             f"'{TAKE_SKIP_TRAILING_STOP_TARGET}'. "
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
    
    # Регрессионные функции потерь
    parser.add_argument('--regression_loss', type=str, default='huber', choices=['huber', 'asymmetric', 'directional'],
                        help="Loss функция для регрессии (default: huber)")
    parser.add_argument('--asym_over_penalty', type=float, default=1.0,
                        help="Штраф за перепрогноз (FP) в AsymmetricLoss (default: 1.0)")
    parser.add_argument('--asym_under_penalty', type=float, default=10.0,
                        help="Штраф за недопрогноз (FN) в AsymmetricLoss (default: 10.0)")
    
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
    parser.add_argument('--optuna_json', type=str, default=None,
                        help="Путь к JSON файлу с лучшими параметрами Optuna")
    parser.add_argument('--seq_len', type=int, default=20,
                        help="Количество фракталов в последовательности (default: 20)")
    
    parser.add_argument(
        '--clear_cache', action='store_true',
        help="Удалить старый кэш .npy перед загрузкой"
    )
    parser.add_argument(
        '--model_kwargs', type=str, default=None,
        help='JSON строка с архитектурными параметрами модели. '
             'Пример: \'{"d_model": 32, "nhead": 8, "num_layers": 3}\''
    )
    parser.add_argument(
        '--encoder_ckpt', type=str, default=None,
        help='Путь к checkpoint для transfer learning (загружает encoder веса, сбрасывает classifier).'
             ' Пример: ML/checkpoints/transformer_updn_best.pt'
    )

    return parser.parse_args()


def main():
    """Точка входа: парсинг аргументов → обучение модели."""
    args = parse_args()

    # Загружаем архитектурные параметры
    model_kwargs = None
    if args.model_kwargs:
        model_kwargs = json.loads(args.model_kwargs)
    if args.optuna_json:
        with open(args.optuna_json, 'r', encoding='utf-8') as f:
            optuna_data = json.load(f)
        best_params = optuna_data.get('best_params', {})
        
        # Перезаписываем аргументы CLI
        if 'lr' in best_params: args.lr = best_params['lr']
        if 'batch_size' in best_params: args.batch_size = best_params['batch_size']
        if 'patience' in best_params: args.patience = best_params['patience']
        if 'weight_decay' in best_params: args.weight_decay = best_params['weight_decay']
        if 'scheduler_patience' in best_params: args.scheduler_patience = best_params['scheduler_patience']
        if 'scheduler_factor' in best_params: args.scheduler_factor = best_params['scheduler_factor']
        if 'focal_gamma' in best_params: args.focal_gamma = best_params['focal_gamma']
        if 'focal_minority_weight' in best_params: args.focal_minority_weight = best_params['focal_minority_weight']
        if 'huber_delta' in best_params: setattr(args, 'huber_delta', best_params['huber_delta'])
        if 'seq_len' in best_params: args.seq_len = best_params['seq_len']
        
        # Извлекаем параметры архитектуры (всё кроме training params)
        training_params = {
            'lr', 'batch_size', 'patience', 'weight_decay',
            'scheduler_patience', 'scheduler_factor',
            'focal_gamma', 'focal_minority_weight',
            'huber_delta', 'seq_len',
            'asym_over_penalty', 'asym_under_penalty',
        }
        if model_kwargs is None:
            model_kwargs = {}
        for k, v in best_params.items():
            if k not in training_params:
                model_kwargs[k] = v
                
        print(f"✅ Успешно загружены параметры Optuna из {args.optuna_json}")

    print("=" * 60)
    print("  NEURAL NETWORK TRAINING")
    print(f"  Модель: {args.model}  |  Задача: {args.task}")
    print(f"  Epochs: {args.epochs}, Batch: {args.batch_size}, LR: {args.lr}, SeqLen: {args.seq_len}")
    if model_kwargs:
        print(f"  Model kwargs: {model_kwargs}")
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
        huber_delta=getattr(args, 'huber_delta', DEFAULTS['huber_delta']),
        regression_loss=args.regression_loss,
        asym_over_penalty=args.asym_over_penalty,
        asym_under_penalty=args.asym_under_penalty,
        scheduler_patience=args.scheduler_patience,
        scheduler_factor=args.scheduler_factor,
        metric_mode=args.metric_mode,
        min_signal_recall=args.min_signal_recall,
        use_weighted_sampler=args.use_weighted_sampler,
        model_kwargs=model_kwargs,
        seq_len=args.seq_len,
        clear_cache=args.clear_cache,
        encoder_ckpt=getattr(args, 'encoder_ckpt', None),
    )

    # Сохраняем результат как JSON
    regression = (args.task in ['regression', 'regression_updn', TRADE_PNL_TARGET, TRAILING_STOP_TARGET])
    binary_classification = (args.task in BINARY_CLASSIFICATION_TARGETS)
    triple_barrier = (args.task == 'triple_barrier')
    entry_path = (args.task == ENTRY_PATH_TARGET)
    entry_path_quantile = (args.task == ENTRY_PATH_V1_QUANTILE_TARGET)
    entry_path_like = entry_path or entry_path_quantile
    trailing_stop_quantile = (args.task == TRAILING_STOP_TARGET_QUANTILE_TARGET)
    take_skip_trailing_stop = (args.task == TAKE_SKIP_TRAILING_STOP_TARGET)

    if triple_barrier:
        result_serializable = {
            'model_name': result['model_name'],
            'task': result['task'],
            'best_mean_auc': result['best_metric'],
            'best_epoch': result['best_epoch'],
            'num_parameters': result['num_parameters'],
            'training_time': result['training_time'],
            'per_target': result['best_metrics'].get('per_target', {}),
        }
        suffix = task_checkpoint_suffix(args.task)
    elif binary_classification:
        result_serializable = {
            'model_name': result['model_name'],
            'task': result['task'],
            'best_auc': result['best_metric'],
            'best_epoch': result['best_epoch'],
            'num_parameters': result['num_parameters'],
            'training_time': result['training_time'],
            'val_metrics': {
                k: v for k, v in result['best_metrics'].items()
                if isinstance(v, float)
            },
        }
        suffix = task_checkpoint_suffix(args.task)
    elif entry_path or entry_path_quantile:
        if entry_path_quantile:
            result_serializable = {
                'model_name': result['model_name'],
                'task': result['task'],
                'best_val_score': result['best_metric'],
                'best_epoch': result['best_epoch'],
                'num_parameters': result['num_parameters'],
                'training_time': result['training_time'],
                'val_metrics': {
                    'val_score': result['best_metrics'].get('val_score'),
                    'ret_pearson_r': result['best_metrics'].get('ret_pearson_r'),
                    'path_reg_pearson_r': result['best_metrics'].get('path_reg_pearson_r'),
                    'path_cls_f1_macro': result['best_metrics'].get('path_cls_f1_macro'),
                    'active_path_cls_f1_macro': result['best_metrics'].get('active_path_cls_f1_macro'),
                    'interval_coverage': result['best_metrics'].get('interval_coverage'),
                    'median_interval_width': result['best_metrics'].get('median_interval_width'),
                    'q10_pinball_loss': result['best_metrics'].get('q10_pinball_loss'),
                    'q90_pinball_loss': result['best_metrics'].get('q90_pinball_loss'),
                },
                'ret_per_target': result['best_metrics'].get('ret_per_target', {}),
                'path_reg_per_target': result['best_metrics'].get('path_reg_per_target', {}),
                'path_cls_per_class': {
                    str(k): v for k, v in result['best_metrics'].get('path_cls_per_class', {}).items()
                },
                'active_path_cls_per_class': {
                    str(k): v for k, v in result['best_metrics'].get('active_path_cls_per_class', {}).items()
                },
            }
        else:
            result_serializable = {
                'model_name': result['model_name'],
                'task': result['task'],
                'best_ret_pearson_r': result['best_metric'],
                'best_epoch': result['best_epoch'],
                'num_parameters': result['num_parameters'],
                'training_time': result['training_time'],
                'val_metrics': {
                    'ret_pearson_r': result['best_metrics'].get('ret_pearson_r'),
                    'pearson_r': result['best_metrics'].get('pearson_r'),
                    'mae': result['best_metrics'].get('mae'),
                    'rmse': result['best_metrics'].get('rmse'),
                    'r2': result['best_metrics'].get('r2'),
                    'path_reg_pearson_r': result['best_metrics'].get('path_reg_pearson_r'),
                    'path_cls_f1_macro': result['best_metrics'].get('path_cls_f1_macro'),
                    'active_path_cls_f1_macro': result['best_metrics'].get('active_path_cls_f1_macro'),
                },
                'ret_per_target': result['best_metrics'].get('ret_per_target', {}),
                'path_reg_per_target': result['best_metrics'].get('path_reg_per_target', {}),
                'path_cls_per_class': {
                    str(k): v for k, v in result['best_metrics'].get('path_cls_per_class', {}).items()
                },
                'active_path_cls_per_class': {
                    str(k): v for k, v in result['best_metrics'].get('active_path_cls_per_class', {}).items()
                },
            }
        suffix = task_checkpoint_suffix(args.task)
    elif trailing_stop_quantile:
        result_serializable = {
            'model_name': result['model_name'],
            'task': result['task'],
            'best_val_score': result['best_metric'],
            'best_epoch': result['best_epoch'],
            'num_parameters': result['num_parameters'],
            'training_time': result['training_time'],
            'val_metrics': {
                'val_score': result['best_metrics'].get('val_score'),
                'q50_pearson_r': result['best_metrics'].get('q50_pearson_r'),
                'q50_mae': result['best_metrics'].get('q50_mae'),
                'interval_coverage': result['best_metrics'].get('interval_coverage'),
                'median_interval_width': result['best_metrics'].get('median_interval_width'),
                'q10_pinball_loss': result['best_metrics'].get('q10_pinball_loss'),
                'q50_pinball_loss': result['best_metrics'].get('q50_pinball_loss'),
                'q90_pinball_loss': result['best_metrics'].get('q90_pinball_loss'),
            },
        }
        suffix = task_checkpoint_suffix(args.task)
    elif take_skip_trailing_stop:
        result_serializable = {
            'model_name': result['model_name'],
            'task': result['task'],
            'best_val_score': result['best_metric'],
            'best_epoch': result['best_epoch'],
            'num_parameters': result['num_parameters'],
            'training_time': result['training_time'],
            'val_metrics': {
                k: v for k, v in result['best_metrics'].items()
                if isinstance(v, float)
            },
        }
        suffix = task_checkpoint_suffix(args.task)
    elif regression:
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
        suffix = task_checkpoint_suffix(args.task)
    else:
        result_serializable = {
            'model_name': result['model_name'],
            'task': result['task'],
            'best_metric': result['best_metric'],
            'metric_name': result.get('metric_name'),
            'best_f1_macro': result['best_metrics'].get('f1_macro'),
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
        suffix = task_checkpoint_suffix(args.task)

    result_path = CHECKPOINTS_DIR / f'{args.model}{suffix}_result.json'
    with open(result_path, 'w', encoding='utf-8') as f:
        json.dump(result_serializable, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Результат сохранён: {result_path}")

    # ── Логирование эксперимента ─────────────────────────────────────────────
    checkpoint_path = str(CHECKPOINTS_DIR / f'{args.model}{suffix}_best.pt')

    # Логирование теперь происходит внутри train_model() - дублировать не нужно
    # logger = CSVExperimentLogger()
    # logger.log_experiment(config_dict, metrics_dict, checkpoint_path=checkpoint_path)

    print("\n" + "=" * 60)
    print("  ✅ ОБУЧЕНИЕ ЗАВЕРШЕНО")
    print("=" * 60)


if __name__ == '__main__':
    main()
