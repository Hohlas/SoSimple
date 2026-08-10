import csv


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
