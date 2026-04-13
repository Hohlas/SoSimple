from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import pandas as pd

from API.export_entry_path_v1_quantile_signals import (
    apply_production_rule,
    load_rule_payload_from_file,
)


DEFAULT_VALIDATION_CSV = Path("ML/reports/entry_path_v1_quantile_validation_predictions.csv")
DEFAULT_TEST_CSV = Path("ML/reports/entry_path_v1_quantile_test_predictions.csv")
DEFAULT_RULE_PATH = Path("ML/reports/entry_path_v1_quantile_selected_rule.json")
DEFAULT_OUTPUT_DIR = Path("ML/reports/quantile_execution_improvement")
DEFAULT_VARIANTS = ["baseline_24", "timeout_12"]
REQUIRED_COLUMNS = {"time", "signal", "true_ret_12_dir_atr", "true_ret_24_dir_atr"}


def apply_exit_variant(frame: pd.DataFrame, variant: str) -> pd.DataFrame:
    result = frame.copy()
    if variant == "baseline_24":
        result["pnl_atr"] = result["true_ret_24_dir_atr"].astype(float)
        return result
    if variant == "timeout_12":
        result["pnl_atr"] = result["true_ret_12_dir_atr"].astype(float)
        return result
    raise ValueError(f"unsupported variant: {variant}")


def compute_variant_metrics(frame: pd.DataFrame) -> dict[str, Any]:
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

    pnl = frame["pnl_atr"].astype(float)
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


def evaluate_variants(frame: pd.DataFrame, variants: list[str]) -> pd.DataFrame:
    rows = []
    for variant in variants:
        variant_frame = apply_exit_variant(frame, variant=variant)
        rows.append({"variant": variant, **compute_variant_metrics(variant_frame)})
    return pd.DataFrame(rows)


def choose_validation_winner(grid: pd.DataFrame) -> dict[str, Any]:
    sortable = grid.copy()
    sortable["_pf_sort"] = sortable["pf"].apply(lambda value: -math.inf if pd.isna(value) else float(value))
    ordered = sortable.sort_values(["_pf_sort", "n_trades"], ascending=[False, False], kind="stable").reset_index(drop=True)
    row = ordered.iloc[0]
    return {"variant": row["variant"], "pf": float(row["pf"]), "n_trades": int(row["n_trades"])}


def select_frozen_quantile_trades(
    frame: pd.DataFrame,
    *,
    rule_path: str | Path,
    baseline_predictions_path: str | Path,
) -> pd.DataFrame:
    rule_payload = load_rule_payload_from_file(rule_path)
    baseline_frame = pd.read_csv(Path(baseline_predictions_path), sep=";")
    selected_mask = apply_production_rule(frame, baseline_frame, rule_payload)
    return frame.loc[selected_mask].copy().reset_index(drop=True)


def _resolve_baseline_predictions_path(rule_path: str | Path, split: str) -> Path:
    raw = json.loads(Path(rule_path).read_text(encoding="utf-8"))
    baseline_rule_path = Path(raw["baseline_rule_path"])
    baseline_raw = json.loads(baseline_rule_path.read_text(encoding="utf-8"))
    key = "test_csv" if split == "test" else "validation_csv"
    return Path(baseline_raw[key])


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def _read_prediction_csv(path: str | Path) -> pd.DataFrame:
    frame = pd.read_csv(Path(path), sep=";")
    if not REQUIRED_COLUMNS.issubset(frame.columns):
        missing = ", ".join(sorted(REQUIRED_COLUMNS - set(frame.columns)))
        raise ValueError(f"missing required columns: {missing}")
    return frame


