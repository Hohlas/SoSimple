# =============================================================================
# Файл: API/exit_policy_research.py
# Назначение: offline research CLI для сравнения ML-политик выхода и
#             position management без переобучения модели, поверх уже
#             сгенерированных `ml_signals.csv`
# Язык: Python 3.11+
# Создан: 2026-04-08
# Зависимости:
#   Входные данные:
#     - MT/MQL4/Files/ml_signals.csv
#     - DATA/XAUUSD_H1_OHLC.csv
#     - DATA/Nero_validation_labeled.csv
#     - DATA/Nero_test_labeled.csv
#   Выходные данные:
#     - stdout ranking table
#     - optional frozen policy JSON (`--save-best`)
# Использование:
#   python -m API.exit_policy_research --split-profile validation_research
#   python -m API.exit_policy_research --split-profile validation_research --save-best ML/reports/frozen_exit_policy.json
#   python -m API.exit_policy_research --split-profile test_final --policy ML/reports/frozen_exit_policy.json
# =============================================================================

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

try:
    from . import signal_research as sr
except ImportError:
    import signal_research as sr

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SIGNALS_FILE = PROJECT_ROOT / 'MT' / 'MQL4' / 'Files' / 'ml_signals.csv'
OHLC_FILE = PROJECT_ROOT / 'DATA' / 'XAUUSD_H1_OHLC.csv'
VALIDATION_FILE = PROJECT_ROOT / 'DATA' / 'Nero_validation_labeled.csv'
TEST_FILE = PROJECT_ROOT / 'DATA' / 'Nero_test_labeled.csv'

REVERSE_RATIOS = [2.0, 2.2, 2.5]
KEEP_RATIOS = [1.4, 1.6, 1.8]
MIN_HOLD_BARS = [1, 2, 3]
PROFIT_START_ATRS = [0.5, 1.0, 1.5]


def simulate_trade_exit(trade_frame: pd.DataFrame, policy: dict) -> dict:
    entry_signal = int(trade_frame['signal'].iloc[0])
    min_hold_bars = int(policy.get('min_hold_bars', 0))
    keep_ratio_min = policy.get('keep_ratio_min')
    profit_start_atr = policy.get('profit_start_atr')
    peak_fav_atr = float('-inf')

    for row in trade_frame.itertuples(index=False):
        same_ratio = row.ratio_up if entry_signal == 1 else row.ratio_dn
        opposite_ratio = row.ratio_dn if entry_signal == 1 else row.ratio_up
        peak_fav_atr = max(peak_fav_atr, float(getattr(row, 'fav_atr', row.net_atr)))

        if opposite_ratio >= policy.get('reverse_ratio', float('inf')):
            return {'exit_bar': int(row.bar), 'reason': 'reverse_ratio'}
        if row.bar < min_hold_bars or keep_ratio_min is None or same_ratio >= keep_ratio_min:
            continue
        if profit_start_atr is not None:
            if peak_fav_atr >= profit_start_atr:
                return {'exit_bar': int(row.bar), 'reason': 'profit_guard'}
            continue
        return {'exit_bar': int(row.bar), 'reason': 'weak_edge'}

    return {
        'exit_bar': int(trade_frame['bar'].iloc[-1]),
        'reason': 'timeout',
    }


def rank_policies(table: pd.DataFrame, min_trades: int = 50) -> pd.DataFrame:
    out = table[table['trades'] >= min_trades].copy()
    out = out.sort_values(['pf', 'trades'], ascending=[False, False]).reset_index(drop=True)
    return out


