import pandas as pd

from ML.benchmark_trailing_stop_target_quantile import pick_validation_winner, summarize_candidate


def test_summarize_candidate_for_q10_gt_zero_rule():
    frame = pd.DataFrame(
        {
            'signal': [1, 1, -1],
            'pred_trail_48_pnl_atr_x3_q10': [0.4, -0.1, 0.2],
            'pred_trail_48_pnl_atr_x3_q50': [0.8, 0.3, 0.6],
            'pred_trail_48_pnl_atr_x3_q90': [1.2, 0.9, 1.4],
            'true_trail_48_pnl_atr_x3': [1.0, -0.5, 0.6],
        }
    )

    row = summarize_candidate(
        frame,
        candidate='q10_gt_zero',
        threshold=0.0,
        true_col='true_trail_48_pnl_atr_x3',
    )

    assert row['candidate'] == 'q10_gt_zero'
    assert row['threshold'] == 0.0
    assert row['trades'] == 2
    assert row['pf'] > 1.0


def test_pick_validation_winner_prefers_pf_then_lower_ulcer_then_more_trades():
    table = pd.DataFrame(
        [
            {'candidate': 'q10_gt_zero', 'threshold': 0.0, 'pf': 1.2, 'ulcer_index_atr': 0.8, 'trades': 11},
            {'candidate': 'q10_gt_m', 'threshold': 0.3, 'pf': 1.2, 'ulcer_index_atr': 0.7, 'trades': 9},
            {'candidate': 'q10_q50_positive', 'threshold': 0.0, 'pf': 1.1, 'ulcer_index_atr': 0.1, 'trades': 20},
        ]
    )

    winner = pick_validation_winner(table, min_pf=1.0)

    assert winner['candidate'] == 'q10_gt_m'
    assert winner['threshold'] == 0.3
