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
GATE_MIN_SEED_PF = 1.0
DEFAULT_PNL_COLUMN = "pnl_hold24_atr"
DEFAULT_DROP_SESSIONS = frozenset({"ny"})


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


def _parse_time_frame(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out["time"] = pd.to_datetime(out["time"], format="%Y.%m.%d %H:%M", errors="coerce")
    if out["time"].isna().any():
        raise ValueError("time contains unparsable timestamps")
    return out


def _compute_pf(values: pd.Series) -> float | None:
    gains = float(values[values > 0].sum())
    losses = float(-values[values < 0].sum())
    if gains == 0.0 and losses == 0.0:
        return None
    if losses == 0.0:
        return math.inf
    return gains / losses


def _validate_join_alignment(
    frame: pd.DataFrame,
    baseline_frame: pd.DataFrame,
    joined: pd.DataFrame,
) -> None:
    key_columns = ["time", "signal"]
    if frame.duplicated(key_columns).any():
        raise ValueError("frame contains duplicate (time, signal) rows")
    if baseline_frame.duplicated(key_columns).any():
        raise ValueError("baseline_frame contains duplicate (time, signal) rows")
    if len(joined) != len(frame):
        raise ValueError("baseline_frame does not align one-to-one on (time, signal)")


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

    parsed_frame = _parse_time_frame(frame)
    parsed_baseline = _parse_time_frame(baseline_frame)
    working = attach_baseline_score(parsed_frame, parsed_baseline)
    _validate_join_alignment(parsed_frame, parsed_baseline, working)
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
    selected["session"] = selected["time"].dt.hour.map(assign_session_bucket)
    selected["year"] = selected["time"].dt.year.astype(int)
    selected["time"] = selected["time"].dt.strftime("%Y.%m.%d %H:%M")
    selected["pnl_hold12_atr"] = pd.to_numeric(
        selected["true_ret_12_dir_atr"], errors="raise"
    ).astype(float)
    selected["pnl_hold24_atr"] = pd.to_numeric(
        selected["true_ret_24_dir_atr"], errors="raise"
    ).astype(float)
    return selected


def filter_session_trades(
    frame: pd.DataFrame,
    drop_sessions: frozenset[str] = DEFAULT_DROP_SESSIONS,
) -> pd.DataFrame:
    if "session" not in frame.columns:
        raise ValueError("session column is required")
    invalid_sessions = sorted(set(frame["session"]) - {"asia", "london", "overlap", "ny"})
    if invalid_sessions:
        raise ValueError(f"unknown session values: {invalid_sessions}")
    return frame.loc[~frame["session"].isin(drop_sessions)].copy()


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

    pf = _compute_pf(pnl)

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


def count_negative_year_slices(frame: pd.DataFrame, pnl_column: str) -> int:
    negative_years = 0
    for _, yearly in frame.groupby("year"):
        if len(yearly) < 3:
            continue
        pf = _compute_pf(pd.to_numeric(yearly[pnl_column], errors="raise"))
        if pf is not None and pf < 1.0:
            negative_years += 1
    return negative_years


def build_yearly_breakdown(
    frame: pd.DataFrame,
    pnl_column: str = DEFAULT_PNL_COLUMN,
    min_year_trades: int = 3,
) -> tuple[pd.DataFrame, int]:
    columns = [
        "year",
        "n_trades",
        "pf",
        "mean_pnl_atr",
        "gross_profit",
        "gross_loss",
    ]
    if frame.empty:
        return pd.DataFrame(columns=columns), 0

    working = frame.copy()
    working["time"] = pd.to_datetime(
        working["time"], format="%Y.%m.%d %H:%M", errors="coerce"
    )
    if working["time"].isna().any():
        raise ValueError("time contains unparsable timestamps")

    working["year"] = working["time"].dt.year.astype(int)
    rows: list[dict[str, Any]] = []
    negative_years = 0

    for year, group in working.groupby("year", sort=True):
        metrics = compute_metrics(group, pnl_column=pnl_column)
        if int(metrics["n_trades"]) >= min_year_trades and metrics["pf"] is not None:
            if float(metrics["pf"]) < 1.0:
                negative_years += 1
        rows.append(
            {
                "year": int(year),
                "n_trades": metrics["n_trades"],
                "pf": metrics["pf"],
                "mean_pnl_atr": metrics["mean_pnl_atr"],
                "gross_profit": metrics["gross_profit"],
                "gross_loss": metrics["gross_loss"],
            }
        )

    return pd.DataFrame(rows, columns=columns), negative_years


def evaluate_split(
    frame: pd.DataFrame,
    split: str,
    pnl_column: str = DEFAULT_PNL_COLUMN,
    min_year_trades: int = 3,
) -> dict[str, Any]:
    yearly, negative_years = build_yearly_breakdown(
        frame,
        pnl_column=pnl_column,
        min_year_trades=min_year_trades,
    )
    metrics = compute_metrics(frame, pnl_column=pnl_column)
    return {
        "split": split,
        **metrics,
        "negative_year_slices": negative_years,
        "yearly": yearly.to_dict(orient="records"),
    }


def decide_session_gate(
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
    elif not math.isfinite(float(baseline_pf)):
        reasons.append(f"baseline_pf={baseline_pf} is not finite")
    if filtered_pf is None:
        reasons.append("filtered_pf=None")
    elif not math.isfinite(float(filtered_pf)):
        reasons.append(f"filtered_pf={filtered_pf} is not finite")
    if filtered_n_trades < GATE_MIN_TRADES:
        reasons.append(f"filtered_n_trades={filtered_n_trades} < {GATE_MIN_TRADES}")
    if filtered_pf is None or filtered_pf <= GATE_MIN_PF:
        reasons.append(f"filtered_pf={filtered_pf} <= {GATE_MIN_PF}")
    if baseline_pf is not None and filtered_pf is not None and filtered_pf < baseline_pf:
        reasons.append(f"filtered_pf={filtered_pf:.4f} < baseline_pf={baseline_pf:.4f}")
    if filtered_negative_year_slices > 0:
        reasons.append(f"filtered_negative_year_slices={filtered_negative_year_slices} > 0")

    invalid_seed_pfs = [
        value for value in seed_pf_values
        if value is None or not math.isfinite(float(value))
    ]
    if invalid_seed_pfs:
        reasons.append(f"seed_pf_values_contain_non_finite: {invalid_seed_pfs}")
    weak_seed_pfs = [
        value for value in seed_pf_values
        if value is not None and math.isfinite(float(value)) and value <= GATE_MIN_SEED_PF
    ]
    if weak_seed_pfs:
        reasons.append(f"seed_pf_values_contain_pf<=1.0: {weak_seed_pfs}")

    return {
        "verdict": "gate_pass" if not reasons else "gate_fail",
        "reasons": reasons,
    }
