import json
from pathlib import Path

import pandas as pd

from ML.benchmark_quantile_execution_improvement import (
    apply_exit_variant,
    choose_validation_winner,
    compute_variant_metrics,
    evaluate_variants,
    main,
)


def test_apply_exit_variant_timeout_shortens_holding_horizon():
    frame = pd.DataFrame(
        {
            "true_ret_24_dir_atr": [2.0, -1.0],
            "true_ret_12_dir_atr": [1.0, -0.4],
        }
    )

    result = apply_exit_variant(frame, variant="timeout_12")

    assert list(result["pnl_atr"]) == [1.0, -0.4]


def test_compute_variant_metrics_counts_pf():
    frame = pd.DataFrame(
        {
            "pnl_atr": [2.0, -1.0, 3.0],
        }
    )

    result = compute_variant_metrics(frame)

    assert result["n_trades"] == 3
    assert result["pf"] == 5.0


def test_evaluate_variants_returns_one_row_per_variant():
    frame = pd.DataFrame(
        {
            "true_ret_24_dir_atr": [2.0, -1.0],
            "true_ret_12_dir_atr": [1.0, -0.4],
        }
    )

    result = evaluate_variants(frame, variants=["baseline_24", "timeout_12"])

    assert list(result["variant"]) == ["baseline_24", "timeout_12"]
    assert list(result["n_trades"]) == [2, 2]


def test_choose_validation_winner_prefers_pf_uplift():
    grid = pd.DataFrame(
        {
            "variant": ["baseline_24", "timeout_12"],
            "pf": [2.0, 3.0],
            "n_trades": [40, 40],
        }
    )

    result = choose_validation_winner(grid)

    assert result["variant"] == "timeout_12"


def test_main_writes_variant_artifacts(tmp_path: Path):
    validation = tmp_path / "validation.csv"
    test = tmp_path / "test.csv"
    output = tmp_path / "out"

    frame = pd.DataFrame(
        {
            "time": ["2025-01-01", "2025-01-02"],
            "signal": [1, -1],
            "true_ret_12_dir_atr": [1.0, -0.4],
            "true_ret_24_dir_atr": [2.0, -1.0],
            "pred_ret_24_dir_atr": [1.0, 1.0],
            "pred_ret_24_q10": [1.0, 1.0],
            "pred_ret_24_q90": [2.0, 2.0],
        }
    )
    baseline = frame[["time", "signal", "pred_ret_24_dir_atr"]].copy()
    rule = tmp_path / "rule.json"
    baseline_rule = tmp_path / "baseline_rule.json"
    baseline_rule.write_text(
        json.dumps(
            {
                "validation_csv": str(tmp_path / "baseline_validation.csv"),
                "test_csv": str(tmp_path / "baseline_test.csv"),
                "winner": {"score_threshold": 0.0},
            }
        ),
        encoding="utf-8",
    )
    rule.write_text(
        json.dumps(
            {
                "baseline_rule_path": str(baseline_rule),
                "baseline_threshold": 0.0,
                "winner": {"correction": 0.0, "rule": "lb_gt_m", "m": 0.0, "w": 0.0},
            }
        ),
        encoding="utf-8",
    )
    frame.to_csv(validation, sep=";", index=False)
    frame.to_csv(test, sep=";", index=False)
    baseline.to_csv(tmp_path / "baseline_validation.csv", sep=";", index=False)
    baseline.to_csv(tmp_path / "baseline_test.csv", sep=";", index=False)

    code = main(
        [
            "--validation-predictions",
            str(validation),
            "--test-predictions",
            str(test),
            "--output-dir",
            str(output),
            "--rule-path",
            str(rule),
        ]
    )

    assert code == 0
    assert (output / "validation_grid.csv").exists()
    assert (output / "test_grid.csv").exists()
    assert (output / "selected_variant.json").exists()
    assert (output / "run_metadata.json").exists()
    payload = json.loads((output / "selected_variant.json").read_text(encoding="utf-8"))
    assert payload["variant"] in {"baseline_24", "timeout_12"}


def test_main_returns_2_for_missing_required_column(tmp_path: Path):
    predictions = tmp_path / "bad.csv"
    predictions.write_text("time;signal\n2025-01-01;1\n", encoding="utf-8")

    code = main(
        [
            "--validation-predictions",
            str(predictions),
            "--test-predictions",
            str(predictions),
            "--output-dir",
            str(tmp_path / "out"),
        ]
    )

    assert code == 2
