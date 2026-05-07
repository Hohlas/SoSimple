import json
from pathlib import Path

import pandas as pd

from ML import run_entry_path_live_safe_retrain as runner


def test_seed_slug_pads_to_three_digits():
    assert runner.seed_slug(7) == 'seed_007'
    assert runner.seed_slug(123) == 'seed_123'


def test_run_single_seed_writes_isolated_artifacts(monkeypatch, tmp_path):
    calls = {'train': 0, 'export': 0, 'benchmark': 0}

    def fake_train_model(**kwargs):
        calls['train'] += 1
        run_dir = Path(kwargs['output_dir'])
        checkpoint = run_dir / 'transformer_entry_path_v1_features_entry_path_v1_live_safe_best.pt'
        checkpoint.write_bytes(b'checkpoint')
        return {
            'best_metric': 0.27,
            'best_epoch': 4,
            'checkpoint_path': str(checkpoint),
            'runtime_metadata': {'device': 'cpu', 'torch': 'test-torch'},
        }

    def fake_export_predictions(**kwargs):
        calls['export'] += 1
        output = Path(kwargs['output_csv'])
        output.write_text('time;signal;pred_ret_24_dir_atr;true_ret_24_dir_atr\n', encoding='utf-8')
        return output

    def fake_run_benchmark(**kwargs):
        calls['benchmark'] += 1
        output_dir = Path(kwargs['output_dir'])
        test_summary = output_dir / 'entry_path_trade_filter_test_summary.csv'
        pd.DataFrame(
            [{
                'candidate': 'A',
                'target_coverage': 0.075,
                'trades': 37,
                'pf': 3.7,
            }]
        ).to_csv(test_summary, sep=';', index=False)
        return {
            'winner': {
                'candidate': 'A',
                'target_coverage': 0.075,
                'pf': 2.5,
                'trades': 36,
            },
            'test_summary_path': str(test_summary),
            'sequential_summary': {
                'pf': 2.4,
                'trades': 26,
                'win_rate': 0.65,
            },
        }

    monkeypatch.setattr(runner, 'train_model', fake_train_model)
    monkeypatch.setattr(runner, 'export_predictions', fake_export_predictions)
    monkeypatch.setattr(runner, 'run_benchmark', fake_run_benchmark)

    result = runner.run_single_seed(
        seed=42,
        output_root=tmp_path,
        epochs=5,
        patience=10,
        batch_size=256,
        seq_len=20,
        feature_profile='entry_path_v1_live_safe',
        coverage_grid=[0.05, 0.075],
        min_period_trades=10,
        sequential_hold_bars=24,
        clear_cache=True,
        skip_existing=False,
    )

    run_dir = tmp_path / 'seed_042'
    assert calls == {'train': 1, 'export': 2, 'benchmark': 1}
    assert (run_dir / 'summary.json').exists()
    assert (run_dir / 'validation_predictions.csv').exists()
    assert (run_dir / 'test_predictions.csv').exists()
    assert result['checkpoint_path'].endswith('_best.pt')
    assert result['benchmark']['winner']['candidate'] == 'A'
    assert result['test_summary']['pf'] == 3.7


def test_summarize_runs_writes_csv_and_json(tmp_path):
    runs = [
        {
            'config': {'seed': 42},
            'checkpoint_path': 'seed_042/checkpoint.pt',
            'train_result': {
                'best_metric': 0.27,
                'best_epoch': 4,
                'runtime_metadata': {'device': 'cuda', 'torch': '2.x'},
            },
            'benchmark': {
                'winner': {'candidate': 'A', 'target_coverage': 0.075, 'pf': 2.5, 'trades': 36},
                'sequential_summary': {'pf': 2.4, 'trades': 26, 'win_rate': 0.65},
            },
            'test_summary': {'pf': 3.7, 'trades': 37},
        }
    ]

    payload = runner.summarize_runs(runs, tmp_path)

    assert Path(payload['summary_csv']).exists()
    saved = json.loads((tmp_path / 'multi_seed_summary.json').read_text(encoding='utf-8'))
    assert saved['rows'][0]['seed'] == 42
    assert saved['rows'][0]['winner'] == 'A'
