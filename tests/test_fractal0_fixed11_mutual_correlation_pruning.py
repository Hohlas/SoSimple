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


def _trade_frame(rule_id: str, rank: int, times: list[str], pnl: list[float], sides: list[str]) -> pd.DataFrame:
    return pruning.normalize_fixed11_trades(
        pd.DataFrame(
            {
                "rule_id": [rule_id] * len(times),
                "original_rank": [rank] * len(times),
                "profile_id": ["time_only"] * len(times),
                "model_id": ["linear"] * len(times),
                "target_id": ["target"] * len(times),
                "filter_id": ["top30"] * len(times),
                "position_id": [f"{rule_id}_pos_{index}" for index in range(len(times))],
                "split_row_id": list(range(len(times))),
                "fill_index": list(range(len(times))),
                "signal_time": times,
                "fill_time": times,
                "exit_time": times,
                "side": sides,
                "pnl_r": pnl,
                "hold_bars": [1] * len(times),
            }
        )
    )


def test_pair_metrics_classify_strong_duplicate() -> None:
    left = _trade_frame("r1", 1, ["2025-01-01 01:00:00", "2025-01-02 01:00:00"], [1.0, -0.5], ["BUY", "SELL"])
    right = _trade_frame("r2", 2, ["2025-01-01 01:00:00", "2025-01-02 01:00:00"], [1.0, -0.5], ["BUY", "SELL"])

    metrics = pruning.compute_pair_metrics(left, right)

    assert metrics["fill_overlap_ratio"] == 1.0
    assert metrics["signal_overlap_ratio"] == 1.0
    assert metrics["same_direction_ratio"] == 1.0
    assert metrics["fill_bucket_pnl_corr"] == 1.0
    assert metrics["redundancy_verdict"] == "strong_duplicate"


def test_pair_metrics_classify_unclear_or_complementary() -> None:
    left = _trade_frame("r1", 1, ["2025-01-01 01:00:00", "2025-01-03 01:00:00"], [1.0, 1.0], ["BUY", "BUY"])
    right = _trade_frame("r2", 2, ["2025-01-02 01:00:00", "2025-01-04 01:00:00"], [1.0, 1.0], ["SELL", "SELL"])

    metrics = pruning.compute_pair_metrics(left, right)

    assert metrics["fill_overlap_ratio"] == 0.0
    assert metrics["signal_overlap_ratio"] == 0.0
    assert metrics["same_direction_ratio"] == 0.0
    assert metrics["exit_drawdown_overlap_ratio"] == 0.0
    assert metrics["redundancy_verdict"] == "unclear_or_complementary"


def test_build_pairwise_matrix_emits_all_pairs() -> None:
    trades = pd.concat(
        [
            _trade_frame("r1", 1, ["2025-01-01 01:00:00"], [1.0], ["BUY"]),
            _trade_frame("r2", 2, ["2025-01-01 01:00:00"], [1.0], ["BUY"]),
            _trade_frame("r3", 3, ["2025-01-02 01:00:00"], [1.0], ["SELL"]),
        ],
        ignore_index=True,
    )

    pairwise = pruning.build_pairwise_matrix(trades)

    assert len(pairwise) == 3
    assert set(pairwise["left_rule_id"]) | set(pairwise["right_rule_id"]) == {"r1", "r2", "r3"}


def test_single_trade_bucket_matches_existing_correlation_module() -> None:
    left = _trade_frame("r1", 1, ["2025-01-01 01:00:00", "2025-01-02 01:00:00"], [1.0, -0.5], ["BUY", "SELL"])
    right = _trade_frame("r2", 2, ["2025-01-01 01:00:00", "2025-01-02 01:00:00"], [1.0, -0.5], ["BUY", "SELL"])
    left_canonical = left.rename(columns={"rule_id": "system_name", "fill_time": "entry_time", "pnl_r": "pnl_atr"}).assign(
        instrument="XAUUSD", provider="MetaQuotes", holding_bars=left["hold_bars"]
    )
    right_canonical = right.rename(columns={"rule_id": "system_name", "fill_time": "entry_time", "pnl_r": "pnl_atr"}).assign(
        instrument="XAUUSD", provider="MetaQuotes", holding_bars=right["hold_bars"]
    )

    metrics = pruning.compute_pair_metrics(left, right)
    canonical = canonical_correlation.compute_pair_metrics(left_canonical, right_canonical)

    assert metrics["fill_overlap_ratio"] == canonical["trade_overlap_ratio"]
    assert metrics["fill_jaccard"] == canonical["entry_time_jaccard"]
    assert metrics["same_direction_ratio"] == canonical["same_direction_ratio"]
    assert metrics["exit_daily_pnl_corr"] == canonical["daily_pnl_corr"]


def test_repeated_fill_time_is_aggregated_without_losing_trade_count() -> None:
    left = pruning.normalize_fixed11_trades(
        pd.DataFrame(
            {
                "rule_id": ["r1", "r1"],
                "original_rank": [1, 1],
                "profile_id": ["time_only", "time_only"],
                "model_id": ["linear", "linear"],
                "target_id": ["target", "target"],
                "filter_id": ["top30", "top30"],
                "position_id": ["r1_a", "r1_b"],
                "split_row_id": [1, 2],
                "fill_index": [10, 10],
                "signal_time": ["2025-01-01 00:00:00", "2025-01-01 00:30:00"],
                "fill_time": ["2025-01-01 01:00:00", "2025-01-01 01:00:00"],
                "exit_time": ["2025-01-01 02:00:00", "2025-01-01 03:00:00"],
                "side": ["BUY", "BUY"],
                "pnl_r": [1.0, 2.0],
                "hold_bars": [1, 2],
            }
        )
    )
    right = pruning.normalize_fixed11_trades(
        pd.DataFrame(
            {
                "rule_id": ["r2"],
                "original_rank": [2],
                "profile_id": ["time_only"],
                "model_id": ["linear"],
                "target_id": ["target"],
                "filter_id": ["top30"],
                "position_id": ["r2_a"],
                "split_row_id": [3],
                "fill_index": [10],
                "signal_time": ["2025-01-01 00:00:00"],
                "fill_time": ["2025-01-01 01:00:00"],
                "exit_time": ["2025-01-01 02:00:00"],
                "side": ["BUY"],
                "pnl_r": [3.0],
                "hold_bars": [1],
            }
        )
    )

    metrics = pruning.compute_pair_metrics(left, right)

    assert metrics["shared_fill_bucket_count"] == 1
    assert metrics["left_trade_count_at_shared_fills"] == 2
    assert metrics["right_trade_count_at_shared_fills"] == 1
    assert metrics["fill_bucket_pnl_corr"] == 1.0


