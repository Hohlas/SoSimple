from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "DATA"
REPORTS_DIR = ROOT / "ML" / "reports"
OHLC_FILE = ROOT / "MT" / "MQL4" / "Files" / "Nero.csv"
STAGE6_0_JSON_REPORT_PATH = REPORTS_DIR / "stage6_0_outcome_based_triple_barrier.json"


@dataclass(frozen=True)
class Stage60Config:
    horizon_bars: int = 24
    stop_offset_atr: float = 0.5
    take_profit_atr: float = 2.0
    entry_lag_bars: int = 1
    same_bar_policy: str = "sl_first"
    primary_profile: str = "clock_shift_back"
    disclosure_profiles: tuple[str, ...] = ("clock_shift_back_impulse",)
    seeds: tuple[int, ...] = (42, 77, 123)


STAGE6_0_CONFIG = Stage60Config()


def stage6_target_columns() -> tuple[str, ...]:
    return (
        "stage6_side",
        "stage6_entry_time",
        "stage6_entry_price",
        "stage6_stop_price",
        "stage6_take_price",
        "stage6_close_reason",
        "stage6_invalid_reason",
        "stage6_bars_held",
        "stage6_pnl_r",
        "stage6_pnl_r_spread_020",
        "stage6_pnl_r_spread_040",
        "stage6_risk_atr",
        "stage6_reward_risk",
        "stage6_tp_vs_rest_flag",
        "stage6_definitive_tp_vs_sl_flag",
    )


def stage6_feature_denylist() -> tuple[str, ...]:
    return stage6_target_columns()


def stage6_first_touch_trade_result(entry_price: float, stop_price: float,
                                    take_price: float, side: str,
                                    future_bars: list[dict],
                                    timeout_close: float | None = None) -> dict:
    if side not in {"buy", "sell"}:
        raise ValueError(f"side must be buy or sell, got {side}")
    risk = abs(entry_price - stop_price)
    reward = abs(take_price - entry_price)
    if risk <= 0.0:
        return {"close_reason": "INVALID", "bars_held": 0, "pnl_r": np.nan}

    for idx, bar in enumerate(future_bars, start=1):
        high = float(bar["high"])
        low = float(bar["low"])
        close = float(bar["close"])
        if side == "buy":
            sl_hit = low <= stop_price
            tp_hit = high >= take_price
        else:
            sl_hit = high >= stop_price
            tp_hit = low <= take_price
        if sl_hit and tp_hit:
            return {"close_reason": "AMBIGUOUS_SL_FIRST", "bars_held": idx, "pnl_r": -1.0}
        if sl_hit:
            return {"close_reason": "SL", "bars_held": idx, "pnl_r": -1.0}
        if tp_hit:
            return {"close_reason": "TP", "bars_held": idx, "pnl_r": float(reward / risk)}

    if not future_bars:
        return {"close_reason": "INVALID", "bars_held": 0, "pnl_r": np.nan}
    close = float(timeout_close if timeout_close is not None else future_bars[-1]["close"])
    if side == "buy":
        pnl_r = (close - entry_price) / risk
    else:
        pnl_r = (entry_price - close) / risk
    return {"close_reason": "TIMEOUT", "bars_held": len(future_bars), "pnl_r": float(pnl_r)}
