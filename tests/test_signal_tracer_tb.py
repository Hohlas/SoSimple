# =============================================================================
# Файл: tests/test_signal_tracer_tb.py
# Назначение: Unit-тесты TB-specific parsing в statistics/signal_tracer.py
# Язык: Python 3.11+
# Использование:
#   ./.venv/bin/python -m pytest tests/test_signal_tracer_tb.py -q
# =============================================================================

import os
import importlib.machinery

_proj_root = os.path.join(os.path.dirname(__file__), '..')
st = importlib.machinery.SourceFileLoader(
    'signal_tracer', os.path.join(_proj_root, 'statistics', 'signal_tracer.py')
).load_module()


def test_parse_tb_log_line_extracts_sl_tp_prob():
    line = "TB BUY prob=0.731 ev=3.42 SL=2.0ATR TP=6.0ATR bar=2025.01.03 04:00"

    out = st.parse_tb_signal_line(line)

    assert out['prob'] == 0.731
    assert out['sl_atr'] == 2.0
    assert out['tp_atr'] == 6.0


def test_parse_fractal0_reads_atr_from_23_field_format():
    fractal = (
        "1664470800:0.06476853043:-1:0.07949640602:0.1059952006:0:0:"
        "0.8500000238:0:0:0.8392652273:0:0:0:0:0:0:0:0:0:0:5.5:3"
    )

    out = st.parse_fractal0(fractal)

    assert out is not None
    assert out['fractal_time'] == 1664470800
    assert out['direction'] == -1
    assert out['fractal_atr'] == 5.5


def test_build_tb_dossier_exports_sl_pnl_in_atr_units():
    target_time = "2025.01.03 04:00"
    signal_row = {
        'time': target_time,
        'signal': '1',
        'sl_atr': '2.0',
        'tp_atr': '3.0',
        'prob': '0.7547',
        'ev': '1.7736',
    }
    fractal = {
        'fractal_time': st.time_str_to_unix(target_time),
        'fractal_atr': 5.0,
        'price': 1900.0,
    }
    mt4_trade = {
        'dir': 'BUY',
        'val': 100.0,
        'stp': 90.0,
        'prf': 115.0,
        'atr_mt4': 5.0,
        'close_type': 'SL',
        'close_price': None,
    }

    out = st.build_tb_dossier(target_time, signal_row, None, fractal, mt4_trade=mt4_trade)

    assert out['mt4_result'] == 'LOSS(SL)'
    assert out['mt4_pnl_pips'] == -10.0
    assert out['mt4_pnl_atr'] == -2.0


def test_build_tb_dossier_exports_market_pnl_in_atr_units():
    target_time = "2025.01.03 04:00"
    signal_row = {
        'time': target_time,
        'signal': '-1',
        'sl_atr': '2.0',
        'tp_atr': '3.0',
        'prob': '0.9032',
        'ev': '2.5161',
    }
    fractal = {
        'fractal_time': st.time_str_to_unix(target_time),
        'fractal_atr': 5.0,
        'price': 1900.0,
    }
    mt4_trade = {
        'dir': 'SELL',
        'val': 100.0,
        'stp': 110.0,
        'prf': 85.0,
        'atr_mt4': 5.0,
        'close_type': 'MARKET',
        'close_price': 92.5,
    }

    out = st.build_tb_dossier(target_time, signal_row, None, fractal, mt4_trade=mt4_trade)

    assert out['mt4_result'] == 'WIN(MKT)'
    assert out['mt4_pnl_pips'] == 7.5
    assert out['mt4_pnl_atr'] == 1.5


def test_time_str_to_unix_uses_utc():
    assert st.time_str_to_unix("1970.01.01 00:00") == 0
