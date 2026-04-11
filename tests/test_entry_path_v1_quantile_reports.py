import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader

sys.path.insert(0, '.')

from ML import evaluate_test as eval_mod
from ML import export_entry_path_v1_quantile_predictions as export_mod
from ML.entry_path_v1_quantile_task import ENTRY_PATH_V1_QUANTILE_TARGET
from ML.data_loader import EntryPathDataset


class _DummyQuantileModel(torch.nn.Module):
    def __init__(self, **kwargs):
        super().__init__()
        self.bias = torch.nn.Parameter(torch.zeros(1))

    def load_state_dict(self, state_dict, strict=True):
        return torch.nn.modules.module._IncompatibleKeys([], [])

    def to(self, device):
        return self

    def eval(self):
        return self

    def forward(self, x, mask=None):
        batch = x.shape[0]
        base = torch.linspace(0.1, 0.4, batch, device=x.device, dtype=x.dtype).unsqueeze(-1)
        return {
            'ret': torch.cat([base, base + 0.1, base + 0.2], dim=1),
            'path_reg': torch.cat([base + i for i in range(6)], dim=1),
            'path_cls': torch.cat([base + 0.3, base + 0.2, base + 0.5], dim=1),
            'ret_q10': base - 0.05,
            'ret_q90': base + 0.35,
        }


class _CrossedQuantileModel(_DummyQuantileModel):
    def forward(self, x, mask=None):
        out = super().forward(x, mask=mask)
        out['ret_q10'], out['ret_q90'] = out['ret_q90'], out['ret_q10']
        return out


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    pd.DataFrame(rows).to_csv(path, sep=';', index=False)


def _make_entry_path_dataset() -> EntryPathDataset:
    X = np.zeros((2, 4, 20), dtype=np.float32)
    y_reg = np.array([
        [0.1, 0.2, 0.3, 1.0, 1.1, 1.2, 2.0, 2.1, 2.2],
        [0.4, 0.5, 0.6, 1.3, 1.4, 1.5, 2.3, 2.4, 2.5],
    ], dtype=np.float32)
    y_cls = np.array([2, 0], dtype=np.int64)
    mask = np.ones((2, 4), dtype=bool)
    signal = np.array([1, -1], dtype=np.int64)
    return EntryPathDataset(X, y_reg, y_cls, mask, signal)


def _make_entry_path_dataset_with_inactive() -> EntryPathDataset:
    X = np.zeros((3, 4, 20), dtype=np.float32)
    y_reg = np.array([
        [0.1, 0.2, 0.3, 1.0, 1.1, 1.2, 2.0, 2.1, 2.2],
        [0.4, 0.5, 0.6, 1.3, 1.4, 1.5, 2.3, 2.4, 2.5],
        [0.7, 0.8, 0.9, 1.6, 1.7, 1.8, 2.6, 2.7, 2.8],
    ], dtype=np.float32)
    y_cls = np.array([2, 0, 1], dtype=np.int64)
    mask = np.ones((3, 4), dtype=bool)
    signal = np.array([1, 0, -1], dtype=np.int64)
    return EntryPathDataset(X, y_reg, y_cls, mask, signal)


def test_export_cli_writes_train_validation_test_csvs_with_quantiles(tmp_path, monkeypatch):
    train_dataset = _make_entry_path_dataset()
    val_dataset = _make_entry_path_dataset()
    test_dataset = _make_entry_path_dataset()

    train_loader = DataLoader(train_dataset, batch_size=2, shuffle=False)
    val_loader = DataLoader(val_dataset, batch_size=2, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=2, shuffle=False)

    called = {}

    def fake_create_data_loaders(*args, **kwargs):
        called['target'] = kwargs['target']
        return train_loader, val_loader, None

    def fake_create_test_loader(*args, **kwargs):
        return test_loader

    train_csv = tmp_path / 'Nero_train_labeled.csv'
    val_csv = tmp_path / 'Nero_validation_labeled.csv'
    test_csv = tmp_path / 'Nero_test_labeled.csv'
    _write_csv(train_csv, [{'time': '2024.01.01 00:00', 'signal': 1} for _ in range(2)])
    _write_csv(val_csv, [{'time': '2024.01.01 00:00', 'signal': -1} for _ in range(2)])
    _write_csv(test_csv, [{'time': '2024.01.01 00:00', 'signal': 1} for _ in range(2)])

    monkeypatch.setattr(export_mod, 'TRAIN_FILE', train_csv)
    monkeypatch.setattr(export_mod, 'VAL_FILE', val_csv)
    monkeypatch.setattr(export_mod, 'TEST_FILE', test_csv)
    monkeypatch.setattr(export_mod, 'REPORTS_DIR', tmp_path)
    monkeypatch.setattr(export_mod, 'create_data_loaders', fake_create_data_loaders)
    monkeypatch.setattr(export_mod, 'create_test_loader', fake_create_test_loader)
    monkeypatch.setattr(export_mod, 'build_entry_path_v1_quantile_model', lambda *_args, **_kwargs: _DummyQuantileModel())
    monkeypatch.setattr(export_mod.torch, 'load', lambda *args, **kwargs: {
        'model_name': 'transformer',
        'model_kwargs': {'input_features': 20, 'seq_len': 4},
        'model_state_dict': {},
    })
    monkeypatch.setattr(
        export_mod,
        'parse_args',
        lambda: SimpleNamespace(
            checkpoint=tmp_path / 'checkpoint.pt',
            output_dir=tmp_path,
            batch_size=2,
            num_workers=0,
            clear_cache=False,
            splits=['train', 'validation', 'test'],
            seed=42,
        ),
    )
    (tmp_path / 'checkpoint.pt').write_text('stub', encoding='utf-8')

    export_mod.main()

    assert called['target'] == 'entry_path_v1'

    for split in ('train', 'validation', 'test'):
        csv_path = tmp_path / f'entry_path_v1_quantile_{split}_predictions.csv'
        assert csv_path.exists()
        frame = pd.read_csv(csv_path, sep=';')
        assert 'pred_ret_24_q10' in frame.columns
        assert 'pred_ret_24_q90' in frame.columns
        assert len(frame) == 2


