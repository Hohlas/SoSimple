import json
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ML.benchmark_quantile_ny_session import select_quantile_trades as upstream_select_quantile_trades
from ML.benchmark_quantile_pred_adv_cap import (
    compute_adv_threshold,
    build_validation_first_adv_cap,
    decide_adv_cap_gate,
    evaluate_split,
    filter_by_adv_cap,
    main,
    select_frozen_quantile_trades,
)


def test_compute_adv_threshold_uses_validation_q75():
    frame = pd.DataFrame({"pred_adv_12_atr": [0.01, 0.02, 0.03, 0.04]})

    assert compute_adv_threshold(frame, quantile=0.75) == 0.0325


def test_compute_adv_threshold_requires_pred_adv_12_atr():
    frame = pd.DataFrame({"other": [0.01, 0.02]})

    with pytest.raises(ValueError, match=r"missing columns: \['pred_adv_12_atr'\]"):
        compute_adv_threshold(frame, quantile=0.75)


@pytest.mark.parametrize("bad_value", [None, float("nan"), float("inf"), float("-inf")])
def test_compute_adv_threshold_rejects_non_finite_pred_adv_values(bad_value):
    frame = pd.DataFrame({"pred_adv_12_atr": [0.01, bad_value, 0.03]})

    with pytest.raises(ValueError, match=r"pred_adv_12_atr contains null/NaN/non-finite values"):
        compute_adv_threshold(frame, quantile=0.75)


def test_filter_by_adv_cap_keeps_values_at_threshold():
    frame = pd.DataFrame({"pred_adv_12_atr": [0.01, 0.03, 0.04]})

    out = filter_by_adv_cap(frame, threshold=0.03)

    assert out["pred_adv_12_atr"].tolist() == [0.01, 0.03]


def test_filter_by_adv_cap_requires_pred_adv_12_atr():
    frame = pd.DataFrame({"other": [0.01, 0.03, 0.04]})

    with pytest.raises(ValueError, match=r"missing columns: \['pred_adv_12_atr'\]"):
        filter_by_adv_cap(frame, threshold=0.03)


@pytest.mark.parametrize("bad_threshold", [None, float("nan"), float("inf"), float("-inf")])
def test_filter_by_adv_cap_rejects_non_finite_threshold(bad_threshold):
    frame = pd.DataFrame({"pred_adv_12_atr": [0.01, 0.03, 0.04]})

    with pytest.raises(ValueError, match=r"threshold must be a finite number"):
        filter_by_adv_cap(frame, threshold=bad_threshold)


def test_decide_adv_cap_gate_rejects_support_and_seed_collapse():
    result = decide_adv_cap_gate(
        baseline_pf=8.0,
        filtered_pf=12.0,
        filtered_n_trades=29,
        filtered_negative_year_slices=0,
        seed_pf_values=[2.0, 0.9],
    )

    assert result["verdict"] == "gate_fail"
    assert "filtered_n_trades=29 < 30" in result["reasons"]
    assert "seed_pf_values_contain_pf<=1.0: [0.9]" in result["reasons"]


@pytest.mark.parametrize(
    "kwargs, expected_reason",
    [
        (
            dict(
                baseline_pf=None,
                filtered_pf=12.0,
                filtered_n_trades=30,
                filtered_negative_year_slices=0,
                seed_pf_values=[2.0, 2.5],
            ),
            "baseline_pf=None",
        ),
        (
            dict(
                baseline_pf=8.0,
                filtered_pf=float("nan"),
                filtered_n_trades=30,
                filtered_negative_year_slices=0,
                seed_pf_values=[2.0, 2.5],
            ),
            "filtered_pf=nan is not finite",
        ),
        (
            dict(
                baseline_pf=8.0,
                filtered_pf=12.0,
                filtered_n_trades=float("nan"),
                filtered_negative_year_slices=0,
                seed_pf_values=[2.0, 2.5],
            ),
            "filtered_n_trades=nan is not finite",
        ),
        (
            dict(
                baseline_pf=8.0,
                filtered_pf=12.0,
                filtered_n_trades=30,
                filtered_negative_year_slices=float("nan"),
                seed_pf_values=[2.0, 2.5],
            ),
            "filtered_negative_year_slices=nan is not finite",
        ),
        (
            dict(
                baseline_pf=8.0,
                filtered_pf=12.0,
                filtered_n_trades=30,
                filtered_negative_year_slices=0,
                seed_pf_values=[2.0, float("inf"), 2.5],
            ),
            "seed_pf_values_contain_non_finite: [inf]",
        ),
    ],
)
def test_decide_adv_cap_gate_rejects_invalid_numeric_values(kwargs, expected_reason):
    result = decide_adv_cap_gate(**kwargs)

    assert result["verdict"] == "gate_fail"
    assert expected_reason in result["reasons"]


