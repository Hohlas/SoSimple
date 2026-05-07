from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from ML.benchmark_entry_path_v1_quantile_filter import run_benchmark as run_quantile_benchmark
from ML.entry_path_trade_filter import build_candidate_a_score
from ML.entry_path_trade_filter import build_trade_filter_report_markdown
from ML.entry_path_trade_filter import evaluate_frozen_threshold
from ML.entry_path_trade_filter import evaluate_score_grid
from ML.entry_path_trade_filter import run_sequential_check
from ML.entry_path_v1_quantile_task import ENTRY_PATH_V1_QUANTILE_TARGET
from ML.export_entry_path_predictions import export_predictions
from ML.train import DEFAULTS
from ML.train import train_model


DEFAULT_BASELINE_ROOT = Path('ML/reports/entry_path_v1_live_safe_xauusd_no_predict_pool_server_multiseed')
DEFAULT_OUTPUT_DIR = Path('ML/reports/entry_path_v1_quantile_live_safe_cpu_baseline')
DEFAULT_BASELINE_COVERAGE = 0.075


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
    if isinstance(value, float) and not np.isfinite(value):
        return str(value)
    return value


def seed_slug(seed: int) -> str:
    return f'seed_{int(seed):03d}'


def _load_prediction_frame(path: str | Path) -> pd.DataFrame:
    frame = pd.read_csv(Path(path), sep=';')
    frame['time'] = pd.to_datetime(frame['time'], format='%Y.%m.%d %H:%M', errors='coerce')
    return frame


