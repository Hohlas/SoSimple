# =============================================================================
# Файл: tests/test_triple_barrier_calibration.py
# Назначение: Unit-тесты EV/calibration helper для Triple Barrier thresholding
# Язык: Python 3.11+
# Использование:
#   ./.venv/bin/python -m pytest tests/test_triple_barrier_calibration.py -q
# =============================================================================

import sys

import numpy as np
import pytest

sys.path.insert(0, 'ML')
import threshold_analysis as ta


def test_expected_value_uses_calibrated_probability():
    p = np.array([0.70])
    out = ta.expected_value_from_probability(p, sl=2, tp=6)
    assert float(out[0]) == pytest.approx(3.6, abs=1e-9)
