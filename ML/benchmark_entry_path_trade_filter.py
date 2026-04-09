import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from ML.entry_path_trade_filter import apply_candidate_b_score
from ML.entry_path_trade_filter import build_candidate_a_score
from ML.entry_path_trade_filter import build_trade_filter_report_markdown
from ML.entry_path_trade_filter import evaluate_frozen_threshold
from ML.entry_path_trade_filter import evaluate_score_grid
from ML.entry_path_trade_filter import fit_candidate_b_score
from ML.entry_path_trade_filter import pick_best_slice
from ML.entry_path_trade_filter import run_sequential_check


DEFAULT_VALIDATION_CSV = Path('ML/reports/entry_path_v1_validation_predictions.csv')
DEFAULT_TEST_CSV = Path('ML/reports/entry_path_test_predictions.csv')
DEFAULT_OUTPUT_DIR = Path('ML/reports')
DEFAULT_COVERAGE_GRID = [0.65, 0.68, 0.70, 0.72, 0.75]


def load_prediction_frame(path) -> pd.DataFrame:
    frame = pd.read_csv(Path(path), sep=';')
    frame['time'] = pd.to_datetime(frame['time'], format='%Y.%m.%d %H:%M', errors='coerce')
    return frame


def run_benchmark(
    validation_csv,
    test_csv,
    output_dir,
    coverage_grid,
    min_period_trades=10,
    sequential_hold_bars=24,
):
    validation_path = Path(validation_csv)
    test_path = Path(test_csv)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    validation_frame = load_prediction_frame(validation_path)
    test_frame = load_prediction_frame(test_path)

    validation_score_a = build_candidate_a_score(validation_frame)
    test_score_a = build_candidate_a_score(test_frame)

    candidate_b_scaler = fit_candidate_b_score(validation_frame, include_path6=True)
    validation_score_b = apply_candidate_b_score(validation_frame, candidate_b_scaler, include_path6=True)
    test_score_b = apply_candidate_b_score(test_frame, candidate_b_scaler, include_path6=True)

    candidate_b_no_path6_scaler = fit_candidate_b_score(validation_frame, include_path6=False)
    validation_score_b_no_path6 = apply_candidate_b_score(
        validation_frame,
        candidate_b_no_path6_scaler,
        include_path6=False,
    )
    test_score_b_no_path6 = apply_candidate_b_score(
        test_frame,
        candidate_b_no_path6_scaler,
        include_path6=False,
    )

    validation_summary = pd.concat(
        [
            evaluate_score_grid(
                frame=validation_frame,
                score=validation_score_a,
                candidate='A',
                target_coverages=coverage_grid,
                min_period_trades=min_period_trades,
            ),
            evaluate_score_grid(
                frame=validation_frame,
                score=validation_score_b,
                candidate='B',
                target_coverages=coverage_grid,
                min_period_trades=min_period_trades,
            ),
            evaluate_score_grid(
                frame=validation_frame,
                score=validation_score_b_no_path6,
                candidate='B_no_path6',
                target_coverages=coverage_grid,
                min_period_trades=min_period_trades,
            ),
        ],
        ignore_index=True,
    )

    winner = pick_best_slice(validation_summary).to_dict()
    winner_candidate = winner['candidate']
    winner_score = {
        'A': test_score_a,
        'B': test_score_b,
        'B_no_path6': test_score_b_no_path6,
    }[winner_candidate]
    frozen_threshold = float(winner['score_threshold'])
    target_coverage = float(winner['target_coverage'])

    test_summary = evaluate_frozen_threshold(
        frame=test_frame,
        score=winner_score,
        candidate=winner_candidate,
        threshold=frozen_threshold,
        target_coverage=target_coverage,
        min_period_trades=min_period_trades,
    )

    winner_score_series = pd.Series(np.asarray(winner_score, dtype=np.float64), index=test_frame.index, dtype='float64')
    selected_mask = winner_score_series >= frozen_threshold
    selected_mask.loc[test_frame['signal'].to_numpy() == 0] = False
    sequential_summary = run_sequential_check(
        frame=test_frame,
        selected_mask=selected_mask,
        hold_bars=sequential_hold_bars,
    )

    validation_summary_path = output_path / 'entry_path_trade_filter_validation_summary.csv'
    test_summary_path = output_path / 'entry_path_trade_filter_test_summary.csv'
    rule_path = output_path / 'entry_path_trade_filter_selected_rule.json'
    report_path = output_path / 'entry_path_trade_filter_report.md'

    validation_summary.to_csv(validation_summary_path, sep=';', index=False)
    test_summary.to_csv(test_summary_path, sep=';', index=False)

    payload = {
        'winner': winner,
        'coverage_grid': [float(value) for value in coverage_grid],
        'validation_csv': str(validation_path),
        'test_csv': str(test_path),
        'sequential_hold_bars': int(sequential_hold_bars),
        'min_period_trades': int(min_period_trades),
        'validation_summary_path': str(validation_summary_path),
        'test_summary_path': str(test_summary_path),
        'sequential_summary': sequential_summary,
    }
    rule_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')

    report = build_trade_filter_report_markdown(
        validation_best=winner,
        test_row=test_summary.iloc[0].to_dict(),
        sequential_summary=sequential_summary,
        rule_path=str(rule_path),
    )
    report_path.write_text(report, encoding='utf-8')

    return payload


def parse_args():
    parser = argparse.ArgumentParser(description='Benchmark entry path trade filter candidates on validation/test artifacts.')
    parser.add_argument('--validation-csv', default=str(DEFAULT_VALIDATION_CSV))
    parser.add_argument('--test-csv', default=str(DEFAULT_TEST_CSV))
    parser.add_argument('--output-dir', default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument('--coverage-grid', nargs='+', type=float, default=DEFAULT_COVERAGE_GRID)
    parser.add_argument('--min-period-trades', type=int, default=10)
    parser.add_argument('--sequential-hold-bars', type=int, default=24)
    return parser.parse_args()


def main():
    args = parse_args()
    payload = run_benchmark(
        validation_csv=args.validation_csv,
        test_csv=args.test_csv,
        output_dir=args.output_dir,
        coverage_grid=args.coverage_grid,
        min_period_trades=args.min_period_trades,
        sequential_hold_bars=args.sequential_hold_bars,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