def build_policy_library() -> list[dict]:
    policies = [{'name': 'timeout_only'}]

    for reverse_ratio in REVERSE_RATIOS:
        policies.append({
            'name': f'reverse_close_r{reverse_ratio:.1f}',
            'reverse_ratio': reverse_ratio,
        })

    for keep_ratio_min in KEEP_RATIOS:
        for min_hold_bars in MIN_HOLD_BARS:
            policies.append({
                'name': f'weak_edge_k{keep_ratio_min:.1f}_h{min_hold_bars}',
                'keep_ratio_min': keep_ratio_min,
                'min_hold_bars': min_hold_bars,
            })

    for profit_start_atr in PROFIT_START_ATRS:
        for keep_ratio_min in KEEP_RATIOS:
            for min_hold_bars in MIN_HOLD_BARS:
                policies.append({
                    'name': f'profit_guard_p{profit_start_atr:.1f}_k{keep_ratio_min:.1f}_h{min_hold_bars}',
                    'profit_start_atr': profit_start_atr,
                    'keep_ratio_min': keep_ratio_min,
                    'min_hold_bars': min_hold_bars,
                })

    for reverse_ratio in REVERSE_RATIOS[:2]:
        for keep_ratio_min in KEEP_RATIOS[1:]:
            for profit_start_atr in PROFIT_START_ATRS[1:]:
                policies.append({
                    'name': (
                        f'layered_r{reverse_ratio:.1f}_k{keep_ratio_min:.1f}'
                        f'_p{profit_start_atr:.1f}_h2'
                    ),
                    'reverse_ratio': reverse_ratio,
                    'keep_ratio_min': keep_ratio_min,
                    'profit_start_atr': profit_start_atr,
                    'min_hold_bars': 2,
                })

    return policies


def render_mql_thresholds(policy: dict) -> dict:
    return {
        'ML_ExitReverseRatio': float(policy.get('reverse_ratio', 0.0)),
        'ML_ExitKeepRatio': float(policy.get('keep_ratio_min', 0.0)),
        'ML_ExitProfitATR': float(policy.get('profit_start_atr', 0.0)),
        'ML_ExitMinHoldBars': int(policy.get('min_hold_bars', 0)),
    }


def load_split_times(csv_path: Path) -> pd.DatetimeIndex:
    frame = pd.read_csv(csv_path, sep=';', usecols=['time'], parse_dates=['time'])
    return pd.DatetimeIndex(frame['time'].dropna().drop_duplicates().sort_values())


def filter_frame_to_split(
    frame: pd.DataFrame,
    split_profile: str,
    validation_file: Path = VALIDATION_FILE,
    test_file: Path = TEST_FILE,
) -> pd.DataFrame:
    if split_profile == 'validation_research':
        split_times = load_split_times(validation_file)
    elif split_profile == 'test_final':
        split_times = load_split_times(test_file)
    else:
        raise ValueError(f'Unknown split profile: {split_profile}')

    out = frame.copy()
    out['time'] = pd.to_datetime(out['time'])
    out = out[out['time'].isin(split_times)].copy()
    return out.sort_values('time').reset_index(drop=True)


def build_trade_frame(frame: pd.DataFrame, entry_idx: int, max_hold_bars: int = 12) -> pd.DataFrame:
    entry = frame.iloc[entry_idx]
    entry_signal = int(entry['signal'])
    entry_close = float(entry['close'])
    entry_atr = float(entry.get('atr14', 0.0)) or 1.0
    max_idx = min(entry_idx + max_hold_bars, len(frame) - 1)

    peak_high = entry_close
    trough_low = entry_close
    rows = []

    for idx in range(entry_idx, max_idx + 1):
        row = frame.iloc[idx]
        peak_high = max(peak_high, float(row['high']))
        trough_low = min(trough_low, float(row['low']))

        if idx == entry_idx:
            net_atr = 0.0
            fav_atr = 0.0
        elif entry_signal == 1:
            net_atr = (float(row['close']) - entry_close) / entry_atr
            fav_atr = (peak_high - entry_close) / entry_atr
        else:
            net_atr = (entry_close - float(row['close'])) / entry_atr
            fav_atr = (entry_close - trough_low) / entry_atr

        rows.append({
            'bar': idx - entry_idx,
            'time': row['time'],
            'signal': entry_signal,
            'ratio_up': float(row['ratio_up']),
            'ratio_dn': float(row['ratio_dn']),
            'net_atr': net_atr,
            'fav_atr': fav_atr,
        })

    return pd.DataFrame(rows)