def _make_quantile_frame(pred_adv_values, signals=None, years=None):
    signals = signals or [1, 1, 0, 1]
    years = years or [2023, 2023, 2023, 2024]
    rows = []
    for idx, (pred_adv, signal, year) in enumerate(zip(pred_adv_values, signals, years, strict=True), start=1):
        rows.append(
            {
                "time": f"{year}.01.0{idx} 0{idx}:00",
                "signal": signal,
                "pred_ret_24_q10": 1.0,
                "pred_ret_24_q90": 2.0,
                "true_ret_12_dir_atr": 0.5 * idx,
                "true_ret_24_dir_atr": 1.0 * idx,
                "pred_adv_12_atr": pred_adv,
            }
        )
    frame = pd.DataFrame(rows)
    baseline = pd.DataFrame(
        {
            "time": frame["time"],
            "signal": frame["signal"],
            "pred_ret_24_dir_atr": [0.6, 0.7, 0.8, 0.9],
        }
    )
    return frame, baseline


def _selected_rule():
    return {
        "baseline_threshold": 0.5,
        "winner": {
            "rule": "baseline",
            "correction": 0.0,
            "m": 0.0,
            "w": 0.0,
        },
    }


def _write_quantile_predictions(
    path: Path,
    pnl_values: list[float],
    *,
    pred_adv_values: list[float] | None = None,
) -> None:
    if pred_adv_values is None:
        pred_adv_values = [0.10] * len(pnl_values)
    rows = []
    for idx, (pnl, pred_adv) in enumerate(zip(pnl_values, pred_adv_values, strict=True), start=1):
        rows.append(
            {
                "time": f"2025.01.{idx:02d} 00:00",
                "signal": 1,
                "pred_ret_24_q10": 0.1,
                "pred_ret_24_q90": 0.3,
                "true_ret_12_dir_atr": pnl,
                "true_ret_24_dir_atr": pnl,
                "pred_adv_12_atr": pred_adv,
            }
        )
    pd.DataFrame(rows).to_csv(path, sep=";", index=False)


def _write_baseline_predictions(path: Path, n_rows: int) -> None:
    rows = [
        {
            "time": f"2025.01.{idx:02d} 00:00",
            "signal": 1,
            "pred_ret_24_dir_atr": 0.6,
        }
        for idx in range(1, n_rows + 1)
    ]
    pd.DataFrame(rows).to_csv(path, sep=";", index=False)


def _prepare_cli_inputs(
    tmp_path: Path,
    *,
    validation_pnl: list[float],
    test_pnl: list[float],
    seed_ids: list[int],
) -> tuple[Path, Path, Path, Path, Path, Path]:
    validation_predictions = tmp_path / "validation_predictions.csv"
    test_predictions = tmp_path / "test_predictions.csv"
    baseline_validation_predictions = tmp_path / "baseline_validation_predictions.csv"
    baseline_test_predictions = tmp_path / "baseline_test_predictions.csv"
    selected_rule = tmp_path / "selected_rule.json"
    root_dir = tmp_path / "root"

    _write_quantile_predictions(validation_predictions, validation_pnl)
    _write_quantile_predictions(test_predictions, test_pnl)
    _write_baseline_predictions(baseline_validation_predictions, len(validation_pnl))
    _write_baseline_predictions(baseline_test_predictions, len(test_pnl))
    selected_rule.write_text(json.dumps(_selected_rule()), encoding="utf-8")

    for seed in seed_ids:
        seed_dir = root_dir / f"seed_{seed:03d}"
        seed_dir.mkdir(parents=True, exist_ok=True)
        _write_quantile_predictions(
            seed_dir / "entry_path_v1_quantile_validation_predictions.csv",
            validation_pnl,
        )
        _write_quantile_predictions(
            seed_dir / "entry_path_v1_quantile_test_predictions.csv",
            test_pnl,
        )

    return (
        validation_predictions,
        test_predictions,
        baseline_validation_predictions,
        baseline_test_predictions,
        selected_rule,
        root_dir,
    )


def test_select_frozen_quantile_trades_matches_upstream_selection_and_preserves_pred_adv():
    frame, baseline = _make_quantile_frame([0.10, 0.20, 0.90, 0.30])
    selected_rule = _selected_rule()

    upstream = upstream_select_quantile_trades(
        frame=frame,
        baseline_frame=baseline,
        selected_rule=selected_rule,
    )
    out = select_frozen_quantile_trades(
        frame=frame,
        baseline_frame=baseline,
        selected_rule=selected_rule,
    )

    pd.testing.assert_frame_equal(out, upstream)
    assert out["pred_adv_12_atr"].tolist() == [0.10, 0.20, 0.30]


