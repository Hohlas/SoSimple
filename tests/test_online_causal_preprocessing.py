import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from processing.online_causal_preprocessing import preprocess_online_csv, preprocess_online_frame
from processing.online_causal_preprocessing import validate_fractal_sorting


def _fractal(ts: int, price: float, direction: int, front: float, back: float) -> str:
    values = [
        ts,
        price,
        direction,
        front,
        back,
        0,
        4,
        0,
        0,
        2,
        10,
        20,
        30,
        40,
        50,
        60,
        70,
        1.5,
        0,
        0,
        0,
        1.0,
    ]
    return ":".join(str(v) for v in values)


def _legacy_fractal(ts: int, price: float, direction: int, front: float, back: float) -> str:
    values = [
        ts,
        price,
        direction,
        front,
        back,
        0,
        0,
        0,
        1.0,
        1,
        0.5,
        10.0,
        8.0,
        15.0,
        12.0,
        20.0,
        16.0,
        2.5,
    ]
    return ":".join(str(v) for v in values)


def test_preprocess_online_frame_sorts_fractals_before_normalization():
    raw = pd.DataFrame(
        {
            "time": ["2026.04.29 03:55"],
            "signal": [0],
            "predict": [0],
            "ATR": [2.1],
            "fractal0": [_fractal(100, 4600.0, 1, 30, 40)],
            "fractal1": [_fractal(300, 4620.0, -1, 10, 20)],
            "fractal2": [_fractal(200, 4610.0, 1, 20, 30)],
        }
    )

    processed = preprocess_online_frame(raw)

    first_parts = str(processed.loc[0, "fractal0"]).split(":")
    assert first_parts[0] == "300"
    assert first_parts[2] == "-1"


def test_preprocess_online_frame_normalizes_price_but_preserves_online_targets():
    raw = pd.DataFrame(
        {
            "time": ["2026.04.29 03:55"],
            "signal": [0],
            "predict": [0],
            "ATR": [2.1],
            "fractal0": [_fractal(100, 4600.0, 1, 30, 40)],
            "fractal1": [_fractal(300, 4620.0, -1, 10, 20)],
            "fractal2": [_fractal(200, 4610.0, 1, 20, 30)],
        }
    )

    processed = preprocess_online_frame(raw)

    prices = [float(str(processed.loc[0, f"fractal{i}"]).split(":")[1]) for i in range(3)]
    assert prices == [1.0, 0.5, 0.0]
    assert processed.loc[0, "signal"] == 0
    assert processed.loc[0, "predict"] == 0


def test_preprocess_online_csv_writes_preprocessed_file(tmp_path):
    raw = pd.DataFrame(
        {
            "time": ["2026.04.29 03:55"],
            "signal": [0],
            "predict": [0],
            "ATR": [2.1],
            "fractal0": [_fractal(100, 4600.0, 1, 30, 40)],
            "fractal1": [_fractal(300, 4620.0, -1, 10, 20)],
        }
    )
    input_csv = tmp_path / "Nero.csv"
    output_csv = tmp_path / "runtime_input_preprocessed.csv"
    raw.to_csv(input_csv, sep=";", index=False)

    processed = preprocess_online_csv(input_csv=input_csv, output_csv=output_csv)

    assert output_csv.exists()
    reread = pd.read_csv(output_csv, sep=";")
    assert str(reread.loc[0, "fractal0"]).split(":")[0] == "300"
    assert list(processed.columns) == list(reread.columns)
    assert str(processed.loc[0, "fractal1"]) == str(reread.loc[0, "fractal1"])


def test_validate_fractal_sorting_rejects_unsorted_frame():
    raw = pd.DataFrame(
        {
            "fractal0": [_fractal(100, 4600.0, 1, 30, 40)],
            "fractal1": [_fractal(300, 4620.0, -1, 10, 20)],
        }
    )

    with pytest.raises(ValueError, match="fractal sorting validation failed"):
        validate_fractal_sorting(raw)


def test_validate_fractal_sorting_allows_equal_timestamps():
    raw = pd.DataFrame(
        {
            "fractal0": [_fractal(300, 4600.0, 1, 30, 40)],
            "fractal1": [_fractal(300, 4620.0, -1, 10, 20)],
        }
    )

    assert validate_fractal_sorting(raw) == {"checked_rows": 1, "error_rows": 0}


def test_preprocess_online_frame_handles_empty_dataframe():
    raw = pd.DataFrame(columns=["time", "signal", "predict", "ATR", "fractal0", "fractal1"])

    processed = preprocess_online_frame(raw)

    assert processed.empty
    assert list(processed.columns) == list(raw.columns)


def test_preprocess_online_frame_supports_legacy_18_field_fractals():
    raw = pd.DataFrame(
        {
            "time": ["2026.04.29 03:55"],
            "signal": [0],
            "predict": [0],
            "ATR": [2.1],
            "fractal0": [_legacy_fractal(100, 4600.0, 1, 30, 40)],
            "fractal1": [_legacy_fractal(300, 4620.0, -1, 10, 20)],
        }
    )

    processed = preprocess_online_frame(raw)

    parts = str(processed.loc[0, "fractal0"]).split(":")
    assert parts[0] == "300"
    assert len(parts) == 22


def test_preprocess_online_frame_is_idempotent_for_sorted_normalized_input():
    raw = pd.DataFrame(
        {
            "time": ["2026.04.29 03:55"],
            "signal": [0],
            "predict": [0],
            "ATR": [2.1],
            "fractal0": [_fractal(300, 4620.0, -1, 10, 20)],
            "fractal1": [_fractal(200, 4610.0, 1, 20, 30)],
            "fractal2": [_fractal(100, 4600.0, 1, 30, 40)],
        }
    )

    once = preprocess_online_frame(raw)
    twice = preprocess_online_frame(once)

    assert twice.equals(once)


def test_preprocess_online_frame_is_quiet_by_default(capsys):
    raw = pd.DataFrame(
        {
            "time": ["2026.04.29 03:55"],
            "signal": [0],
            "predict": [0],
            "ATR": [2.1],
            "fractal0": [_fractal(100, 4600.0, 1, 30, 40)],
            "fractal1": [_fractal(300, 4620.0, -1, 10, 20)],
        }
    )

    preprocess_online_frame(raw)

    captured = capsys.readouterr()
    assert captured.out == ""
