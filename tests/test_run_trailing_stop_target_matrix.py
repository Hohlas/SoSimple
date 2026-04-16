import json

import numpy as np
import pandas as pd

from ML.run_trailing_stop_target_matrix import (
    DEFAULT_MATRIX_CONFIGS,
    _jsonable,
    config_slug,
    run_single_config,
)


def test_default_matrix_covers_three_x_values_and_three_sequence_lengths():
    slugs = {config_slug(row['target_column'], row['seq_len']) for row in DEFAULT_MATRIX_CONFIGS}
    assert slugs == {
        'trail_48_pnl_atr_x2_seq20',
        'trail_48_pnl_atr_x2_seq50',
        'trail_48_pnl_atr_x2_seq100',
        'trail_48_pnl_atr_x3_seq20',
        'trail_48_pnl_atr_x3_seq50',
        'trail_48_pnl_atr_x3_seq100',
        'trail_48_pnl_atr_x5_seq20',
        'trail_48_pnl_atr_x5_seq50',
        'trail_48_pnl_atr_x5_seq100',
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
        (reports_dir / 'evaluate_test_trailing_stop_target_v1.md').write_text('ok', encoding='utf-8')
        (reports_dir / 'trailing_stop_target_test_predictions.csv').write_text('time;signal\n', encoding='utf-8')

    def fake_generate_signals(**kwargs):
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
                'pred_trail_48_pnl_atr_x5': [1.0, 0.7, 0.2],
                'true_trail_48_pnl_atr_x5': [1.0, -0.5, -0.2],
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
                'pred_trail_48_pnl_atr_x5': [0.8, 0.1],
                'true_trail_48_pnl_atr_x5': [0.8, -0.2],
            }
        )
        validation.to_csv(prefix.parent / f'{prefix.name}_validation_predictions.csv', sep=';', index=False)
        test.to_csv(prefix.parent / f'{prefix.name}_test_predictions.csv', sep=';', index=False)

    monkeypatch.setattr(matrix, 'train_model', fake_train_model)
    monkeypatch.setattr(matrix, 'run_evaluation', fake_run_evaluation)
    monkeypatch.setattr(matrix, 'generate_signals', fake_generate_signals)

    result = run_single_config(
        target_column='trail_48_pnl_atr_x2',
        seq_len=20,
        output_dir=tmp_path / 'matrix',
        epochs=1,
        patience=1,
        batch_size=8,
        seed=42,
        min_pf=1.0,
        skip_existing=False,
    )

    summary_path = tmp_path / 'matrix' / 'trail_48_pnl_atr_x2_seq20' / 'summary.json'
    assert summary_path.exists()
    saved = json.loads(summary_path.read_text(encoding='utf-8'))
    assert saved['config']['target_column'] == 'trail_48_pnl_atr_x2'
    assert saved['config']['seq_len'] == 20
    assert saved['benchmark']['final_verdict']['verdict'] == 'go'
    assert result['benchmark']['final_verdict']['validation_winner']['candidate'] == 'pred_trail_48_pnl_atr_x2'
