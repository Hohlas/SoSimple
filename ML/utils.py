# =============================================================================
# Файл: utils.py
# Назначение: Общие утилиты для обучения нейросетей (seed, метрики, подсчёт параметров)
# Язык: Python 3.11+
# Обновлён: 2026-02-23
# Зависимости:
#   Входные данные: нет
#   Выходные данные: нет
# Внешние зависимости:
#   - torch>=2.0
#   - numpy>=1.24
#   - scikit-learn>=1.2
# Использование:
#   from ML.utils import set_seed, compute_metrics, count_parameters
# =============================================================================

"""
Общие утилиты для ML-экспериментов с нейросетями.

Включает: фиксацию seed, вычисление метрик классификации,
подсчёт параметров модели.
"""

import os
import random

import numpy as np
import torch
from scipy import stats
from sklearn.metrics import (
    f1_score,
    precision_score,
    recall_score,
    classification_report,
    confusion_matrix,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    roc_auc_score,
)


def set_seed(seed: int = 42):
    """
    Фиксация seed для воспроизводимости всех экспериментов.

    Устанавливает seed для: random, numpy, torch (CPU + CUDA).
    Включает детерминированный режим cuDNN.

    Аргументы:
        seed: Значение seed (по умолчанию 42)
    """
    os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG', ':4096:8')
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    torch.use_deterministic_algorithms(True, warn_only=True)


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """
    Вычисление набора метрик классификации.

    Аргументы:
        y_true: Истинные метки, shape (n_samples,), значения из {-1, 0, 1}
        y_pred: Предсказанные метки, shape (n_samples,), значения из {-1, 0, 1}

    Возвращает:
        Словарь с ключами:
        - f1_macro: float — macro F1-score (основная метрика)
        - f1_per_class: dict — F1 для каждого класса {-1: ..., 0: ..., 1: ...}
        - precision_neg, precision_pos: float — precision для сигнальных классов
        - recall_neg, recall_pos: float — recall для сигнальных классов
        - signal_precision: float — средний precision (-1 и 1 классов)
        - signal_recall: float — средний recall (-1 и 1 классов)
        - f1_minority: float — средний F1 (-1 и 1 классов)
        - confusion_matrix: np.ndarray shape (3, 3) — матрица ошибок
        - classification_report: str — полный текстовый отчёт
    """
    labels = [-1, 0, 1]
    target_names = ['Sell (-1)', 'Neutral (0)', 'Buy (1)']

    f1_macro = f1_score(y_true, y_pred, average='macro', labels=labels)

    f1_per = f1_score(y_true, y_pred, average=None, labels=labels)
    f1_per_class = {label: score for label, score in zip(labels, f1_per)}

    # Precision и Recall для каждого класса
    precision_per = precision_score(y_true, y_pred, average=None, labels=labels, zero_division=0)
    recall_per = recall_score(y_true, y_pred, average=None, labels=labels, zero_division=0)

    precision_neg = precision_per[0]  # класс -1
    precision_pos = precision_per[2]  # класс 1
    recall_neg = recall_per[0]        # класс -1
    recall_pos = recall_per[2]        # класс 1

    signal_precision = (precision_neg + precision_pos) / 2
    signal_recall = (recall_neg + recall_pos) / 2
    f1_minority = (f1_per_class[-1] + f1_per_class[1]) / 2

    cm = confusion_matrix(y_true, y_pred, labels=labels)

    report = classification_report(
        y_true, y_pred,
        labels=labels,
        target_names=target_names,
        zero_division=0
    )

    return {
        'f1_macro': f1_macro,
        'f1_per_class': f1_per_class,
        'precision_neg': precision_neg,
        'precision_pos': precision_pos,
        'recall_neg': recall_neg,
        'recall_pos': recall_pos,
        'signal_precision': signal_precision,
        'signal_recall': signal_recall,
        'f1_minority': f1_minority,
        'confusion_matrix': cm,
        'classification_report': report,
    }


def compute_regression_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """
    Вычисление набора метрик регрессии.

    Аргументы:
        y_true: Истинные значения predict, shape (n_samples,)
        y_pred: Предсказанные значения, shape (n_samples,)

    Возвращает:
        Словарь с ключами:
        - mae: float — Mean Absolute Error
        - rmse: float — Root Mean Squared Error
        - r2: float — R² (коэффициент детерминации)
        - pearson_r: float — Корреляция Пирсона (основная метрика early stopping)
        - pearson_p: float — p-значение корреляции
    """
    mae = mean_absolute_error(y_true, y_pred)
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    r2 = r2_score(y_true, y_pred)
    pearson_r, pearson_p = stats.pearsonr(y_true, y_pred)

    return {
        'mae': float(mae),
        'rmse': rmse,
        'r2': float(r2),
        'pearson_r': float(pearson_r),
        'pearson_p': float(pearson_p),
    }


UPDN_TARGET_NAMES = ['up_3', 'dn_3', 'up_6', 'dn_6', 'up_12', 'dn_12', 'up_24', 'dn_24', 'up_48', 'dn_48']


