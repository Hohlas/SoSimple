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

sys.path.insert(0, '.')

stdlib_statistics_path = Path(sysconfig.get_paths()['stdlib']) / 'statistics.py'
statistics_spec = spec_from_file_location('statistics', stdlib_statistics_path)
statistics_module = module_from_spec(statistics_spec)
statistics_spec.loader.exec_module(statistics_module)
sys.modules['statistics'] = statistics_module

from ML import train as tr


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
