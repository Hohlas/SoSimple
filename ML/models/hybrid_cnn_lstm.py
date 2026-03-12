# =============================================================================
# Файл: hybrid_cnn_lstm.py
# Назначение: Hybrid CNN+LSTM модель для классификации фрактальных последовательностей
# Язык: Python 3.11+
# Обновлён: 2026-02-18
# Зависимости:
#   Внешние зависимости:
#     - torch>=2.0
# Использование:
#   from ML.models.hybrid_cnn_lstm import HybridCNNLSTMClassifier
# Примечания:
#   - Conv1D блок извлекает локальные паттерны → LSTM агрегирует глобально
#   - Conv1D (11→32, k=5) → Conv1D (32→64, k=3) → LSTM (hidden=64)
#   - Concat последних hidden states → FC → 3 класса
# =============================================================================

"""
Hybrid CNN+LSTM классификатор для последовательностей фракталов.

Объединяет преимущества обоих подходов:
- CNN: эффективное извлечение локальных паттернов между соседними фракталами
- LSTM: агрегация глобальной временной динамики из CNN-фичей
"""

import torch
import torch.nn as nn


class HybridCNNLSTMClassifier(nn.Module):
    """
    Hybrid CNN+LSTM для sequence classification.

    Архитектура:
        Input (batch, 100, 11) → transpose → (batch, 11, 100)
        → Conv1D(11→32, k=5) → BN → ReLU → MaxPool(2)
        → Conv1D(32→64, k=3) → BN → ReLU
        → transpose → (batch, seq_len', 64)
        → LSTM(input=64, hidden=64)
        → Concat(last_hidden_fwd, last_hidden_bwd) → (batch, 128)
        → Dropout(0.3)
        → FC(128, 64) → ReLU
        → Dropout(0.3)
        → FC(64, 3)

    Аргументы:
        input_features: Количество входных признаков (по умолчанию 11)
        cnn_channels: Каналы свёрточных слоёв (по умолчанию [32, 64])
        lstm_hidden: Размер hidden state LSTM (по умолчанию 64)
        num_classes: Количество классов (по умолчанию 3)
        dropout: Dropout rate (по умолчанию 0.3)
    """

    def __init__(
        self,
        input_features: int = 17,
        cnn_channels: list[int] | None = None,
        lstm_hidden: int = 64,
        num_classes: int = 3,
        dropout: float = 0.3,
    ):
        super().__init__()

        if cnn_channels is None:
            cnn_channels = [32, 64]

        # CNN блок для извлечения локальных паттернов
        self.cnn = nn.Sequential(
            # Блок 1: 11 → 32
            nn.Conv1d(in_channels=input_features, out_channels=cnn_channels[0],
                      kernel_size=5, padding=2),
            nn.BatchNorm1d(cnn_channels[0]),
            nn.ReLU(),
            nn.MaxPool1d(kernel_size=2),

            # Блок 2: 32 → 64
            nn.Conv1d(in_channels=cnn_channels[0], out_channels=cnn_channels[1],
                      kernel_size=3, padding=1),
            nn.BatchNorm1d(cnn_channels[1]),
            nn.ReLU(),
            # Без MaxPool — сохраняем больше временной информации для LSTM
        )

        # LSTM для глобальной динамики; обрабатывает CNN-features
        self.lstm = nn.LSTM(
            input_size=cnn_channels[-1],  # 64
            hidden_size=lstm_hidden,
            num_layers=1,
            batch_first=True,
            bidirectional=True,
        )

        # Classifier head
        # Bi-LSTM → concat fwd + bwd = 2 * lstm_hidden
        self.classifier = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(lstm_hidden * 2, 64),
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
            mask: Не используется напрямую, для совместимости интерфейса.

        Возвращает:
            Logits, shape (batch, num_classes)
        """
        # CNN ожидает (batch, channels, length)
        x = x.transpose(1, 2)   # (batch, features, seq_len)

        # CNN блок
        x = self.cnn(x)          # (batch, 64, seq_len // 2)

        # Обратно к (batch, seq_len', channels) для LSTM
        x = x.transpose(1, 2)   # (batch, seq_len // 2, 64)

        # LSTM
        lstm_out, (h_n, _c_n) = self.lstm(x)

        # Pooling: concat последних hidden states bi-LSTM
        # h_n: (2, batch, lstm_hidden) — 2 для bidirectional
        h_fwd = h_n[-2]    # (batch, lstm_hidden)
        h_bwd = h_n[-1]    # (batch, lstm_hidden)
        pooled = torch.cat([h_fwd, h_bwd], dim=1)  # (batch, 2 * lstm_hidden)

        logits = self.classifier(pooled)  # (batch, num_classes)
        return logits
