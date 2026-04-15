import pandas as pd

from ML.benchmark_quantile_relaxed_composition import (
    apply_pred_adv_filter,
    apply_session_filter,
    build_relaxed_candidate_grid,
    choose_relaxed_baseline,
    evaluate_filters,
    label_session_bucket,
    prepare_relaxed_selection_frame,
    resolve_frozen_validation_trades,
    summarize_relaxed_candidates,
    should_run_combined_filter,
    summarize_selected_trades,
)


def test_build_relaxed_candidate_grid_limits_search_space():
    result = build_relaxed_candidate_grid()

    assert result == [
        ("lb_gt_m", 0.15),
        ("lb_gt_m", 0.20),
        ("lb_gt_m", 0.25),
        ("lb_gt_m", 0.30),
        ("lb_gt_m", 0.35),
    ]


def test_summarize_selected_trades_counts_pf_and_year_failures():
    frame = pd.DataFrame(
        {
            "time": ["2024.01.01 00:00", "2024.02.01 00:00", "2025.01.01 00:00"],
            "true_ret_24_dir_atr": [2.0, -1.0, 3.0],
        }
    )

    result = summarize_selected_trades(frame, min_year_trades=1)

    assert result["trades"] == 3
    assert result["pf"] == 5.0
    assert result["negative_year_slices"] == 0


def test_choose_relaxed_baseline_prefers_first_candidate_that_hits_trade_target():
    grid = pd.DataFrame(
        [
            {"candidate": "a", "trades": 40, "pf": 4.0, "negative_year_slices": 1, "mean_pnl_atr": 1.2},
            {"candidate": "b", "trades": 64, "pf": 3.0, "negative_year_slices": 0, "mean_pnl_atr": 1.1},
            {"candidate": "c", "trades": 70, "pf": 2.8, "negative_year_slices": 0, "mean_pnl_atr": 0.9},
        ]
    )

    result = choose_relaxed_baseline(
        grid,
        frozen_validation_trades=32,
        trade_multiplier=2.0,
        min_pf=2.0,
    )

    assert result["candidate"] == "b"


def test_choose_relaxed_baseline_returns_not_viable_when_target_is_missed():
    grid = pd.DataFrame(
        [
            {"candidate": "a", "trades": 40, "pf": 3.0, "negative_year_slices": 0, "mean_pnl_atr": 1.0},
        ]
    )

    result = choose_relaxed_baseline(
        grid,
        frozen_validation_trades=32,
        trade_multiplier=2.0,
        min_pf=2.0,
    )

    assert result["verdict"] == "relaxed_baseline_not_viable"
    assert result["max_trades_in_grid"] == 40


def test_apply_session_filter_excludes_ny_rows():
    frame = pd.DataFrame(
        {
            "session": ["asia", "ny", "overlap"],
            "pred_adv_12_atr": [0.1, 0.2, 0.3],
        }
    )

    result = apply_session_filter(frame)

    assert list(result["session"]) == ["asia", "overlap"]


def test_apply_pred_adv_filter_keeps_values_below_threshold():
    frame = pd.DataFrame(
        {
            "pred_adv_12_atr": [0.01, 0.02, 0.03],
        }
    )

    result = apply_pred_adv_filter(frame, threshold=0.02)

    assert list(result["pred_adv_12_atr"]) == [0.01, 0.02]


def test_should_run_combined_filter_requires_noticeable_standalone_result():
    grid = pd.DataFrame(
        [
            {"filter_name": "session_only", "trades": 70, "pf": 3.5, "negative_year_slices": 0, "pf_delta_vs_baseline": 0.8},
            {"filter_name": "pred_adv12_only", "trades": 30, "pf": 1.1, "negative_year_slices": 2, "pf_delta_vs_baseline": -0.2},
        ]
    )

    assert should_run_combined_filter(grid) is True


def test_label_session_bucket_uses_broker_hour_ranges():
    frame = pd.DataFrame(
        {
            "time": ["2024.01.01 01:00", "2024.01.01 08:00", "2024.01.01 15:00", "2024.01.01 21:00"],
        }
    )

    result = label_session_bucket(frame)

    assert list(result["session"]) == ["asia", "london", "overlap", "ny"]


def test_evaluate_filters_reports_pf_delta_vs_baseline():
    selected_frame = pd.DataFrame(
        {
            "time": ["2024.01.01 01:00", "2024.01.02 21:00", "2025.01.01 15:00"],
            "true_ret_24_dir_atr": [2.0, -1.0, 1.0],
            "pred_adv_12_atr": [0.01, 0.03, 0.02],
        }
    )

    result = evaluate_filters(selected_frame, min_year_trades=1)

    assert list(result["filter_name"]) == ["session_only", "pred_adv12_only"]
    assert list(result["trades"]) == [2, 2]
    assert all(value >= 1.0 for value in result["pf_delta_vs_baseline"])


def test_summarize_relaxed_candidates_builds_one_row_per_candidate():
    frame = pd.DataFrame(
        {
            "time": ["2024.01.01 00:00", "2024.01.02 00:00", "2025.01.01 00:00"],
            "baseline_selected": [True, True, True],
            "lb": [1.0, 2.0, 3.0],
            "width": [0.5, 0.5, 0.5],
            "true_ret_24_dir_atr": [2.0, -1.0, 3.0],
        }
    )

    result = summarize_relaxed_candidates(frame, min_year_trades=1)

    assert len(result) == 5
    assert list(result["candidate"]) == [
        "lb_gt_m_q15",
        "lb_gt_m_q20",
        "lb_gt_m_q25",
        "lb_gt_m_q30",
        "lb_gt_m_q35",
    ]


def test_prepare_relaxed_selection_frame_joins_baseline_and_marks_selected_rows():
    frame = pd.DataFrame(
        {
            "time": ["2024.01.01 00:00", "2024.01.02 00:00"],
            "signal": [1, 1],
            "pred_ret_24_q10": [1.0, 2.0],
            "pred_ret_24_q90": [2.0, 3.0],
            "true_ret_24_dir_atr": [0.5, -0.5],
        }
    )
    baseline_frame = pd.DataFrame(
        {
            "time": ["2024.01.01 00:00", "2024.01.02 00:00"],
            "signal": [1, 1],
            "pred_ret_24_dir_atr": [0.2, -0.2],
        }
    )

    result = prepare_relaxed_selection_frame(
        frame,
        baseline_frame,
        baseline_threshold=0.0,
        correction=0.0,
    )

    assert list(result["baseline_selected"]) == [True, False]
    assert "lb" in result.columns
    assert "width" in result.columns


def test_resolve_frozen_validation_trades_uses_validation_row_not_test_summary():
    grid = pd.DataFrame(
        [
            {"candidate": "lb_gt_m_q35", "trades": 32},
            {"candidate": "lb_gt_m_q30", "trades": 35},
        ]
    )
    selected_rule = {"winner": {"candidate": "lb_gt_m_q35", "trades": 48}}

    result = resolve_frozen_validation_trades(grid, selected_rule)

    assert result == 32
