import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, '.')

import ML.data_loader as dl
from ML.entry_path_task import ENTRY_PATH_TARGET, ENTRY_PATH_V1_FEATURE_COLUMNS


def _write_entry_path_cache(root: Path, prefix: str, rows: int = 3) -> None:
    x = np.arange(rows * 100 * dl.N_FRACTAL_FEATURES, dtype=np.float32).reshape(rows, 100, dl.N_FRACTAL_FEATURES)
    mask = np.ones((rows, 100), dtype=bool)
    engineered = np.ones((rows, len(ENTRY_PATH_V1_FEATURE_COLUMNS)), dtype=np.float32)
    y_reg = np.zeros((rows, 9), dtype=np.float32)
    y_cls = np.zeros(rows, dtype=np.int64)
    signal = np.ones(rows, dtype=np.int64)

    np.save(root / f'X_{prefix}.npy', x)
    np.save(root / f'mask_{prefix}.npy', mask)
    np.save(root / f'y_{prefix}_{ENTRY_PATH_TARGET}_engineered.npy', engineered)
    np.save(root / f'y_{prefix}_{ENTRY_PATH_TARGET}_reg.npy', y_reg)
    np.save(root / f'y_{prefix}_{ENTRY_PATH_TARGET}_cls.npy', y_cls)
    np.save(root / f'y_{prefix}_{ENTRY_PATH_TARGET}_signal.npy', signal)


def _write_entry_path_profile_cache(root: Path, prefix: str, profile: str, rows: int = 3, width: int = 4) -> None:
    x = np.arange(rows * 100 * dl.N_FRACTAL_FEATURES, dtype=np.float32).reshape(rows, 100, dl.N_FRACTAL_FEATURES)
    mask = np.ones((rows, 100), dtype=bool)
    engineered = np.ones((rows, width), dtype=np.float32)
    y_reg = np.zeros((rows, 9), dtype=np.float32)
    y_cls = np.zeros(rows, dtype=np.int64)
    signal = np.ones(rows, dtype=np.int64)
    suffix = f'_features_{profile}'

    np.save(root / f'X_{prefix}.npy', x)
    np.save(root / f'mask_{prefix}.npy', mask)
    np.save(root / f'y_{prefix}_{ENTRY_PATH_TARGET}_engineered{suffix}.npy', engineered)
    np.save(root / f'y_{prefix}_{ENTRY_PATH_TARGET}_reg{suffix}.npy', y_reg)
    np.save(root / f'y_{prefix}_{ENTRY_PATH_TARGET}_cls{suffix}.npy', y_cls)
    np.save(root / f'y_{prefix}_{ENTRY_PATH_TARGET}_signal{suffix}.npy', signal)


def test_create_data_loaders_supports_entry_path_seq_len_20_50_100(monkeypatch, tmp_path):
    train_csv = tmp_path / 'Nero_train_labeled.csv'
    val_csv = tmp_path / 'Nero_validation_labeled.csv'
    pd.DataFrame({'time': ['2026.01.01 00:00'], 'signal': [1]}).to_csv(train_csv, sep=';', index=False)
    pd.DataFrame({'time': ['2026.01.02 00:00'], 'signal': [1]}).to_csv(val_csv, sep=';', index=False)
    _write_entry_path_cache(tmp_path, 'train')
    _write_entry_path_cache(tmp_path, 'val')

    monkeypatch.setattr(dl, 'DATA_DIR', tmp_path)
    monkeypatch.setattr(dl, 'TRAIN_FILE', train_csv)
    monkeypatch.setattr(dl, 'VAL_FILE', val_csv)

    for seq_len in (20, 50, 100):
        train_loader, val_loader, _ = dl.create_data_loaders(
            batch_size=2,
            target=ENTRY_PATH_TARGET,
            seq_len=seq_len,
            num_workers=0,
        )
        train_batch = next(iter(train_loader))
        val_batch = next(iter(val_loader))

        assert train_batch[0].shape[1] == seq_len
        assert train_batch[4].shape[1] == seq_len
        assert val_batch[0].shape[1] == seq_len
        assert val_batch[4].shape[1] == seq_len


def test_create_data_loaders_rejects_unsupported_entry_path_seq_len(monkeypatch, tmp_path):
    train_csv = tmp_path / 'Nero_train_labeled.csv'
    val_csv = tmp_path / 'Nero_validation_labeled.csv'
    pd.DataFrame({'time': ['2026.01.01 00:00'], 'signal': [1]}).to_csv(train_csv, sep=';', index=False)
    pd.DataFrame({'time': ['2026.01.02 00:00'], 'signal': [1]}).to_csv(val_csv, sep=';', index=False)
    _write_entry_path_cache(tmp_path, 'train')
    _write_entry_path_cache(tmp_path, 'val')

    monkeypatch.setattr(dl, 'DATA_DIR', tmp_path)
    monkeypatch.setattr(dl, 'TRAIN_FILE', train_csv)
    monkeypatch.setattr(dl, 'VAL_FILE', val_csv)

    try:
        dl.create_data_loaders(batch_size=2, target=ENTRY_PATH_TARGET, seq_len=30, num_workers=0)
    except ValueError as exc:
        assert 'supports only seq_len values' in str(exc)
    else:
        raise AssertionError('Expected ValueError for unsupported entry_path seq_len')


def test_create_data_loaders_keeps_non_default_entry_path_feature_profile_cache_separate(monkeypatch, tmp_path):
    train_csv = tmp_path / 'Nero_train_labeled.csv'
    val_csv = tmp_path / 'Nero_validation_labeled.csv'
    pd.DataFrame({'time': ['2026.01.01 00:00'], 'signal': [1]}).to_csv(train_csv, sep=';', index=False)
    pd.DataFrame({'time': ['2026.01.02 00:00'], 'signal': [1]}).to_csv(val_csv, sep=';', index=False)
    _write_entry_path_profile_cache(tmp_path, 'train', 'baseline_clean', width=4)
    _write_entry_path_profile_cache(tmp_path, 'val', 'baseline_clean', width=4)

    monkeypatch.setattr(dl, 'DATA_DIR', tmp_path)
    monkeypatch.setattr(dl, 'TRAIN_FILE', train_csv)
    monkeypatch.setattr(dl, 'VAL_FILE', val_csv)

    train_loader, _, _ = dl.create_data_loaders(
        batch_size=2,
        target=ENTRY_PATH_TARGET,
        seq_len=20,
        num_workers=0,
        entry_path_feature_profile='baseline_clean',
    )

    batch = next(iter(train_loader))
    assert batch[1].shape[1] == 4