def build_trade_frame_cache(frame: pd.DataFrame, max_hold_bars: int = 12) -> dict[int, pd.DataFrame]:
    signal_rows = frame.index[frame['signal'] != 0].tolist()
    return {idx: build_trade_frame(frame, idx, max_hold_bars=max_hold_bars) for idx in signal_rows}


def simulate_policy(
    frame: pd.DataFrame,
    policy: dict,
    max_hold_bars: int = 12,
    trade_frame_cache: dict[int, pd.DataFrame] | None = None,
) -> pd.DataFrame:
    ordered = frame.sort_values('time').reset_index(drop=True)
    trades = []
    idx = 0

    while idx < len(ordered):
        entry_signal = int(ordered.loc[idx, 'signal'])
        if entry_signal == 0:
            idx += 1
            continue

        if trade_frame_cache is None:
            trade_frame = build_trade_frame(ordered, idx, max_hold_bars=max_hold_bars)
        else:
            trade_frame = trade_frame_cache[idx]
        exit_info = simulate_trade_exit(trade_frame, policy)
        exit_bar = min(int(exit_info['exit_bar']), len(trade_frame) - 1)
        exit_idx = idx + exit_bar
        exit_row = trade_frame.iloc[exit_bar]

        blocked_signals = 0
        if exit_idx > idx:
            blocked_signals = int((ordered.loc[idx + 1:exit_idx, 'signal'] != 0).sum())

        trades.append({
            'entry_time': ordered.loc[idx, 'time'],
            'exit_time': ordered.loc[exit_idx, 'time'],
            'entry_signal': entry_signal,
            'exit_bar': exit_bar,
            'reason': exit_info['reason'],
            'pnl_atr': float(exit_row['net_atr']),
            'blocked_signals': blocked_signals,
        })

        if exit_info['reason'] == 'reverse_ratio' and int(ordered.loc[exit_idx, 'signal']) == -entry_signal:
            idx = exit_idx
            continue
        idx = exit_idx + 1

    return pd.DataFrame(trades)


def _profit_factor(pnl_atr: pd.Series) -> float:
    wins = pnl_atr[pnl_atr > 0].sum()
    losses = pnl_atr[pnl_atr < 0].abs().sum()
    if losses == 0:
        return float('inf') if wins > 0 else float('nan')
    if wins == 0:
        return 0.0
    return float(wins / losses)


def summarize_policy_result(trades: pd.DataFrame, policy: dict) -> dict:
    if trades.empty:
        return {
            'policy': policy['name'],
            'trades': 0,
            'pf': float('nan'),
            'win_rate': float('nan'),
            'avg_hold_bars': float('nan'),
            'avg_blocked_signals': float('nan'),
            'net_atr': 0.0,
        }

    pnl = pd.to_numeric(trades['pnl_atr'], errors='coerce').fillna(0.0)
    holds = pd.to_numeric(trades['exit_bar'], errors='coerce')
    blocked = pd.to_numeric(trades.get('blocked_signals', pd.Series(0, index=trades.index)), errors='coerce')

    return {
        'policy': policy['name'],
        'trades': int(len(trades)),
        'pf': _profit_factor(pnl),
        'win_rate': float((pnl > 0).mean() * 100.0),
        'avg_hold_bars': float(holds.mean()),
        'avg_blocked_signals': float(blocked.mean()),
        'net_atr': float(pnl.sum()),
    }


def load_policy_file(policy_path: Path) -> dict:
    payload = json.loads(Path(policy_path).read_text(encoding='utf-8'))
    return payload.get('policy', payload)


def resolve_policy_candidates(split_profile: str, policy_path: Path | None) -> list[dict]:
    if policy_path is not None:
        return [load_policy_file(policy_path)]
    if split_profile == 'test_final':
        raise ValueError('test_final requires a frozen policy JSON')
    return build_policy_library()


