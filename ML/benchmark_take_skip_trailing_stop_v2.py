from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from ML.benchmark_take_skip_trailing_stop import (
    DEFAULT_THRESHOLDS,
    DEFAULT_TOP_K,
    _active_rows,
    _coverage_years,
    _jsonable,
    _max_drawdown_atr,
    _negative_year_slices,
    _parse_time_column,
    _profit_concentration_top_10,
    _profit_factor,
    _trades_per_year,
)
from ML.take_skip_trailing_stop_v2_task import TAKE_SKIP_TRAILING_STOP_V2_COLUMNS


def _target_pnl_column(target_column: str) -> str:
    _, horizon, x_suffix = target_column.split('_')
    return f'true_trail_{horizon}_pnl_atr_{x_suffix}'


def summarize_candidate(
    frame: pd.DataFrame,
    target_column: str,
    candidate: str,
    threshold: float,
    coverage_years: int | None = None,
) -> dict[str, float]:
    score_col = f'pred_{target_column}'
    label_col = f'true_{target_column}'
    pnl_col = _target_pnl_column(target_column)
    if score_col not in frame.columns or label_col not in frame.columns or pnl_col not in frame.columns:
        raise ValueError(f'missing benchmark columns for target {target_column!r}')

    active = _active_rows(frame)
    if candidate == 'prob_ge_threshold':
        live = active.loc[active[score_col] >= threshold].copy()
    elif candidate == 'top_k_probability':
        live = active.nlargest(max(1, int(len(active) * threshold + 0.999999)), score_col).copy() if not active.empty else active.copy()
    else:
        raise ValueError(f'unknown candidate: {candidate}')

    pnl = live[pnl_col].astype(float)
    gross_profit, gross_loss, pf = _profit_factor(pnl)
    ulcer_index = float(abs(pnl.cumsum()).mean()) if len(pnl) else 0.0
    positive_rate_selected = float(live[label_col].astype(float).mean()) if len(live) else 0.0
    return {
        'target_column': target_column,
        'candidate': candidate,
        'threshold': float(threshold),
        'trades': int(len(live)),
        'trades_per_year': _trades_per_year(live, coverage_years),
        'gross_profit': gross_profit,
        'gross_loss': gross_loss,
        'pf': pf,
        'negative_year_slices': _negative_year_slices(live, pnl_col),
        'profit_concentration_top_10': _profit_concentration_top_10(pnl),
        'ulcer_index_atr': ulcer_index,
        'max_drawdown_atr': _max_drawdown_atr(pnl),
        'positive_rate_selected': positive_rate_selected,
    }


def build_candidate_table(
    frame: pd.DataFrame,
    target_column: str,
    thresholds: tuple[float, ...] = DEFAULT_THRESHOLDS,
    top_k_values: tuple[float, ...] = DEFAULT_TOP_K,
) -> pd.DataFrame:
    coverage_years = _coverage_years(frame)
    rows = [
        summarize_candidate(frame, target_column=target_column, candidate='prob_ge_threshold', threshold=float(threshold), coverage_years=coverage_years)
        for threshold in thresholds
    ]
    rows.extend(
        summarize_candidate(frame, target_column=target_column, candidate='top_k_probability', threshold=float(k), coverage_years=coverage_years)
        for k in top_k_values
    )
    return pd.DataFrame(rows)


def pick_validation_winner(table: pd.DataFrame, min_pf: float, min_trades_per_year: float) -> pd.Series | None:
    eligible = table.loc[(table['pf'] > min_pf) & (table['trades_per_year'] >= min_trades_per_year)].copy()
    if eligible.empty:
        return None
    ranked = eligible.sort_values(
        ['pf', 'negative_year_slices', 'max_drawdown_atr', 'trades'],
        ascending=[False, True, True, False],
    )
    return ranked.iloc[0]


def run_benchmark(
    *,
    validation_csv: Path,
    test_csv: Path,
    output_dir: Path,
    min_pf: float,
    min_trades_per_year: float,
    targets: tuple[str, ...] = tuple(TAKE_SKIP_TRAILING_STOP_V2_COLUMNS),
) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    validation = pd.read_csv(validation_csv, sep=';')
    test = pd.read_csv(test_csv, sep=';')

    _parse_time_column(validation)
    test_coverage_years = _coverage_years(test)

    tables = [build_candidate_table(validation, target_column=target_column) for target_column in targets]
    validation_table = pd.concat(tables, ignore_index=True) if tables else pd.DataFrame()
    validation_grid_path = output_dir / 'validation_grid.csv'
    validation_table.to_csv(validation_grid_path, sep=';', index=False)

    winner = pick_validation_winner(validation_table, min_pf=min_pf, min_trades_per_year=min_trades_per_year)
    final_verdict: dict[str, object] = {'verdict': 'reject', 'validation_winner': None, 'test_result': None}
    if winner is not None:
        test_result = summarize_candidate(
            test,
            target_column=str(winner['target_column']),
            candidate=str(winner['candidate']),
            threshold=float(winner['threshold']),
            coverage_years=test_coverage_years,
        )
        final_verdict = {
            'verdict': 'go',
            'validation_winner': _jsonable(winner.to_dict()),
            'test_result': _jsonable(test_result),
        }

    final_verdict_path = output_dir / 'final_verdict.json'
    final_verdict_path.write_text(json.dumps(_jsonable(final_verdict), ensure_ascii=False, indent=2), encoding='utf-8')
    return {
        'validation_grid_path': str(validation_grid_path),
        'final_verdict_path': str(final_verdict_path),
        'final_verdict': final_verdict,
    }
