import pandas as pd

from ML.benchmark_take_skip_trailing_stop_v2_followup import (
    build_candidate_table,
    pair_score_targets_with_eval_pnl,
    pick_frequency_first,
    pick_quality_first,
    run_followup_benchmark,
    summarize_candidate,
)


def _frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            'time': [
                '2024.01.01 00:00',
                '2024.06.01 00:00',
                '2025.01.01 00:00',
                '2025.06.01 00:00',
            ],
            'signal': [1, 1, 1, 1],
            'pred_take_24_x8': [0.95, 0.82, 0.68, 0.54],
            'pred_take_24_x4': [0.80, 0.79, 0.60, 0.58],
            'true_trail_24_pnl_atr_x8': [2.0, 1.0, -0.5, 0.6],
            'true_trail_24_pnl_atr_x10': [2.2, 1.3, -0.2, 0.9],
            'true_trail_24_pnl_atr_x12': [2.4, 1.4, 0.1, 1.1],
        }
    )


def test_pair_score_targets_with_eval_pnl_adds_x10_x12_followups():
    pairs = pair_score_targets_with_eval_pnl(
        score_targets=['take_12_x2', 'take_24_x8', 'take_48_x4'],
        eval_x_values=(8, 10, 12),
    )

    assert ('take_24_x8', 'true_trail_24_pnl_atr_x8') in pairs
    assert ('take_24_x8', 'true_trail_24_pnl_atr_x10') in pairs
    assert ('take_24_x8', 'true_trail_24_pnl_atr_x12') in pairs
    assert ('take_12_x2', 'true_trail_12_pnl_atr_x10') in pairs
    assert ('take_48_x4', 'true_trail_48_pnl_atr_x12') in pairs


def test_summarize_candidate_scores_cross_exit_pair():
    row = summarize_candidate(
        _frame(),
        score_target='take_24_x8',
        eval_pnl_column='true_trail_24_pnl_atr_x10',
        candidate='prob_ge_threshold',
        threshold=0.8,
        coverage_years=2,
    )

    assert row['score_target'] == 'take_24_x8'
    assert row['eval_pnl_column'] == 'true_trail_24_pnl_atr_x10'
    assert row['trades'] == 2
    assert row['pf'] == float('inf')
    assert row['trades_per_year'] == 1.0


def test_build_candidate_table_contains_both_candidate_families():
    table = build_candidate_table(
        _frame(),
        pairings=[('take_24_x8', 'true_trail_24_pnl_atr_x8')],
        thresholds=(0.7,),
        top_k_values=(0.5,),
    )

    assert {'prob_ge_threshold', 'top_k_probability'} == set(table['candidate'])
    assert set(table['score_target']) == {'take_24_x8'}
    assert set(table['eval_pnl_column']) == {'true_trail_24_pnl_atr_x8'}


def test_pick_frequency_first_prefers_more_trades_when_pf_above_one():
    table = pd.DataFrame(
        [
            {
                'score_target': 'take_24_x8',
                'eval_pnl_column': 'true_trail_24_pnl_atr_x8',
                'candidate': 'prob_ge_threshold',
                'threshold': 0.8,
                'trades': 10,
                'trades_per_year': 5.0,
                'gross_profit': 8.0,
                'gross_loss': 4.0,
                'pf': 2.0,
                'negative_year_slices': 0,
                'profit_concentration_top_10': 0.2,
                'ulcer_index_atr': 1.0,
                'max_drawdown_atr': 2.0,
                'positive_rate_selected': 0.7,
            },
            {
                'score_target': 'take_24_x8',
                'eval_pnl_column': 'true_trail_24_pnl_atr_x10',
                'candidate': 'top_k_probability',
                'threshold': 0.2,
                'trades': 16,
                'trades_per_year': 8.0,
                'gross_profit': 9.0,
                'gross_loss': 6.0,
                'pf': 1.5,
                'negative_year_slices': 0,
                'profit_concentration_top_10': 0.3,
                'ulcer_index_atr': 1.5,
                'max_drawdown_atr': 3.0,
                'positive_rate_selected': 0.6,
            },
        ]
    )

    winner = pick_frequency_first(table, min_pf=1.0)

    assert winner is not None
    assert winner['eval_pnl_column'] == 'true_trail_24_pnl_atr_x10'
    assert winner['trades_per_year'] == 8.0


def test_run_followup_benchmark_emits_quality_and_frequency_winners(tmp_path):
    validation_csv = tmp_path / 'validation.csv'
    test_csv = tmp_path / 'test.csv'
    _frame().to_csv(validation_csv, sep=';', index=False)
    _frame().to_csv(test_csv, sep=';', index=False)

    result = run_followup_benchmark(
        validation_csv=validation_csv,
        test_csv=test_csv,
        output_dir=tmp_path / 'followup',
        pairings=[('take_24_x8', 'true_trail_24_pnl_atr_x8'), ('take_24_x8', 'true_trail_24_pnl_atr_x12')],
        thresholds=(0.5, 0.7),
        top_k_values=(0.5,),
        min_pf=1.0,
        min_trades_per_year=0.1,
    )

    assert result['quality_first']['validation_winner'] is not None
    assert result['frequency_first']['validation_winner'] is not None
    assert result['quality_first']['test_result'] is not None
    assert result['frequency_first']['test_result'] is not None
