import numpy as np
import pandas as pd

import ML.baseline.analyze_regression_updn_already_moved_audit as audit


def test_parse_fractal0_extracts_time_price_and_direction():
    value = "1700000000:2030.5:-1:0.1:0.2:0:0:0:0.3:1:0.4:1:2:3:4:5:6:0.7:0.8:0.9:1.0:2.5:2"

    parsed = audit.parse_fractal0(value)

    assert parsed == {
        "time": 1700000000,
        "price": 2030.5,
        "direction": -1,
        "shift": 2,
    }


def test_safe_log_ratio_is_finite_for_zero_denominator():
    result = audit.safe_log_ratio(np.array([2.0, 0.0]), np.array([0.0, 3.0]))

    assert np.isfinite(result).all()
    assert result[0] > 0
    assert result[1] < 0


def test_movement_from_fractal_to_entry_separates_up_and_down():
    up = audit.movement_from_fractal_to_entry(fractal_price=100.0, entry_open=103.0)
    down = audit.movement_from_fractal_to_entry(fractal_price=100.0, entry_open=97.5)

    assert up["already_up"] == 3.0
    assert up["already_dn"] == 0.0
    assert down["already_up"] == 0.0
    assert down["already_dn"] == 2.5


def test_attach_entry_open_uses_first_bar_after_signal_time():
    rows = pd.DataFrame({
        "time": ["2021.01.01 10:00"],
        "fractal0": ["1609491600:100.0:-1:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:1.0:2"],
    })
    ohlc = pd.DataFrame({
        "time": pd.to_datetime(["2021.01.01 10:00", "2021.01.01 11:00"]),
        "open": [101.0, 102.0],
        "high": [102.0, 103.0],
        "low": [99.0, 101.0],
        "close": [101.5, 102.5],
    })

    enriched, report = audit.attach_entry_open(rows, ohlc)

    assert report["missing_entry_open"] == 0
    assert enriched.loc[0, "entry_time"] == pd.Timestamp("2021.01.01 11:00")
    assert enriched.loc[0, "entry_open"] == 102.0


def test_reconstruct_window_moves_uses_next_h_bars_after_fractal_bar():
    rows = pd.DataFrame({
        "time": ["2021.01.01 10:00"],
        "fractal0_price": [100.0],
        "fractal0_time": [pd.Timestamp("2021.01.01 09:00")],
    })
    ohlc = pd.DataFrame({
        "time": pd.to_datetime([
            "2021.01.01 09:00", "2021.01.01 10:00",
            "2021.01.01 11:00", "2021.01.01 12:00",
        ]),
        "open": [100.0, 101.0, 102.0, 101.0],
        "high": [101.0, 103.0, 104.0, 102.0],
        "low": [99.0, 100.5, 101.5, 98.0],
        "close": [100.5, 102.0, 102.5, 99.0],
    })

    result = audit.reconstruct_window_moves(rows, ohlc, horizon=3)

    assert result.loc[0, "reconstructed_up_3"] == 4.0
    assert result.loc[0, "reconstructed_dn_3"] == 2.0
    assert result.loc[0, "bars_in_window_3"] == 3


