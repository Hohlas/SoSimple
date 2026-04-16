from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import torch
import torch.nn as nn

import API.generate_signals as signal_api
from ML import data_loader
from ML import evaluate_test
from ML import train

from ML.trailing_stop_target_quantile_task import (
    TRAILING_STOP_TARGET_QUANTILE_BASE_COLUMN,
    TRAILING_STOP_TARGET_QUANTILE_Q10_COLUMN,
    TRAILING_STOP_TARGET_QUANTILE_Q50_COLUMN,
    TRAILING_STOP_TARGET_QUANTILE_Q90_COLUMN,
    TRAILING_STOP_TARGET_QUANTILE_TARGET,
    build_trailing_stop_quantile_export_frame,
    compute_trailing_stop_quantile_metrics,
)


def test_quantile_task_constants_match_design():
    assert TRAILING_STOP_TARGET_QUANTILE_TARGET == 'trailing_stop_target_quantile_v1'
    assert TRAILING_STOP_TARGET_QUANTILE_Q10_COLUMN == 'pred_trail_48_pnl_atr_x3_q10'
    assert TRAILING_STOP_TARGET_QUANTILE_Q50_COLUMN == 'pred_trail_48_pnl_atr_x3_q50'
    assert TRAILING_STOP_TARGET_QUANTILE_Q90_COLUMN == 'pred_trail_48_pnl_atr_x3_q90'


def test_build_export_frame_orders_crossed_quantiles():
    frame = build_trailing_stop_quantile_export_frame(
        times=np.array(['2026.01.01 00:00']),
        signals=np.array([1]),
        pred_q10=np.array([[0.8]], dtype=np.float32),
        pred_q50=np.array([[0.4]], dtype=np.float32),
        pred_q90=np.array([[0.1]], dtype=np.float32),
        true=np.array([[0.3]], dtype=np.float32),
    )

    assert frame.loc[0, 'pred_trail_48_pnl_atr_x3_q10_raw'] == 0.8
    assert frame.loc[0, 'pred_trail_48_pnl_atr_x3_q50_raw'] == 0.4
    assert frame.loc[0, 'pred_trail_48_pnl_atr_x3_q90_raw'] == 0.1
    assert frame.loc[0, 'pred_trail_48_pnl_atr_x3_q10'] == 0.1
    assert frame.loc[0, 'pred_trail_48_pnl_atr_x3_q50'] == 0.4
    assert frame.loc[0, 'pred_trail_48_pnl_atr_x3_q90'] == 0.8
    assert frame.loc[0, 'true_trail_48_pnl_atr_x3'] == 0.3


def test_compute_quantile_metrics_still_rejects_crossed_bounds_at_raw_contract_level():
    with pytest.raises(ValueError, match='must satisfy q10 <= q50 <= q90'):
        compute_trailing_stop_quantile_metrics(
            true_target=np.array([0.0, 1.0], dtype=np.float32),
            pred_q10=np.array([0.5, 0.8], dtype=np.float32),
            pred_q50=np.array([0.4, 0.7], dtype=np.float32),
            pred_q90=np.array([0.3, 0.6], dtype=np.float32),
        )


def test_build_export_frame_rejects_mismatched_row_counts():
    with pytest.raises(ValueError, match='signals must have the same length as times'):
        build_trailing_stop_quantile_export_frame(
            times=np.array(['2026.01.01 00:00']),
            signals=np.array([1, -1]),
            pred_q10=np.array([[0.1]], dtype=np.float32),
            pred_q50=np.array([[0.2]], dtype=np.float32),
            pred_q90=np.array([[0.3]], dtype=np.float32),
        )

    with pytest.raises(ValueError, match='pred_q10 must have shape'):
        build_trailing_stop_quantile_export_frame(
            times=np.array(['2026.01.01 00:00']),
            signals=np.array([1]),
            pred_q10=np.array([[0.1, 0.2]], dtype=np.float32),
            pred_q50=np.array([[0.2]], dtype=np.float32),
            pred_q90=np.array([[0.3]], dtype=np.float32),
        )

    with pytest.raises(ValueError, match='true must have the same row count as times'):
        build_trailing_stop_quantile_export_frame(
            times=np.array(['2026.01.01 00:00']),
            signals=np.array([1]),
            pred_q10=np.array([[0.1]], dtype=np.float32),
            pred_q50=np.array([[0.2]], dtype=np.float32),
            pred_q90=np.array([[0.3]], dtype=np.float32),
            true=np.array([[0.4], [0.5]], dtype=np.float32),
        )


