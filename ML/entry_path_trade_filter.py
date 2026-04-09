import json

import numpy as np
import pandas as pd


CANDIDATE_B_WEIGHTS = {
    'ret24': 0.45,
    'ret12': 0.20,
    'edge12': 0.15,
    'edge24': 0.10,
    'path6': 0.10,
}


def build_candidate_a_score(frame: pd.DataFrame) -> np.ndarray:
    return frame['pred_ret_24_dir_atr'].to_numpy(dtype=np.float64)


def build_candidate_b_components(frame: pd.DataFrame, include_path6: bool = True) -> pd.DataFrame:
    components = {
        'ret24': frame['pred_ret_24_dir_atr'].to_numpy(dtype=np.float64),
        'ret12': frame['pred_ret_12_dir_atr'].to_numpy(dtype=np.float64),
        'edge12': (
            frame['pred_fav_12_atr'].to_numpy(dtype=np.float64)
            - frame['pred_adv_12_atr'].to_numpy(dtype=np.float64)
        ),
        'edge24': (
            frame['pred_fav_24_atr'].to_numpy(dtype=np.float64)
            - frame['pred_adv_24_atr'].to_numpy(dtype=np.float64)
        ),
    }
    if include_path6:
        components['path6'] = (
            frame['pred_path_6_prob_pos'].to_numpy(dtype=np.float64)
            - frame['pred_path_6_prob_neg'].to_numpy(dtype=np.float64)
        )
    return pd.DataFrame(components, index=frame.index)


def fit_percentile_rank(values: np.ndarray) -> np.ndarray:
    sorted_values = np.sort(np.asarray(values, dtype=np.float64))
    return sorted_values


def apply_percentile_rank(values: np.ndarray, fit: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=np.float64)
    sorted_values = np.asarray(fit, dtype=np.float64)
    if sorted_values.size == 0:
        return np.zeros(values.shape, dtype=np.float64)
    ranks = np.searchsorted(sorted_values, values, side='right') / sorted_values.size
    return ranks.astype(np.float64, copy=False)


def compose_candidate_b_score(normalized: pd.DataFrame, include_path6: bool = True) -> np.ndarray:
    weights = {
        column: weight
        for column, weight in CANDIDATE_B_WEIGHTS.items()
        if include_path6 or column != 'path6'
    }
    total_weight = float(sum(weights.values()))
    score = np.zeros(len(normalized), dtype=np.float64)
    for column, weight in weights.items():
        score += normalized[column].to_numpy(dtype=np.float64) * weight
    return score / total_weight if total_weight > 0 else score


def fit_candidate_b_score(frame: pd.DataFrame, include_path6: bool = True) -> dict[str, np.ndarray]:
    components = build_candidate_b_components(frame, include_path6=include_path6)
    return {column: fit_percentile_rank(components[column].to_numpy(dtype=np.float64)) for column in components.columns}


def apply_candidate_b_score(
    frame: pd.DataFrame,
    scaler: dict[str, np.ndarray],
    include_path6: bool = True,
) -> np.ndarray:
    components = build_candidate_b_components(frame, include_path6=include_path6)
    normalized = pd.DataFrame({
        column: apply_percentile_rank(components[column].to_numpy(dtype=np.float64), scaler[column])
        for column in components.columns
    }, index=components.index)
    return compose_candidate_b_score(normalized, include_path6=include_path6)


def compute_pf(values) -> float:
    pnl = np.asarray(values, dtype=np.float64)
    gross_profit = float(pnl[pnl > 0].sum())
    gross_loss = float(-pnl[pnl < 0].sum())
    if gross_loss > 0:
        return gross_profit / gross_loss
    if gross_profit > 0:
        return float('inf')
    return 0.0


def _attach_period_column(frame: pd.DataFrame, min_period_trades: int):
    out = frame.copy()
    if out.empty:
        out['period'] = pd.Series(dtype='object')
        return out, 'half_year'

    year_period = pd.Series(pd.NA, index=out.index, dtype='object')
    valid_time = out['time'].notna()
    year_period.loc[valid_time] = out.loc[valid_time, 'time'].dt.year.astype('Int64').astype(str)
    eligible_years = int((year_period.dropna().value_counts() >= min_period_trades).sum())
    if eligible_years >= 2:
        out['period'] = year_period
        return out, 'year'

    half_year = pd.Series(pd.NA, index=out.index, dtype='object')
    valid_time = out['time'].notna()
    half_year.loc[valid_time] = (
        out.loc[valid_time, 'time'].dt.year.astype('Int64').astype(str)
        + 'H'
        + np.where(
            out.loc[valid_time, 'time'].dt.month.to_numpy() <= 6,
            '1',
            '2',
        )
    )
    out['period'] = half_year
    return out, 'half_year'


