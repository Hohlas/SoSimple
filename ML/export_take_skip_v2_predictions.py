# =============================================================================
# Файл: export_take_skip_v2_predictions.py
# Назначение: Export prediction CSV для take_skip_v2 на произвольном Nero_XXX.csv без обучения.
# Обновлён: 2026-04-23
# Входные данные:
#   - Nero_XXX.csv с колонками time/signal/fractal* и trailing-stop PnL (откуда: MT/MQL4/Files)
#   - checkpoint.pt для take_skip_v2 contour (откуда: ML/reports/*/checkpoint.pt)
# Выходные данные:
#   - prediction CSV с pred_take_* и optional true_* колонками (куда: output)
# Использование:
#   python -m ML.export_take_skip_v2_predictions --input-csv ... --checkpoint ... --output ...
# Примечания:
#   - helper ничего не обучает и не меняет frozen rule
# =============================================================================

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader, Dataset

from ML.data_loader import parse_fractals_to_3d
from ML.models.transformer import TransformerClassifier
from ML.run_take_skip_original_contour_feature_matrix import append_repeated_channels
from ML.run_take_skip_original_contour_feature_matrix import build_original_contour_engineered_features
from ML.run_take_skip_original_contour_feature_matrix import FEATURE_MODES
from ML.run_take_skip_original_contour_feature_matrix import OriginalContourArrays
from ML.run_take_skip_original_contour_feature_matrix import build_original_contour_arrays
from ML.take_skip_trailing_stop_v2_task import TAKE_SKIP_TRAILING_STOP_V2_COLUMNS


DEFAULT_TARGET_COLUMNS_9 = tuple(column for column in TAKE_SKIP_TRAILING_STOP_V2_COLUMNS if column.endswith(("_x2", "_x4", "_x8")))


class PredictionDataset(Dataset):
    def __init__(self, X: np.ndarray, mask: np.ndarray):
        self.X = torch.from_numpy(X.astype(np.float32)).float()
        self.mask = torch.from_numpy(mask.astype(bool)).bool()

    def __len__(self) -> int:
        return len(self.X)

    def __getitem__(self, idx: int):
        return self.X[idx], self.mask[idx]


def _infer_num_classes(ckpt: dict) -> int:
    model_kwargs = ckpt.get("model_kwargs", {})
    if "num_classes" in model_kwargs:
        return int(model_kwargs["num_classes"])
    classifier_weights: list[tuple[int, object]] = []
    for key, value in ckpt["model_state_dict"].items():
        if key.startswith("classifier.") and key.endswith(".weight") and getattr(value, "ndim", 0) == 2:
            layer_idx = int(key.split(".")[1])
            classifier_weights.append((layer_idx, value))
    if classifier_weights:
        classifier_weights.sort(key=lambda item: item[0])
        return int(classifier_weights[-1][1].shape[0])
    raise ValueError("cannot infer num_classes from checkpoint")


def _resolve_target_columns(num_classes: int, target_columns: tuple[str, ...] | None) -> tuple[str, ...]:
    if target_columns is not None:
        if len(target_columns) != num_classes:
            raise ValueError(f"target_columns length {len(target_columns)} does not match num_classes {num_classes}")
        return tuple(target_columns)
    if num_classes == len(DEFAULT_TARGET_COLUMNS_9):
        return DEFAULT_TARGET_COLUMNS_9
    if num_classes == len(TAKE_SKIP_TRAILING_STOP_V2_COLUMNS):
        return tuple(TAKE_SKIP_TRAILING_STOP_V2_COLUMNS)
    raise ValueError(f"cannot infer target_columns for num_classes={num_classes}")


def _predict_probabilities(
    model: TransformerClassifier,
    X: np.ndarray,
    mask: np.ndarray,
    *,
    batch_size: int,
) -> np.ndarray:
    loader = DataLoader(PredictionDataset(X, mask), batch_size=batch_size, shuffle=False, drop_last=False)
    model.eval()
    chunks = []
    with torch.no_grad():
        for X_batch, mask_batch in loader:
            logits = model(X_batch, mask=mask_batch)
            chunks.append(torch.sigmoid(logits).cpu().numpy())
    return np.vstack(chunks).astype(np.float32)


def _target_to_true_pnl_column(target_column: str) -> str:
    _, horizon, x_suffix = target_column.split("_")
    return f"trail_{horizon}_pnl_atr_{x_suffix}"


def _build_export_frame(arrays: OriginalContourArrays, pred_prob: np.ndarray, *, include_true_targets: bool) -> pd.DataFrame:
    pred_prob = np.asarray(pred_prob, dtype=np.float32)
    if pred_prob.shape != arrays.y.shape:
        raise ValueError(f"pred_prob shape {pred_prob.shape} does not match target shape {arrays.y.shape}")
    frame = pd.DataFrame({"time": arrays.times, "signal": arrays.signal})
    for idx, target in enumerate(arrays.target_columns):
        frame[f"pred_{target}"] = pred_prob[:, idx]
        if include_true_targets:
            frame[f"true_{target}"] = arrays.y[:, idx]
            frame[f"true_{_target_to_true_pnl_column(target)}"] = arrays.true_pnl[:, idx]
    return frame