def test_trailing_stop_quantile_task_wiring_helpers():
    assert data_loader.task_checkpoint_suffix(TRAILING_STOP_TARGET_QUANTILE_TARGET) == '_trailing_stop_target_quantile_v1'
    assert data_loader.task_target_column(TRAILING_STOP_TARGET_QUANTILE_TARGET) == TRAILING_STOP_TARGET_QUANTILE_TARGET


def test_create_test_loader_trailing_stop_quantile_branch(monkeypatch, tmp_path):
    df = pd.DataFrame(
        {
            'time': ['2025.01.01 00:00', '2025.01.01 01:00'],
            'signal': [1, -1],
            TRAILING_STOP_TARGET_QUANTILE_BASE_COLUMN: [0.2, 0.5],
        }
    )

    monkeypatch.setattr(data_loader, 'DATA_DIR', tmp_path)
    monkeypatch.setattr(data_loader, 'TEST_FILE', tmp_path / 'Nero_test_labeled.csv')
    monkeypatch.setattr(data_loader.pd, 'read_csv', lambda *args, **kwargs: df)
    monkeypatch.setattr(data_loader, 'validate_csv_columns', lambda *args, **kwargs: None)
    monkeypatch.setattr(data_loader, 'validate_fractal_format', lambda *args, **kwargs: None)
    monkeypatch.setattr(
        data_loader,
        'parse_fractals_to_3d',
        lambda frame: (
            np.ones((len(frame), data_loader.N_FRACTALS, data_loader.N_FRACTAL_FEATURES), dtype=np.float32),
            np.ones((len(frame), data_loader.N_FRACTALS), dtype=bool),
        ),
    )

    loader = data_loader.create_test_loader(
        batch_size=2,
        target=TRAILING_STOP_TARGET_QUANTILE_TARGET,
        seq_len=20,
        clear_cache=True,
        num_workers=0,
    )

    X_batch, y_batch, mask_batch = next(iter(loader))
    assert X_batch.shape == (2, 20, data_loader.N_FRACTAL_FEATURES)
    assert mask_batch.shape == (2, 20)
    assert y_batch.shape == (2, 1)
    np.testing.assert_allclose(y_batch.numpy(), np.array([[0.2], [0.5]], dtype=np.float32))


