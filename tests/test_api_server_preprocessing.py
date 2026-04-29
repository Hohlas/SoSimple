import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from API import api_server


class _FakeModel:
    def __call__(self, X_tensor, *, mask):
        return torch.tensor([[0.8, 0.1, 0.0, 0.0, 0.0, 0.0]], dtype=torch.float32)


def _fractal(ts: int, direction: int = 1) -> str:
    values = [
        ts,
        4600.0,
        direction,
        10.0,
        20.0,
        0,
        0,
        0,
        1.0,
        1,
        0.5,
        10.0,
        8.0,
        15.0,
        12.0,
        20.0,
        16.0,
        0,
        0,
        0,
        0,
        2.5,
    ]
    return ":".join(str(value) for value in values)


def test_predict_signal_uses_shared_online_preprocessing(monkeypatch):
    captured: dict[str, pd.DataFrame] = {}

    def _fake_preprocess_online_frame(frame):
        captured["frame"] = frame.copy()
        return frame

    def _fake_parse_fractals_to_3d(frame):
        return (
            np.zeros((1, 100, 20), dtype=np.float32),
            np.ones((1, 100), dtype=bool),
        )

    monkeypatch.setattr(api_server, "preprocess_online_frame", _fake_preprocess_online_frame)
    monkeypatch.setattr(api_server, "parse_fractals_to_3d", _fake_parse_fractals_to_3d)
    monkeypatch.setattr(api_server, "model", _FakeModel())
    monkeypatch.setattr(api_server, "device", torch.device("cpu"))
    monkeypatch.setattr(api_server.MLServiceSettings, "seq_len", 20, raising=False)

    request = api_server.PredictRequest(
        atr_slow=2.1,
        fractals=[_fractal(100 + idx) for idx in range(api_server.N_FRACTALS)],
    )

    response = api_server.predict_signal(request)

    assert "frame" in captured
    assert captured["frame"].loc[0, "fractal0"].startswith("100:")
    assert response["signal"] == 1
