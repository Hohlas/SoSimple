from __future__ import annotations

import math
from typing import Any

import pandas as pd


GATE_MIN_TRADES = 30
GATE_MIN_PF = 2.0
GATE_MAX_NEGATIVE_YEAR_SLICES = 0
GATE_MIN_SEED_PF = 1.0


def _format_invalid_numeric_reason(name: str, value: float | None) -> str:
    return f"{name}={value} is invalid"


def _is_nan_value(value: Any) -> bool:
    return value is not None and pd.isna(value)


def compute_metrics(frame: pd.DataFrame, pnl_column: str) -> dict[str, Any]:
    raw_pnl = frame[pnl_column]
    if raw_pnl.isna().any():
        raise ValueError(f"{pnl_column} contains null/NaN pnl values")

    pnl = pd.to_numeric(raw_pnl, errors="raise").astype(float)
    if pd.isna(pnl).any():
        raise ValueError(f"{pnl_column} contains null/NaN pnl values")

    n_trades = int(len(pnl))
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


def decide_hold12_gate(
    *,
    hold24_pf: float | None,
    hold12_pf: float | None,
    hold24_mean_pnl_atr: float | None = None,
    hold12_mean_pnl_atr: float | None = None,
    mean_pnl_tolerance_atr: float = 0.0,
    hold12_n_trades: int,
    hold12_negative_year_slices: int,
    seed_pf_values: list[float],
) -> dict[str, Any]:
    reasons: list[str] = []
    hold12_pf_is_nan = _is_nan_value(hold12_pf)
    hold24_pf_is_nan = _is_nan_value(hold24_pf)
    hold24_mean_pnl_atr_is_nan = _is_nan_value(hold24_mean_pnl_atr)
    hold12_mean_pnl_atr_is_nan = _is_nan_value(hold12_mean_pnl_atr)
    mean_pnl_tolerance_atr_is_nan = _is_nan_value(mean_pnl_tolerance_atr)

    if hold12_n_trades < GATE_MIN_TRADES:
        reasons.append(f"hold12_n_trades={hold12_n_trades} < {GATE_MIN_TRADES}")

    if hold12_pf is None:
        hold12_pf_text = "None" if hold12_pf is None else f"{hold12_pf:.4f}"
        reasons.append(f"hold12_pf={hold12_pf_text} <= {GATE_MIN_PF}")
    elif hold12_pf_is_nan:
        reasons.append(_format_invalid_numeric_reason("hold12_pf", hold12_pf))
    elif hold12_pf <= GATE_MIN_PF:
        reasons.append(f"hold12_pf={hold12_pf:.4f} <= {GATE_MIN_PF}")

    if hold24_pf_is_nan:
        reasons.append(_format_invalid_numeric_reason("hold24_pf", hold24_pf))
    elif hold24_pf is not None and hold12_pf is not None and not hold12_pf_is_nan and hold12_pf < hold24_pf:
        reasons.append(f"hold12_pf={hold12_pf:.4f} < hold24_pf={hold24_pf:.4f}")

    if (
        hold24_mean_pnl_atr is not None
        and hold12_mean_pnl_atr is not None
        and mean_pnl_tolerance_atr_is_nan
    ):
        reasons.append(_format_invalid_numeric_reason("mean_pnl_tolerance_atr", mean_pnl_tolerance_atr))
    elif hold24_mean_pnl_atr_is_nan:
        reasons.append(_format_invalid_numeric_reason("hold24_mean_pnl_atr", hold24_mean_pnl_atr))
    elif hold12_mean_pnl_atr_is_nan:
        reasons.append(_format_invalid_numeric_reason("hold12_mean_pnl_atr", hold12_mean_pnl_atr))
    if (
        hold24_mean_pnl_atr is not None
        and hold12_mean_pnl_atr is not None
        and not hold24_mean_pnl_atr_is_nan
        and not hold12_mean_pnl_atr_is_nan
        and not mean_pnl_tolerance_atr_is_nan
        and hold12_mean_pnl_atr < hold24_mean_pnl_atr - mean_pnl_tolerance_atr
    ):
        reasons.append(
            "hold12_mean_pnl_atr="
            f"{hold12_mean_pnl_atr:.4f} < hold24_mean_pnl_atr={hold24_mean_pnl_atr:.4f}"
        )

    if hold12_negative_year_slices > GATE_MAX_NEGATIVE_YEAR_SLICES:
        reasons.append(
            "hold12_negative_year_slices="
            f"{hold12_negative_year_slices} > {GATE_MAX_NEGATIVE_YEAR_SLICES}"
        )

    seed_pf_nan_values = [value for value in seed_pf_values if _is_nan_value(value)]
    if seed_pf_nan_values:
        reasons.append(f"seed_pf_values_contain_invalid_numeric_values: {seed_pf_nan_values}")

    weak_seed_values = [value for value in seed_pf_values if value <= GATE_MIN_SEED_PF]
    if weak_seed_values:
        reasons.append(f"seed_pf_values_contain_pf<=1.0: {weak_seed_values}")

    return {
        "verdict": "gate_pass" if not reasons else "gate_fail",
        "reasons": reasons,
    }