def test_export_predictions_validation_only_does_not_create_unrequested_loaders(tmp_path, monkeypatch):
    val_dataset = _make_entry_path_dataset()
    val_loader = DataLoader(val_dataset, batch_size=2, shuffle=False)

    val_csv = tmp_path / 'Nero_validation_labeled.csv'
    _write_csv(val_csv, [{'time': '2024.01.01 00:00', 'signal': -1} for _ in range(2)])

    monkeypatch.setattr(export_mod, 'VAL_FILE', val_csv)
    monkeypatch.setattr(export_mod, 'REPORTS_DIR', tmp_path)
    monkeypatch.setattr(export_mod, 'TRAIN_FILE', tmp_path / 'unused_train.csv')
    monkeypatch.setattr(export_mod, 'TEST_FILE', tmp_path / 'unused_test.csv')
    monkeypatch.setattr(
        export_mod,
        'create_data_loaders',
        lambda *args, **kwargs: (None, val_loader, None),
    )
    monkeypatch.setattr(
        export_mod,
        'create_test_loader',
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError('test loader should not be created')),
    )
    monkeypatch.setattr(
        export_mod,
        'build_entry_path_v1_quantile_model',
        lambda *_args, **_kwargs: _DummyQuantileModel(),
    )
    monkeypatch.setattr(export_mod.torch, 'load', lambda *args, **kwargs: {
        'model_name': 'transformer',
        'model_kwargs': {'input_features': 20, 'seq_len': 4},
        'model_state_dict': {},
    })

    checkpoint = tmp_path / 'checkpoint.pt'
    checkpoint.write_text('stub', encoding='utf-8')

    payload = export_mod.export_predictions(
        checkpoint=checkpoint,
        output_dir=tmp_path,
        splits=['validation'],
        seed=42,
    )

    assert set(payload.keys()) == {'validation'}
    assert (tmp_path / 'entry_path_v1_quantile_validation_predictions.csv').exists()
    assert not (tmp_path / 'entry_path_v1_quantile_test_predictions.csv').exists()


def test_evaluate_test_quantile_writes_report_with_quantile_metrics(tmp_path, monkeypatch):
    dataset = _make_entry_path_dataset_with_inactive()
    loader = DataLoader(dataset, batch_size=2, shuffle=False)

    csv_path = tmp_path / 'Nero_test_labeled.csv'
    _write_csv(
        csv_path,
        [
            {
                'time': '2024.01.01 00:00',
                'signal': 1,
                'ret_6_dir_atr': 0.1,
                'ret_12_dir_atr': 0.2,
                'ret_24_dir_atr': 0.3,
                'fav_6_atr': 1.0,
                'adv_6_atr': 1.1,
                'fav_12_atr': 1.2,
                'adv_12_atr': 1.3,
                'fav_24_atr': 1.4,
                'adv_24_atr': 1.5,
                'path_6_class': -1,
            },
            {
                'time': '2024.01.01 01:00',
                'signal': -1,
                'ret_6_dir_atr': 0.4,
                'ret_12_dir_atr': 0.5,
                'ret_24_dir_atr': 0.6,
                'fav_6_atr': 1.6,
                'adv_6_atr': 1.7,
                'fav_12_atr': 1.8,
                'adv_12_atr': 1.9,
                'fav_24_atr': 2.0,
                'adv_24_atr': 2.1,
                'path_6_class': 1,
            },
            {
                'time': '2024.01.01 02:00',
                'signal': 0,
                'ret_6_dir_atr': 10.0,
                'ret_12_dir_atr': 10.0,
                'ret_24_dir_atr': 10.0,
                'fav_6_atr': 2.2,
                'adv_6_atr': 2.3,
                'fav_12_atr': 2.4,
                'adv_12_atr': 2.5,
                'fav_24_atr': 2.6,
                'adv_24_atr': 2.7,
                'path_6_class': 0,
            },
        ],
    )

    monkeypatch.setattr(eval_mod, 'TEST_FILE', csv_path)
    monkeypatch.setattr(eval_mod, 'REPORTS_DIR', tmp_path)
    monkeypatch.setattr(eval_mod, 'CHECKPOINTS_DIR', tmp_path)
    monkeypatch.setattr(eval_mod, 'create_test_loader', lambda *args, **kwargs: loader)
    monkeypatch.setattr(eval_mod, 'build_entry_path_v1_quantile_model', lambda *_args, **_kwargs: _CrossedQuantileModel())
    monkeypatch.setattr(eval_mod.torch, 'load', lambda *args, **kwargs: {
        'model_name': 'transformer',
        'model_kwargs': {'input_features': 20, 'seq_len': 4},
        'model_state_dict': {},
        'epoch': 3,
        'metric_name': 'val_score',
        'best_metric': 0.42,
    })

    checkpoint = tmp_path / 'transformer_entry_path_v1_quantile_best.pt'
    checkpoint.write_text('stub', encoding='utf-8')

    eval_mod.run_evaluation(
        checkpoint_path=str(checkpoint),
        task=ENTRY_PATH_V1_QUANTILE_TARGET,
    )

    export_path = tmp_path / 'entry_path_v1_quantile_test_predictions.csv'
    report_path = tmp_path / 'evaluate_test_entry_path_v1_quantile.md'

    assert export_path.exists()
    assert report_path.exists()

    frame = pd.read_csv(export_path, sep=';')
    report = report_path.read_text(encoding='utf-8')

    assert 'pred_ret_24_q10' in frame.columns
    assert 'pred_ret_24_q90' in frame.columns
    assert 'interval_coverage' in report
    assert 'median_interval_width' in report
    assert 'val_score' in report
    assert 'interval_coverage: **1.0000**' in report
    assert 'median_interval_width: **0.4000**' in report
    assert 'active_rows: **2**' in report
    assert 'crossed_quantile_rows' in report
    assert 'Entry Path v1 Quantile' in report


