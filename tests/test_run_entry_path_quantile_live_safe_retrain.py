import json
from pathlib import Path

import pandas as pd

from ML import run_entry_path_quantile_live_safe_retrain as runner


def test_seed_slug_pads_to_three_digits():
    assert runner.seed_slug(7) == 'seed_007'
    assert runner.seed_slug(123) == 'seed_123'


def _prediction_frame():
    return pd.DataFrame(
        {
            'time': ['2025.01.01 00:00', '2025.01.02 00:00', '2025.01.03 00:00', '2025.01.04 00:00'],
            'signal': [1, 1, 1, 0],
            'pred_ret_24_dir_atr': [0.9, 0.4, -0.1, 0.2],
            'true_ret_24_dir_atr': [1.0, -0.5, 0.25, 0.0],
        }
    )


def test_build_baseline_a_rule_writes_rule_and_summaries(tmp_path):
    validation_csv = tmp_path / 'validation_predictions.csv'
    test_csv = tmp_path / 'test_predictions.csv'
    _prediction_frame().to_csv(validation_csv, sep=';', index=False)
    _prediction_frame().to_csv(test_csv, sep=';', index=False)

    result = runner.build_baseline_a_rule(
        validation_csv=validation_csv,
        test_csv=test_csv,
        output_dir=tmp_path / 'out',
        target_coverage=0.5,
        min_period_trades=1,
        sequential_hold_bars=24,
    )

    out = tmp_path / 'out'
    assert (out / 'baseline_a_selected_rule.json').exists()
    assert (out / 'baseline_a_validation_summary.csv').exists()
    assert (out / 'baseline_a_test_summary.csv').exists()
    assert result['winner']['candidate'] == 'A'
    assert result['winner']['target_coverage'] == 0.5


def test_run_single_seed_writes_isolated_quantile_artifacts(monkeypatch, tmp_path):
    calls = {'train': 0, 'export': 0, 'baseline': 0, 'quantile': 0}

    baseline_root = tmp_path / 'baseline'
    baseline_seed = baseline_root / 'seed_042'
    baseline_seed.mkdir(parents=True)
    (baseline_seed / 'validation_predictions.csv').write_text('x\n', encoding='utf-8')
    (baseline_seed / 'test_predictions.csv').write_text('x\n', encoding='utf-8')

    def fake_train_model(**kwargs):
        calls['train'] += 1
        run_dir = Path(kwargs['output_dir'])
        checkpoint = run_dir / 'transformer_entry_path_v1_quantile_best.pt'
        checkpoint.write_bytes(b'checkpoint')
        return {
            'best_metric': 0.31,
            'best_epoch': 4,
            'checkpoint_path': str(checkpoint),
            'runtime_metadata': {'device': 'cpu', 'torch': 'test-torch'},
        }

    def fake_export_predictions(**kwargs):
        calls['export'] += 1
        output = Path(kwargs['output_csv'])
        output.write_text('time;signal;pred_ret_24_q10;pred_ret_24_q90\n', encoding='utf-8')
        return output

    def fake_build_baseline_a_rule(**kwargs):
        calls['baseline'] += 1
        out = Path(kwargs['output_dir'])
        rule = out / 'baseline_a_selected_rule.json'
        rule.write_text(
            json.dumps(
                {
                    'winner': {'candidate': 'A', 'target_coverage': 0.075, 'pf': 2.1, 'trades': 36},
                    'validation_csv': str(kwargs['validation_csv']),
                    'test_csv': str(kwargs['test_csv']),
                    'sequential_summary': {'pf': 2.0, 'trades': 29},
                }
            ),
            encoding='utf-8',
        )
        return json.loads(rule.read_text(encoding='utf-8'))

    def fake_run_quantile_benchmark(**kwargs):
        calls['quantile'] += 1
        out = Path(kwargs['output_dir'])
        test_summary = out / 'entry_path_v1_quantile_filter_test_summary.csv'
        pd.DataFrame(
            [{
                'candidate': 'lb_gt_m',
                'rule': 'lb_gt_m',
                'trades': 22,
                'pf': 3.4,
            }]
        ).to_csv(test_summary, sep=';', index=False)
        return {
            'winner': {'candidate': 'lb_gt_m', 'rule': 'lb_gt_m', 'pf': 4.1, 'trades': 24},
            'test_summary_path': str(test_summary),
            'sequential_summary': {'pf': 2.8, 'trades': 12, 'win_rate': 0.75},
        }

    monkeypatch.setattr(runner, 'train_model', fake_train_model)
    monkeypatch.setattr(runner, 'export_predictions', fake_export_predictions)
    monkeypatch.setattr(runner, 'build_baseline_a_rule', fake_build_baseline_a_rule)
    monkeypatch.setattr(runner, 'run_quantile_benchmark', fake_run_quantile_benchmark)

    result = runner.run_single_seed(
        seed=42,
        output_root=tmp_path / 'out',
        baseline_root=baseline_root,
        epochs=5,
        patience=10,
        batch_size=256,
        seq_len=20,
        baseline_coverage=0.075,
        alpha=0.1,
        min_trades=10,
        min_period_trades=10,
        sequential_hold_bars=24,
        clear_cache=True,
        skip_existing=False,
    )

    run_dir = tmp_path / 'out' / 'seed_042'
    assert calls == {'train': 1, 'export': 2, 'baseline': 1, 'quantile': 1}
    assert (run_dir / 'summary.json').exists()
    assert (run_dir / 'entry_path_v1_quantile_validation_predictions.csv').exists()
    assert (run_dir / 'entry_path_v1_quantile_test_predictions.csv').exists()
    assert result['quantile_benchmark']['winner']['candidate'] == 'lb_gt_m'
    assert result['quantile_test_summary']['pf'] == 3.4


def test_summarize_runs_writes_csv_and_json(tmp_path):
    runs = [
        {
            'config': {'seed': 42},
            'checkpoint_path': 'seed_042/checkpoint.pt',
            'baseline_rule_path': 'seed_042/baseline_a_selected_rule.json',
            'train_result': {
                'best_metric': 0.31,
                'best_epoch': 4,
                'runtime_metadata': {'device': 'cpu', 'torch': '2.x'},
            },
            'baseline_rule': {
                'winner': {'candidate': 'A', 'target_coverage': 0.075, 'pf': 2.1, 'trades': 36},
                'sequential_summary': {'pf': 2.0, 'trades': 29},
            },
            'quantile_benchmark': {
                'winner': {'candidate': 'lb_gt_m', 'rule': 'lb_gt_m', 'pf': 4.1, 'trades': 24},
                'sequential_summary': {'pf': 2.8, 'trades': 12, 'win_rate': 0.75},
            },
            'quantile_test_summary': {'pf': 3.4, 'trades': 22},
        }
    ]

    payload = runner.summarize_runs(runs, tmp_path)

    assert Path(payload['summary_csv']).exists()
    saved = json.loads((tmp_path / 'multi_seed_summary.json').read_text(encoding='utf-8'))
    assert saved['rows'][0]['seed'] == 42
    assert saved['winner_counts']['lb_gt_m'] == 1
