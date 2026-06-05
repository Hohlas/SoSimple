import pandas as pd

import processing.label_signals as ls


def test_trailing_stop_default_grid_matches_design():
    assert ls.TRAILING_STOP_HORIZONS == (12, 24, 48)
    assert ls.TRAILING_STOP_X_VALUES == (2, 4, 8)


def test_label_trailing_stop_targets_adds_expanded_grid_columns():
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

    out = ls.label_trailing_stop_targets(frame.copy(), hold_bars=2, atr_col='ATR')

    expected = [
        'trail_12_pnl_atr_x2',
        'trail_12_pnl_atr_x4',
        'trail_12_pnl_atr_x8',
        'trail_24_pnl_atr_x2',
        'trail_24_pnl_atr_x4',
        'trail_24_pnl_atr_x8',
        'trail_48_pnl_atr_x2',
        'trail_48_pnl_atr_x4',
        'trail_48_pnl_atr_x8',
    ]
    assert [column for column in out.columns if column.startswith('trail_')] == expected
    for column in expected:
        assert out.loc[10, column] == 0.4


def test_label_trailing_stop_targets_uses_default_grid_when_x_values_omitted():
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
        },
        index=[10],
    )

    out = ls.label_trailing_stop_targets(frame.copy(), hold_bars=2, atr_col='ATR')

    expected = [
        'trail_12_pnl_atr_x2',
        'trail_12_pnl_atr_x4',
        'trail_12_pnl_atr_x8',
        'trail_24_pnl_atr_x2',
        'trail_24_pnl_atr_x4',
        'trail_24_pnl_atr_x8',
        'trail_48_pnl_atr_x2',
        'trail_48_pnl_atr_x4',
        'trail_48_pnl_atr_x8',
    ]
    assert [column for column in out.columns if column.startswith('trail_')] == expected


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

    assert out.loc[10, 'trail_12_pnl_atr_x2'] == 0.4
    assert out.loc[20, 'trail_12_pnl_atr_x2'] == 0.0


def test_label_trailing_stop_targets_uses_ohlc_lookup_when_close_columns_absent(monkeypatch):
    frame = pd.DataFrame(
        {
            'time': ['2025.01.01 00:00'],
            'signal': [1],
            'ATR': [1.0],
        }
    )

    def fake_load_ohlc_index(_path):
        ohlc = {
            't0': (99.0, 101.0, 98.0, 100.0),
            't1': (100.0, 103.0, 101.0, 102.0),
            't2': (102.0, 104.0, 101.0, 103.0),
        }
        times = ['t0', 't1', 't2']
        time_idx = {'2025-01-01T00:00:00+00:00': 0}
        return ohlc, times, time_idx

    class FakeDateTime:
        @staticmethod
        def strptime(value, _fmt):
            class _Parsed:
                def replace(self, tzinfo=None):
                    return '2025-01-01T00:00:00+00:00'
            return _Parsed()

    monkeypatch.setattr(ls, 'load_ohlc_index', fake_load_ohlc_index)
    monkeypatch.setattr('datetime.datetime', FakeDateTime)

    out = ls.label_trailing_stop_targets(
        frame.copy(),
        ohlc_path='unused.csv',
        hold_bars=2,
        atr_col='ATR',
        x_values=(2,),
    )

    assert out.loc[0, 'trail_12_pnl_atr_x2'] == 1.0


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