def test_evaluate_test_parse_args_accepts_entry_path_v1_quantile(monkeypatch):
    monkeypatch.setattr(
        sys,
        'argv',
        ['prog', '--task', ENTRY_PATH_V1_QUANTILE_TARGET],
    )

    args = eval_mod.parse_args()

    assert args.task == ENTRY_PATH_V1_QUANTILE_TARGET


def test_evaluate_test_quantile_writes_report_to_explicit_output_dir(tmp_path, monkeypatch):
    dataset = _make_entry_path_dataset()
    loader = DataLoader(dataset, batch_size=2, shuffle=False)

    csv_path = tmp_path / 'Nero_test_labeled.csv'
    _write_csv(
        csv_path,
        [
            {
                'time': '2024.01.01 00:00',
                'signal': 1,
                'ret_6_dir_atr': 0.1,
                'ret_12_dir_atr': 0.2,
                'ret_24_dir_atr': 0.3,
                'fav_6_atr': 1.0,
                'adv_6_atr': 1.1,
                'fav_12_atr': 1.2,
                'adv_12_atr': 1.3,
                'fav_24_atr': 1.4,
                'adv_24_atr': 1.5,
                'path_6_class': -1,
            },
            {
                'time': '2024.01.01 01:00',
                'signal': -1,
                'ret_6_dir_atr': 0.4,
                'ret_12_dir_atr': 0.5,
                'ret_24_dir_atr': 0.6,
                'fav_6_atr': 1.6,
                'adv_6_atr': 1.7,
                'fav_12_atr': 1.8,
                'adv_12_atr': 1.9,
                'fav_24_atr': 2.0,
                'adv_24_atr': 2.1,
                'path_6_class': 1,
            },
        ],
    )

    output_dir = tmp_path / 'seed_042' / 'reports'
    monkeypatch.setattr(eval_mod, 'TEST_FILE', csv_path)
    monkeypatch.setattr(eval_mod, 'REPORTS_DIR', tmp_path / 'default_reports')
    monkeypatch.setattr(eval_mod, 'create_test_loader', lambda *args, **kwargs: loader)
    monkeypatch.setattr(eval_mod, 'build_entry_path_v1_quantile_model', lambda *_args, **_kwargs: _DummyQuantileModel())
    monkeypatch.setattr(eval_mod.torch, 'load', lambda *args, **kwargs: {
        'model_name': 'transformer',
        'model_kwargs': {'input_features': 20, 'seq_len': 4},
        'model_state_dict': {},
        'epoch': 3,
        'metric_name': 'val_score',
        'best_metric': 0.42,
    })

    checkpoint = tmp_path / 'transformer_entry_path_v1_quantile_best.pt'
    checkpoint.write_text('stub', encoding='utf-8')

    eval_mod.run_evaluation(
        checkpoint_path=str(checkpoint),
        task=ENTRY_PATH_V1_QUANTILE_TARGET,
        output_dir=output_dir,
    )

    assert (output_dir / 'entry_path_v1_quantile_test_predictions.csv').exists()
    assert (output_dir / 'evaluate_test_entry_path_v1_quantile.md').exists()
    assert not (tmp_path / 'default_reports' / 'entry_path_v1_quantile_test_predictions.csv').exists()
