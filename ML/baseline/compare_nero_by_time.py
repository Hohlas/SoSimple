#!/usr/bin/env python3
"""Compare MT4 and MT5 Nero.csv by matching fractals on T (timestamp) within each row.

Fractals in a row are not sorted by time — their cell position depends on
ring-buffer eviction history. Correct parity check: match levels by T within
the same bar, then compare their fields.

Usage:
    python compare_nero_by_time.py --mt4 PATH --mt5 PATH --output-json PATH
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

FRACTAL_COLS = [f"fractal{i}" for i in range(100)]

FIELD_NAMES = [
    "T", "P", "Dir", "FrntVal", "BackVal", "Strong", "Brk",
    "Rev", "PwrSum", "Cnt", "Imp",
    "Up_H12", "Dn_H12", "Up_H24", "Dn_H24",
    "Up_H48", "Dn_H48", "Up_H3", "Dn_H3",
    "Up_H6", "Dn_H6", "ATR", "Shift",
]


def load_csv(path: str, encoding: str) -> pd.DataFrame:
    return pd.read_csv(path, sep=";", encoding=encoding, dtype=str)


def parse_row_fractals(row: pd.Series) -> dict[str, list[str]]:
    """Extract fractals from a row, keyed by T (timestamp string)."""
    result = {}
    for col in FRACTAL_COLS:
        val = row.get(col)
        if pd.isna(val) or val.strip() == "":
            continue
        fields = val.split(":")
        t_key = fields[0]
        result[t_key] = fields
    return result


def compare_rows(fractals_mt4: dict, fractals_mt5: dict) -> dict:
    """Compare two sets of fractals (from same bar time) matched by T."""
    keys4 = set(fractals_mt4.keys())
    keys5 = set(fractals_mt5.keys())
    common = keys4 & keys5
    only4 = keys4 - keys5
    only5 = keys5 - keys4

    matched = len(common)
    total4 = len(keys4)
    total5 = len(keys5)

    if matched == 0:
        return {
            "matched": 0, "only_mt4": len(only4), "only_mt5": len(only5),
            "total_mt4": total4, "total_mt5": total5,
        }

    # Compare fields for matched fractals
    # Use min field count (MT4 may have 22, MT5 has 23)
    field_diffs = {}
    dir_agree = 0
    price_diffs = []
    atr_diffs = []

    for t_key in common:
        f4 = fractals_mt4[t_key]
        f5 = fractals_mt5[t_key]
        n_fields = min(len(f4), len(f5))

        # Direction (index 2)
        if n_fields > 2 and f4[2] == f5[2]:
            dir_agree += 1

        # Price (index 1)
        if n_fields > 1:
            try:
                p4 = float(f4[1])
                p5 = float(f5[1])
                price_diffs.append(abs(p4 - p5))
            except ValueError:
                pass

        # ATR (index 21)
        if n_fields > 21:
            try:
                a4 = float(f4[21])
                a5 = float(f5[21])
                atr_diffs.append(abs(a4 - a5))
            except ValueError:
                pass

        # All numeric fields
        for i in range(1, n_fields):
            if i == 22:  # Shift — MT5 only or different semantics
                continue
            try:
                v4 = float(f4[i])
                v5 = float(f5[i])
                diff = abs(v4 - v5)
                if i not in field_diffs:
                    field_diffs[i] = []
                field_diffs[i].append(diff)
            except ValueError:
                pass

    price_arr = np.array(price_diffs) if price_diffs else np.array([0.0])
    atr_arr = np.array(atr_diffs) if atr_diffs else np.array([0.0])

    return {
        "matched": matched,
        "only_mt4": len(only4),
        "only_mt5": len(only5),
        "total_mt4": total4,
        "total_mt5": total5,
        "match_rate": matched / max(total4, total5, 1),
        "direction_agreement": dir_agree / matched,
        "price_mean_diff": float(price_arr.mean()),
        "price_p50_diff": float(np.percentile(price_arr, 50)),
        "price_p95_diff": float(np.percentile(price_arr, 95)),
        "price_max_diff": float(price_arr.max()),
        "atr_mean_diff": float(atr_arr.mean()),
        "atr_p95_diff": float(np.percentile(atr_arr, 95)),
    }


def main():
    parser = argparse.ArgumentParser(description="Compare Nero CSV by T-matching")
    parser.add_argument("--mt4", required=True)
    parser.add_argument("--mt5", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--sample", type=int, default=0,
                        help="Sample N rows (0=all)")
    args = parser.parse_args()

    print(f"Loading MT4: {args.mt4}")
    df4 = load_csv(args.mt4, "utf-8")
    print(f"  {len(df4)} rows, {len(df4.columns)} columns")

    print(f"Loading MT5: {args.mt5}")
    df5 = load_csv(args.mt5, "utf-16")
    print(f"  {len(df5)} rows, {len(df5.columns)} columns")

    # Dedup tail-wins
    df4 = df4.drop_duplicates(subset="time", keep="last")
    df5 = df5.drop_duplicates(subset="time", keep="last")

    # Intersection
    common_times = sorted(set(df4["time"]) & set(df5["time"]))
    print(f"  Intersection: {len(common_times)} rows")

    if args.sample > 0 and len(common_times) > args.sample:
        step = len(common_times) // args.sample
        common_times = common_times[::step][:args.sample]
        print(f"  Sampled: {len(common_times)} rows")

    df4_idx = df4.set_index("time")
    df5_idx = df5.set_index("time")

    # Aggregate stats
    all_match_rates = []
    all_dir_agreements = []
    all_price_diffs = []
    all_atr_diffs = []
    total_matched = 0
    total_only4 = 0
    total_only5 = 0
    total_fractals4 = 0
    total_fractals5 = 0
    rows_with_zero_match = 0

    for i, t in enumerate(common_times):
        row4 = df4_idx.loc[t]
        row5 = df5_idx.loc[t]

        f4 = parse_row_fractals(row4)
        f5 = parse_row_fractals(row5)

        result = compare_rows(f4, f5)

        total_matched += result["matched"]
        total_only4 += result["only_mt4"]
        total_only5 += result["only_mt5"]
        total_fractals4 += result["total_mt4"]
        total_fractals5 += result["total_mt5"]

        if result["matched"] == 0:
            rows_with_zero_match += 1
            continue

        all_match_rates.append(result["match_rate"])
        all_dir_agreements.append(result["direction_agreement"])
        all_price_diffs.append(result["price_p95_diff"])
        all_atr_diffs.append(result["price_mean_diff"])  # track for summary

        if (i + 1) % 1000 == 0:
            print(f"  Processed {i+1}/{len(common_times)} rows...")

    # Summary
    n_rows = len(all_match_rates)
    summary = {
        "method": "T-matching within row",
        "intersection_rows": len(common_times),
        "rows_compared": n_rows,
        "rows_with_zero_match": rows_with_zero_match,
        "total_fractals_matched": total_matched,
        "total_fractals_only_mt4": total_only4,
        "total_fractals_only_mt5": total_only5,
        "total_fractals_mt4": total_fractals4,
        "total_fractals_mt5": total_fractals5,
        "overall_match_rate": total_matched / max(total_fractals4, total_fractals5, 1),
        "mean_row_match_rate": float(np.mean(all_match_rates)) if all_match_rates else 0,
        "mean_direction_agreement": float(np.mean(all_dir_agreements)) if all_dir_agreements else 0,
        "mean_price_p95_diff": float(np.mean(all_price_diffs)) if all_price_diffs else 0,
        "mt4_time_range": [df4["time"].iloc[0], df4["time"].iloc[-1]],
        "mt5_time_range": [df5["time"].iloc[0], df5["time"].iloc[-1]],
    }

    # Verdict
    match_rate = summary["overall_match_rate"]
    dir_agree = summary["mean_direction_agreement"]
    if match_rate >= 0.95 and dir_agree >= 0.95:
        verdict = "PARITY_PASS"
    elif match_rate >= 0.5:
        verdict = "PARITY_PARTIAL"
    else:
        verdict = "PARITY_FAIL"
    summary["verdict"] = verdict

    print(f"\nVERDICT: {verdict}")
    print(f"  Match rate: {match_rate:.4f}")
    print(f"  Direction agreement: {dir_agree:.4f}")
    print(f"  Mean price p95 diff: {summary['mean_price_p95_diff']:.4f}")
    print(f"  Fractals matched: {total_matched}, only MT4: {total_only4}, only MT5: {total_only5}")

    Path(args.output_json).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output_json, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nResults written to: {args.output_json}")


if __name__ == "__main__":
    main()
