import json

import pandas as pd

from ML.run_trailing_stop_target_quantile import run_single_config


def test_single_run_writes_summary_and_benchmark(monkeypatch, tmp_path):
    import ML.run_trailing_stop_target_quantile as runner

    checkpoint_dir = tmp_path / 'checkpoints'
    reports_dir = tmp_path / 'reports'
    checkpoint_dir.mkdir()
    reports_dir.mkdir()
    monkeypatch.setattr(runner, 'CHECKPOINTS_DIR', checkpoint_dir)
    monkeypatch.setattr(runner, 'REPORTS_DIR', reports_dir)

    def fake_train_model(**kwargs):
        (checkpoint_dir / 'transformer_trailing_stop_target_quantile_v1_best.pt').write_bytes(b'checkpoint')
        return {'best_metric': 0.2, 'task': kwargs['task']}

    def fake_run_evaluation(**kwargs):
        assert kwargs['seq_len_override'] == 20
        (reports_dir / 'evaluate_test_trailing_stop_target_quantile_v1.md').write_text('ok', encoding='utf-8')
        (reports_dir / 'trailing_stop_target_quantile_test_predictions.csv').write_text('time;signal\n', encoding='utf-8')

    def fake_generate_signals(**kwargs):
        assert kwargs['seq_len_override'] == 20
        prefix = runner.Path(kwargs['research_out_prefix'])
        validation = pd.DataFrame(
            {
                'time': ['2026.01.01 00:00', '2026.01.02 00:00', '2026.01.03 00:00'],
                'signal': [1, 1, -1],
                'pred_trail_48_pnl_atr_x3_q10': [0.2, 0.4, -0.3],
                'pred_trail_48_pnl_atr_x3_q50': [0.6, 0.8, 0.1],
                'pred_trail_48_pnl_atr_x3_q90': [1.0, 1.2, 0.8],
                'true_trail_48_pnl_atr_x3': [0.7, -0.2, -0.4],
            }
        )
        test = pd.DataFrame(
            {
                'time': ['2026.02.01 00:00', '2026.02.02 00:00'],
                'signal': [1, -1],
                'pred_trail_48_pnl_atr_x3_q10': [0.3, -0.2],
                'pred_trail_48_pnl_atr_x3_q50': [0.7, 0.0],
                'pred_trail_48_pnl_atr_x3_q90': [1.1, 0.6],
                'true_trail_48_pnl_atr_x3': [0.6, -0.3],
            }
        )
        validation.to_csv(prefix.parent / f'{prefix.name}_validation_predictions.csv', sep=';', index=False)
        test.to_csv(prefix.parent / f'{prefix.name}_test_predictions.csv', sep=';', index=False)

    monkeypatch.setattr(runner, 'train_model', fake_train_model)
    monkeypatch.setattr(runner, 'run_evaluation', fake_run_evaluation)
    monkeypatch.setattr(runner, 'generate_signals', fake_generate_signals)

    result = run_single_config(
        output_dir=tmp_path / 'quantile',
        epochs=1,
        patience=1,
        batch_size=8,
        seed=42,
        min_pf=1.0,
        skip_existing=False,
    )

    summary_path = tmp_path / 'quantile' / 'transformer_seq20_x3_quantile' / 'summary.json'
    saved = json.loads(summary_path.read_text(encoding='utf-8'))
    assert saved['config']['seq_len'] == 20
    assert saved['config']['target_column'] == 'trail_48_pnl_atr_x3'
    assert saved['benchmark']['final_verdict']['verdict'] == 'go'
    assert result['benchmark']['final_verdict']['validation_winner']['candidate'] == 'q10_gt_zero'
