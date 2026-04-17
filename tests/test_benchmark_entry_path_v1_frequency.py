import sys

import pandas as pd

sys.path.insert(0, '.')

from ML.benchmark_entry_path_v1_frequency import pick_candidate


def test_pick_candidate_requires_pf_and_trades_per_year():
    frame = pd.DataFrame(
        [
            {'candidate': 'a', 'pf': 2.4, 'trades_per_year': 22, 'negative_year_slices': 0, 'profit_concentration_top_10': 0.20},
            {'candidate': 'b', 'pf': 2.1, 'trades_per_year': 44, 'negative_year_slices': 0, 'profit_concentration_top_10': 0.18},
            {'candidate': 'c', 'pf': 1.8, 'trades_per_year': 55, 'negative_year_slices': 0, 'profit_concentration_top_10': 0.15},
        ]
    )

    result = pick_candidate(frame, min_pf=2.0, target_trades_per_year=40)

    assert result['candidate'] == 'b'
