from pathlib import Path
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from processing.rebuild_xauusd_top_level_updn import refresh_top_level_columns


def test_refresh_top_level_columns_changes_only_top_level_fields():
    frame = pd.DataFrame(
        {
            "time": ["2021.01.01 10:00"],
            "signal": [1],
            "ATR": [1.0],
            "fractal0": [
                "1609488000:100.0:-1:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:1.0:0"
            ],
            "up_3": [0.0],
            "dn_3": [0.0],
            "up_6": [0.0],
            "dn_6": [0.0],
            "up_12": [0.0],
            "dn_12": [0.0],
            "up_24": [0.0],
            "dn_24": [0.0],
            "up_48": [0.0],
            "dn_48": [0.0],
        }
    )
    params = np.array([[[10.0, 20.0]] * 5], dtype=np.float64)
    ohlc = pd.DataFrame(
        {
            "time": pd.to_datetime(
                [
                    "2021.01.01 08:00",
                    "2021.01.01 09:00",
                    "2021.01.01 10:00",
                    "2021.01.01 11:00",
                    "2021.01.01 12:00",
                    "2021.01.01 13:00",
                    "2021.01.01 14:00",
                    "2021.01.01 15:00",
                    "2021.01.01 16:00",
                    "2021.01.01 17:00",
                    "2021.01.01 18:00",
                    "2021.01.01 19:00",
                    "2021.01.01 20:00",
                    "2021.01.01 21:00",
                    "2021.01.01 22:00",
                    "2021.01.01 23:00",
                    "2021.01.02 00:00",
                    "2021.01.02 01:00",
                    "2021.01.02 02:00",
                    "2021.01.02 03:00",
                    "2021.01.02 04:00",
                    "2021.01.02 05:00",
                    "2021.01.02 06:00",
                    "2021.01.02 07:00",
                    "2021.01.02 08:00",
                    "2021.01.02 09:00",
                    "2021.01.02 10:00",
                    "2021.01.02 11:00",
                    "2021.01.02 12:00",
                    "2021.01.02 13:00",
                    "2021.01.02 14:00",
                    "2021.01.02 15:00",
                    "2021.01.02 16:00",
                    "2021.01.02 17:00",
                    "2021.01.02 18:00",
                    "2021.01.02 19:00",
                    "2021.01.02 20:00",
                    "2021.01.02 21:00",
                    "2021.01.02 22:00",
                    "2021.01.02 23:00",
                    "2021.01.03 00:00",
                    "2021.01.03 01:00",
                    "2021.01.03 02:00",
                    "2021.01.03 03:00",
                    "2021.01.03 04:00",
                    "2021.01.03 05:00",
                    "2021.01.03 06:00",
                    "2021.01.03 07:00",
                    "2021.01.03 08:00",
                    "2021.01.03 09:00",
                    "2021.01.03 10:00",
                ]
            ),
            "high": np.linspace(100.0, 149.0, 51),
            "low": np.linspace(99.0, 90.0, 51),
        }
    )

    rebuilt = refresh_top_level_columns(frame, params, ohlc)

    changed_columns = [col for col in frame.columns if not frame[col].equals(rebuilt[col])]
    assert changed_columns == [
        "up_3",
        "dn_3",
        "up_6",
        "dn_6",
        "up_12",
        "dn_12",
        "up_24",
        "dn_24",
        "up_48",
        "dn_48",
    ]
    assert rebuilt.loc[0, "signal"] == frame.loc[0, "signal"]
    assert rebuilt.loc[0, "ATR"] == frame.loc[0, "ATR"]
    assert rebuilt.loc[0, "fractal0"] == frame.loc[0, "fractal0"]
