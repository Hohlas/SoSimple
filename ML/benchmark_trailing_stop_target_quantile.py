from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from ML.trailing_stop_target_quantile_task import (
    TRAILING_STOP_TARGET_QUANTILE_BASE_COLUMN,
    TRAILING_STOP_TARGET_QUANTILE_Q10_COLUMN,
    TRAILING_STOP_TARGET_QUANTILE_Q50_COLUMN,
    TRAILING_STOP_TARGET_QUANTILE_Q90_COLUMN,
)


DEFAULT_Q10_QUANTILES = (0.80, 0.85, 0.90, 0.95)
DEFAULT_SCORE_THRESHOLD_QUANTILES = (0.80, 0.90)


def _active_rows(frame: pd.DataFrame) -> pd.DataFrame:
    signal = pd.to_numeric(frame.get('signal', 0), errors='coerce').fillna(0).astype(int)
    return frame.loc[signal != 0].copy()


def _profit_factor(pnl: pd.Series) -> tuple[float, float, float]:
    values = pnl.to_numpy(dtype=float)
    gross_profit = float(values[values > 0].sum())
    gross_loss = float(-values[values < 0].sum())
    pf = gross_profit / gross_loss if gross_loss > 0 else (float('inf') if gross_profit > 0 else 0.0)
    return gross_profit, gross_loss, float(pf)


def _spread_aware_score(frame: pd.DataFrame) -> pd.Series:
    width = (frame[TRAILING_STOP_TARGET_QUANTILE_Q90_COLUMN] - frame[TRAILING_STOP_TARGET_QUANTILE_Q10_COLUMN]).abs()
    return frame[TRAILING_STOP_TARGET_QUANTILE_Q10_COLUMN] / width.clip(lower=1e-6)


def _select_live_rows(frame: pd.DataFrame, candidate: str, threshold: float) -> pd.DataFrame:
    active = _active_rows(frame)
    if candidate == 'q10_gt_zero':
        return active.loc[active[TRAILING_STOP_TARGET_QUANTILE_Q10_COLUMN] > 0.0].copy()
    if candidate == 'q10_gt_m':
        return active.loc[active[TRAILING_STOP_TARGET_QUANTILE_Q10_COLUMN] >= threshold].copy()
    if candidate == 'q10_q50_positive':
        return active.loc[
            (active[TRAILING_STOP_TARGET_QUANTILE_Q10_COLUMN] > 0.0)
            & (active[TRAILING_STOP_TARGET_QUANTILE_Q50_COLUMN] > 0.0)
        ].copy()
    if candidate == 'spread_score':
        score = _spread_aware_score(active)
        return active.loc[score >= threshold].copy()
    raise ValueError(f'unknown candidate: {candidate}')


def summarize_candidate(
    frame: pd.DataFrame,
    candidate: str,
    threshold: float,
    true_col: str,
) -> dict[str, float]:
    live = _select_live_rows(frame, candidate=candidate, threshold=threshold)
    gross_profit, gross_loss, pf = _profit_factor(live[true_col]) if true_col in live else (0.0, 0.0, 0.0)
    pnl = live[true_col].to_numpy(dtype=float) if true_col in live else []
    ulcer_index = float(abs(pd.Series(pnl, dtype=float).cumsum()).mean()) if len(pnl) else 0.0
    return {
        'candidate': candidate,
        'threshold': float(threshold),
        'trades': int(len(live)),
        'gross_profit': gross_profit,
        'gross_loss': gross_loss,
        'pf': pf,
        'ulcer_index_atr': ulcer_index,
    }


def pick_validation_winner(table: pd.DataFrame, min_pf: float = 1.0) -> pd.Series | None:
    eligible = table.loc[table['pf'] >= min_pf].copy()
    if eligible.empty:
        return None
    ranked = eligible.sort_values(['pf', 'ulcer_index_atr', 'trades'], ascending=[False, True, False])
    return ranked.iloc[0]


def build_candidate_table(
    frame: pd.DataFrame,
    true_col: str = f'true_{TRAILING_STOP_TARGET_QUANTILE_BASE_COLUMN}',
    q10_quantiles: tuple[float, ...] = DEFAULT_Q10_QUANTILES,
    include_spread_score: bool = True,
) -> pd.DataFrame:
    active = _active_rows(frame)
    rows = [
        summarize_candidate(active, candidate='q10_gt_zero', threshold=0.0, true_col=true_col),
        summarize_candidate(active, candidate='q10_q50_positive', threshold=0.0, true_col=true_col),
    ]
    if not active.empty:
        thresholds = sorted(
            {float(active[TRAILING_STOP_TARGET_QUANTILE_Q10_COLUMN].quantile(q)) for q in q10_quantiles},
            reverse=True,
        )
        rows.extend(
            summarize_candidate(active, candidate='q10_gt_m', threshold=threshold, true_col=true_col)
            for threshold in thresholds
        )
        if include_spread_score:
            score = _spread_aware_score(active)
            score_thresholds = sorted(
                {float(score.quantile(q)) for q in DEFAULT_SCORE_THRESHOLD_QUANTILES},
                reverse=True,
            )
            rows.extend(
                summarize_candidate(active.assign(spread_score=score), candidate='spread_score', threshold=threshold, true_col=true_col)
                for threshold in score_thresholds
            )
    return pd.DataFrame(rows)


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


def run_benchmark(
    *,
    validation_csv: Path,
    test_csv: Path,
    output_dir: Path,
    min_pf: float,
) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    validation = pd.read_csv(validation_csv, sep=';')
    test = pd.read_csv(test_csv, sep=';')

    validation_table = build_candidate_table(validation)
    validation_table.to_csv(output_dir / 'validation_grid.csv', sep=';', index=False)

    winner = pick_validation_winner(validation_table, min_pf=min_pf)
    final_verdict: dict[str, object] = {
        'verdict': 'reject',
        'target_column': TRAILING_STOP_TARGET_QUANTILE_BASE_COLUMN,
        'validation_winner': None,
        'test_result': None,
    }
    if winner is not None:
        test_result = summarize_candidate(
            test,
            candidate=str(winner['candidate']),
            threshold=float(winner['threshold']),
            true_col=f'true_{TRAILING_STOP_TARGET_QUANTILE_BASE_COLUMN}',
        )
        final_verdict = {
            'verdict': 'go',
            'target_column': TRAILING_STOP_TARGET_QUANTILE_BASE_COLUMN,
            'validation_winner': _jsonable(winner.to_dict()),
            'test_result': _jsonable(test_result),
        }

    final_verdict_path = output_dir / 'final_verdict.json'
    final_verdict_path.write_text(json.dumps(_jsonable(final_verdict), ensure_ascii=False, indent=2), encoding='utf-8')
    return {
        'validation_grid_path': str(output_dir / 'validation_grid.csv'),
        'final_verdict_path': str(final_verdict_path),
        'final_verdict': final_verdict,
    }
