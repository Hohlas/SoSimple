from __future__ import annotations

# =============================================================================
# Файл: benchmark_fractal0_price_entry_mechanics.py
# Назначение: Oracle-preflight входа через возврат цены к зоне fractal0_price.
# Обновлён: 2026-07-10
# Использование:
#   ./.venv/bin/python ML/baseline/benchmark_fractal0_price_entry_mechanics.py --fractal0-entry-mechanics
# =============================================================================

import argparse
import dataclasses
import datetime as dt
import json
import math
import os
from pathlib import Path
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from ML.baseline import benchmark_next_open_entry_updn_foundation as next_open


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORTS_DIR = PROJECT_ROOT / "ML" / "reports"
REPORT_JSON_PATH = REPORTS_DIR / "fractal0_price_entry_mechanics.json"
REPORT_ROWS_PATH = REPORTS_DIR / "fractal0_price_entry_mechanics_rows.csv"


@dataclasses.dataclass(frozen=True)
class Fractal0EntryMechanicsConfig:
    experiment: str = "fractal0_price_entry_mechanics"
    research_level: str = "search"
    initial_lifecycle_status: str = "research_scan"
    lifecycle_if_gate_pass: str = "research_hypothesis"
    origin_bias: str = "post_mortem"
    research_priority: str = "high"
    allowed_max_verdict: str = "research_only"
    verdict_if_gate_pass: str = "research_only"
    verdict_if_gate_fail: str = "diagnostic_only"
    entry_mechanics: tuple[str, ...] = ("retest_zone",)
    entry_price_modes: tuple[str, ...] = ("limit_at_fractal0", "zone_edge")
    zone_width_atr: tuple[float, ...] = (0.0, 0.25, 0.5)
    max_fill_lag_bars: tuple[int, ...] = (3, 6)
    horizons: tuple[int, ...] = (3, 6, 12)
    spread_values: tuple[float, ...] = (0.0, 0.2, 0.4)
    side_rule: str = "direction = -fractal0.dir"
    first_order_eligible_bar_offset: int = 1
    primary_selection_split: str = "train_core"
    primary_eval_split: str = "val_stop"
    disclosure_splits: tuple[str, ...] = ("diagnostic_holdout", "low_n_disclosure")
    min_filled_events_total_train_core: int = 300
    min_filled_events_total_val_stop: int = 150
    min_filled_events_per_year_val_stop: int = 30
    min_years_or_windows_val_stop: int = 3
    max_no_fill_rate_val_stop: float = 0.70
    canonical_spread: float = 0.2
    stress_spread: float = 0.4
    canonical_favorable_to_adverse_ratio_min: float = 1.05
    stress_favorable_to_adverse_ratio_min: float = 0.95
    ratio_without_best_year_min: float = 0.95
    prior_search_budget_lower_bound: int = 76


CONFIG = Fractal0EntryMechanicsConfig()
REPORT_REQUIRED_FIELDS = (
    "experiment",
    "verdict",
    "lifecycle_status",
    "research_level",
    "origin_bias",
    "research_priority",
    "allowed_max_verdict",
    "current_search_budget",
    "cumulative_search_budget_lower_bound",
    "cumulative_search_budget_status",
    "target_contract",
    "execution_contract",
    "forbidden_interpretations",
    "side_contract_audit",
    "oracle_summary",
    "selected_train_rule",
    "research_gate",
)


def parse_fractal0(value: object) -> dict | None:
    parts = str(value).split(":")
    if len(parts) < 23:
        return None
    try:
        return {
            "time": int(float(parts[0])),
            "price": float(parts[1]),
            "direction": int(float(parts[2])),
            "shift": int(float(parts[22])),
        }
    except (TypeError, ValueError):
        return None


def trade_side_from_fractal_direction(direction: object) -> str | None:
    try:
        value = float(direction)
    except (TypeError, ValueError):
        return None
    if math.isnan(value) or value == 0:
        return None
    return "SELL" if value > 0 else "BUY"


