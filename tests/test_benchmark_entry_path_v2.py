import sys

import pandas as pd

sys.path.insert(0, '.')

from ML.benchmark_entry_path_v2 import build_candidate_scores
from ML.benchmark_entry_path_v2 import pick_candidate
from ML.benchmark_entry_path_v2 import summarize_candidate


def test_build_candidate_scores_expands_bounded_candidate_set_without_path6_primary_axis():
    frame = pd.DataFrame(
        {
            'signal': [1, -1],
            'pred_ret_12_dir_atr': [0.4, -0.2],
            'pred_ret_24_dir_atr': [0.6, -0.1],
            'pred_fav_12_atr': [1.0, 0.5],
            'pred_adv_12_atr': [0.2, 0.4],
            'pred_fav_24_atr': [1.4, 0.6],
            'pred_adv_24_atr': [0.3, 0.5],
            'pred_path_6_prob_neg': [0.2, 0.4],
            'pred_path_6_prob_flat': [0.3, 0.2],
            'pred_path_6_prob_pos': [0.5, 0.4],
        }
    )

    scores = build_candidate_scores(frame)

    expected = {
        'ret24_only',
        'ret12_plus_ret24_w50',
        'edge12_plus_edge24_w50',
        'ret24_minus_adv24_l10',
        'fav24_minus_adv24_l10',
        'ret24_over_adv24',
        'fav24_over_adv24',
        'ret24_fav12_adv12_a05_b10',
        'ret24_nonflat_confidence',
    }
    assert expected.issubset(scores.keys())
    assert 'path6_prob' not in scores


def test_summarize_candidate_includes_equity_smoothness_metrics():
    frame = pd.DataFrame(
        {
            'time': ['2024.01.01 00:00', '2024.01.02 00:00', '2024.01.03 00:00'],
            'signal': [1, 1, 1],
            'score_x': [0.9, 0.8, 0.7],
            'true_ret_24_dir_atr': [2.0, -1.5, 0.5],
        }
    )
    frame['time'] = pd.to_datetime(frame['time'], format='%Y.%m.%d %H:%M')

    result = summarize_candidate(frame, candidate='score_x', threshold=0.0)

    assert result['candidate'] == 'score_x'
    assert 'ulcer_index_atr' in result
    assert 'max_drawdown_atr' in result
    assert result['max_drawdown_atr'] > 0.0


def test_pick_candidate_prefers_pf_positive_family_over_least_bad_path_style_candidate():
    table = pd.DataFrame(
        [
            {
                'candidate': 'ret24_nonflat_confidence',
                'pf': 0.95,
                'trades_per_year': 40.0,
                'negative_year_slices': 0,
                'profit_concentration_top_10': 0.22,
                'ulcer_index_atr': 1.2,
                'max_drawdown_atr': 2.0,
            },
            {
                'candidate': 'ret24_minus_adv24_l10',
                'pf': 1.35,
                'trades_per_year': 44.0,
                'negative_year_slices': 0,
                'profit_concentration_top_10': 0.21,
                'ulcer_index_atr': 1.4,
                'max_drawdown_atr': 2.4,
            },
        ]
    )

    result = pick_candidate(table, min_pf=2.0, target_trades_per_year=40)

    assert result['candidate'] == 'ret24_minus_adv24_l10'
