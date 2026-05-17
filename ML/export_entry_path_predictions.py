# =============================================================================
# Файл: export_entry_path_predictions.py
# Назначение: Инференс entry_path_v1 / entry_path_v1_quantile на arbitrary labeled CSV без переобучения.
# Обновлён: 2026-04-24
# Входные данные:
#   - labeled CSV с time, signal, ATR, fractal0..fractal99 и entry_path target columns
#   - checkpoint entry_path_v1 или entry_path_v1_quantile
# Выходные данные:
#   - prediction CSV с research-контрактом entry_path_*_predictions.csv
# Использование:
#   python -m ML.export_entry_path_predictions --task entry_path_v1 --input-csv ... --checkpoint ... --output ...
# Примечания:
#   - модуль не переобучает модель и не меняет frozen rules
# =============================================================================

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader

from ML.data_loader import EntryPathDataset
from ML.data_loader import parse_fractals_to_3d
from ML.entry_path_task import ENTRY_PATH_DEFAULT_FEATURE_PROFILE
from ML.entry_path_task import ENTRY_PATH_TARGET
from ML.entry_path_task import build_entry_path_export_frame
from ML.entry_path_task import build_entry_path_model
from ML.entry_path_task import split_entry_path_features
from ML.entry_path_task import split_entry_path_targets
from ML.entry_path_v1_quantile_task import ENTRY_PATH_V1_QUANTILE_TARGET
from ML.entry_path_v1_quantile_task import build_entry_path_v1_quantile_export_frame
from ML.entry_path_v1_quantile_task import build_entry_path_v1_quantile_model
from ML.utils import get_device
from ML.utils import set_seed
from processing.label_signals import add_entry_path_frequency_features

VOL_REGIME_24_MODES = ("rolling", "atr")


def load_checkpoint(checkpoint_path: str | Path, device: torch.device) -> dict:
    return torch.load(Path(checkpoint_path), map_location=device, weights_only=False)


def load_input_frame(path: str | Path) -> pd.DataFrame:
    return pd.read_csv(Path(path), sep=";", low_memory=False)


def _seq_len_from_checkpoint(checkpoint: dict) -> int:
    return int(checkpoint.get("model_kwargs", {}).get("seq_len", 20))


def _build_entry_path_loader(
    frame: pd.DataFrame,
    *,
    task: str,
    seq_len: int,
    batch_size: int,
    num_workers: int,
    feature_profile: str,
    include_true_targets: bool,
) -> DataLoader:
    X, mask = parse_fractals_to_3d(frame)
    if X.shape[1] > seq_len:
        X = X[:, :seq_len, :]
        mask = mask[:, :seq_len]

    if include_true_targets:
        y_reg, y_cls = split_entry_path_targets(frame)
    else:
        y_reg = np.zeros((len(frame), 9), dtype=np.float32)
        y_cls = np.zeros(len(frame), dtype=np.int64)
    signal = pd.to_numeric(frame["signal"], errors="coerce").fillna(0).astype(int).to_numpy(dtype=np.int64)
    engineered = None
    if task == ENTRY_PATH_TARGET:
        engineered = split_entry_path_features(frame, feature_profile=feature_profile, seq_len=seq_len)

    dataset = EntryPathDataset(X, engineered, y_reg, y_cls, mask, signal)
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=torch.cuda.is_available(),
        drop_last=False,
    )


