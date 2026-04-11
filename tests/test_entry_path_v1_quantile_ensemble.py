import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, '.')

from ML import entry_path_v1_quantile_ensemble as ensemble


def _make_seed_frame(q10_values, q90_values):
    return pd.DataFrame({
        'time': ['2024.01.01 00:00', '2024.01.01 01:00'],
        'signal': [1, -1],
        'pred_ret_24_dir_atr': [0.5, 0.3],
        'pred_ret_24_q10': q10_values,
        'pred_ret_24_q90': q90_values,
        'true_ret_24_dir_atr': [1.0, -0.5],
    })


def test_mean_quantile_averages_across_seeds():
    frames = [
        _make_seed_frame([0.2, -0.1], [0.8, 0.3]),
        _make_seed_frame([0.4, -0.3], [1.0, 0.5]),
    ]
    result = ensemble.aggregate_mean_quantile(frames)
    assert abs(result['pred_ret_24_q10'].iloc[0] - 0.3) < 1e-6
    assert abs(result['pred_ret_24_q90'].iloc[0] - 0.9) < 1e-6


def test_majority_vote_requires_quorum():
    masks = [
        pd.Series([True, True]),
        pd.Series([True, False]),
        pd.Series([True, False]),
    ]
    result = ensemble.majority_vote(masks, quorum=3)
    assert result.iloc[0] == True
    assert result.iloc[1] == False

    result2 = ensemble.majority_vote(masks, quorum=2)
    assert result2.iloc[0] == True
    assert result2.iloc[1] == False


def test_aggregate_mean_quantile_preserves_non_quantile_columns():
    frames = [
        _make_seed_frame([0.2, -0.1], [0.8, 0.3]),
        _make_seed_frame([0.4, -0.3], [1.0, 0.5]),
    ]
    result = ensemble.aggregate_mean_quantile(frames)
    assert 'time' in result.columns
    assert 'signal' in result.columns
    assert 'true_ret_24_dir_atr' in result.columns
    assert len(result) == 2
