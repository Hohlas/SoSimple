import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

sys.path.insert(0, ".")

from ML import benchmark_entry_path_causal_surrogate as surrogate


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


def test_build_live_safe_features_uses_fractal0_geometry_and_time():
    features = surrogate.build_live_safe_features(_source_frame())

    assert list(features.columns) == surrogate.FEATURE_COLUMNS
    assert features.loc[0, "fractal_dir"] == -1
    assert features.loc[1, "fractal_strong"] == 1
    assert features.loc[2, "session_hour"] == 2
    assert features.loc[0, "atr"] == 1.0


def test_predict_surrogate_signal_uses_active_probability_threshold():
    probabilities = pd.DataFrame(
        {
            -1: [0.10, 0.40, 0.20],
            0: [0.80, 0.20, 0.55],
            1: [0.10, 0.40, 0.25],
        }
    )

    out = surrogate.predict_surrogate_signal(probabilities, threshold=0.50)

    assert out["surrogate_signal"].tolist() == [0, 1, 0]
    assert np.allclose(out["active_probability"], [0.20, 0.80, 0.45])


def test_surrogate_metrics_reports_active_precision_and_direction_accuracy():
    truth = pd.Series([1, -1, 0, 1])
    pred = pd.Series([1, 0, -1, -1])

    metrics = surrogate.surrogate_classification_metrics(truth, pred)

    assert metrics["active_precision"] == 2 / 3
    assert metrics["active_recall"] == 2 / 3
    assert metrics["direction_accuracy_on_true_active"] == 1 / 3


def test_cli_writes_summary_for_synthetic_surrogate(tmp_path, monkeypatch, capsys):
    source = _source_frame()
    pred = pd.DataFrame(
        {
            "time": source["time"],
            "signal": source["signal"],
            "pred_ret_24_dir_atr": [0.9, 0.8, -0.2],
        }
    )
    ohlc = tmp_path / "ohlc.csv"
    ohlc.write_text(
        "time;open;high;low;close;volume\n"
        "2024.01.01 00:00;100;101;99;100;1\n"
        "2024.01.01 01:00;100;105;99;104;1\n"
        "2024.01.01 02:00;104;106;95;96;1\n"
        "2024.01.01 03:00;96;97;94;95;1\n",
        encoding="utf-8",
    )
    train_source = tmp_path / "train.csv"
    validation_source = tmp_path / "validation.csv"
    test_source = tmp_path / "test.csv"
    validation_predictions = tmp_path / "validation_pred.csv"
    test_predictions = tmp_path / "test_pred.csv"
    source.to_csv(train_source, sep=";", index=False)
    source.to_csv(validation_source, sep=";", index=False)
    source.to_csv(test_source, sep=";", index=False)
    pred.to_csv(validation_predictions, sep=";", index=False)
    pred.to_csv(test_predictions, sep=";", index=False)
    output_dir = tmp_path / "out"

    monkeypatch.setattr(
        surrogate,
        "parse_args",
        lambda: SimpleNamespace(
            train_source=train_source,
            validation_source=validation_source,
            test_source=test_source,
            validation_predictions=validation_predictions,
            test_predictions=test_predictions,
            ohlc=ohlc,
            output_dir=output_dir,
            probability_grid=[0.10, 0.50],
            score_threshold=-1.0,
            min_period_trades=1,
            sequential_hold_bars=2,
            horizon=2,
            random_state=7,
            n_estimators=10,
        ),
    )

    result = surrogate.main()
    printed = json.loads(capsys.readouterr().out)

    assert printed["summary_path"] == result["summary_path"]
    assert (output_dir / "summary.json").exists()
    assert (output_dir / "summary.md").exists()
    assert (output_dir / "test_selected_rows.csv").exists()
