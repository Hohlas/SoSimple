from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import pandas as pd

from ML.benchmark_entry_path_v1_quantile_filter import (
    apply_conformal_correction,
    attach_baseline_score,
    build_rule_mask,
    compute_m_at_quantile,
    load_prediction_frame,
)


def build_relaxed_candidate_grid() -> list[tuple[str, float]]:
    return [
        ("lb_gt_m", 0.15),
        ("lb_gt_m", 0.20),
        ("lb_gt_m", 0.25),
        ("lb_gt_m", 0.30),
        ("lb_gt_m", 0.35),
    ]


def summarize_selected_trades(frame: pd.DataFrame, min_year_trades: int) -> dict:
    work = frame.copy()
    work["time"] = pd.to_datetime(work["time"], format="%Y.%m.%d %H:%M", errors="raise")
    pnl = work["true_ret_24_dir_atr"].astype(float)
    gross_profit = float(pnl[pnl > 0].sum())
    gross_loss = float(-pnl[pnl < 0].sum())
    if gross_loss == 0.0:
        pf = math.inf if gross_profit > 0.0 else 0.0
    else:
        pf = gross_profit / gross_loss
    work["year"] = work["time"].dt.year
    negative_year_slices = 0
    for _, group in work.groupby("year"):
        if len(group) < min_year_trades:
            continue
        if float(group["true_ret_24_dir_atr"].sum()) < 0.0:
            negative_year_slices += 1
    return {
        "trades": int(len(work)),
        "pf": pf,
        "win_rate": float((pnl > 0).mean()) if len(work) else 0.0,
        "mean_pnl_atr": float(pnl.mean()) if len(work) else 0.0,
        "negative_year_slices": negative_year_slices,
    }


def choose_relaxed_baseline(
    grid: pd.DataFrame,
    frozen_validation_trades: int,
    trade_multiplier: float,
    min_pf: float,
) -> dict:
    target_trades = int(math.ceil(frozen_validation_trades * trade_multiplier))
    viable = grid.loc[
        (grid["trades"] >= target_trades)
        & (grid["pf"] >= min_pf)
        & (grid["negative_year_slices"] == 0)
    ].sort_values(["pf", "mean_pnl_atr", "trades"], ascending=[False, False, False])
    if viable.empty:
        return {
            "verdict": "relaxed_baseline_not_viable",
            "target_trades": target_trades,
            "candidate": None,
            "max_trades_in_grid": int(grid["trades"].max()) if not grid.empty else 0,
        }

    row = viable.iloc[0]
    return {
        "verdict": "baseline_candidate",
        "target_trades": target_trades,
        "candidate": row["candidate"],
    }


