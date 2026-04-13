import pandas as pd

from ML.benchmark_fav_3_vs_12_standalone import (
    EPS,
    add_fav_ratio,
    annotate_grid_with_yearly_failures,
    compute_metrics,
    compute_yearly_breakdown,
    count_negative_year_slices,
    evaluate_threshold_grid,
    select_stable_threshold,
)


def test_add_fav_ratio_uses_safe_denominator():
    frame = pd.DataFrame(
        {
            "pred_fav_3": [1.0, 2.0],
            "pred_fav_12": [2.0, 0.0],
        }
    )

    result = add_fav_ratio(frame)

    assert result.loc[0, "fav_3_vs_12"] == 0.5
    assert result.loc[1, "fav_3_vs_12"] == 2.0 / EPS


def test_compute_metrics_counts_trades_and_pf():
    frame = pd.DataFrame(
        {
            "pnl_atr": [2.0, -1.0, 3.0],
        }
    )

    result = compute_metrics(frame)

    assert result["n_trades"] == 3
    assert result["gross_profit"] == 5.0
    assert result["gross_loss"] == 1.0
    assert result["pf"] == 5.0


def test_compute_metrics_returns_numeric_pf_for_zero_pnl():
    frame = pd.DataFrame(
        {
            "pnl_atr": [0.0, 0.0],
        }
    )

    result = compute_metrics(frame)

    assert result["n_trades"] == 2
    assert result["gross_profit"] == 0.0
    assert result["gross_loss"] == 0.0
    assert result["pf"] == 0.0


def test_evaluate_threshold_grid_selects_ratio_lte_threshold():
    frame = pd.DataFrame(
        {
            "fav_3_vs_12": [0.2, 0.5, 0.8],
            "pnl_atr": [1.0, -1.0, 2.0],
            "time": ["2022-01-01", "2022-01-02", "2022-01-03"],
        }
    )

    result = evaluate_threshold_grid(frame, thresholds=[0.3, 0.6])

    assert list(result["threshold"]) == [0.3, 0.6]
    assert list(result["n_trades"]) == [1, 2]
    assert list(result["pf"]) == [float("inf"), 1.0]


def test_compute_yearly_breakdown_reports_negative_years():
    frame = pd.DataFrame(
        {
            "time": ["2022-01-01", "2022-01-02", "2023-01-01", "2023-01-02"],
            "pnl_atr": [2.0, 1.0, -2.0, 1.0],
        }
    )

    result = compute_yearly_breakdown(frame)

    assert list(result["year"]) == [2022, 2023]
    assert result.loc[result["year"] == 2023, "pf"].iloc[0] == 0.5


def test_select_stable_threshold_prefers_passing_window_over_peak():
    grid = pd.DataFrame(
        {
            "threshold": [0.1, 0.2, 0.3, 0.4, 0.5],
            "n_trades": [28, 35, 36, 37, 38],
            "pf": [1.9, 2.1, 2.2, 10.0, 1.0],
            "negative_year_slices": [0, 0, 0, 1, 0],
        }
    )

    selected = select_stable_threshold(
        grid,
        min_trades=30,
        min_pf=2.0,
        max_negative_year_slices=0,
        window_size=3,
        min_passing_in_window=2,
    )

    assert selected["verdict"] == "selected"
    assert selected["threshold"] == 0.3
    assert selected["pf"] != 10.0


def test_select_stable_threshold_sorts_unsorted_thresholds_before_selection():
    grid = pd.DataFrame(
        {
            "threshold": [0.4, 0.1, 0.5, 0.3, 0.2],
            "n_trades": [37, 28, 38, 36, 35],
            "pf": [10.0, 1.9, 1.0, 2.2, 2.1],
            "negative_year_slices": [1, 0, 0, 0, 0],
        }
    )

    selected = select_stable_threshold(
        grid,
        min_trades=30,
        min_pf=2.0,
        max_negative_year_slices=0,
        window_size=3,
        min_passing_in_window=2,
    )

    assert selected["verdict"] == "selected"
    assert selected["threshold"] == 0.3


