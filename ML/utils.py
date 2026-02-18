# =============================================================================
# Файл: utils.py
# Назначение: Общие утилиты для обучения нейросетей (seed, метрики, подсчёт параметров)
# Язык: Python 3.11+
# Обновлён: 2026-02-18
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

import random

import numpy as np
import torch
from sklearn.metrics import (
    f1_score,
    classification_report,
    confusion_matrix,
)


def set_seed(seed: int = 42):
    """
    Фиксация seed для воспроизводимости всех экспериментов.

    Устанавливает seed для: random, numpy, torch (CPU + CUDA).
    Включает детерминированный режим cuDNN.

    Аргументы:
        seed: Значение seed (по умолчанию 42)
    """
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


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
        - confusion_matrix: np.ndarray shape (3, 3) — матрица ошибок
        - classification_report: str — полный текстовый отчёт
    """
    labels = [-1, 0, 1]
    target_names = ['Sell (-1)', 'Neutral (0)', 'Buy (1)']

    f1_macro = f1_score(y_true, y_pred, average='macro', labels=labels)

    f1_per = f1_score(y_true, y_pred, average=None, labels=labels)
    f1_per_class = {label: score for label, score in zip(labels, f1_per)}

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
        'confusion_matrix': cm,
        'classification_report': report,
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


def get_device() -> torch.device:
    """
    Определение доступного устройства (GPU/CPU).

    Возвращает:
        torch.device — cuda если GPU доступен, иначе cpu
    """
    if torch.cuda.is_available():
        device = torch.device('cuda')
        print(f"  🖥️  Используется GPU: {torch.cuda.get_device_name(0)}")
    else:
        device = torch.device('cpu')
        print("  🖥️  Используется CPU")
    return device
