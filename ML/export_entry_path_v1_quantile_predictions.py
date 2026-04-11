import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from ML.data_loader import (
    CSV_SEP,
    TEST_FILE,
    TRAIN_FILE,
    VAL_FILE,
    create_data_loaders,
    create_test_loader,
)
from ML.entry_path_task import ENTRY_PATH_TARGET
from ML.entry_path_v1_quantile_task import (
    ENTRY_PATH_V1_QUANTILE_TARGET,
    build_entry_path_v1_quantile_export_frame,
    build_entry_path_v1_quantile_model,
    count_crossed_quantile_rows,
)
from ML.utils import get_device, set_seed


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHECKPOINTS_DIR = PROJECT_ROOT / 'ML' / 'checkpoints'
REPORTS_DIR = PROJECT_ROOT / 'ML' / 'reports'

DEFAULT_SPLITS = ['train', 'validation', 'test']


def load_checkpoint(checkpoint_path: str | Path, device: torch.device) -> dict:
    return torch.load(Path(checkpoint_path), map_location=device, weights_only=False)


def build_ordered_loader(loader, batch_size: int, num_workers: int):
    dataset = loader.dataset
    return torch.utils.data.DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=torch.cuda.is_available(),
        drop_last=False,
    )


@torch.no_grad()
def export_split(
    model: torch.nn.Module,
    loader,
    frame: pd.DataFrame,
    output_path: Path,
    device: torch.device,
):
    all_ret = []
    all_path_reg = []
    all_path_cls = []
    all_q10 = []
    all_q90 = []
    all_true_reg = []
    all_true_cls = []
    all_times = []
    all_signals = []

    for batch in loader:
        X_batch, y_reg_batch, y_cls_batch, mask_batch, signal_batch = batch
        outputs = model(X_batch.to(device), mask=mask_batch.to(device))
        all_ret.append(outputs['ret'].cpu().numpy())
        all_path_reg.append(outputs['path_reg'].cpu().numpy())
        all_path_cls.append(torch.softmax(outputs['path_cls'], dim=1).cpu().numpy())
        all_q10.append(outputs['ret_q10'].cpu().numpy())
        all_q90.append(outputs['ret_q90'].cpu().numpy())
        all_true_reg.append(y_reg_batch.numpy())
        all_true_cls.append(y_cls_batch.numpy())
        all_signals.append(signal_batch.numpy())

    pred_ret = np.concatenate(all_ret)
    pred_path_reg = np.concatenate(all_path_reg)
    pred_path_cls = np.concatenate(all_path_cls)
    pred_q10 = np.concatenate(all_q10)
    pred_q90 = np.concatenate(all_q90)
    true_reg = np.concatenate(all_true_reg)
    true_cls = np.concatenate(all_true_cls)
    signals = np.concatenate(all_signals)

    export = build_entry_path_v1_quantile_export_frame(
        times=frame['time'].values,
        signals=signals.astype(int),
        pred_ret=pred_ret,
        pred_path_reg=pred_path_reg,
        pred_path_cls=pred_path_cls,
        pred_q10=pred_q10,
        pred_q90=pred_q90,
        true_reg=true_reg,
        true_cls=true_cls,
    )
    export.to_csv(output_path, sep=';', index=False)
    crossed_quantile_rows = count_crossed_quantile_rows(export)
    return export, crossed_quantile_rows


def export_predictions(
    checkpoint: str | Path,
    output_dir: str | Path = REPORTS_DIR,
    batch_size: int = 256,
    num_workers: int = 0,
    clear_cache: bool = False,
    splits: list[str] | None = None,
    seed: int = 42,
) -> dict[str, dict[str, object]]:
    set_seed(seed)
    device = get_device()
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    checkpoint_path = Path(checkpoint)

    ckpt = load_checkpoint(checkpoint_path, device)
    model = build_entry_path_v1_quantile_model(ckpt.get('model_kwargs', {}))
    model.load_state_dict(ckpt['model_state_dict'])
    model = model.to(device)
    model.eval()

    requested_splits = splits or DEFAULT_SPLITS
    seq_len = ckpt.get('model_kwargs', {}).get('seq_len', 20)
    split_loaders: dict[str, object] = {}
    split_frames: dict[str, pd.DataFrame] = {}

    if 'train' in requested_splits or 'validation' in requested_splits:
        train_loader, val_loader, _ = create_data_loaders(
            batch_size=batch_size,
            target=ENTRY_PATH_TARGET,
            use_scaler=False,
            seq_len=seq_len,
            clear_cache=clear_cache,
            num_workers=num_workers,
        )
        if 'train' in requested_splits:
            split_loaders['train'] = build_ordered_loader(train_loader, batch_size=batch_size, num_workers=num_workers)
            split_frames['train'] = pd.read_csv(TRAIN_FILE, sep=CSV_SEP, low_memory=False)
        if 'validation' in requested_splits:
            split_loaders['validation'] = build_ordered_loader(val_loader, batch_size=batch_size, num_workers=num_workers)
            split_frames['validation'] = pd.read_csv(VAL_FILE, sep=CSV_SEP, low_memory=False)

    if 'test' in requested_splits:
        split_loaders['test'] = create_test_loader(
            batch_size=batch_size,
            target=ENTRY_PATH_V1_QUANTILE_TARGET,
            seq_len=seq_len,
            clear_cache=clear_cache,
            num_workers=num_workers,
        )
        split_frames['test'] = pd.read_csv(TEST_FILE, sep=CSV_SEP, low_memory=False)

    results: dict[str, dict[str, object]] = {}
    for split in requested_splits:
        export_path = output_path / f'entry_path_v1_quantile_{split}_predictions.csv'
        export, crossed_quantile_rows = export_split(
            model=model,
            loader=split_loaders[split],
            frame=split_frames[split],
            output_path=export_path,
            device=device,
        )
        if crossed_quantile_rows > 0:
            print(f"  ⚠ {split}: crossed_quantile_rows={crossed_quantile_rows}")
        results[split] = {
            'path': str(export_path),
            'row_count': int(len(export)),
            'crossed_quantile_rows': int(crossed_quantile_rows),
        }

    return results


def parse_args():
    parser = argparse.ArgumentParser(description='Export entry_path_v1_quantile predictions for train/validation/test.')
    parser.add_argument('--checkpoint', required=True)
    parser.add_argument('--output-dir', default=str(REPORTS_DIR))
    parser.add_argument('--batch-size', type=int, default=256)
    parser.add_argument('--num-workers', type=int, default=0)
    parser.add_argument('--clear-cache', action='store_true')
    parser.add_argument('--splits', nargs='+', choices=DEFAULT_SPLITS, default=DEFAULT_SPLITS)
    parser.add_argument('--seed', type=int, default=42)
    return parser.parse_args()


def main():
    args = parse_args()
    payload = export_predictions(
        checkpoint=args.checkpoint,
        output_dir=args.output_dir,
        batch_size=args.batch_size,
        num_workers=args.num_workers,
        clear_cache=args.clear_cache,
        splits=args.splits,
        seed=args.seed,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return payload


if __name__ == '__main__':
    main()