def test_retained_subset_uses_original_rank_not_locked_test_pf() -> None:
    summary = pd.DataFrame(
        {
            "rule_id": ["r1", "r2"],
            "original_rank": [1, 2],
            "pf": [1.2, 9.9],
            "bs_p05": [1.1, 9.0],
            "n_trades": [100, 100],
        }
    )
    selection = pd.DataFrame({"rule_id": ["r1", "r2"], "decision": ["KEEP_CANDIDATE", "KEEP_CANDIDATE"]})
    trades = pd.concat(
        [
            _trade_frame("r1", 1, ["2025-01-01 01:00:00", "2025-01-02 01:00:00"], [1.0, -0.5], ["BUY", "SELL"]),
            _trade_frame("r2", 2, ["2025-01-01 01:00:00", "2025-01-02 01:00:00"], [9.0, -4.5], ["BUY", "SELL"]),
        ],
        ignore_index=True,
    )
    inputs = pruning.Fixed11Inputs(
        audit={"overall_decision": "candidate_audit_passed"},
        summary=summary,
        selection=selection,
        trades=trades,
        paths={},
        sha256={},
    )
    pairwise = pruning.build_pairwise_matrix(trades)

    manifest = pruning.build_retained_subset(inputs, pairwise)

    retained = [item["rule_id"] for item in manifest["rules"] if item["decision"] == "RETAIN"]
    dropped = [item["rule_id"] for item in manifest["rules"] if item["decision"] == "DROP_STRONG_DUPLICATE"]
    assert retained == ["r1"]
    assert dropped == ["r2"]
    assert manifest["representative_policy"] == "lowest_original_rank_then_rule_id"


def test_retained_subset_can_keep_all_rules_when_no_strong_duplicates() -> None:
    trades = pd.concat(
        [
            _trade_frame("r1", 1, ["2025-01-01 01:00:00"], [1.0], ["BUY"]),
            _trade_frame("r2", 2, ["2025-01-02 01:00:00"], [1.0], ["SELL"]),
        ],
        ignore_index=True,
    )
    inputs = pruning.Fixed11Inputs(
        audit={"overall_decision": "candidate_audit_passed"},
        summary=pd.DataFrame({"rule_id": ["r1", "r2"], "original_rank": [1, 2], "n_trades": [100, 100]}),
        selection=pd.DataFrame({"rule_id": ["r1", "r2"], "decision": ["KEEP_CANDIDATE", "KEEP_CANDIDATE"]}),
        trades=trades,
        paths={},
        sha256={},
    )

    manifest = pruning.build_retained_subset(inputs, pruning.build_pairwise_matrix(trades))

    assert manifest["overall_decision"] == "pruning_passed"
    assert manifest["retained_count"] == 2
    assert manifest["removed_count"] == 0


def test_transitive_duplicate_does_not_drop_without_direct_representative_edge() -> None:
    trades = pd.concat(
        [
            _trade_frame("r1", 1, ["2025-01-01 01:00:00", "2025-01-02 01:00:00"], [1.0, -1.0], ["BUY", "SELL"]),
            _trade_frame("r2", 2, ["2025-01-01 01:00:00", "2025-01-02 01:00:00"], [1.0, -1.0], ["BUY", "SELL"]),
            _trade_frame("r3", 3, ["2025-01-02 01:00:00", "2025-01-03 01:00:00"], [-1.0, 1.0], ["SELL", "BUY"]),
        ],
        ignore_index=True,
    )
    inputs = pruning.Fixed11Inputs(
        audit={"overall_decision": "candidate_audit_passed"},
        summary=pd.DataFrame({"rule_id": ["r1", "r2", "r3"], "original_rank": [1, 2, 3], "n_trades": [100, 100, 100]}),
        selection=pd.DataFrame(
            {"rule_id": ["r1", "r2", "r3"], "decision": ["KEEP_CANDIDATE", "KEEP_CANDIDATE", "KEEP_CANDIDATE"]}
        ),
        trades=trades,
        paths={},
        sha256={},
    )
    pairwise = pd.DataFrame(
        [
            {"left_rule_id": "r1", "right_rule_id": "r2", "redundancy_verdict": "strong_duplicate"},
            {"left_rule_id": "r1", "right_rule_id": "r3", "redundancy_verdict": "partial_overlap"},
            {"left_rule_id": "r2", "right_rule_id": "r3", "redundancy_verdict": "strong_duplicate"},
        ]
    )

    manifest = pruning.build_retained_subset(inputs, pairwise)

    decisions = {item["rule_id"]: item["decision"] for item in manifest["rules"]}
    assert decisions["r1"] == "RETAIN"
    assert decisions["r2"] == "DROP_STRONG_DUPLICATE"
    assert decisions["r3"] == "RETAIN"
    assert manifest["indirect_duplicate_edges_not_used_for_drop"]
