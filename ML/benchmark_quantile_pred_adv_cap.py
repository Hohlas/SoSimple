from __future__ import annotations

import math
from typing import Any

import pandas as pd


ADV_COLUMN = "pred_adv_12_atr"
GATE_MIN_TRADES = 30
GATE_MIN_PF = 2.0
GATE_MIN_SEED_PF = 1.0


def _require_adv_column(frame: pd.DataFrame) -> pd.Series:
    if ADV_COLUMN not in frame.columns:
        raise ValueError(f"missing columns: ['{ADV_COLUMN}']")
    return pd.to_numeric(frame[ADV_COLUMN], errors="raise")


def _is_finite_number(value: Any) -> bool:
    if pd.isna(value):
        return False
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def _require_finite_series(series: pd.Series) -> pd.Series:
    if series.isna().any():
        raise ValueError(f"{ADV_COLUMN} contains null/NaN/non-finite values")
    values = series.to_numpy(dtype="float64", copy=False)
    if not pd.Series(values).map(_is_finite_number).all():
        raise ValueError(f"{ADV_COLUMN} contains null/NaN/non-finite values")
    return series.astype(float)


def compute_adv_threshold(frame: pd.DataFrame, quantile: float = 0.75) -> float:
    values = _require_finite_series(_require_adv_column(frame))
    threshold = float(values.quantile(quantile))
    if not math.isfinite(threshold):
        raise ValueError(f"{ADV_COLUMN} contains null/NaN/non-finite values")
    return threshold


def filter_by_adv_cap(frame: pd.DataFrame, threshold: float) -> pd.DataFrame:
    if not _is_finite_number(threshold):
        raise ValueError("threshold must be a finite number")
    values = _require_finite_series(_require_adv_column(frame))
    return frame.loc[values <= float(threshold)].copy()


def decide_adv_cap_gate(
    *,
    baseline_pf: float | None,
    filtered_pf: float | None,
    filtered_n_trades: int,
    filtered_negative_year_slices: int,
    seed_pf_values: list[float],
) -> dict[str, Any]:
    reasons: list[str] = []

    if baseline_pf is None:
        reasons.append("baseline_pf=None")
    elif not _is_finite_number(baseline_pf):
        reasons.append(f"baseline_pf={baseline_pf} is not finite")

    if filtered_pf is None:
        reasons.append("filtered_pf=None")
    elif not _is_finite_number(filtered_pf):
        reasons.append(f"filtered_pf={filtered_pf} is not finite")
    elif filtered_pf <= GATE_MIN_PF:
        reasons.append(f"filtered_pf={filtered_pf:.4f} <= {GATE_MIN_PF}")

    if not _is_finite_number(filtered_n_trades):
        reasons.append(f"filtered_n_trades={filtered_n_trades} is not finite")
    elif int(filtered_n_trades) != float(filtered_n_trades):
        reasons.append(f"filtered_n_trades={filtered_n_trades} is not an integer")
    elif filtered_n_trades < GATE_MIN_TRADES:
        reasons.append(f"filtered_n_trades={filtered_n_trades} < {GATE_MIN_TRADES}")

    if (
        _is_finite_number(baseline_pf)
        and _is_finite_number(filtered_pf)
        and filtered_pf < baseline_pf
    ):
        reasons.append(f"filtered_pf={filtered_pf:.4f} < baseline_pf={baseline_pf:.4f}")

    if not _is_finite_number(filtered_negative_year_slices):
        reasons.append(
            f"filtered_negative_year_slices={filtered_negative_year_slices} is not finite"
        )
    elif int(filtered_negative_year_slices) != float(filtered_negative_year_slices):
        reasons.append(
            f"filtered_negative_year_slices={filtered_negative_year_slices} is not an integer"
        )
    elif filtered_negative_year_slices > 0:
        reasons.append(f"filtered_negative_year_slices={filtered_negative_year_slices} > 0")

    invalid_seed_pfs = [
        value for value in seed_pf_values
        if not _is_finite_number(value)
    ]
    if invalid_seed_pfs:
        reasons.append(f"seed_pf_values_contain_non_finite: {invalid_seed_pfs}")

    weak_seed_pfs = [
        value for value in seed_pf_values
        if _is_finite_number(value) and float(value) <= GATE_MIN_SEED_PF
    ]
    if weak_seed_pfs:
        reasons.append(f"seed_pf_values_contain_pf<=1.0: {weak_seed_pfs}")

    return {
        "verdict": "gate_pass" if not reasons else "gate_fail",
        "reasons": reasons,
    }
