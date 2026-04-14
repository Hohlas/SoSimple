from __future__ import annotations

import math
from typing import Any

import pandas as pd

from ML.benchmark_entry_path_v1_quantile_filter import (
    apply_conformal_correction,
    attach_baseline_score,
    build_rule_mask,
)


GATE_MIN_TRADES = 30
GATE_MIN_PF = 2.0
GATE_MAX_NEGATIVE_YEAR_SLICES = 0
GATE_MIN_SEED_PF = 1.0


def select_quantile_trades(
    frame: pd.DataFrame,
    baseline_frame: pd.DataFrame,
    selected_rule: dict[str, Any],
) -> pd.DataFrame:
    required_columns = {
        "time",
        "signal",
        "pred_ret_24_q10",
        "pred_ret_24_q90",
        "true_ret_12_dir_atr",
        "true_ret_24_dir_atr",
    }
    missing = sorted(required_columns.difference(frame.columns))
    if missing:
        raise ValueError(f"missing columns: {missing}")

    working = attach_baseline_score(frame, baseline_frame)
    baseline_threshold = float(selected_rule["baseline_threshold"])
    winner = selected_rule["winner"]

    working["baseline_selected"] = (
        (pd.to_numeric(working["signal"], errors="raise") != 0)
        & (pd.to_numeric(working["baseline_score"], errors="raise") >= baseline_threshold)
    )
    working = apply_conformal_correction(working, float(winner["correction"]))
    selected_mask = build_rule_mask(
        working,
        rule=str(winner["rule"]),
        m=float(winner["m"]),
        w=float(winner["w"]),
    )
    selected = working.loc[selected_mask].copy()
    selected["pnl_hold12_atr"] = pd.to_numeric(
        selected["true_ret_12_dir_atr"], errors="raise"
    ).astype(float)
    selected["pnl_hold24_atr"] = pd.to_numeric(
        selected["true_ret_24_dir_atr"], errors="raise"
    ).astype(float)
    return selected


def build_yearly_breakdown(
    frame: pd.DataFrame, min_year_trades: int = 3
) -> tuple[pd.DataFrame, int]:
    columns = [
        "year",
        "n_trades_hold12",
        "pf_hold12",
        "mean_pnl_hold12_atr",
        "n_trades_hold24",
        "pf_hold24",
        "mean_pnl_hold24_atr",
    ]
    if frame.empty:
        return pd.DataFrame(columns=columns), 0

    working = frame.copy()
    working["time"] = pd.to_datetime(
        working["time"], format="%Y.%m.%d %H:%M", errors="coerce"
    )
    working = working.loc[working["time"].notna()].copy()
    if working.empty:
        return pd.DataFrame(columns=columns), 0

    working["year"] = working["time"].dt.year.astype(int)
    rows: list[dict[str, Any]] = []
    negative_years = 0

    for year, group in working.groupby("year", sort=True):
        hold12 = compute_metrics(group, "pnl_hold12_atr")
        hold24 = compute_metrics(group, "pnl_hold24_atr")
        if int(hold12["n_trades"]) >= min_year_trades:
            hold12_pf = hold12["pf"]
            if hold12_pf is not None and hold12_pf < 1.0:
                negative_years += 1

        rows.append(
            {
                "year": int(year),
                "n_trades_hold12": hold12["n_trades"],
                "pf_hold12": hold12["pf"],
                "mean_pnl_hold12_atr": hold12["mean_pnl_atr"],
                "n_trades_hold24": hold24["n_trades"],
                "pf_hold24": hold24["pf"],
                "mean_pnl_hold24_atr": hold24["mean_pnl_atr"],
            }
        )

    return pd.DataFrame(rows, columns=columns), negative_years


def evaluate_split(
    frame: pd.DataFrame, split: str, min_year_trades: int = 3
) -> dict[str, Any]:
    yearly, negative_years = build_yearly_breakdown(
        frame, min_year_trades=min_year_trades
    )
    return {
        "split": split,
        "hold12": compute_metrics(frame, "pnl_hold12_atr"),
        "hold24": compute_metrics(frame, "pnl_hold24_atr"),
        "negative_year_slices_hold12": negative_years,
        "yearly": yearly.to_dict(orient="records"),
    }


def _format_invalid_numeric_reason(name: str, value: Any) -> str:
    return f"{name}={value} is invalid"


def _is_invalid_numeric_value(value: Any, *, allow_none: bool = False) -> bool:
    if value is None:
        return not allow_none
    try:
        return math.isnan(float(value))
    except (TypeError, ValueError):
        return True


