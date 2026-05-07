from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import pandas as pd

from ML.benchmark_entry_path_trade_filter import DEFAULT_COVERAGE_GRID
from ML.benchmark_entry_path_trade_filter import run_benchmark
from ML.entry_path_task import ENTRY_PATH_LIVE_SAFE_FEATURE_PROFILE
from ML.entry_path_task import ENTRY_PATH_TARGET
from ML.export_entry_path_predictions import export_predictions
from ML.train import DEFAULTS
from ML.train import train_model


DEFAULT_A_COVERAGE_GRID = [0.05, 0.075, 0.10, 0.125, 0.15, 0.20, 0.25, 0.30]


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


def seed_slug(seed: int) -> str:
    return f'seed_{int(seed):03d}'


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
    epochs: int,
    patience: int,
    batch_size: int,
    seq_len: int,
    feature_profile: str,
    coverage_grid: list[float],
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
        task=ENTRY_PATH_TARGET,
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
        entry_path_feature_profile=feature_profile,
        output_dir=run_dir,
    )
    checkpoint_path = Path(train_result['checkpoint_path'])

    validation_predictions = run_dir / 'validation_predictions.csv'
    test_predictions = run_dir / 'test_predictions.csv'
    export_predictions(
        input_csv='DATA/Nero_validation_labeled.csv',
        checkpoint=checkpoint_path,
        output_csv=validation_predictions,
        task=ENTRY_PATH_TARGET,
        feature_profile=feature_profile,
        seed=seed,
    )
    export_predictions(
        input_csv='DATA/Nero_test_labeled.csv',
        checkpoint=checkpoint_path,
        output_csv=test_predictions,
        task=ENTRY_PATH_TARGET,
        feature_profile=feature_profile,
        seed=seed,
    )

    benchmark = run_benchmark(
        validation_csv=validation_predictions,
        test_csv=test_predictions,
        output_dir=run_dir,
        coverage_grid=coverage_grid,
        min_period_trades=min_period_trades,
        sequential_hold_bars=sequential_hold_bars,
    )
    test_summary = _load_test_summary(Path(benchmark['test_summary_path']))

    payload = {
        'config': {
            'seed': int(seed),
            'epochs': int(epochs),
            'patience': int(patience),
            'batch_size': int(batch_size),
            'seq_len': int(seq_len),
            'feature_profile': feature_profile,
            'coverage_grid': [float(value) for value in coverage_grid],
            'min_period_trades': int(min_period_trades),
            'sequential_hold_bars': int(sequential_hold_bars),
            'clear_cache': bool(clear_cache),
        },
        'checkpoint_path': str(checkpoint_path),
        'prediction_files': {
            'validation': str(validation_predictions),
            'test': str(test_predictions),
        },
        'train_result': _jsonable(train_result),
        'benchmark': _jsonable(benchmark),
        'test_summary': test_summary,
        'runtime_sec': time.time() - started_at,
    }
    summary_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    return payload


def summarize_runs(runs: list[dict[str, object]], output_root: Path) -> dict[str, object]:
    rows = []
    for run in runs:
        train_result = run.get('train_result', {})
        benchmark = run.get('benchmark', {})
        winner = benchmark.get('winner', {})
        sequential = benchmark.get('sequential_summary', {})
        test_summary = run.get('test_summary', {})
        rows.append({
            'seed': run['config']['seed'],
            'device': train_result.get('runtime_metadata', {}).get('device'),
            'torch': train_result.get('runtime_metadata', {}).get('torch'),
            'best_ret_pearson_r': train_result.get('best_metric'),
            'best_epoch': train_result.get('best_epoch'),
            'winner': winner.get('candidate'),
            'target_coverage': winner.get('target_coverage'),
            'validation_pf': winner.get('pf'),
            'validation_trades': winner.get('trades'),
            'test_pf': test_summary.get('pf'),
            'test_trades': test_summary.get('trades'),
            'sequential_pf': sequential.get('pf'),
            'sequential_trades': sequential.get('trades'),
            'sequential_win_rate': sequential.get('win_rate'),
            'checkpoint_path': run.get('checkpoint_path'),
        })
    summary_frame = pd.DataFrame(rows)
    summary_csv = output_root / 'multi_seed_summary.csv'
    summary_json = output_root / 'multi_seed_summary.json'
    summary_frame.to_csv(summary_csv, sep=';', index=False)
    payload = {
        'rows': rows,
        'summary_csv': str(summary_csv),
    }
    summary_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Run reproducible entry_path_v1_live_safe retrain/export/benchmark per seed.'
    )
    parser.add_argument('--output-dir', default='ML/reports/entry_path_v1_live_safe_reproducibility')
    parser.add_argument('--seeds', nargs='+', type=int, default=[42])
    parser.add_argument('--epochs', type=int, default=5)
    parser.add_argument('--patience', type=int, default=DEFAULTS['patience'])
    parser.add_argument('--batch-size', type=int, default=DEFAULTS['batch_size'])
    parser.add_argument('--seq-len', type=int, default=20)
    parser.add_argument('--feature-profile', default=ENTRY_PATH_LIVE_SAFE_FEATURE_PROFILE)
    parser.add_argument('--coverage-grid', nargs='+', type=float, default=DEFAULT_A_COVERAGE_GRID)
    parser.add_argument('--min-period-trades', type=int, default=10)
    parser.add_argument('--sequential-hold-bars', type=int, default=24)
    parser.add_argument('--clear-cache', action='store_true')
    parser.add_argument('--skip-existing', action='store_true')
    return parser.parse_args()


def main() -> dict[str, object]:
    args = parse_args()
    output_root = Path(args.output_dir)
    output_root.mkdir(parents=True, exist_ok=True)

    runs = []
    for seed in args.seeds:
        runs.append(
            run_single_seed(
                seed=seed,
                output_root=output_root,
                epochs=args.epochs,
                patience=args.patience,
                batch_size=args.batch_size,
                seq_len=args.seq_len,
                feature_profile=args.feature_profile,
                coverage_grid=args.coverage_grid,
                min_period_trades=args.min_period_trades,
                sequential_hold_bars=args.sequential_hold_bars,
                clear_cache=args.clear_cache,
                skip_existing=args.skip_existing,
            )
        )

    manifest = {
        'seeds': [int(seed) for seed in args.seeds],
        'output_dir': str(output_root),
        'runs': runs,
        'summary': summarize_runs(runs, output_root),
    }
    manifest_path = output_root / 'manifest.json'
    manifest_path.write_text(json.dumps(_jsonable(manifest), ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(_jsonable(manifest), ensure_ascii=False, indent=2))
    return manifest


if __name__ == '__main__':
    main()
