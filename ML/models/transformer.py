# =============================================================================
# Файл: transformer.py
# Назначение: Transformer Encoder для классификации фрактальных последовательностей
# Язык: Python 3.11+
# Обновлён: 2026-02-18
# Зависимости:
#   Внешние зависимости:
#     - torch>=2.0
# Использование:
#   from ML.models.transformer import TransformerClassifier
# Примечания:
#   - Input: (batch, seq_len=100, features=11) + positional encoding
#   - 2 encoder layers, d_model=64, nhead=4, feedforward=128
#   - CLS token pooling → FC → 3 класса
#   - Padding mask для NaN позиций
# =============================================================================

"""
Transformer Encoder классификатор для последовательностей фракталов.

Self-attention обнаруживает зависимости между произвольными позициями
в последовательности (не только соседними, как CNN). CLS-токен
агрегирует информацию из всей последовательности.

Padding mask позволяет игнорировать NaN-позиции (фракталы, заполненные
нулями) при вычислении attention weights.
"""

import math

import torch
import torch.nn as nn


class PositionalEncoding(nn.Module):
    """
    Sinusoidal positional encoding (Vaswani et al., 2017).

    Добавляет информацию о позиции фрактала в последовательности.
    Позиция 0 — самый свежий фрактал, 99 — самый старый.

    Аргументы:
        d_model: Размерность модели
        max_len: Максимальная длина последовательности
        dropout: Dropout rate
    """

    def __init__(self, d_model: int, max_len: int = 200, dropout: float = 0.1):
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)

        # Вычисляем positional encoding один раз
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(
            torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model)
        )
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)  # (1, max_len, d_model)
        # Регистрируем как buffer — не обучается, но перемещается на device
        self.register_buffer('pe', pe)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Добавление positional encoding к входу.

        Аргументы:
            x: Input tensor, shape (batch, seq_len, d_model)

        Возвращает:
            x + PE, shape (batch, seq_len, d_model)
        """
        x = x + self.pe[:, :x.size(1), :]
        return self.dropout(x)


class TransformerClassifier(nn.Module):
    """
    Transformer Encoder для sequence classification.

    Архитектура:
        Input (batch, 100, 11)
        → Linear projection (11 → d_model=64)
        → CLS token prepend → (batch, 101, 64)
        → Positional Encoding
        → TransformerEncoder (2 layers, 4 heads, ff=128)
        → CLS token output → (batch, 64)
        → Dropout(0.3)
        → FC(64, 32) → ReLU
        → Dropout(0.3)
        → FC(32, 3)

    Аргументы:
        input_features: Количество входных признаков (по умолчанию 11)
        d_model: Размерность модели (по умолчанию 64)
        nhead: Количество attention heads (по умолчанию 4)
        num_layers: Количество encoder layers (по умолчанию 2)
        dim_feedforward: Размерность feedforward сети (по умолчанию 128)
        num_classes: Количество классов (по умолчанию 3)
        dropout: Dropout rate (по умолчанию 0.3)
    """

    def __init__(
        self,
        input_features: int = 17,
        d_model: int = 64,
        nhead: int = 4,
        num_layers: int = 2,
        dim_feedforward: int = 128,
        num_classes: int = 3,
        dropout: float = 0.3,
    ):
        super().__init__()

        self.d_model = d_model

        # Линейная проекция входных features → d_model
        self.input_projection = nn.Linear(input_features, d_model)

        # Learnable CLS token
        self.cls_token = nn.Parameter(torch.randn(1, 1, d_model))

        # Positional encoding (max_len=101: 100 фракталов + 1 CLS)
        self.pos_encoding = PositionalEncoding(d_model, max_len=200, dropout=dropout)

        # Transformer Encoder
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            activation='relu',
            batch_first=True,
        )
        self.transformer_encoder = nn.TransformerEncoder(
            encoder_layer,
            num_layers=num_layers,
        )

        # Classifier head
        self.classifier = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(d_model, 32),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(32, num_classes),
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
            mask: Padding mask, shape (batch, seq_len).
                  True = валидная позиция, False = padding.
                  PyTorch TransformerEncoder ожидает src_key_padding_mask
                  где True = позиция ИГНОРИРУЕТСЯ. Поэтому инвертируем.

        Возвращает:
            Logits, shape (batch, num_classes)
        """
        batch_size = x.size(0)

        # Проекция features → d_model
        x = self.input_projection(x)  # (batch, seq_len, d_model)

        # Добавляем CLS token в начало последовательности
        cls_tokens = self.cls_token.expand(batch_size, -1, -1)  # (batch, 1, d_model)
        x = torch.cat([cls_tokens, x], dim=1)  # (batch, seq_len + 1, d_model)

        # Positional encoding
        x = self.pos_encoding(x)

        # Padding mask: расширяем на CLS token (CLS всегда валиден)
        if mask is not None:
            # mask: (batch, seq_len), True=valid, False=padding
            # Добавляем True для CLS token
            cls_mask = torch.ones(batch_size, 1, dtype=torch.bool, device=mask.device)
            extended_mask = torch.cat([cls_mask, mask], dim=1)  # (batch, seq_len + 1)
            # PyTorch: src_key_padding_mask True = ИГНОРИРОВАТЬ
            src_key_padding_mask = ~extended_mask
        else:
            src_key_padding_mask = None

        # Transformer Encoder
        x = self.transformer_encoder(x, src_key_padding_mask=src_key_padding_mask)

        # Извлекаем CLS token (позиция 0)
        cls_output = x[:, 0, :]  # (batch, d_model)

        logits = self.classifier(cls_output)  # (batch, num_classes)
        return logits