def apply_session_filter(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.loc[frame["session"] != "ny"].copy()


def apply_pred_adv_filter(frame: pd.DataFrame, threshold: float) -> pd.DataFrame:
    return frame.loc[frame["pred_adv_12_atr"].astype(float) <= threshold].copy()


def should_run_combined_filter(grid: pd.DataFrame) -> bool:
    meaningful = grid.loc[
        (grid["trades"] >= 30)
        & (grid["pf"] >= 2.0)
        & (grid["negative_year_slices"] == 0)
        & (grid["pf_delta_vs_baseline"] >= 0.5)
    ]
    return not meaningful.empty


def label_session_bucket(frame: pd.DataFrame) -> pd.DataFrame:
    work = frame.copy()
    work["time"] = pd.to_datetime(work["time"], format="%Y.%m.%d %H:%M", errors="raise")
    hours = work["time"].dt.hour
    work["session"] = "ny"
    work.loc[hours.between(0, 6), "session"] = "asia"
    work.loc[hours.between(7, 12), "session"] = "london"
    work.loc[hours.between(13, 18), "session"] = "overlap"
    return work


def evaluate_filters(selected_frame: pd.DataFrame, min_year_trades: int) -> pd.DataFrame:
    baseline_summary = summarize_selected_trades(selected_frame, min_year_trades)
    session_frame = apply_session_filter(label_session_bucket(selected_frame))
    pred_adv_threshold = float(selected_frame["pred_adv_12_atr"].astype(float).quantile(0.75))
    pred_adv_frame = apply_pred_adv_filter(selected_frame, threshold=pred_adv_threshold)

    rows = []
    session_summary = summarize_selected_trades(session_frame, min_year_trades)
    rows.append(
        {
            "filter_name": "session_only",
            "threshold": None,
            "pf_delta_vs_baseline": float(session_summary["pf"] - baseline_summary["pf"]),
            **session_summary,
        }
    )
    pred_adv_summary = summarize_selected_trades(pred_adv_frame, min_year_trades)
    rows.append(
        {
            "filter_name": "pred_adv12_only",
            "threshold": pred_adv_threshold,
            "pf_delta_vs_baseline": float(pred_adv_summary["pf"] - baseline_summary["pf"]),
            **pred_adv_summary,
        }
    )
    return pd.DataFrame(rows)


def summarize_relaxed_candidates(frame: pd.DataFrame, min_year_trades: int) -> pd.DataFrame:
    rows = []
    for rule, quantile in build_relaxed_candidate_grid():
        m = compute_m_at_quantile(frame, quantile)
        mask = build_rule_mask(frame, rule=rule, m=m, w=0.0)
        summary = summarize_selected_trades(frame.loc[mask, ["time", "true_ret_24_dir_atr"]], min_year_trades)
        rows.append(
            {
                "candidate": f"{rule}_q{int(quantile * 100):02d}",
                "rule": rule,
                "quantile": quantile,
                "m": m,
                **summary,
            }
        )
    return pd.DataFrame(rows)


def prepare_relaxed_selection_frame(
    frame: pd.DataFrame,
    baseline_frame: pd.DataFrame,
    baseline_threshold: float,
    correction: float,
) -> pd.DataFrame:
    working = frame.copy()
    working["time"] = pd.to_datetime(working["time"], format="%Y.%m.%d %H:%M", errors="raise")
    baseline = baseline_frame.copy()
    baseline["time"] = pd.to_datetime(baseline["time"], format="%Y.%m.%d %H:%M", errors="raise")
    joined = attach_baseline_score(working, baseline)
    joined["baseline_selected"] = (
        (joined["signal"].astype(int) != 0)
        & (joined["baseline_score"].astype(float) >= float(baseline_threshold))
    )
    return apply_conformal_correction(joined, float(correction))


def load_selected_rule(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def resolve_frozen_validation_trades(grid: pd.DataFrame, selected_rule: dict) -> int:
    candidate = selected_rule["winner"]["candidate"]
    match = grid.loc[grid["candidate"] == candidate]
    if not match.empty:
        return int(match.iloc[0]["trades"])
    return int(selected_rule["winner"]["trades"])


def run_validation_baseline_stage(
    *,
    validation_predictions: str | Path,
    baseline_validation_predictions: str | Path,
    selected_rule_path: str | Path,
    output_dir: str | Path,
    trade_multiplier: float = 2.0,
    min_pf: float = 2.0,
    min_year_trades: int = 3,
) -> dict:
    selected_rule = load_selected_rule(selected_rule_path)
    validation_frame = load_prediction_frame(validation_predictions)
    baseline_validation = load_prediction_frame(baseline_validation_predictions)
    prepared = prepare_relaxed_selection_frame(
        validation_frame,
        baseline_validation,
        baseline_threshold=float(selected_rule["baseline_threshold"]),
        correction=float(selected_rule["winner"]["correction"]),
    )
    baseline_grid = summarize_relaxed_candidates(prepared, min_year_trades=min_year_trades)
    frozen_validation_trades = resolve_frozen_validation_trades(baseline_grid, selected_rule)
    selected_baseline = choose_relaxed_baseline(
        baseline_grid,
        frozen_validation_trades=frozen_validation_trades,
        trade_multiplier=trade_multiplier,
        min_pf=min_pf,
    )

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    baseline_grid.to_csv(output_path / "validation_baseline_grid.csv", index=False)
    (output_path / "selected_baseline.json").write_text(
        json.dumps(selected_baseline, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return {
        "validation_baseline_grid": baseline_grid,
        "selected_baseline": selected_baseline,
    }


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validation-predictions", required=True)
    parser.add_argument("--baseline-validation-predictions", required=True)
    parser.add_argument("--selected-rule", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--trade-multiplier", type=float, default=2.0)
    parser.add_argument("--min-pf", type=float, default=2.0)
    parser.add_argument("--min-year-trades", type=int, default=3)
    return parser


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()
    run_validation_baseline_stage(
        validation_predictions=args.validation_predictions,
        baseline_validation_predictions=args.baseline_validation_predictions,
        selected_rule_path=args.selected_rule,
        output_dir=args.output_dir,
        trade_multiplier=args.trade_multiplier,
        min_pf=args.min_pf,
        min_year_trades=args.min_year_trades,
    )


if __name__ == "__main__":
    main()
