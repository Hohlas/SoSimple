# =============================================================================
# Файл: benchmark_take_skip_lib_pic_selection.py
# Назначение: Проверка внешнего слоя отбора `take_skip_v2` по признакам `lib_PIC`.
# Обновлён: 2026-04-20
# Входные данные:
#   - prediction CSV `take_skip_trailing_stop_v2`
#   - исходный/labeled CSV с fractal-колонками
# Выходные данные:
#   - validation_grid.csv
#   - final_verdict.json
# Использование:
#   python -m ML.benchmark_take_skip_lib_pic_selection --validation-predictions ... --validation-source ...
# Примечания:
#   - Не запускает обучение. Порог признака выбирается только на validation и замораживается на test.
# =============================================================================

from __future__ import annotations

import argparse
import json
import math
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
from ML.benchmark_take_skip_trailing_stop_v2_followup import (
    DEFAULT_FOLLOWUP_TOP_K,
    DEFAULT_FOLLOWUP_THRESHOLDS,
    pair_score_targets_with_eval_pnl,
)
from ML.lib_pic_feature_profiles import build_lib_pic_feature_profile


DEFAULT_FEATURE_PROFILE = 'baseline_clean_geometry_path'
DEFAULT_SEQ_LEN = 100
DEFAULT_SCORE_TARGETS = ('take_24_x8', 'take_24_x4')
DEFAULT_EVAL_X_VALUES = (8, 10)
DEFAULT_FEATURE_QUANTILES = (0.50, 0.60, 0.70)
DEFAULT_FEATURE_COLUMNS = (
    'pic_path_edge24_mean_w20',
    'pic_path_edge24_mean_w50',
    'pic_path_rr24_mean_w20',
    'pic_path_win_proxy24_share_w20',
    'pic_geom_balance_mean_w20',
    'pic_geom_front_dominant_share_w20',
)


def _fractal_columns(seq_len: int) -> list[str]:
    return [f'fractal{idx}' for idx in range(seq_len)]


def _source_usecols(path: Path, seq_len: int) -> list[str]:
    header = pd.read_csv(path, sep=';', nrows=0).columns.tolist()
    wanted = ['time', 'signal', 'ATR', 'session_hour', 'weekday']
    wanted.extend(_fractal_columns(seq_len))
    return [column for column in wanted if column in header]


def read_source_for_features(path: Path, *, seq_len: int) -> pd.DataFrame:
    """Читает только колонки, нужные для построения признаков `lib_PIC`."""
    return pd.read_csv(path, sep=';', usecols=_source_usecols(path, seq_len), low_memory=False)


def merge_predictions_with_lib_pic_features(
    *,
    predictions: pd.DataFrame,
    source: pd.DataFrame,
    feature_profile: str,
    seq_len: int,
) -> pd.DataFrame:
    """Добавляет к prediction-строкам признаки `lib_PIC` без изменения порядка строк."""
    if len(predictions) != len(source):
        raise ValueError(f'predictions/source row count mismatch: {len(predictions)} != {len(source)}')
    if 'time' in predictions.columns and 'time' in source.columns:
        pred_time = predictions['time'].astype(str).reset_index(drop=True)
        source_time = source['time'].astype(str).reset_index(drop=True)
        if not pred_time.equals(source_time):
            raise ValueError('predictions/source time columns are not aligned')

    features = build_lib_pic_feature_profile(source.reset_index(drop=True), profile=feature_profile, seq_len=seq_len)
    feature_columns = [column for column in features.columns if column not in predictions.columns]
    return pd.concat([predictions.reset_index(drop=True), features[feature_columns].reset_index(drop=True)], axis=1)


def _select_by_score(active: pd.DataFrame, *, score_col: str, selector: str, threshold: float) -> pd.DataFrame:
    if selector == 'prob_ge_threshold':
        return active.loc[active[score_col] >= threshold].copy()
    if selector == 'top_k_probability':
        k_count = max(1, int(len(active) * threshold + 0.999999))
        return active.nlargest(k_count, score_col).copy() if not active.empty else active.copy()
    raise ValueError(f'unknown selector: {selector}')


def _apply_feature_filter(frame: pd.DataFrame, *, feature_column: str | None, feature_threshold: float | None) -> pd.DataFrame:
    if feature_column is None:
        return frame.copy()
    if feature_column not in frame.columns:
        raise ValueError(f'missing feature column: {feature_column}')
    if feature_threshold is None:
        raise ValueError('feature_threshold is required when feature_column is set')
    return frame.loc[pd.to_numeric(frame[feature_column], errors='coerce').fillna(0.0) >= feature_threshold].copy()