def _is_invalid_count_value(value: Any) -> bool:
    if _is_invalid_numeric_value(value):
        return True
    numeric = float(value)
    return numeric < 0.0 or not numeric.is_integer()


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
    hold12_pf_is_invalid = _is_invalid_numeric_value(hold12_pf)
    hold24_pf_is_invalid = _is_invalid_numeric_value(hold24_pf, allow_none=True)
    hold24_mean_pnl_atr_is_invalid = _is_invalid_numeric_value(
        hold24_mean_pnl_atr, allow_none=True
    )
    hold12_mean_pnl_atr_is_invalid = _is_invalid_numeric_value(
        hold12_mean_pnl_atr, allow_none=True
    )
    mean_pnl_tolerance_atr_is_invalid = _is_invalid_numeric_value(mean_pnl_tolerance_atr)
    hold12_n_trades_is_invalid = _is_invalid_count_value(hold12_n_trades)
    hold12_negative_year_slices_is_invalid = _is_invalid_count_value(
        hold12_negative_year_slices
    )

    if hold12_n_trades_is_invalid:
        reasons.append(_format_invalid_numeric_reason("hold12_n_trades", hold12_n_trades))
    elif hold12_n_trades < GATE_MIN_TRADES:
        reasons.append(f"hold12_n_trades={hold12_n_trades} < {GATE_MIN_TRADES}")

    if hold12_pf is None:
        hold12_pf_text = "None" if hold12_pf is None else f"{hold12_pf:.4f}"
        reasons.append(f"hold12_pf={hold12_pf_text} <= {GATE_MIN_PF}")
    elif hold12_pf_is_invalid:
        reasons.append(_format_invalid_numeric_reason("hold12_pf", hold12_pf))
    elif hold12_pf <= GATE_MIN_PF:
        reasons.append(f"hold12_pf={hold12_pf:.4f} <= {GATE_MIN_PF}")

    if hold24_pf_is_invalid:
        reasons.append(_format_invalid_numeric_reason("hold24_pf", hold24_pf))
    elif (
        hold24_pf is not None
        and hold12_pf is not None
        and not hold12_pf_is_invalid
        and hold12_pf < hold24_pf
    ):
        reasons.append(f"hold12_pf={hold12_pf:.4f} < hold24_pf={hold24_pf:.4f}")

    if mean_pnl_tolerance_atr_is_invalid:
        reasons.append(_format_invalid_numeric_reason("mean_pnl_tolerance_atr", mean_pnl_tolerance_atr))
    if hold24_mean_pnl_atr_is_invalid:
        reasons.append(_format_invalid_numeric_reason("hold24_mean_pnl_atr", hold24_mean_pnl_atr))
    if hold12_mean_pnl_atr_is_invalid:
        reasons.append(_format_invalid_numeric_reason("hold12_mean_pnl_atr", hold12_mean_pnl_atr))
    if (
        hold24_mean_pnl_atr is not None
        and hold12_mean_pnl_atr is not None
        and not hold24_mean_pnl_atr_is_invalid
        and not hold12_mean_pnl_atr_is_invalid
        and not mean_pnl_tolerance_atr_is_invalid
        and hold12_mean_pnl_atr < hold24_mean_pnl_atr - mean_pnl_tolerance_atr
    ):
        reasons.append(
            "hold12_mean_pnl_atr="
            f"{hold12_mean_pnl_atr:.4f} < hold24_mean_pnl_atr={hold24_mean_pnl_atr:.4f}"
        )

    if hold12_negative_year_slices_is_invalid:
        reasons.append(
            _format_invalid_numeric_reason(
                "hold12_negative_year_slices", hold12_negative_year_slices
            )
        )
    elif hold12_negative_year_slices > GATE_MAX_NEGATIVE_YEAR_SLICES:
        reasons.append(
            "hold12_negative_year_slices="
            f"{hold12_negative_year_slices} > {GATE_MAX_NEGATIVE_YEAR_SLICES}"
        )

    invalid_seed_pf_values = [
        value for value in seed_pf_values if _is_invalid_numeric_value(value)
    ]
    if invalid_seed_pf_values:
        reasons.append(f"seed_pf_values_contain_invalid_numeric_values: {invalid_seed_pf_values}")

    weak_seed_values = [
        float(value)
        for value in seed_pf_values
        if not _is_invalid_numeric_value(value) and float(value) <= GATE_MIN_SEED_PF
    ]
    if weak_seed_values:
        reasons.append(f"seed_pf_values_contain_pf<=1.0: {weak_seed_values}")

    return {
        "verdict": "gate_pass" if not reasons else "gate_fail",
        "reasons": reasons,
    }
