import sys

import torch

sys.path.insert(0, '.')

from ML.models.entry_path_v1_quantile_transformer import EntryPathV1QuantileTransformer


def test_entry_path_v1_quantile_transformer_outputs_old_and_new_heads():
    model = EntryPathV1QuantileTransformer(
        input_features=20,
        d_model=32,
        nhead=4,
        num_layers=1,
        dim_feedforward=64,
        dropout=0.1,
    )
    x = torch.randn(4, 20, 20)
    mask = torch.ones(4, 20, dtype=torch.bool)

    out = model(x, mask=mask)

    assert set(out.keys()) == {'ret', 'path_reg', 'path_cls', 'ret_q10', 'ret_q90'}
    assert out['ret'].shape == (4, 3)
    assert out['path_reg'].shape == (4, 6)
    assert out['path_cls'].shape == (4, 3)
    assert out['ret_q10'].shape == (4, 1)
    assert out['ret_q90'].shape == (4, 1)
