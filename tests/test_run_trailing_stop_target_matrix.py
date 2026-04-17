import json

import numpy as np
import pandas as pd

from ML.run_trailing_stop_target_matrix import (
    DEFAULT_MATRIX_CONFIGS,
    _jsonable,
    config_slug,
    run_benchmark,
    run_single_config,
)


def test_default_matrix_covers_three_sequence_lengths():
    slugs = {config_slug(row['seq_len']) for row in DEFAULT_MATRIX_CONFIGS}
    assert slugs == {
        'transformer_seq20',
        'transformer_seq50',
        'transformer_seq100',
    }


def test_jsonable_converts_numpy_scalars_and_arrays():
    payload = _jsonable({'value': np.float32(1.25), 'vector': np.array([1.0, 2.0], dtype=np.float32)})
    assert payload == {'value': 1.25, 'vector': [1.0, 2.0]}


def test_run_single_config_writes_summary_and_benchmark(monkeypatch, tmp_path):
    import ML.run_trailing_stop_target_matrix as matrix

    checkpoint_dir = tmp_path / 'checkpoints'
    reports_dir = tmp_path / 'reports'
    checkpoint_dir.mkdir()
    reports_dir.mkdir()

    monkeypatch.setattr(matrix, 'CHECKPOINTS_DIR', checkpoint_dir)
    monkeypatch.setattr(matrix, 'REPORTS_DIR', reports_dir)

    def fake_train_model(**kwargs):
        ckpt = checkpoint_dir / 'transformer_trailing_stop_target_v1_best.pt'
        ckpt.write_bytes(b'checkpoint')
        return {'best_metric': 0.25, 'task': kwargs['task']}

    def fake_run_evaluation(**kwargs):
        assert kwargs['seq_len_override'] == 20
        (reports_dir / 'evaluate_test_trailing_stop_target_v1.md').write_text('ok', encoding='utf-8')
        (reports_dir / 'trailing_stop_target_test_predictions.csv').write_text('time;signal\n', encoding='utf-8')

    def fake_generate_signals(**kwargs):
        assert kwargs['seq_len_override'] == 20
        prefix = tmp_path / 'ignored'
        if kwargs['research_out_prefix']:
            prefix = matrix.Path(kwargs['research_out_prefix'])
        validation = pd.DataFrame(
            {
                'time': ['2025.01.01 00:00', '2025.01.02 00:00', '2025.01.03 00:00'],
                'signal': [1, 1, -1],
                'pred_trail_48_pnl_atr_x2': [1.8, 1.2, 0.4],
                'true_trail_48_pnl_atr_x2': [2.0, -1.0, -0.5],
                'pred_trail_48_pnl_atr_x3': [1.4, 0.9, 0.3],
                'true_trail_48_pnl_atr_x3': [1.5, -0.5, -0.2],
                'pred_trail_48_pnl_atr_x4': [1.1, 0.8, 0.2],
                'true_trail_48_pnl_atr_x4': [1.0, -0.5, -0.2],
                'pred_trail_48_pnl_atr_x6': [0.9, 0.6, 0.1],
                'true_trail_48_pnl_atr_x6': [0.9, -0.4, -0.1],
                'pred_trail_48_pnl_atr_x8': [0.7, 0.5, 0.1],
                'true_trail_48_pnl_atr_x8': [0.7, -0.3, -0.1],
            }
        )
        test = pd.DataFrame(
            {
                'time': ['2025.02.01 00:00', '2025.02.02 00:00'],
                'signal': [1, -1],
                'pred_trail_48_pnl_atr_x2': [1.7, 0.2],
                'true_trail_48_pnl_atr_x2': [1.5, -0.8],
                'pred_trail_48_pnl_atr_x3': [1.2, 0.2],
                'true_trail_48_pnl_atr_x3': [1.2, -0.3],
                'pred_trail_48_pnl_atr_x4': [1.0, 0.1],
                'true_trail_48_pnl_atr_x4': [0.9, -0.2],
                'pred_trail_48_pnl_atr_x6': [0.8, 0.1],
                'true_trail_48_pnl_atr_x6': [0.8, -0.2],
                'pred_trail_48_pnl_atr_x8': [0.6, 0.1],
                'true_trail_48_pnl_atr_x8': [0.6, -0.2],
            }
        )
        validation.to_csv(prefix.parent / f'{prefix.name}_validation_predictions.csv', sep=';', index=False)
        test.to_csv(prefix.parent / f'{prefix.name}_test_predictions.csv', sep=';', index=False)

    monkeypatch.setattr(matrix, 'train_model', fake_train_model)
    monkeypatch.setattr(matrix, 'run_evaluation', fake_run_evaluation)
    monkeypatch.setattr(matrix, 'generate_signals', fake_generate_signals)

    result = run_single_config(
        seq_len=20,
        output_dir=tmp_path / 'matrix',
        epochs=1,
        patience=1,
        batch_size=8,
        seed=42,
        min_pf=1.0,
        skip_existing=False,
    )

    summary_path = tmp_path / 'matrix' / 'transformer_seq20' / 'summary.json'
    assert summary_path.exists()
    saved = json.loads(summary_path.read_text(encoding='utf-8'))
    assert saved['config']['seq_len'] == 20
    assert saved['config']['target_columns'] == [
        'trail_48_pnl_atr_x2',
        'trail_48_pnl_atr_x3',
        'trail_48_pnl_atr_x4',
        'trail_48_pnl_atr_x6',
        'trail_48_pnl_atr_x8',
    ]
    assert saved['benchmarks']['trail_48_pnl_atr_x2']['final_verdict']['verdict'] == 'go'
    assert result['benchmarks']['trail_48_pnl_atr_x2']['final_verdict']['validation_winner']['candidate'] == 'pred_trail_48_pnl_atr_x2'


