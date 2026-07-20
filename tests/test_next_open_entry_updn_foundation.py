import numpy as np
import pandas as pd

import ML.baseline.benchmark_next_open_entry_updn_foundation as foundation


def test_parse_project_time_uses_real_dataset_format():
    parsed = foundation.parse_project_time("2019.06.20 16:00")

    assert parsed == pd.Timestamp("2019-06-20 16:00:00")


def test_resolve_entry_bar_uses_first_open_strictly_after_signal_time():
    ohlc_times = np.array(pd.to_datetime(
        ["2019-06-20 15:00", "2019-06-20 16:00", "2019-06-20 17:00", "2019-06-20 18:00"]
    ))

    assert foundation.resolve_entry_bar(pd.Timestamp("2019-06-20 16:00"), ohlc_times) == 2
    assert foundation.resolve_entry_bar(pd.Timestamp("2019-06-20 16:30"), ohlc_times) == 2
    assert foundation.resolve_entry_bar(pd.Timestamp("2019-06-20 18:00"), ohlc_times) is None


def test_compute_entry_updn_from_ohlc_measures_from_entry_open():
    highs = np.array([0.0, 0.0, 106.0, 107.5, 104.0])
    lows = np.array([0.0, 0.0, 99.5, 98.0, 101.0])

    up, dn = foundation.compute_entry_updn_from_ohlc(
        entry_index=2,
        horizon=2,
        highs=highs,
        lows=lows,
        entry_open=100.0,
    )

    assert up == 7.5
    assert dn == 2.0


def test_rebuild_entry_targets_adds_entry_columns_for_each_horizon():
    df = pd.DataFrame(
        {
            "time": ["2019.06.20 15:30"],
            "fractal0": ["100:2000.0:1:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0"],
        }
    ).set_index(pd.Index([10]))
    ohlc = pd.DataFrame(
        {
            "time": ["2019.06.20 15:00", "2019.06.20 16:00", "2019.06.20 17:00", "2019.06.20 18:00"],
            "open": [10.0, 11.0, 12.0, 13.0],
            "high": [10.5, 12.5, 15.0, 14.0],
            "low": [9.5, 10.0, 11.5, 12.0],
        }
    )

    rebuilt = foundation.rebuild_entry_targets(df, foundation.prepare_ohlc(ohlc), horizons=(1, 2))

    assert str(rebuilt.loc[10, "entry_time"]) == "2019-06-20 16:00:00"
    assert rebuilt.loc[10, "entry_open"] == 11.0
    assert rebuilt.loc[10, "entry_up_1"] == 1.5
    assert rebuilt.loc[10, "entry_dn_1"] == 1.0
    assert rebuilt.loc[10, "entry_up_2"] == 4.0
    assert rebuilt.loc[10, "entry_dn_2"] == 1.0


def test_validate_summary_rejects_missing_required_fields():
    summary = {"status": "PASS_DIAGNOSTIC"}

    missing = foundation.validate_summary(summary)

    assert "artifact_status" in missing
    assert "target_contract" in missing
    assert "primary_split" in missing
    assert "horizons" in missing


def test_runner_decision_gate_checks_primary_and_disclosure_horizons():
    report = {
        "primary_split": "val_stop",
        "disclosure_splits": ["diagnostic_holdout"],
        "horizons": [3, 6],
        "model_metrics": {
            "val_stop": {
                "log_ratio": {
                    "log_ratio_3": {"spearman": 0.01},
                    "log_ratio_6": {"spearman": 0.02},
                }
            },
            "diagnostic_holdout": {
                "log_ratio": {
                    "log_ratio_3": {"spearman": 0.03},
                    "log_ratio_6": {"spearman": 0.11},
                }
            },
        },
    }

    gate = foundation.build_runner_decision_gate(report, threshold=0.10)

    assert gate["passes"] is True
    assert gate["max_checked_spearman"] == 0.11
    assert foundation.decide_runner_status(report, threshold=0.10) == "PASS_DIAGNOSTIC"
