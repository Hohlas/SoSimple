import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pandas as pd

sys.path.insert(0, '.')

from ML import benchmark_entry_path_v1_quantile_filter as bench


def test_conformal_correction_is_positive_for_missed_intervals():
    correction = bench.compute_conformal_correction(
        true_ret=pd.Series([0.0, 1.0, 2.0]),
        pred_q10=pd.Series([-0.2, 0.8, 1.6]),
        pred_q90=pd.Series([0.2, 1.2, 1.8]),
        alpha=0.10,
    )

    assert correction >= 0.0


def test_conformal_correction_uses_finite_sample_level():
    correction = bench.compute_conformal_correction(
        true_ret=pd.Series([0.0, 0.0, 10.0]),
        pred_q10=pd.Series([0.0, 0.0, 0.0]),
        pred_q90=pd.Series([0.0, 0.0, 0.0]),
        alpha=0.10,
    )

    assert correction == 10.0


def test_benchmark_main_uses_frozen_validation_winner_on_test(tmp_path, monkeypatch):
    validation_quantile = pd.DataFrame(
        {
            'time': ['2024.01.01 00:00', '2024.01.01 01:00', '2024.01.01 02:00', '2024.01.01 03:00'],
            'signal': [1, 1, -1, -1],
            'pred_ret_24_dir_atr': [0.9, 0.8, 0.2, 0.1],
            'pred_ret_12_dir_atr': [0.8, 0.7, 0.3, 0.2],
            'pred_fav_12_atr': [1.1, 1.0, 0.4, 0.3],
            'pred_adv_12_atr': [0.1, 0.2, 0.5, 0.6],
            'pred_fav_24_atr': [1.4, 1.2, 0.5, 0.4],
            'pred_adv_24_atr': [0.2, 0.3, 0.6, 0.7],
            'pred_path_6_prob_neg': [0.1, 0.2, 0.6, 0.7],
            'pred_path_6_prob_pos': [0.8, 0.7, 0.2, 0.1],
            'pred_ret_24_q10': [1.0, 0.1, -0.1, -0.2],
            'pred_ret_24_q90': [0.2, 0.9, 0.3, 0.2],
            'true_ret_24_dir_atr': [1.0, 0.8, -0.3, -0.4],
        }
    )
    test_quantile = validation_quantile.copy()

    baseline_validation = validation_quantile[['time', 'signal', 'pred_ret_24_dir_atr']].copy()
    baseline_test = test_quantile[['time', 'signal', 'pred_ret_24_dir_atr']].copy()

    val_q_path = tmp_path / 'validation_quantile.csv'
    test_q_path = tmp_path / 'test_quantile.csv'
    baseline_val_path = tmp_path / 'baseline_validation.csv'
    baseline_test_path = tmp_path / 'baseline_test.csv'
    validation_quantile.to_csv(val_q_path, sep=';', index=False)
    test_quantile.to_csv(test_q_path, sep=';', index=False)
    baseline_validation.to_csv(baseline_val_path, sep=';', index=False)
    baseline_test.to_csv(baseline_test_path, sep=';', index=False)

    baseline_rule = {
        'winner': {
            'candidate': 'A',
            'score_threshold': 0.75,
        },
        'validation_csv': str(baseline_val_path),
        'test_csv': str(baseline_test_path),
        'sequential_hold_bars': 24,
    }
    baseline_rule_path = tmp_path / 'baseline_rule.json'
    baseline_rule_path.write_text(json.dumps(baseline_rule), encoding='utf-8')

    monkeypatch.setattr(
        bench,
        'parse_args',
        lambda: SimpleNamespace(
            validation_csv=val_q_path,
            test_csv=test_q_path,
            baseline_rule=baseline_rule_path,
            output_dir=tmp_path,
            alpha=0.10,
            min_trades=1,
        ),
    )

    summarize_calls = []
    original_summarize_rule = bench.summarize_rule
    sequential_calls = []
    original_sequential_check = bench.run_sequential_check

    def spy_summarize_rule(frame, candidate, rule, m, w):
        summarize_calls.append(candidate)
        return original_summarize_rule(frame, candidate=candidate, rule=rule, m=m, w=w)

    def spy_sequential_check(frame, selected_mask, hold_bars=24):
        sequential_calls.append(hold_bars)
        return original_sequential_check(frame, selected_mask, hold_bars=hold_bars)

    monkeypatch.setattr(bench, 'summarize_rule', spy_summarize_rule)
    monkeypatch.setattr(bench, 'run_sequential_check', spy_sequential_check)

    payload = bench.main()

    assert payload['winner']['candidate'] in {'baseline', 'lb_gt_0', 'lb_gt_m', 'lb_gt_m_width_le_w'}
    assert payload['frozen_winner']['candidate'] == payload['winner']['candidate']
    assert (tmp_path / 'entry_path_v1_quantile_filter_report.md').exists()
    assert (tmp_path / 'entry_path_v1_quantile_filter_selected_rule.json').exists()
    assert (tmp_path / 'entry_path_v1_quantile_filter_validation_summary.csv').exists()
    assert (tmp_path / 'entry_path_v1_quantile_filter_test_summary.csv').exists()
    assert len(summarize_calls) == 5
    assert sequential_calls == [24]
    assert payload['sequential_summary']['trades'] >= 0
    assert payload['validation_crossed_quantile_rows'] >= 1
    assert payload['test_crossed_quantile_rows'] >= 1

    saved = json.loads((tmp_path / 'entry_path_v1_quantile_filter_selected_rule.json').read_text(encoding='utf-8'))
    assert saved['winner']['candidate'] == payload['winner']['candidate']
    assert saved['sequential_hold_bars'] == 24

    test_summary = pd.read_csv(tmp_path / 'entry_path_v1_quantile_filter_test_summary.csv', sep=';')
    assert test_summary.shape[0] == 1
    assert test_summary.iloc[0]['candidate'] == payload['winner']['candidate']


def test_build_rule_mask_lb_gt_m_uses_custom_threshold():
    """lb_gt_m with m set to a lower quantile should select more rows."""
    frame = pd.DataFrame({
        'baseline_selected': [True, True, True, True],
        'lb': [0.5, 1.0, 1.5, 2.0],
        'width': [1.0, 1.0, 1.0, 1.0],
    })
    mask_median = bench.build_rule_mask(frame, rule='lb_gt_m', m=1.25, w=0.0)
    mask_q30 = bench.build_rule_mask(frame, rule='lb_gt_m', m=0.65, w=0.0)
    assert mask_median.sum() < mask_q30.sum()


def test_compute_m_at_quantile():
    frame = pd.DataFrame({
        'baseline_selected': [True, True, True, True, False],
        'lb': [1.0, 2.0, 3.0, 4.0, 100.0],
    })
    assert bench.compute_m_at_quantile(frame, 0.5) == 2.5
    assert bench.compute_m_at_quantile(frame, 0.0) == 1.0
