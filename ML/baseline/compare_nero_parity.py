#!/usr/bin/env python3
"""Compare MT4 and MT5 Nero.csv files for parity.

Usage:
    python compare_nero_parity.py --mt4 PATH --mt5 PATH --output-json PATH
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


def load_csv(path: str, encoding: str) -> pd.DataFrame:
    return pd.read_csv(path, sep=";", encoding=encoding, dtype=str)


def parse_fractal_field(value: str) -> list[str] | None:
    if pd.isna(value) or value.strip() == "":
        return None
    return value.split(":")


def structural_checks(df_mt4: pd.DataFrame, df_mt5: pd.DataFrame) -> dict:
    cols_mt4 = list(df_mt4.columns)
    cols_mt5 = list(df_mt5.columns)
    column_match = cols_mt4 == cols_mt5

    dup_mt4 = int(df_mt4["time"].duplicated().sum())
    dup_mt5 = int(df_mt5["time"].duplicated().sum())

    # Deduplicate: tail-wins
    df4 = df_mt4.drop_duplicates(subset="time", keep="last").copy()
    df5 = df_mt5.drop_duplicates(subset="time", keep="last").copy()

    times_mt4 = set(df4["time"])
    times_mt5 = set(df5["time"])
    intersection_times = sorted(times_mt4 & times_mt5)

    df4_int = df4[df4["time"].isin(times_mt5)].set_index("time")
    df5_int = df5[df5["time"].isin(times_mt4)].set_index("time")
    df4_int = df4_int.loc[intersection_times]
    df5_int = df5_int.loc[intersection_times]

    # Field count distribution (sampled)
    field_counts_mt4 = {}
    field_counts_mt5 = {}
    sample_idx = list(range(0, len(intersection_times), max(1, len(intersection_times) // 200)))
    for i in sample_idx:
        for col in [c for c in df4_int.columns if c.startswith("fractal")]:
            v4 = df4_int[col].iloc[i]
            fields = parse_fractal_field(v4)
            if fields is not None:
                n = len(fields)
                field_counts_mt4[n] = field_counts_mt4.get(n, 0) + 1
            v5 = df5_int[col].iloc[i]
            fields5 = parse_fractal_field(v5)
            if fields5 is not None:
                n5 = len(fields5)
                field_counts_mt5[n5] = field_counts_mt5.get(n5, 0) + 1

    # Shift consistency (MT5 field 23, index 22)
    shift_violations = 0
    shift_checked = 0
    for i in sample_idx:
        for col in [c for c in df5_int.columns if c.startswith("fractal")]:
            v5 = df5_int[col].iloc[i]
            fields5 = parse_fractal_field(v5)
            if fields5 is not None and len(fields5) == 23:
                shift_checked += 1
                try:
                    s = int(fields5[22])
                    if s < 1:
                        shift_violations += 1
                except ValueError:
                    shift_violations += 1

    return {
        "column_match": column_match,
        "columns_mt4": len(cols_mt4),
        "columns_mt5": len(cols_mt5),
        "column_names_match": cols_mt4 == cols_mt5,
        "rows_mt4_total": len(df_mt4),
        "rows_mt5_total": len(df_mt5),
        "rows_mt4_dedup": len(df4),
        "rows_mt5_dedup": len(df5),
        "duplicate_time_count_mt4": dup_mt4,
        "duplicate_time_count_mt5": dup_mt5,
        "intersection_rows": len(intersection_times),
        "min_time_mt4": df_mt4["time"].min(),
        "max_time_mt4": df_mt4["time"].max(),
        "min_time_mt5": df_mt5["time"].min(),
        "max_time_mt5": df_mt5["time"].max(),
        "min_time_intersection": intersection_times[0] if intersection_times else None,
        "max_time_intersection": intersection_times[-1] if intersection_times else None,
        "field_count_distribution_mt4": field_counts_mt4,
        "field_count_distribution_mt5": field_counts_mt5,
        "shift_checked": shift_checked,
        "shift_violations": shift_violations,
    }, df4_int, df5_int, intersection_times


def numeric_checks(df4_int: pd.DataFrame, df5_int: pd.DataFrame, intersection_times: list) -> dict:
    directions_agree = 0
    directions_total = 0
    price_diffs = []
    t_agree = 0
    t_total = 0
    atr_diffs = []

    for i in range(len(intersection_times)):
        # ATR
        a4 = df4_int["ATR"].iloc[i]
        a5 = df5_int["ATR"].iloc[i]
        try:
            atr_diffs.append(abs(float(a5) - float(a4)))
        except (ValueError, TypeError):
            pass

        # fractal0
        v4 = parse_fractal_field(df4_int["fractal0"].iloc[i])
        v5 = parse_fractal_field(df5_int["fractal0"].iloc[i])
        if v4 is None or v5 is None:
            continue

        # T (index 0)
        t_total += 1
        if v4[0] == v5[0]:
            t_agree += 1

        # direction (index 2)
        directions_total += 1
        if v4[2] == v5[2]:
            directions_agree += 1

        # price (index 1)
        try:
            price_diffs.append(abs(float(v5[1]) - float(v4[1])))
        except (ValueError, TypeError):
            pass

    # Extended: fractal1..fractal9 sampled
    extended = {}
    for fi in range(1, 10):
        col = f"fractal{fi}"
        dir_agree = 0
        dir_total = 0
        p_diffs = []
        for i in range(len(intersection_times)):
            v4 = parse_fractal_field(df4_int[col].iloc[i])
            v5 = parse_fractal_field(df5_int[col].iloc[i])
            if v4 is None or v5 is None:
                continue
            dir_total += 1
            if v4[2] == v5[2]:
                dir_agree += 1
            try:
                p_diffs.append(abs(float(v5[1]) - float(v4[1])))
            except (ValueError, TypeError):
                pass
        extended[col] = {
            "direction_agreement_rate": dir_agree / dir_total if dir_total > 0 else None,
            "direction_total": dir_total,
            "price_p95_diff": float(np.percentile(p_diffs, 95)) if p_diffs else None,
            "price_mean_diff": float(np.mean(p_diffs)) if p_diffs else None,
        }

    def diff_summary(diffs: list) -> dict:
        if not diffs:
            return {"mean": None, "p50": None, "p95": None, "max": None, "count": 0}
        arr = np.array(diffs)
        return {
            "mean": float(arr.mean()),
            "p50": float(np.percentile(arr, 50)),
            "p95": float(np.percentile(arr, 95)),
            "max": float(arr.max()),
            "count": len(arr),
        }

    def classify_diffs(diffs: list) -> dict:
        if not diffs:
            return {"small_drift": 0, "broker_history_shift": 0, "systematic": 0}
        arr = np.array(diffs)
        return {
            "small_drift": int((arr < 0.1).sum()),
            "broker_history_shift": int(((arr >= 0.1) & (arr <= 5.0)).sum()),
            "systematic": int((arr > 5.0).sum()),
        }

    price_summary = diff_summary(price_diffs)
    atr_summary = diff_summary(atr_diffs)

    return {
        "fractal0_direction_agreement_rate": directions_agree / directions_total if directions_total > 0 else None,
        "fractal0_direction_total": directions_total,
        "fractal0_price_diff": price_summary,
        "fractal0_price_diff_classification": classify_diffs(price_diffs),
        "fractal0_T_agreement_rate": t_agree / t_total if t_total > 0 else None,
        "fractal0_T_total": t_total,
        "atr_diff": atr_summary,
        "atr_diff_classification": classify_diffs(atr_diffs),
        "extended_fractal1_9": extended,
    }


def determine_verdict(structural: dict, numeric: dict) -> str:
    if not structural["column_match"]:
        return "PARITY_FAIL"

    # Check parse: field counts should be consistent
    fc_mt4 = structural["field_count_distribution_mt4"]
    fc_mt5 = structural["field_count_distribution_mt5"]
    if not fc_mt4 or not fc_mt5:
        return "PARITY_FAIL"

    dir_rate = numeric["fractal0_direction_agreement_rate"]
    price_p95 = numeric["fractal0_price_diff"]["p95"]
    atr_p95 = numeric["atr_diff"]["p95"]

    if dir_rate is None or price_p95 is None or atr_p95 is None:
        return "PARITY_FAIL"

    if dir_rate >= 0.95 and price_p95 <= 5.0 and atr_p95 <= 1.0:
        return "PARITY_PASS"

    return "PARITY_PARTIAL"


def main():
    parser = argparse.ArgumentParser(description="Compare MT4/MT5 Nero.csv parity")
    parser.add_argument("--mt4", required=True, help="Path to MT4 Nero CSV")
    parser.add_argument("--mt5", required=True, help="Path to MT5 Nero CSV")
    parser.add_argument("--output-json", required=True, help="Output JSON path")
    args = parser.parse_args()

    print(f"Loading MT4: {args.mt4}")
    df_mt4 = load_csv(args.mt4, "utf-8")
    print(f"  {len(df_mt4)} rows, {len(df_mt4.columns)} columns")

    print(f"Loading MT5: {args.mt5}")
    df_mt5 = load_csv(args.mt5, "utf-16")
    print(f"  {len(df_mt5)} rows, {len(df_mt5.columns)} columns")

    print("Running structural checks...")
    structural, df4_int, df5_int, intersection_times = structural_checks(df_mt4, df_mt5)
    print(f"  Intersection: {structural['intersection_rows']} rows")

    print("Running numeric checks...")
    numeric = numeric_checks(df4_int, df5_int, intersection_times)

    verdict = determine_verdict(structural, numeric)
    print(f"\nVERDICT: {verdict}")
    print(f"  Direction agreement: {numeric['fractal0_direction_agreement_rate']:.4f}")
    print(f"  Price p95 diff: {numeric['fractal0_price_diff']['p95']:.4f}")
    print(f"  ATR p95 diff: {numeric['atr_diff']['p95']:.4f}")

    result = {
        "verdict": verdict,
        "structural": structural,
        "numeric": numeric,
        "thresholds": {
            "direction_agreement_min": 0.95,
            "price_p95_max": 5.0,
            "atr_p95_max": 1.0,
        },
    }

    out_path = Path(args.output_json)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2, default=str)
    print(f"\nResults written to: {out_path}")


if __name__ == "__main__":
    main()
