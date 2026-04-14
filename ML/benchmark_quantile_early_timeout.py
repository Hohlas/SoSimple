from __future__ import annotations

import argparse
import json
import math
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
    if working["time"].isna().any():
        raise ValueError("time contains unparsable timestamps")

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


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "item"):
        try:
            return _json_safe(value.item())
        except (TypeError, ValueError):
            pass
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def _load_predictions(path: str | Path) -> pd.DataFrame:
    return pd.read_csv(Path(path), sep=";")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(
            _json_safe(payload),
            handle,
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        )
        handle.write("\n")


def _build_skipped_test_summary(reason: str) -> dict[str, Any]:
    return {
        "split": "test",
        "skipped": True,
        "skip_reason": reason,
        "hold12": {
            "n_trades": 0,
            "wins": 0,
            "losses": 0,
            "gross_profit": 0.0,
            "gross_loss": 0.0,
            "pf": None,
            "win_rate": None,
            "mean_pnl_atr": None,
        },
        "hold24": {
            "n_trades": 0,
            "wins": 0,
            "losses": 0,
            "gross_profit": 0.0,
            "gross_loss": 0.0,
            "pf": None,
            "win_rate": None,
            "mean_pnl_atr": None,
        },
        "negative_year_slices_hold12": 0,
        "yearly": [],
        "gate": {
            "verdict": "skipped_due_to_validation_gate",
            "reasons": [reason],
        },
    }


def run_benchmark(
    *,
    validation_predictions: str | Path,
    test_predictions: str | Path,
    baseline_validation_predictions: str | Path,
    baseline_test_predictions: str | Path,
    selected_rule: str | Path,
    output_dir: str | Path,
) -> dict[str, Any]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    selected_rule_path = Path(selected_rule)
    rule_payload = json.loads(selected_rule_path.read_text(encoding="utf-8"))

    validation_trades = select_quantile_trades(
        _load_predictions(validation_predictions),
        _load_predictions(baseline_validation_predictions),
        rule_payload,
    )
    validation_summary = evaluate_split(validation_trades, split="validation")
    validation_summary["gate"] = decide_hold12_gate(
        hold24_pf=validation_summary["hold24"]["pf"],
        hold12_pf=validation_summary["hold12"]["pf"],
        hold24_mean_pnl_atr=validation_summary["hold24"]["mean_pnl_atr"],
        hold12_mean_pnl_atr=validation_summary["hold12"]["mean_pnl_atr"],
        hold12_n_trades=validation_summary["hold12"]["n_trades"],
        hold12_negative_year_slices=validation_summary["negative_year_slices_hold12"],
        seed_pf_values=[],
    )

    if validation_summary["gate"]["verdict"] == "gate_pass":
        test_trades = select_quantile_trades(
            _load_predictions(test_predictions),
            _load_predictions(baseline_test_predictions),
            rule_payload,
        )
        test_summary = evaluate_split(test_trades, split="test")
        test_summary["gate"] = decide_hold12_gate(
            hold24_pf=test_summary["hold24"]["pf"],
            hold12_pf=test_summary["hold12"]["pf"],
            hold24_mean_pnl_atr=test_summary["hold24"]["mean_pnl_atr"],
            hold12_mean_pnl_atr=test_summary["hold12"]["mean_pnl_atr"],
            hold12_n_trades=test_summary["hold12"]["n_trades"],
            hold12_negative_year_slices=test_summary["negative_year_slices_hold12"],
            seed_pf_values=[],
        )
    else:
        test_summary = _build_skipped_test_summary(
            "validation_gate_failed"
        )

    yearly_rows = [
        {"split": "validation", **row} for row in validation_summary["yearly"]
    ] + [{"split": "test", **row} for row in test_summary["yearly"]]
    pd.DataFrame(yearly_rows).to_csv(
        output_path / "yearly_breakdown.csv", sep=";", index=False
    )

    _write_json(output_path / "validation_summary.json", validation_summary)
    _write_json(output_path / "test_summary.json", test_summary)
    _write_json(
        output_path / "run_metadata.json",
        {
            "validation_predictions": validation_predictions,
            "test_predictions": test_predictions,
            "baseline_validation_predictions": baseline_validation_predictions,
            "baseline_test_predictions": baseline_test_predictions,
            "selected_rule": selected_rule,
            "output_dir": output_dir,
            "selected_rule_payload": rule_payload,
        },
    )

    return {"validation": validation_summary, "test": test_summary}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validation-predictions", required=True)
    parser.add_argument("--test-predictions", required=True)
    parser.add_argument("--baseline-validation-predictions", required=True)
    parser.add_argument("--baseline-test-predictions", required=True)
    parser.add_argument("--selected-rule", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args(argv)

    try:
        run_benchmark(
            validation_predictions=args.validation_predictions,
            test_predictions=args.test_predictions,
            baseline_validation_predictions=args.baseline_validation_predictions,
            baseline_test_predictions=args.baseline_test_predictions,
            selected_rule=args.selected_rule,
            output_dir=args.output_dir,
        )
    except (OSError, ValueError, KeyError, json.JSONDecodeError, pd.errors.ParserError):
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
