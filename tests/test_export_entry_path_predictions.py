import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ML import export_entry_path_predictions as exporter


def _write_input_csv(path: Path) -> None:
    row = {
        "time": "2025.01.01 00:00",
        "signal": 1,
        "ATR": 1.0,
        "ret_6_dir_atr": 0.1,
        "ret_12_dir_atr": 0.2,
        "ret_24_dir_atr": 0.3,
        "fav_6_atr": 0.4,
        "adv_6_atr": 0.1,
        "fav_12_atr": 0.5,
        "adv_12_atr": 0.2,
        "fav_24_atr": 0.6,
        "adv_24_atr": 0.3,
        "path_6_class": 0,
    }
    for idx in range(100):
        row[f"fractal{idx}"] = "1:1:-1:1:1:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:1"
    pd.DataFrame([row, {**row, "time": "2025.01.01 01:00", "signal": -1}]).to_csv(path, sep=";", index=False)


class _FakeEntryPathModel(torch.nn.Module):
    def forward(self, x, engineered, mask=None):
        batch = x.shape[0]
        return {
            "ret": torch.tensor([[1.0, 2.0, 3.0]] * batch),
            "path_reg": torch.tensor([[0.1, 0.2, 0.3, 0.4, 0.5, 0.6]] * batch),
            "path_cls": torch.tensor([[0.0, 2.0, 1.0]] * batch),
        }


class _FakeQuantileModel(torch.nn.Module):
    def forward(self, x, mask=None):
        batch = x.shape[0]
        return {
            "ret": torch.tensor([[1.0, 2.0, 3.0]] * batch),
            "path_reg": torch.tensor([[0.1, 0.2, 0.3, 0.4, 0.5, 0.6]] * batch),
            "path_cls": torch.tensor([[0.0, 2.0, 1.0]] * batch),
            "ret_q10": torch.tensor([[0.7]] * batch),
            "ret_q90": torch.tensor([[1.7]] * batch),
        }


def test_export_predictions_writes_plain_entry_path_contract(tmp_path, monkeypatch):
    input_csv = tmp_path / "instrument.csv"
    output_csv = tmp_path / "entry_path_v1_predictions.csv"
    _write_input_csv(input_csv)

    monkeypatch.setattr(exporter, "set_seed", lambda seed: None)
    monkeypatch.setattr(exporter, "get_device", lambda: torch.device("cpu"))
    monkeypatch.setattr(exporter, "parse_fractals_to_3d", lambda df: (np.zeros((len(df), 5, 20), dtype=np.float32), np.ones((len(df), 5), dtype=bool)))
    monkeypatch.setattr(exporter, "split_entry_path_features", lambda df, feature_profile, seq_len: np.zeros((len(df), 6), dtype=np.float32))
    monkeypatch.setattr(
        exporter,
        "split_entry_path_targets",
        lambda df: (
            np.zeros((len(df), 9), dtype=np.float32),
            np.ones(len(df), dtype=np.int64),
        ),
    )
    monkeypatch.setattr(exporter, "build_entry_path_model", lambda model_name, model_kwargs=None: _FakeEntryPathModel())
    monkeypatch.setattr(
        exporter,
        "load_checkpoint",
        lambda checkpoint_path, device: {"model_name": "transformer", "model_state_dict": {}, "model_kwargs": {"seq_len": 5}},
    )
    monkeypatch.setattr(torch.nn.Module, "load_state_dict", lambda self, state_dict: None)

    exporter.export_predictions(
        input_csv=input_csv,
        checkpoint="dummy.pt",
        output_csv=output_csv,
        task="entry_path_v1",
    )

    out = pd.read_csv(output_csv, sep=";")
    assert out["time"].tolist() == ["2025.01.01 00:00", "2025.01.01 01:00"]
    assert out["signal"].tolist() == [1, -1]
    assert "pred_ret_24_dir_atr" in out.columns
    assert "true_ret_24_dir_atr" in out.columns


def test_export_predictions_supports_runtime_atr_vol_regime_substitution(tmp_path, monkeypatch):
    input_csv = tmp_path / "instrument.csv"
    output_csv = tmp_path / "entry_path_v1_predictions.csv"
    _write_input_csv(input_csv)
    captured: dict[str, pd.DataFrame] = {}

    def _capture_features(df, feature_profile, seq_len):
        captured["frame"] = df.copy()
        return np.zeros((len(df), 6), dtype=np.float32)

    monkeypatch.setattr(exporter, "set_seed", lambda seed: None)
    monkeypatch.setattr(exporter, "get_device", lambda: torch.device("cpu"))
    monkeypatch.setattr(exporter, "parse_fractals_to_3d", lambda df: (np.zeros((len(df), 5, 20), dtype=np.float32), np.ones((len(df), 5), dtype=bool)))
    monkeypatch.setattr(exporter, "split_entry_path_features", _capture_features)
    monkeypatch.setattr(
        exporter,
        "split_entry_path_targets",
        lambda df: (
            np.zeros((len(df), 9), dtype=np.float32),
            np.ones(len(df), dtype=np.int64),
        ),
    )
    monkeypatch.setattr(exporter, "build_entry_path_model", lambda model_name, model_kwargs=None: _FakeEntryPathModel())
    monkeypatch.setattr(
        exporter,
        "load_checkpoint",
        lambda checkpoint_path, device: {"model_name": "transformer", "model_state_dict": {}, "model_kwargs": {"seq_len": 5}},
    )
    monkeypatch.setattr(torch.nn.Module, "load_state_dict", lambda self, state_dict: None)

    exporter.export_predictions(
        input_csv=input_csv,
        checkpoint="dummy.pt",
        output_csv=output_csv,
        task="entry_path_v1",
        vol_regime_24_mode="atr",
    )

    assert captured["frame"]["vol_regime_24"].tolist() == captured["frame"]["ATR"].tolist()


def test_export_predictions_writes_quantile_contract(tmp_path, monkeypatch):
    input_csv = tmp_path / "instrument.csv"
    output_csv = tmp_path / "entry_path_v1_quantile_predictions.csv"
    _write_input_csv(input_csv)

    monkeypatch.setattr(exporter, "set_seed", lambda seed: None)
    monkeypatch.setattr(exporter, "get_device", lambda: torch.device("cpu"))
    monkeypatch.setattr(exporter, "parse_fractals_to_3d", lambda df: (np.zeros((len(df), 5, 20), dtype=np.float32), np.ones((len(df), 5), dtype=bool)))
    monkeypatch.setattr(
        exporter,
        "split_entry_path_targets",
        lambda df: (
            np.zeros((len(df), 9), dtype=np.float32),
            np.ones(len(df), dtype=np.int64),
        ),
    )
    monkeypatch.setattr(exporter, "build_entry_path_v1_quantile_model", lambda model_kwargs=None: _FakeQuantileModel())
    monkeypatch.setattr(
        exporter,
        "load_checkpoint",
        lambda checkpoint_path, device: {"model_state_dict": {}, "model_kwargs": {"seq_len": 5}},
    )
    monkeypatch.setattr(torch.nn.Module, "load_state_dict", lambda self, state_dict: None)

    exporter.export_predictions(
        input_csv=input_csv,
        checkpoint="dummy.pt",
        output_csv=output_csv,
        task="entry_path_v1_quantile",
    )

    out = pd.read_csv(output_csv, sep=";")
    assert out["time"].tolist() == ["2025.01.01 00:00", "2025.01.01 01:00"]
    assert "pred_ret_24_q10" in out.columns
    assert "pred_ret_24_q90" in out.columns