def _score_active_rows(frame: pd.DataFrame, score) -> pd.DataFrame:
    active_mask = frame['signal'].to_numpy() != 0
    active = frame.loc[active_mask].copy()
    if isinstance(score, pd.Series):
        if len(score) == len(frame) and frame.index.isin(score.index).all() and score.index.isin(frame.index).all():
            active['score'] = score.reindex(frame.index).to_numpy(dtype=np.float64)[active_mask]
        elif len(score) == len(active) and active.index.isin(score.index).all() and score.index.isin(active.index).all():
            active['score'] = score.reindex(active.index).to_numpy(dtype=np.float64)
        else:
            missing_active = active.index.difference(score.index)
            missing_frame = frame.index.difference(score.index)
            raise ValueError(
                'Series score is missing required indices for active rows or full frame alignment. '
                f'missing_active={list(missing_active)}, missing_frame={list(missing_frame)}'
            )
    else:
        score = np.asarray(score, dtype=np.float64)
        if score.size == len(active):
            active['score'] = score
        elif score.size == len(frame):
            active['score'] = score[active_mask]
        else:
            raise ValueError(
                f'Unexpected score length: got {score.size}, expected {len(active)} active rows or {len(frame)} full rows.'
            )
    return active


def _evaluate_threshold_slice(
    frame: pd.DataFrame,
    score,
    candidate: str,
    target_coverage: float,
    threshold: float,
    min_period_trades: int,
) -> pd.Series:
    active = _score_active_rows(frame, score)
    if active.empty:
        selected = active
    else:
        selected = active.loc[active['score'] >= threshold].copy()

    pnl = selected['true_ret_24_dir_atr'].to_numpy(dtype=np.float64)
    trades = int(len(selected))
    coverage = float(trades / len(active)) if len(active) > 0 else 0.0
    coverage_gap = float(abs(coverage - target_coverage))
    pf = compute_pf(pnl)
    win_rate = float((pnl > 0).mean()) if trades > 0 else 0.0
    mean_pnl_atr = float(pnl.mean()) if trades > 0 else 0.0

    period_mode = 'half_year'
    eligible_periods = 0
    stable_periods = 0
    worst_period_pf = np.nan
    period_detail = {}

    if trades > 0:
        perioded, period_mode = _attach_period_column(selected, min_period_trades)
        eligible_pfs = []
        for period_key, group in perioded.groupby('period', dropna=True):
            period_pnl = group['true_ret_24_dir_atr'].to_numpy(dtype=np.float64)
            period_pf = compute_pf(period_pnl)
            period_detail[str(period_key)] = {
                'trades': int(len(group)),
                'pf': period_pf,
                'mean_pnl': float(period_pnl.mean()),
            }
            if len(group) >= min_period_trades:
                eligible_periods += 1
                stable_periods += int(period_pf >= 1.0)
                eligible_pfs.append(period_pf)
        if eligible_pfs:
            worst_period_pf = float(min(eligible_pfs))

    stability_ratio = float(stable_periods / eligible_periods) if eligible_periods > 0 else 0.0
    return pd.Series({
        'candidate': candidate,
        'target_coverage': float(target_coverage),
        'coverage': coverage,
        'coverage_gap': coverage_gap,
        'score_threshold': float(threshold),
        'trades': trades,
        'pf': pf,
        'win_rate': win_rate,
        'mean_pnl_atr': mean_pnl_atr,
        'period_mode': period_mode,
        'eligible_periods': int(eligible_periods),
        'stable_periods': int(stable_periods),
        'stability_ratio': stability_ratio,
        'worst_period_pf': worst_period_pf,
        'period_detail_json': json.dumps(period_detail, ensure_ascii=False, sort_keys=True),
    })


def evaluate_score_grid(
    frame: pd.DataFrame,
    score,
    candidate: str,
    target_coverages,
    min_period_trades: int = 10,
) -> pd.DataFrame:
    active = _score_active_rows(frame, score)
    rows = []
    for target_coverage in target_coverages:
        threshold = float(
            active['score'].quantile(1.0 - target_coverage, interpolation='midpoint')
        ) if not active.empty else float('nan')
        rows.append(
            _evaluate_threshold_slice(
                frame=frame,
                score=score,
                candidate=candidate,
                target_coverage=float(target_coverage),
                threshold=threshold,
                min_period_trades=min_period_trades,
            )
        )
    return pd.DataFrame(rows)


def evaluate_frozen_threshold(
    frame: pd.DataFrame,
    score,
    candidate: str,
    threshold: float,
    target_coverage: float,
    min_period_trades: int = 10,
) -> pd.DataFrame:
    return pd.DataFrame([
        _evaluate_threshold_slice(
            frame=frame,
            score=score,
            candidate=candidate,
            target_coverage=float(target_coverage),
            threshold=float(threshold),
            min_period_trades=min_period_trades,
        )
    ])


def pick_best_slice(table: pd.DataFrame) -> pd.Series:
    if table.empty:
        raise ValueError('No slices to rank.')
    eligible_periods = table['eligible_periods'] if 'eligible_periods' in table.columns else pd.Series(0, index=table.index)
    workable_mask = (table['trades'] >= 30) & (eligible_periods >= 1)
    ranking_pool = table.loc[workable_mask].copy() if workable_mask.any() else table
    return ranking_pool.sort_values(
        ['pf', 'stability_ratio', 'coverage_gap', 'trades'],
        ascending=[False, False, True, False],
    ).iloc[0]


