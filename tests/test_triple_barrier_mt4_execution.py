import sys
import json
from pathlib import Path

import pandas as pd

sys.path.insert(0, '.')

from ML import benchmark_triple_barrier_mt4_execution as bench
from ML import triple_barrier_mt4_execution as tb_exec


def _market_frame() -> pd.DataFrame:
    # Label convention (float): 1.0=TP, 0.0=SL, 0.5=Timeout.
    return pd.DataFrame(
        {
            'time': pd.to_datetime([
                '2024-01-01 00:00',
                '2024-01-01 01:00',
                '2024-01-01 02:00',
                '2024-01-01 03:00',
                '2024-01-01 04:00',
                '2024-01-01 05:00',
            ]),
            'buy_sl3_tp3': [1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
            'sell_sl3_tp3': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        }
    )


def test_signal_opens_on_next_bar_not_signal_bar():
    signals = pd.DataFrame(
        {
            'time': pd.to_datetime(['2024-01-01 00:00']),
            'signal': [1],
            'sl_atr': [3.0],
            'tp_atr': [3.0],
        }
    )

    trades, _meta = tb_exec.simulate_mt4_tb(signals, _market_frame(), hold_bars=3)

    assert len(trades) == 1
    assert trades.iloc[0]['signal_time'] == pd.Timestamp('2024-01-01 00:00')
    assert trades.iloc[0]['entry_time'] == pd.Timestamp('2024-01-01 01:00')


def test_same_direction_signal_is_skipped_while_position_open():
    signals = pd.DataFrame(
        {
            'time': pd.to_datetime(['2024-01-01 00:00', '2024-01-01 01:00']),
            'signal': [1, 1],
            'sl_atr': [3.0, 3.0],
            'tp_atr': [3.0, 3.0],
        }
    )

    trades, meta = tb_exec.simulate_mt4_tb(signals, _market_frame(), hold_bars=3)

    assert len(trades) == 1
    assert meta['posblock_skips'] == 1


def test_timeout_closes_position_after_hold_window():
    market = _market_frame().copy()
    market['buy_sl3_tp3'] = [0.5, 0.5, 0.5, 0.5, 0.5, 0.5]
    signals = pd.DataFrame(
        {
            'time': pd.to_datetime(['2024-01-01 00:00']),
            'signal': [1],
            'sl_atr': [3.0],
            'tp_atr': [3.0],
        }
    )

    trades, _meta = tb_exec.simulate_mt4_tb(signals, market, hold_bars=3, timeout_pnl_atr=0.5)

    assert trades.iloc[0]['close_reason'] == 'HoldOverTime'
    assert trades.iloc[0]['exit_time'] == pd.Timestamp('2024-01-01 03:00')
    assert trades.iloc[0]['pnl_atr'] == 0.5


def test_opposite_signal_closes_current_position_with_reversal_reason():
    market = _market_frame().copy()
    market['buy_sl3_tp3'] = [0.5, 0.5, 0.5, 0.5, 0.5, 0.5]
    signals = pd.DataFrame(
        {
            'time': pd.to_datetime(['2024-01-01 00:00', '2024-01-01 01:00']),
            'signal': [1, -1],
            'sl_atr': [3.0, 3.0],
            'tp_atr': [3.0, 3.0],
        }
    )

    trades, meta = tb_exec.simulate_mt4_tb(signals, market, hold_bars=4)

    assert trades.iloc[0]['close_reason'] == 'TB_Reversal'
    assert trades.iloc[0]['exit_time'] == pd.Timestamp('2024-01-01 01:00')
    assert meta['reversals'] == 1
    assert len(trades) == 2


def test_target_name_uses_path_ordered_tb_label_not_close_only_return():
    market = _market_frame().copy()
    market['buy_sl3_tp3'] = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    signals = pd.DataFrame(
        {
            'time': pd.to_datetime(['2024-01-01 00:00']),
            'signal': [1],
            'sl_atr': [3.0],
            'tp_atr': [3.0],
        }
    )

    trades, _meta = tb_exec.simulate_mt4_tb(signals, market, hold_bars=3)

    assert trades.iloc[0]['source_target'] == 'buy_sl3_tp3'
    assert trades.iloc[0]['close_reason'] == 'SL'
    assert trades.iloc[0]['pnl_atr'] == -3.0


def test_benchmark_cli_writes_trades_yearly_and_summary(tmp_path):
    signals = pd.DataFrame(
        {
            'time': ['2024.01.01 00:00'],
            'signal': [1],
            'sl_atr': [3.0],
            'tp_atr': [3.0],
            'prob': [0.7],
            'ev': [0.2],
        }
    )
    labeled = pd.DataFrame(
        {
            'time': ['2024.01.01 00:00', '2024.01.01 01:00', '2024.01.01 02:00', '2024.01.01 03:00'],
            'signal': [1, 0, 0, 0],
            'buy_sl3_tp3': [1.0, 1.0, 1.0, 1.0],
            'sell_sl3_tp3': [0.0, 0.0, 0.0, 0.0],
        }
    )
    rule = {'theta': 0.475, 'min_ev': 0.1}

    signals_path = tmp_path / 'ml_signals_tb.csv'
    labeled_path = tmp_path / 'Nero_test_labeled.csv'
    rule_path = tmp_path / 'tb_selected_rule.json'
    output_trades = tmp_path / 'trades.csv'
    output_yearly = tmp_path / 'yearly.csv'
    output_summary = tmp_path / 'summary.json'

    signals.to_csv(signals_path, sep=';', index=False)
    labeled.to_csv(labeled_path, sep=';', index=False)
    rule_path.write_text(json.dumps(rule), encoding='utf-8')

    payload = bench.run_benchmark(
        signals_path=signals_path,
        labeled_path=labeled_path,
        rule_json=rule_path,
        output_trades=output_trades,
        output_summary=output_summary,
        output_yearly=output_yearly,
    )

    assert payload['trades'] == 1
    assert output_trades.exists()
    assert output_yearly.exists()
    assert output_summary.exists()
