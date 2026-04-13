from __future__ import annotations

import math
from typing import Any

import pandas as pd


def compute_forward_metrics(frame: pd.DataFrame) -> dict[str, Any]:
    trades = int(len(frame))
    if trades == 0:
        return {
            "n_trades": 0,
            "wins": 0,
            "losses": 0,
            "gross_profit": 0.0,
            "gross_loss": 0.0,
            "pf": None,
            "win_rate": None,
            "mean_pnl_atr": None,
        }

    pnl = frame["true_ret_24_dir_atr"].astype(float)
    wins = int((pnl > 0).sum())
    losses = int((pnl < 0).sum())
    gross_profit = float(pnl[pnl > 0].sum())
    gross_loss = float(-pnl[pnl < 0].sum())
    pf = math.inf if gross_loss == 0.0 and gross_profit > 0.0 else gross_profit / gross_loss if gross_loss > 0.0 else 0.0
    return {
        "n_trades": trades,
        "wins": wins,
        "losses": losses,
        "gross_profit": gross_profit,
        "gross_loss": gross_loss,
        "pf": pf,
        "win_rate": wins / trades,
        "mean_pnl_atr": float(pnl.mean()),
    }


def build_time_slices(frame: pd.DataFrame, mode: str = "quarter") -> pd.DataFrame:
    working = frame.copy()
    dt = pd.to_datetime(working["time"])
    if mode != "quarter":
        raise ValueError(f"unsupported slice mode: {mode}")
    working["slice"] = dt.dt.to_period("Q").astype(str).str.replace("Q", "-Q", n=1)

    rows: list[dict[str, Any]] = []
    for key, group in working.groupby("slice", sort=True):
        rows.append({"slice": key, **compute_forward_metrics(group)})
    return pd.DataFrame(rows)


def decide_operational_verdict(
    *,
    historical_pf: float,
    forward_pf: float | None,
    n_trades: int,
    negative_slices: int,
) -> dict[str, Any]:
    if forward_pf is None or n_trades < 10:
        return {"verdict": "watch", "reason": "low_support"}
    if forward_pf < 1.0:
        return {"verdict": "revisit", "reason": "pf_below_1"}
    if forward_pf < historical_pf * 0.5:
        return {"verdict": "watch", "reason": "pf_drawdown"}
    if negative_slices > 1:
        return {"verdict": "watch", "reason": "weak_time_slices"}
    return {"verdict": "confirmed", "reason": "forward_pf_holds"}
