# =============================================================================
# Файл: tests/test_entry_path_v1_quantile_training.py
# Назначение: Контрактные тесты для entry_path_v1_quantile loader/train plumbing.
# Язык: Python 3.11+
# Использование:
#   ./.venv/bin/python -m pytest tests/test_entry_path_v1_quantile_training.py -q
# =============================================================================

import sys

import numpy as np
import pytest
import torch
from torch.utils.data import DataLoader

sys.path.insert(0, '.')

from ML import data_loader as dl
from ML import train as tr
from ML.entry_path_task import ENTRY_PATH_TARGET
from ML.entry_path_v1_quantile_task import ENTRY_PATH_V1_QUANTILE_TARGET


class _DummyQuantileModel(torch.nn.Module):
    def __init__(self, **kwargs):
        super().__init__()
        self.bias = torch.nn.Parameter(torch.zeros(1))

    def forward(self, x, mask=None):
        batch = x.shape[0]
        zeros3 = torch.zeros(batch, 3, dtype=x.dtype, device=x.device)
        zeros6 = torch.zeros(batch, 6, dtype=x.dtype, device=x.device)
        zeros1 = torch.zeros(batch, 1, dtype=x.dtype, device=x.device)
        return {
            'ret': zeros3,
            'path_reg': zeros6,
            'path_cls': zeros3,
            'ret_q10': zeros1,
            'ret_q90': zeros1,
        }


def test_entry_path_v1_quantile_reuses_entry_path_target_profile():
    assert dl.task_target_column(ENTRY_PATH_V1_QUANTILE_TARGET) == ENTRY_PATH_TARGET
    assert dl.task_checkpoint_suffix(ENTRY_PATH_V1_QUANTILE_TARGET) == '_entry_path_v1_quantile'


def test_compute_entry_path_v1_quantile_losses_ignore_inactive_rows():
    outputs_active_only = {
        'ret': torch.zeros(3, 3),
        'path_reg': torch.zeros(3, 6),
        'path_cls': torch.zeros(3, 3),
        'ret_q10': torch.zeros(3, 1),
        'ret_q90': torch.zeros(3, 1),
    }
    outputs_with_bad_inactive_row = {
        'ret': torch.zeros(3, 3),
        'path_reg': torch.zeros(3, 6),
        'path_cls': torch.zeros(3, 3),
        'ret_q10': torch.tensor([[-100.0], [0.0], [0.0]]),
        'ret_q90': torch.tensor([[100.0], [0.0], [0.0]]),
    }
    y_reg = torch.zeros(3, 9)
    y_cls = torch.zeros(3, dtype=torch.long)
    signal = torch.tensor([0, 1, -1], dtype=torch.long)

    loss_good = tr.compute_entry_path_v1_quantile_losses(outputs_active_only, y_reg, y_cls, signal)
    loss_bad = tr.compute_entry_path_v1_quantile_losses(outputs_with_bad_inactive_row, y_reg, y_cls, signal)

    assert loss_good['active_count'] == 2
    assert loss_bad['active_count'] == 2
    assert loss_good['loss_q10'] == pytest.approx(loss_bad['loss_q10'], abs=1e-12)
    assert loss_good['loss_q90'] == pytest.approx(loss_bad['loss_q90'], abs=1e-12)
    assert loss_good['loss'].item() == pytest.approx(loss_bad['loss'].item(), abs=1e-12)


def test_validate_entry_path_v1_quantile_uses_task_module_val_score(monkeypatch):
    captured = {}

    def spy_metrics(**kwargs):
        captured.update(kwargs)
        return {
            'ret_pearson_r': 0.11,
            'interval_coverage': 0.80,
            'median_interval_width': 0.25,
            'coverage_error': 0.0,
            'q10_pinball_loss': 0.01,
            'q90_pinball_loss': 0.02,
            'val_score': 0.73,
        }

    monkeypatch.setattr(
        tr,
        'compute_entry_path_v1_quantile_metrics',
        spy_metrics,
    )
    monkeypatch.setattr(
        tr,
        'compute_entry_path_v1_quantile_losses',
        lambda *args, **kwargs: {
            'loss': torch.tensor(0.0),
            'loss_ret': 0.0,
            'loss_path_reg': 0.0,
            'loss_path_cls': 0.0,
            'loss_q10': 0.0,
            'loss_q90': 0.0,
            'active_count': 1,
        },
    )

    class _ActiveOnlyModel(torch.nn.Module):
        def forward(self, x, mask=None):
            batch = x.shape[0]
            return {
                'ret': torch.zeros(batch, 3, dtype=torch.float32),
                'path_reg': torch.zeros(batch, 6, dtype=torch.float32),
                'path_cls': torch.zeros(batch, 3, dtype=torch.float32),
                'ret_q10': torch.tensor([[99.0], [1.0], [2.0]], dtype=torch.float32),
                'ret_q90': torch.tensor([[199.0], [3.0], [4.0]], dtype=torch.float32),
            }

    dataset = dl.EntryPathDataset(
        X=np.zeros((3, 2, 3), dtype=np.float32),
        y_reg=np.zeros((3, 9), dtype=np.float32),
        y_cls=np.array([0, 1, 2], dtype=np.int64),
        mask=np.ones((3, 2), dtype=bool),
        signal=np.array([0, 1, -1], dtype=np.int64),
    )
    loader = DataLoader(dataset, batch_size=3, shuffle=False)

    loss, metrics = tr.validate_entry_path_v1_quantile(
        model=_ActiveOnlyModel(),
        val_loader=loader,
        device=torch.device('cpu'),
    )

    assert loss == pytest.approx(0.0, abs=1e-12)
    assert metrics['val_score'] == pytest.approx(0.73)
    assert len(captured['true_ret']) == 2
    assert captured['pred_q10'].tolist() == [1.0, 2.0]
    assert captured['pred_q90'].tolist() == [3.0, 4.0]


