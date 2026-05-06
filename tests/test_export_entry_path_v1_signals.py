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
            {
                "time": "2025.01.01 00:00",
                "signal": 1,
                "pred_ret_24_dir_atr": 0.50,
                "pred_ret_12_dir_atr": 0.50,
                "pred_fav_12_atr": 0.60,
                "pred_adv_12_atr": 0.10,
                "pred_fav_24_atr": 0.70,
                "pred_adv_24_atr": 0.20,
                "pred_path_6_prob_pos": 0.70,
                "pred_path_6_prob_neg": 0.20,
            },
            {
                "time": "2025.01.01 00:00",
                "signal": -1,
                "pred_ret_24_dir_atr": -0.40,
                "pred_ret_12_dir_atr": -0.40,
                "pred_fav_12_atr": 0.10,
                "pred_adv_12_atr": 0.60,
                "pred_fav_24_atr": 0.20,
                "pred_adv_24_atr": 0.70,
                "pred_path_6_prob_pos": 0.20,
                "pred_path_6_prob_neg": 0.70,
            },
            {
                "time": "2025.01.01 01:00",
                "signal": -1,
                "pred_ret_24_dir_atr": -0.10,
                "pred_ret_12_dir_atr": -0.10,
                "pred_fav_12_atr": 0.30,
                "pred_adv_12_atr": 0.40,
                "pred_fav_24_atr": 0.40,
                "pred_adv_24_atr": 0.50,
                "pred_path_6_prob_pos": 0.40,
                "pred_path_6_prob_neg": 0.50,
            },
            {
                "time": "2025.01.01 02:00",
                "signal": 0,
                "pred_ret_24_dir_atr": 0.70,
                "pred_ret_12_dir_atr": 0.70,
                "pred_fav_12_atr": 0.80,
                "pred_adv_12_atr": 0.10,
                "pred_fav_24_atr": 0.90,
                "pred_adv_24_atr": 0.20,
                "pred_path_6_prob_pos": 0.80,
                "pred_path_6_prob_neg": 0.10,
            },
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


def test_export_signals_supports_b_no_path6_with_frozen_validation_scaler(tmp_path):
    validation = tmp_path / "validation_predictions.csv"
    predictions = tmp_path / "entry_path_v1_test_predictions.csv"
    _write_predictions(validation)
    _write_predictions(predictions)
    rule_path = tmp_path / "entry_path_trade_filter_selected_rule.json"
    rule_path.write_text(
        json.dumps(
            {
                "winner": {"candidate": "B_no_path6", "score_threshold": 0.7},
                "validation_csv": str(validation),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    output_path = tmp_path / "ml_signals.csv"

    exporter.export_signals(
        predictions_path=predictions,
        rule_path=rule_path,
        output_path=output_path,
    )

    out = pd.read_csv(output_path, sep=";")
    assert out["time"].tolist() == [
        "2025.01.01 00:00",
        "2025.01.01 01:00",
        "2025.01.01 02:00",
    ]
    assert out["signal"].tolist() == [1, 0, 0]


def test_export_signals_rejects_unknown_winner(tmp_path):
    predictions = tmp_path / "entry_path_v1_test_predictions.csv"
    _write_predictions(predictions)
    rule_path = tmp_path / "entry_path_trade_filter_selected_rule.json"
    rule_path.write_text(
        json.dumps({"winner": {"candidate": "unknown", "score_threshold": 0.2}}, ensure_ascii=False, indent=2),
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
