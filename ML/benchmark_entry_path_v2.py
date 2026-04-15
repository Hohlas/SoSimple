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
    gross_profit = float(positive.sum())
    if gross_profit <= 0.0:
        return 1.0
    top_k = max(1, int(np.ceil(positive.size * top_frac)))
    return float(positive[:top_k].sum() / gross_profit)


def compute_equity_smoothness(pnl: np.ndarray) -> tuple[float, float]:
    pnl = np.asarray(pnl, dtype=np.float64)
    if pnl.size == 0:
        return 0.0, 0.0
    equity = np.cumsum(pnl)
    running_peak = np.maximum.accumulate(equity)
    drawdown = np.maximum(0.0, running_peak - equity)
    ulcer_index = float(np.sqrt(np.mean(np.square(drawdown)))) if drawdown.size > 0 else 0.0
    max_drawdown = float(drawdown.max()) if drawdown.size > 0 else 0.0
    return ulcer_index, max_drawdown


def _safe_ratio(numerator: pd.Series, denominator: pd.Series, eps: float = 1e-6) -> pd.Series:
    return numerator / (denominator.abs() + eps)


def build_candidate_scores(frame: pd.DataFrame) -> dict[str, pd.Series]:
    ret12 = frame['pred_ret_12_dir_atr'].astype(float)
    ret24 = frame['pred_ret_24_dir_atr'].astype(float)
    fav12 = frame['pred_fav_12_atr'].astype(float)
    adv12 = frame['pred_adv_12_atr'].astype(float)
    fav24 = frame['pred_fav_24_atr'].astype(float)
    adv24 = frame['pred_adv_24_atr'].astype(float)
    edge12 = fav12 - adv12
    edge24 = fav24 - adv24
    nonflat_confidence = 1.0 - frame['pred_path_6_prob_flat'].astype(float)

    scores: dict[str, pd.Series] = {
        'ret24_only': ret24,
        'ret24_over_adv24': _safe_ratio(ret24, adv24),
        'fav24_over_adv24': _safe_ratio(fav24, adv24),
        'ret24_nonflat_confidence': ret24 * nonflat_confidence,
    }

    for weight in (0.35, 0.50, 0.65):
        code = int(round(weight * 100))
        scores[f'ret12_plus_ret24_w{code:02d}'] = (1.0 - weight) * ret12 + weight * ret24
        scores[f'edge12_plus_edge24_w{code:02d}'] = (1.0 - weight) * edge12 + weight * edge24

    for lam in (0.5, 1.0, 1.5):
        code = int(round(lam * 10))
        scores[f'ret24_minus_adv24_l{code:02d}'] = ret24 - lam * adv24
        scores[f'fav24_minus_adv24_l{code:02d}'] = fav24 - lam * adv24

    for alpha, beta in ((0.5, 1.0), (1.0, 1.0), (0.5, 1.5)):
        acode = int(round(alpha * 10))
        bcode = int(round(beta * 10))
        scores[f'ret24_fav12_adv12_a{acode:02d}_b{bcode:02d}'] = ret24 + alpha * fav12 - beta * adv12

    return scores


def candidate_family(name: str) -> str:
    if name == 'ret24_only':
        return 'ret24_only'
    if name.startswith('ret12_plus_ret24'):
        return 'ret12_plus_ret24'
    if name.startswith('edge12_plus_edge24'):
        return 'edge12_plus_edge24'
    if name.startswith('ret24_minus_adv24'):
        return 'ret24_minus_adv24'
    if name.startswith('fav24_minus_adv24'):
        return 'fav24_minus_adv24'
    if name == 'ret24_over_adv24':
        return 'ret24_over_adv24'
    if name == 'fav24_over_adv24':
        return 'fav24_over_adv24'
    if name.startswith('ret24_fav12_adv12'):
        return 'ret24_fav12_adv12'
    if name == 'ret24_nonflat_confidence':
        return 'ret24_nonflat_confidence'
    return 'other'


def summarize_candidate(frame: pd.DataFrame, candidate: str, threshold: float) -> dict[str, float | int | str]:
    active = frame.loc[frame['signal'].astype(int) != 0].copy()
    selected = active.loc[active[candidate] >= threshold].copy()
    selected = selected.sort_values('time')

    pnl = (
        selected['true_ret_24_dir_atr'].to_numpy(dtype=np.float64)
        if 'true_ret_24_dir_atr' in selected.columns
        else np.array([], dtype=np.float64)
    )
    trades = int(len(selected))
    trade_times = selected['time'].dropna()
    years = int(max(1, trade_times.dt.year.nunique())) if trades > 0 and not trade_times.empty else 1
    yearly_negative = 0
    if trades > 0 and not trade_times.empty and 'true_ret_24_dir_atr' in selected.columns:
        yearly = pd.DataFrame({'year': selected['time'].dt.year, 'pnl': pnl}).dropna(subset=['year'])
        for _, group in yearly.groupby('year'):
            if compute_pf(group['pnl'].to_numpy(dtype=np.float64)) < 1.0:
                yearly_negative += 1
    ulcer_index, max_drawdown = compute_equity_smoothness(pnl)
    return {
        'candidate': candidate,
        'family': candidate_family(candidate),
        'score_threshold': float(threshold),
        'trades': trades,
        'trades_per_year': float(trades / years) if years > 0 else 0.0,
        'pf': compute_pf(pnl) if trades > 0 else 0.0,
        'win_rate': float((pnl > 0).mean()) if trades > 0 else 0.0,
        'mean_pnl_atr': float(pnl.mean()) if trades > 0 else 0.0,
        'profit_concentration_top_10': compute_profit_concentration(pnl),
        'negative_year_slices': int(yearly_negative),
        'ulcer_index_atr': ulcer_index,
        'max_drawdown_atr': max_drawdown,
    }


