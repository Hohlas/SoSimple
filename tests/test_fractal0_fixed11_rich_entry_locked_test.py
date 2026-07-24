from pathlib import Path

from ML.baseline.run_fractal0_fixed11_rich_entry_locked_test import load_execution_contract, load_fixed_rules


def test_load_fixed_rules_reads_exact_11_leaderboard_rows() -> None:
    rules = load_fixed_rules(Path("ML/reports/leaderboard_closure_audit_rules.csv"))

    assert len(rules) == 11
    assert rules[0]["rule_id"] == "rank01_time_only_linear_target_entry_ev_regression_top30"
    assert rules[-1]["rule_id"] == "rank11_movement_plus_time_linear_target_entry_good_0_5r_top50"


def test_load_execution_contract_uses_stop_grid_m5_winner() -> None:
    contract = load_execution_contract(Path("ML/reports/fractal0_stop_grid_m5.json"))

    assert contract["stop_policy"]["stop_policy_id"] == "S2_fractal0_buffer_0_5_entry_floor_2"
    assert contract["entry_rule"]["entry_id"] == "E3_open_pullback_1_0atr"
    assert contract["mask_rule"]["mask_id"] == "M0_no_mask"
    assert contract["exit_rule"]["exit_id"] == "X2_ml_opposite_any_p0_50"
    assert contract["spread"] == 0.2
