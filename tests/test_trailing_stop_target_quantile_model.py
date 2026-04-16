import torch

from ML.models.trailing_stop_target_quantile_transformer import TrailingStopTargetQuantileTransformer


def test_quantile_model_returns_three_scalar_heads():
    model = TrailingStopTargetQuantileTransformer(input_features=20)
    X = torch.zeros((2, 20, 20), dtype=torch.float32)
    mask = torch.ones((2, 20), dtype=torch.bool)

    out = model(X, mask=mask)

    assert set(out.keys()) == {'q10', 'q50', 'q90'}
    assert out['q10'].shape == (2, 1)
    assert out['q50'].shape == (2, 1)
    assert out['q90'].shape == (2, 1)
