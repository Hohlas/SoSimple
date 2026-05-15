# =============================================================================
# Файл: benchmark_entry_path_fractal_level_signal.py
# Назначение: Staged benchmark fractal-level candidate-source для entry path.
# Обновлён: 2026-05-15
# Входные данные:
#   - DATA/Nero_XAUUSD_*_labeled.csv, prediction CSV, OHLC CSV
# Выходные данные:
#   - gate artifacts и benchmark reports (куда: ML/reports/entry_path_v1_fractal_level_signal/)
# Использование:
#   python -m ML.benchmark_entry_path_fractal_level_signal --stage feature-audit
# Примечания:
#   - Stage feature-audit читает только current-row поля time/ATR/fractal0..fractal99.
# =============================================================================

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ML.fractal_level_feature_builder import audit_fractal_rows
from ML.fractal_level_feature_builder import build_feature_contract
from ML.entry_path_level_targets import summarize_direction_baseline


DEFAULT_ROOT = Path("ML/reports/entry_path_v1_live_safe_xauusd_no_predict_pool_server_multiseed/seed_042")
DEFAULT_TRAIN_SOURCE = Path("DATA/Nero_XAUUSD_train_labeled.csv")
DEFAULT_VALIDATION_SOURCE = Path("DATA/Nero_XAUUSD_validation_labeled.csv")
DEFAULT_TEST_SOURCE = Path("DATA/Nero_XAUUSD_test_labeled.csv")
DEFAULT_VALIDATION_PREDICTIONS = DEFAULT_ROOT / "validation_predictions.csv"
DEFAULT_TEST_PREDICTIONS = DEFAULT_ROOT / "test_predictions.csv"
DEFAULT_OHLC = Path("DATA/XAUUSD_H1_OHLC.csv")
DEFAULT_OUTPUT_DIR = Path("ML/reports/entry_path_v1_fractal_level_signal")


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if hasattr(value, "item"):
        return value.item()
    return value


def _audit_usecols() -> list[str]:
    return ["time", "ATR", *[f"fractal{idx}" for idx in range(100)]]


def _load_audit_source(path: str | Path) -> pd.DataFrame:
    return pd.read_csv(Path(path), sep=";", usecols=_audit_usecols())


def run_feature_audit(
    *,
    train_source: str | Path,
    validation_source: str | Path,
    test_source: str | Path,
    output_dir: str | Path,
) -> dict[str, Any]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    split_paths = {
        "train": Path(train_source),
        "validation": Path(validation_source),
        "test": Path(test_source),
    }
    split_audits = {
        split: audit_fractal_rows(_load_audit_source(path))
        for split, path in split_paths.items()
    }
    aggregate = {
        "row_count": sum(int(item["row_count"]) for item in split_audits.values()),
        "missing_invalid_fractal0_rows": sum(int(item["missing_invalid_fractal0_rows"]) for item in split_audits.values()),
        "future_fractal_rows": sum(int(item["future_fractal_rows"]) for item in split_audits.values()),
        "unknown_time_format_rows": sum(int(item["unknown_time_format_rows"]) for item in split_audits.values()),
        "fractal0_updn_nonzero_rows": sum(int(item["fractal0_updn_nonzero_rows"]) for item in split_audits.values()),
        "old_updn_nonzero_rows": sum(int(item["old_updn_nonzero_rows"]) for item in split_audits.values()),
        "sort_violation_rows": sum(int(item["sort_violation_rows"]) for item in split_audits.values()),
    }
    aggregate["old_updn_nonzero_share"] = (
        float(aggregate["old_updn_nonzero_rows"] / aggregate["row_count"])
        if aggregate["row_count"]
        else 0.0
    )
    aggregate["gate_pass"] = bool(
        aggregate["row_count"] > 0
        and aggregate["missing_invalid_fractal0_rows"] == 0
        and aggregate["future_fractal_rows"] == 0
        and aggregate["unknown_time_format_rows"] == 0
        and aggregate["sort_violation_rows"] == 0
    )

    feature_audit = {
        "stage": "feature-audit",
        "inputs": {name: str(path) for name, path in split_paths.items()},
        "usecols": _audit_usecols(),
        "ignored_offline_columns": ["signal", "predict", "ret_*", "fav_*", "adv_*"],
        "splits": split_audits,
        "aggregate": aggregate,
    }
    feature_contract = {
        "stage": "feature-audit",
        "feature_contract": build_feature_contract(fractal_count=100),
    }

    audit_path = output_path / "feature_audit.json"
    contract_path = output_path / "feature_contract.json"
    audit_path.write_text(json.dumps(_jsonable(feature_audit), ensure_ascii=False, indent=2), encoding="utf-8")
    contract_path.write_text(json.dumps(_jsonable(feature_contract), ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "feature_audit_path": str(audit_path),
        "feature_contract_path": str(contract_path),
        **feature_audit,
    }


def run_direction_baseline(
    *,
    train_source: str | Path,
    validation_source: str | Path,
    ohlc: str | Path,
    output_dir: str | Path,
    horizon: int = 24,
) -> dict[str, Any]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    usecols = ["time", "ATR", "fractal0"]
    train = pd.read_csv(Path(train_source), sep=";", usecols=usecols)
    validation = pd.read_csv(Path(validation_source), sep=";", usecols=usecols)
    payload = {
        "stage": "direction-baseline",
        "inputs": {
            "train": str(train_source),
            "validation": str(validation_source),
            "ohlc": str(ohlc),
        },
        "horizon": int(horizon),
        "test_set_used": False,
        "train_diagnostic": summarize_direction_baseline(train, ohlc, horizon=horizon),
        "validation_gate": summarize_direction_baseline(validation, ohlc, horizon=horizon),
    }
    payload["gate_pass"] = bool(payload["validation_gate"]["gate_pass"])
    output_file = output_path / "direction_baseline.json"
    output_file.write_text(json.dumps(_jsonable(payload), ensure_ascii=False, indent=2), encoding="utf-8")
    return {"direction_baseline_path": str(output_file), **payload}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Entry path fractal-level signal benchmark.")
    parser.add_argument("--stage", choices=["feature-audit", "direction-baseline"], required=True)
    parser.add_argument("--train-source", default=str(DEFAULT_TRAIN_SOURCE))
    parser.add_argument("--validation-source", default=str(DEFAULT_VALIDATION_SOURCE))
    parser.add_argument("--test-source", default=str(DEFAULT_TEST_SOURCE))
    parser.add_argument("--validation-predictions", default=str(DEFAULT_VALIDATION_PREDICTIONS))
    parser.add_argument("--test-predictions", default=str(DEFAULT_TEST_PREDICTIONS))
    parser.add_argument("--ohlc", default=str(DEFAULT_OHLC))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--horizon", type=int, default=24)
    return parser.parse_args()


def main() -> dict[str, Any]:
    args = parse_args()
    if args.stage == "feature-audit":
        result = run_feature_audit(
            train_source=args.train_source,
            validation_source=args.validation_source,
            test_source=args.test_source,
            output_dir=args.output_dir,
        )
    elif args.stage == "direction-baseline":
        result = run_direction_baseline(
            train_source=args.train_source,
            validation_source=args.validation_source,
            ohlc=args.ohlc,
            output_dir=args.output_dir,
            horizon=args.horizon,
        )
    else:
        raise ValueError(f"unsupported stage: {args.stage}")
    print(json.dumps(_jsonable(result), ensure_ascii=False, indent=2))
    return result


if __name__ == "__main__":
    main()
