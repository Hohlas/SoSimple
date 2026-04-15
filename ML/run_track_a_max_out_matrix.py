from __future__ import annotations

import argparse
import json
import shutil
import time
from pathlib import Path

from API.generate_signals import generate_signals
from ML.benchmark_entry_path_v2 import run_benchmark
from ML.entry_path_task import ENTRY_PATH_TARGET
from ML.evaluate_test import run_evaluation
from ML.train import CHECKPOINTS_DIR, REPORTS_DIR, train_model
from ML.data_loader import task_checkpoint_suffix


DEFAULT_MATRIX_CONFIGS = [
    {'model': 'transformer', 'seq_len': 20},
    {'model': 'transformer', 'seq_len': 50},
    {'model': 'transformer', 'seq_len': 100},
    {'model': 'entry_path_dual_stream', 'seq_len': 20},
    {'model': 'entry_path_dual_stream', 'seq_len': 50},
    {'model': 'entry_path_dual_stream', 'seq_len': 100},
]


def config_slug(model: str, seq_len: int) -> str:
    return f'{model}_seq{seq_len}'


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


def _copy_if_exists(source: Path, destination: Path) -> None:
    if source.exists():
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def run_single_config(
    *,
    model_name: str,
    seq_len: int,
    epochs: int,
    patience: int,
    batch_size: int,
    seed: int,
    output_root: Path,
    min_pf: float,
    target_trades_per_year: int,
    skip_existing: bool,
) -> dict[str, object]:
    slug = config_slug(model_name, seq_len)
    run_dir = output_root / slug
    run_dir.mkdir(parents=True, exist_ok=True)

    summary_path = run_dir / 'summary.json'
    if skip_existing and summary_path.exists():
        return json.loads(summary_path.read_text(encoding='utf-8'))

    started_at = time.time()
    result = train_model(
        model_name=model_name,
        task=ENTRY_PATH_TARGET,
        epochs=epochs,
        batch_size=batch_size,
        lr=1e-3,
        weight_decay=1e-4,
        patience=patience,
        seed=seed,
        use_scaler=False,
        use_weighted_sampler=False,
        seq_len=seq_len,
        clear_cache=False,
        silent=False,
        model_kwargs={},
    )

    suffix = task_checkpoint_suffix(ENTRY_PATH_TARGET)
    checkpoint_path = CHECKPOINTS_DIR / f'{model_name}{suffix}_best.pt'
    run_checkpoint_path = run_dir / 'checkpoint.pt'
    _copy_if_exists(checkpoint_path, run_checkpoint_path)

    run_evaluation(
        model_name=model_name,
        checkpoint_path=str(run_checkpoint_path),
        task=ENTRY_PATH_TARGET,
        seed=seed,
    )
    _copy_if_exists(REPORTS_DIR / 'evaluate_test_entry_path_v1.md', run_dir / 'evaluate_test_entry_path_v1.md')
    _copy_if_exists(REPORTS_DIR / 'entry_path_test_predictions.csv', run_dir / 'entry_path_test_predictions.csv')

    export_prefix = run_dir / 'entry_path_v1'
    generate_signals(
        model_name=model_name,
        task=ENTRY_PATH_TARGET,
        seed=seed,
        research_out_prefix=str(export_prefix),
    )

    validation_csv = run_dir / 'entry_path_v1_validation_predictions.csv'
    test_csv = run_dir / 'entry_path_v1_test_predictions.csv'
    benchmark_dir = run_dir / 'benchmark_v2'
    benchmark = run_benchmark(
        validation_csv=validation_csv,
        test_csv=test_csv,
        output_dir=benchmark_dir,
        min_pf=min_pf,
        target_trades_per_year=target_trades_per_year,
    )

    payload = {
        'config': {
            'model': model_name,
            'seq_len': seq_len,
            'epochs': epochs,
            'patience': patience,
            'batch_size': batch_size,
            'seed': seed,
        },
        'train_result': _jsonable(result),
        'checkpoint_path': str(run_checkpoint_path),
        'exports': {
            'validation_csv': str(validation_csv),
            'test_csv': str(test_csv),
        },
        'benchmark_v2': _jsonable(benchmark),
        'runtime_sec': time.time() - started_at,
    }
    summary_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Run bounded Track A max-out matrix for entry_path_v1.')
    parser.add_argument('--output-dir', default='ML/reports/track_a_max_out_matrix')
    parser.add_argument('--epochs', type=int, default=3)
    parser.add_argument('--patience', type=int, default=2)
    parser.add_argument('--batch-size', type=int, default=256)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--min-pf', type=float, default=1.0)
    parser.add_argument('--target-trades-per-year', type=int, default=40)
    parser.add_argument('--configs', nargs='*', default=None, help='Optional list of config slugs to run.')
    parser.add_argument('--skip-existing', action='store_true')
    return parser.parse_args()


def main() -> dict[str, object]:
    args = parse_args()
    output_root = Path(args.output_dir)
    output_root.mkdir(parents=True, exist_ok=True)

    selected = set(args.configs or [])
    matrix = [
        config for config in DEFAULT_MATRIX_CONFIGS
        if not selected or config_slug(config['model'], config['seq_len']) in selected
    ]

    runs: list[dict[str, object]] = []
    for config in matrix:
        payload = run_single_config(
            model_name=config['model'],
            seq_len=config['seq_len'],
            epochs=args.epochs,
            patience=args.patience,
            batch_size=args.batch_size,
            seed=args.seed,
            output_root=output_root,
            min_pf=args.min_pf,
            target_trades_per_year=args.target_trades_per_year,
            skip_existing=args.skip_existing,
        )
        runs.append(payload)

    manifest = {
        'runs': runs,
        'configs': [config_slug(config['model'], config['seq_len']) for config in matrix],
    }
    (output_root / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return manifest


if __name__ == '__main__':
    main()
