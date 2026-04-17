import torch

from ML.models.entry_path_dual_stream_transformer import EntryPathDualStreamTransformer


def test_entry_path_dual_stream_transformer_returns_expected_head_shapes():
    model = EntryPathDualStreamTransformer(
        input_features=20,
        engineered_feature_dim=7,
        d_model=32,
        nhead=4,
        num_layers=1,
        dim_feedforward=64,
        dropout=0.0,
    )
    x = torch.randn(5, 20, 20)
    engineered = torch.randn(5, 7)
    mask = torch.ones(5, 20, dtype=torch.bool)

    output = model(x, engineered=engineered, mask=mask)

    assert set(output) == {'ret', 'path_reg', 'path_cls'}
    assert output['ret'].shape == (5, 3)
    assert output['path_reg'].shape == (5, 6)
    assert output['path_cls'].shape == (5, 3)


def test_entry_path_dual_stream_transformer_supports_masked_backward():
    model = EntryPathDualStreamTransformer(
        input_features=20,
        engineered_feature_dim=7,
        d_model=32,
        nhead=4,
        num_layers=1,
        dim_feedforward=64,
        dropout=0.0,
    )
    x = torch.randn(3, 20, 20)
    engineered = torch.randn(3, 7)
    mask = torch.ones(3, 20, dtype=torch.bool)
    mask[0, 10:] = False

    output = model(x, engineered=engineered, mask=mask)
    loss = output['ret'].mean() + output['path_reg'].mean() + output['path_cls'].mean()
    loss.backward()

    assert model.cls_token.grad is not None
    assert model.engineered_encoder[1].weight.grad is not None
