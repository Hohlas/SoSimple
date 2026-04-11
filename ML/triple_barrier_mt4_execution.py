import json
from pathlib import Path

import numpy as np
import pandas as pd

from ML.entry_path_trade_filter import compute_pf


def build_target_name(signal: int, sl_atr: float, tp_atr: float) -> str:
    side = 'buy' if int(signal) > 0 else 'sell'
    return f'{side}_sl{int(round(float(sl_atr)))}_tp{int(round(float(tp_atr)))}'


def load_tb_signals(path: str | Path, theta: float = 0.0, min_ev: float = 0.0) -> pd.DataFrame:
    frame = pd.read_csv(Path(path), sep=';')
    frame['time'] = pd.to_datetime(frame['time'], format='%Y.%m.%d %H:%M', errors='coerce')
    frame = frame.loc[frame['signal'] != 0].copy()
    if 'prob' in frame.columns:
        frame = frame.loc[frame['prob'].astype(float) >= float(theta)].copy()
    if 'ev' in frame.columns:
        frame = frame.loc[frame['ev'].astype(float) >= float(min_ev)].copy()
    return frame.sort_values('time').reset_index(drop=True)


def load_labeled_frame(path: str | Path) -> pd.DataFrame:
    frame = pd.read_csv(Path(path), sep=';', low_memory=False)
    frame['time'] = pd.to_datetime(frame['time'], format='%Y.%m.%d %H:%M', errors='coerce')
    return frame.sort_values('time').reset_index(drop=True)


def _close_trade(position: dict, exit_time, close_reason: str, pnl_atr: float) -> dict[str, object]:
    return {
        'signal_time': position['signal_time'],
        'entry_time': position['entry_time'],
        'exit_time': exit_time,
        'direction': position['direction'],
        'close_reason': close_reason,
        'pnl_atr': float(pnl_atr),
        'source_target': position['source_target'],
    }


def simulate_mt4_tb(
    signals: pd.DataFrame,
    labeled: pd.DataFrame,
    hold_bars: int = 24,
    timeout_pnl_atr: float = 0.5,
) -> tuple[pd.DataFrame, dict[str, object]]:
    market = labeled.sort_values('time').reset_index(drop=True).copy()
    market_index = {ts: idx for idx, ts in enumerate(market['time'])}
    signals = signals.sort_values('time').reset_index(drop=True).copy()

    trades = []
    meta = {
        'trades': 0,
        'wins': 0,
        'losses': 0,
        'timeouts': 0,
        'reversals': 0,
        'posblock_skips': 0,
    }

    open_position = None
    for row in signals.itertuples(index=False):
        signal_time = row.time
        signal = int(row.signal)
        signal_idx = market_index.get(signal_time)
        if signal_idx is None:
            continue

        if open_position is not None and signal_idx >= open_position['close_index']:
            source_row = market.iloc[open_position['signal_idx']]
            outcome = int(source_row.get(open_position['source_target'], 0))
            exit_time = market.iloc[min(open_position['close_index'], len(market) - 1)]['time']
            if outcome > 0:
                trades.append(_close_trade(open_position, exit_time, 'TP', open_position['tp_atr']))
                meta['wins'] += 1
            elif outcome < 0:
                trades.append(_close_trade(open_position, exit_time, 'SL', -open_position['sl_atr']))
                meta['losses'] += 1
            else:
                trades.append(_close_trade(open_position, exit_time, 'HoldOverTime', timeout_pnl_atr))
                meta['timeouts'] += 1
                meta['wins'] += int(timeout_pnl_atr > 0)
                meta['losses'] += int(timeout_pnl_atr < 0)
            open_position = None

        if open_position is not None:
            if open_position['direction'] == signal:
                meta['posblock_skips'] += 1
                continue
            trades.append(_close_trade(open_position, signal_time, 'TB_Reversal', 0.0))
            meta['reversals'] += 1
            open_position = None

        entry_idx = signal_idx + 1
        if entry_idx >= len(market):
            continue

        open_position = {
            'signal_idx': signal_idx,
            'signal_time': signal_time,
            'entry_time': market.iloc[entry_idx]['time'],
            'direction': signal,
            'sl_atr': float(row.sl_atr),
            'tp_atr': float(row.tp_atr),
            'source_target': build_target_name(signal, row.sl_atr, row.tp_atr),
            'close_index': min(signal_idx + hold_bars, len(market) - 1),
        }

    if open_position is not None:
        source_row = market.iloc[open_position['signal_idx']]
        outcome = int(source_row.get(open_position['source_target'], 0))
        exit_time = market.iloc[min(open_position['close_index'], len(market) - 1)]['time']
        if outcome > 0:
            trades.append(_close_trade(open_position, exit_time, 'TP', open_position['tp_atr']))
            meta['wins'] += 1
        elif outcome < 0:
            trades.append(_close_trade(open_position, exit_time, 'SL', -open_position['sl_atr']))
            meta['losses'] += 1
        else:
            trades.append(_close_trade(open_position, exit_time, 'HoldOverTime', timeout_pnl_atr))
            meta['timeouts'] += 1
            meta['wins'] += int(timeout_pnl_atr > 0)
            meta['losses'] += int(timeout_pnl_atr < 0)

    trades_frame = pd.DataFrame(trades)
    pnl = trades_frame['pnl_atr'].to_numpy(dtype=np.float64) if not trades_frame.empty else np.array([], dtype=np.float64)
    meta['trades'] = int(len(trades_frame))
    meta['pf'] = float(compute_pf(pnl))
    meta['win_rate'] = float((pnl > 0).mean()) if len(pnl) > 0 else 0.0
    return trades_frame, meta


def build_yearly_summary(trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame(columns=['year', 'trades', 'pf', 'net_pnl_atr', 'win_rate'])

    frame = trades.copy()
    frame['year'] = pd.to_datetime(frame['entry_time']).dt.year.astype(str)
    rows = []
    for year, group in frame.groupby('year'):
        pnl = group['pnl_atr'].to_numpy(dtype=np.float64)
        rows.append({
            'year': str(year),
            'trades': int(len(group)),
            'pf': float(compute_pf(pnl)),
            'net_pnl_atr': float(pnl.sum()),
            'win_rate': float((pnl > 0).mean()) if len(pnl) > 0 else 0.0,
        })
    return pd.DataFrame(rows)
