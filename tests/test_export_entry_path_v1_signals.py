import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from API import export_entry_path_v1_signals as exporter


def _write_predictions(path: Path) -> None:
    pd.DataFrame(
        [
            {"time": "2025.01.01 00:00", "signal": 1, "pred_ret_24_dir_atr": 0.50},
            {"time": "2025.01.01 00:00", "signal": -1, "pred_ret_24_dir_atr": -0.40},
            {"time": "2025.01.01 01:00", "signal": -1, "pred_ret_24_dir_atr": -0.10},
            {"time": "2025.01.01 02:00", "signal": 0, "pred_ret_24_dir_atr": 0.70},
        ]
    ).to_csv(path, sep=";", index=False)


def test_export_signals_applies_frozen_threshold_and_writes_time_signal(tmp_path):
    predictions = tmp_path / "entry_path_v1_test_predictions.csv"
    _write_predictions(predictions)
    rule_path = tmp_path / "entry_path_trade_filter_selected_rule.json"
    rule_path.write_text(
        json.dumps({"winner": {"candidate": "A", "score_threshold": 0.2}}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    output_path = tmp_path / "ml_signals.csv"

    exporter.export_signals(
        predictions_path=predictions,
        rule_path=rule_path,
        output_path=output_path,
    )

    out = pd.read_csv(output_path, sep=";")
    assert list(out.columns) == ["time", "signal"]
    assert out["time"].tolist() == [
        "2025.01.01 00:00",
        "2025.01.01 01:00",
        "2025.01.01 02:00",
    ]
    assert out["signal"].tolist() == [1, 0, 0]


def test_export_signals_rejects_non_a_winner_without_research_scaler(tmp_path):
    predictions = tmp_path / "entry_path_v1_test_predictions.csv"
    _write_predictions(predictions)
    rule_path = tmp_path / "entry_path_trade_filter_selected_rule.json"
    rule_path.write_text(
        json.dumps({"winner": {"candidate": "B", "score_threshold": 0.2}}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    try:
        exporter.export_signals(
            predictions_path=predictions,
            rule_path=rule_path,
            output_path=tmp_path / "ml_signals.csv",
        )
    except ValueError as exc:
        assert "Unsupported entry_path_v1 winner" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unsupported winner")
