import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ML import benchmark_telemetry_frequency_calibration as calibration


def _prediction_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"time": "2025.01.01 00:00", "signal": 1, "pred_take_24_x8": 0.91, "true_trail_24_pnl_atr_x8": 1.0},
            {"time": "2025.01.01 01:00", "signal": -1, "pred_take_24_x8": 0.85, "true_trail_24_pnl_atr_x8": -0.5},
            {"time": "2025.01.01 02:00", "signal": 0, "pred_take_24_x8": 0.99, "true_trail_24_pnl_atr_x8": 2.0},
            {"time": "2025.01.02 00:00", "signal": 1, "pred_take_24_x8": 0.60, "true_trail_24_pnl_atr_x8": 0.25},
            {"time": "2025.01.02 01:00", "signal": -1, "pred_take_24_x8": 0.40, "true_trail_24_pnl_atr_x8": -0.25},
        ]
    )


def test_calibration_counts_trades_per_day_without_using_pf_as_primary_selector():
    frame = _prediction_frame()

    sparse = calibration.evaluate_candidate(
        frame,
        score_target="take_24_x8",
        selector="prob_ge_threshold",
        threshold=0.9,
    )
    frequent = calibration.evaluate_candidate(
        frame,
        score_target="take_24_x8",
        selector="top_k_probability",
        threshold=1.0,
    )
    selected = calibration.select_diagnostic_preset(pd.DataFrame([sparse, frequent]))

    assert sparse["trades"] == 1
    assert sparse["trades_per_day"] == 0.5
    assert frequent["trades"] == 4
    assert frequent["trades_per_day"] == 2.0
    assert selected["winner"]["selector"] == "top_k_probability"
    assert selected["winner"]["threshold"] == 1.0
    assert selected["diagnostic"] is True


def test_top_k_selector_uses_only_active_signal_rows():
    frame = _prediction_frame()

    result = calibration.evaluate_candidate(
        frame,
        score_target="take_24_x8",
        selector="top_k_probability",
        threshold=0.5,
    )

    assert result["trades"] == 2
    assert result["selected_times"] == ["2025.01.01 00:00", "2025.01.01 01:00"]
    assert "2025.01.01 02:00" not in result["selected_times"]


def test_selection_prioritizes_frequency_over_same_time_opposite_diagnostic():
    sparse_without_opposites = {
        "score_target": "take_24_x8",
        "selector": "prob_ge_threshold",
        "threshold": 0.9,
        "trades": 2,
        "trades_per_day": 1.0,
        "same_time_opposite_signal_groups": 0,
    }
    frequent_with_opposites = {
        "score_target": "take_24_x8",
        "selector": "top_k_probability",
        "threshold": 1.0,
        "trades": 20,
        "trades_per_day": 10.0,
        "same_time_opposite_signal_groups": 2,
    }

    selected = calibration.select_diagnostic_preset(
        pd.DataFrame([sparse_without_opposites, frequent_with_opposites])
    )

    assert selected["winner"]["selector"] == "top_k_probability"
    assert selected["winner"]["threshold"] == 1.0


def test_selected_preset_payload_is_exporter_compatible(tmp_path):
    frame = _prediction_frame()
    predictions = tmp_path / "predictions.csv"
    frame.to_csv(predictions, sep=";", index=False)

    summary = calibration.run_calibration(
        predictions_path=predictions,
        score_targets=("take_24_x8",),
        output_dir=tmp_path / "out",
        thresholds=(0.90,),
        top_k_values=(1.0,),
    )

    selected_rule = json.loads((tmp_path / "out" / "selected_rule.json").read_text(encoding="utf-8"))

    assert summary["selected_rule"]["mode"] == "telemetry_frequency_v1"
    assert selected_rule["winner"]["score_target"] == "take_24_x8"
    assert selected_rule["winner"]["selector"] == "top_k_probability"
    assert selected_rule["winner"]["exit_atr_multiplier"] == 8
    assert selected_rule["execution"]["stop_atr"] == 3.0
    assert (tmp_path / "out" / "calibration_grid.csv").exists()
    assert (tmp_path / "out" / "summary.json").exists()
    assert (tmp_path / "out" / "summary.md").exists()
