#!/usr/bin/env python3
"""
Пересборка top-level up/dn целей в labeled CSV по producer-контракту XAUUSD.

Контракт:
- базовая цена: `fractal0.price`;
- старт окна: следующий OHLC-бар после `fractal0.time`;
- длина окна: следующие H баров по индексу баров, а не по календарным часам;
- метрики: `up_h = max(high - price)`, `dn_h = max(price - low)` внутри окна;
- запись в CSV: только top-level колонки `up_3..dn_48`, нормализованные
  теми же per-row `updn_params`, что уже лежат рядом в `*_updn_params.npy`.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from processing.label_signals import parse_fractal
from processing.normalize import UPDN_PAIRS, piecewise_linear_log_transform


DATA_DIR = PROJECT_ROOT / "DATA"
DEFAULT_OHLC = DATA_DIR / "XAUUSD_H1_OHLC.csv"
DEFAULT_SPLITS = ("train", "validation", "test")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ohlc", type=Path, default=DEFAULT_OHLC)
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    parser.add_argument("--splits", nargs="+", default=list(DEFAULT_SPLITS))
    parser.add_argument("--check-only", action="store_true")
    return parser.parse_args()


def load_ohlc(path: Path) -> pd.DataFrame:
    ohlc = pd.read_csv(path, sep=";", usecols=["time", "high", "low"])
    ohlc["time"] = pd.to_datetime(ohlc["time"], format="%Y.%m.%d %H:%M", errors="coerce")
    ohlc["high"] = pd.to_numeric(ohlc["high"], errors="coerce")
    ohlc["low"] = pd.to_numeric(ohlc["low"], errors="coerce")
    ohlc = ohlc.dropna(subset=["time", "high", "low"]).sort_values("time").drop_duplicates("time")
    return ohlc.reset_index(drop=True)


def reconstruct_raw_targets(frame: pd.DataFrame, ohlc: pd.DataFrame) -> dict[str, np.ndarray]:
    time_to_pos = {timestamp: pos for pos, timestamp in enumerate(ohlc["time"])}
    raw_targets = {
        name: np.zeros(len(frame), dtype=np.float64)
        for pair in UPDN_PAIRS
        for name in pair
    }

    fractal0_values = frame["fractal0"].to_numpy()
    for row_idx, fractal0_value in enumerate(fractal0_values):
        fractal0 = parse_fractal(fractal0_value)
        if fractal0 is None:
            continue
        fractal_time = pd.to_datetime(int(fractal0["time"]), unit="s", errors="coerce")
        start_pos = time_to_pos.get(fractal_time)
        if start_pos is None:
            continue
        price = float(fractal0["price"])
        for up_name, dn_name in UPDN_PAIRS:
            horizon = int(up_name.split("_")[1])
            window = ohlc.iloc[start_pos + 1:start_pos + 1 + horizon]
            if len(window) < horizon:
                continue
            raw_targets[up_name][row_idx] = max(float(window["high"].max()) - price, 0.0)
            raw_targets[dn_name][row_idx] = max(price - float(window["low"].min()), 0.0)
    return raw_targets


def normalize_targets(raw_targets: dict[str, np.ndarray], params: np.ndarray) -> dict[str, np.ndarray]:
    linear_max = 0.85
    tail_strength = 9.0
    eps = 1e-12
    normalized = {}
    for pair_idx, (up_name, dn_name) in enumerate(UPDN_PAIRS):
        up_norm = np.zeros(len(raw_targets[up_name]), dtype=np.float64)
        dn_norm = np.zeros(len(raw_targets[dn_name]), dtype=np.float64)
        for row_idx in range(len(up_norm)):
            brk = float(params[row_idx, pair_idx, 0])
            cap = float(params[row_idx, pair_idx, 1])
            up_norm[row_idx] = piecewise_linear_log_transform(
                np.array([raw_targets[up_name][row_idx]], dtype=np.float64),
                0.0,
                brk,
                cap,
                linear_max,
                tail_strength,
                eps,
            )[0]
            dn_norm[row_idx] = piecewise_linear_log_transform(
                np.array([raw_targets[dn_name][row_idx]], dtype=np.float64),
                0.0,
                brk,
                cap,
                linear_max,
                tail_strength,
                eps,
            )[0]
        normalized[up_name] = up_norm
        normalized[dn_name] = dn_norm
    return normalized


def refresh_top_level_columns(frame: pd.DataFrame, params: np.ndarray, ohlc: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    raw_targets = reconstruct_raw_targets(out, ohlc)
    normalized = normalize_targets(raw_targets, params)
    for column, values in normalized.items():
        out[column] = values
    return out


def split_paths(data_dir: Path, split: str) -> tuple[Path, Path]:
    csv_path = data_dir / f"Nero_XAUUSD_{split}_labeled.csv"
    params_path = data_dir / f"Nero_XAUUSD_{split}_updn_params.npy"
    return csv_path, params_path


def main() -> None:
    args = parse_args()
    ohlc = load_ohlc(args.ohlc)
    target_columns = [name for pair in UPDN_PAIRS for name in pair]

    for split in args.splits:
        csv_path, params_path = split_paths(args.data_dir, split)
        frame = pd.read_csv(csv_path, sep=";")
        params = np.load(params_path)
        rebuilt = refresh_top_level_columns(frame, params, ohlc)

        changed_columns = [col for col in rebuilt.columns if not frame[col].equals(rebuilt[col])]
        print(f"{split}: changed_columns={changed_columns}")

        unexpected = [col for col in changed_columns if col not in target_columns]
        if unexpected:
            raise RuntimeError(f"{split}: unexpected changed columns: {unexpected}")

        if not args.check_only:
            rebuilt.to_csv(csv_path, sep=";", index=False)


if __name__ == "__main__":
    main()
