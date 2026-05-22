import pandas as pd

from ML.entry_path_direct_direction_targets import build_buy_sell_fav_adv
from ML.entry_path_direct_direction_targets import build_target_a_classes
from ML.entry_path_direct_direction_targets import build_target_c_classes
from ML.entry_path_direct_direction_targets import build_target_d_classes
from ML.entry_path_direct_direction_targets import target_pair_to_class


def test_buy_and_sell_fav_adv_are_built_independently_in_atr_units():
    frame = pd.DataFrame({"ATR": [2.0], "up_6": [0.6], "dn_6": [0.2]})

    moves = build_buy_sell_fav_adv(frame, horizons=(6,))

    assert moves.loc[0, "buy_fav_6_atr"] == 0.3
    assert moves.loc[0, "buy_adv_6_atr"] == 0.1
    assert moves.loc[0, "sell_fav_6_atr"] == 0.1
    assert moves.loc[0, "sell_adv_6_atr"] == 0.3


def test_buy_sell_fav_adv_rejects_non_positive_atr_for_atr_targets():
    frame = pd.DataFrame({"ATR": [2.0], "up_6": [0.6], "dn_6": [0.2]})

    moves = build_buy_sell_fav_adv(frame, horizons=(6,))

    assert moves.loc[0, "buy_fav_6_atr"] == 0.3
    bad = build_buy_sell_fav_adv(pd.DataFrame({"ATR": [0.0], "up_6": [0.6], "dn_6": [0.2]}), horizons=(6,))
    assert bad.loc[0, "buy_fav_6_atr"] == 0.0


def test_target_pair_to_class_skips_ambiguous_rows():
    out = target_pair_to_class(
        buy_good=pd.Series([True, False, True, False]),
        sell_good=pd.Series([False, True, True, False]),
    )

    assert out.tolist() == [1, -1, 0, 0]


def test_target_a_and_c_build_sell_skip_buy_classes():
    moves = pd.DataFrame(
        {
            "buy_fav_6_atr": [2.5, 0.5, 2.5],
            "buy_adv_6_atr": [0.5, 3.0, 0.5],
            "sell_fav_6_atr": [0.5, 2.5, 2.5],
            "sell_adv_6_atr": [2.5, 0.5, 0.5],
            "buy_fav_24_atr": [4.5, 0.5, 4.5],
            "buy_adv_12_atr": [1.0, 3.0, 1.0],
            "sell_fav_24_atr": [0.5, 4.5, 4.5],
            "sell_adv_12_atr": [3.0, 1.0, 1.0],
        }
    )

    assert build_target_a_classes(moves, stop_n=2.0, take_y=2.0).tolist() == [1, -1, 0]
    assert build_target_c_classes(moves, take_x=4.0, adverse_y=2.0).tolist() == [1, -1, 0]


def test_target_d_computes_buy_sell_independently_and_conservatively(tmp_path):
    source = pd.DataFrame(
        {
            "time": ["2024.01.01 00:00", "2024.01.01 03:00", "2024.01.01 06:00"],
            "ATR": [1.0, 1.0, 1.0],
        }
    )
    ohlc_path = tmp_path / "ohlc.csv"
    pd.DataFrame(
        {
            "time": [
                "2024.01.01 00:00",
                "2024.01.01 01:00",
                "2024.01.01 02:00",
                "2024.01.01 03:00",
                "2024.01.01 04:00",
                "2024.01.01 05:00",
                "2024.01.01 06:00",
                "2024.01.01 07:00",
                "2024.01.01 08:00",
            ],
            "open": [100.0, 100.0, 103.0, 100.0, 100.0, 97.0, 100.0, 100.0, 100.0],
            "high": [100.0, 103.0, 103.0, 100.0, 100.0, 98.0, 100.0, 103.0, 103.0],
            "low": [100.0, 100.0, 101.0, 100.0, 97.0, 97.0, 100.0, 99.0, 99.0],
            "close": [100.0] * 9,
            "volume": [1] * 9,
        }
    ).to_csv(ohlc_path, sep=";", index=False)

    target = build_target_d_classes(source, ohlc_path, trail_n=1.0, profit_z=1.0, horizon=2)

    assert target.tolist() == [1, -1, 0]
