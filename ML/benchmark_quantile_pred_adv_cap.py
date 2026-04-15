from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from ML.benchmark_quantile_ny_session import (
    build_yearly_breakdown as _build_yearly_breakdown,
    evaluate_split as _evaluate_split,
    select_quantile_trades as _select_quantile_trades,
)


ADV_COLUMN = "pred_adv_12_atr"
DEFAULT_PNL_COLUMN = "pnl_hold24_atr"
DEFAULT_OUTPUT_DIR = Path("ML/reports/quantile_pred_adv_cap")
DEFAULT_ROOT_DIR = Path("ML/reports/entry_path_v1_quantile_robustness")
DEFAULT_SELECTED_RULE = Path("ML/reports/entry_path_v1_quantile_selected_rule.json")
DEFAULT_SEEDS = [7, 17, 42, 77, 123]
DEFAULT_QUANTILE = 0.75
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


def select_frozen_quantile_trades(
    frame: pd.DataFrame,
    baseline_frame: pd.DataFrame,
    selected_rule: dict[str, Any],
) -> pd.DataFrame:
    return _select_quantile_trades(
        frame=frame,
        baseline_frame=baseline_frame,
        selected_rule=selected_rule,
    )


def build_yearly_breakdown(
    frame: pd.DataFrame,
    pnl_column: str = DEFAULT_PNL_COLUMN,
    min_year_trades: int = 3,
) -> tuple[pd.DataFrame, int]:
    return _build_yearly_breakdown(
        frame=frame,
        pnl_column=pnl_column,
        min_year_trades=min_year_trades,
    )


def evaluate_split(
    frame: pd.DataFrame,
    split: str,
    pnl_column: str = DEFAULT_PNL_COLUMN,
    min_year_trades: int = 3,
) -> dict[str, Any]:
    return _evaluate_split(
        frame=frame,
        split=split,
        pnl_column=pnl_column,
        min_year_trades=min_year_trades,
    )


