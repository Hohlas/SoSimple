# =============================================================================
# Файл: tests/test_entry_path_training.py
# Назначение: Unit-тесты CLI plumbing для entry_path_v1 обучения
# Язык: Python 3.11+
# Использование:
#   ./.venv/bin/python -m pytest tests/test_entry_path_training.py -q
# =============================================================================

import sys
import sysconfig
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import torch
from torch.utils.data import DataLoader

sys.path.insert(0, '.')

stdlib_statistics_path = Path(sysconfig.get_paths()['stdlib']) / 'statistics.py'
statistics_spec = spec_from_file_location('statistics', stdlib_statistics_path)
statistics_module = module_from_spec(statistics_spec)
statistics_spec.loader.exec_module(statistics_module)
sys.modules['statistics'] = statistics_module

from ML import train as tr
from ML.data_loader import EntryPathDataset
from ML.losses import HuberLoss


class _FixedBatchEntryPathModel(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.ret = torch.nn.Parameter(torch.zeros((3, 3), dtype=torch.float32))
        self.path_reg = torch.nn.Parameter(torch.zeros((3, 6), dtype=torch.float32))
        self.path_cls = torch.nn.Parameter(torch.tensor([
            [3.0, 0.0, 0.0],
            [0.0, 0.0, 0.0],
            [0.0, 0.0, 3.0],
        ], dtype=torch.float32))

    def forward(self, x, engineered, mask=None):
        batch = x.shape[0]
        return {
            'ret': self.ret[:batch] + engineered[:, :3],
            'path_reg': self.path_reg[:batch],
            'path_cls': self.path_cls[:batch],
        }


def test_main_passes_clear_cache_to_train_model(monkeypatch, tmp_path):
    captured = {}

    monkeypatch.setattr(
        tr,
        'parse_args',
        lambda: SimpleNamespace(
            model='transformer',
            task='entry_path_v1',
            use_scaler=False,
            epochs=1,
            batch_size=32,
            lr=1e-3,
            weight_decay=1e-4,
            patience=1,
            seed=42,
            focal_minority_weight=0.25,
            focal_gamma=2.0,
            regression_loss='huber',
            asym_over_penalty=1.0,
            asym_under_penalty=10.0,
            scheduler_patience=1,
            scheduler_factor=0.5,
            metric_mode='f1_macro',
            min_signal_recall=0.3,
            use_weighted_sampler=False,
            model_kwargs=None,
            seq_len=20,
            encoder_ckpt=None,
            optuna_json=None,
            clear_cache=True,
        ),
    )

    def fake_train_model(**kwargs):
        captured.update(kwargs)
        return {
            'model_name': 'transformer',
            'task': 'entry_path_v1',
            'best_metric': 0.123,
            'best_epoch': 1,
            'num_parameters': 10,
            'training_time': 1.0,
            'best_metrics': {
                'ret_pearson_r': 0.123,
                'pearson_r': 0.123,
                'mae': 0.1,
                'rmse': 0.2,
                'r2': 0.0,
                'path_reg_pearson_r': 0.05,
                'path_cls_f1_macro': 0.33,
                'ret_per_target': {},
                'path_reg_per_target': {},
                'path_cls_per_class': {},
            },
        }

    monkeypatch.setattr(tr, 'train_model', fake_train_model)
    monkeypatch.setattr(tr, 'CHECKPOINTS_DIR', tmp_path)

    tr.main()

    assert captured['clear_cache'] is True


def test_train_one_epoch_entry_path_weights_active_rows_stronger():
    dataset = EntryPathDataset(
        X=np.zeros((3, 4, 2), dtype=np.float32),
        engineered=np.zeros((3, 6), dtype=np.float32),
        y_reg=np.array([
            [1, 1, 1, 0, 0, 0, 0, 0, 0],
            [4, 4, 4, 0, 0, 0, 0, 0, 0],
            [10, 10, 10, 0, 0, 0, 0, 0, 0],
        ], dtype=np.float32),
        y_cls=np.array([0, 1, 2], dtype=np.int64),
        mask=np.ones((3, 4), dtype=bool),
        signal=np.array([-1, 0, 1], dtype=np.int64),
    )
    loader = DataLoader(dataset, batch_size=3, shuffle=False)
    model = _FixedBatchEntryPathModel()
    ret_loss = HuberLoss(delta=1.0, reduction='none')
    path_reg_loss = HuberLoss(delta=1.0)
    path_cls_loss = torch.nn.CrossEntropyLoss(reduction='none')
    optimizer = torch.optim.SGD(model.parameters(), lr=0.1)

    loss = tr.train_one_epoch_entry_path(
        model=model,
        train_loader=loader,
        ret_loss_fn=ret_loss,
        path_reg_loss_fn=path_reg_loss,
        path_cls_loss_fn=path_cls_loss,
        optimizer=optimizer,
        device=torch.device('cpu'),
    )

    expected_ret = (5.0 * 0.5 + 1.0 * 3.5 + 5.0 * 9.5) / 11.0
    cls_row0 = torch.nn.functional.cross_entropy(
        torch.tensor([[3.0, 0.0, 0.0]], dtype=torch.float32),
        torch.tensor([0], dtype=torch.int64),
        reduction='none',
    ).item()
    cls_row1 = torch.nn.functional.cross_entropy(
        torch.tensor([[0.0, 0.0, 0.0]], dtype=torch.float32),
        torch.tensor([1], dtype=torch.int64),
        reduction='none',
    ).item()
    cls_row2 = torch.nn.functional.cross_entropy(
        torch.tensor([[0.0, 0.0, 3.0]], dtype=torch.float32),
        torch.tensor([2], dtype=torch.int64),
        reduction='none',
    ).item()
    expected_cls = (20.0 * cls_row0 + 1.0 * cls_row1 + 20.0 * cls_row2) / 41.0

    assert loss == pytest.approx(expected_ret + 0.5 * expected_cls, rel=1e-6)


def test_validate_entry_path_weights_active_rows_stronger():
    dataset = EntryPathDataset(
        X=np.zeros((3, 4, 2), dtype=np.float32),
        engineered=np.zeros((3, 6), dtype=np.float32),
        y_reg=np.array([
            [1, 1, 1, 0, 0, 0, 0, 0, 0],
            [4, 4, 4, 0, 0, 0, 0, 0, 0],
            [10, 10, 10, 0, 0, 0, 0, 0, 0],
        ], dtype=np.float32),
        y_cls=np.array([0, 1, 2], dtype=np.int64),
        mask=np.ones((3, 4), dtype=bool),
        signal=np.array([-1, 0, 1], dtype=np.int64),
    )
    loader = DataLoader(dataset, batch_size=3, shuffle=False)
    model = _FixedBatchEntryPathModel()
    ret_loss = HuberLoss(delta=1.0, reduction='none')
    path_reg_loss = HuberLoss(delta=1.0)
    path_cls_loss = torch.nn.CrossEntropyLoss(reduction='none')

    _loss, metrics = tr.validate_entry_path(
        model=model,
        val_loader=loader,
        ret_loss_fn=ret_loss,
        path_reg_loss_fn=path_reg_loss,
        path_cls_loss_fn=path_cls_loss,
        device=torch.device('cpu'),
    )

    expected_ret = (5.0 * 0.5 + 1.0 * 3.5 + 5.0 * 9.5) / 11.0
    cls_row0 = torch.nn.functional.cross_entropy(
        torch.tensor([[3.0, 0.0, 0.0]], dtype=torch.float32),
        torch.tensor([0], dtype=torch.int64),
        reduction='none',
    ).item()
    cls_row1 = torch.nn.functional.cross_entropy(
        torch.tensor([[0.0, 0.0, 0.0]], dtype=torch.float32),
        torch.tensor([1], dtype=torch.int64),
        reduction='none',
    ).item()
    cls_row2 = torch.nn.functional.cross_entropy(
        torch.tensor([[0.0, 0.0, 3.0]], dtype=torch.float32),
        torch.tensor([2], dtype=torch.int64),
        reduction='none',
    ).item()
    expected_cls = (20.0 * cls_row0 + 1.0 * cls_row1 + 20.0 * cls_row2) / 41.0

    assert _loss == pytest.approx(expected_ret + 0.5 * expected_cls, rel=1e-6)
    assert 'ret_pearson_r' in metrics
    assert metrics['active_path_cls_f1_macro'] == pytest.approx(2.0 / 3.0, rel=1e-6)
    assert metrics['active_path_cls_f1_macro'] > metrics['path_cls_f1_macro']
