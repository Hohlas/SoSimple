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


def evaluate_threshold_grid(frame: pd.DataFrame, thresholds: list[float]) -> pd.DataFrame:
    rows = []
    for threshold in thresholds:
        selected = frame[frame["fav_3_vs_12"] <= threshold]
        metrics = compute_metrics(selected)
        rows.append({"threshold": float(threshold), **metrics})
    return pd.DataFrame(rows)


def compute_yearly_breakdown(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(
            columns=[
                "year",
                "n_trades",
                "wins",
                "losses",
                "gross_profit",
                "gross_loss",
                "pf",
                "win_rate",
                "mean_pnl_atr",
            ]
        )

    working = frame.copy()
    working["year"] = pd.to_datetime(working["time"]).dt.year
    rows = []
    for year, group in working.groupby("year", sort=True):
        rows.append({"year": int(year), **compute_metrics(group)})
    return pd.DataFrame(rows)


def count_negative_year_slices(frame: pd.DataFrame, min_year_trades: int = 3) -> int:
    yearly = compute_yearly_breakdown(frame)
    if yearly.empty:
        return 0
    total = 0
    for _, row in yearly.iterrows():
        if int(row["n_trades"]) < min_year_trades:
            continue
        pf = row["pf"]
        if pd.notna(pf) and float(pf) < 1.0:
            total += 1
    return total


def annotate_grid_with_yearly_failures(
    frame: pd.DataFrame,
    grid: pd.DataFrame,
    *,
    min_year_trades: int = 3,
) -> pd.DataFrame:
    result = grid.copy()
    result["negative_year_slices"] = [
        count_negative_year_slices(frame[frame["fav_3_vs_12"] <= threshold], min_year_trades=min_year_trades)
        for threshold in result["threshold"]
    ]
    return result


def _prepare_threshold_grid(grid: pd.DataFrame) -> pd.DataFrame:
    working = grid.copy()
    working["threshold"] = pd.to_numeric(working["threshold"], errors="raise")
    if working["threshold"].duplicated().any():
        raise ValueError("duplicate threshold values are not allowed")
    return working.sort_values("threshold", kind="mergesort").reset_index(drop=True)


def select_stable_threshold(
    grid: pd.DataFrame,
    *,
    min_trades: int,
    min_pf: float,
    max_negative_year_slices: int,
    window_size: int,
    min_passing_in_window: int,
) -> dict[str, float | int | str | None]:
    working = _prepare_threshold_grid(grid)
    pf = pd.to_numeric(working["pf"], errors="coerce").fillna(-1.0)
    n_trades = pd.to_numeric(working["n_trades"], errors="coerce").fillna(0).astype(int)
    negative_year_slices = pd.to_numeric(working["negative_year_slices"], errors="coerce").fillna(0).astype(int)
    working["passes_basic_gate"] = (
        (n_trades >= min_trades)
        & (pf >= min_pf)
        & (negative_year_slices <= max_negative_year_slices)
    )

    if window_size <= 0 or window_size % 2 == 0:
        return {"verdict": "no_stable_threshold", "threshold": None}

    left_size = window_size // 2
    right_size = window_size - left_size - 1
    best = None
    for idx, row in working.iterrows():
        start = idx - left_size
        stop = idx + right_size + 1
        if start < 0 or stop > len(working):
            continue
        window = working.iloc[start:stop]
        if len(window) != window_size:
            continue
        passing = int(window["passes_basic_gate"].sum())
        if passing < min_passing_in_window or not bool(row["passes_basic_gate"]):
            continue

        window_pf = pd.to_numeric(window.loc[window["passes_basic_gate"], "pf"], errors="coerce").fillna(-1.0)
        if window_pf.empty:
            window_pf = pd.to_numeric(window["pf"], errors="coerce").fillna(-1.0)

        window_trades = pd.to_numeric(window.loc[window["passes_basic_gate"], "n_trades"], errors="coerce").fillna(0)
        score = (
            passing,
            float(window_pf.median()),
            float(window_pf.min()),
            float(window_trades.median()),
            int(n_trades.iloc[idx]),
        )
        if best is None or score > best["score"]:
            best = {"idx": idx, "score": score}

    if best is None:
        return {"verdict": "no_stable_threshold", "threshold": None}

    row = working.iloc[best["idx"]]
    return {
        "verdict": "selected",
        "threshold": float(row["threshold"]),
        "n_trades": int(n_trades.iloc[best["idx"]]),
        "pf": float(pf.iloc[best["idx"]]),
        "negative_year_slices": int(negative_year_slices.iloc[best["idx"]]),
    }
