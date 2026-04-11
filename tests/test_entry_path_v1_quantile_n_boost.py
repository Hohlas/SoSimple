import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, '.')

from ML import benchmark_entry_path_v1_quantile_n_boost as boost


def _write_minimal_seed(root, seed, *, n_rows=20, candidate='lb_gt_m'):
    seed_dir = root / f'seed_{seed:03d}'
    seed_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for i in range(n_rows):
        rows.append({
            'time': f'2024.01.{1 + i // 24:02d} {i % 24:02d}:00',
            'signal': 1 if i % 2 == 0 else -1,
            'pred_ret_24_dir_atr': 0.5 + i * 0.01,
            'pred_ret_24_q10': 0.1 + i * 0.005,
            'pred_ret_24_q90': 0.8 + i * 0.005,
            'true_ret_24_dir_atr': 0.3 if i % 3 != 0 else -0.2,
        })
    frame = pd.DataFrame(rows)

    for split in ['validation', 'test']:
        frame.to_csv(seed_dir / f'entry_path_v1_quantile_{split}_predictions.csv', sep=';', index=False)

    result_json = {
        'best_val_score': 0.20,
        'val_metrics': {'val_score': 0.20},
    }
    (seed_dir / 'transformer_entry_path_v1_quantile_result.json').write_text(
        json.dumps(result_json), encoding='utf-8',
    )

    rule_json = {
        'winner': {'candidate': candidate, 'rule': candidate, 'm': 0.2, 'w': 5.0,
                    'trades': 15, 'pf': 3.0, 'win_rate': 0.7, 'mean_pnl_atr': 0.5,
                    'coverage': 0.5, 'median_interval_width': 7.0, 'gross_profit': 4.5, 'gross_loss': 1.5},
        'frozen_winner': {'candidate': candidate, 'rule': candidate, 'm': 0.2, 'w': 5.0,
                          'trades': 15, 'pf': 3.0, 'win_rate': 0.7, 'mean_pnl_atr': 0.5,
                          'coverage': 0.5, 'median_interval_width': 7.0, 'gross_profit': 4.5, 'gross_loss': 1.5},
        'baseline_threshold': 0.4,
        'correction': 0.1,
        'sequential_summary': {'trades': 10, 'pf': 2.5, 'win_rate': 0.6, 'mean_pnl_atr': 0.4, 'coverage': 0.4},
        'sequential_hold_bars': 24,
        'validation_csv': str(seed_dir / 'entry_path_v1_quantile_validation_predictions.csv'),
        'test_csv': str(seed_dir / 'entry_path_v1_quantile_test_predictions.csv'),
    }
    (seed_dir / 'entry_path_v1_quantile_filter_selected_rule.json').write_text(
        json.dumps(rule_json), encoding='utf-8',
    )
    return seed_dir


def test_evaluate_gate_pass():
    result = boost.evaluate_gate(n_trades=35, pf=2.5, negative_year_slices=0, same_winner_ratio=4/5)
    assert result['verdict'] == 'gate_pass'


def test_evaluate_gate_fail_low_n():
    result = boost.evaluate_gate(n_trades=25, pf=3.0, negative_year_slices=0, same_winner_ratio=4/5)
    assert result['verdict'] == 'gate_fail'


def test_evaluate_gate_fail_low_pf():
    result = boost.evaluate_gate(n_trades=40, pf=1.5, negative_year_slices=0, same_winner_ratio=4/5)
    assert result['verdict'] == 'gate_fail'


def test_evaluate_gate_fail_negative_years():
    result = boost.evaluate_gate(n_trades=40, pf=3.0, negative_year_slices=1, same_winner_ratio=4/5)
    assert result['verdict'] == 'gate_fail'


def test_relax_sweep_returns_multiple_candidates(tmp_path):
    n = 40
    frame = pd.DataFrame({
        'time': [f'2024.01.{1 + i // 24:02d} {i % 24:02d}:00' for i in range(n)],
        'signal': [1 if i % 2 == 0 else -1 for i in range(n)],
        'pred_ret_24_dir_atr': [0.5 + i * 0.01 for i in range(n)],
        'pred_ret_24_q10': [0.1 + i * 0.005 for i in range(n)],
        'pred_ret_24_q90': [0.8 + i * 0.005 for i in range(n)],
        'true_ret_24_dir_atr': [0.3 if i % 3 != 0 else -0.2 for i in range(n)],
    })
    baseline = frame[['time', 'signal', 'pred_ret_24_dir_atr']].copy()

    result = boost.run_relax_sweep(frame, baseline, baseline_threshold=0.4)
    assert len(result) > len(boost.QUANTILE_SWEEP)
    assert 'quantile' in result.columns
    assert any(result['candidate'].str.contains('q20'))


def test_ensemble_benchmark_produces_rows(tmp_path):
    seeds = [7, 42]
    for s in seeds:
        _write_minimal_seed(tmp_path, s, n_rows=20)

    baseline_path = tmp_path / 'seed_007' / 'entry_path_v1_quantile_validation_predictions.csv'
    baseline = pd.read_csv(baseline_path, sep=';')[['time', 'signal', 'pred_ret_24_dir_atr']]
    seed_dirs = [tmp_path / f'seed_{s:03d}' for s in seeds]

    result = boost.run_ensemble_benchmark(
        seed_dirs=seed_dirs,
        split='validation',
        baseline_frame=baseline,
        baseline_threshold=0.4,
    )
    assert len(result) > 0
    assert 'method' in result.columns


def test_run_full_benchmark_produces_gate_result(tmp_path):
    seeds = [7, 17, 42]
    for s in seeds:
        _write_minimal_seed(tmp_path, s, n_rows=40)

    baseline_rule = {
        'winner': {'candidate': 'A', 'score_threshold': 0.4, 'pf': 2.0},
        'validation_csv': str(tmp_path / 'seed_007' / 'entry_path_v1_quantile_validation_predictions.csv'),
        'test_csv': str(tmp_path / 'seed_007' / 'entry_path_v1_quantile_test_predictions.csv'),
        'sequential_summary': {'pf': 1.5},
        'sequential_hold_bars': 24,
    }
    baseline_path = tmp_path / 'baseline_rule.json'
    baseline_path.write_text(json.dumps(baseline_rule), encoding='utf-8')

    result = boost.run_full_benchmark(
        root_dir=tmp_path,
        seeds=[7, 17, 42],
        baseline_rule=baseline_path,
        output_dir=tmp_path / 'output',
    )
    assert 'gate' in result
    assert result['gate']['verdict'] in ('gate_pass', 'gate_fail')
    assert 'best_candidate' in result
    assert (tmp_path / 'output' / 'n_boost_result.json').exists()


def test_count_negative_year_slices_from_trades():
    frame = pd.DataFrame({
        'time': ['2023.06.01 00:00', '2023.07.01 00:00', '2023.08.01 00:00',
                 '2024.01.01 00:00', '2024.02.01 00:00', '2024.03.01 00:00'],
        'true_ret_24_dir_atr': [-1.0, -1.0, -1.0, 1.0, 1.0, 1.0],
    })
    mask = pd.Series([True, True, True, True, True, True])
    result = boost.count_negative_year_slices_from_trades(frame, mask, min_year_trades=3)
    assert result == 1  # 2023 is negative, 2024 is positive
