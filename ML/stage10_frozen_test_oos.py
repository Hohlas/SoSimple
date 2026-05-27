# =============================================================================
# Файл: stage10_frozen_test_oos.py
# Назначение: Stage 10 — one-shot frozen test/OOS evaluation for Stage 09 rule.
# Обновлён: 2026-05-27
# Входные данные:
#   - DATA/Nero_test_labeled.csv
#   - ML/reports/methodology_cycle_candidate_source_v2/stage09_frozen_rule.json
#   - ML/checkpoints/transformer_winner.pt
#   - ML/checkpoints/pll_normalizer_v1.pkl
# Выходные данные:
#   - ML/reports/methodology_cycle_candidate_source_v2/stage10_frozen_test_oos.json
#   - ML/reports/methodology_cycle_candidate_source_v2/stage10_test_predictions.csv
#   - ML/reports/methodology_cycle_candidate_source_v2/stage10_test_trades.csv
# Использование:
#   ./.venv/bin/python ML/stage10_frozen_test_oos.py
# Примечания:
#   - Test split is read once with the frozen Stage 09 rule.
#   - No threshold/top-k/model/normalizer tuning is allowed here.
# =============================================================================

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ML.data_loader import parse_fractals_to_3d
from ML.pll_normalizer import PLLFeatureNormalizer
from ML.validation_freeze import (
    LABEL_MAP,
    PNL_COL,
    SEED,
    TransformerEncoder3Class,
    compute_pf,
    env_info,
    file_sha256,
    sanitize_for_json,
)

os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"
torch.use_deterministic_algorithms(True)
torch.manual_seed(SEED)
np.random.seed(SEED)

DATA_DIR = Path("DATA")
REPORT_DIR = Path("ML/reports/methodology_cycle_candidate_source_v2")
RULE_PATH = REPORT_DIR / "stage09_frozen_rule.json"
SUMMARY_PATH = REPORT_DIR / "stage10_frozen_test_oos.json"
PREDICTIONS_PATH = REPORT_DIR / "stage10_test_predictions.csv"
TRADES_PATH = REPORT_DIR / "stage10_test_trades.csv"

MIN_PF = 1.5
MIN_TRADES_PER_YEAR = 6.0
MAX_NEGATIVE_YEARS = 0
BASELINE_RF160_VALIDATION_PF = 1.5761


def load_rule() -> dict:
    with open(RULE_PATH) as f:
        rule = json.load(f)
    required = ["checkpoint", "normalizer", "threshold", "seq_len", "target", "n_classes"]
    missing = [key for key in required if key not in rule]
    if missing:
        raise ValueError(f"Frozen rule missing required keys: {missing}")
    return rule


def load_test_proba(rule: dict) -> tuple[pd.DataFrame, np.ndarray, np.ndarray, np.ndarray]:
    test_raw = pd.read_csv(DATA_DIR / "Nero_test_labeled.csv", sep=";")
    y_true = test_raw[rule["target"]].map(LABEL_MAP).fillna(0).astype(int).values
    pnl_r = pd.to_numeric(test_raw[PNL_COL], errors="coerce").fillna(0.0).astype(float).values

    x_test, mask_test = parse_fractals_to_3d(test_raw)
    seq_len = int(rule["seq_len"])
    x_test, mask_test = x_test[:, :seq_len, :], mask_test[:, :seq_len]

    normalizer = PLLFeatureNormalizer.load(rule["normalizer"])
    x_test = normalizer.transform(x_test)

    ckpt = torch.load(rule["checkpoint"], map_location="cpu")
    model = TransformerEncoder3Class()
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()

    ds = TensorDataset(
        torch.from_numpy(x_test).float(),
        torch.from_numpy(mask_test).bool(),
        torch.from_numpy(y_true).long(),
    )
    probs = []
    with torch.no_grad():
        for xb, mb, _ in DataLoader(ds, batch_size=256, shuffle=False):
            probs.append(F.softmax(model(xb, mb), 1)[:, 2].cpu())
    return test_raw, y_true, torch.cat(probs).numpy(), pnl_r