def summarize_candidate(
    frame: pd.DataFrame,
    *,
    score_target: str,
    eval_pnl_column: str,
    selector: str,
    selector_threshold: float,
    feature_column: str | None,
    feature_threshold: float | None,
    feature_quantile: float | None = None,
    coverage_years: int | None = None,
    positive_threshold_atr: float = 0.5,
) -> dict[str, float | str | None]:
    score_col = f'pred_{score_target}'
    if score_col not in frame.columns or eval_pnl_column not in frame.columns:
        raise ValueError(f'missing benchmark columns for pair {(score_target, eval_pnl_column)!r}')

    active = _active_rows(frame)
    live = _select_by_score(active, score_col=score_col, selector=selector, threshold=selector_threshold)
    live = _apply_feature_filter(live, feature_column=feature_column, feature_threshold=feature_threshold)

    pnl = live[eval_pnl_column].astype(float)
    gross_profit, gross_loss, pf = _profit_factor(pnl)
    positive_rate_selected = float((pnl >= positive_threshold_atr).mean()) if len(pnl) else 0.0
    return {
        'score_target': score_target,
        'eval_pnl_column': eval_pnl_column,
        'selector': selector,
        'selector_threshold': float(selector_threshold),
        'feature_filter': 'none' if feature_column is None else 'gte_validation_quantile',
        'feature_column': feature_column,
        'feature_quantile': None if feature_quantile is None else float(feature_quantile),
        'feature_threshold': None if feature_threshold is None else float(feature_threshold),
        'trades': int(len(live)),
        'trades_per_year': _trades_per_year(live, coverage_years),
        'gross_profit': gross_profit,
        'gross_loss': gross_loss,
        'pf': pf,
        'negative_year_slices': _negative_year_slices(live, eval_pnl_column),
        'profit_concentration_top_10': _profit_concentration_top_10(pnl),
        'ulcer_index_atr': float(abs(pnl.cumsum()).mean()) if len(pnl) else 0.0,
        'max_drawdown_atr': _max_drawdown_atr(pnl),
        'positive_rate_selected': positive_rate_selected,
    }


def _feature_thresholds(
    frame: pd.DataFrame,
    *,
    feature_columns: tuple[str, ...],
    feature_quantiles: tuple[float, ...],
) -> list[tuple[str | None, float | None, float | None]]:
    active = _active_rows(frame)
    specs: list[tuple[str | None, float | None, float | None]] = [(None, None, None)]
    for column in feature_columns:
        if column not in frame.columns:
            continue
        values = pd.to_numeric(active[column], errors='coerce').replace([float('inf'), float('-inf')], 0.0).fillna(0.0)
        if values.empty:
            continue
        for quantile in feature_quantiles:
            specs.append((column, float(quantile), float(values.quantile(quantile))))
    return specs


def build_candidate_table(
    frame: pd.DataFrame,
    *,
    pairings: list[tuple[str, str]],
    score_thresholds: tuple[float, ...] = DEFAULT_FOLLOWUP_THRESHOLDS,
    top_k_values: tuple[float, ...] = DEFAULT_FOLLOWUP_TOP_K,
    feature_columns: tuple[str, ...] = DEFAULT_FEATURE_COLUMNS,
    feature_quantiles: tuple[float, ...] = DEFAULT_FEATURE_QUANTILES,
) -> pd.DataFrame:
    coverage_years = _coverage_years(frame)
    feature_specs = _feature_thresholds(
        frame,
        feature_columns=feature_columns,
        feature_quantiles=feature_quantiles,
    )

    rows = []
    for score_target, eval_pnl_column in pairings:
        for feature_column, feature_quantile, feature_threshold in feature_specs:
            for threshold in score_thresholds:
                rows.append(
                    summarize_candidate(
                        frame,
                        score_target=score_target,
                        eval_pnl_column=eval_pnl_column,
                        selector='prob_ge_threshold',
                        selector_threshold=float(threshold),
                        feature_column=feature_column,
                        feature_threshold=feature_threshold,
                        feature_quantile=feature_quantile,
                        coverage_years=coverage_years,
                    )
                )
            for top_k in top_k_values:
                rows.append(
                    summarize_candidate(
                        frame,
                        score_target=score_target,
                        eval_pnl_column=eval_pnl_column,
                        selector='top_k_probability',
                        selector_threshold=float(top_k),
                        feature_column=feature_column,
                        feature_threshold=feature_threshold,
                        feature_quantile=feature_quantile,
                        coverage_years=coverage_years,
                    )
                )
    return pd.DataFrame(rows)


