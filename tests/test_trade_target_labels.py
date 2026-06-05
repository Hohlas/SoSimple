import pandas as pd
import processing.label_signals as ls


def test_label_trade_targets_adds_directional_outcome_columns():
    frame = pd.DataFrame({
        'time': ['2025.01.01 00:00', '2025.01.01 01:00', '2025.01.01 02:00'],
        'signal': [1, -1, 0],
        'ATR': [10.0, 10.0, 10.0],
        'up_12': [20.0, 5.0, 7.0],
        'dn_12': [5.0, 20.0, 9.0],
        'up_24': [25.0, 6.0, 8.0],
        'dn_24': [7.0, 25.0, 10.0],
    })

    out = ls.label_trade_targets(frame.copy())

    assert 'trade_outcome_h12' in out.columns
    assert 'trade_pnl_h12_atr' in out.columns
    assert 'archetype_target' in out.columns

    assert out.loc[0, 'trade_outcome_h12'] == 1
    assert out.loc[0, 'trade_pnl_h12_atr'] == 1.5
    assert out.loc[0, 'archetype_target'] == 1

    assert out.loc[1, 'trade_outcome_h12'] == 1
    assert out.loc[1, 'trade_pnl_h12_atr'] == 1.5
    assert out.loc[1, 'archetype_target'] == 1

    assert out.loc[2, 'trade_outcome_h12'] == 0
    assert out.loc[2, 'trade_pnl_h12_atr'] == 0.0
    assert out.loc[2, 'archetype_target'] == 0


def test_label_trade_targets_marks_large_pullback_as_non_archetype():
    frame = pd.DataFrame({
        'time': ['2025.01.01 03:00'],
        'signal': [1],
        'ATR': [10.0],
        'up_12': [18.0],
        'dn_12': [12.0],
        'up_24': [22.0],
        'dn_24': [13.0],
    })

    out = ls.label_trade_targets(frame.copy())

    assert out.loc[0, 'trade_outcome_h12'] == 1
    assert out.loc[0, 'trade_pnl_h12_atr'] == 0.6
    assert out.loc[0, 'archetype_target'] == 0


def test_label_trade_targets_uses_ohlc_path_when_provided(tmp_path):
    frame = pd.DataFrame({
        'time': ['2025.01.01 00:00'],
        'signal': [1],
        'ATR': [99.0],
        'up_12': [1.0],
        'dn_12': [9.0],
        'up_24': [1.0],
        'dn_24': [9.0],
    })

    rows = []
    closes = [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 120]
    highs =  [100, 102, 103, 104, 105, 106, 107, 108, 125, 110, 111, 112, 121]
    lows =   [100,  99, 100, 101, 102, 103, 104, 105,  98, 107, 108, 109, 119]
    for idx in range(13):
        rows.append({
            'time': pd.Timestamp('2025-01-01 00:00') + pd.Timedelta(hours=idx),
            'open': closes[idx],
            'high': highs[idx],
            'low': lows[idx],
            'close': closes[idx],
            'volume': 1,
            'atr14': 10.0,
        })
    ohlc = pd.DataFrame(rows)
    ohlc_path = tmp_path / 'ohlc.csv'
    ohlc.to_csv(ohlc_path, sep=';', index=False, date_format='%Y.%m.%d %H:%M')

    out = ls.label_trade_targets(frame.copy(), ohlc_path=ohlc_path)

    assert out.loc[0, 'trade_fav_h12'] == 24.0
    assert out.loc[0, 'trade_adv_h12'] == 3.0
    assert out.loc[0, 'trade_pnl_h12_atr'] == 1.9
    assert out.loc[0, 'trade_outcome_h12'] == 1
    assert out.loc[0, 'archetype_target'] == 1
