#!/usr/bin/env python3
"""Read-only checks for the 2026-07-29 Python/MT4 fill chronology report."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import struct
from collections import Counter
from datetime import datetime
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = ROOT / "ML/reports/fractal0_fixed11_retained_mt4_parity"
RULE_ID = "rank05_time_only_linear_target_entry_avoid_sl_top30"
HST_DIR = Path(
    "/home/hohla/.mt4/drive_c/Program Files (x86)/MetaTrader 4/history/MetaQuotes-Demo"
)


FILES = {
    "mt4_event_log": ROOT / "MT/tester/files/ML_Trade_Events_SoSimple_1709200448.csv",
    "python_trades": ROOT / "ML/reports/fractal0_fixed11_rich_entry_locked_test_trades.csv",
    "python_metadata": ROOT / "ML/reports/fractal0_fixed11_rich_entry_locked_test.json",
    "python_h1": ROOT / "DATA/XAUUSD_H1_OHLC.csv",
    "mt4_exported_h1": ROOT / "MT/MQL4/Files/XAUUSD_H1_OHLC_new.csv",
    "m5_csv": ROOT / "MT/MQL4/Files/XAUUSD_M5_OHLC.csv",
    "hst_h1": HST_DIR / "XAUUSD60.hst",
    "hst_m5": HST_DIR / "XAUUSD5.hst",
    "hst_m1": HST_DIR / "XAUUSD1.hst",
}

for base in [ROOT / "MT/MQL4/Files", ROOT / "MT/tester/files"]:
    prefix = "mql4" if "MQL4" in base.parts else "tester"
    for kind in ["signals", "exits"]:
        for slot in range(1, 6):
            name = f"ml_{kind}_fixed11_rule{slot:02d}.csv"
            FILES[f"{prefix}_{name}"] = base / name


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def file_info(path: Path) -> dict[str, object]:
    if not path.exists():
        return {
            "path": str(path),
            "exists": False,
        }
    st = path.stat()
    return {
        "path": str(path),
        "exists": True,
        "sha256": sha256(path),
        "size_bytes": st.st_size,
        "mtime_utc": datetime.utcfromtimestamp(st.st_mtime).isoformat(timespec="seconds"),
    }


def read_hst(path: Path) -> pd.DataFrame:
    data = path.read_bytes()
    payload = len(data) - 148
    if payload <= 0:
        raise ValueError(f"bad HST size: {path}")
    if payload % 60 == 0:
        fmt = "<qddddqiq"
        size = 60
        rows = [
            {
                "time": pd.to_datetime(t, unit="s"),
                "open": o,
                "high": h,
                "low": l,
                "close": c,
                "volume": tv,
            }
            for t, o, h, l, c, tv, _spread, _real_volume in struct.iter_unpack(
                fmt, data[148:]
            )
        ]
    elif payload % 44 == 0:
        fmt = "<iddddd"
        size = 44
        rows = [
            {
                "time": pd.to_datetime(t, unit="s"),
                "open": o,
                "high": h,
                "low": l,
                "close": c,
                "volume": v,
            }
            for t, o, l, h, c, v in struct.iter_unpack(fmt, data[148:])
        ]
    else:
        raise ValueError(f"unknown HST record size for {path}: payload={payload}")
    df = pd.DataFrame(rows).drop_duplicates("time", keep="last").sort_values("time")
    df.attrs["record_size"] = size
    return df


def read_ohlc(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, sep=";")
    df["time"] = pd.to_datetime(df["time"])
    for col in ["open", "high", "low", "close"]:
        df[col] = pd.to_numeric(df[col])
    return df


def event_counts(path: Path) -> dict[str, object]:
    counts: Counter[str] = Counter()
    reasons: Counter[str] = Counter()
    profit = 0.0
    with path.open(newline="") as f:
        for row in csv.DictReader(f, delimiter=";"):
            counts[row["event"]] += 1
            if row["event"] == "CLOSE":
                reasons[row["reason"]] += 1
                profit += float(row["profit"] or 0.0)
            elif row["event"] == "OPEN_FAILED":
                reasons[row["reason"]] += 1
    return {
        "events": dict(counts),
        "reasons": dict(reasons),
        "closed_profit_sum": round(profit, 2),
    }


def profit_factor(values: pd.Series) -> float:
    gains = values[values > 0].sum()
    losses = -values[values < 0].sum()
    if losses == 0:
        return math.inf
    return gains / losses


def stale_pnl(event_path: Path, trades_path: Path) -> dict[str, object]:
    ev = pd.read_csv(event_path, sep=";")
    ev = ev[ev["reason"].isin(["StalePendingAfterMLClose", "StaleFillAfterMLClose"])].copy()
    ev["direction"] = ev["direction"].str.upper()
    ev["signal_time"] = pd.to_datetime(ev["signal_time"]).dt.strftime("%Y-%m-%d %H:%M:%S")
    trades = pd.read_csv(trades_path, sep=";")
    trades = trades[trades["rule_id"] == RULE_ID].copy()
    trades["direction"] = trades["side"].str.upper()
    trades["signal_time"] = pd.to_datetime(trades["signal_time"]).dt.strftime("%Y-%m-%d %H:%M:%S")
    result = {}
    for reason, group in ev.groupby("reason"):
        keys = group[["signal_time", "direction"]].drop_duplicates()
        merged = trades.merge(keys, on=["signal_time", "direction"], how="inner")
        result[reason] = {
            "count": int(len(group)),
            "unique_signal_direction_keys": int(len(keys)),
            "python_matched_rows": int(len(merged)),
            "python_pnl_r_sum": round(float(merged["pnl_r"].sum()), 6),
            "python_close_reasons": {
                str(k): int(v) for k, v in merged["close_reason"].value_counts().items()
            },
        }
    return result


def hold_bars_summary(trades_path: Path) -> dict[str, object]:
    trades = pd.read_csv(trades_path, sep=";")
    sub = trades[trades["rule_id"] == RULE_ID].copy()
    buckets = [
        ("0", sub[sub["hold_bars"] == 0]),
        ("1", sub[sub["hold_bars"] == 1]),
        ("2", sub[sub["hold_bars"] == 2]),
        ("3..5", sub[(sub["hold_bars"] >= 3) & (sub["hold_bars"] <= 5)]),
        (">5", sub[sub["hold_bars"] > 5]),
    ]
    out = {}
    for name, group in buckets:
        out[name] = {
            "n": int(len(group)),
            "sum_pnl_r": round(float(group["pnl_r"].sum()), 4),
            "mean_r": round(float(group["pnl_r"].mean()), 4),
            "pf": round(float(profit_factor(group["pnl_r"])), 4),
        }
    h0 = sub[sub["hold_bars"] == 0]
    out["hold0_close_reasons"] = {
        str(k): {"n": int(len(g)), "sum_pnl_r": round(float(g["pnl_r"].sum()), 4)}
        for k, g in h0.groupby("close_reason")
    }
    return out


def h1_vs_hst_summary(csv_path: Path, hst_path: Path) -> dict[str, object]:
    left = read_ohlc(csv_path)
    right = read_hst(hst_path)
    merged = left.merge(right, on="time", suffixes=("_csv", "_hst"))
    diffs = pd.Series(False, index=merged.index)
    for col in ["open", "high", "low", "close"]:
        diffs |= (merged[f"{col}_csv"] - merged[f"{col}_hst"]).abs() > 1e-6
    merged["diff"] = diffs
    merged["year"] = merged["time"].dt.year
    yearly = {
        str(int(year)): int(group["diff"].sum())
        for year, group in merged.groupby("year")
        if int(group["diff"].sum()) > 0
    }
    return {
        "csv_rows": int(len(left)),
        "hst_rows": int(len(right)),
        "matched_rows": int(len(merged)),
        "hst_record_size": int(right.attrs["record_size"]),
        "large_differences_by_year": yearly,
        "best_offset_hours_checked": 0,
    }


def first_touch(m5: pd.DataFrame, row: pd.Series) -> tuple[pd.Timestamp | None, dict[str, object] | None]:
    fill_time = pd.Timestamp(row["fill_time"])
    end = fill_time + pd.Timedelta(hours=1)
    window = m5[(m5["time"] >= fill_time) & (m5["time"] < end)].copy()
    limit_price = float(row["entry_effective_price"])
    if row["side"] == "BUY":
        hit = window[window["low"] <= limit_price]
    else:
        hit = window[window["high"] >= limit_price]
    if hit.empty:
        return None, None
    first = hit.iloc[0]
    return first["time"], {
        "time": first["time"].strftime("%Y-%m-%d %H:%M:%S"),
        "open": float(first["open"]),
        "high": float(first["high"]),
        "low": float(first["low"]),
        "close": float(first["close"]),
    }


def chronology_examples(trades_path: Path, m5_path: Path) -> list[dict[str, object]]:
    trades = pd.read_csv(trades_path, sep=";")
    sub = trades[
        (trades["rule_id"] == RULE_ID)
        & (trades["hold_bars"] == 0)
        & (trades["close_reason"] == "ML_CLOSE")
    ].copy()
    m5 = read_ohlc(m5_path)
    examples = []
    for signal_time in ["2022-12-05 23:00:00", "2022-12-14 22:00:00"]:
        row = sub[sub["signal_time"] == signal_time].iloc[0]
        touch_time, touch_ohlc = first_touch(m5, row)
        examples.append(
            {
                "signal_time": signal_time,
                "side": row["side"],
                "limit": float(row["entry_effective_price"]),
                "python_fill_time": row["fill_time"],
                "python_exit_time": row["exit_time"],
                "first_m5_touch_time": None if touch_time is None else touch_time.strftime("%Y-%m-%d %H:%M:%S"),
                "first_m5_bar_ohlc": touch_ohlc,
                "close_reason": row["close_reason"],
                "pnl_r": float(row["pnl_r"]),
                "source_m5_sha256": sha256(m5_path),
            }
        )
    return examples


def hold0_m5_aggregate(trades_path: Path, m5_path: Path) -> dict[str, int]:
    trades = pd.read_csv(trades_path, sep=";")
    sub = trades[
        (trades["rule_id"] == RULE_ID)
        & (trades["hold_bars"] == 0)
        & (trades["close_reason"] == "ML_CLOSE")
    ].copy()
    m5 = read_ohlc(m5_path)
    counts: Counter[str] = Counter()
    for _, row in sub.iterrows():
        touch_time, _touch_ohlc = first_touch(m5, row)
        if touch_time is None:
            counts["m5_no_hit"] += 1
        elif touch_time == pd.Timestamp(row["fill_time"]):
            counts["first_m5_touch_at_h1_open"] += 1
        else:
            counts["first_m5_touch_after_h1_open"] += 1
    counts["total"] = int(len(sub))
    return dict(counts)


def write_examples_csv(examples: list[dict[str, object]]) -> None:
    path = OUT_DIR / "chronology_examples.csv"
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "signal_time",
                "side",
                "limit",
                "python_fill_time",
                "python_exit_time",
                "first_m5_touch_time",
                "first_m5_bar_ohlc",
                "close_reason",
                "pnl_r",
                "source_m5_sha256",
            ],
            delimiter=";",
        )
        writer.writeheader()
        for row in examples:
            row = dict(row)
            row["first_m5_bar_ohlc"] = json.dumps(row["first_m5_bar_ohlc"], sort_keys=True)
            writer.writerow(row)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    examples = chronology_examples(FILES["python_trades"], FILES["m5_csv"])
    write_examples_csv(examples)
    manifest = {
        "stage": "fixed11_python_mt4_fill_chronology",
        "status": "DIAGNOSTIC_ONLY",
        "rule_id": RULE_ID,
        "generated_by": str(Path(__file__).relative_to(ROOT)),
        "artifact_hashes": {name: file_info(path) for name, path in FILES.items()},
        "event_counts": event_counts(FILES["mt4_event_log"]),
        "stale_pnl": stale_pnl(FILES["mt4_event_log"], FILES["python_trades"]),
        "h1_vs_hst": h1_vs_hst_summary(FILES["python_h1"], FILES["hst_h1"]),
        "hold_bars_summary": hold_bars_summary(FILES["python_trades"]),
        "hold0_m5_aggregate": hold0_m5_aggregate(FILES["python_trades"], FILES["m5_csv"]),
        "chronology_examples_csv": str(
            (OUT_DIR / "chronology_examples.csv").relative_to(ROOT)
        ),
        "hst_parser": {
            "header_bytes": 148,
            "record_size_auto_detected": "60_or_44_bytes",
            "timezone_offset_hours_selected": 0,
        },
    }
    out = OUT_DIR / "fill_chronology_manifest.json"
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(out.relative_to(ROOT))
    print((OUT_DIR / "chronology_examples.csv").relative_to(ROOT))
    print(json.dumps(manifest["event_counts"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
