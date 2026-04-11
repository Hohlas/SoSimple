import json
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, '.')

from ML import benchmark_entry_path_v1_quantile_robustness as bench
from ML import entry_path_v1_quantile_robustness as robustness


def _write_seed_run(root: Path, seed: int, *, candidate: str = 'lb_gt_m', base_year: int = 2023) -> Path:
    seed_dir = root / f'seed_{seed:03d}'
    seed_dir.mkdir(parents=True, exist_ok=True)

    result_payload = {
        'model_name': 'transformer',
        'task': 'entry_path_v1_quantile',
        'best_val_score': 0.20 + seed / 1000.0,
        'best_epoch': 4,
        'val_metrics': {
            'val_score': 0.20 + seed / 1000.0,
            'ret_pearson_r': 0.15,
            'interval_coverage': 0.80,
            'median_interval_width': 7.0,
        },
    }
    (seed_dir / 'transformer_entry_path_v1_quantile_result.json').write_text(
        json.dumps(result_payload),
        encoding='utf-8',
    )

    rule_payload = {
        'winner': {
            'candidate': candidate,
            'rule': candidate,
            'm': -1.0,
            'w': 5.0,
            'trades': 24,
            'pf': 6.0,
            'win_rate': 0.75,
            'mean_pnl_atr': 1.2,
            'coverage': 0.5,
            'median_interval_width': 7.1,
        },
        'frozen_winner': {
            'candidate': candidate,
            'rule': candidate,
            'm': -1.0,
            'w': 5.0,
            'trades': 18,
            'pf': 5.2,
            'win_rate': 0.72,
            'mean_pnl_atr': 1.1,
            'coverage': 0.4,
            'median_interval_width': 7.3,
        },
        'sequential_hold_bars': 24,
        'sequential_summary': {
            'trades': 10,
            'accepted_indices': [0, 3, 6],
            'coverage': 0.55,
            'pf': 3.0,
            'mean_pnl_atr': 0.9,
            'win_rate': 0.7,
        },
    }
    (seed_dir / 'entry_path_v1_quantile_filter_selected_rule.json').write_text(
        json.dumps(rule_payload),
        encoding='utf-8',
    )

    rows = [
        {
            'time': f'{base_year}.01.01 00:00',
            'signal': 1,
            'pred_ret_24_dir_atr': 0.9,
            'pred_ret_24_q10': 1.0,
            'pred_ret_24_q90': 2.0,
            'true_ret_24_dir_atr': 1.5,
        },
        {
            'time': f'{base_year}.01.10 00:00',
            'signal': -1,
            'pred_ret_24_dir_atr': 0.8,
            'pred_ret_24_q10': 0.7,
            'pred_ret_24_q90': 1.3,
            'true_ret_24_dir_atr': -0.5,
        },
        {
            'time': f'{base_year + 1}.01.01 00:00',
            'signal': 1,
            'pred_ret_24_dir_atr': 0.95,
            'pred_ret_24_q10': 1.2,
            'pred_ret_24_q90': 2.4,
            'true_ret_24_dir_atr': 2.0,
        },
        {
            'time': f'{base_year + 1}.02.01 00:00',
            'signal': -1,
            'pred_ret_24_dir_atr': 0.85,
            'pred_ret_24_q10': 0.8,
            'pred_ret_24_q90': 1.6,
            'true_ret_24_dir_atr': 1.0,
        },
        {
            'time': f'{base_year + 1}.03.01 00:00',
            'signal': 1,
            'pred_ret_24_dir_atr': 0.75,
            'pred_ret_24_q10': 0.6,
            'pred_ret_24_q90': 1.1,
            'true_ret_24_dir_atr': -0.2,
        },
    ]
    pd.DataFrame(rows).to_csv(
        seed_dir / 'entry_path_v1_quantile_test_predictions.csv',
        sep=';',
        index=False,
    )
    return seed_dir


def test_load_seed_run_collects_result_rule_and_test_metrics(tmp_path):
    seed_dir = _write_seed_run(tmp_path, 42)

    summary = robustness.load_seed_run(seed_dir)

    assert summary['seed'] == 42
    assert summary['winner_candidate'] == 'lb_gt_m'
    assert summary['test_pf'] == 5.2
    assert summary['sequential_pf'] == 3.0
    assert summary['best_val_score'] == pytest.approx(0.242)


def test_load_seed_run_falls_back_to_checkpoint_tree_for_result_json(tmp_path):
    reports_root = tmp_path / 'ML' / 'reports' / 'entry_path_v1_quantile_robustness'
    seed_dir = _write_seed_run(reports_root, 42)
    result_path = seed_dir / 'transformer_entry_path_v1_quantile_result.json'
    checkpoint_dir = tmp_path / 'ML' / 'checkpoints' / 'entry_path_v1_quantile_robustness' / 'seed_042'
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_result = checkpoint_dir / result_path.name
    checkpoint_result.write_text(result_path.read_text(encoding='utf-8'), encoding='utf-8')
    result_path.unlink()

    summary = robustness.load_seed_run(seed_dir)

    assert summary['seed'] == 42
    assert summary['best_val_score'] == pytest.approx(0.242)


def test_build_yearly_summary_groups_by_year_and_counts_negative_slices(tmp_path):
    seed_dir = _write_seed_run(tmp_path, 7)

    yearly = robustness.build_yearly_summary(seed_dir, min_trades=1)

    assert set(yearly['period']) == {'2023', '2024'}
    year_2023 = yearly.loc[yearly['period'] == '2023'].iloc[0]
    assert year_2023['trades'] == 2
    assert year_2023['net_pnl_atr'] == 1.0
    assert year_2023['pf'] == 3.0


