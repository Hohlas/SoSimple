# =============================================================================
# Файл: prepare_entry_path_mt4_parity.py
# Назначение: Подготовка frozen `entry_path_v1_live_safe + A` export для MT4 parity.
# Обновлён: 2026-05-07
# Входные данные:
#   - validation/test prediction CSV (откуда: `ML.run_entry_path_live_safe_retrain`)
# Выходные данные:
#   - rule JSON, metadata JSON, `ml_signals.csv` (куда: `ML/reports/...` и MT4 paths)
# Использование:
#   python -m ML.prepare_entry_path_mt4_parity --copy-to-mt4
# Примечания:
#   - фиксирует только candidate A; auto-winner B/B_no_path6 здесь не используется.
# =============================================================================

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

from API.export_entry_path_v1_signals import export_signals
from ML.benchmark_entry_path_trade_filter import evaluate_frozen_threshold
from ML.benchmark_entry_path_trade_filter import evaluate_score_grid
from ML.benchmark_entry_path_trade_filter import load_prediction_frame
from ML.entry_path_trade_filter import build_candidate_a_score
from ML.entry_path_trade_filter import run_sequential_check


DEFAULT_ROOT = Path("ML/reports/entry_path_v1_live_safe_xauusd_no_predict_pool_server_multiseed/seed_042")
DEFAULT_OUTPUT_DIR = Path("ML/reports/mt4_entry_path_v1_live_safe_parity")


def _jsonable(value):
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "tolist"):
        return value.tolist()
    if hasattr(value, "item"):
        return value.item()
    return value


def _coverage_slug(target_coverage: float) -> str:
    return f"a{int(round(float(target_coverage) * 1000)):03d}"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _signal_counts(path: Path) -> dict[str, int]:
    frame = pd.read_csv(path, sep=";", usecols=["signal"])
    signals = pd.to_numeric(frame["signal"], errors="coerce").fillna(0).astype(int)
    return {
        "rows": int(len(signals)),
        "nonzero_signals": int((signals != 0).sum()),
        "buy_signals": int((signals > 0).sum()),
        "sell_signals": int((signals < 0).sum()),
    }


def prepare_parity_export(
    *,
    validation_csv: str | Path,
    test_csv: str | Path,
    output_dir: str | Path,
    target_coverage: float = 0.075,
    min_period_trades: int = 10,
    sequential_hold_bars: int = 24,
    copy_to_mt4: bool = False,
) -> dict[str, object]:
    validation_path = Path(validation_csv)
    test_path = Path(test_csv)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    validation_frame = load_prediction_frame(validation_path)
    test_frame = load_prediction_frame(test_path)
    validation_score = build_candidate_a_score(validation_frame)
    test_score = build_candidate_a_score(test_frame)

    validation_row = evaluate_score_grid(
        frame=validation_frame,
        score=validation_score,
        candidate="A",
        target_coverages=[target_coverage],
        min_period_trades=min_period_trades,
    ).iloc[0].to_dict()
    threshold = float(validation_row["score_threshold"])

    test_row = evaluate_frozen_threshold(
        frame=test_frame,
        score=test_score,
        candidate="A",
        threshold=threshold,
        target_coverage=target_coverage,
        min_period_trades=min_period_trades,
    ).iloc[0].to_dict()

    selected_mask = pd.Series(test_score, index=test_frame.index, dtype="float64") >= threshold
    selected_mask.loc[test_frame["signal"].to_numpy() == 0] = False
    sequential_summary = run_sequential_check(
        frame=test_frame,
        selected_mask=selected_mask,
        hold_bars=sequential_hold_bars,
    )

    slug = _coverage_slug(target_coverage)
    rule_path = output_path / f"entry_path_v1_live_safe_{slug}_rule.json"
    signals_path = output_path / "ml_signals.csv"
    metadata_path = output_path / "metadata.json"

    rule_payload = {
        "winner": validation_row,
        "coverage_grid": [float(target_coverage)],
        "validation_csv": str(validation_path),
        "test_csv": str(test_path),
        "sequential_hold_bars": int(sequential_hold_bars),
        "min_period_trades": int(min_period_trades),
        "test_summary": test_row,
        "sequential_summary": sequential_summary,
        "mt4_contract": {
            "symbol_period": "XAUUSD60",
            "entry": "next_bar_open",
            "exit_mode": "timeout",
            "hold_bars": int(sequential_hold_bars),
            "max_positions": 1,
            "take_profit_atr": 0,
            "back_stop_atr": 999,
            "allow_reversal": 0,
            "score_filter": 0,
        },
    }
    rule_path.write_text(json.dumps(_jsonable(rule_payload), ensure_ascii=False, indent=2), encoding="utf-8")

    export_signals(
        predictions_path=test_path,
        rule_path=rule_path,
        output_path=signals_path,
        copy_to_mt4=copy_to_mt4,
    )

    metadata = {
        "label": "entry_path_v1_live_safe_a075_mt4_parity",
        "rule_path": str(rule_path),
        "signals_path": str(signals_path),
        "validation_csv": str(validation_path),
        "test_csv": str(test_path),
        "target_coverage": float(target_coverage),
        "score_threshold": threshold,
        "validation": validation_row,
        "test": test_row,
        "sequential": sequential_summary,
        "signals_sha256": _sha256(signals_path),
    }
    metadata.update(_signal_counts(signals_path))
    metadata_path.write_text(json.dumps(_jsonable(metadata), ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "rule_path": str(rule_path),
        "signals_path": str(signals_path),
        "metadata_path": str(metadata_path),
        **metadata,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare entry_path_v1_live_safe A-rule export for MT4 parity.")
    parser.add_argument("--validation-csv", default=str(DEFAULT_ROOT / "validation_predictions.csv"))
    parser.add_argument("--test-csv", default=str(DEFAULT_ROOT / "test_predictions.csv"))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--target-coverage", type=float, default=0.075)
    parser.add_argument("--min-period-trades", type=int, default=10)
    parser.add_argument("--sequential-hold-bars", type=int, default=24)
    parser.add_argument("--copy-to-mt4", action="store_true")
    return parser.parse_args()


def main() -> dict[str, object]:
    args = parse_args()
    result = prepare_parity_export(
        validation_csv=args.validation_csv,
        test_csv=args.test_csv,
        output_dir=args.output_dir,
        target_coverage=args.target_coverage,
        min_period_trades=args.min_period_trades,
        sequential_hold_bars=args.sequential_hold_bars,
        copy_to_mt4=args.copy_to_mt4,
    )
    print(json.dumps(_jsonable(result), ensure_ascii=False, indent=2))
    return result


if __name__ == "__main__":
    main()
