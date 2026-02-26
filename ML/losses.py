# =============================================================================
# Файл: losses.py
# Назначение: Focal Loss для обучения на несбалансированных данных
# Язык: Python 3.11+
# Обновлён: 2026-02-23
# Зависимости:
#   Входные данные: нет
#   Выходные данные: нет
# Внешние зависимости:
#   - torch>=2.0
# Использование:
#   from ML.losses import FocalLoss
# Примечания:
#   - При дисбалансе 95%/2.5%/2.5% обычный CrossEntropy с class_weight
#     недостаточен (baseline: recall minority 1-12%). Focal Loss снижает
#     вклад уверенно классифицированных примеров (majority класс 0).
# =============================================================================

"""
Focal Loss для мультиклассовой классификации.

Focal Loss (Lin et al., 2017) добавляет модулирующий фактор (1 - p_t)^gamma
к стандартному cross-entropy loss. Это снижает вклад легко классифицируемых
примеров (majority-класс 0 ≈ 95%) и фокусирует обучение на сложных
(minority-классы -1 и 1 ≈ 2.5% каждый).
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class FocalLoss(nn.Module):
    """
    Focal Loss для мультиклассовой классификации.

    FL(p_t) = -alpha_t * (1 - p_t)^gamma * log(p_t)

    Аргументы:
        alpha: Веса классов, list/tensor длины num_classes.
               alpha=[0.495, 0.01, 0.495] даёт больший вес minority-классам
               (-1 и 1), меньший — majority-классу (0).
               Порядок соответствует индексам классов после маппинга:
               0 → class -1, 1 → class 0, 2 → class 1.
        gamma: Фокусирующий параметр (по умолчанию 2.0).
               gamma=0 эквивалентен CrossEntropy.
               gamma=2 — рекомендуемое значение из оригинальной статьи.
        reduction: 'mean' | 'sum' | 'none'

    Пример:
        >>> loss_fn = FocalLoss(alpha=[0.495, 0.01, 0.495], gamma=2.0)
        >>> logits = torch.randn(32, 3)   # batch=32, 3 класса
        >>> targets = torch.randint(0, 3, (32,))
        >>> loss = loss_fn(logits, targets)
    """

    def __init__(
        self,
        alpha: list[float] | None = None,
        gamma: float = 2.0,
        reduction: str = 'mean',
    ):
        super().__init__()
        self.gamma = gamma
        self.reduction = reduction

        if alpha is not None:
            # Регистрируем как buffer — не обучается, но перемещается на device
            self.register_buffer('alpha', torch.tensor(alpha, dtype=torch.float32))
        else:
            self.alpha = None

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        """
        Вычисление Focal Loss.

        Аргументы:
            logits: Выходы модели (до softmax), shape (batch, num_classes)
            targets: Целевые метки, shape (batch,), значения 0..num_classes-1

        Возвращает:
            Скалярный loss (если reduction='mean' или 'sum')
        """
        # Вероятности через log_softmax (численно стабильнее)
        log_probs = F.log_softmax(logits, dim=1)         # (batch, C)
        probs = torch.exp(log_probs)                      # (batch, C)

        # Выбираем p_t и log(p_t) для правильного класса
        targets_one_hot = F.one_hot(targets, num_classes=logits.size(1))  # (batch, C)
        targets_one_hot = targets_one_hot.float()

        p_t = (probs * targets_one_hot).sum(dim=1)         # (batch,)
        log_p_t = (log_probs * targets_one_hot).sum(dim=1) # (batch,)

        # Модулирующий фактор
        focal_weight = (1 - p_t) ** self.gamma              # (batch,)

        # Alpha-взвешивание
        if self.alpha is not None:
            alpha_t = self.alpha[targets]                    # (batch,)
            focal_weight = alpha_t * focal_weight

        # Focal Loss = -alpha_t * (1 - p_t)^gamma * log(p_t)
        loss = -focal_weight * log_p_t                       # (batch,)

        if self.reduction == 'mean':
            return loss.mean()
        elif self.reduction == 'sum':
            return loss.sum()
        else:
            return loss


class HuberLoss(nn.Module):
    """
    Huber Loss для регрессии на непрерывных значениях predict.

    Huber Loss (delta=1.0 по умолчанию) менее чувствителен к выбросам,
    чем MSE: при |error| < delta ведёт себя как MSE, при |error| >= delta —
    как MAE. Это важно для predict, где редкие сильные движения цены
    могут давать большие выбросы.

    Аргументы:
        delta: Порог переключения MSE/MAE (по умолчанию 1.0)
        reduction: 'mean' | 'sum' | 'none'

    Пример:
        >>> loss_fn = HuberLoss(delta=1.0)
        >>> preds = torch.randn(32)
        >>> targets = torch.randn(32)
        >>> loss = loss_fn(preds, targets)
    """

    def __init__(self, delta: float = 1.0, reduction: str = 'mean'):
        super().__init__()
        self._loss = nn.HuberLoss(delta=delta, reduction=reduction)

    def forward(self, preds: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        """
        Вычисление Huber Loss.

        Аргументы:
            preds: Предсказания модели, shape (batch,)
            targets: Целевые значения predict, shape (batch,)

        Возвращает:
            Скалярный loss (если reduction='mean' или 'sum')
        """
        return self._loss(preds, targets)

