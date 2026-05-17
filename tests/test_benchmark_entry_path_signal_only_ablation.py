import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

sys.path.insert(0, ".")

from ML import benchmark_entry_path_signal_only_ablation as ablation


def _sample_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "time": pd.to_datetime(
                [
                    "2023-01-01 00:00",
                    "2023-01-01 01:00",
                    "2023-01-01 02:00",
                    "2023-01-02 00:00",
                    "2024-01-01 00:00",
                    "2024-01-01 01:00",
                ]
            ),
            "signal": [1, 1, 0, -1, 1, -1],
            "pred_ret_24_dir_atr": [0.90, 0.10, 0.80, 0.70, 0.20, 0.60],
            "true_ret_24_dir_atr": [1.0, -0.5, 0.0, 2.0, -1.0, 3.0],
        }
    )


def test_signal_only_summary_keeps_all_nonzero_signal_rows():
    frame = _sample_frame()

    summary = ablation.summarize_mask(
        frame,
        selected_mask=ablation.build_signal_only_mask(frame),
        label="signal_only",
        min_period_trades=1,
        sequential_hold_bars=2,
    )

    assert summary["label"] == "signal_only"
    assert summary["selected"]["trades"] == 5
    assert np.isclose(summary["selected"]["pf"], 4.0)
    assert np.isclose(summary["selected"]["win_rate"], 0.6)
    assert summary["sequential"]["trades"] == 3
    assert summary["sequential"]["accepted_indices"] == [0, 3, 5]
    assert np.isclose(summary["sequential"]["pf"], float("inf"))


def test_current_score_gate_is_subset_of_signal_only_and_reports_delta():
    frame = _sample_frame()
    signal_only = ablation.build_signal_only_mask(frame)
    current = ablation.build_current_score_gate_mask(frame, threshold=0.60)

    comparison = ablation.compare_summaries(
        signal_only=ablation.summarize_mask(
            frame,
            selected_mask=signal_only,
            label="signal_only",
            min_period_trades=1,
            sequential_hold_bars=2,
        ),
        current=ablation.summarize_mask(
            frame,
            selected_mask=current,
            label="current_score_gate",
            min_period_trades=1,
            sequential_hold_bars=2,
        ),
    )

    assert current.tolist() == [True, False, False, True, False, True]
    assert comparison["selected_trade_delta"] == -2
    assert np.isinf(comparison["selected_pf_delta"])
    assert comparison["sequential_trade_delta"] == 0
    assert comparison["sequential_pf_delta"] == 0.0


def test_cli_writes_summary_json_markdown_and_masks(tmp_path, monkeypatch, capsys):
    frame = _sample_frame()
    predictions_path = tmp_path / "test_predictions.csv"
    frame.assign(time=frame["time"].dt.strftime("%Y.%m.%d %H:%M")).to_csv(
        predictions_path,
        sep=";",
        index=False,
    )
    output_dir = tmp_path / "out"

    monkeypatch.setattr(
        ablation,
        "parse_args",
        lambda: SimpleNamespace(
            predictions=predictions_path,
            threshold=0.60,
            output_dir=output_dir,
            min_period_trades=1,
            sequential_hold_bars=2,
        ),
    )

    result = ablation.main()
    captured = capsys.readouterr()
    printed = json.loads(captured.out)

    assert printed["summary_path"] == result["summary_path"]
    assert (output_dir / "summary.json").exists()
    assert (output_dir / "summary.md").exists()
    assert (output_dir / "selected_rows.csv").exists()

    saved = json.loads((output_dir / "summary.json").read_text(encoding="utf-8"))
    assert saved["signal_only"]["selected"]["trades"] == 5
    assert saved["current_score_gate"]["selected"]["trades"] == 3
    selected_rows = pd.read_csv(output_dir / "selected_rows.csv", sep=";")
    assert set(selected_rows["selection"]) == {"current_score_gate", "signal_only_rejected_by_score"}
