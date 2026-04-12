import numpy as np

from ML import data_loader as dl
from ML import entry_path_quantile_task as eqt
from ML import train as train_mod


def test_task_target_column_returns_quantile_profile():
    assert dl.task_target_column(eqt.ENTRY_PATH_QUANTILE_TARGET) == eqt.ENTRY_PATH_QUANTILE_TARGET


def test_split_loader_accepts_entry_path_quantile_target(monkeypatch):
    seen = {}

    def fake_create_data_loaders(**kwargs):
        seen.update(kwargs)
        return 'train_loader', 'val_loader', None

    monkeypatch.setattr(dl, 'create_data_loaders', fake_create_data_loaders)

    loader = dl.create_split_loader(split='validation', target=eqt.ENTRY_PATH_QUANTILE_TARGET, seq_len=20)

    assert loader == 'val_loader'
    assert seen['target'] == eqt.ENTRY_PATH_QUANTILE_TARGET


def test_compute_quantile_val_score_penalizes_coverage_error_and_width():
    metrics = train_mod.compute_entry_path_quantile_metrics(
        y_true=np.array([0.0, 1.0, 2.0], dtype=np.float32),
        pred_point=np.array([0.0, 1.0, 2.0], dtype=np.float32),
        pred_q10=np.array([-1.0, 0.0, 1.0], dtype=np.float32),
        pred_q90=np.array([1.0, 2.0, 3.0], dtype=np.float32),
    )

    assert 'val_score' in metrics
    assert metrics['interval_coverage'] == 1.0
    assert metrics['median_interval_width'] == 2.0
    assert np.isclose(metrics['coverage_error'], 0.2)
    assert np.isclose(metrics['val_score'], 1.0 - 0.5 * 0.2 - 0.1 * 2.0)
