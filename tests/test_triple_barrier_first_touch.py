# =============================================================================
# Файл: tests/test_triple_barrier_first_touch.py
# Назначение: Unit-тесты first-touch helper для Triple Barrier разметки
# Язык: Python 3.10+
# Использование:
#   ./.venv/bin/python -m pytest tests/test_triple_barrier_first_touch.py -q
# =============================================================================

import sys
from datetime import datetime, timezone

import pandas as pd

sys.path.insert(0, 'processing')
import label_signals as ls


def test_first_touch_prefers_sl_when_low_hits_before_high():
    bars = pd.DataFrame([
        {'open': 100.0, 'high': 101.0, 'low': 98.0, 'close': 99.0},
        {'open': 99.0, 'high': 104.0, 'low': 97.0, 'close': 103.0},
    ])

    out = ls.first_touch_barrier_outcome(
        bars=bars,
        direction=1,
        entry_price=100.0,
        sl_price=98.0,
        tp_price=104.0,
    )

    assert out == 0


def test_label_first_barrier_hit_uses_row_time_not_fractal_time(tmp_path):
    ohlc_path = tmp_path / "ohlc.csv"
    pd.DataFrame([
        {'time': '2023.01.01 00:00', 'open': 100.0, 'high': 100.0, 'low': 100.0, 'close': 100.0, 'volume': 1},
        {'time': '2023.01.01 01:00', 'open': 100.0, 'high': 103.5, 'low': 100.0, 'close': 103.0, 'volume': 1},
        {'time': '2023.01.01 02:00', 'open': 103.0, 'high': 103.2, 'low': 100.8, 'close': 101.0, 'volume': 1},
    ]).to_csv(ohlc_path, sep=';', index=False)

    fractal_time = int(datetime(2023, 1, 1, 0, 0, tzinfo=timezone.utc).timestamp())
    fractal0 = (
        f"{fractal_time}:100.0:1:0:0:0:0:0:0:0:0:"
        "0:0:0:0:0:0:0:0:0:0:1.0:0"
    )
    df = pd.DataFrame([{
        'time': '2023.01.01 01:00',
        'ATR': 1.0,
        'fractal0': fractal0,
    }])

    out = ls.label_first_barrier_hit(df, str(ohlc_path))

    assert out.at[0, 'buy_sl2_tp3'] == 0.0
