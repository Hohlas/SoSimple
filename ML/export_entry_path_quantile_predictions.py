import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from ML.data_loader import (
    CSV_SEP,
    TEST_FILE,
    TRAIN_FILE,
    VAL_FILE,
    create_split_loader,
    create_test_loader,
)
from ML.entry_path_quantile_task import (
    ENTRY_PATH_QUANTILE_TARGET,
    attach_quantile_context_columns,
    build_entry_path_quantile_export_frame,
)
from ML.evaluate_test import build_entry_path_quantile_model
from ML.utils import get_device, set_seed


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHECKPOINTS_DIR = PROJECT_ROOT / 'ML' / 'checkpoints'
REPORTS_DIR = PROJECT_ROOT / 'ML' / 'reports'


def export_split(
    split: str,
    model: torch.nn.Module,
    device: torch.device,
    seq_len: int,
) -> Path:
    if split == 'train':
        loader = create_split_loader(
            split='train',
            target=ENTRY_PATH_QUANTILE_TARGET,
            batch_size=256,
            seq_len=seq_len,
            num_workers=0,
            shuffle_train=False,
        )
        source = pd.read_csv(TRAIN_FILE, sep=CSV_SEP, low_memory=False)
        export_name = 'entry_path_quantile_train_predictions.csv'
    elif split == 'validation':
        loader = create_split_loader(
            split='validation',
            target=ENTRY_PATH_QUANTILE_TARGET,
            batch_size=256,
            seq_len=seq_len,
            num_workers=0,
        )
        source = pd.read_csv(VAL_FILE, sep=CSV_SEP, low_memory=False)
        export_name = 'entry_path_quantile_validation_predictions.csv'
    elif split == 'test':
        loader = create_test_loader(
            batch_size=256,
            target=ENTRY_PATH_QUANTILE_TARGET,
            seq_len=seq_len,
            num_workers=0,
        )
        source = pd.read_csv(TEST_FILE, sep=CSV_SEP, low_memory=False)
        export_name = 'entry_path_quantile_test_predictions.csv'
    else:
        raise ValueError("split must be 'train', 'validation', or 'test'")

    all_point = []
    all_q10 = []
    all_q90 = []
    all_true = []

    model.eval()
    with torch.no_grad():
        for X_batch, y_batch, mask_batch in loader:
            outputs = model(X_batch.to(device), mask=mask_batch.to(device))
            all_point.append(outputs['ret_point'].cpu().numpy())
            all_q10.append(outputs['ret_q10'].cpu().numpy())
            all_q90.append(outputs['ret_q90'].cpu().numpy())
            all_true.append(y_batch.numpy())

    export = build_entry_path_quantile_export_frame(
        times=source['time'].values,
        signals=source['signal'].values.astype(int),
        pred_point=np.concatenate(all_point).reshape(-1),
        pred_q10=np.concatenate(all_q10).reshape(-1),
        pred_q90=np.concatenate(all_q90).reshape(-1),
        true_ret=np.concatenate(all_true).reshape(-1) if 'ret_24_dir_atr' in source.columns else None,
    )
    export = attach_quantile_context_columns(export, source[['time', 'ATR']])
    export_path = REPORTS_DIR / export_name
    export.to_csv(export_path, sep=';', index=False)
    return export_path


def main():
    parser = argparse.ArgumentParser(description='Export entry_path_quantile_v1 predictions for train/validation/test.')
    parser.add_argument(
        '--checkpoint',
        type=str,
        default=str(CHECKPOINTS_DIR / 'transformer_entry_path_quantile_v1_best.pt'),
        help='Path to the quantile checkpoint.',
    )
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()

    set_seed(args.seed)
    device = get_device()
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    ckpt_path = Path(args.checkpoint)
    if not ckpt_path.exists():
        raise FileNotFoundError(f'Checkpoint not found: {ckpt_path}')

    ckpt = torch.load(ckpt_path, map_location=device, weights_only=False)
    model = build_entry_path_quantile_model(ckpt.get('model_kwargs', {}))
    model.load_state_dict(ckpt['model_state_dict'])
    model = model.to(device)
    seq_len = ckpt.get('model_kwargs', {}).get('seq_len', 20)

    for split in ('train', 'validation', 'test'):
        export_path = export_split(split=split, model=model, device=device, seq_len=seq_len)
        print(f'✅ {split}: {export_path.name}')


if __name__ == '__main__':
    main()
