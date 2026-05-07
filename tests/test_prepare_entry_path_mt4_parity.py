import json

import pandas as pd

from ML import prepare_entry_path_mt4_parity as prep


def _write_predictions(path, scores):
    frame = pd.DataFrame(
        {
            "time": [f"2025.01.01 0{i}:00" for i in range(len(scores))],
            "signal": [1, -1, 1, -1],
            "pred_ret_24_dir_atr": scores,
            "true_ret_24_dir_atr": [2.0, -1.0, 3.0, -2.0],
        }
    )
    frame.to_csv(path, sep=";", index=False)


def test_prepare_entry_path_mt4_parity_freezes_candidate_a_rule_and_exports_signals(tmp_path):
    validation = tmp_path / "validation_predictions.csv"
    test = tmp_path / "test_predictions.csv"
    output_dir = tmp_path / "parity"
    _write_predictions(validation, [0.1, 0.2, 0.3, 0.4])
    _write_predictions(test, [0.05, 0.25, 0.35, 0.45])

    result = prep.prepare_parity_export(
        validation_csv=validation,
        test_csv=test,
        output_dir=output_dir,
        target_coverage=0.5,
        copy_to_mt4=False,
    )

    rule = json.loads((output_dir / "entry_path_v1_live_safe_a500_rule.json").read_text(encoding="utf-8"))
    signals = pd.read_csv(output_dir / "ml_signals.csv", sep=";")
    metadata = json.loads((output_dir / "metadata.json").read_text(encoding="utf-8"))

    assert result["rule_path"] == str(output_dir / "entry_path_v1_live_safe_a500_rule.json")
    assert rule["winner"]["candidate"] == "A"
    assert rule["winner"]["target_coverage"] == 0.5
    assert rule["winner"]["score_threshold"] == 0.25
    assert signals["signal"].tolist() == [0, -1, 1, -1]
    assert metadata["nonzero_signals"] == 3
    assert metadata["buy_signals"] == 1
    assert metadata["sell_signals"] == 2
