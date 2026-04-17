import sys

import pandas as pd

sys.path.insert(0, '.')

from ML.feature_screen_entry_path import rank_features_by_mutual_information


def test_rank_features_by_mutual_information_orders_columns():
    frame = pd.DataFrame(
        {
            'f_good': [0, 0, 1, 1],
            'f_noise': [0, 1, 0, 1],
            'target': [0, 0, 1, 1],
        }
    )

    result = rank_features_by_mutual_information(
        frame,
        feature_cols=['f_good', 'f_noise'],
        target_col='target',
    )

    assert list(result['feature']) == ['f_good', 'f_noise']
