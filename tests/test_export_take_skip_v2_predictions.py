import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from ML.models.transformer import TransformerClassifier
from ML.run_take_skip_original_contour_feature_matrix import OriginalContourArrays
from ML.take_skip_trailing_stop_v2_task import TAKE_SKIP_TRAILING_STOP_V2_COLUMNS
from ML import export_take_skip_v2_predictions as exporter


def _zero_checkpoint(path: Path, *, input_features: int, num_classes: int) -> None:
    model = TransformerClassifier(input_features=input_features, num_classes=num_classes)
    state_dict = model.state_dict()
    for key, value in state_dict.items():
        state_dict[key] = torch.zeros_like(value)
    torch.save(
        {
            "model_state_dict": state_dict,
            "model_kwargs": {"input_features": input_features, "num_classes": num_classes},
            "task": "take_skip_trailing_stop_v2",
        },
        path,
    )


def test_export_predictions_plain_transformer_writes_expected_columns(tmp_path, monkeypatch):
    csv_path = tmp_path / "Nero_EURUSD.csv"
    frame = pd.DataFrame(
        {
            "time": ["2025.01.01 00:00", "2025.01.01 01:00"],
            "signal": [1, -1],
            "trail_12_pnl_atr_x2": [0.6, -0.1],
            "trail_12_pnl_atr_x4": [0.0, 0.0],
            "trail_12_pnl_atr_x8": [0.0, 0.0],
            "trail_24_pnl_atr_x2": [0.0, 0.0],
            "trail_24_pnl_atr_x4": [0.0, 0.0],
            "trail_24_pnl_atr_x8": [0.7, 0.0],
            "trail_48_pnl_atr_x2": [0.0, 0.0],
            "trail_48_pnl_atr_x4": [0.0, 0.0],
            "trail_48_pnl_atr_x8": [0.0, 0.8],
        }
    )
    frame.to_csv(csv_path, sep=";", index=False)

    monkeypatch.setattr(
        exporter,
        "parse_fractals_to_3d",
        lambda _frame: (np.zeros((2, 100, 3), dtype=np.float32), np.ones((2, 100), dtype=bool)),
    )

    ckpt_path = tmp_path / "plain.pt"
    _zero_checkpoint(ckpt_path, input_features=3, num_classes=9)
    output_path = tmp_path / "predictions.csv"

    written = exporter.export_predictions(
        input_csv=csv_path,
        checkpoint_path=ckpt_path,
        output_path=output_path,
        mode="plain_transformer",
        seq_len=50,
    )

    assert written == output_path
    saved = pd.read_csv(output_path, sep=";")
    assert list(saved.columns[:2]) == ["time", "signal"]
    assert saved.shape[0] == 2
    assert f"pred_{TAKE_SKIP_TRAILING_STOP_V2_COLUMNS[0]}" in saved.columns
    assert f"true_{TAKE_SKIP_TRAILING_STOP_V2_COLUMNS[0]}" in saved.columns
    assert f"true_trail_24_pnl_atr_x8" in saved.columns


def test_export_predictions_original_contour_uses_feature_builder(tmp_path, monkeypatch):
    csv_path = tmp_path / "Nero_XAGUSD.csv"
    pd.DataFrame({"time": ["2025.01.01 00:00"], "signal": [1]}).to_csv(csv_path, sep=";", index=False)

    arrays = OriginalContourArrays(
        X=np.zeros((1, 50, 844), dtype=np.float32),
        mask=np.ones((1, 50), dtype=bool),
        y=np.zeros((1, 9), dtype=np.float32),
        signal=np.array([1], dtype=np.int64),
        times=np.array(["2025.01.01 00:00"], dtype=object),
        true_pnl=np.zeros((1, 9), dtype=np.float32),
        target_columns=tuple(TAKE_SKIP_TRAILING_STOP_V2_COLUMNS[:9]),
        parsed_X=np.zeros((1, 100, 20), dtype=np.float32),
        engineered=np.zeros((1, 824), dtype=np.float32),
    )
    monkeypatch.setattr(exporter, "build_original_contour_arrays", lambda *args, **kwargs: arrays)

    ckpt_path = tmp_path / "original.pt"
    _zero_checkpoint(ckpt_path, input_features=844, num_classes=9)
    output_path = tmp_path / "original_predictions.csv"

    written = exporter.export_predictions(
        input_csv=csv_path,
        checkpoint_path=ckpt_path,
        output_path=output_path,
        mode="original_contour",
        seq_len=50,
        feature_mode="original_plus_path",
    )

    assert written == output_path
    saved = pd.read_csv(output_path, sep=";")
    assert saved.loc[0, "time"] == "2025.01.01 00:00"
    assert saved.loc[0, "signal"] == 1
    assert f"pred_{TAKE_SKIP_TRAILING_STOP_V2_COLUMNS[5]}" in saved.columns


