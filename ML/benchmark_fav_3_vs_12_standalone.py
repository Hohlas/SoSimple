from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


EPS = 1e-6
DEFAULT_UPDN_ACTIVE_DIR = Path("ML/reports/quantile_fav_composition/updn_active_source")
DEFAULT_SEED_DIR = Path("ML/reports/entry_path_v1_quantile_robustness/seed_007")
DEFAULT_OUTPUT_DIR = Path("ML/reports/fav_3_vs_12_standalone")
DEFAULT_THRESHOLDS = [round(x / 100, 2) for x in range(20, 121, 2)]
REQUIRED_UPDN_COLUMNS = {"time", "signal", "pred_fav_3", "pred_fav_12"}
REQUIRED_QUANTILE_COLUMNS = {"time", "signal", "true_ret_24_dir_atr"}


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
    negative_year_slices = pd.to_numeric(working["negative_year_slices"], errors="coerce").fillna(
        max_negative_year_slices + 1
    ).astype(int)
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


def _parse_thresholds(value: str) -> list[float]:
    try:
        thresholds = [float(part.strip()) for part in value.split(",") if part.strip()]
    except ValueError as exc:
        raise argparse.ArgumentTypeError("thresholds must be comma-separated numbers") from exc
    if not thresholds:
        raise argparse.ArgumentTypeError("threshold list must not be empty")
    if any(not math.isfinite(threshold) for threshold in thresholds):
        raise argparse.ArgumentTypeError("thresholds must be finite numbers")
    if len(thresholds) != len(set(thresholds)):
        raise argparse.ArgumentTypeError("duplicate threshold values are not allowed")
    return sorted(thresholds)


def _load_updn_frame(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, sep=";")
    missing = REQUIRED_UPDN_COLUMNS.difference(frame.columns)
    if missing:
        raise ValueError(f"{path} missing required columns: {sorted(missing)}")
    for column in ["pred_fav_3", "pred_fav_12"]:
        frame[column] = pd.to_numeric(frame[column], errors="raise")
    pd.to_datetime(frame["time"], errors="raise")
    return add_fav_ratio(frame)


def _quantile_split_path(seed_dir: Path, split: str) -> Path:
    return seed_dir / f"entry_path_v1_quantile_{split}_predictions.csv"


def _load_quantile_active_outcomes(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, sep=";")
    missing = REQUIRED_QUANTILE_COLUMNS.difference(frame.columns)
    if missing:
        raise ValueError(f"{path} missing required columns: {sorted(missing)}")
    frame["true_ret_24_dir_atr"] = pd.to_numeric(frame["true_ret_24_dir_atr"], errors="raise")
    pd.to_datetime(frame["time"], errors="raise")
    return frame.loc[frame["signal"] != 0, ["time", "signal", "true_ret_24_dir_atr"]].reset_index(drop=True)


def attach_outcomes_by_active_row_order(updn_frame: pd.DataFrame, quantile_active_frame: pd.DataFrame) -> pd.DataFrame:
    out = updn_frame.copy().reset_index(drop=True)
    expected = out[["time", "signal"]].reset_index(drop=True)
    actual = quantile_active_frame[["time", "signal"]].reset_index(drop=True)
    if len(expected) != len(actual) or not expected.equals(actual):
        raise ValueError("updn active source does not match quantile active outcome row order")
    out["pnl_atr"] = quantile_active_frame["true_ret_24_dir_atr"].to_numpy()
    return out


