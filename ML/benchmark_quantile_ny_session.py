from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path
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
DEFAULT_OUTPUT_DIR = Path("ML/reports/quantile_ny_session")
DEFAULT_ROOT_DIR = Path("ML/reports/entry_path_v1_quantile_robustness")
DEFAULT_SELECTED_RULE = Path("ML/reports/entry_path_v1_quantile_selected_rule.json")
DEFAULT_SEEDS = [7, 17, 42, 77, 123]


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
    joined: pd.DataFrame,
) -> None:
    if len(joined) < len(frame):
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
    _validate_join_alignment(parsed_frame, working)
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
    if frame["session"].isna().any():
        raise ValueError("session column contains null/NaN values")
    invalid_sessions = sorted(
        value for value in set(frame["session"]) - {"asia", "london", "overlap", "ny"}
    )
    if invalid_sessions:
        raise ValueError(f"unknown session values: {invalid_sessions}")
    return frame.loc[~frame["session"].isin(drop_sessions)].copy()


def select_non_ny_quantile_trades(
    frame: pd.DataFrame,
    baseline_frame: pd.DataFrame,
    selected_rule: dict[str, Any],
) -> pd.DataFrame:
    selected = select_quantile_trades(
        frame=frame,
        baseline_frame=baseline_frame,
        selected_rule=selected_rule,
    )
    return filter_session_trades(selected)


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


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if hasattr(value, "item"):
        return _json_safe(value.item())
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if pd.isna(value):
        return None
    return value


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(_json_safe(payload), indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _parse_seeds(raw_value: str | None) -> list[int]:
    if raw_value is None:
        return list(DEFAULT_SEEDS)
    chunks = [chunk.strip() for chunk in raw_value.split(",") if chunk.strip()]
    if not chunks:
        raise ValueError("seeds must not be empty")
    return [int(chunk) for chunk in chunks]


def _load_rule_payload(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _summarize_filtered_split(
    selected: pd.DataFrame,
    filtered: pd.DataFrame,
    split: str,
) -> dict[str, Any]:
    baseline_metrics = compute_metrics(selected, DEFAULT_PNL_COLUMN)
    filtered_metrics = evaluate_split(filtered, split=split, pnl_column=DEFAULT_PNL_COLUMN)
    gate = decide_session_gate(
        baseline_pf=baseline_metrics["pf"],
        filtered_pf=filtered_metrics["pf"],
        filtered_n_trades=filtered_metrics["n_trades"],
        filtered_negative_year_slices=filtered_metrics["negative_year_slices"],
        seed_pf_values=[],
    )
    return {
        "split": split,
        "status": "evaluated",
        "baseline": {
            **baseline_metrics,
            "negative_year_slices": count_negative_year_slices(selected, DEFAULT_PNL_COLUMN),
        },
        "filtered": filtered_metrics,
        "gate": gate,
    }


def _yearly_rows(split: str, scope: str, frame: pd.DataFrame) -> pd.DataFrame:
    yearly, _ = build_yearly_breakdown(frame, DEFAULT_PNL_COLUMN)
    if yearly.empty:
        return pd.DataFrame(
            columns=[
                "split",
                "scope",
                "year",
                "n_trades",
                "pf",
                "mean_pnl_atr",
                "gross_profit",
                "gross_loss",
            ]
        )
    out = yearly.copy()
    out.insert(0, "scope", scope)
    out.insert(0, "split", split)
    return out


def _load_quantile_frame(path: str | Path) -> pd.DataFrame:
    return pd.read_csv(Path(path), sep=";")


def _seed_prediction_path(root_dir: Path, seed: int, split: str) -> Path:
    return root_dir / f"seed_{seed:03d}" / f"entry_path_v1_quantile_{split}_predictions.csv"


def _seed_summary_rows(
    *,
    root_dir: Path,
    seeds: list[int],
    selected_rule: dict[str, Any],
    baseline_validation_predictions: str | Path,
    baseline_test_predictions: str | Path,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, Any]] = []
    yearly_frames: list[pd.DataFrame] = []
    for seed in seeds:
        seed_dir = root_dir / f"seed_{seed:03d}"
        validation_path = _seed_prediction_path(root_dir, seed, "validation")
        test_path = _seed_prediction_path(root_dir, seed, "test")
        if not validation_path.exists() or not test_path.exists():
            raise FileNotFoundError(f"missing seed artifacts for seed {seed}")

        validation_selected = select_quantile_trades(
            frame=_load_quantile_frame(validation_path),
            baseline_frame=_load_quantile_frame(baseline_validation_predictions),
            selected_rule=selected_rule,
        )
        validation_filtered = select_non_ny_quantile_trades(
            frame=_load_quantile_frame(validation_path),
            baseline_frame=_load_quantile_frame(baseline_validation_predictions),
            selected_rule=selected_rule,
        )
        validation_summary = _summarize_filtered_split(
            validation_selected,
            validation_filtered,
            split="validation",
        )

        test_selected = select_quantile_trades(
            frame=_load_quantile_frame(test_path),
            baseline_frame=_load_quantile_frame(baseline_test_predictions),
            selected_rule=selected_rule,
        )
        test_filtered = select_non_ny_quantile_trades(
            frame=_load_quantile_frame(test_path),
            baseline_frame=_load_quantile_frame(baseline_test_predictions),
            selected_rule=selected_rule,
        )
        test_summary = _summarize_filtered_split(
            test_selected,
            test_filtered,
            split="test",
        )

        rows.append(
            {
                "seed": seed,
                "seed_dir": str(seed_dir),
                "validation_baseline_pf": validation_summary["baseline"]["pf"],
                "validation_baseline_trades": validation_summary["baseline"]["n_trades"],
                "validation_filtered_pf": validation_summary["filtered"]["pf"],
                "validation_filtered_trades": validation_summary["filtered"]["n_trades"],
                "validation_filtered_negative_year_slices": validation_summary["filtered"]["negative_year_slices"],
                "validation_gate_verdict": validation_summary["gate"]["verdict"],
                "test_baseline_pf": test_summary["baseline"]["pf"],
                "test_baseline_trades": test_summary["baseline"]["n_trades"],
                "test_filtered_pf": test_summary["filtered"]["pf"],
                "test_filtered_trades": test_summary["filtered"]["n_trades"],
                "test_filtered_negative_year_slices": test_summary["filtered"]["negative_year_slices"],
                "test_gate_verdict": test_summary["gate"]["verdict"],
            }
        )
        yearly_frames.extend(
            [
                _yearly_rows("validation", "baseline", validation_selected),
                _yearly_rows("validation", "filtered", validation_filtered),
                _yearly_rows("test", "baseline", test_selected),
                _yearly_rows("test", "filtered", test_filtered),
            ]
        )

    yearly = pd.concat([frame for frame in yearly_frames if not frame.empty], ignore_index=True)
    return pd.DataFrame(rows), yearly


def run_benchmark(
    *,
    validation_predictions: str | Path,
    test_predictions: str | Path,
    baseline_validation_predictions: str | Path,
    baseline_test_predictions: str | Path,
    selected_rule_path: str | Path = DEFAULT_SELECTED_RULE,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    root_dir: str | Path | None = None,
    seeds: list[int] | None = None,
) -> dict[str, Any]:
    selected_rule = _load_rule_payload(selected_rule_path)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    validation_selected = select_quantile_trades(
        frame=_load_quantile_frame(validation_predictions),
        baseline_frame=_load_quantile_frame(baseline_validation_predictions),
        selected_rule=selected_rule,
    )
    validation_filtered = select_non_ny_quantile_trades(
        frame=_load_quantile_frame(validation_predictions),
        baseline_frame=_load_quantile_frame(baseline_validation_predictions),
        selected_rule=selected_rule,
    )
    validation_summary = _summarize_filtered_split(
        validation_selected,
        validation_filtered,
        split="validation",
    )

    if validation_summary["gate"]["verdict"] == "gate_pass":
        test_selected = select_quantile_trades(
            frame=_load_quantile_frame(test_predictions),
            baseline_frame=_load_quantile_frame(baseline_test_predictions),
            selected_rule=selected_rule,
        )
        test_filtered = select_non_ny_quantile_trades(
            frame=_load_quantile_frame(test_predictions),
            baseline_frame=_load_quantile_frame(baseline_test_predictions),
            selected_rule=selected_rule,
        )
        test_summary: dict[str, Any] = _summarize_filtered_split(
            test_selected,
            test_filtered,
            split="test",
        )
        yearly_frames = [
            _yearly_rows("validation", "baseline", validation_selected),
            _yearly_rows("validation", "filtered", validation_filtered),
            _yearly_rows("test", "baseline", test_selected),
            _yearly_rows("test", "filtered", test_filtered),
        ]
    else:
        test_summary = {
            "split": "test",
            "status": "skipped_due_to_validation_gate",
            "reason": "validation_gate_failed",
            "validation_gate": validation_summary["gate"],
        }
        yearly_frames = [
            _yearly_rows("validation", "baseline", validation_selected),
            _yearly_rows("validation", "filtered", validation_filtered),
        ]

    yearly_breakdown = pd.concat([frame for frame in yearly_frames if not frame.empty], ignore_index=True)

    per_seed_summary = pd.DataFrame()
    if root_dir is not None:
        if seeds is None:
            seeds = list(DEFAULT_SEEDS)
        per_seed_summary, _ = _seed_summary_rows(
            root_dir=Path(root_dir),
            seeds=seeds,
            selected_rule=selected_rule,
            baseline_validation_predictions=baseline_validation_predictions,
            baseline_test_predictions=baseline_test_predictions,
        )

    _write_json(output_path / "validation_summary.json", validation_summary)
    _write_json(output_path / "test_summary.json", test_summary)
    yearly_breakdown.to_csv(output_path / "yearly_breakdown.csv", sep=";", index=False)
    per_seed_summary.to_csv(output_path / "per_seed_summary.csv", sep=";", index=False)
    _write_json(
        output_path / "run_metadata.json",
        {
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "validation_predictions": str(validation_predictions),
            "test_predictions": str(test_predictions),
            "baseline_validation_predictions": str(baseline_validation_predictions),
            "baseline_test_predictions": str(baseline_test_predictions),
            "selected_rule_path": str(selected_rule_path),
            "output_dir": str(output_path),
            "root_dir": str(root_dir) if root_dir is not None else None,
            "seeds": seeds if seeds is not None else ([] if root_dir is None else list(DEFAULT_SEEDS)),
            "validation_gate": validation_summary["gate"],
            "test_status": test_summary["status"],
        },
    )
    return {
        "validation_summary": validation_summary,
        "test_summary": test_summary,
        "yearly_breakdown": yearly_breakdown,
        "per_seed_summary": per_seed_summary,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Benchmark frozen quantile trades with an NY-session exclusion filter."
    )
    parser.add_argument("--validation-predictions", required=True)
    parser.add_argument("--test-predictions", required=True)
    parser.add_argument("--baseline-validation-predictions", required=True)
    parser.add_argument("--baseline-test-predictions", required=True)
    parser.add_argument("--selected-rule", required=True)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--root-dir", default=None)
    parser.add_argument("--seeds", default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        run_benchmark(
            validation_predictions=args.validation_predictions,
            test_predictions=args.test_predictions,
            baseline_validation_predictions=args.baseline_validation_predictions,
            baseline_test_predictions=args.baseline_test_predictions,
            selected_rule_path=args.selected_rule,
            output_dir=args.output_dir,
            root_dir=args.root_dir,
            seeds=_parse_seeds(args.seeds),
        )
    except (OSError, ValueError, KeyError, pd.errors.ParserError):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
