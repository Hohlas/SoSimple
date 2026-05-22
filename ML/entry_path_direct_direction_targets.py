# =============================================================================
# Файл: entry_path_direct_direction_targets.py
# Назначение: BUY/SELL target families для direct SELL/SKIP/BUY entry-path модели.
# Обновлён: 2026-05-15
# Входные данные:
#   - DATA/Nero_*_labeled.csv и DATA/XAUUSD_H1_OHLC.csv
# Выходные данные:
#   - target classes -1/0/1 и target frequency summaries
# Использование:
#   from ML.entry_path_direct_direction_targets import build_buy_sell_fav_adv
# Примечания:
#   - source["signal"] не используется как target source.
# =============================================================================

from __future__ import annotations

from datetime import timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from processing.label_signals import load_ohlc_index


def build_buy_sell_fav_adv(
    source: pd.DataFrame,
    horizons: tuple[int, ...] = (3, 6, 12, 24, 48),
) -> pd.DataFrame:
    """Строит BUY/SELL moves в ATR units из raw up/dn price distances."""
    out = pd.DataFrame(index=source.index)
    atr = pd.to_numeric(source.get("ATR", pd.Series(0.0, index=source.index)), errors="coerce").fillna(0.0).astype(float)
    safe_atr = atr.where(atr > 0.0, np.nan)
    for horizon in horizons:
        up_raw = pd.to_numeric(source[f"up_{horizon}"], errors="coerce").fillna(0.0).astype(float)
        dn_raw = pd.to_numeric(source[f"dn_{horizon}"], errors="coerce").fillna(0.0).astype(float)
        up = (up_raw / safe_atr).replace([np.inf, -np.inf], np.nan).fillna(0.0)
        dn = (dn_raw / safe_atr).replace([np.inf, -np.inf], np.nan).fillna(0.0)
        out[f"buy_fav_{horizon}_atr"] = up.astype(float)
        out[f"buy_adv_{horizon}_atr"] = dn.astype(float)
        out[f"sell_fav_{horizon}_atr"] = dn.astype(float)
        out[f"sell_adv_{horizon}_atr"] = up.astype(float)
    return out


def target_pair_to_class(buy_good: pd.Series, sell_good: pd.Series) -> pd.Series:
    """Преобразует BUY/SELL positive masks в класс -1/0/1; ambiguous -> SKIP."""
    buy = pd.Series(buy_good).fillna(False).astype(bool)
    sell = pd.Series(sell_good).fillna(False).astype(bool)
    out = pd.Series(0, index=buy.index, dtype="int64")
    out.loc[buy & ~sell] = 1
    out.loc[sell & ~buy] = -1
    return out


def build_target_a_classes(moves: pd.DataFrame, stop_n: float, take_y: float) -> pd.Series:
    """Target A: быстрый отскок за 6 баров, отдельно для BUY и SELL."""
    buy_good = (moves["buy_adv_6_atr"] < float(stop_n)) & (moves["buy_fav_6_atr"] >= float(take_y))
    sell_good = (moves["sell_adv_6_atr"] < float(stop_n)) & (moves["sell_fav_6_atr"] >= float(take_y))
    return target_pair_to_class(buy_good, sell_good)


def build_target_c_classes(moves: pd.DataFrame, take_x: float, adverse_y: float) -> pd.Series:
    """Target C: 24-bar favorable move при ограниченном 12-bar adverse move."""
    buy_good = (moves["buy_fav_24_atr"] >= float(take_x)) & (moves["buy_adv_12_atr"] <= float(adverse_y))
    sell_good = (moves["sell_fav_24_atr"] >= float(take_x)) & (moves["sell_adv_12_atr"] <= float(adverse_y))
    return target_pair_to_class(buy_good, sell_good)


def build_target_d_classes(
    source: pd.DataFrame,
    ohlc_path: str | Path,
    trail_n: float,
    profit_z: float,
    horizon: int,
) -> pd.Series:
    """Target D: trailing-прибыль отдельно для BUY и SELL; ambiguous -> SKIP."""
    buy_good, sell_good = build_target_d_masks(source, ohlc_path, trail_n=trail_n, profit_z=profit_z, horizon=horizon)
    return target_pair_to_class(buy_good, sell_good)


