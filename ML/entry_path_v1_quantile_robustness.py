import json
from pathlib import Path

import numpy as np
import pandas as pd

from ML.entry_path_trade_filter import compute_pf


RESULT_JSON_NAME = 'transformer_entry_path_v1_quantile_result.json'
RULE_JSON_NAME = 'entry_path_v1_quantile_filter_selected_rule.json'
TEST_CSV_NAME = 'entry_path_v1_quantile_test_predictions.csv'


def _seed_from_dir(seed_dir: str | Path) -> int:
    name = Path(seed_dir).name
    if name.startswith('seed_'):
        return int(name.split('_', 1)[1])
    raise ValueError(f'Cannot parse seed from directory name: {name}')


def _load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding='utf-8'))


def _resolve_result_json(seed_path: Path) -> Path:
    direct = seed_path / RESULT_JSON_NAME
    if direct.exists():
        return direct

    parts = list(seed_path.parts)
    if 'reports' in parts:
        idx = parts.index('reports')
        checkpoint_parts = parts[:]
        checkpoint_parts[idx] = 'checkpoints'
        candidate = Path(*checkpoint_parts) / RESULT_JSON_NAME
        if candidate.exists():
            return candidate

    raise FileNotFoundError(f'Result JSON not found for seed dir: {seed_path}')


def load_prediction_frame(path: str | Path) -> pd.DataFrame:
    frame = pd.read_csv(Path(path), sep=';')
    frame['time'] = pd.to_datetime(frame['time'], format='%Y.%m.%d %H:%M', errors='coerce')
    return frame


def load_seed_run(seed_dir: str | Path) -> dict[str, object]:
    seed_path = Path(seed_dir)
    result = _load_json(_resolve_result_json(seed_path))
    rule = _load_json(seed_path / RULE_JSON_NAME)

    winner = rule['winner']
    frozen = rule['frozen_winner']
    sequential = rule.get('sequential_summary', {})

    return {
        'seed': _seed_from_dir(seed_path),
        'seed_dir': str(seed_path),
        'winner_candidate': winner.get('candidate'),
        'winner_rule': winner.get('rule'),
        'best_val_score': float(
            result.get('best_val_score', result.get('val_metrics', {}).get('val_score', 0.0))
        ),
        'validation_pf': float(winner.get('pf', 0.0)),
        'validation_trades': int(winner.get('trades', 0)),
        'test_pf': float(frozen.get('pf', 0.0)),
        'test_trades': int(frozen.get('trades', 0)),
        'test_win_rate': float(frozen.get('win_rate', 0.0)),
        'test_mean_pnl_atr': float(frozen.get('mean_pnl_atr', 0.0)),
        'sequential_pf': float(sequential.get('pf', 0.0)),
        'sequential_trades': int(sequential.get('trades', 0)),
        'sequential_win_rate': float(sequential.get('win_rate', 0.0)),
        'sequential_mean_pnl_atr': float(sequential.get('mean_pnl_atr', 0.0)),
    }


def _load_selected_test_trades(seed_dir: str | Path) -> pd.DataFrame:
    seed_path = Path(seed_dir)
    frame = load_prediction_frame(seed_path / TEST_CSV_NAME)
    rule = _load_json(seed_path / RULE_JSON_NAME)

    correction = float(rule.get('correction', 0.0))
    baseline_threshold = float(rule.get('baseline_threshold', 0.0))
    winner = rule.get('winner', {})
    rule_name = winner.get('rule', 'baseline')
    m = float(winner.get('m', 0.0))
    w = float(winner.get('w', 0.0))

    frame = frame.loc[frame['signal'] != 0].copy()
    frame['baseline_selected'] = frame['pred_ret_24_dir_atr'].to_numpy(dtype=np.float64) >= baseline_threshold
    frame['lb'] = np.minimum(frame['pred_ret_24_q10'], frame['pred_ret_24_q90']) - correction
    frame['ub'] = np.maximum(frame['pred_ret_24_q10'], frame['pred_ret_24_q90']) + correction
    frame['width'] = frame['ub'] - frame['lb']

    if rule_name == 'baseline':
        selected_mask = frame['baseline_selected']
    elif rule_name == 'lb_gt_0':
        selected_mask = frame['baseline_selected'] & (frame['lb'] > 0.0)
    elif rule_name == 'lb_gt_m':
        selected_mask = frame['baseline_selected'] & (frame['lb'] > m)
    elif rule_name == 'lb_gt_m_width_le_w':
        selected_mask = frame['baseline_selected'] & (frame['lb'] > m) & (frame['width'] <= w)
    else:
        raise ValueError(f'Unknown quantile rule: {rule_name}')

    return frame.loc[selected_mask].copy()


