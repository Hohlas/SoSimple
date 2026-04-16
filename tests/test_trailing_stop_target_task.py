import numpy as np
import pandas as pd

from API.generate_signals import DEFAULT_OPTUNA_JSON, resolve_optuna_json
from ML import data_loader
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