def _current_search_budget() -> int:
    return (
        len(CONFIG.entry_mechanics)
        * len(CONFIG.entry_price_modes)
        * len(CONFIG.zone_width_atr)
        * len(CONFIG.max_fill_lag_bars)
        * len(CONFIG.horizons)
        * len(CONFIG.spread_values)
    )


def fractal0_entry_config() -> dict[str, object]:
    config = dataclasses.asdict(CONFIG)
    for key in (
        "entry_mechanics",
        "entry_price_modes",
        "zone_width_atr",
        "max_fill_lag_bars",
        "horizons",
        "spread_values",
        "disclosure_splits",
    ):
        config[key] = list(config[key])
    current = _current_search_budget()
    config["current_search_budget"] = current
    config["cumulative_search_budget_status"] = "lower_bound_disclosed"
    config["cumulative_search_budget_lower_bound"] = CONFIG.prior_search_budget_lower_bound + current
    config["locked_test"] = "not_opened"
    return config


def audit_side_contract(rows: pd.DataFrame) -> dict:
    directions = pd.to_numeric(rows.get("fractal0_direction"), errors="coerce").dropna().astype(int)
    counts = {str(key): int(value) for key, value in directions.value_counts().sort_index().items()}
    return {
        "status": "PASS" if set(counts).issubset({"-1", "1"}) and counts else "FAIL",
        "direction_counts": counts,
        "required_before_research_only": True,
        "side_rule": CONFIG.side_rule,
        "note": "Project contract: direction = -fractal0.dir; -1 -> BUY, 1 -> SELL.",
    }


def parse_project_time(value: object) -> pd.Timestamp:
    return next_open.parse_project_time(value)


def _safe_float(value: object) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return float("nan")
    return out


def first_order_eligible_index(signal_time: pd.Timestamp, ohlc: pd.DataFrame, offset: int) -> int | None:
    if pd.isna(signal_time):
        return None
    times = ohlc["parsed_time"].to_numpy()
    first_after_signal = int(times.searchsorted(signal_time.to_datetime64(), side="right"))
    idx = first_after_signal + int(offset)
    return idx if idx < len(ohlc) else None


def _reachable_zone_entry_price(low: float, high: float, center: float, lower: float, upper: float) -> float | None:
    if low <= center <= high:
        return float(center)
    if high < lower or low > upper:
        return None
    reachable_lower = max(low, lower)
    reachable_upper = min(high, upper)
    if reachable_lower > reachable_upper:
        return None
    if high < center:
        return float(lower) if low <= lower <= high else float(reachable_upper)
    if low > center:
        return float(upper) if low <= upper <= high else float(reachable_lower)
    return float(center)


def resolve_retest_zone_fill(
    signal_time: pd.Timestamp,
    fractal0_price: float,
    atr: float,
    zone_width_atr: float,
    max_fill_lag_bars: int,
    entry_price_mode: str,
    ohlc: pd.DataFrame,
) -> dict:
    if pd.isna(signal_time) or not np.isfinite(fractal0_price) or not np.isfinite(atr) or atr <= 0:
        return {"filled": False, "fill_time": pd.NaT, "fill_index": None, "fill_lag_bars": None, "entry_price": np.nan}
    start = first_order_eligible_index(signal_time, ohlc, CONFIG.first_order_eligible_bar_offset)
    if start is None:
        return {"filled": False, "fill_time": pd.NaT, "fill_index": None, "fill_lag_bars": None, "entry_price": np.nan}

    zone_width = float(zone_width_atr) * float(atr)
    center = float(fractal0_price)
    lower = center - zone_width
    upper = center + zone_width
    times = ohlc["parsed_time"].to_numpy()
    end = min(start + int(max_fill_lag_bars), len(ohlc))

    for pos in range(start, end):
        high = float(ohlc.iloc[pos]["high"])
        low = float(ohlc.iloc[pos]["low"])
        entry_price = None
        if entry_price_mode == "limit_at_fractal0":
            entry_price = center if low <= center <= high else None
        elif entry_price_mode == "zone_edge":
            entry_price = _reachable_zone_entry_price(low, high, center, lower, upper)
        else:
            raise ValueError(f"Unknown entry_price_mode: {entry_price_mode}")
        if entry_price is not None:
            return {
                "filled": True,
                "fill_time": pd.Timestamp(times[pos]),
                "fill_index": int(pos),
                "fill_lag_bars": int(pos - start + 1),
                "entry_price": float(entry_price),
            }

    return {"filled": False, "fill_time": pd.NaT, "fill_index": None, "fill_lag_bars": None, "entry_price": np.nan}


