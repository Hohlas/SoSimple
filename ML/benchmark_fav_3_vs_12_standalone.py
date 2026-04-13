from __future__ import annotations

import math

import pandas as pd


EPS = 1e-6


def add_fav_ratio(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    denom = result["pred_fav_12"].clip(lower=EPS)
    result["fav_3_vs_12"] = result["pred_fav_3"] / denom
    return result


def compute_metrics(frame: pd.DataFrame) -> dict[str, float | int | None]:
    n_trades = int(len(frame))
    if n_trades == 0:
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

    pnl = frame["pnl_atr"].astype(float)
    wins = int((pnl > 0).sum())
    losses = int((pnl < 0).sum())
    gross_profit = float(pnl[pnl > 0].sum())
    gross_loss = float(-pnl[pnl < 0].sum())
    if gross_loss == 0.0:
        pf = math.inf if gross_profit > 0.0 else 0.0
    else:
        pf = gross_profit / gross_loss

    return {
        "n_trades": n_trades,
        "wins": wins,
        "losses": losses,
        "gross_profit": gross_profit,
        "gross_loss": gross_loss,
        "pf": pf,
        "win_rate": wins / n_trades,
        "mean_pnl_atr": float(pnl.mean()),
    }
