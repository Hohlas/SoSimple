# =============================================================================
# Файл: bilstm.py
# Назначение: Bi-LSTM модель для классификации фрактальных последовательностей
# Язык: Python 3.10+
# Обновлён: 2026-02-18
# Зависимости:
#   Внешние зависимости:
#     - torch>=2.0
# Использование:
#   from ML.models.bilstm import BiLSTMClassifier
# Примечания:
#   - Input: (batch, seq_len=100, features=11)
#   - 2 слоя Bi-LSTM (hidden_size=64), dropout=0.3
#   - Pooling: concat(last_hidden_fwd, last_hidden_bwd)
#   - FC → 3 класса
# =============================================================================

"""
Bi-LSTM классификатор для последовательностей фракталов.

Двунаправленный LSTM захватывает зависимости как от свежих (pos 0),
так и от старых фракталов. Pooling конкатенирует последние hidden states
обоих направлений.
"""

import torch
import torch.nn as nn


class BiLSTMClassifier(nn.Module):
    """
    Bidirectional LSTM для классификации sequence → class.

    Архитектура:
        Input (batch, 100, 11)
        → Bi-LSTM layer 1 (hidden=64, bidirectional)
        → Dropout(0.3)
        → Bi-LSTM layer 2 (hidden=64, bidirectional)
        → Pooling: concat(last_fwd, last_bwd) → (batch, 128)
        → Dropout(0.3)
        → FC(128, 64) → ReLU
        → Dropout(0.3)
        → FC(64, 3)

    Аргументы:
        input_features: Количество входных признаков (по умолчанию 11)
        hidden_size: Размер hidden state LSTM (по умолчанию 64)
        num_layers: Количество слоёв LSTM (по умолчанию 2)
        num_classes: Количество классов (по умолчанию 3)
        dropout: Dropout between LSTM layers (по умолчанию 0.3)
    """

    def __init__(
        self,
        input_features: int = 11,
        hidden_size: int = 64,
        num_layers: int = 2,
        num_classes: int = 3,
        dropout: float = 0.3,
    ):
        super().__init__()

        self.hidden_size = hidden_size
        self.num_layers = num_layers

        self.lstm = nn.LSTM(
            input_size=input_features,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            bidirectional=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )

        # После concat(fwd, bwd) → 2 * hidden_size = 128
        self.classifier = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(hidden_size * 2, 64),
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
            mask: Не используется в LSTM, присутствует для совместимости интерфейса.

        Возвращает:
            Logits, shape (batch, num_classes)
        """
        # x: (batch, seq_len, features)
        # lstm_out: (batch, seq_len, 2 * hidden_size)
        # h_n: (num_layers * 2, batch, hidden_size) — последние hidden states
        lstm_out, (h_n, _c_n) = self.lstm(x)

        # Pooling: concat последних hidden states forward и backward
        # h_n shape: (num_layers * 2, batch, hidden_size)
        # Forward last layer: h_n[-2], Backward last layer: h_n[-1]
        h_fwd = h_n[-2]    # (batch, hidden_size)
        h_bwd = h_n[-1]    # (batch, hidden_size)
        pooled = torch.cat([h_fwd, h_bwd], dim=1)  # (batch, 2 * hidden_size)

        logits = self.classifier(pooled)  # (batch, num_classes)
        return logits
