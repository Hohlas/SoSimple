import sys

import torch

sys.path.insert(0, '.')

from ML.models.entry_path_transformer import EntryPathTransformer


def test_entry_path_transformer_returns_expected_head_shapes():
    model = EntryPathTransformer(
        input_features=20,
        d_model=32,
        nhead=4,
        num_layers=1,
        dim_feedforward=64,
        dropout=0.1,
    )
    x = torch.randn(2, 20, 20)
    mask = torch.ones(2, 20, dtype=torch.bool)

    out = model(x, mask=mask)

    assert out['ret'].shape == (2, 3)
    assert out['path_reg'].shape == (2, 6)
    assert out['path_cls'].shape == (2, 3)


def test_entry_path_transformer_supports_masked_backward():
    model = EntryPathTransformer(
        input_features=20,
        d_model=32,
        nhead=4,
        num_layers=1,
        dim_feedforward=64,
        dropout=0.1,
    )
    x = torch.randn(2, 20, 20, requires_grad=True)
    mask = torch.tensor([
        [True] * 12 + [False] * 8,
        [True] * 20,
    ], dtype=torch.bool)

    out = model(x, mask=mask)
    loss = out['ret'].sum() + out['path_reg'].sum() + out['path_cls'].sum()
    loss.backward()

    assert model.cls_token.grad is not None


def test_entry_path_transformer_uses_separate_head_blocks():
    model = EntryPathTransformer(
        input_features=20,
        d_model=32,
        nhead=4,
        num_layers=1,
        dim_feedforward=64,
        dropout=0.1,
    )

    assert not hasattr(model, 'shared_head')
    assert isinstance(model.ret_head, torch.nn.Sequential)
    assert isinstance(model.path_reg_head, torch.nn.Sequential)
    assert isinstance(model.path_cls_head, torch.nn.Sequential)


def test_entry_path_transformer_path_cls_has_sequence_pool():
    model = EntryPathTransformer(
        input_features=20,
        d_model=32,
        nhead=4,
        num_layers=1,
        dim_feedforward=64,
        dropout=0.1,
    )

    assert hasattr(model, 'path_cls_sequence_proj')
    assert hasattr(model, 'path_cls_time_pool')