def build_yearly_summary(seed_dir: str | Path, min_trades: int = 5) -> pd.DataFrame:
    seed_path = Path(seed_dir)
    frame = _load_selected_test_trades(seed_path)
    if frame.empty:
        return pd.DataFrame(columns=['seed', 'period', 'trades', 'net_pnl_atr', 'pf', 'win_rate', 'mean_pnl_atr'])

    frame['period'] = frame['time'].dt.year.astype('Int64').astype(str)
    rows = []
    seed = _seed_from_dir(seed_path)
    for period, group in frame.groupby('period', dropna=True):
        pnl = group['true_ret_24_dir_atr'].to_numpy(dtype=np.float64)
        rows.append({
            'seed': seed,
            'period': str(period),
            'trades': int(len(group)),
            'net_pnl_atr': float(pnl.sum()),
            'pf': float(compute_pf(pnl)),
            'win_rate': float((pnl > 0).mean()) if len(pnl) > 0 else 0.0,
            'mean_pnl_atr': float(pnl.mean()) if len(pnl) > 0 else 0.0,
            'eligible': bool(len(group) >= min_trades),
        })
    return pd.DataFrame(rows)


def build_rolling_summary(seed_dir: str | Path, window_size: int = 10, step_size: int = 5) -> pd.DataFrame:
    seed_path = Path(seed_dir)
    frame = _load_selected_test_trades(seed_path).sort_values('time').reset_index(drop=True)
    if frame.empty:
        return pd.DataFrame(columns=['seed', 'window_index', 'start_time', 'end_time', 'trades', 'net_pnl_atr', 'pf'])

    rows = []
    seed = _seed_from_dir(seed_path)
    window_index = 0
    for start in range(0, len(frame), step_size):
        chunk = frame.iloc[start:start + window_size].copy()
        if chunk.empty or len(chunk) < window_size:
            continue
        pnl = chunk['true_ret_24_dir_atr'].to_numpy(dtype=np.float64)
        rows.append({
            'seed': seed,
            'window_index': window_index,
            'start_time': chunk.iloc[0]['time'],
            'end_time': chunk.iloc[-1]['time'],
            'trades': int(len(chunk)),
            'net_pnl_atr': float(pnl.sum()),
            'pf': float(compute_pf(pnl)),
            'win_rate': float((pnl > 0).mean()) if len(pnl) > 0 else 0.0,
            'mean_pnl_atr': float(pnl.mean()) if len(pnl) > 0 else 0.0,
        })
        window_index += 1
        if start + window_size >= len(frame):
            break
    return pd.DataFrame(rows)


def summarize_seed_matrix(seed_rows: list[dict[str, object]]) -> pd.DataFrame:
    return pd.DataFrame(seed_rows).sort_values('seed').reset_index(drop=True)


def build_verdict(
    runs: pd.DataFrame,
    yearly: pd.DataFrame,
    baseline_test_pf: float,
    baseline_sequential_pf: float,
) -> dict[str, object]:
    if runs.empty:
        return {
            'seed_count': 0,
            'same_rule_count': 0,
            'median_test_pf': 0.0,
            'median_sequential_pf': 0.0,
            'worst_seed_test_trades': 0,
            'negative_year_slices': 0,
            'verdict': 'reject_quantile_upgrade',
        }

    dominant_count = int(runs['winner_candidate'].value_counts().max())
    median_test_pf = float(runs['test_pf'].median())
    median_sequential_pf = float(runs['sequential_pf'].median())
    worst_seed_test_trades = int(runs['test_trades'].min())
    negative_year_slices = int(
        yearly.loc[(yearly['trades'] >= 5) & (yearly['net_pnl_atr'] < 0)].shape[0]
    ) if not yearly.empty else 0

    if (
        dominant_count >= 4
        and median_test_pf > baseline_test_pf
        and median_sequential_pf >= baseline_sequential_pf
        and worst_seed_test_trades >= 15
        and negative_year_slices == 0
    ):
        verdict = 'go_mt4'
    elif median_test_pf < baseline_test_pf or dominant_count <= max(1, len(runs) // 2):
        verdict = 'reject_quantile_upgrade'
    else:
        verdict = 'needs_more_research'

    return {
        'seed_count': int(len(runs)),
        'same_rule_count': dominant_count,
        'median_test_pf': median_test_pf,
        'median_sequential_pf': median_sequential_pf,
        'worst_seed_test_trades': worst_seed_test_trades,
        'negative_year_slices': negative_year_slices,
        'verdict': verdict,
    }