def compute_future_updn_from_fill(
    fill_index: int,
    horizon: int,
    ohlc: pd.DataFrame,
    entry_price: float,
) -> tuple[float, float]:
    end = int(fill_index) + int(horizon)
    if end > len(ohlc):
        return np.nan, np.nan
    window = ohlc.iloc[int(fill_index) : end]
    up = max(float(window["high"].max()) - float(entry_price), 0.0)
    dn = max(float(entry_price) - float(window["low"].min()), 0.0)
    return float(np.round(up, 10)), float(np.round(dn, 10))


def build_retest_rows(
    df: pd.DataFrame,
    ohlc: pd.DataFrame,
    zone_width_atr: float,
    max_fill_lag_bars: int,
    entry_price_mode: str,
    horizons: tuple[int, ...],
) -> pd.DataFrame:
    out = df.copy().reset_index(drop=True)
    if "signal_time" not in out.columns:
        out["signal_time"] = out["time"].map(parse_project_time)
    if "fractal0_price" not in out.columns or "fractal0_direction" not in out.columns:
        parsed = out["fractal0"].map(parse_fractal0)
        out["fractal0_price"] = parsed.map(lambda item: item["price"] if item else np.nan)
        out["fractal0_direction"] = parsed.map(lambda item: item["direction"] if item else np.nan)
    out["side_rule"] = CONFIG.side_rule
    out["side"] = out["fractal0_direction"].map(trade_side_from_fractal_direction)
    out["entry_price_mode"] = entry_price_mode
    out["zone_width_atr"] = float(zone_width_atr)
    out["max_fill_lag_bars"] = int(max_fill_lag_bars)
    out["filled"] = False
    out["fill_time"] = pd.NaT
    out["fill_index"] = pd.Series(pd.NA, index=out.index, dtype="Int64")
    out["fill_lag_bars"] = pd.Series(pd.NA, index=out.index, dtype="Int64")
    out["entry_price"] = np.nan

    for horizon in horizons:
        out[f"target_entry_up_{horizon}"] = np.nan
        out[f"target_entry_dn_{horizon}"] = np.nan
        out[f"target_entry_log_ratio_{horizon}"] = np.nan
        out[f"has_full_h{horizon}"] = False

    ohlc_times = ohlc["parsed_time"].to_numpy()
    highs = ohlc["high"].to_numpy(dtype=float)
    lows = ohlc["low"].to_numpy(dtype=float)
    signal_times = out["signal_time"].to_numpy()
    prices = pd.to_numeric(out["fractal0_price"], errors="coerce").to_numpy(dtype=float)
    atrs = pd.to_numeric(out["ATR"], errors="coerce").to_numpy(dtype=float)
    row_count = len(out)
    filled_values = np.zeros(row_count, dtype=bool)
    fill_time_values = np.full(row_count, np.datetime64("NaT"), dtype="datetime64[ns]")
    fill_index_values = np.full(row_count, -1, dtype=np.int64)
    fill_lag_values = np.full(row_count, -1, dtype=np.int64)
    entry_price_values = np.full(row_count, np.nan, dtype=float)
    has_full_values = {horizon: np.zeros(row_count, dtype=bool) for horizon in horizons}
    target_up_values = {horizon: np.full(row_count, np.nan, dtype=float) for horizon in horizons}
    target_dn_values = {horizon: np.full(row_count, np.nan, dtype=float) for horizon in horizons}
    target_log_ratio_values = {horizon: np.full(row_count, np.nan, dtype=float) for horizon in horizons}

    for idx, (signal_time, price, atr) in enumerate(zip(signal_times, prices, atrs, strict=True)):
        signal_ts = pd.Timestamp(signal_time)
        if pd.isna(signal_ts) or not np.isfinite(price) or not np.isfinite(atr) or atr <= 0:
            continue
        start = int(ohlc_times.searchsorted(signal_ts.to_datetime64(), side="right")) + CONFIG.first_order_eligible_bar_offset
        if start >= len(ohlc):
            continue

        center = float(price)
        zone_width = float(zone_width_atr) * float(atr)
        lower = center - zone_width
        upper = center + zone_width
        end = min(start + int(max_fill_lag_bars), len(ohlc))
        fill_index = None
        entry_price = np.nan
        for pos in range(start, end):
            high = float(highs[pos])
            low = float(lows[pos])
            if entry_price_mode == "limit_at_fractal0":
                candidate = center if low <= center <= high else None
            elif entry_price_mode == "zone_edge":
                candidate = _reachable_zone_entry_price(low, high, center, lower, upper)
            else:
                raise ValueError(f"Unknown entry_price_mode: {entry_price_mode}")
            if candidate is not None:
                fill_index = int(pos)
                entry_price = float(candidate)
                break
        if fill_index is None:
            continue

        filled_values[idx] = True
        fill_time_values[idx] = ohlc_times[fill_index]
        entry_price_values[idx] = entry_price
        fill_index_values[idx] = fill_index
        fill_lag_values[idx] = int(fill_index - start + 1)

        for horizon in horizons:
            target_end = fill_index + int(horizon)
            if target_end > len(ohlc):
                continue
            up = max(float(np.max(highs[fill_index:target_end])) - entry_price, 0.0)
            dn = max(entry_price - float(np.min(lows[fill_index:target_end])), 0.0)
            up = float(np.round(up, 10))
            dn = float(np.round(dn, 10))
            has_full_values[horizon][idx] = True
            target_up_values[horizon][idx] = up
            target_dn_values[horizon][idx] = dn
            target_log_ratio_values[horizon][idx] = float(next_open.safe_log_ratio(np.array([up]), np.array([dn]))[0])

    out["filled"] = filled_values
    out["fill_time"] = pd.to_datetime(fill_time_values)
    out["entry_price"] = entry_price_values
    out["fill_index"] = pd.Series(fill_index_values).mask(fill_index_values < 0).astype("Int64")
    out["fill_lag_bars"] = pd.Series(fill_lag_values).mask(fill_lag_values < 0).astype("Int64")
    for horizon in horizons:
        out[f"has_full_h{horizon}"] = has_full_values[horizon]
        out[f"target_entry_up_{horizon}"] = target_up_values[horizon]
        out[f"target_entry_dn_{horizon}"] = target_dn_values[horizon]
        out[f"target_entry_log_ratio_{horizon}"] = target_log_ratio_values[horizon]

    return out