def _build_plain_export_frame(frame: pd.DataFrame, seq_len: int, target_columns: tuple[str, ...], *, include_true_targets: bool) -> OriginalContourArrays:
    parsed_X, mask = parse_fractals_to_3d(frame)
    source_columns = [_target_to_true_pnl_column(column) for column in target_columns]
    missing = [column for column in source_columns if column not in frame.columns]
    if include_true_targets and missing:
        raise ValueError(f"missing take/skip v2 source columns: {missing}")
    if missing:
        true_pnl = np.zeros((len(frame), len(target_columns)), dtype=np.float32)
        y = np.zeros_like(true_pnl)
    else:
        true_pnl = frame[source_columns].to_numpy(dtype=np.float32)
        y = (true_pnl >= 0.5).astype(np.float32)
    return OriginalContourArrays(
        X=parsed_X[:, :seq_len, :].astype(np.float32, copy=False),
        mask=mask[:, :seq_len].astype(bool, copy=False),
        y=y,
        signal=pd.to_numeric(frame["signal"], errors="coerce").fillna(0).to_numpy(dtype=np.int64),
        times=frame["time"].astype(str).to_numpy(dtype=object),
        true_pnl=true_pnl,
        target_columns=target_columns,
        parsed_X=parsed_X,
        engineered=np.zeros((len(frame), 0), dtype=np.float32),
    )


def _build_original_contour_inference_arrays(
    frame: pd.DataFrame,
    *,
    seq_len: int,
    feature_mode: str,
    target_columns: tuple[str, ...],
) -> OriginalContourArrays:
    parsed_X, mask = parse_fractals_to_3d(frame)
    engineered = build_original_contour_engineered_features(
        frame,
        parsed_X,
        feature_mode=feature_mode,
        seq_len=seq_len,
    )
    X = append_repeated_channels(parsed_X, engineered)[:, :seq_len, :]
    return OriginalContourArrays(
        X=X.astype(np.float32, copy=False),
        mask=mask[:, :seq_len].astype(bool, copy=False),
        y=np.zeros((len(frame), len(target_columns)), dtype=np.float32),
        signal=pd.to_numeric(frame["signal"], errors="coerce").fillna(0).to_numpy(dtype=np.int64),
        times=frame["time"].astype(str).to_numpy(dtype=object),
        true_pnl=np.zeros((len(frame), len(target_columns)), dtype=np.float32),
        target_columns=target_columns,
        parsed_X=parsed_X,
        engineered=engineered,
    )


def export_predictions(
    *,
    input_csv: str | Path,
    checkpoint_path: str | Path,
    output_path: str | Path,
    mode: str,
    seq_len: int,
    feature_mode: str | None = None,
    target_columns: tuple[str, ...] | None = None,
    include_true_targets: bool = True,
    batch_size: int = 256,
) -> Path:
    frame = pd.read_csv(Path(input_csv), sep=";", low_memory=False)
    ckpt = torch.load(Path(checkpoint_path), map_location="cpu", weights_only=False)
    num_classes = _infer_num_classes(ckpt)
    resolved_targets = _resolve_target_columns(num_classes, target_columns)

    if mode == "plain_transformer":
        arrays = _build_plain_export_frame(
            frame,
            seq_len=seq_len,
            target_columns=resolved_targets,
            include_true_targets=include_true_targets,
        )
    elif mode == "original_contour":
        if feature_mode not in FEATURE_MODES:
            raise ValueError(f"feature_mode must be one of {FEATURE_MODES}")
        if include_true_targets:
            arrays = build_original_contour_arrays(
                frame,
                feature_mode=str(feature_mode),
                seq_len=seq_len,
                target_columns=resolved_targets,
            )
        else:
            arrays = _build_original_contour_inference_arrays(
                frame,
                feature_mode=str(feature_mode),
                seq_len=seq_len,
                target_columns=resolved_targets,
            )
    else:
        raise ValueError("mode must be plain_transformer or original_contour")

    model_kwargs = dict(ckpt.get("model_kwargs", {}))
    model_kwargs["input_features"] = int(arrays.X.shape[2])
    model_kwargs["num_classes"] = num_classes
    model = TransformerClassifier(**model_kwargs)
    model.load_state_dict(ckpt["model_state_dict"])
    pred_prob = _predict_probabilities(model, arrays.X, arrays.mask, batch_size=int(batch_size))

    export = _build_export_frame(arrays, pred_prob, include_true_targets=include_true_targets)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    export.to_csv(output, sep=";", index=False)
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export take_skip_v2 prediction CSV for an arbitrary Nero_XXX.csv.")
    parser.add_argument("--input-csv", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--mode", choices=["plain_transformer", "original_contour"], required=True)
    parser.add_argument("--seq-len", type=int, required=True)
    parser.add_argument("--feature-mode", default=None)
    parser.add_argument("--target-columns", nargs="+", default=None)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--inference-only", action="store_true", help="Do not require trail_* source columns and do not write true_* columns.")
    return parser.parse_args()


def main() -> Path:
    args = parse_args()
    output = export_predictions(
        input_csv=args.input_csv,
        checkpoint_path=args.checkpoint,
        output_path=args.output,
        mode=args.mode,
        seq_len=args.seq_len,
        feature_mode=args.feature_mode,
        target_columns=tuple(args.target_columns) if args.target_columns else None,
        include_true_targets=not args.inference_only,
        batch_size=args.batch_size,
    )
    print(output)
    return output


if __name__ == "__main__":
    main()