def test_validation_threshold_comes_from_selected_validation_rows_only_and_caps_inclusively():
    validation_frame, validation_baseline = _make_quantile_frame(
        [0.10, 0.20, 0.30, 0.99],
        signals=[1, 1, 1, 0],
    )
    test_frame, test_baseline = _make_quantile_frame(
        [0.05, 0.25, 0.40, 0.80],
        signals=[1, 1, 1, 0],
    )
    selected_rule = _selected_rule()

    result = build_validation_first_adv_cap(
        validation_frame=validation_frame,
        validation_baseline_frame=validation_baseline,
        test_frame=test_frame,
        test_baseline_frame=test_baseline,
        selected_rule=selected_rule,
        quantile=0.75,
    )

    assert result["validation_threshold"] == pytest.approx(0.25)
    assert result["validation_selected"]["pred_adv_12_atr"].tolist() == [0.10, 0.20, 0.30]
    assert result["validation_filtered"]["pred_adv_12_atr"].tolist() == [0.10, 0.20]
    assert result["test_filtered"]["pred_adv_12_atr"].tolist() == [0.05, 0.25]
    assert result["test_summary"]["n_trades"] == 2


def test_evaluate_split_reports_yearly_metrics():
    frame = pd.DataFrame(
        {
            "time": [
                "2023.01.01 00:00",
                "2023.02.01 00:00",
                "2023.03.01 00:00",
                "2024.01.01 00:00",
                "2024.02.01 00:00",
                "2024.03.01 00:00",
            ],
            "pnl_hold24_atr": [1.0, -2.0, -1.0, 2.0, 1.0, -1.0],
        }
    )

    out = evaluate_split(frame, split="validation", pnl_column="pnl_hold24_atr")

    assert out["n_trades"] == 6
    assert out["wins"] == 3
    assert out["losses"] == 3
    assert out["gross_profit"] == 4.0
    assert out["gross_loss"] == 4.0
    assert out["pf"] == pytest.approx(1.0)
    assert out["win_rate"] == pytest.approx(0.5)
    assert out["mean_pnl_atr"] == pytest.approx(0.0)
    assert out["negative_year_slices"] == 1
    assert [row["year"] for row in out["yearly"]] == [2023, 2024]
    assert out["yearly"][0]["pf"] == pytest.approx(1 / 3)
    assert out["yearly"][1]["pf"] == pytest.approx(3.0)


def test_cli_writes_validation_artifacts_and_skips_test_when_gate_fails(tmp_path: Path):
    (
        validation_predictions,
        test_predictions,
        baseline_validation_predictions,
        baseline_test_predictions,
        selected_rule,
        root_dir,
    ) = _prepare_cli_inputs(
        tmp_path,
        validation_pnl=[2.0, 1.0, -1.0],
        test_pnl=[2.0, 1.0, -1.0],
        seed_ids=[7, 17],
    )
    output_dir = tmp_path / "output"

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
    assert metadata["validation_threshold"] == pytest.approx(0.1)
    assert test_summary["status"] == "skipped_due_to_validation_gate"
    assert test_summary["gate"]["verdict"] == "skipped_due_to_validation_gate"
    assert per_seed["seed"].tolist() == [7, 17]
    assert {"root_dir", "seed_dir"}.issubset(per_seed.columns)
    assert metadata["seeds"] == [7, 17]


def test_cli_evaluates_test_once_when_validation_gate_passes(tmp_path: Path):
    (
        validation_predictions,
        test_predictions,
        baseline_validation_predictions,
        baseline_test_predictions,
        selected_rule,
        root_dir,
    ) = _prepare_cli_inputs(
        tmp_path,
        validation_pnl=[3.0] * 24 + [-1.0] * 6,
        test_pnl=[3.0] * 24 + [-1.0] * 6,
        seed_ids=[7, 17],
    )
    output_dir = tmp_path / "output"

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
    validation_summary = json.loads((output_dir / "validation_summary.json").read_text(encoding="utf-8"))
    test_summary = json.loads((output_dir / "test_summary.json").read_text(encoding="utf-8"))
    yearly_breakdown = pd.read_csv(output_dir / "yearly_breakdown.csv", sep=";")
    per_seed = pd.read_csv(output_dir / "per_seed_summary.csv", sep=";")
    metadata = json.loads((output_dir / "run_metadata.json").read_text(encoding="utf-8"))

    assert validation_summary["gate"]["verdict"] == "gate_pass"
    assert test_summary["status"] == "evaluated"
    assert test_summary["gate"]["verdict"] == "gate_pass"
    assert metadata["validation_threshold"] == pytest.approx(0.1)
    assert metadata["test_status"] == "evaluated"
    assert per_seed["seed"].tolist() == [7, 17]
    assert list(yearly_breakdown["split"].unique()) == ["validation", "test"]