def _decide_verdict(validation_grid: pd.DataFrame, test_grid: pd.DataFrame, winner: dict[str, Any]) -> str:
    if winner["variant"] == "baseline_24":
        return "no_execution_uplift"
    validation_base = validation_grid.loc[validation_grid["variant"] == "baseline_24"].iloc[0]
    test_base = test_grid.loc[test_grid["variant"] == "baseline_24"].iloc[0]
    test_winner = test_grid.loc[test_grid["variant"] == winner["variant"]].iloc[0]
    if float(winner["pf"]) <= float(validation_base["pf"]):
        return "no_execution_uplift"
    if float(test_winner["pf"]) <= float(test_base["pf"]):
        return "no_execution_uplift"
    return "execution_uplift_candidate"


def _expected_frozen_test_trades(rule_path: str | Path) -> int | None:
    raw = json.loads(Path(rule_path).read_text(encoding="utf-8"))
    frozen = raw.get("frozen_test")
    if isinstance(frozen, dict) and "trades" in frozen:
        return int(frozen["trades"])
    winner = raw.get("winner")
    if isinstance(winner, dict) and "trades" in winner:
        return int(winner["trades"])
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Benchmark simple execution variants around frozen quantile.")
    parser.add_argument("--validation-predictions", default=str(DEFAULT_VALIDATION_CSV))
    parser.add_argument("--test-predictions", default=str(DEFAULT_TEST_CSV))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--rule-path", default=str(DEFAULT_RULE_PATH))
    parser.add_argument("--baseline-validation-predictions", default=None)
    parser.add_argument("--baseline-test-predictions", default=None)
    args = parser.parse_args(argv)

    try:
        validation_frame = _read_prediction_csv(args.validation_predictions)
        test_frame = _read_prediction_csv(args.test_predictions)
        baseline_validation = args.baseline_validation_predictions or _resolve_baseline_predictions_path(args.rule_path, "validation")
        baseline_test = args.baseline_test_predictions or _resolve_baseline_predictions_path(args.rule_path, "test")
        validation_selected = select_frozen_quantile_trades(
            validation_frame,
            rule_path=args.rule_path,
            baseline_predictions_path=baseline_validation,
        )
        test_selected = select_frozen_quantile_trades(
            test_frame,
            rule_path=args.rule_path,
            baseline_predictions_path=baseline_test,
        )
        expected_test_trades = _expected_frozen_test_trades(args.rule_path)
        if expected_test_trades is not None and len(test_selected) != expected_test_trades:
            return 2
        validation_grid = evaluate_variants(validation_selected, DEFAULT_VARIANTS)
        test_grid = evaluate_variants(test_selected, DEFAULT_VARIANTS)
        winner = choose_validation_winner(validation_grid)
        verdict = _decide_verdict(validation_grid, test_grid, winner)
    except (OSError, ValueError, KeyError, IndexError, pd.errors.ParserError):
        return 2

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    validation_grid.to_csv(output_dir / "validation_grid.csv", sep=";", index=False)
    test_grid.to_csv(output_dir / "test_grid.csv", sep=";", index=False)

    selected = {
        **winner,
        "verdict": verdict,
        "test": test_grid.loc[test_grid["variant"] == winner["variant"]].iloc[0].to_dict(),
        "baseline_validation": validation_grid.loc[validation_grid["variant"] == "baseline_24"].iloc[0].to_dict(),
        "baseline_test": test_grid.loc[test_grid["variant"] == "baseline_24"].iloc[0].to_dict(),
    }
    metadata = {
        "validation_predictions": args.validation_predictions,
        "test_predictions": args.test_predictions,
        "rule_path": args.rule_path,
        "baseline_validation_predictions": str(baseline_validation),
        "baseline_test_predictions": str(baseline_test),
        "validation_selected_trades": int(len(validation_selected)),
        "test_selected_trades": int(len(test_selected)),
        "variants": DEFAULT_VARIANTS,
    }

    (output_dir / "selected_variant.json").write_text(
        json.dumps(_json_safe(selected), indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    (output_dir / "run_metadata.json").write_text(
        json.dumps(_json_safe(metadata), indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
