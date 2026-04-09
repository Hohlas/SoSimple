import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

sys.path.insert(0, '.')

from ML import benchmark_entry_path_trade_filter as bench
from ML import entry_path_trade_filter as etf


def test_candidate_a_uses_pred_ret_24_dir_atr():
    frame = pd.DataFrame({'pred_ret_24_dir_atr': [0.4, -0.2, 0.1]})
    score = etf.build_candidate_a_score(frame)
    assert np.allclose(score, np.array([0.4, -0.2, 0.1]))


def test_percentile_rank_uses_only_validation_distribution():
    fit = etf.fit_percentile_rank(np.array([10.0, 20.0, 30.0, 40.0]))
    transformed = etf.apply_percentile_rank(np.array([5.0, 20.0, 35.0, 50.0]), fit)
    assert np.allclose(transformed, np.array([0.0, 0.5, 0.75, 1.0]))


def test_candidate_b_score_uses_fixed_weights():
    normalized = pd.DataFrame({
        'ret24': [0.9, 0.1],
        'ret12': [0.8, 0.2],
        'edge12': [0.7, 0.3],
        'edge24': [0.6, 0.4],
        'path6': [0.5, 0.5],
    })
    score = etf.compose_candidate_b_score(normalized)
    assert np.allclose(score, np.array([0.78, 0.22]))


def test_candidate_b_score_without_path6_renormalizes_other_weights():
    normalized = pd.DataFrame({
        'ret24': [0.9, 0.1],
        'ret12': [0.8, 0.2],
        'edge12': [0.7, 0.3],
        'edge24': [0.6, 0.4],
        'path6': [0.0, 1.0],
    })

    score = etf.compose_candidate_b_score(normalized, include_path6=False)

    expected = np.array([
        (0.45 * 0.9 + 0.20 * 0.8 + 0.15 * 0.7 + 0.10 * 0.6) / 0.90,
        (0.45 * 0.1 + 0.20 * 0.2 + 0.15 * 0.3 + 0.10 * 0.4) / 0.90,
    ])
    assert np.allclose(score, expected)


def test_candidate_b_pipeline_preserves_index_and_orders_scores():
    frame = pd.DataFrame(
        {
            'pred_ret_24_dir_atr': [0.1, 0.8, 0.4],
            'pred_ret_12_dir_atr': [0.2, 0.7, 0.3],
            'pred_fav_12_atr': [0.4, 0.9, 0.5],
            'pred_adv_12_atr': [0.1, 0.2, 0.4],
            'pred_fav_24_atr': [0.5, 1.0, 0.6],
            'pred_adv_24_atr': [0.2, 0.3, 0.5],
            'pred_path_6_prob_pos': [0.2, 0.9, 0.4],
            'pred_path_6_prob_neg': [0.3, 0.1, 0.5],
        },
        index=[10, 20, 30],
    )

    components = etf.build_candidate_b_components(frame)
    scaler = etf.fit_candidate_b_score(frame)
    score = etf.apply_candidate_b_score(frame, scaler)

    assert components.index.equals(frame.index)
    assert len(score) == len(frame)
    assert score.argmax() == 1


def test_percentile_rank_maps_smallest_fit_value_to_one_over_n():
    fit = etf.fit_percentile_rank(np.array([10.0, 20.0, 30.0, 40.0]))
    transformed = etf.apply_percentile_rank(np.array([10.0]), fit)
    assert np.allclose(transformed, np.array([0.25]))


def test_score_active_rows_aligns_shuffled_series_by_index():
    frame = pd.DataFrame(
        {
            'signal': [1, 0, -1],
            'true_ret_24_dir_atr': [0.3, 0.0, -0.2],
        },
        index=[10, 20, 30],
    )
    score = pd.Series([0.8, 0.7, 0.9], index=[30, 20, 10])

    active = etf._score_active_rows(frame, score)

    assert active.index.tolist() == [10, 30]
    assert np.allclose(active['score'].to_numpy(), np.array([0.9, 0.8]))


