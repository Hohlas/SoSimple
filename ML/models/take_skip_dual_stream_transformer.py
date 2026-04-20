# =============================================================================
# Файл: take_skip_dual_stream_transformer.py
# Назначение: Dual-stream Transformer для take_skip_v2 с признаками lib_PIC.
# Обновлён: 2026-04-20
# Входные данные:
#   - sequence tensor shape (batch, seq_len, input_features)
#   - engineered tensor shape (batch, engineered_feature_dim)
# Выходные данные:
#   - logits shape (batch, output_dim)
# Использование:
#   from ML.models.take_skip_dual_stream_transformer import TakeSkipDualStreamTransformer
# Примечания:
#   - Возвращает logits; sigmoid применяется снаружи при BCE/evaluation/export.
# =============================================================================

from __future__ import annotations

import torch
import torch.nn as nn

from ML.models.transformer import PositionalEncoding


class TakeSkipDualStreamTransformer(nn.Module):
    """Transformer для совместного чтения фрактальной последовательности и `lib_PIC` признаков."""

    def __init__(
        self,
        input_features: int = 20,
        engineered_feature_dim: int = 117,
        output_dim: int = 15,
        d_model: int = 64,
        nhead: int = 4,
        num_layers: int = 2,
        dim_feedforward: int = 128,
        dropout: float = 0.3,
    ):
        super().__init__()
        self.input_projection = nn.Linear(input_features, d_model)
        self.cls_token = nn.Parameter(torch.randn(1, 1, d_model))
        self.pos_encoding = PositionalEncoding(d_model, max_len=200, dropout=dropout)

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            activation='relu',
            batch_first=True,
        )
        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)

        self.engineered_encoder = nn.Sequential(
            nn.LayerNorm(engineered_feature_dim),
            nn.Linear(engineered_feature_dim, d_model),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(d_model, d_model),
            nn.ReLU(),
        )
        self.fusion = nn.Sequential(
            nn.LayerNorm(d_model * 2),
            nn.Linear(d_model * 2, d_model),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(d_model, output_dim),
        )

    def forward(
        self,
        x: torch.Tensor,
        engineered: torch.Tensor,
        mask: torch.Tensor | None = None,
    ) -> torch.Tensor:
        batch_size = x.size(0)

        seq = self.input_projection(x)
        cls_tokens = self.cls_token.expand(batch_size, -1, -1)
        seq = torch.cat([cls_tokens, seq], dim=1)
        seq = self.pos_encoding(seq)

        if mask is not None:
            cls_mask = torch.ones(batch_size, 1, dtype=torch.bool, device=mask.device)
            src_key_padding_mask = ~torch.cat([cls_mask, mask], dim=1)
        else:
            src_key_padding_mask = None

        seq = self.transformer_encoder(seq, src_key_padding_mask=src_key_padding_mask)
        cls_output = seq[:, 0, :]
        engineered_output = self.engineered_encoder(engineered)
        return self.fusion(torch.cat([cls_output, engineered_output], dim=1))