def evaluate_candidates(frame: pd.DataFrame, target_coverages: list[float]) -> pd.DataFrame:
    rows: list[dict[str, float | int | str]] = []
    active = frame.loc[frame['signal'].astype(int) != 0].copy()
    if active.empty:
        return pd.DataFrame(
            columns=[
                'candidate', 'family', 'score_threshold', 'target_coverage', 'trades', 'trades_per_year',
                'pf', 'win_rate', 'mean_pnl_atr', 'profit_concentration_top_10', 'negative_year_slices',
                'ulcer_index_atr', 'max_drawdown_atr',
            ]
        )

    work = active.copy()
    for candidate, score in build_candidate_scores(active).items():
        work[candidate] = score.to_numpy(dtype=np.float64)
        for coverage in target_coverages:
            threshold = float(work[candidate].quantile(1.0 - coverage, interpolation='midpoint'))
            row = summarize_candidate(work, candidate=candidate, threshold=threshold)
            row['target_coverage'] = float(coverage)
            rows.append(row)
    return pd.DataFrame(rows)


def pick_candidate(table: pd.DataFrame, min_pf: float, target_trades_per_year: int) -> pd.Series:
    if table.empty:
        raise ValueError('Candidate table is empty')

    live = table.copy()
    live['trades_gap'] = (live['trades_per_year'] - float(target_trades_per_year)).abs()

    def tier(row: pd.Series) -> int:
        if row['pf'] >= min_pf and row['negative_year_slices'] == 0:
            return 3
        if row['pf'] > 1.0 and row['negative_year_slices'] <= 1:
            return 2
        if row['pf'] > 1.0:
            return 1
        return 0

    live['selection_tier'] = live.apply(tier, axis=1)

    for column in ('ulcer_index_atr', 'max_drawdown_atr', 'profit_concentration_top_10'):
        if column not in live.columns:
            live[column] = float('inf')

    return live.sort_values(
        [
            'selection_tier',
            'pf',
            'negative_year_slices',
            'ulcer_index_atr',
            'profit_concentration_top_10',
            'trades_gap',
            'max_drawdown_atr',
            'trades_per_year',
        ],
        ascending=[False, False, True, True, True, True, True, False],
    ).iloc[0]


def build_family_summary(table: pd.DataFrame) -> pd.DataFrame:
    if table.empty:
        return pd.DataFrame(columns=['family', 'rows', 'best_pf', 'best_trades_per_year', 'best_negative_year_slices'])
    summary = table.sort_values('pf', ascending=False).groupby('family', as_index=False).first()
    summary = summary[['family', 'candidate', 'pf', 'trades_per_year', 'negative_year_slices', 'ulcer_index_atr', 'profit_concentration_top_10']]
    return summary.rename(
        columns={
            'candidate': 'best_candidate',
            'pf': 'best_pf',
            'trades_per_year': 'best_trades_per_year',
            'negative_year_slices': 'best_negative_year_slices',
            'ulcer_index_atr': 'best_ulcer_index_atr',
            'profit_concentration_top_10': 'best_profit_concentration_top_10',
        }
    )


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
    validation_family_summary = build_family_summary(validation_grid)
    winner = pick_candidate(validation_grid, min_pf=min_pf, target_trades_per_year=target_trades_per_year)

    test_scores = build_candidate_scores(test)
    test_work = test.copy()
    test_work[str(winner['candidate'])] = test_scores[str(winner['candidate'])].to_numpy(dtype=np.float64)
    test_row = summarize_candidate(test_work, str(winner['candidate']), float(winner['score_threshold']))
    test_grid = pd.DataFrame([test_row])

    verdict = 'accept' if test_row['pf'] >= min_pf and test_row['negative_year_slices'] == 0 else 'reject'
    selected_candidate = {
        key: (value.item() if hasattr(value, 'item') else value)
        for key, value in winner.to_dict().items()
    }
    diagnostics = {
        'validation_rows': int(len(validation_grid)),
        'families': sorted(validation_grid['family'].unique().tolist()),
        'validation_rows_pf_gt_1': int((validation_grid['pf'] > 1.0).sum()),
        'validation_rows_pf_gt_1_2': int((validation_grid['pf'] > 1.2).sum()),
        'validation_rows_pf_gt_1_5': int((validation_grid['pf'] > 1.5).sum()),
    }
    final_verdict = {
        'verdict': verdict,
        'min_pf': min_pf,
        'target_trades_per_year': target_trades_per_year,
        'validation_candidate': selected_candidate,
        'test_summary': test_row,
        'diagnostics': diagnostics,
    }
    run_metadata = {
        'validation_csv': str(validation_csv),
        'test_csv': str(test_csv),
        'target_coverages': [float(value) for value in target_coverages],
        'candidate_count': int(len(build_candidate_scores(validation))),
    }

    validation_grid.to_csv(out_dir / 'validation_grid.csv', sep=';', index=False)
    validation_family_summary.to_csv(out_dir / 'validation_family_summary.csv', sep=';', index=False)
    test_grid.to_csv(out_dir / 'test_grid.csv', sep=';', index=False)
    (out_dir / 'selected_candidate.json').write_text(json.dumps(selected_candidate, ensure_ascii=False, indent=2), encoding='utf-8')
    (out_dir / 'final_verdict.json').write_text(json.dumps(final_verdict, ensure_ascii=False, indent=2), encoding='utf-8')
    (out_dir / 'run_metadata.json').write_text(json.dumps(run_metadata, ensure_ascii=False, indent=2), encoding='utf-8')
    return final_verdict


def parse_args():
    parser = argparse.ArgumentParser(description='Validation-first diagnostic benchmark for entry_path_v1 selection layer.')
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
