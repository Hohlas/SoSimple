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


from ML.baseline.benchmark_stage5_transformer_breach import build_stage5_4_features, extract_stage5_1b_fields


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


def _stage6_pf_from_pnl(values) -> float | None:
    arr = np.asarray(values, dtype=np.float64)
    arr = arr[np.isfinite(arr)]
    profit = float(arr[arr > 0.0].sum())
    loss = float(-arr[arr < 0.0].sum())
    if loss == 0.0:
        return None if profit == 0.0 else float("inf")
    return profit / loss


def _stage6_add_year(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    ts = pd.to_datetime(out["time"], format="%Y.%m.%d %H:%M", errors="coerce")
    out["_year"] = ts.dt.year
    return out


def _stage6_distribution_summary(values) -> dict:
    arr = np.asarray(values, dtype=np.float64)
    arr = arr[np.isfinite(arr)]
    if len(arr) == 0:
        return {"n": 0, "min": None, "p01": None, "median": None, "p99": None, "max": None}
    return {
        "n": int(len(arr)),
        "min": float(np.min(arr)),
        "p01": float(np.percentile(arr, 1)),
        "median": float(np.median(arr)),
        "p99": float(np.percentile(arr, 99)),
        "max": float(np.max(arr)),
    }


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


def stage6_split_integrity_audit(full: pd.DataFrame, labeled: pd.DataFrame) -> dict:
    warnings = []
    duplicate_times = int(full["time"].duplicated().sum()) if "time" in full else 0
    if duplicate_times:
        warnings.append("DUPLICATE_TIME_VALUES")
    year_counts = labeled["_year"].value_counts(dropna=False).sort_index().to_dict()
    invalid_reasons = labeled.get("stage6_invalid_reason", pd.Series(["unknown"] * len(labeled))).value_counts().to_dict()
    return {
        "duplicate_times": duplicate_times,
        "year_counts": {str(k): int(v) for k, v in year_counts.items()},
        "invalid_reasons": {str(k): int(v) for k, v in invalid_reasons.items()},
        "warnings": warnings,
    }


def stage6_load_labeled_splits(ohlc_path: Path = OHLC_FILE) -> dict[str, pd.DataFrame]:
    train = pd.read_csv(DATA_DIR / "Nero_XAUUSD_train_labeled.csv", sep=";")
    val = pd.read_csv(DATA_DIR / "Nero_XAUUSD_validation_labeled.csv", sep=";")
    test = pd.read_csv(DATA_DIR / "Nero_XAUUSD_test_labeled.csv", sep=";")
    full = pd.concat([train, val, test], ignore_index=True)
    labeled = _stage6_add_year(stage6_build_outcome_labels(full, ohlc_path=ohlc_path))
    splits = {
        "train_core": labeled.loc[labeled["_year"] <= 2020].copy(),
        "val_stop": labeled.loc[labeled["_year"].between(2021, 2022)].copy(),
        "diagnostic_holdout": labeled.loc[labeled["_year"].between(2023, 2025)].copy(),
        "low_n_disclosure": labeled.loc[labeled["_year"] == 2026].copy(),
    }
    splits["_integrity"] = stage6_split_integrity_audit(full, labeled)
    return splits


def _stage6_split_preflight(df: pd.DataFrame) -> dict:
    valid = df["stage6_close_reason"] != "INVALID"
    sub = df.loc[valid]
    n = int(len(sub))
    counts = sub["stage6_close_reason"].value_counts().to_dict()
    tp = int(counts.get("TP", 0))
    sl = int(counts.get("SL", 0) + counts.get("AMBIGUOUS_SL_FIRST", 0))
    timeout = int(counts.get("TIMEOUT", 0))
    yearly = {}
    warnings = []
    for year, group in sub.groupby("_year"):
        yearly[str(int(year))] = int(len(group))
        if len(group) < 200:
            warnings.append(f"YEARLY_VALID_LT_200:{int(year)}")
    tp_rate = float(tp / n) if n else 0.0
    timeout_rate = float(timeout / n) if n else 0.0
    risk = sub["stage6_risk_atr"].to_numpy(dtype=np.float64) if "stage6_risk_atr" in sub else np.asarray([])
    reward_risk = sub["stage6_reward_risk"].to_numpy(dtype=np.float64) if "stage6_reward_risk" in sub else np.asarray([])
    pnl = sub["stage6_pnl_r"].to_numpy(dtype=np.float64) if "stage6_pnl_r" in sub else np.asarray([])
    timeout_pnl = sub.loc[sub["stage6_close_reason"] == "TIMEOUT", "stage6_pnl_r"].to_numpy(dtype=np.float64)
    by_side = {}
    if "stage6_side" in sub:
        for side, group in sub.groupby("stage6_side"):
            by_side[str(side)] = {
                "n": int(len(group)),
                "tp_rate": float((group["stage6_close_reason"] == "TP").mean()) if len(group) else 0.0,
                "pf": _stage6_pf_from_pnl(group["stage6_pnl_r"]),
            }
    if tp_rate < 0.05 or tp_rate > 0.70:
        warnings.append("TP_RATE_OUTSIDE_0_05_0_70")
    if timeout_rate > 0.70:
        warnings.append("TIMEOUT_GT_0_70")
    if n < 1000:
        warnings.append("VALID_ROWS_LT_1000")
    if len(risk) and np.nanpercentile(risk, 1) <= 0:
        warnings.append("RISK_ATR_P01_LE_0")
    if len(risk) and np.nanpercentile(risk, 99) > 10:
        warnings.append("RISK_ATR_P99_GT_10")
    if len(reward_risk) and np.nanpercentile(reward_risk, 99) > 20:
        warnings.append("REWARD_RISK_P99_GT_20")
    if len(pnl) and np.nanmax(np.abs(pnl)) > 20:
        warnings.append("PNL_R_ABS_MAX_GT_20")
    return {
        "n": n,
        "invalid": int((~valid).sum()),
        "counts": {str(k): int(v) for k, v in counts.items()},
        "tp_rate": tp_rate,
        "sl_or_ambiguous_rate": float(sl / n) if n else 0.0,
        "timeout_rate": timeout_rate,
        "risk_atr": _stage6_distribution_summary(risk),
        "reward_risk": _stage6_distribution_summary(reward_risk),
        "pnl_r": _stage6_distribution_summary(pnl),
        "timeout_pnl_r": {
            **_stage6_distribution_summary(timeout_pnl),
            "profitable_timeout_rate": float((timeout_pnl > 0).mean()) if len(timeout_pnl) else None,
            "total_timeout_pnl_r": float(np.nansum(timeout_pnl)) if len(timeout_pnl) else 0.0,
        },
        "by_side": by_side,
        "yearly_valid_rows": yearly,
        "warnings": warnings,
    }


def stage6_outcome_preflight(split: dict[str, pd.DataFrame]) -> dict:
    out = {
        name: _stage6_split_preflight(df)
        for name, df in split.items()
        if isinstance(df, pd.DataFrame)
    }
    if "_integrity" in split:
        out["_integrity"] = split["_integrity"]
    return out


def stage6_oracle_preflight(split: dict[str, pd.DataFrame]) -> dict:
    out = {}
    for name, df in split.items():
        if not isinstance(df, pd.DataFrame):
            continue
        valid = df["stage6_close_reason"] != "INVALID"
        sub = df.loc[valid].copy()
        tp_only = sub["stage6_close_reason"] == "TP"
        out[name] = {
            "all_trade_pf": _stage6_pf_from_pnl(sub["stage6_pnl_r"]),
            "all_trade_trades": int(len(sub)),
            "tp_only_oracle_pf": _stage6_pf_from_pnl(sub.loc[tp_only, "stage6_pnl_r"]),
            "tp_only_oracle_trades": int(tp_only.sum()),
            "trades_per_year": float(len(sub) / max(sub["_year"].nunique(), 1)) if len(sub) else 0.0,
        }
    return out


def stage6_assert_no_target_feature_names(feature_names: list[str] | tuple[str, ...] | None) -> None:
    if not feature_names:
        return
    bad = [name for name in feature_names if str(name).startswith("stage6_")]
    assert not bad, f"stage6 target leaked into feature names: {bad[:5]}"


def stage6_build_features(df: pd.DataFrame, profile: str) -> np.ndarray:
    clean = df.drop(columns=[c for c in stage6_feature_denylist() if c in df.columns])
    X = build_stage5_4_features(clean, profile)
    feature_names = getattr(X, "feature_names", None)
    stage6_assert_no_target_feature_names(feature_names)
    return X


def stage6_build_feature_split(split: dict[str, pd.DataFrame], profile: str) -> dict[str, np.ndarray]:
    return {
        name: stage6_build_features(df, profile)
        for name, df in split.items()
        if isinstance(df, pd.DataFrame)
    }
