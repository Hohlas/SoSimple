import numpy as np
import pandas as pd
import pytest

import ML.evaluate_test as evaluate_test
import API.generate_signals as signal_api
from ML import data_loader
from ML import train
from ML.take_skip_trailing_stop_v2_task import (
    TAKE_SKIP_THRESHOLD_ATR_V2,
    TAKE_SKIP_TRAILING_STOP_V2_COLUMNS,
    TAKE_SKIP_TRAILING_STOP_V2_TARGET,
    TAKE_SKIP_TRUE_PNL_V2_COLUMNS,
    build_take_skip_v2_export_frame,
    compute_take_skip_v2_metrics,
    split_take_skip_v2_targets,
)


def test_take_skip_v2_columns_match_design():
    assert TAKE_SKIP_TRAILING_STOP_V2_TARGET == 'take_skip_trailing_stop_v2'
    assert TAKE_SKIP_THRESHOLD_ATR_V2 == 0.5
    assert TAKE_SKIP_TRAILING_STOP_V2_COLUMNS == [
        'take_12_x2', 'take_12_x4', 'take_12_x8',
        'take_24_x2', 'take_24_x4', 'take_24_x8',
        'take_48_x2', 'take_48_x4', 'take_48_x8',
    ]
    assert TAKE_SKIP_TRUE_PNL_V2_COLUMNS == [
        'trail_12_pnl_atr_x2', 'trail_12_pnl_atr_x4', 'trail_12_pnl_atr_x8',
        'trail_24_pnl_atr_x2', 'trail_24_pnl_atr_x4', 'trail_24_pnl_atr_x8',
        'trail_48_pnl_atr_x2', 'trail_48_pnl_atr_x4', 'trail_48_pnl_atr_x8',
    ]


def test_split_take_skip_v2_targets_thresholds_at_half_atr():
    frame = pd.DataFrame(
        {
            'trail_12_pnl_atr_x2': [0.49, 0.50],
            'trail_12_pnl_atr_x4': [0.50, 0.10],
            'trail_12_pnl_atr_x8': [0.0, 0.51],
            'trail_24_pnl_atr_x2': [1.0, -1.0],
            'trail_24_pnl_atr_x4': [0.40, 0.50],
            'trail_24_pnl_atr_x8': [0.80, 0.20],
            'trail_48_pnl_atr_x2': [0.49, 0.51],
            'trail_48_pnl_atr_x4': [0.50, 0.50],
            'trail_48_pnl_atr_x8': [-0.50, 3.00],
        }
    )

    y = split_take_skip_v2_targets(frame)

    assert y.dtype == np.float32
    assert y.tolist() == [
        [0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0],
        [1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 1.0, 1.0],
    ]


def test_split_take_skip_v2_targets_fails_on_missing_columns():
    frame = pd.DataFrame({'trail_12_pnl_atr_x2': [1.0]})

    with pytest.raises(ValueError, match='missing take/skip v2 source columns'):
        split_take_skip_v2_targets(frame)


def test_build_take_skip_v2_export_frame_includes_probabilities_and_true_pnl():
    pred_prob = np.full((2, 9), 0.25, dtype=np.float32)
    true_label = np.zeros((2, 9), dtype=np.float32)
    true_pnl = np.arange(18, dtype=np.float32).reshape(2, 9)

    frame = build_take_skip_v2_export_frame(
        times=['2026.01.01 00:00', '2026.01.02 00:00'],
        signals=[1, -1],
        pred_prob=pred_prob,
        true_label=true_label,
        true_pnl=true_pnl,
    )

    assert frame.shape[0] == 2
    assert 'pred_take_12_x2' in frame.columns
    assert 'true_take_48_x8' in frame.columns
    assert 'true_trail_24_pnl_atr_x4' in frame.columns


def test_compute_take_skip_v2_metrics_validates_inputs():
    y_true = np.zeros((2, 9), dtype=np.float32)
    y_prob = np.ones((2, 9), dtype=np.float32) * 0.5

    metrics = compute_take_skip_v2_metrics(y_true, y_prob)

    assert metrics['bce'] > 0.0
    assert 'positive_rate_take_12_x2' in metrics
    assert 'brier_take_48_x8' in metrics

    bad_prob = y_prob.copy()
    bad_prob[0, 0] = 1.5
    with pytest.raises(ValueError, match='probabilities in \\[0, 1\\]'):
        compute_take_skip_v2_metrics(y_true, bad_prob)


def test_data_loader_task_suffix_for_take_skip_v2():
    assert data_loader.task_target_column(TAKE_SKIP_TRAILING_STOP_V2_TARGET) == TAKE_SKIP_TRAILING_STOP_V2_TARGET
    assert data_loader.task_checkpoint_suffix(TAKE_SKIP_TRAILING_STOP_V2_TARGET) == '_take_skip_trailing_stop_v2'


def test_take_skip_v2_seq_len_is_respected():
    assert data_loader.validate_seq_len_for_target(TAKE_SKIP_TRAILING_STOP_V2_TARGET, 20) == 20
    assert data_loader.validate_seq_len_for_target(TAKE_SKIP_TRAILING_STOP_V2_TARGET, 50) == 50
    assert data_loader.validate_seq_len_for_target(TAKE_SKIP_TRAILING_STOP_V2_TARGET, 100) == 100