def build_target_d_masks(
    source: pd.DataFrame,
    ohlc_path: str | Path,
    trail_n: float,
    profit_z: float,
    horizon: int,
) -> tuple[pd.Series, pd.Series]:
    """Возвращает BUY/SELL positive masks для Target D."""
    buy_good = []
    sell_good = []
    ohlc, times, time_idx = load_ohlc_index(str(ohlc_path))
    parsed_time = pd.to_datetime(source["time"], format="%Y.%m.%d %H:%M", errors="coerce")
    atr_values = pd.to_numeric(source["ATR"], errors="coerce").fillna(0.0)

    for pos, row_time in enumerate(parsed_time):
        atr = float(atr_values.iloc[pos])
        if pd.isna(row_time) or atr <= 0:
            buy_good.append(False)
            sell_good.append(False)
            continue
        base_idx = time_idx.get(row_time.to_pydatetime().replace(tzinfo=timezone.utc))
        if base_idx is None:
            buy_good.append(False)
            sell_good.append(False)
            continue
        entry_idx = base_idx + 1
        end_idx = entry_idx + int(horizon)
        if entry_idx >= len(times) or end_idx > len(times):
            buy_good.append(False)
            sell_good.append(False)
            continue
        entry_price = float(ohlc[times[entry_idx]][0])
        bars = [
            {
                "high": float(ohlc[times[idx]][1]),
                "low": float(ohlc[times[idx]][2]),
                "close": float(ohlc[times[idx]][3]),
            }
            for idx in range(entry_idx, end_idx)
        ]
        buy_pnl = _simulate_trailing_profit_atr(bars, direction=1, entry_price=entry_price, atr=atr, trail_n=trail_n)
        sell_pnl = _simulate_trailing_profit_atr(bars, direction=-1, entry_price=entry_price, atr=atr, trail_n=trail_n)
        buy_good.append(buy_pnl >= float(profit_z))
        sell_good.append(sell_pnl >= float(profit_z))

    return pd.Series(buy_good, index=source.index), pd.Series(sell_good, index=source.index)


def summarize_target_frequencies(
    splits: dict[str, pd.DataFrame],
    *,
    ohlc_path: str | Path,
    include_ac_targets: bool = False,
) -> pd.DataFrame:
    """Считает частоты target families для train/validation gate.

    A/C включаются только для raw up/dn sources. Нормализованные split CSV не
    являются корректным ATR-source для этих target families.
    """
    rows: list[dict[str, Any]] = []
    specs = [
        {"target_family": "D", "params": {"trail_n": 2.0, "profit_z": 1.0, "horizon": 24}},
    ]
    if include_ac_targets:
        specs = [
            {"target_family": "A", "params": {"stop_n": 0.2, "take_y": 0.3}},
            {"target_family": "C", "params": {"take_x": 0.5, "adverse_y": 0.3}},
            *specs,
        ]
    for spec in specs:
        split_rows = []
        for split, source in splits.items():
            buy_good, sell_good = _target_masks_for_spec(source, spec, ohlc_path=ohlc_path)
            classes = target_pair_to_class(buy_good, sell_good)
            split_rows.append(_frequency_row(split, source, spec, buy_good, sell_good, classes))

        train_row = next(row for row in split_rows if row["split"] == "train")
        validation_row = next(row for row in split_rows if row["split"] == "validation")
        family_gate = (
            train_row["positive_count"] >= 500
            and validation_row["positive_count"] >= 100
            and validation_row["buy_count"] >= 50
            and validation_row["sell_count"] >= 50
            and validation_row["major_year_min_positive_count"] >= 20
            and not validation_row["one_sided_or_sparse_year"]
            and validation_row["ambiguous_rate"] <= 0.20
        )
        for row in split_rows:
            row["gate_pass"] = bool(family_gate)
            rows.append(row)
    return pd.DataFrame(rows)