def test_build_yearly_summary_uses_selected_quantile_trades_only(tmp_path):
    seed_dir = _write_seed_run(tmp_path, 7)
    (seed_dir / 'entry_path_v1_quantile_filter_selected_rule.json').write_text(
        json.dumps(
            {
                'winner': {
                    'candidate': 'lb_gt_m',
                    'rule': 'lb_gt_m',
                    'm': 0.5,
                    'w': 10.0,
                },
                'frozen_winner': {'trades': 1, 'pf': 2.0},
                'baseline_threshold': 0.5,
                'correction': 0.0,
                'sequential_summary': {'trades': 1, 'pf': 2.0},
            }
        ),
        encoding='utf-8',
    )
    pd.DataFrame(
        [
            {
                'time': '2023.01.01 00:00',
                'signal': 1,
                'pred_ret_24_dir_atr': 0.9,
                'pred_ret_24_q10': 1.0,
                'pred_ret_24_q90': 2.0,
                'true_ret_24_dir_atr': 1.5,
            },
            {
                'time': '2023.01.02 00:00',
                'signal': 1,
                'pred_ret_24_dir_atr': 0.4,
                'pred_ret_24_q10': -2.0,
                'pred_ret_24_q90': -1.0,
                'true_ret_24_dir_atr': -5.0,
            },
        ]
    ).to_csv(seed_dir / 'entry_path_v1_quantile_test_predictions.csv', sep=';', index=False)

    yearly = robustness.build_yearly_summary(seed_dir, min_trades=1)

    assert len(yearly) == 1
    assert yearly.iloc[0]['trades'] == 1
    assert yearly.iloc[0]['net_pnl_atr'] == 1.5


def test_build_rolling_summary_uses_fixed_windows_without_refit(tmp_path):
    seed_dir = _write_seed_run(tmp_path, 17)

    rolling = robustness.build_rolling_summary(seed_dir, window_size=2, step_size=2)

    assert len(rolling) == 2
    assert rolling.iloc[0]['window_index'] == 0
    assert rolling.iloc[0]['trades'] == 2
    assert rolling.iloc[1]['window_index'] == 1


def test_build_verdict_distinguishes_go_and_reject():
    summary = pd.DataFrame([
        {'seed': 7, 'winner_candidate': 'lb_gt_m', 'test_pf': 6.0, 'test_trades': 18, 'sequential_pf': 3.2},
        {'seed': 17, 'winner_candidate': 'lb_gt_m', 'test_pf': 5.5, 'test_trades': 19, 'sequential_pf': 3.0},
        {'seed': 42, 'winner_candidate': 'lb_gt_m', 'test_pf': 4.8, 'test_trades': 17, 'sequential_pf': 2.9},
        {'seed': 77, 'winner_candidate': 'lb_gt_m', 'test_pf': 4.7, 'test_trades': 16, 'sequential_pf': 2.95},
        {'seed': 123, 'winner_candidate': 'lb_gt_0', 'test_pf': 4.5, 'test_trades': 15, 'sequential_pf': 2.87},
    ])
    yearly = pd.DataFrame([
        {'seed': 7, 'period': '2023', 'trades': 6, 'net_pnl_atr': 0.5},
        {'seed': 17, 'period': '2023', 'trades': 7, 'net_pnl_atr': 0.3},
    ])

    verdict = robustness.build_verdict(summary, yearly, baseline_test_pf=4.29, baseline_sequential_pf=2.87)

    assert verdict['verdict'] == 'go_mt4'
    assert verdict['same_rule_count'] == 4

    reject = robustness.build_verdict(
        pd.DataFrame([
            {'seed': 7, 'winner_candidate': 'baseline', 'test_pf': 3.2, 'test_trades': 9, 'sequential_pf': 1.5},
            {'seed': 17, 'winner_candidate': 'lb_gt_0', 'test_pf': 3.0, 'test_trades': 10, 'sequential_pf': 1.4},
        ]),
        pd.DataFrame([
            {'seed': 7, 'period': '2023', 'trades': 6, 'net_pnl_atr': -1.0},
            {'seed': 17, 'period': '2023', 'trades': 7, 'net_pnl_atr': -0.5},
        ]),
        baseline_test_pf=4.29,
        baseline_sequential_pf=2.87,
    )

    assert reject['verdict'] == 'reject_quantile_upgrade'


def test_benchmark_cli_aggregates_seed_dirs_and_writes_artifacts(tmp_path):
    _write_seed_run(tmp_path, 7)
    _write_seed_run(tmp_path, 17)

    baseline_rule = {
        'winner': {'candidate': 'A', 'pf': 4.29},
        'sequential_summary': {'pf': 2.87},
    }
    baseline_rule_path = tmp_path / 'baseline_rule.json'
    baseline_rule_path.write_text(json.dumps(baseline_rule), encoding='utf-8')

    output_dir = tmp_path / 'aggregate'
    payload = bench.run_benchmark(
        root_dir=tmp_path,
        seeds=[7, 17],
        baseline_rule=baseline_rule_path,
        output_dir=output_dir,
    )

    assert payload['seed_count'] == 2
    assert (output_dir / 'runs.csv').exists()
    assert (output_dir / 'yearly.csv').exists()
    assert (output_dir / 'rolling.csv').exists()
    assert (output_dir / 'summary.json').exists()