def test_run_benchmark_rejects_when_no_candidate_meets_min_pf(tmp_path):
    validation = pd.DataFrame(
        {
            'time': ['2025.01.01 00:00', '2025.01.02 00:00'],
            'signal': [1, 1],
            'pred_trail_48_pnl_atr_x3': [0.7, 0.2],
            'true_trail_48_pnl_atr_x3': [-1.0, -0.5],
        }
    )
    test = pd.DataFrame(
        {
            'time': ['2025.02.01 00:00'],
            'signal': [1],
            'pred_trail_48_pnl_atr_x3': [0.3],
            'true_trail_48_pnl_atr_x3': [-0.2],
        }
    )
    validation_csv = tmp_path / 'validation.csv'
    test_csv = tmp_path / 'test.csv'
    validation.to_csv(validation_csv, sep=';', index=False)
    test.to_csv(test_csv, sep=';', index=False)

    result = run_benchmark(
        validation_csv=validation_csv,
        test_csv=test_csv,
        target_column='trail_48_pnl_atr_x3',
        output_dir=tmp_path / 'benchmark',
        min_pf=1.0,
    )

    assert result['final_verdict']['verdict'] == 'reject'
    assert result['final_verdict']['validation_winner'] is None


def test_run_single_config_skip_existing_ignores_stale_hyperparams(monkeypatch, tmp_path):
    import ML.run_trailing_stop_target_matrix as matrix

    checkpoint_dir = tmp_path / 'checkpoints'
    reports_dir = tmp_path / 'reports'
    checkpoint_dir.mkdir()
    reports_dir.mkdir()
    monkeypatch.setattr(matrix, 'CHECKPOINTS_DIR', checkpoint_dir)
    monkeypatch.setattr(matrix, 'REPORTS_DIR', reports_dir)

    run_dir = tmp_path / 'matrix' / 'transformer_seq20'
    run_dir.mkdir(parents=True)
    (run_dir / 'summary.json').write_text(
        json.dumps(
            {
                'config': {
                    'seq_len': 20,
                    'epochs': 1,
                    'patience': 1,
                    'batch_size': 8,
                    'seed': 42,
                    'min_pf': 1.0,
                }
            }
        ),
        encoding='utf-8',
    )

    calls = {'train': 0}

    def fake_train_model(**kwargs):
        calls['train'] += 1
        (checkpoint_dir / 'transformer_trailing_stop_target_v1_best.pt').write_bytes(b'checkpoint')
        return {'best_metric': 0.1}

    def fake_run_evaluation(**kwargs):
        assert kwargs['seq_len_override'] == 20
        (reports_dir / 'evaluate_test_trailing_stop_target_v1.md').write_text('ok', encoding='utf-8')
        (reports_dir / 'trailing_stop_target_test_predictions.csv').write_text('time;signal\n', encoding='utf-8')

    def fake_generate_signals(**kwargs):
        assert kwargs['seq_len_override'] == 20
        prefix = matrix.Path(kwargs['research_out_prefix'])
        frame = pd.DataFrame(
            {
                'time': ['2025.01.01 00:00'],
                'signal': [1],
                'pred_trail_48_pnl_atr_x2': [1.0],
                'true_trail_48_pnl_atr_x2': [1.0],
                'pred_trail_48_pnl_atr_x3': [1.0],
                'true_trail_48_pnl_atr_x3': [1.0],
                'pred_trail_48_pnl_atr_x4': [1.0],
                'true_trail_48_pnl_atr_x4': [1.0],
                'pred_trail_48_pnl_atr_x6': [1.0],
                'true_trail_48_pnl_atr_x6': [1.0],
                'pred_trail_48_pnl_atr_x8': [1.0],
                'true_trail_48_pnl_atr_x8': [1.0],
            }
        )
        frame.to_csv(prefix.parent / f'{prefix.name}_validation_predictions.csv', sep=';', index=False)
        frame.to_csv(prefix.parent / f'{prefix.name}_test_predictions.csv', sep=';', index=False)

    monkeypatch.setattr(matrix, 'train_model', fake_train_model)
    monkeypatch.setattr(matrix, 'run_evaluation', fake_run_evaluation)
    monkeypatch.setattr(matrix, 'generate_signals', fake_generate_signals)

    run_single_config(
        seq_len=20,
        output_dir=tmp_path / 'matrix',
        epochs=1,
        patience=1,
        batch_size=8,
        seed=42,
        min_pf=1.0,
        skip_existing=True,
    )

    assert calls['train'] == 1