def test_create_test_loader_reuses_entry_path_cache_for_quantile_task(monkeypatch, tmp_path):
    monkeypatch.setattr(dl, 'DATA_DIR', tmp_path)
    monkeypatch.setattr(dl, 'TEST_FILE', tmp_path / 'Nero_test_labeled.csv')

    tmp_path.joinpath('Nero_test_labeled.csv').write_text('time;signal;predict;ATR\n1;1;0;1\n', encoding='utf-8')
    np.save(tmp_path / 'X_test.npy', np.arange(3 * 4 * 20, dtype=np.float32).reshape(3, 4, 20))
    np.save(tmp_path / 'mask_test.npy', np.ones((3, 4), dtype=bool))
    np.save(tmp_path / 'y_test_entry_path_v1_reg.npy', np.arange(27, dtype=np.float32).reshape(3, 9))
    np.save(tmp_path / 'y_test_entry_path_v1_cls.npy', np.array([0, 1, 2], dtype=np.int64))
    np.save(tmp_path / 'y_test_entry_path_v1_signal.npy', np.array([0, 1, -1], dtype=np.int64))

    loader = dl.create_test_loader(
        batch_size=3,
        target=ENTRY_PATH_V1_QUANTILE_TARGET,
        seq_len=2,
        clear_cache=False,
        num_workers=0,
    )

    batch = next(iter(loader))
    assert len(batch) == 5
    assert batch[0].shape == (3, 2, 20)
    assert batch[1].shape == (3, 9)
    assert batch[2].tolist() == [0, 1, 2]
    assert batch[4].tolist() == [0, 1, -1]


def test_train_model_routes_entry_path_v1_quantile_through_entry_path_loader_and_checkpoint(monkeypatch, tmp_path):
    captured = {}

    def fake_create_data_loaders(*, target, **kwargs):
        captured['target'] = target
        train_loader = [
            (
                torch.zeros(2, 3, dtype=torch.float32),
                torch.zeros(2, 9, dtype=torch.float32),
                torch.ones(2, dtype=torch.bool),
                torch.tensor([0, 1], dtype=torch.int64),
            )
        ]
        val_loader = [
            (
                torch.zeros(2, 3, dtype=torch.float32),
                torch.zeros(2, 9, dtype=torch.float32),
                torch.ones(2, dtype=torch.bool),
                torch.tensor([0, 1], dtype=torch.int64),
            )
        ]
        return train_loader, val_loader, None

    monkeypatch.setattr(tr, 'create_data_loaders', fake_create_data_loaders)
    monkeypatch.setattr(tr, 'EntryPathV1QuantileTransformer', _DummyQuantileModel)
    monkeypatch.setattr(tr, 'train_one_epoch_entry_path_v1_quantile', lambda *args, **kwargs: 0.0)
    monkeypatch.setattr(
        tr,
        'validate_entry_path_v1_quantile',
        lambda *args, **kwargs: (
            0.0,
            {
                'ret_pearson_r': 0.1,
                'mae': 0.0,
                'rmse': 0.0,
                'r2': 0.0,
                'path_reg_pearson_r': 0.2,
                'path_cls_f1_macro': 0.3,
                'active_path_cls_f1_macro': 0.4,
                'val_score': 0.73,
            },
        ),
    )
    monkeypatch.setattr(tr, '_log_experiment', lambda **kwargs: None)
    monkeypatch.setattr(tr, 'set_seed', lambda seed: None)
    monkeypatch.setattr(tr, 'get_device', lambda: torch.device('cpu'))
    monkeypatch.setattr(tr, 'CHECKPOINTS_DIR', tmp_path)
    monkeypatch.setattr(tr, 'PLOTS_DIR', tmp_path)
    monkeypatch.setattr(tr, 'REPORTS_DIR', tmp_path)
    monkeypatch.setattr(torch, 'save', lambda obj, path: captured.setdefault('checkpoint', path))

    result = tr.train_model(
        model_name='transformer',
        task=ENTRY_PATH_V1_QUANTILE_TARGET,
        epochs=1,
        batch_size=2,
        lr=1e-3,
        weight_decay=0.0,
        patience=1,
        seed=42,
        use_scaler=False,
        use_weighted_sampler=False,
        silent=True,
        model_kwargs={},
    )

    assert captured['target'] == ENTRY_PATH_TARGET
    assert str(captured['checkpoint']).endswith('_entry_path_v1_quantile_best.pt')
    assert result['metric_name'] == 'val_score'
    assert result['best_metric'] == pytest.approx(0.73)
