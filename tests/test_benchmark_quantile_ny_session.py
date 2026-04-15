import json
import sys
import math
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ML.benchmark_quantile_ny_session import (
    assign_session_bucket,
    count_negative_year_slices,
    decide_session_gate,
    evaluate_split,
    filter_session_trades,
    main,
    select_non_ny_quantile_trades,
    select_quantile_trades,
)


def test_assign_session_bucket_maps_known_hours():
    assert assign_session_bucket(2) == "asia"
    assert assign_session_bucket(6) == "asia"
    assert assign_session_bucket(7) == "london"
    assert assign_session_bucket(9) == "london"
    assert assign_session_bucket(12) == "london"
    assert assign_session_bucket(13) == "overlap"
    assert assign_session_bucket(15) == "overlap"
    assert assign_session_bucket(18) == "overlap"
    assert assign_session_bucket(19) == "ny"
    assert assign_session_bucket(21) == "ny"


def test_assign_session_bucket_rejects_invalid_hours():
    with pytest.raises(ValueError, match=r"hour must be in \[0, 23\], got -1"):
        assign_session_bucket(-1)

    with pytest.raises(ValueError, match=r"hour must be in \[0, 23\], got 24"):
        assign_session_bucket(24)


def test_count_negative_year_slices_ignores_tiny_years():
    frame = pd.DataFrame(
        [
            {"year": 2023, "pnl_atr": -1.0},
            {"year": 2023, "pnl_atr": 3.0},
            {"year": 2024, "pnl_atr": -2.0},
            {"year": 2024, "pnl_atr": -1.0},
            {"year": 2025, "pnl_atr": -1.0},
            {"year": 2025, "pnl_atr": 2.0},
            {"year": 2025, "pnl_atr": 2.0},
        ]
    )

    assert count_negative_year_slices(frame, pnl_column="pnl_atr") == 0


def test_evaluate_split_does_not_count_all_zero_year_as_negative():
    frame = pd.DataFrame(
        [
            {"time": "2025.01.01 02:00", "pnl_atr": 0.0},
            {"time": "2025.01.02 02:00", "pnl_atr": 0.0},
            {"time": "2025.01.03 02:00", "pnl_atr": 0.0},
        ]
    )

    result = evaluate_split(frame, split="validation", pnl_column="pnl_atr")

    assert result["pf"] is None
    assert result["negative_year_slices"] == 0
    assert result["yearly"][0]["pf"] is None


def test_select_non_ny_quantile_trades_drops_passing_ny_session():
    quantile_frame = pd.DataFrame(
        {
            "time": [
                "2025.01.01 02:00",
                "2025.01.01 15:00",
                "2025.01.01 21:00",
            ],
            "signal": [1, -1, 1],
            "pred_ret_24_q10": [0.5, 1.0, 0.5],
            "pred_ret_24_q90": [2.0, 3.0, 2.0],
            "true_ret_12_dir_atr": [1.5, 2.5, -1.0],
            "true_ret_24_dir_atr": [2.0, 3.0, -2.0],
        }
    )
    baseline_frame = pd.DataFrame(
        {
            "time": [
                "2025.01.01 02:00",
                "2025.01.01 15:00",
                "2025.01.01 21:00",
            ],
            "signal": [1, -1, 1],
            "pred_ret_24_dir_atr": [0.5, 0.5, 0.5],
        }
    )
    rule_payload = {
        "baseline_threshold": 0.0,
        "winner": {
            "rule": "lb_gt_m",
            "m": 0.0,
            "w": 10.0,
            "correction": 0.0,
        },
    }

    selected = select_non_ny_quantile_trades(
        frame=quantile_frame,
        baseline_frame=baseline_frame,
        selected_rule=rule_payload,
    )

    assert selected["session"].tolist() == ["asia", "overlap"]
    assert selected["time"].tolist() == ["2025.01.01 02:00", "2025.01.01 15:00"]
    assert selected["year"].tolist() == [2025, 2025]
    assert selected["pnl_hold24_atr"].tolist() == [2.0, 3.0]