def test_evaluate_score_grid_computes_pf_and_period_stability():
    frame = pd.DataFrame({
        'time': pd.to_datetime([
            '2023-01-01 00:00',
            '2023-01-02 00:00',
            '2024-01-01 00:00',
            '2024-01-02 00:00',
        ]),
        'signal': [1, 1, -1, -1],
        'true_ret_24_dir_atr': [1.0, -0.5, 1.2, -0.4],
    })
    score = [0.9, 0.8, 0.2, 0.1]

    table = etf.evaluate_score_grid(frame, score, candidate='A', target_coverages=[0.50], min_period_trades=1)

    assert table.iloc[0]['candidate'] == 'A'
    assert table.iloc[0]['trades'] == 2
    assert table.iloc[0]['pf'] == 2.0
    assert np.isclose(table.iloc[0]['coverage'], 0.5)
    assert np.isclose(table.iloc[0]['coverage_gap'], 0.0)
    assert np.isclose(table.iloc[0]['score_threshold'], 0.5)
    assert table.iloc[0]['stability_ratio'] == 1.0
    assert table.iloc[0]['period_mode'] == 'half_year'
    assert table.iloc[0]['eligible_periods'] == 1
    assert table.iloc[0]['stable_periods'] == 1
    assert table.iloc[0]['worst_period_pf'] == 2.0
    detail = json.loads(table.iloc[0]['period_detail_json'])
    assert set(detail.keys()) == {'2023H1'}


def test_evaluate_score_grid_uses_year_mode_when_two_years_are_eligible():
    frame = pd.DataFrame({
        'time': pd.to_datetime([
            '2023-01-01 00:00',
            '2023-01-02 00:00',
            '2024-01-01 00:00',
            '2024-01-02 00:00',
        ]),
        'signal': [1, 1, -1, -1],
        'true_ret_24_dir_atr': [1.0, -0.5, 1.2, -0.4],
    })
    score = [0.9, 0.8, 0.2, 0.1]

    table = etf.evaluate_score_grid(frame, score, candidate='A', target_coverages=[1.0], min_period_trades=2)

    assert table.iloc[0]['period_mode'] == 'year'
    assert table.iloc[0]['eligible_periods'] == 2
    assert table.iloc[0]['stable_periods'] == 2
    detail = json.loads(table.iloc[0]['period_detail_json'])
    assert set(detail.keys()) == {'2023', '2024'}


def test_evaluate_frozen_threshold_uses_passed_threshold_directly():
    frame = pd.DataFrame({
        'time': pd.to_datetime([
            '2023-01-01 00:00',
            '2023-01-02 00:00',
            '2024-01-01 00:00',
            '2024-01-02 00:00',
        ]),
        'signal': [1, 1, -1, -1],
        'true_ret_24_dir_atr': [1.0, -0.5, 1.2, -0.4],
    })
    score = [0.9, 0.8, 0.2, 0.1]

    table = etf.evaluate_frozen_threshold(
        frame,
        score,
        candidate='F',
        threshold=0.85,
        target_coverage=1.0,
        min_period_trades=1,
    )

    assert table.iloc[0]['score_threshold'] == 0.85
    assert table.iloc[0]['trades'] == 1
    assert np.isclose(table.iloc[0]['coverage'], 0.25)
    assert np.isclose(table.iloc[0]['coverage_gap'], 0.75)


