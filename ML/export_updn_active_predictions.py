import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader

from ML.data_loader import FractalSequenceDataset, UPDN_TARGETS
from ML.models import get_model
from ML.utils import get_device


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / 'DATA'
if PROJECT_ROOT.parent.name == '.worktrees':
    MAIN_TREE_ROOT = PROJECT_ROOT.parent.parent
else:
    MAIN_TREE_ROOT = PROJECT_ROOT
CANONICAL_DATA_DIR = MAIN_TREE_ROOT / 'DATA'
CHECKPOINTS_DIR = PROJECT_ROOT / 'ML' / 'checkpoints'
DEFAULT_CHECKPOINT = CHECKPOINTS_DIR / 'transformer_updn_best.pt'
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / 'ML' / 'reports' / 'quantile_fav_composition' / 'updn_active_source'


def _data_path(name: str) -> Path:
    local = DATA_DIR / name
    if local.exists():
        return local
    canonical = CANONICAL_DATA_DIR / name
    return canonical


def _split_artifacts(split: str) -> tuple[Path, Path, Path, Path]:
    if split == 'validation':
        return (
            _data_path('X_val.npy'),
            _data_path('mask_val.npy'),
            _data_path('y_val_updn.npy'),
            _data_path('Nero_validation_labeled.csv'),
        )
    if split == 'test':
        return (
            _data_path('X_test.npy'),
            _data_path('mask_test.npy'),
            _data_path('y_test_updn.npy'),
            _data_path('Nero_test_labeled.csv'),
        )
    raise ValueError(f'Unsupported split: {split}')


def _load_active_split(split: str) -> tuple[np.ndarray, np.ndarray, np.ndarray, pd.DataFrame]:
    x_path, mask_path, y_path, csv_path = _split_artifacts(split)
    X = np.load(x_path)
    mask = np.load(mask_path)
    y = np.load(y_path)
    meta = pd.read_csv(csv_path, sep=';', usecols=['time', 'signal'], low_memory=False)
    active_idx = np.flatnonzero(meta['signal'].to_numpy() != 0)
    return X[active_idx], mask[active_idx], y[active_idx], meta.iloc[active_idx].reset_index(drop=True)


def _infer(model: torch.nn.Module, device: torch.device, X: np.ndarray, y: np.ndarray, mask: np.ndarray) -> np.ndarray:
    ds = FractalSequenceDataset(X, y, mask, regression=True)
    loader = DataLoader(ds, batch_size=256, shuffle=False, num_workers=0)
    outs = []
    with torch.no_grad():
        for xb, _yb, mb in loader:
            pred = model(xb.to(device), mask=mb.to(device)).cpu().numpy()
            outs.append(pred)
    return np.concatenate(outs)


def export_updn_active_predictions(
    checkpoint_path: str | Path = DEFAULT_CHECKPOINT,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> dict[str, str]:
    checkpoint_path = Path(checkpoint_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    device = get_device()
    ckpt = torch.load(checkpoint_path, map_location=device, weights_only=False)
    model = get_model(
        ckpt.get('model_name', 'transformer'),
        num_classes=ckpt.get('num_classes', 1),
        **ckpt.get('model_kwargs', {}),
    )
    model.load_state_dict(ckpt['model_state_dict'])
    model = model.to(device)
    model.eval()

    payload = {}
    for split in ['validation', 'test']:
        X, mask, y, meta = _load_active_split(split)
        pred = _infer(model, device, X, y, mask)
        frame = pd.DataFrame({
            'time': meta['time'].values,
            'signal': meta['signal'].astype(int).values,
        })
        for i, name in enumerate(UPDN_TARGETS):
            frame[name] = pred[:, i]
        frame['pred_fav_3'] = np.where(frame['signal'].to_numpy() == 1, frame['up_3'], frame['dn_3'])
        frame['pred_fav_12'] = np.where(frame['signal'].to_numpy() == 1, frame['up_12'], frame['dn_12'])
        frame['fav_3_vs_12'] = frame['pred_fav_3'] / np.clip(frame['pred_fav_12'], 1e-6, None)
        out_path = output_dir / f'{split}_active_updn_predictions.csv'
        frame.to_csv(out_path, sep=';', index=False)
        payload[split] = str(out_path)

    metadata = {
        'checkpoint_path': str(checkpoint_path),
        'output_dir': str(output_dir),
        'files': payload,
    }
    (output_dir / 'metadata.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')
    return payload


def parse_args():
    parser = argparse.ArgumentParser(description='Export active-only updn predictions for composition research.')
    parser.add_argument('--checkpoint', default=str(DEFAULT_CHECKPOINT))
    parser.add_argument('--output-dir', default=str(DEFAULT_OUTPUT_DIR))
    return parser.parse_args()


def main():
    args = parse_args()
    payload = export_updn_active_predictions(
        checkpoint_path=args.checkpoint,
        output_dir=args.output_dir,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return payload


if __name__ == '__main__':
    main()