def run_sequential_check(frame: pd.DataFrame, selected_mask, hold_bars: int = 24) -> dict[str, object]:
    active_mask = frame['signal'].to_numpy() != 0
    active = frame.loc[active_mask].copy()
    active_positions = np.flatnonzero(active_mask)
    if isinstance(selected_mask, pd.Series):
        if len(selected_mask) == len(frame) and frame.index.is_unique and selected_mask.index.is_unique and frame.index.isin(selected_mask.index).all() and selected_mask.index.isin(frame.index).all():
            selected_active = selected_mask.reindex(frame.index).to_numpy(dtype=bool)[active_mask]
        elif len(selected_mask) == len(active) and active.index.is_unique and selected_mask.index.is_unique and active.index.isin(selected_mask.index).all() and selected_mask.index.isin(active.index).all():
            selected_active = selected_mask.reindex(active.index).to_numpy(dtype=bool)
        else:
            if len(selected_mask) == len(frame) and (not frame.index.is_unique or not selected_mask.index.is_unique):
                raise ValueError(
                    'selected_mask Series alignment to frame.index requires unique indices on both Series and frame.'
                )
            if len(selected_mask) == len(active) and (not active.index.is_unique or not selected_mask.index.is_unique):
                raise ValueError(
                    'selected_mask Series alignment to active.index requires unique indices on both Series and active rows.'
                )
            raise ValueError(
                'selected_mask Series is missing required indices for active rows or full frame alignment. '
                f'missing_active={list(active.index.difference(selected_mask.index))}, '
                f'missing_frame={list(frame.index.difference(selected_mask.index))}'
            )
    else:
        mask_array = np.asarray(selected_mask, dtype=bool)
        if len(mask_array) == len(frame):
            selected_active = mask_array[active_mask]
        elif len(mask_array) == len(active):
            selected_active = mask_array
        else:
            raise ValueError(
                f'Unexpected selected_mask length: got {len(mask_array)}, '
                f'expected {len(active)} active rows or {len(frame)} full rows.'
            )

    selected = active.loc[selected_active].copy()

    accepted_indices = []
    accepted_pnl = []
    last_accepted_pos = None
    selected_positions = active_positions[selected_active]
    for idx, row, current_pos in zip(selected.index, selected.itertuples(index=False), selected_positions, strict=False):
        if last_accepted_pos is not None and current_pos - last_accepted_pos < hold_bars:
            continue
        accepted_indices.append(idx)
        accepted_pnl.append(float(row.true_ret_24_dir_atr))
        last_accepted_pos = current_pos

    pnl = np.asarray(accepted_pnl, dtype=np.float64)
    trades = int(len(accepted_indices))
    selected_trades = int(len(selected))
    coverage = float(trades / selected_trades) if selected_trades > 0 else 0.0
    pf = compute_pf(pnl)
    mean_pnl_atr = float(pnl.mean()) if trades > 0 else 0.0
    win_rate = float((pnl > 0).mean()) if trades > 0 else 0.0

    return {
        'trades': trades,
        'accepted_indices': accepted_indices,
        'coverage': coverage,
        'pf': pf,
        'mean_pnl_atr': mean_pnl_atr,
        'win_rate': win_rate,
    }


def build_trade_filter_report_markdown(validation_best, test_row, sequential_summary, rule_path) -> str:
    winner = validation_best.get('candidate', 'N/A')
    lines = [
        '# Entry Path Trade Filter Report',
        '',
        f'Победитель: **{winner}**',
        '',
        '## Validation Winner',
        '',
        f"- candidate: `{validation_best.get('candidate', 'N/A')}`",
        f"- pf: **{float(validation_best.get('pf', 0.0)):.4f}**",
        f"- coverage: **{float(validation_best.get('coverage', 0.0)):.2%}**",
        f"- stability_ratio: **{float(validation_best.get('stability_ratio', 0.0)):.2f}**",
        '',
        '## Test Check',
        '',
        f"- candidate: `{test_row.get('candidate', 'N/A')}`",
        f"- pf: **{float(test_row.get('pf', 0.0)):.4f}**",
        f"- coverage: **{float(test_row.get('coverage', 0.0)):.2%}**",
        f"- stability_ratio: **{float(test_row.get('stability_ratio', 0.0)):.2f}**",
        '',
        '## Sequential Check',
        '',
        f"- trades: **{int(sequential_summary.get('trades', 0))}**",
        f"- pf: **{float(sequential_summary.get('pf', 0.0)):.4f}**",
        f"- coverage_vs_selected: **{float(sequential_summary.get('coverage', 0.0)):.2%}**",
        f"- mean_pnl_atr: **{float(sequential_summary.get('mean_pnl_atr', 0.0)):.4f}**",
        f"- win_rate: **{float(sequential_summary.get('win_rate', 0.0)):.2%}**",
        '',
        '## Frozen Rule',
        '',
        f'- Rule path: `{rule_path}`',
    ]
    return '\n'.join(lines)
