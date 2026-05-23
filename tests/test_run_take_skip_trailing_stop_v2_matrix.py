import json

import pandas as pd
import pytest

from ML.run_take_skip_trailing_stop_v2_matrix import config_slug, run_single_config


def test_config_slug():
    assert config_slug(20) == 'transformer_seq20'


def test_single_config_writes_summary_and_benchmark(monkeypatch, tmp_path):
    import ML.run_take_skip_trailing_stop_v2_matrix as runner

    checkpoint_dir = tmp_path / 'checkpoints'
    reports_dir = tmp_path / 'reports'
    checkpoint_dir.mkdir()
    reports_dir.mkdir()
    monkeypatch.setattr(runner, 'CHECKPOINTS_DIR', checkpoint_dir)
    monkeypatch.setattr(runner, 'REPORTS_DIR', reports_dir)

    def fake_train_model(**kwargs):
        assert kwargs['task'] == 'take_skip_trailing_stop_v2'
        assert kwargs['seq_len'] == 20
        assert kwargs['clear_cache'] is True
        (checkpoint_dir / 'transformer_take_skip_trailing_stop_v2_best.pt').write_bytes(b'checkpoint')
        return {'best_metric': -0.1, 'task': kwargs['task']}

    def fake_run_evaluation(**kwargs):
        assert kwargs['task'] == 'take_skip_trailing_stop_v2'
        assert kwargs['seq_len_override'] == 20
        (reports_dir / 'evaluate_test_take_skip_trailing_stop_v2.md').write_text('ok', encoding='utf-8')

    def fake_generate_signals(**kwargs):
        prefix = runner.Path(kwargs['research_out_prefix'])
        frame = pd.DataFrame(
            {
                'time': ['2025.01.01 00:00', '2025.01.02 00:00'],
                'signal': [1, 1],
                'pred_take_12_x2': [0.9, 0.1],
                'pred_take_12_x4': [0.9, 0.1],
                'pred_take_12_x8': [0.9, 0.1],
                'pred_take_24_x2': [0.9, 0.1],
                'pred_take_24_x4': [0.9, 0.1],
                'pred_take_24_x8': [0.9, 0.1],
                'pred_take_48_x2': [0.9, 0.1],
                'pred_take_48_x4': [0.9, 0.1],
                'pred_take_48_x8': [0.9, 0.1],
                'true_take_12_x2': [1, 0],
                'true_take_12_x4': [1, 0],
                'true_take_12_x8': [1, 0],
                'true_take_24_x2': [1, 0],
                'true_take_24_x4': [1, 0],
                'true_take_24_x8': [1, 0],
                'true_take_48_x2': [1, 0],
                'true_take_48_x4': [1, 0],
                'true_take_48_x8': [1, 0],
                'true_trail_12_pnl_atr_x2': [1.0, -1.0],
                'true_trail_12_pnl_atr_x4': [1.0, -1.0],
                'true_trail_12_pnl_atr_x8': [1.0, -1.0],
                'true_trail_24_pnl_atr_x2': [1.0, -1.0],
                'true_trail_24_pnl_atr_x4': [1.0, -1.0],
                'true_trail_24_pnl_atr_x8': [1.0, -1.0],
                'true_trail_48_pnl_atr_x2': [1.0, -1.0],
                'true_trail_48_pnl_atr_x4': [1.0, -1.0],
                'true_trail_48_pnl_atr_x8': [1.0, -1.0],
            }
        )
        frame.to_csv(prefix.parent / f'{prefix.name}_validation_predictions.csv', sep=';', index=False)
        frame.to_csv(prefix.parent / f'{prefix.name}_test_predictions.csv', sep=';', index=False)

    monkeypatch.setattr(runner, 'train_model', fake_train_model)
    monkeypatch.setattr(runner, 'run_evaluation', fake_run_evaluation)
    monkeypatch.setattr(runner, 'generate_signals', fake_generate_signals)

    result = run_single_config(
        seq_len=20,
        output_dir=tmp_path / 'matrix',
        epochs=1,
        patience=1,
        batch_size=8,
        seed=42,
        min_pf=0.5,
        min_trades_per_year=0.1,
    )

    summary = tmp_path / 'matrix' / 'transformer_seq20' / 'summary.json'
    assert summary.exists()
    saved = json.loads(summary.read_text(encoding='utf-8'))
    assert saved['config']['seq_len'] == 20
    assert result['benchmark']['final_verdict']['verdict'] == 'go'


def test_single_config_fails_when_checkpoint_missing(monkeypatch, tmp_path):
    import ML.run_take_skip_trailing_stop_v2_matrix as runner

    checkpoint_dir = tmp_path / 'checkpoints'
    reports_dir = tmp_path / 'reports'
    checkpoint_dir.mkdir()
    reports_dir.mkdir()
    monkeypatch.setattr(runner, 'CHECKPOINTS_DIR', checkpoint_dir)
    monkeypatch.setattr(runner, 'REPORTS_DIR', reports_dir)
    monkeypatch.setattr(runner, 'train_model', lambda **kwargs: {'best_metric': -0.1})

    with pytest.raises(FileNotFoundError, match='required checkpoint'):
        run_single_config(
            seq_len=20,
            output_dir=tmp_path / 'matrix',
            epochs=1,
            patience=1,
            batch_size=8,
            seed=42,
            min_pf=1.0,
            min_trades_per_year=0.1,
        )