def export_predictions(
    *,
    input_csv: str | Path,
    checkpoint: str | Path,
    output_csv: str | Path,
    task: str,
    batch_size: int = 256,
    num_workers: int = 0,
    feature_profile: str = ENTRY_PATH_DEFAULT_FEATURE_PROFILE,
    seed: int = 42,
    include_true_targets: bool = True,
    vol_regime_24_mode: str = "rolling",
) -> Path:
    if task not in {ENTRY_PATH_TARGET, ENTRY_PATH_V1_QUANTILE_TARGET}:
        raise ValueError(f"unsupported task: {task}")
    if vol_regime_24_mode not in VOL_REGIME_24_MODES:
        available = ", ".join(VOL_REGIME_24_MODES)
        raise ValueError(f"unsupported vol_regime_24_mode: {vol_regime_24_mode}. Available: {available}")

    set_seed(seed)
    device = get_device()
    checkpoint_payload = load_checkpoint(checkpoint, device)
    frame = add_entry_path_frequency_features(load_input_frame(input_csv))
    if vol_regime_24_mode == "atr":
        frame["vol_regime_24"] = pd.to_numeric(frame["ATR"], errors="coerce").fillna(0.0)
    seq_len = _seq_len_from_checkpoint(checkpoint_payload)
    loader = _build_entry_path_loader(
        frame,
        task=task,
        seq_len=seq_len,
        batch_size=batch_size,
        num_workers=num_workers,
        feature_profile=feature_profile,
        include_true_targets=include_true_targets,
    )

    if task == ENTRY_PATH_TARGET:
        model = build_entry_path_model(
            checkpoint_payload.get("model_name", "transformer"),
            checkpoint_payload.get("model_kwargs", {}),
        )
    else:
        model = build_entry_path_v1_quantile_model(checkpoint_payload.get("model_kwargs", {}))
    model.load_state_dict(checkpoint_payload["model_state_dict"])
    model = model.to(device)
    model.eval()

    all_ret = []
    all_path_reg = []
    all_path_cls = []
    all_q10 = []
    all_q90 = []
    all_true_reg = []
    all_true_cls = []

    with torch.no_grad():
        for batch in loader:
            if task == ENTRY_PATH_TARGET:
                X_batch, engineered_batch, y_reg_batch, y_cls_batch, mask_batch, _signal_batch = batch
                outputs = model(
                    X_batch.to(device),
                    engineered_batch.to(device),
                    mask=mask_batch.to(device),
                )
            else:
                X_batch, y_reg_batch, y_cls_batch, mask_batch, _signal_batch = batch
                outputs = model(
                    X_batch.to(device),
                    mask=mask_batch.to(device),
                )
                all_q10.append(outputs["ret_q10"].cpu().numpy())
                all_q90.append(outputs["ret_q90"].cpu().numpy())

            all_ret.append(outputs["ret"].cpu().numpy())
            all_path_reg.append(outputs["path_reg"].cpu().numpy())
            all_path_cls.append(torch.softmax(outputs["path_cls"], dim=1).cpu().numpy())
            all_true_reg.append(y_reg_batch.numpy())
            all_true_cls.append(y_cls_batch.numpy())

    export_kwargs = {
        "times": frame["time"].values,
        "signals": pd.to_numeric(frame["signal"], errors="coerce").fillna(0).astype(int).values,
        "pred_ret": np.concatenate(all_ret),
        "pred_path_reg": np.concatenate(all_path_reg),
        "pred_path_cls": np.concatenate(all_path_cls),
        "true_reg": np.concatenate(all_true_reg),
        "true_cls": np.concatenate(all_true_cls),
    }
    if not include_true_targets:
        export_kwargs["true_reg"] = None
        export_kwargs["true_cls"] = None

    if task == ENTRY_PATH_TARGET:
        export = build_entry_path_export_frame(**export_kwargs)
    else:
        export = build_entry_path_v1_quantile_export_frame(
            **export_kwargs,
            pred_q10=np.concatenate(all_q10),
            pred_q90=np.concatenate(all_q90),
        )

    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    export.to_csv(output_path, sep=";", index=False)
    return output_path


def parse_args():
    parser = argparse.ArgumentParser(description="Export entry_path predictions for an arbitrary labeled CSV.")
    parser.add_argument("--task", choices=[ENTRY_PATH_TARGET, ENTRY_PATH_V1_QUANTILE_TARGET], required=True)
    parser.add_argument("--input-csv", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--feature-profile", default=ENTRY_PATH_DEFAULT_FEATURE_PROFILE)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--no-true-targets", action="store_true")
    parser.add_argument(
        "--vol-regime-24-mode",
        choices=VOL_REGIME_24_MODES,
        default="rolling",
        help="rolling keeps the training contract; atr uses runtime-compatible vol_regime_24 := ATR.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    path = export_predictions(
        input_csv=args.input_csv,
        checkpoint=args.checkpoint,
        output_csv=args.output,
        task=args.task,
        batch_size=args.batch_size,
        num_workers=args.num_workers,
        feature_profile=args.feature_profile,
        seed=args.seed,
        include_true_targets=not args.no_true_targets,
        vol_regime_24_mode=args.vol_regime_24_mode,
    )
    print(path)
    return path


if __name__ == "__main__":
    main()