def compute_oracle_mfe_rows(rows: pd.DataFrame, horizon: int, spread: float) -> pd.DataFrame:
    active = rows.loc[rows["filled"].astype(bool)].copy()
    up_col = f"target_entry_up_{horizon}"
    dn_col = f"target_entry_dn_{horizon}"
    active = active.loc[active[up_col].notna() & active[dn_col].notna()].copy()
    buy_mask = active["side"] == "BUY"
    sell_mask = active["side"] == "SELL"
    active["oracle_favorable_move_after_cost"] = np.nan
    active["oracle_adverse_move"] = np.nan
    active.loc[buy_mask, "oracle_favorable_move_after_cost"] = pd.to_numeric(active.loc[buy_mask, up_col], errors="coerce") - float(spread)
    active.loc[buy_mask, "oracle_adverse_move"] = pd.to_numeric(active.loc[buy_mask, dn_col], errors="coerce")
    active.loc[sell_mask, "oracle_favorable_move_after_cost"] = pd.to_numeric(active.loc[sell_mask, dn_col], errors="coerce") - float(spread)
    active.loc[sell_mask, "oracle_adverse_move"] = pd.to_numeric(active.loc[sell_mask, up_col], errors="coerce")
    active["horizon"] = int(horizon)
    active["spread"] = float(spread)
    return active.reset_index(drop=True)