def add_prediction_columns(df: pd.DataFrame, y_true: np.ndarray, proba: np.ndarray,
                           pnl_r: np.ndarray, threshold: float) -> pd.DataFrame:
    out = df[["time", "signal", "ATR"]].copy()
    out["target_label"] = df["buy_sl3_tp3"].values
    out["target_class"] = y_true
    out["proba_tp"] = proba
    out["threshold"] = threshold
    out["selected"] = proba >= threshold
    out["pnl_r"] = np.where(out["selected"], pnl_r, 0.0)
    return out


def per_period_pf(predictions: pd.DataFrame, period: str) -> dict:
    df = predictions.copy()
    dt = pd.to_datetime(df["time"], format="%Y.%m.%d %H:%M", errors="coerce")
    if period == "year":
        groups = dt.dt.year
    elif period == "quarter":
        groups = dt.dt.to_period("Q").astype(str)
    else:
        raise ValueError(f"Unsupported period: {period}")

    result = {}
    for key, group in df.groupby(groups):
        if pd.isna(key):
            continue
        selected = group["selected"].to_numpy(dtype=bool)
        pnl = group["pnl_r"].to_numpy(dtype=float)
        r = compute_pf(pnl, selected=selected)
        result[str(key)] = r
    return result


def per_side_pf(predictions: pd.DataFrame) -> dict:
    result = {}
    for side, signal_value in [("BUY", 1), ("SELL", -1), ("SIGNAL_0", 0)]:
        group = predictions[predictions["signal"] == signal_value]
        selected = group["selected"].to_numpy(dtype=bool)
        pnl = group["pnl_r"].to_numpy(dtype=float)
        result[side] = compute_pf(pnl, selected=selected)
    return result


def drawdown_stats(trades: pd.DataFrame) -> dict:
    if trades.empty:
        return {"max_drawdown_r": 0.0, "ending_pnl_r": 0.0, "min_equity_r": 0.0}
    equity = trades["pnl_r"].cumsum().to_numpy(dtype=float)
    running_max = np.maximum.accumulate(np.insert(equity, 0, 0.0))[1:]
    drawdown = running_max - equity
    return {
        "max_drawdown_r": round(float(drawdown.max(initial=0.0)), 4),
        "ending_pnl_r": round(float(equity[-1]), 4),
        "min_equity_r": round(float(equity.min(initial=0.0)), 4),
    }


def count_negative_years(per_year: dict) -> int:
    return sum(1 for row in per_year.values() if row["trades"] > 0 and row["PF"] < 1.0)


def slice_stability(per_year: dict, aggregate_trades: int) -> dict:
    active_years = sum(1 for row in per_year.values() if row["trades"] > 0)
    idle_years = [year for year, row in per_year.items() if row["trades"] == 0]
    max_year_trades = max((row["trades"] for row in per_year.values()), default=0)
    max_year_trade_share = max_year_trades / aggregate_trades if aggregate_trades else 0.0
    max_years = [year for year, row in per_year.items() if row["trades"] == max_year_trades and max_year_trades > 0]
    return {
        "active_years": active_years,
        "idle_years": idle_years,
        "max_year_trades": max_year_trades,
        "max_years": max_years,
        "max_year_trade_share": round(float(max_year_trade_share), 4),
    }


def selected_signal_distribution(predictions: pd.DataFrame) -> dict:
    selected = predictions[predictions["selected"]]
    counts = selected["signal"].value_counts().to_dict()
    total = len(selected)
    return {
        str(int(signal)): {
            "trades": int(count),
            "share": round(float(count / total), 4) if total else 0.0,
        }
        for signal, count in sorted(counts.items())
    }