def load_market_frame(
    split_profile: str,
    signals_file: Path = SIGNALS_FILE,
    ohlc_file: Path = OHLC_FILE,
    validation_file: Path = VALIDATION_FILE,
    test_file: Path = TEST_FILE,
) -> pd.DataFrame:
    signals = pd.read_csv(signals_file, sep=';', parse_dates=['time'], low_memory=False)
    ohlc = pd.read_csv(ohlc_file, sep=';', parse_dates=['time'], low_memory=False)
    ohlc = ohlc.sort_values('time').drop_duplicates(subset='time', keep='last').reset_index(drop=True)

    atr_fallback = sr.compute_atr14(ohlc)
    if 'atr14' in ohlc.columns:
        ohlc['atr14'] = pd.to_numeric(ohlc['atr14'], errors='coerce').fillna(atr_fallback)
    else:
        ohlc['atr14'] = atr_fallback

    frame = signals.merge(
        ohlc[['time', 'open', 'high', 'low', 'close', 'atr14']],
        on='time',
        how='inner',
    )
    frame = frame.sort_values('time').drop_duplicates(subset='time', keep='last').reset_index(drop=True)
    frame = filter_frame_to_split(
        frame,
        split_profile=split_profile,
        validation_file=validation_file,
        test_file=test_file,
    )
    frame['ratio_up'] = pd.to_numeric(frame['up_12'], errors='coerce') / pd.to_numeric(frame['dn_12'], errors='coerce').clip(lower=1e-6)
    frame['ratio_dn'] = pd.to_numeric(frame['dn_12'], errors='coerce') / pd.to_numeric(frame['up_12'], errors='coerce').clip(lower=1e-6)
    return frame


def evaluate_policies(
    frame: pd.DataFrame,
    policies: list[dict],
    min_trades: int = 80,
    max_hold_bars: int = 12,
    apply_trade_floor: bool = True,
) -> pd.DataFrame:
    ordered = frame.sort_values('time').reset_index(drop=True)
    trade_frame_cache = build_trade_frame_cache(ordered, max_hold_bars=max_hold_bars)
    rows = []
    for policy in policies:
        trades = simulate_policy(
            ordered,
            policy,
            max_hold_bars=max_hold_bars,
            trade_frame_cache=trade_frame_cache,
        )
        rows.append(summarize_policy_result(trades, policy))

    table = pd.DataFrame(rows)
    if table.empty:
        return table
    if apply_trade_floor:
        return rank_policies(table, min_trades=min_trades)
    return table.sort_values(['pf', 'trades'], ascending=[False, False]).reset_index(drop=True)


def save_best_policy(path: Path, policy: dict, summary: dict, split_profile: str) -> None:
    payload = {
        'saved_at': pd.Timestamp.now(tz='UTC').isoformat(),
        'split_profile': split_profile,
        'policy': policy,
        'summary': summary,
        'mql_inputs': render_mql_thresholds(policy),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding='utf-8')


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Offline research for ML-guided exit and position management.'
    )
    parser.add_argument(
        '--split-profile',
        choices=['validation_research', 'test_final'],
        default='validation_research',
    )
    parser.add_argument('--min-trades', type=int, default=80)
    parser.add_argument('--max-hold-bars', type=int, default=12)
    parser.add_argument('--save-best', type=Path, default=None)
    parser.add_argument('--policy', type=Path, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    frame = load_market_frame(split_profile=args.split_profile)
    policies = resolve_policy_candidates(args.split_profile, args.policy)
    table = evaluate_policies(
        frame,
        policies,
        min_trades=args.min_trades,
        max_hold_bars=args.max_hold_bars,
        apply_trade_floor=args.policy is None and args.split_profile == 'validation_research',
    )

    if table.empty:
        print('No policies passed the requested support floor.')
        return

    display_cols = ['policy', 'trades', 'pf', 'win_rate', 'avg_hold_bars', 'avg_blocked_signals', 'net_atr']
    print(table[display_cols].to_string(index=False))

    if args.save_best is not None:
        best_row = table.iloc[0].to_dict()
        best_policy = next(policy for policy in policies if policy['name'] == best_row['policy'])
        save_best_policy(args.save_best, best_policy, best_row, split_profile=args.split_profile)
        print(f'\nSaved best policy to {args.save_best}')


if __name__ == '__main__':
    main()
