import pandas as pd

import processing.label_signals as ls


def test_label_trailing_stop_targets_adds_x2_x3_x5_columns():
    frame = pd.DataFrame(
        {
            'time': ['2025.01.01 00:00'],
            'signal': [1],
            'ATR': [10.0],
            'Close': [100.0],
            'High': [100.0],
            'Low': [100.0],
            'Close_1': [103.0],
            'High_1': [105.0],
            'Low_1': [99.0],
            'Close_2': [104.0],
            'High_2': [106.0],
            'Low_2': [102.0],
        }
    , index=[10])

    out = ls.label_trailing_stop_targets(frame.copy(), hold_bars=2, atr_col='ATR', x_values=(2, 3, 5))

    assert 'trail_48_pnl_atr_x2' in out.columns
    assert 'trail_48_pnl_atr_x3' in out.columns
    assert 'trail_48_pnl_atr_x5' in out.columns
    assert out.loc[10, 'trail_48_pnl_atr_x2'] == 0.4
    assert out.loc[10, 'trail_48_pnl_atr_x3'] == 0.4
    assert out.loc[10, 'trail_48_pnl_atr_x5'] == 0.4


def test_label_trailing_stop_targets_skips_nan_signal_and_atr():
    frame = pd.DataFrame(
        {
            'time': ['2025.01.01 00:00', '2025.01.01 01:00'],
            'signal': [1, float('nan')],
            'ATR': [10.0, float('nan')],
            'Close': [100.0, 100.0],
            'High': [100.0, 100.0],
            'Low': [100.0, 100.0],
            'Close_1': [103.0, 101.0],
            'High_1': [105.0, 101.0],
            'Low_1': [99.0, 99.0],
            'Close_2': [104.0, 101.0],
            'High_2': [106.0, 101.0],
            'Low_2': [102.0, 99.0],
        },
        index=[10, 20],
    )

    out = ls.label_trailing_stop_targets(frame.copy(), hold_bars=2, atr_col='ATR', x_values=(2,))

    assert out.loc[10, 'trail_48_pnl_atr_x2'] == 0.4
    assert out.loc[20, 'trail_48_pnl_atr_x2'] == 0.0


def test_simulate_trailing_stop_exit_buy_closes_on_retrace_from_best_high():
    bars = [
        {'high': 105.0, 'low': 100.0, 'close': 104.0},
        {'high': 112.0, 'low': 103.0, 'close': 111.0},
        {'high': 110.0, 'low': 105.0, 'close': 102.0},
    ]

    pnl_atr = ls.simulate_trailing_stop_exit(
        bars=bars,
        direction=1,
        entry_price=100.0,
        atr=2.0,
        trail_atr=3.0,
    )

    assert pnl_atr == 3.0


def test_simulate_trailing_stop_exit_buy_stops_on_same_bar_retrace_after_new_high():
    bars = [
        {'high': 103.0, 'low': 100.0, 'close': 102.0},
    ]

    pnl_atr = ls.simulate_trailing_stop_exit(
        bars=bars,
        direction=1,
        entry_price=100.0,
        atr=1.0,
        trail_atr=2.0,
    )

    assert pnl_atr == 1.0


def test_simulate_trailing_stop_exit_sell_stops_on_same_bar_retrace_after_new_low():
    bars = [
        {'high': 100.0, 'low': 97.0, 'close': 98.0},
    ]

    pnl_atr = ls.simulate_trailing_stop_exit(
        bars=bars,
        direction=-1,
        entry_price=100.0,
        atr=1.0,
        trail_atr=2.0,
    )

    assert pnl_atr == 1.0