def _build_take_skip_v2_frame() -> pd.DataFrame:
    row = {
        'time': ['2025.01.01 00:00', '2025.01.01 01:00'],
        'signal': [1, -1],
        'predict': [0.1, 0.2],
        'ATR': [1.0, 2.0],
        'session_hour': [10, 11],
        'weekday': [2, 3],
        'range_atr_6': [0.5, 0.6],
        'body_atr_3': [0.1, 0.2],
        'ret_dir_atr_lag1': [0.0, 0.1],
        'vol_regime_24': [1.0, 1.1],
        'ret_6_dir_atr': [0.2, 0.3],
        'ret_12_dir_atr': [0.3, 0.4],
        'ret_24_dir_atr': [0.4, 0.5],
        'fav_3_atr': [0.1, 0.2],
        'adv_3_atr': [0.0, 0.1],
        'fav_6_atr': [0.2, 0.3],
        'adv_6_atr': [0.1, 0.2],
        'fav_12_atr': [0.3, 0.4],
        'adv_12_atr': [0.2, 0.3],
        'fav_24_atr': [0.4, 0.5],
        'adv_24_atr': [0.3, 0.4],
    }
    for column in TAKE_SKIP_TRUE_PNL_V2_COLUMNS:
        row[column] = [0.6, 0.1]
    return pd.DataFrame(row)


def test_create_data_loaders_take_skip_v2_uses_full_sequence_and_wide_targets(monkeypatch, tmp_path):
    df = _build_take_skip_v2_frame()

    monkeypatch.setattr(data_loader, 'DATA_DIR', tmp_path)
    monkeypatch.setattr(data_loader, 'TRAIN_FILE', tmp_path / 'Nero_train_labeled.csv')
    monkeypatch.setattr(data_loader, 'VAL_FILE', tmp_path / 'Nero_validation_labeled.csv')
    monkeypatch.setattr(data_loader, 'TEST_FILE', tmp_path / 'Nero_test_labeled.csv')
    monkeypatch.setattr(data_loader.pd, 'read_csv', lambda *args, **kwargs: df)
    monkeypatch.setattr(data_loader, 'validate_data_contract', lambda *args, **kwargs: None)
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

    train_loader, val_loader, _ = data_loader.create_data_loaders(
        batch_size=2,
        target=TAKE_SKIP_TRAILING_STOP_V2_TARGET,
        seq_len=20,
        clear_cache=True,
        num_workers=0,
    )

    X_train, y_train, mask_train = next(iter(train_loader))
    X_val, y_val, mask_val = next(iter(val_loader))

    assert X_train.shape == (2, 20, X_train.shape[2])
    assert X_val.shape == (2, 20, X_val.shape[2])
    assert X_train.shape[2] > data_loader.N_FRACTAL_FEATURES
    assert y_train.shape == (2, 9)
    assert y_val.shape == (2, 9)
    assert mask_train.shape == (2, 20)
    assert mask_val.shape == (2, 20)


def test_create_test_loader_take_skip_v2_branch(monkeypatch, tmp_path):
    df = _build_take_skip_v2_frame()

    monkeypatch.setattr(data_loader, 'DATA_DIR', tmp_path)
    monkeypatch.setattr(data_loader, 'TEST_FILE', tmp_path / 'Nero_test_labeled.csv')
    monkeypatch.setattr(data_loader.pd, 'read_csv', lambda *args, **kwargs: df)
    monkeypatch.setattr(data_loader, 'validate_data_contract', lambda *args, **kwargs: None)
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
        target=TAKE_SKIP_TRAILING_STOP_V2_TARGET,
        seq_len=20,
        clear_cache=True,
        num_workers=0,
    )

    X_batch, y_batch, mask_batch = next(iter(loader))
    assert X_batch.shape[0] == 2
    assert X_batch.shape[1] == 20
    assert X_batch.shape[2] > data_loader.N_FRACTAL_FEATURES
    assert y_batch.shape == (2, 9)
    assert mask_batch.shape == (2, 20)


def test_train_initial_best_metric_allows_first_negative_take_skip_v2_score():
    best_metric = train.initial_best_metric(TAKE_SKIP_TRAILING_STOP_V2_TARGET)
    assert best_metric == -float('inf')


def test_generate_signals_accepts_take_skip_v2_research_task_constant():
    assert TAKE_SKIP_TRAILING_STOP_V2_TARGET in signal_api.RESEARCH_EXPORT_TASKS


def test_evaluate_and_generate_modules_wire_take_skip_v2_exports():
    evaluate_source = evaluate_test.Path(evaluate_test.__file__).read_text(encoding='utf-8')
    generate_source = signal_api.Path(signal_api.__file__).read_text(encoding='utf-8')

    assert 'TAKE_SKIP_TRAILING_STOP_V2_TARGET' in evaluate_source
    assert 'build_take_skip_v2_export_frame' in evaluate_source
    assert 'TAKE_SKIP_TRAILING_STOP_V2_TARGET' in generate_source
    assert 'build_take_skip_v2_export_frame' in generate_source
