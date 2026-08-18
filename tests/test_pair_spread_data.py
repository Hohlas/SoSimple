# tests/test_pair_spread_data.py
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_MODULE_PATH = Path(__file__).resolve().parents[1] / 'statistics' / 'pair_spread' / 'pair_data.py'
_spec = importlib.util.spec_from_file_location('pair_data', _MODULE_PATH)
pair_data = importlib.util.module_from_spec(_spec)
sys.modules['pair_data'] = pair_data
_spec.loader.exec_module(pair_data)


def _write_csv(path, rows):
    lines = ['time;open;high;low;close;volume']
    lines += rows
    path.write_text('\n'.join(lines) + '\n')


def test_load_ohlc_csv_parses_and_cleans(tmp_path):
    p = tmp_path / 'SYM_OHLC.csv'
    _write_csv(p, [
        '2020.01.01 00:00;1.0;1.1;0.9;1.05;100',
        '2020.01.01 00:00;1.0;1.1;0.9;1.06;100',   # дубль времени
        '2020.01.01 00:05;1.06;1.2;1.0;1.10;50',
        '2020.01.01 00:10;0.0;0.0;0.0;0.0;0',      # close <= 0
    ])
    df = pair_data.load_ohlc_csv(p)
    assert len(df) == 2
    assert df.index[0] == pd.Timestamp('2020-01-01 00:00')
    assert df.loc[pd.Timestamp('2020-01-01 00:00'), 'close'] == 1.06  # keep='last'
    assert list(df.columns) == ['open', 'high', 'low', 'close']


def test_resample_to_h1_ohlc(tmp_path):
    rows = []
    closes = [1.0, 1.1, 1.2, 1.15, 1.3, 1.25, 1.2, 1.22, 1.18, 1.19, 1.21, 1.20]
    for i, c in enumerate(closes):
        rows.append(f'2020.01.01 00:{i*5:02d};{c};{c+0.01};{c-0.01};{c};10')
    p = tmp_path / 'SYM_OHLC.csv'
    _write_csv(p, rows)
    h1 = pair_data.resample_to_h1(pair_data.load_ohlc_csv(p))
    assert len(h1) == 1
    bar = h1.iloc[0]
    assert bar['open'] == 1.0
    assert bar['close'] == 1.20
    assert bar['high'] == 1.3 + 0.01
    assert bar['low'] == 1.0 - 0.01


def test_build_log_spreads_beta():
    t = pd.date_range('2020-01-01', periods=3, freq='5min')
    a = pd.Series([2.0, 4.0, 8.0], index=t)
    b = pd.Series([1.0, 2.0, 4.0], index=t)
    s = pair_data.build_log_spreads(a, b, beta=1.0)
    assert np.allclose(s, np.log(2.0))
    # a = b^2: ln a - 2*ln b = 0 тождественно (исправлено по аудиту К-2.1)
    a2 = pd.Series([1.0, 4.0, 16.0], index=t)
    s2 = pair_data.build_log_spreads(a2, b, beta=2.0)
    assert np.allclose(s2, 0.0)


def test_build_log_spreads_inner_join():
    t1 = pd.date_range('2020-01-01', periods=3, freq='5min')
    t2 = t1[1:]
    a = pd.Series([2.0, 2.0, 2.0], index=t1)
    b = pd.Series([1.0, 1.0], index=t2)
    s = pair_data.build_log_spreads(a, b, beta=1.0)
    assert len(s) == 2
    assert s.index[0] == t1[1]


def test_split_constants():
    assert pair_data.TRAIN_END == pd.Timestamp('2022-12-31 23:59')
    assert pair_data.TEST_START == pd.Timestamp('2023-01-01 00:00')
