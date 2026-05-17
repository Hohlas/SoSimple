import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

sys.path.insert(0, ".")

from ML import benchmark_entry_path_all_rows_ranking as all_rows


def _write_ohlc(path: Path) -> None:
    path.write_text(
        "time;open;high;low;close;volume\n"
        "2024.01.01 00:00;100;101;99;100;1\n"
        "2024.01.01 01:00;100;106;99;105;1\n"
        "2024.01.01 02:00;105;106;101;102;1\n"
        "2024.01.01 03:00;102;103;96;97;1\n"
        "2024.01.01 04:00;97;99;95;98;1\n",
        encoding="utf-8",
    )


def _prediction_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "time": ["2024.01.01 00:00", "2024.01.01 01:00", "2024.01.01 02:00"],
            "signal": [0, 1, 0],
            "pred_ret_24_dir_atr": [0.90, 0.20, 0.80],
        }
    )


def _source_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "time": ["2024.01.01 00:00", "2024.01.01 01:00", "2024.01.01 02:00"],
            "ATR": [1.0, 1.0, 1.0],
            "fractal0": [
                "1:100:-1:0",  # fractal dir -1 -> BUY
                "2:100:1:0",   # fractal dir 1 -> SELL
                "3:100:0:0",
            ],
        }
    )


def test_fractal0_direction_uses_existing_diagnostic_convention():
    signal = all_rows.direction_from_fractal0(pd.Series(["1:2:-1:4", "1:2:1:4", "bad", "1:2:0:4"]))

    assert signal.tolist() == [1, -1, 0, 0]


def test_build_all_rows_frame_recomputes_pnl_for_fractal0_direction(tmp_path):
    ohlc_path = tmp_path / "ohlc.csv"
    _write_ohlc(ohlc_path)

    frame = all_rows.build_all_rows_frame(
        predictions=_prediction_frame(),
        source=_source_frame(),
        ohlc_path=ohlc_path,
        horizon=2,
    )

    assert frame["all_rows_signal"].tolist() == [1, -1, 0]
    assert frame.loc[0, "all_rows_ret_24_dir_atr"] == 2.0
    assert frame.loc[1, "all_rows_ret_24_dir_atr"] == 8.0
    assert frame.loc[2, "all_rows_ret_24_dir_atr"] == 0.0


def test_evaluate_grid_selects_threshold_on_validation_and_checks_test(tmp_path):
    ohlc_path = tmp_path / "ohlc.csv"
    _write_ohlc(ohlc_path)
    validation = all_rows.build_all_rows_frame(
        predictions=_prediction_frame(),
        source=_source_frame(),
        ohlc_path=ohlc_path,
        horizon=2,
    )
    test = validation.copy()

    result = all_rows.run_grid_benchmark(
        validation=validation,
        test=test,
        coverage_grid=[0.5, 1.0],
        min_period_trades=1,
        sequential_hold_bars=2,
    )

    assert result["winner"]["target_coverage"] == 1.0
    assert result["winner"]["trades"] == 2
    assert result["test"]["trades"] == 2
    assert result["sequential"]["trades"] == 1


def test_cli_writes_all_rows_report(tmp_path, monkeypatch, capsys):
    ohlc_path = tmp_path / "ohlc.csv"
    _write_ohlc(ohlc_path)
    pred_path = tmp_path / "pred.csv"
    source_path = tmp_path / "source.csv"
    _prediction_frame().to_csv(pred_path, sep=";", index=False)
    _source_frame().to_csv(source_path, sep=";", index=False)
    output_dir = tmp_path / "out"

    monkeypatch.setattr(
        all_rows,
        "parse_args",
        lambda: SimpleNamespace(
            validation_predictions=pred_path,
            validation_source=source_path,
            test_predictions=pred_path,
            test_source=source_path,
            ohlc=ohlc_path,
            output_dir=output_dir,
            coverage_grid=[0.5, 1.0],
            min_period_trades=1,
            sequential_hold_bars=2,
            horizon=2,
        ),
    )

    result = all_rows.main()
    printed = json.loads(capsys.readouterr().out)

    assert printed["summary_path"] == result["summary_path"]
    assert (output_dir / "summary.json").exists()
    assert (output_dir / "summary.md").exists()
    assert (output_dir / "test_selected_rows.csv").exists()
