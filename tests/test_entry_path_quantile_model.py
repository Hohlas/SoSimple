import torch

from ML.models.entry_path_quantile_transformer import EntryPathQuantileTransformer


def test_entry_path_quantile_transformer_outputs_three_ret24_heads():
    model = EntryPathQuantileTransformer(input_features=20, d_model=32, nhead=4, num_layers=1, dim_feedforward=64, dropout=0.1)
    x = torch.randn(4, 20, 20)
    mask = torch.ones(4, 20, dtype=torch.bool)

    out = model(x, mask=mask)

    assert set(out.keys()) == {'ret_point', 'ret_q10', 'ret_q90'}
    assert out['ret_point'].shape == (4, 1)
    assert out['ret_q10'].shape == (4, 1)
    assert out['ret_q90'].shape == (4, 1)