def test_nat_rows_do_not_create_fake_periods_or_eligible_counts():
    frame = pd.DataFrame({
        'time': pd.to_datetime([
            '2023-01-01 00:00',
            None,
            '2023-01-02 00:00',
            '2024-01-01 00:00',
            '2024-01-02 00:00',
        ]),
        'signal': [1, 1, 1, -1, -1],
        'true_ret_24_dir_atr': [1.0, 0.3, -0.5, 1.2, -0.4],
    })
    score = [0.95, 0.90, 0.85, 0.20, 0.10]

    table = etf.evaluate_score_grid(frame, score, candidate='N', target_coverages=[1.0], min_period_trades=2)

    assert table.iloc[0]['period_mode'] == 'year'
    assert table.iloc[0]['eligible_periods'] == 2
    detail = json.loads(table.iloc[0]['period_detail_json'])
    assert '<NA>' not in detail
    assert set(detail.keys()) == {'2023', '2024'}


def test_pick_best_slice_prefers_pf_then_stability_then_coverage_gap_then_trades():
    table = pd.DataFrame([
        {'candidate': 'pf_wins', 'pf': 1.80, 'stability_ratio': 0.1, 'coverage_gap': 0.9, 'trades': 10},
        {'candidate': 'trades_wins', 'pf': 1.70, 'stability_ratio': 0.9, 'coverage_gap': 0.2, 'trades': 20},
        {'candidate': 'coverage_wins', 'pf': 1.70, 'stability_ratio': 0.9, 'coverage_gap': 0.2, 'trades': 10},
        {'candidate': 'coverage_gap_worse', 'pf': 1.70, 'stability_ratio': 0.9, 'coverage_gap': 0.5, 'trades': 10},
        {'candidate': 'stability_worse', 'pf': 1.70, 'stability_ratio': 0.5, 'coverage_gap': 0.2, 'trades': 50},
    ])

    best = etf.pick_best_slice(table)

    assert best['candidate'] == 'pf_wins'
    assert table.sort_values(
        ['pf', 'stability_ratio', 'coverage_gap', 'trades'],
        ascending=[False, False, True, False],
    )['candidate'].tolist() == [
        'pf_wins',
        'trades_wins',
        'coverage_wins',
        'coverage_gap_worse',
        'stability_worse',
    ]


def test_pick_best_slice_prefers_workable_trade_count_over_tiny_pf_spike():
    table = pd.DataFrame([
        {
            'candidate': 'tiny_tail',
            'pf': 6.0,
            'stability_ratio': 0.0,
            'coverage_gap': 0.0,
            'trades': 24,
            'eligible_periods': 0,
        },
        {
            'candidate': 'workable_tail',
            'pf': 2.5,
            'stability_ratio': 1.0,
            'coverage_gap': 0.001,
            'trades': 36,
            'eligible_periods': 2,
        },
        {
            'candidate': 'too_weak',
            'pf': 1.2,
            'stability_ratio': 1.0,
            'coverage_gap': 0.001,
            'trades': 60,
            'eligible_periods': 4,
        },
    ])

    best = etf.pick_best_slice(table)

    assert best['candidate'] == 'workable_tail'


def test_sequential_check_skips_overlapping_rows():
    frame = pd.DataFrame({
        'time': pd.to_datetime([
            '2024-01-01 00:00',
            '2024-01-01 01:00',
            '2024-01-01 02:00',
            '2024-01-01 03:00',
            '2024-01-01 04:00',
            '2024-01-01 05:00',
        ]),
        'signal': [1, 1, 0, -1, 0, 1],
        'true_ret_24_dir_atr': [1.0, -0.2, 0.0, -1.0, 0.0, 0.7],
    })
    selected_mask = pd.Series([True, True, True, True], index=frame.index[frame['signal'] != 0])

    out = etf.run_sequential_check(frame, selected_mask, hold_bars=2)

    assert out['trades'] == 3
    assert out['accepted_indices'] == [0, 3, 5]
    assert np.isclose(out['coverage'], 0.75)


def test_sequential_check_rejects_duplicate_index_series_alignment():
    frame = pd.DataFrame({
        'signal': [1, 0, -1],
        'true_ret_24_dir_atr': [0.4, 0.0, -0.2],
    }, index=[10, 10, 20])
    selected_mask = pd.Series([True, True, True], index=[10, 10, 20])

    with np.testing.assert_raises_regex(ValueError, 'requires unique indices'):
        etf.run_sequential_check(frame, selected_mask, hold_bars=2)


