from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from ML.entry_path_trade_filter import compute_pf


def load_prediction_frame(path: str | Path) -> pd.DataFrame:
    frame = pd.read_csv(Path(path), sep=';')
    frame['time'] = pd.to_datetime(frame['time'], format='%Y.%m.%d %H:%M', errors='coerce')
    return frame


def compute_profit_concentration(pnl: np.ndarray, top_frac: float = 0.10) -> float:
    pnl = np.asarray(pnl, dtype=np.float64)
    positive = np.sort(pnl[pnl > 0])[::-1]
    if positive.size == 0:
        return 1.0
    top_k = max(1, int(np.ceil(positive.size * top_frac)))
    gross_profit = float(positive.sum())
    if gross_profit <= 0.0:
        return 1.0
    return float(positive[:top_k].sum() / gross_profit)


def summarize_candidate(frame: pd.DataFrame, candidate: str, threshold: float) -> dict[str, float | int | str]:
    active = frame.loc[frame['signal'].astype(int) != 0].copy()
    selected = active.loc[active[candidate] >= threshold].copy()
    pnl = selected['true_ret_24_dir_atr'].to_numpy(dtype=np.float64) if 'true_ret_24_dir_atr' in selected.columns else np.array([], dtype=np.float64)
    trades = int(len(selected))
    trade_times = selected['time'].dropna()
    years = int(max(1, trade_times.dt.year.nunique())) if trades > 0 and not trade_times.empty else 1
    yearly_negative = 0
    if trades > 0 and not trade_times.empty and 'true_ret_24_dir_atr' in selected.columns:
        year_frame = pd.DataFrame({'year': selected['time'].dt.year, 'pnl': pnl}).dropna(subset=['year'])
        for _, group in year_frame.groupby('year'):
            if compute_pf(group['pnl'].to_numpy(dtype=np.float64)) < 1.0:
                yearly_negative += 1
    return {
        'candidate': candidate,
        'score_threshold': float(threshold),
        'trades': trades,
        'trades_per_year': float(trades / years) if years > 0 else 0.0,
        'pf': compute_pf(pnl) if trades > 0 else 0.0,
        'profit_concentration_top_10': compute_profit_concentration(pnl),
        'negative_year_slices': int(yearly_negative),
    }


def evaluate_candidates(frame: pd.DataFrame, target_coverages: list[float]) -> pd.DataFrame:
    rows: list[dict[str, float | int | str]] = []
    active = frame.loc[frame['signal'].astype(int) != 0].copy()
    if active.empty:
        return pd.DataFrame(columns=['candidate', 'score_threshold', 'trades', 'trades_per_year', 'pf', 'profit_concentration_top_10', 'negative_year_slices'])

    candidate_scores = {
        'ret24': active['pred_ret_24_dir_atr'].to_numpy(dtype=np.float64),
        'edge24': (
            active['pred_fav_24_atr'].to_numpy(dtype=np.float64)
            - active['pred_adv_24_atr'].to_numpy(dtype=np.float64)
        ),
        'path6_prob': (
            active['pred_path_6_prob_pos'].to_numpy(dtype=np.float64)
            - active['pred_path_6_prob_neg'].to_numpy(dtype=np.float64)
        ),
    }

    work = active.copy()
    for candidate, score in candidate_scores.items():
        work[candidate] = score
        for coverage in target_coverages:
            threshold = float(work[candidate].quantile(1.0 - coverage, interpolation='midpoint'))
            rows.append(summarize_candidate(work, candidate, threshold))
    return pd.DataFrame(rows)


def pick_candidate(table: pd.DataFrame, min_pf: float, target_trades_per_year: int) -> pd.Series:
    if table.empty:
        raise ValueError('Candidate table is empty')
    live = table.loc[
        (table['pf'] >= min_pf)
        & (table['trades_per_year'] >= target_trades_per_year)
        & (table['negative_year_slices'] == 0)
    ].copy()
    if live.empty:
        live = table.loc[(table['pf'] >= min_pf) & (table['negative_year_slices'] == 0)].copy()
    if live.empty:
        live = table.copy()
    live['trades_gap'] = (live['trades_per_year'] - float(target_trades_per_year)).abs()
    return live.sort_values(
        ['trades_gap', 'pf', 'profit_concentration_top_10', 'trades_per_year'],
        ascending=[True, False, True, False],
    ).iloc[0]