def pick_validation_winner(table: pd.DataFrame, *, min_pf: float, min_trades_per_year: float) -> pd.Series | None:
    eligible = table.loc[(table['pf'] > min_pf) & (table['trades_per_year'] >= min_trades_per_year)].copy()
    if eligible.empty:
        return None
    eligible['_uses_feature'] = (eligible['feature_filter'] != 'none').astype(int)
    ranked = eligible.sort_values(
        [
            'pf',
            'negative_year_slices',
            'profit_concentration_top_10',
            'max_drawdown_atr',
            '_uses_feature',
            'trades_per_year',
        ],
        ascending=[False, True, True, True, False, False],
    )
    return ranked.iloc[0]


def pick_frequency_winner(table: pd.DataFrame, *, min_pf: float, require_feature: bool = False) -> pd.Series | None:
    eligible = table.loc[(table['pf'] > min_pf) & (table['negative_year_slices'] == 0)].copy()
    if require_feature:
        eligible = eligible.loc[eligible['feature_filter'] != 'none'].copy()
    if eligible.empty:
        return None
    eligible['_uses_feature'] = (eligible['feature_filter'] != 'none').astype(int)
    ranked = eligible.sort_values(
        [
            'trades_per_year',
            'pf',
            'profit_concentration_top_10',
            'max_drawdown_atr',
            '_uses_feature',
        ],
        ascending=[False, False, True, True, False],
    )
    return ranked.iloc[0]


def _freeze_to_test(winner: pd.Series | None, test: pd.DataFrame) -> dict[str, object] | None:
    if winner is None:
        return None
    return _jsonable(
        summarize_candidate(
            test,
            score_target=str(winner['score_target']),
            eval_pnl_column=str(winner['eval_pnl_column']),
            selector=str(winner['selector']),
            selector_threshold=float(winner['selector_threshold']),
            feature_column=None if pd.isna(winner['feature_column']) else str(winner['feature_column']),
            feature_threshold=None if pd.isna(winner['feature_threshold']) else float(winner['feature_threshold']),
            feature_quantile=None if pd.isna(winner['feature_quantile']) else float(winner['feature_quantile']),
            coverage_years=_coverage_years(test),
        )
    )


def _winner_to_dict(winner: pd.Series | None) -> dict[str, object] | None:
    if winner is None:
        return None
    raw = winner.to_dict()
    return _json_safe({key: value for key, value in raw.items()})


def _json_safe(value):
    """Преобразует NaN/inf в переносимые JSON-значения."""
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, 'tolist'):
        return _json_safe(value.tolist())
    if hasattr(value, 'item'):
        return _json_safe(value.item())
    if value is None:
        return None
    if isinstance(value, float):
        if math.isnan(value):
            return None
        if math.isinf(value):
            return 'inf' if value > 0 else '-inf'
    return value


def _winner_block(winner: pd.Series | None, test: pd.DataFrame) -> dict[str, object]:
    return {
        'validation_winner': _winner_to_dict(winner),
        'test_result': _freeze_to_test(winner, test),
    }


def run_selection_benchmark_from_frames(
    *,
    validation: pd.DataFrame,
    test: pd.DataFrame,
    pairings: list[tuple[str, str]],
    score_thresholds: tuple[float, ...] = DEFAULT_FOLLOWUP_THRESHOLDS,
    top_k_values: tuple[float, ...] = DEFAULT_FOLLOWUP_TOP_K,
    feature_columns: tuple[str, ...] = DEFAULT_FEATURE_COLUMNS,
    feature_quantiles: tuple[float, ...] = DEFAULT_FEATURE_QUANTILES,
    min_pf: float = 1.0,
    min_trades_per_year: float = 6.0,
) -> dict[str, object]:
    _parse_time_column(validation)
    _parse_time_column(test)
    validation_grid = build_candidate_table(
        validation,
        pairings=pairings,
        score_thresholds=score_thresholds,
        top_k_values=top_k_values,
        feature_columns=feature_columns,
        feature_quantiles=feature_quantiles,
    )
    winner = pick_validation_winner(validation_grid, min_pf=min_pf, min_trades_per_year=min_trades_per_year)
    frequency_winner = pick_frequency_winner(validation_grid, min_pf=min_pf)
    feature_frequency_winner = pick_frequency_winner(validation_grid, min_pf=min_pf, require_feature=True)
    return {
        'validation_grid': validation_grid,
        'validation_winner': _winner_to_dict(winner),
        'test_result': _freeze_to_test(winner, test),
        'quality_first': _winner_block(winner, test),
        'frequency_first': _winner_block(frequency_winner, test),
        'feature_frequency_first': _winner_block(feature_frequency_winner, test),
    }


