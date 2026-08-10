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