def test_filter_session_trades_rejects_unknown_session_values():
    frame = pd.DataFrame({"session": ["asia", "broken"]})

    with pytest.raises(ValueError, match=r"unknown session values: \['broken'\]"):
        filter_session_trades(frame)


def test_filter_session_trades_rejects_null_session_values():
    frame = pd.DataFrame({"session": ["asia", None]})

    with pytest.raises(ValueError, match=r"session column contains null/NaN values"):
        filter_session_trades(frame)


def test_select_quantile_trades_rejects_misaligned_baseline_frame():
    quantile_frame = pd.DataFrame(
        {
            "time": ["2025.01.01 02:00", "2025.01.01 15:00"],
            "signal": [1, -1],
            "pred_ret_24_q10": [0.5, 1.0],
            "pred_ret_24_q90": [2.0, 3.0],
            "true_ret_12_dir_atr": [1.5, 2.5],
            "true_ret_24_dir_atr": [2.0, 3.0],
        }
    )
    baseline_frame = pd.DataFrame(
        {
            "time": ["2025.01.01 02:00"],
            "signal": [1],
            "pred_ret_24_dir_atr": [0.5],
        }
    )
    rule_payload = {
        "baseline_threshold": 0.0,
        "winner": {"rule": "lb_gt_m", "m": 0.0, "w": 10.0, "correction": 0.0},
    }

    with pytest.raises(ValueError, match=r"baseline_frame does not align one-to-one"):
        select_quantile_trades(
            frame=quantile_frame,
            baseline_frame=baseline_frame,
            selected_rule=rule_payload,
        )


def test_select_quantile_trades_rejects_unparsable_timestamps():
    quantile_frame = pd.DataFrame(
        {
            "time": ["2025.01.01 02:00", "bad-time"],
            "signal": [1, -1],
            "pred_ret_24_q10": [0.5, 1.0],
            "pred_ret_24_q90": [2.0, 3.0],
            "true_ret_12_dir_atr": [1.5, 2.5],
            "true_ret_24_dir_atr": [2.0, 3.0],
        }
    )
    baseline_frame = pd.DataFrame(
        {
            "time": ["2025.01.01 02:00", "2025.01.01 15:00"],
            "signal": [1, -1],
            "pred_ret_24_dir_atr": [0.5, 0.5],
        }
    )
    rule_payload = {
        "baseline_threshold": 0.0,
        "winner": {
            "rule": "lb_gt_m",
            "m": 0.0,
            "w": 10.0,
            "correction": 0.0,
        },
    }

    with pytest.raises(ValueError, match=r"time contains unparsable timestamps"):
        select_quantile_trades(
            frame=quantile_frame,
            baseline_frame=baseline_frame,
            selected_rule=rule_payload,
        )


def test_decide_session_gate_rejects_support_and_seed_collapse():
    result = decide_session_gate(
        baseline_pf=8.0,
        filtered_pf=20.0,
        filtered_n_trades=29,
        filtered_negative_year_slices=0,
        seed_pf_values=[2.0, 3.0, 0.9],
    )

    assert result["verdict"] == "gate_fail"
    assert "filtered_n_trades=29 < 30" in result["reasons"]
    assert "seed_pf_values_contain_pf<=1.0: [0.9]" in result["reasons"]


def test_decide_session_gate_rejects_non_finite_pf_values():
    result = decide_session_gate(
        baseline_pf=None,
        filtered_pf=None,
        filtered_n_trades=30,
        filtered_negative_year_slices=0,
        seed_pf_values=[2.0, math.nan, None],
    )

    assert result["verdict"] == "gate_fail"
    assert "baseline_pf=None" in result["reasons"]
    assert "filtered_pf=None" in result["reasons"]
    assert "filtered_pf=None <= 2.0" in result["reasons"]
    assert any(reason.startswith("seed_pf_values_contain_non_finite: [nan, None]") for reason in result["reasons"])


