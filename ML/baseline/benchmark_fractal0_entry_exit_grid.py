# =============================================================================
# Файл: benchmark_fractal0_entry_exit_grid.py
# Назначение: Research-runner Fractal0 entry/exit и stop-policy сеток с
#   OHLC/M5-симуляцией, ML-exit слоем и перестановочной коррекцией.
# Обновлён: 2026-07-21
# Зависимости:
#   Входные данные:
#     - DATA/XAUUSD_H1_OHLC.csv
#     - MT/MQL4/Files/XAUUSD_M5_OHLC.csv (опционально для execution ordering)
#     - DATA/Nero_XAUUSD_train_labeled.csv
#     - DATA/Nero_XAUUSD_validation_labeled.csv
#     - ML/reports/entry_based_movement_filter_freeze.json
#     - ML/reports/entry_based_movement_filter_freeze_scores.csv
#   Выходные данные:
#     - ML/reports/fractal0_entry_exit_grid*.json/csv
#     - ML/reports/fractal0_stop_grid_m5*.json/csv
# Использование:
#   ./.venv/bin/python ML/baseline/benchmark_fractal0_entry_exit_grid.py --threads 24
#   ./.venv/bin/python ML/baseline/benchmark_fractal0_entry_exit_grid.py --exit-shortlist stop_grid --skip-stress-spread
# Примечания:
#   - locked_test не открывается; результат не выше research_only.
# =============================================================================
from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import math
import os
import tempfile
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesClassifier

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclasses.dataclass(frozen=True)
class Fractal0EntryExitGridConfig:
    experiment: str = "fractal0_entry_exit_grid"
    lifecycle_status: str = "research_scan"
    allowed_max_verdict: str = "research_only"
    locked_test: str = "not_opened"
    canonical_spread: float = 0.20
    stress_spread: float = 0.40
    protective_stop_atr: float = 0.5
    same_bar_tp_sl_policy: str = "SL first"
    default_threads: int = 24
    permutation_repeats: int = 200
    permutation_seed: int = 20260720
    output_prefix: str = "ML/reports/fractal0_entry_exit_grid"
    movement_freeze_json: str = "ML/reports/entry_based_movement_filter_freeze.json"
    movement_freeze_scores: str = "ML/reports/entry_based_movement_filter_freeze_scores.csv"
    ohlc_path: str = "DATA/XAUUSD_H1_OHLC.csv"
    execution_ohlc_path: str = ""
    train_path: str = "DATA/Nero_XAUUSD_train_labeled.csv"
    validation_path: str = "DATA/Nero_XAUUSD_validation_labeled.csv"


CONFIG = Fractal0EntryExitGridConfig()
MAX_EXIT_HOLD_BARS = 24
EXIT_TARGETS = (
    "target_exit_opposite_any",
    "target_exit_opposite_strong",
    "target_exit_hold_close",
    "target_exit_movement_exhaustion",
)
EXIT_MODEL_SEEDS = (42, 43, 44)
EXIT_FEATURE_COLUMNS_BASE = [
    "bars_since_fill",
    "unrealized_pnl_r_before_decision",
    "max_favorable_r_before_decision",
    "max_adverse_r_before_decision",
    "ATR",
]
EXIT_FEATURE_COLUMNS_M1_ONLY = ["movement_score", "movement_score_available"]


def _path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else PROJECT_ROOT / path


def parse_project_time(value: object) -> pd.Timestamp:
    return pd.to_datetime(str(value).replace(".", "-", 2), errors="coerce")


def parse_ohlc_time_series(values: pd.Series) -> pd.Series:
    parsed = pd.to_datetime(values.astype(str), format="%Y.%m.%d %H:%M", errors="coerce")
    if parsed.isna().any():
        fallback = pd.to_datetime(values.astype(str).str.replace(".", "-", n=2, regex=False), errors="coerce")
        parsed = parsed.fillna(fallback)
    return parsed


def load_ohlc(config: Fractal0EntryExitGridConfig = CONFIG) -> pd.DataFrame:
    ohlc = pd.read_csv(_path(config.ohlc_path), sep=";")
    ohlc = ohlc.rename(columns={col: col.lower() for col in ohlc.columns})
    ohlc["time"] = parse_ohlc_time_series(ohlc["time"])
    return ohlc.dropna(subset=["time"]).sort_values("time").reset_index(drop=True)


def load_ohlc_path(path: str | Path) -> pd.DataFrame:
    ohlc = pd.read_csv(_path(path), sep=";")
    ohlc = ohlc.rename(columns={col: col.lower() for col in ohlc.columns})
    ohlc["time"] = parse_ohlc_time_series(ohlc["time"])
    return ohlc.dropna(subset=["time"]).sort_values("time").reset_index(drop=True)


def prepare_execution_ohlc_index(execution_ohlc: pd.DataFrame) -> pd.DataFrame:
    indexed = execution_ohlc.copy()
    indexed["_h1_time"] = pd.to_datetime(indexed["time"], errors="coerce").dt.floor("h")
    indexed = indexed.dropna(subset=["_h1_time"]).sort_values(["_h1_time", "time"])
    return indexed.set_index("_h1_time", drop=False)


def load_role_splits(config: Fractal0EntryExitGridConfig = CONFIG) -> dict[str, pd.DataFrame]:
    train = pd.read_csv(_path(config.train_path), sep=";").reset_index(drop=True)
    validation = pd.read_csv(_path(config.validation_path), sep=";").reset_index(drop=True)
    train["time"] = train["time"].map(parse_project_time)
    validation["time"] = validation["time"].map(parse_project_time)
    midpoint = len(validation) // 2
    splits = {
        "train_core": train,
        "val_select": validation.iloc[:midpoint].reset_index(drop=True),
        "val_eval": validation.iloc[midpoint:].reset_index(drop=True),
    }
    for name, frame in splits.items():
        frame["split"] = name
        frame["split_row_id"] = np.arange(len(frame), dtype=int)
    return splits


def entry_grid() -> list[dict[str, object]]:
    return [
        {"entry_id": "E0_selected_zone_edge", "entry_mode": "zone_edge", "anchor": "fractal0_price", "zone_atr": 0.5, "lag_bars": 6, "horizon": 3},
        {"entry_id": "E1_simple_limit_at_fractal0", "entry_mode": "limit_at_fractal0", "anchor": "fractal0_price", "zone_atr": 0.0, "lag_bars": 6, "horizon": 3},
        {"entry_id": "E2_open_pullback_0_5atr", "entry_mode": "open_pullback", "anchor": "calculation_open", "pullback_atr": 0.5, "lag_bars": 6, "horizon": 3},
        {"entry_id": "E3_open_pullback_1_0atr", "entry_mode": "open_pullback", "anchor": "calculation_open", "pullback_atr": 1.0, "lag_bars": 6, "horizon": 3},
    ]


STOP_GRID_EXIT_IDS = {
    "X0_fixed_r_0_7",
    "X1_ml_opposite_strong_p0_55",
    "X1_ml_opposite_strong_p0_65",
    "X1_ml_opposite_strong_p0_75",
    "X2_ml_opposite_any_p0_50",
    "X2_ml_opposite_any_p0_55",
    "X2_ml_opposite_any_p0_60",
    "X3_ml_hold_close_p0_50",
    "X3_ml_hold_close_p0_60",
    "X3_ml_hold_close_p0_70",
    "X7_time_6",
    "X7_time_12",
}
STOP_GRID_ENTRY_IDS = {"E1_simple_limit_at_fractal0", "E2_open_pullback_0_5atr", "E3_open_pullback_1_0atr"}


def exit_grid(shortlist: str | None = None) -> list[dict[str, object]]:
    out: list[dict[str, object]] = [{"exit_id": "X0_fixed_r_0_7", "family": "fixed_r", "tp_r": 0.7}]
    for t in (0.55, 0.65, 0.75):
        out.append({"exit_id": f"X1_ml_opposite_strong_p{t:.2f}".replace(".", "_"), "family": "ml_opposite_strong", "prob_threshold": t})
    for t in (0.50, 0.55, 0.60):
        out.append({"exit_id": f"X2_ml_opposite_any_p{t:.2f}".replace(".", "_"), "family": "ml_opposite_any", "prob_threshold": t})
    for t in (0.50, 0.60, 0.70):
        out.append({"exit_id": f"X3_ml_hold_close_p{t:.2f}".replace(".", "_"), "family": "ml_hold_close", "prob_threshold": t})
    for t in (0.55, 0.65, 0.75):
        out.append({"exit_id": f"X4_ml_movement_exhaustion_p{t:.2f}".replace(".", "_"), "family": "ml_movement_exhaustion", "prob_threshold": t})
    for model in ("hold_close", "movement_exhaustion"):
        for t in (0.55, 0.65, 0.75):
            out.append({"exit_id": f"X5_fixed_sl_ml_profit_exit_{model}_p{t:.2f}".replace(".", "_"), "family": "fixed_sl_ml_profit_exit", "model": model, "prob_threshold": t})
    for distance in (0.2, 2.0, 3.0, 5.0):
        for activation in (0.0, 1.0, 2.0, 3.0):
            out.append({"exit_id": f"X6_trail_atr_{distance:g}_activation_{activation:g}".replace(".", "_"), "family": "trail_atr", "trail_distance_atr": distance, "activation_atr": activation})
    for hold_bars in (1, 2, 6, 12):
        out.append({"exit_id": f"X7_time_{hold_bars}", "family": "time_exit", "hold_bars": hold_bars})
    for giveback in (0.30, 0.50, 0.70):
        for activation in (1.0, 2.0, 3.0):
            out.append({"exit_id": f"X8_giveback_{int(giveback * 100)}_activation_{activation:g}".replace(".", "_"), "family": "profit_giveback", "giveback_fraction": giveback, "activation_atr": activation})
    if shortlist == "stop_grid":
        return [item for item in out if item["exit_id"] in STOP_GRID_EXIT_IDS]
    return out


def stop_policy_grid() -> list[dict[str, object]]:
    return [
        {"stop_policy_id": "S0_current_0_5", "family": "current", "fractal0_buffer_atr": 0.5, "entry_floor_atr": 0.5},
        {"stop_policy_id": "S1_fractal0_buffer_0_5_entry_floor_1", "family": "fractal0_buffer_entry_floor", "fractal0_buffer_atr": 0.5, "entry_floor_atr": 1.0},
        {"stop_policy_id": "S2_fractal0_buffer_0_5_entry_floor_2", "family": "fractal0_buffer_entry_floor", "fractal0_buffer_atr": 0.5, "entry_floor_atr": 2.0},
        {"stop_policy_id": "S3_fractal0_buffer_0_5_entry_floor_3", "family": "fractal0_buffer_entry_floor", "fractal0_buffer_atr": 0.5, "entry_floor_atr": 3.0},
    ]


def mask_grid() -> list[dict[str, object]]:
    return [
        {"mask_id": "M0_no_mask", "kind": "none"},
        {"mask_id": "M1_frozen_movement_top5", "kind": "frozen_movement_top_fraction", "selected_fraction": 0.05},
    ]