def test_denormalize_updn_matrix_uses_source_row_params():
    values = np.array([
        [0.85, 0.425, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.85, 0.425, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    ], dtype=np.float32)
    params = {
        "train": np.array([[[10.0, 20.0]] * 5], dtype=np.float64),
        "validation": np.array([[[100.0, 200.0]] * 5], dtype=np.float64),
    }
    source = pd.Series(["train", "validation"])
    source_row_idx = pd.Series([0, 0])

    out = audit.denormalize_updn_matrix(values, source, source_row_idx, params)

    np.testing.assert_allclose(out[0, :2], [10.0, 5.0])
    np.testing.assert_allclose(out[1, :2], [100.0, 50.0])


def test_attach_already_moved_columns_reports_unclipped_share():
    rows = pd.DataFrame({
        "fractal0_price": [100.0],
        "entry_open": [103.0],
        "actual_up_3_price": [2.0],
        "actual_dn_3_price": [4.0],
        "pred_up_3_price": [5.0],
        "pred_dn_3_price": [1.0],
    })

    out = audit.attach_already_moved_columns(rows, horizons=(3,))

    assert out.loc[0, "already_up"] == 3.0
    assert out.loc[0, "already_dn"] == 0.0
    assert out.loc[0, "already_up_share_3"] == 1.5
    assert out.loc[0, "already_dn_share_3"] == 0.0
    assert out.loc[0, "actual_residual_up_3_by_subtraction"] == 0.0
    assert out.loc[0, "actual_residual_dn_3_by_subtraction"] == 4.0
    assert out.loc[0, "pred_residual_up_3_by_subtraction"] == 2.0
    assert out.loc[0, "pred_residual_dn_3_by_subtraction"] == 1.0


def test_summary_reports_direction_groups():
    rows = pd.DataFrame({
        "fractal0_direction": [-1, -1, 1, 1],
        "already_up_share_3": [0.8, 0.2, 0.0, 0.1],
        "already_dn_share_3": [0.0, 0.1, 0.7, 0.3],
        "already_abs_share_max_3": [0.8, 0.2, 0.7, 0.3],
        "future_up_from_entry_3": [1.0, 0.0, 0.0, 1.0],
        "future_dn_from_entry_3": [0.0, 1.0, 2.0, 0.0],
        "pred_log_ratio_3": [2.0, 1.0, -2.0, -1.0],
        "actual_log_ratio_3": [2.1, 0.8, -2.2, -0.9],
        "future_entry_log_ratio_3": [0.1, -0.1, 0.0, 0.2],
        "pred_residual_log_ratio_3": [0.2, 0.1, -0.2, -0.1],
        "actual_residual_log_ratio_3": [0.1, -0.1, -0.1, 0.1],
    })

    summary = audit.summarize_already_moved(rows, horizons=(3,))

    assert "h3" in summary
    assert summary["h3"]["rows"] == 4
    assert summary["h3"]["dir_-1"]["rows"] == 2
    assert summary["h3"]["dir_1"]["rows"] == 2


def test_attach_future_from_entry_columns_measures_remaining_window():
    rows = pd.DataFrame({
        "entry_time": [pd.Timestamp("2021.01.01 11:00")],
        "entry_open": [102.0],
        "label_end_time_3": [pd.Timestamp("2021.01.01 12:00")],
    })
    ohlc = pd.DataFrame({
        "time": pd.to_datetime(["2021.01.01 11:00", "2021.01.01 12:00"]),
        "open": [102.0, 101.0],
        "high": [103.0, 104.0],
        "low": [101.5, 99.0],
        "close": [102.5, 100.0],
    })

    out = audit.attach_future_from_entry_columns(rows, ohlc, horizons=(3,))

    assert out.loc[0, "future_up_from_entry_3"] == 2.0
    assert out.loc[0, "future_dn_from_entry_3"] == 3.0
    assert out.loc[0, "bars_after_entry_3"] == 2


def test_subtraction_residual_can_differ_from_direct_future_move():
    rows = pd.DataFrame({
        "fractal0_price": [100.0],
        "entry_open": [103.0],
        "actual_up_3_price": [5.0],
        "actual_dn_3_price": [1.0],
        "pred_up_3_price": [5.0],
        "pred_dn_3_price": [1.0],
        "entry_time": [pd.Timestamp("2021.01.01 11:00")],
        "label_end_time_3": [pd.Timestamp("2021.01.01 12:00")],
    })
    ohlc = pd.DataFrame({
        "time": pd.to_datetime(["2021.01.01 11:00", "2021.01.01 12:00"]),
        "open": [103.0, 102.0],
        "high": [103.2, 103.1],
        "low": [102.5, 101.0],
        "close": [102.8, 101.5],
    })

    rows = audit.attach_already_moved_columns(rows, horizons=(3,))
    rows = audit.attach_future_from_entry_columns(rows, ohlc, horizons=(3,))

    assert rows.loc[0, "actual_residual_up_3_by_subtraction"] == 2.0
    assert rows.loc[0, "future_up_from_entry_3"] == 0.2


def test_cli_flag_is_registered():
    parser = audit.build_arg_parser()
    args = parser.parse_args(["--regression-updn-already-moved-audit"])

    assert args.regression_updn_already_moved_audit is True


def test_select_label_window_contract_uses_fixed_bar_contract():
    rows = pd.DataFrame({
        "fractal0_price": [100.0],
        "fractal0_time": [pd.Timestamp("2021.01.01 09:00")],
        "actual_up_3_price": [4.0],
        "actual_dn_3_price": [2.0],
    })
    ohlc = pd.DataFrame({
        "time": pd.to_datetime([
            "2021.01.01 09:00",
            "2021.01.01 10:00",
            "2021.01.01 11:00",
            "2021.01.01 12:00",
        ]),
        "open": [100.0, 101.0, 102.0, 101.0],
        "high": [101.0, 103.0, 104.0, 102.0],
        "low": [99.0, 100.5, 101.5, 98.0],
        "close": [100.5, 102.0, 102.5, 99.0],
    })

    contract = audit.select_label_window_contract(rows, ohlc, horizons=(3,))

    assert contract["status"] == "PASS"
    assert contract["contract"] == "next_h_ohlc_bars_after_fractal_bar"


def test_coverage_disclosure_marks_used_rows():
    rows = pd.DataFrame({
        "fractal0_price": [1.0, np.nan],
        "entry_open": [2.0, 2.0],
        "bars_in_window_3": [3, 2],
        "bars_after_entry_3": [1, 0],
    })

    result = audit.coverage_disclosure(rows, horizons=(3,))

    assert result["rows_total"] == 2
    assert result["rows_used_in_summary"] == 1
    assert rows["used_in_summary"].tolist() == [True, False]
