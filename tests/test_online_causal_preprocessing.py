import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from processing.online_causal_preprocessing import preprocess_online_csv, preprocess_online_frame
from processing.online_causal_preprocessing import validate_fractal_sorting
from processing.normalize import parse_fractal


def _fractal(ts: int, price: float, direction: int, front: float, back: float) -> str:
    values = [
        ts,
        price,
        direction,
        front,
        back,
        0,
        4,
        0,
        0,
        2,
        10,
        20,
        30,
        40,
        50,
        60,
        70,
        1.5,
        0,
        0,
        0,
        1.0,
        0,     # shift (index 22)
    ]
    return ":".join(str(v) for v in values)


def test_preprocess_online_frame_is_idempotent_for_sorted_normalized_input():
    raw = pd.DataFrame(
        {
            "time": ["2026.04.29 03:55"],
            "signal": [0],
            "predict": [0],
            "ATR": [2.1],
            "fractal0": [_fractal(300, 4620.0, -1, 10, 20)],
            "fractal1": [_fractal(200, 4610.0, 1, 20, 30)],
            "fractal2": [_fractal(100, 4600.0, 1, 30, 40)],
        }
    )

    once = preprocess_online_frame(raw)
    twice = preprocess_online_frame(once)

    assert twice.equals(once)


def test_preprocess_online_frame_is_quiet_by_default(capsys):
    raw = pd.DataFrame(
        {
            "time": ["2026.04.29 03:55"],
            "signal": [0],
            "predict": [0],
            "ATR": [2.1],
            "fractal0": [_fractal(100, 4600.0, 1, 30, 40)],
            "fractal1": [_fractal(300, 4620.0, -1, 10, 20)],
        }
    )

    preprocess_online_frame(raw)

    captured = capsys.readouterr()
    assert captured.out == ""
