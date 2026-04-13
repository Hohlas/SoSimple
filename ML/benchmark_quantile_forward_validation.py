from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import pandas as pd


METRIC_COLUMNS = [
    "n_trades",
    "wins",
    "losses",
    "gross_profit",
    "gross_loss",
    "pf",
    "win_rate",
    "mean_pnl_atr",
]
TIME_SLICE_COLUMNS = ["slice", *METRIC_COLUMNS]


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
    if mode != "quarter":
        raise ValueError(f"unsupported slice mode: {mode}")
    working = frame.copy()
    dt = pd.to_datetime(working["time"])
    working["slice"] = dt.dt.to_period("Q").astype(str).str.replace("Q", "-Q", n=1)

    rows: list[dict[str, Any]] = []
    for key, group in working.groupby("slice", sort=True):
        rows.append({"slice": key, **compute_forward_metrics(group)})
    return pd.DataFrame(rows, columns=TIME_SLICE_COLUMNS)


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


def _count_negative_slices(time_slices: pd.DataFrame) -> int:
    if time_slices.empty or "pf" not in time_slices.columns:
        return 0
    return int(sum(1 for value in time_slices["pf"] if pd.notna(value) and value < 1.0))


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--forward-predictions", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--historical-pf", required=True, type=float)
    parser.add_argument("--slice-mode", default="quarter")
    args = parser.parse_args(argv)

    try:
        frame = pd.read_csv(args.forward_predictions, sep=";")
        required_columns = {"time", "signal", "true_ret_24_dir_atr"}
        if not required_columns.issubset(frame.columns):
            return 2
        signal = pd.to_numeric(frame["signal"], errors="coerce")
        active_rows = frame.loc[signal.notna() & (signal != 0)].copy()
        forward_metrics = compute_forward_metrics(active_rows)
        time_slices = build_time_slices(active_rows, mode=args.slice_mode)
        negative_slices = _count_negative_slices(time_slices)
        verdict = decide_operational_verdict(
            historical_pf=args.historical_pf,
            forward_pf=forward_metrics["pf"],
            n_trades=forward_metrics["n_trades"],
            negative_slices=negative_slices,
        )
    except (OSError, ValueError, KeyError, pd.errors.ParserError):
        return 2

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    summary = {
        "input_path": args.forward_predictions,
        "historical_pf": args.historical_pf,
        "slice_mode": args.slice_mode,
        "total_rows": int(len(frame)),
        "active_rows": int(len(active_rows)),
        "negative_slices": negative_slices,
        "forward_metrics": forward_metrics,
        **verdict,
    }
    run_metadata = {
        "input_path": args.forward_predictions,
        "historical_pf": args.historical_pf,
        "slice_mode": args.slice_mode,
        "total_rows": int(len(frame)),
        "active_rows": int(len(active_rows)),
    }

    with (output_dir / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(_json_safe(summary), handle, indent=2, ensure_ascii=False, allow_nan=False)
        handle.write("\n")
    time_slices.to_csv(output_dir / "time_slices.csv", sep=";", index=False)
    with (output_dir / "run_metadata.json").open("w", encoding="utf-8") as handle:
        json.dump(_json_safe(run_metadata), handle, indent=2, ensure_ascii=False, allow_nan=False)
        handle.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