def test_train_model_routes_trailing_stop_quantile_to_quantile_path(monkeypatch, tmp_path):
    calls = {}

    class FakeQuantileModel(nn.Module):
        def __init__(self, **kwargs):
            super().__init__()
            self.bias = nn.Parameter(torch.zeros(1))

        def forward(self, x, mask=None):
            batch = x.shape[0]
            base = self.bias.expand(batch, 1)
            return {
                'q10': base,
                'q50': base,
                'q90': base,
            }

    def fake_create_data_loaders(*args, **kwargs):
        calls['create_data_target'] = kwargs['target']
        calls['use_weighted_sampler'] = kwargs['use_weighted_sampler']
        return ['train-batch'], ['val-batch'], None

    monkeypatch.setattr(train, 'CHECKPOINTS_DIR', tmp_path / 'checkpoints')
    monkeypatch.setattr(train, 'PLOTS_DIR', tmp_path / 'plots')
    monkeypatch.setattr(train, 'REPORTS_DIR', tmp_path / 'reports')
    monkeypatch.setattr(train, 'set_seed', lambda seed: None)
    monkeypatch.setattr(train, 'get_device', lambda: torch.device('cpu'))
    monkeypatch.setattr(train, 'create_data_loaders', fake_create_data_loaders)
    monkeypatch.setattr(train, 'TrailingStopTargetQuantileTransformer', FakeQuantileModel)
    monkeypatch.setattr(train, 'train_one_epoch_trailing_stop_target_quantile', lambda *args, **kwargs: 0.123)
    monkeypatch.setattr(
        train,
        'validate_trailing_stop_target_quantile',
        lambda *args, **kwargs: (
            0.456,
            {
                'q10_pinball_loss': 0.1,
                'q50_pinball_loss': 0.2,
                'q90_pinball_loss': 0.3,
                'q50_mae': 0.4,
                'q50_pearson_r': 0.75,
                'interval_coverage': 0.8,
                'median_interval_width': 0.9,
                'val_score': 0.7,
            },
        ),
    )
    monkeypatch.setattr(train, '_log_experiment', lambda **kwargs: None)

    result = train.train_model(
        model_name='transformer',
        task=TRAILING_STOP_TARGET_QUANTILE_TARGET,
        epochs=1,
        batch_size=2,
        use_scaler=False,
        use_weighted_sampler=True,
        seq_len=20,
        silent=True,
        clear_cache=True,
    )

    assert calls['create_data_target'] == TRAILING_STOP_TARGET_QUANTILE_TARGET
    assert calls['use_weighted_sampler'] is False
    assert result['task'] == TRAILING_STOP_TARGET_QUANTILE_TARGET
    assert result['metric_name'] == 'val_score'
    assert result['best_metric'] == pytest.approx(0.7)
    saved_ckpt = torch.load(
        tmp_path / 'checkpoints' / 'transformer_trailing_stop_target_quantile_v1_best.pt',
        weights_only=False,
    )
    assert saved_ckpt['seq_len'] == 20


def test_run_evaluation_uses_trailing_stop_quantile_export_branch(monkeypatch, tmp_path):
    calls = {}
    report_dir = tmp_path / 'reports'
    checkpoint_dir = tmp_path / 'checkpoints'
    checkpoint_dir.mkdir()
    report_dir.mkdir()

    class FakeQuantileModel(nn.Module):
        def __init__(self):
            super().__init__()
            self.bias = nn.Parameter(torch.zeros(1))

        def forward(self, x, mask=None):
            batch = x.shape[0]
            base = torch.arange(batch, dtype=torch.float32, device=x.device).unsqueeze(1)
            return {
                'q10': base + 0.3 + self.bias,
                'q50': base + 0.2 + self.bias,
                'q90': base + 0.1 + self.bias,
            }

    fake_model = FakeQuantileModel()
    checkpoint_path = checkpoint_dir / 'transformer_trailing_stop_target_quantile_v1_best.pt'
    checkpoint_path.write_bytes(b'checkpoint')

    def fake_create_test_loader(*args, **kwargs):
        calls['create_test_loader_target'] = kwargs['target']
        calls['create_test_loader_seq_len'] = kwargs['seq_len']
        X = torch.zeros((2, 20, 20), dtype=torch.float32)
        y = torch.zeros((2, 1), dtype=torch.float32)
        mask = torch.ones((2, 20), dtype=torch.bool)
        return torch.utils.data.DataLoader(torch.utils.data.TensorDataset(X, y, mask), batch_size=2)

    df = pd.DataFrame(
        {
            'time': ['2025.01.01 00:00', '2025.01.01 01:00'],
            'signal': [1, -1],
            TRAILING_STOP_TARGET_QUANTILE_BASE_COLUMN: [0.2, 0.5],
        }
    )

    def fake_build_export_frame(**kwargs):
        calls['export_kwargs'] = kwargs
        return build_trailing_stop_quantile_export_frame(**kwargs)

    monkeypatch.setattr(evaluate_test, 'CHECKPOINTS_DIR', checkpoint_dir)
    monkeypatch.setattr(evaluate_test, 'REPORTS_DIR', report_dir)
    monkeypatch.setattr(evaluate_test, 'create_test_loader', fake_create_test_loader)
    monkeypatch.setattr(evaluate_test, 'build_trailing_stop_quantile_export_frame', fake_build_export_frame)
    monkeypatch.setattr(evaluate_test.pd, 'read_csv', lambda *args, **kwargs: df)
    monkeypatch.setattr(evaluate_test.torch, 'load', lambda *args, **kwargs: {
        'model_state_dict': fake_model.state_dict(),
        'epoch': 1,
        'metric_name': 'val_score',
        'best_metric': 0.7,
        'model_name': 'transformer',
        'seq_len': 50,
        'task': TRAILING_STOP_TARGET_QUANTILE_TARGET,
    })
    monkeypatch.setattr(
        evaluate_test,
        'build_trailing_stop_target_quantile_model',
        lambda *_args, **_kwargs: fake_model,
    )

    evaluate_test.run_evaluation(
        model_name='transformer',
        task=TRAILING_STOP_TARGET_QUANTILE_TARGET,
        checkpoint_path=None,
    )

    assert calls['create_test_loader_target'] == TRAILING_STOP_TARGET_QUANTILE_TARGET
    assert calls['create_test_loader_seq_len'] == 50
    assert calls['export_kwargs']['pred_q10'].shape == (2, 1)
    assert calls['export_kwargs']['pred_q50'].shape == (2, 1)
    assert calls['export_kwargs']['pred_q90'].shape == (2, 1)
    assert calls['export_kwargs']['true'].shape == (2, 1)
    assert (report_dir / 'evaluate_test_trailing_stop_target_quantile_v1.md').exists()
    assert (report_dir / 'trailing_stop_target_quantile_test_predictions.csv').exists()

    calls.clear()
    evaluate_test.run_evaluation(
        model_name='transformer',
        task=TRAILING_STOP_TARGET_QUANTILE_TARGET,
        checkpoint_path=None,
        seq_len_override=20,
    )

    assert calls['create_test_loader_seq_len'] == 20


