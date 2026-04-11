"""
N-boost benchmark for entry_path_v1_quantile.

Tries two approaches to increase trade count:
1. Relax filter: sweep lb quantile thresholds on validation.
2. Multi-seed ensemble: aggregate predictions across seeds.

Applies go/no-go gate to frozen test result.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from ML.benchmark_entry_path_v1_quantile_filter import (
    apply_conformal_correction,
    attach_baseline_score,
    build_rule_mask,
    compute_conformal_correction,
    compute_m_at_quantile,
    load_baseline_rule,
    load_prediction_frame,
    pick_winner,
    summarize_rule,
)
from ML.entry_path_trade_filter import compute_pf, run_sequential_check
from ML.entry_path_v1_quantile_ensemble import (
    aggregate_mean_quantile,
    load_seed_predictions,
    majority_vote,
)


GATE_MIN_TRADES = 30
GATE_MIN_PF = 2.0
GATE_MIN_YEAR_TRADES = 3
GATE_MIN_SAME_WINNER_RATIO = 0.8

QUANTILE_SWEEP = [0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50]
RULES_TO_SWEEP = ['lb_gt_m', 'lb_gt_0', 'lb_gt_m_width_le_w']


def evaluate_gate(
    n_trades: int,
    pf: float,
    negative_year_slices: int,
    same_winner_ratio: float,
) -> dict:
    reasons = []
    if n_trades < GATE_MIN_TRADES:
        reasons.append(f'n_trades={n_trades} < {GATE_MIN_TRADES}')
    if pf < GATE_MIN_PF:
        reasons.append(f'pf={pf:.2f} < {GATE_MIN_PF}')
    if negative_year_slices > 0:
        reasons.append(f'negative_year_slices={negative_year_slices} > 0')
    if same_winner_ratio < GATE_MIN_SAME_WINNER_RATIO:
        reasons.append(f'same_winner_ratio={same_winner_ratio:.2f} < {GATE_MIN_SAME_WINNER_RATIO}')

    return {
        'verdict': 'gate_pass' if not reasons else 'gate_fail',
        'n_trades': n_trades,
        'pf': pf,
        'negative_year_slices': negative_year_slices,
        'same_winner_ratio': same_winner_ratio,
        'reasons': reasons,
    }


def _ensure_datetime_time(frame: pd.DataFrame) -> pd.DataFrame:
    """Convert 'time' column to datetime if it is not already."""
    if 'time' in frame.columns and not pd.api.types.is_datetime64_any_dtype(frame['time']):
        frame = frame.copy()
        frame['time'] = pd.to_datetime(frame['time'], format='%Y.%m.%d %H:%M', errors='coerce')
    return frame


def run_relax_sweep(
    validation_frame: pd.DataFrame,
    baseline_validation: pd.DataFrame,
    baseline_threshold: float,
    alpha: float = 0.10,
    min_trades: int = 10,
) -> pd.DataFrame:
    validation_frame = _ensure_datetime_time(validation_frame)
    baseline_validation = _ensure_datetime_time(baseline_validation)
    validation = attach_baseline_score(validation_frame, baseline_validation)
    validation['baseline_selected'] = (
        (validation['signal'].to_numpy() != 0)
        & (validation['baseline_score'].to_numpy(dtype=np.float64) >= baseline_threshold)
    )

    selected = validation.loc[validation['baseline_selected']].copy()
    correction = compute_conformal_correction(
        selected['true_ret_24_dir_atr'].to_numpy(dtype=np.float64),
        selected['pred_ret_24_q10'].to_numpy(dtype=np.float64),
        selected['pred_ret_24_q90'].to_numpy(dtype=np.float64),
        alpha=alpha,
    )
    validation = apply_conformal_correction(validation, correction)

    rows = []
    for q in QUANTILE_SWEEP:
        m = compute_m_at_quantile(validation, q)
        w = float(validation.loc[validation['baseline_selected'], 'width'].median()) if validation['baseline_selected'].any() else 0.0
        for rule in RULES_TO_SWEEP:
            candidate = f'{rule}_q{int(q*100):02d}'
            row = summarize_rule(validation, candidate=candidate, rule=rule, m=m, w=w)
            row['quantile'] = q
            row['correction'] = correction
            rows.append(row)

    rows.append({
        **summarize_rule(validation, candidate='baseline', rule='baseline', m=0.0, w=0.0),
        'quantile': None,
        'correction': correction,
    })

    return pd.DataFrame(rows)


def run_ensemble_benchmark(
    seed_dirs: list[str | Path],
    split: str,
    baseline_frame: pd.DataFrame,
    baseline_threshold: float,
    alpha: float = 0.10,
    min_trades: int = 10,
) -> pd.DataFrame:
    frames = [_ensure_datetime_time(load_seed_predictions(sd, split=split)) for sd in seed_dirs]
    baseline_frame = _ensure_datetime_time(baseline_frame)

    # Mean quantile
    mean_frame = aggregate_mean_quantile(frames)
    mean_validation = attach_baseline_score(mean_frame, baseline_frame)
    mean_validation['baseline_selected'] = (
        (mean_validation['signal'].to_numpy() != 0)
        & (mean_validation['baseline_score'].to_numpy(dtype=np.float64) >= baseline_threshold)
    )
    selected = mean_validation.loc[mean_validation['baseline_selected']].copy()
    correction = compute_conformal_correction(
        selected['true_ret_24_dir_atr'].to_numpy(dtype=np.float64),
        selected['pred_ret_24_q10'].to_numpy(dtype=np.float64),
        selected['pred_ret_24_q90'].to_numpy(dtype=np.float64),
        alpha=alpha,
    )
    mean_validation = apply_conformal_correction(mean_validation, correction)
    m = compute_m_at_quantile(mean_validation, 0.5)
    w = float(mean_validation.loc[mean_validation['baseline_selected'], 'width'].median()) if mean_validation['baseline_selected'].any() else 0.0

    rows = []
    for rule in RULES_TO_SWEEP:
        candidate = f'ensemble_mean_{rule}'
        row = summarize_rule(mean_validation, candidate=candidate, rule=rule, m=m, w=w)
        row['method'] = 'mean_quantile'
        row['correction'] = correction
        rows.append(row)

    # Majority vote
    for quorum in [3, 4]:
        per_seed_masks = []
        for f in frames:
            sv = attach_baseline_score(f, baseline_frame)
            sv['baseline_selected'] = (
                (sv['signal'].to_numpy() != 0)
                & (sv['baseline_score'].to_numpy(dtype=np.float64) >= baseline_threshold)
            )
            sel = sv.loc[sv['baseline_selected']].copy()
            c = compute_conformal_correction(
                sel['true_ret_24_dir_atr'].to_numpy(dtype=np.float64),
                sel['pred_ret_24_q10'].to_numpy(dtype=np.float64),
                sel['pred_ret_24_q90'].to_numpy(dtype=np.float64),
                alpha=alpha,
            )
            sv = apply_conformal_correction(sv, c)
            sm = compute_m_at_quantile(sv, 0.5)
            per_seed_masks.append(build_rule_mask(sv, rule='lb_gt_m', m=sm, w=0.0))

        vote_mask = majority_vote(per_seed_masks, quorum=quorum)
        pnl = mean_validation.loc[vote_mask, 'true_ret_24_dir_atr'].to_numpy(dtype=np.float64)
        trades = int(vote_mask.sum())
        pf = compute_pf(pnl) if trades > 0 else 0.0
        rows.append({
            'candidate': f'ensemble_vote_q{quorum}',
            'rule': 'majority_vote',
            'method': 'majority_vote',
            'trades': trades,
            'pf': pf,
            'win_rate': float((pnl > 0).mean()) if trades > 0 else 0.0,
            'mean_pnl_atr': float(pnl.mean()) if trades > 0 else 0.0,
            'm': 0.0,
            'w': 0.0,
            'coverage': 0.0,
            'median_interval_width': 0.0,
            'gross_profit': float(pnl[pnl > 0].sum()) if trades > 0 else 0.0,
            'gross_loss': float(-pnl[pnl < 0].sum()) if trades > 0 else 0.0,
            'correction': correction,
        })

    return pd.DataFrame(rows)


def count_negative_year_slices_from_trades(
    test_frame: pd.DataFrame,
    selected_mask: pd.Series,
    min_year_trades: int = GATE_MIN_YEAR_TRADES,
) -> int:
    selected = test_frame.loc[selected_mask].copy()
    if selected.empty or 'time' not in selected.columns:
        return 0
    selected['time'] = pd.to_datetime(selected['time'], format='%Y.%m.%d %H:%M', errors='coerce')
    selected['year'] = selected['time'].dt.year
    total = 0
    for _, group in selected.groupby('year'):
        if len(group) < min_year_trades:
            continue
        pnl = group['true_ret_24_dir_atr'].to_numpy(dtype=np.float64)
        if pnl.sum() < 0:
            total += 1
    return total


def run_full_benchmark(
    root_dir: str | Path,
    seeds: list[int],
    baseline_rule: str | Path,
    output_dir: str | Path,
    alpha: float = 0.10,
    min_trades: int = 10,
) -> dict:
    root = Path(root_dir)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    baseline_data = load_baseline_rule(baseline_rule)
    baseline_threshold = float(baseline_data['winner'].get('score_threshold', 0.0))
    baseline_validation = load_prediction_frame(baseline_data['validation_csv'])
    baseline_test = load_prediction_frame(baseline_data['test_csv'])
    hold_bars = int(baseline_data.get('sequential_hold_bars', 24))

    seed_dirs = [root / f'seed_{s:03d}' for s in seeds]
    primary_seed_dir = seed_dirs[0]

    # Step 1: Relax filter sweep on validation (primary seed)
    val_frame = _ensure_datetime_time(load_seed_predictions(primary_seed_dir, split='validation'))
    relax_table = run_relax_sweep(val_frame, baseline_validation, baseline_threshold, alpha, min_trades)

    # Step 2: Ensemble sweep on validation
    ensemble_table = run_ensemble_benchmark(seed_dirs, 'validation', baseline_validation, baseline_threshold, alpha, min_trades)

    # Combine and pick best on validation
    combined = pd.concat([relax_table, ensemble_table], ignore_index=True)
    combined_path = out / 'n_boost_validation_sweep.csv'
    combined.to_csv(combined_path, sep=';', index=False)

    best = pick_winner(combined, min_trades=min_trades).to_dict()

    # Frozen test
    is_ensemble = str(best.get('method', '')) == 'mean_quantile'

    if is_ensemble:
        test_frame = aggregate_mean_quantile([_ensure_datetime_time(load_seed_predictions(sd, split='test')) for sd in seed_dirs])
    else:
        test_frame = _ensure_datetime_time(load_seed_predictions(primary_seed_dir, split='test'))

    test = attach_baseline_score(test_frame, baseline_test)
    test['baseline_selected'] = (
        (test['signal'].to_numpy() != 0)
        & (test['baseline_score'].to_numpy(dtype=np.float64) >= baseline_threshold)
    )
    correction = float(best.get('correction', 0.0))
    test = apply_conformal_correction(test, correction)

    m = float(best.get('m', 0.0))
    w = float(best.get('w', 0.0))
    rule = best.get('rule', 'baseline')

    frozen_test = summarize_rule(test, candidate=best['candidate'], rule=rule, m=m, w=w)
    frozen_mask = build_rule_mask(test, rule=rule, m=m, w=w)
    sequential = run_sequential_check(test, frozen_mask, hold_bars=hold_bars)

    # Multi-seed stability (for relax variant)
    if not is_ensemble:
        same_count = 0
        for sd in seed_dirs:
            sd_val = _ensure_datetime_time(load_seed_predictions(sd, split='validation'))
            sd_table = run_relax_sweep(sd_val, baseline_validation, baseline_threshold, alpha, min_trades)
            sd_best = pick_winner(sd_table, min_trades=min_trades)
            if sd_best['candidate'] == best['candidate']:
                same_count += 1
        same_winner_ratio = same_count / len(seeds)
    else:
        same_winner_ratio = 1.0

    # Negative year slices (on best candidate's frozen test trades)
    neg_year_slices = count_negative_year_slices_from_trades(test, frozen_mask)

    # Gate
    gate = evaluate_gate(
        n_trades=int(frozen_test['trades']),
        pf=float(frozen_test['pf']),
        negative_year_slices=neg_year_slices,
        same_winner_ratio=same_winner_ratio,
    )

    payload = {
        'best_candidate': best,
        'frozen_test': frozen_test,
        'sequential': sequential,
        'gate': gate,
        'is_ensemble': is_ensemble,
        'seeds': seeds,
        'sweep_path': str(combined_path),
    }

    result_path = out / 'n_boost_result.json'
    result_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding='utf-8')

    return payload


def parse_args():
    parser = argparse.ArgumentParser(description='N-boost benchmark for entry_path_v1_quantile.')
    parser.add_argument('--root-dir', required=True)
    parser.add_argument('--seeds', type=int, nargs='+', required=True)
    parser.add_argument('--baseline-rule', required=True)
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--alpha', type=float, default=0.10)
    parser.add_argument('--min-trades', type=int, default=10)
    return parser.parse_args()


def main():
    args = parse_args()
    payload = run_full_benchmark(
        root_dir=args.root_dir,
        seeds=args.seeds,
        baseline_rule=args.baseline_rule,
        output_dir=args.output_dir,
        alpha=args.alpha,
        min_trades=args.min_trades,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return payload


if __name__ == '__main__':
    main()