def test_trade_filter_report_mentions_winner_and_secondary_check():
    validation_best = {'candidate': 'B', 'pf': 1.42, 'coverage': 0.69, 'stability_ratio': 1.0}
    test_row = {'candidate': 'B', 'pf': 1.31, 'coverage': 0.68, 'stability_ratio': 1.0}
    sequential = {'trades': 24, 'pf': 1.18, 'coverage': 0.52}

    report = etf.build_trade_filter_report_markdown(
        validation_best=validation_best,
        test_row=test_row,
        sequential_summary=sequential,
        rule_path='ML/reports/entry_path_trade_filter_selected_rule.json',
    )

    assert report.startswith('# Entry Path Trade Filter Report')
    assert 'Победитель: **B**' in report
    assert '## Validation Winner' in report
    assert '## Test Check' in report
    assert '## Sequential Check' in report
    assert '- coverage_vs_selected: **52.00%**' in report
    assert '- coverage: **52.00%**' not in report
    assert '## Frozen Rule' in report


def test_benchmark_main_cli_writes_rule_and_report(tmp_path, monkeypatch, capsys):
    val = pd.DataFrame({
        'time': ['2023.01.01 00:00', '2023.01.02 00:00', '2024.01.01 00:00', '2024.01.02 00:00'],
        'signal': [1, 1, -1, -1],
        'pred_ret_12_dir_atr': [0.9, 0.8, 0.2, 0.1],
        'pred_ret_24_dir_atr': [0.9, 0.8, 0.2, 0.1],
        'pred_fav_12_atr': [1.2, 1.1, 0.4, 0.3],
        'pred_adv_12_atr': [0.2, 0.3, 0.5, 0.6],
        'pred_fav_24_atr': [1.5, 1.3, 0.5, 0.4],
        'pred_adv_24_atr': [0.3, 0.4, 0.6, 0.7],
        'pred_path_6_prob_neg': [0.1, 0.2, 0.6, 0.7],
        'pred_path_6_prob_pos': [0.8, 0.7, 0.2, 0.1],
        'true_ret_24_dir_atr': [1.0, 0.8, -0.3, -0.4],
    })
    test = val.copy()

    val_path = tmp_path / 'val.csv'
    test_path = tmp_path / 'test.csv'
    val.to_csv(val_path, sep=';', index=False)
    test.to_csv(test_path, sep=';', index=False)

    monkeypatch.setattr(
        bench,
        'parse_args',
        lambda: SimpleNamespace(
            validation_csv=val_path,
            test_csv=test_path,
            output_dir=tmp_path,
            coverage_grid=[0.70],
            min_period_trades=1,
            sequential_hold_bars=2,
        ),
    )

    bench.main()
    captured = capsys.readouterr()
    out = json.loads(captured.out)

    assert out['winner']['candidate'] in {'A', 'B', 'B_no_path6'}
    assert (tmp_path / 'entry_path_trade_filter_validation_summary.csv').exists()
    assert (tmp_path / 'entry_path_trade_filter_test_summary.csv').exists()
    assert (tmp_path / 'entry_path_trade_filter_selected_rule.json').exists()
    assert (tmp_path / 'entry_path_trade_filter_report.md').exists()

    validation_summary = pd.read_csv(tmp_path / 'entry_path_trade_filter_validation_summary.csv', sep=';')
    assert {'A', 'B', 'B_no_path6'}.issubset(set(validation_summary['candidate']))

    payload = json.loads((tmp_path / 'entry_path_trade_filter_selected_rule.json').read_text(encoding='utf-8'))
    assert payload['winner']['candidate'] == out['winner']['candidate']
    assert Path(payload['validation_csv']).name == 'val.csv'