def test_parse_args_reads_mode_and_feature_mode(monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "export_take_skip_v2_predictions.py",
            "--input-csv",
            "Nero_EURUSD.csv",
            "--checkpoint",
            "model.pt",
            "--output",
            "pred.csv",
            "--mode",
            "original_contour",
            "--feature-mode",
            "original_plus_path",
            "--seq-len",
            "50",
            "--batch-size",
            "1024",
        ],
    )

    args = exporter.parse_args()

    assert args.input_csv == "Nero_EURUSD.csv"
    assert args.checkpoint == "model.pt"
    assert args.output == "pred.csv"
    assert args.mode == "original_contour"
    assert args.feature_mode == "original_plus_path"
    assert args.seq_len == 50
    assert args.batch_size == 1024


def test_export_predictions_allows_inference_without_true_pnl_columns(tmp_path, monkeypatch):
    csv_path = tmp_path / "Nero_GBPUSD.csv"
    pd.DataFrame({"time": ["2025.01.01 00:00"], "signal": [1]}).to_csv(csv_path, sep=";", index=False)
    monkeypatch.setattr(
        exporter,
        "parse_fractals_to_3d",
        lambda _frame: (np.zeros((1, 100, 3), dtype=np.float32), np.ones((1, 100), dtype=bool)),
    )

    ckpt_path = tmp_path / "plain.pt"
    _zero_checkpoint(ckpt_path, input_features=3, num_classes=9)
    output_path = tmp_path / "predictions.csv"

    exporter.export_predictions(
        input_csv=csv_path,
        checkpoint_path=ckpt_path,
        output_path=output_path,
        mode="plain_transformer",
        seq_len=50,
        include_true_targets=False,
    )

    saved = pd.read_csv(output_path, sep=";")
    assert "pred_take_24_x8" in saved.columns
    assert "true_take_24_x8" not in saved.columns


def test_export_predictions_inference_only_avoids_second_original_contour_parse(tmp_path, monkeypatch):
    csv_path = tmp_path / "Nero_USDCHF.csv"
    pd.DataFrame({"time": ["2025.01.01 00:00"], "signal": [1]}).to_csv(csv_path, sep=";", index=False)

    parse_calls = {"count": 0}

    def _parse(_frame):
        parse_calls["count"] += 1
        return np.zeros((1, 100, 3), dtype=np.float32), np.ones((1, 100), dtype=bool)

    monkeypatch.setattr(exporter, "parse_fractals_to_3d", _parse)
    monkeypatch.setattr(
        exporter,
        "build_original_contour_engineered_features",
        lambda frame, parsed_X, **kwargs: np.zeros((len(frame), 5), dtype=np.float32),
    )

    def _unexpected(*args, **kwargs):
        raise AssertionError("build_original_contour_arrays should not be used in inference-only mode")

    monkeypatch.setattr(exporter, "build_original_contour_arrays", _unexpected)

    ckpt_path = tmp_path / "original.pt"
    _zero_checkpoint(ckpt_path, input_features=8, num_classes=9)
    output_path = tmp_path / "predictions.csv"

    exporter.export_predictions(
        input_csv=csv_path,
        checkpoint_path=ckpt_path,
        output_path=output_path,
        mode="original_contour",
        seq_len=50,
        feature_mode="original_baseline",
        include_true_targets=False,
    )

    assert parse_calls["count"] == 1
    saved = pd.read_csv(output_path, sep=";")
    assert "pred_take_24_x8" in saved.columns
