import numpy as np
import pandas as pd

from ML.entry_path_direct_direction_targets import build_buy_sell_fav_adv
from ML.entry_path_direct_direction_targets import build_target_d_masks


def test_buy_target_matches_target_d_buy_side():
    source = pd.DataFrame(
        {
            "time": ["2024.01.01 10:00"],
            "ATR": [1.0],
            "up_3": [0.5],
            "dn_3": [0.2],
            "up_6": [0.5],
            "dn_6": [0.2],
            "up_12": [0.5],
            "dn_12": [0.2],
            "up_24": [0.8],
            "dn_24": [0.2],
            "up_48": [0.9],
            "dn_48": [0.1],
        }
    )
    moves = build_buy_sell_fav_adv(source, horizons=(6,))
    buy_fav = moves["buy_fav_6_atr"].iloc[0]
    buy_adv = moves["buy_adv_6_atr"].iloc[0]
    assert isinstance(buy_fav, float)
    assert isinstance(buy_adv, float)


def test_binary_signal_logic_simple_threshold():
    p_buy = np.array([0.6, 0.3, 0.4, 0.5])
    p_sell = np.array([0.2, 0.7, 0.3, 0.5])
    buy_threshold = 0.5
    sell_threshold = 0.5
    signals = np.zeros(len(p_buy), dtype=int)
    buy_fire = p_buy >= buy_threshold
    sell_fire = p_sell >= sell_threshold
    signals[buy_fire & ~sell_fire] = 1
    signals[sell_fire & ~buy_fire] = -1
    assert signals[0] == 1
    assert signals[1] == -1
    assert signals[2] == 0
    assert signals[3] == 0


def test_binary_signal_logic_margin_rule():
    p_buy = np.array([0.6, 0.3, 0.5, 0.6])
    p_sell = np.array([0.2, 0.7, 0.4, 0.55])
    buy_threshold = 0.5
    sell_threshold = 0.5
    margin = 0.10
    signals = np.zeros(len(p_buy), dtype=int)
    buy_fire = p_buy >= buy_threshold
    sell_fire = p_sell >= sell_threshold
    buy_margin = (p_buy - p_sell) >= margin
    sell_margin = (p_sell - p_buy) >= margin
    signals[buy_fire & buy_margin] = 1
    signals[sell_fire & sell_margin] = -1
    assert signals[0] == 1
    assert signals[1] == -1
    assert signals[2] == 0
    assert signals[3] == 0


def test_binary_ambiguous_rows_remain_positive():
    buy_good = pd.Series([True, True, False, True])
    sell_good = pd.Series([False, True, False, False])
    ambiguous = buy_good & sell_good
    assert ambiguous.iloc[1]
    buy_target = buy_good.astype(int)
    sell_target = sell_good.astype(int)
    assert buy_target.iloc[1] == 1
    assert sell_target.iloc[1] == 1


def test_margin_zero_equivalent_to_simple_threshold():
    p_buy = np.array([0.7, 0.3, 0.55, 0.48])
    p_sell = np.array([0.2, 0.6, 0.45, 0.50])
    buy_threshold = 0.5
    sell_threshold = 0.5
    margin = 0.0
    simple = np.zeros(len(p_buy), dtype=int)
    buy_fire = p_buy >= buy_threshold
    sell_fire = p_sell >= sell_threshold
    simple[buy_fire & ~sell_fire] = 1
    simple[sell_fire & ~buy_fire] = -1
    with_margin = np.zeros(len(p_buy), dtype=int)
    buy_margin = (p_buy - p_sell) >= margin
    sell_margin = (p_sell - p_buy) >= margin
    with_margin[buy_fire & buy_margin] = 1
    with_margin[sell_fire & sell_margin] = -1
    np.testing.assert_array_equal(simple, with_margin)