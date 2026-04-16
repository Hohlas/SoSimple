import numpy as np
import pandas as pd
import torch
import torch.nn as nn

from API.generate_signals import DEFAULT_OPTUNA_JSON, resolve_optuna_json
from ML import data_loader
from ML import evaluate_test
from ML import train
from ML.trailing_stop_target_task import (
    TRAILING_STOP_TARGET,
    TRAILING_STOP_TARGET_COLUMNS,
    build_trailing_stop_export_frame,
)


def test_trailing_stop_task_constants_match_design():
    assert TRAILING_STOP_TARGET == 'trailing_stop_target_v1'
    assert TRAILING_STOP_TARGET_COLUMNS == [
        'trail_48_pnl_atr_x2',
        'trail_48_pnl_atr_x3',
        'trail_48_pnl_atr_x5',
    ]


def test_build_trailing_stop_export_frame_adds_pred_columns():
    frame = build_trailing_stop_export_frame(
        times=np.array(['2025.01.01 00:00']),
        signals=np.array([1]),
        pred=np.array([[0.1, 0.2, 0.3]], dtype=np.float32),
        true=np.array([[0.4, 0.5, 0.6]], dtype=np.float32),
    )
    assert list(frame.columns) == [
        'time',
        'signal',
        'pred_trail_48_pnl_atr_x2',
        'pred_trail_48_pnl_atr_x3',
        'pred_trail_48_pnl_atr_x5',
        'true_trail_48_pnl_atr_x2',
        'true_trail_48_pnl_atr_x3',
        'true_trail_48_pnl_atr_x5',
    ]


def test_trailing_stop_task_wiring_helpers():
    assert data_loader.task_checkpoint_suffix(TRAILING_STOP_TARGET) == '_trailing_stop_target_v1'
    assert data_loader.task_target_column(TRAILING_STOP_TARGET) == TRAILING_STOP_TARGET


def test_resolve_optuna_json_ignores_default_bundle_for_trailing_stop(tmp_path):
    assert resolve_optuna_json(TRAILING_STOP_TARGET, DEFAULT_OPTUNA_JSON) is None

    custom_optuna = tmp_path / 'optuna_best_params_trailing_stop_target_v1.json'
    custom_optuna.write_text('{"best_params": {"dropout": 0.1}}', encoding='utf-8')
    assert resolve_optuna_json(TRAILING_STOP_TARGET, str(custom_optuna)) == str(custom_optuna)


def test_create_test_loader_trailing_stop_branch(monkeypatch, tmp_path):
    df = pd.DataFrame(
        {
            'time': ['2025.01.01 00:00', '2025.01.01 01:00'],
            'signal': [1, -1],
            'trail_48_pnl_atr_x2': [0.1, 0.4],
            'trail_48_pnl_atr_x3': [0.2, 0.5],
            'trail_48_pnl_atr_x5': [0.3, 0.6],
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
        target=TRAILING_STOP_TARGET,
        seq_len=20,
        clear_cache=True,
        num_workers=0,
    )

    X_batch, y_batch, mask_batch = next(iter(loader))
    assert X_batch.shape == (2, 20, data_loader.N_FRACTAL_FEATURES)
    assert mask_batch.shape == (2, 20)
    assert y_batch.shape == (2, 3)
    np.testing.assert_allclose(
        y_batch.numpy(),
        np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]], dtype=np.float32),
    )


def test_train_model_routes_trailing_stop_to_regression_path(monkeypatch, tmp_path):
    calls = {}

    class FakeModel(nn.Module):
        def __init__(self, input_features: int, num_classes: int):
            super().__init__()
            self.linear = nn.Linear(input_features, num_classes)

    def fake_get_model(name, **kwargs):
        calls['get_model_kwargs'] = kwargs.copy()
        calls['get_model_name'] = name
        assert kwargs['num_classes'] == 3
        return FakeModel(kwargs['input_features'], kwargs['num_classes'])

    def fake_create_data_loaders(*args, **kwargs):
        calls['create_data_target'] = kwargs['target']
        return ['train-batch'], ['val-batch'], None

    monkeypatch.setattr(train, 'CHECKPOINTS_DIR', tmp_path / 'checkpoints')
    monkeypatch.setattr(train, 'PLOTS_DIR', tmp_path / 'plots')
    monkeypatch.setattr(train, 'REPORTS_DIR', tmp_path / 'reports')
    monkeypatch.setattr(train, 'get_device', lambda: torch.device('cpu'))
    monkeypatch.setattr(train, 'get_model', fake_get_model)
    monkeypatch.setattr(train, 'create_data_loaders', fake_create_data_loaders)
    monkeypatch.setattr(train, 'train_one_epoch', lambda *args, **kwargs: 0.123)
    monkeypatch.setattr(
        train,
        'validate_regression',
        lambda *args, **kwargs: (
            0.456,
            {'pearson_r': 0.9, 'mae': 0.1, 'rmse': 0.2, 'r2': 0.3},
        ),
    )
    monkeypatch.setattr(train, '_log_experiment', lambda **kwargs: None)

    result = train.train_model(
        model_name='transformer',
        task=TRAILING_STOP_TARGET,
        epochs=1,
        batch_size=2,
        use_scaler=False,
        use_weighted_sampler=False,
        seq_len=20,
        silent=True,
        clear_cache=True,
    )

    assert calls['create_data_target'] == TRAILING_STOP_TARGET
    assert calls['get_model_name'] == 'transformer'
    assert calls['get_model_kwargs']['num_classes'] == 3
    assert result['task'] == TRAILING_STOP_TARGET
    assert result['best_metric'] == 0.9


