import json
import pytest
from ML.baseline.position_ordinal_analysis import (
    parse_trades,
    compute_pf,
    analyze_candidate,
    load_all_candidates,
    aggregate_and_bootstrap,
    run,
)


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


def test_compute_pf_basic():
    result = compute_pf([100.0, -50.0, 200.0, -100.0])
    assert result["pf"] == pytest.approx(2.0)
    assert result["n"] == 4
    assert result["gross_profit"] == pytest.approx(300.0)
    assert result["gross_loss"] == pytest.approx(150.0)


def test_compute_pf_all_losses():
    result = compute_pf([-100.0, -50.0])
    assert result["pf"] == 0.0
    assert result["gross_profit"] == 0.0


def test_compute_pf_all_wins():
    result = compute_pf([100.0, 50.0])
    assert result["pf"] == float("inf")
    assert result["gross_loss"] == 0.0


def test_compute_pf_empty():
    result = compute_pf([])
    assert result["pf"] == 0.0
    assert result["n"] == 0


def test_analyze_candidate_groups_by_ordinal():
    trades = [
        {"ticket": "1", "side": "SELL", "ordinal": 1, "profit": 100.0},
        {"ticket": "2", "side": "SELL", "ordinal": 1, "profit": -50.0},
        {"ticket": "3", "side": "BUY", "ordinal": 2, "profit": 200.0},
        {"ticket": "4", "side": "BUY", "ordinal": 2, "profit": -100.0},
        {"ticket": "5", "side": "SELL", "ordinal": 3, "profit": -80.0},
        {"ticket": "6", "side": "SELL", "ordinal": 5, "profit": 150.0},
        {"ticket": "7", "side": "BUY", "ordinal": 7, "profit": -30.0},
    ]
    result = analyze_candidate(trades)
    assert result["n_trades"] == 7
    assert result["by_ordinal"]["1"]["pf"] == pytest.approx(2.0)
    assert result["by_ordinal"]["1"]["n"] == 2
    assert result["by_ordinal"]["2"]["pf"] == pytest.approx(2.0)
    assert result["by_ordinal"]["2"]["n"] == 2
    assert result["by_ordinal"]["3"]["pf"] == 0.0
    assert result["by_ordinal"]["3"]["n"] == 1
    assert "5+" in result["by_ordinal"]
    assert result["by_ordinal"]["5+"]["n"] == 2
    assert result["by_ordinal"]["5+"]["pf"] == pytest.approx(5.0)
    assert "4" not in result["by_ordinal"]


def test_analyze_candidate_empty():
    result = analyze_candidate([])
    assert result["n_trades"] == 0
    assert result["by_ordinal"] == {}


def test_load_all_candidates(tmp_path):
    for name in ["cand_a", "cand_b"]:
        d = tmp_path / name
        d.mkdir()
        p = d / "events.csv"
        header = "event;time;ticket;side;profit;open_positions"
        p.write_text(header + "\n"
            "OPEN;2021.01.04 11:00;1;SELL;0.0;1\n"
            "CLOSE;2021.01.04 15:00;1;SELL;50.0;0\n")
    result = load_all_candidates(str(tmp_path))
    assert set(result.keys()) == {"cand_a", "cand_b"}
    assert len(result["cand_a"]) == 1
    assert result["cand_a"][0]["ordinal"] == 1


def test_aggregate_and_bootstrap_structure():
    all_trades = {
        "cand_a": [
            {"ticket": "1", "side": "SELL", "ordinal": 1, "profit": 100.0, "year": 2021},
            {"ticket": "2", "side": "SELL", "ordinal": 1, "profit": -50.0, "year": 2022},
            {"ticket": "3", "side": "BUY", "ordinal": 2, "profit": -80.0, "year": 2021},
        ],
        "cand_b": [
            {"ticket": "4", "side": "SELL", "ordinal": 1, "profit": -30.0, "year": 2021},
            {"ticket": "5", "side": "BUY", "ordinal": 2, "profit": 200.0, "year": 2022},
        ],
    }
    result = aggregate_and_bootstrap(all_trades, n_bootstrap=100, seed=42)
    assert "aggregated" in result
    assert "1" in result["aggregated"]
    assert "ci_lower" in result["aggregated"]["1"]
    assert "ci_upper" in result["aggregated"]["1"]
    assert result["n_candidates"] == 2
    assert result["n_total_trades"] == 5
    assert result["bootstrap_config"]["n_bootstrap"] == 100
    assert "by_ordinal_by_year" in result
    assert "2021" in result["by_ordinal_by_year"]["1"]
    assert "2022" in result["by_ordinal_by_year"]["1"]
    assert result["by_ordinal_by_year"]["1"]["2021"]["n"] == 2


def test_run_produces_json(tmp_path):
    cand_dir = tmp_path / "data" / "cand_x"
    cand_dir.mkdir(parents=True)
    header = "event;time;ticket;side;profit;open_positions"
    (cand_dir / "events.csv").write_text(header + "\n"
        "OPEN;2021.01.04 11:00;1;SELL;0.0;1\n"
        "CLOSE;2021.01.04 15:00;1;SELL;100.0;0\n")
    out = tmp_path / "out.json"
    run(str(tmp_path / "data"), str(out))
    assert out.exists()
    data = json.loads(out.read_text())
    assert "aggregated" in data
    assert data["n_candidates"] == 1
