import torch
import torch.nn as nn

from ML.models.transformer import PositionalEncoding


class EntryPathTransformer(nn.Module):
    def __init__(
        self,
        input_features: int = 20,
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

        self.ret_head = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(d_model, 32),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(32, 3),
        )
        self.path_reg_head = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(d_model, 32),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(32, 6),
        )
        self.path_cls_sequence_proj = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(d_model, 32),
            nn.ReLU(),
        )
        self.path_cls_time_pool = nn.Linear(32, 1)
        self.path_cls_head = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(32, 32),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(32, 3),
        )

    def forward(
        self,
        x: torch.Tensor,
        mask: torch.Tensor | None = None,
    ) -> dict[str, torch.Tensor]:
        batch_size = x.size(0)

        x = self.input_projection(x)
        cls_tokens = self.cls_token.expand(batch_size, -1, -1)
        x = torch.cat([cls_tokens, x], dim=1)
        x = self.pos_encoding(x)

        if mask is not None:
            cls_mask = torch.ones(batch_size, 1, dtype=torch.bool, device=mask.device)
            src_key_padding_mask = ~torch.cat([cls_mask, mask], dim=1)
        else:
            src_key_padding_mask = None

        x = self.transformer_encoder(x, src_key_padding_mask=src_key_padding_mask)
        cls_output = x[:, 0, :]
        sequence_output = x[:, 1:, :]

        path_cls_hidden = self.path_cls_sequence_proj(sequence_output)
        path_cls_pool_logits = self.path_cls_time_pool(path_cls_hidden).squeeze(-1)
        if mask is not None:
            path_cls_pool_logits = path_cls_pool_logits.masked_fill(~mask, float('-inf'))
        path_cls_pool_weights = torch.softmax(path_cls_pool_logits, dim=1).unsqueeze(-1)
        path_cls_output = (path_cls_hidden * path_cls_pool_weights).sum(dim=1)

        return {
            'ret': self.ret_head(cls_output),
            'path_reg': self.path_reg_head(cls_output),
            'path_cls': self.path_cls_head(path_cls_output),
        }
