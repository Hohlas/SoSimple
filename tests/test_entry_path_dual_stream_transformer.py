import sys

import torch

sys.path.insert(0, '.')

from ML.models.entry_path_dual_stream_transformer import EntryPathDualStreamTransformer


def test_entry_path_dual_stream_transformer_returns_expected_head_shapes():
    model = EntryPathDualStreamTransformer(
        input_features=20,
        engineered_feature_dim=7,
        d_model=32,
        nhead=4,
        num_layers=1,
        dim_feedforward=64,
        dropout=0.1,
    )
    x = torch.randn(2, 20, 20)
    engineered = torch.randn(2, 7)
    mask = torch.ones(2, 20, dtype=torch.bool)

    out = model(x, engineered, mask=mask)

    assert out['ret'].shape == (2, 3)
    assert out['path_reg'].shape == (2, 6)
    assert out['path_cls'].shape == (2, 3)


def test_entry_path_dual_stream_transformer_supports_masked_backward():
    model = EntryPathDualStreamTransformer(
        input_features=20,
        engineered_feature_dim=7,
        d_model=32,
        nhead=4,
        num_layers=1,
        dim_feedforward=64,
        dropout=0.1,
    )
    x = torch.randn(2, 20, 20, requires_grad=True)
    engineered = torch.randn(2, 7, requires_grad=True)
    mask = torch.tensor([
        [True] * 12 + [False] * 8,
        [True] * 20,
    ], dtype=torch.bool)

    out = model(x, engineered, mask=mask)
    loss = out['ret'].sum() + out['path_reg'].sum() + out['path_cls'].sum()
    loss.backward()

    assert model.cls_token.grad is not None
    assert model.engineered_encoder[1].weight.grad is not None
