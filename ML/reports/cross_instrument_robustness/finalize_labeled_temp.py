#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd


def _bootstrap_paths() -> Path:
    repo_root = Path(__file__).resolve().parents[3]
    processing_dir = repo_root / "processing"
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    if str(processing_dir) not in sys.path:
        sys.path.insert(0, str(processing_dir))
    return repo_root


REPO_ROOT = _bootstrap_paths()

from processing.normalize import normalize_rowwise  # noqa: E402
from processing.label_main import save_datasets, split_train_val_test  # noqa: E402


def finalize_labeled_temp(*, input_csv: Path, output_base: Path) -> None:
    stats_path = Path(f"{output_base}_normalization_stats.csv")
    frame = pd.read_csv(input_csv, sep=";", low_memory=False)
    print({"loaded_rows": int(len(frame)), "input_csv": str(input_csv)})

    normalized, updn_params = normalize_rowwise(
        frame,
        stats_path=str(stats_path),
        return_updn_params=True,
    )
    train_df, val_df, test_df = split_train_val_test(normalized)
    save_datasets(train_df, val_df, test_df, output_base)

    n_train = len(train_df)
    n_val = len(val_df)
    np.save(f"{output_base}_train_updn_params.npy", updn_params[:n_train])
    np.save(f"{output_base}_validation_updn_params.npy", updn_params[n_train:n_train + n_val])
    np.save(f"{output_base}_test_updn_params.npy", updn_params[n_train + n_val:])
    print(
        {
            "train_rows": int(n_train),
            "validation_rows": int(n_val),
            "test_rows": int(len(test_df)),
            "output_base": str(output_base),
        }
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Finalize *_labeled_temp.csv into normalized train/validation/test splits.")
    parser.add_argument("--input-csv", required=True)
    parser.add_argument("--output-base", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    finalize_labeled_temp(
        input_csv=(REPO_ROOT / args.input_csv).resolve() if not Path(args.input_csv).is_absolute() else Path(args.input_csv),
        output_base=(REPO_ROOT / args.output_base).resolve() if not Path(args.output_base).is_absolute() else Path(args.output_base),
    )


if __name__ == "__main__":
    main()
