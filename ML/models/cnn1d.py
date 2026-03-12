# =============================================================================
# Файл: cnn1d.py
# Назначение: 1D-CNN модель для классификации фрактальных последовательностей
# Язык: Python 3.11+
# Обновлён: 2026-02-18
# Зависимости:
#   Внешние зависимости:
#     - torch>=2.0
# Использование:
#   from ML.models.cnn1d import CNN1DClassifier
# Примечания:
#   - Input: (batch, seq_len=100, features=11) — внутри транспонируется
#   - 3 блока: Conv1D → BatchNorm → ReLU → MaxPool
#   - Каналы: 32 → 64 → 128, kernel_sizes: 5, 3, 3
#   - Global Average Pooling → FC → 3 класса
# =============================================================================

"""
1D-CNN классификатор для последовательностей фракталов.

Свёрточные слои эффективно захватывают локальные паттерны
между соседними фракталами. Conv1D применяется по оси времени:
каждый фильтр «видит» kernel_size последовательных фракталов.
"""

import torch
import torch.nn as nn


class CNN1DClassifier(nn.Module):
    """
    1D Convolutional Neural Network для sequence classification.

    Архитектура:
        Input (batch, 100, 11) → transpose → (batch, 11, 100)
        → Conv1D(11→32, k=5) → BN → ReLU → MaxPool(2)   → (batch, 32, 48)
        → Conv1D(32→64, k=3) → BN → ReLU → MaxPool(2)   → (batch, 64, 23)
        → Conv1D(64→128, k=3) → BN → ReLU → MaxPool(2)  → (batch, 128, 10)
        → Global Average Pooling                          → (batch, 128)
        → Dropout(0.3)
        → FC(128, 64) → ReLU
        → Dropout(0.3)
        → FC(64, 3)

    Аргументы:
        input_features: Количество входных каналов (= n_features, по умолчанию 11)
        num_classes: Количество классов (по умолчанию 3)
        dropout: Dropout rate (по умолчанию 0.3)
    """

    def __init__(
        self,
        input_features: int = 11,
        num_classes: int = 3,
        dropout: float = 0.3,
    ):
        super().__init__()

        # Блок 1: Conv1D → BatchNorm → ReLU → MaxPool
        self.block1 = nn.Sequential(
            nn.Conv1d(in_channels=input_features, out_channels=32, kernel_size=5, padding=2),
            nn.BatchNorm1d(32),
            nn.ReLU(),
            nn.MaxPool1d(kernel_size=2),
        )

        # Блок 2
        self.block2 = nn.Sequential(
            nn.Conv1d(in_channels=32, out_channels=64, kernel_size=3, padding=1),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.MaxPool1d(kernel_size=2),
        )

        # Блок 3
        self.block3 = nn.Sequential(
            nn.Conv1d(in_channels=64, out_channels=128, kernel_size=3, padding=1),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.MaxPool1d(kernel_size=2),
        )

        # Global Average Pooling → адаптивно к любой длине
        self.global_avg_pool = nn.AdaptiveAvgPool1d(1)

        # Classifier head
        self.classifier = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, num_classes),
        )

    def forward(
        self,
        x: torch.Tensor,
        mask: torch.Tensor | None = None,
    ) -> torch.Tensor:
        """
        Forward pass.

        Аргументы:
            x: Input tensor, shape (batch, seq_len, features)
            mask: Не используется в CNN, присутствует для совместимости интерфейса.

        Возвращает:
            Logits, shape (batch, num_classes)
        """
        # Conv1d ожидает (batch, channels, length)
        # Транспонируем: (batch, seq_len, features) → (batch, features, seq_len)
        x = x.transpose(1, 2)

        x = self.block1(x)   # (batch, 32, 50)
        x = self.block2(x)   # (batch, 64, 25)
        x = self.block3(x)   # (batch, 128, 12)

        # Global Average Pooling → (batch, 128, 1) → squeeze → (batch, 128)
        x = self.global_avg_pool(x).squeeze(-1)

        logits = self.classifier(x)  # (batch, num_classes)
        return logits
