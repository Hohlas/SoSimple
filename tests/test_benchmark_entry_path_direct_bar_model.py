import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

sys.path.insert(0, ".")

from ML import benchmark_entry_path_direct_bar_model as direct


def _source_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "time": ["2024.01.01 00:00", "2024.01.01 01:00", "2024.01.01 02:00"],
            "signal": [1, -1, 0],
            "ATR": [1.0, 2.0, 1.5],
            "fractal0": [
                "1:100:-1:0.1:0.2:1:0:0.3:0.4:2:0.5:0:0:0:0:0:0:0:0:0:0:1.1",
                "2:101:1:0.2:0.3:1:0:0.4:0.5:3:0.6:0:0:0:0:0:0:0:0:0:0:1.2",
                "3:102:0:0.3:0.4:0:0:0.5:0.6:4:0.7:0:0:0:0:0:0:0:0:0:0:1.3",
            ],
        }
    )


def test_build_direct_target_uses_profitable_direction_and_skip():
    frame = _source_frame()
    frame["ret_24_dir_atr"] = [0.2, -0.3, 0.0]

    target = direct.build_direct_target(frame, return_column="ret_24_dir_atr", edge_threshold=0.05)

    assert target.tolist() == [1, 1, 0]


def test_predict_direct_signal_uses_active_probability_and_direction_edge():
    probabilities = pd.DataFrame(
        {
            -1: [0.10, 0.55, 0.20],
            0: [0.70, 0.20, 0.50],
            1: [0.20, 0.25, 0.30],
        }
    )

    out = direct.predict_direct_signal(probabilities, threshold=0.50)

    assert out["direct_signal"].tolist() == [0, -1, 1]
    assert np.allclose(out["direct_score"], [0.30, 0.80, 0.50])
    assert np.allclose(out["direction_edge"], [0.10, -0.30, 0.10])


def test_direct_metrics_report_direction_quality_on_selected_rows():
    truth = pd.Series([1, -1, 0, 1])
    pred = pd.Series([1, 1, -1, 0])

    metrics = direct.direct_classification_metrics(truth, pred)

    assert metrics["active_precision"] == 2 / 3
    assert metrics["active_recall"] == 2 / 3
    assert metrics["direction_accuracy_on_pred_active"] == 1 / 2
    assert metrics["correct_signal_precision"] == 1 / 3
    assert metrics["correct_signal_recall"] == 1 / 3


def test_cli_writes_summary_for_synthetic_direct_model(tmp_path, monkeypatch, capsys):
    source = _source_frame()
    train = source.copy()
    validation = source.copy()
    test = source.copy()
    train["ret_24_dir_atr"] = [0.5, 0.4, -0.2]
    validation["ret_24_dir_atr"] = [0.5, 0.4, -0.2]
    test["ret_24_dir_atr"] = [0.5, 0.4, -0.2]

    ohlc = tmp_path / "ohlc.csv"
    ohlc.write_text(
        "time;open;high;low;close;volume\n"
        "2024.01.01 00:00;100;101;99;100;1\n"
        "2024.01.01 01:00;100;105;99;104;1\n"
        "2024.01.01 02:00;104;106;95;96;1\n"
        "2024.01.01 03:00;96;97;94;95;1\n",
        encoding="utf-8",
    )
    train_path = tmp_path / "train.csv"
    validation_path = tmp_path / "validation.csv"
    test_path = tmp_path / "test.csv"
    train.to_csv(train_path, sep=";", index=False)
    validation.to_csv(validation_path, sep=";", index=False)
    test.to_csv(test_path, sep=";", index=False)
    output_dir = tmp_path / "out"

    monkeypatch.setattr(
        direct,
        "parse_args",
        lambda: SimpleNamespace(
            train_source=train_path,
            validation_source=validation_path,
            test_source=test_path,
            ohlc=ohlc,
            output_dir=output_dir,
            probability_grid=[0.10, 0.50],
            return_column="ret_24_dir_atr",
            edge_threshold=0.05,
            min_period_trades=1,
            sequential_hold_bars=2,
            horizon=2,
            random_state=11,
            n_estimators=10,
        ),
    )

    result = direct.main()
    printed = json.loads(capsys.readouterr().out)

    assert printed["summary_path"] == result["summary_path"]
    assert (output_dir / "summary.json").exists()
    assert (output_dir / "summary.md").exists()
    assert (output_dir / "test_selected_rows.csv").exists()