def test_validate_trailing_stop_target_quantile_orders_crossed_heads_before_metrics(monkeypatch):
    captured = {}

    def spy_metrics(**kwargs):
        captured.update(kwargs)
        return {
            'q10_pinball_loss': 0.1,
            'q50_pinball_loss': 0.2,
            'q90_pinball_loss': 0.3,
            'q50_mae': 0.4,
            'q50_pearson_r': 0.5,
            'interval_coverage': 0.6,
            'median_interval_width': 0.7,
        }

    class FakeQuantileModel(nn.Module):
        def forward(self, x, mask=None):
            return {
                'q10': torch.tensor([[0.8], [0.7]], dtype=torch.float32),
                'q50': torch.tensor([[0.4], [0.5]], dtype=torch.float32),
                'q90': torch.tensor([[0.1], [0.3]], dtype=torch.float32),
            }

    monkeypatch.setattr(train, 'compute_trailing_stop_quantile_metrics', spy_metrics)
    loader = torch.utils.data.DataLoader(
        torch.utils.data.TensorDataset(
            torch.zeros((2, 20, 20), dtype=torch.float32),
            torch.tensor([[0.2], [0.6]], dtype=torch.float32),
            torch.ones((2, 20), dtype=torch.bool),
        ),
        batch_size=2,
    )

    loss, metrics = train.validate_trailing_stop_target_quantile(
        model=FakeQuantileModel(),
        val_loader=loader,
        device=torch.device('cpu'),
    )

    assert loss >= 0.0
    assert metrics['val_score'] == pytest.approx(0.5)
    assert captured['pred_q10'].tolist() == pytest.approx([0.1, 0.3])
    assert captured['pred_q50'].tolist() == pytest.approx([0.4, 0.5])
    assert captured['pred_q90'].tolist() == pytest.approx([0.8, 0.7])