def build_baseline_a_rule(
    *,
    validation_csv: str | Path,
    test_csv: str | Path,
    output_dir: str | Path,
    target_coverage: float = DEFAULT_BASELINE_COVERAGE,
    min_period_trades: int = 10,
    sequential_hold_bars: int = 24,
) -> dict[str, object]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    validation_path = Path(validation_csv)
    test_path = Path(test_csv)

    validation_frame = _load_prediction_frame(validation_path)
    test_frame = _load_prediction_frame(test_path)
    validation_score = build_candidate_a_score(validation_frame)
    test_score = build_candidate_a_score(test_frame)

    validation_summary = evaluate_score_grid(
        frame=validation_frame,
        score=validation_score,
        candidate='A',
        target_coverages=[float(target_coverage)],
        min_period_trades=min_period_trades,
    )
    winner = validation_summary.iloc[0].to_dict()
    threshold = float(winner['score_threshold'])

    test_summary = evaluate_frozen_threshold(
        frame=test_frame,
        score=test_score,
        candidate='A',
        threshold=threshold,
        target_coverage=float(target_coverage),
        min_period_trades=min_period_trades,
    )
    score_series = pd.Series(np.asarray(test_score, dtype=np.float64), index=test_frame.index, dtype='float64')
    selected_mask = score_series >= threshold
    selected_mask.loc[test_frame['signal'].to_numpy() == 0] = False
    sequential_summary = run_sequential_check(
        frame=test_frame,
        selected_mask=selected_mask,
        hold_bars=sequential_hold_bars,
    )

    validation_summary_path = output_path / 'baseline_a_validation_summary.csv'
    test_summary_path = output_path / 'baseline_a_test_summary.csv'
    rule_path = output_path / 'baseline_a_selected_rule.json'
    report_path = output_path / 'baseline_a_report.md'
    validation_summary.to_csv(validation_summary_path, sep=';', index=False)
    test_summary.to_csv(test_summary_path, sep=';', index=False)

    payload = {
        'winner': _jsonable(winner),
        'coverage_grid': [float(target_coverage)],
        'validation_csv': str(validation_path),
        'test_csv': str(test_path),
        'sequential_hold_bars': int(sequential_hold_bars),
        'min_period_trades': int(min_period_trades),
        'validation_summary_path': str(validation_summary_path),
        'test_summary_path': str(test_summary_path),
        'sequential_summary': _jsonable(sequential_summary),
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


def _load_test_summary(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    frame = pd.read_csv(path, sep=';')
    if frame.empty:
        return {}
    return _jsonable(frame.iloc[0].to_dict())


def run_single_seed(
    *,
    seed: int,
    output_root: Path,
    baseline_root: Path,
    epochs: int,
    patience: int,
    batch_size: int,
    seq_len: int,
    baseline_coverage: float,
    alpha: float,
    min_trades: int,
    min_period_trades: int,
    sequential_hold_bars: int,
    clear_cache: bool,
    skip_existing: bool,
) -> dict[str, object]:
    run_dir = output_root / seed_slug(seed)
    run_dir.mkdir(parents=True, exist_ok=True)
    summary_path = run_dir / 'summary.json'
    if skip_existing and summary_path.exists():
        return json.loads(summary_path.read_text(encoding='utf-8'))

    started_at = time.time()
    train_result = train_model(
        model_name='transformer',
        task=ENTRY_PATH_V1_QUANTILE_TARGET,
        epochs=epochs,
        batch_size=batch_size,
        lr=DEFAULTS['lr'],
        weight_decay=DEFAULTS['weight_decay'],
        patience=patience,
        seed=seed,
        use_scaler=False,
        use_weighted_sampler=False,
        seq_len=seq_len,
        clear_cache=clear_cache,
        model_kwargs={},
        output_dir=run_dir,
    )
    checkpoint_path = Path(train_result['checkpoint_path'])

    validation_predictions = run_dir / 'entry_path_v1_quantile_validation_predictions.csv'
    test_predictions = run_dir / 'entry_path_v1_quantile_test_predictions.csv'
    export_predictions(
        input_csv='DATA/Nero_validation_labeled.csv',
        checkpoint=checkpoint_path,
        output_csv=validation_predictions,
        task=ENTRY_PATH_V1_QUANTILE_TARGET,
        seed=seed,
    )
    export_predictions(
        input_csv='DATA/Nero_test_labeled.csv',
        checkpoint=checkpoint_path,
        output_csv=test_predictions,
        task=ENTRY_PATH_V1_QUANTILE_TARGET,
        seed=seed,
    )

    baseline_seed_dir = baseline_root / seed_slug(seed)
    baseline_rule = build_baseline_a_rule(
        validation_csv=baseline_seed_dir / 'validation_predictions.csv',
        test_csv=baseline_seed_dir / 'test_predictions.csv',
        output_dir=run_dir,
        target_coverage=baseline_coverage,
        min_period_trades=min_period_trades,
        sequential_hold_bars=sequential_hold_bars,
    )
    baseline_rule_path = run_dir / 'baseline_a_selected_rule.json'

    quantile = run_quantile_benchmark(
        validation_csv=validation_predictions,
        test_csv=test_predictions,
        baseline_rule=baseline_rule_path,
        output_dir=run_dir,
        alpha=alpha,
        min_trades=min_trades,
    )
    quantile_test_summary = _load_test_summary(Path(quantile['test_summary_path']))

    payload = {
        'config': {
            'seed': int(seed),
            'epochs': int(epochs),
            'patience': int(patience),
            'batch_size': int(batch_size),
            'seq_len': int(seq_len),
            'baseline_root': str(baseline_root),
            'baseline_coverage': float(baseline_coverage),
            'alpha': float(alpha),
            'min_trades': int(min_trades),
            'min_period_trades': int(min_period_trades),
            'sequential_hold_bars': int(sequential_hold_bars),
            'clear_cache': bool(clear_cache),
        },
        'checkpoint_path': str(checkpoint_path),
        'prediction_files': {
            'validation': str(validation_predictions),
            'test': str(test_predictions),
        },
        'baseline_rule_path': str(baseline_rule_path),
        'train_result': _jsonable(train_result),
        'baseline_rule': _jsonable(baseline_rule),
        'quantile_benchmark': _jsonable(quantile),
        'quantile_test_summary': quantile_test_summary,
        'runtime_sec': time.time() - started_at,
    }
    summary_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    return payload


def summarize_runs(runs: list[dict[str, object]], output_root: Path) -> dict[str, object]:
    rows = []
    for run in runs:
        train_result = run.get('train_result', {})
        quantile = run.get('quantile_benchmark', {})
        q_winner = quantile.get('winner', {})
        q_seq = quantile.get('sequential_summary', {})
        q_test = run.get('quantile_test_summary', {})
        baseline = run.get('baseline_rule', {})
        b_winner = baseline.get('winner', {})
        b_seq = baseline.get('sequential_summary', {})
        rows.append({
            'seed': run['config']['seed'],
            'device': train_result.get('runtime_metadata', {}).get('device'),
            'torch': train_result.get('runtime_metadata', {}).get('torch'),
            'best_val_score': train_result.get('best_metric'),
            'best_epoch': train_result.get('best_epoch'),
            'baseline_candidate': b_winner.get('candidate'),
            'baseline_target_coverage': b_winner.get('target_coverage'),
            'baseline_validation_pf': b_winner.get('pf'),
            'baseline_validation_trades': b_winner.get('trades'),
            'baseline_sequential_pf': b_seq.get('pf'),
            'baseline_sequential_trades': b_seq.get('trades'),
            'quantile_winner': q_winner.get('candidate'),
            'quantile_rule': q_winner.get('rule'),
            'quantile_validation_pf': q_winner.get('pf'),
            'quantile_validation_trades': q_winner.get('trades'),
            'quantile_test_pf': q_test.get('pf'),
            'quantile_test_trades': q_test.get('trades'),
            'quantile_sequential_pf': q_seq.get('pf'),
            'quantile_sequential_trades': q_seq.get('trades'),
            'quantile_sequential_win_rate': q_seq.get('win_rate'),
            'checkpoint_path': run.get('checkpoint_path'),
            'baseline_rule_path': run.get('baseline_rule_path'),
        })
    summary_frame = pd.DataFrame(rows)
    summary_csv = output_root / 'multi_seed_summary.csv'
    summary_json = output_root / 'multi_seed_summary.json'
    summary_frame.to_csv(summary_csv, sep=';', index=False)

    winner_counts = summary_frame['quantile_winner'].value_counts(dropna=False).to_dict() if not summary_frame.empty else {}
    rule_counts = summary_frame['quantile_rule'].value_counts(dropna=False).to_dict() if not summary_frame.empty else {}
    payload = {
        'rows': _jsonable(rows),
        'winner_counts': _jsonable(winner_counts),
        'rule_counts': _jsonable(rule_counts),
        'summary_csv': str(summary_csv),
    }
    summary_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Run entry_path_v1_quantile retrain over server CPU live-safe baseline A.'
    )
    parser.add_argument('--output-dir', default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument('--baseline-root', default=str(DEFAULT_BASELINE_ROOT))
    parser.add_argument('--seeds', nargs='+', type=int, default=[42])
    parser.add_argument('--epochs', type=int, default=5)
    parser.add_argument('--patience', type=int, default=DEFAULTS['patience'])
    parser.add_argument('--batch-size', type=int, default=DEFAULTS['batch_size'])
    parser.add_argument('--seq-len', type=int, default=20)
    parser.add_argument('--baseline-coverage', type=float, default=DEFAULT_BASELINE_COVERAGE)
    parser.add_argument('--alpha', type=float, default=0.10)
    parser.add_argument('--min-trades', type=int, default=10)
    parser.add_argument('--min-period-trades', type=int, default=10)
    parser.add_argument('--sequential-hold-bars', type=int, default=24)
    parser.add_argument('--clear-cache', action='store_true')
    parser.add_argument('--skip-existing', action='store_true')
    return parser.parse_args()


def main() -> dict[str, object]:
    args = parse_args()
    output_root = Path(args.output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    baseline_root = Path(args.baseline_root)

    runs = []
    for seed in args.seeds:
        runs.append(
            run_single_seed(
                seed=seed,
                output_root=output_root,
                baseline_root=baseline_root,
                epochs=args.epochs,
                patience=args.patience,
                batch_size=args.batch_size,
                seq_len=args.seq_len,
                baseline_coverage=args.baseline_coverage,
                alpha=args.alpha,
                min_trades=args.min_trades,
                min_period_trades=args.min_period_trades,
                sequential_hold_bars=args.sequential_hold_bars,
                clear_cache=args.clear_cache,
                skip_existing=args.skip_existing,
            )
        )

    manifest = {
        'seeds': [int(seed) for seed in args.seeds],
        'output_dir': str(output_root),
        'baseline_root': str(baseline_root),
        'runs': runs,
        'summary': summarize_runs(runs, output_root),
    }
    manifest_path = output_root / 'manifest.json'
    manifest_path.write_text(json.dumps(_jsonable(manifest), ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(_jsonable(manifest), ensure_ascii=False, indent=2))
    return manifest


if __name__ == '__main__':
    main()