def test_cli_writes_validation_artifacts_and_skips_test_when_gate_fails(tmp_path: Path):
    validation_predictions = tmp_path / "validation_predictions.csv"
    test_predictions = tmp_path / "test_predictions.csv"
    baseline_validation_predictions = tmp_path / "baseline_validation_predictions.csv"
    baseline_test_predictions = tmp_path / "baseline_test_predictions.csv"
    selected_rule = tmp_path / "selected_rule.json"
    output_dir = tmp_path / "output"
    root_dir = tmp_path / "root"

    validation_predictions.write_text(
        "time;signal;pred_ret_24_q10;pred_ret_24_q90;true_ret_12_dir_atr;true_ret_24_dir_atr\n"
        "2025.01.01 02:00;1;0.1;0.3;1.0;2.0\n"
        "2025.01.01 15:00;-1;0.1;0.3;1.0;1.0\n"
        "2025.01.01 21:00;1;0.1;0.3;1.0;-1.0\n",
        encoding="utf-8",
    )
    test_predictions.write_text(
        "time;signal;pred_ret_24_q10;pred_ret_24_q90;true_ret_12_dir_atr;true_ret_24_dir_atr\n"
        "2025.01.02 02:00;1;0.1;0.3;1.0;2.0\n"
        "2025.01.02 15:00;-1;0.1;0.3;1.0;1.0\n"
        "2025.01.02 21:00;1;0.1;0.3;1.0;-1.0\n",
        encoding="utf-8",
    )
    baseline_validation_predictions.write_text(
        "time;signal;pred_ret_24_dir_atr\n"
        "2025.01.01 02:00;1;0.5\n"
        "2025.01.01 15:00;-1;0.5\n"
        "2025.01.01 21:00;1;0.5\n",
        encoding="utf-8",
    )
    baseline_test_predictions.write_text(
        "time;signal;pred_ret_24_dir_atr\n"
        "2025.01.02 02:00;1;0.5\n"
        "2025.01.02 15:00;-1;0.5\n"
        "2025.01.02 21:00;1;0.5\n",
        encoding="utf-8",
    )
    selected_rule.write_text(
        json.dumps(
            {
                "baseline_threshold": 0.0,
                "winner": {
                    "rule": "baseline",
                    "m": 0.0,
                    "w": 0.0,
                    "correction": 0.0,
                },
            }
        ),
        encoding="utf-8",
    )

    for seed in (7, 17):
        seed_dir = root_dir / f"seed_{seed:03d}"
        seed_dir.mkdir(parents=True, exist_ok=True)
        (seed_dir / "entry_path_v1_quantile_validation_predictions.csv").write_text(
            validation_predictions.read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        (seed_dir / "entry_path_v1_quantile_test_predictions.csv").write_text(
            test_predictions.read_text(encoding="utf-8"),
            encoding="utf-8",
        )

    code = main(
        [
            "--validation-predictions",
            str(validation_predictions),
            "--test-predictions",
            str(test_predictions),
            "--baseline-validation-predictions",
            str(baseline_validation_predictions),
            "--baseline-test-predictions",
            str(baseline_test_predictions),
            "--selected-rule",
            str(selected_rule),
            "--output-dir",
            str(output_dir),
            "--root-dir",
            str(root_dir),
            "--seeds",
            "7,17",
        ]
    )

    assert code == 0
    validation_path = output_dir / "validation_summary.json"
    test_path = output_dir / "test_summary.json"
    yearly_path = output_dir / "yearly_breakdown.csv"
    per_seed_path = output_dir / "per_seed_summary.csv"
    metadata_path = output_dir / "run_metadata.json"
    assert validation_path.exists()
    assert test_path.exists()
    assert yearly_path.exists()
    assert per_seed_path.exists()
    assert metadata_path.exists()

    validation_summary = json.loads(validation_path.read_text(encoding="utf-8"))
    test_summary = json.loads(test_path.read_text(encoding="utf-8"))
    per_seed = pd.read_csv(per_seed_path, sep=";")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

    assert validation_summary["gate"]["verdict"] == "gate_fail"
    assert test_summary["status"] == "skipped_due_to_validation_gate"
    assert per_seed["seed"].tolist() == [7, 17]
    assert metadata["seeds"] == [7, 17]
