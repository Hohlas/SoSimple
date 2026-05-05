"""
Aggregate quantile predictions from multiple seed checkpoints.

Two modes:
- mean_quantile: average pred_ret_24_q10/q90 across seeds, keep other columns from first frame.
- majority_vote: signal passes only if >= quorum seeds select it.
"""
from pathlib import Path

import pandas as pd


QUANTILE_COLUMNS = ['pred_ret_24_q10', 'pred_ret_24_q90']


def load_seed_predictions(seed_dir: str | Path, split: str = 'test') -> pd.DataFrame:
    path = Path(seed_dir) / f'entry_path_v1_quantile_{split}_predictions.csv'
    return pd.read_csv(path, sep=';')


def aggregate_mean_quantile(frames: list[pd.DataFrame]) -> pd.DataFrame:
    base = frames[0].copy()
    for col in QUANTILE_COLUMNS:
        stacked = pd.concat([f[col] for f in frames], axis=1)
        base[col] = stacked.mean(axis=1)
    return base


def majority_vote(masks: list[pd.Series], quorum: int = 3) -> pd.Series:
    stacked = pd.concat(masks, axis=1)
    return stacked.sum(axis=1) >= quorum