def _ratio_without_best_year(events: pd.DataFrame) -> float | None:
    if events.empty:
        return None
    years = pd.to_datetime(events["time"]).dt.year
    yearly = events.groupby(years)["oracle_favorable_move_after_cost"].sum()
    if len(yearly) <= 1:
        return None
    best_year = yearly.idxmax()
    reduced = events.loc[years != best_year]
    return summarize_mfe_metrics(reduced, rows_total=len(reduced), rows_filled=len(reduced))["favorable_to_adverse_ratio"]


def summarize_mfe_metrics(events: pd.DataFrame, rows_total: int, rows_filled: int) -> dict:
    if events.empty:
        return {
            "rows_total": int(rows_total),
            "filled_events": int(rows_filled),
            "no_fill_rate": 1.0 if rows_total else 0.0,
            "favorable_sum_after_cost": 0.0,
            "adverse_sum": 0.0,
            "favorable_to_adverse_ratio": None,
            "active_years": 0,
            "filled_events_per_year_min": 0,
            "ratio_without_best_year": None,
        }
    favorable = pd.to_numeric(events["oracle_favorable_move_after_cost"], errors="coerce").fillna(0.0)
    adverse = pd.to_numeric(events["oracle_adverse_move"], errors="coerce").fillna(0.0)
    favorable_sum = float(favorable.sum())
    adverse_sum = float(adverse.sum())
    years = pd.to_datetime(events["time"]).dt.year
    per_year = events.groupby(years).size()
    return {
        "rows_total": int(rows_total),
        "filled_events": int(rows_filled),
        "no_fill_rate": float(1.0 - rows_filled / rows_total) if rows_total else 0.0,
        "favorable_sum_after_cost": float(np.round(favorable_sum, 10)),
        "adverse_sum": float(np.round(adverse_sum, 10)),
        "favorable_to_adverse_ratio": float(favorable_sum / adverse_sum) if adverse_sum > 0 else None,
        "active_years": int(per_year.size),
        "filled_events_per_year_min": int(per_year.min()) if len(per_year) else 0,
        "ratio_without_best_year": _ratio_without_best_year(events),
    }


def research_gate(selected_train_summary: dict, eval_summary: dict, side_contract_audit: dict) -> dict:
    checks = {
        "side_contract_status": side_contract_audit.get("status") == "PASS",
        "selected_on_train_core": selected_train_summary.get("spread") == CONFIG.canonical_spread,
        "zero_spread_not_gate": eval_summary.get("spread") != 0.0,
        "min_filled_events_total_train_core": selected_train_summary.get("filled_events", 0) >= CONFIG.min_filled_events_total_train_core,
        "min_filled_events_total_val_stop": eval_summary.get("filled_events", 0) >= CONFIG.min_filled_events_total_val_stop,
        "min_filled_events_per_year_val_stop": eval_summary.get("filled_events_per_year_min", 0) >= CONFIG.min_filled_events_per_year_val_stop,
        "min_years_or_windows_val_stop": eval_summary.get("active_years", 0) >= CONFIG.min_years_or_windows_val_stop,
        "max_no_fill_rate_val_stop": eval_summary.get("no_fill_rate", 1.0) <= CONFIG.max_no_fill_rate_val_stop,
        "canonical_favorable_to_adverse_ratio": (
            eval_summary.get("favorable_to_adverse_ratio") is not None
            and eval_summary["favorable_to_adverse_ratio"] >= CONFIG.canonical_favorable_to_adverse_ratio_min
        ),
        "stress_favorable_to_adverse_ratio": (
            eval_summary.get("stress_favorable_to_adverse_ratio") is not None
            and eval_summary["stress_favorable_to_adverse_ratio"] >= CONFIG.stress_favorable_to_adverse_ratio_min
        ),
        "ratio_without_best_year": (
            eval_summary.get("ratio_without_best_year") is not None
            and eval_summary["ratio_without_best_year"] >= CONFIG.ratio_without_best_year_min
        ),
    }
    return {
        "passes": all(checks.values()),
        "checks": checks,
        "verdict_if_pass": CONFIG.verdict_if_gate_pass,
        "lifecycle_if_pass": CONFIG.lifecycle_if_gate_pass,
        "verdict_if_fail": CONFIG.verdict_if_gate_fail,
        "forbidden_terms": ["PnL", "PF", "profitable", "tradable", "live-ready"],
    }


