import csv
import json
import os
import random


def parse_trades(events_path):
    opens = {}
    closes = []
    with open(events_path, newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            event = row["event"]
            if event == "OPEN":
                opens[row["ticket"]] = (
                    int(row["open_positions"]),
                    row["side"],
                    int(row["time"][:4]),
                )
            elif event == "CLOSE":
                closes.append(
                    (row["ticket"], float(row["profit"]), row["side"])
                )
    trades = []
    for ticket, profit, side in closes:
        if ticket in opens:
            ordinal, _, year = opens[ticket]
            trades.append({
                "ticket": ticket,
                "side": side,
                "ordinal": ordinal,
                "profit": profit,
                "year": year,
            })
    return trades


def compute_pf(profits):
    gp = sum(p for p in profits if p > 0)
    gl = abs(sum(p for p in profits if p < 0))
    n = len(profits)
    if gl == 0:
        pf = float("inf") if gp > 0 else 0.0
    elif gp == 0:
        pf = 0.0
    else:
        pf = gp / gl
    return {"pf": pf, "n": n, "gross_profit": gp, "gross_loss": gl}


def analyze_candidate(trades):
    groups = {}
    for t in trades:
        ordinal = t["ordinal"]
        key = "5+" if ordinal >= 5 else str(ordinal)
        groups.setdefault(key, []).append(t["profit"])
    by_ordinal = {}
    for key, profits in groups.items():
        pf_data = compute_pf(profits)
        by_ordinal[key] = pf_data
    return {"by_ordinal": by_ordinal, "n_trades": len(trades)}


def load_all_candidates(max64_dir):
    result = {}
    for name in sorted(os.listdir(max64_dir)):
        events_path = os.path.join(max64_dir, name, "events.csv")
        if os.path.isfile(events_path):
            result[name] = parse_trades(events_path)
    return result


def aggregate_and_bootstrap(all_trades, n_bootstrap=2000, seed=42):
    ordinal_keys = ["1", "2", "3", "4", "5+"]
    candidate_names = sorted(all_trades.keys())
    n_candidates = len(candidate_names)

    per_candidate = {}
    for name, trades in all_trades.items():
        per_candidate[name] = analyze_candidate(trades)

    aggregated = {}
    for key in ordinal_keys:
        profits = []
        for name in candidate_names:
            for t in all_trades[name]:
                t_key = "5+" if t["ordinal"] >= 5 else str(t["ordinal"])
                if t_key == key:
                    profits.append(t["profit"])
        if not profits:
            continue
        pf_data = compute_pf(profits)

        ci_values = []
        rng = random.Random(seed)
        for _ in range(n_bootstrap):
            sampled_names = [
                candidate_names[rng.randint(0, n_candidates - 1)]
                for _ in range(n_candidates)
            ]
            boot_profits = []
            for name in sampled_names:
                for t in all_trades[name]:
                    t_key = "5+" if t["ordinal"] >= 5 else str(t["ordinal"])
                    if t_key == key:
                        boot_profits.append(t["profit"])
            if boot_profits:
                bp = compute_pf(boot_profits)
                if bp["pf"] != float("inf"):
                    ci_values.append(bp["pf"])

        ci_values.sort()
        if len(ci_values) >= 20:
            ci_lower = ci_values[int(0.025 * len(ci_values))]
            ci_upper = ci_values[int(0.975 * len(ci_values))]
        else:
            ci_lower = None
            ci_upper = None

        aggregated[key] = {
            **pf_data,
            "ci_lower": ci_lower,
            "ci_upper": ci_upper,
        }

    n_total = sum(len(t) for t in all_trades.values())

    by_ordinal_by_year = {}
    for key in ordinal_keys:
        year_groups = {}
        for name in candidate_names:
            for t in all_trades[name]:
                t_key = "5+" if t["ordinal"] >= 5 else str(t["ordinal"])
                if t_key == key:
                    year_groups.setdefault(t["year"], []).append(t["profit"])
        if year_groups:
            by_ordinal_by_year[key] = {
                str(y): compute_pf(profits)
                for y, profits in sorted(year_groups.items())
            }

    return {
        "status": "DIAGNOSTIC_ONLY",
        "n_candidates": n_candidates,
        "n_total_trades": n_total,
        "aggregated": aggregated,
        "by_ordinal_by_year": by_ordinal_by_year,
        "per_candidate": per_candidate,
        "bootstrap_config": {
            "n_bootstrap": n_bootstrap,
            "seed": seed,
        },
    }


def run(input_dir, output_path):
    all_trades = load_all_candidates(input_dir)
    result = aggregate_and_bootstrap(all_trades)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="Position-ordinal PnL diagnostic for MT5 max=64 pilot"
    )
    parser.add_argument(
        "--input-dir",
        default="ML/reports/mt5_execution_loop/multipos_pilot/max64",
    )
    parser.add_argument(
        "--output",
        default="ML/reports/mt5_execution_loop/diagnostics/position_ordinal_pnl.json",
    )
    args = parser.parse_args()
    run(args.input_dir, args.output)
    print(f"Wrote {args.output}")
