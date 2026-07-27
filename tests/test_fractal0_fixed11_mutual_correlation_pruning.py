import json
from pathlib import Path

import pandas as pd
import pytest

from ML import benchmark_system_correlation as canonical_correlation
from ML.baseline import prune_fractal0_fixed11_mutual_correlation as pruning


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_csv(path: Path, content: str) -> None:
    path.write_text(content.strip() + "\n", encoding="utf-8")


def test_preflight_requires_passed_candidate_audit(tmp_path: Path) -> None:
    audit_json = tmp_path / "audit.json"
    _write_json(audit_json, {"overall_decision": "candidate_audit_blocked"})
    prefix = tmp_path / "fixed11"
    _write_csv(prefix.with_name(prefix.name + "_summary.csv"), "rule_id;n_trades\nr1;100")
    _write_csv(prefix.with_name(prefix.name + "_selection.csv"), "rule_id;original_rank;decision\nr1;1;KEEP_CANDIDATE")
    _write_csv(
        prefix.with_name(prefix.name + "_trades.csv"),
        "rule_id;original_rank;profile_id;model_id;target_id;filter_id;position_id;split_row_id;fill_index;signal_time;fill_time;exit_time;side;pnl_r;hold_bars\n"
        "r1;1;p;m;t;f;pos1;10;11;2025-01-01 00:00:00;2025-01-01 01:00:00;2025-01-01 02:00:00;BUY;1.0;1",
    )

    with pytest.raises(ValueError, match="candidate_audit_passed"):
        pruning.load_inputs(prefix, audit_json)


def test_normalize_fixed11_trades_maps_side_to_direction() -> None:
    trades = pd.DataFrame(
        {
            "rule_id": ["r1", "r1"],
            "original_rank": [1, 1],
            "profile_id": ["time_only", "time_only"],
            "model_id": ["linear", "linear"],
            "target_id": ["target_entry_ev_regression", "target_entry_ev_regression"],
            "filter_id": ["top30", "top30"],
            "position_id": ["pos1", "pos2"],
            "split_row_id": [10, 20],
            "fill_index": [11, 21],
            "signal_time": ["2025-01-01 00:00:00", "2025-01-02 00:00:00"],
            "fill_time": ["2025-01-01 01:00:00", "2025-01-02 01:00:00"],
            "exit_time": ["2025-01-01 02:00:00", "2025-01-02 02:00:00"],
            "side": ["BUY", "SELL"],
            "pnl_r": [1.5, -0.5],
            "hold_bars": [1, 1],
        }
    )

    normalized = pruning.normalize_fixed11_trades(trades)

    assert normalized["direction"].tolist() == [1, -1]
    assert normalized["fill_time"].tolist() == sorted(normalized["fill_time"].tolist())
    assert normalized["pnl_r"].tolist() == [1.5, -0.5]


def test_preflight_rejects_mismatched_summary_selection_trades(tmp_path: Path) -> None:
    audit_json = tmp_path / "audit.json"
    prefix = tmp_path / "fixed11"
    rules = [f"r{index:02d}" for index in range(1, 12)]
    _write_json(audit_json, {"overall_decision": "candidate_audit_passed"})
    _write_csv(
        prefix.with_name(prefix.name + "_summary.csv"),
        "rule_id;original_rank;n_trades\n"
        + "\n".join(f"{rule_id};{index};100" for index, rule_id in enumerate(rules, start=1)),
    )
    _write_csv(
        prefix.with_name(prefix.name + "_selection.csv"),
        "rule_id;original_rank;decision\n"
        + "\n".join(f"{rule_id};{index};KEEP_CANDIDATE" for index, rule_id in enumerate(rules, start=1)),
    )
    trade_rows = []
    for index, rule_id in enumerate(rules[:-1], start=1):
        for trade_index in range(100):
            trade_rows.append(
                f"{rule_id};{index};p;m;t;f;{rule_id}_{trade_index};{trade_index};{trade_index};"
                "2025-01-01 01:00:00;2025-01-01 01:00:00;2025-01-01 02:00:00;BUY;1.0;1"
            )
    _write_csv(
        prefix.with_name(prefix.name + "_trades.csv"),
        "rule_id;original_rank;profile_id;model_id;target_id;filter_id;position_id;split_row_id;fill_index;signal_time;fill_time;exit_time;side;pnl_r;hold_bars\n"
        + "\n".join(trade_rows),
    )

    with pytest.raises(ValueError, match="rule_id sets must match"):
        pruning.load_inputs(prefix, audit_json)
