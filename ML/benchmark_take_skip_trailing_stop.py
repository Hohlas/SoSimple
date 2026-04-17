from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from ML.take_skip_trailing_stop_task import TAKE_SKIP_TRAILING_STOP_COLUMNS


DEFAULT_THRESHOLDS = (0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95)
DEFAULT_TOP_K = (0.005, 0.01, 0.02, 0.03, 0.05, 0.075, 0.10)


def _parse_time_column(frame: pd.DataFrame) -> pd.Series:
    if 'time' not in frame.columns:
        raise ValueError('benchmark frame missing required time column')
    parsed = pd.to_datetime(frame['time'], format='%Y.%m.%d %H:%M', errors='coerce')
    invalid = parsed.isna()
    if invalid.any():
        raise ValueError(f'unparseable time rows in benchmark frame: {invalid[invalid].index.tolist()}')
    return parsed


def _coverage_years(frame: pd.DataFrame) -> int:
    if frame.empty:
        return 0
    years = _parse_time_column(frame).dt.year
    return int(years.max() - years.min() + 1)


def _active_rows(frame: pd.DataFrame) -> pd.DataFrame:
    signal = pd.to_numeric(frame.get('signal', 0), errors='coerce').fillna(0).astype(int)
    return frame.loc[signal != 0].copy()


def _profit_factor(pnl: pd.Series) -> tuple[float, float, float]:
    values = pnl.to_numpy(dtype=float)
    gross_profit = float(values[values > 0].sum())
    gross_loss = float(-values[values < 0].sum())
    pf = gross_profit / gross_loss if gross_loss > 0 else (float('inf') if gross_profit > 0 else 0.0)
    return gross_profit, gross_loss, float(pf)


def _series_profit_factor(pnl: pd.Series) -> float:
    return _profit_factor(pnl)[2]


def _profit_concentration_top_10(pnl: pd.Series) -> float:
    profits = np.sort(pnl[pnl > 0].to_numpy(dtype=float))[::-1]
    total_profit = float(profits.sum())
    if total_profit <= 0.0:
        return 0.0
    top_count = max(1, int(np.ceil(len(profits) * 0.10)))
    return float(profits[:top_count].sum() / total_profit)


def _max_drawdown_atr(pnl: pd.Series) -> float:
    values = pnl.to_numpy(dtype=float)
    if len(values) == 0:
        return 0.0
    equity = values.cumsum()
    peaks = np.maximum.accumulate(np.insert(equity, 0, 0.0))[1:]
    drawdowns = peaks - equity
    return float(drawdowns.max(initial=0.0))


def _trades_per_year(frame: pd.DataFrame, coverage_years: int | None) -> float:
    if frame.empty:
        return 0.0
    if coverage_years is None:
        coverage_years = _coverage_years(frame)
    if coverage_years <= 0:
        return 0.0
    return float(len(frame) / coverage_years)


def _negative_year_slices(frame: pd.DataFrame, pnl_col: str) -> int:
    if frame.empty:
        return 0
    years = _parse_time_column(frame).dt.year
    by_year = frame.assign(_year=years.to_numpy())
    return int(sum(_series_profit_factor(group[pnl_col]) < 1.0 for _, group in by_year.groupby('_year')))


def _jsonable(value):
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, 'tolist'):
        return value.tolist()
    if hasattr(value, 'item'):
        return value.item()
    return value


def _target_pnl_column(target_column: str) -> str:
    return f"true_trail_48_pnl_atr_x{target_column.rsplit('x', 1)[1]}"


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
        if active.empty:
            live = active.copy()
        else:
            live_count = max(1, int(np.ceil(len(active) * threshold)))
            live = active.nlargest(live_count, score_col).copy()
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


def pick_validation_winner(
    table: pd.DataFrame,
    min_pf: float,
    min_trades_per_year: float,
) -> pd.Series | None:
    eligible = table.loc[(table['pf'] >= min_pf) & (table['trades_per_year'] >= min_trades_per_year)].copy()
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
    targets: tuple[str, ...] = tuple(TAKE_SKIP_TRAILING_STOP_COLUMNS),
) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    validation = pd.read_csv(validation_csv, sep=';')
    test = pd.read_csv(test_csv, sep=';')

    _coverage_years(validation)
    test_coverage_years = _coverage_years(test)

    tables = [build_candidate_table(validation, target_column=target_column) for target_column in targets]
    validation_table = pd.concat(tables, ignore_index=True) if tables else pd.DataFrame()
    validation_grid_path = output_dir / 'validation_grid.csv'
    validation_table.to_csv(validation_grid_path, sep=';', index=False)

    winner = pick_validation_winner(validation_table, min_pf=min_pf, min_trades_per_year=min_trades_per_year)
    final_verdict: dict[str, object] = {
        'verdict': 'reject',
        'validation_winner': None,
        'test_result': None,
    }
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