def build_validation_first_adv_cap(
    *,
    validation_frame: pd.DataFrame,
    validation_baseline_frame: pd.DataFrame,
    test_frame: pd.DataFrame,
    test_baseline_frame: pd.DataFrame,
    selected_rule: dict[str, Any],
    quantile: float = 0.75,
) -> dict[str, Any]:
    validation_selected = select_frozen_quantile_trades(
        frame=validation_frame,
        baseline_frame=validation_baseline_frame,
        selected_rule=selected_rule,
    )
    validation_threshold = compute_adv_threshold(validation_selected, quantile=quantile)
    validation_filtered = filter_by_adv_cap(validation_selected, threshold=validation_threshold)

    test_selected = select_frozen_quantile_trades(
        frame=test_frame,
        baseline_frame=test_baseline_frame,
        selected_rule=selected_rule,
    )
    test_filtered = filter_by_adv_cap(test_selected, threshold=validation_threshold)

    return {
        "validation_threshold": validation_threshold,
        "validation_selected": validation_selected,
        "validation_filtered": validation_filtered,
        "test_selected": test_selected,
        "test_filtered": test_filtered,
        "validation_summary": evaluate_split(
            validation_filtered,
            split="validation",
            pnl_column=DEFAULT_PNL_COLUMN,
        ),
        "test_summary": evaluate_split(
            test_filtered,
            split="test",
            pnl_column=DEFAULT_PNL_COLUMN,
        ),
    }


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
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
    if pd.isna(value):
        return None
    return value


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(_json_safe(payload), indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _load_predictions(path: str | Path) -> pd.DataFrame:
    return pd.read_csv(Path(path), sep=";")


def _load_rule_payload(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _parse_seeds(raw_value: str | None) -> list[int]:
    if raw_value is None:
        return list(DEFAULT_SEEDS)
    chunks = [chunk.strip() for chunk in raw_value.split(",") if chunk.strip()]
    if not chunks:
        raise ValueError("seeds must not be empty")
    return [int(chunk) for chunk in chunks]


def _empty_metrics_frame() -> pd.DataFrame:
    return pd.DataFrame({"time": pd.Series(dtype="object"), DEFAULT_PNL_COLUMN: pd.Series(dtype="float64")})


def _empty_split_summary(split: str, validation_threshold: float, reason: str) -> dict[str, Any]:
    empty_metrics = evaluate_split(_empty_metrics_frame(), split=split, pnl_column=DEFAULT_PNL_COLUMN)
    return {
        "split": split,
        "status": "skipped_due_to_validation_gate",
        "skip_reason": reason,
        "validation_threshold": validation_threshold,
        "baseline": empty_metrics,
        "filtered": empty_metrics,
        "gate": {
            "verdict": "skipped_due_to_validation_gate",
            "reasons": [reason],
        },
    }


def _summarize_filtered_split(
    *,
    split: str,
    validation_threshold: float,
    selected: pd.DataFrame,
    filtered: pd.DataFrame,
    seed_pf_values: list[float],
) -> dict[str, Any]:
    baseline_metrics = evaluate_split(selected, split=split, pnl_column=DEFAULT_PNL_COLUMN)
    filtered_metrics = evaluate_split(filtered, split=split, pnl_column=DEFAULT_PNL_COLUMN)
    gate = decide_adv_cap_gate(
        baseline_pf=baseline_metrics["pf"],
        filtered_pf=filtered_metrics["pf"],
        filtered_n_trades=filtered_metrics["n_trades"],
        filtered_negative_year_slices=filtered_metrics["negative_year_slices"],
        seed_pf_values=seed_pf_values,
    )
    return {
        "split": split,
        "status": "evaluated",
        "validation_threshold": validation_threshold,
        "baseline": baseline_metrics,
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


def _seed_summary_rows(
    *,
    root_dir: Path,
    seeds: list[int],
    selected_rule: dict[str, Any],
    baseline_validation_predictions: str | Path,
    baseline_test_predictions: str | Path,
    validation_threshold: float,
) -> tuple[pd.DataFrame, list[float]]:
    root_dir = Path(root_dir)
    rows: list[dict[str, Any]] = []
    validation_seed_pf_values: list[float] = []
    baseline_validation_frame = _load_predictions(baseline_validation_predictions)
    baseline_test_frame = _load_predictions(baseline_test_predictions)

    for seed in seeds:
        seed_dir = root_dir / f"seed_{seed:03d}"
        validation_path = seed_dir / "entry_path_v1_quantile_validation_predictions.csv"
        test_path = seed_dir / "entry_path_v1_quantile_test_predictions.csv"
        if not validation_path.exists() or not test_path.exists():
            raise FileNotFoundError(f"missing seed artifacts for seed {seed}")

        validation_selected = select_frozen_quantile_trades(
            frame=_load_predictions(validation_path),
            baseline_frame=baseline_validation_frame,
            selected_rule=selected_rule,
        )
        validation_filtered = filter_by_adv_cap(
            validation_selected,
            threshold=validation_threshold,
        )
        validation_summary = _summarize_filtered_split(
            split="validation",
            validation_threshold=validation_threshold,
            selected=validation_selected,
            filtered=validation_filtered,
            seed_pf_values=[],
        )

        test_selected = select_frozen_quantile_trades(
            frame=_load_predictions(test_path),
            baseline_frame=baseline_test_frame,
            selected_rule=selected_rule,
        )
        test_filtered = filter_by_adv_cap(
            test_selected,
            threshold=validation_threshold,
        )
        test_summary = _summarize_filtered_split(
            split="test",
            validation_threshold=validation_threshold,
            selected=test_selected,
            filtered=test_filtered,
            seed_pf_values=[],
        )

        validation_seed_pf_values.append(validation_summary["filtered"]["pf"])
        rows.append(
            {
                "seed": seed,
                "root_dir": str(root_dir),
                "seed_dir": str(seed_dir),
                "validation_baseline_pf": validation_summary["baseline"]["pf"],
                "validation_baseline_n_trades": validation_summary["baseline"]["n_trades"],
                "validation_filtered_pf": validation_summary["filtered"]["pf"],
                "validation_filtered_n_trades": validation_summary["filtered"]["n_trades"],
                "validation_filtered_negative_year_slices": validation_summary["filtered"]["negative_year_slices"],
                "validation_gate_verdict": validation_summary["gate"]["verdict"],
                "test_baseline_pf": test_summary["baseline"]["pf"],
                "test_baseline_n_trades": test_summary["baseline"]["n_trades"],
                "test_filtered_pf": test_summary["filtered"]["pf"],
                "test_filtered_n_trades": test_summary["filtered"]["n_trades"],
                "test_filtered_negative_year_slices": test_summary["filtered"]["negative_year_slices"],
                "test_gate_verdict": test_summary["gate"]["verdict"],
            }
        )

    return pd.DataFrame(rows), validation_seed_pf_values


def run_benchmark(
    *,
    validation_predictions: str | Path,
    test_predictions: str | Path,
    baseline_validation_predictions: str | Path,
    baseline_test_predictions: str | Path,
    selected_rule: str | Path = DEFAULT_SELECTED_RULE,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    root_dir: str | Path | None = None,
    seeds: list[int] | None = None,
    quantile: float = DEFAULT_QUANTILE,
) -> dict[str, Any]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    validation_frame = _load_predictions(validation_predictions)
    test_frame = _load_predictions(test_predictions)
    baseline_validation_frame = _load_predictions(baseline_validation_predictions)
    baseline_test_frame = _load_predictions(baseline_test_predictions)
    selected_rule_payload = _load_rule_payload(selected_rule)

    validation_selected = select_frozen_quantile_trades(
        frame=validation_frame,
        baseline_frame=baseline_validation_frame,
        selected_rule=selected_rule_payload,
    )
    validation_threshold = compute_adv_threshold(validation_selected, quantile=quantile)
    validation_filtered = filter_by_adv_cap(validation_selected, threshold=validation_threshold)

    seed_values = list(DEFAULT_SEEDS if seeds is None else seeds)
    per_seed_summary = pd.DataFrame()
    seed_validation_pf_values: list[float] = []
    if root_dir is not None:
        per_seed_summary, seed_validation_pf_values = _seed_summary_rows(
            root_dir=Path(root_dir),
            seeds=seed_values,
            selected_rule=selected_rule_payload,
            baseline_validation_predictions=baseline_validation_predictions,
            baseline_test_predictions=baseline_test_predictions,
            validation_threshold=validation_threshold,
        )

    validation_summary = _summarize_filtered_split(
        split="validation",
        validation_threshold=validation_threshold,
        selected=validation_selected,
        filtered=validation_filtered,
        seed_pf_values=seed_validation_pf_values,
    )

    if validation_summary["gate"]["verdict"] == "gate_pass":
        test_selected = select_frozen_quantile_trades(
            frame=test_frame,
            baseline_frame=baseline_test_frame,
            selected_rule=selected_rule_payload,
        )
        test_filtered = filter_by_adv_cap(test_selected, threshold=validation_threshold)
        test_summary = _summarize_filtered_split(
            split="test",
            validation_threshold=validation_threshold,
            selected=test_selected,
            filtered=test_filtered,
            seed_pf_values=[],
        )
        yearly_frames = [
            _yearly_rows("validation", "baseline", validation_selected),
            _yearly_rows("validation", "filtered", validation_filtered),
            _yearly_rows("test", "baseline", test_selected),
            _yearly_rows("test", "filtered", test_filtered),
        ]
    else:
        test_summary = _empty_split_summary(
            split="test",
            validation_threshold=validation_threshold,
            reason="validation_gate_failed",
        )
        yearly_frames = [
            _yearly_rows("validation", "baseline", validation_selected),
            _yearly_rows("validation", "filtered", validation_filtered),
        ]

    yearly_breakdown = pd.concat([frame for frame in yearly_frames if not frame.empty], ignore_index=True)

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
            "selected_rule": str(selected_rule),
            "output_dir": str(output_path),
            "root_dir": str(root_dir) if root_dir is not None else None,
            "seeds": seed_values if root_dir is not None else [],
            "quantile": quantile,
            "validation_threshold": validation_threshold,
            "validation_gate": validation_summary["gate"],
            "test_status": test_summary["status"],
        },
    )
    return {
        "validation_summary": validation_summary,
        "test_summary": test_summary,
        "yearly_breakdown": yearly_breakdown,
        "per_seed_summary": per_seed_summary,
        "run_metadata": {
            "validation_threshold": validation_threshold,
            "validation_gate": validation_summary["gate"],
            "test_status": test_summary["status"],
        },
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Benchmark frozen quantile trades with a validation-first pred_adv cap."
    )
    parser.add_argument("--validation-predictions", required=True)
    parser.add_argument("--test-predictions", required=True)
    parser.add_argument("--baseline-validation-predictions", required=True)
    parser.add_argument("--baseline-test-predictions", required=True)
    parser.add_argument("--selected-rule", required=True)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--root-dir", default=None)
    parser.add_argument("--seeds", default=None)
    parser.add_argument("--quantile", default=DEFAULT_QUANTILE, type=float)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        seeds = _parse_seeds(args.seeds) if args.seeds is not None else None
        run_benchmark(
            validation_predictions=args.validation_predictions,
            test_predictions=args.test_predictions,
            baseline_validation_predictions=args.baseline_validation_predictions,
            baseline_test_predictions=args.baseline_test_predictions,
            selected_rule=args.selected_rule,
            output_dir=args.output_dir,
            root_dir=args.root_dir,
            seeds=seeds,
            quantile=args.quantile,
        )
    except (OSError, ValueError, KeyError, json.JSONDecodeError, pd.errors.ParserError):
        return 2
    return 0


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


if __name__ == "__main__":
    raise SystemExit(main())
