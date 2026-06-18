# =============================================================================
# File: ML/models/fractal_breach_transformer.py
# Purpose: Small Transformer encoder for breach classification (Stage 5.0)
# Language: Python 3.10+
# Created: 2026-06-17
# =============================================================================

import math
import numpy as np
import torch
import torch.nn as nn


class TokenSelector:
    """Static methods for selecting and ordering fractal tokens by profile rules."""

    @staticmethod
    def by_corridor(prices: np.ndarray, f0_price: float, atr: float,
                    corridor_atr: float, seq_len: int):
        """Select fractals within ±corridor_atr of f0_price, order by distance."""
        dist = np.abs(prices - f0_price)
        threshold = corridor_atr * atr
        within = np.where(dist <= threshold)[0]
        sorted_idx = within[np.argsort(dist[within])]
        selected = np.zeros(seq_len, dtype=int)
        mask = np.zeros(seq_len, dtype=bool)
        n_use = min(len(sorted_idx), seq_len)
        selected[:n_use] = sorted_idx[:n_use]
        mask[:n_use] = True
        return selected, mask, prices[selected[:n_use]].tolist()

    @staticmethod
    def by_nearest(prices: np.ndarray, f0_price: float, k: int, seq_len: int):
        """Select k fractals closest to f0_price, order by distance ascending."""
        dist = np.abs(prices - f0_price)
        sorted_idx = np.argsort(dist)
        n_use = min(k, len(prices))
        selected = np.zeros(seq_len, dtype=int)
        mask = np.zeros(seq_len, dtype=bool)
        selected[:n_use] = sorted_idx[:n_use]
        mask[:n_use] = True
        return selected, mask, prices[selected[:n_use]].tolist()

    @staticmethod
    def newest_n(n: int, n_total: int, seq_len: int):
        """Select first n fractals (newest), pad to seq_len."""
        selected = np.zeros(seq_len, dtype=int)
        mask = np.zeros(seq_len, dtype=bool)
        n_use = min(n, n_total, seq_len)
        selected[:n_use] = np.arange(n_use, dtype=int)
        mask[:n_use] = True
        return selected, mask

    @staticmethod
    def all_fractals(n_total: int, seq_len: int):
        """Select all fractals in order (fractal0 newest)."""
        selected = np.zeros(seq_len, dtype=int)
        mask = np.zeros(seq_len, dtype=bool)
        n_use = min(n_total, seq_len)
        selected[:n_use] = np.arange(n_use, dtype=int)
        mask[:n_use] = True
        return selected, mask


class FractalBreachTransformer(nn.Module):
    """
    Small Transformer encoder for binary breach classification.

    Inputs: tokens (batch, seq_len, token_dim), row_features (batch, row_dim), mask (batch, seq_len)
    Output: logits (batch, 1) for BCEWithLogitsLoss

    Architecture:
        token_projection: Linear(token_dim -> d_model)
        pos_embedding: learned position embedding 0..seq_len-1
        encoder: 2 layers, d_model=64, nhead=4, dim_feedforward=128, dropout=0.15
        pooling: masked mean + newest valid token concat → 2*d_model
        row_mlp: small MLP for row features → d_row_out
        head: Linear(2*d_model + d_row_out, 1)
    """

    def __init__(
        self,
        token_dim: int = 10,
        row_dim: int = 5,
        d_model: int = 64,
        nhead: int = 4,
        num_layers: int = 2,
        dim_feedforward: int = 128,
        dropout: float = 0.15,
        max_seq_len: int = 128,
    ):
        super().__init__()
        self.d_model = d_model

        self.token_projection = nn.Linear(token_dim, d_model)
        self.pos_embedding = nn.Embedding(max_seq_len, d_model)

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            activation='relu',
            batch_first=True,
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)

        self.row_mlp = nn.Sequential(
            nn.Linear(row_dim, d_model // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(d_model // 2, d_model // 2),
        )

        self.head = nn.Sequential(
            nn.Linear(2 * d_model + d_model // 2, d_model),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(d_model, 1),
        )

    def forward(self, tokens: torch.Tensor, row_features: torch.Tensor,
                mask: torch.Tensor) -> torch.Tensor:
        """
        Args:
            tokens: (batch, seq_len, token_dim)
            row_features: (batch, row_dim)
            mask: (batch, seq_len), True = valid token, False = padding
        Returns:
            logits: (batch, 1)
        """
        batch, seq_len, _ = tokens.shape
        device = tokens.device

        x = self.token_projection(tokens)  # (batch, seq_len, d_model)

        positions = torch.arange(seq_len, device=device).unsqueeze(0).expand(batch, -1)
        x = x + self.pos_embedding(positions)

        src_key_padding_mask = ~mask if mask is not None else None

        x = self.encoder(x, src_key_padding_mask=src_key_padding_mask)  # (batch, seq_len, d_model)

        any_valid = mask.any(dim=1, keepdim=True)  # (batch, 1)
        valid_mask_3d = mask.unsqueeze(-1).float()  # (batch, seq_len, 1)
        denom = valid_mask_3d.sum(dim=1).clamp(min=1)  # (batch, 1)
        masked_mean = (x * valid_mask_3d).sum(dim=1) / denom  # (batch, d_model)

        newest_idx = mask.float().argmax(dim=1)  # (batch,) — first True
        newest_token = x[torch.arange(batch, device=device), newest_idx]  # (batch, d_model)

        pooled = torch.cat([masked_mean, newest_token], dim=-1)  # (batch, 2*d_model)

        row_out = self.row_mlp(row_features)  # (batch, d_model//2)

        combined = torch.cat([pooled, row_out], dim=-1)  # (batch, 2*d_model + d_model//2)

        logits = self.head(combined)  # (batch, 1)
        return logits