def validate_report(report: dict) -> list[str]:
    return [field for field in REPORT_REQUIRED_FIELDS if field not in report]


def select_best_train_rule(oracle_summary: dict) -> dict:
    train = oracle_summary.get(CONFIG.primary_selection_split, {})
    candidates = {
        key: value
        for key, value in train.items()
        if value.get("spread") == CONFIG.canonical_spread
    }
    if not candidates:
        return {"key": None, "selection_split": CONFIG.primary_selection_split, "summary": None}
    key = max(
        candidates,
        key=lambda item: candidates[item].get("favorable_to_adverse_ratio") or -1.0,
    )
    return {"key": key, "selection_split": CONFIG.primary_selection_split, "summary": candidates[key]}


def _rows_output_view(rows: pd.DataFrame) -> pd.DataFrame:
    base_columns = [
        "split_name",
        "time",
        "signal_time",
        "fractal0_price",
        "fractal0_direction",
        "side_rule",
        "side",
        "entry_price_mode",
        "zone_width_atr",
        "max_fill_lag_bars",
        "filled",
        "fill_time",
        "fill_lag_bars",
        "entry_price",
    ]
    target_columns = [
        column
        for column in rows.columns
        if column.startswith("target_entry_") or column.startswith("has_full_h")
    ]
    return rows.loc[:, [column for column in base_columns + target_columns if column in rows.columns]].copy()


def _rule_key(entry_price_mode: str, zone_width: float, fill_lag: int, horizon: int, spread: float) -> str:
    return (
        f"entry_{entry_price_mode}"
        f"_zone_{zone_width}"
        f"_lag_{fill_lag}"
        f"_h{horizon}"
        f"_spread_{spread}"
    )


