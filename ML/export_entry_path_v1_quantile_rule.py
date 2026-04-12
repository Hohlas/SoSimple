"""Export production rule for entry_path_v1_quantile.

Computes per-seed conformal correction + m(quantile) + median interval width,
aggregates to median across seeds, and writes a production rule JSON that MT4
and downstream tooling can consume.
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
    summarize_rule,
)
from ML.entry_path_trade_filter import run_sequential_check
from ML.entry_path_v1_quantile_ensemble import load_seed_predictions


def _ensure_datetime_time(frame: pd.DataFrame) -> pd.DataFrame:
    if 'time' in frame.columns and not pd.api.types.is_datetime64_any_dtype(frame['time']):
        frame = frame.copy()
        frame['time'] = pd.to_datetime(frame['time'], format='%Y.%m.%d %H:%M', errors='coerce')
    return frame


def compute_seed_params(
    seed_dir: str | Path,
    baseline_frame: pd.DataFrame,
    baseline_threshold: float,
    quantile: float,
    alpha: float = 0.10,
) -> dict:
    seed_dir = Path(seed_dir)
    val = _ensure_datetime_time(load_seed_predictions(seed_dir, split='validation'))
    baseline_frame = _ensure_datetime_time(baseline_frame)
    joined = attach_baseline_score(val, baseline_frame)
    joined['baseline_selected'] = (
        (joined['signal'].to_numpy() != 0)
        & (joined['baseline_score'].to_numpy(dtype=np.float64) >= baseline_threshold)
    )
    selected = joined.loc[joined['baseline_selected']].copy()
    correction = compute_conformal_correction(
        selected['true_ret_24_dir_atr'].to_numpy(dtype=np.float64),
        selected['pred_ret_24_q10'].to_numpy(dtype=np.float64),
        selected['pred_ret_24_q90'].to_numpy(dtype=np.float64),
        alpha=alpha,
    )
    joined = apply_conformal_correction(joined, correction)
    m = compute_m_at_quantile(joined, quantile)
    w = float(joined.loc[joined['baseline_selected'], 'width'].median()) if joined['baseline_selected'].any() else 0.0
    return {
        'seed_dir': str(seed_dir),
        'correction': correction,
        'm': m,
        'w': w,
    }


def _summarize_test(
    seed_dir: Path,
    baseline_test: pd.DataFrame,
    baseline_threshold: float,
    rule: str,
    m: float,
    w: float,
    correction: float,
    hold_bars: int,
    candidate: str,
) -> tuple[dict, dict]:
    test = _ensure_datetime_time(load_seed_predictions(seed_dir, split='test'))
    baseline_test = _ensure_datetime_time(baseline_test)
    joined = attach_baseline_score(test, baseline_test)
    joined['baseline_selected'] = (
        (joined['signal'].to_numpy() != 0)
        & (joined['baseline_score'].to_numpy(dtype=np.float64) >= baseline_threshold)
    )
    joined = apply_conformal_correction(joined, correction)
    frozen = summarize_rule(joined, candidate=candidate, rule=rule, m=m, w=w)
    mask = build_rule_mask(joined, rule=rule, m=m, w=w)
    sequential = run_sequential_check(joined, mask, hold_bars=hold_bars)
    return frozen, sequential


def export_rule(
    root_dir: str | Path,
    seeds: list[int],
    baseline_rule_path: str | Path,
    rule: str,
    quantile: float,
    alpha: float,
    output_path: str | Path,
    n_boost_result_path: str | Path | None = None,
) -> dict:
    root = Path(root_dir)
    output_path = Path(output_path)

    baseline_data = load_baseline_rule(baseline_rule_path)
    baseline_threshold = float(baseline_data['winner'].get('score_threshold', 0.0))
    baseline_validation = load_prediction_frame(baseline_data['validation_csv'])
    baseline_test = load_prediction_frame(baseline_data['test_csv'])
    hold_bars = int(baseline_data.get('sequential_hold_bars', 24))

    seed_dirs = [root / f'seed_{s:03d}' for s in seeds]
    per_seed = []
    for sd, seed in zip(seed_dirs, seeds):
        params = compute_seed_params(
            seed_dir=sd,
            baseline_frame=baseline_validation,
            baseline_threshold=baseline_threshold,
            quantile=quantile,
            alpha=alpha,
        )
        params['seed'] = seed
        per_seed.append(params)

    median_m = float(pd.Series([p['m'] for p in per_seed]).median())
    median_w = float(pd.Series([p['w'] for p in per_seed]).median())
    median_correction = float(pd.Series([p['correction'] for p in per_seed]).median())

    candidate = f'{rule}_q{int(quantile * 100):02d}'
    frozen, sequential = _summarize_test(
        seed_dir=seed_dirs[0],
        baseline_test=baseline_test,
        baseline_threshold=baseline_threshold,
        rule=rule,
        m=median_m,
        w=median_w,
        correction=median_correction,
        hold_bars=hold_bars,
        candidate=candidate,
    )

    n_boost_payload = None
    if n_boost_result_path is not None:
        n_boost_payload = json.loads(Path(n_boost_result_path).read_text(encoding='utf-8'))

    winner = {
        'candidate': candidate,
        'rule': rule,
        'quantile': quantile,
        'm': median_m,
        'w': median_w,
        'correction': median_correction,
        'alpha': alpha,
        'trades': frozen['trades'],
        'pf': frozen['pf'],
        'win_rate': frozen['win_rate'],
        'mean_pnl_atr': frozen['mean_pnl_atr'],
        'coverage': frozen['coverage'],
        'median_interval_width': frozen['median_interval_width'],
        'gross_profit': frozen['gross_profit'],
        'gross_loss': frozen['gross_loss'],
    }

    payload = {
        'winner': winner,
        'baseline_rule_path': str(baseline_rule_path),
        'baseline_threshold': baseline_threshold,
        'seeds': list(seeds),
        'per_seed_params': per_seed,
        'root_dir': str(root),
        'sequential_hold_bars': hold_bars,
        'sequential_summary': sequential,
        'frozen_test': frozen,
    }
    if n_boost_payload is not None:
        payload['n_boost_gate'] = n_boost_payload.get('gate')
        payload['n_boost_result_path'] = str(n_boost_result_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding='utf-8')
    return payload


def parse_args():
    parser = argparse.ArgumentParser(description='Export production rule JSON for entry_path_v1_quantile.')
    parser.add_argument('--root-dir', required=True)
    parser.add_argument('--seeds', type=int, nargs='+', required=True)
    parser.add_argument('--baseline-rule', required=True)
    parser.add_argument('--rule', required=True)
    parser.add_argument('--quantile', type=float, required=True)
    parser.add_argument('--alpha', type=float, default=0.10)
    parser.add_argument('--output', required=True)
    parser.add_argument('--n-boost-result', default=None)
    return parser.parse_args()


def main():
    args = parse_args()
    payload = export_rule(
        root_dir=args.root_dir,
        seeds=args.seeds,
        baseline_rule_path=args.baseline_rule,
        rule=args.rule,
        quantile=args.quantile,
        alpha=args.alpha,
        output_path=args.output,
        n_boost_result_path=args.n_boost_result,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return payload


if __name__ == '__main__':
    main()
