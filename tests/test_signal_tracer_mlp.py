# =============================================================================
# Файл: tests/test_signal_tracer_mlp.py
# Назначение: Unit-тесты MLP direct-mode parsing в statistics/signal_tracer.py
# =============================================================================

import sys
from pathlib import Path

sys.path.insert(0, 'statistics')
import signal_tracer as st


def test_parse_log_reads_mlp_timeout_trade(tmp_path):
    log_path = tmp_path / '20260411.log'
    log_path.write_text(
        "\n".join(
            [
                "0\t16:51:27.944\t2024.07.01 18:00:00  $o$imple XAUUSD,H1: 163856255:: MLP BUY signal_time=2024.07.01 17:00 entry_time=2024.07.01 18:00 score=0.000000 Val=2327.96",
                "0\t16:51:31.014\t2024.07.02 19:00:00  $o$imple XAUUSD,H1: 163856255:: MLP CLOSE BUY reason=Timeout signal_time=2024.07.01 17:00 entry_time=2024.07.01 18:00 exit_time=2024.07.02 19:00 hold_bars=24 entry=2327.96 exit=2322.86 atr=4.89 pnl_atr=-1.0420 score=0.000000",
            ]
        ),
        encoding='utf-8',
    )

    trades = st.parse_log(log_path)

    assert len(trades) == 1
    trade = trades[0]
    assert trade['track'] == 'mlp'
    assert trade['dir'] == 'BUY'
    assert trade['bar_time'] == '2024.07.01 17:00'
    assert trade['entry_time'] == '2024.07.01 18:00'
    assert trade['exit_time'] == '2024.07.02 19:00'
    assert trade['close_type'] == 'MARKET'
    assert trade['close_reason'] == 'Timeout'
    assert trade['val'] == 2327.96
    assert trade['close_price'] == 2322.86
    assert trade['atr_mt4'] == 4.89
    assert trade['mt4_pnl_atr'] == -1.042


def test_build_dossier_handles_mlp_market_trade():
    out = st.build_dossier(
        target_time='2024.07.01 17:00',
        signal_row={'time': '2024.07.01 17:00', 'signal': '1'},
        nero_cols=None,
        fractal={
            'fractal_time': st.time_str_to_unix('2024.07.01 17:00'),
            'fractal_atr': 4.89,
            'price': 2327.96,
        },
        params=st.ML_DEFAULTS,
        mt4_trade={
            'track': 'mlp',
            'dir': 'BUY',
            'bar_time': '2024.07.01 17:00',
            'entry_time': '2024.07.01 18:00',
            'exit_time': '2024.07.02 19:00',
            'hold_bars': 24,
            'val': 2327.96,
            'close_price': 2322.86,
            'atr_mt4': 4.89,
            'mt4_pnl_atr': -1.042,
            'close_type': 'MARKET',
            'close_reason': 'Timeout',
            'order_num': None,
        },
    )

    assert out['track'] == 'mlp'
    assert out['direction'] == 'BUY'
    assert out['close_reason'] == 'Timeout'
    assert out['entry_time'] == '2024.07.01 18:00'
    assert out['exit_time'] == '2024.07.02 19:00'
    assert out['mt4_result'] == 'LOSS(MKT)'
    assert out['mt4_pnl_atr'] == -1.042


def test_print_dossier_handles_mlp_track(capsys):
    st.print_dossier(
        {
            'time': '2024.07.01 17:00',
            'track': 'mlp',
            'signal': 1,
            'direction': 'BUY',
            'entry_time': '2024.07.01 18:00',
            'exit_time': '2024.07.02 19:00',
            'hold_bars': 24,
            'close_reason': 'Timeout',
            'val': 2327.96,
            'close_price': 2322.86,
            'atr_mt4': 4.89,
            'mt4_result': 'LOSS(MKT)',
            'mt4_pnl_atr': -1.042,
        },
        st.ML_DEFAULTS,
    )

    out = capsys.readouterr().out
    assert 'MLP Direct Mode' in out
    assert 'Timeout' in out
    assert 'LOSS(MKT)' in out
