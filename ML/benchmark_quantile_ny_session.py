from __future__ import annotations

import math
from typing import Any

import pandas as pd


GATE_MIN_TRADES = 30
GATE_MIN_PF = 2.0
GATE_MIN_SEED_PF = 1.0


def assign_session_bucket(hour: int) -> str:
    hour = int(hour)
    if hour < 0 or hour > 23:
        raise ValueError(f"hour must be in [0, 23], got {hour}")
    if 0 <= hour <= 6:
        return "asia"
    if 7 <= hour <= 12:
        return "london"
    if 13 <= hour <= 18:
        return "overlap"
    return "ny"


def _compute_pf(values: pd.Series) -> float | None:
    gains = float(values[values > 0].sum())
    losses = float(-values[values < 0].sum())
    if gains == 0.0 and losses == 0.0:
        return None
    if losses == 0.0:
        return math.inf
    return gains / losses


def count_negative_year_slices(frame: pd.DataFrame, pnl_column: str) -> int:
    negative_years = 0
    for _, yearly in frame.groupby("year"):
        if len(yearly) < 3:
            continue
        pf = _compute_pf(pd.to_numeric(yearly[pnl_column], errors="raise"))
        if pf is not None and pf < 1.0:
            negative_years += 1
    return negative_years


def decide_session_gate(
    *,
    baseline_pf: float | None,
    filtered_pf: float | None,
    filtered_n_trades: int,
    filtered_negative_year_slices: int,
    seed_pf_values: list[float],
) -> dict[str, Any]:
    reasons: list[str] = []
    if baseline_pf is not None and not math.isfinite(float(baseline_pf)):
        reasons.append(f"baseline_pf={baseline_pf} is not finite")
    if filtered_pf is not None and not math.isfinite(float(filtered_pf)):
        reasons.append(f"filtered_pf={filtered_pf} is not finite")
    if filtered_n_trades < GATE_MIN_TRADES:
        reasons.append(f"filtered_n_trades={filtered_n_trades} < {GATE_MIN_TRADES}")
    if filtered_pf is None or filtered_pf <= GATE_MIN_PF:
        reasons.append(f"filtered_pf={filtered_pf} <= {GATE_MIN_PF}")
    if baseline_pf is not None and filtered_pf is not None and filtered_pf < baseline_pf:
        reasons.append(f"filtered_pf={filtered_pf:.4f} < baseline_pf={baseline_pf:.4f}")
    if filtered_negative_year_slices > 0:
        reasons.append(f"filtered_negative_year_slices={filtered_negative_year_slices} > 0")

    invalid_seed_pfs = [value for value in seed_pf_values if not math.isfinite(float(value))]
    if invalid_seed_pfs:
        reasons.append(f"seed_pf_values_contain_non_finite: {invalid_seed_pfs}")
    weak_seed_pfs = [value for value in seed_pf_values if math.isfinite(float(value)) and value <= GATE_MIN_SEED_PF]
    if weak_seed_pfs:
        reasons.append(f"seed_pf_values_contain_pf<=1.0: {weak_seed_pfs}")

    return {
        "verdict": "gate_pass" if not reasons else "gate_fail",
        "reasons": reasons,
    }
