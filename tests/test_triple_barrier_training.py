# =============================================================================
# Файл: tests/test_triple_barrier_training.py
# Назначение: Unit-тесты transfer-learning kwargs для TB обучения
# Язык: Python 3.10+
# Использование:
#   ./.venv/bin/python -m pytest tests/test_triple_barrier_training.py -q
# =============================================================================

import sys
import sysconfig
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

sys.path.insert(0, '.')

stdlib_statistics_path = Path(sysconfig.get_paths()['stdlib']) / 'statistics.py'
statistics_spec = spec_from_file_location('statistics', stdlib_statistics_path)
statistics_module = module_from_spec(statistics_spec)
statistics_spec.loader.exec_module(statistics_module)
sys.modules['statistics'] = statistics_module

from ML import train as tr


def test_transfer_learning_inherits_encoder_architecture_kwargs():
    encoder_kwargs = {
        'd_model': 32,
        'nhead': 8,
        'num_layers': 3,
        'dim_feedforward': 128,
        'dropout': 0.166,
        'input_features': 20,
    }

    resolved = tr.resolve_model_kwargs_for_encoder_transfer(
        model_kwargs={'input_features': 20},
        encoder_model_kwargs=encoder_kwargs,
    )

    assert resolved['d_model'] == 32
    assert resolved['nhead'] == 8
    assert resolved['num_layers'] == 3
    assert resolved['dim_feedforward'] == 128
    assert resolved['dropout'] == 0.166
