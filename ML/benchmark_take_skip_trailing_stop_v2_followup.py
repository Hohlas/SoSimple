from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from ML.benchmark_take_skip_trailing_stop import (
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


DEFAULT_FOLLOWUP_THRESHOLDS = (0.50, 0.55, 0.60, 0.65, 0.70, 0.75)
DEFAULT_FOLLOWUP_TOP_K = (0.01, 0.02, 0.03, 0.05, 0.07, 0.10, 0.15, 0.20)
DEFAULT_EVAL_X_VALUES = (8, 10, 12)
DEFAULT_MIN_PF = 1.0
DEFAULT_MIN_TRADES_PER_YEAR = 6.0


def pair_score_targets_with_eval_pnl(
    score_targets: list[str] | tuple[str, ...],
    eval_x_values: tuple[int, ...] = DEFAULT_EVAL_X_VALUES,
) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for score_target in score_targets:
        _, horizon, _x_suffix = score_target.split('_')
        for x_value in eval_x_values:
            pairs.append((score_target, f'true_trail_{horizon}_pnl_atr_x{x_value}'))
    return pairs


def summarize_candidate(
    frame: pd.DataFrame,
    *,
    score_target: str,
    eval_pnl_column: str,
    candidate: str,
    threshold: float,
    coverage_years: int | None = None,
    positive_threshold_atr: float = 0.5,
) -> dict[str, float]:
    score_col = f'pred_{score_target}'
    if score_col not in frame.columns or eval_pnl_column not in frame.columns:
        raise ValueError(f'missing followup columns for pair {(score_target, eval_pnl_column)!r}')

    active = _active_rows(frame)
    if candidate == 'prob_ge_threshold':
        live = active.loc[active[score_col] >= threshold].copy()
    elif candidate == 'top_k_probability':
        k_count = max(1, int(len(active) * threshold + 0.999999))
        live = active.nlargest(k_count, score_col).copy() if not active.empty else active.copy()
    else:
        raise ValueError(f'unknown candidate: {candidate}')

    pnl = live[eval_pnl_column].astype(float)
    gross_profit, gross_loss, pf = _profit_factor(pnl)
    ulcer_index = float(abs(pnl.cumsum()).mean()) if len(pnl) else 0.0
    positive_rate_selected = float((pnl >= positive_threshold_atr).mean()) if len(pnl) else 0.0
    return {
        'score_target': score_target,
        'eval_pnl_column': eval_pnl_column,
        'candidate': candidate,
        'threshold': float(threshold),
        'trades': int(len(live)),
        'trades_per_year': _trades_per_year(live, coverage_years),
        'gross_profit': gross_profit,
        'gross_loss': gross_loss,
        'pf': pf,
        'negative_year_slices': _negative_year_slices(live, eval_pnl_column),
        'profit_concentration_top_10': _profit_concentration_top_10(pnl),
        'ulcer_index_atr': ulcer_index,
        'max_drawdown_atr': _max_drawdown_atr(pnl),
        'positive_rate_selected': positive_rate_selected,
    }


def build_candidate_table(
    frame: pd.DataFrame,
    *,
    pairings: list[tuple[str, str]],
    thresholds: tuple[float, ...] = DEFAULT_FOLLOWUP_THRESHOLDS,
    top_k_values: tuple[float, ...] = DEFAULT_FOLLOWUP_TOP_K,
) -> pd.DataFrame:
    coverage_years = _coverage_years(frame)
    rows = []
    for score_target, eval_pnl_column in pairings:
        for threshold in thresholds:
            rows.append(
                summarize_candidate(
                    frame,
                    score_target=score_target,
                    eval_pnl_column=eval_pnl_column,
                    candidate='prob_ge_threshold',
                    threshold=float(threshold),
                    coverage_years=coverage_years,
                )
            )
        for top_k in top_k_values:
            rows.append(
                summarize_candidate(
                    frame,
                    score_target=score_target,
                    eval_pnl_column=eval_pnl_column,
                    candidate='top_k_probability',
                    threshold=float(top_k),
                    coverage_years=coverage_years,
                )
            )
    return pd.DataFrame(rows)


def pick_quality_first(table: pd.DataFrame, *, min_pf: float, min_trades_per_year: float) -> pd.Series | None:
    eligible = table.loc[(table['pf'] > min_pf) & (table['trades_per_year'] >= min_trades_per_year)].copy()
    if eligible.empty:
        return None
    ranked = eligible.sort_values(
        ['pf', 'negative_year_slices', 'max_drawdown_atr', 'trades'],
        ascending=[False, True, True, False],
    )
    return ranked.iloc[0]


def pick_frequency_first(table: pd.DataFrame, *, min_pf: float) -> pd.Series | None:
    eligible = table.loc[(table['pf'] > min_pf) & (table['negative_year_slices'] == 0)].copy()
    if eligible.empty:
        return None
    ranked = eligible.sort_values(
        ['trades_per_year', 'pf', 'profit_concentration_top_10', 'max_drawdown_atr'],
        ascending=[False, False, True, True],
    )
    return ranked.iloc[0]


def _freeze_to_test(
    winner: pd.Series | None,
    test_frame: pd.DataFrame,
) -> dict[str, float] | None:
    if winner is None:
        return None
    return _jsonable(
        summarize_candidate(
            test_frame,
            score_target=str(winner['score_target']),
            eval_pnl_column=str(winner['eval_pnl_column']),
            candidate=str(winner['candidate']),
            threshold=float(winner['threshold']),
            coverage_years=_coverage_years(test_frame),
        )
    )


def run_followup_benchmark(
    *,
    validation_csv: Path,
    test_csv: Path,
    output_dir: Path,
    pairings: list[tuple[str, str]],
    thresholds: tuple[float, ...] = DEFAULT_FOLLOWUP_THRESHOLDS,
    top_k_values: tuple[float, ...] = DEFAULT_FOLLOWUP_TOP_K,
    min_pf: float = DEFAULT_MIN_PF,
    min_trades_per_year: float = DEFAULT_MIN_TRADES_PER_YEAR,
) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    validation = pd.read_csv(validation_csv, sep=';')
    test = pd.read_csv(test_csv, sep=';')
    _parse_time_column(validation)
    _parse_time_column(test)

    table = build_candidate_table(
        validation,
        pairings=pairings,
        thresholds=thresholds,
        top_k_values=top_k_values,
    )
    table_path = output_dir / 'validation_followup_grid.csv'
    table.to_csv(table_path, sep=';', index=False)

    quality_winner = pick_quality_first(table, min_pf=min_pf, min_trades_per_year=min_trades_per_year)
    frequency_winner = pick_frequency_first(table, min_pf=min_pf)
    result = {
        'validation_grid_path': str(table_path),
        'quality_first': {
            'validation_winner': None if quality_winner is None else _jsonable(quality_winner.to_dict()),
            'test_result': _freeze_to_test(quality_winner, test),
        },
        'frequency_first': {
            'validation_winner': None if frequency_winner is None else _jsonable(frequency_winner.to_dict()),
            'test_result': _freeze_to_test(frequency_winner, test),
        },
    }
    result_path = output_dir / 'followup_summary.json'
    result_path.write_text(json.dumps(_jsonable(result), ensure_ascii=False, indent=2), encoding='utf-8')
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description='Take/skip v2 follow-up benchmark over ready-made prediction CSVs.')
    parser.add_argument('--validation-csv', type=Path, required=True)
    parser.add_argument('--test-csv', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--score-target', action='append', default=[])
    args = parser.parse_args()

    score_targets = args.score_target or ['take_24_x8']
    pairings = pair_score_targets_with_eval_pnl(score_targets)
    result = run_followup_benchmark(
        validation_csv=args.validation_csv,
        test_csv=args.test_csv,
        output_dir=args.output_dir,
        pairings=pairings,
    )
    print(json.dumps(_jsonable(result), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