def compute_multitarget_regression_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """
    Метрики для multi-target регрессии (6 Up/Dn таргетов).

    Аргументы:
        y_true: shape (n_samples, 6)
        y_pred: shape (n_samples, 6)

    Возвращает:
        Словарь: per-target pearson_r + средние метрики.
        Ключ 'pearson_r' содержит среднее по всем таргетам (для early stopping).
    """
    n_targets = y_true.shape[1]
    per_target = {}
    pearson_rs = []

    for i in range(n_targets):
        name = UPDN_TARGET_NAMES[i] if i < len(UPDN_TARGET_NAMES) else f'target_{i}'
        m = compute_regression_metrics(y_true[:, i], y_pred[:, i])
        per_target[name] = m
        pearson_rs.append(m['pearson_r'])

    avg_mae = float(np.mean([per_target[n]['mae'] for n in per_target]))
    avg_rmse = float(np.mean([per_target[n]['rmse'] for n in per_target]))
    avg_r2 = float(np.mean([per_target[n]['r2'] for n in per_target]))
    avg_pearson_r = float(np.mean(pearson_rs))

    return {
        'mae': avg_mae,
        'rmse': avg_rmse,
        'r2': avg_r2,
        'pearson_r': avg_pearson_r,
        'pearson_p': 0.0,
        'per_target': per_target,
    }


def compute_binary_classification_metrics(
    y_true: np.ndarray,
    y_pred_proba: np.ndarray,
    target_names: list[str] | None = None,
    threshold: float = 0.5,
) -> dict:
    """
    Metrics for multi-target binary classification (Triple Barrier).

    Args:
        y_true: shape (n_samples, n_targets), binary {0, 1}
        y_pred_proba: shape (n_samples, n_targets), probabilities [0, 1]
        target_names: list of target names for per-target reporting
        threshold: classification threshold for precision/recall

    Returns:
        Dict with per-target AUC, precision, recall, and mean AUC.
    """
    n_targets = y_true.shape[1]
    if target_names is None:
        target_names = [f'target_{i}' for i in range(n_targets)]

    per_target = {}
    aucs = []

    for i in range(n_targets):
        name = target_names[i]
        yt = y_true[:, i]
        yp = y_pred_proba[:, i]

        # Exclude TIMEOUT (0.5) rows — keep only definitive outcomes {0, 1}
        mask = (yt == 0) | (yt == 1)
        yt_bin = yt[mask]
        yp_bin_m = yp[mask]

        # AUC (handle edge case: only one class present)
        n_pos = float((yt_bin == 1).sum())
        n_neg = float((yt_bin == 0).sum())
        if n_pos == 0 or n_neg == 0:
            auc = 0.5  # uninformative
        else:
            auc = float(roc_auc_score(yt_bin, yp_bin_m))

        # Precision / Recall at threshold (on definitive rows only)
        yp_bin = (yp_bin_m >= threshold).astype(int)
        tp = ((yp_bin == 1) & (yt_bin == 1)).sum()
        fp = ((yp_bin == 1) & (yt_bin == 0)).sum()
        fn = ((yp_bin == 0) & (yt_bin == 1)).sum()

        precision = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
        recall = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
        pos_rate = float(n_pos / len(yt_bin)) if len(yt_bin) > 0 else 0.0

        per_target[name] = {
            'auc': auc,
            'precision': precision,
            'recall': recall,
            'pos_rate': pos_rate,
            'n_pos': int(n_pos),
        }
        aucs.append(auc)

    mean_auc = float(np.mean(aucs))

    return {
        'mean_auc': mean_auc,
        'per_target': per_target,
    }


def compute_single_binary_classification_metrics(
    y_true: np.ndarray,
    y_pred_proba: np.ndarray,
    threshold: float = 0.5,
) -> dict:
    """
    Метрики для single-target binary classification.

    Args:
        y_true: shape (n_samples,), binary {0, 1}
        y_pred_proba: shape (n_samples,), probabilities [0, 1]
        threshold: probability threshold for hard predictions

    Returns:
        Dict with auc, precision, recall, f1, confusion_matrix, classification_report.
    """
    y_true = np.asarray(y_true).astype(int)
    y_pred_proba = np.asarray(y_pred_proba).astype(np.float64)
    y_pred = (y_pred_proba >= threshold).astype(int)

    if len(np.unique(y_true)) < 2:
        auc = 0.5
    else:
        auc = float(roc_auc_score(y_true, y_pred_proba))

    precision = float(precision_score(y_true, y_pred, zero_division=0))
    recall = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    report = classification_report(
        y_true,
        y_pred,
        labels=[0, 1],
        target_names=['Bad (0)', 'Good (1)'],
        zero_division=0,
    )

    return {
        'auc': auc,
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'confusion_matrix': cm,
        'classification_report': report,
        'positive_rate': float(y_true.mean()) if len(y_true) else 0.0,
    }


def count_parameters(model: torch.nn.Module) -> int:
    """
    Подсчёт обучаемых параметров модели.

    Аргументы:
        model: PyTorch модель

    Возвращает:
        Количество обучаемых параметров (int)
    """
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def get_device(device_override: str | None = None) -> torch.device:
    """
    Определение устройства (GPU/CPU).

    Возвращает:
        torch.device — выбранное устройство
    """
    if device_override is not None:
        device_override = device_override.lower()
    if device_override == 'cpu':
        device = torch.device('cpu')
        print("  🖥️  Используется CPU")
    elif device_override == 'cuda':
        if not torch.cuda.is_available():
            raise RuntimeError('CUDA недоступна, нельзя использовать --device cuda')
        device = torch.device('cuda')
        print(f"  🖥️  Используется GPU: {torch.cuda.get_device_name(0)}")
    elif device_override in (None, 'auto'):
        if torch.cuda.is_available():
            device = torch.device('cuda')
            print(f"  🖥️  Используется GPU: {torch.cuda.get_device_name(0)}")
        else:
            device = torch.device('cpu')
            print("  🖥️  Используется CPU")
    else:
        raise ValueError(f"unknown device override: {device_override}")
    return device