def test_run_evaluation_uses_trailing_stop_export_branch(monkeypatch, tmp_path):
    calls = {}
    report_dir = tmp_path / 'reports'
    checkpoint_dir = tmp_path / 'checkpoints'
    checkpoint_dir.mkdir()
    report_dir.mkdir()

    class FakeModel(nn.Module):
        def __init__(self):
            super().__init__()
            self.bias = nn.Parameter(torch.zeros(1))

        def forward(self, x, mask=None):
            batch = x.shape[0]
            base = torch.arange(batch, dtype=torch.float32, device=x.device).unsqueeze(1)
            return base.repeat(1, 3) + self.bias

    fake_model = FakeModel()
    checkpoint_path = checkpoint_dir / 'transformer_trailing_stop_target_v1_best.pt'
    checkpoint_path.write_bytes(b'checkpoint')

    def fake_get_model(name, **kwargs):
        calls['get_model_kwargs'] = kwargs.copy()
        return fake_model

    def fake_create_test_loader(*args, **kwargs):
        calls['create_test_loader_target'] = kwargs['target']
        X = torch.zeros((2, 20, 20), dtype=torch.float32)
        y = torch.zeros((2, 3), dtype=torch.float32)
        mask = torch.ones((2, 20), dtype=torch.bool)
        return torch.utils.data.DataLoader(torch.utils.data.TensorDataset(X, y, mask), batch_size=2)

    df = pd.DataFrame(
        {
            'time': ['2025.01.01 00:00', '2025.01.01 01:00'],
            'signal': [1, -1],
            'trail_48_pnl_atr_x2': [0.1, 0.4],
            'trail_48_pnl_atr_x3': [0.2, 0.5],
            'trail_48_pnl_atr_x5': [0.3, 0.6],
        }
    )

    def fake_build_export_frame(**kwargs):
        calls['export_kwargs'] = kwargs
        return build_trailing_stop_export_frame(**kwargs)

    monkeypatch.setattr(evaluate_test, 'CHECKPOINTS_DIR', checkpoint_dir)
    monkeypatch.setattr(evaluate_test, 'REPORTS_DIR', report_dir)
    monkeypatch.setattr(evaluate_test, 'get_model', fake_get_model)
    monkeypatch.setattr(evaluate_test, 'create_test_loader', fake_create_test_loader)
    monkeypatch.setattr(evaluate_test.pd, 'read_csv', lambda *args, **kwargs: df)
    monkeypatch.setattr(evaluate_test.torch, 'load', lambda *args, **kwargs: {
        'model_state_dict': fake_model.state_dict(),
        'epoch': 1,
        'metric_name': 'pearson_r',
        'best_metric': 0.9,
        'model_name': 'transformer',
    })
    monkeypatch.setattr(evaluate_test, 'build_trailing_stop_export_frame', fake_build_export_frame)

    evaluate_test.run_evaluation(
        model_name='transformer',
        task=TRAILING_STOP_TARGET,
        checkpoint_path=None,
    )

    assert calls['create_test_loader_target'] == TRAILING_STOP_TARGET
    assert calls['export_kwargs']['pred'].shape == (2, 3)
    assert calls['export_kwargs']['true'].shape == (2, 3)
    assert (report_dir / 'evaluate_test_trailing_stop_target_v1.md').exists()
    assert (report_dir / 'trailing_stop_target_test_predictions.csv').exists()