def _target_masks_for_spec(
    source: pd.DataFrame,
    spec: dict[str, Any],
    *,
    ohlc_path: str | Path,
) -> tuple[pd.Series, pd.Series]:
    family = spec["target_family"]
    params = spec["params"]
    if family == "A":
        moves = build_buy_sell_fav_adv(source, horizons=(6,))
        buy_good = (moves["buy_adv_6_atr"] < params["stop_n"]) & (moves["buy_fav_6_atr"] >= params["take_y"])
        sell_good = (moves["sell_adv_6_atr"] < params["stop_n"]) & (moves["sell_fav_6_atr"] >= params["take_y"])
        return buy_good, sell_good
    if family == "C":
        moves = build_buy_sell_fav_adv(source, horizons=(12, 24))
        buy_good = (moves["buy_fav_24_atr"] >= params["take_x"]) & (moves["buy_adv_12_atr"] <= params["adverse_y"])
        sell_good = (moves["sell_fav_24_atr"] >= params["take_x"]) & (moves["sell_adv_12_atr"] <= params["adverse_y"])
        return buy_good, sell_good
    if family == "D":
        return build_target_d_masks(
            source,
            ohlc_path,
            trail_n=params["trail_n"],
            profit_z=params["profit_z"],
            horizon=params["horizon"],
        )
    raise ValueError(f"unsupported target family: {family}")


def _frequency_row(
    split: str,
    source: pd.DataFrame,
    spec: dict[str, Any],
    buy_good: pd.Series,
    sell_good: pd.Series,
    classes: pd.Series,
) -> dict[str, Any]:
    row_count = int(len(source))
    ambiguous = buy_good & sell_good
    positive = classes.isin([-1, 1])
    years = pd.to_datetime(source["time"], format="%Y.%m.%d %H:%M", errors="coerce").dt.year
    major_year_min_positive, one_sided_or_sparse = _major_year_stats(years, classes)
    old_signal = pd.to_numeric(source.get("signal", pd.Series(0, index=source.index)), errors="coerce").fillna(0).astype(int)
    overlap = positive & (old_signal != 0)
    return {
        "target_family": spec["target_family"],
        "params": json_dumps_compact(spec["params"]),
        "split": split,
        "row_count": row_count,
        "buy_count": int((classes == 1).sum()),
        "sell_count": int((classes == -1).sum()),
        "skip_count": int((classes == 0).sum()),
        "ambiguous_count": int(ambiguous.sum()),
        "ambiguous_rate": float(ambiguous.mean()) if row_count else 0.0,
        "positive_count": int(positive.sum()),
        "positive_rate": float(positive.mean()) if row_count else 0.0,
        "major_year_min_positive_count": int(major_year_min_positive),
        "one_sided_or_sparse_year": bool(one_sided_or_sparse),
        "overlap_with_old_signal_count": int(overlap.sum()),
        "overlap_with_old_signal_rate": float(overlap.sum() / max(int(positive.sum()), 1)),
    }


def _major_year_stats(years: pd.Series, classes: pd.Series) -> tuple[int, bool]:
    work = pd.DataFrame({"year": years, "class": classes}).dropna(subset=["year"])
    min_positive = 0
    sparse = False
    major_seen = False
    for _, group in work.groupby("year"):
        if len(group) < 500:
            continue
        major_seen = True
        buy_count = int((group["class"] == 1).sum())
        sell_count = int((group["class"] == -1).sum())
        positive_count = buy_count + sell_count
        min_positive = positive_count if min_positive == 0 else min(min_positive, positive_count)
        if positive_count < 20 or buy_count < 5 or sell_count < 5:
            sparse = True
    return (min_positive if major_seen else 0), sparse or not major_seen


def json_dumps_compact(value: Any) -> str:
    import json

    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _simulate_trailing_profit_atr(
    bars: list[dict[str, float]],
    *,
    direction: int,
    entry_price: float,
    atr: float,
    trail_n: float,
) -> float:
    if direction == 1:
        best_high = float(entry_price)
        stop = best_high - float(trail_n) * atr
        for bar in bars:
            old_stop = stop
            if float(bar["low"]) <= old_stop:
                return (old_stop - entry_price) / atr
            if float(bar["high"]) > best_high:
                best_high = float(bar["high"])
                stop = best_high - float(trail_n) * atr
        return (float(bars[-1]["close"]) - entry_price) / atr if bars else 0.0

    best_low = float(entry_price)
    stop = best_low + float(trail_n) * atr
    for bar in bars:
        old_stop = stop
        if float(bar["high"]) >= old_stop:
            return (entry_price - old_stop) / atr
        if float(bar["low"]) < best_low:
            best_low = float(bar["low"])
            stop = best_low + float(trail_n) * atr
    return (entry_price - float(bars[-1]["close"])) / atr if bars else 0.0
