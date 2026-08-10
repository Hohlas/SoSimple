import pytest
from ML.baseline.position_ordinal_analysis import parse_trades


def _write_events(path, lines):
    header = "event;time;ticket;side;profit;open_positions"
    path.write_text(header + "\n" + "\n".join(lines))


def test_parse_trades_matches_open_close_by_ticket(tmp_path):
    p = tmp_path / "events.csv"
    _write_events(p, [
        "OPEN;2021.01.04 11:00;2;SELL;0.0;2",
        "CLOSE;2021.01.04 15:00;2;SELL;-56.9;1",
        "OPEN;2021.01.04 16:00;5;SELL;0.0;2",
        "CLOSE;2021.01.05 03:00;5;SELL;-44.3;1",
    ])
    trades = parse_trades(str(p))
    assert len(trades) == 2
    assert trades[0]["ticket"] == "2"
    assert trades[0]["ordinal"] == 2
    assert trades[0]["profit"] == -56.9
    assert trades[0]["side"] == "SELL"
    assert trades[0]["year"] == 2021
    assert trades[1]["ticket"] == "5"
    assert trades[1]["ordinal"] == 2
    assert trades[1]["profit"] == -44.3
    assert trades[1]["year"] == 2021


def test_parse_trades_skips_close_without_open(tmp_path):
    p = tmp_path / "events.csv"
    _write_events(p, [
        "CLOSE;2021.01.04 15:00;99;BUY;100.0;0",
    ])
    trades = parse_trades(str(p))
    assert trades == []


def test_parse_trades_ignores_non_open_close_events(tmp_path):
    p = tmp_path / "events.csv"
    _write_events(p, [
        "INIT;2021.01.04 01:00;;;-1;0",
        "ORDER_PLACED;2021.01.04 10:00;2;SELL;0.0;1",
        "ML_EVAL;2021.01.04 11:00;2;SELL;0.0;1",
        "OPEN;2021.01.04 11:00;2;SELL;0.0;1",
        "CLOSE;2021.01.04 15:00;2;SELL;-56.9;0",
    ])
    trades = parse_trades(str(p))
    assert len(trades) == 1
    assert trades[0]["ordinal"] == 1
    assert trades[0]["profit"] == -56.9
    assert trades[0]["year"] == 2021


def test_parse_trades_empty_file(tmp_path):
    p = tmp_path / "events.csv"
    _write_events(p, [])
    trades = parse_trades(str(p))
    assert trades == []


def test_parse_trades_extracts_year_from_open_time(tmp_path):
    p = tmp_path / "events.csv"
    _write_events(p, [
        "OPEN;2022.06.15 10:00;1;BUY;0.0;1",
        "CLOSE;2022.06.15 14:00;1;BUY;50.0;0",
    ])
    trades = parse_trades(str(p))
    assert len(trades) == 1
    assert trades[0]["year"] == 2022