def run_fractal0_entry_mechanics(
    output_path: Path = REPORT_JSON_PATH,
    rows_path: Path = REPORT_ROWS_PATH,
) -> dict:
    started_at = dt.datetime.now(dt.timezone.utc).isoformat()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ohlc = next_open.load_ohlc()
    split_frames = next_open.load_research_splits()

    all_rows = []
    oracle_summary: dict[str, dict] = {}
    side_contract_audit = {"status": "FAIL", "required_before_research_only": True}

    for split_name, frame in split_frames.items():
        prepared_frame = frame.copy()
        prepared_frame["signal_time"] = prepared_frame["time"].map(parse_project_time)
        parsed = prepared_frame["fractal0"].map(parse_fractal0)
        prepared_frame["fractal0_price"] = parsed.map(lambda item: item["price"] if item else np.nan)
        prepared_frame["fractal0_direction"] = parsed.map(lambda item: item["direction"] if item else np.nan)
        split_summary: dict[str, dict] = {}
        for entry_price_mode in CONFIG.entry_price_modes:
            for zone_width in CONFIG.zone_width_atr:
                for fill_lag in CONFIG.max_fill_lag_bars:
                    rebuilt = build_retest_rows(
                        prepared_frame,
                        ohlc,
                        zone_width_atr=float(zone_width),
                        max_fill_lag_bars=int(fill_lag),
                        entry_price_mode=entry_price_mode,
                        horizons=CONFIG.horizons,
                    )
                    rebuilt["split_name"] = split_name
                    all_rows.append(_rows_output_view(rebuilt))
                    if split_name == CONFIG.primary_selection_split:
                        side_contract_audit = audit_side_contract(rebuilt)
                    rows_total = len(rebuilt)
                    rows_filled = int(rebuilt["filled"].astype(bool).sum())
                    for horizon in CONFIG.horizons:
                        for spread in CONFIG.spread_values:
                            events = compute_oracle_mfe_rows(rebuilt, horizon=int(horizon), spread=float(spread))
                            key = _rule_key(entry_price_mode, float(zone_width), int(fill_lag), int(horizon), float(spread))
                            summary = summarize_mfe_metrics(events, rows_total=rows_total, rows_filled=rows_filled)
                            summary.update(
                                {
                                    "entry_price_mode": entry_price_mode,
                                    "zone_width_atr": float(zone_width),
                                    "max_fill_lag_bars": int(fill_lag),
                                    "horizon": int(horizon),
                                    "spread": float(spread),
                                    "side_rule": CONFIG.side_rule,
                                    "zero_spread_diagnostic_only": float(spread) == 0.0,
                                }
                            )
                            split_summary[key] = summary
        oracle_summary[split_name] = split_summary

    rows_df = pd.concat(all_rows, ignore_index=True) if all_rows else pd.DataFrame()
    rows_df.to_csv(rows_path, sep=";", index=False)
    selected_train_rule = select_best_train_rule(oracle_summary)
    eval_summary = {}
    if selected_train_rule["key"]:
        eval_key = selected_train_rule["key"]
        eval_summary = dict(oracle_summary.get(CONFIG.primary_eval_split, {}).get(eval_key, {}))
        stress_key = eval_key.replace(f"_spread_{CONFIG.canonical_spread}", f"_spread_{CONFIG.stress_spread}")
        stress = oracle_summary.get(CONFIG.primary_eval_split, {}).get(stress_key, {})
        eval_summary["stress_favorable_to_adverse_ratio"] = stress.get("favorable_to_adverse_ratio")

    gate = research_gate(selected_train_rule.get("summary") or {}, eval_summary, side_contract_audit)
    verdict = gate["verdict_if_pass"] if gate["passes"] else gate["verdict_if_fail"]
    lifecycle = gate["lifecycle_if_pass"] if gate["passes"] else "exploratory_result"
    config = fractal0_entry_config()
    report = {
        "experiment": CONFIG.experiment,
        "verdict": verdict,
        "lifecycle_status": lifecycle,
        "research_level": CONFIG.research_level,
        "origin_bias": CONFIG.origin_bias,
        "research_priority": CONFIG.research_priority,
        "allowed_max_verdict": CONFIG.allowed_max_verdict,
        "current_search_budget": config["current_search_budget"],
        "cumulative_search_budget_lower_bound": config["cumulative_search_budget_lower_bound"],
        "cumulative_search_budget_status": config["cumulative_search_budget_status"],
        "target_contract": {
            "type": "MFE_MAE_after_fill_no_trade_exit",
            "future_derived_fields": [
                "target_entry_up_*",
                "target_entry_dn_*",
                "target_entry_log_ratio_*",
                "oracle_favorable_move_after_cost",
                "oracle_adverse_move",
            ],
            "forbidden_as_input": True,
        },
        "execution_contract": {
            "entry_mechanic": "retest_zone",
            "entry_price_modes": list(CONFIG.entry_price_modes),
            "first_order_eligible_bar_offset": CONFIG.first_order_eligible_bar_offset,
            "exit_contract": "none_in_this_stage",
            "metric_contract": "oracle_favorable_move_after_cost_not_trade_result",
        },
        "forbidden_interpretations": [
            "PnL",
            "PF",
            "прибыльно",
            "готово",
            "можно запускать",
            "live-ready",
            "tradable",
        ],
        "config": config,
        "preflight": {"ohlc": next_open.preflight_ohlc(ohlc), "locked_test": "not_opened"},
        "side_contract_audit": side_contract_audit,
        "oracle_summary": oracle_summary,
        "selected_train_rule": selected_train_rule,
        "selected_eval_summary": eval_summary,
        "research_gate": gate,
        "rows_path": str(rows_path),
        "started_at": started_at,
        "finished_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    missing = validate_report(report)
    if missing:
        report["verdict"] = "diagnostic_only"
        report["lifecycle_status"] = "exploratory_result"
        report["missing_report_fields"] = missing
    output_path.write_text(json.dumps(report, indent=2, default=str))
    return report


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fractal0-entry-mechanics", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    if args.fractal0_entry_mechanics:
        report = run_fractal0_entry_mechanics()
        print({"verdict": report["verdict"], "json": str(REPORT_JSON_PATH), "rows": str(REPORT_ROWS_PATH)})
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