def expanded_grid(
    active_stop_policies: list[dict[str, object]] | None = None,
    active_entries: list[dict[str, object]] | None = None,
    active_masks: list[dict[str, object]] | None = None,
    active_exits: list[dict[str, object]] | None = None,
) -> list[dict[str, object]]:
    stops = active_stop_policies or stop_policy_grid()
    entries = active_entries or entry_grid()
    masks = active_masks or mask_grid()
    exits = active_exits or exit_grid()
    return [{**stop, **entry, **mask, **exit_rule, "spread": CONFIG.canonical_spread} for stop in stops for entry in entries for mask in masks for exit_rule in exits]


def stable_json_hash(payload: dict[str, object]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str).encode()).hexdigest()


def run_config_hash(config: dict[str, object]) -> str:
    return stable_json_hash(config)


def resume_key(run: dict[str, object]) -> str:
    keys = ("stop_policy_id", "entry_id", "mask_id", "exit_id", "spread")
    if "split" in run:
        keys = (*keys, "split")
    return stable_json_hash({key: run.get(key) for key in keys})


def write_progress_atomic(path: Path, progress: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", delete=False, dir=path.parent, encoding="utf-8") as handle:
        json.dump(progress, handle, ensure_ascii=True, indent=2, default=str)
        tmp = Path(handle.name)
    tmp.replace(path)


def load_progress(path: Path, expected_hash: str) -> dict[str, object]:
    if not path.exists():
        return {"run_config_hash": expected_hash, "completed": {}, "failed": {}}
    progress = json.loads(path.read_text(encoding="utf-8"))
    if progress.get("run_config_hash") != expected_hash:
        raise ValueError("run_config_hash mismatch")
    progress.setdefault("completed", {})
    progress.setdefault("failed", {})
    return progress


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def preflight_inputs(config: Fractal0EntryExitGridConfig) -> dict[str, object]:
    errors: list[dict[str, object]] = []
    artifacts: list[dict[str, object]] = []
    freeze_json = _path(config.movement_freeze_json)
    freeze_data: dict[str, object] = {}
    if freeze_json.exists():
        freeze_data = json.loads(freeze_json.read_text(encoding="utf-8"))
        artifacts.append({"id": "movement_freeze_json", "path": str(freeze_json), "sha256": sha256_file(freeze_json)})
        missing = sorted({"verdict", "locked_test", "frozen_rule", "scores_csv"} - set(freeze_data))
        if missing:
            errors.append({"id": "movement_freeze_json", "path": str(freeze_json), "reason": "missing_keys", "missing_keys": missing})
    else:
        errors.append({"id": "movement_freeze_json", "path": str(freeze_json), "reason": "missing"})
    scores_path = _path(config.movement_freeze_scores)
    resolution = "from_config"
    if not scores_path.exists() and freeze_data.get("scores_csv"):
        candidate = _path(str(freeze_data["scores_csv"]))
        if candidate.exists():
            scores_path = candidate
            resolution = "from_freeze_json_scores_csv"
    required = [
        ("ohlc", _path(config.ohlc_path), {"time", "open", "high", "low", "close", "atr14"}, ";"),
        ("train_core", _path(config.train_path), {"time", "ATR", "fractal0"}, ";"),
        ("validation", _path(config.validation_path), {"time", "ATR", "fractal0"}, ";"),
        ("movement_freeze_scores", scores_path, {"split", "split_row_id", "time", "year", "score", "entry_movement_3", "selected"}, None),
    ]
    if config.execution_ohlc_path:
        required.append(("execution_ohlc", _path(config.execution_ohlc_path), {"time", "open", "high", "low", "close"}, ";"))
    sep_contract: dict[str, str] = {}
    for artifact_id, path, columns, sep in required:
        if not path.exists():
            errors.append({"id": artifact_id, "path": str(path), "reason": "missing"})
            continue
        actual_sep = sep or _detect_sep(path)
        sep_contract[artifact_id] = actual_sep
        header = pd.read_csv(path, nrows=0, sep=actual_sep).columns.tolist()
        missing = sorted(columns - set(header))
        if missing:
            errors.append({"id": artifact_id, "path": str(path), "reason": "missing_columns", "missing_columns": missing})
        artifacts.append({"id": artifact_id, "path": str(path), "sha256": sha256_file(path), "columns": header})
    return {
        "status": "FAIL" if errors else "PASS",
        "errors": errors,
        "input_artifacts": artifacts,
        "input_artifact_hashes": {item["id"]: item["sha256"] for item in artifacts},
        "input_path_resolution": {"movement_freeze_scores": resolution},
        "csv_separator_contract": sep_contract,
    }


def _detect_sep(path: Path) -> str:
    line = path.read_text(encoding="utf-8", errors="ignore").splitlines()[0]
    return ";" if line.count(";") >= line.count(",") else ","


def parse_fractal0(value: object) -> dict | None:
    parts = str(value).split(":")
    if len(parts) < 23:
        return None
    try:
        return {"time": int(float(parts[0])), "price": float(parts[1]), "direction": int(float(parts[2])), "shift": int(float(parts[22]))}
    except (TypeError, ValueError):
        return None


def side_from_fractal_dir(direction: object) -> str | None:
    try:
        value = float(direction)
    except (TypeError, ValueError):
        return None
    if math.isnan(value) or value == 0:
        return None
    return "BUY" if value < 0 else "SELL"


def _first_eligible_index(signal_time: pd.Timestamp, ohlc: pd.DataFrame, offset: int) -> int | None:
    times = pd.to_datetime(ohlc["time"]).to_numpy()
    idx = int(times.searchsorted(pd.Timestamp(signal_time).to_datetime64(), side="right")) + int(offset)
    return idx if idx < len(ohlc) else None


def resolve_limit_price(row: pd.Series, entry_rule: dict[str, object], calculation_open: float) -> float:
    atr = float(row.get("ATR", row.get("atr14", np.nan)))
    fractal = parse_fractal0(row.get("fractal0"))
    fractal_price = float(row.get("fractal0_price", fractal["price"] if fractal else np.nan))
    side = side_from_fractal_dir(row.get("fractal0_direction", fractal["direction"] if fractal else np.nan))
    if entry_rule["entry_mode"] == "open_pullback":
        pullback = float(entry_rule["pullback_atr"]) * atr
        return float(calculation_open - pullback if side == "BUY" else calculation_open + pullback)
    if entry_rule["entry_mode"] == "zone_edge":
        zone = float(entry_rule.get("zone_atr", 0.0)) * atr
        return float(fractal_price + zone if side == "BUY" else fractal_price - zone)
    return fractal_price


def resolve_executable_fill(side: str, signal_time: pd.Timestamp, limit_price: float, max_fill_lag_bars: int, spread: float, ohlc: pd.DataFrame, first_order_eligible_bar_offset: int = 1) -> dict[str, object]:
    start = _first_eligible_index(signal_time, ohlc, first_order_eligible_bar_offset)
    if start is None:
        return {"filled": False, "fill_index": None, "fill_time": pd.NaT, "entry_effective_price": np.nan, "entry_bid_equivalent": np.nan}
    for pos in range(start, min(start + int(max_fill_lag_bars), len(ohlc))):
        low_bid = float(ohlc.iloc[pos]["low"])
        high_bid = float(ohlc.iloc[pos]["high"])
        if side == "BUY" and low_bid + float(spread) <= float(limit_price):
            return {"filled": True, "fill_index": pos, "fill_time": pd.Timestamp(ohlc.iloc[pos]["time"]), "entry_effective_price": float(limit_price), "entry_bid_equivalent": float(limit_price) - float(spread)}
        if side == "SELL" and high_bid >= float(limit_price):
            return {"filled": True, "fill_index": pos, "fill_time": pd.Timestamp(ohlc.iloc[pos]["time"]), "entry_effective_price": float(limit_price), "entry_bid_equivalent": float(limit_price)}
    return {"filled": False, "fill_index": None, "fill_time": pd.NaT, "entry_effective_price": np.nan, "entry_bid_equivalent": np.nan}


def resolve_protective_stop(
    side: str,
    fractal0_price: float,
    entry_bid_equivalent: float,
    atr: float,
    stop_policy: dict[str, object] | None = None,
) -> dict[str, object]:
    policy = stop_policy or stop_policy_grid()[0]
    family = str(policy.get("family", "current"))
    fractal_buffer = float(policy.get("fractal0_buffer_atr", CONFIG.protective_stop_atr))
    entry_floor = float(policy.get("entry_floor_atr", CONFIG.protective_stop_atr))
    if family == "current":
        if side == "BUY":
            stop = float(min(fractal0_price, entry_bid_equivalent) - fractal_buffer * atr)
        else:
            stop = float(max(fractal0_price, entry_bid_equivalent) + fractal_buffer * atr)
        source = "current_entry_or_fractal_anchor"
    elif family == "fractal0_buffer_entry_floor":
        if side == "BUY":
            fractal_stop = float(fractal0_price - fractal_buffer * atr)
            floor_stop = float(entry_bid_equivalent - entry_floor * atr)
            stop = min(fractal_stop, floor_stop)
            source = "fractal0_buffer" if fractal_stop <= floor_stop else "entry_floor"
        else:
            fractal_stop = float(fractal0_price + fractal_buffer * atr)
            floor_stop = float(entry_bid_equivalent + entry_floor * atr)
            stop = max(fractal_stop, floor_stop)
            source = "fractal0_buffer" if fractal_stop >= floor_stop else "entry_floor"
    else:
        raise ValueError(f"unknown stop policy family: {family}")
    distance_atr = abs(float(entry_bid_equivalent) - stop) / float(atr) if atr else float("nan")
    return {"protective_stop_price": stop, "stop_source": source, "stop_distance_atr": distance_atr, "risk_distance_atr": distance_atr}


def protective_stop_price(
    side: str,
    fractal0_price: float,
    entry_bid_equivalent: float,
    atr: float,
    stop_policy: dict[str, object] | None = None,
) -> float:
    return float(resolve_protective_stop(side, fractal0_price, entry_bid_equivalent, atr, stop_policy)["protective_stop_price"])


def _execution_window_for_h1_bar(execution_ohlc: pd.DataFrame | None, h1_time: pd.Timestamp) -> pd.DataFrame:
    if execution_ohlc is None or execution_ohlc.empty or "time" not in execution_ohlc.columns:
        return pd.DataFrame()
    start = pd.Timestamp(h1_time)
    if "_h1_time" in execution_ohlc.columns and execution_ohlc.index.name == "_h1_time":
        try:
            window = execution_ohlc.loc[start]
            if isinstance(window, pd.Series):
                window = window.to_frame().T
            return window.reset_index(drop=True)
        except KeyError:
            return pd.DataFrame()
    end = start + pd.Timedelta(hours=1)
    return execution_ohlc.loc[(execution_ohlc["time"] >= start) & (execution_ohlc["time"] < end)].reset_index(drop=True)


def _first_limit_touch_execution_time(
    side: str,
    h1_time: pd.Timestamp,
    limit_price: float,
    spread: float,
    execution_ohlc: pd.DataFrame | None,
) -> pd.Timestamp | pd.NaT:
    window = _execution_window_for_h1_bar(execution_ohlc, h1_time)
    if window.empty:
        return pd.NaT
    for _, bar in window.iterrows():
        low_bid = float(bar["low"])
        high_bid = float(bar["high"])
        if side == "BUY" and low_bid + float(spread) <= float(limit_price):
            return pd.Timestamp(bar["time"])
        if side == "SELL" and high_bid >= float(limit_price):
            return pd.Timestamp(bar["time"])
    return pd.NaT


def build_entry_rows(
    rows: pd.DataFrame,
    ohlc: pd.DataFrame,
    entry_rule: dict[str, object],
    spread: float,
    stop_policy: dict[str, object] | None = None,
    execution_ohlc: pd.DataFrame | None = None,
) -> pd.DataFrame:
    out = []
    policy = stop_policy or stop_policy_grid()[0]
    ohlc_times = pd.to_datetime(ohlc["time"]).to_numpy()
    opens = pd.to_numeric(ohlc["open"], errors="coerce").to_numpy(dtype=float)
    highs = pd.to_numeric(ohlc["high"], errors="coerce").to_numpy(dtype=float)
    lows = pd.to_numeric(ohlc["low"], errors="coerce").to_numpy(dtype=float)
    for split_row_id, row in rows.reset_index(drop=True).iterrows():
        fractal = parse_fractal0(row.get("fractal0"))
        if not fractal:
            continue
        side = side_from_fractal_dir(fractal["direction"])
        if side is None:
            continue
        signal_time = pd.Timestamp(row["time"])
        idx = int(ohlc_times.searchsorted(signal_time.to_datetime64(), side="right"))
        if idx >= len(ohlc):
            continue
        atr = float(row.get("ATR", row.get("atr14", np.nan)))
        limit_price = resolve_limit_price(row, entry_rule, float(opens[idx]))
        planned_entry_bid_equivalent = float(limit_price) - float(spread) if side == "BUY" else float(limit_price)
        start = idx + 1
        end = min(start + int(entry_rule.get("lag_bars", 6)), len(ohlc))
        fill = {
            "filled": False,
            "fill_index": None,
            "fill_time": pd.NaT,
            "fill_execution_time": pd.NaT,
            "fill_execution_time_source": "not_filled",
            "fill_execution_confirmed": False,
            "entry_effective_price": np.nan,
            "entry_bid_equivalent": np.nan,
        }
        for pos in range(start, end):
            if side == "BUY" and lows[pos] + float(spread) <= float(limit_price):
                fill = {
                    "filled": True,
                    "fill_index": int(pos),
                    "fill_time": pd.Timestamp(ohlc_times[pos]),
                    "fill_execution_time": _first_limit_touch_execution_time(side, pd.Timestamp(ohlc_times[pos]), float(limit_price), float(spread), execution_ohlc),
                    "fill_execution_time_source": "pending",
                    "fill_execution_confirmed": False,
                    "entry_effective_price": float(limit_price),
                    "entry_bid_equivalent": float(limit_price) - float(spread),
                }
                break
            if side == "SELL" and highs[pos] >= float(limit_price):
                fill = {
                    "filled": True,
                    "fill_index": int(pos),
                    "fill_time": pd.Timestamp(ohlc_times[pos]),
                    "fill_execution_time": _first_limit_touch_execution_time(side, pd.Timestamp(ohlc_times[pos]), float(limit_price), float(spread), execution_ohlc),
                    "fill_execution_time_source": "pending",
                    "fill_execution_confirmed": False,
                    "entry_effective_price": float(limit_price),
                    "entry_bid_equivalent": float(limit_price),
                }
                break
        if fill["filled"]:
            if execution_ohlc is None:
                fill["fill_execution_time"] = fill["fill_time"]
                fill["fill_execution_time_source"] = "h1_no_execution_ohlc"
                fill["fill_execution_confirmed"] = False
            elif pd.isna(fill.get("fill_execution_time")):
                fill["fill_execution_time_source"] = "missing_m5_touch"
                fill["fill_execution_confirmed"] = False
            else:
                fill["fill_execution_time_source"] = "m5_touch"
                fill["fill_execution_confirmed"] = True
        entry_bid_equivalent = float(fill["entry_bid_equivalent"]) if fill["filled"] else planned_entry_bid_equivalent
        stop_info = resolve_protective_stop(side, fractal["price"], entry_bid_equivalent, atr, policy)
        stop = float(stop_info["protective_stop_price"])
        r_value = abs(float(fill["entry_effective_price"]) - stop) if fill["filled"] else np.nan
        planned_r_value = abs(float(limit_price) - stop)
        fractal_snapshot = {col: row.get(col) for col in rows.columns if str(col).startswith("fractal") and str(col)[7:].isdigit()}
        out.append(
            {
                **fill,
                **fractal_snapshot,
                "position_id": f"{policy['stop_policy_id']}:{entry_rule['entry_id']}:{split_row_id}",
                "split": row.get("split"),
                "split_row_id": int(row.get("split_row_id", split_row_id)),
                "signal_time": signal_time,
                "time": signal_time,
                "side": side,
                "calculation_open": float(opens[idx]),
                "limit_price": float(limit_price),
                "planned_entry_price": float(limit_price),
                "planned_entry_bid_equivalent": planned_entry_bid_equivalent,
                "planned_protective_stop_price": stop,
                "planned_r_value": planned_r_value,
                "atr": atr,
                "ATR": atr,
                "fractal0_price": fractal["price"],
                "protective_stop_price": stop,
                "r_value": r_value,
                "stop_policy_id": policy["stop_policy_id"],
                "stop_family": policy["family"],
                "entry_floor_atr": policy["entry_floor_atr"],
                "fractal0_buffer_atr": policy["fractal0_buffer_atr"],
                "stop_source": stop_info["stop_source"],
                "stop_distance_atr": stop_info["stop_distance_atr"],
                "risk_distance_atr": stop_info["risk_distance_atr"],
            }
        )
    return pd.DataFrame(out)


def _effective_exit_bars(side: str, bars: pd.DataFrame, spread: float) -> pd.DataFrame:
    if side == "BUY":
        return bars.copy()
    shifted = bars.copy()
    for col in ("open", "high", "low", "close"):
        shifted[col] = pd.to_numeric(shifted[col], errors="coerce") + float(spread)
    return shifted


def _pnl_r(side: str, entry_price: float, exit_price: float, r_value: float) -> float:
    return float(((exit_price - entry_price) if side == "BUY" else (entry_price - exit_price)) / r_value)


def _resolve_same_bar_with_execution_ohlc(
    side: str,
    h1_bar: pd.Series,
    execution_ohlc: pd.DataFrame | None,
    spread: float,
    stop: float,
    tp: float,
    not_before: pd.Timestamp | None = None,
) -> tuple[str, pd.Series, bool] | None:
    start = pd.to_datetime(h1_bar.get("time"), errors="coerce")
    if pd.isna(start):
        return None
    window = _execution_window_for_h1_bar(execution_ohlc, start)
    if window.empty:
        return None
    if not_before is not None and pd.notna(not_before):
        window = window.loc[pd.to_datetime(window["time"]) >= pd.Timestamp(not_before)].reset_index(drop=True)
        if window.empty:
            return None
    bars = _effective_exit_bars(side, window.reset_index(drop=True), spread)
    for _, bar in bars.iterrows():
        high, low = float(bar["high"]), float(bar["low"])
        stop_hit = low <= stop if side == "BUY" else high >= stop
        tp_hit = high >= tp if side == "BUY" else low <= tp
        if stop_hit and tp_hit:
            return "SL", bar, True
        if stop_hit:
            return "SL", bar, False
        if tp_hit:
            return "TP", bar, False
    return None


def simulate_trade(
    entry: dict[str, object],
    ohlc: pd.DataFrame,
    exit_rule: dict[str, object],
    spread: float,
    ml_scores: dict[int, float] | None = None,
    execution_ohlc: pd.DataFrame | None = None,
) -> dict[str, object]:
    side = str(entry["side"])
    start = int(entry.get("fill_index", 0))
    bars = _effective_exit_bars(side, ohlc.iloc[start:].reset_index(drop=True), spread)
    entry_price = float(entry["entry_effective_price"])
    stop = float(entry["protective_stop_price"])
    r_value = float(entry["r_value"])
    fixed_tp_enabled = exit_rule.get("family") == "fixed_r"
    tp = entry_price + float(exit_rule.get("tp_r", 0.7)) * r_value if side == "BUY" else entry_price - float(exit_rule.get("tp_r", 0.7)) * r_value
    hold_limit = int(exit_rule.get("hold_bars", MAX_EXIT_HOLD_BARS))
    best_r = -np.inf
    for i, bar in bars.iloc[: min(len(bars), max(hold_limit + 1, MAX_EXIT_HOLD_BARS + 1))].iterrows():
        decision_time = pd.Timestamp(bar.get("time", pd.NaT))
        fill_execution_time = pd.Timestamp(entry.get("fill_execution_time", entry.get("fill_time", pd.NaT)))
        fill_execution_confirmed = bool(entry.get("fill_execution_confirmed", pd.notna(fill_execution_time)))
        fill_h1_time = pd.Timestamp(entry.get("fill_time", pd.NaT))
        same_h1_as_fill = pd.notna(fill_h1_time) and decision_time == fill_h1_time
        earliest_event_time = fill_execution_time if same_h1_as_fill and fill_execution_confirmed and pd.notna(fill_execution_time) else None
        fill_h1_missing_m5_touch = same_h1_as_fill and not fill_execution_confirmed
        high, low = float(bar["high"]), float(bar["low"])
        stop_hit = low <= stop if side == "BUY" else high >= stop
        tp_hit = (high >= tp if side == "BUY" else low <= tp) if fixed_tp_enabled else False
        ambiguous = bool(stop_hit and tp_hit)
        if fill_h1_missing_m5_touch:
            stop_hit = False
            tp_hit = False
            ambiguous = False
        if same_h1_as_fill and (stop_hit or tp_hit) and execution_ohlc is not None:
            resolved = _resolve_same_bar_with_execution_ohlc(side, bar, execution_ohlc, spread, stop, tp, earliest_event_time)
            if resolved is not None:
                reason, resolved_bar, still_ambiguous = resolved
                price = stop if reason == "SL" else tp
                if pd.Timestamp(resolved_bar.get("time", pd.NaT)) == earliest_event_time:
                    still_ambiguous = True
                return _trade_result(reason, side, entry_price, price, r_value, i, resolved_bar, still_ambiguous)
            stop_hit = False
            tp_hit = False
            ambiguous = False
        if ambiguous:
            resolved = _resolve_same_bar_with_execution_ohlc(side, bar, execution_ohlc, spread, stop, tp, None)
            if resolved is not None:
                reason, resolved_bar, still_ambiguous = resolved
                price = stop if reason == "SL" else tp
                return _trade_result(reason, side, entry_price, price, r_value, i, resolved_bar, still_ambiguous)
        if stop_hit:
            return _trade_result("SL", side, entry_price, stop, r_value, i, bar, ambiguous)
        if tp_hit and fixed_tp_enabled:
            return _trade_result("TP", side, entry_price, tp, r_value, i, bar, ambiguous)
        close_price = float(bar["close"])
        now_r = _pnl_r(side, entry_price, close_price, r_value)
        best_r = max(best_r, now_r)
        if i >= hold_limit:
            return _trade_result("TIME", side, entry_price, close_price, r_value, i, bar, False)
        if exit_rule.get("family") == "profit_giveback" and best_r >= float(exit_rule.get("activation_atr", 1.0)) and now_r <= best_r * (1.0 - float(exit_rule.get("giveback_fraction", 0.5))):
            return _trade_result("GIVEBACK", side, entry_price, close_price, r_value, i, bar, False)
        ml_decision_is_after_fill = i > 0 and not same_h1_as_fill
        ml_execution_pos = i + 1
        can_execute_ml_close = ml_execution_pos < len(bars)
        if (
            ml_decision_is_after_fill
            and can_execute_ml_close
            and (str(exit_rule.get("family", "")).startswith("ml") or exit_rule.get("family") == "fixed_sl_ml_profit_exit")
        ):
            score = (ml_scores or {}).get(i, 0.0)
            ml_exit_bar = bars.iloc[ml_execution_pos]
            ml_exit_price = float(ml_exit_bar["open"])
            if score >= float(exit_rule.get("prob_threshold", 1.1)) and (exit_rule.get("family") != "fixed_sl_ml_profit_exit" or now_r >= 0):
                return _trade_result("ML_CLOSE", side, entry_price, ml_exit_price, r_value, ml_execution_pos, ml_exit_bar, False)
    last = bars.iloc[-1]
    return _trade_result("TIME", side, entry_price, float(last["close"]), r_value, len(bars) - 1, last, False)


def _trade_result(reason: str, side: str, entry_price: float, exit_price: float, r_value: float, hold_bars: int, bar: pd.Series, ambiguous: bool) -> dict[str, object]:
    return {"filled": True, "close_reason": reason, "pnl_r": _pnl_r(side, entry_price, exit_price, r_value), "hold_bars": int(hold_bars), "ambiguous": ambiguous, "exit_price": float(exit_price), "exit_time": str(bar.get("time", ""))}


def compute_trade_metrics(trades: pd.DataFrame) -> dict[str, object]:
    pnl = pd.to_numeric(trades.get("pnl_r"), errors="coerce").dropna()
    wins, losses = pnl[pnl > 0], pnl[pnl < 0]
    gross_profit = float(wins.sum())
    gross_loss = float(-losses.sum())
    equity = pnl.cumsum()
    dd = equity.cummax() - equity
    return {"n_trades": int(len(pnl)), "gross_profit": gross_profit, "gross_loss": gross_loss, "pf": float(gross_profit / gross_loss) if gross_loss > 0 else None, "mean_pnl_r": float(pnl.mean()) if len(pnl) else None, "median_pnl_r": float(pnl.median()) if len(pnl) else None, "max_drawdown_r": float(dd.max()) if len(dd) else 0.0, "win_rate": float((pnl > 0).mean()) if len(pnl) else None, "ambiguous_same_bar_rate": float(trades.get("ambiguous", pd.Series(dtype=bool)).fillna(False).astype(bool).mean()) if len(trades) else 0.0, "exit_reason_counts": trades.get("close_reason", pd.Series(dtype=object)).value_counts().to_dict()}


def yearly_metrics(trades: pd.DataFrame) -> list[dict[str, object]]:
    if trades.empty:
        return []
    frame = trades.copy()
    frame["year"] = pd.to_datetime(frame.get("exit_time", frame.get("time")), errors="coerce").dt.year.fillna(0).astype(int)
    return [{"year": int(year), **compute_trade_metrics(group)} for year, group in frame.groupby("year")]


def filter_trades_for_rule(trades: pd.DataFrame, rule: dict[str, object], split: str | None = None, spread: float | None = None) -> pd.DataFrame:
    if trades.empty:
        return trades.copy()
    key_cols = ["entry_id", "mask_id", "exit_id"]
    if "stop_policy_id" in trades.columns and "stop_policy_id" in rule:
        key_cols.insert(0, "stop_policy_id")
    mask = pd.Series(True, index=trades.index)
    for key in key_cols:
        mask &= trades[key].eq(rule[key])
    if split is not None and "split" in trades:
        mask &= trades["split"].eq(split)
    spread_col = "spread" if "spread" in trades else "metric_spread" if "metric_spread" in trades else None
    if spread is not None and spread_col is not None:
        mask &= pd.to_numeric(trades[spread_col], errors="coerce").eq(float(spread))
    return trades.loc[mask].copy()


def effective_profit_years_from_yearly(yearly: list[dict[str, object]]) -> float:
    gross_profits = np.array([max(0.0, float(row.get("gross_profit") or 0.0)) for row in yearly], dtype=float)
    total = float(gross_profits.sum())
    if total <= 0.0:
        return 0.0
    shares = gross_profits / total
    return float(1.0 / np.square(shares).sum())


def block_bootstrap_pf(trades: pd.DataFrame, seed: int = 20260720, n_bootstrap: int = 1000, block_size: int = 20) -> dict[str, object]:
    pnl = pd.to_numeric(trades.get("pnl_r"), errors="coerce").dropna().to_numpy()
    if len(pnl) == 0:
        return {"bs_p05": None, "samples": 0}
    rng = np.random.default_rng(seed)
    vals = []
    for _ in range(n_bootstrap):
        sample = rng.choice(pnl, size=len(pnl), replace=True)
        gp, gl = sample[sample > 0].sum(), -sample[sample < 0].sum()
        vals.append(float(gp / gl) if gl > 0 else 99.0)
    return {"bs_p05": float(np.quantile(vals, 0.05)), "samples": int(n_bootstrap)}


def load_frozen_movement_mask(report_path: Path, scores_path: Path) -> dict[str, object]:
    return {"report": json.loads(report_path.read_text(encoding="utf-8")), "scores": pd.read_csv(scores_path, sep=_detect_sep(scores_path))}


def apply_mask(rows: pd.DataFrame, mask_id: str, frozen_scores: pd.DataFrame | None) -> pd.DataFrame:
    if mask_id == "M0_no_mask":
        out = rows.copy()
        out["movement_mask_selected"] = True
        return out
    if frozen_scores is None:
        raise ValueError("frozen movement scores required for M1_frozen_movement_top5")
    selected = frozen_scores.loc[frozen_scores["selected"].astype(bool), ["split_row_id", "score"]].rename(columns={"score": "movement_score"})
    out = rows.merge(selected, on="split_row_id", how="inner")
    out["movement_mask_selected"] = True
    return out


def validate_movement_mask_coverage(rows: pd.DataFrame, scores: pd.DataFrame) -> dict[str, object]:
    row_ids = set(rows["split_row_id"].tolist())
    score_ids = set(scores["split_row_id"].tolist())
    missing = row_ids - score_ids
    return {"status": "PASS" if not missing else "FAIL", "rows": len(row_ids), "score_rows": len(score_ids), "missing_score_rows": len(missing), "coverage": 1.0 if not row_ids else (len(row_ids) - len(missing)) / len(row_ids)}


def compute_attribution(summary: pd.DataFrame, winner: dict[str, object]) -> list[dict[str, object]]:
    stop_filter = {"stop_policy_id": winner["stop_policy_id"]} if "stop_policy_id" in summary.columns and "stop_policy_id" in winner else {}
    checks = [
        ("A0_matched_entry_mask_baseline_exit", {**stop_filter, "entry_id": winner["entry_id"], "mask_id": winner["mask_id"], "exit_id": "X0_fixed_r_0_7"}),
        ("A1_same_exit_no_mask", {**stop_filter, "entry_id": winner["entry_id"], "mask_id": "M0_no_mask", "exit_id": winner["exit_id"]}),
        ("A2_same_exit_simple_entry", {**stop_filter, "entry_id": "E1_simple_limit_at_fractal0", "mask_id": winner["mask_id"], "exit_id": winner["exit_id"]}),
        ("A4_same_entry_mask_time_exit", {**stop_filter, "entry_id": winner["entry_id"], "mask_id": winner["mask_id"], "exit_id": "X7_time_6"}),
    ]
    out = []
    for check_id, filters in checks:
        row = summary
        for key, value in filters.items():
            row = row[row[key] == value]
        baseline_pf = None if row.empty else float(row.iloc[0]["pf"])
        out.append({"check_id": check_id, "baseline_pf": baseline_pf})
    return out


def build_exit_decision_rows(trades: pd.DataFrame, ohlc: pd.DataFrame) -> pd.DataFrame:
    rows = []
    times = pd.to_datetime(ohlc["time"]).to_numpy()
    opens = pd.to_numeric(ohlc["open"], errors="coerce").to_numpy(dtype=float)
    highs = pd.to_numeric(ohlc["high"], errors="coerce").to_numpy(dtype=float)
    lows = pd.to_numeric(ohlc["low"], errors="coerce").to_numpy(dtype=float)
    closes = pd.to_numeric(ohlc["close"], errors="coerce").to_numpy(dtype=float)
    for _, trade in trades.iterrows():
        fill = int(trade["fill_index"])
        last_decision = min(len(ohlc) - 1, fill + MAX_EXIT_HOLD_BARS)
        side = str(trade["side"])
        entry_price = float(trade["entry_effective_price"])
        r_value = float(trade["r_value"])
        for idx in range(fill + 1, last_decision):
            bars_since_fill = idx - fill
            known_start = fill + 1
            known_end = idx + 1
            close_now = _pnl_r(side, entry_price, closes[idx], r_value)
            if side == "BUY":
                favorable_before = (float(np.nanmax(highs[known_start:known_end])) - entry_price) / r_value
                adverse_before = (entry_price - float(np.nanmin(lows[known_start:known_end]))) / r_value
            else:
                favorable_before = (entry_price - float(np.nanmin(lows[known_start:known_end]))) / r_value
                adverse_before = (float(np.nanmax(highs[known_start:known_end])) - entry_price) / r_value
            favorable_before = max(0.0, float(favorable_before))
            adverse_before = max(0.0, float(adverse_before))
            future_start = idx + 1
            future_end = min(idx + 4, len(ohlc))
            if future_start >= future_end:
                fav = 0.0
                adv = 0.0
                hold_3 = close_now
            elif side == "BUY":
                fav = (float(np.nanmax(highs[future_start:future_end])) - entry_price) / r_value
                adv = (entry_price - float(np.nanmin(lows[future_start:future_end]))) / r_value
                hold_3 = _pnl_r(side, entry_price, closes[future_end - 1], r_value)
            else:
                fav = (entry_price - float(np.nanmin(lows[future_start:future_end]))) / r_value
                adv = (float(np.nanmax(highs[future_start:future_end])) - entry_price) / r_value
                hold_3 = _pnl_r(side, entry_price, closes[future_end - 1], r_value)
            movement_score = trade.get("movement_score", np.nan)
            rows.append(
                {
                    "position_id": trade.get("position_id"),
                    "side": side,
                    "decision_bar_time": pd.Timestamp(times[idx]),
                    "feature_available_time": pd.Timestamp(times[idx + 1]),
                    "decision_time": pd.Timestamp(times[idx + 1]),
                    "ml_decision_time": pd.Timestamp(times[idx + 1]),
                    "first_exit_execution_time": pd.Timestamp(times[idx + 1]),
                    "bars_since_fill": bars_since_fill,
                    "ml_exit_eligible": True,
                    "entry_effective_price": entry_price,
                    "r_value": r_value,
                    "ATR": trade.get("ATR", trade.get("atr", np.nan)),
                    "unrealized_pnl_r_before_decision": close_now,
                    "max_favorable_r_before_decision": favorable_before,
                    "max_adverse_r_before_decision": adverse_before,
                    "future_favorable_r_3": fav,
                    "future_adverse_r_3": adv,
                    "close_now_pnl_r": close_now,
                    "decision_bar_close_pnl_r_for_target": close_now,
                    "hold_3_pnl_r": hold_3,
                    "movement_score": movement_score,
                    "movement_score_available": bool(pd.notna(movement_score)),
                }
            )
    return pd.DataFrame(rows)


def build_exit_targets(decision_rows: pd.DataFrame) -> pd.DataFrame:
    out = decision_rows.copy()
    out["target_exit_opposite_any"] = (out["future_adverse_r_3"] >= 0.5).astype(int)
    out["target_exit_opposite_strong"] = (out["future_adverse_r_3"] >= 1.0).astype(int)
    out["target_exit_hold_close"] = (out["close_now_pnl_r"] >= out["hold_3_pnl_r"] + 0.1).astype(int)
    out["target_exit_movement_exhaustion"] = ((out["future_favorable_r_3"] < 0.3) & (out["future_adverse_r_3"] >= 0.5)).astype(int)
    return out


def exit_feature_columns(mask_id: str) -> list[str]:
    return EXIT_FEATURE_COLUMNS_BASE + (EXIT_FEATURE_COLUMNS_M1_ONLY if mask_id == "M1_frozen_movement_top5" else [])


def train_exit_models(
    train_rows: pd.DataFrame,
    threads: int,
    seeds: tuple[int, ...] = EXIT_MODEL_SEEDS,
    n_estimators: int = 200,
) -> dict[str, object]:
    models: dict[str, object] = {}
    rows = build_exit_targets(train_rows) if not set(EXIT_TARGETS).issubset(train_rows.columns) else train_rows.copy()
    started = time.time()
    for mask_id in ("M0_no_mask", "M1_frozen_movement_top5"):
        cols = [col for col in exit_feature_columns(mask_id) if col in rows.columns]
        models[mask_id] = {}
        if not cols or rows.empty:
            models[mask_id] = {target: [0.0] for target in EXIT_TARGETS}
            continue
        x = rows[cols].fillna(0.0)
        for target in EXIT_TARGETS:
            y = rows[target].astype(int)
            if y.nunique() < 2:
                models[mask_id][target] = [float(y.iloc[0]) if len(y) else 0.0]
                continue
            fitted = []
            for seed in seeds:
                print(
                    f"train ml-exit mask={mask_id} target={target} seed={seed} rows={len(rows)} features={len(cols)} elapsed={time.time() - started:.1f}",
                    flush=True,
                )
                clf = ExtraTreesClassifier(n_estimators=n_estimators, max_depth=8, min_samples_leaf=50, random_state=seed, n_jobs=threads)
                clf.fit(x, y)
                fitted.append(clf)
            models[mask_id][target] = fitted
    return models


def score_exit_models(models: dict[str, object], decision_rows: pd.DataFrame) -> pd.DataFrame:
    out = decision_rows.copy()
    for mask_id, targets in models.items():
        cols = [col for col in exit_feature_columns(mask_id) if col in out.columns]
        x = out[cols].fillna(0.0)
        for target, fitted in targets.items():
            values = []
            for model in fitted:
                values.append(np.full(len(out), model) if isinstance(model, float) else model.predict_proba(x)[:, 1])
            out[f"score_{target}_{mask_id}"] = np.median(np.vstack(values), axis=0) if values else 0.0
    return out


def _target_for_exit_rule(exit_rule: dict[str, object]) -> str | None:
    family = str(exit_rule.get("family"))
    if family == "ml_opposite_any":
        return "target_exit_opposite_any"
    if family == "ml_opposite_strong":
        return "target_exit_opposite_strong"
    if family == "ml_hold_close":
        return "target_exit_hold_close"
    if family == "ml_movement_exhaustion":
        return "target_exit_movement_exhaustion"
    if family == "fixed_sl_ml_profit_exit":
        model = str(exit_rule.get("model", ""))
        return "target_exit_hold_close" if model == "hold_close" else "target_exit_movement_exhaustion"
    return None


def _score_map_for_entries(
    entries: pd.DataFrame,
    ohlc: pd.DataFrame,
    scored_decisions: pd.DataFrame,
    exit_rule: dict[str, object],
    mask_id: str,
) -> dict[str, dict[int, float]]:
    target = _target_for_exit_rule(exit_rule)
    if target is None:
        return {}
    score_col = f"score_{target}_{mask_id}"
    if score_col not in scored_decisions.columns:
        return {}
    eligible = scored_decisions.copy()
    if "ml_exit_eligible" in eligible.columns:
        eligible = eligible.loc[eligible["ml_exit_eligible"].astype(bool)].copy()
    eligible = eligible.loc[pd.to_numeric(eligible["bars_since_fill"], errors="coerce") > 0].copy()
    maps: dict[str, dict[int, float]] = {}
    for position_id, group in eligible.groupby("position_id"):
        maps[str(position_id)] = {
            int(row["bars_since_fill"]): float(row[score_col])
            for _, row in group.iterrows()
            if pd.notna(row.get(score_col))
        }
    return maps


def select_winner(summary: pd.DataFrame) -> dict[str, object]:
    candidates = summary[(summary["n_trades"] >= 300) & (summary["negative_years"] <= 1) & (summary["mean_pnl_r"] > 0) & (summary["pf_without_best_year"] >= 1.10)].copy()
    if candidates.empty:
        candidates = summary.copy()
    candidates["ml_threshold_count"] = candidates["exit_id"].astype(str).str.contains("_p").astype(int)
    candidates = candidates.sort_values(["bs_p05", "ml_threshold_count", "max_drawdown_r"], ascending=[False, True, True])
    winner = candidates.iloc[0].to_dict()
    winner["selection_metric"] = "BS_p05"
    return winner


def _summary_from_trades(trades: pd.DataFrame, run: dict[str, object], split: str, spread: float, n_bootstrap: int = 200) -> dict[str, object]:
    metrics = compute_trade_metrics(trades)
    risk_distance_atr = pd.to_numeric(trades.get("risk_distance_atr"), errors="coerce") if "risk_distance_atr" in trades else pd.Series(dtype=float)
    tp_distance_atr = pd.to_numeric(trades.get("tp_distance_atr"), errors="coerce") if "tp_distance_atr" in trades else pd.Series(dtype=float)
    bs = block_bootstrap_pf(trades, seed=int(resume_key({**run, "split": split, "spread": spread})[:8], 16), n_bootstrap=n_bootstrap)
    yearly = yearly_metrics(trades)
    yearly_pf = [row.get("pf") for row in yearly if row.get("pf") is not None]
    best_year_pf = max(yearly_pf) if yearly_pf else None
    negative_years = sum((row.get("mean_pnl_r") or 0.0) < 0.0 for row in yearly)
    if len(yearly) > 1 and best_year_pf is not None:
        year_frame = trades.copy()
        year_frame["_year"] = pd.to_datetime(year_frame["exit_time"], errors="coerce").dt.year
        grouped = []
        for year, group in year_frame.groupby("_year"):
            pf = compute_trade_metrics(group).get("pf")
            grouped.append((year, pf if pf is not None else -1.0))
        best_year = max(grouped, key=lambda item: item[1])[0]
        pf_without_best = compute_trade_metrics(year_frame.loc[year_frame["_year"] != best_year]).get("pf")
    else:
        pf_without_best = metrics.get("pf")
    return {
        **{k: run[k] for k in ("stop_policy_id", "entry_id", "mask_id", "exit_id") if k in run},
        "split": split,
        "spread": float(spread),
        **metrics,
        "risk_distance_atr": float(risk_distance_atr.median()) if not risk_distance_atr.dropna().empty else None,
        "tp_distance_atr": float(tp_distance_atr.median()) if not tp_distance_atr.dropna().empty else None,
        "bs_p05": bs["bs_p05"],
        "negative_years": int(negative_years),
        "pf_without_best_year": pf_without_best,
        "effective_profit_years": effective_profit_years_from_yearly(yearly),
        "n_years": int(len(yearly)),
    }


def _simulate_entries(
    entries: pd.DataFrame,
    ohlc: pd.DataFrame,
    run: dict[str, object],
    spread: float,
    scored_decisions: pd.DataFrame | None = None,
    execution_ohlc: pd.DataFrame | None = None,
) -> pd.DataFrame:
    filled = entries.loc[entries["filled"].astype(bool) & pd.to_numeric(entries["r_value"], errors="coerce").gt(0)].copy()
    if filled.empty:
        return pd.DataFrame()
    ml_maps = _score_map_for_entries(filled, ohlc, scored_decisions if scored_decisions is not None else pd.DataFrame(), run, str(run["mask_id"]))
    out = []
    for _, entry in filled.iterrows():
        entry_dict = entry.to_dict()
        result = simulate_trade(entry_dict, ohlc, run, spread, ml_scores=ml_maps.get(str(entry_dict["position_id"])), execution_ohlc=execution_ohlc)
        out.append(
            {
                **result,
                "position_id": entry_dict["position_id"],
                "split": entry_dict.get("split"),
                "split_row_id": entry_dict.get("split_row_id"),
                "entry_id": run["entry_id"],
                "mask_id": run["mask_id"],
                "exit_id": run["exit_id"],
                "fill_execution_time": entry_dict.get("fill_execution_time"),
                "fill_execution_time_source": entry_dict.get("fill_execution_time_source"),
                "fill_execution_confirmed": entry_dict.get("fill_execution_confirmed"),
                "stop_policy_id": run.get("stop_policy_id", entry_dict.get("stop_policy_id")),
                "stop_family": entry_dict.get("stop_family"),
                "entry_floor_atr": entry_dict.get("entry_floor_atr"),
                "fractal0_buffer_atr": entry_dict.get("fractal0_buffer_atr"),
                "stop_source": entry_dict.get("stop_source"),
                "stop_distance_atr": entry_dict.get("stop_distance_atr"),
                "risk_distance_atr": entry_dict.get("risk_distance_atr"),
                "tp_distance_atr": float(run.get("tp_r", np.nan)) * float(entry_dict.get("risk_distance_atr", np.nan)) if str(run.get("family")) == "fixed_r" else np.nan,
                "side": entry_dict["side"],
                "entry_effective_price": entry_dict["entry_effective_price"],
                "entry_bid_equivalent": entry_dict["entry_bid_equivalent"],
                "protective_stop_price": entry_dict["protective_stop_price"],
                "r_value": entry_dict["r_value"],
                "signal_time": str(entry_dict.get("signal_time")),
                "fill_time": str(entry_dict.get("fill_time")),
                "fill_index": int(entry_dict.get("fill_index")),
            }
        )
    return pd.DataFrame(out)


def _read_frozen_scores(config: Fractal0EntryExitGridConfig) -> pd.DataFrame:
    path = _path(config.movement_freeze_scores)
    if not path.exists():
        report = json.loads(_path(config.movement_freeze_json).read_text(encoding="utf-8"))
        path = _path(str(report["scores_csv"]))
    scores = pd.read_csv(path, sep=_detect_sep(path))
    scores["selected"] = scores["selected"].astype(bool)
    return scores


def _entry_cache_for_spread(
    splits: dict[str, pd.DataFrame],
    ohlc: pd.DataFrame,
    spread: float,
    frozen_scores: pd.DataFrame,
    stop_policies: list[dict[str, object]] | None = None,
    entries: list[dict[str, object]] | None = None,
    masks: list[dict[str, object]] | None = None,
    execution_ohlc: pd.DataFrame | None = None,
) -> tuple[dict[tuple[str, str, str, str], pd.DataFrame], dict[str, object]]:
    cache: dict[tuple[str, str, str, str], pd.DataFrame] = {}
    rows_by_split_before_after_mask: dict[str, object] = {}
    fill_rate_by_entry: dict[str, object] = {}
    entry_rules = entries or entry_grid()
    stop_rules = stop_policies or [stop_policy_grid()[0]]
    masks = masks or mask_grid()
    for split, rows in splits.items():
        split_scores = frozen_scores.loc[frozen_scores["split"].eq("train" if split == "train_core" else split)].copy()
        rows_by_split_before_after_mask[split] = {}
        for stop_policy in stop_rules:
            stop_id = str(stop_policy["stop_policy_id"])
            for entry in entry_rules:
                entry_rows = build_entry_rows(rows, ohlc, entry, spread, stop_policy, execution_ohlc)
                filled_rate = float(entry_rows["filled"].mean()) if len(entry_rows) else 0.0
                fill_rate_by_entry.setdefault(f"{stop_id}:{entry['entry_id']}", {})[split] = filled_rate
                for mask in masks:
                    masked = apply_mask(entry_rows, str(mask["mask_id"]), split_scores)
                    cache[(split, stop_id, str(entry["entry_id"]), str(mask["mask_id"]))] = masked
                    rows_by_split_before_after_mask[split][f"{stop_id}:{entry['entry_id']}:{mask['mask_id']}"] = {
                        "raw_rows_before_entry": int(len(rows)),
                        "entry_rows_before_mask": int(len(entry_rows)),
                        "rows_after_mask": int(len(masked)),
                        "before": int(len(entry_rows)),
                        "after": int(len(masked)),
                        "filled_after": int(masked["filled"].sum()) if "filled" in masked else 0,
                    }
    return cache, {"rows_by_split_before_after_mask": rows_by_split_before_after_mask, "fill_rate_by_entry": fill_rate_by_entry}


def _train_ml_exit_layer(
    entry_cache: dict[tuple[str, str, str, str], pd.DataFrame],
    ohlc: pd.DataFrame,
    threads: int,
    seeds: tuple[int, ...] = EXIT_MODEL_SEEDS,
    n_estimators: int = 200,
) -> tuple[dict[str, object], dict[str, object]]:
    train_decisions_by_stop: dict[str, list[pd.DataFrame]] = {}
    started = time.time()
    built_rows = 0
    for (split, stop_policy_id, _entry_id, mask_id), entries in entry_cache.items():
        if split != "train_core":
            continue
        filled = entries.loc[entries["filled"].astype(bool)].copy()
        print(
            f"prepare train ml-exit decisions entry={_entry_id} mask={mask_id} filled={len(filled)} elapsed={time.time() - started:.1f}",
            flush=True,
        )
        if not filled.empty:
            decisions = build_exit_decision_rows(filled, ohlc)
            built_rows += len(decisions)
            print(
                f"prepare train ml-exit decisions entry={_entry_id} mask={mask_id} decision_rows={len(decisions)} total_decision_rows={built_rows} elapsed={time.time() - started:.1f}",
                flush=True,
            )
            decisions["mask_id"] = mask_id
            decisions["stop_policy_id"] = stop_policy_id
            train_decisions_by_stop.setdefault(stop_policy_id, []).append(decisions)
    models: dict[str, object] = {}
    target_rates: dict[str, object] = {"train_core": {}}
    for stop_policy_id, frames in train_decisions_by_stop.items():
        rows = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
        print(
            f"prepare train ml-exit fit stop_policy={stop_policy_id} rows={len(rows)} seeds={list(seeds)} n_estimators={n_estimators} threads={threads}",
            flush=True,
        )
        models[stop_policy_id] = train_exit_models(rows, threads=threads, seeds=seeds, n_estimators=n_estimators)
        if not rows.empty:
            targets = build_exit_targets(rows)
            target_rates["train_core"][stop_policy_id] = {target: float(targets[target].mean()) for target in EXIT_TARGETS}
    print(f"prepare train ml-exit fit complete elapsed={time.time() - started:.1f}", flush=True)
    return models, target_rates


def _score_decision_cache(
    entry_cache: dict[tuple[str, str, str, str], pd.DataFrame],
    ohlc: pd.DataFrame,
    models: dict[str, object],
) -> dict[tuple[str, str, str, str], pd.DataFrame]:
    scored: dict[tuple[str, str, str, str], pd.DataFrame] = {}
    for key, entries in entry_cache.items():
        split, stop_policy_id, _entry_id, mask_id = key
        if split == "train_core":
            continue
        filled = entries.loc[entries["filled"].astype(bool)].copy()
        if filled.empty:
            scored[key] = pd.DataFrame()
            continue
        decisions = build_exit_decision_rows(filled, ohlc)
        stop_models = models.get(stop_policy_id, {}) if isinstance(models.get(stop_policy_id, {}), dict) else {}
        scored[key] = score_exit_models({mask_id: stop_models.get(mask_id, {})}, decisions)
    return scored


def evaluate_winner_on_val_eval(winner: dict[str, object], val_eval_summary: pd.DataFrame) -> dict[str, object]:
    mask = val_eval_summary["entry_id"].eq(winner["entry_id"]) & val_eval_summary["mask_id"].eq(winner["mask_id"]) & val_eval_summary["exit_id"].eq(winner["exit_id"])
    if "stop_policy_id" in val_eval_summary.columns and "stop_policy_id" in winner:
        mask &= val_eval_summary["stop_policy_id"].eq(winner["stop_policy_id"])
    row = val_eval_summary[mask]
    return row.iloc[0].to_dict() if not row.empty else dict(winner)


def permutation_verdict(observed_bs_p05: float, null_best_bs_p05: list[float]) -> dict[str, object]:
    p = (1 + sum(float(v) >= float(observed_bs_p05) for v in null_best_bs_p05)) / (1 + len(null_best_bs_p05))
    return {"empirical_p_value": float(p), "status": "PASS" if p <= 0.10 else "RESEARCH_HINT", "null_repeats": len(null_best_bs_p05)}


def _permutation_groups(trades: pd.DataFrame) -> list[np.ndarray]:
    frame = trades.copy()
    if "exit_time" in frame.columns:
        frame["_perm_year"] = pd.to_datetime(frame["exit_time"], errors="coerce").dt.year.fillna(0).astype(int)
    else:
        frame["_perm_year"] = 0
    frame["_perm_side"] = frame["side"].astype(str) if "side" in frame.columns else "ALL"
    return [idx.to_numpy(dtype=int) for _, idx in frame.groupby(["_perm_year", "_perm_side"], sort=False).groups.items()]


def run_selection_permutation(
    summary: pd.DataFrame,
    trades: pd.DataFrame,
    repeats: int,
    seed: int,
    n_bootstrap: int = 200,
    heartbeat_every: int = 0,
) -> dict[str, object]:
    observed = float(select_winner(summary)["bs_p05"])
    rng = np.random.default_rng(seed)
    val_select_trades = trades.loc[trades["split"].eq("val_select")].copy() if "split" in trades.columns else trades.copy()
    val_select_trades = val_select_trades.reset_index(drop=True)
    if val_select_trades.empty:
        verdict = permutation_verdict(observed, [])
        verdict["null_best_bs_p05"] = []
        verdict["method"] = "block_shuffled_val_select_pnl_r"
        return verdict
    groups = _permutation_groups(val_select_trades)
    pnl = pd.to_numeric(val_select_trades["pnl_r"], errors="coerce").fillna(0.0).to_numpy()
    key_cols = ["entry_id", "mask_id", "exit_id"]
    if "stop_policy_id" in val_select_trades.columns and "stop_policy_id" in summary.columns:
        key_cols.insert(0, "stop_policy_id")
    summary_spread = None
    if "spread" in summary.columns:
        if summary["spread"].nunique(dropna=True) == 1:
            summary_spread = float(summary["spread"].dropna().iloc[0])
        if "spread" in val_select_trades.columns:
            key_cols.append("spread")
    null: list[float] = []
    for repeat in range(repeats):
        if heartbeat_every and repeat % heartbeat_every == 0:
            print(f"permutation repeat={repeat}/{repeats}", flush=True)
        shuffled = pnl.copy()
        for idx in groups:
            shuffled[idx] = rng.permutation(shuffled[idx])
        permuted = val_select_trades.copy()
        permuted["pnl_r"] = shuffled
        rows = []
        for keys, group in permuted.groupby(key_cols, sort=False):
            key_values = keys if isinstance(keys, tuple) else (keys,)
            run = dict(zip(key_cols, key_values))
            spread = float(run.get("spread", summary_spread if summary_spread is not None else CONFIG.canonical_spread))
            rows.append(_summary_from_trades(group, run, "val_select", spread, n_bootstrap=n_bootstrap))
        null.append(float(select_winner(pd.DataFrame(rows))["bs_p05"]))
    verdict = permutation_verdict(observed, null)
    verdict["null_best_bs_p05"] = null
    verdict["method"] = "block_shuffled_val_select_pnl_r"
    verdict["grouping"] = "year+side_when_available"
    verdict["observed_winner_bs_p05"] = observed
    verdict["metric_bootstrap_samples"] = int(n_bootstrap)
    return verdict


def compute_stop_diagnostics(trades: pd.DataFrame) -> list[dict[str, object]]:
    if trades.empty:
        return []
    required = {"stop_policy_id", "split", "stop_source"}
    if not required.issubset(trades.columns):
        return []
    rows: list[dict[str, object]] = []
    group_cols = ["stop_policy_id", "split", "stop_source"]
    for keys, group in trades.groupby(group_cols, dropna=False):
        stop_policy_id, split, stop_source = keys
        close_reason = group["close_reason"].astype(str)
        stop_distance = pd.to_numeric(group.get("stop_distance_atr"), errors="coerce")
        r_value = pd.to_numeric(group.get("r_value"), errors="coerce")
        rows.append(
            {
                "stop_policy_id": stop_policy_id,
                "split": split,
                "stop_source": stop_source,
                "n_trades": int(len(group)),
                "sl_count": int(close_reason.eq("SL").sum()),
                "sl_rate": float(close_reason.eq("SL").mean()),
                "median_stop_distance_atr": float(stop_distance.median()),
                "p10_stop_distance_atr": float(stop_distance.quantile(0.10)),
                "p90_stop_distance_atr": float(stop_distance.quantile(0.90)),
                "mean_r_value": float(r_value.mean()),
                "median_r_value": float(r_value.median()),
            }
        )
    return rows


def sample_size_warnings(summary: pd.DataFrame) -> list[dict[str, object]]:
    if summary.empty:
        return []
    warnings: list[dict[str, object]] = []
    for (split, mask_id), group in summary.groupby(["split", "mask_id"], dropna=False):
        n_trades = pd.to_numeric(group.get("n_trades"), errors="coerce")
        min_trades = int(n_trades.min()) if not n_trades.dropna().empty else 0
        median_trades = float(n_trades.median()) if not n_trades.dropna().empty else 0.0
        if str(mask_id) == "M1_frozen_movement_top5" and min_trades < 100:
            warnings.append(
                {
                    "split": split,
                    "mask_id": mask_id,
                    "warning": "low_trade_count_control_only",
                    "min_n_trades": min_trades,
                    "median_n_trades": median_trades,
                    "interpretation": "do_not_compare_to_M0_as_equal_sample",
                }
            )
    return warnings


def rejected_alternatives(summary: pd.DataFrame, winner: dict[str, object]) -> list[dict[str, object]]:
    if summary.empty:
        return []
    keys = ["stop_policy_id", "entry_id", "mask_id", "exit_id"]
    rows: list[dict[str, object]] = []
    wanted = [
        (
            "current_s0_fixed_r_baseline",
            {
                "stop_policy_id": "S0_current_0_5",
                "entry_id": "E3_open_pullback_1_0atr",
                "mask_id": "M0_no_mask",
                "exit_id": "X0_fixed_r_0_7",
                "split": "val_eval",
            },
            "S0 baseline retained for comparison; not selected by stop-grid val_select winner key.",
        ),
        (
            "s1_neighbor_same_family",
            {
                "stop_policy_id": "S1_fractal0_buffer_0_5_entry_floor_1",
                "entry_id": winner.get("entry_id"),
                "mask_id": winner.get("mask_id"),
                "exit_id": "X2_ml_opposite_any_p0_55",
                "split": "val_select",
            },
            "Neighbor stop policy had lower val_select BS_p05 than S2 winner.",
        ),
        (
            "s3_neighbor_same_key",
            {
                "stop_policy_id": "S3_fractal0_buffer_0_5_entry_floor_3",
                "entry_id": winner.get("entry_id"),
                "mask_id": winner.get("mask_id"),
                "exit_id": winner.get("exit_id"),
                "split": "val_select",
            },
            "Wider stop reduced SL rate but had lower val_select BS_p05 than S2.",
        ),
        (
            "diagnostic_best_val_eval_s2_e1",
            {
                "stop_policy_id": "S2_fractal0_buffer_0_5_entry_floor_2",
                "entry_id": "E1_simple_limit_at_fractal0",
                "mask_id": "M0_no_mask",
                "exit_id": "X2_ml_opposite_any_p0_50",
                "split": "val_eval",
            },
            "Best S2 row on val_eval is diagnostic-only; winner selection is restricted to val_select.",
        ),
    ]
    for alt_id, filters, reason in wanted:
        frame = summary
        for key, value in filters.items():
            frame = frame.loc[frame[key].eq(value)]
        if frame.empty:
            continue
        row = frame.iloc[0].to_dict()
        rows.append(
            {
                "alternative_id": alt_id,
                **{key: row.get(key) for key in (*keys, "split", "n_trades", "pf", "bs_p05", "risk_distance_atr", "tp_distance_atr")},
                "reason": reason,
            }
        )
    return rows


def decide_research_verdict(val_eval_metrics: dict[str, object], permutation: dict[str, object], stress_required: bool = True) -> dict[str, object]:
    reasons = []
    lifecycle = "research_hypothesis"
    if float(val_eval_metrics.get("pf") or 0) < 1.50 or float(val_eval_metrics.get("bs_p05") or 0) < 1.10 or int(val_eval_metrics.get("n_trades") or 0) < 300:
        lifecycle = "research_hint"
        reasons.append("val_eval_gate_failed")
    if stress_required and float(val_eval_metrics.get("stress_pf") or 0) < 1.20:
        lifecycle = "research_hint"
        reasons.append("stress_warning")
    if permutation.get("status") != "PASS":
        lifecycle = "research_hint"
        reasons.append("permutation_warning")
    if float(val_eval_metrics.get("ambiguous_same_bar_rate") or 0) > 0.10:
        lifecycle = "diagnostic_only"
        reasons.append("ambiguous_same_bar_rate_gt_0_10")
    elif float(val_eval_metrics.get("ambiguous_same_bar_rate") or 0) > 0.05:
        lifecycle = "research_hint"
        reasons.append("ambiguous_same_bar_rate_gt_0_05")
    return {"verdict": "research_only", "lifecycle_status": lifecycle, "reasons": reasons}


def run_one_config(
    run: dict[str, object],
    split_rows: dict[str, pd.DataFrame],
    ohlc: pd.DataFrame,
    ml_scores: dict[str, pd.DataFrame],
    spread: float,
    execution_ohlc: pd.DataFrame | None = None,
) -> dict[str, object]:
    split = str(run.get("split", "val_select"))
    entries = split_rows[split]
    scored = ml_scores.get(split)
    trades = _simulate_entries(entries, ohlc, run, spread, scored, execution_ohlc)
    trades["spread"] = float(spread)
    summary = _summary_from_trades(trades, run, split, spread)
    summary["trades"] = trades
    return summary


def run_matrix(args: argparse.Namespace) -> dict[str, object]:
    started = time.time()
    print("start fractal0_entry_exit_grid", flush=True)
    config = dataclasses.replace(CONFIG, output_prefix=args.output_prefix, execution_ohlc_path=args.execution_ohlc_path)
    preflight = preflight_inputs(config)
    print(f"preflight {preflight['status']}", flush=True)
    if preflight["status"] != "PASS":
        raise SystemExit(f"preflight failed: {preflight['errors']}")
    prefix = _path(args.output_prefix)
    progress_path = prefix.with_name(prefix.name + "_progress.json")
    active_stop_policies = stop_policy_grid() if args.stop_grid_mode == "full" else [stop_policy_grid()[0]]
    active_exits = exit_grid(None if args.exit_shortlist == "full" else args.exit_shortlist)
    stop_grid_entries = [entry for entry in entry_grid() if str(entry["entry_id"]) in STOP_GRID_ENTRY_IDS]
    requested_entries = stop_grid_entries if args.exit_shortlist == "stop_grid" else entry_grid()
    runs_all = expanded_grid(active_stop_policies=active_stop_policies, active_entries=requested_entries, active_exits=active_exits)
    runs = runs_all[: args.smoke_limit_runs] if args.smoke_limit_runs else runs_all
    cfg_hash = run_config_hash({"config": dataclasses.asdict(config), "grid": runs, "implementation": "real_ohlc_ml_exit_stop_policy_v1", "skip_stress_spread": bool(args.skip_stress_spread)})
    progress = load_progress(progress_path, cfg_hash) if args.resume else {"run_config_hash": cfg_hash, "completed": {}, "failed": {}}

    print("prepare load inputs", flush=True)
    ohlc = load_ohlc(config)
    execution_ohlc = prepare_execution_ohlc_index(load_ohlc_path(config.execution_ohlc_path)) if config.execution_ohlc_path else None
    if execution_ohlc is not None:
        print(f"prepare execution ohlc rows={len(execution_ohlc)} path={config.execution_ohlc_path}", flush=True)
    splits = load_role_splits(config)
    if args.smoke_limit_runs:
        splits = {name: frame.head(500).copy().reset_index(drop=True) for name, frame in splits.items()}
        for name, frame in splits.items():
            frame["split"] = name
            frame["split_row_id"] = np.arange(len(frame), dtype=int)
    frozen_scores = _read_frozen_scores(config)
    run_entry_ids = {str(run["entry_id"]) for run in runs}
    run_mask_ids = {str(run["mask_id"]) for run in runs}
    run_stop_ids = {str(run["stop_policy_id"]) for run in runs}
    active_entries = [entry for entry in entry_grid() if str(entry["entry_id"]) in run_entry_ids]
    active_masks = [mask for mask in mask_grid() if str(mask["mask_id"]) in run_mask_ids]
    active_stop_policies = [policy for policy in active_stop_policies if str(policy["stop_policy_id"]) in run_stop_ids]
    print("prepare entry cache canonical", flush=True)
    canonical_entry_cache, cache_report = _entry_cache_for_spread(
        splits,
        ohlc,
        CONFIG.canonical_spread,
        frozen_scores,
        active_stop_policies,
        active_entries,
        active_masks,
        execution_ohlc,
    )
    stress_entry_cache = {}
    if not args.skip_stress_spread:
        print("prepare entry cache stress", flush=True)
        stress_entry_cache, _ = _entry_cache_for_spread(
            {"val_eval": splits["val_eval"]},
            ohlc,
            CONFIG.stress_spread,
            frozen_scores,
            active_stop_policies,
            active_entries,
            active_masks,
            execution_ohlc,
        )
    print("prepare train ml-exit", flush=True)
    ml_seeds = (42,) if args.smoke_limit_runs else EXIT_MODEL_SEEDS
    ml_estimators = 25 if args.smoke_limit_runs else 200
    ml_models, target_rates = _train_ml_exit_layer(canonical_entry_cache, ohlc, int(args.threads), seeds=ml_seeds, n_estimators=ml_estimators)
    print("prepare score ml-exit canonical", flush=True)
    canonical_decisions = _score_decision_cache(canonical_entry_cache, ohlc, ml_models)
    stress_decisions = {}
    if not args.skip_stress_spread:
        print("prepare score ml-exit stress", flush=True)
        stress_decisions = _score_decision_cache(stress_entry_cache, ohlc, ml_models)

    summary_rows: list[dict[str, object]] = []
    stress_rows: list[dict[str, object]] = []
    trade_frames: list[pd.DataFrame] = []
    total_runs = len(runs) * (2 if args.skip_stress_spread else 3)
    done_runs = 0
    for run in runs:
        for split in ("val_select", "val_eval"):
            run_with_split = {**run, "split": split}
            key = resume_key({**run_with_split, "spread": CONFIG.canonical_spread})
            if key in progress["completed"]:
                summary_rows.append(progress["completed"][key])
                done_runs += 1
                continue
            try:
                entry_key = (split, str(run["stop_policy_id"]), str(run["entry_id"]), str(run["mask_id"]))
                result = run_one_config(
                    run_with_split,
                    {split: canonical_entry_cache[entry_key]},
                    ohlc,
                    {split: canonical_decisions.get(entry_key, pd.DataFrame())},
                    CONFIG.canonical_spread,
                    execution_ohlc,
                )
                trades = result.pop("trades")
                if not trades.empty:
                    trade_frames.append(trades)
                summary_rows.append(result)
                progress["completed"][key] = result
            except Exception as exc:  # pragma: no cover - defensive runner behavior
                progress["failed"][key] = {"error": str(exc), "run": run_with_split}
            done_runs += 1
            write_progress_atomic(progress_path, progress)
            print(f"progress done_runs={done_runs}/{total_runs} elapsed={time.time() - started:.1f}", flush=True)

        if not args.skip_stress_spread:
            stress_run = {**run, "split": "val_eval"}
            stress_key = resume_key({**stress_run, "spread": CONFIG.stress_spread})
            try:
                entry_key = ("val_eval", str(run["stop_policy_id"]), str(run["entry_id"]), str(run["mask_id"]))
                stress_result = run_one_config(
                    stress_run,
                    {"val_eval": stress_entry_cache[entry_key]},
                    ohlc,
                    {"val_eval": stress_decisions.get(entry_key, pd.DataFrame())},
                    CONFIG.stress_spread,
                    execution_ohlc,
                )
                stress_result.pop("trades", None)
                stress_rows.append(stress_result)
                progress["completed"][stress_key] = stress_result
            except Exception as exc:  # pragma: no cover - defensive runner behavior
                progress["failed"][stress_key] = {"error": str(exc), "run": stress_run}
            done_runs += 1
            write_progress_atomic(progress_path, progress)
            print(f"progress done_runs={done_runs}/{total_runs} elapsed={time.time() - started:.1f}", flush=True)

    summary = pd.DataFrame(summary_rows)
    stress_summary = pd.DataFrame(stress_rows)
    if summary.empty:
        raise SystemExit("matrix produced no summary rows")
    val_select_summary = summary.loc[summary["split"].eq("val_select")].copy()
    val_eval_summary = summary.loc[summary["split"].eq("val_eval")].copy()
    winner = select_winner(val_select_summary)
    eval_metrics = evaluate_winner_on_val_eval(winner, val_eval_summary)
    if not stress_summary.empty:
        stress_match = stress_summary.loc[
            stress_summary["entry_id"].eq(winner["entry_id"])
            & stress_summary["mask_id"].eq(winner["mask_id"])
            & stress_summary["exit_id"].eq(winner["exit_id"])
            & stress_summary["stop_policy_id"].eq(winner["stop_policy_id"])
        ]
        if not stress_match.empty:
            eval_metrics["stress_pf"] = stress_match.iloc[0].get("pf")
    attribution = compute_attribution(summary, winner)
    trades = pd.concat(trade_frames, ignore_index=True) if trade_frames else pd.DataFrame()
    permutation = run_selection_permutation(val_select_summary, trades, int(args.permutation_repeats), CONFIG.permutation_seed)
    verdict = decide_research_verdict(eval_metrics, permutation, stress_required=not args.skip_stress_spread)
    yearly = pd.DataFrame(yearly_metrics(trades))
    winner_yearly = pd.DataFrame(yearly_metrics(filter_trades_for_rule(trades, winner, split="val_eval", spread=CONFIG.canonical_spread)))
    if not winner_yearly.empty:
        winner_yearly.insert(0, "metric_split", "val_eval")
        winner_yearly.insert(0, "spread", CONFIG.canonical_spread)
        winner_yearly.insert(0, "exit_id", winner["exit_id"])
        winner_yearly.insert(0, "mask_id", winner["mask_id"])
        winner_yearly.insert(0, "entry_id", winner["entry_id"])
        winner_yearly.insert(0, "stop_policy_id", winner["stop_policy_id"])
    stop_diagnostics = pd.DataFrame(compute_stop_diagnostics(trades))
    sample_warnings = sample_size_warnings(summary)
    alternatives = rejected_alternatives(summary, winner)
    selection_cells = len(active_stop_policies) * len(active_entries) * len(active_masks) * len(active_exits)
    stress_spread_status = "deferred_shortlist_only" if args.skip_stress_spread else "computed"
    artifact = {
        **preflight,
        **verdict,
        "locked_test": "not_opened",
        "canonical_current_artifact": str(prefix.with_suffix(".json")),
        "post_review_artifacts": [],
        "superseded_fields": [],
        "rows_by_split_before_after_mask": cache_report["rows_by_split_before_after_mask"],
        "fill_rate_by_entry": cache_report["fill_rate_by_entry"],
        "ambiguous_same_bar_rate": float(eval_metrics.get("ambiguous_same_bar_rate") or 0.0),
        "ml_feature_columns_used": {"M0_no_mask": exit_feature_columns("M0_no_mask"), "M1_frozen_movement_top5": exit_feature_columns("M1_frozen_movement_top5")},
        "ml_target_positive_rate_by_split": target_rates,
        "current_search_budget": {
            "selection_cells": selection_cells,
            "expected_completed_without_stress": selection_cells * 2,
            "stress_cells": 0 if args.skip_stress_spread else selection_cells,
            "ml_exit_model_jobs": len(active_stop_policies) * len(active_exits),
            "permutation_repeats": int(args.permutation_repeats),
        },
        "cumulative_search_budget": {"status": "disclosed_current_stage_only"},
        "stop_policy_grid": stop_policy_grid(),
        "exact_grid": {"stop_policies": active_stop_policies, "entries": active_entries, "masks": active_masks, "exits": active_exits},
        "winner_selection_key": "stop_policy_id + entry_id + mask_id + exit_id",
        "permutation_key": "stop_policy_id + entry_id + mask_id + exit_id",
        "stress_spread_status": stress_spread_status,
        "stress_spread_interpretation": "configured_but_not_computed" if args.skip_stress_spread else "computed",
        "fixed_risk_interpretation": "pnl_r assumes equal risk per trade, not equal lot size",
        "multiple_testing_correction": permutation,
        "ml_exit_target_contracts": list(EXIT_TARGETS),
        "pnl_convention": {"ohlc_price_type": "bid", "spread": "full bid-ask spread", "same_bar_tp_sl_policy": CONFIG.same_bar_tp_sl_policy, "execution_ohlc_path": config.execution_ohlc_path or None, "execution_ohlc_usage": "limit_fill_timestamp_and_same_h1_post_fill_event_order" if config.execution_ohlc_path else None},
        "simulator_test_status": "covered_by_unit_tests",
        "attribution_status": "computed",
        "stop_diagnostics_status": "computed",
        "movement_mask_live_cutoff_status": "no_absolute_live_cutoff",
        "sample_size_warning_status": "computed",
        "sample_size_warnings": sample_warnings,
        "selected_winner": {k: _jsonable(v) for k, v in winner.items()},
        "val_select_winner_metrics": {k: _jsonable(v) for k, v in winner.items()},
        "val_eval_winner_metrics": {k: _jsonable(v) for k, v in eval_metrics.items()},
        "rejected_alternatives": alternatives,
        "split_roles": {"train_core": "model_training_only", "val_select": "winner_selection", "val_eval": "frozen_rule_check"},
        "canonical_spread": CONFIG.canonical_spread,
        "stress_spread": CONFIG.stress_spread,
        "yearly_scope": "all_grid_simulated_trade_rows",
        "winner_yearly_scope": "selected_winner_val_eval_only",
        "attribution": attribution,
        "forbidden_interpretations": ["production ready", "live-ready", "tradable", "ready_for_locked_test"],
        "allowed_max_verdict": CONFIG.allowed_max_verdict,
    }
    prefix.parent.mkdir(parents=True, exist_ok=True)
    prefix.with_suffix(".json").write_text(json.dumps(artifact, ensure_ascii=True, indent=2, default=str), encoding="utf-8")
    summary.drop(columns=[], errors="ignore").to_csv(prefix.with_name(prefix.name + "_summary.csv"), index=False, sep=";")
    trades.to_csv(prefix.with_name(prefix.name + "_trades.csv"), index=False, sep=";")
    yearly.to_csv(prefix.with_name(prefix.name + "_yearly.csv"), index=False, sep=";")
    yearly.to_csv(prefix.with_name(prefix.name + "_all_grid_yearly.csv"), index=False, sep=";")
    winner_yearly.to_csv(prefix.with_name(prefix.name + "_winner_yearly.csv"), index=False, sep=";")
    if args.skip_stress_spread:
        pd.DataFrame(
            [
                {
                    "stress_spread_status": stress_spread_status,
                    "stress_spread": CONFIG.stress_spread,
                    "reason": "full stress-spread deferred to shortlist-only follow-up",
                }
            ]
        ).to_csv(prefix.with_name(prefix.name + "_spread_stress.csv"), index=False, sep=";")
    else:
        stress_summary.to_csv(prefix.with_name(prefix.name + "_spread_stress.csv"), index=False, sep=";")
    stop_diagnostics.to_csv(prefix.with_name(prefix.name + "_stop_diagnostics.csv"), index=False, sep=";")
    pd.DataFrame(attribution).to_csv(prefix.with_name(prefix.name + "_attribution.csv"), index=False, sep=";")
    pd.DataFrame({"null_best_bs_p05": permutation.get("null_best_bs_p05", [])}).to_csv(prefix.with_name(prefix.name + "_permutation.csv"), index=False, sep=";")
    print("finished fractal0_entry_exit_grid", flush=True)
    return artifact


def _jsonable(value: object) -> object:
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    return value


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--threads", type=int, default=CONFIG.default_threads)
    parser.add_argument("--output-prefix", default=CONFIG.output_prefix)
    parser.add_argument("--resume", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--smoke-limit-runs", type=int, default=0)
    parser.add_argument("--permutation-repeats", type=int, default=CONFIG.permutation_repeats)
    parser.add_argument("--execution-ohlc-path", default=CONFIG.execution_ohlc_path)
    parser.add_argument("--stop-grid-mode", choices=("full", "current-only"), default="full")
    parser.add_argument("--exit-shortlist", choices=("full", "stop_grid"), default="full")
    parser.add_argument("--skip-stress-spread", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    run_matrix(parse_args(argv))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