def run_selection_benchmark(
    *,
    validation_predictions_csv: Path,
    test_predictions_csv: Path,
    validation_source_csv: Path,
    test_source_csv: Path,
    output_dir: Path,
    feature_profile: str = DEFAULT_FEATURE_PROFILE,
    seq_len: int = DEFAULT_SEQ_LEN,
    score_targets: tuple[str, ...] = DEFAULT_SCORE_TARGETS,
    eval_x_values: tuple[int, ...] = DEFAULT_EVAL_X_VALUES,
    feature_columns: tuple[str, ...] = DEFAULT_FEATURE_COLUMNS,
    min_pf: float = 1.0,
    min_trades_per_year: float = 6.0,
) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)

    validation_predictions = pd.read_csv(validation_predictions_csv, sep=';')
    test_predictions = pd.read_csv(test_predictions_csv, sep=';')
    validation_source = read_source_for_features(validation_source_csv, seq_len=seq_len)
    test_source = read_source_for_features(test_source_csv, seq_len=seq_len)

    validation = merge_predictions_with_lib_pic_features(
        predictions=validation_predictions,
        source=validation_source,
        feature_profile=feature_profile,
        seq_len=seq_len,
    )
    test = merge_predictions_with_lib_pic_features(
        predictions=test_predictions,
        source=test_source,
        feature_profile=feature_profile,
        seq_len=seq_len,
    )
    pairings = pair_score_targets_with_eval_pnl(list(score_targets), eval_x_values=eval_x_values)
    result = run_selection_benchmark_from_frames(
        validation=validation,
        test=test,
        pairings=pairings,
        feature_columns=feature_columns,
        min_pf=min_pf,
        min_trades_per_year=min_trades_per_year,
    )

    validation_grid_path = output_dir / 'validation_grid.csv'
    result['validation_grid'].to_csv(validation_grid_path, sep=';', index=False)
    final_verdict = {
        'verdict': 'reject' if result['validation_winner'] is None else 'go',
        'feature_profile': feature_profile,
        'seq_len': seq_len,
        'validation_winner': result['validation_winner'],
        'test_result': result['test_result'],
        'quality_first': result['quality_first'],
        'frequency_first': result['frequency_first'],
        'feature_frequency_first': result['feature_frequency_first'],
    }
    final_verdict_path = output_dir / 'final_verdict.json'
    final_verdict_path.write_text(json.dumps(_json_safe(final_verdict), ensure_ascii=False, indent=2), encoding='utf-8')
    return {
        'validation_grid_path': str(validation_grid_path),
        'final_verdict_path': str(final_verdict_path),
        'final_verdict': final_verdict,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description='External lib_PIC selection benchmark for take_skip_v2 predictions.')
    parser.add_argument('--validation-predictions', type=Path, required=True)
    parser.add_argument('--test-predictions', type=Path, required=True)
    parser.add_argument('--validation-source', type=Path, default=Path('DATA/Nero_validation_labeled.csv'))
    parser.add_argument('--test-source', type=Path, default=Path('DATA/Nero_test_labeled.csv'))
    parser.add_argument('--output-dir', type=Path, default=Path('ML/reports/take_skip_lib_pic_selection'))
    parser.add_argument('--feature-profile', default=DEFAULT_FEATURE_PROFILE)
    parser.add_argument('--seq-len', type=int, default=DEFAULT_SEQ_LEN)
    parser.add_argument('--score-target', action='append', default=[])
    parser.add_argument('--eval-x', type=int, action='append', default=[])
    parser.add_argument('--min-pf', type=float, default=1.0)
    parser.add_argument('--min-trades-per-year', type=float, default=6.0)
    args = parser.parse_args()

    result = run_selection_benchmark(
        validation_predictions_csv=args.validation_predictions,
        test_predictions_csv=args.test_predictions,
        validation_source_csv=args.validation_source,
        test_source_csv=args.test_source,
        output_dir=args.output_dir,
        feature_profile=args.feature_profile,
        seq_len=args.seq_len,
        score_targets=tuple(args.score_target) or DEFAULT_SCORE_TARGETS,
        eval_x_values=tuple(args.eval_x) or DEFAULT_EVAL_X_VALUES,
        min_pf=args.min_pf,
        min_trades_per_year=args.min_trades_per_year,
    )
    print(json.dumps(_json_safe(result), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