def run_benchmark(
    validation_csv: str | Path,
    test_csv: str | Path,
    output_dir: str | Path,
    min_pf: float = 2.0,
    target_trades_per_year: int = 40,
    target_coverages: list[float] | None = None,
) -> dict[str, object]:
    target_coverages = target_coverages or [0.25, 0.35, 0.45, 0.55, 0.65]
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    validation = load_prediction_frame(validation_csv)
    test = load_prediction_frame(test_csv)

    validation_grid = evaluate_candidates(validation, target_coverages)
    winner = pick_candidate(validation_grid, min_pf=min_pf, target_trades_per_year=target_trades_per_year)

    test_work = test.copy()
    if winner['candidate'] == 'ret24':
        test_work['ret24'] = test_work['pred_ret_24_dir_atr'].to_numpy(dtype=np.float64)
    elif winner['candidate'] == 'edge24':
        test_work['edge24'] = (
            test_work['pred_fav_24_atr'].to_numpy(dtype=np.float64)
            - test_work['pred_adv_24_atr'].to_numpy(dtype=np.float64)
        )
    else:
        test_work['path6_prob'] = (
            test_work['pred_path_6_prob_pos'].to_numpy(dtype=np.float64)
            - test_work['pred_path_6_prob_neg'].to_numpy(dtype=np.float64)
        )
    test_row = summarize_candidate(test_work, str(winner['candidate']), float(winner['score_threshold']))
    test_grid = pd.DataFrame([test_row])

    verdict = 'accept' if test_row['pf'] >= min_pf and test_row['negative_year_slices'] == 0 else 'reject'
    selected_candidate = {
        key: (value.item() if hasattr(value, 'item') else value)
        for key, value in winner.to_dict().items()
    }
    final_verdict = {
        'verdict': verdict,
        'min_pf': min_pf,
        'target_trades_per_year': target_trades_per_year,
        'validation_candidate': selected_candidate,
        'test_summary': test_row,
    }
    run_metadata = {
        'validation_csv': str(validation_csv),
        'test_csv': str(test_csv),
        'target_coverages': [float(value) for value in target_coverages],
    }

    validation_grid.to_csv(out_dir / 'validation_grid.csv', sep=';', index=False)
    test_grid.to_csv(out_dir / 'test_grid.csv', sep=';', index=False)
    (out_dir / 'selected_candidate.json').write_text(json.dumps(selected_candidate, ensure_ascii=False, indent=2), encoding='utf-8')
    (out_dir / 'final_verdict.json').write_text(json.dumps(final_verdict, ensure_ascii=False, indent=2), encoding='utf-8')
    (out_dir / 'run_metadata.json').write_text(json.dumps(run_metadata, ensure_ascii=False, indent=2), encoding='utf-8')
    return final_verdict


def parse_args():
    parser = argparse.ArgumentParser(description='Benchmark entry_path_v1 candidates toward higher trade frequency.')
    parser.add_argument('--validation-csv', required=True)
    parser.add_argument('--test-csv', required=True)
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--min-pf', type=float, default=2.0)
    parser.add_argument('--target-trades-per-year', type=int, default=40)
    parser.add_argument('--target-coverages', nargs='+', type=float, default=[0.25, 0.35, 0.45, 0.55, 0.65])
    return parser.parse_args()


def main():
    args = parse_args()
    verdict = run_benchmark(
        validation_csv=args.validation_csv,
        test_csv=args.test_csv,
        output_dir=args.output_dir,
        min_pf=args.min_pf,
        target_trades_per_year=args.target_trades_per_year,
        target_coverages=args.target_coverages,
    )
    print(json.dumps(verdict, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