def test_generate_signals_uses_checkpoint_seq_len_for_trailing_stop_quantile(monkeypatch, tmp_path):
    calls = {}

    class FakeQuantileModel(nn.Module):
        def __init__(self):
            super().__init__()
            self.bias = nn.Parameter(torch.zeros(1))

        def forward(self, x, mask=None):
            batch = x.shape[0]
            base = torch.ones((batch, 1), dtype=torch.float32, device=x.device)
            return {
                'q10': base * 0.1 + self.bias,
                'q50': base * 0.2 + self.bias,
                'q90': base * 0.3 + self.bias,
            }

    fake_model = FakeQuantileModel()
    checkpoint_dir = tmp_path / 'checkpoints'
    reports_dir = tmp_path / 'reports'
    checkpoint_dir.mkdir()
    reports_dir.mkdir()
    (checkpoint_dir / 'transformer_trailing_stop_target_quantile_v1_best.pt').write_bytes(b'checkpoint')

    def fake_create_data_loaders(*args, **kwargs):
        calls.setdefault('data_loader_targets', []).append(kwargs['target'])
        calls.setdefault('data_loader_seq_lens', []).append(kwargs['seq_len'])
        loader = torch.utils.data.DataLoader(
            torch.utils.data.TensorDataset(
                torch.zeros((2, 20, 20), dtype=torch.float32),
                torch.zeros((2, 1), dtype=torch.float32),
                torch.ones((2, 20), dtype=torch.bool),
            ),
            batch_size=2,
        )
        return loader, loader, None

    def fake_create_test_loader(*args, **kwargs):
        calls['test_loader_target'] = kwargs['target']
        calls['test_loader_seq_len'] = kwargs['seq_len']
        return torch.utils.data.DataLoader(
            torch.utils.data.TensorDataset(
                torch.zeros((2, 20, 20), dtype=torch.float32),
                torch.zeros((2, 1), dtype=torch.float32),
                torch.ones((2, 20), dtype=torch.bool),
            ),
            batch_size=2,
        )

    csv_frames = {
        signal_api.VAL_FILE: pd.DataFrame(
            {
                'time': ['2025.01.01 00:00', '2025.01.01 01:00'],
                'signal': [1, -1],
                TRAILING_STOP_TARGET_QUANTILE_BASE_COLUMN: [0.2, 0.5],
            }
        ),
        signal_api.TEST_FILE: pd.DataFrame(
            {
                'time': ['2025.01.02 00:00', '2025.01.02 01:00'],
                'signal': [1, -1],
                TRAILING_STOP_TARGET_QUANTILE_BASE_COLUMN: [0.1, 0.4],
            }
        ),
    }

    def fake_read_csv(path, *args, **kwargs):
        return csv_frames[Path(path)]

    monkeypatch.setattr(signal_api, 'CHECKPOINTS_DIR', checkpoint_dir)
    monkeypatch.setattr(signal_api, 'REPORTS_DIR', reports_dir)
    monkeypatch.setattr(signal_api, 'resolve_optuna_json', lambda *args, **kwargs: None)
    monkeypatch.setattr(signal_api, 'set_seed', lambda seed: None)
    monkeypatch.setattr(signal_api, 'get_device', lambda: torch.device('cpu'))
    monkeypatch.setattr(signal_api, 'create_data_loaders', fake_create_data_loaders)
    monkeypatch.setattr(signal_api, 'create_test_loader', fake_create_test_loader)
    monkeypatch.setattr(signal_api.pd, 'read_csv', fake_read_csv)
    monkeypatch.setattr(signal_api.torch, 'load', lambda *args, **kwargs: {
        'model_state_dict': fake_model.state_dict(),
        'model_name': 'transformer',
        'num_classes': 1,
        'seq_len': 50,
        'task': TRAILING_STOP_TARGET_QUANTILE_TARGET,
    })
    monkeypatch.setattr(
        signal_api,
        'build_trailing_stop_target_quantile_model',
        lambda *_args, **_kwargs: fake_model,
    )

    signal_api.generate_signals(
        model_name='transformer',
        task=TRAILING_STOP_TARGET_QUANTILE_TARGET,
        research_out_prefix=str(reports_dir / 'tsq'),
    )

    assert calls['data_loader_targets'] == [TRAILING_STOP_TARGET_QUANTILE_TARGET]
    assert calls['data_loader_seq_lens'] == [50]
    assert calls['test_loader_target'] == TRAILING_STOP_TARGET_QUANTILE_TARGET
    assert calls['test_loader_seq_len'] == 50
    assert (reports_dir / 'tsq_validation_predictions.csv').exists()
    assert (reports_dir / 'tsq_test_predictions.csv').exists()

    validation_export_text = (reports_dir / 'tsq_validation_predictions.csv').read_text(encoding='utf-8')
    assert 'true_trail_48_pnl_atr_x3' in validation_export_text
