import pandas as pd
import pytest

from ML.benchmark_take_skip_trailing_stop_v2 import (
    build_candidate_table,
    pick_validation_winner,
    run_benchmark,
    summarize_candidate,
)


def _frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            'time': ['2024.01.01 00:00', '2025.01.01 00:00', '2026.01.01 00:00'],
            'signal': [0, 1, 0],
            'pred_take_24_x4': [0.1, 0.9, 0.2],
            'true_take_24_x4': [0, 1, 0],
            'true_trail_24_pnl_atr_x4': [0.0, 1.2, 0.0],
        }
    )


def test_summarize_candidate_uses_full_split_coverage():
    row = summarize_candidate(
        _frame(),
        target_column='take_24_x4',
        candidate='prob_ge_threshold',
        threshold=0.8,
        coverage_years=3,
    )
    assert row['trades'] == 1
    assert row['pf'] == float('inf')
    assert row['trades_per_year'] == pytest.approx(1.0 / 3.0)


def test_build_candidate_table_contains_threshold_and_topk_candidates():
    table = build_candidate_table(_frame(), target_column='take_24_x4')
    assert {'prob_ge_threshold', 'top_k_probability'} <= set(table['candidate'])
    assert 'profit_concentration_top_10' in table.columns
    assert 'max_drawdown_atr' in table.columns


def test_pick_validation_winner_uses_soft_success_gate():
    table = pd.DataFrame(
        [
            {
                'target_column': 'take_24_x4',
                'candidate': 'prob_ge_threshold',
                'threshold': 0.7,
                'trades': 10,
                'trades_per_year': 6.0,
                'gross_profit': 5.0,
                'gross_loss': 1.0,
                'pf': 1.0,
                'negative_year_slices': 0,
                'profit_concentration_top_10': 0.2,
                'ulcer_index_atr': 1.0,
                'max_drawdown_atr': 0.5,
                'positive_rate_selected': 0.8,
            },
            {
                'target_column': 'take_24_x4',
                'candidate': 'top_k_probability',
                'threshold': 0.05,
                'trades': 12,
                'trades_per_year': 6.0,
                'gross_profit': 4.0,
                'gross_loss': 2.0,
                'pf': 1.1,
                'negative_year_slices': 0,
                'profit_concentration_top_10': 0.3,
                'ulcer_index_atr': 1.5,
                'max_drawdown_atr': 0.8,
                'positive_rate_selected': 0.7,
            },
        ]
    )
    winner = pick_validation_winner(table, min_pf=1.0, min_trades_per_year=6.0)
    assert winner is not None
    assert winner['candidate'] == 'top_k_probability'


def test_run_benchmark_fails_fast_on_bad_dates(tmp_path):
    validation = _frame()
    test = _frame()
    test.loc[2, 'time'] = 'bad-date'
    validation_csv = tmp_path / 'validation.csv'
    test_csv = tmp_path / 'test.csv'
    validation.to_csv(validation_csv, sep=';', index=False)
    test.to_csv(test_csv, sep=';', index=False)

    with pytest.raises(ValueError, match='unparseable time'):
        run_benchmark(
            validation_csv=validation_csv,
            test_csv=test_csv,
            output_dir=tmp_path / 'benchmark',
            min_pf=1.0,
            min_trades_per_year=0.1,
            targets=('take_24_x4',),
        )


def test_run_benchmark_selects_on_validation_and_freezes_to_test(tmp_path):
    validation = pd.DataFrame(
        {
            'time': ['2025.01.01 00:00', '2025.01.02 00:00'],
            'signal': [1, 1],
            'pred_take_24_x4': [0.9, 0.2],
            'true_take_24_x4': [1, 0],
            'true_trail_24_pnl_atr_x4': [1.0, -1.0],
        }
    )
    test = pd.DataFrame(
        {
            'time': ['2026.01.01 00:00', '2026.01.02 00:00'],
            'signal': [1, 1],
            'pred_take_24_x4': [0.95, 0.1],
            'true_take_24_x4': [1, 0],
            'true_trail_24_pnl_atr_x4': [0.8, -0.6],
        }
    )
    validation_csv = tmp_path / 'validation.csv'
    test_csv = tmp_path / 'test.csv'
    validation.to_csv(validation_csv, sep=';', index=False)
    test.to_csv(test_csv, sep=';', index=False)

    result = run_benchmark(
        validation_csv=validation_csv,
        test_csv=test_csv,
        output_dir=tmp_path / 'benchmark',
        min_pf=0.5,
        min_trades_per_year=0.1,
        targets=('take_24_x4',),
    )

    assert result['final_verdict']['verdict'] == 'go'
    assert result['final_verdict']['validation_winner']['target_column'] == 'take_24_x4'
    assert result['final_verdict']['test_result']['trades'] == 1