def _json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        return "inf" if value > 0 else "-inf"
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return _json_ready(value.item())
    return value


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(_json_ready(payload), indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _selected_metrics(frame: pd.DataFrame, threshold: float | None, min_year_trades: int) -> dict[str, Any]:
    if threshold is None:
        return {
            "threshold": None,
            "n_trades": 0,
            "wins": 0,
            "losses": 0,
            "gross_profit": 0.0,
            "gross_loss": 0.0,
            "pf": None,
            "win_rate": None,
            "mean_pnl_atr": None,
            "negative_year_slices": 0,
        }

    selected = frame[frame["fav_3_vs_12"] <= threshold]
    metrics = compute_metrics(selected)
    metrics["threshold"] = float(threshold)
    metrics["negative_year_slices"] = count_negative_year_slices(selected, min_year_trades=min_year_trades)
    return metrics


def _passes_gate(
    metrics: dict[str, Any],
    *,
    min_trades: int,
    min_pf: float,
    max_negative_year_slices: int,
) -> bool:
    pf = metrics.get("pf")
    pf_value = float(pf) if pf is not None and pd.notna(pf) else -1.0
    return (
        int(metrics["n_trades"]) >= min_trades
        and pf_value >= min_pf
        and int(metrics["negative_year_slices"]) <= max_negative_year_slices
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Benchmark fav_3_vs_12 as a standalone threshold filter.")
    parser.add_argument("--updn-active-dir", type=Path, default=DEFAULT_UPDN_ACTIVE_DIR)
    parser.add_argument("--seed-dir", type=Path, default=DEFAULT_SEED_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--thresholds", type=_parse_thresholds, default=DEFAULT_THRESHOLDS)
    parser.add_argument("--min-trades-validation", type=int, default=30)
    parser.add_argument("--min-trades-test", type=int, default=30)
    parser.add_argument("--min-pf-validation", type=float, default=2.0)
    parser.add_argument("--min-pf-test", type=float, default=1.5)
    parser.add_argument("--max-negative-year-slices-validation", type=int, default=0)
    parser.add_argument("--max-negative-year-slices-test", type=int, default=0)
    parser.add_argument("--min-year-trades", type=int, default=3)
    parser.add_argument("--window-size", type=int, default=5)
    parser.add_argument("--min-passing-in-window", type=int, default=3)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    validation_path = args.updn_active_dir / "validation_active_updn_predictions.csv"
    test_path = args.updn_active_dir / "test_active_updn_predictions.csv"
    validation_quantile_path = _quantile_split_path(args.seed_dir, "validation")
    test_quantile_path = _quantile_split_path(args.seed_dir, "test")
    if (
        not validation_path.exists()
        or not test_path.exists()
        or not validation_quantile_path.exists()
        or not test_quantile_path.exists()
    ):
        return 2

    try:
        validation = attach_outcomes_by_active_row_order(
            _load_updn_frame(validation_path),
            _load_quantile_active_outcomes(validation_quantile_path),
        )
        test = attach_outcomes_by_active_row_order(
            _load_updn_frame(test_path),
            _load_quantile_active_outcomes(test_quantile_path),
        )
    except (KeyError, ValueError, pd.errors.ParserError):
        return 2

    validation_grid = evaluate_threshold_grid(validation, args.thresholds)
    validation_grid = annotate_grid_with_yearly_failures(
        frame=validation,
        grid=validation_grid,
        min_year_trades=args.min_year_trades,
    )

    selected_threshold = select_stable_threshold(
        validation_grid,
        min_trades=args.min_trades_validation,
        min_pf=args.min_pf_validation,
        max_negative_year_slices=args.max_negative_year_slices_validation,
        window_size=args.window_size,
        min_passing_in_window=args.min_passing_in_window,
    )
    threshold = selected_threshold["threshold"]
    validation_selected = _selected_metrics(validation, threshold, args.min_year_trades)
    test_selected = _selected_metrics(test, threshold, args.min_year_trades)
    test_grid = evaluate_threshold_grid(test, args.thresholds)
    test_grid = annotate_grid_with_yearly_failures(
        frame=test,
        grid=test_grid,
        min_year_trades=args.min_year_trades,
    )

    validation_passes = _passes_gate(
        validation_selected,
        min_trades=args.min_trades_validation,
        min_pf=args.min_pf_validation,
        max_negative_year_slices=args.max_negative_year_slices_validation,
    )
    test_passes = _passes_gate(
        test_selected,
        min_trades=args.min_trades_test,
        min_pf=args.min_pf_test,
        max_negative_year_slices=args.max_negative_year_slices_test,
    )
    verdict = (
        "baseline_candidate"
        if selected_threshold["verdict"] == "selected" and validation_passes and test_passes
        else "reject_as_standalone"
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    validation_grid.to_csv(args.output_dir / "threshold_grid_validation.csv", sep=";", index=False)
    test_grid.to_csv(args.output_dir / "threshold_grid_test.csv", sep=";", index=False)

    if threshold is None:
        yearly_validation = compute_yearly_breakdown(validation.iloc[0:0])
        yearly_test = compute_yearly_breakdown(test.iloc[0:0])
    else:
        yearly_validation = compute_yearly_breakdown(validation[validation["fav_3_vs_12"] <= threshold])
        yearly_test = compute_yearly_breakdown(test[test["fav_3_vs_12"] <= threshold])
    yearly_validation.to_csv(args.output_dir / "yearly_breakdown_validation.csv", sep=";", index=False)
    yearly_test.to_csv(args.output_dir / "yearly_breakdown_test.csv", sep=";", index=False)

    _write_json(
        args.output_dir / "selected_threshold.json",
        {
            **selected_threshold,
            "validation": validation_selected,
            "test": test_selected,
        },
    )
    gates = {
        "min_trades_validation": args.min_trades_validation,
        "min_trades_test": args.min_trades_test,
        "min_pf_validation": args.min_pf_validation,
        "min_pf_test": args.min_pf_test,
        "max_negative_year_slices_validation": args.max_negative_year_slices_validation,
        "max_negative_year_slices_test": args.max_negative_year_slices_test,
        "min_year_trades": args.min_year_trades,
        "window_size": args.window_size,
        "min_passing_in_window": args.min_passing_in_window,
    }
    _write_json(
        args.output_dir / "verdict.json",
        {
            "verdict": verdict,
            "selected_threshold": threshold,
            "validation_passes": validation_passes,
            "test_passes": test_passes,
            "gates": gates,
            "validation": validation_selected,
            "test": test_selected,
        },
    )
    _write_json(
        args.output_dir / "run_metadata.json",
        {
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "updn_active_dir": str(args.updn_active_dir),
            "seed_dir": str(args.seed_dir),
            "output_dir": str(args.output_dir),
            "validation_input": str(validation_path),
            "test_input": str(test_path),
            "validation_quantile_input": str(validation_quantile_path),
            "test_quantile_input": str(test_quantile_path),
            "validation_rows": int(len(validation)),
            "test_rows": int(len(test)),
            "thresholds": args.thresholds,
            "gates": gates,
            "selection_split": "validation",
            "test_policy": "single_confirmation_after_validation_selection",
        },
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
