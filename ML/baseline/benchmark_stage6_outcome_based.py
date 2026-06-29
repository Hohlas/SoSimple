from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "DATA"
REPORTS_DIR = ROOT / "ML" / "reports"
OHLC_FILE = ROOT / "MT" / "MQL4" / "Files" / "Nero.csv"
STAGE6_0_JSON_REPORT_PATH = REPORTS_DIR / "stage6_0_outcome_based_triple_barrier.json"


@dataclass(frozen=True)
class Stage60Config:
    horizon_bars: int = 24
    stop_offset_atr: float = 0.5
    take_profit_atr: float = 2.0
    entry_lag_bars: int = 1
    same_bar_policy: str = "sl_first"
    primary_profile: str = "clock_shift_back"
    disclosure_profiles: tuple[str, ...] = ("clock_shift_back_impulse",)
    seeds: tuple[int, ...] = (42, 77, 123)


STAGE6_0_CONFIG = Stage60Config()


def stage6_target_columns() -> tuple[str, ...]:
    return (
        "stage6_side",
        "stage6_entry_time",
        "stage6_entry_price",
        "stage6_stop_price",
        "stage6_take_price",
        "stage6_close_reason",
        "stage6_invalid_reason",
        "stage6_bars_held",
        "stage6_pnl_r",
        "stage6_pnl_r_spread_020",
        "stage6_pnl_r_spread_040",
        "stage6_risk_atr",
        "stage6_reward_risk",
        "stage6_tp_vs_rest_flag",
        "stage6_definitive_tp_vs_sl_flag",
    )


def stage6_feature_denylist() -> tuple[str, ...]:
    return stage6_target_columns()


from ML.baseline.benchmark_stage5_transformer_breach import extract_stage5_1b_fields


def stage6_first_touch_trade_result(entry_price: float, stop_price: float,
                                    take_price: float, side: str,
                                    future_bars: list[dict],
                                    timeout_close: float | None = None) -> dict:
    if side not in {"buy", "sell"}:
        raise ValueError(f"side must be buy or sell, got {side}")
    risk = abs(entry_price - stop_price)
    reward = abs(take_price - entry_price)
    if risk <= 0.0:
        return {"close_reason": "INVALID", "bars_held": 0, "pnl_r": np.nan}

    for idx, bar in enumerate(future_bars, start=1):
        high = float(bar["high"])
        low = float(bar["low"])
        close = float(bar["close"])
        if side == "buy":
            sl_hit = low <= stop_price
            tp_hit = high >= take_price
        else:
            sl_hit = high >= stop_price
            tp_hit = low <= take_price
        if sl_hit and tp_hit:
            return {"close_reason": "AMBIGUOUS_SL_FIRST", "bars_held": idx, "pnl_r": -1.0}
        if sl_hit:
            return {"close_reason": "SL", "bars_held": idx, "pnl_r": -1.0}
        if tp_hit:
            return {"close_reason": "TP", "bars_held": idx, "pnl_r": float(reward / risk)}

    if not future_bars:
        return {"close_reason": "INVALID", "bars_held": 0, "pnl_r": np.nan}
    close = float(timeout_close if timeout_close is not None else future_bars[-1]["close"])
    if side == "buy":
        pnl_r = (close - entry_price) / risk
    else:
        pnl_r = (entry_price - close) / risk
    return {"close_reason": "TIMEOUT", "bars_held": len(future_bars), "pnl_r": float(pnl_r)}


def _stage6_parse_time(value) -> pd.Timestamp | None:
    ts = pd.to_datetime(value, format="%Y.%m.%d %H:%M", errors="coerce")
    if pd.isna(ts):
        return None
    return pd.Timestamp(ts)


def stage6_load_ohlc_index(path: Path = OHLC_FILE):
    df = pd.read_csv(path, sep=";")
    df["time"] = pd.to_datetime(df["time"], format="%Y.%m.%d %H:%M", errors="coerce")
    df = df.dropna(subset=["time"]).copy()
    df = df.sort_values("time").reset_index(drop=True)
    times = [pd.Timestamp(v) for v in df["time"]]
    ohlc = {
        times[i]: {
            "open": float(df.at[i, "open"]),
            "high": float(df.at[i, "high"]),
            "low": float(df.at[i, "low"]),
            "close": float(df.at[i, "close"]),
        }
        for i in range(len(df))
    }
    time_idx = {ts: i for i, ts in enumerate(times)}
    return ohlc, times, time_idx