def test_select_stable_threshold_rejects_duplicate_thresholds():
    grid = pd.DataFrame(
        {
            "threshold": [0.2, 0.2, 0.3],
            "n_trades": [35, 36, 37],
            "pf": [2.1, 2.2, 2.3],
            "negative_year_slices": [0, 0, 0],
        }
    )

    try:
        select_stable_threshold(
            grid,
            min_trades=30,
            min_pf=2.0,
            max_negative_year_slices=0,
            window_size=3,
            min_passing_in_window=2,
        )
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for duplicate thresholds")


def test_select_stable_threshold_rejects_even_window_size():
    grid = pd.DataFrame(
        {
            "threshold": [0.1, 0.2, 0.3, 0.4],
            "n_trades": [35, 36, 37, 38],
            "pf": [2.1, 2.2, 2.3, 2.4],
            "negative_year_slices": [0, 0, 0, 0],
        }
    )

    selected = select_stable_threshold(
        grid,
        min_trades=30,
        min_pf=2.0,
        max_negative_year_slices=0,
        window_size=2,
        min_passing_in_window=2,
    )

    assert selected["verdict"] == "no_stable_threshold"
    assert selected["threshold"] is None


def test_select_stable_threshold_penalizes_failed_neighbors_in_window_score():
    grid = pd.DataFrame(
        {
            "threshold": [0.1, 0.2, 0.3, 0.4, 0.5],
            "n_trades": [35, 36, 37, 38, 39],
            "pf": [2.0, 100.0, 0.1, 2.2, 2.1],
            "negative_year_slices": [0, 0, 0, 0, 0],
        }
    )

    selected = select_stable_threshold(
        grid,
        min_trades=30,
        min_pf=2.0,
        max_negative_year_slices=0,
        window_size=3,
        min_passing_in_window=2,
    )

    assert selected["verdict"] == "selected"
    assert selected["threshold"] == 0.4


def test_select_stable_threshold_treats_missing_yearly_failures_as_fail_closed():
    grid = pd.DataFrame(
        {
            "threshold": [0.1, 0.2, 0.3],
            "n_trades": [35, 36, 37],
            "pf": [2.1, 2.2, 2.3],
            "negative_year_slices": [0, None, 0],
        }
    )

    selected = select_stable_threshold(
        grid,
        min_trades=30,
        min_pf=2.0,
        max_negative_year_slices=0,
        window_size=3,
        min_passing_in_window=3,
    )

    assert selected["verdict"] == "no_stable_threshold"


def test_sparse_bad_year_is_ignored_below_min_year_trades():
    frame = pd.DataFrame(
        {
            "time": [
                "2022-01-01",
                "2022-01-02",
                "2022-01-03",
                "2023-01-01",
                "2023-01-02",
            ],
            "pnl_atr": [1.0, 1.0, 1.0, -3.0, -1.0],
            "fav_3_vs_12": [0.2, 0.2, 0.2, 0.2, 0.2],
        }
    )

    grid = pd.DataFrame({"threshold": [0.3]})
    annotated = annotate_grid_with_yearly_failures(frame, grid, min_year_trades=3)

    assert count_negative_year_slices(frame, min_year_trades=3) == 0
    assert annotated.loc[0, "negative_year_slices"] == 0
    assert count_negative_year_slices(frame, min_year_trades=2) == 1


def test_negative_year_slices_use_pf_not_net_pnl():
    frame = pd.DataFrame(
        {
            "time": ["2023-01-01", "2023-01-02", "2023-01-03"],
            "pnl_atr": [10.0, -6.0, -5.0],
        }
    )

    assert compute_yearly_breakdown(frame).loc[0, "pf"] < 1.0
    assert frame["pnl_atr"].sum() < 0.0
    assert count_negative_year_slices(frame, min_year_trades=3) == 1
