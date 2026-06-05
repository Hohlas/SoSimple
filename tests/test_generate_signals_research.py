# =============================================================================
# Файл: tests/test_generate_signals_research.py
# Назначение: Unit-тесты Triple Barrier signal selection в API/generate_signals.py
# Язык: Python 3.10+
# Использование:
#   ./.venv/bin/python -m pytest tests/test_generate_signals_research.py -q
# =============================================================================

import sys

import numpy as np

sys.path.insert(0, 'API')
import generate_signals as gs


def test_tb_preds_to_signals_returns_flat_when_ev_too_small():
    logits = np.full((1, 12), -10.0, dtype=np.float32)
    logits[0, 3] = 0.1  # buy_sl3_tp3 -> p≈0.525, EV≈0.15 < min_ev

    out = gs.tb_preds_to_signals(logits, theta=0.5, min_ev=0.5)

    assert int(out['signal'].iloc[0]) == 0