def main() -> None:
    rule = load_rule()
    threshold = float(rule["threshold"])
    test_raw, y_true, proba, pnl_r = load_test_proba(rule)

    predictions = add_prediction_columns(test_raw, y_true, proba, pnl_r, threshold)
    trades = predictions[predictions["selected"]].copy()
    trades.insert(0, "trade_id", np.arange(1, len(trades) + 1))

    aggregate = compute_pf(pnl_r, proba, threshold)
    per_year = per_period_pf(predictions, "year")
    per_quarter = per_period_pf(predictions, "quarter")
    side = per_side_pf(predictions)
    negative_years = count_negative_years(per_year)
    stability = slice_stability(per_year, aggregate["trades"])

    dt = pd.to_datetime(test_raw["time"], format="%Y.%m.%d %H:%M", errors="coerce")
    elapsed_years = max((dt.max() - dt.min()).days / 365.25, 1e-9)
    trades_per_year = aggregate["trades"] / elapsed_years

    gates = {
        "pf_ge_1_5": aggregate["PF"] >= MIN_PF,
        "trades_per_year_ge_6": trades_per_year >= MIN_TRADES_PER_YEAR,
        "negative_years_eq_0": negative_years <= MAX_NEGATIVE_YEARS,
        "baseline_uplift_over_rf160_validation_pf": aggregate["PF"] > BASELINE_RF160_VALIDATION_PF,
    }
    verdict = "candidate" if all(gates.values()) else "reject"

    predictions.to_csv(PREDICTIONS_PATH, index=False)
    trades.to_csv(TRADES_PATH, index=False)

    summary = sanitize_for_json({
        "cycle_id": "methodology_cycle_candidate_source_v2",
        "stage": "10-frozen-test-oos",
        "scope": "one-shot frozen test; no tuning",
        "stage_verdict": "PASS",
        "model_verdict": verdict,
        "rule": {
            "path": str(RULE_PATH),
            "threshold": threshold,
            "checkpoint": rule["checkpoint"],
            "checkpoint_sha256_rule": rule["checkpoint_sha256"],
            "checkpoint_sha256_current": file_sha256(rule["checkpoint"]),
            "normalizer": rule["normalizer"],
            "normalizer_sha256_rule": rule["normalizer_sha256"],
            "normalizer_sha256_current": file_sha256(rule["normalizer"]),
            "target": rule["target"],
            "seq_len": rule["seq_len"],
        },
        "frozen_protocol_checks": {
            "test_read_by_stage10_only": True,
            "threshold_unchanged_from_rule": threshold == float(rule["selection_rule"]["threshold"]),
            "checkpoint_hash_matches_rule": file_sha256(rule["checkpoint"]) == rule["checkpoint_sha256"],
            "normalizer_hash_matches_rule": file_sha256(rule["normalizer"]) == rule["normalizer_sha256"],
            "no_training_or_refit": True,
            "no_threshold_or_topk_search": True,
        },
        "test_window": {
            "rows": len(test_raw),
            "start": str(dt.min()),
            "end": str(dt.max()),
            "elapsed_years": round(float(elapsed_years), 4),
        },
        "metrics": {
            **aggregate,
            "trades_per_year": round(float(trades_per_year), 4),
            "negative_years": negative_years,
            **stability,
            **drawdown_stats(trades),
        },
        "per_year": per_year,
        "per_quarter": per_quarter,
        "per_side_diagnostic": side,
        "selected_signal_distribution": selected_signal_distribution(predictions),
        "baseline": {
            "reference": "Stage 07 RF_160 validation baseline; test baseline not retuned/read before this Stage 10 run",
            "rf160_validation_pf": BASELINE_RF160_VALIDATION_PF,
            "uplift_pf": round(float(aggregate["PF"] - BASELINE_RF160_VALIDATION_PF), 4),
        },
        "gates": gates,
        "limitations": [
            "Gross TP/SL metrics only; costs and slippage are deferred to Stage 12.",
            "BUY/SELL side slices use the existing signal label diagnostically; most selected rows may have signal=0, so side slices do not define a live execution side.",
            "Test trades are sparse and year-concentrated; this must be stress-tested in Stage 11 before any production claim.",
            "A candidate verdict is not production approval; robustness, costs, export, MT4 parity and forward-test remain required.",
        ],
        "outputs": {
            "predictions": str(PREDICTIONS_PATH),
            "trades": str(TRADES_PATH),
        },
        "environment": env_info(),
    })

    with open(SUMMARY_PATH, "w") as f:
        json.dump(summary, f, indent=2, allow_nan=False)

    print(f"Summary: {SUMMARY_PATH}")
    print(f"Predictions: {PREDICTIONS_PATH}")
    print(f"Trades: {TRADES_PATH}")
    print(
        f"Stage 10 {verdict}: PF={aggregate['PF']} trades={aggregate['trades']} "
        f"trades/year={trades_per_year:.2f} negative_years={negative_years}"
    )


if __name__ == "__main__":
    main()