def _stage6_invalid_row() -> dict:
    return {
        "stage6_side": "",
        "stage6_entry_time": pd.NaT,
        "stage6_entry_price": np.nan,
        "stage6_stop_price": np.nan,
        "stage6_take_price": np.nan,
        "stage6_close_reason": "INVALID",
        "stage6_invalid_reason": "UNKNOWN",
        "stage6_bars_held": 0,
        "stage6_pnl_r": np.nan,
        "stage6_pnl_r_spread_020": np.nan,
        "stage6_pnl_r_spread_040": np.nan,
        "stage6_risk_atr": np.nan,
        "stage6_reward_risk": np.nan,
        "stage6_tp_vs_rest_flag": np.nan,
        "stage6_definitive_tp_vs_sl_flag": np.nan,
    }


def stage6_build_outcome_labels(df: pd.DataFrame,
                                ohlc_path: Path = OHLC_FILE,
                                config: Stage60Config = STAGE6_0_CONFIG) -> pd.DataFrame:
    out = df.copy()
    ohlc, times, time_idx = stage6_load_ohlc_index(ohlc_path)
    rows = []
    for _, row in out.iterrows():
        labels = _stage6_invalid_row()
        row_time = _stage6_parse_time(row.get("time"))
        if row_time is None or row_time not in time_idx:
            labels["stage6_invalid_reason"] = "TIME_NOT_FOUND"
            rows.append(labels)
            continue
        source_idx = time_idx[row_time]
        entry_idx = source_idx + config.entry_lag_bars
        end_idx = entry_idx + config.horizon_bars
        if entry_idx >= len(times) or end_idx > len(times):
            labels["stage6_invalid_reason"] = "OHLC_HORIZON_MISSING"
            rows.append(labels)
            continue
        fields = extract_stage5_1b_fields(str(row.get("fractal0", "")))
        direction = fields.get("direction", 0.0)
        fractal_price = float(fields.get("price", 0.0) or 0.0)
        atr = float(row.get("ATR", 0.0) or 0.0)
        if atr <= 0.0 or fractal_price <= 0.0:
            labels["stage6_invalid_reason"] = "BAD_FRACTAL_OR_ATR"
            rows.append(labels)
            continue
        entry_time = times[entry_idx]
        entry_price = float(ohlc[entry_time]["open"])
        if direction == -1:
            side = "buy"
            stop_price = fractal_price - config.stop_offset_atr * atr
            take_price = entry_price + config.take_profit_atr * atr
        elif direction == 1:
            side = "sell"
            stop_price = fractal_price + config.stop_offset_atr * atr
            take_price = entry_price - config.take_profit_atr * atr
        else:
            labels["stage6_invalid_reason"] = "BAD_DIRECTION"
            rows.append(labels)
            continue
        future = [ohlc[t] for t in times[entry_idx:end_idx]]
        result = stage6_first_touch_trade_result(
            entry_price=entry_price,
            stop_price=stop_price,
            take_price=take_price,
            side=side,
            future_bars=future,
        )
        reason = result["close_reason"]
        risk = abs(entry_price - stop_price)
        reward = abs(take_price - entry_price)
        labels.update({
            "stage6_side": side,
            "stage6_entry_time": entry_time,
            "stage6_entry_price": entry_price,
            "stage6_stop_price": stop_price,
            "stage6_take_price": take_price,
            "stage6_close_reason": reason,
            "stage6_invalid_reason": "",
            "stage6_bars_held": int(result["bars_held"]),
            "stage6_pnl_r": float(result["pnl_r"]) if np.isfinite(result["pnl_r"]) else np.nan,
            "stage6_pnl_r_spread_020": float(result["pnl_r"] - 0.20 / risk) if risk > 0 else np.nan,
            "stage6_pnl_r_spread_040": float(result["pnl_r"] - 0.40 / risk) if risk > 0 else np.nan,
            "stage6_risk_atr": float(risk / atr) if atr > 0 else np.nan,
            "stage6_reward_risk": float(reward / risk) if risk > 0 else np.nan,
        })
        if reason == "TP":
            labels["stage6_tp_vs_rest_flag"] = 1
            labels["stage6_definitive_tp_vs_sl_flag"] = 1
        elif reason in {"SL", "AMBIGUOUS_SL_FIRST"}:
            labels["stage6_tp_vs_rest_flag"] = 0
            labels["stage6_definitive_tp_vs_sl_flag"] = 0
        elif reason == "TIMEOUT":
            labels["stage6_tp_vs_rest_flag"] = 0
            labels["stage6_definitive_tp_vs_sl_flag"] = np.nan
        rows.append(labels)
    labels_df = pd.DataFrame(rows, index=out.index)
    for col in stage6_target_columns():
        out[col] = labels_df[col]
    return out
